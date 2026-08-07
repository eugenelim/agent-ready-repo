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

## Apply the tiers the system earns — a progressive overlay

This overlay is **progressive**: it grows with what the system actually *is*, so
a plain RAG/chat design is never made to recite concerns that don't bite for it.
Three capability tiers, each gated on a capability the design declares:

- **Tier A — the LLM is on the path.** Apply **always**: the moment a model reads
  or writes anything on the critical path, Tier A is in scope.
- **Tier B — the system acts.** Apply once the design can **take action** — it
  calls tools, runs autonomous steps, or loops. A design that only generates text
  for a human to act on stays at Tier A.
- **Tier C — the agent persists or collaborates.** Split by capability:
  **memory & context integrity** applies once the agent **carries state across
  turns or sessions** (*stateful*); **sub-agent provenance** and **multi-agent
  coordination / identity propagation** apply once **more than one agent**
  collaborates (*multi-agent*). A single stateful agent picks up only the memory
  concern. (**Tool / MCP source provenance is a Tier-B concern**, not Tier C — it
  fires for *any* system that loads externally-sourced tools or MCP servers,
  single-agent included.)

These are **filters, not a worklist**. Name the concerns that bite for *this*
system, at the tier it has earned — never a generic recitation of the whole set.

## Tier A — the LLM is on the path

- **Prompt injection** — untrusted text (user input, retrieved documents, tool
  output, web content) reaching the model can hijack its instructions (OWASP
  LLM01, Prompt Injection). Where is the trust boundary between *instructions*
  and *data*? What can a hijacked turn actually cause? Treat model input as
  untrusted by default. When the design retrieves content or embeds documents
  (RAG, a vector store), that retrieved-content and embedding surface is itself
  an injection-and-disclosure vector (OWASP LLM08, Vector & Embedding
  Weaknesses) — poisoned, over-broad, or cross-tenant retrieval crosses the same
  instruction-vs-data and egress boundaries.
- **Data egress & disclosure** — bidirectional (OWASP LLM02, Sensitive
  Information Disclosure). *Outbound:* what internal/sensitive data crosses the
  boundary to an external model API, and is that egress intended, minimized, and
  contractually allowed (training opt-out, residency)? *Inbound-to-caller:* what
  can be extracted *from* the system through model output — secrets, system
  prompts, another user's data the caller isn't entitled to? The internal-data ↔
  external-model boundary is a first-class trust boundary, not plumbing.
- **Evaluation** — how is output quality measured (an eval set, not vibes)? Is
  the judgment corroborated — an LLM-as-judge *and* a deterministic check rather
  than either alone? A design with no eval story has no way to tell a regression
  from a bad day.
- **Token cost** — token spend is a unit-economics axis that scales with usage
  and can dwarf compute. What's the cost per request at p50/p99, and what bounds
  a multi-turn history that grows unboundedly or a prompt-injected spend? This is
  the denial-of-wallet surface (OWASP LLM10, Unbounded Consumption) — paired with
  the Tier-B loop-cap concern, which bounds the *runaway-loop* half of the same
  risk.
- **Observability** — are prompts, tool calls, and responses traceable enough to
  debug a bad turn at 3am, with content captured **off by default** (it carries
  the egress/disclosure surface above)? Non-determinism makes observability
  harder, not optional. OpenTelemetry's GenAI semantic conventions are the
  converging instrumentation standard here — though still **Development**-status
  (maturing, not yet stable), so treat them as the direction of travel, not a
  settled contract.

## Tier B — the system acts

- **Tool-use authorization & bounded autonomy** — an agent that can call tools
  acts with whatever authority those tools carry (OWASP LLM06, Excessive Agency).
  Are tool permissions scoped to least privilege? Is each destructive or
  outbound-spending tool gated behind confirmation or a policy check? This bullet
  forces the explicit design-time question: **what is the tool allowlist, and
  which actions require confirmation?** "The agent can take actions" with no
  allowlist and no confirmation criteria is the named design-time miss — an
  over-broad tool is a confused deputy waiting to happen.
- **Tool / MCP source provenance** — where do the tools and MCP servers this
  agent loads come from, and is the source trusted (OWASP LLM03, Supply Chain)?
  This fires for *any* externally-sourced tool or MCP load, single-agent
  included — an unverified MCP server is an untrusted instruction-and-action
  surface, not merely a dependency.
