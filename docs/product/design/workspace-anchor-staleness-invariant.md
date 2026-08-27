# Workspace anchor staleness invariant

- **Status:** Draft

## Outcome

Queued work is flagged for human revalidation when a dependency or lifecycle
membership change makes its approved assumptions stale.

## Design question

Define a repository-wide fitness function that detects meaningful anchor drift
without treating every later dependency shipment or membership edit as proof
that an approved spec is invalid.

## Constraints

- Detection must use canonical lifecycle records and artifact revisions, not
  comments, summaries, list order, or session memory.
- A finding must remain non-dispatchable until a human confirms whether the
  approved assumptions still hold.
- The design must distinguish dependency completion from a dependency contract
  changing after approval.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0083-work-intake-and-artifact-routing.md
- Revision: sha256-bytes-v1:8176272b14747e07e70beb752d6b709ccac502c284a9c114ae03c0cb48312a9d
