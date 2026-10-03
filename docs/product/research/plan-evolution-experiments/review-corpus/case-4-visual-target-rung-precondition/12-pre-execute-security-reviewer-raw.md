## Concerns

**1. Candidate-executing subprocesses are capped but not isolated from environment or egress.** `docs/specs/plan-evolution-experiments/spec.md:365-368`, `docs/specs/plan-evolution-experiments/plan.md:64-66`, `docs/specs/plan-evolution-experiments/plan.md:133-136`. A prompt-injected worker can put code in a candidate that the fixed hidden-oracle, regression, or repair command executes; without an acceptance criterion requiring a secret-free environment, denied network egress, and protected-path/read confinement for that subprocess, the candidate can read controller environment or injected hidden assets and leak them through network or retained output before the privacy screen sees them. Fix: Candidate, grading, regression, and repair commands must run under an explicit secret-free environment, denied network/egress, confined readable and writable roots with protected-path denial, and fail-closed terminal accounting when any of those properties cannot be enforced or observed, in addition to the existing no-shell, timeout, output, artifact, and cleanup caps.

## Not checked

- Did not run SAST, SCA, secret scanning, dependency scanners, or fuzzing; this was a spec-stage reasoning review.
- Did not launch or pentest live Codex workers, execute candidate code, inspect credentials, browser profiles, protected configuration, or verify the managed permission profile; this pass reviewed whether the spec and plan define required controls.
- Did not review implementation diffs or runtime code paths outside the spec and plan because this is a pre-execute secure-design review.
- Did not receive the boundary-specific `path-and-file`, `llm-agent`, or `exceptional-conditions` checklist module bodies in the brief; applied the universal method and repository security architecture instead.
