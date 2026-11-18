# Asset: monthly health checklist

Run this on the 1st of every month. Fifteen minutes. It catches the failures
that accumulate silently — stale caches, expired certificates, drifted
templates, tracking drift — while they are still cheap.

## Index and crawl

- [ ] `site:example.com` count is within ~10% of the sitemap URL count
- [ ] Sitemap returns `application/xml` with the expected URL count
- [ ] No new `noindex` pages (grep the templates if the count drops)
- [ ] `robots.txt` still declares the sitemap and does not block a content path

## Site health

- [ ] Home page HTML contains a theme asset reference (proves the theme loads)
- [ ] Theme directory mode is `755` (run `scripts/fix_permissions.py --check`)
- [ ] Certificate valid for at least 3 more weeks
- [ ] Page weight: no above-fold image over 300 KB
- [ ] One form submitted from a fresh incognito session; enquiry arrives

## Tracking

- [ ] Conversion test matrix on the live site (click / Enter / empty / search / double)
- [ ] GA4 `generate_lead` count within ~15% of Ads conversions for last month
- [ ] Both within ~15% of actual enquiries in the inbox — the inbox is the truth
- [ ] Consent banner still appears from an EU IP, and decisions are being logged

## Content

- [ ] Rotation log updated: which names owned primary slots this month
- [ ] No three consecutive articles share a primary name
- [ ] All articles' internal links spot-checked (sample 20)
- [ ] Any page losing traffic gets a diagnosis, not a rewrite

## Hygiene

- [ ] Named backups older than one month deleted from the server
- [ ] Staging/tracked copies in sync (`diff` the templates you touched this month)
- [ ] Failure library: any new incident from this month written up
- [ ] Dependency versions noted (WordPress, PHP, plugin majors) — upgrade deliberately, never via auto-update on a production theme

## Why this exists

Three of these lines exist because of a specific outage: the permission line
exists because a `chmod -R 644` took a site offline for an hour; the form line
exists because expired nonces behind a cache silently rejected enquiries for
days; the tracking lines exist because site-search submits were counted as
leads and the numbers looked excellent while the inbox stayed empty.
