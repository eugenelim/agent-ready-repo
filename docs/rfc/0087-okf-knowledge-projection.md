# RFC-0087: OKF knowledge projection

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-15
- **Date closed:** 2026-08-15
- **Decision weight:** heavy (external knowledge can become agent instructions, crossing file-processing and execution-authority boundaries)
- **Related:**
  - [Research survey](../product/research/google-okf-agentbundle-survey.md) — applied research on Open Knowledge Format (OKF), Agent Skills, ecosystem gaps, and candidate knowledge packs.
  - [Adapter preservation spike](0087-notes/adapter-spike.md) — reproducible fixture, command, digest, output paths, and byte-equality results for nested Skill content.
  - [RFC-0001](0001-bundle-distribution-by-adapter-spec.md) — established canonical pack sources projected into ecosystem-native outputs.
  - [RFC-0029](0029-strengthen-security-reviewer.md) — established router-driven progressive disclosure through Skill references without an adapter-contract change.
  - [RFC-0031](0031-catalogue-package-manager-posture.md) and [ADR-0021](../adr/0021-pack-manifest-source-of-truth-and-scoped-identity.md) — established `pack.toml` as the rich pack-metadata source with one-way projections.
  - [RFC-0060](0060-catalogue-runtime-inventory.md) and [ADR-0049](../adr/0049-catalogue-runtime-inventory-derive-live.md) — established live-derived pack inventory rather than a persisted inventory that can drift.
  - [RFC-0076](0076-catalogue-contracts-composition-semantics-discovery.md) — established `catalogue-index.json` as the deterministic neutral semantic/discovery projection; this experiment must not invent a competing index.
  - [RFC-0085](0085-catalogue-source-identity.md) — separates catalogue authoring sources from generated distribution artifacts.

The **Open Knowledge Format (OKF)** is a directory of Markdown concept files
with YAML frontmatter, links, provenance, lifecycle signals, and hierarchical
`index.md` files. This experiment supports OKF 0.2, the latest published OKF
version verified on 2026-08-15, only. An **Agent Skill** is a
directory whose `SKILL.md` gives an agent activation metadata and instructions,
optionally supported by references, scripts, and assets. A **pack** is
AgentBundle's independently installable unit. AgentBundle calls each kind of
pack content a **primitive**; its current five are Skill, agent, command, hook
body, and hook wiring. An **adapter** deterministically copies or translates
those primitives into one agent product's native layout. This RFC calls
generation from canonical OKF into Skills a **projection**: a one-way,
replaceable build output, never a claim that the two formats are semantically
interchangeable. **Progressive disclosure** means that the agent first sees
short Skill activation metadata, then loads a router, index, or reference only
when the task needs deeper knowledge.

`agentbundle-okf/v1` is AgentBundle's projection-profile version, not an OKF
version. This RFC is `Accepted`: the Approver has accepted the architecture and
waived the optional `Experimental` lifecycle stop. Acceptance does not mean the
feature is implemented, shipped, or publicly stable. The two Draft specs, both
pilots, their security and determinism gates, and the follow-on ADR remain
required before release. Failed pilot evidence stops implementation and requires
an erratum or superseding RFC rather than a caller-specific workaround.
**Decision weight: heavy** means the full evidence, adversarial, cold-reader,
and security reviews are required because the decision crosses an
instruction-authority boundary.

In this RFC, an OKF **concept** is one Markdown knowledge unit. A `Playbook` is
OKF's procedural concept shape and is the only concept type eligible for Skill
instruction projection in v1; other concept types remain references. An
**Attested Computation** describes a reproducible calculation through metadata
such as runtime, executor, and attester. Those fields are descriptive and inert
here: the compiler validates and preserves them but never invokes them. OKF
lifecycle fields such as `status` and `stale_after` tell the router whether an
entry is current, deprecated, or due for review; v1 accepts only the names and
values defined by OKF 0.2 rather than inventing a second lifecycle vocabulary.

**Latest is pinned, not floating.** `agentbundle-okf/v1` maps to exactly OKF
`0.2`. The authored pack profile selects that mapping; the compiler wholly owns
the managed bundle's root `index.md` and emits `okf_version: "0.2"` there. In
write mode an absent root file is created; in check mode it fails as drift. An
existing root with a missing, non-string, older, or newer value fails as a
version conflict in either mode. The compiler does not inspect the network or
infer compatibility. When upstream publishes a
new OKF version, the current compiler continues to support only 0.2 until a
reviewed AgentBundle profile release maps the new version's behavior. The
experiment promises no simultaneous backward-version support.

## Reviewer brief

- **Decision:** Whether AgentBundle should experimentally adopt pack-local OKF knowledge sources and deterministically project them into discoverable Agent Skills.
- **Recommended outcome:** Implement the accepted decision through the two
  pilot specs and require their evidence gates before release.
- **Change if accepted:**
  - Add a pack-local `okf/<bundle>/` authoring-source convention and versioned extension schemas.
  - Generate hierarchical OKF indexes, router Skills, selected concept Skills, and raw OKF delivery deterministically.
  - Expose rich pack, Skill, and knowledge metadata through live catalogue inspection.
- **Affected surface:** Pack layout, extension contracts, a `catalogue-curation` authoring skill and compiler, generated `.apm/skills/`, `agentbundle show`, tests, and product/architecture documentation. The adapter contract does not change.
- **Stakes:** Reversible while experimental; costly to reverse if other catalogues adopt the source layout or extension profile. Security-sensitive because external knowledge can become agent instructions.
- **Review focus:** Canonical-source versus generated-output boundaries; deterministic and offline generation; extension compatibility; path, prompt, and execution safety; and how experimental discovery coexists with `catalogue-index.json`.
- **Not in scope:** A new `.apm` primitive, runtime LLM generation, automatic execution of OKF computations, a hosted registry or search service, or approval to publish a cost-engineering pack.

## The ask

