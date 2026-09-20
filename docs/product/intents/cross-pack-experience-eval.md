# Cross-pack experience evaluation

- **Slug:** `cross-pack-experience-eval` <!-- canonical identity; independent of any filename ordinal -->
- **Status:** Draft
- **Level:** feature
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** [Digital experience doctrine](digital-experience-doctrine.md)
- **Milestone:** M5 in RFC-0071's implementation sequence
- **Authority:** [RFC-0071 D7](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Maintainers can run a golden-path evaluation across strategy, shaping, experience design, frontend engineering, rendered output, and measurement to prove the whole digital-product arc works together.

## Opportunity

Each affected pack has its own evaluation surfaces, but no executable check currently demonstrates that their combined handoffs produce an observable end-to-end experience.

## Assumptions

- The upstream doctrine slices define the artifacts and handoffs that the golden path must exercise.

## What the decision requires

- Put the cross-pack golden-path eval in `packs/experience-design/evals/`; experience design is the terminal whole-journey reviewer (RFC-0071 D7).
- Cover four fixture types: public marketing plus docs, SaaS onboarding plus workspace, internal dashboard, and transactional service (RFC-0071 Area F).
- Add deterministic `tools/` checks for referenced skills, phantom handoffs, risk-mode contract fields, contract-copy drift, and evidence-manifest entries (RFC-0071 Area F).
- Start integrated evals report-only and calibrate them before promoting them to gates (RFC-0071 Area F).
- Deliver M5 only after M2 through M4 in the accepted implementation sequence (RFC-0071 § Implementation sequence).

### Observed state — 2026-09-20

Each row is a check against the live tree (`packs/`, `guides/`, `web/`,
`docs-site/`, `tools/`, `packages/`), re-runnable rather than trusted. Frozen
spec bodies under `docs/specs/` are historical records and were not counted as
evidence. This is an observation on a date, not a status field.

| Requirement | Observed | Check |
| --- | --- | --- |
| golden-path eval in `packs/experience-design/evals/` | not started | that directory does not exist; all 120 `evals/` dirs in the tree sit at `packs/*/.apm/skills/*/evals/` |
| four fixture types | not started | the four names → 1 unrelated hit in `core/init-project` eval queries; no fixture set exists |
| five deterministic `tools/` checks | partial | 1 of 5 — `tools/catalogue/check_contract_parity.py` ships. `tools/test-all.py:88-93` records that chain completeness, phantom-handoff resolution and boundary-guard adjacency "have no successor"; risk-mode and evidence-manifest checks → 0 hits |
| start report-only, calibrate before gating | not started | the integrated eval does not exist. The precedent holds for the *existing* Tier-A eval: `.github/workflows/pack-evals.yml` runs it `continue-on-error` |
| deliver M5 only after M2–M4 | partial | ordering is encoded — `workspace.toml:518` lists 7 unmet `needs` — but the predecessors are still intents, not specs |

**0 shipped · 2 partial · 3 not started.**

Two stale references in this intent's own wording:

- It names `packs/experience-design/evals/` as the eval home. The live
  convention is `packs/<pack>/.apm/skills/<skill>/evals/`; there are 120 such
  directories and zero pack-level ones.
- Its runbook names `tools/run-pack-evals.py`, which does not exist. The runner
  is `agentbundle pack evals run`, which is what
  `.github/workflows/pack-evals.yml` actually invokes. CI is fine; the citation
  is not — and the same dead path is repeated in the `[pack.evals]` comment of
  at least five `pack.toml` files.

## Non-goals

- Promoting the cross-pack eval to a gate is deferred until calibration evidence includes at least two weak-fixture runs and one real-product fixture (RFC-0071 Follow-on work).

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
