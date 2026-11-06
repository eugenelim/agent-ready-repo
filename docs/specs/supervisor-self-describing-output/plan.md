# Plan: Supervisor self-describing output

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** the analog is `status`, the one verb that already takes `--json` (`work-supervisor.py` `_parser`) and builds its answer in `_supervisor_loop.status`; every verb prints through the one `_emit` function in `work-supervisor.py`; refusal text is built in `_validate_result`; tests drive `main(argv)` through `tests/skills/work-loop/supervisor_harness.py`. Named uncertainty: none; the suite that reads § Single-agent fallback is `tests/roster/test_sequential_implementer_dispatch_contract.py`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections or its `Terminal Intent`. A change to tasks, tests, stubs, design, or
> approach is a working-plan edit made by the controller while no attempt is open.

## Approach

Five output changes and one release. T3 writes the routing table first, in `session-resumption.md`, because it is the one home of the routing decision and the script strings are pinned to it. T1, T2 and T3 are independent. T4 adds `route` to `work-supervisor.py` after T1 and T3, because T1 and T4 share the parser and `main`. T5 writes the remaining reference sentences once the behavior exists. T6 adds the eval case, T7 the release. No refusal code, exit code or verb changes, and no accepted value changes except `--json` after every verb. The riskiest part is T4: `route` must reach every output path, which is why it rides on the one `_emit` function instead of on each call site.

## Constraints

- Pack rules in `packs/AGENTS.md`: `.apm/` is the source; no test under `.apm/`; bump `pack.toml` and `plugin.json` together; load skill modules in tests by pack- and skill-qualified name; shipped pack text cites no internal records.
- The supervisor pins the installed skill's scripts at `start`. Edits land in `packs/core/.apm/`. Once a task commits a change under `scripts/`, the installed copy differs from the pack source, so the run issues a `regenerate` request before `terminal`; the controller answers it with the repository's self-host command and reports only the envelope, and the supervisor commits the rebuilt skill copies. No task touches `dispatch.py`, so the packaged `_data/` mirror stays untouched.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** run `work-supervisor.py status <spec-dir> --json` and `next <spec-dir>` from the rebuilt install at Closeout and read the output.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface reference | T3, T5 | pin test on the three reference files and on the script strings | close-work reads the three files |
| Release history | T7 | release checker output, fragment | close-work reads the fragment |

## Design (LLD)

### Behavior & rules
Traces to: AC-0002 to AC-0007. Owned by: T2, T3, T4.

**The routing table** lives in `session-resumption.md`, step 3, which T3 retitles "Route by what `status` or `next` shows". It replaces the current table, states "first match wins, top to bottom", and gives one row per shape, each with the exact string `route` carries. This is the one statement of the routing decision: T3 also rewrites step 1 of that file, which says a refusal is "the first thing to deal with", so that it points to the table instead of ranking anything. The script strings are pinned equal to the table by a test, so they cannot drift.

| Order | Verb | Shape | `route` string |
| --- | --- | --- | --- |
| 1 | status, next | cap: `status` on a non-terminal run with `retry_count` at or above the cap; `next` with the `retry-cap` human decision | `Retry cap reached: stop and surface it; no replan or approval resets it.` |
| 2 | status, next | refusal with code `recovery-leftovers` | `Remove or restore the paths the refusal detail names, then run next.` |
| 3 | status, next | any other top-level refusal | `Refused (<code>, owner: <owner>): see supervisor.md, Refusals and their owners.` |
| 4 | status | pending regenerate step | `Run next: it commits the pending regenerate step.` |
| 5 | status, next | terminal | `Run status --check, then the Finish checklist and PR.` |
| 6 | status, next | any other open `human-decision` request | `Read this request's reason under Human decisions in supervisor.md: a named human answers some; for the rest fix the cause, then run next.` |
| 7 | status | any other open request | `Run next and answer the request it issues.` |
| 7 | next | any other request | `Answer the request, write the result outside the spec directory, then run report <spec-dir> <result.json>.` |
| 8 | status | none of the above | `Run next.` |

