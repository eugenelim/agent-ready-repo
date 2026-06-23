# RFC-0042: Agentic well-architected overlay as a first-class workload-class lens (design + review)

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental (optional: trial running, results pending — see the Experiment / validation section) -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-23
- **Date closed:** 2026-06-23
- **Related:** `docs/specs/well-architected-cloud/` (Shipped/frozen — the 5-concern lens this widens); RFC-0032 (architect `design-reviewer`); ADR-0023 ("three reviewers" ceiling scopes core code-review lenses); RFC-0029 (`security-reviewer` / `security-checklists` `llm-agent` module the overlay routes to); RFC-0041 (`operational-safety` progressive-disclosure reference-library precedent)

## The ask

**Recommendation (BLUF):** Promote the GenAI/agentic well-architected overlay from a review-time-only reference into a **first-class workload-class lens** that `architect-design` loads **by construction** *and* `architect-review` loads in WA mode — the **same shared lens file**, consumed at both times — and expand its content from today's five concerns to a **progressive, capability-tiered taxonomy** (Tier A *LLM on the path* → Tier B *the system acts* → Tier C *the agent persists or collaborates*). Scoped to GenAI/agentic only; ML / SaaS / serverless stay named-but-deferred.

**Why now (SCQA).** *Situation:* the `architect` pack ships a GenAI/agentic lens, and `architect-review`'s WA mode can apply it. *Complication:* the lens reaches the *design* artifact only after the fact — `architect-design`'s by-construction pass (`SKILL.md:45-60`) routes on provider/provider-class (with a leading-edge-novelty fallback) but has **no workload-class axis**, so it never loads the lens; agentic systems are designed against flat pillars and only get the agentic overlay if a reviewer happens to run WA mode; and the lens itself covers only five concerns, missing the human-oversight, bounded-autonomy, and auditability concerns that the major clouds, OWASP, and NIST now treat as baseline for systems that *act*. *Question:* should the agentic overlay be built in at design time as well as review time, and broadened to the current state of the practice?

**Decisions requested:**

1. **Vehicle (D1).** Reverse the frozen spec's review-time-only scoping via a new RFC + new spec (the frozen spec cannot be amended). · *Recommend:* yes · decide-by: this RFC's acceptance · default: as recommended.
2. **Routing (D2).** Add **workload-class as a second, orthogonal routing axis** in `architect-design`'s by-construction step, loading the shared lens when the workload is agentic — mirroring `architect-review`'s existing concern-lens × workload-class split. · *Recommend:* yes · decide-by: acceptance.
3. **Taxonomy (D3).** Expand the overlay to a **progressive, capability-tiered** concern set (A→B→C), each concern grounded in ≥2 independent sources, keeping the pack's "reason about boundaries, name frameworks never; apply what bites" altitude. · *Recommend:* yes · decide-by: acceptance.
4. **Graduated-autonomy framing (D4).** Include graduated autonomy ("start with oversight, widen as track record accumulates") as an **engineering-judgment** principle, *not* a standards mandate — no source formalises threshold-gated checkpoint removal, and Anthropic's autonomy research argues against prescriptive per-action thresholds. · *Recommend:* yes · decide-by: acceptance.
5. **Scope (D5).** GenAI/agentic only; ML / SaaS / serverless remain named-but-unbacked in the rubric (status quo), explicitly deferred. · *Recommend:* yes · decide-by: acceptance.

## Problem & goals

**Diagnosis.** The agentic overlay exists but is mis-wired and under-scoped:

- **Mis-wired (design-time gap).** `architect-design/SKILL.md:45-60` makes a design "well-architected by construction" by routing on **provider/provider-class** (named cloud → pillars; primitives → capability gaps; local-first → local-dev), plus a leading-edge-novelty fallback for domains no shipped reference fits. There is no **workload-class** axis. The GenAI/agentic lens file is duplicated into the design skill, but **no step in `architect-design`'s procedure references it** — it is a dead copy until a workload-class branch wires it in (the leading-edge fallback can't reach it: agentic *has* a shipped reference, so that branch never fires for it). So an agent system is shaped against generic pillars, and the agentic concerns enter (if at all) only when `architect-review`'s WA mode is run and its findings feed the convergence loop. This was a deliberate scoping decision in the frozen `well-architected-cloud` spec (`spec.md:32-41`, `:219-220`): the workload-class lens axis lives in review, design consumes it second-hand.
- **Under-scoped (content gap).** The shipped lens names five concerns: prompt injection, tool-use authz, data egress, evals/observability, token cost (`spec.md:254-257`). It does not make **human oversight / HITL**, **bounded autonomy / intent verification**, or **auditable action trails** first-class — precisely the concerns that distinguish a system that *acts* from one that only *generates text*, and the ones every surveyed cloud + OWASP + NIST now treat as baseline (see Evidence).

