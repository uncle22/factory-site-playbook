#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check that a list of URLs returns what you expect.

Built for one job: before publishing an article or a page, prove that every
internal link resolves. A link to a 404 passes no ranking value and makes the
page look careless, and it is entirely your own fault.

Usage:
    python check_links.py --base https://example.com --paths /products/,/contact/
    python check_links.py --base https://example.com --file urls.txt
    python check_links.py --sitemap https://example.com/sitemap.xml --limit 200

Options:
    --expect 200        comma-separated acceptable status codes (default 200,301,302,308)
    --concurrency 8     parallel requests
    --timeout 20        per-request timeout in seconds
    --insecure          skip TLS verification (self-signed staging)
    --csv out.csv       write results to CSV

Exit codes: 0 all acceptable, 5 at least one unexpected status.
"""
import argparse
import csv
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch(url, timeout, insecure):
    request = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
    context = None
    if insecure:
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            return response.status, response.geturl()
    except urllib.error.HTTPError as exc:
        return exc.code, url
    except urllib.error.URLError as exc:
        return "ERR", str(exc.reason)[:40]
    except Exception as exc:                       # timeouts, TLS failures, bad hosts
        return "ERR", str(exc)[:40]


def load_from_sitemap(sitemap_url, timeout, insecure):
    request = urllib.request.Request(sitemap_url, headers={"User-Agent": UA})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", "replace")
    if "<loc>" not in body:
        sys.exit("no <loc> entries in %s - is it returning HTML?" % sitemap_url)
    return re.findall(r"<loc>\s*(.*?)\s*</loc>", body)


def compose(base, path):
    """Join base and path without producing a double slash or a missing one."""
    if path.startswith("http"):
        return path
    root = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return root + path


def main():
    ap = argparse.ArgumentParser(description="Check HTTP status codes for a URL list.")
    ap.add_argument("--base", default="", help="prefix for paths")
    ap.add_argument("--paths", default="", help="comma-separated paths")
    ap.add_argument("--file", default="", help="file with one URL or path per line")
    ap.add_argument("--sitemap", default="", help="read URLs from a sitemap")
    ap.add_argument("--limit", type=int, default=0, help="cap the number of URLs checked")
    ap.add_argument("--expect", default="200,301,302,308")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--timeout", type=int, default=20)
    ap.add_argument("--insecure", action="store_true")
    ap.add_argument("--csv", default="")
    args = ap.parse_args()

    urls = []
    if args.paths:
        for path in args.paths.split(","):
            path = path.strip()
            if not path:
                continue
            if not path.startswith("http"):
                if not args.base:
                    sys.exit("--base is required when --paths contains relative paths")
                if not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
                    path += "/"
            urls.append(compose(args.base, path))
    if args.file:
        with open(args.file, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                urls.append(compose(args.base, line))
    if args.sitemap:
        urls.extend(load_from_sitemap(args.sitemap, args.timeout, args.insecure))
    if not urls:
        sys.exit("nothing to check: pass --paths, --file or --sitemap")
    if args.limit:
        urls = urls[:args.limit]

    acceptable = {int(code) for code in args.expect.split(",") if code.strip().isdigit()}

    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        results = list(pool.map(lambda u: (u,) + fetch(u, args.timeout, args.insecure), urls))

    failures = []
    for url, status, final in results:
        mark = "ok " if status in acceptable else "BAD"
        redirect = "" if final == url else "  -> %s" % final
        print("[%s] %-4s %s%s" % (mark, status, url, redirect))
        if status not in acceptable:
            failures.append((url, status))

    print("\n%d checked, %d unexpected" % (len(results), len(failures)))
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["url", "status", "final_url"])
            writer.writerows(results)
        print("csv written: %s" % args.csv)

    sys.exit(5 if failures else 0)


if __name__ == "__main__":
    main()
