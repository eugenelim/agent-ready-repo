# Spec: Catalogue Tooling — Lint

- **Status:** Draft
- **Owner:** eugenelim
- **Initiative:** ini-005 AgentBundle Portable Catalogue Tooling
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ini-005 brief (Bucket 5); [`spec/catalogue-tooling-foundation`](../catalogue-tooling-foundation/spec.md)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

`agentbundle/catalogue_tooling/lint.py` exists as a stub that raises
`NotImplementedError`. No portable, stdlib-only lint command exists that an
external catalogue can run without a Makefile or `tools/` directory. The
existing `agentbundle/build/lint_packs.py` has valuable portability checks
(symlink rejection, Windows-poisonous names, per-target metadata caps) but
no structured result type, no JSON output, and no catalogue-level rules
(duplicate identity, name/version parity, schema validation, etc.).

This spec fills `lint.py` with a `lint_catalogue(root, pack=None) -> LintResult`
function, wraps the existing `lint_packs` logic as the portability rule set,
adds the portable catalogue-level rules, implements JSON and table renderers,
wires the `agentbundle catalogue lint` and `agentbundle lint packs` CLI stubs
from the foundation spec, and adds a deprecation shim for the legacy
`python -m agentbundle.build lint-packs` entry point.

## Boundaries

### Always do

- Implement `lint_catalogue(root: Path, pack: str | None = None) -> LintResult`
  in `agentbundle/catalogue_tooling/lint.py`. This is the single callable
  for all lint paths — CLI and programmatic.
- Call `agentbundle.build.lint_packs.lint_all_packs` (or `lint_pack`) to
  reuse the existing portability checks; translate string findings into
  `Diagnostic` objects with stable codes.
- Add the portable catalogue-level rules listed in § Acceptance Criteria.
- Implement `render_json(result: LintResult) -> str` and
  `render_table(result: LintResult) -> str` in `lint.py` or a sibling
  `_render.py`. `render_json` emits one valid JSON document; `render_table`
  groups diagnostics by pack.
- Replace the `NotImplementedError` stubs in the `agentbundle catalogue lint`
  and `agentbundle lint packs` CLI handlers with real dispatch to
  `lint_catalogue`. Both routes call the **same function** — no duplicate
  validation logic.
- Add `python -m agentbundle.build lint-packs` deprecation shim: print one
  line to stderr (`agentbundle.build lint-packs is deprecated; use agentbundle
  catalogue lint --root <root> instead`) then delegate to `lint_catalogue`.
- Use stable diagnostic codes of the form `CAT-Lxxx` (see § Acceptance
  Criteria for the full table).
- Emit `--format json` output exclusively to stdout; all progress and
  warnings to stderr.
- Deterministic ordering: diagnostics sorted by (pack, source-relative path,
  line, col, code).
- Python 3.11 stdlib only. Read-only: no file mutations.
- All new tests pass; all existing tests pass.

### Ask first

- Adding a `--fix` mode (out of scope for lint).
- Reporting doc-quality or governance issues (RFC checks, SAST findings).
- Changing the `CAT-Lxxx` numbering after the spec is accepted.

### Never do

- Duplicate the portability logic from `lint_packs.py` — call it, don't copy it.
- Write to any file or directory during a lint run.
- Spawn a subprocess to call `agentbundle` from within `agentbundle`.
- Include credentials, bearer tokens, or credential-bearing URLs in any output.
- Emit partial JSON or newline-delimited JSON; one complete document to stdout.

## Testing Strategy

- **TDD** for each new portable rule: write the failing test first, then the
  rule. One test per violation path + one clean-catalogue happy path.
- **TDD** for renderers: one test for `render_json` (valid JSON, required
  top-level keys, deterministic ordering); one for `render_table` (groups by
  pack, no empty sections).
- **Goal-based** for CLI wiring: subprocess `agentbundle catalogue lint --root
  <clean-fixture>` exits 0; `agentbundle lint packs --root <dirty-fixture>`
  exits 1 with findings.
- **Goal-based** for deprecation shim: subprocess `python -m agentbundle.build
  lint-packs --packs-dir <dir>` exits with same code as `catalogue lint`; stderr
  contains the deprecation string.

## Acceptance Criteria

- [ ] AC1: `lint_catalogue(root)` returns a `LintResult` with `ok=True` and
  no diagnostics for a clean fixture catalogue.
- [ ] AC2: `lint_catalogue(root, pack="foo")` filters diagnostics to only the
  named pack; diagnostics for other packs are not included.
