# How to use an Artifactory-hosted catalogue

**Use this when:** You are an enterprise adopter configuring agentbundle for an internal Artifactory mirror, running CI-driven bulk upgrades, or operating in a network-restricted or MDM-managed environment.
**Prerequisites:** The `agentbundle` CLI on PATH (or a local clone with `pip install -e packages/agentbundle/`); for Flows A and D, a fork of the catalogue repository; for Flow B, a CI pipeline with access to `${{ secrets.AGENTBUNDLE_HTTP_BEARER_TOKEN }}`.
**Result:** One of six enterprise adoption flows completed, with no undocumented steps.

This guide covers six adoption patterns for enterprise environments:

- **[Flow A](#flow-a--org-bootstrap-from-fork)** — configure an org fork to ship your Artifactory channel at Layer 3
- **[Flow B](#flow-b--repo-scope-ci-upgrade)** — run scoped bulk upgrades with JSON output for CI pipelines
- **[Flow C](#flow-c--user-scope-mdm-update)** — distribute the org Artifactory channel via MDM
- **[Flow D](#flow-d--source-conflict-remediation)** — understand and recover from source-conflict errors
- **[Flow E](#flow-e--fully-disconnected-hosts)** — operate in air-gapped or fully offline environments
- **[Flow F](#flow-f--security-controls)** — review token handling, transport, integrity, and runtime controls

---

## Flow A — Org bootstrap from fork

Distribute the org Artifactory channel so that every developer who installs from the org fork receives it at Layer 3, without any manual `agentbundle config set source` step.

**Step 1 — Fork the catalogue repository.**

Create a fork of the catalogue repository under your org. For example, fork it to `git+https://git.example.test/acme/agent-catalogue`.

**Step 2 — Edit `agentbundle/_data/install-defaults.toml` in the fork.**

Open `agentbundle/_data/install-defaults.toml` inside `packages/agentbundle/` of your fork. Add an `[organization.artifactory]` block with `enabled = true` and all four required fields:

```toml
[organization.artifactory]
enabled    = true
base-url   = "https://artifactory.example.test"
repository = "agentbundle-local"
bundle     = "core"
channel    = "stable"
```

- `base-url` — the root URL of your Artifactory instance.
- `repository` — the Artifactory repository key where catalogues are stored.
- `bundle` — the pack bundle name (matches the `--bundle` value used when the archive was packaged).
- `channel` — the channel name (matches the `--channel` value used when the archive was packaged).

> All four fields are required when `enabled = true`. An `enabled = true` block with any field missing is malformed and causes `install` to exit 1 before touching any file.

The agentbundle CLI constructs the channel source from these fields:

```
catalogue+<base-url>/<repository>/catalogues/<bundle>/channels/<channel>.json
```

For the example above, that resolves to:

```
catalogue+https://artifactory.example.test/agentbundle-local/catalogues/core/channels/stable.json
```

**Step 3 — Package the catalogue archive and publish it.**

Before developers can install from Artifactory, you must package and upload the catalogue. From your fork root, run:

```bash
agentbundle package-catalogue \
  --root . \
  --bundle core \
  --release 0.13.7 \
  --channel stable \
  --output dist/
```

This produces a deterministic archive and a channel descriptor in `dist/`. See [publish-to-artifactory.md](publish-to-artifactory.md) for the complete five-step upload sequence once that guide ships; the `package-catalogue` reference is in [`../reference/agentbundle.md`](../reference/agentbundle.md).

**Step 4 — Distribute the fork.**

Make the fork available to your developers and instruct them to install from it:

```bash
pip install -e packages/agentbundle/ --index-url https://pypi.example.test/simple/
# or, from a local checkout of the fork:
pip install -e /path/to/your-fork/packages/agentbundle/
```

**What the developer receives.**

A developer who installs agentbundle from the org fork receives the `[organization.artifactory]` block baked into the wheel. On their first `agentbundle install --pack core`, the CLI resolves sources in the five-layer precedence chain:

| Layer | Source |
| ----- | ------ |
| 1 — Explicit arg | `--catalogue` flag passed at invocation time |
| 2 — User config | `[settings].source` in the user's `config.toml` |
| 3 — Org bootstrap | `[organization.artifactory]` in the installed wheel's `_data/install-defaults.toml` |
| 4 — Editable-clone | PEP 610 detection when agentbundle is installed from a local editable clone |
| 5 — Packaged fallback | `[defaults].source` in `install-defaults.toml` |

Layer 3 activates automatically from the org wheel. The developer does not run `agentbundle config set source`. Layers 1 and 2 still take precedence if a developer or their IDE sets them explicitly.

---

## Flow B — Repo-scope CI upgrade

Upgrade all installed packs at repo scope in a CI pipeline, capturing machine-readable JSON output for PR annotation or downstream tooling.

**The command:**

```bash
agentbundle upgrade --all --scope repo --format json --yes
```

- `--all` — upgrade every `(pack, adapter)` row at the scope; mutually exclusive with `--pack`.
- `--scope repo` — operate on the repo-scope state file in the current working directory.
- `--format json` — emit a single JSON document to stdout.
- `--yes` — required when `--format json` and `--dry-run` is not set; the JSON mode has no interactive confirmation prompt.

**stdout vs stderr.**

In `--format json` mode, stdout carries exactly one valid JSON document when the command exits. All progress messages, warnings, and diagnostics go to stderr. Do not mix stdout with stderr when consuming the output.

**JSON output shape (schema_version 1):**

```json
{
  "schema_version": 1,
  "command": "upgrade",
  "mode": "all",
  "scope": "repo",
  "dry_run": false,
  "sources": [
    {
      "source": "catalogue+https://artifactory.example.test/agentbundle-local/catalogues/core/channels/stable.json",
      "resolved": true,
      "error_code": null,
      "error_message": null
    }
  ],
  "rows": [
    {
      "pack": "core",
      "adapter": "claude-code",
      "scope": "repo",
      "source": "catalogue+https://artifactory.example.test/agentbundle-local/catalogues/core/channels/stable.json",
      "installed_version": "0.13.6",
      "available_version": "0.13.7",
      "status": "upgrade-available",
      "status_reason": null,
      "outcome": "completed"
    }
  ],
  "summary": {
    "total": 3,
    "upgrade_available": 1,
    "up_to_date": 2,
    "ahead": 0,
    "unknown": 0,
    "planned": 0,
    "completed": 1,
    "skipped": 2,
    "blocked": 0,
    "failed": 0,
    "not_attempted": 0
  }
}
```

**Partial failure.**

If an apply step fails midway, agentbundle stops immediately. It does not roll back rows that completed before the failure. The JSON output discloses this honestly:

- Completed rows show `"outcome": "completed"`.
- The failing row shows `"outcome": "failed"`.
- Remaining rows that were not attempted show `"outcome": "not-attempted"`.

The word "rolled back" does not appear in any output because no rollback occurs. Re-running `agentbundle upgrade --all --scope repo --format json --yes` after a partial failure is safe: rows already upgraded report `"outcome": "skipped"` with `"status": "up-to-date"`. The operation is idempotent for completed rows.

**GitHub Actions example:**

```yaml
name: agentbundle-upgrade

on:
  workflow_dispatch:

jobs:
  upgrade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install agentbundle
        run: pip install agentbundle

      - name: Upgrade all packs
        env:
          AGENTBUNDLE_HTTP_BEARER_TOKEN: ${{ secrets.AGENTBUNDLE_HTTP_BEARER_TOKEN }}
        run: |
          agentbundle upgrade --all --scope repo --format json --yes \
            > upgrade-result.json

      - name: Annotate PR
        run: |
          completed=$(jq '.summary.completed' upgrade-result.json)
          failed=$(jq '.summary.failed' upgrade-result.json)
          echo "Upgraded: $completed  Failed: $failed"
          if [ "$failed" -gt 0 ]; then
            jq -r '.rows[] | select(.outcome == "failed") | "FAILED: \(.pack) (\(.adapter))"' upgrade-result.json
            exit 1
          fi
```

The bearer token is read from the `AGENTBUNDLE_HTTP_BEARER_TOKEN` environment variable. It is never written to any file and never appears in the JSON output. See [Flow F](#flow-f--security-controls) for the full token-handling guarantee.

---

## Flow C — User-scope MDM update

Distribute the org Artifactory channel to developer workstations via MDM, so that every managed machine receives the correct source configuration without manual steps from developers.

### Path 1 — Layer 3 via a pre-configured wheel (MDM deploys the org fork wheel)

Package the org fork's `agentbundle` wheel (which contains the `[organization.artifactory]` block in `agentbundle/_data/install-defaults.toml`) and deploy it via MDM to managed machines.

The installer script run by MDM:

```bash
pip install agentbundle==0.14.0 \
  --index-url https://pypi.example.test/simple/
```

**What this activates:** Layer 3 (org bootstrap). The channel source is read from the wheel at install time; no developer action is needed.

### Path 2 — Layer 2 via a pre-written user config file (MDM writes `config.toml`)

MDM writes the agentbundle user config file to the correct platform-specific path before the developer first runs agentbundle:

| Platform | Config path |
| -------- | ----------- |
| macOS    | `~/Library/Application Support/agentbundle/config.toml` |
| Linux    | `${XDG_CONFIG_HOME:-~/.config}/agentbundle/config.toml` |
| Windows  | `%APPDATA%\agentbundle\config.toml` |

The config file content:

```toml
[settings]
source = "catalogue+https://artifactory.example.test/agentbundle-local/catalogues/core/channels/stable.json"
```

**What this activates:** Layer 2 (user config). This takes precedence over Layer 3 (org bootstrap), so use Path 2 when you want the user config to be the authoritative source and override any wheel-baked default. The `AGENTBUNDLE_HTTP_BEARER_TOKEN` environment variable must be available when the developer runs `agentbundle install` — MDM can inject it via a login script or a secrets manager integration.

**Choosing between Path 1 and Path 2:**

- Use **Path 1** (Layer 3) when you want to ship a complete, self-contained wheel that developers install exactly like the public agentbundle — the org source is baked in.
- Use **Path 2** (Layer 2) when you want the org Artifactory source to override even a developer's personal `agentbundle config set source` setting, or when you manage Python environments separately from the agentbundle wheel.

---

## Flow D — Source-conflict remediation

When `agentbundle install` is run and a pack at the same scope is already recorded as coming from a different source, the CLI refuses with a source-conflict error. This protects provenance: two installs of the same pack from different catalogues cannot coexist at the same scope.

**Error shape:**

```
error: source conflict for 'core' at repo scope
  incoming source:  catalogue+https://artifactory.example.test/agentbundle-local/catalogues/core/channels/stable.json
  existing rows:
    claude-code  catalogue+https://legacy.example.test/old-repo/catalogues/core/channels/stable.json
  --force does not override source conflicts.
  recovery paths:
    1. to migrate the existing row and record the new source, run:
         agentbundle upgrade --pack core \
           catalogue+https://artifactory.example.test/agentbundle-local/catalogues/core/channels/stable.json
    2. to start fresh from a different source, first uninstall all existing adapters:
         agentbundle uninstall --pack core
       then reinstall from the intended catalogue.
```

> `--force` does not bypass source-conflict refusal. `--force` removes leftover files from an interrupted install; it does not override the source-provenance check. These are separate gates. The error message states this explicitly.

**Recovery path 1 — migrate the legacy row (recommended).**

Running `upgrade --pack` from the intended new source migrates the existing row and records the new canonical source:

```bash
agentbundle upgrade --pack core \
  catalogue+https://artifactory.example.test/agentbundle-local/catalogues/core/channels/stable.json
```

This upgrades the pack in place. After this succeeds, `agentbundle install --pack core` from the same Artifactory source proceeds without conflict. Use this path when the pack content and your local edits should be preserved.

**Recovery path 2 — uninstall and reinstall (full reset).**

If you want a clean install from the new source:

```bash
agentbundle uninstall --pack core
agentbundle install \
  catalogue+https://artifactory.example.test/agentbundle-local/catalogues/core/channels/stable.json \
  --pack core
```

Tier-2 files (files you edited locally) and Tier-3 files (files outside the pack's projected paths) survive `uninstall` by design. Only the upstream-managed Tier-1 files are removed.

**Legacy rows.**

A row with `source = None` or `source = "agent-ready-repo"` (the legacy literal) represents unknown provenance. It triggers the same conflict refusal as a known-but-different source. The error message identifies these as "unknown/legacy source" and names both recovery paths above.

---

## Flow E — Fully disconnected hosts

In air-gapped or fully offline environments, pass a local directory path as the catalogue argument. No outbound network connection is needed.

**Prepare the catalogue archive on a connected machine.**

On a machine with network access, package the catalogue:

```bash
agentbundle package-catalogue \
  --root /path/to/catalogue-fork \
  --bundle core \
  --release 0.13.7 \
  --channel stable \
  --output /path/to/dist/
```

This produces two files in `dist/`:
- `core-0.13.7.tar.gz` — the deterministic archive
- `channels/stable.json` — the channel descriptor with a SHA-256 digest

Transfer both files to the air-gapped host (USB, secure file transfer, etc.) and place them under a consistent directory, for example `/opt/agentbundle/catalogues/`.

**Install on the disconnected host.**

```bash
agentbundle install /opt/agentbundle/catalogues/ --pack core
```

agentbundle reads the channel descriptor from the local path, verifies the SHA-256 digest of the archive, and installs without making any outbound connection. The `AGENTBUNDLE_HTTP_BEARER_TOKEN` environment variable is not needed for local-path catalogues.

**Upgrade on the disconnected host.**

Copy a newer archive to the same local directory and run:

```bash
agentbundle upgrade --pack core /opt/agentbundle/catalogues/
```

**Bulk upgrade on the disconnected host.**

If all installed packs at a scope use the same local catalogue path:

```bash
agentbundle upgrade --all --scope repo
```

The `--all` path resolves each row's source from the recorded `PackState.source`. Rows originally installed from the local path upgrade from that path without a network connection.

---

## Flow F — Security controls

This flow lists all security controls in agentbundle's `catalogue+https://` and `archive+https://` source implementation. Review these controls before deploying to a regulated or security-sensitive environment.

### Bearer token supply and redaction

- **Supply:** the bearer token for Artifactory-hosted catalogues is supplied exclusively via the `AGENTBUNDLE_HTTP_BEARER_TOKEN` environment variable. There is no `--token` flag and no config-file token field.
- **No persistence:** the token is never written to any state file, config file, install marker, or log file. It exists only in the process environment for the duration of the command.
- **No stdout exposure:** the token never appears in stdout — not in the JSON output, not in the table output, not in the `installed:` confirmation line.
- **No exception repr exposure:** if an HTTP request fails, the exception repr and the error message shown to the user have the `Authorization` header value removed. The redacted form is `Authorization: [redacted]`.
- **Error message redaction:** all error messages and log lines that reference a source URI have URL user-info (`user:pass@host` form) removed before display. The canonical source stored in state is similarly credential-free: `canonicalize_source()` rejects source strings containing URL user-info at write time.

### Cross-origin redirect refusal

- Before any HTTP request is sent, agentbundle pins the origin to the host in the originally-requested URL.
- Any redirect response that changes the `host` portion of the URL is refused before the redirect is followed. The bearer token is never forwarded to a host other than the one in the original request.

### TLS trust model

- agentbundle uses the OS or Python CA bundle (`SSL_CERT_FILE` or the `certifi` bundle when present). Certificate validation is always performed; there is no option to skip or weaken it.
- Proxies: `HTTPS_PROXY` and `NO_PROXY` environment variables are honored via Python's standard `urllib` proxy handling.

### No background daemon

- agentbundle has no background daemon, no persistent service, and no scheduled process. Every invocation is a discrete foreground command that exits when done. There is no agent process to compromise between invocations.

### SHA-256 integrity verification

- The channel descriptor (`channels/stable.json`) declares the SHA-256 digest of the archive it references.
- agentbundle verifies the downloaded archive byte-for-byte against the declared digest before any install write. A digest mismatch causes the command to exit with a non-zero code; no file is written to the project.
- The digest check covers the complete archive, not individual files within it.

### Extraction hardening

After the archive passes the digest check, extraction enforces the following:

| Rejection | Reason |
| --------- | ------ |
| Path-traversal entries (`../` or absolute paths) | Prevent writes outside the install root |
| Absolute path members | Same as above |
| Symlink members | Prevent symlink-following attacks |
| Hard link members | Prevent hard-link attacks |
| Device files | Prevent device-node creation |
| FIFO members | Prevent named-pipe creation |

Any archive member that matches one of these conditions causes extraction to abort before any file is written.

### Safety limits

To prevent resource exhaustion from malicious or malformed archives:

| Limit | Value |
| ----- | ----- |
| Channel descriptor | 1 MiB |
| Archive | 256 MiB |
| Archive members | 20,000 |
| Expanded size | 1 GiB |
| Request timeout | finite (no infinite wait) |

---

## Related

- [Install agentbundle from a clone](install-agentbundle-from-clone.md) — how to install the CLI from an org fork or local checkout.
- [Upgrade an installed pack](upgrade-packs.md) — single-pack and bulk upgrade flows.
- [`agentbundle` reference](../reference/agentbundle.md) — flag reference, source precedence chain, and `AGENTBUNDLE_HTTP_BEARER_TOKEN` documentation.
- [Publish to Artifactory](publish-to-artifactory.md) — the five-step sequence for packaging and uploading a catalogue archive to Artifactory.
