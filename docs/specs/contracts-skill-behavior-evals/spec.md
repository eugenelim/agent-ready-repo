# Spec: Behavior evals with expect blocks for the contracts skills

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored when the spec is approved
- **Constrained by:** RFC-0037 Errata E3; `pack-activation-evals` spec
- **Brief:** brief:pack-eval-rollout-completion-delivery
- **Discovery:** intent:pack-eval-rollout-completion
- **Depends on:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

Maintainers can check that `api-contract` and `event-contract` emit a valid contract artifact without a live model run. The evals carry `expect` blocks and fixtures that a deterministic validator can grade.

## What Changes

- `expect` blocks and fixtures in the `evals.json` of `api-contract` and `event-contract`, in the form other skills' evals already use (for example `packs/converters/.apm/skills/file-to-markdown/evals/evals.json`).
- A fixture validator that checks a fixture artifact against the contract format using tooling already in the repository.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Eval conventions | The two skills' `evals/` directories | eugenelim | Eval schema test passes | close-work verifies the schema test and fixture validator pass |

## Agent Rules

### Always do

- Copy the `expect` shape from an existing eval.
- Keep fixtures small and synthetic.

### Ask first

- Adding a new validation dependency; record it first.

### Never do

- Run a model.
- Change any skill's behavior.

## Testing Strategy

TDD for the fixture validator: a valid fixture passes and a seeded wrong artifact fails. Goal-based: the eval schema test passes over the two files.

## Acceptance Criteria

- [ ] **AC1.** Both skills' `evals.json` files carry at least one case with an `expect` block.
- [ ] **AC2.** Each `expect` block names a fixture and the assertion the validator grades.
- [ ] **AC3.** The fixture validator passes on the shipped fixtures.
- [ ] **AC4.** The validator fails on a seeded artifact that violates the contract format.
- [ ] **AC5.** The existing eval schema test passes.

## Follow-ons

- eugenelim: slices P2 to P4 in `brief:pack-eval-rollout-completion-delivery`.

## Assumptions

- Open question for eugenelim: which validator grades an OpenAPI or event-schema fixture offline. Recommended default: the repository's existing contract validators under `tools/` if present; otherwise a structural check on required keys, recorded as a limit.
- No `expect` block exists in the contracts evals today (checked 2026-11-05), so this slice adds the first.
