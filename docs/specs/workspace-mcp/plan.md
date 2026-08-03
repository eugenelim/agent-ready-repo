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

- Spike (e) failure → asyncio rewrite required; Tasks 1 and 2 redesigned before starting. **CLOSED: spike (e) passed.**
- Spike (c) failure + no viable fallback → Stage 1 deferred entirely. **CLOSED: spike (c) failed but fallback designed (poll-based via `workspace_status()`); Stage 1 proceeds with updated AC3/AC7/AC8.**
- `permissions.allow` projection requires breaking adapter contract → Task 5 blocked; follow-on RFC required; AC17/AC18 deferred.
- loop-engine outbox protocol adds ~30 lines to `cmd_transition`/`cmd_init`; `make build-self` reprojection required afterward.

## Changelog

- 2026-08-03: Initial plan (spec-plan mode). Stage 0 spikes pending; implementation not started.

## Tasks

### Task 0 — Stage 0 spike closure (prerequisite; not implementation)

**Depends on:** — (blocks all other tasks)
**Verification:** Goal-based check
**Done when:** All five Stage 0 spike results documented; none returns a design-sinking failure without a designed fallback.
**Tests:** no stub (goal-based)
**Approach:** ~~Run spikes (a)–(e) against a production Claude Code + Conductor session.~~ **COMPLETE (2026-08-03).** Results documented in `docs/rfc/0078-notes/spike-results.md`. ADR-0068 updated with confirmed namespace `_agentbundle.core/` (spike (b)). design.md Component 3 updated per spike (a): single `session/new._meta.systemPrompt` injection confirmed sufficient. Spike (c) fallback designed: AC3/AC7/AC8 updated to reflect poll-based observability via `workspace_status()`. Spikes (d) and (e) passed without action.

---

### Task 1 — loop-engine events.jsonl append and outbox protocol

**Depends on:** Task 0
**Verification:** TDD
**Tests:**
- `packages/agentbundle/tests/test_loop_engine_events_jsonl.py`: outbox write protocol (write pending → atomic state write → append events.jsonl → delete pending); outbox recovery at `cmd_init` startup AND at `cmd_transition` entry/resume case (pending.to == state AND pending.seq == transition_sequence → replay; mismatch → discard; crash-then-next-transition) (ACs 0, 0a).
  *Stub:* `test_outbox_recovery_replay_when_to_matches_state` → `assert False  # STUB: AC0a`
  `test_outbox_recovery_discard_when_to_mismatches_state` → `assert False  # STUB: AC0a`
  `test_cmd_transition_recovers_stale_pending_before_new_transition` → `assert False  # STUB: AC0a (crash-then-next-transition: pending from prior crash must be replayed/discarded at top of next cmd_transition, not lost)`
  `test_cmd_transition_recovers_foreign_spec_pending_before_writing_own` → `assert False  # STUB: AC0a (cross-spec: crash on spec-A then transition on spec-B must recover spec-A's pending against spec-A's engine-state.json before writing spec-B's new pending event — skipping leaves spec-A's event silently lost to the step-2 overwrite)`

**Note on line schema:** all events.jsonl lines must use `{"seq", "run_id", "spec", "from", "event", "to", "at"}` field names — matching design.md:317. Tests must assert that field names match exactly (not `to_state`/`from_state`/`timestamp`).

**Approach:**
In `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`:
- Add `.loop-run/` dir creation in `cmd_init`.
- Add `events.jsonl` initialization (write header line with `run_id`) in `cmd_init`.
- In `cmd_transition`, implement in this order:
  1. **Recovery check (before writing a new pending event):** if `.loop-run/events.pending` exists, apply universal pending recovery:
     - Read `pending["spec"]` to identify the owning spec directory.
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

### Task 2 — `agentbundle.workspace_mcp` core module

**Depends on:** Task 0, Task 1 (events.jsonl must exist before the bridge can be tested end-to-end), Task 4 (`analyze_bounded(autonomous_dispatch=True)` must exist before Task 2 calls it)
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

