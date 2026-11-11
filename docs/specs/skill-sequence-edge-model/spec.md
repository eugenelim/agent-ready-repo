# Spec: Skill sequence edge model and derivation script

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored when the spec is approved
- **Constrained by:** `skill-sequence-wayfinding` intent; `contracts/skill.schema.json` (`metadata` extension table)
- **Brief:** brief:skill-sequence-wayfinding-delivery
- **Discovery:** capability:skill-sequence-wayfinding
- **Depends on:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

A maintainer can print the closed set of edges and terminal nodes across the packs that ship a `JOURNEY.md`, with a stated rule for which skills name a successor. The set is stable and checked.

## What Changes

- An edge model carrying each stage's skills, successor, branch and dependency reason, and a derivation script that prints every edge and terminal node.
- A stated successor rule that says which skills name a successor (replacing the three predicates that returned 1, 24 and 17).
- A decision, recorded in this spec, on where the successor lives.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Where the successor lives | This spec's Assumptions and the intent's Unresolved question 1 | eugenelim | Decision recorded | none |
| Maintainer procedure | The derivation script | `tools/` or the journey tooling | eugenelim | Golden edge list test | close-work verifies the test |

## Agent Rules

### Always do

- Validate all `JOURNEY.md` files with `tools/lint-pack-journeys.py` before and after.
- Cite what `docs-wayfinding-cluster` and `docs-job-pages` already own.

### Ask first

- Make any new journey field required; it stays optional.
- Edit skill text; that is slice W3.

### Never do

- Break any existing `JOURNEY.md`.
- Put the successor in a top-level skill frontmatter key.

## Testing Strategy

Goal-based: the lint passes on all journeys; the derivation script prints a stable golden edge list under test. TDD: a seeded stage with an unknown successor fails.

## Acceptance Criteria

- [ ] **AC1.** `tools/lint-pack-journeys.py` passes on every `JOURNEY.md` after the change.
- [ ] **AC2.** The derivation script prints every edge and terminal node and the output matches a committed golden list.
- [ ] **AC3.** The spec states the successor rule and the location decision.
- [ ] **AC4.** A seeded edge to a skill that does not exist fails the script.
- [ ] **AC5.** Skill successors, when carried in skill frontmatter, sit under `metadata` and validate against `contracts/skill.schema.json`.

## Follow-ons

- eugenelim: `brief:skill-sequence-wayfinding-delivery` slices W2 to W4; deliverable orientation in a later brief.

## Assumptions

- Open question for eugenelim: where the successor lives. Recommended default: the skill `metadata` table, because `contracts/skill.schema.json` accepts nested keys there (checked 2026-11-05: a nested key validates and a top-level key is rejected) and `JOURNEY.md` stays untouched.
- The set of packs is whatever `JOURNEY.md` files exist when the script runs (fifteen on 2026-11-05).
