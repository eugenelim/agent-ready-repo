# Brief: intents get deterministic placement, safe admission, and a typed ordinal identity

- **Slug:** `intent-identity-and-registration`
- **Received:** 2026-09-18
- **Owner:** eugenelim, Platform Core maintainer
- **Status:** Draft
- **Readiness:** `Draft`. Was `Ready` 2026-09-19 by eugenelim, bound to revision `f2d8d76dcf75c77b`. The 2026-09-20 slice re-cut is a delivery-map change and therefore material, so `author-delivery-brief` returns the brief to `Draft` before a fresh review; the `["ini-010".brief_queue]` membership moved from `ready` to `draft` in the same change, which is what the projection requires. **No slice is dispatchable while this holds.** `Ready` returns only on a revision-bound `Clean` result plus explicit human confirmation.
- **Correction, 2026-09-20.** An earlier revision of this line claimed the projection forbade the `Ready → Draft` transition and kept the brief at `Ready` on that basis. That was wrong. The rule is keyed by queue collection — `brief_queue.ready` expects `Ready`, `brief_queue.draft` expects `Draft` (`workspace_status_engine.py:3218-3229`) — so the artifact and its membership simply have to move together. There was no rule collision to resolve.

## Outcome

A repository intent carries a typed ordinal identity, declares its own shape in its metadata, and resolves from exactly one canonical reference — with an ambiguous or invalid reference failing closed rather than guessing. The corpus stays addressable by a human reading a filename and by a machine walking the graph, and keeps being so as intents are added, renumbered and reissued.

**Placement left this brief entirely on 2026-09-20.** Where a repository intent is written is not a problem this brief has: `intake-intent`'s path is a pinned core hand-off and its vault-source admission is a designed flow, so the defect recorded under `## Current-state evidence` was a misreading, corrected there. What remains of that surface is registered rather than sliced — the pinned-handoff rule is stated for briefs but not intents, and the resolution order is an unreconciled conflict between RFC-0040's resolution tail and RFC-0096 § 4.

## Success metrics

Outcome-level observations at brief altitude. Each can fail, and each binds in both directions — an implementation that
refuses everything fails this set as surely as one that accepts everything. The falsifiable criteria that operationalise
them, including checkers, exit codes, read boundaries and fixture cohorts, are **spec-owned** and deliberately absent here.

- **A repository intent lands where the adopter configured it.** `intake-intent` resolves its destination from the configured `[product] output_dir` rather than a hardcoded path, keeps the conventional path when nothing resolves, and refuses a configured value that cannot become a safe repository-relative candidate. A placement path resolving through a symlink out of its anchoring root refuses; every other out-of-repository resolution keeps ADR-0030 D7's Ask-first deviation, disclosed by D6. **What this no longer promises:** which authority decides repository-versus-personal across packs, and whether a pack default precedes elicitation. Those are one unreconciled conflict between RFC-0040's resolution tail and RFC-0096 § 4, owned by the register entry against ADR-0030 and settled by an ADR, not by a slice of this brief.
- **An ordinal is allocated without shared mutable state, or not at all.** An admission-eligible intent whose altitude the prefix table maps gets one. An intent whose altitude it does not map keeps full `kind:slug` identity, admission and graph participation, and loses only the alias. The allocator refuses rather than guessing for input it could not fully read.
- **A renumber leaves no stale citation.** No stale path-shaped citation survives it, and canonical pointer values are unchanged. A renumber is not free — it requires lockstep edits to `workspace.toml` path entries and Markdown link targets, and the owner accepted that cost; the constraint is on completeness of the sweep, not on its price.
- **A canonical reference resolves to one artifact; an ambiguous one refuses.** These are two different things, and the brief keeps them apart. A **bare slug is a legacy fallback**: it resolves while it is unique and refuses the moment it is not. A **typed pointer is canonical storage**: the migration cohort becomes typed not because bare slugs fail today, but because a bare slug that is unique now can be made ambiguous by any later artifact, so storing one is storing a latent failure. After the sweep the derived cohort holds no untyped resolvable value, and the fallback remains for references outside it.
- **An intent's shape is declared, not inferred.** Whether it has been de-risked or reviewed is answerable from its metadata without opening the body. Both enforcement points work: the shaping review accepts a conforming shape and rejects a non-conforming one at ratification, and the corpus lint reports drift across intents already on disk. Neither passing substitutes for the other. **Required decision for the spec:** how ratification checks the shape contract without becoming an open-ended schema or quality gate. The parent records this enforcement point as untested and in tension with the shaping reviewer's bounded well-formedness role, so the spec must define that boundary and carry a validation obligation for it rather than inheriting the tension unstated.
- **Admission stays a gate.** An admission-eligible intent that conforms is admitted; one that does not is refused rather than admitted with a gap.

