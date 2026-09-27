# Spec: frontend-visual-authority

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none — this feature publishes no interface surface; the
  adopter-owned `[design] output_dir` read paths are an existing contract this
  spec consumes without changing.
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

A team whose design work already produced an aesthetic direction gets a
frontend build that inherits it, renders itself, and corrects visible
divergence before the gates run, instead of one that quietly picks a different
look. Success is that a distinctive approved direction survives implementation:
the surface is rendered and compared against that direction during EXECUTE, and
no visual-verification claim can be recorded for a surface nothing looked at.

## What Changes

- A four-rung visual-authority precedence rule, replacing the named-aesthetic-reference step — `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md` § PLAN pre-flight
- The canonical product-reference table (Linear, Stripe, Vercel, Raycast, Arc, Notion, Toss) — deleted
- Every surviving pointer to that table, renamed to the standalone fallback rung it becomes — `SKILL.md` § 0, `references/design-handoff.md` § refusals, and the shipped `design-handoff-read` eval case
- The concrete seed token block, moved out of the always-loaded path — `references/fallback-tokens.md`
- The print/PPT block, moved to its own reference and routed independently of which rung supplied token values — `references/print-surface.md`. Held by a regression assertion rather than a criterion: it guards a defect this slice introduced and then fixed, which the accepted intent did not ask for
- A render → observe → bounded-correct loop for significant visual work — `SKILL.md` § EXECUTE phase
- Perceptual comparison guidance and the machine-readable rule tables behind it — `references/visual-observation.md`
- One new evidence-manifest field, `visual authority` — `SKILL.md` § Evidence manifest, the field list `fe-status` reads, and the two guide manifest examples
- A seventh reviewer lens reading the manifest as a claim to be tested, and the per-lens confirmation rule that scopes it — `packs/frontend-engineering/.apm/agents/frontend-reviewer.md`
- Six control-flow eval cases covering the integrated, brownfield, standalone, non-visual and no-browser paths — `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json`
- A test module parsing the new rule tables — `packs/frontend-engineering/tests/skills/frontend-engineering/`
- Adopter guidance for the precedence rule, including the tutorial's worked example — `guides/frontend-engineering/`

## Durable Outputs

| Semantic role | Destination | Owner | Evidence | Closeout condition |
| --- | --- | --- | --- | --- |
| User-facing promise | `guides/frontend-engineering/how-to/read-the-design-handoff.md` | frontend-engineering | The how-to names the four rung keys in precedence order | AC-0024 green |
| User-facing promise (worked example) | `guides/frontend-engineering/tutorials/scaffold-a-component.md` | frontend-engineering | Its brief and its aesthetic step are re-based onto the standalone fallback rung, so the tutorial demonstrates rung 4 rather than a named product | AC-0023 green |
| Current product truth (read contract) | `packs/frontend-engineering/.apm/skills/frontend-engineering/references/design-handoff.md` | frontend-engineering | Its two refusal clauses name the fallback rung, preserving the refuse-does-not-fall-through semantics | AC-0006 green |
| Current product truth | `packs/frontend-engineering/JOURNEY.md` stage 3, gate `accept-frontend-evidence` | frontend-engineering | Journey stage 3 names the observation loop; the gate's `whatToCheck` names `visual authority` | Journey and skill agree, and the web mirror is regenerated |
| Interface compatibility | `packs/frontend-engineering/pack.toml`, `.claude-plugin/plugin.json` | frontend-engineering | Matching bumped versions | `test_pack_and_plugin_versions_match[frontend-engineering]` passes |
| Reusable learning | `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json` | frontend-engineering | Six cases A–F with distinct ids | Eval harness shape lint passes and each case names its expected control flow |
| Release history | `docs/product/changelog.md` | frontend-engineering | One entry under the bumped version | Entry names the precedence rule and the observation loop |

Retention class: repository-durable for every row above. No local-only or
PR-only record carries an obligation in this slice.

## Agent Rules

### Always do

- Express visual authority over the three read paths `direction/<slug>.md`, `screens/<slug>/<screen>.md` and `tokens/<slug>.md` beneath the adopter's configured design output directory, naming no pack and no upstream skill.
- Keep the existing handoff read keyed on no heading inside an artifact body; frontmatter may be read, section names may not.
- Record the rung that supplied visual authority, including when the rung was the standalone fallback.
- State rung conditions as properties this pack defines. A frontmatter value only an upstream template produces is an illustration, never the condition itself.
- Re-run `python -m pytest packs/frontend-engineering/tests/skills/frontend-engineering/ -q` and `python3 -m agentbundle catalogue lint --root . --deep` after every edit to a shipped pack file. The `--deep` flag is load-bearing: a shallow run reports no body-length finding and exits zero however long the file is.

