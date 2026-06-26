# Plan: traceability-lint

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The lint is a single stdlib-only Python script,
`packs/core/.apm/skills/work-loop/scripts/lint-traceability.py`, projected to
every adapter's `work-loop/scripts/` the way `lint-spec-status.py` is. It is built
in four layers that mirror `lint-brief-coverage.py`'s shape, scaled from one edge
in one repo to nine edges **across repos**: **(1) find nodes** by marker through
the three-tier base resolution, recognizing file-backed nodes by filename/header
and container-embedded nodes by extracting typed entries; **(2) build the directed
edge set** by reading each adjacent-layer pointer from the artifact that carries it,
keying nodes by a **stable, location-independent id** (slug / `kind:namespace/name`
/ `contract@version`), never a path; **(3) resolve each endpoint** to local /
satisfied-by-reference / unresolvable — joining cross-repo references through a
present value-stream rollup or sidecar; **(4) classify** each node as connected,
structural orphan (backward/forward), dangling edge, or cycle, plus an optional
sidecar cross-check.

The riskiest parts are two. First, the **node-and-edge registry** — per node-type,
how it is recognized (file vs container-embedded) and its stable-id; per
adjacent-pair, which artifact carries the pointer and the field. Second, **endpoint
resolution across a repo boundary**: a `spec` in module-repo-A whose
`Discovery:`/`parent-intent:` points at a discovery artifact in the meta-repo must
read as *satisfied-by-reference* (a well-formed reference — pinned or unpinned),
**not** a dangling edge — the central false-positive a single-tree scan would
produce. The lint reuses
the existing value-stream convention (reference-by-version + read-only courier
snapshot; the rollup row schema; `unknown / not-yet-catalogued`) rather than
inventing a parallel one. Everything is fixture-driven: synthetic single-repo and
meta-repo-plus-module-repo workspaces (full chain, partial chain, container-embedded
extraction, cross-repo reference pinned/unpinned/unresolvable, dangling, cycle,
sidecar drift, empty) each assert an exact finding list and exit code.

## Constraints

- **RFC-0048** Decision 6 (structural orphans only; semantic scope-creep deferred,
  O10); D7 (sidecar matrix authoritative when present); note 04 (which node-types
  are container-embedded vs file-backed); note 08 (marker / three-tier resolution +
  folder ontology — its single-monorepo scope is generalized here, a tracked
  RFC-0048 amendment); note 09 (O4 the lint, O6 "traceability closed", O8 the spec
  `Discovery:` up-edge).
- **RFC-0030 / ADR-0022 / `align-value-stream`** the value-stream meta-repo +
  cross-repo convention this reuses: `parent-intent:`, reference-by-`contract@version`
  + read-only courier snapshot, the rollup row schema
  (`Component | Brief (repo+slug) | Contract@version | Status (snapshot) | Coverage pointer`),
  Backstage `kind:namespace/name`, `unknown / not-yet-catalogued`.
- **RFC-0049** the integration loop — the cross-repo consumer of `component`s
  (the chain's leaf-side context; component-down-edge traceability is RFC-0049's).
- **RFC-0040** the `agentbundle-layout.toml` layout config tier-1 reads.
- **RFC-0019 / `receive-brief`** the `lint-brief-coverage.py` this generalizes.
- **RFC-0025 / `work-loop`** the skill-script projection + agent-invoked
  finish-time invocation surface this rides.
- Prior art for the by-convention cross-boundary model (stable-id, three endpoint
  states, open-world gaps, structural-vs-semantic split) is synthesized in
  [`notes/cross-repo-traceability-research.md`](notes/cross-repo-traceability-research.md).
- The `Discovery:` header and frontmatter `type:` markers on discovery artifacts
  are **out-of-scope dependencies** (spec § Assumptions): read where present,
  degrade where absent.

## Construction tests

**Integration tests:** an end-to-end run over a full-chain single-repo fixture
asserting clean exit 0; the same with one edge cut asserting the named orphan and
(under `--strict`) exit 1; a **meta-repo + module-repo pair** asserting a cross-repo
`Discovery:`/`contract@version` reference resolves as satisfied-by-reference (not
dangling) and an unresolvable one reports `unknown / not-yet-catalogued`; a
recognized sidecar asserting it supplies the authoritative edge set.
**Manual verification:** run the lint against this repo (specs, no discovery chain)
and confirm it no-ops cleanly (exit 0, no spurious orphans).

## Design (LLD)

Stack: stdlib-only Python 3 (`argparse`, `re`, `json`, `pathlib`, `tomllib`),
matching `lint-spec-status.py` / `lint-brief-coverage.py`. No framework; no
third-party dependency.