## Scope / Non-goals

In scope:

- **Removed 2026-09-20: placement.** The brief previously scoped a repository intent's destination as work. It is not: the path is a pinned core hand-off and vault-source admission is designed behaviour. The allocator therefore has no placement prerequisite — `max + 1` is directory-scoped and the directory is pinned.
- Safe admission of a repository intent, preserving the confinement, provenance, and terse-capture rules admission already applies. **Owner decision 2026-09-18: admission is forward-only and applies to new admissions only.** The 23 intents already on disk without a registry entry are cited as evidence that admission is uneven; closing that backlog is not this work's obligation.
- A new prefix-type-aware ordinal allocator, and the filename identity contract `<TYPE>-NNNN-<slug>.md` it serves, over the four seeded tokens `VISION` (`product-vision`), `STRAT` (`product-strategy`), `CAP` (`capability`) and `FEAT` (`feature`), with ordinals sequenced per type.
- Refusal behaviour for an altitude outside the four seeded tokens, and for an intent carrying no `Level:` at all. The table is closed: such an intent gets no ordinal, keeps its `kind:slug` identity, and is not given an inferred altitude to mint a prefix from.
- The renumber and reissue procedure, including the tombstone that keeps `max + 1` correct and keeps old citations resolving. **Required decision for the spec: how a tombstone coexists with the shape contract.** A tombstone occupies an intent-shaped path while carrying no intent content, so a corpus lint that requires metadata on every intent-shaped file will reject it. The spec must decide how a tombstone is identified, how it is excluded from intent-shape validation, whether resolution follows it to the reissued artifact, and what happens when its target is missing or when two tombstones point at each other.
- The **intent metadata shape contract**, which separates two things the corpus lint must not conflate: **which fields are required to be present**, and **which carry a closed vocabulary when present**. The parent settles that `Kind` and `Status` carry closed vocabularies rather than free text. **`Level` stays open** under ADR-0033 D2; what is closed is the **prefix table** mapping an altitude to an ordinal token, so ordinal eligibility is decided by that mapping and an unmapped `Level` is refused an ordinal without `Level` becoming enum-valued. Enforced in **two places, neither substituting for the other**: the shaping review gates it at ratification, and a corpus lint catches drift across intents already on disk, which no per-artifact gate reaches. What each `Status` value *means* and who may move between them is [FEAT-0005](../intents/FEAT-0005-lifecycle-and-closure.md)'s. **Required decisions for the spec, settled by neither this brief nor the parent:** which fields are required to be *present* as opposed to merely constrained when present, and what each closed vocabulary's member set is — including whether `Kind` is restricted to the chain rungs. The intent model makes `Kind` additive and prompt-only, so requiring its presence would contradict it.
- **Shaping-progress fields in the preamble**, so whether an intent has been de-risked and whether it has passed a shaping review are declared rather than inferred. Measured 2026-09-19 across 144 intents: none carries either field, and `Draft` is being read as "neither has happened" — an inference a body scan contradicts for 9 Draft intents, including this brief's own parent. A de-risk record in the body is not the signal; the field is.
- **Required decision for the spec: how the corpus lint treats intents predating every field the contract newly requires** — not only the shaping-progress pair. Each newly required field has the same cutover problem: requiring it fails the whole corpus on the lint's first run, and skipping absence enforces nothing. The choice per field — backfill at cutover, a dated legacy exception, or requiring it only on admission from a named point forward — is a spec decision. This brief records that it must be made for each, and that leaving it implicit produces a check that is either unusable or vacuous.
- The cross-artifact reference grammar. The canonical written pointer form is `<kind>:<slug>` — `intent:repository-work-graph`, `brief:<slug>`, `spec:<slug>`. A typed ordinal such as `CAP-0001` is a display alias and is **not** an accepted pointer value, because it does not exist for a refused altitude or for any forward-only legacy artifact. A bare untyped slug stays readable only as a fail-closed fallback that refuses on ambiguity; every resolvable pointer value in the derived migration cohort moves to the canonical form. **Required decision for the spec: which fields are in the migration population, and what each maps to.** `Brief:` and `Parent intent:` have obvious canonical targets. `Contract:` and `Discovery:` do not — both are overloaded, carrying prose such as "none new" in some artifacts and a resolvable reference in others, so a field-name count overstates the population. The migration cohort must be derived by whether a value resolves, not by which field it sits in, and the canonical target kind for each migrating field named before the sweep runs.

