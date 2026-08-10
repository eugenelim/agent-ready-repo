#!/usr/bin/env python3
"""Construction tests for tools/lint-plugin-roster.py.

The point of this gate is that it is NOT derived from the production predicate,
so its test must not be either. Every case builds a marketplace by hand and
asserts against the module's hard-coded rosters.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "lint_plugin_roster", Path(__file__).parent / "lint-plugin-roster.py"
)
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)

FAILURES: list[str] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        FAILURES.append(name)
        print(f"  FAIL {name}: {detail}")


def _marketplace(root: Path, names) -> None:
    d = root / ".claude-plugin"
    d.mkdir(parents=True, exist_ok=True)
    (d / "marketplace.json").write_text(
        json.dumps({"plugins": [{"name": n} for n in names]}),
        encoding="utf-8", newline="\n",
    )


def main() -> int:
    print("test-lint-plugin-roster:")

    _check("the two rosters do not overlap",
           not (lint.PUBLISHED & lint.NOT_PUBLISHED),
           f"overlap: {sorted(lint.PUBLISHED & lint.NOT_PUBLISHED)}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _marketplace(root, sorted(lint.PUBLISHED))
        _check("the exact published roster passes", lint.check(root) == [],
               f"got {lint.check(root)}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # THE case this gate exists for: a repo-only pack got widened and
        # published. The derived membership lint stays green here.
        _marketplace(root, sorted(lint.PUBLISHED) + ["core"])
        out = lint.check(root)
        _check("a widened repo-only pack fails",
               len(out) == 1 and "core" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Fail-closed truncation: absences alone would miss this.
        _marketplace(root, sorted(lint.PUBLISHED - {"architect"}))
        out = lint.check(root)
        _check("a silently dropped pack fails",
               len(out) == 1 and "architect" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _marketplace(root, sorted(lint.PUBLISHED) + ["brand-new-pack"])
        out = lint.check(root)
        _check("an unrostered pack forces a decision",
               len(out) == 1 and "brand-new-pack" in out[0], f"got {out}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        out = lint.check(root)
        _check("a missing marketplace fails", len(out) == 1, f"got {out}")

    if FAILURES:
        print(f"test-lint-plugin-roster: FAIL ({len(FAILURES)})", file=sys.stderr)
        return 1
    print("test-lint-plugin-roster: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
