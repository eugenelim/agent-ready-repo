# Plan: Next-item suggestions removed

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/core/.apm/skills/workspace-status/SKILL.md` § Next-actions (the only home of `next_queue` and `next_shape`); `packs/core/tests/skills/workspace-status/test_priority_field_invariance.py` (a pack test over one skill's own files); `docs/specs/workspace-retirement/retirement-record.md` § Equivalence and `tests/roster/test_workspace_retirement_inventory.py` (the rules a new row must meet); `docs/specs/intent-view-session-start/spec.md` (the `Amended in part by:` header form).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md`. A genuine artifact error
> follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

The suggestions are skill prose, not code: `git grep` finds `next_queue` and `next_shape` in no engine, packaged copy, or MCP server, only in § Next-actions and in records. So the change is a prose edit with a pack test that pins it, then the retirement bookkeeping with its checks in the retirement roster suite. T1 edits the skill and its pins; T2 records the removal in the retirement record, the inventory, FEAT-0034, and the amended spec; T3 ships it.

## Constraints

- RFC-0106 D3: removing the suggestions is authorised; selecting among several ready specs always lists them and asks, and no rule may choose one automatically.
- FEAT-0034 C3 and the owner's decision of 2026-10-25: order is never a position in a shared list. Owner decisions of 2026-10-27: plain removal; the active-spec choice lists every active spec; no eval case.
- The `priority-header-field` spec's Never-do: nothing that orders work reads the `Priority:` field.
- `packs/AGENTS.md` § Version bump rule (patch), § Shipped pack content carries no internal-governance citations, § Self-hosting projection (`make build-self`, never edit projections).
- `tests/AGENTS.md` and `tools/lint-pack-test-boundary.py` (`pack-tests-stay-in-pack`): a pack test reads only its own pack, so every check over `docs/` lives in `tests/roster/`.
- `.workspace-prune-protected.toml`: every `docs/specs/<slug>` literal a roster test names is listed there.
- `tests/roster/test_workspace_retirement_inventory.py` runs on every PR: every changed file that names `workspace.toml`, `workspace-status`, or `workspace_status` needs a governing row.

## Construction tests

**Integration tests:** none; T2's roster checks run against this repository's real files.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth: § Next-actions | T1 | `test_next_actions_suggestions_removed.py` passes | AC-0001 to AC-0003 checked |
| Decision rationale: Equivalence row | T2 | `test_workspace_retirement_inventory.py` passes | AC-0004 checked |
| Current product truth: inventory | T2 | Same suite passes | AC-0005 to AC-0007 checked |
| Interface compatibility: amended spec header | T2 | Header line present | Line names this spec and what this spec's `Amends:` line names |
| Current product truth: FEAT-0034 list-order answer | T2 | T2 Done-when conditions hold | Count and readers match the `reads_order` rows |
| Release history | T3 | Changelog gate passes; `core` versions agree | Fragment present |
| Delivery membership | T3 | `lint-brief-coverage.py` lists the spec | Coverage lint passes |

## Design (LLD)

### Design decisions

- **Removal, not replacement.** The two choices go with no stand-in. Ready to start already lists every ready item with its command, so the reader loses no route. Traces to AC-0001.
- **One choice per active spec.** The active-spec line becomes "for each entry in `canonical.active`", rendered in the order the JSON gives with no claim that the order means anything. Traces to AC-0002.
- **The candidate paragraph goes.** The paragraph "If `canonical.blocked` or `canonical.findings` is non-empty for a candidate, surface the stable `code`, `path`, and `next_action`; do not select it as `next_queue` or `active_spec`" is deleted whole. Its candidate was an item considered for `next_queue` or `active_spec`, and it was dead or wrongly scoped. Read as the candidate's own findings, it never fired: the engine puts an entry in `canonical.ready` only when it is dispatchable, which needs no findings, and in `canonical.active` only when its own `findings` list is empty (`workspace_status.py`, the `canonical` block). Read by `path`, it matched a waiting item's `unsatisfied_dependency` finding, which names the spec it waits on, and so hid an active spec that others depend on. No reachable output is lost: step 5b still shows each blocked entry's first finding `code` and `next_action` when the graph renders, and § Blocked still shows what each item waits on. Traces to AC-0001, AC-0002.
- **No eval case.** The eval harness copies each fixture to the workspace root under its base name (`packages/agentbundle/agentbundle/commands/pack_evals.py`, `seed_workspace`), so no fixture can hold `docs/specs/<slug>/spec.md`, and no current `workspace-status` fixture reaches a ready or active spec. A case would pass without testing anything. The pack test is the proof, and the PR names `packs/AGENTS.md`'s eval-harness rule as not met, with this reason.
- **The Equivalence Case text matches D3 word for word.** With backticks removed, "the first-in-list next_queue and next_shape suggestions" appears in RFC-0106 D3's Order bullet, so the retirement check's rule that a removal's text appears under its linked heading accepts a link to `#d3--per-item-homes-for-what-headers-cannot-yet-supply`. The row's Evidence cell names `packs/core/tests/skills/workspace-status/test_next_actions_suggestions_removed.py`. The Equivalence opening sentence gains slice 6. Traces to AC-0004.
- **Inventory rows.** A new `docs/specs/next-item-suggestions-removal/*` contract row with owner 6. The `docs/specs/workspace-status-next-actions/*` row drops `reads_order` and moves to owner 9, because after the amendment it still states the "do not re-read `workspace.toml`" rule that slice 9 retires. Two rows' consumers name a suggestion today, and both are rewritten: the engine row (`packages/agentbundle/agentbundle/_data/workspace_status_engine.py`) drops "emits next_queue and next_shape", which it never did, and the next-actions row becomes "workspace-status next-actions procedure: active-spec, parallel-session and work-intake choices". The `workspace-status/*` row keeps `reads_order`: Ready to start and the readiness bridge still read `canonical.ready` in registry order until slices 8 and 9. Traces to AC-0005, AC-0006, AC-0007.
- **Records that name the readers.** The `entry position` Disposition row's Home cell drops `docs/specs/workspace-status-next-actions/*` from "read today by" and says the Next-actions list picks nothing by position; its Owner stays 8. FEAT-0034 § Unresolved questions, which counts and names the `reads_order` readers, is brought into line with the inventory's `reads_order = true` rows and drops the next-actions spec and the `next_queue`/`next_shape` parenthetical.

