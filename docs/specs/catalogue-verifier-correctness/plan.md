# Plan: catalogue-verifier-correctness

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Mode and declined patterns

Mode: full (compliance boundary: verifier is a trust signal; multi-feature: 13 confirmed
defects across 11 of 19 pipeline steps; structural: host-only leak extraction; T10 is
regression coverage, not a defect fix — PyYAML guard already correct at HEAD).

Declined:
- Tempted to extend the verifier with new Wave 4 JOURNEY.md validation in the same PR;
  declining — Wave 4 defines the JOURNEY validator; this spec owns only the correctness
  of already-advertised steps. Wave 4 amends this spec when it integrates.
- Tempted to renumber steps when removing the host-only check from step 11; declining —
  step numbers are a public surface; remove the check, keep the step number and a pass.
- Tempted to implement output drift (step 14) by running `make build-self` to regenerate
  projections; declining — verification must be read-only; comparison must use a
  deterministic projection derived from source, not a subprocess.
- Tempted to add new verification steps beyond 19; declining — step additions require
  RFC or a separate spec.
- Tempted to add step-11 validation and projection rules for agentic
  `metadata.boundaries`; declining — this plan does not change that metadata contract,
  and adding public verifier behavior would violate the spec's correctness-only boundary.
- Tempted to emit `return []` with a docstring comment for steps that cannot be
  implemented in this PR; declining — every step must either implement or return a
  single `NotImplemented`-typed finding with a description, never a silent empty list.

## Pre-EXECUTE self-coverage checks

- Domain claim: `verify.py` `_VERIFY_STEPS` has 19 entries at HEAD. Confirmed: step 19
  (`_step_wave2_integrations`) was added in Wave 2; module docstring says "18-step" —
  this is the defect in AC10.
- Domain claim: `.claude-plugin/plugin.json` is the canonical plugin path. Confirmed:
  install.py references `.claude-plugin/plugin.json`; verify.py steps 4 and 5 use
  `pack_dir / "plugin.json"` — this is the defect in AC1/AC2.
- Domain claim: `profile.schema.json` is loadable from `_data/`. Confirmed via Wave 1
  spec (shipped schema sync for profile.schema.json).
- Domain claim: `_APM_SKILL_BLOCKLIST` in verify.py contains `agent-ready-repo` by name.
  Confirmed by direct read of verify.py at HEAD.
- Resolve-vs-surface: pre-EXECUTE review found contract and construction-test gaps. They
  are resolved in this PLAN revision; implementation remains blocked until the revised
  spec and plan pass review and receive fresh human approval.

## Task list

```
T0   Config validation exception guard (step 1)   Depends on: none
T1   Plugin path correction (steps 4+5)           Depends on: none
T2   Profile schema validation (step 6)           Depends on: none
T2b  Marketplace source path (step 12)            Depends on: none
T3   Dependency validation (step 7)               Depends on: none
T4   Adapter compatibility (step 8)               Depends on: none
T5   Output drift (step 14)                       Depends on: none
T6   Package preflight (step 17)                  Depends on: none
T7   Fixture checks (step 18)                     Depends on: none
T8   Host-only leak extraction (step 11)          Depends on: none
T9   Step count + docstring fix                   Depends on: none
T10  PyYAML availability fix (step 11)            Depends on: none
T11  External-catalogue portability test          Depends on: T0–T10, T2b
T12  Version + changelog + closeout               Depends on: T0–T11, T2b
```

**Wave note:** T0–T10 and T2b all modify `verify.py` and are NOT parallelizable in supervisor
mode — parallel implementers would conflict on the same file. Execute all tasks sequentially.
T11 and T12 depend on all prior tasks and must be last.
Final sequence: T0, T2, T2b, T3–T10 (sequential), then T11, then T12.

---

## T0 — Config validation exception guard (step 1)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/tests/integration/test_catalogue_verify_step1.py` (new — uses tmp_path; filesystem test)

**Tests (write red first):**

stub: true — materialized in `test_catalogue_verify_step1.py`; collect passes and the
red assertion fails on raw diagnostic forwarding.

```python
class TestStepConfigValidation:
    def test_malformed_catalogue_toml_returns_structured_diagnostic(self, tmp_path):
        # write malformed TOML as catalogue.toml (e.g., unclosed bracket)
        # call verify_catalogue(tmp_path) or similar
        # assert result contains at least one Diagnostic, does NOT raise an exception
        # (malformed catalogue.toml must not escape as AttributeError or TOMLDecodeError)
        raise NotImplementedError  # STUB: AC0
    def test_malformed_catalogue_toml_redacts_sensitive_details(self, tmp_path):
        # malformed config includes a secret-like value and runs under an identifiable root
        # assert CAT-V-001 contains neither raw exception text, the value, nor absolute root
        raise NotImplementedError  # construction stub: config diagnostic redaction
    def test_absent_catalogue_toml_continues_without_step1_diagnostic(self, tmp_path):
        # empty tmp_path — no catalogue.toml
        # call verify_catalogue(tmp_path)
        # assert no CAT-V-001; later CAT-V-002 source-identity lint is allowed
        raise NotImplementedError  # construction stub: missing config continues
```

**Approach:**

`verify_catalogue()` calls `load_catalogue_config(root)` before entering `_VERIFY_STEPS`.
The current partial guard catches `CatalogueConfigError` and returns CAT-V-001, but it
forwards `str(exc)` directly. That message is not a stable or safe public diagnostic: it
can contain parser detail, absolute paths, or sensitive configuration text.
`_step_config_validation` remains a no-op. A missing `catalogue.toml` returns `None` from
`load_catalogue_config()`; do not convert that case into CAT-V-001. The remaining pipeline
still runs and may correctly return CAT-V-002 for a missing source-identity contract.

Fix: retain the pre-loop `load_catalogue_config(root)` try/except, but replace raw exception
forwarding with a bounded step-1 message such as `catalogue.toml is invalid`; use the
repository-relative diagnostic path `catalogue.toml`. Do NOT restructure
the step protocol by removing the pre-loop load — every subsequent step receives `config`
from that pre-loop call, and removing it would pass `None` to valid catalogues, silently
skipping config-dependent lint, schema, build, and drift checks. The guarded pre-load
is the only correct approach. Do NOT silently swallow the error — return a structured
finding per the "Boundaries / Never do" rule. Tests, rather than new control flow, are the
main residual for this partially implemented task.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_step1.py -q` exits 0.

---

## T1 — Plugin path correction (steps 4 and 5) — DONE

Landed ahead of this plan's own loop, via the `version-parity-probes-wrong-path`
backlog item, which turned out to duplicate this task. Both steps read
`pack_dir / ".claude-plugin" / "plugin.json"`.
`tests/integration/test_catalogue_verify_plugin_path.py` (the file *Done when*
below names) holds eight cases — the three stubbed below, plus:

- a root-level `plugin.json` beside a correct one is still a finding,
- a pack with no manifest anywhere is not a finding,
- a malformed manifest is a finding (parse error *and* misplacement),
- a name mismatch is a CAT-V-005 finding,
- a version mismatch is a CAT-V-005 finding.

Every asserting case plants a contradicting decoy at the legacy root path, so
reverting the probe reds the suite rather than passing on a lucky miss
(confirmed by reverting `_plugin_json_path` and re-running).

Verified on the real CLI: `python3 -m agentbundle catalogue verify --root .`
reports `ok=true` with no diagnostics on this repo; injecting a
`pack.toml`/`plugin.json` version mismatch into `packs/contracts/` flips it to
`ok=false` with `CAT-V-005 contracts pack.toml version '99.0.0' != plugin.json
version '0.3.5'`.

**Deviation from the Approach below**, recorded as an AC1 amendment in
[spec.md](spec.md): the missing-manifest branch stays a silent skip, and the
CAT-V-004 finding fires on a `plugin.json` at the *pack root* instead. An
unconditional missing-manifest error reds 20+ packaging tests whose fixture
catalogues ship no manifest, and `catalogue lint` already treats the manifest as
optional. That lint branch is currently unreachable for the same path reason
(see the `lint-plugin-json-probes-wrong-path` backlog entry) — so the parity
argument is a statement of intent for both gates, not an appeal to live
behaviour; whoever fixes lint should keep the two aligned.

**Release:** T1 shipped independently as a patch. T12 derives the next available
version from the package manifest and current workspace collision notes rather than
reserving a number in this plan. Its changelog entry covers T0 and T2–T11 only —
T1 already has its own published changelog sections.

Resume this plan at T0. The rest of the task is left below as the record.

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/tests/integration/test_catalogue_verify_plugin_path.py` (new; filesystem — uses tmp_path)

