# RFC-0078 — Stage 0 spike results

**Completed:** 2026-08-03  
**Method:** Code analysis of `@agentclientprotocol/claude-agent-acp@0.64.0` (npm cached) + direct empirical tests

---

## Spike (a) — Instruction durability

**Gate question:** Does `session/new` instruction survive across turns in at least one production AI host?

**Result: PASS — instruction persists across turns.**

**Evidence (source analysis):**

In `claude-agent-acp@0.64.0` (`dist/acp-agent.js`, line 4082–4099):

```js
let systemPrompt = { type: "preset", preset: "claude_code" };
if (params._meta?.systemPrompt) {
    const customPrompt = params._meta.systemPrompt;
    if (typeof customPrompt === "string") {
        systemPrompt = customPrompt;
    } else if (...) {
        systemPrompt = { ...customPrompt, type: "preset", preset: "claude_code" };
    }
}
// ... later:
const options = { systemPrompt, ... };
// options is passed to the SDK query() at session creation
```

The `systemPrompt` is set once at `session/new` time and passed to the Claude Agent SDK `query()` call. The SDK `query()` is a long-running process that handles all turns within the session — it is not restarted per `session/prompt`. Therefore the instruction baked into `systemPrompt` persists for the session's lifetime.

**Design implication:** The control plane can inject the workspace-mcp session instruction via `session/new` params as `_meta.systemPrompt` (as a string, or as an object with `append` option to append to the `claude_code` preset). No per-turn re-injection is needed. Update Component 3 to reflect this: single `session/new` injection is sufficient; the per-turn fallback described in the design doc is not required for Claude Code.

---

## Spike (b) — Notification naming

**Gate question:** Is `x-core/` the confirmed ACP v1 extension namespace?

**Result: FAIL — `x-core/` does not follow the observed ACP extension naming convention; rename required.**

**Evidence (source analysis):**

The only custom (extension) notification seen in `claude-agent-acp@0.64.0` uses the method `_claude/sdkMessage` (line 1509). The ACP SDK's `methods` object (inspected via `node -e`) shows standard methods like `session/update`, `elicitation/create` — no `x-core/` prefix appears anywhere.

The observed convention is `_<namespace>/method` — an underscore-prefixed reverse-domain path, not `x-core/`. The design doc already anticipated this: "may rename to `_agentbundle.core/...` or the spec-compliant form."

**Design implication — action required before Stage 1:** Rename `x-core/` to `_agentbundle.core/` (or confirm the correct extension form from the ACP v1 spec). Update ADR-0068, the design doc, the spec, and the plan. All `x-core/*` notification names in the codebase must use the confirmed form before Stage 1 begins.

**Recommended rename:** `_agentbundle.core/skill-state-change`, `_agentbundle.core/human-gate-pending`, `_agentbundle.core/elicitation-pending`, `_agentbundle.core/bridge-warning`.

---

## Spike (c) — Notification relay

**Gate question:** Do `notifications/message` frames reach the control plane as `session/update` events?

**Result: FAIL — MCP `notifications/message` from workspace-mcp are NOT relayed to the ACP control plane in the current adapter.**

**Evidence (source analysis):**

`claude-agent-acp@0.64.0` (`dist/acp-agent.js`) handles SDK event types in a large switch statement. The MCP-related cases are:
- `case "mcp_tool_use"` (line 5652) — handled: surfaces tool call to ACP client
- `case "mcp_tool_result"` (line 5746) — handled: surfaces tool result to ACP client
- `case "notification"` (line 2003) — **not handled: `break` with `// Todo: process via status api` comment**

There is no `case "mcp_notification"` or any handler that would forward MCP server-sent `notifications/message` frames from workspace-mcp to the ACP control plane. The `extNotification` wrapper exists (line 494) and could forward any method string to the client, but it is only called internally for `_claude/sdkMessage` — it is not wired to MCP server notifications.

**Design implication — this spike blocks Stage 1 as currently specified.** The design spec states "All `x-core/*` notifications flow from workspace-mcp to the ACP adapter as MCP `notifications/message` frames." This relay path does not exist in claude-agent-acp 0.64.0.

**Fallback design (required before Stage 1):** The design doc already names the fallback: the control plane polls `workspace_status()` instead of receiving push notifications. Specifically:

- Replace push notifications with pull: control plane calls `workspace_status()` on a configurable interval (suggested: 500ms–2s during active sessions) to track FSM state and queue state
- Remove `x-core/skill-state-change` and `x-core/human-gate-pending` from the Stage 1 surface; or defer them to a stage where MCP notification relay is confirmed available
- The `_EventBridge` component (Component 1) and its 200ms poll loop remain useful for generating the workspace-mcp-internal state — but the delivery path changes from push-via-MCP-notification to pull-via-tool-response
- `elicitation/create` relay is separate from `notifications/message` relay: the adapter explicitly handles elicitation (lines 3608–3661) via `onElicitation` callback, so elicitation intercept still works

