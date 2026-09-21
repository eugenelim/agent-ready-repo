# T8 completion evidence

**Task:** the contract change is documented and released.
**Completed:** 2026-09-20. Amendment 006 corrected its file list first.

## What shipped

- An adopter reference guide, an architecture entry describing the record
  class and the validation **as delivered** — the reasoning tier alone, with
  the mechanical tier named as not built — and a security entry carrying the
  complete gap list with **no count**, per the canonical Durable Outputs row.
- The stale three-blocker pin updated at both sites the ride-along spec
  carries it, with the reason recorded in that spec's own ledger so its
  owner inherits it rather than finding a silent edit.
- Version bumped to 2.26.22 across the pack manifest and the plugin
  manifest, one topmost changelog entry in the product changelog. There is
  no pack-level changelog in this repository.
- Eval coverage for the new kind and a command refusal.

## Corrections the controller made after the report

Two things the report called pre-existing were **caused by this delivery**:

- **A pack test reaching outside its pack.** T6's comparison test read the
  repository spec from under `packs/core/tests/`, which a lint forbids.
  Moved to the roster suite and its path depth recalibrated; three tests
  pass and the boundary lint is clean.
- **The register finding.** Reported as pre-existing on the backlog
  registration. It is not: the entry was `Draft` in `[backlog].open`, which
  is valid, and approving the spec is what made the pairing impossible.

A third finding it raised was real and outside amendment 006's scope: a
**third** site carrying the three-blocker wording, in a core-pack guide,
test-pinned nowhere and therefore caught by no gate. Fixed, and a sweep
confirms no site still carries the old wording. That is the second amendment
in this run whose sweep under-counted the homes, both times missing the one
nothing mechanically checks.

## Verification

- project-knowledge suite: **322 passed**. Ride-along and relocated tests:
  19 passed. `lint-pack-test-boundary`: clean. Contract parity: 18 files
  byte-identical.
- All **47 criteria** owned by exactly one task and cited by an implementing
  test, including the three amendment 005 moved into T7.

## Open, recorded deliberately

One roster check fails: the register has no honest slot for a spec that is
approved and implemented but unmerged. See the transient note in
`resolve-vs-surface.md`.
