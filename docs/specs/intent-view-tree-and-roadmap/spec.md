# Spec: Intent view tree, roadmap and grouped rail

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-17 by eugenelim, spec and plan, after spec-mode shaping (clean, round 5) and adversarial (clean, round 3) reviews; the 2026-10-17 contract amendment was approved by eugenelim the same day after shaping (clean, round 4) and adversarial (clean, round 3) reviews of its delta.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105, RFC-0108 (as corrected by its 2026-10-16 and 2026-10-17 errata entries)
- **Amended in part by:** [intent-view-readiness-handover](../intent-view-readiness-handover/spec.md) — its criterion 0004 and its Ask-first "Any change to the payload, a `query` output, or any derivation", as that spec's `Amends:` line states.
- **Amends:** [intent-view-session-start](../intent-view-session-start/spec.md), by criterion:
  - 0001 (five destinations, their order, counts and list header) — replaced by AC-0001 to AC-0004 and AC-0050;
  - 0007 (sort keys) — extended by AC-0010 for the new question and by AC-0052 for Browse under each Group choice and under filters; 0008 (empty lines) — extended by AC-0011;
  - 0009 (a row is name, state and context cells) — narrowed: a roadmap row holds progress in place of a context cell (AC-0012);
  - 0024 (Browse all intents) — replaced by AC-0025 to AC-0039, which carry its query parity for filters and its "Clear filters" control;
  - 0025 (scoped export) — extended by AC-0040 and AC-0041 for the new question and Browse's sections;
  - 0030 (fragment state) — extended by AC-0039;
  - 0042 (outstanding unavailable) — its "first three questions show unknown" is restated by AC-0004 by question name, and extended by AC-0019 and AC-0037;
  - 0043 (empty corpus) — "each of the four questions shows 0" becomes each of the five counted questions (AC-0004).
  Every other criterion of that spec — including 0012's refused-parent context, which AC-0029 keeps on tree rows — and of [intent-view-source-and-style](../intent-view-source-and-style/spec.md) carries over unchanged.
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

A maintainer planning work, or reporting progress to leadership, opens the intent view and finds a rail grouped by job — Work, Progress, Tidy, Browse — whose new question "How far along is each capability?" shows every capability under its product strategy with how much of the work beneath it is delivered, in progress or not started, and never claims a health it cannot know. "Browse all intents" becomes a tree they can expand and collapse as a whole, narrow to open or done work while keeping each match's ancestors visible as labelled context, and regroup by capability.

## What Changes

- The rail gains labelled groups and a sixth question, in a new order — `view_src/labels.js`, `view_src/chrome.js`.
- The rail links show short labels; each list names its full question above its title, and each link carries its question as its accessible description — the view's reading of RFC-0108 rule 1 with short labels, recorded as the owner's Approver-signed RFC-0108 errata entry of 2026-10-17 — `view_src/labels.js`, `view_src/chrome.js`.
- A roadmap body lists capabilities under their product strategies with progress — a new part `view_src/roadmap.js`, added to the builder's part list in `intent_view.py`.
- "Browse all intents" gains Show, Group, Expand all and Collapse all controls, sections, context rows and a by-capability grouping — `view_src/list-bodies.js`, `view_src/rows.js`, `view_src/routing.js`.
- Progress bars, the tree toolbar, rail groups and context rows get their style — `view_assets/view-base.css`, `view_assets/view.css`.
- A fixture corpus with product strategies, nested capabilities and every delivery band — `packs/core/tests/skills/navigate-intents/fixtures/roadmap/`.
- Shipped browser checks that read question order or the tree's shape read them by question key and section — `view_browser_checks.py`.
- Core moves to its next patch version.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | A shipped spec's criteria change | `Amended in part by:` header line of `docs/specs/intent-view-session-start/spec.md` | This spec's implementer | Header line present | Names this spec and each criterion this spec's `Amends:` line names |
| Design evidence | The rail order and roadmap rest on a practitioner survey | `docs/design/evidence/tracker-navigation-survey.md` | eugenelim | File present | Its "What this means" section matches the shipped rail order |
| User procedure | The page gains a question and Browse controls | `guides/core/how-to/navigate-intents.md` § Export an offline view (re-read whole) | `core` maintainer | Guide lints pass | Names the grouped rail, the roadmap question and its bands, and Browse's controls |
| Skill instructions | The described page changes | `navigate-intents/SKILL.md` § Export an offline view | `core` maintainer | Self-host re-run shows no diff | Names the six questions and the Browse controls |
| Release history | A pack content change | A changelog fragment under `docs/product/changelog.d/` | Pack release workflow | Fragment validates | Fragment present at the bumped version |
| Verification record | Browser, width and review evidence | `docs/specs/intent-view-tree-and-roadmap/notes/verification-ledger.md` and `notes/screens/` | Implementer | Ledger entries with commits and counts | Ledger cited by the pull request |
| Coordination | A confirmed brief slice | `workspace.toml`, the brief's Spec map | Implementer | Entry and row present | Entry follows the spec's status |

