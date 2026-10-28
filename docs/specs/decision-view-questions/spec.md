# Spec: Decision view questions

- **Status:** Implementing
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0108 (D1 rules 1, 2, 6 and 7; D5 step 2; errata of 2026-10-17), RFC-0105 (D4 portable-view constraints)
- **Depends on:** spec:decision-view-style
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

A maintainer who opens the `navigate-decisions` HTML explorer sees, without searching, five named questions answered with counts — what was decided recently, what is still being decided, what was replaced, what each area holds and how decisions replaced each other — and reaches every record through Browse all. Each list says how it is sorted, and a picked record's detail opens with its state and what replaced it before its raw header fields, which sit collapsed at the end; this release is `navigate-decisions`' RFC-0108 D5 step 2 adoption.

## What Changes

- A question rail of six links, grouped by job, sits beside the zones from 90rem and as a tab row above them below 90rem — `explorer.py` `_build_html`, `explorer_assets/explorer.js`, `explorer_assets/explorer.css`.
- The rail replaces the List / Graph / Context switch. Browse all is the former List, Lineage is the former Graph, and the detail offers "Lineage" and "Guidance context" links for the picked record.
- Four new lists — Recently decided, Still being decided, Replaced and By area — are built in the browser from the data the export already carries, each with its full question, title, count and sort key in the list head.
- The page opens on Recently decided; `#list`, `#graph`, `#context` and `#detail/<id>` links keep working.
- The detail leads with the state line, supersession notices, what the record replaces, its dates and areas, and the two links; the header-field table moves into a collapsed "All header fields" section after the record body.
- With nothing picked, from 40rem the empty detail shows a one-line "In this list:" summary of the current list.
- `SKILL.md` § Export and repo-governance's version (2.4.0 → 2.5.0) describe the new view.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | The skill's export section names the List / Graph / Context switch, which goes | `packs/repo-governance/.apm/skills/navigate-decisions/SKILL.md` § Export, and its built projections | navigate-decisions owner | Text names the six rail questions and the detail's Lineage and Guidance context links; no List / Graph / Context sentence | `make build-self` leaves no diff |
| Current product truth | Not applicable: no page under `guides/` describes the explorer; `SKILL.md` is its only user-facing description | none | — | — | — |
| Release history | Visible change to a shipped skill, and the D5 step 2 adoption | `docs/product/changelog.d/<uuid>.md` for repo-governance 2.5.0; `pack.toml` and `plugin.json` version | navigate-decisions owner | Fragment names the rail and the adoption; both versions at 2.5.0 | `python3 tools/changelog.py validate` exits 0 |
| Decision rationale | RFC-0108 D1 and D5 already decide this; the owner's choice of questions (2026-10-27) is recorded in this spec | none — no new decision is taken | — | — | — |
| Design tokens | Not applicable: the rail uses the shared base's existing rail classes and the token file's existing § Layout tracks | none | — | — | — |
| Activation evals | Not applicable: the skill's description and triggers do not change | none | — | — | — |
| Verification record | Browser evidence, edited-test list and owner approval | `docs/specs/decision-view-questions/notes/verification-ledger.md` and `notes/screens/` | implementer | Rows for AC-0026 to AC-0029 | Every row filled |

## Agent Rules

### Always do

- Keep every shipped `decision-navigation` criterion and every `decision-view-style` criterion true; in particular decision-navigation criteria 0008, 0010, 0016, 0021, 0023, 0025, 0026 and 0027.
- Build the new lists in the browser from fields the export already embeds, and insert every record-derived string through `textContent` or `setAttribute`.
- Key every lookup this change adds that is built from record text (area names, ids, lifecycle words) by own keys only, so a value such as `constructor` or `__proto__` is ordinary data. The existing `statusMap` in `explorer.js` and `chainOf` in `lineage.js` are outside this change.
- Run `make build-self` after editing pack sources and commit the regenerated projections.

### Ask first

- Any change to the canonical `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css` or its copy, since it also changes the intents view and needs a core version bump.
- Any change to the export payload, the query envelope, or the data the JSON block carries.
- Adding a rail question beyond the six this spec names, or removing a visible control beyond the List / Graph / Context switch.

### Never do

- No new dependency, no new module boundary, no new script file, and no new top-level directory.
- No `'unsafe-inline'`, `'unsafe-eval'` or inline `style` attribute anywhere in the export, and no `'style'` or `"style"` string literal in the explorer's scripts.
- No change to record admission, lineage derivation, trust classes or source-link rules.
- No health-mode content (due, stale, superseded-but-cited, missing confirmation) in the page, and no ordering or grouping drawn from a field this spec does not name.

