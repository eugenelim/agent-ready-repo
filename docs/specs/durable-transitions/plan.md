# Plan: Durable cohort effects for engine transitions

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `docs/architecture/loop-parallelism.md` § 1 (the design), ADR-0125 D1-D3 (authority and closed registry), `docs/architecture/loop-infrastructure.md` §§ 3-6 (current writers, locks, crash windows), and `packs/core/.apm/skills/work-loop/references/session-resumption.md` (the manual protocol being removed). Analogous production implementations: `begin_contract_amendment`, `apply_contract_amendment`, and `contract_amendment_replay_status` in `loop-cohort.py`; `_recover_pending` and the transition commit in `loop-engine.py`; review operation-id replay in `loop-cohort.py`. Corresponding tests: `test_contract_amendment_wave4.py`, `test_loop_engine.py`, and targeted cases in `test_loop_concurrency.py`. Named deviation: the prompt names `packs/core/CHANGELOG.md`, which does not exist; the repository-owned changelog source is `packs/core/seeds/docs/product/changelog.md` and its projection is `docs/product/changelog.md`.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> execution observations go in `notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.

## Approach

Build in five dependency-ordered layers, each ending with a working repository:
the cohort representation and status predicate; lock-held effect application;
engine integration; crash and mutation proof; then operating docs, projections,
and release surfaces. The representation layer first replaces the old amendment
keys and separates cohort schema version 2 from engine schema version 1. The
effect layer refactors existing cohort verbs into lock-held state mutators and
puts exactly five adapters behind one registry. The engine layer prepares the
marker, performs the unlocked classification, delegates the locked recheck and
effect commit to `loop-cohort.py`, then commits engine state last.

The pre-review disconfirming probe searched the current cohort module for
callable state-mutator seams. It found amendment helpers, but `wave advance`,
`record-attempt`, and `review record` still keep their mutations inline in the
locked CLI handlers. T2 therefore owns extracting those pure mutators before
the registry adapters exist; it does not assume reusable helpers that the tree
does not contain.

This is expected to exceed 2,000 reviewable lines once table-driven crash cases,
schema cases, operating guidance, and projections are counted. Review is shaped
as three units: representation/effects (T1-T2), engine/recovery proof (T3-T4),
and published workflow/release record (T5-T6). Each unit runs its targeted tests
and receives adversarial review before the next unit; the final unit receives
the full diff-level adversarial and quality passes. The task graph is serial on
purpose because each layer changes the contract consumed by the next.

## Constraints

- ADR-0125 D1 authorizes the engine to apply a registered cohort effect as part of a transition.
- ADR-0125 D2 fixes the registry at five events. A sixth event is not an implementation choice.
- ADR-0125 D3 keeps `loop-cohort.py` as writer of record. `loop-engine.py` may call the module but may not write cohort `state.json` itself.
- ADR-0061 D5 remains in force. This delivery does not enable concurrent dispatch.
- `loop-parallelism.md` § 1 is the mechanism. In particular, status reads history after marker clearance, only amendment pins an artifact, and retention truncates oldest entries rather than refusing at 20.
- Cohort-state schema becomes 2 in `loop-cohort.py`, its initial asset, and `_loop_guards.py`. `loop-engine.py` keeps its engine-state `SCHEMA_VERSION = 1`; its cohort reads are validated by the guard/cohort modules.
- Existing wave-exit R2 and R4 tolerances remain pass. Avoid changing `_wave_exit_verdict`; if it must move, run the 35,728-state partition walker before and after.
- `.apm` is source. `make build-self` regenerates `.claude/` and `.agents/`; a source-only change without parity is incomplete.
- No new dependency, top-level directory, migration compatibility layer, per-event history, or formal `contracts/` artifact is needed. The existing scripts, state reference, and tests own these internal CLI/state boundaries.

## Construction tests

**Integration tests:**

- A table-driven engine test covers every registry row at both crash cuts: after marker persistence/before effect, and after cohort effect/history persistence/before engine-state persistence. Each replay asserts an effect count of exactly one, one matching history entry, a cleared marker, and one engine sequence advance.
- A closed-set test derives the FSM event set from the engine table, asserts the five registry members, and proves every derived non-member skips the cohort-effect path and leaves cohort state byte-identical.
- Mixed-schema CLI tests cover old cohort/new engine and new cohort/old engine refusal without mutation, while targeted guard tests keep R2 and R4 passing.
- A real temporary-spec smoke uses the built source for one registered transition and one interrupted replay; it records commands and outcomes in `notes/verification-ledger.md`.

**Mutation proof:** Every new guard gets one source edit made with `apply_patch`, one targeted test that goes red, and an inverse `apply_patch` restoring the exact source before the next probe. The ledger records the guard, edit, test node, failing assertion, and restored green run. The minimum set is: history-not-marker status; last-entry-only applied; closed registry; locked reclassification; `loop-cohort.py` writer rail; cohort/engine schema split; oldest-first retention with newest preserved; and review operation id equal to transition id. No checkout, reset, or stash is used.

**Manual verification:** One CLI smoke after `make build-self`; no browser or external service is involved.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Architecture: `loop-parallelism.md`, `loop-infrastructure.md` | T5 | text names the shipped marker, registry, lock order, schema choice, and recovery | close-work finds no stale planned/manual statement for § 1 |
| Serialized-state contract: `state-schema.md` | T1 | schema/status/retention tests plus updated field table in the representation review unit | emitted asset and status JSON match the reference |
| Maintainer/recovery flow: `SKILL.md`, `full-mode-engine.md`, `session-resumption.md` | T3 | source-shape search and engine E2E in the engine-integration review unit | no separate registered cohort mutation remains in ordinary or recovery flow |
| Release history and user promise: seed changelog and two version manifests | T6 | version-parity assertion and build parity | fresh remote-main comparison still yields exactly one patch |
| Reusable learning: `evals.json` | T5 | JSON parse plus content review | non-cosmetic change has an honest interruption/replay record |
| Verification record: `notes/verification-ledger.md` | T1-T6 | red/green, crash, mutation, review, and gate receipts | every AC maps to current evidence and no failed probe is left unexplained |

## Design (LLD)

### Design decisions

Owned by: T1-T3

- **One history replaces two amendment keys.** `transition_history` is the only replay ledger and `pending_transition` is the only marker. `cmd_status` and the generalized replay status read those fields; no compatibility alias survives the schema reset.
- **Only the cohort version moves.** The duplicated name does not imply one format. `loop-cohort.py` and `_loop_guards.py` consume cohort `state.json` and move to 2; `loop-engine.py` owns `engine-state.json` and stays at 1. Tests name each file, so a future blanket bump fails.
- **The marker and effect are two cohort commits.** `prepare_transition` persists or validates the marker under the cohort lock, then returns. `apply_transition_effect` later reacquires that lock, reclassifies from history, applies when absent, appends history, and clears the marker atomically. This creates the intentional crash cut the marker protects.
- **The same key spans both idempotency layers.** Review adapters pass `transition_id` as `operation_id`. This closes the only reason `reviewers-clean` needed a human replay authorization gate.
- **A space budget replaces a count budget.** Append the newest entry, serialize the whole candidate with compact separators and UTF-8, then discard oldest history entries until the candidate is at most 1,048,576 bytes. Never discard the newest; if it cannot fit alone, refuse the unchanged input state.

### Data & schema

Owned by: T1, T2

`pending_transition` is either `null` or an object containing
`transition_id`, `pre_transition_sequence`, `event`, canonical `args`, and
`opened_at`. `transition_history` is an ordered list whose entries repeat the
identity fields and carry the effect's audit snapshot. Only the
`contract-amendment` entry contains completed-task section hashes and evidence
needed for the `plan.md` pin. The last entry is the applied baseline; older
entries are audit history only and may be truncated.

The initial state asset removes `amendment_pending` and `amendment_history`, adds
the two unified fields, and stamps cohort schema 2. `loop-engine init` continues
to stamp engine schema 1. Existing run files are neither read through an alias
nor rewritten; the mismatch refusal directs the authorized reset pair.

### Interfaces & contracts

Owned by: T1-T3

- `loop-cohort.py` exports `transition_replay_status(spec_dir, *, transition_id, pre_transition_sequence, event, args) -> str`, `prepare_transition(...) -> str`, and `apply_transition_effect(...) -> str`. The first is read-only; the latter two own their cohort locks and writes.
- `loop-cohort.py` owns `_TRANSITION_EFFECTS`, a literal mapping with five keys. Each adapter delegates to an existing state mutator or to amendment logic refactored from the shipped implementation.
- `loop-engine transition` accepts the effect payload at the same invocation that fires the event. `wave-passed` keeps `--wave-index`; amendment keeps owner/reason/evidence options; review events accept the existing `review record` evidence forms and fingerprint options. `gates-failed` needs no new payload. Invalid event/option combinations refuse before marker creation.
- Existing direct cohort verbs stay available for cohort maintenance and tests, but the work-loop controller no longer calls them as a second half of an engine transition. Their implementations share the same pure mutators as the registry adapters so validation does not fork.
- No recognized formal contract type in `contracts/` fits this run-local CLI/state format. The public grammar is pinned by parser and subprocess tests plus `state-schema.md`.

### Component / module decomposition

Owned by: T1-T3

- `loop-cohort.py`: schema-2 state ownership, transition identity validation, status, history retention, effect registry, lock-held effect dispatch, and existing direct cohort commands.
- `_loop_guards.py`: cohort schema expectation and unchanged guard semantics, including R2/R4 tolerances.
- `loop-engine.py`: event argument validation, canonical transition-id derivation, calls into the cohort module, and engine-last commit/outbox flow.
- `assets/state.json`: initial cohort representation.
- Tests: `test_contract_amendment_wave4.py` for status/retention/amendment pins, `test_loop_engine.py` for registry and engine replay, and targeted `test_loop_concurrency.py` nodes for lock/writer rails and real subprocess crash behavior.

### State & control flow

Owned by: T2, T3

```
loop-engine transition                         # engine lock already held
  validate event and effect payload
  compute transition_id from run_id + pre_sequence + event + canonical args
  loop-cohort.prepare_transition(...)         # cohort lock; marker durable
  transition_replay_status(...)               # unlocked read
  loop-cohort.apply_transition_effect(...)    # cohort lock
      reclassify from history
      applied  -> validate pin if amendment; clear matching marker if needed
      conflict -> refuse without mutation
      absent   -> invoke registry adapter; append retained history
      clear marker in same atomic state write
  build/write events.pending when required
  write engine-state.json                     # last durable state commit
  append events.jsonl and clear events.pending
