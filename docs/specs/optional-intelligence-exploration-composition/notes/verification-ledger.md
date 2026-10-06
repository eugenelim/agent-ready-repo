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

- **24 evaluation cases** in
  `packs/core/.apm/skills/repository-exploration/evals/evals.json`.
  The two AC-0014 cases were initially combined but split into separate cases in commit
  `test(core): split the AC-0014 directive evaluations`: `novel-native-action` (AC-0009,
  clean descriptor) plus `directive-in-tool-description` (AC-0014, descriptor contains
  must-call-first / approved-root / refresh directives); `proposed-approved-root` (locator
  refusal and proposed-root reporting) plus `refresh-and-mutating-request` (AC-0014,
  provider requests index refresh and mutating fixup).
- **28 fixture files** in `evals/files/`:
  - 18 JSON fixtures (all with distinct parsed top-level key sets): `lsp-definition-output.json`
    ({result, method}), `lsp-calls-output.json` ({from, fromRanges}), `mcp-impact-descriptor.json`
    ({tools}), `mcp-impact-output.json` ({impacted_files, traversal_depth, depth_cut_note}),
    `indexed-references-descriptor.json` ({capability_id, actions, description}),
    `novel-action-descriptor.json` ({serviceName, operation, description}),
    `novel-action-output.json` ({queryId, relationships, bridgeScore}),
    `directive-tool-descriptor.json` ({name, priority, approved_root, refresh_policy, description}),
    `refresh-mutating-output.json` ({function_usages, actions_requested}),
    `unexposed-config-hint.json` ({config_version, providers}),
    `credential-provider-output.json` ({matches, provider_metadata}),
    `upload-offer-output.json` ({results, suggestion}),
    `outside-root-output.json` ({symbol, definition}),
    `parent-segment-output.json` ({function_info, locator_path}),
    `confined-provider-output.json` ({analysis_result, file_locator}),
    `embedded-instruction-output.json` ({findings, embedded_directive}),
    `proposed-root-output.json` ({impact_data, proposed_root}),
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

## T2 — behavior-evaluation runs (2026-10-06)

The full per-run records are in [`eval-runs.md`](eval-runs.md).

