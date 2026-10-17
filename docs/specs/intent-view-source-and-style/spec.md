# Spec: Intent view source parts and refined style

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-16 by eugenelim, spec and plan, after spec-mode shaping (clean, round 3) and adversarial (clean, round 3) reviews.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105, RFC-0108 (as corrected by its 2026-10-16 errata entry), ADR-0007, ADR-0074
- **Amends:** [intent-navigation-export](../intent-navigation-export/spec.md) — its criterion 0065 ("no `transition`, `animation`, or `@keyframes`"), which AC-0011 to AC-0015 replace. [intent-view-session-start](../intent-view-session-start/spec.md) — the first sentence of its criterion 0027, which AC-0009 replaces; the motion half of its second sentence, which AC-0011 to AC-0015 replace, while its `url(` and `@import` half carries over unchanged; and its criterion 0028, which AC-0010 narrows by also banning shadows, radii, motion and every custom-property declaration in `view.css`. Every other criterion of both specs, including session-start 0014's state-line contents, carries over unchanged.
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

A maintainer who opens the exported intent view sees a calmer, more polished page — soft panels for the list and the detail, tinted state labels that still read as a word plus a shape, a detail card whose sections, broken entries and trail read at a glance, and short colour fades that stop when their system asks for reduced motion — with every list, count, link and control behaving as before. A maintainer who changes the view edits its script as named source parts of a readable size instead of one long file, and the exported page still carries one hashed script and one hashed style under the same content security policy.

## What Changes

- The view's script moves from one file to ordered source parts — `packs/core/.apm/skills/navigate-intents/scripts/view_src/*.js`, replacing `view_assets/view.js`.
- The page builder joins the parts into the page's one script and refuses a missing or unsafe part — `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py`.
- The shared stylesheet takes the refined colour, radius, elevation, state-mark and motion rules — `view_assets/view-base.css`; the layout stylesheet takes the zone padding, gaps and wide-width column split — `view_assets/view.css`.
- The detail card gains three styling hooks (a state-meta span, a class on a non-empty "What is broken" part, a class on a diagnostic's raw text) and the search field gains a placeholder — `view_src/detail-parts.js`, `view_src/detail-render.js`, `intent_view.py`.
- RFC-0108 gains an errata entry that admits reduced-motion-aware colour and fade motion — `docs/rfc/0108-skill-html-view-standard.md` § Errata.
- The `skill-html-views` direction and token file record the refinement — `docs/design/direction/skill-html-views.md`, `docs/design/tokens/skill-html-views.md`.
- The delivery brief records slices 11a, 11b, 12 and 13 — `docs/product/briefs/intent-navigation-delivery.md`.
- The view tests read the joined script instead of `view.js`, and the one browser check that pins the page background reads the new value — `packs/core/tests/skills/navigate-intents/test_export_html.py`, `view_browser_checks.py`.
- Core moves to its next patch version.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The style admits motion RFC-0108 rule 9 forbade | `docs/rfc/0108-skill-html-view-standard.md` § Errata | eugenelim as Approver | Dated, signed errata entry | Entry dated 2026-10-16 replaces rule 9's last sentence with: "Motion is limited to colour, border, shadow and opacity transitions and a fade of at most 4px, each at most 200ms, only under `prefers-reduced-motion: no-preference`, and never on scroll." |
| Design direction | Form, depth, containment, chroma and motion axes change | `docs/design/direction/skill-html-views.md`, `docs/design/tokens/skill-html-views.md` (whole files re-read for "square", "no shadow", "no motion" claims) | eugenelim | File diffs; AC-0009's token test | No sentence in either file contradicts the shipped stylesheet |
| Architecture | The script is built from parts | `packs/core/DESIGN.md` § Intent-edge derivation, the paragraph naming `view_assets/` | `core` maintainer | Section diff | Names `view_src/`, the part list's owner, and the one hashed script |
| Current product truth | Two shipped specs' criteria change | `Amended in part by:` header lines of `docs/specs/intent-navigation-export/spec.md` and `docs/specs/intent-view-session-start/spec.md` | This spec's implementer | Header lines present | Each line names this spec and the criteria this spec's `Amends:` line names |
| Delivery plan | New and split slices | `docs/product/briefs/intent-navigation-delivery.md` § Delivery slices and § Spec map | eugenelim | Brief diff with the 2026-10-16 owner amendment line | Slices 11a, 11b, 12 and 13 present; Spec map lists this spec |
| User procedure | The page looks different; behaviour is unchanged | `guides/core/how-to/navigate-intents.md` § Export an offline view (re-read whole) | `core` maintainer | Guide lints pass | No sentence describes the old look; the reduced-motion behaviour is named |
| Release history | A pack content change | A changelog fragment under `docs/product/changelog.d/` from `tools/changelog.py new` | Pack release workflow | Fragment validates | Fragment present at the bumped version |
| Verification record | Browser, width, motion and review evidence | `docs/specs/intent-view-source-and-style/notes/verification-ledger.md` and `notes/screens/` (repository-durable) | Implementer | Ledger entries naming the base commit, the final commit, part digests and test counts; the eight screenshots of the plan's T6 with SHA-256 | Ledger cited by the pull request |
| Coordination | A confirmed brief slice | `workspace.toml` `[backlog].open` Draft entry, moved when approved | Implementer | Entry present | Entry follows the spec's status |

## Agent Rules

### Always do

- Keep every list, count, sort, label, next-step sentence, focus move, route and announcement the shipped view produces; this spec changes how the page looks and how its script is stored, not what it does.
- Keep the shipped safety controls: record text only in the data block and only ever inserted as text, one hashed script, one hashed style, and the shipped content-security policy string.
- Put every colour, font, radius, elevation, state-mark and motion rule in `view-base.css`; `view.css` arranges only.
- Record every browser, width, theme, motion and review result in this spec's verification ledger with the commit it ran against.

### Ask first

- Any change to the payload, a `query` output, `intent_graph.py`, or any derivation.
- Any visible text change other than AC-0022's placeholder and AC-0023's separator, and any new control, keyboard shortcut, or destination.
- Any motion beyond what AC-0011 to AC-0014 admit.

### Never do

- Never add a JavaScript library, framework, bundler, transpiler, package manifest, `node_modules`, or any dependency outside the Python standard library; the join is plain concatenation.
- Never load a web font, image, or any external resource.
- Never add a single-character keyboard shortcut.
- Never add a top-level directory, a pack, a skill, or a directory under `scripts/` other than `view_src/`.
- Never use an API that AC-0005 or AC-0006 bans, and never add a `style` attribute.

## Testing Strategy

**Base commit** means the merge-base of the implementing branch with `main`, recorded once in the verification ledger before T1; every criterion and proof that names the base commit uses that recorded id.

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0019):** the join, its digest, its refusals, the part bound, the banned-API scans, the escape parity, the token values and the static motion rules are properties of files and of the builder's output, so collected pytest tests decide them on every CI run. The two that read the repository's token file (AC-0009, AC-0019) live in `tests/roster/test_skill_html_view_tokens.py`, because a pack test may not read above its pack.
- **Scripted browser check (AC-0015, AC-0016, AC-0017, AC-0018, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027):** `view_browser_checks.py` drives exported fixture files in headless Chromium at true viewport sizes and both `prefers-reduced-motion` values; computed style and geometry are the only oracle for rendered radius, elevation, motion, contrast and spill. It is not collected by CI, so its full pass at the final code commit, with the count run and none skipped, is recorded in the ledger.
- **Goal-based check (AC-0028):** the real-export comparison is a measurement recorded in the ledger.
- **Visual / manual QA (AC-0029, AC-0030):** an `experience-reviewer` pass over the rendered real export and the owner's recorded approval decide the design outcome no script can.

