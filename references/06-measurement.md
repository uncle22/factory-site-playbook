# P6 — Measurement, consent and conversion

A B2B site with no enquiry tracking is a site you cannot improve. Worse, the default WordPress setup produces numbers that look plausible and are wrong in ways that lead to bad decisions: conversions attributed to the wrong page, duplicate counts inflating performance, and EU traffic measured without consent.

This stage fixes the layer, in this order: consent defaults → tag loading → conversion definition → deduplication → verification.

## Input

- **A written definition of a lead** — what counts as one, and what does not. "Form submitted" and "genuine enquiry" are different events, and the gap between them is where the numbers lie.
- **Account access** for every destination you intend to fire at, plus the ability to inspect live network requests. Without request-level access you are trusting a UI that hides failures.
- **A jurisdiction list.** Which regions get the consent banner, which get defaults granted, and who decided. This is a legal input, not a design choice.
- **The form's DOM selectors**, so tracking can be scoped to real enquiry forms and not the site search box.
- **A baseline.** Even one month of "before" numbers makes the next change auditable.

## Deliverable

1. **A consent default block** emitted before any tag, with region logic that can be read and changed by someone who did not write it.
2. **An event table**: event name, trigger, where it fires, deduplication method, destination. One row per event, no prose.
3. **A conversion action per platform**, with the counting method stated (one per submission, or one per session) and the counter that enforces it.
4. **A monthly reconciliation template**, with the three columns that matter: platform-reported conversions, inbox leads, and the difference explained.
5. **A revocation path** — how a visitor withdraws consent after the fact, and where that is recorded.

## Consent must come before tags

Under Google's consent framework, a default consent state has to be pushed **before** any Google tag loads. If your tag manager fires first, the default arrives too late and the tag has already written cookies.

Order in the document head:

```html
<script>
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}

gtag('consent', 'default', {
  'ad_storage': 'denied',
  'ad_user_data': 'denied',
  'ad_personalization': 'denied',
  'analytics_storage': 'denied',
  'wait_for_update': 2000,
  'url_passthrough': true,
  'ads_data_redaction': true
});
</script>
<!-- tag loader comes after this -->
```

Four configuration details, each of which fails silently:

| Setting | If missing |
|---|---|
| All four consent types `denied` by default | Non-consented regions get cookies written before the banner appears |
| `wait_for_update: 2000` | The tag proceeds before the banner resolves, so the visitor's choice arrives too late |
| `url_passthrough: true` | **Click identifiers are lost.** `gclid` is dropped when ad storage is denied, and paid traffic becomes unattributable |
| `ads_data_redaction: true` | Ad identifiers are sent in a region where they should not be |

`url_passthrough` is the one that quietly destroys reporting. The site is technically compliant, the tag reports fine, and every paid click looks organic.

### Then grant, per region

Default `denied` is a global setting. Visitors outside the consent regions should not have to click a banner to be measured:

```php
// after the default push, before the tag loads
if (not in EEA / UK / CH) {
    gtag('consent', 'update', {
        ad_storage: 'granted', ad_user_data: 'granted',
        ad_personalization: 'granted', analytics_storage: 'granted'
    });
}
```

Regional detection belongs server-side (geo-IP or Cloudflare country header), not in JavaScript, because a client-side guess runs after the tags.

### The banner

- **Show it only where required.** A banner shown to a US visitor who does not need it reduces conversion and adds nothing legally.
- **Localise it.** A consent banner in English on a German page is a signal that nobody thought about the market.
- **Provide a withdrawal path.** Consent that cannot be withdrawn is not consent. A footer link that reopens the banner is enough.
- **Log the decision.** Store the timestamp, the choice, and a hashed IP. If a regulator asks, "we believe they consented" is not evidence.

Do not install a third-party consent plugin and assume it works. Free tiers of consent plugins have pageview quotas; when the quota is exhausted, the script can stop injecting the banner entirely while the site continues to load tags. The failure is silent and looks like "consent is configured".

## Defining a conversion

A B2B lead is a form submission. That is the only conversion worth counting on this kind of site, and it has to be defined precisely, because the obvious implementation over-counts.

### The naive implementation

```js
document.addEventListener('click', e => {
  if (e.target.closest('button[type=submit]')) {
    gtag('event', 'conversion', {'send_to': 'AW-XXXX/yyyy'});
  }
});
```

This counts:

- the internal site-search submit button,
- the newsletter box,
- the "apply coupon" button on a checkout,
- and every click on a submit button in a form that fails validation.

On a site with a search box in the header, this inflates conversions by double digits and makes every campaign look better than it is.

### The corrected implementation

