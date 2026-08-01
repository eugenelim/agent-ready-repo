# Plan: workspace-status simplification — Order 1A

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Move `tools/workspace_status_engine.py` into the workspace-status skill's flat
`scripts/` directory using `git mv`, add a thin JSON CLI wrapper alongside it,
update the Phase 0 test suite to import from the skill-local path, update SKILL.md
to invoke the CLI instead of carrying embedded parsing/DAG prose, add projection
and end-to-end tests, correct the skill-authoring guide, then run `make build-self`
and the full gate sequence.

The riskiest part is the SKILL.md update: the model-executed skill must continue to
render identically while delegating all data work to the backend. The CLI must be
invocable from any cwd. The projection tests must prove the installed artifact
contains both scripts.

Tasks are sequenced so T2 (engine move + CLI) must complete before T3 (consumer
update) and T4 (SKILL.md wiring), which must complete before T5 (installer tests).
T6 (guide fix) and T7 (build + review) are terminal.

## Constraints

- RFC-0023: no shared-libs projection; skills must be self-contained.
- RFC-0049, RFC-0064: workspace.toml schema and workspace-status semantics are authority; no behavior change in Order 1A.
- Phase 0 characterization suite (41 tests) is the compatibility authority.
- No third-party dependencies; no installer production code changes.
- Sequential execution only (tasks overlap on SKILL.md, Phase 0 tests, and build-self output).

## Construction tests

**Integration tests:**
- End-to-end: install core pack into tmp adopter dir; invoke installed `workspace_status.py` via `sys.executable` against a fixture workspace; parse JSON; compare semantic result against direct source-engine execution.
- CLI invocation from non-repo cwd (cross-cwd test).

**Manual verification:**
- Record exact command, exit code, `schema_version`, ready/blocked/finding counts from the installed CLI execution (AC17).

## Design (LLD)

### Design decisions

- `scripts/workspace_status_engine.py` — moved from `tools/` via `git mv`; unchanged API and behavior. Traces to: AC1, AC2, AC6.
- `scripts/workspace_status.py` — thin CLI: accepts `--root <dir>`. Synthesizes `workspace_present`/`workspace_root` (CLI-synthesized fields; `analyze()` does not provide them — if workspace.toml is absent, `parse_workspace` raises `FileNotFoundError` which the CLI pre-checks and maps to exit 1 with `workspace_present: false`). On presence, invokes `analyze(root)`, calls `compute_type2_cleanup()` per Type 2 finding to populate `type2_cleanup_ops`, serializes to UTF-8 JSON with `schema_version: 1`, exits 0 on success, exits 2 on unexpected errors via top-level `except Exception` routing to stderr (no traceback, no absolute paths on stdout). No `shell=True`; `pathlib`; list-form subprocess in tests. Traces to: AC4, AC5, AC7, AC8, AC11, AC20.
- SKILL.md update — removes embedded parsing/DAG/reconciliation procedure (§1 "Read workspace.toml" through §2a "Reconciliation" and §2 "Resolve the DAG"); rewrites §6 "Next-actions" to consume JSON `ready`/`unblocked`/`active` lists rather than re-running DAG resolution prose; instructs model to invoke `scripts/workspace_status.py --root "<repo-root>"` (quoted) and parse its JSON; preserves §3–§6 rendering, §4 skill-routing, §5 missing-fields handling, and cleanup confirmation sections. Traces to: AC4, AC7, AC15.
- Phase 0 test migration — replaces `from workspace_status_engine import …` with an `importlib` source-path loader resolving the skill-local module. No engine copy in `tools/`. Traces to: AC3, AC6.
- Projection tests — for each adapter that projects skills, assert both scripts exist in the installed workspace-status directory and are byte-identical to the source. Traces to: AC9.
- Guide correction — removes line 69 shared-libs promise; states self-containment rule and that shared-libs is a specialized source-enumeration rail only. Traces to: AC14.

### Interfaces & contracts

