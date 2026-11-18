# P1 — Naming and information architecture

This is the stage everyone skips and the one that decides whether the site works in year two. It is also the cheapest stage to get right and the most expensive to fix later, because renaming a product after 40 pages point at it means 40 edits and a redirect map.

## The problem this solves

A physical product has more than one name. Three vocabularies collide:

- **The factory's name** — what the production line calls it, usually a functional or historical label.
- **The buyer's name** — what the person ordering it calls it, which is usually based on shape and use, not mechanism.
- **The platform's name** — what marketplaces and directories call it, which is usually generic and competitive.

If you pick one and use it everywhere, you lose the searches that use the others. If you use all of them on every page, you compete with yourself: two pages target the same phrase, search engines pick one, and the other disappears. This is the single most common self-inflicted wound in B2B product sites.

The fix is a **naming matrix**: an explicit table saying which name owns which slot on which page. Not a keyword list. An ownership record.

## Input

| You need | If missing |
|---|---|
| The full product range, with internal names | Build it from the catalogue and the factory's model list |
| A sense of how buyers actually search | Ask sales for the words customers use in emails; supplement with a search operator check |
| Competitor category structures | Look at the top three organic results for the head term |
| Existing URL inventory | Export from the sitemap before changing anything |

## Deliverable

Two artifacts.

**1. The naming matrix.** One row per trade name, one column per slot.

```
| Name | Role | Owns title on | Owns H1 on | Owns URL | Body/alt only |
|------|------|---------------|------------|----------|---------------|
| A    | generic umbrella | home, category root | home | /products/ | — |
| B    | shape-specific | product pages of that shape | same | /products/b/ | alt, H2 |
| C    | function-specific | one landing page | same | /c/ | body |
| D    | secondary | never | never | never | H2, alt only |
```

**2. The URL and category tree.** Written down before a single page is built.

```
/products/                     ← umbrella, lists everything
/products/{shape-family}/      ← one per family, 6–12 products each
/product/{model-slug}/         ← one per model, singular
/{use-case}/                   ← landing pages that cut across families
```

## Rules that prevent the collision

**One name owns one slot.** A name may own `title` on a set of pages, or appear in body copy, but not both on the same page. If a page's title says "X" and its H1 says "Y", you have told the search engine two different things about the same page.

**The primary name appears at most once per page in a primary slot.** Title, H1, and the first H2 are primary slots. Repeating the head term in all three is not reinforcement, it is a signal of thin content. Use the second slot for the qualifying attribute — size, drive type, configuration — instead.

**No three consecutive articles share a primary name.** If three published pieces in a row all target the same head term, the third one cannibalises the first two. Rotate deliberately, and record the rotation so you can see it.

**Product page metadata uses the name that belongs to that model's shape**, never the umbrella term. The umbrella term already has an owner (the category page); using it on 40 product pages dilutes the category page and leaves every product page competing with its own parent.

**Secondary names go in H2, body and image alt only.** They still get indexed, and they capture the long tail without fighting for a primary slot.

## URL conventions

Pick these once and never negotiate again:

- **Product detail pages: singular.** `/product/{slug}/`. Plural is reserved for the listing. Mixing them produces a 404 that looks like a working page because a catch-all template answers it.
- **Category listings: plural.** `/products/`, `/products/{family}/`.
- **Lowercase, hyphenated, ASCII.** No model numbers with slashes — a model sold as `X100A/B` becomes `x100a-b` in the URL, not `x100a/b`.
- **No dates, no years, no version numbers in URLs** unless the content is genuinely annual. A URL with a year has to be redirected every January.
- **One canonical form per page.** If a page is reachable at two paths, pick one and redirect the other with a 301, not a canonical tag alone.

For a non-Latin market, decide whether the URL slug is transliterated or localised. Localised slugs rank better for local queries but break every internal link you have already written. Decide before launch, not after.

## Category tree depth

Three levels is the practical maximum: root → family → product. A fourth level (root → family → sub-family → product) is only worth it when a family has more than about 25 products and the sub-families have genuinely different buyer intent.

The test: **can a buyer reach any product in three clicks from the home page?** If not, either the tree is too deep or the navigation is wrong.

A family with fewer than four products should be merged upward. An empty or near-empty category page is a thin page, and a site full of thin category pages drags the whole domain.

## Long-tail templates

Once the matrix exists, long-tail pages are generated from formulas rather than invented:

```
{name} + wholesale
{name} + manufacturer
{name} + OEM / custom
{name} + for {venue}
{name} + {attribute}
{name} + {configuration}
```

Each formula produces one page **only if** the search result for that exact phrase is weak. Check it in P4 before building. Generating 30 formula pages and hoping is how sites get filtered for thin content.

## Checklist

- [ ] Every trade name in use is listed, including the ones only sales uses
- [ ] Each name has exactly one role and one set of owned slots
- [ ] No two published pages share a primary name
- [ ] Product page titles use their own shape name, not the umbrella
- [ ] URL pattern fixed for products (singular) and listings (plural)
- [ ] Model numbers with special characters have a defined slug transformation
- [ ] Category tree is at most three levels, every family has four or more products
- [ ] Every product reachable in three clicks
- [ ] Article rotation recorded for the last three published pieces
- [ ] Redirect map written for every URL that changes

## Failure modes

| Symptom | Cause | Where |
|---|---|---|
| Two pages alternate in rankings for the same phrase | Two names both claim a primary slot | `90` F-05 |
| New product page never ranks, category page loses position | Product page used the umbrella term already owned by the category | `90` F-05 |
| A product URL returns 404 while the listing works | Singular/plural mismatch | `90` F-08 |
| Traffic drops after a site-wide rename | Rename without a 301 map | `90` F-12 |
| Category pages get no traffic despite good products | Families too small, pages are thin | `90` F-06 |

## When to break these rules

The rules assume the names are genuinely interchangeable to buyers. They are not always. If two names describe products with different buyers, different price points and different use cases, they are two products, not two names — split the pages and drop the matrix for that pair.

The matrix is a tool for resolving genuine synonyms. It is not a reason to merge things that should be separate.
