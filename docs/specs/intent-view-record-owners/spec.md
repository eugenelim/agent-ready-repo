# Spec: Intent view record owners

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105, RFC-0108 (D1 rules 1 to 10 as corrected by its errata entries), ADR-0007, ADR-0074
- **Amends:** [intent-navigation](../intent-navigation/spec.md) — criteria 0015, 0072 and 0076 and its Ask-first "Changing the query schema…"; [intent-navigation-export](../intent-navigation-export/spec.md) — its Ask-first "Changing the query schema, the derivation, or any `query` operation's output"; [intent-view-session-start](../intent-view-session-start/spec.md) — criteria 0002, 0004, 0005, 0006, 0008, 0009, 0019, 0023, 0024, 0025, 0030, 0038, 0040 and 0042, its Always-do "Build every list, count and next step from the payload…", and its Ask-first rules "Any change to `close-work/scripts/intent_graph.py`, the payload schema, or any `query` output" and "Adding a sixth destination, a third filter to any question…"; [intent-view-source-and-style](../intent-view-source-and-style/spec.md) — its Ask-first rules "Any change to the payload, a `query` output, `intent_graph.py`, or any derivation" and "Any visible text change … and any new control…"; [intent-view-handover-prompt](../intent-view-handover-prompt/spec.md) — its Ask-first "Any change to the payload, a `query` output, or any derivation" and its Never-do "Never add … a script part beyond `handover.js`"; [intent-view-tree-and-roadmap](../intent-view-tree-and-roadmap/spec.md) — criteria 0004, 0005, 0007, 0012, 0019, 0025, 0030, 0031, 0032, 0033, 0034, 0035, 0036, 0038, 0041, 0049 and 0053, its Always-do "Build every list, count, band and grouping from the payload…", and its Ask-first rules "Any change to the payload, a `query` output, or any derivation" and "Any destination beyond the six questions, or any control beyond Show, Group, Expand all and Collapse all"; [intent-view-readiness-handover](../intent-view-readiness-handover/spec.md) — criteria 0022, 0025, 0028 and 0030, its Ask-first "Any change to a `query` output, the derivation, or a hand-over prompt", and its Never-do "Never … add a module or script part beyond `intent_readiness.py` and `readiness.js`"; [intent-dependency-graphs](../intent-dependency-graphs/spec.md) — its Ask-first "Any change to `close-work/scripts/intent_graph.py` or to `intent_graph.py`'s derivation output". The table "Amended criteria and rules" at the end of § Acceptance Criteria states each disposition. Every other criterion and rule of those eight specs carries over unchanged.
- **Brief:** brief:intent-navigation-delivery
- **Discovery:** none
- **Contract:** none — the query result and view payload fields are contracted here and in the specs this one amends.
- **Shape:** mixed

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

A maintainer opens the offline intent view, picks their own name in one "Owner" control, and every question narrows to the records whose `Owner:` header names them, while each row still shows its owner and every count inside a row still covers all the work beneath it. An agent gets the same fact from the bounded query: every intent, brief and spec node, `record`, `search` entry and `outstanding` item carries the raw `owner` value, and `search` takes an `owner` selector, matched without regard to letter case or spacing.

## What Changes

