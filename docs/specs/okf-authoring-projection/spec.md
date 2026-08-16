# Spec: OKF authoring projection

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0087
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/okf-pack-profile-v1.schema.json`](../../../contracts/jsonschema/okf-pack-profile-v1.schema.json), [`contracts/jsonschema/okf-agentbundle-extension-v1.schema.json`](../../../contracts/jsonschema/okf-agentbundle-extension-v1.schema.json)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Catalogue maintainers can author one or more OKF 0.2 knowledge bundles beneath a
pack, use a deterministic `compile-okf` Skill to project those bundles into
portable router and reviewed procedure Skills, and prove that committed output
matches canonical source. The same profile and compiler serve the
cost-engineering and `security-checklists` pilots without domain- or
caller-specific branches. Compilation is offline, confines all reads and writes
to declared pack roots, preserves inert knowledge and unknown extensions, and
never turns descriptive OKF computation metadata into execution authority.

## Boundaries

The canonical/source, generated/output, and instruction/data boundaries in
RFC-0087 apply to every compiler mode and pilot fixture.

### Always do

- Treat `packs/<pack>/okf/<bundle>/` plus `[pack.metadata.okf]` as canonical and
  treat compiler-owned indexes, `.apm/skills/` projections, and
  `.okf-generated.json` as replaceable generated output.
- Treat every managed `index.md` as wholly compiler-owned. Derive the root
  `okf_version: "0.2"` field from the authored `agentbundle-okf/v1` profile
  selection and reject a conflicting committed value with a stable diagnostic.
- Resolve and confine every filesystem path before reading, staging, copying,
  replacing, or removing it; process only regular files and reject symlinks.
- Keep every OKF executor, attester, script, code fence, remote resource, and
  unknown non-AgentBundle extension inert while preserving source bytes in the
  router's delivered OKF tree.
- Require both a valid `x-agentbundle.skill` declaration and a matching
  content-addressed pack-local review record before generating a procedure
  Skill.

### Ask first

- Ask the RFC Approver before changing the supported OKF version, the
  `agentbundle-okf/v1` profile, a resource bound, or the projection digest
  tuple.
- Ask before introducing tool permissions, executable bundle content, remote
  retrieval, or any authority beyond filesystem reads of untrusted knowledge.
- Ask before publishing the cost-engineering prototype, promoting the compiler
  into the AgentBundle CLI, or adding an AgentBundle primitive or adapter rule.
- Ask before replacing deterministic manual migration instructions with a
  compatibility promise or keeping more than one active OKF profile.

### Never do

- Never use an LLM, network response, current time, random value, host-specific
  absolute path, or environment-dependent ordering during compilation.
- Never infer projection intent from concept type, headings, prose, directory
  placement, executor metadata, or an AI classification.
- Never edit a generated file as its own source of truth, follow a symlink, use
  a glob for cleanup, or remove an output whose manifest digest and generated
  markers do not match.
- Never add a runtime dependency to the base `agentbundle` package or a new
  top-level repository directory for this experiment.
- Never add caller names, cost terminology, or security-boundary names to the
  generic compiler path.

## Testing Strategy

- **Schema and validation rules — TDD.** Positive and negative fixtures exercise
  both JSON Schemas, OKF 0.2 parsing, every resource limit, every path/file-type
  rail, lifecycle rules, and the review-digest boundary because these are
  compressible invariants with exact expected diagnostics.
- **Projection and ownership — TDD.** Golden trees cover index generation,
  router and procedure Skill rendering, source and projection digests, manifest
  ownership, safe stale cleanup, and hostile-content isolation. Property-style
  cases vary path spelling, file order, Unicode normalization, case, and
  repeated execution.
- **Determinism and drift — goal-based checks.** The check command compiles the
  same input twice in independent temporary trees, compares those trees, then
  compares committed output without mutating it. A repository gate runs this
  path for every managed pilot pack.
- **Delivery — goal-based integration checks.** Existing build adapters project
  a generated router with nested OKF references; byte comparisons cover Claude
  Code, Kiro IDE, Kiro CLI, Copilot, Cursor, Codex, and Gemini.
- **Pilot usefulness and safety — recorded E2E evaluation.** Each caller uses a
  frozen hand-authored baseline and at least 20 pre-registered routing cases,
  including at least five security-critical cases, under the model/harness and
  thresholds fixed by RFC-0087. This validates the user outcome rather than
  compiler structure alone.

## Acceptance Criteria

- [ ] **AC1:** `okf-pack-profile-v1.schema.json` accepts the documented
  `[pack.metadata.okf]` shape, fixes `profile` to `agentbundle-okf/v1`, validates
  bundle IDs, pack-relative `okf/` paths, router Skill names, projected concept
  paths, and `sha256:` review digests, and rejects unknown profile properties.
- [ ] **AC2:** `okf-agentbundle-extension-v1.schema.json` accepts only the
  documented `x-agentbundle` object, requires a Playbook projection to name its
  profile, Skill name, activation description, and instruction section, limits
  includes to 64 unique confined relative file paths, and rejects unknown
  AgentBundle extension properties.
- [ ] **AC3:** The compiler supports exactly the mapping
  `agentbundle-okf/v1` → OKF `0.2`, performs no version lookup, and emits
  `okf_version: "0.2"` into compiler-owned root `index.md` frontmatter. Write
  mode creates an absent first index; check mode reports it as `OKF011` drift.
  An existing root with a missing, older, newer, or non-string value conflicts
  with the active profile and fails as `OKF002` in either mode.
- [ ] **AC4:** A replacement profile cannot become active unless its checked-in
  behavior map, positive/negative/round-trip fixtures, adapter-preservation
  fixtures, deterministic manual migration instructions, and before/after
  source fixtures are present; no automated migrator or simultaneous older
  profile is required.
- [ ] **AC5:** `compile_okf.py --root <catalogue> --pack <name>` writes only the
  selected pack's compiler-owned `index.md` files, `.apm/skills/` projections,
  and `.okf-generated.json`; `--check` writes nothing beneath the catalogue.
- [ ] **AC6:** A successful invocation exits 0. Input, schema, content,
  security, path, collision, and ownership failures exit 1. Drift or a repeated
  compile that differs exits 2. Every failure line begins with one identifier
  from `OKF001`–`OKF012`, uses normalized repository-relative paths, and is
  sorted by identifier then path.
- [ ] **AC7:** The diagnostic registry is fixed as: `OKF001` invalid pack
  profile; `OKF002` unsupported or missing OKF version; `OKF003` malformed OKF
  concept/index; `OKF004` unsafe path or file type; `OKF005` resource limit;
  `OKF006` duplicate or case-folded output collision; `OKF007` unresolved or
  ineligible projection intent; `OKF008` review-digest mismatch; `OKF009`
  prohibited execution or remote retrieval request; `OKF010` generated-output
  ownership conflict; `OKF011` committed-output drift; `OKF012`
  non-deterministic repeated compilation.
- [ ] **AC8:** Parsing rejects YAML explicit tags and aliases, disables object
  construction, and rejects structures deeper than 20 levels without
  executing constructors or resolving remote references.
- [ ] **AC9:** A bundle is rejected before generation if it exceeds 4,096
  regular files, 2,000 concepts, 32 MiB total bytes, 16 directory levels,
  2 MiB for one Markdown file, or 64 KiB of frontmatter; boundary-equal fixtures
  pass and boundary-plus-one fixtures fail as `OKF005`.
- [ ] **AC10:** Absolute paths, `..` traversal, backslash variants, ASCII
  controls, Windows-reserved characters or device-name segments, trailing dots
  or spaces, escaping symlinks, symlink inputs or outputs, non-regular files,
  duplicate normalized paths, and Unicode-NFC or case-folded collisions fail
  before any pack write on every host.
- [ ] **AC11:** Every managed `index.md` is wholly compiler-owned, carries a
  first-body-line marker exactly
  `<!-- agentbundle-managed: profile=agentbundle-okf/v1 kind=okf-index -->`, is
  generated solely from valid direct children and canonical concept metadata,
  omits empty branches, counts concepts according to RFC-0087, and sorts entries
  by NFC-normalized POSIX relative-path bytes without timestamps or invented
  summaries. The root also carries the profile-derived OKF version; no index
  mixes authored and generated regions.
- [ ] **AC12:** The generated router reads the root index first, descends only
  through named child indexes, reports stale or directly requested deprecated
  knowledge, refuses deprecated procedural entrypoints, and cites the selected
  normalized concept path without loading the full bundle into its initial
  body.
- [ ] **AC13:** A concept procedure Skill is generated only for `type: Playbook`
  with a valid `x-agentbundle.skill` declaration and an exact matching
  `projected-concepts` entry; declared projection intent without either half
  fails as `OKF007`, and a deprecated projected concept fails as `OKF007`.
- [ ] **AC13a:** `instruction-section` is an NFC-normalized, case-sensitive
  identifier with no leading/trailing whitespace that selects exactly one
  unfenced level-2 ATX heading whose source line is `## <identifier>`. Its body
  starts after that heading and ends before the next unfenced level-1 or level-2
  ATX heading, retaining nested level-3–6 headings. Missing, duplicate, empty,
  Setext, inline-formatted, closing-hash, or fenced-code-only matches fail as
  `OKF007`; normalized LF UTF-8 body bytes are the projected instruction bytes.
