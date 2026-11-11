# ADR-0142: Meta-repo handover: component slices acquired by component repos, status by pinned receipts

- **Status:** Accepted
- **Date:** 2026-10-10
- **Areas:** shaping, security, contracts
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0022 D3,D4,D9; ADR-0019 D9
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0107 (the proposal this records — D4 and D5); ADR-0022 (the value-stream meta-repo this amends); ADR-0019 (the per-component brief projection this amends); RFC-0083 (closure receipts, amended by RFC-0107's erratum); RFC-0103 (the pointer grammar this qualifies); [security review](../rfc/0107-notes/security-review.md) (the clean proposal-stage pass)

## Context

- ADR-0022 sliced a feature intent into briefs that cross into component repositories.
- No skill could carry a brief there. `author-delivery-brief` writes only inside its own
  repository, so the only route was a hand copy, which leaves two authorities for one
  brief.
- Status returned only through a rollup edited by hand.
- RFC-0083 specified closure receipts on the parent intent, but they were never built.
- Core treated every external locator as passive provenance and never read it.

## Decision

We will hand meta-repo work to component repositories as component slices that each
component repository acquires at a pinned revision, and return status as receipts read
under human control.

- **D1:** A component slice states one component repository's share of a meta-repo
  feature intent. It lives in the meta-repo and holds every cross-repository link. The
  feature intent's affected repositories derive from its component slices.
- **D2:** The component repository acquires a component slice at a pinned revision,
  under the lifecycle rules Core applies to tracker items, and writes its own brief.
  The meta-repo never writes a delivery brief.
- **D3:** The component brief still carries a `contract@version` reference and a
  read-only contract snapshot, fixed by the component slice's pinned revision.
- **D4:** Core publishes the component-slice contract. `product-engineering` writes
  component slices and owns status collection. Core imports nothing from
  `product-engineering`.
- **D5:** Core may read another repository only during acquire, refresh, and status
  collection. Existing offline reconciliation surfaces gain no cross-repository access.
- **D6:** A read target comes only from a human-reviewed record:
  - in a component repo, the acquisition record a human started;
  - in the meta-repo, its own reviewed repository list.

  A parent pointer grants no read on its own.
- **D7:** A pin is an immutable commit reachable from the designated reviewed branch.
  The read returns that commit's real objects, never a working tree. No receipt is ever
  written from an unreachable pin.
- **D8:** Local reads accept only repository-relative regular-file entries within a size
  limit, and run no checkout configuration or hooks. API reads use a declared provider
  read surface confined to the configured host, and the credential is never sent
  elsewhere.
- **D9:** Status collection runs only on a current human request. Every receipt write
  needs a human-set switch. A receipt holds only the status fact, the pin, and
  repository-relative locators, and its status comes only from a commit on the reviewed
  branch.
- **D10:** Cross-repository pointers extend RFC-0103's `<kind>:<slug>` grammar with a
  repository qualifier. The brief's parent pointer is now interpreted as a
  cross-repository link, within D6.

## Consequences

**Positive:**
- Each brief has one copy and one authority.
- Delivery status reaches the meta-repo as reviewed evidence.
- RFC-0083's closure receipts get a carrier.

**Negative:**
- Core's trust boundary widens to a second repository.
- The commit-history read path and the provider read surface are new code that needs a
  spec-stage security review.
- The rollup stops being a free-form table.

**Revisit if:** a spec-stage security review cannot meet D6–D9, or a receipt is ever
counted from a pin outside the reviewed branch.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** each spec that implements D5–D9 passes `security-reviewer` against these
  controls, with the four questions deferred in the proposal-stage review answered.
- **Owner:** eugenelim

## Alternatives considered

- **Hand copy:** two authorities for one brief.
- **The meta-repo writes and pushes briefs:** the meta-repo would own another
  repository's Ready gate.
- **The component repo re-shapes from scratch, linking back:** contract and dependency
  facts are lost.
- **Paste-only transport:** no refresh is possible.

## References

- [RFC-0107](../rfc/0107-verb-mode-shaping-and-intake-with-slice-handover.md)
- [Meta-repo handover audit](../product/findings/meta-repo-handover-audit.md)
- [RFC-0107 security review](../rfc/0107-notes/security-review.md)
