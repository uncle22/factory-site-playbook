# S — SEO rules that survived contact with a live site

This file is the consolidation layer. P1 covers naming and P4 covers content production; this one is the checklist you run against a page before and after publishing, plus the rules that do not belong to any single stage.

Read it as pass/fail. Every item here can be verified with a command, a crawler or a screenshot. Nothing here is a matter of taste.

## Input

- A live URL, or a draft about to go live.
- The primary phrase the page is supposed to win, written down in one sentence.
- Access to the rendered HTML, not the editor preview.

If you cannot state the primary phrase in one sentence, stop. A page without a declared target will compete with itself or with a sibling page, and you will find out six months later.

## Deliverable

One audit row per URL, filled from the rendered HTML rather than the admin screen:

| URL | Primary phrase | `title` | Chars | Desc chars | Canonical | Indexable | Int. links | `allintitle` | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| `/example-page/` |  |  |  |  |  |  |  |  | pass / fix |

Ten to fifteen rows is a realistic audit for a small catalogue. The verdict column is the only one that requires judgement; the rest are copied from a crawler, and a row with blanks is an unfinished audit, not a passing one.

## The five placement rules

1. **One primary phrase owns `title`, `H1` and the URL slug.** Secondary phrases go into `H2`, body copy and image `alt`. A secondary phrase must never appear in the `title` of a page whose sibling already owns it.

2. **Same phrase, same slot, once per page.** If a trade name appears in the `H1`, do not repeat it in the first `H2` as well. Repetition in the title block is the most common way a page reads as spam to a human and as duplication to a crawler.

3. **`title` and `H1` are different assets and should not be identical strings.** The `title` is written for the result page: it can carry the brand and a modifier. The `H1` is written for the visitor who already clicked. Identical is survivable; identical on twenty pages is a template problem.

4. **Lengths.** `title` 50 to 67 characters including the brand suffix. `meta description` 150 to 158 characters, cut on a word boundary. `H1` under 70. These are not ranking factors, they are truncation limits, and truncated text loses the modifier that made the click.

5. **The slug never changes after launch.** If it must change, the redirect is 301, single hop, and the old URL is removed from the sitemap in the same deploy. Chains of two or more hops are a self-inflicted crawl budget leak.

## Metadata has one source of truth

The failure pattern is a page where `title`, `og:title`, the `H1` and the meta description are edited in four different places and drift apart. Pick one:

- **Derived.** `title` from the post title plus a pattern, description from the excerpt, `og:*` from the same values. Cheapest to maintain, loses per-page control.
- **Stored.** An explicit SEO title and description field per page, with the derived value as fallback when empty. Keeps control, and needs a review step so empty fields do not silently ship.

Whichever you pick, the rendered page must show the value you set. Verify by fetching the HTML, not by looking at the admin screen. A field that saved but is not read by the template is a very common half-finished feature:

```bash
curl -s -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36" \
  https://example.com/page/ | grep -o '<title>[^<]*</title>'
```

If you are on WordPress, note that `wp post update <id> <file>` replaces the **entire** body. Changing a title with that command will silently wipe the content. Use `--post_title` on its own.

## Indexing and crawl

- **Do not assume `/sitemap.xml` exists.** Read `robots.txt`, take the `Sitemap:` line, then count the URLs in that file. Sites built by plugins often have a sitemap that omits custom post types, and a sitemap with the right total but the wrong members looks healthy in every dashboard.
- **Count published versus count in sitemap.** A gap of more than a couple of URLs means something is excluded on purpose or by accident, and you should know which.
- **Canonical is self-referential** on every indexable page. A canonical pointing at a parent page de-indexes the child without any warning.
- **No `noindex` on a page you intend to rank**, including the second language version. This is easy to ship accidentally when a template inherits a staging flag.
- **404 means 404.** A soft 404 that returns `200` with "not found" in the body is indexed as thin content.

## Hreflang, when there is more than one language

The cluster must be closed and reciprocal:

- Every language version lists **all** versions, including itself.
- `x-default` points at the version you want a language-less visitor to land on.
- A page that exists in three languages emits four tags, not three.
- The tags live in `<head>`, absolute URLs, no redirects in the target.

One missing return tag breaks the whole cluster for that page pair, and the symptom is mild: the wrong language ranks in the wrong market, and nothing in Search Console screams.

## Internal links

Internal links are the only ranking signal you fully control. Treat them like a build artifact:

- 8 to 12 contextual links into a new article, all to pages that already exist and return `200`.
- Anchor text is the target page's primary phrase, not "read more", not the URL.
- Links inside the body, not only in a footer block. Footer links are discounted.
- **Validate before publishing.** Crawl the list and fail the publish if anything is not `200`:

```bash
python scripts/check_links.py --urls urls.txt
```

- A link to a page that 301s passes a naive check and still wastes the signal. Follow redirects and report the final URL.

## Images

- `width` and `height` attributes on every `<img>`. Missing dimensions is the cheapest source of layout shift.
- `alt` describes the object and its context in one line. It is not a keyword field; three keyword variants in one `alt` reads as manipulation.
- `loading="lazy"` everywhere except the first viewport.
- **`og:image` must be JPEG or PNG, 1200×630.** WebP is not rendered by several social and messaging clients, and the preview silently falls back to a grey box. This is a real failure in the library, not a theoretical one.
- Article images at 100% container width. If a legacy rule caps post images at 380–420 px, a map or a spec diagram becomes unreadable and the mobile share fails with it.

## Structured data

- Mark up what is visibly on the page. `Product`, `FAQPage`, `BreadcrumbList` are the three that pay for themselves on a B2B catalogue.
- `FAQPage` only where the questions and answers are actually rendered. Hidden `FAQPage` markup is a manual-action risk.
- Do not attach properties to a type that does not accept them just because the schema validator is lenient. An `inLanguage` on an `ItemList` is the kind of thing that passes local validation and fails at scale.
- After any product data edit, re-fetch the rendered page and confirm the markup still parses. A single unescaped `&` in a value will silently kill the whole block.

## Difficulty, before writing

Run the operator check on the exact phrase, not on the head term:

```
allintitle:"your exact phrase"
```

- **Under 100 results** — the phrase is contestable by a site of any age with a competent page.
- **100 to 300** — needs the phrase in the title plus several supporting pages linking in.
- **Over 300** — you are competing with established authority. Either pick a longer phrase or accept a 12-month horizon.

`scripts/allintitle.js` automates this. Rate-limit yourself: one query every 20 to 30 seconds, and stop when you get a challenge page. The count is a signal, not a measurement.

## Cannibalisation check

Before publishing, search your own site for the primary phrase:

```bash
curl -s "https://example.com/?s=your+phrase" | grep -o '<h2[^>]*>[^<]*</h2>' | head
```

If two pages have the phrase in `title`, one of them loses. Decide which, demote the other to a secondary phrase, and update its internal links. Do this at publish time, not after both have six months of history.

## Checklist

- [ ] Primary phrase declared, in one sentence.
- [ ] Primary phrase in `title`, `H1`, slug, first 100 words.
- [ ] No sibling page owns the same phrase in `title`.
- [ ] `title` ≤ 67 characters, `meta description` ≤ 158, both cut on a word boundary.
- [ ] `title`, `og:title`, `H1` and description consistent with each other.
- [ ] Canonical self-referential; page not `noindex`.
- [ ] Page appears in the sitemap named in `robots.txt`; count matches published count.
- [ ] Every language version emits the full hreflang set including `x-default`.
- [ ] 8 to 12 internal links, all `200` after following redirects.
- [ ] Every `<img>` has `width`, `height`, `alt`; `og:image` is JPEG/PNG at 1200×630.
- [ ] Structured data parses on the rendered page.
- [ ] `allintitle` count recorded, with the date.
- [ ] Verified on the live URL with a browser user agent and a bare URL, at 1440 px and 390 px.

## Failure modes

| Symptom | Likely cause | Entry |
|---|---|---|
| Page is live, not indexed after three weeks | canonical points elsewhere, or `noindex` inherited from a template | F-07 |
| Two pages alternate in rankings | same phrase in two `title` tags | F-05 |
| Shared link shows no image | `og:image` is WebP, or the tag is absent | F-17 |
| Description truncated mid-word in results | description generated by character count, not word boundary | F-22 |
| Rich result disappears after a data edit | unescaped character broke the JSON-LD block | F-18 |
| Only one language ranks | hreflang cluster not reciprocal | F-09 |
| Category page gets nothing while products rank | category page has no unique phrase, only a product list | F-06 |
| New article flat for months | topic chosen on volume, phrase not contestable | F-20, F-24 |

## Anti-patterns

- Adding a keyword to `alt` text of a decorative image.
- Publishing a page with a placeholder description and meaning to fix it later.
- Redirecting an old URL to the homepage instead of its closest equivalent.
- Trusting the CMS preview for `title` and description; previews do not render the SEO layer.
- Chasing a head term because it has volume, when the long-tail phrase converts and ranks in three weeks.
