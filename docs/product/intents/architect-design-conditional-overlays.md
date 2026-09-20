# Route the lenses a design's shape and workload require

- **Status:** Accepted
- **Level:** feature

## Outcome

`architect-design` loads the system-shape and workload-class concepts a design actually turns on, and a layered or modular subsystem design shows its internal boundaries when a boundary is the decision being made.

## Boundary

- Admits: a system-shape axis in the design router, selecting from the six shapes the corpus already ships.
- Admits: extending the workload axis beyond GenAI/agentic to the remaining workload families the corpus ships.
- Admits: a conditional internal-boundaries view in the subsystem template, activated by a named trigger.
- Admits: naming the limit of dependency-direction evidence. Comparison against manifests, imports, and tests is within the skill's read authority; exhaustive proof of dynamic resolution is not, and that gap is stated rather than implied covered.
- Excludes: making ports-and-adapters the default structural spine. Its corpus entry presents it as one mechanism among layering, modules, dependency injection, transaction boundaries, and import rules.
- Excludes: importing `architect-assess/references/concept-routing.md` as the design router. It routes by observed match and assessment intent, not by proposed design.
- Excludes: any new OKF concept or category. Scope and shape selection are skill-level routing, and the corpus ontology is pinned by exact equality.
- Excludes: changing the three scope templates' section structure or the `D1`-`D6` decomposition criteria. Both shipped, and this intent builds on them.

## Owner

- architect pack maintainer.

## Unresolved questions

- Which named trigger activates the internal-boundaries view, and whether it fires on the system shape alone or on the boundary being the decision.
- Whether the workload axis extends to every remaining family at once, or only to those whose shipped lens carries a tier the proposed design exercises.

## Projection

- ADR-0118 tracks this as slice 3 of four. One spec under `docs/specs/` is the expected delivery artifact, following `architect-design-scope-templates` and `architect-design-document-gates`.

## Opportunity

The corpus ships six system shapes and several workload families that the design router never selects. A design is shaped against provider, quality, and GenAI/agentic concerns only, so a shape-specific concern — an event schema, a delivery guarantee, a transaction boundary — reaches a document only if the author happens to raise it.

## Assumptions

- The three scope templates and the `D1`-`D6` decomposition rubric are shipped and stable, so this intent extends them rather than revising them.


## De-risk

- **Door:** two-way. The change is skill prose plus one conditional template section in a versioned pack, so reversal is a patch release. Being wrong is cheap to undo but reaches installed adopters first.
- **Prototype-approach:** `prototype-led`. Building one shape axis is cheaper than designing an experiment about it, so the build is the test.

**Riskiest assumption:** routing more lenses into the author's context produces a *better* design rather than a *longer* one.

**What would have to be true:** a shape-specific or workload-specific concern the author would otherwise have missed reaches the document; the overlay adds material a reader judges load-bearing; and the added material does not push documents back toward the accumulation failure the three templates and the `D1`-`D6` rubric were built to stop.

**Kill condition (predeclared 2026-09-19):** author one subsystem design twice against the same source problem — once with the event-driven shape overlay active, once without. Kill the overlay if a reviewer who did not write it judges that the overlay's added content is not load-bearing, or if the routed document grows without a named concern that the unrouted one missed. Growth alone is not a pass, and a concern the author would have raised anyway is not a find.

```
validation_hook:
  assumption: Routing shape and workload lenses adds concerns an author would otherwise miss, rather than adding bulk.
  kill_condition: A reviewer who did not write the overlay judges its added content not load-bearing, or the routed document grows with no named concern the unrouted one missed.
  activity: Author the same subsystem design with and without the event-driven shape overlay, then have an independent reviewer mark each added passage load-bearing or not.
  status: to-validate
```

**Verdict:** pending — the probe has not run. The predeclared line above is fixed and is not to be edited to fit whatever the probe returns.