- **Recommendation (bottom line up front):** Implement the accepted OKF authoring and projection profile through its two pilot specs. Canonical bundles live under `packs/<pack>/okf/`; an AI-assisted authoring workflow may prepare them, but a deterministic compiler validates and generates router indexes, Skill metadata and bodies, raw-bundle delivery, and catalogue discovery records. Run the design against two callers and satisfy every promotion gate before release or before deciding whether to promote the compiler into the public AgentBundle command line or add a new adapter primitive.
- **Why now (situation–complication–question):** AgentBundle already transports arbitrary files inside Skills unchanged, while OKF supplies a portable knowledge format with provenance, freshness, extensions, and progressive indexes. What is missing is a governed boundary between pack discovery, agent Skill selection, concept retrieval, and execution authority. The question is whether a bounded projection experiment can establish that boundary without making builds probabilistic or prematurely expanding the public adapter contract.
- **Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Where does canonical OKF live, and how is it delivered? | `packs/<pack>/okf/<bundle>/`, projected into router Skill references | Separates canonical knowledge from generated Skills while reusing current adapter delivery | This review | Confirm the new pack-local source convention |
| D2 | When does OKF-to-Skill projection run? | Authoring time; commit generated output and drift-check it | Keeps normal installation and adapter builds deterministic and dependency-free | This review | Confirm committed generated outputs |
| D3 | How does a concept opt into Skill generation? | A versioned `x-agentbundle.skill` declaration plus a matching pack-local review entry and full projection digest | Prevents facts and schemas from being misrepresented as reviewed procedures | This review | Confirm the two-key projection boundary |
| D4 | What instruction or execution authority does OKF carry? | Projection requires an explicit pack-local review record; projection never grants tools | OKF prose, executor, and attester metadata must not become ambient authority | This review | Confirm the fail-closed authority policy |
| D5 | What experiment is sufficient? | A cost-engineering prototype plus `security-checklists` | Two callers test genericity without catalogue-wide commitment | This review | Confirm the callers and promotion gate |
| D6 | How is knowledge discovered? | Pack metadata from `pack.toml`; Skill metadata from generated `SKILL.md`; hierarchical concept indexes from OKF; expose all three live through additive `show --format json` fields | Each level has one source of truth and a discovery surface suited to its consumer | This review | Confirm the three-level discovery contract |
| D7 | Where may AI participate? | AI-assisted source authoring only; deterministic, offline validation and compilation | Retains useful AI curation without making builds probabilistic | This review | Confirm the determinism boundary |
| D8 | Which OKF versions does one compiler release support? | Exactly one pinned, reviewed version; `agentbundle-okf/v1` maps only to OKF 0.2 | Prevents a young upstream format from changing parser, lifecycle, or routing behavior implicitly | This review | Confirm single-version support with no backward-compatibility commitment |

## Problem & goals

**Diagnosis.** AgentBundle can already carry an OKF directory inside a Skill,
but that fact alone does not define a maintainable knowledge system. Four
discovery and authority gaps remain:

1. If the canonical bundle lives inside a generated Skill, source and output
   become indistinguishable and the Skill can accidentally become its own source
   of truth.
2. Pack metadata, Skill activation metadata, and OKF concept metadata serve
   different discovery moments. Deriving all three from one description would
   erase distinctions; authoring all three independently would create drift.
3. OKF permits extensions and Attested Computations, but does not define Agent
   Skill generation, code packaging, invocation, or sandboxing. A consumer that
   infers those semantics silently widens authority.
4. AI can improve ingestion and curation, but an LLM in the build would make
   output non-repeatable and make review evidence expire on every run.

**Goals.**

- Ship conformant OKF bundles natively inside ordinary Agent Skills on every
  current adapter.
- Give a pack one explicit canonical location for OKF authoring sources.
- Generate only those Skills for which the source explicitly declares
  activation semantics.
- Make pack selection, Skill selection, and concept retrieval independently
  discoverable without duplicating an authoritative inventory.
- Preserve unknown OKF extensions and the original concept documents.
- Make compilation deterministic, offline, path-confined, and drift-gated.
- Validate the genericity of the projection with two meaningfully different
  callers before expanding a public interface.
- Support one explicit OKF version per active AgentBundle profile and require a
  reviewed migration before changing that version.

**Non-goals.**

- **A universal knowledge runtime.** This experiment emits files; it does not
  add vector search, graph storage, retrieval servers, or an MCP service.
- **A new AgentBundle primitive.** `.apm/knowledge/` and adapter-contract changes
  wait until an observed caller cannot be served by Skill-contained delivery.
- **Automatic proceduralization.** Facts, schemas, metrics, and references do
  not become Skills merely because they have titles and descriptions.
- **Execution of bundle code.** Executors, attesters, scripts, and remote
  resources remain inert unless a later, separately reviewed contract activates
  them.
- **A competing catalogue index or OKF fields in the public neutral index.**
  RFC-0076's existing `catalogue-index.json` remains authoritative for neutral
  cross-pack discovery. During the experiment it exposes the pack's existing
  metadata but receives no OKF-specific schema fields.
- **Publication of the pilot pack.** Cost engineering is a prototype caller;
  publication requires the catalogue pack-proposal workflow after results land.
- **Replacing human review with schemas.** Schemas establish structure; they do
  not establish truth, usefulness, licensing, or safe procedural meaning.

## Proposal

### D1 — Pack-local canonical OKF, delivered through Skills

An adopting pack gains one authoring-source directory:

```text
packs/<pack>/
├── pack.toml
├── okf/
│   └── <bundle>/
│       ├── index.md
│       ├── concepts/
│       └── playbooks/
└── .apm/skills/
    ├── <router>/
    │   ├── SKILL.md
    │   └── references/okf/       # generated copy of the bundle
    └── <projected-skill>/        # generated from an opted-in concept
        └── SKILL.md
```

`okf/<bundle>/` is canonical for knowledge. The compiler owns the router Skill,
the copied `references/okf/` tree, and every concept-derived Skill. Authors edit
the OKF concepts and pack metadata, then regenerate. Generated Skill directories
carry a machine-readable source path, profile version, and source digest as
string-valued marker keys in `metadata` plus a visible generated-file notice.

The pack declares managed bundles through its existing open extension table.
`projected-concepts` is the local review boundary: naming a concept here means a
maintainer reviewed the complete agent-facing projection identified by
`reviewed-projection-digest` and permits it to become a Skill.
Neither this declaration nor the concept extension grants tools.

```toml
[pack.metadata.okf]
profile = "agentbundle-okf/v1"

[[pack.metadata.okf.bundles]]
id = "cost-engineering"
path = "okf/cost-engineering"
router-skill = "cost-engineering"

[[pack.metadata.okf.bundles.projected-concepts]]
path = "playbooks/triage-ai-cost-anomaly.md"
reviewed-projection-digest = "sha256:..."
```

Whenever the table is present, it is validated by the dedicated OKF profile
schema. It does not become a core `pack.schema.json` field during the
experiment. This preserves
the distinction established by RFC-0031: `pack.toml` remains authoritative for
pack positioning, licensing, dependencies, categories, keywords, and links;
OKF remains authoritative for its concepts.

The experiment owns two OKF projection schemas at
`contracts/jsonschema/okf-pack-profile-v1.schema.json` and
`contracts/jsonschema/okf-agentbundle-extension-v1.schema.json`. Core
`pack.schema.json` continues to allow the metadata extension but does not absorb
its fields. The compiler owns `packs/<pack>/.okf-generated.json`, a committed
manifest of normalized source paths, managed output paths, and digests; it is
generated state, not an authoring source.

Each generated Skill marker uses the Agent Skills string-valued metadata keys
`generated-by`, `source-path`, and `source-digest`; `generated-by` is exactly
`agentbundle-okf/v1`. A concept-derived Skill additionally carries
`reviewed-projection-digest`; a router has no concept review tuple. The manifest
records a digest of the entire previously generated directory. A stale target
is removable only when that directory digest and all applicable marker values
still match the previous manifest.

