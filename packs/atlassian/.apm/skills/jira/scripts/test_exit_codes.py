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


def test_stdio_utf8_hardening_present() -> None:
    # Windows console hardening: stdout/stderr are reconfigured to UTF-8 at
    # the top of file-path invocation, so non-ASCII output (UTF-8 JSON / CSV
    # payloads on stdout — which is errors="strict" by default and *does*
    # crash on a cp1252 console — plus em-dash messages) is safe. Must sit
    # before the import guard so the guard's own messages are covered too.
    # Source-asserted: a real non-UTF-8 Windows console isn't reproducible in
    # a portable test (proven by A/B in the PR: --help crashed on `→`
    # without this).
    assert 'reconfigure(encoding="utf-8")' in SRC, \
        "stdout/stderr UTF-8 hardening missing"
    assert SRC.index('if __package__ in (None, "") and __spec__ is None:') \
        < SRC.index('reconfigure(encoding="utf-8")'), \
        "UTF-8 hardening must sit inside the file-path-invocation gate"
    assert SRC.index('reconfigure(encoding="utf-8")') < SRC.index("missing dependency"), \
        "UTF-8 hardening must run before the import guard"


def _deps_installed() -> bool:
    """False when the import guard fires (deps/shim absent) → skip behavioral."""
    proc = _run("--help")
    return not (proc.returncode == 2 and "missing dependency" in proc.stderr)


# --- behavioral (real file-path invocation; need deps installed) -----------

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


def test_outofset_token_flag_value_scrubbed() -> None:
    # A token under a flag OUTSIDE the deny-set must not have its value
    # echoed by argparse's error(); the scrubbing parser redacts it. The
    # dotted JWT-shaped value also guards the regex charset (must include
    # `.`), per the security review.
    secret = "eyJhbGciOi." + "A" * 30 + ".Sig1234567890ABCDEF"  # noqa: S105 — JWT-shaped test literal
    proc = _run("check", "--bogus-flag", secret)
    assert secret not in proc.stdout and secret not in proc.stderr, \
        "out-of-set token value leaked"
    assert "<scrubbed>" in proc.stderr, "value not scrubbed by the parser"


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


_BEHAVIORAL = {
    "test_token_on_cli_rejected_exits_1_without_leak",
    "test_outofset_token_flag_value_scrubbed",
    "test_help_exits_0",
}


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
