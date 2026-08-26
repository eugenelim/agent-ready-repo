# Plan: Portable Agent Plugin projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `ARCHITECTURE.md`; `docs/architecture/overview.md`; `docs/rfc/0092-first-class-distribution-routes.md`; `docs/specs/distribution-route-contract/{spec,plan}.md`; explicit APM and Claude projectors in `packages/agentbundle/agentbundle/build/main.py`; route construction tests in `packages/agentbundle/tests/build_pipeline/test_distribution_route_{contract,resolution,golden}.py`. Named deviation: this is the third deliberately hand-written route before Phase 2 extracts a registry, and it replaces the existing routes' partial link posture with confined regular-file reads for the new route only.

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document may change while its status is `Drafting` or `Executing`.
> Substantial approach changes are recorded in the changelog.

## Approach

Land the portable route in six dependency-ordered layers. First pin the
external 1.0.0 contract as an offline, licensed bundle. Then extend the existing
closed route contract and explicit resolver with a third named recipe. Add pure
admission and manifest derivation before any filesystem writes, project skills
through confined regular-file reads, add a separately governed extension
namespace registry, and finish by making the route part of the real default
build with complete-tree determinism, packaged-data parity, maintainer
documentation, and package version updates. Keep the route-specific dispatch
explicit in `build/main.py`; the generic registry remains Phase 2 work.

## Constraints

- RFC-0092 fixes the route/adapter separation, portable 1.0.0 target, manifest
  field mapping, AC3 roster baseline, extension allocation requirement, offline
  validation, and Phase 2 registry deferral.
- ADR-0090 keeps distribution routes sibling to runtime adapters; no portable
  behavior is added to `adapter.toml`.
- ADR-0021 keeps `pack.toml` the rich canonical source and every generated
  manifest a one-way projection.
- ADR-0072 supplies the precedent for mirroring an upstream schema while
  treating the normative external specification and real clients as final
  authorities.
- `packages/AGENTS.md` requires UTF-8 text I/O, `build_pipeline` test paths,
  projection-layout coverage across shipped adapters, and paired package
  version updates for non-cosmetic changes.
- The repository adds no dependency and performs no network access in the
  normal build. Contract acquisition is a maintainer/update operation, not a
  build step.
- Existing APM and Claude route output is a frozen regression surface; the new
  filesystem posture is applied to `agent-plugin` without silently changing
  those shipped bytes.

## Planning record

**Assumption trio**

- **Files:** route contracts and vendored contract data under `contracts/`;
  byte-identical CLI data and a new recipe under
  `packages/agentbundle/agentbundle/`; explicit route logic in
  `build/main.py`; build-pipeline/unit/integration fixtures; package versions;
  and maintainer/reference documentation.
- **Done evidence:** exact upstream blob/provenance checks, route/schema and
  packaged-data parity, negative admission/security tests, deterministic
  complete-tree fixtures, unchanged APM/Claude goldens, the full agentbundle
  suite, build/lint gates, and a real consecutive-build smoke.
- **Not changing:** canonical MCP, runtime adapters/direct install, generic
  registry extraction, marketplace publication, seeds/adaptation, runtime
  verification, or native Codex/Kiro/Copilot behavior.

**Declined patterns**

- Generic projector registry — deferred by RFC-0092 until three route
  implementations provide evidence.
- Opaque metadata passthrough — it would make unreviewed vendor fields an
  authoring API and defeat closed portable validation.
- Network schema resolution — it makes ordinary builds non-reproducible and
  unavailable offline.
- `shutil.copytree(..., symlinks=True)` reuse — it preserves unsafe entry
  kinds that this route's publication boundary must reject.
- Name rewriting — it hides identity collisions and breaks reversibility.
- Shared safe-copy abstraction for all routes — changing shipped APM/Claude
  output posture is outside this slice; extract only after a second safe-copy
  consumer exists.

**Resolve-vs-surface disposition**

- Resolved from repository authority: route ownership, slice boundary,
  metadata mapping, first-maintainer policy, portable component inventory,
  default output path, and existing-route invariance.
