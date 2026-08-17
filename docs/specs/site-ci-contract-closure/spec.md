# Spec: Site CI contract closure

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0082
- **Brief:** tech-site-completion
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what done means. The implementing
> change matches this spec or updates it before merge.

## Objective

Contributors receive a required CI failure whenever catalogue navigation,
guide indexing, documentation entry links, site routing, rendered links, or the
registered docs color pairs regress. The same focused tests remain runnable
locally without adding a dependency or silently relying on a broad test target
that required CI does not execute.

## Boundaries

### Always do

- Execute the exact seven registered Python test modules as required CI tests.
- Keep the contrast checker dependency-free and test its pass and fail paths.
- Trigger the gate whenever its implementation, fixtures, workflows, or
  relevant site inputs change.

### Ask first

- Change the accepted 4.5:1 contrast threshold or registered color-pair set.
- Remove or replace one of the seven registered test modules.
- Move test ownership across the RFC-0082 boundary.

### Never do

- Claim coverage because a test appears only in a local Make target.
- Add a package or JavaScript dependency for contrast verification.
- Weaken a failure to advisory, continue-on-error, or source-shape-only proof.

## Testing Strategy

- CI inclusion and path-trigger behavior use TDD construction tests over the
  workflow because the invariant is deterministic and easy to seed broken.
- The seven behavioral modules execute as goal-based CI checks.
- Contrast math and CLI exit behavior use TDD with known passing, boundary, and
  failing color pairs.
- The final required job is exercised through the same command contributors run
  locally.

## Acceptance Criteria

- [ ] Required CI executes these seven modules:
  `tools/test_validate_guides.py`,
  `tools/test_check_guide_index.py`,
  `tools/test_catalogue_navigation.py`,
  `tools/test_documentation_entry_links.py`,
  `tools/test_build_site_link_rewrites.py`,
  `tools/test_check_rendered_site_links.py`, and
  `tools/test_build_site_routing.py`.
- [ ] A construction test parses the required workflow and fails when any of
  the seven modules is absent, misspelled, advisory, or placed outside the
  required job.
- [ ] `tools/check-docs-contrast.py` has focused tests for light and dark
  pairs, the 4.5:1 boundary, invalid color input, and non-zero exit on failure.
- [ ] Required CI runs the contrast checker and fails when a registered pair is
  below 4.5:1.
- [ ] Workflow path filters include the seven tests, their production modules,
  the contrast checker and its test, docs palette sources, and the workflow
  itself.
- [ ] The focused local command and required CI command select the same test
  modules and contrast contract.
- [ ] No new dependency is introduced and existing test ownership remains
  consistent with RFC-0082.

## Assumptions

- Technical: the seven modules exist in the local aggregate test target but not
  as required CI steps (source: `Makefile` and `.github/workflows/build-check.yml`).
- Technical: the dependency-free contrast checker currently passes all
  registered light and dark pairs (source: `tools/check-docs-contrast.py`
  probe during intake).
- Product: required CI, not optional reporting, is the accepted outcome
  (source: user confirmation 2026-08-17).
- Process: catalogue and pack test ownership follows RFC-0082 (source:
  `docs/rfc/0082-test-ownership-boundaries-and-inclusion.md`).
- Process: no dependency is added for this programme (source:
  `docs/product/briefs/tech-site-completion.md`).
