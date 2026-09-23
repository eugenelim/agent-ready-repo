# Repository work graph

- **Slug:** `repository-work-graph` <!-- canonical identity; independent of the filename ordinal -->
- **Status:** Accepted
- **Accepted:** 2026-09-19 by eugenelim. Revision `01676a0990c0dcff` returned a clean independent intent-mode shaping review on all six conditions. The gate was earned rather than granted: the first round on revision `dabd803955ef3fcb` drew `MALFORMED(children)`, which was correct — the decomposition log still described the pre-restructure cut, naming coordination and projection as children after both became sibling capabilities. That log was rewritten to the current five-child cut. The reviewer was then mutation-checked, returning `MALFORMED(children)` for a packet with the child list removed and clean for the repaired artifact, so the pass discriminates on content. Deliberately unregistered: `backlog.open` is the only initiative-free collection and admits `Status: Draft` alone.

- **Nonmaterial correction 2026-09-19 by eugenelim, lifecycle owner.** `Unresolved questions`, `Projection` and `Source` were backfilled to meet ADR-0098 D2's admission contract, which this family met only in part because it was framed by `frame-intent` and never admitted through `intake-intent`. `intake-intent` classes a change to projection, unresolved questions or source authority as material, which would return this intent to `Draft`; the lifecycle owner recorded it as nonmaterial because the sections record open matters and provenance that already existed in the artifact, and decide nothing new. Prior review evidence stands.
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** opportunity:graph-powered-sdlc
- **De-risked:** 2026-09-18
- **Shaping-reviewed:** 2026-09-19
- **Decomposed:** 2026-09-19 children

## Outcome

- **Steerable input:** Reduce the effort it takes to answer "what work exists, at what altitude, under what parent, in what state, and where does it land in delivery" from the repository's own artifacts.
- **Lagging outcome:** Product engineers and delivery agents navigate repository work as a trustworthy graph from intent through delivery, with each artifact's altitude, parent, state and delivery mapping answerable without reading the corpus.
- **Guardrail:** Canonical artifacts stay authoritative and the graph stays derived. Deterministic discovery, lifecycle integrity and provenance do not weaken. Dependency checking and dispatch safety are `CAP-0003`'s to preserve, and nothing here may erode them. No tracker's hierarchy becomes the product model. Existing accepted decisions and existing registered work keep their meaning.

## Opportunity

- **Functional job:** Find, place, and follow a piece of repository work from the outcome it serves down to the change that ships it, without reading the whole corpus or reconstructing the shape by hand.
- **Emotional job:** Trust that what the repository says about its own work is current, because the answer is derived from the artifacts rather than restated beside them.
- **Social job:** Show maintainers and adopters a defensible account of what is being built and why, and show an external stakeholder the same account in their own tracker without surrendering the model to it.
- **Struggling moment:** Today the answer is assembled by hand. `docs/product/intents/` held 130 intent files against 107 canonical registrations when this intent was framed on 2026-09-18, so 23 had no registry presence and the registry is not the inventory. The 23-file gap is the evidence; the population moves as intents are added, so a later count of the same directory reads higher on both sides. Only 9 intents carry a `Parent intent:` pointer, so altitude and parentage are mostly unrecorded rather than merely unindexed. `workspace.toml` is 1,559 lines and every registration edits it: over the 30 days measured on 2026-09-13, 20 of 51 rebases that had to replay a `workspace.toml` edit conflicted.

## Boundary

Includes:

- intent discovery and registration;
- identity and typed ordinals, and the cross-artifact reference grammar that resolves a pointer to exactly one artifact. **Decided 2026-09-18:** the ordinal is allocated `max + 1` over the directory unioned with `origin`, forward-only, renumbered at admission, by a prefix-type-aware allocator that edits no counter file — so this intent's guardrail against a shared counter holds. It rides in the filename as a typed prefix at every altitude, while identity binds to each artifact's `Slug:` field, so a renumber changes no reference. An altitude change after admission reissues at the new prefix and leaves a tombstone. [FEAT-0001](FEAT-0001-intent-identity-and-registration.md) owns the record, the measured renumbering cost, and the ADR-0108 reconciliation;
- parent and related-intent edges;
- derived graph and status views over the work corpus, and the surfaces that carry them;
- mappings from intents to briefs and specs;
- repository versus personal intent locations.

Excludes:

