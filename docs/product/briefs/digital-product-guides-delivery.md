# Brief: adopters can follow the whole digital-product workflow from the guides

- **Slug:** `digital-product-guides-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/digital-product-guides-update.md`](../intents/digital-product-guides-update.md), cut into slices on 2026-11-05 from a read of the code and specs.
- **Parent intent:** intent:digital-product-guides-update

## Outcome

An adopter finds an intent index for each of the four doctrine packs, one host-neutral end-to-end tutorial, and an adapter compatibility matrix with short host overlays, and each claim traces to a dated receipt or says it is not measured.

## Success metrics

- `product-strategy`, `product-engineering` and `frontend-engineering` each carry a pack-wide intent index whose routes all resolve to registered skills, checked by a test. `experience-design` already has one.
- The compatibility matrix names the adapter-contract revision and marks every primitive supported, transformed, degraded or dropped.
- The tutorial runs the chain strategy, shaping, design, build using a recorded fixture as its worked example.

## Scope / Non-goals

**In scope:**

- Three missing pack indexes and the check that verifies them.
- Host overlays on their own page under `guides/_shared/reference/`, linking to the page `guides/_shared/reference/adapter-support.md`; the generated support block there is owned by `claude-manifest-migration-support-claims-delivery` slice P1 and is not a dependency of G2. The compatibility matrix and overlays use `contracts/adapter.schema.json` and `docs/architecture/runtime-adapter-crosswalk.md` (record the revision in the matrix).
- One tutorial under the shared guides, linked from the four packs, including a section that distinguishes filesystem Agent Skills, host plugins, hooks, agents and commands, Skills over MCP, and A2A `AgentSkill` as separate contracts (owned by G3).

**Non-goals:**

- A docs-generation platform.
- Live host validation (follow-up below).
- Merging those contracts into one concept; G3 only distinguishes them.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| G1 | Intent indexes for the three packs without one, plus a test that each route resolves to a registered skill. | The new test passes on the tree and fails on a seeded dead route; guide-index check | none | Ordering waiver (Constraints) |
| G2 | Host overlays on a separate page that links to `adapter-support.md` (its generated block comes from the manifest brief's P1; G2 does not wait for it), plus the compatibility columns from the adapter contract; live-eval column reads `not measured` until receipts exist. | Drift test compares the matrix with the adapter contract; link check | none | Ordering waiver (Constraints) |
| G3 | Host-neutral end-to-end tutorial using a recorded fixture, linked from the pack guides. | The tutorial contains the contract-distinction section and links an E2 golden-path report (a test fails on a missing link); guide affordance audit shows chat input, supplied input, sample output and stated outcome; links resolve | G1, brief:cross-pack-experience-eval-delivery slice E2, brief:skill-sequence-wayfinding-delivery slice W1 (edge data for the tutorial's next steps) | waits until E2 and W1 are delivered |

### Manual or live residue, split off as non-blocking follow-ups

- Last-validated host versions and dates for the matrix. They come from the live per-host runs that `cross-pack-experience-eval-delivery` names as its dispatch-only follow-up (owner eugenelim) and are recorded in the matrix when those runs exist.

## Constraints / Appetite

Waiver recorded 2026-11-05 by eugenelim, lifecycle owner: the RFC-0071 ordering is waived for slices G1 and G2 only. The rest of M6 keeps the strict order, and RFC-0071 text is unchanged.

Three small sessions; G1 and G2 can run in parallel.

## Assumptions / Risks

- Riskiest assumption: indexes plus one tutorial are enough without a new docs platform. G1 tests it on three packs.
- Risk: the tutorial repeats next-step edges that the wayfinding edge model owns; G3 depends on W1 for that reason.

## Ready gaps (Draft only)

None open; the ordering waiver is recorded.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

- Parent intent: [`digital-product-guides-update.md`](../intents/digital-product-guides-update.md).
