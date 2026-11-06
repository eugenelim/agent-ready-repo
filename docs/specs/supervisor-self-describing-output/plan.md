# Plan: Supervisor self-describing output

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** the analog is `status`, the one verb that already takes `--json` (`work-supervisor.py` `_parser`) and builds its answer in `_supervisor_loop.status`; every verb prints through the one `_emit` function in `work-supervisor.py`; refusal text is built in `_validate_result`; dispatch findings take their `next_action` from `_FINDING_NEXT_ACTIONS` (`_header_readiness.py`) through `make` in `dispatch.py`; tests drive `main(argv)` through `tests/skills/work-loop/supervisor_harness.py` and `test_dispatch.py`. Named uncertainty: none; the suite that reads § Single-agent fallback is `tests/roster/test_sequential_implementer_dispatch_contract.py`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections or its `Terminal Intent`. A change to tasks, tests, stubs, design, or
> approach is a working-plan edit made by the controller while no attempt is open.

## Approach

Six output changes and one release. T3 writes the routing table first, in `session-resumption.md`, because it is the one home of the routing decision and the script strings are pinned to it. T1, T2 and T5 are independent. T4 adds `route` to `work-supervisor.py` after T1 and T3, because T1 and T4 share the parser and `main`. T6 writes the remaining reference sentences once the behavior exists. T7 adds the two eval cases, T8 the release. No refusal code, exit code, verb or accepted value changes. The riskiest part is T4: `route` must reach every output path, which is why it rides on the one `_emit` function instead of on each call site.

## Constraints

- Pack rules in `packs/AGENTS.md`: `.apm/` is the source; no test under `.apm/`; bump `pack.toml` and `plugin.json` together; load skill modules in tests by pack- and skill-qualified name; shipped pack text cites no internal records.
- The supervisor pins the installed skill's scripts at `start`. Edits land in `packs/core/.apm/`; the installed copy changes only at Closeout.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** run `work-supervisor.py status <spec-dir> --json`, `next <spec-dir>` and `dispatch.py --start <a Shipped spec>` from the rebuilt install at Closeout and read the output.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface reference | T3, T6 | pin test on the three reference files and on the script strings | close-work reads the three files |
| Release history | T8 | release checker output, fragment | close-work reads the fragment |

## Design (LLD)

### Behavior & rules
Traces to: AC-0002 to AC-0009. Owned by: T2, T3, T4, T5.

**The routing table** lives in `session-resumption.md` § Route by what `status` shows. It replaces the current table, states "first match wins, top to bottom", and gives one row per shape, each with the exact string `route` carries. This is the one statement of the routing decision; the script strings are pinned equal to it by a test, so they cannot drift.

| Order | Verb | Shape | `route` string |
| --- | --- | --- | --- |
| 1 | status | non-terminal, `retry_count` at or above the cap | `Retry cap reached: stop and surface it; no replan or approval resets it.` |
| 2 | status, next | standing refusal | `Refused (<code>, owner: <owner>): see supervisor.md, Refusals and their owners.` |
| 3 | status | non-empty `recovery_leftovers` | `Remove or restore each path in recovery_leftovers, then run next.` |
| 4 | status | pending regenerate step | `Run next: it commits the pending regenerate step.` |
| 5 | status, next | terminal | `Run status --check, then the Finish checklist and PR.` |
| 6 | status, next | open `human-decision` request | `Wait for the named human; report only the answers supervisor.md lists for this reason.` |
| 7 | status | any other open request | `Run next and answer the request it issues.` |
| 7 | next | any other request | `Answer the request, write the result outside the spec directory, then run report <spec-dir> <result.json>.` |
| 8 | status | none of the above | `Run next.` |

`<code>` and `<owner>` are the refusal's own `code` and `owner`; `detail` is never included. Row 1 matches `status --check`, where the cap exit wins over the refusal exit. The cap is read from the workspace policy once the workspace exists; the pin and ref-storage refusals fire before it, so only row 2 applies to them.