Owned by: T1, T2

## Tasks

### T1 — § Next-actions picks nothing by position, and its pins pass

**Depends on:** none
**Verification mode:** goal-based check
**Touches:** `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/tests/skills/workspace-status/test_next_actions_suggestions_removed.py`, `.claude/skills/workspace-status/SKILL.md`, `.agents/skills/workspace-status/SKILL.md`

**Tests:**
- `test_next_actions_suggestions_removed.py` reads the source `SKILL.md` through a path built from `Path(__file__).resolve().parents[3] / ".apm/skills/workspace-status/SKILL.md"` and slices the Next-actions section by the spec's term:
  - AC-0001, AC-0003: one test each, substring checks on the whole file and on the slice.
  - AC-0002: one line of the slice contains both `for each entry in` and `canonical.active`, and the slice has no `first entry in`.
- Before the `SKILL.md` edit, the AC-0001 and AC-0002 tests fail and the AC-0003 test passes.

**Done when:** the new suite passes, `make build-self` leaves the projections equal to the source, and `python3 tools/lint-pack-test-boundary.py` passes.

### T2 — The retirement record, inventory, FEAT-0034, and amended spec record the removal

**Depends on:** T1
**Verification mode:** goal-based check
**Touches:** `docs/specs/workspace-retirement/retirement-record.md`, `docs/specs/workspace-retirement/inventory.toml`, `docs/specs/workspace-status-next-actions/spec.md`, `docs/product/intents/FEAT-0034-workspace-registry-retirement.md`, `tests/roster/test_workspace_retirement_inventory.py`, `.workspace-prune-protected.toml`

**Tests:**
- `test_workspace_retirement_inventory.py` gains one test per criterion against the real files, reusing its own record-table parser and governing-row lookup:
  - AC-0004: the Equivalence row by Case text, with Slice, Result, and Authority anchor.
  - AC-0005, AC-0006: the governing row of each named path, by the suite's first-`fnmatchcase` lookup.
  - AC-0007: every row's `consumer`.
- Each `docs/specs/<slug>` literal the new tests name is in `.workspace-prune-protected.toml`.

**Done when:** the roster suite passes, and each of these holds:
- the amended spec's header carries an `Amended in part by:` line naming this spec and what this spec's `Amends:` line names;
- the retirement record's § Equivalence opening sentence contains `slice 6 records`;
- the `entry position` Disposition row's Home cell does not contain `docs/specs/workspace-status-next-actions/*`;
- FEAT-0034 § Unresolved questions contains `Six consumers read registry array order` and contains none of `workspace-status-next-actions`, `next_queue`, or `next_shape`.

### T3 — Release: version, changelog, and delivery membership

**Depends on:** T2
**Verification mode:** goal-based check
**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/<new fragment>.md`, `docs/product/briefs/workspace-registry-retirement-delivery.md` (Spec map row), `workspace.toml` (this spec's entry), `docs/specs/next-item-suggestions-removal/spec.md` and `plan.md` (status and checked criteria)

**Tests:**
- `core` is at one new patch version in both manifests; `python3 tools/changelog.py validate` passes; `lint-brief-coverage.py` lists this spec under the brief and exits 0; `make lint-ruff lint-mypy` passes.

**Done when:** those checks pass and the spec's status and its `workspace.toml` entry move together.

## Risks

- An agent may still pick the top item of Ready to start on its own. No gate can see that, and no eval case can reach the state (see Design).

## Changelog

- 2026-10-27: drafted.
- 2026-10-27: spec approved by eugenelim.
- 2026-10-27: plan approved by eugenelim.
