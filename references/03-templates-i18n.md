# P3 — Templates, multilingual pages, forms and schema

By this stage the data exists (P2) and the names are decided (P1). P3 turns that into pages a visitor can land on, in more than one language, with a form that actually reaches an inbox and markup that search engines can read.

## Input

- **A settled product data source from P2.** If the array shape is still moving, every template edit is throwaway work. Templates read the array; they never contain product facts.
- **A template layering decision**, written down: child theme over a parent, or a custom theme. Without it the next person adds a file in the wrong layer and cannot see why nothing changes.
- **The language list, with one declared master** — which version is written first, and which language a visitor with no detectable preference lands on.
- **A form endpoint that already exists server-side.** Do not build a form whose handler is still a TODO.
- **The schema types you intend to emit**, chosen before markup is written rather than retrofitted.

If the language list is still open, settle it first. Retrofitting hreflang onto finished templates is a week of careful work; building it in is an afternoon.

## Deliverable

1. **One full-page template per language version or landing page**, self-contained: own head block, own copy, own form action.
2. **A reusable hreflang block** that emits the complete cluster from one source, so a fourth language does not mean editing three templates.
3. **A form handler** with server-side validation, a honeypot and IP rate limiting, plus a documented decision about nonces on cached pages.
4. **A JSON-LD inventory**: which page type emits which schema, and where each value comes from.
5. **A drift note**: where the tracked copy of each template lives, and how a server-side hotfix gets written back.

Work order is templates, then translations, then schema. Schema goes last because it has to describe what the rendered page actually contains, and the copy is the last thing to stop moving.

## Template layering

Keep three layers apart, because mixing them is what makes a site impossible to hand over:

| Layer | Contains | Never contains |
|---|---|---|
| Data | Product arrays, FAQ arrays, copy strings | Markup |
| Template | PHP that loops over data, slots, conditionals | Copy decisions, business numbers |
| Style | One stylesheet per surface | Layout decisions made in inline styles |

A template that hardcodes a specification is a template you will edit 48 times. A stylesheet that carries layout is a stylesheet you will break when you change a page.

## Full-page templates vs the loop

WordPress gives you two ways to render a page: let the theme's page template run the loop on post content, or bypass it and render a whole page from a PHP template file.

**Use a full-page template when:** the page has a fixed structure you designed (a landing page, a language version, a process page), the content is not a paragraph a client will edit, and the layout has sections that would not survive a WYSIWYG editor.

**Use the loop when:** the page is editorial content that someone other than a developer will change.

Decide per page, not per site. A site where every page is a full-page template is unmaintainable; a site where every page runs the loop cannot produce a landing page that converts.

### The one line you must not delete

A full-page template still has to call `wp_footer()` before `</body>`. It injects queued scripts, and every tracking tag, analytics snippet and plugin hook depends on it. A template that renders perfectly without it will look correct, pass every visual check, and silently measure nothing.

Same for `wp_head()` in the head, for the same reason. If you are hand-writing the `<head>` to control title and meta, call `wp_head()` anyway and then override — do not omit it.

### Hand-written head, when you need it

Search engines and social platforms read different things. When the theme's output is wrong for a landing page, control it explicitly:

```php
<title><?php echo esc_html($seo_title); ?></title>
<meta name="description" content="<?php echo esc_attr($seo_desc); ?>">
<meta property="og:title" content="<?php echo esc_attr($og_title); ?>">
<meta property="og:image" content="<?php echo esc_url($og_image); ?>">
<link rel="canonical" href="<?php echo esc_url($canonical); ?>">
<?php wp_head(); ?>
```

Two details that cost an afternoon each if missed:

- **Social previews do not render WebP reliably.** The in-page hero can be WebP; the `og:image` should be a JPEG or PNG, 1200 × 630.
- **Open Graph tags must be absolute URLs.** A relative path silently produces no preview card, and no error.

## Multilingual clusters

A language version is not a translation of a page. It is a page that stands on its own, in a cluster with the others.

**Every page in the cluster emits every tag, including a self-reference and `x-default`:**

```html
<link rel="alternate" hreflang="en" href="https://example.com/">
<link rel="alternate" hreflang="de" href="https://example.com/de/">
<link rel="alternate" hreflang="fr" href="https://example.com/fr/">
<link rel="alternate" hreflang="x-default" href="https://example.com/">
```

Rules:

- **Reciprocal and complete.** If `/de/` lists three alternates, every one of those three must list `/de/` back. A one-way tag is ignored.
- **`x-default` points at the international version**, normally the English page. Omitting it is the most common cluster defect and it is invisible in a browser.
- **Do not put hreflang on pages that are not translations.** A landing page in one language is not a cluster of one.
- **The cluster, not the site, is the unit.** Adding a fourth language means editing every page's head in the existing three.

