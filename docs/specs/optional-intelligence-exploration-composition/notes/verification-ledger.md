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

### Review repair round 1 (post-gates, 2026-10-06)

Repairs from the sustained post-gates adversarial, quality-engineer, and
experience-reviewer findings. Three red proofs recorded here; gates re-run
after each restore.

**Red proof 1 — Ask-first list complete (`test_skill_ask_first_list_complete`):**
Temporarily removed `"calling a hosted service beyond existing authority, "` from
the SKILL.md Ask-first line; `test_skill_ask_first_list_complete` failed
(`1 failed in 0.30s`, AssertionError at line 775). Phrase restored; test green.

**Red proof 2 — Procedure order (`test_skill_procedure_steps_present`):**
Temporarily removed step 5 (`5. **Keep caveats.** …`) from SKILL.md §Procedure;
`test_skill_procedure_steps_present` failed (`1 failed in 0.38s`, AssertionError
at line 578: phrase `"keep caveats"` not found in § Procedure). Step restored; test green.

**Red proof 3 — CLI ceiling forwarding (`test_cli_ceiling_forwarded_by_main`):**
Temporarily removed `max_bytes=MAX_PROVIDER_READ_BYTES` from `gr.main(argv, …)`
in `scripts/read-locator.py`; `test_cli_ceiling_forwarded_by_main` failed
(`1 failed`, `AssertionError: Expected exit 3 for oversize file, got 0`).
Grounding's default 2 MB ceiling applied instead of the monkeypatched 16 bytes,
so the 17-byte file was read (exit 0) rather than refused. Argument restored; test green.

**Files changed in repair round 1:**
- `packs/core/.apm/skills/repository-exploration/SKILL.md`: wording (`none becomes
  a phase` → `no tool is ever a required step`); Ask-first list widened to include
  `uploading content` and `calling a hosted service beyond existing authority`.
- `packs/core/.apm/skills/repository-exploration/evals/evals.json`: five prompts
  neutralized (conflicting-derived-sources, outside-root-locator, parent-segment-
  locator, proposed-approved-root, unavailable-reader); two assertions added to all
  24 cases (AC-0001 and AC-0007 graders).
- `packs/core/tests/skills/repository-exploration/test_exploration_reader.py`:
  `_PROCEDURE_STEPS` replaced with `_PROCEDURE_STEP_PHRASES`; `test_skill_procedure_steps_present`
  scoped to § Procedure and made order-checking; `test_skill_locator_read_through_reader_script`
  and `test_skill_provider_output_is_data` scoped to their sections; 11 new tests added
  (no-preferred-class, locator-section root source, locator-section finality, provider-output
  file-text, three cannot-rules, ask-first-complete, CLI ceiling, CLI read buffer/order).
- `packs/core/tests/skills/repository-exploration/test_exploration_evals.py`: all 24
  pinned assertion digests updated.
- `packs/core/README.md`: glosses added for caller, native shape, repository-native
  evidence; locator paragraph condensed to one sentence.
- `docs/specs/optional-intelligence-exploration-composition/notes/verification-ledger.md`:
  pre-rebase SHA corrected; T2 fixture count corrected to 29; T3 file breakdown corrected.

**Gate result after repair round 1:**
- `pytest packs/core/tests/skills/repository-exploration/ packs/core/tests/pack/ -q`:
  340 passed (47 skill + 293 pack).