The compiled router remains an ordinary `skill` primitive. The current
`direct-directory` projection copies its nested `references/okf/` tree to every
adapter, so no adapter-contract version bump is required.

### D2 — Authoring-time compiler; committed, drift-gated output

The experimental compiler belongs to a new authoring skill in the
`catalogue-curation` pack rather than the public AgentBundle CLI. It may use the
repository's existing authoring-only YAML dependency; AgentBundle's normal
installation and adapter build keep their dependency-free posture.

The compiler performs this fixed pipeline:

1. Load and validate `[pack.metadata.okf]` against its versioned profile schema.
2. Resolve `agentbundle-okf/v1` to OKF 0.2 without a network lookup, then parse
   each declared bundle as OKF 0.2 and validate concept frontmatter, paths, and
   `x-agentbundle` objects. The authored profile declaration is the version
   selection; an existing root index that declares another version fails.
3. Generate every hierarchical `index.md` file from concept metadata. The root
   index additionally carries compiler-emitted `okf_version: "0.2"` from the
   active profile mapping. In first-write mode an absent index is created; an
   existing index is replaceable only when its prior manifest digest and
   generated marker match. In check mode, generate indexes only in temporary
   staging and compare them with committed indexes. Authors never edit an
   `index.md` in a managed bundle.
4. Generate the router Skill and copy the complete managed bundle into its
   `references/okf/` directory.
5. Generate one Skill only when a valid `x-agentbundle.skill` declaration and
   its bundle's `projected-concepts` review entry name the same concept and the
   reviewed projection digest matches.
6. Emit the stable manifest of managed output paths and source digests. Stale
   removal is confined to the current pack's `.apm/skills/` root and is allowed
   only when the target is a real directory, contains the compiler's generated
   marker, and its current digest matches the previous manifest. A symlink,
   missing marker, changed digest, non-directory, or path outside that root is a
   hard failure requiring human resolution; cleanup never follows a glob.
7. In check mode, generate into a temporary directory and compare bytes with
   committed output; any difference is a catalogue verification failure.

Normal recipes and adapters receive only ordinary `.apm/skills/` and remain
projection-only. During the pilot, the `catalogue-curation` authoring skill at
`packs/catalogue-curation/.apm/skills/compile-okf/` owns one script interface:
`scripts/compile_okf.py --root <catalogue> --pack <name>` writes, and the same
invocation with `--check` stages and compares without modifying the pack. Every
failure has a versioned diagnostic identifier, nonzero exit status, and stable
path-sorted ordering; human-readable message prose is not a compatibility
surface. The implementation spec enumerates the identifiers before coding. A
successful two-caller experiment may
propose promotion to an optional `agentbundle catalogue compile-okf` command;
this RFC does not grant it.

### D3 — Explicit, versioned concept-to-Skill extension

OKF allows producer-defined frontmatter and requires consumers to tolerate
unknown fields. AgentBundle uses one namespaced object:

```yaml
---
type: Playbook
title: Triage an AI cost anomaly
description: Determine whether an AI workload cost change is expected or actionable.
x-agentbundle:
  profile: agentbundle-okf/v1
  skill:
    name: triage-ai-cost-anomaly
    description: Triage unexpected AI workload spend. Use for cost spikes or alerts.
    instruction-section: procedure
    include:
      - references/anomaly-signals.md
---
```

The extension schema requires a Skill-compatible name and an
activation-oriented description. For procedural concepts such as `Playbook`,
`instruction-section` names one Markdown section whose authored body supplies
the procedure. The compiler does not blindly transclude the whole concept. It
places only that reviewed section inside a fixed Skill template that separates
control instructions from cited source material, identifies the source path and
digest, and tells the agent to treat included sources as untrusted data rather
than instructions. The pack-local `reviewed-projection-digest` must match the
canonical projection tuple or compilation fails. That tuple contains the
profile version, normalized bundle-relative concept source path, Skill name,
activation description, resolved licence and compatibility, boundary list,
instruction-section identifier and normalized byte digest, the exact fixed
Skill-template source-byte digest, plus every include's normalized path and byte
digest. It therefore binds every generated provenance field to its source path,
and any agent-facing template edit invalidates review even if the profile
version is unchanged. The tuple is encoded as UTF-8 canonical JSON with sorted
keys and no insignificant whitespace, then hashed with SHA-256. Thus a change
to activation text, wrapper instructions, provenance, or reference context
invalidates review just as an instruction edit does. The `include` array is
optional, contains at most 64 bundle-relative regular-file paths, and copies
those files under generated `references/`; URLs, symlinks, directories, and a
link-in-place mode are not supported.

Generated router and concept Skills carry the repository's list-valued Agent
Skills extension `metadata.boundaries: [filesystem_read_untrusted]`. This is
separate from the string-valued generated markers and is a discovery
signal, not enforcement. Catalogue JSON derives its `boundaries` array from
this list. Generated Skills never contain `allowed-tools`; a later RFC and
security review would be required to introduce a tool-bearing mapping.

Concepts without `x-agentbundle.skill` remain discoverable OKF references.
Concepts with the extension but without a matching pack-local review entry also
remain references, but both write and check mode fail: unresolved projection
intent cannot silently ship.
Neither `type: Playbook`, a `# Steps` heading, a directory name, nor an AI
classification implicitly creates a Skill. Unknown non-AgentBundle extensions
are ignored by the compiler and preserved in the delivered OKF copy.

The JSON Schemas for the pack profile and concept extension carry explicit
`$schema` and `$id` values and their own profile version. An unsupported
AgentBundle profile fails compilation; an unknown unrelated OKF extension does
not.

### D4 — Knowledge is inert; reviewed instructions are explicit

An OKF bundle is untrusted content at the compiler boundary. The compiler:

- never executes an OKF executor, attester, script, or code fence;
- never converts OKF `runtime`, `executor`, or `attester` fields into Agent
  Skills `allowed-tools`;
- never fetches a URL or dereferences a remote `resource` during compilation;
- confines every declared path to the canonical bundle root after
  canonicalization and rejects path traversal, absolute filesystem paths,
  escaping symlinks, duplicate output names, and case-folding collisions;
- parses YAML with aliases and aggregate resource use bounded by the chosen
  parser and refuses unsupported tags or object construction;
- treats Markdown and instructions as untrusted prompt content, preserving
  provenance and keeping the router's control instructions in a generated
  wrapper rather than taking routing commands from a concept body.

The pilot security gate applies the repository's AST01/AST05 prompt-boundary
review to every projected instruction section and includes golden hostile
concepts that attempt instruction override, secret disclosure, tool escalation,
and source-path fabrication. The local digest records which complete projection
tuple was reviewed; it does not assert that the content is true or safe without
the review. Any changed tuple fails compilation and remains only canonical OKF
until its reviewed projection digest is updated. Thus canonical OKF can directly
author a Skill procedure, but only through a visible, content-addressed
instruction boundary.

