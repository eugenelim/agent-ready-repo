# Improve product-documentation page design across code surfaces

- **Slug:** product-documentation-page-design
- **Level:** feature
- **Owner:** Product documentation maintainers
- **Status:** Draft

## Outcome

Product documentation can be created or improved for any code-backed product
surface without assuming the surface is an ARR pack.

## Boundary

- Generalize source discovery and page-design guidance in
  `author-product-docs` beyond pack READMEs and pack journeys.
- Keep pack documentation as one supported case rather than the default model.
- Add evaluation coverage for at least one non-pack code surface before
  changing the skill contract.
- Do not roll this broader skill change into the current workflow-page slice.

## Non-goals

- Do not change `author-product-docs` as part of the workflow-page slice.
- Do not remove or de-prioritize pack documentation support.
- Do not require one page template for every code surface.

## Riskiest assumption

The skill can infer a product surface and its documentation obligations from
heterogeneous code repositories without becoming vague or over-prescriptive.

## Unresolved questions

- What minimum evidence lets the skill identify a product surface and its
  user-facing behavior from code?
- Which page-design rules belong in the main skill, supporting references, and
  evaluation fixtures?
- Which non-pack surfaces form a representative evaluation set?

## Projection

- Shape this intent before opening a delivery spec; keep the current
  workflow-page implementation independent.

## Opportunity

The current skill description and workflow are centered on pack documentation,
so they do not establish a reliable route for documenting an arbitrary
application, library, CLI, or service surface.

## Source

- Mode: chat-only
- Locator: conversation/workflow-page-contract
- Revision: 2026-09-25
- Authority: transferred-to-repository
