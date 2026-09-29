# Plan: Plan Evolution Experiments

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `packages/agentbundle/agentbundle/commands/pack_evals.py` and `tools/test-run-pack-evals.py` for bounded agent invocation and error capture; `tools/bench-workspace-status.py` for structured benchmark output; `docs/product/research/work-loop-review-economics-spike.md`, `docs/product/research/work-loop-focused-re-review-spike.md`, and `docs/product/research/work-loop-repair-correctness-spike.md` for prior measures; `.agents/skills/work-loop/scripts/_loop_guards.py`, `loop-cohort.py`, and `loop-engine.py` for current lock and amendment mechanics. Deviation: there is no shipped Codex build executor or JSONL schema, so this plan adds a research-only adapter instead of extending `pack_evals.py`.
- **Review shape:** MIXED — deterministic harness invariants plus semantic interpretation of observed model runs.
- **TDD stubs:** completed legacy T1 and completed collaboration task T6 each
  contain one exact Python/pytest red stub. Other active tasks use goal-based or
  observed-behavior checks and record `no stub (mode)`.

> **Plan contract:** completed T1–T12 sections and every collected run manifest
> remain pinned. T13 is preserved as a terminal methodological negative result.
> The natural-work inclusion, classification, stopping, and release rules are
> pinned after approval. Delivery observations live in
> `notes/verification-ledger.md`.

## Current amendment strategy

Preserve completed T1–T12 evidence and every historical run manifest exactly.
T13 has already consumed 95 of its 96 permitted starts. Close it without an
eighth review round, retain its raw artifacts and retired apparatus, and publish
only the methodological conclusion that the synthetic design cannot support a
work-loop effectiveness claim.

T14 reuses the existing real-corpus methodology, four Tier-A histories, two
aggregate cases, the 15-round occasioning loop, and the repository-wide survey.
It freezes a small event table and reconstructs the baseline scorecard before
any prospective threshold is chosen. It starts no model process and adds no
grader or self-certifying control.

T15 defines and, only after a separate release approval, observes a bounded
cohort of consecutive eligible real work-loop cases. The normal delivery loop
stops after sustained blocking consequences close. One independent cold
full-document audit then runs on the exact stopped revision as a shadow
measurement; advisory prose does not reopen the loop. Models are recorded as
case attributes, not assigned as treatments.

### Current constraints

- Keep existing `results.json`, `evidence-index.json`, `wave-1.json`, gate memos,
  retrospective review-churn records, T13 raw artifacts, and the T13 retirement
  record byte-preserved.
- Do not run Sonnet, Opus, the synthetic holdout, another T13 repair/review
  round, or any replacement seeded-defect cell.
- Treat the existing real review histories as the primary baseline. Preserve
  original finding text and dispositions; add only a normalized event table
  with source citations and explicit missingness.
- Define durable blockers from stable requirements, executable failures,
  protected risks, and new external evidence. Do not infer usefulness from raw
  severity, prose length, or a reviewer's confidence.
- Count a repair-origin blocker only when the pre-repair state lacked it and
  the repair caused the post-repair state.
- Count a prose churn event only when unchanged accepted text is blocked without
  a new requirement, executable failure, protected risk, or external evidence.
- Keep retrospective, T13 synthetic, and prospective observations separate.
  Never pool their rows or convert a T13 grader score into natural-work quality.
- Admit prospective cases consecutively under the frozen rule. Record every
  exclusion and missing field; do not select cases by outcome or model.
- Bind the exact stopped revision before the shadow audit. Only independently
  adjudicated protected blockers count as escapes; advisory prose stays residue.
- Record requested and resolved models, tokens, wall time, and session identity
  only when observed. Never estimate missing historical telemetry.
- Require a separate reviewed release record and owner approval before any
  prospective process starts. That record owns the minimum cohort, observation
  window, model policy, thresholds, and process budget.
- Add no new orchestration layer, hidden grader, mutation registry, promotion
  gate, or self-consistency claim. Use a small versioned event table and direct
  arithmetic.

### Current construction tests

Goal-based checks validate the frozen inclusion table, source citations,
finding lineage, stopped-revision digest, evidence-class separation, and direct
scorecard arithmetic. Manual review classifies durable blockers, protected
escapes, repair origin, and prose churn. Observed checks use the real historical
review trajectories and, only after a separate release approval, consecutive
real work-loop cases. No construction test claims that its own pass proves
measurement validity.

### Current durable-output map

| Output | Tasks | Completion evidence |
| --- | --- | --- |
| Collaboration adapter, schemas, and tests | T6 | Targeted tests plus Ruff and mypy |
| Provider-labelled design and task packages | T6–T7 | Frozen digest, exact allocation, seven resolved recipes, eight non-executed code calibrations |
| Run 0 receipts and collection memos | T8 | Immutable failed Run 0a plus eight fresh terminal Run 0b subjects and a passing replacement gate |
| Run 0b standalone recovery report | T8 | `codex-collaboration-run-0b-report.md` reproduces the replacement decision and gates without reading this spec or plan |
| Run 1 evidence | T9 | 54 trajectories, up to 12 batched adjudicator starts, terminal accounting, finding registry reconciliation |
| Runs 2–5 evidence | T10 | 18 plan authors and 90 terminal construction responses |
| Run 6 evidence | T11 | 48 paired planner-constructor trajectories and 96 terminal starts |
| Run 7 evidence | T12 | 36 copied-snapshot review/repair trajectories, up to 12 batched adjudicator starts, repair lineage |
| T13 methodological closeout | T13 | Preserve 95 terminal starts and seven review rounds; record why the synthetic block cannot answer natural effectiveness |
| Natural-history baseline | T14 | Frozen event definitions, source-bound recode, complete multi-measure baseline, zero model starts |
| Prospective natural-work protocol and cohort | T15 | Reviewed release record first; then consecutive cases, exact stopped revisions, one shadow audit each, and a bounded report |

### Current design

`tools/plan_evolution_workbench/causal_runner.py` is a pure-standard-library
entry point as required by `tools/AGENTS.md`. It owns a new design schema,
ordinal ledger, bounded JSON/archive/path handling, snapshot preparation,
grading, and atomic receipts. It does not import repository packages or the
legacy `runner.py`; matching safety invariants are covered by construction
tests rather than a runtime dependency. Its CLI surface is:

