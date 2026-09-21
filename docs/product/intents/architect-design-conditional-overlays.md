# Route the lenses a design's shape and workload require

- **Slug:** `architect-design-conditional-overlays`
- **Status:** Accepted
- **Level:** feature
- **Owner:** eugenelim

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

- ADR-0118 tracks this as slice 3 of four, following `architect-design-scope-templates` and `architect-design-document-gates`. Amended 2026-09-20: the expected artifacts are `docs/specs/architect-design-shape-overlay/` for `S1`, a spike for the probe, conditionally one spec each for `S2` and `S3`, and a revert spec on a killed verdict.

## Opportunity

The corpus ships six system shapes and several workload families that the design router never selects. A design is shaped against provider, quality, and GenAI/agentic concerns only, so a shape-specific concern — an event schema, a delivery guarantee, a transaction boundary — reaches a document only if the author happens to raise it.

## Assumptions

- The three scope templates and the `D1`-`D6` decomposition rubric are shipped and stable, so this intent extends them rather than revising them.


## De-risk

- **Door:** two-way. The change is skill prose plus one conditional template section in a versioned pack, so reversal is a patch release. Being wrong is cheap to undo but reaches installed adopters first.
- **Prototype-approach:** `prototype-led`. Building one shape axis is cheaper than designing an experiment about it. Amended 2026-09-20: the probe needs the axis to exist before it can run, so the build precedes the test rather than being it.

**Riskiest assumption:** routing more lenses into the author's context produces a *better* design rather than a *longer* one.

**What would have to be true:** a shape-specific or workload-specific concern the author would otherwise have missed reaches the document; the overlay adds material a reader judges load-bearing; and the added material does not push documents back toward the accumulation failure the three templates and the `D1`-`D6` rubric were built to stop.

**Kill condition (predeclared 2026-09-19):** author one subsystem design twice against the same source problem — once with the event-driven shape overlay active, once without. Kill the overlay if a reviewer who did not write it judges that the overlay's added content is not load-bearing, or if the routed document grows without a named concern that the unrouted one missed. Growth alone is not a pass, and a concern the author would have raised anyway is not a find.

```
validation_hook:
  assumption: Routing shape and workload lenses adds concerns an author would otherwise miss, rather than adding bulk.
  kill_condition: A reviewer who did not write the overlay judges its added content not load-bearing, or the routed document grows with no named concern the unrouted one missed.
  activity: Author the same subsystem design with and without the event-driven shape overlay, then have an independent reviewer mark each added passage load-bearing or not.
  status: to-validate — ran 2026-09-20 and could not decide. The paired comparison cannot separate the overlay from author run-to-run variance at n=1: a same-condition control diverged more than the treatment. Settling it needs several pairs per condition with one judge and one brief, reporting whether routed-vs-unrouted divergence exceeds unrouted-vs-unrouted divergence.
```

```
validation_hook:
  assumption: The unrouted arm of the paired comparison is producible after S1 ships the axis.
  kill_condition: No mechanism produces a design from this router with the shape axis inactive, so the predeclared comparison cannot be run as written.
  activity: Name the baseline mechanism — a pinned pre-S1 skill revision, a marker-region removal in a scratch copy, or an equivalent — and record it with the spike's method before either arm is authored.
  status: to-validate — still open, and the 2026-09-20 run did not test it. The baselines that ran used a pre-axis `HEAD`, which is the one mechanism S1 landing does consume. The hook's own first alternative survives it: those arms were authored against a working tree whose `SKILL.md` was byte-identical to commit `7c794b79341313f8b6832d36db5df5ef4e27114d`, and that pinned revision stays recoverable after the axis is in `main`. What is untested is only whether authoring against a pinned revision, rather than against the working tree, reproduces the baseline — plus marker-region removal, where a first attempt left a stray blank line that `git diff` caught.
```

**Why the second hook exists.** Before the 2026-09-20 amendment the unrouted arm was free, because the axis had not shipped. After `S1` the router carries the axis on every run, and the spec's `no shape lens selected` receipt fires only when no shape carries an open decision — which changes the source problem rather than suppressing the routing. Naming the baseline mechanism is not an edit to the predeclared bar; it is what makes the bar runnable.

**Verdict:** untested — the probe ran on 2026-09-20 and could not decide. Read literally neither limb fired, but a control pair of two *unrouted* runs of the same brief diverged more than the routed/unrouted pair did: 15 differing load-bearing concerns against 11. An instrument that returns the same answer when the treatment is absent is not measuring the treatment, so reporting `survived` would report an artifact. The `kill_condition` and `activity` fields above are unedited and stand for whatever experiment can test them; `status` carries this run's outcome, which is what that field is for. `docs/specs/architect-design-shape-overlay/notes/probe/` holds the four arms, their hashes, the method, both blind judgments, and `verdict-final.md`, which names the measurement study that would settle it. `S2` and `S3` therefore stay gated: the condition they are conditional on is unmet, not lifted, and neither is contracted.

