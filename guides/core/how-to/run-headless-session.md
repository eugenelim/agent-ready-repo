# Run a headless session with workspace-mcp

A control harness drives Claude Code sessions programmatically — no human watching each turn. workspace-mcp is the per-session MCP server the `core` pack ships for exactly this use: structured queue discovery, FSM-state observability, and scoped git operations.

**What your harness gets:** `workspace_status()` returns the queue of ready and blocked items. Gates surface as `gate_pending: true` with a `gate_question` the harness routes to a human.

**Stage 1 scope:** Claude Code via ACP. Codex is planned; Kiro CLI, Copilot CLI, and Gemini CLI are deferred.

## Prerequisites

- `agentbundle install --pack core` run in the target repo
- Python 3.11+ on the machine running the harness
- An ACP-capable control harness — Claude Code via the `claude-agent-acp` bridge or native Agent SDK
- `workspace.toml` with at least one initiative in the target repo (see [orient at session start](orient-at-session-start.md))

## Step 1 — Enable headless permissions

Claude Code requires explicit permission for each MCP tool before a headless session can use it. Without this, sessions hang waiting for interactive approval.

Add the six `workspace-mcp` tool strings to `permissions.allow` in `.claude/settings.json` in the target repo:

```json
{
  "permissions": {
    "allow": [
      "mcp__workspace-mcp__workspace_status",
      "mcp__workspace-mcp__elicit",
      "mcp__workspace-mcp__git_status",
      "mcp__workspace-mcp__git_branch",
      "mcp__workspace-mcp__git_commit",
      "mcp__workspace-mcp__git_push"
    ]
  }
}
```

> Automated permission projection is an open item — hand-edit `.claude/settings.json` or include the block in your repo's seed files until it ships.

## Step 2 — Discover the work queue

Open a short-lived discovery session with no environment variables. Send a prompt asking the agent to call `workspace_status()`, then read the `ready[]` and `shaping[]` arrays to choose what to dispatch.

```json
{
  "method": "session/new",
  "params": {
    "cwd": "/absolute/path/to/repo",
    "mcpServers": [
      {
        "name": "workspace-mcp",
        "command": "python3",
        "args": [".claude/skills/workspace-status/scripts/workspace_mcp_server.py"]
      }
    ]
  }
}
```

The `workspace_status()` response:

```json
{
  "ready": [
    {
      "ini_slug": "my-initiative",
      "type": "work",
      "slug": "fix-login-bug",
      "dispatch_skill": "work-loop",
      "has_gates": true
    }
  ],
  "shaping": [],
  "blocked": [],
  "active": [],
  "gate_pending": false,
  "current_state": null
}
```

Pick an item from `ready[]` or `shaping[]`. Skip items where `unmet_needs` is non-empty (blocked) or `available` is `false` (required pack not installed — run `agentbundle install --pack <required_pack>` first). Close the discovery session.

## Step 3 — Dispatch the item

The env var you set depends on the item's `type`. One env var selects the session mode.

### Work items (`type: "work"`, `dispatch_skill: "work-loop"`)

Set `WORKSPACE_MCP_SPEC_PATH` to the spec directory path (relative to `cwd`). work-loop manages its own git lifecycle — `git_branch`, `git_commit`, and `git_push` are intentionally unavailable. The harness role is to monitor `workspace_status()` and respond to gates.

```json
{
  "method": "session/new",
  "params": {
    "cwd": "/absolute/path/to/repo",
    "mcpServers": [
      {
        "name": "workspace-mcp",
        "command": "python3",
        "args": [".claude/skills/workspace-status/scripts/workspace_mcp_server.py"],
        "env": [
          { "name": "WORKSPACE_MCP_SPEC_PATH", "value": "docs/specs/fix-login-bug" }
        ]
      }
    ],
    "_meta": {
      "systemPrompt": "<DEFAULT_SESSION_INSTRUCTION>"
    }
  }
}
```

Then send the first message to start the agent (the session is idle until a prompt arrives):

```json
{
  "method": "session/prompt",
  "params": {
    "sessionId": "<id from session/new response>",
    "prompt": [{ "type": "text", "text": "Run the work-loop for the dispatched item at docs/specs/fix-login-bug." }]
  }
}
```

### Non-FSM items (`type: "research"` | `"design"` | `"shape"` | `"strategy"`)

> **Stage 3 (planned).** The workspace-mcp git tools for non-FSM item types are
> wired in the server, but the agent-side skill flows that drive research, design,
> shape, and strategy items headlessly are not yet shipped. This section documents
> the MCP wire format for when those skills land.

Set `WORKSPACE_MCP_DISPATCHED_ITEM` as `{ini_slug}/{type}:{slug}`. This unlocks `git_branch`, `git_commit`, and `git_push` scoped to the item's configured output paths.

```json
{
  "method": "session/new",
  "params": {
    "cwd": "/absolute/path/to/repo",
    "mcpServers": [
      {
        "name": "workspace-mcp",
        "command": "python3",
        "args": [".claude/skills/workspace-status/scripts/workspace_mcp_server.py"],
        "env": [
          { "name": "WORKSPACE_MCP_DISPATCHED_ITEM", "value": "my-initiative/research:competitive-analysis" }
        ]
      }
    ]
  }
}
```

Retrieve the session instruction at runtime:

```python
from agentbundle.workspace_mcp import DEFAULT_SESSION_INSTRUCTION
```

