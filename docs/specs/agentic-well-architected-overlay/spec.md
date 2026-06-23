# Spec: agentic-well-architected-overlay

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0032, RFC-0042 (D1–D5 + open-question defaults OQ1/OQ2); RFC-0029 (the `security-checklists` `llm-agent` module the security-boundary concerns route to — the coverage-parity target); the Shipped/frozen `well-architected-cloud` spec (the review-time-only scoping this widens and the five-concern lens this expands)
- **Contract:** none <!-- pure-markdown skill content; no API/event/RPC surface -->
- **Shape:** n/a — skill prose + reference-content authoring across two `architect` skills; no application LLD

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A solution architect using the `architect` pack designs an agentic system — one that uses tools, takes autonomous action, or runs an agent loop — and gets the GenAI/agentic well-architected overlay **applied by construction at design time**, not only if a reviewer later runs well-architected (WA) mode. The overlay reflects current practice for systems that *act*: alongside the shipped prompt-injection / tool-authz / data-egress / evals / cost concerns, it makes human oversight, bounded autonomy with intent verification, and auditable action trails first-class. It is **progressive** — a plain RAG/chat design applies only the baseline tier; a multi-agent system with outbound spend authority applies all three — so an adopter is never made to recite concerns that don't bite for their system. Design time and review time consume **one shared lens file**, so the two never diverge, and the overlay keeps the pack's altitude: name the boundary and the question it forces, name no frameworks, route control-level verification to `security-reviewer` / `security-checklists`.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Keep the overlay **prose at design altitude** — name the concern and the question it forces; route control-level verification to `security-reviewer` / `security-checklists` (`llm-agent` module).
- Expand **both** copies of `lens-genai-agentic.md` (`architect-design` and `architect-review`) identically, each keeping its one-line duplication note (the pack's per-skill duplication is the principle, not a bug).
- Keep the per-tier gating a **filter, not a worklist** — preserve the shipped lens's "apply the concerns that bite for THIS system" instruction.
- Bump the `architect` pack version (`pack.toml` + `plugin.json`) and refresh its projection, since this changes a user-facing capability.

### Ask first

- Any change to `architect-review`'s WA-mode rubric (`rubric-well-architected.md`) beyond keeping its GenAI/agentic route pointed at the shared lens — the review side's lens-selection model is already shipped and out of scope to redesign.
- Backing any of ML / SaaS / serverless (they are explicitly deferred — see AC and the backlog register).

### Never do

- Ship a new reviewer agent, a new skill, or any executable tooling / evals for the overlay (Principle 3; ADR-0023 ceiling; ADR-0032).
- Inline the Tier A/B/C concern list into `architect-design/SKILL.md` — the routing branch loads the reference; the taxonomy lives in the reference (progressive disclosure).
- Edit the frozen `well-architected-cloud` spec body or the frozen RFC-0042 body.
- Assert that any standard prescribes threshold-gated checkpoint removal — graduated autonomy is engineering judgment, not a standards mandate.

## Testing Strategy

This is a skill-prose / reference-content change; verification is **goal-based** and **manual QA**, with no TDD-mode logic:

- **Routing branch wiring, lens structure, both-copies-identical, coverage parity, pack-version bump, rubric-route-preserved** — *goal-based*: a `grep` / `diff` / build one-liner verifies each outcome. (Several are cross-cutting checks that span the touched files — see `plan.md` Construction tests.)
- **The overlay fires and gates as intended on a real agentic concept** — *manual QA, exercised end-to-end*: run `architect-design` on an agentic concept and on a plain-RAG concept and record what the skill actually loads and produces (the workload-class branch fires for the agentic one and loads the tier(s) that apply; the RAG one stays Tier A). A passing grep alone does not satisfy this — the built artifact (the skill, run as a user would) must produce the right behaviour.

## Acceptance Criteria

- [ ] **Workload-class routing axis exists.** `architect-design`'s Stage 0 (the "well-architected by construction" step, `SKILL.md:45-60`) gains a **workload-class** axis alongside its existing **provider** axis. When the concept's workload is agentic — the design names tool-use, autonomous action, or an agent loop — the step loads `references/lens-genai-agentic.md` and shapes the concept against the tier(s) that apply.
- [ ] **The two axes are orthogonal.** An agentic system on a named cloud loads **both** the cloud pillars (`well-architected-pillars.md`) and the agentic overlay; routing is additive, not either/or. A non-acting generative design (plain RAG/chat) loads only Tier A.
- [ ] **The routing branch is the only `SKILL.md` addition.** The Tier A/B/C concern list is **not** inlined into `architect-design/SKILL.md`; the branch loads the reference file (progressive disclosure).
- [ ] **The shared lens is reorganised into a progressive, capability-tiered taxonomy** — Tier A *the LLM is on the path* → Tier B *the system acts* → Tier C *the agent persists or collaborates* — with explicit per-tier gating instructions (apply Tier A always; Tier B once the system can act; Tier C once it persists state or runs multiple agents).
- [ ] **Tier A** carries: prompt injection / instruction-vs-data trust boundary; data egress & disclosure boundary (bidirectional — what crosses *to* the model and what can be extracted *from* the system); evaluation (eval set, LLM-as-judge + deterministic, corroborate); token cost (p50/p99, multi-turn-history term — the **LLM10** Unbounded-Consumption / denial-of-wallet anchor, paired with the Tier-B loop-cap concern); observability (prompts/tool-calls/responses traceable, content off by default).
- [ ] **Tier B** carries: tool-use authorization & bounded autonomy — least privilege, gated destructive/spending tools, **intent verification** (surface the planned action chain before irreversible/outbound actions, prefer reversible actions, confused-deputy framing); the bullet **forces the explicit design-time question** *what is the tool allowlist, and which actions require confirmation?* (an "the agent can take actions" design with no allowlist or confirmation criteria is the named design-time miss). Also: **tool / MCP source provenance** (where do the tools and MCP servers this agent loads come from, and is the source trusted? — the LLM03 supply-chain trust question, firing for any externally-sourced tool/MCP load, single-agent included); **output handling** (model output is untrusted input to the next sink — validated before it drives a tool/shell/query/follow-on action); **execution isolation & blast radius** (sandbox posture for code-running/untrusted-content tools, distinct from authorization); **human oversight & graduated autonomy**; **auditability & attributable action trails**; reliability under non-determinism (max-iteration/loop caps enforced outside the model, idempotent calls, graceful degradation — the runaway-loop half of the **LLM10** Unbounded-Consumption anchor).
- [ ] **Tier C** carries: memory & context integrity; **sub-agent** provenance (a design-time trust question for delegated agents — it shares the **LLM03** supply-chain route with Tier-B tool/MCP provenance, as the multi-agent-gated facet of the same control, not a distinct module check); multi-agent coordination, inter-agent trust & **identity/privilege propagation across a delegation chain**.
- [ ] **The trust triad is first-class in Tier B** — human oversight & HITL, intent verification, and auditable/attributable action trails each appear as a named concern with the question it forces, not folded into the existing tool-authz or observability bullets.
- [ ] **Graduated autonomy is framed as engineering judgment, not a standards mandate.** The lens names the *question* (what is the oversight posture, and what evidence would justify widening it?) and carries the explicit cap that **irreversibility and blast radius bound how far autonomy widens regardless of track record**. It does not assert that any standard prescribes threshold-gated checkpoint removal.
- [ ] **Tier C's gate is split** — memory & context integrity fires on *stateful*; **sub-agent** provenance + multi-agent coordination/identity-propagation fire on *multi-agent*; **tool/MCP source provenance fires on Tier B** (any system that loads external tools, single-agent included — aligning the design-time gate with the `llm-agent` LLM03 trigger) — so a single stateful agent picks up only the memory concern (RFC-0042 OQ2 default, refined so single-agent tool-supply-chain trust isn't gated out).
- [ ] **Observability names OTel GenAI semantic conventions as the converging instrumentation standard with an explicit maturity caveat** (they are "Development" status) — the RFC-0041 honest-caveat pattern (RFC-0042 OQ1 default).
- [ ] **Coverage parity with the `llm-agent` control module is bidirectional.** Every Tier A/B/C **security-boundary** concern (prompt injection, data egress/disclosure, tool-use authz, output handling, execution isolation, inter-agent comms, identity/privilege propagation, tool/MCP + sub-agent provenance, memory poisoning) names the boundary at design altitude and routes control-level verification to `security-reviewer` / `security-checklists` (`llm-agent`). The mapping is checked **both ways**: (a) every `llm-agent` control item (LLM01/02/03/05/06/10 + the spec-stage proactive control) is covered by an overlay concern, **and** (b) every overlay security-boundary concern resolves to a named `llm-agent` check **or** to an explicit *design-altitude-only* status — so the route-out never silently points at a missing control.
- [ ] **The overlay's net-new agentic boundaries are reconciled with the module.** Execution isolation & blast radius, inter-agent identity/privilege propagation, and memory poisoning exceed the current `llm-agent` module's surface (it stops at LLM01/02/03/05/06/10, with no Agentic-Top-10 content). Each is named at design altitude in the overlay; the corresponding `llm-agent` module extension (Agentic Top 10: tool misuse, identity/privilege abuse, memory poisoning) is recorded as a deferred backlog entry, so the route-out has a tracked destination rather than landing on a missing control. (deferred: llm-agent-module-agentic-boundary-extension)
- [ ] **OWASP anchors cover the poisoning & retrieval surface.** The overlay's memory & context integrity / poisoning concern (Tier C) carries the **LLM04** (Data & Model Poisoning) anchor, and its retrieved-content / embedding surface (Tier A injection + egress) carries the **LLM08** (Vector & Embedding Weaknesses) anchor — both omitted from RFC-0042's OWASP mapping (the frozen RFC can't be edited; this spec is the corrected record).
- [ ] **Both lens copies are identical** (modulo the per-skill duplication note): `architect-design/references/lens-genai-agentic.md` and `architect-review/references/lens-genai-agentic.md` carry the same expanded taxonomy, each retaining its duplication note.
- [ ] **`architect-review` WA mode still routes GenAI/agentic to the shared lens** — `rubric-well-architected.md`'s workload-class lens selection continues to load `lens-genai-agentic.md` with no regression to its concern-lens × workload-class axes.
- [ ] **The overlay keeps the pack's altitude** — names the concern + the question it forces, names no frameworks, and preserves the apply-what-bites instruction; the tiers filter, they do not become a recite-the-whole-list checklist.
- [ ] **The `architect` pack version is bumped** (`pack.toml` `[pack].version` + `plugin.json`) and its projection refreshed, per the user-facing-capability-change rule.
- [ ] **A `[Unreleased] → Added` changelog entry** is added in the implementing PR (`docs/product/changelog.md`).
- [ ] **The overlay is dogfooded end-to-end** — `architect-design` run on a real agentic concept loads the workload-class branch and gates the tiers as intended, and on a plain-RAG concept loads only Tier A; the observed behaviour is recorded (manual QA).
- [ ] **ML / SaaS / serverless remain named-but-unbacked** in `rubric-well-architected.md`; the deferral is recorded in the backlog register, not RFC-only prose. (deferred: ml-saas-serverless-workload-class-lenses)

## Assumptions

- Technical: `architect-design` Stage 0 routes on provider/provider-class today with no workload-class axis, and the duplicated `lens-genai-agentic.md` is a dead copy in that skill (no procedure step references it) (source: `packs/architect/.apm/skills/architect-design/SKILL.md:45-60`, probe 2026-06-23).
- Technical: `architect-review`'s WA mode already models the orthogonal concern-lens × workload-class axes and loads `lens-genai-agentic.md` for the GenAI/agentic class (source: `rubric-well-architected.md:11-19`, probe 2026-06-23).
- Technical: the shared lens ships at five concerns and routes its security-boundary concerns to `security-checklists` `llm-agent` today (source: `lens-genai-agentic.md`, probe 2026-06-23).
- Process: the implementation of the skill edits lands in a **separate** PR; this spec + ADR-0032 + the plan are the governance deliverable, and the spec stays `Draft` until that implementing PR flips it (source: RFC-0042 § Follow-on artifacts; repo pattern, RFC-0041 follow-on #363).
- Process: a frozen spec cannot be amended, so the review-time-only scoping is widened by ADR-0032 + this new spec rather than by editing `well-architected-cloud` (source: `CONVENTIONS.md` § Document lifecycle, Frozen row; RFC-0042 D1).
- Product: the two RFC open questions are settled to their RFC-recommended defaults — OTel named with a maturity caveat (OQ1), Tier C's gate split into stateful-vs-multi-agent (OQ2) (source: RFC-0042 § Open questions, decide-by "implementing-spec authoring").
