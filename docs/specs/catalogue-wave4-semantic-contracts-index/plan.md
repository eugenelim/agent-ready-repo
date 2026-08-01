# Plan: catalogue-wave4-semantic-contracts-index

- **Status:** Drafting
- **Spec:** [`spec.md`](spec.md)

## Mode and declined patterns

Mode: full (new public CLI command `agentbundle catalogue index`; new public contract
`contracts/catalogue-index.schema.json`; new JOURNEY.md pack-level convention; engine
change to `_data/`; multi-phase: schema + CLI + convention + first-party files).

Declined:
- Tempted to write a standalone `contracts/journey.schema.json` JSON Schema for JOURNEY.md
  frontmatter validation; declining — Wave 4 validates required keys programmatically in
  the generator only; formal schema deferred (Assumption 11 in spec).
- Tempted to surface `lifecycle` in the index; declining — `pack.toml` has no `lifecycle`
  field and `pack.schema.json` has no `lifecycle` property; deferred to a follow-on wave
  that amends both schemas together.
- Tempted to emit `catalogue.version` in the index schema; declining — `catalogue.toml`
  has no authoritative version field; version identity is associated during
  `catalogue package`, not index generation.
- Tempted to derive adapters from a `[distribution.agentbundle]` section in pack.toml;
  declining — that section does not exist; derivation comes from `contracts/adapter.toml`
  keys (deferred: exact derivation rule to be confirmed against `catalogue lint` logic).
- Tempted to add `--no-journey` flag to skip JOURNEY.md parsing; declining — no caller
  needs it yet; malformed JOURNEY.md already falls back gracefully (warning, empty array).

## Pre-EXECUTE self-coverage checks

- Domain claim: `agentbundle catalogue index` namespace is unoccupied. Verified: current
  registered `agentbundle catalogue` subcommands are lint, verify, build, self-host,
  package, sync-defaults, init. `index` is not in this list.
- Domain claim: `contracts/catalogue-index.schema.json` does not exist at HEAD. Verified
  by directory listing of `contracts/`.
- Domain claim: existing JOURNEY.md files have all required frontmatter keys (AC1).
  Verified by inspection at spec time: `packs/core/JOURNEY.md`,
  `packs/governance-extras/JOURNEY.md`, `packs/desk-research/JOURNEY.md`,
  `packs/architect/JOURNEY.md` each contain `journey_id`, `pack`, `start_state`,
  `end_state`, `scope`, `tagline`, and `contract` with required sub-keys.
- Domain claim: `check_contract_parity.py` auto-discovers every `*.json`/`*.toml` in
  `contracts/` without modification. Verified: tool uses glob over contracts/; adding
  `catalogue-index.schema.json` is sufficient.
- Resolve-vs-surface: OQ2 (RFC-0076) requires confirming `catalogue index` path is
  unoccupied. Resolved at spec time and recorded in spec.md OQ2 resolution section.

## Task list

```
T1  Journey validator module             Depends on: none
T2  catalogue-index.schema.json          Depends on: none
T3  CLI registration (catalogue index)   Depends on: none
T4  catalogue_index.py generator         Depends on: T1, T2, T3
T5  First-party JOURNEY.md files         Depends on: T1
T6  Authoring hub § "Journey format"     Depends on: none
T7  Tests: JOURNEY.md unit tests         Depends on: T1, T4
T8  Tests: schema + parity               Depends on: T2
T9  Tests: integration test fixture      Depends on: T4
T10 Version, footer, changelog, closeout Depends on: T1–T9
```

Parallel first wave: T1, T2, T3, T6 (all independent).
Second wave (once T1/T2 complete): T5 (needs T1), T8 (needs T2).
Third wave (once T1+T2+T3 complete): T4 (needs T1, T2, T3).

---

## T1 — Journey validator module

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/agentbundle/catalogue_tooling/journey_validator.py` (new)

**Tests:**
```python
# packages/agentbundle/tests/test_catalogue_wave4_journey_validator.py
class TestJourneyValidator:
    def test_all_required_keys_present_returns_journey_data(self): ...
    def test_missing_required_key_returns_none_and_emits_warning(self): ...
    def test_journey_absent_returns_empty_array_no_warning(self): ...
    def test_malformed_yaml_returns_empty_array_emits_warning(self): ...
    def test_optional_keys_absent_no_warning(self): ...
