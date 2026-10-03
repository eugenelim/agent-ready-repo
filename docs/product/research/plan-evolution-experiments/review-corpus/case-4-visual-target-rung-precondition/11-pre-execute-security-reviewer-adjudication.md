## Main-loop result
**1. [Concern] 1: Forbidden agent tools are not denied before release.** `docs/specs/plan-evolution-experiments/spec.md:97`. The target records the managed profile/tool surface before release and fails closed for protected-path denial gaps or requested/observed forbidden use, but it does not make exposed web/network/delegation/escalation/external-messaging tools absent or denied before worker launch; AC-0005A also omits web from its release predicate at `docs/specs/plan-evolution-experiments/spec.md:343`. The plan repeats the same pre-launch gap by stopping on missing protected-path denials or requested/observed network/delegation/escalation/external messaging while only instructing workers not to use web at `docs/specs/plan-evolution-experiments/plan.md:44`. A worker that receives untrusted task material can reach the claimed exfiltration path before the controller observes and records the deviation, so the security consequence is reachable at this stage; proposed mechanism: adequate. Fix: Make inferential release fail closed before launch unless web, network, delegation, approval escalation, and external messaging tools are absent or denied by the managed profile, or explicitly label the affected run set as unreleased/non-inferential/non-secret-bearing evidence; add web to AC-0005A's forbidden-use release predicate.

## Refuted audit
None.

## Indeterminate audit
None.