Adding or updating a `projected-concepts` entry is a pack-maintainer assertion
subject to ordinary code review and the security-reviewer gate; the compiler
cannot mint the reviewed projection digest automatically in write mode. It may
print the candidate digest in a non-mutating diagnostic so the reviewer can
compare and copy it after reviewing the exact projection tuple.

Parsing is deliberately bounded. A managed bundle may contain at most 4,096
regular files and 2,000 concepts, occupy at most 32 MiB, and nest at most 16
directories. One Markdown file may be at most 2 MiB and its YAML frontmatter at
most 64 KiB. YAML explicit tags and aliases are rejected, object construction is
disabled, and parsed data may nest at most 20 levels. The profile schemas may
lower these limits but may not raise them during the experiment. Negative
fixtures exercise every limit.

A future Skill may intentionally invoke reviewed computation tooling, but that
binding is a separate security-boundary decision with explicit tool permissions,
tests, and security review. Attested Computation metadata alone never grants it.

### D5 — Two-caller experiment and promotion gate

The experiment uses two callers with different knowledge shapes:

1. **Cost-engineering prototype.** A non-published corpus derived from
   attribution-compatible Financial Operations (FinOps) guidance and the
   FinOps Open Cost and Usage Specification (FOCUS), covering estimation,
   allocation, anomaly triage, unit economics, workload optimization, and AI
   cost controls. It exercises external provenance, freshness, domain concepts,
   and procedural playbooks.
2. **Existing knowledge-heavy skill.** Project `security-checklists` into OKF
   without changing its user-facing behavior. Its router plus eleven
   boundary-keyed reference modules exercise established progressive disclosure
   and provide a repo-owned, hand-authored behavior baseline. The pilot authors
   its eval set before implementation because no existing eval set is assumed.

The pilot is not a published pack. Implementation proceeds through the two
Draft pilot specs, and results are recorded in
`docs/rfc/0087-notes/pilot-results.md`. This RFC remains `Accepted`; pilot
failure stops release and triggers an erratum or superseding RFC.

Promotion requires all of the following:

- both callers use one profile and compiler path with no caller-name or domain
  branches;
- two consecutive compiles of the same input produce byte-identical trees;
- all supported adapters preserve the delivered OKF bytes;
- unknown extension fixtures survive delivery unchanged;
- malformed profile, path escape, symlink escape, duplicate Skill, unsupported
  or missing OKF version, a deprecated concept selected in
  `projected-concepts`, and concepts that ask compilation to run an executor,
  attester, script, or remote resource fail with stable diagnostics;
- generated Skills pass the existing Agent Skills and catalogue lint gates;
- each caller has at least 20 cases in
  `docs/rfc/0087-notes/pilot-cases/<caller>.json`, with expected concept paths,
  forbidden paths, and at least five security-critical cases fixed before any
  baseline or generated run. Those cases cover instruction override, secret
  disclosure, tool escalation, path fabrication, and stale/deprecated routing;
- against the same recorded model and harness configuration, the generated
  router is run three times per case and variant. Its top-1 expected-path pass
  rate across at least 60 attempts per caller is at least 80% and no lower than
  the hand-authored baseline; every security-critical attempt passes and no run
  invents a concept path or source;
- a maintainer can update one concept, regenerate, and explain every resulting
  diff within 30 minutes without editing generated files.

Passing the experiment permits a follow-on decision; it does not automatically
create a public CLI command, a new primitive, or a published pack.

For this pilot, **supported adapters** means exactly Claude Code, Kiro IDE, Kiro
CLI, Copilot, Cursor, Codex, and Gemini as named in adapter contract v0.18. A
later adapter is outside the trial until its contract declares Skill
`direct-directory` preservation and repeats the byte fixture.

The RFC Approver is accountable for the experiment. The Approver may delegate
corpus preparation, implementation, and harness execution, but must confirm the
cases and baselines were frozen before generated runs, sign the pilot results,
and decide whether the accepted design is ready to ship or must be corrected or
superseded.

### D6 — Three-level discovery with one source per level

Discovery occurs at three different times and must not collapse into one field.

| Level | Consumer question | Source of truth | Produced/served surface |
| --- | --- | --- | --- |
| Pack | “Should I inspect or install this pack?” | `pack.toml` | Existing `catalogue-index.json`/marketplace projections, `list-packs`, and rich `show` metadata |
| Skill | “Should I activate this procedure?” | Authored Skill frontmatter or `x-agentbundle.skill` for generated Skills | Installed/generated `SKILL.md` name, description, licence, compatibility, metadata |
| Concept | “Which knowledge should I load now?” | OKF concept path and frontmatter | Generated hierarchical `index.md` files traversed by the router |

**Pack discovery.** `pack.toml` remains authored because pack purpose,
dependencies, licence, links, categories, and keywords are product/distribution
claims, not properties the compiler can safely infer from concepts. Existing
marketplace routes continue receiving their supported subset.

**Skill discovery.** Generated Skill frontmatter comes only from the validated
extension plus declared inheritance such as pack licence. The required
description says both what the Skill does and when to use it. The installed
agent tool discovers it through the ordinary Agent Skills mechanism; the
compiler does not create a second activation index.

**Concept discovery.** For every managed directory, the compiler generates an
OKF `index.md` from direct child directories and concept metadata. Entries use
the concept path, title, description, type, lifecycle state, and Skill-projection
flag. `concept_count` counts valid concept Markdown files below the bundle root,
excluding generated indexes and non-concept includes. Ordering is byte-stable by
normalized POSIX-style relative path after Unicode NFC normalization; paths that
collide when case-folded are rejected on every platform. A directory without a
valid child concept or sub-index is omitted. Duplicate concept identifiers,
invalid lifecycle values, and malformed concept frontmatter fail compilation.
Indexes contain no AI-written summary that is absent from canonical frontmatter
and no build timestamp. Authors express semantic grouping through the bundle
hierarchy and concept metadata, not by hand-editing generated indexes.

The router Skill body is generated from a fixed template. It directs the agent
to read the root index, descend through relevant sub-indexes, reject deprecated
entrypoints, surface staleness, and cite the concept path it used. It does not
inline the entire bundle into the initial prompt.

An **entrypoint** is a concept path exposed by a generated index. A deprecated
concept stays indexed and delivered for historical reference, with its state
visible, but the router must not select it as current procedural guidance and
must report the deprecation when asked for it directly. A deprecated concept in
`projected-concepts` is a compilation error; deprecation alone does not make the
raw reference invalid.

**Catalogue inspection.** Here, the **catalogue** is the local tree of authored
packs and **live-derived** means the command reads that tree on demand rather
than consulting a separately stored inventory. RFC-0060's live-derive rule
remains intact. On this authoritative source path,
`agentbundle show <pack> --format json` gains three additive fields while
preserving the existing `skills: [name, ...]` and `agents` arrays:

