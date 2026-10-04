# Spec: Silent taxonomy domain is an upstream gap

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0139, ADR-0130
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

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

A frontend implementer handed a resolved token taxonomy that says nothing about a
domain the surface needs holds that axis and routes it to the taxonomy's owner,
instead of inventing values. Success is that the installed frontend rules name
this third gap source, every surface that restates the gap sources agrees, and
both the roster walk and a model-eval case exercise the hold.

## What Changes

- The `gap-sources` and `gap-record-contents` rows — `packs/frontend-engineering/.apm/skills/frontend-engineering/references/visual-observation.md`.
- The unresolved-domain sentence in step 2 and the upstream-gap routing paragraph — `packs/frontend-engineering/.apm/skills/frontend-engineering/SKILL.md`.
- The gap-source paragraph and its routing sentence — `guides/frontend-engineering/how-to/read-the-design-handoff.md`.
- A `silent-domain` fixture and walk case, explicit `needed_domains` on every existing fixture whose taxonomy resolves, and Shape and containment and Spatial structure sections in the existing checkout taxonomies — `tests/roster/test_visual_handoff_golden_path.py`, `tests/roster/fixtures/visual-handoff-golden-path/`.
- A `visual-authority-silent-domain` eval case, and Typography, Shape and containment, and Spatial structure values in the two golden build prompts — `packs/frontend-engineering/.apm/skills/frontend-engineering/evals/evals.json`.
- A frontend-engineering patch release.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The gap sources ADR-0130 D2 fixed change | `docs/adr/0139-a-taxonomy-silent-domain-is-an-upstream-gap.md` | eugenelim | ADR-0139 `Accepted`; ADR-0130 `Superseded in part: ADR-0139 D2` | both records agree |
| User-facing promise | Adopters read the gap sources in the how-to | `guides/frontend-engineering/how-to/read-the-design-handoff.md` | pack maintainer | three sources named | guide test green |
| Release history | Shipped pack content changes | `docs/product/changelog.md` | pack maintainer | a free-standing frontend-engineering section at the bumped version | entry present |

## Agent Rules

### Always do

- State the third gap source in the installed rule table first; every other
  surface restates that table.
- Keep the frontend `SKILL.md` body within the budget AC-0003 names.

### Ask first

- Any change to how `design-system` writes a taxonomy.
- Any new operation kind beyond `taxonomy-supply-required` and
  `domain-completion-required`.

### Never do

- Let a lower rung, the fallback, or a local premise fill a taxonomy-silent
  domain.
- Add a rung, a dependency, a module boundary, or a top-level directory.
- Edit ADR-0130's prose; only its `Superseded in part` field changes.

## Testing Strategy

- **The rule and its restatements (AC-0001, AC-0002, AC-0003, AC-0004, AC-0012):** TDD
  over the installed and source rule text, extending the existing pack and
  roster tests.
- **The walk (AC-0005, AC-0006, AC-0011):** TDD through the roster golden-path
  walk over the fixtures, with an in-test mutation for AC-0006.
- **The eval cases (AC-0007, AC-0008):** TDD over the installed `evals.json`;
  running them against a model is report-only and outside this contract.
- **Decision record and release (AC-0009, AC-0010):** goal-based checks.

## Acceptance Criteria

- [x] **AC-0001.** The installed `visual-observation.md` `gap-sources` cell
      names a third source — a resolved `tokens/<slug>.md` that supplies no
      value the surface needs in a domain and does not record that domain
      unresolved — and states the test for need: the implementation would
      otherwise set a value in that domain.
- [x] **AC-0002.** The installed `gap-record-contents` cell assigns
      `domain-completion-required` to a domain the taxonomy left silent as well
      as one it recorded unresolved, names no third operation kind, and the
      installed `gap-outcome` cell routes a silent domain to whoever produced
      the taxonomy.
- [x] **AC-0003.** The frontend `SKILL.md` step-2 rule says a domain the
      taxonomy leaves silent is held as an upstream gap, and the `SKILL.md`
      body stays at or under 968 lines.
- [x] **AC-0012.** The frontend `SKILL.md` upstream-gap paragraph and the
      `read-the-design-handoff.md` routing sentence each say that a domain the
      taxonomy left silent routes to whoever produced the taxonomy, keep the
      recorded owner or operation as the route for the other sources, and name
      no specific upstream skill.
- [x] **AC-0004.** `read-the-design-handoff.md` names the silent-domain source
      alongside the two existing sources, and the roster adopter-prose test
      asserts all three.
- [x] **AC-0005.** On a `silent-domain` fixture — a resolved direction, a
      taxonomy that lists Typography in its Authority table but gives no
      Typography values, and `needed_domains` including Typography — the walk
      holds Typography under `domain-completion-required`, sources every other
      needed domain from the taxonomy, loads no fallback, and writes the gap
      record `{"axes held": ["Typography"], "operation kind":
      "domain-completion-required"}`.
- [x] **AC-0006.** Every existing walk fixture whose taxonomy resolves declares
      `needed_domains`, and the walk holds none of them silent; removing the
      `confirmed` fixture's Typography section in-test makes the walk hold
      Typography as silent.
- [x] **AC-0011.** The `silent-domain` fixture's taxonomy also gives no
      Graphic language values, Graphic language is not in its
      `needed_domains`, and the walk does not hold it.
- [x] **AC-0007.** The installed `evals.json` carries a
      `visual-authority-silent-domain` case whose prompt states a resolved
      taxonomy silent on typography; it carries an assertion beginning
      `Does not` that names inventing a value for the silent domain, an
      assertion not beginning `Does not` that names holding typography as an
      upstream gap, an `expect.output_contains` listing
      `domain-completion-required` and one resolved colour value from the
      prompt, and an `expect.output_excludes` listing the same fallback colour
      values the golden cases exclude.
- [x] **AC-0008.** The `visual-golden-path-confirmed-values` and
      `visual-golden-path-unconfirmed-target` prompts state the resolved values
      of their scenario fixture's Typography, Shape and containment, and
      Spatial structure sections, and the roster test checks each value against that fixture's
      taxonomy.
- [x] **AC-0009.** ADR-0139 carries `Status: Accepted`, and ADR-0130 carries
      `Superseded in part: ADR-0139 D2`.
- [x] **AC-0010.** `frontend-engineering` carries one patch version above its
      version on `main` at merge — `0.4.4` against today's `0.4.3` —
      identically in `pack.toml`, `.claude-plugin/plugin.json`,
      `.claude-plugin/marketplace.json` and a free-standing changelog heading,
      and `agentbundle catalogue lint --root . --deep` and
      `agentbundle catalogue verify --root .` exit zero.

## Follow-ons

none

## Assumptions

none
