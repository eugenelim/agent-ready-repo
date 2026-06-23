# Dogfood — `architect-design` Stage 0 workload-class routing (AC: dogfooded end-to-end)

Manual QA per the spec's Testing Strategy and plan T7. The *built*
`architect-design` skill (`SKILL.md` step 3 + `references/lens-genai-agentic.md`)
was exercised on two concepts via an independent walkthrough — what the
procedure loads and which tiers gate is recorded below, not just a passing grep.

## Concept 1 — agentic (AWS customer-support refund agent)

> A customer-support agent on AWS that reads a user's ticket, searches an
> internal KB (RAG over a vector store), can autonomously issue refunds up to $50
> via a payments tool or escalate to a human, loads two third-party MCP servers
> (shipping-status, CRM), and runs a plan→act loop with retry on tool failure.
> Single agent, no persistent memory.

**Loaded:** provider axis → `well-architected-pillars.md` + `tradeoffs-and-sensitivity.md`
(trigger: named provider "AWS"); workload-class axis → `lens-genai-agentic.md`
(trigger matched on all three: tool-use, autonomous action, agent loop).
**Axes are additive** — both the AWS pillars and the agentic overlay load.

**Tiers that gate:**
- **Tier A (always):** prompt injection (untrusted ticket + RAG/embedding LLM08 surface), data egress & disclosure, evaluation, token cost, observability — all bite.
- **Tier B (the system acts):** tool-use authz & bounded autonomy (the $50 ceiling is the bounded-autonomy decision), **tool/MCP source provenance** (two third-party MCP servers — fires single-agent), output handling (output drives the payments tool), execution isolation & blast radius, human oversight & graduated autonomy (escalate path; $50 cap), intent verification, auditability, reliability under non-determinism (loop cap + idempotent retry) — all bite.
- **Tier C — correctly suppressed:** memory & context integrity does **not** fire (concept states "no persistent memory" → *stateful* gate unmet); sub-agent provenance + multi-agent coordination/identity-propagation do **not** fire ("single agent" → *multi-agent* gate unmet). MCP provenance lands at **Tier B**, exactly as the lens specifies — loading external MCP servers does not drag in Tier C.

## Concept 2 — plain RAG / non-acting (Azure docs Q&A assistant)

> An internal docs Q&A assistant on Azure: retrieve top-k passages from a vector
> store, model writes a grounded, cited answer. No actions, no tools, no
> persistence.

**Loaded:** provider axis → `well-architected-pillars.md` + `tradeoffs-and-sensitivity.md`
(trigger: named provider "Azure"); workload-class axis → `lens-genai-agentic.md`
at **Tier A baseline only** (trigger: generative, LLM on the critical path; the
widened generative-or-agentic trigger means a non-acting RAG design still loads
the overlay, and the overlay gates itself to Tier A).

**Tiers that gate:**
- **Tier A (always):** prompt injection (question + retrieved-passages/embedding surface), data egress & disclosure, evaluation, token cost, observability — bite.
- **Tier B — correctly silent:** the system takes no action (no tools, no autonomy, no loop) → "stays at Tier A." Tool/MCP provenance does **not** fire (no external tools).
- **Tier C — correctly silent:** no persistence → no memory concern; single, no delegation → no multi-agent concerns.

## Verdict

Routing fires correctly. The agentic concept loads **both** axes and lights
Tier A + the full Tier B while correctly suppressing all of Tier C; the
plain-RAG concept loads the provider pillars plus the overlay at **Tier A only**,
with Tier B/C correctly silent. The progressive filter does real work in both
directions — it is not a recite-the-whole-list checklist.