```json
{
  "name": "cost-engineering",
  "version": "0.1.0",
  "description": "Cost-engineering knowledge and procedures.",
  "skills": ["cost-engineering"],
  "agents": [],
  "integrations": [],
  "source": "catalogue",
  "pack_metadata": {
    "categories": ["devops"],
    "keywords": ["cost-engineering"],
    "license": "Apache-2.0 OR MIT"
  },
  "skill_metadata": [
    {
      "name": "cost-engineering",
      "description": "...",
      "license": "Apache-2.0 OR MIT",
      "compatibility": null,
      "generated_from": "okf/cost-engineering",
      "profile": "agentbundle-okf/v1",
      "digest": "sha256:...",
      "boundaries": ["filesystem_read_untrusted"]
    }
  ],
  "knowledge": [
    {
      "id": "cost-engineering",
      "format": "okf",
      "okf_version": "0.2",
      "router_skill": "cost-engineering",
      "content_license": "CC-BY-4.0",
      "concept_count": 24,
      "digest": "sha256:..."
    }
  ]
}
```

This is the full top-level response shape, not a replacement snippet. The new
keys are additive: `name`, `version`, `description`, `skills`, `agents`,
`integrations`, and `source` retain their current meaning, type, and
catalogue-versus-installed-state behavior. The additive response is an
allowlist governed as a complete response by
`contracts/jsonschema/agentbundle-show.schema.json`, not raw frontmatter
serialization. On an
authoritative source pack, `pack_metadata` is always an object,
`skill_metadata` has one entry per authored or generated `.apm/skills/`
directory, and `knowledge` is an array that is empty when no OKF bundle is
declared. Authored Skill entries use `null` for `generated_from`, `profile`, and
`digest`; their `boundaries` value is the authored list or an empty array.
`pack_metadata` exposes exactly `categories`, `keywords`, and `license`;
`skill_metadata` exposes exactly `name`, `description`, `license`,
`compatibility`, normalized-relative `generated_from`, `profile`, `digest`, and
`boundaries`; `knowledge` exposes exactly `id`, `format`, `okf_version`,
`router_skill`, `content_license`, `concept_count`, and `digest`. It never emits
concept bodies, absolute paths, remote-resource URLs, authors, source records,
or unknown provenance/extension fields. `content_license` comes from the
bundle's OKF licence declaration; a missing bundle licence may inherit the pack
licence only when that inheritance is explicit and SPDX-compatible, otherwise
compilation fails.

The installed-state fallback means inspection of an installed pack when its
authored catalogue source is absent. It remains honest: existing `skills` and
`agents` behavior is unchanged, while all three new keys are always present and
are `null`. Human-readable `show` and `list-packs` output do not change during
the experiment. RFC-0076's `catalogue-index.json` continues to expose existing
pack-level metadata and remains the only neutral cross-pack index. Its public
schema does not gain `skill_metadata` or `knowledge` during this experiment;
before public stabilization, the pilot outcome must either propose an RFC-0076
contract amendment or explicitly retain `show` as the only rich OKF inspection
surface.

### D7 — AI-assisted authoring; deterministic compilation

AI may participate before source review:

- extract and propose concepts from licensed sources;
- suggest titles, descriptions, tags, links, playbook bodies, and activation
  descriptions;
- propose pack positioning for a maintainer to accept in `pack.toml`;
- identify stale or unsupported knowledge for human review.

Every accepted value is committed as canonical OKF or pack metadata. OKF's
`generated` flag records machine assistance, `sources` records provenance,
`verified` records review state, `status` records lifecycle state, and
`stale_after` records the review-due date. These fields preserve provenance and
lifecycle without pretending machine generation is human review.

Compilation itself is deterministic and offline:

- same canonical bytes plus compiler/profile version produce the same bytes;
- output is UTF-8 with LF line endings and stable key/path ordering;
- no current time, random identifier, environment-specific absolute path,
  network result, or LLM output enters generated files;
- SHA-256 digests cover the exact UTF-8/LF bytes of every declared canonical
  input, its normalized relative path, and the profile version, encoded in
  sorted path order; no host path, timestamp, or generated index enters a source
  digest;
- check mode compiles twice and compares the two temporary output trees before
  comparing committed output;
- schema validation and golden input/output fixtures govern structure;
- human review governs truth, licence, usefulness, and safe procedural meaning.

### D8 — One pinned OKF version; reviewed replacement, not compatibility

The compiler carries one active support mapping:

| AgentBundle profile | Supported OKF version | Bundle declaration | Other versions |
| --- | --- | --- | --- |
| `agentbundle-okf/v1` | `0.2` | Authored profile selection; compiler-emitted `okf_version: "0.2"` in root `index.md` frontmatter | Fail with a version diagnostic |

The mapping is release data committed with the schemas and compiler; “latest”
never means a network lookup or an unpinned branch. An upstream version does not
become supported merely because OKF labels it backward-compatible. Its adoption
requires a reviewed behavior map covering bundle and index grammar, required and
optional fields, paths and links, provenance/trust/lifecycle semantics,
computation metadata, unknown-extension handling, and security boundaries.
Positive, negative, round-trip, and adapter-preservation fixtures must pass for
the new behavior.

If adopted, the new OKF version receives a new AgentBundle profile version. At
most one profile is active in a compiler release. The previous profile becomes
retired and that compiler rejects it with a migration diagnostic. The adopting
release must ship a reviewed source-migration note that maps every changed
behavior and gives deterministic manual conversion steps plus before/after
fixtures. An automated migration tool is optional and is not promised up front.
Existing committed Skill projections remain ordinary transportable files, but
their OKF source cannot be regenerated by the new compiler until migrated. This
is an intentional absence of backward-support commitment while both formats are
young, not a claim that migration will always be breaking.

## Options considered

Each table states the axis that makes its options collectively exhaustive and
includes the current do-nothing state.

### Source and delivery boundary

**Axis:** where knowledge crosses from pack authoring into an installed agent.
It can remain unsupported, live inside an existing primitive, gain a new
primitive, or remain external and be fetched at use time.

| Option | Prior art | Trade-off | Verdict |
| --- | --- | --- | --- |
| Do nothing | Ordinary Skill references today | No change; no governed canonical source or extension profile | Rejected |
| **Pack-local OKF source → Skill-contained delivery** | OKF permits subdirectory distribution; Agent Skills permit references | Reuses all adapters; adds one authoring convention and compiler | **Recommended** |
| New `.apm/knowledge/` primitive | AgentBundle's five projected primitive types | Clean first-class delivery, but every adapter and route changes before need is proven | Deferred |
| Runtime external fetch | Remote knowledge services | Independently updateable, but introduces availability, integrity, privacy, and trust dependencies | Rejected |

### Transformation time

**Axis:** the transformation can never run, run for the author, run in every
distribution build, or run in the adopter environment.

