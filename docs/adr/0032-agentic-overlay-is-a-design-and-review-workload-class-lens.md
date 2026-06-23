# ADR-0032: The agentic well-architected overlay is a first-class workload-class lens applied at design *and* review — a routing axis plus progressive taxonomy on the existing `architect` skills, not a new primitive

- **Status:** Accepted
- **Date:** 2026-06-23
- **Decision-makers:** eugenelim
- **Consulted:** RFC-0042 (the accepted decision this records, incl. its AWS-Agentic-Lens spike result and the D1–D5 decision set); the spec-stage adversarial + design + security review of this ADR and the implementing spec
- **Supersedes:** none
- **Related:** RFC-0042 (the accepted decision this ADR records); `docs/specs/well-architected-cloud/` (Shipped/frozen — the spec whose review-time-only scoping this widens, and the source of the five-concern lens being expanded); RFC-0032 (the `architect` `design-reviewer` / fresh-context critique whose value the design-time-only alternative would have lost); ADR-0023 (the three-reviewer ceiling scopes the core *code-review* lenses — cited to show a design-time skill lens does not engage it); RFC-0029 (the `security-checklists` `llm-agent` module the overlay's security-boundary concerns route to); RFC-0041 / ADR-0031 (the precedent for a progressive-disclosure concern library consumed by a pack lens, and for naming an emerging-standard's maturity caveat honestly)

## Context

The `architect` pack ships a GenAI/agentic well-architected overlay, and `architect-review`'s well-architected (WA) mode can apply it as a workload-class lens (`rubric-well-architected.md:11-19`). But the overlay is **mis-wired** and **under-scoped**, and both gaps trace to one frozen scoping decision.

- **Mis-wired (design-time gap).** `architect-design` makes a design "well-architected by construction" at its Stage 0 (`SKILL.md:45-60`) by routing on **provider / provider-class** (named cloud → pillars; primitives → capability gaps; local-first → local-dev), plus a leading-edge-novelty fallback for domains no shipped reference fits. There is **no workload-class axis**. The GenAI/agentic lens file is duplicated into the design skill, but no step in the procedure references it — it is a dead copy, and the leading-edge fallback can't reach it (agentic *has* a shipped reference, so that branch never fires). An agentic system is therefore shaped against flat pillars, and the overlay enters — if at all — only when a reviewer happens to run WA mode and its findings feed the convergence loop.
- **Under-scoped (content gap).** The shipped lens names five concerns — prompt injection, tool-use authz, data egress, evals/observability, token cost (`spec.md:254-257`). It does not make **human oversight / HITL**, **bounded autonomy / intent verification**, or **auditable, attributable action trails** first-class — precisely the concerns that distinguish a system that *acts* from one that only *generates text*, and the ones the major clouds, OWASP, and NIST now treat as baseline.

Both gaps follow from the `well-architected-cloud` spec's deliberate decision that the workload-class lens axis lives in *review*, with design consuming it second-hand (`spec.md:32-41`, `:219-220`). That spec is **Shipped/frozen** — its body is immutable (`CONVENTIONS.md` § Document lifecycle, Frozen row) — and **no ADR or RFC governs the review-time-only scoping** (`plan.md:35`), so there is nothing to mechanically supersede: the scoping must be *named explicitly and widened* by a new decision.

Constraints in force when deciding:

- **CHARTER Principle 3 (a habit, not infrastructure).** The repo ships doctrine and prose the agent reasons from, never a runtime engine or executable tooling. This forecloses shipping evals or an executable overlay.
- **CHARTER Principle 2 (no duplication).** A capability belongs in exactly one place; a parallel skill that re-implements `architect-design`'s framing is rejected.
- **The pack's "no required composition / per-skill duplication" shape** (`architect/README.md:54-57`, `:153-156`). Each skill stands alone; shared references are duplicated per skill with a duplication note rather than shared by inter-skill reference.
- **The three-reviewer ceiling (ADR-0023).** Core code-review has exactly three lenses — `adversarial-reviewer`, `security-reviewer`, `quality-engineer`. A fourth is out of bounds.
- **The pack's altitude:** reason about boundaries and authority, name frameworks never, apply what bites; route control-level verification to `security-reviewer` / `security-checklists`.

RFC-0042 settled *whether* and *how* to close these gaps (decisions D1–D5, with the riskiest assumption — that leading practice treats agentic as a workload-class lens applied at *both* design and review — confirmed against the AWS Well-Architected Agentic AI Lens). This ADR records the load-bearing, expensive-to-reverse calls — the *lifecycle position*, the *routing form*, the *taxonomy shape*, and the *autonomy framing* — so a future maintainer doesn't re-litigate them. The mechanical detail (the exact routing-branch wording, the Tier A/B/C concern list, the coverage-parity criterion) is spec-level and lives in the implementing spec, not here.

