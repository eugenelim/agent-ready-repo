# Spec: catalogue-verifier-correctness

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md) (portable verifier is D1/D2 infrastructure); [catalogue-wave2-pack-integrations](../catalogue-wave2-pack-integrations/spec.md) (step 19 defines integration-verification scope)
- **Gated on:** [catalogue-wave2-pack-integrations](../catalogue-wave2-pack-integrations/spec.md) (Shipped — step 19 establishes final pipeline scope)
- **Shape:** service (correctness fix; no new public interface; existing `agentbundle catalogue verify` surface is unchanged; engine change to verify.py and commands/install.py — installer grammar expanded to match verifier)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

**Mode:** full (compliance/security boundary: verifier is a trust signal for enterprise adoption; multi-feature: 13 confirmed defects across 11 steps; structural: host-only leak extracted to repository-local tooling).

## Objective

`packages/agentbundle/agentbundle/catalogue_tooling/verify.py` advertises a 19-step
portable catalogue verification pipeline but has 13 confirmed defects: step 1 originally
let malformed `catalogue.toml` escape as an unhandled exception instead of a structured
diagnostic (a partial guard now exists but lacks contract coverage and safe diagnostic
redaction), wrong plugin path in steps 4 and 5, wrong
marketplace source path in step 12 (`_step_marketplace` reads `dist/marketplace.json`
which never exists — source is `config.paths.marketplace`; the step silently returns `[]`
for every catalogue), five unimplemented steps (7, 8, 14, 17, 18) that return `[]`
silently, parse-only profile validation in step 6, incorrect step count in the module
docstring (says "18-step"; pipeline has 19 entries), and a host-specific identity check
embedded in portable code (step 11 checks for `agent-ready-repo` by name). Note: the
PyYAML availability guard already returns a structured `Diagnostic` warning at HEAD —
no defect; T10 adds regression coverage only.

These defects mean an enterprise adopter running `agentbundle catalogue verify` against
their catalogue receives a partial result presented as complete verification. Step stubs
return empty finding lists, silently passing checks that are not performed. Wave 4 adds a
standalone `catalogue index` command; the stubs in the existing 19-step pipeline must be
corrected before Wave 4 integrates so that Wave 4 inherits an honest verification foundation.

This spec owns the correctness residual for the already-advertised portable verifier.
It does not extend the verifier with new Wave 4 or Wave 5 behaviors — those waves amend
this spec at implementation time.

## Boundaries

### Always do

- Verify `SKIP_SAST=1 make build-check` exits 0 before committing.
- Run `python3 -m pytest packages/agentbundle/tests/ -q` and confirm all tests pass.
- For every unimplemented step corrected, add a corresponding test that exercises the
  real implementation (not a stub).
- Keep the existing `agentbundle catalogue verify` command surface unchanged — no new
  flags, no changed exit codes, no output format changes (fixing correctness only).
- Use `packs/<pack>/.claude-plugin/plugin.json` as the canonical plugin path in all
  verification steps (not `packs/<pack>/plugin.json`).

### Ask first

- Changing any exit code or output format for `agentbundle catalogue verify` — the surface
  is public and changing it would be a breaking change requiring RFC.
- Extending step scope beyond what was advertised in the step's original docstring —
  scope additions may require a new spec or RFC amendment.
- Adding new verification steps beyond the existing 19 — numbered steps are a public
  contract surface.

### Never do

- Implement neutral index generation (Wave 4 scope).
- Implement JOURNEY.md semantic indexing (Wave 4 scope).
- Implement release integrity or mutation-refusal logic (Wave 5 scope).
- Extend step 11 with new agentic-skill boundary-metadata validation or projection rules;
  that is a separate public contract, not a correction to this step's advertised behavior.
- Add third-party dependencies not already in `agentbundle` or its optional extras.
- Silently swallow exceptions in corrected steps — correct steps fail openly with a
  structured diagnostic.
- Leave any step returning `return []` without a real implementation or an explicit
  `NotImplemented` result with a diagnostic.

## Testing Strategy

- **Config validation (AC0):** TDD — malformed configuration returns a step-1
  diagnostic without raising; its message is bounded and redacted. Missing
  `catalogue.toml` reaches the remaining pipeline and produces no step-1 diagnostic.
