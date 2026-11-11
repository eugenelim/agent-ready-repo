# Plan: Intent dependency graphs

- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Spec:** [`spec.md`](spec.md)
- **Constrained by:** RFC-0106 D3; RFC-0105; RFC-0103; RFC-0108 D1
- **Repository anchors:** `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py` (`_VALID_OPS`, `run_query`, `_check_limits`, `_check_text_byte_limit`, `_resolve_identity`, `build_view_payload`, `_scope_node_ids`); `intent_graph.py` (`_walk_artifact_dir`, `_read_artifact_bytes`, `_decode_utf8`, `_preamble_visible`, `_value_form_intent_parent`, `_resolve_intent_typed`, `_resolve_intent_path`, `_make_related_edges` as the closest analogue); `view_assets/view.js` (`renderDetail`, `recordDetails`, `brokenEntries`, `brokenOf`, `parseRoute`, `hashFor`, `GROUP_LABELS`, `STATE_HELP`, `MARKS`); `view_assets/view.css`. Tests: `packs/core/tests/skills/navigate-intents/test_query_contract.py`, `test_related_intents.py`, `test_export_payload.py`, `test_export_html.py`, `view_browser_checks.py`, `view_bench.py`, and `navigate_intents_fixture_builders.py`.
- **Retention:** repository-durable spec and plan, fingerprints recorded at approval. Implementers, reviewers, resuming agents, and CI need them. Source/tests, the navigator guide, pack design, and the release fragment own post-closeout truth.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, execution
> observations belong in `notes/verification-ledger.md`; a genuine artifact
> error follows the controlled-amendment path. `Touches`, `Tests` and
> `Done when` are pinned; `Design`, `Approach` and `Risks` are working material.

## Constraints

- One slice PR targets the default branch after slice 10; its tasks are ordered commits inside it in dependency order: T1, T2, T3, T4, T6, T5.
- Reuse the existing navigator and export. No new dependencies, cross-skill imports, shared renderer, index, or writer migration. Standard-library-only Python; `textContent`-only DOM; the shipped content-security policy string, data-block escape and forbidden-API list are unchanged.
- `intent_graph.py` and its byte-identical `close-work` copy are not touched.
- No `.apm/` source carries an internal citation (the `packs/AGENTS.local.md` grep).
- Run `make lint-ruff lint-mypy` and the combined touched suites before final review; dispatch the full gates once on the slice PR. No `make ci` push precheck.
- Expected review shape: DEEP, bounded to one navigator enhancement.

## Durable-output map

| Output | Tasks | Evidence owner |
| --- | --- | --- |
| Dependency reading, bounded query, text, and compatibility | T1 | Core navigator tests |
| View payload member | T2 | Export payload tests |
| Detail part, broken entries, record groups, Key and routing | T3 | Browser suite |
| Keyboard, width, theme and inert content | T4 | Browser suite and `test_export_html.py` |
| Scale, real export, screenshots and experience review | T5 | Ledger and `notes/screens/` |
| Guide, skill, pack design, versions, changelog fragment, activation, projections, coordination | T6 | Guide/evaluation/catalogue checks and ledger |

## Design (LLD)

### Where the dependency reading lives

Owned by: T1, T2

