## Main-loop result
**1. [concern] finding-1: Candidate-executing subprocesses lack explicit environment, egress, and read confinement.** `docs/specs/plan-evolution-experiments/spec.md:365`. AC-0007A requires shell-free argv, isolated cwd, timeout, bounded output/artifacts, process-tree cleanup, and capped status, while the plan repeats those caps at plan lines 64-66 and then runs oracle/regression grading against worker candidates at plan lines 133-136; the cited command surface therefore exists, and the current acceptance text does not require a secret-free environment, denied network/egress, or confined readable roots for candidate, grading, regression, and repair subprocesses. The security authority applies because the same spec treats agent output as untrusted data and forbids exposing hidden tests, grading commands, protected configuration, or credentials to workers; candidate-authored code executed by those subprocesses can reach controller environment, protected files, or injected hidden assets unless the subprocess boundary denies it, and bounded output/privacy screening happens after possible read or egress. Proposed mechanism: adequate. Fix: extend the command-execution acceptance criterion and plan constraints so every candidate, grading, regression, and repair subprocess runs with an explicit secret-free environment, denied network/egress, confined readable and writable roots, protected-path denial, and fail-closed terminal accounting whenever any property cannot be enforced or observed.

## Refuted audit
None.

## Indeterminate audit
None.