**Tests (write red first):**

```python
class TestStepPluginValidation:
    def test_finds_plugin_at_correct_path(self, tmp_path):
        # fixture: pack_dir/.claude-plugin/plugin.json with valid content
        # assert: step 4 returns no findings
        raise NotImplementedError  # STUB: AC1
    def test_missing_at_wrong_path_emits_finding(self, tmp_path):
        # fixture: pack_dir/plugin.json (wrong path); no .claude-plugin/plugin.json
        # assert: step 4 returns at least one finding
        raise NotImplementedError  # STUB: AC1
    def test_version_parity_uses_correct_path(self, tmp_path):
        # fixture: .claude-plugin/plugin.json with version matching pack.toml
        # assert: step 5 finds no parity violation
        raise NotImplementedError  # STUB: AC2
```

Note: all open TDD task stubs must be materialized as compilable red tests before
EXECUTE begins and recorded as `stub: true` in their task. Package tests use
behavior-named construction-stub comments rather than internal AC identifiers, per
`packages/AGENTS.local.md`.

**Approach:**

In `_step_plugin_validation` and `_step_version_parity`:

1. Replace the path:
```python
plugin_path = pack_dir / "plugin.json"
```
with:
```python
plugin_path = pack_dir / ".claude-plugin" / "plugin.json"
```

2. Change the missing-file branch from a silent `continue` to an explicit finding:
```python
if not plugin_json.exists():
    diags.append(_err("CAT-V-004", "plugin.json not found at .claude-plugin/plugin.json",
                      pack=pack_dir.name))
    continue
```
Without this second change, a pack that has only `plugin.json` (wrong path) would still be silently skipped, making the `test_missing_at_wrong_path_emits_finding` test impossible to satisfy.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_plugin_path.py -q` exits 0.

---

## T2 — Profile schema validation (step 6)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/tests/integration/test_catalogue_verify_profile_schema.py` (new)

**Tests (write red first):**

stub: true — materialized in `test_catalogue_verify_profile_schema.py`; collect passes
and schema/reference/confinement assertions are red.

```python
class TestStepProfiles:
    def test_valid_profile_passes(self, tmp_path):
        # fixture: valid profile.toml conforming to profile.schema.json; all referenced
        # packs exist in root/packs/
        # assert: step 6 returns no findings
        raise NotImplementedError  # STUB: AC3
    def test_schema_violation_emits_finding(self, tmp_path):
        # fixture: profile.toml missing required field (e.g. scope — profile.schema.json
        # requires scope, description, and packs; name is NOT a required schema field)
        # assert: step 6 returns at least one finding
        raise NotImplementedError  # STUB: AC3
    def test_missing_pack_reference_emits_finding(self, tmp_path):
        # fixture: schema-valid profile.toml referencing pack "nonexistent-pack"; no
        # directory root/packs/nonexistent-pack/ present
        # assert: step 6 emits a finding (pack reference not satisfied)
        # rationale: schema validation passes for well-formed pack name; existence check
        # catches the missing pack — applies whether config is None or not (use root/packs/)
        raise NotImplementedError  # STUB: AC3
    def test_config_none_pack_ref_check_still_runs(self, tmp_path):
        # fixture: no catalogue.toml (config is None); schema-valid profile referencing
        # a missing pack
        # assert: step 6 still emits a pack-ref finding (config-None does not skip this check)
        raise NotImplementedError  # STUB: AC3
    def test_invalid_or_traversing_pack_reference_emits_finding(self, tmp_path):
        # schema-valid profile shape whose pack value violates canonical slug grammar
        # assert: finding is emitted before any path outside packs_dir is read
        raise NotImplementedError  # construction stub: invalid pack reference
    def test_symlink_or_junction_escape_emits_finding(self, tmp_path):
        # packs/<slug> resolves outside the configured packs root
        # assert: finding is root-relative and the escaped sentinel is never read
        raise NotImplementedError  # construction stub: confined pack reference
```

**Approach:**

Extend `_step_profiles` in two passes per profile file:
1. **Schema validation**: load `profile.schema.json` from `_data/` via `importlib.resources`
   and validate each parsed profile dict using `agentbundle.build.validate.validate` (the
   existing stdlib helper — no new dependency). Convert a validation failure to a finding.
   Keep the existing parse check as the first gate (malformed TOML/JSON still produces a
   finding before schema validation). Do NOT import `jsonschema` directly — `agentbundle`
   has no `jsonschema` dependency in its base or optional extras.
2. **Pack-reference validation**: `profile.schema.json` defines `packs` as an array of
   objects shaped `{"pack": "<slug>"}` (confirmed: `additionalProperties: false`, required:
   `["pack"]`). For each entry in the profile's `packs` array, extract `entry["pack"]` as
   the pack slug — do NOT treat the entry itself as the slug, as that raises `TypeError`
   in `root / <dict>`. Check that `packs_dir / entry["pack"]` exists as a directory, where
   `packs_dir = root / config.paths.packs if config is not None else root / "packs"` —
   this matches `lint.py:1801` which also reads `config.paths.packs` when config exists.
   Note: `contracts/catalogue.schema.json:74-76` defines `[catalogue.paths].packs` as the
   relative packs-dir path and lint.py honors it; use the same derivation here so a
   catalogue with a custom packs path does not produce false "missing pack" findings.
   Validate the referenced name against the canonical pack-name grammar before joining it
   to `packs_dir`. Resolve both the root and candidate and require the candidate to remain
   beneath the canonical root; reject absolute/traversing values and symlink or Windows
   junction escapes without reading the escaped target. Detect junctions through
   `Path.is_junction()` when available (with a false-returning compatibility fallback), so
   the detector is construction-testable on non-Windows hosts. Use the repository's existing
   pack-name/path-confinement helpers when available rather than adding a local variant.
   A missing or escaped pack directory → finding. This check applies whether `config is
   None` or not.
   Also update test fixtures and comments to use the object form: `{"pack": "nonexistent-pack"}`
   not a bare string in the profile's packs array.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_profile_schema.py -q` exits 0.

---

## T2b — Marketplace source path (step 12)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/tests/integration/test_catalogue_verify_marketplace.py` (new)

**Tests (write red first):**

stub: true — materialized in `test_catalogue_verify_marketplace.py`; collect passes and
the source-path assertion is red.

```python
class TestStepMarketplace:
    def test_absent_marketplace_passes(self, tmp_path):
        # no .claude-plugin/marketplace.json — step 12 returns [] (not an error)
        raise NotImplementedError  # STUB: AC3a
    def test_malformed_marketplace_emits_finding(self, tmp_path):
        # .claude-plugin/marketplace.json contains invalid JSON
        # assert step 12 returns at least one finding (CAT-V-012)
        # this currently FAILS — step reads dist/marketplace.json which doesn't exist → []
        raise NotImplementedError  # STUB: AC3a
    def test_valid_marketplace_passes(self, tmp_path):
        # .claude-plugin/marketplace.json contains valid JSON
        # assert step 12 returns []
        raise NotImplementedError  # STUB: AC3a
```

**Approach:**

