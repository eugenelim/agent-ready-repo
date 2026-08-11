# Spec: Adopter-usable seed links

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Every repository-relative link in the shipped `core` conventions seed that
names catalogue governance or maintainer-only guidance resolves from the
adopter's installed surface. The credential-broker convention remains
self-contained, while catalogue-only hook guidance lives only in the local
maintainer context.

## Boundaries

### Always do

- State the four supported credential brokers directly in the conventions seed.
- Test governance links against the scaffolded pack output, not the self-host repository.
- Keep catalogue-only operational pointers in `AGENTS.local.md`.

### Ask first

- Any change that removes adopter-usable credential-broker guidance.
- Any broader cleanup of links outside `docs/CONVENTIONS.md`.

### Never do

- Ship this catalogue's numbered ADRs or RFCs to make a seed link resolve.
- Replace a dead relative link with a catalogue-specific external URL.
- Add a dependency, public engine behavior, or new module boundary for link validation.

## Testing Strategy

- **TDD:** the first-install snapshot test rejects every repository-relative
  Markdown link in scaffolded core `docs/CONVENTIONS.md` whose target is absent
  from the scaffolded pack. External URLs and same-document anchors are exempt;
  the installed target-closure contract is what the self-host tree masks.
- **Goal-based check:** catalogue lint and self-host drift checks verify the
  cleaned seed, its projection, and pack metadata remain consistent.
- **Manual QA:** read the installed-facing paragraph and confirm the broker
  rule remains complete without provenance links.

## Acceptance Criteria

- [x] The shipped `docs/CONVENTIONS.md` contains neither the catalogue-specific
  `ADR-0003` / `RFC-0013` citations nor links to their records, and the four
  broker ids remain stated directly.
- [x] The two `tools/hooks/README.md` links are absent from the shipped
  conventions seed and the repo-only pointer is recorded in `AGENTS.local.md`.
- [x] A first-install regression fails when the scaffolded core conventions
  document contains any repository-relative Markdown link whose target is
  absent from that scaffolded pack.
- [x] `docs/CONVENTIONS.md` is byte-identical to the canonical core seed.
- [x] The non-cosmetic core content change carries its required patch version,
  marketplace regeneration, and catalogue changelog entry.

## Assumptions

- Technical: the core conventions seed is the source of the self-hosted
  projection (source: `packs/AGENTS.local.md`).
- Technical: no pack seed carries `docs/adr/0003-credential-broker-contract.md`
  or `docs/rfc/0013-credential-broker-contract.md` (source: repository search
  2026-08-11).
- Process: non-cosmetic pack changes require a patch bump and host catalogue
  release bookkeeping (source: `packs/AGENTS.md` and `packs/AGENTS.local.md`).
- Product: shipped material references only paths and capabilities present in
  the adopter's installed surface (source: user confirmation 2026-08-11).
