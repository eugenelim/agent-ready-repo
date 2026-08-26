# Spec: Portable Agent Plugin projection

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0092; ADR-0090; ADR-0021; ADR-0072
- **Brief:** docs/product/briefs/distribution-routes-programme.md
- **Discovery:** `docs/product/intents/portable-agent-plugin-projection.md`
- **Contract:** `contracts/distribution-routes.toml`; `contracts/distribution-routes.schema.json`; `contracts/agent-plugin-extension-namespaces.toml`; `contracts/agent-plugin-extension-namespaces.schema.json`; `contracts/vendor/agent-plugins/1.0.0/plugin.schema.json`; `contracts/vendor/agent-plugins/1.0.0/mcp.schema.json`; `contracts/vendor/agent-plugins/1.0.0/LICENSE.md`; `contracts/vendor/agent-plugins/1.0.0/PROVENANCE.md`
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A catalogue maintainer runs the existing build and receives a deterministic,
offline-validatable Agent Plugins 1.0.0 package at
`dist/agent-plugins/<pack>/` for every pack whose canonical content is
portable without loss. Each emitted package derives its root manifest and
`skills/` tree from canonical pack sources, admits only allocated and
schema-valid reverse-domain extensions, and makes exclusions explicit without
changing the existing APM, Claude-plugin, or direct-install outputs.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Derive portable metadata from `pack.toml`, skills from
  `.apm/skills/<skill>/`, and extension content only from an explicitly
  allocated namespace and its declared pack source.
- Validate the route contract, source package, derived manifest, extension
  declaration, and completed output tree before treating an artifact as
  publishable; refuse unsafe or ambiguous input with the pack, route, and
  failing component named.
- Build from vendored, provenance-pinned schemas with no network access, write
  output deterministically, and preserve the existing APM and Claude-plugin
  golden trees byte-for-byte.
- Use the repository's confined regular-file helpers for pack-authored reads
  and reject link-like, hard-linked, or non-regular entries before route output
  mutation.

### Ask first

- Change the pinned Agent Plugins specification version, upstream schema bytes,
  licence record, or immutable provenance.
- Emit a portable package for a pack containing a canonical primitive that the
  route declares dropped, or weaken an exclusion/refusal into silent loss.
- Activate a reverse-domain namespace, change its owner, or change its
  versioned schema.
- Add or promote any runtime-support, client-conformance, publication, or
  adaptation claim.

### Never do

- Add the canonical MCP authoring model, emit `mcp.json`, or implement MCP
  direct-install/native-route parity; those behaviors belong to Phase 1B even
  though the 1.0.0 MCP schema is vendored here.
- Introduce the generic distribution-route registry, a new dependency, a
  network fetch in the normal build, or an additional canonical pack primitive.
- Project agents, commands, hooks, libraries, binaries, IDE hooks, seeds,
  adaptation markers, or generated manifests as portable authoring sources.
- Normalize a non-conforming pack or namespace identity silently, preserve an
  unsafe filesystem entry, or claim that schema conformance proves runtime or
  security behavior.

## Testing Strategy

- **Route admission, manifest derivation, namespace allocation, and deterministic
  traversal — TDD at unit and build-pipeline surfaces.** These are compressible
  rules with negative cases: invalid identities, dropped primitives,
  undeclared/colliding namespaces, malformed metadata, unsafe entries, and
  unstable ordering must each produce a precise refusal.
- **Vendored contract identity, packaged-data parity, existing-route
  invariance, and complete-tree determinism — goal-based checks exercised by
  integration tests.** Exact upstream blob identities, licence/provenance,
  byte-identical contract copies, two-build tree equality, and unchanged
  APM/Claude fixtures are mechanical outcomes.
- **Maintainer journey — visual/manual QA through the real built artifact.**
  Run the normal catalogue build, validate an emitted eligible package against
  the vendored 1.0.0 schema, observe a named exclusion for an ineligible pack,
  and rerun the build with an identical output-tree digest. This exercises the
  same entry point and files a maintainer publishes, not a mocked projector.
- **Filesystem trust boundary — TDD plus integration fixtures.** Symlink,
  junction/reparse-point where supported, hard-link, FIFO/device, traversal,
  source-change, and stale-output cases prove fail-closed preflight,
  transactional cleanup, and post-write validation.

