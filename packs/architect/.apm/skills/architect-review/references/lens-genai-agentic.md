# GenAI / agentic lens — the workload-class overlay for LLM-driven systems

A workload-class lens for systems where an LLM or an agent is on the critical
path: it reviews the *same* design through the concerns that flat pillars miss
for generative/agentic workloads. AI/GenAI is the clear first-class workload
class across all three cloud vendors (AWS GenAI + Responsible-AI lenses, Google
AI/ML perspective, Azure AI-in-operations) — this is the cloud-agnostic
distillation of that overlay.

> Note: this reference is intentionally duplicated from `architect-design`'s
> `references/lens-genai-agentic.md`. Skill autonomy beats DRY at this scale —
> each skill stands alone. See the pack README.

## Distinct from the managed-platform agentic *diagram* refs

`architect-diagram` ships `agentic-bedrock-agentcore.md`, `agentic-ai-foundry.md`,
and `agentic-vertex-agent-engine.md` — those are *diagram vocabularies* for three
managed agent platforms. This lens is **not** that. It is a provider-agnostic
*design-quality* overlay, and it applies **even when the agent runtime is
self-hosted on primitives** (no managed agent platform in sight). Reasoning about
quality is the job here; drawing a managed platform is not.

## The concerns

- **Prompt injection** — untrusted text (user input, retrieved documents, tool
  output, web content) reaching the model can hijack its instructions. Where is
  the trust boundary between *instructions* and *data*? What can a hijacked turn
  actually cause? Treat model input as untrusted by default.
- **Tool-use authorization** — an agent that can call tools acts with whatever
  authority those tools carry. Are tool permissions scoped to least privilege?
  Is a destructive or outbound-spending tool gated behind confirmation or a
  policy check? An agent with an over-broad tool is a confused-deputy waiting to
  happen.
- **Data egress to the LLM** — what internal/sensitive data crosses the boundary
  to an external model API? Is that egress intended, minimized, and contractually
  allowed (training opt-out, residency)? The internal-data → external-LLM
  boundary is a first-class trust boundary, not plumbing.
- **Evals & observability** — how is output quality measured (an eval set, not
  vibes)? Are prompts, tool calls, and responses traced enough to debug a bad
  turn at 3am? Non-determinism makes observability harder, not optional.
- **Token cost** — token spend is a unit-economics axis that scales with usage
  and can dwarf compute. What's the cost per request at p50/p99, and what stops a
  runaway loop or a prompt-injected spend?

## Routes into the security boundary

Prompt-injection, tool-use authz, and data-egress are security-boundary
concerns. This lens names them at design altitude (trust boundaries, least
privilege, egress minimization); control-level verification routes to the repo's
`security-reviewer` / `security-checklists` (the `llm-agent` module), per
`cross-cutting-questions.md`. Name frameworks never — the lens reasons about
boundaries and authority, not whether to use a particular agent framework or
vector store.

## Use, don't recite

Apply the concerns that bite for *this* agentic system. A self-hosted single-tool
assistant and a multi-agent system with outbound spend authority have very
different injection and tool-authz surfaces — name theirs, not a generic five.
