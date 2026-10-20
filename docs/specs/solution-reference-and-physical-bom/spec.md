# Spec: solution-reference-and-physical-bom

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
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

A team running a product across several component repos gets one path that
works end to end. A named skill writes the solution repo's shared system
reference and that repo's stated hard limits. The longer shaping route carries
on from `capability-map.md` into `intent decompose`, and every shaping skill
names the same owner for the brief. An architect who finishes a design can also
take an optional physical architecture with a bill of materials (BOM), meaning
a list of the resources the design needs. Each line names its exact SKU, tier
or container image URI, and its price is grounded in a cited source or marked
unpriced.

## What Changes

- A **solution reference mode** in `architect-design`, with its own template. It writes the system C4 view, domain boundaries, shared contracts and conformance rule for a coordinating repo that holds no app code — `packs/architect/.apm/skills/architect-design/SKILL.md`, `assets/solution-reference.md`
- The step-2 "never draft a reference architecture" rule narrowed to a single codebase, which still routes to Core's `adapt-to-project` or `init-project` — `architect-design/SKILL.md`, `packs/architect/DESIGN.md`, `packs/architect/README.md`, `packs/architect/pack.toml`
- A **physical architecture and BOM** offer after a full design converges, with a reference and a template — `architect-design/SKILL.md`, `references/physical-bom.md`, `assets/physical-architecture-bom.md`
- `align-value-stream` step 4 offers the solution reference mode — `packs/product-engineering/.apm/skills/align-value-stream/SKILL.md`, `packs/product-engineering/pack.toml`
- `align-value-stream` step 1 proposes a fixed "Hard limits" README section for the solution repo, from a new asset — `align-value-stream/SKILL.md`, `assets/hard-limits.md`
- The longer route continues into `intent decompose` from `capability-map.md`, and the capability map's next-step section names it — `intent/SKILL.md`, `intent/references/{decompose,frame}.md`, `map-capabilities/SKILL.md`, `map-capabilities/assets/capability-map-template.md`, `map-capabilities/examples/*/capability-map.md`
- One sentence naming the brief owners, used by every shaping skill that refuses to write a brief — `frame-situation`, `identify-opportunities`, `diverge-solutions`, `place-bet`, `map-capabilities` `SKILL.md`
- Evals, pinned tests, guides and release surfaces for both packs — `evals/`, `packs/*/tests/`, `guides/architect/`, `guides/product-engineering/`, `guides/core/explanation/role-journeys.md`, `docs/product/changelog.d/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Two new architect outputs and a changed shaping route | `guides/architect/how-to/establish-reference-architecture.md` (solution-repo route); new `guides/architect/how-to/get-a-physical-architecture-and-bom.md`; `guides/product-engineering/how-to/map-capabilities.md`; `guides/product-engineering/how-to/run-a-capability-across-a-value-stream.md`; `guides/product-engineering/explanation/the-intent-tree.md`; `guides/_shared/reference/detailed-operating-model.md`; `docs/architecture/lifecycle-flow.md`; `guides/core/explanation/role-journeys.md`; both pack READMEs | pack maintainer | Guide validators pass | Each guide states the shipped behaviour; no guide or doc still says the longer route ends at `map-capabilities` |
| Current product truth | Skill behaviour lives in skill text, references and assets | the skill files under What Changes | pack maintainer | Pinned tests, evals, catalogue lint | AC-0001 to AC-0011 and AC-0013 to AC-0015 checked |
| Decision rationale | Reference-architecture ownership moves for coordinating repos | `packs/architect/DESIGN.md` § Reference architecture | architect maintainer | Section names both owners and the split | No surface still says architect-design never writes any reference architecture |
| Release history | Both packs bump | `docs/product/changelog.d/` fragments via `tools/changelog.py new` | release author | Fragment validator | AC-0012 checked |

Current architecture, interface compatibility, operations and maintainer procedure do not apply: the change adds no module, API, service or maintainer workflow.

## Agent Rules

### Always do

- Keep both new architect outputs optional. The physical architecture and BOM is offered once, after convergence, or made on a direct request. The solution reference mode runs only on a direct request or an accepted offer.
- Ground every BOM price in a cited source carrying its date and region. Mark a line that has no grounded price `unpriced`, leave it out of the total, and state the count of unpriced lines.
- Identify every BOM line exactly. A `cloud resource` line names its provider SKU, service identifier and tier. A `container image` line names its registry URI. A `licence` line names the vendor product, edition and licence SKU. A `hardware` line names the vendor model or part number. Take each identifier from the design, the repository, or a cited provider, vendor or registry source.
- Use `no direct cost` only for a line whose cost another named line carries, and state that line on it.
- Save solution-reference and BOM output through `architect-design`'s existing save modes and confinement rules. Write nothing until the user confirms.
- Keep every architect offer added in product-engineering behind the available-skills roster check, followed by the silent clause the pack's offer test pins.

### Ask first

- Any change to Core skills (`adapt-to-project`, `init-project`, `author-delivery-brief`, `work-intake`).
- Renumbering the six-step shaping sequence, or adding a step to it.
- A bump level other than patch for either pack.

### Never do

- Never let the BOM state a price recalled from model memory, compute a total that includes an unpriced line, or invent an image URI or digest.
- Never let solution reference mode write a single codebase's golden path; that stays with Core's producers.
- Never add a new skill, script, module boundary or dependency for this feature.

## Testing Strategy

- **Skill text, assets, manifests and eval inventory (AC-0001 to AC-0010, AC-0013 to AC-0015): TDD.** Standard-library pytest suites read the shipped files and pin the phrases, sections, manifest entries and eval case ids each criterion names. A deleted phrase, section or case turns them red.
- **Agent behaviour: advisory.** The behaviour lives in prose the agent reads. The eval cases are frozen for a judge to score, but no run of them gates this spec. The pinned tests prove the cases exist, not that an agent passes them.
- **Trigger queries and eval shape (AC-0011): goal-based check.** A pinned test reads the queries, and `agentbundle catalogue lint --root . --deep` validates eval shape.
- **Release surfaces (AC-0012): goal-based check.** Catalogue lint and verify pass, and the changelog validator accepts both fragments.
- **Guides: goal-based check.** `tools/validate_guides.py`, `tools/check-guide-index.py` and `tools/lint-guide-titles.py` pass.

## Acceptance Criteria

- [ ] **AC-0001.** `architect-design/SKILL.md` has a `## Solution reference mode` section that states the mode is for a coordinating repo with no app code, routes a repo with app code to `adapt-to-project` or `init-project`, names `assets/solution-reference.md`, names the role `current-architecture`, and states that nothing is written before per-section confirmation.
- [ ] **AC-0002.** `assets/solution-reference.md` has these level-two headings in this order: `Scope`, `System context`, `Component landscape`, `Domain boundaries`, `Shared contracts`, `Cross-cutting standards`, `Conformance`, `Coordination constraints`, `Open questions`; the `System context` and `Component landscape` sections each contain a fenced `mermaid` block.
- [ ] **AC-0003.** Step 2 of the `architect-design` procedure names `adapt-to-project`, `init-project`, and "Never draft", and scopes that refusal with the words "single codebase"; `packs/architect/DESIGN.md` § Reference architecture names solution reference mode; the `core-reference-architecture-handoff` entry's `purpose` in `packs/architect/pack.toml` contains "single codebase".
- [ ] **AC-0004.** Procedure step 7 of `architect-design/SKILL.md` ends with a one-time offer of a physical architecture and BOM that names `references/physical-bom.md`. That reference states that a design with no deployment model gets no BOM and an offer to write the design first, and that every deployment unit in the design's deployment section maps to at least one BOM line or is listed as not costed with a reason.
- [ ] **AC-0013.** `references/physical-bom.md` states that every BOM line has a `Kind` of exactly `cloud resource`, `container image`, `licence`, or `hardware`, and names the identifier each kind takes: provider SKU, service identifier and tier; registry URI; vendor product, edition and licence SKU; vendor model or part number. It states that a container image is written `registry/repository:tag`, gains `@sha256:` only from evidence, and gets a visible placeholder when unpublished, never an invented URI or digest.
- [ ] **AC-0014.** `references/physical-bom.md` states that every line has a price status of `priced`, `unpriced`, or `no direct cost`; a `priced` line cites its source, date, and region; `unpriced` lines are left out of the total and counted; a `no direct cost` line names the line that carries its cost; no price comes from model memory.
- [ ] **AC-0015.** `references/physical-bom.md` states that the architecture-change altitude produces a delta BOM whose lines carry a `Change` of add, remove, or resize and whose totals state the net monthly change.
- [ ] **AC-0005.** `assets/physical-architecture-bom.md` contains a physical topology table, a fenced `mermaid` block, a BOM table whose header columns are exactly `Line`, `Deployment unit`, `Kind`, `Identifier`, `Tier / size`, `Qty`, `Unit price`, `Monthly`, `Price status`, `Source`, a delta BOM table whose header columns are the same list with `Change` after `Line`, and a totals section that names the currency, the unpriced-line count, the excluded costs, and the net monthly change.
- [ ] **AC-0006.** `align-value-stream/SKILL.md` step 4 contains an offer paragraph that names `architect-design`'s solution reference mode and carries both the available-skills roster check and the sentence "If it is not in the roster, continue with this skill's own behaviour and say nothing about it: no mention, no note, and no error."; `packs/product-engineering/pack.toml` declares an `architect` integration whose `consumers` include `skill:align-value-stream` and whose `fallback` contains "say nothing about it".
- [ ] **AC-0007.** `align-value-stream/assets/hard-limits.md` has a `## Hard limits` section of exactly three list items, naming no atomic cross-repo commit, no shared release train, and a rollup that is a snapshot rather than a live feed. `align-value-stream/SKILL.md` step 1 names `assets/hard-limits.md`, the solution repo's README, and confirmation before writing, and none of the phrases "no atomic cross-repo commit", "no shared release train", or "snapshot, not a live feed" (case-insensitive, whitespace- and emphasis-collapsed) appears in `SKILL.md`.
- [ ] **AC-0008.** The `intent` `SKILL.md` § Longer route keeps exactly its six numbered steps and five `(separate skill)` markers and adds an unnumbered continuation in which `decompose` (intent mode) takes `capability-map.md` as input and each Build capability becomes a capability-level child intent; `decompose.md`'s orientation line says that on the longer route it follows `map-capabilities` and no longer says the longer route does not use it; `intent/references/frame.md`'s single-line orientation line contains "does not use it until `intent decompose` hands it a child intent"; `map-capabilities/SKILL.md`, its `assets/capability-map-template.md`, and each capability map under its `examples/` name `intent decompose` as the next step, and none of them names `lean-canvas` or `author-delivery-brief create` as the next step after capability mapping.
- [ ] **AC-0009.** `frame-situation`, `identify-opportunities`, `diverge-solutions`, `place-bet`, and `map-capabilities` `SKILL.md` each contain, whitespace-collapsed, the sentence "Never produce a brief: `lean-canvas` writes the one-page initiative brief and `author-delivery-brief` owns the delivery brief."; no file under `packs/product-engineering/.apm/` contains, whitespace-collapsed, "`place-bet` + `author-delivery-brief create`" or "`lean-canvas` / `author-delivery-brief create` owns".
- [ ] **AC-0010.** `architect-design/evals/evals.json` contains cases `solution-reference-mode`, `solution-reference-app-repo-routes-to-core`, `physical-bom-offer-and-grounding`, and `physical-bom-delta-for-change`; `align-value-stream/evals/evals.json` contains `solution-reference-offer-architect-absent-silent` and `hard-limits-readme-proposal`; each case has at least three assertions, and the `-absent-silent` case has an assertion beginning "Does not mention".
- [ ] **AC-0011.** `architect-design/evals/eval_queries.json` has at least one `should_trigger: true` query naming a solution or system reference architecture and at least one naming a bill of materials, and `agentbundle catalogue lint --root . --deep` exits 0.
- [ ] **AC-0012.** Each pack's version is one patch above its version at the branch base, identical in `pack.toml`, `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`; a changelog fragment exists for each pack; `agentbundle catalogue verify --root .` exits 0.

## Follow-ons

none

## Assumptions

none
