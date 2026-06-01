# Spec: greenfield-inception

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0021, ADR-0011
- **Brief:** none <!-- authored directly from the RFC, not decomposed from a product brief -->
- **Contract:** none <!-- init-project is a skill (an LLM workflow); it exposes no machine interface, so new-spec step 4b is skipped -->
- **Shape:** mixed — a skill (the `init-project` workflow), a CONVENTIONS seed amendment, and adopter guides. The plan's `## Design (LLD)` is pruned to the two sub-sections this spans.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter starting a **brand-new repo** from an idea has no front-door today.
The methodology has a brownfield front-door (`adapt-to-project`), a downstream
build loop (brief → foundation → spec → LLD → `work-loop`), and — since
RFC-0020 — a foundation artifact (`reference.md`). Greenfield has nothing: the
adopter researches the idea, then *yolo*s a throwaway prototype and retrofits
structure once it sort-of works, losing the research rationale and shipping no
recorded foundation.

This feature gives that path a home: **`init-project`**, a new `core` skill that
turns an idea into a structured repo by **composing the skills the repo already
owns** — it orchestrates, it does not reinvent. It runs a **trigger gate**
(throwaways and single-scripts skip it and scaffold directly; it fires only when
there are real stack/structure/tooling decisions); applies a **value gate over
fed-in discovery** (`research`-pack output, a provided PRD, or a `receive-brief`
brief — `init-project` *consumes* discovery, it never performs it), pausing if
the business value can't be stated plainly, and emitting the first **brief**;
makes the **foundation decision** with recorded rationale — an **ADR** plus
**`reference.md`**, authored from the arc42 template asset RFC-0020 already
shipped; authors a **walking skeleton** (a thin, kept, end-to-end slice that
links the main architectural components) as a spec via `new-spec` and hands its
*build* to `work-loop`; then **hands off** to the normal `brief → spec → LLD →
work-loop` loop with `reference.md` in place for every LLD to conform to.

Success for the adopter: starting from an idea (and a discovery shape produced
upstream), they run one skill and end up with a recorded foundation, a validated
walking skeleton, and the normal build loop running — instead of a throwaway
they later clean up. The steps are **fluid phases of attention, not a waterfall**
(revisitable as understanding firms up), with **scoped handoffs** (each step gets
only the artifacts the next one needs). The flow stays out of the way for
throwaways, and it is explicitly **not** an autonomous code generator.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Run the **trigger gate first**: if there are no real stack/structure/tooling
  decisions ahead (a script, a spike, a throwaway), scaffold directly and **skip**
  the flow; otherwise continue.
- **Consume** fed-in discovery — `research`-pack output (applied mode), a provided
  PRD, or a `receive-brief` brief — as the input to the value gate.
- **Compose** the existing skills (`research` handoff, the brief, `reference.md`
  authoring, `new-spec`, `work-loop`) — orchestrate them; reference them rather
  than restating their procedures.
- Treat the steps as **fluid, revisitable phases** (the walking skeleton routinely
  sends you back to amend the foundation), and pass each step only the artifacts
  it needs (**scoped handoff**).
- Author the foundation decision with **recorded rationale** — an ADR (what / why
  / alternatives / re-evaluation date) and a `reference.md` instantiated from the
  arc42 template asset.

### Ask first

- Before proceeding past the **value gate** when the business value can't be
  stated plainly — pause and send discovery back upstream rather than guessing.
- Before treating the **walking skeleton** as anything other than kept-and-minimal
  — it is authored as a real spec and built through `work-loop`, never a sketch.
- Before choosing a stack with **no recorded rationale** — the foundation decision
  needs its ADR before the skeleton is authored.

### Never do

