# Brief: finish the pack-eval coverage that needs no live service

- **Slug:** `pack-eval-rollout-completion-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/pack-eval-rollout-completion.md`](../intents/pack-eval-rollout-completion.md), cut into slices on 2026-11-05 from a read of the code and specs.
- **Parent intent:** intent:pack-eval-rollout-completion

## Outcome

Deterministic `contracts` skills have behavior evals with `expect` blocks, the converters gate reads the pack manifest instead of a hand list, and the judge rubrics for the remaining skills are written, all checked offline.

## Success metrics

- `api-contract` and `event-contract` evals carry `expect` blocks and fixtures that validate their output.
- The converters carry-over step in `build-check` reads `[pack.evals].skills`, and `mermaid-renderer` is reconciled in the same change.
- Rubric files exist for `new-package` and the core judgment skills and pass schema validation.

## Scope / Non-goals

**In scope:**

- Contracts `expect` blocks and fixtures.
- Gate consolidation.
- Tier-4 rubric authoring.
- The four core activation-boundary cases and the reusable first-value rubric fields (first-task completion, visible-artifact presence, recovery path, next-action clarity) from RFC-0064 Amendment 4 (which defines Level A and B pack obligations), as slice P4.

**Non-goals:**

- Calibration and the report-only versus gate decision.
- Behavior evals for credentialed backend skills (atlassian, figma).

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| P1 | `expect` blocks and fixtures for `api-contract` and `event-contract`. | Eval schema test and a fixture validator pass; seeded wrong artifact fails | none | none |
| P2 | Converters gate consolidation: read `[pack.evals].skills`; reconcile `mermaid-renderer`. | `lint-ci-parity` and the build-check step logic pass locally; a seeded missing skill fails | P1 | Own PR, per the intent |
| P3 | Tier-4 judge rubrics for `new-package` and the core judgment skills that have none today (enumerate them in the slice spec from the pack manifest), authored offline. No rubric schema file exists under `packs/**/evals` today, so the P3 spec defines the rubric format. | Each rubric validates against the format the P3 spec names; a seeded malformed rubric fails | none | Spec names the core skill list and rubric format |
| P4 | The four core activation-boundary cases added to the core `eval_queries.json` files, and the four first-value rubric fields recorded as reusable fields for the cross-pack adoption overlay. | The eval query schema test passes; each case names a skill and its expected activation or non-activation | none | Spec cites where the four cases are defined |

### Manual or live residue, split off as non-blocking follow-ups

- Rubric runs and calibration use the scheduled `pack-evals` workflow with a model key; owner-run and non-blocking.
- Backend skills (atlassian 8, figma 1) need credentials or a recorded-interaction harness. Out of scope until a recorded transcript exists.

## Constraints / Appetite

Four small sessions.

## Assumptions / Risks

- Riskiest assumption: contracts output can be validated by a deterministic script. Check with the existing OpenAPI and event-schema tooling in P1.
- Risk: changing the build-check step breaks the converters carry-over disposition. P2 keeps the msg-to-markdown negative assertion.

## Ready gaps (Draft only)

None open. The P3 spec obligation is to name the core judgment skill list and the rubric format; the P4 spec obligation is to cite where the four cases are defined.

## Spec map

| Spec | Status |
| --- | --- |
|  |  |

## Provenance

- Parent intent: [`pack-eval-rollout-completion.md`](../intents/pack-eval-rollout-completion.md).