### Ask first

- Before changing any `accept-frontend-evidence` gate line inside `PINNED_SKIP_COST` (`whatGoodLooksLike`, `whatBadLooksLike`, `consequence`, and the known-exceptions sentence).
- Before changing the `| unverified items |` manifest row, which a test pins byte-exact.
- Before adding a sixth GATES step, which would move the gate-count prose the verify mode derives.

### Never do

- Never add a required dependency between `frontend-engineering` and any other pack; `prerequisitePacks` stays empty and the `experience-design` entry stays `recommended`.
- Never introduce a new `## ` heading in `SKILL.md`: one between `## GATES phase — Verification` and `## Performance targets` truncates the gate-enumeration parser, and one before the end of `### 5. Rendered-page inspection` shortens the section three test modules read.
- Never add a new browser runtime, screenshot tool, provider-specific UI dependency, or top-level directory; the observation loop reuses the shipped capture mechanism.
- Never let the EXECUTE observation loop replace GATES step 5, and never let it iterate beyond its stated bound without an explicit operator request.

## Testing Strategy

| Outcome from `Outcome` | Mode | Why |
| --- | --- | --- |
| The direction is inherited rather than re-decided | TDD | The precedence order and what each rung binds are a table a parser reads; a wrong order reds a test. |
| The surface is rendered and compared during EXECUTE | TDD | Activation, the representative-capture set and the loop bound are rule-table rows; a changed bound reds the bound test. |
| No visual-verification claim without a capture | TDD | A predicate over candidate values, mirroring the shipped `observations_value_is_acceptable` rejection test. |
| Standalone operation survives with no design artifact | TDD | The declared-dependency greps are regression guards that already hold; the criterion that can newly fail is the forbidden-literal check over the new reference, which reds if a rung is keyed on upstream vocabulary. |
| The entrypoint shrinks rather than grows | TDD | The budget is a pack-suite assertion, not a one-off command, because it must re-run after every later task that writes the entrypoint. The assertion re-derives the lint's post-frontmatter counting rule and is the canonical counter for the 960 figure; the lint only errors at 1000 and cannot verify 960. |
| The six control-flow cases read correctly to an agent | visual / manual QA | Eval prompts are judged, not asserted; the harness records expected output, and the shape lint proves the file is well-formed. |

## Acceptance Criteria

**Two delivery slices, one contract.** Slice 1 is the executable contract
inside `packs/frontend-engineering/.apm/` — precedence, the observation loop,
the manifest field, the reviewer lens — and ships as `0.3.4`. Slice 2 is the
journey, the web mirror, the guide tree and its release, and ships as `0.3.5`.
The spec stays `Implementing` until slice 2 closes: a criterion left open is
delivery debt, not a shipped exception. The plan's coverage table assigns every
criterion to a task, and its task list marks where the slice boundary falls.


Every criterion below that greps a closed list of **aesthetic anchors or
upstream vocabulary** — AC-0004, AC-0004a, AC-0005, AC-0006, AC-0018a and
AC-0023 — is a **named-literal proxy**, and the spec says so rather than
implying more. No predicate recognises a product name it was not given, so they catch a
surviving anchor, never a newly invented one. The ban is on aesthetic anchors:
a reference to the repository's `linear` pack by its pack name is an excluded
case, not a violation.

