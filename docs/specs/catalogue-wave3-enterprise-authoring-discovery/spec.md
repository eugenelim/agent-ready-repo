# Spec: catalogue-wave3-enterprise-authoring-discovery

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0076 D5](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
- **Contract:** none
- **Shape:** mixed

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
does not conflict with ini-005's surface. Phase 0 reconciliation (2026-07-31) closed
ini-005 as complete: `catalogue-tooling-rewire` was never authored; no spec dir exists;
no `catalogue contracts` subcommand was registered. Current registered `agentbundle
catalogue` subcommands: `lint`, `verify`, `build`, `self-host`, `package`,
`sync-defaults`, `init`. The `contracts` subcommand path is confirmed unoccupied.
Wave 3 claims `agentbundle catalogue contracts` and marks OQ1 resolved in RFC-0076.

## Boundaries

### Always do

- Use `importlib.resources` to locate bundled files — never fall back to filesystem
  discovery of the source `contracts/` directory.
- Keep `contracts/` and `agentbundle/_data/` byte-identical. This wave adds no new
  contracts but must not disturb byte-parity for existing ones. Run
  `python3 tools/catalogue/check_contract_parity.py` before committing.
- Generate the bundled positive inventory from `contracts/` and verify it before
  committing. Run `python3 tools/catalogue/sync_contract_inventory.py --check`.
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

- **OQ1 resolution (AC1):** goal-based — the RFC checkbox remains checked and this
  spec's OQ1 resolution paragraph records the detailed namespace-reconciliation
  evidence. Distinct from CLI registration; verified in T7 Done-when, not by `--help`.
- **CLI registration (AC2–AC5):** goal-based — `--help` on the new subcommand group and
  each sub-subcommand exits 0 with the expected flags and positionals visible.
- **Contracts inspector (AC6–AC10):** TDD — package tests in
  `test_catalogue_wave3_contracts_inspector.py` verify the bundled positive inventory,
  private `_data` exclusion, kind mapping, show behavior, byte-exact export, and
  zero-write unsafe-destination failures. Repo-owned `tools/test_contract_parity.py`
  verifies the generated inventory against canonical `contracts/`, including a stale
  inventory failure, without making the shipped sdist suite depend on checkout files.
- **contracts list output (AC11–AC12):** TDD — `test_catalogue_wave3_contracts_cli.py`
  invokes `agentbundle.cli.main()` with public argv and asserts exact table headers,
  complete rows, and a JSON array whose required values are strings.
- **contracts show output (AC13–AC14):** TDD — public CLI invocation for a valid name
  exits 0 with full content; an invalid name exits 1 with one-line stderr and no traceback.
- **contracts export output (AC15–AC17):** TDD — public CLI invocation creates the
  output directory and all inventory members; exact reference-copy notice is in stderr;
  output and destination link/non-regular failures exit 2 without a traceback or leak.
- **Init next-step output (AC18–AC19):** TDD — success table output contains the hub
  path and contracts-list hint; JSON output schema unchanged.
- **Hub section 12 (AC20–AC22):** goal-based — section present; scaffold sync check
  passes; no governance citations.
- **Cold-read + offline navigation (AC23–AC24):** TDD —
  `test_catalogue_wave3_offline_navigation.py`: list → show each → assert non-empty;
  export → compare to show content.
- **Engine change + version (AC25–AC26):** grep confirms `0.34.0` in both version
  authorities and all three release documents; git log confirms the
  `Engine-Change-RFC: RFC-0076` footer.
- **Regression (AC27–AC30):** `make build-check` (SAST included) and pytest exit 0;
  AGENTS.md line counts pass.

## Acceptance Criteria

### Phase A — OQ1 resolution and CLI registration

- [x] AC1: RFC-0076 OQ1 is marked resolved. The OQ1 checkbox in
  `docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md` is checked.
  This spec's **OQ1 resolution** paragraph records the supporting facts: the namespace
  was unoccupied, ini-005 was complete, `catalogue-tooling-rewire` was never authored,
  and Wave 3 claims the command path.

- [x] AC2: `agentbundle catalogue contracts --help` exits 0 and lists three
  subcommands: `list`, `show`, `export`.

- [x] AC3: `agentbundle catalogue contracts list --help` exits 0 and shows a
  `--format` flag accepting `table` (default) and `json`.

- [x] AC4: `agentbundle catalogue contracts show --help` exits 0 and shows a
  `<name>` positional.

- [x] AC5: `agentbundle catalogue contracts export --help` exits 0 and shows an
  `--output` flag (required).

### Phase B — Contracts inspector module

- [x] AC6: `agentbundle.catalogue_tooling.contracts_inspector` exists. It exports:
  - `ContractInfo` — a dataclass with fields `name: str`, `kind: str`, `file: str`.
  - `list_bundled_contracts() -> list[ContractInfo]`
  - `show_contract(name: str) -> str | None`
  - `export_contracts(output_dir: Path) -> list[str]`
  - `ContractResourceError` — raised when the bundled inventory is missing,
    empty, or malformed, or when a listed resource cannot be read. Load-bearing
    for the CLI's exit-code contract: `list`/`show` map it to exit 1, `export`
    to exit 2.

- [x] AC7: `list_bundled_contracts()` returns exactly the names in a packaged positive
  inventory generated from the canonical `contracts/` directory. Unknown future files
  placed in `agentbundle/_data/` are excluded unless the generated inventory names them;
  `_data/`-only internals and the `catalogue-scaffold/` subtree therefore fail closed.
  The inventory contains every canonical `*.json` and `*.toml` contract and is verified
  by repository tooling, not maintained as a second hand-authored roster. This AC is the
  single canonical statement of the bundled-contract count; other sections reference it
  rather than restating a number that would drift independently. Each
  `ContractInfo.kind` is `"json-schema"` for `*.schema.json` files, `"toml"` for
  `*.toml` files, and `"json"` for any other `*.json` contract. An empty inventory is
  rejected as malformed — it means a truncated build, not a bundle with no contracts.
  The implementation reads only the packaged inventory at runtime; build tooling and
  tests derive the expected inventory from a `contracts/` directory scan rather than a
  frozen count constant.

- [x] AC8: `show_contract(name)` returns the full UTF-8 string content of the named
  bundled file when `name` is one of the public contract names (derived dynamically
  from `list_bundled_contracts()`). Returns `None` when
  `name` is not in the known set. `show_contract` with a name containing `/` or `\`
  returns `None` (path-separator rejection, no ValueError).

- [x] AC9: `export_contracts(output_dir)` creates `output_dir` if absent; copies each
  bundled contract's bytes to `output_dir / contract.file`; returns the list of relative
  filenames written (same order as `list_bundled_contracts()`). Before writing any file,
  it raises `ValueError` if `output_dir` is a symlink or if any existing destination is
  a symlink or non-regular file. The output-directory check uses
  `output_dir.is_symlink()` — lstat, does not follow the link — not
  `output_dir.resolve().is_symlink()`, which always returns False after following.
  Link refusal is scoped to `output_dir` itself and to each destination. A symlinked
  **ancestor** is resolved normally and accepted — `/tmp` is a symlink to `private/tmp`
  on macOS, and a symlinked `$HOME` or checkout is common on Linux, so refusing
  ancestors would break the ordinary AC15 flow on most developer machines.
  After the complete preflight, writes use a repository-owned descriptor-held no-follow
  batch primitive: on POSIX the output-directory descriptor remains open for every
  temporary-file creation and atomic replacement; the portability fallback revalidates
  the output directory before replacement, which is detection rather than prevention
  against a local attacker racing that window. Direct `Path.write_text()` /
  `Path.write_bytes()` writes are forbidden.
  Exported files are written `0o644` — they are reference copies an adopter may place
  in a shared directory, so they must not land unreadable.
  The primitive (`safety.write_files_no_follow`) provides link refusal only and
  performs **no root confinement**, unlike `write_jailed` (ADR-0017,
  `core-path-confinement`). That is sound here because `--output` is operator-supplied,
  not derived from pack or catalogue content; any future caller passing an untrusted
  `output_dir` must `assert_under` a root first.

- [x] AC10: `list_bundled_contracts()`, `show_contract()`, and `export_contracts()` all
  use `importlib.resources` to access bundled files. None depend on the source
  `contracts/` directory being present at runtime.

### Phase C — contracts command handler

- [x] AC11: `agentbundle catalogue contracts list` (table output, default) prints a
  table with column headers `NAME`, `KIND`, `FILE` and one data row per bundled contract.
  All public contracts appear (the AC7 inventory set). Exit code 0. Note: RFC-0076
  D5's candidate column list includes `version`; Wave 3 omits it because bundled
  contracts carry no uniform version field — the agentbundle version (returned by
  `--version`) is the governing version for the entire bundled set.

- [x] AC12: `agentbundle catalogue contracts list --format json` prints a JSON array
  to stdout where each element has at minimum `"name"`, `"kind"`, `"file"` keys and
  valid string values. Exit code 0.

- [x] AC13: `agentbundle catalogue contracts show pack.schema.json` prints the full
  content of the bundled `pack.schema.json` to stdout. Exit code 0.

- [x] AC14: `agentbundle catalogue contracts show nonexistent-name.json` prints a
  one-line error message to stderr naming the unrecognized contract, and exits non-zero
  (exit code 1). No traceback is shown.

- [x] AC15: `agentbundle catalogue contracts export --output <tmpdir>` creates `<tmpdir>`,
  writes every contract returned by `list_bundled_contracts()` into it (one file per
  contract), and prints a file manifest to stdout listing each written filename. Exit
  code 0.

- [x] AC16: `agentbundle catalogue contracts export --output <tmpdir>` prints the
  following notice to stderr (exact phrase match for the core sentence):
  "These are reference copies only. They do not override the contracts used for
  validation by this agentbundle version."

- [x] AC17: `agentbundle catalogue contracts export --output <symlink-path>` where
  `<symlink-path>` resolves to a symlink exits with code 2 and a clear error message
  to stderr. A pre-existing symlink or non-regular file at any contract destination is
  refused the same way. No files are written when preflight fails, and no traceback or
  internal path is exposed. Tests place the unsafe destination after at least one valid
  inventory member and prove that no earlier contract file was created.

### Phase D — Init command next-step output

- [x] AC18: `agentbundle catalogue init <target>` (table output) on success emits a
  "Next steps:" block containing at minimum:
  - A reference to `guides/_shared/reference/catalogue-authoring-standards.md` (the
    authoring hub, scaffolded into the new catalogue).
  - The hint `agentbundle catalogue contracts list` to view bundled contract schemas.

- [x] AC19: `agentbundle catalogue init <target> --format json` output is unchanged —
  the JSON schema for `InitResult` is not modified by this wave. No `next_steps` key
  is added to the JSON output.

### Phase E — Hub section 12 and scaffold sync

- [x] AC20: `guides/_shared/reference/catalogue-authoring-standards.md` gains section
  "12. Bundled contract inspection" (after section 11). The section includes:
  - A statement that bundled contracts can be listed, inspected, and exported without
    network access using the running agentbundle version.
  - A code snippet showing all three commands:
    `agentbundle catalogue contracts list`, `agentbundle catalogue contracts show <name>`,
    `agentbundle catalogue contracts export --output <dir>`.
  - The "reference copies only" notice inline.
  - No RFC, ADR, or spec path citations.

- [x] AC21: `python3 tools/catalogue/sync_authoring_scaffold.py --check` exits 0 after
  the hub update. The scaffold copy at
  `packages/agentbundle/agentbundle/_data/catalogue-scaffold/guides/_shared/reference/catalogue-authoring-standards.md`
  matches the updated live file.

- [x] AC22: The updated hub section 12 contains no host CI workflow requirements, Make
  target requirements, or internal governance citations. An explicit absence check covers
  `.github/workflows`, `make `, `RFC-`, `docs/rfc/`, `ADR`, `docs/adr/`, and `docs/specs/`.

### Phase F — Cold-read and offline navigation

- [x] AC23: A pytest test in `test_catalogue_wave3_offline_navigation.py` exercises the
  full cold-read path: calls `list_bundled_contracts()`, then calls `show_contract(name)`
  for every returned `ContractInfo.name`, and asserts that every call returns a non-None,
  non-empty string. The test does not make network requests (stdlib `socket` is not
  opened during the test run, verified by the test).

- [x] AC24: A pytest test in `test_catalogue_wave3_offline_navigation.py` calls
  `export_contracts(tmp_path)` and asserts: (a) exactly the dynamically listed public
  contracts are written (the AC7 inventory set);
  (b) each written file's byte content matches the corresponding `show_contract(name)`
  return value encoded as UTF-8; (c) no symlinks exist in `tmp_path`.

### Phase G — Engine change, version, changelog, regression

- [x] AC25: `packages/agentbundle/pyproject.toml` version is bumped to the next
  available AgentBundle minor version after inspecting current HEAD at implementation
  time (current HEAD is `0.33.3`; Wave 3 reserves `0.34.0` unless another branch claims
  it before merge). `agentbundle/version.py`
  `CLI_VERSION` is set to match in lockstep. At least one commit in the PR contains
  `Engine-Change-RFC: RFC-0076` in its message. Verified before merge: `main` is still
  at `0.33.3`, so no other in-flight branch claimed `0.34.0`; the footer is carried by
  the commit that adds the CLI subcommand.

- [x] AC26: `packages/agentbundle/CHANGELOG.md` and `docs/product/changelog.md` have
  `0.34.0` entries
  describing: (a) the new `agentbundle catalogue contracts` CLI surface (`list`, `show`,
  `export`); (b) the `catalogue init` next-step guidance addition; (c) hub section 12.
  `packages/agentbundle/README-pypi.md` describes the same new CLI surface and reports
  `0.34.0` in its current-release section.

### Regression

- [x] AC27: `make build-check` exits 0 after all changes, **with the SAST/SCA leg
  included** — not the `SKIP_SAST=1` variant, which prints an explicit INCOMPLETE
  banner. This wave adds filesystem-primitive code under `packages/` and a new
  script under `tools/`, both inside `SAST_DIRS`, so the skipped variant would
  omit exactly the code the scanners exist to cover.
- [x] AC28: `python3 -m pytest packages/agentbundle/tests/ -q` exits 0 after all changes.
- [x] AC29: `wc -l packs/AGENTS.md` ≤ 150.
- [x] AC30: `wc -l AGENTS.md` ≤ 250.

## Assumptions

- **Technical:** `agentbundle catalogue contracts` is not reserved by ini-005's
  `catalogue-tooling-rewire` spec (verified: spec not yet authored at time of this wave;
  current registered `agentbundle catalogue` subcommands do not include `contracts`).
- **Technical:** Nested subparsers within `agentbundle catalogue contracts` are
  supported by the existing argparse wiring (verified: `oplog` uses the same three-level
  pattern in `cli.py`).
- **Technical:** `importlib.resources` can read the generated inventory and its named
  files from `agentbundle._data`; verified at HEAD for the AC7 inventory set.
- **Technical:** Version `0.34.0` is the next minor from current HEAD `0.33.3`. Verify
  before opening the PR that no other in-flight branch has claimed this version number.
- **Technical:** The generated positive inventory, checked against `contracts/`, is the
  sole runtime membership authority; `_data/` enumeration is not a public-discovery API.
- **Deferred:** Adding a `catalogue contracts check` command that validates a given local
  file against the bundled schema (useful for adopter-local contract validation). Out of
  scope for Wave 3; file under `backlog` if the need surfaces.
- **Deferred:** Surfacing `next_steps` in the `InitResult` JSON output (for consistency
  with `SelfHostedInitResult`). Wave 3 emits hints only in table output; JSON schema is
  unchanged. Tracked as `(deferred: init-result-json-next-steps)` in
  `workspace.toml [backlog].open`.
