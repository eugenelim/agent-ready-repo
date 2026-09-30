# Plan: Product-specific creative-direction contract

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `AGENTS.md`, `packs/AGENTS.md`, `packs/AGENTS.local.md`, `ARCHITECTURE.md`, `guides/_shared/reference/catalogue-authoring-standards.md`, [`creative-direction-modes`](../creative-direction-modes/spec.md), `packs/experience-design/.apm/skills/creative-direction/`, `packs/experience-design/pack.toml`; no new module boundary or dependency, and the named uncertainty is how much of the prose contract belongs in the always-loaded skill versus operation references.

> **Plan contract:** this is the implementation and verification strategy.
> `Touches`, `Tests`, and `Done when` are completion-gate inputs. After approval,
> execution observations belong in `notes/verification-ledger.md`.

## Approach

Start with one pack-local construction test that pins the new output fields and retained behavior. Then revise the smallest existing owners: `SKILL.md` for input and routing rules, operation references for method detail, the template for the captured contract, and evals for agent behavior. Finish by updating the public guide and required release surfaces, regenerating projections, and running the targeted pack, catalogue, lint, and manual-invocation checks.

## Constraints

- RFC-0033 keeps this work inside the Experience Design pack.
- ADR-0024 keeps the skill framework-agnostic and portable.
- ADR-0116 keeps the only durable output under `<output_dir>/direction/`.
- The shipped [`creative-direction-modes`](../creative-direction-modes/spec.md) contract owns the route set, operation set, axis inventory, divergence rule, write boundary, and browserless text representation.
- `packs/AGENTS.md` requires a patch version bump in both source manifests and an eval-harness update for a non-cosmetic `.apm/` change.
- `packs/AGENTS.local.md` requires marketplace regeneration and a release entry with an explicit Highlights decision.
- No new RFC, executable, dependency, hook, browser surface, image-analysis requirement, or cross-pack dependency enters this slice.
- `frame-intent`, `frontend-engineering`, `design-review`, and reviewer-agent files are outside the write boundary.
- The source-anonymity requirement applies to every tracked and generated artifact.
- Skill-engineering knowledge provider: unavailable; repository contracts and the accepted request are the authoring baseline.

## Grounding

The pre-review disconfirming probe resolved every planned skill owner as a regular file and found all three route names and five operation names in the current `SKILL.md`. This supports an in-place contract extension; implementation stops for amendment if any owner disappears or the retained names move before execution.

## Construction tests

**Integration tests:** the targeted pack-local pytest reads the shipped skill, template, references, and eval corpus together; deep catalogue lint and catalogue verification cover packaging.

**Manual verification:** invoke the built `creative-direction` skill once from direct product answers with no upstream pack, comp, browser, or image-analysis tool. Record the returned engagement mode, visual thesis, first-viewport thesis, visual-target disposition, and honesty/fallback behavior in `notes/verification-ledger.md`.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Skill, references, and template | T1, T2 | Targeted construction test and diff | AC-0001–AC-0016 checked; catalogue verification passes |
| Skill eval corpus | T1, T3 | Valid JSON and retained/new rubric cases | AC-0017 checked; eval structural checks pass |
| Experience Design guide | T4 | Guide-agreement test and diff | Guide states the independent contract |
| Pack, plugin, and marketplace versions | T4 | Matching source versions and zero generated drift | AC-0018 checked; projection is current |
| Release history | T4 | Changelog entry with Highlights | Entry version and behavior match the pack |

## Design (LLD)

### Design decisions

<!-- Owned by: T2. -->

The always-loaded `SKILL.md` owns the input contract, engagement-mode definition, required output fields, and operation routing. Detail that applies only during exploration, grounding, visualization, or convergence stays in the corresponding reference, while the template remains the single owner of the durable artifact shape. Traces to: AC-0001–AC-0016. Owned by: T2.

### Interfaces & contracts

<!-- Owned by: T2. -->

