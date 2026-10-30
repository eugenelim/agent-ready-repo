# Verification ledger: Windows confined write

Execution observations for the approved plan. This file is not hash-pinned; it
records how tasks were verified, not new obligations.

## T1: red evidence (2026-10-29)

Before any implementation, on the unmodified module:

- `python -m pytest packs/core/tests/skills/work-loop/test_confined_mutation_path_checked.py -q`
  ended `5 failed, 107 errors in 0.94s`. Every case that patches `_host_mode()`
  errored in its fixture, because the attribute did not exist.
- `WORK_SUPERVISOR_INTEGRATION=1 python -m pytest packs/core/tests/skills/work-loop/test_supervisor_untrusted_unsafe_host.py -q`
  ended `8 failed, 2 passed`, each failure
  `AttributeError: ... has no attribute 'race_free_mutation'`.

After implementation the same suites pass, and so does the work-loop integration
lane (4313 passed, 25 skipped).

## T1: gate placement

The plan places the untrusted-code check before dispatch. It first ran before
the installed-file pin check, which loaded supervisor modules before they were
verified and failed three `test_supervisor_pinning.py` cases. The check now runs
in `_main` after the pin check and workspace construction, and before
`check_pins`, dispatch, and every run lock. A refusal still writes nothing. On a
host without race-free writes, a pin refusal therefore takes precedence over
`untrusted-unsafe-host`.

## T2: alias roots

The plan's AC-0009 case (root given as its short-name alias, target in long
form) cannot pass a purely textual `relative_to`. In the path-checked mode the
helper keeps the lexical result when it succeeds, and otherwise resolves only
the root and retries; the target's own text is never resolved, and a root that is
a link is refused. The POSIX tests simulate the alias; the Windows job proves it.

On Windows the append holds its file open when the pre-commit hook runs, and a
directory holding an open file cannot be renamed. The Windows module therefore
accepts either outcome for the append swap: the swap lands and the append raises
`denied-rollback-failed`, or the swap is refused and the append succeeds with
exactly the bytes supplied.

## Evals

No work-loop eval covers the confined-mutation helper.

## Deferred nits

Deferred Nit (security review): superscript device names (COM¹ to COM³, LPT¹ to LPT³) are outside AC-0004's list. A device target still fails the regular-file check before any byte. Status: deferred.
