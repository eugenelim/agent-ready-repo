# Pack Config and Operation Log API

> **Audience:** pack authors writing Python or shell scripts that need to resolve
> a user-scope directory, read configuration, or record operations.
>
> **Added in:** agentbundle 0.21.0 (RFC-0074).

---

## Overview

Three primitives give pack scripts a stable, cross-catalogue interface:

| Primitive | What it does |
|---|---|
| `pack_dir(pack_name)` | Resolve (and create) the user-scope directory for a pack |
| `load_pack_config(pack_name)` | Read the merged two-layer configuration dict |
| `write_entry(pack_name, action, src)` | Append a structured entry to the pack's operation log |

CLI equivalents are available via `agentbundle pack-config` and `agentbundle oplog`.

---

## `pack_dir`

```python
from agentbundle.config import pack_dir
from pathlib import Path

# Resolve and create ~/.agentbundle/atlassian/ (mode 0o700)
d: Path = pack_dir("atlassian")
```

**Signature:**
```python
def pack_dir(
    pack_name: str,
    *,
    state: State | None = None,
    home: Path | None = None,
) -> Path
```

**Resolution order (ADR-0058):**
1. If `state` rows for the pack exist, read `user-root` from them. All rows must agree; `PackRootConflict` raised if they disagree.
2. If no rows exist, fall back to `~/.agentbundle` (or `home / ".agentbundle"` when `home=` is given).

**Errors:**
- `ValueError` — `pack_name` fails slug grammar (`^[a-z0-9][a-z0-9-]*$`) or is reserved.
- `PackRootConflict(ValueError)` — multiple adapter rows disagree on `user-root`.
- `OSError` — the target path is a symlink or outside home.

**Reserved slugs:** `bin`, `state`, `credentials`, `state.toml`.

---

## `load_pack_config`

```python
from agentbundle.config import load_pack_config

cfg: dict = load_pack_config("atlassian")
url = cfg.get("url", "https://jira.example.com/")
```

**Signature:**
```python
def load_pack_config(
    pack_name: str,
    *,
    path: Path | None = None,
    state: State | None = None,
    home: Path | None = None,
) -> dict
```

**Two-layer cascade (ADR-0059):**

| Layer | Source | Precedence |
|---|---|---|
| 1 Baked | `_data/install-defaults.toml [pack-defaults.<pack>]` | Lower |
| 2 User | `<pack_dir>/config.toml` | Higher |

Shallow merge: user wins on key collision. Malformed user `config.toml` → `RuntimeWarning` + baked-only result.

Returns `{}` when both layers are absent.

**`path=` override:** reads the user layer from `path` instead of the default location.

---

## `write_entry`

```python
from agentbundle.oplog import write_entry

write_entry("atlassian", "install", src="git+https://example.com/catalogue")
write_entry("atlassian", "upgrade", src="...", dst="/path/to/file")
```

**Signature:**
```python
def write_entry(
    pack_name: str,
    action: str,
    src: str,
    dst: str | None = None,
    *,
    extra: dict | None = None,
    state: object = None,
    home: Path | None = None,
) -> None
```

**Emitted JSON object shape:**

```json
{"action": "install", "src": "git+https://example.com/", "ts": "2026-07-28T00:00:00+00:00"}
```

`ts` (ISO-8601 UTC) is always the last field. `dst` is omitted when `None`.

**Errors:**
- `ValueError` — `extra` contains a reserved key (`action`, `src`, `dst`, `ts`).
- `EntryTooLargeError` — base fields exceed 4096 bytes.

**Extra fields and truncation:** when `extra` is provided and the full entry would exceed 4096 bytes, `extra` fields are dropped and `"_truncated": true` is added.

**Atomicity:** on POSIX, a single `os.write()` to `O_CREAT|O_APPEND` guarantees non-interleaved lines on local filesystems. NFS is not supported — set `AGENTBUNDLE_NFS_OPLOG=1` to suppress warnings.

---

## Catalogue operator configuration

Declare per-pack defaults and a custom user directory in `catalogue.toml`:

```toml
[catalogue]
user-dir = "~/custom-dir"   # optional; defaults to ~/.agentbundle

[pack-defaults.atlassian]
url = "https://jira.yourorg.com/"

[pack-defaults.github]
org = "example-org"
```

Run `agentbundle catalogue sync-defaults --write` after editing to bake the values into `_data/install-defaults.toml`.

`user-dir` must start with `~/`. Absolute paths outside `$HOME` are rejected.

---

## CLI — `agentbundle pack-config`

```
agentbundle pack-config show <pack>
agentbundle pack-config get  <pack> <key>
agentbundle pack-config set  <pack> <key> <value>
agentbundle pack-config unset <pack> <key>
```

`show` prints all keys labeled `(baked default)` or `(user override)`.
`get` exits 1 when the key is absent.

---

## CLI — `agentbundle oplog`

```
agentbundle oplog show  <pack> [--since=<ISO>]
agentbundle oplog clear <pack> --yes
```

`show` prints the last 50 entries (or all when fewer). `--since` filters to entries at or after the given ISO-8601 timestamp.

`clear` truncates `ops.jsonl`. `--yes` is always required — there is no TTY exception.