```

The engine lock is outermost and the cohort lock is never held across a
subprocess. Events outside the registry skip every cohort transition call.
Recovery replays the same engine command and arguments; the marker preserves the
pre-transition key if engine state has already advanced, and history remains the
authority if the marker has already been cleared.

### Behavior & rules

Owned by: T1-T3

- `applied` consults only the last history entry. Amendment then re-reads `plan.md` through the managed reader and runs `validate_completed_task_sections`; the other four return applied from history alone.
- `conflict` is sticky for a different id at the same pre-transition sequence or a failed amendment pin. It never overwrites the marker or history.
- `absent` is based on history, not the marker. A matching marker with no matching history is the normal prepared-but-not-applied state.
- A prepare call is idempotent for byte-equivalent identity and args. A different marker for the same pre-transition sequence refuses.
- Canonical args use sorted-key compact JSON. File-backed review payloads are validated and reduced to bounded audit facts before marker persistence so replay does not depend on a temporary artifact disappearing between commits; amendment remains the sole artifact re-read for applied classification.

### Failure, edge cases & resilience

Owned by: T1-T4

- Crash before marker write: no cohort effect; ordinary retry prepares it.
- Crash after marker write: history says absent; retry applies once.
- Crash after effect/history write and marker clear: history says applied; retry skips the effect and finishes engine state.
- Crash after engine-state write: shipped `_recover_pending` finalizes the outbox; effect history already agrees.
- Schema mismatch, malformed marker/history, conflicting transition identity, missing effect payload, or oversized newest entry: refuse before mutation with one bounded diagnostic.
- A retention implementation that searches older entries for applied would make truncation unsafe. T1 pins last-entry-only status and T4 mutates it.
- `reviewers-clean` no longer waits for replay authorization only because `transition_id == operation_id`; a test breaks that equality and must make the replay proof fail.

### Quality attributes (NFRs)

Owned by: T3-T6

- Cohort state remains at or below 1,048,576 serialized bytes after every successful transition-effect commit.
- No effect path performs network I/O or an unbounded subprocess under either lock.
- The source and two projections remain byte-equivalent under the existing build parity check.
- Diagnostics remain bounded through existing CLI helpers; tests assert behavior rather than logging new state payloads.

### Dependencies & integration

Owned by: T3, T5

No new package or service. The engine already loads `loop-cohort.py` by path and
already holds engine state across the amendment call. The change expands that
existing boundary and removes the fingerprint exemption for amendment once all
five effects use the same lock-held protocol. The operating documents and eval
record are edited in `.apm`, then projected by the repository build.

## Tasks

### T1: Unified status, schema split, and retention are executable

**Depends on:** none

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/.apm/skills/work-loop/scripts/_loop_guards.py, packs/core/.apm/skills/work-loop/assets/state.json, packs/core/.apm/skills/work-loop/references/state-schema.md, packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py, packs/core/tests/skills/work-loop/test_loop_guards.py

**Tests:**

- AC-0001, AC-0002, AC-0005, AC-0006, AC-0013, and AC-0014: table-driven unit and CLI tests for history-based status, amendment pin drift, cleared markers, persisted sequence, >20 entries, truncation, and newest-alone refusal.
- AC-0011, AC-0012, and AC-0018: initial asset/schema tests plus old/new mixed-state refusal tests; existing R2/R4 nodes stay green and `state-schema.md` is updated in the same review unit.
- `test_applied_status_survives_marker_clear` (AC-0002) — `stub: true`; validation result recorded below.

```python
# STUB: AC-0002 — applied status survives marker clearance
import importlib.util
import json
import sys
from pathlib import Path

