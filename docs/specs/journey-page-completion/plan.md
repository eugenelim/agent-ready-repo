# Plan: Journey page completion

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; substantive changes are recorded below.

## Approach

Establish the semantic-ID contract and failure cases first, migrate the exact
34 approved mappings in canonical sources, and regenerate all derived copies.
Then add the three accepted editorial payloads and adapt rendering to keep IDs
internal while labels, focus, and fragments behave predictably. Exhaustive
emitted and browser tests close the work; source shape alone is insufficient.

## Constraints

- `packs/*/JOURNEY.md` remains canonical; generated copies are never edited
  independently.
- [`editorial-decisions.md`](editorial-decisions.md) is the accepted mapping,
  copy, and interaction ledger; implementation does not reclassify it.
- `docs/design/principles/tech-site.md` and
  `docs/specs/platform-site/aesthetic-direction.md` govern visual decisions.
- Priority content is limited to `core`, `product-engineering`, and
  `release-engineering`.
- No dependency, public route, navigation change, pack-version bump, or
  plugin-description change.
- Shipped `JOURNEY.md` content carries no internal governance citation.

## Construction tests

**Integration tests:** validate all 34 mappings, regenerate every journey,
build the marketing site, enumerate every emitted gate link and target across
all 12 pages, prove no raw identifier is visible, then run the combined
page-and-fragment checker.

**Manual verification:** the exact editorial content already carries recorded
approval. Rendered design review covers all three priority routes, while the
programme's physical-device gesture remains separate from deterministic
browser tests.

## Design (LLD)

### Design decisions

- `decisionGateIds` is the sole decision-to-gate relationship and
  `humanGates[].label` is the sole visible-label source. Parallel display
  strings are rejected because they drift. Traces to: AC1-AC5.
- Identity is `(journey_id, gate.id)` and the renderer adds only the fixed
  `decision-` fragment prefix. Label normalization and order-based identity are
  rejected. Traces to: AC2, AC3, AC6, AC7.
- All journey sources adopt the identifier contract in one migration, while
  editorial additions remain priority-only. Traces to: AC2, AC8.

### Data & schema

- Every human gate owns one stable lowercase semantic ID;
  `contract.decisionGateIds` is an ordered array of those IDs. Validation
  rejects malformed values, duplicates, and missing references. Traces to:
  AC1-AC3, AC7.
- Optional `eyebrow` and `goodOutputDescription` are required by construction
  tests only for the three approved priority IDs. Traces to: AC8, AC9.

### Component / module decomposition

- `JourneyContract.astro` resolves IDs to gate labels and emits links and
  derived ordinals.
- `GateDetail.astro` owns the matching focusable heading and fragment target.
- The journey page owns eyebrow and transcript placement without changing the
  route shell. Traces to: AC4-AC9.

### State & control flow

- Build-time validation fails before rendering when an ID is malformed,
  missing, duplicate, or ambiguous. Valid IDs flow from canonical pack source
  through generated content to both chip href and heading DOM ID. Traces to:
  AC1-AC7, AC11.
- Native links update the URL; a narrowly bounded enhancement moves focus and
  scrolls the matching heading without inventing a second identity or label
  store. Traces to: AC6, AC7.

### Quality attributes (NFRs)

- Exhaustive emitted checks cover all 12 journeys; browser checks cover every
  priority chip at all approved widths and themes. Traces to: AC12, AC15.

## Tasks

### T1: Invalid journey identity contracts fail before rendering

**Depends on:** none

**Touches:** web/src/content.config.ts, tools/test_build_site_routing.py, tools/test_catalogue_navigation.py

**Tests:**
- TDD: add failing fixtures for malformed, missing, duplicate, and unresolved
  IDs and for a display string supplied where an ID is required (AC1-AC3, AC7).
- TDD: prove label changes and gate reordering preserve fragments while only
  displayed ordinals change (AC3, AC4).

**Approach:**
- Define the internal semantic-key and referential-integrity contract.
- Keep labels on human-gate definitions only.

**Done when:** each invalid fixture fails for the intended reason and both
identity-independence mutations pass.

### T2: Canonical journeys adopt the exact 34-ID mapping

**Depends on:** T1

