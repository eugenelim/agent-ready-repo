## Concerns

**1. Forbidden agent tools are recorded but not denied before release.** `docs/specs/plan-evolution-experiments/spec.md:97-104`, `docs/specs/plan-evolution-experiments/spec.md:343-346`, `docs/specs/plan-evolution-experiments/plan.md:44-56`. A prompt-injected or malfunctioning collaboration worker that can see a web, network, delegation, escalation, or external-messaging tool can use it once before the controller records the deviation, leaking candidate content, hidden-path markers, or credential-shaped material outside the workbench while the acceptance criterion only requires a stopped record after requested or observed use and omits `web` from AC-0005A's release predicate. Fix: The release criteria must fail closed before launch unless those tools are absent or denied by the managed profile; if the platform cannot make that enforceable and observable, the run set must stay unreleased or be explicitly downgraded to non-inferential/non-secret-bearing evidence, and AC-0005A must name `web` alongside network, delegation, escalation, and external messaging.

## Not checked

- Did not run SAST, SCA, secret scanning, or dependency scanners; this was a spec-stage reasoning review.
- Did not launch or pentest live Codex workers, inspect credentials, browser profiles, protected configuration, or verify the managed permission profile; this pass reviewed whether the spec and plan define the required release criteria.
- Did not review implementation diffs or runtime code paths because this is pre-execute spec-stage review.
- Did not examine unrelated endpoint authentication, endpoint authorization, cryptographic primitive, dependency, or deployment/IaC classes because this spec does not add those boundaries.
