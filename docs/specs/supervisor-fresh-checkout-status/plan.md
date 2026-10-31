# Plan: Supervisor status in a checkout without the run's store

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/work-loop-execution-supervisor.md` (run store row); the pin checks `work-supervisor.py` `_preflight` and `_supervisor_attempt.py` `AttemptStore.check_pins`; their suite `packs/core/tests/skills/work-loop/test_supervisor_pinning.py` (fixture `pinned_template`, helpers `_copy_repo`, `_run`, `_load_cli`) and the harness controller `supervisor_harness.Controller.drive`, which `test_supervisor_consumer_map.py` uses to reach terminal. No new structure.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place while no attempt is open.

## Approach

One code task changes the two pin checks and the `status` view; one task updates the reference, the architecture page and the captured defect; one task releases `core`. The riskiest part is keeping the exception to `status` alone: both checks must test the verb and the store directory's absence together, so a store that exists but is damaged still refuses.

This run changes the supervisor scripts it runs under. The installed copy under `.claude/skills/work-loop/` is regenerated only when `next` issues the `regenerate` request, never by hand mid-run.

## Constraints

- ADR-0144: the supervisor is the skill-shipped procedure owner; the pin check stays its first act.
- ADR-0074 and the scripts' own rule: standard library only, and the entry point imports no sibling before its pre-import check decides.
- `execution-supervisor-attempt-security`'s pin-check criterion (number 0014) holds for every verb but `status`, and for `status` whenever the store directory exists.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** T4.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `references/supervisor.md` | T2 | the reference states the `verification` field and the `status` exception | review reads it |
| Architecture page run-store row | T2 | the row's text | review reads it |
| Captured defect | T2 | `docs/product/captured/supervisor-common-config-residue.md` | the file's `Kind:` and `Status:` lines |
| Release history | T3 | version and changelog gates | AC-0008 |
| Delivery records | T4 | `delivery/` committed by the supervisor | AC-0007 |

## Design (LLD)

### Behavior & rules

Traces to: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006.

- **Pre-import check.** In `_preflight`, the refusal `the supervisor's pin record is missing` for a working run absent from the pinned runs is skipped only when the verb is `status` and `os.lstat(<store root>/<working run>)` raises `FileNotFoundError`; any other `OSError` raises `_PinRefused(..., unverifiable=True)`. Every other refusal there is unchanged and still runs on that path: the per-directory `records no spec` and `has no pin record` refusals, the comparison with every pinned spec store's pins (the `guarded` list keyed on `pinned[0] == spec`), and the open-attempt guard over other runs. `_preflight` returns the set of run ids whose pins it compared with the installed files and found equal, to the pins or to that run's open `regenerate` source digests: every `guarded` store that matched.
- **Post-import check.** `_main` hands that result to `workspace.attempts`. `AttemptStore.check_pins` reads the committed run. When it has a pin record, the existing comparison runs unchanged, and `verification` is `"pinned"` when the committed run id is in the pre-import set, `"committed-records-only"` otherwise; it adds no refusal. When it has no pin record, the verb is `status`, and the committed run's store directory is absent by the same `FileNotFoundError` test, it returns with `verification` `"committed-records-only"`; a present store directory with no pins still refuses. The attribute defaults to `"committed-records-only"`, which is what a spec with no approvals, or a call with no installed digests (the in-process test seam), reports.
- **Which run id governs.** The committed run governs `check_pins` and the view; the working run governs only the pre-import no-store lookup. A missing or forged working copy changes nothing else: every pinned spec store is still compared, so the committed run's store is compared and its id lands in the pre-import set.
- **The view.** The `status` branch of `_main` adds `verification` to the view `loop.status` returns before printing it. `--check`'s exit rules are unchanged.
- **No writes.** The no-store `status` path writes nothing: the pin event logger runs only on a `_PinRefused`, and `status` never calls a store write. The probe on the repro branch showed no store directory created; AC-0003's case is the guard.

### Design decisions

- **Absence of the store directory is the signal, not absence of pins.** A store directory is born whole with its spec record, so an existing directory without pins is a crash window or damage, which the attempt-security pin-check criterion refuses. Only a checkout that never ran the supervisor, or whose store was removed whole, has no directory.
- **Any run state, not only terminal.** A squash merge drops the supervisor's trailered commits, so on `main` a finished run derives as non-terminal; limiting the exception to terminal runs would leave `main` red after the next squash merge (owner decision, 2026-10-30).

## Tasks

### T1: `status` without the store