```text
python3 tools/plan_evolution_workbench/causal_runner.py validate-design --design <path>
python3 tools/plan_evolution_workbench/causal_runner.py compile-assignments --design <path> --run-dir <path>
python3 tools/plan_evolution_workbench/causal_runner.py prepare-slot --run-dir <path> --slot <id>
python3 tools/plan_evolution_workbench/causal_runner.py record-launch --run-dir <path> --slot <id> --agent-id <id>
python3 tools/plan_evolution_workbench/causal_runner.py ingest-terminal --run-dir <path> --slot <id> --report <path>
python3 tools/plan_evolution_workbench/causal_runner.py grade-slot --run-dir <path> --slot <id>
python3 tools/plan_evolution_workbench/causal_runner.py summarize --run-dir <path> --output <path>
```

The document-only branch uses this surface only for deterministic assignment,
ordinal, receipt, and bounded-summary records. It does not call candidate
preparation or `grade-slot`; static document grading is performed by the
controller against frozen text/JSON registries without subprocess execution.

Each task package contains a neutral task brief, ordered acceptance atoms,
permitted and prohibited paths, baseline digest, visible regression commands,
complexity and provenance, treatment-rendering atoms, hidden-oracle asset
manifest, and leakage-audit receipt. Reference implementation facts are absent.

Assignments are deterministically randomized within task × replication blocks.
They carry stable slot ID, run set, blind arm, matched-control ID, phase graph,
requested model, candidate and artifact digests, and an opaque grader ID. Raw
events are append-only: `assignment-frozen`, `phase-reserved`,
`phase-launched`, `phase-terminal`, `candidate-frozen`, `grade-terminal`,
finding or repair events where applicable, and `slot-terminal`.

All disposable-root reads use a bounded open that canonicalizes and confines
the path, rejects symlinks, reparse points, junctions, multiple hard links,
special files, absolute or traversing archive members, path loops, and any
identity change while opening. No model-derived path reaches a command, gate,
grade, or report sink before that validation.

The grader freezes a candidate digest, copies the candidate to a separate root,
injects only declared hidden assets, refuses undeclared collisions, runs oracle
and regression commands, records bounded output, and proves the original digest
unchanged. Infrastructure errors stay distinct from candidate failures.

## Closed CLI foundation — approach

Build a standard-library workbench under `tools/plan_evolution_workbench/`, keep frozen method and result records under `docs/product/research/plan-evolution-experiments/`, and admit the frozen historical task frame. The first wave contains the calibration allocation plus breadth-first core work. Gates at the ordinals owned by the spec decide only integrity, harm, futility, and reserve allocation. Workers start cold except in declared continuity treatments. Append-only progress makes every slot resumable, hidden oracles grade builds after workers stop, and the standalone report preserves misses and inconclusive results while separating direct, retrospective, proxy, and source evidence.

## Closed CLI foundation — constraints

- Record the user's base-freshness waiver before implementation. It waives only that check.
- Provisional model classes are `gpt-5.6-luna` (`standard`) and `gpt-5.6-sol` (`frontier`). First assigned uses are capability probes and still spend their slots.
- Export baselines with `git archive`, then initialize independent one-commit repositories with no source refs, remotes, alternates, or object sharing.
- Keep hidden oracles and reference patches outside candidates; add hidden tests only after a worker stops.
- Create separate resolved roots for immutable inputs, candidates, hidden
  oracles, prompts, raw outputs, and evidence. Candidate sandboxes receive only
  their candidate root; controller-only siblings are neither readable nor
  writable from worker tools.
- Freeze and digest the design, measures, smallest effects worth acting on, and scoring declaration before slot 1. Changing them after results exist needs user approval and cannot rewrite earlier results.
- Count every started Codex process, including failures and continuity treatments. Enforce the spec-owned wave and study ceilings before spawn. Do not retry automatically or reassign failed slots.
- Do not install browser or other task dependencies. Exclude once and retain the reason.
- Launch candidates only after read, write, network, environment, credential,
  tool, delegation, approval-escalation, token, time, and process canaries prove
  the explicit sandbox profile. The worker tool environment is allowlisted;
  Codex service authentication remains runtime-owned and tool-inaccessible.
- The workbench performs no HTTP or DNS. Source material comes only from the
  frozen exact-URL inventory through a supported first-party retrieval tool or
  owner-supplied content outside the workbench. Retain only redacted prompts and
  bounded summaries in tracked evidence.
- No candidate patch enters the product tree, and no pilot result changes production workflow policy in this delivery.

## Closed CLI foundation — construction tests

**Integration tests:** a dry-run fixture exercises design loading, slot reservation, cold-worker command construction, environment allowlisting, redaction, strict schema rejection, normalized terminal capture, and resume without starting Codex. A reference-admission run exercises canonical path/archive confinement and hidden grading. Calibration canaries prove denied reads, writes, egress, credential access, delegation, and approval escalation before inference.

**Manual verification:** review prompt redactions, semantic-drift labels, evidence-class labels, and the final H1–H13 table. Confirm H11 is labeled an agent proxy.

## Closed CLI foundation — durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Reusable workbench under `tools/plan_evolution_workbench/` | legacy-L1–legacy-L8 | Red/green tests, isolation fixture, and dry run | Workbench tests pass independently of the delivery spec |
| Frozen methodology, wave designs, normalized results, and evidence index under `docs/product/research/plan-evolution-experiments/` | legacy-L1–legacy-L8 | Validated design, zero pending slots, source and artifact digests | Fresh validation and no dependency on the spec directory |
| Verification ledger | legacy-L1–legacy-L8 | Waiver, admissions, exclusions, model resolution, deviations, and gates | Every load-bearing observation cited |
| Research report | legacy-L9 | Complete self-contained H1–H13 matrix and source map | Independent review accepts arithmetic and labels without consulting this spec or plan |
| Corrected work-loop source plus projections | legacy-L9 | Canonical pack source agrees with current amendment code and lifecycle contract; self-host projections regenerate | Documentation and projection gates green |
| Core pack release coupling | legacy-L9 | Authored manifest versions, generated projections, and changelog agree | Pack/version/release gates green |
| Spec index row | legacy-L9 | Exact status and counts | Spec-status/index lint green |

## Closed CLI foundation — design (LLD)

### Design decisions

Non-routing historical owners in `codex-cli-r1`: legacy-L1, legacy-L2,
legacy-L4, legacy-L5, legacy-L6, legacy-L7