- Resolved from the upstream oracle: published 1.0.0 layout, schema identifiers,
  exact schema bytes/blob identities, and Apache-2.0 schema licence.
- Resolved by user: catalogue-maintainer outcome and the “schemas now, MCP
  behavior in Phase 1B” boundary.
- Surface later only if implementation evidence contradicts the AC3
  inventory, an extension requires activation rather than reservation, or a
  required behavior cannot be achieved without a new dependency/authoring
  surface.

## Construction tests

**Integration tests**

- Build the complete catalogue twice into independent temporary roots and
  compare a canonical inventory of relative path, SHA-256, and executable bit
  for `agent-plugins/`.
- Run the normal build with network access unavailable and validate every
  emitted `plugin.json` against the vendored schema.
- Compare complete APM and Claude-plugin golden trees before and after the new
  route is enabled.
- Build/package the CLI and assert every new contract, schema, licence,
  provenance file, and recipe is present and byte-identical to its authored
  source.

**Manual verification**

- Run the real catalogue build; record one eligible artifact's root inventory
  and successful schema validation, one ineligible pack's complete named
  exclusion, and equal consecutive tree digests.
- No client runtime is exercised and no support claim is promoted; Phase 1A is
  documentation-verified.

## Design (LLD)

### Design decisions

- Keep `agent-plugin` as an explicit third branch in the Phase 0 resolver and
  per-pack runner. This satisfies RFC-0092's third-real-route prerequisite
  without pre-implementing Phase 2.
- Store exact upstream schema bytes and their licence/provenance as one
  versioned vendor bundle under
  `contracts/vendor/agent-plugins/1.0.0/`; mirror that bundle byte-for-byte
  into CLI data.
- Derive a fresh portable manifest from `pack.toml`; do not reuse the
  Claude-derived manifest because it admits route-only fields.
- Allocate extension namespaces in a dedicated closed contract rather than
  adding a seventh distribution-route concern or treating extension content as
  a canonical primitive.
- Preflight every admitted pack and extension before deleting or writing the
  `agent-plugins` route output. Fresh files are written from confined reads;
  a post-write tree audit closes output-side link and kind assumptions.

Traces to: AC1–AC12 · `contracts/distribution-routes.*` ·
`contracts/agent-plugin-extension-namespaces.*`.

### Interfaces & contracts

- `contracts/distribution-routes.toml` gains the explicit
  `route.agent-plugin` declaration. Its schema remains closed and requires
  all three concrete routes.
- `contracts/agent-plugin-extension-namespaces.toml` maps a reverse-domain
  namespace to `owner`, `state = reserved | active`, and, for active
  entries, a repository-relative versioned JSON Schema. Its schema rejects
  duplicate/case-colliding identities, unsafe schema paths, missing owners, and
  active entries without schemas.
- `pack.metadata.agent-plugin.extensions.<namespace>` is the existing open
  metadata escape hatch used for manifest extension objects. A same-named
  pack-root directory is the optional file-extension source; declaring an
  empty object permits a file-only extension without creating another source
  field.
- The upstream `plugin.schema.json` is the emitted-manifest contract.
  `mcp.schema.json` is vendored and packaged but has no Phase 1A producer or
  consumer beyond provenance/parity checks.

Traces to: AC1, AC2, AC4, AC7, AC8 · contract paths named above.

### Failure, edge cases & resilience

- Admission inventories every present canonical source path whose route
  capability is `dropped`; a skipped pack receives one stable diagnostic with
  the complete sorted primitive list.
- Manifest/name/extension validation and the full source-tree safety preflight
  run before route-output mutation. Pack-authored failures remain `ValueError`
  refusals with pack and route context; unexpected I/O remains a runtime error
  with the pack named.
- Confined traversal accepts only directories and single-link regular files,
  never follows links, reads through the no-follow helper, and rechecks source
  identity while opening. Output paths are assembled from validated identities,
  confined under the selected output root, and audited after write.
