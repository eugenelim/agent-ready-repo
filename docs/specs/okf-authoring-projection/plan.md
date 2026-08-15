# Plan: OKF authoring projection

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as implementation evidence changes.

## Approach

Implement the experiment as a pack-local authoring tool, not an AgentBundle
runtime command. Start from the two approved JSON Schema contracts and a golden
fixture corpus; add a small Python compiler beneath the shipped `compile-okf`
Skill; separate pure parsing/normalization/rendering from guarded filesystem
application; then exercise the same pipeline against the two pilots. Generated
outputs remain ordinary `.apm/skills/` directories, so existing adapters and
install routes stay unchanged. Repository verification invokes check mode for
the managed pilot packs, while the pilot harness records behavioral evidence
outside shipped pack content.

## Constraints

- RFC-0087 D1–D8 govern source ownership, projection time, authority,
  discovery, determinism, pilot scope, and the single-version support policy.
- `contracts/jsonschema/okf-pack-profile-v1.schema.json` and
  `contracts/jsonschema/okf-agentbundle-extension-v1.schema.json` are the
  interface contracts. Runtime validators and fixtures must agree with them.
- The shipped Skill and script contain no repository-only RFC/spec citations;
  implementation tests may trace to this spec.
- Python 3.11 is the minimum runtime. PyYAML may be an explicit authoring
  prerequisite, but `packages/agentbundle` retains an empty base dependency
  list.
- All source reads, temporary staging, output application, and stale cleanup
  follow the pack path-confinement and no-symlink rules.
- This plan adds no public CLI verb, adapter primitive, new top-level directory,
  or published cost-engineering pack.

## Construction tests

**Integration tests:**

- Run the same compiler entrypoint and instrumented stage registry over both
  pilots; assert no caller/domain branch and byte-identical repeated outputs.
- Project one generated router through all seven adapter families and compare
  the nested OKF tree against the canonical generated Skill references.
- Run the repository verification entrypoint against clean, drifted, hostile,
  and ownership-conflicted pilot trees; assert expected exits and no mutation in
  check mode.
- Run the frozen routing harness against baseline and generated variants and
  write the reproducible result record required by RFC-0087.

**Manual verification:**

- For one canonical concept in each pilot, a maintainer regenerates, reviews
  the diff, records elapsed time, and confirms no generated file was edited.
- The RFC Approver confirms case/baseline freeze before generated runs and signs
  the resulting evidence before an `Open` → `Experimental` transition.

## Design (LLD)

### Design decisions

- One compiler release exposes one immutable `Profile` value:
  `agentbundle-okf/v1` maps to OKF 0.2. A dispatch table makes the mapping
  explicit without retaining inactive parsers. Traces to AC3–AC4.
- Parsing and rendering are pure over bytes and normalized relative paths;
  filesystem discovery and application sit at the edges. This makes repeated
  compile and host-independence directly testable. Traces to AC21–AC22.
- JSON Schemas describe the external TOML/YAML-shaped extension objects; typed
  Python validation enforces cross-file uniqueness, filesystem, Markdown, and
  security rules schemas cannot express. Traces to AC1–AC18.
- The compiler prints candidate review digests but never writes them into
  canonical source. Human review remains the authority boundary. Traces to
  AC13–AC17.

### Data & schema

- `PackProfile` owns `profile` and an ordered set of `BundleDeclaration`
  records. A declaration owns `id`, pack-relative `path`, `router-skill`, and
  zero or more reviewed projection records.
- `AgentBundleExtension` owns the profile and one `SkillProjection` containing
  name, activation description, instruction-section identifier, and confined
  includes.
- `NormalizedBundle` contains immutable concept/index records keyed by
  NFC-normalized POSIX paths. It retains canonical bytes separately from parsed
  discovery fields.
- Every `index.md` is a generated record. Root version metadata comes from the
  profile dispatch table; index markers and prior manifest bytes govern safe
  replacement exactly as generated Skill markers govern output ownership. The
  first body line is the fixed AC11 HTML marker; the manifest repeats that exact
  marker beside kind `okf-index` and the complete file digest.