Non-goals:

- **Renumbering the existing corpus onto ordinals.** Adoption of the *ordinal* is forward-only, following ADR-0108 D6's precedent of not renumbering 442 spec directories: an intent carrying no ordinal at cutover keeps none. This is distinct from the pointer-value migration in scope above, which is required rather than excluded — an untyped pointer is ambiguous under a fail-closed grammar, so every untyped value must become typed for resolution to refuse correctly. **Both cohorts are derived from the authoritative corpus at migration time, not from a count fixed here.** The 95 pointer values and 135 unprefixed intents measured 2026-09-18 are current-state evidence of scale; they are not the delivery obligation, because both populations move before delivery.
- **The derived graph that reads identity.** That is `intent-graph-navigation`.
- **Relocating workspace coordination state.** That is `workspace-coordination-reorganization`, and this brief only owes it the lockstep renumber edit.
- **Any tracker identifier scheme.** That is `external-tracker-projection`.
- **Reusing `next-ordinal.py` unchanged.** The owner chose a new allocator; this brief must not fall back to the existing script.

## Current-state evidence

Measured 2026-09-18 against the working tree.

- **Placement was recorded here as a live defect; it is not one.** This bullet previously read that `frame-intent` resolves an output directory through three tiers while `intake-intent` hardcodes `docs/product/intents/{slug}.md`, so "an adopter who points `output_dir` at a personal vault therefore gets `frame-intent` writing to the vault and `intake-intent` writing to the repository", called "the deterministic-placement defect already live". **Corrected 2026-09-20.** `intake-intent` admits personal and vault sources by design — `SKILL.md:81-85` requires a human-confirmed repository-relative destination, minimized provenance and explicit authority transfer first, and its renderer carries `_TRANSFER_MODES = {"chat-only", "personal", "personal-vault", "vault"}`. Authoring in a vault and admitting into the repository are two stages of one flow. The hardcoded path is a **pinned core hand-off**, the same treatment `frame-intent`'s own layout reference already gives `decompose-intent`'s briefs output: a path that hands off to core "stays pinned (a deliberate non-goal of this layout config)". That rule is stated for briefs and not for intents, which is the only real gap, and it is registered rather than sliced.

