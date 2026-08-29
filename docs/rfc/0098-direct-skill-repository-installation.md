# RFC-0098: Direct skill repository installation

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-27
- **Date closed:** 2026-08-27
- **Decision weight:** heavy
- **Related:** RFC-0031 (catalogue package-manager posture), RFC-0034 (pack profiles), RFC-0085 (catalogue source identity), ADR-0036 (trusted install-source precedence), ADR-0039 (install identity and footprint co-ownership)

## Reviewer brief

- **Decision:** Admit bounded single-skill and multi-skill repositories as direct `agentbundle` install sources without requiring them to become catalogues.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Detect three direct skill-repository shapes after the existing source resolver runs, then normalize them into the pack shape the installer already consumes.
  - Run one dependency-free admissibility gate before any write and reuse existing pack projection, state, dry-run, upgrade, drift, and uninstall machinery.
  - Publish a normative repository-format reference and an author how-to alongside the CLI help and docs-site changes.
- **Affected surface:** `agentbundle install`, `validate`, manifestless skill lifecycle commands, pack state provenance, `pack.toml` schema versioning, public CLI help, author guidance, and the generated documentation site.
- **Stakes:** Costly to reverse once external repositories depend on detection, identity, and compatibility behavior; the remote-source path also crosses network, archive, filesystem, and agent-instruction trust boundaries.
- **Review focus:** Whether normalization genuinely reuses the pack pipeline, whether deterministic validation fails closed before writes, and whether manifestless update identity is stable without inventing a semantic version.
- **Not in scope:** New catalogue transports, recursive ecosystem-wide discovery, private-repository authentication, arbitrary hidden-directory discovery, non-skill direct packs, a hosted registry, or a claim that deterministic validation proves skill prose or scripts safe.

## The ask

**Recommendation (bottom line up front).** Keep catalogue installation unchanged. After the existing source resolver returns a local directory, classify it as a catalogue, a manifest-backed direct skill pack, a manifestless skill collection, or a manifestless single skill. Normalize each direct shape into a temporary canonical pack tree and pass it through the existing validation, projection, install-state, upgrade, drift, and uninstall paths. Refuse ambiguous or mechanically unsafe sources before any write.

**Why now (situation–complication–question).** AgentBundle already installs packs and profiles from any source that resolves to a valid catalogue, but many portable skill repositories publish a root `SKILL.md` or a root `skills/` collection rather than a full `catalogue.toml + packs/` envelope. Requiring every such author to adopt a catalogue adds structure whose registry, profile, and multi-pack capabilities they do not need. A one-shot copier would reach those repositories but discard AgentBundle's differentiators: cross-adapter projection, file safety, provenance, drift, upgrade, and uninstall. The question is whether AgentBundle can admit the common repository shapes without creating a second package manager inside the existing one.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Which direct source shapes are admitted? | Root `pack.toml + skills/`, root `skills/`, and root `SKILL.md` only | Covers the common single and collection forms while keeping discovery bounded. | This review | Confirm the deliberately small discovery surface. |
| D2 | How do direct sources enter installation? | Normalize to temporary canonical packs, then reuse the current pack pipeline | Avoids a parallel projector, safety model, and lifecycle implementation. | This review | Confirm the reuse boundary and its parity tests. |
| D3 | What does the optional manifest mean? | It opts the whole root `skills/` collection into one named, versioned pack lifecycle | Gives authors a clear choice between independently managed skills and a cohesive set. | This review | Confirm that partial direct-pack installation is refused. |
| D4 | How are manifestless skills identified and updated? | One synthetic pack identity per selected skill, backed by source kind, relative path, revision, and content digest in existing pack-keyed state | Preserves current ownership and conflict machinery without inventing a semantic version or a new state hierarchy. | This review | Confirm the state addition is sufficient and not a hidden public pack fiction. |
| D5 | What blocks installation? | A dependency-free deterministic admissibility profile shared by `validate` and `install`; failures are non-bypassable | Authors and adopters must receive the same result before content reaches an agent runtime. | This review | Confirm the mandatory checks and honest limits. |
| D6 | How does the CLI resolve selection and preview? | Extend existing commands; require explicit selection on ambiguity and enrich `--dry-run` | Reuses current UX and remains deterministic in terminals and automation. | This review | Confirm no picker or new preview command is needed. |
| D7 | How is the optional manifest versioned? | Require `schema = 1` for new direct packs; no embedded schema URI; deprecate without removal inside a schema major | Gives external authors a stable contract without adding runtime schema fetching or a perpetual cross-major promise. | This review | Confirm compatibility policy. |
| D8 | What documentation is part of the capability? | One normative format reference, one author how-to, and updates to existing install/help surfaces | Lets a human or agent reshape and verify a repository without learning catalogue internals. | This review | Confirm documentation ships with behavior, not afterward. |

## Problem & goals

### Diagnosis

The current CLI resolves a **catalogue source** and then locates `packs/<name>/pack.toml`. RFC-0085 deliberately defines catalogue identity as root `catalogue.toml` plus root `packs/`. A repository containing only one skill or one `skills/` directory is therefore not an invalid catalogue; it is a different source shape that the CLI does not classify.

AgentBundle already owns the costly parts of installation: scope and adapter resolution, pack validation, primitive projection, per-file planning, collision handling, state and operation logs, drift, upgrade, and uninstall. Adding direct skill repositories by copying folders straight into target-specific skill directories would bypass those controls and create lifecycle behavior inconsistent with catalogue packs.

The authoring path has a related gap. `agentbundle validate` accepts a canonical pack directory, and `agentbundle catalogue lint --deep` accepts a catalogue. A repository author cannot point the CLI at a common greyfield repository—a repository whose content was not authored under AgentBundle's full catalogue conventions—and receive the exact deterministic admission result the installer will enforce.

### Goals

- Install a common single-skill or multi-skill repository without requiring a catalogue.
- Preserve current catalogue behavior and source precedence exactly.
- Make one normalization boundary feed the existing pack validator, projector, planner, state writer, and lifecycle commands.
- Give an optional root manifest a precise meaning: one named and versioned skill set installed as a pack.
- Give manifestless skills stable source-backed identity, update, drift, and uninstall behavior.
- Reject deterministic structural, path, manifest, and collision failures before any write.
- Let authors run the same admission checks locally, with stable machine-readable output.
- Publish a contract that a human or coding agent can use to reshape an existing repository.

### Non-goals

