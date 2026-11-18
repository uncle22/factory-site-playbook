#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baseline audit of a live site: what it is built on, what is indexed, what is heavy.

This is the automated half of stage P0. It cannot judge content, and it cannot
see inside an admin panel — those stay manual. What it does is remove the guesswork
about stack, sitemap health and page weight.

Usage:
    python site_audit.py https://example.com
    python site_audit.py https://example.com --json
    python site_audit.py https://example.com --paths /,/de/,/products/

Reads a browser user agent by default, because several CDNs serve a different
(and less informative) response to unfamiliar clients.
"""
import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def request(url, timeout=25, insecure=False, headers=None):
    merged = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9",
              "Accept-Encoding": "identity"}
    if headers:
        merged.update(headers)
    context = None
    if insecure:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers=merged)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
            body = response.read().decode("utf-8", "replace")
            return response.status, dict(response.headers), body, response.geturl()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        return exc.code, dict(exc.headers or {}), body, url
    except Exception as exc:
        return None, {}, "", str(exc)


def find(pattern, text, flags=re.I):
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def audit(base, paths, insecure):
    base = base.rstrip("/") + "/"
    findings = {}

    status, headers, html, final = request(base, insecure=insecure)
    findings["status"] = status
    findings["final_url"] = final
    findings["server"] = headers.get("Server")
    findings["cache_headers"] = {
        key: value for key, value in headers.items()
        if key.lower() in ("x-cache", "age", "cf-cache-status", "via", "x-cache-hits")
    }

    findings["generator"] = find(r'<meta name="generator" content="([^"]+)"', html)
    findings["theme"] = sorted(set(re.findall(r"wp-content/themes/([^/\"']+)", html)))
    findings["plugins"] = [p for p in sorted(set(
        re.findall(r"wp-content/plugins/([^/\"'?]+)", html))) if p not in ("*", "")]
    findings["plugins"] = findings["plugins"][:15]
    findings["has_wp_json"] = 'rel="https://api.w.org/"' in html or "/wp-json/" in html

    # title, description, canonical, og:image
    findings["title"] = find(r"<title[^>]*>(.*?)</title>", html, re.S)
    findings["title_length"] = len(findings["title"]) if findings["title"] else 0
    findings["description"] = find(r'<meta name="description" content="([^"]*)"', html)
    findings["canonical"] = find(r'<link rel="canonical" href="([^"]+)"', html)
    findings["og_image"] = find(r'<meta property="og:image" content="([^"]+)"', html)

    # hreflang cluster
    alternates = re.findall(r'<link[^>]+hreflang="([^"]+)"[^>]+href="([^"]+)"', html)
    alternates += [(h, u) for u, h in
                   re.findall(r'<link[^>]+href="([^"]+)"[^>]+hreflang="([^"]+)"', html)]
    findings["hreflang"] = sorted(set(alternates))
    findings["hreflang_has_xdefault"] = any(code == "x-default" for code, _ in alternates)

    # robots
    robots_status, robots_headers, robots_body, _ = request(
        urljoin(base, "/robots.txt"), insecure=insecure)
    findings["robots_status"] = robots_status
    findings["robots_disallow"] = re.findall(r"(?im)^disallow:\s*(\S+)", robots_body or "")

    # sitemap — trust robots.txt first, it is the only authoritative declaration
    declared = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots_body or "")
    candidates = declared + ["sitemap.xml", "sitemap_index.xml", "wp-sitemap.xml"]
    findings["sitemap"] = {"url": None, "status": None, "content_type": None,
                           "loc_count": 0, "looks_like_xml": False, "declared": declared}
    for candidate in candidates:
        target = candidate if candidate.startswith("http") else urljoin(base, candidate)
        sm_status, sm_headers, sm_body, _ = request(target, insecure=insecure)
        content_type = (sm_headers.get("Content-Type") or "").split(";")[0].strip()
        loc_count = sm_body.count("<loc>")
        findings["sitemap"] = {
            "url": target,
            "status": sm_status,
            "content_type": content_type,
            "loc_count": loc_count,
            "looks_like_xml": content_type.endswith("xml") and loc_count > 0,
            "declared": declared,
        }
        if loc_count > 0:
            break

    # heaviest images on the page
    images = re.findall(r'<img[^>]+src="([^"]+)"', html)
    heavy = []
    for src in dict.fromkeys(images[:20]):
        if src.startswith("data:"):
            continue
        absolute = urljoin(base, src)
        _, img_headers, img_body, _ = request(absolute, insecure=insecure)
        size = len(img_body.encode("utf-8", "replace")) if isinstance(img_body, str) else 0
        heavy.append({"src": absolute.split("/")[-1][:40],
                      "ext": urlparse(absolute).path.rsplit(".", 1)[-1].lower(),
                      "kb": round(size / 1024.0, 1)})
    heavy.sort(key=lambda item: item["kb"], reverse=True)
    findings["heaviest_images"] = heavy[:5]

    # per-path status — plain concatenation, urljoin treats "" and "/" inconsistently
    findings["paths"] = []
    for path in paths:
        target = base + path.lstrip("/")
        code, _, body, error = request(target, insecure=insecure)
        findings["paths"].append({"path": path, "status": code,
                                  "bytes": len(body), "error": None if code else error})

    return findings


def main():
    ap = argparse.ArgumentParser(description="Baseline audit of a live site.")
    ap.add_argument("url")
    ap.add_argument("--paths", default="/", help="comma-separated paths to probe")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--insecure", action="store_true")
    args = ap.parse_args()

    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    data = audit(args.url, paths, args.insecure)

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print("=" * 62)
    print("BASELINE AUDIT  %s" % args.url)
    print("=" * 62)
    print("status            %s" % data["status"])
    if data["final_url"] and data["final_url"].rstrip("/") != args.url.rstrip("/"):
        print("final url         %s" % data["final_url"])
    print("server            %s" % (data["server"] or "unknown"))
    if data["cache_headers"]:
        print("cache layer       %s" % ", ".join(
            "%s:%s" % (k, v) for k, v in data["cache_headers"].items()))
    print("generator         %s" % (data["generator"] or "none declared"))
    print("theme             %s" % (", ".join(data["theme"]) or "not detected"))
    if data["plugins"]:
        print("plugins seen      %s" % ", ".join(data["plugins"]))
    print()

    print("title             %s" % (data["title"] or "MISSING"))
    print("title length      %d %s" % (data["title_length"],
                                       "(over 67, will truncate)" if data["title_length"] > 67 else ""))
    print("description       %s" % (data["description"] or "MISSING"))
    print("canonical         %s" % (data["canonical"] or "MISSING"))
    print("og:image          %s" % (data["og_image"] or "MISSING"))
    print()

    print("hreflang tags     %d%s" % (len(data["hreflang"]),
                                      "" if data["hreflang_has_xdefault"] else "  (no x-default)"))
    for code, href in data["hreflang"]:
        print("                  %-10s %s" % (code, href))
    print()

    sitemap = data["sitemap"]
    print("sitemap           %s" % (sitemap["url"] or "not found"))
    if sitemap["url"]:
        print("                  status %s, type %s, %d urls%s"
              % (sitemap["status"], sitemap["content_type"], sitemap["loc_count"],
                 "" if sitemap["looks_like_xml"] else "   <-- not valid XML"))
    if sitemap["declared"]:
        print("                  declared in robots: %s" % ", ".join(sitemap["declared"]))
    print("robots.txt        status %s" % data["robots_status"])
    for rule in data["robots_disallow"][:8]:
        print("                  disallow %s" % rule)
    print()

    if data["heaviest_images"]:
        print("heaviest images")
        for image in data["heaviest_images"]:
            flag = "  <-- over 300 KB" if image["kb"] > 300 else ""
            print("                  %7.1f KB  %-8s %s%s"
                  % (image["kb"], image["ext"], image["src"], flag))
        print()

    print("paths")
    for row in data["paths"]:
        status = row["status"] if row["status"] is not None else "ERR"
        flag = "" if row["status"] == 200 else "  <-- unexpected"
        detail = row.get("error") or ("%d bytes" % row["bytes"])
        print("                  %-4s %-22s %s%s"
              % (status, row["path"], detail, flag))

    print()
    print("manual checks still required:")
    print("  - indexed count (site: operator in a browser)")
    print("  - consent default position relative to tag loading")
    print("  - one conversion fired manually, with a count")
    print("  - cache purge actually landing (see references/05-deploy-cache.md)")


if __name__ == "__main__":
    main()