## Agent Rules

### Always do

- Build every list, count, band and grouping from the payload the export already embeds; whether an item is open comes only from the payload's open items.
- Keep the source-and-style spec's safety and stylesheet rules (its criteria 0001 to 0010).
- Record every browser, width, theme and review result in this spec's verification ledger with the commit it ran against.

### Ask first

- Any change to the payload, a `query` output, or any derivation.
- Any health, status or priority judgement the records do not hold.
- Any destination beyond the six questions, or any control beyond Show, Group, Expand all and Collapse all.

### Never do

- Never generate the words "on track", "at risk", "off track", or any other health judgement in view text.
- Never add a JavaScript library, framework, bundler, or dependency outside the Python standard library.
- Never add a single-character keyboard shortcut.

## Testing Strategy

- **TDD (AC-0042, AC-0043, AC-0044):** the part list, the static stylesheet rules and the absence of health words from the view's source are properties of files, decided by collected pytest tests.
- **Scripted browser check (AC-0051, AC-0052, AC-0053, AC-0054, AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0032, AC-0033, AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0048, AC-0049, AC-0050):** `view_browser_checks.py` drives exported fixture files in headless Chromium. Expected sections, bands, counts and cells come from a Python reading of the same export's payload that applies this spec's definitions, and the `roadmap` fixture's README states each record's band by hand, so a wrong definition shows as a disagreement with the hand-stated bands. Its full pass at the final code commit is recorded in the ledger.
- **Goal-based check (AC-0045):** the real export over this repository is compared with the Python reading and recorded in the ledger.
- **Visual / manual QA (AC-0046, AC-0047):** an `experience-reviewer` pass is advisory evidence; the owner's recorded approval is the gate.

## Acceptance Criteria

Unless a criterion names another fixture, it is checked on a whole-corpus export of the `roadmap` fixture corpus, opened from local disk. Terms:

- **Open item, display name, name order, ancestor list, intent in the export:** as the session-start spec defines them; "intent in the export" is any intent record in the payload, whatever its status.
- **Status word:** the leading run of ASCII letters of a node's status, as the session-start spec defines it.
- **Level tag:** "Vision" for `product-vision`, "Strategy" for `product-strategy`, "Capability" for `capability`, "Feature" for `feature`, "Unrecorded" for an empty level, and the level value itself otherwise.
- **Delivery band** of an intent, brief or spec in the export, while `outstanding` is available: **in progress** when it is an open item whose status word is `Implementing` or `Executing`; **not started** when it is any other open item; **delivered** when it is not an open item and its status word is `Fulfilled` or `Shipped`; **stopped** when it is not an open item and its status word is anything else.
- **Work beneath** a node: every intent, brief and spec reachable from it by following, from each intent reached, its record's `children`, `briefs` and `specs`, and from each brief reached, every spec with a resolved `Brief:` edge to it; the node itself is excluded and each reached node counts once.
- **Current work:** the work beneath that is delivered, in progress or not started.
- **Delivered share:** the delivered count divided by the current-work count, as a whole percentage rounded half up; undefined when current work is empty.
- **Capability loop:** the capability members of a parent loop, as the Tree root term uses that phrase, whatever other intents the loop passes through; each such capability is treated as having no nearest capability ancestor, so every capability still appears exactly once. Every upward walk stops at a repeated node, as the session-start spec's ancestor list does. The derivation refuses one edge of each parent loop, marking it with the state `cycle` (`intent_graph.py`, `_find_refused_cycle_edges`), so this term guards an edited or hostile payload, and the cases that exercise it are payload edits.
- **Nearest strategy** of a capability: the first intent in the export of level `product-strategy` met walking its resolved parent edges upward; **nearest capability ancestor** likewise for level `capability`. A strategy sitting between two capabilities therefore heads no section: the lower capability nests under the upper one.
- **Tree root:** an intent in the export whose parent edge is absent, refused, or names an intent not in the export, plus, among intents not reachable from those by child edges, only members of a parent loop: each loop member in name order that no earlier root's subtree has reached. An unreachable intent that is not a loop member hangs beneath a loop and is placed in that loop's subtree. In a scoped export, the only tree root is the scoped intent.
- **Context row:** a tree row shown only because a row beneath it is shown.

### The rail

- [x] **AC-0050.** Every question's list sits below a header that shows the list's title, its count and its sort key.

- [x] **AC-0001.** With no URL fragment, the `nav` landmark holds exactly six question links whose visible labels are, in this order: "Next up" (the question "What can I work on next?"), "Broken" ("What is broken?"), "Capability progress" ("How far along is each capability?"), "Open by capability" ("What is still open under a capability?"), "No parent" ("What has no parent?") and "All intents" ("Browse all intents"); the first is marked `aria-current="page"`. Criteria below name each question by its full question.
- [x] **AC-0051.** Each question's list header shows the full question, as worded in AC-0001, in a line above the list title.
- [x] **AC-0054.** Each rail link's computed accessible description is its full question, as worded in AC-0001, through `aria-describedby`.
- [x] **AC-0002.** The six links sit in four lists whose computed accessible names are "Work" (the first two links), "Progress" (the next two), "Tidy" (the fifth) and "Browse" (the sixth), each name coming from a visible group label through `aria-labelledby`.
- [x] **AC-0003.** At a true viewport width below 1440 CSS px the four group labels are visually hidden and the lists keep their accessible names; at 1440 CSS px and wider the labels are visible.
- [x] **AC-0004.** Every question link except "Browse all intents" shows as visible text a count: for "How far along is each capability?" the number of capabilities in the export, and for each other question the number of rows its list shows, as the session-start spec counts them. While `outstanding` is unavailable, "What can I work on next?", "What is still open under a capability?" and "What has no parent?" show "unknown"; in an empty corpus all five show 0.

### The roadmap question

