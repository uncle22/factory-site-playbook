---
name: factory-site-playbook
description: Build or rebuild a B2B export website on WordPress, end to end. Use when the task involves launching a manufacturer site from scratch, auditing an existing export site, structuring product data across many models, building multilingual landing pages, writing and publishing SEO articles at scale, deploying theme files safely, or debugging a site that returns 200 while being broken. Triggers on "B2B website", "export site", "factory website", "manufacturer site", "product catalogue site", "WordPress theme deploy", "hreflang", "multilingual landing page", "product data structure", "keyword difficulty", "cache purge not working", "site down but 200".
---

# Factory Site Playbook

Six stages, P0 to P6, plus two cross-cutting rule sets. Each stage has a reference file with input, deliverable, checklist and failure modes. Do not skip P1 and P2 — they are the ones that decide whether the site is maintainable in year two.

## Who this is written for

This is a practitioner's playbook, not a tutorial. It assumes you already know how a website is built and how search works, and that what you are missing is the part nobody writes down: the sequence, the failure modes, and the rules that only become obvious after a site has been live for a year.

Assume competence with all of the following before using it:

- HTML and one templating language. The examples are PHP because WordPress is the assumed stack, but the reasoning is portable.
- SSH, a file transfer tool, and the command line.
- The vocabulary of technical SEO: canonical, hreflang, sitemap, structured data, log files.
- WordPress administration from the database side, not just the admin UI.
- Analytics and consent concepts well enough to read a conversion report and doubt it.

Out of scope, deliberately: installing WordPress, choosing a theme, buying a domain, picking plugins, writing copy for you. There are ten thousand pages covering those. This one starts where they stop.

If you are looking for a step-by-step guide to putting a small business site online for the first time, this will read as hostile. It is not written for that.

## Routing

Match the request to a stage, then **read that reference file before acting**. Do not work from this file alone.

| If the task is… | Stage | Read |
|---|---|---|
| Starting from nothing, or "is this site any good" | P0 Baseline audit | `references/00-audit.md` |
| Naming a product, choosing URLs, structuring categories, fixing duplicate or competing page titles | P1 Naming and IA | `references/01-naming-ia.md` |
| Adding products, changing specs, reorganising a product list, image sizing | P2 Product data | `references/02-product-data.md` |
| Building a landing page, a product template, a language version, a form, schema markup | P3 Templates and i18n | `references/03-templates-i18n.md` |
| Choosing article topics, writing or commissioning content, checking internal links | P4 Content engine | `references/04-content-engine.md` |
| Uploading a file to a server, clearing cache, "the change did not appear" | P5 Deploy and cache | `references/05-deploy-cache.md` |
| Setting up analytics, consent, conversion tracking, "are we measuring this right" | P6 Measurement | `references/06-measurement.md` |
| Auditing metadata, indexing, hreflang, internal links, keyword difficulty on a page | Cross-cutting | `references/07-seo-rules.md` |
| Structuring a page so an answer engine quotes it, writing FAQs, entity naming | Cross-cutting | `references/08-geo-rules.md` |
| Something broke and the symptom does not match the cause | Any | `references/90-failure-library.md` **first** |

If two stages apply, do P0 or P5 first when the site is unknown or unstable, content stages otherwise. The two cross-cutting files are checklists, not stages: run them at the end of P1, P3 and P4 rather than in sequence.

## Non-negotiable rules

These came from real outages. They apply even when the user asks otherwise, and even when the shortcut looks safe.

1. **Never `chmod -R 644` a directory tree.** Directories need `755`. A blanket `644` removes the execute bit, PHP cannot enter the directory, and WordPress silently falls back to a bare render while every page still returns 200. If a deploy script touches permissions, it must do `find -type d -exec chmod 755` and `find -type f -exec chmod 644` separately.

2. **Verify with a bare URL and a browser user agent.** A cached response never executes PHP, so any check that relies on a cache-bypassing header will pass on a page that is broken for visitors.

3. **Send cache purges to 443 at the origin, not port 80.** Port 80 usually answers with a 301, and a redirect drops the `PURGE` method. A `200` from a purge request is not evidence that anything was purged.

4. **Back up before every overwrite.** Remote copy with a timestamped suffix, not a local copy. Rollback has to be one command.

5. **Never let staging and production templates drift.** If a template is edited on the server, write it back to the tracked copy in the same session. Drift surfaces weeks later as a page that "lost" a feature.

6. **One product name per slot.** A product with several trade names needs an explicit owner for `title`, `H1`, `URL` and body. Two pages competing for the same phrase is the most common self-inflicted SEO wound in this sector.

7. **Do not publish specifications you cannot source.** Leave the field empty with a note rather than filling it with a plausible number. A wrong load rating travels to the buyer's insurer.

8. **Never expose credentials in a script.** Environment variables only, never committed, never echoed into logs.

9. **A quantity without its condition is a future dispute.** "Up to 200 kg" is a different claim from "200 kg". Write the condition into the same sentence as the number, or leave the number out.

10. **Every paragraph must survive being lifted out of context.** Answer engines retrieve passages, not pages. A paragraph that needs the one before it to make sense is a paragraph nobody will ever quote, and it is also the paragraph a skimming buyer misreads.

## Stage contract

For every stage, produce all four of these, in this order:

1. **Input** — what you must know before starting, and what to do when it is missing.
2. **Deliverable** — the artifact, with the required fields.
3. **Checklist** — pass/fail items, each one verifiable by a command or a screenshot, not by opinion.
4. **Failure modes** — what usually goes wrong at this stage, and the pointer into the library.

## Reporting

State what you verified and how. "Deployed" is not a report. "Uploaded, `php -l` clean, cache purged on 443, verified with a bare URL at 1440 px and 390 px, product count 48, sitemap 101 URLs" is a report.

When a check fails, say which check and what it returned. Do not summarise a failure as a success with reservations.

## Provenance

Maintained by **YB-L** ([@uncle22](https://github.com/uncle22)), from the work of building and maintaining B2B export sites for manufacturers in southern China. Every rule in the failure library came from a live site, at the point where it broke.