`_step_marketplace` currently reads `build_output_dir / "marketplace.json"` — that path
(`dist/marketplace.json`) never exists; the step silently returns `[]` for every catalogue.
The source marketplace file is at `config.paths.marketplace` (from catalogue config) or
`root / ".claude-plugin" / "marketplace.json"` when config is absent.

Fix: replace the `build_output_dir / "marketplace.json"` lookup with:
```python
if config is not None:
    marketplace = root / getattr(getattr(config, "paths", None), "marketplace",
                                 ".claude-plugin/marketplace.json")
else:
    marketplace = root / ".claude-plugin" / "marketplace.json"
```
If absent: return `[]` (marketplace.json is created by `catalogue self-host`, not required
before build — absence is not an error). If present but malformed: return a CAT-V-012
finding. Do NOT change the step number, the step's role in `_VERIFY_STEPS`, or the
diagnostic code.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_marketplace.py -q` exits 0.

---

## T3 — Dependency validation (step 7)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/agentbundle/catalogue_tooling/lint.py` (update `_profile_lint_one` to use shared RFC parser)
- `packages/agentbundle/agentbundle/commands/install.py` (update `validate_dependencies_required` to use shared RFC parser)
- `packages/agentbundle/tests/integration/test_catalogue_verify_dependencies.py` (new)

**Tests (write red first):**

stub: true — materialized in `test_catalogue_verify_dependencies.py`,
`test_install_dependencies_gate.py`, and `test_catalogue_tooling_lint.py`; collect passes.
The red construction suite covers every deterministic AC4 branch, the complete accepted
range grammar and exclusion boundaries across verify/install/lint, external-catalogue
profile closure, and traversal/symlink confinement before EXECUTE.

```python
class TestStepDependencies:
    def test_no_dependencies_passes(self, tmp_path):
        raise NotImplementedError  # STUB: AC4
    def test_valid_dependency_reference_passes(self, tmp_path):
        raise NotImplementedError  # STUB: AC4
    def test_missing_dependency_emits_finding(self, tmp_path):
        raise NotImplementedError  # STUB: AC4
    def test_version_out_of_range_emits_finding(self, tmp_path):
        # required local dep with version satisfying range → no finding
        # required local dep with version outside range → finding
        raise NotImplementedError  # STUB: AC4
    def test_recommended_dep_absent_does_not_emit_finding(self, tmp_path):
        # recommended local dep whose pack directory does not exist → no finding
        # (recommended = informational; absence is not a failure per RFC-0001)
        raise NotImplementedError  # STUB: AC4
    def test_conflicts_dep_source_present_no_finding(self, tmp_path):
        # conflicts local dep whose pack directory EXISTS in packs/ → no finding
        # (verifier validates reference shape and range only; installed-state enforcement
        # is the installer's job — RFC-0001 §337-342 scopes conflicts to installed packs,
        # not source-tree presence; a catalogue may distribute mutually exclusive packs)
        raise NotImplementedError  # STUB: AC4
    def test_conflicts_dep_valid_reference_no_finding(self, tmp_path):
        # conflicts entry with valid fields and valid range syntax → no finding
        # regardless of whether the pack directory exists
        # (AC4: conflicts validates reference structure only, no presence check)
        raise NotImplementedError  # STUB: AC4
    def test_tilde_range_passes_grammar_check(self, tmp_path):
        # required dep with version "~0.1.0" → valid per RFC-0001 grammar → no syntax finding
        # (validates that the full RFC-0001 grammar is used, not caret-only)
        raise NotImplementedError  # STUB: AC4
    def test_comparator_range_passes_grammar_check(self, tmp_path):
        # required dep with version ">=0.1.0" → valid per RFC-0001 grammar → no syntax finding
        raise NotImplementedError  # STUB: AC4
    def test_cross_catalogue_dep_valid_range_passes(self, tmp_path):
        # dependency.catalogue != current catalogue name, range syntax valid → no finding
        raise NotImplementedError  # STUB: AC4
    def test_cross_catalogue_dep_malformed_range_emits_finding(self, tmp_path):
        # dependency.catalogue != current catalogue name, but version is malformed string
        # (e.g., "not-a-semver") → range syntax validated before skipping lookup → finding
        raise NotImplementedError  # STUB: AC4
    def test_circular_dependency_emits_finding(self, tmp_path):
        # catalogue with two packs: A requires B, B requires A
        # assert step 7 emits a finding naming the cycle (RFC-0001 §312-317 requires rejection)
        # (no existing lint or build step checks this; step 7 is the only gate)
        raise NotImplementedError  # STUB: AC4
    def test_pack_flag_scopes_dependency_check(self, tmp_path):
        # catalogue with two packs (A valid, B with invalid required reference)
        # run verify --pack A → assert NO finding (B's defect must not surface in A-only mode)
        # (AC4 scoping: check only the selected pack's dependencies)
        raise NotImplementedError  # STUB: AC4
    def test_invalid_or_traversing_dependency_pack_emits_finding(self, tmp_path):
        # local dependency pack violates canonical slug grammar
        # assert: finding is emitted before local path lookup
        raise NotImplementedError  # construction stub: invalid dependency pack
    def test_dependency_symlink_or_junction_escape_emits_finding(self, tmp_path):
        # packs/<dependency> resolves outside packs_dir
        # assert: finding is root-relative and escaped pack.toml is never read
        raise NotImplementedError  # construction stub: confined dependency lookup
    def test_config_none_skips_local_check_emits_diagnostic(self, tmp_path):
        # catalogue with NO catalogue.toml (config is None)
        # pack A declares required dep: catalogue = "my-catalogue", pack = "B"; pack B is absent
        # assert: step 7 does NOT emit a "missing required dep" finding (cannot classify local vs
        # cross without catalogue identity); DOES emit an informational diagnostic about skipped
        # local dep validation for pack A
        # rationale: root.name is the checkout dir and changes on rename — not a portable identity.
        # package_catalogue() also leaves catalogue_name = None (package.py:548-556). Skip rather
        # than guess; inform rather than silently pass.
        raise NotImplementedError  # STUB: AC4
```

**Approach:**

Implement `_step_dependencies` per the dependency schema in `contracts/pack.schema.json`:
dependencies are objects with `catalogue`, `pack`, `version` under
`[pack.dependencies.required]`, `[pack.dependencies.recommended]`, and
`[pack.dependencies.conflicts]`. Algorithm:
1. Load `pack.toml`; read `pack.dependencies` if present.
2. Get current catalogue name from `catalogue.toml [catalogue].name`. If `catalogue.toml`
   is absent (config is None), `current_catalogue_name` is None. Do NOT use `root.name` as a
   fallback — `root.name` is the checkout directory name, which changes on rename or different
   mount path and is not a portable catalogue identifier. Confirmed: `package_catalogue()` also
   leaves `catalogue_name = None` in this case (`package.py:548-556`); introducing a root-name
   guess would diverge from that behaviour and classify external deps as local if the catalogue
   name happens to match the folder name.
   When config is None AND any packs have `[pack.dependencies]` entries: emit one informational
   diagnostic (not a blocking finding) per affected pack — "catalogue identity unknown (no
   catalogue.toml); local dependency classification skipped for pack X". Skip local-lookup checks
   for all deps in that pack. Cross-catalogue deps are unaffected: they are already expected to
   skip the local lookup.
