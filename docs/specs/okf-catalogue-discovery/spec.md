# Spec: OKF catalogue discovery

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0087, RFC-0060, RFC-0076
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/agentbundle-show.schema.json`](../../../contracts/jsonschema/agentbundle-show.schema.json)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Catalogue maintainers and programmatic consumers can inspect one pack with
`agentbundle show <pack> --format json` and receive one schema-governed,
deterministically ordered response covering pack positioning, Skill activation
metadata, and declared OKF knowledge bundles. Catalogue-backed inspection derives
the response live from the selected pack's authored and generated files. When
only install state is available, the command preserves its existing inventory
fallback and marks all three rich metadata levels unavailable with `null`
instead of fabricating them. Existing JSON fields, error exits, human-readable
output, and `catalogue-index.json` retain their current meanings.

## Boundaries

This spec governs successful `show --format json` responses and the read-only
derivation needed to produce them. It does not make OKF a registry or runtime.

### Always do

- Validate every successful JSON response against the complete
  `agentbundle-show.schema.json` contract and emit every contracted top-level
  key on both catalogue and installed-state success paths.
- Read catalogue-backed metadata on demand from `pack.toml`, `.apm/skills/`,
  declared OKF roots, and compiler-owned markers/manifests; normalize all paths
  relative to the selected pack and sort every inventory deterministically.
- Expose only the explicit pack, Skill, and knowledge allowlists in this spec;
  use `null` where installed state cannot establish metadata.
- Preserve the current unknown-pack and unavailable-catalogue error contract:
  nonzero exit, one-line stderr, and empty stdout, including JSON mode.
- Treat malformed managed OKF declarations or generated metadata as an honest
  inspection failure rather than returning a partial or fabricated success.

### Ask first

- Ask before changing the human-readable `show` table, `list-packs`,
  `catalogue-index.json`, marketplace projections, or any cross-pack discovery
  surface.
- Ask before exposing concept bodies, source/provenance records, remote URLs,
  authors, arbitrary frontmatter, or unknown extensions in CLI output.
- Ask before retaining OKF discovery data in install state or introducing a
  cache, registry, search service, or runtime compiler invocation.
- Ask before changing any existing field type/meaning, removing a response key,
  or publishing the package without its required release/version documentation.

### Never do

- Never invoke `compile-okf`, mutate a pack, fetch a remote resource, execute
  bundle content, or require an LLM while serving `show`.
- Never infer pack or knowledge metadata from names, prose, adapter paths, or
  installed files when the canonical source is unavailable.
- Never serialize raw TOML/YAML/frontmatter maps, filesystem absolute paths,
  secret-bearing values, concept content, or compiler diagnostics into a
  successful response.
- Never add OKF-specific fields to `catalogue-index.json`, a new top-level
  repository directory, or a new public package layer under this experiment.
- Never add PyYAML or another dependency to the base AgentBundle runtime for
  discovery.

## Testing Strategy

- **Response contract — TDD.** Positive catalogue and installed-state fixtures,
  plus one negative mutation for every required field/type/closed object, prove
  the complete JSON Schema and renderer stay aligned.
- **Live derivation — TDD.** Pack, authored Skill, generated Skill, OKF bundle,
  lifecycle, path, digest, and malformed-source fixtures exercise pure metadata
  extraction and allowlisting because these are exact data invariants.
- **CLI compatibility — goal-based integration checks.** Process-level tests
  compare legacy fields, exits, stdout/stderr, table output, and installed-state
  union behavior before and after the additive response.
- **Cross-feature consistency — goal-based integration checks.** Golden digest
  and metadata fixtures are shared with the authoring compiler so `show` reports
  the same normalized bundle and generated-Skill identities without invoking
  that compiler.
- **Release readiness — goal-based checks.** Package tests, schema validation,
  README/CLI examples, version parity, and distribution metadata prove the
  changed public JSON interface ships coherently.

## Acceptance Criteria

- [ ] **AC1:** `contracts/jsonschema/agentbundle-show.schema.json` is valid JSON
  Schema 2020-12, links back to this spec, closes every object, and governs the
  complete successful response rather than an OKF fragment.
- [ ] **AC2:** Every successful JSON response contains exactly these top-level
  keys: `name`, `version`, `description`, `skills`, `agents`, `integrations`,
  `source`, `pack_metadata`, `skill_metadata`, and `knowledge`.
- [ ] **AC3:** The existing `name`, `version`, `description`, `skills`, `agents`,
  `integrations`, and `source` fields retain their current types, ordering,
  catalogue derivation, installed-state degradation, and meaning, including
  `null` catalogue `version` or `description` when that optional key is absent.
- [ ] **AC4:** On `source: "catalogue"`, `pack_metadata` is an object containing
  exactly `categories`, `keywords`, and `license`, derived from `[pack]` in
  `pack.toml`; absent categories/keywords become empty arrays and an absent
  licence becomes `null`.
- [ ] **AC5:** On `source: "catalogue"`, `skill_metadata` is a name-sorted array
  with exactly one entry for every live `.apm/skills/<name>/` directory that
  has a valid `SKILL.md`, matching the full untagged `skills` inventory rather
  than `[pack.evals].skills`.
- [ ] **AC6:** Each Skill entry contains exactly `name`, `description`,
  `license`, `compatibility`, `generated_from`, `profile`, `digest`, and
  `boundaries`. Authored values come from the allowed Skill frontmatter fields;
  missing values use `null` or `[]`, never inferred pack values.
- [ ] **AC7:** A generated Skill entry reports `generated_from`, `profile`, and
  `digest` only when its generated markers are complete, string-valued, use a
  confined normalized relative source path, name the supported profile, and
  agree with the compiler manifest. A concept-derived procedure must also carry
  a valid manifest-matching `reviewed-projection-digest`, while a router must
  omit that marker. Both report their `boundaries` list; incomplete, unexpected,
  or conflicting markers fail inspection. The review digest is validated but
  not emitted because it is outside the response allowlist.
- [ ] **AC8:** On `source: "catalogue"`, `knowledge` is sorted by bundle ID and
  contains exactly one entry for every `[pack.metadata.okf.bundles]`
  declaration; packs without that table return `knowledge: []`.
- [ ] **AC9:** Each knowledge entry contains exactly `id`, `format`,
  `okf_version`, `router_skill`, `content_license`, `concept_count`, and
  `digest`; `format` is `"okf"`, `okf_version` is `"0.2"`, paths are never
  emitted, and all other values derive from the declaration and live bundle.
- [ ] **AC10:** `concept_count` counts valid concept Markdown files beneath the
  bundle root, excluding compiler-owned indexes and non-concept includes. The
  bundle digest uses the compiler's canonical source-digest algorithm and
  matches its manifest; disagreement fails inspection.
- [ ] **AC11:** `content_license` comes from the root OKF licence declaration or
  from an explicit, compiler-validated SPDX-compatible pack-licence inheritance
  marker; absence or incompatible inheritance fails inspection rather than
  guessing.
- [ ] **AC12:** Catalogue discovery parses only the bounded scalar/list
  frontmatter subset required by the allowlist using the base-runtime standard
  library path; aliases, tags, malformed structures, unsupported profiles,
  unsafe or non-portable paths, missing roots, manifest drift, duplicate
  IDs/names, and Unicode-NFC or case-folded collisions return nonzero with empty
  stdout and one normalized one-line stderr diagnostic.
- [ ] **AC12a:** Before full parsing, discovery rejects `pack.toml` above 1 MiB,
  `.okf-generated.json` above 8 MiB, more than 4,096 Skill or agent directories,
  more than 128 integrations or declared bundles, a `SKILL.md` above 2 MiB,
  Skill frontmatter above 64 KiB, parsed manifest or frontmatter nesting above
  20 levels, or any categories, keywords, boundaries, consumers, or providers
  list above 256 items. Declared bundles retain the OKF corpus limits.
  Boundary-equal fixtures pass and boundary-plus-one fixtures fail before
  oversized content is fully parsed.
- [ ] **AC13:** The command never emits concept bodies, instruction sections,
  includes, executor/attester/runtime data, remote resource URLs, authors,
  source records, absolute paths, arbitrary pack metadata, or unknown
  frontmatter/extensions.
- [ ] **AC14:** All name, boundary, category, keyword, and bundle arrays use
  stable ascending Unicode-NFC ordering with duplicates removed; repeated calls
  over the same pack bytes emit byte-identical compact JSON plus one LF.
- [ ] **AC15:** On `source: "installed-state"`, `version` and `description` stay
  `null`, `integrations` stays `[]`, current multi-scope/multi-adapter
  `skills`/`agents` union behavior is unchanged, and `pack_metadata`,
  `skill_metadata`, and `knowledge` are each exactly `null`.
- [ ] **AC16:** A catalogue-backed pack with no Skills or OKF declaration
  returns empty `skills`, `agents`, `skill_metadata`, and `knowledge` arrays and
  a non-null `pack_metadata` object; this is a successful schema-valid response.
- [ ] **AC17:** An unknown catalogue pack, or an unavailable catalogue plus a
  pack absent from install state, preserves the current exit-1, empty-stdout,
  one-line-stderr behavior under both table and JSON formats.
- [ ] **AC18:** Human-readable `show`, `list-packs`, marketplace output, and the
  RFC-0076 `catalogue-index.json` contract and bytes are unchanged by the
  experiment.
- [ ] **AC19:** `show` reads live sources on every catalogue-backed invocation,
  performs no network call, compiler call, cache write, state write, or pack
  write, and behaves identically when PyYAML is not installed.
- [ ] **AC20:** The discovery implementation and full-schema tests cover both
  generated pilots and a non-OKF pack. The cost pilot's exact reserved
  pack-shaped bytes are staged under a temporary discoverable catalogue path
  for the CLI test; the working catalogue continues to omit the reserved source
  from list/publish surfaces. A pack/Skill metadata edit is visible on the next
  call without regeneration of a discovery index; an OKF source edit that has
  not regenerated its manifest/projection fails honestly as drift on the next
  call.
- [ ] **AC21:** The release-bearing AgentBundle change receives synchronized
  package version metadata, `README-pypi.md` documentation of the additive JSON
  fields and installed-state null behavior, changelog/release notes, and all
  package integration tests before publication.

## Assumptions

- Technical: the current successful `show --format json` object contains
  `name`, `version`, `description`, `skills`, `agents`, `integrations`, and
  `source`; installed-state fallback uses null metadata and unions inventories
  across scopes/adapters (source:
  `packages/agentbundle/agentbundle/commands/show.py` and
  `packages/agentbundle/tests/integration/test_show_cmd.py`).
- Technical: AgentBundle targets Python 3.11+ with no base dependencies, while
  its existing catalogue tooling includes a standard-library frontmatter
  subset parser suitable for scalar/list discovery fields after verification
  against the required shapes (source: `packages/agentbundle/pyproject.toml`
  and `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`).
- Product: the experimental discovery surface is programmatic JSON inspection;
  human-readable output and cross-pack discovery remain unchanged (source:
  RFC-0087 D6; user confirmation 2026-08-15).
- Process: a public AgentBundle output-format change requires a package version
  bump, `README-pypi.md` update, and PyPI release before downstream consumption
  (source: `packages/AGENTS.local.md`).
- Process: RFC-0060 requires live-derived inventory and RFC-0076 owns the
  neutral `catalogue-index.json`; this spec adds neither a persisted discovery
  index nor OKF fields to that contract (source: RFC-0060, ADR-0049, RFC-0076).
- Process: the complete response contract is a standalone JSON Schema under
  `contracts/jsonschema/`; no JSON Schema authoring skill is installed, so it is
  directly authored without rule-enforcement and validated with the repository
  toolchain (source: `docs/CONVENTIONS.md`; user confirmation 2026-08-15).