- The derivation sets `owner` on every node from the preamble it already reads, in both byte-identical copies of `intent_graph.py`.
- `navigate_intents.py` carries `owner` on `record`, `search` entries and `outstanding` items, and `search` accepts an `owner` selector. Plain-text output does not change.
- The view gains an "Owner" control in the header, an owner cell at the end of every row, an "Owner" line in "Record details", and owner narrowing in every list. A new script part, `view_src/owners.js`, holds the owner key, options and match. `rows.js`, `list-bodies.js`, `browse.js`, `roadmap.js`, `lists.js`, `labels.js`, `routing.js`, `chrome.js`, `detail-render.js` and, for the readiness rows, `readiness.js` call it. The builder's part list in `intent_view.py` names it. Cell and control layout go in `view.css`, and any colour goes in `view-base.css`.
- A fixture corpus `fixtures/owners/` holds every owner form, with a README that states each record's owner by hand. The `hostile` fixture gains hostile owner values.
- The skill instructions, user guide, evaluations and amended specs' headers describe the owner.
- Core moves to its next unused patch version.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Eight specs' criteria or rules change | An `Amended in part by:` header line in each spec this spec's `Amends:` line names | This spec's implementer | Header lines present | Each names this spec and what this spec's `Amends:` line names for it |
| Interface compatibility | Query results and the `search` selectors gain `owner` | `packs/core/.apm/skills/navigate-intents/SKILL.md` — the query result paragraphs, the `search` selector list and § Export an offline view | `core` maintainer | Self-host re-run shows no diff | Names the `owner` field, the selector's matching rule and the Owner control |
| User procedure | The page gains a control and a row cell | `guides/core/how-to/navigate-intents.md` § Export an offline view, re-read whole | `core` maintainer | `tools/lint-guide-titles.py`, `tools/validate_guides.py` and `tools/lint-guides-no-repo-only-refs.py` pass | Says how to narrow the page to one owner, what "No owner recorded" means, and that counts inside a row are not narrowed |
| Skill activation | A new question shape | `navigate-intents/evals/eval_queries.json` | `core` maintainer | The eval file holds the new case | AC-0007 holds |
| Release history | A pack content change | A changelog fragment under `docs/product/changelog.d/` from `tools/changelog.py new` | Pack release workflow (`packs/AGENTS.local.md`) | Fragment validates; Highlights decided | Fragment present at the bumped version |
| Verification record | Browser, width, scale, real-export and review evidence | `docs/specs/intent-view-record-owners/notes/verification-ledger.md` and `notes/screens/` (repository-durable) | Implementer | Ledger entries with commit, test counts and screenshot SHA-256 values | Ledger cited by the pull request |
| Coordination | A confirmed brief slice | `workspace.toml` `[backlog].open` while Draft, then `["ini-010".work].queue` once approved; the brief's Spec map | Implementer | Entry and Spec-map row present | Entry follows the spec's status |

## Agent Rules

### Always do

- Change both copies of `intent_graph.py` in one commit, and keep them byte-identical.
- Read the owner from the preamble bytes the derivation already reads, through the same preamble reader; add no file read and no new limit.
- Keep `owner` raw in the derivation and every query result; apply the owner key only to compare.
- Put every owner value into the page only as text, through the view's existing element and escape helpers.
- Record every browser, width, scale, real-export and review result in this spec's verification ledger with the commit it ran against.

### Ask first

- Any change to the owner key, such as merging `@name` with `name` or splitting a value at a comma.
- Adding `owner` to plain-text output, to `tree` or `ancestors` results, or a selector to `outstanding`.
- Letting the owner choice change any number AC-0013 names.

### Never do

- Never take an owner from anything but the record's own `Owner:` preamble header: no Git author, `CODEOWNERS`, `workspace.toml`, body prose or model judgement.
- Never let the owner produce an edge, a placement, a status or an ordering.
- Never change the shipped content-security policy string except its two digests.
- Never add a dependency outside the Python standard library, a JavaScript library, a module under `scripts/`, or a script part beyond `owners.js`.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0009):** the owner field, the selector, the unchanged text output, the inert HTML and the byte-identical copy are pure functions of fixture files, so collected pytest tests decide them. The `owners` fixture's README states each record's owner and each selector's result by hand, so a wrong reading rule shows up as a disagreement with the hand-stated values. They run in `make test`, which CI runs only through the dispatch-only `test-corpus.yml` workflow. The ledger records a passing dispatch at the final code commit.
- **Scripted browser check (AC-0008, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0030, AC-0031, AC-0032):** `view_browser_checks.py` drives exported fixture files in headless Chromium at true viewport sizes. A browser is the only oracle for rendered rows, controls, focus and layout. Expected rows and counts come from a Python reading of the same export's payload that applies this spec's terms, cross-checked against the `owners` README. The suite is not collected by CI, so its full pass at the final code commit, with the count run and none skipped, is recorded in the ledger.
- **Goal-based check (AC-0027, AC-0028):** the scale benchmark and the real export are measurements recorded in the ledger.
- **Visual / manual QA (AC-0029):** an adjudicated `experience-reviewer` pass over screenshots decides the design outcome no script can, and it is a completion gate.

## Acceptance Criteria

Unless a criterion names another fixture, it is checked on a whole-corpus export, or a query, of the `owners` fixture corpus, with the export opened from local disk. Terms used below:

