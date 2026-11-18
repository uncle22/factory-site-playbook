# G — GEO: getting cited, not just ranked

GEO here means generative engine optimization: making a page the source an answer engine quotes or links to, rather than a page that happens to rank tenth and gets skipped because the answer is already on screen.

Separate the two goals clearly, because they pull in different directions:

- **SEO** optimizes for a ranked list. The unit of competition is the page.
- **GEO** optimizes for extraction. The unit of competition is the paragraph.

A page can win at one and lose at the other. A 3,000-word narrative with a great title ranks and never gets quoted, because there is no self-contained sentence to lift. A page of short factual blocks gets quoted constantly and ranks poorly if the title is generic. You want both, and the way to get both is to write for extraction and title for the list.

This file is deliberately short on speculation. Everything below is either a formatting rule you can check in the HTML, or a habit that has a measurable effect on whether a passage survives being lifted out of context.

## Input

- **A drafted page**, not an outline. Extraction quality is a property of finished prose; it cannot be checked from headings.
- **The buyer's actual questions**, in their words, collected before writing. Eight to twelve is enough for a product category.
- **The entity names** already fixed in P1 — product name, category name, company name, and the place names you are willing to publish.
- **The standards and regulations you can cite** without asking anyone, and the list of numbers you can publish with their conditions attached.
- **A baseline of what answer surfaces currently say** for your key prompts, recorded with a date, so improvement is measurable rather than felt.

## Deliverable

1. **Rewritten opening paragraphs** for every `H2` on the page: answer in the first 40 to 60 words, context afterwards.
2. **A named-entity pass** — every section that names its own subject, no unresolved pronoun carrying the meaning.
3. **A FAQ block** in query form, each answer 40 to 80 words and each one taking a position.
4. **A prompt table** with the baseline recorded: date, prompt, cited or not, which source, which URL of yours.
5. **A defects list** — the paragraphs you could not make extractable, and why. Those are usually a positioning problem, not a writing problem.

## The mechanics worth knowing

A generative answer is assembled from passages. The retrieval step does not read your page the way a person does: it splits the document into chunks, embeds them, and pulls the chunks that answer the query. Three consequences follow, and they are the whole game:

1. **Chunk boundaries are not your paragraph boundaries.** Anything that only makes sense with the previous sentence may be retrieved alone and quoted alone.
2. **A chunk has no memory.** Pronouns, "as mentioned above", "this process", "the former" become unresolvable when the chunk is lifted.
3. **Specificity is the tie-breaker.** Between two chunks that both answer the question, the one carrying a number, a standard reference or a named entity is the one that gets quoted, because it is the one that makes the answer look sourced.

## The rules

### 1. Answer first, then explain

Every `H2` opens with a 40 to 60 word paragraph that answers the heading's question completely. Context, caveats and history come after. If the answer is buried in the fourth paragraph, the passage that gets retrieved is the fourth paragraph, without the heading that explains it.

Bad:

> Choosing a container is a decision that many buyers find difficult. There are several factors to consider, and the right answer depends on your situation. In our experience, working with hundreds of clients, we have found that...

Good:

> A 40HQ carries about 76 m³ of usable volume against roughly 15 tonnes of payload. For most cartoned goods the limit is volume, not weight, and the carton count follows from the carton size rather than from a fixed number per container.

The second version is wrong in details you may disagree with, and that is fine. It is liftable. The first version is unfalsifiable and therefore useless to an answer engine.

### 2. One fact per paragraph

If a paragraph contains three claims, the retrieval layer may keep the one you did not want quoted. Split it. A paragraph of one claim and one consequence is the ideal shape for extraction.

### 3. No unresolved references

- Name the thing again instead of writing "it", "this", "the former".
- Repeat the product category in a section that starts mid-argument.
- Never open a paragraph with "As mentioned above".

This reads slightly repetitive to a human skimming linearly, and it is the single highest-leverage change for extractability. Write the repetition so it reads as natural restatement, not as a stutter.

### 4. Name entities in full, once per section

Company name, product name, standard number, place name. `EN 12150-1` not "the glass standard"; `Rotterdam` not "the port" on first mention in a section. An answer engine builds an entity graph; unnamed things do not enter it, and a page that never names its own subject will not be cited as a source about that subject.

Consistency matters more than completeness: if the product is called one thing in the `H1` and another in the body, retrieval treats them as two entities and neither accumulates authority across the page.

### 5. Quantify with units and conditions

`200 kg` beats `high load capacity`. `25 to 30 days from deposit` beats `fast lead time`. `0.5 to 1.5 Wh per cell` beats `small battery`.

Add the condition when the number is conditional: "up to 200 kg on the electric models; 150 kg on the hydraulic and manual frames". A number without its condition is the kind of claim that gets quoted back at you by a buyer who read it as universal, which is worse than not being quoted.

### 6. Cite the standard, not the consensus

