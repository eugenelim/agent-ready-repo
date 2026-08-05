# Spec: workspace-mcp — Stage 1 implementation

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0078](../../rfc/0078-workspace-mcp.md) (Accepted 2026-08-03)
- **Design doc:** [`docs/architecture/workspace-mcp/design.md`](../../architecture/workspace-mcp/design.md) (converged at Codex Round 8; zero P1 findings)
- **ADRs:** [ADR-0062](../../adr/0062-workspace-mcp-per-session-only-constraint.md) · [ADR-0063](../../adr/0063-session-instruction-universal-elicitation.md) · [ADR-0064](../../adr/0064-events-jsonl-as-fsm-event-source.md) · [ADR-0065](../../adr/0065-elicit-elicitation-create-response-file-fallback.md) · [ADR-0066](../../adr/0066-reactive-git-at-turnend.md) · [ADR-0067](../../adr/0067-lifecycle-manifest-builtin-defaults-workspace-types-d.md) · [ADR-0068](../../adr/0068-notification-namespace-x-core.md) · [ADR-0069](../../adr/0069-threading-model-daemon-threads-bounded-pool.md)
- **Shape:** new module (`agentbundle.workspace_mcp`) + loop-engine events.jsonl append + core-pack alias + agentbundle Claude adapter projection target

> **Spec contract:** this document defines what "done" means for Stage 1. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Stage gate

**Stage 1 does not begin implementation until all five Stage 0 spikes close:**

| Spike | Gate question | Result |
| ----- | ------------- | ------ |
| (a) Instruction durability | Does `session/new` instruction survive across turns in at least one production AI host? | **PASS** — `systemPrompt` in `_meta` baked into `query()` at session creation; persists across turns. No per-turn re-injection needed. |
| (b) Notification naming | Is `x-core/` the confirmed ACP v1 extension namespace? (ADR-0068 updates on result) | **FAIL → renamed** — Observed convention is `_<namespace>/method` (e.g. `_claude/sdkMessage`). All `x-core/` references renamed to `_agentbundle.core/`. ADR-0068 updated. |
| (c) Notification relay | Do `notifications/message` frames reach the control plane as `session/update` events? | **FAIL → fallback** — `claude-agent-acp@0.64.0` does not relay MCP `notifications/message` (`case "notification": break`). Fallback: control plane polls `workspace_status()`. AC3, AC7, AC8 updated. |
| (d) Module-mode spawn | Does `python3 -I -m agentbundle.workspace_mcp` install and work? | **PASS** — isolation confirmed; submodule import works under `-I`. |
| (e) Threading model | Does stdlib daemon threads + bounded pool handle nested `elicitation/create` re-entrancy? | **PASS** — `{request_id: Event}` map pattern; two concurrent elicitations resolved without deadlock. |

All five Stage 0 spikes closed. Spikes (b) and (c) required design updates (rename + poll-based fallback); both are resolved. Implementation may begin.

## Objective

Deliver the Stage 1 workspace-mcp implementation: a per-session MCP server (Claude Code adapter only) that gives the control plane structured FSM-transition notifications, human-gate intercept, and git lifecycle tools for work-loop sessions, with zero missed transitions and zero behavior change when workspace-mcp is not configured.

**Scope — Stage 1 only:**
- Adapter: Claude Code (Class A)
- Skill: work-loop (FSM observability)
- Components: loop-engine events.jsonl append (new), event bridge, workspace_status tool, elicit tool, git tools (scoped)
- Not in Stage 1: artifact watcher (Stage 3), non-FSM skills (Stage 3), Codex/Copilot/Kiro (Stages 2a/2b/2c), multi-instance (Stage 4)

## Acceptance Criteria

### Loop-engine changes (enabling event bridge)

