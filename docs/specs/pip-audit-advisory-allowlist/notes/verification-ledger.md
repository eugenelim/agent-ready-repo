# Verification ledger: pip-audit-advisory-allowlist

Execution observations. The approved `spec.md` and `plan.md` hold obligations;
this file holds what running the build actually produced. Not hash-pinned.

## Mutation proofs (T3's obligation)

Three mutations, each predicted in the plan to redden named cases. All three did.
The wrapper was restored byte-identical afterwards (`diff -q` against a
pre-mutation copy).

| Mutation | Predicted | Observed |
| --- | --- | --- |
| Partition treats every advisory as allowlisted and every entry as matched | cases 10, 11 | both reddened; 63 passed, 3 failed |
| Stale detector reports every entry live | cases 14, 15, 16, 17 | all reddened, plus 16a and 18; 52 passed, 14 failed |
| Version comparison switched to string ordering | case 18 | reddened; 65 passed, 1 failed |

The third is the load-bearing one. Under string comparison `"2.9.0" >= "2.14.0"`
is true, so the gate takes the retirement branch and emits `ACTION: remove this
entry` — instructing a maintainer to delete a written risk acceptance on
evidence the fix is absent, which `spec.md`'s Never-do forbids.

## Deviations from a task row's literal method

**T2 rows 11 and 13 predicted exit 1; the wrapper returns exit 2.** Observed by
driving `evaluate()` directly. Not a falsified decision — AC8's precedence rule
(exit 2 over exit 1) is *upheld*: in both inputs the entry matches nothing, which
trips AC4's retirement branch, and precedence puts the untrustworthy-verdict code
above the blocking advisory. The rows mis-predicted what the spec's own rule
implies. The assertions were initially written loose (`code in (1, 2)`,
`code != 0`) and are now pinned to 2.

**The suite grew from 33 scenarios to 38, then to 39 (85 assertions).** Post-gates
review added: duplicate-entry rejection (9a), an undecidable `fixed_in` membership
branch (19b), an empty `fix_versions` branch (19c), an include-line refusal in
`direct_requirements` (21c), a manifest-naming empty-derivation error (21d), and a
case-folded transport scrub (23c). None contradicts an acceptance criterion; each
is defensive behaviour beyond what the ACs enumerate, and each is pinned by an
assertion the recipe runs, so removing one reddens the gate. Recorded here rather
than by amendment because no settled decision was falsified.

## Defects the suite caught during implementation

- `allowed_packages = [1]` crashed a `", ".join()` over a non-string (case 21b).
- Cases 15, 16, 17 were passing by vocabulary coincidence: they asserted the word
  "remove" was absent while the wrapper said "delete". Replaced with explicit
  `ACTION: remove this entry` / `ACTION: change nothing yet` tokens.
- `_utf8_streams()` raised `AttributeError` on a redirected stream, turning a
  caller's capture into a crash. Now guarded by `hasattr`.

## Defects post-gates review caught that gates could not

- `build_env` removed only the exact upper and lower spellings of each transport
  variable. `urllib.request.getproxies_environment` case-folds every key, so
  `Https_Proxy` survived and was honoured. Measured:
  `build_env({'Https_Proxy': 'http://evil'})` returned it intact and urllib then
  reported `{'https': 'http://evil'}`. Now matched case-insensitively, like the
  `PIP_` rule already was.
- `versions_equal` returns `None` for an unorderable version, and `any()` read
  that as `False` — so `fixed_in` byte-identical to a published `2.14.0rc1`
  reported as "matches none of the fix versions the advisory publishes",
  asserting a comparison never performed. Now three branches: agrees,
  could-not-compare, decided mismatch.

## Gate evidence

| Gate | Result |
| --- | --- |
| `make sast` | exit 0 (after two earlier failures, below) |
| `tools/test-run-pip-audit-gate.py` | 39 scenarios, 85 assertions, 0 failed |
| Same suite from a different cwd | 85 passed — pins that case 27 does not pass via an unresolvable relative manifest |
| `make lint-ruff lint-mypy` | clean, 149 source files |
| `pytest tools/test_local_ci_shared_test_deduplication.py` | 51 passed |
| `tools/test-audit-requirements.py` | passed |
| Live wrapper on the real manifest | exit 0, ten acceptances printed with package, version and retirement condition |

## `make sast` failures observed, and their causes

1. **Two bandit findings in the new files.** B108 on two `/tmp/...` string
   literals in the test fixture (inert dict values — changed rather than
   suppressed), and an unmatched `# nosec B603`: the call goes through the
   injected `runner` seam, so bandit never raised B603 there, and
   `run-bandit-gate.py` fails on a suppression that matched nothing (ADR-0084).
   Fixing the second introduced a third failure — the replacement comment
   contained the literal `# nosec` token in prose and was parsed as a real
   suppression.
2. **A semgrep per-rule timeout** on
   `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`, a file not in this
   diff, at 1-minute load average 85.5 on 10 CPUs. Diagnosed by the route
   `run-semgrep-gate.py` prints: the exact invocation against that file alone
   exits 0. Load, not a budget breach.

## Digest re-pin evidence

All eight extracted Makefile surfaces recomputed from this worktree. Exactly
`sast-unleased` and `SAST_CONFIG` moved — the two this change edits. `SAST_DIRS`,
`SEMGREP_EXCLUDE`, `build-check-unleased`, `sast`, `gate_verdict` and
`gate_verdict_calls` reproduced byte-identically against their existing pins, so
the new values supersede live pins rather than stale ones.
