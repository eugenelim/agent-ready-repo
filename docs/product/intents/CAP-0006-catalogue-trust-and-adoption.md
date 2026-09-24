# Catalogue trust and adoption

- **Slug:** `catalogue-trust-and-adoption` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:trustworthy-org-owned-catalogues

## Outcome

- **Steerable input:** The share of questions about a catalogue that only its maintainers can answer, and the share of contributions that only they can make.
- **Lagging outcome:** An outsider can trust, adopt and contribute to a catalogue without a maintainer in the loop. Five things make that true, and § Decomposition owns exactly one each: they can **find** what it holds; **judge** whether it is worth adopting; **confirm** that what they received is what was published; **learn** to author one; and the first-party catalogue **runs on** this rather than beside it.
- **Guardrail:** Every answer comes from a contract, a manifest, a digest, a test or a generated surface — never from prose an author remembered to update. A discovery, evaluation or publication surface never asserts more than its evidence supports.

## Opportunity

- **Functional job:** Find what a catalogue contains, judge whether it fits, confirm what arrived, and learn to author one.
- **Emotional job:** Adopt or extend a pack without first reading the maintainer's mind about what it depends on or what publishing it will do.
- **Social job:** Show a reviewer where a claim about the catalogue is enforced, rather than asserting it.
- **Struggling moment:** The catalogue's facts live in prose, in code and in the maintainer's head at once, so every question about it — and every contribution to it — routes through the people who built it.

## Boundary

This capability owns whether a catalogue can be **trusted and adopted** by
someone who did not build it. It does not own **putting a pack in**, which is
[CAP-0007 catalogue publication](CAP-0007-catalogue-publication.md), nor
**getting it onto a host**, **installing or upgrading it**, or **operating**
it. Those are its four sibling members under
[STRAT-0004](STRAT-0004-trustworthy-org-owned-catalogues.md).

**It cedes publication and keeps release integrity.** The seam is drawn by
artifact, not by subject: this capability's
`catalogue-wave5-release-integrity` owns the **release archive** — digests over
it, comparison against a prior archive, refusal of same-version mutation —
because those are what a receiver checks. CAP-0007 owns an **individual pack's
identity inside the marketplace schema**. Both are digests over different
artifacts, and claiming the territory once on each side is what the merged cut
attempted on 2026-09-24 got wrong.

The line against projection also moves work: a rule, hook or manifest that
exists to reach a host's native surface is *reaches*, however much it is
authored in the catalogue. `catalogue-rules-primitive` is the live instance —
it reads as discovery and is projection.

It does not own **reaching first value**, which
`nontechnical-pack-first-value-rollout` already owns.

Its design authority is
[RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md),
Accepted 2026-07-29.

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

Five children, one per clause of the lagging outcome.

- **find** — [Catalogue search verb](catalogue-search-verb.md) — query the neutral index for packs, profiles and their discoverable metadata.
- **judge** — [Catalogue marketing evaluator surface](catalogue-wave7-marketing-evaluator.md) — the open formats, contracts, ownership model and release evidence, stated for an evaluator.
- **confirm** — [Catalogue release integrity](catalogue-wave5-release-integrity.md) — archive digests, prior-archive comparison, same-version mutation refusal.
- **learn** — [Catalogue technical documentation architecture](catalogue-wave6-technical-docs-ia.md) — an organized Build a Catalogue path with contract references and packaging guidance.
- **run on** — [Catalogue migration and closeout](catalogue-wave9-migration-closeout.md) — the first-party migration completed against the release, evaluator and documentation outcomes.

RFC-0076 assigns no new decision to Wave 8, which converges README and
CONTRIBUTING by applying decisions D1–D4. It is therefore not a child here.

**Two intents sit inside this capability's outcome and are not yet children**,
recorded rather than absorbed because each would give a clause a second owner:

- `adopter-catalogue-test-command` serves *judge* — running the tests you
  received is how an adopter judges — and *judge* already has an owner.
- `catalogue-archive-guide-corpus` serves *learn*, which already has one, and
  part of it proves an install contract that is neither.

Either could take a clause of its own once the outcome is re-read against a
delivered child. Both stay unparented until then, which is the honest state:
unclaimed, not owned-by-implication.

**Seven candidates were read and rejected**, each recorded so the next reader
does not re-absorb them on their names:

- `plugin-publish-trust-boundary`, `claude-marketplace-pack-identity`,
  `marketplace-config-single-authority` and `marketplace-ingress-validation`
  are publication — CAP-0007.
- `catalogue-trust-store-trust-settings` is the macOS corporate **TLS
  certificate** trust store, not catalogue publication trust.
- `plugin-root-name-collision-guard` is the Claude-plugins **build** refusing a
  colliding projected root, which is projection.
- `catalogue-rules-primitive` projects a portable rule to each adapter's native
  rule surface. Also projection, and the intent the earlier backlog mining
  mis-filed under discovery.
- `claude-apps-first-value-entry` already declares
  `capability:nontechnical-pack-first-value-rollout`. Absorbing it would have
  moved an owned leaf.

## Riskiest assumption

**That the archive/pack seam with CAP-0007 holds under a change that touches
both.** This capability keeps release integrity and cedes pack identity, on the
ground that the two are digests over different artifacts. If that is wrong — if
one change has to move both — the seam is a boundary nobody can maintain, and
the two capabilities merge after all.

What would have to be true: a change to the release archive's digest scheme
leaves the marketplace pack-identity scheme untouched, and the reverse. The
evidence for it is that the two serve different consumers — an adopter
verifying what they downloaded, and a marketplace resolving an entry. The
evidence against it is that a merged cut was attempted on 2026-09-24 precisely
because the two kept reading as one territory.

Not tested, and testable cheaply: the first change to either digest scheme
settles it. Two-way door — merging costs a capability file and nine parent
edges, not a withdrawn interface.

## Assumptions

- That the five clauses survive contact with the first child to reach a spec.
  They were derived from the outcome rather than from the backlog, which is
  what makes them stable against the backlog moving, and also what leaves them
  unproven against real delivery.

## Unresolved questions

- Whether *judge* and *find* are one outcome. The search verb and the evaluator
  surface were cut as separate RFC waves, which is a delivery-sequencing
  artifact rather than an outcome boundary.
- Whether the two unparented intents in § Decomposition each need a clause of
  their own, or whether one clause may hold two children. The second reading
  has not been established against the reviewing rubric, and the first costs an
  outcome clause per intent.