The process allocations and outer ceiling are owned solely by the spec's
`Study allocation` table, and cumulative wave boundaries are owned solely by
its reservation-release schedule. Calibration is excluded from inference. The
reserve may promote at most two hypotheses under a rule frozen before the first
result; unused slots stay unused.

The candidate universe is exactly the 12 tasks below, frozen before admission.
Table row order is the sole admission order. All 12 must be admitted for an
inferential result. An exclusion is preserved and never replaced after
admission starts. Every task has a baseline that fails a hidden oracle, a
reference that passes it, and complexity/uncertainty labels assigned before
outcomes are visible.

`Pre-build` means the contract predates implementation; `reconstructed` means the contract is sanitized from the reference commit and must remain a separate analysis stratum.

| Stratum | Task | Provenance | Baseline → reference | Primary oracle |
| --- | --- | --- | --- | --- |
| documentation/governance | Docs print cascade | pre-build | `464edb0` → `f147ef5` | `npm run test:e2e:gate --prefix web` |
| documentation/governance | Work-loop argless resume | pre-build | `0653042` → `d667e5f` | Structural activation/routing/projection predicates |
| documentation/governance | Decision-record ordinal uniqueness | pre-build | `7458ca8` → `3d1d041` | New-ADR/new-RFC ordinal and roster uniqueness tests |
| adapters/validation | Non-JSON SSO guard | reconstructed | `a3a8a06` → `cc8e989` | Jira non-JSON read-path suite |
| adapters/validation | Workspace routing invariants | pre-build | `8676488` → `4f5b978` | Workspace engine/CLI/MCP/projection suites |
| adapters/validation | Pack profiles | pre-build | `9a2f554` → `8e07cfa` | Profile manifest/lint/install fixture suites |
| filesystem/security | Atomic-write symlink hardening | reconstructed | `50bc138` → `2a2fff1` | `TestAtomicWriteSymlinkHardening` |
| filesystem/security | Core path confinement | reconstructed | `ed59272` → `4b41fe3` | Work-loop confinement/status/traceability suites |
| filesystem/security | Catalogue corporate trust store | reconstructed | `d1bc469` → `76f37de` | Trust unit, fallback, and local-TLS integration suites |
| multi-file refactor | Shared lint driver | reconstructed | `2f9451f` → `f9c4455` | The spec's evidence replay plus lint-harness tests |
| multi-file refactor | AgentBundle engine stragglers | reconstructed | `8c3494b` → `de23041` | Six focused AgentBundle/tool suites |
| multi-file refactor | Work-loop concurrency reliability | reconstructed | `ae99dd9` → `7071655` | State-lock, direct concurrency, cohort, and lock-bypass checks |

The manifest stores full 40-character commits and exact argv arrays. Reference observations, completed checkmarks, verification logs, reviewer outcomes, and finished construction tests are stripped from reconstructed inputs under task-specific rules before candidate exposure. H13 reports pre-build and reconstructed strata separately.

The core is a constrained mixed-level design with the process count derived from the spec's Core-experiment allocation. Each task receives six or seven independent planner→builder episodes under the frozen balancing algorithm. Two episodes are the H13 matched pair: their task facts, model allocation, lock semantics, handoff, probe, plan density, rule delivery, prompts, and limits are identical, and only separate versus unified artifact packaging changes. The remaining episodes cross full-plan versus semantic-decision lock; protected versus unprotected intent under a standard drift challenge; retained, trajectory, or prose handoff; standard/frontier planner; standard, standard-with-escalation, or frontier builder policy; probe on/off; compact/narrative plan; static/JIT rules; and artifact shape where the H13 match permits it. The only predeclared interactions are model allocation × task uncertainty, plan compactness × builder strength, and artifact shape × lock semantics.

The H13 variants contain byte-equivalent decisions, constraints, and tasks; only packaging changes. H1 and H13 remain crossed rather than bundled. Repository safety rules are never withheld. A retained episode is the declared H3 treatment; every independent episode otherwise starts cold with an opaque task alias and fresh archive.

Review sampling derives its subject and reviewer counts from the spec's Independent-review allocation. Each selected unchanged subject is assigned to one or three independent cold reviews; the assignment also balances full versus decision-delta input. Before review selection, every core builder emits a fixed-schema final self-audit over the unchanged candidate, and the workbench stores it as H7's control. Reviewers cannot see self-audits or earlier verdicts and cannot repair subjects. Oracle-decidable findings bypass model adjudication; the spec-owned adjudication allocation receives batched, treatment-blind records and never judges its own findings.

Run breadth-first and balance model variants over calendar time. A model-version change starts a new block. The spec-owned intermediate gates apply only frozen integrity, harm, futility, precision, token, and task-coverage rules; they never select cells from favorable individual outputs. The task is the unit of generalization and cold episodes are nested observations.

### Data & schema

Non-routing historical owners in `codex-cli-r1`: legacy-L1, legacy-L8

`methodology.md` owns the standalone experiment definitions, measures, quality guardrail, thresholds, stopping rules, exact source-URL inventory, and source-refresh provenance after closeout. During delivery, the spec's allocation and token tables are the sole numeric authority. `wave-*.json` derives those values and contains the frozen digest, hypotheses, models, slots, tasks, treatments, seeds, timeouts, prompt templates, oracle commands, and scoring rules. Validation rejects an H1–H13 mismatch, any allocation or limit unequal to the spec-derived design, duplicate slots, a candidate outside the frozen 12-task frame, factor imbalance, leaked reference identifiers, or a changed digest after the first reservation.

`progress.jsonl` is append-only and local to the run. Minimum fields are `item`, `status` in `pending|done|failed`, and `note`; process records also carry the fields in AC-0006. Latest valid state is authoritative. A torn final line is ignored and logged on resume; malformed earlier data fails closed.

Every JSON or JSONL surface has one versioned schema with exact fields, types,
enums, byte and collection bounds, nesting limits, finite-number checks, and
confined path types. The standard-library decoder rejects non-finite constants
and duplicate object keys. Unknown fields fail unless the owning schema names a
bounded extension map. Model output stays inert bytes until the applicable
schema accepts it; no pickle, YAML object loader, `eval`, or executable output
path is permitted.

