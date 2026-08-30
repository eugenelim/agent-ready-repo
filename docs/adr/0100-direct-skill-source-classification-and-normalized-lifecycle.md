# ADR-0100: Direct skill sources classify after resolution and normalize into canonical packs

- **Status:** Accepted
- **Date:** 2026-08-27
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** [RFC-0098](../rfc/0098-direct-skill-repository-installation.md) (direct-source contract and Errata); [RFC-0085](../rfc/0085-catalogue-source-identity.md) (catalogue identity); [ADR-0036](0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md) (source precedence and its 2026-08-11 Erratum handing catalogue identity to RFC-0085); [ADR-0039](0039-footprint-co-ownership-install-identity-and-shared-prefix-class.md) (pack/adapter identity and rollback posture)

## Decision summary

- **Decision:** Classify bounded direct skill sources only after resolution, normalize admitted shapes into canonical packs, and retain pack-keyed state with direct provenance.
- **Because:** This keeps validation, projection, ownership, state, drift, and lifecycle in their existing owners rather than creating a second installer.
- **Applies to:** Explicit local and hardened GitHub `git+https` direct-skill sources, their manifests, state, lifecycle commands, and author contract.
- **Tradeoff accepted:** Normalization performs temporary confined copying and a deliberately narrow source, manifest, and remote-trust contract.
- **Revisit if:** (1) an import-boundary test cannot prove install and validate reach direct classification through the named shared entry point; (2) a supported adapter cannot preserve byte-identical canonical/direct projections; (3) a required source needs a transport beyond hardened GitHub; (4) an approved primitive needs lifecycle behavior not representable by a pack row; or (5) the N/N−1 manifest-major support window expires.

## Context

[RFC-0085](../rfc/0085-catalogue-source-identity.md) defines a catalogue by root `catalogue.toml` and `packs/`; [ADR-0036](0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md) owns source precedence; [ADR-0039](0039-footprint-co-ownership-install-identity-and-shared-prefix-class.md) owns pack/adapter identity and ownership. A repository rooted at `SKILL.md` or `skills/` is a different source shape, not a malformed catalogue—except a partial `catalogue.toml` marker, which remains malformed.

The durable limit is **admissible, not safe**: deterministic checks establish a bounded structural and provenance contract but never prove skill prose or scripts harmless. State-schema and manifest-schema versions are independent namespaces.

## Decision

> Direct sources classify after resolution, normalize into the canonical pack pipeline, and preserve pack-keyed lifecycle semantics with explicit direct provenance.

### 1. Classify after resolution

After the resolver returns a confined directory, classify an existing canonical `pack.toml + .apm/` pack through its existing path; a catalogue only when both `catalogue.toml` and `packs/` exist; otherwise a direct pack, manifestless collection, or manifestless single. A `catalogue.toml` without `packs/` is a partial catalogue marker and refuses. Root `SKILL.md + skills/`, root `pack.toml + SKILL.md`, unsupported nested roots, and other overlaps refuse. RFC-0098 E13 owns root-context disposition, AC32 owns direct measured content, and AC33 owns its budgets.

**Consequence:** Catalogue precedence is preserved while no transport gains an implicit root-shape rule. A local path already at a skill is allowed; collection/direct-pack child names must equal frontmatter names, while root-single frontmatter is authoritative.

**Revisit trigger:** A classification fixture requires a new precedence rule or a recursive/hidden discovery exception.

**2026-08-28 Erratum — trigger fired, decision retained.** RFC-0098 E14 admits `.claude/skills/` as a second collection root and one bounded category level below a collection root, on corpus evidence that the single-root rule refused six of thirteen legitimate sources. This is a hidden-root exception, so the trigger above fired; the decision in §1 is retained because the exception is enumerable at fixed depth rather than recursive, and because E14 adds compensating refusals — ambiguity when both roots are present, and refusal when the source root lies inside the projection target or bears catalogue markers.

### 2. Normalize through one named entry point

`direct_source.admit_and_normalize` (or its final explicitly named equivalent) owns classification, confined inventory, normalization, and baseline direct admission. Both `validate` and install preflight reach direct classification only through that entry point; an import-boundary construction test enforces this. Canonical `pack.toml + .apm/` paths retain their existing route.

Normalization copies into a temporary canonical pack only the byte string returned by the single confined read of each admitted regular file, never symlinks or reopens source content. It reuses canonical validation → rendering → planning → installation → state, and the temporary path is never provenance or receipt content.

Family-2 inventory is likewise single-traversal. `catalogue_tooling/file_safety.py` raises `BoundExceeded`, an `UnsafeContentError` subclass carrying the breached budget, so direct admission maps a bound to its registered diagnostic without message parsing; existing catalogue callers retain their `UnsafeContentError` catch behavior. A separate direct diagnostic represents a source that cannot be traversed or changes during admission, rather than misclassifying that condition as measured-path integrity.

**Consequence:** Byte-identical projection and plan parity against hand-authored canonical fixtures is release-critical.

**Revisit trigger:** The import-boundary test fails or parity requires a direct-only downstream branch.

### 3. Keep lifecycle identity pack-keyed

A direct pack is one named/versioned indivisible lifecycle. A manifestless selected skill becomes one synthetic pack whose identity is its validated skill name; the internal sentinel is never rendered, compared, or publisher-claimable. A same-name direct/other source collision at one adapter refuses in either direction; recovery is removal or rename/re-source followed by a normal install, never `--force`.

**Consequence:** No collection object or state hierarchy is added; manifestless rows remain independently upgradable and removable.

**Revisit trigger:** Upgrade/uninstall demonstrably requires a durable collection identity or source conflicts cannot be recovered through existing ownership semantics.

### 4. Add direct provenance with lazy state migration