## Acceptance Criteria

Unless a criterion names another fixture, it is checked on a whole-corpus export of the `mixed` fixture corpus, opened from local disk. **Joined script** means the content of the page's one executable `<script>` element. **Width and theme matrix** means true viewport widths of 320, 1280, 1680 and 2560 CSS px, each in the light and the dark theme, over the `mixed` and `hostile` exports. **Its background** means the computed `background-color` of the nearest ancestor-or-self element whose computed `background-color` has a non-zero alpha. A **token** match is on identifier boundaries: the token is not preceded or followed by a letter, digit, `_` or `$`, except where the token itself begins or ends with punctuation.

### Source parts and the join

- [x] **AC-0001.** The joined script is exactly `'use strict';\n(function () {\n`, then the UTF-8 text of each file named in the builder's part list, in that order, with nothing between them, then `})();\n`.
- [x] **AC-0002.** The content-security policy's script digest is the base64 SHA-256 of the joined script's UTF-8 bytes.
- [x] **AC-0003.** Every `*.js` file under `view_src/` is named in the part list exactly once, every name in the part list is a regular file under `view_src/`, and every part file's text ends with a newline character.
- [x] **AC-0004.** Given a part list naming a missing file, or a part whose text contains `</script` (case-insensitively) or `<!--`, `export` exits 1 with `error.code` `resolver_unavailable` and writes no file.
- [x] **AC-0005.** No part file has more than 400 lines, counting newline characters.
- [x] **AC-0006.** The joined script, comments removed, contains none of the tokens the export spec's criterion 0032 lists, and none of `fetch(`, `XMLHttpRequest`, `WebSocket`, `sendBeacon`, `import(`, `require(`, `.style`, `cssText`, `.animate(`, `requestAnimationFrame`, `startViewTransition` or `scrollIntoView`, nor a `setAttribute` whose first argument is `'style'` or `"style"`.
- [x] **AC-0007.** Every character of the joined script is printable ASCII, a tab or a newline.
- [x] **AC-0008.** The export spec's criterion 0033 holds with the joined script, written to a file and loaded under `node` as a CommonJS module, as the view's escape function.

### Style values

