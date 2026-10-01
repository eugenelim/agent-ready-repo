# Plan: loop-cohort wave decision

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - Governing design: [`docs/architecture/loop-parallelism.md` § 4](../../architecture/loop-parallelism.md#4-the-wave-decision-contract) — owns the payload, admission walk, reason and refusal vocabularies, guard order, and screen/gate boundary.
  - Governing decisions: ADR-0005 D1–D6, ADR-0061 D5 with its 2026-09-22 erratum, and RFC-0015 Proposal decisions 1–3 with its 2026-05-29 and 2026-09-25 errata.
  - Source convention: [`packs/AGENTS.md`](../../../packs/AGENTS.md) and [`packs/core/AGENTS.md`](../../../packs/core/AGENTS.md) — `.apm/` is source, a new primitive takes a minor bump, pack evals change with non-cosmetic content, and adapter copies are generated.
  - Analogous implementation: `cmd_status`, `parse_touches_by_task`, `globs_overlap`, `wave_touches_disjoint`, `_DANGER_PATH_RE`, and the untouched `cmd_dispatch_decision` in `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`.
  - Guard construction path: `read_state`, `_state_or_reason`, `check_identity`, and `check_schedule_current` in `packs/core/.apm/skills/work-loop/scripts/_loop_guards.py`.
  - Corresponding tests: `packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py`, with existing subprocess helpers and screen/gate separation assertions; repository-level JSON Schema precedent in `tests/roster/test_loop_run_event_contract.py`. Pack tests stay within `packs/core/`; a new named roster step owns the repository contract and runs on CI rather than locally.
  - Named deviation: `wave-decision --json` is the first cohort verb whose refusal is a stdout JSON envelope; all existing verbs keep the shipped stderr `stop()` convention.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/loop-cohort-wave-decision/notes/verification-ledger.md`.

## Approach

Add one parser entry and one read-only handler to the existing cohort script.
The handler reuses the shipped plan and glob predicates, maps guard failures to
the closed refusal vocabulary without parsing diagnostic prose, builds the
greedy task cohort and pair matrix in plan order, then renders either the human
view or one JSON envelope. Before construction it validates the success-envelope
state scalars, task uniqueness, and the Owner-approved `Touches:` budgets. Pack
tests drive the real file-path CLI and compare `state.json` bytes on every path;
a repository-owned roster test validates emitted JSON against the public schema.

## Constraints

- `loop-parallelism.md` § 4 is the implementation design; this plan does not reopen its choices.
- ADR-0005 D4 remains the only file-disjointness greenlight because it reads populated branches; no pre-dispatch result satisfies it.
- ADR-0061 D5 still defers concurrent execution. The verb returns evidence only.
- `cmd_dispatch_decision` and its parser stay byte-identical. The new parser uses no shared `parallel` token with that gate.
- `_DANGER_PATH_RE` stays text-matching and unchanged, but the maintained guidance names both consumers.
- Existing bounded readers and exported guards own state and plan reads. No raw `Path.read_text()` or new file reader is added.
- The Owner-approved effective-touch budgets are owned by spec AC-0018 and `loop-parallelism.md` § 4. Limit breaches are authored-plan failures and fold into `plan-status-illegal` before classification or pair construction.
- The JSON Schema is hand-authored because no `jsonschema` authoring skill is installed; Draft 2020-12 validation is the enforcement substitute.
- Repository-level schema assertions live in `tests/roster/`, with the required named build-check step, parity disposition, and prune protection. The roster test is not run locally; the PR's build-check owns it.
- No local roster run, `make ci`, § 3 plan-width work, D5 lift, new dependency, new module, or new top-level directory is in scope.

## Construction tests

**Integration tests:** the pack suite drives the real `loop-cohort.py` CLI for every verdict and refusal shape without reading outside `packs/core/`. A repository-owned roster module validates representative CLI payloads and negative fixtures against the repository contract.

**Manual verification:** after source projection, invoke the built `wave-decision --json` on one temporary scheduled cohort and record stdout, stderr, exit code, and before/after state hashes in the verification ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface contract — JSON Schema and spec | T1, T3 | schema-validation tests over emitted payloads | contract trace resolves both ways and spec criteria are checked |
| Current architecture — `loop-parallelism.md` § 4 | T4 | content assertion for approval state plus unchanged D4/D5 boundary | architecture review finds no planned/untaken claim for the shipped verb |
| Supervisor procedure and contract discovery | T4 | content assertions and generated-copy parity | built work-loop references expose one consistent screen/gate story |
| Release history and version surfaces | T4 | version-equality check, changelog parser/build output | fresh-base minor version and product release entry are present |
| Eval contract record | T4 | JSON parse and exact case assertions | eval entry remains present without being cited as verification |

## Design (LLD)

### Data & schema

The public contract is a Draft 2020-12 JSON Schema with a top-level `oneOf` for
verdict and refusal envelopes. Verdict objects are closed at every object node,
pin `payload_version: 1` and `admission_pending: true`, and use closed enums for
wave, task, pair, and reason vocabularies. Task IDs mirror the plan grammar
`T[0-9]+[a-z]?` with a 64-character maximum; arrays pin the Owner-approved
maximum of 64 unfinished tasks and 2,016 pairs. Each task touch array has at
most 64 unique strings, each touch and reason glob has at most 256 characters,
and `x-max-total-touches: 256` records the aggregate CLI invariant that Draft
2020-12 cannot express as a sum over nested arrays. Refusal objects are closed, pin
`payload_version: 1`, enumerate all nine codes, and constrain string `detail`
to 1–96 characters. The renderer maps each code to one fixed public-safe JSON
message; raw guard and exception diagnostics remain available only through the
human stderr path.

Traces to: AC-0001, AC-0003, AC-0004, AC-0006–AC-0009, AC-0011, AC-0015, AC-0018 · `contracts/jsonschema/loop-cohort-wave-decision.schema.json`.

Owned by: T1, T3, T4.

### Interfaces & contracts

The CLI surface is `loop-cohort wave-decision <spec-dir> [--wave <n>]
[--force-sequential [<task-id>]] [--json]`. Bare `--force-sequential`
refuses every task; the valued form refuses only the named task ID.
JSON success and refusal use stdout; human success uses stdout; human refusal
uses `stop()` on stderr. Exit codes are 0 for verdicts and 1 for refusals.
JSON refusal detail is selected from a closed code-to-message map and is never
constructed from the raw diagnostic argument supplied to the renderer.

The handler first calls `_resolve_spec_dir`; a confinement failure emits the
folded `state-unreadable` refusal through the selected channel before any state
or plan read. It then calls `check_identity` with no expected run id, validates
that `run_id` is a non-empty string, the three schedule fields it consumes, the
selected task-ID uniqueness/grammar/length, and the 64-task remaining-wave limit,
then calls `check_schedule_current` before reading touches from the scheduled
`plan.md`. After the bounded plan read and before classification, it validates
the 64-per-task, 256-per-wave, and 256-character effective-touch limits. It
echoes the stored scheduled `plan_hash` and never recomputes that field for output.

Traces to: AC-0001, AC-0002, AC-0007, AC-0008, AC-0010–AC-0012, AC-0015–AC-0018 · `contracts/jsonschema/loop-cohort-wave-decision.schema.json`.

Owned by: T1, T3, T4.

### Failure, edge cases & resilience

The handler maps guard result branches to codes by the guard or precondition
that decided them. It does not split the deliberately folded spec-path/state
read failures or plan-read/status failures by parsing their prose. `no-schedule`
and state-shape `state-malformed` checks precede schedule-currency checks; wave
bounds precede indexing; `empty-wave`, `run_id`, task-ID uniqueness/validation,
and the 64-task limit follow completed-task subtraction. Effective-touch limits
run after schedule currency and the bounded plan read but before danger-path,
overlap, admission, or pair construction. Every path is
read-only and is compared against the original state bytes.

Traces to: AC-0007, AC-0008, AC-0012, AC-0015, AC-0017, AC-0018.

Owned by: T1, T2, T3, T4.

### Quality attributes (NFRs)

Determinism comes from plan order for the greedy walk and pair combinations.
Auditability comes from closed reason objects and a schema that refuses unknown
fields. Safety comes from a vocabulary disjoint from the post-write gate, a
source pin that leaves its handler and parser untouched, and the measured
resource bounds owned by spec AC-0018 and `loop-parallelism.md` § 4.

Traces to: AC-0003–AC-0011, AC-0015, AC-0017, AC-0018.

Owned by: T1, T2, T3, T4.

## Tasks

### T1: The emitted decision and refusal envelopes satisfy the public contract

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py, contracts/jsonschema/loop-cohort-wave-decision.schema.json, contracts/README.md

**Tests:**

- Materialize the exact stub below after the existing subprocess helpers in `test_loop_cohort_schedule.py`; function `test_wave_decision_json_reports_scheduled_wave` covers AC-0001, AC-0002, and AC-0012 (`stub: true`).

```python
# STUB: AC-0001 — the real CLI emits one read-only decision envelope
def test_wave_decision_json_reports_scheduled_wave(git_repo):
    plan = (
        "# Plan\n\n- **Status:** Executing\n\n"
        "### T1: a\n**Depends on:** none\n**Touches:** src/a/*.py\n\n"
        "### T2: b\n**Depends on:** none\n**Touches:** src/b/*.py\n"
    )
    scheduled = _schedule(git_repo, plan)
    assert scheduled.returncode == 0, scheduled.stderr
    before = (git_repo / "state.json").read_bytes()

    result = _run_lc("wave-decision", str(git_repo), "--json", cwd=git_repo)

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["payload_version"] == 1
    assert payload["wave"] == ["T1", "T2"]
    assert payload["wave_disposition"] == "all-parallel-capable"
    assert payload["cohort"] == ["T1", "T2"]
    assert payload["admission_pending"] is True
    assert (git_repo / "state.json").read_bytes() == before
```

PLAN validation: `python3 -m py_compile` passed. The isolated named pytest case
failed at the intended contract edge because argparse does not yet recognize
`wave-decision`; the process exited 2 and listed the shipped verb set.

- Deferred assertions completed during green: parameterize widths 1–5 and assert the pair count equals `n*(n-1)//2`, order is `itertools.combinations(wave, 2)`, pair objects have no disposition, and relations cover `disjoint`, `overlapping`, and `unknown` (AC-0003).
- Drive both `--force-sequential <task-id>` and bare `--force-sequential`; assert valued scope is one named wave task, bare scope is the whole wave, both emit verdicts in JSON and human modes, and forced reasons still accumulate with other unary reasons. Drive the other reason codes, exact per-code fields, and a three-peer overlap fixture that proves the first admitted collision short-circuits later peers (AC-0004, AC-0005, AC-0016).
- Drive single-task, all-capable, partial, all-sequential, and no-admitted-peer shapes; assert cohort cardinality is zero or at least two (AC-0006).
- Parameterize the nine refusal codes. Include absolute-outside, `..`, symlink-escape, invalid/overlong task-ID, 64-task success, and 65-task refusal fixtures. For each refusal fixture, assert JSON stdout and empty stderr under `--json`, human stderr and empty stdout without it, exit 1, schema validity, and byte-identical state (AC-0007, AC-0008, AC-0012, AC-0015).
- Explicitly cover absent/non-directory spec paths, unreadable or invalid state, unsupported state schema, no schedule, malformed `schedule_waves`, malformed `completed_task_ids`, malformed `current_wave_index`, missing plan, unreadable/illegal-status plan, stale hash, out-of-range wave, completed-task subtraction, and fully completed/empty remaining wave (AC-0002, AC-0007, AC-0012).
- Validate the schema itself, every emitted payload fixture, and negative mutants for unknown code/field, invalid/overlong task IDs, over-limit arrays, a one-member `cohort`, missing `admission_pending`, `parallel` disposition, and pair disposition (AC-0009, AC-0011).
- Pin the exact pre-change source slices for `cmd_dispatch_decision` and its parser, and assert the new handler's reachable call graph excludes `dispatch_decision`, `wave_is_disjoint`, cohort writers, worktree functions, and merge-tree execution (AC-0009, AC-0010).

**Approach:**

- Keep verdict construction deterministic and side-effect-free behind the CLI handler. Reuse `parse_touches_by_task`, `globs_overlap`, and `_DANGER_PATH_RE`; do not add a parallel predicate family.
- Route refusals through one renderer that receives a code and guard detail. It writes JSON only when `args.json` is true and delegates the human form to `stop()`.

**Done when:** the named touched test module passes, every emitted payload validates against the schema, and the CLI/state-byte assertions cover every success and refusal class.

### T2: Source-edited mutants prove the new guards and safety rails are live

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, docs/specs/loop-cohort-wave-decision/notes/verification-ledger.md

**Tests:**

- `no stub (goal-based mutation proof)` — edit out each new pre-index state-shape guard, the task-ID guard, the 64-task bound, the completed-task subtraction, `admission_pending`, and the read-only/no-writer rail one at a time; a named targeted test must fail for each mutant, then pass after restoring the original bytes by editing (AC-0001, AC-0002, AC-0007, AC-0009, AC-0012, AC-0015).
- Edit the overlap walk to continue past its first admitted collision; the named short-circuit test must fail, then pass after edit-back (AC-0005).
- Edit a pair row to add task disposition; schema and payload-shape tests must fail, then pass after edit-back (AC-0003, AC-0011).

**Approach:**

- Follow `work-loop/references/mutation-proof.md`; never use checkout, reset, or stash. Record each exact edit, red command and failure, restoration edit, and green command in the verification ledger.

**Done when:** every new guard or rail has a recorded red-on-edit and green-on-restoration result, with the source restored byte-for-byte.

### T3: JSON refusal detail is bounded and public-safe

**Depends on:** T1, T2

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py, contracts/jsonschema/loop-cohort-wave-decision.schema.json, docs/specs/loop-cohort-wave-decision/notes/verification-ledger.md

**Tests:**

- **TDD** — materialize the exact stub below in `test_loop_cohort_schedule.py`; it proves caller-controlled path text cannot cross the JSON boundary (`stub: true`). Then parameterize all nine refusal codes and assert each JSON `detail` equals its fixed code-specific public message, is at most 96 characters, and contains no raw fixture path or injected diagnostic marker; assert the same fixtures retain the richer diagnostic through the non-JSON stderr path (AC-0007, AC-0008, AC-0017).

```python
def test_wave_decision_json_refusal_detail_is_public_safe(git_repo):
    marker = "DO-NOT-ECHO"
    outside = git_repo.parent / marker

    result = _run_lc("wave-decision", str(outside), "--json", cwd=git_repo)

    assert result.returncode == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload == {
        "payload_version": 1,
        "refusal": "state-unreadable",
        "detail": "cohort state could not be read",
    }
    assert marker not in result.stdout
```
- Validate every JSON refusal against the schema and reject an otherwise-valid refusal whose `detail` is 97 characters (AC-0011, AC-0017).
- Mutation proof: edit the JSON renderer to emit its raw diagnostic argument, show the named public-detail test fails, restore by editing back, and record red/green commands plus byte restoration in the verification ledger (AC-0017).

**Approach:**

- Add one closed mapping beside the existing wave-decision constants. `_emit_wave_refusal` uses that mapping only for JSON and keeps its existing raw `detail` argument for `stop()` on the human path. Keep the nine refusal codes, envelope fields, and payload version unchanged.

**Done when:** all nine JSON refusal details are fixed, bounded, schema-valid, free of caller-controlled diagnostics, and mutation-proven while human refusals remain useful.

### T4: Post-review repairs and published surfaces agree

**Depends on:** T1, T2, T3

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/.apm/skills/work-loop/references/supervisor-mode.md, packs/core/.apm/skills/work-loop/evals/evals.json, packs/core/tests/skills/work-loop/test_loop_cohort_schedule.py, contracts/jsonschema/loop-cohort-wave-decision.schema.json, contracts/README.md, tests/roster/test_loop_cohort_wave_decision_contract.py, .github/workflows/build-check.yml, tools/lint-ci-parity.py, .workspace-prune-protected.toml, docs/architecture/loop-parallelism.md, docs/specs/loop-cohort-wave-decision/notes/verification-ledger.md, packs/core/seeds/docs/product/changelog.md, docs/product/changelog.md, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, .claude/skills/work-loop/**, .agents/skills/work-loop/**, .claude-plugin/marketplace.json

**Tests:**

- `no stub (goal-based documentation and release checks)` — content assertions distinguish `wave-decision` from `dispatch-decision`, preserve ADR-0005 D4, state `admission_pending`, document the fixed public-safe JSON refusal detail and richer human diagnostic, name both `_DANGER_PATH_RE` consumers, and keep ADR-0061 D5 deferred (AC-0013, AC-0017).
- Extend the pack CLI suite with missing/empty `run_id`, duplicate unfinished task IDs, non-directory spec path, invalid state JSON, and unreadable state fixtures. Assert both channels, fixed public-safe details, and byte-identical state where a state file exists (AC-0001, AC-0007, AC-0008, AC-0012, AC-0015, AC-0017).
- Add boundary fixtures for 64/65 globs on one task, 256/257 total globs across a selected wave, and 256/257-character globs. Assert accepted boundaries, `plan-status-illegal` refusals before classification, both channels, and byte-identical state (AC-0007, AC-0008, AC-0012, AC-0018).
- Source-edit each new `run_id`, duplicate-ID, per-task glob-count, per-wave glob-count, and glob-length guard so its named test fails, then restore by editing back and record red/green commands plus identical source digests in the verification ledger (AC-0015, AC-0018).
- Remove repository-schema reads from the pack-local suite. Add a repository-owned roster test for emitted representative payloads, all refusal envelopes, negative schema mutants, per-task touch `maxItems: 64`, glob `maxLength: 256`, and `x-max-total-touches: 256`; wire its named build-check step, `STEP_DISPOSITION`, and prune protection without running `tests/roster/` locally (AC-0011, AC-0014, AC-0018).
- Run `python3 tools/test-lint-pack-test-boundary.py` after relocating schema assertions and record its passing exit status; this is separate from the prohibited local roster run (AC-0014).
- Correct the architecture preamble so it names § 4 as implemented and leaves only § 3 planned (AC-0013).
- Parse the eval JSON and assert one case teaches that `parallel-capable` is pending, pair rows never admit tasks, and a refusal has no admission field (AC-0014).
- Immediately before publishing, fetch `origin`, derive the next unclaimed minor version from the fresh base, update `pack.toml`, plugin JSON, and the topmost core heading in both the pack-source changelog seed and the separately maintained repository `docs/product/changelog.md`, then assert equality across all four surfaces (AC-0014).
- Run `FORCE=1 make build-self` mid-change and trust its three-copy parity report; rerun without `FORCE` for the finish gate and verify no source/projection drift (AC-0014).
- Invoke the built verb on a temporary real cohort fixture and record JSON stdout, empty stderr, exit 0, and equal before/after state hashes (AC-0001, AC-0012, AC-0014).

**Approach:**

- Keep T1–T3 sections and their evidence pinned. T4 is the only unfinished task and owns every post-review correction.
- Parse effective touches once for the selected wave, validate the three resource bounds, then pass the validated map into decision construction so the guard cannot be bypassed by reparsing.
- Keep behavioral CLI assertions pack-local and move only repository contract ownership into the roster surface required by `tests/AGENTS.md`.

**Done when:** every sustained post-gates finding is repaired, every new guard is mutation-proven, the durable outputs agree, the generated copies are current, local gates and targeted non-roster suites pass, CI wiring owns the roster contract test, and the real built-verb smoke is recorded.

## Rollout

This is a reversible core-pack minor release with no state migration, feature
flag, infrastructure, external service, or mixed-version write concern. Rolling
back the code and pack version removes the read-only verb; existing cohort state
and every shipped execution path remain valid.

## Risks

- **Refusal misclassification.** Mapping by diagnostic prose would make codes drift when wording changes. The design maps by the deciding guard or precondition and keeps the two deliberate folds explicit.
- **False greenlight.** A word or field shared with the post-write gate could be read as admission. Closed schema enums, source pins, and guidance keep the vocabularies disjoint.
- **Read-only regression.** A helper chosen for convenience could take the cohort lock or write state. Byte equality on all paths and the no-writer source assertion make that observable.
- **Output and comparison amplification.** Pair rows grow quadratically with wave width and touch comparisons multiply across task pairs. The limits and measured comparison ceiling owned by spec AC-0018 and `loop-parallelism.md` § 4 refuse excessive input before classification.
- **Version collision.** Another branch can claim the same minor version after this draft. T4 derives the release bytes from a fresh `origin` immediately before publishing rather than pinning a number now.

## Changelog

<!-- Approvals are added by the work-loop G-plan sequence. -->

- 2026-09-29 — Spec approved (scope) by eugenelim.
- 2026-09-29 — Plan approved (build strategy) by eugenelim.
- 2026-09-29 — Owner-approved contract amendment replaced the nonexistent `packs/core/CHANGELOG.md` target with `packs/core/seeds/docs/product/changelog.md` and its generated `docs/product/changelog.md` projection; T1 and T2 evidence remains complete.
- 2026-09-29 — Owner-approved secure-design amendment added a bounded public-safe JSON refusal detail contract as T3 and moved release/projection work to T4; T1 and T2 evidence remains complete.
- 2026-09-29 — Spec re-approved (amended scope) by eugenelim.
- 2026-09-29 — Plan re-approved (amended build strategy) by eugenelim.
- 2026-09-29 — Owner-approved final contract amendment records the pack changelog seed and repository product changelog as separately maintained T4 outputs; T1–T3 evidence remains complete.
- 2026-09-29 — Spec re-approved (final changelog-ownership scope) by eugenelim.
- 2026-09-29 — Plan re-approved (final T4 build strategy) by eugenelim.
- 2026-09-29 — Owner-approved resource amendment adds the effective-touch budgets owned by spec AC-0018 and `loop-parallelism.md` § 4; T1–T3 evidence remains complete and T4 owns the post-review repairs.
- 2026-09-29 — Spec re-approved (resource-bound repair scope) by eugenelim.
- 2026-09-29 — Plan re-approved (resource-bound T4 repair strategy) by eugenelim.
