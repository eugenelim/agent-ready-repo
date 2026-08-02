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
  declining — that section does not exist. Derivation rule frozen (Phase 0B, per AC10/T4):
  **Legacy-pack gate first** — if `[pack.adapter-contract].version` is absent or `"0.1"`,
  skip `[pack.install]` entirely and use all `contracts/adapter.toml [adapter]` keys
  (sourced from the bundled `_data/adapter.toml` via `importlib.resources` — NOT the
  catalogue-root `contracts/adapter.toml` which is optional/absent in external catalogues).
  Only for non-legacy packs: use `allowed-adapters` list key under `[pack.install]` (read
  as `pack_install.get("allowed-adapters")`) when present; otherwise use all adapter keys.
  A legacy pack that happens to contain `[pack.install][allowed-adapters]` still uses the
  full adapter list — `[pack.install]` is ignored for legacy packs.
- Tempted to add `--no-journey` flag to skip JOURNEY.md parsing; declining — no caller
  needs it yet. A present malformed JOURNEY.md fails the command (fail-closed); the
  correct response is to fix the JOURNEY.md, not bypass the check.

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
# packages/agentbundle/tests/integration/test_catalogue_wave4_journey_validator.py
class TestJourneyValidator:
    def test_all_required_keys_present_returns_journey_data(self):
        raise NotImplementedError  # STUB: AC1
    def test_missing_required_key_returns_none_and_emits_error(self):
        raise NotImplementedError  # STUB: AC3
    def test_journey_absent_returns_empty_array_no_warning(self):
        raise NotImplementedError  # STUB: AC5
    def test_malformed_yaml_fails_index_generation(self):
        raise NotImplementedError  # STUB: AC4
    def test_optional_keys_absent_no_warning(self):
        raise NotImplementedError  # STUB: AC2
    def test_pyyaml_absent_with_no_journey_md_does_not_raise(self):
        # journey_absent → parse_journey_md never imports yaml → no ImportError
        # assert: (None, []) returned without attempting yaml import
        raise NotImplementedError  # STUB: AC4
    def test_pyyaml_absent_with_present_journey_md_emits_error(self):
        # journey file exists; monkeypatch import yaml to raise ImportError
        # assert: (None, [error_message]) returned with install instruction
        raise NotImplementedError  # STUB: AC4
```

**Approach:**

Write `journey_validator.py` exporting:
- `REQUIRED_KEYS: frozenset[str]` — the AC1 required frontmatter keys:
  `{"journey_id", "pack", "start_state", "end_state", "scope", "tagline", "contract"}`
- `CONTRACT_REQUIRED_KEYS: frozenset[str]` — required sub-keys of `contract`:
  `{"useItWhen", "youProvide", "youReceive", "yourDecisions"}`
- `parse_journey_md(path: Path) -> tuple[dict | None, list[str]]` — reads a JOURNEY.md
  file. Returns `(frontmatter_dict, errors)`. Rules:
  - File absent → `(None, [])` (caller maps None to empty journeys array, no error)
  - File present, valid YAML with all required keys → `(data, [])`
  - File present, valid YAML, missing required key → `(None, [error_message])`
  - File present, invalid YAML → `(None, [error_message])`
  - File present, optional keys absent → `(data, [])` (not an error condition)
  The command handler treats any non-empty errors list as a fail-closed condition:
  exit 1, no output file written, structured diagnostic emitted (AC6).
  - Extracts only the YAML frontmatter block (content between leading `---` delimiters);
    does not parse JOURNEY.md body markdown.

Use `PyYAML` via the `agentbundle[lint]` optional extra for YAML parsing (Option B, frozen at Phase 0B). PyYAML is NOT in agentbundle's base dependencies — it is in the `lint` optional extra only. Import PyYAML lazily: attempt `import yaml` only inside `parse_journey_md`, not at module load time. If a JOURNEY.md file is absent, `parse_journey_md` is never called and PyYAML is never imported — the command exits 0 without requiring the lint extra. If a JOURNEY.md file is present and PyYAML is unavailable (`import yaml` raises `ImportError`), return `(None, ["PyYAML required — install agentbundle[lint]"])`, which triggers the fail-closed exit-1 path in the command handler. No new top-level runtime dependency is added.

**Done when:** red-green cycle passes; `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_wave4_journey_validator.py -q` exits 0.

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
  effect-declaration objects. `content` is an optional object with sub-fields
  `skills`, `agents`, `commands`, `scripts`, `hooks`, `seeds`, `shared-libs`, `user-libs` (each an optional array
  of strings). `execution` is an optional array of strings (automatic-execution
  surface names). These two fields are distinct from `effects` (author-declared).
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
- `packages/agentbundle/tests/integration/test_catalogue_wave4_index_generator.py` (stubs; T7 fills)

**Tests (write red stubs before generator code):**
```python
class TestGenerateIndex:
    def test_output_validates_against_schema(self, tmp_path):
        raise NotImplementedError  # STUB: AC13
    def test_deterministic_without_timestamp(self, tmp_path):
        raise NotImplementedError  # STUB: AC16
    def test_generated_at_absent_by_default(self, tmp_path):
        raise NotImplementedError  # STUB: AC15
    def test_source_date_epoch_sets_generated_at(self, tmp_path):
        raise NotImplementedError  # STUB: AC15
    def test_generated_at_flag_overrides_env(self, tmp_path):
        raise NotImplementedError  # STUB: AC15
