# Verification ledger: code-intelligence-standalone

## T1: A user-scope install succeeds with no packs installed

- Date: 2026-10-10
- Tests: `packs/code-intelligence/tests/pack/test_manifest.py` red before the
  manifest edit (2 failed, 10 passed), green after (12 passed, 0 failed).
- Lint: `make lint-ruff lint-mypy` passed.
- Manual install, run from an empty git repository with `HOME=<tmp>/home`:
  `agentbundle install --pack code-intelligence --scope user --adapter claude-code <catalogue>`
- Exit code: 0
- Installed skill path: `<tmp>/home/.claude/skills/code-intelligence/SKILL.md`

## T2: Skill, references, and agents carry the baseline with no Core role

- Date: 2026-10-10
- Commit: `4bd63713c`; follow-up skill fixes from T3 runs: `726e79f6f`,
  `a38693e46`, `9bd0c07ab`.
- Tests: `packs/code-intelligence/tests` 189 passed at `4bd63713c`; 199 passed
  at `9bd0c07ab`.
- Lint: `make lint-ruff lint-mypy` passed.

## T3: Eval cases name no Core and pass with only code-intelligence

- Date: 2026-10-10
- Commits: `7cfc3764e` (eval rewrite, `test_core_surface.py`), `044a3c947`
  (eval 7 hop assertion).
- Tests: `packs/code-intelligence/tests` 199 passed.
- Graded runs (interim): see [`eval-runs.md`](eval-runs.md). The four
  composition cases each have a full-pass run at `9bd0c07ab`, recorded before
  the case 3 fix; that fix voids them, and T3 closes on reruns at its final
  skill commit. Eval 7 has none (3/4 in
  four runs) and moves to the regression set by owner decision, 2026-10-10.
- Regression runs (interim): failures in cases 1, 5, 8, and 9 match the
  origin/main skill at `cbcb32d73`. Case 3 is a regression against that
  baseline and returns to T2 by owner decision, 2026-10-10.
- Runs at `2595da79c` (case 3 fix; superseded by the post-review fix round): the four composition cases pass
  every assertion (behavior grader `[ok]` for all four); case 3 passes 4/4 in
  two runs; failures in cases 1, 5, and 8 match origin/main at `cbcb32d73`;
  eval 7 is not gated; case 9's single assertion-3 miss passed in two reruns
  and is accepted by owner decision, 2026-10-10. Details:
  [`eval-runs.md`](eval-runs.md#runs-at-2595da79c-superseded-by-the-post-review-fix-round).
- Final runs at `4a2e484bf` (post-review fix round): the four composition
  cases pass every assertion (behavior grader `[ok]`); cases 1, 3, 4, and 9
  pass; the failures in cases 5 and 8 match origin/main at `cbcb32d73`; eval 7
  is not gated. Details:
  [`eval-runs.md`](eval-runs.md#final-runs-at-4a2e484bf-t3-closes-on-these).

## T4: Docs, version, changelog, and projection updated

- Date: 2026-10-10
- Commit: `dfaca931a`.
- Tests: `packs/code-intelligence/tests` plus
  `tools/test_marketplace_envelope_parity.py` 262 passed; the changelog
  projection tests in `tools/test_build_site_routing.py` passed.
- `agentbundle catalogue lint --root . --deep` and `catalogue verify --root .`
  passed; a second `catalogue self-host --root . --write` produced no diff.
- README and first-session tutorial read whole: neither requires `core`.
