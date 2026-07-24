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


_REPO = Path(__file__).resolve().parent.parent
_JIRA = _REPO / "packs/atlassian/.apm/skills/jira/scripts"
_CONF = _REPO / "packs/atlassian/.apm/skills/confluence-crawler/scripts"
# The per-skill SSO files RFC-0023 forbids sharing as a projected module, so they
# are duplicated byte-for-byte across the two skills. Pin them equal here so a
# one-sided edit to the security-control loader fails loudly instead of drifting.
_DUPLICATED = ("_sso_config.py", "setup_sso.py", "test_sso_config.py", "test_setup_sso.py", "test_auth_selector.py")


def _load_module(path: Path, name: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so `@dataclass` (which resolves cls.__module__ via
    # sys.modules) works while loading the loader from a file path.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _parity_failures() -> list[str]:
    fails: list[str] = []
    for fn in _DUPLICATED:
        jb, cb = (_JIRA / fn), (_CONF / fn)
        if not jb.is_file() or not cb.is_file():
            fails.append(f"missing duplicated file: {fn}")
        elif jb.read_bytes() != cb.read_bytes():
            fails.append(f"{fn} differs between jira and confluence-crawler scripts/")
    # The lint's schema set must equal the loader's (the triplicated [sso] key set
    # must not drift between the lint that pins it and the loader that enforces it).
    try:
        lint_mod = _load_module(_LINT, "lint_sso_config")
        loader_mod = _load_module(_JIRA / "_sso_config.py", "sso_loader")
        if lint_mod._ALLOWED_SSO_KEYS != loader_mod._ALLOWED_SSO_KEYS:
            fails.append(
                "lint _ALLOWED_SSO_KEYS != loader _ALLOWED_SSO_KEYS "
                f"({sorted(lint_mod._ALLOWED_SSO_KEYS)} vs {sorted(loader_mod._ALLOWED_SSO_KEYS)})"
            )
    except Exception as exc:  # noqa: BLE001
        fails.append(f"schema-parity check crashed: {exc!r}")
    return fails


def main() -> int:
    failures: list[str] = []
    for label, body, expected in CASES:
        got = _run(body)
        if got != expected:
            failures.append(f"{label}: expected exit {expected}, got {got}")

    failures.extend(_parity_failures())

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
