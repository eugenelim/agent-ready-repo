#!/usr/bin/env python3
"""Seed the sso-broker profile from references/sso-config.toml.

Reads and **validates** the ``[sso]`` config through the loader (which applies the
credbroker scheme / root-relative primitives *before* the broker is
touched), then drives ``sso-broker register <profile>`` with the connection
parameters from the file. No cookie value is ever passed on argv — only validated
connection parameters (path-not-value). The headed-browser
capture and at-rest storage are the unchanged broker's job.

Run once after an enterprise pre-bakes ``references/sso-config.toml`` with
``auth_default = "sso-cookie"``::

    python scripts/setup_sso.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sibling modules importable when run as ``python scripts/setup_sso.py`` and
# append the credbroker user-scope floor (lowest precedence) so the loader's
# validation primitives resolve in a no-repo install. (Mirrors jira.py.)
_here = Path(__file__).resolve().parent
if str(_here) not in sys.path:
    sys.path.insert(0, str(_here))
_floor = Path("~/.agentbundle/lib").expanduser()
if _floor.is_dir() and str(_floor) not in sys.path:
    sys.path.append(str(_floor))

import subprocess  # noqa: E402

from _sso_config import SsoConfig, load_sso_config  # noqa: E402


def _broker_path() -> Path:
    return Path.home() / ".agentbundle" / "bin" / "sso-broker.py"


def build_register_argv(broker: Path, cfg: SsoConfig) -> list[str]:
    """Translate a validated SsoConfig into a ``sso-broker register`` argv.

    Only connection parameters cross argv — never a cookie value.
    """
    argv = [
        sys.executable,
        str(broker),
        "register",
        cfg.profile,
        "--login-url",
        cfg.login_url,
        "--success-url-pattern",
        cfg.success_url_pattern,
        "--validation-endpoint",
        cfg.validation_endpoint,
    ]
    for domain in cfg.cookie_domains:
        argv += ["--cookie-domain", domain]
    if cfg.session_filename:
        argv += ["--session-filename", cfg.session_filename]
    if cfg.ttl_hint_minutes:
        argv += ["--ttl-hint-minutes", str(cfg.ttl_hint_minutes)]
    return argv


def main(argv: list[str] | None = None) -> int:
    try:
        cfg = load_sso_config()  # validates before we touch the broker
    except Exception as exc:  # noqa: BLE001 — malformed config → don't register
        print(f"error: invalid sso-config.toml: {exc}", file=sys.stderr)
        return 2

    if cfg is None:
        print(
            'sso-config.toml: auth_default = "creds" — nothing to register '
            "(token auth is in effect).",
            file=sys.stderr,
        )
        return 0

    broker = _broker_path()
    if not broker.is_file():
        print(
            f"error: sso-broker not installed at {broker}; install the "
            "credential-brokers pack first.",
            file=sys.stderr,
        )
        return 2

    print(
        f"running: sso-broker register {cfg.profile} "
        "(opens a headed browser for SSO sign-in; the cookie jar is captured and "
        "stored by the broker — no cookie value passes through this helper).",
        file=sys.stderr,
    )
    return subprocess.run(build_register_argv(broker, cfg)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
