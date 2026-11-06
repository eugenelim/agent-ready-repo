# Spec: Project-knowledge closeout measurement tool

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** none — authored when the spec is approved
- **Constrained by:** RFC-0077; `project-knowledge-foundation` spec AC19
- **Brief:** brief:project-knowledge-adoption-closeout-delivery
- **Discovery:** capability:project-knowledge-adoption-closeout
- **Depends on:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Outcome

The owner can read one measurement of project-knowledge adoption, growth, latency, capture loss and operator support for this repository. The report decides whether any scale or durability follow-on has measured pressure.

## What Changes

- A read-only tool that reports adoption (active topic count, distinct `producer` values across topic occurrences), topic counts by scope tier, body-envelope reachability per scope, observation-journal growth under `docs/knowledge/observations`, capture loss (pending observations with no terminal disposition), enquiry latency (wall-clock, report-only) and operator support (refusal codes with no recovery line in the skill references; report-only).
- A fail condition that trips when the retention or derived-index thresholds (the AC19 budgets) cannot be read from the repository.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Tool usage | The tool's `--help` and a short note in the project-knowledge skill references | eugenelim | Test passing | close-work verifies the tests pass |

## Agent Rules

### Always do

- Count from `docs/knowledge/topics.index.json` and the topic files at run time.
- Keep the tool read-only.

### Ask first

- Persisting a result store.

### Never do

- Assert on enquiry latency in a test.
- Write to `docs/knowledge/`.

## Testing Strategy

TDD with fixture knowledge stores for each measure; a goal-based run over the real tree. Latency is recorded only.

## Acceptance Criteria

- [ ] **AC1.** Run against the real tree, the tool's active topic count equals a count taken from the topic files.
- [ ] **AC2.** Seeded fixtures test each measure, including a topic scoped repository-wide and a topic on the `tools` base.
- [ ] **AC3.** Capture loss counts pending observations with no terminal disposition in a seeded journal.
- [ ] **AC4.** The tool fails with a named error when the AC19 budget figures cannot be read.
- [ ] **AC5.** The tool writes nothing to the repository.

## Follow-ons

- eugenelim: `brief:project-knowledge-adoption-closeout-delivery` slice K2 and `knowledge-topic-scope-granularity` curation.

## Assumptions

- Open question for eugenelim: where the tool lives. Recommended default: a script under `packs/core/.apm/skills/project-knowledge/scripts/` beside the other project-knowledge scripts, so it ships with the skill.
- The AC19 figures are read from `docs/specs/project-knowledge-foundation/spec.md`; the spec assumes the tool may parse that file or carry a pinned copy with a test that compares them.
