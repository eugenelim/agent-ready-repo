# Brief: close the project-knowledge programme on repository evidence

- **Slug:** `project-knowledge-adoption-closeout-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as reviewed `Clean` by an independent delivery-brief review at commit `97221f5bb`; the later edits were wording corrections, recorded as nonmaterial by the lifecycle owner. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/project-knowledge-adoption-closeout.md`](../intents/project-knowledge-adoption-closeout.md), cut into slices on 2026-11-05 from a read of the code and specs.
- **Parent intent:** capability:project-knowledge-adoption-closeout

## Outcome

The programme closes on measured repository evidence of adoption, repository growth, enquiry latency and capture loss, with privacy checked by the existing project-knowledge confinement and privacy tests and operator support recorded as advisory, and each of the four conditional follow-ons is retained, activated or closed on that evidence.

## Success metrics

- One read-only measurement tool reports adoption, growth, enquiry latency and capture loss for this repository. The thresholds for retention and derived indexing are the published v1 budgets in `docs/specs/project-knowledge-foundation/spec.md` AC19. External capture and multi-project sharing have no numeric threshold in the repository; their threshold is a stated requirement from the owner, so K2 closes them unless one is supplied.
- K2 records the result of the existing project-knowledge confinement and privacy tests as the privacy check; operator support is advisory and gates nothing.
- A closeout spec records gaps against the existing contracts and a disposition for observation retention, derived indexing, external capture durability and multi-project sharing, with the closed-without-implementation default.

## Scope / Non-goals

**In scope:**

- A measurement tool over `docs/knowledge/`: counts and sizes are deterministic; enquiry latency is recorded wall-clock time and is report-only, never asserted.
- The closeout evaluation and dispositions.

**Non-goals:**

- Any follow-on implementation; each needs its own measured trigger and, for storage and sharing, its own RFC.
- Physical-device or external-system evidence.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| K1 | Measurement tool: adoption (active topic count and the number of distinct `producer` values across topic occurrences), topic counts by scope tier, body-envelope reachability per scope, observation journal growth under `docs/knowledge/observations`, capture loss as pending observations with no terminal disposition, counted from the observation journals, enquiry latency recorded as report-only wall-clock time over a fixed enquiry set, and operator support (the number of refusal codes in the project-knowledge scripts that have no recovery line in the skill references; report-only). | The tool computes the topic count at run time from `docs/knowledge/topics.index.json` and matches a count from the topic files; seeded fixtures test each measure; it fails if the retention or derived-index threshold (AC19 budgets) cannot be read from the repository | none | none |
| K2 | Closeout spec: lifecycle evaluation against existing contracts and the four follow-on dispositions. | Dispositions cite K1 output; a test checks each follow-on has a disposition record | K1 | none |

### Manual or live residue, split off as non-blocking follow-ups

- Adoption evidence from other repositories; none is available, so closeout is for this repository only.

## Decisions

- 2026-11-05, eugenelim: K1 may run before the engineering and operational integration survey, because measurement does not need it. K2's lifecycle evaluation covers only the workflow classes already integrated (authoring, review, research); if the survey later adds a class, K2's evaluation is extended rather than reopened.

## Constraints / Appetite

Two small sessions.

## Assumptions / Risks

- Riskiest assumption: repository-contained evidence is enough to close. K1's test is its fail condition: it fails if the retention or derived-index threshold (AC19 budgets) cannot be read from the repository.
- Risk: measured pressure is absent for all four follow-ons, which closes them without work.

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

- Parent intent: [`project-knowledge-adoption-closeout.md`](../intents/project-knowledge-adoption-closeout.md).