## Decision

> We will treat the GenAI/agentic well-architected overlay as a **first-class workload-class lens consumed by construction at design time *and* at review time, from one logical lens (physically duplicated per the pack's per-skill shape, kept byte-identical)**; expand it into a **progressive, capability-tiered taxonomy** (Tier A *the LLM is on the path* → Tier B *the system acts* → Tier C *the agent persists or collaborates*); and ship it as a **routing branch plus reference-content expansion on the existing `architect` skills** — not as a new reviewer, a new skill, or any executable tooling.

Four sub-decisions, each expensive to reverse:

- **Lifecycle position — design *and* review, one *logical* lens (the reversal).** The overlay is applied by construction when a design is *shaped* (`architect-design` Stage 0) and re-checked when a design is *critiqued* (`architect-review` WA mode), consuming the **same** `lens-genai-agentic.md` — one *logical* lens, physically duplicated per the pack's per-skill shape and kept byte-identical (not a single physical file — which refines RFC-0042's "no divergence" goal into "divergence *caught at review*" once the physical-duplication constraint is admitted). This **names the frozen `well-architected-cloud` spec's review-time-only scoping explicitly and widens it**; the frozen spec stays as the record of what shipped. This is the call the implementing spec (D1's "new spec") carries forward; the frozen body is not edited.
- **Routing form — workload-class as a second, orthogonal axis in design's by-construction step.** `architect-design`'s Stage 0 gains a *workload-class* axis alongside its existing *provider* axis. The two are orthogonal: an agentic system on a named cloud loads both the cloud pillars and the agentic overlay. This mirrors `architect-review`'s already-shipped concern-lens × workload-class split (`rubric-well-architected.md:11-19`) — the design side adopts the model review already has. The trigger is the system *acting* (the design names tool-use, autonomous action, or an agent loop); a non-acting generative design (plain RAG/chat) loads only Tier A.
- **Taxonomy shape — progressive, capability-tiered (A→B→C), not flat and not pillar-keyed.** Concerns are grouped by the capability that triggers them, so an adopter applies only the tier that matches how agentic their system is. The tiers are a **filter, not a worklist** — the shipped lens's "apply the concerns that bite for THIS system" instruction is preserved. Both AWS (GenAI Lens → Agentic Lens) and Azure ("retrieval → task-based → autonomous") escalate guidance by capability; a flat list would burden a plain-RAG design with multi-agent concerns, and a pillar-keyed list would bury the act-vs-generate distinction the overlay exists to draw.
- **Graduated-autonomy framing — engineering judgment, not a standards mandate.** The overlay includes graduated autonomy ("begin with oversight at decision boundaries, widen as a measured track record accumulates") as an engineering-judgment principle. It does **not** assert that any standard prescribes threshold-gated checkpoint removal — none does, and Anthropic's own autonomy research argues against prescriptive per-action thresholds. The framing carries the explicit cap that **irreversibility and blast radius bound how far autonomy widens regardless of track record**: a clean record justifies widening on reversible actions, never on the irreversible / outbound / spending actions Tier B already says to gate. A **partially-reversible or reversible-at-a-cost** action (a rollback-able deploy, a refundable charge) defaults to the *gated* side absent a deliberate per-action judgment to treat it as reversible — the gated-by-default partition is the safe default, not an exhaustive classification.

Boundaries on the decision:

- **No new primitive.** This is a routing-line change plus reference-content expansion on existing `architect` skills — not a new reviewer agent and not a new skill. A standalone "agentic-design" skill is rejected against Principle 2 and the pack's three-peer-skill shape; a fourth reviewer is rejected against ADR-0023. The three-reviewer ceiling is **cited, not engaged** — a design-time workload-class lens is a *skill behaviour*, not a code-review reviewer: ADR-0023 scopes reviewers of a *code diff*, and the overlay shapes a design artifact before any code exists and adds no diff-review pass, so the ceiling's subject is simply absent.
- **Prose only.** No executable tooling, evals, or runtime ships, consistent with Principle 3 and the rest of the pack. The expansion lives in the on-demand reference file (progressive disclosure); `architect-design/SKILL.md` gains one routing branch, not the taxonomy.
- **Security-boundary concerns name the boundary at design altitude and route control-level verification to `security-reviewer` / `security-checklists` (`llm-agent` module)** — exactly as the shipped lens does. The overlay does not own controls. The implementing spec makes **coverage parity** between the overlay's security-boundary concern set and the `llm-agent` module an explicit, **bidirectional** acceptance criterion (every module control is covered by an overlay concern, *and* every overlay security concern resolves to a named module check or an explicit design-altitude-only status). Where the overlay names an agentic boundary the `llm-agent` module does not yet enumerate (execution isolation, inter-agent identity/privilege propagation, memory poisoning), the spec records the module extension as a deferred backlog item rather than letting the route-out land on a missing control — the overlay still names the boundary at design altitude meanwhile, since `security-reviewer` reasons from cross-cutting standards (OWASP/STRIDE/LINDDUN), not the module text alone.
- **Scope is GenAI/agentic only.** ML / SaaS / serverless remain named-but-unbacked in `rubric-well-architected.md` (status quo); this decision neither backs nor removes them. The deferral is recorded in `docs/backlog.md`, not left as RFC-only prose.

## Decision drivers

- **Leading practice treats agentic as a workload-class lens used at *both* design and review** — drives the dual-consumption + workload-class framing. Confirmed against the AWS Well-Architected Agentic AI Lens (a workload-class lens explicitly scoped to "Designing a new agentic AI system… or Reviewing an existing agentic AI deployment," with bounded autonomy, tiered human oversight, and auditability as first-class principles); Azure structures the same content as design areas plus a testing/evaluation gate. No surveyed framework attaches agentic guidance to review only.
- **The design-time gap is real, present pain** — drives the routing branch. The design skill has no workload-class axis and the lens copy is a dead file; agentic systems are shaped against flat pillars today.
- **Principle 2 + the pack's three-peer-skill shape** — rules out a new `agentic-design` skill; a routing branch in the existing skill suffices, and a parallel skill would duplicate `architect-design`'s framing.
- **Principle 3 (habit, not infrastructure)** — rules out evals or executable tooling; the overlay stays prose.
- **The three-reviewer ceiling (ADR-0023)** — rules out a fourth, agentic-lens reviewer; cited to show that a design-time skill lens does not engage it.
- **The pack's "name the boundary, route controls out" altitude** — drives the route-to-`security-reviewer` boundary and the coverage-parity criterion, keeping the overlay from drifting into control-level prescriptions it shouldn't own.
- **Anthropic's autonomy research as counter-evidence** — drives D4's engineering-judgment framing over a prescriptive oversight-threshold matrix.

## Consequences

**Positive:**

- The overlay is **built in at design time and re-checked at review time from one logical lens** — physically two per-skill copies kept byte-identical per the pack's duplication shape, with divergence a maintenance burden *caught at review* rather than prevented by construction — so design and review reason from the same content, matching the strongest prior art (the AWS Agentic Lens's explicit design-or-review scoping).
- The design side **reuses the orthogonal concern × workload-class axis model `architect-review` already ships**, so this is a second consumer of an existing pattern, not a new mechanism.
- **Progressive disclosure keeps the surface small**: `architect-design/SKILL.md` gains one routing branch; the expanded taxonomy lives in the on-demand reference, so a plain-RAG design isn't burdened with Tier B/C concerns and the skill body doesn't bloat.
- The overlay's content moves up to current practice (the trust triad — HITL, intent verification, attributable action trails — becomes first-class) without leaving the pack's design altitude.

**Negative:**

- A **frozen-spec scope decision is reversed**, which costs a new spec and a clear "we changed our mind, here's why" in governance (this ADR + the implementing spec). Recorded deliberately rather than worked around.
- The overlay grows from five concerns to a **materially larger, tier-gated set** — more surface to maintain as the practice moves (the agentic-security standards and OTel GenAI conventions are still settling).
- **Design-time routing adds an "is this agentic?" judgment call early**, when the concept is least settled. Mitigated: the trigger is the system *acting*, and Tier A is the explicit non-acting baseline, so over-firing drags in at most Tier A.

**Neutral / to revisit:**

