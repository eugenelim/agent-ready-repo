# Plan: workspace-mcp — Stage 1 implementation

- **Status:** Approved <!-- Drafting | Approved | Done -->
- **Spec:** [`spec.md`](spec.md)

> **Blocked:** Stage 0 spikes (a)–(e) must close before any task in this plan begins implementation. The plan is authored now to make scope and sequencing explicit; wave scheduling is confirmed after spikes close.

## Constraints

- Pure stdlib Python 3.11+; no new runtime dependencies on agentbundle or workspace-mcp.
- ADR-0062: per-session-only spawn; no persistent daemon, no port binding.
- ADR-0063: session instruction as the universal elicitation mechanism; no per-skill modification.
- ADR-0064: events.jsonl as the FSM event source; loop-engine's CLI interface is unchanged (new internal behavior only — the events.jsonl append in `cmd_transition` and `cmd_init`).
- ADR-0065: elicit() + elicitation/create (never advertised in ServerCapabilities) + response-file fallback.
- ADR-0066: reactive git at TurnEnd; no declarative `git_managed` flags.
- ADR-0067: built-in manifest defaults + workspace-types.d/ extension (workspace-types.d/ deferred to Stage 3).
- ADR-0068: `_agentbundle.core/` notification namespace (confirmed by spike (b); global rename complete).
- ADR-0069: daemon threads + bounded worker pool (pool size 4); asyncio rewrite triggered if spike (e) fails.
- `is_need_satisfied()` default semantics are preserved for human-managed sessions; autonomous-dispatch mode is additive.
- `shell=False` and `--` end-of-options separator enforced on all git subprocess calls.

## Risks

- Spike (e) failure → asyncio rewrite required; T1 and T2 redesigned before starting. **CLOSED: spike (e) passed.**
- Spike (c) failure + no viable fallback → Stage 1 deferred entirely. **CLOSED: spike (c) failed but fallback designed (poll-based via `workspace_status()`); Stage 1 proceeds with updated AC3/AC7/AC8.**
- `permissions.allow` projection requires breaking adapter contract → T5 blocked; follow-on RFC required; AC17/AC18 deferred.
- loop-engine outbox protocol adds ~30 lines to `cmd_transition`/`cmd_init`; `make build-self` reprojection required afterward.

## Changelog

- 2026-08-03: Initial plan. Stage 0 spikes pending; implementation not started.
- 2026-08-03: Revised per pre-EXECUTE adversarial + security review. Added graceful I/O degradation, cmd_reset .loop-run/ removal, no-header-line clarification, AC0a missing-engine-state.json + path-containment branches, subprocess timeout, git_branch base-param explicit rejection, bounded-read for frame-size cap, safety.assert_under for slug containment, AC5 FSM-state reset, AC12 poll timeout + 0700 temp-dir, AC11 shutdown-event cancellation, AC24 lifecycle manifest + test stub, Boundaries "Never do" rails + trust assumptions. Re-Approved after revisions.

## Tasks

### T0 — Stage 0 spike closure (prerequisite; not implementation)

**Depends on:** none
**Verification:** Goal-based check
**Done when:** All five Stage 0 spike results documented; none returns a design-sinking failure without a designed fallback.
**Tests:** no stub (goal-based)
**Approach:** ~~Run spikes (a)–(e) against a production Claude Code + Conductor session.~~ **COMPLETE (2026-08-03).** Results documented in `docs/rfc/0078-notes/spike-results.md`. ADR-0068 updated with confirmed namespace `_agentbundle.core/` (spike (b)). design.md Component 3 updated per spike (a): single `session/new._meta.systemPrompt` injection confirmed sufficient. Spike (c) fallback designed: AC3/AC7/AC8 updated to reflect poll-based observability via `workspace_status()`. Spikes (d) and (e) passed without action.

---

### T1 — loop-engine events.jsonl append and outbox protocol

