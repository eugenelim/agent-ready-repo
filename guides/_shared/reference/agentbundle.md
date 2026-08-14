# `agentbundle` — reference

> The three operations a fresh PyPI user actually performs, plus the built-in help surface. For the full subcommand catalogue, run `agentbundle --help`.

## Install `agentbundle`

```bash
python -m pip install agentbundle
```

To install from a clone instead — for repo contributors or for users on an offline / corporate network — see [`../how-to/install-agentbundle-from-clone.md`](../how-to/install-agentbundle-from-clone.md).

After install, every subcommand is reachable via `agentbundle <verb>` or `python -m agentbundle <verb>`. `agentbundle --help` lists the full set.

## Install a pack

```bash
agentbundle install <catalogue-uri> --pack <pack-name>
```

`<catalogue-uri>` is a local path to a checked-out pack catalogue, or a `git+https://…` URL. `--pack` selects which pack from the catalogue to install.

Common flags:

| Flag                       | Effect                                                                                  |
| -------------------------- | --------------------------------------------------------------------------------------- |
| `--scope {repo,user}`      | Target install scope; default `repo`.                                                   |
| `--adapter <name>`         | Override the resolved adapter per-invocation (e.g. `claude-code`, `codex`, `kiro`).     |
| `--output <dir>`           | Output root; default depends on scope.                                                  |
| `--dry-run`                | Preview the per-file plan (action + tier + target path) to stdout and exit 0 without writing anything. Refused with `--force`. See [Preview before applying](#preview-before-applying). |

Run `agentbundle install --help` for the complete set.

## See what's installed

`agentbundle list-installed` reads your state files (not a catalogue) and reports every installed `(pack, adapter)` row across both scopes, with its version and whether an upgrade is available:

```bash
agentbundle list-installed
```

```
PACK        ADAPTER      SCOPE  INSTALLED  LATEST  STATUS
architect   claude-code  user   0.9.0      0.10.0  upgrade-available
architect   codex        user   0.9.0      0.10.0  upgrade-available
core        claude-code  repo   0.5.0      0.5.0   up-to-date
```

The `STATUS` is computed against the resolved catalogue: `up-to-date`, `upgrade-available`, or `unknown` (when the catalogue can't be resolved, or doesn't carry that pack). When the catalogue is unreachable the command still lists every row — `LATEST` shows `—` and `STATUS` is `unknown` — and exits 0; it never fails just because it couldn't reach a catalogue.

| Flag                  | Effect                                                                                       |
| --------------------- | -------------------------------------------------------------------------------------------- |
| `--scope {repo,user}` | Limit the listing to one scope; default lists both.                                          |
| `--no-check` / `--offline` | Skip the catalogue check entirely (no network): print only `PACK ADAPTER SCOPE INSTALLED`. |
| `--check-drift`       | Add a `DRIFT` column counting installed files edited locally since install (on-disk SHA differs from the recorded one). |

## Preview before applying

Both `agentbundle install` and `agentbundle upgrade` accept `--dry-run`: it runs the full read-only pre-flight, prints a per-file plan to stdout (one `<action> <tier> <target>` line each — `create` / `overwrite` / `companion`, with Tier-2 lines naming the `.upstream.<ext>` companion), and exits 0 without writing anything. Diagnostics and pre-flight failures go to stderr.

```bash
agentbundle install <catalogue-uri> --pack core --dry-run
agentbundle upgrade <catalogue-uri> --pack core --dry-run
```

`install --dry-run --force` is refused — `--force`'s destructive cleanup is incompatible with a read-only preview. See the [preview how-to](../how-to/preview-install-or-upgrade.md) for how to read the plan.

## Configure the default adapter

Once installed, `agentbundle` resolves the target adapter on every install via a fixed cascade:

1. The `--adapter` flag, if passed.
2. The state-hint from a prior install of the same pack (so an upgrade stays on the adapter it was originally installed under).
3. The user-config file, if you've set one.
4. At user scope only: an on-disk IDE probe — if you have `~/.claude/`, `~/.codex/`, or `~/.kiro/` populated, the matching adapter is picked. This is the auto-detection layer for users who never ran `agentbundle config set` and don't pass `--adapter`.
5. The built-in default (`scope.DEFAULT_ADAPTER`, currently `claude-code`).

`agentbundle config` reads and writes layer 3. Four actions:

```bash
agentbundle config path                   # where the file lives
agentbundle config get [<key>]            # show effective value + provenance
agentbundle config set <key> <value>      # validate and write
agentbundle config unset <key>            # remove (deletes file if empty)
```

Today the only registered key is `adapter`. Future keys would be added by the framework; the command surface stays the same.

### Example

```bash
$ agentbundle config path
/Users/alice/Library/Application Support/agentbundle/config.toml

$ agentbundle config get adapter
adapter	claude-code	(builtin)

$ agentbundle config set adapter codex
$ agentbundle config get adapter
adapter	codex	(file)

$ agentbundle install ./my-catalogue --pack demo
# resolves to codex unless overridden by --adapter or a state-hint.

$ agentbundle config unset adapter
$ agentbundle config get adapter
adapter	claude-code	(builtin)
```

### File location

| Platform | Path                                                                |
| -------- | ------------------------------------------------------------------- |
| macOS    | `~/Library/Application Support/agentbundle/config.toml`             |
| Linux    | `${XDG_CONFIG_HOME:-~/.config}/agentbundle/config.toml`             |
| Windows  | `%APPDATA%\agentbundle\config.toml`                                 |

The file is plain TOML with a single `[settings]` table:

```toml
[settings]
adapter = "codex"
```

You can hand-edit it; `agentbundle config` is a convenience over the file, not a gate.

### When `agentbundle install` will refuse

If you have `adapter = "<name>"` configured and either:

- `<name>` is not supported at the install scope (e.g. `copilot` configured but installing at user scope — Copilot is repo-only), or
- the pack's `[pack.install] allowed-adapters` doesn't include `<name>`,

then `agentbundle install` refuses with a message naming the conflict and listing the escape hatches (`--scope`, `--adapter`, `agentbundle config set`, `agentbundle config unset`). The configured value is preserved — the install just doesn't proceed under a value you didn't pick.

Upgrades preserve their existing adapter regardless of user-config. If you installed a pack under `claude-code`, then ran `agentbundle config set adapter codex`, then upgraded that pack, the upgrade stays on `claude-code` — `agentbundle config` shapes fresh installs, not relayouts of existing ones.

## What `upgrade` reports

`agentbundle upgrade` takes **no version** — the target is whatever the catalogue you point at declares (to pin a past version, point the catalogue at that git ref). It tells you honestly what it did:

- A real version change reports `upgraded: <pack> @ <scope> <from> -> <to>`.
- Re-running against the version you already have is a **re-apply**, not an upgrade: it reports `re-applied: <pack> @ <scope> <version> (already current)` — or names the count of locally edited files it kept as `.upstream` companions, when there were edits. Before it acts, it tells you up front how many of your edits will be preserved.
- A pack installed for **more than one adapter** at a scope needs `--adapter` to disambiguate; the refusal lists each adapter with its installed version, e.g. `pass --adapter to pick one: claude-code (0.9.0), codex (0.9.0)`. The same applies to `diff` and `uninstall`.

## Catalogue source resolution

Every source verb — `install`, `upgrade`, `list-packs`, `list-profiles`, `list-installed` — takes an optional trailing catalogue argument. When you omit it, the CLI resolves one through a five-layer, first-match-wins chain:

| Layer | Source | Set by |
| ----- | ------ | ------ |
| 1 | Explicit catalogue argument | `agentbundle install --pack <name> <catalogue>` — passed through verbatim, no validation |
| 2 | User config `[settings].source` | `agentbundle config set source <catalogue>` |
| 3 | Org Artifactory bootstrap | `[distribution.agentbundle.artifactory]` in `catalogue.toml`, baked into the wheel by `agentbundle catalogue sync-defaults --write` |
| 4 | Editable-install detection | `pip install -e <clone>` — auto-detected via PEP 610 `direct_url.json`; walks up to the enclosing `.git` root |
| 5 | Packaged default | `_data/install-defaults.toml` `[defaults].source` — baked into the wheel at publish time |

Setting `AGENTBUNDLE_NO_REMOTE=1` skips Layers 3 and 4 (the org Artifactory bootstrap and editable-install detection), falling through directly to Layer 5. See [`AGENTBUNDLE_NO_REMOTE`](#environment-variables) below.

## Environment variables

| Variable | Default | Purpose |
| -------- | ------- | ------- |
| `AGENTBUNDLE_HTTP_BEARER_TOKEN` | unset | Bearer token sent as `Authorization: Bearer <token>` on `catalogue+https://` and `archive+https://` requests. **Secret — do not log or persist to version control.** Example: `AGENTBUNDLE_HTTP_BEARER_TOKEN=<token> agentbundle install --pack core` |
| `AGENTBUNDLE_CA_BUNDLE` | unset | Absolute path to a PEM CA bundle for TLS verification, honoured on every catalogue source form. Raises `CatalogueError` if the path does not exist — including on `git+https://`, where the variable was previously ignored. **Semantics differ by source form:** on `git+https://` the bundle is *added* to the default trust store; on `catalogue+https://` and `archive+https://` it *replaces* it, which pins verification to your own authority. Example: `AGENTBUNDLE_CA_BUNDLE=/etc/ssl/corp-ca.pem agentbundle install --pack core` |
| `SSL_CERT_FILE`, `SSL_CERT_DIR`, `REQUESTS_CA_BUNDLE` | unset | Standard OpenSSL-family trust-store paths, honoured on `git+https://` sources only — the `catalogue+https://` and `archive+https://` paths read `AGENTBUNDLE_CA_BUNDLE` alone. Precedence is `AGENTBUNDLE_CA_BUNDLE`, then `SSL_CERT_FILE`, then `REQUESTS_CA_BUNDLE`; anchors are added to the default store, never substituted for it. A stale `REQUESTS_CA_BUNDLE` is ignored harmlessly. A stale `SSL_CERT_FILE` or `SSL_CERT_DIR` is **not** recoverable: OpenSSL resolves its default paths from those variables, so a bad value leaves the trust store empty and every fetch fails verification. Unset them rather than pointing them at a missing file. |
| `AGENTBUNDLE_NO_SYSTEM_TRUST` | unset | When set to any non-empty value, disables the operating-system trust fallback described in [Corporate networks](#corporate-networks) below. The underlying verification error is still reported, with the troubleshooting guidance appended. |
| `AGENTBUNDLE_NO_REMOTE` | unset | When set to any non-empty value, skips Layer 3 (org Artifactory bootstrap) and Layer 4 (editable-install detection), falling through to Layer 5. Use on hosts that cannot reach Artifactory, or in CI pipelines that resolve a local catalogue. Example: `AGENTBUNDLE_NO_REMOTE=1 agentbundle install --pack core /path/to/local-catalogue` |
| `HTTPS_PROXY` | unset | Proxy URL for outbound HTTPS requests. Read automatically by Python's `urllib.request.ProxyHandler`; no `agentbundle`-specific wiring needed. Example: `HTTPS_PROXY=http://proxy.example.com:3128 agentbundle install --pack core` |
| `NO_PROXY` | unset | Comma-separated list of hostnames that bypass the HTTPS proxy. Read automatically by Python's `urllib.request.ProxyHandler`. Example: `NO_PROXY=internal.example.com,localhost` |

## Corporate networks

On a network that inspects TLS traffic, a proxy re-signs outbound HTTPS with a
private root certificate authority. That authority is installed in the operating
system's trust store by your IT department, but Python reads its own certificate
file rather than the OS store, so a catalogue fetch fails with:

```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

`agentbundle` recovers from this on its own. When verification fails, it retries
once against the administrator-controlled trust anchors the operating system
already provides, and reports that it did so:

```
agentbundle: certificate verification failed for github.com; retrying with
operating-system trust anchors
```

The fallback reads one store: `/Library/Keychains/System.keychain`, the
administrator keychain. Your login keychain is never read, because it is
writable without administrator rights and a certificate landing there is not an
IT trust decision. Apple's own root program is not read either — the retry
already starts from the certificates Python trusts by default, so importing a
second curated root set would widen trust for no gain.

Verification stays strict: hostname checking and full chain validation apply on
every attempt, the fallback only ever *adds* trust anchors, and no flag or
variable disables verification. One caveat worth stating plainly: macOS lets an
administrator mark a certificate *Never Trust*, and the fallback does not read
those markings, so such a certificate is still used as an anchor. It is bounded
to a keychain only an administrator can write.

### Why the fallback is macOS-only

macOS is the only platform where Python ignores the operating system's trust
store. `ssl.SSLContext.load_default_certs` has a Windows branch and no macOS
branch, so:

| Platform | Trust source | Needs the fallback? |
| --- | --- | --- |
| **Windows** | Python loads the Windows `CA` and `ROOT` stores directly, honouring each certificate's trust settings | **No.** A root your IT team pushes by Group Policy or Intune is already trusted. |
| **Linux** | OpenSSL reads `/etc/ssl/certs` | No, provided the authority was installed there (`update-ca-certificates`). |
| **WSL** | Same as Linux — a WSL distribution does **not** inherit the Windows certificate store | **Yes, and the fallback cannot help.** See below. |
| **macOS** | OpenSSL reads a PEM file; the keychain is invisible to it | Yes — this is the case the fallback exists for. |

On Windows and Linux the install fails with a message saying no operating-system
anchors were available, rather than silently retrying against the same trust
store. On those platforms a verification failure has some *other* cause, so
reach for the troubleshooting steps in the error rather than assuming a
missing corporate root.

### When Python trusts nothing at all

A separate failure with the same error text, and the first one reported from the
field. A python.org macOS installer build ships without a configured certificate
store: until its `Install Certificates.command` runs, the interpreter trusts
**zero** authorities and every HTTPS request fails — no proxy involved.

Check it directly:

```bash
python3 -c "import ssl; print(ssl.get_default_verify_paths())"
```

`cafile=None` with no `capath` means the store is unconfigured. Fix it once:

```bash
open "/Applications/Python 3.x/Install Certificates.command"
# or point the interpreter at the system bundle
export SSL_CERT_FILE=/etc/ssl/cert.pem
```

`agentbundle` also repairs this case automatically on macOS: when it finds an
empty trust store it reads the system public certificate bundle
(`/etc/ssl/cert.pem`) alongside the administrator keychain, because the
administrator keychain holds private roots and cannot complete a public chain on
its own. That file is Apple's own TLS-purpose export — deliberately not a dump of
`SystemRootCertificates.keychain`, which additionally carries code-signing and
other single-purpose roots that have no business anchoring a TLS chain. The
recovery is announced on stderr and names the wider trust set. It rescues the
install; it does not fix the interpreter, so run the command above to stop every
other tool failing the same way.

### WSL

WSL is the case most likely to surprise a Windows-standardised organisation. Your
IT team pushes the corporate authority to the Windows certificate store, Windows
tools pick it up, and anything inside the WSL distribution does not — the two
have separate trust stores. Install the authority into the distribution, or point
`AGENTBUNDLE_CA_BUNDLE` at it:

```bash
# Debian/Ubuntu, from inside the WSL distribution
sudo cp corporate-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates
```

Export the authority from Windows first (Certificate Manager → Trusted Root
Certification Authorities → Export as Base-64 X.509).
### Egress allowlists

- A GitHub archive fetch redirects `github.com` →
  `codeload.github.com`. If your proxy permits only the first host, the fetch
  fails after certificates are working. Both hosts need to be reachable.

To opt out and see the raw verification error, set
`AGENTBUNDLE_NO_SYSTEM_TRUST=1`.

## Catalogue CI

`agentbundle catalogue lint`, `agentbundle catalogue verify`, and
`agentbundle catalogue package` are the portable commands for validating and
packaging a catalogue in CI. For the full pipeline contract — publication
ordering, exit codes, responsibility boundaries, and JSON output shapes — see
the [Catalogue CI contract](catalogue-ci-contract.md).

`agentbundle catalogue contracts list|show|export` enumerates, prints, or copies
the contract files bundled with the running version, with no network access.
See section 12 of the
[catalogue authoring standards](catalogue-authoring-standards.md).

## Other subcommands

See `agentbundle --help` for the full set (`list-packs`, `list-profiles`, `list-targets`, `list-installed`, `validate`, `render`, `adapt`, `diff`, `upgrade`, `uninstall`, `reconcile`, etc.). Each has its own `--help` page documenting its flags.