- **the three sibling capabilities' scope.** The accepted decision corpus as constraints belongs to `CAP-0002 Decision graph`; operational coordination state to `CAP-0003 Workspace coordination reorganization`; outbound rendering to `CAP-0004 External tracker projection`.;
- implementation details — which file format, schema, script, or storage shape delivers any of the above;
- a tracker's hierarchy as the canonical model. A tracker stays a projection target;
- wholesale methodology replacement. The existing `frame-intent` → `de-risk-intent` → `decompose-intent` shaping loop and the existing delivery loop stay in force, and this intent coordinates its children rather than absorbing the artifacts they touch;
- **any persisted graph artifact.** Decided 2026-09-18: the graph is derived from artifact headers on demand and never committed or written to disk, across every child. `intent-graph-navigation` § Settled design decisions holds the reasoning and the condition that would reopen it. The corresponding guardrail is that graph metadata lives in preamble fields and never in artifact bodies, because that is what keeps derivation cheap enough to repeat.

## Owner

- eugenelim, Platform Core maintainer. Accountable for this intent's outcome.

## Unresolved questions

- Whether an adopter who installs the packs but never runs the shaping loop is unharmed by a richer repository graph. The only open assumption, and the research names it as the first thing to test.

## Projection

Not yet selected. Outbound tracker projection is [CAP-0004](CAP-0004-external-tracker-projection.md)'s surface and is not yet shaped, so no target exists to project to.

## Assumptions

- An adopter who installs the packs but does not run this repository's shaping loop is not harmed by a richer repository graph, because the graph is derived and the current slug/path identity keeps working. **Untested** — the only open assumption this intent still carries, and the research below names it as the first thing to test.
- **Knowledge surface:** in-repo doc set (`docs/adr/`, `docs/product/`, `packs/`). No MCP knowledge tool or internal CLI was present in this session.

Two assumptions left this list once they stopped being assumptions. The capability bet — repository artifacts as the authoritative inventory while the workspace keeps only non-derivable coordination state — was tested and survived, and the **De-risk record** below owns it end to end. The typed-ordinal question was settled on 2026-09-18 and is recorded as a decision in the **Boundary** above.

## De-risk record

- **Level kind:** capability, so the pack maps the dominant assumption to **architectural / adoption** — which is what was tested. The verdict below was reached while this intent was framed one rung lower and briefly held one rung higher; neither move touched the assumption, because an allocation and identity mechanism's viability does not depend on the altitude of the intent that owns it.
- **Reversibility triage:** two-way door for the artifacts and registrations this intent itself creates — they are files and registry entries, and reverting them costs one commit. One-way door for the capability bet: once repository tooling, generated views, and the corpus depend on the artifacts being authoritative, moving authority back is expensive. The one-way half sets the default.
- **Prototype-approach:** `validate-first`. The cheapest probe that can fail is a consumer inventory over the current code, not a build.

### Riskiest assumption

Repository-contained intent artifacts can provide the authoritative inventory and graph while workspace coordination retains only the non-derivable operational state, without weakening deterministic discovery, lifecycle integrity, provenance, dependency checks, or dispatch safety.

What would have to be true: every current repository consumer of a registered intent entry must read either something the intent artifact can carry, or operational coordination state that a reorganized workspace would still hold. If some consumer needs a third thing, the split does not exist and the bet is wrong.

### Kill condition, predeclared

The repository has no traffic metric here, so the bar is qualitative. **Kill if any one of the five named properties — deterministic discovery, lifecycle integrity, provenance, dependency checking, dispatch safety — has a current repository consumer that can be satisfied only by workspace-held state which the intent artifact cannot carry and which is not operational coordination state.** One such consumer is enough to kill. The line was set before the inventory was run, and the inventory covers all five properties, so the test could have failed on any of them.

### Evidence, per property

Measured on 2026-09-18 against the working tree.

- **Deterministic discovery — survives.** The artifact directory is already the inventory and the registry is already a lossy subset: 130 intent files on disk against 107 registered canonical intent entries, with 23 real intents carrying no registry presence and no registered entry pointing at a missing file. Artifact-sourced discovery is also already implemented — `packs/core/.apm/skills/work-loop/scripts/lint-traceability.py` reports `source=derived from artifacts, 599 node(s), 85 edge(s)` with no workspace read. Moving inventory authority to the artifacts cannot lose anything the registry holds, because the registry holds strictly less.
- **Lifecycle integrity — survives.** Reconciliation already reads lifecycle status out of the artifact: `_metadata_from_root` parses the artifact's `- **Status:**` field (`packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`), and 128 of the 130 intent files carry one (119 Draft, 9 Accepted). `docs/product/AGENTS.md` § "Status has one home" already assigns status authority to the artifact and casts registered membership as confirmation evidence. What membership carries beyond that — which lifecycle list, which initiative — is coordination state, and it stays.
- **Provenance — survives.** The artifact is already a provenance carrier and reconciliation already cross-checks it: `provenance_mismatch` compares the entry's `source.parent`, `ref`, and `revision` against `parent`, `source ref`, and `source revision` read from the artifact, and `intake-intent`'s renderer writes `source_ref` and `source_revision` into the artifact. The admission pin itself — that a named revision was admitted at a moment — is non-derivable coordination state and stays in the registry.
- **Dependency checking — survives.** `needs` edges are chosen at admission and are absent from the artifact. They are non-derivable operational coordination state, which is exactly what the assumption says the workspace retains. 28 of the 107 registered intent entries carry a non-empty `needs`.
- **Dispatch safety — survives, and is structurally independent.** `dispatchable` in `workspace_status_engine.py` requires `entry.kind == "spec"`, a `work.queue` membership, an active initiative, an `Approved` status, and a readable plan. No intent entry can ever be dispatchable, and `work-intake` step 6 registers an admitted intent as "a Draft, non-dispatchable entry" with no processor dispatch. Intent registration cannot move dispatch in either direction.