```js
const LEAD_FORMS = ['#hero-form', '#contact-form', '#landing-form'];

document.addEventListener('click', e => {
  const btn = e.target.closest('button[type=submit]');
  if (!btn) return;
  const form = btn.closest('form');
  if (!form) return;
  if (!LEAD_FORMS.some(sel => form.matches(sel))) return;
  if (!form.checkValidity()) return;
  gtag('event', 'conversion', {'send_to': 'AW-XXXX/yyyy'});
}, true);
```

Four guards, each closing a real hole: a submit button, inside a form, on the allowlist, passing native validation.

### Keyboard submission

A visitor who presses Enter in a field does not click anything. If the only trigger is `click`, that lead is invisible. Add a `submit` listener on the allowed forms, in the capture phase, so it fires before the handler that may navigate away:

```js
document.addEventListener('submit', e => {
  if (!LEAD_FORMS.some(sel => e.target.matches(sel))) return;
  if (!e.target.checkValidity()) return;
  sendConversionOnce();
}, true);
```

### Deduplication

Clicking a submit button also fires `submit`. Pressing Enter twice fires twice. Some tag implementations do not deduplicate, so one enquiry becomes two or three conversions, and the reported cost per lead is a third of reality.

Do not wrap `window.gtag` to count calls. `gtag.js` replaces that function when it loads, so your wrapper disappears and the counter stops working at an unpredictable moment — usually right after a page view, which makes it look like it never worked.

Count what you push instead:

```js
let convCount = 0;
function sendConversionOnce() {
  if (convCount > 0) return;
  convCount++;
  dataLayer.push({'event': 'conversion', 'send_to': 'AW-XXXX/yyyy'});
}
```

The counter lives in the page scope and survives as long as the page does. That is exactly the scope you want: one conversion per page load.

## Two destinations, two events

Keep advertising and analytics separate:

| Destination | Event | Purpose |
|---|---|---|
| Ads | `conversion` | Bidding signal. Accuracy matters most here. |
| GA4 | `generate_lead` | Reporting, funnel analysis, audience building |

Sending the same event to both through one tag is possible and usually wrong: the Ads conversion gets counted twice if GA4 also imports it, and the two systems then disagree permanently. Send each event to one destination, and deduplicate within each.

## Verifying it

Test on the live site, with a debug tool that shows fired tags, and run the same matrix every time the form changes:

| Case | Expected Ads conversions | Expected GA4 events |
|---|---|---|
| Click submit on a valid lead form | 1 | 1 |
| Press Enter in a lead form field | 1 | 1 |
| Submit an empty required field | 0 | 0 |
| Submit the header site-search | 0 | 0 |
| Double-click submit fast | 1 (not 2) | 1 |
| Submit on each language version | 1 per version | 1 per version |

If the double-click case returns 2, deduplication is broken. If the empty-form case returns 1, the validity guard is missing. If the search case returns 1, the allowlist is missing.

Record the result of this matrix with a date. It is the only evidence that tracking worked on a given day, and tracking breaks silently when a form is restructured.

## Monthly reconciliation

Once a month, compare three numbers for the same period:

1. Conversions reported by Ads.
2. `generate_lead` events in GA4.
3. Enquiries actually present in the inbox or CRM.

They will never be identical — bots, blocked scripts, ad blockers, and consent choices account for a few percent. A gap over about 15% means something is structurally wrong: a form removed from the allowlist, a tag not loading on one language, or a handler failing after a template change.

The inbox is the source of truth. Everything else is instrumentation, and instrumentation drifts.

## Checklist

- [ ] Consent default pushed before any tag loads, all four types denied
- [ ] `wait_for_update`, `url_passthrough`, `ads_data_redaction` all present
- [ ] Non-consent regions granted server-side, not in JavaScript
- [ ] Banner shown only in required regions, localised, with a withdrawal path
- [ ] Consent decisions logged with timestamp and hashed IP
- [ ] Ads conversion fires on click and on Enter, once per page load
- [ ] Lead-form allowlist covers every lead form and excludes site search
- [ ] `checkValidity()` guard present
- [ ] No wrapper around `window.gtag`
- [ ] GA4 `generate_lead` sent separately from the Ads conversion
- [ ] Full test matrix run on live, results dated and recorded
- [ ] Monthly inbox-vs-platform gap checked

## Failure modes

| Symptom | Cause | Where |
|---|---|---|
| Paid traffic reports as direct/organic | `url_passthrough` missing, `gclid` dropped | `90` F-28 |
| Conversions look great, inbox is empty | Site-search submit counted as a lead | `90` F-11 |
| One enquiry counted twice | Click and submit both fire, no deduplication | `90` F-29 |
| Deduplication worked for a day, then stopped | Counter wrapped `window.gtag`, which was replaced | `90` F-30 |
| EU traffic shows no consent prompt | Third-party consent script quota exhausted | `90` F-31 |
| A form converts in the debugger, not for visitors | Nonce expired in a cached page | `90` F-16 |
