# Spec: Site CI contract closure

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0082](../../rfc/0082-test-ownership-boundaries-and-inclusion.md), [ADR-0086](../../adr/0086-split-the-sast-gate-into-its-own-ci-job.md), [`spec/ci-gate-parallelization`](../ci-gate-parallelization/spec.md) AC16
- **Brief:** docs/product/briefs/tech-site-completion.md
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
- Assert workflow source shape without proving it by seeded deletion — a bare
  presence assertion does not detect removal (see the register's
  `site-test-source-substring-assertions` entry).
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

- [x] Required CI executes these seven modules (satisfied before this spec, by
  the shipped `docs/specs/build-check-coverage-gaps/spec.md` AC1; they run
  unconditionally in `gate-main`, which branch protection requires by name
  alongside `make build-check`, `gate-sast`, and `gate-export-boundary`):
  `tools/test_validate_guides.py`,
  `tools/test_check_guide_index.py`,
  `tools/test_catalogue_navigation.py`,
  `tools/test_documentation_entry_links.py`,
  `tools/test_build_site_link_rewrites.py`,
  `tools/test_check_rendered_site_links.py`, and
  `tools/test_build_site_routing.py`.
- [x] A standing construction test parses `build-check.yml` and fails when any of
  the seven modules is absent, misspelled, neutered, or placed outside the
  `gate-main` job specifically (`gate-main` is a required context; the
  `build-check` aggregator is a separate required context that runs no pytest).
  "Neutered" covers at least `continue-on-error`, a step-level `if:`, and a
  `working-directory:` redirection. It lives with the other `build-check.yml`
  posture assertions in `tools/test-build-check-workflow.py`, which the
  aggregator invokes — not inside `gate-main`, the job it protects. Each of the
  seven names is proven by seeded deletion against an in-memory copy, because a
  bare presence assertion cannot detect removal.
- [x] `tools/check-docs-contrast.py` has focused tests for light and dark pairs,
  the 4.5:1 threshold boundary (asserted on the comparison's inclusivity through the
  seam `main()` uses, plus the tightest real pairs either side; measured: no
  gray-on-gray 6-hex pair and no shipped-palette pair lands exactly on 4.5), each
  named invalid-input case — malformed hex, legal-but-unsupported three-digit
  shorthand, an unresolvable `var()` chain, and a palette that cannot be read or
  decoded — and non-zero exit on failure.
  Each refuses with a diagnostic rather than an uncaught traceback.
- [x] Required CI runs the contrast checker and fails when a registered pair is
  below 4.5:1.
- [x] The gate is never skipped for a relevant change, because `build-check.yml`
  carries no `paths:` filter on either trigger and so runs on every pull request
  to `main` — verified by asserting the *absence* of a `paths:` key under both
  `on.pull_request` and `on.push`. Adding path filters is prohibited, not merely
  unnecessary: the workflow's jobs are required contexts by name, so on a PR
  touching none of the filtered paths the workflow would never run, the required
  checks would never report, and the PR would be permanently unmergeable.
- [x] Every module and script the new CI step names is reachable from `make ci`,
  proven by `tools/lint-ci-parity.py`'s coverage layer. Set-equality between one
  local command and one CI job is deliberately NOT claimed:
  `docs/specs/ci-gate-parallelization/spec.md` AC16 settled that parity became
  one-to-many when the workflow split into three jobs, with addressability as the
  replacement invariant, and `make build-check` runs no pytest at all.
- [x] No new dependency is introduced and existing test ownership remains
  consistent with RFC-0082.

## Assumptions

- Technical: the seven modules already run in BOTH the local aggregate test
  target and `gate-main`, a required context — the intake assumption that they
  were absent from CI was false. What is absent is a standing construction test
  pinning that fact, and any CI or Make invocation of
  `tools/check-docs-contrast.py` (source: `Makefile` test target and
  `.github/workflows/build-check.yml` `gate-main`; branch-protection contexts read
  from the GitHub API on 2026-08-17).
- Technical: the dependency-free contrast checker currently passes all
  registered light and dark pairs (source: `tools/check-docs-contrast.py`
  probe during intake).
- Product: required CI, not optional reporting, is the accepted outcome
  (source: user confirmation 2026-08-17).
- Process: catalogue and pack test ownership follows RFC-0082 (source:
  `docs/rfc/0082-test-ownership-boundaries-and-inclusion.md`).
- Process: no dependency is added for this programme (source:
  `docs/product/briefs/tech-site-completion.md`).
