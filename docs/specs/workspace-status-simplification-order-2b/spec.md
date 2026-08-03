# Spec: workspace-status simplification — Order 2B

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (write-authority boundary + public-interface change + multi-feature/dependent tasks + workspace.toml mutation without comment loss)
- **Constrained by:**
  - [RFC-0049](../../rfc/0049-the-release-loop-and-company-os.md) — Company OS architecture authority
  - [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md) — workspace.toml schema and workspace-status behavior authority
  - `packs/core/.apm/skills/workspace-status/SKILL.md` — production behavior
  - `docs/specs/workspace-status-simplification-order-1b/spec.md` — Order 1B contract; architectural baseline preserved
- **Contract:** none (internal skill interface only)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Extend the installed, self-contained `workspace-status` backend with two
progressive repair modes that complete the five-command surface:

| Subcommand | Scope | Writes |
|---|---|---|
| `status` | Bounded — Type 2+3, declared entries only | No |
| `explain` | Focused projection from bounded result | No |
| `reconcile` | Exhaustive — Type 1+2+3 | No |
| `repair-plan` | Exhaustive reconciliation → read-only plan of Type 2 queue operations | No |
| `repair-apply` | Explicit apply of an unchanged plan against verified workspace state | Yes |

Use the existing `scripts/workspace_status.py` CLI and
`scripts/workspace_status_engine.py` engine. Do not create a separate skill.

### Architectural boundary

Order 2B is a narrow safety envelope around the legacy Type 2 queue cleanup
surface. It is not a generic repair framework, schema migration, active-run
manager, runtime claim system, or replacement for work-loop.

Order 3A and Order 3B will later redesign lifecycle ownership. Keep Order 2B
small enough that its list operations can be removed cleanly in that migration.

## Prerequisite gate evidence

Verified in current production sources before authoring this spec:

1. **`status` is the bounded default path.** `analyze_bounded` never calls
   `_run_type1_scan`; `SKILL.md` invokes the `status` subcommand.
   (`workspace_status_engine.py:716`, `workspace_status.py:306–308`)

2. **`explain` is a bounded projection.** Routes to `analyze_bounded` then
   `explain_item`; no file I/O beyond the bounded scan.
   (`workspace_status.py:302–305`)

3. **`reconcile` is exhaustive read-only Type 1/2/3.** `analyze()` calls
   `_run_type1_scan` + `_run_type23_scan`; no write path.
   (`workspace_status_engine.py:665–714`)

4. **work-loop no longer performs portfolio stale-state reconciliation.**
   `work-loop/SKILL.md` Step 0 emits a per-spec stale warning only for the
   spec currently being worked; no portfolio-wide scan is performed.
   `workspace_status_engine.py:972–1000` documents the distinction.

5. **Reconciliation returns required metadata.** `ReconciliationFinding` carries
   `finding_type`, `ini_slug`, `list_name` (exact source list), `spec_path`
   (canonical path), and `spec_status` (observed status). `compute_type2_cleanup`
   derives cleanup eligibility from these fields.
   (`workspace_status_engine.py:101–108`, `1047–1093`)

6. **Scripts are self-contained and projected.** Both scripts are in
   `packs/core/.apm/skills/workspace-status/scripts/`; `build-self` projects them
   to all supported adapters. No runtime imports from shared-libs or siblings.

7. **Canonical spec vocabulary.** `VALID_STATUSES = frozenset({"Draft",
   "Approved", "Implementing", "Shipped", "Archived"})` at engine line 291.

## Repair eligibility policy

### Automatically planable operations

Only Type 2 findings from `work.queue` are automatically planable:

| Finding | Source | Spec status | Operation |
|---|---|---|---|
| Type 2 | `work.queue` | `Shipped` | Remove from queue; append bare string to `work.shipped` if absent |
| Type 2 | `work.queue` | `Archived` | Remove from queue only |

A path that appears more than once in the same `work.queue` list is a duplicate
and is not automatically planable — route all findings for that path to
`manual_findings` with `reason="type2-queue-duplicate"`.