```
(Full fixture tests filled in T7.)

**Approach:**

`index_generator.py` exports `generate_index(catalogue_root: Path, generated_at: str | None) -> dict`.

**Symlink confinement (applies to ALL reads and scans in this algorithm):**
- **Directory walks:** check `entry.is_symlink()` before descending or including any entry;
  silently exclude symlinks.
- **Direct file reads (steps 1-3):** before calling `open()` on any constructed path
  (`catalogue.toml`, `packs/<name>/pack.toml`, `packs/<name>/JOURNEY.md`,
  `profiles/*.toml`), call `path.is_symlink()` and treat the file as absent if it is a
  symlink — do NOT dereference. `path.is_symlink()` alone is the correct guard; do not
  call `path.resolve()`, which dereferences. A symlink could escape `CATALOGUE_ROOT`
  into arbitrary filesystem paths (AC20 / spec.md:335-336).

Algorithm:
1. Read `catalogue.toml` from root (symlink check first). Extract `[catalogue].name`
   (required) and `[catalogue].description` (optional).
2. Enumerate `packs/*/pack.toml`. For each pack (symlink check before reading pack.toml):
   - Extract required fields: `name`, `version`, `scope`.
   - Extract optional fields: `description`, `categories`.
   - Derive `adapters` via the same contract-version-aware logic as
     `_profile_pack_allowed_adapters` (frozen rule, Phase 0B / AC10):
     1. Check for contract version via
        `pack_data.get("pack", {}).get("adapter-contract", {}).get("version")`
        (the `[pack.adapter-contract].version` field in `pack.toml`). The parsed TOML
        nests `adapter-contract` under the `pack` table — use the two-level lookup;
        the existing helper uses `pack_toml.get("pack", {}).get("adapter-contract")`
        as the canonical pattern.
     2. If contract version is absent or `"0.1"` (legacy pack): emit the full adapter set
        from the **bundled** `_data/adapter.toml [adapter]` keys (loaded via
        `importlib.resources` — the same source existing catalogue tooling uses). Do NOT
        read from the catalogue root's `contracts/adapter.toml` — that file is optional
        and absent in external catalogues created by `catalogue init`. The installer
        ignores `[pack.install]` for legacy packs; the index must match.
     3. If contract version is present and not `"0.1"`: read `allowed-adapters` from
        `pack_data.get("pack", {}).get("install", {}).get("allowed-adapters", [])` —
        `[pack.install]` is nested under the `pack` top-level key, NOT at the root of the
        parsed dict; use that subset if non-empty, otherwise emit all `_data/adapter.toml`
        keys. Do NOT use a standalone `contract_version` field — the canonical field is
        `[pack.adapter-contract].version`.
        **Validate the subset:** for each string in `allowed-adapters`, verify it is a key in
        the bundled `_data/adapter.toml [adapter]` section. An unknown or misspelled entry
        (e.g. `"claude"` instead of `"claude-code"`) must cause exit 1 with a diagnostic naming
        the unrecognized value — do NOT publish it; `catalogue index` does not invoke the
        verifier, so this is the only guard against false adapter advertisement.
   - Extract `integrations` from `[[pack.integrations]]` entries; emit empty array
     if absent.
   - Build `integrations_inverse` by scanning all packs.
   - Call `parse_journey_md(packs/<name>/JOURNEY.md)` (symlink check before reading). Map
     result to `journeys` and `effects` (author-declared); exit 1 if the validator returns
     errors (fail-closed per AC6 — missing required keys or malformed YAML are errors).
   - Build `content` by scanning canonical pack source directories: enumerate
     `.apm/skills/` → skills (skill subdirectory names), `.apm/agents/` → agents,
     `.apm/commands/` → commands, `.apm/hooks/` → hooks, `seeds/` → seeds,
     `.apm/shared-libs/` → `shared-libs` (immediate entry names — files OR subdirectories;
     e.g. `credential-brokers` ships direct `.py` files there, not only subdirs;
     omit sub-field if absent or empty),
     `.apm/user-libs/` → `user-libs` (immediate entry names — files OR subdirectories;
     omit sub-field if absent or empty). For
     `scripts`: enumerate each skill's `scripts/` subdirectory
     (`.apm/skills/<skill>/scripts/`) since scripts live per-skill, not at pack root;
     collect relative paths. **Exclude known cache and temp artifacts from all directory
     scans by name**, NOT by the hidden-file heuristic (do NOT skip all paths starting
     with `.` — authored dotfiles like `seeds/.gitignore` and `seeds/.gitkeep` are real
     distributed source that must be included per the canonical pack layout). The
     exclusion set is: exact directory/file names `{__pycache__, .cache, .DS_Store,
     .pytest_cache, .mypy_cache, .ruff_cache}` and suffixes `{.pyc, .pyo, .pyd,
     .tmp, .swp}`. Skip any path whose name exactly matches an excluded name or whose
     suffix is in the excluded suffix set. This list must be maintained as source code
     evolves — when new tool caches appear, add them. This applies to the scripts scan and all recursive traversals — two
     checkouts of the same source must produce identical `content.scripts` arrays
     regardless of whether `__pycache__/` is populated locally (AC16/AC17). Omit a
     sub-field when the corresponding directory is absent or empty (after exclusion) in
     all skill directories. **Sort every scan-derived sub-array by normalized name or relative
     path** (e.g., `sorted(scripts)`, `sorted(script_paths)`) — directory enumeration
     order is not stable across filesystems; unsorted arrays produce non-deterministic
     bytes and violate AC16.
   - Build `execution` by scanning: `.apm/hook-wiring/` entries, `.apm/kiro-ide-hooks/`
     entries, and `.apm/adapter-root-bins/*.py` files (the canonical adapter-root execution
     surface per `contracts/adapter.toml:148-157`; tracked as mode `100644` not executable,
     so do NOT filter by permission bits — enumerate by directory name and `.py` extension).
     Exclude non-source markers (e.g., `__init__.py`, `__pycache__/`). **Also exclude files
     whose stem starts with `_`** — Python convention for private/helper modules (e.g.
     `credential-brokers` ships `_sso_credman_windows.py` and `_sso_keychain_macos.py` as
     imports of `sso-broker.py`; they are NOT entry points and must not appear in `execution`).
     **Sort the resulting array by normalized entry name.** Emit empty array when no automatic-
     execution surfaces are found.
   - Compute `digest` per AC17 algorithm.
3. Enumerate `profiles/*.toml`. For each profile:
   - Extract `name` (filename stem), `scope`, optional `description`.
4. Assemble index dict: sort packs by name, profiles by name.
5. Set `generated_at` if and only if `generated_at` arg is not None.
6. Validate the assembled index dict against `catalogue-index.schema.json` using
   `agentbundle.build.validate.validate` (stdlib-only subset validator — no jsonschema
   dependency). Exit 1 on non-empty errors list.
7. Return the assembled dict.

`catalogue_index.py` command handler:
- Resolves output path (default `<CATALOGUE_ROOT>/catalogue-index.json`).
- Determines `generated_at` value:
  1. If `--generated-at` flag is set, **parse and normalize strictly**:
     a. Use regex `r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$'`
        as a structural pre-check (rejects date-only strings and offset-naive timestamps).
     b. Parse with `datetime.datetime.strptime()` or `datetime.fromisoformat()` +
        `.astimezone(datetime.timezone.utc)` to validate calendar fields (rejects
        semantically invalid dates like `2026-99-99T25:61:61Z` which the regex cannot
        catch). Use `datetime.timezone.utc` explicitly — bare `.astimezone()` converts to
        the local timezone, producing host-dependent bytes that violate AC16.
     c. **Normalize to UTC, second precision, `Z` suffix** — strip fractional seconds, convert
        any `+00:00` or other offset to `Z`. This guarantees that `SOURCE_DATE_EPOCH` and
        `--generated-at` produce the same canonical string format, and that the output always
        satisfies AC16's determinism requirement.
     d. If any step fails, exit 1 with a structured diagnostic
        ("generated_at must be a valid RFC 3339 date-time with timezone, e.g. 2026-08-01T00:00:00Z").
     Do NOT pass through as-is: `agentbundle.build.validate.validate` does not implement the
     JSON Schema `format` keyword, so schema validation alone cannot catch invalid timestamps.
     User-input boundary (AGENTS.md §input-validation): validate and normalize at the CLI handler,
     not inside `generate_index()`.
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

**Done when:**
```python
# Run against ALL packs that have JOURNEY.md (AC26: "All packs that have JOURNEY.md files")
# Not a hardcoded list — enumerate dynamically so new packs are auto-covered:
python3 -c "
from agentbundle.catalogue_tooling.journey_validator import parse_journey_md
from pathlib import Path
failed = []
for journey in sorted(Path('packs').glob('*/JOURNEY.md')):
    data, errors = parse_journey_md(journey)
    if errors:
        failed.append((journey, errors))
        print(f'FAIL {journey}: {errors}')
    else:
        print(f'OK   {journey}')
