## Concerns

**1. Holdout prompts are outside `AC-0024` frame checks.** `docs/specs/plan-evolution-experiments/spec.md:579-584`, `docs/specs/plan-evolution-experiments/plan.md:810-819`. T15 still has holdout starts, but its task checks do not require the typed untrusted-data frame, controller-owned provenance, body/frame/full-prompt/schema digest binding, or authority-exclusion gate that AC-0024 only names for T13/T14, so an instruction-shaped holdout packet could contaminate external validation before output screening catches the aftermath. Fix: Extend the AC-0024 acceptance criterion and T15 tests/done gate to every holdout worker prompt, or explicitly state T15 has no worker-visible document/source body; launch must refuse when the frame, digest, or authority-exclusion check fails.

## Not checked

- Did not run SAST, dependency, secret, or CVE scanners; those are scanner-owned and outside this reasoning-only spec review.
- Did not verify provider transport behavior, served model identity, or runtime tool isolation live; this review checked whether the spec and plan require the right evidence.
- Did not inspect ignored `.context` handoff bytes or future model outputs; those are execution artifacts, not present implementation evidence.
