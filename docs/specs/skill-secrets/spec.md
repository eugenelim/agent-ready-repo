# Spec: skill-secrets

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0006](../../rfc/0006-skill-secrets-storage.md)
  — sole driving RFC. Touches
  [ADR-0002](../../adr/0002-install-scope-per-pack-default-and-allowance.md)
  (amends § Consequences with the narrow "hook-shaped" definition this
  spec depends on) and the
  [`agent-spec-cli`](../agent-spec-cli/spec.md) spec
  (stdlib-only commitment; CLI subcommand surface).

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Make credential-bearing skills first-class citizens of the catalogue:
declare *where* credentials live, *who* reads them, and *what* a skill
is forbidden from doing with them, in a way that works on stock CPython
+ the OS the user already has (no `python-dotenv`, no `keyring`, no
third-party deps).

Concretely the implementing PRs deliver:

1. **A two-layer architecture rule** — skills do not hold credentials.
   A *credentialed primitive* (a Python module, an MCP server, or a CLI
   wrapper packaged as a primitive) owns the secret on disk and
   constructs the API call inside its own process; the LLM never sees
   cleartext as a tool argument. The architecture is enforced by prose
   in `CONVENTIONS.md`, by an author-facing template, and by
   `conventions-check` lint rules that flag the easy violations.

2. **A three-tier storage convention** — credentialed primitives
   resolve a secret in this order, first-hit-wins:
   - **Tier 1:** `<NAMESPACE>_API_TOKEN` env var (plus siblings
     `_BASE_URL`, `_EMAIL`, `_FLAVOR`).
   - **Tier 2:** OS keyring — macOS Keychain via
     `/usr/bin/security` subprocess (token via child stdin, never
     argv), `service = "agentbundle"`, `account = "<namespace>:<key>"`;
     Windows Credential Manager via in-process `ctypes` against
     `advapi32.{CredReadW, CredWriteW, CredDeleteW, CredFree}` with
     `CRED_TYPE_GENERIC`, `CRED_PERSIST_LOCAL_MACHINE`, target-name
     convention `agentbundle:<namespace>:<key>`, `UserName =
     "<namespace>"`.
   - **Tier 3:** dotfile at `~/.agentbundle/credentials.env`
     (`pathlib.Path.home()`-resolved), mode `0600` + parent `0700` on
     POSIX, DACL-verified via `icacls` on Windows. The fallback floor.

   Linux `libsecret` stays deferred to a v2 RFC; Linux lands on
   Tier 3 in v1.

3. **A stdlib-only loader and CLI verb** — `agentbundle.credentials`
   exposes `load_credentials(namespace, required_keys)` for
   primitive authors to import; `agentbundle creds` ships four
   subcommands (`setup`, `check`, `where`, `rm` — **no `get`**); both
   are stdlib-only (`getpass`, `os`, `pathlib`, `subprocess`,
   `argparse`, `tomllib`, `ctypes` on Windows).

