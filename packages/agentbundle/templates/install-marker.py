"""Canonical stdlib-only install-marker writer for the Claude-plugins install route.

This script is invoked by the ``SessionStart`` hook derived by ``agentbundle build``
into every pack's ``.claude-plugin/plugin.json``. It detects first-install-or-update
and writes a ``[[packs-installed]]`` entry to the scope-correct
``.adapt-install-marker.toml`` file so the existing core session-start nudge and
``/adapt-to-project`` skill can consume it.

Spec: docs/specs/claude-plugins-install-route/spec.md

Environment variables consumed (all required unless noted):
  CLAUDE_PLUGIN_ROOT   — path to the pack's root in the Claude-plugins cache.
  CLAUDE_PLUGIN_DATA   — path to the pack's per-session data directory (hash file lives here).
  HOME                 — user home directory (user-scope marker path).
  CLAUDE_PROJECT_DIR   — (optional) path to the current project directory; when absent,
                         local and project scope checks are skipped.

Exit codes:
  0 — success (marker written, or warm-cache skip, or refused-and-warned on scope mismatch).
  1 — marker write failed (hash file NOT written; next session retries).
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
# Vendored helper — copied from agentbundle.config._emit_basic_string.
# Source path: packages/agentbundle/agentbundle/config.py
# Keep in sync with the source; any security fix there must be applied here too.
# The self-host drift gate (make build-check) asserts byte-identical output
# across the fixed attack corpus — do NOT silently alter this function.
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
            raw = json.loads(settings_path.read_text(encoding="utf-8"))
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
) -> pathlib.Path:
    """Return the scope-correct marker file path.

    ``repo`` → ``<project_dir>/.adapt-install-marker.toml``
    ``user`` → ``<home>/.agent-ready/.adapt-install-marker.toml``
    """
    if marker_scope == "user":
        agent_ready = home / ".agent-ready"
        agent_ready.mkdir(mode=0o700, parents=True, exist_ok=True)
        return agent_ready / ".adapt-install-marker.toml"
    else:
        # repo scope — project_dir must be set; callers ensure this.
        assert project_dir is not None, "project_dir required for repo-scope marker"
        return project_dir / ".adapt-install-marker.toml"


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
    except Exception:
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
    """
    if not marker_path.exists():
        return []
    try:
        data = tomllib.loads(marker_path.read_text(encoding="utf-8"))
    except Exception:
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
        - ``install-route`` — basic string fixed literal ``"claude-plugins"``.
        - ``unresolved-markers`` and ``new-companions`` are OMITTED (v0.4
          relaxes them to optional; the writer has no visibility into the
          projected primitive tree).
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
            ts_str = str(ts)
        lines.append(f"installed-at = {ts_str}")
        # install-route: use the stored value; fall back to "cli" for entries
        # written by the CLI writer before this field existed (v0.3 markers).
        install_route = entry.get("install-route", "cli")
        lines.append(f"install-route = {_emit_basic_string(install_route)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _write_marker(marker_path: pathlib.Path, new_entry: dict) -> None:
    """Read-modify-write the marker file via atomic rename.

    Reads existing entries, replaces any existing entry for the same pack name
    (upgrade semantics — does not stack), appends the new entry if not
    replacing, then writes via ``tempfile.NamedTemporaryFile`` + ``os.replace``.

    The tempfile is created in the same directory as the marker file so
    ``os.replace`` is always on the same filesystem (the POSIX guarantee
    that makes it atomic).
    """
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
    Boundaries §Never do).
    """
    plugin_data.mkdir(parents=True, exist_ok=True)
    hash_path = plugin_data / "pack-manifest-hash"
    hash_path.write_text(current_hash + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Main entrypoint
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    """Writer entrypoint. Reads ``${CLAUDE_PLUGIN_ROOT}`` and
    ``${CLAUDE_PLUGIN_DATA}`` from ``os.environ``. Returns exit code.
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

    # --- Compute hash ---
    try:
        current_hash = _manifest_hash(plugin_root)
    except Exception as exc:
        print(f"install-marker: failed to hash pack.toml: {exc}", file=sys.stderr)
        return 1

    # --- Scope detection ---
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
        marker = _marker_path(scope, project_dir, home)
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
        "install-route": "claude-plugins",
    }

    # --- Write marker (must succeed before writing hash file) ---
    try:
        _write_marker(marker, new_entry)
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