3. For each dependency object in `required` + `recommended` + `conflicts`:
   a. **Validate range grammar first** (regardless of `catalogue` field): attempt to parse
      `dependency.version` using a **shared RFC-0001 range grammar helper** that accepts
      the full grammar defined in RFC-0001 §344-349 — `^X.Y`, `~X.Y`, `>=X.Y`, compound
      (`>=A <B`), and prerelease ranges. Do NOT reuse the caret-only install/profile
      validator (`^X.Y` only) — it rejects valid RFC-0001 ranges and would produce false
      findings for external packs using tilde or comparator syntax. Introduce a shared
      `parse_version_range(expr) -> bool` helper (or reuse an existing RFC-0001-complete
      parser if one exists) rather than extending the caret-only parser. A range string
      the RFC-0001 grammar does not accept emits a finding (syntax error) and skips the
      remaining checks for this dependency.
   b. If `dependency.catalogue == current_catalogue_name` (and range syntax is valid),
      validate `dependency.pack` against the canonical pack-name grammar, resolve the
      candidate beneath `packs_dir.resolve()`, and refuse absolute/traversing values plus
      symlink or Windows-junction escapes before reading `pack.toml`. Then branch by
      dependency kind per RFC-0001 semantics (§ dependency semantics):
      - **`required`**: fail-if-unsatisfied. Verify `packs/<dependency.pack>/` exists;
        if not, emit a finding (missing required dependency). If present, read the pack's
        `pack.toml` version field and check it satisfies the declared range; version out
        of range emits a finding (version incompatibility).
      - **`recommended`**: informational. Do NOT emit a finding if the pack is absent or
        the version is out of range — missing recommended is not a failure.
      - **`conflicts`**: validate reference structure only. Range syntax was already
        checked at step 3a. Do NOT test for pack presence in `packs/` — RFC-0001 §337-342
        scopes this constraint to a pack already installed, not one present in the
        catalogue source tree. A catalogue may distribute mutually exclusive packs for
        installers to choose between; source-tree presence is not the violation. Produce
        no finding for `conflicts` entries with valid reference structure.
   c. If `dependency.catalogue != current_catalogue_name` (and range syntax is valid):
      cross-catalogue dependency — skip local lookup; produce no finding.
4. A pack with no `[pack.dependencies]` section → empty finding list (for that pack).
5. **Cycle detection (required-dependency graph):** After per-entry checks (steps 1-4),
   build a directed graph of within-catalogue required dependencies across ALL packs in scope:
   - When `--pack A` is specified: build the subgraph of packs reachable from A via required
     deps within the current catalogue only; run DFS on that subgraph.
   - When no `--pack`: build the full required-dependency graph across all packs; run DFS.
   If DFS discovers a back-edge (cycle), emit a finding for each pack in the cycle naming
   the cycle path (e.g. "A → B → A: circular required dependency (RFC-0001 §312-317)").
   Use a simple iterative DFS with `visiting` and `visited` sets to avoid recursion depth
   issues on large graphs. A pack not present in the catalogue (already caught in step 3b)
   is treated as a terminal node (no outgoing required edges) for cycle detection.
Replace `return []` with real implementation. Do NOT use bare pack names or
`catalogue:<name>:<pack>` string tokens — the schema uses an object representation.

**Profile linter alignment (same task):** Two changes to `_profile_lint_one` (in `lint.py`)
are required, since step 2 runs before step 7:

1. **Grammar fix:** Replace the caret-only range check with the shared `parse_version_range`
   helper. If `_profile_lint_one` still rejects valid tilde/comparator ranges with "only
   ^X.Y is supported," the verifier pipeline fails before reaching step 7.

2. **Cross-catalogue closure fix:** `_profile_required_deps` currently discards the
   `catalogue` field from each dependency object and reports the dep as missing from the
   profile's packs list. For a pack with a required dep whose `catalogue` differs from
   the current catalogue, this produces a false finding ("dep not in profile") even though
   AC4 says cross-catalogue deps skip local lookup. Update `_profile_required_deps` and
   `_profile_lint_one` to carry the `catalogue` field through and skip external entries
   (where `dep.catalogue != current_catalogue_name`) when checking profile closure.
   Use the same `current_catalogue_name` derivation as step 7 (config.name when config
   is not None; no fallback identity when config is None — skip closure check in that case).

**Installer alignment (same task):** `commands/install.py::validate_dependencies_required`
also enforces caret-only `^X.Y` grammar (documented in its docstring at line 4054). If
the verifier accepts `~X.Y` or `>=X.Y` ranges after T3 but the installer still rejects
them, a catalogue passes `catalogue verify` yet fails `catalogue install` — verification
would be lying. Update `validate_dependencies_required` to use the same shared
`parse_version_range` helper and satisfaction logic so that accepted ranges are also
installable. The version grammar is a contract invariant; verify and install must agree.

**Existing-test migration (same task):** Two existing tests assert caret-only rejection
behavior that T3's grammar expansion will reverse. Both must be updated or replaced as
part of T3 before the full suite can pass:

1. `packages/agentbundle/tests/integration/test_install_dependencies_gate.py:300` —
   `test_install_unsupported_range_grammar_rejected`: asserts `~0.1` is rejected and
   `"only ^X.Y is supported"` appears in stderr. After T3, `~0.1` is a valid RFC-0001
   tilde range that passes both `validate_dependencies_required` and the verifier. Update
   this test: replace with a positive tilde case AND a malformed case, AND add positive
   cases for every other newly accepted form — otherwise a broken comparator, compound, or
   prerelease implementation could pass every gate while `catalogue verify` accepts a dep
   that `catalogue install` rejects (the exact divergence this task eliminates). Add:
   - `test_install_valid_tilde_range_passes` — `~0.1.0` accepted by installer
   - `test_install_valid_comparator_range_passes` — `>=0.1.0` accepted by installer
   - `test_install_valid_compound_range_passes` — `>=0.1.0 <1.0.0` accepted by installer
   - `test_install_valid_prerelease_range_passes` — `>=0.1.0-alpha.1` accepted by installer
   - `test_install_malformed_range_rejected` — `"not-a-version"` rejected by installer
   Boundary-negative (just-outside-version): add at least one case per form (e.g. installed
   version 0.0.9 against `>=0.1.0`) asserting the installer emits a version-constraint finding.

2. `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py:533` —
   `test_check_profiles_unsupported_range_grammar`: asserts `~=0.1` produces CAT-L028
   "unsupported version range". After T3, `~=0.1` is still NOT a valid RFC-0001 range
   (RFC-0001 uses `~X.Y` not `~=X.Y`; `~=` is PEP-440 syntax) — this test may still be
   valid. Verify before changing: if `~=` is correctly rejected by the shared
   `parse_version_range` helper, the test stays as-is; if the helper mistakenly accepts it,
   the helper has a bug. Do NOT silently skip this check — run the lint test and confirm.

**Done when:**
```bash
python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_dependencies.py -q  # exits 0
python3 -m pytest packages/agentbundle/tests/integration/test_install_dependencies_gate.py -q  # exits 0
python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py -k "range" -q  # exits 0
```

---

## T4 — Adapter compatibility (step 8)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/tests/integration/test_catalogue_verify_adapter_compat.py` (new)

**Tests (write red first):**

stub: true — materialized in `test_catalogue_verify_adapter_compat.py`; collect passes
and the unknown-adapter assertion is red.

```python
class TestStepAdapterCompat:
    def test_no_allowed_adapters_passes(self, tmp_path):
        raise NotImplementedError  # STUB: AC5
    def test_known_adapter_passes(self, tmp_path):
        raise NotImplementedError  # STUB: AC5
    def test_unknown_adapter_emits_finding(self, tmp_path):
        raise NotImplementedError  # STUB: AC5
    def test_legacy_pack_skips_adapter_check(self, tmp_path):
        # fixture pack with [pack.install] allowed-adapters = ["not-real-adapter"] BUT
        # NO [pack.adapter-contract] section (legacy pack)
        # assert NO finding — installer ignores [pack.install] for legacy packs;
        # verifier must match (gate through pack_spec_version like _profile_pack_allowed_adapters)
        raise NotImplementedError  # STUB: AC5
    def test_pack_flag_scopes_adapter_check(self, tmp_path):
        # catalogue with two packs (A valid, B with unknown adapter in allowed-adapters)
        # run verify --pack A → assert NO finding (B's defect must not surface in A-only mode)
        # (AC5 scoping: check only the selected pack's adapter compat)
        raise NotImplementedError  # STUB: AC5
```

