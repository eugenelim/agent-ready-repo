# Plan: semgrep-selftest-batching

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn — while its Status is `Drafting`
> or `Executing`. When it changes substantially (a different approach, not just
> a re-ordering), note why in the changelog at the bottom. Once it is `Done`
> and the spec is `Shipped`, the directory freezes as a unit
> (`docs/CONVENTIONS.md` § Document lifecycle).

## Approach

One file changes: `tools/test-semgrep-argv-boundary.py`. `scan(target)` — which spawns
one semgrep per target — is replaced by `scan_all(targets)`, which spawns one semgrep
over all of them and returns findings keyed by repo-relative path, containing only the
targets semgrep reports as scanned. The three test functions keep their names, their
assertions, and their output strings; they read from the mapping instead of calling
semgrep.

The one deliberate behaviour addition is that **all five targets** must now appear in
semgrep's scanned set before their findings are asserted on. The per-invocation version
checked this only for the three production scripts. Batching makes the check necessary
for the fixtures too: findings arrive keyed by path, so a key that never matches yields
an empty finding list, and a "zero findings" assertion would pass without the rule
having examined anything. Making absence-from-scanned a failure converts that whole
class of bug from a silent green into a loud red.

Path-key construction is the one place this can go wrong. Semgrep reports paths
relative to its working directory, which the script already pins to `REPO_ROOT`, so the
key is `target.relative_to(REPO_ROOT).as_posix()`. Fail-closed by construction: a
mismatch means the target is absent from the mapping, which is a failure.

Verification is mutation, not inspection — see the spec's Testing Strategy. A green run
proves nothing about a test's ability to fail.

## Tasks

### T1: The self-test proves the same things in one semgrep process

**Depends on:** none

**Touches:** tools/test-semgrep-argv-boundary.py

**Verification mode:** goal-based check, plus the mandatory mutation pass.

**Tests:** no stub (goal-based). The artifact under change is itself the test; its
construction check is the mutation pass below.

**Approach:**
- Replace `scan(target)` with `scan_all(targets)`: one `subprocess.run` invoking
  `semgrep --config <RULE> --json --quiet --metrics off <t1> … <t5>` with
  `cwd=REPO_ROOT`, unchanged in every other respect.
- Build `{repo_relative_path: [findings]}` from `results[]` grouped by `path`,
  restricted to the paths in `paths.scanned`. Keep the existing
  `RuntimeError` when semgrep produces no stdout.
- Add one helper that resolves a target to its findings and fails the named case if the
  target is absent from the scanned set; route all three test functions through it.
- Call `scan_all` once in `main()` and pass the mapping to the three test functions.
- Leave the skip-when-absent branch, the missing-rule branch, the `ok`/`fail` helpers,
  the counters, and the summary block exactly as they are.

**Done when:**
- `python3 tools/test-semgrep-argv-boundary.py` exits 0 in under 15s (baseline 29.8s).
- Exactly one `semgrep` process is spawned, confirmed by counting invocations.
- **Mutation 1:** reverting the fix in one ratcheted production script makes the test
  exit 1 naming that script.
- **Mutation 2:** neutering the rule's pattern makes the positive-fixture case exit 1.
- **Mutation 3:** corrupting the path-key construction makes the test exit 1 rather
  than passing vacuously.
- `make sast`, `python3 tools/lint-ruff.py`, and
  `python3 -m pytest tools/test_build_gate_chain.py -q` are green.

## Risks

- **A faster self-test that can no longer fail is worse than the slow one.** This is the
  whole risk of the change, and the reason three mutations gate it rather than a passing
  run. Mutation 3 targets the failure mode the refactor itself introduces.
- **`tools/` is in `SAST_DIRS`**, so this diff makes the run SAST-relevant and
  `gate-sast` executes — the intended safety property, and also why CI feedback is slow.
- Semgrep's `paths.scanned` semantics are load-bearing for the reached-the-file
  assertion. Verified by probe for the batched shape; a semgrep major-version bump is a
  re-probe point (`tools/requirements-sast.txt` pins `semgrep>=1.166,<2`).

## Changelog

- 2026-08-17: initial plan.