- [ ] **AC-0000** `SKILL.md`'s PLAN pre-flight names all four rung keys in the order AC-0001 fixes, and names `references/visual-observation.md` as where their rules are read. The four keys are required, not just a pointer: routing alone would hold the always-loaded entrypoint to a weaker standard than AC-0024 holds the derived guide page to.
- [ ] **AC-0000a** `SKILL.md`'s EXECUTE phase states the render → observe → correct sequence and the one-correction bound, and names `references/visual-observation.md` as where the activation rubric and the full bound are read.
- [ ] **AC-0000b** In `references/visual-observation.md`'s `## Authority precedence` table, each of the `approved-visual-target`, `direction-and-taxonomy` and `incumbent-system` rows carries a `source` cell. The first two name one of `direction/<slug>.md`, `screens/<slug>/<screen>.md` or `tokens/<slug>.md`; the third names the repository's existing visual system. `local-premise` carries `none — stated in-session`.
- [ ] **AC-0001** `references/visual-observation.md` carries an `## Authority precedence` table whose row keys, in order, are `approved-visual-target`, `direction-and-taxonomy`, `incumbent-system`, `local-premise`.
- [ ] **AC-0002** `references/visual-observation.md` carries an `## Authority limits` table enumerating what visual authority never controls, whose row keys are exactly `product-behaviour`, `accessibility`, `content-correctness`, `data-and-state`, `security`, `component-contracts`, `platform-constraints`.
- [ ] **AC-0003** Every row of the `## Authority precedence` table carries a non-empty `requires` cell and a non-empty `falls-to` cell.
- [ ] **AC-0003a** The `approved-visual-target` row's `requires` cell is `recorded-human-confirmation`.
- [ ] **AC-0003b** Each row's `falls-to` cell names the next row key in the AC-0001 order, and the last row's is `none — terminal`. This pins every demotion edge, not only the chain's ends: a cell naming no rung, or an upward demotion, reds.
- [ ] **AC-0004** `references/visual-observation.md` contains none of the identifiers `experience-design`, `creative-direction`, `design-system`.
- [ ] **AC-0004a** No `requires` or `falls-to` cell in any rule table in `references/visual-observation.md` carries the value `proposed` or `selected`. The check is scoped to those cells, not to the words: ordinary prose such as "the selected viewport" stays legal.
- [ ] **AC-0005** No file under `packs/frontend-engineering/.apm/skills/frontend-engineering/` or `packs/frontend-engineering/.apm/agents/` contains, as a whole word, any of `Linear`, `Stripe`, `Vercel`, `Raycast`, `Arc`, `Notion`, `Toss`. The predicate is **case-sensitive**, and the root excludes sibling skills: `responsive-layout/SKILL.md` legitimately says `linear interpolation`, and a case-insensitive sweep of the whole pack would red on a CSS term in a skill this slice does not touch.
- [ ] **AC-0006** No file under `packs/frontend-engineering/.apm/` contains the phrase `canonical set`, `canonical product-reference set`, or `canonical reference set`. The predicate is case-insensitive and whitespace-normalized across line breaks, because one live pointer wraps mid-phrase and one is a capitalised heading.
- [ ] **AC-0007** `SKILL.md` contains no `:root {` and no line matching `^\s*--ds-color-primary\s*:`; `var(--ds-color-primary)` usages elsewhere in the file are expected to remain.
- [ ] **AC-0008** `SKILL.md` § PLAN pre-flight names `references/fallback-tokens.md` as where the fallback token block is read from.
- [ ] **AC-0009** `SKILL.md`'s body is at most 960 lines, counted as the catalogue skill-spec lint counts it — post-frontmatter, `splitlines()`. The pack-suite assertion is the canonical counter; the lint is a cross-check that errors only at 1000, so the two cannot silently disagree below that.
- [ ] **AC-0010** `references/visual-observation.md` carries a `## Loop bound` table whose rows are `correction-passes` = `1`, `verification-renders-after-correction` = `1`, `further-passes` = `operator-requested`, and `residual-divergence` = `recorded-not-iterated`.
- [ ] **AC-0011** The `## Activation` table's `activates` row enumerates exactly `new-surface`, `new-major-component`, `substantial-redesign`, `composition-change`, `responsive-restructuring`, `implementation-from-visual-target`.
- [ ] **AC-0012** The `## Activation` table's `skips` row enumerates exactly `copy-only`, `behaviour-only`, `trivial-variant`, `non-visual-accessibility-fix`, `engineering-refactor`.
- [ ] **AC-0013** The `## Activation` table carries a `test` row and a `skip-recorded` row whose value is `required`.
- [ ] **AC-0014** `references/visual-observation.md` carries a `## Verification claims` table whose `claim-without-capture` row reads `rejected`, driven by the same predicate shape `observations_value_is_acceptable` applies to the observations field.
- [ ] **AC-0015** The required-field table under `SKILL.md` § Evidence manifest carries a `visual authority` row.
- [ ] **AC-0015a** `packs/frontend-engineering/.apm/skills/fe-status/SKILL.md` describes the manifest as a 13-field record. `SKILL.md:350`'s "full 12-field contract" is explicitly out of scope: that is the page/screen contract, a different twelve, and editing it would break a correct surface.
- [ ] **AC-0016** `frontend-reviewer.md` carries a `### Lens 7 — Visual authority` heading.
- [ ] **AC-0017** `frontend-reviewer.md`'s per-lens confirmation rule states what Lens 7 reads and why it is not held to diff-confirmation.
- [ ] **AC-0018** `frontend-reviewer.md` states `seven lenses` at least twice.
- [ ] **AC-0018a** `frontend-reviewer.md` contains none of the literals `across six lenses`, `the six lenses`, `these six lenses`, `the other five lenses`, `the other five against`. The predicate is case-insensitive, matching AC-0006: one target site capitalises the phrase mid-sentence and a case-sensitive check passes straight over it. The ranges `Lenses 1-5` and `lenses 1-5` need no exclusion — no banned literal reaches them — and they are deliberately legal, because they describe the diff-reading lenses rather than counting the roster.
- [ ] **AC-0019** The `review-frontend-implementation` gate in `packs/frontend-engineering/JOURNEY.md` names the visual-authority lens.
- [ ] **AC-0019c** `JOURNEY.md`'s stage-3 implementation sequence describes the precedence rule, and names neither a canonical aesthetic reference nor a seed token block as a step.
- [ ] **AC-0019a** The `description` frontmatter of `frontend-reviewer.md` names the visual-authority lens, and stays a single line of at most 1024 characters.
- [ ] **AC-0019b** `pack.toml`'s `starter-prompt` and `expected-result` describe the visual-authority pre-flight, and neither names an aesthetic reference nor a seed token block as a step the user asks for.
- [ ] **AC-0020** `packs/frontend-engineering/pack.toml` declares no required dependency on another pack.
- [ ] **AC-0021** `packs/frontend-engineering/JOURNEY.md` carries `prerequisitePacks: []`.
- [ ] **AC-0022** `evals/evals.json` carries cases with these six ids, alongside the cases it already ships: `visual-authority-approved-target`, `visual-authority-direction-only`, `visual-authority-incumbent`, `visual-authority-standalone`, `visual-authority-non-visual`, and `visual-authority-no-browser`.
- [ ] **AC-0023** No file under `guides/frontend-engineering/` contains, as a whole word, any of the seven product names AC-0005 lists, under the same case-sensitive predicate.
- [ ] **AC-0023a** No file under `guides/frontend-engineering/` contains the phrase `canonical set`, `canonical product-reference set`, or `canonical reference set`, under AC-0006's predicate.
- [ ] **AC-0024** `guides/frontend-engineering/how-to/read-the-design-handoff.md` names the four precedence rung keys in the order AC-0001 fixes.
- [ ] **AC-0024a** `guides/frontend-engineering/reference/frontend-engineering.md`'s description of the pre-flight names the precedence rule rather than a named aesthetic reference.
- [ ] **AC-0024b** Every reference in `guides/frontend-engineering/` to a numbered `frontend-engineering` pre-flight step names a step that exists after the renumbering, or names the step by title instead of by number.
- [ ] **AC-0025** `packs/frontend-engineering/pack.toml` and `.claude-plugin/plugin.json` both carry version `0.3.4` when slice 1 ships.
- [ ] **AC-0025a** Both files carry version `0.3.5` when slice 2 ships. Slice 1 changes pack content on its own, so it owes its own bump and its own eval-harness update; slice 2 does the same rather than riding slice 1's.

