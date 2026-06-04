#!/usr/bin/env python3
"""Smoke test for publish_page.py's banded exit-code contract
(docs/specs/credentialed-cli-exit-code-contract).

Deterministic, network-free coverage: `--help` exits 0; banded constants + the
`except Exception` (not BaseException) catch-all + the import guard are present
(source). Runtime Tier2HardFail/HTTP mappings need a live keychain/server, so
the catch-all's shape is asserted by source. The behavioral check self-skips
when deps aren't installed (the import guard exits 2 before main runs).

Run: python3 test_exit_codes.py     (exit 0 = all assertions pass)
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CLI = HERE / "publish_page.py"
SRC = CLI.read_text(encoding="utf-8")


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(CLI), *args],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _deps_installed() -> bool:
    proc = _run("--help")
    return not (proc.returncode == 2 and "missing dependency" in proc.stderr)


def test_help_exits_0() -> None:
    proc = _run("--help")
    assert proc.returncode == 0, f"--help should exit 0, got {proc.returncode}"


def test_banded_constants_defined() -> None:
    for const in ("EXIT_OK = 0", "EXIT_ERROR = 1", "EXIT_USER_ACTION = 2"):
        assert const in SRC, f"missing banded constant: {const}"


def test_no_stale_constants() -> None:
    for stale in ("EXIT_USER_ERROR", "EXIT_AUTH_ERROR", "EXIT_SERVER_ERROR"):
        assert stale not in SRC, f"stale constant still present: {stale}"


def test_catch_all_is_except_exception_not_baseexception() -> None:
    assert "except Exception" in SRC, "missing top-level except Exception catch-all"
    assert "except BaseException" not in SRC, "catch-all must not be BaseException"


def test_import_guard_present() -> None:
    assert "credentials_shim sibling not projected" in SRC, "missing shim guard"
    assert "missing dependency" in SRC, "missing dependency guard"


_BEHAVIORAL = {"test_help_exits_0"}


def main() -> int:
    deps = _deps_installed()
    tests = {k: v for k, v in sorted(globals().items()) if k.startswith("test_")}
    failures: list[str] = []
    skipped = 0
    for name, fn in tests.items():
        if name in _BEHAVIORAL and not deps:
            skipped += 1
            continue
        try:
            fn()
        except AssertionError as exc:
            failures.append(f"{name}: {exc}")
    for f in failures:
        sys.stderr.write(f"FAIL {f}\n")
    if failures:
        return 1
    note = f" ({skipped} behavioral skipped — deps not installed)" if skipped else ""
    sys.stderr.write(f"ok — {len(tests) - skipped} checks passed{note}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
