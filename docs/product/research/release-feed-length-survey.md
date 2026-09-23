# Bounding the length of a public "what shipped" feed

> Discipline: applied (practitioner-pattern survey)

Commissioned to answer whether `/now/` should adopt an age-based cutoff — a
rolling 30 days was the proposal — and whether it should paginate. Measured
2026-09-22 against the built site and four retrieval passes over practitioner
sources.

**Answer in one line: reject the age cutoff, fix the structure first, and treat
pagination as a later and separate decision.** The reasoning follows.

## What the surface actually is

Measured from `build/` and `now-highlights.generated.json` on 2026-09-22, not
carried over from the close-out:

| Property | Value |
| --- | --- |
| Release groups | 156 |
| HTML | 224 KB |
| Height at 320 CSS px | 107,902 px — 120 viewport heights at 900 |
| Height at 1100 CSS px | 49,747 px — 55 viewport heights |
| Headings on the page | **1** `<h2>`, 0 `<h3>` |
| `id` attributes on the page | **3** — `main`, `now-heading`, `now-releases-heading` |
| Outbound links to `/docs/changelog/` | 157 — one per group, plus an index link |

Two of those lines reframe the question and are the reason this survey does not
recommend what it was asked about.

## Findings

### 1. No comparable product truncates a release feed by age `[high]`

Twelve public changelog or release feeds were checked, the live surface visited
rather than an article about it: GitHub Releases, Stripe, Twilio, Linear,
Vercel, Tailwind, Supabase, Sentry, Cloudflare, Notion, Basecamp, and the Keep a
Changelog convention itself.

**Zero of twelve apply an age-based cutoff.** Every one either paginates by
count or offset with all history still reachable, or renders one long page
covering years — Tailwind's runs back to June 2020 on a single page, Supabase's
to October 2022. The only real choice these products make is *how much shows
before you click*, never *whether older entries stop existing*.

Five use numbered pagination (GitHub `?page=N`, Twilio, Sentry, Linear, Notion),
three a load-more or "Older Posts" chain that still resolves to a page-N URL
(Vercel, Basecamp, Linear), one offset-by-timestamp (Basecamp). Eleven of twelve
give each entry its own stable URL or anchor.

Downgrade factors considered and not applied: these are direct observations of
live surfaces, not vendor claims about themselves. Two observations are held
back as `[uncertain]` and appear under *Known unknowns* rather than here.

Keep a Changelog is silent on retention, truncation and pagination. Its only
adjacent principle cuts the other way: "A changelog which only mentions some of
the changes can be as dangerous as not having a changelog."

### 2. Rolling windows belong to recency claims, not cumulative ones `[moderate]`

Where a time window *is* the established pattern, the surface answers a recency
question. Atlassian Statuspage defaults to 90 days of uptime history — and even
there the full record stays one click away on a `/uptime` sub-page. A 2019
outage says nothing about today's reliability, so decay is the correct
behaviour.

A shipping history makes the opposite kind of claim. Its value is cumulative:
the archive *is* the argument. On the evidential side, Google's SearchLiaison
stated during the CNET pruning story that old content is not penalised — "That's
not a thing! ... Older content can still be helpful, too" — and John Mueller
called the SEO effect of that deletion "unlikely to be noticeable". Even the
qualified pro-pruning position from Google is *harmless*, not *beneficial*.