- [ ] **AC14:** The review digest is SHA-256 over canonical JSON containing the
  profile, normalized bundle-relative concept source path, Skill name and
  activation description, resolved licence and compatibility, boundary list,
  instruction-section identifier and SHA-256 of its normalized bytes, SHA-256
  of the exact fixed Skill-template source bytes, and an ordered list of every
  include's normalized path and byte SHA-256. The tuple uses UTF-8 canonical
  JSON with sorted keys and no insignificant whitespace; published golden
  encoding/digest vectors fix the representation. Any tuple change fails as
  `OKF008` until a maintainer records the newly printed candidate digest.
- [ ] **AC15:** A generated procedure Skill contains only the reviewed Markdown
  section inside the fixed wrapper, copies at most 64 declared regular-file
  includes, labels included content as untrusted data, and contains no
  `allowed-tools` field.
- [ ] **AC16:** Router and generated procedure Skills carry `generated-by`,
  `source-path`, and `source-digest` string markers plus
  `metadata.boundaries: [filesystem_read_untrusted]`; procedure Skills also
  carry `reviewed-projection-digest`.
- [ ] **AC17:** Executor, attester, runtime, code-fence, script, and remote
  resource metadata never invokes code, grants tools, performs network I/O, or
  enters router control instructions. Hostile fixtures prove instruction
  override, secret disclosure, tool escalation, and fabricated source paths
  remain data.
