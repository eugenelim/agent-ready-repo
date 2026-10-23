# Red proof discriminates a stub that ran

- **Slug:** `red-proof-discriminates-a-stub-that-ran`
- **Status:** Draft
- **Kind:** outcome
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:work-loop-delivery-efficiency

## Outcome

- **Steerable input:** Make the supervisor's red proof rest on evidence the stub
  actually ran, rather than on its exit code alone.
- **Lagging outcome:** A stub command that cannot start is refused with a stable
  code instead of being recorded as a failing test.
- **Guardrail:** The control observation must not be conditionable by the stub
  run it checks, and an unavailable control refuses rather than admits.

## Opportunity

`_all_red` in `_supervisor_tdd.py` compares each stub's exit code against its
declared `red_exit` and nothing else. Any failure to start lands on the same
code: a missing module, a bad `{path}` substitution, a conftest that raises at
import, a stub file that is itself the program and is absent.

This was observed, not predicted. A launch change dropped the interpreter's
packages, `python -m pytest` answered `No module named pytest` and exited 1, and
the supervisor admitted the red proof. The same run silently disarmed the
conftest fixtures of VI-5030 and VI-5031, because the attack they plant never
executed either. Forged evidence is the class
`execution-supervisor-attempt-security` exists to stop, so the gap is in scope
for the programme even though that slice deferred it.

## Boundary

- Includes the evidence rule for a red proof, its stable refusal code and
  security event, and the budget the extra observation spends.
- A first candidate, not yet a decision: run the same command on the same tree
  with the stub file absent, and refuse when that also gives a declared red
  exit. Four gaps were found in it and any design must answer them — the stub
  shares and may write the scratch tree, so it can condition the control run;
  the control run doubles launches under a budget that must stay below
  `run_lock_stale_seconds`; a task with several stubs needs a rule for which
  files are absent; and a control run that yields no exit code must refuse.
- Excludes the launch route, which is
  [`supervisor-launch-routing-for-plan-authored-commands`](supervisor-launch-routing-for-plan-authored-commands.md).

## Owner

- eugenelim, Platform Core maintainer.

## Unresolved questions

- Does a control observation give enough signal, or must the stub emit positive
  evidence that its assertion executed?
- Which budget pays, and does the relation to the run lock's stale window still
  hold when launches double?
- Is a stub file that is present but never executed — a collection error, a
  runner usage error — inside this intent or a named residual risk?

## Source

- Mode: repo-origin
- Locator: docs/specs/execution-supervisor-attempt-security/spec.md
- Authority: repo-origin