### Verdict — survived

No consumer of any of the five properties needs a third category of state. Two constraints were found and are recorded rather than waived:

- **C1 — position is an in-run join key.** `_surviving_work` in `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` matches closeout verdicts by `(collection, entry_index)` rather than by any entry value, because no value is unique — a legacy `"spec/x"` string and a canonical `{path = "spec/x", kind = "defect"}` entry share a raw path. Both sides walk the same in-memory arrays in one parse and "agree by construction", so this is a join inside one derivation, not a durable stored identity. It constrains how the workspace side may be reorganized — `workspace-coordination-reorganization` must supply a stable per-entry identity or preserve single-parse enumeration — and it does not touch the inventory claim.
- **C2 — a retained field with no reader.** For `repo-origin` entries the registry's `source.revision` is compared against nothing: the `provenance_mismatch` revision check is guarded by `entry.source.mode == "tracker-origin"`. 89 of the 107 registered intent entries carry a revision, and all of the entries this family creates are `repo-origin`. `workspace-coordination-reorganization` must decide whether that field is an admission pin worth keeping, and must not assume a consumer exists.

### Validation hook

```
validation_hook:
  assumption: Repository-contained intent artifacts can be the authoritative inventory and graph while workspace coordination keeps only non-derivable operational state, with deterministic discovery, lifecycle integrity, provenance, dependency checks, and dispatch safety intact.
  kill_condition: Any one of those five properties has a current repository consumer that can be satisfied only by workspace-held state the artifact cannot carry and that is not operational coordination state.
  activity: to-validate — a maintainer-run navigation exercise in which a product engineer and a delivery agent each answer "what work exists, under what parent, in what state, and where does it land" from the derived graph alone, on a repository whose registry has been reduced to coordination state, plus a replay of the consumer inventory against every writer and external adopter of `workspace.toml`. The evidence above is desk-grounding against current code, and desk-grounding is not validation.
```

## Research

[Graph-powered SDLC — applied survey](../research/graph-powered-sdlc-survey.md) bears on this capability in two ways. The no-daemon decision is externally corroborated — build-graph daemons are latency optimisations over a graph the files alone define. And the observer boundary is binary rather than gradual: coverage is near-total where a shaping skill writes the header and absent outside it, so the assumption that an adopter who never runs the loop is unharmed is the first thing to test.

## Fulfilment rollup — the behaviour three of the features jointly enable

When a spec closes, walk the graph **upward**: spec → feature intent → capability → strategy → vision. At each rung ask whether every child is terminal. If so, that rung becomes **eligible** for fulfilment, and the walk continues to its parent until it reaches a rung with an unfulfilled child.

This is the capability's payoff rather than a feature of its own, because no single feature delivers it:

- [Intent-to-delivery traceability](FEAT-0003-intent-delivery-traceability.md) supplies the bottom edge. Without a spec knowing which feature it fulfils, the walk has no first step.
- [Intent graph navigation](FEAT-0002-intent-graph-navigation.md) supplies the walk itself, and the parent edges it traverses.
- [Intent identity and registration](FEAT-0001-intent-identity-and-registration.md) supplies the lifecycle vocabulary the walk evaluates — which statuses are terminal, and which transitions are legal.

**Eligibility is computed; closure is decided** — the computation is this capability's, and the decision belongs to [Lifecycle and closure](FEAT-0005-lifecycle-and-closure.md). The rollup never sets a status. The existing brief-coverage contract already draws this line — an all-shipped spec map makes a brief *eligible* for closeout and explicitly does not close it — and the same rule holds here for the same reason. Rolling a vision to `Fulfilled` because its descendants happen to be terminal would let a mechanical count retire a product bet.