if failed:
    raise SystemExit(f'{len(failed)} pack(s) failed JOURNEY.md validation')
print('All JOURNEY.md files pass.')
"
```
Each JOURNEY.md that exists must parse with an empty errors list.  The four packs named
in AC23–AC25 (core, governance-extras, desk-research, architect) must appear in the output
and pass; any additional packs with JOURNEY.md files must also pass.

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
- `packages/agentbundle/tests/integration/test_catalogue_wave4_journey_validator.py` (flesh out stubs from T1)
- `packages/agentbundle/tests/integration/test_catalogue_wave4_index_generator.py` (new)

**Tests:**

```python
# test_catalogue_wave4_journey_validator.py (already written as stubs in T1 — fill assertions)
class TestParseJourneyMd:
    def test_all_required_keys_present(self, tmp_path):
        # write fixture JOURNEY.md with all AC1 required keys
        # assert returns (data_dict, [])
        raise NotImplementedError  # STUB: AC1
    def test_missing_required_key_emits_error(self, tmp_path):
        # write fixture JOURNEY.md missing one required key
        # assert returns (None, [error_message])
        raise NotImplementedError  # STUB: AC3
    def test_journey_absent_returns_none_no_warning(self, tmp_path):
        # file does not exist
        # assert returns (None, [])
        raise NotImplementedError  # STUB: AC5
    def test_malformed_yaml_returns_none_emits_error(self, tmp_path):
        # write fixture with invalid YAML in frontmatter
        # assert returns (None, [error_message])
        raise NotImplementedError  # STUB: AC4
    def test_optional_keys_absent_no_warning(self, tmp_path):
        # write fixture with only required keys (no optional keys)
        # assert returns (data_dict, [])
        raise NotImplementedError  # STUB: AC2