**Approach:**

Implement `_step_adapter_compat` with the same contract-version gate as
`_profile_pack_allowed_adapters`: for each pack, check its
`[pack.adapter-contract].version` field (`pack_toml.get("pack", {}).get("adapter-contract", {}).get("version")`).
If absent or `"0.1"` (legacy pack), skip the adapter-compat check entirely — the
installer ignores `[pack.install]` for legacy packs, so verifying `allowed-adapters`
here would reject valid legacy packs that happen to have stray values. For non-legacy
packs: read the `allowed-adapters` list key from `[pack.install]` (accessed as
`pack_toml.get("pack", {}).get("install", {}).get("allowed-adapters", [])` — `[pack.install]`
lives under the top-level `pack` key, not at the root of the parsed TOML dict);
for each named adapter string, verify it is a key in `contracts/adapter.toml [adapter]`.
Unknown adapter → finding. Load adapter keys from `_data/adapter.toml` via
`importlib.resources`. Replace `return []` with real implementation.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_adapter_compat.py -q` exits 0.

---

## T5 — Output drift (step 14)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/tests/integration/test_catalogue_verify_output_drift.py` (new)

**Tests (write red first):**

stub: true — materialized in `test_catalogue_verify_output_drift.py`; collect passes and
the confined-tree assertion is red.

```python
class TestStepOutputDrift:
    def test_no_generated_projections_passes(self, tmp_path):
        raise NotImplementedError  # STUB: AC6
    def test_up_to_date_projection_passes(self, tmp_path):
        raise NotImplementedError  # STUB: AC6
    def test_stale_projection_emits_finding(self, tmp_path):
        raise NotImplementedError  # STUB: AC6
    def test_file_only_in_configured_output_emits_finding(self, tmp_path):
        # configured output has a stale file that is absent from the fresh tree
        # (pack removed from catalogue but output not cleaned) — must produce a finding
        raise NotImplementedError  # STUB: AC6
    def test_file_only_in_fresh_output_emits_finding(self, tmp_path):
        # fresh tree has a file absent from configured output
        # (new pack added to catalogue but output not yet rebuilt) — must produce a finding
        raise NotImplementedError  # STUB: AC6
    def test_pack_flag_scopes_comparison_to_selected_pack(self, tmp_path):
        # catalogue with two packs (A and B); full build exists for both;
        # run verify --pack A → fresh tree contains only A; assert no finding
        # for pack B (out-of-scope packs must not produce spurious findings)
        raise NotImplementedError  # STUB: AC6
    def test_output_symlink_or_junction_escape_is_refused(self, tmp_path):
        # configured output contains a directory alias to an out-of-root sentinel
        # assert: root-relative finding; sentinel content is never compared
        raise NotImplementedError  # construction stub: confined output walk
    def test_output_resolution_loop_terminates_with_finding(self, tmp_path):
        # configured output contains a circular symlink/reparse path
        # assert: verifier catches resolution failure and terminates deterministically
        raise NotImplementedError  # construction stub: bounded output walk
```

**Approach:**

Implement `_step_output_drift` to detect stale build output. Key facts:
- `build-output` belongs to `[catalogue.paths]` and is loaded as `config.paths.build_output`
  (NOT `[distribution.agentbundle].build_output` — that path does not exist).
- The builder (`catalogue build`) emits projection trees: `dist/claude-plugins/`, `dist/apm/`.
  There are no versioned archives or manifests per pack in normal output.

Algorithm:
1. Resolve the build-output path: `root / (config.paths.build_output if config else "dist")`.
   If the directory does not exist, return `[]` (catalogue has never been built — not an error).
2. Re-run build into a fresh `tmpdir` sub-path (step 10 already does this — inspect if
   the temporary tree is already available via the shared tmpdir; if so, reuse it).
   **Selected-pack scoping:** if `catalogue verify --pack foo` was invoked, step 10 calls
   `build_catalogue(..., pack=pack)` and the fresh tree contains only the selected pack.
   Scope both trees to the same pack's projection paths (`dist/claude-plugins/<pack>/`,
   `dist/apm/<pack>/`) before comparing; otherwise all other packs in configured output
   produce spurious "stale" findings. When no `--pack` is specified, compare full trees.
3. Walk both trees with one confined regular-file iterator. Canonicalize each root; record
   the resolved current directory before inspecting filenames; reject child directories
   whose resolved path leaves the root, including Windows junction/reparse points; never
   follow symlink aliases; call `Path.is_junction()` when available (with a false-returning
   compatibility fallback); and catch both `OSError` and `RuntimeError` from resolution.
   Yield only root-relative paths so diagnostics cannot expose checkout paths. A refused
   path produces a structured finding and its target is never read.
4. Compare bidirectionally (scoped as above):
   a. For every file in the (scoped) configured output tree: if the file is absent from
      the fresh tree or its contents differ → emit a finding naming the stale path.
   b. For every file in the (scoped) fresh tree: if it is absent from the configured output
      → emit a finding naming the missing path (newly added pack projection not yet built).
5. Replace `return []` with real implementation.

Note: per-pack `.claude-code/`, `.cursor/`, `.kiro/`, `.copilot/`, `.codex/` trees do NOT
exist in the packs directory layout. Catalogue-level self-host projection drift is covered
by step 15 (`_step_selfhost_drift`); step 14 targets build-output package projection trees.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_output_drift.py -q` exits 0.

---

## T6 — Package preflight (step 17)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/tests/integration/test_catalogue_verify_package_preflight.py` (new)

**Tests (write red first):**

stub: true — materialized in `test_catalogue_verify_package_preflight.py`; collect passes
and the missing-manifest assertion is red.

```python
class TestStepPackagePreflight:
    def test_valid_pack_passes(self, tmp_path): ...
    def test_missing_pack_toml_emits_finding(self, tmp_path): ...
    def test_pack_toml_schema_violation_emits_finding(self, tmp_path): ...
    def test_missing_readme_does_not_emit_finding(self, tmp_path): ...
        # README.md is NOT required by the pack contract; the builder treats absence
        # as a no-op (test_no_readme_is_noop_not_error in build tests confirms this).
        # A verifier finding for missing README would introduce a new contract rule
        # under a correctness-only spec — not permitted. Assert no finding is emitted.
    def test_config_less_preflight_emits_no_finding(self, tmp_path): ...
        # This test exercises step 17 with config=None and a valid pack;
        # the step must fall back to root/"packs" and emit no finding.
    def test_catalogue_root_required_paths_are_out_of_scope(self, tmp_path): ...
        # valid pack.toml without marketplace/license files still passes step 17
        # because those are packaging-root rules, not pack preflight.
```

**Approach:**

Implement `_step_package_preflight` as the narrow pack contract in AC7:
1. Derive `packs_dir` from `config.paths.packs` when config exists, otherwise
   `root / "packs"`. A missing packs directory is an empty catalogue, not a step-17 error.
2. Iterate non-reserved pack directories, honoring `--pack` when supplied.
3. Require each selected pack's `pack.toml` to exist and parse as TOML; malformed or
   missing files emit a finding.
4. Validate the parsed value against bundled `pack.schema.json` using the existing
   stdlib validator; each schema error emits a finding.
5. Do not check README, catalogue-root required paths, licenses, marketplace files,
   package include lists, or packaging-content traversal. Replace `return []` with the
   implementation above.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_package_preflight.py -q` exits 0.

---

## T7 — Fixture checks (step 18)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/agentbundle/catalogue_tooling/skill_spec_lint.py` (promote nested validators to module-level)
- `packages/agentbundle/tests/integration/test_catalogue_verify_fixture_checks.py` (new)

**Tests (write red first):**

stub: true — materialized in `test_catalogue_verify_fixture_checks.py`; collect passes
and the malformed-manifest assertion is red.

