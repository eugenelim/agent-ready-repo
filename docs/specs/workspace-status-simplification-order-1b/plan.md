# Plan: workspace-status simplification — Order 1B

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog.

## Approach

Extend the Order 1A engine and CLI to add three read modes without changing the
existing full-analysis path. The engine gets two private scan helpers (`_run_type1_scan`,
`_run_type23_scan`), `analyze_bounded` (Type 2+3 only), and `explain_item` (focused
projection). The CLI gets manual argv pre-dispatch for subcommands. SKILL.md switches
its default invocation to `status`. All existing tests must pass unchanged.

The riskiest part is the subcommand routing: `--root` must be accepted with or without
a subcommand prefix, and the no-subcommand path must produce a reconcile-equivalent
result with a deprecation warning only on stderr. The `status` mode's bounded scope
must be structurally proven through the AC10/AC11 fixture test.

Sequential throughout (engine → CLI → tests → SKILL.md → build).

## Constraints

- RFC-0023: no shared-libs projection; scripts remain self-contained.
- RFC-0064: workspace.toml schema unchanged; workspace-status semantics preserved.
- Order 1A compatibility: `analyze(root)` API unchanged; all existing CLI tests pass.
- No new runtime dependency; no installer production code changes.
- Sequential: tasks overlap on engine, CLI, tests, and SKILL.md.

## Construction tests

All tests written as red stubs before T2 implementation.

**T2 (engine) — unit tests added to `tools/test_workspace_status.py`** (alongside existing engine tests):
- `test_analyze_bounded_skips_type1`: N declared entries + M untracked live specs;
  `analyze_bounded` result has `type1 == []` and `global_scan_performed == False`