`results.json` is the bounded tracked summary: methodology/design and prompt digests, task admission, process events, per-cell measures, hypothesis inputs, exclusions, and artifact digests. `evidence-index.json` binds each reported measure to retained evidence. Both exclude raw chain-of-thought, personal data, full candidate trees, and unbounded output. Raw JSONL and candidate roots stay in the ignored run directory.

### Interfaces & contracts

Non-routing historical owner in `codex-cli-r1`: legacy-L1

```text
python3 tools/plan_evolution_workbench/runner.py validate --design <path>
python3 tools/plan_evolution_workbench/runner.py admit --design <path> --run-dir <path>
python3 tools/plan_evolution_workbench/runner.py run --design <path> --run-dir <path>
python3 tools/plan_evolution_workbench/runner.py summarize --design <path> --run-dir <path> --output <path>
```

`run` reserves before spawn, executes pending slots in frozen randomized order, writes terminal state after each slot, and stops cleanly on signals. It uses argv arrays without a shell and rejects every model-derived command or path until schema and confinement validation passes. `--dry-run` emits redacted argv, the explicit sandbox/tool/environment policy, and fixture terminal records without starting a model.

### State & control flow

Non-routing historical owners in `codex-cli-r1`: legacy-L1, legacy-L4,
legacy-L5, legacy-L6, legacy-L7, legacy-L8

The sequence is `method frozen → tasks admitted/excluded → calibration and initial core → W1 gate → core through W2 → W2 gate → final legal core plus reviews/adjudication/reserve in W3 → hidden grading → summarized`. A builder becomes eligible only after its planner succeeds. Excluded-task slots end as environment failures and are not selectively reallocated.

Every build first restates the fixed outcome in structured output; mismatch is semantic-drift evidence. Evolving cells append construction decision diffs and validate only affected gates. Pinned cells leave their plans unchanged and record compliance, amendment pressure, escalation, or failure.

### Failure, edge cases & resilience

Non-routing historical owners in `codex-cli-r1`: legacy-L1, legacy-L2,
legacy-L3, legacy-L4, legacy-L5, legacy-L6, legacy-L7

- Missing model: `failed: model-unavailable`; no alias substitution.
- Timeout/non-zero exit: terminal failure with output digest; slot remains spent.
- Missing local dependency: task exclusion before candidate execution.
- Hidden-oracle infrastructure failure: separate from candidate failure; affected verdicts become inconclusive.
- Sandbox or confinement unavailable, unobservable, or widened: refuse launch
  and record a spent infrastructure failure if reservation already occurred.
- Malformed, oversized, non-finite, duplicate-key, unknown-field, or
  unconfined structured input: fail closed before its command, gate, grade, or
  report sink and retain a bounded diagnostic digest.
- Interrupted append: ignore only a torn last line, retain it for audit, and resume from the last valid record.
- Construction discovery in an evolving cell: append a decision diff, prove the fixed digest unchanged, run delta validation, and continue without broad rereview.
- Construction discovery in a pinned cell: preserve the plan and record the resulting path.

### Quality attributes (NFRs)

Non-routing historical owners in `codex-cli-r1`: legacy-L1, legacy-L3,
legacy-L4, legacy-L5, legacy-L6, legacy-L7, legacy-L8

The workbench derives category allocations, cumulative fixed releases, the
adaptive-reserve range, the study ceiling, and role/token ceilings from the
spec-owned sources and checks them before spawn. A gate memo explicitly
advances a fixed release and separately freezes admitted reserve item IDs;
without that authority, the next interval or reserve item remains unavailable.
Resume after reservation cannot duplicate an item. Reproducibility uses
baseline, method, design, prompt, snapshot, output, and oracle digests; model
nondeterminism remains explicit.

### Dependencies & integration

Non-routing historical owner in `codex-cli-r1`: legacy-L1

The workbench uses Python's standard library, local Git, the installed Codex CLI, the repository's `agentbundle.catalogue_tooling.file_safety` helpers, and existing task dependencies. Repository-confined paths use those helpers. Disposable run roots use a documented equivalent only where the helper contract does not apply, with the same canonicalize-then-contain and link/special-file rejection proven by construction tests. It follows subprocess and error-capture conventions from `pack_evals.py` without changing that production command. Official OpenAI documentation retrieval did not establish account-specific model availability or JSONL token fields, so calibration probes the local CLI and unavailable fields stay unavailable. The plan records `knowledge provider unavailable` because no eligible provider is exposed.

## Tasks

T1–T5 below are completed historical sections pinned by the controlled
amendment. Their CLI assumptions govern only the closed legacy block. T6 onward
implements the amended collaboration study.

### T1: The workbench and frozen method fail closed

**Depends on:** none

**Touches:** `tools/plan_evolution_workbench/**`, `docs/product/research/plan-evolution-experiments/methodology.md`, `docs/product/research/plan-evolution-experiments/wave-*.json`, `docs/specs/plan-evolution-experiments/notes/verification-ledger.md`

**Verification mode:** TDD.

**Tests:**
- `test_staged_design_and_process_ceilings` (AC-0001, AC-0002, AC-0003), `stub: true`
- Goal-based construction tests cover strict schemas, canonical path and archive
  confinement, dry-run sandbox/environment/tool policy, and no-fetch behavior
  (AC-0014, AC-0015, AC-0016, AC-0017), `no stub (mode)`