**Depends on:** T0
**Verification:** TDD
**Tests:**
- `packages/agentbundle/tests/test_loop_engine_events_jsonl.py`: outbox write protocol (write pending → atomic state write → append events.jsonl → delete pending); outbox recovery at `cmd_init` startup AND at `cmd_transition` entry/resume case (pending.to == state AND pending.seq == transition_sequence → replay; mismatch → discard; crash-then-next-transition) (ACs 0, 0a).
  *Stubs:*
  `test_outbox_recovery_replay_when_to_matches_state` → `assert False  # STUB: AC0a`
  `test_outbox_recovery_discard_when_to_mismatches_state` → `assert False  # STUB: AC0a`
  `test_cmd_transition_recovers_stale_pending_before_new_transition` → `assert False  # STUB: AC0a (crash-then-next-transition: pending from prior crash must be replayed/discarded at top of next cmd_transition, not lost)`
  `test_cmd_transition_recovers_foreign_spec_pending_before_writing_own` → `assert False  # STUB: AC0a (cross-spec: crash on spec-A then transition on spec-B must recover spec-A's pending against spec-A's engine-state.json before writing spec-B's new pending event — skipping leaves spec-A's event silently lost to the step-2 overwrite)`
  `test_io_failure_does_not_abort_transition` → `assert False  # STUB: AC0 graceful-degradation — monkeypatch events.jsonl append to raise PermissionError; assert engine-state.json write still succeeds and a warning is emitted`

**Note on line schema:** all events.jsonl lines must use `{"seq", "run_id", "spec", "from", "event", "to", "at"}` field names — matching design.md:317. Tests must assert that field names match exactly (not `to_state`/`from_state`/`timestamp`). `cmd_init` creates `events.jsonl` as an **empty file** — no header line is written; the bridge identifies run_id from the first event's `run_id` field.

