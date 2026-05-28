"""User-scope CLI config: read, write, unset of `~/.../agentbundle/config.toml`.

The file holds adapter-scoped settings the user can change post-pip-install
without monkey-patching `scope.DEFAULT_ADAPTER`. See
`docs/specs/agentbundle-config-subcommand/spec.md` for the contract.

Module surface:
  - `UserConfig` — frozen dataclass; today only `adapter: str | None`.
  - `_user_config_path(*, platform, env, home)` — pure path resolver.
  - `read_user_config(path)` — fail-soft loader (warns on malformed
    TOML or unknown adapter value; never raises).
  - `load_user_config()` — convenience: `read_user_config(_user_config_path())`.
  - `write_setting(path, key, value)` — validates and writes.
  - `unset_setting(path, key)` — removes and (when empty) deletes the file.

`UserConfig` is referenced from `agentbundle.scope.configured_adapter` only
as a forward-declared annotation (`from __future__ import annotations`), so
`scope.py` does not import this module at runtime. That keeps the cycle
broken: `user_config.py → scope.py` (for the shipped-adapter sanity check
in `read_user_config`) is the only direction.
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from agentbundle.config import _emit_basic_string


_KNOWN_KEYS: tuple[str, ...] = ("adapter",)


@dataclass(frozen=True)
class UserConfig:
    """Parsed `[settings]` table from the user-scope config file.

    `None` means "the key was absent from the file, the file did not
    exist, or the on-disk value failed validation." Callers cannot
    distinguish these three from the dataclass alone; the loader emits
    a stderr warning when validation drops a value.
    """

    adapter: str | None = None


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _user_config_path(
    *,
    platform: str | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve the OS-conventional path to `<dir>/agentbundle/config.toml`.

    Pure: no disk I/O. Defaults to `sys.platform`, `os.environ`,
    `Path.home()` for production callers; tests pass explicit values.
    """
    p = platform if platform is not None else sys.platform
    e: Mapping[str, str] = env if env is not None else os.environ
    h = home if home is not None else Path.home()
    if p == "darwin":
        base = h / "Library" / "Application Support"
    elif p == "win32":
        appdata = e.get("APPDATA")
        base = Path(appdata) if appdata else h / "AppData" / "Roaming"
    else:
        # Linux + every other POSIX falls back to XDG.
        xdg = e.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else h / ".config"
    return base / "agentbundle" / "config.toml"


# ---------------------------------------------------------------------------
# Read / load
# ---------------------------------------------------------------------------


def read_user_config(path: Path) -> UserConfig:
    """Load the config file fail-soft.

    A missing file returns `UserConfig()`. A malformed file emits a
    one-line stderr warning and returns `UserConfig()`. An on-disk
    `adapter` value not in `shipped_adapters_from_contract()` emits
    a one-line stderr warning listing the admissible names and
    returns `UserConfig()`.

    The fail-soft contract is load-bearing: `cli.py:main()` calls
    `load_user_config()` on every invocation including `--help` and
    `config path`, so a broken file must not block recovery commands.
    """
    if not path.exists():
        return UserConfig()
    try:
        with path.open("rb") as fh:
            parsed = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        print(
            f"agentbundle: warning: user config at {path} is malformed "
            f"({exc}); ignoring. Edit or remove the file with "
            f"`agentbundle config unset adapter` or hand-edit "
            f"`{path}`.",
            file=sys.stderr,
        )
        return UserConfig()

    settings = parsed.get("settings", {})
    if not isinstance(settings, dict):
        # An on-disk [settings] that's not a table is structurally
        # invalid — same fail-soft contract.
        print(
            f"agentbundle: warning: user config at {path} has a "
            f"non-table `settings` entry; ignoring.",
            file=sys.stderr,
        )
        return UserConfig()

    raw_adapter = settings.get("adapter")
    if raw_adapter is None:
        return UserConfig()
    if not isinstance(raw_adapter, str):
        print(
            f"agentbundle: warning: user config at {path} has a "
            f"non-string `adapter` value ({type(raw_adapter).__name__}); "
            f"ignoring.",
            file=sys.stderr,
        )
        return UserConfig()

    # Validate against the shipped adapter contract. Late import to
    # avoid a circular import at module load.
    from agentbundle.scope import shipped_adapters_from_contract

    shipped = shipped_adapters_from_contract()
    if raw_adapter not in shipped:
        print(
            f"agentbundle: warning: user config at {path} has an "
            f"adapter value ({raw_adapter!r}) that is not in the "
            f"current adapter contract. Admissible: {sorted(shipped)}. "
            f"Falling back to the built-in default; either edit the "
            f"file or run `agentbundle config set adapter <name>`.",
            file=sys.stderr,
        )
        return UserConfig()

    return UserConfig(adapter=raw_adapter)


