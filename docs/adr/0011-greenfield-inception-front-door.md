# ADR-0011: Greenfield inception is a new `init-project` flow that composes existing skills — a value gate over fed-in discovery, a recorded foundation, then a walking skeleton; not an autonomous generator

- **Status:** Accepted <!-- Proposed | Accepted | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-06-01
- **Deciders:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0021 (greenfield inception — the accepted proposal these decisions record); RFC-0019 + ADR-0009 (the brief and the plan-owned LLD — `init-project` emits the first brief and hands off to this loop); RFC-0020 + ADR-0010 (the normative `reference.md` — `init-project`'s foundation step is the greenfield population path that authors it); the `adapt-to-project` skill (the brownfield front-door this mirrors); the `research` pack (applied-mode discovery, fed *in*); `greenfield-inception` spec; `docs/CHARTER.md` §Principles

## Context

The methodology has a **brownfield** front-door (`adapt-to-project`), a downstream
build loop (brief → foundation → spec → LLD → `work-loop`), and — once RFC-0020
shipped — a foundation artifact (`reference.md`). It has **no greenfield
front-door**. The forces at play when an adopter starts from a brand-new repo:

- **No idea→repo path.** Adopters research an idea, then *yolo* a throwaway
  prototype and retrofit structure once it sort-of works — losing the research
  rationale and shipping no recorded foundation (the yolo-then-cleanup
  anti-pattern). The cross-industry principled replacement is the **walking
  skeleton / tracer bullet / steel thread**: a thin, kept, end-to-end slice that
  links the main architectural components and validates the architecture early.
- **The stack decision goes unrecorded.** Greenfield is exactly where the
  stack/structure/tooling choices are made; without a value-gated inception they
  are improvised, and the *why* is lost.
- **`reference.md` has a greenfield producer named but not built.** ADR-0010 D4
  names greenfield authoring as one of three population paths and points it at
  RFC-0021; the template asset (`packs/core/.apm/skills/adapt-to-project/assets/reference.md`)
  already ships, waiting for that producer.
- **Throwaways must stay frictionless.** A weekend script does not want
  inception ceremony; forcing it drives people off the path.
- **Multi-agent envy.** The prior art includes autonomous "AI software company"
  generators (BMAD's autonomous end, MetaGPT, ChatDev) that turn one line into a
  repo — impressive demos, but uneven, survivorship-biased production quality and
  a heavy framework to own.
- **Reuse over new mechanism.** The repo already has every piece: `research`
  (discovery), the brief layer (RFC-0019), `reference.md` authoring (RFC-0020),
  `new-spec`, and `work-loop`. Greenfield inception is an *orchestration* of these,
  not a new artifact type.

## Decision

> We will add a **greenfield front-door** — the **`init-project`** flow, a `core`
> skill — that turns an *idea* into a structured repo by **composing existing
> skills**: a **trigger gate** filters out throwaways; a **value gate over
> fed-in discovery** produces the first brief; a **foundation step** records the
> stack as an ADR + `reference.md`; a **walking skeleton** validates that
> foundation; then it **hands off** to the normal `brief → spec → LLD →
> work-loop` build. It is the greenfield twin of `adapt-to-project`, not an
> extension of it, and it is **not** an autonomous code generator.

Specifically, recording RFC-0021's four decisions plus its resolved open question:

1. **Front-door locus (RFC-0021 D1).** A **new** greenfield inception flow
   (`init-project`), not an extension of `adapt-to-project` — that skill adapts
   *existing* content; greenfield has none. The two are symmetric twins under
   `core`.
2. **Flow shape (D2).** Trigger gate → **value gate over fed-in discovery** →
   **foundation** (ADR + `reference.md`) → **walking skeleton** → **handoff** to
   `brief → spec → LLD → work-loop`. These are **fluid phases of attention, not a
   one-way waterfall** (any artifact is revisitable as understanding firms up),
   with **scoped handoffs** — each step receives only the artifacts the next step
   needs, not the whole accreted history.
3. **Trigger gate (D3).** Throwaway / single-script / spike repos **skip** the
   flow and scaffold directly (yolo stays fine). It fires **only** when there are
   real tech-stack / structure / tooling decisions.
4. **Generation engine (D4).** **Compose existing single-purpose skills** +
   author a walking skeleton; **decline** the autonomous multi-agent "software
   company" engine as the engine, while **borrowing** its agent-orchestrated
   *structured-document handoff* and its *scoped-context* discipline. The human
   stays in the loop and the existing skills do the work.
5. **Discovery is fed *in*, never owned (D2/Non-goals).** `init-project`
   **consumes** a discovery shape — `research`-pack output (applied mode), a
   provided PRD, or a `receive-brief` brief — and does not perform market /
   technical research itself. Owning discovery is the `research` pack's job
   (scoped-handoff principle).
6. **Walking skeleton: author the spec, hand the build to `work-loop` (RFC-0021
   Open Question 1).** `init-project` **orchestrates** — it authors the
   walking-skeleton *spec* through `new-spec` and hands the *build* to
   `work-loop`; it does not itself execute the build. The skeleton is held to the
   same contract as any feature — **kept and minimal, not a throwaway**.

## Consequences

**Positive:**

- Greenfield gains a front-door symmetric to brownfield's: idea → structured repo
  with a justified foundation, replacing yolo-then-cleanup.
- `reference.md`'s greenfield population path (ADR-0010 D4) is realized — the
  foundation step authors the first `reference.md` from the already-shipped
  template asset, and every downstream LLD conforms to it.
- The stack decision is reasoned and recorded (an ADR with alternatives + a
  re-evaluation date), not improvised.
- Boring and maintainable: no new agent framework, no new artifact type — an
  orchestrating skill over machinery the repo already owns and tests.
- Throwaways stay frictionless; ceremony lands only where it pays.

**Negative:**

- A new orchestrating skill to own and keep accurate as the skills it composes
  (`research`, brief, `reference.md` authoring, `new-spec`, `work-loop`) evolve.
- A soft ordering dependency: `init-project` composes RFC-0019 + RFC-0020
  artifacts, so those must land first (they have — all three sibling specs are
  Shipped).
- The "walking skeleton" can decay into the throwaway it was meant to replace if
  it is not held to the feature contract. Mitigated by D6 — it is authored as a
  real spec and built through `work-loop`.

**Neutral / to revisit:**

- **Frequency bet (RFC-0021 Assumption 1, falsifiable).** Greenfield-with-real-
  decisions must happen often enough among adopters to earn a front-door
  (Principle 4). If most new repos are throwaways, the gate sends them to yolo and
  this rarely fires — watch adoption.
- **Steel-thread generalization (Assumption 2).** The walking-skeleton claim is
  decades-stable for human teams; that it holds for *agent-built* repos is the
  part not yet proven and worth watching.
- The value-gate trigger ("real decisions ahead?") is a judgment, not a flag;
  whether agents apply it consistently is observable in practice.

## Alternatives considered

- **Extend `adapt-to-project` instead of a new flow (D1)** — rejected: that skill
  adapts *existing* content by definition; greenfield has none. Folding them
  conflates two opposite starting conditions.
- **Template-repo only (`Use this template`) (D1)** — rejected: zero logic, but no
  value gate, no recorded foundation, and no skeleton — it scaffolds files, not a
  reasoned start.
- **Foundation-first, no inception (D2)** — rejected: skips the value gate; the
  stack is chosen before the problem is understood.
- **Skeleton-first, no foundation (D2)** — rejected: validates integration but
  bakes in unrecorded stack decisions — the very loss this replaces.
- **Always run / never run the flow (D3)** — always-run is friction on a weekend
  script; never-run is back to yolo-then-cleanup. The "real decisions" gate is the
  right-size-to-stakes middle.
- **Autonomous multi-agent "software company" engine (D4)** — rejected as the
  engine: uneven production quality, a heavy framework, survivorship-biased
  evidence (RFC-0021 research AP2). Its *structured-document handoff* and
  *scoped-context* discipline are borrowed; the autonomous engine is not.
- **Pure stack scaffolder (`create-*` / cookiecutter) (D4)** — rejected: fast code
  but no reasoned foundation and no value gate.
- **`init-project` authors *and builds* the walking skeleton (Open Q1)** —
  rejected: it would duplicate `work-loop`'s execution role. `init-project`
  orchestrates; `work-loop` executes (D6).
- **`init-project` performs discovery itself** — rejected: that is the `research`
  pack's scope. Owning it would violate the scoped-handoff boundary and bloat the
  flow.

## References

- RFC-0021 — `docs/rfc/0021-greenfield-inception.md` (the accepted proposal;
  Decisions 1–4, the three-RFC seam diagram, Open Question 1, § Follow-on
  artifacts).
- RFC-0021 research — `docs/rfc/0021-greenfield-inception-research.md` (the
  applied-mode prior-art survey: walking skeleton / steel thread, Lean Inception,
  the spec-driven / agentic landscape, the survivorship-bias flag on autonomous
  generation).
- ADR-0009 — `docs/adr/0009-product-brief-layer-and-plan-owned-lld.md` (the brief
  layer and plan-owned LLD `init-project` feeds).
- ADR-0010 — `docs/adr/0010-reference-architecture-foundation.md` (the normative
  `reference.md`; D4 names greenfield authoring — this ADR's flow — as a
  population path, and ships the template asset it consumes).
- `greenfield-inception` spec — `docs/specs/greenfield-inception/spec.md` (the
  implementation contract for `init-project`).
- [Walking skeleton (Henrico Dolfing)](https://www.henricodolfing.com/2018/04/start-your-project-with-walking-skeleton.html);
  [Steel threads (Rubick)](https://www.rubick.com/steel-threads/);
  [Lean Inception (Fowler)](https://martinfowler.com/articles/lean-inception/).
