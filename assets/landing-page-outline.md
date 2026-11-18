# Asset: multilingual landing page outline

Structure for a market landing page (`/de/`, `/fr/`, `/de/` …) built as a
full-page template. Written from a page that converts; the sections are in the
order that earned that result.

## Section order

```
1. HERO          headline + one-line promise + photo + one button
2. PROBLEMS      3-4 bullets naming the buyer's actual pain, in their words
3. PRODUCTS      grid of models for this market, 4-12 items
4. PROOF         one factory photo, one line about capacity, one line about QC
5. SPECS         comparison table, 5-8 rows, the models from section 3
6. TERMS         MOQ, lead time, shipping terms, payment - the four questions
7. COMPLIANCE    certifications that exist, with a caveat line
8. QUALITY       inspection process in 3 steps
9. FAQ           4-6 questions specific to this market
10. CONTACT      form + what happens after submission
```

## Rules that come from failures

- **Call `wp_head()` and `wp_footer()`.** Omitting `wp_footer()` silently
  removes every queued script, including conversion tracking. The page looks
  perfect and measures nothing.
- **Own the head.** Emit `<title>`, description, canonical and Open Graph
  explicitly, then call `wp_head()`. The `og:image` is a JPEG/PNG at
  1200x630 with an absolute URL — WebP does not render in several social
  scrapers, and a relative path produces no preview at all.
- **Emit the full hreflang cluster** on this page, including a self-reference
  and `x-default`. Every other member of the cluster must list this page back.
  Generate the block from one function; hand-written clusters are how
  non-reciprocal tags happen.
- **The form posts to its own AJAX action.** Do not share an action with
  another form; one failure should not take out both. Return JSON with an
  explicit status, and make the front end show real errors.
- **No nonce gate behind cache.** A cached page serves expired nonces, and
  submissions start failing in the afternoon. Honeypot + IP rate limit
  instead, with the rejection logged.
- **Anchor IDs are localised** (`#modelos`, `#modele`), matching the nav
  labels. A shared anchor slug is a machine-translation tell.
- **The page is generated from the source language template by a script,**
  then hand-reviewed. Two hand-maintained templates drift on the first
  urgent fix, and the drift surfaces months later as a missing section.

## Head block template

```php
<title><?php echo esc_html($seo_title); ?></title>
<meta name="description" content="<?php echo esc_attr($seo_desc); ?>">
<link rel="canonical" href="<?php echo esc_url($canonical); ?>">
<meta property="og:title" content="<?php echo esc_attr($og_title); ?>">
<meta property="og:description" content="<?php echo esc_attr($seo_desc); ?>">
<meta property="og:image" content="<?php echo esc_url($og_image); ?>">
<?php foreach ($cluster as $lang => $href): ?>
<link rel="alternate" hreflang="<?php echo esc_attr($lang); ?>" href="<?php echo esc_url($href); ?>">
<?php endforeach; ?>
<?php wp_head(); ?>
```

`$cluster` includes the page's own language and `x-default`.

## Pre-publish checklist

- [ ] `wp_head()` + `wp_footer()` present
- [ ] OG image renders in a social preview debugger
- [ ] Hreflang cluster complete, reciprocal, with `x-default`
- [ ] Form: dedicated AJAX action, JSON status, real error display
- [ ] Honeypot rejects a filled honeypot and passes a real submission
- [ ] JSON-LD: Organization on the page; no `inLanguage` on any ItemList
- [ ] Localised anchors match the nav labels
- [ ] 1440px and 390px screenshots, no horizontal overflow
- [ ] Conversion test matrix run on the live URL (click, Enter, empty, search, double)
