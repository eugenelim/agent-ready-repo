# ADR-0172: An approval is a verified named human's answer bound to a gate digest

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, work-loop
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 (the trust model this records); ADR-0157 (parked gates, approval unchanged); ADR-0162 (the siblings whose `report` reads the field list); ADR-0163 (the `new-spec` copy of the field list); ADR-0169 (tracker-verified level); ADR-0173 (the scribe that writes the record); ADR-0174 (the pinned approver set); ADR-0175 (pool core); ADR-0178 (relayed tracker signals); ADR-0181 (verified-human approve counts); ADR-0182 (the version rule); ADR-0184 (the supervisor-less session route)

## Context

Unattended runs stay safe only if approval comes from a human and nothing a worker touches can change who counts as one. The system needs one definition of an approval, a record of who gave it, and one list of protected fields.

## Decision

We will define an approval as the answer of a verified named human, bound to the exact gate digest, and we will record every approval with its verification level.

- **D1:** A changed digest refuses with `stale-digest`.
- **D2:** A worker, tracker text, a label from an unverified, bot or app actor, and a controller default are never approvals. A model judge or an unverified rejection or `changes-requested` only parks the gate. A loosening signal needs a verified identity.
- **D3:** There are four levels: `session-attested`, `host-attested`, `tracker-verified` and `control-plane-signed`. `ferryman` v1 accepts only `session-attested`, which is its own terminal prompt.
- **D4:** Each gate lists the levels it takes in `[gates.<gate>] accept`. The default is `session-attested` only.
- **D5:** In v1 the actor is the Git `user.email` matched against a committed identity table. This is provisional (page 10d D65). `plan_reviewer_ref` must equal `owner_ref`.
- **D6:** `in-session` is advisory. It is a level only on page 05 for the session route (ADR-0184), and it never appears in an accept list.
- **D7:** For `session-attested`, the answer at the terminal prompt is the approver's own act. The scribe writes only the edit that answer names, as the approver's recorded delegate, so every ADR-0157 D4 bar stands.
- **D8:** An `approval-attribution.v1` record has these fields: `gate`, `artifact`, `digest`, `decision`, `actor`, `verification`, `channel`, `at`, and an optional `tracker` object.
- **D9:** `approval-fields.v1` is one list of `fields`, `protected_paths` and `executed_paths`. `executed_paths` holds every file the controller reads to decide or executes. The guard and each sibling's `report` both read it. The `new-spec` copy is authoritative, and `ferryman` adopts it (ADR-0163).
- **D10:** The refusal on a `fields_version` mismatch is ADR-0182 D6.
- **D11:** A guard in `ferryman`, and in each sibling's `report` under `ferryman`, compares each attempt with its pre-attempt `HEAD`, full ref map and tree. It refuses `worker-commit`, `worker-moved-ref`, an approval-field edit or a protected-path change. It never reverts, and it parks with the tree as found.
- **D12:** Levels beyond `session-attested` count only once ADR-0181 and that level's own record are Accepted: ADR-0169 for `tracker-verified`, and ADR-0175 and ADR-0178 for `control-plane-signed`.

## Consequences

**Positive:**
- Approval has one meaning across every channel.
- The field list has one home, so the guard and the siblings cannot drift apart.

**Negative:**
- Only the terminal prompt approves in v1.
- Any local process can set `user.email`, and a same-user process could feed the prompt. RFC-0117 accepts both for v1.

**Revisit if:** a fifth verification level is needed.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a guard corpus refuses every approval-bearing edit, and schema tests cover both record and field list.
- **Owner:** eugenelim

## Alternatives considered

- **Let a worker or a controller default approve:** a worker could then set its own approval.
- **Trust any local terminal user:** the actor would not be a verified named human.

## References

- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/05b-approval-integrity-and-trusted-configuration.md`
- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md`
- `docs/adr/0157-work-loop-approval-gates-park-instead-of-halting.md`
