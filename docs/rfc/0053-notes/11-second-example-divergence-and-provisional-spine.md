# Second example — divergence, the provisional spine, and the grounding-vs-surface triage

> DOGFOOD RECORD (RFC-0053). A second, structurally-different walk of `discovery-loop` —
> a **household executive-assistant AI** — run to test two things RFC-0053's first spike
> (the `example-assistant`, [note 02](../0048-notes/02-worked-example-flow-trace.md)) did
> not: (1) whether the **all-convergent loop commits early** without a divergence stage, and
> (2) whether a converged blackboard over-claims (**converged ≠ validated**). Both failures
> reproduced. This record is the evidence behind **Decision 6** (the exploratory scaffold) and
> the § *Converged is not validated* principle. Domain facts are real desk research (web,
> 2026-06-30); the point of the walk is the *method*, not the kitchen app.

## What the loop did wrong on the first pass (the finding)

Asked to scaffold "an executive-assistance AI for household kitchen management," the loop —
running purely convergent (G0→G1→G1.5→converge→G2) — **locked onto the first coherent framing**
(a narrow kitchen "draft-and-approve" assistant) and elaborated it to a full decision brief. It
**missed**:

- a *higher altitude* — a real top executive/estate manager runs the **whole household** (staff,
  vendors, property, $500k–several-million budgets, travel, correspondence, appointments); the
  kitchen is one sliver [AchieveHospitality; Aunt Ann's In-House Staffing];
- a *deeper sub-domain* — meal → recipe → ingredient → **which store stocks it, at what price** is a
  whole knowledge/sourcing layer the first pass glossed.

This is textbook **myopic-greedy commitment** (the failure mode RFC-0048 note 03 names). It is not
fixed by "research harder" — desk research and the operator shared the same blind spot. It is fixed
**structurally**, by forcing divergence before convergence.

## Stage 1 — Divergence (what Decision 6 adds)

Candidate product shapes across **altitude** (narrow-slice ↔ whole-domain) × **mechanic** (how it
gets/keeps knowledge):

| | Shape | Bet | Great at | What kills it | Riskiest assumption |
|---|---|---|---|---|---|
| S1 | Kitchen EA — draft & approve *(the first-pass framing)* | invert the maintenance burden for food only | weeknight toil; food waste | too narrow to be a "household EA" | coarse state is enough (A2) |
| S2 | **Household chief-of-staff EA** | be the principal's estate manager; kitchen is one module | matches a real EA; high willingness-to-pay | huge surface; cross-domain trust | a generalist EA is trusted across all domains (A4) |
| S3 | Sourcing / knowledge-graph-first | the core is meal→recipe→ingredient→store→price | concrete $ savings; buyable ontologies | store data fragmented/unreliable | store-sourcing data is good enough |
| S4 | Coordination layer (concierge) | orchestrate the *humans* + existing apps; nudge, delegate, follow up | sidesteps the pantry-sync death; mirrors how a real EA delegates | depends on members doing nudged tasks | households respond to delegation (A1/A3) |
| S5 | Ambient / auto-capture | passively capture state (receipts, bank feed, smart-fridge) | zero logging burden | the confirmed pantry-sync failure; privacy | passive capture is accurate enough |

**Re-convergence (and how divergence changed the answer).** The first pass jumped to S1. Run with
divergence, the answer inverts: the *strategic* product is **S2** (household chief-of-staff), its
mechanic should be **S4** (concierge/delegation, not data-ownership — which also dodges the
pantry-sync death every competitor hit), the kitchen module rests on **S3's core as a *bought*
dependency** (a recipe ontology), and it **does not promise** store-accurate sourcing (S3's fatal
assumption). S1 survives only as a deliberately-narrow **first slice to ship**, not the product.
That re-framing is invisible without the divergence pass — which is the argument for Decision 6.

## The deep sub-domain + the grounding-vs-surface triage

| Knowledge dependency | Referent? | Verdict |
|---|---|---|
| recipe ↔ ingredient mapping + substitution | **Yes** — Spoonacular food ontology, Edamam graph (2.3M recipes, Ontotext GraphDB) | **GROUND** — integrate a supplied API; don't build |
| ingredient → nutrition / dietary flags | **Yes** — same APIs | **GROUND** |
| what a top EA / estate manager actually does | **Yes** — documented estate-management practice | **GROUND** (frame-domain) |
| store-level "who stocks X, at what price" | **Partial/unreliable** — major-chain APIs exist, thin coverage, scraping-based | **SURFACE** — ground where reliable, human-checkpoint elsewhere; don't promise universal sourcing |
| the **altitude** bet (kitchen vs whole-household) | **No referent** — a value/scope call | **SURFACE** at G1.5 |
| the principal's prefs / dietary / budget / family | **No referent** — user-specific | **SURFACE** — elicit, never invent |

This is the **resolve-vs-surface predicate** (note 05) applied *to discovery itself*: ground only
where a reliable referent exists; **surface rather than grind** where it is absent or unreliable —
because more loop rounds there produce confident hallucination, not truth.

## Stage 3 — the provisional spine (converged ≠ validated)

The chosen spine (S2 + S4 mechanic, S3-core integrated) emitted as a *connected hypothesis*, each
node tagged **[GROUND]** / **[SURFACE]** / **[VALIDATE→Vn]**:

- **Vision** — a household runs food/calendar/vendors/budget by delegating to an assistant that
  drafts and acts only on approval. **[VALIDATE→V1: generalist EA vs. point tools?]**
- **Capabilities** — food-and-meals *(first slice)* **[GROUND]** · calendar · vendors/home-maint ·
  budget/spend **[GROUND: receipt/bank capture feasible]** · errands/delegation · identity/trust
  **[GROUND security; SURFACE: cross-domain trust threshold]**. *Wedge domain?* **[SURFACE + V1]**
- **Domain** — food cycle plan→shop→cook→restock **[GROUND]** · estate-manager to-be model
  **[GROUND]** · recipe↔ingredient ontology **[GROUND: buy]** · store sourcing **[SURFACE]** ·
  principal prefs **[SURFACE]** · real friction ranking **[VALIDATE→V1]**
- **Journey / architecture / backlog** — concierge mechanic over a recipe-API-backed kitchen module,
  identity/trust first; each node traced to an outcome. **[VALIDATE→V2: observe one real week]**

**Validation plan (the "room left in").** V1 interviews (n≈8: wedge, generalist-vs-point, trust) ·
V2 one-week diary study (n≈5 households: real cycle, delegation response, A1/A3) · V3 two-week
Wizard-of-Oz pilot (human behind the curtain → tests the concierge bet without building it, A1/A2) ·
V4 usability test (restock + approval flow, A2). The spine is built **to be entered into these**, not
to replace them — the agent can scaffold each guide + synthesize transcripts, but a human runs the
sessions (the GAP-1 boundary).

## What this demonstrates for RFC-0053

- **Decision 6 is warranted.** A purely convergent loop commits early; divergence-then-convergence
  caught a strictly better framing the first pass could not see.
- **Converged ≠ validated.** The brief is a provisional spine; its load-bearing assumptions (A1–A5)
  are knowable only through V1–V4, which desk-grounding cannot substitute for.
- **The triage is the resolve-vs-surface predicate.** Ground against a referent; surface where none
  exists. "Keep grinding" was the wrong default on the absent/unreliable referents.

**Sources (desk research, 2026-06-30):** household food waste ~⅓ of food acquired; ~$2,913/yr family
of four [Penn State; RTS; EPA]; 32% shop with no plan, planners save ~$564/yr [ReFED]; pantry-sync
is the killer failure ("can never stay synchronized"; Plan to Eat removed it) [MealThinker; Recipy;
OrganizEat]; estate-manager scope = household COO [AchieveHospitality; Aunt Ann's]; recipe↔ingredient
ontologies [Spoonacular; Edamam/Ontotext]; store availability fragmented [Datarade; ScrapingBee].