Rated `[moderate]` rather than `[high]`: the strongest anti-pruning source
(Crestodina's eleven-expert round-up) carries a documented survivorship problem
in both directions. The pro-pruning case studies bundled pruning with a
concurrent rewrite or migration, so the effect cannot be isolated; the
null-result cases surfaced only because that one author specifically solicited
them. The generic SEO-explainer cluster restating the crawl-budget argument
(Semrush, Surfer, SEO.com and others) is one voice, not five.

### 3. Our own cadence makes an age window useless `[high]`

This is local measurement, not literature. The whole 156-release history spans
**37 days**, 2026-08-16 to 2026-09-22.

| Window | Groups kept | Share of page |
| --- | ---: | ---: |
| Last 30 days | 142 | 91% |
| Last 60 days | 156 | 100% |
| Last 90 days | 156 | 100% |

A rolling 30-day window removes 14 of 156 groups and leaves roughly 109 viewport
heights instead of 120. The median gap between releases is **0 days** and the
longest gap in the entire history is **4 days**: 57 releases in August, 99 in a
partial September. The page is long because it is dense — about 4.2 releases per
day — not because it is old.

### 4. An age window on a bursty cadence can empty the page `[inference]`

Explicitly flagged as reasoned, not cited. Targeted searches found no
practitioner writing on age-window versus count-window behaviour for release
feeds specifically, and the searches that claimed to returned unrelated noise
that was discarded rather than dressed up as evidence.

The structural argument: an age window's item count varies with the calendar. On
an irregular cadence a quiet quarter yields a page with **zero items** — the
evidence surface goes blank exactly when a sceptical evaluator most needs to see
that the project still ships. A count window ("last 25 releases") degrades
gracefully and never empties. Our current cadence makes this remote today, and
permanent if the rule is written the wrong way round.

### 5. Page length is not a WCAG failure `[high]`

Worth stating plainly because the opposite is often asserted. SC 1.4.10 Reflow
restricts scrolling in *two* dimensions at 320 CSS px; vertical scrolling is the
assumed and accepted mechanism. Nothing in the criterion bounds total page
length, and no other numbered success criterion was found that does.

So `/now/` is a usability and information-architecture problem, not a compliance
one. That should set its priority. The accessibility case against very long
feeds rests on practitioner findings, not on a conformance violation.

### 6. If we ever paginate, the SEO shape is settled and has changed `[high]`

- `rel="next"` / `rel="prev"` were retired by Google as an indexing signal,
  announced 2019-03-21. Google's current pagination documentation, last updated
  2025-12-10, still states it does not use them. Bing reportedly still treats
  them as a discovery hint, so they are not universally dead.
- Current Google guidance: ordinary crawlable `<a href>` links between pages,
  and **each page carries its own self-referencing canonical**. The doc says
  explicitly: "Don't use the first page of a paginated sequence as the canonical
  page."
- The older "canonicalise everything to a View All page" advice traces to
  Google's 2011 post from the same now-dead era and is **not** reasserted in the
  current documentation. Treat as superseded.
- Googlebot "doesn't 'click' buttons and generally doesn't trigger JavaScript
  functions that require user actions". Content behind infinite scroll or a
  JS-only load-more is therefore invisible to it unless real paginated URLs
  exist as a fallback.

### 7. Infinite scroll is the one option to rule out `[high]`

NN/g, Deque and W3C WAI converge independently. Keyboard users hit a dead end,
because content loads on scroll position rather than on focus reaching the end.
The footer can become permanently unreachable. `role="feed"` is a real partial
remedy but helps only screen-reader users in browse mode — it does nothing for
keyboard-only, switch or speech-recognition users.

A load-more button needs focus moved to the first newly loaded item plus a
polite live-region announcement. That is converged practitioner guidance, not a
normative rule: SC 4.1.3 Status Messages covers the *announcement*, and its
Understanding document explicitly excludes the loaded results themselves. SC
2.4.3 Focus Order is frequently mis-cited for this and does not cleanly apply.

### 8. Deep links survive collapse in all three engines — measured here `[high]`

The retrieval pass flagged Safari's plain `#id` behaviour as its single biggest
open risk: WebKit's own Safari 26.2 announcement names only Find and Text
Fragment as auto-expand triggers, not plain anchors.

Tested directly rather than left open. A closed `<details>` containing an
`#anchor` target, loaded cold:

| Engine | Version | `<details>` auto-opened | Target rendered |
| --- | --- | --- | --- |
| Chromium | 153.0.8010.12 | yes | yes |
| Firefox | 155.0 | yes | yes |
| WebKit | 26.6 | yes | yes |

All three scrolled to the target. This closes the retrieval pass's open question
for the engine, with one honest limit: Playwright's WebKit is the engine, not
shipping Safari, and iOS Safari is untested. The same distinction the manifest
already draws for VoiceOver applies.

### 9. `<summary>` is not a heading, and screen-reader support is uneven `[moderate]`

Scott O'Hara documents that `<summary>` exposes an implicit button role, and a
button treats its contents as presentational — so an `<h2>` inside a `<summary>`
is not exposed as a heading. Announcement varies across pairings ("Disclosure
Triangle", "Button", "Summary", or nothing), and forcing `role="button"` to
normalise it breaks state announcement in macOS Safari with VoiceOver. Removing
the default marker breaks state communication in Firefox with VoiceOver, because
the triangle is that pairing's only state channel. Adrian Roselli adds that many
independent `<details>` need an explicit group label to read as a related set.

For `/now/` specifically this objection is currently moot in one direction and
sharp in the other: **the page has no per-group headings to lose**. It also
means disclosure would be layered onto a page that has no heading structure to
begin with, which is the wrong order of operations.

## Keeping history far back — the strategies people actually use

Commissioned as a follow-up once the owner confirmed the archive stays
complete. The question stops being *what to cut* and becomes *what makes a
permanently growing archive navigable*. Seven mechanisms recur, and they
compose rather than compete.

| Mechanism | Who, observed live | What it buys | Where it stops working |
| --- | --- | --- | --- |
| Date index / jump-to | Sentry — month dropdown back to March 2023 | Non-adjacent jumps | A flat list needs a year→month split eventually |
| Year/month archive routes | Simon Willison — year links 2002–2026 into month and day pages | Permanent, linkable structure | Degrades into dead ends unless pages chain to neighbours |
| Numbered pagination | GitHub, Twilio, Sentry, Linear, Notion | Bounds page weight; crawlable | Adds a click between reader and evidence |
| Faceted filtering | Twilio — 50+ product filter | Narrows a large corpus by dimension | A flat 50-item dropdown is its own scaling problem |
| Version-train grouping | Stripe — Dahlia / Clover / Basil | Matches "which release am I on" | Only when readers navigate by version, not date |
| Full RSS/Atom feed | Sentry, Simon Willison | Moves completeness off the HTML page | None found — the cheapest of the seven |
| `content-visibility: auto` | Nolan Lawson, 40,000 nodes | Render cost, not bytes | **Breaks find-in-page in WebKit** |

`[high]` The evidenced stacks are coherent, not arbitrary. Sentry runs index +
pagination + feed simultaneously. Twilio runs facets + pagination + feed, with
facets substituting for the index rather than for pagination. Stripe runs
version-trains on one long page with no pagination at all, which works because
its entries are short table rows and its readers navigate by release rather
than by date.

`[moderate]` The feed is the highest value per unit of effort. Two independent
sources publish a full-history feed explicitly covering everything, which lets
the HTML page be a display and navigation layer rather than also being the
exhaustive machine-readable record. We publish no feed today.

`[moderate]` `content-visibility: auto` carries a caveat that disqualifies it
here. Google's own demo reports 232 ms → 30 ms initial render, and Nolan
Lawson measured ~45% on a 40,000-node page with no find-in-page or scrollbar
breakage in Chromium and Firefox. But WebKit's implementation is reported
broken for find-in-page — text inside skipped subtrees cannot be found. On a
page whose primary job is "find the release I remember", that is the wrong
trade until WebKit is fixed. `[moderate]` not `[high]`: the defect reaches us
through one secondary citation of an independent report, and its current status
was not re-verified against the WebKit tracker.

`[moderate]` Client-side search costs less than its reputation. Lunr and Fuse
ship the whole index — cited at 2–4 MB for ~1,100 entries — while Pagefind
shards and lazy-loads, claimed under 30 KB initial. At a few hundred entries
either is tolerable. Treat the figures as vendor-adjacent; they come from
comparison posts, not a controlled benchmark. Relevant local fact: **Pagefind
already ships in this repository**, on the docs site via Starlight, so part of
the build-step cost is already paid.

## Recommendation

**Do not adopt an age-based cutoff.** Findings 1, 2 and 3 agree: nobody does it,
it suits a recency claim rather than a cumulative one, and on our cadence a
30-day window would cut 9% of the page. It would also write a rule whose failure
mode is blanking the page during a quiet stretch.

**Step 1 — fix the structure, not the length. Do this first.** The page has one
heading and three ids for 156 groups. A screen-reader user cannot skim it by
heading; nobody can link to a single release on it; and there is no in-page
contents or return-to-top, which is exactly what the original finding named. Give
each group a heading and a stable `id`, add in-page contents and return-to-top.
No route change, no build change, no URL change — and because no inbound
per-release anchors exist today, nothing can break. This addresses the "can't
find anything" complaint directly and is the prerequisite for anything below.

**Step 1 shipped 2026-09-22.** Measured after: headings on the page went from
**2 to 162**, every release carries its `changelogAnchor` as a stable `id`, and
a 31-entry date index links each day to its first release. At 320 the index
collapses to one column with no horizontal overflow; at 1100 it is four
columns. The page is fractionally *longer* — 120.3 viewport heights against
119.9, and 235 KB against 224 KB — which is the honest outcome: step 1 makes
the page navigable, it does not make it short. Bounding it is steps 2 and 3.

**Step 2 — publish a feed. Cheap, and it changes what the page must carry.**
An Atom or RSS feed covering the complete history is the one mechanism with no
identified downside, and it is what lets the HTML page be a navigation layer
rather than the exhaustive record.

**Step 2 shipped 2026-09-22.** `/now/feed.xml`, Atom 1.0, 186 KB, all 156
releases, advertised from `/now/` through a `rel="alternate"` link. Atom rather
than RSS because it specifies its date format and requires `<id>` to be a
permanent unique IRI, and a feed of release records wants stable identity above
all — a reader that re-shows every entry on each fetch is worse than no feed.
Entry ids are the release anchors step 1 put on the page, so the feed and the
page name a release the same way.

No new dependency: `@astrojs/rss` would do it, but a static endpoint returning
a string does it with nothing but the standard library. The cost is that the
XML escaping is ours, so it is one function used at every interpolation, and
seven guards assert the result against a real XML parser rather than a regex —
entry count against the projection, id uniqueness and resolvability against the
page's anchors, RFC 3339 on every timestamp, and markup surviving the round
trip. The corpus exercises `<`, `>`, `"` and `'` on its own (`agentbundle
upgrade --skill <name>` is in there); `&` appears nowhere in it, so that branch
is covered by a direct test of the escaper including the ordering case where a
late ampersand replacement would turn `<` into `&amp;lt;`.

**Step 3 — re-measure, then bound the page.** Length is not a compliance
failure (finding 5), so the bar is whether the page is still unusable after
steps 1 and 2. When it is, adopt the evidenced trio — **index + numbered
pagination + feed**, which is Sentry's exact stack:

- *Numbered pagination* is the majority pattern and the SEO-safe one, provided
  each page self-canonicalises and pages link with ordinary `<a href>`. Cheap
  here, because step 1 gives the anchors and nothing external links into
  per-release fragments.
- *Permalinks shipped 2026-09-22, ahead of pagination and for this reason.*
  `/now/<anchor>/`, 156 pages, and the feed's entry ids now name them instead
  of `/now/#<anchor>`. The build went 51 pages to 207 and stayed under 5s. The
  dependency below is therefore discharged, and pagination can proceed without
  breaking a published identity.
- *Pagination now has a dependency it did not have when this was written.* The
  feed's entry `<id>`s are `/now/#<anchor>`, and an `<id>` must be permanent.
  Paginating `/now/` moves an older release off that URL, so every feed id for
  it silently stops resolving. The fix is the shape 11 of the 12 surveyed
  products already use — a per-release permalink, `/now/<anchor>/`, which the
  feed points at instead. That makes step 3 "permalinks + pagination", not
  "pagination", and it is the reason to decide it deliberately rather than
  treat it as a rendering change.
- *The date index needs a second level as history grows.* It lists 31 dates
  today. At a year it would list several hundred, which is a second long page,
  so it becomes year → month before then.
- *Progressive disclosure* keeps one URL and is safe for deep links (finding 8),
  but it does not reduce the 235 KB and it adds a widget with the uneven
  screen-reader behaviour of finding 9.
- *`content-visibility: auto`* is tempting for render cost and is ruled out for
  now by the WebKit find-in-page defect above.
- *Infinite scroll* is ruled out by finding 7.

Prefer pagination over disclosure if step 2 is needed at all. Disclosure hides
the symptom and keeps the payload; pagination fixes both and matches what
comparable products do.

**The trade-off, stated.** Pagination splits one URL's accumulated signals
across N and adds a click between a reader and older evidence, on a page whose
purpose is to make the volume of shipped work visible at a glance. That cost is
real and is the reason step 2 is conditional rather than recommended outright.

## Known unknowns

- **Known-unknown:** whether `/now/` is still unusable after step 1. Would be
  closed by: re-running the 320 and 1100 measurements once headings, in-page
  contents and return-to-top exist, and deciding against the result rather than
  against today's number.
- **Known-unknown:** whether plain `#id` anchors auto-expand a closed
  `<details>` in *shipping* Safari and iOS Safari. Would be closed by: a manual
  check on a real device. Playwright's WebKit 26.6 says yes and is strong
  evidence for the engine, but it is not Safari. A three-line JS fallback that
  opens the targeted `<details>` on load removes the question entirely and is
  worth shipping regardless.
- **Known-unknown:** what caniuse's "partial support" flag on `hidden=until-found`
  is keying on for current Firefox and Safari. MDN calls the feature Baseline
  newly-available since December 2025; caniuse still shows partial. The two
  trackers disagree and no primary source was found resolving it. Only relevant
  if we adopt `hidden=until-found` rather than plain `<details>`.
- **Known-unknown:** whether Cloudflare's changelog and Supabase's really lack a
  cutoff. Both were fetched without JavaScript execution, so a lazy-load
  mechanism would have been invisible. Excluded from the "zero of twelve" claim's
  load-bearing weight; ten of the twelve were confirmed directly.
- **Unknowable from available evidence:** whether pagination helps or hurts a
  low-traffic evidence page specifically. All retrievable guidance targets
  large e-commerce catalogues where crawl budget and duplicate dilution are the
  concern. No source addresses this scenario, and the counterfactual cannot be
  run on a single site.

## Adjacent defect found while measuring

`/docs/changelog/` — the archive every one of the 157 outbound links points at —
is **2.08 MB of HTML with 297 headings**, 9.3× the page this survey is about. Any
recommendation that routes readers "to the full changelog for older entries"
sends them somewhere heavier than where they started. Registered separately
rather than folded into this decision.

## Sources

Deduplicated by practitioner and vendor cluster; several posts from one vendor
count as one voice.

**Live product surfaces** — [GitHub Releases](https://github.com/rails/rails/releases),
[Stripe](https://docs.stripe.com/changelog), [Twilio](https://www.twilio.com/en-us/changelog),
[Linear](https://linear.app/changelog), [Vercel](https://vercel.com/changelog),
[Tailwind](https://tailwindcss.com/blog), [Supabase](https://supabase.com/changelog),
[Sentry](https://sentry.io/changelog/), [Cloudflare](https://developers.cloudflare.com/changelog/),
[Notion](https://www.notion.com/releases), [Basecamp](https://updates.37signals.com/post/category/Basecamp).

**Conventions and standards** — [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/);
W3C WAI Understanding docs for [1.4.10 Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html),
[4.1.3 Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html),
[2.4.3 Focus Order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order);
[WAI-ARIA APG Feed Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/feed/).

**Search engine guidance** — [Google pagination best practices](https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading)
(updated 2025-12-10); [Search Engine Land on the rel=next/prev retirement](https://searchengineland.com/google-no-longer-supports-relnext-prev-314319)
(2019-03); [Search Engine Roundtable](https://www.seroundtable.com/google-cnet-content-pruning-plans-35876.html)
and [MediaPost](https://www.mediapost.com/publications/article/388152/google-warns-against-content-pruning-as-cnet-del.html)
(2023-08) relaying the Mueller / SearchLiaison statements.

**Accessibility practitioners** — [NN/g on infinite scrolling](https://www.nngroup.com/articles/infinite-scrolling-tips/)
(2022-09-04); [Deque on infinite scroll and role=feed](https://www.deque.com/blog/infinite-scrolling-rolefeed-accessibility-issues/)
(2019-10-02); [Scott O'Hara on details/summary](https://www.scottohara.me/blog/2022/09/12/details-summary.html)
(2022); [Adrian Roselli](http://adrianroselli.com/2023/08/progressively-enhanced-html-accordion.html)
(2023); [Aleksandr Hovhannisyan on load-more focus](https://www.aleksandrhovhannisyan.com/blog/load-more-button-focus/)
(2021, updated 2022).

**Browser support** — [WebKit Features for Safari 26.2](https://webkit.org/blog/17640/webkit-features-for-safari-26-2/)
(2025-12-12); [Bugzilla 1724299](https://bugzilla.mozilla.org/show_bug.cgi?id=1724299)
(Firefox 139, 2025-05-27); [Chrome Platform Status 5032469667512320](https://chromestatus.com/feature/5032469667512320)
(M96); [whatwg/html PR #6466](https://github.com/whatwg/html/pull/6466).

**Content pruning debate** — [Crestodina, Orbit Media](https://www.orbitmedia.com/blog/deleting-old-content/),
counted as one voice carrying eleven named practitioners on both sides;
the generic SEO-explainer cluster ([representative](https://www.semrush.com/blog/content-pruning/))
counted as one.

**Status pages** — [Atlassian Statuspage historical uptime](https://support.atlassian.com/statuspage/docs/display-historical-uptime-of-components/).