- `test_analyze_bounded_file_counts`: `declared_spec_files_read <= N` (≤ not =, since
  entries missing spec.md don't increment), `global_scan_files_read == 0`,
  `files_read == declared_spec_files_read`
- `test_analyze_full_file_counts`: same fixture; `global_scan_performed == True`,
  `global_scan_files_read >= M` (≥ not =, since walk reads tracked specs too),
  `files_read == declared_spec_files_read + global_scan_files_read`
- `test_explain_item_ready`: item in queue with no deps; `selector_status: "matched"`,
  `classification: "ready"`, `blocking_needs: []`, all deps `satisfied: true`
- `test_explain_item_blocked`: item blocked by dep; `classification: "blocked"`,
  `blocking_needs` non-empty, unsatisfied dep listed
- `test_explain_item_active`: item in work.active; `classification: "active"`, `list: "active"`
- `test_explain_item_shipped`: item in work.shipped; `classification: "shipped"`, `list: "shipped"`
- `test_explain_item_not_found`: unknown selector; `selector_status: "not_found"`
- `test_explain_item_ambiguous_cross_initiative`: same slug in two distinct initiatives'
  work queues; `selector_status: "ambiguous"` with `matches` list
- `test_explain_item_within_ini_duplicate_not_ambiguous`: slug in both active and shipped
  of one initiative; `selector_status: "matched"`, `list: "active"` (active > shipped precedence)
- `test_explain_item_shaping_only_not_found`: slug exists only in shaping (ini A), not in
  any work queue; `selector_status: "not_found"` (shaping items not searched)
- `test_explain_item_downstream_sole_blocker`: entry A (ini-001) blocked only by B
  (ini-001); `explain_item(result, B)` has `downstream_unblocked == [A.path]`
- `test_explain_item_downstream_not_sole_blocker`: entry A blocked by B and C;
  `explain_item(result, B)` has A absent from `downstream_unblocked`
- `test_explain_item_downstream_cross_ini_excluded`: entry A (ini-002) blocked by B
  (ini-001, cross-ini dep); `explain_item(result, B)` does NOT list A in
  `downstream_unblocked` (different ini_slug)
- `test_analyze_bounded_path_traversal_entry`: fixture with a workspace entry whose path
  is `spec/../../../etc/passwd`; `analyze_bounded` result has
  `declared_spec_files_read == 0` (confinement via `_safe_spec_path()` rejects the path,
  returns None, file is not read); no exception raised; result is structurally valid
  (AC1 security invariant — `_safe_spec_path()` guard is active in bounded mode)

Call-site counts are verified behaviorally by AC10/AC11 fixture tests rather than
brittle source-grep counts; see `test_ac10_bounded_structural_cost` and
`test_ac11_full_structural_cost` in the CLI tests section below.
- `test_explain_cli_ambiguous_exit0`: CLI invocation with two-initiative fixture where
  slug exists in both; exit code 0; JSON has `selector_status: "ambiguous"`
- `test_explain_missing_item_arg`: `explain --root <dir>` with no `--item`; exit code 2;
  stderr non-empty; stdout empty (AC14b)

**T3 (CLI) — subcommand tests added to `tools/test_workspace_status_cli.py`:**
- `test_status_subcommand_mode_field`: JSON has `"mode": "status"`
- `test_status_subcommand_no_global_scan`: `scan.global_spec_scan_performed: false`,
  `scan.global_scan_spec_files_read: 0`
- `test_status_bounded_type1_absent`: fixture with M untracked live specs;
  `reconciliation.type1 == []` in status mode; `reconciliation.types_performed == [2, 3]`
- `test_reconcile_subcommand_mode_field`: JSON has `"mode": "reconcile"`
- `test_reconcile_subcommand_global_scan`: `scan.global_spec_scan_performed: true`;
  `reconciliation.types_performed == [1, 2, 3]`
- `test_ac10_bounded_structural_cost`: N declared + M untracked;
  `global_scan_spec_files_read == 0` and `declared_spec_files_read <= N` in status mode
- `test_ac11_full_structural_cost`: same fixture; `global_scan_spec_files_read >= M`
  in reconcile mode
- `test_no_subcommand_compatibility`: exit 0; stdout identical to reconcile output;
  `mode: "reconcile"` in JSON
- `test_no_subcommand_stderr_warning`: stderr contains deprecation text; stdout empty
  of warning
- `test_explain_matched`: valid selector; `selector_status: "matched"`, `explained_item`
  present with all required keys; `scan.global_scan_spec_files_read == 0` (AC10 explain
  coverage — explain inherits `analyze_bounded`, so the global walk is structurally absent)
- `test_explain_not_found`: unknown selector; exit 0; `selector_status: "not_found"`
- `test_reconciliation_metadata_fields`: status and reconcile modes include `performed`,
  `complete`, `types_performed` in `reconciliation` object; explain mode is excluded (its
  JSON payload has no `reconciliation` key — see `_build_explain_json` in LLD and AC13)
- `test_scan_field_present`: all modes include `scan` object with four required keys
  (`global_spec_scan_performed`, `workspace_files_read`, `declared_spec_files_read`,
  `global_scan_spec_files_read`)
- `test_diagnostics_compat`: for status and reconcile modes only: `diagnostics.spec_files_read`
  equals `scan.declared_spec_files_read + scan.global_scan_spec_files_read`; explain mode
  JSON does not include `diagnostics` (focused projection)
- `test_absent_workspace_mode_field`: each subcommand returns `mode` in absent-workspace
  JSON payload
- `test_cli_no_writes_all_modes`: write-snapshot assertion for status, reconcile, explain

## Design (LLD)

### Engine changes (`workspace_status_engine.py`)

**`_run_type1_scan(root, all_tracked) -> tuple[list[ReconciliationFinding], int]`** *(new)*
- Extracted verbatim from the Type 1 block in `run_reconciliation`
- Call-site count: see AC1 (canonical definition; not restated here to avoid drift)
- Accepts `all_tracked: set[str]`; returns `(findings, files_read)`

**`_run_type23_scan(root, initiatives) -> tuple[list[ReconciliationFinding], int]`** *(new)*
- Extracted verbatim from the Type 2 + Type 3 blocks in `run_reconciliation`
- Call-site count: see AC1 (canonical definition; not restated here to avoid drift)
- All path resolution goes through `_safe_spec_path()` (inherited, not re-implemented)
- Returns `(findings, files_read)`

**`run_reconciliation(root, initiatives) -> tuple[list[ReconciliationFinding], int]`** *(refactored, same signature)*
- Body becomes: call `_run_type1_scan` + `_run_type23_scan`, merge results
- Semantics unchanged; `files_read` total unchanged (sum of both helpers' counts)
- Kept for backward compatibility with existing test callers that call `run_reconciliation` directly

**`WorkspaceStatusResult` — field changes** *(spec Assumption: one constructor call site)*
```python
# Remove: files_read: int
# Add AFTER elapsed_s and top_level_backlog (defaulted fields must follow non-defaulted):
global_scan_performed: bool = dataclasses.field(default=False)
declared_spec_files_read: int = dataclasses.field(default=0)
global_scan_files_read: int = dataclasses.field(default=0)

@property
def files_read(self) -> int:   # backward compat for existing result.files_read callers
    return self.declared_spec_files_read + self.global_scan_files_read
```
Constructor kwarg `files_read=` removed; `analyze()` updated to pass the two new fields.

**`analyze_bounded(root: Path) -> WorkspaceStatusResult`** *(new)*
```python
workspace = parse_workspace(workspace_path)
initiatives = extract_initiatives(workspace)
# classify (identical to analyze())
findings, declared_files = _run_type23_scan(root, initiatives)
top_level_backlog = extract_top_level_backlog(workspace)
return WorkspaceStatusResult(
    ...,
    global_scan_performed=False,
    declared_spec_files_read=declared_files,
    global_scan_files_read=0,
)
```

**`analyze(root: Path) -> WorkspaceStatusResult`** *(existing — call sites updated)*
```python
# Existing parse + classify unchanged
all_tracked = {e.path for ini in initiatives for e in ini.work.queue + ini.work.active + ini.work.shipped}
# Call helpers directly (not via run_reconciliation) to obtain split file counts:
type1_findings, type1_files = _run_type1_scan(root, all_tracked)
type23_findings, type23_files = _run_type23_scan(root, initiatives)
reconciliation = type1_findings + type23_findings
...
return WorkspaceStatusResult(
    ...,
    global_scan_performed=True,
    declared_spec_files_read=type23_files,
    global_scan_files_read=type1_files,
)
```

**`explain_item(result: WorkspaceStatusResult, selector: str) -> dict`** *(new)*
- Normalize: `slug = normalize_for_shaping_guard(selector)` (reuses existing helper)
- Selector is never joined into a filesystem path — in-memory lookup only
- Build path for work-queue match: `f"spec/{slug}"`
- Work-queue-only lookup (no shaping search):
  1. Build path: `f"spec/{slug}"`
  2. Check each active initiative (status="active"): work.active, work.shipped, work.queue
  3. Collect matching initiatives (by ini_slug); count distinct initiatives
     - 1 distinct ini → `matched`; resolve list/classification: active > shipped > queue
       (slug in both active and shipped → list="active", classification="active")
     - 0 inis → `not_found` (includes shaping-only and paused-initiative items)
     - 2+ inis → `ambiguous` with matches list (one entry per ini, slug + ini_slug)
- `downstream_unblocked`: entries in `result.blocked` where `ini_slug == matched.ini_slug`
  AND `blocking_needs == [f"work:{matched.path}"]` (sole remaining blocker, same initiative)
- Returns a dict; does not return `WorkspaceStatusResult`

### CLI changes (`workspace_status.py`)

**Subcommand routing — manual pre-dispatch:**
```python
_SUBCOMMANDS = frozenset({"status", "explain", "reconcile"})

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    argv = list(argv)

    # Pre-dispatch: first token is a known subcommand → strip it
    if argv and argv[0] in _SUBCOMMANDS:
        subcommand = argv.pop(0)
        compat_alias = False
    else:
        subcommand = "reconcile"    # backward-compat default
        compat_alias = True

    if compat_alias:
        print(
            "workspace-status: no subcommand specified; defaulting to reconcile. "
            "Use 'reconcile' explicitly.",
            file=sys.stderr,
        )
    # Parse --root (and --item for explain) from remaining argv
    ...
```

This preserves `--root <dir>` (no subcommand) for existing callers with no argparse changes to `--root` handling.

**`_build_json(root, result, mode) -> dict`** (extend signature, add `mode` arg):
- Add `"mode"` top-level key
- Add `"scan"` top-level object:
  - `global_spec_scan_performed`: `result.global_scan_performed`
  - `workspace_files_read`: 1
  - `declared_spec_files_read`: `result.declared_spec_files_read`
  - `global_scan_spec_files_read`: `result.global_scan_files_read`
- Add to `reconciliation` object (additive):
  - `performed`: `True` (always — Type 2+3 always run)
  - `complete`: `result.global_scan_performed` (True only in reconcile)
  - `types_performed`: `[1, 2, 3]` if global_scan else `[2, 3]`
- Keep `diagnostics` unchanged: `spec_files_read = result.files_read`
- Add `mode` to the absent-workspace JSON payload

**`_build_explain_json(root, result, selector, explain_result) -> dict`** *(new)*:
- Top-level: `mode`, `workspace_present`, `workspace_root`, `scan`, `selector`, `selector_status`
- When matched: also `explained_item`
- Does NOT include `work`, `shaping`, or `reconciliation` arrays

### SKILL.md changes

- §1 invocation: change to `status` subcommand
- Key fields: add `mode`, `scan.*`, `reconciliation.performed/complete/types_performed`
- §2 "Untracked live specs" block: gate display on `1 in reconciliation.types_performed`;
  when absent emit: "_Type 1 scan not performed (status mode) — run `reconcile` to find untracked specs_"
- Add: "To audit untracked specs or drift, use `reconcile` subcommand"
- Add: "To investigate a specific item, use `explain --item <selector>`"

### Interfaces and contracts

JSON additive extension (schema_version stays 1 — backward-compatible additions only):

Scan field names use `global_scan_spec_files_read` (not `reconciliation_spec_files_read`)
to avoid implying Type 2+3 reads are excluded from reconciliation.

```json
{
  "schema_version": 1,
  "mode": "status",
  "scan": {
    "global_spec_scan_performed": false,
    "workspace_files_read": 1,
    "declared_spec_files_read": 48,
    "global_scan_spec_files_read": 0
  },
  "reconciliation": {
    "performed": true,
    "complete": false,
    "types_performed": [2, 3],
    "type1": [],
    "type2": [...],
    "type3": [...],
    "type2_cleanup_ops": [...]
  },
  "diagnostics": {
    "workspace_files_read": 1,
    "spec_files_read": 48
  }
}
```

Explain mode JSON (mode-specific payload; no work/shaping/reconciliation arrays):
```json
{
  "schema_version": 1,
  "mode": "explain",
  "workspace_present": true,
  "workspace_root": "...",
  "scan": { "global_spec_scan_performed": false, ... },
  "selector": "spec/m1-workspace-core",
  "selector_status": "matched",
  "explained_item": {
    "path": "spec/m1-workspace-core",
    "slug": "m1-workspace-core",
    "ini_slug": "ini-002",
    "list": "queue",
    "classification": "ready",
    "blocking_needs": [],
    "dependencies": [{"need": "work:spec/m0-foundation", "satisfied": true}],
    "downstream_unblocked": ["spec/m2-foo"]
  }
}
```

## Tasks

### T1: Spec + Plan (this task)

- **Mode:** goal-based check
- **Done when:** both files exist and pre-EXECUTE reviewers return Clean
- **Tests:** none (documents only)

### T2: Engine — scan helpers, bounded analysis, explain

- **Mode:** TDD
- **Tests (red stubs written before T2 implementation):** see Construction tests section
- **Approach:** Extract `_run_type1_scan` and `_run_type23_scan`; update `WorkspaceStatusResult`
  fields (remove `files_read` field, add three new fields, add `files_read` property);
  update `analyze()` constructor call; add `analyze_bounded()`; add `explain_item()`
- **Done when:** all T2 red stubs green; no regressions in existing tests

### T3: CLI — subcommand routing and JSON extension

- **Mode:** TDD
- **Tests (red stubs written before T3 implementation):** see Construction tests section
- **Approach:** Add `_SUBCOMMANDS` pre-dispatch; extend `_build_json` signature; add
  `_build_explain_json`; add `--item` arg parsing for explain mode
- **Done when:** all T3 red stubs green; all Order 1A CLI tests still pass

### T4: SKILL.md update

- **Mode:** goal-based check
- **Done when:**
  - `status` subcommand in §1 invocation (grep)
  - `types_performed` gate in reconciliation rendering block
  - `reconcile` guidance present (exhaustive audit trigger)
  - `explain` guidance present, including note that shaping items and paused-initiative
    items return `not_found` (AC14a)
  - New `mode` and `scan` fields present in Key fields section

### T5: Build and manual verification

- **Mode:** visual / manual QA
- **Done when:** `make build-self` passes; `make ci` passes; each mode invoked against
  repo's workspace.toml and output recorded

## Changelog

| Date | Change | Reason |
|------|--------|--------|
| Initial | First draft | Order 1B spec authoring |
| Rev 2 | Extracted `_run_type23_scan`; fixed file-count tracking; resolved AC2/AC13 contradiction (work-first precedence); specified argv pre-dispatch; renamed `reconciliation_spec_files_read` → `global_scan_spec_files_read`; added AC10/AC11 fixture tests; defined active/shipped classification; defined downstream_unblocked (sole-remaining-blocker); added cross-initiative ambiguity; added absent-workspace mode field; noted `files_read` field→property constructor edit; noted reuse of `normalize_for_shaping_guard` | Adversarial + security review findings (pass 1) |
| Rev 3 | Fixed AC1 call-site count (one for type1, two for type23); changed AC2/AC3 from `=` to `≤`/`≥`; added active-initiative filter to explain_item lookup; ambiguity counts distinct initiatives not raw matches; added within-ini duplicate test; restricted downstream_unblocked to same ini_slug; fixed call-site grep to exclude `def` lines; renamed test_type23_single_call_site; clarified subcommand-first argv ordering; qualified Order 1A AC8 reference | Adversarial review findings (pass 2) |
| Rev 4 | Corrected call-site counts: type1=2 (run_reconciliation+analyze), type23=3 (run_reconciliation+analyze+analyze_bounded); annotated AC6/AC7 JSON examples with ≤/≥; restricted explain to work-queue-only (no shaping search); added CLI-level ambiguous exit-0 test; noted defaulted field placement after elapsed_s; noted analyze() calls helpers directly (not run_reconciliation) for split counts; added SKILL.md active-only scope note | Adversarial review findings (pass 3) |
| Rev 5 | Scoped AC13 (diagnostics) to status+reconcile modes; Boundaries references AC1 for call-site counts; added AC14b (missing --item exit behavior); added active>shipped>queue list/classification precedence in AC5 and LLD; dropped brittle source-grep call-site tests in favor of behavioral AC10/AC11 proof; moved engine unit tests to test_workspace_status.py; added T4 done-when for AC14a | Adversarial review findings (pass 4) |
| Rev 6 | Scoped `test_reconciliation_metadata_fields` to status+reconcile (explain has no reconciliation object); added `global_scan_spec_files_read == 0` assertion to `test_explain_matched` (AC10 explain coverage); added `test_analyze_bounded_path_traversal_entry` confinement test; replaced LLD call-site counts with "see AC1" references to prevent drift | Adversarial review findings (pass 5) |
