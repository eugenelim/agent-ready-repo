"""Canonical stdlib-only install-marker writer for the Claude-plugins and APM install routes.

This script is invoked by a ``SessionStart`` hook derived by ``agentbundle build``
into every pack's projected output:
  - ``dist/claude-plugins/<pack>/.claude-plugin/plugin.json``  — claude-plugins route
  - ``dist/apm/<pack>/.apm/hooks/install-marker.json``         — APM route

It detects first-install-or-update and writes a ``[[packs-installed]]`` entry
to the scope-correct ``.adapt-install-marker.toml`` file so the existing core
session-start nudge and ``/adapt-to-project`` skill can consume it.

Specs:
  docs/specs/claude-plugins-install-route/spec.md  (route = "claude-plugins")
  docs/specs/apm-install-route-parity/spec.md      (route = "apm"; --install-route flag)

CLI:
  ``--install-route {claude-plugins,apm}`` is *required*. The build pipeline bakes
  the value into the projected hook ``command`` at projection time for both routes;
  the writer does no runtime route-sniffing. ``"cli"`` is *not* a valid choice — the
  CLI route uses ``agentbundle install._append_install_marker`` directly and never
  invokes this template.

Environment variables consumed under ``--install-route claude-plugins``:
  CLAUDE_PLUGIN_ROOT   — path to the pack's root in the Claude-plugins cache.
  CLAUDE_PLUGIN_DATA   — path to the pack's per-session data directory (hash file lives here).
  HOME                 — user home directory (user-scope marker path).
  CLAUDE_PROJECT_DIR   — (optional) path to the current project directory; when absent,
                         local and project scope checks are skipped.

Environment variables consumed under ``--install-route apm`` (precedence-resolved):
  CLAUDE_PLUGIN_DATA   — APM's Claude Code target rewrites ``${PLUGIN_ROOT}`` to
                         ``${CLAUDE_PLUGIN_ROOT}`` *and* sets this; used directly when set.
  PLUGIN_ROOT          — APM's generic per-target token; ``${PLUGIN_ROOT}/.data`` for the
                         hash file when ``${CLAUDE_PLUGIN_DATA}`` is unset.
  CURSOR_PLUGIN_ROOT   — APM's Cursor target equivalent; ``${CURSOR_PLUGIN_ROOT}/.data``
                         when both above are unset.
  CLAUDE_PLUGIN_ROOT   — APM's Claude Code pack-root token (when set, used as pack root).
  HOME                 — user home directory (user-scope marker path; also used to
                         detect ``writer-under-$HOME`` scope).
  Scope detection under APM is by writer's own resolved ``__file__`` path containment
  under ``cwd`` (→ repo scope) or ``HOME`` (→ user scope), not by ``enabledPlugins``.

Exit codes:
  0 — success (marker written, or warm-cache skip, or refused-and-warned on scope mismatch),
      or argparse rejected the flag (the latter is exit 2 per argparse's defaults).
  1 — marker write failed (hash file NOT written; next session retries).
  2 — ``argparse`` parse error (missing or invalid ``--install-route``).
"""

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import tomllib
from datetime import timezone


# ---------------------------------------------------------------------------
# Vendored pack-name / pack-version shape rules — copied from
# agentbundle.commands.install._PACK_NAME_RE / _PACK_VERSION_RE.
# Source path: packages/agentbundle/agentbundle/commands/install.py
# Keep in sync with the source; the regexes are the CLI's canonical gate for
# pack-name shape and must match exactly (same pattern string, same flags).
# Security Concern 7: without this guard a pack with `name = "core\nevil"` in
# pack.toml would pass unchecked and land phantom TOML lines in the marker.
# ---------------------------------------------------------------------------
import re as _re

_PACK_NAME_RE = _re.compile(r"^[a-z0-9][a-z0-9-]*$")
_PACK_VERSION_RE = _re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$"
)

# ---------------------------------------------------------------------------
# Vendored helper — copied from agentbundle.config._emit_basic_string.
# Source path: packages/agentbundle/agentbundle/config.py
# Keep in sync with the source; any security fix there must be applied here too.
# The self-host drift gate (make build-check) asserts byte-identical output
# across the fixed attack corpus — do NOT silently alter this function.
# Note: the source raises ConfigError; here we raise ValueError (stdlib-only
# constraint means no ConfigError import). Behaviour is otherwise identical.
# ---------------------------------------------------------------------------

# Control characters that TOML 1.0 § Strings forbids unescaped inside a
# basic-string. Everything in U+0000..U+001F except `\t` (which has a
# short escape), plus U+007F. The `\uXXXX` long-form covers them all.
_TOML_SHORT_ESCAPES = {
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
    '"': '\\"',
    "\\": "\\\\",
}


