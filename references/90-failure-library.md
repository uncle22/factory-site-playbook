# Failure library

Every entry happened on a live site. The pattern is always the same: the symptom points at one layer, the cause is in another, and the wrong layer absorbs the debugging time.

Read this before debugging anything that makes no sense. The first section is ordered by how much time each one cost.

---

## Tier 1 — caused an outage or a silent loss

### F-01 · Whole site renders wrong, every URL returns 200, every file passes lint

**Symptom.** Pages load, unstyled and structurally wrong. Every URL returns `200`. `php -l` passes on every file. Logs show no fatal. Admin works.

**Misdiagnosis.** PHP syntax error, broken plugin, corrupted CSS, database issue. Hours go into reading logs that are empty.

**Actual cause.** A recursive permission change applied `644` to directories. Directories need the execute bit to be traversed; without it PHP cannot enter the theme directory, and WordPress falls back to a bare render served with status 200.

**Diagnose.**

```bash
stat -c '%a %U:%G %n' /path/to/wp-content/themes/child-theme
# 644 → wrong, should be 755
```

**Fix.**

```bash
find /path/to/theme -type d -exec chmod 755 {} \;
find /path/to/theme -type f -exec chmod 644 {} \;
```

**Prevention.** Never `chmod -R 644` a tree. Two `find` commands, always. Any deploy script that touches permissions gets reviewed for this specifically. Triage rule: site-wide wrong render + 200 status → check directory mode first.

---

### F-02 · Deploy reported success, page never changed

**Symptom.** Upload completes, lint passes, purge command returns `200`, page is identical to before. Repeating the purge changes nothing.

**Misdiagnosis.** File did not upload, wrong file edited, cache plugin not clearing, CDN stuck.

**Actual cause.** The purge was sent to port 80. The web server answers port 80 with a 301 redirect to HTTPS, and a redirect is generated before the request reaches the reverse proxy. The `PURGE` method is dropped, Varnish never invalidates, and `curl -w '%{http_code}'` reports the redirect target's status — a very convincing `200`.

**Diagnose.** Send the purge to the origin on 443 with the hostname pinned:

```bash
curl -sk -X PURGE --resolve example.com:443:127.0.0.1 https://example.com/path/ -o /dev/null -w '%{http_code}\n'
```

Then check the cache header. If it still says `HIT` with an old `age`, the purge did not land.

**Fix.** Correct the deploy script's purge step. Verify with a bare URL and a browser user agent, and assert on content, not status code.

**Prevention.** A `200` from a purge command is not evidence of anything. Every deploy asserts a content change.

---

### F-03 · Page converts in testing, measures nothing in production

**Symptom.** A landing page works. The form submits and the enquiry arrives. Analytics shows no conversion for that page, ever. Conversion tracking "works" on other pages.

**Misdiagnosis.** Tag misconfigured, wrong conversion ID, consent blocking, ad blocker.

**Actual cause.** The landing page is a full-page PHP template that renders the entire document and never calls `wp_footer()`. The tracking script was queued through `wp_enqueue_script`, so it is never printed. The page looks perfect because nothing visual depends on that call.

**Diagnose.**

```bash
curl -s https://example.com/landing/ | grep -c 'googletagmanager\|gtag('
# 0 → the tag is not in the output at all
```

Check the template file for `wp_head()` and `wp_footer()`.

**Fix.** Add `wp_footer()` before `</body>` and `wp_head()` inside `<head>`. Re-run the conversion test matrix.

**Prevention.** A full-page template has exactly two mandatory calls. Any template that replaces `header.php` or `footer.php` gets a checklist item for both.

---

### F-16 · Enquiries stop arriving in the afternoon, form looks fine

**Symptom.** Mornings are normal. By mid-afternoon, submissions fail. The visitor sees a spinner or a thank-you. Nothing in the form changed.

**Misdiagnosis.** Email deliverability, SMTP, spam filtering, hosting.