**Touches:** packs/*/JOURNEY.md

**Tests:**
- Goal-based: enumerate all 34 ledger rows and prove every canonical source has
  the exact ID, label, order, and reference (AC1, AC2).
- Goal-based: prove visible source content contains no legacy gate code, raw
  semantic ID, slash-prefixed invocation, or internal governance citation
  (AC5, AC9, AC14).

**Approach:**
- Apply only the accepted mapping to canonical sources; retain `globalGate`
  only as non-rendered source coordination metadata where still required.
- Replace visible legacy-code references with their approved labels.
- Do not change pack/plugin versions, plugin descriptions, or changelogs.

**Done when:** all 34 mappings validate, legacy identifiers are absent from
visible content, and installed-payload metadata is unchanged.

### T3: Generated journey copies reproduce canonical identity exactly

**Depends on:** T2

**Touches:** tools/build-site.py, web/src/content/journeys/*.md, marketplace.json

**Tests:**
- Goal-based: regenerate all journey copies and assert byte-appropriate
  canonical parity for IDs, labels, order, and source content (AC11).
- Goal-based: prove all 12 existing route IDs remain present and pack/plugin
  versions and descriptions are unchanged (AC13, AC14).

**Approach:**
- Run the existing projector; never edit a generated copy by hand.
- Recalculate catalogue/marketplace output only where deterministic projection
  requires it, without changing installed version metadata.

**Done when:** projection is clean, route inventory is stable, and no version
or description drift exists.

### T4: Priority journeys receive the accepted editorial payload

**Depends on:** T3

**Touches:** packs/core/JOURNEY.md, packs/product-engineering/JOURNEY.md, packs/release-engineering/JOURNEY.md, web/src/content/journeys/*.md

**Tests:**
- Goal-based: compare the three eyebrows and transcripts verbatim with the
  ledger and prove non-priority journeys remain optional (AC8, AC9).
- Goal-based: regenerate and recheck canonical parity (AC11).

**Approach:**
- Copy the accepted content verbatim, using ordinary routing language for Core
  and explicit bare skill names for the two supervisor-dependent examples.
- Regenerate derived copies.

**Done when:** all six fields match the ledger and generated copies match their
canonical sources.

### T5: Decision chips expose human labels and stable interaction

**Depends on:** T3, T4

**Touches:** web/src/components/journeys/JourneyContract.astro, web/src/components/journeys/GateDetail.astro

**Tests:**
- Goal-based: enumerate every emitted chip and assert label ownership, order,
  derived ordinal, exact href, unique target, fixed section copy, and absence
  of visible identifiers (AC4-AC6, AC12).
- TDD: seed a broken fragment and prove the combined checker fails (AC7, AC12).

**Approach:**
- Resolve IDs once in the renderer and pass the stable ID to both link and
  heading while rendering labels only from the gate definition.
- Use native links plus the smallest focus/scroll behavior needed by the
  accepted interaction contract.

**Done when:** emitted HTML proves every one-to-one relationship and no raw ID
or legacy code is adopter-visible.

### T6: Priority pages pass emitted, browser, and design evidence

**Depends on:** T5, spec:site-browser-quality-gate/T2

**Touches:** docs/specs/platform-site/journey-page-template.md, tools/test_build_site_routing.py, web/src/test/e2e/**/*.ts

**Tests:**
- Goal-based: assert the living template uses `product-engineering` and
  `release-engineering`, not stale aliases (AC10).
- Goal-based: enumerate all 12 emitted pages and run the combined route and
  fragment checker (AC12, AC14).
- Goal-based E2E: activate every priority chip by keyboard at all approved
  widths and themes; assert fragment, focus, scroll, direct-load, overflow, and
  axe behavior (AC6, AC7, AC15).
- Visual/manual QA: review the three rendered priority routes against the named
  aesthetic direction and tech-site principles (AC15).

**Approach:**
- Correct only the stale living-template IDs.
- Verify emitted behavior; do not treat source props or screenshot existence as
  proof.

**Done when:** exhaustive emitted checks, the browser matrix, and recorded
design review pass with unchanged routes.

## Rollout

Land validation before the all-source migration, then regenerate before adding
editorial content and renderer behavior. Keep canonical and generated copies
coherent at every task boundary. Rollback is a normal source revert; there is
no version, dependency, migration, or infrastructure change.

## Risks

- Hand-assigned IDs can collide; the exact ledger, complete enumeration, and
  mutation-sensitive validation make uniqueness and stability build invariants.