# test_catalogue_wave4_index_generator.py
class TestGenerateIndex:
    def test_two_pack_fixture_produces_valid_index(self, tmp_path):
        # fixture catalogue: two packs (one with JOURNEY.md, one without), one profile
        # assert: output parses as JSON; validates against catalogue-index.schema.json;
        # pack with JOURNEY.md has non-empty journeys; pack without has empty journeys;
        # profile entry present; digest fields are non-empty strings;
        # pack with .apm/skills/ has non-empty content.skills list;
        # pack with .apm/hook-wiring/ has non-empty execution list
        raise NotImplementedError  # STUB: AC13
    def test_deterministic_with_source_date_epoch(self, tmp_path):
        # run generate_index twice with same SOURCE_DATE_EPOCH
        # assert outputs are byte-identical
        raise NotImplementedError  # STUB: AC16
    def test_deterministic_without_timestamp(self, tmp_path):
        # run generate_index twice with no timestamp
        # assert outputs are byte-identical AND generated_at absent
        raise NotImplementedError  # STUB: AC16
    def test_invalid_pack_toml_exits_1(self, tmp_path):
        # fixture catalogue with malformed pack.toml
        # assert ValueError or SystemExit(1)
        raise NotImplementedError  # STUB: AC6
    def test_content_arrays_sorted_regardless_of_scan_order(self, tmp_path):
        # fixture pack with multiple skills created in non-alphabetical order
        # run generate_index twice using different creation order for same skills
        # assert content.skills list is alphabetically sorted in both outputs
        # (validates that sort is applied post-scan, not relying on os enumeration order)
        raise NotImplementedError  # STUB: AC16
    def test_cache_artifacts_excluded_from_content_scripts_and_digest(self, tmp_path):
        # fixture: pack with a script file, then add __pycache__/foo.pyc AND .cache/result
        # Step 1: generate index WITHOUT cache artifacts → record digest_before
        # Step 2: add __pycache__/foo.pyc and .cache/result to fixture
        # Step 3: generate index WITH cache artifacts → record digest_after
        # assert content.scripts does NOT include __pycache__, .pyc, or .cache entries
        # assert digest_before == digest_after (cache files must not affect pack digest)
        # (AC16/AC17: two checkouts with identical source but different cache state must
        # produce byte-identical index; asserting only content.scripts is insufficient —
        # cache could still pollute the digest without appearing in content.scripts)
        raise NotImplementedError  # STUB: AC16
    def test_authored_dotfiles_included_in_content_seeds(self, tmp_path):
        # fixture pack with seeds/.gitignore present (canonical pack layout ships this)
        # run generate_index against fixture
        # assert content.seeds INCLUDES '.gitignore' (authored dotfile is real source)
        # validates that exclusion is by known artifact names, not by hidden-file heuristic
        raise NotImplementedError  # STUB: AC10
    def test_shared_libs_direct_files_indexed(self, tmp_path):
        # fixture pack with .apm/shared-libs/ containing direct .py files (no subdirectory),
        # mirroring the credential-brokers layout (credentials_shim.py etc.)
        # run generate_index against fixture
        # assert content.shared-libs INCLUDES the file names (not empty despite no subdirs)
        # validates that shared-libs scan enumerates immediate entries, not only subdirectories
        raise NotImplementedError  # STUB: AC10
    def test_underscore_prefix_modules_excluded_from_execution(self, tmp_path):
        # fixture pack with .apm/adapter-root-bins/ containing:
        #   sso-broker.py (entry point), _helper.py (private module, underscore prefix)
        # run generate_index against fixture
        # assert execution INCLUDES 'sso-broker.py' but NOT '_helper.py'
        # validates that underscore-prefix files are excluded from execution inventory
        # (mirroring credential-brokers: _sso_credman_windows.py is imported, not executed)
        raise NotImplementedError  # STUB: AC10
    @pytest.mark.skipif(
        os.name == "nt" and not _can_create_symlinks(),
        reason="requires symlink privileges (Windows: Developer Mode or elevated prompt)",
    )
    def test_symlink_escape_excluded_from_content(self, tmp_path):
        # fixture pack with .apm/skills/ containing a symlink to a directory outside the pack
        # run generate_index against fixture
        # assert content.skills does NOT include the symlink entry or any target contents
        # validates that symlinks are silently excluded without dereferencing (AC20/spec:335-336)
        # _can_create_symlinks(): try os.symlink on a temp path; return bool; catch OSError
        raise NotImplementedError  # STUB: AC20
    @pytest.mark.skipif(
        os.name == "nt" and not _can_create_symlinks(),
        reason="requires symlink privileges (Windows: Developer Mode or elevated prompt)",
    )
    def test_symlink_pack_toml_treated_as_absent(self, tmp_path):
        # fixture: packs/<name>/pack.toml is a symlink to a valid pack.toml outside the catalogue
        # run generate_index against the catalogue root
        # assert the pack is treated as missing (skipped), not as a valid pack
        # validates direct-file-read confinement: is_symlink() is checked before open()
        # (AC20 / spec.md:335-336; companion to test_symlink_escape_excluded_from_content)
        raise NotImplementedError  # STUB: AC20
    def test_unknown_allowed_adapter_exits_1(self, tmp_path):
        # fixture non-legacy pack with allowed-adapters = ["claude"]  # invalid; correct is "claude-code"
        # assert generate_index raises SystemExit(1) and diagnostic names the unknown value
        # validates that allowed-adapters subset is validated against bundled adapter keys
        raise NotImplementedError  # STUB: AC12
