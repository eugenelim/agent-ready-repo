#!/usr/bin/env python3
"""Smoke test for jira_align.py's banded exit-code contract
(docs/specs/credentialed-cli-exit-code-contract).

Deterministic, network-free coverage: token-on-CLI rejection exits 1 without
echoing the token; `--help` exits 0; banded constants + the `except Exception`
(not BaseException) catch-all + the import guard are present (source). The
runtime Tier2HardFail/HTTP mappings need a live keychain/server, so the
catch-all's shape is asserted by source instead. Behavioral checks self-skip
when deps aren't installed (the import guard exits 2 before main runs).

Run: python3 test_exit_codes.py     (exit 0 = all assertions pass)
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
CLI = HERE / "jira_align.py"
SRC = CLI.read_text(encoding="utf-8")


def _run(*args: str) -> subprocess.CompletedProcess:
    # Force UTF-8 in the child and on decode: the CLI writes non-ASCII
    # (em-dashes in its messages) to stderr, and on Windows the default
    # console / pipe codec is cp1252 — without this the child raises
    # UnicodeEncodeError emitting its own guard messages and the parent
    # mis-decodes, defeating the exit-code assertions below.
    return subprocess.run(
        [sys.executable, "-B", str(CLI), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
        },
    )


def _deps_installed() -> bool:
    proc = _run("--help")
    return not (proc.returncode == 2 and "missing dependency" in proc.stderr)


# CONVENTIONS § "The argv ban" canonical six — every credentialed CLI must
# refuse these before argparse can echo the value.
CANONICAL_BANNED_FLAGS = (
    "--token", "--api-token", "--api-key", "--bearer", "--pat", "--password",
)


def test_token_on_cli_rejected_exits_1_without_leak() -> None:
    secret = "SECRET-tok-abc123"  # noqa: S105 — test literal, not a real cred
    # Exercised per-flag so a deny-set regression on any canonical flag
    # fails here, not just on --token.
    for flag in CANONICAL_BANNED_FLAGS:
        proc = _run("check", flag, secret)
        assert proc.returncode == 1, f"{flag}: expected 1, got {proc.returncode}: {proc.stderr}"
        assert secret not in proc.stdout and secret not in proc.stderr, f"{flag}: token leaked"
        assert "must not be passed on the command line" in proc.stderr, \
            f"{flag}: exit 1 did not come from the token-reject guard"


def test_token_reject_wired_source() -> None:
    # Unconditional source check: the behavioral test above is in _BEHAVIORAL
    # and self-skips when deps aren't installed (the import guard exits before
    # main()'s reject runs) — i.e. the deps-less CI lint env. Guards the reject
    # wiring and the canonical-six deny-set against silent drift.
    assert SRC.count("_reject_token_on_cli") >= 2, "reject helper not defined+called"
    for flag in CANONICAL_BANNED_FLAGS:
        assert f'"{flag}"' in SRC, f"canonical banned flag {flag} missing from deny-set"


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