```python
# STUB: AC-0001, AC-0002, AC-0003 — validate allocation and staged releases
import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("plan_evolution_runner", ROOT / "runner.py")
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_staged_design_and_process_ceilings(tmp_path: Path) -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-design.json")
    summary = runner.validate_design(design)

    assert summary["hypotheses"] == tuple(f"H{i}" for i in range(1, 14))
    assert summary["allocations"] == design["allocations"]
    assert summary["study_ceiling"] == sum(design["allocations"].values())
    releases = design["fixed_releases"]
    reserve = design["reserve_release"]
    assert releases[0]["study_start"] == 1
    assert all(
        current["study_start"] == previous["study_end"] + 1
        for previous, current in zip(releases, releases[1:], strict=False)
    )
    assert reserve["study_start"] == releases[-1]["study_end"] + 1
    assert reserve["study_end"] == design["study_ceiling"]

    ledger = runner.InvocationLedger(
        tmp_path / "progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=releases,
        reserve_release=reserve,
    )
    first_capacity = releases[0]["study_end"] - releases[0]["study_start"] + 1
    for slot in range(1, first_capacity + 1):
        assert ledger.reserve(f"w1-{slot}", wave="W1") == (slot, slot)
    with pytest.raises(runner.InvocationLimitError):
        ledger.reserve("unreleased-w2", wave="W2")
    assert not ledger.was_started("unreleased-w2")

    ledger.release_next("W2", gate_memo_digest="sha256:gate-w1")
    assert ledger.reserve("w2-1", wave="W2") == (
        releases[1]["study_start"],
        1,
    )

    study_ledger = runner.InvocationLedger(
        tmp_path / "study-progress.jsonl",
        study_ceiling=design["study_ceiling"],
        fixed_releases=releases,
        reserve_release=reserve,
    )
    for index, release in enumerate(releases):
        if index:
            study_ledger.release_next(
                release["wave"],
                gate_memo_digest=f"sha256:gate-{release['wave']}",
            )
        capacity = release["study_end"] - release["study_start"] + 1
        for slot in range(1, capacity + 1):
            study_ledger.reserve(
                f"{release['wave']}-{slot}",
                wave=release["wave"],
            )
    with pytest.raises(runner.InvocationLimitError):
        study_ledger.reserve("reserve-1", wave="W3")

    reserve_capacity = reserve["study_end"] - reserve["study_start"] + 1
    reserve_items = tuple(
        f"reserve-{slot}" for slot in range(1, reserve_capacity + 1)
    )
    study_ledger.release_reserve(
        reserve_items,
        gate_memo_digest="sha256:gate-w2-reserve",
    )
    for item in reserve_items:
        study_ledger.reserve(item, wave="W3")
    with pytest.raises(runner.InvocationLimitError):
        study_ledger.reserve("study-overflow", wave=releases[-1]["wave"])
    assert not study_ledger.was_started("study-overflow")
```

Stub validation: `python3 -m py_compile` passes in disposable scratch. `python3 -m pytest -q` is intentionally red during PLAN because `runner.py` does not exist at this contract surface. The disposable source copy is removed; the cleanup observation is recorded in the verification ledger.

**Approach:** keep reusable execution machinery in `tools/` and semantic research records in `docs/product/research/`. Use argv arrays, explicit timeouts, captured output, no shell, append-after-item progress, and atomic bounded summaries.

**Done when:** the exact stub proves red then green; edge cases cover torn final records, duplicate/terminal items, prompt leakage, factor imbalance, contamination, replacement accounting, unreleased-wave, undeclared-reserve, and outer-ceiling refusal, plus schema, confinement, sandbox-policy, and dry-run no-spawn failures.

### T2: At least 12 task clusters have isolated, discriminating admission records

**Depends on:** T1

**Touches:** `docs/product/research/plan-evolution-experiments/wave-*.json`, `docs/product/research/plan-evolution-experiments/evidence-index.json`, `docs/specs/plan-evolution-experiments/notes/verification-ledger.md`, `/private/tmp/plan-evolution-*`

**Verification mode:** goal-based; no stub (mode).

**Tests:**
- Every admitted reference passes its frozen oracle and its baseline or seeded fault fails that same oracle (AC-0004)
- Every exported candidate has no source remote, alternates, shared objects, reference commit, or hidden-oracle path; archive members, links, and all declared roots pass canonical confinement checks (AC-0005, AC-0015)
- Corpus coverage contains at least 12 tasks and at least three tasks in each declared stratum for inference; otherwise later tasks run only the bounded case-study branch (AC-0003, AC-0004)
- Complexity and uncertainty labels are reproducible from pre-outcome reference facts (AC-0003)

**Approach:** process exactly the frozen table from top row to bottom row.
Exclude a candidate only when its reference fails the frozen oracle, its
baseline/seeded fault does not fail that oracle, a declared dependency is
absent, the required no-network oracle cannot run, or source isolation cannot
be established. Preserve every rejection and its first stable reason; do not
replace it with another task. Never place reference archives in
candidate-readable parents.

**Done when:** all 12 frozen candidates have admitted/excluded records with baseline/reference, oracle and mutation result, stratum, provenance, complexity, uncertainty, environment, tree digest, and isolation checks; rejected candidates remain in the evidence index; no inference slot has started.

### T3: Calibration processes prove the instruments

**Depends on:** T2

**Touches:** `tools/plan_evolution_workbench/**`, `docs/product/research/plan-evolution-experiments/results.json`, `docs/product/research/plan-evolution-experiments/evidence-index.json`, `docs/specs/plan-evolution-experiments/notes/verification-ledger.md`, `/private/tmp/plan-evolution-*`

**Verification mode:** goal-based integration; no stub (mode).

**Tests:**
- Exercise planner, builder, reviewer, and adjudicator capture without contributing observations to hypothesis estimates (AC-0006, AC-0017)
- Prove timestamp events, snapshots after file-changing boundaries, token fields or explicit unavailability, timeout/cap handling, hidden grading, and contamination detection (AC-0002, AC-0005, AC-0006, AC-0007)
- Confirm provisional standard/frontier model identifiers or terminally record them unavailable without substitution (AC-0006, AC-0010)
- Run negative read/write/egress/environment/credential/tool/delegation and approval-escalation canaries; refuse inference if any worker authority is wider than the frozen profile or cannot be observed (AC-0014)

**Done when:** every reservation in the spec-owned calibration allocation is terminal, the instrument-loss rate is known, and no inferential slot starts if snapshot/oracle/isolation capture is unreliable.

### T4: The first process gate has breadth-first core evidence

**Depends on:** T3

**Touches:** `docs/product/research/plan-evolution-experiments/results.json`, `docs/product/research/plan-evolution-experiments/evidence-index.json`, `docs/specs/plan-evolution-experiments/notes/verification-ledger.md`, `/private/tmp/plan-evolution-*`

**Verification mode:** observed behavior; no stub (mode).

**Tests:**
- Run calibration plus the core slots admitted in the spec-owned W1 release breadth-first with treatment/model/time balance and cold independent contexts except declared retention cells (AC-0002, AC-0003, AC-0006)
- Grade every builder with hidden quality guardrails and retain failed/capped episodes in cost denominators (AC-0007, AC-0008, AC-0009, AC-0010)
- Capture and strictly schema-validate every builder's final self-audit before hidden grading or reviewer selection (AC-0011, AC-0017)
- Emit the W1-gate integrity memo; it either leaves W2 unavailable or explicitly releases W2, and it makes no inferential success claim (AC-0002, AC-0003)