```

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_wave4_journey_validator.py packages/agentbundle/tests/integration/test_catalogue_wave4_index_generator.py -q` exits 0.

---

## T8 — Tests: schema + parity

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/tests/integration/test_catalogue_wave4_schema.py` (new)

**Tests:**

```python
class TestCatalogueIndexSchema:
    def test_schema_parses_as_valid_json(self):
        # load contracts/catalogue-index.schema.json
        # assert json.loads() succeeds without exception
        raise NotImplementedError  # STUB: AC13
    def test_normative_fields_only_fixture_validates(self):
        # fixture: minimal index with only required fields
        # assert agentbundle.build.validate.validate() returns empty list (no errors)
        raise NotImplementedError  # STUB: AC13
    def test_full_fields_fixture_validates(self):
        # fixture: index with all optional fields populated
        # assert agentbundle.build.validate.validate() returns empty list (no errors)
        raise NotImplementedError  # STUB: AC13
    def test_missing_schema_version_fails_validation(self):
        # fixture: index missing schema_version
        # assert agentbundle.build.validate.validate() returns non-empty errors list
        raise NotImplementedError  # STUB: AC13
    def test_contracts_and_data_copies_byte_identical(self):
        # read contracts/catalogue-index.schema.json
        # read packages/agentbundle/agentbundle/_data/catalogue-index.schema.json
        # assert bytes are identical
        raise NotImplementedError  # STUB: AC13