### Design decisions
- **One script, four layers (find → build → resolve → classify), not a package.**
  Mirrors the precedent lints; keeps projection + the no-cross-skill-import rule
  simple. Alternative (a shared traceability library imported by both loops)
  rejected — couples independently-projected trees. Traces to: all ACs · none.
- **Identity is a stable, location-independent id by convention, never a path.**
  Slug for most nodes, `kind:namespace/name` for a component, `contract@version`
  for a contract — reusing the existing conventions; this is what lets an edge
  cross a repo boundary. Traces to: AC2, AC5 · none.
- **Three endpoint states, not two** (the cross-repo correctness core): an edge
  endpoint is *local* (resolvable in this root), *satisfied-by-reference* (a
  well-formed pointer — a stable-id resolving to an external target, snapshot
  optional), or *unresolvable*. A satisfied-by-reference endpoint is connected, not
  a defect. **Pinning is an orthogonal `pinned`/`unpinned` flag** on that state
  (unpinned = informational soft warning, never fatal), not a membership condition.
  Traces to: AC5, AC9, AC11 · none.
- **Reuse the value-stream cross-repo mechanism, never a parallel one** — the
  rollup row schema + `contract@version` + courier snapshot + `unknown /
  not-yet-catalogued`. Traces to: AC2, AC11, AC13, AC14 · none.
- **Defect discriminator, three-way:** absent pointer = orphan (informational; exit
  1 under `--strict`); pointer to a missing *local* target or malformed = dangling
  (exit 1 always); well-formed external pointer = satisfied-by-reference. Computed
  from distinct states, so one break is never two classes. Traces to: AC6, AC9,
  AC10, AC12 · none.
- **Sidecar/rollup authoritative when present; derive-from-artifacts when absent.**
  Drift is warn-only until the matrix schema is pinned (deferred:
  sidecar-drift-hard-fail). Traces to: AC14 · none.

### Data & schema
- **Node registry** (in-source constant): per node-type, its realization +
  stable-id rule. File-backed — `screen`→`screens/<name>.md`+`type: screen-brief`;
  `contract`→`contracts/<type>/*` (id `contract@version`); `spec`→`docs/specs/*/spec.md`
  via `Status:`; `component`→`packages/<c>/` dir or repo (id `kind:namespace/name`).
  Container-embedded (extractor) — `outcome`/`opportunity`/`capability`→ the intent
  ladder `docs/product/intents/*.md`; `action`→ journey-map entries; `service`→
  service-blueprint entries. **The intent-ladder extractor is reconciled, not
  invented:** per note 04 the ladder tags `outcome+opportunity` *kinds* across
  `vision/strategy/capability/feature` *levels*, so `capability` is a level while
  `outcome`/`opportunity` are kinds; the extractor maps `outcome`→ declared
  outcome(s) (the traceability root), `opportunity`→ opportunity-tree rungs,
  `capability`→ a capability-level intent, pinned against the
  `frame-intent`/`decompose-intent` format when it lands, degrading until then.
- **Edge registry** (in-source constant): per adjacent pair, the pointer-holder
  artifact + field + direction — `spec→(discovery/brief)` via `Discovery:`/`Brief:`/
  `parent-intent:` (back-link); `spec→component` via `Component:` (forward,
  reverse-indexed); `spec→contract` via `Contract:`/`contract@version`;
  `service→screen`/`screen→action` via blueprint/journey structure. Each field's
  **recognizer matches the rendered on-disk label, not a raw key** — the brief
  renders `**Parent intent:**` (capitalized, spaced; not literal `parent-intent:`),
  specs render `**Status:**`/`**Brief:**`/`**Discovery:**` — matched
  case-insensitively, the `lint-brief-coverage.py` `_BRIEF_RE = \*\*Brief:\*\*`
  precedent. Out-of-scope pointer fields find nothing until they exist.
- **Edge set:** an in-memory directed graph keyed by **stable-id**
  `node-id → producer-node-id` + the reverse consumer index. Each edge carries its
  endpoint state (local / satisfied-by-reference / unresolvable) and, for a
  reference, its `pinned`/`unpinned` flag (and the pinned version when present) +
  snapshot-present flag.
- **Cross-repo join:** a present value-stream **rollup** (row schema above) or
  **sidecar** supplies edges whose endpoints live in other repos; a reference whose
  id+version appears there resolves satisfied-by-reference, else unresolvable →
  `unknown / not-yet-catalogued`.
