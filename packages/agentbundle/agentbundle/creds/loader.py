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

import dataclasses
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tomllib

from .exceptions import (
    CredentialsMissingError,
    PermissiveAclError,
    SchemaError,
    Tier2HardFailError,
)

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

    Reads ``~/.agent-ready/credentials.env`` via the stdlib parser and
    looks up ``<NAMESPACE>_<KEY>``. Returns ``None`` on miss; a malformed
    dotfile also returns ``None`` (the upstream resolver raises
    ``CredentialsMissingError`` if the key was required, naming the
    namespace and the missing key list).
    """
    return _dotfile_read(namespace, key)


# ── Tier 3 — dotfile ───────────────────────────────────────────────────


def _dotfile_path() -> pathlib.Path:
    """Canonical Tier-3 dotfile path per spec § AC13.

    Resolves to ``pathlib.Path.home() / ".agent-ready" / "credentials.env"``
    on every platform. Tests redirect ``HOME`` (and ``USERPROFILE`` on
    Windows) to a ``tmp_path``-scoped directory so the developer's real
    ``~/.agent-ready/`` is never touched.
    """
    return pathlib.Path.home() / ".agent-ready" / "credentials.env"


def _dotfile_env_name(namespace: str, key: str) -> str:
    """Compose the dotfile entry name — same shape as the Tier-1 env var."""
    return f"{namespace.upper()}_{key}"


def _dotfile_read(namespace: str, key: str) -> str | None:
    """Look up ``<NAMESPACE>_<KEY>`` in the Tier-3 dotfile."""
    path = _dotfile_path()
    if not path.is_file():
        return None
    try:
        values = parse_env_file(path)
    except EnvParseError:
        return None
    raw = values.get(_dotfile_env_name(namespace, key))
    if not raw:
        return None
    return raw


def _quote_for_dotfile(value: str) -> str:
    """Render a value for the dotfile.

    Use double-quotes only when the bare value would be ambiguous to the
    parser (contains whitespace or a leading ``#``). Embedded double
    quotes / dollar signs are not the user's tokens in practice — the
    parser refuses ``$`` and embedded quotes would re-enter as ``"a"b"``
    which the parser strips clumsily. Tokens this rejects shouldn't be
    in scope for Tier-3 storage and the helper surfaces the parser
    error if a round-trip would corrupt the value.
    """
    if not value:
        return '""'
    if " " in value or value.startswith("#"):
        return f'"{value}"'
    return value


def _verify_icacls(
    path: pathlib.Path, *, allow_permissive_acl: bool = False
) -> None:
    """Run ``icacls`` on the path and refuse if any non-default ACE grants
    read access (spec § AC15). No-op on POSIX.

    Default ACEs on a per-user file are the inheriting user,
    ``NT AUTHORITY\\SYSTEM``, and ``BUILTIN\\Administrators``. Any other
    principal granted access is flagged unless the caller opts in.
    """
    if os.name != "nt":  # pragma: no cover — POSIX path
        return
    res = subprocess.run(  # pragma: no cover — exercised only on Windows
        ["icacls", str(path)], capture_output=True, text=True, check=False
    )
    if res.returncode != 0:
        raise PermissiveAclError(
            f"icacls inspection failed for {path}: rc={res.returncode} "
            f"stderr={res.stderr.strip()}"
        )
    suspect = []
    for line in res.stdout.splitlines():
        stripped = line.strip()
        # Flag any ACE granting access to non-default principals.
        if (
            "BUILTIN\\Users" in stripped
            or "Everyone" in stripped
            or "Authenticated Users" in stripped
        ):
            suspect.append(stripped)
    if suspect and not allow_permissive_acl:
        raise PermissiveAclError(
            f"DACL too permissive on {path}: {suspect}; pass "
            f"allow_permissive_acl=True to override"
        )


def _ensure_parent(parent: pathlib.Path) -> None:
    """Create the dotfile parent at mode 0o700 if absent (spec § AC15).

    If the parent already exists, do **not** rewrite its mode — the
    directory is shared with RFC-0004 install state. On POSIX warn on
    stderr if the existing mode is more permissive than 0o755.
    """
    if not parent.exists():
        parent.mkdir(mode=0o700, parents=True)
        return
    if os.name == "posix":
        mode = parent.stat().st_mode & 0o777
        if mode > 0o755:
            sys.stderr.write(
                f"warning: {parent} mode is {oct(mode)} (more permissive "
                f"than 0o755); leaving in place — shared with install state\n"
            )


def _dotfile_write(
    namespace: str,
    key: str,
    value: str,
    *,
    allow_permissive_acl: bool = False,
) -> None:
    """Write ``(namespace, key) → value`` to the Tier-3 dotfile atomically.

    Atomic write contract per spec § AC14:
    ``tempfile.mkstemp(dir=target_dir)`` → ``os.write`` →
    ``os.fchmod`` (POSIX) → ``os.close`` → ``os.replace``. A mid-write
    read sees either the prior contents or the new contents, never
    partial.
    """
    path = _dotfile_path()
    parent = path.parent
    _ensure_parent(parent)

    existing: dict[str, str] = {}
    if path.is_file():
        try:
            existing = parse_env_file(path)
        except EnvParseError:
            existing = {}
    existing[_dotfile_env_name(namespace, key)] = value
    content = "".join(
        f"{k}={_quote_for_dotfile(v)}\n" for k, v in existing.items()
    )

    fd, tmp_path_str = tempfile.mkstemp(dir=str(parent), prefix=".creds.")
    tmp_path = pathlib.Path(tmp_path_str)
    try:
        os.write(fd, content.encode("utf-8"))
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        os.close(fd)
        if os.name == "nt":
            _verify_icacls(tmp_path, allow_permissive_acl=allow_permissive_acl)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _dotfile_delete(namespace: str, key: str) -> None:
    """Remove ``(namespace, key)`` from the dotfile atomically.

    No-op if the dotfile is absent or the key isn't present. Atomic
    rewrite shape matches ``_dotfile_write``.
    """
    path = _dotfile_path()
    if not path.is_file():
        return
    try:
        existing = parse_env_file(path)
    except EnvParseError:
        return
    target = _dotfile_env_name(namespace, key)
    if target not in existing:
        return
    del existing[target]
    content = "".join(
        f"{k}={_quote_for_dotfile(v)}\n" for k, v in existing.items()
    )
    parent = path.parent
    fd, tmp_path_str = tempfile.mkstemp(dir=str(parent), prefix=".creds.")
    tmp_path = pathlib.Path(tmp_path_str)
    try:
        os.write(fd, content.encode("utf-8"))
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        os.close(fd)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _tier2_backend_label() -> str:
    """Human-readable label for the Tier-2 backend on this platform."""
    if sys.platform == "darwin":
        return "macOS Keychain"
    if sys.platform == "win32":
        return "Windows Credential Manager"
    return "(no Tier-2 backend on this platform)"


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
    resolve at any tier. The exception carries a ``tiers_tried``
    attribute mapping each missing key to an ordered list of trailer
    lines (which tier was checked and why it missed); the default
    ``str()`` form embeds those trailers under the key name so a
    user who ran ``creds setup`` can triage from the message alone.

    The ``schema_path`` kwarg is reserved for T7 — primitive authors who
    load their own schema can pass it here; the default ``None`` defers
    to the canonical lookup (T7 wires the canonical path resolver).
    """
    resolved: dict[str, str] = {}
    missing: list[str] = []
    tiers_tried: dict[str, list[str]] = {}
    dotfile_path = _dotfile_path()
    dotfile_present = dotfile_path.is_file()
    backend_label = _tier2_backend_label()
    for key in required_keys:
        attempts: list[str] = []
        env_name = f"{namespace.upper()}_{key}"

        # Tier 1 — env var.
        v = _tier1_env(namespace, key)
        if v:
            resolved[key] = v
            continue
        attempts.append(f"Tier 1: env {env_name!r} not set")

        # Tier 2 — OS keyring (when loaded). Tier2HardFailError
        # propagates per AC11 (no silent fallback to Tier 3 on hard
        # fail); only a clean miss falls through.
        if _tier2_backend is None:
            attempts.append("Tier 2: not loaded (no keyring backend on this platform)")
        else:
            v = _tier2_backend.read_credential(namespace, key)
            if v:
                resolved[key] = v
                continue
            attempts.append(f"Tier 2: {backend_label} — entry not present")

        # Tier 3 — dotfile.
        v = _tier3(namespace, key)
        if v:
            resolved[key] = v
            continue
        if dotfile_present:
            attempts.append(
                f"Tier 3: dotfile {dotfile_path} present but "
                f"{_dotfile_env_name(namespace, key)!r} not in it"
            )
        else:
            attempts.append(f"Tier 3: dotfile {dotfile_path} absent")

        missing.append(key)
        tiers_tried[key] = attempts

    if missing:
        # One-line preamble preserves the AC3 contract (message names
        # namespace and the missing-keys list); the per-key trailer
        # block comes below for triage.
        lines = [
            f"namespace {namespace!r}: missing required credential(s): "
            f"{', '.join(missing)}"
        ]
        for key in missing:
            lines.append(f"  {key}:")
            for trailer in tiers_tried[key]:
                lines.append(f"    {trailer}")
        raise CredentialsMissingError(
            "\n".join(lines),
            namespace=namespace,
            missing=missing,
            tiers_tried=tiers_tried,
        )
    return Credentials(namespace, resolved)


# ── creds-schema.toml parser (spec § AC24, AC24b) ─────────────────────


@dataclasses.dataclass(frozen=True, slots=True)
class KeyDef:
    """A single required key declared in ``creds-schema.toml``.

    ``secret=True`` keys are prompted via ``getpass.getpass`` (no echo);
    ``secret=False`` keys are prompted via ``input()`` per spec § AC24.
    """

    name: str
    label: str
    secret: bool


@dataclasses.dataclass(frozen=True, slots=True)
class CredsSchema:
    """A parsed ``creds-schema.toml`` for a single namespace."""

    namespace: str
    keys: tuple[KeyDef, ...]


def _parse_schema(path: pathlib.Path) -> CredsSchema:
    """Parse a ``creds-schema.toml`` file into a typed ``CredsSchema``.

    Per spec § AC24, the expected shape is::

        [namespace]
        name = "<namespace>"

        [[namespace.keys]]
        name = "API_TOKEN"
        label = "<service> API token"
        secret = true

    The parser raises ``SchemaError`` (naming the path) on missing
    ``[namespace]``, empty ``namespace.keys``, or non-boolean ``secret``.
    """
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    except FileNotFoundError as exc:
        raise SchemaError(f"creds-schema.toml not found: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise SchemaError(f"creds-schema.toml malformed ({path}): {exc}") from exc

    ns_table = data.get("namespace")
    if not isinstance(ns_table, dict):
        raise SchemaError(f"creds-schema.toml missing [namespace] ({path})")
    namespace = ns_table.get("name")
    if not isinstance(namespace, str) or not namespace:
        raise SchemaError(
            f"creds-schema.toml missing namespace.name ({path})"
        )
    raw_keys = ns_table.get("keys")
    if not isinstance(raw_keys, list) or not raw_keys:
        raise SchemaError(
            f"creds-schema.toml namespace.keys must declare at least one key ({path})"
        )
    keys: list[KeyDef] = []
    for idx, entry in enumerate(raw_keys):
        if not isinstance(entry, dict):
            raise SchemaError(
                f"creds-schema.toml namespace.keys[{idx}] is not a table ({path})"
            )
        name = entry.get("name")
        label = entry.get("label")
        secret = entry.get("secret")
        if not isinstance(name, str) or not name:
            raise SchemaError(
                f"creds-schema.toml namespace.keys[{idx}].name missing or non-string ({path})"
            )
        if not isinstance(label, str):
            raise SchemaError(
                f"creds-schema.toml namespace.keys[{idx}].label missing or non-string ({path})"
            )
        if not isinstance(secret, bool):
            raise SchemaError(
                f"creds-schema.toml namespace.keys[{idx}].secret must be boolean ({path})"
            )
        keys.append(KeyDef(name=name, label=label, secret=secret))
    return CredsSchema(namespace=namespace, keys=tuple(keys))


_SKILL_MD_RE = re.compile(r"^\.claude/skills/([^/]+)/SKILL\.md$")


def resolve_schema_path(
    state: "object", pack: str, skill_name: str
) -> pathlib.Path:
    """Resolve the canonical ``creds-schema.toml`` path per spec § AC24b.

    Walks ``state.packs[pack].files`` for a relpath matching
    ``^\\.claude/skills/<skill_name>/SKILL\\.md$``; takes that
    relpath's parent directory and joins ``references/creds-schema.toml``.
    Returns the absolute path resolved against the state file's
    container directory (caller is responsible for joining the right
    scope root if needed; this function returns the *relative-form
    rooted at* the path the state stored).

    Raises ``SchemaError`` if no matching SKILL.md row is in
    ``pack.files`` — names the offending pack and skill so the message
    is actionable.

    Uses the **existing** v0.3 state-file schema — no new fields are
    added.
    """
    packs = getattr(state, "packs", None)
    if not isinstance(packs, dict):
        raise SchemaError(
            f"state has no ``packs`` attribute or wrong type "
            f"(got {type(state).__name__})"
        )
    pack_state = packs.get(pack)
    if pack_state is None:
        raise SchemaError(
            f"pack {pack!r} not present in state.packs "
            f"(known: {sorted(packs)})"
        )
    files = getattr(pack_state, "files", None)
    if not isinstance(files, dict):
        raise SchemaError(
            f"state.packs[{pack!r}].files is missing or not a dict"
        )
    for relpath in files:
        m = _SKILL_MD_RE.match(relpath)
        if m and m.group(1) == skill_name:
            parent = pathlib.PurePosixPath(relpath).parent
            return pathlib.Path(str(parent / "references" / "creds-schema.toml"))
    raise SchemaError(
        f"creds-schema.toml not found at expected path: no "
        f"``.claude/skills/{skill_name}/SKILL.md`` row in pack "
        f"{pack!r}'s files table"
    )


__all__ = [
    "CredsSchema",
    "Credentials",
    "CredentialsMissingError",
    "EnvParseError",
    "KeyDef",
    "PermissiveAclError",
    "SchemaError",
    "Tier2HardFailError",
    "load_credentials",
    "parse_env_file",
    "resolve_schema_path",
]


class EnvParseError(ValueError):
    """Raised when an ``.env`` file violates the supported subset.

    Messages include the 1-based physical line number so a log reader
    can jump to the offending line.
    """


#: Upper bound on dotfile size. A credentials dotfile holds a few
#: dozen key=value lines; 1 MiB is six orders of magnitude over the
#: realistic ceiling. A larger file is either corruption or a
#: misplaced read against the wrong path — refuse rather than load
#: gigabytes into memory on every credential resolution.
DOTFILE_MAX_BYTES = 1 << 20  # 1 MiB


def parse_env_file(path: pathlib.Path) -> dict[str, str]:
    """Parse the file at ``path`` into a ``{KEY: value}`` mapping.

    Reads with ``newline=""`` so embedded ``\\r`` bytes are preserved;
    only the trailing line terminator is stripped.

    Refuses files larger than ``DOTFILE_MAX_BYTES`` (1 MiB) to bound
    the read against a misconfigured or malicious dotfile path.
    """
    try:
        size = path.stat().st_size
    except OSError:
        size = 0
    if size > DOTFILE_MAX_BYTES:
        raise EnvParseError(
            f"dotfile {path!s} is {size} bytes; refusing to read more than "
            f"{DOTFILE_MAX_BYTES} bytes — verify the path is the credentials "
            f"dotfile, not a misconfigured target."
        )
    # Use ``path.open(newline="")`` instead of ``read_text(newline=...)``
    # — the ``newline`` keyword on ``Path.read_text`` was added in Python
    # 3.13; the project targets 3.11+ via the CI matrix.
    with path.open(encoding="utf-8", newline="") as fh:
        text = fh.read()
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
