# ADR-0069: Threading model — daemon threads and bounded worker pool

- **Status:** Accepted (pending validation from Stage 0 spike (e))
- **Date:** 2026-08-03
- **Decision-makers:** eugenelim

## Decision summary

- **Decision:** workspace-mcp uses Python stdlib threading throughout: (1) the event bridge and artifact watcher run on daemon threads that poll independently without blocking the main stdio handler; (2) `elicit()` tool calls — which block until the AI host responds to the nested `elicitation/create` request or until the response file appears — are dispatched to a bounded worker-thread pool (pool size: 4); (3) the main stdio loop reads and dispatches incoming MCP messages to either the daemon threads (for event/watcher triggers) or the worker pool (for blocking tool calls); (4) shared stdout is guarded by a single write lock; (5) the main loop maintains a `{request_id: Event/queue}` map to route incoming `elicitation/create` responses to the correct waiting worker.
- **Because:** workspace-mcp is a pure-stdlib Python 3.11+ process (no new dependencies). asyncio is the idiomatic Python concurrency model for I/O-bound work but requires the entire callchain to be async-aware, which is complex for a stdlib-only stdio MCP server with mixed blocking and polling behaviors. The daemon-thread + bounded-pool model separates concerns cleanly: polling loops (event bridge, artifact watcher) run independently of request handling; blocking tool calls (elicit) run in the pool without starving other requests; the main loop stays non-blocking.
- **Applies to:** `packages/agentbundle/agentbundle/workspace_mcp.py` (the threading architecture, pool initialization, write lock, and request-response routing map).
- **Tradeoff accepted:** Python's GIL means stdlib threads do not achieve true CPU parallelism, but all workspace-mcp work is I/O-bound (file reads, subprocess calls, MCP stdio reads/writes) — the GIL is not a bottleneck. Pool size 4 is chosen because workspace-mcp serves one client per session (per ADR-0062); pool > 1 handles nested `elicitation/create` re-entrancy where the response arrives on a separate read-loop iteration while the original `elicit` worker is blocked waiting. The threading model is validated by Stage 0 spike (e); if it cannot handle real MCP stdio concurrency (specifically nested re-entrancy), an asyncio rewrite is required before Stage 1.
- **Revisit if:** Stage 0 spike (e) reveals that stdlib threading cannot handle nested `elicitation/create` re-entrancy (async rewrite triggered); or workspace-mcp is extended to serve multiple clients per instance (Stage 4 multi-session, which changes the pool-size calculation); or Python 3.13+ per-interpreter GIL changes the threading performance profile enough to reconsider asyncio.

## Context

workspace-mcp's concurrency requirements come from three sources:

1. **Background polling.** The event bridge polls `.loop-run/events.jsonl` every 200ms. The artifact watcher polls output directories every 200ms. Both are I/O-bound and must not block the MCP request handler.

2. **Blocking tool calls.** The `elicit()` tool handler blocks synchronously: it sends an `elicitation/create` request to the AI host and waits for the response. The response arrives on the same MCP stdio channel that the main loop is reading. A single-threaded handler that blocks on `elicit()` would deadlock: the main loop cannot read the `elicitation/create` response while it is blocked handling the `elicit()` tool call.

3. **Stdout serialization.** Multiple threads may attempt to write MCP response frames to stdout concurrently (worker threads writing `elicit()` results; daemon threads writing notification frames). A write lock prevents interleaved frames.

The bounded pool (size 4) is sufficient for per-session spawn: each workspace-mcp instance serves exactly one AI agent (one client). Pool size > 1 is needed only for nested `elicitation/create` re-entrancy — the scenario where an outer `elicit()` worker is waiting on an `elicitation/create` response, and the control plane sends a second `elicitation/create` response on the same channel before the outer response resolves. With pool size 4, up to 3 nested levels of re-entrancy are supported (one worker blocked at each level, one free to handle the response). In practice, re-entrancy beyond depth 1 is unexpected; pool size 4 provides margin.

The `{request_id: Event/queue}` map in the main loop routes incoming MCP messages (including `elicitation/create` responses) to the correct waiting worker by matching `request_id` fields. The main loop posts the response to the worker's Event/queue; the worker unblocks and completes the `elicit()` tool call.

## Alternatives rejected

**asyncio throughout.** The entire server is async-native: the main loop is an asyncio event loop, tool handlers are coroutines, background polling runs as asyncio tasks. This is the most idiomatic Python 3.11+ concurrency model and eliminates the threading complexity. Rejected for the initial implementation because: (a) converting a blocking subprocess-based git tool to fully async requires `asyncio.create_subprocess_exec`, increasing code complexity; (b) pure-stdlib asyncio MCP stdio server is a non-trivial pattern that requires careful framing to avoid mixing async and sync code; (c) the daemon-thread model delivers the same functional outcome (non-blocking main loop, concurrent polling and blocking calls) with simpler code. If spike (e) shows the threading model is insufficient, asyncio is the designated fallback.

**Cooperative polling in the request handler (no threads).** The event bridge and artifact watcher run as polling steps inside the MCP message handler loop — check for events, check for artifacts, handle one MCP message, repeat. This is single-threaded but prevents `elicit()` from blocking: the handler polls and checks the response file on each iteration until it appears. Rejected because it conflates polling cadence with MCP message throughput; a slow poll (waiting for a response) would delay all other MCP message processing during that window.

**Single-thread with `select()`/`selectors`.** A `selectors`-based single-thread multiplexes stdin (MCP messages), event log file descriptors, and a timeout for polling. This avoids threads but cannot handle `elicit()`'s blocking `elicitation/create` response wait, which is not a file descriptor select — it is waiting for a specific MCP response message identified by `request_id`. The `selectors` model does not solve the routing problem. Rejected.