- `_SAFE_SLUG_RE = re.compile(r'^[a-zA-Z0-9._-]+$')`. Slug guard: match regex AND not in `{'.', '..'}` AND not starting with `-`. After pattern formatting, `Path(resolved).resolve()` must be under `_STATIC_OUTPUT_BASES[type]`.
- `DEFAULT_SESSION_INSTRUCTION`: embedded constant per design.md Component 3 (AC20).
- `_EventBridge(daemon=True)`: 200ms poll of `.loop-run/events.jsonl`; byte-offset + inode tracking; seq dedup; maintains internal FSM state (current state, gate fields); detects `*-HUMAN-GATE` in the `to` field and updates internal gate state `{gate, gate_question, review_findings}` (reads reviewer report from spec dir disk). **Spike (c) fallback:** notifications are generated internally but not relayed to ACP control plane; FSM state exposed via `workspace_status()` `current_state`/`gate_pending`/`gate_question`/`review_findings` fields (AC7, AC8). Control plane polls `workspace_status()` to observe transitions.
- `_WorkspaceStatusTool`: reads workspace.toml via `workspace_status_engine.analyze_bounded(..., autonomous_dispatch=True)`; pack-presence filter (6 roots, OR logic); slug safety guard.
- `_ElicitTool` (dispatched to worker pool): `elicitation/create` path (AC11) OR response-file path (AC12, O_EXCL, 0600, reject pre-existing, poll, temp+rename read, cleanup); capability detected at init (never advertise in ServerCapabilities — AC13).
- `_GitTools`: `git_status` (always); `git_branch(name)` — validate via `subprocess.run(["git", "check-ref-format", "--branch", name], ...)` (the `--branch` form rejects names starting with `-`; the plain refname form does not — pin this form), then `subprocess.run(["git", "checkout", "-b", name], shell=False)` (NO `--` — branch name is an option argument, not a pathspec; `--branch`-form check-ref-format is the injection defense); `git_commit(message)` — intersect uncommitted paths with output_pattern, stage only matching paths via `["git", "add", "--", *matched_paths]`; `git_push(branch)` — two-sided check before `["git", "push", "--", "origin", branch]`; discovery-mode guard on mutating tools (AC15).
- `_StdioLoop` (main thread): JSON-framed MCP reads; 1 MiB frame-size cap (AC16a); malformed JSON quarantine (AC16b); unknown request_id rejection (AC16c); `{request_id: Event}` map for elicitation routing; write lock for stdout; dispatches tool calls to `ThreadPoolExecutor(max_workers=4)`.
- `_init_handshake`: reads host capabilities; selects elicitation delivery path; constructs ServerCapabilities WITHOUT `elicitation` (AC13).
- Entry point: `def main(): ...` and `if __name__ == '__main__': main()`.

**AC20 verification (goal-based):** see spec.md Testing Strategy — import module, assert `DEFAULT_SESSION_INSTRUCTION` is non-empty and contains `'elicit'`.

---

### Task 3 — Core-pack alias script

**Depends on:** Task 2
**Verification:** Goal-based check
**Done when:** `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py` exists, `python3 workspace_mcp_server.py` invokes the module identically to module-mode.
**Tests:** no stub (goal-based — one-line delegation; no new logic)
**Approach:** Write a single-line delegation:
```python
#!/usr/bin/env python3
import agentbundle.workspace_mcp as _m; _m.main()
```

---

### Task 4 — `is_need_satisfied()` autonomous-dispatch mode

**Depends on:** Task 0
**Verification:** TDD
**Tests:**
- `packages/agentbundle/tests/test_workspace_status_engine_autonomous.py`:
  - `shape:` absent from active AND backlog → unsatisfied when `autonomous_dispatch=True`; satisfied when `False` (AC19)
  - `research:` absent from backlog as type "research" → unsatisfied when `autonomous_dispatch=True`; satisfied when `False` (AC19)
  *Stubs:* `test_shape_absent_unsatisfied_autonomous` → `assert False  # STUB: AC19`; `test_research_absent_unsatisfied_autonomous` → `assert False  # STUB: AC19`

**Approach:**
Update the delegation chain in `workspace_status_engine.py`:
1. `is_need_satisfied(need, ini_slug, all_initiatives, autonomous_dispatch: bool = False)` at line 456:
   - `shape:` branch: if `autonomous_dispatch`, also check `ini.shaping.backlog` for the slug — absent from both active AND backlog → return False. (Current behavior: absent from active → `slug not in active_slugs` returns True/satisfied, even if slug never existed — the gap for autonomous mode.)
   - `research:` branch: if `autonomous_dispatch`, add explicit absent-target check: `slug not in research_slugs` currently returns **True (satisfied)** when slug is absent from backlog — the known bug for autonomous mode. Fix: when `autonomous_dispatch`, absent from backlog as type "research" → return False.