**Measurement dependency, recorded rather than resolved.** The obvious instrument for this kill condition is `DA10`, which slice 2 shipped. It is not used here, because `architect-design-gate-calibration` exists precisely to establish whether `DA10`'s bound is sound. Measuring this bet with an uncalibrated instrument would produce a verdict that reads clean whichever way the bound is wrong. The two intents are independent to build: nothing in this one waits on calibrated gates to ship. The dependency is on *verification*: calibrate the instrument, then trust a mechanical verdict from it. It was carried as a `needs` edge on this intent's `backlog.open` entry in `workspace.toml`. That entry was unregistered on 2026-09-20 when this intent moved to `Accepted`, because no registered collection admits an intent at that status, and the edge went with it. **This paragraph is now the dependency's only home.** Until that edge is discharged, this bet's verdict rests on the reviewer judgment named in the kill condition above, not on a `DA10` result.

## Decomposition

Cut by shippability, into three slices. Each ships, tests, and delivers on its own; none is a component or layer cut.

```
architect-design-conditional-overlays (feature)
├─ S1  system-shape axis                              [CONTRACTED — docs/specs/architect-design-shape-overlay/]
├─ P   the overlay probe                              [SPIKE — carries the kill condition; ran against S1's working-tree axis]
├─ S2  workload axis beyond GenAI/agentic             [conditional on P's verdict]
└─ S3  conditional internal-boundaries view           [conditional on P's verdict; needs S1's shape axis]
```

**Why only S1 is contracted.** The bet — that routing more lenses adds concerns rather than bulk — is un-resolved, and `S2` and `S3` inherit it whole. Contracting all three now would fan specs out of a bet no probe has tested. Because the approach is `prototype-led`, the probe needs the axis to exist before it can run.

**Amended 2026-09-20 — the probe is separated from `S1` and runs as a spike.** `S1` was originally contracted as the axis *and* the probe together. Authoring that contract took eight adversarial review rounds; the shape axis drew no finding in any of them and every round's findings were against the probe. Round eight established why: the probe's remaining questions are empirical, not specificational — whether a passage diff is a sound proxy for a concern the baseline missed, whether the routed document is identifiable from its own vocabulary, and how an overlay instruction is bound to the shipped region. A document cannot settle those, so specifying the probe further was not converging. `S1` therefore ships the axis alone, and the probe runs afterwards as a bounded spike against it, owned by the architect pack maintainer. The kill condition above is unchanged and remains the spike's bar; `DA3` and `DA10` remain barred as its instrument. `S2` and `S3` are contracted only once the spike returns a surviving verdict, never on `S1` having shipped.

**What a killed verdict costs `S1`.** `S1` ships before the bet is tested, so a kill does not leave it untouched: a separate spec reverts the shape axis, its eval case, its construction suite, and the ADR-0118 erratum. Until that revert lands the axis sits in `main`, which the door rating above prices as a patch release.

**Why `S3` is not folded into `S1`.** Its trigger reads the system shape, so it cannot precede the shape axis. Folding it in would put two decisions behind one verdict and make a kill unattributable.

**Branch considered and dropped.** A cut along the three excluded items — ports-and-adapters, the router import, the OKF ontology — was rejected: those are exclusions, not slices, and none of them ships anything.

## Delivery contract — S1

For the `new-spec` gate. Attributed context, not an approved spec.

- **Outcome:** the design router selects a system-shape concept. (Amended 2026-09-20: the paired-design comparison moved to the separately-owned spike; see Decomposition.)
- **Boundaries:** `packs/architect/.apm/skills/architect-design/` — its routing and its subsystem template asset. Nothing outside the skill (ADR-0118's own scope line).
- **Non-goals:** the workload axis (`S2`); the internal-boundaries view (`S3`); ports-and-adapters as a default spine; importing `architect-assess/references/concept-routing.md`; any new OKF concept or category; any change to the three templates' section structure or the `D1`-`D6` criteria.
- **Dependencies:** none to build. A verification-only dependency on `architect-design-gate-calibration` was carried as a `needs` edge on this intent's `backlog.open` entry until 2026-09-20, when acceptance unregistered that entry and the edge with it. It never blocked delivery: `S1` returns no verdict, and the spike's verdict rests on reviewer judgment rather than on a `DA10` result. The measurement-dependency paragraph in `## De-risk` is its home now.
- **Design context:** six system-shape concepts ship under `packs/architect/okf/architecture-lenses/concepts/system-shapes/`. Before `S1`, `SKILL.md` step 4 (Stage 0) routed on quality, provider, local-first, novelty, and GenAI/agentic, with no shape axis; `S1` added one there. The corpus ontology is pinned by exact equality in `packs/architect/tests/pack/test_architecture_lenses_corpus.py`, so the axis is skill routing and adds no concept file.
- **Delivery questions, for the spec author:** which named trigger selects a shape when a design exhibits more than one; whether a shape-routed concept loads at a tier or whole. Both are answered in `docs/specs/architect-design-shape-overlay/`: the trigger is an open decision turning on the shape's coordination mechanism, and a shape concept loads whole because the six are flat files with no tiers. The third question — what is recorded when the paired designs disagree with the reviewer — moved to the spike with the probe.
- **Verification the contract carries:** the predeclared kill condition above is the acceptance bar for the probe, and it is not to be restated as a softer criterion. Amended 2026-09-20: it binds the spike rather than `S1`'s spec, because the probe is no longer in that spec's scope.
- **Source provenance:** ADR-0118 (Accepted) at `c4b2f5912bad080f095ffb32d354b54c31d6c54f`; this intent's own de-risk block.

## Source

- Mode: repo-origin
- Locator: docs/adr/0118-architect-design-scope-routed-model-first-templates.md
- Revision: c4b2f5912bad080f095ffb32d354b54c31d6c54f
- Authority: repo-origin
