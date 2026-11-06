# Plan: Supervisor self-describing output

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** the analog is `status`, the one verb that already takes `--json` (`work-supervisor.py` `_parser`) and builds its answer in `_supervisor_loop.status`; refusal text is built in `_validate_result`; dispatch findings take their `next_action` from `_FINDING_NEXT_ACTIONS` (`_header_readiness.py`) through `make` in `dispatch.py`; tests drive `main(argv)` through `tests/skills/work-loop/supervisor_harness.py` and `test_dispatch.py`. Named uncertainty: none; the suite that reads § Single-agent fallback is `tests/roster/test_sequential_implementer_dispatch_contract.py`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections or its `Terminal Intent`. A change to tasks, tests, stubs, design, or
> approach is a working-plan edit made by the controller while no attempt is open.

## Approach

Five small, independent output changes and one release. T1 to T3 edit `work-supervisor.py` and `_supervisor_loop.py` in order, because T1 and T3 share the parser and `main`. T4 edits `dispatch.py` alone. T5 writes the reference sentences once the behavior exists. T6 adds the two eval cases. T7 bumps the release. Every change alters wording or adds one key and one accepted flag; no refusal code, exit code, or verb changes. The riskiest part is T3: a new `status` key must not disturb callers, which is why the key is additive and the existing status tests run unchanged.

## Constraints

- Pack rules in `packs/AGENTS.md`: `.apm/` is the source; no test under `.apm/`; bump `pack.toml` and `plugin.json` together; load skill modules in tests by pack- and skill-qualified name; shipped pack text cites no internal records.
- The supervisor pins the installed skill's scripts at `start`. Edits land in `packs/core/.apm/`; the installed copy changes only at Closeout.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** run `work-supervisor.py status <spec-dir> --json` and `dispatch.py --start <a Shipped spec>` from the rebuilt install at Closeout and read the output.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface reference | T5 | pin test on the three reference files | close-work reads the three files |
| Release history | T7 | release checker output, fragment | close-work reads the fragment |

## Design (LLD)

### Behavior & rules
Traces to: the route, `invalid-result` and `Shipped` criteria. Owned by: T2, T3, T4.

`route` is computed once, in `work-supervisor.py`, by one helper that every `status` emission passes through: the answer `loop.status` builds, the `supervisor-changed` pin refusal on `status`, and the unsupported-ref-storage refusal on `status`. Precedence follows `status --check`, first match wins, each a fixed string of 160 characters or fewer:

1. A non-terminal run whose `retry_count` is at or above `implementation_retry_cap` (read from the workspace policy, so the refusal branch needs no new key): `Retry cap reached: stop and surface it; no replan or approval resets it.`
2. Standing refusal: `Refused (<code>, owner: <owner>): see supervisor.md, Refusals and their owners.` The refusal `detail` is never included.
3. Non-empty `recovery_leftovers`: `Remove or restore each path in recovery_leftovers, then run next.`
4. A pending regenerate step: `Run next: it commits the pending regenerate step.`
5. Terminal: `Run status --check, then the Finish checklist and PR.`
6. Open request of kind `human-decision`: `Wait for the named human; report only the answers supervisor.md lists for this reason.`
7. Any other open request: `Run next and answer the request it issues.`
8. Otherwise: `Run next.`

The two early refusals carry no run view, so only row 2 applies to them.

`invalid-result` messages from `_validate_result`: `result must be a JSON object`; `result schema_version must be 1`; `result <field> must be a non-empty string` for `request_id`, `run_id`, `kind`. None repeats a received value.

The `Shipped` finding keeps code `impossible_transition`; its `next_action` reads: `A Shipped spec is frozen. Start follow-up work as a new spec. If the new work reverses part of this one, write a decision record and set this spec's Status line to Shipped (superseded in part by ADR-NNNN — <what changed>; everything else stands); edit nothing else.` In `_refusal` it applies to a named `--start` or `--resume` target that is in `cooled_paths` (a cooled spec is a `Shipped` spec whose lifecycle record has cooled; its body is never opened) or whose status is `Shipped`, by replacing `next_action` on the dict `make` returns. This breaks the dispatch rule that a printed `next_action` equals its table entry for this one case; T4 names it as the exception in the table-pair test.

### Interfaces & contracts
Traces to: the `--json` criterion. Owned by: T1.

Each verb parser gains `--json` as `store_true`, read by nothing: every verb already prints one JSON object. `status` keeps its existing flag.

## Tasks

### T1: Every verb accepts `--json` with unchanged output

**Depends on:** none

**Tests:**
- TDD, at `main(argv)`: for each of `park`, `gates`, `start`, `next`, `report`, `status`, `resolve-effect`, a call with `--json` and a call without it print equal stdout and return equal exit codes (AC-0001). Read-only verbs compare directly; verbs that refuse on the harness repo compare their refusals.

**Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_json_flag.py`

**Done when:** `test_supervisor_json_flag.py` is green and `test_supervisor_step_loop.py` is still green.

### T2: `invalid-result` names the failing field

**Depends on:** none

**Tests:**
- TDD, at `loop.report`: a non-object result, a `schema_version` of the string `"execution-result.v1"`, a `schema_version` of `2`, and each of `request_id`, `run_id`, `kind` missing, empty or not a string refuse `invalid-result`; each detail names its field and the required form; no detail contains the sent value (AC-0005). The check itself is unchanged, so the tests assert no behavior for `true` or `1.0`.

**Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_loop.py`, `packs/core/tests/skills/work-loop/test_supervisor_results.py`

**Done when:** the new cases in `test_supervisor_results.py` are green and the existing `invalid-result` cases in `test_supervisor_review_closure.py` still pass.

### T3: `status` carries a `route`

**Depends on:** T1

**Tests:**
- TDD, at `main(["status", ...])`: one case per route row in the design, plus one case each for the `supervisor-changed` refusal and the unsupported-ref-storage refusal, and one for a run that is both capped and refused (route names the cap); each checks the string and its length at or under 160, and that a refusal's `detail` text is absent (AC-0002, AC-0003); `status --check` exit codes equal the values the existing tests already assert (AC-0004).

**Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_status_route.py`

**Done when:** `test_supervisor_status_route.py` is green and the status assertions in `test_supervisor_step_loop.py` and `test_supervisor_readiness.py` are unchanged and green.

### T4: The `Shipped` refusal names its route

**Depends on:** none

**Tests:**
- TDD, at `dispatch.py` with `--start` and `--resume` on a `Shipped` spec and on a cooled spec: code is `impossible_transition`, `next_action` names a new spec, a decision record and the `Shipped (superseded in part by ADR-NNNN …)` form (AC-0006). A `--start` on an `Implementing` spec and a `--resume` on an `Approved` spec keep the table `next_action` (AC-0007). `test_every_finding_dispatch_prints_is_a_table_pair` gains a named exception for the Shipped route text.

**Touches:** `packs/core/.apm/skills/work-loop/scripts/dispatch.py`, `packs/core/tests/skills/work-loop/test_dispatch.py`

**Done when:** the new cases in `test_dispatch.py` are green and the rest of `test_dispatch.py` is unchanged and green.

### T5: Reference sentences

**Depends on:** T1, T3

**Tests:**
- Goal-based: a pin test asserts that `supervisor-mode.md` § Single-agent fallback points an undispatchable reviewer role at `SKILL.md` and holds no `BLOCKED` text (AC-0008), that `supervisor.md` states `--json` goes after the verb and defines `route`, that `state-schema.md` lists `route` among the `status` keys, and that `session-resumption.md` names `route` among the keys it reads (AC-0009).

**Touches:** `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/references/state-schema.md`, `packs/core/.apm/skills/work-loop/references/session-resumption.md`, `packs/core/tests/skills/work-loop/test_supervisor_self_description_guidance.py`

**Done when:** the pin test and `tests/roster/test_sequential_implementer_dispatch_contract.py` are green.

### T6: Eval cases

**Depends on:** T4, T5

**Tests:**
- Goal-based: `evals.json` loads, ids are unique, and two new cases carry the prompts and assertions of AC-0010.

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`

**Done when:** `python3 -c "import json;json.load(open('packs/core/.apm/skills/work-loop/evals/evals.json'))"` exits 0, all `id` values are unique, and the two new ids are present.

### T7: Release the `core` patch

**Depends on:** T1, T2, T3, T4, T5, T6

**Tests:**
- Goal-based: `python3 tools/check-core-release.py --base origin/main` passes (AC-0011); `tests/roster/test_registry_upgrade_notes.py` passes.

**Approach:**
- Fetch `origin/main` first and take the next patch above the `core` version it carries; set it in `pack.toml`, `.claude-plugin/plugin.json`, a new fragment under `docs/product/changelog.d/`, and `_RELEASED["core"]` in `tests/roster/test_registry_upgrade_notes.py`.

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `tests/roster/test_registry_upgrade_notes.py`

**Done when:** the release checker and the roster file named above both pass.

## Rollout

Ships as one patch release of `core`. Reversible by revert. Closeout, after `terminal`: rebuild projections, then run `tests/roster/test_sequential_implementer_dispatch_contract.py`, `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, `tools/test_local_ci_shared_test_deduplication.py`, `tests/roster/test_registry_upgrade_notes.py` and `tests/roster/test_workspace_retirement_inventory.py`; a ledger or note in this spec directory that names retired workspace files needs an inventory row.

## Risks

- A caller compares a whole `status` object: mitigated by the additive key and unchanged status tests.
- Models filter `status` output, so `route` may go unseen: accepted; the spec records it as unmeasured.
- Main ships `core` while the run is open: T7 takes the next patch above fetched main and re-checks before push.
- The installed copy is stale for pinned-script edits until Closeout: roster projection tests fail until then and are excused.

## Changelog
