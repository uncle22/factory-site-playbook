#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose and repair WordPress theme permissions.

The failure this prevents: `chmod -R 644` on a directory tree. Directories need
the execute bit to be traversed. Without it PHP cannot enter the theme directory,
and WordPress renders a bare fallback page while still returning HTTP 200.

Correct state:
    directories  755
    files        644

Environment:
    DEPLOY_HOST, DEPLOY_USER, DEPLOY_PASS (or DEPLOY_KEY), WP_ROOT, THEME_DIR

Usage:
    python fix_permissions.py --check            # report only, changes nothing
    python fix_permissions.py --fix              # repair
    python fix_permissions.py --fix --dry-run    # show the commands, run nothing

Exit codes: 0 clean (check) or repaired (fix); 4 problems found in check mode.
"""
import argparse
import os
import sys

try:
    import paramiko
except ImportError:
    sys.exit("paramiko is required: pip install paramiko")


def env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        sys.exit("missing required environment variable: %s" % name)
    return value


def connect():
    host = env("DEPLOY_HOST", required=True)
    user = env("DEPLOY_USER", required=True)
    key = os.environ.get("DEPLOY_KEY")
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if key:
            cli.connect(host, 22, user, key_filename=key, timeout=30)
        else:
            cli.connect(host, 22, user, env("DEPLOY_PASS", required=True), timeout=30)
    except Exception as exc:
        sys.exit("connection failed: %s" % exc)
    return cli


def run(cli, cmd, timeout=240):
    _, out, err = cli.exec_command(cmd, timeout=timeout)
    stdout = out.read().decode("utf-8", "replace")
    stderr = err.read().decode("utf-8", "replace")
    out.channel.recv_exit_status()
    return stdout, stderr


def main():
    ap = argparse.ArgumentParser(description="Check or repair WordPress theme permissions.")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="report only")
    group.add_argument("--fix", action="store_true", help="repair to 755/644")
    ap.add_argument("--path", default=None,
                    help="absolute theme path; defaults to WP_ROOT/wp-content/themes/THEME_DIR")
    ap.add_argument("--dry-run", action="store_true", help="print commands without running them")
    args = ap.parse_args()

    wp_root = env("WP_ROOT", required=True).rstrip("/")
    theme_dir = env("THEME_DIR", required=True).strip("/")
    path = args.path or "%s/wp-content/themes/%s" % (wp_root, theme_dir)

    cli = connect()

    # --- diagnosis -------------------------------------------------------
    print("theme path: %s" % path)

    out, _ = run(cli, "test -d '%s' && echo yes || echo no" % path)
    if out.strip() != "yes":
        sys.exit("path does not exist on the server: %s" % path)

    out, _ = run(cli, "stat -c '%%a %%U:%%G' '%s'" % path)
    root_mode = out.strip()
    print("root:       %s" % root_mode)

    # a directory without the execute bit cannot be traversed by PHP
    root_octal = root_mode.split()[0] if root_mode else ""
    root_broken = len(root_octal) >= 3 and (int(root_octal[-1]) & 1) == 0

    bad_dirs_out, _ = run(
        cli,
        "find '%s' -type d ! -perm -u+x -printf '%%m %%p\\n' 2>/dev/null | head -20" % path)
    bad_files_out, _ = run(
        cli,
        "find '%s' -type f ! -perm -u+r -printf '%%m %%p\\n' 2>/dev/null | head -20" % path)

    bad_dirs = [l for l in bad_dirs_out.splitlines() if l.strip()]
    bad_files = [l for l in bad_files_out.splitlines() if l.strip()]

    total_dirs_out, _ = run(cli, "find '%s' -type d | wc -l" % path)
    total_files_out, _ = run(cli, "find '%s' -type f | wc -l" % path)
    print("counts:     %s dirs, %s files"
          % (total_dirs_out.strip() or "?", total_files_out.strip() or "?"))

    if root_broken:
        print("\nCRITICAL: root directory is %s, missing the execute bit." % root_octal)
        print("          PHP cannot traverse it. The site will render a bare fallback")
        print("          page while still returning HTTP 200. Fix this first.")
    if bad_dirs:
        print("\ndirectories without execute permission (%d shown):" % len(bad_dirs))
        for line in bad_dirs:
            print("  " + line)
    if bad_files:
        print("\nfiles without read permission (%d shown):" % len(bad_files))
        for line in bad_files:
            print("  " + line)

    problems = bool(root_broken or bad_dirs or bad_files)
    if not problems:
        print("\npermissions look correct")
        cli.close()
        sys.exit(0)

    if args.check:
        print("\nno changes made (--check). re-run with --fix to repair.")
        cli.close()
        sys.exit(4)

    # --- repair ----------------------------------------------------------
    cmds = [
        ("dirs  -> 755", "find '%s' -type d -exec chmod 755 {} \\;" % path),
        ("files -> 644", "find '%s' -type f -exec chmod 644 {} \\;" % path),
    ]
    if args.dry_run:
        print("\nwould run:")
        for label, cmd in cmds:
            print("  [%s] %s" % (label, cmd))
        cli.close()
        return

    print()
    for label, cmd in cmds:
        run(cli, cmd)
        print("  [%-12s] applied" % label)

    # --- verify ----------------------------------------------------------
    out, _ = run(cli, "stat -c '%%a' '%s'" % path)
    after = out.strip()
    print("\nroot now: %s" % after)

    remaining_dirs, _ = run(cli, "find '%s' -type d ! -perm -u+x | wc -l" % path)
    remaining_files, _ = run(cli, "find '%s' -type f ! -perm -u+r | wc -l" % path)
    print("remaining: %s dirs, %s files without permission"
          % (remaining_dirs.strip(), remaining_files.strip()))

    domain = os.environ.get("SITE_DOMAIN")
    if domain:
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
        run(cli, "cd '%s' && wp cache flush --allow-root >/dev/null 2>&1" % wp_root)
        run(cli, "curl -sk -o /dev/null --resolve %s:443:127.0.0.1 -X PURGE https://%s/"
            % (domain, domain))
        out, _ = run(cli, "curl -sk -A '%s' https://%s/ -o /dev/null -w '%%{http_code}'"
                     % (ua, domain))
        print("home page: HTTP %s" % out.strip())
        print("           a 200 alone does not prove the theme is loading.")
        print("           confirm a theme asset appears in the HTML.")

    cli.close()
    print("done")


if __name__ == "__main__":
    main()