def load_user_config() -> UserConfig:
    """Convenience: `read_user_config(_user_config_path())`.

    `cli.py:main()` calls this once per invocation and attaches the
    result to `args._user_config` before dispatching.
    """
    return read_user_config(_user_config_path())


# ---------------------------------------------------------------------------
# Write / unset (shared invariants)
# ---------------------------------------------------------------------------


def _parse_known_or_raise(path: Path) -> dict[str, Any]:
    """Parse the file as TOML and refuse any shape this writer can't
    safely round-trip.

    The fail-loud guards: any non-`[settings]` top-level table or any
    non-string value under `[settings]` (including nested tables, which
    `tomllib` materialises as dict values). Both cases raise with the
    same "future setting type not yet supported" message; the caller is
    expected to leave the file untouched.
    """
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        parsed = tomllib.load(fh)
    for top_key, value in parsed.items():
        if top_key != "settings":
            raise ValueError(
                f"agentbundle: future setting table not yet supported: "
                f"[{top_key}] in {path}. Hand-edit or remove the file."
            )
        if not isinstance(value, dict):
            raise ValueError(
                f"agentbundle: future setting type not yet supported: "
                f"non-table `settings` in {path}."
            )
        for k, v in value.items():
            if not isinstance(v, str):
                raise ValueError(
                    f"agentbundle: future setting type not yet supported: "
                    f"non-string value under [settings] (key {k!r}, "
                    f"type {type(v).__name__}) in {path}. Hand-edit or "
                    f"remove the file."
                )
    return parsed


def _emit_settings(settings: dict[str, str]) -> bytes:
    """Render `{key: str_value}` into a deterministic TOML file body.

    Keys are emitted in sorted order; values go through
    `_emit_basic_string` (same helper `agentbundle.config` uses for
    state-file writes). Empty `settings` returns empty bytes — the
    caller decides whether to write or delete.
    """
    if not settings:
        return b""
    lines = ["[settings]"]
    for k in sorted(settings):
        lines.append(f"{k} = {_emit_basic_string(settings[k])}")
    lines.append("")  # trailing newline
    return "\n".join(lines).encode("utf-8")


def _validate_key_value(key: str, value: str) -> None:
    """Refuse unknown keys; for `adapter`, refuse unknown values."""
    if key not in _KNOWN_KEYS:
        raise ValueError(
            f"agentbundle: unknown setting {key!r}. Known settings: "
            f"{list(_KNOWN_KEYS)}."
        )
    if key == "adapter":
        from agentbundle.scope import shipped_adapters_from_contract

        shipped = shipped_adapters_from_contract()
        if value not in shipped:
            raise ValueError(
                f"agentbundle: unknown adapter {value!r}. Admissible: "
                f"{sorted(shipped)}."
            )


def write_setting(path: Path, key: str, value: str) -> None:
    """Validate `(key, value)`, then write the file (creating parents).

    Idempotent on repeat with the same value (same bytes are written).
    Raises `ValueError` on validation failure or on a file shape this
    writer refuses; the on-disk file is not mutated in those cases.
    """
    _validate_key_value(key, value)
    parsed = _parse_known_or_raise(path)
    settings = dict(parsed.get("settings", {}))
    settings[key] = value
    body = _emit_settings(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


def unset_setting(path: Path, key: str) -> None:
    """Remove `key` from `[settings]`. Delete the file if it becomes
    empty AND no other top-level tables are present.

    Idempotent: unsetting a missing key (or operating on a missing
    file) is a no-op. Raises `ValueError` on an unknown key or on a
    file shape this writer refuses; the on-disk file is not mutated
    in those cases.
    """
    if key not in _KNOWN_KEYS:
        raise ValueError(
            f"agentbundle: unknown setting {key!r}. Known settings: "
            f"{list(_KNOWN_KEYS)}."
        )
    if not path.exists():
        return
    parsed = _parse_known_or_raise(path)
    settings = dict(parsed.get("settings", {}))
    if key not in settings:
        return
    del settings[key]
    other_tables = [k for k in parsed if k != "settings"]
    if not settings and not other_tables:
        path.unlink()
        return
    body = _emit_settings(settings)
    path.write_bytes(body)