JSON output schema (schema_version: 1):
```json
{
  "schema_version": 1,
  "workspace_present": bool,
  "workspace_root": str,
  "initiatives": [{"slug", "name", "status", "milestone", "brief_queue": BriefQueue | null}],
  "work": {
    "ready":   [{"path", "slug", "needs", "ini_slug", "blocking_needs": [str]}],
    "blocked": [{"path", "slug", "needs", "ini_slug", "blocking_needs": [str]}],
    "active":  [{"path", "slug", "needs", "ini_slug"}],
    "shipped": [{"path", "slug", "needs", "ini_slug"}]
  },
  "shaping": {
    "ready":   [{"slug", "entry_type", "needs", "ini_slug", "blocking_needs": [str]}],
    "signals": [{"slug", "entry_type", "needs", "ini_slug", "blocking_needs": [str]}],
    "blocked": [{"slug", "entry_type", "needs", "ini_slug", "blocking_needs": [str]}]
  },
  "reconciliation": {
    "type1": [Finding],
    "type2": [Finding],
    "type3": [Finding],
    "type2_cleanup_ops": [CleanupOp]
  },
  "diagnostics": {"workspace_files_read": 1, "spec_files_read": int}
}
```
Note: `backlog` is NOT in the JSON output. SKILL.md reads `[backlog].open` from workspace.toml text directly (for comment-line extraction, which requires raw text access the TOML parser doesn't provide). The `diagnostics.workspace_files_read` is a CLI-side constant (1 — always one workspace.toml). The §6 `unblocked` list is derived from JSON `work.ready` (not a separate JSON field).
Traces to: AC5, AC6, AC7.

### Failure, edge cases & resilience

- workspace.toml absent → `{"schema_version": 1, "workspace_present": false}`, exit 1.
- Malformed TOML → stderr message, exit 2; no traceback in stdout.
- Missing spec files → skip under today's skip rules (no error).
- Unicode paths and content → explicit `encoding="utf-8"` throughout.
- Non-repo cwd → engine resolves all paths from explicit `--root` argument.

## Tasks

### T1: Contract, preflight, and pre-EXECUTE review

**Depends on:** none

**Tests:** no stub (goal-based)

**Approach:**
- Create `docs/specs/workspace-status-simplification-order-1a/spec.md` and `plan.md` (this document).
- Record assumption trio and declined temptations.
- Run Phase 0 suite and benchmark; record baseline results in this plan.
- Run `loop-cohort.py init docs/specs/workspace-status-simplification-order-1a`.
- Run pre-EXECUTE adversarial and security review; resolve all findings to Clean.
- Run `loop-cohort.py approve-plan docs/specs/workspace-status-simplification-order-1a`.

**Done when:** spec and plan drafted; pre-EXECUTE reviewers return Clean; `loop-cohort check --phase plan` exits 0.

**Baseline results (recorded pre-EXECUTE):**
- Phase 0 tests: 41 passed, 0 failed
- Benchmark: 313 spec dirs, 44 ready, 4 blocked, 4 active, 32 shipped, 4 archived, Type 1=1, Type 2=0, Type 3=0
- Analysis elapsed first run: 0.2302s, repeated: 0.2394s

---

### T2: CLI and production engine location

**Depends on:** T1

**Tests:**
- `test_cli_success` — run CLI against fixture workspace; assert exit 0, JSON parses, `schema_version == 1`. (AC5, AC11)
- `test_cli_deterministic` — run twice on unchanged fixture; assert outputs are byte-identical. (AC5)
- `test_cli_workspace_absent` — run with no `workspace.toml`; assert exit 1, JSON `workspace_present == false`. (AC5)
- `test_cli_malformed_toml` — run with invalid TOML; assert exit 2, no traceback in stdout. (AC20)
- `test_cli_generic_exception` — use a deterministic error path that works regardless of uid: point `--root` at a dir where `workspace.toml` is a subdirectory (raises `IsADirectoryError` on open) or monkeypatch `tomllib.loads` to raise; assert exit 2, stdout is empty, no absolute paths on stdout. (AC20)
- `test_cli_no_writes` — snapshot fixture subtree membership and mtimes before execution; assert no new files created and no mtimes changed after. (AC8)
- `test_cli_non_repo_cwd` — invoke from `tempfile.gettempdir()`; assert exit 0. (AC11)
- `test_cli_unicode` — fixture with Unicode paths/content; assert exit 0, JSON parses. (AC11)
- `test_cli_type2_cleanup_ops_populated` — fixture with a Type 2 finding; assert `reconciliation.type2_cleanup_ops` is non-empty. (AC5, AC7)
- `test_engine_module_importable` — `importlib` load of production module; assert `analyze` callable. (AC1, AC3)
- `test_cli_stdlib_only_imports` — grep both scripts for non-stdlib, non-relative imports; assert none. (AC12, AC13)

**Approach:**
- `git mv tools/workspace_status_engine.py packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`
- Create `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` — thin CLI: arg parse (`--root`), import engine via script-relative `importlib.util` loader or direct path insertion, call `analyze(root)`, call `compute_type2_cleanup()` per Type 2 finding, serialize JSON with `schema_version: 1`, top-level `except Exception` (not bare `except`) routing all unhandled exceptions to stderr (exit 2) with no traceback on stdout.
- Update engine module docstring to remove stale "parallel reference model not used by production" language; state the production-backend role; remove the SKILL.md SHA-256 contract anchor note (now stale).
- Add CLI tests to `tools/test_workspace_status_cli.py`.
- Confirm engine module is importable from skill-local path.

**Done when:** red CLI tests exist; `git mv` completed; CLI written; focused tests green.

**Declined temptations:**
- Adding `--quick` / `--full` flag (scope exclusion)
- Creating a helper module for types (no second runtime caller requires it in this PR)
- Creating a `--fix` subcommand (read-only; scope exclusion)
- Using a package import instead of script-relative import (no Python package; self-contained skill)

---

### T3: Migrate Phase 0 consumers

**Depends on:** T2

**Tests:**
- All 41 existing Phase 0 tests pass against skill-local module.
- Benchmark structural counts unchanged (same fixture dimensions, same analysis results).
- `test_skill_contract_anchor` updated: removes the SHA-256 hash anchor and its `_SKILL_CONTRACT_START/END/HASH` constants only (the hash targets SKILL.md prose that T4 will delete — the test would fail after T4). The structural assertion (SKILL.md invokes CLI; no second DAG) is T4's domain (`test_skill_invokes_cli` and `test_skill_no_dag_prose`); T3 only neutralizes the stale anchor. (AC3)
- `test_work_loop_contract_anchor` passes unchanged.
- `test_symlink_escape_rejected` — plant a symlinked spec dir escaping root; assert it is not read in Type-1 scan. (AC19)

**Approach:**
- Update `tools/test_workspace_status.py`: replace `from workspace_status_engine import …` with an `importlib.util` source-path loader resolving to `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`.
- Update `tools/bench-workspace-status.py`: same loader pattern.
- Remove the SHA-256 hash anchor and its `_SKILL_CONTRACT_START/END/HASH` constants from `test_workspace_status.py` (`test_skill_contract_anchor`): the hash targets SKILL.md §1–§6 prose that T4 will delete, so retaining it causes a RED in T4. The structural assertions (SKILL.md invokes CLI; no second DAG) belong to T4's tests; T3 only removes the stale anchor. The work-loop anchor test (`test_work_loop_contract_anchor`) is unrelated to the engine move and stays unchanged.
- Remove or revise wording in tests/bench that describes the engine as "a parallel reference model not used by production."
- Confirm 41 tests pass and benchmark dimensions are identical.

**Done when:** 41 tests green against production module; benchmark prints same structural counts; `ls tools/workspace_status_engine.py` exits non-zero (file absent). (AC2)

---

### T4: Wire workspace-status SKILL.md

**Depends on:** T2, T3

**Tests:**
- `test_skill_invokes_cli` — assert SKILL.md contains `scripts/workspace_status.py`. (AC4)
- `test_skill_no_dag_prose` — assert SKILL.md does not contain "### 2. Resolve the DAG", "resolve the DAG", or "whose `needs` are all satisfied" (detects both section removal and §6 rewrite). (AC4, AC15)
- `test_skill_cleanup_preserved` — assert SKILL.md retains Type 2 cleanup confirmation language ("Reply Y"). (AC7)
- `test_skill_no_quickfull` — assert SKILL.md does not contain `--quick` or `--full`. (AC15)
- `test_skill_quoted_root` — assert SKILL.md invocation uses a quoted `--root` argument. (Boundaries / AC4)
- `test_skill_parallel_graph_preserved` — assert SKILL.md retains "parallel opportunities" and `--bg` offer strings (§6b/§6c). (AC6 / next-action semantics)

**Approach:**
- Edit `packs/core/.apm/skills/workspace-status/SKILL.md`:
  - Replace §1 "Read workspace.toml" through §2a "Reconciliation" procedure with a step instructing the model to invoke `scripts/workspace_status.py --root <repo-root>` and parse the JSON result.
  - Remove §2 "Resolve the DAG" manual procedure.
  - Retain §3 "Surface results" rendering instructions (these drive model output from JSON data).
  - Retain §4 "Skill prompts by type" (installed skill/pack availability is runtime-only).
  - Retain §5 "Missing fields" resilience instructions.
  - Rewrite §6 "Next-actions" to consume JSON `work.ready` (for both `next_queue` and `unblocked`), `work.blocked` (for §6b dependency graph blocked rows), `work.active`, and `shaping.ready`/`shaping.signals` lists (no DAG resolution prose; remove any sentence using "whose `needs` are all satisfied").
  - Retain Type 2 cleanup confirmation block and write behavior (operation metadata comes from JSON `type2_cleanup_ops`).
  - Do not hand-edit projected copies; run `make build-self` in T7.
- Keep SKILL.md below repository size limits.

**Done when:** structural tests green; SKILL.md invokes CLI; no duplicate DAG/reconciliation procedure; cleanup behavior preserved.

---

### T5: Installer projection tests

**Depends on:** T2, T4

**Tests:**
- `test_workspace_status_scripts_projected` — for each adapter that projects skills (claude-code, kiro, codex, copilot, cursor, gemini), render the core pack, locate workspace-status SKILL.md, assert adjacent `scripts/workspace_status.py` and `scripts/workspace_status_engine.py` exist and are byte-identical to source. (AC9)
- `test_installed_cli_end_to_end` — install core pack into tmp adopter dir; invoke `scripts/workspace_status.py` via `sys.executable` with `--root <fixture-workspace>` from a cwd outside the fixture; parse JSON; assert `schema_version == 1`, `workspace_present == true`; compare semantic result with direct source-engine execution. (AC10, AC11, AC17)

**Approach:**
- Add `packages/agentbundle/agentbundle/build/tests/test_workspace_status_projection.py`.
- Use existing render/install test utilities from adapter tests.
- Verify no installer production code change is required. If scripts/ are not projected, surface the evidence (this would invalidate the Order 1A design and require a surface to human rather than a silent installer change).

**Done when:** all projection tests green; installed CLI invoked and result recorded; no installer production code changed.

---

### T6: Correct skill-authoring guide

**Depends on:** none

**Tests:** no stub (goal-based)

**Approach:**
- Edit `guides/_shared/how-to/author-a-skill.md`, specifically the paragraph at line 69 that says "put it in `.apm/shared-libs/<name>/` — the projection system copies it into every adapter's layout alongside the skill directories."
- Replace with accurate guidance:
  - Every installed skill must be self-contained.
  - Skill-local runtime code belongs in that skill's flat `scripts/` directory.
  - Cross-skill filesystem imports are invalid.
  - Generic shared-libs-to-skill projection is not currently supported.
  - The surviving `.apm/shared-libs/` mechanism is a specialized source-enumeration rail for the adapter-root-bins companion shim, not a reusable consumer-library delivery mechanism.
  - Multiple independently installed skills needing one runtime implementation require an approved shared-runtime or vendoring contract rather than an assumed sibling path.
- Run catalogue lint to confirm no lint regressions.

**Done when:** `guides/_shared/how-to/author-a-skill.md` no longer promises generic shared-libs projection; lint passes.

---

### T7: Build, simplify, and final review

**Depends on:** T1–T6

**Tests:** no stub (goal-based + manual QA)

**Approach:**
- Run `make build-self`; verify `.claude/skills/workspace-status/scripts/workspace_status.py` and `workspace_status_engine.py` are present.
- Run `python3 tools/lint-ruff.py`.
- Run `make lint-mypy`.
- Run `SKIP_SAST=1 make build-check`.
- Run `make ci`.
- Run `git diff --check` and `git status --short`.
- Run the simplify pass on new code only (CLI wrapper and test files).
- Run adversarial, security, and quality-engineer reviewers; resolve all findings.
- Run `scripts/lint-spec-status.py`.
- Record installed CLI invocation: exact command, exit code, schema_version, counts.
- Complete work-loop finish checklist.

**Done when:** all gates green; all reviewers Clean; installed CLI invoked and recorded; finish checklist ticked.

---

## Rollout

No deploy step. `make build-self` regenerates the self-host projection. The PR merges a new SKILL.md (behavior-equivalent to today's), two new scripts, updated tests and benchmark, and a guide correction. The change is reversible (revert the PR).

## Risks

- SKILL.md update may accidentally remove rendering or confirmation behavior — mitigated by structural tests (T4) and adversarial review.
- Phase 0 test anchor (`test_skill_contract_anchor`) targets deleted SKILL.md prose — handled in T3 by converting it to a structural check instead of a hash.
- scripts/ projection may not be exercised by existing adapter tests for workspace-status — T5 validates this; if it fails, surface to human (do not silently broaden into an installer change).
- TOML comment-preserving write behavior in SKILL.md is unchanged (model still owns the write); backend output provides the operation metadata.

## Changelog

- 2026-07-31: initial plan
