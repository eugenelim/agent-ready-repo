"""``agentbundle oplog`` subcommands.

Subcommands:
  show  <pack> [--since=<ISO>]  — print last 50 entries (or all when < 50).
  clear <pack> --yes            — truncate ops.jsonl; requires --yes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

_DEFAULT_TAIL = 50


def run(args: argparse.Namespace) -> int:
    """Entry point for ``agentbundle oplog``."""
    sub: str | None = getattr(args, "oplog_sub", None)
    if sub is None:
        print("oplog: specify a subcommand (show, clear)", file=sys.stderr)
        return 1
    if sub == "show":
        return _cmd_show(args)
    if sub == "clear":
        return _cmd_clear(args)
    print(f"oplog: unknown subcommand {sub!r}", file=sys.stderr)
    return 1


def _ops_path(pack_name: str, args: argparse.Namespace, *, create: bool = True) -> Path:
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

    return _pack_dir(pack_name, state=state, home=home, create=create) / "ops.jsonl"


def _cmd_show(args: argparse.Namespace) -> int:
    pack_name: str = args.pack
    since: str | None = getattr(args, "since", None)

    ops_file = _ops_path(pack_name, args, create=False)
    if not ops_file.exists():
        return 0

    lines = ops_file.read_text(encoding="utf-8", errors="replace").splitlines()
    entries = []
    for raw in lines:
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if since is not None:
            ts = entry.get("ts", "")
            if ts < since:
                continue
        entries.append(entry)

    tail = entries[-_DEFAULT_TAIL:]
    for entry in tail:
        print(json.dumps(entry, separators=(",", ":")))
    return 0


def _cmd_clear(args: argparse.Namespace) -> int:
    pack_name: str = args.pack
    yes: bool = getattr(args, "yes", False)

    if not yes:
        print(
            "oplog clear: requires --yes to confirm truncation of ops.jsonl",
            file=sys.stderr,
        )
        return 1

    ops_file = _ops_path(pack_name, args, create=False)
    if ops_file.exists():
        ops_file.write_text("", encoding="utf-8", newline="\n")
    return 0