## Acceptance Criteria

- [x] The repository vendors the exact Agent Plugins 1.0.0
  `schemas/1.0.0/plugin.schema.json` and
  `schemas/1.0.0/mcp.schema.json` bytes from immutable upstream commit
  `ff8ab5e392cc87bd88d87c060815a87490e51003`; provenance records upstream
  paths, commit, Git blob identities
  `8fed0e1fe45d0464aee880d3fbab228b71ecfc1e` and
  `a9139a4259b932c60b5351c8d9da6a5c60c97646`, and the upstream Apache-2.0
  schema licence, and a normal build performs no schema fetch.
- [x] The authored and bundled distribution-route contracts declare exactly
  one new explicit `agent-plugin` route with output
  `agent-plugins/<pack>/`, a root-manifest projector, no runtime-adapter or
  marketplace projector, no lifecycle trigger, `skill = native`, and every
  other Phase 0 canonical primitive = `dropped`; the contract and recipe
  schemas reject any inconsistent declaration.
- [x] The normal catalogue build emits portable artifacts for the exact 13
  currently buildable skills-only packs — `atlassian`, `catalogue-curation`,
  `contracts`, `converters`, `figma`, `github`, `governance-extras`,
  `iac-terraform`, `linear`, `monorepo-extras`, `product-documentation`,
  `product-strategy`, and `user-guide-diataxis` — and emits no artifact for
  the eight packs carrying dropped canonical primitives: `architect`
  (`agent`), `core` (`agent`, `hook-body`, `hook-wiring`, `command`, and
  `kiro-ide-hook`), `credential-brokers` (`shared-libs`, `adapter-root-bins`,
  and `user-libs`), `desk-research` (`agent`), `experience-design` (`agent`),
  `frontend-engineering` (`agent`), `product-engineering` (`agent`), and
  `release-engineering` (`agent`). Every exclusion diagnostic names the pack,
  `agent-plugin` route, and complete set of excluding primitives.
- [x] Each emitted root `plugin.json` validates before and after write against
  the vendored 1.0.0 plugin schema and contains only: the canonical `$schema`;
  the unchanged canonical pack name; optional `version`, `description`,
  first-maintainer `author` containing only `{"name": <maintainer name>}`,
  `homepage`, `repository`, `license`, and `keywords` values when present; and
  allocated extension data when present. Maintainer email, URL, username, and
  account identifiers are never projected into the portable author object.
  Claude-only `source`, `category`, `displayName`, hooks, and component
  paths are absent. Manifest and extension data must contain only strict JSON
  values: non-finite numbers such as NaN and positive or negative infinity are
  rejected before publication rather than emitted by a permissive serializer.
- [x] A canonical pack name that violates the portable 1–64 character,
  lowercase `[a-z0-9.-]`, alphanumeric-edge, no-`--`, or no-`..`
  constraints fails with a named diagnostic; the projector never rewrites the
  identity.
- [x] Every immediate canonical skill directory is projected to
  `skills/<skill>/` with its confined regular files, relative hierarchy,
  bytes, and executable/non-executable mode preserved; discovery is
  lexicographically stable and no other `.apm/` primitive enters the package.
- [x] A canonical extension-namespace registry allocates each reverse-domain
  name to one owner and lifecycle state, reserves `dev.kiro` for the Kiro
  profile and `com.github.copilot` for the Copilot profile, and requires an
  active namespace to name a versioned validation schema before pack content
  can use it.
- [x] Portable manifest extension data and an optional same-named pack-root
  extension directory are projected only when the pack declares the namespace
  through its existing `pack.metadata.agent-plugin.extensions` table and the
  registry marks it active; invalid, undeclared, reserved, duplicate,
  case-colliding, schema-invalid, or destination-colliding content refuses the
  pack before publication. Before namespace-schema validation or route-output
  mutation, the combined extension manifest data is bounded to 8 MiB of strict
  UTF-8 JSON, nesting depth 20, 4,096 total object members, 64 KiB of UTF-8 for
  any key or string value, and 256 items in any array; boundary-plus-one input
  is refused.
