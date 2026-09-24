# Catalogue publication

- **Slug:** `catalogue-publication` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:trustworthy-org-owned-catalogues

## Outcome

- **Steerable input:** The number of people who have to be trusted, rather than checked, for a pack to reach a marketplace.
- **Lagging outcome:** An organisation publishes into its own catalogue safely. Four things make that true, and § Decomposition owns exactly one each: who may publish is a reviewable **boundary** rather than an assumption; each published pack carries an **identity** a consumer can recover independently; the marketplace's own settings have one **configuration** authority; and bad input is rejected at **ingress** before it can resolve an install route.
- **Guardrail:** Publication is gated by evidence a reviewer can inspect, never by who holds the credential. A rejected input fails before it reaches an install route, not after.

## Opportunity

- **Functional job:** Get an organisation's own pack into its catalogue without hand-checking every step.
- **Emotional job:** Publish without wondering who else could have, or what a malformed entry will do downstream.
- **Social job:** Answer "who approved this, and against what" with a record rather than a name.
- **Struggling moment:** Publication runs on implicit trust in whoever holds access, and a malformed entry is discovered by the adopter who installs it rather than at the gate.

## Boundary

This capability owns **putting a pack in**. It does not own whether a catalogue
can be trusted and adopted, which is
[CAP-0006](CAP-0006-catalogue-trust-and-adoption.md).

**The seam with CAP-0006 is release integrity, and it is drawn by artifact.**
CAP-0006's `catalogue-wave5-release-integrity` owns the **release archive** —
digests over the archive, comparison against a prior one, and refusal of
same-version mutation. This capability's `claude-marketplace-pack-identity`
owns an **individual pack's identity inside the marketplace schema**. Both are
digests, which is why the earlier cut claimed the territory twice; they are
digests over different artifacts, and a change to one does not reach the other.

It does not own projection to a host's native surface, the install and upgrade
lifecycle, or day-to-day operation. Those are sibling members under
[STRAT-0004](STRAT-0004-trustworthy-org-owned-catalogues.md).

## Decomposition

Four children, one per clause of the lagging outcome.

- **boundary** — [Plugin publish trust boundary](plugin-publish-trust-boundary.md) — an independently reviewable actor boundary, an approver preview, and current live-control evidence.
- **identity** — [Claude marketplace pack identity](claude-marketplace-pack-identity.md) — an independently identifiable and recoverable content digest per pack, compatible with the upstream marketplace schema.
- **configuration** — [Marketplace config single authority](marketplace-config-single-authority.md) — branch and description set once in `catalogue.toml`, used by every public render path.
- **ingress** — [Marketplace ingress validation](marketplace-ingress-validation.md) — invalid Git references and empty configured branches rejected before a fork can resolve an install route to upstream.

**Two neighbours were read and rejected**, both previously mis-filed here on
their names:

- `catalogue-trust-store-trust-settings` is the macOS corporate **TLS
  certificate** trust store. The word is the only thing it shares with
  publication trust.
- `plugin-root-name-collision-guard` is the Claude-plugins **build** refusing a
  colliding projected root. That is projection, so it belongs to the *reaches*
  member.

## Riskiest assumption

**That a reviewable actor boundary is what makes publication safe, rather than
the content check that follows it.** If it is wrong, *boundary* and *ingress*
collapse into one clause and this capability is three children, not four.

What would have to be true: the harms publication can do are dominated by *who
acted*, not by *what they published*. The evidence for it is that
`plugin-publish-trust-boundary` exists because live controls were found
unreviewable, which is an actor problem. The evidence against it is
`marketplace-ingress-validation`, whose failures are malformed content reaching
an install route regardless of who submitted it.

Not tested. Two-way door: merging two clauses costs an edit, not a withdrawn
interface.

## Assumptions

- That publication is one capability rather than a facet of each route. It is
  cut as one because the four children share a gate; if routes diverge enough
  that each needs its own publication rules, this splits along the route set.

## Unresolved questions

- Whether *identity* belongs here or in CAP-0006. The § Boundary seam draws it
  by artifact — pack entry versus release archive — and that line has not yet
  been tested by a change that touches both.
- Whether an organisation publishing only privately needs *ingress* at all, or
  whether it is a public-marketplace concern.