- [ ] AC3: Catalogue-level rules produce diagnostics with the following stable
  codes (all severity ERROR unless noted):

  | Code     | Rule                                                         |
  |----------|--------------------------------------------------------------|
  | CAT-L001 | `catalogue.toml` present but invalid per config.py           |
  | CAT-L002 | Required catalogue marker missing (packs dir or marketplace.json) |
  | CAT-L003 | Duplicate pack identity across packs dir                     |
  | CAT-L004 | Pack directory name differs from `[pack].name` in pack.toml  |
  | CAT-L005 | pack.toml not parseable as TOML                              |
  | CAT-L006 | pack.toml fails pack.schema.json validation                  |
  | CAT-L007 | plugin.json not parseable as JSON                            |
  | CAT-L008 | plugin.json fails plugin schema validation                   |
  | CAT-L009 | pack.toml and plugin.json name or version mismatch           |
  | CAT-L010 | Skill directory missing SKILL.md                             |
  | CAT-L011 | Skill frontmatter missing required key or invalid value      |
  | CAT-L012 | Agent metadata file missing required frontmatter             |
  | CAT-L013 | Command metadata structure invalid (where applicable)        |
  | CAT-L014 | Hook or hook-wiring file structure invalid                   |
  | CAT-L015 | Profile schema invalid or references unknown primitive       |
  | CAT-L016 | Source-relative path escapes pack root                       |
  | CAT-L017 | Case-insensitive path collision within pack                  |
  | CAT-L018 | Primitive name not unique within pack                        |
  | CAT-L019 | Declared adapter name not in adapter contract                |
  | CAT-L020 | Allowed scope value not in permitted set                     |
  | CAT-L021 | Configured path escapes catalogue root                       |
  | CAT-L022 | Symlink in shippable pack content (WARN on absence)          |
  | CAT-L023 | Windows-poisonous path name                                  |
  | CAT-L024 | Primitive name does not match required pattern               |
  | CAT-L025 | Primitive name exceeds max length                            |
  | CAT-L026 | Primitive description exceeds max length                     |
  | CAT-L027 | Multiline metadata form not supported                        |

- [ ] AC4: `render_json(result)` returns a string that is a valid JSON object
  containing: `schema_version`, `command`, `operation`, `agentbundle_version`,
  `catalogue_schema_version`, `ok`, `diagnostics` (array). Each diagnostic
  object contains: `code`, `severity`, `pack`, `path`, `line`, `col`,
  `message`, `remediation`. Output is deterministic across identical inputs.
- [ ] AC5: `render_table(result)` groups diagnostics by pack, emits a header
  row per pack, and is human-readable plain text.
- [ ] AC6: `agentbundle catalogue lint --root <clean>` exits 0 and emits no
  diagnostics. `agentbundle catalogue lint --root <dirty>` exits 1 and emits
  at least one diagnostic to stderr (table mode default).
- [ ] AC7: `agentbundle catalogue lint --root <dir> --format json` emits one
  valid JSON document to stdout and nothing to stdout in non-json mode; all
  warnings and progress go to stderr in both modes.
- [ ] AC8: `agentbundle lint packs --root <dir>` produces identical exit code
  and diagnostics to `agentbundle catalogue lint --root <dir>` on the same
  input. Both call `lint_catalogue` with no intervening validation.
- [ ] AC9: `python -m agentbundle.build lint-packs --packs-dir <dir>` prints
  the deprecation string to stderr and exits with the same code as
  `agentbundle catalogue lint --root <parent-of-packs-dir>`.
- [ ] AC10: Diagnostics are sorted by (pack, path, line, col, code) in all
  output modes. Identical inputs always produce identical output.
- [ ] AC11: All existing `agentbundle/build/lint_packs` tests pass unmodified.

## Assumptions

1. The foundation spec is merged and `catalogue_tooling/lint.py` already exists
   as a stub; this spec replaces the stub body only.
2. `agentbundle.build.lint_packs.lint_pack` and `lint_all_packs` remain their
   public API and are not moved by this spec.
3. `pack.schema.json` exists at the pack root or a canonical path discoverable
   relative to the catalogue root; if absent the CAT-L006 rule emits WARN, not
   ERROR.
4. The adapter contract at `docs/contracts/adapter.toml` is the authoritative
   list of known adapter names for CAT-L019.
5. `agentbundle_version` in JSON output is read from `agentbundle.__version__`
   (already exists); `catalogue_schema_version` is read from `catalogue.toml`
   when present, else `"unknown"`.