```python
class TestStepFixtureChecks:
    def test_no_fixtures_passes(self, tmp_path):
        raise NotImplementedError  # STUB: AC8
    def test_valid_fixture_passes(self, tmp_path):
        raise NotImplementedError  # STUB: AC8
    def test_malformed_fixture_emits_finding(self, tmp_path):
        raise NotImplementedError  # STUB: AC8
    def test_empty_fixture_emits_finding(self, tmp_path):
        raise NotImplementedError  # STUB: AC8
    def test_missing_query_field_emits_finding(self, tmp_path):
        # eval_queries.json with entry missing required 'query' field
        # assert structural validation catches it (syntax is valid; shape is wrong)
        raise NotImplementedError  # STUB: AC8
    def test_non_boolean_should_trigger_emits_finding(self, tmp_path):
        # eval_queries.json with should_trigger = "yes" (string, not boolean)
        # assert structural validation catches it
        raise NotImplementedError  # STUB: AC8
    def test_pack_flag_scopes_fixture_check(self, tmp_path):
        # catalogue with two packs (A valid, B with malformed eval fixture)
        # run verify --pack A → assert NO finding (B's defect must not surface in A-only mode)
        # (AC8 scoping: check only the selected pack's eval fixtures)
        raise NotImplementedError  # STUB: AC8
    def test_payload_files_not_parsed(self, tmp_path):
        # skill with a valid evals/evals.json and a evals/files/sample.txt containing
        # intentionally non-JSON content (raw email body, binary chars)
        # assert: step 18 emits NO finding for the payload file
        # rationale: evals/files/** are opaque test inputs; parsing them produces false findings
        raise NotImplementedError  # STUB: AC8
```

**Approach:**

Implement `_step_fixture_checks` to scan for deterministic eval fixture files in the
canonical nested location: `.apm/skills/<skill>/evals/` (recursively per skill directory).
There is no pack-root `evals/` directory — eval files live per-skill under `.apm/`.

**Validator extraction (same task):** `_check_eval_queries` and `_check_evals_json` are
currently nested inside `lint_skill_spec`. Step 18 is a second caller (per AGENTS.md §
"Inline a single-use operation. Extract a helper once a second caller actually appears.")
— promote both to module-level private functions in `skill_spec_lint.py` as part of this
task (confirmed location: `skill_spec_lint.py:420` and `:448`). Call them from
`lint_skill_spec` exactly as before, AND call them from `_step_fixture_checks`. Do NOT
target `lint.py` — that module only imports `lint_skill_spec`; moving helpers there would
break the existing `lint_skill_spec` caller. This prevents the eval contract from silently
diverging between `catalogue lint` and `catalogue verify` when the eval format changes.
Do NOT inline a copy — two copies will drift. The module-level signature should stay
private (`_check_eval_queries`, `_check_evals_json`); no public API change is required.

For each skill directory under `.apm/skills/`:
1. Scan for `evals/evals.json` and `evals/eval_queries.json` only — do NOT recursively
   parse all `.json`/`.jsonl` under `evals/`. The `evals/files/` subtree contains opaque
   payload inputs (e.g. raw email bodies, binary attachments) that may be intentionally
   malformed or non-JSON; parsing them would produce false findings.
2. For each manifest file found (`evals.json`, `eval_queries.json`):
   a. Verify the file parses correctly (valid JSON) and has non-empty content →
      finding if malformed or empty.
   b. **Validate structural shape via the extracted module-level helpers:** call
      `_check_eval_queries` for `eval_queries.json` entries (required: `query` string,
      `should_trigger` boolean) and `_check_evals_json` for `evals.json` entries
      (required fields present). Structurally invalid fixtures produce findings.
3. For payload files referenced by manifest entries (e.g. `file` fields in eval entries):
   verify existence only — do NOT parse or validate their content.
Replace `return []` with real implementation. The test fixture must use
`.apm/skills/<skill>/evals/evals.json` and `evals/eval_queries.json` paths (not bare
`evals/*.json`) to exercise the actual layout, and must include a case where a
`evals/files/` payload exists but is intentionally non-JSON — assert no finding is emitted
for that file.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_fixture_checks.py -q` exits 0.

---

## T8 — Host-only leak extraction (step 11 blocklist)

**Verification mode:** TDD + goal-based

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py`
- `packages/agentbundle/agentbundle/catalogue_tooling/lint.py`
- `packages/agentbundle/tests/unit/test_catalogue_tooling_lint.py` (migrate existing assertion)
- `tools/catalogue/verify_host_checks.py` (new — repository-local tooling)
- `tools/catalogue/tests/test_verify_host_checks.py` (new — gate-chain contract test)
- `tools/repo/build_gate_chain.py` (wire new tool into gate chain)
- `Makefile` or `tools/repo/build_gate_chain.py` (add `tools/catalogue/tests/` to an executed test target)

**Tests (write red first):**

stub: true — materialized in `tools/catalogue/tests/test_verify_host_checks.py`; collect
passes. The red suite covers pattern detection in both preserved scan scopes, seed opt-in,
sentinel and fenced-example exemptions, confinement to the core APM tree, checker presence,
and both test/checker runtime gate registrations.

