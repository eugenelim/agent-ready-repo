# Human judgment: decomposition, equipping, and the phase walkthrough

The capstone. Decomposes every place human judgment enters the vision→ship flow,
maps each to a mechanism that equips an agent, and walks the phases.

## The unifying insight

**"Human judgment" is mostly missing-referent labor wrapped around a small
irreducible core.** Kahneman's condition for valid expert intuition is *a regular
environment with reliable feedback* — i.e. an external referent. Where a referent
exists (the world, a standard, a simulated consequence, a precedent), the judgment
is substitutable: the agent does it AGAINST the referent and records it. Where no
referent can exist — originating what we *want* (value), and *accepting*
irreversible risk (accountability) — it is irreducible and stays with the human.

So the equipping strategy is two moves: (1) **supply the referent** for each
substitutable judgment type; (2) **compress the irreducible core** into the fastest
elicit → offer-grounded-options → ratify interaction.

## Decomposition of judgment types

| # | Judgment type | Question it answers | Where it appears | Equipping mechanism | Repo primitive | Residue → surface when |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | **Empirical / factual** | what is true about the domain/tech? | domain grounding; API/contract shape | **research + retrieval** (referent = the world) | research pack ✓, contract-acquisition ✓ | sources conflict or absent |
| 2 | **Normative / standards** | what's the correct way per established practice? | a11y, security controls, API conventions, UI heuristics | **behavior guides / checklists** (referent = codified standard) | security-checklists ✓, operational-safety ✓, experience quality floor ✓, CONVENTIONS ✓, WCAG/W3C/OWASP refs | standards conflict / silent on the case |
| 3 | **Predictive / consequence** | what happens if X? what could go wrong? | blast radius, failure modes, scenario-thinking | **simulation** — pre-mortem, trace, ACH, fresh-context adversarial (referent = simulated future + failure taxonomy) | de-risk-intent ✓, devils-advocate ✓, adversarial-reviewer ✓, self-coverage gate ✦ | genuinely novel / black-swan |
| 4 | **Aesthetic / taste** | does it look/feel right? | visual direction, UX feel | **grounded referent** — persona + precedent + standards (Kahneman: valid only with a stable referent) | aesthetic-direction ⊕, design-critique ⊕ | no precedent; brand seed missing |
| 5 | **Trade-off / prioritization** | given limits, what matters more? | MVP scope, appetite, what to cut | **objective function + decision matrix** (referent = stated outcomes/metrics) | frame-intent outcomes ✓ + appetite ✓ + ranking step | objective ambiguous / weights unset |
| 6 | **Value / strategic intent** | what do WE want? what's the bet? | the vision; brand; "this product not that" | **elicit + offer grounded options + execute faithfully** — cannot originate | frame-intent intake ✓, AskUserQuestion, offer-options ✦ | always (irreducible — origination of ends) |
| 7 | **Risk-acceptance / accountability** | do we accept this irreversible risk? ship? | one-way doors: spend, legal, security sign-off, deploy | **package the decision for fast ratification** — accountability is non-transferable | decision brief ✦, reversibility triage (de-risk) ✓ | always at one-way doors |

**Spectrum:** types 1–4 are substitutable (agent does them against a referent);
type 5 is substitutable once the objective is set; types 6–7 are irreducible
(origination of preference; acceptance of accountability) — but even these the
agent reduces to elicit/offer/ratify.

## Refined surfacing predicate (unifies gates with judgment types)

Surface to the human iff: **(a)** the judgment is type 6 or 7 (irreducible), OR
**(b)** a substitutable judgment's referent FAILED (the residue column). Everything
else the agent determines against its referent and records. This is the single rule
behind every gate.

Cynefin check the agent runs to pick the referent: clear → apply best-practice
(type 2 guide); complicated → analyze/research (type 1); complex → probe/simulate
(type 3); the value/irreversible cells (6/7) always route to the human.

## Phase-by-phase

Each phase: dominant judgments → how the agent is equipped → what surfaces (and
which type forces it) → artifacts. The self-coverage gate runs before any
"converged" claim; the predicate decides every human touch.

**Phase 0 — Intake (gate G0).** Dominant: type 6 (value). Agent elicits vision /
scale / appetite / brand seed via structured interview, reflects back its reading,
offers grounded interpretations. *Surfaces:* the value seed (irreducible) — human
confirms. *Artifacts:* product-vision intent.

**Phase 1 — Discovery & domain grounding (gates G1, G1.5).** Dominant: types 1
(empirical), 2 (normative), 5 (trade-off). Agent researches how the real activity
works + best practice + naive-failure modes (Domain Framing), de-risks the riskiest
assumption, bounds MVP against the stated appetite, builds the persona.
*Surfaces:* the MVP cut (type 5, value-laden) + assumptions research couldn't
ground (type 1 referent-failure) — human ratifies the scope line. *Artifacts:*
Domain Framing + Scope Boundary (the MVP out-of-scope register), persona, intent/OST, assumption test.

**Phase 2 — Convergence design (the blackboard loop → gate G2).** Dominant: types
3 (predictive), 4 (aesthetic), 2 (normative), 5 (trade-off). Agent runs the
product/UX/tech lenses in one context, simulates (pre-mortem/trace), pressure-tests
taste against the grounded reference, checks standards (security/quality/a11y as
live lenses), reconciles via the open-questions queue, runs the self-coverage gate.
*Surfaces at G2:* the decision brief for ratification (type 7 — about to spend
build tokens), any irreducible tension, residual taste-seed forks (type 6).
*Artifacts:* journey map, service blueprint, screen inventory, grounded aesthetic
direction, design critiques, architecture sketch + contracts, coverage record.

**Phase 3 — Specification (gate G3).** Dominant: types 2 + 3. Agent turns each
brief into a spec; security + adversarial review at spec stage (standards +
simulation). *Surfaces:* only on a risk trigger (security boundary, new dependency,
structural). *Artifacts:* briefs, specs.

**Phase 4 — Build (gate G4).** This is the verifiable regime — agent runs hardest.
work-loop + supervisor-mode fan-out + the three reviewers; **tests/lint/types are
the referent**, so judgment is mechanically checkable. *Surfaces:* rarely (stall at
cap / blocked). *Artifacts:* code, tests.

**Phase 5 — Ship (gate G5).** Dominant: type 7 (accountability). Agent assembles
the deploy decision — blast radius, rollback, cost, security sign-off, reversibility
class. *Surfaces:* always (irreversible). *Artifacts:* deploy plan.

## The human's total interaction (the "how much human" answer)

Across the whole flow: **seed** the vision/brand (P0) · **ratify** the MVP cut and
grounded options (P1–P2) · **ratify** the decision brief (G2) · **ratify** ship
(G5) · plus bounded **referent-failure escalations**. A handful of compressed
touchpoints, not continuous oversight — because every other judgment was converted
to referent-grounded labor the agent did and recorded.
