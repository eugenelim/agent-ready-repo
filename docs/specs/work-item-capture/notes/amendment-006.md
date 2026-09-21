# Amendment 006 — a stale cross-feature pin, and a release path that does not exist

**Authorised by:** eugenelim, 2026-09-20
**Against:** approved_plan_hash 2af3e2ae303c

Two corrections, both landing on T8, both found before T8 ran.

## 1. The blocker-list pin belongs to another spec and is now stale

`docs/specs/ride-along-admission-test/` pins a clause byte-for-byte across
every site that carries it, including this sentence:

> a defect blocked on a decision, an instrument, or elapsed time is captured

Three blockers. **This spec settles four** — decision, instrument,
elapsed-time and dependency — and its criteria refuse anything outside that
set. T6 widened the shipped skill prose to match, correctly, and broke the
pin: `test_ride_along_admission_test.py::test_capture_section_routing_bullet`
now fails.

This is our regression, not a pre-existing one. It was reported as
pre-existing relative to T7, which is true and is not the same claim.

**The pin is doing its job.** It caught a cross-feature behaviour change
neither spec's review could have: ours never read that suite, and that spec
predates ours. The resolution is that the pin is stale, not that our change
is wrong — the shipped prose is now correct and the frozen copy is not.

Two sites carry the clause and both need the fourth blocker:
`docs/specs/ride-along-admission-test/spec.md` and
`packs/core/tests/pack/test_ride_along_admission_test.py`.

Widening the blocker list does not touch what that spec is *about* — it pins
the routing clause for ride-along eligibility, and the blocker enumeration is
incidental to that subject.

## 2. T8's release path names a file that does not exist

T8's `Touches:` lists `packs/core/CHANGELOG.md`. **No pack-level changelog
exists anywhere in this repository.** Checked against a real core-pack
version bump, which touched `docs/product/changelog.md`,
`packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` — and no
pack changelog.

T8 would have blocked on its own release obligation. Found by checking the
last task's targets exist before dispatching it, rather than after.

## The amendment

T8's `Touches:` drops the nonexistent pack changelog and gains:
- `docs/product/changelog.md` — the real release-history home;
- `docs/specs/ride-along-admission-test/spec.md` and
  `packs/core/tests/pack/test_ride_along_admission_test.py` — the two sites
  carrying the stale pin.

T8 updates both pinned sites to the four-blocker wording and records in the
ride-along spec's own notes why its pin moved, so that spec's owner inherits
the reason rather than a silent edit.

## Standing instruction this produces

The audit after amendment 004 asked whether each task owned a place to put
its proof. It did not ask whether the paths a task names **exist**. Both
questions belong in the same check, and a plan's file list should be
validated against the tree at approval rather than at execution.
