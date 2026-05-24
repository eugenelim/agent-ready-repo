# RFC-0006: Credential storage for credentialed skills

- **Status:** Accepted
- **Author:** eugenelim
- **Date opened:** 2026-05-24
- **Date closed:** 2026-05-24
- **Related:**
  [ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md)
  (user-scope mechanics). The ADR's
  [user-scope hook-primitive ban](../adr/0002-install-scope-per-pack-default-and-allowance.md#consequences)
  uses the phrase *"hook-shaped primitives"* without further
  definition. This RFC adopts the **narrow reading** — binds to
  runtime events AND requires wiring-merge into a hand-edited
  shared file — faithful to the precedent
  [RFC-0005](0005-user-scope-hook-support.md) sets (the entire
  design surface of RFC-0005 is the merge-into-shared-settings-file
  mechanic; the load-bearing question was always the merge
  problem, not path ownership). Under the narrow reading,
  credentials are out of scope of the ban. § Follow-on artifacts
  commits to an ADR-0002 amendment that freezes this definition.
- **Related:**
  [`docs/CONVENTIONS.md`](../CONVENTIONS.md) — accepting this RFC
  introduces a new top-level section ("Credentialed skills") naming
  the storage tiers and the argv ban.

## Summary

Skills that need a secret today have no convention to follow *in
this catalogue*. The leading repos we surveyed (`gh` CLI,
`sooperset/mcp-atlassian`, `dropkit`, `langpingxue/atlassian-skills`,
the official Atlassian remote MCP) have already converged on a
narrow set of patterns — env-var override, OS keyring where
available, dotfile floor, argv ban — but the catalogue itself has
not adopted any of them. This RFC adopts the consensus shape with
two adjustments (stdlib-only loader; two-layer "skills don't hold
credentials" architecture) for `agent-ready-repo`.

The proposal is **two-layer**:

1. **Architecture rule.** Skills do not hold credentials. A
   *credentialed primitive* (an MCP server, a CLI wrapper, or a
   broker subprocess that ships from a pack) holds the secret on
   disk and hands the cleartext to the API call inside its own
   process. The LLM never sees the secret as a tool argument.

2. **Storage rule (gh-CLI-shaped, stdlib-only).** Credentialed
   primitives read credentials by precedence: explicit
   environment variable → OS keyring (macOS Keychain via
   `/usr/bin/security`; Windows Credential Manager via `ctypes` +
   `advapi32.CredReadW`/`CredWriteW`; Linux `libsecret` phased) →
   dotfile at `~/.agent-ready/credentials.env` (resolved via
   `pathlib.Path.home()`), mode 0600 on POSIX, DACL-restricted on
   Windows. Acquisition is an interactive Python stdlib script
   shipped from the `core` pack, never invoked by the LLM. Argv
   delivery is forbidden.

The tooling concretely is: one CLI verb (`agentbundle creds` —
subcommands `setup`/`check`/`where`/`rm`, no `get`), a stdlib-only
loader (`agent_ready.credentials`) with per-platform Tier-2
backends (macOS `/usr/bin/security` via subprocess; Windows
Credential Manager via `ctypes` + `advapi32.CredReadW`/`CredWriteW`),
a stdlib `.env` parser, one `SKILL.md` snippet under
`docs/_templates/`, `conventions-check` rule extensions (refuses
`--token`/`--api-key`/`--bearer`/`--pat`/`--password` flags in
credentialed-primitive scripts and warns when the SKILL.md "Don't"
block is missing), and one new section in `CONVENTIONS.md`. No new
top-level pack; the helper and verb land in `core`. macOS Keychain and Windows
Credential Manager are both implemented as Tier-2 backends in v1
(stdlib only); Linux `libsecret` is the one deferred tier.

## Motivation

The cost of inaction is concrete and accumulating.

**There is no answer to "where do I put the secret?" today.** The
session that produced this RFC started because a credential-bearing
skill (an internal Jira / Confluence wrapper) had no convention to
follow. `docs/CONVENTIONS.md` does not mention secrets, none of the
five accepted specs do, and ADR-0002 establishes the user-scope
*directory* (`~/.agent-ready/`) but says nothing about what may live
in it. Every new credentialed skill is a re-invention; the
re-inventions will diverge.

**Corporate-package constraints rule out the obvious off-the-shelf
answers.** The adopters this catalogue exists for are running
agent toolchains inside locked-down environments where
`pip install python-dotenv` or `pip install keyring` is a
ticket, an internal-mirror gate, or a hard no. The convention has
to work on stock CPython + the OS the user already has. That rules
out the path most third-party skill catalogues (including dropkit)
walked.

**Skills run as the user and can grep the dotfile.** The biggest
worry is not at-rest theft; it is that a credentialed skill running
under an agent harness can `cat ~/.agent-ready/credentials.env`
and surface the bytes to the model context, the chat transcript, or
a tool call's `params` blob. No file mode prevents this. The
defense has to be architectural (skills don't read credentials at
all; credentialed primitives do) and prose (SKILL.md "Don't" rules
the agent treats as cooperative-but-fallible guardrails). Both have
to be written down or they don't exist.

**Anti-patterns are already in the wild.** `langpingxue/
atlassian-skills` Mode 2 takes credentials as a function argument
("for agent environments where environment variables are not
available"). That's exactly the failure mode this RFC exists to
forbid: it puts cleartext through the LLM's tool-arg context window
on every call. Without a convention, our packs will eventually
import or imitate that pattern.

**Two adjacent decisions are blocked on this one.**
[ADR-0002](../adr/0002-install-scope-per-pack-default-and-allowance.md)
forbids hook-shaped primitives at user scope pending RFC-0005.
RFC-0005 itself defers naming the first user-scope hook-bearing pack
on the same "land mechanics under release pressure → corners cut"
precedent. A credential primitive is the *other* user-scope-by-
nature primitive shape, and authors will start asking for it as
soon as a credentialed skill ships. Writing the convention now means
that question has a settled answer.

The credential primitive does not invoke ADR-0002's ban: under the
narrow reading of "hook-shaped" this RFC adopts (binds to runtime
events AND requires wiring-merge), credentials qualify on neither
prong. The reading is consistent with RFC-0005's entire design
surface, which is the merge-into-shared-settings-file mechanic
(`user-merge-json` for `~/.claude/settings.json`,
`merge-into-agent-json` for `.kiro/agents/<name>.json`). The
load-bearing concern was always the merge problem; "hook-shaped"
is shorthand for that mechanic, not for "any primitive whose
natural home is a user-scope path." § Follow-on artifacts commits
to an ADR-0002 amendment freezing this definition.

## Proposal

### 1. Two-layer architecture: skills don't hold credentials

The convention separates two roles:

- **Credentialed primitive.** Holds the secret. Knows how to read
  the dotfile / keyring / env var. Constructs the API call inside
  its own process. Examples: an MCP server (`mcp-atlassian`-shaped);
  a CLI wrapper packaged as a primitive (`python -m agent_ready.jira
  search ...` — loads credentials via `agent_ready.credentials`
  internally, never returns them via stdout); a broker subprocess
  invoked by name from a skill.

- **Skill.** Orchestrates the credentialed primitive. Reads its exit
  code and stdout, relays results, never reads the credential file
  itself. Its `SKILL.md` declares which primitive it depends on and
  carries the standard "Don't" block (below) verbatim.

A skill that violates the boundary — by reading the dotfile
directly, accepting `--token`, or holding the cleartext in a
variable the LLM constructs — is non-conforming. `conventions-check`
catches the lexical cases.

### 2. Storage tiers (gh-CLI-shaped, stdlib-only)

A credentialed primitive resolves the secret in this order. The
first hit wins; lower tiers are not consulted.

| Tier | Source | Use case | At-rest protection |
| --- | --- | --- | --- |
| 1 | `<NAMESPACE>_API_TOKEN` env var (and siblings: `_BASE_URL`, `_EMAIL`, `_FLAVOR`) | CI, headless dev VMs, agent harnesses that inject secrets via a wrapper process, corporate boxes where neither keyring nor dotfile is welcome | None — process-scoped only; relies on the launcher (Vault Agent, SSM run, `op run --`) to keep cleartext out of disk |
| 2 | OS keyring via stdlib only. macOS: `/usr/bin/security find-generic-password -s <service> -a <account> -w` (subprocess; token passes via child stdin, never argv). Windows: `ctypes.windll.advapi32.CredReadW` / `CredWriteW` against `wincred.h`'s `CREDENTIAL` struct (in-process; no subprocess); credential type `CRED_TYPE_GENERIC`, persistence `CRED_PERSIST_LOCAL_MACHINE` (see "Windows support" below), target-name convention `agent-ready:<namespace>:<key>`. Linux deferred — see "Why Linux libsecret stays deferred" below. | Dev laptops where the platform's user-bound encrypted credential store is available (macOS Keychain or Windows Credential Manager). | OS-level. macOS Keychain encrypts to the user's keychain master key (login-session-unlocked); Windows Credential Manager encrypts via DPAPI keyed to the user's password / master key (survives logoff and reboot; the user account is the key, not the session). |
| 3 | Dotfile: `~/.agent-ready/credentials.env` (resolved via `pathlib.Path.home()` — `$HOME/.agent-ready/` on POSIX, `%USERPROFILE%\.agent-ready\` on Windows), mode 0600 on POSIX with parent dir 0700, namespaced keys (`JIRA_API_TOKEN`, `CONFLUENCE_API_TOKEN`, etc.) | Linux boxes (default, until libsecret tier lands); Windows or macOS boxes where the user passed `--allow-insecure-fallback` at setup time to opt out of Tier 2; or `ERROR_NOT_FOUND` at read time (legitimate "no credential exists" case — see Win32 error-code matrix). **Not reached** when a Tier-2 call returns `ERROR_NO_SUCH_LOGON_SESSION` or other hard-fail codes: silent degradation defeats the security posture the user chose. | Filesystem ACLs (POSIX mode bits on Linux/macOS; inherited DACL from `%USERPROFILE%` on Windows, verified via `icacls`; permissiveness gated by `--allow-permissive-acl` — see § 3) |

**The setup helper announces which tier it landed on.** If the
user asked for keyring and got the dotfile, the helper says so on
stderr and exits non-zero unless `--allow-insecure-fallback` was
passed at setup time. The only two reasons keyring → dotfile
happens in v1 are (i) Linux, where Tier 2 is deferred, and (ii)
the user explicitly passed `--allow-insecure-fallback` to opt
out of Tier 2 on a Tier-2-capable box. Hard-fail Win32 error
codes (`ERROR_NO_SUCH_LOGON_SESSION`, `ERROR_INVALID_FLAGS`,
`ERROR_LOGON_FAILURE`) do **not** trigger a Tier-3 outcome —
they exit non-zero per the error matrix in § 2 Tier 2. This is
the [cli/cli #10108](https://github.com/cli/cli/issues/10108)
policy: silent degradation is the security smell, not the
dotfile itself.

**No `python-dotenv`.** The loader is a stdlib parser, ~12 lines,
that handles `KEY=value`, `KEY="value with spaces"`, and `# comment`
lines. CRLF tolerance: a single trailing `\r` is stripped from each
line before splitting on `=` (`line.rstrip("\r\n")`); `\r`
characters inside a quoted value are preserved (tokens never
contain them, but the rule is pinned so the spec phase's test
matrix can fix it). It is deliberately less featureful than
`python-dotenv`: no variable expansion, no `export ` prefix, no
multi-line values. The parser ships in `core` (see § Tooling
deliverables).

**One shared file, namespaced keys.** A single dotfile holds keys
for every credentialed primitive on the box, with vendor prefixes
(`JIRA_API_TOKEN`, `CONFLUENCE_API_TOKEN`, `JIRAALIGN_API_TOKEN`,
…). The shape matches dropkit and `mcp-atlassian`; the alternative
(one file per primitive) was considered and rejected because (a)
the user enters their email and base URL once for a vendor that
fans out across multiple skills (Atlassian: Jira + Confluence +
Bitbucket all share an email and an API token); (b) the
filesystem-level "every credentialed primitive can read every
other's keys" cost is already paid by the architecture rule
(skills don't read the file directly; primitives do, and a
primitive that reads keys it doesn't own is non-conforming
regardless of where they live). The schema for which keys belong
to which namespace lives in per-namespace `creds-schema.toml`
files (§ 5).

**Path consistency with the catalogue's user-scope root.** The
catalogue's existing user-scope artifacts live under `~/.agent-ready/`
(RFC-0004 install state at `~/.agent-ready/state.toml`;
adapt-to-project at `~/.agent-ready/.adapt-discovery.toml` etc.).
The credentials dotfile lives under the same root rather than under
XDG `~/.config/`. One audit point per box; one resolution call
(`pathlib.Path.home()`) on every platform. The XDG-respect cost is
accepted; the catalogue made this choice in RFC-0004 ahead of this
RFC and consistency is more valuable than per-platform purity.

**Windows support: full parity with macOS in v1.** All three tiers
work on Windows with stdlib only.

- **Tier 1 (env var).** Identical to POSIX — Python reads
  `os.environ` the same way.
- **Tier 2 (Windows Credential Manager via `ctypes`).** The loader
  calls `ctypes.windll.advapi32.CredReadW(target, type, flags,
  &credential_ptr)` to read and `CredWriteW(&credential, flags)`
  to write, with `credential_ptr` freed via `CredFree`. The
  `CREDENTIAL` struct is constructed in-process; the token never
  crosses a subprocess boundary, so **argv exposure is structurally
  impossible** (the heap-resident UTF-16 token bytes remain
  visible to a crash dump or attached debugger — the same way a
  Python `bytes` buffer feeding the macOS `security` subprocess
  does. In-process memory residue is out of scope for this RFC).
  The `cmdkey`-based alternative was rejected: Microsoft's docs
  confirm `cmdkey` is write-only from the CLI by design on
  Win10/11, so a `cmdkey`-based Tier-2 can't read back at load
  time. Credentials use `CRED_TYPE_GENERIC` (= 1), persistence
  `CRED_PERSIST_LOCAL_MACHINE` (= 2; see persistence-flag
  selection below), and target-name convention
  `agent-ready:<namespace>:<key>` (sorts together in Credential
  Manager UI under one alphabetic prefix; the prefix is
  unregistered and collision risk with third-party tools is
  theoretical). The `UserName` field is set to the namespace
  string so credentials appear with a non-blank account in the UI.
  At-rest encryption is DPAPI keyed to the user's password /
  master key, surviving logoff and reboot. Reference
  implementations of the ctypes shape exist in `pywin32-ctypes`,
  Samba's `dpapi.py`, and Microsoft's `jupyter-Kqlmagic`
  `dpapi_crypto.py`; this RFC targets a minimal stdlib `ctypes`
  wrapping (under 100 lines — actual count pinned in the spec
  phase against a skeleton). The full Win32 surface is `CredReadW`,
  `CredWriteW`, `CredDeleteW`, `CredFree` plus the `CREDENTIAL`
  struct definition.

  **Persistence-flag selection.** Three values are available:
  `CRED_PERSIST_SESSION` (1; lost at logoff),
  `CRED_PERSIST_LOCAL_MACHINE` (2; survives logoff and reboot on
  this machine only), `CRED_PERSIST_ENTERPRISE` (3; roams to every
  machine the user logs into via the user's roaming profile). The
  proposal picks `LOCAL_MACHINE` because credential blast-radius
  should be local: a developer's API token reaching every
  domain-joined box they log into (the `ENTERPRISE` behavior) is
  a worse outcome than re-running `setup` on each box. This
  matches the persistence choice common to single-machine
  credential tools (e.g. `cmdkey /generic`'s default); the spec
  phase pins the exact precedent citation before committing the
  default. Adopters
  who want the roaming behavior can amend the spec; `SESSION`
  defeats the v1 goal (re-entering a token at every logon is the
  ergonomic regression Tier 2 exists to avoid).

  **Win32 error-code handling.** `CredReadW` returns four error
  codes the loader distinguishes:
  - `ERROR_NOT_FOUND` (1168) — no credential at this target;
    legitimate "run setup" case. Loader falls through to Tier 3.
  - `ERROR_NO_SUCH_LOGON_SESSION` (1312) — caller has no
    interactive logon session (e.g. service running as
    `LocalSystem`, scheduled task without `S4U`). Loader **does
    not** fall through to Tier 3 — Tier 2 was the security
    posture the user chose; silently degrading defeats it. Hard
    error with stderr naming the cause; the operator must either
    set the env var (Tier 1) or run the service under a real
    user account.
  - `ERROR_INVALID_FLAGS` (1004) — programming error in our
    ctypes call. Hard error with the offending flag value.
  - `ERROR_LOGON_FAILURE` (1326) — DPAPI key derivation failed
    (cached creds expired on a domain-joined box). Hard error;
    user re-authenticates and the next call succeeds.
- **Tier 3 (dotfile).** Path resolves to
  `%USERPROFILE%\.agent-ready\credentials.env` via
  `pathlib.Path.home()`. `os.chmod` is **not** invoked on Windows:
  Python's `os.chmod` honors only the `S_IWRITE` bit there, so
  passing `0o600` could clear the read-only flag rather than
  enforce a meaningful policy. The helper guards the call with
  `os.name == "posix"`. At-rest protection on Windows derives from
  the DACL inherited from `%USERPROFILE%` (typically user + SYSTEM
  + Administrators only), verified with `icacls` after creation
  (§ 3).

**Why Linux `libsecret` stays deferred.** Not because of `ctypes`
availability — `ctypes.CDLL("libsecret-1.so.0")` would work the
same way `ctypes.windll.advapi32` does on Windows when the library
is present, with graceful `OSError` fallback to Tier 3 when it
isn't. The real deferral reason is the *D-Bus session matrix* the
Linux keyring requires: GNOME Keyring / KWallet / KeePassXC all
speak the freedesktop.org Secret Service API over a D-Bus session
bus, which is absent on headless containers / WSL2 / SSH-only dev
boxes; the locked-keyring "please type your password to unlock"
prompt is a separate UX flow with no analogue on Mac or Windows;
and the org-management story (corporate fleets running GNOME
Keyring under MDM vs. raw KeePassXC vs. nothing) needs an
adopter-profile audit before the convention picks a default.
Three integration paths exist (`secret-tool` CLI, `gi.repository.
Secret` Python bindings, `ctypes.CDLL("libsecret-1.so.0")` direct)
and choosing among them is part of the audit. Linux adopters land
on Tier 3 (dotfile) in v1; the v2 RFC scopes libsecret
integration alongside the adopter-profile audit and picks one
path among the three.

### 3. Acquisition: one Python stdlib script

The interactive setup script is a single Python file shipped from
`core`, run as `agentbundle creds setup <namespace>`. Stdlib only
(`getpass`, `os`, `pathlib`, `subprocess`, `argparse`, `tomllib`).
It:

- Prompts for the namespace's required keys (defined by a
  per-namespace `creds-schema.toml` the credentialed primitive
  ships under `references/`).
- Reads tokens via `getpass.getpass`, which is portable across
  Linux, macOS, and Windows terminals and hides input without
  shelling out to `stty`. The helper guards each `getpass.getpass`
  call with an explicit `sys.stdin.isatty()` check — see the
  detailed handling further down for why the check is necessary
  on Windows (where `getpass` reads `msvcrt.getwch()` regardless
  of stdin redirection).
- Writes atomically: `mktemp` in the target dir → set permissions
  → `os.replace`. Permission step is guarded by `os.name`:
  POSIX (`os.name == "posix"`) calls `os.chmod(path, 0o600)`;
  Windows skips the chmod (it would clear `S_IWRITE` rather than
  enforce a meaningful policy) and instead runs `icacls <path>` to
  verify the inherited DACL contains only the user, SYSTEM, and
  Administrators. If the DACL is more permissive (additional
  groups granted read access), the helper refuses with stderr
  naming the offending ACEs unless the user passes
  `--allow-permissive-acl`.
- For keyring tier on macOS, shells out to `/usr/bin/security
  add-generic-password -U -s <service> -a <account> -w` (**no token
  on argv** — the trailing `-w` with no value triggers `security`'s
  prompt mode, which the `security(1)` man page recommends as
  *"Put at end of command to be prompted (recommended)"*). The
  setup script writes the token to the child's stdin via
  `subprocess.Popen(..., stdin=PIPE)` + `proc.communicate(input=
  token.encode())`. Verification uses `find-generic-password -w`,
  which prints the password to stdout for capture by the parent
  (parent never echoes it). This avoids the `ps -ef` /
  `/proc/<pid>/cmdline` leak that `-w <token>` would create — the
  exact anti-pattern § 6 bans.
- For keyring tier on Windows, calls `ctypes.windll.advapi32.
  CredWriteW(&credential, 0)` with a `CREDENTIAL` struct
  constructed in-process: `Type = CRED_TYPE_GENERIC (1)`,
  `Persist = CRED_PERSIST_LOCAL_MACHINE (2)`,
  `TargetName = "agent-ready:<namespace>:<key>"`,
  `UserName = "<namespace>"` (non-NULL so the entry shows a
  non-blank account in the Credential Manager UI; the namespace
  is the natural account label since the key is already encoded
  in `TargetName`), `CredentialBlob` pointing at the
  UTF-16-encoded token, `CredentialBlobSize =
  len(token_utf16_bytes)`. All other `CREDENTIAL` fields
  (`Flags`, `Comment`, `LastWritten`, `AttributeCount`,
  `Attributes`, `TargetAlias`) are left at `ctypes.Structure`'s
  zero/NULL default — required for `CRED_TYPE_GENERIC` (`Flags`
  must be 0; `Attributes` must be NULL when `AttributeCount` is
  0; `LastWritten` is set by the API, ignored on write) and
  pinned by a byte-equality round-trip assertion in the spec
  phase. The token never crosses a process boundary — **argv**
  leak is structurally impossible (in-process heap residue is out
  of scope; see § 2 Tier 2). Verification re-reads via
  `CredReadW(target, type, 0, &out_ptr)` and compares the returned
  blob, then `CredFree(out_ptr)`.
- Refuses to read the token from **its own** stdin (the helper
  process's stdin) when not a tty, or from argv, env, or a pipe.
  Tokens enter through the interactive `getpass` prompt or
  nowhere. Note: this is distinct from the macOS Tier-2 bullet
  above, which writes the token to a *child* process's stdin
  (`security`'s `subprocess.Popen(stdin=PIPE)`) — the helper's own
  stdin and the child's stdin are different file descriptors. The
  helper guards its own stdin with an explicit
  `sys.stdin.isatty()` check before calling `getpass.getpass`;
  the check is needed on every OS but is especially important on
  Windows, where `getpass` uses `msvcrt.getwch()` to read the
  console buffer regardless of stdin redirection and would
  otherwise succeed silently in CI-like contexts.
- Reports the tier it wrote to.

Python (not Bash + PowerShell parity) because the credentialed
primitive itself will be Python — the helper inherits the
primitive's runtime, and we don't pay a second-language tax to
support Windows.

### 4. The argv ban and the SKILL.md "Don't" boilerplate

Two prose rules, both reported by `conventions-check`. The rules
are scoped to **primitive class** via two new optional `SKILL.md`
frontmatter keys: `credentialed: true` and
`primitive-class: credentialed-cli | mcp-server`. Absence of
`credentialed:` means the skill is not credentialed; the lint
skips it. The existing `tools/lint-agent-artifacts.sh` "no unknown
keys" rule is amended in lockstep with this RFC's acceptance to
allow the two new keys; this avoids introducing a new
`manifest.json` file format the catalogue has no other use for.

**Argv ban (credentialed-CLI class).** Credentialed-CLI primitives
must refuse `--token`, `--api-token`, `--api-key`, `--bearer`,
`--pat`, and `--password` flags and exit non-zero. The lint greps
for these flag names being *accepted* in `argparse.ArgumentParser`
calls inside any script under the primitive's `scripts/` directory.

**MCP-server class — parallel rules.** MCP servers and other
HTTP-listener primitives (`mcp-atlassian`-shaped) legitimately
accept credential *configuration* — e.g., `--bearer-header
X-Auth-Token` names which header to consult per-request; the
multi-tenant BYOT gateway pattern is genuinely valid for that
class. The lint scopes the argv ban to *value-shaped* flag names
only (the list above); *header-naming* flags (`--bearer-header`,
`--header-prefix`, `--auth-header`) are allowed and not refused
by the lint. The two-layer architecture rule still applies — the
skill never constructs the server invocation; the user wires the
server into their MCP host config out-of-band. The storage
convention (Tiers 1/2/3) does *not* apply to MCP-server primitives
that hold no on-disk state; their "Don't" block has a parallel
form ("the server may accept tokens per-request via headers;
never log header values; the storage convention does not apply
because nothing is persisted").

**Operational surface for `mcp-server` primitives.** `agentbundle
install` / `uninstall` treat the class identically to other
primitive types (skills, agents, commands) — the class affects
*lint scoping* and *SKILL.md template variant*, not install
mechanics. An `mcp-server` primitive typically has no `scripts/`
directory (the server is a wired-in process the adopter
configures into their MCP host); the `scripts/`-based argv lint
is therefore a no-op for this class, which is the correct
outcome. The spec phase pins the SKILL.md content shape for
`mcp-server` (transport / configuration documentation, host-side
wiring guidance) alongside the credentialed-CLI shape. The SKILL.md template at
`docs/_templates/credentialed-skill-SKILL.md` carries both
variants as labeled sections; authors pick the one matching their
`primitive-class:` frontmatter and delete the other (the spec
phase pins whether selection is a copy-the-matching-block step or
a templating step — for now it is the simpler copy step).

**SKILL.md "Don't" block.** Every credentialed skill embeds the
following block verbatim (path-substituted) in its `SKILL.md`,
under a `### Security rules (non-negotiable)` heading:

```markdown
- Secrets live only in `~/.agent-ready/credentials.env`
  (mode 0600 on POSIX; DACL-restricted on Windows), the OS keyring,
  or process environment variables.
  **Never** read that file, print it, or echo the token.
- **Never** put the token on the command line. The primitive
  refuses flags like `--token` / `--api-token` / `--bearer` /
  `--pat` / `--password` and exits — do not work around it.
- If `check` exits with the "missing credentials" code, tell the
  user to run `agentbundle creds setup <namespace>` themselves.
  It's interactive — do not run it for them.
```

`conventions-check` reads `credentialed:` and `primitive-class:`
from each skill's `SKILL.md` frontmatter to scope which rules
apply. When `credentialed: true` is set, the lint **reports
findings** (does not block PRs — `conventions-check` is a slash
command, not a CI gate; the existing command's own contract is
*"report findings and let the user decide what to do"*). PR-side
enforcement is a separate cross-cutting concern not introduced
by this RFC.

Reported findings:

- The SKILL.md "Don't" block is absent.
- For `primitive-class = "credentialed-cli"`: any script under
  the primitive's `scripts/` directory accepts a flag whose
  normalized name (strip leading `-`, casefold) matches
  `{token, api_token, api_key, bearer, pat, password}`. The
  normalization defeats trivial obfuscation (`"--" + "token"`,
  casing variants); deep obfuscation (dynamic flag names
  assembled at runtime) is out of scope of the lint and lives
  under the architectural rule.
- Any substring match of the dotfile path
  (`.agent-ready/credentials.env`) inside a skill's `scripts/`,
  with an opt-out comment-marker (`# credentialed-primitive:
  reads-creds-directly` on the same line) for primitives that
  legitimately read the file. The marker is itself flagged in PR
  review.

The exact "Don't" wording — credentialed-CLI variant and
MCP-server variant — is published as a snippet under
`docs/_templates/credentialed-skill-SKILL.md` so authors copy-paste
rather than reinvent. When the catalogue later adopts CI-side
lint enforcement (separate RFC), severity becomes a per-rule
config there.

### 5. Tooling deliverables

This is the explicit ask: what does the catalogue ship?

All of these land in **`core`**. No new top-level pack.

| Deliverable | Location | Purpose |
| --- | --- | --- |
| `agentbundle creds` verb with subcommands `setup`, `check`, `where`, `rm` | `packages/agentbundle/agentbundle/creds/` | CLI entry point. `setup` is the interactive acquisition flow; `check` returns exit code 0 (ok) / 2 (missing) / 3 (other); `where` reports which tier resolved for a given namespace; `rm <namespace>` deletes from whichever tier holds it. **No `get` subcommand in v1.** A `creds get` that prints a token to stdout is the wrap-and-leak shape: a skill author can `subprocess.check_output(['agentbundle', 'creds', 'get', ...])` and capture the cleartext into LLM-visible scope. **The gap this creates, named honestly:** a user with their token only in agent-ready Tier 2/3 cannot pipe it into a non-Python tool's env var (a Bash one-liner, a third-party CLI). The composition `op run -- ...` works only if the credential is duplicated into 1Password; agent-ready can't project Tier-2/3 → env var for outside-Python consumers. Users who need that composition either (a) put the credential in their secrets-manager-of-choice and use that tool's env-var-injection wrapper, or (b) wait for v1.1, where a `creds export` subcommand that writes to a *file* (mode 0600, atomic) — not stdout — would restore composition while keeping wrap-and-leak harder. Not adding it in v1 is deliberate; the gap is a known limitation, not an oversight |
| `agent_ready.credentials` Python module | `packages/agentbundle/agentbundle/creds/loader.py` + `creds/_keychain_macos.py` + `creds/_credman_windows.py` | Stdlib-only loader credentialed-primitive authors import: `load_credentials(namespace, required_keys=[...]) -> Credentials`. Implements the three-tier precedence. Per-platform Tier-2 backends are isolated in `_keychain_macos.py` (subprocess wrapper over `/usr/bin/security`) and `_credman_windows.py` (ctypes wrapper over `advapi32.CredReadW`/`CredWriteW`/`CredDeleteW`/`CredFree`). No external deps |
| Stdlib `.env` parser | same file | The ~12-line parser. Documented as "intentionally less than `python-dotenv`" |
| `creds-schema.toml` format | Schema file ships under each credentialed primitive's `references/` directory; format documented in `docs/specs/skill-secrets/spec.md` (follow-on). **Primitive enumeration** for `agentbundle creds setup` invoked without a positional namespace argument: walks both scope state files (`<repo>/.agent-ready-state.toml` + `~/.agent-ready/state.toml`) — same shape as the RFC-0004 AC *"`adapt` walks both"* and the `adapt-to-project` spec's both-scope walk — and lists every installed primitive whose `SKILL.md` frontmatter declares `credentialed: true`. `agentbundle creds setup <namespace>` (positional) skips the walk and operates on the named primitive directly | Per-namespace declaration of required keys + UI labels the setup script reads |
| `SKILL.md` template snippet | `docs/_templates/credentialed-skill-SKILL.md` | The "Don't" boilerplate carrying both labelled variants — `credentialed-cli` (full storage convention + argv ban) and `mcp-server` (per-request header guidance; storage convention does not apply). Author picks the section matching their `primitive-class:` frontmatter and deletes the other |
| `conventions-check` rule | `packs/core/.apm/commands/conventions-check` (extended) | Detects argv-flag violations, missing "Don't" block, skill reading the dotfile path directly |
| `CONVENTIONS.md` section | `docs/CONVENTIONS.md` | New top-level "Credentialed skills" section pointing at the template, the loader, and this RFC |
| Worked example | `packs/core/.apm/skills/example-credentialed-skill/` | A real (no-op) credentialed skill that imports `agent_ready.credentials`, ships a `creds-schema.toml`, and includes the "Don't" block. Lives under `.apm/skills/` because it's a primitive (it ships to adopters' skill set), not under `seeds/` which carries adopter-installed README / template / governance content per `docs/CONVENTIONS.md` § Pack source-of-truth split. Adopters copy this as a starting point or remove it via `agentbundle uninstall` if not needed |
| Documentation | `docs/guides/how-to/add-a-credentialed-skill.md` | Diátaxis how-to walking through the contract |

**Why this lands in `core`, not a new pack.** `core` ships
`agentbundle` (the CLI + adapter-contract code) into the adopter's
Python environment via pip / pipx — not via pack file projection.
The `agent_ready.credentials` module is reached by
credentialed-primitive Python code through normal `import` against
that pip-installed package; it is *not* re-projected into each
user-scope pack's primitive directory. Cross-scope coupling does
not materialize because there is nothing user-scope to project:
the loader lives in `site-packages`, the pack the user-scope
primitive ships from doesn't carry a copy. This matches the way
every credentialed primitive in the surveyed corpus
(`mcp-atlassian`, `dropkit`, `gh` CLI) imports its credential
loader from the package install, not from a pack tree. The
alternative — a separate `creds-runtime` pack — would force
user-scope packs to declare a cross-scope dependency on it, which
RFC-0004 § `recommends` across scopes deliberately keeps as a
warn-not-refuse path. The pip-install route avoids that
declaration entirely.

**`creds-schema.toml` vs. extending `manifest.json`.** `manifest.json`
is per-skill; one skill may multiplex multiple credential
namespaces (a "compose" skill that needs both Jira and Slack
tokens), and one credentialed primitive may serve multiple skills.
Schemas are per-namespace, not per-skill; the separate file matches
the cardinality. Inlining into `manifest.json` would force either
duplication (each skill repeats the same schema) or a level of
indirection (`manifest.json` points at a shared schema by name)
that ends up reinventing the separate file. Keep them separate.

**What we explicitly do not ship in v1:**

- A keyring backend for Linux (`libsecret` / `secret-tool`).
  Phased to a v2 RFC alongside an audit of which adopter profiles
  need it. The dotfile is the floor on Linux; macOS Keychain and
  Windows Credential Manager are the v1 keyring tiers, both via
  stdlib only.
- An OAuth flow (device code, PKCE). Vendors that support OAuth
  should ship an MCP server; the credential primitive's job is to
  wrap *token-shaped* secrets, not orchestrate IdP round trips.
- A secrets manager integration (Vault, 1Password, AWS SSM). The
  env-var tier composes naturally with these via `op run --`,
  `vault agent`, etc. We don't need to be in that loop.
- Per-skill ACL prompting on the macOS Keychain item. `security
  add-generic-password -T /usr/bin/python3` would limit which
  binaries can read, but the locked-down corporate Mac fleet
  typically rewrites Keychain ACL policies via MDM anyway. Document
  the option, don't enforce it.

### 6. Anti-pattern register

`CONVENTIONS.md` records these as forbidden, with reasoning that
points back at this RFC:

- **Token as function argument or tool argument.** Cleartext flows
  through the LLM's tool-call params; visible in transcripts and
  in any harness that logs tool calls.
- **`--token` / `--api-key` / similar argv flags.** Cleartext lands
  in process listings, shell history, the prompt context if the
  LLM constructs the command, and any logging that records argv.
- **Shelling out with the secret as an argv item, even via a
  list-form `subprocess.run([..., token, ...])`.** Same exposure —
  argv is visible to any local process via `ps` /
  `/proc/<pid>/cmdline`. Tokens reach child processes via stdin
  (`subprocess.Popen(stdin=PIPE)` + `communicate(token.encode())`)
  or via the child's environment (`env={**os.environ,
  "X_TOKEN": token}`), never via argv. This is the rule that
  applies to the Tier-2 macOS Keychain invocation (§ 3).
- **Skill reads the dotfile directly.** Once the cleartext is in
  the skill's Python process, the LLM can `print()` it; the
  primitive boundary is the only place where the secret is held
  out of the LLM-controlled process. Skills shell out to the
  primitive; they don't `open()` the file.
- **`SSL_VERIFY=False` default.** Surprising-bad default (see
  `langpingxue/atlassian-skills`). `--insecure` is opt-in only.
- **Hardcoded fallback secret** ("default if env var unset").
  Hardcoded secrets get committed.

### 7. Corporate concerns the primitive must respect

The credentialed-primitive contract requires:

- **Honor `HTTPS_PROXY` / `NO_PROXY` from the environment.**
  Corporate outbound traffic goes through a proxy.
- **Honor the system trust store via `REQUESTS_CA_BUNDLE`,
  `SSL_CERT_FILE`, or `SSL_CERT_DIR`.** MITM-decrypting corporate
  proxies install a CA there; an `httpx`/`requests` call that only
  trusts `certifi` will fail.
- **Refuse `--insecure` / `verify=False` as a default.** It's a
  per-invocation user opt-in, never on by default, and the primitive
  emits a stderr warning when it's used.

These three are documented in the credentialed-primitive section of
`CONVENTIONS.md` and checked by `conventions-check`'s primitive lint.

## Alternatives considered

### A. Do nothing — let each skill author invent

The cost: every credentialed skill ships its own config path,
permission mode, and "where do I put the token?" answer. The
divergence is already visible in the dropkit / langpingxue /
mcp-atlassian comparison from this session's research; the
`langpingxue` Mode 2 (token as function arg) shows what happens at
the bad end of the curve. Without a written convention an adopter
will pick the wrong neighbor. Rejected.

### B. Dropkit clone — dotfile only, no keyring tier, `python-dotenv`

The simplest answer; the one dropkit already runs. Two reasons
against:

1. `python-dotenv` is a Python dep that some corporate package
   policies will gate. Replacing it with ~12 lines of stdlib
   removes the friction at zero capability cost.
2. macOS Keychain via `/usr/bin/security` is free (stdlib
   subprocess, no Python dep), already on every Mac, and is a real
   security upgrade over a 0600 dotfile. Leaving it out for "v1
   simplicity" forfeits the easiest win.

Worth keeping the dotfile-only flavor as the *fallback path*
within the tiered model, which the proposal does.

### C. Require an MCP server or external secrets manager

"Skills don't deal in credentials; route everything through
`mcp-atlassian` / Vault / 1Password / AWS SSM." Compelling for
OAuth-supporting vendors (SpillwaveSolutions/jira does this) but
forfeits the long tail: internal corporate APIs, region-specific
endpoints, vendors without an MCP. Also pushes a hard dependency
onto every adopter, which conflicts with the "stock CPython + the
OS the user already has" floor we set for corporate-package
reasons. The proposal *enables* this pattern (Tier 1 env var
composes with `op run --` etc.) but does not require it.

### D. Use the Anthropic Skills `/skills` API store

Anthropic's hosted skills can persist per-user state. Out of scope:
this catalogue runs outside Anthropic's harness too (Cursor,
Codex, Gemini CLI per the AGENTS.md split), and we can't make a
convention that depends on one vendor's storage backend.

### E1. Convention + loader, no CLI verb

Ship the storage tiers, the SKILL.md "Don't" block, and the
`agent_ready.credentials` loader, but no `agentbundle creds` verb.
Authors run their own setup script per primitive.

Rejected because the setup flow is *the* place the argv ban,
keyring tier announcement, and `--allow-insecure-fallback` /
`--allow-permissive-acl` discipline get enforced. Pushing that to
per-primitive scripts means each primitive re-implements (and
re-misses) it. The CLI verb is ~100 lines for a real
defense-in-depth gain.

### E2. Convention only, no helper code

Write the storage tiers and the "Don't" block into
`CONVENTIONS.md`, ship the template snippet, stop there. Authors
implement loaders themselves.

Rejected because three skill authors writing three not-quite-the-
same stdlib `.env` parsers is the failure mode this catalogue
exists to prevent. The stdlib `.env` parser alone is ~12 lines;
the per-platform Tier-2 backends (`_keychain_macos.py`,
`_credman_windows.py`) are under 100 lines each per § 2. Not
shipping any of it would be parsimony for its own sake. The convention-without-code path
also forfeits `conventions-check` enforcement (the lint reads
`"credentialed": true` from `manifest.json`; without a stable
loader API the lint has nothing to anchor on).

### F. Subprocess-broker pattern only — skills never see cleartext

Stronger LLM-context hygiene than even the proposal: instead of the
skill loading creds and constructing an HTTP client, the skill
invokes a per-call broker (`creds get jira | http POST ...`) so
cleartext is only ever inside a one-shot process the LLM doesn't
directly control. Considered. Rejected for v1 because:

- The "credentialed primitive owns the secret" rule already
  achieves this for skill authors who follow the architecture
  rule; the primitive is the broker.
- Forcing every credentialed call into a separate subprocess slows
  bulk operations (a JQL export streaming 5,000 issues becomes
  5,000 subprocess invocations) without commensurate gain.
- The contract benefits from being one layer, not two.

The proposal does not preclude future broker-style primitives;
they slot in as a sub-shape of "credentialed primitive."

## Drawbacks

- **New surface to maintain.** `agent_ready.credentials` and
  `agentbundle creds` are real code, and the stdlib `.env` parser
  will hit edge cases (`KEY=value with # comment`,
  leading/trailing whitespace, equals-in-value) that
  `python-dotenv` already solved. (CRLF is not on this list —
  § 2 pins the trailing-only `\r` strip rule.) We pay for
  stdlib-only with a small amount of test surface.

- **macOS Keychain access can surprise headless agents.** A skill
  running under an SSH session that wasn't unlocked via the GUI
  may hit a Keychain unlock prompt that times out. The setup
  helper documents this and the user can opt for the dotfile tier;
  the failure mode is loud, not silent. Still, "it works on my
  laptop but not in CI" is a real ticket we will get.

- **Stdlib `.env` parser is not `python-dotenv`.** Authors used to
  `python-dotenv`'s richer syntax (variable expansion, `export`
  prefix, multiline) will trip. The convention document calls this
  out; the parser is deliberately small.

- **Token-on-disk for vendors without OAuth.** Tier 2 helps on
  macOS and Windows; on Linux (and on macOS/Windows when the
  adopter passed `--allow-insecure-fallback` at setup time),
  Tier 3 is the floor and an attacker with user-equivalent
  process access on the box reads the file. The prose guardrails
  are real but soft. We're trading "perfect" for "actually
  adoptable inside corporate constraints" — the same trade
  `gh` CLI makes, and the same one dropkit's adopters already
  accept.

- **`conventions-check` lint has false negatives.** Detecting
  "this skill reads the dotfile directly" via grep catches the
  obvious cases (`open(os.path.expanduser("~/.agent-ready/
  credentials.env"))`) but not obfuscation
  (`open(os.environ["HOME"] + "/.agent-ready/credentials.env")`,
  `argparse as ap; ap.ArgumentParser().add_argument("--" + "token")`).
  The lint is a tripwire, not a sandbox. See § 4 for the
  manifest-driven discriminator (`"credentialed": true`) that scopes
  which rules apply, and § 6 for the broader rule set the lint
  approximates.

- **One more user-scope-by-nature primitive shape, on top of
  RFC-0005's hook-wiring.** The credential dotfile is the second
  class of primitive whose natural home is a user-scope path.
  This RFC adopts the narrow reading of ADR-0002's "hook-shaped"
  (binds to runtime events AND requires wiring-merge — see §
  Motivation and § Follow-on artifacts' ADR amendment), so the
  ban does not apply to credentials. The drawback is that the
  catalogue grows another user-scope-by-nature primitive shape
  and the ADR-0002 reading gets exercised one more time; the
  amendment freezing the narrow definition is the mitigation.
  Rollback: if the narrow reading is rejected during this RFC's
  review, the credential primitive returns to an RFC-0005-style
  merge-story design (the dotfile becomes a wiring-merge target
  rather than a pack-owned file) and this RFC defers acceptance
  until that follow-on design lands.

- **Forecloses a couple of designs.** Once
  `~/.agent-ready/credentials.env` is the documented path, moving
  it is a breaking change. Specifically foreclosed: (a) a
  per-namespace file layout (`~/.agent-ready/credentials.d/jira.env`
  etc.) that some adopters prefer for IT-policy reasons; (b) an
  XDG-compliant variant (`~/.config/agent-ready/credentials.env`)
  for adopters following the Freedesktop convention; (c) a
  per-primitive file (`packs/<pack>/credentials.env`) that would
  keep credentials co-located with the primitive but conflict with
  the user-scope-data principle. Each can be added behind a future
  RFC as a non-default; the canonical path is one.

- **`core` grows a runtime-import surface.** To date `core` has
  been adapter contract + CLI + conventions enforcement — not a
  *runtime library that user-scope primitives import.* Accepting
  this RFC makes `agent_ready.credentials` a transitive dependency
  of every credentialed primitive. The defense in § 5
  (pip-installed, not pack-projected — so no cross-scope projection
  happens) is real but new. Future RFCs that put more
  runtime-import surface in `core` get easier; a deliberate
  reviewer should weigh whether that's the slope we want.

- **Windows Tier-3 fallback at-rest protection is no stronger
  than the inherited DACL on `%USERPROFILE%`.** Windows Tier-2
  (Credential Manager via `ctypes`) is the default on Windows in
  v1, so this drawback applies only when the adopter explicitly
  passed `--allow-insecure-fallback` at `setup` time to opt out
  of Tier 2 (e.g., they're scripting against a service account
  and have decided env-var injection at run time is the right
  call, but want a dotfile floor for development). For those
  cases: domain-joined corporate fleets with Group Policy roaming
  profiles can present a permissive `%USERPROFILE%` DACL (local
  Administrators group includes helpdesk roles). The setup helper
  verifies the dotfile's DACL with `icacls` after creation and
  refuses non-zero unless the user passes `--allow-permissive-acl`,
  parallel to `--allow-insecure-fallback`. Even with the check,
  an org whose helpdesk is in the local Administrators group
  still reads the file. The remediation is to use Tier 2
  (Credential Manager) — which is the v1 default — or env-var
  injection (Tier 1).

- **Windows test matrix grows substantially.** Following the
  precedent from
  [`agent-spec-cli` plan § 643-646](../specs/agent-spec-cli/plan.md)
  ("a Windows row is documented" for cross-platform mechanics),
  the spec phase adds two buckets of Windows rows:

  *CI-runnable on `windows-latest` GitHub Actions runners:*
  dotfile CRLF tolerance (trailing-only `\r` strip);
  `pathlib.Path.home()` resolution to `%USERPROFILE%`;
  atomic rename via `os.replace`; `os.chmod` POSIX-guard
  (assert the call is skipped on `os.name != "posix"`);
  `icacls` DACL inspection against a real DACL on a temp file;
  `CredWriteW` / `CredReadW` / `CredDeleteW` / `CredFree` round-trip
  via ctypes (the GitHub runner's user session supports Credential
  Manager calls); UTF-16 `CredentialBlob` byte-equality
  round-trip; the no-argv-leak invariant for the Windows write
  path (assert no `cmdkey` or `subprocess` invocation with the
  token).

  *Local-Windows or manual QA only (not CI-runnable):*
  `getpass.getpass` tty-refusal — GitHub runners don't allocate a
  PTY for job steps; the unit test for this path monkeypatches
  `sys.stdin.isatty`, the *real* tty behavior is documented as a
  manual-QA row;
  `CRED_PERSIST_LOCAL_MACHINE` semantics across logoff — a CI job
  is a single session; survives-logoff is a manual-QA row;
  the `ERROR_NO_SUCH_LOGON_SESSION` hard-error path under
  `LocalSystem` service-account context — needs a scheduled task /
  service runner that CI doesn't provide; manual-QA row.

  Each manual-QA row in the spec carries a checklist line the
  release process exercises before tagging.

- **ctypes wrapping for `advapi32` is unfamiliar to most adopters.**
  The Windows Credential Manager path is under 100 lines (see
  § 2 for the pinned phrasing) of `ctypes`
  struct definitions and Win32 API calls — code the average
  catalogue contributor will not be comfortable modifying. The
  spec phase pins the API surface (`CredReadW`, `CredWriteW`,
  `CredDeleteW`, `CredFree` only) and documents the `CREDENTIAL`
  struct layout inline so the file stays a maintainable shape.
  Risk: ctypes type-mismatch bugs are silent (wrong-sized struct
  fields return garbage rather than crashing) — the test matrix
  has to round-trip values and assert exact byte-equality.

## Unresolved questions

1. **Linux `libsecret` tier — confirm-only.** Windows Credential
   Manager is in v1 (in-process ctypes against `advapi32.dll`,
   which is in every Windows install). Linux `libsecret` could be
   in v1 by the same shape (`ctypes.CDLL("libsecret-1.so.0")`
   with `OSError` fallback), but is deferred to v2 because the
   four corporate-Linux dev environments that actually matter all
   fail libsecret's happy path by default:

   - **Headless / SSH dev boxes:**
     [Ubuntu Launchpad #1420914](https://bugs.launchpad.net/bugs/1420914)
     confirms *"headless mode (such as in an ssh session) is not
     supported for libsecret"*.
   - **WSL2:** fails out-of-the-box with *"Cannot autolaunch D-Bus
     without X11 $DISPLAY"*
     ([microsoft/WSL #4254](https://github.com/microsoft/WSL/issues/4254));
     needs the `wsl-secret-service` bridge or a systemd-user-instance
     workaround.
   - **Docker dev containers:** known broken — *"dumps either
     pyobject or libsecret errors"*
     ([Azure SDK #19857](https://github.com/Azure/azure-sdk-for-python/issues/19857)).
   - **Python `keyring` library on Linux:** open issue
     [jaraco/keyring #514](https://github.com/jaraco/keyring/issues/514)
     ("Error communicating with dbus") with explicit fallback-chain
     recommendations to `PlaintextKeyring`.

   Pulling Linux into v1 means writing the fallback matrix for
   these four sub-cases as ACs in *this* spec, doubling its
   surface. Deferral keeps v1 scoped and v2 well-bounded.
   Reviewers: confirm-only — this is not a decide item.

## Follow-on artifacts

Filled in upon acceptance.

- **ADR-NNNN: Credential storage for credentialed skills** — records
  the tier order (env > keyring > user-scope dotfile at
  `~/.agent-ready/credentials.env`), the stdlib-only loader policy,
  and the two-layer architecture rule as a binding decision so
  future RFCs amend rather than relitigate.
- **ADR amendment: ADR-0002 § Consequences.** Extends the
  "hook-shaped primitives are forbidden at user scope" sentence
  with the precise definition this RFC adopts:
  *"hook-shaped" means a primitive that (i) binds to a runtime event
  (e.g. `UserPromptSubmit`, `PreToolUse`) **and** (ii) requires
  wiring-merge into a hand-edited shared file (e.g.
  `~/.claude/settings.json`, `.kiro/agents/<name>.json`). The
  conjunction is intentional: a primitive that satisfies only one
  of (i) or (ii) is **not** hook-shaped under this definition and
  is governed by its own RFC, not this ban.* The amendment lands
  as a normal PR (small, definitional) under RFC-0006's umbrella
  alongside this RFC's acceptance. RFC-0005's design also benefits
  from the frozen definition; it currently treats "hook-shaped" by
  example rather than by definition.
- **Spec: `docs/specs/skill-secrets/`** — implementation spec for
  `agentbundle creds` (subcommands, exit codes, schema format,
  walked-vs-explicit namespace discovery), the
  `agent_ready.credentials` loader (API shape, error types,
  precedence semantics), and the `creds-schema.toml` format.
  Tracks ACs for: the macOS Keychain integration (stdin-fed
  `/usr/bin/security`); the Windows Credential Manager integration
  (`ctypes` over `advapi32.CredReadW`/`CredWriteW`/`CredDeleteW`/
  `CredFree`, UTF-16 `CredentialBlob`, `CRED_TYPE_GENERIC`,
  `CRED_PERSIST_LOCAL_MACHINE`, `UserName = "<namespace>"` for
  Credential Manager UI grouping, all other `CREDENTIAL` fields
  (`Flags`, `Comment`, `LastWritten`, `AttributeCount`,
  `Attributes`, `TargetAlias`) zero-initialised via
  `ctypes.Structure` defaults, `agent-ready:<namespace>:<key>`
  target-name convention); the Win32 error-code dispatch matrix
  (`ERROR_NOT_FOUND` falls through to Tier 3;
  `ERROR_NO_SUCH_LOGON_SESSION` / `ERROR_INVALID_FLAGS` /
  `ERROR_LOGON_FAILURE` hard-fail with stderr naming the cause);
  the stdlib `.env` parser (CRLF trailing-only); the atomic-write
  contract; the "announce which tier" policy; the
  `--allow-insecure-fallback` opt-in (dotfile when keyring
  expected); and the `--allow-permissive-acl` opt-in (Windows-only,
  after `icacls` inspection).
- **Convention change: `docs/CONVENTIONS.md`** — adds the
  "Credentialed skills" section (storage tiers, argv ban,
  SKILL.md "Don't" block, anti-pattern register, corporate-network
  requirements).
- **Template addition: `docs/_templates/credentialed-skill-SKILL.md`**
  — the copy-pasteable "Don't" block + a minimal skill scaffold.
- **Pack-side: `packs/core`** — extends `core` with the
  `agent_ready.credentials` loader, the `agentbundle creds` verb,
  and the `conventions-check` rule extensions. No new pack.
- **Guide: `docs/guides/how-to/add-a-credentialed-skill.md`** — the
  Diátaxis how-to walking an adopter through the convention.
- **Roadmap entry**: `docs/ROADMAP.md` gains a new section for
  `skill-secrets` once the spec lands, plus a v2-libsecret roadmap
  stub citing this RFC's Q1 so the deferred Linux tier doesn't get
  lost.

## Amendments

- 2026-05-24 (cosmetic, post-acceptance): the credentialed-skill
  template's canonical landing path was named throughout this RFC as
  `docs/_templates/credentialed-skill-SKILL.md`. That directory was
  retired the same day (see [RFC-0002 § Amendments](0002-self-hosting.md#amendments))
  when its contents moved into per-skill `assets/` folders. The
  template should land at the analogous skill-relative path —
  i.e. inside the assets folder of whatever skill the credentialed-skill
  scaffolding ultimately ships under (typically a sibling skill in
  `packs/core/.apm/skills/<credentialed-skill-author-skill>/assets/`
  or, if it's a standalone template for any author to copy, the
  appropriate `assets/` location is decided when the implementing PR
  lands). The substantive convention (the "Don't" block + minimal
  scaffold) is unchanged; only the path is amended.

