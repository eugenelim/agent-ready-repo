# Trustworthy organisation-owned catalogues

- **Slug:** `trustworthy-org-owned-catalogues` <!-- canonical identity; independent of the filename ordinal -->
- **Kind:** opportunity <!-- chain rung: the need this strategy addresses on the opportunity-solution tree; orthogonal to Level -->
- **Status:** Draft
- **Level:** product-strategy
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** ai-native-ecosystem — [AI-native ecosystem](VISION-0001-ai-native-ecosystem.md)

## Outcome

- **Steerable input:** The effort an organisation spends deciding whether a pack is safe, current and composable with what it already runs — and the effort it spends publishing its own.
- **Lagging outcome:** An organisation runs its own catalogue of agent capability that it trusts, composes and extends — including packs it never publishes — rather than consuming an external one on faith or building everything itself. Its own packs are first-class alongside anything it adopts, not second-class extensions bolted onto someone else's catalogue.
- **Guardrail:** Trust is established by contract and evidence, never by reputation. Composition never silently changes what an installed capability does, and an organisation's own packs are first-class rather than second-class extensions.

## Opportunity

- **Functional job:** Find, judge, compose and publish agent capability for an organisation, with enough evidence to defend the choice.
- **Emotional job:** Install something without wondering what it will do, what it depends on, or whether it is still maintained.
- **Social job:** Answer a security or procurement question about an installed capability with a contract and provenance rather than an assurance.
- **Struggling moment:** Capability is distributed as files with no contract, no composition semantics and no discovery surface, so an organisation either trusts an external source on faith or rebuilds internally. Neither scales, and both are how an agent platform stops being adoptable.

**Why an organisation owns rather than consumes.** None of these is about the catalogue being better than an alternative; all four are about control:

- **Security.** A pack encodes how the organisation actually works. Publishing it, or running one whose contents it cannot audit, is an exposure it will not accept.
- **Competitive advantage.** The workflows worth packaging are often the differentiator. An organisation that cannot keep a pack private cannot package its best work at all.
- **Integration with its own systems.** Capability has to reach internal toolsets, services and data that no external catalogue knows about.
- **Custom workflows.** The organisation's process is its own; a catalogue that only distributes someone else's loops does not fit it.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this strategy's outcome.

## Unresolved questions

- Whether an organisation wants to own a catalogue rather than consume one. The load-bearing bet, untested.
- Whether the six areas are one strategy or two: projection and install lifecycle are held here by absence of another owner rather than by fit.
- Whether contract-and-evidence trust satisfies a real security or procurement review.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Boundary

Includes everything between a pack's source and an organisation trusting what it runs, in six areas the backlog actually occupies:

- **Contract authority and composition semantics** — what a pack declares, and what composing two of them means.
- **Multi-host projection** — one source of capability rendered into each host's native shape, and the route set that defines which hosts are reachable.
- **Install, upgrade and integrity lifecycle** — how capability arrives, stays current, and proves it was not altered.
- **Publication trust and release integrity** — identity, provenance, digests, and the reviewable boundary a publish crosses.
- **Discovery and search** — the semantic index and the verbs over it.
- **Adoption, evaluation and operation** — the surfaces an organisation judges a pack by, and the settings it runs a catalogue with.

Excludes the loops and packs whose content it distributes ([Platform Core](STRAT-0002-platform-core.md)), the model of work ([Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md)), and the non-engineering operating model ([Autonomous product-team operating model](STRAT-0003-autonomous-product-team-operating-model.md)). It is the distribution and trust layer beneath all three, not a participant in any of them.

Projection and install lifecycle are named here because Platform Core's boundary explicitly excludes distribution, so they have no other owner. The earlier boundary omitted both while naming discovery, which is the smallest of the six areas — a scope statement that missed 19 of the 40 intents in its own territory.

## Assumptions

