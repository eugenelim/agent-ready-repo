# Verification ledger: header-derived dispatch

## Live replay

Run 2026-10-29 with `tools/replay-dispatch.py` at repository commit `811815b3c` (the tool itself is added by the commit that records this run), over a `git worktree` of snapshot commit `95a8cc985`:

```
python3 tools/replay-dispatch.py --root <worktree> --base-engine <worktree>/packs/core/.apm/skills/workspace-status/scripts/workspace_status.py
```

Exit code: `0`.

```
base canonical.ready 0 []
base canonical.active 2 ["docs/specs/execution-supervisor-attempt-security/spec.md", "docs/specs/workspace-retirement/spec.md"]
dispatch ready 0 []
dispatch active 3 ["docs/specs/execution-supervisor-attempt-security/spec.md", "docs/specs/plan-evolution-experiments/spec.md", "docs/specs/workspace-retirement/spec.md"]
workspace.toml sha256 38ea32422f18d8d02bd6ac1f7c366ff14a7a45aac4d8af6066d7f59ee55250cb
lifecycle records 0
differing specs 3
DIFF * argless_start base={"action": "ask", "path": null, "candidates": ["docs/specs/execution-supervisor-attempt-security/spec.md", "docs/specs/workspace-retirement/spec.md"]} dispatch={"action": "ask", "path": null, "candidates": ["docs/specs/execution-supervisor-attempt-security/spec.md", "docs/specs/plan-evolution-experiments/spec.md", "docs/specs/workspace-retirement/spec.md"]}
DIFF * argless_resume base={"action": "ask", "path": null, "candidates": ["docs/specs/execution-supervisor-attempt-security/spec.md", "docs/specs/workspace-retirement/spec.md"]} dispatch={"action": "ask", "path": null, "candidates": ["docs/specs/execution-supervisor-attempt-security/spec.md", "docs/specs/plan-evolution-experiments/spec.md", "docs/specs/workspace-retirement/spec.md"]}
DIFF docs/specs/execution-supervisor-attempt-security/spec.md resume base={"action": "refuse", "path": null, "candidates": []} dispatch={"action": "resume", "path": "docs/specs/execution-supervisor-attempt-security/spec.md", "candidates": []}
DIFF docs/specs/experience-pack-0.6.0/spec.md start base={"action": "refuse", "path": null, "candidates": []} dispatch={"action": "invalid_selector", "path": null, "candidates": []}
DIFF docs/specs/experience-pack-0.6.0/spec.md resume base={"action": "refuse", "path": null, "candidates": []} dispatch={"action": "invalid_selector", "path": null, "candidates": []}
DIFF docs/specs/plan-evolution-experiments/spec.md active base=false dispatch=true
DIFF docs/specs/plan-evolution-experiments/spec.md resume base={"action": "refuse", "path": null, "candidates": []} dispatch={"action": "resume", "path": "docs/specs/plan-evolution-experiments/spec.md", "candidates": []}
```

The snapshot holds no lifecycle record (`lifecycle records 0`), so the second run AC-0019 describes (a scratch copy with each cooled spec entry's `source.parent` copied into its record's `parent`) has nothing to copy and was not run.

`experience-pack-0.6.0` has a dot in its directory name, so `dispatch.py` refuses its named selectors with `invalid_selector` (exit 2). The tool records that as the decision action `invalid_selector`; the base answers `refuse`.

### Classification

The author assigns each case and class by hand, and the owner approves the list below.

| Spec path | Field | Base | Dispatch | Case | Class |
| --- | --- | --- | --- | --- | --- |
| `*` | `argless_start` | `ask` over 2 candidates | `ask` over 3 candidates | | |
| `*` | `argless_resume` | `ask` over 2 candidates | `ask` over 3 candidates | | |
| `docs/specs/execution-supervisor-attempt-security/spec.md` | `resume` | `refuse` | `resume` | | |
| `docs/specs/experience-pack-0.6.0/spec.md` | `start` | `refuse` | `invalid_selector` | | |
| `docs/specs/experience-pack-0.6.0/spec.md` | `resume` | `refuse` | `invalid_selector` | | |
| `docs/specs/plan-evolution-experiments/spec.md` | `active` | `false` | `true` | | |
| `docs/specs/plan-evolution-experiments/spec.md` | `resume` | `refuse` | `resume` | | |

## Owner approvals

| Date | Item | Approval |
| --- | --- | --- |
| 2026-10-29 | Dated re-pin of `cooling.py` and the schema digests in `tests/roster/test_cooling_scope_closure.py` (AC-0015) | Authorized by eugenelim |
