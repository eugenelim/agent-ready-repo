# Spec: workspace-status simplification — Order 1B

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (public-interface change + file-I/O scope change + multi-feature/dependent tasks + structural change to scan behavior)
- **Constrained by:**
  - [RFC-0023](../../rfc/0023-credential-manager-broker.md) — shared-libs projection retired; skills must be self-contained
  - [RFC-0049](../../rfc/0049-the-release-loop-and-company-os.md) — Company OS architecture authority
  - [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md) — workspace.toml schema and workspace-status behavior authority
  - `packs/core/.apm/skills/workspace-status/SKILL.md` — production behavior; rendering preserved
  - `docs/specs/workspace-status-simplification-order-0/spec.md` — Phase 0 characterization; compatibility authority
  - `docs/specs/workspace-status-simplification-order-1a/spec.md` — Order 1A contract; architectural baseline preserved
- **Contract:** none (internal skill interface only)
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Add progressive, read-only modes to the installed `workspace-status` backend.
Make `status` the default path used by the `workspace-status` skill.

Three modes with a single shared implementation spine:

| Mode | Scope | Trigger |
|------|-------|---------|
| `status` | Bounded — declared workspace entries only; Type 2 + Type 3 reconciliation | Session start, queue check |
| `explain` | Focused projection from bounded status result; one item | Investigate a specific item |
| `reconcile` | Exhaustive — Type 1 + Type 2 + Type 3 | Explicit audit request |

No-subcommand invocation is a compatibility alias for `reconcile`, with a deprecation
warning on stderr. All modes are strictly read-only.

## Boundaries

### Always do

- Extract `_run_type23_scan(root, initiatives)` from `run_reconciliation`, alongside
  `_run_type1_scan(root, all_tracked)`. `run_reconciliation` is refactored to call both
  helpers and remains semantically identical (same signature, same 2-tuple return). `analyze()`
  also calls both helpers directly to obtain split file counts. `analyze_bounded` calls
  `_run_type23_scan` only. Call-site counts are the canonical definition in AC1.
- Add `analyze_bounded(root)` to the engine: parses workspace.toml once, classifies
  declared entries, calls `_run_type23_scan` (Type 2 + Type 3 only), never calls
  `_run_type1_scan`. `_safe_spec_path()` confinement is preserved because bounded mode
  inherits the guard through the shared `_run_type23_scan` helper.
- Extend `WorkspaceStatusResult` with `global_scan_performed: bool`,
  `declared_spec_files_read: int`, and `global_scan_files_read: int`; make `files_read`
  a property returning the sum (backward compat for any caller of `result.files_read`).
  Remove the `files_read` dataclass field; update the one call to `analyze(root)` in the
  engine that constructs `WorkspaceStatusResult` with `files_read=…`.
- Add `explain_item(result, selector)` to the engine: normalizes selector to slug using
  the existing `normalize_for_shaping_guard()`; searches result in-memory only; performs
  no file I/O and never constructs a filesystem path from the selector.
- Keep `analyze(root)` as the full/reconcile path: parse once, classify, call
  `_run_type1_scan` + `_run_type23_scan` separately to populate both file-count fields.
- Add subcommand routing to `workspace_status.py` via manual pre-dispatch (not nested
  argparse subparsers): inspect `argv[0]` for a known subcommand; if found, strip it and
  parse the remaining tokens (including `--root`) with the existing argument parser; if
  `argv[0]` is not a known subcommand, treat all tokens as implicit reconcile arguments and
  emit a deprecation warning on stderr only. Subcommand-first; `--root` follows the subcommand.
- Extend `_build_json` in the CLI to add `mode` (string) and `scan` (object) top-level
  fields to every mode's JSON output; add `performed`, `complete`, `types_performed`
  to the existing `reconciliation` object (additive; keep `type1`, `type2`, `type3`,
  `type2_cleanup_ops`); keep `diagnostics` unchanged for backward compatibility.
- Include `mode` in the absent-workspace JSON payload (`workspace_present: false` branch)
  for each subcommand, so callers can identify the active mode even on early exit.