- IDs can leak through otherwise convenient rendering; emitted text assertions
  across all 12 pages prevent internal vocabulary from becoming UI copy.
- Runtime activation cannot be proven by transcript copy; adapter/runtime
  tests retain ownership of that behavior.

## Changelog

- 2026-08-17: initial plan after approval of the priority and canonical gate-ID
  contracts.
- 2026-08-17: fixed the 34-ID mapping, label ownership, invisible-ID behavior,
  exact priority copy, invocation convention, unchanged-version consequence,
  deterministic migration order, and exhaustive evidence contract.
- 2026-08-18: applied the approved 34 semantic IDs and labels. Reconciled the
  three affected gate bodies minimally: `decide-rfc` now uses the RFC outcomes
  accepted or rejected (the RFC vocabulary in `docs/CONVENTIONS.md` contains no
  Deferred status); `approve-journey` now matches the derived-screen review;
  and `approve-okr-cascade` now matches its gap-ranking and routing work.
- 2026-08-18: rewrote canonical rendered legacy-code prose by mechanical
  substitution. The six hand-authored journeys remain deferred as
  `legacy-hand-authored-journey-gate-mappings` because the approved ledger has
  no semantic ID or label mappings for them.
- 2026-08-18: made decision fragments conditional on `decisionGateIds`.
  Canonical journeys emit stable semantic fragments and keyboard/focus behavior;
  hand-authored `yourDecisions` journeys remain display-only, preventing new
  durable links from legacy codes.
- 2026-08-18: discharged `browser-gate-journey-chip-cases-inert`. The six
  decision-chip cases in `web/src/test/e2e/site-quality-gate.spec.ts`, which
  `spec/site-browser-quality-gate` registered because semantic chips were absent
  and the cases skipped, now run and pass: 112 passed, 0 skipped, for core,
  product-engineering, and release-engineering at 360 and 1440. This spec
  withdrew the entry from `[backlog].open`.
- 2026-08-18: expanded priority decision-chip interaction coverage to all five
  approved marketing widths. Themes are deliberately not mutated for journey
  routes: `docs/specs/site-browser-quality-gate/spec.md:78` requires marketing
  routes to run without theme mutation; the marketing matrix already supplies
  their all-width overflow, axe, and fragment coverage.
- 2026-08-18: reconciled three shortened labels with their gate bodies only:
  `decide-rfc` removes the stale Deferred vocabulary (RFC statuses are defined
  in `docs/CONVENTIONS.md`), `approve-journey` narrows the screen-list check to
  its derivation from the journey, and `approve-okr-cascade` names the cascade
  rather than its downstream gap routing.
- 2026-08-18: decision fragments, chip hrefs, and focus behavior are conditional
  on `decisionGateIds`; this avoids minting public fragments from legacy codes on
  hand-authored journeys. Their unresolved display-copy migration is deferred as
  `legacy-hand-authored-journey-gate-mappings` pending approved ledger mappings.
- 2026-08-19: closed two evidence gaps found after the gates were green. The
  independent reviewer showed the priority eyebrow and transcript copy had no
  automated control, though the evidence contract requires the three priority
  pages to emit it exactly; `tools/test_journey_editorial_decisions.py` now
  compares the ledger against canonical frontmatter byte-for-byte and confines
  eyebrows to the priority set. A sweep of the evidence contract against the
  suite then showed direct fragment loading was equally unverified, so the
  browser gate gained six cold-load cases. Both are mutation-proved: a one-word
  eyebrow or transcript drift fails, an eyebrow added to a non-priority journey
  fails, and removing the gate heading's `tabindex="-1"` fails every cold-load
  case. Transcript absence is deliberately not asserted for non-priority
  journeys — `atlassian` carried a `goodOutputDescription` before this spec.
- 2026-08-19: recorded that cold-load focus is provided by the HTML
  fragment-navigation algorithm focusing a focusable target, not by the inline
  script, which serves the same-document `hashchange` path. The two mechanisms
  are complementary, and the new cases pin both.
- 2026-08-19: amended AC15 to drop "in both approved themes". Journey routes are
  marketing routes, which `site-browser-quality-gate` AC1 exercises without
  theme mutation, and their emitted pages carry no `data-theme`; that spec's AC2
  owns dual-theme coverage for the two `/docs/` routes. No approved theme,
  width, overflow tolerance, or axe threshold changed — the clause named a
  condition these routes cannot express.
