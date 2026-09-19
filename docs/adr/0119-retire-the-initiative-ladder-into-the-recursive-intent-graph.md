# ADR-0119: Retire the Initiative ladder into the recursive intent graph

- **Status:** Accepted
- **Date:** 2026-09-18
- **Areas:** shaping, workspace
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0019 (the recursive intent ontology this restores as sole canon); ADR-0033 (`Level` as an open recognized set); ADR-0051 (the `workspace.toml` format whose per-initiative sections this reframes); ADR-0112 (an index over a corpus is generated or absent); RFC-0064 (the record that introduced the second hierarchy)

## Context

Two ladders describe the same repository work.

ADR-0019 models product shaping as one recursive, level-tagged `intent` whose leaf is a shippable spec, and explicitly rejects separate work-item types. ADR-0033 refines it: `Level` is an open field carrying the recognized set `product-vision › product-strategy › capability › feature`.

RFC-0064 later introduced a second hierarchy — Company → Initiative → Project — to give `workspace.toml` a coordination vocabulary. That hierarchy has since partly collapsed on its own. The standalone Project artifact was removed. The Initiative artifact remains, and its template directs the reader to `docs/CONVENTIONS.md §5b` for the altitude hierarchy that defines what an "altitude-1" initiative is — a file retired by a Shipped spec, so that definition has no surviving home.

What remains is not one ontology. `INI-001` is a product vision and lives under `docs/product/shaping/`. `ini-002-initiative-brief.md` is a `Level: product-strategy` intent and lives under `docs/product/intents/`. `INI-009` is an Initiative document with no intent level. `INI-003` names two different concepts in two namespaces. Four `ini-*` operational sections exist in `workspace.toml`; one non-template initiative document exists on disk.

The ambiguity is no longer only conceptual. Because `brief_queue` is a per-initiative structure and `backlog.open` — the only initiative-free collection — admits a non-defect entry at `Status: Draft` only, an artifact that reaches Ready or Accepted has no initiative-free home. Work with no truthful initiative must therefore either assert a false one or go unregistered. That is a coordination mechanism refusing work on ontological grounds, and it is what forced this decision.

`Initiative` has meanwhile been used for at least three different things: a product existence bet, a strategic path across capabilities, and an operational delivery bucket. A term carrying three meanings cannot be an altitude.

## Decision

**We retire `Initiative` as a canonical repository artifact and as a workspace ownership boundary, and we make the recursive intent graph the single canonical ladder.**

- **D1:** The recursive, level-tagged `intent` of ADR-0019 and ADR-0033 is the sole canonical hierarchy for product shaping in this repository. There is one vocabulary.
- **D2:** `Initiative` is not an altitude and is not a canonical artifact. It survives only as a generated portfolio or delivery view, as an external tracker projection, and as a legacy alias during migration.
- **D3:** Existing initiative content is reclassified by meaning, not by container: a product existence or ecosystem bet becomes a `product-vision` intent; a strategic path across several capabilities becomes a `product-strategy` intent; one capability bet becomes a `capability` intent; time-bounded delivery across several specs becomes a delivery brief or a generated view; and an operational queue bucket becomes a workspace projection rather than a product artifact.
- **D4:** An intent registers in `workspace.toml` directly. Its product parent comes from `Parent intent:`; its lifecycle state comes from the workspace record. Registration does not require membership of an operational initiative bucket.
- **D5:** A capability does not require a strategy parent. An explicit `Parent intent: none` means the altitude was deliberately entered; an **absent** `Parent intent:` field means legacy or unclassified. The two are distinct and must not be conflated.
- **D6:** A tracker's containers are a classification hint, never the local ontology. The canonical levels are the repository's own, and outbound projection maps them per tracker.
- **D7:** Adoption is forward-only in the same sense ADR-0108 D6 uses. Existing artifacts are reclassified as they are touched or by the migration feature that owns the sweep; no bulk rewrite of the corpus is required by this record.

D4 is the operative half. D1 through D3 restate and consolidate an ontology the repository had already accepted; D4 removes the ownership boundary that was blocking registration, and is the reason this is recorded as a decision rather than as documentation.

## Consequences

**What becomes possible.** Work registers at its true altitude without a false initiative. The graph gains the two rungs above `capability` that the initiative ladder had been standing in for, so a strategy has somewhere to live and a vision has somewhere to be argued. Downstream, architecture, specs and implementations can become aware of accepted decisions and apply them as policy, because there is one graph to traverse rather than two vocabularies to reconcile.

**What it costs.** `docs/product/initiatives/` and `docs/product/shaping/` must be emptied into intents and retired, including a template that cites a retired file. The `ini-*` sections lose their ownership meaning and keep only a projection meaning, which requires the workspace side to offer an initiative-free home for a non-Draft artifact — it does not today. Until that lands, a Ready or Accepted artifact with no truthful initiative stays unregistered, which is a real gap and not a workaround.

**What is deliberately not decided here.** Where operational coordination state lives after the buckets stop being an ownership boundary; whether `initiative` is ever re-admitted as an adopter-named intervening `Level`, which ADR-0033 D2 already permits and this record does not forbid; and the projection profile for each tracker.

**Revisit if:** work routinely cannot be classified into the four recognized altitudes without inventing a rung; or an initiative-free registration home proves unachievable without breaking dispatch, provenance, lifecycle or dependency safety; or an adopter's tracker cannot receive a faithful projection of the canonical levels.

## Confirmation

- **Mode:** structural review of the repository's own corpus.
- **Signal:** every intent resolves to one of the recognized altitudes with an explicit or deliberately-absent parent; no artifact refers to `Initiative` as a canonical level or altitude; and an intent at any status registers without an initiative bucket.
- **Owner:** eugenelim.

## Alternatives considered

- **Keep both ladders and document the mapping.** Rejected: the mapping is what has failed. Three meanings of `Initiative` cannot be mapped to one altitude, and the definition the template points at no longer exists.
- **Promote `Initiative` to a recognized intent `Level`.** Rejected: ADR-0033 D2 permits an adopter to name an intervening altitude, but doing so here would bless the ambiguity rather than resolve it, and the operational bucket meaning is not an altitude at all.
- **Retire the intent ladder and keep Initiative.** Rejected: it reverses ADR-0019 and ADR-0033, discards the recursion and the per-level de-risk that the shaping skills are built on, and adopts a tracker-shaped container as local ontology, which D6 forbids.
- **Leave registration as-is and accept unregistered artifacts.** Rejected: registration is the coordination evidence other tooling reads, so silent absence is worse than a false entry, and both are worse than removing the boundary.
