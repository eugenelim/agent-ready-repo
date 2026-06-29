# Spec: frame-domain

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0048 (Decision 4; child 2 of the autonomous product-team series — the foundation RFC is Open and *provisional*, and this spec is authored under its series-execution standard, Decision 9) · RFC-0040 + ADR-0030 (the consolidated `agentbundle-layout.toml` adopter-file mechanism the config-resolution tier reads)
- **Brief:** none
- **Contract:** none — the two typed artifacts are prompt-only markdown schemas carried in the `frame-domain` skill body (Charter Principle 3); there is no `contracts/<type>/` file, no API surface.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An agent shaping a product upstream — at the G1.5 Domain & MVP point of the
discovery loop, or standalone — runs the `frame-domain` skill and gets **two
typed artifacts that ground the product in the real-world activity it serves and
bound its MVP before any screen, service, or architecture is drawn**. The skill
emits them together from one `research`-grounded pass, but they are separate
artifacts because they have separate downstream lifecycles:

1. **Domain Framing** (`domain-framing.md`, `type: domain-framing`) — the
   grounding artifact. It has a **real-world-activity half** (how the activity is
   actually done, its best practice, and the naive-design failure modes —
   evidence-grounded via `research` applied mode, not the agent's untested
   intuition) and, for a brownfield product, a **current-system half** (how the
   existing system already does it, reverse-engineered from code and docs via
   `decision-archaeology` plus architecture extraction). Its purpose is
   correctness against **hallucinating a domain the agent does not know**.
2. **Scope Boundary** (`scope-boundary.md`, `type: scope-boundary`) — the
   upstream **MVP out-of-scope register** that names, explicitly, the tempting
   capabilities the appetite excludes, each with its appetite reason. It is the
   G1.5 **scope-creep guard** against **over-scoping past the MVP**; the brief
   inherits and refines it at G3 (the `scope-boundary → brief` edge).

Each artifact carries a stable marker — a canonical filename and a frontmatter
`type:` — so downstream lenses and tools can find it regardless of where the
adopter's layout puts it, and the skill resolves each write path through the
catalogue's standard three tiers (config → designed default → discover-by-marker)
so it is never hardcoded. Each finding the agent cannot ground from evidence is
surfaced as a named residual assumption rather than silently asserted, so a human
reviewing the MVP boundary sees exactly what rests on grounding and what rests on
a guess.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Wrap `research` applied mode** to produce Domain Framing's real-world-activity
  half — the applied-mode discipline (practitioner grey literature, the prior-art /
  best-practice / case-study / anti-pattern frames, the survivorship-bias and
  stale-prior-art overlay) is what grounds "how the activity is really done" and
  surfaces the naive-failure modes. The skill consumes the applied-mode findings
  and shapes them into the Domain Framing artifact; it does not re-implement retrieval.