- **OTel GenAI semantic conventions are "Development" status.** The overlay may name them as the converging instrumentation standard *with an explicit maturity caveat* (the RFC-0041 pattern) — revisit and drop the caveat when they stabilise. (RFC-0042 open question 1, resolved to this default.)
- **Tier C's gate is split** — memory & context integrity fires on *stateful*, while sub-agent provenance + multi-agent coordination/identity-propagation fire on *multi-agent* (tool/MCP *source* provenance moves up to Tier B, where any externally-sourced tool/MCP load is the LLM03 supply-chain trust question) — so a single stateful agent picks up only the memory concern. This is the sharpest instance of RFC-0042's falsifiable assumption that the capability-tiered grouping is the right cut (adopters can tell which tier they're in); if the Tier-C split proves ambiguous in practice, that assumption — and the taxonomy-shape sub-decision — is what fails. Revisit then. (RFC-0042 open question 2, resolved to this default.)
- **ML / SaaS / serverless stay deferred**, named-but-unbacked. A future RFC that backs any of them reopens this scope.

## Confirmation

- The implementing spec's acceptance criteria encode the decision — the workload-class routing branch in `architect-design` Stage 0, the expanded progressive Tier A/B/C `lens-genai-agentic.md` in **both** skill copies, the trust triad and graduated-autonomy framing, the Tier-C gate split, the coverage-parity criterion against the `llm-agent` module, and the dogfood run — so conformance is checkable against the spec.
- The spec-stage and diff review passes (adversarial + design + security) confirm that **no new primitive creeps in** (the standing scope-inflation risk), that the overlay **stays prose at design altitude** with no control-level prescriptions, that the **route-to-`security-reviewer` boundary holds**, and that the **two lens copies stay identical** (the pack's per-skill duplication, not divergence).
- **Enforcement is deliberately review-time, not a standing CI gate.** Conformance is confirmed at the implementing PR (the spec's ACs) and thereafter by the three reviewer passes' standing doctrine; there is no machine fitness function asserting "the overlay ships no executable tooling" or "the two copies match" against future drift. This matches Principle 3 (the bar that forecloses a code gate is the same one that keeps the overlay prose) and ADR-0030/0031's precedent of accepting a prose-enforced, reviewer-held residual. A later optional governance lint (e.g. asserting the two lens copies are byte-identical modulo the duplication note) could harden it without reversing this ADR, and is recorded as a possible follow-up, not a requirement.

## Alternatives considered

- **Do nothing — keep the lens review-only and at five concerns.** Rejected against the **design-time-gap** driver: agentic systems keep being shaped against flat pillars, and the trust/oversight/audit gap persists. This is the status-quo cell, and it is the outlier against all surveyed prior art.
- **Review-time only, expand content.** Rejected as half the ask — it fixes the content gap but not the wiring gap; design still shapes against generic pillars first and the overlay arrives as rework.
- **Design-time only — load the overlay by construction, drop the review-side lens.** Rejected against **RFC-0032's fresh-context-critique value**: a design would mark its own homework, regressing the independent review pass.
- **A new standalone "agentic-design" skill.** Rejected against **Principle 2 and the pack's three-peer-skill shape** — a parallel skill re-implements `architect-design`'s framing; a routing branch suffices.
- **A fourth, agentic-lens reviewer.** Rejected against **the three-reviewer ceiling (ADR-0023)** — the design-time lens is a skill behaviour, not a code-review reviewer.
- **A flat or pillar-keyed taxonomy** instead of capability-tiered. Rejected against the **prior-art escalate-by-capability pattern**: a flat list burdens plain-RAG designs with multi-agent concerns, and a pillar-keyed list buries the act-vs-generate distinction.
- **Graduated autonomy as a prescribed oversight-threshold matrix.** Rejected against **Anthropic's autonomy research** (per-action thresholds create friction without commensurate safety) and the absence of any standard formalising threshold-gated checkpoint removal — hence the engineering-judgment framing with the irreversibility/blast-radius cap.

## References

- RFC-0042 — Agentic well-architected overlay as a first-class workload-class lens (the accepted decision this ADR records; decisions D1–D5, the AWS-Agentic-Lens spike, and the evidence base).
- `docs/specs/well-architected-cloud/` — the Shipped/frozen spec whose review-time-only scoping is widened and whose five-concern lens is expanded.
- RFC-0032 — the `architect` `design-reviewer` / fresh-context critique (the value the design-time-only alternative would lose).
- ADR-0023 — the three-reviewer ceiling scopes the core code-review lenses (cited; not engaged by a design-time skill lens).
- RFC-0029 — the `security-checklists` `llm-agent` module the overlay's security-boundary concerns route to.
- RFC-0041 / ADR-0031 — precedent for a progressive-disclosure concern library consumed by a pack lens, and for honestly caveating an emerging standard's maturity.
- [AWS Well-Architected Agentic AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentic-ai-lens.html) — the prior art confirming the workload-class, design-and-review framing.
- CHARTER Principles 2 and 3 — the no-duplication and habit-not-infrastructure bars this decision clears.
