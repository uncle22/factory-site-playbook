#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy one file into a WordPress theme, safely.

Sequence: backup -> upload to temp -> php -l -> move into place -> purge -> verify.

The order matters. Linting after the move means a syntax error is already live.
Purging before the move means the cache serves the old file again.

Environment (required):
    DEPLOY_HOST       server hostname or IP
    DEPLOY_USER       ssh/sftp user
    DEPLOY_PASS       password           (or DEPLOY_KEY for a private key path)
    WP_ROOT           absolute path to the WordPress root on the server
    THEME_DIR         theme directory name, e.g. my-child-theme

Environment (optional):
    THEME_REL         theme path relative to the SFTP root, when the SFTP user is
                      chrooted and sees a different path than the shell does.
                      e.g. /public_html/wp-content/themes/my-child-theme
    SITE_DOMAIN       domain used for the purge and verify steps
    ORIGIN_IP         origin IP for --resolve during purge (default 127.0.0.1)
    VERIFY_PATHS      comma-separated paths to check after deploy, e.g. /,/products/

Usage:
    python deploy_theme_file.py local.php functions.php
    python deploy_theme_file.py local.php functions.php --verify-marker "newString"
    python deploy_theme_file.py local.php functions.php --dry-run

Exit codes: 0 success, 1 lint failed, 2 verify failed, 3 connection failed.
"""
import argparse
import os
import posixpath
import sys
import time

try:
    import paramiko
except ImportError:
    sys.exit("paramiko is required: pip install paramiko")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        sys.exit("missing required environment variable: %s" % name)
    return value


class Remote:
    def __init__(self):
        host = env("DEPLOY_HOST", required=True)
        user = env("DEPLOY_USER", required=True)
        key = os.environ.get("DEPLOY_KEY")
        self.cli = paramiko.SSHClient()
        self.cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if key:
                self.cli.connect(host, 22, user, key_filename=key, timeout=30)
            else:
                self.cli.connect(host, 22, user, env("DEPLOY_PASS", required=True), timeout=30)
        except Exception as exc:
            sys.exit("connection failed: %s" % exc)

    def run(self, cmd, timeout=180):
        _, out, err = self.cli.exec_command(cmd, timeout=timeout)
        stdout = out.read().decode("utf-8", "replace").strip()
        stderr = err.read().decode("utf-8", "replace").strip()
        code = out.channel.recv_exit_status()
        return code, stdout, stderr

    def step(self, label, cmd, timeout=180):
        code, out, err = self.run(cmd, timeout)
        flag = "ok" if code == 0 else "EXIT %d" % code
        line = out.splitlines()[0][:200] if out else ""
        print("  [%-10s] %-12s %s%s" % (label, flag, line, ("  ERR: " + err[:160]) if err else ""))
        return code, out


def main():
    ap = argparse.ArgumentParser(description="Deploy one file into a WordPress theme.")
    ap.add_argument("local_file")
    ap.add_argument("remote_name", help="filename inside the theme directory")
    ap.add_argument("--verify-marker", default=None,
                    help="string that must appear in the response body after deploy")
    ap.add_argument("--dry-run", action="store_true", help="upload and lint, do not move into place")
    args = ap.parse_args()

    if not os.path.isfile(args.local_file):
        sys.exit("local file not found: %s" % args.local_file)

    wp_root = env("WP_ROOT", required=True).rstrip("/")
    theme_dir = env("THEME_DIR", required=True).strip("/")
    theme_rel = env("THEME_REL") or posixpath.join("wp-content/themes", theme_dir)
    shell_theme = posixpath.join(wp_root, "wp-content/themes", theme_dir)
    domain = env("SITE_DOMAIN")
    origin = env("ORIGIN_IP", "127.0.0.1")
    stamp = time.strftime("%Y%m%d%H%M%S")

    r = Remote()
    print("deploy %s -> %s/%s" % (args.local_file, shell_theme, args.remote_name))

    # 1. backup
    r.step("backup",
           "cp -p %s/%s %s/%s.bak-%s 2>/dev/null || true"
           % (shell_theme, args.remote_name, shell_theme, args.remote_name, stamp))

    # 2. upload to a temp name, never in place
    tmp_name = ".tmp-deploy-%s" % stamp
    sftp = r.cli.open_sftp()
    try:
        sftp.put(args.local_file, posixpath.join(theme_rel, tmp_name))
        print("  [%-10s] ok" % "upload")
    except Exception as exc:
        sftp.close()
        sys.exit("upload failed: %s" % exc)

    # 3. lint the uploaded file, in place, before it becomes the real file
    code, out = r.step("php -l", "php -l %s/%s" % (shell_theme, tmp_name))
    if code != 0:
        r.run("rm -f %s/%s" % (shell_theme, tmp_name))
        sftp.close()
        sys.exit(1)

    if args.dry_run:
        r.run("rm -f %s/%s" % (shell_theme, tmp_name))
        sftp.close()
        print("dry run: uploaded and linted, not moved into place")
        return

    # 4. preserve ownership and mode, then move
    r.step("install",
           "chmod 644 %s/%s && mv -f %s/%s %s/%s"
           % (shell_theme, tmp_name, shell_theme, tmp_name, shell_theme, args.remote_name))
    sftp.close()

    # 5. purge both cache layers
    r.step("wp cache", "cd %s && wp cache flush --allow-root 2>&1 | tail -1" % wp_root)
    if domain:
        r.step("varnish",
               "curl -sk -o /dev/null -w '%%{http_code}' --resolve %s:443:%s "
               "-X PURGE https://%s/" % (domain, origin, domain))
    else:
        print("  [%-10s] skipped    SITE_DOMAIN not set" % "varnish")

    # 6. verify with a bare URL and a browser user agent, then assert content
    if not domain:
        print("verify skipped: SITE_DOMAIN not set")
        return

    paths = [p.strip() for p in env("VERIFY_PATHS", "/").split(",") if p.strip()]
    failed = False
    for path in paths:
        code, out = r.run(
            "curl -sk -A '%s' https://%s%s -o /tmp/_verify.html -w '%%{http_code}'"
            % (UA, domain, path))
        status = out.strip()[-3:] if out else "???"
        print("  [%-10s] %-12s %s" % ("verify", path, status))
        if status != "200":
            failed = True
            continue
        if args.verify_marker:
            _, count_out = r.run("grep -c -- '%s' /tmp/_verify.html" % args.verify_marker)
            count = (count_out or "0").strip() or "0"
            hit = count.isdigit() and int(count) > 0
            print("  [%-10s] marker       %s (%s hits)" % ("assert", "found" if hit else "MISSING", count))
            if not hit:
                failed = True

    r.cli.close()
    if failed:
        print("VERIFY FAILED - rollback with: cp %s/%s.bak-%s %s/%s"
              % (shell_theme, args.remote_name, stamp, shell_theme, args.remote_name))
        sys.exit(2)
    print("done")


if __name__ == "__main__":
    main()