- **Plugin path correction (AC1–AC2):** TDD — write fixtures with `pack_dir/.claude-plugin/plugin.json`
  and `pack_dir/plugin.json`; assert correct path is found and wrong path produces a
  finding; assert step 5 version-parity uses the same corrected path.
- **Profile validation (AC3):** TDD — write profile fixtures with a known schema violation,
  a missing pack, an invalid pack slug, and a symlink/junction escape; assert step 6 emits
  structured findings and never resolves a reference outside the configured packs root.
- **Dependency validation (AC4):** TDD — write fixture with missing and present dependency;
  assert step 7 returns findings for missing, empty for present; no `return []`; test
  `--pack` scoped mode confirms unrelated-pack defects produce no finding.
- **Marketplace source path (AC3a):** TDD — write fixture with malformed source `marketplace.json`
  at `config.paths.marketplace`; assert step 12 emits a finding (not silently passes).
- **Installer/linter grammar alignment (AC4a):** TDD — update `test_install_dependencies_gate.py:300`
  to split the `~0.1`-rejected assertion into `test_install_valid_tilde_range_passes`
  (positive) and `test_install_malformed_range_rejected` (negative, genuinely invalid
  string); exercise the same grammar through `catalogue lint`, including cross-catalogue
  profile closure. Run both suites as part of T3 Done-when.
- **Adapter compatibility (AC5):** TDD — write fixture with pack declaring an unsupported
  adapter in the `allowed-adapters` list key under `[pack.install]`; assert step 8 emits
  a finding; no `return []`.
- **Output drift (AC6):** TDD — write fixtures with stale output plus symlink/junction and
  loop escapes; assert step 14 emits root-relative findings without reading outside the
  configured output root or hanging; no `return []`.
- **Package preflight (AC7):** TDD — write fixture triggering package preflight failure;
  assert step 17 emits a finding; no `return []`.
- **Fixture checks (AC8):** TDD — write fixture with malformed deterministic fixture;
  assert step 18 emits a finding; no `return []`.
- **Host-only leak (AC9):** goal-based — grep confirms no `agent-ready-repo` string in
  `verify.py`; blocklist logic present only in repository-local tooling.
- **Step count (AC10):** goal-based — grep docstring for "19-step"; assert `len(_VERIFY_STEPS) == 19`.
- **PyYAML guard coverage (AC11):** regression TDD — simulate unavailable PyYAML;
  assert step 11 returns a non-empty `list[Diagnostic]` (already correct behavior at HEAD;
  test ensures this is not regressed). No `verify.py` code change required.
- **External-catalogue portability (AC12):** integration test — run `catalogue verify`
  against an external-catalogue fixture (no host-specific content); assert exit 0 with no
  host-specific findings.
- **Regression (AC13–AC15):** `SKIP_SAST=1 make build-check` exits 0; pytest exits 0;
  line count caps maintained.

## Acceptance Criteria

### Phase AA — Config validation (step 1)

- [x] AC0: When `catalogue.toml` is **present but contains malformed TOML**, `verify_catalogue()`
  returns a result containing at least one structured `Diagnostic` attributed to step 1,
  rather than letting the TOML parse exception escape. Implementation note: the pre-loop
  `load_catalogue_config(root)` call is wrapped in a try/except; on failure the function
  returns early with a step-1 diagnostic (without entering `_VERIFY_STEPS`) — `_step_config_validation`
  itself is therefore not reached in this path. AC0 requires that the caller receives a
  step-1 diagnostic, not that `_step_config_validation` generates it. The diagnostic uses
  a bounded reason category and the repository-relative path `catalogue.toml`; it never
  includes a stack trace, an absolute checkout path, URL userinfo/query text, secret-like
  configuration values, or the raw exception string. `load_catalogue_config()` returns
  `None` for a missing `catalogue.toml`, so absence must not produce CAT-V-001 and
  verification continues through the remaining steps. An empty directory may still fail
  later source-identity lint with CAT-V-002; this criterion does not override that shipped
  behavior. Unit tests cover malformed, redacted, and missing-config cases.

### Phase A — Plugin path correction