- **Admission is uneven.** Counted in `docs/product/intents/` on 2026-09-18: 23 intents on disk have no registry presence. The load-bearing figure is the 23-file gap, derived from the directory against the registry; totals below were taken from the same directory as it grew and are not comparable to each other. The gap, not the population, is the evidence: it held at 23 both before and after this family's intents were created.
- **The existing allocator renumbers under real concurrency.** Nine ADR/RFC records were renumbered after assignment — `0112→0114`, `0109→0111`, `0108→0109`, `0047→0100`, `0074→0101`, `0055→0109`, `0106→0110`, `0101→0102`, `0098→0101` — seven of them inside three days, 2026-09-11 to 2026-09-13. The owner accepted this cost.
- **A typed prefix breaks the existing allocator silently.** `next-ordinal.py` matches `^(\d{4,})[-.]`, anchored, so on a directory of only `CAP-0001-alpha.md` and `FEAT-0007-beta.md` it returns `0001` with exit 0, and `--check` reports clean because nothing was matched. This is the single most important failure to design against.
- **A digit-prefixed intent path is valid on the two surfaces probed.** Probed by prefixing one real intent, registering it, reconciling, and reverting. This covers admission and reconciliation only, not every reference surface the outcome promises, so the compatibility assumption stays open: `_is_public_slug_segment("0001-repository-work-graph")` is `True`, the entry evaluated with no findings, and reconciliation produced zero new findings against the baseline.
- **Pointer values are untyped and resolution guesses.** `resolve_endpoint` in `lint-traceability.py` suffix-matches a bare slug against every node id and picks among multiple hits by sort order; its comment concedes a slug can match more than one. The corpus holds 6 cross-type slug collisions — 2 intent/brief, 4 intent/spec — and one fired during this brief's own shaping, taking the lint to exit 1. Counted 2026-09-18, 95 occurrences of the four pointer-bearing field names are untyped: 29 `Brief:`, 36 `Contract:`, 15 `Discovery:`, 15 `Parent intent:`. That is a field-occurrence count, not a pointer count — `Contract:` and `Discovery:` also carry prose — so it bounds the sweep's upper size rather than naming its population. Typing the resolvable ones is bounded by that population; carrying ordinals on spec directories instead would touch 4,974 `docs/specs/` path occurrences across 1,299 files, which is the comparison that selected pointer typing.
- **No unseeded altitude is in use.** Measured 2026-09-18 across 137 intents: 110 `feature`, 14 `capability`, 2 `product-strategy`, 0 `product-vision`, and 11 carrying no `Level:` at all. Nothing uses an altitude outside the seeded four, so refusing to derive a prefix has no blast radius today, and the live case is the 11 unclassified intents rather than a hypothetical `epic`.
- **A renumber touches path-shaped citations only.** 161 files cite an intent path, of which `workspace.toml` holds the registry `path` entries; a stale `path` raises `missing_artifact`, which `tests/roster/test_workspace_status_projection.py` treats as fail-closed. Pointer *values* are unaffected, because identity binds to each artifact's `Slug:` field rather than its filename — demonstrated by this tree's own renumber, where the bare `Parent intent:` value stayed correct while only its link target moved.
## Constraints / Appetite