> **Trusted checkouts only:** The spawn args above use the projected adapter path (`.claude/skills/…`). This requires `agentbundle install --pack core` to have run in the checkout. Untrusted-repo / isolated-mode support (`python -I`) is deferred to Stage 2.

## Step 4 — Monitor progress

Poll `workspace_status()` after each response from the agent to check whether the work-loop has reached a gate:

```python
status = call_tool("workspace_status")
if status["gate_pending"]:
    gate     = status["gate"]           # e.g. "SPEC-HUMAN-GATE"
    question = status["gate_question"]  # the specific question to route
    # send question to your human channel; collect answer
```

Key fields in the response:

| Field | Type | Meaning |
|---|---|---|
| `current_state` | string \| null | Work-loop FSM phase; null when idle |
| `gate_pending` | bool | True when human input is required before work continues |
| `gate` | string \| null | Gate name — e.g. `SPEC-HUMAN-GATE`, `REVIEW-HUMAN-GATE` |
| `gate_question` | string \| null | The specific question the work-loop is asking |
| `ready` | array | Build items (type: work) dispatchable now |
| `shaping` | array | Non-FSM items (research, design, shape, strategy); entries with `unmet_needs` are blocked; entries with `available: false` need their `required_pack` installed |
| `active` | array | Items currently in progress |
| `blocked` | array | Items with unmet dependencies |
| *(per item)* `available` | bool \| absent | `false` when the item's `dispatch_skill` is not installed; absent when available |
| *(per item)* `required_pack` | string \| null | Pack to install when `available: false`; e.g. `"desk-research"` (use `agentbundle install --pack <value>`) |

> **Stage 1 note:** The `claude-agent-acp` bridge does not relay MCP push notifications to the harness in this release. Poll `workspace_status()` after each session update rather than relying on notification events.

## Step 5 — Respond to gates

When `gate_pending` is true, the work-loop is paused waiting for a human decision. The `DEFAULT_SESSION_INSTRUCTION` directs the agent to call `elicit(gate_question)` at gate states. This means **gate responses require ACP elicitation**, not `session/prompt`.

### Required: declare elicitation capability

Declare elicitation support under `clientCapabilities` in the ACP init handshake. `claude-agent-acp` reads `clientCapabilities.elicitation.form` (or `.url`) — `capabilities.elicitation` is not the correct key and leaves MCP forwarding disabled. At minimum, include:

```json
{
  "method": "initialize",
  "params": {
    "clientCapabilities": {
      "elicitation": { "form": true }
    }
  }
}
```

The agent then sends `elicitation/create` and blocks until the harness resolves it:

1. The agent calls `elicit()` → workspace-mcp sends an MCP `elicitation/create` JSON-RPC request to the harness (server→client)
2. Your harness receives the request, routes the question to the human channel
3. Your harness returns the human's answer as the JSON-RPC response to the `elicitation/create` request
4. The `elicit()` call unblocks and the work-loop continues

> **Stage 1 limitation — response-file fallback unsupported.** When `clientCapabilities.elicitation`
> is absent, `elicit()` falls back to a temp response file. The file path is carried only in the
> `_agentbundle.core/elicitation-pending` MCP push notification, which the Stage 1 bridge drops
> (see Stage 1 note above). The harness cannot discover the file path, so the fallback always
> times out after 300 seconds. Declare `clientCapabilities.elicitation` or the gate will hang.

> **`session/prompt` is not a gate-response mechanism.** Sending `session/prompt` while `elicit()`
> is pending sends a new message to the model without resolving the blocking tool call. The
> `elicit()` call remains blocked and the session does not make progress.

## When it doesn't work

| Symptom | Cause | Fix |
|---|---|---|
| Session hangs indefinitely | Missing `permissions.allow` entries | Add all six `mcp__workspace-mcp__*` strings to `.claude/settings.json` (Step 1) |
| `workspace_status()` returns `{"error": "workspace_status_engine.py not found…"}` | `agentbundle install --pack core` has not been run in the checkout | Run `agentbundle install --pack core` in the target repo |
| `git_branch`, `git_commit`, or `git_push` returns `"not available in work-loop (FSM) mode"` | `WORKSPACE_MCP_SPEC_PATH` is set — work-loop manages its own git lifecycle; mutating git tools are blocked | Expected for work items; monitor gates, don't call git mutating tools |
| `git_commit` returns `"git_commit unavailable: no output_pattern (work-loop owns git)"` | `WORKSPACE_MCP_DISPATCHED_ITEM` set for a `work`-type item without `WORKSPACE_MCP_SPEC_PATH` | Use `SPEC_PATH` for work items (not `DISPATCHED_ITEM`); `DISPATCHED_ITEM` is for non-FSM types only |
| `git_commit` returns `"refusing commit: N pre-staged file(s) outside output_pattern"` | The repo has pre-staged files outside the item's output paths | Unstage those files before calling `git_commit`, or use `git reset HEAD` |
| `git_branch` returns `"session branch already set"` | `git_branch` was called a second time in the same dispatched session | `git_branch` may only be called once per non-FSM session; a resumed session may already have a locked branch |
| Item slug not found in `workspace.toml` | `WORKSPACE_MCP_DISPATCHED_ITEM` references a slug that doesn't exist in the queue | Verify the slug against `workspace_status()` `ready[]` before dispatching |

## Reference

Full workspace-mcp architecture, notification contract, security constraints, deferred adapter roadmap, and Class B (Kiro CLI) setup: [`docs/architecture/workspace-mcp/design.md`](../../../docs/architecture/workspace-mcp/design.md).
