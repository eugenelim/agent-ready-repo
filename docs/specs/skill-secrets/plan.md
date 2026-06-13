# Plan: skill-secrets

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

> **Post-shipment frontmatter migration (2026-05-25).** The
> `credentialed` and `primitive-class` keys named throughout T9 / T10 /
> T12 below now nest under the agentskills.io-spec `metadata:` escape
> hatch (`metadata.credentialed`, `metadata.primitive-class`). The
> spec's AC25 / AC29 / Boundaries sections were updated in lockstep
> and [RFC-0006 § Amendments](../../rfc/0006-skill-secrets-storage.md#amendments)
> records the rationale. Construction-test descriptions below name the
> original top-level shape — the actual on-disk fixtures
> (`packages/agentbundle/tests/fixtures/creds/skills/*/SKILL.md`,
> `tools/test-lint-agent-artifacts.sh` heredocs) use the nested shape.
> The drift is intentional history; spec.md is the contract.

## Approach

Fifteen tasks (T13 split into T13a/T13b/T13c) across four
surfaces:

- **Definitional (T1)** — ADR-0002 amendment freezing the narrow
  "hook-shaped" definition the spec depends on. Single-file edit;
  lands in this spec PR alongside the spec itself.
- **Runtime library (T2–T7)** — `agentbundle.credentials` loader
  (shim package at `packages/agentbundle/agentbundle/` re-exporting
  from `agentbundle.creds.loader`), the stdlib `.env` parser,
  per-platform Tier-2 backends (`_keychain_macos.py` subprocess
  wrapper; `_credman_windows.py` ctypes wrapper, dispatch
  platform-discriminated at module-load time per AC4b), Tier-3
  dotfile read/write, and the `creds-schema.toml` parser. All
  library code under `packages/agentbundle/agentbundle/creds/`.
  `pyproject.toml`'s `tool.setuptools.packages.find.include` is
  extended in T3 so the `agentbundle` shim ships with the wheel.
  TDD throughout — the contract is small and the failure modes
  are concrete.
- **CLI surface (T8)** — `agentbundle creds setup`/`check`/`where`/`rm`
  at `packages/agentbundle/agentbundle/commands/creds.py` (matches
  the existing eleven sibling verbs at `agentbundle/commands/`),
  wired to the loader + Tier-2/3 backends; namespace enumeration
  walks both scope state files; tombstone arguments enforce the
  argv ban with the documented stderr text.
- **Conventions, lint, templates, worked example, docs
  (T9–T13c)** — SKILL.md frontmatter extensions,
  `tools/lint-agent-artifacts.sh` allow-list update,
  `conventions-check` AST-walker lint extensions, author skill
  carrying both template variants, worked example skill, the
  seed-side CONVENTIONS.md edit (T13a), the Diátaxis how-to
  (T13b), and the ROADMAP closure pass (T13c).

Riskiest part is **T5 (Windows Credential Manager via ctypes)** —
ctypes type-mismatch bugs are silent (wrong-sized struct fields
return garbage rather than raising), so the test matrix has to assert
byte-equality round-trips against every `CREDENTIAL` field. The
implementation is small (<100 lines per RFC-0006 § 2) but the
regression surface is wide and the platform is non-Darwin/non-Linux
where most contributors don't develop.

Second-riskiest is **T8 (CLI verb)** — five subcommands, three tier
backends, two opt-out flags (`--allow-insecure-fallback`,
`--allow-permissive-acl`), one schema parser, one dual-scope state
walk. Decomposed into per-subcommand tests so each path is verified
independently before integration.

Per-tier verifiability is independent: T4 lands without T5 (Darwin
CI runs Tier 2 via the macOS backend; on Windows CI the macOS
backend is not loaded per AC4b's platform dispatch), T5 lands
without T6 (every platform exercises Tier 1 + Tier 2 first, falls
through to Tier 3 only when Tier 2 returns `None`). The plan does
not bundle adapters into a single mega-task — each tier's tests run
independently.

## Constraints

- [RFC-0006](../../rfc/0006-skill-secrets-storage.md) — drives every
  decision; specific sections cited inline per task.
- [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md)
  — § Consequences amended in T1 to freeze the narrow "hook-shaped"
  definition; the architecture rule (skills don't hold credentials;
  credentialed primitives at user scope are not hook-shaped) depends
  on the amendment.
- [`agent-spec-cli` spec](../agent-spec-cli/spec.md) — stdlib-only
  commitment (no `python-dotenv`, no `keyring`, no `pywin32`); CLI
  subcommand surface lives under
  `packages/agentbundle/agentbundle/commands/`; per-subcommand exit
  codes follow the existing 0/2/3 convention.
- [`distribution-adapters` spec](../distribution-adapters/spec.md) —
  pack source-tree layout (`.apm/skills/<name>/SKILL.md`, `assets/`,
  `references/`, `scripts/`); SKILL.md frontmatter schema.
- [`adapt-to-project` spec](../adapt-to-project/spec.md) — dual-scope
  state-file walk shape (`<repo>/.agentbundle-state.toml` +
  `~/.agentbundle/state.toml`) for namespace enumeration in T8.

## Construction tests

Most construction tests live under **Tasks** below (per-task
`Tests:` subsections). This section covers cross-cutting tests only.

**Integration tests:**

- **Fixture-skill end-to-end** (touches T9, T10, T12): each fixture
  under `packages/agentbundle/tests/fixtures/creds/skills/` runs
  through `tools/lint-agent-artifacts.sh` and through the
  `conventions-check` lint extension; conforming fixtures pass clean,
  malformed fixtures produce the expected findings.
- **Tier precedence end-to-end** (touches T3, T4, T5, T6): a fixture
  namespace with one key set in env, one in Tier 2, one in Tier 3
  exercises `load_credentials` and asserts the right tier resolved
  for each key. Runs on Darwin + Windows runners; on Linux no
  Tier-2 backend is loaded (per AC4b), so the Tier-2-targeted key
  falls through to Tier 3.
- **`agentbundle creds` round-trip** (touches T8): `setup` →
  `where` → `check` → `rm` against a fixture namespace; assert
  tier announced on stderr matches `where`'s output; assert exit
  codes match the spec.

**Manual verification** (release-checklist rows; RFC-0006 §
Drawbacks "Windows test matrix grows substantially"):

- `getpass.getpass` real-tty refusal on a Windows interactive
  terminal (GitHub runners don't allocate a PTY).
- `CRED_PERSIST_LOCAL_MACHINE` survives-logoff round-trip on a real
  Windows box (write → logoff → logon → read).
- `ERROR_NO_SUCH_LOGON_SESSION` hard-fail under `LocalSystem`
  service-account context (scheduled-task runner).

## Tasks

### T1: Amend ADR-0002 with narrow "hook-shaped" definition

**Depends on:** none

**Tests:** (verification mode: goal-based check)

- *Substring assertion:* `grep` the ADR file for the exact
  conjunction phrasing: `(i) binds to a runtime event` AND
  `(ii) requires wiring-merge into a hand-edited shared file` AND
  `is **not** hook-shaped under this definition`. All three must
  appear. [AC1]
- *Heading assertion:* the file contains the literal heading
  `### 2026-05-24 — Narrow definition of "hook-shaped" (per RFC-0006)`
  under an `## Amendments` section. [AC1]
- *Link resolution:* `tools/lint-agents-md.sh` resolves every link
  the amendment adds (RFC-0006, RFC-0005). [AC1]

**Approach:**

- Add `## Amendments` section to ADR-0002 after § References.
- Quote the amendment text verbatim from RFC-0006 § Follow-on
  artifacts (the "(i) binds AND (ii) requires wiring-merge"
  conjunction), cite RFC-0006 by section anchor, and note RFC-0005's
  implicit dependence on the same definition.

**Done when:** the three grep assertions pass; `make build-check`
clean.

### T2: Stdlib `.env` parser

**Depends on:** none

**Tests:** (verification mode: TDD;
test file: `packages/agentbundle/tests/unit/test_credentials_parser.py`)

- *Parses* `KEY=value` → `{"KEY": "value"}`. [AC2]
- *Parses* `KEY="value with spaces"` → `{"KEY": "value with spaces"}`.
  [AC2]
- *Strips* trailing `\r` on `KEY=value\r\n` lines.  [AC2]
- *Preserves* `\r` inside quoted values: `KEY="a\rb"` →
  `{"KEY": "a\rb"}`. [AC2]
- *Ignores* `# comment` lines and blank lines.
- *Refuses* (raises `EnvParseError`) on `export KEY=value`.
- *Refuses* on `KEY=$OTHER` (variable expansion).
- *Refuses* on multi-line quoted values (`KEY="line1\nline2"` across
  two physical lines).
- *Accepts* `KEY=value=with=equals` → `{"KEY": "value=with=equals"}`.

**Approach:**

- New file `packages/agentbundle/agentbundle/creds/__init__.py`
  (empty) and `packages/agentbundle/agentbundle/creds/loader.py`.
- Implement `parse_env_file(path: Path) -> dict[str, str]` as the
  ~12-line parser; document the "intentionally less than
  `python-dotenv`" comment inline.
- Add `EnvParseError` exception class.

**Done when:** all 9 parser tests pass; no third-party imports.

### T3: `agentbundle.credentials` loader API + Tier-1 env-var backend

**Depends on:** T2

**Tests:** (verification mode: TDD;
test file: `packages/agentbundle/tests/unit/test_credentials_loader.py`)

- *`load_credentials("jira", required_keys=["API_TOKEN"])` returns*
  a `Credentials` object with `.API_TOKEN` attribute when
  `JIRA_API_TOKEN` is in `os.environ`. [AC3, AC5]
- *Returns* the value from `os.environ["JIRA_API_TOKEN"]`. [AC5]
- *Empty env var* (`JIRA_API_TOKEN=""`) is treated as unset; falls
  through to Tier 2 (which is unavailable by absence in this task,
  per AC4b), then Tier 3 (unimplemented in this task, returns
  `None`) → `CredentialsMissingError`. [AC5]
- *Missing required key* raises `CredentialsMissingError` naming
  the namespace and the missing key list. [AC3]
- *`Credentials` is immutable* — attribute assignment raises.
- *Public surface:* `agentbundle.credentials` re-exports
  `load_credentials`, `Credentials`, `CredentialsMissingError`,
  `Tier2HardFailError`; nothing else.
- *Wheel installability:* an integration test runs
  `python -m pip install --target {tmp_path}/site
  packages/agentbundle`, then `PYTHONPATH={tmp_path}/site
  python -c "from agentbundle.credentials import load_credentials"`,
  and asserts exit 0. Runs on every CI platform. [AC4c]
- *Platform dispatch:* a test monkeypatches `sys.platform = "linux"`,
  reloads `agentbundle.credentials`, asserts neither
  `agentbundle.creds._keychain_macos` nor
  `agentbundle.creds._credman_windows` are in `sys.modules`. [AC4b]

**Approach:**

- Implement `Credentials` as a frozen `dataclass` (slots, immutable).
- Implement `load_credentials(namespace, required_keys)` with the
  precedence resolver; Tier 2 dispatch follows AC4b's platform
  discrimination at module-load time; Tier 3 is stubbed to return
  `None` in this task. Signature is *resolution only* — schema
  concerns stay out of this surface per the AC24b clarification.
- Define exception hierarchy in
  `packages/agentbundle/agentbundle/creds/exceptions.py`.
- Create shim package
  `packages/agentbundle/agentbundle/__init__.py` (empty) and
  `packages/agentbundle/agentbundle/credentials.py` (re-exports
  from `agentbundle.creds.loader`) so
  `from agentbundle.credentials import load_credentials` resolves
  for credentialed-primitive authors.
- **Edit `packages/agentbundle/pyproject.toml`**:
  `[tool.setuptools.packages.find] include` becomes
  `["agentbundle*", "agentbundle*"]`. Without this edit, the shim
  is not picked up by `pip install` and AC4c fails.

**Done when:** all tests pass; the wheel-install test confirms the
shim is discoverable.

### T4: macOS Keychain Tier-2 backend

**Depends on:** T3

**Tests:** (verification mode: TDD + integration;
test file: `packages/agentbundle/tests/integration/test_keychain_macos.py`,
skipped on non-Darwin)

- *Write* a value via `_keychain_macos.write_credential(namespace,
  key, value)`; *read* via `read_credential(namespace, key)`;
  byte-equality assert. [AC7]
- *Token absent from argv:* during the `Popen` call, inspect
  `psutil.Process(child_pid).cmdline()` (or `/proc/<pid>/cmdline`
  on Darwin's procfs-equivalent path) and assert the token bytes
  are absent. [AC6]
- *`find-generic-password` shape:* mocked subprocess assertion that
  argv is `["/usr/bin/security", "find-generic-password", "-s",
  "agentbundle", "-a", "<namespace>:<key>", "-w"]`. [AC6]
- *`add-generic-password` shape:* mocked subprocess assertion that
  argv is `["/usr/bin/security", "add-generic-password", "-U",
  "-s", "agentbundle", "-a", "<namespace>:<key>", "-w"]` with no
  trailing token argument; token passes via `stdin=PIPE`. [AC6]
- *Missing credential:* `read_credential` on an unset namespace
  returns `None` (the resolver falls through). [AC8 inverse]
- *Non-Darwin platforms:* per AC4b/AC8, the module is **not
  imported** when `sys.platform != "darwin"`. A loader-level test
  asserts `agentbundle.creds._keychain_macos` is absent from
  `sys.modules` after a fresh import of `agentbundle.credentials`
  under monkeypatched `sys.platform = "linux"`.
- *Test isolation:* every test creates a `tmp_path`-scoped Keychain
  via `security create-keychain`, exports `KEYCHAIN_PATH`, and
  deletes the keychain in teardown. No writes to the developer's
  login keychain.

**Approach:**

- New file
  `packages/agentbundle/agentbundle/creds/_keychain_macos.py`.
- Implement `read_credential(namespace, key) -> str | None` and
  `write_credential(namespace, key, value) -> None` and
  `delete_credential(namespace, key) -> None`.
- Wire into the loader's Tier-2 dispatch in T3 (the dispatch is
  platform-discriminated; the loader imports the backend by
  `sys.platform` at module-load time).

**Done when:** Darwin CI runs the full test file green; non-Darwin
CI skips the file cleanly; loader's Tier-2 path resolves correctly
on Darwin.

### T5: Windows Credential Manager Tier-2 backend

**Depends on:** T3

**Tests:** (verification mode: TDD + integration;
test file: `packages/agentbundle/tests/integration/test_credman_windows.py`,
skipped on non-Windows)

- *`CREDENTIAL` struct field zero-init:* construct a `CREDENTIAL`
  instance via `ctypes.Structure` defaults; assert `Flags == 0`,
  `Comment == None`, `LastWritten == FILETIME(0, 0)`,
  `AttributeCount == 0`, `Attributes == None`, `TargetAlias ==
  None`. [AC9]
- *Round-trip byte-equality:* write a value, read it,
  `assert read_back == value.encode("utf-16-le")`. [AC10]
- *Target-name convention:* assert the `TargetName` field on a
  written credential is exactly `"agentbundle:<namespace>:<key>"`.
  [AC9]
- *`UserName` field:* assert the `UserName` field is the namespace
  string. [AC9]
- *Persistence flag:* assert `Persist == CRED_PERSIST_LOCAL_MACHINE
  (2)`. [AC9]
- *Credential type:* assert `Type == CRED_TYPE_GENERIC (1)`. [AC9]
- *Win32 error dispatch:* monkeypatch the wrapper's
  `GetLastError`-equivalent boundary (the implementation either uses
  `ctypes.WinError(code)` after a `BOOL`-false return, or reads
  `ctypes.get_last_error()` after `use_last_error=True` binding) to
  inject each of `1168` (`ERROR_NOT_FOUND`), `1312`
  (`ERROR_NO_SUCH_LOGON_SESSION`), `1004` (`ERROR_INVALID_FLAGS`),
  `1326` (`ERROR_LOGON_FAILURE`); assert `read_credential` returns
  `None` for 1168 and raises `Tier2HardFailError` with stderr-shaped
  message naming the cause for the other three. The implementation
  pins which boundary to monkeypatch in a docstring so the test
  attaches at the right level. [AC11]
- *No argv leak:* assert no subprocess is invoked during write/read;
  `CredFree` is called after every successful read. [AC9 — ctypes-only]
- *Non-Windows platforms:* per AC4b/AC12, the module is **not
  imported** when `sys.platform != "win32"`. Parallel
  assertion-style test to T4's non-Darwin case.
- *Test isolation:* every test uses a target-name prefix derived
  from `tmp_path` (`f"agentbundle-test-{tmp_path.name}:..."`),
  guaranteeing no collision with a developer's real Credential
  Manager entries; `delete_credential` runs in teardown.

**Approach:**

- New file
  `packages/agentbundle/agentbundle/creds/_credman_windows.py`.
- Define `CREDENTIAL` `ctypes.Structure` matching `wincred.h`'s
  layout (the four surface functions are `CredReadW`,
  `CredWriteW`, `CredDeleteW`, `CredFree`); use
  `ctypes.windll.advapi32` to bind.
- Implement `read_credential`/`write_credential`/`delete_credential`
  with the error-code dispatch matrix.
- Wire into the loader's Tier-2 dispatch on Windows.
- Per RFC-0006 § 2: under 100 lines total (the file is
  declarations-heavy by nature; the spec phase pins the upper bound,
  not the exact count).

**Done when:** Windows CI runs the full test file green; non-Windows
CI skips the file cleanly; loader's Tier-2 path resolves correctly
on Windows.

### T6: Tier-3 dotfile read + write

**Depends on:** T2, T3

**Tests:** (verification mode: TDD;
test file: `packages/agentbundle/tests/unit/test_credentials_dotfile.py`;
**platform gating:** POSIX assertions guarded by
`@pytest.mark.skipif(sys.platform == "win32", ...)`; Windows
assertions guarded by `@pytest.mark.skipif(sys.platform != "win32",
...)`. Tests platform-agnostic to the dotfile shape — path
resolution, atomic write, fallback semantics — run unguarded.)

- *Path resolves* to `pathlib.Path.home() / ".agentbundle" /
  "credentials.env"` with `$HOME` redirected to `tmp_path`. [AC13]
- *Atomic write:* monkeypatch `os.replace` to record the temp-file
  path; assert the temp file lives in the target directory (not in
  `/tmp`); assert mid-write `os.read` of the target path returns
  either the prior contents or the new contents, never partial.
  [AC14]
- *POSIX permissions:* on POSIX, after write to a non-existent
  parent, assert `path.stat().st_mode & 0o777 == 0o600` and
  `parent.stat().st_mode & 0o777 == 0o700`. [AC15]
- *POSIX shared-parent behavior:* on POSIX, create the parent first
  with mode `0o755` (simulating a brownfield `~/.agentbundle/`
  shared with RFC-0004 install state), write the credentials file,
  assert the helper **does not rewrite** the parent's mode (mode
  stays `0o755`) but emits a stderr warning naming the permissive
  mode. [AC15]
- *Windows permissions:* on Windows, assert `os.chmod` is NOT
  called (monkeypatch to record calls); assert `icacls <path>` is
  invoked after write and its output is parsed; if a fixture DACL
  contains a `BUILTIN\Users:R` ACE, the helper raises
  `PermissiveAclError` unless `allow_permissive_acl=True` is
  passed. [AC15]
- *Tier-3 fallback:* when Tier 1 returns `None` and the Tier-2
  backend is unloaded (or the loaded backend returns `None`), the
  loader reads the key from the dotfile via the T2 parser. [AC4]
- *Tier-3 miss:* when no dotfile exists, the loader returns `None`
  for the key (resolver raises `CredentialsMissingError` if it's
  required). [AC4]

**Approach:**

- Extend `loader.py` with `_dotfile_read(namespace, key) -> str |
  None` and `_dotfile_write(namespace, key, value, *,
  allow_permissive_acl=False) -> None` and
  `_dotfile_delete(namespace, key) -> None`.
- Implement atomic write via `tempfile.mkstemp(dir=target_dir)` →
  `os.write` → `os.fchmod` (POSIX) → `os.close` → `os.replace`.
- Implement `_verify_icacls(path)` on Windows: run `icacls <path>`,
  parse the output for non-default ACEs (anything beyond the
  inherited `<user>`, `NT AUTHORITY\SYSTEM`,
  `BUILTIN\Administrators`), raise `PermissiveAclError` if any
  found.

**Done when:** all dotfile tests pass on both Darwin (POSIX path)
and Windows (icacls path); loader's Tier-3 fallback works.

### T7: `creds-schema.toml` format + parser

**Depends on:** T3

**Tests:** (verification mode: TDD;
test file: `packages/agentbundle/tests/unit/test_credentials_schema.py`)

- *Parses* a fixture
  `tests/fixtures/creds/schema-valid/creds-schema.toml` into a
  typed `CredsSchema` object with `.namespace`, `.keys` (list of
  `KeyDef(name, label, secret)`). [AC24]
- *Refuses* a schema with no `[namespace]` table
  (`SchemaError("missing [namespace]")`).
- *Refuses* a schema with an empty `namespace.keys` list
  (`SchemaError("namespace.keys must declare at least one key")`).
- *Refuses* a key with `secret` of non-boolean type.
- *Schema validation* reads the namespace's
  `references/creds-schema.toml` from a fixture skill directory.
- *Canonical-path resolution:* given a fixture state-file
  conforming to the **existing** v0.3 `PackState` schema with
  `files = { ".claude/skills/<name>/SKILL.md" = { sha = "...", ... } }`,
  `_relative_schema_path(state, pack, name)` walks `pack.files` for
  the SKILL.md relpath matching
  `^\.claude/skills/[^/]+/SKILL\.md$` (matching the skill name),
  takes its parent dir, joins `references/creds-schema.toml`, and
  returns the state-relative path. Missing file raises
  `SchemaError("creds-schema.toml not found at expected path:
  <path>")`. No new state-schema fields are required. [AC24b]

**Approach:**

- Add `_parse_schema(path: Path) -> CredsSchema` to `loader.py`
  using `tomllib`.
- Add `CredsSchema` and `KeyDef` dataclasses.
- Add `_relative_schema_path(state, pack, skill_name) -> Path` for
  AC24b's state-walk; underscore-prefixed because CLI callers route
  through `commands/creds._resolve_schema_for_namespace` (the
  by-namespace twin); see the loader docstring for the contract.
- Document the schema shape in `loader.py` docstring; the canonical
  format definition lives in `spec.md` § AC24.

**Done when:** schema tests pass. `load_credentials` itself stays
*resolution-only* per AC24b's clarification — schema validation
lives in the `agentbundle creds check` CLI surface, not on the
loader.

### T8: `agentbundle creds` CLI verb

**Depends on:** T3, T6, T7

**Tests:** (verification mode: TDD + integration;
test file: `packages/agentbundle/tests/integration/test_creds_cli.py`)

- *`setup <namespace>` writes to Tier 2 on Darwin/Windows;* stderr
  matches `"wrote to keyring"`; exit 0. [AC16]
- *`setup <namespace>` writes to Tier 3 on Linux;* stderr matches
  `"wrote to dotfile"`; exit 0. [AC16]
- *`setup --allow-insecure-fallback` on Darwin* writes to Tier 3;
  stderr matches `"wrote to dotfile (insecure fallback)"`. [AC22]
- *`setup --allow-permissive-acl` on Windows* (or simulated via a
  monkeypatched `_verify_icacls`): writes Tier 3 to a fixture path
  whose parsed DACL contains a `BUILTIN\Users:R` ACE; exits 0;
  stderr matches `"permissive DACL accepted"`. Without the flag
  against the same fixture, exits non-zero with stderr matching
  `"DACL too permissive"`. [AC15, AC22]
- *`setup` with no positional argument* walks both state files,
  prints the list of `credentialed: true` primitives, prompts via
  `input()`. [AC17]
- *`check <namespace>` exits 0* when all required keys resolve;
  *exits 2* when any missing (stderr names them); *exits 3* on
  Tier-2 hard-fail or schema parse error. [AC18]
- *`where <namespace>` prints* one line per required key naming the
  resolving tier (`env`, `keyring`, `dotfile`, `missing`); does not
  print the value. [AC19]
- *`rm <namespace>` deletes* from every tier holding any of the
  namespace's keys; refuses with stderr if no tier holds anything.
  [AC20]
- *No `get` subcommand:* `agentbundle creds get foo` exits non-zero
  with `unknown command: get` (argparse subparser refusal). [AC21]
- *`setup` refuses non-tty stdin (POSIX only):* assertion via
  subprocess with `stdin=subprocess.DEVNULL`; exits non-zero with
  `stdin is not a tty`. Skipped on Windows — `getpass.getpass`
  uses `msvcrt.getwch()` regardless of `isatty()`, so the
  POSIX-shaped test does not exercise the real path; Windows tty
  refusal is a manual-QA row (§ Construction tests → Manual
  verification). [AC23]
- *`setup` refuses argv-borne token (all platforms):* the argparse
  subparser declares `--token`, `--api-token`, `--api-key`,
  `--bearer`, `--pat`, `--password` as **tombstone arguments**
  whose custom action prints `tokens cannot be passed via argv`
  to stderr and exits non-zero. Tests invoke each flag form and
  assert the stderr text. [AC23]

**Approach:**

- New file
  `packages/agentbundle/agentbundle/commands/creds.py`.
- Implement four subcommands via `argparse` subparsers: `setup`,
  `check`, `where`, `rm`.
- The `setup` subparser registers tombstone arguments
  (`--token`/`--api-token`/`--api-key`/`--bearer`/`--pat`/`--password`)
  with a custom `_RefuseTokenArgvAction` per AC23. Scope is the
  `setup` subparser only — other verbs are unaffected.
- `setup` invokes `getpass.getpass` per `secret = true` key;
  `input()` per `secret = false` key.
- Wire into `agentbundle/cli.py` as a new top-level verb.
- Per-subcommand exit codes: 0 success, 2 missing-credential,
  3 other error (matches the existing pattern in
  `agentbundle/commands/`).

**Done when:** all CLI tests pass; `agentbundle creds --help` lists
exactly four subcommands.

### T9: SKILL.md frontmatter extension + lint allow-list

**Depends on:** none (lint changes; no runtime coupling)

**Tests:** (verification mode: goal-based check;
inherits the existing harness's primitives — `mktemp -d` + inline
`cat <<EOF` heredocs + `LINT_ROOT="$TMP" bash
tools/lint-agent-artifacts.sh` — but uses a **per-fixture-tree
invocation shape**: the existing harness runs the linter once
against one tempdir mixing pass-and-fail fixtures and asserts an
`EXPECTED_PATTERNS` list; the credentialed cases need separate
trees because the positive and negative cases must produce
different lint exit codes. Two separate tempdirs + two invocations
is the additive shape.)

- *`credentialed: true` accepted:* an inline-heredoc skill at
  `$TMP/.claude/skills/conforming-credentialed/SKILL.md` with
  `credentialed: true` + `primitive-class: credentialed-cli` in
  frontmatter; running `LINT_ROOT="$TMP" bash tools/lint-agent-artifacts.sh`
  against a tmp tree containing only this skill exits 0. [AC25]
- *`credentialed: not-a-bool` refused:* a separate `$TMP2` tree
  with `credentialed: "yes"` (string) in frontmatter; lint exits
  non-zero; assert stderr substring `credentialed` and `must be
  boolean`. [AC25]
- *`primitive-class: unknown-class` refused:* a separate `$TMP3`
  tree with `primitive-class: mcp-broker`; lint exits non-zero;
  assert stderr substring `primitive-class` and one of
  `credentialed-cli, mcp-server`. [AC25]
- *Absence of `credentialed:` stays clean:* extending the
  existing "wrong-name" / "missing-desc" / etc. fixtures in
  `test-lint-agent-artifacts.sh` to *not* declare `credentialed:`
  confirms the existing pass-set is unaffected.

**Approach:**

- Edit `tools/lint-agent-artifacts.sh`: extend
  `ALLOWED_SKILL_KEYS = {"name", "description", "dependencies",
  "credentialed", "primitive-class"}`.
- Add a type-check branch: if `credentialed` is present, require
  boolean; if `primitive-class` is present, require one of
  `{"credentialed-cli", "mcp-server"}`.
- Extend `tools/test-lint-agent-artifacts.sh`:
  - Add new positive-fixture inline heredocs constructing the
    `conforming-credentialed` skill in a separate `$TMP_CRED_OK`
    tempdir; run the lint against it and assert exit 0.
  - Add two new negative-fixture sections constructing
    `bad-credentialed` and `bad-primitive-class` skills in
    separate tempdirs; assert exit non-zero with the documented
    stderr substrings.
  - Follow the existing `setup`/`trap rm -rf` discipline so
    fixtures don't leak.

**Done when:** the three new inline fixtures pass/fail as
specified; `tools/test-lint-agent-artifacts.sh` exits 0.

### T10: `conventions-check` lint extensions

**Depends on:** T9

**Tests:** (verification mode: TDD + integration;
test file: `packages/agentbundle/tests/integration/test_conventions_check_creds.py`)

- *Missing "Don't" block:* fixture skill at
  `packages/agentbundle/tests/fixtures/creds/skills/missing-dont-block/`
  has `credentialed: true` frontmatter but no `### Security rules
  (non-negotiable)` heading; lint reports the finding. [AC26(a)]
- *Argv flag accepted in credentialed-CLI script:* fixture skill at
  `…/skills/argv-flag/scripts/cli.py` calls
  `parser.add_argument("--token", ...)`; lint reports the finding.
  [AC26(b)]
- *Normalisation:* fixture variants
  `parser.add_argument("--Token", ...)`,
  `parser.add_argument("--api-Key", ...)`,
  `parser.add_argument("--" + "token", ...)` all flagged. [AC27]
- *Header-naming flags not flagged on `mcp-server` class:* fixture
  skill with `primitive-class: mcp-server` calling
  `add_argument("--bearer-header", ...)` is clean.
- *Dotfile substring in skill scripts:* fixture skill with
  `scripts/leak.py` containing
  `open(os.path.expanduser("~/.agentbundle/credentials.env"))` —
  lint reports the architectural violation. [AC26(c)]
- *Opt-out marker:* same fixture with
  `# credentialed-primitive: reads-creds-directly` on the same line
  is clean (but the marker itself is noted in PR review per
  spec.md § Conventions and lint).
- *Conforming fixture clean:* the `…/skills/conforming/` fixture
  passes the extended lint with zero findings.

**Approach:**

- Extend `packs/core/.apm/commands/conventions-check.md` body to
  document the three credentialed-skill rules.
- Implement the actual lint checks as a helper script
  `tools/lint-credentialed-skills.sh` (matches the existing pattern
  of `tools/lint-agents-md.sh` + `tools/lint-agent-artifacts.sh` —
  bash wrapper that shells out to an inline `python3 - <<'PY' ... PY`
  heredoc).
- **AC26(a) — "Don't" block presence.** The Python heredoc opens
  each `SKILL.md` whose YAML frontmatter declares `credentialed:
  true`, scans the body for the literal heading
  `### Security rules (non-negotiable)`, and within the section
  body greps for the two `**Never**` substrings and the
  `do not run it for them` phrase from RFC-0006 § 4. Missing
  heading or any missing substring → finding.
- **AC26(b) — argv-flag detection.** Same heredoc uses
  `ast.parse` to walk `argparse.ArgumentParser.add_argument` calls
  in every `scripts/**/*.py` file under a `credentialed: true,
  primitive-class: credentialed-cli` skill. For each
  `Call(func=Attribute(attr='add_argument'))` whose first
  positional arg is a `Constant(value=str)` beginning with `-`,
  normalise the string per AC27 (strip leading `-`, casefold,
  replace `-` with `_`) and compare against
  `{"token", "api_token", "api_key", "bearer", "pat", "password"}`.
  Dynamic flag names (`"--" + "token"`) are matched by also
  walking `BinOp(op=Add, left=Constant(str),
  right=Constant(str))` first-arg shapes and concatenating literal
  constants before normalisation. Deeper obfuscation (formatted
  strings, computed names) is out of scope per `spec.md` §
  Drawbacks.
- **AC26(c) — dotfile-substring + opt-out comment.** Per-line
  substring scan of every `scripts/**/*.py` file under a
  `credentialed: true` skill, looking for
  `.agentbundle/credentials.env`. A line containing the substring
  is skipped iff the literal opt-out comment
  `# credentialed-primitive: reads-creds-directly` appears on
  the same line (comparison after `str.rstrip()`). Otherwise →
  finding.
- The slash command runs the new helper alongside the two existing
  ones.

**Done when:** all four fixtures produce the expected lint output;
the AST walker catches the four obfuscation variants in
`spec.md` § AC27; `packs/core/.apm/commands/conventions-check.md`
lists the new helper alongside the existing two.

### T11: `add-credentialed-skill` author skill + template variants

**Depends on:** T9, T10

**Tests:** (verification mode: goal-based check)

- *Skill structure:*
  `packs/core/.apm/skills/add-credentialed-skill/SKILL.md` exists
  with kebab-case dir name, valid frontmatter, triggers listed in
  description. [AC28]
- *Template structure:* `assets/credentialed-skill-SKILL.md`
  contains two `### Variant:` headings — `credentialed-cli` and
  `mcp-server`. [AC28]
- *Verbatim "Don't" block:* the `credentialed-cli` variant
  contains the verbatim block from RFC-0006 § 4 — a substring grep
  for each of the two `**Never**` lines (`**Never** read that
  file, print it, or echo the token` and `**Never** put the token
  on the command line`), the third bullet's `do not run it for
  them` phrase, and the `agentbundle creds setup <namespace>`
  reference.
- *Template+lint integration:* a fixture skill that copies the
  `credentialed-cli` variant verbatim into its `SKILL.md` body
  passes T10's extended `conventions-check` clean (closes the
  drift-trap between the template and the lint).
- *Lint:* `tools/lint-agent-artifacts.sh` accepts the skill;
  `tools/lint-agents-md.sh` resolves all internal links.

**Approach:**

- Create
  `packs/core/.apm/skills/add-credentialed-skill/SKILL.md` with a
  short procedure: pick `primitive-class`, copy variant from
  `assets/`, fill placeholders, declare schema, import loader.
- Create `assets/credentialed-skill-SKILL.md` with the two labeled
  variants per RFC-0006 § 4 (credentialed-cli — full storage
  convention + argv ban; mcp-server — header-naming flags allowed,
  storage convention does not apply).

**Done when:** the skill ships and `tools/lint-agent-artifacts.sh`
passes against it.

### T12: `example-credentialed-skill` worked example

**Depends on:** T3, T7, T9, T11

**Tests:** (verification mode: goal-based check + integration;
test file: `packages/agentbundle/tests/integration/test_example_credentialed_skill.py`)

- *Skill structure:* the directory contains
  `SKILL.md`, `scripts/cli.py`, `references/creds-schema.toml`.
  [AC29]
- *SKILL.md frontmatter:* `credentialed: true`,
  `primitive-class: credentialed-cli`; passes
  `tools/lint-agent-artifacts.sh`. [AC29]
- *SKILL.md body:* contains the verbatim credentialed-CLI "Don't"
  block from `add-credentialed-skill`'s template. [AC29]
- *`scripts/cli.py` imports* `agentbundle.credentials.load_credentials`
  and refuses argv-ban flags (asserts `SystemExit` non-zero when
  invoked with `--token=x`). [AC29]
- *`references/creds-schema.toml`* declares two keys —
  `API_TOKEN` (`secret = true`, the required token) and a
  `BASE_URL` sibling (`secret = false`, also resolved through
  the three-tier ladder). The loader treats both as required
  via `required_keys=["API_TOKEN", "BASE_URL"]`; "sibling" is
  the spec § Objective wording (Tier 1's `_BASE_URL`/`_EMAIL`/
  `_FLAVOR` shape), not a hint that the key is optional at the
  loader level. [AC29]
- *Conventions-check clean:* the extended lint from T10 reports
  zero findings against this skill. [AC29]

**Approach:**

- Create the skill under
  `packs/core/.apm/skills/example-credentialed-skill/` per spec.md
  § AC29.
- The `cli.py` is a 30-line no-op: parses args, loads credentials,
  prints `f"would call {schema.namespace} API with token=*** at
  {base_url}"` to stdout — never echoes the token.

**Done when:** the skill passes both lints and the integration test;
`agentbundle render` projects it under every adapter without
warnings.

### T13a: `CONVENTIONS.md` "Credentialed skills" section (via seed upstream)

**Depends on:** T12

**Tests:** (verification mode: goal-based check)

- *Seed edit:* `packs/core/seeds/docs/CONVENTIONS.md` gains a
  top-level `## Credentialed skills` section. [AC30]
- *Section content:* substring assertions for two-layer
  architecture mention, three storage tiers, argv ban,
  anti-pattern register link to `../rfc/0006-skill-secrets-storage.md#6-anti-pattern-register`,
  corporate-network requirements link to RFC-0006 § 7. [AC30]
- *Build gate:* `make build-self` projects the seed into the
  live repo; `make build-check` exits 0. [AC30, AC33]
- *No direct edit:* the projected `docs/CONVENTIONS.md` is **not**
  touched directly — a `git diff` shows the change only in the
  seed-side path during the editing phase. (After `make build-self`,
  the projected file matches.)

**Approach:**

- Edit `packs/core/seeds/docs/CONVENTIONS.md`: add the new section
  after the existing top-level sections (placement at the end,
  before the README footer).
- Run `make build-self` to regenerate `docs/CONVENTIONS.md`.
- Run `make build-check` to confirm no drift.

**Done when:** `make build-check` clean; the projected
`docs/CONVENTIONS.md` contains the new section.

### T13b: Diátaxis how-to `add-a-credentialed-skill.md`

**Depends on:** T12

**Tests:** (verification mode: goal-based check)

- *File exists* at `docs/guides/credential-brokers/how-to/add-a-credentialed-skill.md`
  with frontmatter conforming to the Diátaxis how-to shape (per
  the `new-guide` skill's `assets/howto.md` template). [AC31]
- *References worked example* by path
  (`packs/core/.apm/skills/example-credentialed-skill/`). [AC31]
- *Lint:* `tools/lint-agents-md.sh` exits clean against the new
  guide; every internal link resolves.

**Approach:**

- Run the `new-guide` skill in `how-to` quadrant.
- Walk-through structure: pick a namespace → write the schema →
  import the loader → embed the "Don't" block → declare
  frontmatter → run `agentbundle creds setup` → run `agentbundle
  creds check`. ~200 lines.

**Done when:** the file lands; the lint passes.

### T13c: `backlog.md` per-task entries close

**Depends on:** T12

**Tests:** (verification mode: goal-based check)

- *Section structure:* `docs/backlog.md` contains a top-level
  `## skill-secrets` section (already drafted in the spec PR;
  this task closes its open items as work lands). [AC32]
- *Per-task grouping:* the section bullets are grouped by task
  (T1–T13c), not per-AC; every task row T1, T2, T3, T4, T5, T6,
  T7, T8, T9, T10, T11, T12, T13a, T13b, T13c (15 tasks) is
  checked after its implementing PR lands. [AC32]
- *v2-libsecret stub:* the `## Cross-spec /
  outside-the-spec-tree` section retains the `v2 RFC: Linux
  libsecret tier` stub citing RFC-0006 § Unresolved Q1.
- *Lint:* `tools/lint-agents-md.sh` exits clean.

**Approach:**

- Walk through each task's AC closure: T1 closes AC1; T2 closes
  AC2; etc. Mark `[x]` per task as the implementation PR lands.
- The skill-secrets ROADMAP section was scaffolded in this spec
  PR (T0 — the spec itself, not a numbered plan task). T13c is
  the final close-out pass before the spec moves Draft → Shipped.

**Done when:** every task T1–T13c's row is checked; the `Last
updated` date at the top of backlog.md is bumped.

## Rollout

Definitional + spec PR (T1 + this spec): no production behaviour
changes; only documents land.

Implementation PRs (T2–T13): land incrementally, each behind no
flag. The first user-visible surface is `agentbundle creds setup`
in T8; prior to T8 the loader is library-only and not yet wired
into any skill. The worked example (T12) is the first credentialed
skill shipped from the catalogue; until then, no in-tree skill
declares `credentialed: true`.

No backwards-incompatibility: every change is additive (new
frontmatter keys are optional; new lint findings are reported,
not blocked; new CLI verb is opt-in by adopter invocation).

Reversal: every task in T2–T13 is single-PR-revertible. The
ADR-0002 amendment in T1 is a definitional change; reverting it
would require simultaneously reverting any skill or RFC that has
come to rely on the narrow definition. Treat the amendment as a
one-way door once T2 begins.

## Risks

- **ctypes silent-corruption in T5.** Wrong-sized struct fields on
  Windows return garbage rather than crashing. Mitigation:
  byte-equality round-trip tests on every field; explicit
  `assert sizeof(CREDENTIAL) == EXPECTED` against the documented
  Win32 layout.
- **macOS Keychain unlock prompt in T4 CI.** GitHub Actions
  `macos-latest` runners require the test Keychain to be unlocked
  via `security unlock-keychain` before `add-generic-password`
  works. Mitigation: the test fixture creates and unlocks a
  scratch keychain in `setup_module`; CI documents the password.
- **`tomllib` Python-version floor.** `tomllib` is stdlib only from
  Python 3.11. The repo's existing `agent-spec-cli` spec pins
  Python 3.11+, so this is not new — but confirm in T7 before
  importing.
- **Linux test matrix degradation.** Linux contributors testing
  T8's `setup` flow exercise only Tier 3, not Tier 2. The
  integration tests are platform-gated; a Linux-only contributor
  cannot verify the Tier-2 paths locally. Mitigation: CI matrix
  covers `ubuntu-latest`, `macos-latest`, `windows-latest`; reviews
  for T4 and T5 require a Darwin / Windows reviewer respectively.
- **Worked-example tracking the convention.** Every change to the
  "Don't" block in `add-credentialed-skill`'s assets must propagate
  to `example-credentialed-skill`'s SKILL.md verbatim. Mitigation:
  T12's integration test diffs the two and refuses on drift.
- **`conventions-check` slash-command shell-out parity.** The
  existing command body runs `tools/lint-*.sh` scripts; T10 adds a
  third. If a future contributor invokes the slash command via a
  non-Claude harness without re-reading the body, the lint may not
  fire. Mitigation: keep the slash command's body authoritative
  (the command lists every helper it shells out to) — same as the
  existing two.

## Changelog

- 2026-05-24: initial plan.