The public interface is the installed `creative-direction` skill plus `<output_dir>/direction/<slug>.md`; no separate `contracts/` file applies. The template adds fields without changing the artifact path or `type: creative-direction` identity. Traces to: AC-0001–AC-0008, AC-0011–AC-0013. Owned by: T2.

### Component / module decomposition

<!-- Owned by: T2, T3. -->

- `SKILL.md`: graceful inputs, engagement-mode overlay, operation-level ownership, and output summary.
- `references/grounding.md`: product mechanism, honest proof, evidence and asset status, provenance, and specificity check.
- `references/explore.md`: category-default and trope detection with an earned-pattern exception.
- `references/visualize.md`: optional approved-target record and responsive binding rules.
- `references/converge.md`: required thesis capture and conditional signature interaction.
- `references/refusals.md`: generic direction, invented proof, decorative motion, and absolute-style-rule refusals.
- `assets/creative-direction-template.md`: durable fields.
- `evals/`: behavioral cases.

Traces to: AC-0001–AC-0017. Owned by: T2, T3.

### State & control flow

<!-- Owned by: T2. -->

`frame` classifies the primary engagement mode and assembles enough product evidence from whatever valid inputs exist. `explore` uses that posture and user job when judging familiar patterns. `converge` runs the product-specificity check and captures the visual, viewport, target, interaction, evidence, and asset commitments. Missing optional inputs produce focused questions or labeled assumptions; they do not stop the route. Traces to: AC-0001–AC-0015. Owned by: T2.

### Behavior & rules

<!-- Owned by: T2. -->

Engagement modes implement the authoritative four-value map in the spec's `Agent Rules`. They describe visitor posture, while surface genre continues to describe the surface family and its IA/craft context. A direction is specific only when substituting a category peer changes its mechanism, proof, or visual commitments. Familiar visual patterns remain valid when the posture and job justify them; the skill rejects unsupported generic choices rather than banning a style family. Traces to: AC-0002–AC-0005, AC-0009, AC-0010, AC-0015, AC-0019. Owned by: T2.

### Failure, edge cases & resilience

<!-- Owned by: T2. -->

The skill treats absent upstream artifacts, absent visual targets, and absent image or browser capabilities as normal input states. It distinguishes placeholders from available material and refuses fabricated evidence; unresolved product facts remain questions or labeled assumptions. Traces to: AC-0007, AC-0008, AC-0011, AC-0012, AC-0016. Owned by: T2.

### Quality attributes

<!-- Owned by: T1, T3, T4. -->

The change remains pure Markdown and JSON, keeps progressive disclosure, preserves the current output path, and adds no runtime dependency. Construction tests cover exact contract anchors; eval rubrics cover the judgment-heavy agent behavior those tests cannot execute. Traces to: AC-0013–AC-0018. Owned by: T1, T3, T4.

### Dependencies & integration

<!-- Owned by: T2. -->

Product intent, Digital Experience Contract, screen brief, existing product, direct answers, and approved visual targets are optional evidence sources, not installed-pack dependencies. Product Engineering and Frontend Engineering are neither required nor invoked. Traces to: AC-0011, AC-0012, AC-0016. Owned by: T2.

## Tasks

### T1: Construction test fails when the new contract or retained behavior is absent

**Depends on:** none

**Touches:** `packs/experience-design/tests/skills/creative-direction/test_contract.py`

**Tests:**

- TDD for AC-0001, AC-0002, AC-0005, AC-0006, AC-0007, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0016, and AC-0019: add the following exact red stub, run it against the current skill, and retain the same contract-surface assertions while filling the full construction matrix:

```python
from pathlib import Path


PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "creative-direction"


def test_creative_direction_publishes_product_specific_contract() -> None:
    """The shipped skill and artifact template expose the new contract."""
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    template = (SKILL_ROOT / "assets/creative-direction-template.md").read_text(
        encoding="utf-8"
    )
    contract = skill + template
    for required in (
        "Engagement mode",
        "Product-specific visual thesis",
        "First-viewport thesis",
        "Approved visual target",
    ):
        assert required in contract
```

**Done when:** the stub fails for the missing new contract before T2 and the completed targeted test suite passes after T3.

