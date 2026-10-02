# Catalogue technical documentation architecture

- **Slug:** `catalogue-wave6-technical-docs-ia`
- **Status:** Accepted
- **Accepted:** 2026-10-02 by eugenelim, lifecycle owner. Basis: explicit owner direction to refresh, de-risk, and apply the needed reviews; the recorded de-risking verdict survived, and intent-mode review of this revision produced no malformed findings.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **De-risked:** 2026-10-02
- **Shaping-reviewed:** 2026-10-02
- **Decomposed:** no
- **Parent intent:** capability:catalogue-trust-and-adoption
- **Governed by:** [RFC-0076 D9](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)

## Outcome

- **Input (steerable):** The share of representative catalogue-authoring tasks for which an author or evaluator reaches the correct authoritative next step from the technical site without backtracking or choosing a weaker source.
- **Outcome (lagging):** Catalogue authors and evaluators can move from creating a catalogue through authoring, verification, packaging, and publication without reconstructing the path from pack-oriented or consumer-oriented pages.
- **Guardrail:** Existing consumer and pack-guide routes stay intact, the sidebar gains no independently maintained fact inventory, and generated reference text never claims semantics that the source contract does not express.

## Opportunity

The guide index now offers an Extend the catalogue learning path and the docs home links to catalogue creation, but the technical site still has no single Build a Catalogue route matching RFC-0076 D9. Authors must assemble the contract, authoring, testing, and packaging path from separate guide and reference locations.

- **Functional job:** Find the next authoritative step for creating, extending, verifying, packaging, or evaluating a catalogue from one technical documentation route.
- **Emotional job:** Know that the path is complete and current without guessing which pack-oriented guide or schema file is authoritative.
- **Social job:** Point contributors and reviewers to one maintained authoring path whose facts trace to contracts.
- **Struggling moment:** Catalogue creation and authoring guidance exists, but its entry points, schema references, integration guidance, and release steps are spread across the guide index, shared guides, generated site navigation, and raw contracts.

## Boundary

This intent owns the Build a Catalogue information architecture: the technical-site entry route, its ordered links, and the rule that field-reference facts are generated or contract-tested where machine contracts can support them. Existing guide and contract owners keep the content and semantics of their pages; this intent links or projects them and does not restate their contracts.

The central guide renderer, pack-specific guide routes, catalogue evaluation marketing, release-integrity behavior, and publication mechanics remain with their existing owners. RFC-0076 D9 assigns only the authoring documentation route and the generated-versus-narrative reference cut here.

## Current evidence — 2026-10-02

- [`guides/README.md`](../../../guides/README.md) has an Extend the catalogue learning path with catalogue-curation, first-skill, org-stack-pack, and create-catalogue entries.
- [`docs-site/src/content/docs/index.mdx`](../../../docs-site/src/content/docs/index.mdx) links to catalogue creation under Go deeper, but it does not present the distinct Use the catalogue and Build or evaluate a catalogue routes required by RFC-0076 D9.
- The shared guide corpus already contains catalogue creation, authoring standards, pack and skill authoring, profile design, verification, packaging, and publication material. The missing work is the owned information architecture, the remaining route content, and contract-backed reference projection.
- [`catalogue-wave4-semantic-contracts-index`](../../specs/catalogue-wave4-semantic-contracts-index/spec.md) and [`documentation-entry-navigation`](../../specs/documentation-entry-navigation/spec.md) are shipped, so both declared prerequisites are complete.

## Assumptions

- Machine contracts contain enough annotations to generate a useful core of the `pack.toml` and `skill.schema.json` references; narrative owns semantics the contracts do not express.
- The existing Extend the catalogue learning path can remain a short guided route while Build a Catalogue becomes the complete reference-oriented route.
- **Knowledge surface:** the in-repository RFC, guide corpus, docs-site entry page and navigation generator, shipped prerequisite specs, tests, and product-intent corpus at revision `2f33168e489345e386977012d553f26b26cdaa8f`.

## Riskiest assumption

**The ten RFC-0076 routes form one useful author journey, and presenting them as one owned path improves task completion over the current distributed entry points.** If authors still backtrack or choose the wrong authority at the same rate, the new grouping is only a navigation label and the bet fails.

## De-risking verdict

- **Reversibility:** two-way door. Documentation grouping and navigation can be changed without migrating user data or preserving a wire contract.
- **Prototype approach:** `prototype-led`; the current guide tree is the low-cost prototype used to test the proposed route against real content.
- **What would have to be true:** The ten RFC-0076 routes form one coherent author journey, and the current site does not already make that journey easy to follow from its primary entry points.
- **Kill condition (predeclared 2026-10-02):** Kill the bet if the current technical site already exposes all ten routes through one top-level authoring path, gives the home page distinct use and build-or-evaluate choices, and traces reference facts to contracts without an independent inventory.
- **Probe:** Trace each D9 route through the current guide index, shared guide corpus, docs home, generated navigation path, and machine contracts at revision `2f33168e489345e386977012d553f26b26cdaa8f`.
- **Result:** Most underlying material exists, and the guide index has a four-step Extend the catalogue path. No top-level route assembles all ten D9 steps, the docs home offers only a lower Go deeper link rather than the two required choices, and the field-reference projection boundary remains unresolved. The kill condition did not fire.
- **Verdict:** **Survived, desk-grounded.** The content is sufficient to prototype the route and the navigation gap is current. Whether the grouping improves author success remains `to-validate` with target users.

```yaml
validation_hook:
  assumption: One Build a Catalogue path helps authors and evaluators find the authoritative next step faster than the current distributed entry points.
  kill_condition: The prototype does not outperform the current entry points; at least 4 of 5 target users must complete the creation, contract-reference, verification, and packaging tasks within three minutes each with fewer wrong-authority choices and less backtracking than the current-site baseline.
  activity: Run paired task-based navigation tests with catalogue authors and evaluators on the current site and on a low-fidelity ten-route prototype, recording completion, time, backtracking, and wrong-authority choices for each task.
```

## What the decision requires

- Add a top-level docs-site section named "Build a Catalogue" with the ten routes named in RFC-0076 D9, from Create a catalogue through Package and publish (RFC-0076 D9).
- Update `index.mdx` with distinct "Use the catalogue" and "Build or evaluate a catalogue" routes (RFC-0076 D9).
- Leave the central guide-rendering and existing pack-guide routes unchanged (RFC-0076 D9).
- Generate or contract-test sidebar facts instead of maintaining an independent inventory (RFC-0076 D9).
- Generate `pack.toml` and `skill.schema.json` field references from machine contracts where practical (RFC-0076 D9).

## Non-goals

- Rewriting the existing authoring, verification, packaging, or publication guides when their content is already current.
- Changing the central guide renderer or the existing pack-specific guide routes.
- Moving catalogue evaluation marketing, release-integrity behavior, or publication mechanics into the technical documentation feature.
- Maintaining a hand-authored sidebar fact inventory where facts can be generated or contract-tested.
- Generating narrative semantics that the machine contracts do not express.

## Open questions the RFC left

- Wave 6 determines which `pack.schema.json` fields can use schema annotations for generated references and which need manual narrative explanation (RFC-0076 OQ4).

## Decomposition

None yet. This feature intent projects to one technical-documentation information-architecture specification after acceptance; the specification owns the route inventory, navigation projection, and generated-versus-narrative reference cut.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md
- Revision: 2f33168e489345e386977012d553f26b26cdaa8f
