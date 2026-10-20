# Spec: Architecture before the cut on the intent short route

- **Status:** Implementing
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

A team shaping work on the `intent` short route with `architect-design` installed is offered the architecture design after the bet survives `intent de-risk` and before `intent decompose` cuts it, at a scope picked from the intent's level, as the operating model says: "Take it before you cut the work, and if it changes the capabilities, take the longer route." They can decline it once per intent and decompose as usual, and a team without `architect-design` sees no change: no mention, no note, and no error.

## What Changes

- `intent/SKILL.md` gains `### Architecture before the cut` inside § The intent lifecycle: the one home for when the offer is made, the level-to-scope table, what "covers" means, and the decline rule. The short route names the stage between `de-risk` and `decompose` without renumbering.
- On a surviving bet on the short route, `de-risk.md` offers `architect-design` and recommends it instead of `intent decompose`.
- `decompose.md` gains `## Design before you cut`. It pauses once to offer `architect-design` when no design covers the intent. It cuts as usual after a decline. When the design changes the intent's capabilities, it recommends `map-capabilities` for a capability or higher and reframing the parent capability for a feature.
- Decompose step 1 keeps its subsystem-boundary check and drops its own narrower offer, which the new section replaces.
- Evals cover the installed, declined-earlier, covered, capabilities-changed, and not-installed paths, and the existing decompose cases state their roster. Pack tests pin the offers, the scope table, the precedence, and the silence.
- The adopter guide gains a design step before the work is broken down. The README states the new offer.
- `product-engineering` 2.0.1 with a changelog fragment; projections regenerated.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Adopters see a new step on the short route. | `guides/product-engineering/how-to/frame-the-intent.md`; `packs/product-engineering/README.md` | Product-engineering maintainers | AC-0016, AC-0017 | Both describe the design step and its decline. |
| Release history | Non-cosmetic skill behaviour change. | A fragment under `docs/product/changelog.d/` made by `tools/changelog.py new` | Pack release maintainer | AC-0015 | Fragment validates. |
| Current architecture | Not applicable: no module, boundary, or pack relation changes; the `architect` integrations in `pack.toml` already cover `architect-design`. | none | — | — | — |
| Decision rationale | Not applicable: the operating model already states the order; this spec makes the skill follow it. | none | — | — | — |

## Agent Rules

### Always do

- Edit `.apm/` sources only, then run `make build-self`.
- Follow every architect offer, in the same paragraph, with the silent clause that `docs/specs/architect-shaping-reach/spec.md` owns.
- Leave the decision with the user: offer `architect-design`, never start it, and cut as usual after a decline.

### Ask first

- Adding an architect offer to any `intent` mode or skill this spec does not name.
- Changing the frame mode's system-shape section or the longer and supervised routes.

### Never do

- Renumber the short route's intent-mode steps, change any `Stage:` line, or add a `##` heading to `intent/SKILL.md`.
- Add a `[pack.dependencies]` entry on `architect`, or, in shipped content under `.apm/`, tell the user to install it or mention its absence.
- Make the architecture step a hard block on `intent decompose`.
- Edit `guides/_shared/explanation/the-operating-model.md`, `guides/_shared/reference/detailed-operating-model.md`, their SVGs, or `tools/render-lifecycle-graphics.py`.

## Testing Strategy

Every phrase check reads the `.apm/` source with whitespace collapsed, is case-sensitive, and lives in `packs/product-engineering/tests/pack/`; prose has no runtime to drive.

- **Canonical rules (AC-0001, AC-0002, AC-0003, AC-0020, AC-0021):** goal-based phrase and heading checks on `SKILL.md` and the mode files.
- **Offers and precedence (AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010):** goal-based phrase and order checks on `de-risk.md` and `decompose.md`, plus the existing per-bullet offer cap widened to count `architect-design`.
- **Silence (AC-0011):** goal-based plus a mutation: `SKILL.md` joins the silent-clause test's offer files, and a mutation proves a dropped clause is reported.
- **Behaviour evals (AC-0012, AC-0013):** goal-based. A pack test asserts each case's id, mode, and deciding assertion; the existing eval-shape tests validate the file.
- **Release and docs (AC-0014, AC-0015, AC-0016, AC-0017):** goal-based: version parity by a `tomllib` and `json` comparison command, `tools/changelog.py validate`, README and guide phrase checks.
- **Projection and guides (AC-0018, AC-0019, AC-0022):** goal-based commands.

## Acceptance Criteria

