# P0 — Baseline audit

Before you change anything, find out what you are standing on. Most wasted weeks in this work come from fixing the wrong layer: rewriting copy on a site that is not indexed, or tuning images on a site whose cache never updates.

An audit answers four questions and nothing else:

1. What is this site actually built on?
2. Is it indexed, and how much of it?
3. Is it fast enough to be judged on content?
4. Are the analytics telling the truth?

Everything else is a priority list, not an audit.

## Input

| You need | If missing |
|---|---|
| The domain, and whether it is live | If it is not live yet, skip to P1 — there is nothing to audit |
| Admin access, or at least a URL | Without admin, audit from outside; mark every server-side claim as unverified |
| A list of target markets | Assume English-speaking plus one EU language; adjust in P1 |
| Existing analytics access | Audit the tracking layer from the page source instead |

## Deliverable

A single table, one row per finding, with a severity and a fix owner. Not a PDF. Not a slide deck. A table someone can work from on Monday.

```
| # | Area | Finding | Evidence | Severity | Stage |
|---|------|---------|----------|----------|-------|
| 1 | Index | 41 URLs in sitemap, 9 indexed | site: query | High | P0 |
| 2 | Cache | PURGE returns 200 but page unchanged | curl diff | Critical | P5 |
| 3 | Tracking | Ads conversion fires on site search | click test | High | P6 |
```

## How to audit

### 1. Technical fingerprint

```bash
curl -sI https://example.com/ | egrep -i 'server|x-powered|via|x-cache|cf-'
```

Read the response headers for what sits in front of the origin. `x-cache: HIT` means a reverse proxy is serving cached HTML, and that single fact changes how you verify every future change (see P5). `server: nginx` plus a `via` header usually means Varnish or a CDN in front.

Then confirm the CMS and theme from the source, not from a guess:

```bash
curl -s https://example.com/ | grep -o 'wp-content/themes/[^/"]*' | sort -u
curl -s https://example.com/wp-json/ | head -c 300
```

A `wp-json` response confirms WordPress and exposes the site name and often the plugin surface. Check `/wp-json/wp/v2/types` for custom post types — a site with products modelled as posts instead of a custom type is a structural finding, because it constrains every future template.

### 2. Index status

Two numbers matter, and they are almost never equal: how many URLs you publish, and how many are indexed.

```bash
# published
curl -s https://example.com/sitemap.xml | grep -c '<loc>'
# indexed (manual, in a browser)
site:example.com
```

A sitemap that returns HTML instead of XML is a common failure — an SPA fallback or a WordPress 404 page served with status 200. Always check the content type:

```bash
curl -sI https://example.com/sitemap.xml | grep -i content-type
```

If the gap between published and indexed is large, check in this order: `robots.txt` blocking, `noindex` in the head, canonical pointing elsewhere, and duplicate content from parameter URLs. Do not start with content quality; it is almost never the first cause on a new site.

### 3. Hreflang integrity

For each language version, confirm all four tags are present and reciprocal, including `x-default`:

```bash
curl -s https://example.com/de/ | grep -o '<link rel="alternate"[^>]*>'
```

A cluster is broken if one member omits a tag, or if a language page points to itself with the wrong locale. Broken clusters do not fail loudly — they just quietly stop the alternate versions from ranking. Check every page in the cluster, not just the one you are editing.

### 4. Performance floor

You are not chasing a score. You are checking three things that a content site cannot survive:

- **Largest image on the page.** Anything over 300 KB above the fold is a fix.
- **Format.** JPEG where WebP is available is a fix.
- **Dimensions vs display size.** A 2000 px image rendered in a 600 px slot is a fix.

```bash
curl -s https://example.com/ | grep -oE 'src="[^"]+\.(jpg|png|webp)"' | sort -u
```

Record the worst offender, not the average. Averages hide the one image that ruins the page.

### 5. Tracking truth

Do not trust the dashboard. Open the page and watch the network panel, or read the source. The audit questions:

- Is a consent default set **before** any tag loads? (If not, EU traffic is being measured illegally and US traffic is being measured wrong.)
- Does the conversion tag fire once per genuine enquiry, and not on internal search?
- Is the same conversion counted twice by two different tags?

P6 covers how to fix this. In P0 you only record whether it is true.

## Checklist

Each item passes or fails on evidence, not opinion.

- [ ] Response headers captured, cache layer identified
- [ ] CMS, theme and custom post types identified from source
- [ ] Published URL count recorded from sitemap
- [ ] Sitemap content type confirmed as XML, not HTML
- [ ] Indexed count recorded from a search operator
- [ ] `robots.txt` and per-page `noindex` checked before blaming content
- [ ] Every language page's hreflang cluster checked for reciprocity and `x-default`
- [ ] Heaviest above-fold image identified with its file size
- [ ] Consent default verified in source, with its position relative to tag loading
- [ ] One conversion test performed manually, result recorded
- [ ] Every finding has a severity and a stage

## Failure modes

| Symptom | Likely cause | Where |
|---|---|---|
| Audit says "all pages return 200" and the site is visibly broken | Permission bits or a PHP fatal hidden by a fallback render | `90` F-01 |
| Every check passes but the change never appears | Purge went to the wrong port | `90` F-02 |
| Sitemap count looks fine but nothing is indexed | Sitemap is a 200-status HTML fallback | `90` F-07 |
| Hreflang "looks right" but alternates never rank | One member of the cluster is missing a reciprocal tag | `90` F-09 |
| Analytics shows conversions that never happened | A non-form submit button matched the conversion selector | `90` F-11 |

## Anti-patterns

**Auditing with a cache-busting header.** You will verify the origin and conclude everything is fine, while visitors get stale HTML. Always test the way a visitor arrives: bare URL, browser user agent.

**Treating a plugin list as the audit.** The plugin list is inventory. The audit is what is broken.

**Reporting averages.** "Average image 180 KB" hides the 1.4 MB hero. Report the worst case and the count over threshold.
