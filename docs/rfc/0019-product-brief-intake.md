# RFC-0019: Product-brief intake + LLD-aware spec/plan — receiving a multi-spec brief into a design-bearing spec-driven loop

- **Status:** Accepted <!-- Draft | Open | Final Comment Period | Accepted | Rejected | Withdrawn | Experimental -->
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-06-01
- **Date closed:** 2026-06-01
- **Related:** RFC-0017 (pluggable API contract standards — many specs reference one contract by reference; the linkage precedent); RFC-0020 (reference-architecture foundation — the LLD reads `reference.md` when present, Decision 9); RFC-0021 (greenfield inception — produces the first brief and feeds this loop); `docs/CONVENTIONS.md` §"document hierarchy" (the doc-altitude diagram this RFC amends) and §4 (Specs and Plans); `docs/CHARTER.md` §Principles (the four bars a core addition must clear); the `new-spec` and `work-loop` skills (core pack).

## The ask

- **Recommendation (BLUF):** Add a product **brief** artifact to the core pack at `docs/product/briefs/<slug>.md`, plus a `receive-brief` skill that ingests a product brief (PRD-style) — **eliciting missing inputs rather than mandating a schema** — decomposes it into engineering specs, and **executes each slice through the existing `new-spec` → `work-loop` pipeline**. The brief carries the *what/why* and a coverage map whose status is **auto-derived from its child specs**. In the same change, enrich the **spec/plan templates** to carry a **low-level design (LLD)** — a `## Design (LLD)` section in `plan.md` built from **stack-neutral** categories, **shape-selected** per spec, and filled with stack-specific content the agent **derives** from the brief-intake or the established repo (never baked into the template). The spec stays the contract; the design lives in the plan.

- **Why now (SCQA):**
  - *Situation.* Core gives adopters spec-driven delivery: `new-spec` writes one feature contract, `work-loop` builds it. One spec = one feature, "sized to be built in days or weeks" (`CONVENTIONS.md:215`).
  - *Complication.* Enterprise adopters don't author all their own work — they **receive** an externally-authored product brief (a PRD, a solution handoff) that spans several features. Core's only work-intake is single-feature `new-spec`, and it lacks the RFC skill (which lives in governance-extras) — so the product→engineering handoff has no home. The adopter either crams a multi-feature brief into one oversized spec (breaking the sizing rule and the per-spec `work-loop`) or fires `new-spec` N times by hand with nothing recording the why, the decomposition, or coverage.
  - *Question.* How does a single-repo, spec-driven toolchain **receive** a multi-feature brief and route it into delivery without losing the why, the decomposition, or the coverage the handoff demands — and carry the **low-level design** an enterprise build needs, without baking any one tech stack into a universal template?

- **Decisions requested:**
  1. **Scope** — own-the-repo-slice only (no cross-repo coordination hub); the brief may carry an optional `Epic:` pointer to an external coordinator. *Recommended; default if no objection.* Decide-by 2026-06-11.
  2. **Carrier** — a new `brief` artifact (not an extension of roadmap/backlog or the spec). *Recommended.* Decide-by 2026-06-11.
  3. **Pack** — ship in **core** (not governance-extras, not a new product pack). *Recommended; most contested — see Options.* Decide-by 2026-06-11.
  4. **Input posture** — elicit missing inputs against a recommended shape + ship an example references file; do not mandate a schema. *Recommended.* Decide-by 2026-06-11.
  5. **User stories** — optional; when present, traced to acceptance criteria via a `Satisfies: US-n` marker. *Recommended.* Decide-by 2026-06-11.
  6. **Linkage** — specs reference their brief via a new `Brief:` field (no nesting); this decision covers the `Brief:` / `Satisfies:` / `Epic:` field set. *Recommended.* Decide-by 2026-06-11.
  7. **Coverage tracking** — the brief's status is **auto-rolled-up** from child specs by a lint, not hand-maintained. *Recommended.* Decide-by 2026-06-11.
  8. **LLD locus** — enrich `plan.md` with a stack-neutral `## Design (LLD)` section (and light `spec.md` touches: a `Shape:` field + AC phrasing for states/NFRs); reuse the existing `Rollout`/`Risks`/`Depends on:` rather than adding tiers. *Recommended.* Decide-by 2026-06-11.
  9. **Stack source** — the LLD's stack-specific content is **derived**: read `docs/architecture/reference.md` (RFC-0020) and conform to it **when present**; otherwise derive from brief-intake context and/or established-repo detection, eliciting gaps. The template ships only universal categories. *Recommended.* Decide-by 2026-06-11.

