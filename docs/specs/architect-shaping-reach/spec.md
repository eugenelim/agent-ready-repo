# Spec: Architect output reaches shaping and specs

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

Teams that install the `architect` pack next to `product-engineering` and `core` get architecture work that flows into shaping, specs, and closeout: framing offers a design at the right scope, brownfield grounding reuses or produces a current-state model, a design reaches the spec through the delivery contract, and a shipped design can be reconciled into current architecture. Teams without `architect` see no change at all: no mention, no note, and no error.

## What Changes

- `architect-design` step 2 checks for a reference architecture, states what it found in the concept, and offers to establish one by routing to Core's `adapt-to-project` or `init-project` when available — `packs/architect/.apm/skills/architect-design/SKILL.md`.
- `architect-design` step 8 says a saved design is future-state and is reconciled into current architecture after the change ships — same file.
- `architect` declares an optional Core handoff for establishing a reference architecture — `packs/architect/pack.toml`.
- `DESIGN.md` § Reference architecture and § Downstream: core describe the real routes — `packs/architect/DESIGN.md`.
- `frame-domain`'s brownfield half reuses a current-architecture artifact, or offers `architect-assess` when installed, before its own extraction — `packs/product-engineering/.apm/skills/frame-domain/SKILL.md`.
- `frame-intent` parks system-shape questions as open design questions and offers `architect-design` at a named scope when installed — `frame-intent/SKILL.md`, `frame-intent/references/knowledge-surfaces.md`.
- `de-risk-intent` grounds a feasibility assumption against current architecture, and offers `architect-assess` when installed and none exists — `de-risk-intent/SKILL.md`.
- `explore-options` and `diverge-solutions` record each candidate's feasibility against current architecture when one is reachable — `explore-options/SKILL.md`, `diverge-solutions/SKILL.md`.
- `decompose-intent` checks slices against subsystem boundaries, offers `architect-design` for a structural decomposition when installed, and carries a resolved design in the delivery contract's design context — `decompose-intent/SKILL.md`.
- `map-capabilities` offers `architect-design` for the Build capabilities when installed — `map-capabilities/SKILL.md`.
- `product-engineering` declares two optional `architect` integrations whose fallback is silent — `packs/product-engineering/pack.toml`.
- `close-work` step 4 offers to reconcile an implemented future-state design into the current-architecture surface, without naming any pack — `packs/core/.apm/skills/close-work/SKILL.md`.
- Behavior evals cover the installed and not-installed paths; pack tests pin the offers and the silence.
- `core` 3.0.3, `architect` 0.15.16, and `product-engineering` 0.13.25 with changelog entries; projections regenerated.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture of the packs | Architect's documented downstream routes change. | `packs/architect/DESIGN.md` § Reference architecture, § Downstream: core | Architect pack maintainers | AC-0002, AC-0004 tests | Both sections describe only routes that exist. |
| Decision rationale | Gap 2 is closed by product-engineering wiring plus a DESIGN.md correction, not by a Core `new-spec` change. | This spec § Decisions; the Core-side reason also in `packs/architect/DESIGN.md` § Downstream: core | eugenelim | Section present; AC-0004 | A reader finds the choice and reason here. |
| User promise | Adopters read what each pack offers when the other is installed. | `packs/architect/README.md`, `packs/product-engineering/README.md`, `packs/core/README.md` § close-work paragraph | Pack maintainers | README sentences (AC-0014) | Each README states its new behaviour. |
| Release history | Non-cosmetic content changes in three packs. | `docs/product/changelog.md` | Pack release maintainer | Three dated entries with Highlights | Entries present and outcome-led. |

## Decisions

