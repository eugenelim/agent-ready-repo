"""Stdlib ``.env`` parser for credentialed primitives.

Intentionally less than ``python-dotenv``: this parser supports only the
narrow subset spec § AC2 pins as the contract for Tier-3 dotfile content
(``~/.agent-ready/credentials.env``). Stdlib-only — no ``python-dotenv``,
no third-party imports — per spec § Boundaries § Never do.

Supported:
    ``KEY=value``
    ``KEY="value with spaces"``
    ``KEY=value=with=equals``  (only the first ``=`` separates)
    ``# comment`` lines and blank lines

Refused (raises ``EnvParseError``):
    ``export KEY=value``         shell-export prefix
    ``KEY=$OTHER``               variable expansion
    quoted value spanning two physical lines

Trailing ``\\r`` from CRLF line endings is stripped; ``\\r`` *inside* a
quoted value is preserved (``KEY="a\\rb"`` → ``{"KEY": "a\\rb"}``).
"""

from __future__ import annotations

import pathlib
import re

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class EnvParseError(ValueError):
    """Raised when an ``.env`` file violates the supported subset.

    Messages include the 1-based physical line number so a log reader
    can jump to the offending line.
    """


def parse_env_file(path: pathlib.Path) -> dict[str, str]:
    """Parse the file at ``path`` into a ``{KEY: value}`` mapping.

    Reads with ``newline=""`` so embedded ``\\r`` bytes are preserved;
    only the trailing line terminator is stripped.
    """
    text = path.read_text(encoding="utf-8", newline="")
    result: dict[str, str] = {}
    for lineno, raw in enumerate(text.split("\n"), start=1):
        # Strip trailing \r (CRLF normalization). rstrip is bounded to the
        # tail, so embedded \r inside a quoted value is preserved.
        line = raw.rstrip("\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            raise EnvParseError(
                f"line {lineno}: `export KEY=value` shell-export syntax is not supported"
            )
        if "=" not in line:
            raise EnvParseError(
                f"line {lineno}: expected `KEY=value`, no '=' found"
            )
        key, _, value = line.partition("=")
        key = key.strip()
        if not _KEY_RE.match(key):
            raise EnvParseError(f"line {lineno}: invalid key {key!r}")
        if value.startswith('"'):
            if len(value) < 2 or not value.endswith('"'):
                raise EnvParseError(
                    f"line {lineno}: multi-line quoted values are not supported"
                )
            value = value[1:-1]
        if "$" in value:
            raise EnvParseError(
                f"line {lineno}: variable expansion (`$NAME`) is not supported"
            )
        result[key] = value
    return result