- [x] AC0 **loop-engine events.jsonl append.** `loop-engine.py` `cmd_transition` appends one JSON line per FSM transition to `.loop-run/events.jsonl` (repo-root-relative, gitignored, ephemeral). Each line contains: `{"seq": <int>, "run_id": "<uuid>", "spec": "<spec-dir>", "from": "<state>", "event": "<event>", "to": "<state>", "at": "<iso8601>"}` — matching the canonical schema in design.md:317 and the notification-contract table at design.md:342. `cmd_init` initializes `.loop-run/` (creates dir; creates `events.jsonl` as an empty file — no header line; every line in the file is a schema-conforming event). `cmd_reset` also removes `.loop-run/` (in addition to removing `engine-state.json`). If `.loop-run/` is absent from `.gitignore`, `cmd_init` appends it. The append follows the outbox protocol: write pending line to `.loop-run/events.pending`, write `engine-state.json` atomically (rename), append pending line to `events.jsonl`, delete pending. **Graceful degradation (universal rule):** all events.jsonl and events.pending I/O (create dir, create file, write, append, delete) is wrapped in a try/except; any I/O failure is caught and emits a logged warning; the FSM state write (`engine-state.json` atomic rename) proceeds uninterrupted regardless. events.jsonl I/O errors never abort a transition. This rule applies to `cmd_init`, `cmd_transition`, and `cmd_reset`.