- **Non-waivable, symlink arm only:** a placement path whose resolution passes through a symlink out of its anchoring root refuses, per `security-checklists/references/path-and-file.md:30-32`. **Corrected 2026-09-20:** this brief previously asserted refusal for *every* out-of-repository resolution. That claim traced to no source and contradicted ADR-0030 D7, which decides the non-symlink case as an untrusted-origin, Ask-first deviation with D6's path disclosure as its control. The narrower rule is the one that holds.
- **No longer required of a spec here:** anything about where an intent is written. Resolution order, repository-versus-personal authority and persistence belong to the RFC-0040 / RFC-0096 reconciliation, registered against ADR-0030.
- **Reuse the ADR/RFC approach, not its script.** `max + 1` over the directory unioned with `origin`, forward-only, renumbered at admission — implemented fresh so it can key on the type prefix.
- **The allocator refuses rather than guesses.** It must not return an ordinal, or report a clean duplicate check, for a corpus it could not fully parse. The shipped script already states this discipline for itself and the replacement must inherit it.
- **No shared mutable allocation state.** ADR-0108's ground is that a repository-global identifier counter is a shared mutable resource this repository has twice failed to coordinate. That rules out a counter file and a repository-global retired list alike.
- **Renumbering is accepted; stale citations are not.** The owner accepted the renumber cost, so the constraint is on completeness of the sweep, not on frequency.
- **The prefix table is closed; `Level` stays open.** ADR-0033 D2 owns the open-`Level` rule and the parent intent owns the four-token mapping; neither is restated here. The delivery consequence is that the allocator refuses an altitude it does not have a token for rather than deriving one. A naive derivation is measurably hazardous — uppercase-and-truncate yields `INIT` for `initiative`, one character from `INI-` and its 395 uses — and a derived namespace cannot be enumerated to prove a duplicate check complete.
- **ADR-0108 D3 holds**, and owns the non-reuse rule. The delivery consequence here is that a retirement leaves a tombstone the allocator counts.

## Assumptions / Risks

- **[Decided]** Prefixes are `VISION`, `STRAT`, `CAP`, `FEAT`, all verified unused at repository scope; `VISION` over `VIS` to clear the one-character gap to `VI-`, which has 70 uses.
- **[Decided]** A post-admission altitude change reissues at the new prefix and leaves a tombstone naming the new identity.
- **[Decided]** An altitude outside the four seeded tokens, or an intent with no `Level:`, is refused an ordinal and keeps `kind:slug` identity. `kind:slug` is canonical and the ordinal is an alias, bound to each artifact's `Slug:` field so a renumber changes no reference.
- **[Decided]** Placement is in scope and sequenced before the allocator. The evidence is the `frame-intent` / `intake-intent` disagreement above. **What is settled is file precedence only** — a repository `agentbundle-layout.toml` wins over the user-scope file, and `intake-intent` adopts that precedence instead of hardcoding a path. **Still open, for the placement spec:** which authority decides whether a given intent is repository or personal work in the first place, and what happens when that configuration is missing or ambiguous. Precedence between two config files does not answer either.
- **[Inferred]** The existing slug/path identity can keep resolving while the filename gains a prefix. Untested.
- **Risk:** the allocator is silently wrong when it is wrong. Both measured failure modes return a plausible ordinal with exit 0, so a construction test that feeds it unparseable and typed-but-unseen input is load-bearing, not optional.
- **Risk:** the renumber procedure couples this work to `workspace.toml`, whose contention `workspace-coordination-reorganization` exists to remove. The two must be sequenced with the tension named rather than discovered.
- **Risk:** refusal for an unseen altitude is the case an adopter hits first and this repository hits last — measured, zero unseeded altitudes in use here — so the refusal path will be under-exercised by self-hosting and needs a construction test rather than reliance on the corpus.

## Post-Ready decisions

Recorded so they are not mistaken for omissions. `author-delivery-brief` §4 places slice derivation after a durable Ready, behind a second distinct confirmation, and a Ready brief with zero specs is valid.

- ~~The slice cut itself~~ — settled 2026-09-20; the Spec map below is its record. Whether the derived pointer-migration cohort lands as one sweep or per artifact type is still open.
- Sequencing against `workspace-coordination-reorganization`, which decides whether the renumber path sweep is built once or twice.

## Source

- **Mode:** repo-origin
- **Locator:** [`docs/product/intents/FEAT-0001-intent-identity-and-registration.md`](../intents/FEAT-0001-intent-identity-and-registration.md)
- Projected from that feature intent by `decompose-intent` on 2026-09-18. The intent is `Accepted` and owns the de-risk record this brief delivers against.
- No `Parent intent:` preamble pointer is carried. ADR-0019 D9 makes that back-pointer an optional addition **at business-unit scale**, and this intent is `Scale: app`. Because the brief and the intent share a slug, writing one also makes the traceability lint resolve the brief's up-edge to the brief itself — a self-referential cycle that exits non-zero. The linkage lives in the locator above and in this brief's `source.ref` registry entry instead.