### T2: Creative Direction produces the product-specific visual contract without optional dependencies

**Depends on:** T1

**Touches:** `packs/experience-design/.apm/skills/creative-direction/SKILL.md`, `packs/experience-design/.apm/skills/creative-direction/references/grounding.md`, `packs/experience-design/.apm/skills/creative-direction/references/explore.md`, `packs/experience-design/.apm/skills/creative-direction/references/visualize.md`, `packs/experience-design/.apm/skills/creative-direction/references/converge.md`, `packs/experience-design/.apm/skills/creative-direction/references/refusals.md`, `packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md`

**Tests:**

- Goal-based construction assertions for AC-0001–AC-0016 and AC-0019 read the shipped files and verify all four mode definitions, mode/genre separation, the four output fields, honesty and provenance rules, optional-input fallback, and absence of banned dependencies or universal style restrictions.
- Contract coverage names AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, and AC-0019 explicitly so every accepted behavior has a construction owner.
- Retention assertions compare the three route names, five operation headings, fifteen template axes, six-axis divergence threshold, counterfactual check, and quality-floor precedence against their established owners (AC-0017).

**Approach:** keep route selection and the concise input/output contract in `SKILL.md`; place operation-specific method in existing references; keep the durable field schema in the template.

**Done when:** T1's completed contract matrix passes and no excluded file appears in the diff.

### T3: Skill evals exercise specificity, fallback, honesty, and retained behavior

**Depends on:** T2

**Touches:** `packs/experience-design/.apm/skills/creative-direction/evals/evals.json`, `packs/experience-design/.apm/skills/creative-direction/evals/eval_queries.json`, `packs/experience-design/tests/skills/creative-direction/test_contract.py`

**Tests:**

- Goal-based checks for AC-0003–AC-0008, AC-0011, AC-0012, AC-0015, AC-0017, and AC-0019 validate new eval cases for a product-specific surface, a direct-answer fallback run, and a generic or unsupported-evidence refusal.
- Retained cases continue to cover `inherit`, `originate`, candidate distance, audience-world referents, and `refine`.

**Done when:** the eval JSON parses, the construction suite proves the required new and retained case inventory, and no case relies on an uninstalled pack or unavailable visual tool.

### T4: The published pack and guide agree with the new behavior

**Depends on:** T2, T3

**Touches:** `guides/experience-design/how-to/establish-design-intent.md`, `packs/experience-design/pack.toml`, `packs/experience-design/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `docs/product/changelog.md`, `docs/specs/creative-direction-contract/notes/verification-ledger.md`

**Tests:**

- Goal-based checks for AC-0018 run the targeted guide-agreement suite, deep catalogue lint, catalogue verification, projection regeneration and zero-drift comparison, and matching-version assertions.
- Visual / manual QA invokes the installed skill with direct answers and no optional upstream or visual capability, then records the observable output against AC-0001, AC-0003, AC-0005, AC-0007, AC-0008, AC-0012, and AC-0016.
- Repository gates run `make lint-ruff lint-mypy` after the smallest targeted suites.

**Done when:** all targeted tests and gates are green, the manual result is recorded, pack and plugin versions match, the marketplace projection is current, and the changelog carries the consumer-visible highlights.

## Rollout

The Markdown and JSON sources ship in the next Experience Design patch release. Rollback is a normal source revert; there is no migration, infrastructure, persistent state, or external deployment sequence.

## Risks

- Adding every rule to `SKILL.md` would make the always-loaded body harder to use; progressive disclosure must keep operation-only detail in references.
- A keyword-only construction test could pass while behavior remains vague; eval rubrics and the manual invocation cover the judgment-heavy contract.
- Tightening category-default detection could become an accidental style ban; the earned-pattern rule and negative construction assertions protect that boundary.
- Generated marketplace output can drift from source metadata; regeneration and zero-drift verification close that gap.

## Changelog

- 2026-09-27: specification approved by `repository-owner`.
- 2026-09-27: execution plan approved by `repository-owner`.