- 2026-08-19: hardened the editorial control after independent review showed the
  first version could not support AC8's word "verbatim": both sides trimmed
  whitespace and dropped blank lines, so an inserted blank paragraph or a
  re-indented line compared equal. Each side now strips only the presentation its
  own format forces — the ledger's blockquote marker and hard-break spaces — and
  the canonical side is compared byte-for-byte with no trailing-space
  normalisation, so stray whitespace in a pack fails. Both sides mirror YAML
  `|-` chomping so a layout-only blank line before the closing fence is not a
  false failure. AC8 now names the three tolerated presentation differences
  instead of claiming an unqualified "verbatim". Transcript confinement uses
  subset rather than set equality: the ledger's claim is that no journey *gains*
  a transcript, and equality would have pinned `atlassian`'s pre-existing copy in
  place forever. Proved by MP11–MP15 — mid-transcript blank line, extra
  indentation, a stray trailing space, and a transcript added to a non-priority
  journey all fail; a trailing blank line before the fence correctly does not.
- 2026-08-19: narrowed the ledger-side normalisation after review showed it was
  broader than AC8 claimed. `rstrip(" ")` removed any number of trailing spaces,
  but a Markdown hard break is two or more; a one-space edit therefore changed
  the ledger's rendering while still comparing equal. The parser now strips
  trailing spaces only when there are at least two, and preserves a lone
  trailing space so it fails. AC8 also dropped the phrase "byte-for-byte", which
  overclaimed: both sources are decoded and split, so line endings are
  normalised rather than compared. Proved by MP16 (hard break 2 -> 1 space now
  fails, previously passed) and MP17 (2 -> 3 spaces still passes, since three
  spaces is still a hard break).
- 2026-08-19: extended the published catalogue contract additively, under
  explicit authorization, after CI surfaced a conflict local gates could not see.
  `tests/roster/test_catalogue_wave4_live_contracts.py` arrived in #1025 — one of
  the eleven commits this branch rebased onto — and is wired only in
  `build-check.yml`, never the Makefile, so `make build-check` passed locally
  while `gate-main` failed. Its validator treats `contract.*` as a closed set and
  also requires `yourDecisions`, so the ratified `contract.decisionGateIds` was
  rejected on all 12 canonical packs. Because the approved ledger fixes the field
  inside `contract`, relocating it was not available, even though unknown
  top-level keys are accepted today. AC13 routes a discovered installed-output
  change to a spec amendment rather than a silent version bump, so the work
  stopped and asked. The authorized resolution is additive: `decisionGateIds`
  optional in `journey_validator`, both byte-identical schema copies, and both
  authoring-standard copies; `yourDecisions` remains required and was restored
  byte-for-byte from the merge-base into all 12 packs. Adopter impact is nil.
  MP18-MP20 prove the change did not open the gate: removing `yourDecisions`
  still fails, a non-array `decisionGateIds` fails, and an unknown contract field
  still fails. The scaffold copy is a projection, so `manifest.json` was
  regenerated with `tools/catalogue/sync_authoring_scaffold.py --write` rather
  than hand-edited.
- 2026-08-19: fixed the recorded design review's three Major findings. Two were
  contrast failures invisible to the browser gate by construction: axe scans the
  resting DOM, so a `:hover`/`:focus-visible` declaration never applies during the
  scan, which is how a chip whose focus style measured 2.40:1 passed a green
  accessibility gate. The chip's focused text is now the system's own
  dark-on-amber CTA pairing (8.07:1) and the gate heading's ring is the same
  near-black the chip already used (16.74:1), so one interaction stops speaking
  two focus languages. The third was a presentation defect the ledger control
  could not see: it compares source to source and was green throughout while the
  rendered page showed markup characters. `parseTranscript` now returns speaker
  turns and the template renders real elements in the page's mono register — no
  Markdown dependency, no `set:html`, so no injection surface. Three new controls
  close the gaps: `expectTextContrast` and `expectOutlineContrast` measure the
  state the element is actually in and composite alpha rather than treating a
  translucent token as an opaque fill, and a transcript case asserts multiple
  attributed turns with no `*` or backtick reaching the reader. MP24-MP26 prove
  each fails without its fix, reproducing 2.40:1, 2.08:1 and a missing transcript.
  Also moved the spec's workspace entry from `queue` to the initiative's existing
  empty `active` list, clearing the `impossible_transition` and `unapproved_spec`
  findings that a merged-but-Implementing artifact produced in a queue.
