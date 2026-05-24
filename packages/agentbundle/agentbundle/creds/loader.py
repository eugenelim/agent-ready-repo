"""Loader API and stdlib ``.env`` parser for credentialed primitives.

This module exposes the public surface a credentialed-primitive author
imports (via the ``agent_ready.credentials`` shim, per spec § AC3):

- ``load_credentials(namespace, required_keys, schema_path=None)`` — resolves
  credentials through Tier 1 (env var) → Tier 2 (OS keyring) → Tier 3
  (dotfile), first-hit-wins per key.
- ``Credentials`` — immutable, attribute-access view of the resolved values.
- ``EnvParseError`` — raised by ``parse_env_file`` on unsupported syntax.

Stdlib-only per spec § Boundaries § Never do — no ``python-dotenv``, no
``keyring``, no third-party imports. The Tier-2 backend is dispatched at
module-load time per AC4b: ``_keychain_macos`` iff ``sys.platform ==
"darwin"``, ``_credman_windows`` iff ``"win32"``, no Tier-2 backend on
other platforms (resolver falls through directly to Tier 3).

``.env`` parser (T2 surface, retained here):

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

import os
import pathlib
import re
import sys

from .exceptions import CredentialsMissingError, Tier2HardFailError

_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Tier-2 backend dispatch at module-load time (spec § AC4b). The backend
# modules are added by T4 (macOS) and T5 (Windows); until they land, the
# try/except yields ``None`` and the resolver skips Tier 2 on the matching
# platform. On Linux (and any non-Darwin / non-Windows platform), no import
# is attempted at all — Tier 2 is unavailable by absence.
if sys.platform == "darwin":
    try:
        from . import _keychain_macos as _tier2_backend  # type: ignore[no-redef]
    except ImportError:
        _tier2_backend = None  # type: ignore[assignment]
elif sys.platform == "win32":
    try:
        from . import _credman_windows as _tier2_backend  # type: ignore[no-redef]
    except ImportError:
        _tier2_backend = None  # type: ignore[assignment]
else:
    _tier2_backend = None


class Credentials:
    """Immutable, attribute-access view of a namespace's resolved credentials.

    Constructed by ``load_credentials``. The contract (spec § AC3) is:

    - Attribute access returns the resolved value:
      ``creds.API_TOKEN`` returns the resolved ``API_TOKEN`` for the
      namespace.
    - Attempting to assign or delete an attribute raises ``AttributeError``;
      callers cannot mutate the object after it leaves the loader.

    No ``__repr__`` override — the default ``object`` repr is intentional
    so a misplaced ``print(creds)`` never echoes the token bytes.
    """

    __slots__ = ("_namespace", "_values")

    def __init__(self, namespace: str, values: dict[str, str]) -> None:
        # Bypass the override below to seed the slot attributes.
        object.__setattr__(self, "_namespace", namespace)
        object.__setattr__(self, "_values", dict(values))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(
            f"Credentials is immutable; cannot set attribute {name!r}"
        )

    def __delattr__(self, name: str) -> None:
        raise AttributeError(
            f"Credentials is immutable; cannot delete attribute {name!r}"
        )

    def __getattr__(self, name: str) -> str:
        # __getattr__ is only invoked when normal lookup (including
        # __slots__) fails — so it serves the credential-name attribute
        # surface and nothing else. Names beginning with ``_`` are
        # internal; the slot lookup already handles ``_namespace`` /
        # ``_values``, so anything starting with ``_`` here is genuinely
        # absent.
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            values = object.__getattribute__(self, "_values")
        except AttributeError as exc:  # pragma: no cover — defensive
            raise AttributeError(name) from exc
        if name in values:
            return values[name]
        namespace = object.__getattribute__(self, "_namespace")
        raise AttributeError(
            f"namespace {namespace!r} has no credential {name!r}"
        )


def _tier1_env(namespace: str, key: str) -> str | None:
    """Resolve ``<NAMESPACE>_<KEY>`` from ``os.environ`` (spec § AC5).

    Empty-string env vars count as unset and return ``None`` so the
    resolver falls through to lower tiers.
    """
    env_name = f"{namespace.upper()}_{key}"
    value = os.environ.get(env_name)
    if not value:
        return None
    return value


def _tier2(namespace: str, key: str) -> str | None:
    """Resolve via the platform-specific keyring backend (spec § AC6, AC9).

    Returns ``None`` when the backend is absent (non-Darwin / non-Windows
    platforms, or backend modules not yet shipped) or reports a clean
    miss. Hard-fail error codes from the underlying API propagate as
    ``Tier2HardFailError`` per AC11.
    """
    if _tier2_backend is None:
        return None
    return _tier2_backend.read_credential(namespace, key)


def _tier3(namespace: str, key: str) -> str | None:
    """Resolve from the Tier-3 dotfile (spec § AC13).

    Stubbed in T3 — T6 implements the dotfile read. Returns ``None`` so
    the resolver continues toward ``CredentialsMissingError`` for any
    key that did not resolve at Tier 1 or Tier 2.
    """
    return None


def load_credentials(
    namespace: str,
    required_keys: list[str],
    *,
    schema_path: pathlib.Path | None = None,
) -> Credentials:
    """Resolve ``required_keys`` for ``namespace``, walking Tiers 1 → 2 → 3.

    First-hit-wins per key (spec § AC4): a key resolved at Tier 1 is not
    re-checked at lower tiers; mixing tiers across keys within one
    namespace is permitted.

    Raises ``CredentialsMissingError`` if any required key did not
    resolve at any tier. The error message names the namespace and the
    list of missing keys per AC3.

    The ``schema_path`` kwarg is reserved for T7 — primitive authors who
    load their own schema can pass it here; the default ``None`` defers
    to the canonical lookup (T7 wires the canonical path resolver).
    """
    resolved: dict[str, str] = {}
    missing: list[str] = []
    for key in required_keys:
        value = (
            _tier1_env(namespace, key)
            or _tier2(namespace, key)
            or _tier3(namespace, key)
        )
        if value:
            resolved[key] = value
        else:
            missing.append(key)
    if missing:
        raise CredentialsMissingError(
            f"namespace {namespace!r}: missing required credential(s): "
            f"{', '.join(missing)}"
        )
    return Credentials(namespace, resolved)


__all__ = [
    "Credentials",
    "CredentialsMissingError",
    "EnvParseError",
    "Tier2HardFailError",
    "load_credentials",
    "parse_env_file",
]


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