## Governance references

These constrain or explain delivery. They do not affect coverage or closure rollups.

- [ADR-0108](../../adr/0108-opaque-append-only-loop-contract-identifiers.md) — D2 and D3 on renumbering and reuse; its Context is the ground that a repository-global counter is uncoordinatable here, and D6 is the forward-only precedent.
- [ADR-0033](../../adr/0033-intent-level-open-recognized-set-decoupled-from-scale.md) — D2 keeps `Level` an open set, which is why the prefix table is closed by decision rather than derived: an open namespace cannot be enumerated to prove a duplicate check complete.
- [ADR-0112](../../adr/0112-index-tables-are-generated-or-absent.md) — an index over a corpus is generated or absent, so the ADR/RFC renumber trap of a hand-edited display column does not carry over.
- [ADR-0077](../../adr/0077-feature-projection-and-tracker-authority.md) — D1's shippability-and-coordination test, which selected a brief over a single delivery contract here.

## Spec map

Five slices. Confirmed 2026-09-19, re-cut on 2026-09-20, and one of the re-cut pair retired the same day. The Status column is auto-derived from each spec; it is not hand-edited.

**Sequencing, as planning guidance rather than blocking edges.** `typed-intent-ordinal-allocator` goes first, and
`intent-renumber-and-reissue` follows it. The placement slice that used to precede them is gone, so nothing now
gates the allocator on a resolved folder: `intake-intent`'s intents path is pinned, which is the resolved folder.
`frame-intent-symlink-escape-refusal`, `intent-metadata-shape-contract` and `intent-reference-grammar-migration` are enterable
at any point; none depends on an ordinal existing.

| Spec | Status |
| --- | --- |
| `frame-intent-symlink-escape-refusal` | <auto> |
| `intent-metadata-shape-contract` | <auto> |
| `typed-intent-ordinal-allocator` | <auto> |
| `intent-reference-grammar-migration` | <auto> |
| `intent-renumber-and-reissue` | <auto> |

### Post-Ready amendment — 2026-09-20, the placement slice re-cut

`intent-placement-and-admission` is replaced by two smaller slices. `author-delivery-brief` §4 places the slice cut
after a durable Ready and this brief's `## Post-Ready decisions` reserves it, so this is the anticipated route rather
than a contract change. **The Ready binding to revision `f2d8d76dcf75c77b` no longer covers this spec map and needs
re-confirmation.**

Why it was re-cut: the single slice had taken on a cross-pack execution channel this brief's outcome never required. The
record of what was removed and why is in
[`docs/specs/intake-intent-configured-destination/notes/verification-ledger.md`](../../specs/intake-intent-configured-destination/notes/verification-ledger.md) § *The re-cut*, which owns it rather than this brief.

- **`intake-intent-configured-destination`** — **retired the same day.** Its founding defect was a misreading of the
  two-stage author-then-admit flow, so there was nothing to build. Correction recorded under
  `## Current-state evidence`; residue registered.
- **`frame-intent-symlink-escape-refusal`** — a placement path whose resolution passes through a symlink out of its
  anchoring root refuses. Every other out-of-repository resolution keeps ADR-0030 D7's Ask-first deviation with D6's
  path disclosure, so this supersedes no decision. Isolated because its evidence is prose rather than code.

**What left this brief's family.** Placement resolution order, repository-versus-personal authority, and whether an
elicited answer is persisted. Two accepted records disagree about them, so no slice here can settle them. Owner:
eugenelim, via `workspace.toml` `[backlog].open` at
`path = "docs/adr/0030-consolidated-pack-output-layout-contract.md"`, which carries the evidence.

**The open question that slice owed is moot.** Which layout section `intake-intent` reads: none. It reads no
configuration for this path, because the path is pinned.
