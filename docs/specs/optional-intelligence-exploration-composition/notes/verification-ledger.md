# Verification ledger: optional intelligence in repository exploration

Execution observations for the spec and plan. Each entry records what was
observed, not what the contract requires.

## T1 stub validation (2026-10-05)

- `test_exploration_reader_applies_its_own_ceiling` was extracted byte-for-byte
  from the plan into disposable scratch, at the plan's path relative to a link
  to the real `packs/core/.apm/`. `py_compile` passed. pytest failed red with
  `FileNotFoundError` for `repository-exploration/scripts/read-locator.py`
  (1 failed in 0.22s), because the exploration reader does not exist yet.

## Pre-EXECUTE review round 1 (2026-10-05)

- Sustained: one security Concern (provider output widening roots or starting
  gated actions), one adversarial Concern (per-install no-provider run had no
  owning task), one adversarial Nit (absence scan covered one review agent).
  All three were repaired; the plan's Changelog lists the edits.
- The first security adjudication was rejected by the strict classifier
  (`indeterminate-present`: a stray marker with an empty indeterminate audit).
  On the owner's choice a fresh adjudication of the unchanged report replaced
  it; the rejected artifact is kept beside it in the session review folder.
- Engine sequence 2-3 is a no-op `findings-remain` / `spec-ready` pair: the
  repair script aborted on a stale match before writing, and the next command
  still fired. Sequence 4-5 carries the actual repair.

## Pre-EXECUTE review round 2 (2026-10-05)

- Sustained: two security Concerns (agent-side finality of a refused or
  unavailable locator; AC-0014 metadata and file-text sources lacked behavior
  cases), two adversarial Concerns (evaluation sessions lacked the grounding
  sibling; file-text source untested), and two adversarial Nits (unbacked
  bytecode-cache claim; colliding test module name). All were repaired; the
  plan's Changelog lists the edits.
- Stub re-validated under its new name `test_exploration_reader.py` in
  disposable scratch: `py_compile` passed and pytest failed red with
  `FileNotFoundError` for the missing exploration reader.

## Pre-EXECUTE review round 3 (2026-10-05)