- [ ] **AC-0001.** `intent/SKILL.md` § The intent lifecycle has a `### Architecture before the cut` subsection containing "Check your available-skills roster for `architect-design`", "offer it before the cut", "never start it yourself", and the silent clause.
- [ ] **AC-0002.** That subsection maps level to scope with these rows: "`product-vision` or `product-strategy` | `application/system`", "`capability` | `subsystem` when the system it belongs to already runs; otherwise `application/system`", and "`feature` | `architecture change`".
- [ ] **AC-0003.** That subsection contains "A design covers an intent when it is a resolved `architecture-design` artifact made for that intent or for one of its ancestors, and it names the system or subsystem the intent changes." and "When the user declines `architect-design` for an intent, do not offer it again for that intent in this conversation. Choosing another offered option counts as declining it; declining the frame mode's system-shape offer does not."
- [ ] **AC-0004.** `intent/SKILL.md` § Short route contains "Then, before `decompose`: `architect-design` (separate skill) is offered", placed after the "2. `de-risk`" line and before the "3. `decompose`" line, in a paragraph that also contains "available-skills roster" and the silent clause.
- [ ] **AC-0005.** The `de-risk.md` § Next survive bullet contains "`intent decompose` (short route)", "`place-bet` (longer route)", "Recommend the one for the route the conversation shows, unless the next paragraph applies.", and a paragraph containing "On the short route, check your available-skills roster for `architect-design`", "When you offer it, recommend `architect-design` instead of `intent decompose`.", "§ Architecture before the cut", and the silent clause.
- [ ] **AC-0006.** The per-bullet offer cap in `test_intent_skill_structure.py` counts `architect-design`, and every `## Next` bullet in the mode files names at most three offers under it.
- [ ] **AC-0007.** `decompose.md` has a `## Design before you cut` section after `## When to invoke` and before `## Procedure`, containing "When `discovery-loop` or its `discovery-lead` agent called this mode, skip this section", "check your available-skills roster for `architect-design`", "pause before cutting", "§ Architecture before the cut", and the silent clause.
- [ ] **AC-0008.** That section contains "When the user declines, cut as usual." and "When the design changes the intent's capabilities, do not cut yet: for a `capability` or higher intent, recommend the longer route at `map-capabilities`; for a `feature`, recommend `intent frame` for its parent capability. Also offer to cut."
- [ ] **AC-0009.** `decompose.md` step 1 still contains "subsystem boundaries" and "Boundaries inform dependencies; the cut stays by shippability, never by component.", and the step-1 text names neither `architect-design` nor `architect-assess`.
- [ ] **AC-0010.** `decompose.md` contains no "`subsystem` or `application/system` scope", and `test_decompose_and_map_capabilities_offers` asserts the `## Design before you cut` phrases in its place.
- [ ] **AC-0011.** `intent/SKILL.md` is in the silent-clause test's offer files, and the test reports a problem when the silent clause is removed from `SKILL.md`'s offer paragraph.
- [ ] **AC-0012.** `intent/evals/evals.json` has these cases, each with the quoted assertion: `de-risk-survive-architect-first` (`de-risk`) "Recommends architect-design instead of intent decompose"; `decompose-architect-first` (`decompose`) "Pauses before cutting and offers architect-design"; `decompose-declined-at-de-risk` (`decompose`) "Cuts without offering architect-design again"; `decompose-design-already-covers` (`decompose`) "Cuts without offering architect-design"; `decompose-design-changes-capabilities` (`decompose`) "Recommends the longer route at map-capabilities"; `decompose-feature-design-changes-capabilities` (`decompose`) "Recommends intent frame for the parent capability"; `de-risk-survive-no-route-architect-installed` (`de-risk`) "Recommends neither route and asks which route applies"; `de-risk-chose-decompose-then-decompose` (`decompose`) "Cuts without offering architect-design again"; `de-risk-survive-architect-absent` (`de-risk`) "Does not mention architect, its skills, or their absence".
- [ ] **AC-0013.** The prompts of the existing `decompose-1` and `capability-negotiated-handoff` cases each contain "The architect skills are not in the available-skills roster."
- [ ] **AC-0014.** `product-engineering` is `2.0.1` in both `pack.toml` and `.claude-plugin/plugin.json`.
- [ ] **AC-0015.** A fragment under `docs/product/changelog.d/` names package `product-engineering` version `2.0.1` with a `## Highlights` section, and `python3 tools/changelog.py validate` exits 0.
- [ ] **AC-0016.** `packs/product-engineering/README.md` contains "`intent de-risk` and `intent decompose` offer `architect-design` before the work is cut".
- [ ] **AC-0017.** `guides/product-engineering/how-to/frame-the-intent.md` has a `## Design the architecture` section after `## Test the riskiest assumption` and before `## Break it into work`, containing "architect", "optional", "agentbundle install --pack architect", and "skip".
- [ ] **AC-0018.** On the committed tree, `agentbundle catalogue verify --root .` exits 0.
- [ ] **AC-0019.** On the committed tree, `make build-self` leaves `git status --porcelain` empty.
- [ ] **AC-0020.** `intent/SKILL.md` has exactly the `##` headings "When to invoke", "The intent lifecycle", "Route mode", and "Modes" besides "Output rendering".
- [ ] **AC-0021.** The mode files still contain "step 1 of 3" (`frame.md`), "step 2 of 3" (`de-risk.md`), and "step 3 of 3" (`decompose.md`).
- [ ] **AC-0022.** `python3 tools/validate_guides.py` exits 0.

## Follow-ons

none

## Assumptions

- Product: the available-skills roster is the only installed check a prompt-only skill has. A host that hides an installed skill gets the silent path, which is safe.