- **Open item, display name, name order, status word, broken entry:** as the session-start spec defines them, with the broken-entry term extended by the readiness-bridge spec's criterion 0030.
- **Context row, tree root, nearest capability ancestor:** as the tree-and-roadmap spec defines them.
- **Preamble reader:** the derivation's reading of a file's header fields: every line above the first line that, with HTML comment regions hidden, starts with `## `, with comment regions hidden. Each `- **Name:** value` line yields its value with one trailing HTML comment and one pair of surrounding backticks removed and surrounding whitespace trimmed.
- **Owner key:** a node's `owner` with each run of spaces and tabs replaced by one space, leading and trailing spaces removed, and each letter A to Z replaced by its lower-case form. An empty owner key means no owner is recorded.
- **Owner label:** for an owner key, the `owner` of the node holding that key whose id is first in code-point order among the export's `nodes`.
- **Owner choice:** the selected option of the page's "Owner" control: "Any owner", one owner key, or "No owner recorded", which chooses the empty key.
- **Matching record:** under an owner choice other than "Any owner", a node whose owner key equals the chosen key.
- **Row link:** an `a.row-link` element in the list zone.
- **Readiness export:** an export of a copy of the `mixed` fixture whose records carry at least two owners, with a checked status input as the readiness-bridge spec states one. Under one option of its Owner control, the start record and at least one other row of "What can I work on next?" are not matching records, and at least one row is.
- **Width and theme matrix:** true viewport widths of 320, 1280, 1680 and 2560 CSS px, each in the light and the dark theme.

### The derivation and the query

- [ ] **AC-0001.** Every intent, brief and spec node carries `owner`, a string equal to the first `Owner:` value the preamble reader yields for its file, or the empty string when it yields none. Over the `owners` fixture every node's `owner` equals the value its README states. That includes a backticked value, a value followed by a comment, a value that is only a comment, an `Owner:` line inside a multi-line comment, a second `Owner:` line, an `Owner:` line below the first `## ` line, mixed letter case and repeated spaces, and an absent line.
- [ ] **AC-0002.** For every query operation in JSON, with any selectors other than `owner`, the result over the `owners` fixture equals the result over a copy with every `Owner:` line removed, once every `owner` member and `provenance.generated_at` are removed from both.
- [ ] **AC-0003.** For `tree --format text`, `outstanding --format text` and `dependencies --format text`, the output over the `owners` fixture is byte-identical to the output over a copy with every `Owner:` line removed.
- [ ] **AC-0004.** The `owner` of a `record` result, of each `search` entry, and of each item of `outstanding`'s `placed` and `no_parent` lists equals the `owner` of its node.
- [ ] **AC-0005.** `search` accepts the selector `owner`. A string value matches exactly the intents whose owner key equals the value's owner key, so a value of `""` or only spaces matches the intents with no owner recorded. A value of any other JSON type returns `invalid_selector`. Over the `owners` fixture, each selector value its README lists returns exactly the intents it states.
- [ ] **AC-0006.** `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py` and `packs/core/.apm/skills/close-work/scripts/intent_graph.py` are byte-identical.
- [ ] **AC-0007.** `navigate-intents`' `evals/eval_queries.json` holds a `should_trigger: true` case that asks for one owner's open work.

### Owner on rows and in the detail

- [ ] **AC-0008.** Every row link the page renders ends with an owner cell. The cell reads "Owner: " followed by the node's `owner` when its owner key is not empty, and "No owner recorded" when it is, and the link's accessible name contains that text. Over the `owners` fixture, this holds for every row of each of the six questions, of search results, of "Browse all intents" with every subtree open, and of "How far along is each capability?". Over the readiness export, it holds for every row of "What can I work on next?".
- [ ] **AC-0009.** Given the `hostile` fixture, whose owner values carry `</script><script>`, `<img src=x onerror=alert(1)>`, `"><svg onload=alert(1)>`, a U+200B zero-width space and the U+202E and U+2066 bidirectional controls, none of those strings appears in the HTML outside the data block.
- [ ] **AC-0031.** Over that `hostile` export, the page's rendered text nodes contain no code point the text output escapes, and each such code point in an owner value appears as its `[U+XXXX]` escape.
- [ ] **AC-0010.** Opening "Record details" for a picked node shows the label "Owner" with the node's `owner`, or "No owner recorded" when its owner key is empty.

### The Owner control

- [ ] **AC-0011.** The header holds a `select` element whose accessible name is "Owner" on every question and while a search is typed. Its options are, in order:
  1. "Any owner";
  2. one option for each non-empty owner key among the export's `nodes`, showing that key's owner label, in code-point order of the key;
  3. "No owner recorded", present only when some node's owner key is empty.

  Over the `owners` fixture the options equal the list its README states.