### Manual findings

No automatic operation for:

| Finding | Source | Spec status | Reason |
|---|---|---|---|
| Type 1 | any | `Approved` / `Implementing` | Untracked — human queue/archive decision |
| Type 2 | `work.active` | any | May represent a live work-loop; human only |
| Type 3 | any | `Approved` / `Implementing` | Premature shipment — ambiguous cause |
| Any | any | `Draft` | Not yet approved |
| Any | any | `Unknown` / missing / malformed | Diagnostic only |
| Type 2 `work.queue` | any | Duplicate path (same ini, same source list) | Manual ambiguity |

A path appearing in both `work.queue` and `work.active` with `Shipped` status
yields one automatic queue operation AND one manual active-source finding.
Do not collapse the active-source finding.

### Approved lifecycle invariant

`Approved` means live implementation intent — never equivalent to Shipped:

- Never automatically removed from queue
- Never automatically appended to `work.shipped`
- The presence of an `Approved` spec in queue or active is not a Type 2 finding;
  it is not eligible for automatic repair

Only reconciliation Type 2 findings with observed status `Shipped` or `Archived`
may be candidates for deterministic repair.

## Boundaries

### Always do

- Add `compute_repair_plan(result, workspace_path)` to the engine (stdlib-only):
  filters `result.type2` to `list_name == "queue"` entries; builds `RepairPlan`
  with `automatic_operations` and `manual_findings`; performs duplicate detection.
- Add `RepairOperation` and `ManualFinding` dataclasses to the engine.
- Add `"repair-plan"` and `"repair-apply"` to `_SUBCOMMANDS` in the CLI.
- `repair-plan` invokes `analyze(root)` (exhaustive reconciliation); builds the
  plan via `compute_repair_plan`; writes the plan JSON to disk (default:
  `<root>/.workspace-repair-plan.json`, overridable with `--plan-file`); also
  emits the same JSON to stdout.
- `repair-apply` reads the plan file; validates its schema; verifies the
  workspace fingerprint; re-verifies each operation's spec status from disk;
  applies each automatic operation using tomlkit for comment-preserving write;
  emits a result JSON to stdout.
- **Fingerprint**: SHA-256 (hexdigest) of `workspace.toml` raw bytes at plan
  time. Read the file once into bytes; verify SHA-256; pass the same bytes to
  `tomlkit.parse()` — never open `workspace.toml` a second time between
  fingerprint check and parse (eliminates TOCTOU window).
- **Spec-status re-verification at apply time**: before writing, re-read each
  automatic operation's `spec.md` and assert the observed status still matches
  the plan's recorded `spec_status`. If any status has changed (e.g.,
  Shipped→Approved between plan and apply), skip that operation and report it as
  `{"op": ..., "skipped": true, "reason": "spec_status_changed"}` in the result.
- **Atomic write**: create the temp file via `tempfile.mkstemp(dir=workspace_path.parent,
  prefix=".workspace.toml.", suffix=".tmp")` (unpredictable name; `O_CREAT|O_EXCL`
  prevents symlink follow); write content; call `os.replace(tmp, workspace_path)`;
  unlink the temp file in `finally` if `os.replace` fails.
- **Path confinement — plan file**: the resolved `--plan-file` path must be
  inside `root.resolve()` for both `repair-plan` (write) and `repair-apply`
  (read); symlink-escape check mirrors the existing `workspace.toml` confinement
  in `workspace_status.py:292–300`. Violation → exit 2.
- **Path confinement — write target**: `repair-apply`'s write target
  (`workspace.toml`) and temp file must resolve within `root.resolve()`.
- **Plan JSON structural validation**: `repair-apply` validates `schema_version
  == 1`, `automatic_operations` is a list, each operation has valid
  `operation_type` (allow-list: `"queue-to-shipped"` or `"queue-remove"`),
  `spec_path` is a non-empty string, and `ini_slug` is a non-empty string.
  Unknown `operation_type` → exit 2 with `reason="plan_invalid"`.