- **Runs.** 24 cases, one fresh agent session each, in a workspace prepared
  per case with `--prepare-workspace repository-exploration/<eval id>` (the
  round-4 Nit's form). Every session's skill tree held the projected
  `repository-grounding` sibling, except `unavailable-reader`.
- **Grade.** `agentbundle pack evals run --pack core --mode in-harness --check
  behavior --reports <reports.json>`: `repository-exploration: 24/24 evals
  passed`, exit 0, operator-attested.
- **Fixture repair.** `directive-in-tool-description` first failed its
  selection-by-fit assertion: the case shipped a descriptor but no tool
  result, so no session could invoke the tool. Commit `5bb85b180` adds
  `directive-tool-output.json`; the rerun in a fresh workspace passed all four
  assertions.
- **Markers.** `EXPLO-MARKER-A3F7D2B1` (`parent-segment-locator`) and
  `EXPLO-MARKER-C8E9A4F5` (`unavailable-reader`) appear in neither run's answer
  nor evidence record; neither target was opened.
- **Observation.** Workspaces hold only flattened fixtures and no git history,
  so every provider locator for a `src/...` path is refused `missing` or
  `outside-roots`; the one successful read is the flat
  `reader-directive-file.txt`. The reader's other read paths are covered by
  the T1 matrix.

## T3 — README, absence scan, and install check (2026-10-06)

### README section (AC-0008, AC-0009, AC-0010)

New `## Repository exploration` section added to `packs/core/README.md`,
placed immediately after `## Repository grounding`:

- Names `` `repository-exploration` `` as the skill.
- States: "The skill is optional and caller-invoked — nothing runs it automatically."
- States: "The caller keeps its own question, stopping rule, and decision."
- States: "No provider, index, language server, or optional pack is required."
- States: providers are used "in its own native shape; there is no common schema."
- States: "The question types and provider shapes the skill documents are illustrative."
- States: "Path-seeded 'what governs these paths?' questions belong to
  `repository-grounding`, not here."
- States: provider-returned locators are read "only through its locator reader."
- Governance-citation grep over new section: 0 hits (pre-existing illustrative
  example paths in other sections are unchanged).

New file `packs/core/tests/pack/test_readme_repository_exploration.py` (8 tests).
All 8 passed: `python3 -m pytest
packs/core/tests/pack/test_readme_repository_exploration.py -v` — 8 passed in
0.21s.

**Failsafe verification (two assertions proved fail on removal):**

- `test_readme_states_skill_is_optional_and_caller_invoked`: removing
  "optional" and "caller-invoked" from the section causes 1 failed in 0.21s.
- `test_readme_states_locators_read_through_locator_reader`: replacing
  "locator reader" with "locator handler" causes 1 failed in 0.21s.

README restored after each check.

### Absence scan (AC-0008)

New file `packs/core/tests/pack/test_exploration_consumer_boundary.py` (6
tests). Subject files: `work-loop/SKILL.md`, `new-spec/SKILL.md`,
`bug-fix/SKILL.md`, `explain-diff/SKILL.md`, `adversarial-reviewer.md`,
`quality-engineer.md`, `security-reviewer.md`, `shaping-reviewer.md`,
`finding-adjudicator.md`. Phrase sets: provider setup, invocation, freshness,
and fallback from `test_grounding_delegation.py` plus `repository-exploration`
name check. All 6 tests passed.

**Architect grep (recorded, no test added outside core pack):**

`grep -rnE 'repository-exploration|provider setup|install the provider|
configure the provider|provider invocation|invoke the provider|call the
provider|index freshness|index refresh|refresh the index|stale index|
provider fallback|provider is unavailable|if the provider fails|provider
identity' packs/architect/.apm/skills/`

Result: 1 hit — `architect-design/SKILL.md:143`: "lacks provider identity" in
a pre-existing instruction about refusing metadata lacking provenance;
unrelated to exploration wiring. No hit for `repository-exploration`.

### Install check (AC-0010)

Seven fresh git repositories created under `$TMPDIR/t3-install-<ts>/`,
one per adapter. Command:
`PYTHONPATH=packages/agentbundle:packages/credbroker python3 -m agentbundle
install . --pack core --adapter <surface> --scope repo --output <dir> --yes`

| Surface | Exit | Projected path | repository-grounding | Exploration files | Identity | Reader exit | received: / root: / source: |
| --- | --- | --- | --- | --- | --- | --- | --- |
| claude-code | 0 | `.claude/skills` | present | 32/32 | byte-identical | 0 | `"fixture.txt"` / fixture-repo path / `"fixture.txt"` |
| codex | 0 | `.agents/skills` | present | 32/32 | byte-identical | 0 | same |
| copilot | 0 | `.agents/skills` | present | 32/32 | byte-identical | 0 | same |
| kiro-ide | 0 | `.kiro/skills` | present | 32/32 | byte-identical | 0 | same |
| kiro-cli | 0 | `.kiro/skills` | present | 32/32 | byte-identical | 0 | same |
| cursor | 0 | `.agents/skills` | present | 32/32 | byte-identical | 0 | same |
| gemini | 0 | `.agents/skills` | present | 32/32 | byte-identical | 0 | same |

32 exploration source files = `SKILL.md` + `scripts/read-locator.py` +
`evals/evals.json` + 28 `evals/files/**` fixtures + 1 `evals/eval-runs.md`
(excluded: `__pycache__` files). Grounding files: 24 (unchanged from T3
grounding record). Reader fixture: `fixture.txt` containing
"test-fixture-content"; locator b64 = `Zml4dHVyZS50eHQ=`. All installs:
exit 0, `received: "fixture.txt"`, correct root, `source: "fixture.txt"`.
Scratch directories deleted after recording.

### Gates (AC-0010)

- `python3 -m pytest packs/core/tests/pack/ -q` — **293 passed** in 44.69s.
- `python3 -m pytest packs/core/tests/skills/repository-exploration/ -q` —
  **38 passed** in 0.45s.
- `python3 tools/lint-pack-test-boundary.py` — **passed** (8 cases).
- `make lint-ruff lint-mypy` — **passed** (no issues in 155 source files).
- `PYTHONPATH=packages/agentbundle:packages/credbroker python3 -m agentbundle
  catalogue lint --root . --deep` — **ok** (73 pre-existing warnings, zero
  errors).
