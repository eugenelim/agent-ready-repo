# Run a headless session with workspace-mcp

A control harness drives Claude Code sessions programmatically — no human watching each turn. workspace-mcp is the per-session MCP server the `core` pack ships for exactly this use: structured queue discovery, FSM-state observability, and scoped git operations.

**What your harness gets:** `workspace_status()` returns the queue of ready and blocked items. Gates surface as `gate_pending: true` with a `gate_question` the harness routes to a human. Git operations are scoped to the dispatched item's output paths so the agent cannot commit outside its lane.

**Stage 1 scope:** Claude Code via ACP. Codex is planned; Kiro CLI, Copilot CLI, and Gemini CLI are deferred.

## Prerequisites

- `agentbundle install core` run in the target repo
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

Open a short-lived discovery session with no environment variables. Send a prompt asking the agent to call `workspace_status()`, then read the `ready[]` array to choose what to dispatch.

```json
{
  "method": "session/new",
  "params": {
    "cwd": "/absolute/path/to/repo",
    "mcpServers": {
      "workspace-mcp": {
        "command": "python3",
        "args": [".claude/skills/workspace-status/scripts/workspace_mcp_server.py"]
      }
    }
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
  "blocked": [],
  "active": [],
  "gate_pending": false,
  "current_state": null
}
```

Pick an item from `ready[]`. Close the discovery session.

## Step 3 — Dispatch the item

Construct `WORKSPACE_MCP_DISPATCHED_ITEM` as `{ini_slug}/{type}:{slug}` from the chosen item. Open a bound session with both env vars and the session instruction:

```json
{
  "method": "session/new",
  "params": {
    "cwd": "/absolute/path/to/repo",
    "mcpServers": {
      "workspace-mcp": {
        "command": "python3",
        "args": [".claude/skills/workspace-status/scripts/workspace_mcp_server.py"],
        "env": {
          "WORKSPACE_MCP_SPEC_PATH": "docs/specs/my-initiative/fix-login-bug",
          "WORKSPACE_MCP_DISPATCHED_ITEM": "my-initiative/work:fix-login-bug"
        }
      }
    },
    "_meta": {
      "systemPrompt": "<DEFAULT_SESSION_INSTRUCTION>"
    }
  }
}
```

`WORKSPACE_MCP_SPEC_PATH` is the spec directory path relative to `cwd`. Setting both env vars unlocks `git_branch`, `git_commit`, and `git_push`, and scopes commits to the item's configured output paths.

Retrieve the session instruction at runtime:

```python
from agentbundle.workspace_mcp import DEFAULT_SESSION_INSTRUCTION
```

**CI / untrusted checkouts:** swap `args` for isolated mode:

```json
"args": ["-I", "-m", "agentbundle.workspace_mcp"]
```

The `-I` flag prevents the repo's files from influencing Python's import path. Required for untrusted code; omit only for developer-owned checkouts.

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
| `ready` | array | Items dispatchable now |
| `active` | array | Items currently in progress |
| `blocked` | array | Items with unmet dependencies |

> **Stage 1 note:** The `claude-agent-acp` bridge does not relay MCP push notifications to the harness in this release. Poll `workspace_status()` after each session update rather than relying on notification events.

## Step 5 — Respond to gates

When `gate_pending` is true, the work-loop is paused waiting for a human decision. Route `gate_question` to your human-in-the-loop channel, collect the answer, and resume with `session/prompt`:

```json
{
  "method": "session/prompt",
  "params": {
    "sessionId": "<id from session/new response>",
    "prompt": "Approved. Proceed with the implementation as planned."
  }
}
```

If your harness implements `session/create_elicitation`, the agent's `elicit()` tool routes questions through that channel automatically — no polling required for inline questions. The `session/prompt` pattern works in all cases as a fallback.

## Reference

Full workspace-mcp architecture, notification contract, security constraints, deferred adapter roadmap, and Class B (Kiro CLI) setup: [`docs/architecture/workspace-mcp/design.md`](../../../../docs/architecture/workspace-mcp/design.md).
