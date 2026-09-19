# Verification ledger — ride-along-admission-test

Execution observations. Not contract; the spec and plan are.

## 2026-09-19 — T1: the control is red, and AC23 cannot be checked from a pack test

**Observed.** `packs/core/tests/pack/test_ride_along_admission_test.py` was
created with 16 test functions covering AC1–AC7, AC9–AC13 and AC20–AC23.
`python3 -m pytest packs/core/tests/pack/test_ride_along_admission_test.py -q`
→ 16 failed, 0 errors, every named function present as an `AssertionError`
rather than a collection error. `python3 -m pytest packs/core/tests/pack/ -q`
→ the sibling 234 tests still pass.

**Plan error found.** `python3 tools/lint-pack-test-boundary.py` → exit 1, 3
failures, check `pack-tests-stay-in-pack`:

```
FAIL: packs/core/tests/pack/test_ride_along_admission_test.py:39: pack test reaches above packs/core via `PACK_ROOT.parent.parent`
FAIL: packs/core/tests/pack/test_ride_along_admission_test.py:40: pack test reaches above packs/core via `REPO_ROOT / 'guides' / 'core' / 'explanation' / 'core-pack.md'`
FAIL: packs/core/tests/pack/test_ride_along_admission_test.py:464: pack test reaches above packs/core via `GUIDE`
```

AC23 reads `guides/core/explanation/core-pack.md`, which is outside
`packs/core/`. The rule is unconditional and the lint runs in `docs.yml` on any
`packs/**` change. Only AC23 trips it; AC22's `evals.json` read stays inside the
pack and is clean. The plan's `Design (LLD)` § Component decomposition and T1's
`Touches` both pinned exactly one new file, and the spec's Agent Rules said the
test "lives beside the existing core pack tests" — so the correction is a
contract amendment, not an in-place fix.

**Method note.** The first attempt to verify this blocker ran the lint through
`| tail -8`, which truncated the three FAIL lines and reported `tail`'s exit
status as 0. The lint was re-run unfiltered before the finding was accepted.

**Owner decision, 2026-09-19 (eugenelim).** Amend by the split precedent in
commit `b14725c01`: AC23's check moves alone to
`tests/roster/test_capture_rename_guide.py`, registered per `tests/AGENTS.md`
with its named step placed above the bulk `pytest tests/ -q` step so it can
report; AC1–AC22 stay in the pack-local file unchanged. AC23's substance is
unchanged. Rejected: verifying the guide by a delivery-time grep (loses the
standing control), and deferring the guide to a follow-on (ships a renamed step
whose published documentation still uses the old name).

**Deviation accepted, T1/AC21.** `test_in_file_anchors_resolve` is scoped to
links targeting `#capture` rather than every anchor in `SKILL.md`. An unscoped
check passes today, because every existing `#capture-learnings` link resolves
against the un-renamed heading, so it could not be red for the stated reason.
The scoped form reds now and stays meaningful after the rename.