State remains keyed by `(pack name, adapter)`. Direct identity is `(source-kind, canonical source, source-path)`; digest and revision are explicitly excluded. `source-path` is absent for a direct pack (not empty) and validated relative POSIX for a manifestless skill; every read re-establishes source root and confinement before joining.

Readers accept 0.4/0.5. This amends the greenfield hard-refusal posture recorded at `packages/agentbundle/agentbundle/config.py` and inherited from ADR-0039, under which a reader refused every unrecognized `schema-version` and no converter existed; the amendment is narrowed to a supported-version set on read. Every direct state mutation goes through `agentbundle.statelock.persist_state_locked` and computes `max(existing, 0.5 if it adds or updates a direct row else 0.4)` against the state re-read inside that lock, never a pre-lock snapshot: catalogue-only mutations stay 0.4 when they begin there, while an existing 0.5 file is never downgraded, including after its last direct row is removed. This preserves ADR-0039’s rollback posture for unaffected users without orphaning direct provenance. Older readers refuse 0.5 through that same existing hard refusal, whose shipped text directs reinstallation rather than migration, so the migration is intentionally reversible only for states that never acquire direct rows.

RFC-0098 D4 as corrected by Erratum E2 is the sole normative digest algorithm owner: it defines sort key, field order, and digest-version migration; the version-prefixed digest is `sha256-1:<hex>`. Digest is content-only. Executable-mode is reported in the security summary but computed at report time and never persisted; the existing `safety.write_jailed` call-site default writes installed direct payloads non-executable, so a source-side bit does not change what lands on disk.

**Consequence:** State migration and digest vectors are compatibility evidence, without duplicated algorithm prose.

**Revisit trigger:** A direct row cannot be represented without changing the pack/adapter key or a new digest version is proposed.

### 5. Require explicit direct-manifest schema and bounded support

A new direct `pack.toml` **must** declare `schema = 1`; omission fails closed. The contract schema and bundled `_data/` copy add that top-level field in byte parity; implicit v1 remains a legacy catalogue-manifest affordance only. Within a supported major, existing field meanings are not removed, repurposed, or newly required; supported majors are N and N−1 for one named release deprecation window, after which the oldest major may be removed by a documented migration. Unsupported majors fail closed.

**Consequence:** Manifest compatibility is explicit and separate from security controls and state versioning; the contract update is release-impacting.

**Revisit trigger:** A proposed field requires an incompatible meaning inside a major or the release policy cannot sustain the N/N−1 window.

### 6. Harden the direct remote boundary

Only explicit local paths and GitHub-only non-credentialed `git+https` may carry direct content. Current resolver behavior does **not** enforce this decision yet. Direct remote intake validates and encodes archive components, refuses bare/defaulted `main`, resolves an explicit ref to a full commit SHA, records it, applies the shared credential-free `git+https` acquisition resource caps, deadline, and E11-defined GitHub/codeload redirect equivalence, and applies direct-only post-extraction link and special-entry refusal. Commit-pinned provenance is therefore bounded by the configured TLS trust store. This closes, for the direct path, the unauthenticated-fetch residual that ADR-0036 accepted only for its upstream-public-default scope; the existing `git+https` catalogue route gains the shared acquisition controls without changing catalogue classification or precedence.

The shared resolver inherits numeric bounds by reference to RFC-0098/its implementation constants, not hard-coded ADR values. Catalogue symlink support remains intact.

**Consequence:** `catalogue+https` and arbitrary archives remain excluded from direct classification, and no direct credentials are sent.

**Revisit trigger:** A new direct carrier or redirect host is requested, or the catalogue-symlink regression fails.

## Consequences

**Positive:** Existing source precedence, adapter projection, ownership, and lifecycle remain the authority; direct authors get a small, explicit contract; and direct remote provenance is commit-pinned.

**Negative:** Direct support deliberately excludes recursive discovery, private auth, arbitrary archives, non-GitHub VCS, dependencies, recipes, and non-skill primitives. Normalization copies/hashes first, and direct state makes the affected installation incompatible with old readers.

## Confirmation

- **Mode:** construction tests, manual CLI exercise, and security evidence.
- **Signal:** import-boundary, shape, canonical/direct parity, state migration, digest vector, remote URL/pin/resource, diagnostic parity, lifecycle, interrupted-install, and catalogue-symlink regression tests pass; the security-checklist record is complete.
- **Owner:** AgentBundle maintainers and reviewers of RFC-0098 implementation work.

## Alternatives considered

| Option | Trade-off |
| --- | --- |
| Require every repository to become a catalogue | Reuses machinery but imposes unnecessary catalogue structure. **Rejected against:** bounded-authoring driver. |
| Copy selected skills directly into runtime directories | Appears small but bypasses projection, ownership, drift, and lifecycle. **Rejected against:** canonical-lifecycle driver. |
| Add an install-unit model and parallel state hierarchy | Makes identities uniform but rewrites mature lifecycle machinery prematurely. **Rejected against:** reversibility and smallest-change drivers. |
| Normalize direct shapes into existing packs | Adds a narrow adapter and provenance while retaining established owners. **Chosen against:** all decision drivers. |

## References

- [RFC-0098](../rfc/0098-direct-skill-repository-installation.md) — accepted direct-source contract and binding Errata.
- [RFC-0085](../rfc/0085-catalogue-source-identity.md) — catalogue identity after source resolution.
- [ADR-0036](0036-install-source-resolves-through-trusted-precedence-chain-no-repo-source-no-cwd.md) — source precedence, including its 2026-08-11 Erratum.
- [ADR-0039](0039-footprint-co-ownership-install-identity-and-shared-prefix-class.md) — pack/adapter identity, ownership, and pre-direct migration posture.