| Option | Prior art | Trade-off | Verdict |
| --- | --- | --- | --- |
| Manual/no compiler | Hand-authored Skills | No machinery; source and output drift | Rejected |
| **Authoring-time, committed output** | AgentBundle source projections; schema-generated source workflows | Reviewable generated diffs and simple installs; committed duplication is drift-gated | **Recommended** |
| Distribution-build compilation | Build-directory code generation | No committed output, but every route gains YAML/compiler coupling and reviewers cannot inspect generated source directly | Rejected for experiment |
| Adopter-time compilation | Local code generators | Customizable, but install becomes environment-dependent and mutating | Rejected |

### Projection-intent location

**Axis:** projection intent is absent, inferred from generic content, stored
beside the concept in a namespaced field, or stored in a separate sidecar.

| Option | Prior art | Trade-off | Verdict |
| --- | --- | --- | --- |
| Do nothing | Plain OKF | No generated Skills | Rejected |
| Infer from `type`/headings/path | Convention-based generators | Minimal metadata; silently invents procedure and activation semantics | Rejected |
| **`x-agentbundle.skill`** | OpenAPI `x-` specification extensions | Intent stays with source and remains valid OKF; requires a maintained schema | **Recommended** |
| Sidecar projection manifest | Generator configuration files | Keeps OKF pure; creates cross-file identity and drift | Rejected for experiment |

### Execution authority

**Axis:** authority can be absent, granted by explicit local review, inferred
from bundle metadata, or inherited from trusting the whole bundle.

| Option | Trade-off | Verdict |
| --- | --- | --- |
| Knowledge only forever | Safest; permanently excludes reviewed computation procedures | Viable fallback, not the selected extensible boundary |
| **Content-addressed reviewed instruction projection, with no tools** | Adds ceremony; preserves least authority | **Recommended** |
| Infer from executor/attester/type | Convenient; turns descriptive metadata into permission | Rejected |
| Trust all bundle code | Simple; unacceptable supply-chain and prompt-injection exposure | Rejected |

### Pilot scope

**Axis:** adoption can stop, exercise one caller, exercise two distinct callers,
or become catalogue-wide immediately.

| Option | Trade-off | Verdict |
| --- | --- | --- |
| Do nothing | No cost; no evidence | Rejected |
| One caller | Cheapest; cannot distinguish generic design from domain branching | Rejected |
| **Two bounded callers** | Enough variation to test genericity; still discardable | **Recommended** |
| Catalogue-wide rollout | Maximum adoption evidence; commits the shape before learning | Rejected |

### Discovery mechanism

**Axis:** discovery can remain implicit, be stored in one flat aggregate, be
generated probabilistically, or be layered deterministically by consumer.

| Option | Trade-off | Verdict |
| --- | --- | --- |
| Do nothing | Agents scan files or maintain lists manually; discovery gap remains | Rejected |
| Add OKF detail to `catalogue-index.json` now | Enables neutral cross-pack knowledge search; changes RFC-0076's public contract before the experiment proves the fields | Deferred to terminal acceptance |
| AI-generated router index during build | Rich semantic grouping; irreproducible and unreviewable drift | Rejected |
| **Layered deterministic discovery** | Three surfaces to specify; each derives from its own canonical metadata without a duplicate inventory | **Recommended** |

### AI participation boundary

**Axis:** AI can be excluded, used only before commit, invoked during builds, or
allowed to own both source and output without a deterministic gate.

| Option | Trade-off | Verdict |
| --- | --- | --- |
| Hand-author everything | Maximum direct control; forfeits scalable ingestion and curation | Not required |
| **AI-assisted canonical authoring + deterministic compiler** | Productive and reviewable; requires provenance discipline | **Recommended** |
| LLM in the build | Can fill gaps automatically; same source need not produce same output | Rejected |
| Unreviewed AI source and output | Fastest; cannot establish provenance, licence, truth, or stable behavior | Rejected |

### OKF version-support policy

**Axis:** a compiler release can support no OKF version, resolve a floating
latest version, support several historical versions, or support one pinned
version that is replaced through review.

| Option | Prior art | Trade-off | Verdict |
| --- | --- | --- | --- |
| Do nothing / best effort | OKF asks unknown consumers to attempt best-effort reading | Maximum tolerance; cannot guarantee deterministic projection semantics | Rejected for the compiler |
| Floating latest | Unpinned schema consumers | No upgrade ceremony; identical repository input can change behavior when upstream changes | Rejected |
| Multi-version compatibility | Mature compilers with maintained language editions | Eases migration; multiplies parser, fixture, and security branches before demand exists | No commitment during experiment |
| **One pinned active version** | Versioned schema/code generators | Small, auditable behavior surface; requires explicit migration when latest changes | **Recommended** |

## Risks & what would make this wrong

**Pre-mortem.** Assume the experiment shipped and failed:

- *Generated Skills drift from OKF.* Mitigation: compiler-owned paths, source
  digests, temporary regeneration, double-compile determinism, and CI drift
  failure.
- *A malicious concept becomes router instructions.* Mitigation: fixed router
  wrapper, a schema-addressed instruction section, matching pack-local review
  digest, hostile-content fixtures, inert computations, no tool inference,
  provenance surfaced, and security review of generated Skill bodies.
- *A path escapes the bundle or overwrites another Skill.* Mitigation:
  canonicalization, bundle-root confinement, symlink refusal, case-folded output
  collision checks, and a digest- and marker-guarded managed-output manifest.
- *Generated indexes flatten useful semantic structure.* Mitigation: directory
  hierarchy and concept metadata are author-controlled; the compiler renders
  rather than semantically clusters. Failure of this model in either pilot is a
  reason to reject or amend D6, not to add an LLM silently.
- *Pack, Skill, and concept descriptions contradict.* Mitigation: document their
  different jobs, derive generated Skill metadata only from the extension, and
  add lint for identical or non-activation-oriented descriptions rather than
  merging the fields.
- *The OKF specification changes beneath the profile.* Mitigation: pin supported
  OKF and AgentBundle profile versions; preserve unknown extensions within the
  pinned version; reject absent, older, or newer version declarations; require a
  behavior map and new profile before upgrading.
- *`show` becomes a de facto unstable registry API.* Mitigation: additive fields,
  preservation of current arrays, explicit nulls on installed-state fallback,
  schema fixtures, and no cross-pack aggregation in this RFC.
- *Licensing is lost during projection.* Mitigation: require pack and source
  attribution, carry licence references into generated Skill metadata, and make
  missing or incompatible licence data a pilot failure.

**Key assumptions (falsifiable).**

- Every current adapter preserves arbitrary nested regular files in a Skill.
  The spike verified this; a future adapter that does not must declare the
  degradation before claiming support for managed OKF packs.
- OKF concept frontmatter contains enough authored discovery metadata to build
  useful hierarchical indexes without semantic generation. The pilot retrieval
  tasks test this directly.
- Explicit `x-agentbundle.skill` declarations are acceptable authoring overhead.
  If both pilot maintainers bypass or duplicate them, the profile is wrong.
- Two distinct callers can share one compiler without domain branches. A branch
  on caller identity fails the promotion gate.
