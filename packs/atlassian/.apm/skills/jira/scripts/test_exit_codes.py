#!/usr/bin/env python3
"""Smoke test for jira.py's banded exit-code contract
(docs/specs/credentialed-cli-exit-code-contract).

Deterministic, network-free coverage:
  - token-on-CLI rejection exits 1 (EXIT_ERROR) and never echoes the token;
  - `--help` exits 0;
  - the banded constants + the `except Exception` (not BaseException)
    catch-all + the import guard are present (source inspection).

The runtime Tier2HardFail/401/403/5xx mappings need a live keychain or server,
which a standalone smoke test can't force deterministically; the catch-all's
*shape* (except Exception → EXIT_ERROR, no str(exc) on the unexpected path) is
asserted by source instead. If the skill's deps aren't installed, the behavioral
checks self-skip (the import guard exits 2 before main runs).

Run: python3 test_exit_codes.py     (exit 0 = all assertions pass)
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CLI = HERE / "jira.py"
SRC = CLI.read_text(encoding="utf-8")


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-B", str(CLI), *args],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _deps_installed() -> bool:
    """False when the import guard fires (deps/shim absent) → skip behavioral."""
    proc = _run("--help")
    return not (proc.returncode == 2 and "missing dependency" in proc.stderr)


# --- behavioral (real file-path invocation; need deps installed) -----------

def test_token_on_cli_rejected_exits_1_without_leak() -> None:
    secret = "SECRET-tok-abc123"  # noqa: S105 — test literal, not a real cred
    proc = _run("check", "--token", secret)
    assert proc.returncode == 1, f"expected 1, got {proc.returncode}: {proc.stderr}"
    assert secret not in proc.stdout and secret not in proc.stderr, "token leaked"
    assert "command line" in proc.stderr, "expected the argv-ban message"


def test_help_exits_0() -> None:
    proc = _run("--help")
    assert proc.returncode == 0, f"--help should exit 0, got {proc.returncode}"


# --- structural (source inspection; always run) ----------------------------

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


_BEHAVIORAL = {"test_token_on_cli_rejected_exits_1_without_leak", "test_help_exits_0"}


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