- **Sidecar `traceability.json`** (read-only, optional): the materialized edge set
  at `<discovery-base>/<initiative>/_state/traceability.json` (note 08), discovered
  by the same three-tier rule (config → default `docs/discovery/` → glob
  `_state/traceability.json`), never a hardcoded `_state/` path. Schema is `core`
  doctrine (RFC-0048 D7), **not pinned yet** — recognize a versioned schema when it
  lands; warn until then.
  Traces to: AC1, AC2, AC4, AC5, AC11, AC14 · none.

### Interfaces & contracts
- **CLI:** `lint-traceability.py [--root DIR] [--strict]`. `--root` defaults to
  git-toplevel-or-script-parent (`lint-brief-coverage.py` `_repo_root`). The same
  binary serves both **postures** — run in a module repo it checks the local
  sub-chain + validates outbound pointers are well-formed; run in the meta-repo it
  joins component rows through the rollup. The posture is inferred from what the
  root contains (a rollup/sidecar ⇒ federated), not a flag.
- **Exit codes:** `0` clean/reported (orphans informational; unresolvable-cross-repo
  and drift never fatal); `1` defect — dangling edge or cycle (always), or
  structural orphan (under `--strict`).
- **Output:** stdout = per-node report (incl. endpoint state per edge) + one-line
  summary; stderr = hard violations + count. Mirrors the precedent lints.
  Traces to: AC12, AC13, AC14, AC17 · none.

### State & control flow
- **Three-tier base resolution per layer**, lazy: (1) `agentbundle-layout.toml`
  (`./` then `~/.agentbundle/`); (2) designed default; (3) glob for the recognizer
  marker. **Base ambiguity** → reported; **instance enumeration** within a base is
  expected-many, never an ambiguity error. Traces to: AC3 · none.
- **Endpoint resolution pass:** for each edge, classify the target — present in the
  local node set ⇒ local; absent locally but a well-formed reference (stable-id,
  optionally pinned) resolvable via rollup/sidecar/snapshot ⇒ satisfied-by-reference
  (pinning recorded as an orthogonal `pinned`/`unpinned` flag); else ⇒ unresolvable
  (sub-classified broken vs unverifiable-cross-repo). Traces to: AC5, AC11 · none.
- **Classification pass:** for each present node, check up/down edges with terminal
  exemption (root needs no up, leaf needs no down) and **globally-unpopulated-layer
  skip** (nearest populated adjacent layer only when the intervening layer is empty
  everywhere; skipping a populated layer is an orphan). A producer walk guarded by a
  visited-set (cycle ⇒ hard violation, no recursion past a repeat). Traces to:
  AC6, AC7, AC8, AC9, AC10 · none.

### Failure, edge cases & resilience
- **No chain artifacts** → exit 0, silent. **Partial chain** → only real orphans.
- **Cross-repo reference, target not visible** → satisfied-by-reference if
  resolvable via rollup/sidecar (pinned or unpinned; unpinned flagged
  informational); else `unknown / not-yet-catalogued` (informational).
- **Malformed frontmatter / unreadable file** → skip with a note, never crash.
- **Self / cyclic pointer** → hard violation via visited-set; walk terminates.
- **Absent sidecar/rollup** → derive locally (standalone); **present but
  unrecognized schema** → warn, never hard-fail.
- **Python absent** → the skill checklist no-ops (precedent posture).
  Traces to: AC5, AC8, AC9, AC10, AC11, AC14, AC15 · none.

