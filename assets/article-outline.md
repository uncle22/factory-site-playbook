# Asset: article outline and pre-publish checklist

The structure used for every article on the site, plus the checklist that runs
before anything goes live. See `references/04-content-engine.md` for the reasoning.

## Structure

```
H1        the phrase, once, plus a qualifier
Lede      2-3 sentences: the situation, the surprise, what this resolves
          (nothing like "in today's competitive landscape")
CONTEXT   why this is harder than it looks
H2 x 5-9  one per decision the buyer makes, in the order they make it
TABLE 1-3 comparative data; this is what people screenshot
H2        "what this means for your order" - the bridge to the product
FAQ 6-9   questions the article did not answer inline
CTA       one specific action, with the destination page
```

Headings are decisions, not topics. "How much does it cost" works; "cost
considerations" does not. If a section could be deleted without breaking the
logic, it is filler.

## Topic gate (before writing anything)

- [ ] Checked with `allintitle:` in **Google** (not an engine that fakes the operator)
- [ ] Compared against two alternative phrasings in the same session
- [ ] Field is weak or competitive, and the site has an angle the top three lack
- [ ] Commercial path exists: a reader of this page can plausibly buy from us

## Before writing

- [ ] Naming matrix consulted: who owns this phrase's primary slot
- [ ] Rotation checked: no three consecutive articles share a primary name
- [ ] Spelling variety decided (American or British) and recorded if it deviates from the site default

## Before publishing

- [ ] H1 contains the phrase once
- [ ] Title tag ≤ 67 characters including the brand suffix, phrase first
- [ ] Meta description written in the excerpt field, 140-160 characters, not a title restatement
- [ ] At least one comparative table
- [ ] Three to six internal links, anchors describe the destination
- [ ] Every internal link returns 200 (run `scripts/check_links.py`)
- [ ] At least one inbound link added to an existing page
- [ ] Em dash count in body copy: 0
- [ ] No repeated `not X, but Y` construction
- [ ] No paragraph that is a three-item list in every sentence
- [ ] Conclusion does not restate the introduction
- [ ] Spelling scan for the opposite variety's markers
- [ ] Featured image: JPEG/PNG for social, 1200 x 630, not the WebP hero
- [ ] Facts sourced; anything uncertain hedged rather than asserted

## Publish mechanics

```bash
wp post create article.html \
  --post_title="..." \
  --post_name="slug-without-year" \
  --post_status=publish \
  --post_category=<buying-guides-id> \
  --post_author=<author-id> \
  --post_excerpt="the meta description text"
```

**Any string containing `$` goes in single quotes or a file.** Double quotes
let the shell expand `$54` into `4`, and you will publish a price that is
wrong by two orders of magnitude with no error anywhere.

Set the SEO title and featured image as post meta in a second step. Then
purge the sitemap cache on 443 and confirm the new URL appears.

## After publishing

- [ ] Live URL shows the correct title tag, description, og:image
- [ ] Body rendered (not escaped, not truncated) — read one paragraph in the browser
- [ ] URL present in the sitemap after purge
- [ ] Screenshots at 1440px and 390px
- [ ] Topic and difficulty number recorded for the rotation log
