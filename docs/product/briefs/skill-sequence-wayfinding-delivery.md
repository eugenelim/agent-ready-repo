# Brief: a practitioner always knows what to run next and what the step leaves them holding

- **Slug:** `skill-sequence-wayfinding-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as reviewed `Clean` by an independent delivery-brief review at commit `b2cfd8ecf`; the later edits were wording corrections, recorded as nonmaterial by the lifecycle owner. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/skill-sequence-wayfinding.md`](../intents/skill-sequence-wayfinding.md), cut into slices on 2026-11-05 from a read of the code and specs.
- **Parent intent:** capability:skill-sequence-wayfinding

## Outcome

For each pack with a declared sequence, every edge and terminal node can be answered from the skill or guide surface: position, next step, and the dependency reason for that edge. Each answer matches the pack's declared edge model.

## Success metrics

- A script enumerates the closed set of edges and terminal nodes across the packs that ship a `JOURNEY.md` (fifteen today; the files themselves settle the set).
- A lint fails when a skill's stated successor disagrees with that edge model.
- The pilot pack passes a three-question check (position, next step, dependency reason) on every edge.

## Scope / Non-goals

**In scope:**

- The edge model and its derivation.
- A drift lint.
- Projection of next-step text, one feature spec per pack, starting with `experience-design`, plus the cross-pack edges (for example `copy-direction` to `ux-writing`) as their own slice.

**Non-goals:**

- Deliverable orientation (path and shape); it needs the pilot result and is deferred to its own brief.
- Autonomous chaining of skills; the surface names the next step and the practitioner runs it.
- Rewriting skill methods.
- A new navigation product.
- Packs without a `JOURNEY.md` in this brief.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| W1 | Edge model, plus a derivation script; the slice spec answers where the successor lives (skill `metadata` extension table or machine-readable `JOURNEY.md` stages; parent Unresolved question 1). The script prints every edge and terminal, and the slice states the successor rule (which skills name a successor). | Schema validation of all fifteen journeys; the script output is a stable golden list | none | none |
| W2 | Drift lint: a skill's stated successor must match the edge model for packs that opted in, where opting in is a per-pack marker that W2 defines and W3 sets for its pack; with an empty opt-in set the lint passes and says so. | pytest with a seeded disagreement, a case with zero opted-in packs that passes, and a case with one opted-in pack that fails on a disagreeing successor; clean on the tree | W1 | none |
| W3 | Projection of next-step text into one pack's skills; first pack `experience-design`; each later pack is its own spec. W3 sets the opt-in marker (defined in W2) for its pack and a check script that reads the pack's edge model, each skill's `SKILL.md` successor statement, and the journey stages, and asks position, next step and reason for every edge, and for every terminal node confirms the surface says it is terminal. | The check script passes for the pack, and a test fails if the pack's opt-in marker is missing; W2 stays clean | W2 | Pack-owner decision on each disagreement with a hand-written successor; default if none is given: keep the hand-written text and record the disagreement |
| W4 | Cross-pack edges: skills whose successor lives in another pack, declared once in the edge model. | Edge script lists each cross-pack edge; W2 checks each one between two opted-in packs, and the slice fails if fewer than two packs are opted in | W2 and W3 for two packs | none |

### Manual or live residue, split off as non-blocking follow-ups

- Practitioner testing of the surface by a person; the W3 check script replaces it.

## Constraints / Appetite

W1 and W2 first (two sessions). W3 is one session per pack; W4 is one session.

## Assumptions / Risks

- Riskiest assumption: the journey contract can carry edges without breaking its 15 files. W1 validates that with the schema.
- Risk: the shipped `docs-wayfinding-cluster` and `docs-job-pages` specs may already cover part of this; the W1 spec cites what they own.
- Risk: no rule yet says which skills name a successor (three predicates returned 1, 24 and 17). W1 states that successor rule.
- Risk: the 24 hand-written successors may disagree with the edge model. Any disagreement goes to the pack owner for a decision before W3 rewrites that pack's text.

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

- Parent intent: [`skill-sequence-wayfinding.md`](../intents/skill-sequence-wayfinding.md).
