# Runtime mechanism crosswalk

**Purpose:** Map Pi, Claude Code, Codex, Conductor, and tmux mechanisms onto the
neutral contracts owned by the execution supervisor.
**Author:** Platform Core
**Status:** Draft
**Last updated:** 2026-10-01
**Reviewers:** Runtime-adapter and Core maintainers

## 1. Scope and Context

This document maps runtime mechanisms, not product equivalence. The
[execution supervisor](work-loop-execution-supervisor.md) owns the contracts;
no runtime named here owns acceptance meaning or becomes mandatory.

## 2. Pi Reference Decomposition

| Pi package or surface | Architectural lesson | Agent-ready-repo mapping | Adoption |
| --- | --- | --- | --- |
| `pi-ai` | Providers sit below loops | Runtime capability | Retain the seam, not the API |
| `pi-agent-core` | Tool and event loop is separable | Agent extension | First native adapter pattern |
| `pi-coding-agent` | Interfaces share mechanics | Supervisor transports | Pattern only |
| Extensions and resources | Executable modules stay outside core policy | Extensions and skills | Procedure outside policy |
| Sessions and `pi-durable` | Conversation is not product truth; durability is optional | Journal adapter | Attempts, never acceptance proof |
| `pi-telemetry` | Events cross typed adapter contracts | Supervisor events and fixtures | Adopt the pattern |
| `chord` and `pi-tui` | Multiprocess services and UI sit above the runtime | Deferred transports | No core dependency |

## 3. Runtime Crosswalk

The named sources are [Pi packages](https://github.com/earendil-works/pi#all-packages),
[Claude Code architecture](https://code.claude.com/docs/en/how-claude-code-works),
[Claude Code extensions](https://code.claude.com/docs/en/features-overview),
[Conductor parallel agents](https://www.conductor.build/docs/concepts/parallel-agents),
[Conductor workspaces](https://www.conductor.build/docs/concepts/workspaces-and-branches),
[Git worktrees](https://git-scm.com/docs/git-worktree), and
[tmux sessions](https://github.com/tmux/tmux/wiki/Getting-Started).

| Concern | Agent-ready-repo target | Current work-loop | Pi | Claude Code | Conductor | tmux |
| --- | --- | --- | --- | --- | --- | --- |
| Policy and context | Skills state obligations | Skill mixes policy and procedure | Resources, prompts, skills | `CLAUDE.md`, rules, skills | Project instructions | Configuration only |
| Agent loop | Runtime extension | Active host works around phase commands | `pi-agent-core` | Built-in harness loop | Selected coding agent | Any attached process |
| Tool and model binding | Provider capability | Host is implicit | `pi-ai`, tools, providers | Tools, MCP, plugins | Hosted agent | None |
| Transport | Request/result contracts | Python engine and cohort commands | JSON, RPC, SDK | CLI, SDK, hooks | UI, terminal, API | CLI and control socket |
| Recovery state | Replaceable journal | Engine/cohort events and locks | Sessions; optional `pi-durable` | Resumable session | Workspace, branch, chat, process | Server, session, window, pane |
| Parallelism | Scheduler plus workspace and agent capabilities | Cohorts and waves | Extension concern | Subagents and sessions | Shared or isolated workspaces | Panes without isolation |
| Verification and review | Evidence and reports | Gates and reviews drive phases | Extension concern | Tools and hooks | Checks and diff review | Process output only |
| Security | Shared file/process confinement | Prose plus helpers | OS authority unless sandboxed | Permissions and hooks | Workspace is not security | Child-user authority |

## 4. Adapter Invariants

| Invariant | Enforcement |
| --- | --- |
| Runtime sophistication cannot change delivery meaning | Every adapter passes the shared semantic and recovery suite |
| A workspace or terminal is not a sandbox | Untrusted execution requires a verified host containment capability |
| Session loss cannot erase acceptance facts | Sessions and journals contain only repairable mechanical state |
| Missing runtime capabilities degrade safely | The selector chooses the sequential floor or refuses before dispatch |
| Provider-specific APIs do not enter skill policy | Typed requests and results terminate at the adapter boundary |

## 5. Verification authority

The execution supervisor's
[runtime support matrix](work-loop-execution-supervisor.md#7-quality-scenarios-and-verification)
is the sole owner of support status, capability declarations, and required
conformance. This crosswalk adds no runtime-specific proof obligation.