- `GeneratedManifest` stores the active profile, normalized managed paths,
  source digests, complete generated-directory digests, and marker values. Its
  serialization is stable JSON with UTF-8/LF and sorted keys.
- The review tuple is canonical JSON with sorted keys and compact separators;
  it contains only normalized paths, scalar/list metadata, and named SHA-256
  byte digests—not embedded source bytes. All digests use lowercase SHA-256
  prefixed by `sha256:` and are pinned by golden vectors.

### Interfaces & contracts

- `scripts/compile_okf.py --root <catalogue> --pack <name> [--check]` is the
  only compiler process interface. Write is the default; check is read-only.
- Exit status 0 means success, 1 means rejected input/authority/ownership, and 2
  means drift or internal non-determinism. Diagnostics implement AC6–AC7.
- The profile and extension inputs implement the two JSON Schemas linked from
  the spec. Cross-field and filesystem invariants are additive compiler checks,
  not undocumented relaxations of those contracts.

### Component / module decomposition

- `compile_okf.py` is the thin CLI and orchestration boundary.
- `okf_compiler.py` owns typed records, bounded YAML/frontmatter parsing,
  normalization, validation, deterministic index/router/procedure rendering,
  hashing, manifests, and safe apply/check operations. It stays importable by
  tests without process spawning.
- Skill-local templates under `assets/` are canonical compiler inputs whose
  bytes participate in review/source digests; generated copies are never
  imported back as templates.
- Skill tests own focused fixtures. RFC evidence owns frozen pilot cases,
  baselines, results, and timing so adopter-facing pack content carries no
  repository governance references.

### State & control flow

1. Resolve the catalogue and selected real pack directory without following a
   pack or bundle symlink.
2. Load the TOML extension and validate the active profile contract.
3. Inventory bounded regular files, inspect any existing root version for a
   profile conflict, parse concepts, normalize paths, and accumulate all
   diagnostics before generation.
4. Render wholly generated canonical indexes (including the profile-derived
   root version), router, reviewed procedure Skills, copied references, and
   manifest into an isolated staging directory.
5. Compile again into a second staging directory and compare complete trees.
6. In check mode, compare staging with committed files and return without pack
   writes. In write mode, preflight every existing managed target against the
   prior manifest before applying replacements or safe stale removals.

### Behavior & rules

- Validation is fail-closed for the supported profile and `x-agentbundle`
  namespace, but preserves and ignores unrelated OKF extensions.
- Indexes derive only from authored metadata and hierarchy. Router control text
  comes only from fixed templates; concept prose is cited data unless a reviewed
  instruction section crosses the projection boundary.
- Instruction selection recognizes only an exact NFC-normalized level-2 ATX
  source line, tracks CommonMark backtick or tilde fences of at least three
  characters so headings inside them remain content, and closes the section at
  the next unfenced level-1/2 ATX heading.
- All sorted output uses normalized relative-path byte ordering. The compiler
  never observes filesystem iteration order as semantic order.
- Error collection stops before mutation and renders diagnostics in the stable
  registry order.

### Failure, edge cases & resilience

- Any parse, limit, path, collision, lifecycle, authority, or review failure
  produces no managed writes.
- A staging mismatch is treated as compiler non-determinism, not as ordinary
  output drift.
- An ownership conflict for either a generated Skill directory or managed
  `index.md` preserves both the current path and manifest and names the exact
  normalized target requiring human resolution.
- Write application uses staged complete directories and atomic replacement
  where supported; rollback or partial-application behavior is covered by
  injected filesystem failures before implementation is accepted.

### Quality attributes (NFRs)

- Determinism: complete repeated output trees are byte-identical across the
  supported CI hosts.
- Security: no network, execution, symlink following, out-of-root read/write,
  raw control transfer, or secret-bearing absolute path appears in output or
  diagnostics.
- Maintainability: the two pilots traverse the same named stages and a
  maintainer completes and explains each update exercise within 30 minutes.
- Portability: generated Skills pass existing catalogue lint and all supported
  adapter preservation checks.

### Dependencies & integration