- **Duplicate detection**: `compute_repair_plan` detects paths appearing more
  than once in the same initiative's `work.queue` Type 2 findings and routes all
  occurrences to `manual_findings` with `reason="type2-queue-duplicate"`.
- **tomlkit dependency**: tomlkit handles comment-preserving TOML writes in
  `repair-apply`; imported only in the CLI write path, not in the engine.
  Import guarded: `ImportError` → exit 2, `reason="tomlkit_unavailable"`.
- **In-place queue mutation**: remove matched entries from the existing tomlkit
  array in place (`del queue[i]`) rather than reconstructing the array, to
  preserve per-entry inline comments and multiline formatting.
- **Add to `.gitignore`**: append `.workspace-repair-plan.json` and
  `.workspace.toml.*.tmp` to `.gitignore` so the plan file and any temp files
  are never accidentally committed.
- Keep `workspace_status_engine.py` stdlib-only; tomlkit lives in the CLI only.
- Preserve `compute_type2_cleanup` with no change (backward compat for SKILL.md
  cleanup-offer rendering which uses `type2_cleanup_ops`).
- `repair-plan --root <dir>` exits 0 even when `automatic_operations` is empty;
  the plan is still written (zero-op plan is a valid answer).
- `repair-apply` with an empty `automatic_operations` list exits 0 with
  `{"applied": true, "operations_applied": 0}`.
- `repair-apply` when `workspace.toml` is absent: exit 2 with
  `{"applied": false, "reason": "workspace_absent"}`.
- Add new subcommand tests to `tools/test_workspace_status_cli.py`.
- Add engine unit tests to `tools/test_workspace_status.py`.
- Update the stdlib-only allowlist in `tools/test_workspace_status_cli.py`
  (`_STDLIB_MODULES`) to include `hashlib` and `datetime`; add `tomlkit` as an
  explicit CLI-only blessed exception.
- Update `SKILL.md` §1a subcommand table with `repair-plan` and `repair-apply`
  entries; add §1b or equivalent with invocation guidance.
- Run `make build-self` after editing `packs/`; verify projection is unchanged.

### Ask first

- Any change to workspace.toml schema
- Any change to the fingerprint algorithm after the spec is approved
- Changing `compute_type2_cleanup` behavior or its returned shape
- Any write path for `work.active` source entries in Order 2B

### Never do

- Automatic `work.active` removal — any finding with `list_name == "active"` is
  always a manual finding, never an automatic operation
- Treat `Approved` as completion — see Approved lifecycle invariant above
- Create a separate repair skill or separate reconciliation logic
- Add `repair-plan` or `repair-apply` to the engine's entry-point docstring
  functions (they are CLI-level, not engine entry points)
- Use `tomllib` + `tomli_w` (strips comments)
- Use `shell=True` in any subprocess call
- Change or remove `compute_type2_cleanup` (existing SKILL.md cleanup path)
- Store the plan inside the spec dir or any git-tracked path by default
- Add any dependency other than `tomlkit` (already available)
- Move either script out of `scripts/`
- Change workspace.toml schema

## Plan file schema

Written to `<root>/.workspace-repair-plan.json` by default. The plan file
contains the **same JSON** emitted on stdout — it is the full merged output of
`_build_json(root, result, "repair-plan")` plus plan fields (`workspace_fingerprint`,
`planned_at`, `automatic_operations`, `manual_findings`). The example below is
abridged; the real file also contains `workspace_present`, `scan`, `work`,
`shaping`, and `reconciliation` keys from the `_build_json` merge.