COHORT_PATH = (
    Path.cwd()
    / "packs/core/.apm/skills/work-loop/scripts/loop-cohort.py"
)


def _load_cohort():
    spec = importlib.util.spec_from_file_location("durable_t1_cohort", COHORT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_applied_status_survives_marker_clear(tmp_path: Path) -> None:
    cohort = _load_cohort()
    transition = {
        "transition_id": "transition-7",
        "pre_transition_sequence": 7,
        "event": "gates-failed",
        "args": {},
    }
    state = {
        "schema_version": 2,
        "run_id": "run-current",
        "pending_transition": None,
        "transition_history": [transition],
    }
    (tmp_path / "state.json").write_text(
        json.dumps(state) + "\n", encoding="utf-8"
    )

    assert cohort.transition_replay_status(
        tmp_path,
        transition_id=transition["transition_id"],
        pre_transition_sequence=7,
        event="gates-failed",
        args=transition["args"],
) == "applied"
```

**Stub validation:** disposable `python3 -m py_compile` passed; isolated pytest
failed at the intended missing `transition_replay_status` surface (2026-09-25;
three-stub run: 3 failed in 0.99s).

**Approach:** Generalize the shipped amendment status and serialization helpers in place. Remove the count refusal and old keys in the same layer so no test or status surface has two replay authorities.

**Done when:** the stub and all listed criteria are green, schema-1 cohort input refuses without mutation, `state-schema.md` agrees with the emitted schema-2 asset and status JSON, and a targeted suite covering the two touched test modules passes.

### T2: The closed registry applies all five effects under one cohort protocol

**Depends on:** T1

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py, packs/core/tests/skills/work-loop/test_loop_engine.py, packs/core/tests/skills/work-loop/test_loop_concurrency.py

**Tests:**

- AC-0003 and AC-0004: one parameterized case per registry member plus exhaustive non-member coverage derived from the FSM event set.
- AC-0009 and AC-0010 at the cohort boundary: prepare and apply take the cohort lock, apply reclassifies inside it, and source checks reject a direct engine state write or an open-ended dispatch.
- AC-0015: both review events store `operation_id == transition_id`; matching replay is a no-op.
- `test_transition_effect_registry_is_closed` (AC-0003) — `stub: true`; validation result recorded below.

```python
# STUB: AC-0003 — the transition effect registry is the closed five-event set
import importlib.util
import sys
from pathlib import Path

COHORT_PATH = (
    Path.cwd()
    / "packs/core/.apm/skills/work-loop/scripts/loop-cohort.py"
)


def _load_cohort():
    spec = importlib.util.spec_from_file_location("durable_t2_cohort", COHORT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_transition_effect_registry_is_closed() -> None:
    cohort = _load_cohort()
    assert set(cohort._TRANSITION_EFFECTS) == {
        "contract-amendment", "wave-passed", "gates-failed",
        "findings-remain", "reviewers-clean",
    }
```

**Stub validation:** disposable `python3 -m py_compile` passed; isolated pytest
failed at the intended missing `_TRANSITION_EFFECTS` surface (2026-09-25;
single-stub revalidation after shaping repair: 1 failed in 0.76s).

**Approach:** Extract pure state mutators from the existing locked command implementations, then have both direct commands and registry adapters call them. Keep lock ownership at the public transition-effect boundary to prevent engine/cohort lock code from forking.

**Done when:** every registry member's observable effect is green, every non-member preserves cohort bytes, the review replay uses one key, and the writer/lock source checks pass.

### T3: Engine transitions own the complete cohort effect and commit engine state last

**Depends on:** T2

**Touches:** packs/core/.apm/skills/work-loop/scripts/loop-engine.py, packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/references/full-mode-engine.md, packs/core/.apm/skills/work-loop/references/session-resumption.md, packs/core/tests/skills/work-loop/test_loop_engine.py, packs/core/tests/skills/work-loop/test_contract_amendment_wave4.py, packs/core/tests/skills/work-loop/test_loop_concurrency.py

**Tests:**

- AC-0003, AC-0004, AC-0006, AC-0009, AC-0010, and AC-0015 at the engine CLI: validate/canonicalize payload, prepare, classify, apply, then write engine state; unregistered events do not call the cohort protocol.
- AC-0017: the source work-loop and resumption flows issue no separate registered cohort mutation after the engine transition; projection parity remains T5's build obligation.
- Amendment regression: plan pinning and both recovery directions stay green under the generalized path.
- Review CLI cases cover fingerprints, each clean-report form, all-skipped, adjudication, retry-cap override, and invalid cross-event arguments before marker persistence.
- `test_review_transition_accepts_effect_payload` (AC-0015) — `stub: true`; validation result recorded below.

```python
# STUB: AC-0015 — review evidence is part of the engine transition payload
import importlib.util
import sys
from pathlib import Path

ENGINE_PATH = (
    Path.cwd()
    / "packs/core/.apm/skills/work-loop/scripts/loop-engine.py"
)


def _load_engine():
    spec = importlib.util.spec_from_file_location("durable_t3_engine", ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_review_transition_accepts_effect_payload() -> None:
    engine = _load_engine()
    args = engine.build_parser().parse_args(
        ["transition", "docs/specs/example", "reviewers-clean", "--all-skipped"]
    )
    assert args.all_skipped is True
```

**Stub validation:** disposable `python3 -m py_compile` passed; isolated pytest
failed at the intended absent `--all-skipped` transition option (2026-09-25;
three-stub run: 3 failed in 0.99s).

**Approach:** Replace the amendment-only branches with one registry-aware path. Preserve the existing outbox commit path and its single engine-state write; the generalized effect completes before that path begins.

**Done when:** registered CLI transitions and their source operating/resumption guidance need no follow-up cohort command, all unregistered transitions retain prior cohort bytes, and the ordered stub plus targeted engine/amendment/concurrency nodes pass.

### T4: Every crash window and every new guard has falsifiable proof

**Depends on:** T3

**Touches:** packs/core/tests/skills/work-loop/test_loop_engine.py, packs/core/tests/skills/work-loop/test_loop_concurrency.py, docs/specs/durable-transitions/notes/verification-ledger.md

**Tests:**

- AC-0007 and AC-0008: ten crash/replay cases, two cuts for each registry member, with effect-specific counters or state facts bound to exactly one.
- AC-0010: a static check rejects direct engine writes/unlinks of cohort `state.json` and requires the five-key registry owner in `loop-cohort.py`.
- Construction-test mutation set: eight source edits, one red targeted node each, then exact inverse edits and restored green nodes.
- `no stub (implementation-discovered)`: the existing subprocess harness has no crash-injection seam at either new cut. Discovery predicate: after T3, identify the narrowest callable or environment-controlled hook reached immediately after marker persistence and immediately after the cohort commit, without adding a production-only test branch. Constraint: both cuts must terminate a real child process and the same public CLI command must perform the replay. Proof obligation: one parameterized pytest family covers all five events × both cuts and binds effect/history counts to one. Verification mode: TDD exercised end to end with targeted real-subprocess nodes.

**Approach:** Reuse the real-subprocess harness only for the cuts that need process death; keep table setup and effect counters in `test_loop_engine.py` so `test_loop_concurrency.py` remains targeted. Run only named concurrency nodes locally.

**Done when:** all ten crash cases are green, each of the eight mutation edits has a recorded red result and restored green result, and no source mutation remains in `git diff`.

### T5: The published work-loop no longer carries a human effect-replay table

**Depends on:** T4

**Touches:** packs/core/.apm/skills/work-loop/evals/evals.json, docs/architecture/loop-parallelism.md, docs/architecture/loop-infrastructure.md, packs/core/tests/skills/work-loop/, .claude/, .agents/

**Tests:**

- AC-0016 and AC-0017: targeted verdict regressions plus a source/projection search proving the ordinary and resumption flows issue no second effect command.
- AC-0019: `env FORCE=1 make build-self` reports three-copy parity; relevant pack construction tests pass.
- Goal-based: architecture references reconcile the fields, registry, schema split, retention, and reset boundary already shipped with their living state/recovery references in T1 and T3.
- Goal-based: `evals.json` parses and contains one honest crash/replay case without being counted as execution evidence.
- `no stub (goal-based)`: the build parity command and bounded source/projection searches directly verify this task's outputs.

**Approach:** Reconcile the architecture record and eval after T1/T3 have updated the living schema and recovery references in their own review units, then regenerate all projections from the already-updated `.apm` source.

**Done when:** all durable-output closeout conditions owned by T5 are met, parity is clean, and the projections preserve T3's source rule that no registered event has a documented second cohort mutation.

### T6: Release surfaces and the complete verification record agree

**Depends on:** T5

**Touches:** packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, packs/core/seeds/docs/product/changelog.md, docs/product/changelog.md, docs/specs/durable-transitions/spec.md, docs/specs/durable-transitions/plan.md, docs/specs/durable-transitions/notes/verification-ledger.md

**Tests:**

- Goal-based: compare current GitHub `main` through the one approved read-only API probe immediately before editing the version; choose exactly one patch above that merge-base and assert both manifests plus the topmost seed/projection core heading agree.
- Local gate: `make lint-ruff lint-mypy` and only the touched pytest suites; never `tests/roster/` or `make ci`.
- Goal-based: `lint-spec-status.py --root .`, pack tests required by the touched construction path, and final `make build-self` parity.
- Manual E2E: built-source temporary run and interrupted replay recorded with exact command, result, and cleanup limitation if the managed profile blocks directory removal after assertions.
- `no stub (goal-based/manual QA)`: existing gate commands and the recorded real CLI gesture are the verification surfaces.

**Approach:** Keep the version literal out of the approved plan. The environment forbids ref-writing fetches, so use the already-probed authenticated read-only GitHub API to compare remote `main`; do not claim a fetch occurred. Edit the seed changelog, regenerate its projection, and record the repo/prompt path discrepancy in the ledger.

**Done when:** every AC has current evidence in the ledger, the local gate is green or carries only the one pre-existing cleanup skip confirmed against HEAD, version/projection parity is clean, and the spec/plan lifecycle fields reflect the completed implementation.

## Rollout

One pack release with no feature flag. Cohort schema 2 and engine schema 1 ship
together. An existing run or a rollback across the boundary refuses and requires
the already-authorized destructive pair `loop-cohort reset` then `loop-engine
reset`; retry/review progress is discarded while `spec.md` and `plan.md` remain.
There is no in-place migration, backfill, external infrastructure, or partial
deployment sequence.

## Risks

- **A second replay authority survives.** Removing only one old amendment key or leaving a manual cohort call in guidance can double-apply an effect. T1 removes the keys together and T5 searches source plus projections.
- **The marker is cleared before status reads it.** That launders the core crash window. AC-0002 and its mutation probe require applied status with `pending_transition: null`.
- **An older history match is accepted.** That breaks retention's safety proof. AC-0014 and its mutation probe force the last-entry rule.
- **Review audit payload disappears between prepare and replay.** The marker stores bounded canonical audit facts, not only a temporary path; amendment is the deliberate exception because it re-pins `plan.md`.
- **The engine gains an accidental direct writer.** AST/source checks plus ADR-0125 D3 review pin the module boundary.
- **The cohort-only version bump invalidates engine state.** Tests assert both stamped files and their separate constants, not one vague schema version.
- **The task size hides partial integration.** The five serial layers and three review units each end with runnable targeted tests and no knowingly broken intermediate tree.

## Changelog

- 2026-09-25: spec approved by eugenelim
- 2026-09-25: plan approved by eugenelim