- **An organisation wants to own a catalogue rather than consume one.** The *motive* is not in doubt — security, competitive advantage, internal integration and custom workflows are named in the Opportunity above and are ordinary enterprise drivers. What is **untested** is whether this catalogue lets them act on it: whether an organisation can author, keep private, compose and operate its own packs here without a hosted registry, and whether doing so is cheaper than the internal tooling it would otherwise build. That is the load-bearing bet, and it is a question about this product rather than about demand.
- **The six areas are one strategy rather than two.** Projection and install lifecycle could be a platform concern rather than a distribution one. They are held here because Platform Core's boundary excludes distribution and no other strategy claims them, which is an argument from absence, not from fit. **Untested**, and the assumption most likely to force a re-cut.
- **Knowledge surface:** in-repo doc set and the `ini-007` queue. Extracted 2026-09-18 from [RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md); mined against the live backlog 2026-09-19.

**Not de-risked.** No assumption above carries a kill condition. Delivery has settled buildability questions, not the desirability bet, so re-enter `de-risk-intent` before treating this as a tested strategy.

What delivery has already settled is recorded under **Delivery to date** rather than carried here as a bet.


## Delivery to date

This strategy is **not greenfield**. Its work has been running as the `ini-007` queue, "Catalogue Contracts, Composition, Semantics, and Discovery", `active` at milestone *M2 · Authoring Discovery + Information Architecture*, with 16 specs Shipped — contract convergence, pack integrations, source identity, verifier correctness, classification, semantic contracts and neutral index, enterprise authoring, OKF projection and discovery, and direct skill-repository installation.

[RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md) is Accepted and is this strategy's design authority, not its charter. One Draft delivery brief, [catalogue discovery and release integrity](../briefs/catalogue-discovery-and-release-integrity.md), carries the next tranche.

Delivery also settles one of this strategy's original assumptions. **Contract-and-evidence trust is mechanically in place**: contract convergence, source identity, semantic contracts and the neutral index all shipped. What remains untested is whether that mechanism satisfies a real security or procurement review — the social job this strategy claims — which is a question about adopters, not about the mechanism.

## Decomposition

Forty intents sit in this strategy's territory and **none declares a parent**, so the graph cannot currently show that this strategy has any work under it. They group into six capability-shaped clusters, which are the proposed cut:

| Proposed capability | Intents | Notable |
| --- | --- | --- |
| Multi-host projection and the route set | 10 | `distribution-route-registry`, `codex-plugin-route`, `cross-adapter-behavior-enforcement` |
| Publication trust and release integrity | 10 | `plugin-publish-trust-boundary`, `catalogue-wave5-release-integrity` |
| Install, upgrade and integrity lifecycle | 9 | `agentbundle-install-integrity`, `direct-skill-lifecycle` |
| Adoption and evaluation surfaces | 6 | `claude-apps-first-value-entry`, `catalogue-wave7-marketing-evaluator` |
| Discovery and search | 3 | `catalogue-search-verb`, `catalogue-rules-primitive` |
| Catalogue operation | 2 | `catalogue-level-telemetry-endpoint-default` |

The missing parent edges are this strategy's problem to fix, not the children's. Four of the forty have already reached a terminal shaping state without one — `catalogue-trust-store-trust-settings`, `convenient-install-defaults-followons`, `plugin-root-name-collision-guard`, `upgrade-orphan-removal-on-projection-shape-change` — and an intent with no parent cannot roll up, so this strategy can never compute as fulfilled while any of them hangs loose. Each child's own status stays its own to declare.

### Decomposition decisions

- **The cut follows the backlog, not RFC-0076's four headings.** The RFC names contracts, composition, semantics and discovery. Two of the three largest real clusters — projection and install lifecycle — have no heading there, so cutting to the RFC would have reproduced the boundary gap this mining found.
- **No capability intents were minted yet.** The cut is recorded here as the proposed partition; creating six capability files is a decomposition step with its own review, and the parent is still Draft and un-de-risked.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Extracted 2026-09-18 from [`docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md`](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md), and mined 2026-09-19 against the live `ini-007` queue.