- Update `SKILL.md` to invoke `status` subcommand; gate the "Untracked live specs"
  rendering on `reconciliation.types_performed` containing `1`; add `reconcile` and
  `explain` invocation guidance.
- Add new subcommand tests to `tools/test_workspace_status_cli.py`.
- Run `make build-self` after editing packs/; verify generated projection is unchanged.

### Ask first

- Any change to workspace.toml schema (not in scope)
- Any change to Phase 0 characterization test assertions beyond adding new result fields
- Any change to Type 2 cleanup confirmation behavior
- Any change to installer production code

### Never do

- Add `repair-plan`, `repair-apply`, `--fix`, or automatic mutation
- Create a separate `workspace-reconcile` skill
- Add a second independent analysis pass when explain can reuse the bounded result
- Add new missing-target or cycle detection semantics (not in scope for Order 1B)
- Put the engine in shared-libs or import from sibling skills
- Add any third-party dependency
- Change workspace.toml schema
- Add caching
- Change the Type 2 or Type 3 reconciliation semantics
- Move either script out of `scripts/`
- Use `shell=True` in any subprocess call
- Use the selector string as a filesystem path component inside `explain_item`
- Duplicate the Type 2/3 scan loops in `analyze_bounded` (always route through the shared helper)

## Testing Strategy

- **TDD** — subcommand routing (status/explain/reconcile/no-subcommand), bounded vs.
  full scan scope with a fixture carrying N declared + M untracked live specs, explain
  selector behaviors (match/not-found/ambiguous), JSON contract fields (mode, scan,
  reconciliation metadata, absent-workspace mode), stderr-only deprecation warning.
  Tests written as red stubs before implementation.
- **Goal-based check** — `make build-self` passes; SKILL.md invocation uses `status`
  subcommand (grep); `types_performed` gate is present in SKILL.md rendering section.
- **Visual / manual QA** — each mode invoked end-to-end against the repo's own
  `workspace.toml`; exit code, mode field, scan counts, and reconciliation metadata
  recorded per mode.

## Acceptance Criteria

- [x] AC1. `_run_type1_scan(root, all_tracked)` and `_run_type23_scan(root, initiatives)`
  both exist in the engine as private functions. `_run_type1_scan` has exactly two call
  sites: inside `run_reconciliation` and inside `analyze`. `_run_type23_scan` has exactly
  three call sites: inside `run_reconciliation`, inside `analyze`, and inside
  `analyze_bounded`. `run_reconciliation` remains semantically identical to its Order 1A
  form (same signature, same 2-tuple return; backward compatible with existing callers).
  `analyze_bounded` calls `_run_type23_scan` only — it never calls `_run_type1_scan`.
  All declared-spec path resolution in `_run_type23_scan` goes through the existing
  `_safe_spec_path()` confinement helper — no confinement bypass in bounded mode.
- [x] AC2. `analyze_bounded(root)` exists and populates `WorkspaceStatusResult` with
  `global_scan_performed=False`, `declared_spec_files_read` ≤ N (Type 2+3 reads — entries
  with no spec.md do not increment the count), `global_scan_files_read=0`.
  `result.files_read` (property) returns `declared_spec_files_read`.
- [x] AC3. `analyze(root)` (full/reconcile path) populates `global_scan_performed=True`,
  `declared_spec_files_read` ≤ N (Type 2+3 reads), `global_scan_files_read` ≥ M (Type 1
  reads — count includes all spec.md files read during the global walk, tracked and
  untracked). `result.files_read` equals `declared_spec_files_read + global_scan_files_read`.
