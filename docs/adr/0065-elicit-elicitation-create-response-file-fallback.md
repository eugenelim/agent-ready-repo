# ADR-0065: elicit() tool + elicitation/create + response-file fallback

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision-makers:** eugenelim

## Decision summary

- **Decision:** workspace-mcp implements a two-tier elicitation delivery mechanism: (1) primary — `elicitation/create` in MCP server→client direction (workspace-mcp requests a structured response from the AI host), bridged by the AI host through the ACP adapter as an `_agentbundle.core/elicitation-pending` event to the control plane; (2) fallback — a temporary response file written to an `mkdtemp()`-isolated directory, polled by workspace-mcp until the control plane writes the response using the temp-and-rename protocol.
- **Because:** `elicitation/create` is the MCP-native path (MCP 2025-06-18, standard server→client direction) and delivers structured gate decisions with type enforcement. However, not all adapters support it: Codex CLI does not list `elicitation/create` as a feature (Stage 2a validation confirmed); Kiro CLI's support is unconfirmed. The response-file fallback is the correct secondary path for adapters that do not support `elicitation/create`. A single implementation that gracefully degrades covers both cases without per-adapter branching in skills.
- **Applies to:** `packages/agentbundle/agentbundle/workspace_mcp.py` (Component 3 — the `elicit()` MCP tool and its two delivery paths); adapter-capability detection in the MCP init handshake; the response-file security constraints documented in the design doc.
- **Tradeoff accepted:** The response-file path introduces a polling loop and a race window (same-user process can race `O_EXCL` creation before workspace-mcp does at session start). The response-file fallback is used only for adapters that do not support `elicitation/create`; when `elicitation/create` is available it is the primary path. The response-file path is not a secure gate for multi-user or shared-machine deployments; this is documented in the install guide.
- **Revisit if:** Codex CLI and Kiro CLI add `elicitation/create` support, making the fallback unnecessary for all Class A/B adapters in scope; or a third elicitation delivery mechanism becomes available that closes the race window without requiring MCP `elicitation/create` support.

## Context

`elicitation/create` is defined in the MCP specification (2025-06-18) as a server→client request: the server asks the client (AI host) to elicit a structured response from the user, with the response typed and validated by the schema in the request. ACP v1 adapts this mechanism — the AI host bridges the `elicitation/create` request through the ACP adapter as a structured event to the control plane.

workspace-mcp calls `elicitation/create` synchronously (blocking until the AI host responds) from a worker thread, while the main stdio loop continues reading incoming MCP messages. This is the re-entrancy requirement: the `elicitation/create` response arrives on the same MCP stdio channel that the main loop is reading, so a single-threaded handler that blocks on the `elicit()` call would deadlock.

The capability-declaration bug in `claude-agent-acp` (issue #419) means workspace-mcp must check the AI host's capability list during the MCP init handshake: if `elicitation` is absent from the host's declared capabilities, workspace-mcp omits it from its own init response and uses the response-file fallback. The check happens at init, not at the call site, because the failure mode is at init (not at the `elicitation/create` call).

The response-file protocol requires the control plane to write the response atomically using temp-and-rename (write to a temp file in the same directory, then `rename()`). workspace-mcp reads the file only once the rename completes; a partial write is never observed.

## Alternatives rejected

**Webhook delivery.** The control plane registers an HTTP endpoint; workspace-mcp POSTs the elicitation request to it. Requires the control plane to expose an inbound HTTP endpoint and workspace-mcp to know its URL. Adds a network dependency and a firewall/proxy concern. Rejected in favor of the MCP-native `elicitation/create` path, which uses the existing MCP channel with no new network surface.

**SSE event stream for elicitations.** workspace-mcp emits an SSE event when an elicitation is pending; the control plane listens and responds via a separate `session/prompt`. Requires a persistent HTTP listener on workspace-mcp's side — port binding that violates ADR-0062's per-session-only constraint. Rejected.

**Per-adapter branching in skills.** Each skill checks which adapter is present and delivers gate questions through different code paths. Rejected by ADR-0063 (session instruction as the universal mechanism): if the session instruction is the universal elicitation router, the delivery path is workspace-mcp's internal concern, not the skill's.

**Response-file as the only path (no elicitation/create).** Simpler — one code path, no MCP extension. Rejected because it loses structured typing (the response is free-form text in the file, not a typed schema), and because `elicitation/create` is the MCP standard that future AI hosts will increasingly support.
