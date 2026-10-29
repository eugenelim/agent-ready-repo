# Verification ledger: header-derived dispatch

## Live replay

Run 2026-10-29 with `tools/replay-dispatch.py` at repository commit `df96661ed` (its byte-identical pre-rebase twin is `811815b3c`; the tool itself is added by the commit that records this run), over a `git worktree` of snapshot commit `95a8cc985`:

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

For the § Equivalence rows, the 2026-10-29 RFC-0106 § Errata entry replaces the D1 and D3 citations below; D1 and D3 remain the decisions that entry applies.

The author assigns each case and class by hand, and the owner approves the list below.

| Spec path | Field | Base | Dispatch | Case | Class |
| --- | --- | --- | --- | --- | --- |
| `*` | `argless_start` | `ask` over 2 candidates | `ask` over 3 candidates | `unregistered-implementing` | accepted removal (RFC-0106 D1) |
| `*` | `argless_resume` | `ask` over 2 candidates | `ask` over 3 candidates | `unregistered-implementing` | accepted removal (RFC-0106 D1) |
| `docs/specs/execution-supervisor-attempt-security/spec.md` | `resume` | `refuse` | `resume` | `dependent-finding-names-spec` | accepted removal (RFC-0106 § Errata, 2026-10-29, item 9) |
| `docs/specs/experience-pack-0.6.0/spec.md` | `start` | `refuse` | `invalid_selector` | `dotted-slug-selector` | accepted removal (RFC-0106 § Errata, 2026-10-29, item 10) |
| `docs/specs/experience-pack-0.6.0/spec.md` | `resume` | `refuse` | `invalid_selector` | `dotted-slug-selector` | accepted removal (RFC-0106 § Errata, 2026-10-29, item 10) |
| `docs/specs/plan-evolution-experiments/spec.md` | `active` | `false` | `true` | `unregistered-implementing` | accepted removal (RFC-0106 D1) |
| `docs/specs/plan-evolution-experiments/spec.md` | `resume` | `refuse` | `resume` | `unregistered-implementing` | accepted removal (RFC-0106 D1) |

## Owner approvals

| Date | Item | Approval |
| --- | --- | --- |
| 2026-10-29 | Dated re-pin of `cooling.py` and the schema digests in `tests/roster/test_cooling_scope_closure.py` (AC-0015) | Authorized by eugenelim |
| 2026-10-29 | The live replay's classified difference list above (AC-0019) | Approved by eugenelim |
| 2026-10-29 | The case replay's classification, including `dep-spec-open`'s unregistered target under RFC-0106 D1 (AC-0018) | Approved by eugenelim |
| 2026-10-29 | RFC-0106 § Errata entry of 2026-10-29, cases `duplicate-membership`, `provenance-mismatch`, `inactive-initiative`, `impossible-transition`, `registry-settled-target-with-findings`, `symlink-spec-file`, `symlink-spec-dir-alias`, `cooled-child-none-record-predates-parent` (name corrected from `cooled-child-record-predates-parent` with the owner's approval, 2026-10-29), `dependent-finding-names-spec`, `dotted-slug-selector` (AC-0022), wording approved before commit | Approved by eugenelim |
| 2026-10-29 | Adding the `dependent-finding-names-spec` and `dotted-slug-selector` corpus cases, recording only their new keys | Approved by eugenelim |
| 2026-10-29 | Superseded by the next row: controlled amendment of AC-0021 as first drafted, naming three rows and items (11) to (13) | Approved by eugenelim, then superseded |
| 2026-10-29 | Controlled amendment of AC-0021 and AC-0022 as committed: four rows (`unregistered-approved`, `unregistered-implementing`, `dep-spec-open`, `several-ready`) cite the 2026-10-29 RFC-0106 § Errata entry; that entry's final wording, items (1) to (14), with items (11) to (13) under D1 and item (14) under D3, approved before its commit; spec and plan re-approved | Approved by eugenelim |
| 2026-10-29 | Implementation review: add replay cases `registry-settled-defect-closed` and `registry-settled-kind-mismatch` with only their new keys recorded; amend AC-0018 to replace `provenance_reference` with `invalid_artifact_path` for a spec whose `Brief:` names a path that is not a brief file; settle the ledger citation of `811815b3c` (the pre-rebase twin of on-branch `df96661ed`, byte-identical `dispatch.py`) as a Nit fixed by citing `df96661ed` | Approved by eugenelim |
| 2026-10-29 | Keep `registry-settled-defect` and `registry-settled-kind-differs`, their keys and their rows under their names, relabelled in the suite as exercising a refused membership | Approved by eugenelim |
