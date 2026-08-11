# RFC-0085: Catalogue source identity

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-11
- **Date closed:** 2026-08-11
- **Decision weight:** heavy (this reverses part of an accepted governance decision)
- **Related:** RFC-0046 (the proposal that established default catalogue source resolution), ADR-0036 (the architecture decision record for that source-resolution design), `docs/guides/reference/catalogue-toml.md` (the organization Artifactory bootstrap added to the current chain)

`agentbundle` is the Python command-line tool that installs and projects packs
from a catalogue. A **pack** is a named bundle of agent primitives. A
**catalogue source root** is the authoring checkout that contains those packs;
it is distinct from an **installable archive**, which is a generated
distribution payload. An **adapter** maps catalogue primitives into one target
agent tool's filesystem format. **Projection** is the generation of those
adapter-specific files. **Self-host projection** applies that generation back
into the catalogue's own checkout so maintainers can use the catalogue through
their selected agent tools.

## Reviewer brief

- **Decision:** Define the adapter-neutral identity of a catalogue source root.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Require `catalogue.toml` and `packs/` for local source discovery, lint, and verify.
  - Require the Claude plugin marketplace only when the effective adapters include `claude-code`.
  - Release the breaking initial-development change as `agentbundle` 0.33.0.
- **Affected surface:** `agentbundle` source discovery, `catalogue lint` (portable source checks), `catalogue verify` (the full source-checkout pipeline), tests, and catalogue-author documentation.
- **Stakes:** Costly to reverse after catalogues rely on the new identity; intentionally breaking during 0.x development.
- **Review focus:** Source-root versus installable-archive boundaries, and consistency between adapter projection and lint.
- **Not in scope:** Source precedence, explicit catalogue-argument validation, installable archive layout, or a global removal of every internal no-config fallback.

## The ask

- **Recommendation (bottom line up front):** Recognize a catalogue source root through `catalogue.toml` plus the literal root `packs/` directory. Treat `.claude-plugin/marketplace.json`—the manifest consumed by Claude Code's plugin marketplace—as an adapter artifact rather than catalogue identity, and require it only when the effective adapter set includes `claude-code`.
- **Why now (situation–complication–question):** A catalogue can select Kiro, a non-Claude target, as its preferred adapter; self-host projection then correctly omits Claude-specific files. The linter and local-source detector still treat the Claude marketplace as unconditional, so valid Kiro-only source catalogues either fail lint or are not discovered. The project is still on `agentbundle` 0.x and can establish one adapter-neutral source contract before the Claude-specific marker becomes entrenched.
- **Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What identifies a catalogue source root? | `catalogue.toml` plus `packs/` | Both are adapter-neutral authoring inputs and already form the documented catalogue contract. | This review | Confirm the intentional legacy break. |
| D2 | Where is that identity enforced? | Local default-source discovery, `catalogue lint`, and `catalogue verify` | These are the surfaces that decide whether a source root exists and is valid. | This review | Confirm the bounded enforcement scope. |
| D3 | When is the Claude marketplace required? | Only when effective adapters include `claude-code` | This matches the existing self-host projection rule. | This review | Confirm adapter-derived behavior. |
| D4 | How does the change ship? | `agentbundle` 0.33.0 | Package policy requires a version bump and the change intentionally drops compatibility. | Implementation | Confirm release coupling. |

## Problem & goals

**Diagnosis.** Source discovery currently recognizes a local catalogue only when `packs/` and `.claude-plugin/marketplace.json` both exist. Catalogue lint repeats the marketplace requirement unconditionally. Self-host projection, however, omits Claude-specific files when the effective adapters exclude `claude-code`. The same source can therefore be valid to the projection engine but invalid to discovery and lint.

**Goals.**

- Give catalogue source roots one adapter-neutral identity: `catalogue.toml` plus `packs/`.
- Make lint and verify reject roots missing either required source marker.
- Keep Claude marketplace generation and lint requirements governed by the same effective-adapter rule.
- Preserve validation of a marketplace whenever one exists.
- Preserve the source-precedence chain, repository-bounded editable walk, and explicit-source behavior.

**Non-goals.**

