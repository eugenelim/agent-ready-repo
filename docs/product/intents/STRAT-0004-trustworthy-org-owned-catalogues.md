# Trustworthy organisation-owned catalogues

- **Slug:** `trustworthy-org-owned-catalogues` <!-- canonical identity; independent of the filename ordinal -->
- **Kind:** opportunity <!-- chain rung: the need this strategy addresses on the opportunity-solution tree; orthogonal to Level -->
- **Status:** Draft
- **Level:** product-strategy
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** outcome:ai-native-ecosystem

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

- Whether an organisation wants to own a catalogue rather than consume one. The load-bearing bet. § De-risk record names it, predeclares its kill condition and carries its validation hook; the hook is `to-validate`, so the bet is still untested.
- Whether the six areas are one strategy or two: projection and install lifecycle are held here by absence of another owner rather than by fit. Routed, not tested — see § De-risk record.
- Whether contract-and-evidence trust satisfies a real security or procurement review. A second market-existence sub-bet, deliberately not folded into the main hook — see § De-risk record.

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


## De-risk record

- **Level kind:** `product-strategy`, so the dominant assumption is
  **market-existence** — will anyone want this at all, and can it be a
  business. That is categorically not feature desirability, and it is tested
  once here rather than re-litigated under each capability below.
- **Reversibility triage:** **one-way door.** `ini-007` has shipped 18 specs,
  `agentbundle` publishes to PyPI at 0.49.0, and the contracts, CLI surface and
  state schema are interfaces adopters derive trees against. Unwinding the bet
  means withdrawing a published interface, not deleting files. The one-way
  classification sets the default approach.
- **Prototype-approach:** `validate-first`. No prototype in this repository can
  test this bet. The question is whether organisations outside it will carry
  the cost of owning a catalogue, and nothing built here is evidence about
  them.

### Riskiest assumption

An organisation will accept the standing operating cost of owning a catalogue
— curating it, keeping it current, and staffing an owner for it — rather than
consuming an external one or building each capability ad hoc.

What would have to be true, in order of how much each would cost to be wrong:

1. The organisation already has workflows it treats as unpublishable — for
   security or for competitive advantage. Without these, "own rather than
   consume" has no motive and the strategy's four control arguments are
   reasons nobody needs.
2. Someone in the organisation would be accountable for the catalogue. A
   capability with no owner is not adopted, whatever its merits.
3. The cost of owning is below the cost of the two alternatives it displaces.

The strategy's § Opportunity states all four control arguments — security,
competitive advantage, integration, custom workflows — as **rationale**. Every
one is a reason an organisation *would* want this. None is evidence that one
*does*. That gap is the bet.

### Kill condition, predeclared

This is pre-PMF with no traffic, so the bar is qualitative and is set here
before any probe runs.

**Kill if, across six target organisations, fewer than four can name a
workflow they have already packaged or have deliberately refused to publish,
or fewer than four can name the role that would own the catalogue.**

Both conjuncts must clear four of six. They are separated because they fail
differently and the failures mean opposite things: the first failing says the
motive is absent and the strategy is wrong; the second failing says the motive
is real but unstaffable, and the strategy needs a different adoption path
rather than abandonment. A single combined bar would hide which happened.

### Evidence held today

**None that bears on the bet.** Recorded explicitly rather than left to
inference, because this strategy has substantial delivery behind it and
delivery reads like evidence.

- This repository self-hosts its own catalogue, so it is an organisation
  running one. It is **not** evidence: n=1, and the organisation is the
  authors. A tool's makers using it is the weakest possible support for a
  demand claim.
- The 18 shipped `ini-007` specs are evidence the mechanism works, not that
  anyone wants it. § Delivery to date already draws this line for the
  contract-and-evidence half; it holds for the whole bet.
- No adopter interview, pilot, or procurement review has been run.

### Verdict — not yet reached

The kill condition is predeclared and the activity that would settle it is
named below. **Running it is out of this skill's charter and needs a human.**
The intent therefore stays `Status: Draft` and carries no `De-risked:` stamp:
stamping one would assert a verdict nobody reached.

```
validation_hook:
  assumption: >
    An organisation will accept the standing operating cost of owning a
    catalogue rather than consuming an external one or building ad hoc.
  kill_condition: >
    Across six target organisations, fewer than four naming a workflow they
    have packaged or refused to publish, or fewer than four naming the role
    that would own the catalogue.
  activity: >
    Six semi-structured interviews with platform or security leads at
    organisations that already run an internal developer platform. Ask for a
    workflow they would not publish, and for who would own a catalogue, before
    describing this one — describing it first supplies both answers.
  status: to-validate
```

### The other two open questions, routed rather than tested

Neither is the riskiest assumption, and testing either instead would be
comfort-testing.

