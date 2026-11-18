# P2 — Product data as a single source

The moment you have more than about ten products, hand-built product pages become the main source of inconsistency. Spec A says 120 cm on the page, 185 cm in the catalogue, and 180 cm again in the schema markup. Nobody notices until a buyer measures a delivery.

The fix is structural: **one data file, one template, zero hand-written product pages.**

## The shape of the problem

A product page carries the same facts in six places: the visible spec table, the size options, the JSON-LD, the image alt text, the category listing card, and the quotation email your sales team sends. If those six come from six different sources, they will disagree.

With a data-driven model, they come from one array entry, and a spec change is a one-line edit.

## Input

| You need | If missing |
|---|---|
| A model list with variant suffixes | Build it from the catalogue; treat every suffix as a real variant until sales confirms otherwise |
| Dimensions, load ratings, frame type | Catalogue PDF, then the internal spec spreadsheet, in that order |
| Packing data (carton dimensions, units per carton) | Ask the factory; leave the field empty rather than estimating |
| Photography, one set per model | See the image pipeline below |

**Source hierarchy.** When the catalogue and the internal spreadsheet disagree, do not average them. Three tests decide which is current: does the photograph show the dimension claimed, does the packing figure physically accommodate it, and which document has the later revision date. Record the decision and the reason next to the entry. Six months later someone will ask why the number differs from the PDF, and "because we decided" is not an answer.

**When a field is genuinely unknown, leave it empty and say so on the page.** A visible "to be confirmed with the quotation" is honest and costs nothing. A plausible invented number travels to a buyer's insurer and costs everything.

## Deliverable

A single PHP (or JSON) file where each product is one associative array, plus a template that renders every page from it.

```php
'xx-123' => array(
    'model'   => 'XX123A/B',
    'title'   => 'XX123A/B &mdash; Descriptive Name with Attribute',
    'series'  => 'Steel Workbenches',
    'line'    => 'steel-workbenches',       // category slug this product belongs to
    'badges'  => array( 'new' ),           // rendered as chips; drives filtering
    'cover'   => $A . 'xx123-1.webp',
    'gallery' => array( 'xx123-1.webp', 'xx123-2.webp', 'xx123-3.webp' ),
    'options' => array(                     // swatch groups on the product page
        array(
            'label' => 'Powder Coat Color',
            'items' => array(
                array( 'name' => 'Graphite', 'hex' => '#3a3d40', 'on' => true ),
                array( 'name' => 'Light Grey', 'hex' => '#c9ccce' ),
            ),
        ),
    ),
    'qs'      => array(                     // quick specs, rendered as a definition list
        'MOQ'          => '50 pcs',
        'Lead Time'    => '35&ndash;45 days',
        'Overall Size' => '150 &times; 75 &times; 85 cm',
        'Max Load'     => '500 kg',
        'Assembly'     => 'Flat-packed &mdash; bolts and tool included',
    ),
    'points'  => array(                     // selling points, one sentence each
        'First concrete reason this model exists',
        'Second reason, with a number in it',
    ),
    'specs'   => array(                     // full table; may be longer than qs
        'Model'        => 'XX123A/B',
        'Overall Size' => '150 &times; 75 &times; 85 cm',
    ),
),
```

### Field contracts

- **`model`** — exactly as printed on the carton. Variant suffixes live here, not in separate keys, unless the variants differ in more than width.
- **`title`** — includes the model and one differentiating attribute. HTML entities for typography; no raw `&` or `×`.
- **`line`** — must match an existing category slug, or the product never appears in any listing. This is the most common silent failure: the product page works, the listing does not.
- **`cover`** — the single image used on listing cards and social previews. Must be square.
- **`gallery`** — order matters; the first image is what a buyer sees when they open the page.
- **`qs`** — six to eight rows maximum. More than that and the table stops being a quick spec and becomes a wall.
- **`points`** — concrete, one sentence each, at least half containing a number.
- **`specs`** — the full table. Rows that exist only here are fine; rows that contradict `qs` are a bug.

### Sort order

Newest-first is what buyers expect and what the listings assume. Use an explicit sort key per product:

```php
$sort = array(
    'xx-123' => 2026111402,   // YYYYMMDDnn — date, then sequence within the day
    'xx-122' => 2026111401,
);
```

**A product missing from the sort map must not silently sort to the end.** Default it to zero and accept that it lands last — but log a warning at build time, because "I added a product and it appeared at the bottom of the page" is a five-minute bug report and a two-hour investigation if the map is undocumented.

## Image pipeline

One rule saves the most time: **all listing and card images are square, all product images are at least 800 × 800, and nothing is uploaded as JPEG.**

```bash
# square crop, centred, then resize and convert
python scripts/image_pipeline.py in.jpg out.webp --size 800 --fit cover --quality 84
```

Details that matter:

- **WebP at quality 84 with method 6.** The method number is the encoder effort; 6 is the point where file size stops improving and build time starts hurting.
- **`--fit cover` for cards, `--fit contain` for anything with a shape that must not be cut.**
- **Never mirror-pad a non-square product image to make it square.** A reflected strip at the edge reads as a manufacturing defect in the product itself. Crop to a detail, or extend the background with a sampled flat colour.
- **Separate the cover from the gallery.** A cover that crops badly is more damaging than a gallery image that does, because the cover is what appears in search results and social cards.
- **Keep the original.** A 4000 px master is the only thing that lets you re-crop later without a new photo shoot.

## Editing safely

A 200 KB data file with 50 entries is not a file you rewrite. Two rules:

1. **Replace by key, never by whole-file regeneration.** Read the file, locate `'xx-123' => array(`, find its matching closing `),`, replace that block. Regenerating the file from a spreadsheet loses every hand edit made in the last six months.
2. **Back up before every write**, with a suffix that identifies the change (`products-data.php.bak-xx123`), not a timestamp nobody can read.

## Checklist

- [ ] Every entry has a unique key, and the key matches the URL slug
- [ ] Every `line` resolves to an existing category slug
- [ ] Every product appears in its listing page, not just at its own URL
- [ ] Sort map covers every key, and the newest product is first
- [ ] No spec appears in `qs` with a different value than in `specs`
- [ ] Every cover is square and under 120 KB
- [ ] Every gallery image exists on disk; no broken paths
- [ ] Unknown fields are visibly marked as pending, not filled with estimates
- [ ] JSON-LD on the page matches the visible spec table
- [ ] Product count on the listing page equals the entry count

## Failure modes

| Symptom | Cause | Where |
|---|---|---|
| Product page works, listing page does not show it | `line` does not match a category slug | `90` F-04 |
| New product appears last | Missing from the sort map | `90` F-04 |
| Another product's data changed unexpectedly | Whole-file regeneration overwrote hand edits | `90` F-10 |
| Image looks like it has a defect along one edge | Mirror-padding a non-square photo | `90` F-13 |
| Spec table and structured data disagree | Specs typed twice, once in the array and once in the template | `90` F-14 |
| Buyer receives a product with a different rating than the page promised | Estimated value published as fact | `90` F-15 |
