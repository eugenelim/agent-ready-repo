"""``agentbundle config`` — get/set/unset/path on the user-scope config file.

See `docs/specs/agentbundle-config-subcommand/spec.md` AC1, AC2, AC5–AC10.

The handler is intentionally small: an action-dispatch dict, a small
known-keys registry, and four `_do_*` workers. Future settings keys
should be a one-line addition to `_KNOWN_KEYS` plus their write-time
validator — no abstraction beyond that.
"""

from __future__ import annotations

import argparse
import sys

from agentbundle.scope import DEFAULT_ADAPTER
from agentbundle.user_config import (
    _KNOWN_KEYS,
    UserConfig,
    _user_config_path,
    read_user_config,
    unset_setting,
    write_setting,
)


def _do_path(args: argparse.Namespace) -> int:
    print(str(_user_config_path()))
    return 0


def _effective_value(key: str, cfg: UserConfig) -> tuple[str, str]:
    """Return `(value, provenance)` for key under the current config.

    Provenance is one of `file` (set in the on-disk config) or
    `builtin` (no on-disk value; resolver falls back to the constant).
    """
    if key == "adapter":
        if cfg.adapter is not None:
            return cfg.adapter, "file"
        return DEFAULT_ADAPTER, "builtin"
    if key == "source":
        if cfg.source is not None:
            return cfg.source, "file"
        # No builtin constant for `source`: the layer-4 packaged default is
        # not a config value, so an absent key reports `unset`, not `builtin`.
        return "", "unset"
    # Defense in depth — _KNOWN_KEYS gates entry to this branch.
    raise ValueError(f"agentbundle: unknown setting {key!r}")


def _do_get(args: argparse.Namespace) -> int:
    key = args.key
    if key is not None and key not in _KNOWN_KEYS:
        print(
            f"agentbundle: unknown setting {key!r}. Known settings: "
            f"{list(_KNOWN_KEYS)}.",
            file=sys.stderr,
        )
        return 1
    cfg = read_user_config(_user_config_path())
    keys = [key] if key is not None else list(_KNOWN_KEYS)
    for k in keys:
        value, provenance = _effective_value(k, cfg)
        print(f"{k}\t{value}\t({provenance})")
    return 0


def _do_set(args: argparse.Namespace) -> int:
    key = args.key
    value = args.value
    if key is None or value is None:
        print(
            "agentbundle: `config set` requires both a key and a value. "
            "Usage: agentbundle config set <key> <value>",
            file=sys.stderr,
        )
        return 1
    try:
        write_setting(_user_config_path(), key, value)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def _do_unset(args: argparse.Namespace) -> int:
    key = args.key
    if key is None:
        print(
            "agentbundle: `config unset` requires a key. Usage: "
            "agentbundle config unset <key>",
            file=sys.stderr,
        )
        return 1
    if key not in _KNOWN_KEYS:
        print(
            f"agentbundle: unknown setting {key!r}. Known settings: "
            f"{list(_KNOWN_KEYS)}.",
            file=sys.stderr,
        )
        return 1
    try:
        unset_setting(_user_config_path(), key)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


_ACTIONS = {
    "get": _do_get,
    "set": _do_set,
    "unset": _do_unset,
    "path": _do_path,
}


def run(args: argparse.Namespace) -> int:
    action = args.config_action
    handler = _ACTIONS.get(action)
    if handler is None:
        # argparse's `choices=` should catch this before dispatch; guard
        # anyway so a hand-built Namespace gets a clean refusal.
        print(
            f"agentbundle: unknown config action {action!r}. Known: "
            f"{list(_ACTIONS)}.",
            file=sys.stderr,
        )
        return 1
    return handler(args)