**Where `route` is added.** One `_emit` function prints every answer. `_main` records the verb (and, once the workspace exists, the cap) in a module-level routing context; `_emit` adds `route` to the payload when the verb is `status` or `next`. Every output path, including each handler in `_main` and the early refusals, therefore carries it by construction. A `status` answer from `loop.status` and any other payload is classified by its keys (`refusal`, `terminal`, `request`, `recovery_leftovers`, `pending_step`).

**`invalid-result` messages** from `_validate_result`: `result must be a JSON object`; `result schema_version must be 1`; `result <field> must be a non-empty string` for `request_id`, `run_id`, `kind`. None repeats a received value. The check itself is unchanged: it still compares `schema_version` with `SCHEMA_VERSION`.

**The frozen-spec finding** keeps code `impossible_transition`. Its `next_action` reads: `This spec is Shipped or closed, so it is frozen. Start follow-up work as a new spec. If the new work reverses part of this one, record the decision in an ADR, then annotate the Status line of this spec as "Shipped (superseded in part by ADR-NNNN — <what changed>; everything else stands)" and of its plan as "Done (superseded in part by ADR-NNNN — <what changed>; everything else stands)"; see new-spec, Superseding a frozen document.` In `_refusal` it applies to a named `--start` or `--resume` target that is in `cooled_paths` (a cooled record names a closed spec; its body is never opened) or whose status is `Shipped`, by replacing `next_action` on the dict `make` returns. No existing dispatch test dispatches a Shipped or cooled target through the table-pair test, so no exception is added there.

### Interfaces & contracts
Traces to: AC-0001. Owned by: T1.

Each verb parser gains `--json` as `store_true`, read by nothing: every verb already prints one JSON object. `--json` goes after the verb; the top-level parser does not take it. `status` keeps its existing flag.

## Tasks

### T1: Every verb accepts `--json` after the verb, with unchanged output

**Depends on:** none

**Tests:**
- TDD, at `main(argv)`: for each of `park`, `gates`, `start`, `next`, `report`, `status`, `resolve-effect`, a call with `--json` and a call without it print equal stdout and return equal exit codes (AC-0001). Read-only verbs compare directly; verbs that refuse on the harness repo compare their refusals.

**Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_json_flag.py`

**Done when:** `test_supervisor_json_flag.py` is green and `test_supervisor_step_loop.py` is still green.

### T2: `invalid-result` names the failing field

**Depends on:** none

**Tests:**
- TDD, at `loop.report` and `_validate_result`: a non-object result, a `schema_version` of the string `"execution-result.v1"`, a `schema_version` of `2`, and each of `request_id`, `run_id`, `kind` missing, empty or not a string refuse `invalid-result`; each detail names its field and the required form; no detail contains the sent value (AC-0007). A well-formed result still passes `_validate_result` unchanged. The check is unchanged, so the tests assert no behavior for `true` or `1.0`.

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py`, `packs/core/tests/skills/work-loop/test_supervisor_results.py`

**Done when:** the new cases in `test_supervisor_results.py` are green and the rest of that file is unchanged and green.

### T3: The routing table is the one home of the routing decision

**Depends on:** none

**Tests:**
- Goal-based: a pin test parses the table in `session-resumption.md` and asserts the first-match statement, one row per shape in the design (nine rows), and that every string is 160 characters or fewer (AC-0005, AC-0011).

**Touches:** `packs/core/.apm/skills/work-loop/references/session-resumption.md`, `packs/core/tests/skills/work-loop/test_supervisor_self_description_guidance.py`

**Done when:** the pin test is green and `tests/roster/test_ase_composition_fixture_evidence.py`, `packs/core/tests/skills/work-loop/test_parked_gates_guidance.py` and `packs/core/tests/skills/work-loop/test_work_intake_dispatch.py` are still green.

### T4: `status` and `next` carry `route`

**Depends on:** T1, T3