**Actual cause.** The form carries a WordPress nonce for CSRF protection. The page is behind full-page cache, so the same HTML — containing the same nonce — is served to everyone for hours. Nonces expire, typically after 12–24 hours. Submissions from a cached page fail validation server-side, and depending on the handler, the visitor may still see a success message.

**Diagnose.** Load the page with a cached response, extract the nonce, check its age. Or check the handler log for nonce failures clustered in the afternoon.

**Fix.** You cannot have a strict nonce and a cached page. Either exclude the page from caching, or keep the nonce but demote failure to a logged event, and defend with a honeypot, an IP rate limit and a minimum submit time.

**Prevention.** Any CSRF token inside a cacheable page is a bug waiting for the cache to fill. Decide the trade-off at build time, and log the rejection so the fallback is visible.

---

### F-11 · Conversions look excellent, the inbox is empty

**Symptom.** Conversion count roughly double the actual enquiries. Cost per lead looks great. Sales says the leads are not there.

**Misdiagnosis.** Attribution window, duplicate conversions from page reloads.

**Actual cause.** The conversion listener matched any `button[type=submit]` on the page. The header contains a site-search form with a submit button. Every internal search counted as a lead.

**Diagnose.** Run one internal search, watch the tag. If a conversion fires, this is the cause.

**Fix.** Add an allowlist of lead-form selectors, and require the button to be inside one of them. Also require `form.checkValidity()` so an empty required field does not count.

**Prevention.** Full test matrix on every form change: valid submit, Enter key, empty form, site search, double click. Each has an expected count.

---

## Tier 2 — cost a day or more

### F-07 · Sitemap has the right URL count and nothing is indexed

**Symptom.** Sitemap lists 100+ URLs. Search console shows a handful indexed. New pages never appear.

**Misdiagnosis.** Content quality, domain age, crawl budget.

**Actual cause.** The sitemap URL returns status 200 with `Content-Type: text/html` — a catch-all template or an SPA fallback answered the request. Search engines receive an HTML page where XML was expected, and drop the whole file.

**Diagnose.**

```bash
curl -sI https://example.com/sitemap.xml | grep -i content-type
```

**Fix.** Make the sitemap route return real XML with the correct content type, or generate a static file.

**Prevention.** Any generated feed — sitemap, RSS, JSON endpoint — gets a content-type assertion in the deploy check.

---

### F-09 · Only one language version ranks

**Symptom.** Three language versions are live and indexable. Only the primary ranks, in any market.

**Misdiagnosis.** Translation quality, local link building, hreflang being "not supported".

**Actual cause.** The cluster is not reciprocal. One page emits three `hreflang` tags; the pages it names do not point back. Search engines ignore one-way annotations. Separately, `x-default` is often missing, which removes the cluster's fallback.

**Diagnose.** For each page in the cluster, dump every `alternate` tag and compare the sets.

```bash
for u in / /de/ /fr/; do
  echo "== $u"; curl -s https://example.com$u | grep -o '<link rel="alternate"[^>]*>'
done
```

**Fix.** Every member emits every alternate plus a self-reference plus `x-default`.

**Prevention.** Generate the head block from one function that takes the cluster as a list. Never hand-write hreflang per page.

---

### F-19 · A page lost a section nobody remembers removing

**Symptom.** A live page is missing a block that exists in a backup. No commit, no ticket, no explanation.

**Misdiagnosis.** Plugin update, theme update, caching.

**Actual cause.** The template was edited directly on the server (an urgent copy fix, a quick class change), and the tracked local copy was never updated. Later, the local copy was deployed — a legitimate deploy — and it overwrote the server version, reverting every server-side edit at once.

**Diagnose.** Diff the live file against the tracked copy. Every difference is an edit that exists in only one place.

**Fix.** Reconcile deliberately: decide which version is correct, merge, then deploy.

**Prevention.** Any server-side edit gets downloaded and committed in the same session. If a change must be urgent, commit it immediately after — the two minutes are cheaper than the archaeology.

---

### F-21 · A published price is missing digits