### Generating translations without drift

When a language page is a full translation of another full-page template, do not maintain two hand-edited files. Generate the second from the first with a script that walks the source and substitutes strings in order, then hand-review the output.

The reason is not speed, it is drift. Two hand-maintained templates diverge on the first urgent fix, and six months later one of them is missing a section that the other has. If a fix must go into both, the script is the only thing that reliably remembers.

Anchor IDs should be localised too (`#models` → `#modelos` → `#modele`). Shared anchors work, but a nav label in one language jumping to an anchor slug in another is the kind of detail that makes a site feel machine-translated.

## Forms that survive a cached page

A quotation form is the commercial point of the whole site. Two failure modes destroy it, and both look fine from the outside.

### Nonce expiry behind a full-page cache

The standard WordPress pattern is a nonce in the form for CSRF protection. With full-page caching, the HTML containing that nonce is served to everybody for hours. Nonces expire. By mid-afternoon every submission fails validation — and the visitor sees either a spinner or a generic thank-you, depending on how the handler reports errors.

You cannot have both a strict nonce and a cached page. Pick one:

- **Disable caching on the page** (acceptable for a contact page, expensive for a landing page you advertise to).
- **Keep the nonce, but treat failure as a log entry rather than a rejection**, and rely on other defences.

The second option is usually correct. Replace the nonce gate with:

- **A honeypot field**, hidden by CSS, that a human never fills.
- **An IP rate limit**, keyed on a hashed address, with a threshold that a real buyer never reaches.
- **A time-to-submit floor**, rejecting submissions under two seconds.

Log every rejected nonce so you can see whether the fallback is doing real work.

### Handler wiring

Use `admin-ajax.php` with separate actions per form, so one form's failure does not take out the other:

```php
add_action('wp_ajax_nopriv_lead', 'lead_handler');
add_action('wp_ajax_lead', 'lead_handler');
```

Return JSON with an explicit status, and have the front end show a real error instead of a fake success. A form that thanks the visitor for an enquiry that never arrived is worse than a form that shows an error.

## Structured data

Add JSON-LD for the things that exist on the page, and nothing else:

- **`Organization`** on the home page, once.
- **`Product`** on product pages, with `offers` only if a price is actually published.
- **`BreadcrumbList`** wherever breadcrumbs are visible.
- **`ItemList`** on category pages.
- **`FAQPage`** only where the questions are visible on that page.

Two constraints learned the hard way:

- **`ItemList` does not take `inLanguage`.** Adding it fails validation and takes the whole list out of eligibility, which is worse than not marking it up at all.
- **Every marked-up field must be visible on the page.** A `Product` with a price in JSON-LD and no price on the page is a manual-action risk, not a rich-result opportunity.

Validate with the Rich Results test after every template change, not once at launch. A broken block usually arrives with a data change, not a template change.

## Checklist

- [ ] Every full-page template calls `wp_head()` and `wp_footer()`
- [ ] `og:image` is JPEG or PNG, 1200 × 630, absolute URL, and renders in a preview debugger
- [ ] Language cluster emits complete, reciprocal tags including `x-default`, on every page
- [ ] Translation pages are generated from the source, not hand-maintained
- [ ] Form posts to a dedicated AJAX action and returns a real error on failure
- [ ] Cached pages cannot silently reject submissions (honeypot + rate limit, or no cache)
- [ ] Honeypot tested: a filled honeypot is rejected, a real submission is not
- [ ] JSON-LD validates, contains no `inLanguage` on `ItemList`, and matches visible content
- [ ] 1440 px and 390 px screenshots taken, no horizontal overflow, no console errors
- [ ] Staging and production templates are byte-identical after the change

## Failure modes

| Symptom | Cause | Where |
|---|---|---|
| Page converts in testing, not in production | Missing `wp_footer()` | `90` F-03 |
| Enquiries stop arriving in the afternoon | Nonce expired inside a cached page | `90` F-16 |
| Shared link shows no image | WebP `og:image` or relative URL | `90` F-17 |
| Only one language ranks | Cluster not reciprocal, or `x-default` missing | `90` F-09 |
| Rich result disappears after a data edit | `ItemList` carrying `inLanguage` | `90` F-18 |
| A page lost a section nobody remembers removing | Staging/production drift | `90` F-19 |

## Anti-patterns

**Testing a form by clicking the button yourself.** You are one request with a fresh nonce. Test again after the page has been cached, or from a second browser profile hours later.

**Translating by pasting into a translation tool and pasting back.** The structure survives, the conversion copy does not. Translate the marketing sections deliberately; something in every language gets lost in a literal pass.