- PyYAML is loaded only by the authoring compiler and is documented as its
  prerequisite. The implementation uses safe composition plus explicit alias,
  tag, size, and depth checks rather than object construction.
- Existing pack TOML loading, Agent Skills lint, build adapters, and repository
  gate orchestration are reused after verifying their functions exist.
- The discovery spec consumes the committed manifest and generated Skill
  metadata; it does not call the compiler from `agentbundle show`.

## Tasks

### T1: Contract examples and all profile/extension schema fixtures agree

**Depends on:** none

**Touches:** `contracts/jsonschema/okf-*.schema.json`, `packs/catalogue-curation/tests/skills/compile-okf/fixtures/contracts/**`, `packs/catalogue-curation/tests/skills/compile-okf/test_contracts.py`

**Verification mode:** TDD.

**Tests:**

- Add positive examples for empty and projected bundles and negative cases for
  every closed property, scalar bound, path form, Skill name, include limit,
  and digest form in AC1–AC2.
- Validate the schemas themselves as JSON Schema 2020-12 and prove every
  example has the expected verdict.

**Approach:**

- Keep schemas self-contained and fixtures small; use the schemas as the test
  oracle before any compiler validator exists.

**Done when:** Contract tests pass and every contract boundary in AC1–AC2 has a
red-then-green fixture.

### T2: Bounded OKF 0.2 parsing rejects every invalid or unsafe source

**Depends on:** T1

**Touches:** `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py`, `packs/catalogue-curation/tests/skills/compile-okf/test_parser.py`, `packs/catalogue-curation/tests/skills/compile-okf/fixtures/parser/**`

**Verification mode:** TDD.

**Tests:**

- Stub and implement AC3–AC4 and AC7–AC10, including exact version, YAML,
  resource-bound, symlink, traversal, control-character, Windows device/reserved
  path, Unicode, case-collision, lifecycle, and diagnostic-order cases.
- Assert all invalid cases finish before a render/apply callback can run.

**Approach:**

- Introduce immutable normalized records and pure byte/frontmatter parsers.
- Inventory and bound raw files before parsing YAML; centralize diagnostic IDs
  and relative-path rendering.

**Done when:** The parser fixture suite passes on the minimum Python version and
reports only the AC7 registry.

### T3: Deterministic indexes, routers, reviewed Skills, and manifests match golden trees

**Depends on:** T2

**Touches:** `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py`, `packs/catalogue-curation/.apm/skills/compile-okf/assets/**`, `packs/catalogue-curation/tests/skills/compile-okf/test_render.py`, `packs/catalogue-curation/tests/skills/compile-okf/fixtures/render/**`

**Verification mode:** TDD.

**Tests:**

- Golden-tree tests cover AC11–AC19, including exact/moved/changed/missing index
  markers, empty branches, deprecated and stale concepts,
  exact/missing/duplicate/fenced instruction headings, canonical review-tuple
  encoding vectors and invalidation, includes, hostile prose, unknown
  extensions, Skill markers, and manifest bytes.
- Randomized input enumeration and equivalent Unicode/path orderings produce
  the same normalized output or a stable collision diagnostic.

**Approach:**

- Render every artifact into memory or staging from immutable records and
  checked-in template bytes. Keep canonical raw bytes separate from extracted
  fields.

**Done when:** All golden trees and digest vectors are byte-stable and every
generated Skill passes the existing deep Skill lint.

### T4: Write and check modes are deterministic, confined, and ownership-safe

**Depends on:** T3

**Touches:** `packs/catalogue-curation/.apm/skills/compile-okf/scripts/compile_okf.py`, `packs/catalogue-curation/.apm/skills/compile-okf/scripts/okf_compiler.py`, `packs/catalogue-curation/tests/skills/compile-okf/test_apply.py`, `packs/catalogue-curation/tests/skills/compile-okf/test_cli.py`

**Verification mode:** TDD plus goal-based integration checks.

**Tests:**

- Exercise AC5–AC6 and AC20–AC22 for clean write, clean check, source/output
  drift, double-compile mismatch, first index creation, managed-index
  replacement, stale removal, changed output/index, symlink swap, partial
  filesystem failure, and stdout/stderr stability.