`<code>` and `<owner>` are the refusal's own `code` and `owner`; `detail` is never included. Rows are decided by value, never by key presence, because a non-refused `status` answer always carries `refusal` (`{}`) and `request` (`None`): rows 2 and 3 are a non-empty top-level `refusal` from any source (`derive`, `recovery.inspect`, a `decide` refusal, or a handler in `_main`), split by its `code`; row 6 is a non-null `request` of kind `human-decision` whose `reason` is not `retry-cap`, and row 7 any other non-null `request`. A live-leftovers run reaches row 2 because the recovery gate refuses `recovery-leftovers`. Row 1 matches `status --check`, where the cap exit wins over the refusal exit. `next` follows `decide`'s order, which checks divergence and the recovery gate before the cap: for a capped run with no refusal and no earlier gate, `next` issues the `retry-cap` request and gets the same string as `status`; for a capped run with a standing refusal or an earlier gate, `next` returns that refusal (row 2 or 3) or that `human-decision` (row 6) while `status` names the cap. The cap is read from the workspace policy once the workspace exists. The pin refusal fires before the workspace exists, and the ref-storage `status` payload carries no `retry_count`, so row 3 is the only row those two refusals reach. A usage error prints `{"error": "usage", ...}` and exits 2; it is not a run view or a refusal and carries no `route`.

**Where `route` is added.** One `_emit` function prints every answer. `_main` resets a module-level routing context at the start of every call, records the verb in it (and, once the workspace exists, the cap), and clears it on exit, so a later in-process call never inherits it. `_emit` adds `route` to a payload that is a run view or carries a top-level `refusal` when the verb is `status` or `next`, and skips an `{"error": "usage"}` payload. The tested paths are listed in T4; any other path that prints through `_emit` carries `route` by the same construction.

**`invalid-result` messages** from `_validate_result`: `result must be a JSON object`; `result schema_version must be 1`; `result <field> must be a non-empty string` for `request_id`, `run_id`, `kind`. None repeats a received value. The check itself is unchanged: it still compares `schema_version` with `SCHEMA_VERSION`.

### Interfaces & contracts
Traces to: AC-0001. Owned by: T1.

Each verb parser gains `--json` as `store_true`, read by nothing: every verb already prints one JSON object. `--json` goes after the verb; the top-level parser does not take it. `status` keeps its existing flag.

## Tasks

### T1: Every verb accepts `--json` after the verb, with unchanged output

**Depends on:** none

**Tests:**
- TDD, at `main(argv)`: for each of `park`, `gates`, `start`, `next`, `report`, `status`, `resolve-effect`, a call with `--json` and a call without it print equal stdout and return equal exit codes (AC-0001). Read-only verbs compare directly; verbs that refuse on the harness repo compare their refusals. The usage lines in the module docstring of `work-supervisor.py` show `[--json]` on every verb.

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
- Goal-based: a pin test parses the table in `session-resumption.md` and asserts the first-match statement, one row per shape in the design (nine rows), that the step is titled "Route by what `status` or `next` shows", that every string is 160 characters or fewer (AC-0005), and that step 1 no longer holds the sentence "the first thing to deal with" and points to the table (AC-0009).

**Touches:** `packs/core/.apm/skills/work-loop/references/session-resumption.md`, `packs/core/tests/skills/work-loop/test_supervisor_self_description_guidance.py`

**Done when:** the pin test is green and every suite listed by `grep -rl 'session-resumption' packs/core/tests tests --include='test_*.py'` is green.

### T4: `status` and `next` carry `route`

**Depends on:** T1, T3

**Tests:**
- TDD, at `main(argv)` for `status` and `next`: one case per table row and verb, asserting the answer's `route` equals the table's string for its shape, with the row 2 case built from a run that has live leftovers and no divergence (AC-0002, AC-0004); one case each for the pin-check `supervisor-changed` refusal and the unsupported-ref-storage refusal on `status` (AC-0002), and for the lock and internal-error refusals on `status`, each produced by a forced fault because `status` takes no lock (AC-0002) and the pin-check refusal on `next` (AC-0004); a usage error on `status` and on `next` carries no `route`, and a second in-process call after a `status` call does not inherit its routing context (AC-0002, AC-0004); a capped run with no refusal and no earlier gate gives the cap string on `status` and on `next`, and a capped run with a standing refusal gives the cap string on `status` and the refusal row on `next` (AC-0003); no `route` contains a refusal's `detail` and every one is 160 characters or fewer (AC-0005); `status --check` exit codes equal the values the existing tests assert (AC-0006).

**Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/tests/skills/work-loop/test_supervisor_route.py`

**Done when:** `test_supervisor_route.py` is green and the status assertions in `test_supervisor_step_loop.py` and `test_supervisor_readiness.py` are unchanged and green.

### T5: Remaining reference sentences

**Depends on:** T1, T4

**Tests:**
- Goal-based: the pin test asserts that `supervisor-mode.md` § Single-agent fallback names `SKILL.md` § Step 4. REVIEW and the `fallback` and `mandatory_when` fields of `review-rules.json`, and holds no `BLOCKED` text (AC-0008), that `supervisor.md` states `--json` goes after the verb and that `status` and `next` carry `route` (AC-0009), that `state-schema.md` lists `route` among the `status` keys (AC-0009), and that each string in `work-supervisor.py` equals its row in the routing table.

**Touches:** `packs/core/.apm/skills/work-loop/references/supervisor-mode.md`, `packs/core/.apm/skills/work-loop/references/supervisor.md`, `packs/core/.apm/skills/work-loop/references/state-schema.md`, `packs/core/tests/skills/work-loop/test_supervisor_self_description_guidance.py`

**Done when:** the pin test is green and every suite listed by `grep -rlE 'supervisor(-mode)?\.md|state-schema\.md' packs/core/tests tests --include='test_*.py'` is green, which includes `tests/roster/test_sequential_implementer_dispatch_contract.py`.

### T6: Eval case

**Depends on:** T5

**Tests:**
- Goal-based: `evals.json` loads, ids are unique, and one new case carries the `prompt`, `expected_output` and `assertions` of AC-0010.

**Touches:** `packs/core/.apm/skills/work-loop/evals/evals.json`

**Done when:** `python3 -c "import json;json.load(open('packs/core/.apm/skills/work-loop/evals/evals.json'))"` exits 0, all `id` values are unique, the new id is present, and `packs/core/tests/skills/work-loop/test_supervisor_cutover_source_checks.py` is green.

### T7: Release the `core` patch

**Depends on:** T1, T2, T3, T4, T5, T6

**Tests:**
- Goal-based: `python3 tools/check-core-release.py --base origin/main` passes (AC-0011); `tests/roster/test_registry_upgrade_notes.py` passes.

**Approach:**
- Run `git fetch origin` and take the next patch above the `core` version fetched `origin/main` carries when the task runs; set it in `pack.toml`, `.claude-plugin/plugin.json`, a new fragment under `docs/product/changelog.d/`, and `_RELEASED["core"]` in `tests/roster/test_registry_upgrade_notes.py`.

**Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/`, `tests/roster/test_registry_upgrade_notes.py`

**Done when:** the release checker and the roster file named above both pass.

## Rollout

Ships as one patch release of `core`. Reversible by revert. Closeout, after `terminal`: fetch main and re-check the version, rebuild projections, then run `tests/roster/test_sequential_implementer_dispatch_contract.py`, `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, `tools/test_local_ci_shared_test_deduplication.py`, `tests/roster/test_registry_upgrade_notes.py` and `tests/roster/test_workspace_retirement_inventory.py`; a ledger or note in this spec directory that names retired workspace files needs an inventory row.

## Risks

- A caller compares a whole `status` or `next` object: mitigated by the additive key and unchanged tests.
- Models pipe `status` and `next` output, so `route` may go unseen: accepted; the spec records it as unmeasured.
- Main ships `core` while the run is open: T7 takes the next patch above fetched main and Closeout re-checks before push.
- The installed copy is stale for pinned-script edits until the run's `regenerate` request, and for reference-only edits until Closeout: roster projection tests fail until then and are excused.

## Changelog