**Done when:** every W1 reservation is terminal and the integrity memo is generated solely from frozen rules and aggregate statistics; W2 availability matches that memo.

### T5: The core experiment reaches its decision gate and completes legal core slots

**Depends on:** T4

**Touches:** `docs/product/research/plan-evolution-experiments/results.json`, `docs/product/research/plan-evolution-experiments/evidence-index.json`, `docs/specs/plan-evolution-experiments/notes/verification-ledger.md`, `/private/tmp/plan-evolution-*`

**Verification mode:** observed behavior; no stub (mode).

**Tests:**
- Keep every factor balanced within task/stratum and retain only the three predeclared interactions (AC-0003, AC-0008, AC-0009, AC-0010)
- At the spec-owned W2 gate, compute harm, futility, task-coverage, censoring, token, and predictive-resolution checks without selecting favorable cells; either leave W3 fixed work unavailable or explicitly release it, and separately freeze zero or more admitted reserve item IDs (AC-0002, AC-0003)
- Complete remaining legal core slots only when the frozen gate permits them; bank process savings from retained cells (AC-0002)
- Capture and strictly schema-validate every remaining builder self-audit before hidden grading or reviewer selection (AC-0011, AC-0017)

**Done when:** every admitted legal core slot is terminal, the second-gate allocation memo exists, and H1–H5/H8/H10/H12/H13 have analysis-ready direct inputs or explicit stopping reasons.

### T6: Freeze the collaboration design and build the manual handoff adapter

**Depends on:** T5

**Touches:** `tools/plan_evolution_workbench/causal_runner.py`,
`tools/plan_evolution_workbench/test_causal_runner.py`,
`tools/plan_evolution_workbench/fixtures/valid-causal-design.json`,
`docs/product/research/plan-evolution-experiments/causal-methodology.md`,
`docs/product/research/plan-evolution-experiments/codex-collaboration-design.json`

**Verification mode:** TDD.

**Tests:** `test_causal_design_compiles_exact_shared_panel` is the exact red
stub for AC-0002, AC-0003, AC-0012, and AC-0013. Further tests prove that
another seed changes order but not counts; phase receipts reject gaps,
duplicates, and reordering; provider-labelled outputs cannot overwrite legacy
records; unavailable telemetry remains unavailable; all candidate-executing
commands enforce the environment, egress, root, path, timeout, output,
process-tree, and capped-state policy or terminate without execution; and raw
artifacts enforce byte, retention, privacy, and digest-only quarantine rules
(AC-0006, AC-0007A, AC-0017, AC-0017A).

```python
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("causal_runner", ROOT / "causal_runner.py")
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_causal_design_compiles_exact_shared_panel() -> None:
    design = runner.load_design(ROOT / "fixtures" / "valid-causal-design.json")
    compiled = runner.compile_assignments(design)

    assert compiled["study_id"] == "codex-collaboration-r1"
    assert compiled["study_ceiling"] == 600
    assert compiled["maximum_used"] == 566
    assert compiled["shared_plan_authors"] == 18
    assert compiled["shared_build_panel"] == 90
    assert compiled["blind_adjudication_starts"] == {"run-1": 12, "run-7": 12}
    assert all(not item["released"] for item in compiled["holdout_assignments"])
```

Stub validation: `python3 -m py_compile` passes in disposable scratch. Pytest
collection is intentionally red before EXECUTE because `causal_runner.py` does
not exist at that surface.

**Done when:** the new CLI validates and compiles the exact 600-ceiling design,
prepares a disposable slot, accepts a simulated controller launch and terminal
receipt, grades it, and reproduces a bounded summary without invoking a model.

### T7: Build task packages and recalibrate all hidden oracles

**Depends on:** T6

**Touches:** `docs/product/research/plan-evolution-experiments/task-packages/**`,
`docs/product/research/plan-evolution-experiments/codex-collaboration-evidence-index.json`,
`.context/experiments/codex-collaboration-r1/**`

**Verification mode:** goal-based integration; no stub (mode).

**Tests:** regenerate Git-free snapshots; inject the same frozen hidden assets
into separate baseline and reference grading clones; require assertion-level or
semantic baseline failure, reference pass, seeded-mutation failure, and restored
pass; prove worker-visible roots contain no hidden assets or reference markers
(AC-0004, AC-0005, AC-0007, AC-0007A, AC-0016).

**Done when:** all eight task packages pass semantic oracle discrimination and
leakage checks, or the collaboration study stops before Run 0 with an explicit
task-specific reason.

### T8: Preserve Run 0a and run the replacement calibration

**Depends on:** T7

**Touches:** `docs/product/research/plan-evolution-experiments/codex-collaboration-run-0.json`,
`docs/product/research/plan-evolution-experiments/codex-collaboration-run-0b-report.md`,
`docs/product/research/plan-evolution-experiments/codex-collaboration-evidence-index.json`,
`docs/product/research/plan-evolution-experiments/document-packets/run-0/**`,
`docs/product/research/plan-evolution-experiments/document-packets/run-0b/**`,
`.context/experiments/codex-collaboration-r1/**`

**Verification mode:** observed behavior; no stub (mode).

**Tests:** preserve Run 0a and its eight responses without repair or reuse;
freeze the same two synthetic, non-secret tasks across four artifact forms in a
separate Run 0b manifest; assign fresh study ordinals 9–16; freeze the complete
schema-bearing prompt before launch; require actual-dispatch bytes and digest to
equal that prompt; launch each cold worker once with an explicit
`gpt-5.6-luna` requested route; validate every assignment, launch, terminal
response, strict output parse, schema, alias, atom coverage, static-registry
grade, deviation, and slot receipt; record the managed permission/tool profile
and permanent non-inferential label; reconcile eight new starts and terminals;
prove no prompt includes commands, executable attachments, hidden keys,
personal data, or secrets and no response is executed, imported, or evaluated
(AC-0002, AC-0004, AC-0005, AC-0005A, AC-0006, AC-0007, AC-0007A, AC-0017A,
AC-0018, AC-0019).