- [ ] **AC18:** The router's `references/okf/` tree preserves every canonical
  regular file and unknown non-AgentBundle extension byte-for-byte except
  compiler-owned generated `index.md` files, whose bytes match the staged
  canonical output.
- [ ] **AC19:** `.okf-generated.json` contains only the profile, normalized
  managed source/output paths, managed kind, exact expected marker, source and
  complete-output digests, with stable UTF-8/LF serialization and no time, host
  path, or nondeterministic value. Every index record uses kind `okf-index` and
  the exact AC11 marker.
- [ ] **AC20:** Stale Skill-output removal occurs only for a real directory
  beneath the selected pack's `.apm/skills/` root whose complete current digest
  and applicable generated markers match the prior manifest. A managed
  `index.md` is created only when absent and is replaced or removed only when
  its complete bytes, exact AC11 first-body-line marker, and manifest marker
  value match the prior manifest. Every mismatch fails as `OKF010` and leaves
  the path untouched.
- [ ] **AC21:** `--check` stages two independent compiles, fails as `OKF012` if
  their trees differ, otherwise fails as `OKF011` for any committed drift, and
  leaves source, generated output, stdout-visible candidate review values, and
  the working tree unchanged.
- [ ] **AC22:** Two write-mode compiles from identical canonical bytes and
  profile/compiler versions produce byte-identical complete managed trees on
  macOS, Linux, and Windows test runners.
