# Runtime mechanism comparison

**Bottom line:** Pi, Claude Code, Conductor, and tmux each realize the same
concerns (policy, loop, transport, recovery, parallelism, verification,
security) with different mechanisms. None of them owns acceptance meaning. The
work-loop supervisor's contract targets are in
[`runtime-adapter-crosswalk.md`](../../architecture/runtime-adapter-crosswalk.md).

## Sources

[Pi packages](https://github.com/earendil-works/pi#all-packages),
[Claude Code architecture](https://code.claude.com/docs/en/how-claude-code-works),
[Claude Code extensions](https://code.claude.com/docs/en/features-overview),
[Conductor parallel agents](https://www.conductor.build/docs/concepts/parallel-agents),
[Conductor workspaces](https://www.conductor.build/docs/concepts/workspaces-and-branches),
[Git worktrees](https://git-scm.com/docs/git-worktree), and
[tmux sessions](https://github.com/tmux/tmux/wiki/Getting-Started).

## Pi reference decomposition

| Pi package or surface | Architectural lesson | Agent-ready-repo mapping | Adoption |
| --- | --- | --- | --- |
| `pi-ai` | Providers sit below loops | Runtime capability | Retain the seam, not the API |
| `pi-agent-core` | Tool and event loop is separable | External agent extension consuming the neutral protocol | Compatibility target; no bundled adapter or Core dependency |
| `pi-coding-agent` | Interfaces share mechanics | Supervisor transports | Pattern only |
| Extensions and resources | Executable modules stay outside core policy | Extensions and skills | Procedure outside policy |
| Sessions and `pi-durable` | Conversation is not product truth; durability is optional | Journal adapter | Attempts, never acceptance proof |
| `pi-telemetry` | Events cross typed adapter contracts | Supervisor events and fixtures | Adopt the pattern |
| `chord` and `pi-tui` | Multiprocess services and UI sit above the runtime | Deferred transports | No core dependency |

## Mechanism comparison

| Concern | Pi | Claude Code | Conductor | tmux |
| --- | --- | --- | --- | --- |
| Policy and context | Resources, prompts, skills | `CLAUDE.md`, rules, skills | Project instructions | Configuration only |
| Agent loop | `pi-agent-core` | Built-in harness loop | Selected coding agent | Any attached process |
| Tool and model binding | `pi-ai`, tools, providers | Tools, MCP, plugins | Hosted agent | None |
| Transport | JSON, RPC, SDK | CLI, SDK, hooks | UI, terminal, API | CLI and control socket |
| Recovery state | Sessions; optional `pi-durable` | Resumable session | Workspace, branch, chat, process | Server, session, window, pane |
| Parallelism | Extension concern | Subagents and sessions | Shared or isolated workspaces | Panes without isolation |
| Verification and review | Extension concern | Tools and hooks | Checks and diff review | Process output only |
| Security | OS authority unless sandboxed | Permissions and hooks | Workspace is not security | Child-user authority |