### Quality attributes (NFRs)
- **No hardcoded path** is the load-bearing NFR — AC1/AC2 ("no hardcoded artifact
  path; identity by stable-id") + a self-test grep over the script. Traces to:
  AC1, AC2 · none.

## Tasks

### T1: node-and-edge registry + stable-id scheme + three-tier base resolution

**Depends on:** none

**Tests:**
- Config / default / marker-discovery fixtures each resolve the same layer base;
  base ambiguity reported; instance multiplicity enumerated, not flagged (AC3).
- Each node-type yields its stable-id (slug / `kind:namespace/name` /
  `contract@version`), never a path (AC2).
- A node-type whose markers are absent → "layer unpopulated", not an error (AC8).

**Approach:**
- Define the node registry (realization + stable-id rule) and the adjacent-pair
  edge registry (pointer-holder + field + direction).
- `resolve_base(layer, root)` running tier 1→2→3, separating base resolution from
  instance enumeration; read `agentbundle-layout.toml` with `tomllib`, no-op absent.

**Done when:** resolution + stable-id tests green; no literal artifact path in
source (self-test grep passes).

### T2: node recognition (file-backed + container-embedded extraction)

**Depends on:** T1

**Tests:**
- Fixture intent ladder yields `outcome`/`opportunity`/`capability`; journey yields
  `action`; blueprint yields `service` (AC1).
- Fixture `screen`/`spec`/`contract`/`component` recognized file-backed (AC1).
- A brief authored from the **real** `briefs/_template.md` (rendered
  `**Parent intent:**` label) is recognized — guards the rendered-label-vs-raw-key
  recognizer (AC2, AC4).

**Approach:**
- File-backed: glob + read the recognizer marker (rendered `**Label:**` form,
  case-insensitive). Container-embedded: parse the container, extract typed entries
  (ladder rungs by kind/level; journey/blueprint structured entries).

**Done when:** every node-type's instances are enumerated from the right fixture.

### T3: edge-set builder from conventional pointers

**Depends on:** T2

**Tests:**
- A full-chain fixture builds the complete expected edge set, incl. the
  reverse-indexed `spec→component` edge (AC4).
- A pointer to a present producer yields one up-edge; the reverse index yields the
  down-edge (AC4).

**Approach:**
- For each adjacent pair, read the pointer from its registered holder (back-link or
  forward declaration), building the stable-id-keyed graph + reverse index.

**Done when:** edge-set tests green for a full and a partial chain.

### T4: cross-repo endpoint resolution + rollup/sidecar join + postures

**Depends on:** T3

**Tests:**
- A well-formed cross-repo reference resolves **satisfied-by-reference**, never
  dangling — both `pinned` (with a version) and `unpinned` (stable-id only, flagged
  informational, never fatal) (AC5).
- An unresolvable cross-repo target → `unknown / not-yet-catalogued`,
  informational, never fatal, never silently satisfied (AC11).
- A meta-repo posture joins component rows through the rollup; a module-repo posture
  validates outbound pointers are well-formed (carry a stable-id), reporting an
  unpinned outbound pointer informationally (AC13).
- A recognized sidecar/rollup supplies the authoritative edge set; absent → derive
  locally (AC14).

**Approach:**
- Classify each endpoint local / satisfied-by-reference / unresolvable; resolve
  references via a present rollup (row schema) or sidecar; infer posture from root
  contents.

**Done when:** the cross-repo fixtures (pinned / unpinned / unresolvable; both
postures) produce the expected states and exit codes.

### T5: structural-orphan classifier (backward/forward, terminal, layer-skip)

**Depends on:** T4

**Tests:**
- Backward (up) orphan (no producer, non-root) named with type + direction (AC6).
- Forward (down) orphan (no consumer, non-leaf) named with type + direction (AC6).
- Root `outcome` never a backward orphan; leaf `component` never a forward orphan
  (AC7).
- A node crossing a globally-unpopulated layer not flagged; a node skipping a
  populated layer **is** flagged (AC8).

**Approach:**
- Walk nodes; check up/down edges with terminal exemption + globally-unpopulated
  skip; satisfied-by-reference counts as connected. Emit informational orphan lines.

**Done when:** the classifier reproduces the exact orphan list for every fixture.

### T6: dangling-edge + cycle detection

**Depends on:** T3

**Tests:**
- A pointer to a missing **local** target (or malformed, not a well-formed
  reference) → dangling, exit 1 in every mode (AC9).
- A self-edge (A→A) and a cycle (A→B→A) → hard violation, no non-termination, exit
  1 (AC10).

**Approach:**
- Flag any pointer target that is neither local nor satisfied-by-reference as
  dangling; guard the producer walk with a visited-set.

**Done when:** dangling and cycle fixtures exit 1.

### T7: CLI, exit-code contract, and `--strict`

**Depends on:** T5, T6

**Tests:**
- Default: orphans → exit 0 (informational); `--strict`: any orphan → exit 1 (AC12).
- Dangling/cycle → exit 1 regardless of `--strict`; unresolvable-cross-repo + drift
  → never fatal (AC12).
- Empty workspace → exit 0, no diagnostic (AC15).
- No semantic finding ever emitted (AC16) — assert the report vocabulary is only
  structural/dangling/cycle/drift/endpoint-state terms.
- **Output shape + stdlib-only (AC17):** `--root`/`--strict` accepted; report on
  stdout, hard violations on stderr, a one-line summary; the script's import surface
  is stdlib-only (a test asserts no third-party import / no new dependency).

**Approach:**
- `argparse` for `--root`/`--strict`; `_repo_root` helper; assemble stdout report +
  stderr violations + one-line summary; compute exit code from the defect tiers.

**Done when:** the exit-code matrix is green across all fixtures.

### T8: projection + self-test + no-op verification

**Depends on:** T7

**Tests:**
- `make build-self` projects `lint-traceability.py` to every adapter's
  `work-loop/scripts/` (AC18).
- Running the lint against this repo no-ops cleanly (manual verification, AC15).

**Approach:**
- Place the script under `packs/core/.apm/skills/work-loop/scripts/`; run
  `make build-self`; confirm projection (the `lint-spec-status.py` parity check).
- Add the self-test (no-hardcoded-path grep + the fixture suite) to the same CI
  surface the precedent lints' self-tests use.
- Add a `docs/product/changelog.md` `[Unreleased]` entry and bump `core` if a
  user-visible capability lands (surface the release decision).

**Done when:** projection parity holds and the repo run is clean.

## Rollout

- **Delivery:** additive — a new script + its self-test; no flag-day, no migration,
  fully reversible (delete the script). No data migration, no published interface.
- **Infrastructure:** none.
- **External-system integration:** none new — the lint *reuses* the existing
  value-stream cross-repo convention (rollup, `contract@version` + courier snapshot,
  `parent-intent:`). The `Discovery:` header, frontmatter `type:` markers, container
  artifacts, and the sidecar schema it reads are produced/pinned by sibling efforts;
  until those land the lint degrades gracefully (unpopulated layers, derive locally,
  warn on drift, `unknown / not-yet-catalogued` for cross-repo gaps), so it ships
  and is useful standalone today over the brief↔spec edge it already understands.
- **Deployment sequencing:** none — independent of the sibling children; it grows
  more complete as their markers, the rollup, and the sidecar schema arrive, but
  never blocks on them.

## Risks

- **Marker / pointer heterogeneity outruns the registry.** A producing skill stamps
  a marker the registry doesn't recognize → that layer reads as unpopulated.
  Mitigation: the registry is the single declarative table; altering a node-type or
  pointer field goes through the *Ask first* boundary.
- **Cross-repo reference mis-classified as dangling** (the headline false positive).
  Mitigation: the three-state resolution + reuse of the pinned-reference convention;
  a well-formed external pointer is satisfied-by-reference, an unresolvable one is
  an honest `unknown / not-yet-catalogued`, never a hard orphan; both are
  fixture-asserted.
- **`--strict` over-fires during in-progress discovery.** Mitigation: default mode
  is informational; strict is reserved for the convergence gate (G2) and CI, where
  closure is the requirement (RFC-0048 O6).
- **Container-embedded extraction is format-coupled** to sibling-authored output.
  Mitigation: extract by stable marker (kind/level / `type:`), degrade to "layer
  unpopulated" on an unrecognized shape, never crash; one extractor per registry row.
- **Sidecar/rollup drift false positives** if the matrix schema (not pinned here)
  diverges. Mitigation: drift warn-only until pinned (deferred:
  sidecar-drift-hard-fail); cross-check skipped when absent/unrecognized; artifacts
  stay the standalone source.
- **Rename has no redirect** (Backstage / OSLC finding) → a renamed stable-id
  orphans inbound refs. Mitigation: stable-ids are *Ask first* to change; an
  optional `moved-to` forwarding convention is logged as a future refinement
  (`notes/cross-repo-traceability-research.md`), not v1 scope.

## Changelog

- 2026-06-25: initial plan.
- 2026-06-25: post-spec-mode-review revision — modeled the four container-embedded
  node-types distinctly from the file-backed four; split node/edge registries with
  per-pair pointer holders (incl. reverse-indexed `spec→component`); added the
  dangling-vs-orphan discriminator + cycle guard; scoped layer-skip to
  globally-unpopulated; separated tier-3 base resolution from instance enumeration;
  sidecar authoritative-when-present, drift warn-only. (Findings 1–8, first pass.)
- 2026-06-25: second-pass review fixes — intent-ladder extractor as a kind-vs-level
  reconciliation; sidecar three-tier discovery + `_state/` path; the nine-node chain
  follows **note 08's `…spec→component` terminus** (component is the leaf; note 02's
  `code` is the component's content); removed the mis-placed AC11 deferral marker.
  (Findings 1–4.)
- 2026-06-25: **cross-repo revision** (user direction: the loops span repos —
  `work-loop` per-module, `discovery-loop`/integration-loop same-or-cross-repo).
  Dropped the single-monorepo assumption; made edges **by-convention stable-ids**
  (slug / `kind:namespace/name` / `contract@version`) resolvable in **three endpoint
  states** (local / satisfied-by-reference / unresolvable); added the cross-repo
  resolution + rollup/sidecar-join task (T4) and the two run postures; reused the
  value-stream mechanism (ADR-0022) rather than inventing one; grounded the design
  in wide prior-art research (`notes/cross-repo-traceability-research.md`). Renumbered
  to 18 ACs / 8 tasks.