- **Never perform discovery / research itself.** Discovery is fed *in* (the
  `research` pack's job); `init-project` consumes a shape, it does not own the
  research phase.
- **Never build an autonomous multi-agent "software company" code generator.** The
  human stays in the loop; the existing skills do the work.
- **Never force the flow onto throwaways.** The trigger gate must keep
  single-scripts and spikes on the yolo path.
- **Never produce a throwaway prototype** in place of the walking skeleton — the
  skeleton is kept and minimal, held to the feature contract.
- **Structural:** **never add a new top-level directory** — `init-project` lives at
  `packs/core/.apm/skills/init-project/`, beside the other `core` skills — and
  **never add a cross-pack code import**; `core` imports nothing from another pack
  and the skill composes other skills by *reference*, not import.

## Testing Strategy

`init-project` is an LLM workflow that composes already-shipped, already-tested
skills and assets; it introduces **no new code and no compressible-invariant
logic**, so there is no TDD surface here. Verification is goal-based file/lint
checks plus manual QA of the documented judgment.

- **Skill file + frontmatter: goal-based check.** The `SKILL.md` exists at its
  conventional `core` path and its frontmatter passes `tools/lint-skill-spec.py`;
  the documented procedure contains each named stage (trigger gate, value gate,
  foundation, walking skeleton, handoff) and the declared anti-patterns. No
  production test asserts what file-presence and the linter already prove.
- **`init-project` workflow behavior: manual QA.** The skill's judgment — the
  trigger-gate decision, the value gate, the compose-not-generate posture, the
  author-spec-hand-build split — is verified by walking the flow end to end
  against a worked greenfield scenario and recording the result in the PR, not by
  a unit test that would only assert mock shapes.
- **CONVENTIONS seed amendment: goal-based check.** The seed documents the two
  front-doors and `make build-self` projects it cleanly.
- **Adopter guides: goal-based for existence, manual QA for accuracy.** The three
  guide files existing at their Diátaxis paths is a goal-based check; whether each
  reads accurately against the shipped skill is a manual review recorded in the PR.
- **Projection + gate: goal-based check.** `make build-self` projects the new core
  skill cleanly (no unexpected reverts) and `make build-check` is green.

## Acceptance Criteria

- [x] The **`init-project`** skill ships at
  `packs/core/.apm/skills/init-project/SKILL.md` with valid frontmatter that
  passes `tools/lint-skill-spec.py`.
- [x] The skill documents the **trigger gate as its first step** — real
  stack/structure/tooling decisions → continue; a script / spike / throwaway →
  scaffold directly and skip the flow (Decision 3).
- [x] The skill documents **consuming fed-in discovery** from any of the three
  sources (`research`-pack output, a provided PRD, a `receive-brief` brief) and
  states explicitly that it **does not perform discovery itself**.
- [x] The skill documents the **value gate**: derive business value + MVP from the
  discovery; pause and send discovery upstream if the value can't be stated
  plainly. Its output is the first **brief** (the RFC-0019 artifact).
- [x] The skill documents the **foundation step**: choose the stack/architecture
  with recorded rationale — an **ADR** (what / why / alternatives / re-evaluation
  date) **and `reference.md`**, authored from the arc42 template asset at
  `packs/core/.apm/skills/adapt-to-project/assets/reference.md` (the greenfield
  population path ADR-0010 names).
- [x] The skill documents the **walking-skeleton step**: author a single spec via
  `new-spec` for a thin end-to-end slice that links the main architectural
  components, and **hand the build to `work-loop`** — kept and minimal, not a
  throwaway (resolves RFC-0021 Open Question 1: orchestrate, don't execute).
- [x] The skill documents the **handoff**: from the skeleton on, the normal
  `brief → spec → LLD → work-loop` loop runs with `reference.md` in place for every
  LLD to conform to.
- [x] The skill documents the **fluid-not-waterfall** posture (revisitable phases)
  and **scoped handoffs** (each step receives only the artifacts the next needs).
- [x] The skill's **anti-patterns** explicitly **decline the autonomous
  multi-agent generator** and **forbid forcing ceremony on throwaways** (Decision
  4 + the trigger gate).
- [x] **No new top-level directory and no cross-pack import** are introduced — the
  skill lives under `packs/core/.apm/skills/` and composes other skills by
  reference, not import.
- [x] The **`CONVENTIONS.md` seed amendment** documents the **two front-doors**
  (greenfield `init-project` / brownfield `adapt-to-project`) and where each enters
  the loop; it lands in this spec's implementing PR (it documents an entry point
  this spec creates, so it ships atomically with it).
- [x] **`make build-self`** projects the new core skill cleanly (no unexpected
  reverts to projected paths) and **`make build-check`** is green.
- [x] Three adopter-facing **guide files exist** under `docs/guides/` at their
  Diátaxis paths — a **tutorial** ("From idea to a walking skeleton: start a new
  project"), a **how-to** ("Decide and record your foundation during inception"),
  and an **explanation** ("Why a walking skeleton beats a throwaway prototype").
  *(Authored in this catalogue repo via `new-guide`, which lives in the non-core
  `user-guide-diataxis` pack; guide authoring is not a capability `core` ships to
  adopters — per RFC-0021's "guides in this catalogue repo" scoping.)*
- [x] Each of the three guides **reads accurately** against the shipped skill
  (manual-QA review recorded in the implementing PR).

## Assumptions

- Process: spec is constrained by RFC-0021 (Accepted 2026-06-01); Decisions 1–4
  (new `init-project` flow; value-gate-over-fed-in-discovery → foundation →
  walking skeleton → handoff; trigger gate; compose-not-autogenerate) are settled
  by the RFC's acceptance, not re-litigated here (source:
  `docs/rfc/0021-greenfield-inception.md`).
- Process: the greenfield-front-door decision, the compose-not-generate engine
  choice, and the resolved Open Question 1 (author the skeleton spec, hand the
  build to `work-loop`) are recorded in ADR-0011, drafted alongside this spec
  (source: `docs/adr/0011-greenfield-inception-front-door.md`; user confirmation
  2026-06-01 to draft the ADR now).
- Process: RFC-0021 Open Question 1 is resolved to the RFC's recommended default —
  `init-project` authors the walking-skeleton spec and hands the build to
  `work-loop` (source: user confirmation 2026-06-01; recorded in ADR-0011 D6).
- Process: the soft ordering dependency is satisfied — the three composed specs
  (`product-brief-intake`, `lld-aware-spec-plan`, `reference-architecture`) are all
  `Status: Shipped` (source: `docs/specs/*/spec.md`).
- Technical: the skill lands at `packs/core/.apm/skills/init-project/`, the
  greenfield twin of `adapt-to-project`, beside the four existing core skills
  (source: `ls packs/core/.apm/skills/`).
- Technical: discovery is fed in from the `research` pack's `research` skill, a
  provided PRD, or `receive-brief`; `init-project` consumes it (source: RFC-0021
  Non-goals; `ls packs/research/.apm/skills/`).
- Technical: the foundation step authors `reference.md` from the arc42 template
  asset already shipped at
  `packs/core/.apm/skills/adapt-to-project/assets/reference.md` (instantiated on
  demand, never a seed); this catalogue repo has no `reference.md` of its own
  (source: `reference-architecture` spec; `ls docs/architecture/`).
- Technical: no `new-spec` step 4b contract — the skill exposes no machine
  interface (source: `new-spec` SKILL.md step 4b conditional;
  `product-brief-intake` Contract: none precedent).
- Process: the CONVENTIONS seed amendment and three adopter guides ride along in
  the implementing PR — RFC-0021 § Follow-on names both, and the
  `product-brief-intake` / `reference-architecture` specs set the precedent that an
  RFC-authorized CONVENTIONS amendment ships with the feature that creates the
  entry point (source: `docs/rfc/0021-greenfield-inception.md` § Follow-on;
  `docs/specs/product-brief-intake/spec.md`).
- Product: the adopters served are those starting brand-new repos with real
  stack/structure decisions — the frequency bet RFC-0021 Assumption 1 flags as
  falsifiable (source: RFC-0021 Problem & goals + Risks).