**Symptom.** An article or a product entry shows a number that is off by two orders of magnitude. The source file is correct.

**Misdiagnosis.** Template formatting, database truncation, caching.

**Actual cause.** The content was passed to a shell command in double quotes. `$54` was expanded as a variable, the variable was empty, and the string arrived as `4`. No error, no warning.

**Diagnose.** Compare the published output with the source file byte for byte.

**Fix.** Republish with the string in single quotes, or pass content through a file instead of an argument.

**Prevention.** Any command that carries user content with `$`, backticks, or `\` uses single quotes or a heredoc with a quoted delimiter. Content goes in a file, not in an argument.

---

### F-05 · Two pages alternate in rankings, neither wins

**Symptom.** Page A ranks 8th for a phrase on Monday, page B ranks 9th on Thursday. Both are good pages. Neither improves.

**Misdiagnosis.** Algorithm fluctuation, competitor movement.

**Actual cause.** Two pages both claim the same primary phrase in their title. Search engines pick one per query, switch when one looks slightly better, and neither accumulates the signals that would push it up. Common trigger: a product page reusing the umbrella term already owned by its category page.

**Diagnose.** List every published page whose title contains the phrase. If there are two, this is the cause.

**Fix.** Decide which page owns the phrase (usually the category page for a head term, the product page for a model-specific term) and rewrite the other page's title around a different, still-relevant phrase.

**Prevention.** The naming matrix from P1, maintained as an ownership record. Before publishing, check who already owns the phrase.

---

### F-06 · Category pages get no traffic despite strong products

**Symptom.** Product pages get some long-tail traffic. Category pages rank nowhere. The category has four products in a range of thirty.

**Cause.** Thin category pages. Four products produce a page with almost no unique content, and the products themselves are near-duplicates in structure.

**Fix.** Merge small families upward until each has eight or more genuinely distinct products, or add real comparative content to the category page (selection guidance, specification table, use-case sections).

**Prevention.** A family launches only when it has at least four products; below that it lives inside its parent.

---

### F-20 · Topic chosen on volume alone never ranks

**Symptom.** A keyword tool reported strong volume. The article is good. It ranks on page four.

**Misdiagnosis.** Content quality, on-page optimisation.

**Actual cause.** Difficulty was never checked, or was checked in an engine that does not support the operator. Bing and several regional engines return a normal result count for `allintitle:`, which looks like a difficulty number and is not one.

**Diagnose.** Run the same query in Google and read the count of title matches. Compare against three alternatives.

**Fix.** Reprioritise. Either find an angle nobody has covered, or move the topic down the queue and publish the weak-field alternatives first.

**Prevention.** Every topic gets a difficulty check in Google, recorded with the date, before it enters the queue.

---

## Tier 3 — quiet, structural, expensive later

### F-04 · A new product page works, the listing page does not show it

**Symptom.** `/product/xx-123/` renders correctly. The category page is missing that product. Counts do not add up.

**Cause.** Two independent bugs, often together. The entry's category field does not match any existing category slug, so no listing loop picks it up. And the entry is absent from the sort map, so it defaults to zero and sorts to the end — which, combined with pagination, hides it entirely.

**Fix.** Correct the category slug; add a sort key.

**Prevention.** A build-time assertion: every entry's category resolves, every entry has a sort key, the listing count equals the entry count.

---

### F-08 · A product URL returns 404 while the listing works

**Symptom.** Links to `/products/xx-123/` 404. The product is visible in the listing and its link is correct in the markup.

**Cause.** The detail route is registered singular (`/product/`) and the links were written plural, or a catch-all template returns a 200 page that looks like a 404.

**Fix.** Fix the link generation, add a 301 from the plural form.

**Prevention.** One route constant, referenced everywhere; a link check in the deploy verification.

---

### F-10 · Another product's data changed unexpectedly

**Symptom.** A spec on model A changed. Nobody edited model A. The change matches a value that belongs to model B.

**Cause.** The data file was regenerated wholesale from a spreadsheet or a script, discarding months of hand edits — or a block replacement matched the wrong entry because the key search was not anchored.

**Fix.** Restore from the named backup, reapply the intended change by key.

**Prevention.** Replace by anchored key (`'xx-123' => array(` and its matching close), never regenerate. Back up with a change-named suffix before every write.

---

### F-12 · Traffic drops after a site-wide rename

**Symptom.** Following a naming change, organic traffic halves over two weeks. New URLs are indexed; old ones are gone.

**Cause.** URLs changed without a 301 map.

**Fix.** Build the map from the old sitemap, redirect every changed URL, resubmit.

**Prevention.** A rename is a migration. Old URL inventory exported first, redirect map written before the change, verified after.

---

### F-13 · Product photo shows a defect along one edge

**Symptom.** A product image looks like it has a crease, a shadow line, or a doubled edge. The physical product has none.

**Cause.** A non-square photo was mirror-padded to make it square. The reflected strip reads as a manufacturing artefact on a product where buyers inspect surfaces closely.

**Fix.** Crop to a legitimate detail, or extend with a sampled flat background colour. Never reflect.

**Prevention.** Image pipeline defaults to cover-crop; contain-fit requires an explicit flag with a reason.

---

### F-14 · Spec table and structured data disagree

**Symptom.** The visible table says one value, the JSON-LD says another. Rich results show the wrong figure.

**Cause.** The spec is written twice — once in the data array, once hardcoded in the template or a JSON-LD block.

**Fix.** Generate JSON-LD from the same array the table renders from.

**Prevention.** No specification literal outside the data file. Grep the template for units (`kg`, `cm`, `mm`) as a lint step.

---

### F-15 · Buyer receives a product with a different rating than the page promised

**Symptom.** A load rating or dimension on the page does not match the delivered unit.

**Cause.** A field was unknown at publication, and a plausible value was filled in rather than left empty.

**Fix.** Correct the value from the factory's document, and publish the gap explicitly until then.

**Prevention.** Unknown fields render as "to be confirmed with the quotation". An invented number on a safety-relevant field is a commercial and legal exposure, not a copy decision.

---

### F-17 · Shared link shows no preview image

**Symptom.** Posting the URL to a messaging app or social platform produces a card with no image, or no card at all.

**Cause.** The `og:image` is WebP (not rendered by several scrapers), relative (not resolvable), or under the minimum dimensions.

**Fix.** Serve a JPEG or PNG at 1200 × 630, absolute URL.

**Prevention.** Every page that can be shared gets a dedicated OG asset; the in-page hero format is independent.

---

### F-18 · Rich result disappears after a data edit

**Symptom.** A category page had a list rich result. After adding products, the result vanished and Search Console reports an invalid item.

**Cause.** The `ItemList` block carries `inLanguage`, which is not a valid property there in the form used. The whole block is rejected.

**Fix.** Remove the property. Language belongs on the page, not on that list node.

**Prevention.** Validate structured data after data changes, not only after template changes.

---

### F-22 · Meta description cut mid-word in search results

**Symptom.** The snippet in search results ends mid-sentence or mid-word.

**Cause.** The description field was empty, so the template truncated the body at a fixed character count.

**Fix.** Write an explicit description at 140–160 characters.

**Prevention.** A description is a required field at publication, same as the title.

---

### F-23 · Article reads as generated

**Symptom.** Traffic arrives, engagement is poor, the article does not earn links. Readers cannot say why it feels off.

**Cause.** Structural tells: em dashes in every paragraph, repeated `not X, but Y` constructions, triads, hollow intensifiers, a conclusion that restates the introduction.

**Fix.** Mechanical removal pass, then read aloud.

**Prevention.** Count em dashes before publishing (target zero in body). Ban the repeated construction. Cut any final paragraph that could move to the top without loss.

---

### F-24 · New article gets no traffic for months

**Symptom.** The article is indexed, answers the query, and receives nothing.

**Cause.** Orphan page: no internal links point to it, and it sits deep in the archive where nothing crawls.

**Fix.** Add links from the two or three most relevant existing pages, with descriptive anchor text.

**Prevention.** Every publication includes at least one inbound internal link, added in the same session.

---

### F-25 · Change visible to admin, invisible to visitors

**Symptom.** The developer sees the new version. A colleague, or an incognito window, sees the old one.

**Cause.** The verification request bypassed the cache — an admin session, a query string, or a no-cache header — so PHP ran and produced the new output. Visitors still receive cached HTML.

**Fix.** Purge correctly, then verify with a bare URL and a browser user agent.

**Prevention.** The verification command is copy-pasted from the playbook, never improvised.

---

### F-26 · `wp` reports "not a WordPress installation" while the site runs fine

**Symptom.** `wp` commands fail with an install-not-found error. The same commands worked yesterday. The site is up.

**Cause.** `--path` was passed with a path that resolves differently for the shell user than for the chrooted SFTP user, or the working directory was already correct and the flag pointed elsewhere.

**Fix.** `cd` into the WordPress root and run `wp` without `--path`.

**Prevention.** Document the working directory as part of the deploy environment. `wp --info` first when a command misbehaves.

---

### F-27 · One page returns 500 after an edit, the rest are fine

**Symptom.** A single template produces a 500. Other pages render.

**Cause.** A syntax error in that one file. No lint was run, or the file was edited directly on the server.

**Fix.** Run `php -l`, fix, redeploy.

**Prevention.** Lint the uploaded file before moving it into place, and keep the previous version until verification passes.

---

### F-28 · Paid traffic reports as direct or organic

**Symptom.** Ad platform reports clicks. Analytics attributes almost none of them to paid. Cost per acquisition looks catastrophic.

**Cause.** Consent default denies ad storage, and `url_passthrough` is missing, so click identifiers are dropped from the URL when the visitor does not consent. Every paid click arrives indistinguishable from an organic visit.

**Fix.** Add `url_passthrough: true` to the consent default.

**Prevention.** Four consent settings are checked together, never three of four.

---

### F-29 · One enquiry counted twice

**Symptom.** Conversions exceed inbox enquiries by a small, consistent ratio.

**Cause.** The click listener and the submit listener both fire for the same action. If the tag implementation does not deduplicate, one enquiry becomes two.

**Fix.** A per-page-load counter that permits exactly one conversion.

**Prevention.** The double-click case is in the test matrix with an expected value of 1.

---

### F-30 · Deduplication worked, then stopped

**Symptom.** Deduplication was verified and correct. Days later, conversions doubled again.

**Cause.** The counter wrapped `window.gtag`. When `gtag.js` finished loading, it replaced that function, and the wrapper disappeared with it — usually within the first page view.

**Fix.** Count what you push to `dataLayer`, not calls to `gtag`.

**Prevention.** Never monkey-patch a vendor global that is loaded asynchronously.

---

### F-31 · EU visitors see no consent prompt

**Symptom.** A consent banner is configured and was visible in testing. Now EU visitors get no banner, and tags fire.

**Cause.** The consent plugin was on a free tier with a monthly pageview quota. Past the quota, the CDN serving the banner script returns an empty shell, the banner silently fails to initialise, and tag loading continues.

**Fix.** Self-host the consent layer, with the default state pushed in the page head.

**Prevention.** Never let a third party own the consent gate. If you use one, monitor the banner from an EU IP monthly.

---

## How to use this file

1. Read tier 1 before debugging. Three of the five produce symptoms that point at the wrong layer entirely.
2. When you fix something not listed here, add it. The library is the asset.
3. Every entry has a **Prevention** line. That line is the rule that belongs in the stage checklist.

## Entry template

```
### F-nn · One-line symptom
**Symptom.** What you observe.
**Misdiagnosis.** What it looks like.
**Actual cause.** What it is.
**Diagnose.** The command or check that distinguishes them.
**Fix.** What to do.
**Prevention.** The rule that stops it recurring.
```