That split is also the mechanism the vision's own de-risk found survives. A machine carries the detection — which rungs just became eligible — and a human sees full detail on one small unit, the single rung now in question, rather than surveying the whole tree at lower resolution. It is the opposite of raising the altitude of human attention, which that de-risk killed.

Three preconditions, each currently unmet and each owned by a named feature. The spec-to-feature edge does not exist. Only 9 of 140 intents record a parent, so most walks terminate at the first rung. And `Level` is unenforced, with 11 intents carrying none at all, so a walk cannot reliably tell which rung it is standing on.

One caution carries over from the research: an automated control that emits plausible output is indistinguishable from a working one. A rollup that silently stops walking — because an edge is missing rather than because a child is unfulfilled — reports the same silence as a correct negative. Its liveness needs deliberate testing, not inference from it having produced answers before.

## Decomposition

Five feature children, each pointing back here through `Parent intent:`. Each child owns its own de-risk state and lifecycle status; this intent records only the cut.

- [Intent identity and registration](FEAT-0001-intent-identity-and-registration.md) — identity, typed ordinals, the cross-artifact reference grammar, and the intent shape contract. Owns lifecycle **entry**; `FEAT-0005` owns exit.
- [Intent graph navigation](FEAT-0002-intent-graph-navigation.md)
- [Intent-to-delivery traceability](FEAT-0003-intent-delivery-traceability.md)
- [Single-ladder migration](FEAT-0004-single-ladder-migration.md)
- [Lifecycle and closure](FEAT-0005-lifecycle-and-closure.md) — what a terminal status means and which workflow may set it.

Decision graph, workspace coordination reorganization and external tracker projection are **sibling capabilities**, not children of this one. They sit under [Graph-powered SDLC](STRAT-0001-graph-powered-sdlc.md) because each is an independent value bet rather than an architectural slice of this one buildable thing.

### Decomposition decisions

- **The cut is by the question each child answers, not by artifact or layer.** Identity answers "what is this and where does it go", navigation answers "what exists and how does it relate", traceability answers "what ships it", single-ladder migration answers "how does the existing corpus move onto one ladder", and lifecycle and closure answers "when is it done and who may say so". Cutting by artifact instead — one child per file touched — would have put `workspace.toml` and the intent corpus in the same child and made the de-risked split unshippable in pieces.
- **One dependency edge between the children, recorded rather than smoothed over.** `intent-graph-navigation` cannot safely make feature intents graph nodes until the reference grammar is typed, which is `intent-identity-and-registration`'s work. The provisional delivery order — identity, navigation, traceability, migration, lifecycle — already respects it, so the edge is planning guidance recorded here rather than a `needs` edge.
- **The decision corpus is a sibling capability, not a child.** Accepted ADRs and RFCs constrain this work but are not work items, and they are a separate population with its own validation. Widening `intent-graph-navigation` to cover both would have merged two populations of different trustworthiness under one bet, so `CAP-0002 Decision graph` takes them and this intent's boundary excludes them.
- **Identity is a precondition the other children consume.** Typed four-digit ordinals — the width is part of the filename contract — are `intent-identity-and-registration`'s subject. A renumber must edit the intent path references in `workspace.toml` in lockstep, so that child and `CAP-0003 Workspace coordination reorganization` share a constraint the delivery order must respect. The typed prefix also makes altitude part of identity, so that child carries the reissue-and-tombstone contract for a post-admission altitude change.
- **A product parent sits above this one.** The sibling-spawn test separates architectural slices of one buildable thing — the five children above — from independent value bets, which are the three sibling capabilities. The second grouping needs a strategy parent, which is `STRAT-0001 Graph-powered SDLC`, itself under `VISION-0001 AI-native ecosystem`.
- **The two workspace de-risk constraints travel with `CAP-0003`.** C1 (position as an in-run join key) and C2 (`source.revision` unread for `repo-origin`) both land on the workspace side, so they are recorded on that sibling rather than held in this intent's de-risk trail.
- **No Project, Epic, Initiative, or Arc artifact was created.** Grouping is carried by the `Parent intent:` edges. A coordination artifact whose only job is grouping would restate this intent's boundary in a second place, which `docs/product/AGENTS.md` § "Status has one home" rules out.

## Source

- **Mode:** repo-origin
- **Locator:** `docs/adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md`
- **Revision:** `d53759325`
- **Authority:** eugenelim, lifecycle owner

Authored in this repository's shaping loop on 2026-09-18, under [ADR-0119](../../adr/0119-retire-the-initiative-ladder-into-the-recursive-intent-graph.md), which retired the Initiative ladder into this intent graph.
