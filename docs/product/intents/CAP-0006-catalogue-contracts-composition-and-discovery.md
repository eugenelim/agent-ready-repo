# Catalogue contracts, composition, semantics and discovery

- **Slug:** `catalogue-contracts-composition-and-discovery` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:trustworthy-org-owned-catalogues
- **Shaping-reviewed:** 2026-09-24

## Outcome

- **Steerable input:** The share of questions about a catalogue that only its maintainers can answer.
- **Lagging outcome:** A catalogue is usable by people who did not build it. Five things become possible without a maintainer in the loop, and they are the five this capability still owes: **finding** what a catalogue holds without knowing a name; **confirming** that a received copy is the one that was published; **learning** to author a catalogue; **judging**, as an outsider, whether a catalogue is worth adopting at all; and the first-party catalogue **running on** this capability rather than beside it.
- **Guardrail:** Every answer comes from a contract, a manifest, a digest, a test or a generated surface — never from prose an author remembered to update. A discovery or evaluation surface never asserts more than its evidence supports.

The five clauses above are stated as five because § Decomposition must
partition them one-to-one. What the capability has already delivered — the
contracts, composition semantics, index and upstream sync that make those five
reachable — is § Delivery to date, not an outcome clause, because a delivered
thing has no child left to own it.

## Opportunity

- **Functional job:** Find what a catalogue contains, confirm the copy in hand is intact, learn to author one, and judge whether adopting one is worth it.
- **Emotional job:** Extend or adopt a pack without first reading the maintainer's mind about what it depends on.
- **Social job:** Show a reviewer where a claim about the catalogue is enforced, rather than asserting it.
- **Struggling moment:** The catalogue's facts live in prose, in code and in the maintainer's head at once. Every question about it is answered by a person, so the catalogue does not scale past the people who built it — and neither adopting one nor building one is something an outsider can do unaided.

## Boundary

This capability owns the catalogue's **own** contracts, composition semantics,
discovery surfaces and release integrity. It does not own how a pack is
installed into an adopter's tree, which is the install lifecycle, nor the
projection of pack content into host-specific artifacts. Both sit under the
parent strategy beside this capability rather than inside it.

Its design authority is
[RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md),
Accepted 2026-07-29. This intent is the outcome that RFC serves; the RFC is not
this intent's charter, and where the two differ the RFC's § Wave-to-decision
mapping records the decisions and this intent records the outcome.

## Delivery to date

This capability is **not greenfield**. Its work has been running as the
`ini-007` queue. The shipped specs below are delivery evidence, not members of
the decomposition: a capability decomposes into intents, and a spec is what a
child intent produced. They are grouped by the question each answered.

- **Contract convergence and verifier correctness** — what a pack declares and
  whether the verifier reads it faithfully: `catalogue-wave1-contract-convergence`,
  `catalogue-verifier-correctness`, `catalogue-verify-classification`,
  `catalogue-source-identity`.
- **Composition** — how packs combine without silently changing one another:
  `catalogue-wave2-pack-integrations`, `pack-test-boundary-remaining-packs`,
  `pack-test-compatibility-classes`.
- **Semantics and index** — the neutral, deterministic description a reader or
  a tool consumes: `catalogue-wave4-semantic-contracts-index`,
  `catalogue-wave3-enterprise-authoring-discovery`, `okf-authoring-projection`,
  `okf-catalogue-discovery`.
- **Upstream sync** — an adopter's derived catalogue taking later upstream
  change: `catalogue-sync-dry-run`, `catalogue-sync-apply`, and
  [`catalogue-package-sync`](../../specs/catalogue-package-sync/spec.md), the
  last phase of
  [`upstream-sync.md`](../../architecture/catalogue/upstream-sync.md) § Rollout.
- **Documentation and navigation** — `documentation-entry-navigation`,
  `rendered-site-link-debt`, `governance-guides-cleanup`,
  `direct-skill-repository-installation`, `lint-performance-p0`.

## Decomposition

Open, as its remaining children:

- [Catalogue search verb](catalogue-search-verb.md) — a verb over the neutral semantic index. Answers *can a person find a capability without knowing its name*.
- [Catalogue release integrity](catalogue-wave5-release-integrity.md) — digests, comparisons and same-version mutation refusal. Answers *is the copy in hand the one that was published*.
- [Catalogue technical documentation architecture](catalogue-wave6-technical-docs-ia.md) — an author-focused route for building a catalogue. Answers *can someone build one of these without reading the source*.
- [Catalogue marketing evaluator surface](catalogue-wave7-marketing-evaluator.md) — an evaluator-facing surface. Answers *can a prospective adopter judge this before adopting it*.
- [Catalogue migration and closeout](catalogue-wave9-migration-closeout.md) — first-party migration and closeout. Answers *is the first-party catalogue actually on this capability*.

RFC-0076 assigns no new decision to Wave 8, which converges README and
CONTRIBUTING by applying decisions D1–D4. It is therefore not a child here.

**The partition.** Each member owns exactly one clause of the lagging outcome,
and each clause has exactly one member:

| Outcome clause | Member |
| --- | --- |
| finding | Catalogue search verb |
| confirming | Catalogue release integrity |
| learning | Catalogue technical documentation architecture |
| judging | Catalogue marketing evaluator surface |
| running on | Catalogue migration and closeout |

The marketing evaluator surface is the loosest member, and *judging* is the
clause written to hold it honestly rather than to justify it. It evaluates the
catalogue as a whole rather than a pack inside it, and STRAT-0004's partition
assigns it to a separate adoption-and-evaluation capability. It is held here
because it was cut with the other four against RFC-0076's wave mapping.
Whether it stays is the open question this intent's own de-risk should settle,
and moving it out would take the *judging* clause with it.

## Assumptions

- That the five open children are still the right cut. They were cut against
  RFC-0076's wave mapping in 2026-09-03 and have not been revisited since four
  of their prerequisites shipped.

## Unresolved questions

- Whether the search verb and the marketing evaluator surface are one
  discovery outcome or two. They were cut as separate waves by the RFC's
  mapping, which is a delivery-sequencing artifact rather than an outcome
  boundary.
- Whether release integrity belongs to this capability or to the install
  lifecycle beside it. It is held here because the digest it verifies is a
  property of the catalogue's own publication.
- The parent strategy's open question of whether its six areas are one strategy
  or two bears on this boundary and is not answered here.