- **Gap 1 — fixed in `architect-design`.** It never drafts a reference architecture itself. Core's `adapt-to-project` (existing code) and `init-project` (new project) already own harvesting, resolution, and confirmation, so the design skill routes there when it can and otherwise states the absence.
- **Gap 2 — wired through `product-engineering`, and `DESIGN.md` corrected; no Core `new-spec` change.** `new-spec` already treats a delivery contract's design context as attributed context, so the missing link was that nothing put the design there. `decompose-intent` now does when a resolved design exists. The only other route a Core reader consumes is reconciliation: once the design is folded into the `current-architecture` source and an `AGENTS.md` maps that source, `new-spec` and `work-loop` read it. A `workspace.toml` `needs` entry only orders work — it keeps a spec blocked until the design lands — and carries no content. `work-loop` keeps reading only mapped architecture sources; a Core change to read future-state designs would add a second architecture authority to every Core adopter.
- **Gap 4 — the longer route.** Its architect offer sits at `map-capabilities`, where Build capabilities first exist. `diverge-solutions` gains the same feasibility note as `explore-options`; it offers no architect skill, because its options must stay comparable bets rather than designs.
- **Gap 5 — generic step in `close-work`.** It uses only the Core semantic roles `architecture-design` and `current-architecture`, so it works for any producer and never names a pack.
- **Detection.** A product-engineering skill detects an architect skill by checking its available-skills roster, the primitive `frame-domain` and `discovery-loop` already use. Unlike `desk-research`, an absent architect is not a grounding gap, so nothing records it.

## Agent Rules

### Always do

- Edit `.apm/` sources only, then run `make build-self`.
- Phrase every architect offer in a product-engineering skill as conditional on the roster check, followed by the silent clause quoted in AC-0011.
- Keep Outcome and Opportunity solution-independent: a system-shape question never enters either field.

### Ask first

- Adding an architect offer to a product-engineering skill not named in this spec.
- Changing `new-spec`, `work-loop`, or `author-delivery-brief`.

### Never do

- Name `architect`, any `architect-*` skill, or the Architect pack in a shipped Core file this change edits.
- Add a `[pack.dependencies]` entry between these packs, or tell the user to install `architect`.
- Record, mention, or warn about architect's absence in any product-engineering artifact or reply.
- Let `architect-design` draft or write a reference architecture itself.
- Edit `guides/_shared/explanation/the-operating-model.md`, its two SVGs, `tools/render-lifecycle-graphics.py`, `docs/architecture/lifecycle-flow.md`, or `docs/design/screens/guides-lifecycle-ia.md`.

## Testing Strategy

- **Skill prose (AC-0001 – AC-0012):** goal-based. Pack tests read each `.apm/` source, collapse whitespace, and assert the required phrases case-sensitively; prose has no runtime to drive. Each pack's tests read only that pack.
- **Silent degradation (AC-0011):** goal-based plus a mutation. The test asserts the silent clause follows each roster check and that no product-engineering skill contains an install-architect or architect-absent phrase. A mutation run adds a forbidden phrase and proves the test fails.
- **Behavior evals (AC-0013):** goal-based. The existing eval-shape tests plus a pack test for the not-installed case ids and their assertions.
- **Release and projection (AC-0014, AC-0015):** goal-based commands: version parity, changelog headings, `catalogue verify`, and a clean self-host.

## Acceptance Criteria

