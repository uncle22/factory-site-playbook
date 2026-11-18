# P4 — The content engine

Publishing one good article is a project. Publishing fifty is a system. This stage is about the system: how topics get chosen, how articles get structured, how links get validated, and how the output avoids the two failure modes that kill B2B content — reading like a machine wrote it, and reading like a brochure.

## Input

- **The naming matrix from P1.** Every article's primary phrase has to come out of it. Writing an article against a phrase no page owns creates a competitor to your own site.
- **A candidate list already filtered by intent**, from sales calls, buyer emails and the questions that arrive before an order. Keyword tools supply volume; they do not supply the question.
- **An inventory of existing articles with their primary phrases**, so the new piece does not cannibalise one that already ranks.
- **A working publish path** — CLI or API access, category assignment, author assignment, excerpt field. If publishing is manual through a web editor, decide now who does it and how metadata gets set.
- **Someone who will read the draft as a buyer**, not as the author. Without that reader, tone drift goes unnoticed for twenty articles.

## Deliverable

1. **A topic table**: primary phrase, `allintitle` count with the date, supporting secondary phrases, which existing page links in, target publish week.
2. **An article skeleton** committed before drafting: `H2` sequence, the question each section answers, the internal links and their anchors, the FAQ set.
3. **A publish runbook** that a second person could follow: which command, which fields, which image, which category.
4. **A post-publish verification record** — live URL, status, word count, link check result, metadata as rendered.

The skeleton is the part people skip. Drafting straight into prose produces articles that answer three questions in one section and never answer the one the buyer asked.

## Picking topics

The question is never "what should we write about". It is "what can this site realistically rank for this quarter".

### Difficulty check

The fastest available signal is the `allintitle:` operator, which counts pages with the phrase in the title. Pages that put the phrase in the title are the ones actually competing for it.

```bash
node scripts/allintitle.js "your phrase" "another phrase"
```

Reading the counts as a heuristic, not a rule:

| Title matches | Read |
|---|---|
| Under ~100 | Weak field. Publish if the page is genuinely better than the top three. |
| ~100–1,000 | Competitive. Needs real depth, sourced facts, and internal links. |
| ~1,000–5,000 | Editorial-level. Usually needs domain authority the site does not have yet. |
| Over ~5,000 | Skip unless there is a specific angle nobody has covered. |

These thresholds move by industry and by how commercial the phrase is. The number matters less than the comparison: check the phrase you want against two or three alternatives in the same session and pick the weakest one that still has commercial intent.

**Do the check in Google, not in a regional engine.** Bing and several regional engines do not support `allintitle:` and will return a normal result count instead, which looks plausible and is meaningless. Verify the operator works before trusting any number.

### Where topics actually come from

In rough order of value for a B2B manufacturer:

1. **Questions from the quotation inbox.** Every buyer who asks "can it fit a 40HQ" is a topic with proven demand.
2. **Objections that lose deals.** Price comparison, certification, lead time, freight. Each objection is a page.
3. **Adjacent purchase decisions.** Packaging, shipping terms, import duty, installation. The buyer researches these anyway; be the source.
4. **Competitor gaps.** What the top three results do not answer.
5. **Keyword tools.** Useful for volume, useless for intent. Use last.

A topic with no commercial path is a topic for someone else's blog.

## Article structure

A structure that works for this sector, in order:

```
H1        — the phrase, once, plus the qualifier
Lede      — 2–3 sentences: the situation, the surprise, what the article resolves
            (no "in today's competitive landscape", ever)
Context   — why this is harder than it looks, 1–2 paragraphs
H2 × 5–9  — one per decision the buyer has to make, in the order they make them
Table × 1–3 — comparative data, the thing people screenshot
H2        — "what this means for your order" (the bridge to the product)
FAQ × 6–9 — the questions the article did not answer inline
CTA       — one action, specific, not "contact us today"
```

Two structural rules:

- **Headings are decisions, not topics.** "How much does it cost" is a decision. "Cost considerations" is a topic. Buyers scan headings looking for their own question.
- **Every H2 answers a question the lede implied.** If a heading could be deleted without breaking the article's logic, it is filler.

Length follows from the structure, not the other way round. A 1,200-word article that answers the question beats a 3,000-word article that circles it. Do not pad to hit a number.

## Internal links

Internal links are the only ranking lever you fully control, and the only one where a broken link is entirely your fault.

Before publishing, every internal link must return 200:

```bash
python scripts/check_links.py --base https://example.com \
  --paths /products/ /products/steel-workbenches/ /how-to-order/ /catalog/
```

Rules:

- **Three to six internal links per article.** More looks like a link farm, fewer wastes the page.
- **Link to pages that exist and are indexed.** A link to a 404 passes no value and looks careless.
- **Anchor text describes the destination**, not "click here" and not the exact head term of the page you are linking to (that reads as manipulation and competes with the target's own title).
- **Update the old pages too.** A new article with no inbound links is an orphan. Add a link from the most relevant existing page in the same session.

## Making it not read like a machine

The tells are consistent, and they are all removable mechanically:

- **Em dashes.** Count them. A published article with 20 em dashes in 1,500 words reads as generated. Target zero in body copy.
- **`not X, but Y` constructions.** "It is not a cost problem, it is a paperwork problem." One per article is style; four is a signature.
- **Hollow intensifiers.** "crucial", "seamless", "robust", "leverage", "in today's landscape". Delete and see if the sentence still means something.
- **Triads everywhere.** Three-item lists are fine once. Three-item lists in every paragraph is a rhythm nobody writes naturally.
- **Conclusions that restate the introduction.** If the last paragraph could be moved to the top without loss, cut it.

Run the draft through a rewrite pass with those rules explicit, then read it aloud. The ear catches what the checklist misses.

**Spelling consistency is a rule, not a preference.** Pick one variety — American or British — and apply it to the whole site, because a page mixing "color" and "organisation" reads as assembled from two sources. Whichever you pick, scan for the other one's markers before publishing:

| American markers | British markers |
|---|---|
| color, organize, center, meter, program, license, traveled | colour, organise, centre, metre, programme, licence, travelled |

Product units (`kg`, `mm`) and container types (`20GP`, `40HQ`) are international and do not change. A single article can be written in the other variety deliberately — but record that it is an exception, or the next editor will "fix" it.

## Metadata, and how it actually works

Two fields do the visible work in search results, and in WordPress neither is stored where people assume:

- **Title tag** — set it explicitly, keep it under about 67 characters including the brand suffix, and put the phrase first. Longer gets truncated mid-word.
- **Meta description** — commonly generated from the post excerpt, truncated at about 155–160 characters. Writing it in the excerpt field is the only way to control it without a plugin. A description cut mid-sentence is worse than a short one.

Do not write a meta description that repeats the title. It is a second chance to earn the click, not a second title.

## Publishing mechanics

Automate the post creation so every article gets the same fields:

```bash
wp post create article.html \
  --post_title="..." \
  --post_name="slug-without-year" \
  --post_status=publish \
  --post_category=4 \
  --post_author=2 \
  --post_excerpt="meta description text"
```

Then set the SEO title and the featured image as post meta, in a separate step. **Quote any string containing `$` in single quotes** — a shell will expand `$54` to `4` and you will publish a price that is wrong by two orders of magnitude, silently.

After publishing, confirm four things on the live URL, not in the admin: title tag, description, `og:image`, and that the body rendered (not escaped, not truncated). Then confirm the URL appears in the sitemap after a cache purge.

## Checklist

- [ ] Difficulty checked in Google with `allintitle:`, against two alternatives
- [ ] H1 contains the phrase once; title tag under 67 characters with brand
- [ ] Lede states the situation and the payoff in three sentences
- [ ] At least one comparative table
- [ ] Six to nine FAQ entries, each answering a real question
- [ ] Three to six internal links, all returning 200, at least one inbound link added
- [ ] Em dash count zero in body copy
- [ ] No repeated `not X, but Y` construction
- [ ] Spelling variety consistent and scanned for the other
- [ ] Meta description written in the excerpt field, 140–160 characters, not a title restatement
- [ ] Featured image set, JPEG or PNG for social, 1200 × 630
- [ ] Published, then verified on the live URL after a purge

## Failure modes

| Symptom | Cause | Where |
|---|---|---|
| Topic chosen on volume alone, never ranks | Difficulty never checked, or checked in an engine that fakes the operator | `90` F-20 |
| Article published with a price missing digits | `$` expanded by the shell | `90` F-21 |
| Meta description cut mid-word in search results | Excerpt field empty, template truncating the body | `90` F-22 |
| Article reads as generated | Em dashes, triads, restated conclusion | `90` F-23 |
| New article gets no traffic for months | Orphan page, no inbound internal links | `90` F-24 |
| Duplicate article on the same phrase outranks the first | No rotation record | `90` F-05 |
