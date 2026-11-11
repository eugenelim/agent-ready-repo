# ADR-0181: A recorded answer carrying a verified named human's approve counts as that human's approve

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, work-loop
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0157 (D4 is superseded in part by this record once it is Accepted; the mirror lines follow then); ADR-0159 (D10 keeps its guarantees); RFC-0113 (the run grant keeps its guarantees); RFC-0099 (section 7); RFC-0117 (the approval and trust model); ADR-0172 (approval invariant, levels, attribution record and approval-fields contract); ADR-0173 (gate scribe); ADR-0178 (relayed tracker signals)

## Context

ADR-0157 D4 says only `approve` from the gate's named human advances a gate, and "No verb, flag, default, or record turns a parked gate into an approval." A host, a tracker or a pool can carry that human's approve. D4 as written does not say whether such a recorded answer counts. v1 does not need the change, because the terminal answer is the approver's own act (RFC-0117, page 05b, page 10d D74).

## Decision

We will count a recorded answer that carries a verified named human's approve at an enumerated level as that human's approve, and keep every other clause of ADR-0157 D4.

- **D1:** The levels this record enables are `host-attested`, `tracker-verified` and `control-plane-signed`. Each is the `verification` value of the attribution record, and `channel` is a separate field (ADR-0172 D5, D8). A level counts per gate only where the repository's accept list for that gate names it. `session-attested` rests on ADR-0172 and ADR-0173 and does not depend on this record.
- **D2:** The answer's attribution record names the verified human and carries the exact gate digest. A changed digest refuses `stale-digest` (ADR-0172 D1).
- **D3:** The sentence in ADR-0157 D4 that is narrowed is "No verb, flag, default, or record turns a parked gate into an approval." Its replacement is "No verb, flag, default, or record turns a parked gate into an approval, except a recorded answer that carries the named human's verified approve at a level the gate's accept list names." Every other clause of ADR-0157 D4 stands word for word: no answer, a timeout, a session end, a `stale` state, a missing or malformed record, and any listing output leave the gate unapproved, and `reject` takes the existing route.
- **D4:** ADR-0157 D1 to D3 and D5 to D7 are untouched. ADR-0159 D10 holds: no runner output, standing order, policy value, timeout or default approves, and merge stays human. RFC-0113 holds: a grant only narrows and authorises nothing. RFC-0099 section 7 holds. A grant cannot add a level to a gate's accept list.
- **D5:** v1 accepts only `session-attested`. A verified tracker label is recorded as a run-state field and a `tracker-signal-ignored` event until the gate's accept list names `tracker-verified` and a non-approver mirror identity exists (RFC-0117 D3).

## Consequences

**Positive:**
- A host, tracker or pool answer from the named human can advance a gate, with a record of who gave it and for which digest.
- The change is narrow, and the rest of D4 remains the rule.

**Negative:**
- Each level needs its own verification, so the change is larger than the sentence suggests.
- Until acceptance, a tracker label cannot approve a gate.

**Revisit if:** a level cannot verify the named human, or ADR-0172 changes the levels.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a test per level that an answer without a verified human, a level the accept list does not name, a changed digest (`stale-digest`) or an unrecorded answer leaves the gate unapproved. A test that v1 records only `tracker-signal-ignored` for a tracker label. The test that pins ADR-0159 D10's RFC-0099 section 7 guarantee passes unchanged.
- **Owner:** eugenelim

## Alternatives considered

- **Host and tracker signals only trigger a session-attested terminal confirmation:** the human must always answer in the terminal.
- **The approver always writes `Status` by hand:** no recorded answer counts.

## References

- `docs/adr/0157-work-loop-approval-gates-park-instead-of-halting.md` (D4)
- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/10-decisions-and-records.md` (record 18)
- `docs/architecture/unattended-delivery-runner/05b-approval-integrity-and-trusted-configuration.md`
- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md` (D35, D74)
