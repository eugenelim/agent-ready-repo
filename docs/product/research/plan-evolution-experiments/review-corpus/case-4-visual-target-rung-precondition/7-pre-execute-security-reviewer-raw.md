## Blockers

**1. [reason] Active collaboration release gate lacks the worker authority canary it relies on.** `docs/specs/plan-evolution-experiments/plan.md:420`, `docs/specs/plan-evolution-experiments/plan.md:508`. A collaboration worker with the shared runtime's filesystem or network tools can read hidden or sibling roots, source material, or credentials before producing a schema-valid terminal receipt; the active Run 0 gate validates assignment, launch, terminal, freeze, grade, contamination, and accounting receipts, while the explicit read/write/egress/environment/credential/delegation canary is tied to the earlier instrument-calibration section rather than the `codex-collaboration-r1` release criterion. Fix: The `codex-collaboration-r1` Run 0 and inferential-release acceptance criterion must fail closed before any inferential start unless controller-observable canaries prove the exact worker tool profile: candidate-root-only reads and writes, no source/sibling/hidden/credential access, no network/delegation/external messaging, and explicit stopped or infrastructure records when any control is widened or unobservable.

## Concerns

**2. [hybrid] Disposable-root path validation omits hard-link and open-time identity requirements.** `docs/specs/plan-evolution-experiments/plan.md:269`. A task package, archive member, or model-written path that is a hard-linked regular file or changes between validation and read can pass a shallow canonical-prefix check and let grading or evidence bytes cross the candidate boundary. Fix: The spec and plan must require repository `file_safety` helpers for repository roots and a documented equivalent for disposable roots that canonicalizes after symlink resolution, rejects symlinks, reparse points, junctions, hard links, special files, absolute or traversing archive members, and path loops, detects identity changes while opening, and fails closed before command, gate, grade, or report use.

## Not checked

- Did not run SAST, SCA, secret scanning, or dependency audit; those are scanner-owned tool checks outside this spec-stage design pass.
- Did not execute Codex collaboration workers or validate the live sandbox/tool policy; this review assessed whether the pre-execute spec and plan make those controls acceptance criteria at the right depth.
- Did not review unrelated legacy `codex-cli-r1`, Claude calibration, or non-worker experiment statistics except where they shaped the amended worker/data/path boundary.
- Did not inspect credentials, browser profiles, protected configuration, or personal data, per repository policy.