- The route output is rebuilt from an empty route subtree after successful
  preflight, so removed source files cannot survive as stale artifacts.

Traces to: AC3, AC5, AC8–AC10.

### Quality attributes (NFRs)

- **Determinism:** sorted pack/skill/namespace/file traversal; stable manifest
  key order; LF JSON; source bytes and executable bits preserved; inventory
  equality across consecutive builds.
- **Security:** no network build, no link-like/hard-linked/non-regular source or
  output, no unallocated extension content, no silent identity normalization,
  and pre-write plus post-write validation.
- **Compatibility:** existing route golden trees and direct-install tests stay
  unchanged; the route is additive.
- **Maintainability:** no dependency or generic registry; external bytes,
  provenance, namespace allocation, projection rules, and tests each have one
  canonical home.

Traces to: AC1, AC8–AC15.

### Dependencies & integration

- Upstream Agent Plugins 1.0.0 is a vendored authoring/update dependency only.
  AC1 and the vendored `PROVENANCE.md` are the sole source of truth for the
  acquired commit, schema blob identities, source paths, and licence.
- Phase 0's resolver, recipe parser, contract bundling, JSON Schema validator,
  pack discovery, and golden-fixture machinery are reused.
- Phase 1B consumes the vendored MCP schema and depends on this route, but no
  Phase 1B code or source model enters these tasks.

Traces to: AC1–AC3, AC11–AC15.

## Tasks

### T1: The portable 1.0.0 contract bundle is immutable, licensed, offline, and packaged

**Depends on:** none

**Touches:** `contracts/vendor/agent-plugins/1.0.0/**`,
`contracts/README.md`, `packages/agentbundle/agentbundle/_data/**`,
`packages/agentbundle/tests/build_pipeline/test_distribution_route_contract.py`

**Verification mode:** goal-based contract identity, mutation, and packaged-data
parity checks.

**Construction-test artifact:** no stub (goal-based) —
`packages/agentbundle/tests/build_pipeline/test_distribution_route_contract.py::test_agent_plugin_vendor_bundle_matches_upstream_identity`.

**Tests:**

- Goal-based: both vendored schema bytes resolve to the immutable upstream Git
  blob identities in AC1; mutation of either byte fails.
- Goal-based: licence and provenance name the upstream repository, immutable
  commit, source paths, blob identities, canonical schema IDs, and Apache-2.0
  software licence.
- Goal-based: authored/vendor files and bundled CLI data are byte-identical,
  discoverable by the packaged-data loader, and require no network.

**Approach:**

- Add the exact upstream schema bytes plus `LICENSE.md` and a repository-owned
  `PROVENANCE.md` to the versioned vendor directory.
- Add byte-identical package-data copies and extend the existing public
  contract/parity inventory without changing schema contents.
- Record the vendor bundle and authority relationship in `contracts/README.md`.

**Done when:** all AC1 mutation/parity tests pass with outbound network disabled.

### T2: The closed route contract and recipe resolve one explicit agent-plugin route

**Depends on:** T1

**Touches:** `contracts/distribution-routes.*`,
`packages/agentbundle/agentbundle/_data/distribution-routes.*`,
`packages/agentbundle/agentbundle/build/recipes/per-pack-agent-plugin.toml`,
`packages/agentbundle/agentbundle/build/main.py`,
`packages/agentbundle/tests/build_pipeline/test_distribution_route_*.py`

**Verification mode:** TDD for the closed route/recipe contract plus goal-based
source-to-package parity.

**Construction-test artifact:** `stub: true` —
`packages/agentbundle/tests/build_pipeline/test_distribution_route_contract.py::test_agent_plugin_route_contract_is_closed_and_resolvable` must be materialized, collected, and red at the start of T2 before the Approach begins.

**Tests:**

- TDD: contract/schema tests accept exactly the AC2 declaration and reject a
  missing route, wrong output, adapter/marketplace/lifecycle projector, or
  incorrect capability.
