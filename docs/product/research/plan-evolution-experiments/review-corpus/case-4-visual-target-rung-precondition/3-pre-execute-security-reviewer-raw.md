## Concerns

**1. Worker document bytes lack a prompt-authority delimiter criterion.** `docs/specs/plan-evolution-experiments/spec.md:354-363`. A repository-public or synthetic packet can contain instruction-shaped prose and be sent to Sol, Sonnet, or Opus as ordinary prompt content, letting that text compete with controller instructions before output screening catches only the aftermath. Fix: Add acceptance criteria and T13/T14 task checks requiring every worker-visible document/source body to be explicitly delimited and labelled as untrusted data with provenance, with the frame barred from changing run definitions, tool use, paths, scoring, hidden-material handling, or the output schema.

## Not checked

- Did not run SAST, dependency, secret, or CVE scanners; those are scanner-owned and outside this reasoning-only spec review.
- Did not verify provider transport behavior, served model identity, or runtime tool isolation live; this review checked whether the spec and plan require the right evidence.
- Did not inspect ignored `.context` handoff bytes or future model outputs; those are execution artifacts, not present implementation evidence.