- `make lint-ruff lint-mypy`: passed (155 source files, no issues).
- `python3 tools/lint-pack-test-boundary.py`: passed (8 cases).
- `agentbundle catalogue lint --root . --deep`: ok (75 pre-existing warnings, zero errors).
- Governance-citation grep over skill dir and README exploration section: zero new hits.

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
- **29 fixture files** in `evals/files/`:
  - 19 JSON fixtures, each with a distinct parsed top-level key set: `confined-provider-output.json` ({analysis_result, file_locator}), `credential-provider-output.json` ({matches, provider_metadata}), `directive-tool-descriptor.json` ({name, priority, approved_root, refresh_policy, description}), `directive-tool-output.json` ({navigation_hits, index_state}), `embedded-instruction-output.json` ({findings, embedded_directive}), `indexed-references-descriptor.json` ({capability_id, actions, description}), `lsp-calls-output.json` ({from, fromRanges}), `lsp-definition-output.json` ({result, method}), `mcp-impact-descriptor.json` ({tools}), `mcp-impact-output.json` ({impacted_files, traversal_depth, depth_cut_note}), `novel-action-descriptor.json` ({serviceName, operation, description}), `novel-action-output.json` ({queryId, relationships, bridgeScore}), `outside-root-output.json` ({symbol, definition}), `parent-segment-output.json` ({function_info, locator_path}), `proposed-root-output.json` ({impact_data, proposed_root}), `reader-directive-provider-output.json` ({reference_analysis, file_ref}), `refresh-mutating-output.json` ({function_usages, actions_requested}), `unexposed-config-hint.json` ({config_version, providers}), `upload-offer-output.json` ({results, suggestion}).
  - 10 non-JSON fixtures: 3 tool descriptions (`lsp-definition-tool-description.txt`, `lsp-calls-tool-description.txt`, `cli-dep-tool-description.txt`), 2 CLI outputs (`cli-dep-output.txt`, `cli-search-conflict-output.txt`), 2 Python sources (`src-api-handler-py.py`, `src-function-py.py`), 2 marker files (`marker-target.txt`, `confined-target.txt`), and 1 reader-directive file (`reader-directive-file.txt`).
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
  result, so no session could invoke the tool. Commit `9b39e930e` adds
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
`evals/evals.json` + 29 `evals/files/**` fixtures
(excluded: `__pycache__` files, `evals/eval-runs.md` is not a projected source).
Grounding files: 24 (unchanged from T3
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

## T4 — repository gates and release (2026-10-06)

### Repository gates

| Gate | Result | Count | Runtime |
| --- | --- | --- | --- |
| `pytest packs/core/tests/skills/repository-exploration/ packs/core/tests/skills/repository-grounding/ -q` | pass | 143 passed, 2 skipped | 62.90s |
| `pytest packs/core/tests/pack/ -q` | pass | 293 passed | 37.90s |
| `pytest tests/roster/test_skill_census.py -q` | pass | 1 passed | 0.28s |
| `pytest tools/test_local_ci_shared_test_deduplication.py -q` | pass | 51 passed | 127.70s |
| `pytest tools/test_intent_corpus_gate.py tools/test_check_core_release.py -q` | pass | 34 passed | 69.25s |
| `make lint-ruff lint-mypy` | pass | 155 source files, no issues | ~8s |
| `python3 tools/lint-ci-parity.py` | pass | 74 recipe lines, 127 targets, all dispositioned | — |
| `python3 tools/lint-pack-test-boundary.py` | pass | 8 cases | — |
| `agentbundle catalogue lint --root . --deep` | pass | 73 pre-existing warnings, zero errors | — |
| `agentbundle catalogue verify --root .` | pass | ok | — |
| `python3 .claude/skills/work-loop/scripts/lint-spec-status.py --root .` | pass | 2 of 530 specs changed, metadata clean | — |
| `python3 tools/repo/check_release_impact.py --base origin/main` | pass | 116 changed files, none release-impacting | — |
| Governance-citation grep over `packs/core/.apm/skills/repository-exploration/` | pass | zero hits | — |
| `pytest tools/test_build_site_routing.py::test_the_generator_projects_the_real_changelog_into_a_valid_payload -q` | pass | 1 passed | 0.74s |

### Release record

- **Baseline:** Core 2.28.0 at `origin/main` (the `## [core][2.28.0] — 2026-10-05` entry).
- **Derivation:** `repository-exploration` is a new primitive → minor class → 2.28.0 + minor = **2.29.0**.
- **Manifests:** `packs/core/pack.toml` version = `2.29.0`; `packs/core/.claude-plugin/plugin.json` version = `2.29.0`. Both agree.
- **Marketplace:** `.claude-plugin/marketplace.json` lists 16 plugins; `core` is absent (Core is a repository-only pack).
- **Changelog entry:** Free-standing `## [core][2.29.0] — 2026-10-06` inserted directly above `## [core][2.28.0] — 2026-10-05` in `docs/product/changelog.md`.
- **Highlights disposition:** Consumer-visible change — adds `repository-exploration` skill that consumers can invoke → Highlights written (two bullets: the exploration method and tool-output-stays-data). Test `test_the_generator_projects_the_real_changelog_into_a_valid_payload` passes with the new entry, confirming projection.

### Acceptance-criteria evidence map

| AC | Description (short) | Evidence |
| --- | --- | --- |
| AC-0001 | Question-led | Evals: `lsp-goto-definition`, `lsp-incoming-calls`, `cli-dependency-path`, `mcp-transitive-impact`, `authority-question-native-fallback`, `co-change-question-native-fallback`, `no-provider-baseline`, `poor-fit-provider`, `timed-out-provider`, `malformed-provider-output`, `conflicting-derived-sources`, `bounded-stop-surplus-provider`, `novel-native-action`, `directive-in-tool-description`, `unexposed-config-provider-hint`, `credential-in-provider-output`, `broad-upload-declined`, `outside-root-locator`, `parent-segment-locator`, `unavailable-reader`, `embedded-instruction-in-output`, `proposed-approved-root`, `refresh-and-mutating-request`, `reader-file-text-as-data`; SKILL.md `## Procedure` order test; evidence-record-fields test |
| AC-0002 | Exposed-only discovery | Evals: `unexposed-config-provider-hint`; SKILL.md exposed-surface and no-probe tests |
| AC-0003 | Task fit controls invocation | Evals: `lsp-goto-definition`, `poor-fit-provider`, `timed-out-provider`, `malformed-provider-output`; SKILL.md procedure fit step |
| AC-0004 | Native shapes intact | Evals: `lsp-goto-definition`, `lsp-incoming-calls`, `cli-dependency-path`, `mcp-transitive-impact`; construction test for distinct fixture key sets; SKILL.md no-common-schema and no-preferred-class tests |
| AC-0005 | Deliberate fallback | Evals: `authority-question-native-fallback`, `co-change-question-native-fallback`, `poor-fit-provider`, `timed-out-provider`, `malformed-provider-output`; SKILL.md procedure fallback step |
| AC-0006 | Evidence advisory | Evals: `mcp-transitive-impact`, `conflicting-derived-sources`, `embedded-instruction-in-output`; SKILL.md authoritative-check step |
| AC-0007 | Bounded stopping | Evals: `lsp-goto-definition`, `lsp-incoming-calls`, `cli-dependency-path`, `mcp-transitive-impact`, `authority-question-native-fallback`, `co-change-question-native-fallback`, `no-provider-baseline`, `poor-fit-provider`, `timed-out-provider`, `malformed-provider-output`, `conflicting-derived-sources`, `bounded-stop-surplus-provider`, `novel-native-action`, `directive-in-tool-description`, `unexposed-config-provider-hint`, `credential-in-provider-output`, `broad-upload-declined`, `outside-root-locator`, `parent-segment-locator`, `unavailable-reader`, `embedded-instruction-in-output`, `proposed-approved-root`, `refresh-and-mutating-request`, `reader-file-text-as-data`; SKILL.md `## Procedure` stop step |
| AC-0008 | No consumer ceremony | Pack test `test_exploration_consumer_boundary.py`; recorded architect grep (0 `repository-exploration` hits) |
| AC-0009 | Not a frozen taxonomy | Evals: `novel-native-action`; SKILL.md illustrative-taxonomy test; README pin `test_readme_states_examples_are_illustrative` |
| AC-0010 | Core standalone and portable | Evals: `no-provider-baseline`; seven-surface install check (T3); README pack tests; `catalogue verify` |
| AC-0011 | Minimized disclosure | Evals: `credential-in-provider-output`, `broad-upload-declined`; SKILL.md disclosure section |
| AC-0012 | Locator confinement | Evals: `outside-root-locator`, `parent-segment-locator`, `unavailable-reader`; exploration reader matrix and CLI tests (including `test_cli_ceiling_forwarded_by_main`); grounding caller-ceiling and unchanged-default tests; markers absent from both marker cases |
| AC-0013 | Release pipeline | Release record (T4): 2.28.0 baseline, minor class, both manifests 2.29.0, free-standing changelog entry with Highlights, no Core entry in `.claude-plugin/marketplace.json` |
| AC-0014 | Provider output stays data | Evals: `directive-in-tool-description`, `embedded-instruction-in-output`, `proposed-approved-root`, `refresh-and-mutating-request`, `reader-file-text-as-data`; SKILL.md tests pinning the three `cannot` rules, root sources, and the Ask-first list |

### Reusable-learning disposition

No capture: the run's lessons concern eval-fixture authoring (a directive case needs a tool result to be runnable) and adjudicator format slips from round 1, both of which concern eval tooling and the review loop rather than the exploration skill or its method.

## Post-gates review repair round 1 — behavior-evaluation reruns (2026-10-06)

- **Why.** Review round 1 sustained that AC-0001 and AC-0007 evidence named
  cases that did not grade them, and that five prompts named the graded
  outcome. Every case now carries both checks, and the five prompts state
  only the question, a neutral stopping condition, and the fixtures.
- **Runs.** All 24 cases re-ran once in fresh agent sessions under the same
  procedure as the first round; records are in [`eval-runs.md`](eval-runs.md).
- **Grade.** `agentbundle pack evals run --pack core --mode in-harness --check
  behavior --reports <reports.json>`: `repository-exploration: 24/24 evals
  passed`, exit 0, operator-attested.
- **Map.** The AC evidence map above now uses only `evals.json` case ids and
  lists every case under the criteria it grades.

## Post-gates review repair round 2 (2026-10-06)

- Five sustained Nits (README glosses and plain wording, a merged SKILL.md
  clause, the T2 fixture inventory) were applied by the controller directly,
  not by an implementer. The cohort's decline vocabulary has no
  controller-applied code, so the dispatch record uses `human-directed`.
- Gates on the touched surfaces: README pin and exploration suites 55 passed;
  `make lint-ruff lint-mypy` pass; governance-citation grep 0 hits;
  `make build-self` exit 0.