```

**Approach:**

Write `journey_validator.py` exporting:
- `REQUIRED_KEYS: frozenset[str]` — the AC1 required frontmatter keys:
  `{"journey_id", "pack", "start_state", "end_state", "scope", "tagline", "contract"}`
- `CONTRACT_REQUIRED_KEYS: frozenset[str]` — required sub-keys of `contract`:
  `{"useItWhen", "youProvide", "youReceive", "yourDecisions"}`
- `parse_journey_md(path: Path) -> tuple[dict | None, list[str]]` — reads a JOURNEY.md
  file. Returns `(frontmatter_dict, warnings)`. Rules:
  - File absent → `(None, [])` (caller maps None to empty journeys array, no warning)
  - File present, valid YAML with all required keys → `(data, [])`
  - File present, valid YAML, missing required key → `(None, [warning_message])`
  - File present, invalid YAML → `(None, [warning_message])`
  - File present, optional keys absent → `(data, [])` (not a warning condition)
  - Extracts only the YAML frontmatter block (content between leading `---` delimiters);
    does not parse JOURNEY.md body markdown.

Use `PyYAML` (already in agentbundle dependencies) for YAML parsing. No new dependencies.

**Done when:** red-green cycle passes; `python3 -m pytest packages/agentbundle/tests/test_catalogue_wave4_journey_validator.py -q` exits 0.

---

## T2 — `contracts/catalogue-index.schema.json`

**Verification mode:** goal-based

**Touches:**
- `contracts/catalogue-index.schema.json` (new)
- `packages/agentbundle/agentbundle/_data/catalogue-index.schema.json` (new, byte-identical)

**Tests:** none (byte-parity verified in T8; schema validity verified in T8)

**Approach:**

Write `contracts/catalogue-index.schema.json` per AC9–AC11:
- `$schema`: `"https://json-schema.org/draft/2020-12/schema"`
- `title`: `"Catalogue Index"`
- `type`: `"object"`, `additionalProperties: false` at every object level
- Required top-level fields: `schema_version` (string, enum `["1"]`), `catalogue`
  (object), `packs` (array), `profiles` (array)
- Optional top-level field: `generated_at` (string, format `date-time`)
- `catalogue` object: required `name` (string); optional `description` (string); no
  `version` field (omitted per AC9 — no authoritative source)
- `packs` array items: per AC10 required/optional field list. No `lifecycle` field.
  `adapters` is optional array of strings. `journeys` is optional array of
  journey-summary objects per AC10 schema. `effects` is optional array of
  effect-declaration objects.
- `profiles` array items: per AC11. `name` (required, string), `scope` (required,
  string, enum `["user","repo"]`), `description` (optional, string). No `version` field.
- `digest` field in packs items: required string (SHA-256 hex)

After writing `contracts/catalogue-index.schema.json`, byte-copy it to
`packages/agentbundle/agentbundle/_data/catalogue-index.schema.json`.

**Done when:**
- `python3 -c "import json; json.load(open('contracts/catalogue-index.schema.json'))"` exits 0
- `python3 tools/catalogue/check_contract_parity.py` exits 0 (auto-discovers new file)

---

## T3 — CLI registration (`agentbundle catalogue index`)

**Verification mode:** goal-based

**Touches:**
- `packages/agentbundle/agentbundle/cli.py`

**Tests:** none (goal-based)

**Approach:**

Within the existing `# --- catalogue <sub> ---` block in `_build_parser()`, add an `index`
subparser after `init`:

```python
# index
_ci_p = cat_subs.add_parser(
    "index",
    help="Generate a neutral catalogue index from pack.toml and JOURNEY.md files.",
)
_ci_p.add_argument(
    "catalogue_root",
    nargs="?",
    default=".",
    metavar="CATALOGUE_ROOT",
    help="Path to the catalogue root (default: current directory).",
)
_ci_p.add_argument(
    "--output",
    metavar="PATH",
    help="Output file path (default: <CATALOGUE_ROOT>/catalogue-index.json).",
)
_ci_p.add_argument(
    "--format",
    choices=["table", "json"],
    default="table",
    help="Command result output format (does not affect the output file).",
)
_ci_p.add_argument(
    "--dry-run",
    action="store_true",
    help="Validate and generate in memory; write nothing to disk.",
)
_ci_p.add_argument(
    "--generated-at",
    metavar="ISO8601",
    help=(
        "Set generated_at to this ISO 8601 timestamp. Overrides SOURCE_DATE_EPOCH. "
        "When neither this flag nor SOURCE_DATE_EPOCH is set, generated_at is omitted."
    ),
)
_ci_p.set_defaults(func=_lazy("catalogue_index"))
```

**Done when:** `agentbundle catalogue index --help` exits 0 and lists all four flags.

---

## T4 — `catalogue_index.py` generator