- Snapshot the tree before and after every failing/check invocation and assert
  no unauthorized mutation.

**Approach:**

- Make the CLI thin; stage twice under an approved temporary root, preflight
  all operations, then apply a deterministic operation list.

**Done when:** Process-level tests prove exit codes, diagnostics, atomicity, and
check-mode non-mutation.

### T5: The catalogue-curation pack ships a usable compile-okf authoring Skill

**Depends on:** T4

**Touches:** `packs/catalogue-curation/.apm/skills/compile-okf/**`, `packs/catalogue-curation/pack.toml`, `packs/catalogue-curation/.claude-plugin/plugin.json`, `packs/catalogue-curation/evals/**`, `packs/catalogue-curation/tests/pack/**`, `docs/product/changelog.md`

**Verification mode:** Goal-based checks plus Tier-A/Tier-B-lite evals.

**Tests:**

- Verify AC24: activation near-misses, a confined sample compilation, declared
  prerequisite behavior, pack/plugin version parity, pack inventory, and no
  internal-governance citations in shipped content.
- Run pack lint, pack tests, eval schema checks, and self-host drift checks.

**Approach:**

- Write concise operator instructions that distinguish canonical source from
  generated output and invoke the fixed script interface.
- Apply the required minor pack bump only after all pack sources are ready, then
  regenerate adapter projections and marketplace metadata once.

**Done when:** The pack's focused tests/evals and catalogue lint pass, and all
generated adapter projections are synchronized.

### T6: The cost-engineering pilot has frozen source, baseline, and cases

**Depends on:** T5

**Touches:** `packs/_okf-pilot-cost-engineering/**`, `docs/rfc/0087-notes/pilot-cases/cost-engineering.json`, `docs/rfc/0087-notes/pilot-baselines/**`, `docs/rfc/0087-notes/pilot-licenses/**`

**Verification mode:** Goal-based provenance checks and recorded E2E baseline.

**Tests:**

- Validate attribution, licence compatibility, OKF 0.2 structure, at least 20
  frozen cases, at least five fixed security cases, and a same-configuration
  hand-authored baseline for AC25–AC27.
- Compile with pipeline-stage instrumentation and assert no caller-name branch.
- Stage the pack-shaped reserved asset without content changes beneath a
  temporary catalogue's `packs/cost-engineering/` path and validate its complete
  discovery response; assert the working catalogue does not list or publish the
  underscore-prefixed source.

**Approach:**

- Keep the complete pack-shaped prototype at the immediate reserved
  `packs/_okf-pilot-cost-engineering/` path until a separate pack proposal
  succeeds; record source revisions and transformations without importing
  vendor-specific examples. The compiler resolves this exact immediate child;
  normal catalogue discovery continues to ignore underscore-prefixed assets.

**Done when:** Canonical source, legal evidence, cases, baseline, and generated
output are reviewable and frozen before generated evaluation.

### T7: security-checklists projects through OKF without behavior loss

**Depends on:** T5