- TDD: recipe resolution accepts `agent-plugin` and still rejects undeclared
  names, mismatched output, and attempts to synthesize a generic registration
  surface.
- Goal-based: the authored and bundled route contracts remain byte-identical;
  current APM/Claude route-resolution tests remain green.

**Approach:**

- Extend the closed schema and TOML with the third concrete route and bump only
  the route-contract version required by that shape change.
- Add the per-pack recipe and include it in the normal default recipe set.
- Extend the existing explicit resolver maps/branches; do not introduce dynamic
  registration.

**Done when:** AC2 is pinned by contract and resolver tests with no change in
existing route resolutions.

### T3: Admission and manifest derivation produce only conforming portable identities

**Depends on:** T2

**Touches:** `packages/agentbundle/agentbundle/build/main.py`,
`packages/agentbundle/tests/{unit,build_pipeline}/**/*agent_plugin*.py`,
`packages/agentbundle/tests/build_pipeline/fixtures/**`

**Verification mode:** TDD for admission, manifest derivation, strict JSON, and
diagnostics plus a goal-based corpus-roster check.

**Construction-test artifact:** `stub: true` —
`packages/agentbundle/tests/build_pipeline/test_agent_plugin_projection.py::test_agent_plugin_admission_and_manifest_contract` must be materialized, collected, and red at the start of T3 before the Approach begins.

**Tests:**

- TDD: an inventory fixture covers skills-only eligibility, each dropped
  primitive alone, multiple dropped primitives, empty primitive directories,
  and the exact sorted diagnostic required by AC3.
- TDD: portable manifest mapping covers every AC4 source field, emit-only-when-
  present behavior, first-maintainer name-only author selection with every
  email/URL/username/account field omitted, forbidden Claude-only fields,
  invalid JSON-compatible metadata including NaN and positive/negative
  infinity, strict JSON serialization, and pre/post schema validation.
- TDD: valid edge identities and every AC5 invalid-name class are accepted or
  refused without normalization.
- TDD/integration: symlink, supported reparse/junction, hard-link, non-regular,
  over-1-MiB, and source-replaced `pack.toml` fixtures fail through the confined
  single-link read seam before any route output mutation.
- TDD: malformed metadata and identity refusals expose only the pack, route,
  component, validated relative path when applicable, and stable error class;
  absolute host paths, raw values, and schema payloads never appear. Identity
  and path fixtures containing controls, ANSI escapes, newline, bidi,
  zero-width, and non-ASCII code points are rendered as stable ASCII JSON
  strings without changing accepted artifact values.
- Goal-based: the current corpus resolves to the exact eligible and excluded
  membership named by the AC3 roster and a checked fixture.

**Approach:**

- Add pure route-specific inventory and manifest-derivation helpers next to the
  existing resolver/projectors.
- Acquire and parse canonical `pack.toml` bytes only through the blessed
  confined single-link regular-file reader with the AC9 size and replacement
  checks, completing preflight before route output mutation.
- Compute dropped-primitive presence from canonical contract source paths,
  excluding non-canonical seeds/docs/tests from admission.
- Build the manifest in portable schema order and validate it in memory before
  any destination write.

**Done when:** AC3–AC5 and the manifest-input portion of AC9 are green and no
agent-plugin filesystem write is needed to test admission or manifest mapping.

### T4: Skills project through a confined, deterministic package writer

**Depends on:** T3

**Touches:** `packages/agentbundle/agentbundle/build/main.py`,
`packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py`,
`packages/agentbundle/tests/build_pipeline/**/*agent_plugin*.py`

**Verification mode:** TDD for the route-local safe writer plus integration
fixtures for preflight, stale-output cleanup, and completed-tree audit.

**Construction-test artifact:** `stub: true` —
`packages/agentbundle/tests/build_pipeline/test_agent_plugin_projection.py::test_agent_plugin_projection_refuses_unsafe_or_oversize_skill_trees` must be materialized, collected, and red at the start of T4 before the Approach begins.

**Tests:**