**Tests:**
- TDD, at `main(argv)` for `status` and `next`: one case per table row, asserting the answer's `route` equals the table's string for its shape (AC-0002, AC-0004); one case each for the pin-check `supervisor-changed` refusal, the generic-handler `supervisor-changed` refusal, the unsupported-ref-storage refusal, the lock refusal and the internal-error refusal (AC-0002); a run that is both capped and refused names the cap (AC-0003); no `route` contains a refusal's `detail` and every one is 160 characters or fewer (AC-0005); `status --check` exit codes equal the values the existing tests assert (AC-0006).

**Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_route.py`

**Done when:** `test_supervisor_route.py` is green and the status assertions in `test_supervisor_step_loop.py` and `test_supervisor_readiness.py` are unchanged and green.

### T5: The frozen-spec refusal names its route

**Depends on:** none

**Tests:**
- TDD, at `dispatch.py` with `--start` and `--resume` on a `Shipped` spec and on a cooled spec (the existing fixture cools an `Approved` spec): code is `impossible_transition`; `next_action` says the spec is frozen, names a new spec, a decision record and both Status forms, and does not say the spec is `Shipped` outright (AC-0008). A `--start` on an `Implementing` spec and a `--resume` on an `Approved` spec keep the table `next_action` (AC-0009).

**Touches:** `packs/core/.apm/skills/work-loop/scripts/dispatch.py`, `packs/core/tests/skills/work-loop/test_dispatch.py`

**Done when:** the new cases in `test_dispatch.py` are green and the rest of `test_dispatch.py` is unchanged and green.

### T6: Remaining reference sentences

**Depends on:** T1, T4

**Tests:**
- Goal-based: the pin test asserts that `supervisor-mode.md` § Single-agent fallback points an undispatchable reviewer role at `SKILL.md` and holds no `BLOCKED` text (AC-0010), that `supervisor.md` states `--json` goes after the verb and that `status` and `next` carry `route` (AC-0011), that `state-schema.md` lists `route` among the `status` keys (AC-0011), and that each string in `work-supervisor.py` equals its row in the routing table.

**Touches:** `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/references/state-schema.md`, `packs/core/tests/skills/work-loop/test_supervisor_self_description_guidance.py`

**Done when:** the pin test and `tests/roster/test_sequential_implementer_dispatch_contract.py` are green.

### T7: Eval cases

**Depends on:** T5, T6

**Tests:**
- Goal-based: `evals.json` loads, ids are unique, and two new cases carry the prompts and assertions of AC-0012.

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`

**Done when:** `python3 -c "import json;json.load(open('packs/core/.apm/skills/work-loop/evals/evals.json'))"` exits 0, all `id` values are unique, and the two new ids are present.

### T8: Release the `core` patch

**Depends on:** T1, T2, T3, T4, T5, T6, T7

**Tests:**
- Goal-based: `python3 tools/check-core-release.py --base origin/main` passes (AC-0013); `tests/roster/test_registry_upgrade_notes.py` passes.

**Approach:**
- Take the next patch above the `core` version `origin/main` carries when the task runs; set it in `pack.toml`, `.claude-plugin/plugin.json`, a new fragment under `docs/product/changelog.d/`, and `_RELEASED["core"]` in `tests/roster/test_registry_upgrade_notes.py`.

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `tests/roster/test_registry_upgrade_notes.py`

**Done when:** the release checker and the roster file named above both pass.

## Rollout

Ships as one patch release of `core`. Reversible by revert. Closeout, after `terminal`: fetch main and re-check the version, rebuild projections, then run `tests/roster/test_sequential_implementer_dispatch_contract.py`, `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, `tools/test_local_ci_shared_test_deduplication.py`, `tests/roster/test_registry_upgrade_notes.py` and `tests/roster/test_workspace_retirement_inventory.py`; a ledger or note in this spec directory that names retired workspace files needs an inventory row.

## Risks

- A caller compares a whole `status` or `next` object: mitigated by the additive key and unchanged tests.
- Models pipe `status` and `next` output, so `route` may go unseen: accepted; the spec records it as unmeasured.
- Main ships `core` while the run is open: T8 takes the next patch above fetched main and Closeout re-checks before push.
- The installed copy is stale for pinned-script edits until Closeout: roster projection tests fail until then and are excused.

## Changelog