4. **An argv ban and a `SKILL.md` "Don't" block** —
   credentialed-CLI-class primitives must refuse `--token`,
   `--api-token`, `--api-key`, `--bearer`, `--pat`, `--password`;
   MCP-server-class primitives may accept *header-naming* flags
   (`--bearer-header`, `--auth-header`, `--header-prefix`) but not
   value-shaped flags. Skills carry a verbatim "Don't" block in
   `SKILL.md`. Two optional frontmatter keys nested under the
   spec-blessed `metadata:` escape hatch (`metadata.credentialed: bool`,
   `metadata.primitive-class: credentialed-cli | mcp-server`) scope
   which rules apply; `tools/lint-agent-artifacts.sh` recognises them
   while the top-level allow-list stays aligned with
   [agentskills.io](https://agentskills.io/specification).

5. **An ADR-0002 amendment** freezing the narrow definition of
   "hook-shaped" (binds to runtime event AND requires wiring-merge into
   a hand-edited shared file) that this spec's architecture depends
   on — credentials qualify on neither prong, so the user-scope ban
   does not apply.

6. **A worked example and a how-to guide** — `example-credentialed-skill`
   ships under `packs/core/.apm/skills/` as a runnable no-op
   credentialed skill (imports `agentbundle.credentials`, ships a
   `creds-schema.toml`, embeds the "Don't" block);
   `docs/guides/how-to/add-a-credentialed-skill.md` walks adopters
   through writing their own.

7. **An author skill carrying the template variants** —
   `packs/core/.apm/skills/add-credentialed-skill/assets/credentialed-skill-SKILL.md`
   holds the copy-paste "Don't" block in two labeled variants
   (credentialed-cli, mcp-server); authors copy the variant matching
   their `primitive-class`.

Success looks like: a fixture pack carrying a credentialed primitive
loads its token from any of the three tiers across macOS and Windows,
the `agentbundle creds setup <namespace>` flow writes to the right
tier and reports it on stderr, `conventions-check` reports a finding
on a fixture skill missing its "Don't" block, and `make build-check`
exits clean with the convention documented in the seed-side upstream
of `docs/CONVENTIONS.md` (per [`docs/CONVENTIONS.md` § Pack
source-of-truth split](../../CONVENTIONS.md#pack-source-of-truth-split)
— direct edits to the projected path are bounced by the gate).

## Boundaries

The three-tier guard that keeps an implementing agent inside the
lines. *Always do* applies without asking; *Ask first* requires
human sign-off before proceeding; *Never do* is a hard rule, even
under time pressure.

### Always do

- **Stdlib only.** All credential-handling code (`agentbundle.credentials`,
  the `.env` parser, the `agentbundle creds` verb, per-platform Tier-2
  backends) uses stdlib modules exclusively (`os`, `pathlib`,
  `subprocess`, `getpass`, `argparse`, `tomllib`, `ctypes` on
  Windows). Inherits the
  [`agent-spec-cli` spec § Library-first](../agent-spec-cli/spec.md)
  constraint.
- **Run the gates** (`make build-check`) before declaring any task
  done, even for markdown-only edits. Self-hosted files mean
  unintended drift between `packs/core/seeds/` and `<repo>/` surfaces
  here.
- **Use fixture credentials and a redirected `$HOME` for every test.**
  Tests never touch the developer's real `~/.agentbundle/credentials.env`,
  real macOS Keychain, or real Windows Credential Manager. Tests set
  `$HOME` to a `tmp_path`-scoped directory; Tier-2 round-trips on
  Windows use a target-name prefix that includes the test's
  `tmp_path` hash so a flaky test cannot collide with a developer's
  real entries.
- **Tokens enter child processes via stdin or environment, never via
  argv.** The macOS Tier-2 backend uses
  `subprocess.Popen(stdin=PIPE)` + `proc.communicate(input=token.encode())`
  against `/usr/bin/security`'s `-w` prompt mode. The Windows Tier-2
  path uses in-process `ctypes` so token bytes never cross a process
  boundary at all.
- **Announce the resolved tier on stderr** after every `setup` or
  `check` operation. The `gh` CLI policy (see RFC-0006 § 2 Tier 2 —
  cited issue `cli/cli #10108`) — silent degradation defeats the
  posture the user chose.
- **Cite RFC-0006 by section name** in any spec amendment, ADR, or
  guide so the durable rationale stays discoverable from the
  implementation.
- **Edit projected paths through their seed upstream.** `docs/CONVENTIONS.md`
  and any other path under `make build-check`'s gate is edited via
  `packs/core/seeds/docs/CONVENTIONS.md` (etc.), then `make build-self`
  regenerates the projected copy. See
  [`docs/CONVENTIONS.md` § Pack source-of-truth split](../../CONVENTIONS.md#pack-source-of-truth-split).

### Ask first

- **Changing the canonical dotfile path** (`~/.agentbundle/credentials.env`).
  Once shipped, this is a breaking change; RFC-0006 § Drawbacks lists
  three specifically-foreclosed alternatives (per-namespace file
  layout; XDG variant; per-primitive path) — moving to any of them
  needs an RFC amendment.
- **Changing the tier order** (env → keyring → dotfile). The order is
  the gh-CLI-shaped consensus the RFC adopted; reordering needs
  review against the corporate-package constraints (Tier 1 is the only
  composable path for Vault Agent / `op run --` wrappers).
- **Adding a `get` subcommand** to `agentbundle creds` (writing the
  cleartext token to stdout). RFC-0006 § 5 explicitly rejects this in
  v1 as the "wrap-and-leak" shape; a future `creds export` writing
  to a *file* (mode 0600) is a separate RFC.
- **Renaming any of the two new SKILL.md frontmatter keys**
  (`credentialed`, `primitive-class`). They're consumed by
  `tools/lint-agent-artifacts.sh` and by `conventions-check`; renaming
  requires updating every credentialed skill in lockstep. The keys
  live under the `metadata:` escape hatch (per the agentskills.io
  spec's top-level allow-list) as `metadata.credentialed` and
  `metadata.primitive-class`; nesting under `metadata:` is **not** a
  rename and does not invoke this rule.
- **Adding a Linux Tier-2 backend** (`libsecret`). RFC-0006 § 2 defers
  this to a v2 RFC alongside an adopter-profile audit; adding it in
  this spec doubles the test matrix and re-opens the deferral.

### Never do

- **No new top-level dependency.** Stdlib only, per RFC-0006 §
  Motivation (corporate package gates). No `python-dotenv`, no
  `keyring`, no `pywin32`, no `requests`. The Windows Tier-2 path
  uses `ctypes` against `advapi32.dll` which is in every Windows
  install; the macOS path shells out to `/usr/bin/security` which
  is in every macOS install. If a tier needs a third-party module to
  work, the tier is rejected.
- **No new top-level directory.** All new runtime code lives under
  `packages/agentbundle/agentbundle/creds/` (library — loader,
  per-platform Tier-2 backends, schema parser, exceptions) and
  `packages/agentbundle/agentbundle/commands/creds.py` (CLI
  dispatcher — matches the existing sibling-verb convention at
  `agentbundle/commands/{install,uninstall,upgrade,...}.py`). The
  `agentbundle` public shim — added so credentialed-primitive
  authors can `from agentbundle.credentials import load_credentials`
  per RFC-0006 § 5 — lives at `packages/agentbundle/agentbundle/`
  and is the **only** new public Python import root; further roots
  need an RFC. New tests under `packages/agentbundle/tests/`; new
  fixtures under `packages/agentbundle/tests/fixtures/creds/`.
- **No `agentbundle creds get` subcommand.** Anything that prints a
  token to stdout enables `subprocess.check_output(['agentbundle',
  'creds', 'get', ...])` inside a skill, defeating the architecture
  rule. The CLI has four verbs: `setup`, `check`, `where`, `rm`.
- **No token on argv, anywhere.** Not in `agentbundle creds setup`'s
  own argv (the helper refuses to accept tokens via `--token`-shaped
  flags), not in subprocess calls the helper makes (macOS uses child
  stdin; Windows uses in-process ctypes), not in primitive scripts
  (the lint refuses the flag names).
- **No silent fallback from hard-fail Win32 error codes.**
  `ERROR_NOT_FOUND` (1168) falls through to Tier 3 — that's the
  "no credential exists" case. `ERROR_NO_SUCH_LOGON_SESSION` (1312),
  `ERROR_INVALID_FLAGS` (1004), `ERROR_LOGON_FAILURE` (1326) **hard
  fail** with stderr naming the cause. Silently degrading defeats
  the security posture the user chose.
- **No live writes to the developer's `~/.agentbundle/`, Keychain, or
  Credential Manager from tests or CI.** Every test sets `$HOME` to
  `tmp_path`; every Windows Credential Manager round-trip uses a
  `tmp_path`-derived target-name prefix; macOS Keychain tests are
  skipped on non-Darwin CI, run only against a `tmp_path`-scoped
  Keychain via `security create-keychain` when on Darwin (see
  Construction tests below).
- **No skill reads the dotfile directly.** Only credentialed primitives
  do. Skills shell out to or import the primitive; they never
  `open(os.path.expanduser("~/.agentbundle/credentials.env"))`. The
  lint catches the obvious cases; the architectural rule covers the
  obfuscated ones.
- **No `SSL_VERIFY=False` / `verify=False` defaults** in any
  credentialed primitive shipped from this catalogue. `--insecure`
  is opt-in only and emits a stderr warning. (Inherited from RFC-0006
  § 7; this spec wires the lint.)

## Testing Strategy

Three verification modes mapped per Objective behavior:

- **TDD** for everything with a compressible invariant: the stdlib
  `.env` parser (CRLF strip; quoted values; comments; equals-in-value),
  the precedence resolver, per-platform Tier-2 byte-equality
  round-trips, the Win32 error-code dispatch matrix, the dotfile
  atomic-write contract, the `creds-schema.toml` parser, and the lint
  rule outputs. Construction tests live in
  `packages/agentbundle/tests/unit/test_credentials*.py` and
  `packages/agentbundle/tests/integration/test_creds_cli.py`. The
  contract-shaped examples in RFC-0006 (e.g. "token via child stdin,
  not argv"; "byte-equality round-trip on `CredentialBlob`") map to
  construction tests one-to-one.

- **Goal-based check** for the schema additions and the worked
  example. JSON-schema validation of the SKILL.md frontmatter
  extensions passes/fails as a shell check
  (`tools/lint-agent-artifacts.sh` exits 0). The worked example
  `example-credentialed-skill` exercises a smoke path
  (`agentbundle render` projects it; `tools/lint-agent-artifacts.sh`
  accepts its frontmatter; the `add-credentialed-skill` author skill
  ships both template variants in its `assets/` folder; the
  `conventions-check` extensions report the expected findings on a
  malformed fixture skill).

- **Visual / manual QA** for the Windows-specific behaviors GitHub
  Actions cannot exercise. The RFC pins the buckets (RFC-0006 §
  Drawbacks "Windows test matrix grows substantially") and this spec
  inherits them:
  - `getpass.getpass` real-tty refusal (GH runners don't allocate a
    PTY; unit test monkeypatches `sys.stdin.isatty`, real tty path is
    manual-QA).
  - `CRED_PERSIST_LOCAL_MACHINE` survives-logoff semantics (CI is a
    single session; manual-QA row).
  - `ERROR_NO_SUCH_LOGON_SESSION` under `LocalSystem` service-account
    context (needs scheduled-task runner CI doesn't provide;
    manual-QA row).

  Each manual-QA row carries a release-checklist line in
  [`docs/product/release-checklist.md`](../../product/release-checklist.md)
  under the `skill-secrets` section.

**Construction tests inline the parser inputs** via `tmp_path` heredocs
rather than checked-in fixture files. The two parser shapes that
demand a fixture-tree share (the `conventions-check` skill fixtures,
which the walker discovers by path) live under
`packages/agentbundle/tests/fixtures/creds/skills/`; everything else
(schema TOMLs, valid / quoted / CRLF / comment dotfile shapes) is
constructed in the test body so the corpus stays self-describing
under the orphan-fixture walker (AC34):

- **Inlined via `tmp_path`:** schema-valid and schema-missing-required
  TOMLs, the four parser-shape dotfiles
  (`dotfile-valid` / `dotfile-quoted` / `dotfile-crlf` /
  `dotfile-comment`). The full text appears in the test that exercises
  it; no orphan-fixture risk.
- **Checked-in under `tests/fixtures/creds/`:** the four
  `conventions-check` skill fixtures —
  `skills/conforming/`,
  `skills/missing-dont-block/`,
  `skills/argv-flag/scripts/cli.py`,
  `skills/dotfile-grep/scripts/leak.py` — because the lint walker
  resolves them by directory path during its scan.

Every Acceptance Criterion below maps to at least one
construction-test or fixture exercise.

## Acceptance Criteria

ADR amendment (lands in the spec PR, not a follow-up):

- [x] **AC1.** `docs/adr/0002-install-scope-per-pack-default-and-allowance.md`
      carries an `## Amendments` section whose first sub-heading is
      `### 2026-05-24 — Narrow definition of "hook-shaped" (per RFC-0006)`
      and whose body contains the verbatim conjunction phrasing
      *"(i) binds to a runtime event AND (ii) requires wiring-merge
      into a hand-edited shared file ... a primitive that satisfies
      only one of (i) or (ii) is **not** hook-shaped under this
      definition and is governed by its own RFC, not the ban in this
      ADR."* `tools/lint-agents-md.sh` resolves every internal link
      added by the amendment.

Stdlib parser and loader API:

- [x] **AC2.** A stdlib `.env` parser in
      `packages/agentbundle/agentbundle/creds/loader.py` accepts
      `KEY=value`, `KEY="value with spaces"`, `# comment` lines, blank
      lines; strips trailing `\r\n` / `\n` from the **line tail
      only**, outside any quoted value (so `KEY="a\rb"` parses to
      `{"KEY": "a\rb"}` — the `\r` inside the quotes is preserved);
      refuses `export KEY=value`, refuses variable expansion
      (`KEY=$OTHER`), refuses multi-line quoted values (a quoted
      value spanning two physical lines is a parse error).
- [x] **AC3.** `agentbundle.credentials.load_credentials(namespace,
      required_keys)` returns an immutable `Credentials` object
      whose attribute access returns the resolved values; missing
      required keys raise `CredentialsMissingError` naming the
      namespace and the missing keys. The function is the only public
      entry point primitive authors import.
- [x] **AC4.** Precedence is **Tier 1 (env) → Tier 2 (keyring) → Tier 3
      (dotfile)** per key, first-hit-wins. A key resolved at Tier 1 is
      not re-checked at lower tiers; mixing tiers across keys within
      one namespace is permitted (one key from env, another from
      keyring, another from dotfile is a valid resolution).
- [x] **AC4b.** **Tier-2 backend dispatch is platform-discriminated at
      module-load time.** The loader imports
      `_keychain_macos` iff `sys.platform == "darwin"`,
      `_credman_windows` iff `sys.platform == "win32"`, and no
      Tier-2 backend on other platforms (Tier 2 is unavailable by
      absence; resolver falls through directly to Tier 3). The dispatch
      is verified by a test that monkeypatches `sys.platform` and
      reloads the module.
- [x] **AC4c.** `agentbundle.credentials.load_credentials` is reachable
      from an installed wheel. Verified by `pip install
      packages/agentbundle` followed by
      `python -c "from agentbundle.credentials import load_credentials"`
      exiting 0 in a clean virtualenv on each CI platform. The
      `agentbundle` shim package is included by
      `packages/agentbundle/pyproject.toml`'s
      `[tool.setuptools.packages.find] include` list.

Tier 1 (env var):

- [x] **AC5.** Reading `<NAMESPACE>_API_TOKEN` (and any sibling key
      declared in `creds-schema.toml`, e.g. `_BASE_URL`, `_EMAIL`,
      `_FLAVOR`) from `os.environ` returns the value. Empty-string env
      var counts as unset and falls through to Tier 2.

Tier 2 (macOS Keychain):

- [x] **AC6.** On Darwin, the Tier-2 read path shells out to
      `/usr/bin/security find-generic-password -s "agentbundle" -a
      "<namespace>:<key>" -w` and captures stdout; the write path uses
      `add-generic-password -U -s "agentbundle" -a "<namespace>:<key>"
      -w` with the token written to the child's stdin via
      `subprocess.Popen(stdin=PIPE)` + `proc.communicate(...)`. **The
      token never appears in argv**; a fixture test exercises a
      `psutil`-shaped argv inspection during the call and asserts the
      token bytes are absent.
- [x] **AC7.** Round-trip: write a value, read it, compare bytes; the
      stored value matches the input.
- [x] **AC8.** The `_keychain_macos` backend module is **not imported**
      when `sys.platform != "darwin"` (per AC4b). A loader-level test
      sets `sys.platform = "linux"`, reloads
      `agentbundle.credentials`, and asserts the macOS backend
      module is absent from `sys.modules`; the resolver falls through
      from Tier 2 to Tier 3 without raising.

Tier 2 (Windows Credential Manager):

- [x] **AC9.** On Windows, the Tier-2 read/write/delete path calls
      `ctypes.windll.advapi32.CredReadW(target, type, flags,
      &credential_ptr)`, `CredWriteW(&credential, flags)`,
      `CredDeleteW(target, type, flags)`, and `CredFree(ptr)` against
      a `CREDENTIAL` struct built in-process with
      `Type = CRED_TYPE_GENERIC (1)`,
      `Persist = CRED_PERSIST_LOCAL_MACHINE (2)`,
      `TargetName = "agentbundle:<namespace>:<key>"`,
      `UserName = "<namespace>"`,
      `CredentialBlob` pointing at the UTF-16-encoded token bytes,
      `CredentialBlobSize = len(token_utf16_bytes)`. All other
      `CREDENTIAL` fields (`Flags`, `Comment`, `LastWritten`,
      `AttributeCount`, `Attributes`, `TargetAlias`) zero-initialised
      via `ctypes.Structure` defaults.
- [x] **AC10.** Round-trip: write a value, read it, **byte-equality**
      assertion against the UTF-16-encoded original. Test runs on
      `windows-latest` GitHub Actions.
- [x] **AC11.** Win32 error-code dispatch matrix:
      `ERROR_NOT_FOUND (1168)` → return `None`, resolver falls through
      to Tier 3;
      `ERROR_NO_SUCH_LOGON_SESSION (1312)` → raise
      `Tier2HardFailError` naming the cause; resolver **does not**
      fall through;
      `ERROR_INVALID_FLAGS (1004)` → raise `Tier2HardFailError`
      naming the offending flag value;
      `ERROR_LOGON_FAILURE (1326)` → raise `Tier2HardFailError`
      naming DPAPI key-derivation failure.
- [x] **AC12.** The `_credman_windows` backend module is **not
      imported** when `sys.platform != "win32"` (per AC4b). Parallel
      test to AC8 with `sys.platform = "linux"`; the Windows backend
      module is absent from `sys.modules`.

Tier 3 (dotfile):

- [x] **AC13.** Path resolves to `pathlib.Path.home() /
      ".agentbundle" / "credentials.env"` on every platform.
- [x] **AC14.** Write path is atomic: `tempfile.mkstemp` in the target
      directory → `os.write` → `os.replace`. A mid-write read sees
      either the prior file contents or the new contents, never
      partial.
- [x] **AC15.** On POSIX (`os.name == "posix"`), the helper calls
      `os.chmod(path, 0o600)` on the file. The parent directory
      `~/.agentbundle/` is **shared** with RFC-0004 install state
      (`state.toml`) and the `adapt-to-project` marker — the
      credentials helper **does not** unconditionally chmod the
      parent. Instead: if the parent does not yet exist, it is
      created with `mkdir(mode=0o700)`; if it already exists, the
      helper reads `parent.stat().st_mode` and warns on stderr if
      the mode is more permissive than `0o755`, but does **not**
      rewrite it. On Windows the helper **does not** call
      `os.chmod` and instead runs `icacls <path>` after creation,
      parses the output, and refuses if any non-default ACE grants
      read access unless `--allow-permissive-acl` was passed at
      setup time.

CLI verb `agentbundle creds`:

- [x] **AC16.** `agentbundle creds setup <namespace>` reads the
      namespace's required keys from `creds-schema.toml`, prompts via
      `getpass.getpass` (guarded by `sys.stdin.isatty()` — refuses
      non-tty with stderr), writes to the highest-available tier
      (keyring on Darwin/Windows; dotfile on Linux or when
      `--allow-insecure-fallback` is passed), and announces the
      resolved tier on stderr. Three distinct stderr messages
      identify which posture the helper landed on:
      `"wrote to keyring (<tier-2-backend>)"` on Darwin/Windows
      Tier 2; `"wrote to dotfile (Linux — Tier 2 deferred to v2
      RFC)"` on Linux (no opt-out involved); `"wrote to dotfile
      (insecure fallback)"` on Darwin/Windows when
      `--allow-insecure-fallback` was passed. A log reader can
      distinguish platform-deferred Tier 3 from opt-out Tier 3
      without further context.
- [x] **AC17.** `agentbundle creds setup` (no positional namespace
      argument) walks both scope state files
      (`<repo>/.agentbundle-state.toml` and
      `~/.agentbundle/state.toml`) for installed primitives whose
      `SKILL.md` frontmatter declares `metadata.credentialed: true`
      (nested under the agentskills.io-spec `metadata:` escape
      hatch), prints the list, and prompts for a selection. Same
      dual-scope walk shape as `adapt-to-project`. The walk uses the
      **existing** `PackState.files` table (no state-schema bump):
      for each `(pack, relpath)` whose relpath matches the regex
      `^\.claude/skills/[^/]+/SKILL\.md$` (or the equivalent
      adapter-specific projection for non-Claude adapters), the CLI
      opens `<scope-root>/<relpath>`, reads its YAML frontmatter,
      and includes the skill in the list iff
      `metadata.credentialed: true`.
      The CLI then resolves the selected primitive's schema via the
      canonical convention pinned in AC24b and exits non-zero with
      a clear stderr error if the file is absent.
- [x] **AC18.** `agentbundle creds check <namespace>` exits 0 when
      the namespace's required keys all resolve, exit 2 when any is
      missing (stderr names the missing keys), exit 3 for other
      errors (unparseable schema, Tier-2 hard-fail).
- [x] **AC19.** `agentbundle creds where <namespace>` prints, per
      required key, the tier each one resolved at (`env`, `keyring`,
      `dotfile`, or `missing`). Does not print the value.
- [x] **AC20.** `agentbundle creds rm <namespace>` deletes every key
      in the namespace from every tier that holds it (env clears are
      a no-op the helper documents on stderr; keyring deletes via the
      per-platform backend; dotfile rewrites without those keys). The
      helper refuses with stderr if no tier holds any of the
      namespace's keys.
- [x] **AC21.** No `agentbundle creds get` subcommand exists. A
      negative test asserts `agentbundle creds get foo` exits non-zero
      with `unknown command: get` on stderr.
- [x] **AC22.** `agentbundle creds setup --allow-insecure-fallback` on
      a Tier-2-capable box writes to Tier 3 and exits 0; without the
      flag, falling back to Tier 3 on a Tier-2-capable box exits
      non-zero with stderr naming the reason. On Linux the helper
      writes to Tier 3 unconditionally and the flag is a no-op.
      The "is the box Tier-2-capable" detection follows a per-platform
      exit-code matrix:
      - **macOS** (parallel to AC11's Win32 matrix): `/usr/bin/security`
        exit `0` → success; `44` (`errSecItemNotFound`) → falls
        through to Tier 3 as legitimate "no credential"; `45`
        (`errSecDuplicateItem`) on add → upsert with `-U` (already
        passed) succeeded; `25308` (`errSecInteractionNotAllowed`)
        or `-25291` (`errSecNotAvailable`) — Keychain locked or
        unavailable — **hard fail** unless
        `--allow-insecure-fallback` was passed. Any other non-zero
        exit code is a hard fail with stderr naming the `security`
        exit code.
      - **Windows**: the Win32 matrix in AC11 governs (`ERROR_NOT_FOUND`
        → Tier 3 fallthrough; everything else listed → hard fail).
- [x] **AC23.** The helper refuses to read the token from **its own**
      stdin when not a tty, from argv, from env, or from a pipe.
      Tokens enter through the interactive `getpass` prompt or
      nowhere; the helper exits non-zero in every other case. The
      argv-refusal is implemented by **tombstone arguments**: the
      argparse subparser registers `--token`, `--api-token`,
      `--api-key`, `--bearer`, `--pat`, `--password` as known flags
      whose action is a custom `_RefuseTokenArgvAction` that prints
      the literal string `tokens cannot be passed via argv`
      (verbatim; this exact byte sequence is the canonical anchor;
      T8 tests grep for it) to stderr and exits non-zero.
      This guarantees the documented stderr text for AC23's tests
      (not argparse's default `unrecognized arguments:` message).
      The tombstone registration is **scoped to the `creds setup`
      subparser only**; it does not pollute other `agentbundle`
      verbs.
      The tty refusal is **POSIX-tested**: `sys.stdin.isatty()`-shaped
      assertions run on Darwin and Linux CI via
      `stdin=subprocess.DEVNULL`. The Windows tty-refusal path is a
      manual-QA row (§ Testing Strategy) — GitHub `windows-latest`
      runners do not allocate a PTY for job steps, and `msvcrt.getwch`
      reads regardless of `isatty()` on Windows; a real-terminal test
      is part of release.

`creds-schema.toml` format:

- [x] **AC24.** `creds-schema.toml` declares the namespace's required
      keys with shape:
      ```toml
      [namespace]
      name = "jira"
      [[namespace.keys]]
      name = "API_TOKEN"
      label = "Jira API token"
      secret = true
      [[namespace.keys]]
      name = "BASE_URL"
      label = "Jira instance base URL"
      secret = false
      ```
      The loader parses this with `tomllib`; `secret = true` keys are
      hidden via `getpass`, `secret = false` keys are prompted via
      `input()`.
- [x] **AC24b.** **Canonical schema path:** a credentialed primitive's
      schema lives at `<skill-dir>/references/creds-schema.toml`
      where `<skill-dir>` is the projected skill directory (e.g.
      `.claude/skills/<name>/`). The CLI resolves the path by walking
      the relevant `PackState.files` table for an entry whose relpath
      matches `^\.claude/skills/[^/]+/SKILL\.md$` (the projected
      SKILL.md), taking its parent directory, and joining
      `references/creds-schema.toml`. The resolution uses the
      **existing** v0.3 state-file schema — no new fields are added.
      `load_credentials(namespace, required_keys)` is *resolution
      only* — schema concerns (validating `required_keys` against
      the schema's declared keys, prompting, secret/non-secret
      labels) live in the `agentbundle creds setup` / `creds check`
      CLI surface, not on the loader's signature. Primitive code is
      not expected to validate against the schema at load time; the
      `creds check` verb is the canonical way to surface a
      schema/required-keys mismatch.

Conventions and lint:

- [x] **AC25.** `tools/lint-agent-artifacts.sh` enforces the
      [agentskills.io](https://agentskills.io/specification)
      top-level frontmatter allow-list (`name`, `description`,
      `license`, `compatibility`, `metadata`, `allowed-tools`) and
      recognises `credentialed` (boolean) and `primitive-class`
      (string: `credentialed-cli` | `mcp-server`) nested under the
      spec's `metadata:` escape hatch. Schema refuses other values
      for `metadata.primitive-class`; absence of `metadata.credentialed`
      (or of `metadata:` entirely) means the skill is not credentialed
      and the lint skips the credentialed-specific checks.
- [x] **AC26.** `packs/core/.apm/commands/conventions-check.md`
      extends to report three credentialed-skill findings:
      (a) `metadata.credentialed: true` skill missing the verbatim
      "Don't" block under a `### Security rules (non-negotiable)`
      heading;
      (b) for `primitive-class = "credentialed-cli"`: any script under
      the primitive's `scripts/` directory accepts a normalised flag
      name matching `{token, api_token, api_key, bearer, pat,
      password}` in `argparse.ArgumentParser.add_argument` calls;
      (c) any script under a skill's `scripts/` directory contains
      the substring `.agentbundle/credentials.env` without the opt-out
      comment marker (`# credentialed-primitive: reads-creds-directly`)
      on the same line. The lint exits non-zero on any finding so
      `conventions-check` blocks merges that introduce a credentialed-
      skill convention drift; `tools/lint-credentialed-skills.sh` and
      `docs/CONVENTIONS.md` § Credentialed skills are the canonical
      reflection of this behavior.
- [x] **AC27.** Normalisation rule for AC26(b): strip leading `-`,
      casefold, replace `-` with `_`; matches defeat trivial
      obfuscation (`"--" + "token"`, `--Token`, `--api-Key`).

Templates and worked example:

- [x] **AC28.** A new author skill at
      `packs/core/.apm/skills/add-credentialed-skill/` ships with a
      `SKILL.md` (triggering on "add a credentialed skill", "new
      credentialed primitive") and an `assets/credentialed-skill-SKILL.md`
      template carrying **both labelled variants** —
      `### Variant: credentialed-cli` (full storage convention +
      argv ban) and `### Variant: mcp-server` (header-naming flags
      allowed; storage convention does not apply). Authors copy the
      variant matching their `primitive-class`. The path
      `packs/core/.apm/skills/add-credentialed-skill/assets/` is the
      canonical landing pinned by this spec, replacing the
      pre-amendment path named in
      [RFC-0006 § Amendments](../../rfc/0006-skill-secrets-storage.md#amendments).
- [x] **AC29.** A worked example at
      `packs/core/.apm/skills/example-credentialed-skill/` ships with:
      a `SKILL.md` declaring `metadata.credentialed: true` and
      `metadata.primitive-class: credentialed-cli` (nested under the
      agentskills.io-spec `metadata:` escape hatch), embedding the
      credentialed-CLI "Don't" block verbatim; a `scripts/cli.py`
      importing `agentbundle.credentials` and refusing the argv-ban
      flags; a `references/creds-schema.toml` declaring `API_TOKEN`
      (`secret = true`, required) and `BASE_URL` (`secret = false`,
      a sibling key in the spec § Objective sense — also resolved
      through the three-tier ladder and consumed by `cli.py`); the
      skill passes both `tools/lint-agent-artifacts.sh` and the
      extended `conventions-check`.

Adapter portability (RFC-0011 / pack-allowed-adapters):

- [x] **AC29b.** `packs/core/.apm/skills/add-credentialed-skill/SKILL.md`
      (and its projected `.claude/skills/...` copy) carries an
      `## Adapter portability — [pack.install] allowed-adapters`
      section naming the three currently-admitted user-scope-capable
      values (`claude-code`, `kiro`, `codex`) and the catalogue's
      `atlassian` / `figma` packs' declaration as the reference
      example. No change to credential loading (AC3 untouched). The
      migration walkthrough lives at
      `docs/guides/how-to/v05-to-v06-pack-upgrade.md`.

Conventions, guide, roadmap:

- [x] **AC30.** The **seed-side upstream** of `docs/CONVENTIONS.md` at
      `packs/core/seeds/docs/CONVENTIONS.md` gains a top-level
      `## Credentialed skills` section naming the two-layer
      architecture rule, the three storage tiers, the argv ban, the
      anti-pattern register from RFC-0006 § 6, and the
      corporate-network requirements from RFC-0006 § 7
      (`HTTPS_PROXY`/`NO_PROXY` honored; system trust store via
      `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`/`SSL_CERT_DIR`;
      `--insecure` opt-in only). Each subsection links back to
      RFC-0006 by anchor. The projected `docs/CONVENTIONS.md` is
      regenerated by `make build-self`; direct edits to the
      projected path are bounced by `make build-check` (AC33).
- [x] **AC31.** A Diátaxis how-to at
      `docs/guides/how-to/add-a-credentialed-skill.md` walks an
      adopter through writing a credentialed primitive end-to-end:
      pick a namespace; write the schema; import the loader; embed
      the "Don't" block; declare frontmatter; run `setup`; run
      `check`. References the worked example.
- [x] **AC32.** `docs/ROADMAP.md` carries a `## skill-secrets` section
      replacing the previous cross-spec stub. Entries close
      incrementally **per task** following the existing ROADMAP
      grouping convention (one bullet per task / AC range, not one
      bullet per AC); per-AC checkbox state is read from `spec.md`,
      not duplicated. The `v2-libsecret` stub citing RFC-0006 §
      Unresolved Q1 lives under the existing
      § *Cross-spec / outside-the-spec-tree*.

Verification:

- [x] **AC33.** `make build-check` exits clean with the amendments
      applied (no drift between `packs/core/seeds/` and `<repo>/`).
- [x] **AC34.** Every fixture file under
      `packages/agentbundle/tests/fixtures/creds/` and every fixture
      skill under `packages/agentbundle/tests/fixtures/creds/skills/`
      is referenced by path in at least one test under
      `packages/agentbundle/tests/`. An orphan-fixture detection
      check (a test that walks the fixtures tree and asserts each
      file's relative path appears as a substring in the test corpus)
      is part of the suite (`tests/unit/test_credentials_fixtures.py`).
- [x] **AC35.** No test or CI step writes to the developer's real
      `~/.agentbundle/`, real macOS Keychain (verified by checking
      no Keychain entry persists outside a `tmp_path`-scoped
      Keychain), or real Windows Credential Manager (verified by
      target-name prefix isolation against a `tmp_path` hash). The
      posture is enforced as a static-analysis assertion at
      `tests/unit/test_credentials_no_live_writes.py`: every backend's
      integration test file must contain the documented isolation
      anchor (`SERVICE` / `SERVICE_PREFIX_OVERRIDE` monkeypatch),
      and dotfile tests must redirect `$HOME`.


## Changelog

- **2026-05-26 amendment (credential-broker-contract):** AC34 and AC35 inheritance invariants — that credentialed-skill primitives never see a credential leak through a parent process's environment, and that the loader's API never returns a credential type weaker than `Credentials` — now apply to the vendored `credentials_shim` import surface projected by the `shared-libs/` build-pipeline primitive class, not to the removed `agentbundle.credentials` PyPI module. The migration is byte-equivalent modulo the enumerated import-path deltas in `docs/specs/credential-broker-contract/spec.md` AC6; the inheritance invariants are unchanged. See [`docs/specs/credential-broker-contract/spec.md`](../credential-broker-contract/spec.md).
