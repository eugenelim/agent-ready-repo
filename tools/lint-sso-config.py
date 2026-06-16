#!/usr/bin/env python3
"""Structural lint for upstream ``references/sso-config.toml`` (RFC-0035; AC15).

Every shipped ``sso-config.toml`` must be PLACEHOLDER-shaped so no real instance
config, captured cookie value, or non-``creds`` default can ship upstream:

  - ``auth_default == "creds"`` (the SSO-cookie path is opt-in by the adopter);
  - the ``[sso]`` key set is a subset of the declared connection-param schema;
  - every URL / cookie-domain host is a ``*.invalid`` placeholder;
  - no scalar value matches a cookie-value (opaque-token) shape.

This is **TOML-key structural** — it parses the file with ``tomllib`` and reasons
about keys and typed values, never a substring grep. So ``crowd.token_key`` (a
cookie *name*, not present here), ``session_filename``, and ``success_url_pattern``
never false-positive (contrast the credentialed-lint substring trap).

Usage::

    python tools/lint-sso-config.py            # scan the repo's shipped files
    python tools/lint-sso-config.py <file>...  # scan specific files (self-test)

Exit 0 = clean; 1 = findings (printed to stderr).
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

# The atlassian [sso] connection-param schema (keep in sync with each skill's
# scripts/_sso_config.py _ALLOWED_SSO_KEYS).
_ALLOWED_SSO_KEYS = frozenset(
    {
        "profile",
        "base_url",
        "login_url",
        "success_url_pattern",
        "cookie_domains",
        "validation_endpoint",
        "session_filename",
        "ttl_hint_minutes",
    }
)
_URL_KEYS = ("base_url", "login_url", "success_url_pattern")

# An opaque token blob: >=20 chars of a base64/urlsafe alphabet with NO ``.``,
# ``/``, ``:`` or whitespace — so URLs, paths, domains, and filenames (which all
# carry a separator) can't match, but a pasted JSESSIONID/crowd-token value does.
_COOKIE_VALUE_SHAPE = re.compile(r"^[A-Za-z0-9_\-+=]{20,}$")


def _host_of(value: str) -> str:
    return (urlsplit(value).hostname or "").lower()


def _walk_strings(obj: object):
    """Yield every scalar string anywhere in the parsed TOML."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_strings(v)


def lint_file(path: Path) -> list[str]:
    findings: list[str] = []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"{path}: cannot parse TOML: {exc}"]

    if data.get("auth_default") != "creds":
        findings.append(
            f"{path}: auth_default must be \"creds\" upstream "
            f"(got {data.get('auth_default')!r}); the SSO-cookie path is adopter opt-in"
        )

    sso = data.get("sso")
    if not isinstance(sso, dict):
        findings.append(f"{path}: missing [sso] table")
        sso = {}

    unknown = sorted(set(sso) - _ALLOWED_SSO_KEYS)
    if unknown:
        findings.append(f"{path}: unknown [sso] keys (outside the schema): {unknown}")

    for key in _URL_KEYS:
        if key in sso:
            host = _host_of(str(sso[key]))
            if not host.endswith(".invalid"):
                findings.append(
                    f"{path}: [sso].{key} host {host!r} is not a *.invalid placeholder"
                )

    for dom in sso.get("cookie_domains", []) or []:
        if not str(dom).endswith(".invalid"):
            findings.append(
                f"{path}: [sso].cookie_domains entry {dom!r} is not a *.invalid placeholder"
            )

    for value in _walk_strings(data):
        if _COOKIE_VALUE_SHAPE.match(value):
            findings.append(
                f"{path}: a value matches a cookie-value (opaque-token) shape: "
                f"{value[:8]}… — no captured cookie value may ship upstream"
            )

    return findings


def _default_paths() -> list[Path]:
    root = Path(__file__).resolve().parent.parent
    return sorted(root.glob("packs/*/.apm/skills/*/references/sso-config.toml"))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    paths = [Path(a) for a in args] if args else _default_paths()

    findings: list[str] = []
    for path in paths:
        findings.extend(lint_file(path))

    if findings:
        for f in findings:
            sys.stderr.write(f"sso-config lint: {f}\n")
        sys.stderr.write(f"sso-config lint: {len(findings)} finding(s)\n")
        return 1

    sys.stderr.write(f"sso-config lint: {len(paths)} file(s) scanned, 0 finding(s)\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