- [x] **AC-0001.** `architect-design/SKILL.md` step 2 contains a reference-architecture check that, after collapsing whitespace, contains each of: "reference architecture", "State what you found", "`adapt-to-project`", "`init-project`", "available-skills roster", and "Never draft". It routes to `adapt-to-project` for existing code and `init-project` for a new project, and when neither is available it states the absence in the concept and continues.
- [x] **AC-0002.** `packs/architect/DESIGN.md` § Reference architecture names `adapt-to-project` and `init-project` as the producers `architect-design` routes to, and no longer says `architect-design` establishes the artifact at a destination itself.
- [x] **AC-0003.** `packs/architect/pack.toml` has an integration with `id = "core-reference-architecture-handoff"`, `pack = "core"`, `kind = "handoff"`, consumers `["skill:architect-design"]`, and providers `["skill:adapt-to-project", "skill:init-project"]`, whose fallback says the absence is stated in the concept.
- [x] **AC-0004.** `packs/architect/DESIGN.md` § Downstream: core does not contain "reads it to orient". It names exactly two routes by which a design reaches a spec or `work-loop`: `decompose-intent`'s delivery-contract design context, and reconciliation into `current-architecture` read when an `AGENTS.md` maps that source. It says a `workspace.toml` `needs` entry only orders work, and it records why Core does not read future-state designs.
- [x] **AC-0005.** `architect-design/SKILL.md` step 8 states that a saved `architecture-design` is future-state and, after the change ships, is reconciled into `current-architecture` rather than read as current.
- [x] **AC-0006.** `frame-domain/SKILL.md`'s brownfield section, after collapsing whitespace, contains "current-architecture", "`architect-assess`", and "available-skills roster": it reuses a reachable current-architecture artifact first, offers `architect-assess` only when it is in the roster, and otherwise runs its own extraction. Its detect-and-degrade section says an absent `architect-assess` is not named in the artifact.
- [x] **AC-0007.** `frame-intent/SKILL.md` has a section on system-shape questions that parks the question as an open design question outside Outcome and Opportunity and, when `architect-design` is in the roster, offers it at one of the three scopes `application/system`, `subsystem`, or `architecture change`. `frame-intent/references/knowledge-surfaces.md` no longer contains "hand it to the architect lens" and points to that section.
- [x] **AC-0008.** `de-risk-intent/SKILL.md` grounds a feasibility assumption against a reachable current-architecture artifact, and offers `architect-assess` only when it is in the roster and no such artifact exists.
- [x] **AC-0009.** `explore-options/SKILL.md`'s candidate slot carries an optional `feasibility` field filled from a reachable current-architecture artifact, and `diverge-solutions/SKILL.md` gives each option the same optional feasibility note in step 3 and an optional Feasibility field in step 5's Options entry. Neither skill names an architect skill.
- [x] **AC-0010.** `decompose-intent/SKILL.md` checks children against subsystem boundaries from a reachable current-architecture or architecture-design artifact inside step 1, while still cutting by shippability, without renumbering any step; offers `architect-design` only when it is in the roster; and its step 3, "Project the confirmed delivery unit", carries a resolved `architecture-design` locator in the delivery contract's design context, or in a delivery brief's design artifacts. `map-capabilities/SKILL.md` offers `architect-design` for Build capabilities only when it is in the roster.
- [x] **AC-0011.** Every architect offer in `frame-domain`, `frame-intent`, `de-risk-intent`, `decompose-intent`, and `map-capabilities` is followed in the same paragraph by this sentence, compared after collapsing whitespace: "If it is not in the roster, continue with this skill's own behaviour and say nothing about it: no mention, no note, and no error." No file under `packs/product-engineering/.apm/` contains, case-insensitively, "install architect", "install the architect", or "architect is not installed". `packs/product-engineering/pack.toml` declares no dependency on `architect`, and declares integrations with `pack = "architect"` for `skill:architect-design` and `skill:architect-assess` whose fallbacks contain "say nothing about it". The test fails when a mutation drops the clause from one offer.
- [x] **AC-0012.** `close-work/SKILL.md` step 4, after collapsing whitespace, contains "offer to reconcile it into the resolved `current-architecture` surface", "Apply it only under step 7's confirmation", and "never overwrite a current-architecture source without per-file acceptance", and names `architecture-design`. No line of `close-work/SKILL.md`, `close-work/evals/evals.json`, or `packs/core/README.md` matches the case-insensitive regex `\barchitect\b|architect-`.
- [x] **AC-0013.** Behavior evals exist with these ids: `frame-domain` `architect-installed-current-state` and `architect-absent-silent`; `frame-intent` `system-shape-question-architect-installed` and `system-shape-question-architect-absent`; `de-risk-intent` `feasibility-architect-absent-silent`; `decompose-intent` `architect-absent-silent`; `architect-design` `no-reference-architecture`; `close-work` `reconcile-implemented-design`. Each `-absent` case has an assertion containing "Does not mention".
- [x] **AC-0014.** `core` is `3.0.3`, `architect` is `0.15.16`, and `product-engineering` is `0.13.25` in both `pack.toml` and `.claude-plugin/plugin.json`. `docs/product/changelog.md` has a dated `## [core][3.0.3]`, `## [architect][0.15.16]`, and `## [product-engineering][0.13.25]` entry, each with `### Highlights`, above every older release entry. After collapsing whitespace, `packs/architect/README.md` contains "offers Core's `adapt-to-project` or `init-project`"; `packs/product-engineering/README.md` contains "When the `architect` pack is installed" and "Without it, they say nothing about it."; `packs/core/README.md` contains "reconcile an implemented future-state design into current architecture".
- [x] **AC-0015.** On the committed tree, `agentbundle catalogue verify --root .` passes and `make build-self` leaves `git status --porcelain` empty.

## Follow-ons

none

## Assumptions

- Product: the available-skills roster is the only installed check a prompt-only skill has. A host that hides an installed skill from the roster gets the silent path, which is safe.