- **Output handling** — model output is untrusted input to the next sink (OWASP
  LLM05, Improper Output Handling). Is it validated or escaped before it drives a
  tool call, a shell command, a query, an HTML render, or a follow-on action?
  Treat the model as the *source* of injection here.
- **Execution isolation & blast radius** — for tools that run code or process
  untrusted content, what is the sandbox posture, and what is the blast radius if
  a call goes wrong? This is distinct from *authorization* (who may call) — it is
  *containment* (what a call can reach once made).
- **Human oversight & graduated autonomy** — what is the oversight posture: which
  decisions keep a human *in* the loop (approve before acting) versus *on* the
  loop (monitor and interrupt)? Widening autonomy is **engineering judgment, not
  a standards mandate** — name what evidence would justify widening it, and the
  hard cap that **irreversibility and blast radius bound how far autonomy widens
  regardless of track record**: a partially-reversible or high-blast-radius
  action defaults to gated however reliable the agent has been.
- **Intent verification** — before an irreversible or outbound action, is the
  agent's *planned action chain* surfaced for confirmation, and are reversible
  actions preferred over irreversible ones? Verifying intent against the plan is
  how a confused-deputy or hijacked turn is caught *before* it acts, not after.
- **Auditability & attributable action trails** — is every action the agent takes
  attributable to a principal and reconstructable after the fact (what was
  decided, on what input, under whose authority)? An action trail you can't
  replay is an incident you can't investigate.
- **Reliability under non-determinism** — what enforces a max-iteration / loop cap
  *outside* the model, so a runaway agent can't spend without bound (the
  runaway-loop half of OWASP LLM10, Unbounded Consumption, paired with the Tier-A
  token-cost concern)? Are tool calls idempotent where retried, and does the
  system degrade gracefully when the model returns garbage or a tool fails?
- **Synchronous long-running turn** — an agent turn is the canonical
  long-running operation; if it sits behind a synchronous front door, does the
  worst-case turn fit the binding timeout? Apply the serverless lens's
  sync-vs-async gate for the mechanics (it fires even when the runtime is not
  itself serverless).

## Tier C — the agent persists or collaborates

- **Memory & context integrity** *(stateful)* — when the agent carries state
  across turns or sessions, what stops that memory from being poisoned — a
  malicious past turn, a tainted retrieved document, an injected "fact" that
  steers later decisions (OWASP LLM04, Data & Model Poisoning)? Persisted context
  is an instruction surface that outlives the turn that wrote it.
- **Sub-agent provenance** *(multi-agent)* — when an agent delegates to other
  agents, where do those delegated agents come from and is each trusted? This is
  the multi-agent-gated facet of the same supply-chain trust question as Tier-B
  tool/MCP provenance (OWASP LLM03), not a distinct control — a delegated agent
  is another externally-defined actor in the loop.
- **Multi-agent coordination, inter-agent trust & identity/privilege
  propagation** *(multi-agent)* — across a delegation chain, how is trust
  established between agents, and how do identity and privilege propagate — does
  a sub-agent inherit more authority than the request that spawned it should
  carry? Privilege that amplifies as it crosses agents is the multi-agent
  confused-deputy.

## Routes into the security boundary

The security-boundary concerns above name trust boundaries, least privilege, and
egress minimization at **design altitude only**; control-level verification
routes to the repo's `security-reviewer` / `security-checklists` (the `llm-agent`
module), per `cross-cutting-questions.md`. The concerns that route to a named
module check: prompt injection, data egress & disclosure, tool-use
authorization, tool/MCP & sub-agent provenance, output handling, the token /
loop-cap consumption surface, and — for a system that acts, delegates, or
persists state — **execution isolation & blast radius**, **inter-agent
identity/privilege propagation**, and **memory poisoning**.

Name these boundaries at design altitude here; their control-level verification
routes to the `llm-agent` module like every other security-boundary concern
above. Name implementation frameworks never — this lens reasons about boundaries
and authority, not whether to use a particular agent framework or vector store.

## Use, don't recite

Apply the concerns that bite for *this* agentic system, at the tier it has
earned. A self-hosted single-tool assistant and a multi-agent system with
outbound spend authority have very different injection, tool-authz, and
coordination surfaces — name theirs, not a generic list.
