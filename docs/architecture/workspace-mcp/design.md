# Workspace MCP

`workspace-mcp` is a per-session stdio MCP server for an agentbundle-equipped
repository. It gives an ACP control plane four capabilities: workspace
readiness (`workspace_status`), controlled elicitation (`elicit`), lifecycle-scoped
Git operations (`git_status`, `git_branch`, `git_commit`, `git_push`), and
loop-state notifications.

It exits with its session, binds no network port, reads
the loop event stream, and never writes it. Readiness comes from running the
packaged `work-loop` dispatch, so the server holds no readiness logic of its own.

## 1. Structure

The server is one module, `agentbundle.workspace_mcp`, started with
`python3 -m agentbundle.workspace_mcp`. The `workspace-status` skill also ships
a thin launcher, `scripts/workspace_mcp_server.py`, that imports it.[^1] Tool
calls run on a bounded thread pool, and a single write lock serializes
responses.

| Tool | Behavior |
| --- | --- |
| `workspace_status` | Runs dispatch, maps each ready, active, or blocked spec to an item, and adds bound loop state |
| `elicit` | Sends `elicitation/create` when the client declares the capability, else waits for a response file |
| `git_status`, `git_branch`, `git_commit`, `git_push` | Lifecycle-scoped Git after manifest validation |

Two environment variables bind a session. `WORKSPACE_MCP_SPEC_PATH` binds an FSM
session and `WORKSPACE_MCP_DISPATCHED_ITEM` binds a non-FSM item. Mutating Git
tools are available only when `WORKSPACE_MCP_DISPATCHED_ITEM` binds a non-FSM
item.

[^1]: `packages/agentbundle/agentbundle/workspace_mcp.py` (`main`, `_dispatch_tool`); `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py`.

## 2. Readiness: packaged dispatch

`workspace_status` calls `dispatch()` from the copy of `work-loop`'s `dispatch.py`
packaged in `agentbundle/_data/`. It never loads a repository, installed-skill,
or pack copy, because the tool runs in the control plane's trust domain and must
not execute repository-controlled code. From a zipapp, where `_data/` is not a
directory, the five source files are copied into a private temporary directory
and loaded from there.[^2]

The result keeps dispatch's `canonical` payload and returns `ready`, `active`,
and `blocked` items of type `work`. `shaping` is always empty. Each item carries
`slug`, `path`, `dispatchable`, `findings`, `dispatch_skill`, `output_pattern`,
`has_gates`, and `required_pack`.

An item whose dispatch skill is not installed
under any of six pack roots gets `available: false`. A slug that fails the slug
guard or a non-spec item is skipped. If dispatch raises, the tool returns an
empty `ready` and `active` and one canonical failure in `blocked`.

Dispatch reads `workspace.toml` only to refuse. While that file holds an entry
it refuses with `unmigrated_workspace`, until `workspace-status repair-apply`
moves the entries.

A refusal carries empty `ready`, `active`, and `blocked`
lists, so `workspace_status` returns those three lists empty. The refusal
appears only in `canonical.decision` (`action: refuse`) and
`canonical.findings`, and a client that reads only `blocked` sees no blocked
work.[^3]

The lifecycle manifest (dispatch skill and output pattern per item type) is a
built-in constant. The `workspace-types.d/` extension that
[ADR-0067](../../adr/0067-lifecycle-manifest-builtin-defaults-workspace-types-d.md)
decides is not read by the server. **STATUS: PLANNED.**

[^2]: `_load_packaged_dispatch` and `_DISPATCH_FILES` in `packages/agentbundle/agentbundle/workspace_mcp.py`.
[^3]: `_WorkspaceStatusTool.call` in `workspace_mcp.py`; `_refused` in `packs/core/.apm/skills/work-loop/scripts/dispatch.py`.

## 3. State and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Session process state | Server process | `workspace_mcp.py` | ACP client and agent |
| Event offset | Per-session server state | `workspace_mcp.py` | Event bridge |
| Response file | Per-elicitation temporary directory (mode 0700) | ACP client response writer | `elicit` |
| Loop events | `.loop-run/events.jsonl` | `work-loop` `work-supervisor.py` | Event bridge |
| Full-mode run status | `docs/specs/<feature>/.supervisor/run.json` | `work-loop` `work-supervisor.py` | Event bridge and `workspace_status` (display only) |
| Workspace lifecycle | Artifact headers; `workspace.toml` holds legacy entries only | Owning workflow | `workspace_status`, Git tools |