**Touches:** `packs/core/okf/**`, `packs/core/.apm/skills/security-checklists/**`, `packs/core/.okf-generated.json`, `packs/core/tests/skills/security-checklists/**`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md`, `docs/rfc/0087-notes/pilot-cases/security-checklists.json`, `docs/rfc/0087-notes/pilot-baselines/**`

**Verification mode:** TDD for construction plus recorded E2E baseline.

**Tests:**

- Freeze the current hand-authored router/reference behavior, then prove the
  generated variant preserves its eleven boundary modules and user-visible
  behavior while satisfying AC12–AC18 and AC25–AC27.
- Compile with the same stage instrumentation as T6 and assert no
  security-specific compiler branch.

**Approach:**

- Express the existing hierarchy and reference metadata as canonical OKF while
  preserving the current Skill activation contract and progressive-disclosure
  behavior.
- Apply the synchronized pack/plugin version bump and changelog entry required
  for the non-cosmetic generated Skill/source change, then self-host once after
  all core pack sources are final.

**Done when:** Existing and new tests pass, the generated tree is explainable,
and the baseline/case freeze predates generated runs.

### T8: Repository gates and adapter checks reject every managed-pilot drift

**Depends on:** T6, T7

**Touches:** `tools/catalogue/pre_pr_catalogue.py`, `tools/test_*.py`, `packages/agentbundle/tests/build_pipeline/**`, `Makefile`

**Verification mode:** Goal-based integration checks.

**Tests:**

- Exercise AC23 and AC29 through the actual repository gate and all supported
  adapter projections for clean, drifted, and unsafe managed inputs.
- Confirm packs without `[pack.metadata.okf]` retain byte-for-byte behavior and
  do not require PyYAML during normal AgentBundle install/build paths.

**Approach:**

- Add one deterministic repository-level discovery of managed pilot packs and
  invoke the shipped compiler's check mode; do not change public AgentBundle
  verification semantics during the experiment.

**Done when:** Focused integration tests and `SKIP_SAST=1 make build-check` pass
with clean pilots and fail predictably for injected drift.

### T9: Pilot evidence and experimental architecture are complete

**Depends on:** T8, spec:okf-catalogue-discovery/T4

**Touches:** `docs/rfc/0087-notes/pilot-results.md`, `docs/architecture/pack-layout.md`, `docs/architecture/agentbundle.md`, `docs/specs/okf-authoring-projection/spec.md`, `docs/specs/okf-authoring-projection/plan.md`

**Verification mode:** Recorded E2E evaluation and goal-based documentation checks.

**Tests:**

- Run AC26–AC28 exactly as pre-registered, capture commands/configuration/raw
  measurements/failures, and verify the result document accounts for every RFC
  promotion gate.
- Run documentation link/lint gates and confirm the architecture text labels
  all OKF surfaces Experimental.

**Approach:**

- Execute baselines before generated variants, preserve failed attempts, record
  both maintainer update exercises, and ask the RFC Approver to sign the results
  before changing lifecycle status.

**Done when:** The evidence is reproducible, all applicable ACs are checked, and
the RFC has enough information for its next lifecycle decision.

## Rollout

- **Delivery:** Land contracts, compiler, and tests before either pilot source.
  Keep all behavior experimental and repository-scoped. Generated Skills ship
  through existing adapters only after check mode is clean.
- **Infrastructure:** None. Compilation uses local files and approved temporary
  directories; no service, database, secret, network permission, or scheduler
  is introduced.
- **External-system integration:** External knowledge is acquired and reviewed
  before it becomes canonical source. Compilation never fetches it.
- **Deployment sequencing:** T1–T5 establish the generic path; T6 and T7 may
  proceed independently; T8 integrates both; discovery T4 and T8 precede final
  evidence. A failed pilot is retained as evidence and may lead to rejection,
  not patched with a caller branch.
- **Rollback:** Remove the experimental schemas, compiler Skill, managed OKF
  sources and projections, gate wiring, architecture text, and discovery fields
  under the RFC's rejection/withdrawal cleanup rule. The RFC and evidence stay.

## Risks

- The existing Skill frontmatter or pack lint parser may not safely expose the
  nested metadata needed by the compiler; verify before reuse and keep the
  compiler's untrusted YAML path separate if its guarantees differ.
- Cross-platform case and Unicode behavior can make a locally deterministic
  implementation diverge in CI; normalize in pure data structures and retain
  platform-specific fixtures.
- Committed generated output can collide with maintainer edits; the manifest
  preflight deliberately stops rather than attempting a merge.
- The security-checklists conversion can accidentally measure formatting parity
  instead of behavior parity; the frozen user-level routing cases are the
  deciding evidence.
- External cost guidance may have attribution or versioning constraints that
  make the prototype unsuitable; stop that pilot rather than weakening licence
  validation.
- A repository-only gate can be mistaken for a supported AgentBundle feature;
  docs and runtime help must keep the Experimental authoring-skill boundary
  explicit.

## Changelog

- 2026-08-15: Initial plan following RFC-0087 Open approval, the single OKF 0.2
  support decision, and confirmation of JSON Schema contract locations.
