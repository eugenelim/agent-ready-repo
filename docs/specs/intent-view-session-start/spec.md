# Spec: Intent view for session start

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-13 by eugenelim, spec and plan together, after spec-mode shaping (clean, round 3), adversarial (round 3 findings repaired) and security spec-stage (advisory findings repaired in the plan) reviews; reports under `.context/reviews/63e509d4-5537-4666-b9af-ae46a254bfa1/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105, RFC-0108, ADR-0007, ADR-0074
- **Amends:** [intent-navigation-export](../intent-navigation-export/spec.md) — its view criteria 0035, 0037 to 0044, 0046 to 0053, 0056 to 0064, 0068 and 0069 to 0071, which this spec's criteria replace as the table at the end of § Acceptance Criteria states. Its other criteria carry over unchanged.
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

A maintainer opens the exported intent view at the start of a session and answers four questions from its first screen, without search: what can I work on next, what is still open under a capability, what has no parent, and what is broken. Each item leads with its human name, shows its state as a word plus a shape, and names its next step in plain words (which skill, and why), on a page that fills every width from 320 to 2560 CSS px in light and dark and follows the selected "Scan, then act" direction.

## What Changes

- The view's script and layout stylesheet are rewritten around the four questions plus "Browse all intents" — `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.js` and `view.css`.
- A new shared stylesheet carries the colour, type, spacing, focus and state-mark rules every maintainer view shares — `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css`.
- The page shell and its style hashing join the shared stylesheet and the layout stylesheet into the one hashed style element — `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py`.
- A byte-parity checker for copies of the shared stylesheet, with its self-test, joins the build-check chain — `tools/check_view_base_parity.py`, `tools/test_check_view_base_parity.py`, `tools/repo/build_gate_chain.py`.
- The view tests follow the new page — `packs/core/tests/skills/navigate-intents/test_export_html.py`, `view_browser_checks.py`, `view_bench.py`.
- The skill instructions, user guide and evaluations describe the four questions — `navigate-intents/SKILL.md`, `guides/core/how-to/navigate-intents.md`, `navigate-intents/evals/eval_queries.json`.
- Core moves from 3.1.1 to 3.1.2.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User procedure | The page a user opens changes shape | `guides/core/how-to/navigate-intents.md` § Export an offline view (whole section re-read for stale "summary strip" and "four views" claims) | `core` maintainer | `tools/lint-guide-titles.py`, `tools/validate_guides.py`, `tools/lint-guides-no-repo-only-refs.py` pass | The section names the four questions, "Browse all intents", the Key, and that readiness is not checked |
| Skill instructions and activation | The export's described output changes | `navigate-intents/SKILL.md` § Export an offline view; `navigate-intents/evals/eval_queries.json` | `core` maintainer | Self-host re-run shows no diff; the eval file holds the new case | SKILL.md describes the four questions; the eval case is present |
| Architecture | A new shared asset and a join rule inside the skill | `packs/core/DESIGN.md` § Intent-edge derivation | `core` maintainer | Section diff | Names `view-base.css`, the join into one hashed style, and the parity gate |
| Current product truth | The shipped export contract's view criteria change | `docs/specs/intent-navigation-export/spec.md` header `Amended in part by:` line | This spec's implementer | Header line present | Line names this spec and the replaced criteria |
| Release history | A pack content change | A changelog fragment under `docs/product/changelog.d/` for `core` 3.1.2, from `tools/changelog.py new` | Pack release workflow (`packs/AGENTS.local.md`) | Fragment validates; Highlights decided | Fragment present at the bumped version |
| Verification record | Browser, width, scale and review evidence | `docs/specs/intent-view-session-start/notes/verification-ledger.md` and `notes/screens/` (repository-durable) | Implementer | Ledger entries with commit, asset digests, test counts; 8 screenshots with SHA-256 | Ledger cited by the pull request |
| Coordination | A confirmed brief slice | `workspace.toml` `["ini-010".work]`; the brief's Spec map | Implementer | Entry and Spec-map row present | Entry moved to `shipped` when this spec ships |

## Agent Rules

### Always do

- Build every list, count and next step from the payload the export already embeds; change no derivation, query, or payload field.
- Keep the shipped safety controls: record text only in the data block and only ever inserted as text, one hashed script, one hashed style, and the shipped content-security policy string.
- Keep every glyph decorative and hidden from assistive technology, with the state word as the read text.
- Record every browser, width, scale and review result in this spec's verification ledger with the commit it ran against.

### Ask first

- Any change to `close-work/scripts/intent_graph.py`, the payload schema, or any `query` output.
- Adding a sixth destination, a third filter to any question, or any ordering not named in these criteria.
- Any JavaScript library, runtime dependency outside the Python standard library, build step, or new CI workflow.

### Never do

- Never show readiness: no ▶ mark, no "ready to start" wording, no `workspace-status` call or input, and no read of `workspace.toml`.
- Never show a copyable prompt, launch anything, reach the network, or write anywhere but the export destination.
- Never use `innerHTML`, `outerHTML`, `insertAdjacentHTML`, `document.write`, `eval`, `Function`, or a string-argument timer, and never add a `style` attribute.
- Never add a top-level directory, a pack, a skill, or a module under `scripts/` other than the one stylesheet named above.
- Never put a colour, font or state-mark rule in `view.css`; those live only in `view-base.css`.

## Testing Strategy

- **TDD (AC-0026, AC-0027, AC-0028, AC-0029):** the style join, the token values, the layout file's limits and the parity checker are properties of files and of a script's exit code, so collected pytest tests decide them on every CI run.
- **Scripted browser check (AC-0050, AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043):** the Playwright suite `view_browser_checks.py` drives exported fixture files in headless Chromium at true viewport sizes; a browser is the only oracle for rendered lists, focus and layout. It is not collected by CI, so its pass at the final code commit, with the commit id, the SHA-256 of the three view assets and the count of tests run with none skipped, is recorded in the ledger.
- **Goal-based check (AC-0044, AC-0045, AC-0046, AC-0047):** the scale benchmark, the real export, the activation run and the screenshots are measurements recorded in the ledger.
- **Visual / manual QA (AC-0048, AC-0049):** an `experience-reviewer` pass over the rendered real export, and the owner's first-screen check, decide the design-intent outcome no script can.

## Acceptance Criteria

Unless a criterion names another fixture, it is checked on a whole-corpus export of the `mixed` fixture corpus, opened from local disk. Terms used below:

- **Open item:** an item of the payload's `outstanding.placed` or `outstanding.no_parent`.
- **Status word:** the leading run of ASCII letters of a record's status.
- **Display name:** the node's heading with one leading `Spec: `, `Brief: `, `Intent: `, `Feature: `, `Capability: `, `Outcome: ` or `Opportunity: ` label removed; the node's slug when the heading is empty.
- **Name order:** ascending by display name compared case-insensitively, ties broken by node id.
- **Beneath:** an open item is beneath a node when that node's id is in the item's `ancestors`, or, for a spec, in any of its placements' `ancestors`.
- **Ancestor list:** for an open item, its `ancestors` or, for a spec, each placement's `ancestors`, nearest first. For any other node, the chain built by following resolved edges from it: an intent's resolved `Parent intent:` edge, a brief's resolved `Parent intent:` edge, and a spec's resolved `Brief:` or `Discovery:` edges, one list per starting edge in the order those edges appear in the payload's `edges`, each stopping at a repeated node.
- **Lists children:** an intent record lists children when any of its `children`, `briefs` or `specs` is non-empty.
- **Broken entry:** an edge in `edges` that carries a `state`, or one delivery diagnostic of one record.
- **Outside the export:** a node id that is not in the payload's `nodes`.
- **Width and theme matrix:** true viewport widths of 320, 1280, 1680 and 2560 CSS px, each in the light and the dark theme, over the `mixed` and `hostile` exports.

### The first screen

- [ ] **AC-0001.** With no URL fragment, the page's one `nav` landmark holds exactly five links in this order: "What can I work on next?", "What is still open under a capability?", "What has no parent?", "What is broken?" and "Browse all intents". Each of the first four shows as visible text the number of rows its list shows; over the `mixed` fixture those are 3, 2, 6 and 0. The first link is marked `aria-current="page"`, and its list is showing below a header that repeats the list's title, count and sort key.
- [ ] **AC-0002.** "What can I work on next?" lists exactly the open items in a startable stage, in this stage order and then by name order: specs with status word `Implementing`, specs with `Approved`, briefs with `Executing`, briefs with `Ready`, then intents with `Accepted` that list no children. Over the `mixed` fixture it lists `spec:bravo-spec`, `brief:bravo-delivery` and `intent:india-none`, in that order.
- [ ] **AC-0003.** The list in AC-0002 has the title "In a startable stage", its lead line reads "Readiness not checked in this snapshot.", and the page renders no ▶ glyph.
- [ ] **AC-0004.** "What is still open under a capability?" lists each live intent of level `capability` with at least one open item beneath it, each row showing that count as "<n> open", ordered by count descending and then by name order. Over the `mixed` fixture it lists `capability:alpha-cap` with 4 and `outcome:charlie-out` with 2.
- [ ] **AC-0005.** "What has no parent?" lists exactly `outstanding.no_parent`, under the subheadings "Intents", "Briefs" and "Specs" in that order, each holding its items in name order, with a subheading shown only when it holds an item. Its only filters are type and level, and each lists the same items as the unfiltered list restricted to that type or level.
- [ ] **AC-0006.** "What is broken?" lists one row per broken entry, in name order of the record that holds it. An edge row's context shows the field and its state label; a diagnostic row's context shows "Delivery diagnostic: <code>". Over the `hostile` export built with a resolver seam that adds one delivery diagnostic, the list holds every edge carrying a `state` and that diagnostic.
- [ ] **AC-0007.** Every list header names its sort key: "By stage, then name", "By open count, then name", "By type, then name", "By name", and, for "Browse all intents", "Under each parent, by name".
- [ ] **AC-0050.** The header's meta line shows the snapshot time and the intent, brief and spec totals, each equal to the matching `summary` value (intents as the sum of `intents_by_level`).
- [ ] **AC-0008.** Given a question with nothing to list, the list area shows its positive line instead of a list: "Nothing is in a startable stage.", "No capability has open work beneath it.", "Every open item has a parent." or "Nothing is broken.".

### Rows and marks

- [ ] **AC-0009.** Every worklist row is one link holding, in order, a name cell, a state cell and a context cell. Its accessible name starts with the item's display name and contains the state word, and its visible text contains its node id only when the display name is the slug.
- [ ] **AC-0010.** Every row, the detail state line and every trail entry inside the export carry one state mark: a glyph with `aria-hidden="true"` followed by a word. The first rule that matches sets it: ✕ and "Broken" on a row of "What is broken?"; ● for status word `Implementing` or `Executing`; ◆ for `Approved`, `Accepted` or `Ready`; ✓ for a node in the export that is not an open item while `outstanding` is available; ◇ otherwise. Outside the first rule, the word is the status word.
- [ ] **AC-0011.** Every row's context cell holds the type ("Spec", "Brief", or "Intent" with its level), followed, when the item has an ancestor list, by "under" and the display name of the nearest ancestor in its first list, or that ancestor's node id and "outside this export" when it is outside the export.
- [ ] **AC-0012.** In "Browse all intents", the row of an intent whose parent edge carries a `state` shows "refused parent:" and that state label in its context cell.

### Detail

- [ ] **AC-0013.** Picking a row shows the item in the detail zone under an `h2` of its display name, followed by these parts in this order: a state line, "Next step", "Open beneath", "What is broken", "Where it sits", "Open the file", and a "Record details" disclosure that is closed until opened.
- [ ] **AC-0014.** The state line holds the item's state mark, its type, "<n> open beneath" and "<m> broken", where m counts the broken entries the record holds. While `outstanding` is unavailable it reads "open work unknown" in place of the open count, and m counts only its edges carrying a `state`.
- [ ] **AC-0015.** "Next step" shows exactly one sentence, from the first rule that matches, and no prompt, `code` element or copy control:
  1. `outstanding` unavailable: "No next step shown: delivery mapping was incomplete, so this snapshot cannot tell what is open.";
  2. not an open item: "Nothing to do. It is <status word>.";
  3. spec `Implementing`: "Continue building it with the work-loop skill. It is already being built.";
  4. spec `Approved`: "Build it with the work-loop skill. It is approved, and work-loop checks readiness before it starts.";
  5. any other spec: "Finish the spec with the new-spec skill. It needs approval before it is built.";
  6. any brief: "Work on it with the author-delivery-brief skill in continue mode. Briefs are delivered through their slices.";
  7. an `Accepted` intent that lists no children: "Decompose it with the intent skill. It is accepted but has nothing beneath it yet.";
  8. an `Accepted` intent with an open item beneath it: "Pick an item from Open beneath. Its work is already decomposed.";
  9. any other `Accepted` intent: "Close it with the close-work skill if its outcome is met. Everything beneath it is finished.";
  10. any other intent: "Keep shaping it with the intent skill. It is not accepted yet.".

  Over a copy of the `mixed` fixture where the terminal `intent:juliet-done` names `intent:india-none` as its parent, `intent:india-none` shows sentence 9.
- [ ] **AC-0016.** "Open beneath" lists every open item beneath the picked node as a link with its state mark, under "Intents", "Briefs" and "Specs" subheadings in name order, or reads "Nothing open beneath." While `outstanding` is unavailable it reads "Open work unknown: delivery mapping incomplete."
- [ ] **AC-0017.** "What is broken" lists every broken entry the picked record holds, an edge with the plain-words meaning the Key gives its state and a diagnostic with its code, or reads "Nothing broken here." While `outstanding` is unavailable it lists the record's edges carrying a `state` and reads "Delivery diagnostics were unavailable."
- [ ] **AC-0018.** "Where it sits" shows each ancestor list of the item as a trail from the root to the nearest ancestor, or reads "No parent." only when the item has no ancestor list. Over the `mixed` fixture, `spec:golf-new`, which is not an open item, shows a trail ending at `intent:golf-new`. Each trail entry is a link to that node with its state mark, or, outside the export, its node id as plain text marked "outside this export".
- [ ] **AC-0019.** Opening "Record details" shows the item's node id, path, type, level, kind and status, and every edge group the export spec's intent and brief-or-spec detail criteria (0042 and 0043) require, with the labels its closed-label-set criterion (0035) lists. While `outstanding` is unavailable, it states that delivery mapping was unavailable in place of the delivery groups.
- [ ] **AC-0020.** Given a fragment naming a node id not in the payload, the detail zone reads "That item is not in this snapshot." and the question's list still shows.
- [ ] **AC-0021.** Focus after an action: choosing a question leaves focus on its link; picking a row at 40rem wide or more leaves focus on the row and the live region announces "Showing <display name>"; picking a row below 40rem, or following a link inside the detail zone, moves focus to the detail `h2`.

### Key, search and browse

- [ ] **AC-0022.** A "Key" disclosure sits in the worklist header, closed on load. Opened, it explains each state mark, each edge group, each state label and each trust-class label; nothing outside it carries a legend. Every group, state and trust-class label the page renders over the `hostile` fixture is in the closed set the export spec's criterion 0035 lists, and every state-mark glyph is one of ● ◆ ◇ ✕ △ ✓, where △ marks only a source link labelled "may be newer than this export".
- [ ] **AC-0023.** The header holds a search field on every destination. Typing lists every node whose slug or heading contains the text case-insensitively, in name order, and in a whole-corpus export its intents equal what `query --operation search` returns for the `text` selector. Escape empties the field and restores the question's list. Given no match, the list names the search text and offers one "Clear search" control.
- [ ] **AC-0024.** "Browse all intents" lists every live intent once under its resolved parent, roots and siblings in name order. Its level, kind and status filters, in a whole-corpus export, list the same intents as `query --operation search` with the same selectors. Given a filter result with nothing, the list names the filters that emptied it and offers one "Clear filters" control.
- [ ] **AC-0025.** Given an export with `--from`, a banner names the scoped intent, every question lists only in-scope items, "Browse all intents" has the scoped intent as its only root, search and each filter list the in-scope subset of what `query --operation search` returns for the same selectors, and the header's totals (AC-0050) say they cover the whole corpus.

### Shared style and parity

- [ ] **AC-0026.** The page's one `<style>` element's content is the UTF-8 text of `view-base.css`, one newline, then the text of `view.css`, and the content-security policy's style digest is the digest of that content.
- [ ] **AC-0027.** `view-base.css` declares each colour role of the § Colour table in `docs/design/tokens/skill-html-views.md`, from `--c-bg` to `--c-warn`, with its light value on `:root` and its dark value inside `@media (prefers-color-scheme: dark)`. Neither stylesheet declares `transition`, `animation`, `@keyframes`, `url(` or `@import`.
- [ ] **AC-0028.** `view.css` declares no colour literal (hex, `rgb(`, `hsl(` or a named colour), no `font-family`, and no `--c-` or `--t-` custom property.
- [ ] **AC-0029.** `tools/check_view_base_parity.py` exits 0 when every file named `view-base.css` under `packs/*/.apm/` is byte-identical to the canonical `navigate-intents` file, and exits 1 naming each file that differs. Its self-test proves both outcomes, and both run in the build-check chain.

### Behaviour, layout and access

- [ ] **AC-0030.** The URL fragment holds the question, search text, filters and picked node. Reloading restores them. Picking a question or a row adds a history entry and browser back returns to the previous question and selection; typing in search or changing a filter adds none.
- [ ] **AC-0031.** At a true 320 CSS px viewport the page needs no horizontal scrolling, the questions sit above the list in one column, and picking a row shows the detail in place of the list with a "Back to list" control that restores the list with focus on the picked row.
- [ ] **AC-0032.** At a true 1280 CSS px viewport the questions sit in one row above the list and the detail zone, which sit side by side.
- [ ] **AC-0033.** At true 1680 and 2560 CSS px viewports the questions, the list and the detail zone sit side by side, and the right edge of the detail zone lies within 48 CSS px of the viewport's right edge.
- [ ] **AC-0034.** Across the width and theme matrix, no focused element is entirely hidden by other page content.
- [ ] **AC-0035.** Across the width and theme matrix, every interactive target is at least 24 by 24 CSS px.
- [ ] **AC-0036.** Across the width and theme matrix, every rendered text node's computed colour has a contrast ratio of at least 4.5:1 against its computed background.
- [ ] **AC-0037.** Across the width and theme matrix, every focused element shows a focus indicator with a contrast ratio of at least 3:1 against the background it sits on.
- [ ] **AC-0038.** Using the keyboard alone, a reader can choose each question, search, filter, expand and collapse a "Browse all intents" subtree, pick a row, follow a detail link, open the Key and "Record details", and return with browser back.
- [ ] **AC-0039.** The page has exactly one `h1` and one each of the `header`, `nav` and `main` landmarks.
- [ ] **AC-0040.** A polite live region announces the list's title and count after each question switch, search and filter change.
- [ ] **AC-0041.** Every interactive control's accessible name contains its visible label text, and every subtree toggle's accessible name contains the display name of the intent it toggles.

### States

- [ ] **AC-0042.** Given an export whose `outstanding` is unavailable, the first three questions show "unknown" as their count and each list reads "Can't list open work: delivery mapping incomplete." with the reason; "What is broken?" lists the edges carrying a `state` and says delivery diagnostics were unavailable; and "Browse all intents" still lists every live intent.
- [ ] **AC-0043.** Given a corpus with no intent, brief or spec, the page reads "No intents, briefs or specs found under this root." and each of the four questions shows 0.

### Measurement and review

- [ ] **AC-0044.** The export spec's scale benchmark (its criterion 0066), re-run on this view with the default destination "What can I work on next?", meets its thresholds at 1, 10, 25 and 50 times this repository's corpus, and the ledger records each result with whether `outstanding` was available and how many rows the default list showed.
- [ ] **AC-0045.** An export over this repository at the final code commit, opened in headless Chromium, lists every live intent in "Browse all intents" once its subtrees are expanded, and the ledger records the command, the file size and the four question counts.
- [ ] **AC-0046.** `navigate-intents`' `evals/eval_queries.json` holds a `should_trigger: true` case asking for an offline view to pick what to work on this session, and an activation run of it, three runs under Claude Code, triggers `navigate-intents` in every run; the ledger records the run.
- [ ] **AC-0047.** Eight screenshots of the real export's first screen, at 320, 1280, 1680 and 2560 CSS px in light and dark, taken at true viewport sizes at the final code commit, are committed under `notes/screens/` and listed in the ledger with their SHA-256.
- [ ] **AC-0048.** An `experience-reviewer` pass over the rendered real export against RFC-0108 D1 rules 1 to 10 and the `skill-html-views` direction's ranked goals leaves no Major or Blocker finding after adjudication, recorded in the ledger.
- [ ] **AC-0049.** The owner answers the four questions from the real export's first screen without search, recorded in the ledger with the date.

### Export view criteria: carried or replaced

Every view criterion of the export spec, from 0028 to 0071, is either carried unchanged or replaced here.

| Export spec criterion | Disposition |
| --- | --- |
| 0028 source links, 0034 escapes, 0036 no network | Carried; their browser checks are kept |
| 0045 outside-export targets as plain text | Carried; AC-0011 and AC-0018 apply it to rows and trails |
| 0054 damaged data, 0055 no script, 0065 no motion | Carried; their checks are kept |
| 0066 scale, 0067 activation | Carried; AC-0044 and AC-0046 re-run them |
| 0035 closed label set | Replaced by AC-0022 |
| 0037 summary strip | Replaced by AC-0050 for the intent, brief and spec totals. The strip's outstanding, refused-edge and parentless-intent totals are dropped: the question counts of AC-0001 take their place and count different sets (startable open items, capabilities, open items with no parent, and broken entries including delivery diagnostics) |
| 0042, 0043 detail | Replaced by AC-0013 to AC-0019 |
| 0038 Tree view | Replaced by AC-0024, AC-0012 |
| 0039 Outstanding view | Replaced by AC-0002, AC-0005, AC-0016, AC-0018 |
| 0040 Refused edges view | Replaced by AC-0006 |
| 0041 Parentless view | Replaced by AC-0005; a terminal parentless intent stays in AC-0024 |
| 0044 legend | Replaced by AC-0022 |
| 0046, 0069, 0070, 0071 scoped export | Replaced by AC-0025, AC-0050 |
| 0047, 0050 outstanding unavailable | Replaced by AC-0014, AC-0015, AC-0017, AC-0019, AC-0042 |
| 0048 search and filters | Replaced by AC-0023, AC-0024 |
| 0049 empty filter | Replaced by AC-0023, AC-0024 |
| 0051, 0052, 0053 empty states | Replaced by AC-0008, AC-0043 |
| 0056 keyboard | Replaced by AC-0038 |
| 0057 focus | Replaced by AC-0021, AC-0031, AC-0037 |
| 0058 focus not hidden, 0059 targets, 0060 reflow | Replaced by AC-0034, AC-0035, AC-0031 |
| 0061 landmarks, 0062 announcements, 0063 names | Replaced by AC-0039, AC-0040, AC-0041 |
| 0064 contrast | Replaced by AC-0036, AC-0037 |
| 0068 real export | Replaced by AC-0045 |

## Follow-ons

- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 11 — readiness bridge and copyable hand-over prompt in this view.
- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 8 — re-fit intent dependency graphs to this layout.
- eugenelim: `docs/product/intents/FEAT-0002-intent-graph-navigation.md` § Validation hook — the 4-of-6-session comparison against repository search on the shipped build.

## Assumptions

none