**Goals.**

- The agentic overlay is applied **by construction at design time** *and* **at review time**, from one shared lens file (no divergence between the two).
- The overlay's concern set reflects current practice for agentic systems and is **progressive** — an adopter applies only the tier that matches how agentic their system is, so a plain RAG/chat design isn't burdened with multi-agent coordination concerns.
- The overlay keeps the pack's altitude: name the concern and the question it forces; route control-level verification to `security-reviewer`; name no frameworks; apply what bites.

**Non-goals.**

- **Backing the ML / SaaS / serverless workload-class lenses.** They stay named-but-unbacked in `rubric-well-architected.md`. (Could have been a goal — declined to keep this RFC about the agentic overlay.)
- **A new reviewer agent or a new skill.** This is a routing + content change to existing `architect` skills, not a new primitive. (ADR-0023's "three reviewers" ceiling is not engaged; cited, not reversed.)
- **Cloud-platform agentic *diagram* vocabularies** (Bedrock AgentCore / AI Foundry / Vertex). Those stay in `architect-diagram` as drawing aids; this overlay is provider-agnostic design-quality reasoning.
- **Executable tooling / evals for the overlay.** Prose guidance only, consistent with the rest of the pack.

## Proposal

### D1 — Vehicle

The `well-architected-cloud` spec is **Shipped/frozen** (`spec.md:3`; immutable bodies per `CONVENTIONS.md` § Document lifecycle, Frozen row, `:103`) and no ADR/RFC governs its review-time-only scoping (`plan.md:35`), so there is nothing to mechanically supersede. This RFC **names that scoping explicitly and widens it**, and acceptance spawns a **new spec** under `docs/specs/agentic-well-architected-overlay/` that carries the implementing ACs. The frozen spec stays as the record of what shipped.

### D2 — Routing: workload-class as an orthogonal axis

`architect-review` already models two orthogonal lens axes (`rubric-well-architected.md:11-19`): a **concern-lens** and a **workload-class lens**. The change adds the *workload-class* axis to `architect-design`'s by-construction step, alongside the existing *provider* routing — the two are orthogonal (an agentic system on AWS gets both the AWS pillars and the agentic overlay). When the concept's workload is agentic (the design names tool-use, autonomous action, or an agent loop), Step 3 loads the shared lens and shapes the concept against the tier(s) that apply. The **same `lens-genai-agentic.md`** is the single source consumed by both skills (the pack's deliberate per-skill duplication of shared references is preserved — each skill stands alone, per the pack README).

### D3 — Progressive, capability-tiered taxonomy

The overlay is reorganised so concerns are grouped by the **capability that triggers them**. An adopter applies Tier A always, Tier B once the system can act, Tier C once it persists state or runs multiple agents. The trust triad (HITL / intent verification / auditable action trails) lives in Tier B.

- **Tier A — the LLM is on the path** (any generative system, including plain RAG/chat):
  - *Prompt injection / instruction-vs-data trust boundary* — treat model **input** as untrusted (OWASP LLM01).
  - *Data egress & disclosure boundary* — bidirectional: what internal/sensitive data crosses *to* the model (intended, minimised, contractually allowed), **and** what can be extracted *from* the system via crafted input — system-prompt/tool-schema extraction, cross-tenant context bleed (shapes whether secrets belong in the prompt at all) (OWASP LLM02 / LLM07).
  - *Evaluation* — quality measured by an eval set, not vibes; LLM-as-judge for subjective dimensions, deterministic checks where exact; corroborate to resist judge-gaming.
  - *Token cost* — cost per request at p50/p99; the multi-turn history term, not just the system prompt, dominates.
  - *Observability* — prompts, tool calls, and responses traceable enough to debug a bad turn (content off by default for sensitivity).
- **Tier B — the system acts** (tool-using / autonomous agent):
  - *Tool-use authorization & bounded autonomy* — tools scoped to least privilege; destructive/spending tools gated; **intent verification** — surface the planned action chain before irreversible/outbound actions; prefer reversible actions; confused-deputy framing (OWASP LLM06 "excessive agency").
  - *Output handling* — model **output** is untrusted input to the next sink: where is it validated before it drives a tool call, shell, query, or follow-on action? (the outbound twin of the Tier-A input boundary — an agent can pass every authz/HITL/audit check and still wire raw output into an action) (OWASP LLM05).
  - *Execution isolation & blast radius* — for tools that run code or process untrusted content (code interpreters, self-hosted runtimes), the sandbox/isolation posture, distinct from authorization: authz answers "may the agent call this"; isolation answers "what's the blast radius if a prompt-injected call reaches it" (sharpest for the self-hosted agents the lens explicitly targets).
  - *Human oversight & graduated autonomy* — HITL at decision boundaries proportional to risk and reversibility; an example posture is autonomous-for-low-risk / notify-for-medium / approve-for-high (a shape to reason from, **not** a mandated matrix); resist consent/decision fatigue.
  - *Auditability & attributable action trails* — a tamper-evident, attributable record of agent actions and an oversight surface over it; reconstruct what happened during any execution.
  - *Reliability under non-determinism* — explicit max-iteration / loop caps enforced outside the model; idempotent tool calls; graceful degradation; bound runaway/prompt-injected consumption (OWASP LLM10).
- **Tier C — the agent persists or collaborates** (stateful / multi-agent):
  - *Memory & context integrity* — persistent cross-session state's integrity, privacy, and poisoning surface.
  - *Tool / sub-agent provenance* — a design-time question (not a runtime scan): where do tools, MCP servers, and sub-agents come from, and is the source trusted? (OWASP Agentic supply-chain).
  - *Multi-agent coordination, inter-agent trust & identity propagation* — orchestration/handoff, the inter-agent trust boundary, how **identity and privilege propagate across a delegation chain** (A→B: does B act with A's authority or its own — the confused-deputy framing extended past a single agent), and the read-heavy-vs-write-heavy judgement on whether multi-agent helps at all.

Tier-A/B/C security-boundary concerns (injection, egress/disclosure, tool authz, output handling, execution isolation, inter-agent comms, identity propagation, provenance, memory poisoning) name the boundary at design altitude and **route control-level verification to `security-reviewer` / `security-checklists` (`llm-agent` module)**, exactly as the shipped lens does. The implementing spec should make **coverage parity** between this concern set and the `llm-agent` control module an explicit acceptance criterion, so the two surfaces don't diverge as OWASP moves.

### D4 — Graduated-autonomy framing

Graduated autonomy is included as **engineering judgment**: begin a first deployment with oversight at decision boundaries and widen autonomy as a measured track record accumulates. The overlay will *not* assert that a standard prescribes threshold-gated checkpoint removal — none does, and Anthropic's own autonomy research argues against prescriptive per-action thresholds (see Evidence). The concern names the *question* (what is the oversight posture, and what evidence would justify widening it?), not a formula — and it carries the explicit caveat that **irreversibility and blast radius cap how far autonomy widens regardless of track record**: track record justifies widening on reversible actions, not on the irreversible/outbound/spending actions Tier B already says to gate (where failures are rare-but-catastrophic and a clean record is least informative).

### D5 — Scope

GenAI/agentic only. `rubric-well-architected.md:17` continues to name ML / SaaS / serverless without backing files; this RFC neither backs nor removes them. The implementing spec notes them as a known, deferred gap.

## Options considered

**Axis: *where the agentic overlay is applied in the design/review lifecycle*** — the table is the cross-product of {design-time construction · review-time critique · both} × {status-quo content · expanded content}. Do-nothing is the {review-only × status-quo} cell; the recommended option is {both × expanded}. Option 2 (design-time-only) is listed without its content variant for brevity, since the lifecycle position is what disqualifies it.

| Option | What it does | Trade-off vs. goals |
| --- | --- | --- |
| **0. Do-nothing** | Keep the lens review-only, five concerns. | Agentic systems keep getting designed against flat pillars; the trust/oversight/audit gap persists; the lens stays behind the state of practice. Cost of delay: every agentic design shaped in the pack misses the overlay unless a reviewer manually invokes WA mode. |
| **1. Review-time only, expand content** | Broaden the taxonomy but leave it consumed only via `architect-review`→convergence. | Fixes the content gap, not the wiring gap. Design still shapes against generic pillars first; overlay arrives as rework. Half the ask. |
| **2. Design-time only** | Load the overlay by construction, drop the review-side lens. | Loses the independent fresh-context critique (RFC-0032's whole point); a design marks its own homework. Regresses review. |
| **★ 3. Both, one shared lens (recommended)** | Workload-class axis in design *and* review WA mode, same file, progressive taxonomy. | Built-in at design, re-checked at review, no divergence. Matches the strongest prior art (AWS Agentic Lens is explicitly "use when designing… or reviewing"). Cost: a routing-line change in design + a spec; the frozen-spec scope reversal must be named. |
| **4. New standalone "agentic-design" skill** | Carve agentic design into its own skill. | Violates the pack's three-peer-skill shape and the "don't add a primitive when a routing branch suffices" discipline; duplicates `architect-design`'s framing. Over-built. |

Prior-art grounding: Option 3's "one lens, design + review" shape is exactly the AWS Well-Architected **Agentic AI Lens** ("Use this lens when: *Designing* a new agentic AI system… *or* *Reviewing* an existing agentic AI deployment"). Azure structures the same content as AI-workload *design areas* (design-time) plus a testing/evaluation gate (review-time). No surveyed framework attaches agentic guidance to review *only* — Option 1/Do-nothing is the outlier, and it's the status quo.

**A second axis — *taxonomy shape*** — flat list vs. capability-tiered vs. pillar-keyed. Chosen: **capability-tiered** (Tier A→B→C), because both AWS (GenAI Lens → Agentic Lens) and Azure ("retrieval → task-based → autonomous" complexity) escalate guidance by what the system can do; a flat list would force plain-RAG designs to wade through multi-agent concerns, and a pure pillar-keyed list buries the act-vs-generate distinction the overlay exists to draw.

## Risks & what would make this wrong

**Pre-mortem.**

- *Overlay becomes a recite-the-whole-list checklist.* Mitigation: keep the shipped lens's "apply the concerns that bite for THIS system" instruction and the per-tier gating; the tiers are a filter, not a worklist.
- *Design-time routing over-fires*, tagging every LLM feature "agentic" and dragging Tier B/C into plain RAG. Mitigation: the trigger is the system *acting* (tool-use / autonomous loop), and Tier A is explicitly the non-acting baseline.
- *Skill bloat.* Mitigation: the expansion lives in the on-demand reference file (progressive disclosure); `architect-design/SKILL.md` gains one routing branch, not the taxonomy.
- *Security framing drifts into control-level prescriptions* the pack shouldn't own. Mitigation: preserve the route-to-`security-reviewer` boundary; the overlay reasons at design altitude only.

**Key assumptions (falsifiable).**

- *Leading practice treats agentic as a first-class workload-class lens used at both design and review time.* Falsifiable by showing the major frameworks attach agentic guidance to only one phase. **Checked — holds** (AWS Agentic Lens, verified; see Evidence).
- *A capability-tiered grouping is the right cut.* Falsifiable if adopters can't tell which tier they're in — i.e. if "the system acts" is ambiguous in practice.
- *The trust triad is genuinely absent today, not just differently worded.* Falsifiable by finding HITL/intent-verification/audit already first-class in the shipped lens (they are not — `lens-genai-agentic.md` mentions tool "confirmation" once and observability-for-debug, nothing on oversight posture or attributable trails).

**Drawbacks.** A frozen-spec scope decision is being reversed, which costs a new spec and a clear "we changed our mind, here's why" in governance. The overlay grows from five concerns to a materially larger, tier-gated set — more surface to maintain as the practice moves (OTel GenAI conventions and the agentic-security standards are still settling). And design-time routing adds a judgement call ("is this agentic?") the author must make early, when the concept is least settled.

## Evidence & prior art

**Spike / de-risk result.** The riskiest assumption — that leading standards treat agentic as a first-class workload-class lens applied at *both* design and review time — was checked by fetching the **AWS Well-Architected Agentic AI Lens** (published 2026-06-10). Confirmed: it is a workload-class lens organised on the six WA pillars, explicitly scoped to *"Designing a new agentic AI system… or Reviewing an existing agentic AI deployment,"* and it makes bounded autonomy, tiered human oversight, and transparency/auditability first-class responsible-AI principles (AGENTSEC04 guardrails+HITL; AGENTOPS05 tracing/observability). Both the workload-class framing and the dual design+review consumption are externally validated. The assumption holds. ([AWS Agentic AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentic-ai-lens.html))

**Repo precedent.**

- `docs/specs/well-architected-cloud/spec.md:254-257` — the shipped 5-concern lens (the content being expanded); `:32-41`, `:219-220` — the review-time-only scoping (being widened); `plan.md:35` — no ADR/RFC governs it.
- `packs/architect/.apm/skills/architect-design/SKILL.md:45-60` — provider/provider-class by-construction routing with no workload-class axis (the line gaining a workload-class branch).
- `packs/architect/.apm/skills/architect-review/references/rubric-well-architected.md:11-19` — the orthogonal concern × workload-class axes design has not adopted; `:17` — ML/SaaS/serverless named, only GenAI/agentic backed.
- ADR-0023 + RFC-0032 — "three reviewers" ceiling scopes core *code-review* lenses; a design-time workload-class lens (a skill behaviour, not a reviewer) doesn't engage it. Cited, not reversed.
- RFC-0029 — the `security-checklists` `llm-agent` module the overlay's Tier-B/C concerns route to.
- RFC-0041 — precedent for a progressive-disclosure concern-library consumed by a pack lens, and for naming an emerging-standard caveat honestly.

**External prior art.** All anchors fetched and confirmed to contain the cited claim.

- [AWS Well-Architected Agentic AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentic-ai-lens.html) (2026-06-10) — workload-class lens, design+review, six pillars, bounded autonomy / tiered HITL / auditability.
- [Azure Well-Architected — AI workload: Responsible AI design area](https://learn.microsoft.com/en-us/azure/well-architected/ai/responsible-ai) — HITL checkpoints, escape hatches, auditability of agent activity, complexity tiers (retrieval → task → autonomous).
- [Google Cloud Architecture Framework — AI/ML perspective (Security)](https://docs.cloud.google.com/architecture/framework/perspectives/ai-ml/security) — HITL evaluation, audit/lineage via Vertex ML Metadata.
- [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/) — LLM06 Excessive Agency, LLM10 Unbounded Consumption (the Tier-B authz and reliability anchors).
- [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/2025/12/09/owasp-genai-security-project-releases-top-10-risks-and-mitigations-for-agentic-ai-security/) (2025-12) — agent behaviour hijacking, tool misuse, identity/privilege abuse, memory poisoning, human-trust manipulation.
- [NIST AI RMF 1.0](https://nvlpubs.nist.gov/nistpubs/ai/nist.ai.100-1.pdf) (Map 3.5 — human oversight processes defined/assessed/documented) + [GenAI Profile (AI 600-1)](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf).
- [Anthropic — Building Effective Agents](https://www.anthropic.com/research/building-effective-agents) — simplicity-first, explicit max-iterations, human checkpoints, prefer-reversible-actions.
- [Anthropic — Measuring Agent Autonomy](https://www.anthropic.com/research/measuring-agent-autonomy) — the **counter-evidence** for D4: prescriptive per-action oversight thresholds create friction without commensurate safety; oversight calibrates with demonstrated reliability rather than a fixed removal threshold.
- [Cognition — Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents) vs. [Anthropic — multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — the Tier-C tension; the read-heavy-vs-write-heavy distinction is the deciding variable (a synthesis of the two, not a verbatim claim of either).
- [OpenTelemetry GenAI observability](https://opentelemetry.io/blog/2026/genai-observability/) — emerging trace conventions for agents; **caveat: still "Development" status**, cite as the converging convention, not a stable standard.

## Open questions

1. **Observability altitude.** Should the overlay name OTel GenAI semantic conventions as the converging instrumentation standard, given they're still "Development" status? *Recommended default:* name them with an explicit maturity caveat (the RFC-0041 pattern), since the pack does reference standards but flags their maturity. · owner: eugenelim · decide-by: implementing-spec authoring.
2. **Should memory-integrity gate independently of multi-agent?** A single stateful agent has persistent memory (and its poisoning surface) but no coordination/identity-propagation concern — so the "stateful" and "multi-agent" triggers for Tier C are not the same trigger. *Recommended default:* split Tier C's gate in two — memory & context integrity fires on *stateful*, while provenance + coordination/identity fire on *multi-agent* — so a single stateful agent picks up only the memory concern. · owner: eugenelim · decide-by: implementing-spec authoring.

## Follow-on artifacts

<!-- Filled in on acceptance. -->

- ADR — record the decision that the agentic overlay is a first-class workload-class lens applied at design *and* review time (the reversal of the frozen spec's review-time-only scoping).
- Spec: `docs/specs/agentic-well-architected-overlay/` — the workload-class routing branch in `architect-design`, the expanded progressive `lens-genai-agentic.md` (both skill copies), and the dogfood ACs; bumps `architect` (current version per `packs/architect/pack.toml`). The spec carries an AC for **coverage parity** between the overlay's concern set and the `security-checklists` `llm-agent` control module, and records the **ML/SaaS/serverless deferral** as a `docs/backlog.md` register entry (with a `(deferred: <anchor>)` AC marker), not RFC-only prose that rots.
- Changelog: `[Unreleased] → Added` entry in the implementing PR.
