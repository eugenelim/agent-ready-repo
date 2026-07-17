#!/usr/bin/env python3
"""Session-start hook: prints knowledge-base entries from
docs/knowledge/patterns.jsonl as a context block, then nudges the
adapter when there are pending packs to adapt.

Pure-stdlib Python port of session-start.sh. Native-Windows-parity
companion of the bash version: same env vars, same arguments, same
exit codes, same stdout/stderr shape.

Optional argument: --scope <path-or-glob>
  When set, only entries whose stored `scope` glob *covers* the
  given path are printed (e.g. --scope packages/auth/server.ts
  returns entries scoped to packages/auth/**, packages/**, and the
  repo-wide *). Without --scope, every entry is printed.

Output goes to stdout; missing or empty knowledge file produces no
output and exits 0. Malformed lines are skipped with a one-line
warning to stderr (so the rot is visible) and do not abort the hook.
Wiring lives in each tool's hook surface (Claude Code:
.claude/settings.json; see tools/hooks/README.md).

Fixture mode:
  KNOWLEDGE_FILE=<path>     read a different knowledge file
  ADAPT_REPO_MARKER=<path>  override repo-scope marker (default: repo_root/.adapt-install-marker.toml)
  ADAPT_USER_MARKER=<path>  override user-scope marker (default: ~/.agentbundle/.adapt-install-marker.toml)
"""

from __future__ import annotations

import fnmatch
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

USAGE = """\
Session-start hook: prints knowledge entries as a context block.

Usage:
  session-start.py [--scope <path-or-glob>]
  session-start.py --help

Optional argument: --scope <path-or-glob>
  When set, only entries whose stored `scope` glob *covers* the
  given path are printed (e.g. --scope packages/auth/server.ts
  returns entries scoped to packages/auth/**, packages/**, and the
  repo-wide *). Without --scope, every entry is printed.

Output goes to stdout; missing or empty knowledge file produces no
output and exits 0. Malformed lines are skipped with a one-line
warning to stderr.

Environment:
  KNOWLEDGE_FILE     override the knowledge-base path
  ADAPT_REPO_MARKER  override repo-scope adapt marker
  ADAPT_USER_MARKER  override user-scope adapt marker
"""


def _repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except FileNotFoundError:
        pass
    return Path.cwd()


def _safe_override_path(raw: str, base: Path) -> Path | None:
    """Resolve an operator-supplied path override and confine it to ``base``.

    Returns the resolved ``Path`` when it stays inside ``base`` — the natural
    scope for that override (the repo root for repo-scoped files, the home
    directory for the user-scoped marker) — and ``None`` otherwise, so the
    caller falls back to its trusted default.

    Env vars are operator config, but an auto-running session hook must not let
    a stray or hostile value steer it at an arbitrary file: not just directory
    traversal (``../../etc/passwd``, CWE-22) but any *absolute* path to a
    secret (``/etc/passwd``, ``~/.ssh/id_rsa``) or a symlink that escapes after
    resolution — all of which are CWE-73 "external control of file name". The
    containment check runs *after* ``resolve()``, so symlink targets are
    validated at their real location, not their lexical form. Shipping the
    barrier here means no adopter repo inherits the unsanitised env → path flow.
    """
    raw = raw.strip()
    if not raw:
        return None
    try:
        resolved = Path(raw).expanduser().resolve()
        base_resolved = base.resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if not resolved.is_relative_to(base_resolved):
        sys.stderr.write(
            f"session-start: ignoring out-of-bounds path override {raw!r} "
            f"(must resolve within {base_resolved})\n"
        )
        return None
    return resolved


def _parse_args(argv: list[str]) -> str:
    """Return the scope filter (empty string if absent). Mirrors the
    bash arg loop: --scope requires a value, --help/-h prints USAGE
    and exits 0, anything else exits 2."""
    scope_filter = ""
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--scope":
            i += 1
            if i >= len(argv) or argv[i].startswith("-"):
                print(
                    "session-start: --scope requires a path or glob value",
                    file=sys.stderr,
                )
                sys.exit(2)
            scope_filter = argv[i]
        elif arg in ("--help", "-h"):
            print(USAGE)
            sys.exit(0)
        else:
            print(f"session-start: unknown argument {arg}", file=sys.stderr)
            sys.exit(2)
        i += 1
    return scope_filter