- **Reverse-engineer the brownfield current-system half via `decision-archaeology`**
  (the rationale chain, alternatives considered, and revival check over the
  existing system's choices) plus architecture extraction from code and docs —
  into Domain Framing, only when a current system exists.
- **Emit the Scope Boundary's out-of-scope register** as a first-class artifact: the
  explicit list of tempting-but-excluded capabilities, each with the appetite reason
  it is out, so the scope-creep guard and the human at the MVP boundary have a
  referent (the brief inherits/refines it at G3).
- **Emit the stable markers** on each artifact: `domain-framing.md` /
  `type: domain-framing` and `scope-boundary.md` / `type: scope-boundary`, so each is
  discoverable by marker regardless of path.
- **Resolve the write path in three tiers** — (1) the adopter's chosen discovery
  base from `agentbundle-layout.toml` (RFC-0040 / ADR-0030's adopter-file mechanism;
  both files are shared *discovery-loop* artifacts, so their config home is
  the discovery layout key, not `product-engineering`'s file-per-slug
  `intents`/`rollups` table); (2) the designed defaults
  `docs/discovery/<initiative>/domain-framing.md` and `…/scope-boundary.md`;
  (3) discover-by-marker — and
  **create the directory lazily on first write**, at the resolved path.
- **Detect optional dependencies and degrade cleanly** — if `research` or
  `decision-archaeology` is not installed, name the gap in the artifact and
  produce the best-effort grounding the agent can, flagging the ungrounded residue
  as named assumptions (Tier-1 detect-and-degrade, RFC-0048 D8 progressive
  enhancement).
- **Surface every ungrounded finding as a named residual assumption** — anything
  the wrapped research could not settle is listed for the human, never asserted as
  fact.

### Ask first

- **Adding a component beyond the ones this spec fixes** — Domain Framing's two
  halves (real-world-activity, brownfield current-system) and Scope Boundary's
  out-of-scope register — e.g. folding the persona in as a co-product (per RFC-0048
  DRIFT-F persona is *elicited inline by its first consumer*, not a separately
  produced artifact; it is out of scope here),
  or adding a third artifact to the `frame-domain` skill's output.
- **Changing either canonical filename or frontmatter `type:` value**
  (`domain-framing.md` / `type: domain-framing`, `scope-boundary.md` /
  `type: scope-boundary`) — these are the stable contract other skills and the
  traceability lint resolve against; renaming any is a cross-artifact break.
- **Promoting the skill from a standalone producer to a non-skippable gate** — the
  hard "cannot proceed without it" enforcement is discovery-loop / coordinator
  doctrine (RFC-0048 D5/D7/D8, child 5), not this skill's to own.
- **Binding the exact config table/key for the shared `docs/discovery/` home** —
  RFC-0048 note 08 sketches it as `[experience.layout] discovery = "…"`, but
  `[<pack>.layout]` is the *manifest-side* default source, not the adopter-file
  read target, and the shipped `[product-engineering]` table is file-per-slug
  (`parent` + `intents`/`rollups`), which cannot host a per-initiative discovery
  tree. The precise adopter-file table for `docs/discovery/` is a **cross-cutting
  layout decision owned by the experience-pack / layout child effort** (the drift
  between note 08's sketch and the shipped ADR-0030 contract is surfaced here for
  reconciliation into RFC-0048, per its series-execution standard). Until it is
  bound, this skill resolves via the default and discover-by-marker tiers and reads
  whatever discovery key the layout effort settles — it does **not** mint a new
  table itself.

### Never do

- **No new dependency, no new top-level directory, no new module boundary, no new
  pack.** The skill lands in the existing `product-engineering` pack; the default
  `docs/discovery/` home is a *resolved default*, not a hardcoded path, and is
  introduced by RFC-0048's layout note, not minted here.
- **No runtime engine, script, or code that generates the artifact or its
  filename.** The artifact and its path are produced by the agent following the
  skill body (Charter Principle 3, prompt-only) — the same posture as
  `research-typed-artifacts` and `research-project-start`.
- **No hardcoded path.** The skill must never write to a literal path; it always
  runs the three-tier resolve, and surfaces ambiguity (multiple or zero
  marker-matches) rather than guessing.
- **No silent assertion of an ungrounded domain claim** — an unevidenced finding
  is either grounded by the wrapped research or surfaced as a named assumption;
  it is never stated as fact in the artifact body.

## Testing Strategy

- **Skill-body contract — wrapping, components, marker, resolution, degrade
  (AC1–AC8):** goal-based check. The deliverable is prompt-only prose in a
  skill body; `rg -F` greps assert that the body wires `research` applied mode and
  `decision-archaeology`, names the required components of both artifacts and the
  residual-assumption rule, emits both canonical filenames + frontmatter markers
  (`type: domain-framing`, `type: scope-boundary`),
  documents the three-tier resolve (incl. the ordered tiers and discover-by-marker),
  and names the detect-and-degrade path. There is no logic to unit-test — the right
  altitude is a structural grep, as in the `research-typed-artifacts` sibling spec.
  **AC8 (degrade) is grep-only by the prompt-only constraint** — no engine exists to
  exercise the dependency-absent branch, so the verification is that the body
  *specifies* the degrade behaviour, backstopped by the `Never do` "no silent
  assertion" rule.
- **Discoverability by marker (AC6):** goal-based check — a grep for each frontmatter
  marker (`type: domain-framing`, `type: scope-boundary`) against an artifact written
  to a *non-default* path resolves it, proving discovery does not depend on the path.
- **Two observable produced artifacts (AC2 + AC6):** visual / manual QA — a real
  `frame-domain` invocation against the RFC-0048 worked example
  (`example-assistant`) through its documented happy path produces
  `domain-framing.md` (the two grounding halves) and `scope-boundary.md` (the
  out-of-scope register) (AC2), each carrying its marker (AC6), recorded in the
  implementing PR. This is the end-to-end surface: the skill only proves out across
  the wrapped-research → shape → write flow.
- **Standalone invocability (AC9):** goal-based check — a grep asserts the body
  declares no hard dependency on the (unbuilt) coordinator / discovery-loop, and the
  worked-example run above is driven *without* the coordinator present.
- **Lint conformance (AC10):** goal-based check — `lint-packs` and the
  agent-artifact lint pass on the new skill (frontmatter, description, body
  shape).

## Acceptance Criteria

- [ ] **AC1 — wraps research applied mode.** The `frame-domain` skill body
  invokes `research` in `applied` mode to ground Domain Framing's real-world-activity
  half, and states that it *consumes and shapes* the applied-mode findings rather than
  re-implementing retrieval.
- [ ] **AC2 — two typed artifacts, fixed components.** The skill body defines two
  typed artifacts from one pass: **Domain Framing** with exactly two components (the
  real-world-activity half — how the activity is really done · best practice ·
  naive-failure modes — and the brownfield current-system half) and **Scope
  Boundary** (the MVP out-of-scope register).
- [ ] **AC3 — brownfield half via decision-archaeology.** The skill body
  reverse-engineers Domain Framing's current-system half via `decision-archaeology`
  plus architecture extraction, and states this half is produced **only when a
  current system exists** (greenfield omits it, and the artifact says so).
- [ ] **AC4 — Scope Boundary register is first-class.** The Scope Boundary schema
  requires the out-of-scope register to list each excluded capability *with its
  appetite reason*, not a bare list, and names it the G1.5 scope-creep guard the
  brief inherits/refines at G3.
- [ ] **AC5 — residual assumptions surfaced.** The body requires every finding the
  wrapped research could not ground to be listed as a named residual assumption,
  and forbids asserting an ungrounded domain claim as fact.
- [ ] **AC6 — stable markers.** Domain Framing is named `domain-framing.md` carrying
  `type: domain-framing`, and Scope Boundary `scope-boundary.md` carrying
  `type: scope-boundary`; given either at a non-default path, a marker search
  resolves it.
- [ ] **AC7 — three-tier path resolution.** The skill body documents resolution for
  each artifact in order: (1) the adopter's discovery base from
  `agentbundle-layout.toml` (RFC-0040 / ADR-0030 adopter-file mechanism — whatever
  discovery layout key the cross-cutting layout effort settles; currently unbound,
  see § Ask first, so resolution falls to the default and marker tiers until then;
  *not* `product-engineering`'s `intents`/`rollups` table), (2) designed defaults
  `docs/discovery/<initiative>/domain-framing.md` and `…/scope-boundary.md`,
  (3) discover-by-marker; it creates the directory lazily on first write and
  surfaces ambiguity rather than guessing.
- [ ] **AC8 — detect-and-degrade on optional deps.** With `research` or
  `decision-archaeology` absent, the skill names the gap, degrades to best-effort
  grounding, and flags the ungrounded residue — it does not fail hard and does not
  silently fabricate grounding. (Grep-only verification — see Testing Strategy.)
- [ ] **AC9 — standalone.** The skill is invokable standalone with no hard
  dependency on the unbuilt coordinator / discovery-loop; the worked-example run is
  driven without the coordinator present.
- [ ] **AC10 — lint-clean.** The skill passes `lint-packs` and the agent-artifact
  lint (frontmatter, description, body shape), and projects via `make build-self`
  with no drift.

## Assumptions

- Technical: the primitive ships as a new prompt-only skill `frame-domain` in the
  `product-engineering` pack (source: `packs/product-engineering/.apm/skills/`;
  RFC-0048 worked-example table row 3 "frame-domain (PE)").
- Technical: `research` applied mode emits `<topic-slug>-survey.md` and does not
  emit Domain Framing for free, so the skill wraps and shapes it (source:
  `packs/research/.apm/skills/research/SKILL.md`; `docs/rfc/0048-notes/03-autonomy-and-gate-economics.md`).
- Technical: the brownfield half is reverse-engineered via `decision-archaeology`
  (`<topic-slug>-archaeology.md`) + architecture extraction; research / archaeology
  are optional Tier-1 detect-and-degrade deps (source:
  `packs/research/.apm/skills/decision-archaeology/SKILL.md`; RFC-0048 Decision 8
  progressive-enhancement).
- Technical: the write path resolves config → default → discover-by-marker, with
  the config tier reading the adopter's discovery base from `agentbundle-layout.toml`
  (RFC-0040 / ADR-0030 adopter-file `[<pack>]` mechanism — *not* the manifest-side
  `[pack.layout]` table) and a stable marker (canonical filename + frontmatter
  `type:`) (source: `packs/research/.apm/skills/research-project-start/SKILL.md` +
  `references/agentbundle-layout.md`; `docs/specs/consolidated-pack-layout/spec.md`;
  `docs/rfc/0048-notes/08-artifact-layout-and-backlog.md`).
- Process: RFC-0048 note 08's `[experience.layout] discovery` config-key sketch
  drifts from the shipped ADR-0030 contract (wrong table side; PE's file-per-slug
  shape can't host a discovery tree); per the series-execution standard this drift
  is surfaced for reconciliation into RFC-0048, and the precise config key is
  deferred to the cross-cutting layout effort (source: this spec's Boundaries §
  Ask first).
- Process: authoring this child spec against the Open/provisional RFC-0048 is the
  series-execution standard the RFC itself adopts (source: RFC-0048 Decision 9 +
  Provisional-foundation note).
- Product: the skill emits two artifacts — Domain Framing (real-world-activity
  half + brownfield current-system half) and Scope Boundary (the MVP out-of-scope
  register) — split because they have separate downstream lifecycles; the persona
  is a separate artifact, excluded here (source: RFC-0048 Decision 4 + § Amendments
  2026-06-26 + task direction; `docs/rfc/0048-notes/04-artifact-inventory.md`).