- Discovering `.claude/skills/`, `.agents/skills/`, `.codex/skills/`, or every other runtime's installed projection by default.
- Recursive fallback discovery or implicit traversal of hidden directories.
- Supporting direct agents, hooks, commands, seeds, or shared libraries in the first direct-pack format. A direct pack in this RFC is a skills-only pack.
- Resolving direct-pack dependencies, conflicts, or catalogue recipes. Those relationships still require a catalogue in the first version.
- Adding GitHub shorthand, generic Git, Secure Shell (SSH), private-repository authentication, GitLab, Bitbucket, arbitrary `archive+https`, or direct-repository descriptors. Direct repositories use explicit local paths or the existing GitHub-only, non-credentialed `git+https` route; `catalogue+https` remains catalogue-only.
- Installing a subset of a manifest-backed direct pack.
- Executing publisher code during install.
- Claiming that static checks can determine whether natural-language instructions or arbitrary scripts are benign.
- Creating a registry, dependency solver, lockfile format, new preview command, or interactive skill picker.

## Proposal

### D1 — Bounded source-shape classification

Source acquisition and precedence remain governed by ADR-0036 and RFC-0085. Classification occurs only after the existing resolver has produced a local directory. It uses root markers and confined reads in this order:

| Shape | Required root markers | Install selection |
| --- | --- | --- |
| Catalogue | `catalogue.toml` and `packs/` | Existing `--pack` or `--profile` behavior |
| Direct skill pack | `pack.toml` and `skills/<name>/SKILL.md` | Whole pack only |
| Manifestless collection | `skills/<name>/SKILL.md`, no `pack.toml` | One or more explicit skills, or `--all-skills` |
| Manifestless single | `SKILL.md`, no `pack.toml` and no root `skills/` collection | The single skill |

The root `skills/` form admits direct child skill directories only. A directory without `SKILL.md` is not a skill. Names beginning with `.` are not discovered. A caller may pass a local path that already points at one skill directory; support for a remote arbitrary subpath or repository-tree URL is deferred with the transport work.

Catalogue markers win because they identify an existing supported contract. All other overlap is refused rather than resolved by precedence. In particular, root `SKILL.md` plus a discoverable root `skills/` collection is ambiguous, as is root `pack.toml` plus root `SKILL.md`. The diagnostic lists the detected shapes and the exact supported recovery: remove the duplicate source surface or point at one local skill directory.

The classifier does not scan runtime-specific directories. Those directories commonly contain generated or already-installed projections; treating them as authoring source would duplicate skills and risk re-exporting content the repository does not own.

The transport is known before the shape is. In the first version, only an explicit local path or the existing GitHub-only `git+https` source may carry a direct repository. Before direct support ships, that GitHub resolver must be hardened to accept only HTTPS `github.com` repository identities, follow redirects only to the fixed GitHub/codeload host set, send no AgentBundle bearer token, publisher credential, cookie, or caller-supplied authorization header, and enforce the existing archive subsystem's 256 MiB download, 20,000-member, 1 GiB expanded-size, timeout, and safe-extraction boundaries before classification. The current GitHub resolver does not yet enforce all of those limits; reusing it unchanged is not conforming implementation. `catalogue+https` remains a catalogue-channel descriptor and must resolve to a catalogue; it is never reclassified as a direct repository and its bearer-token path is never used for one. `archive+https` also remains outside direct classification until a separate host, redirect, DNS/IP-range, credential-forwarding, and integrity contract is approved. Post-extraction confined inventory enforces the per-file, total-tree, count, nesting, and entry-type limits. Supporting another transport requires its own trust and resource contract rather than falling through classification.

### Existing concepts relied upon

- The **source resolver** turns an explicit source string into a local directory plus provenance; it does not decide what repository shape that directory contains.
- A **canonical pack** is the existing internal `pack.toml` plus `.apm/skills/` input consumed by validation and rendering. **Projection** is the adapter-specific transformation of that input into target files. An **adapter** names a target runtime, while **scope** names the destination level such as repository or user.
- A **confined read or inventory** walks only regular files beneath an already validated root without following links. A **skill envelope** is one admitted skill directory: `SKILL.md` plus the allowed payload directories defined in D5.
- **Pack-keyed state** is the existing installed-state row keyed by pack name and adapter. The existing **source-conflict policy** refuses reuse of that identity by another source. A **platform-poisonous name** is a path segment the existing pack tooling rejects because it is reserved or unsafe on a supported filesystem.

### D2 — Normalize, then install

The new code produces a temporary canonical catalogue fragment rather than adding a direct-source branch to every downstream subsystem:

```text
resolved source
      │
      ▼
classify + confined inventory
      │
      ▼
temporary root/packs/<identity>/
├── pack.toml
└── .apm/skills/<skill>/...
      │
      ▼
existing validate → render → plan → install → state path
```

Normalization uses the standard library and the repository's confined-file helpers. It copies only the selected skill envelopes into an approved temporary directory; it does not symlink source content into the normalized tree. Files are read through the same no-follow, regular-file boundary used by catalogue tooling. The direct source remains the recorded provenance; the temporary path never enters durable state or user-facing receipts.

A direct skill pack reuses its root `pack.toml` and maps every admitted `skills/<name>/` directory to `.apm/skills/<name>/`. A manifestless skill receives the smallest generated `pack.toml` needed by the existing pipeline. Because that pipeline requires a version, the generated manifest uses the reserved constant `0.0.0+agentbundle.manifestless`; a publisher-supplied direct pack may not claim that value. The generated manifest and sentinel are internal adapters, not files written into the publisher's repository or public release identities.

The implementation must expose one library function that both `validate` and `install` call. A validation path that merely resembles installation is insufficient: construction tests must prove that the normalized inventory and diagnostics are the same for both callers.

### D3 — Manifest-backed pack semantics

Root `pack.toml` is optional. When present beside root `skills/`, it declares one direct skill pack:

- `[pack].name` is the install identity.
- `[pack].version` is the pack's semantic version.
- `[pack.install]` may declare the existing scope and adapter constraints.
- Every admitted direct child under `skills/` belongs to the pack.
- Installation, upgrade, drift reporting, and uninstall operate on the whole set.

For a direct pack, schema 1 deliberately admits only the existing fields required to name, describe, and constrain installation: required `[pack].name` and `[pack].version`; optional `[pack].description`, `[pack].license`, `[pack.adapter-contract]`, and `[pack.install]`. This is the same pack-manifest schema major with an additional direct-source profile, not a second meaning for the fields. If `install` is absent, the existing defaults apply: repository scope, local scope by repository-scope opt-in, and no manifest-level adapter restriction. CLI scope and adapter precedence remain unchanged. Catalogue metadata, rich display metadata, runtime-dependency declarations, profiles, recipes, dependencies, adaptation, seeds, and declarations for non-skill primitives are refused even if the broader catalogue-pack schema knows those fields. Unknown keys fail closed. The normative author reference owns this subset and links its schema by version.

