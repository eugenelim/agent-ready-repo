#!/usr/bin/env python3
"""Self-test for tools/lint-pack-maintainers.py.

Pure-stdlib Python so the suite runs on Windows without an MSYS shell. Each
case writes a fixture `packs/` tree into a tempdir, runs the linter as a
subprocess against it with `--root`, and asserts the exit code and a
diagnostic substring.

The three failing cases are the three ways a manifest declares nobody — the
key absent, the array empty, and an entry carrying no usable name. They are
separate cases because a single `if not maintainers` would pass the third,
and the third is the one a careless edit actually produces.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

import selftest_harness

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "tools" / "lint-pack-maintainers.py"

_CHECKS = selftest_harness.CaseFailures("test-lint-pack-maintainers")

_NAMED = """[pack]
name = "good"
version = "1.0.0"

[[pack.maintainers]]
name = "someone"
"""

_NO_KEY = """[pack]
name = "nokey"
version = "1.0.0"
"""

_EMPTY_ARRAY = """[pack]
name = "empty"
version = "1.0.0"
maintainers = []
"""

_NAMELESS = """[pack]
name = "nameless"
version = "1.0.0"

[[pack.maintainers]]
email = "someone@example.invalid"
"""

_BLANK_NAME = """[pack]
name = "blank"
version = "1.0.0"

[[pack.maintainers]]
name = "   "
"""


def _root(base: pathlib.Path, packs: dict[str, str]) -> pathlib.Path:
    """Materialise a fixture catalogue root holding the given manifests."""
    base.mkdir(parents=True, exist_ok=True)
    for slug, body in packs.items():
        pack = base / "packs" / slug
        pack.mkdir(parents=True, exist_ok=True)
        (pack / "pack.toml").write_text(body, encoding="utf-8")
    return base


def _run(root: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(REPO_ROOT / "tools"),
    )


def _check(name: str, root: pathlib.Path, expected: int, needle: str) -> None:
    result = _run(root)
    combined = result.stdout + result.stderr
    if result.returncode != expected:
        _CHECKS.fail(name, f"exit {result.returncode}, expected {expected}: {combined}")
        return
    if needle not in combined:
        _CHECKS.fail(name, f"missing {needle!r} in: {combined}")


def main() -> int:
    with tempfile.TemporaryDirectory() as raw:
        tmp = pathlib.Path(raw)

        _check(
            "named-maintainer-passes",
            _root(tmp / "ok", {"good": _NAMED}),
            0,
            "each with a named maintainer",
        )

        # The three ways to declare nobody, each its own case.
        _check("absent-key", _root(tmp / "a", {"nokey": _NO_KEY}), 1, "no [[pack.maintainers]] entry")
        _check("empty-array", _root(tmp / "b", {"empty": _EMPTY_ARRAY}), 1, "no [[pack.maintainers]] entry")
        _check("entry-without-name", _root(tmp / "c", {"nameless": _NAMELESS}), 1, "names nobody")
        _check("whitespace-name", _root(tmp / "d", {"blank": _BLANK_NAME}), 1, "names nobody")

        # One good pack does not excuse a bad one in the same catalogue.
        _check(
            "mixed-catalogue-fails",
            _root(tmp / "mixed", {"good": _NAMED, "nokey": _NO_KEY}),
            1,
            "nokey",
        )

        # `_`-prefixed directories are templates, not shipped packs.
        _check(
            "underscore-prefixed-skipped",
            _root(tmp / "tmpl", {"_example": _NO_KEY, "good": _NAMED}),
            0,
            "each with a named maintainer",
        )

        # A catalogue holding only templates scanned a real directory and found
        # no shipped pack — distinct from having no packs/ at all.
        _check(
            "only-templates-is-empty-scan",
            _root(tmp / "onlytmpl", {"_example": _NAMED}),
            0,
            "no shipped packs",
        )

        # Absent packs/ is a pass with its own message, not a traceback.
        (tmp / "nopacks").mkdir()
        _check("absent-packs-dir", tmp / "nopacks", 0, "no packs/ directory")

        # An unreadable manifest is reported, not raised.
        broken = _root(tmp / "broken", {})
        bad = broken / "packs" / "broken"
        bad.mkdir(parents=True)
        (bad / "pack.toml").write_text("this is not = valid = toml\n", encoding="utf-8")
        _check("unreadable-manifest", broken, 1, "manifest unreadable")

        # The real catalogue must pass, so the rule ships green.
        _check("this-repository-passes", REPO_ROOT, 0, "each with a named maintainer")

    return _CHECKS.report()


if __name__ == "__main__":
    raise SystemExit(main())
