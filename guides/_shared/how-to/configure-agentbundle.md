---
title: "Configure agentbundle"
summary: "Set a default adapter, choose the catalogue source, and use the environment variables and sign-in providers that agentbundle reads."
pack: _shared
kind: how-to
aliases:
  - guides/_shared/how-to/configure-adapter
---

# Configure agentbundle

Pin the agent tool and catalogue that `agentbundle` uses, so you stop passing flags on every install.

## Set a default adapter

```bash
agentbundle config set adapter cursor
```

The setting is user-global. It applies to repo and user installs. The other `config` actions:

```bash
agentbundle config path                   # where the file lives
agentbundle config get [<key>]            # effective value and where it came from
agentbundle config set <key> <value>      # validate and write
agentbundle config unset <key>            # remove; deletes the file if empty
```

The keys are `adapter` and `source`. Valid adapters are `claude-code`, `cursor`, `codex`, `copilot`, `gemini`, `kiro-ide`, `kiro-cli`.

An install picks its adapter in this order. The first match wins.

1. The `--adapter` flag.
2. The adapter recorded by an earlier install of the same pack.
3. Your config file.
4. At user scope only, the IDE folder found on disk: `~/.claude/`, `~/.codex/`, or `~/.kiro/`.
5. The default, `claude-code`.

### File location

| Platform | Path |
| --- | --- |
| macOS | `~/Library/Application Support/agentbundle/config.toml` |
| Linux | `${XDG_CONFIG_HOME:-~/.config}/agentbundle/config.toml` |
| Windows | `%APPDATA%\agentbundle\config.toml` |

The file is plain TOML. You can edit it by hand.

```toml
[settings]
adapter = "codex"
```

### When install refuses

An install refuses when the configured adapter is not allowed at the scope, or is not in the pack's `allowed-adapters`. Copilot, for example, is repo-only, so a configured `copilot` refuses a user-scope install. The message names the conflict and the ways out: `--scope`, `--adapter`, `agentbundle config set`, `agentbundle config unset`. Your configured value is kept.

An upgrade keeps the adapter the pack was installed with, whatever the config says. Config only shapes new installs.

## Choose the catalogue source

When you leave out the catalogue argument, `agentbundle` picks one source. The first match wins.

| Layer | Source | Set by |
| --- | --- | --- |
| 1 | Catalogue argument, used as given | `agentbundle install --pack <name> <catalogue>` |
| 2 | User config | `agentbundle config set source <catalogue>` |
| 3 | Organization Artifactory bootstrap | `[distribution.agentbundle.artifactory]` in `catalogue.toml`, baked in by `agentbundle catalogue sync-defaults --write` |
| 4 | Editable-install clone | `pip install -e <clone>`, found through PEP 610 `direct_url.json` |
| 5 | Packaged default | `[defaults].source` in `_data/install-defaults.toml`, set at publish time |

`source` in your config overrides every organization default. Set it only when you need a different catalogue.

`AGENTBUNDLE_NO_REMOTE=1` skips layers 3 and 4:

```bash
AGENTBUNDLE_NO_REMOTE=1 agentbundle install --pack core /path/to/local-catalogue
```

This applies to `install`, `upgrade`, `list-packs`, `list-profiles`, and `list-installed`.

## Environment variables

| Variable | Purpose |
| --- | --- |
| `AGENTBUNDLE_HTTP_BEARER_TOKEN` | Bearer token for `catalogue+https://` and `archive+https://` sources. A secret: do not log it or commit it. |
| `JFROG_CLI_SERVER_ID` | JFrog CLI profile to use when several match. Makes the JFrog provider required. |
| `AGENTBUNDLE_CA_BUNDLE` | Absolute path to a PEM CA bundle. Added to trust on `git+https://`, replaces trust on `catalogue+https://` and `archive+https://`. Fails if the path is missing. |
| `SSL_CERT_FILE`, `SSL_CERT_DIR` | OpenSSL trust paths. A stale path leaves trust empty, so unset them instead. |
| `REQUESTS_CA_BUNDLE` | Extra anchors for `git+https://` only. |
| `AGENTBUNDLE_NO_SYSTEM_TRUST` | Any non-empty value turns off the macOS keychain retry. |
| `AGENTBUNDLE_NO_REMOTE` | Any non-empty value skips source layers 3 and 4. |
| `HTTPS_PROXY`, `NO_PROXY` | Proxy and bypass list. Python reads them with no extra setup. |

See [Install agentbundle](install-agentbundle.md#behind-a-corporate-network) for TLS and proxy problems. The [command reference](../reference/agentbundle.md#environment-variables) has the full text of each variable.

## Protected catalogue sign-in

For an `https` catalogue that needs a sign-in, `agentbundle` tries four providers in order and stops at the first one that is available. A provider that is set up but broken fails the install with no fallback.

| Priority | Provider | Available when |
| --- | --- | --- |
| 1 | Bearer token | `AGENTBUNDLE_HTTP_BEARER_TOKEN` is non-empty |
| 2 | JFrog CLI | `jf` 2.105.0 or newer is on `PATH` and a profile's Artifactory URL prefixes the catalogue URL |
| 3 | `.netrc` | `~/.netrc` has a `machine` entry matching `host` or `host:port`, with safe permissions |
| 4 | Anonymous | Always |

`AGENTBUNDLE_CA_BUNDLE` does not reach the `jf api` subprocess. On Linux set `SSL_CERT_FILE` or `SSL_CERT_DIR`. On macOS add the CA to the system keychain.

Publishing a protected catalogue and shipping organization defaults are covered in [Set enterprise defaults](configure-catalogue-enterprise-distribution.md). Failure codes are in the [command reference](../reference/agentbundle.md#protected-catalogue-authentication).