- [x] The route rejects symlinks, junctions/reparse points, hard-linked files,
  non-regular entries, lexical/resolved traversal, and source replacement
  across the canonical `pack.toml`, skill, and extension inputs before mutating
  that route's output; `pack.toml` is read through the confined single-link
  regular-file seam with a 1 MiB limit. Across the combined skill and extension
  inputs for one pack it also
  rejects any regular file larger than 2 MiB, more than 4,096 regular files,
  more than 32 MiB total regular-file bytes, or a relative path deeper than 20
  components before mutation, then validates that the completed artifact
  contains only confined directories and single-link regular files.
- [x] Rebuilding twice from the same source produces the same sorted relative
  path inventory, file bytes, and executable-mode inventory; stale files from
  a prior build are absent and every generated JSON file uses UTF-8, stable key
  order, two-space indentation, one trailing LF, and no platform-dependent line
  endings. JSON serialization is strict (`allow_nan=False` or equivalent).
- [x] Existing APM and Claude-plugin complete-tree golden fixtures remain
  byte-identical, direct `agentbundle install` behavior is unchanged, and no
  generic registry or adapter-contract ownership is introduced.
- [x] The packaged CLI contains byte-identical copies of every route contract,
  vendored schema, provenance/licence file, and default recipe it needs; source
  and packaged-data parity gates fail on drift, and non-cosmetic package
  versions are updated together.
- [x] Maintainer documentation names the real build command, output layout,
  eligibility/exclusion rule, offline schema-validation source, and
  documentation-verified support posture, and explicitly states that MCP,
  seeds, adaptation, publication automation, and runtime verification are not
  provided by this slice.
- [x] The focused unit/build-pipeline/integration suites, full
  `packages/agentbundle/tests/` suite, contract parity, catalogue build, lint,
  and build-check gates pass; the real build smoke records one valid eligible
  artifact, one named exclusion, and identical consecutive output digests.
- [x] Every refusal diagnostic is sanitized and contains only the pack, route,
  failing component, an already-validated relative path when applicable, and a
  stable error class. It never exposes an absolute host path, raw pack-authored
  value, schema payload, or other source content that could contain a secret-like
  string. Every untrusted identity or relative-path field uses a deterministic
  ASCII JSON-string representation that escapes controls, ANSI escapes,
  newlines, bidirectional/zero-width characters, and all non-ASCII code points;
  this display escaping never normalizes the accepted artifact identity.

## Assumptions

- Technical: Phase 0's route contract and explicit two-route resolver are shipped and are the required predecessor (source: `docs/specs/distribution-route-contract/spec.md`; `contracts/distribution-routes.toml`).
- Technical: Phase 1A is the portable manifest/skills/extensions slice, while canonical MCP behavior is a separate Phase 1B slice (source: `docs/product/briefs/distribution-routes-programme.md`; user confirmation 2026-08-25).
- Technical: Agent Plugins 1.0.0 is a published directory contract with root `plugin.json`, fixed `skills/`, optional root `mcp.json`, and reverse-domain extension data/directories; the two official schemas are version-paired and locally selectable (source: the immutable upstream identifiers recorded in AC1; upstream `spec/1.0.0.md`).
- Technical: the upstream schema blobs and Apache-2.0 software licence retain the immutable identities recorded only in AC1 and the corresponding vendored `PROVENANCE.md` (source: GitHub contents API reads on 2026-08-25; upstream `LICENSE.md`).
- Technical: the existing pack metadata projection selects the first listed maintainer as singular `author`; the portable route preserves that selection while privacy-minimizing the new public artifact to the maintainer `name` field only (source: `packages/agentbundle/agentbundle/build/main.py:229`; `docs/CONVENTIONS.md#privacy`).
- Technical: the current buildable corpus matches the exact eligible and excluded membership recorded only in AC3 (source: `docs/rfc/0092-first-class-distribution-routes.md` P6; current `contracts/adapter.toml` inventory verified 2026-08-25).
- Product: the user is a catalogue maintainer using the existing build, and success is deterministic `dist/agent-plugins/<pack>/` output for every portable-eligible pack without a runtime-verification claim (source: user confirmation 2026-08-25).
- Process: this structural, published-interface, and filesystem-boundary change uses full work-loop mode with separate human spec and plan approvals before implementation (source: `AGENTS.md`; `.agents/skills/work-loop/SKILL.md`).