```json
{
  "schema_version": 1,
  "mode": "repair-plan",
  "workspace_present": true,
  "workspace_root": "<absolute path>",
  "workspace_fingerprint": "<sha256-hex>",
  "planned_at": "<iso8601>",
  "... (scan, work, shaping, reconciliation keys from _build_json merge) ...": "...",
  "automatic_operations": [
    {
      "operation_type": "queue-to-shipped",
      "spec_path": "spec/my-feature",
      "spec_status": "Shipped",
      "ini_slug": "ini-002"
    },
    {
      "operation_type": "queue-remove",
      "spec_path": "spec/old-feature",
      "spec_status": "Archived",
      "ini_slug": "ini-002"
    }
  ],
  "manual_findings": [
    {
      "finding_type": 2,
      "spec_path": "spec/in-progress",
      "spec_status": "Shipped",
      "ini_slug": "ini-002",
      "list_name": "active",
      "reason": "type2-active-source"
    }
  ]
}
```

`operation_type`:
- `"queue-to-shipped"` — remove from `work.queue`, append bare string to `work.shipped` if absent
- `"queue-remove"` — remove from `work.queue` only (Archived)

`reason` values for `manual_findings`:
- `"type1-untracked"` — Type 1: untracked live spec
- `"type2-active-source"` — Type 2 with source `active`
- `"type3-premature"` — Type 3: prematurely shipped
- `"type2-queue-duplicate"` — Type 2 queue path appearing >1 time in same ini
- `"type2-queue-approved"` — Type 2 from queue with `Approved` status (should not occur; defensive)
- `"type2-queue-draft"` — Type 2 from queue with `Draft` status (should not occur; defensive)

## Testing Strategy

- **TDD** — engine: `compute_repair_plan` with Type 2 queue Shipped, Archived, active-source variants; plan fingerprint generation; `RepairOperation` / `ManualFinding` shapes. CLI: `repair-plan` JSON contract, `repair-apply` apply + fingerprint mismatch + empty plan + zero-op plan + write-snapshot. Tests written as red stubs before implementation.
- **Goal-based check** — `make build-self` passes; `repair-plan` and `repair-apply` appear in SKILL.md §1a table (grep).
- **Visual / manual QA** — `repair-plan` invoked against this repo's `workspace.toml`; plan JSON inspected for correctness; `repair-apply` invoked against a fixture workspace.toml and post-write diff verified.

## Acceptance Criteria

### Engine additions

- [x] AC1. `RepairOperation` dataclass exists in the engine with fields:
  `operation_type: str`, `spec_path: str`, `spec_status: str`, `ini_slug: str`.
  `operation_type` is `"queue-to-shipped"` when `spec_status == "Shipped"` and
  `"queue-remove"` when `spec_status == "Archived"`.

- [x] AC2. `ManualFinding` dataclass exists in the engine with fields:
  `finding_type: int`, `spec_path: str`, `spec_status: str`, `ini_slug: str`,
  `list_name: str`, `reason: str`.

- [x] AC3. `RepairPlan` dataclass (or equivalent structure) exists in the engine
  with fields: `automatic_operations: list[RepairOperation]`,
  `manual_findings: list[ManualFinding]`, `workspace_fingerprint: str`,
  `planned_at: str`.

- [x] AC4. `compute_repair_plan(result, workspace_path)` exists in the engine.
  Given a `WorkspaceStatusResult` from `analyze()`:
  - **Duplicate detection first**: for each initiative, build a set of paths that
    appear more than once in `result.type2` entries with `list_name == "queue"`
    for that `ini_slug`. All Type 2 queue findings for a duplicate path route to
    `manual_findings` with `reason="type2-queue-duplicate"`.
  - For non-duplicate Type 2 queue findings:
    - `spec_status == "Shipped"` → `RepairOperation(operation_type="queue-to-shipped", ...)`
    - `spec_status == "Archived"` → `RepairOperation(operation_type="queue-remove", ...)`
  - All other findings become `ManualFinding` entries:
    - `list_name == "active"` Type 2 → `reason="type2-active-source"`
    - Type 1 → `reason="type1-untracked"`
    - Type 3 → `reason="type3-premature"`
  - `workspace_fingerprint` = SHA-256 hexdigest of `workspace_path.read_bytes()`.
  - `planned_at` = timezone-aware UTC ISO8601 with explicit `+00:00` offset, e.g.
    `datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")`
    which produces the form `"2026-08-02T12:00:00+00:00"` (never `"Z"`).
  - A path in both `work.queue` and `work.active` with `Shipped` status yields one
    `RepairOperation` (for the queue finding) and one `ManualFinding` with
    `reason="type2-active-source"` (for the active finding). Never collapses.