- [ ] **AC-0012.** Given an owner choice other than "Any owner", each of these lists exactly the row links it lists under "Any owner" whose node is a matching record, in the same order and under the same subheadings, with a subheading shown only when it holds a listed row link: "What can I work on next?", "What is broken?" (where an entry's node is the record that holds it), "What is still open under a capability?", "What has no parent?", and search results. Over the readiness export, "What can I work on next?" also meets this.
- [ ] **AC-0013.** Under every owner choice, each of these numbers equals the number shown under "Any owner", and this list is the complete set this criterion covers: the "<n> open" count, "<c>/<t> closed", "<n> open items", and a roadmap row's band counts, delivered share and bar cells. So do each strategy heading's progress and the detail state line's open-beneath and broken counts.
- [ ] **AC-0014.** Given the readiness export, whose `readiness.start.id` is a node id, under an owner choice for which that record is not a matching record, no row holds a start tag. Under an owner choice for which it is a matching record, that record's row holds the tag that the readiness-bridge spec's criterion 0025 states.

### Browse all intents

- [ ] **AC-0015.** In "Browse all intents", an intent is a **Browse match** when it matches the Show choice, as the tree-and-roadmap spec's criteria 0032 and 0033 state, and is a matching record or the owner choice is "Any owner". With no level, kind or status filter set, under either Group choice and every Show choice, the list shows a row exactly when its intent is a Browse match or a row beneath it is shown, and every shown row that is not a Browse match is a context row. Over the `owners` fixture, each owner choice its README lists shows exactly the rows and context rows it states under "Full hierarchy" with "All", "By capability" with "All", and "Full hierarchy" with "Open".
- [ ] **AC-0016.** With a level, kind or status filter set and an owner choice other than "Any owner", "Browse all intents" lists flat, in name order, the intents that match the filters, the Show choice and the owner choice. Under "All", those are the intents `query --operation search` returns for the same filter selectors with `owner` set to the chosen key.
- [ ] **AC-0017.** After each change of the owner choice, the polite live region announces the list title and the list header's count.

### How far along is each capability?

- [ ] **AC-0018.** Given an owner choice other than "Any owner", "How far along is each capability?" lists a capability exactly when it is a matching record or a capability nested beneath it is listed. It shows a strategy section only when the section holds a listed capability. Over the `owners` fixture, each owner choice its README lists shows exactly the capabilities it states.
- [ ] **AC-0019.** In that list, every listed capability that is not a matching record shows the visible text "context", and its row link's accessible name contains "shown for context". No matching record's row shows either.

### Counts, header and empty lists

- [ ] **AC-0020.** Under an owner choice other than "Any owner", each question link's count and each list header's count is the number of row links its list shows that are not context rows. That rule covers every question except "Browse all intents", which shows no rail count, and except a count that the specs this one amends show as "unknown", which stays "unknown".
- [ ] **AC-0021.** While the owner choice is not "Any owner", each list header shows, below its lead, the line "Only rows whose owner is <owner label>." or, for "No owner recorded", "Only rows with no owner recorded.". While it is "Any owner", no list header shows either line.
- [ ] **AC-0022.** Given a question's list that shows at least one row link under "Any owner" with the same filters and none under the current owner choice, the list area reads "Nothing matches " and then a description, followed by ".". The description lists each set filter as the session-start spec describes it, followed by `owner "<owner label>"` or `no owner recorded`, joined by ", ". The area offers one "Clear filters" control, which sets "Any owner" and clears every filter. A list that shows nothing under "Any owner" with the same filters shows the empty line or filtered-empty state the specs this one amends state.
- [ ] **AC-0030.** Given a search text that matches at least one node under "Any owner" and none under the current owner choice, the list area reads `Nothing matches the search "<text>" for owner "<owner label>".`, or `Nothing matches the search "<text>" with no owner recorded.`, and offers one "Clear owner" control, which sets "Any owner" and keeps the search text. A search with no match under "Any owner" shows the session-start spec's criterion 0023 line and its "Clear search" control.

### Owner narrowing is the only difference

- [ ] **AC-0032.** The check covers four exports, with every subtree and disclosure open:
  1. the whole-corpus `owners` export;
  2. an `owners` export scoped with `--from` to the capability its README names;
  3. an `owners` export whose `outstanding` is unavailable;
  4. the readiness export.

  It covers every question, every Show and Group choice, no search and the search text the README names, and each owner choice: the README's choices on the first three exports, and every option its Owner control offers on the readiness export. The page under that owner choice is compared with the page under "Any owner" with the same other choices, and it differs only in these ways:
  1. its row links that are not context rows are exactly the "Any owner" page's row links that are not context rows and whose node is a matching record, in the same relative order;
  2. its context rows are those AC-0015 and AC-0018 state;
  3. its counts are those AC-0020 states, and the live region announces what AC-0017 states;
  4. a subtree toggle's hidden text counts its row's shown child rows, the rows shown directly beneath it, and a row with no shown child row has no toggle;
  5. it shows AC-0021's line;
  6. a subheading that holds no row link is gone;
  7. where no row link is left, the list area shows the AC-0022 or AC-0030 state;
  8. a start tag is absent as AC-0014 states;
  9. the Owner control's selected option differs.

  Every other rendered text node is identical, including the scope banner, header totals, notices, "unknown" counts, lead lines, sort keys, row text, the Key and the detail pane.
- [ ] **AC-0023.** The URL fragment holds the owner choice as `owner`, and reloading restores it. Changing the owner choice adds no history entry. Choosing a question or picking a row keeps the owner choice. A fragment `owner` that names no option shows "Any owner" and lists as "Any owner" does.

### Access and layout

- [ ] **AC-0024.** Using the keyboard alone, a reader can reach the "Owner" control and change its choice. After the list re-renders, focus stays on the control.
- [ ] **AC-0025.** Across the width and theme matrix, over an `owners` export whose longest owner value is 200 code points with no space, and with that owner chosen, no two rows' boxes overlap. Every owner cell also lies within its row's box, and the document's `scrollWidth` does not exceed the viewport width.
- [ ] **AC-0026.** The session-start spec's criteria 0034, 0035, 0036, 0037 and 0041 hold across the width and theme matrix over the `owners` export, with an owner chosen and with the owner control included.

### Measurement and review

- [ ] **AC-0027.** The export spec's scale benchmark (its criterion 0066) is re-run on this view over corpora whose every record carries an `Owner:` line. It meets the export spec's thresholds at 1, 10, 25 and 50 times this repository's corpus, and the ledger records each result.
- [ ] **AC-0028.** An export of this repository at the final code commit is opened in headless Chromium. Its "Owner" control shows the options, and for each option "What can I work on next?" and "Browse all intents" show the row counts, that a ledger-recorded script computes from that export's payload by this spec's terms. The ledger records the option count and each option's two counts.
- [ ] **AC-0029.** An `experience-reviewer` pass leaves no Major or Blocker finding after adjudication. It covers screenshots of three states across the width and theme matrix, over the real export: "What can I work on next?" with an owner chosen, "Browse all intents" with an owner chosen and context rows open, and "How far along is each capability?" with an owner chosen. It reviews them against RFC-0108 D1 rules 1 to 10 as corrected and the `skill-html-views` direction's ranked goals. The ledger records the 24 screenshots' SHA-256 values and each finding's adjudicated disposition.

### Amended criteria and rules

**Owner reading**, as a disposition below: under "Any owner" the criterion holds as written. Under any other owner choice, its lists, counts and empty states are read through AC-0032, and every other clause holds as written.

| Amended spec: criterion or rule | Disposition |
| --- | --- |
| Navigator 0015, `search` selectors | Extended by AC-0005 with `owner` |
| Navigator 0072, `record` fields | Extended by AC-0004 with `owner` |
| Navigator 0076, `search` entry fields | Extended by AC-0004 with `owner`; `tree` and `ancestors` fields carried unchanged |
| Navigator Ask-first "Changing the query schema, the admitted edge fields…" | This spec is that ask for the `owner` field and selector, decided by the owner's approval; the schema name, edge fields and every other rule carried unchanged |
| Export Ask-first "Changing the query schema, the derivation, or any `query` operation's output" | This spec is that ask for `owner`, decided by the owner's approval; carried unchanged for every other change |
| Session-start 0002, 0004, 0005, 0006 and the readiness-bridge spec's 0022 and 0030, each "lists exactly…" | Owner reading; AC-0012 states the narrowed lists |
| Session-start 0008 and the readiness-bridge spec's 0028, empty lines | Owner reading; AC-0022 states the narrowed empty state |
| Session-start 0009, a row is a name, a state and a context cell | Extended by AC-0008 with a final owner cell |
| Session-start 0019, "Record details" fields | Extended by AC-0010 with "Owner" |
| Session-start 0023, search | Owner reading; AC-0030 states the narrowed no-match state |
| Session-start 0024, Browse lists every live intent once; filter parity; empty filter result | Owner reading; AC-0016 adds `owner` to its filter parity, and AC-0022 extends its empty filter result |
| Session-start 0025, scoped export | Owner reading |
| Session-start 0042, the page while `outstanding` is unavailable | Owner reading |
| Session-start 0030, fragment state | Extended by AC-0023 |
| Session-start 0038, keyboard | Extended by AC-0024 |
| Session-start 0040, live region | Extended by AC-0017 |
| Session-start Always-do "Build every list, count and next step from the payload…; change no derivation, query, or payload field" | Narrowed to admit the `owner` node field; every other field carried unchanged |
| Session-start Ask-first "Any change to `close-work/scripts/intent_graph.py`, the payload schema, or any `query` output" | This spec is that ask for `owner`, decided by the owner's approval |
| Session-start Ask-first "Adding a sixth destination, a third filter to any question, or any ordering not named in these criteria" | This spec is that ask for the page-wide owner choice; carried unchanged otherwise |
| Source-and-style Ask-first "Any change to the payload, a `query` output, `intent_graph.py`, or any derivation" | This spec is that ask for `owner`, decided by the owner's approval |
| Source-and-style Ask-first "Any visible text change … and any new control…" | This spec is that ask for the Owner control, the owner cell, the "Clear owner" control, the "Record details" Owner line (AC-0010), and AC-0019, AC-0021, AC-0022 and AC-0030's text |
| Hand-over prompt Ask-first "Any change to the payload, a `query` output, or any derivation" | This spec is that ask for `owner`; the prompts carried unchanged |
| Hand-over prompt Never-do "Never add … a script part beyond `handover.js`" and readiness-bridge Never-do "Never … add a module or script part beyond `intent_readiness.py` and `readiness.js`" | Narrowed to admit the script part `owners.js` |
| Readiness-bridge 0025, exactly one row holds a start tag | Owner reading; AC-0014 states the start tag |
| Readiness-bridge Ask-first "Any change to a `query` output, the derivation, or a hand-over prompt" | This spec is that ask for `owner`, decided by the owner's approval |
| Tree-and-roadmap 0004 and 0036, counts | Owner reading; 0036's count reads "Browse match" for "matching the Show choice" |
| Tree-and-roadmap 0005, every capability listed once | Owner reading; AC-0018 states the narrowed list |
| Tree-and-roadmap 0007, each top capability in exactly one section | Owner reading |
| Tree-and-roadmap 0019, every capability listed while `outstanding` is unavailable | Owner reading |
| Tree-and-roadmap 0041, the scoped intent is the only "Hierarchy roots" entry | Owner reading |
| Tree-and-roadmap 0049, scoped "By capability" lists every intent once | Owner reading |
| Tree-and-roadmap 0012 and 0025, row contents | Extended by AC-0008 with a final owner cell |
| Tree-and-roadmap 0030 and 0031, every intent appears exactly once | Owner reading |
| Tree-and-roadmap 0032, 0033, 0034 and 0035, Show matches, context rows and open subtrees | Read "Browse match" (AC-0015) for "matches the choice"; 0034 and 0035 apply under "All" too when the owner choice is not "Any owner" |
| Tree-and-roadmap 0038, the flat filtered list | Extended by AC-0016 with the owner choice |
| Tree-and-roadmap 0053, the Browse lead | Carried unchanged; AC-0021's line follows it |
| Tree-and-roadmap Always-do "Build every list, count, band and grouping from the payload the export already embeds…" | Carried unchanged; `owner` is in the payload |
| Tree-and-roadmap Ask-first "Any change to the payload, a `query` output, or any derivation" | This spec is that ask for `owner`, decided by the owner's approval |
| Dependency-graphs Ask-first "Any change to `close-work/scripts/intent_graph.py` or to `intent_graph.py`'s derivation output" | This spec is that ask for `owner`, decided by the owner's approval; carried unchanged otherwise |
| Tree-and-roadmap Ask-first "Any destination beyond the six questions, or any control beyond Show, Group, Expand all and Collapse all" | This spec is that ask for the Owner control; carried unchanged otherwise |

## Follow-ons

none

## Assumptions

none