- Redefining installable catalogue archives as source roots. Distribution payloads may omit authoring configuration.
- Changing remote source syntax, precedence, or network trust.
- Adding a legacy-marker transition period or automatic migration.
- Making the low-level configuration loader reject absence for every internal caller; the public source-validity boundaries own the mandate.

## Proposal

### D1 — Adapter-neutral source markers

A local catalogue source root contains a regular `catalogue.toml` file and a
literal `packs/` directory at the same root. `catalogue.toml` is the
schema-validated authoring configuration; its `[catalogue.paths]` table may
name additional operational paths, but it cannot rename either identity
marker. The default-source resolver uses the two root markers when it validates
a local source stored in user configuration and when it discovers a catalogue
from an editable Python installation.

Editable discovery resolves symlinks and `..` components (canonicalization),
walks upward from the installed package to the nearest matching ancestor, and
never walks above the enclosing Git repository root. Those existing
repository-boundary rules remain unchanged. The ordered source-precedence
chain—explicit command argument, user configuration, organization Artifactory
bootstrap, editable discovery, then the packaged default—also remains
unchanged. The organization bootstrap resolves a distribution-provided remote
catalogue and does not use local filesystem markers; only configured local
paths and editable discovery consume the marker predicate changed here.

The marker pair remains an accident guard, not a security control. Both files are forgeable by an actor who can already write inside the clone; code provenance continues to come from the trusted source-precedence chain established by RFC-0046 and ADR-0036.

### D2 — Enforcement boundaries

`catalogue lint` emits a catalogue-level error when `catalogue.toml` is absent
or the literal root `packs/` marker is missing. Once identity is established
and configuration is valid, lint separately checks any custom
`catalogue.paths.packs` location as an operational path; that configured-path
check cannot substitute for the root marker. `catalogue verify` runs lint even
when configuration loading returns no config, so an empty or legacy root no
longer passes by skipping config-dependent steps.

Other internal callers may continue using the configuration loader's optional return where their established behavior needs it. This RFC changes catalogue-source identity, not every fallback in the engine.

### D3 — Adapter-aware marketplace requirement

The **preferred adapter** is the target named in `catalogue.toml`. The
**effective adapter set** is what self-host actually projects: a preferred
adapter outside `build/recipes/self-host.toml`
`[recipe.adapters].targets` becomes the sole target; otherwise the recipe's
full target list remains effective. An absent, empty, unreadable, or malformed
list uses the built-in `claude-code` and `codex` defaults. The calculation
exposes one reusable predicate for whether Claude-specific project artifacts
are projected. Self-host generation and catalogue lint both consume it.

- Effective adapters include `claude-code`: a missing marketplace at
  `catalogue.paths.marketplace` emits `CAT-L002`, the existing missing-marker
  lint diagnostic.
- Effective adapters exclude `claude-code`: marketplace absence is valid.
- A marketplace that exists is still parsed and checked for the documented
  Claude plugin-manifest shape and catalogue entries.
- A missing `catalogue.toml` never falls back to marketplace-based identity.

### D4 — Release and migration

`agentbundle` moves from its current 0.32.0 release to 0.33.0 and publishes a
new Python Package Index (PyPI) artifact. Catalogue maintainers add a valid
`catalogue.toml` and root `packs/` directory before upgrading. Current
catalogues created by `catalogue init` already satisfy the new identity. No
compatibility alias or warning-only release is provided.

RFC-0046 and ADR-0036 receive dated errata approved by their named approver,
replacing the old Claude marketplace marker with `catalogue.toml`; their
source-precedence and repository-boundary decisions remain intact.

## Options considered

Two independent axes exhaust the decision space. Marker compatibility can
accept only the existing pair, both old and new pairs, or only the new pair.
Marketplace enforcement can be unconditional, derived from adapters, or
absent. The tables enumerate every combination on each axis before the chosen
answers are composed.