```python
# In test_catalogue_tooling_lint.py — migrate existing assertion:
# test_check_seeds_blocklist_hit currently asserts CAT-L029 is emitted when
# agent-ready-repo appears in seeds. After _SEEDS_BLOCKLIST_PATTERNS is emptied,
# this test must be updated: assert the pattern is NOT matched by the portable lint
# module; move the host-specific pattern-hit assertion to test_verify_host_checks.py.
def test_seeds_blocklist_is_empty_in_portable_lint(): ...
    # assert _SEEDS_BLOCKLIST_PATTERNS == [] (or equivalent empty check)
    # ensures no host-specific content leaks via re-import after extraction

# In tools/catalogue/tests/test_verify_host_checks.py — stdlib-only (AGENTS.md §238-241:
# new tools/ additions must be pure-stdlib Python; use unittest + tempfile, not pytest):
import unittest, tempfile, subprocess, sys, os

class TestHostCheckDetectsPattern(unittest.TestCase):
    # Seeds scan scope: packs with `lint-seeds = true` in pack.toml, within seeds/ subdir.
    # APM scan scope: packs/core/.apm/skills/ ONLY (hardcoded in current _step_agent_artifacts).
    # The new verify_host_checks.py MUST preserve these exact scan boundaries — broadening
    # them would cause build-check to fail on existing pack content (e.g. packs/atlassian
    # already contains RFC/K patterns in APM skill bodies; scanning beyond core would fail CI).
    # For seeds cases, content must be PLACEHOLDER-SHAPED: include the required placeholder
    # token for the seed filename (AGENTS.md requires "<project-name>") so that shape
    # validation passes before reaching the blocklist logic. If the fixture content fails the
    # placeholder check, the test passes trivially (blocklist never reached) — a false green.
    # The trigger pattern is EMBEDDED in the placeholder-shaped content.
    # File must be "AGENTS.md" (a recognized _SEEDS_REQUIRED_PLACEHOLDERS key) — "seeds.md"
    # is an unknown seed path and is rejected before the blocklist check runs.
    SEED_FILE = "packs/seed-test-pack/seeds/AGENTS.md"
    APM_FILE  = "packs/core/.apm/skills/test-skill/SKILL.md"
    CASES = [
        # Seeds — opted-in pack; recognized seed file; placeholder-shaped content + trigger.
        # Content: "A monorepo for `<project-name>` — contains {trigger}"
        ("agent-ready-repo",    SEED_FILE, True),
        ("RFC-0042",            SEED_FILE, True),
        ("K-0003",              SEED_FILE, True),
        ("distribution-adapters", SEED_FILE, True),
        # APM skill body — packs/core/.apm/skills/ only (preserve existing scope)
        ("agent-ready-repo",    APM_FILE,  False),
        ("RFC-0042",            APM_FILE,  False),
        ("K-0003",              APM_FILE,  False),
    ]
    def _make_seed_content(self, trigger: str) -> str:
        # Embed trigger inside placeholder-shaped AGENTS.md content so shape validation passes.
        # <project-name> is the required placeholder (from _SEEDS_REQUIRED_PLACEHOLDERS["AGENTS.md"]).
        return f"# AGENTS.md\nA monorepo for `<project-name>` — contains {trigger}"
    def _run_case(self, trigger, location, needs_lint_seeds_opt_in):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, location)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                if needs_lint_seeds_opt_in:
                    f.write(self._make_seed_content(trigger))
                else:
                    f.write(trigger)
            if needs_lint_seeds_opt_in:
                # write pack.toml with lint-seeds = true so seeds scanner includes this pack
                pack_toml = os.path.join(root, "packs", "seed-test-pack", "pack.toml")
                os.makedirs(os.path.dirname(pack_toml), exist_ok=True)
                with open(pack_toml, "w") as f:
                    f.write('[pack]\nname = "seed-test-pack"\nlint-seeds = true\n')
            result = subprocess.run(
                [sys.executable, "tools/catalogue/verify_host_checks.py", "--root", root],
                capture_output=True,
            )
            return result.returncode
    # Generate test methods for each case (one per case; parametrize requires pytest)

class TestSeedExemptions(unittest.TestCase):
    """Verify that verify_host_checks.py preserves _seeds_check_file's exemption mechanisms.

    Real-world case: packs/core/seeds/docs/CONVENTIONS.md has RFC-0013 guarded by a
    seed-content-lint-ignore sentinel. A literal pattern scanner that ignores exemptions
    would flag that seed and break make build-check.
    """
    def _seed_path(self, root: str) -> str:
        return os.path.join(root, "packs", "seed-test-pack", "seeds", "AGENTS.md")

    def _write_pack_toml(self, root: str) -> None:
        toml = os.path.join(root, "packs", "seed-test-pack", "pack.toml")
        os.makedirs(os.path.dirname(toml), exist_ok=True)
        with open(toml, "w") as f:
            f.write('[pack]\nname = "seed-test-pack"\nlint-seeds = true\n')

    def test_fenced_content_is_exempt(self):
        # pattern inside a Markdown code fence → no finding
        with tempfile.TemporaryDirectory() as root:
            self._write_pack_toml(root)
            target = self._seed_path(root)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write("# AGENTS.md\n<project-name>\n```\nagent-ready-repo\n```\n")
            result = subprocess.run(
                [sys.executable, "tools/catalogue/verify_host_checks.py", "--root", root],
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_sentinel_is_exempt(self):
        # pattern on the line after a seed-content-lint-ignore sentinel → no finding
        with tempfile.TemporaryDirectory() as root:
            self._write_pack_toml(root)
            target = self._seed_path(root)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as f:
                f.write(
                    "# AGENTS.md\n"
                    "<project-name>\n"
                    "<!-- seed-content-lint-ignore: test exemption -->\n"
                    "[RFC-0013](rfc/0013-credential-broker.md)\n"
                )
            result = subprocess.run(
                [sys.executable, "tools/catalogue/verify_host_checks.py", "--root", root],
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode())

class TestGateChainWiring(unittest.TestCase):
    def test_gate_chain_invokes_verify_host_checks(self):
        # import build_gate_chain; assert step list contains verify_host_checks.py
        # (NOT a source-substring grep — checks runtime step list)
        raise NotImplementedError  # STUB: AC9
    def test_host_check_tests_executed_by_ci(self):
        # assert tools/catalogue/tests/ is in a Makefile target or build_gate_chain step
        raise NotImplementedError  # STUB: AC9
```

**Approach:**

1. Remove from `verify.py`: `_APM_SKILL_BLOCKLIST` and all code that references it.
   Step 11 in `_VERIFY_STEPS` continues to exist (do not renumber); its implementation
   runs only portable checks (skill counts, duplicates, schema) after this change.

2. Remove from `lint.py` `_SEEDS_BLOCKLIST_PATTERNS` all host-specific patterns. At
   HEAD, all four patterns are host-specific to this repository:
   - `r"agent-ready-repo"` — the repo's catalogue name
   - `r"RFC-00\d\d"` — RFC numbering scheme used only in this repository
   - `r"K-00\d\d"` — knowledge item numbering scheme used only in this repository
   - The catalogue spec name list (distribution-adapters, self-hosting, etc.) — internal spec slugs
   Move all four to `verify_host_checks.py`. If an adopter's `_SEEDS_BLOCKLIST_PATTERNS`
   needs to remain non-empty, it must contain only patterns relevant to that adopter's
   conventions — the blocklist must not ship pre-populated with another catalogue's names.

3. Move the host-specific checks to `tools/catalogue/verify_host_checks.py`. This new
   script accepts `--root <dir>` and exits non-zero if host-specific content is found.
   The script **must preserve both exemption mechanisms from `_seeds_check_file`**:
   - **Fenced-content exemption:** patterns that appear inside Markdown code fences
     (```` ``` ```` ... ```` ``` ````) are NOT checked. The checker tracks fence state
     line-by-line (toggle on each bare fence marker) and skips pattern matching inside
     fences.
   - **`seed-content-lint-ignore` sentinel:** a line matching
     `<!-- seed-content-lint-ignore: <reason> -->` protects the NEXT non-blank,
     non-fence-marker content line from the blocklist check. The sentinel is consumed on
     the following content line regardless of whether a pattern matches.
   Both exemptions are load-bearing: `packs/core/seeds/docs/CONVENTIONS.md` currently
   has `RFC-0013` in a link exempted by a sentinel (confirmed at line ~1113). A literal
   pattern scanner that does not honour these exemptions would flag this file and break
   `make build-check`. Add negative tests for both exemptions (see test class below).

4. Wire `verify_host_checks.py` into `tools/repo/build_gate_chain.py`: add it as a
   gate step that is invoked during `make build-check`. Do not rely on script
   auto-discovery — add an explicit call in the gate chain's `build-check` step list.
   Without explicit wiring, the check silently disappears once the blocklists are removed
   from the portable modules.

**Done when:**
```bash
! grep -r "agent-ready-repo" packages/agentbundle/agentbundle/catalogue_tooling/verify.py  # exit 0 (no matches)
! grep -r "agent-ready-repo" packages/agentbundle/agentbundle/catalogue_tooling/lint.py    # exit 0 (no matches)
python3 tools/catalogue/verify_host_checks.py --help  # exit 0
python3 -m pytest tools/catalogue/tests/ -q  # exit 0 (host-check tests pass)
SKIP_SAST=1 make build-check  # exit 0 with verify_host_checks running as part of chain
# Note: tools/catalogue/tests/ must be wired into an executed test target (Makefile or
# build_gate_chain.py step) so CI runs these tests independently of the host repo being clean.
# A source-substring grep is insufficient — the step must assert runtime invocation.
```

---

## T9 — Step count and docstring fix

**Verification mode:** goal-based