- Existing `catalogue-index.json` pack metadata plus live `show` inspection is
  sufficient for the trial. A demonstrated need for cross-pack concept search
  would trigger an explicit RFC-0076 schema amendment rather than a competing
  index or a silent field addition.
- Maintaining only the latest reviewed OKF version is acceptable during the
  experiment. A real adopter need to regenerate an older bundle would invalidate
  that assumption and require an explicit compatibility decision rather than an
  undocumented parser branch.

**Drawbacks.** This adds a new pack-source directory, two OKF projection
schemas, one complete `show` response schema, an authoring skill with a compiler,
generated files, new catalogue-verification work, and additive CLI JSON fields.
Authors must understand which files are
canonical. Committed generated output increases diffs and repository size. The
profile supports OKF rather than a format-neutral abstraction, and the first
implementation may be discarded if the experiment fails. Those are the accepted
costs of obtaining real evidence before a deeper engine or adapter commitment.

## Evidence & prior art

**Spike / de-risk result.** The riskiest assumption was that every current
adapter preserves an arbitrary nested OKF tree and unknown extension fields. A
temporary pack placed a router at `.apm/skills/okf-router/` and an OKF concept at
`references/okf/playbooks/triage.md`, including an unknown foreign frontmatter
object. Projection through Claude Code, Kiro IDE, Kiro CLI, Copilot, Cursor,
Codex, and Gemini produced a byte-identical concept at every target. The
temporary output trees were removed after the check; the fixture, executable
harness, command, SHA-256 digest, and observed paths remain in the linked
[adapter preservation spike](0087-notes/adapter-spike.md). This proves delivery,
not the compiler or retrieval behavior; those remain the experiment.

**Repo precedent.**

- [`contracts/adapter.toml`](../../contracts/adapter.toml) v0.18 declares
  `skill` as `direct-directory` for every current adapter family. RFC-0029
  already relies on nested Skill references for progressive disclosure.
- RFC-0001 established one source projected into per-tool outputs. RFC-0031 and
  ADR-0021 established authored rich metadata with lossy one-way projection.
- RFC-0060 and ADR-0049 deliberately derive pack inventory live from `.apm/`
  rather than persist a second inventory. D6 extends the live response with
  metadata while preserving that decision.
- RFC-0076 already establishes `catalogue-index.json` as the generated neutral
  semantic/discovery projection. D6 leaves its public schema unchanged during
  the trial and uses it only for existing pack-level discovery.
- RFC-0085 distinguishes catalogue authoring sources from generated installable
  artifacts, the distinction D1 applies inside a pack.
- [`contracts/pack.schema.json`](../../contracts/pack.schema.json) intentionally
  leaves `[pack.metadata]` open for extension data while keeping core pack fields
  closed and schema-enforced.
- [`packages/agentbundle/pyproject.toml`](../../packages/agentbundle/pyproject.toml)
  keeps AgentBundle's runtime dependency-free and already carries YAML only as
  an authoring/lint extra, supporting D2's placement outside normal builds.

**External prior art.** Every load-bearing citation below was fetched and
checked during RFC research:

- The [OKF v0.2 specification](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md),
  rechecked as the latest published version on 2026-08-15,
  defines directory/subdirectory distribution, concept frontmatter, permissive
  unknown fields, progressive `index.md` files, provenance and lifecycle
  signals, and inert Attested Computations. It explicitly does not define code
  packaging, invocation, serving, or sandboxing.