## Follow-ons

- `packs/experience-design/JOURNEY.md` and `guides/experience-design/how-to/choose-the-depth.md` each state that the frontend pre-flight falls back to its own canonical reference for an unfilled slot. This slice removes that fallback, so both sentences become false on the day it ships. Owner: experience-design. Out of this slice by owner decision: the sentences live in another pack, and correcting them here would pull that pack's version bump and its eval-harness obligation into a frontend change. No test pins either sentence, so nothing reds — which is why this entry exists rather than a criterion.
- The `work-loop` dispatch line for `frontend-reviewer` (`packs/core/.apm/skills/work-loop/SKILL.md`) enumerates the reviewer's lenses inline and does not mention visual authority. Owner: core. Out of this slice: the line is core-owned, its shipped test pins three content strings that a seventh lens does not falsify, and obliging the edit here would import core's version-bump and eval-harness obligations for no gain.

- The `experience-design >= 3.0.0` recommendation in `packs/frontend-engineering/pack.toml` is a major behind the shipped `4.0.0`. Owner: frontend-engineering. Out of this slice's frontier: nothing in the accepted intent depends on the pin's value.
- A deterministic visual-divergence scanner, live visual variants, image generation, pixel matching, and computer-vision region extraction are all out of scope by the accepted intent and have no owner in this slice.

## Assumptions

- Technical: `recorded-human-confirmation` is a property this pack defines, and no control verifies it. It is a claim in an adopter-writable file, exactly as `type:` is, and a writer that records confirmation some other way than the one the reference illustrates still satisfies rung 1. What this pack cannot do is notice a writer that stops recording confirmation at all: every direction then resolves to `direction-and-taxonomy` and nothing watches. Only a control outside the agent closes that, and this slice adds none.
- Product: whether the observation loop should activate on a retrofit that restores a missing state without changing composition is unsettled. It changes the `activates` row's `composition-change` member. The pack owner can settle it; until then the member reads as a composition test, which excludes that case.
