# Cross-pack experience evaluation

- **Slug:** `cross-pack-experience-eval` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:digital-experience-doctrine
- **Milestone:** M5 in RFC-0071's implementation sequence
- **Governed by:** [RFC-0071 D7](../../rfc/0071-digital-experience-doctrine.md)
- **De-risked:** no
- **Shaping-reviewed:** no
- **Decomposed:** 2026-10-01 spec

## Outcome

Maintainers can run a golden-path evaluation across strategy, shaping, experience design, frontend engineering, rendered output, and measurement to prove the whole digital-product arc works together.

## Opportunity

Each affected pack has its own evaluation surfaces, but no executable check currently demonstrates that their combined handoffs produce an observable end-to-end experience.

## Assumptions

- Approved upstream doctrine specs define the artifact identities, handoff semantics, and negative cases the golden path must exercise; delivered implementations later supply the executable fixtures.
- **Knowledge surface:** the in-repository RFC, pack, guide, adapter contract, workflow, and spec corpus plus the 2026-10-01 current-standards survey.

## Riskiest assumption

A bounded layered evaluation can prove source projection, host activation,
handoff, final artifact, and journey outcome well enough without becoming a
general-purpose eval platform or remote-agent protocol implementation.

## What the decision requires

- Resolve RFC-0071 D7's stale destination explicitly. Skill-local activation
  fixtures stay with their skills; the cross-pack orchestrator belongs in an
  existing repository-level test or tool ownership area, with Experience
  Design retaining the terminal whole-journey review responsibility.
- Cover four fixture types: public marketing plus docs, SaaS onboarding plus workspace, internal dashboard, and transactional service (RFC-0071 Area F).
- Add deterministic `tools/` checks for referenced skills, phantom handoffs, risk-mode contract fields, contract-copy drift, and evidence-manifest entries (RFC-0071 Area F).
- Validate canonical Agent Skills sources and every supported adapter
  projection, including declared transformations, degradations, and dropped
  primitives. Run positive and negative activation cases on each supported
  headless host, and record an explicit manual or not-measured row for a host
  without automatable evidence.
- Separate activation, process, handoff, final artifact, journey outcome,
  style, and efficiency signals. Compare against a no-skill or prior-version
  baseline and record host version, model, adapter-contract version, fixture,
  permissions, and measurement status.
- Start integrated evals report-only and calibrate them before promoting them to gates (RFC-0071 Area F).
- Deliver M5 only after M2 through M4 in the accepted implementation sequence (RFC-0071 § Implementation sequence).

### Observed state — 2026-10-01

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| golden-path eval owned by experience design | not started; destination needs correction | no pack-level eval exists. The live convention is skill-local evals, so the spec must choose a real owner inside the pack rather than create the dead `packs/experience-design/evals/` shape literally |
| four fixture types | not started | the four names → 1 unrelated hit in `core/init-project` eval queries; no fixture set exists |
| five deterministic seam checks | partial | contract parity and general cross-pack boundary checks exist, but no one harness establishes chain completeness, phantom-handoff resolution, risk-mode fields, and evidence-manifest entries together |
| start report-only, calibrate before gating | not started | the integrated eval does not exist. The precedent holds for the *existing* Tier-A eval: `.github/workflows/pack-evals.yml` runs it `continue-on-error` |
| deliver M5 only after M2–M4 | waits on predecessor delivery contracts | workspace dependencies encode the order. M5 needs approved M2a, M2b, M3c, and M3d specs before its own spec can pin the fixture and handoff contract; execution still waits for their delivered artifacts |
| supported adapter and host matrix | not started | `agentbundle pack evals run` projects one pack, uses a Claude-only detector, and excludes cross-pack collisions; the four doctrine packs also do not share the same declared adapter set |

**0 shipped · 1 partial · 4 not started · 1 blocked; the destination decision is also open.**

Two stale references in this intent's own wording:

- It names `packs/experience-design/evals/` as the eval home. The live
  convention is `packs/<pack>/.apm/skills/<skill>/evals/`; there are 120 such
  directories and zero pack-level ones.
- Its runbook names `tools/run-pack-evals.py`, which does not exist. The runner
  is `agentbundle pack evals run`, which is what
  `.github/workflows/pack-evals.yml` actually invokes. CI is fine; the citation
  is not — and the same dead path is repeated in the `[pack.evals]` comment of
  at least five `pack.toml` files.

### Current-standards pressure test — 2026-10-01

The [external survey](../research/digital-experience-doctrine-current-standards-survey.md)
shows that identical `SKILL.md` source does not prove identical host behavior.
The local adapter contract is v0.18, while official headless execution surfaces
now exist for several supported hosts. Use deterministic checks across every
projection, a small live activation suite across supported headless hosts,
rotating full journeys, and bounded manual GUI smoke tests. Do not add blanket
MCP or A2A conformance; pin those standards only when a fixture crosses that
boundary.

### Spec-authoring dependency

Refresh and de-risk this intent when M2a, M2b, M3c, and M3d have approved
specs. Their contracts are the minimum evidence needed to name the crossing
artifacts, negative fixtures, and layer-specific verdicts without freezing
guesses into the eval. Delivery of M5 remains ordered after the upstream work;
spec authoring does not need to wait for every implementation once those
contracts are approved.

## Non-goals

- Promoting the cross-pack eval to a gate is deferred until calibration evidence includes at least two weak-fixture runs and one real-product fixture (RFC-0071 Follow-on work).

## Decomposition

One same-repository spec and plan at
`docs/specs/cross-pack-experience-eval/` own M5 once its predecessor intents
are terminal. They correct the stale destination, then deliver the layered
source, projection, activation, handoff, journey, and calibration checks as one
evaluation product. This remains one feature because every layer proves the
same cross-pack journey. Re-decompose if a general-purpose eval platform or a
remote-agent protocol implementation enters scope.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