## Testing Strategy

- **Question membership, order, counts and empty states (AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0030):** scripted Chromium checks in `browser_checks.py` over the `mixed`, `lineage-chain` and new `questions` fixtures and small corpora generated inside a test. The lists are built by the page script, so only a rendered page shows them; each test derives the expected rows from the export's own data island in Python, so the oracle is independent of the script.
- **Rail, routing and detail structure (AC-0001, AC-0002, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021):** scripted Chromium checks, because focus, history entries, `aria-current` and the order of rendered detail parts exist only in a running page.
- **Rail layout across widths (AC-0022, AC-0023):** scripted Chromium checks of `getBoundingClientRect()` at true viewports, because the tracks are CSS media rules.
- **Hostile record text (AC-0024):** scripted Chromium checks over the `questions` fixture, which holds markup-shaped and inherited-property area names and lifecycle words.
- **Policy floor (AC-0025):** TDD in `test_html_publication.py`, since it is a string property of the emitted file and the assets.
- **Regression of shipped contracts (AC-0026, AC-0027):** goal-based. The existing suites run unchanged except tests the ledger lists, and real-export counts are compared before and after.
- **Whole-page judgement (AC-0028, AC-0029):** visual and manual QA on a real export of this repository, with screenshots, an `experience-reviewer` pass and the owner's approval recorded in the ledger.

## Acceptance Criteria

Unless a criterion names another fixture, it is checked on a full export of the `mixed` fixture corpus, opened from local disk. Terms used below:

- **A record's word** is the first run of letters in its lifecycle `raw_value`, lowercased; a record with no lifecycle value has none.
- **Decided** means the word is `accepted`, `superseded`, `deprecated`, `rejected` or `withdrawn`. **Being decided** means the word is `draft`, `proposed`, `open`, `final` or `experimental`. A record with any other word, or none, is neither.
- **A header date** is the first ten characters of the `raw_value` of the record's first header field with that label, the label compared case-insensitively, when they have the form `YYYY-MM-DD`; otherwise the record has no such date. **The decision date** reads `Date` for an ADR and `Date closed` for an RFC. **The opened date** reads `Date` for an ADR and `Date opened` for an RFC.
- **A record's areas** are the comma-separated parts of the `display_value` of its first header field labelled `Areas`, the label compared case-insensitively, each part trimmed, with empty parts dropped and exact repeats within the record dropped. Two areas are the same area only when their text is identical.
- **Export order** is the order of `records` in the data island. **A chain** is a connected group of two or more records joined by `checked` relationships.
- **Decision order** sorts records with a decision date first, newest date first, equal dates in reverse export order, then records with no decision date in export order.
- **The selected record** is the admitted record whose id the route carries, as `#<view>/<id>` or `#<view>/<id>/unpicked`. It is **picked** when the route carries no `/unpicked`; picked matters only below 40rem, where the detail replaces the list. **Nothing is selected** when the route carries no id.
- **The rail** is the `nav` element labelled "Questions". **A list's rows** are the `.row-link` buttons in the current view's region of the list zone, in DOM order, rows inside a closed section included; a hidden region's rows are never a list's rows. **A list's records** are the distinct records its rows show, each counted once.
- **Width and theme matrix** and **each view** keep their meanings from `docs/specs/decision-view-style/spec.md`, with **each view** extended to the Recently decided list and the By area list with every area section open; the By area list is checked on the `questions` export. Every clause about areas — in AC-0009, AC-0010's line, AC-0013, AC-0017, AC-0018 and AC-0021 — is checked on the `questions` fixture, which holds a record that a search removes from an area section.

### The rail

- [ ] **AC-0001.** The rail holds exactly six links, in this order and with these visible labels: "Recently decided", "Still being decided", "Replaced", "Lineage", "By area", "Browse all". They sit under three headings in order — "Decisions" (the first two), "Changes" (the next two), "Browse" (the last two). Each link's accessible description is its full question: "What was decided most recently?", "What is still being decided?", "Which decisions were replaced?", "How did decisions replace each other?", "What does each area hold?", "Browse every record".
- [ ] **AC-0002.** Each rail link except Browse all shows one count, and Browse all shows none. The counts are: decided records; being-decided records; records whose `superseded_by` is non-empty; chains; and distinct areas across all records. Each count is unchanged by search, the Kind filter and the Status filter. Checked on `mixed` and on the `questions` fixture against counts the test computes from the data island.

### The lists