The server reads `run.json` through the confined regular-file read with a 64 KiB
bound. A link, non-regular, oversized, unreadable, or malformed file leaves the
session with no run and no gate.

## 4. Event bridge and elicitation

The event bridge tails matching `.loop-run/events.jsonl` events by byte offset
and emits `_agentbundle.core/` state and human-gate notifications. The run id,
`run_active`, stage, and pending gate come from `run.json`, and `current_state`
is its stage. A gate question passes a content-safety check and appears only
inside inert framing.

A rejected or oversized question shows a fixed
placeholder. The bridge only displays the gate. A human answer reaches the
supervisor only through its own `human-decision` request.[^4]

`elicit` publishes a response file by exclusive creation and atomic rename in
the private directory. A partial or different-UID pre-seeded response cannot be
consumed. Same-UID isolation is not guaranteed, so the response-file path is for
clients without elicitation support (Codex, Kiro CLI).

[^4]: `_EventBridge`, `_ElicitTool` in `workspace_mcp.py`; [ADR-0064](../../adr/0064-events-jsonl-as-fsm-event-source.md), [ADR-0065](../../adr/0065-elicit-elicitation-create-response-file-fallback.md), [ADR-0068](../../adr/0068-notification-namespace-x-core.md).

## 5. Git tools

Git tools validate the dispatched lifecycle manifest before any subprocess. A
staging scope's wildcard structure comes only from that manifest. A configured
`output_dir` supplies the scope's static base and nothing else, and a base
carrying `*`, `?`, `[`, `{`, or `}` is refused before it reaches the pattern.

A
refused `output_dir` leaves `git_commit` unavailable for that item with an error
naming the configuration section, and the other Git tools stay available.
Pre-staged files outside the dispatched output pattern cause a refusal.
A slug must match
`^[a-zA-Z0-9._-]+$` and cannot be `.`, `..`, or begin with `-`.

Manifest branch
validation routes pushes and does not authenticate them.

## 6. Failure and recovery

If the event file shrinks or its inode changes, the bridge resets its offset and
rediscovers the run identifier from `run.json`. It holds a partial final event
until the next poll. A missing events file while `.loop-run/` exists adds an
`EVENTS-FILE-MISSING` warning to the loop-state fields.

The server does not enforce isolated mode. Python `-I` keeps a
repository-provided `agentbundle/` directory from shadowing the installed wheel.
The spawner must start the server with `-I` in an untrusted checkout, and
nothing in the server or the launcher checks that it did.[^6]

[^6]: Module docstring of `packages/agentbundle/agentbundle/workspace_mcp.py`, which lists `-I` as the isolated mode for CI and testing; `packs/core/.apm/skills/workspace-status/scripts/workspace_mcp_server.py` imports the module with no flag check.

## 7. Mechanical invariants

Behavior tests cover the tool surface, event bridge and poller, supervisor-run
reading, elicitation, Git tools, dispatch, and the dependency read.[^5] No check
verifies notification delivery against a live ACP client.

[^5]: `packages/agentbundle/tests/**/test_workspace_mcp_*.py`.

## 8. Relevant ADRs

- [ADR-0062](../../adr/0062-workspace-mcp-per-session-only-constraint.md) — per-session constraint
- [ADR-0064](../../adr/0064-events-jsonl-as-fsm-event-source.md) — events JSONL as FSM event source
- [ADR-0065](../../adr/0065-elicit-elicitation-create-response-file-fallback.md) — elicit response-file fallback
- [ADR-0067](../../adr/0067-lifecycle-manifest-builtin-defaults-workspace-types-d.md) — lifecycle manifest defaults and `workspace-types.d/`
- [ADR-0068](../../adr/0068-notification-namespace-x-core.md) — notification namespace
- [ADR-0069](../../adr/0069-threading-model-daemon-threads-bounded-pool.md) — threading model
- [ADR-0144](../../adr/0144-work-loop-supervisor-owns-procedure.md) — supervisor owns procedure (D10 moves the run-id source to `run.json`)

[Workspace MCP production readiness](../../product/intents/workspace-mcp-production-readiness.md)
owns the remaining hardening.
