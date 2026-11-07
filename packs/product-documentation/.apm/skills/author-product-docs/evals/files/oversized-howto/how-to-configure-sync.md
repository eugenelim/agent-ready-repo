# Configure sync for Fieldlog

Fieldlog stores field notes on your machine and syncs them to a shared workspace. This page explains how sync works, lists every setting, gives a full config template, and walks through setting up your first sync.

## Background

Fieldlog was built around an offline-first design. Notes are written to a local SQLite store, and a sync worker pushes them to the server in batches. The worker keeps a queue table with one row per pending note, a vector clock per device, and a tombstone table for deletions. When two devices edit the same note, the conflict resolver compares vector clocks first and falls back to timestamps. The queue is drained in order, and each batch is wrapped in a transaction so a failed request leaves the queue unchanged. The design trades some write latency for the ability to work with no network at all.

The worker runs inside the main process on a timer. It wakes every `sync.interval` seconds, takes up to `sync.batch_size` rows, and posts them. On a 429 or 5xx response it applies exponential backoff up to `sync.retry_limit` attempts. Tombstones are kept for 30 days so that a device that was offline can still learn about deletions.

## Set up your first sync

1. Open a terminal and run `fieldlog init`.
2. Run `fieldlog auth login` and paste your token.
3. Run `fieldlog sync now`.
4. Run `fieldlog sync status` and check that the queue is empty.
5. Now change a setting. Open the config file and set `sync.interval` to 60. Save it and run `fieldlog sync now` again.
6. If you want to change conflict handling, read the Settings table below and choose a policy.
7. If you work on a metered connection, also set `sync.compress` to true and `sync.batch_size` to 20.
8. If you use a proxy, set `network.proxy`. Then run `fieldlog doctor` to check the proxy.

## Settings

| Setting | Type | Default | What it does |
| --- | --- | --- | --- |
| `sync.interval` | integer | `300` | Seconds between sync runs. |
| `sync.batch_size` | integer | `50` | Notes sent per request. |
| `sync.retry_limit` | integer | `5` | Retries before a note is marked failed. |
| `sync.retry_wait` | integer | `10` | Seconds to wait between retries. |
| `sync.conflict_policy` | string | `newest` | One of newest, local, remote. |
| `sync.compress` | boolean | `true` | Compress payloads. |
| `sync.timeout` | integer | `30` | Request timeout in seconds. |
| `storage.path` | string | `~/fieldlog` | Folder that holds local notes. |
| `storage.max_size_mb` | integer | `512` | Cap for the local store. |
| `storage.prune_after_days` | integer | `90` | Delete synced notes older than this. |
| `network.proxy` | string | `none` | Proxy URL, if any. |
| `network.tls_verify` | boolean | `true` | Verify server certificates. |
| `network.user_agent` | string | `fieldlog` | Value of the user agent header. |
| `log.level` | string | `info` | One of debug, info, warn, error. |
| `log.file` | string | `none` | Write logs to this file. |
| `log.rotate_mb` | integer | `10` | Rotate the log at this size. |
| `auth.token_ttl` | integer | `3600` | Seconds a session token lasts. |
| `auth.refresh` | boolean | `true` | Refresh tokens before they expire. |
| `ui.theme` | string | `light` | One of light, dark. |
| `ui.confirm_delete` | boolean | `true` | Ask before deleting a note. |

## Full config template

Copy this file to `~/.config/fieldlog/config.toml` and edit it.

```toml

[sync]
# Seconds between sync runs.
interval = 300
# Notes sent per request.
batch_size = 50
# Retries before a note is marked failed.
retry_limit = 5
# Seconds to wait between retries.
retry_wait = 10
# One of newest, local, remote.
conflict_policy = "newest"
# Compress payloads.
compress = true
# Request timeout in seconds.
timeout = 30

[storage]
# Folder that holds local notes.
path = "~/fieldlog"
# Cap for the local store.
max_size_mb = 512
# Delete synced notes older than this.
prune_after_days = 90

[network]
# Proxy URL, if any.
proxy = "none"
# Verify server certificates.
tls_verify = true
# Value of the user agent header.
user_agent = "fieldlog"

[log]
# One of debug, info, warn, error.
level = "info"
# Write logs to this file.
file = "none"
# Rotate the log at this size.
rotate_mb = 10

[auth]
# Seconds a session token lasts.
token_ttl = 3600
# Refresh tokens before they expire.
refresh = true

[ui]
# One of light, dark.
theme = "light"
# Ask before deleting a note.
confirm_delete = true
```

## How the queue table is laid out

The queue table has the columns `id`, `note_id`, `op`, `payload`, `device_clock`, `attempts`, and `last_error`. The `op` column holds `put` or `delete`. A row is deleted only after the server acknowledges the batch that contains it. If the process is killed mid-batch, the rows stay and are sent again, so the server must treat repeated `put` operations as idempotent. The tombstone table has `note_id`, `deleted_at`, and `device_clock`, and a nightly job removes rows older than 30 days.

## Troubleshooting

If sync stalls, run `fieldlog sync status`. If the queue grows, check `log.file` for 429 responses. If a note keeps failing, look at `last_error` in the queue table with the SQLite shell.
