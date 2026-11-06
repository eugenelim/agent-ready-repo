# Catalogue migration and closeout

- **Slug:** `catalogue-wave9-migration-closeout`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Parent intent:** capability:catalogue-trust-and-adoption
- **Governed by:** [RFC-0076 § Wave-to-decision mapping — Wave 9](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
- **Depends on:** intent:catalogue-wave7-marketing-evaluator

## Outcome

First-party maintainers can complete the catalogue migration with the release, evaluator, and technical-documentation outcomes reconciled into a verified closeout.

## Opportunity

The foundation, discovery, and presentation waves are delivered through separate boundaries, so the repository still needs an owned final migration and closure step that proves they work together.

## Current state — checked 2026-11-05

Three of the four foundations are done: `catalogue-wave2-pack-integrations` and `documentation-entry-navigation` are Shipped specs, and `catalogue-wave5-release-integrity` is a Fulfilled intent with a Shipped spec (`catalogue-wave6-technical-docs-ia` is also Fulfilled). Only `catalogue-wave7-marketing-evaluator` is open, so it is the one dependency kept above. `agentbundle catalogue verify --root .` runs agent-only (about 80 seconds).

## Assumptions

- Closeout adds no new behaviour. It confirms the delivered waves work together and closes the parent capability.
- **Riskiest assumption:** once wave 7 ships, nothing else blocks closing the parent capability. Test it agent-only: run `agentbundle catalogue verify --root .` and the contract parity checks, then let `close-work` return the closure verdict with every live descendant named.

## What the decision requires

- Wave 9 is the first-party migration and closeout wave; RFC-0076 states no finer requirements for this slice (RFC-0076 § Wave-to-decision mapping).

## Non-goals

- Building new behaviour. The intent confirms delivered waves and closes the parent capability.
- Waves 5 and 6, which are already Fulfilled, and wave 7, which owns the evaluator page.
- Wave 8, which RFC-0076 assigns no new decision.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** `navigate_intents.py query --operation tree` and `outstanding` for `capability:catalogue-trust-and-adoption`; `agentbundle catalogue verify --root .`; `tools/catalogue/check_contract_parity.py` and `check_spec_version.py`.
- **Observed:** the capability has five children. Wave 5 and wave 6 are Fulfilled, and three are live: `catalogue-search-verb`, `catalogue-wave7-marketing-evaluator` and this intent. The two catalogue checks pass (19 contract files byte-identical, member `$id`s agree). The verify run took 81 seconds and reported one error, a stray `__pycache__` file under `dist/` (an environment artifact, not a catalogue defect).
- **Verdict:** partly holds, so not stamped. Wave 7 is not the only blocker: closing the capability also needs the search verb terminal. This intent's own closeout checks pass today apart from the stray cache file.

## Readiness

- **Route:** `close-work`, with no spec and no brief. This intent builds nothing.
- **First slice:** once `catalogue-wave7-marketing-evaluator` ships, run `agentbundle catalogue verify --root .` and the release and parity gates on the first-party catalogue, record the result, then let `close-work` check whether `capability:catalogue-trust-and-adoption` is eligible to close. The capability also waits for `catalogue-search-verb`, which this intent does not cover.
- **Agent-only proof:** the verify run exits 0 with the recorded counts, and `close-work` returns the closure verdict.
- **Owner option:** withdraw this intent and let `close-work` close the capability directly once wave 7 and the search verb are terminal. Nothing else changes, because the intent holds no requirement of its own.
- **Not before:** wave 7 ships. Capability closure needs the search verb terminal as well.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f