- [x] AC1: `_step_plugin_validation` (step 4) resolves the plugin manifest at
  `pack_dir / ".claude-plugin" / "plugin.json"`, not at `pack_dir / "plugin.json"`.
  A unit test confirms: a pack with only `.claude-plugin/plugin.json` passes step 4;
  a pack with only `plugin.json` (wrong path) produces a finding.

  **Manifest presence is not required; the pack root is not a manifest location.**
  A `plugin.json` at the pack root is a CAT-V-004 finding whether or not the
  canonical manifest is also present — a root copy is invisible to every consumer
  while looking present in the tree. A pack with no manifest anywhere is *not* a
  finding: verify runs against adopter catalogues, `catalogue lint` already treats
  the manifest as optional, and an unconditional error fails every manifest-less
  pack (including the packaging suite's own fixtures).
  `docs/architecture/pack-layout.md` still requires the manifest of *first-party*
  packs; that is a publication-route rule enforced by `build/main.py`, not a
  portable-verifier rule.

- [x] AC2: `_step_version_parity` (step 5) resolves the plugin manifest at the same
  corrected path as AC1. A unit test confirms version-parity check uses the `.claude-plugin/`
  path and correctly detects version mismatches.

> **Phase A landed ahead of the rest of this spec** — see [plan T1](plan.md) for
> the task record, coverage, observed verification output, and the release
> reasoning. AC3 onward are untouched.

### Phase B — Profile validation

- [x] AC3: `_step_profiles` (step 6) validates each profile file in two passes:
  (a) **Schema validation** — validates against `profile.schema.json` using
  `agentbundle.build.validate.validate`. A profile with a deliberate schema violation
  (e.g., missing required `scope` field — `profile.schema.json` requires `scope`,
  `description`, and `packs`; there is no `name` field) produces a non-empty finding list.
  (b) **Pack-reference validation** — `profile.schema.json` defines `packs` as an array of
  objects `{"pack": "<slug>"}` (not strings). For each entry, extract `entry["pack"]` and
  check that `<packs_dir>/<slug>/` exists, where `packs_dir = root / config.paths.packs if
  config is not None else root / "packs"` (matching `lint.py:1801`). A schema-valid profile
  that references a pack not present in the configured packs directory produces a finding.
  Before joining a pack reference to `packs_dir`, validate it against the canonical pack-name
  grammar and resolve the candidate under `packs_dir.resolve()`. Invalid names, absolute or
  traversing names, and candidates that escape through a symlink or Windows junction produce
  a structured finding without reading outside the configured root. A unit test covers each
  pass independently (schema failure, pack-ref missing, invalid slug, resolved escape).

### Phase B.5 — Marketplace source path

- [x] AC3a: `_step_marketplace` (step 12) is corrected to read the marketplace file from
  `config.paths.marketplace` (the source path — `config.paths.marketplace` defaults to
  `.claude-plugin/marketplace.json` in the catalogue root; use `root / config.paths.marketplace`
  when config is present, or `root / ".claude-plugin" / "marketplace.json"` when absent).
  The current implementation reads `dist/marketplace.json`, which is never present at
  verification time for a catalogue that has not been built — this causes the step to
  silently return `[]` for every catalogue. A unit test confirms: a catalogue with a
  malformed `config.paths.marketplace` file (invalid JSON) causes step 12 to return a
  non-empty finding list. An absent marketplace file continues to return `[]` (not an error
  — marketplace.json is created by `catalogue self-host`, not required to exist before build).

### Phase C — Dependency validation

- [x] AC4: `_step_dependencies` (step 7) is implemented. It validates dependency
  references as declared in `pack.schema.json`: dependencies are objects with required
  `catalogue`, `pack`, and `version` fields, listed under `[pack.dependencies.required]`,
  `[pack.dependencies.recommended]`, and `[pack.dependencies.conflicts]`. For each
  dependency object: first, validate range syntax for the `version` field regardless of
  `catalogue` — a malformed range string is one the full RFC-0001 range grammar does not
  accept. RFC-0001 explicitly permits caret (`^X.Y`), tilde (`~X.Y`), comparator (`>=X.Y`),
  compound (`>=A <B`), and prerelease forms — these are valid, not malformed. Only strings
  that match none of these accepted forms produce a finding. A caret-only parser is
  insufficient. A malformed range skips the remaining checks for that entry. Then branch
  by dependency kind (RFC-0001 semantics):
  - **`required`** (same-catalogue, range valid): if the referenced pack is absent from
    `packs/` → finding; if present but version out of range → finding.
  - **`recommended`** (same-catalogue, range valid): absence and version mismatch are
    informational — produce no finding.
  - **`conflicts`** (same-catalogue, range valid): validate the dependency reference
    structure only (fields and range syntax already checked earlier). Do NOT test for pack
    presence in `packs/` — RFC-0001 §337-342 defines this constraint against a pack
    already *installed*, not one present in the catalogue source tree. A catalogue may
    distribute two mutually exclusive packs for installers to choose between; treating
    source-tree presence as "installed" would fail every legitimate same-catalogue
    `conflicts` declaration. Installed-state enforcement is the installer's responsibility.
  - **cross-catalogue** (any kind, range valid): skip local lookup; produce no finding.
  Additionally, detect dependency graph cycles (RFC-0001 §312-317): after validating
  all individual entries, build the `required` dependency graph and check for cycles
  (e.g., pack A requires B and B requires A). A cycle produces a finding naming the
  cycle members. No current lint or build step performs this graph check.
  A pack with no dependencies produces an empty finding list. The step no longer
  returns `[]`. When `catalogue verify --pack A` is invoked, check only pack A's
  dependencies (including its cycle graph); do not scan unrelated packs — an unrelated
  invalid pack must not produce a finding in `--pack A` mode. A unit test confirms this:
  a catalogue with two packs where pack B has an invalid `required` reference; running
  with `--pack A` produces no finding. Before any local dependency lookup, validate the
  referenced pack against the canonical pack-name grammar and confine the resolved candidate
  beneath `packs_dir.resolve()`; invalid, traversing, or symlink/junction-escaping references
  produce a finding without reading the escaped path.

### Phase C.5 — Installer grammar alignment

- [x] AC4a: `commands/install.py::validate_dependencies_required` and catalogue profile lint
  are updated to accept the
  same full RFC-0001 range grammar as the expanded verifier step 7 — `^X.Y`, `~X.Y`,
  `>=X.Y`, compound (`>=A <B`), and prerelease forms. This is required for verify/install
  consistency: if the verifier accepts a range that the installer rejects, a pack passes
  `catalogue verify` then fails `catalogue install`, making verification dishonest. The
  existing test `test_install_unsupported_range_grammar_rejected` (at
  `tests/integration/test_install_dependencies_gate.py:300`) asserts `~0.1` is rejected —
  this test must be updated: split into `test_install_valid_tilde_range_passes` (positive,
  `~0.1` succeeds) and `test_install_malformed_range_rejected` (negative, a genuinely
  invalid string such as `"not-a-version"` fails). The version grammar is a public contract
  invariant; `catalogue verify`, `catalogue lint`, and `catalogue install` must agree on what
  is valid. Profile lint carries the dependency's catalogue identity through closure checks
  and skips external-catalogue dependencies rather than reporting them as missing locally.
  CLI-level tests cover every accepted grammar form, malformed syntax, boundary-negative
  versions, and cross-catalogue profile closure.

### Phase D — Adapter compatibility

- [x] AC5: `_step_adapter_compat` (step 8) is implemented. For each pack in the catalogue:
  gate the check through the same contract-version-aware logic as
  `_profile_pack_allowed_adapters` — if the pack's `[pack.adapter-contract].version` is
  absent or `"0.1"` (legacy pack), skip the `allowed-adapters` check entirely (the
  installer ignores `[pack.install]` for legacy packs; checking it here would reject valid
  legacy packs that happen to have a stray `allowed-adapters` value). For non-legacy packs:
  validate that each adapter named in `allowed-adapters` is a recognized adapter target.
  **TOML nesting:** `[pack.install]` lives under the top-level `pack` key; access as
  `pack_data.get("pack", {}).get("install", {}).get("allowed-adapters", [])`.
  Do NOT use `pack_data.get("install", {})` or `pack_data["install"]` — those look up
  a non-existent root-level `install` key and silently return empty, letting unknown
  adapters pass unchecked. A recognized adapter target is one present in
  `contracts/adapter.toml [adapter]` keys. An unknown adapter produces a
  finding. The step no longer returns `[]`. When `catalogue verify --pack A` is invoked,
  check only pack A's adapter compatibility; do not check unrelated packs.

### Phase E — Output drift

- [x] AC6: `_step_output_drift` (step 14) is implemented. It compares the configured
  build-output directory (`dist/` by default, or the path from `config.paths.build_output`
  in `catalogue.toml`'s `[catalogue.paths]` table) against a deterministic re-derivation
  from current pack source. If no build-output directory exists, the step returns an empty
  finding list (catalogue has never been packaged — not an error). If the build-output
  directory exists and any file in the projection trees (`dist/claude-plugins/`,
  `dist/apm/`) is stale relative to the freshly generated equivalent, a finding is
  emitted for each differing path. The step no longer returns `[]`. Note: per-pack
  adapter directories are not per-pack subdirectories in this catalogue layout;
  catalogue-level self-host projection drift is covered by step 15. The comparison walks
  only regular files confined beneath the canonical configured-output and fresh-output
  roots. It records each resolved directory before processing children, refuses symlink and
  Windows-junction/reparse escapes, catches both `OSError` and `RuntimeError` from resolution,
  terminates on loops, and reports only repository-relative paths. Tests cover each escape
  and loop behavior without reading an out-of-root sentinel.

### Phase F — Package preflight

- [x] AC7: `_step_package_preflight` (step 17) is implemented. It confirms
  `pack.toml` is present and parses; confirms `pack.toml` validates against
  `pack.schema.json`. Missing or malformed `pack.toml` produces a finding. `README.md`
  absence does NOT produce a finding — `README.md` is not a required file per the pack
  contract (the builder treats its absence as a no-op; rejecting it here would introduce
  a new contract rule under a correctness-only spec). Step 17 does not add catalogue-root
  required-path checks, license/marketplace checks, packaging traversal, or new custom-path
  refusal behavior; those are packaging-contract changes outside this correctness fix. The
  step no longer returns `[]`.

### Phase G — Fixture checks

- [x] AC8: `_step_fixture_checks` (step 18) is implemented. It validates the two named eval
  manifest files present under each skill's `.apm/skills/<skill>/evals/` directory:
  `evals.json` and `eval_queries.json`. Only these two files are parsed — `.jsonl` files
  and files under `evals/files/` are not scanned (those are opaque payload inputs that may
  be intentionally non-JSON). Validation includes: (a) the manifest file parses correctly
  (valid JSON) and has non-empty content — a malformed or empty manifest produces a finding;
  and (b) structural validity — entries must pass the shape checks already enforced by
  `skill_spec_lint._check_eval_queries` (for `eval_queries.json`) and
  `skill_spec_lint._check_evals_json` (for `evals.json`), i.e., required fields present,
  `should_trigger` is boolean. Payload files referenced by manifest entries are checked
  for existence only, not parsed. Reuse those existing validators. Note: verifier step 2
  calls lint without `deep=True` so shallow lint alone does not cover these structural
  checks. The step no longer returns `[]`. When `catalogue verify --pack A` is invoked,
  check only pack A's eval fixtures; do not scan unrelated packs.

### Phase H — Host-only leak

- [x] AC9: `_APM_SKILL_BLOCKLIST` in `verify.py` and all four host-specific patterns in
  `_SEEDS_BLOCKLIST_PATTERNS` in `lint.py` are removed from their respective portable
  modules. The four patterns to remove from `lint.py` are:
  `(r"agent-ready-repo", ...)`, `(r"RFC-00\d\d", ...)`, `(r"K-00\d\d", ...)`, and
  the internal spec-name pattern. These host-specific checks are moved to
  repository-local tooling (`tools/catalogue/verify_host_checks.py`) that is wired into
  `make build-check` via `tools/repo/build_gate_chain.py` but is not distributed with
  agentbundle. A grep confirms no `agent-ready-repo` literal string remains in either
  `verify.py` or `lint.py`. The repository-local tool is invoked by the gate chain and
  its absence from the chain produces a CI failure (not a silent pass).

### Phase I — Step count and help accuracy

- [x] AC10: The module-level docstring of `verify.py` is updated to accurately reflect
  the pipeline: "19-step" (not "18-step"). `len(_VERIFY_STEPS)` equals 19 (confirmed
  by a unit assertion or a `grep`-based goal-based check).

### Phase J — PyYAML guard regression coverage

- [x] AC11: Step 11's PyYAML guard returns a structured `Diagnostic` warning via
  `_warn()` when `import yaml` fails. This behavior is already correct at HEAD and is
  NOT a defect fix — AC11 exists to establish regression coverage. A unit test confirms:
  with PyYAML absent (monkeypatched `ImportError`), step 11 returns a non-empty
  `list[Diagnostic]` (not an empty list or `logging.warning()`); with PyYAML present,
  step 11 proceeds normally. No `verify.py` code change is required for this AC.

### Phase K — External-catalogue portability

- [x] AC12: An integration test runs `agentbundle catalogue verify` against a minimal
  external-catalogue fixture. Its portable seed intentionally mentions
  `agent-ready-repo` to prove host vocabulary is allowed in ordinary external content;
  the fixture contains no host-specific skills or repository policy configuration.
  The test asserts: exit code is 0 (no blocker findings); no finding's `message` field
  references `agent-ready-repo` or any host-specific identifier. The step count is
  verified separately by a unit assertion: `len(_VERIFY_STEPS) == 19` (programmatic —
  per-step output is not exposed by `VerifyResult` and asserting it from command output
  would require a format change that is out of scope).

### Regression

- [x] AC13: `SKIP_SAST=1 make build-check` exits 0.
- [ ] AC14 (deferred: pre-existing-enterprise-agentbundle-full-suite):
  `python3 -m pytest packages/agentbundle/tests/ -q` exits 0. The managed session blocks
  pip/venv trust-store fixture setup and protected key-material filename globs before the
  affected tests reach product behavior; the remaining suite passed.
- [x] AC15: `wc -l AGENTS.md` ≤ 250; `wc -l packs/AGENTS.md` ≤ 150.

## Assumptions

**Technical**

1. `verify.py` `_VERIFY_STEPS` list has exactly 19 entries at HEAD (confirmed: step 19
   for Wave 2 integrations was added; docstring saying "18-step" is incorrect).
2. `.claude-plugin/plugin.json` is the canonical plugin manifest path (confirmed by
   reviewing pack directory structure and install.py).
3. `profile.schema.json` exists in `_data/` and is loadable via `importlib.resources`
   (confirmed: Wave 1 shipped schema sync).
4. Step 11 already returns a structured `Diagnostic` warning via `_warn()` when PyYAML
   is missing at HEAD — this is correct behavior. T10 adds regression coverage only;
   no code change is required for this assumption.
5. Host-only blocklist check in step 11 currently uses `agent-ready-repo` as a string
   literal; this is not portable to external catalogues.
6. Output drift (step 14) detection scope is the build-output projection trees emitted
   by `catalogue build`: `dist/claude-plugins/<pack>/` and `dist/apm/<pack>/`. Not
   the self-host projections (`.claude/`, `.codex/`, `.agents/` in the repo root — those
   are `catalogue self-host` scope covered by step 15) and not `catalogue-index.json`
   (Wave 4 scope). The configured output path is `config.paths.build_output` from
   `catalogue.toml [catalogue.paths]`; the default is `dist/`.

**Deferred**

7. Step 19 (Wave 2 integrations verification) is already implemented via Wave 2's scope;
   this spec does not change it — only ensures it is tested as part of the portability
   integration test.
8. JOURNEY.md validation is deferred to Wave 4 spec — Wave 4 defines the JOURNEY.md
   convention and validator; this spec does not implement JOURNEY validation. No new
   verifier step number is assigned here: step 13 is already occupied by plugin manifest
   schema validation, and new step numbers require RFC authorization per the "Ask first"
   boundary above.
9. Step 20+ (index validation, mutation refusal, release integrity) are Wave 4/5 scope.