**Verification mode:** TDD (deterministic JSON generator with hard byte-determinism,
schema validity, and digest invariants; unit tests gate T4 — T7 fills in fixture tests
that depend on T4, but T4's own core invariants are tested first)

**Touches:**
- `packages/agentbundle/agentbundle/commands/catalogue_index.py` (new)
- `packages/agentbundle/agentbundle/catalogue_tooling/index_generator.py` (new)
- `packages/agentbundle/tests/test_catalogue_wave4_index_generator.py` (stubs; T7 fills)

**Tests (write red stubs before generator code):**
```python
class TestGenerateIndex:
    def test_output_validates_against_schema(self, tmp_path): ...
    def test_deterministic_without_timestamp(self, tmp_path): ...
    def test_generated_at_absent_by_default(self, tmp_path): ...
    def test_source_date_epoch_sets_generated_at(self, tmp_path): ...
    def test_generated_at_flag_overrides_env(self, tmp_path): ...
```
(Full fixture tests filled in T7.)

**Approach:**

`index_generator.py` exports `generate_index(catalogue_root: Path, generated_at: str | None) -> dict`.

Algorithm:
1. Read `catalogue.toml` from root. Extract `[catalogue].name` (required) and
   `[catalogue].description` (optional).
2. Enumerate `packs/*/pack.toml`. For each pack:
   - Extract required fields: `name`, `version`, `scope`.
   - Extract optional fields: `description`, `categories`.
   - Derive `adapters` from `contracts/adapter.toml [adapter]` keys (deferred: confirm
     logic against `catalogue lint` during implementation; emit empty array if uncertain).
   - Extract `integrations` from `[[pack.integrations]]` entries; emit empty array
     if absent.
   - Build `integrations_inverse` by scanning all packs.
   - Call `parse_journey_md(packs/<name>/JOURNEY.md)`. Map result to `journeys` and
     `effects`; emit warnings to stderr via `logging.warning`.
   - Compute `digest` per AC17 algorithm.
3. Enumerate `profiles/*.toml`. For each profile:
   - Extract `name` (filename stem), `scope`, optional `description`.
4. Assemble index dict: sort packs by name, profiles by name.
5. Set `generated_at` if and only if `generated_at` arg is not None.
6. Validate against `catalogue-index.schema.json` using `jsonschema`. Exit 1 on failure.
7. Return the assembled dict.

`catalogue_index.py` command handler:
- Resolves output path (default `<CATALOGUE_ROOT>/catalogue-index.json`).
- Determines `generated_at` value:
  1. If `--generated-at` flag is set, use it as-is.
  2. Else if `SOURCE_DATE_EPOCH` env var is set, convert the Unix integer timestamp
     to an ISO 8601 UTC string (second precision, `Z` suffix).
  3. Else pass `None` → `generated_at` field omitted from output.
- Calls `generate_index(catalogue_root, generated_at)`.
- On `--dry-run`: validates but does not write; prints "Validation passed." to stdout.
- On success: writes JSON (UTF-8, final newline, 2-space indent, sorted keys). Prints
  summary table or JSON result to stdout per `--format`.
- Makes no network requests; does not invoke subprocesses.

**Done when (manual QA):**
```bash
python3 -m agentbundle catalogue index . --dry-run  # exits 0
python3 -m agentbundle catalogue index . --output /tmp/ci.json  # exits 0, file written
python3 -c "import json; d=json.load(open('/tmp/ci.json')); print(len(d['packs']), 'packs')"  # prints N packs
python3 -m agentbundle catalogue index nonexistent-path  # exits 1 or 2
```

---

## T5 — First-party JOURNEY.md files

**Verification mode:** goal-based

**Touches:**
- `packs/core/JOURNEY.md` (verify existing; update if required keys missing)
- `packs/governance-extras/JOURNEY.md` (verify existing; update if required keys missing)
- `packs/desk-research/JOURNEY.md` (verify existing; update if required keys missing)
- `packs/architect/JOURNEY.md` (verify existing; update if required keys missing)

**Tests:** none (verified by T9 integration test — `catalogue index` run against first-party
catalogue exits 0 and all four packs produce non-empty `journeys`)

**Approach:**

For each of the four JOURNEY.md files:
1. Read the YAML frontmatter block.
2. Check all AC1 required keys are present: `journey_id`, `pack`, `start_state`,
   `end_state`, `scope`, `tagline`, `contract` (with sub-keys `useItWhen`, `youProvide`,
   `youReceive`, `yourDecisions`).
3. If any required key is absent, add it with a placeholder value and note in the commit
   message that the field was added for convention conformance.
4. Do not change existing values unless they are structurally incorrect (e.g., wrong type).
5. Apply migration conformance rule (AC5): these files predate the formal convention;
   verify body contains the activation-trigger table and at least two numbered workflow
   steps — do not rename sections.

**Done when:** `python3 -c "from agentbundle.catalogue_tooling.journey_validator import parse_journey_md; from pathlib import Path; [print(k, parse_journey_md(Path(f'packs/{k}/JOURNEY.md'))) for k in ['core','governance-extras','desk-research','architect']]"` shows `(data_dict, [])` for each pack (no warnings).

---

## T6 — Authoring hub § "Journey format"

**Verification mode:** goal-based

**Touches:**
- `guides/_shared/reference/catalogue-authoring-standards.md`
- `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md`
  (kept in sync via `sync_authoring_scaffold.py`)

**Tests:** none (goal-based)

**Approach:**

Locate the "Journey format" section in `catalogue-authoring-standards.md`. Remove the
"not yet available" placeholder. Replace with (per AC27):
1. A one-paragraph summary of the JOURNEY.md convention (one file per pack; YAML
   frontmatter is normative; body markdown is informational).
2. A reference to `packs/<pack>/JOURNEY.md` as the file location.
3. A plain-text (non-hyperlink) reference to `contracts/catalogue-index.schema.json`
   as the machine contract that indexes journey data.
4. A pointer to `agentbundle catalogue index` command for generating the neutral index.

No RFC, ADR, or spec path citations in the guide content. No CI workflow requirements.
No Make target requirements.

After editing: `python3 tools/catalogue/sync_authoring_scaffold.py --check` must exit 0.
If it exits non-zero, copy the guide to the scaffold path manually, then rerun.

**Done when:**
- `grep -q "Journey format" guides/_shared/reference/catalogue-authoring-standards.md` exits 0
- `! grep -qi "not yet available" guides/_shared/reference/catalogue-authoring-standards.md` exits 0
- `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0

---

## T7 — Tests: JOURNEY.md unit tests

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/tests/test_catalogue_wave4_journey_validator.py` (flesh out stubs from T1)
- `packages/agentbundle/tests/test_catalogue_wave4_index_generator.py` (new)

**Tests:**

```python
# test_catalogue_wave4_journey_validator.py (already written as stubs in T1 — fill assertions)
class TestParseJourneyMd:
    def test_all_required_keys_present(self, tmp_path):
        # write fixture JOURNEY.md with all AC1 required keys
        # assert returns (data_dict, [])
        ...
    def test_missing_required_key_emits_warning(self, tmp_path):
        # write fixture JOURNEY.md missing one required key
        # assert returns (None, [warning])
        ...
    def test_journey_absent_returns_none_no_warning(self, tmp_path):
        # file does not exist
        # assert returns (None, [])
        ...
    def test_malformed_yaml_returns_none_emits_warning(self, tmp_path):
        # write fixture with invalid YAML in frontmatter
        # assert returns (None, [warning])
        ...
    def test_optional_keys_absent_no_warning(self, tmp_path):
        # write fixture with only required keys (no optional keys)
        # assert returns (data_dict, [])
        ...

# test_catalogue_wave4_index_generator.py
class TestGenerateIndex:
    def test_two_pack_fixture_produces_valid_index(self, tmp_path):
        # fixture catalogue: two packs (one with JOURNEY.md, one without), one profile
        # assert: output parses as JSON; validates against catalogue-index.schema.json;
        # pack with JOURNEY.md has non-empty journeys; pack without has empty journeys;
        # profile entry present; digest fields are non-empty strings
        ...
    def test_deterministic_with_source_date_epoch(self, tmp_path):
        # run generate_index twice with same SOURCE_DATE_EPOCH
        # assert outputs are byte-identical
        ...
    def test_deterministic_without_timestamp(self, tmp_path):
        # run generate_index twice with no timestamp
        # assert outputs are byte-identical AND generated_at absent
        ...
    def test_invalid_pack_toml_exits_1(self, tmp_path):
        # fixture catalogue with malformed pack.toml
        # assert ValueError or SystemExit(1)
        ...
```

**Done when:** `python3 -m pytest packages/agentbundle/tests/test_catalogue_wave4_journey_validator.py packages/agentbundle/tests/test_catalogue_wave4_index_generator.py -q` exits 0.

---

## T8 — Tests: schema + parity

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/tests/test_catalogue_wave4_schema.py` (new)

**Tests:**

```python
class TestCatalogueIndexSchema:
    def test_schema_parses_as_valid_json(self):
        # load contracts/catalogue-index.schema.json
        # assert json.loads() succeeds without exception
        ...
    def test_normative_fields_only_fixture_validates(self):
        # fixture: minimal index with only required fields
        # assert jsonschema.validate() passes
        ...
    def test_full_fields_fixture_validates(self):
        # fixture: index with all optional fields populated
        # assert jsonschema.validate() passes
        ...
    def test_missing_schema_version_fails_validation(self):
        # fixture: index missing schema_version
        # assert jsonschema.ValidationError raised
        ...
    def test_contracts_and_data_copies_byte_identical(self):
        # read contracts/catalogue-index.schema.json
        # read packages/agentbundle/agentbundle/_data/catalogue-index.schema.json
        # assert bytes are identical
        ...
```

**Done when:** `python3 -m pytest packages/agentbundle/tests/test_catalogue_wave4_schema.py -q` exits 0.

---

## T9 — Tests: integration test fixture (AC22 two-pack fixture)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/tests/fixtures/catalogue_wave4/catalogue.toml` (new)
- `packages/agentbundle/tests/fixtures/catalogue_wave4/packs/pack-with-journey/pack.toml` (new)
- `packages/agentbundle/tests/fixtures/catalogue_wave4/packs/pack-with-journey/JOURNEY.md` (new)
- `packages/agentbundle/tests/fixtures/catalogue_wave4/packs/pack-without-journey/pack.toml` (new)
- `packages/agentbundle/tests/fixtures/catalogue_wave4/profiles/test-profile.toml` (new)
- `packages/agentbundle/tests/test_catalogue_wave4_integration.py` (new)

**Tests:**

```python
FIXTURE_DIR = Path(__file__).parent / "fixtures" / "catalogue_wave4"

class TestCatalogueIndexCommand:
    def test_dry_run_exits_0_no_file_written(self, tmp_path):
        # run agentbundle catalogue index FIXTURE_DIR --dry-run
        # assert exit 0; assert no catalogue-index.json written
        ...
    def test_output_file_written_and_validates(self, tmp_path):
        # run agentbundle catalogue index FIXTURE_DIR --output <tmp_path/ci.json>
        # assert exit 0; file exists; parses as JSON; validates against schema
        ...
    def test_pack_with_journey_has_nonempty_journeys(self, tmp_path):
        # pack-with-journey has JOURNEY.md with all required keys → non-empty journeys
        ...
    def test_pack_without_journey_has_empty_journeys(self, tmp_path):
        # pack-without-journey has no JOURNEY.md → journeys: []
        ...
    def test_profile_present_in_output(self, tmp_path):
        # fixture has one profile → profile entry present in output profiles array
        ...
    def test_output_is_deterministic(self, tmp_path):
        # run twice against fixture, no timestamp flag → byte-identical output
        ...
    def test_nonexistent_root_exits_nonzero(self):
        # run agentbundle catalogue index /nonexistent-path
        # assert exit 1 or 2
        ...
```

Fixture is the dedicated two-pack catalogue specified in AC22 (not the live repo root).
Write minimal but valid `pack.toml` and `catalogue.toml` files; include one JOURNEY.md
with all required frontmatter keys from AC1.

**Done when:** `python3 -m pytest packages/agentbundle/tests/test_catalogue_wave4_integration.py -q` exits 0.

---

## T10 — Version, Engine-Change-RFC, changelog, closeout

**Verification mode:** goal-based

**Touches:**
- `packages/agentbundle/pyproject.toml`
- `packages/agentbundle/agentbundle/version.py`
- `docs/product/changelog.md`
- `docs/specs/catalogue-wave4-semantic-contracts-index/spec.md` (Status: Implementing → Shipped)
- `workspace.toml` (move Wave 4 entry from queue to shipped)

**Tests:** none (goal-based)

**Approach:**

1. Inspect `packages/agentbundle/pyproject.toml` `version` and any open PRs to determine
   the next unclaimed minor version (Wave 2 shipped as `0.27.0`; Wave 3 targets `0.28.0`;
   Wave 4 takes the next after both).
2. Set `version = "<VER>"` in `pyproject.toml`. Set `CLI_VERSION = "<VER>"` in `version.py`.
3. Confirm every commit that modified `agentbundle/_data/` or added the `catalogue index`
   CLI has `Engine-Change-RFC: RFC-0076` in its message. Add to the commit message for
   this task if not yet present.
4. Add `[Unreleased]` or `<VER>` entry to `docs/product/changelog.md` covering:
   - New `agentbundle catalogue index` command
   - `catalogue-index.schema.json` bundled in `_data/`
   - Version bump
   - JOURNEY.md convention formalized
5. Run full gates:
   - `SKIP_SAST=1 make build-check` (exits 0, including `check-contract-parity` for new schema)
   - `python3 -m pytest packages/agentbundle/tests/ -q` (exits 0)
   - `wc -l packs/AGENTS.md` ≤ 150
   - `wc -l AGENTS.md` ≤ 250
6. Mark RFC-0076 OQ2 checkbox checked in `docs/rfc/0076-*.md` (already resolved in spec;
   the checkbox update completes the loop).
7. Update spec.md Status: Shipped.
8. Move Wave 4 entry from `queue` to `shipped` in `workspace.toml` ini-007 work section.
9. Run `python3 tools/lint-ruff.py` and fix any issues.

**Done when:**
- `grep "version" packages/agentbundle/pyproject.toml` shows `<VER>`
- `SKIP_SAST=1 make build-check` exits 0
- `python3 -m pytest packages/agentbundle/tests/ -q` exits 0
- `grep "Engine-Change-RFC: RFC-0076" $(git log --format="%H" HEAD~10..HEAD)` returns at least one commit
- Spec Status shows Shipped

## Constraints

- No production code changes before T1/T2/T3 stubs are written.
- T4 may not start until T1, T2, T3 are complete (generator depends on validator module,
  schema path, and CLI registration for test invocation).
- T5 (first-party JOURNEY.md) may start once T1 is complete.
- T10 must be last; version must not be bumped until all other tasks pass gates.

## Risks

- The `adapters` derivation rule from `contracts/adapter.toml` is underspecified. AC10
  defers exact logic to implementation. If `catalogue lint` adapter validation logic is
  complex, T4 may need to emit an empty array and flag for follow-on — record in PR.
- Integration tests (T9) run against the live first-party catalogue. If a JOURNEY.md file
  is malformed at implementation time, T5 (first-party files) must be fixed first.
- `sync_authoring_scaffold.py --check` will fail T6 if the scaffold copy is not updated.
  Run the sync command (not just `--check`) if the check fails.