- [x] AC5. `compute_repair_plan` is stdlib-only (no import of tomlkit, requests,
  or any third-party library).

### CLI — repair-plan

- [x] AC6. `workspace_status.py repair-plan --root <dir>` (or
  `--root <dir> --plan-file <path>`) exits 0; stdout is valid UTF-8 JSON with:
  - `"schema_version": 1`
  - `"mode": "repair-plan"`
  - `"workspace_present": true`
  - `"workspace_root": "<absolute-path>"`
  - `"workspace_fingerprint": "<sha256-hex>"`
  - `"planned_at": "<iso8601+00:00>"`
  - `"automatic_operations": [...]` (list of dicts; `RepairOperation` dataclasses serialized via `dataclasses.asdict()`)
  - `"manual_findings": [...]` (list of dicts; `ManualFinding` dataclasses serialized via `dataclasses.asdict()`)

- [x] AC7. When `automatic_operations` is empty (no automatically planable Type 2
  queue findings), `repair-plan` still exits 0 and still writes the plan file.
  The JSON `automatic_operations` array is `[]`.

- [x] AC8. `repair-plan` writes the plan JSON to
  `<root>/.workspace-repair-plan.json` by default. `--plan-file <path>` overrides
  the output path. Stdout is emitted first; the plan file write follows. If the
  file write fails, stdout has already been emitted (plan is available to the
  caller); exit code is 2 on file write failure (AC26).

- [x] AC9. `repair-plan --root <dir>` where `<dir>` has no `workspace.toml`
  exits 1 with `{"schema_version": 1, "mode": "repair-plan", "workspace_present":
  false, "workspace_root": "<abs-path>"}` on stdout.

- [x] AC10. The `scan` field in `repair-plan` JSON output reflects the exhaustive
  reconciliation (`global_spec_scan_performed: true`,
  `reconciliation.types_performed: [1, 2, 3]`) — `repair-plan` uses `analyze()`
  not `analyze_bounded()`.

### CLI — repair-apply

- [x] AC11. `workspace_status.py repair-apply --root <dir>` reads the plan from
  `<root>/.workspace-repair-plan.json` by default. `--plan-file <path>` overrides.

- [x] AC12. `repair-apply` single-read fingerprint verification: reads
  `workspace.toml` once into bytes; computes SHA-256 hexdigest; compares to
  `workspace_fingerprint` in the plan file; passes those same bytes to
  `tomlkit.parse()` — no second open of `workspace.toml` between verification
  and parse (TOCTOU elimination). On mismatch: exits 2; stderr includes
  "fingerprint mismatch" (no absolute path leaked); stdout is
  `{"schema_version": 1, "mode": "repair-apply", "applied": false,
  "reason": "fingerprint_mismatch"}`.

- [x] AC12a. `repair-apply` validates plan JSON structure before applying:
  - `schema_version == 1`; `automatic_operations` is a list.
  - Each operation has `operation_type` in `{"queue-to-shipped", "queue-remove"}`,
    non-empty `spec_path` (no `..` components, not an absolute path), non-empty `ini_slug`.
  - `operation_type` ↔ `spec_status` coupling: `"queue-to-shipped"` is valid only
    when `spec_status == "Shipped"`; `"queue-remove"` only when `spec_status == "Archived"`.
    A mismatched pair → `reason="plan_invalid"`.
  - Unknown `operation_type` or missing required field → exit 2 with `reason="plan_invalid"`.
  - `spec_path` containing `..` or an absolute component → exit 2 with `reason="plan_invalid"`.