stub: no stub (goal-based check)

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/verify.py` (module docstring, `verify_catalogue` docstring, verification-table comment)
- `packages/agentbundle/agentbundle/cli.py` (CLI help text at line ~781)
- Any living user guides in `docs/guides/` or `guides/` that reference "18-step pipeline"

**Tests:** none (goal-based)

**Approach:**

Search all public references to "18-step" across the agentbundle package and living guides:
1. In `verify.py`'s module-level docstring, replace `"18-step"` with `"19-step"`.
2. In `verify.py`'s `verify_catalogue` function docstring, replace `"18-step"` with `"19-step"` if present.
3. In `verify.py`'s verification-table comment block, update any "18-step" reference.
4. In `cli.py` (~line 781), update any "18-step" reference in the `catalogue verify` help string.
5. In any living user guide under `docs/guides/` or `guides/` that describes the verify pipeline, replace "18-step" with "19-step".
   Note: `docs/specs/catalogue-ci-documentation/spec.md:131` (Status: Shipped, frozen history) contains "18-step `verify`" as a point-in-time claim about the 0.22.x release surface — leave that instance intact; it is historical record, not a living guide.

Verify `len(_VERIFY_STEPS) == 19`.

**Done when:**
```bash
! grep -r "18-step" packages/agentbundle/  # 0 matches
! grep -r "18-step" docs/guides/ guides/   # 0 matches (or no guides reference this)
grep "19-step" packages/agentbundle/agentbundle/catalogue_tooling/verify.py  # 1+ matches
python3 -c "from agentbundle.catalogue_tooling.verify import _VERIFY_STEPS; assert len(_VERIFY_STEPS) == 19"  # exit 0
```

---

## T10 — PyYAML guard regression coverage (step 11)

**Verification mode:** TDD (regression coverage — this is NOT a defect fix)

**Touches:**
- `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py` (existing — contains the regression tests; no new file)

**Tests:**

stub: n/a — the named regression tests already exist and collect.

**Note:** `packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py` already
contains `test_step_agent_artifacts_pyyaml_absent` (monkeypatches `import yaml`, asserts
`CAT-V-011` warning Diagnostic is returned) and its clean-path companion. T10 does NOT
add new test stubs — the existing tests provide the regression coverage this task exists
to ensure. The only obligation of T10 is: verify that those existing tests still pass
after T8's blocklist extraction; confirm `_step_agent_artifacts` still returns
`[_warn("CAT-V-011", ...)]` when `import yaml` raises `ImportError`.

Do NOT create a new test file; do NOT duplicate the existing coverage. Do NOT modify
`verify.py` in this task.

**Done when:** `python3 -m pytest packages/agentbundle/tests/unit/test_catalogue_tooling_verify.py -k pyyaml -q` exits 0 (existing tests still pass after T8 refactor).

---

## T11 — External-catalogue portability test

**Verification mode:** TDD

**Depends on:** T0–T10, T2b

**Touches:**
- `packages/agentbundle/tests/fixtures/external_catalogue/` (new fixture directory)
- `packages/agentbundle/tests/integration/test_catalogue_verify_external_portability.py` (new; filesystem — uses fixture dir and tmp_path)

**Tests:**

stub: true — materialized with the synthetic `external_catalogue` fixture and
`test_catalogue_verify_external_portability.py`; collect passes and the host-leak
assertion is red while the nineteen-step assertion is green.

```python
FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "external_catalogue"

class TestExternalCataloguePortability:
    def test_verify_exits_0_on_clean_external_catalogue(self, tmp_path):
        # Run agentbundle catalogue verify against external_catalogue fixture
        # assert exit code 0
        raise NotImplementedError  # STUB: AC12
    def test_no_host_specific_findings(self, tmp_path):
        # assert no finding references "agent-ready-repo" or host-specific identifiers
        raise NotImplementedError  # STUB: AC12
    def test_step_count_is_19(self):
        # assert len(_VERIFY_STEPS) == 19 (programmatic unit check — VerifyResult
        # does not expose per-step output, so this is not derivable from CLI output)
        raise NotImplementedError  # STUB: AC10
    def test_external_catalogue_with_agent_ready_repo_in_seeds_passes(self, tmp_path):
        # fixture: a pack with lint-seeds = true in pack.toml; seed file at
        # seeds/AGENTS.md (a recognized _SEEDS_REQUIRED_PLACEHOLDERS key) with content:
        #   "A monorepo for `<project-name>` — discusses agent-ready-repo"
        # (includes required placeholder "<project-name>" + the pattern to be de-flagged)
        # assert: catalogue verify exits 0 — after lint blocklist extraction, "agent-ready-repo"
        # in a portable catalogue's seed is no longer flagged by the verifier
        # (DO NOT use seeds.md — it is rejected as an unknown seed path before reaching lint)
        raise NotImplementedError  # STUB: AC12
```

Fixture: a minimal two-pack catalogue with no host-specific content, valid
`.claude-plugin/plugin.json` in each pack, valid `pack.toml`, valid `profile.toml`.
A separate seed fixture at `seeds/AGENTS.md` (recognized path) contains both
`<project-name>` (required placeholder to pass shape validation) and the literal string
"agent-ready-repo" to exercise the lint-blocklist-extraction test case above.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_verify_external_portability.py -q` exits 0.

---

## T12 — Version + changelog + closeout

**Verification mode:** goal-based

stub: no stub (goal-based check)

**Depends on:** T0–T11, T2b

**Touches (this PR):**
- `packages/agentbundle/pyproject.toml` — derive and apply the next available version
- `packages/agentbundle/agentbundle/version.py` — same
- `packages/agentbundle/README-pypi.md` — describe the release-bearing verifier behavior
- `docs/product/changelog.md` — add the new release section; do not duplicate T1
- `docs/specs/catalogue-verifier-correctness/spec.md` — check completed ACs and set Shipped
- `docs/specs/catalogue-verifier-correctness/plan.md` — set Done

**Touches (post-publish follow-on PR):**
- `workspace.toml` (move verifier-correctness from queue to shipped)

**Tests:** none (goal-based)

**Approach:**

1. Inspect current HEAD version and bump to next available AgentBundle minor.
2. Add changelog entry covering: profile schema validation;
   dependency (with version range) / adapter / output-drift / package-preflight / fixture
   implementations; host-only leak extracted to repository-local tooling; all public
   "18-step" references updated to "19-step"; regression coverage added for PyYAML guard
   (was already correct; no behavior change).
3. Update `README-pypi.md` so the checked-in package description matches the release.
4. Include `Engine-Change-RFC: RFC-0076` in the commit message footer (verify.py
   is catalogue tooling infrastructure; D1/D2 authority model).
5. Check every completed AC, set spec Status to Shipped, and set plan Status to Done.
6. Run full gates: `SKIP_SAST=1 make build-check`; `python3 -m pytest packages/agentbundle/tests/ -q`.
7. Tag and publish to PyPI — T3 changes accepted dependency-range semantics for
   `validate_dependencies_required`, which is a public CLI semantic change per
   `packages/AGENTS.local.md:7-13`. After the PR merges: tag `agentbundle-vX.Y.Z` and
   push to PyPI via the standard release process before closing out this spec.

**Post-publish follow-on (separate change, after PyPI release is confirmed):**
8. Move `spec/catalogue-verifier-correctness` from `queue` to `shipped` in `workspace.toml`.

Only step 8 waits for publication confirmation; package policy permits the release PR to
close the spec and plan while workspace membership remains active until publication.

**Done when:**
```bash
SKIP_SAST=1 make build-check   # exit 0
python3 -m pytest packages/agentbundle/tests/ -q   # exit 0
! grep "agent-ready-repo" packages/agentbundle/agentbundle/catalogue_tooling/verify.py  # exit 0
grep "19-step" packages/agentbundle/agentbundle/catalogue_tooling/verify.py   # 1 match
```

## Constraints

- T11 may not start until T0–T10 and T2b all pass gates — the portability test validates the
  cumulative result of all corrections.
- T12 must be last; derive its version only after T0–T11 and T2b pass gates and re-check
  current workspace collision notes at execution time.
- No step may be left returning `return []` without a real implementation or a
  `NotImplemented` finding — silent empty results are the root cause of this spec.

## Risks

- Output drift (T5) requires deriving a deterministic re-projection read-only. If the
  projection logic is not cleanly separable from the write path, T5 may need to defer
  the comparison to a simpler file-hash comparison against a stored baseline.
- Package preflight (T6) schema validation depends on `pack.schema.json` being up to date
  at implementation time. If Wave 4 has amended the schema, T6 must use the amended schema.
- External-catalogue fixture (T11) must not include any content from this repository's
  packs directory — use synthetic fixture data only.
