# Plan: Intent view record owners

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `intent_graph.py` `derive` and `_preamble_visible`, where the shipped `heading` field is the analogue (slice 9, `docs/specs/intent-node-headings/`); `navigate_intents.py` `_build_intent_record`, `_op_search` and `_VALID_SELECTORS`, and `_build_outstanding_items`; `view_src/rows.js` `rowLink`, `browse.js` `treeRow` and its `ctx.match`, `roadmap.js` `capabilityRow`, `routing.js` `parseRoute`/`questionHash`, and `chrome.js` `buildNav`; the part list in `intent_view.py`; and the construction path `packs/core/tests/pack/test_intent_delivery_relations_copies.py`, `test_derivation_contract.py`, `test_query_contract.py`, `test_outstanding.py`, `test_export_html.py` and `view_browser_checks.py`. Named uncertainty: the readiness-bridge spec is Approved but not built, so its `readiness.js` rows are grounded only once it merges (T4).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan. After approval, grounding for
> a seam recorded as `no stub (implementation-discovered)` goes to the
> verification ledger; a settled design decision that execution falsified is a
> plan error that follows the controlled-amendment procedure. Treating them as
> contract is how a review spends a round on prose no gate consumes — the
> measured share is over half the plan's lines. `Grounding` stays *recorded*,
> because a per-task resolution that nobody wrote is not grounding; what it stops
> being is a claim a reviewer holds the plan to.

## Approach

Eight tasks in dependency order. The `owners` fixture comes first, because every criterion reads its hand-stated values. The README is the oracle that keeps both owner-key implementations, Python and JavaScript, honest. The derivation and query change is small and follows slice 9's `heading` path exactly. The view work then splits into three review units: the control and the row cell, the flat lists, and the two tree-shaped lists. The tree-shaped lists carry the only new structural logic, which is context rows in the roadmap. Safety and layout run once the visible surface is final. Documentation, the version bump and measurement close the work. This spec lands after the readiness-bridge spec's pull request, and T4 is the first task that needs it.

## Constraints

- RFC-0105: the view never re-derives the graph, and the owner comes only from the payload's `nodes`.
- RFC-0108 D1 rules 1 to 10 as corrected; the `skill-html-views` direction and token file.
- The source-and-style spec's criteria 0001 to 0010 keep holding: one hashed script from named parts, no part over 400 lines, banned APIs, colour only in `view-base.css`, and the layout sheet's limits.
- ADR-0007 and ADR-0074: standard library only; no cross-skill import.
- `packs/AGENTS.md`: bump `pack.toml` and `.claude-plugin/plugin.json` together, add a changelog fragment, update the eval harness, self-host after edits, and cite no internal governance in shipped pack text.
- `make build-self` refuses a dirty tree, so commit first and regenerate after. A roster test requires exactly the next core patch, so re-read main's core version before bumping and rebump if main moves.

## Construction tests

**Unit and contract tests:** `test_derivation_contract.py`, `test_query_contract.py` and `test_outstanding.py` run the derivation and `run_query` over the `owners` fixture and over a temporary copy of it with `Owner:` lines removed, and compare the results with the README's values. `test_intent_delivery_relations_copies.py` already decides byte identity.
**Integration tests:** `view_browser_checks.py` exports the `owners`, `mixed` and `hostile` fixtures through `nav.run_export`. It reads its expectations from a Python owner-key helper over the export's payload, and checks that helper against the README.
**Manual verification:** the real export, the screenshots and the `experience-reviewer` pass, recorded in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Amended-in-part headers | T7 | Eight header lines | Each names this spec and its amended items |
| Skill instructions and evals | T7 | `SKILL.md`; `eval_queries.json`; self-host no diff | AC-0007; owner field, selector and control described |
| User guide | T7 | Guide lints pass | Owner narrowing described |
| Changelog and version | T7 | Fragment; both version files | Fragment validates |
| Verification ledger and screens | T8 | Ledger; `notes/screens/` | Cited by the PR |
| Coordination | T7, T8 | `workspace.toml` entry; Spec-map row | Entry moved to `shipped` |

## Design (LLD)

### Data & schema

Traces to: AC-0001, AC-0004, AC-0005.

Owned by: T2

`derive` sets `"owner": owner_vals[0] if owner_vals else ""` on each of the three node dicts, reading `fields.get("Owner", [])`. The `fields` value comes from `_preamble_visible`, which the intent and spec loops already compute. The brief loop's existing `fields` local (`intent_graph.py:1171`) is read the same way, so there is no second preamble parse. The JSON stays raw, as `heading` does. `_build_intent_record`, the `search` entry builder and both item shapes in `_build_outstanding_items` copy `node.get("owner", "")`. The view payload's `nodes` and `records` therefore carry it with no export change, and the payload schema name stays `intent-navigation.view.v1`. The added bytes over this repository's 769 nodes total about 17 KB, measured as the JSON length of each node's `owner` member. That is far under the 100 MiB export budget.