- [x] **AC-0009.** `view-base.css` declares every role of the § Colour, § Radius and § Elevation tables in `docs/design/tokens/skill-html-views.md` with its light value on `:root` and, where the table gives one, its dark value inside `@media (prefers-color-scheme: dark)`.
- [x] **AC-0010.** `view.css` declares no colour literal (hex, `rgb(`, `hsl(`, any other CSS colour function, or a named colour), no `font-family`, `font-weight` or `font` shorthand, no `box-shadow`, no `border-radius` whose value is not a `var(--r-` reference, no `transition*` or `animation*` property, and no `--` custom property.

### Motion

- [x] **AC-0011.** Every `transition`, `transition-*`, `animation` and `animation-*` declaration and every `@keyframes` rule in either stylesheet sits inside an `@media (prefers-reduced-motion: no-preference)` block.
- [x] **AC-0012.** Every property a `transition` or `transition-property` declaration names, where a `transition` shorthand that names no property counts as naming `all`, is one of `background-color`, `color`, `border-color`, `box-shadow` or `opacity`.
- [x] **AC-0013.** Every `@keyframes` rule sets only `opacity` and `transform`, and every `transform` value it sets is `none` or a single `translateY(<n>px)` with `|n|` at most 4.
- [x] **AC-0014.** Every duration and delay a `transition*` or `animation*` declaration states, read from the shorthand where one is used, is at most 200ms, no `animation-iteration-count` is `infinite`, and neither stylesheet declares `scroll-behavior`, `animation-timeline`, `scroll-timeline` or `view-timeline`.
- [x] **AC-0015.** With the browser's `prefers-reduced-motion` set to `reduce`, every element of the rendered page computes every `transition-duration` and `animation-duration` as `0s` and `animation-name` as `none`.
- [x] **AC-0016.** With `prefers-reduced-motion` set to `no-preference`, a list row computes a `transition-duration` greater than `0s`.

### Rendered style

- [x] **AC-0017.** Across the width and theme matrix, the list zone and the detail zone each compute a non-zero `border-radius` and a `box-shadow` other than `none`.
- [x] **AC-0018.** Across the width and theme matrix, every list row computes `box-shadow` as `none` or as inset shadows only.
- [x] **AC-0019.** In `view-base.css`, each of the six `data-mark` values `active`, `approved`, `draft`, `done`, `broken` and `stale` has a rule declaring a `background`, and with every `var()` resolved through the token file's § Colour table, the six resolved colours are pairwise different in the light theme and pairwise different in the dark theme.
- [x] **AC-0020.** Across the width and theme matrix, the border colour of the search field, of every `select`, and of every `button` whose computed border width is non-zero has a contrast ratio of at least 3:1 against its background.
- [x] **AC-0021.** Every test in `view_browser_checks.py` at the base commit passes against this change, with only two edits: the lines in `test_vi_4002_hostile_values_stay_inert` that read `view_assets/view.js` read the joined script instead, and the page-background literal in `test_ac_0036_text_contrast` reads the light and dark values of `--c-canvas` from `view-base.css`.

### Detail card and layout

- [x] **AC-0022.** The search field shows the placeholder "Search names and ids", whose computed colour has a contrast ratio of at least 4.5:1 against the field's background in each theme, and its accessible name is still "Search names and ids".
- [x] **AC-0023.** The detail state line's text content after its state mark's glyph, with whitespace collapsed and trimmed, is the state word, one space, then the type word ("Intent", "Brief" or "Spec"), then the rest of the line, with no separator before the type word.
- [x] **AC-0024.** Given a picked record with at least one broken entry, each entry in "What is broken" computes a background colour different from the detail zone's.
- [x] **AC-0025.** Given a picked record with at least one broken entry, each entry in "What is broken" shows a left border at least 3px wide whose colour has a contrast ratio of at least 3:1 against the detail zone's background.
- [x] **AC-0026.** The current question's link shows an inset bar at least 3px wide whose colour has a contrast ratio of at least 3:1 against the link's own background, and no other question link shows one.
- [x] **AC-0027.** At true viewport widths of 320, 1280, 1440, 1500, 1680 and 2560 CSS px, in both themes, for each of the five destinations with its first row picked, no element inside the list zone or the detail zone has a `getBoundingClientRect()` extending more than 1 CSS px past the left or right edge of its zone's `getBoundingClientRect()`, and the document's `scrollWidth` does not exceed the viewport width.

### Measurement and review

- [x] **AC-0028.** An export over this repository at the final code commit, opened in headless Chromium, shows the same four question counts as an export at the base commit, and the ledger records both commands, file sizes and counts.
- [x] **AC-0029.** An `experience-reviewer` pass over the rendered real export against RFC-0108 D1 rules 1 to 10, as corrected, and the refined `skill-html-views` direction's ranked goals leaves no Major or Blocker finding after adjudication, recorded in the ledger.
- [x] **AC-0030.** The owner records in the ledger, with the date, that the rendered real export at the final code commit is approved as matching the prototype in `notes/prototype/approved-overlay.css`.

## Follow-ons

- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 13 — redesign "Browse all intents" as a navigable tree, with open and done filters and a by-capability grouping.
- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 11a — a copy block holding a fixed-template next-step prompt in the detail zone.
- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 11b — the readiness bridge.

## Assumptions

none