`intent_graph.derive` stays unchanged, so `close-work`'s copy and every existing operation keep their output (AC-0012). Its output drops each node's preamble fields and the tombstone index, so `navigate_intents.py` gains one function that re-reads the intent collection through `intent_graph`'s confined helpers (`_walk_artifact_dir`, `_read_artifact_bytes`, `_decode_utf8`, `_preamble_visible`) and builds the live-intent and tombstone indexes the dependency resolution needs. It copies three of `derive`'s rules: the file admission (direct children of `docs/product/intents/` matching the resolver's `_ARTIFACT_FILE_RE`), tombstone detection (a `Tombstone:` field, with `Slug:` and `Reissued as:`), and node identity (`_compute_node_id`). A test runs the re-read beside `derive` over every fixture corpus and asserts the same live-intent ids, so a drift in either copy turns red. At run time, if the live intent ids it reads differ from `derive`'s intent nodes, a file changed between the two reads, and the operation refuses with `unsafe_input` (AC-0004).

Each `Depends on:` value, after comments are hidden and empty or `none`-led values dropped, is split on commas, and empty items are dropped, as `_make_related_edges` does; the remaining items across all occurrences, in file order, are the item list `position` indexes. The value's form comes from the inherited `_value_form_intent_parent`, whose typed grammar already includes the slug check, so a typed value with a malformed slug is `unrecognized`. A `typed` value with an intent kind resolves through `_resolve_intent_typed` (`kind_mismatch`, `retired_target`, `dangling`); a `typed` value with `brief:` or `spec:` is `outside_scope`. A `path` value is first checked for an empty, `.` or `..` segment, which is `unparseable`, and then resolves through `_resolve_intent_path`, a pure lookup: its `out_of_type` result becomes `outside_scope`, and its `to`, `retired_target`, `dangling` and `unparseable` results are kept. Every other form is `unparseable`. Pointer diagnostics join on (source intent, value). Edges join on the waiting/prerequisite pair and carry every contributing value and form in their basis. Cycle groups, including a self-loop, are found over the whole corpus's resolved edges with an iterative strongly-connected-components pass, so a deep chain cannot exhaust the interpreter stack.

### Query and text

Owned by: T1

`dependencies` joins `_VALID_OPS`. `_add_query_args` gains `--direction`; the existing `--depth` argument is reused. Traversal is breadth-first over the resolved edges from the start in the chosen direction, recording each intent's step count; `both` runs both traversals and keeps each intent's smaller count. The result's cycle diagnostics are the corpus cycle groups with a returned member. `_count_result_elements` counts no dependency records, so the operation counts its returned intents and its edges plus diagnostics itself and applies the same thresholds (`_DEFAULT_MAX_INTENTS`, `_DEFAULT_MAX_EDGES`, `_DEFAULT_MAX_RESULT_BYTES`) and precedence; text uses `_check_text_byte_limit`; refusal names `depth`. Text lists returned intents in node-id order, then `waiting -> prerequisite` lines, then diagnostics, in record order, under a header stating direction, depth and header-only scope, every value through `_escape_display`.

### Payload

Owned by: T2

`build_view_payload` adds `dependencies` with the whole corpus's edge records and diagnostics, or, with `--from`, those of the linked set: one breadth-first pass each way from the in-scope intents. Every query from an in-scope intent stays inside that set, so the view can answer exactly what the query answers without carrying unrelated subtrees. No other member changes. `test_export_payload.py`'s exact-key assertion (`_KEYS`) gains `dependencies`, the amended export criterion 0001; its other assertions stay as they are.

### View

Owned by: T3, T4

`view.js` indexes `data.dependencies` once into prerequisite and dependent adjacency lists, pointer diagnostics by source, and cycle diagnostics by member. A small `namedIntent` helper renders AC-0018's link or outside-export plain text, so lines, diagnostics and the record groups share one rule. The "Dependencies" part runs the same breadth-first traversal in the browser and takes cycle diagnostics from the payload rather than detecting cycles itself; its result is compared with the query's in the browser suite (AC-0020), so the two implementations are held equal by a test rather than by sharing code. `parseRoute` reads `dir` and `steps` only from the offered choices and treats anything else as the default, so a crafted fragment cannot bound a loop or reach the page as text. The part is a `section` with an `h3`, a lead `p`, two native `select` controls with `label` elements, a sort-key line, a `ul` of edge lines and a `ul` of diagnostics. Links use `hashFor`; the route gains `dir` and `steps` keys, written only when non-default and changed with `replaceRoute` so no history entry is added. Broken-entry building (`brokenEntries`, `brokenOf`) gains the dependency diagnostics, held only by in-scope intents and independent of `outstanding`, so "What is broken?", the detail "What is broken" part and the state-line count stay one computation. `recordDetails` gains the two groups; `GROUP_LABELS`, `GROUP_HELP`, `STATE_HELP` gain their entries and a new `FORM_HELP` table gives the five value forms their meanings, so forms render through the existing `labelChip` seam; the ✕ mark's help, the `cycle` help and the "What is broken?" lead line are reworded to cover dependency loops; and the Key gains the "waits for" line. Every record value renders in a `code.value` element, as `edgeItem` already does. `view.css` gains layout rules only, so that an edge line wraps its two names at 320 CSS px; no colour, font or token rule is added there.

### User-documentation draft

Owned by: T6

The navigator guide gains a dependency task: "Ask which intents this intent depends on, or which depend on it. Run `query --operation dependencies --id <identity> --direction prerequisites --depth 2 --format text`, or open the offline view, pick an intent and use its Dependencies part. Each line reads 'A waits for B': A's `Depends on:` header names B. The view reads `Depends on:` headers, accepting typed references and legacy repository paths. It does not include workspace-only dependencies or decide whether work may start. Check the listed problems before relying on a dependency chain. An export made with `--from` also carries the dependency records of intents linked to that subtree, and names those outside it by id." The guide's existing `--from` lines are corrected to say so.

## Tasks

### T1: Dependency query and text fixtures pass

**Depends on:** none
**Verification mode:** TDD
**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`, `packs/core/tests/skills/navigate-intents/test_dependencies.py` (new), `packs/core/tests/skills/navigate-intents/fixtures/dependency/` (new), `packs/core/tests/skills/navigate-intents/navigate_intents_fixture_builders.py`, `docs/specs/intent-dependency-graphs/notes/verification-ledger.md`, `workspace.toml` (the entry moves from `queue` to `active` in T1's first commit)

**Tests:**
- **VI-1001.** In `test_dependencies.py`, drive `run_query` over the dependency fixture: all registered intent kinds, a typed/path alias pair, repeated and comma-separated fields, null and comment-only values, an empty comma item and a `none` field before a real value (with their `position` values), body and other-field decoys, typed `brief:` and `spec:` targets live and missing, an `adr:` value, a misspelled kind, a malformed slug, brief and spec paths, paths with backslash, absolute, empty, `.` and `..` segments, malformed, `kind_mismatch`, `dangling` and `retired_target` values with and without a reissue, a repeated faulty value, a chain, a diamond, a self-loop, a multi-intent cycle, a cycle group of two overlapping loops, one cycle member that writes two faulty values, and a parent hierarchy giving the AC-0020 `--from` scope. A generated chain and cycle group each of 2,001 intents, queried from the chain's first waiting intent and from one cycle member with `both` and all steps, give a result or `result_too_large`. A seam that adds, removes or tombstones an intent between the two reads gives `unsafe_input` from the query (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005).
- **VI-1002.** Assert independently written node/edge/diagnostic sets and step counts for each direction at depths 0, 1, 2 and all steps, including `both` across a cycle; invalid direction, depth and identities; exactly-at and over each result limit; and text goldens including an isolated start and escaped controls (AC-0006, AC-0007, AC-0008).
- **VI-1003.** Record in the ledger the real corpus's `Depends on:` headers with their forms and accept/reject counts before finalizing refusal fixtures. Add workspace-absent/present/unreadable and query repository-byte-snapshot checks, and compatibility fixtures proving existing operations' results are unchanged when dependency headers are added, changed or faulty. The re-read's live-intent ids equal `derive`'s over every fixture corpus. An unknown operation still returns `unknown_operation` (AC-0012, AC-0013).

**Approach:** red first on a `run_query(... operation="dependencies")` call returning `unknown_operation` today, then build the reading, traversal, limits and text as the LLD describes.

**Done when:** `test_dependencies.py` and the existing navigator suites pass, with counts and runtime in the ledger.

### T2: The view payload carries dependencies

**Depends on:** T1
**Verification mode:** TDD
**Touches:** `navigate_intents.py`, `packs/core/tests/skills/navigate-intents/test_export_payload.py` (including its `_KEYS` assertion), `packs/core/tests/skills/navigate-intents/test_export_publication.py`

**Tests:**
- **VI-2001.** The payload's keys are the ten the amended export criterion 0001 names. Over the dependency fixture, `dependencies` holds the whole corpus's records in record order, and with a `--from` scope whose linked set holds an intent outside `nodes` exactly the linked set's, leaving out at least one edge and one diagnostic of the whole corpus. Over `mixed` and over the dependency fixture, every other member equals a golden recorded from the navigator before this change (AC-0016).
- **VI-2002.** Export's halves: the between-reads seam makes export refuse with `unsafe_input`; the 2,001-intent chain and cycle group write a file or refuse with `export_too_large`; export leaves repository bytes unchanged apart from its scratch output (AC-0004, AC-0005, AC-0013).

**Done when:** `test_export_payload.py` and `test_export_publication.py` pass.

### T3: The Dependencies part, broken entries, record groups and Key

**Depends on:** T2
**Verification mode:** scripted browser check
**Touches:** `view_assets/view.js`, `view_assets/view.css`, `packs/core/tests/skills/navigate-intents/view_browser_checks.py`, `packs/core/tests/skills/navigate-intents/fixtures/hostile/`

**Tests:**
- **VI-3001.** Part placement, lead line and controls, absent for briefs and specs (AC-0009, AC-0017).
- **VI-3002.** Edge lines, order including a `both` choice across a cycle, sort-key line, named intents inside and outside the export, the three empty lines and the no-line-but-diagnostics line (AC-0018); diagnostic order, fault sources and cycle members as named intents, `outside_scope` entries and values in their own `code` element (AC-0019).
- **VI-3003.** For every intent of the dependency fixture, every "Show" choice and every "Steps" choice, the part equals `run_query` for the same selection, in a whole-corpus export and, for every in-scope intent, in one with the AC-0020 `--from` scope (AC-0020).
- **VI-3004.** Broken rows, the detail part's rendering of a fault and a cycle, and the state-line count over the dependency fixture, with `outstanding` available and unavailable, and with `--from` holding entries only on in-scope intents; the `mixed` fixture's question counts stay 3, 2, 6 and 0 (AC-0021). Record-detail groups, in `position` order with value forms and named targets (AC-0022); within one holder, dependency entries after inherited ones, and for a holder with two faults and a cycle membership, faults by `position` then the cycle (AC-0021). Key additions including the five value forms, reworded ✕ and lead-line text, and the closed label set over the hostile fixture with hostile `Depends on:` values (AC-0023). Fragment, reload and history behaviour, and fragments with negative, huge and non-numeric `steps` and an unknown `dir` (AC-0024).

**Done when:** `view_browser_checks.py` passes with none skipped.

### T4: Keyboard, width, theme and inert content

**Depends on:** T3
**Verification mode:** scripted browser check
**Touches:** `view_assets/view.css`, `view_browser_checks.py`, `packs/core/tests/skills/navigate-intents/test_export_html.py`, `packs/core/tests/skills/navigate-intents/fixtures/hostile/`

**Tests:**
- **VI-4001.** Keyboard-only path and focus moves; accessible names; across the width and theme matrix with a cycle shown: no horizontal scroll at 320, focus not hidden, 24 by 24 targets, 4.5:1 text and 3:1 focus contrast (AC-0010).
- **VI-4002.** Hostile `Depends on:` values, including copies of a state-mark glyph, a state label and "waits for": no escaped code point in rendered text, each value only inside its `code` element, no record-derived markup or attribute, only fragment or source-link hrefs, no network request, unchanged policy string; unsafe reads refuse (AC-0011).

**Done when:** `view_browser_checks.py` and `test_export_html.py` pass with none skipped.

### T5: Scale, real export, screenshots and review

**Depends on:** T4, T6
**Verification mode:** goal-based check and visual / manual QA
**Touches:** `packs/core/tests/skills/navigate-intents/view_bench.py`, `docs/specs/intent-dependency-graphs/notes/verification-ledger.md`, `docs/specs/intent-dependency-graphs/notes/screens/`

**Tests:**
- **VI-5001.** `view_bench.py` meets its thresholds at 1, 10, 25 and 50 times this repository's corpus (AC-0025).
- **VI-5002.** A throwaway script exports this repository, opens it in headless Chromium, compares each `Depends on:`-writing intent's part with `both` and "All" against the query, and captures 8 screenshots at true viewports (AC-0026).
- **VI-5003.** The `experience-reviewer` agent reviews the screenshots and rendered facts; its findings are adjudicated (AC-0027).
- **VI-5004.** After the last code-bearing commit, `view_browser_checks.py` and `test_export_html.py` run once more; the ledger records the commit id, the SHA-256 of `view.js`, `view.css` and `view-base.css`, and the count of tests run with none skipped (the Testing Strategy record for the browser criteria).

**Done when:** the ledger records the bench, the real-export comparison, the 8 digests, the adjudicated review and the final-commit browser-suite record.

### T6: Docs, skill, evals, release and coordination

**Depends on:** T4
**Verification mode:** goal-based integration and activation
**Touches:** `packs/core/.apm/skills/navigate-intents/SKILL.md`, `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json`, `guides/core/how-to/navigate-intents.md`, `packs/core/DESIGN.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `workspace.toml`, `docs/specs/intent-dependency-graphs/notes/verification-ledger.md`, adapter projections via self-host

**Tests:**
- **VI-6001.** The activation evaluation gains dependency positives and enforcement/migration/mutation near-misses, run under the procedure the export ledger records for its activation criterion (AC-0014).
- **VI-6002.** The guide's dependency task and the design section; `tools/validate_guides.py`, `tools/lint-guide-titles.py` and `tools/lint-guides-no-repo-only-refs.py` pass (AC-0015).
- **VI-6003.** Core moves to the next unreleased patch version above the default branch's at build time, in both manifests (a new query operation is changed content, not a new primitive); a fragment from `tools/changelog.py new` with Highlights; `make build-self` twice with no second diff; `agentbundle catalogue verify --root .` passes; the installed navigator answers the dependency fixture's query and export; the citation grep finds nothing new (AC-0015).

**Done when:** every check above passes with ledger evidence.

## Rollout

One Core patch release merges to the default branch after slice 10. No flag, infrastructure, migration, or external service is added. Rollback reverts this slice's source, guides and release fragment; canonical dependency records are untouched.

## Risks

- The re-read of the intent collection doubles intent reads per query and export; T5's bench decides whether it stays within the thresholds.
- Legacy pointers can be read without repairing their authoring form. The guide distinguishes compatibility from the canonical typed form.
- A dependency view can be mistaken for dispatch authority. The part's lead line, the Key and the guide state it does not decide whether work can start.

## Changelog

- 2026-10-08: spec and plan approved together by the repository owner. Shaping round 1 is clean. Adversarial round 1 returned two findings; adjudication refuted both. Reports are under `.context/reviews/e40bed9c-cd45-4488-aef0-1d6c56224584/`. Approved revisions: spec SHA-256 `4c9c1b52f7571116e35a4b5da5739ea6547b5aaf377f4b10eb67b55de942c86e`; plan SHA-256 `691bbbf216858ab641c273ad5d8bfcdfeda09ab8e2887c7cf713268fe30c0405`.
- 2026-10-08: nonmaterial wording correction after approval to AC-0007.
- 2026-10-13: re-fitted to the session-start view before the build, as the delivery brief requires. The view criteria now follow that page's detail parts, marks, Key, routing and width zones; state labels reuse the navigator's existing set; the payload gains an additive `dependencies` member; the plan's tasks are rebuilt on the landed seams. Status returned to Draft/Drafting pending re-approval.
- 2026-10-14: owner decision: the shipped predecessor specs are historical records and are not edited. This spec's `Amends:` line and its amended-criteria table own the amendments; no pointer is added to the shipped specs. Round 1 review findings (shaping, adversarial, security) repaired.
- 2026-10-14: round 2 findings repaired: value forms and typed grammar reuse the navigator's classifier; record order, named-intent rendering and the scoped linked set are defined; each surface's own size refusal is named; export halves move to T2; the final-commit browser record moves to T5.
- 2026-10-14: round 3 findings repaired: values carry their written `position`; within-holder order, the deep-query selection and the scoped test's scope are named; T6 now precedes T5 so T5 records the final code commit.
- 2026-10-14: round 4 findings repaired: `position` indexes the kept non-empty items; empty comma items are dropped; T6 touches the ledger; VI-3004 checks the within-holder fault-then-cycle order.
- 2026-10-14: round 5 findings repaired: T1's fixture owns the scoped-export shape and the faults-plus-cycle holder; cycle diagnostics order by their first member by name; the Key explains the five value forms.
- 2026-10-14: spec approved by eugenelim
- 2026-10-14: plan approved by eugenelim