2. `classify_entries(ini, all_initiatives, autonomous_dispatch: bool = False)` at line 536: propagate parameter to each `is_need_satisfied(n, ini.slug, all_initiatives, autonomous_dispatch)` call (lines 559, 612).
3. `analyze_bounded(root: Path, autonomous_dispatch: bool = False)` at line 844: propagate to `classify_entries(ini, initiatives, autonomous_dispatch)` call (line 862). `workspace_status()` passes `autonomous_dispatch=True` to `analyze_bounded`.
4. `analyze()` callers do NOT change (human-session default=False).
5. Update SKILL.md §2 (needs-resolution table) and the `shape:`/`research:` comments in `workspace_status_engine.py` to document the two-mode semantics. In doing so, strip the stale `schema.md:113`, `schema.md:114`, and `SKILL.md:90` citations from those comments (the file does not exist and the SKILL.md line number is inside a TOML template block, not needs-resolution prose) — replace with "SKILL.md §2".

**Anchor-test sweep:** grep for tests that directly call `is_need_satisfied()` or indirectly via `analyze_bounded()` — update any that assert the old behavior on absent targets (should be zero; the default=False preserves existing semantics).

---

### Task 5 — `permissions.allow` additive-merge projection

**Depends on:** Task 0, Task 2 (tool names canonical)
**Verification:** Goal-based check
**Done when:** `agentbundle install core` on a clean repo adds exactly 6 `mcp__workspace-mcp__*` entries (parsed assertion, not grep count). Repeat on a repo with pre-existing `permissions.allow` entries: existing preserved, no duplicates.
**Tests:** `packages/agentbundle/tests/test_adapter_permissions_projection.py` — install core on tmp repo, parse `.claude/settings.json`, assert all 6 ids present in `permissions.allow`.
**Approach:** Add additive-merge projection target to `packages/agentbundle/agentbundle/_data/adapter.toml` for the Claude adapter. Implement the merge logic (if the projection capability for `permissions.allow` doesn't exist, add it). If the adapter contract cannot be extended non-breakingly, mark AC17/AC18 `(deferred: workspace-mcp-permissions-projection-contract)` and file the follow-on RFC.

---

### Task 6 — Version bump, changelog, and README

**Depends on:** Tasks 1–5
**Verification:** Goal-based check
**Done when:** agentbundle version bumped (minor); `CHANGELOG.md` has `[Unreleased]` entry with `Engine-Change-RFC: RFC-0078`; `README.md` documents `workspace_mcp`.
**Tests:** no stub (goal-based)
**Approach:** Standard agentbundle version bump per `packages/AGENTS.md`. Run `make build-self` (if Task 1 or alias-script changes weren't already reprojected) to sync projected files.

---

### Task 7 — Full gates pass

**Depends on:** Tasks 1–6
**Verification:** Goal-based check
**Done when:** `python3 -m pytest packages/agentbundle/tests/ -q` exits 0; `make lint-ruff` exits 0; `SKIP_SAST=1 make build-check` exits 0.
**Tests:** no stub — running the suite IS the check
**Approach:** Fix any pre-existing failures per pre-flight protocol. If CI wiring for `packages/agentbundle` tests is absent, add the step.

---

## Wave schedule (provisional — confirmed after Task 0 closes)

| Wave | Tasks | Notes |
| ---- | ----- | ----- |
| 0 | Task 0 (spikes) | Gate; blocks all others |
| 1 | Task 1, Task 4 | Independent; Task 1 writes loop-engine; Task 4 writes workspace_status_engine; no shared files |
| 2 | Task 2 | Core module; depends on Task 1 for end-to-end event bridge tests |
| 3 | Task 3, Task 5 | Alias (depends on Task 2); permissions projection (depends on Task 2) |
| 4 | Task 6 | Version bump; depends on all prior tasks |
| 5 | Task 7 | Full gates; depends on all prior tasks |

Tasks 1 and 4 CAN run in parallel within Wave 1 — they edit different files. If parallel dispatch is attempted: Task 1 edits `loop-engine.py`; Task 4 edits `workspace_status_engine.py` — no shared files, safe to run concurrently. Confirm no shared test fixture pollution before dispatching in parallel.
