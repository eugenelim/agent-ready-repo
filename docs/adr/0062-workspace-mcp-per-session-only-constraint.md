# ADR-0062: workspace-mcp per-session-only constraint

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision-makers:** eugenelim

## Decision summary

- **Decision:** `workspace-mcp` spawns once per session and exits when the session ends. No persistent daemon mode, no port binding, no background process that outlives the controlling AI agent session.
- **Because:** The project charter's Principle 3 ("a habit, not a tool") distinguishes the catalogue's primitives from infrastructure services. A persistent daemon would constitute infrastructure: it binds resources across sessions, requires lifecycle management, and creates a blast radius for crashes and stale state that the current tooling (loop-engine, workspace-status) does not expose. The per-session model is the minimal surface needed to close the ACP observability gap without becoming infrastructure.
- **Applies to:** `packages/agentbundle/agentbundle/workspace_mcp.py`; `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py`; any control-plane integration that spawns workspace-mcp; RFC-0078 and its follow-on spec/plan.
- **Tradeoff accepted:** A control plane that wants workspace-mcp for workspace discovery across sessions must open a short-lived *discovery session* (call `workspace_status()`, read the result, exit) rather than querying a persistent daemon. This adds one round-trip of latency per discovery cycle.
- **Revisit if:** The project charter is amended to include managed runtime services as in-scope primitives; or a persistent mode is requested by multiple adopters and a distinct RFC documents the lifecycle management, crash recovery, and security implications.

## Context

`workspace-mcp` is an MCP server that bridges loop-engine FSM events, workspace queue state, and git lifecycle to ACP control planes. RFC-0078 chartered it subject to the charter's Principle 3 constraint, and the decision to require per-session spawn was made at the design stage to keep workspace-mcp clearly on the "habit" side of the charter boundary.

The MCP stdio transport — stdin/stdout of the spawned child process — is architecturally per-session: it communicates with exactly one AI agent and exits when that agent's stdin closes. Multiple concurrent workspace-mcp instances on the same machine are fully isolated by process; there is no shared mutable state.

The per-session constraint also enforces the no-port-binding requirement: without a persistent process there is nothing to bind, eliminating a class of port-collision and firewall issues that would complicate adopter deployment.

## Alternatives rejected

**Persistent daemon with a Unix socket.** A long-lived process listening on a Unix socket would allow the control plane to query workspace state between sessions without spawning a new process. Rejected because it requires process supervision (restart on crash), socket lifecycle management (cleanup on unclean exit), and a documented security boundary around who may connect. These obligations push workspace-mcp past the "habit" threshold into infrastructure territory — a charter violation unless the charter is amended.

**SSE sidecar for real-time notifications.** A side-process emitting SSE events over HTTP would allow the control plane to receive FSM transitions without an open MCP session. Rejected for the same reason as the daemon, and additionally because SSE requires a persistent HTTP listener — port binding that violates this constraint.