`--skill` and `--all-skills` are refused for this shape. Partial installation would make the manifest ambiguous about version, tests, and ownership. An author who wants independently managed skills omits `pack.toml`; a caller cannot override the author's selected lifecycle at install time. “Whole pack” means indivisible selection, upgrade identity, drift reporting, and ownership; it does not add a new transactional or rollback guarantee beyond the existing multi-pack installer.

The first version supports skills only. Existing catalogue packs remain the route for agents, hooks, commands, seeds, shared libraries, profiles, and cross-pack dependencies. A direct `pack.toml` that declares or relies on unsupported primitive surfaces fails validation with a specific diagnostic rather than silently dropping content.

Direct packs also refuse `[pack.dependencies]` and catalogue recipes in the first version. Resolving those declarations would require a second source lookup and composition policy, neither of which is needed to install one repository's skill set.

### D4 — Manifestless identity and lifecycle

Each selected manifestless skill is normalized as one synthetic single-skill pack whose identity is the validated skill name. Installing several selections in one command reuses the existing multi-pack preflight and installation path; it does not create a durable collection object.

The durable state remains keyed by `(pack name, adapter)`. Every direct-source row, including a manifest-backed pack, records a content digest. A manifestless row also gains the provenance required to reconstruct one skill:

- `source-kind = "skill"`;
- `source-path`, a confined repository-relative path to the skill directory;
- `source-digest`, a SHA-256 digest over the admitted canonical relative-path and file-byte inventory;
- existing `source` and `source-revision` fields where the transport supplies them.

The state schema advances from 0.4 to 0.5. The new CLI reads 0.4 and 0.5, upgrades to 0.5 on the next state mutation, and writes new direct rows only as 0.5. An existing pack row gains no direct fields during that rewrite. Older CLIs reject 0.5 with an upgrade instruction rather than discarding unknown provenance. Tests pin 0.4-to-0.5 loading, mixed legacy/direct rows, byte-stable preservation of absent optional fields, and fail-closed behavior in an old-reader fixture. `source-path` is never interpreted before the resolved source root is re-established and confinement is rechecked.

The digest algorithm is part of state schema 0.5. A manifestless skill hashes logical paths relative to its envelope (`SKILL.md`, `scripts/...`); a direct pack hashes `pack.toml` plus each envelope under `skills/<validated-name>/...`. Repository files outside that set, directories, timestamps, and ownership are excluded. Each logical path must already be Unicode NFC, uses `/` separators, and is UTF-8 encoded; case-fold collisions are refused before hashing. Entries sort by their encoded path bytes. SHA-256 receives, for each entry, an unsigned 64-bit big-endian path-byte length, the path bytes, one execute-metadata byte (`0x00` = known absent, `0x01` = present, `0x02` = unavailable), an unsigned 64-bit big-endian content length, and the exact content bytes. Empty directories therefore have no identity. A future algorithm change requires a named digest-version migration rather than silently changing comparison.

Manifestless skills have no semantic package version in the agentskills.io format. Their state row may carry the reserved internal sentinel only to satisfy the existing pack-state type. Whenever `source-kind = "skill"`, `list-installed`, receipts, JSON, update detection, and lifecycle code must neither expose nor compare that value; they identify the unit as a skill and report its revision or digest. Update availability means that the currently resolved confined envelope has a different source digest, not that one pseudo-version sorts above another. Direct-pack receipts and drift reporting also show the digest, and a mutable transport revision or unchanged `[pack].version` cannot conceal changed admitted bytes. `upgrade --skill <name>` without `--pack` re-resolves a manifestless skill's recorded source and path, re-runs admissibility, previews the file plan under existing rules, and replaces it. The existing `upgrade --pack <pack> --skill <primitive>` combination keeps its current meaning: select one primitive inside a catalogue pack. `uninstall --skill <name>` routes to the same pack-keyed file-ownership removal path. Existing pack lifecycle syntax otherwise remains unchanged.

A skill name collision with an installed pack or another skill from a different source is refused by the existing source-conflict policy. For that comparison, a direct identity is `(source-kind, canonical source, source-path)`: a direct pack uses `source-kind = "pack"` and the empty path; a manifestless skill uses `source-kind = "skill"` and its confined repository-relative path. Revision and digest describe a version of that identity and may change only through upgrade; they do not make a colliding install a new source. Scope and adapter remain the existing outer state/ownership dimensions. The user must remove or rename one identity; `--force` does not choose a source.

### D5 — Shared deterministic admissibility gate

`agentbundle validate <path>` expands from "canonical pack directory" to "supported source directory." To preserve current behavior, a path with the existing canonical `pack.toml + .apm/` markers takes the current canonical-pack validator directly and does not enter direct-source classification; a regression fixture pins `validate packs/<pack>`. All other paths use the D1 classifier, inventory, normalization, and existing validators. `--format json` returns stable diagnostics and the detected shape; `--deep` retains the stronger authoring checks that require the optional lint dependencies.

Before any direct-source write, install runs the dependency-free baseline from the same library. Mandatory failures include:

- an unsupported, empty, or ambiguous root shape;
- unsafe or unresolvable root, skill, manifest, or file paths;
- symbolic links, hard links, junctions, reparse points, devices, first-in-first-out nodes, or other non-regular payload entries;
- path traversal, absolute payload paths, case-insensitive collisions, and platform-poisonous names already rejected by pack tooling;
- configured file-count, total-byte, per-file-byte, and nesting limits, enforced during remote acquisition as well as after extraction;
- unreadable or non-UTF-8 `SKILL.md` content and size violations;
- missing or malformed frontmatter; a missing, invalid, or out-of-bounds scalar `name` or `description`; an unknown top-level key; or a YAML tag, anchor, or alias in a field the baseline consumes;
- a collection or direct-pack child whose directory name differs from its validated frontmatter name, an invalid name, or a duplicate name. For a root single or a local path that itself points at a skill, the frontmatter name is authoritative because the checkout directory is transport-controlled;
- invalid `pack.toml`, unsupported manifest schema, or unsupported direct-pack content;
- a pack name or version that fails the existing bounded identifier and Semantic Versioning checks, or an admitted description/license value containing control characters or exceeding its schema-1 length bound;
- a source-identity or destination ownership collision found by existing preflight.