- [x] AC12b. `repair-apply` re-verifies each operation's spec status from disk
  before writing. For each automatic operation:
  - Derive the slug from `spec_path` and route through the engine's `_safe_spec_path(root, slug)`;
    this function returns the `spec.md` Path if it resolves within `root/docs/specs/`, or `None`
    on traversal (`..`) or escape — skip with `reason="spec_status_unreadable"` on `None`.
  - Re-read `docs/specs/<slug>/spec.md`; extract `Status:` using `extract_spec_status`.
  - If status cannot be read → skip with `reason="spec_status_unreadable"`.
  - **Re-derive** the action from the disk-verified status (not from the plan's
    `operation_type`): `Shipped` → `queue-to-shipped`; `Archived` → `queue-remove`;
    any other status (including `Approved`) → skip with `reason="spec_status_changed"`.
  - If the disk status no longer matches `spec_status` in the plan → skip with
    `reason="spec_status_changed"`.
  - `per_operation` array in result JSON records each skipped op as
    `{"path": ..., "applied": false, "reason": "<reason>"}`.
  - `applied: true` overall; `operations_applied` counts only successfully-written ops.

- [x] AC13. `repair-apply` with a valid fingerprint and non-empty
  `automatic_operations` applies each operation using tomlkit:
  - `"queue-to-shipped"`: remove the entry from `work.queue` in place (bare or
    inline-object form, matched by `path` field); append bare string to
    `work.shipped` if key exists and path absent; create `work["shipped"]` array
    if the key is absent; deduplication by path.
  - `"queue-remove"`: remove the entry from `work.queue` in place; nothing appended.
  - Writes atomically only when `applied > 0`: `tempfile.mkstemp(dir=workspace_path.parent, prefix=".workspace.toml.", suffix=".tmp")`; write content via the returned fd; close fd; `os.replace(tmp, workspace_path)`; `finally` unlink temp if `os.replace` failed. When all operations are skipped (`applied == 0`), no mkstemp call is made and workspace.toml is not touched.
  - `per_operation` array is present on every `applied: true` result (including
    the empty-ops case); it records every operation — applied ops as
    `{"path":..., "applied":true}` and skipped ops as
    `{"path":..., "applied":false, "reason":"..."}`. It is non-empty whenever
    `automatic_operations` is non-empty. Error shapes (`applied: false`) do not
    carry `per_operation`.
  - Exits 0; stdout is `{"schema_version": 1, "mode": "repair-apply",
    "applied": true, "operations_applied": N, "per_operation": [...]}` where N = operations successfully written.

- [x] AC14. `repair-apply` with an empty `automatic_operations` list exits 0
  without writing to `workspace.toml` (verified by SHA-256 equality or mtime
  check, not just absence of exception); stdout is
  `{"schema_version": 1, "mode": "repair-apply", "applied": true,
  "operations_applied": 0, "per_operation": []}`. The short-circuit must happen
  before any `tempfile.mkstemp` call. Fingerprint verification still precedes
  the empty-ops short-circuit — a stale fingerprint exits 2 `fingerprint_mismatch`
  even on an empty `automatic_operations` list.

