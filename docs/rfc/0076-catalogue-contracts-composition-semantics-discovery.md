# RFC-0076: Catalogue Contracts, Composition, Semantics, and Discovery

<!-- Written for a cold reader. "Pack" means an installable catalogue unit
(pack.toml + .apm/ primitives). "Contract" means a machine-readable JSON
Schema or TOML configuration that is versioned and validated. "Integration"
refers to the optional [[pack.integrations]] composition convention introduced
by D6. -->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-29
- **Date closed:** 2026-07-29
- **Decision weight:** major <!-- New public schemas, new CLI surface, new
  catalogue-index.json format, behavioral change to packaging (mutation refusal),
  information-architecture changes to docs-site and marketing site. -->
- **Related:**
  - [RFC-0003](0003-spec-and-cli.md) (lifts adapter contract to published open standard;
    contracts/ and conformance suite originate here)
  - [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) (original adapter contract RFC)
  - [RFC-0059](0059-notes/) (catalogue-curation pack — authoring workflow)
  - [RFC-0065](0065-iac-terraform-pack.md) (D5 noted source-author review requirement)
  - [ini-005 workspace entry](../../workspace.toml) (AgentBundle Portable Catalogue
    Tooling — complements this initiative; ini-005 delivers the public `agentbundle
    catalogue *` CLI surface that D5 extends)
  - [ini-006 workspace entry](../../workspace.toml) (Catalogue CI Contract — complete;
    D1 authority model is compatible with ini-006's responsibility boundary)

---

## Reviewer brief

- **Decision:** Whether to establish (D1) a canonical contract authority model,
  (D2) sync four missing schemas to agentbundle's bundled data, (D3) update
  contracts/README completeness, (D4) create a portable authoring-standards hub,
  (D5) add a bundled-contract inspection CLI surface, (D6) define an optional
  pack-integration convention, (D7) introduce a deterministic neutral catalogue
  index, (D8) add release-integrity contracts (content digests + mutation refusal),
  (D9) add a "Build a Catalogue" top-level section to the docs site, and (D10) add
  an evaluator-oriented marketing page.
- **Recommended outcome:** Accept D1–D10 with noted constraints.
- **Change if accepted (summary):**
  - `contracts/README.md` — lists all 11 active contracts (D3).
  - `contracts/pack.schema.json` — adds `[[pack.integrations]]` table (D6).
  - `packages/agentbundle/agentbundle/_data/` — adds `guide.schema.json`,
    `skill.schema.json`, `skill-manifest.schema.json`, `target-vocab.toml` with
    byte-parity CI gate (D2). Adds `agentbundle catalogue contracts` CLI commands (D5).
  - `guides/_shared/reference/catalogue-authoring-standards.md` — new portable hub (D4).
  - `catalogue-index.json` — new neutral format spec (D7, schema in contracts/).
  - `catalogue-manifest.json` — gains content digests and mutation-refusal logic (D8).
  - `docs-site/` — new "Build a Catalogue" top-level section (D9).
  - `web/` — new `/evaluate/` page (D10).
  - Root `README.md` and `CONTRIBUTING.md` — fork language replaced; direct links
    to evaluate, build, contracts, contribute.
- **Affected surfaces:**
  - `contracts/pack.schema.json` + `agentbundle/_data/` sync
  - `packages/agentbundle/` — CLI surface changes (engine changes require version
    bump + `Engine-Change-RFC: RFC-0076` footer per AGENTS.local.md policy)
  - `packs/README.md`, `packs/AGENTS.md`, `profiles/README.md`, `profiles/AGENTS.md`
  - `guides/_shared/reference/catalogue-authoring-standards.md` (new)
  - `docs-site/src/content/docs/` (new section)
  - `web/src/pages/evaluate.astro` (new page)
  - `README.md`, `CONTRIBUTING.md`
  - First-party pack.toml files for pilot integrations
- **Stakes:** High. This RFC changes public machine contracts (pack.schema.json) and
  introduces a new CLI surface that external consumers of agentbundle will observe.
  D6 (integrations) and D7 (catalogue-index) are new public contracts with no prior
  art in this codebase. D8 (mutation refusal) is a behavioral breaking change for
  any workflow that re-packages the same version with different content.
- **Review focus:** D5 CLI surface spelling; D6 [[pack.integrations]] schema fields
  and the four `kind` values; D7 catalogue-index.json shape; D8 mutation refusal
  scope (full catalogue vs per-pack).
- **Not in scope:** Hosted registry service; publisher namespaces; exact version
  selectors; multi-version dependency solving; subjective trust scores; automatic
  integration dispatch; executable `when` expressions; automatic installation of
  integration targets; cross-catalogue integrations before qualified identities;
  replacement of the central site framework; CI workflow generation; background
  update services.

---

## The ask

This RFC establishes the governance framework for the Catalogue Contracts, Composition,
Semantics, and Discovery initiative (ini-007). It does not implement any change — each
decision is implemented by a wave-specific spec. The RFC's role is to:

1. Lock the authority model before any wave changes any contract.
2. Accept or reject each proposed surface before any spec is authored against it.
3. Record the design decisions that the wave specs can reference as their governance basis.

Implementation proceeds in nine waves under work-loop full mode. No wave ships before
the relevant decisions in this RFC are in the Accepted state.

---

## Background

Audience discovery research (2026-07-29, `docs/product/research/catalogue-audience-discovery.md`)
found that 6 of 8 navigation targets fail today:

- No portable authoring-standards hub in the scaffold or the repo.
- The docs site is consumer-only; no "Build a Catalogue" section exists.
- No `/evaluate/` marketing page; no evaluator-oriented evidence.
- Root README has pre-init-command fork language.
- `contracts/README.md` lists 4 of 11 active contracts.
- packs/AGENTS.md schema map is not linked to machine contracts.

Contract inventory research (2026-07-29, `docs/product/research/catalogue-contract-guidance-inventory.md`)
found that four contracts present in `contracts/` are absent from `agentbundle/_data/`:

- `guide.schema.json`
- `skill.schema.json`
- `skill-manifest.schema.json`
- `target-vocab.toml`

No CI gate verifies byte-parity between `contracts/` and `_data/`. No neutral
`catalogue-index.json` exists (only the Claude-specific `marketplace.json`). No
`[[pack.integrations]]` convention exists to express optional cross-pack composition.
No bundled-contract inspection CLI surface exists for offline use.

---

## Decisions

### D1 — Contract authority model

**Decision:** The following authority direction is canonical. Each tier is
deterministically derived from the tier above it.

```
contracts/
    canonical authored public contracts
    normative source of truth for all machine formats

        → (byte-identical projection, CI-gated)

packages/agentbundle/agentbundle/_data/
    executable contracts bundled with AgentBundle
    must be byte-identical to contracts/ for each file present in both
    install-defaults.toml and install-marker.py are _data/-only (not public contracts)

        → (validation and generation read _data/ schemas)

generated neutral catalogue-index.json
    semantic and discovery projection
    deterministic, content-addressable

        → (generated references derived from contracts and catalogue content)

AGENTS.md, README.md, and guides
    concise operational and narrative guidance
    NOT an independent schema source
    schema maps in AGENTS files must be explicitly normative-linked and contract-tested
    human guides explain why and how; they do not define undocumented schema fields
```

**Constraint:** External catalogues do not need to copy `contracts/`. Catalogue-local
contract copies cannot override the running AgentBundle version.

**Impact:** Requires D2 (sync), CI gate, and normative pointer additions to AGENTS files.

---

### D2 — Missing schema sync to agentbundle/_data/

**Decision:** Add `guide.schema.json`, `skill.schema.json`, `skill-manifest.schema.json`,
and `target-vocab.toml` to `packages/agentbundle/agentbundle/_data/`. These files must
be byte-identical to their `contracts/` counterparts.

Add a CI gate that verifies byte-parity for all schema files that appear in both
`contracts/` and `_data/`. Gate runs on every PR that touches either path.

**Engine change:** Each schema file addition to `_data/` requires:
1. `packages/agentbundle/pyproject.toml` version bump.
2. `Engine-Change-RFC: RFC-0076` footer in the commit message.
3. `tools/catalogue/sync_authoring_scaffold.py` extended to cover schema parity check
   (or a separate `tools/catalogue/check_contract_parity.py` tool if scope differs).

**Rationale:** Skill and guide validation in `agentbundle catalogue lint` today does not
load `skill.schema.json` from `_data/` because it is absent. Air-gapped environments
and the bundled wheel cannot validate skill frontmatter against the canonical schema.

---

### D3 — contracts/README.md completeness

**Decision:** Update `contracts/README.md` to list all active contracts:

| File | What it pins | Governing spec/RFC |
|------|-------------|-------------------|
| `adapter.toml` | Per-IDE adapter projection rules | RFC-0001 / distribution-adapters spec |
| `adapter.schema.json` | JSON Schema for adapter.toml | RFC-0001 (AC #1) |
| `pack.schema.json` | JSON Schema for pack.toml | RFC-0001 (AC #3); RFC-0076 (D6 adds [[pack.integrations]]) |
| `plugin-manifest.schema.json` | JSON Schema for .claude-plugin/plugin.json | RFC-0001 (AC #4) |
| `plugin-manifest.derived.schema.json` | Derived schema (agentbundle _data copy) | distribution-adapters |
| `catalogue.schema.json` | JSON Schema for catalogue.toml | catalogue-tooling-foundation spec |
| `profile.schema.json` | JSON Schema for profile TOML files | pack-profiles spec |
| `guide.schema.json` | JSON Schema for guide frontmatter | pack-journeys spec |
| `skill.schema.json` | JSON Schema for skill SKILL.md frontmatter and body | agentbundle-skill-spec-lint-and-evals spec |
| `skill-manifest.schema.json` | JSON Schema for agentbundle skill manifest | agentbundle-skill-spec-lint-and-evals spec |
| `target-vocab.toml` | Vocabulary for adapter target names | distribution-adapters spec |
| `catalogue-index.schema.json` | JSON Schema for catalogue-index.json | RFC-0076 (D7, new) |

This is a documentation-only change; it does not modify any schema. No engine change required.

---

### D4 — Portable authoring-standards hub

**Decision:** Create `guides/_shared/reference/catalogue-authoring-standards.md` as the
single portable hub for catalogue authoring. This file:

- Is shipped in the `agentbundle` catalogue scaffold (Wave 1 adds it to
  `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/`).
- Routes via named links to every authoritative authoring contract:
  - Catalogue format (`catalogue.schema.json` + how-to guide)
  - Pack manifest (`pack.schema.json` + how-to guide)
  - Pack README standard (packs/README.md)
  - Pack layout (packs/AGENTS.md)
  - Skill frontmatter (`skill.schema.json` + author-a-skill guide)
  - Skill body and progressive-disclosure guidance
  - Optional pack integrations (Wave 2 adds this entry)
  - Profile format (`profile.schema.json` + design-a-profile guide)
  - Journey format (Wave 4 adds this entry)
  - Lint and verify commands
  - CI contract (`catalogue-ci-contract.md`)
  - Package and publication guidance

- States explicitly that machine contracts in `contracts/` are normative.
- Contains no host CI workflow requirements (portable).
- Contains no host Make target requirements (portable).
- Is useful without the host site (no links require the source repo to exist;
  every section can stand alone from the scaffold).

**Engine change:** Adding the hub to the scaffold requires version bump +
`Engine-Change-RFC: RFC-0076` footer.

**Rationale:** Every audience journey found in research (A–E) reaches a dead end
without a hub. The hub is the single fix that satisfies the navigation target
"from packs/README.md, one link to authoring standards; from the hub, one further
link to every authoritative contract."

---

### D5 — Bundled-contract inspection CLI surface

**Decision:** Add the following commands to `agentbundle catalogue contracts`:

```
agentbundle catalogue contracts list
    Table output: name, kind, version, schema/file. JSON with --format json.
    Lists all contracts bundled in the running agentbundle version.

agentbundle catalogue contracts show <name>
    Shows full content of the named bundled contract.
    <name> is from the names returned by `contracts list`.

agentbundle catalogue contracts export --output <dir>
    Copies all bundled contracts to <dir>.
    Prints a manifest of exported files.
    Does NOT override agentbundle's validation behavior.
    Exported files are reference copies only.
```

**Requirements:**
- Uses `importlib.resources` to locate bundled files.
- Works without network access.
- Exposes exact bundled contracts for the running agentbundle version.
- The `export` subcommand distinguishes reference export from executable override
  (a printed notice: "These are reference copies only. They do not override the
  contracts used for validation by this agentbundle version.").
- Supports `--format json` where the primary output is tabular.
- No third-party runtime dependencies beyond the existing agentbundle package.

**Not frozen until:** ini-005 `catalogue-tooling-rewire` spec is accepted (to avoid
conflicting with the `agentbundle catalogue *` surface that ini-005 is establishing).
The spelling above is the candidate; the accepted surface must satisfy the requirements.

**Engine change:** New CLI subcommand requires version bump + `Engine-Change-RFC: RFC-0076`.

---

### D6 — Optional pack-integration convention

**Decision:** Add an optional `[[pack.integrations]]` array-of-tables to `pack.toml`
(and to `contracts/pack.schema.json`). Each integration declares a named, optional
behavior seam between two packs.

#### Semantics

An integration:
- is always optional — the consuming skill must declare and honor a fallback;
- never auto-installs its target;
- never participates in dependency closure;
- never changes source resolution;
- never imports another pack's files;
- describes a conditional behavior seam at a skill boundary;
- requires a `fallback` field explaining what the consuming skill does when the
  integration target is absent;
- may be indexed and rendered (in CLI output, docs, marketing pages);
- may be used by skills through capability-roster checks and supplied artifacts.

#### Schema fields (candidate — to be frozen by Wave 2 spec)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | yes | string | Unique within the pack; `^[a-z0-9][a-z0-9-]*$` |
| `pack` | yes | string | Target pack name |
| `kind` | yes | enum | `input`, `augment`, `review`, `handoff` |
| `role` | yes | string | User-facing label for the integration's role |
| `consumers` | yes | array of strings | Pack-qualified primitive references (`skill:<name>`, `agent:<name>`, `command:<name>`, `hook:<name>`) |
| `providers` | yes | array of strings | Pack-qualified primitives provided by the target pack |
| `when` | yes | string | Explanatory text (NOT an executable expression language) |
| `purpose` | yes | string | One sentence describing the benefit |
| `fallback` | yes | string | What the consuming skill does when the target is absent |
| `version` | no | string | Semver range for compatible target pack version |

**Kind definitions:**
- `input`: the target pack provides an artifact the consuming skill accepts as primary input.
- `augment`: the target pack adds a pre-flight step or contextual enhancement to the consuming skill.
- `review`: the target pack provides a reviewer for an artifact the consuming skill produces.
- `handoff`: the consuming skill passes its output to the target pack for further processing.

**`when` is explanatory text only.** It describes the condition under which the
integration is useful. It is not evaluated by any runtime. No executable `when`
expressions are added to any pack.

#### Validation rules

Portable validation must enforce:
- Unique integration IDs within a pack.
- Closed `kind` enum (the four values above).
- Valid local consumer references (the named primitives must exist in the pack).
- Non-empty `when`, `purpose`, and `fallback`.
- No self-target integration (a pack cannot integrate with itself).
- Valid version-range grammar when `version` is present.
- When the target pack is present in the catalogue:
  - Version compatibility check.
  - Valid provider references (the named primitives must exist in the target).
- When the target pack is absent:
  - Portable catalogue verification still succeeds.
  - CLI and neutral index indicate the target is unavailable in this snapshot.

Host first-party policy (this repository) may require all first-party integration
targets to resolve. This is enforced in the Wave 2 spec's first-party test suite,
not in portable validation.

**Cross-catalogue integrations remain deferred** until registry-qualified identities exist.

#### First-party pilot entries (Wave 2)

At minimum, implement and test:

1. `core` → `frontend-engineering`:
   - `frontend-preflight-augment` (`kind: augment`) — frontend pre-flight augmentation
   - `frontend-cold-reviewer` (`kind: review`) — frontend cold reviewer

2. `governance-extras` `new-rfc` → `desk-research`:
   - `promoted-research-evidence` (`kind: input`) — desk-research provides promoted evidence

3. `governance-extras` `new-rfc` → `product-engineering`:
   - `design-proposal` (`kind: input`) — shaped product intent or decision proposal

4. `governance-extras` `new-rfc` → `architect`:
   - `design-proposal` (`kind: input`) — architecture proposal or reviewed design document

For entries 3 and 4: both may use the same `role: design-proposal`; the consuming
`new-rfc` skill determines whether one or both available inputs are useful.

Verify actual pack versions and primitive names from HEAD before authoring entries.

#### Runtime contract

AgentBundle does not automatically dispatch an integration. The consuming skill is
responsible for:
- Checking the available capability roster.
- Accepting an already-supplied upstream artifact.
- Applying the integration only when its `when` condition matches.
- Recording its use in the work-loop state or skill output.
- Applying its declared `fallback` when the target pack is absent.

#### Presentation

Integrations are exposed through:
- `agentbundle show <pack>` — table and JSON output
- Neutral `catalogue-index.json` — relationship view and inverse relationship view
- Pack README guidance (authoring convention, not a hand-maintained full list)
- Technical pack reference pages
- Marketing pack pages (rendered as relationship view with user-facing labels)

User-facing labels (Wave 7 rendering):
- `kind: input` → "Accepts input from"
- `kind: augment` → "Works with"
- `kind: review` → "Optional reviewers"
- `kind: handoff` → "Hands off to"

---

### D7 — Neutral catalogue index

**Decision:** Introduce `catalogue-index.json` as a deterministic, content-addressable
semantic and discovery projection generated from the catalogue's pack.toml files,
JOURNEY.md files (Wave 4), skill manifests, and integration entries.

**Three distinct files — never merge:**

| File | Purpose | Generated by |
|------|---------|-------------|
| `catalogue-index.json` | Semantic and discovery projection | `agentbundle catalogue index` (new command, Wave 4) |
| `catalogue-manifest.json` | Immutable file and digest evidence | `agentbundle catalogue package` (enhanced in Wave 5) |
| `.claude-plugin/marketplace.json` | Claude-specific marketplace projection | `agentbundle catalogue self-host` (existing) |

**catalogue-index.json schema (candidate — Wave 4 spec owns the full schema):**

```json
{
  "schema_version": "1",
  "generated_at": "<iso8601>",
  "catalogue": {
    "name": "...",
    "version": "...",
    "description": "..."
  },
  "packs": [
    {
      "name": "...",
      "version": "...",
      "description": "...",
      "scope": "repo|user",
      "categories": [...],
      "lifecycle": "...",
      "adapters": [...],
      "integrations": [...],
      "integrations_inverse": [...],
      "journeys": [...],
      "effects": [...],
      "documentation": "...",
      "digest": "..."
    }
  ],
  "profiles": [...]
}
```

**Normative fields:** `schema_version`, `generated_at`, `catalogue`, `packs[].name`,
`packs[].version`, `packs[].scope`. All other fields are conditionally required (Wave 4 spec specifies requirements).

**Contract location:** `contracts/catalogue-index.schema.json` (new, Wave 4).

---

### D8 — Release integrity

**Decision:**

1. **Content digests:** `agentbundle catalogue package` adds a `SHA-256` content digest
   for each pack and profile to `catalogue-manifest.json`. The digest covers the pack's
   normalized content tree (excluding generated outputs). Algorithm: SHA-256 of the
   sorted, normalized file list.

2. **Same-version mutation refusal:** When re-packaging a version that already exists
   in the output archive directory, `agentbundle catalogue package` refuses and exits 2
   unless `--force` is passed. This prevents silent content mutation under the same
   version string. First-party CI policy in this repo prohibits `--force` in the
   publish pipeline.

3. **Human and JSON release comparison:** `agentbundle catalogue package` adds a
   `--compare <archive>` flag that compares the current package against a previous
   archive and emits a diff (added/removed/changed packs with version and digest
   changes). Human output (default) and `--format json` output both supported.

**Scope:** The mutation refusal applies at the catalogue-archive level (a packaged
`.tar.gz`). It does not prevent local development re-builds; it fires only when an
archive with the same version already exists at the output path.

---

### D9 — Technical documentation information architecture

**Decision:** Add a top-level "Build a Catalogue" section to the docs site. Navigation:

```
Build a Catalogue
  ├── Create a catalogue              (existing create-a-catalogue.md guide)
  ├── Catalogue authoring standards  (new D4 hub)
  ├── Author a pack                  (existing author-a-pack guides)
  ├── Author a skill                 (existing author-a-skill.md guide)
  ├── Optional pack integrations     (Wave 2 — new)
  ├── Author a profile               (existing design-a-profile.md guide)
  ├── Journey format                 (Wave 4 — new)
  ├── Contract and schema reference  (generated from contracts/ — Wave 6)
  ├── Verify and test                (existing catalogue-ci-contract.md)
  └── Package and publish            (existing how-to + Wave 5)
```

Update the docs-site home page (`index.mdx`) to surface two distinct routes:
- "Use the catalogue" (existing consumer focus)
- "Build or evaluate a catalogue" (new authoring/evaluation route)

The central guide-rendering and existing pack guide routes are unchanged.

Generate or contract-test sidebar facts rather than maintaining an independent
inventory. Field reference pages for pack.toml and skill.schema.json are
generated from machine contracts where practical (Wave 6 spec defines "practical").

---

### D10 — Marketing evaluator surface

**Decision:** Add a `/evaluate/` page to the marketing site explaining in accessible
terms:

- Open file-based formats (pack.toml, skill SKILL.md, profile TOML)
- Versioned contracts (contracts/ directory, RFC-0003 standard)
- Deterministic verification and packaging (agentbundle catalogue verify/package)
- Human gates (RFC/ADR governance process)
- Source ownership (user owns their catalogue)
- Adapter projection (one source → multiple agent IDEs)
- Release integrity (mutation refusal, content digests — Wave 8, after D8 ships)
- Optional composition (Wave 7, after D6 ships)
- Links to technical evidence (docs-site, contracts/, agentbundle PyPI)

Do not turn the marketing site into raw schema documentation.

Update catalogue and pack pages (Wave 7) to consume neutral-index facts for:
version, scope, adapters, lifecycle, optional integrations, documentation links.

Render pack composition as a legible relationship view (user-facing labels from D6).

Avoid broadly redesigning the visual system.

---

## Open questions (implementation-time resolutions)

These questions do not block RFC acceptance. Each is resolved by the owning wave spec.

**OQ1 — D5 surface spelling conflict with ini-005:** The `agentbundle catalogue contracts`
commands must not conflict with the surface ini-005's `catalogue-tooling-rewire` spec
establishes. The Wave 3 spec (enterprise authoring discovery) verifies the surface before
implementing it. If ini-005 reserves `agentbundle catalogue contracts`, an alternative
subcommand path (e.g., `agentbundle contracts`) is acceptable.
*Resolves in: Wave 3 spec.*

**OQ2 — D7 catalogue-index command spelling:** `agentbundle catalogue index` is the
candidate subcommand. ini-005's CLI surface may constrain the namespace. The Wave 4 spec
confirms the spelling before implementing.
*Resolves in: Wave 4 spec.*

**OQ3 — D8 mutation refusal scope:** The decision applies at catalogue-archive level.
The Wave 5 spec determines whether pack-level archives (if any) are also in scope.
*Resolves in: Wave 5 spec.*

**OQ4 — D9 generated field references:** The Wave 6 spec determines which `pack.schema.json`
fields are sufficiently described by the schema annotations to generate reference pages,
and which require manual narrative explanation beyond what the JSON schema provides.
*Resolves in: Wave 6 spec.*

---

## Wave-to-decision mapping

| Wave | Decisions implemented |
|------|-----------------------|
| 1 | D1 (authority model), D2 (schema sync), D3 (README), D4 (hub) |
| 2 | D6 (integrations) |
| 3 | D5 (contracts CLI), D4 (hub in scaffold) |
| 4 | D7 (catalogue-index) |
| 5 | D8 (release integrity) |
| 6 | D9 (docs-site IA) |
| 7 | D10 (marketing evaluator) |
| 8 | README/CONTRIBUTING convergence (no new decision — applies D1-D4) |
| 9 | First-party migration + closeout |

---

## Acceptance criteria (for this RFC)

- [x] D1–D10 reviewed and accepted (accepted 2026-07-29)
- [ ] OQ1 resolved in Wave 3 spec: D5 surface does not conflict with ini-005 catalogue-tooling-rewire
- [ ] OQ2 resolved in Wave 4 spec: D7 catalogue-index command spelling confirmed
- [ ] OQ3 resolved in Wave 5 spec: D8 mutation refusal scope clarified
- [ ] OQ4 resolved in Wave 6 spec: D9 generated field reference criterion defined
- [x] Wave-to-decision mapping reviewed; no wave implements an unaccepted decision