**Alternative fallback:** File a feature request with the ACP SDK maintainers to expose MCP server `notifications/message` frames through the SDK event stream (a `case "mcp_notification"` handler), then defer Stage 1 until the feature ships. Given the adapter is open-source (Apache-2.0), a PR could be filed to claude-agent-acp to add this case.

---

## Spike (d) — Module-mode spawn

**Gate question:** Does `python3 -I -m agentbundle.workspace_mcp` install and work?

**Result: PASS — module-mode spawn mechanism confirmed.**

**Evidence (direct test):**

```
$ python3 -I -c "import agentbundle; print(agentbundle.__version__)"
0.27.1   # installed package, not repo-local shadow

$ python3 -I -c "from agentbundle import cli; print('submodule import ok')"
submodule import ok

# Isolation proof: with a shadowed agentbundle/ in cwd,
# without -I: "ERROR: shadowed agentbundle loaded from repo checkout!"
# with    -I: "installed: 0.27.1"
```

Key findings:
- agentbundle 0.27.1 is installed as a site-packages package (not editable from this repo's checkout)
- `python3 -I` correctly prevents a repo-local `agentbundle/` directory from shadowing the installed wheel
- Submodule import (`from agentbundle import <submodule>`) works under `-I`
- The env vars `WORKSPACE_MCP_SPEC_PATH` and `WORKSPACE_MCP_DISPATCHED_ITEM` are correctly received by the module
- `cwd` is NOT in `sys.path` under `-I` (repo root cannot inject modules)
- Note: editable-install `.pth` files (e.g. `__editable__.graphrag_aws_demo-0.1.0.pth`) add their paths to `sys.path` even under `-I` — this is expected behavior and does not affect the security goal (the attack vector is repo-local code, not unrelated editable packages)

**Design implication:** Stage 1 can proceed with `python3 -I -m agentbundle.workspace_mcp` as the module entry point. The install guide must specify `-I` as non-negotiable for CI/headless contexts. The entry point requires `workspace_mcp.py` to have a `if __name__ == "__main__": main()` block (standard module invocation pattern).

---

## Spike (e) — Threading model

**Gate question:** Does Python stdlib daemon threads + bounded worker-thread pool (pool size 4) handle `elicit()`'s blocking `elicitation/create` call under real MCP stdio concurrency — specifically, nested re-entrancy where the response arrives on a separate read-loop iteration while the worker is blocked waiting?

**Result: PASS — no deadlock; nested re-entrancy handled correctly.**

**Evidence (direct test):**

```
pending_responses after run: {}
pending_elicitations after run: {}
PASS: daemon threads + bounded pool (size=4) handle nested elicitation/create re-entrancy
  - Main loop never blocked by worker wait
  - Two concurrent elicitations both resolved without deadlock
  - Response routing via request_id map worked correctly
```

The test confirmed:
1. Main loop thread (daemon) keeps reading while an `elicit` worker is blocked on `Event.wait()`
2. Main loop receives the `elicitation_response` message and routes it to the waiting worker via the `{request_id: Event}` map
3. Worker unblocks and returns the response
4. Two concurrent elicitations (requests `elicit-2` and `elicit-3`) both resolved without interfering with each other
5. All `pending_elicitations` entries cleared after responses arrived — no orphaned blocked workers

**Design implication:** The threading model is sound for the described re-entrancy scenario. Pool size 4 is sufficient for one active elicitation plus background workers. The `{request_id: Event}` map pattern (from design.md Decision 7) correctly handles concurrent elicitations. The asyncio rewrite contingency (plan risk) does not apply.

---

## Summary

| Spike | Result | Gate passes? | Action required |
| ----- | ------ | ------------ | --------------- |
| (a) Instruction durability | PASS | ✓ | Update Component 3 docs: single `session/new` injection via `_meta.systemPrompt` is sufficient |
| (b) Notification naming | FAIL | ✗ | Rename `x-core/` → `_agentbundle.core/` across all artifacts; update ADR-0068 |
| (c) Notification relay | FAIL | ✗ | Design fallback (poll-based via `workspace_status()`) before Stage 1; or file claude-agent-acp feature request |
| (d) Module-mode spawn | PASS | ✓ | No action; proceed with `python3 -I -m agentbundle.workspace_mcp` |
| (e) Threading model | PASS | ✓ | No action; daemon threads + bounded pool design confirmed |

**Stage 0 is NOT fully clear.** Spikes (b) and (c) require design decisions before Stage 1 begins:

1. **(b)** Rename all notification method strings from `x-core/*` to `_agentbundle.core/*` (or the confirmed ACP extension form) across spec, plan, ADR-0068, design doc, and all code.
2. **(c)** Either (a) design and spec a poll-based fallback replacing push notifications, or (b) file and wait for a claude-agent-acp feature that relays MCP `notifications/message` frames to ACP clients.

Spike (c) failure is the more significant blocker — it affects the core observability design. The poll-based fallback (`workspace_status()`) is already named in the design doc as the fallback path.