### Interfaces & contracts

Traces to: AC-0005, AC-0016.

Owned by: T2, T5

`owner` joins `_VALID_SELECTORS`, and the existing string-type check covers it. The owner key exists twice, as `_owner_key` in `navigate_intents.py` and `ownerKey` in `owners.js`, because the view must not call Python. Both lower only A to Z, and collapse only spaces and tabs, so they agree on every input. Python's `str.lower` and JavaScript's `toLowerCase` differ on non-ASCII letters, which is why neither is used. The README lists one non-ASCII value as a case that proves this.

### Component / module decomposition

Traces to: AC-0008, AC-0010, AC-0011, AC-0012, AC-0018, AC-0023.

Owned by: T3, T4, T5

`view_src/owners.js` is a new part, placed after `rows.js` in the builder's part list. It holds the owner key, the option list, the owner label, the matching-record predicate, the owner cell and the control. It also holds the route encoding for the owner choice: `owner=k:<key>` for a key and `owner=none` for "No owner recorded". The prefix scheme keeps a real owner such as "none" from colliding with the sentinel. `rowLink` appends the owner cell, so every list, the tree and the readiness rows get it through one call. `capabilityRow` appends it separately. `parseRoute` keeps `owner` only when it names an option. `questionHash` leaves `owner` alone, as it leaves `show` and `group`. The "Clear filters" control's override sets `owner` to empty.

### State & control flow

Traces to: AC-0012, AC-0015, AC-0017, AC-0018, AC-0020, AC-0022.

Owned by: T4, T5

Each list body applies the matching-record predicate to its row ids after it computes them, and before it renders or counts. A row-held number is computed from the unfiltered data, so the counts in AC-0013 never see the owner. `browse.js` already separates "match" from "shown" in `ctx.match` and `ctx.shown`. The Browse match is `ctx.match` with the owner predicate added, and the Show branch's open-on-render and context-tag logic run whenever either Show or owner narrows. `roadmap.js` adopts the same visibility memo. A capability is shown when it matches, or when a nested capability is shown. A shown capability that does not match takes the tree's context tag and its visually hidden "shown for context" text. `buildNav` sets rail counts once today, because the data never changes. The owner choice changes them, so the count text is refreshed in `handleRoute` whenever `owner` differs from the previous route.

### Quality attributes (NFRs)

Traces to: AC-0024, AC-0025, AC-0026.

Owned by: T3, T6

The control is a native `select` with a visible `label`, so it needs no ARIA of its own. Focus is kept across the re-render by the existing `heldFilter` path in `chrome.js`, which is extended to the header control. The owner cell is the last grid item of `.row-link`. At widths where rows hold several columns, it spans the full row below the other cells, so no grid template gains a column. It uses `overflow-wrap: anywhere` so a 200-code-point token wraps. Its colour is the existing muted-text token, which already meets 4.5:1 in both themes.

## Tasks

### T1: The `owners` fixture states every owner case by hand

**Depends on:** none

**Touches:** `packs/core/tests/skills/navigate-intents/fixtures/owners/**`, `packs/core/tests/skills/navigate-intents/fixtures/README.md`

**Tests:**
- `no stub (implementation-discovered)`: the README's table layout is the seam, and it does not exist until this task writes it. Discovery predicate: the implementer finds the README's tables can be parsed by splitting Markdown table rows on `|`. Constraint: the parser lives in the test module and reads only the README. Required outcome: every record in the corpus has exactly one owner-table row. Verification mode: TDD, a collected pytest test. Proof obligation: the cross-check test below goes red when one record is added to the corpus without a README row, and the ledger records that red.
- A collected test in `test_derivation_contract.py` parses the README's owner table, option list, owner-selector table, non-owner selector table (one value each for `level`, `kind`, `exact_status`, `parentless` and `text`) and per-choice Browse expectations (under "Full hierarchy" with "All", "By capability" with "All", and "Full hierarchy" with "Open") and roadmap expectations. It asserts that every record path the README names exists in the fixture, and that every record in the fixture appears in the table. A table that drifts from the corpus therefore fails before any owner code exists.

**Approach:**
- The corpus holds a product strategy, two capabilities with one nested under the other, intents under each, a brief and specs with open and closed statuses, and every AC-0001 owner form. One owner appears in two letter-case and spacing variants. One value holds a non-ASCII capital letter. A capability's owner differs from the owners of the intents beneath it, so context rows occur under "Full hierarchy", "By capability" and the roadmap. That combination is what makes AC-0015 and AC-0018 fail on a wrong rule.

