# Factory Site Playbook

A production playbook for building a B2B export website on WordPress — the kind a real factory needs, not the kind an agency sells.

It is written as an agent skill: drop the folder into a coding agent's skills directory and it will route work through six stages. Read it as a document and it works too.

> **Licence split, up front.** `scripts/` is MIT. Everything you read — `references/`, `assets/`, `SKILL.md`, both READMEs — is **CC BY-NC-SA 4.0**: attribution to YB-L, no commercial redistribution, adaptations stay open. See [Licence](#licence).

Built and maintained by **[YB-L](https://github.com/uncle22)** from the work of building and maintaining B2B export sites for manufacturers in southern China. The methods are here; the commercial details deliberately are not.

---

## Read this before you clone it

This is a **practitioner's playbook, not a course.** It is written for someone who already knows how to build a site and how search works, and needs the part that is not in the tutorials: the order of operations, the failure modes, and the rules you only learn after a site has been live for a year.

You will get value from it if you are comfortable with:

- HTML and a templating language — the examples are PHP, the reasoning is stack-agnostic
- SSH, SFTP, and a command line
- Technical SEO vocabulary: canonical, hreflang, sitemap, structured data, crawl budget
- WordPress beyond the admin panel — `wp-cli`, the database, theme files
- Analytics and consent well enough to distrust a conversion report

It will **not** teach you how to install WordPress, pick a theme, buy a domain, choose plugins, or write your first article. Those are covered everywhere else. This starts where those stop.

If you are putting a site online for the first time, the failure library will read as alarming and the checklists as excessive. That is because they were written by someone who had already been burned.

## Why this exists

Most "how to build a B2B website" content is written by people who have never shipped one. It lists plugins, recommends themes, and stops before the part that actually breaks.

This playbook is the opposite. Every rule in it is attached to something that went wrong on a live site with real traffic, real ad spend and real enquiries:

- A `chmod -R 644` on a theme directory took the whole site down while every page still returned HTTP 200 and every file still passed `php -l`.
- A cache purge sent to port 80 returned `200` and did nothing, because nginx answered with a 301 and swallowed the `PURGE` method. The cache stayed stale for weeks and we thought it was working.
- A full-page cache served pages containing expired form nonces, which silently rejected genuine enquiries for days.
- A pricing template was edited on the server but not in the staging copy, and the two drifted until a German landing page shipped with the wrong hero.

None of those are covered in a plugin tutorial. All of them are covered in [`references/90-failure-library.md`](references/90-failure-library.md).

## Where it fits

- An in-house marketer or developer inheriting a WordPress site from an agency that has left.
- A factory with a catalogue PDF and no site, where someone on staff can actually build one.
- A trading company whose site gets traffic and no enquiries.
- Anyone rebuilding the same site for a second product line instead of starting over.

It assumes WordPress, PHP templates, and a willingness to touch code. It does not assume a budget for enterprise tooling.

## The six stages, plus two rule sets

| Stage | What it produces | Reference |
|---|---|---|
| **P0 Baseline audit** | Technical fingerprint, index status, tracking verification, priority list | [`00-audit.md`](references/00-audit.md) |
| **P1 Naming and IA** | Naming matrix (one product, several names, one owner per slot), category tree, URL rules | [`01-naming-ia.md`](references/01-naming-ia.md) |
| **P2 Product data** | One array as the single source of truth, sort keys, spec fields, image pipeline | [`02-product-data.md`](references/02-product-data.md) |
| **P3 Templates and i18n** | Full-page templates, hreflang clusters, AJAX forms, structured data | [`03-templates-i18n.md`](references/03-templates-i18n.md) |
| **P4 Content engine** | Keyword difficulty checks, article skeleton, internal link validation, de-slopping | [`04-content-engine.md`](references/04-content-engine.md) |
| **P5 Deploy and cache** | Upload, lint, back up, purge two cache layers, verify with a bare URL | [`05-deploy-cache.md`](references/05-deploy-cache.md) |
| **P6 Measurement** | Consent defaults, dual tracking with deduplication, monthly reconciliation | [`06-measurement.md`](references/06-measurement.md) |
| **S SEO rules** | Placement, metadata, crawl, hreflang, links, images, difficulty, cannibalisation — as pass/fail | [`07-seo-rules.md`](references/07-seo-rules.md) |
| **G GEO rules** | Answer-first structure, extractable paragraphs, entity naming, FAQ form, citation monitoring | [`08-geo-rules.md`](references/08-geo-rules.md) |

Each stage has the same four parts: **input**, **deliverable**, **checklist**, **failure modes**. The failure modes point back into the library. The two rule sets are checklists rather than stages — run them at the end of P1, P3 and P4.

## Three entries from the failure library

**The site that returned 200 while being broken.** A batch permission change used `chmod -R 644` on a theme directory. Directories need the execute bit to be traversed, so PHP could not enter the theme, and WordPress fell back to rendering a bare page. Every URL still returned 200. Every file still passed `php -l`. The fix took four minutes once the cause was known; finding the cause took an hour, because the symptom pointed at code and the cause was a permission bit.

**The purge that reported success.** `curl -X PURGE http://example.com/` returned `200`, so the deploy script logged success. The request had been answered by nginx with a 301 redirect, and the redirect does not carry a `PURGE` method. Varnish never saw it. Everything deployed in that period was verified against stale HTML. The fix is to send `PURGE` straight to the origin on 443 with `--resolve`, and to verify with a bare URL and a browser user agent, because a cached page never executes PHP.

**The nonce that expired inside the cache.** A landing page form used a WordPress nonce for CSRF. With full-page caching enabled, the HTML containing the nonce was served to everyone for hours. Nonces expire, so by mid-afternoon every submission failed validation — and the form looked fine, because the failure happened server-side. The fix was to stop treating the nonce as a hard gate on cached pages and rely on a honeypot plus IP rate limiting instead.

## How to use it

**As an agent skill.** Copy the folder into your skills directory (`~/.claude/skills/`, `~/.workbuddy/skills/`, or equivalent). The `SKILL.md` frontmatter declares when it activates. The agent then loads the reference for the stage it is working on instead of guessing.

**As a manual.** Read P0 before you touch anything. Read P5 before your first deploy. Keep the failure library open the first time something breaks in a way that makes no sense.

**As a build order.** The stages are sequential on a new site and independent on an existing one. P1 and P2 are the ones people skip, and they are the ones that decide whether year two is maintainable.

## Scripts

| Script | Purpose |
|---|---|
| `scripts/site_audit.py` | Fingerprint a site: CMS, theme, plugins, index counts, response headers, hreflang |
| `scripts/check_links.py` | Crawl a list of URLs, report status codes and redirects |
| `scripts/allintitle.js` | Query Google's `allintitle:` operator headlessly and read the result count |
| `scripts/image_pipeline.py` | Resize to a square, convert to WebP, quality and method control |
| `scripts/deploy_theme_file.py` | Upload, lint, back up, purge, verify — with credentials in environment variables |
| `scripts/fix_permissions.py` | Diagnose and repair theme directory permissions (755 dirs, 644 files) |

All scripts read credentials from environment variables. Nothing is hardcoded.

## What is deliberately not here

This is a public playbook, so it documents method, not commercial data. Removed: product specifications, pricing, MOQ and payment terms, which models carry which certification, supplier and customer lists, keyword ranking positions and target keyword sets, ad account structure and spend, analytics property IDs, server addresses and credentials.

What stayed: the reasoning, the templates, the scripts, and every failure mode. Those are the parts that transfer to another industry.

## Licence

Two licences, split by file type.

- **`scripts/`** — MIT. Use them, modify them, ship them inside a paid service. Keep the copyright line.
- **Everything else** — `references/`, `assets/`, `SKILL.md`, both READMEs — **CC BY-NC-SA 4.0**. You may read it, use it on your own sites, translate it and adapt it to another industry. You may not sell it, bundle it into a paid product or a client deliverable, or publish a modified version under a different or more permissive licence. Attribution to **YB-L** with a link back is required.

Adapting it for your own industry and publishing your version is explicitly allowed, provided the result carries the same licence and credits this repository. Doing that and calling it your own original work is not.

Commercial licensing is a conversation, not a loophole: [open an issue](https://github.com/uncle22/factory-site-playbook/issues) or reach out via GitHub.

## Contributing

Issues and pull requests are welcome, particularly failure modes. If something in here is wrong for your stack, say so with the version numbers.

Note that contributions to the documentation are accepted under CC BY-NC-SA 4.0, the same licence it ships under. By opening a pull request you agree to that.
