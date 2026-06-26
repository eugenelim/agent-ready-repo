# Spec: traceability-lint

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0048 (governing — Decision 6); RFC-0040, RFC-0019, RFC-0025, RFC-0030, ADR-0022, RFC-0049 (mechanism precedent)
- **Brief:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A maintainer of an autonomous product-team workspace needs to know, mechanically,
that the artifact chain holds together — that no screen was designed without a
service behind it, no spec was authored without a discovery parent, no component
was built without a spec. The **traceability lint** is the tool that answers this.
It walks the chain
`outcome → opportunity → capability → screen → action → service → contract → spec → component`
and flags every **structural orphan** — a node that exists but asserts no producer
above it (a *backward* orphan — the scope-creep / unjustified-artifact signal) or
has no consumer below it (a *forward* orphan — the uncovered-intent signal). It
generalizes `receive-brief`'s `lint-brief-coverage.py` (which checks the single
brief↔spec edge in one repo) to the full nine-layer chain **across repositories**.

**The chain spans repos, because the loops do.** `work-loop` builds **per
module** — one module is one repo (or one `packages/<c>/` within a monorepo).
`discovery-loop` and the integration loop ([RFC-0049](../../rfc/0049-the-integration-loop-and-company-os.md))
work **within one module or across many** — so the upstream discovery artifacts
(`outcome`…`service`, the shared contracts) commonly live in a discovery or
value-stream **meta-repo** ([ADR-0022](../../adr/0022-value-stream-meta-repo-cross-component-layer.md)),
while each `spec`+`component` is built in its own module repo. A lint that scans a
single working tree therefore sees only part of the chain. The crossing is handled
the only way a cross-boundary link can be: **by convention, not by path** — every
node carries a **stable, location-independent identifier** (a marker slug; a
component's Backstage `kind:namespace/name`; a `contract@version`) and every edge
is a **conventional pointer field carrying that id** (`Discovery:`/`Brief:`/
`parent-intent:` upward, `Component:` and `contract@version` across), exactly the
mechanism the value-stream layer already ships (reference-by-version + a read-only
courier snapshot, never a fork). The lint **reuses that mechanism; it never invents
a parallel one.**

The crossing is what makes a cross-repo edge endpoint resolve to one of **three**
states, not two: **local** (resolvable in this root), **satisfied-by-reference** (a
well-formed conventional pointer — a stable-id resolving to an external target,
optionally a courier snapshot present, and flagged `pinned`/`unpinned`), or
**unresolvable**. A satisfied-by-reference endpoint is **not** a defect; the lint
reports an
unresolvable cross-repo endpoint honestly as `unknown / not-yet-catalogued` (the
value-stream rollup's own term) rather than crashing or false-greening — the
open-world posture every federated catalog takes.

Success is: the maintainer runs one command — in a single module repo, or in the
meta-repo over the federated rollup — and learns exactly which nodes are
disconnected and in which direction, which references cross a repo boundary and
whether they are pinned, and which targets are not yet catalogued. A strict mode
fails a convergence or CI gate when the local chain must be closed; graceful
silence in a workspace with no chain artifacts at all. The lint checks *structure
only*; whether a node is parented to the **right** outcome (semantic scope-creep)
is never its call — structural presence is mechanizable, semantic correctness is
not (the established traceability split).

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Identify every node by a stable, location-independent id carried by
  convention** — a marker slug, a component's `kind:namespace/name` triplet, a
  `contract@version` — never a file path. Paths are local; ids cross repos.
- **Reuse the existing cross-repo pointer mechanism** — `parent-intent:`,
  `Brief:`/`Discovery:`, `Component:`, `contract@version` + read-only courier
  snapshot, and the value-stream rollup row schema (ADR-0022; `align-value-stream`).
  Read references at their pinned version; treat a snapshot as provenance, never an
  authority.
- **Resolve each layer's base location by the three-tier rule** —
  `agentbundle-layout.toml` config → designed default → discover-by-marker — never
  a literal hardcoded path. Base-location ambiguity is reported, not guessed; node
  instances within a resolved location are enumerated (multiplicity is normal).
- **Resolve a cross-repo endpoint to one of three states** — local /
  satisfied-by-reference / unresolvable — and report an unresolvable cross-repo
  target as `unknown / not-yet-catalogued`, never as satisfied and never as a
  fatal orphan (the open-world, federated-catalog posture).
- **Degrade gracefully.** A missing marker, pointer, layer, snapshot, or sidecar
  is reported informationally — never a crash. No chain artifacts at all → exit 0
  with no diagnostic (the `lint-brief-coverage.py` no-brief precedent).
- **Keep the output shape and exit-code discipline aligned** with the two
  precedent lints: informational lines to stdout, hard violations to stderr, a
  one-line summary.

### Ask first

- **Changing a node's canonical marker, its stable-id scheme, or a producer-pointer
  field** — these are the conventions every producing skill and every other repo
  write against; a change ripples across repos.
- **Adding a chain node-type** beyond the nine, or **reordering the chain** — the
  spine RFC-0048's whole model hangs from.
- **Wiring the lint as a fail-closed CI gate** on a path where a PR event exists —
  permitted, like the precedent lints, but a deliberate gating choice, not a
  default this spec turns on.

### Never do

- **Never attempt semantic scope-creep detection** — judging whether a node is
  parented to the *correct* in-appetite outcome. Deferred to the coordinator spike
  (RFC-0048 O10); stays a human call at G1.5. The lint judges *presence* of an
  edge, never its *rightness* — the structural-vs-semantic boundary the
  traceability literature shows is not reliably mechanizable.
- **Never invent a parallel cross-repo pointer or id scheme** — reuse the
  value-stream / Backstage conventions; a second scheme forks the graph.
- **Never treat a well-formed cross-repo reference as a dangling edge**, nor a
  not-yet-catalogued target as silently satisfied — the two opposite false
  verdicts a naive single-tree scan produces.
- **Never wire the lint into the projected `pre-pr` hook body** — that body
  projects to adopter trees and would mis-fire (no PR-open hook event in an adopter
  repo); the agent-invoked finish-time checklist and an explicit CI gate are the
  two invocation surfaces.
- **Never add a new top-level dependency** — stdlib-only Python, like both
  precedent lints.
- **Never `import` from another skill's scripts** — shared token-extraction logic
  is kept in lockstep by hand, the way the precedent lints already are.
- **Never hardcode a path** into the discovery of any artifact type — a single
  literal `docs/specs/` shortcut defeats the marker generalization.

## Testing Strategy

- **Structural-orphan detection (up/backward, down/forward, terminal exemption,
  layer-skip): TDD.** A compressible invariant over a graph — fixture workspaces
  in, exact orphan list out. The core of the lint.
- **The three endpoint states (local / satisfied-by-reference / unresolvable) and
  the three defect classes (orphan / dangling / cycle): TDD.** Each is
  deterministic; fixtures cover the discriminators — a well-formed cross-repo
  reference is satisfied-by-reference, a pointer to a missing local target is
  dangling, an absent pointer is an orphan, an unresolvable cross-repo target is
  `unknown / not-yet-catalogued`.
- **Node realization + stable-id identity: TDD.** A fixture intent ladder, journey,
  blueprint assert container-embedded extraction; a fixture screen/spec/contract/
  component assert file-backed recognition and stable-id (slug / triplet /
  `contract@version`) derivation.
- **Cross-repo resolution via rollup/sidecar: TDD + integration.** A fixture
  meta-repo rollup + component-repo pair assert references resolve across the
  boundary; a pinned-vs-unpinned reference is reported accordingly.
- **Run postures (single-repo, meta-repo/federated): goal-based + integration.**
- **Exit-code contract: goal-based check.**
- **Graceful degradation / no-op-clean: TDD.**
- **Projection to every adapter: goal-based check** (`make build-self`).

## Acceptance Criteria

- [ ] The lint **recognizes each chain node-type by its realization** — a
  **file-backed node** (`screen`, `contract`, `spec`, `component`) by canonical
  filename + frontmatter `type:`/header, and a **container-embedded node**
  (`outcome`/`opportunity`/`capability` in the intent ladder, `action` in the
  journey, `service` in the blueprint) by extracting its typed entry — per a
  declarative marker registry, with **no hardcoded artifact path** in source.
- [ ] The lint **identifies every node by a stable, location-independent id carried
  by convention** — a marker slug, a component's `kind:namespace/name`, a
  `contract@version` — reusing the existing conventions (`parent-intent:`,
  `Brief:`/`Discovery:`, `Component:`, `contract@version`), never a file path and
  never a new parallel id scheme.
- [ ] Each **layer's base location is resolved by the three tiers** (config →
  default → discover-by-marker); base-location ambiguity is reported, while
  multiple node instances within a resolved location are enumerated.
- [ ] The lint **builds the directed edge set** by reading each adjacent-layer
  edge from the conventional pointer that carries it — a back-link
  (`Discovery:`/`Brief:`/`parent-intent:`) or a forward declaration (`Component:`,
  `contract@version`); a `component`'s producer edge is derived by reverse-indexing
  specs' `Component:` declarations.
- [ ] Each edge endpoint **resolves to one of three states** — **local**
  (resolvable in this root), **satisfied-by-reference** (a well-formed conventional
  pointer — a stable-id resolving to an external target, courier snapshot optional),
  or **unresolvable** — and a **satisfied-by-reference endpoint is never reported as
  a defect**. **Pinning is an orthogonal flag on the satisfied-by-reference state,
  not part of its definition:** a reference carrying a pinned version is `pinned`; a
  stable-id reference with no pinned version is `unpinned` — still
  satisfied-by-reference, reported informationally (exit 0, never fatal), because
  pinning is the ADR-0022 `contract@version` convention and an unpinned reference is
  a soft warning, not a broken edge. The state/discriminator is thus total over
  every pointer shape.
- [ ] A node that **asserts no producer pointer** (and is not in the root layer) is
  a **backward (up) orphan**; a node with **no consumer pointing at it** (and not
  in the leaf layer) is a **forward (down) orphan** — each named with node, type,
  and missing direction.
- [ ] **Terminal layers are exempt** at their open end: `outcome` is never a
  backward orphan; `component` is never a forward orphan (its cross-repo consumer,
  the integration loop, is [RFC-0049](../../rfc/0049-the-integration-loop-and-company-os.md)'s).
- [ ] **Layer-skip is scoped to globally-unpopulated layers only**: when a layer
  has no artifacts anywhere in scope (a CLI tool has no `screen`/`action` layer),
  edge requirements resolve to the nearest *populated* adjacent layer; a node that
  skips a layer **populated elsewhere** is a real orphan, not exempt.
- [ ] A **dangling edge** — a pointer that names a **missing local target**, or is
  malformed (no resolvable stable-id and not a well-formed cross-repo reference) —
  is a hard violation, **exit 1 in every mode**. The discriminator is explicit and
  three-way: absent pointer = orphan; pointer to a missing local target / malformed
  = dangling; well-formed external pointer = satisfied-by-reference. The classifier
  never reports one break as two classes.
- [ ] A **self-referential or cyclic producer pointer** (A→A, A→B→A) is a hard
  violation reported **without non-termination**, **exit 1 in every mode**.
- [ ] An **unresolvable cross-repo endpoint** (and a not-yet-catalogued rollup row)
  is reported as **`unknown / not-yet-catalogued`** — **informational, never fatal
  and never silently satisfied** (the open-world, federated-catalog posture).
- [ ] **Exit codes are coherent:** default mode — structural orphans are
  **informational (exit 0)**; **`--strict`** — any structural orphan **exits 1**
  (the convergence-/CI-gate enforcing "traceability closed", RFC-0048 O6); dangling
  edges and cycles **exit 1 in every mode**; unresolvable-cross-repo, unpinned
  references, and drift are **never fatal**.
- [ ] The lint runs in **two postures**: **single-repo** (checks the local
  sub-chain and validates that outbound cross-repo pointers are well-formed — carry
  a stable-id — reporting an unpinned outbound pointer informationally), and
  **meta-repo / federated** (joins component rows through the value-stream rollup /
  sidecar). `--root` selects the tree per invocation.
- [ ] When a **recognized sidecar `traceability.json` or value-stream rollup is
  present** it supplies the cross-repo edge set the lint resolves references
  against (authoritative-when-present, RFC-0048 D7); when **absent** the lint
  **derives the edge set from the local artifacts** (the standalone mode). A
  matrix↔artifact disagreement is reported as **drift, warn-only (exit 0)** — the
  warn-only posture is this spec's firm shipped contract; **future hardening** —
  promoting drift to a hard violation once the sidecar matrix schema is pinned — is
  tracked at
  [`docs/backlog.md` → `sidecar-drift-hard-fail`](../../backlog.md#sidecar-drift-hard-fail).
- [ ] The lint **no-ops cleanly** — exit 0, no diagnostic — when no chain artifacts
  exist (the `lint-brief-coverage.py` no-brief precedent), and **degrades
  gracefully** (informational, never a crash) when a marker, pointer, layer,
  snapshot, or sidecar is absent or unreadable.
- [ ] The lint **never reports a semantic finding** — no judgment about whether a
  node is parented to the *correct* outcome; only edge presence/absence, the three
  endpoint states, and the three defect classes.
- [ ] The lint accepts **`--root DIR`** and **`--strict`**, runs stdlib-only (no
  new dependency), and mirrors the precedent lints' output shape (stdout report,
  stderr violations, one-line summary).
- [ ] **`make build-self`** projects the script to every adapter's
  `work-loop/scripts/`, the way `lint-spec-status.py` projects.

## Assumptions

- Technical: generalizes `lint-brief-coverage.py` — reads artifacts directly
  (markers + conventional pointers), reports coverage, hard-fails only on a defect
  class (source: `packs/core/.apm/skills/receive-brief/scripts/lint-brief-coverage.py`).
- Technical: ships as a `core` `work-loop` skill script projected to every adapter,
  the `lint-spec-status.py` home (source:
  `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`; user confirmation
  2026-06-25 — alternative dedicated-skill home left open).
- Technical: stdlib-only Python, `.py` for Windows portability (source: both
  precedent lints; CLAUDE.md new-tools-are-Python rule).
- Technical: **the chain spans repos** — `work-loop` is per-module (per repo);
  `discovery-loop` and the integration loop are same-or-cross-module/repo; upstream
  discovery artifacts and shared contracts commonly live in a discovery /
  value-stream meta-repo (source: user direction 2026-06-25; RFC-0030 Decision 9;
  ADR-0022; RFC-0049; supersedes RFC-0048 note 08's single-monorepo scope — a
  tracked RFC-0048 amendment).
- Technical: cross-boundary links are **by convention, not by path** — a stable,
  location-independent id (marker slug / Backstage `kind:namespace/name` /
  `contract@version`) carried in a conventional pointer field, resolvable in one of
  three states (local / satisfied-by-reference / unresolvable). This is the
  invariant pattern of every cross-boundary traceability system surveyed — OSLC
  (link by URI, version-pinned), OpenLineage (`namespace:name`), SLSA/in-toto
  (subject digest + `resolvedDependencies`), purl, Backstage (`kind:namespace/name`)
  — and is already realized in-repo by ADR-0022's reference-by-version + courier
  snapshot (source: notes/cross-repo-traceability-research.md; ADR-0022;
  `packs/product-engineering/.apm/skills/align-value-stream/`).
- Technical: the lint **reuses** the value-stream rollup row schema
  (`Component | Brief (repo+slug) | Contract@version | Status (snapshot) | Coverage pointer`)
  and `unknown / not-yet-catalogued` honest-gap term as the cross-repo join, never a
  parallel mechanism (source:
  `packs/product-engineering/.apm/skills/align-value-stream/assets/rollup-template.md`;
  `references/cross-component-rollup.md`).
- Technical: the canonical chain is the nine-node
  `outcome → opportunity → capability → screen → action → service → contract → spec → component`
  (the form the brief named), with note 08's `…spec → component` terminus —
  `component` is the buildable leaf and `code` (note 02's worked-example terminus) is
  the component's *content*, not a separate node. Note 01's chain carries a distinct
  `Journey step` rung and pairs `Screen + Action`; deliberately compressed to the
  nine here; reordering/adding a node-type is an *Ask first* boundary (source:
  RFC-0048 note 08 ontology; note 02 worked example; note 01).
- Technical: conventional pointer fields are matched by their **rendered on-disk
  form**, not a raw frontmatter key — the brief's `**Parent intent:**` bold label
  (`packs/core/seeds/docs/product/briefs/_template.md`), the spec's
  `**Status:**`/`**Brief:**` headers — exactly as `lint-brief-coverage.py` matches
  `**Brief:**`; the logical field names in this spec (`parent-intent:`, `Brief:`,
  `Component:`) denote those rendered labels, matched case-insensitively (source:
  `packs/core/.apm/skills/receive-brief/scripts/lint-brief-coverage.py` `_BRIEF_RE`).
- Technical: four of the nine node-types are **container-embedded**, not per-file —
  `outcome`/`opportunity`/`capability` are intent-ladder rungs, `action` a
  journey-map entry, `service` a service-blueprint entry; the lint recognizes them
  by intra-container extraction. In the ladder, `outcome`/`opportunity` are intent
  *kinds* and `capability` a *level* (note 04), so the rung→chain-node extractor is
  reconciled against the `frame-intent`/`decompose-intent` format and degrades
  until present (source: RFC-0048 note 04 artifact inventory; note 08 ontology).
- Technical/governance: the sidecar matrix is **authoritative when present**
  (RFC-0048 D7) with a **derive-from-artifacts standalone mode when absent**; the
  refinement is reconciled into RFC-0048 as a tracked amendment per its
  provisional-foundation note (source: RFC-0048 D7 + the shippable-standalone goal).
- Process: the structural-vs-semantic split is grounded — structural link presence
  is mechanizable, semantic link correctness is not reliably so (the SoK
  traceability survey; ReqToCode's "structural presence, not semantic correctness";
  the low precision of IR/ML trace-recovery), and a *backward* orphan is the
  classic scope-creep / unjustified-artifact signal (RTM, ISO 26262 / DO-178C
  bidirectional traceability) — so semantic scope-creep stays the human call at
  G1.5 (source: notes/cross-repo-traceability-research.md; RFC-0048 Decision 6 / O10).
- Process: the `Discovery:` spec→discovery up-edge header (O8) and frontmatter
  `type:` markers on discovery artifacts are **out-of-scope dependencies** —
  authored by sibling children and the RFC-gated "CONVENTIONS edit" follow-on; the
  lint degrades gracefully where absent (source: `docs/CONVENTIONS.md:284`
  spec-metadata contract is RFC-gated; RFC-0048 follow-on list).
- Process: the sidecar `traceability.json` matrix schema is `core` doctrine **not
  yet pinned**, so drift ships warn-only until it lands (source: RFC-0048 D7;
  deferral `sidecar-drift-hard-fail` in `docs/backlog.md`).
- Process: semantic scope-creep detection is out of scope — deferred to the
  coordinator spike (source: RFC-0048 Decision 6; note 09 O10).
- Product: the chain and the structural-vs-semantic split came directly in the
  brief; the cross-repo / per-module-loop topology is the user's correction of the
  initial single-monorepo framing (source: user direction 2026-06-25).