- TDD: nested skills preserve paths, bytes, and executable bits in stable order;
  absent/empty skills are handled consistently with admission.
- TDD/integration: symlink, supported reparse/junction, hard-link, FIFO/device,
  lexical traversal, resolved escape, source replacement, and output collision
  fixtures fail before route output mutation.
- TDD/integration: a file over 2 MiB, a 4,097th combined regular file, a
  combined 32 MiB plus one byte, and a relative path at depth 21 each fail
  before route output mutation; boundary-equal fixtures pass.
- TDD: unsafe and over-limit diagnostics expose only sanitized route context
  and ASCII JSON-escaped validated relative paths, never absolute paths or
  source values; control/ANSI/newline/bidi/zero-width fixtures cannot forge a
  second diagnostic line.
- Integration: a failed preflight leaves a sentinel prior route tree
  byte-identical; a successful rebuild removes stale files and the post-write
  inventory contains only confined directories and single-link regular files.

**Approach:**

- Enumerate files with the blessed confined helpers and read each file through
  the no-follow, single-link seam; preserve only the source executable bit on
  fresh regular-file outputs.
- Preflight every admitted pack before clearing `agent-plugins/`, write paths
  from validated identities only, and audit the completed tree.
- Keep this writer route-local until another safe-copy consumer warrants
  extraction.

**Done when:** AC6, AC8, and the skills portion of AC9 pass on the supported
platform fixture matrix.

### T5: Extension namespaces are allocated, validated, collision-safe, and optional

**Depends on:** T4

**Touches:** `contracts/agent-plugin-extension-namespaces.*`,
`packages/agentbundle/agentbundle/_data/agent-plugin-extension-namespaces.*`,
`packages/agentbundle/agentbundle/build/main.py`,
`packages/agentbundle/tests/build_pipeline/**/*agent_plugin*.py`

**Verification mode:** TDD for allocation, strict manifest data, bounded file
projection, and collision refusal plus goal-based packaged-contract parity.

**Construction-test artifact:** `stub: true` —
`packages/agentbundle/tests/build_pipeline/test_agent_plugin_projection.py::test_agent_plugin_extensions_require_active_valid_allocations` must be materialized, collected, and red at the start of T5 before the Approach begins.

**Tests:**

- TDD: the registry accepts the two reserved allocations, rejects invalid
  reverse-domain names/case collisions/duplicate owners/unsafe schema paths,
  and requires a versioned schema for every active namespace.
- TDD: an injected active fixture namespace projects manifest data and an
  optional same-named root directory; reserved, undeclared, malformed,
  schema-invalid (including non-finite numeric data), case-colliding,
  destination-colliding, unsafe, and over-limit file variants refuse before
  output mutation with sanitized diagnostics.
- TDD: combined extension manifest data at each AC8 limit passes, while 8 MiB
  plus one serialized byte, depth 21, a 4,097th object member, a key/string over
  64 KiB, and a 257th array item fail before schema validation and output
  mutation.
- TDD: namespace, identity, and relative-path diagnostics use stable ASCII
  JSON-string escaping for control/ANSI/newline/bidi/zero-width/non-ASCII input
  without normalizing projected values.
- Goal-based: registry/schema source and packaged copies remain byte-identical;
  the current corpus emits no extension content.

**Approach:**

- Add the closed allocation registry and schema with an `x-spec` pointer back
  to this spec; reserve the RFC-owned Kiro and Copilot names without activating
  them.
- Parse only `pack.metadata.agent-plugin.extensions`, require object values,
  and treat a declared namespace's same-named pack-root directory as its sole
  file source.
- Walk extension manifest data against the AC8 byte/depth/member/string/array
  limits, serialize it strictly, then validate against the registry-named
  schema; reuse T4's safe writer for directory content.

**Done when:** AC7–AC8 pass and an inactive/reserved namespace cannot enter an
artifact.

### T6: The default build, packaged CLI, documentation, and release gates prove the maintainer journey

**Depends on:** T5