- **Whether the six areas are one strategy or two** is a two-way door:
  re-cutting capability intents costs edits, not withdrawn interfaces. It is
  now partly live rather than open — [CAP-0006](CAP-0006-catalogue-contracts-composition-and-discovery.md)
  was minted across three rows of § Decomposition's partition, so the next
  capability minted is where the question gets answered in practice.
- **Whether contract-and-evidence trust satisfies a real security or
  procurement review** is a genuine second market-existence sub-bet and the
  more testable of the two, because one real review settles it. It is not
  folded into the hook above: an organisation can want to own a catalogue and
  still fail procurement, and merging them would let a pass on one read as a
  pass on both. It needs its own hook when someone has a review to put it
  through.

## Delivery to date

This strategy is **not greenfield**. Its work has been running as the `ini-007` queue, "Catalogue Contracts, Composition, Semantics, and Discovery", `active` at milestone *M2 · Authoring Discovery + Information Architecture*, with 16 specs Shipped — contract convergence, pack integrations, source identity, verifier correctness, classification, semantic contracts and neutral index, enterprise authoring, OKF projection and discovery, and direct skill-repository installation.

[RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md) is Accepted and is this strategy's design authority, not its charter. The next tranche is carried by [CAP-0006 catalogue contracts, composition and discovery](CAP-0006-catalogue-contracts-composition-and-discovery.md), this strategy's first declared capability child.

Delivery also settles one of this strategy's original assumptions. **Contract-and-evidence trust is mechanically in place**: contract convergence, source identity, semantic contracts and the neutral index all shipped. What remains untested is whether that mechanism satisfies a real security or procurement review — the social job this strategy claims — which is a question about adopters, not about the mechanism.

## Decomposition

Forty intents sit in this strategy's territory and **none declares a parent**, so the graph cannot currently show that this strategy has any work under it. They group into six capability-shaped clusters, which are the proposed cut:

| Proposed capability | Intents | Notable |
| --- | --- | --- |
| Multi-host projection and the route set | 10 | `distribution-route-registry`, `codex-plugin-route`, `cross-adapter-behavior-enforcement` |
| Publication trust and release integrity | 10 | `plugin-publish-trust-boundary`; `catalogue-wave5-release-integrity` absorbed by CAP-0006 |
| Install, upgrade and integrity lifecycle | 9 | `agentbundle-install-integrity`, `direct-skill-lifecycle` |
| Adoption and evaluation surfaces | 6 | `claude-apps-first-value-entry`; `catalogue-wave7-marketing-evaluator` absorbed by CAP-0006 |
| Discovery and search | 3 | `catalogue-rules-primitive`; `catalogue-search-verb` absorbed by CAP-0006 |
| Catalogue operation | 2 | `catalogue-level-telemetry-endpoint-default` |

The missing parent edges are this strategy's problem to fix, not the children's. Four of the forty have already reached a terminal shaping state without one — `catalogue-trust-store-trust-settings`, `convenient-install-defaults-followons`, `plugin-root-name-collision-guard`, `upgrade-orphan-removal-on-projection-shape-change` — and an intent with no parent cannot roll up, so this strategy can never compute as fulfilled while any of them hangs loose. Each child's own status stays its own to declare.

### Decomposition decisions

- **The cut follows the backlog, not RFC-0076's four headings.** The RFC names contracts, composition, semantics and discovery. Two of the three largest real clusters — projection and install lifecycle — have no heading there, so cutting to the RFC would have reproduced the boundary gap this mining found.
- **One capability intent is minted; the other five are not.** [CAP-0006](CAP-0006-catalogue-contracts-composition-and-discovery.md) was minted on 2026-09-24 by owner decision, replacing the Draft delivery brief that carried the same tranche. It is the first child to declare this strategy as its parent. The remaining five clusters stay a proposed partition; creating their files is a decomposition step with its own review, and this parent is still Draft and un-de-risked.
- **CAP-0006 crosses three rows of the partition above, by decision rather than by oversight.** It takes `catalogue-search-verb` from Discovery and search, `catalogue-wave5-release-integrity` from Publication trust and release integrity, and `catalogue-wave7-marketing-evaluator` from Adoption and evaluation surfaces, because all five of its open children were already cut together against RFC-0076's wave mapping and splitting them across three unminted capabilities would have left the tranche with no single owner. It does **not** reproduce the boundary gap the decision above names: its own § Boundary excludes projection and the install lifecycle explicitly, so those two clusters remain unclaimed and still need capabilities of their own. Whether its three donor rows survive as capabilities once it exists is an open question for this strategy's own de-risk.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Extracted 2026-09-18 from [`docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md`](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md), and mined 2026-09-19 against the live `ini-007` queue.
