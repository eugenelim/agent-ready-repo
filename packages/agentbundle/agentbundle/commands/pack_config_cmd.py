"""``agentbundle pack-config`` subcommands.

Subcommands:
  get   <pack> <key>           — print effective value; exit 1 if absent.
  set   <pack> <key> <value>   — write key to user config.toml.
  unset <pack> <key>           — remove key from user config.toml.
  show  <pack>                 — show all keys with (baked default) / (user override) labels.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse


def run(args: argparse.Namespace) -> int:
    """Entry point for ``agentbundle pack-config``."""
    sub: str | None = getattr(args, "pack_config_sub", None)
    if sub is None:
        print("pack-config: specify a subcommand (get, set, unset, show)", file=sys.stderr)
        return 1
    if sub == "get":
        return _cmd_get(args)
    if sub == "set":
        return _cmd_set(args)
    if sub == "unset":
        return _cmd_unset(args)
    if sub == "show":
        return _cmd_show(args)
    print(f"pack-config: unknown subcommand {sub!r}", file=sys.stderr)
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_baked_only(pack_name: str) -> dict:
    """Return the baked [pack-defaults.<pack>] layer only."""
    import importlib.resources

    try:
        resource = importlib.resources.files("agentbundle").joinpath(
            "_data/install-defaults.toml"
        )
        if resource.is_file():
            raw = tomllib.loads(resource.read_text(encoding="utf-8"))
            return raw.get("pack-defaults", {}).get(pack_name, {})
    except Exception:
        pass
    here = Path(__file__).resolve()
    defaults_path = here.parents[1] / "_data" / "install-defaults.toml"
    if defaults_path.exists():
        try:
            raw = tomllib.loads(defaults_path.read_text(encoding="utf-8"))
            return raw.get("pack-defaults", {}).get(pack_name, {})
        except Exception:
            pass
    return {}


def _load_user_config(config_path: Path) -> dict:
    """Read user config.toml; return {} when absent or malformed."""
    import warnings

    if not config_path.exists():
        return {}
    try:
        return tomllib.loads(config_path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError, OSError) as exc:
        warnings.warn(
            f"pack-config: malformed config.toml at {config_path}: {exc}",
            RuntimeWarning,
            stacklevel=3,
        )
        return {}


def _write_toml_simple(path: Path, data: dict) -> None:
    """Write *data* as a simple TOML file (string values only, no sections)."""
    from agentbundle.config import _emit_basic_string, _toml_key

    lines = []
    for k in sorted(data):
        lines.append(f"{_toml_key(k)} = {_emit_basic_string(str(data[k]))}")
    path.write_text("\n".join(lines) + "\n" if lines else "", encoding="utf-8", newline="\n")


def _resolve_config_path(
    args: argparse.Namespace, pack_name: str, *, create: bool = True
) -> Path:
    from agentbundle import safety
    from agentbundle.config import load_state
    from agentbundle.config import pack_dir as _pack_dir

    home_arg = getattr(args, "home", None)
    home = Path(home_arg) if home_arg else None

    state = None
    try:
        state_path = safety.user_state_path(home=home)
        if state_path.exists():
            state = load_state(state_path)
    except Exception:
        pass

    return _pack_dir(pack_name, state=state, home=home, create=create) / "config.toml"


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------


def _cmd_get(args: argparse.Namespace) -> int:
    from agentbundle import safety
    from agentbundle.config import load_pack_config, load_state

    pack_name: str = args.pack
    key: str = args.key
    home_arg = getattr(args, "home", None)
    home = Path(home_arg) if home_arg else None

    state = None
    try:
        state_path = safety.user_state_path(home=home)
        if state_path.exists():
            state = load_state(state_path)
    except Exception:
        pass

    effective = load_pack_config(pack_name, state=state, home=home)
    if key not in effective:
        print(f"pack-config get: key {key!r} not set for pack {pack_name!r}", file=sys.stderr)
        return 1
    print(effective[key])
    return 0


def _cmd_set(args: argparse.Namespace) -> int:
    pack_name: str = args.pack
    key: str = args.key
    value: str = args.value

    config_path = _resolve_config_path(args, pack_name)
    current = _load_user_config(config_path)
    current[key] = value
    _write_toml_simple(config_path, current)
    return 0


def _cmd_unset(args: argparse.Namespace) -> int:
    pack_name: str = args.pack
    key: str = args.key

    config_path = _resolve_config_path(args, pack_name)
    current = _load_user_config(config_path)
    if key in current:
        del current[key]
        _write_toml_simple(config_path, current)
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    from agentbundle import safety
    from agentbundle.config import load_pack_config, load_state

    pack_name: str = args.pack
    home_arg = getattr(args, "home", None)
    home = Path(home_arg) if home_arg else None

    state = None
    try:
        state_path = safety.user_state_path(home=home)
        if state_path.exists():
            state = load_state(state_path)
    except Exception:
        pass

    baked = _load_baked_only(pack_name)
    effective = load_pack_config(pack_name, state=state, home=home)

    all_keys = sorted(set(baked) | set(effective))
    if not all_keys:
        print(f"(no configuration for pack {pack_name!r})")
        return 0

    config_path = _resolve_config_path(args, pack_name, create=False)
    user = _load_user_config(config_path)

    for k in all_keys:
        val = effective.get(k, "")
        label = "(user override)" if k in user else "(baked default)"
        print(f"{k} = {val!r}  {label}")
    return 0