**Approach:**
In `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`:
- Add `.loop-run/` dir creation in `cmd_init`. Append `.loop-run/` to `.gitignore` if not already present.
- Add `events.jsonl` initialization in `cmd_init`: create as empty file (no header line).
- Add `cmd_reset` cleanup: remove `.loop-run/` directory (in addition to removing `engine-state.json`).
- Wrap all events.jsonl and events.pending I/O in try/except; log warnings on failure; never let I/O exceptions propagate to the FSM state write.
- In `cmd_transition`, implement in this order:
  1. **Recovery check (before writing a new pending event):** if `.loop-run/events.pending` exists, apply universal pending recovery:
     - Read `pending["spec"]` to identify the owning spec directory. Validate via `safety.assert_under(repo_root, Path(pending["spec"]))` — if validation fails (path escapes repo root), discard the pending file.
     - If `{pending["spec"]}/engine-state.json` is absent (owning spec dir deleted, or crash before the state write), discard the pending file.
     - If a `.tmp`-in-progress rename file exists alongside `events.pending` (crash during atomic state write), complete the rename first, then re-evaluate.
     - Load `{pending["spec"]}/engine-state.json` (the owning spec's state, regardless of which spec is currently transitioning).
     - If `pending["to"] == owning_state["state"] AND pending["seq"] == owning_state["transition_sequence"] AND pending["run_id"] == owning_state["run_id"]` → **replay** (append to events.jsonl, delete pending); else → **discard** (delete pending).
     Skipping a foreign pending file defers its loss to step 2 (where the new pending event overwrites it), silently losing the owning spec's missed transition. Recovery must run unconditionally against the owning spec before any write.
  2. **Write pending JSON** to `.loop-run/events.pending` (os.replace-safe atomic write to temp, then rename).
  3. **Write `engine-state.json`** atomically (temp + rename — already done).
  4. **Append** pending line from `.loop-run/events.pending` to `.loop-run/events.jsonl`.
  5. **Delete** `.loop-run/events.pending`.
- In `cmd_init`, check for a stale `.loop-run/events.pending` on startup:
  - Read `pending["spec"]`. Load `{pending["spec"]}/engine-state.json` (the owning spec's state).
  - If `pending["to"] == owning_state["state"]` AND `pending["seq"] == owning_state["transition_sequence"]` AND `pending["run_id"] == owning_state["run_id"]`: replay (append, delete). Else: discard.
- Run `make build-self` after changes to reproject loop-engine to `.agents/skills/work-loop/scripts/loop-engine.py`.

**Anchor-test sweep:** grep `packages/agentbundle/tests/` for `loop-engine` or `loop_engine` fixtures → identify any that snapshot `cmd_transition` output and update if the new events.jsonl append changes observable behavior.

---

### T2 — `agentbundle.workspace_mcp` core module

**Depends on:** T0, T1, T4
**Verification:** TDD (unit) + Visual/manual QA (end-to-end)
**Tests:**
- `test_workspace_mcp_event_bridge.py`: byte-offset tail; seq dedup (AC6, `seq ≤ last_emitted_seq` → skip); partial-line buffering on torn-write — partial last line held at offset, completed on next poll, no crash (AC4); inode change or size < offset → offset/buffer/run_id reset (AC5); human-gate detection (`to` field matches `*-HUMAN-GATE`) and enriched notification payload (ACs 3, 7).
  *Stubs:* `test_human_gate_sets_gate_state_in_workspace_status` → `assert False  # STUB: AC7 (gate_pending=True, gate/gate_question/review_findings set in workspace_status() response)`
  `test_partial_line_buffered_no_crash` → `assert False  # STUB: AC4`
  `test_inode_change_resets_offset_and_run_id` → `assert False  # STUB: AC5`
- `test_workspace_mcp_tools.py`: `workspace_status()` result shape, pack-presence (6 roots OR-logic), slug safety `^[a-zA-Z0-9._-]+$` + dot-segment rejection + realpath containment (ACs 8, 9, 10).
  *Stubs:* `test_slug_dot_dot_rejected` → `assert False  # STUB: AC10`; `test_slug_containment_stays_under_output_base` → `assert False  # STUB: AC10`
- `test_workspace_mcp_elicit.py`: capability detection at init; elicit MCP path (AC11); response-file O_EXCL guard raises on pre-existing file (AC12); workspace-mcp never advertises `elicitation` in ServerCapabilities (AC13).
  *Stubs:* `test_response_file_oexcl_guard` → `assert False  # STUB: AC12`; `test_server_capabilities_omits_elicitation` → `assert False  # STUB: AC13`
- `test_workspace_mcp_git.py`: check-ref-format validation of branch name; `--` separator present in every subprocess call that carries agent-supplied data; commit intersects output_pattern (rejects null-pattern items); push two-sided branch check (AC14); discovery-mode returns error for `git_branch`/`git_commit`/`git_push`; `git_status` allowed in discovery-mode (AC15).
  *Stubs:* `test_git_commit_intersects_output_pattern` → `assert False  # STUB: AC14`; `test_git_push_two_sided_branch_check` → `assert False  # STUB: AC14`; `test_git_branch_rejects_leading_dash_and_unsafe_names` → `assert False  # STUB: AC14 (check-ref-format --branch form rejects -foo, --track; plain form does not)`; `test_discovery_mode_rejects_mutating_tools` → `assert False  # STUB: AC15`
- `test_workspace_mcp_stdin.py`: 1 MiB frame-size cap quarantines and discards oversized frame; malformed JSON discarded with error response; unknown request_id discarded (AC16).
  *Stubs:* `test_oversized_frame_quarantined` → `assert False  # STUB: AC16`; `test_unknown_request_id_discarded` → `assert False  # STUB: AC16`
- `test_workspace_mcp_lifecycle.py`: stdin close → process exits within 5s (AC22).
  *Stub:* `test_stdin_close_exits_process` → `assert False  # STUB: AC22`

**Approach:**
Implement `packages/agentbundle/agentbundle/workspace_mcp.py`. Key components:

- `_SAFE_SLUG_RE = re.compile(r'^[a-zA-Z0-9._-]+$')`. Slug guard: match regex AND not in `{'.', '..'}` AND not starting with `-`. After pattern formatting, use `safety.assert_under(static_output_base, resolved_dir)` for containment (not a bespoke startswith).
- `_LIFECYCLE_MANIFEST: dict[str, dict]`: embedded constant mapping each initiative item type (`work`, `shape`, `research`, `strategy`, `design`, `signal`, `brief`) to `{dispatch_skill, output_pattern, has_gates, required_pack}`. Values match design.md's type→lifecycle table exactly. `workspace_status()` uses this dict to populate per-item metadata fields. Not computed at runtime from workspace.toml (AC24).
- `DEFAULT_SESSION_INSTRUCTION`: embedded constant per design.md Component 3 (AC20).
- `_EventBridge(daemon=True)`: 200ms poll of `.loop-run/events.jsonl`; byte-offset + inode tracking; seq dedup; maintains internal FSM state (current state, gate fields); detects `*-HUMAN-GATE` in the `to` field and updates internal gate state `{gate, gate_question, review_findings}` (reads reviewer report from spec dir disk). **Spike (c) fallback:** notifications are generated internally but not relayed to ACP control plane; FSM state exposed via `workspace_status()` `current_state`/`gate_pending`/`gate_question`/`review_findings` fields (AC7, AC8). Control plane polls `workspace_status()` to observe transitions.
- `_WorkspaceStatusTool`: reads workspace.toml via `workspace_status_engine.analyze_bounded(..., autonomous_dispatch=True)`; pack-presence filter (6 roots, OR logic); slug safety guard.
- `_ElicitTool` (dispatched to worker pool): `elicitation/create` path (AC11) OR response-file path (AC12, O_EXCL, 0600, reject pre-existing, poll, temp+rename read, cleanup); capability detected at init (never advertise in ServerCapabilities — AC13).
- `_GitTools`: `git_status` (always); `git_branch(name)` — reject any non-None `base` with an explicit tool error (AC14); validate `name` via `subprocess.run(["git", "check-ref-format", "--branch", name], ...)` (the `--branch` form rejects names starting with `-`; the plain refname form does not — pin this form), then `subprocess.run(["git", "checkout", "-b", name], shell=False)` (NO `--` — branch name is an option argument, not a pathspec; `--branch`-form check-ref-format is the injection defense); `git_commit(message)` — intersect uncommitted paths with output_pattern, stage only matching paths via `["git", "add", "--", *matched_paths]`; `git_push(branch)` — two-sided check before `["git", "push", "--", "origin", branch]`; all subprocess calls use `timeout=30`; discovery-mode guard on mutating tools (AC14, AC15).
- `_StdioLoop` (main thread): JSON-framed MCP reads; 1 MiB frame-size cap (AC16a); malformed JSON quarantine (AC16b); unknown request_id rejection (AC16c); `{request_id: Event}` map for elicitation routing; write lock for stdout; dispatches tool calls to `ThreadPoolExecutor(max_workers=4)`.
- `_init_handshake`: reads host capabilities; selects elicitation delivery path; constructs ServerCapabilities WITHOUT `elicitation` (AC13).
- Entry point: `def main(): ...` and `if __name__ == '__main__': main()`.

**AC20 verification (goal-based):** see spec.md Testing Strategy — import module, assert `DEFAULT_SESSION_INSTRUCTION` is non-empty and contains `'elicit'`.
**AC24 verification (goal-based):** see spec.md Testing Strategy — import module, assert `_LIFECYCLE_MANIFEST` keys equal the required 7 types.

---

### T3 — Core-pack alias script

**Depends on:** T2
**Verification:** Goal-based check
**Done when:** `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py` exists, `python3 workspace_mcp_server.py` invokes the module identically to module-mode.
**Tests:** no stub (goal-based — one-line delegation; no new logic)
**Approach:** Write a single-line delegation:
```python
#!/usr/bin/env python3
import agentbundle.workspace_mcp as _m; _m.main()
```

---

### T4 — `is_need_satisfied()` autonomous-dispatch mode

**Depends on:** T0
**Verification:** TDD
**Tests:**
- `packages/agentbundle/tests/test_workspace_status_engine_autonomous.py`:
  - `shape:` absent from active AND backlog → unsatisfied when `autonomous_dispatch=True`; satisfied when `False` (AC19)
  - `research:` absent from backlog as type "research" → unsatisfied when `autonomous_dispatch=True`; satisfied when `False` (AC19)
  *Stubs:* `test_shape_absent_unsatisfied_autonomous` → `assert False  # STUB: AC19`; `test_research_absent_unsatisfied_autonomous` → `assert False  # STUB: AC19`

**Approach:**
Update the delegation chain in `workspace_status_engine.py` (use function names; line numbers are informative only and will drift):
1. `is_need_satisfied(need, ini_slug, all_initiatives, autonomous_dispatch: bool = False)`:
   - `shape:` branch: if `autonomous_dispatch`, also check `ini.shaping.backlog` for the slug — absent from both active AND backlog → return False. (Current behavior: absent from active → `slug not in active_slugs` returns True/satisfied, even if slug never existed — the gap for autonomous mode.)
   - `research:` branch: if `autonomous_dispatch`, add explicit absent-target check: `slug not in research_slugs` currently returns **True (satisfied)** when slug is absent from backlog — the known bug for autonomous mode. Fix: when `autonomous_dispatch`, absent from backlog as type "research" → return False.
2. `classify_entries(ini, all_initiatives, autonomous_dispatch: bool = False)`: propagate parameter to each `is_need_satisfied(n, ini.slug, all_initiatives, autonomous_dispatch)` call.
3. `analyze_bounded(root: Path, autonomous_dispatch: bool = False)`: propagate to `classify_entries(ini, initiatives, autonomous_dispatch)` call. `workspace_status()` passes `autonomous_dispatch=True` to `analyze_bounded`.
4. `analyze()` callers do NOT change (human-session default=False).
5. Update SKILL.md §2 (needs-resolution table) and the `shape:`/`research:` comments in `workspace_status_engine.py` to document the two-mode semantics. In doing so, strip the stale `schema.md:113`, `schema.md:114`, and `SKILL.md:90` citations from those comments (the file does not exist and the SKILL.md line number is inside a TOML template block, not needs-resolution prose) — replace with "SKILL.md §2".

**Anchor-test sweep:** grep for tests that directly call `is_need_satisfied()` or indirectly via `analyze_bounded()` — update any that assert the old behavior on absent targets (should be zero; the default=False preserves existing semantics).

---

### T5 — `permissions.allow` additive-merge projection

**Depends on:** T0, T2
**Verification:** Goal-based check
**Done when:** `agentbundle install core` on a clean repo adds exactly 6 `mcp__workspace-mcp__*` entries (parsed assertion, not grep count). Repeat on a repo with pre-existing `permissions.allow` entries: existing preserved, no duplicates.
**Tests:** `packages/agentbundle/tests/test_adapter_permissions_projection.py` — install core on tmp repo, parse `.claude/settings.json`, assert all 6 ids present in `permissions.allow`.
**Approach:** Add additive-merge projection target to `packages/agentbundle/agentbundle/_data/adapter.toml` for the Claude adapter. Implement the merge logic (if the projection capability for `permissions.allow` doesn't exist, add it). If the adapter contract cannot be extended non-breakingly, mark AC17/AC18 `(deferred: workspace-mcp-permissions-projection-contract)` and file the follow-on RFC.

---

### T6 — Version bump, changelog, and README

**Depends on:** T1, T2, T3, T4, T5
**Verification:** Goal-based check
**Done when:** agentbundle version bumped (minor); `CHANGELOG.md` has `[Unreleased]` entry with `Engine-Change-RFC: RFC-0078`; `README.md` documents `workspace_mcp`.
**Tests:** no stub (goal-based)
**Approach:** Standard agentbundle version bump per `packages/AGENTS.md`. Run `make build-self` (if Task 1 or alias-script changes weren't already reprojected) to sync projected files.

---

### T7 — Full gates pass

**Depends on:** T1, T2, T3, T4, T5, T6
**Verification:** Goal-based check
**Done when:** `python3 -m pytest packages/agentbundle/tests/ -q` exits 0; `make lint-ruff` exits 0; `SKIP_SAST=1 make build-check` exits 0.
**Tests:** no stub — running the suite IS the check
**Approach:** Fix any pre-existing failures per pre-flight protocol. If CI wiring for `packages/agentbundle` tests is absent, add the step.

---

## Wave schedule

| Wave | Tasks | Notes |
| ---- | ----- | ----- |
| 0 | T0 | Gate; blocks all others — COMPLETE |
| 1 | T1, T4 | Independent; T1 writes loop-engine; T4 writes workspace_status_engine; no shared files |
| 2 | T2 | Core module; depends on T1 for end-to-end event bridge tests |
| 3 | T3, T5 | Alias (depends on T2); permissions projection (depends on T2) |
| 4 | T6 | Version bump; depends on all prior tasks |
| 5 | T7 | Full gates; depends on all prior tasks |

**Wave execution is sequential** (Phase 1 supervisor mode: parallel fan-out disabled). Tasks 1 and 4 share Wave 1 but execute sequentially within the wave. Each wave's tasks are committed before the next wave begins.