**Measurement dependency, recorded rather than resolved.** The obvious instrument for this kill condition is `DA10`, which slice 2 shipped. It is not used here, because `architect-design-gate-calibration` exists precisely to establish whether `DA10`'s bound is sound. Measuring this bet with an uncalibrated instrument would produce a verdict that reads clean whichever way the bound is wrong. The two intents are independent to build: nothing in this one waits on calibrated gates to ship. The dependency is on *verification*, so it is recorded as a `needs` edge on this intent in `workspace.toml` — calibrate the instrument, then trust a mechanical verdict from it. Until that edge is discharged, this bet's verdict rests on the reviewer judgment named in the kill condition above, not on a `DA10` result.

## Decomposition

Cut by shippability, into three slices. Each ships, tests, and delivers on its own; none is a component or layer cut.

```
architect-design-conditional-overlays (feature)
├─ S1  system-shape axis + the overlay probe          [CONTRACTED — carries the kill condition]
├─ S2  workload axis beyond GenAI/agentic             [conditional on S1's verdict]
└─ S3  conditional internal-boundaries view           [conditional on S1's verdict; needs S1's shape axis]
```

**Why only S1 is contracted.** The bet — that routing more lenses adds concerns rather than bulk — is un-resolved, and `S2` and `S3` inherit it whole. Contracting all three now would fan specs out of a bet no probe has tested. Because the approach is `prototype-led`, `S1` *is* the probe: building the shape axis and authoring the paired designs resolves the kill condition. `S2` and `S3` are named here so they are not re-derived, and are contracted only once `S1` returns a surviving verdict.

**Why `S3` is not folded into `S1`.** Its trigger reads the system shape, so it cannot precede the shape axis. Folding it in would put two decisions behind one verdict and make a kill unattributable.

**Branch considered and dropped.** A cut along the three excluded items — ports-and-adapters, the router import, the OKF ontology — was rejected: those are exclusions, not slices, and none of them ships anything.

## Delivery contract — S1

For the `new-spec` gate. Attributed context, not an approved spec.

- **Outcome:** the design router selects a system-shape concept, and one subsystem design authored with the event-driven overlay is set against the same design authored without it.
- **Boundaries:** `packs/architect/.apm/skills/architect-design/` — its routing and its subsystem template asset. Nothing outside the skill (ADR-0118's own scope line).
- **Non-goals:** the workload axis (`S2`); the internal-boundaries view (`S3`); ports-and-adapters as a default spine; importing `architect-assess/references/concept-routing.md`; any new OKF concept or category; any change to the three templates' section structure or the `D1`-`D6` criteria.
- **Dependencies:** none to build. `needs` carries a verification-only edge to `architect-design-gate-calibration`; `S1`'s verdict rests on reviewer judgment, not on a `DA10` result, precisely so this edge does not block it.
- **Design context:** six system-shape concepts ship under `packs/architect/okf/architecture-lenses/concepts/system-shapes/`. `SKILL.md` step 3 routes on quality, provider, local-first, novelty, and GenAI/agentic — there is no shape axis. The corpus ontology is pinned by exact equality in `packs/architect/tests/pack/test_architecture_lenses_corpus.py`, so the axis is skill routing and adds no concept file.
- **Delivery questions, for the spec author:** which named trigger selects a shape when a design exhibits more than one; whether a shape-routed concept loads at a tier or whole; and what the spec records when the probe's paired designs disagree with the reviewer's load-bearing judgment.
- **Verification the contract carries:** the predeclared kill condition above is the acceptance bar for the probe, and it is not to be restated as a softer criterion in the spec.
- **Source provenance:** ADR-0118 (Accepted) at `c4b2f5912bad080f095ffb32d354b54c31d6c54f`; this intent's own de-risk block.

## Source

- Mode: repo-origin
- Locator: docs/adr/0118-architect-design-scope-routed-model-first-templates.md
- Revision: c4b2f5912bad080f095ffb32d354b54c31d6c54f
- Authority: repo-origin
