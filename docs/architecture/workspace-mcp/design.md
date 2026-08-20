# Workspace MCP

## 1. Purpose and boundary

`workspace-mcp` is a per-session, stdio MCP server for an
agentbundle-equipped repository. It exposes workspace status, controlled
elicitation, scoped Git operations, and loop-state observations to an ACP
control plane.

It exits with its session and binds no network port. It reads loop events but
does not write the event stream.

## 2. Entrypoints

- `python3 -m agentbundle.workspace_mcp` starts the server.
- `workspace_status` reads workspace and bound-loop state.
- `elicit` sends a client elicitation request or uses the response-file
  fallback.
- `git_status`, `git_branch`, `git_commit`, and `git_push` provide
  lifecycle-scoped Git operations.
- `WORKSPACE_MCP_SPEC_PATH` binds an FSM session.
  `WORKSPACE_MCP_DISPATCHED_ITEM` binds a non-FSM item. Neither enables
  mutating tools in discovery mode.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Session process state | Server process | `workspace_mcp.py` | ACP client and agent |
| Event offset | Per-session server state | `workspace_mcp.py` | Event bridge |
| Response file | Per-elicitation temporary directory | ACP client response writer | `elicit` |
| Loop events | `.loop-run/events.jsonl` | `loop-engine.py` | Workspace MCP event bridge |
| Workspace lifecycle | `workspace.toml` and artifacts | Owning workflow | `workspace_status` and Git tools |

## 4. Dependencies and allowed edges

Workspace MCP reads `workspace.toml`, lifecycle artifacts, and
`.loop-run/events.jsonl`. It tails events by byte offset and never writes them.

The server invokes loop and Git operations through its bounded tool surface.
Git tools validate the dispatched lifecycle manifest before subprocess use.
Third-party pack types may extend `workspace-types.d/` additively.

## 5. Primary flows

1. The control plane starts a bound or discovery session and the agent calls
   `workspace_status`.
2. The event bridge tails matching loop events and emits namespaced state and
   human-gate notifications.
3. `elicit` sends `elicitation/create` when the client supports it; otherwise
   it waits for an atomically published response file.
4. Git tools validate output paths and branch before status, branch, commit, or
   push operations.

## 6. Failure and recovery behavior

If an event file shrinks or its inode changes, the bridge resets its offset and
rediscovers the run identifier. It holds a partial final event until the next
poll.

Response files use a private directory, exclusive creation, and atomic rename.
A partial or different-UID pre-seeded response cannot be consumed. Same-UID
isolation is not guaranteed.

Pre-staged files outside the dispatched output pattern cause a Git refusal.
Discovery and FSM modes disable mutating Git tools. Invalid slugs are rejected
before output-pattern construction: they must match `^[a-zA-Z0-9._-]+$` and
cannot be `.`, `..`, or begin with `-`. Manifest branch validation routes pushes
but does not authenticate them.

Untrusted checkouts start with Python `-I`. Isolated mode prevents a
repository-provided `agentbundle/` directory from shadowing the installed wheel.

## 7. Observability and evidence

`workspace_status` returns ready, shaping, blocked, and active items with
unmet dependencies and bound FSM fields. The event bridge emits
`_agentbundle.core/` notifications and records its byte-offset progress.

Git tool results, response paths, lifecycle artifacts, and the loop event stream
provide the session evidence record.

## 8. Mechanical invariants

None. No supplied command mechanically verifies workspace-MCP's runtime
security boundaries or notification delivery.

## 9. Relevant ADRs

- [ADR-0062 — Workspace MCP per-session constraint](../../adr/0062-workspace-mcp-per-session-only-constraint.md)
- [ADR-0064 — Events JSONL as FSM event source](../../adr/0064-events-jsonl-as-fsm-event-source.md)
- [ADR-0065 — Elicit create response-file fallback](../../adr/0065-elicit-elicitation-create-response-file-fallback.md)
- [ADR-0068 — Notification namespace x-core](../../adr/0068-notification-namespace-x-core.md)
- [ADR-0069 — Threading model: daemon threads and bounded pool](../../adr/0069-threading-model-daemon-threads-bounded-pool.md)

## 10. Last verified against commit

`c8cf4b37`