## Problem & goals

A product brief and an engineering spec are different artifacts owned by different roles. The prior art is explicit: *"the product manager owns the PRD,"* which covers *"what to build"* and *"user experience"*, while *"the engineering lead or tech lead"* writes the spec, which covers *"how the team will implement the requirements"* — architecture, data models, API contracts ([PRD vs Product Brief vs Spec](https://www.ideaplan.io/compare/prd-vs-product-brief-vs-product-spec)). **Core jumps straight to the engineering spec.** There is no inbox for the thing product hands engineering.

This is not cosmetic. `CONVENTIONS.md:215` sizes a spec at *one feature, days-to-weeks*, and `work-loop` runs *per spec*. A multi-feature brief is months of work across features — it provably **cannot** be one spec without breaking both. So any multi-feature input structurally forces a layer *above* the spec, and core ships none. The gap shows up precisely where an organization separates the product and engineering functions — i.e. in the enterprise.

### Goals

- Receive a product brief that spans multiple specs, and record its *what/why* (problem, outcome, success metrics, scope) as a durable handoff artifact.
- **Elicit** the brief's missing inputs conversationally rather than rejecting input that doesn't match a fixed schema.
- **Decompose** the brief into independently-shippable, feature-sized specs and **execute** each through the existing `new-spec` → `work-loop` pipeline.
- Maintain a **coverage map** (brief → spec → status) so "is this brief delivered?" is answerable — and keep it current **automatically**, derived from child-spec status.
- Support **optional** user-story traceability (brief story → spec acceptance criteria) without forcing it.
- Own only **this repo's slice**; point upward to an external coordinator when the brief is part of a cross-repo epic.
- Give the engineering build a **low-level design** home in the plan, built from stack-neutral categories and filled with stack-specific content the agent **derives** — so an enterprise LLD fits without baking a stack into a universal template.

### Non-goals

- **A cross-repo coordination hub.** Coordinating an epic across repos is a tracker's job (Jira, GitHub Projects, an integration repo). We integrate with it via an optional pointer; we do not become it.
- **A new "user story" artifact tier.** Acceptance criteria already are the testable user-story unit; we add a trace marker, not a directory or object.
- **A portfolio/initiative layer above the brief.** One received brief is the ceiling of this RFC; multi-brief portfolio rollup is out of scope.
- **Mandating a brief schema.** The shape is a guide, not a gate (see Decision 4).
- **Replacing roadmap or backlog.** The brief slots between them; both keep their jobs.
- **Baking any tech stack into the templates.** The `## Design (LLD)` categories are stack-neutral; React/TanStack/Kafka/Spring etc. appear only in the *derived, filled instance*, never in the shipped template (Principle 1).
- **Moving design above the spec.** The brief carries *what/why*; the per-spec LLD stays in `plan.md`. The spec gains only a light shape-selector and AC guidance — **no LLD body** migrates into it; it remains the contract.
- **A separate `design.md` tier.** The plan is the design home; we add a section, not an artifact.
- **Reshaping the spec lifecycle into delta-expressed / always-living specs.** OpenSpec's delta specs (ADDED/MODIFIED/REMOVED merged into a source-of-truth) and Intent's living-specs were considered and **deferred**: they would change `spec.md`'s shape for every adopter, partly duplicate the existing "living-during-build / drift-is-a-bug" model, and "always living" conflicts with the deliberate "frozen after ship" stance. Delta-expression, if pursued, is its own future RFC — not a rider here.

## Proposal

### The brief artifact (Decisions 2, 3)

A brief lives at `docs/product/briefs/<slug>.md` — inside core's existing product surface (`packs/core/seeds/docs/product/` already ships `roadmap.md` and `changelog.md`). It carries:

- **Outcome** — the problem and the user-facing outcome (the load-bearing field).
- **Success metrics**, **scope / non-goals**, **appetite** (a constraint, not an estimate — *"we want to … do it in six weeks, not three months"* ([Shape Up](https://basecamp.com/shapeup/1.5-chapter-06))).
- **User stories** — *optional* (Decision 5).
- **`Epic:`** — *optional* pointer to an external coordinator's id, carried in from the brief when this repo's work is one slice of a cross-repo epic (Decision 1).
- **Spec map** — the coverage table (`spec → status`, plus a `story` column in the story-list shape), **auto-derived** (Decision 7).

The brief sits between two artifacts core already has. The repo's canonical document hierarchy (`CONVENTIONS.md:~24–65`) already places `product/` (roadmap + changelog) as the "external current state" bucket; this RFC adds `briefs/` under that bucket and amends the diagram accordingly. The altitude mirrors the product hierarchy where an *Initiative* is a *"measurable outcome … [that] appears on roadmap"* and the bodies of work that serve it *"appear in backlog"* ([Initiative vs Epic vs Story](https://roadmap.one/blog/posts/blog26-initiative-epic-story/)):

```
roadmap          forward-looking themes        ──references──►  briefs
  └─ BRIEF        received outcome + spec map   ◄── NEW; backlog rolls up to it
       └─ spec    engineering contract (how)    (role unchanged; +Shape: field, see LLD)
            └─ AC  the testable user-story unit
```

### Two shapes, one toggle (Decision 5)

The user-story section is the only toggle; it changes traceability granularity, not the pipeline.

- **Shape A — no stories.** The agent derives spec boundaries from outcome + scope and surfaces the cut for confirmation. Coverage is **spec-granular**. Stories still exist — they're written as the spec's ACs at authoring time.
- **Shape B — story list.** Stories carry ids (`US-n`); decomposition is *grouping stories into specs*; each satisfying AC carries `Satisfies: US-n`. Coverage is **story-granular**: "US-2 → `password-reset` AC3 → shipped." A story too big to fit one spec is an epic — split it.

### Linkage (Decision 6)

A derived spec references its brief through a new `Brief:` field in the spec front-matter (sibling to the existing `Constrained by:` and `Contract:` fields in `new-spec`'s `spec.md`). Reference, not nesting: specs stay flat under `docs/specs/<feature>/`, a spec can predate its brief, and this mirrors how RFC-0017 already lets many specs reference one contract over time. `Constrained by:` is reserved for governance constraints (ADR/RFC); `Brief:` records product provenance — distinct semantics, distinct field. The same decision settles the two companion markers: `Satisfies: US-n` on ACs (Decision 5) and the optional `Epic:` field on the brief (Decision 1).

### The skill and the execution spine

`receive-brief` (core skill):

1. **Elicit.** Ingest whatever the adopter has (a pasted PRD, a doc, a link, or nothing). Elicit the load-bearing fields (outcome, scope) conversationally; offer the rest. Never reject for non-conformance (Decision 4).
2. **Decompose.** Cut the brief into independently-shippable, independently-testable feature slices (the shippability test, not a component/layer split). In Shape B, this is grouping stories; flag any uncovered outcome as a gap and any epic-sized story for splitting.
3. **Execute.** For each slice, chain `new-spec` to scaffold `spec.md` + `plan.md`, stamp the `Brief:` back-link (and `Satisfies:` on ACs in Shape B), then hand off to `work-loop`. The brief is thus **executable**: `brief → (spec, plan) × N → work-loop`.

### Auto-rolled-up coverage (Decision 7)

A lint reads every `docs/specs/*/spec.md` `Status:` field, follows the `Brief:` back-links, and rolls each brief's spec-map status up from its children — so the brief stays a live tracker with no hand-maintenance, and a brief whose every spec is Shipped reports *delivered* on its own. This is the "operating document tied to execution" that modern PRDs aim for, made mechanical. Placement of the lint (build-check vs CI-only/advisory) is Open question 1.

### Example references file (Decision 4)

The skill ships `examples/` with a worked brief in **both** shapes (a no-stories outcome brief and a story-list brief), showing the expected fields and a populated spec map. It is a guide that demonstrates the shape — never a schema the skill enforces.

### LLD enrichment of spec/plan (Decisions 8, 9)

An enterprise build needs a low-level design — for UI: screen states, component decomposition, state management, navigation, accessibility; for backend: data model, sequence, resilience, security, deployment sequencing. These abstract to **ten stack-neutral categories**: design decisions; data & schema; interfaces & contracts; component/module decomposition; state & control flow; behavior & rules; failure, edge cases & resilience; quality attributes (NFRs); dependencies & integration; rollout & deployment. The category *names* are universal; *which* are heavy and *how* they are filled is stack-specific.

The enrichment keeps the spec as the contract and puts the design in the plan:

- **`spec.md` (light).** Add a stack-neutral **`Shape:`** field (`ui | service | data | integration | mixed`) that selects which plan sub-sections scaffold; extend AC guidance so a UI **state/trigger/outcome** lands as an acceptance criterion and an NFR with a pass/fail bar (e.g. WCAG-AA, p99) is an AC; minor `Contract:` / `Testing Strategy` wording so events/BFF and integration/E2E are first-class. The spec grows no LLD body.
- **`plan.md` (the LLD home).** Add a **`## Design (LLD)`** section before `## Tasks`, built from the ten categories as **optional, shape-selected** sub-headings, each tracing to the AC(s) it satisfies and the `contracts/` it implements. **Expand the existing `## Rollout`** to cover infra, external-system integration, and deployment sequencing (the one dimension with no home today). Dependencies reuse `Depends on:` / `Touches:`; testing reuses `Construction tests` + the spec's `Testing Strategy`. Net new surface: one section added, one expanded.

**Stack derivation.** `new-spec` (and `receive-brief` when it scaffolds specs) derives the **shape** (from the brief or by asking) and the **stack**. For the stack it **first reads `docs/architecture/reference.md` (RFC-0020) when present** and conforms the LLD to that foundation (referencing its components/stereotypes/standards by name); when absent it **degrades** — detecting the established repo's lockfiles/build files/imports and/or the brief-intake context, eliciting gaps (a one-line nudge may suggest establishing a foundation). The check is the seam that lets RFC-0019 and RFC-0020 land in either order: 0019 ships standalone via the degrade path, and the day a `reference.md` exists the LLD conforms to it automatically. The template ships only the categories; the stack lives in the filled instance.

**Minimal by default.** The Design section is optional and shape-pruned; a one-file change keeps a thin plan. The enrichment is **additive** — no existing spec/plan section is removed or renamed — so specs and plans authored before this change stay valid.

## Options considered

Each requested decision's option space is modelled below, MECE along a stated axis. A do-nothing-equivalent row appears where the axis admits it (Decisions 1, 4, 7, 8); the global do-nothing is at the end of this section (Decisions 2, 3, 6, 9 presuppose the brief/LLD exists, so their axes don't carry a separate do-nothing).

### Decision 1 — Scope — *axis: how much cross-repo coordination the toolchain owns*

| Option | What | Trade-off |
| --- | --- | --- |
| **Own-the-repo-slice** ★ | Ingest this repo's portion; point upward via optional `Epic:` | Honest about the single-repo install boundary; relies on an external hub the adopter already has |
| Build-a-hub | Ship cross-repo coordination ourselves | Duplicates Jira / GitHub Projects; breaks the single-repo model; near-certain charter violation |
| Do-nothing | Adopter coordinates by hand | Zero build cost; the gap persists |

Every cross-repo system places the coordinator *above* the repos and threads a shared id into per-repo work — Gerrit *topics* ([Gerrit](https://gerrit-review.googlesource.com/Documentation/cross-repository-changes.html)) and GitHub change-set ids ([GitHub polyrepo](https://wellarchitected.github.com/library/architecture/recommendations/implementing-polyrepo-engineering/)). Own-the-slice is that pattern's repo end.

### Decision 2 — Carrier — *axis: which artifact holds the received brief*

| Option | Trade-off |
| --- | --- |
| **New `brief` artifact** ★ | One small artifact; holds PRD prose + coverage map + delivered lifecycle that nothing else can |
| Extend `roadmap.md` / `backlog.md` | Reuses a file, but roadmap is a flat forward list ("Not commitments") and backlog is open-items-only by spec — neither holds the why or a closed→delivered map |
| Absorb into the spec | No new artifact, but a spec is single-feature (`CONVENTIONS.md:215`) — it cannot carry a multi-feature brief |

### Decision 3 — Pack — *axis: which pack ships it* (most contested)

| Option | Trade-off |
| --- | --- |
| **core** ★ | The handoff is stack-agnostic (Principle 1); reuses core's existing product surface; cost = core grows past "just specs" |
| governance-extras | Natural neighbour to RFC/ADR — **but adopters install core *without* it, which recreates the exact gap this RFC closes**; and a brief is *work-intake* (like `new-spec`), not rule-change governance |
| new `product` pack | Clean separation — but a whole pack for one artifact + one skill is heavier than core-growth, and it fragments the product surface core already ships |

The `jira-defect-flow` intake precedent lives in the *non-core* `atlassian` pack, which might look like an argument against core. It isn't: that skill is Jira-specific and so fails Principle 1 (Universal) for core. Brief-intake is stack-agnostic, so the constraint that pushed `jira-defect-flow` out of core does not apply here.

### Decision 4 — Input posture — *axis: input rigidity*

| Option | Trade-off |
| --- | --- |
| Mandate a fixed schema | Consistent input, but rejects real-world briefs that arrive half-formed; contradicts the "elicit" intent |
| **Elicit + example refs** ★ | Meets adopters where they are; the example shows the shape. Shape Up warns against over-specifying ([Shape Up](https://basecamp.com/shapeup/1.5-chapter-06)); PRD practice treats templates as guides |
| Freeform, no shape | Lowest friction, but no shared shape for the agent to decompose against |

### Decision 5 — User stories — *axis: story requirement*

| Option | Trade-off |
| --- | --- |
| Require stories | Forces a `## User stories` section; contradicts Shape Up's caution against over-specifying |
| **Optional + `Satisfies:` trace** ★ | Both shapes work from one toggle; story-granular coverage when product provides stories, spec-granular when it doesn't |
| Ban stories | Loses the finest-grain traceability the enterprise handoff asks for |

### Decision 6 — Linkage — *axis: coupling between brief and spec*

| Option | Trade-off |
| --- | --- |
| **Reference via `Brief:` field** ★ | Specs stay flat; a spec can predate its brief; mirrors RFC-0017's many-specs-one-contract reference |
| Nest specs under the brief dir | Changes `new-spec`'s flat `docs/specs/<feature>/` path; couples a spec to exactly one brief |

### Decision 7 — Coverage tracking — *axis: how brief status is kept current*

| Option | Trade-off |
| --- | --- |
| Hand-maintained spec map | No new tooling, but drifts the moment a spec ships and nobody edits the brief |
| **Auto-rollup lint** ★ | Live tracker, zero hand-maintenance, reads only existing `Status:` fields; cost = one new lint to maintain |
| No tracking | Cheapest, but "is this brief delivered?" becomes unanswerable — defeats the handoff |

### Decision 8 — LLD locus — *axis: where the design lives*

| Option | Trade-off |
| --- | --- |
| **Enrich `plan.md` (+ light spec)** ★ | Plan is already the design step (Kiro's "Design", spec-kit's "Plan"); additive section, no new tier; reuses Rollout/Depends-on |
| Separate `design.md` in the spec dir | Cleaner for heavyweight, separately-reviewed LLD — but a new per-spec artifact and review gate for every adopter |
| Put LLD in the spec | Single doc, but conflates contract with design and bloats the spec a single-feature contract is meant to stay |
| Do-nothing (no LLD) | Plan stays thin — but the enterprise design has nowhere to live; deployment sequencing remains homeless |

### Decision 9 — Stack source — *axis: how stack-specific content enters the LLD*

| Option | Trade-off |
| --- | --- |
| **Derive (brief-intake + repo detection), elicit as fallback** ★ | Template stays universal (Principle 1); content matches the real codebase; degrades to a question when detection is ambiguous |
| Adopter hard-codes a stack template | Precise for one org, but every adopter must author a template, and core can't ship a universal default |
| Bake a stack into the shipped template | Zero setup for that stack — but violates universality and rots for everyone else |

**Do-nothing** (across all axes) keeps core lean but leaves the structural gap: the most common enterprise scenario — "an architect handed us a design, now build it" — has no supported path, and the build that follows has no place to record its design.

## Risks & what would make this wrong

- **Pre-mortem.**
  - *The brief becomes ceremony adopters skip.* Mitigation: the skill earns its place by *executing* (brief → specs → work-loop) and *auto-tracking* coverage — value beyond the document.
  - *Elicit-not-mandate yields briefs too thin to decompose.* Mitigation: the skill insists only on the load-bearing fields (outcome, scope) and surfaces gaps; everything else is offered, not required.
  - *The auto-rollup lint is noisy or brittle.* Mitigation: it reads only existing `Status:` fields via `Brief:` back-links — no new state; if a back-link is missing the brief simply shows that spec as untracked.
  - *The layer duplicates roadmap.* Mitigation: roadmap *references* briefs and backlog *rolls up to* them; the brief is the only artifact holding the why + coverage.
  - *The `## Design (LLD)` section bloats every plan, including trivial ones.* Mitigation: the section is optional and shape-pruned; the small-change path keeps a thin plan, per the existing right-size-to-stakes ethos.
  - *Stack derivation guesses wrong (ambiguous or greenfield repo).* Mitigation: detection degrades to elicitation — the agent asks rather than inventing a stack; the brief-intake context is a second signal.
  - *Touching `spec.md`/`plan.md` breaks existing specs/plans.* Mitigation: every change is **additive** — a new optional field/section, nothing removed or renamed — so prior specs/plans stay valid and the self-host projection re-renders cleanly.

- **Two claims that must stay separate.** The de-risk spike establishes only that *a layer above the spec is structurally forced **if** a multi-feature brief arrives* (a multi-feature brief cannot be one spec). It does **not** establish that such briefs arrive **often enough** to earn a core primitive. The first is settled; the second is the open product call below. Conflating them would let the "structurally forced" framing smuggle in a frequency claim it cannot support.

- **Decision 3 against the four charter principles (`CHARTER.md:58`), by name.**
  1. *Universal across tech stacks* — **clears.** The product→engineering handoff is stack-agnostic.
  2. *Substantive, not duplicative* — **clears.** No existing artifact carries a received brief + coverage map; `new-spec` is single-feature by contract.
  3. *A habit, not a tool* — **mostly clears.** The receive → decompose → execute workflow is a way of working; the auto-rollup lint is the one component that leans "tool," justified only as mechanical support for the habit (and demotable to advisory — Open question 1).
  4. *Used often enough to stick* — **the open one.** This is Assumption 1 below; the principle it must clear is frequency, not structure.

- **Key assumptions (falsifiable).**
  1. **Enough adopters receive externally-authored, multi-feature briefs to earn a *core* primitive (Principle 4).** If most adopters author their own single features, `new-spec` alone suffices and this is over-build. *Cannot be settled by a spike.* What would move the Approver: anecdotal frequency evidence — how many times has this repo (or a known adopter) actually received such a brief? If the honest answer is "rarely," ship it in a non-core pack or defer.
  2. Decomposing a brief into shippable specs is judgment the agent can do well enough to be useful, not just mechanically.
  3. Auto-rolling status up from child-spec `Status:` fields is reliable enough to trust as a coverage answer.
  4. The ten LLD categories are genuinely stack-neutral — they hold a UI feature, a backend service, a data pipeline, and an integration without privileging any stack. If a real LLD has a dimension none of the ten captures, the abstraction is wrong.
  5. The agent can derive shape and stack reliably enough that the filled LLD is useful more often than it misleads.
- **Drawbacks.** One more artifact and one more skill to maintain; a new lint in the gate set; core grows past "just specs." **Changing `spec.md`/`plan.md` is the widest blast radius here** — those templates are the contract for *every* adopter and the self-host projection, so even an additive change touches everyone; the mitigation (additive-only) bounds but does not erase that. The bet is that the handoff and the LLD are common enough that the cost is repaid.

## Evidence & prior art

- **Spike / de-risk result (brief layer).** *Riskiest assumption:* that the brief layer is needed at all and isn't just a spec with more ACs. *Check (against the convention):* `CONVENTIONS.md:215` sizes a spec at days-to-weeks/one feature and `work-loop` runs per spec; a multi-feature brief is months across features, so it cannot be one spec without breaking both — **the layer is structurally forced (conditional on such a brief arriving), independent of frequency.** Holds, with the frequency caveat kept separate (Risks).
- **Spike / de-risk result (LLD categories — Assumption 4).** *Check:* the ten stack-neutral categories were validated against two real enterprise LLDs supplied during drafting — a UI per-screen LLD (design decisions, screen states, component hierarchy, server/local/form state, client validation, BFF contract, routing, accessibility, responsive, error/edge, observability, testing, MFE deps, deployment impact) and a backend LLD (component stereotype, business workflow + rules, internal framework, data model, API contracts, Kafka events, sequence, resilience, security, observability, testing, external deps, infra + deployment sequencing). **Every item mapped to one of the ten categories; the only dimension with no prior home was deployment sequencing, now covered by the expanded `## Rollout`.** Holds. The remaining risk is derivation reliability (Assumption 5), accepted on judgment.
- **Repo precedent.** `CONVENTIONS.md:215` (spec = single feature); the document-hierarchy diagram at `CONVENTIONS.md:~24–65` (assigns every doc to one bucket and already shows `product/` holding roadmap + changelog — the bucket `briefs/` joins, and the diagram this RFC amends); `new-spec`'s `spec.md` (`Constrained by:` / `Contract:` fields — the back-link pattern `Brief:` extends); `packs/core/seeds/docs/product/roadmap.md` (items "link to a spec"; substantive additions go through RFC); `docs/backlog.md` ("open items by spec"); RFC-0017 (many specs reference one contract by reference — the linkage precedent the brief lifts into an adopter-facing artifact); `packs/atlassian/.apm/skills/jira-defect-flow` ("Stage 1 — Intake" precedent, in a non-core pack — see Decision 3). No existing brief/intake/PRD skill in any pack.
- **External prior art.** Product/engineering ownership split — [PRD vs Product Brief vs Spec](https://www.ideaplan.io/compare/prd-vs-product-brief-vs-product-spec); appetite-as-constraint and don't-over-specify — [Shape Up ch.6](https://basecamp.com/shapeup/1.5-chapter-06); the outcome-that-appears-on-roadmap / body-of-work-in-backlog hierarchy — [Initiative vs Epic vs Story](https://roadmap.one/blog/posts/blog26-initiative-epic-story/); cross-repo coordination via a hub-above-repos + shared id — [Gerrit topics](https://gerrit-review.googlesource.com/Documentation/cross-repository-changes.html), [GitHub polyrepo](https://wellarchitected.github.com/library/architecture/recommendations/implementing-polyrepo-engineering/). Spec-driven corroboration of the brief/spec/coverage shape — [OpenSpec](https://github.com/Fission-AI/OpenSpec) (proposal-first + *delta specs* marking ADDED/MODIFIED/REMOVED, confirmed against its concepts doc) and Intent (Augment Code) *living specs* (the spec reflects what was actually built — the auto-rollup posture of Decision 7).

## Open questions

1. **Auto-rollup lint placement** — in `make build-check` (fails fast, local) vs CI-only/advisory (lighter local gate). *Recommended default:* CI-only/advisory, not in the local gate, to keep `build-check` fast; promote to build-check only if coverage drift proves common. (No backlog-style precedent is claimed — the repo has no purpose-built coverage lint today.) Owner: eugenelim · decide-by 2026-06-18.
2. **Skill name** — `receive-brief` vs `new-brief`. *Recommended default:* `receive-brief` (the verb is *receive/decompose*, distinct from `new-spec`'s *author*). Owner: eugenelim · decide-by 2026-06-18.
3. **Whether `examples/` ships one shape or both** — *Recommended default:* both (a no-stories brief and a story-list brief), since the two-shape behavior is the load-bearing nuance. Owner: eugenelim · decide-by 2026-06-18.

## Follow-on artifacts

Filled in on acceptance:

- ADR-NNNN: record the brief-layer decision (new artifact altitude between roadmap and spec; own-the-slice boundary) and the LLD-locus decision (design lives in the plan; stack is derived, not baked).
- Spec: `docs/specs/product-brief-intake/` — the `brief` template, the `receive-brief` skill, the `Brief:` / `Satisfies:` / `Epic:` fields, the example references file, and the auto-rollup lint.
- Spec: `docs/specs/lld-aware-spec-plan/` — the `spec.md` `Shape:` field + AC guidance, the `plan.md` `## Design (LLD)` section + expanded `## Rollout`, and the shape/stack-derivation step in `new-spec` and `receive-brief`. (Touches the core templates — additive only.)
- Convention change: `docs/CONVENTIONS.md` — amend the document-hierarchy diagram to add `briefs/` under `product/`; document the `roadmap → brief → spec → AC` altitude and the `Brief:` field on specs; document the spec/plan LLD enrichment (the `Shape:` field, the `## Design (LLD)` categories, stack-derivation) in §4 (Specs and Plans).
- **User guides (in *this* catalogue repo, `docs/guides/`, authored via `new-guide`)** — the implementing spec/plan plans and writes them as part of "done", so the new capabilities ship documented for adopters:
  - *How-to* — "Receive a product brief and decompose it into specs" (the `receive-brief` flow, end to end).
  - *Reference* — the `brief` artifact fields (incl. `Epic:`, the spec map) and the spec/plan additions (`Brief:`, `Shape:`, the `## Design (LLD)` categories).
  - *Explanation* — "Why a brief layer": the `roadmap → brief → spec → AC` altitude and the product→engineering handoff this closes.