| Option | Prior art | Trade-off |
| --- | --- | --- |
| **Keep `packs/` plus marketplace (do nothing)** | Current RFC-0046/ADR-0036 implementation | No migration, but source identity remains tied to one adapter and Kiro-only catalogues remain inconsistent. |
| **Accept old or new marker pairs** | Compatibility transitions commonly retain legacy manifests | Reduces immediate breakage, but creates two identities and lets a Claude artifact indefinitely substitute for catalogue configuration. |
| **Require `catalogue.toml` plus `packs/`** ★ | `pyproject.toml` and `Cargo.toml` use tool-neutral manifests to identify project roots | One clear identity and no adapter coupling; legacy roots must migrate. |

| Marketplace policy | Consequence |
| --- | --- |
| **Always require it (do nothing)** | Contradicts intentionally non-Claude projection. |
| **Derive requirement from effective adapters** ★ | Matches generation while retaining Claude completeness checks. |
| **Never require it** | Allows incomplete Claude projections to pass lint. |

## Risks & what would make this wrong

**Pre-mortem.**

- *A legacy catalogue stops resolving after upgrade.* This is intentional but must be visible through the 0.33.0 release and migration note; no silent fallback remains.
- *Lint and self-host calculate adapters differently later.* One shared predicate and cross-surface regression tests prevent semantic drift.
- *Installable archives are accidentally subjected to source-root rules.* Enforcement stays in source discovery and catalogue authoring commands; generated installable archives continue to be checked by their archive manifest and content rules, not source markers.
- *A missing config produces duplicate or confusing diagnostics.* Lint emits one catalogue-level missing-config diagnostic and verify delegates to that result.

**Key assumptions.**

- Modern source catalogues already carry `catalogue.toml`; `catalogue init`
  creates it and `catalogue package --flavor source` includes it in the
  authoring-source archive.
- The old marker pair is not a security boundary; accepted RFC-0046 and ADR-0036 explicitly call it an accident guard.
- Effective-adapter membership is the authoritative signal for Claude project artifacts.

**Drawbacks.** Existing legacy roots require a manual configuration file before they work with 0.33.0. Tests built around intentionally config-less roots must become representative modern catalogue fixtures. The version requires a PyPI release before downstream users can consume the fix.

## Evidence & prior art

**Spike / de-risk result.** A read-only trace of the current five-layer source
resolver confirmed that changing its local-path marker predicate leaves the
organization Artifactory bootstrap, source precedence, canonicalization,
nearest-ancestor selection, and the enclosing-git-root boundary untouched.
RFC-0046 and ADR-0036 explicitly state that the two markers are forgeable and
serve only as an accident guard, so substituting an adapter-neutral manifest
does not weaken a claimed trust control. The source-flavour package—an archive
of the authoring catalogue—includes `catalogue.toml`; generated installable
archives are separate. An explicit catalogue argument continues directly to
the catalogue resolver instead of being classified by default-source
discovery.

**Repo precedent.**

- `docs/guides/reference/catalogue-toml.md` calls `catalogue.toml` the file that makes a directory a recognized catalogue.
- `catalogue init` creates both `catalogue.toml` and `packs/`.
- Self-host projection already gates Claude-specific files on effective-adapter membership.
- RFC-0046 and ADR-0036 establish the source-precedence and repository-bounded discovery controls retained here.

**External prior art.**

- The [Python Packaging `pyproject.toml` specification](https://packaging.python.org/en/latest/specifications/pyproject-toml/) defines a tool-neutral configuration surface containing project metadata.
- The [Cargo project locator](https://doc.rust-lang.org/cargo/commands/cargo-locate-project.html) finds a project by walking upward for its `Cargo.toml` manifest.
- [Semantic Versioning 2.0.0](https://semver.org/) defines major version zero for initial development and recommends minor-version increments during rapid API evolution.

## Open questions

None. The source marker, enforcement scope, marketplace predicate, and release increment are approved together.

## Follow-on artifacts

- Signed errata to RFC-0046 and ADR-0036 for the source-marker decision.
- Spec: `docs/specs/catalogue-source-identity/`.
- Updates to catalogue reference documentation and architecture text that still describe the Claude marketplace as source identity.
- `agentbundle` 0.33.0 changelog/release note and a migration note telling
  legacy catalogue maintainers to add `catalogue.toml` and root `packs/`
  before upgrading.