- 2026-08-19: re-review of the three Major fixes confirmed all three resolved and
  found two more. One was a regression this branch introduced: the transcript fix
  changed a shared template, and `atlassian` ships a `goodOutputDescription` that
  is prose rather than a session — the grandfathered field whose allowlist entry
  this spec already carries. It was rendering as a single unattributed turn: an
  empty `<dt>` around 127 words of author prose in the 13px mono session register,
  asserting session evidence for a paraphrase. The template now branches on the
  parse result and prose renders in the prose register. The control could not see
  it because it looped only the three priority routes, so it is now enumerated
  from the built site and covers all 18 journey routes; MP27 forces every route
  into the session register and fails exactly one of eighteen. A guard case
  asserts the enumeration is non-empty, because an empty route list would make
  every case vacuous.
  The second was a Minor this branch made conspicuous rather than caused: the gate
  heading and its card both painted an identical 3px near-black ring at the same
  offset, verified from computed styles on both elements. Invisible while both sat
  at 2.08:1; obvious at 15:1. The heading now owns the indicator for both
  `:focus-visible` and `:target`, so the cold-load path that needs its own
  selector survives — programmatic focus on a `tabindex="-1"` heading matches
  `:focus-visible` only by Chromium heuristic — and the card computes
  `outline-style: none`.
  Deferred to its own PR by owner decision: the review's M2, the global
  `:focus-visible` amber ring in `web/src/styles/base.css`, which measures 2.29:1
  on light surfaces against a 3:1 non-text floor and 8.07:1 on the dark hero where
  it is correct. It is pre-existing, owned by the design-system layer, and lands on
  every marketing route, so it warrants its own review rather than riding along in
  a journey-pages fix. AC15 stays unticked until it is resolved and re-reviewed.
- 2026-08-19: resolved the design review's M2, the last known blocker on AC15's
  design-review clause. The global `:focus-visible` ring was `--ds-accent` at
  2.29:1 on the light page and 2.08:1 on the card, under the 3:1 non-text floor,
  while being correct at 8.07:1 on the dark hero — so a blanket swap would have
  broken what worked. A `--ds-focus-ring` semantic token now carries
  `--ds-on-surface` (16.49:1) by default and is re-declared to `--ds-accent` on
  dark carriers, which works because the override lives in the global stylesheet
  where it can match Astro's rendered classes and inherit into scoped descendants.
  `--ds-on-surface` was chosen over `--ds-accent-deep` (5.43:1) so the whole site
  speaks one focus language, matching the journey controls; a second focus colour
  on the same page had itself been flagged.
  The authored patch contained a defect no static reading caught. Its dark-carrier
  list included `.journey-narrative pre`, which looks right — those syntax
  highlighted blocks carry `--ds-hero-bg` and receive `tabindex` when they overflow.
  But `outline-offset` draws a ring OUTSIDE the element's box, so those four
  focusable blocks had an amber ring landing on the light page at rgb(250,250,249):
  2.29:1, the exact defect being fixed, reintroduced. Measured in a browser, not
  read. The rule is that the token must describe the surface behind the ring, so
  dark *containers* belong in the list and focusable dark *elements* do not; the
  entry was removed and the reasoning recorded in `tokens.css` so it is not re-added.
  That is also why the control is not a list. `expectEveryFocusStopHasContrastingRing`
  walks real Tab stops, measures each ring against its composited backdrop, and ends
  on one full focus cycle — a fixed 160-press walk took 40s on `/journeys/` and blew
  the case budget. It runs over AC1's matrix plus `/primitives-fixture`, which is not
  added to `MARKETING_ROUTES` because that constant is the ratified AC1 set, but is
  the only place five of the changed primitives render. MP28 restores the original
  defect and fails 17 cases naming `a.skip-nav` 2.29:1 and `a.loop__link` 2.08:1;
  MP29 restores the authored defect and fails on `pre.astro-code.github-dark` at
  2.29:1. Both restorations byte-identical.