The baseline uses the bundled schema and standard-library parsing. It cannot change based on whether optional PyYAML, Bandit, Semgrep, or a software-composition-analysis scanner happens to be installed. A mandatory check that cannot complete is a failure, not a warning. `--force` and `--yes` cannot bypass these failures.

The baseline skill contract requires scalar `name` and `description` fields and permits the existing top-level `license`, `compatibility`, `metadata`, and `allowed-tools` fields. It consumes only the required scalars and the bounded security-summary fields; it does not deserialize publisher-defined YAML objects or execute tags. For a collection or direct pack, each selected child envelope may contain `SKILL.md` and confined regular files beneath `scripts/`, `references/`, `assets/`, and `evals/`; another entry inside that child, a hidden entry, or a link-like or special file fails. For a root single or a local path already at a skill, only `SKILL.md` and those four named payload directories form the envelope; other regular root entries are repository context and are ignored. In every shape, ignored content is never normalized, hashed, reported as installed, or projected. Full nested type and agentskills.io conformance remains a `--deep` check. The bundled versioned contract and the public reference are authoritative; the reference also links to the dated upstream [Agent Skills specification](https://agentskills.io/specification).

`--deep` remains an author and assimilation check. It may run the full agentskills.io lint and the repository's declared static-analysis and dependency scanners, but those tools do not become runtime dependencies of the base installer. Assimilation continues to add raw-body inspection, explicit confirmation for executable code, and reviewer reasoning against the Agentic Skills security checklist.

A passing baseline is reported as **admissible**, not safe. It proves that the selected bytes meet the declared deterministic transport, tree, metadata, and ownership contract. It does not prove that natural-language instructions are non-malicious, that requested permissions are least-privilege, or that arbitrary scripts contain no vulnerability. A skill is **script-bearing** when its admitted envelope contains any regular file below `scripts/`; install copies or projects those bytes but never executes publisher code, while a runtime agent may later act on the installed instructions or invoke a script. **Executable-mode presence** means at least one admitted regular file has any source POSIX execute bit set; transports or platforms without trustworthy mode metadata report `unknown` and do not guess from an extension or shebang. `validate --format json`, `install --dry-run`, and the confirmation summary preserve and report, per skill, `allowed-tools`, `metadata.boundaries`, `metadata.credentialed`, script presence, and executable-mode presence. Missing declarations are shown as undeclared rather than inferred safe.

Before a remote direct-source install mutates a target, the existing `--yes` mechanism confirms that summary together with source, revision and digest, selections, scope, adapter, and destination. An interactive local direct install follows existing mutation confirmation behavior and adds no remote-trust prompt. A non-interactive remote direct install must pass `--yes`; `--dry-run` never prompts or writes. No new confirmation framework is introduced.

### D6 — CLI selection, preview, and receipts

The existing `install` grammar becomes source-aware while preserving all current catalogue forms:

```text
agentbundle install --pack <name> [catalogue]
agentbundle install --profile <name> [catalogue]
agentbundle install <direct-source>
agentbundle install <manifestless-source> --skill <name> [--skill <name> ...]
agentbundle install <manifestless-source> --all-skills
```

Representative complete forms are:

```console
agentbundle install ./skills-repository --skill code-review --scope repo --adapter codex
agentbundle install 'git+https://github.com/acme/skills@v1.2.3' --all-skills --scope user --adapter claude --yes
agentbundle upgrade --skill code-review --scope repo --adapter codex
agentbundle uninstall --skill code-review --scope repo --adapter codex
```

`catalogue+https` and `archive+https` are deliberately absent: neither may carry a direct repository in v1.

Rules:

1. `--pack` and `--profile` retain current catalogue semantics.
2. With neither, the positional source is required and must classify as a direct shape.
3. A single manifestless skill needs no selector.
4. A collection with no selector prints the sorted candidates and exact `--skill` / `--all-skills` commands, then exits non-zero. It never silently installs all skills and does not open an interactive picker.
5. `--skill` is repeatable and rejects unknown or duplicate names before any write.
6. `--dry-run` performs the complete resolve, classify, validate, normalize, projection, and per-file planning path without mutation. Its summary adds source identity, detected shape, selected units, script presence, scope, adapter, and provenance before the existing file plan.
7. A successful command prints a receipt with installed kind and name, source, revision and digest, scope, adapter, and the matching update and uninstall commands.

`list-installed` adds a `KIND` column whenever the displayed result contains at least one manifestless skill and always includes `kind` in JSON; pack-only table output remains unchanged. Existing pack rows remain meaning-compatible. For `upgrade`, standalone `--skill` selects an installed manifestless skill while `--pack P --skill S` retains the existing primitive-within-pack meaning; the parser reports that distinction in help and rejects ambiguous combinations. Standalone skill upgrade admits repository, user, and local scope; the existing pack-upgrade scope contract is unchanged. `uninstall --skill` is mutually exclusive with `--pack`. Scope and adapter disambiguation follow the existing commands. These are thin selectors over the same pack-keyed state and file-ownership paths, not separate lifecycle engines.

### D7 — Manifest schema versioning and compatibility

New direct skill packs declare the manifest contract explicitly:

```toml
schema = 1

[pack]
name = "example-skills"
version = "1.0.0"
```

`schema` is the manifest-format version. `[pack].version` is the published pack version. Existing catalogue pack manifests without `schema` remain implicit schema 1 and continue to validate; scaffolds and new direct-pack documentation emit the explicit field.

The manifest does not carry a schema URI. AgentBundle validates against its bundled schema, and the public author reference links to a stable versioned schema resource. Embedding an arbitrary URI would add a second identifier, mismatch rules, and pressure to fetch publisher-controlled URLs during validation without improving runtime dispatch.

Compatibility follows three rules:

1. A field is not removed, repurposed, or made newly required inside one schema major.
2. A deprecated field remains accepted in that major, is marked deprecated in the JSON Schema, produces a coded warning with its replacement, and is omitted from new scaffolds.
3. Removing or changing a field's meaning requires a new schema major and a documented migration. The project does not promise that every future CLI supports every old major forever; supported majors are published explicitly, and an unsupported major fails closed with an upgrade or migration instruction.

Security validation remains independent of syntactic compatibility. A value admitted by an older schema may still be refused when using it would violate a current path, integrity, or execution-safety control; such refusals require a specific diagnostic and release note.

### D8 — Author contract, help, and documentation site

The capability is incomplete until a repository author can reshape and verify a source without reading AgentBundle internals. The same release adds:

- `guides/_shared/reference/skill-repository-format.md`: the normative root shapes, detection order, ambiguity rules, direct-pack manifest, independent-skill contract, security baseline, diagnostics, compatibility policy, and stable raw schema link;
- `guides/_shared/how-to/make-a-skill-repository-installable.md`: a task-focused migration from root skill or loose collection to root `skills/`, the optional manifest decision, self-containment checks, `validate --deep`, and local `install --dry-run`;
- a copyable prompt that tells a coding agent to read the normative format, preserve unrelated repository content and tests, keep every manifestless skill self-contained, optionally add the manifest only when indivisible selection and lifecycle ownership are intended, run validation, and present the diff;
- updates to the existing install-routes and AgentBundle reference pages;
- `agentbundle install --help`, `validate --help`, `upgrade --help`, and `uninstall --help` examples covering the supported direct forms, ambiguity recovery, dry-run, non-interactive confirmation, and lifecycle;
- generated docs-site navigation, build, and rendered-link verification through the existing `guides/` publication path.

The documentation set stays deliberately small. The author how-to owns the first-value journey; the format reference owns durable contract detail. Separate tutorial, migration, security, and explanation pages are deferred until their content can no longer remain coherent in those two pages.

## Options considered

The main design axis is where direct-source compatibility enters the existing system.

| Option | Trade-off |
| --- | --- |
| Require every repository to become a catalogue (do nothing) | Reuses everything, but imposes catalogue metadata and a `packs/` hierarchy on authors distributing one skill or one cohesive collection. |
| Copy selected skills directly into each runtime's skill directory | Small initial implementation, but bypasses adapter projection, pack validation, state ownership, drift, upgrade, and uninstall. It creates the second installer this RFC is trying to avoid. |
| Add a new generalized install-unit model and parallel state hierarchy | Makes pack and skill identities theoretically uniform, but rewrites mature lifecycle code before a second primitive kind requires it. |
| **Normalize direct shapes into existing packs** | Adds a bounded adapter and small provenance fields while retaining the established installer. This is the recommended first rung. |

Discovery breadth is a separate axis. Ecosystem installers commonly inspect many runtime-specific paths or recurse when no known root is found. AgentBundle instead admits the two source roots users can author intentionally—`SKILL.md` and `skills/`—and rejects ambiguity. Explicit remote subpaths and more source locations can be added later from observed demand without weakening the initial contract.

## Risks & what would make this wrong

### Pre-mortem

- **Normalization becomes a validation bypass.** If direct installation calls a lighter validator or copies bytes after validation through a different path, source and canonical packs diverge. Mitigation: one normalize-and-validate library, confined descriptor reads, and parity fixtures whose canonical pack and direct-source projections are byte-identical.
- **Synthetic skill identity leaks as fake package versioning.** A hash or commit presented as Semantic Versioning would produce misleading ordering. Mitigation: state records kind, path, revision, and digest explicitly; human and JSON outputs distinguish skills from versioned packs.
- **An update resolves a different path than the installed skill.** Repository contents can move or a relative path can be replaced by a link. Mitigation: record the relative path, re-establish the source root, rerun confinement and shape validation, and refuse missing or renamed identities rather than guessing.
- **Broad discovery installs generated or attacker-hidden content.** Mitigation: direct children under root `skills/` only, no dot directories, no recursive fallback, and ambiguity refusal.
- **A remote repository exhausts disk or memory before post-fetch validation.** Mitigation: apply the existing bounded download and extraction limits to the GitHub direct-source acquisition path, then enforce expanded-tree limits during inventory.
- **A passing report is mistaken for a malware verdict.** Mitigation: use `admissible`, enumerate the checks performed, label script presence, require remote confirmation, and document the natural-language and code-analysis limits.
- **Manifest evolution becomes permanent compatibility debt.** Mitigation: compatibility is durable within a schema major, not an unbounded promise across all future majors.

### Falsifiable assumptions

- **The pack pipeline is reusable after layout normalization.** Falsified if direct skill content requires a distinct projection or ownership rule. Current build inventory already treats a skill as a self-contained directory under `.apm/skills/`, so the source-path difference is representational rather than behavioral.
- **Existing pack-keyed state can represent manifestless skills with small provenance additions.** Falsified if upgrade or uninstall needs a durable collection entity or dependency graph. The proposed lifecycle installs each manifestless skill independently and uses the current per-name source-conflict and file-ownership model.
- **Dependency-free baseline validation is meaningful.** Falsified if required agentskills.io metadata cannot be checked without an optional parser. The existing catalogue linter already performs dependency-free frontmatter presence and bounded-field checks; `--deep` remains the optional full-conformance layer.

### Drawbacks

- A skills-only direct pack is narrower than a catalogue pack, so authors needing hooks, agents, commands, seeds, dependencies, or profiles must still adopt a catalogue.
- Manifestless skills gain digest-based update detection rather than semantic release comparison.
- The same skill name cannot coexist from two sources at one scope and adapter.
- Direct-source normalization adds temporary copying and hashing cost before every install or update.
- Existing remote source syntax remains less paste-friendly than tools accepting bare `OWNER/REPO`; this is intentionally deferred rather than bundled into the trust-boundary change.

## Evidence & prior art

### Repository evidence

- RFC-0085 defines catalogue identity as `catalogue.toml + packs/`; this RFC adds sibling source shapes after resolution rather than weakening that identity.
- ADR-0036 makes source selection a provenance boundary and rejects current-working-directory discovery. Direct sources therefore remain explicit and use the existing trusted precedence and transport path.
- ADR-0039 establishes pack/adapter install identity and shared file ownership. One synthetic pack row per manifestless skill preserves that model.
- `packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py` already supplies confined directory walks, no-follow regular-file reads, hard-link refusal, size bounds, and confined hashing.
- `agentbundle install --dry-run` already executes a non-mutating per-file plan; extending its summary is smaller than adding preview infrastructure.
- `agentbundle validate`, `catalogue lint --deep`, the build renderer, and the installed-state lifecycle already divide baseline, deep authoring, projection, and ownership responsibilities. The proposal composes them rather than duplicating them.

### External prior art

- [Vercel `skills`](https://github.com/vercel-labs/skills) accepts single- and multi-skill repositories, supports explicit skill selection, and searches several common skill roots. Its broad discovery demonstrates ecosystem demand; its root precedence and recursive fallback also show why AgentBundle should refuse ambiguity instead of silently shadowing candidates.
- [GitHub CLI skill installation](https://cli.github.com/manual/gh_skill_install) supports repository and local sources, exact skill selection, hidden-directory opt-in, pinning, multiple agents, and provenance-bearing installation metadata. AgentBundle adopts explicit selection and provenance while retaining its own adapter and scope model.
- [GitHub CLI skill preview](https://cli.github.com/manual/gh_skill_preview) shows the value of inspecting a skill tree and body before installation. AgentBundle folds the corresponding source, risk, and file-plan summary into its existing `--dry-run` rather than adding another command.
- [Claude Code plugin discovery](https://code.claude.com/docs/en/discover-plugins) separates finding a marketplace from installing a plugin and presents scope plus the components that will be installed. AgentBundle keeps catalogue registration separate and adopts a concise direct-source “will install” summary.

### De-risk result

The easiest-looking design—a first-class generalized install-unit hierarchy—was tested against current state and command ownership and rejected. Installed state is deliberately keyed by `(pack name, adapter)`; source conflicts, file ownership, list, drift, upgrade, and uninstall all build on that key. A direct skill has the same projected payload and ownership needs as a one-skill pack. Normalizing it to that existing unit and adding source kind/path/digest is sufficient for the proposed scope. A new hierarchy would add abstraction without a second behavior that needs it.

## Experiment / validation

Implementation is accepted only when the following construction evidence passes:

1. **Shape matrix:** positive fixtures for catalogue, direct pack, collection, single skill, and local path already at a skill; negative fixtures for every ambiguous overlap and unsupported nested/hidden shape.
2. **Normalization parity:** the same skill bytes authored once as a canonical pack and once as each direct shape produce byte-identical adapter projections and file plans.
3. **Safety mutations:** traversal, link, junction/reparse where supported, hard-link, device/FIFO, case collision, poisonous name, oversized remote artifact/tree/file, malformed UTF-8, invalid frontmatter, and manifest mismatch fixtures all fail before any target or state write.
4. **Lifecycle steel thread:** dry-run, install, list, source-change detection, `upgrade --skill`, drift, and `uninstall --skill` for repo, user, and local scope across representative shared-prefix and adapter-specific targets.
5. **State compatibility:** existing state files load and round-trip without acquiring direct-source fields; manifestless rows preserve kind/path/digest and the reserved internal version; `list-installed`, receipt, JSON, drift, and upgrade fixtures prove the sentinel is never exposed or used for ordering; source conflicts remain non-bypassable.
6. **CLI behavior:** one unit proceeds; multiple units without selection list and refuse; repeated and all selection behave deterministically; non-interactive remote install requires `--yes`; standalone `upgrade --skill <installed-skill>` selects a manifestless row; existing `upgrade --pack <pack> --skill <primitive>` retains its current meaning; ambiguous selector combinations fail with the documented diagnostic; JSON contracts and exit codes are pinned.
7. **Validator parity:** every mandatory failure emits the same diagnostic from explicit `validate` and install preflight.
8. **Documentation proof:** every documented command is exercised against a fixture, CLI help snapshots pass, guide validation succeeds, the generated docs site builds, and rendered links resolve.
9. **Security review:** path-and-file, outbound acquisition, supply-chain, exceptional-condition, and agentic-skills checklist findings are resolved before implementation merges.

Failure of normalization parity or lifecycle replay invalidates the recommended design and requires returning to the RFC rather than adding direct-source special cases downstream.

## Open questions

None. Discovery roots, normalization, manifest semantics, state identity, validation depth, CLI behavior, schema policy, and documentation scope are decided together.

## Follow-on artifacts

- ADR recording direct-source classification after source resolution, normalization into canonical packs, manifest-backed versus manifestless lifecycle identity, and schema-major compatibility.
- Feature spec and plan under `docs/specs/direct-skill-repository-installation/` covering the construction matrix above.
- `contracts/pack.schema.json` and bundled-schema update for explicit `schema = 1`, with legacy implicit-v1 acceptance.
- Public `skill-repository-format` reference and `make-a-skill-repository-installable` how-to, plus existing install-route and CLI reference updates.
- Current-state architecture updates to catalogue, skill-and-pack format, pack manifest, AgentBundle command/state, and security pages after implementation ships.
- Release notes naming the new source shapes, manifestless digest lifecycle, deterministic admission boundary, and compatibility limits.

## Current normative state

For credential-free `git+https` sources, E11 owns the **Family 1 acquisition bounds**, redirect equivalence, and runtime floor on both direct and catalogue routes. They attach to every credential-free `git+https` transport fetch, not only a fetch before classification, so a `list-installed --check` status probe carries them unchanged. A full 40-hex requested ref must equal the archive-derived SHA.

For direct sources, E11 owns the **Family 2 measured-envelope bounds** and evaluation order; E13 owns direct candidate-rooting and root-context disposition. E14 owns the recognised collection roots and the optional one-level category grouping. E15 owns the path-depth bound and its origin. Local paths receive Family 2 only. E1–E4, E6–E10, and E12 remain in force as written. E5 continues to govern library-resolved per-member destination and link-target confinement, and delegates filter mode and ownership behavior to the standard library; it also governs direct-only post-extraction refusal of links and special entries encountered in a candidate path. Catalogue `git+https` symlink support and catalogue selector/precedence behavior remain unchanged.

## Errata

The RFC body above this current-state layer is preserved as the original accepted decision record. These dated, approver-signed corrections govern where that body conflicts with verified repository behavior or later approved decisions.

### E1 — `validate --deep` is refused, not added

**2026-08-27 — Approver: eugenelim.** The body says `agentbundle validate --deep` retains an existing stronger authoring check. That does not hold: only `catalogue lint --deep` exists, and it accepts a catalogue rather than a direct repository. Rather than build that surface, it is now an explicit non-goal. The admitted direct shapes are a root `skills/` collection or a root `SKILL.md`, which the dependency-free baseline already decides, so a deep conformance pass earns nothing the baseline does not already give an author. Deep agentskills.io conformance remains a catalogue concern under `catalogue lint --deep`. Consequences: the author how-to documents plain `validate`; the whole direct path stays dependency-free, removing the optional-PyYAML behaviour contract that would otherwise have sat against the no-runtime-dependency rule; and an author wanting full conformance linting adopts a catalogue.

### E2 — Digest is content-only

**2026-08-27 — Approver: eugenelim.** D4 says the execute-metadata byte is included in the digest. That does not hold because mode availability differs by platform and would create phantom updates. The digest is now sorted path/content entries only: for each entry SHA-256 receives u64be path-byte length, path bytes, u64be content length, and exact content bytes; entries sort by encoded path bytes and include no execute byte. Executable-mode presence is reported in the security summary but is computed at report time and never persisted. The existing `safety.write_jailed` call-site default creates installed direct payloads non-executable, so a source-side bit does not change what lands on disk. A mode-only change is therefore not an update and is not tracked.

### E3 — State migration is lazy and direct-only

**2026-08-27 — Approver: eugenelim.** D4 says every next state mutation upgrades 0.4 to 0.5. That conflicts with ADR-0039’s rollback posture and needlessly changes catalogue-only installations. Readers accept 0.4/0.5, and a mutation writes `max(existing, 0.5 if it adds or updates a direct-source row else 0.4)`: catalogue-only state stays 0.4 when it began there, while an existing 0.5 file is never downgraded.

### E4 — Remote refs resolve to commit SHAs

**2026-08-27 — Approver: eugenelim.** D1/D6 admit the existing GitHub route without a pin, including a default `main`; ADR-0036 accepted that residual only for an upstream public default. That scope no longer holds for arbitrary direct instruction repositories. Remote direct installation refuses bare/defaulted `main`, resolves an explicit branch or tag to a full commit SHA, and records it as `source-revision`. The recorded SHA must be **derived from, or verified against, the acquired archive bytes**, so that it attests to the content actually installed. A separate out-of-band resolution request is not required; if one is made it is uncredentialed, locked to the same GitHub host set, byte-capped and deadline-bound, and the acquired archive must still be verified to correspond to the resolved SHA — otherwise a force-push between the two requests lets `source-revision` attest to a commit the user never received.

### E5 — Shared resource controls, direct-only link refusal

**2026-08-27 — Approver: eugenelim.** D1 says the shared resolver inherits all archive safe-extraction boundaries. That would reject catalogue symlinks, including self-hosted catalogue members. Download/member/expanded-size caps, the acquisition deadline, origin-locked redirects, **and per-member destination validation** apply to the shared path: before any member is written, evaluate the library-resolved `TarInfo.name` and `.size`, never a reconstructed member name; validate its destination, and refuse absolute paths, `..` components, Windows separators, and any destination resolving outside the extraction root. Pax global attributes can override later member `path` and `size`. For every admitted link, `linkname` must be relative and its resolved target must remain below the extraction root; the per-member loop calls `tf.extract(member, path=…, filter="data")`, so the standard library owns its filter’s mode and ownership behavior. Case-fold collisions and device/FIFO refusal apply to both credential-free routes; only symlink and hard-link admission/refusal is direct-only. Direct post-extraction inventory also refuses junctions/reparse points and other special entries, while a catalogue legitimately carries symlinks. A symlinked GitHub catalogue remains a regression case. Replacing the current bulk `extractall(filter="data")` with a per-member loop does not license dropping the destination, link-target, data-filter, or direct-only admission controls that call was providing.

### E6 — Bounds are baseline-validator rules

**2026-08-27 — Approver: eugenelim.** D5 suggests schema-1 length bounds can be expressed in the JSON Schema. The repository’s stdlib schema subset ignores unsupported length keywords. Control-character and byte-length limits on publisher-controlled values are enforced in baseline validator code, not by new schema keywords.

### E7 — Help verification is structural

**2026-08-27 — Approver: eugenelim.** The validation list calls for CLI help snapshots. No snapshot framework exists, while the established tests inspect parser actions and help fields structurally. Help obligations use structural parser assertions, not rendered-help substring checks or a new dependency.

### E8 — GitHub archive components are validated and encoded

**2026-08-27 — Approver: eugenelim.** The body treats parsed GitHub owner/repo/ref as safe for raw archive-URL interpolation. The current ref capture permits path and URL metacharacters, so a crafted ref can traverse to a different repository while state attests the pasted source. Owner, repo, and ref must be GitHub-character validated; dot segments, `?`, `#`, and controls refuse; path segments are percent-encoded; and the assembled URL is re-parsed and verified as `https://github.com/<owner>/<repo>/archive/...` before request.

### E9 — Manifestless display uses `-`

**2026-08-27 — Approver: eugenelim.** D6 adds `KIND` but leaves the manifestless version cell undefined. Rendering the internal sentinel would violate D4. Manifestless rows render `—` in `INSTALLED`; JSON omits version, and the same rule applies to `show`.

### E10 — Direct-pack `source-path` is absent

**2026-08-27 — Approver: eugenelim.** D4 says a direct pack uses `source-kind = "pack"` and the empty path. That does not hold: an empty path is ambiguous with a malformed relative path and conflicts with the direct-state confinement contract. Direct-pack `source-path` is absent; absence and an empty value are distinct, and an empty value is invalid. The direct-state representation governs this distinction.

### E11 — Transport acquisition and measured-envelope bounds

**2026-08-27 — Approver: eugenelim.** The RFC body’s 256 MiB / 20,000-member / 1 GiB figures are the descriptor-route constants in `https_catalogue.py`; the credential-free `git+https` route in `catalogue.py` does not apply them. The earlier 10 MiB / 25 MiB / 1,000-member model was in the spec draft, not this RFC, and bound the wrong object for a whole-repository archive. E11 supersedes E5’s resource-bound, acquisition-deadline, and redirect-policy clauses with two distinct families. **Acquisition bounds** attach to every credential-free `git+https` transport fetch before classification, catalogue or direct: 256 MiB downloaded, 20,000 members, 1 GiB incrementally measured decompressed bytes on the decompressed side of gzip and tripping mid-read, a 30-second socket timeout, and a 90-second inactivity/stall timeout. The socket timeout necessarily fires first during acquisition stalls; the 90-second inactivity code is therefore reachable only during extraction. There is no separate total elapsed-time deadline. The residual that a slow drip can reset the socket and inactivity timers is accepted for this decision; the acquisition module exposes injectable clock/progress seams so deadline tests lower the defaults deterministically. At most five HTTPS-only, user-info-free redirects are allowed; each target is either `github.com/<owner>/<repo>/archive/<ref>` or `codeload.github.com/<owner>/<repo>/tar.gz/<ref>` for the requested owner, repository, and ref, compared in the same percent-encoded form as requested. The existing `git+https` catalogue route gains its first byte/member/expanded bounds and redirect handler. **Measured-envelope bounds** apply in two phases during direct candidate enumeration and selected-envelope admission: enumeration checks entries (2,500), then depth (12, per E15), then files (1,000); candidate selection derives from that bounded enumeration and is capped at 500. After enumeration, the read phase checks per-file size (1 MiB, including `SKILL.md`) and then total size (25 MiB). The entry count is passed as `max_entries` during confined traversal; `max_files` alone does not bound a directory-only tree. Values equal to a bound are allowed and values greater than it refuse. The direct per-file bound dominates the unchanged 2 MiB `max_skill_bytes` and 1 MiB `max_pack_toml_bytes` discovery ceilings, which are never reached on this route. Local paths take the latter family only. Neither family is raised by environment, flag, or configuration. Before the first `tf.extract`, `direct_source_acquisition.py` reads `sys.version_info` at call time: a minor below 3.11 refuses, 3.11 needs patch 13 or later, 3.12 patch 11 or later, 3.13 patch 4 or later, 3.14 patch 0 or later, and a minor above 3.14 is allowed; `packages/agentbundle/pyproject.toml` remains advisory only.

### E12 — Payload disclosure covers the measured payload directories

**2026-08-27 — Approver: eugenelim.** The accepted body defines script-bearing content through `scripts/` and describes script presence. The direct security summary now discloses measured non-`SKILL.md` payload files under `scripts/`, `references/`, `assets/`, and `evals/`, with their digests. This widens disclosure only; it does not alter the admission boundary or authorize execution of any payload.

### E13 — Root repository context is outside direct enumeration

**2026-08-28 — Approver: eugenelim.** The body’s root-single/local-path wording says other regular root entries are ignored, but did not cover hidden root entries, direct-pack and collection roots, or state whether ignored context participates in the direct bounds. That gap made a direct installation of an ordinary repository depend on unrelated repository size and root links. For root-single/local-skill, direct-pack, and collection shapes, non-candidate root repository context—including hidden files and directories and link-like or special entries—is outside direct enumeration, except the `.claude/skills/` collection root admitted by E14. The fixed markers `catalogue.toml`, `packs/`, `pack.toml`, `SKILL.md`, `skills/`, and `.claude/skills/` are always probed; a link-like or special entry at a candidate path refuses unconditionally before enumeration. Enumeration and Family-2 counting start only at the E14 collection root plus root `pack.toml` for a direct pack, or at root `SKILL.md` plus `scripts/`, `references/`, `assets/`, and `evals/` for a root single/local skill. Context is neither traversed nor counted toward Family-2 entries, depth, or files, and is never normalized, hashed, reported, or projected.

### E14 — Two collection roots and one optional category level

**2026-08-28 — Approver: eugenelim.** D1 recognises a collection only at a root `skills/` whose direct children are skill envelopes. A corpus of eighteen real public skill repositories (T0d) showed that this admits seven of the thirteen legitimate single-owner collections, and that four of the six refusals fall into two conventions the single-root rule could admit: topical grouping one level below the collection root (`skills/<category>/<name>/SKILL.md`), and publishing from the installed location (`.claude/skills/<name>/SKILL.md`) in repositories that are themselves agent workspaces. Both are fixed-depth and enumerable; neither requires the recursive discovery the body refuses. The remaining two refusals are root-level grouping with no collection root, which this erratum still refuses. Measured after adoption, `.claude/skills/` admitted two of the six directly; the category level admitted none of them, because its only instance in that corpus refuses on budgets, and its justification rests on a wider corpus in which four of five category-grouped repositories admit.

A collection root is therefore `skills/` **or** `.claude/skills/`. Within that root, a direct child holding `SKILL.md` is a skill envelope, and a direct child holding no `SKILL.md` is a category directory whose own direct children holding `SKILL.md` are skill envelopes. Exactly these two levels are recognised; a third refuses. Envelope and category children may be mixed under one root.

Fail-closed rules: a repository containing both `skills/` and `.claude/skills/` refuses as ambiguous and names both paths, with recovery through an explicit local path at the intended root; a category directory holding neither an envelope nor `SKILL.md` refuses as a childless root does today; and skill identity remains the **leaf** directory name, which must equal the frontmatter name, so two categories declaring the same leaf name collide and refuse under the existing same-name rule rather than being silently namespaced. `source-path` continues to record the full relative path and disambiguates provenance.

**This erratum supersedes the `no dot directories` clause of the accepted body's broad-discovery mitigation**, which reads "direct children under root `skills/` only, no dot directories, no recursive fallback, and ambiguity refusal". The remainder of that mitigation stands unchanged: no recursive fallback, ambiguity refusal, and direct children only — one bounded category level is not recursion, because its depth is fixed rather than discovered. `.claude/skills/` is the sole hidden path this decision admits; E13's rule that hidden root context is ignored is otherwise unchanged, and no other dot-directory becomes a collection root. Because `.claude/skills/` is also AgentBundle's own repo-scope projection target, a direct install whose resolved source root lies inside the resolved projection target for the selected scope refuses, as does a source carrying catalogue markers: a catalogue repository takes the catalogue route and is never admitted directly. Root-level category grouping (`<category>/<name>/SKILL.md` with no collection root) remains refused, because it is structurally indistinguishable from a vendored aggregate of other publishers' collections — the corpus held both shapes and no mechanical test separates them.

The extra level costs one level of depth, which is what prompted E15 to move the depth origin to the skill envelope. E15 owns the depth number and its origin; no figure is restated here.

### E15 — Depth is measured from the skill envelope and bounded at 12

**2026-08-28 — Approver: eugenelim.** Before this erratum, E11 bounded path depth at 10 measured from the enumeration root. Two defects follow. First, the origin is layout-dependent: E14's optional category level consumes one level, so an identical skill payload measures one deeper merely because its publisher groups by topic, and the same repository changes verdict when regrouped. Second, the value was chosen without a stated cost basis. Both defects are independent of the corpus: the origin is wrong however deep real payloads happen to be.

Depth is therefore measured from **each skill envelope**, not from the enumeration root, so the bound expresses how deep a skill's own payload may nest and is independent of collection layout, category grouping, and the choice of collection root. Measured that way the corpus maximum is 7 (`chujianyun`'s vendored `references/docs/api-reference/speech-synthesis/voice-design/cosyvoice/` tree; `anthropics/skills` reaches 6 through `xlsx/scripts/office/schemas/ecma/fouth-edition/`).

The bound is raised from 10 to **12** so that the admitted maximum of 6 and the widest observed payload of 7 both clear it after the origin change, without inviting arbitrary nesting. The raise is justified by the origin correction and by AC36's cost ceiling: all six Family-2 budgets simultaneously at their limits measure 1.92–2.12 s and 26 MiB against the 5 s / 256 MiB ceiling. The earlier 1.70 s figure omitted depth and selected-skill count, which turn out to dominate: enumeration was 1.32 s of 1.70 s at three budgets and 4.02 s of 4.97 s at six.

No corpus verdict changes. Depth was not the binding constraint for any admitted repository — the deepest, `anthropics/skills`, measures 6 — and `chujianyun` continues to refuse on file count and per-file size, which this erratum does not touch.
