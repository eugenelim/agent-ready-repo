# Spec: catalogue-wave3-enterprise-authoring-discovery

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0076 D5](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
- **Contract:** `packages/agentbundle/agentbundle/commands/catalogue_contracts.py` (new), `packages/agentbundle/agentbundle/catalogue_tooling/contracts_inspector.py` (new)
- **Shape:** new CLI surface + init UX update + hub section + tests

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full (structural: new `agentbundle catalogue contracts` CLI surface; public interface:
new subcommand group visible to all agentbundle adopters; RFC-0076 OQ1 resolution required
before implementation; multi-feature: CLI + init update + hub section + tests)

## Objective

Wave 3 implements RFC-0076 D5 — the bundled-contract inspection CLI surface — and
completes the authoring discovery gap for enterprise and air-gapped adopters. After this
wave, any adopter with `agentbundle` installed can enumerate, inspect, and export the
exact contract files their version bundles, without network access. The `agentbundle
catalogue init` success path surfaces the authoring hub path and the new CLI. Hub section
12 documents the three commands so offline readers find them without visiting the source repo.

**OQ1 resolution (RFC-0076):** Wave 3 verifies that `agentbundle catalogue contracts`
does not conflict with ini-005's `catalogue-tooling-rewire` spec. The rewire spec has not
been authored as of this wave. Current registered `agentbundle catalogue` subcommands:
`lint`, `verify`, `build`, `self-host`, `package`, `sync-defaults`, `init`. The
`contracts` subcommand path is not reserved. Wave 3 claims `agentbundle catalogue contracts`
and marks OQ1 resolved in RFC-0076.

## Boundaries

### Always do

- Use `importlib.resources` to locate bundled files — never fall back to filesystem
  discovery of the source `contracts/` directory.
- Keep `contracts/` and `agentbundle/_data/` byte-identical. This wave adds no new
  contracts but must not disturb byte-parity for existing ones. Run
  `python3 tools/catalogue/check_contract_parity.py` before committing.
- Sync `catalogue-authoring-standards.md` to the scaffold after every hub edit.
  Run `python3 tools/catalogue/sync_authoring_scaffold.py --check` before committing.
- Add `Engine-Change-RFC: RFC-0076` to the commit(s) that add the new CLI subcommand.
- Keep the hub content free of host CI workflow requirements, Make target requirements,
  and internal governance citations (RFC/ADR/spec paths).
- Keep packs/AGENTS.md ≤ 150 lines and root AGENTS.md ≤ 250 lines.

### Ask first

- Adding a fourth subcommand to `agentbundle catalogue contracts` beyond `list`, `show`,
  `export`.
- Including `_data/`-only files (`install-defaults.toml`, `install-marker.py`) in the
  `contracts list` output — these are internal defaults, not public machine contracts.
- Including the `catalogue-scaffold/` subdirectory as a contract in `contracts list`.
- Adding `next_steps` to `InitResult` in `results.py` (changing the stable result
  schema for the init command). The Wave 3 approach emits hints directly from the table
  handler; JSON output is unchanged.

### Never do

- Let `export` create symlinks in the output directory — copy regular file bytes only.
- Accept a `contracts show` or `contracts export` name containing path separators
  (`/`, `\`); reject with a clear error.
- Override agentbundle's validation behavior through the `export` command — the exported
  files are reference copies only and this must be printed explicitly.
- Make any network call in `contracts_inspector.py` — importlib.resources is the sole
  source; the module must work air-gapped.
- Cite RFC, ADR, or spec paths in the shipped hub content
  (`catalogue-authoring-standards.md`).
- Edit projected outputs under `.claude-code/`, `.cursor/`, `.kiro/`, etc. directly;
  edit `.apm/` sources then run `catalogue self-host`.
- Exceed the AGENTS.md line caps.

## Testing Strategy

- **OQ1 resolution (AC1):** goal-based — `grep '- \[x\] OQ1 resolved'
  docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md` returns a match
  after T7. Distinct from CLI registration; verified in T7 Done-when, not by `--help`.
- **CLI registration (AC2–AC5):** goal-based — `--help` on the new subcommand group and
  each sub-subcommand exits 0 with the expected flags and positionals visible.
- **Contracts inspector (AC6–AC10):** TDD — `test_catalogue_wave3_contracts_inspector.py`
  unit tests: list count, kind mapping, show returns content for valid name / None for
  invalid, export writes all files with matching content.
- **contracts list output (AC11–AC12):** TDD — `test_catalogue_wave3_contracts_cli.py`
  calls the handler with a namespace; asserts table rows and JSON array structure.
- **contracts show output (AC13–AC14):** TDD — valid name exits 0 with non-empty stdout;
  invalid name exits non-zero.
- **contracts export output (AC15–AC17):** TDD — output directory created; all 11 files
  written; "reference copies only" notice in stderr; symlink target exits 2.
- **Init next-step output (AC18–AC19):** TDD — success table output contains the hub
  path and contracts-list hint; JSON output schema unchanged.
- **Hub section 12 (AC20–AC22):** goal-based — section present; scaffold sync check
  passes; no governance citations.
- **Cold-read + offline navigation (AC23–AC24):** TDD —
  `test_catalogue_wave3_offline_navigation.py`: list → show each → assert non-empty;
  export → compare to show content.
- **Engine change + version (AC25–AC26):** grep confirms version strings; git log
  confirms Engine-Change-RFC footer; grep confirms `0.28.0` or `[Unreleased]` entry
  present in `docs/product/changelog.md` (AC26).
- **Regression (AC27–AC30):** `SKIP_SAST=1 make build-check` and pytest exit 0;
  AGENTS.md line counts pass.

## Acceptance Criteria

### Phase A — OQ1 resolution and CLI registration

- [ ] AC1: RFC-0076 OQ1 is marked resolved. The OQ1 checkbox in
  `docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md` is checked.
  The resolved text states: "`agentbundle catalogue contracts` does not conflict with
  ini-005 `catalogue-tooling-rewire` (spec not yet authored). Wave 3 claims this path."

- [ ] AC2: `agentbundle catalogue contracts --help` exits 0 and lists three
  subcommands: `list`, `show`, `export`.

- [ ] AC3: `agentbundle catalogue contracts list --help` exits 0 and shows a
  `--format` flag accepting `table` (default) and `json`.

- [ ] AC4: `agentbundle catalogue contracts show --help` exits 0 and shows a
  `<name>` positional.

- [ ] AC5: `agentbundle catalogue contracts export --help` exits 0 and shows an
  `--output` flag (required).

### Phase B — Contracts inspector module

- [ ] AC6: `agentbundle.catalogue_tooling.contracts_inspector` exists. It exports:
  - `ContractInfo` — a dataclass with fields `name: str`, `kind: str`, `file: str`.
  - `list_bundled_contracts() -> list[ContractInfo]`
  - `show_contract(name: str) -> str | None`
  - `export_contracts(output_dir: Path) -> list[str]`

- [ ] AC7: `list_bundled_contracts()` returns exactly 11 entries — one for each file
  present in both `contracts/` and `agentbundle/_data/`. The 11 names are:
  `adapter.schema.json`, `adapter.toml`, `catalogue.schema.json`, `guide.schema.json`,
  `pack.schema.json`, `plugin-manifest.derived.schema.json`,
  `plugin-manifest.schema.json`, `profile.schema.json`, `skill-manifest.schema.json`,
  `skill.schema.json`, `target-vocab.toml`. The `install-defaults.toml` file and the
  `catalogue-scaffold/` subdirectory are not included. Each `ContractInfo.kind` is
  `"json-schema"` for `*.schema.json` files and `"toml"` for `*.toml` files.

- [ ] AC8: `show_contract(name)` returns the full UTF-8 string content of the named
  bundled file when `name` is one of the 11 public contract names. Returns `None` when
  `name` is not in the known set. `show_contract` with a name containing `/` or `\`
  returns `None` (path-separator rejection, no ValueError).

- [ ] AC9: `export_contracts(output_dir)` creates `output_dir` if absent; copies each
  bundled contract's bytes to `output_dir / contract.file`; returns the list of relative
  filenames written (same order as `list_bundled_contracts()`). Raises `ValueError`
  if `output_dir` is a symlink (checked via `output_dir.is_symlink()` — lstat, does not
  follow the link — not `output_dir.resolve().is_symlink()`, which always returns False
  after following).

- [ ] AC10: `list_bundled_contracts()`, `show_contract()`, and `export_contracts()` all
  use `importlib.resources` to access bundled files. None depend on the source
  `contracts/` directory being present at runtime.

### Phase C — contracts command handler

- [ ] AC11: `agentbundle catalogue contracts list` (table output, default) prints a
  table with column headers `NAME`, `KIND`, `FILE` and one data row per bundled contract.
  All 11 contracts appear. Exit code 0. Note: RFC-0076 D5's candidate column list
  includes `version`; Wave 3 omits it because bundled contracts carry no uniform version
  field — the agentbundle version (returned by `--version`) is the governing version for
  the entire bundled set.

- [ ] AC12: `agentbundle catalogue contracts list --format json` prints a JSON array
  to stdout where each element has at minimum `"name"`, `"kind"`, `"file"` keys and
  valid string values. Exit code 0.

- [ ] AC13: `agentbundle catalogue contracts show pack.schema.json` prints the full
  content of the bundled `pack.schema.json` to stdout. Exit code 0.

- [ ] AC14: `agentbundle catalogue contracts show nonexistent-name.json` prints a
  one-line error message to stderr naming the unrecognized contract, and exits non-zero
  (exit code 1). No traceback is shown.

- [ ] AC15: `agentbundle catalogue contracts export --output <tmpdir>` creates `<tmpdir>`,
  writes all 11 contract files into it (one file per contract), and prints a file manifest
  to stdout listing each written filename. Exit code 0.

- [ ] AC16: `agentbundle catalogue contracts export --output <tmpdir>` prints the
  following notice to stderr (exact phrase match for the core sentence):
  "These are reference copies only. They do not override the contracts used for
  validation by this agentbundle version."

- [ ] AC17: `agentbundle catalogue contracts export --output <symlink-path>` where
  `<symlink-path>` resolves to a symlink exits with code 2 and a clear error message
  to stderr. No files are written.

### Phase D — Init command next-step output

- [ ] AC18: `agentbundle catalogue init <target>` (table output) on success emits a
  "Next steps:" block containing at minimum:
  - A reference to `guides/_shared/reference/catalogue-authoring-standards.md` (the
    authoring hub, scaffolded into the new catalogue).
  - The hint `agentbundle catalogue contracts list` to view bundled contract schemas.

- [ ] AC19: `agentbundle catalogue init <target> --format json` output is unchanged —
  the JSON schema for `InitResult` is not modified by this wave. No `next_steps` key
  is added to the JSON output.

### Phase E — Hub section 12 and scaffold sync

- [ ] AC20: `guides/_shared/reference/catalogue-authoring-standards.md` gains section
  "12. Bundled contract inspection" (after section 11). The section includes:
  - A statement that bundled contracts can be listed, inspected, and exported without
    network access using the running agentbundle version.
  - A code snippet showing all three commands:
    `agentbundle catalogue contracts list`, `agentbundle catalogue contracts show <name>`,
    `agentbundle catalogue contracts export --output <dir>`.
  - The "reference copies only" notice inline.
  - No RFC, ADR, or spec path citations.

- [ ] AC21: `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0 after
  the hub update. The scaffold copy at
  `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md`
  matches the updated live file.

- [ ] AC22: The updated hub section 12 contains no host CI workflow requirements, Make
  target requirements, or internal governance citations.

### Phase F — Cold-read and offline navigation

- [ ] AC23: A pytest test in `test_catalogue_wave3_offline_navigation.py` exercises the
  full cold-read path: calls `list_bundled_contracts()`, then calls `show_contract(name)`
  for every returned `ContractInfo.name`, and asserts that every call returns a non-None,
  non-empty string. The test does not make network requests (stdlib `socket` is not
  opened during the test run, verified by the test).

- [ ] AC24: A pytest test in `test_catalogue_wave3_offline_navigation.py` calls
  `export_contracts(tmp_path)` and asserts: (a) exactly 11 files are written;
  (b) each written file's byte content matches the corresponding `show_contract(name)`
  return value encoded as UTF-8; (c) no symlinks exist in `tmp_path`.

### Phase G — Engine change, version, changelog, regression

- [ ] AC25: `packages/agentbundle/pyproject.toml` version is bumped to `0.28.0`.
  `packages/agentbundle/agentbundle/version.py` `CLI_VERSION` is set to `"0.28.0"` in
  lockstep. At least one commit in the PR contains `Engine-Change-RFC: RFC-0076` in
  its message.

- [ ] AC26: `docs/product/changelog.md` has an `[Unreleased]` or `0.28.0` entry
  describing: (a) the new `agentbundle catalogue contracts` CLI surface (`list`, `show`,
  `export`); (b) the `catalogue init` next-step guidance addition; (c) hub section 12.

### Regression

- [ ] AC27: `SKIP_SAST=1 make build-check` exits 0 after all changes.
- [ ] AC28: `python3 -m pytest packages/agentbundle/tests/ -q` exits 0 after all changes.
- [ ] AC29: `wc -l packs/AGENTS.md` ≤ 150.
- [ ] AC30: `wc -l AGENTS.md` ≤ 250.

## Assumptions

- **Technical:** `agentbundle catalogue contracts` is not reserved by ini-005's
  `catalogue-tooling-rewire` spec (verified: spec not yet authored at time of this wave;
  current registered `agentbundle catalogue` subcommands do not include `contracts`).
- **Technical:** Nested subparsers within `agentbundle catalogue contracts` are
  supported by the existing argparse wiring (verified: `oplog` uses the same three-level
  pattern in `cli.py`).
- **Technical:** `importlib.resources` can enumerate and read all files in the
  `agentbundle._data` package directory — verified at HEAD: all 11 contract files are
  present in `packages/agentbundle/agentbundle/_data/`.
- **Technical:** Version `0.28.0` is the next minor from `0.27.0` (Wave 2). Verify
  before opening the PR that no other in-flight branch has claimed this version number.
- **Technical:** The 11 public contracts that appear in both `contracts/` and `_data/`
  are: `adapter.schema.json`, `adapter.toml`, `catalogue.schema.json`, `guide.schema.json`,
  `pack.schema.json`, `plugin-manifest.derived.schema.json`, `plugin-manifest.schema.json`,
  `profile.schema.json`, `skill-manifest.schema.json`, `skill.schema.json`,
  `target-vocab.toml`. The `install-defaults.toml` file is `_data/`-only and excluded.
- **Deferred:** Adding a `catalogue contracts check` command that validates a given local
  file against the bundled schema (useful for adopter-local contract validation). Out of
  scope for Wave 3; file under `backlog` if the need surfaces.
- **Deferred:** Surfacing `next_steps` in the `InitResult` JSON output (for consistency
  with `SelfHostedInitResult`). Wave 3 emits hints only in table output; JSON schema is
  unchanged. Tracked as `(deferred: init-result-json-next-steps)` in
  `workspace.toml [backlog].open`.
