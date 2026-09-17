# ADR-0068: Notification namespace — _agentbundle.core/

- **Status:** Accepted
- **Date:** 2026-08-03
- **Areas:** orchestration, telemetry
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** updated 2026-08-03 from Stage 0 spike (b) result

## Decision summary

- **Decision:** Custom ACP notifications emitted by workspace-mcp use the `_agentbundle.core/` prefix (e.g., `_agentbundle.core/skill-state-change`, `_agentbundle.core/human-gate-pending`). The placeholder `x-core/` used at design time is retired.
- **Because:** Stage 0 spike (b) found that the only custom (extension) notification observed in `claude-agent-acp@0.64.0` uses the method name `_claude/sdkMessage` — an underscore-prefixed reverse-domain path (`_<namespace>/method`). The `x-core/` form (HTTP-header convention) does not match this pattern. `_agentbundle.core/` follows the same `_<namespace>/method` convention as `_claude/sdkMessage` and is the agentbundle core pack's correct extension namespace.
- **Applies to:** `packages/agentbundle/agentbundle/workspace_mcp.py` (all notification emission points); control-plane integration code that subscribes to `_agentbundle.core/*` notifications; documentation in design.md and docs/rfc/0078-workspace-mcp.md; the spec and plan.
- **Tradeoff accepted:** The rename from `x-core/` to `_agentbundle.core/` is a pre-Stage-1 global rename across all in-tree artifacts. A grep-and-replace is the mitigation.
- **Revisit if:** The ACP v1 specification is updated to define a different extension-naming convention; or a different namespace is adopted by the agentbundle ecosystem.

## Context

MCP `notifications/message` is the standard mechanism for servers to emit events to clients. ACP v1 adapts this: the AI host bridges `notifications/message` frames from workspace-mcp through the ACP adapter as `session/update` events to the control plane. The `type` field of the notification determines what the control plane can subscribe to and act on.

ACP v1 defines an extension-naming rule for custom notification types. The rule parallels IANA extension naming (HTTP, MIME) in using a vendor or project namespace to prevent type conflicts. The placeholder `x-core/` was used during design; Stage 0 spike (b) evaluated it against the observed ACP convention and confirmed `_agentbundle.core/` as the correct form.

Not using a namespace at all — emitting bare names like `skill-state-change` — risks collision with future standard ACP notification types and with other MCP server notifications in a multi-server session.

## Decision

Custom ACP notifications emitted by workspace-mcp carry the `_agentbundle.core/` prefix.

- **D1:** Custom (extension) ACP notifications emitted by workspace-mcp use the `_agentbundle.core/` prefix, following the observed ACP `_<namespace>/method` convention.
- **D2:** No notification is emitted under a bare, un-namespaced name.
- **D3:** The placeholder `x-core/` is retired, and the rename to `_agentbundle.core/` is applied across every in-tree artifact before Stage 1 — all emission points in `packages/agentbundle/agentbundle/workspace_mcp.py`, control-plane subscriber code, design.md, `docs/rfc/0078-workspace-mcp.md`, the spec, and the plan.
- **D4:** Every custom notification shares that one prefix, so the control plane can subscribe with the single pattern `_agentbundle.core/*` rather than per event type.

## Consequences

**Revisit if:** the ACP v1 specification defines an extension-naming convention other than `_<namespace>/method` (D1); or the agentbundle ecosystem adopts a different namespace, which re-runs the tree-wide rename D3 accepted.

## Alternatives considered

**Bare notification names (no namespace).** `skill-state-change`, `human-gate-pending`, etc. Rejected because collision with standard ACP types is plausible as the ACP specification evolves, and collision with other MCP servers in a multi-server session is possible.

**`x-core/` form.** HTTP-header-style naming (`x-` vendor prefix). Rejected by spike (b) result: the only custom notification observed in `claude-agent-acp@0.64.0` uses `_claude/sdkMessage` — not `x-core/` — confirming the ACP extension convention is `_<namespace>/method`, not the HTTP-header form.

**Per-notification custom type (no shared prefix).** Each notification type uses a unique opaque identifier rather than a shared namespace prefix. Rejected because it makes the subscription pattern `_agentbundle.core/*` impossible; the control plane must subscribe to each event individually, creating a maintenance surface as new event types are added.