- [x] AC4. `explain_item(result, selector)` exists in the engine. Selector is normalized
  to slug using the existing `normalize_for_shaping_guard()`. The function searches
  result in-memory only: never reads a file; never constructs a filesystem path from the
  selector. Lookup is restricted to **active initiatives** (status = "active") and
  **work queues only** (queue/active/shipped lists; shaping entries are not searched).
  Ambiguity is determined by counting distinct active initiatives with a matching
  work-queue entry, not raw match count (a slug in both active and shipped of one
  initiative counts as one initiative, not two). Returns one of:
  - `{"selector_status": "matched", "explained_item": {...}}` — slug found in work
    queues of exactly one active initiative
  - `{"selector_status": "not_found"}` — slug not found in any active initiative's
    work queues (including selectors for shaping items or paused-initiative items)
  - `{"selector_status": "ambiguous", "matches": [...]}` — slug found in work queues
    of more than one distinct active initiative (cross-initiative same-slug collision)
  Ambiguous is declared only when the slug appears in work queues of two or more
  distinct active initiatives simultaneously.
- [x] AC5. `explained_item` shape when the item is in the work queue (queue, active,
  or shipped list):
  ```
  path          — canonical queue entry path (e.g. "spec/m1-workspace-core")
  slug          — path with "spec/" stripped
  ini_slug      — owning initiative slug
  list          — "active" if in work.active; "shipped" if in work.shipped (and not
                   active); "queue" if in work.queue (and not active or shipped).
                   Precedence: active > shipped > queue (a slug in both active and
                   shipped resolves to "active")
  classification — "active" (in work.active) | "shipped" (in work.shipped, not active) |
                   "ready" | "blocked" (queue entries, per classify_entries output)
  blocking_needs — from EntryClassification for queue entries; [] for active/shipped
  dependencies  — [{need: <str>, satisfied: <bool>}] for all declared needs;
                   [] for entries with no declared needs; [] for active/shipped
  downstream_unblocked — paths of entries in result.blocked that share the same
                         ini_slug as the matched item AND whose blocking_needs list
                         contains only "work:<this-path>" (sole remaining unsatisfied
                         need within their initiative; they become ready if this item
                         shipped). Cross-initiative blocking_needs are not evaluated here.
  ```
- [x] AC6. `workspace_status.py status --root <dir>` routes to `analyze_bounded`; JSON
  output contains `"mode": "status"` and `"scan": {"global_spec_scan_performed": false,
  "workspace_files_read": 1, "declared_spec_files_read": ≤N (actual read count, see AC10),
  "global_scan_spec_files_read": 0}`; `reconciliation.types_performed` is `[2, 3]`;
  `reconciliation.performed` is `true`; `reconciliation.complete` is `false`.
- [x] AC7. `workspace_status.py reconcile --root <dir>` routes to `analyze` (existing
  full path); JSON output contains `"mode": "reconcile"` and
  `"scan": {"global_spec_scan_performed": true, ..., "global_scan_spec_files_read": ≥M
  (actual read count, see AC11)}`; `reconciliation.types_performed` is `[1, 2, 3]`;
  `reconciliation.performed` is `true`; `reconciliation.complete` is `true`.
- [x] AC8. `workspace_status.py explain --root <dir> --item <selector>` routes to
  `analyze_bounded` then `explain_item`; JSON contains `"mode": "explain"`, `"selector"`,
  `"selector_status"`, and (when matched) `"explained_item"`. Explain mode's `scan`
  reflects the bounded analysis (same as status mode).
- [x] AC9. `workspace_status.py --root <dir>` (no subcommand) produces JSON output
  identical to `reconcile`; a deprecation warning is emitted on stderr; stdout contains
  only valid JSON; exit code is 0 on success. The absent-workspace branch for all
  subcommands includes `"mode"` in the JSON (`workspace_present: false` payload).
- [x] AC10. Structural-cost proof — bounded mode: a fixture with N declared workspace
  entries and M additional untracked live Approved/Implementing specs in `docs/specs/`
  produces `scan.global_scan_spec_files_read` = 0 and
  `scan.declared_spec_files_read` ≤ N in status mode. The global spec tree (`docs/specs/`)
  is never walked in status or explain mode.
- [x] AC11. Structural-cost proof — full mode: the same fixture produces
  `scan.global_scan_spec_files_read` ≥ M (Type 1 walk reads the M untracked files) in
  reconcile mode. The Type 1 walk IS performed in reconcile mode.