def _emit_basic_string(value: str) -> str:
    """Serialise *value* as a TOML 1.0 basic-string literal (incl. quotes).

    Every write-path that interpolates a pack-sourced string into TOML output
    routes through here. The grammar matches what ``tomllib`` will accept:
    short escapes for ``\\b \\t \\n \\f \\r \\" \\\\``, ``\\uXXXX`` for any
    other control char (U+0000..U+001F and U+007F), and verbatim emission
    for everything else (including multi-byte UTF-8).

    Returns the *quoted* form ``"...escaped..."`` so callers write
    ``key = {_emit_basic_string(v)}`` without re-adding quotes.

    Raises ``ValueError`` if *value* is not a string.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"basic-string position expects str, got {type(value).__name__}"
        )
    chunks: list[str] = ['"']
    for ch in value:
        short = _TOML_SHORT_ESCAPES.get(ch)
        if short is not None:
            chunks.append(short)
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            chunks.append(f"\\u{ord(ch):04X}")
        else:
            chunks.append(ch)
    chunks.append('"')
    return "".join(chunks)


# ---------------------------------------------------------------------------
# Vendored path-jail helpers — copied from agentbundle.safety.
# Source path: packages/agentbundle/agentbundle/safety.py
# Keep in sync with the source; any security fix there must be applied here too.
# Vendored inline because this writer is stdlib-only (no agentbundle import).
# ---------------------------------------------------------------------------

# Windows reserves these device names regardless of extension.
_WINDOWS_RESERVED_NAMES = frozenset(
    ["CON", "PRN", "AUX", "NUL"]
    + [f"COM{i}" for i in range(1, 10)]
    + [f"LPT{i}" for i in range(1, 10)]
)

# Characters Windows refuses in filenames (backslash omitted — treated as separator).
_WINDOWS_FORBIDDEN_CHARS = frozenset('<>:"|?*')


def _assert_under(target: pathlib.Path, jail: pathlib.Path) -> None:
    """Refuse if ``target`` resolves outside ``jail``.

    ``jail`` is expected to be a pre-resolved path (from ``_marker_path``), so
    we only re-resolve the *target* here. This closes the TOCTOU window: the
    jail value is fixed at probe time and cannot be redirected by a symlink
    introduced between the probe and this check.

    Raises ``ValueError`` if ``os.path.realpath(target)`` is not under
    ``jail``. Uses ``relative_to`` on resolved paths to foil ``..``
    traversal and symlink escape.
    """
    resolved_target = pathlib.Path(os.path.realpath(target))
    # jail is already resolved; do not call os.path.realpath on it again.
    try:
        resolved_target.relative_to(jail)
    except ValueError:
        raise ValueError(
            f"install-marker: marker path {resolved_target} escapes the per-scope jail "
            f"{jail}; refusing write"
        )


def _assert_portable_name(component: str) -> None:
    """Refuse Windows-poisonous filename components.

    Checks three classes (all OSes — pack content travels to Windows adopters):
      1. Reserved device names (CON/PRN/AUX/NUL/COM1-9/LPT1-9), case-insensitive,
         matched on the pre-extension stem (Windows treats ``CON.txt`` as ``CON``).
      2. Names ending in ``.`` or `` `` (Windows strips both silently).
      3. Names containing ``< > : " | ? *`` (illegal in Windows filenames).
      4. Names containing control characters (U+0000..U+001F or U+007F).

    Raises ``ValueError`` with a one-line message naming the component.
    """
    if not component or component in (".", ".."):
        return
    for ch in component:
        if ch in _WINDOWS_FORBIDDEN_CHARS:
            raise ValueError(
                f"install-marker: refusing path component with forbidden character "
                f"{ch!r}: {component!r}"
            )
        if ord(ch) < 0x20 or ord(ch) == 0x7F:
            raise ValueError(
                f"install-marker: refusing path component with control character "
                f"U+{ord(ch):04X}: {component!r}"
            )
    if component.endswith(".") or component.endswith(" "):
        raise ValueError(
            f"install-marker: refusing path component with trailing dot or space: "
            f"{component!r}"
        )
    stem = component.split(".", 1)[0]
    if stem.upper() in _WINDOWS_RESERVED_NAMES:
        raise ValueError(
            f"install-marker: refusing Windows-reserved device name "
            f"{stem!r} in component {component!r}"
        )


# ---------------------------------------------------------------------------
# Scope detection helpers
# ---------------------------------------------------------------------------


def _detect_origin(
    *,
    plugin_name: str,
    home: pathlib.Path,
    project_dir: pathlib.Path | None,
) -> str | None:
    """Walk the three ``enabledPlugins`` settings files in precedence order.

    Returns the most-specific origin scope on opt-in: ``"local"``,
    ``"project"``, or ``"user"``. Returns ``None`` for fall-through
    (pack is not enabled at any scope).

    Precedence: local → project → user (most-specific wins).
    Missing file, malformed JSON, absent ``enabledPlugins`` key, or
    ``enabledPlugins`` present but not a JSON array are each treated as
    "not opted in at that scope" and fall through.
    """
    candidates: list[tuple[str, pathlib.Path]] = []

    if project_dir is not None:
        candidates.append(("local", project_dir / ".claude" / "settings.local.json"))
        candidates.append(("project", project_dir / ".claude" / "settings.json"))

    candidates.append(("user", home / ".claude" / "settings.json"))

    for origin, settings_path in candidates:
        if not settings_path.exists():
            continue
        try:
            read_text = settings_path.read_text(encoding="utf-8")
        except OSError:
            continue
        # Cap read size to 1 MiB to guard against DoS via giant file.
        if len(read_text) > 1_048_576:
            continue
        try:
            raw = json.loads(read_text)
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(raw, dict):
            continue
        enabled = raw.get("enabledPlugins")
        if not isinstance(enabled, list):
            continue
        # Check whether this pack is in the list; compare by name prefix
        # since installed plugins may appear as "name@marketplace-url".
        for entry in enabled:
            if not isinstance(entry, str):
                continue
            # Match by pack name as a prefix component (before '@').
            entry_name = entry.split("@")[0].strip()
            if entry_name == plugin_name:
                return origin

    return None


def _marker_scope(origin: str) -> str:
    """Collapse the three-valued origin to the two-valued marker scope.

    ``local`` and ``project`` → ``"repo"``
    ``user``                  → ``"user"``

    This collapse is the Blocker-1 rail: the ``allowed-scopes`` comparison
    and the marker-file location both use the two-valued scope; only the
    adopter-facing stderr messages use the three-valued origin.
    """
    if origin in ("local", "project"):
        return "repo"
    return "user"


# ---------------------------------------------------------------------------
# Pack manifest helpers
# ---------------------------------------------------------------------------


def _pack_toml(plugin_root: pathlib.Path) -> dict:
    """Load and return the pack manifest dict from ``pack.toml``."""
    toml_path = plugin_root / "pack.toml"
    with open(toml_path, "rb") as fh:
        return tomllib.load(fh)


def _manifest_hash(plugin_root: pathlib.Path) -> str:
    """Return the SHA-256 hex digest of ``${CLAUDE_PLUGIN_ROOT}/pack.toml``."""
    toml_path = plugin_root / "pack.toml"
    data = toml_path.read_bytes()
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Marker file helpers
# ---------------------------------------------------------------------------


def _marker_path(
    marker_scope: str,
    project_dir: pathlib.Path | None,
    home: pathlib.Path,
) -> "tuple[pathlib.Path, pathlib.Path]":
    """Return ``(marker_path, resolved_jail)`` for the given scope.

    ``repo`` → ``(<project_dir>/.adapt-install-marker.toml, resolved(project_dir))``
    ``user`` → ``(<home>/.agentbundle/.adapt-install-marker.toml, resolved(~/.agentbundle))``

    The returned ``resolved_jail`` is pre-resolved here so ``_write_marker``
    can use it directly without re-resolving, closing the TOCTOU window where
    a symlink introduced between probe and write would resolve both sides to
    the foreign target and pass the jail check trivially (Concern-3).
    """
    if marker_scope == "user":
        agentbundle = home / ".agentbundle"
        # Symlink / non-directory probe (mirrors safety.user_state_path):
        # mkdir with exist_ok=True, then check lstat. A pre-existing symlink
        # (even pointing at a real directory) is refused so an attacker cannot
        # redirect marker writes to an arbitrary location.
        if agentbundle.is_symlink():
            target = os.path.realpath(agentbundle)
            raise ValueError(
                f"install-marker: {agentbundle} is a symlink to {target}; refusing"
            )
        if agentbundle.exists() and not agentbundle.is_dir():
            raise ValueError(
                f"install-marker: {agentbundle} exists but is not a directory; refusing"
            )
        agentbundle.mkdir(mode=0o700, parents=True, exist_ok=True)
        resolved_jail = pathlib.Path(os.path.realpath(agentbundle))
        return agentbundle / ".adapt-install-marker.toml", resolved_jail
    else:
        # repo scope — project_dir must be set; callers ensure this.
        if project_dir is None:
            raise ValueError("project_dir required for repo-scope marker")
        resolved_jail = pathlib.Path(os.path.realpath(project_dir))
        return project_dir / ".adapt-install-marker.toml", resolved_jail


def _should_fire(
    marker_path: pathlib.Path,
    pack_name: str,
    plugin_data: pathlib.Path,
    current_hash: str,
) -> bool:
    """Implement the dual-detection condition.

    Returns ``True`` (fire the writer) when either:
      - The hash file at ``${CLAUDE_PLUGIN_DATA}/pack-manifest-hash`` is
        missing or differs from ``current_hash``; OR
      - The hash matches but the marker file has no ``[[packs-installed]]``
        entry naming this pack.

    Returns ``False`` (warm cache — skip) only when BOTH conditions hold:
      the hash matches AND the marker contains an entry for this pack.
    """
    hash_file = plugin_data / "pack-manifest-hash"

    # Condition 1: hash diff.
    if not hash_file.exists():
        return True
    stored_hash = hash_file.read_text(encoding="utf-8").strip()
    if stored_hash != current_hash:
        return True

    # Hash matches — check condition 2: marker entry absent.
    if not marker_path.exists():
        return True
    try:
        data = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        # Malformed marker — treat as absent entry; fire.
        return True
    entries = data.get("packs-installed", [])
    if not isinstance(entries, list):
        return True
    for entry in entries:
        if isinstance(entry, dict) and entry.get("name") == pack_name:
            return False  # warm cache: hash matches AND entry present

    return True  # hash matches but entry absent


# ---------------------------------------------------------------------------
# Marker write helpers
# ---------------------------------------------------------------------------


def _read_entries(marker_path: pathlib.Path) -> list[dict]:
    """Read existing ``[[packs-installed]]`` entries from the marker file.

    Drops any entry whose ``installed-at`` is not a ``datetime.datetime``
    (defence-in-depth: mirrors install.py:866-874).

    Coerces ``unresolved-markers`` and ``new-companions`` to ``list[str]``
    when they are present: non-list values or lists containing non-str items
    are dropped with a one-line stderr warning, and the rest of the entry
    survives (Concern-4).
    """
    if not marker_path.exists():
        return []
    try:
        data = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError) as exc:
        # Diagnostic aligned with the CLI writer at install.py:846-849.
        print(
            f"install-marker: warning: existing install marker at {marker_path} "
            f"is malformed ({exc}); prior entries lost — re-run install "
            f"for any earlier packs",
            file=sys.stderr,
        )
        return []
    raw_entries = data.get("packs-installed", [])
    if not isinstance(raw_entries, list):
        return []
    entries: list[dict] = []
    for e in raw_entries:
        if not isinstance(e, dict):
            continue
        ts = e.get("installed-at")
        if not isinstance(ts, datetime.datetime):
            # Drop entries with non-datetime installed-at (same defence as CLI).
            continue
        # Coerce unresolved-markers and new-companions to list[str].
        # A tampered marker could carry a non-list or list-with-non-str
        # value for these fields; passing the raw value to _emit_basic_string
        # would raise. Coerce here and warn so the entry's other valid
        # fields survive re-emission.
        # Security Concern 2: type-validate name, version, install-route.
        # A tampered marker with name=42 (TOML integer) passes the
        # installed-at filter but raises ValueError at _emit_basic_string
        # time, bricking subsequent marker writes. Drop such entries.
        _skip_entry = False
        for _field in ("name", "version"):
            _val = e.get(_field)
            if _val is not None and not isinstance(_val, str):
                _label = e.get("name") if _field != "name" else "<unnamed>"
                _label_str = _label if isinstance(_label, str) else "<unnamed>"
                print(
                    f"install-marker: warning: marker entry has non-string "
                    f"{_field} (got {type(_val).__name__}); dropping entry "
                    f"for pack {_label_str!r}",
                    file=sys.stderr,
                )
                _skip_entry = True
                break
        if not _skip_entry:
            _route_val = e.get("install-route")
            if _route_val is not None and not isinstance(_route_val, str):
                _name_val = e.get("name", "<unnamed>")
                _name_str = _name_val if isinstance(_name_val, str) else "<unnamed>"
                print(
                    f"install-marker: warning: marker entry for {_name_str!r} "
                    f"has non-string install-route "
                    f"(got {type(_route_val).__name__}); dropping field",
                    file=sys.stderr,
                )
                e = dict(e)  # shallow copy before mutation
                del e["install-route"]
        if _skip_entry:
            continue
        e = dict(e)  # shallow copy so we don't mutate the tomllib-parsed dict
        for field in ("unresolved-markers", "new-companions"):
            if field not in e:
                continue
            raw_val = e[field]
            if not isinstance(raw_val, list) or not all(
                isinstance(item, str) for item in raw_val
            ):
                pack = e.get("name", "<unknown>")
                actual_type = type(raw_val).__name__
                print(
                    f"install-marker: existing marker entry for {pack} has malformed "
                    f"{field} ({actual_type} instead of list[str]); dropping field",
                    file=sys.stderr,
                )
                del e[field]
        entries.append(e)
    return entries


def _serialise_marker(entries: list[dict]) -> str:
    """Serialise a list of ``[[packs-installed]]`` entries to TOML text.

    Mirrors the field-for-field emission in install.py:896-934:
      - ``marker-schema-version`` — basic string.
      - Per entry:
        - ``name`` — basic string (TOML-injection safe).
        - ``version`` — basic string.
        - ``installed-at`` — bare TOML offset-datetime literal (no quotes).
        - ``install-route`` — basic string.
        - ``unresolved-markers`` and ``new-companions`` — if present on the
          entry (CLI-seeded entries carry both; writer-created entries omit
          them). Pass-through verbatim so CLI-seeded entries survive re-emit.
    """
    lines: list[str] = [
        f"marker-schema-version = {_emit_basic_string('0.1')}",
        "",
    ]
    for entry in entries:
        lines.append("[[packs-installed]]")
        lines.append(f"name = {_emit_basic_string(entry['name'])}")
        lines.append(f"version = {_emit_basic_string(entry['version'])}")
        # Emit installed-at as a bare TOML offset-datetime literal (load-bearing).
        # The CLI loader at install.py:866-874 drops any entry whose installed-at
        # is not a datetime; emitting a basic-string would round-trip as str
        # and get dropped on the next CLI invocation (Blocker-3 rail).
        ts = entry["installed-at"]
        if isinstance(ts, datetime.datetime):
            ts_str = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            raise ValueError(
                f"installed-at must be datetime, got {type(ts).__name__}"
            )
        lines.append(f"installed-at = {ts_str}")
        # install-route: use the stored value; fall back to "cli" for entries
        # written by the CLI writer before this field existed (v0.3 markers).
        install_route = entry.get("install-route", "cli")
        lines.append(f"install-route = {_emit_basic_string(install_route)}")
        # Pass-through unresolved-markers and new-companions if present on the
        # entry. CLI-seeded entries carry both; writer-created entries omit them
        # (the writer has no visibility into the projected primitive tree —
        # per spec). Re-emit verbatim using _emit_basic_string so CLI-seeded
        # queue/companion lists survive a Claude-plugins writer pass.
        if "unresolved-markers" in entry:
            markers_repr = ", ".join(
                _emit_basic_string(m) for m in entry.get("unresolved-markers", [])
            )
            lines.append(f"unresolved-markers = [{markers_repr}]")
        if "new-companions" in entry:
            comps_repr = ", ".join(
                _emit_basic_string(c) for c in entry.get("new-companions", [])
            )
            lines.append(f"new-companions = [{comps_repr}]")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _write_marker(
    marker_path: pathlib.Path,
    new_entry: dict,
    jail: pathlib.Path,
) -> None:
    """Read-modify-write the marker file via atomic rename.

    Reads existing entries, replaces any existing entry for the same pack name
    (upgrade semantics — does not stack), appends the new entry if not
    replacing, then writes via ``tempfile.NamedTemporaryFile`` + ``os.replace``.

    The tempfile is created in the same directory as the marker file so
    ``os.replace`` is always on the same filesystem (the POSIX guarantee
    that makes it atomic).

    ``jail`` is the **pre-resolved** per-scope root (as returned by
    ``_marker_path``): the real path of ``~/.agentbundle`` for user scope,
    or the real path of ``project_dir`` for repo scope. Callers must pass
    the value that ``_marker_path`` returns without re-resolving — this closes
    the TOCTOU window where a symlink introduced between probe and write would
    otherwise redirect the output. The path-jail check runs before the write.
    """
    # Path-jail check: verify marker_path resolves inside jail.
    # jail is a pre-resolved path from _marker_path; _assert_under does not
    # re-resolve it so the probe-time trusted jail value is used throughout.
    _assert_under(marker_path, jail)
    # Portable-name check on filename components *under* the jail only.
    # The jail trusted-prefix (e.g. "/home/user/.agentbundle") is not
    # user-influenced and contains OS-specific separators (e.g. "C:\\")
    # on Windows that would falsely trigger the "forbidden character ':'"
    # guard. Only the components beneath the jail need validation.
    try:
        rel = marker_path.relative_to(jail)
    except ValueError:
        # marker_path is outside jail; _assert_under already raised,
        # but guard defensively in case the call order is rearranged.
        rel = marker_path
    for part in rel.parts:
        _assert_portable_name(part)

    existing = _read_entries(marker_path)
    # Replace any existing entry for the same pack name (AC8 upgrade semantics).
    entries = [e for e in existing if e.get("name") != new_entry["name"]]
    entries.append(new_entry)

    content = _serialise_marker(entries)
    content_bytes = content.encode("utf-8")

    marker_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a tempfile in the same directory, then os.replace for atomicity.
    tmp_fd, tmp_name = tempfile.mkstemp(dir=marker_path.parent, suffix=".tmp")
    try:
        os.write(tmp_fd, content_bytes)
        os.close(tmp_fd)
        tmp_fd = -1
        os.replace(tmp_name, marker_path)
    except Exception:
        # Clean up tempfile on error (best effort).
        if tmp_fd >= 0:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _write_hash(plugin_data: pathlib.Path, current_hash: str) -> None:
    """Write the hash file at ``${CLAUDE_PLUGIN_DATA}/pack-manifest-hash``.

    Only called from ``main`` AFTER ``_write_marker`` returns successfully
    (the write-after-success ordering is the spec's robustness rail — see
    Boundaries §Never do). Hash-write failure is non-fatal (main allows it
    to proceed with exit 0 + warning); the next session retries detection.

    Uses tempfile + os.replace for atomicity, matching the marker write rail.
    """
    plugin_data.mkdir(parents=True, exist_ok=True)
    hash_path = plugin_data / "pack-manifest-hash"
    content_bytes = (current_hash + "\n").encode("utf-8")
    # Atomic write — tempfile-in-parent + os.replace, matching the marker rail.
    tmp_fd, tmp_name = tempfile.mkstemp(dir=plugin_data, suffix=".tmp")
    try:
        os.write(tmp_fd, content_bytes)
        os.close(tmp_fd)
        tmp_fd = -1
        os.replace(tmp_name, hash_path)
    except Exception:
        if tmp_fd >= 0:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# APM-route helpers (apm-install-route-parity AC3 / AC4)
# ---------------------------------------------------------------------------


def _resolve_data_dir(env: "dict[str, str]") -> "pathlib.Path | None":
    """Resolve hash-file directory per the apm-install-route-parity AC3 precedence.

    Precedence (first set-and-non-empty wins):
      1. ``${CLAUDE_PLUGIN_DATA}``       — APM at Claude Code target.
      2. ``${PLUGIN_ROOT}/.data``        — APM's generic per-target token.
      3. ``${CURSOR_PLUGIN_ROOT}/.data`` — APM at Cursor target.

    Returns ``None`` when none of the three is set-and-non-empty; callers
    treat this as the no-match fall-through and exit 0 without writing the
    marker (the no-partial-state rail).

    Empty-string values are treated as unset (an APM target that exports
    ``PLUGIN_ROOT=""`` must not be silently picked over a later-precedence
    fallback that *is* set).
    """
    cpd = env.get("CLAUDE_PLUGIN_DATA", "")
    if cpd:
        return pathlib.Path(cpd)
    pr = env.get("PLUGIN_ROOT", "")
    if pr:
        return pathlib.Path(pr) / ".data"
    cpr = env.get("CURSOR_PLUGIN_ROOT", "")
    if cpr:
        return pathlib.Path(cpr) / ".data"
    return None


def _apm_detect_scope(
    writer_path: pathlib.Path,
    cwd: pathlib.Path,
    home: pathlib.Path,
) -> "str | None":
    """Detect APM-route marker scope by writer's resolved ``__file__`` containment.

    Returns:
      ``"repo"`` if ``writer_path.resolve()`` is contained under
        ``cwd.resolve()`` — first-branch-wins, even when ``cwd`` is itself
        nested under ``$HOME`` and the home branch would also succeed in the
        abstract (AC4 case (a)).
      ``"user"`` if (and only if) the repo branch fails and ``writer_path``
        is contained under ``home.resolve()``.
      ``None`` otherwise — no-match fall-through; the caller exits 0 without
        writing the marker (the no-partial-state rail).

    Symlinks are resolved on both sides via ``.resolve()`` before comparison
    so a writer that lives under a symlinked cache directory still passes
    the containment check (AC4 case (d)).
    """
    wp = writer_path.resolve()
    cwd_r = cwd.resolve()
    home_r = home.resolve()
    try:
        if wp.is_relative_to(cwd_r):
            return "repo"
    except ValueError:
        pass
    try:
        if wp.is_relative_to(home_r):
            return "user"
    except ValueError:
        pass
    return None


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------


def _parse_args(argv: "list[str]") -> argparse.Namespace:
    """Parse the writer's CLI surface.

    ``--install-route`` is two-valued (``claude-plugins`` | ``apm``) and
    ``required=True`` — argparse exits non-zero with a usage message on
    either missing flag or invalid choice. ``"cli"`` is *not* admitted; the
    CLI route uses ``agentbundle install._append_install_marker`` directly
    and never invokes this template.
    """
    parser = argparse.ArgumentParser(prog="install-marker")
    parser.add_argument(
        "--install-route",
        choices=["claude-plugins", "apm"],
        required=True,
        help=(
            "the install route that projected this writer; baked into the "
            "[[packs-installed]] entry verbatim. Required; no default."
        ),
    )
    return parser.parse_args(argv)


def main(argv: "list[str]") -> int:
    """Writer entrypoint.

    Parses ``--install-route``, dispatches to the route-appropriate scope-
    detection path, and writes the marker. Returns exit code.
    """
    args = _parse_args(argv)

    if args.install_route == "apm":
        return _main_apm(args)
    return _main_claude_plugins(args)


def _main_claude_plugins(args: argparse.Namespace) -> int:
    """Claude-plugins-route writer (behaviour-preserving past the argparse prefix).

    Reads ``${CLAUDE_PLUGIN_ROOT}`` and ``${CLAUDE_PLUGIN_DATA}`` from
    ``os.environ``; scope detection via ``_detect_origin`` (enabledPlugins walk).
    """
    # --- Environment ---
    plugin_root_str = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    plugin_data_str = os.environ.get("CLAUDE_PLUGIN_DATA", "")
    home_str = os.environ.get("HOME", "")
    project_dir_str = os.environ.get("CLAUDE_PROJECT_DIR", "")

    if not plugin_root_str:
        print("install-marker: CLAUDE_PLUGIN_ROOT is not set", file=sys.stderr)
        return 1
    if not plugin_data_str:
        print("install-marker: CLAUDE_PLUGIN_DATA is not set", file=sys.stderr)
        return 1
    if not home_str:
        print("install-marker: HOME is not set", file=sys.stderr)
        return 1

    plugin_root = pathlib.Path(plugin_root_str)
    plugin_data = pathlib.Path(plugin_data_str)
    home = pathlib.Path(home_str)
    project_dir: pathlib.Path | None = (
        pathlib.Path(project_dir_str) if project_dir_str else None
    )

    # --- Load pack manifest ---
    try:
        pack = _pack_toml(plugin_root)
    except Exception as exc:
        print(f"install-marker: failed to read pack.toml: {exc}", file=sys.stderr)
        return 1

    pack_meta = pack.get("pack", {})
    pack_name: str = pack_meta.get("name", "")
    pack_version: str = pack_meta.get("version", "")
    install_table = pack_meta.get("install", {})
    allowed_scopes: list = install_table.get("allowed-scopes", [])

    if not pack_name:
        print("install-marker: pack.toml is missing [pack].name", file=sys.stderr)
        return 1

    # Security Concern 7: validate pack name and version against the same
    # shape rules the CLI enforces (_PACK_NAME_RE / _PACK_VERSION_RE vendored
    # above from packages/agentbundle/agentbundle/commands/install.py).
    # A pack with control chars / newlines in name passes undetected otherwise,
    # enabling TOML injection in the marker file. Refuse-and-warn, exit 0 (no
    # marker write, no hash file update) so the next session retries.
    if not isinstance(pack_name, str) or not _PACK_NAME_RE.fullmatch(pack_name):
        print(
            f"install-marker: pack name {pack_name!r} fails pack-name shape rule "
            f"(must match ^[a-z0-9][a-z0-9-]*$); skipping marker write",
            file=sys.stderr,
        )
        return 0

    if pack_version and (
        not isinstance(pack_version, str)
        or not _PACK_VERSION_RE.fullmatch(pack_version)
    ):
        print(
            f"install-marker: pack version for {pack_name!r} fails pack-version "
            f"shape rule; skipping marker write",
            file=sys.stderr,
        )
        return 0

    # --- Compute hash ---
    try:
        current_hash = _manifest_hash(plugin_root)
    except Exception as exc:
        print(f"install-marker: failed to hash pack.toml: {exc}", file=sys.stderr)
        return 1

    # --- Scope detection (claude-plugins route: enabledPlugins walk) ---
    origin = _detect_origin(
        plugin_name=pack_name,
        home=home,
        project_dir=project_dir,
    )

    if origin is None:
        # No-match fall-through: exit 0 without writing the marker AND
        # without updating ${CLAUDE_PLUGIN_DATA} so the next session retries.
        return 0

    scope = _marker_scope(origin)

    # --- Allowed-scopes refusal rail ---
    if allowed_scopes and scope not in allowed_scopes:
        print(
            f"install-marker: pack {pack_name} declares allowed-scopes={allowed_scopes!r}, "
            f"detected install scope {origin}; skipping marker write",
            file=sys.stderr,
        )
        # Exit 0; do NOT update ${CLAUDE_PLUGIN_DATA} so next session re-checks.
        return 0

    # --- Derive marker path ---
    if scope == "repo" and project_dir is None:
        # Cannot write a repo-scope marker without a project directory.
        # This can happen if CLAUDE_PROJECT_DIR is unset but scope is repo
        # (should not occur given detection logic, but guard defensively).
        print(
            "install-marker: repo-scope marker requested but CLAUDE_PROJECT_DIR is unset",
            file=sys.stderr,
        )
        return 0

    try:
        marker, resolved_jail = _marker_path(scope, project_dir, home)
    except Exception as exc:
        print(f"install-marker: failed to resolve marker path: {exc}", file=sys.stderr)
        return 1

    # --- Dual-detection check ---
    if not _should_fire(marker, pack_name, plugin_data, current_hash):
        # Warm cache — exit cleanly, nothing to do.
        return 0

    # --- Build new entry ---
    new_entry: dict = {
        "name": pack_name,
        "version": pack_version,
        "installed-at": datetime.datetime.now(timezone.utc),
        "install-route": args.install_route,
    }

    # --- Write marker (must succeed before writing hash file) ---
    # resolved_jail is pre-resolved by _marker_path; passing it directly
    # to _write_marker closes the TOCTOU window (Concern-3).
    try:
        _write_marker(marker, new_entry, resolved_jail)
    except Exception as exc:
        print(f"install-marker: marker write failed: {exc}", file=sys.stderr)
        # Do NOT write hash file — next session retries the marker write.
        return 1

    # --- Write hash file only after marker write succeeds ---
    try:
        _write_hash(plugin_data, current_hash)
    except Exception as exc:
        # Hash write failure is non-fatal for the adopter (the marker was written),
        # but log it so the next session retries detection rather than silently skipping.
        print(f"install-marker: hash write failed (next session will retry): {exc}", file=sys.stderr)

    return 0


def _main_apm(args: argparse.Namespace) -> int:
    """APM-route writer (apm-install-route-parity AC2/3/4/5).

    Reads precedence-resolved data directory and pack root from the APM
    environment; scope detection by writer's own resolved ``__file__`` path
    containment under ``cwd`` (→ repo) or ``$HOME`` (→ user). The marker
    schema and the allowed-scopes refusal rail are unchanged from the
    claude-plugins route — only the *detection* mechanism differs.
    """
    # --- Environment ---
    env = os.environ
    home_str = env.get("HOME", "")
    if not home_str:
        print("install-marker: HOME is not set", file=sys.stderr)
        return 1
    home = pathlib.Path(home_str)

    # --- Resolve data directory per AC3 precedence ---
    plugin_data = _resolve_data_dir(env)
    if plugin_data is None:
        # No-match fall-through (no APM data-directory token set); exit 0
        # without writing marker or hash file (the no-partial-state rail).
        # Emit a one-line stderr so an APM target whose token names we got
        # wrong does not silently no-op forever — the writer's failure
        # mode appears in the target tool's hook log.
        print(
            "install-marker: no APM data-directory token set "
            "(looked for ${CLAUDE_PLUGIN_DATA}, ${PLUGIN_ROOT}, "
            "${CURSOR_PLUGIN_ROOT}); skipping marker write",
            file=sys.stderr,
        )
        return 0

    # --- Resolve pack root ---
    # Pack-root precedence mirrors the data-dir chain's structure
    # (Claude Code → generic → Cursor) but uses the pack-root token
    # at each tier (CLAUDE_PLUGIN_ROOT / PLUGIN_ROOT / CURSOR_PLUGIN_ROOT);
    # data-dir's first tier is CLAUDE_PLUGIN_DATA, not CLAUDE_PLUGIN_ROOT,
    # so the two token sets overlap but are not identical.
    cpr_pack = env.get("CLAUDE_PLUGIN_ROOT", "")
    pr_pack = env.get("PLUGIN_ROOT", "")
    cur_pack = env.get("CURSOR_PLUGIN_ROOT", "")
    if cpr_pack:
        plugin_root = pathlib.Path(cpr_pack)
    elif pr_pack:
        plugin_root = pathlib.Path(pr_pack)
    elif cur_pack:
        plugin_root = pathlib.Path(cur_pack)
    else:
        # Data dir resolved (per above) but no pack-root token set: same
        # no-partial-state rail — exit 0 without writing.
        print(
            "install-marker: no APM pack-root token set "
            "(looked for ${CLAUDE_PLUGIN_ROOT}, ${PLUGIN_ROOT}, "
            "${CURSOR_PLUGIN_ROOT}); skipping marker write",
            file=sys.stderr,
        )
        return 0

    # --- Load pack manifest ---
    try:
        pack = _pack_toml(plugin_root)
    except Exception as exc:
        print(f"install-marker: failed to read pack.toml: {exc}", file=sys.stderr)
        return 1

    pack_meta = pack.get("pack", {})
    pack_name: str = pack_meta.get("name", "")
    pack_version: str = pack_meta.get("version", "")
    install_table = pack_meta.get("install", {})
    allowed_scopes: list = install_table.get("allowed-scopes", [])

    if not pack_name:
        print("install-marker: pack.toml is missing [pack].name", file=sys.stderr)
        return 1

    # Vendored pack-name / pack-version shape rules — identical to the
    # claude-plugins branch above (security-load-bearing; do not skip).
    if not isinstance(pack_name, str) or not _PACK_NAME_RE.fullmatch(pack_name):
        print(
            f"install-marker: pack name {pack_name!r} fails pack-name shape rule "
            f"(must match ^[a-z0-9][a-z0-9-]*$); skipping marker write",
            file=sys.stderr,
        )
        return 0
    if pack_version and (
        not isinstance(pack_version, str)
        or not _PACK_VERSION_RE.fullmatch(pack_version)
    ):
        print(
            f"install-marker: pack version for {pack_name!r} fails pack-version "
            f"shape rule; skipping marker write",
            file=sys.stderr,
        )
        return 0

    # --- Compute hash ---
    try:
        current_hash = _manifest_hash(plugin_root)
    except Exception as exc:
        print(f"install-marker: failed to hash pack.toml: {exc}", file=sys.stderr)
        return 1

    # --- Scope detection (APM route: writer's projected-path containment) ---
    writer_path = pathlib.Path(__file__)
    cwd = pathlib.Path.cwd()
    scope = _apm_detect_scope(writer_path, cwd, home)
    if scope is None:
        # No-match fall-through: writer not contained under cwd or $HOME.
        # Emit a one-line stderr so the failure mode is visible — a writer
        # projected outside both roots is most often a target-tool packaging
        # bug (cache directory under a non-standard mount point).
        print(
            f"install-marker: writer at {writer_path} not under cwd "
            f"({cwd}) or $HOME ({home}); skipping marker write",
            file=sys.stderr,
        )
        return 0

    # --- Allowed-scopes refusal rail (unchanged grammar from claude-plugins) ---
    if allowed_scopes and scope not in allowed_scopes:
        print(
            f"install-marker: pack {pack_name} declares allowed-scopes={allowed_scopes!r}, "
            f"detected install scope {scope}; skipping marker write",
            file=sys.stderr,
        )
        return 0

    # --- Derive marker path ---
    # For APM repo scope, cwd plays the role project_dir plays in the
    # claude-plugins route — the marker lands under it directly.
    project_dir_for_marker = cwd if scope == "repo" else None
    try:
        marker, resolved_jail = _marker_path(scope, project_dir_for_marker, home)
    except Exception as exc:
        print(f"install-marker: failed to resolve marker path: {exc}", file=sys.stderr)
        return 1

    # --- Ensure data directory exists ---
    # APM does not pre-create the per-pack .data/ subdirectory; mkdir before
    # the hash file write rail attempts to open it.
    try:
        plugin_data.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        print(f"install-marker: failed to create data directory: {exc}", file=sys.stderr)
        return 1

    # --- Dual-detection check ---
    if not _should_fire(marker, pack_name, plugin_data, current_hash):
        return 0

    # --- Build new entry ---
    new_entry: dict = {
        "name": pack_name,
        "version": pack_version,
        "installed-at": datetime.datetime.now(timezone.utc),
        "install-route": args.install_route,
    }

    # --- Write marker (must succeed before writing hash file) ---
    try:
        _write_marker(marker, new_entry, resolved_jail)
    except Exception as exc:
        print(f"install-marker: marker write failed: {exc}", file=sys.stderr)
        return 1

    # --- Write hash file only after marker write succeeds ---
    try:
        _write_hash(plugin_data, current_hash)
    except Exception as exc:
        print(
            f"install-marker: hash write failed (next session will retry): {exc}",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