- [x] AC0a **outbox ownership — universal pending recovery in both `cmd_transition` and `cmd_init`.** `.loop-run/events.pending` is repo-global (shared across all active specs). When a pending file exists, recovery always runs against the file's **owning spec** (identified by `pending["spec"]`), not the current spec — because skipping a foreign pending file only defers the overwrite to step 2, silently losing the owning spec's missed transition:
  1. Read `pending["spec"]` to identify the owning spec directory. Validate `pending["spec"]` via `safety.assert_under(repo_root, Path(pending["spec"]))` before any path construction — if validation fails (path escapes repo root), discard the pending file.
  2. Load `{pending["spec"]}/engine-state.json` (the owning spec's state, regardless of which spec is currently running). If this file is absent (owning spec dir deleted, or crash before the state write), discard the pending file (delete without appending).
  3. If a `.tmp`-in-progress rename file exists alongside `events.pending` (crash during the atomic state write), complete the rename first, then re-evaluate steps 1–2 against the now-complete state.
  4. If `pending["to"] == owning_state["state"]` AND `pending["seq"] == owning_state["transition_sequence"]` AND `pending["run_id"] == owning_state["run_id"]`: **replay** (append to events.jsonl, delete pending). Otherwise: **discard** (delete pending without appending).
  This check runs at the **start of `cmd_transition`** (before writing a new pending event — handles the same-spec resume case and the cross-spec case where another spec's crash left a foreign pending file) AND at **`cmd_init` startup** (handles the restart-from-scratch case). Not running recovery before writing step 2 overwrites the prior pending file and silently loses the missed transition, whether same-spec or cross-spec. This ensures loop-engine (not workspace-mcp) owns events.pending replay.

### workspace-mcp module

- [x] AC1 **Module entry point.** `pip install agentbundle` installs `agentbundle/workspace_mcp.py`. `python3 -I -m agentbundle.workspace_mcp --help` exits 0. `python3 -I -m agentbundle.workspace_mcp` with a real `session/new` MCP handshake completes init, declares the tool surface, and enters the request loop.

- [x] AC2 **Core-pack alias.** `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py` exists and delegates to `agentbundle.workspace_mcp` (no logic duplication).

- [ ] AC3 `(deferred: workspace-mcp-stage1-behavioral-tests)` **Event bridge — zero missed transitions.** In a complete work-loop session (spec-plan mode: 7+ transitions), workspace-mcp's event bridge reads every FSM transition from `.loop-run/events.jsonl` with no gaps (consecutive `seq` values tracked internally). Rapid back-to-back transitions within a single 200ms poll cycle are both captured. The current FSM state is exposed via `workspace_status()` (see AC8); `_agentbundle.core/skill-state-change` notifications are generated but NOT relayed to the ACP control plane by `claude-agent-acp@0.64.0` (spike (c) — `case "notification": break`). Verified by internal unit test of the bridge's offset tracking and seq deduplication logic.

- [ ] AC4 `(deferred: workspace-mcp-stage1-behavioral-tests)` **Event bridge — torn-write recovery.** A partial last line in `.loop-run/events.jsonl` (simulated by a half-complete JSON line) does not crash the bridge or emit a malformed notification; the partial line is buffered until the remainder arrives.

- [ ] AC5 `(deferred: workspace-mcp-stage1-behavioral-tests)` **Event bridge — inode/truncation reset.** When `.loop-run/events.jsonl` is deleted and recreated (via `loop-engine reset`, which now removes `.loop-run/` per AC0), workspace-mcp detects the inode change or size-less-than-offset condition, resets offset, buffer, run_id, `current_state`, `gate_pending`, `gate`, `gate_question`, and `review_findings` (all FSM/gate fields cleared to null/false), and reattaches correctly without missing events from the new file.

- [ ] AC6 `(deferred: workspace-mcp-stage1-behavioral-tests)` **Event bridge — seq deduplication.** workspace-mcp tracks the last-emitted `seq`; an event line with `seq ≤ last_emitted_seq` is skipped without emitting a duplicate notification.

- [ ] AC7 `(deferred: workspace-mcp-stage1-behavioral-tests)` **Human-gate state in `workspace_status()`.** When workspace-mcp's event bridge reads a transition whose `to` field ends in `*-HUMAN-GATE`, the gate state is reflected in `workspace_status()` response fields: `gate_pending: true`, `gate: "<to>"`, `gate_question: "<question string>"`, `review_findings: "<last known reviewer report from disk, if any>"`. The control plane detects gate entry by polling `workspace_status()` and checking `gate_pending`. `_agentbundle.core/human-gate-pending` is also generated (spec-compliant contract target) but is not relayed to the ACP control plane in `claude-agent-acp@0.64.0` (spike (c) fallback).

- [ ] AC8 `(deferred: workspace-mcp-stage1-behavioral-tests)` **`workspace_status()` tool.** Returns a JSON object with `ready`, `shaping`, `blocked`, `active`, and FSM state keys. Each `ready` item has `ini_slug`, `type`, `slug`, and `dispatch_skill`. Each `blocked` item has an `unmet_needs` list. Items for absent packs appear with `available: false` and `required_pack: "<pack-name>"`. DAG resolution follows workspace.toml `needs:` edges. **FSM state fields (spike (c) fallback — poll-based observability):** `current_state` (string — current loop-engine FSM state, null if no active run), `gate_pending` (bool — true when current state ends in `*-HUMAN-GATE`), `gate` (string or null — the `*-HUMAN-GATE` state name when `gate_pending` is true), `gate_question` (string or null — gate question from `engine-state.json`), `review_findings` (string or null — last reviewer output from disk). When `events.jsonl` is missing when expected, returns `{"warning": "EVENTS-FILE-MISSING", "current_state": null}` rather than omitting the FSM fields silently.

- [ ] AC9 `(deferred: workspace-mcp-stage1-behavioral-tests)` **Pack-presence filter.** For a workspace with a missing optional pack, `workspace_status()` returns items for that pack's types with `available: false, required_pack: "<pack-name>"`. Pack presence is checked against 6 roots (3 adapters × repo-scope + user-scope), OR logic.

- [x] AC10 **Slug safety guard — regex and containment.** Before formatting an `ini_slug`, `type`, or `slug` value into an output_pattern glob, workspace-mcp validates each segment against `^[a-zA-Z0-9._-]+$` AND explicitly rejects any segment that is `.`, `..`, or starts with `-`. After formatting, the resolved directory is verified to remain under `repo_root` via `safety.assert_under(repo_root, resolved_dir)` — not a bespoke `startswith` comparison. *Note: the regex guard (`^[a-zA-Z0-9._-]+$`) already prevents traversal (`..`) and single-segment escapes, so `repo_root` is a safe containment base for Stage 1; tightening to the type's specific output base is a Stage 2 hardening item.* An item failing either check is excluded from the result (logged as a warning).

- [ ] AC11 `(deferred: workspace-mcp-stage1-behavioral-tests)` **`elicit()` tool — MCP path.** On an AI host that declares `elicitation` capability in its init handshake, `elicit()` sends an `elicitation/create` MCP server→client request with the question and options, blocks in a worker thread until the response arrives on the main stdio loop's `{request_id: Event/queue}` map, and returns the response to the caller. The worker checks a session-level shutdown `threading.Event` at each unblock step; when the shutdown event fires (stdin closes), the worker returns an error rather than blocking indefinitely.

- [ ] AC12 `(deferred: workspace-mcp-stage1-behavioral-tests)` **`elicit()` tool — response-file fallback.** On an AI host that does NOT declare `elicitation` capability, `elicit()`: (a) creates a temp directory with mode `0700` via `mkdtemp()`; creates the response file within it using `O_EXCL` (fails if file already exists — anti-pre-seed guard), sets file permissions `0600`; (b) writes the question to the file; (c) polls until the control plane overwrites the file using the temp-and-rename protocol, or until a configurable timeout (default 300 seconds) expires — on timeout, the tool returns an error; if the polled file contains invalid JSON (partial write in progress), the poll continues rather than returning a malformed response; (d) reads the response and returns it. The temp dir is cleaned up on session end. If a pre-existing file is found at `O_EXCL` creation time, the tool raises an error rather than reading the possibly-forged response. The response-file path is selected only when `capabilities.elicitation` is absent from the init handshake; its same-OS-user limitation (the `O_EXCL` guard does not prevent a same-uid process from racing) is documented in the module docstring as a known constraint for shared-machine deployments.

- [ ] AC13 `(deferred: workspace-mcp-stage1-behavioral-tests)` **`elicitation` capability — never advertised in ServerCapabilities.** workspace-mcp never includes `elicitation` in its MCP ServerCapabilities response (regardless of what the AI host declares). It selects the delivery path (AC11 vs AC12) from the host's `capabilities.elicitation` field in the init handshake. (Fixes bug #419 where advertising `elicitation` as a server capability produces an invalid MCP handshake.)

- [ ] AC14 `(deferred: workspace-mcp-stage1-behavioral-tests)` **git tools — scoped commit and validated push.** `git_status()` returns the current git status. `git_branch(name, base=None)` validates `name` via `git check-ref-format --branch <name>` (the `--branch` form rejects names starting with `-` and other invalid characters; the plain refname form does not) before any subprocess call; after passing validation, creates and checks out the new branch with `["git", "checkout", "-b", name]` (`shell=False`; no `--` here — the branch name is an option argument, not a pathspec; the `--branch`-form `check-ref-format` is the injection defense). Any caller-supplied `base` value is rejected with an explicit tool error ("base parameter is not supported; workspace-mcp always branches from HEAD"); the tool does not silently ignore it (no silently-ignored parameters — AGENTS.md §"add an option only when a second caller needs to differ"). `git_commit(message)` intersects uncommitted files with the dispatched item's `output_pattern` before staging — files not matching the pattern are not staged (reject null-pattern items with an error); stages only matching paths via `["git", "add", "--", *matched_paths]`. `git_push(branch)` performs a two-sided check: `branch` argument must equal the immutable session-bound branch (from env var or git HEAD at session start) AND HEAD must equal that branch; fails with an explicit error if either check fails; runs `["git", "push", "--", "origin", branch]`. `shell=False` enforced on all subprocess calls. All subprocess git calls use `timeout=30` (seconds, configurable); a subprocess timeout surfaces as a tool error, not a hang. `--` end-of-options separator applies to commands taking pathspec positional arguments (`git add`, `git push`); `git checkout -b` takes the branch name as an option argument and does not use `--`. Git hooks (`pre-commit`, `commit-msg`, `pre-push`) execute normally — see Boundaries: Trusted-repo assumption.

- [ ] AC15 `(deferred: workspace-mcp-stage1-behavioral-tests)` **git tools — discovery-mode guard.** In discovery mode (no env vars), `git_branch`, `git_commit`, and `git_push` return an error; `git_status` is allowed.

- [ ] AC15a `(deferred: workspace-mcp-stage1-behavioral-tests)` **git tools — FSM-mode guard.** When `WORKSPACE_MCP_SPEC_PATH` is set — regardless of whether `WORKSPACE_MCP_DISPATCHED_ITEM` is also set — `git_branch`, `git_commit`, and `git_push` return an error; `git_status` is allowed. SPEC_PATH is the dominant signal: when both env vars are present (unsupported configuration), FSM mode wins and a startup warning is logged. This ensures work-loop manages its own git lifecycle even when a misconfigured or stale harness supplies both variables.

- [ ] AC16 `(deferred: workspace-mcp-stage1-behavioral-tests)` **MCP stdin validation.** The main stdio loop enforces: (a) a frame-size cap (configurable, default 1 MiB) enforced **during** a bounded read — the read stops and the frame is quarantined and discarded with an error response without accumulating the full oversized frame in memory first; the connection is NOT dropped; (b) malformed JSON frames are discarded with an error response, not propagated; (c) `elicitation/create` responses whose `request_id` does not match any outstanding server-issued request are discarded (not routed to a worker).

- [ ] AC17 `(deferred: workspace-mcp-permissions-projection-contract)` **Headless permissions projection.** `agentbundle install core` additively merges the following entries into `.claude/settings.json` `permissions.allow`: `mcp__workspace-mcp__workspace_status`, `mcp__workspace-mcp__elicit`, `mcp__workspace-mcp__git_status`, `mcp__workspace-mcp__git_branch`, `mcp__workspace-mcp__git_commit`, `mcp__workspace-mcp__git_push`. Existing entries are preserved; no entry is duplicated. **This pre-approval is safe only because AC14's output_pattern scoping and push branch check are in force** — implementers must not weaken AC14 under the assumption that pre-approval is bounded by the tool's safety controls. **Trusted-repo assumption (see Boundaries):** pre-approval does not disable git hooks; see the Boundaries section's "Never do" and "Trusted-repo assumption" for the full constraint. *Deferred reason: `permissions.allow` is an array; the current adapter `merge-json` mode handles dict payloads only. A new adapter projection mode and schema bump are needed — warrant a follow-on RFC.*

- [ ] AC18 `(deferred: workspace-mcp-permissions-projection-contract)` **`permissions.allow` projection — non-breaking.** The additive-merge does not break existing adopter Claude adapter projections. Verified by `agentbundle install core` on a repo with and without pre-existing `permissions.allow` entries. *Deferred with AC17.*

- [x] AC19 **Needs-resolution semantics — autonomous dispatch mode.** `is_need_satisfied()`, `classify_entries()`, and `analyze_bounded()` each gain an `autonomous_dispatch: bool = False` parameter. `workspace_status()` calls `analyze_bounded(autonomous_dispatch=True)`, which propagates the parameter through `classify_entries(autonomous_dispatch=True)` to `is_need_satisfied(autonomous_dispatch=True)`. When `autonomous_dispatch=True`: a `shape:` target absent from both `ini.shaping.active` AND `ini.shaping.backlog` is treated as *unsatisfied* (current default behavior: absent from `active` → treated as satisfied regardless of backlog); a `shape:` target that IS in `backlog` (queued, not yet started) is treated as *satisfied* — its presence in backlog confirms the work is planned. When `False` (default): behavior is unchanged (SKILL.md §2 semantics preserved for human-managed sessions). **`research:` semantics (both modes):** a `research:` target absent from `ini.shaping.backlog` as type "research" is treated as *satisfied* in BOTH human and autonomous mode. Rationale: completed research items are removed from the backlog when done; there is no separate "completed" list, so absent-from-backlog is indistinguishable from completed. The autonomous-mode distinction does not apply to `research:` needs — both modes use the same logic: absent → satisfied, present → unsatisfied. SKILL.md §2 (needs-resolution table) and the `shape:`/`research:` explanatory comments in `workspace_status_engine.py` are updated to document the two-mode semantics.

- [x] AC20 **Session instruction template.** workspace-mcp ships a default session instruction template (embedded string constant) that the control plane can inject via `session/new.instruction`. The template instructs the AI to call `elicit()` for all questions, decisions, and option-selection moments. The template is readable as a constant from the installed module (e.g., `agentbundle.workspace_mcp.DEFAULT_SESSION_INSTRUCTION`). The content is consistent with the design doc's Component 3 specification.

- [ ] AC21 `(deferred: workspace-mcp-stage1-behavioral-tests)` **Zero behavior change without workspace-mcp.** A work-loop session run without `workspace-mcp` in `session/new.mcpServers` produces output identical to the pre-workspace-mcp baseline. Verified by running a spec-plan loop session with and without the server configured; diffing stdout.

- [ ] AC22 `(deferred: workspace-mcp-stage1-behavioral-tests)` **Per-session exit.** workspace-mcp exits when stdin closes. No port is bound; no process survives after session end. Verified by spawning workspace-mcp, closing its stdin, and asserting the process has exited within 5 seconds.

- [x] AC23 **agentbundle version bump.** `packages/agentbundle` version bumped (minor — new public module surface); `Engine-Change-RFC: RFC-0078` footer in the changelog entry; `CHANGELOG.md` `[Unreleased]` entry present. `packages/agentbundle/README.md` documents the `workspace_mcp` module.

- [x] AC24 **Built-in lifecycle manifest.** The built-in lifecycle manifest (implementing ADR-0067 built-in defaults) is a verifiable table embedded in `workspace_mcp.py` (not computed at runtime from workspace.toml). It maps each initiative item type (`work`, `shape`, `research`, `strategy`, `design`, `signal`, `brief`) to `{dispatch_skill, output_pattern, has_gates, required_pack}`. The table matches the type→lifecycle mapping in design.md. `workspace_status()` uses this table to populate the `dispatch_skill`, `output_pattern`, and `required_pack` fields on each returned item. `workspace_status_engine.py:analyze_bounded()` receives the type's resolved metadata fields from the module rather than computing them ad hoc.

*`(deferred: workspace-mcp-stage1-behavioral-tests)` — Deferral reason: AC3–AC9, AC11–AC16, AC21–AC22 require behavioral integration tests against a running `workspace_mcp.py` subprocess (EventBridge polling, elicit O_EXCL, git subprocess injection, frame-size cap). These tests are written as `pytest.skip()` stubs in Stage 1 and will be promoted to green passing tests before the module ships to production. The implementation code is present and code-reviewed; the stubs document the intended verification shape. Follow-on tracking: `workspace.toml [backlog] workspace-mcp-stage1-behavioral-tests`.*

*`(deferred: workspace-mcp-brief-queue-exposure)` — `workspace_status()` does not yet surface `brief_queue` items from initiatives. Brief items appear in the lifecycle manifest (AC24) but the queue itself is out of scope for Stage 1; the `brief_queue` field on `Initiative` is not yet standardised across workspace.toml versions. Follow-on: when `workspace.toml` brief-queue layout is ratified, add a `briefs` key to the `workspace_status()` response alongside `ready`/`shaping`/`blocked`.*

## Boundaries

**In scope for Stage 1:**
- `packages/agentbundle/agentbundle/workspace_mcp.py` — new module
- `packs/core/.apm/skills/work-loop/scripts/loop-engine.py` — events.jsonl append + outbox protocol (AC0, AC0a); projected to `.agents/skills/work-loop/scripts/loop-engine.py` via `make build-self`
- `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py` — alias script
- `packages/agentbundle/agentbundle/_data/adapter.toml` — new additive-merge projection target
- `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` — `is_need_satisfied()` update (AC19)
- SKILL.md §2 — needs-resolution two-mode semantics (AC19)
- `packages/agentbundle/` tests covering ACs 0–23
- agentbundle version bump; `make build-self` reprojection

**Out of scope for Stage 1:**
- Artifact watcher (Stage 3)
- Non-FSM skills (Stage 3)
- Codex CLI, Copilot CLI, Kiro CLI adapters (Stages 2a/2b/2c)
- workspace-types.d/ third-party extension (Stage 3)
- workspace.toml initiative entry (scheduling decision)

**Never do:**
- Bind a TCP/UDP port or create any persistent network listener (ADR-0062: per-session only)
- Add a runtime dependency to `agentbundle` or `workspace_mcp` beyond Python 3.11+ stdlib
- Absorb events.jsonl I/O failures into the FSM state write — they must fail independently (AC0 graceful degradation)
- Make `workspace_mcp` aware of specific adapter implementations — it is adapter-agnostic
- Store or replay notifications across sessions (ephemeral per-session design; nothing survives `stdin.close()`)
- Call `safety.write_jailed` or any write path except events.jsonl/events.pending (read-only by design for observability tools; git tools use subprocess, not write_jailed)

**Trusted-repo assumption (AC14, AC17):** The git tools (`git_commit`, `git_push`) run git's hook scripts (`pre-commit`, `commit-msg`, `pre-push`) without disabling them, because the pre-commit linting gate is a legitimate CI control. This pre-approval (AC17) assumes the repo's hooks are trusted. In untrusted-repo contexts (executing against a third-party or attacker-influenced repo), the six pre-approved git tools should be removed from `permissions.allow` before deployment. Stage 1 targets trusted-repo sessions only.

**Human-gate integrity assumption (AC7, AC11–AC13):** The `elicit()` tool's human-gate semantics rely on the ACP host faithfully relaying `elicitation/create` to a human operator. `request_id` matching (AC16c) is routing-only, not authentication — a control-plane compromise could satisfy its own elicitations. This is an out-of-scope threat for Stage 1; integrity is provided by the host's relay contract, not by workspace-mcp.

## Testing Strategy

**Unit tests (TDD) — materialized stubs before implementation:**
- `test_loop_engine_events_jsonl.py`: outbox protocol — write pending → atomic state write → append → delete (AC0); graceful degradation — monkeypatch events.jsonl append to raise PermissionError, assert FSM state write (`engine-state.json`) still succeeds and warning is logged (AC0); outbox recovery at `cmd_init` startup AND at `cmd_transition` entry (resume case) — replay or discard based on pending.to/seq match, crash-then-next-transition (AC0a)
- `test_workspace_mcp_event_bridge.py`: event bridge offset tracking; human-gate detection and enriched notification payload (AC3, AC7); partial-line buffering on torn-write — partial last line held at offset, completed on next poll, no crash (AC4); inode/truncation reset — inode change or size < offset → reset offset/buffer/run_id AND all FSM/gate fields to re-attach (AC5); seq deduplication — `seq ≤ last_emitted_seq` skipped without duplicate emission (AC6)
- `test_workspace_mcp_tools.py`: `workspace_status()` result shape, pack-presence filter, slug safety guard + containment check (AC8, AC9, AC10)
- `test_workspace_status_engine_autonomous.py`: `is_need_satisfied()` + `classify_entries()` + `analyze_bounded()` autonomous-dispatch mode — `shape:` absent from active AND backlog → unsatisfied; `research:` absent from backlog as type "research" → unsatisfied; default=False preserves existing semantics (AC19)
- `test_workspace_mcp_elicit.py`: capability detection, `elicitation/create` response routing, response-file O_EXCL guard (AC11, AC12, AC13)
- `test_workspace_mcp_git.py`: `check-ref-format` validation, `--` separator, output_pattern commit intersection, push two-sided branch check (AC14); discovery-mode returns error for mutating tools (AC15); FSM-mode guard — SPEC_PATH only and SPEC_PATH + DISPATCHED_ITEM both block mutating tools (AC15a)
- `test_workspace_mcp_stdin.py`: frame-size cap, malformed JSON quarantine, unknown request_id rejection (AC16)
- `test_workspace_mcp_lifecycle.py`: per-session exit on stdin close (AC22)

**Integration / Visual/manual QA:**
- End-to-end: `python3 -I -m agentbundle.workspace_mcp` with a real Claude Code session running a spec-plan work-loop. Validate AC3 (no seq gap), AC7 (gate notification payload), AC11 (elicit path at `SPEC-HUMAN-GATE`).
- AC21: run a spec-plan loop session without `mcpServers`; repeat with workspace-mcp configured; diff stdout — no diff expected. Record observed stdout from both runs.
- AC2: invoke alias script via `python3 packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py --help`; confirm output identical to `python3 -m agentbundle.workspace_mcp --help` (Goal-based).

**Goal-based checks:**
- `python3 -I -m agentbundle.workspace_mcp --help` exits 0 (AC1)
- `python -c "from agentbundle.workspace_mcp import DEFAULT_SESSION_INSTRUCTION; assert DEFAULT_SESSION_INSTRUCTION and 'elicit' in DEFAULT_SESSION_INSTRUCTION"` exits 0 (AC20)
- `agentbundle install core` on clean repo → Python: parse `.claude/settings.json`; assert all 6 MCP tool ids present in `permissions.allow` (AC17)
- `agentbundle install core` on repo with pre-existing `permissions.allow` → confirm existing entries preserved, no duplicates (AC18)
- `grep -E "^## \[Unreleased\]|Engine-Change-RFC: RFC-0078" packages/agentbundle/CHANGELOG.md` — both present (AC23)
- `python -c "from agentbundle.workspace_mcp import _LIFECYCLE_MANIFEST; assert set(_LIFECYCLE_MANIFEST.keys()) == {'work','shape','research','strategy','design','signal','brief'}"` exits 0 (AC24)
- `python3 -m pytest packages/agentbundle/tests/ -q` green

## Assumptions

1. Stage 0 spikes (a)–(e) all close with passing results before implementation begins.
2. The agentbundle Claude adapter can gain an additive-merge `permissions.allow` projection target without a breaking contract change. If false, AC17/AC18 are deferred: `(deferred: workspace-mcp-permissions-projection-contract)`.
3. Spike (b) result: `x-core/` is NOT the ACP v1 extension convention; observed form is `_<namespace>/method`. All references renamed to `_agentbundle.core/` before Stage 1. ADR-0068 updated.
4. `is_need_satisfied()` can accept an `autonomous_dispatch` parameter without changing default semantics for human-managed sessions.