- [x] AC12. The `reconciliation` object in JSON retains `type1`, `type2`, `type3`, and
  `type2_cleanup_ops` from Order 1A; `performed`, `complete`, and `types_performed` are
  additive new fields. No existing key is removed or renamed.
- [x] AC13. `diagnostics` object preserved in JSON for `status` and `reconcile` modes
  with the same fields (`workspace_files_read`, `spec_files_read`) for backward
  compatibility. `diagnostics.spec_files_read` equals `scan.declared_spec_files_read +
  scan.global_scan_spec_files_read`. The `explain` mode JSON is a focused projection
  that does not include `diagnostics` (or `reconciliation` arrays); see `_build_explain_json`
  in the plan LLD. `test_diagnostics_compat` is scoped to status and reconcile modes.
- [x] AC14. Explain: valid selector returns `selector_status: "matched"` and
  `explained_item` per AC5. Ready entry: `blocking_needs` = `[]`, all dependencies have
  `satisfied: true`. Blocked entry: `blocking_needs` non-empty, unsatisfied dependencies
  listed. `downstream_unblocked` contains only entries for which this item is the sole
  remaining unsatisfied need. Unknown selector: `selector_status: "not_found"`. Cross-
  initiative work-queue collision: `selector_status: "ambiguous"` with `matches` list.
  Exit code is 0 for both `not_found` and `ambiguous` (structured diagnostics, not errors).
  A CLI-level test (`test_explain_cli_ambiguous_exit0`) asserts exit 0 for an ambiguous
  invocation — not just the engine-level return shape.
- [x] AC14a. `explain` active-only scope is documented in the SKILL.md `explain` guidance:
  selectors for shaping items or items in paused/closed initiatives return `not_found`.
  (Plan T4 must include a SKILL.md bullet for this.)
- [x] AC14b. `explain` invoked without `--item` exits non-zero (exit 2) with a usage
  error on stderr; stdout is empty. A CLI test (`test_explain_missing_item_arg`) asserts
  this behavior.
- [x] AC15. `SKILL.md` procedure invokes `status` subcommand as the default; the
  "Untracked live specs" rendering block is gated on
  `reconciliation.types_performed` containing `1` — when absent, the block is omitted
  and a pointer to `reconcile` mode is shown instead; guidance for when to invoke
  `reconcile` and `explain` is present; new `mode` and `scan` fields documented in the
  Key fields section.
- [x] AC16. `make build-self`, focused tests, `make build-check`, and `make ci` pass.
- [x] AC17. Existing Order 1A CLI tests all pass without modification. No existing test
  assertion is weakened.
- [x] AC18. Each mode invoked end-to-end against the repo's own workspace.toml; exit
  code, mode field, scan counts, and reconciliation metadata recorded per mode.
- [x] AC19. The CLI is read-only in all three modes; verified by the Order 1A AC8
  write-snapshot assertion (test_cli_no_writes) extended to cover all three subcommands.

## Known gaps preserved from Order 1A

KD-01 through KD-09 are preserved unchanged. Order 1B does not fix any known defect.

## Assumptions

- Technical: Engine is ~903 lines, stdlib-only, at `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` — confirmed
- Technical: `run_reconciliation` inline Type 2/3 loops are extractable to `_run_type23_scan` without changing semantics; `_safe_spec_path` guards are preserved in the extracted helper
- Technical: `explain_item` requires no file I/O — all data lives in `WorkspaceStatusResult` already populated by `analyze_bounded`
- Technical: `normalize_for_shaping_guard` is the canonical selector-to-slug normalizer and covers all selector input forms
- Technical: Making `files_read` a property requires removing the dataclass field and updating the one constructor call in `analyze()` — confirmed by reading engine:660-666
- Technical: Manual argv pre-dispatch (inspect argv[0] for known subcommand) resolves the `--root` placement ambiguity without breaking any existing test
- Process: Full-mode work-loop required; risk triggers: public-interface change, structural scan-scope change, multi-feature/dependent tasks, file-I/O boundary — confirmed
- Process: `loop-engine` / `loop-cohort` scripts absent from this repo — named skip for state machine; full mode rigor applied without it