**Done when:** the README cross-check test passes and the fixture exports with `status: ok`.

### T2: The derivation and query carry `owner`

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/intent_graph.py`, `packs/core/.apm/skills/close-work/scripts/intent_graph.py`, `packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py`, `packs/core/tests/skills/navigate-intents/test_derivation_contract.py`, `packs/core/tests/skills/navigate-intents/test_query_contract.py`, `packs/core/tests/skills/navigate-intents/test_outstanding.py`

**Tests:**
- `test_derivation_contract.py` decides AC-0001 against the README's owner table. Its contract-surface stub, compiled and run red against the current derivation over the `mixed` fixture (it fails on the `owner` assertion), is:

  ```python
  def test_every_node_carries_owner_ac0001() -> None:  # stub: true
      nodes = ig.derive(_FIXTURE_MIXED)["nodes"]
      assert nodes
      assert all(isinstance(n.get("owner"), str) for n in nodes)
  ```
- `test_query_contract.py` decides AC-0002 and AC-0003 by copying the fixture to `tmp_path`, dropping every line matching `^- \*\*Owner:\*\*`, and running every operation in `_VALID_OPS` on both trees: `summary`; `record`, `ancestors`, `tree` and `dependencies` with `--id` set to each live intent the README names; `tree` without `--id`; `outstanding` with and without `--from`; and `search` with no selectors and with each entry of the README's non-owner selector table, which covers every member of `_VALID_SELECTORS` except `owner`. JSON results are compared with `owner` members and `generated_at` stripped. `tree`, `outstanding` and `dependencies` with `--format text` are compared byte for byte. It decides AC-0005 against the README's selector table, plus `{"owner": 1}` and `{"owner": null}` for `invalid_selector`.
- `test_outstanding.py` and `test_query_contract.py` decide AC-0004 for `record`, `search` and both `outstanding` lists.
- The existing byte-identity assertion in `test_intent_delivery_relations_copies.py` decides AC-0006.

**Done when:** those suites and `test_intent_delivery_relations_copies.py` pass, and `make lint-ruff lint-mypy` passes.

### T3: Every row shows its owner and the header offers the Owner control

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/view_src/owners.js`, `rows.js`, `roadmap.js`, `routing.js`, `labels.js`, `chrome.js`, `detail-render.js`, `packs/core/.apm/skills/navigate-intents/scripts/intent_view.py`, `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.css`, `packs/core/tests/skills/navigate-intents/view_browser_checks.py`, `packs/core/tests/skills/navigate-intents/test_export_html.py`

**Tests:**
- `no stub (mode)`: scripted browser check.
- Browser checks decide AC-0008's `owners` clause, AC-0010, AC-0011, AC-0023 and AC-0024 over the `owners` export.
- The shipped row-shape assertion `["c-name", "c-state", "c-context"]` in `view_browser_checks.py`, which checks session-start criterion 0009, moves to `["c-name", "c-state", "c-context", "c-owner"]`, as AC-0008 extends that criterion.
- `test_export_html.py`'s part-list and part-size tests keep the source-and-style spec's criteria 0001 to 0008 with `owners.js` added.

**Done when:** those browser checks pass, `test_export_html.py` passes, and a fresh `owners` export opens with no console error.

### T4: The flat lists, counts and empty states follow the owner choice

**Depends on:** T3, spec:intent-view-readiness-handover/T7 (its pull request merged into main, and this branch rebased onto it)

