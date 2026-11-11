# ADR-0173: One gate scribe writes each approval under a write-ahead intent

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, work-loop
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 (the trust model this records); ADR-0157 (D4 returns a rejected pair to drafting); ADR-0164 (the foreground ferryman that runs the scribe); ADR-0172 (the approval invariant and attribution record); ADR-0174 (the trusted configuration pin); ADR-0181 (verified-human approve counts)

## Context

An approval edit and its attribution record must land together. A crash between them must never leave a half-approval. A worker must not be able to forge the edit.

## Decision

We will have one scribe write each approval edit and its attribution record in a single commit, under a write-ahead intent that a startup check resolves.

- **D1:** The scribe is the one non-supervisor committer in `ferryman`. It writes the approval edit and the record in one commit, both or neither.
- **D2:** Before writing, it writes and syncs `scribe/intent-<id>.json`. The intent holds the gate, digests, decision, actor, verification, evidence ref, base `HEAD` and commit message. For each planned file it holds the path, the `before` hash, the `after` hash and the `before` bytes.
- **D3:** Before any `next`, `ferryman` looks for an open intent and decides by the files' current hashes. There are six outcomes, in this order:
  1. All files at `before`: abandon the intent (`scribe-abandoned`).
  2. `HEAD` already holds the planned tree on the base `HEAD`: close the intent, with no second commit.
  3. Some or all files at `after`, nothing committed: roll forward only if the approval re-verifies from durable evidence. `tracker-verified` re-fetches the tracker event. `host-attested` or `control-plane-signed` needs the control file for the same `id` still present and inside the window rule. Otherwise it restores.
  4. A `session-attested` answer always restores and prompts again. A restore writes the `before` bytes only into files whose hash equals `after`.
  5. Any file at a hash that is neither `before` nor `after`: park as `scribe-unrecoverable`, name the paths, and touch nothing.
  6. Uncommitted edits in approval-bearing files with no intent: refuse as `scribe-intent-missing` and park.
- **D4:** The scribe regenerates the `after` bytes from the intent's semantic fields and compares them with the recorded hash, so a forged intent cannot commit other content.
- **D5:** Rejection uses the same scribe and needs a verified human. In one commit it sets the spec to `Draft` and the plan to `Drafting`, and the record carries decision `request-changes` or `reject`. This applies ADR-0157 D4's rule that reject returns the pair to drafting.
- **D6:** The scribe covers only brief-ready, spec-approved and plan-approved. Discovery gates G0 to G3 use the discovery-supervisor's own commit.

## Consequences

**Positive:**
- A crash at any step leaves no half-approval.
- A forged intent file cannot commit different content.

**Negative:**
- The scribe adds a recovery state that operators must understand.
- A `session-attested` crash costs a second prompt.

**Revisit if:** a gate outside the three in D6 needs the scribe.

## Confirmation

- **Mode:** lint/CI
- **Signal:** kill-point tests B-S1 to B-S6 resolve with no half-approval.
- **Owner:** eugenelim

## Alternatives considered

- **The approver edits `Status:` by hand:** the attribution record would not land with the edit.
- **Write the edit with no intent record:** a crash would leave nothing to decide from.

## References

- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/05b-approval-integrity-and-trusted-configuration.md`
- `docs/adr/0157-work-loop-approval-gates-park-instead-of-halting.md`