def _emit_knowledge(path: Path, scope_filter: str) -> None:
    """Read JSONL knowledge file and emit the `=== knowledge ===` block.

    Malformed lines are skipped with a single stderr warning. Empty
    files (no entries after parsing + scope filter) emit no stdout.
    """
    entries = []
    malformed = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if scope_filter:
            # Caller passed a path or narrower glob; only emit entries
            # whose stored scope *covers* it. fnmatch is greedy across
            # `/`, so `packages/auth/**` matches `packages/auth/server.ts`.
            scope = entry.get("scope", "")
            if not fnmatch.fnmatch(scope_filter, scope):
                continue
        entries.append(entry)

    if malformed:
        print(
            f"session-start: skipped {malformed} malformed line(s) in "
            f"docs/knowledge/patterns.jsonl — each line must be a JSON object "
            f"(see docs/knowledge/README.md)",
            file=sys.stderr,
        )

    if not entries:
        return

    print("=== knowledge ===")
    for e in entries:
        print(
            f"[{e.get('id', '?')}] ({e.get('kind', '?')}, {e.get('scope', '?')}) "
            f"{e.get('title', '')}"
        )
        body = e.get("body", "").strip()
        if body:
            for ln in body.splitlines():
                print(f"    {ln}")
        source = e.get("source", "")
        if source:
            print(f"    — {source}")
        print()


def _pack_names_from_marker(path: Path) -> list[str]:
    """Return `[pack.name for pack in packs-installed]` from the TOML
    marker at *path*. Empty list on any failure (missing file, parse
    error, wrong shape) — silent fallback matches bash."""
    if not path.exists():
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        # Bash version silently returned empty. Python adds a one-line
        # stderr warning so a corrupted marker is visible to the
        # operator — defence in depth, doesn't change exit code.
        print(
            f"session-start: skipped malformed marker {path} ({type(exc).__name__})",
            file=sys.stderr,
        )
        return []
    entries = data.get("packs-installed", [])
    if not isinstance(entries, list):
        return []
    out = []
    for entry in entries:
        if isinstance(entry, dict):
            name = entry.get("name")
            if isinstance(name, str):
                out.append(name)
    return out


def _emit_adapt_nudge(repo_marker: Path, user_marker: Path) -> None:
    repo_names = _pack_names_from_marker(repo_marker)
    user_names = _pack_names_from_marker(user_marker)
    all_names = sorted(set(repo_names) | set(user_names))
    if not all_names:
        return
    scopes_with_entries = sum(bool(n) for n in (repo_names, user_names))
    joined = ", ".join(all_names)
    print(
        f"=== adapt-to-project: {len(all_names)} pack(s) pending adaptation "
        f"across {scopes_with_entries} scope(s): {joined} — run /adapt-to-project ==="
    )


def main(argv: list[str]) -> int:
    scope_filter = _parse_args(argv[1:])
    repo_root = _repo_root()

    home = Path.home()
    knowledge_file = _safe_override_path(
        os.environ.get("KNOWLEDGE_FILE", ""), repo_root
    ) or (repo_root / "docs" / "knowledge" / "patterns.jsonl")
    if knowledge_file.is_file() and knowledge_file.stat().st_size > 0:
        _emit_knowledge(knowledge_file, scope_filter)

    repo_marker = _safe_override_path(
        os.environ.get("ADAPT_REPO_MARKER", ""), repo_root
    ) or (repo_root / ".adapt-install-marker.toml")
    user_marker = _safe_override_path(
        os.environ.get("ADAPT_USER_MARKER", ""), home
    ) or (home / ".agentbundle" / ".adapt-install-marker.toml")
    _emit_adapt_nudge(repo_marker, user_marker)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
