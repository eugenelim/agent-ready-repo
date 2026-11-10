# ADR-0163: The spec supervisor ships inside `new-spec`, and `work-loop` stays the front door

- **Status:** Accepted
- **Date:** 2026-11-10
- **Areas:** orchestration, work-loop
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0144 (the pinned supervisor); ADR-0162 (the contract the spec supervisor implements)

## Context

A spec supervisor needs a home. `work-loop` is the front door for spec work today, and each new skill name is something a user has to learn. The pinned `work-loop` copy must stay byte-identical.

## Decision

We will ship `spec-supervisor.py` inside the existing core skill `new-spec` and keep `work-loop` as the only front door.

- **D1:** `spec-supervisor.py` lives in `new-spec` at repo scope, with its own `supervisor.toml`, policy file and store.
- **D2:** With it installed, `work-loop`'s spec-plan mode drives pre-approval through it and calls `work-supervisor start` at plan approval through `delegate-verb`. Without it, `references/pre-execute-review.md` stays the procedure.
- **D3:** No file under `work-loop/scripts/` and no policy JSON in its pin set changes. The sibling shares only the command contract and no code with `work-supervisor.py`.

## Consequences

**Positive:**
- Users learn no new skill.
- The work supervisor's pin stays byte-identical.

**Negative:**
- `new-spec` now carries a script, so its releases carry supervisor changes.
- `work-loop`'s spec-plan mode needs an installed-or-not branch.

**Revisit if:** `new-spec` splits, or `work-loop` stops being the front door.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the work-loop pin suites stay green, and a pack test checks that the pinned files are unchanged.
- **Owner:** eugenelim

## Alternatives considered

- **A new `spec-loop` skill:** it adds a name and overlaps `work-loop`'s spec-plan mode.
- **The script in `work-loop/scripts/`:** that directory is the work supervisor's pin set, so an edit there voids runs.

## References

- `docs/rfc/0115-mechanized-delivery.md`
- `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`
