# ADR-0184: Light work runs as a supervisor-less `ferryman session`

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** orchestration, work-loop
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0162 (supervisors under one command contract); ADR-0164 (the foreground ferryman); ADR-0166 (the frontier); ADR-0171 (repository copy of supervisors, detection and confined files)

## Context

Light work has no spec and no plan, so no supervisor can drive it. `work-loop` direct-light does this by hand today and leaves no `docs/specs/` or work registry change. `ferryman` needs a route for it that keeps a human in charge.

## Decision

We will add `ferryman session [--ticket <ref>] <prompt-or-request-file>`, which runs one worker with no supervisor.

- **D1:** A session runs one worker with no `next` or `report` loop, no spec, no plan, no scribe and no supervisor. It leaves no `docs/specs/` or work registry change.
- **D2:** The invocation by a local human is the authority. An issue or pull request is only context, and a `--ticket` is fetched as untrusted context.
- **D3:** The `light` label only lists a `light_candidates` entry. No model triages.
- **D4:** A session runs on a `ferryman/session-<hash>` branch or in a checkout that refuses a dirty tree, as `run` does.
- **D5:** A session reuses workers, profiles, limits, orphan handling, the projector, events, the inbox, control files, locks and the path-based guard checks (`worker-commit`, `worker-moved-ref` and protected paths). It adds a working-tree check that refuses an untracked path outside the declared files.
- **D6:** The worker returns `handoff`, `escalate-full`, `needs-human` or `blocked` in a required result file or token, since exit 0 carries no meaning.
- **D7:** `escalate-full` and `needs-human` park `light-escalated`. `blocked` stops the run `needs-attention` with a reason. `ferryman` never restarts a light run as full and never respawns (`max_respawns` 0).
- **D8:** The worker never commits. The result is the uncommitted tree plus the checkpoint ref `refs/ferryman/sessions/<run-id>/product`, and a human publishes.
- **D9:** A session has no resume, and a kill parks `session-interrupted`. A node marker or a committed `[pool]` table refuses it with `session-pool-refused`, and the refusal fails closed.
- **D10:** Ticket fields are labelled data and never fill the declared files or the allow list. A `--ticket` run refuses an `unenforced` or `unverifiable` enforcement level, and any shell or network profile, without a recorded acknowledgement.
- **D11:** Direct-light is proven only by a clean `git status` limited to the declared files, no `docs/specs/` or work registry change, and a recorded reviewer outcome.

## Consequences

**Positive:**
- Light work gets the guard, limits and events of a full run with no supervisor to build.
- A human launches and publishes every session.

**Negative:**
- A killed session cannot resume, so a human publishes, discards or deletes the kept branch.
- The `light-mode.md` slice of brief `ferryman-local-delivery`, delivered with phase PL, also needs a core version bump and an eval-harness update.

**Revisit if:** light work needs resume, or a pool must run sessions.

## Confirmation

- **Mode:** lint/CI
- **Signal:** kill-point tests for the five session boundaries (B-X1 to B-X5) that park `session-interrupted`, a test that no `docs/specs/` or work registry change remains, a test for the untracked-path check, a `session-pool-refused` test for a node marker and for a committed `[pool]` table, a test that ticket text never changes the declared files or allow list, and a test that a `--ticket` run refuses `unenforced`, `unverifiable` and shell or network profiles without an acknowledgement.
- **Owner:** eugenelim

## Alternatives considered

- **Model triage with a first-class light route:** nothing commits the work, a model verdict replaces the only human check, and a stateless controller cannot resume it.
- **A trimmed spec and plan:** light work would still create durable artifacts.

## References

- `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md` (Session route)
- `docs/architecture/unattended-delivery-runner/03-ferryman-runtime.md` (session steps, exit codes, B-X1 to B-X5)
- `docs/architecture/unattended-delivery-runner/10c-review-decisions.md` (D75)
- `packs/core/.apm/skills/work-loop/references/light-mode.md`