**Done when:** Run 0a remains an immutable failed calibration and Run 0b has
eight fresh terminal document subjects whose exact rendering, receipt,
static-grading, privacy, deviation, and accounting gates all pass. A Run 0b
standalone recovery report reproduces the decision, accounting, slot results,
limitations, and durable evidence without reading this spec or plan before any
later collection reopens. A Run 0b failure or missing report leaves later
document collections closed and permits no further replacement; every
inferential release remains false regardless.

### T9: Run the pre-execute review-policy experiment

**Depends on:** T8

**Touches:** `docs/product/research/plan-evolution-experiments/codex-collaboration-run-1.json`,
`docs/product/research/plan-evolution-experiments/codex-collaboration-evidence-index.json`,
`docs/product/research/plan-evolution-experiments/document-packets/run-1/**`,
`.context/experiments/codex-collaboration-r1/**`

**Verification mode:** observed behavior; no stub (mode).

**Tests:** freeze identical three-revision subjects and a treatment-blind defect
registry; run 54 cold policy trajectories with at most three reviews each;
reserve, launch, terminally account for, and reconcile no more than 12 batched
blind-adjudication starts assigned to Run 1;
reconcile recall, precision, novelty relation, changed-material status, rounds,
and prose counts against the registry; validate that packets are non-secret,
outputs remain data, and every result is non-inferential (AC-0005, AC-0007,
AC-0007A, AC-0011, AC-0012, AC-0018, AC-0019).

**Done when:** all collected Run 1 reservations are terminal and H9
non-inferential review-policy inputs are complete without reviewer edits to
subjects or executed model output.

### T10: Author paired plans and run the five-arm document-construction panel

**Depends on:** T9

**Touches:** `docs/product/research/plan-evolution-experiments/codex-collaboration-runs-2-5.json`,
`docs/product/research/plan-evolution-experiments/codex-collaboration-evidence-index.json`,
`docs/product/research/plan-evolution-experiments/document-packets/runs-2-5/**`,
`.context/experiments/codex-collaboration-r1/**`

**Verification mode:** observed behavior; no stub (mode).

**Tests:** run 18 plan authors and 90 bounded construction responses; prove Run
3 atom equivalence, Run 4 obligation equivalence, Run 2 amendment rules, Run 5
context assignment, static hidden-registry grading, scope checks, self-audits,
no executable output handling, and exact shared-control accounting (AC-0007,
AC-0007A, AC-0008, AC-0009, AC-0012, AC-0018, AC-0019).

**Done when:** every collected plan/construction reservation is terminal and H1,
H3, H10, and H13 have paired non-inferential inputs or explicit stopped cells.

### T11: Run requested planner-constructor model allocation

**Depends on:** T10

**Touches:** `docs/product/research/plan-evolution-experiments/codex-collaboration-run-6.json`,
`docs/product/research/plan-evolution-experiments/codex-collaboration-evidence-index.json`,
`docs/product/research/plan-evolution-experiments/document-packets/run-6/**`,
`.context/experiments/codex-collaboration-r1/**`

**Verification mode:** observed behavior; no stub (mode).

**Tests:** cross the frozen four document tasks, two requested planner routes,
two requested constructor routes, and three replications; reconcile 48
trajectories and 96 starts; keep planner and constructor observations separate,
served identity unavailable unless observed, and build performance out of scope
(AC-0006, AC-0010, AC-0018, AC-0019).

**Done when:** all Run 6 reservations are terminal and H4 has non-inferential
requested-routing observations without an unsupported served-model or build-
performance claim.

### T12: Run copied-response document-review loops

**Depends on:** T11

**Touches:** `docs/product/research/plan-evolution-experiments/codex-collaboration-run-7.json`,
`docs/product/research/plan-evolution-experiments/codex-collaboration-evidence-index.json`,
`docs/product/research/plan-evolution-experiments/document-packets/run-7/**`,
`.context/experiments/codex-collaboration-r1/**`

**Verification mode:** observed behavior; no stub (mode).

**Tests:** select 12 construction responses by the frozen blinded rule; copy each before
policy assignment; run 36 trajectories with no more than three reviews and two
document repairs; statically grade after every repair; reconcile fingerprints, dispositions,
novelty, self-audits, repair benefit, repair-origin defects, and churn prose;
reserve, launch, terminally account for, and reconcile no more than 12 batched
blind-adjudication starts assigned to Run 7
(AC-0007, AC-0007A, AC-0011, AC-0012, AC-0018, AC-0019).

**Done when:** all Run 7 reservations are terminal and H7/H9 inputs retain
complete subject and repair lineage.

### T13: Close the synthetic extension as a methodological negative result

**Depends on:** T12

**Touches:** `docs/product/research/plan-evolution-experiments/review-churn-evidence-report.md`,
`docs/specs/plan-evolution-experiments/notes/verification-ledger.md`,
`.context/experiments/codex-headless-sol-loop-confirmation-r1/**`

**Verification mode:** goal-based archival reconciliation and manual research
review; no stub (mode).

**Tests:** reconcile 95 terminal starts and one unused start against the frozen
96-start cap; bind the seven raw review reports, retirement record, digest
manifest, and standalone JSON/Markdown handoff; verify that no tracked
historical artifact is rewritten and no eighth model/reviewer start occurs;
add a bounded report section that separates the retained observations from the
unsupported natural-work claims and names the apparatus defects that invalidate
the latter (AC-0002, AC-0017, AC-0019, AC-0020).

**Done when:** T13 is durably labelled a methodological negative result, its
evidence remains inspectable, its seeded recall and synthetic policy contrasts
are excluded from work-loop effectiveness recommendations, and no further T13,
Sonnet, Opus, or synthetic validation start is scheduled.

### T14: Reconstruct and freeze the natural-history effectiveness baseline

**Depends on:** T13

**Touches:** `docs/product/research/plan-evolution-experiments/review-effectiveness-methodology.md`,
`docs/product/research/plan-evolution-experiments/review-effectiveness-baseline.json`,
`docs/product/research/plan-evolution-experiments/review-effectiveness-report.md`,
`docs/specs/plan-evolution-experiments/notes/verification-ledger.md`

**Verification mode:** goal-based source reconciliation, direct arithmetic, and
manual finding-lineage review; no stub (mode).

