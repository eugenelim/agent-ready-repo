# Third example — a science / hardware product (the structurally-different stress test)

> DOGFOOD RECORD (RFC-0053). The two prior walks (`example-assistant`,
> [note 02](../0048-notes/02-worked-example-flow-trace.md); household-EA,
> [note 11](11-second-example-divergence-and-provisional-spine.md)) are both **consumer/agent
> software** products — structurally alike. This third walk is deliberately **off that axis**:
> a **science product with hardware in the loop** — a *self-driving-lab control plane* whose
> software designs experiments, drives instruments, **measures real readings**, and iterates over
> **multiple physical cycles**. It is the "structurally-different second example" RFC-0053's
> validation gate (Open question 1) owes, and it stresses the loop where software examples cannot.
> Domain facts are real desk research (web, 2026-06-30).

## The product idea (given)

An **agentic control plane for a self-driving lab**: software that runs closed-loop research cycles
over real instruments — **Design → Make → Test → Analyze (DMTA)** — proposing experiments, executing
them on hardware, capturing measurements, analyzing, and proposing the next cycle, toward a research
goal (e.g. optimize a material/formulation). Grounded in the mature SDL pattern: A-Lab (Bayesian
optimization + LLM experiment design, thousands of materials/week), Coscientist (LLM reasoning +
robotic liquid handlers + spectroscopic feedback), and the SiLA2/LIMS instrument-integration stack.

## Stage 1 — Divergence (Decision 6)

Axes: **altitude** (single instrument ↔ whole autonomous lab ↔ cross-lab platform) × **mechanic**
(how much the software *decides* vs. *plumbs*).

| | Shape | Bet | Great at | What kills it | Riskiest assumption |
|---|---|---|---|---|---|
| T1 | **Experiment copilot** (HITL) | suggest experiments + capture readings; scientist runs them | low risk, fast adoption, trust-building | thin — a smarter ELN; no autonomy payoff | scientists want suggestions, not just capture |
| T2 | **Closed-loop optimizer, one platform** | Bayesian/active-learning drives DMTA on a single rig | concrete cycle-time win; the A-Lab shape, scoped | one rig ≠ a product; integration tax per instrument | the loop beats manual on *this* rig (validate by experiment) |
| T3 | **Full SDL orchestration control plane** | schedule + drive many instruments; the lab OS | the real infra product; high value | huge surface; per-instrument driver tax; safety | one control plane generalizes across heterogeneous hardware |
| T4 | **Agentic AI-scientist** | LLM reasons over literature + results, generates protocols + control code (Coscientist) | the frontier; cognitive + physical autonomy | correctness/safety of generated control code on real hardware | LLM-generated protocols are safe to run physically |
| T5 | **Instrument-integration + readings/provenance layer** | the SiLA2/LIMS plumbing + measurement capture + data provenance; optimization later | foundational; everyone needs it; lowest research risk | commoditized-adjacent; not the "AI" story | integration + provenance is the real bottleneck |

**Re-convergence.** Unlike the software examples, the shapes here differ by **orders of magnitude in
cost and risk** — committing early (e.g. to T3/T4) is a multi-year misallocation. A defensible path:
**T5 foundation** (instrument integration + readings/provenance — the "measure readings" the brief
names) **+ T1 copilot** as the wedge, with **T2** (closed-loop on one platform) as the *bet to
validate by real DMTA cycles*, deferring **T3/T4** until the wedge proves the loop beats manual.
Autonomy is *earned per cycle*, not assumed. This staged answer is invisible without divergence.

## What this example *stresses* about the discovery-loop (the payoff)

This walk is valuable because it bends the loop where software products don't:

1. **The verifier is physical — slow, costly, and can fail *dangerously*.** A "cycle" is a real
   experiment (hours–days, consumable cost, robot/chemical safety), not a fast/cheap/safe test. This
   stresses **D4 (cost budget + outer cap)** hard, and turns the **discovery-threat-reviewer** from
   an infosec lens into a **physical-safety** lens — an unsafe reaction or robot action is a
   *physical one-way door*. **Finding:** the discovery reviewer roster must stretch to
   **operational/physical safety** for hardware products (reuse `operational-safety` depth; possibly
   a roster note for RFC-0048's implementing spec).
2. **Two loops, do not conflate.** The user's "iterations through multiple cycles" is the **product's
   runtime DMTA loop**, *not* the discovery loop. `discovery-loop` must **design** the DMTA control
   plane; it must not be confused with running it — the same two-loops discipline as
   discovery-vs-`work-loop`/`release-loop`. **Finding:** a discovery spine can legitimately *contain
   the design of another loop*; the RFC's "what converges" frame should not be read as "the only loop."
3. **Hardware grounding is a supplied-contract problem.** SiLA2/LIMS + proprietary instrument drivers
   are contracts the loop may not hold → **GROUND via `contract-acquisition` (RFC-0041) or SURFACE**,
   exactly the grounding-vs-surface triage — and worse than the store-sourcing case (note 11) because
   getting it wrong damages hardware.
4. **Converged ≠ validated, at its sharpest.** It is *research*: the outcome itself is unknown — the
   spine cannot assume the science works. The validation hooks here **are experiments** (the
   product's own DMTA), and a kill condition is literal ("the closed loop does not beat manual after
   N cycles / cost"). Desk-grounding can confirm the *pattern* (SDLs exist) but never that *this*
   research goal is reachable.

## Grounding-vs-surface triage

| Dependency | Referent? | Verdict |
|---|---|---|
| DMTA closed-loop pattern | **Yes** — A-Lab, Coscientist, SDL literature | **GROUND** |
| SiLA2 / LIMS / instrument contracts | **Partial** — standard exists; per-device drivers proprietary | **GROUND via contract-acquisition where held, else SURFACE** |
| physical-safety envelope (dangerous reactions/robot actions) | **Partial** — domain SOPs exist, site-specific | **SURFACE** to a human + safety lens (physical one-way door) |
| whether the closed loop beats manual for *this* goal | **No** — it is the research question | **VALIDATE** by the product's own DMTA cycles |
| the specific instruments/budget/site | **No** — adopter-specific | **SURFACE** — elicit |

## Stage 3 — provisional spine (tagged)

- **Vision** — accelerate a research program by closing the DMTA loop over real instruments.
  **[VALIDATE: does autonomy beat manual here?]**
- **Capabilities** — instrument integration + readings/provenance **[GROUND/contract-acquisition]** ·
  experiment copilot **[GROUND]** · closed-loop optimizer (one platform) **[VALIDATE by DMTA]** ·
  orchestration/scheduling **[SURFACE: per-site]** · safety envelope **[SURFACE: physical one-way door]**
- **Architecture** — the control plane *is a designed runtime loop* (DMTA): planner → instrument
  drivers (SiLA2) → measurement capture → analyzer → next-experiment proposer; agentic reasoning
  optional (T4) and gated by safety. **[Two-loops note: discovery designs this; it does not run it.]**
- **Validation plan** — V1 expert interviews (which research programs, manual baseline) · V2 a
  shadow/HITL pilot on one rig (copilot accuracy) · V3 a bounded closed-loop run on one platform
  with a hard cost/cycle cap + a kill condition (does it beat manual?) · V4 a safety review of any
  generated control code **before** it touches hardware.

## What this demonstrates for RFC-0053

- **Reinforces Decision 6 hardest** — the shapes differ by orders of magnitude in cost/risk; early
  commitment is the most expensive here, so forced divergence matters most.
- **Stresses D4 + the safety contract** — physical cycles + safety make the cost cap and a
  physical-safety reviewer lens load-bearing, not optional.
- **Confirms the two-loops discipline** — a discovery spine may design *another* runtime loop; the
  "what converges" frame is about the *discovery* loop only.
- **Confirms converged ≠ validated at the extreme** — for a research product, only experiments
  validate; the spine is explicitly a hypothesis whose verifier is physical.

**Sources (desk research, 2026-06-30):** SDL DMTA closed loop + A-Lab + Coscientist [arXiv:2510.23045
*A Survey of AI Scientists*; PMC9454899 *Autonomous Chemical Experiments*; IFP *Scaling Materials
Discovery with Self-Driving Labs*; ChemCopilot 2026]; SiLA2/LIMS instrument integration + orchestration
layers [Wiley Analytical Science 2019; Tecan SiLA2 SDK, ScienceDirect; *Reference architecture model
for robot integration*, ScienceDirect].