- [ ] **AC-0003.** With no hash, the list zone shows the Recently decided list, and its rail link carries `aria-current="page"`.
- [ ] **AC-0004.** For each rail question, the list region shows, in DOM order, the full question, a level-2 heading with the text below, and a line naming the sort key with the text below:

  | Question | Heading | Sort line |
  | --- | --- | --- |
  | Recently decided | Decided records | Newest decision first (ADR Date, RFC Date closed) |
  | Still being decided | Records still open | Oldest first (ADR Date, RFC Date opened) |
  | Replaced | Replaced records | Replaced in full first, then in part; by id within each |
  | Lineage | Lifecycle graph | Largest chain first, then by lowest record number |
  | By area | Records by area | Areas A to Z; newest decision first within each |
  | Browse all | All records | By kind, then number |

- [ ] **AC-0005.** The Recently decided rows are the decided records in decision order, with a heading "No decision date" before the first record that has none. Checked on the `questions` fixture, which holds an equal-date pair and decided records with no decision date.
- [ ] **AC-0006.** The Still being decided rows are the being-decided records: those with an opened date first, oldest first, equal dates in export order; then, under a heading "No opened date", those without one in export order. Checked on the `questions` fixture, which holds one record for each of `Draft`, `Proposed`, `Open`, `Final Comment Period` and `Experimental`, an undated one, and records whose words are `constructor` and `tostring`; those two appear in no list but Browse all and By area, and count in no rail count but the area count.
- [ ] **AC-0007.** Given an export whose list holds no record before search and filters, the list has no rows and shows its empty text, never the "No records match" message: Recently decided "No record has a decided status: Accepted, Superseded, Deprecated, Rejected or Withdrawn."; Still being decided "Nothing is being decided: no record has a Draft, Proposed, Open, Final Comment Period or Experimental status."; Replaced "No record is replaced in full or in part."; By area "No record has an Areas field." Checked on `lineage-chain` for Still being decided and By area, and on a generated one-record corpus holding a `Proposed` ADR for the other two.
- [ ] **AC-0008.** The Replaced rows sit under two headings: "Replaced in full" holds each record with at least one `superseded_by` entry whose `partial` is false, and "Replaced in part" holds the rest of the records with a non-empty `superseded_by`; each heading's records are in export order, and a heading with no records is not shown. Each row keeps its supersession notice.
- [ ] **AC-0009.** The By area list holds one section per distinct area, each a `details` element closed when the list first shows, ordered by the area name compared case-insensitively, then by code point. Each section's summary shows the area name and the count of its records after search and filters, a section left with no record after narrowing is not shown, and its rows are the records with that area in decision order, with no heading inside the section. A record with several areas appears in each of their sections.
- [ ] **AC-0010.** When some but not all records have an area, the By area list's head states how many records have no area, in the form "<n> records have no area; Browse all lists them." (singular "record has" for one). The line is absent when every record has an area, checked on a generated two-record corpus where both have one.
- [ ] **AC-0011.** The Lineage link shows the lifecycle graph: with no record selected, every chain as a small diagram, as decision-navigation criterion 0026 defines it.
- [ ] **AC-0012.** The Browse all rows are every record in export order.
- [ ] **AC-0030.** In every list except Lineage, each `.row` of a record with a non-empty `superseded_by` carries the decision-navigation criterion 0025 marker, and each `.row` of a record with only unresolved supersession claims carries the unresolved-claim note, as Browse all's rows do.
- [ ] **AC-0013.** In every list except Lineage, search, the Kind filter and the Status filter narrow the rows to those whose record also matches them, and the list head's count reads "<shown> of <total> records shown", where shown is the list's records after narrowing and total its records before. With no matching row in a list that holds records, the list shows the "No records match …" message and the Reset filters button.

### Routing and keyboard

- [ ] **AC-0014.** A hash of `#recent`, `#deciding`, `#replaced`, `#graph`, `#areas` or `#list`, optionally followed by `/<id>` or `/<id>/unpicked`, opens the rail question whose link targets it (`#graph` is Lineage, `#list` is Browse all) with that selection. A hash whose first part is none of these, nor `context` or `detail`, opens Browse all with nothing selected. `#detail/<id>` on a cold load opens Browse all with the record picked.
- [ ] **AC-0015.** `#context/<id>` opens the guidance context for that record, and a bare `#context` shows "Pick a record, then choose Guidance context in its detail."; in both, no rail link carries `aria-current`.
- [ ] **AC-0016.** Activating a rail link by Enter or by click shows its list, moves focus to the list's level-2 heading, keeps the selected record selected (unpicked), and adds one history entry when the route changes and none when it does not; browser Back then restores the previous list and selection.
- [ ] **AC-0017.** In each list, every row of the selected record carries `aria-current="true"`. At 320 CSS px, after "Back to list" from a picked record, focus is on the first such row, and in By area the sections holding the record are open; when the current list has no row of the selected record, focus is on the list's level-2 heading.

