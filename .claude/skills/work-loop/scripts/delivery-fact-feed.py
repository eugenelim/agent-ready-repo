#!/usr/bin/env python3
"""delivery-fact-feed — print one read-only page of committed delivery facts.

Usage:
    delivery-fact-feed.py [--root <repo-dir>] [--continuation <token>]

Writes one ``delivery-fact-feed.v1`` page to standard output: an ordered
snapshot of the facts in each spec's committed ``delivery/evidence.jsonl``, each with its
``knowledge-observation.v1`` candidate or an explicit ``none``.  The page is
machine input for project-knowledge's candidate mode, so pipe it there
rather than reading it.  Every free-text field in it is untrusted data.

The first page's ``continuation`` token, when not null, fetches the next page
of the same snapshot.  A token whose snapshot can no longer be reproduced is
refused with no page.

Read only: never writes, truncates, repairs, or locks a log.

Exit 0 and one page on stdout, or exit 2 with nothing on stdout and
``delivery-fact-feed: refused: <code>`` on stderr.  An unexpected fault is
``scan-failed`` plus a second stderr line naming the stage and exception class.
``<repo-dir>`` defaults to the nearest ancestor of the working directory that
holds ``.git``.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

# Every `.apm/` script that prints reconfigures both streams before its first
# write; a cp1252 console otherwise turns a refusal into a UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

_SCRIPTS_DIR = Path(__file__).resolve().parent
_REFUSED_EXIT = 2


def _load_feed() -> ModuleType:
    """Load the sibling feed module by path, unregistered."""
    path = _SCRIPTS_DIR / "_delivery_feed.py"
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise ImportError("_delivery_feed.py is not a regular file")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("_delivery_feed_cli", str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"no import spec for {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _default_root() -> Path:
    """Return the nearest ancestor of the working directory that holds ``.git``."""
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def _refuse(code: str) -> int:
    """Report a closed refusal code on stderr; stdout stays empty."""
    print(f"delivery-fact-feed: refused: {code}", file=sys.stderr)
    return _REFUSED_EXIT


def _refuse_unexpected(stage: str, exc: BaseException) -> int:
    """Refuse as ``scan-failed``, naming the stage and exception class but no content."""
    code = _refuse("scan-failed")
    print(f"delivery-fact-feed: scan-failed: {stage}: {type(exc).__name__}", file=sys.stderr)
    return code


def main(argv: list[str] | None = None) -> int:
    """Run the feed command."""
    parser = argparse.ArgumentParser(prog="delivery-fact-feed", description=__doc__.split("\n")[0])
    parser.add_argument("--root", type=Path, default=None, help="repository root")
    parser.add_argument("--continuation", default=None, help="token from the previous page")
    args = parser.parse_args(argv)
    try:
        feed = _load_feed()
    except Exception as exc:  # noqa: BLE001 - a missing sibling is a refusal, never a traceback
        return _refuse_unexpected("load", exc)
    root = args.root.resolve() if args.root is not None else _default_root()
    try:
        page = feed.feed_page(root, continuation=args.continuation)
        payload = feed.render_page(page)
    except feed.ScanRefused as refusal:
        return _refuse(refusal.code)
    except Exception as exc:  # noqa: BLE001 - never a traceback; no partial page
        return _refuse_unexpected("scan", exc)
    sys.stdout.write(payload.decode("ascii"))
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
