# Brief: a platform lead can judge the catalogue model from one claim-then-proof page

- **Slug:** `catalogue-evaluator-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/catalogue-wave7-marketing-evaluator.md`](../intents/catalogue-wave7-marketing-evaluator.md), cut into slices on 2026-11-05 from a read of the code and a run of the published-specification checks.
- **Parent intent:** intent:catalogue-wave7-marketing-evaluator

## Outcome

A platform lead can open `/evaluate/` on the marketing site, read each of the nine RFC-0076 D10 claims, and follow every claim to a public proof page. Catalogue and pack pages show only facts the neutral index carries, and optional pack integrations appear as a relationship view.

## Success metrics

- All nine claims link to a destination that is public: a docs-site page, a page of the published catalogue specification, or the PyPI package page.
- The pack and catalogue pages take version, scope, adapters, integrations and documentation links from `catalogue-index.json`, except the declared site documentation link for packs the index leaves without one, which the page labels as a site fallback. Install-route facts (`pluginInstallable`, the install command) stay with their current owners.

## Scope / Non-goals

**In scope:**

- The platform-lead journey stub, the `/evaluate/` page, index-backed facts, and the D6 relationship view, as RFC-0076 D10 states them.

**Non-goals:**

- A `lifecycle` field, a catalogue version, a visual redesign, publishing the specification, and the Build a Catalogue route.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| E2 | The platform-lead journey stub: the reader, their decision, and the claims they check, written as a journey under `docs/design/journeys/`. | No existing lint reads `docs/design/journeys/` (`tools/lint-journey-contract.py` reads `web/src/content/journeys/`, which holds pack journeys), so E2 adds a small check that the stub names its reader, their decision, and each of the nine claims | none | none |
| E3 | The `/evaluate/` spec and page with a build-time link check. | `web` build; an offline link check covers internal links only, fails on any link into maintainer-only material (an RFC, spec or `docs/guides/` page), and allow-lists the PyPI link declared in `site.toml`; rendered-output test | E2 | none |
| E4 | Index-backed facts on the catalogue and pack pages, with a labelled site fallback for the 8 packs that lack a documentation link. | Build input generated from `catalogue-index.json`; a test fails if version, scope, adapters, integrations or documentation links come from anywhere but the index, other than the labelled fallback | none | none |
| E5 | The pack relationship view with the D6 labels. | Rendered-output test over a fixture index with forward and inverse integrations | E4 | none |

The claim re-probe against the published specification is a governance step outside the slice table: it amends the parent intent and needs no spec. It is recorded in the parent intent's Re-probe result.

### Manual or live residue, split off as non-blocking follow-ups

- Five-minute sessions with platform leads on the released page.
- A signed-out browser pass over the deployed `/evaluate/` links.

## Constraints / Appetite

Four to five sessions. E2 and E4 can run in parallel.

## Assumptions / Risks

- Riskiest assumption, two halves: every claim has a public proof page, which the re-probe recorded in the parent intent settled and the link check keeps true; and a platform lead can make the build-or-adopt call from the page, which is still unvalidated and is checked by the non-blocking platform-lead sessions in the manual residue.
- Risk: 15 of 23 packs have a documentation link in the index. E4 declares a labelled fallback, so the page never claims more than the index or a named fallback holds.

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |

## Governance references (optional)

- [RFC-0076 D10](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md) and [RFC-0109](../../rfc/0109-catalogue-specification-publication.md).

## Provenance

- Parent intent: [`catalogue-wave7-marketing-evaluator.md`](../intents/catalogue-wave7-marketing-evaluator.md).
