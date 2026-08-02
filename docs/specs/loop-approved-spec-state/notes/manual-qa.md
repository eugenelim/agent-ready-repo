# Manual QA — AC9 end-to-end integration flows

Recorded 2026-08-02. Runs were executed via real subprocesses against
temporary directories using `tempfile.TemporaryDirectory()`.

Scripts invoked as:
- `python3 packs/core/.apm/skills/work-loop/scripts/loop-engine.py`
- `python3 packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`

---

## Flow 1 — Code mode

**Expected AC9 outcome:** all steps exit 0; final state is `CODE-IMPLEMENTATION`;
`last_event: plan-locked`.

### Steps

| Step | Command | Exit code | Stdout (truncated) |
|------|---------|-----------|-------------------|
| 1 | `loop-engine init myfeature --mode code --json` | 0 | `{"run_id": "5b581963-a72e-47d8-983b-a22328b5ec5b", "feature": "myfeature", "mode": "code"}` |
| 2 | `loop-cohort init myfeature --run-id 5b581963...` | 0 | `loop-cohort: initialised .../state.json (feature=myfeature run_id=5b581963-a72e-47d8-983b-a22328b5ec5b)` |
| 3 | `loop-engine transition spec-ready` | 0 | `loop-engine: transition 'SPEC-PLAN-DRAFTING' → 'spec-ready' → 'SPEC-PLAN-REVIEW' (seq=1) for myfeature` |
| 4 | `loop-engine transition reviewers-clean` | 0 | `loop-engine: transition 'SPEC-PLAN-REVIEW' → 'reviewers-clean' → 'SPEC-HUMAN-GATE' (seq=2) for myfeature` |
| 5 | `[update spec.md Status: Approved]` then `loop-engine transition spec-approved` | 0 | `loop-engine: transition 'SPEC-HUMAN-GATE' → 'spec-approved' → 'PLAN-HUMAN-GATE' (seq=3) for myfeature` |
| 6 | `[update plan.md Status: Approved]` then `loop-engine transition plan-approved` | 0 | `loop-engine: transition 'PLAN-HUMAN-GATE' → 'plan-approved' → 'SPEC-PLAN-APPROVED' (seq=4) for myfeature` |
| 7 | `loop-cohort approve-plan --expect-run-id 5b581963...` | 0 | `loop-cohort: approve-plan for myfeature (approved_spec_hash=52fc097d75d6… approved_plan_hash=c0e87351e99a…)` |
| 8 | `loop-cohort schedule --expect-run-id 5b581963...` | 0 | `loop-cohort: topological order for myfeature ... wave 1: T1 / wave 2: T2 / schedule persisted (2 wave(s))` |
| 9 | `loop-engine transition plan-locked` | 0 | `loop-engine: transition 'SPEC-PLAN-APPROVED' → 'plan-locked' → 'CODE-IMPLEMENTATION' (seq=5) for myfeature` |

### Final engine-state.json

```json
{
  "schema_version": 1,
  "run_id": "5b581963-a72e-47d8-983b-a22328b5ec5b",
  "feature": "myfeature",
  "mode": "code",
  "state": "CODE-IMPLEMENTATION",
  "last_event": "plan-locked",
  "last_event_context": null,
  "transition_sequence": 5,
  "last_transition_at": "2026-08-02T05:14:52Z"
}
```

### AC9 outcome

MATCHED. Final state `CODE-IMPLEMENTATION` with `last_event: plan-locked`. All 9
steps exited 0.

---

## Flow 2 — Spec-plan mode

**Expected AC9 outcome:** all steps exit 0; final state is `DONE`;
spec.md and plan.md both retain `Status: Approved`.

### Steps

| Step | Command | Exit code | Stdout (truncated) |
|------|---------|-----------|-------------------|
| 1 | `loop-engine init myfeature --mode spec-plan --json` | 0 | `{"run_id": "03daffbb-4af4-4dfa-b5a5-7d2ac6055426", "feature": "myfeature", "mode": "spec-plan"}` |
| 2 | `loop-cohort init myfeature --run-id 03daffbb...` | 0 | `loop-cohort: initialised .../state.json (feature=myfeature run_id=03daffbb-4af4-4dfa-b5a5-7d2ac6055426)` |
| 3 | `loop-engine transition spec-ready` | 0 | `loop-engine: transition 'SPEC-PLAN-DRAFTING' → 'spec-ready' → 'SPEC-PLAN-REVIEW' (seq=1) for myfeature` |
| 4 | `loop-engine transition reviewers-clean` | 0 | `loop-engine: transition 'SPEC-PLAN-REVIEW' → 'reviewers-clean' → 'SPEC-HUMAN-GATE' (seq=2) for myfeature` |
| 5 | `[update spec.md Status: Approved]` then `loop-engine transition spec-approved` | 0 | `loop-engine: transition 'SPEC-HUMAN-GATE' → 'spec-approved' → 'PLAN-HUMAN-GATE' (seq=3) for myfeature` |
| 6 | `[update plan.md Status: Approved]` then `loop-engine transition plan-approved` | 0 | `loop-engine: transition 'PLAN-HUMAN-GATE' → 'plan-approved' → 'SPEC-PLAN-APPROVED' (seq=4) for myfeature` |
| 7 | `loop-cohort approve-plan --expect-run-id 03daffbb...` | 0 | `loop-cohort: approve-plan for myfeature (approved_spec_hash=52fc097d75d6… approved_plan_hash=9a123f278e11…)` |
| 8 | `loop-engine transition plan-locked` | 0 | `loop-engine: transition 'SPEC-PLAN-APPROVED' → 'plan-locked' → 'DONE' (seq=5) for myfeature` |

Note: no `loop-cohort schedule` step — spec-plan mode does not require a schedule.

### Final engine-state.json

```json
{
  "schema_version": 1,
  "run_id": "03daffbb-4af4-4dfa-b5a5-7d2ac6055426",
  "feature": "myfeature",
  "mode": "spec-plan",
  "state": "DONE",
  "last_event": "plan-locked",
  "last_event_context": null,
  "transition_sequence": 5,
  "last_transition_at": "2026-08-02T05:14:56Z"
}
```

### AC9 outcome

MATCHED. Final state `DONE` with `last_event: plan-locked`. All 8 steps exited 0.
spec.md and plan.md both retained `Status: Approved` at the `DONE` terminal state.
