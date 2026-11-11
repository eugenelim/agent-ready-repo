# Spec: Cross-pack experience seam checks

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored when the spec is approved
- **Constrained by:** RFC-0071 D7 and Area F; the shipped `digital-experience-contract` spec
- **Brief:** brief:cross-pack-experience-eval-delivery
- **Discovery:** intent:cross-pack-experience-eval
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

Maintainers get one offline check that the handoffs between the four doctrine packs resolve and that adapter projections declare what they change. A pack that passes its own rubric but breaks the chain fails before release.

## What Changes

- A seam check script and its test in the repository-level `tools/` area, one check per failure class: referenced skills resolve; no phantom handoff to a skill that does not exist; the contract's `risk-tier` field (RFC-0071's risk-mode) is present where the contract requires it; contract-copy drift between the packs' copies of the Digital Experience Contract reference; evidence-manifest entries exist where `frontend-engineering` requires one; adapter projections declare their transformed, degraded and dropped primitives against `contracts/adapter.schema.json` and `docs/architecture/runtime-adapter-crosswalk.md`.
- Terminal whole-journey review stays in `experience-design`; the harness and fixtures are a later slice (E2).

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | The check is a repository gate candidate | `tools/` script and test; guide reference line in the cross-pack section of `guides/_shared/` | eugenelim | Test passing; the script's `--help` names each class | close-work verifies the test passes and the check exits zero on the tree |
| Decision rationale | RFC-0071 ordering waiver covers this slice only | The brief's Constraints (already recorded) | eugenelim | Waiver text in the brief | Nothing further |

## Agent Rules

### Always do

- Cite the contract reference and the adapter files rather than copying their text.
- Keep the check read-only and offline.
- Report every failure with the file and the class.

### Ask first

- Any move of the check into the required CI gate chain.
- Any new dependency.

### Never do

- Treat the check as a gate before calibration; E2 and later runs are report-only.
- Call a model or a network service.

## Testing Strategy

TDD for each failure class: one seeded violation per class fails and names the class; a clean run over the real tree passes. Goal-based check: `python3 tools/lint-ci-parity.py` still exits zero after the script is added.

## Acceptance Criteria

- [ ] **AC1.** A seeded unresolved skill reference makes the check fail and name the class `unresolved-skill`.
- [ ] **AC2.** A seeded handoff to a missing skill fails and names `phantom-handoff`.
- [ ] **AC3.** A seeded contract copy with a missing `risk-tier` field fails and names `risk-tier`.
- [ ] **AC4.** A seeded divergence between two packs' copies of the contract reference fails and names `contract-copy-drift`.
- [ ] **AC5.** A seeded missing evidence-manifest entry fails and names `evidence-manifest`.
- [ ] **AC6.** A seeded adapter projection with an undeclared dropped primitive fails and names `adapter-projection`.
- [ ] **AC7.** The check exits zero on the current tree, with no network and no model call.

## Follow-ons

- eugenelim: `brief:cross-pack-experience-eval-delivery` slice E2 — fixtures and report-only harness.

## Assumptions

- Open question for eugenelim: which existing `tools/` file name and make target should carry the check. Recommended default: a new `tools/check-cross-pack-seams.py` with its test beside it, not wired into `make ci` until E2 calibrates it.
- The exact list of contract copies to compare is read from the packs that ship `references/digital-experience-contract.md`; the spec assumes that file name is stable.