### Detail

- [ ] **AC-0018.** With a record selected, the detail zone's parts appear in this DOM order, a part being absent when it has nothing to show: the heading; the state line; the supersession and unresolved-claim notices; a "Replaces" line naming, as links, each record the selected record supersedes through a `checked` relationship, with "in part" and the scope for a partial one; a facts line with the opened date for a being-decided record and the decision date for any other, then the record's areas; a links line holding a "Lineage" link, a "Guidance context" link and the record's source link, or its inert source path when no link is allowed; the record content; then the Relationships, Support references and "All header fields" sections. RFC-0108 rule 6's "next step" and "what is open beneath it" have no counterpart here: a decision record carries neither, so the lead is its state, what replaced it, what it replaces and its unresolved claims.
- [ ] **AC-0019.** The "All header fields" section is a `details` element, closed when a record is first shown, and holds the shipped header-field table with its rows unchanged: Kind, Status, Source, every header field as the decision-navigation § Corpus and query contract defines it, and Source link.
- [ ] **AC-0020.** Activating the detail's "Lineage" link shows the Graph view focused on the selected record, and its "Guidance context" link shows the guidance context for it; at 320 CSS px either one shows the list zone in place of the detail.
- [ ] **AC-0021.** From 40rem, with nothing selected, the detail zone shows "Pick a record to see its detail." and, when the current list holds at least one record after narrowing (or, for Lineage, at least one chain), a `.list-summary` line beginning "In this list:". For every list but Lineage it names, for each kind among the list's records after narrowing, their count followed by the kind's name (singular for one, plural otherwise); the Replaced line also names how many are replaced in full and how many in part, and the By area line the number of area sections shown after narrowing. The Lineage line names the number of chains and the number of records in them. In the guidance context with nothing selected, the detail shows the prompt and no `.list-summary` line.

### Layout

- [ ] **AC-0022.** At 1680 and 2560 CSS px the rail's right edge is at or left of the list zone's left edge, the rail is 16.5rem wide within 1 CSS px, and the two overlap vertically; at 1280 CSS px all six rail links share one top edge and the rail's bottom edge is at or above the zones' top edge; at 320 CSS px the rail's bottom edge is at or above the zones' top edge.
- [ ] **AC-0023.** Across the width and theme matrix, the rail meets decision-view-style criteria 0010 (no element past its container's edge, no page-wide horizontal scroll) and 0014 (text contrast at least 4.5:1), and every rail link is at least 24 by 24 CSS px.

### Safety and policy

- [ ] **AC-0024.** On the `questions` fixture, area names `<img src=x onerror=alert(1)>`, `constructor` and `__proto__` each form their own By area section, and, with the record holding them selected, appear in the detail's facts line; in both places they show as literal text and add no element other than the list and detail markup, and no page error is raised. At 320 CSS px, "Back to list" in By area with that record picked raises no page error and meets AC-0017 for it.
- [ ] **AC-0025.** The export still meets decision-view-style criteria 0001, 0002, 0004, 0005, 0006, 0020 and 0021.

### Regression and review

- [ ] **AC-0026.** Every test in `test_html_publication.py`, `test_query_contract.py` and `browser_checks.py` at the base commit passes against this change unedited, except tests the verification ledger lists one by one. Each listed test names the shipped criterion it verified and the replacing assertion that still verifies that criterion; a test may be removed without replacement only when what it checks is the List / Graph / Context switch, which this spec removes.
- [ ] **AC-0027.** An export over this repository at the final code commit shows the same record count, the same count per kind and per lifecycle value, and the same number of relationships as an export at the base commit, and the ledger records both commands, file sizes and counts.
- [ ] **AC-0028.** An `experience-reviewer` pass over screenshots of the real export across the width and theme matrix, against RFC-0108 D1 rules 1, 2, 6 and 7 and the `skill-html-views` direction's ranked goals, leaves no Major or Blocker finding after adjudication, recorded in the ledger.
- [ ] **AC-0029.** The owner records in the ledger, with the date, that the real export at the final code commit has the question rail they approved and matches the `navigate-intents` view's layout.

## Follow-ons

none

## Assumptions

- Technical: experience-design pack not installed — design intent for this surface is ungrounded
- Product: the design intent rests on the selected `skill-html-views` direction and the navigate-intents view — what it would change: the rail and detail criteria, if the experience review finds that direction does not fit this view (settled by: the AC-0028 review and the owner's AC-0029 approval).