- [x] **AC-0005.** "How far along is each capability?" lists every capability in the export exactly once, whatever its status.
- [x] **AC-0006.** A capability with a nearest capability ancestor is listed in a nested list inside that ancestor's list item, after the ancestor's row link.
- [x] **AC-0007.** Every capability with no nearest capability ancestor is listed in exactly one section: the section of its nearest strategy, or, when it has none, the section "Not under a product strategy in this export".
- [x] **AC-0008.** Strategy sections are headed by the strategy's display name, ordered by name order, followed by the "Not under a product strategy in this export" section; a section is shown only when it holds a capability.
- [x] **AC-0009.** Within a section and within a nested list, capabilities are in name order.
- [x] **AC-0010.** The list header's sort key reads "By strategy, then name".
- [x] **AC-0011.** Given a corpus that holds intents but no capability, the list area reads "No capability is recorded."; given an empty corpus, it reads the session-start spec's empty-corpus line instead.
- [x] **AC-0012.** Each capability row is one link to that capability holding, in order, its display name, its state mark and its progress.
- [x] **AC-0013.** A row's progress shows "<n> delivered", then "<n> in progress" and "<n> not started" each only when non-zero, then "<n> stopped" only when non-zero, each n being that band's count over the capability's work beneath.
- [x] **AC-0014.** A row whose current work is non-empty shows its delivered share followed by "%".
- [x] **AC-0015.** A row whose current work is empty and whose work beneath holds stopped items shows "0 delivered" and "<n> stopped", no share, and a bar of 24 empty cells.
- [x] **AC-0016.** A row whose work beneath is empty shows "Nothing beneath yet" and no counts, share or bar.
- [x] **AC-0017.** A row's bar is hidden from assistive technology and holds exactly 24 cells.
- [x] **AC-0048.** A bar's delivered, in-progress and not-started cell counts are the largest-remainder apportionment of 24 over those three bands' counts — each band takes the integer part of `24 × count ÷ current`, and the cells still unassigned go one each to the bands with the largest `(24 × count) mod current`, ties going delivered, then in progress, then not started — so a non-zero band can take 0 cells.
- [x] **AC-0018.** Each strategy section's heading line shows that strategy's progress over its own work beneath, by AC-0013 to AC-0017 and AC-0048.
- [x] **AC-0019.** Given an export whose `outstanding` is unavailable, the roadmap question still lists every capability under its section, and each row and strategy heading shows "Progress unknown: delivery mapping incomplete." in place of counts, share and bar.
- [x] **AC-0020.** In each theme, the bar's delivered, in-progress, not-started and empty cells compute four pairwise-different background colours.

### Browse all intents: controls

- [x] **AC-0021.** "Browse all intents" shows, above its list, a group labelled "Show" holding three buttons "All", "Open" and "Done", a group labelled "Group" holding two buttons "Full hierarchy" and "By capability", and two buttons "Expand all" and "Collapse all".
- [x] **AC-0022.** Within the Show group and within the Group group exactly one button has `aria-pressed="true"`; with no fragment those are "All" and "Full hierarchy".
- [x] **AC-0023.** "Expand all" opens every subtree in the list's first section, and "Collapse all" closes every one; neither opens or closes a section disclosure.
- [x] **AC-0024.** After "Expand all" or "Collapse all", focus stays on the button pressed.

### Browse all intents: the tree

- [x] **AC-0025.** Each tree row's link holds the intent's display name followed by its level tag.
- [x] **AC-0026.** While `outstanding` is available, a tree row with intents beneath it in the current grouping shows "<c>/<t> closed", where t is the number of those intents and c the number of them that are not open items.
- [x] **AC-0027.** While `outstanding` is available, a tree row with at least one open item beneath it shows "<n> open items", n being the number of open items beneath it as the session-start spec counts them, the same in either grouping.
- [x] **AC-0028.** Every subtree toggle has `aria-expanded` matching its state and an accessible name containing the display name of the intent it toggles.
- [x] **AC-0029.** A tree row whose intent's parent edge carries a `state` shows "refused parent:" and that state label, as the session-start spec's criterion 0012 requires.
- [x] **AC-0030.** In a whole-corpus export with "Full hierarchy" and "All", the list holds a section "Hierarchy roots" listing, in name order, every tree root that has intents beneath it, then a closed disclosure "No parent and nothing beneath" listing every other tree root; with every subtree and the disclosure open, every intent in the export appears exactly once.
- [x] **AC-0031.** With "By capability" and "All", the list holds a section "Top-level capabilities" listing every capability with no nearest capability ancestor, each holding as children the intents whose nearest capability ancestor it is, then a closed disclosure "Not under a capability" listing every other intent that is neither a capability nor has a nearest capability ancestor; with everything open, every intent in the export appears exactly once.

### Browse all intents: Show