- **Depends on:** none
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`, `packs/core/.apm/skills/work-loop/scripts/_supervisor_attempt.py`, `packs/core/tests/skills/work-loop/test_supervisor_pinning.py`
- **Tests:** for AC-0001, AC-0002, AC-0003, AC-0004, AC-0005 and AC-0006, in `test_supervisor_pinning.py`, each running the real CLI through `_run(_load_cli(skill), …)`:
  - a module-scoped terminal template: a harness repository started and driven to terminal by `h.Controller(...).drive()`;
  - a no-store checkout made by `git clone` of that terminal repository: `status --check` exits `0`, `terminal` is true, `verification` is `committed-records-only`;
  - a no-store checkout whose `HEAD` is one commit holding the template's tree with no supervisor commit (the squash shape): `status --check` exits `0` with an empty `refusal` and `committed-records-only`;
  - after each of those two calls: no `.git/agentbundle-supervisor`, no `<spec>/.supervisor`, no `.loop-run`, and the same `HEAD` and porcelain status;
  - in the terminal clone, `start`, `next`, `report` and `resolve-effect` each refuse `supervisor-changed` with `the supervisor's pin record is missing`, `HEAD` unchanged;
  - new cases for AC-0005, each with an installed pinned file edited unless stated: in a copy of the started template, the working-tree approvals' first line rewritten to a run id with no store; in the terminal clone, another spec's run holding an open attempt; in the started template, `pins.json` removed (no edit); and, for the post-import check, a started template whose working-tree first line names a run with no store while the committed run's store has its `pins.json` removed and an orphan mark (no edit);
  - `status` on the unmodified started template prints `verification: pinned`;
  - in the started template with the working-tree `delivery/approvals.jsonl` deleted and the install unedited, `next` exits as it does at the base and `status` prints `pinned`;
  - in the started template with the working-tree approvals' first line rewritten to a run id that has no store and the install unedited, `status` prints `pinned`;
  - during an open `regenerate` with the edited pack source copied into the installed skill, as `test_an_open_regenerate_is_honored_only_while_it_is_open` does, so the installed files equal the recorded source and differ from the pins, `status` prints `pinned`.
- **Done when:** the AC-0001, AC-0002, AC-0003 and AC-0006 cases red at the base for the reasons the Testing Strategy states, then pass; the AC-0004 and AC-0005 cases pass before and after the change; and the whole pinning suite and `make lint-ruff lint-mypy` pass.

### T2: Reference, architecture page and captured defect

- **Depends on:** T1
- **Verification mode:** goal-based check
- **Touches:** `packs/core/.apm/skills/work-loop/references/supervisor.md`, `docs/architecture/work-loop-execution-supervisor.md`, `docs/product/captured/supervisor-common-config-residue.md`
- **Tests:** none; the reference's Refusals row and Status section, and the architecture run-store row, state the `status` exception and the `verification` field; the Refusals row also says that in a checkout that ran the supervisor, once a later release changes the installed supervisor, a finished run's `status` refuses on its pins until its store directory is removed; the captured file carries `Kind: defect` and `Status: Open`.
- **Done when:** `agentbundle catalogue lint --root . --deep` and the captured-item lint the pre-PR catalogue hook runs both pass.

### T3: Release

- **Depends on:** T1, T2
- **Verification mode:** goal-based check
- **Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, one `docs/product/changelog.d/` fragment, generated projections
- **Tests:** none; AC-0008.
- **Done when:** the version-bump and changelog gates pass and `make build-self` leaves no diff.

### T4: The hook on this branch

- **Depends on:** T1, T2, T3
- **Verification mode:** visual / manual QA
- **Touches:** `tests/roster/test_core_pre_pr_hook.py`, `docs/specs/supervisor-fresh-checkout-status/notes/verification-ledger.md`
- **Tests:** for AC-0007: `test_pre_pr_passes_when_no_spec_holds_approvals` removes every `docs/specs/*/delivery` directory from its sandbox and commits that before running the hook, its assertions unchanged; it and `test_shipped_pre_pr_runs_no_linter_labels` pass on this branch with its `delivery/` committed. The branch is pushed, cloned fresh into a temporary directory at the pushed commit, and in that clone `status docs/specs/supervisor-fresh-checkout-status --check` and the shipped `pre-pr.py` each exit `0`. The commit id, commands and exit codes are recorded in the ledger.
- **Done when:** the ledger holds those commands with exit `0`.

## Rollout

- **Delivery:** one `core` patch release. Adopters get it on their next install; nothing in their repositories changes.
- **Reversal:** revert the release; no stored state changes shape.

## Risks

- A controller that reads `status --json` and rejects unknown keys sees one new key. The shipped hook reads only the exit code.

## Changelog

- 2026-10-30: spec approved by eugenelim at `01c13d980`.