```

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_wave4_schema.py -q` exits 0.

---

## T9 — Tests: integration test fixture (AC22 two-pack fixture)

**Verification mode:** TDD

**Touches:**
- `packages/agentbundle/tests/fixtures/catalogue_wave4/catalogue.toml` (new)
- `packages/agentbundle/tests/fixtures/catalogue_wave4/packs/pack-with-journey/pack.toml` (new)
- `packages/agentbundle/tests/fixtures/catalogue_wave4/packs/pack-with-journey/JOURNEY.md` (new)
- `packages/agentbundle/tests/fixtures/catalogue_wave4/packs/pack-without-journey/pack.toml` (new)
- `packages/agentbundle/tests/fixtures/catalogue_wave4/profiles/test-profile.toml` (new)
- `packages/agentbundle/tests/integration/test_catalogue_wave4_integration.py` (new)

**Tests:**

```python
FIXTURE_DIR = Path(__file__).parent.parent / "fixtures" / "catalogue_wave4"

class TestCatalogueIndexCommand:
    def test_dry_run_exits_0_no_file_written(self, tmp_path):
        # run agentbundle catalogue index FIXTURE_DIR --dry-run
        # assert exit 0; assert no catalogue-index.json written
        raise NotImplementedError  # STUB: AC14
    def test_output_file_written_and_validates(self, tmp_path):
        # run agentbundle catalogue index FIXTURE_DIR --output <tmp_path/ci.json>
        # assert exit 0; file exists; parses as JSON; validates against schema
        raise NotImplementedError  # STUB: AC13
    def test_pack_with_journey_has_nonempty_journeys(self, tmp_path):
        # pack-with-journey has JOURNEY.md with all required keys → non-empty journeys
        raise NotImplementedError  # STUB: AC7
    def test_pack_without_journey_has_empty_journeys(self, tmp_path):
        # pack-without-journey has no JOURNEY.md → journeys: []
        raise NotImplementedError  # STUB: AC5
    def test_profile_present_in_output(self, tmp_path):
        # fixture has one profile → profile entry present in output profiles array
        raise NotImplementedError  # STUB: AC11
    def test_output_is_deterministic(self, tmp_path):
        # run twice against fixture, no timestamp flag → byte-identical output
        raise NotImplementedError  # STUB: AC16
    def test_nonexistent_root_exits_nonzero(self):
        # run agentbundle catalogue index /nonexistent-path
        # assert exit 1 or 2
        raise NotImplementedError  # STUB: AC19
    def test_malformed_journey_exits_1_no_output_file(self, tmp_path):
        # Write a fresh minimal catalogue in tmp_path with one pack containing a JOURNEY.md
        # whose YAML frontmatter is invalid (e.g., unclosed quote or bad indent).
        # Do NOT use FIXTURE_DIR (it contains valid content — don't modify it).
        # run: agentbundle catalogue index <tmp_path/catalogue> --output <tmp_path/ci.json>
        # assert exit 1; assert ci.json does NOT exist
        raise NotImplementedError  # STUB: AC4
    def test_missing_required_journey_key_exits_1_no_output_file(self, tmp_path):
        # Write a fresh minimal catalogue in tmp_path with one pack containing a JOURNEY.md
        # that has valid YAML but is missing one required key (e.g., journey_id absent).
        # Do NOT use FIXTURE_DIR.
        # assert exit 1; assert no output file written
        raise NotImplementedError  # STUB: AC3
    def test_invalid_generated_at_exits_1(self, tmp_path):
        # run: agentbundle catalogue index FIXTURE_DIR --generated-at "not-a-date" --output <tmp_path/ci.json>
        # assert exit 1 (explicit parse failure before schema validation)
        # assert ci.json does NOT exist (fail-closed — partial output must not be written)
        # validates that as-is passthrough is not used: agentbundle.build.validate.validate
        # does not implement JSON Schema `format`, so schema validation alone cannot catch this
        raise NotImplementedError  # STUB: AC15
    def test_date_only_generated_at_exits_1(self, tmp_path):
        # run: agentbundle catalogue index FIXTURE_DIR --generated-at "2026-08-01" --output <tmp_path/ci.json>
        # assert exit 1 — date-only is NOT a valid date-time (JSON Schema `date-time` requires
        # time component and timezone); datetime.fromisoformat() accepts it but RFC 3339 rejects it
        raise NotImplementedError  # STUB: AC15
    def test_offset_naive_generated_at_exits_1(self, tmp_path):
        # run: agentbundle catalogue index FIXTURE_DIR --generated-at "2026-08-01T12:00:00" --output <tmp_path/ci.json>
        # assert exit 1 — offset-naive timestamp lacks timezone; RFC 3339 requires timezone offset or Z
        raise NotImplementedError  # STUB: AC15
    def test_non_utc_offset_normalized_to_utc(self, tmp_path):
        # run: agentbundle catalogue index FIXTURE_DIR
        #      --generated-at "2026-08-01T17:30:00+05:30" --output <tmp_path/ci.json>
        # assert exit 0; load output; assert generated_at == "2026-08-01T12:00:00Z"
        # (validates .astimezone(datetime.timezone.utc), not bare .astimezone() which
        # converts to local timezone and produces host-dependent bytes — AC16)
        raise NotImplementedError  # STUB: AC16
    def test_adapter_root_bins_in_execution(self, tmp_path):
        # build fixture pack with .apm/adapter-root-bins/my-adapter.py
        # run catalogue index against fixture
        # assert 'my-adapter.py' appears in pack's execution array
        # validates that .apm/adapter-root-bins/ is enumerated by directory name (not permission bits)
        raise NotImplementedError  # STUB: AC10
    def test_legacy_v01_pack_uses_full_adapter_set(self, tmp_path):
        # fixture pack with [pack.install] allowed-adapters = ["claude"] BUT
        # NO [pack.adapter-contract] section (legacy pack, no contract version)
        # → installer ignores [pack.install]; index must emit full adapter set
        # assert adapters contains ALL contracts/adapter.toml keys, not just ["claude"]
        raise NotImplementedError  # STUB: AC12
    def test_non_legacy_pack_uses_allowed_adapters_subset(self, tmp_path):
        # fixture pack with [pack.adapter-contract] version = "1.0" AND
        # [pack.install] allowed-adapters = ["claude-code"]
        # (canonical field is [pack.adapter-contract].version, NOT a standalone contract_version;
        # "claude" is not a key in contracts/adapter.toml — use "claude-code")
        # assert adapters == ["claude-code"] (subset honored for non-legacy packs)
        raise NotImplementedError  # STUB: AC12
```

Fixture is the dedicated two-pack catalogue specified in AC22 (not the live repo root).
Write minimal but valid `pack.toml` and `catalogue.toml` files; include one JOURNEY.md
with all required frontmatter keys from AC1.

**Done when:** `python3 -m pytest packages/agentbundle/tests/integration/test_catalogue_wave4_integration.py -q` exits 0.

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
6. Verify OQ2 compatibility: confirm RFC-0076 OQ2 checkbox is already checked
   (`- [x] OQ2 resolved in Wave 4 spec`) and that the accepted resolution remains
   compatible with the Wave 4 implementation. No RFC mutation is required — OQ2 was
   resolved at spec approval time.
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

- Integration tests (T9) run against the live first-party catalogue. If a JOURNEY.md file
  is malformed at implementation time, T5 (first-party files) must be fixed first.
- `sync_authoring_scaffold.py --check` will fail T6 if the scaffold copy is not updated.
  Run the sync command (not just `--check`) if the check fails.
