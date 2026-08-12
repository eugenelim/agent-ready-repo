# Catalogue commands reference

All commands operate on a catalogue rooted at `--root` (defaults to the current directory).

## `agentbundle catalogue lint`

Validates pack sources against contracts without building.

```
agentbundle catalogue lint [--root ROOT] [--pack PACK] [--format {table,json}]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | `.` | Catalogue root directory |
| `--pack` | _(all)_ | Limit to a single pack name |
| `--format` | `table` | Output format: `table` or `json` |

Exits 0 when all checks pass; non-zero on any failure. Runs as step 2 of `catalogue verify`.

## `agentbundle catalogue verify`

Runs the full 18-step source pipeline: lint, schema validation, contract checks, build (into a temp
directory), self-host drift check, and more.

```
agentbundle catalogue verify [--root ROOT] [--pack PACK] [--archive ARCHIVE]
                             [--sha256-file SHA256_FILE] [--format {table,json}]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | `.` | Catalogue root directory (source mode) |
| `--pack` | _(all)_ | Limit to a single pack |
| `--archive` | _(none)_ | Path to a `.tar.gz` archive (archive mode) |
| `--sha256-file` | _(none)_ | SHA-256 sidecar for archive verification |
| `--format` | `table` | Output format |

When `--archive` is given, verify switches to archive mode: it checks the archive's SHA-256 against
the sidecar and validates archive members, paths, manifest digests, markers, and compatibility
without treating the installable artifact as a source catalogue.

## `agentbundle catalogue build`

Builds the catalogue dist tree (populates `dist/` or `--output`).

```
agentbundle catalogue build [--root ROOT] [--output OUTPUT]
                            [--pack PACK] [--recipe RECIPE]
                            [--format {table,json}]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | `.` | Catalogue root directory |
| `--output` | From `catalogue.toml` | Output directory |
| `--pack` | _(all)_ | Limit to a single pack |
| `--recipe` | _(default)_ | Recipe name or `.toml` path |
| `--format` | `table` | Output format |

## `agentbundle catalogue self-host`

Manages the self-host projection — writes or checks adapter-projected files (skills, agents, hooks,
commands) from `.apm/` sources into the adapter-expected layout.

Which adapter folders are written and whether Claude-specific root files (`CLAUDE.md`,
`.claude-plugin/marketplace.json`) are included depends on the effective adapter set.
Set `preferred-adapter` in `[distribution.agentbundle]` of `catalogue.toml` to control
this: an adapter not in the default `SELF_HOST_ADAPTERS` list (e.g. `"kiro-ide"`) restricts
projection to that adapter only and omits the Claude-specific files; absent or a value already
in `SELF_HOST_ADAPTERS` uses the default set (claude-code + codex).

```
agentbundle catalogue self-host [--root ROOT] [--check | --write] [--force]
                                [--windows] [--format {table,json}]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | `.` | Catalogue root directory |
| `--check` | — | Dry-run; exits non-zero if projection is out of date |
| `--write` | — | Write projected files |
| `--force` | `false` | Write even on a dirty working tree |
| `--windows` | `false` | With `--check`: run the AgentBundle and pack Windows-portability suite (bundler build, drift gates, path-sensitive tests, experience lint, pre-pr). CredBroker's package suite is separate. Requires `--check`. |
| `--format` | `table` | Output format |

One of `--check` or `--write` is required. `--windows` is only valid with `--check`.

## `agentbundle catalogue package`

Packages the built catalogue into a distributable archive with a SHA-256 sidecar and a channel
descriptor, following the Artifactory output layout.

```
agentbundle catalogue package --bundle BUNDLE --release RELEASE
                               --channel CHANNEL --output OUTPUT
                               [--root ROOT] [--source-revision REV]
                               [--minimum-agentbundle-version VER]
                               [--published-at TIMESTAMP]
```

| Flag | Required | Description |
|------|----------|-------------|
| `--bundle` | yes | Bundle/product identifier (e.g. `engineering`) |
| `--release` | yes | Release version string (e.g. `1.0.0`) |
| `--channel` | yes | Channel name (e.g. `stable`) |
| `--output` | yes | Output root directory |
| `--root` | no | Catalogue root (default: `.`) |
| `--source-revision` | no | VCS revision for audit metadata |
| `--minimum-agentbundle-version` | no | Minimum consumer version required |
| `--published-at` | no | Timestamp override (ISO-8601) |

Output layout:

```
<output>/catalogues/<bundle>/releases/<release>/<channel>/
  <bundle>-<release>.tar.gz        # archive
  <bundle>-<release>.tar.gz.sha256 # SHA-256 sidecar
  channel.json                     # channel descriptor (do not publish before verifying)
```

## `agentbundle catalogue sync-defaults`

Syncs `[catalogue.install-defaults]` from `catalogue.toml` into the self-hosted adapters' install
manifests.

```
agentbundle catalogue sync-defaults [--root ROOT] [--check | --write]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--root` | `.` | Catalogue root directory |
| `--check` | — | Dry-run; exits non-zero on drift |
| `--write` | — | Write updated manifests |