- [x] AC15. When plan file is not found: exits 2; stderr includes "plan file not
  found" without leaking absolute paths; stdout is `{"schema_version": 1, "mode":
  "repair-apply", "applied": false, "reason": "plan_file_not_found"}`.

- [x] AC16. When plan file exists but is malformed JSON or fails structural
  validation: exits 2; stderr includes the specific issue without leaking
  absolute paths; stdout is `{"schema_version": 1, "mode": "repair-apply",
  "applied": false, "reason": "plan_file_parse_error"}` for malformed JSON or
  `reason="plan_invalid"` for structural validation failure.

- [x] AC16a. `repair-apply` when `workspace.toml` is absent at apply time: exits
  2 with `{"schema_version": 1, "mode": "repair-apply", "applied": false,
  "reason": "workspace_absent"}`. **Implementation note:** the shared absent-workspace
  guard at `workspace_status.py:279-288` runs before subcommand dispatch and exits 1
  for all subcommands. This guard must be gated off for `repair-apply` (e.g.
  `if subcommand != "repair-apply":` around lines 279-300 and the symlink guard),
  so the repair-apply branch owns its own workspace-presence and confinement checks
  with the correct exit-2/`applied:false` shape. The shared guard's exit-1 remains
  correct for all other subcommands (AC9 for repair-plan correctly wants exit 1).

- [x] AC16b. `repair-apply` when tomlkit is unavailable: exits 2 with
  `{"schema_version": 1, "mode": "repair-apply", "applied": false,
  "reason": "tomlkit_unavailable"}`. Verified by a test that invokes the CLI
  in a subprocess with tomlkit shadowed (a `PYTHONPATH`-prefixed stub that raises
  `ImportError` on `import tomlkit`).

- [x] AC16c. Write-target confinement: inside the repair-apply branch (after the
  shared guard is gated off per AC16a), verify
  `(root / "workspace.toml").resolve().relative_to(root.resolve())` — a symlinked
  `workspace.toml` pointing outside `root` triggers exit 2 with
  `{"schema_version":1, "mode":"repair-apply", "applied":false,
  "reason":"workspace_outside_root"}`. This is subcommand-aware and distinct from the
  shared `workspace_status.py:292-300` guard (which has no stdout JSON shape).

- [x] AC16d. `--plan-file` path confinement: the resolved plan-file path must be
  inside `root.resolve()` for both `repair-plan` (write) and `repair-apply`
  (read). The check is unconditional `resolved_path.relative_to(root.resolve())`
  — it covers direct paths, relative traversal (`../../x.json`), and symlinks
  alike. Violation → exit 2 with `reason="plan_file_outside_root"` (mirrors the
  existing workspace.toml confinement; does not gate on `is_symlink()` alone).

- [x] AC17. Inline-object queue entries (`{path = "spec/foo", needs = "..."}`)
  are removed in place by matching on the `path` field value; all other inline
  objects in the array remain intact; per-entry inline comments on other entries
  are preserved after removal.

- [x] AC18. `repair-apply` never writes to `workspace.toml` when the plan
  contains only `manual_findings` (i.e., `automatic_operations` is `[]`).
  Stdout shape is identical to AC14's empty-ops shape (including `per_operation: []`).

- [x] AC19. A write-snapshot test (`test_repair_apply_no_writes`) confirms that
  `repair-plan` alone does not write to `workspace.toml` (only to the plan file).

- [x] AC20. `repair-apply` does not remove or modify `work.active` entries under
  any circumstance. A fixture with a Type 2 `active`-source finding in the plan's
  `manual_findings` list causes zero writes to that initiative's `work.active`.

### SKILL.md and tests

- [x] AC19a. `repair-apply` with multiple automatic operations spanning two
  initiatives applies all operations correctly; `operations_applied` equals the
  number of successfully-written operations (≥2 in the fixture test).

- [x] AC20a. `repair-apply` when a plan operation's spec.md is missing or its
  status cannot be parsed: operation is skipped with
  `reason="spec_status_unreadable"` in `per_operation`; no write occurs for
  that operation; other operations proceed normally.

- [x] AC20b. Defensive per-operation reasons `"initiative_not_found"` (initiative
  slug absent from workspace.toml) and `"entry_not_found_in_queue"` (fingerprint
  matched but queue entry absent) are accepted as valid `per_operation` outcomes
  with `applied: false`. These paths are only reachable via a hand-edited plan
  whose fingerprint still matches; they are guarded paths, not primary flows.

- [x] AC20c. End-to-end round-trip: a test runs `repair-plan` on a fixture
  workspace.toml, reads the produced default plan file, passes it to
  `repair-apply`, and asserts `operations_applied > 0` and workspace.toml
  mutated as expected. This covers the serialization join between plan writer
  and apply reader.

- [x] AC21. `SKILL.md` §1a subcommand table includes `repair-plan` and
  `repair-apply` rows with correct `Scope` and `Writes` annotations (table
  structure, not just prose mentions).

- [x] AC21a. `.gitignore` includes `.workspace-repair-plan.json`,
  `.workspace.toml.*.tmp`, and `.plan.*.tmp`; `git check-ignore -v
  .workspace-repair-plan.json` matches.

- [x] AC22. The stdlib-only import-purity tests in
  `tools/test_workspace_status_cli.py` (`_STDLIB_MODULES`, `test_engine_stdlib_only`,
  `test_cli_stdlib_only`) pass after updating `_STDLIB_MODULES` to include
  `hashlib` and `datetime`, and exempting `tomlkit` as a blessed CLI-only import.

- [x] AC23. `make build-self`, focused tests, `make build-check`, and `make ci`
  pass.

- [x] AC24. Existing Order 1B CLI and engine tests all pass without modification
  (except `_STDLIB_MODULES` extension in AC22, which is an extension not a
  weakening).

- [x] AC25. Each subcommand (`repair-plan`, `repair-apply`) invoked end-to-end
  against a fixture `workspace.toml`; exit code, mode field, plan contents, and
  post-write diff recorded.

- [x] AC26. `repair-plan` stdout is emitted even when writing the plan file
  fails (e.g., plan file parent directory is unwritable); the plan JSON is
  still valid on stdout; exit code is 2 if the file write failed. For the
  `--plan-file` confinement violation, the check still emits a minimal error
  JSON on stdout (`{schema_version, mode, applied: false, reason:
  "plan_file_outside_root"}`) before exiting 2, consistent with the
  implementation's always-emit-JSON-on-error contract; for the
  unwritable-directory case, the full plan JSON is emitted first and exit 2
  follows only on file-write failure.

- [x] AC27. `repair-plan --plan-file <root>/workspace.toml` (i.e., the plan-file
  path resolves to `workspace.toml` — whether by exact path, symlink, or any
  other resolution) exits 2 with `{"schema_version": 1, "mode": "repair-plan",
  "applied": false, "reason": "plan_file_is_workspace_toml"}`. `workspace.toml`
  is not written or truncated. Verified by a test that passes `workspace.toml`
  as `--plan-file` and asserts exit 2, the `plan_file_is_workspace_toml` reason,
  and that `workspace.toml` content is unchanged.

- [x] AC28. `repair-apply`'s atomic write preserves the original `workspace.toml`
  file mode (permissions). After a successful apply, `stat(workspace_path).st_mode`
  equals the pre-apply mode. Implementation: `Path(tmp_path).chmod(orig_mode)` after
  the fd is closed and before `Path(tmp_path).replace(workspace_path)` — uses
  `Path.chmod()` on the temp path (cross-platform; `os.fchmod` is Unix-only).
  Verified by `test_repair_apply_preserves_file_permissions`.

## Assumptions

- Technical: tomlkit 0.x is available in the runtime environment — confirmed by
  `python3 -c "import tomlkit; print(tomlkit.__version__)"` returning `0.15.1`
- Technical: The existing `compute_type2_cleanup` function covers the same
  operation shapes as the new `RepairOperation` types; Order 2B reuses the
  operation concept but adds a separate dataclass for cleaner plan serialization
- Technical: tomlkit correctly round-trips workspace.toml with all its inline
  objects, comments, and multiline arrays — to be verified in a fixture test
- Technical: `os.replace()` is atomic on POSIX (macOS, Linux) and effectively
  atomic on Windows (unlike `os.rename()` which can fail on Windows when the
  target exists); Python docs confirm `os.replace()` for cross-platform atomic
  replacement
- Technical: loop-engine and loop-cohort scripts ARE present in this repo at
  `packs/core/.apm/skills/work-loop/scripts/` — the Order 1B assumption
  ("loop-engine / loop-cohort scripts absent from this repo") is now outdated
- Process: Full-mode work-loop required; risk triggers: write-authority boundary,
  workspace.toml mutation, Approved lifecycle invariant, concurrent-write concerns,
  public-interface change