**Tests:** freeze the inclusion and exclusion rule before recoding; cover the
four Tier-A histories, the retained aggregate cases, the occasioning 15-round
Claude Code loop, and the repository-wide survey without double-counting;
record revision identity when available, stable requirement or protected-risk
ground, finding family, accepted-surface state, disposition, repair origin,
durable change, role/model identity, tokens, wall time, and explicit
missingness. Recompute durable blocker closure, unique durable blockers per
review start, repair-origin blockers, accepted-surface reopening, same-family
recurrence, same-revision disagreement, appeal reversal/indeterminacy, action
cost, and observed token/time cost without a scalar score. Also report prose-
churn events divided by all blocking findings after the first accepted revision,
events per review start, and attributable review/adjudication/repair actions,
tokens, and time; unavailable lineage stays unavailable. Keep T13 in a separate
methodological table (AC-0017, AC-0020, AC-0021, AC-0024).

**Done when:** every included history has a source-bound event row or explicit
unavailable field, the baseline report reproduces its arithmetic directly, the
classification rules and limitations are frozen before prospective thresholds,
and zero model process starts were used.

### T15: Freeze the prospective release and observe consecutive real work

**Depends on:** T14

**Touches:** `docs/product/research/plan-evolution-experiments/review-effectiveness-methodology.md`,
`docs/product/research/plan-evolution-experiments/review-effectiveness-baseline.json`,
`docs/product/research/plan-evolution-experiments/review-effectiveness-report.md`,
`docs/specs/plan-evolution-experiments/notes/verification-ledger.md`

**Verification mode:** observed behavior after a human release gate, plus
goal-based revision binding and scorecard arithmetic; no stub (mode).

**Tests:** before the first case, write and independently review a release record
that freezes consecutive eligibility, exclusions, protected-defect classes,
new-evidence and durable-observation rules, broad-review reopen triggers,
role/model selection policy, minimum cohort, observation window, thresholds,
and process budget. Stop for owner approval; without it, launch nothing. For
each admitted case, capture the normal broad adversarial and triggered
specialist reviews, blocker adjudication, repairs, focused closure review,
stopping decision, advisory residue, and exact stopped-revision digest. Then
run one independent cold full-document shadow audit over those exact bytes and
adjudicate only claimed blockers. Count an escape only when sustained against a
stable requirement, executable failure, protected risk, or genuinely new
external evidence. Regenerate the scorecard with case-level values, medians,
ranges, missingness, model/role labels, and every protected escape; do not pool
retrospective or T13 rows or emit a scalar verdict. The scorecard must include
the prose-churn numerator and denominator, events per review start, and directly
observed reviewer, adjudicator, and repair cost attributable to those events
(AC-0022, AC-0023, AC-0024).

**Done when:** the release record was approved before the first process start,
all consecutive eligible cases in the observation window are included or carry
a rule-grounded exclusion, every normal loop and shadow audit is terminal, the
report compares risk closure and reviewer churn without requiring `Clean`, and
independent adversarial and quality review are clean.

## Rollout

This is a local research run with no deployment, migration, flag, or cutover.
T13 raw workspaces retain their declared archival status. T14 changes only
research documents. T15 observes normal repository work and adds a shadow audit
only after its separate release approval. Production workflow behavior does not
change through this study; adopting a result requires another reviewed contract.

## Risks

- The retrospective corpus is purposive and may overlap the repository-wide
  aggregate. It describes mechanisms but does not estimate a population effect.
- Historical revisions, model identity, tokens, and wall time are often absent.
  Missingness can make cost comparisons directional only.
- The prospective cohort is observational. Task mix, risk, model routing, and
  reviewer availability can confound changes over time.
- Durable-blocker and prose-churn classification requires judgment. Independent
  adjudication reduces but does not remove disagreement.
- A shadow audit may itself create anchoring or extra cost. It remains a
  measurement layer and may reopen only independently sustained protected risk.
- Consecutive eligibility prevents outcome selection but may yield a small or
  unbalanced cohort within the approved observation window.

## Changelog

<!-- Approval entries are added only at their gates. -->

- 2026-09-26: spec approved by eugenelim
- 2026-09-26: plan approved by eugenelim
- 2026-09-26: unchanged spec reapproved for the authorized T1 stub amendment by eugenelim
- 2026-09-26: amended plan approved and baseline resealing authorized by eugenelim
- 2026-09-27: causal collaboration redesign authorized by eugenelim; approval
  entries for this amended spec and plan were pending the required reviews.
- 2026-09-27: amended causal spec approved by eugenelim through the explicit
  “looks good, go ahead” execution authority; pre-execute reviews are clean.
- 2026-09-27: amended causal plan approved by eugenelim through the same
  execution authority after all sustained review findings were resolved.
- 2026-09-28: document-only non-inferential amendment authorized by eugenelim;
  approval entries for the amended spec and plan await required review.
- 2026-09-28: document-only amended spec approved by eugenelim through the
  explicit “yes” amendment authority; pre-execute reviews are clean.
- 2026-09-28: document-only amended plan approved by eugenelim through the same
  authority after the sole launch-rule contradiction was resolved.
- 2026-09-28: Run 0b recovery authorized by eugenelim after Run 0a failed its
  controller rendering gate; approval entries for the bounded amended spec and
  plan await required review.
- 2026-09-28: Run 0b amended spec approved by eugenelim through the explicit
  `go ahead` recovery authority; pre-execute adversarial review is clean.
- 2026-09-28: Run 0b amended plan approved by eugenelim through the same
  authority; the sealed recovery adds eight starts and permits no second retry.
- 2026-09-29: Sol-first cross-model sensitivity extension and 920-start outer
  ceiling authorized by eugenelim; approval entries for the amended spec and
  plan await required pre-execute review.
- 2026-09-29: Sol-first cross-model amended spec approved by eugenelim through
  the explicit `approved` authority; adversarial and security pre-execute
  reviews are clean.
- 2026-09-29: Sol-first cross-model amended plan approved by eugenelim through
  the same authority; the provider schedule and 920-start ceiling are ready to
  seal.
- 2026-09-29: natural-work effectiveness amendment authorized by eugenelim
  after T13's seven-round closeout; exact amended spec and plan approval awaits
  required pre-execute review.
- 2026-09-29: natural-work amended spec approved by eugenelim through the
  explicit `approved` scope authority; pre-execute adversarial review is clean.
- 2026-09-29: natural-work amended plan approved by eugenelim through the
  explicit `yes` strategy authority; T13 archival closeout and T14 retrospective
  reconstruction may proceed, while T15 prospective starts remain separately
  gated.
