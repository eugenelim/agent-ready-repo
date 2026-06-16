#!/usr/bin/env python3
"""Self-test for tools/lint-sso-config.py (RFC-0035; AC15).

Runs the lint as a real subprocess against crafted fixtures (the documented
file-path invocation), asserting the exit code is the contract. Includes the
substring-trap no-false-positive cases (`session_filename`, `success_url_pattern`,
a value containing the literal "token").

Run directly: ``python tools/test-lint-sso-config.py`` (exit 0 = pass).
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

_LINT = Path(__file__).resolve().parent / "lint-sso-config.py"

_VALID = """
auth_default = "creds"

[sso]
profile = "jira"
base_url = "https://jira.example.invalid"
login_url = "https://sso.example.invalid/login"
success_url_pattern = "https://jira.example.invalid/secure/Dashboard.jspa"
cookie_domains = ["jira.example.invalid"]
validation_endpoint = "/rest/api/2/myself"
session_filename = "session-token.json"
ttl_hint_minutes = 480
"""


def _run(body: str) -> int:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "sso-config.toml"
        f.write_text(textwrap.dedent(body), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(_LINT), str(f)], capture_output=True, text=True
        ).returncode


CASES: list[tuple[str, str, int]] = [
    # (label, body, expected_exit)
    ("valid placeholder passes", _VALID, 0),
    (
        "no false-positive on session_filename / success_url_pattern / 'token' substring",
        _VALID,  # carries session_filename="session-token.json" + success_url_pattern
        0,
    ),
    ("auth_default != creds fails", _VALID.replace('"creds"', '"sso-cookie"'), 1),
    (
        "unknown [sso] key fails",
        _VALID.replace("ttl_hint_minutes = 480", 'ttl_hint_minutes = 480\nrogue = "x"'),
        1,
    ),
    (
        "non-*.invalid url host fails",
        _VALID.replace("jira.example.invalid", "jira.corp.example.com"),
        1,
    ),
    (
        "non-*.invalid cookie_domain fails",
        _VALID.replace(
            'cookie_domains = ["jira.example.invalid"]',
            'cookie_domains = ["jira.corp.example.com"]',
        ),
        1,
    ),
    (
        "cookie-value-shaped value fails",
        _VALID.replace(
            'session_filename = "session-token.json"',
            'session_filename = "AQIC5wM2LY4Sfczssession9eyJhbGciOi"',
        ),
        1,
    ),
]


def main() -> int:
    failures: list[str] = []
    for label, body, expected in CASES:
        got = _run(body)
        if got != expected:
            failures.append(f"{label}: expected exit {expected}, got {got}")

    # The real shipped files must pass (no-arg invocation scans the repo).
    repo_scan = subprocess.run(
        [sys.executable, str(_LINT)], capture_output=True, text=True
    ).returncode
    if repo_scan != 0:
        failures.append(f"repo scan: expected exit 0, got {repo_scan}")

    for f in failures:
        sys.stderr.write(f"FAIL {f}\n")
    if failures:
        return 1
    sys.stderr.write(f"ok — {len(CASES)} cases + repo scan passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