**Touches:** `packages/agentbundle/agentbundle/build/main.py`,
`packages/agentbundle/{pyproject.toml,agentbundle/version.py,README.md}`,
`packages/agentbundle/CHANGELOG.md`, `docs/product/changelog.md`,
`contracts/README.md`, `guides/_shared/explanation/install-routes.md`,
`packages/agentbundle/tests/**`, build/golden fixtures,
`docs/specs/portable-agent-plugin-projection/notes/manual-qa.md`

**Verification mode:** goal-based integration/release closure plus manual QA of
the real built artifact.

**Construction-test artifact:** no stub (goal-based/manual QA) —
`packages/agentbundle/tests/build_pipeline/test_agent_plugin_projection.py::test_default_build_emits_complete_agent_plugin_roster` and
`docs/specs/portable-agent-plugin-projection/notes/manual-qa.md` are the
executable and observed evidence.

**Tests:**

- Integration: independent consecutive default builds produce identical
  agent-plugin inventories and valid manifests for the AC3 eligible roster,
  while exact complete diagnostics cover the AC3 excluded roster.
- Integration: APM and Claude complete-tree goldens and direct-install suites
  remain unchanged; packaged-data, recipe, version, and build-self parity gates
  pass.
- Goal-based: `pyproject.toml`, `version.py`, the package changelog, and the
  product changelog describe the same released AgentBundle version and Phase 1A
  change; a missing or stale changelog entry fails the release evidence.
- Manual QA: run the real build, validate one emitted root manifest against the
  vendored schema, inspect its skills tree, capture one excluded diagnostic,
  and compare consecutive digests as required by AC14. Record the date,
  worktree/ref, exact commands and exit status, observed artifact path and
  inventory, schema-validation result, sanitized exclusion diagnostic,
  consecutive digests, limitations/skips, and explicit confirmation that no
  client runtime or publication path was exercised in
  `docs/specs/portable-agent-plugin-projection/notes/manual-qa.md`.
- Goal-based: documentation contains the command, layout, admission rule,
  offline contract, support posture, and explicit Phase 1A exclusions.

**Approach:**

- Finish the default-build integration and checked complete-tree fixtures.
- Update maintainer-facing route documentation without presenting the artifact
  as a direct-install route or claiming a client/runtime has been exercised.
- Bump `pyproject.toml` and `version.py` together, add matching entries to both
  changelogs, run build-self/parity, and execute the full gate sequence.

**Done when:** AC9–AC15 pass, including the recorded real-artifact smoke and
matching package/product changelog entries for the version bump.

## Rollout

- **Delivery:** additive default-build output. Rollback removes the explicit
  recipe/route declaration and generated `agent-plugins/` subtree while
  leaving canonical pack sources, APM, Claude, and direct install untouched.
- **Infrastructure:** none.
- **External-system integration:** none at build time; upstream Agent Plugins
  material is already vendored and pinned.
- **Deployment sequencing:** T1–T5 land before the route is treated as a
  complete default output; T6 updates the public maintainer surface and package
  version in the same reviewed change. No artifact publication or client
  support promotion occurs in this slice.

## Risks

- The normative specification can impose requirements not encoded by its JSON
  schemas; the implementation must use both the acquired text slice and schema
  tests, and must not market schema validity as client conformance.
- The open `pack.metadata` table can contain TOML-only or instruction-like
  values; the extension boundary accepts only JSON-compatible objects and
  validates only against an allocated namespace schema.
- Filesystem checks can be race-prone or platform-specific; no-follow reads,
  inode/link-count checks, preflight-before-mutation, supported-platform skips,
  and post-write validation provide layered evidence.
- The AC3 roster can drift as packs change; its exact fixture makes that a
  reviewed contract change instead of silently changing published coverage.
- `build/main.py` is already large; route-specific helpers stay cohesive and
  Phase 2, not this slice, owns registry-driven extraction.

## Changelog

- 2026-08-25: Initial plan derived from the accepted Phase 1A slice, confirmed
  product boundary, repository anchors, and Agent Plugins 1.0.0 contract
  acquisition.