- [ ] **AC23:** Claude Code, Kiro IDE, Kiro CLI, Copilot, Cursor, Codex, and
  Gemini projections preserve the generated router's nested OKF regular-file
  bytes and pass existing Agent Skills/catalogue lint rules.
- [ ] **AC24:** `catalogue-curation` ships the `compile-okf` Skill and script,
  declares its authoring-time PyYAML prerequisite without adding a base
  AgentBundle runtime dependency, includes activation and behavior evals, and
  receives the required synchronized minor pack/plugin version bump and
  changelog entry.
- [ ] **AC25:** Both pilot corpora compile through the same functions and
  profile with no condition on caller, pack, bundle, cost, FinOps, security, or
  boundary names; an instrumentation test records the same generic pipeline
  stages for both.
- [ ] **AC25a:** The cost pilot is a complete but non-published pack-shaped
  fixture at `packs/_okf-pilot-cost-engineering/`. The compiler may select that
  exact immediate child by its `--pack` value even though underscore-prefixed
  authoring assets remain absent from normal catalogue discovery and publishing.
  Discovery CLI tests stage the same pack bytes under a temporary discoverable
  catalogue path; production `list-packs` and marketplace behavior stay
  unchanged.
- [ ] **AC26:** Before generated pilot evaluation, each caller has at least 20
  frozen cases with expected and forbidden concept paths, at least five fixed
  security-critical cases, and a recorded hand-authored baseline using the same
  model and harness configuration.
- [ ] **AC27:** Each generated router runs three times per frozen case, reaches
  at least 80% top-1 expected-path success and no lower than its hand-authored
  baseline, passes every security-critical attempt, and fabricates zero concept
  paths or sources.
- [ ] **AC28:** A maintainer changes one canonical concept per caller,
  regenerates without editing generated files, and explains every resulting
  diff within 30 minutes; commands, results, failures, and timing are recorded
  in `docs/rfc/0087-notes/pilot-results.md`.
- [ ] **AC29:** The repository's verification path runs `compile-okf --check`
  for every declared pilot bundle and fails on schema, safety, determinism, or
  committed-output drift without changing normal adapter installation behavior.

## Assumptions

- Technical: OKF 0.2 is the latest published version and the only version this
  experiment supports (source: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md, checked 2026-08-15).
- Technical: AgentBundle targets Python 3.11+ and keeps its base runtime free of
  dependencies; PyYAML is already an optional lint/authoring dependency
  (source: `packages/agentbundle/pyproject.toml`).
- Technical: every current adapter declares or demonstrates direct-directory
  Skill preservation for nested references (source: `contracts/adapter.toml`
  and `docs/rfc/0087-notes/adapter-spike.md`).
- Product: the compiler serves catalogue maintainers and the two experimental
  callers are a non-published cost-engineering prototype and the existing
  `security-checklists` Skill (source: RFC-0087 D5; user confirmation
  2026-08-15).
- Process: a new `catalogue-curation` Skill requires a minor pack version bump,
  matching plugin version, eval coverage, self-host projection, and changelog
  entry (source: `packs/AGENTS.md` and `packs/AGENTS.local.md`).
- Process: the two OKF contracts are standalone JSON Schemas under
  `contracts/jsonschema/`; no JSON Schema authoring skill is installed, so they
  are directly authored without rule-enforcement and validated with the
  repository toolchain (source: `docs/CONVENTIONS.md`; user confirmation
  2026-08-15).
- Process: RFC-0087 is Open and the Approver signs the frozen cases, pilot
  results, and any transition to Experimental or a terminal state (source:
  RFC-0087 lifecycle and D5).