`Per SP188, cells under 20 Wh are excepted from Class 9` is quotable. `Most suppliers agree that small batteries are fine` is not. Standards, regulations, test methods and named tests all transfer into an answer with their authority intact.

### 7. Put comparable facts in a table

Tables are parsed as key-value pairs and survive extraction better than the same facts written as prose. A spec table, a comparison of two product types, a port-to-market transit matrix: each one is a block an answer engine can lift whole, with the column headers acting as the labels the chunk would otherwise lose.

Corollary: a table wider than the mobile viewport must be inside a horizontal scroll container. An unreadable table on a phone still gets indexed, and still loses the human.

### 8. Write FAQs in the question form a person types

`Do you supply replacement castors?` is a query. `Our Capabilities in Material Handling` is a heading. Only the first one matches retrieval.

Six to twenty FAQs on a long article is normal for this format, provided each answer is 40 to 80 words and gives a position. "It depends, contact us" is a wasted FAQ.

### 9. Define, then use

Use the definitional shape at least three times on a long page:

> *X is a Y that Z.*

It is the most reliably extracted sentence pattern there is, and it forces you to state what the thing is before arguing about it. If you cannot write that sentence for your main product, the page has a positioning problem, not a writing problem.

### 10. Show freshness honestly

A visible publication date and a visible update date, both accurate. An answer engine weights recency, and a page that claims 2026 while citing a 2019 regulation is worse than an undated page. Updating a page and leaving the date alone is a form of lying that costs you citations.

### 11. Structure the page so the structure is visible

- One `H1`.
- `H2` per question or per category, phrased as the question.
- `H3` only for sub-parts of that question.
- No `H2` used as a visual divider with no content under it.
- Anchors that are readable, so a citation can deep-link to the section that answered.

### 12. Be boring where boring is correct

Superlatives, "leading manufacturer", "world-class", "state-of-the-art" carry no extractable fact and are the most common filler in this sector. They also make a page read as generated, which is a separate and worse problem.

## What not to bother with

- **`llms.txt`.** Cheap to add, no evidence it changes retrieval. Treat it as decoration, not strategy.
- **Keyword density tuning for AI.** Retrieval works on semantic match, not frequency. Repeating a phrase does not increase the chance a chunk is retrieved; it lowers the quality of the prose around it.
- **Schema markup as a GEO lever.** Useful for rich results, not a meaningful factor in whether a passage is quoted. Mark up what is on the page and stop.
- **Publishing volume as a substitute for structure.** Twenty unstructured pages lose to three structured ones. This is the opposite of the old content-volume playbook, and it is the part people get wrong.

## Monitoring, cheaply

Write down 8 to 12 questions a buyer would actually ask, in their words, before the product is finished. Re-ask them monthly in the answer surfaces that matter for your market, and record only:

| Date | Prompt | Cited? | Which source | Which URL of yours |
|---|---|---|---|---|

Two things come out of this table that no rank tracker gives you: which of your pages are considered sources at all, and which competitor keeps getting quoted for a question you answer better. The second one is the more actionable signal.

Do not chase a single mention. Track whether the set of prompts that cite you grows quarter over quarter.

## Checklist

- [ ] Every `H2` answered in its first 40 to 60 words.
- [ ] No paragraph depends on the previous one to be intelligible.
- [ ] No unresolved pronoun or "as mentioned above" inside a section.
- [ ] Entities named in full at least once per section; product called the same thing throughout.
- [ ] Every quantity has a unit; every conditional quantity has its condition.
- [ ] At least three definitional `X is a Y that Z` sentences.
- [ ] Comparable facts in tables, each table inside a scroll container on mobile.
- [ ] FAQ count 6 or more, each in query form, each answer 40 to 80 words with a position.
- [ ] Publication and update dates visible and true.
- [ ] Anchor IDs on sections, human-readable.
- [ ] Zero superlatives that cannot be verified.
- [ ] Prompt set written down, baseline recorded with a date.

## Failure modes

| Symptom | Likely cause |
|---|---|
| Page ranks but is never quoted | No self-contained answer paragraphs; the page argues instead of stating |
| Quoted answers are subtly wrong | A number was lifted without its condition |
| Competitor quoted for your own product category | Category name used inconsistently, entity never resolved |
| Citations link to the homepage instead of the section | Sections have no stable anchors |
| Traffic from answer engines is zero for a whole category | The category has no page that states what the thing is |
| AI summary contradicts your spec page | Spec table and structured data disagree (see F-14) |

## Interaction with the other stages

- **P1** decides the entity names. GEO cannot fix a naming collision.
- **P4** produces the articles. This file changes how they are structured, not what they are about.
- **S (07)** covers the placement and index mechanics. Run both checklists; they overlap on metadata and do not overlap on extraction.
- **P5** still applies. None of this survives being deployed into a cache that never clears.
