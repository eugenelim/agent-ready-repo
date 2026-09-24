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
- **Lagging outcome:** An outsider can trust, adopt and contribute to a catalogue without a maintainer in the loop. Seven things make that true, and § Decomposition owns exactly one each: they can **find** what it holds; **judge** whether it is worth adopting; **confirm** that what they received is what was published; **publish** into it safely; **learn** to author one; **start** and reach first value; and the first-party catalogue **runs on** this rather than beside it.
- **Guardrail:** Every answer comes from a contract, a manifest, a digest, a test or a generated surface — never from prose an author remembered to update. A discovery, evaluation or publication surface never asserts more than its evidence supports.

## Opportunity

- **Functional job:** Find what a catalogue contains, judge whether it fits, confirm what arrived, publish into it, learn to author one, and get to first value.
- **Emotional job:** Adopt or extend a pack without first reading the maintainer's mind about what it depends on or what publishing it will do.
- **Social job:** Show a reviewer where a claim about the catalogue is enforced, rather than asserting it.
- **Struggling moment:** The catalogue's facts live in prose, in code and in the maintainer's head at once, so every question about it — and every contribution to it — routes through the people who built it.

## Boundary

This capability owns whether a catalogue can be **trusted, adopted and
contributed to**. It does not own **getting it onto a host** (projection and
the route set), **installing or upgrading it** (the install lifecycle), or
**operating it** day to day. It also does not own **reaching first value**, which
`nontechnical-pack-first-value-rollout` already owns. Those are its four
sibling members under
[STRAT-0004](STRAT-0004-trustworthy-org-owned-catalogues.md).

The line against projection is the one that moves work: a rule, hook or
manifest that exists to reach a host's native surface is *reaches*, however
much it is authored in the catalogue. `catalogue-rules-primitive` is the live
instance — it reads as discovery and is projection.

Its design authority for the contracts half is
[RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md),
Accepted 2026-07-29. The publication and adoption halves have no single RFC:
they accumulated across follow-up sessions, which is why an RFC-shaped cut
missed them.

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

Eleven children across six clauses of the lagging outcome. Each child serves
exactly one clause and each clause has at least one child.

**find** — an outsider finds what the catalogue holds without knowing a name.

- [Catalogue search verb](catalogue-search-verb.md) — query the neutral index for packs, profiles and their discoverable metadata.

**judge** — an outsider decides whether adopting is worth it.

- [Catalogue marketing evaluator surface](catalogue-wave7-marketing-evaluator.md) — the open formats, contracts, ownership model and release evidence, stated for an evaluator.
- [Adopter catalogue test command](adopter-catalogue-test-command.md) — one canonical command for the tests an adopter receives, so the judgement rests on a run rather than a claim.

**confirm** — what arrived is what was published.

- [Claude marketplace pack identity](claude-marketplace-pack-identity.md) — an independently recoverable content digest per pack, which is what a receiver checks.

**publish** — an organisation puts its own packs in safely, including ones it never releases.

- [Catalogue release integrity](catalogue-wave5-release-integrity.md) — digests, prior-archive comparison, and same-version mutation refusal. Under *publish* rather than *confirm* because its actor is the publisher: it is the act that makes confirmation possible.
- [Plugin publish trust boundary](plugin-publish-trust-boundary.md) — a reviewable actor boundary and approver preview for marketplace publication.
- [Marketplace config single authority](marketplace-config-single-authority.md) — branch and description set once in `catalogue.toml`.
- [Marketplace ingress validation](marketplace-ingress-validation.md) — invalid Git references and empty branches rejected at ingress.

**learn** — someone can author a catalogue of their own.

- [Catalogue technical documentation architecture](catalogue-wave6-technical-docs-ia.md) — an organized Build a Catalogue path with contract references and packaging guidance.
- [Catalogue archive guide corpus](catalogue-archive-guide-corpus.md) — the adopter guide corpus inside the archive, with its package and install contract proved.

**run on** — the first-party catalogue runs on this capability rather than beside it.

- [Catalogue migration and closeout](catalogue-wave9-migration-closeout.md)

RFC-0076 assigns no new decision to Wave 8, which converges README and
CONTRIBUTING by applying decisions D1–D4. It is therefore not a child here.

**Four candidates were read and rejected**, recorded because each was nearly
absorbed on its name rather than its outcome:

- `catalogue-trust-store-trust-settings` — the macOS corporate **TLS
  certificate** trust store, not catalogue publication trust. Same word,
  different boundary.
- `plugin-root-name-collision-guard` — the Claude-plugins **build** refusing a
  colliding projected root. That is projection, so it is *reaches*.
- `catalogue-rules-primitive` — projecting a portable rule to each adapter's
  native rule surface. Also *reaches*, and the intent the earlier backlog
  mining mis-filed under discovery.
- `claude-apps-first-value-entry` — already declares
  `capability:nontechnical-pack-first-value-rollout`. Absorbing it would have
  moved an owned leaf, so the first-value clause was dropped from this
  capability's outcome rather than staffed by taking someone else's child.

**Why eleven and not five.** The first cut took RFC-0076's four headings. Three
duplicate-scope seams then showed up against the strategy's backlog: release
integrity claimed here and by the publication cluster, evaluation claimed here
and by adoption surfaces, and discovery holding an intent that was projection.
All three are one error — cutting on an RFC while the backlog accumulated
across follow-up sessions the RFC never saw.

## Riskiest assumption

**That trusting a catalogue and publishing into it are one outcome, not two.**
The whole re-cut rests on it. If it is wrong, this capability splits along the
*publish* clause and its five publication children leave for a capability of
their own — which is what the strategy's earlier mining proposed before the
seams were found.

What would have to be true: the same contract, digest or manifest that lets a
receiver confirm what arrived is the one a publisher produces, so a change to
either reaches both. The evidence for it is
`catalogue-wave5-release-integrity`, whose digests serve the publisher who
writes them and the adopter who checks them, and
`claude-marketplace-pack-identity`, which is the same digest read from the
receiving end. The evidence against it is that publication has actors and
approvals — `plugin-publish-trust-boundary` — that confirmation has no
counterpart for.

Not tested. It is a two-way door: re-splitting costs a capability file and
eleven parent edges, not a withdrawn interface, so it is cheaper to learn from
the first publication child reaching spec than to test now.

## Assumptions

- That the six clauses survive contact with the first child to reach a spec.
  They were derived from the outcome rather than from the backlog, which is
  what makes them stable against the backlog moving, and also what leaves them
  unproven against real delivery.

## Unresolved questions

- Whether *judge* and *find* are one outcome. The search verb and the evaluator
  surface were cut as separate RFC waves, which is a delivery-sequencing
  artifact rather than an outcome boundary.
- Where `adopter-catalogue-test-command` belongs. It is under *judge* because
  running the tests you received is how an adopter judges, but its outcome is
  as much about test-command shape as about judgement.
- Whether `catalogue-archive-guide-corpus` is *learn* or *confirm*. It carries
  the guide corpus, which is *learn*, and proves the package and install
  contract, which is neither.