- [x] **AC-0032.** With "Open", a row is shown only when its intent is an open item or a row beneath it is shown.
- [x] **AC-0033.** With "Done", a row is shown only when its intent is not an open item or a row beneath it is shown.
- [x] **AC-0034.** Under "Open" or "Done", every context row shows the visible text "context" and its link's accessible name contains "shown for context", and no row whose intent matches the choice shows either.
- [x] **AC-0035.** Under "Open" or "Done", every subtree that holds a shown row is open on render.
- [x] **AC-0036.** The list header's count names the number of intents in the export matching the Show choice and every filter set, and the polite live region announces the list title and that count after each Show or Group change.
- [x] **AC-0037.** While `outstanding` is unavailable, the "Open" and "Done" buttons are disabled and a note reads "Open and done are unknown: delivery mapping incomplete.", and no row shows a "closed" or "open items" count.
- [x] **AC-0038.** While a level, kind or status filter is set, the list is flat, as the session-start spec's filtered list is: it lists, in name order, the intents matching both the filters and the Show choice, shows no context rows or sections, ignores the Group choice, and keeps the session-start spec's "Clear filters" control and its query parity for the filters alone.
- [x] **AC-0052.** With no filter set, "Browse all intents" shows the sort key "Under each parent, by name" with "Full hierarchy" and "Under each capability, by name" with "By capability"; with a filter set, it shows "By name".
- [x] **AC-0053.** "Browse all intents"'s lead reads "Every intent in the export, under its parent." with "Full hierarchy" and "Every intent in the export, under its nearest capability." with "By capability", prefixed by "Open work only. " when Show is "Open" and by "Done work only. " when Show is "Done"; while a filter is set, the lead reads "Intents matching the filters, by name.", with the same Show prefix.
- [x] **AC-0039.** The URL fragment holds the Show and Group choices as `show` and `group`; reloading restores them, and changing either adds no history entry.

### Scoped export

- [x] **AC-0040.** Given an export with `--from` naming a capability, the roadmap question lists only the capabilities in the export, with sections and nesting computed only from intents in the export.
- [x] **AC-0041.** Given an export with `--from`, "Browse all intents" with "Full hierarchy" lists the scoped intent as the only entry of "Hierarchy roots", whether or not it has intents beneath it, and shows no "No parent and nothing beneath" disclosure.
- [x] **AC-0049.** Given an export with `--from`, "Browse all intents" with "By capability" computes nearest capability ancestors only from intents in the export, and every intent in the export appears exactly once with everything open.

### Files and style

- [x] **AC-0042.** The builder's part list names `roadmap.js`, and every part still meets the source-and-style spec's criteria 0001 to 0008.
- [x] **AC-0043.** Every colour, radius, elevation and motion rule this spec adds sits in `view-base.css`, and `view.css` still meets the source-and-style spec's criterion 0010.
- [x] **AC-0044.** No file under `view_src/` contains "on track", "at risk" or "off track", compared case-insensitively, and the `roadmap` fixture's records contain none.

### Measurement and review

- [x] **AC-0045.** An export over this repository at the final code commit, opened in headless Chromium, shows under "How far along is each capability?" the same sections, capabilities and band counts as the Python reading of that export's payload, and the ledger records each section with its capabilities' delivered shares.
- [x] **AC-0046.** An `experience-reviewer` pass over screenshots of the real export's roadmap question and Browse tree, at 320, 1280, 1680 and 2560 CSS px in light and dark, is recorded in the ledger with every Major or Blocker finding's disposition.
- [x] **AC-0047.** The owner records in the ledger, with the date, that the rendered real export is approved for planning and leadership reporting.

## Follow-ons

- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 13 — record owners: each record's `Owner:` header in the derivation, shown on rows, with an owner filter; it changes the derivation and query contract and is its own spec.
- eugenelim: `docs/product/briefs/intent-navigation-delivery.md` slice 11a — the copyable next-step prompt.
- eugenelim: `docs/specs/intent-view-tree-and-roadmap/notes/verification-ledger.md` § Experience review — trim the repeated type, level and parent from tree rows' context text, which needs an amendment to the session-start spec's criterion 0011 (owner-accepted deferral, 2026-10-17).

## Assumptions

none
