## Main-loop result

**1. [concern] 1: Holdout prompts are outside AC-0024 frame checks.** `docs/specs/plan-evolution-experiments/spec.md:579`. AC-0024 limits the frozen typed untrusted-data frame, controller-owned provenance, authority exclusion, and body/frame/complete-prompt/schema digest rejection to T13/T14 worker prompts, while the same spec still freezes holdout plan-author and construction-response starts and the plan's T15 tests collect the holdout validation set without the equivalent pre-launch frame, digest, and authority-exclusion refusal. The spec's general worker-body framing rule makes that authority applicable, and holdout packet content is reachable through those holdout worker prompts before output screening. Proposed mechanism: adequate. Fix: extend AC-0024 and T15 tests/done gate to every T15 holdout worker prompt, or state and prove that no T15 worker-visible document or source body exists; launch must refuse on frame, digest, or authority-exclusion failure.

## Refuted audit

None.

## Indeterminate audit

None.