**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/view_src/list-bodies.js`, `lists.js`, `chrome.js`, `readiness.js`, `packs/core/tests/skills/navigate-intents/view_browser_checks.py`

**Tests:**
- `no stub (mode)`: scripted browser check.
- Browser checks decide AC-0012, AC-0013, AC-0017, AC-0020, AC-0021, AC-0022 and AC-0030 over the `owners` export, comparing each list under each README owner choice with the same list under "Any owner".
- Browser checks decide AC-0008's readiness clause, AC-0012's readiness clause and AC-0014 over the `mixed` export with a checked status input, built by the readiness-bridge spec's status-input helper.

**Done when:** those checks pass, and the readiness-bridge spec's own browser checks still pass unchanged.

### T5: Browse and the roadmap narrow with context rows

**Depends on:** T4

**Touches:** `packs/core/.apm/skills/navigate-intents/scripts/view_src/browse.js`, `roadmap.js`, `owners.js`, `packs/core/tests/skills/navigate-intents/view_browser_checks.py`

**Tests:**
- `no stub (mode)`: scripted browser check.
- Browser checks decide AC-0015, AC-0018 and AC-0019 against the README's per-choice expectations. Each also checks the general rule over every Group and Show choice, against the Python reading of the payload.
- A browser check over the roadmap decides the amended tree-and-roadmap 0007 rule under each README owner choice: each listed capability with no nearest capability ancestor is in exactly one section.
- Browser checks over an `owners` export scoped with `--from` to a capability the README names decide, under each README owner choice, the amended session-start 0025 and tree-and-roadmap 0041 and 0049 rows: the scoped intent is the only root, the scope banner and whole-corpus totals still show, Browse follows AC-0015 under both Group choices, and AC-0022 shows when nothing is shown. The same scoped export checks search against AC-0012 and AC-0030, and the flat filtered list against `run_query` `search` with `owner` set, limited to the in-scope intents.
- A browser check decides AC-0016 by comparing the flat filtered list with `run_query` `search` over the same fixture, using the filter selectors plus `owner`.
- The shipped tree-and-roadmap checks for its criteria 0030 to 0036 still pass under "Any owner".

**Done when:** those checks pass.

### T6: Hostile owner values stay inert and every layout holds

**Depends on:** T5

**Touches:** `packs/core/tests/skills/navigate-intents/fixtures/hostile/**`, `packs/core/tests/skills/navigate-intents/fixtures/owners/**`, `packs/core/tests/skills/navigate-intents/test_export_html.py`, `packs/core/tests/skills/navigate-intents/view_browser_checks.py`, `packs/core/.apm/skills/navigate-intents/scripts/view_assets/view.css`

**Tests:**
- `test_export_html.py` decides AC-0009 over the `hostile` export, with its owner values added to that fixture's records. Its stub pairs the exclusion with a positive assertion. It was compiled and run red against the current tree, where it fails on the positive assertion because no node carries an owner:

  ```python
  def test_hostile_owner_values_stay_inside_the_data_block_ac0009(hostile_html: str) -> None:  # stub: true
      block = _DATA_BLOCK.search(hostile_html)
      assert block is not None
      owners = [n.get("owner", "") for n in json.loads(block.group(1))["nodes"]]
      assert any("</script><script>" in o for o in owners)
      outside = hostile_html.replace(block.group(1), "")
      for needle in ("</script><script>", "<img src=x", '"><svg', "\u200b", "\u202e", "\u2066"):
          assert needle not in outside, needle
  ```
- A browser check decides AC-0031.
- `no stub (mode)` for AC-0025, AC-0026 and AC-0031: scripted browser check.
- Browser checks decide AC-0025 and AC-0026 across the width and theme matrix, over an `owners` export built in `tmp_path` with one record's owner replaced by a 200-code-point token.

**Done when:** those checks pass and the full `view_browser_checks.py` run reports no skip.

### T7: Instructions, guide, evaluations, amended headers and version are current

**Depends on:** T6

**Touches:** `packs/core/.apm/skills/navigate-intents/SKILL.md`, `packs/core/.apm/skills/navigate-intents/evals/eval_queries.json`, `guides/core/how-to/navigate-intents.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/*`, the eight amended specs' headers, `workspace.toml`, `docs/product/briefs/intent-navigation-delivery.md`

**Tests:**
- `no stub (mode)`: goal-based check.
- A one-line JSON check finds AC-0007's case in `eval_queries.json`.
- The guide lints named in the spec's Durable Outputs pass, and `agentbundle catalogue self-host --root . --write` shows no diff after commit.

**Done when:** `make lint-ruff lint-mypy`, the guide lints, the changelog fragment validation and the core roster version test pass, and `make build-check` passes once locally before the push.

### T8: Measurements and review are recorded

**Depends on:** T7

**Touches:** `docs/specs/intent-view-record-owners/notes/**`

**Tests:**
- `no stub (mode)`: goal-based check and visual / manual QA.
- The scale benchmark script that the export spec's criterion 0066 uses (`view_bench.py`) runs with owner lines in every synthetic record, for AC-0027.
- A ledger-recorded script reads the real export's payload, and a headless Chromium run reads the page, for AC-0028.
- 24 screenshots and an adjudicated `experience-reviewer` pass, for AC-0029.
- Dispatched `test-corpus.yml`, `test-roster.yml` and `pack-javascript.yml` runs at the final code commit are green.

**Done when:** the ledger records each result with its commit, and the pull request cites the ledger.

## Rollout

- **Delivery:** one pull request to main, after the readiness-bridge spec's pull request has merged. Reverting it is a plain revert, because the only stored change is fixture and documentation text.
- **Deployment sequencing:** rebase onto main after the readiness-bridge pull request merges. Re-read the core version on main, bump to its next patch, and re-run `make build-self` after the rebase.

## Risks

- The readiness-bridge build may reshape `rowLink` or the list bodies that T4 edits. T3 keeps its changes inside `owners.js` and one call in `rowLink`, so the rebase conflict stays small.
- A sibling pull request may take core's next patch first. The roster test catches that, and T7 rebumps.

## Changelog
