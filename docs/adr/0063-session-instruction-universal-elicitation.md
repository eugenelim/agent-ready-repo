# ADR-0063: Session instruction for universal elicitation interception

- **Status:** Accepted
- **Date:** 2026-08-03
- **Decision-makers:** eugenelim

## Decision summary

- **Decision:** Elicitation interception is implemented by injecting a single session-level instruction at startup (via `session/new.instruction` or equivalent), not by modifying individual skills to check for and call a `gate_request` or similar tool at their decision points.
- **Because:** The gate problem is not limited to formal FSM states. Every skill elicits from the user — desk-research asks clarifying questions, place-bet asks for prioritization, journey-mapping asks about personas. Covering all of these via per-skill modification scales as O(skills × questions) and requires every future skill to know about workspace-mcp. The session instruction is strictly less coupling: it is injected once and applies to all skills without modification.
- **Applies to:** `packages/agentbundle/agentbundle/workspace_mcp.py` (Component 3 — universal elicitation via session instruction); the session instruction template embedded in workspace-mcp; all control-plane integrations that use workspace-mcp.
- **Tradeoff accepted:** Session instruction compliance is prompt-following, not enforced. The AI may not always call `elicit()` for very short one-word responses ("sure", "yes"). The instruction is strongest for questions with options or structured decisions; it is weakest for affirmations. This residual gap is accepted for the current scope; long-term mitigation is upstream (Claude Code system-prompt enforcement).
- **Revisit if:** Claude Code (or another AI host) exposes a system-prompt enforcement surface that allows workspace-mcp to guarantee elicitation routing; or the non-compliance rate for structured decisions exceeds an acceptable threshold (to be measured in Stage 3 validation).

## Context

The ACP observability gap extends beyond work-loop's FSM states. Desk-research asks clarifying questions and writes briefs to disk. Frame-intent and place-bet ask for prioritization and option selection. Journey-mapping elicits persona information. Every one of these is an AI→user interaction that the control plane is currently blind to.

A per-skill approach (each gate-capable skill calls `gate_request` or similar) was evaluated first (see Alternatives). It covers declared gate states but not informal elicitations, requires skill modifications that multiply indefinitely as new skills are added, and makes each skill aware of whether a control plane is present — coupling the skill to the deployment topology.

The session instruction approach treats the AI agent as the universal proxy: a preamble injected at `session/new` time instructs the AI to route all questions and decisions through `elicit()` rather than emitting them as plain text. The AI then mediates between the skill's elicitation need and the control plane's response, with no skill modification required.

## Alternatives rejected

**Per-skill `gate_request` tool check.** Each gate-capable skill (work-loop, new-spec, place-bet) checks at decision points if a `gate_request` tool is available and calls it. This covers declared gate states only — it misses the majority of AI→user communication that happens through informal elicitations. Covering all informal elicitations via this approach is the same problem as the session instruction, multiplied across every skill, indefinitely. Rejected because it delivers less coverage at greater coupling cost.

**Hook in the AI runtime.** A Claude Code hook that intercepts all assistant messages and routes them through workspace-mcp. This would require changes to the AI host itself, is not feasible for an open-source skill pack, and would intercept non-elicitation output (progress notes, explanations) alongside actual questions — creating noise without structural disambiguation.

**Session/prompt injection at each gate.** The control plane re-injects the decision into a new `session/prompt` when a gate is detected. This is the best-effort fallback path for adapters that support neither `elicitation/create` nor the response-file fallback; it is not the primary design because it requires the control plane to detect the gate from free-form text (the original problem).
