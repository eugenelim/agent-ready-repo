# ADR-0064: events.jsonl as the FSM event source

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision-makers:** eugenelim

## Decision summary

- **Decision:** workspace-mcp's event bridge tail-polls `.loop-run/events.jsonl` — an append-only ephemeral file that loop-engine writes on each FSM transition (Stage 1 work item: AC0 in the spec) — using byte-offset-based seek-and-read, rather than receiving events over an in-process IPC channel or a separate network socket. loop-engine's CLI interface is unchanged; only its internal behavior gains the events.jsonl append and outbox protocol.
- **Because:** loop-engine is a standalone CLI tool invoked by the AI agent. Wiring it to emit events over IPC or a network socket would require loop-engine to know about workspace-mcp's presence — making the CLI adapter-aware and coupling it to the deployment topology. The events.jsonl file requires only internal changes to loop-engine (add the append in `cmd_transition` and `cmd_init`, with the outbox protocol for crash-consistency); it does not change loop-engine's external CLI contract or require it to know about workspace-mcp.
- **Applies to:** `packages/agentbundle/agentbundle/workspace_mcp.py` (Component 1 — event bridge); loop-engine's `.loop-run/events.jsonl` append behavior; the outbox pattern for crash-consistent transitions.
- **Tradeoff accepted:** There is a small window between loop-engine appending an event and workspace-mcp reading it (poll interval: configurable, default 200ms). Transitions within this window are not missed — the bridge tracks byte offset and reads all unread bytes on each poll — but real-time latency is bounded by the poll interval rather than being push-based. Rapid back-to-back transitions (e.g., `wave-passed` followed immediately by `gates-clean`) are both captured on the next poll cycle.
- **Revisit if:** loop-engine gains a stable IPC facility (Unix socket, named pipe) without becoming adapter-aware; or the poll latency becomes unacceptable for a specific control-plane integration that requires sub-100ms transition delivery.

## Context

loop-engine is designed as a pure CLI state machine: it enforces legal transition ordering and writes FSM state to disk (`engine-state.json`). It has no knowledge of who consumes its output or how. This clean boundary is the property that makes loop-engine usable across unattended sessions, supervisor mode, and human-driven sessions without modification.

workspace-mcp must bridge loop-engine events to the MCP/ACP surface without violating this boundary. The events.jsonl file is the chosen interface. Stage 1 adds the events.jsonl append to loop-engine — a pure-internal change (new behavior in `cmd_transition` and `cmd_init`; the CLI contract is unchanged). Once that is in place, workspace-mcp tails the file by tracking a byte offset and reading new bytes on each 200ms poll cycle. Each appended line contains `{"seq", "run_id", "spec", "from", "event", "to", "at"}` (canonical schema: design.md:317); the `run_id` field filters events to the current session. `spec` is the spec-directory path (matching `WORKSPACE_MCP_SPEC_PATH`); `from` and `to` are FSM state names; `at` is the ISO-8601 timestamp.

The outbox pattern (write pending event to `.loop-run/events.pending`, commit state atomically, append to events.jsonl, delete pending) ensures that a crash between the state write and the events.jsonl append is recoverable: on restart, the bridge verifies `pending.to == engine-state.json.state` before replaying the pending event. This closes the phantom-event window from unconditional replay.

Inode/truncation detection (tracking file inode and size alongside byte offset) handles the case where `.loop-run/events.jsonl` is deleted and recreated (e.g., by `loop-engine reset`): when the inode changes or the file size is smaller than the tracked offset, the bridge resets its offset, buffer, and run_id to reattach to the new file.

## Alternatives rejected

**In-process IPC channel (Unix socket, named pipe).** loop-engine emits events over an IPC channel that workspace-mcp subscribes to. This delivers events with push-based latency (no polling) and eliminates the offset-tracking complexity. Rejected because it requires loop-engine to manage connection lifecycle (accept, send, handle disconnection) and to know whether a subscriber is present. The CLI becomes adapter-aware, violating the clean boundary that makes it reusable across deployment contexts.

**Database table (SQLite, etc.).** loop-engine writes transitions to a local SQLite database; workspace-mcp polls the table. Delivers queryable history and indexed lookup. Rejected because it adds a runtime dependency (or a significant stdlib workaround), is overkill for the append-only, single-consumer, ephemeral event stream that workspace-mcp needs, and requires schema management that events.jsonl avoids entirely.

**Shared in-process queue (if loop-engine were a library).** If loop-engine were imported as a Python library rather than invoked as a CLI, it could post directly to a thread-safe queue that workspace-mcp drains. Rejected because converting loop-engine to a library would require reimplementing its CLI surface as a programmatic API, changing the primary interface that the work-loop skill's step commands rely on.
