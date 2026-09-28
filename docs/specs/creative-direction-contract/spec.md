# Spec: Product-specific creative-direction contract

- **Status:** Shipped
- **Owner:** experience-design maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0033; ADR-0024; ADR-0116; [`creative-direction-modes`](../creative-direction-modes/spec.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> change must match this spec or amend it through the repository workflow.
> `Agent Rules`, `Testing Strategy`, and `Acceptance Criteria` are the contract
> sections read by completion gates.

## Outcome

People can turn product context into a specific visual direction that reflects the audience's situation, the product's distinctive mechanism, and evidence the surface can honestly show. The result is buildable from the Experience Design pack alone and remains useful when upstream packs, visual references, browser control, or image analysis are absent.

## What Changes

- The `creative-direction` frame and convergence contracts gain an engagement-mode overlay, a product-specific visual thesis, a first-viewport thesis, and a conditional signature interaction.
- The direction template gains explicit fields for those commitments and for an optional approved visual target.
- Grounding, exploration, visualization, convergence, and refusal guidance distinguish real assets and evidence from placeholders and avoid category-default rules becoming universal style bans.
- Skill evaluations and construction tests cover the new output contract, graceful fallback, content honesty, and retained routes, axes, and divergence checks.
- The Experience Design guide, pack metadata, marketplace projection, and release history reflect the published behavior.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | The published skill contract changes | `packs/experience-design/.apm/skills/creative-direction/` | Experience Design maintainers | Skill, references, template, and eval diff | Targeted construction tests and catalogue verification pass |
| User promise | People need to know what context the skill accepts and what it returns | `guides/experience-design/how-to/establish-design-intent.md` | Experience Design guide maintainers | Guide-agreement test and guide review | Guide names the independent input and output contract without adding a pack dependency |
| Interface compatibility | Non-cosmetic pack content changes | `packs/experience-design/pack.toml`, `packs/experience-design/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Pack maintainers and build projection | Matching patch versions and regenerated marketplace data | Source manifests agree and the projection is current |
| Release history | Pack consumers gain a new capability | `docs/product/changelog.md` | Product documentation maintainers | A free-standing Experience Design patch release entry with highlights | Release entry names the observable outcome and the version matches pack metadata |
| Reusable learning | Agent-level behavior needs durable examples | `packs/experience-design/.apm/skills/creative-direction/evals/` | Skill maintainers | Cases for the new contract, fallback, honesty, and retained behavior | Eval JSON validates and construction tests pin the required cases |

## Agent Rules

### Always do

- Preserve the `inherit`, `extend`, and `originate` routes; the five operations; all fifteen direction axes; candidate divergence; the counterfactual check; and the existing quality floor.
- Treat engagement mode as an overlay on surface genre. Record one primary mode and record a secondary mode only with a reason tied to a distinct user job.
- Classify `persuade` as establishing relevance, confidence, and desire; `operate` as supporting repeated or consequential work; `read` as making structured information easy to understand and navigate; and `experience` as making exploration or immersion part of the value.
- Ground the visual thesis in the audience's situation, the product's distinctive mechanism, and honest proof available to the surface.
- Distinguish available evidence and assets from placeholders. Record provenance for every sourced or generated visual asset proposed by the direction.
- Accept any adequate combination of a product intent, Digital Experience Contract, screen brief, existing product, approved visual target, or direct user answers.
- Keep the existing write target and `type: creative-direction` artifact identity.

### Ask first

- Change the fifteen-axis vocabulary, route set, operation set, artifact path, or frontmatter type.
- Add a dependency on another pack, runtime, browser, image-analysis tool, script, hook, extension, downloaded binary, or package.
- Change a file outside the Creative Direction skill, its Experience Design guide, its pack-local tests and evals, required pack metadata, generated marketplace metadata, this delivery contract, or the release record.

### Never do

- Require Product Engineering, Frontend Engineering, a comp, browser control, or image analysis for a successful run.
- Invent testimonials, customer metrics, screenshots, certifications, product claims, or asset provenance.
- Treat decorative motion as a signature interaction or require an interaction when none materially expresses or explains the product.
- Turn category-default detection into an absolute style ban, font blacklist, fixed radius rule, or universal aesthetic value.
- Let engagement mode replace or silently alter the surface genre.
- Use random or dice-based selection.
- Change `frame-intent`, `frontend-engineering`, `design-review`, or any reviewer agent in this delivery.
- Add source attribution, identifiers, or copied wording from material outside the repository and the accepted user requirements.

## Testing Strategy

- **Published contract (AC-0001, AC-0002, AC-0005, AC-0006, AC-0007, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0016, AC-0019):** TDD through a pack-local construction test. The test reads the real skill, template, references, and eval files and fails when required fields, mode definitions, fallback rules, retained route names, the fifteen-axis inventory, retained divergence threshold, counterfactual check, or quality floor disappear.
- **Agent behavior (AC-0003, AC-0004, AC-0008, AC-0015, AC-0017):** goal-based checks over the skill-local eval corpus. Rubric cases cover product specificity, first-viewport content, content honesty, graceful fallback, and existing inheritance and divergence behavior.
- **Packaging (AC-0018):** goal-based checks through targeted pytest, deep catalogue lint, catalogue verification, generated-projection comparison, and `make lint-ruff lint-mypy`.
- **Invoked artifact:** visual / manual QA through one real `creative-direction` prompt using direct answers with no upstream pack or visual tool. The recorded result must include the four required output fields and must not invent evidence or block on a missing capability.

## Acceptance Criteria

- [x] **AC-0001.** A captured creative-direction artifact names a primary engagement mode from `persuade`, `operate`, `read`, or `experience`; a secondary mode is absent unless the artifact gives a distinct user-job reason for it.
- [x] **AC-0002.** The skill defines engagement mode as visitor posture and surface genre as the kind of surface being designed, and states that neither value overwrites the other.
- [x] **AC-0003.** The output contract requires a product-specific visual thesis that names the audience's situation, the product's distinctive mechanism, and honest proof the surface can show.
- [x] **AC-0004.** The specificity check rejects a direction that can be relabeled for a category peer without materially changing its evidence or choices.
- [x] **AC-0005.** The output contract requires a first-viewport thesis that states what the opening viewport makes clear, which concrete evidence or mechanism it exposes, and which primary action or continuation it supports without prescribing a hero layout.
- [x] **AC-0006.** The output contract records a signature interaction only when it materially expresses the product or helps a person understand or operate it; `none` is valid, and decorative motion does not satisfy the field.
- [x] **AC-0007.** An approved visual target is optional. When present, its record identifies the target, what is binding, what is illustrative, and what may adapt across responsive states.
- [x] **AC-0008.** The skill labels available evidence and assets separately from placeholders, refuses invented claims and product media, and records provenance for proposed sourced or generated visual assets.
- [x] **AC-0009.** Exploration identifies category-default styling and generic tropes, while allowing a familiar pattern when the primary engagement mode and user job justify it.
- [x] **AC-0010.** The skill introduces no absolute style ban, font blacklist, fixed radius, or universal aesthetic value.
- [x] **AC-0011.** A run can begin from any adequate combination of product intent, Digital Experience Contract, screen brief, existing product, approved target, or direct user answers.
- [x] **AC-0012.** When an optional upstream artifact or capability is missing, the skill asks only the unresolved fallback questions or records a labeled assumption and continues without a hard dependency.
- [x] **AC-0013.** The `inherit`, `extend`, and `originate` routes and the `frame`, `explore`, `visualize`, `converge`, and `refine` operations remain available with their current write boundaries.
- [x] **AC-0014.** All fifteen direction axes remain in the template and divergence audit, and candidate sets still fail when their minimum pairwise distance is below six axes.
- [x] **AC-0015.** A generic "clean and modern" direction does not pass the output-quality rubric without product-specific evidence and choices.
- [x] **AC-0016.** The skill requires no random selection, executable engine, browser extension, hook, downloaded binary, new dependency, Product Engineering pack, or Frontend Engineering pack.
- [x] **AC-0017.** Pack-local construction tests and skill evaluations cover the new output contract, graceful fallback, content honesty, and retained route, operation, axis, divergence, counterfactual-check, and quality-floor behavior.
- [x] **AC-0018.** The Experience Design guide, matching pack and plugin patch versions, generated marketplace projection, and release entry agree with the published contract.
- [x] **AC-0019.** The shipped engagement-mode definitions match the authoritative four-value map in `Agent Rules`.

## Follow-ons

none

## Assumptions

none