- The [Agent Skills specification](https://agentskills.io/specification) defines
  required `SKILL.md` name/description metadata and optional references, scripts,
  assets, licence, compatibility, and string-valued metadata. That is the target
  projection contract, not an AgentBundle invention.
- [OpenAPI 3.2 specification extensions](https://spec.openapis.org/oas/v3.2.0.html#specification-extensions)
  use `x-` namespaced fields for optional experimentation and recommend
  extensible implementations. This grounds the `x-agentbundle` pattern.
- [JSON Schema guidance](https://json-schema.org/understanding-json-schema/structuring)
  uses `$id` to give schemas non-relative identities, grounding the versioned
  extension schemas rather than an informal YAML convention.
- [Buf code generation](https://buf.build/docs/generate/) separates canonical,
  consumer-neutral schemas from configured generated outputs and pins generator
  inputs/plugins. This is comparable prior art for D2 and D7, not evidence that
  generated outputs must be committed.
- The [FinOps Framework reuse guidance](https://www.finops.org/introduction/how-to-use/)
  permits adaptation under CC BY 4.0 with attribution and change indication;
  the [FOCUS specification](https://github.com/FinOps-Open-Cost-and-Usage-Spec/FOCUS_Spec)
  supplies a versioned, vendor-neutral cost vocabulary. These make the D5
  prototype legally and structurally plausible; they do not approve the pack.

The fuller ecosystem and demand analysis remains in the linked
[research survey](../product/research/google-okf-agentbundle-survey.md). Public
search did not find a mature, deterministic OKF-to-Agent-Skills compiler with
extension preservation. The survey calls that **moderate confidence**: enough
evidence to justify a reversible experiment, but not enough to claim ecosystem
absence because the conclusion depends on a negative search in a young field.

## Experiment / validation

**Hypothesis.** A schema-governed, deterministic compiler can project two
different OKF knowledge corpora into portable, discoverable Agent Skills without
domain-specific code, losing unknown extensions, widening execution authority,
or regressing the callers' routing behavior.

**What we measure.**

- Byte equality and output-tree equality across repeat compilation and every
  adapter.
- Schema and security-rail behavior over positive and negative golden fixtures.
- Generated Skill conformance and catalogue verification.
- Pack, Skill, and concept discovery through `show --format json`, installed
  Skill metadata, and router traversal respectively.
- Activation and output behavior against the pre-registered cases under
  `docs/rfc/0087-notes/pilot-cases/` and the corresponding hand-authored
  baseline results under `docs/rfc/0087-notes/pilot-baselines/`.
- Maintainer effort and explanatory diff size for one realistic knowledge
  update per caller.
- Compiler code paths taken by each caller; any caller-name/domain condition is
  recorded as a genericity failure.

**Success criteria.** Every structural and security criterion in D5 passes.
Each caller contributes at least 20 pre-registered cases. Using the same
recorded model and harness configuration for baseline and generated variants,
three runs per case produce at least 60 attempts per caller. The generated
router's top-1 expected-path pass rate is at least 80% and at least the baseline
rate; all security-critical attempts pass, and fabricated paths/sources remain
zero. The update exercise finishes within 30 minutes and requires no
generated-file edit.
Any execution of bundle content, non-deterministic diff, unconfined path, lost
unknown extension, or caller-specific compiler branch is an immediate failure
rather than a warning.

**Result handling.** Results go to
`docs/rfc/0087-notes/pilot-results.md`, including commands, fixtures, measured
outputs, and failures. This RFC remains `Accepted` while results are pending.
The Approver signs passing results before release; failing results stop release
and require an erratum or superseding RFC.

## Open questions

None. The source location, projection time, extension, authority boundary,
pilot scope, discovery contract, AI/determinism boundary, and single-version
support policy are the decisions requested in this RFC. Implementation details
that do not alter those contracts belong in the pilot plan and schemas.

## Follow-on artifacts

This RFC was accepted before implementation. The following artifacts remain
required before the feature is shipped or described as stable:

- **Pilot spec (authored, Draft):** `docs/specs/okf-authoring-projection/` — schemas, the
  `catalogue-curation` authoring skill/compiler, generated-output ownership,
  OKF-version support map and upgrade behavior, validation/security rails,
  fixtures, and drift gate.
- **Pilot spec (authored, Draft):** `docs/specs/okf-catalogue-discovery/` — additive `show --format json`
  fields, live-source behavior, installed-state degradation, and compatibility
  tests.
- **Pre-release architecture note:** Update `docs/architecture/pack-layout.md`
  and `docs/architecture/agentbundle.md` with the explicitly pre-release source,
  generated-output, and discovery surfaces so the pilot does not create
  undocumented reality.
- **Pilot evidence:** Commit the pre-registered cases and baselines described in
  D5, then write measured results to `docs/rfc/0087-notes/pilot-results.md`.

Acceptance produces these follow-ons:

- **ADR:** Record pack-local OKF as canonical knowledge with deterministic,
  one-way Skill and discovery projections.
- **Convention:** Add the managed-generated-output rule to
  `docs/CONVENTIONS.md` as a supported catalogue convention.
- **Catalogue proposal:** Run `propose-catalogue-pack` for cost engineering;
  pilot evidence informs but does not replace its additive/frequency review.
- **Possible follow-on RFCs, only if evidence demands them:** a public
  `agentbundle catalogue compile-okf` command, a new `.apm/knowledge/` primitive,
  or an RFC-0076 amendment adding OKF summaries to `catalogue-index.json`.

## Errata

The body above is frozen. Corrections are appended here, and where this section
disagrees with the body, this section is authoritative.

- **2026-08-15 (pre-acceptance):** The Approver confirmed one pinned active OKF version
  with no up-front backward-support or automated-migration commitment. D8 maps
  `agentbundle-okf/v1` to OKF 0.2. The authored profile selects that version;
  the compiler wholly owns every managed `index.md` and emits the mapped version
  in root frontmatter. Reviewed manual migration instructions and fixtures are
  required before a later profile replaces it.
- **2026-08-15 (pre-acceptance):** The Approver confirmed that all three experimental
  interface contracts use the repository's canonical `contracts/jsonschema/`
  location. The discovery schema governs the complete `agentbundle show`
  response so deterministic consumers do not have to compose an undocumented
  legacy shape with an OKF-only fragment.
- **2026-08-15 (acceptance):** The Approver accepted the architecture directly
  and waived the optional `Experimental` RFC lifecycle stop. This is not a
  waiver of implementation evidence: both Draft specs, both pilots, their
  security/determinism gates, the architecture update, and the ADR remain
  release prerequisites. Failed evidence requires correction or supersession;
  it may not be hidden by a caller-specific branch.

### E1 — The pilot baselines are not model runs, so AC26's "same model" and AC27's relative floor cannot be satisfied (2026-08-19) · ✅ signed off: eugenelim (RFC-0087 Approver), 2026-08-19

**§ Experiment / validation states: "Using the same recorded model and harness
configuration for baseline and generated variants ... The generated router's
top-1 expected-path pass rate is at least 80% **and at least the baseline
rate**."** Neither clause is satisfiable against the committed baselines.

`pilot-baselines/cost-engineering-hand-authored.json` records
`"model": "manual-hand-authored-baseline"`, `"baseline_kind":
"hand-authored-router"`, and an `invocation_record` stating "no model, network,
or external content used". It is an expected-answer key derived from the
committed OKF concepts, not a model run, so no model run can be "the same
model" as it.

The same file records `top_1_expected_path_success: 1.0`. A hand-authored key is
correct by construction, so "at least the baseline rate" sets the real bar at
100% across 60 attempts rather than the 80% the same sentence states. The two
thresholds disagree, and the stricter one is an artefact of the baseline's
provenance rather than a quality decision anyone made.

`security-checklists-pending-model-e2e.json` is a placeholder: `status:
"pending"`, summary fields `null`.

**Narrowed boundary:**

1. The hand-authored file is a frozen **expected-answer key**. AC26's parity
   clause is restated as "the generated router is compared against the frozen
   expected-path key".
2. AC27 becomes a **report-only measurement**: the absolute >=80% top-1 rate and
   the zero-fabricated-paths figure are recorded and published; the relative
   "at least the baseline rate" clause is withdrawn.
3. **Security-critical attempts remain a hard gate.** D4's authority boundary is
   not relaxed; a failed security-critical attempt still stops release.
4. The measurement carries an explicit fidelity label, per the shipped
   `pack-activation-evals` convention (`mode` / `fidelity` / `provenance`).
5. The calibrated model-graded arm is deferred by name in
   `workspace.toml [backlog].open` with its unblock condition.

**Precedent.** `spec/pack-activation-evals` (RFC-0037 / ADR-0028, Shipped) already
makes evals report-only and never a merge gate, keeps `make build-check` free of
any live-model step, labels fidelity rather than assuming it, and defers what
cannot be measured by name. RFC-0037 narrowed its own criteria three times
through errata. This follows that precedent rather than creating an exemption.

**What this erratum does not do.** It does not relax D4's authority boundary,
waive D5's structural or security criteria, reduce the two-corpus pilot scope,
or authorise release.

### E2 — AC22's write-mode arm is unavailable on Windows by design; check mode is the evidence there (2026-08-19) · ✅ signed off: eugenelim (RFC-0087 Approver), 2026-08-19

**AC22 requires "two write-mode compiles ... produce byte-identical complete
managed trees on Linux and Windows CI runners and in a recorded local macOS
verification."**

`_apply_outputs_transactionally` refuses when `os.supports_dir_fd` is empty,
returning `OKF010 "safe managed output writes are unavailable on this
platform"`. That set is empty on Windows. The dir-fd confinement is a deliberate
security control, so a Windows write path cannot exist without weakening it.

**Narrowed boundary:** where managed writes are unavailable, the determinism
evidence is **check mode** — re-render plus committed-byte comparison. Write
mode remains the evidence on Linux and macOS.

Evidence satisfying AC22 as narrowed:

- Windows CI, run 32221115655 on `main` d652cff9 (2026-08-19T05:54Z):
  `okf-check: OK _okf-pilot-cost-engineering` and `okf-check: OK core`.
- Linux CI: the same gate runs in `gate-main` through the catalogue pre-PR
  aggregator.
- macOS local, 25.5.0 arm64 / CPython 3.13.13: two write-mode compiles of both
  managed packs leave the tree byte-identical.

A second cause originally recorded against AC22 — `core`'s ownership conflict —
was repaired and is not part of this erratum.