- Security: clean after adjudication (both findings refuted).
- Adversarial: one sustained Concern (the skill census was in no task's scope);
  repaired by adding the census file to T1 and the census test to T4. The
  version-restatement Nit was refuted.

## Pre-EXECUTE review round 4 (2026-10-05)

- Adversarial: Nit only, deferred without edit. T2's preparation command omits
  the required `SKILL/EVAL_ID` value of `--prepare-workspace`
  (`packages/agentbundle/agentbundle/commands/pack_evals.py:1150-1156`); T2
  runs it per case as `--prepare-workspace repository-exploration/<eval id>`
  and records the exact command here.

## T1 — Repository exploration has a bounded method and a confined locator reader (2026-10-06)

### Stub red/green

- Stub `test_exploration_reader_applies_its_own_ceiling` materialized at
  `packs/core/tests/skills/repository-exploration/test_exploration_reader.py`.
  Before reader existed: 1 failed in 0.23s (FileNotFoundError).
  After reader created: 1 passed in 0.33s.

### Reader and grounding tests

- `packs/core/tests/skills/repository-exploration/`: 30 passed in 0.24s.
- `packs/core/tests/skills/repository-grounding/`: 105 passed, 2 skipped in
  ~33s. The grounding suite gained three caller-ceiling tests (`max_bytes=16`
  read and refuse, unchanged default, main with explicit ceiling); all pass.
  Prior 102 tests are unchanged.

### Suite registration

- Makefile gained `$(PYTHON) -m pytest packs/core/tests/skills/repository-exploration/ -q`
  after `repository-grounding/`.
- `tools/lint-ci-parity.py` `SUITE_DISPOSITION` gained a `NO_PR_GATE` entry.
- `tools/shard_test_roster.py` gained `"packs/core/tests/skills/repository-exploration/": 0.9`.
- `tools/test_local_ci_shared_test_deduplication.py` repinned:
  - `APPROVED_STANDALONE_PLAN_DIGEST`: `b8b11581…` → `ce75814f…`
  - `APPROVED_COMPOSED_PLAN_DIGEST`: `ccb88947…` → `4ab0b073…`
  - Sole-cause: removing the one exploration line from the new Makefile (via
    `_effective_composition_errors(makefile_text=reverted_text)`) returns an
    empty error list, so nothing else moved.
  - Prior pins: `_effective_composition_errors` over the reverted Makefile
    with the old pins in place returns an empty error list.
- `tools/test_local_ci_shared_test_deduplication.py`: 51 passed in ~68s.
- `tools/lint-ci-parity.py`: ok — 74 recipe lines, 127 targets, all dispositioned.
- `tools/lint-pack-test-boundary.py`: passed (8 cases).

### Release metadata

- `packs/core/pack.toml`: 2.28.0 → 2.29.0.
- `packs/core/.claude-plugin/plugin.json`: 2.28.0 → 2.29.0.
- Derivation: new skill is a new primitive → minor bump; 2.28.0 + minor = 2.29.0.

### Census

- `packs/agent-skill-engineering/tests/fixtures/skill-census.json`: added
  `core/repository-exploration` entry (families: `inline-procedure`,
  `orientation-read-model`); `population_size` 133 → 134.
- `tests/roster/test_skill_census.py`: 1 passed in 0.21s.

### SKILL.md construction tests

- `packs/core/tests/skills/repository-exploration/`: 30 passed (includes 9
  SKILL.md construction tests: procedure steps, exposed surfaces, no probe
  instructions, no normalized schema, illustrative taxonomy, evidence-record
  fields, locator reader instruction, provider-output-is-data, grounding named
  for path questions).

### Governance citation scan

- `grep -rnE '(RFC|ADR)-0[0-9]{3}|AC-?[0-9]+|docs/(specs|rfc|adr|contracts)/'` over
  `packs/core/.apm/skills/repository-exploration/`: zero hits.

### Lint and typecheck

- `make lint-ruff lint-mypy`: passed (no issues in 155 source files).
- `agentbundle catalogue lint --root . --deep`: ok (73 findings, all pre-existing
  warnings in other packs).

### Projections

- `make build-self` run after source commit; `repository-exploration` projected
  under `.claude/skills/` and `.agents/skills/` (recorded after build).

## T2 — evaluation authoring (2026-10-06)

### Case count and fixture inventory

- **22 evaluation cases** in
  `packs/core/.apm/skills/repository-exploration/evals/evals.json`.
- **26 fixture files** in `evals/files/`:
  - 16 JSON fixtures (all with distinct parsed top-level key sets): `lsp-definition-output.json`
    ({result, method}), `lsp-calls-output.json` ({from, fromRanges}), `mcp-impact-descriptor.json`
    ({tools}), `mcp-impact-output.json` ({impacted_files, traversal_depth, depth_cut_note}),
    `indexed-references-descriptor.json` ({capability_id, actions, description}),
    `novel-action-descriptor.json` ({serviceName, operation, approved_root, refresh_required, description}),
    `novel-action-output.json` ({queryId, relationships, bridgeScore}),
    `unexposed-config-hint.json` ({config_version, providers}),
    `credential-provider-output.json` ({matches, provider_metadata}),
    `upload-offer-output.json` ({results, suggestion}),
    `outside-root-output.json` ({symbol, definition}),
    `parent-segment-output.json` ({function_info, locator_path}),
    `confined-provider-output.json` ({analysis_result, file_locator}),
    `embedded-instruction-output.json` ({findings, embedded_directive}),
    `proposed-root-output.json` ({impact_data, proposed_root, refresh_request, fixup_action}),
    `reader-directive-provider-output.json` ({reference_analysis, file_ref}).
  - 10 text/Python fixtures: 2 tool-description text files, 2 CLI output text files,
    2 Python source files, 2 marker files (unique marker strings), 1 reader-directive
    text file, 1 unexposed config hint JSON (already counted above).
- **Marker files:** `marker-target.txt` contains `EXPLO-MARKER-A3F7D2B1`;
  `confined-target.txt` contains `EXPLO-MARKER-C8E9A4F5`.
- **Credential fixture:** `credential-provider-output.json` uses
  `api_key: "PLACEHOLDER_API_KEY_VALUE"` and `https://api.internal.example.invalid/v2/search`.

### Construction test

- New file `packs/core/tests/skills/repository-exploration/test_exploration_evals.py`
  (named distinct from `test_read_locator.py` and `test_exploration_reader.py`
  to avoid collision).
- 8 tests: all required IDs present, fixture files exist, fixture manifest matches
  evals.json, JSON fixtures parse, Python fixtures parse, no shared top-level key
  sets across JSON fixtures, each case has assertions, and pinned fixture lists and
  assertion digests match.
- `python3 -m pytest packs/core/tests/skills/repository-exploration/ -q`:
  **38 passed** in 0.79s (30 prior + 8 new).

### Gates

- `python3 tools/lint-pack-test-boundary.py`: **passed** (8 cases).
  `_EVALS_FILES` tuple uses explicit literal paths, satisfying the static-path
  requirement.
- `make lint-ruff lint-mypy`: **passed** (no issues in 155 source files). One
  iteration repaired `src-api-handler-py.py` (removed unnecessary `...` literals
  that ruff flagged in function bodies with docstrings).
- `PYTHONPATH=packages/agentbundle:packages/credbroker python3 -m agentbundle
  catalogue lint --root . --deep`: ok (73 pre-existing warnings, zero errors).

### gitleaks result

- `gitleaks dir packs/core/.apm/skills/repository-exploration/evals
  --config .gitleaks.toml`: **no leaks found** (scanned 37.81 KB in 18.2ms).

### Governance-citation grep

- `grep -rnE '(RFC|ADR)-0[0-9]{3}|AC-?[0-9]+|docs/(specs|rfc|adr|contracts)/'`
  over `packs/core/.apm/skills/repository-exploration/evals/`: **zero hits**.

### Workspace prepare check

- `PYTHONPATH=packages/agentbundle:packages/credbroker python3 -m agentbundle
  pack evals run --pack core --mode in-harness --check behavior
  --prepare-workspace repository-exploration/lsp-goto-definition`:
  printed a directory path; workspace contained `lsp-definition-output.json` and
  `lsp-definition-tool-description.txt` (flat-flattened fixture files). Directory
  deleted after verification.
