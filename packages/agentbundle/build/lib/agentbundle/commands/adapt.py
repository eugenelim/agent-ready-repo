"""``agentbundle adapt`` — marker resolution and pending-companion report.

RFC-0004 turned this into a **dual-state-file** walk:

  - Read both ``<repo>/.agent-ready-state.toml`` and
    ``~/.agent-ready/state.toml``. Either may be absent (a fresh repo,
    or no user-scope installs yet).
  - Read marker values from both ``<repo>/.adapt-discovery.toml`` and
    ``~/.agent-ready/.adapt-discovery.toml`` (user-scope discovery
    lives inside the namespaced dot-directory, not as a bare dotfile).
    ``--values-from`` still wins as an explicit override.
  - Walk for ``.upstream.<ext>`` companions per scope; write per-scope
    ``.adapt-pending.md`` reports at the same per-scope locations.
  - ``adapt --ci`` exits non-zero when *either* scope's pending file
    would be non-empty (or any companion is on disk).

Findings are routed by the scope of the state file that recorded them —
a squatter under ``~/.claude/`` is a user-scope finding, a
``.upstream.<ext>`` companion in ``<repo>/`` is a repo-scope finding.

Spec rail: ``.adapt-discovery.toml`` is **never written** here. The
``adapt-to-project`` LLM skill owns the write side.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

# Marker regex (AC14): canonical lowercase-hyphen identifiers. The CLI
# narrows from the prior UPPER_SNAKE-only regex to the canonical form
# that the adapt-to-project skill writes. UPPER_SNAKE markers still
# appearing in adopter trees are left in place with a one-shot warning
# (``_LEGACY_UPPER_RE``); they're not substituted.
_MARKER_RE = re.compile(r"<adapt:([a-z][a-z0-9-]*)>")
_LEGACY_UPPER_RE = re.compile(r"<adapt:([A-Z_][A-Z0-9_]*)>")


@dataclass
class _Scope:
    """Per-scope artifact paths the adapt verb operates on."""

    name: str
    root: Path
    state_path: Path
    discovery_path: Path
    pending_path: Path
    # User-scope writes must pass the adapter's `allowed-prefixes.user`
    # list through to `safety.write_jailed` so the path-jail rail
    # fires. Repo-scope leaves this as None (the repo-jail is the
    # repo root; no additional prefix gate).
    allowed_prefixes: list[str] | None = None


def _find_upstream_companions(root: Path, projected_paths: set[str] | None = None) -> list[Path]:
    """Return ``.upstream.<ext>`` companions of paths recorded in state.

    When *projected_paths* is provided, only companions that sit next to
    a path in the install's projection count — this prevents a stray
    ``vendor/upstream.tar.gz`` or documentation artifact from making
    ``adapt --ci`` exit non-zero. When *projected_paths* is ``None``
    (e.g. no state file present), fall back to the tree walk so the
    command still does something useful.
    """
    from agentbundle.safety import companion_path

    companions: list[Path] = []
    if projected_paths is not None:
        for relpath in sorted(projected_paths):
            comp = root / companion_path(Path(relpath))
            if comp.is_file():
                companions.append(comp)
        return companions

    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        name = p.name
        parts = name.split(".")
        if len(parts) >= 2 and "upstream" in parts:
            idx = parts.index("upstream")
            if idx > 0:
                companions.append(p)
    return companions


def _diff_summary(original: Path, companion: Path) -> str:
    """Return a one-line diff summary: line-count delta and first divergent line."""
    try:
        orig_lines = original.read_text(encoding="utf-8", errors="replace").splitlines()
        comp_lines = companion.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return "binary or unreadable"

    delta = len(comp_lines) - len(orig_lines)
    sign = "+" if delta >= 0 else ""
    first_diff_line: str | None = None
    for i, (ol, cl) in enumerate(zip(orig_lines, comp_lines)):
        if ol != cl:
            first_diff_line = f"line {i + 1}: original={ol[:60]!r} upstream={cl[:60]!r}"
            break
    if first_diff_line is None and len(orig_lines) != len(comp_lines):
        first_diff_line = f"line {min(len(orig_lines), len(comp_lines)) + 1}: (line count differs)"

    parts = [f"lines {sign}{delta}"]
    if first_diff_line:
        parts.append(first_diff_line)
    return "; ".join(parts)


def _apply_markers(text: str, values: dict[str, str], *, src_label: str) -> str:
    """Replace ``<adapt:NAME>`` in *text* using *values*.

    Unknown markers are left in place; a warning is printed to stderr.
    Legacy UPPER_SNAKE markers (per AC14) are left in place with a single
    warning per file.
    """
    if _LEGACY_UPPER_RE.search(text):
        print(
            f"adapt: warning: legacy UPPER_SNAKE marker(s) in {src_label}; "
            f"left in place (canonical form is <adapt:[a-z][a-z0-9-]*>)",
            file=sys.stderr,
        )

    def _replace(m: re.Match) -> str:
        name = m.group(1)
        if name in values:
            return values[name]
        print(
            f"adapt: warning: no value for marker <adapt:{name}> in {src_label}; leaving in place",
            file=sys.stderr,
        )
        return m.group(0)

    return _MARKER_RE.sub(_replace, text)


def _resolve_scopes(args: "argparse.Namespace") -> list[_Scope]:
    """Return the per-scope artifact descriptions adapt walks.

    The repo scope is always present (rooted at ``args.root``). The
    user scope is only added if ``~`` can be resolved — when
    ``$HOME=/`` or otherwise unresolvable, the user scope is silently
    skipped (a repo-only fixture should not refuse on a malformed
    user-scope environment).
    """
    from agentbundle import scope as scope_mod

    repo_root = Path(args.root).resolve()
    scopes: list[_Scope] = [
        _Scope(
            name="repo",
            root=repo_root,
            state_path=repo_root / ".agent-ready-state.toml",
            discovery_path=repo_root / ".adapt-discovery.toml",
            pending_path=repo_root / ".adapt-pending.md",
        ),
    ]
    try:
        user_root = scope_mod.resolve_user_root()
    except scope_mod.UserScopeUnresolvable:
        return scopes
    # User-scope dot-directory: `<user_root>/.agent-ready/`. We don't
    # *create* it here; we only operate on it if it already exists
    # (i.e. some prior user-scope install set it up).
    user_dir = user_root / ".agent-ready"
    if user_dir.is_dir():
        from agentbundle.commands.install import _claude_code_allowed_prefixes_user

        scopes.append(
            _Scope(
                name="user",
                root=user_root,
                state_path=user_dir / "state.toml",
                discovery_path=user_dir / ".adapt-discovery.toml",
                pending_path=user_dir / ".adapt-pending.md",
                allowed_prefixes=_claude_code_allowed_prefixes_user(),
            )
        )
    return scopes


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle adapt``.

    Returns 0 on success; 1 on ``--ci`` with pending companions or
    path-jail refusal at write time.
    """
    from agentbundle.config import ConfigError, load_adapt_discovery_typed, load_state, load_values_from
    from agentbundle import safety

    scopes = _resolve_scopes(args)

    # ── --ci mode ─────────────────────────────────────────────────────────────
    if args.ci:
        any_pending = False
        for s in scopes:
            try:
                state = load_state(s.state_path) if s.state_path.exists() else None
            except ConfigError as exc:
                print(f"adapt: {exc}", file=sys.stderr)
                return 1
            projected = state.projected_paths() if state else None
            companions = _find_upstream_companions(s.root, projected)
            if companions:
                if not any_pending:
                    print(
                        "adapt --ci: pending .upstream.* companions found:",
                        file=sys.stderr,
                    )
                    any_pending = True
                for cp in companions:
                    try:
                        rel = cp.relative_to(s.root)
                    except ValueError:
                        rel = cp
                    print(f"  [{s.name}] {rel}", file=sys.stderr)
        return 1 if any_pending else 0

    # ── Default mode ──────────────────────────────────────────────────────────
    # Build marker values from the **repo-scope** discovery file's
    # [markers] table. Markers are repo-only per RFC-0004 — the user-
    # scope discovery file is still read (to surface legacy-shape errors
    # symmetrically and to honour the dual-scope walk contract) but
    # carries no [markers] table by rail. --values-from (when supplied)
    # wins as the explicit override.
    values: dict[str, str] = {}
    for s in scopes:
        try:
            discovery = load_adapt_discovery_typed(s.discovery_path, scope=s.name)  # type: ignore[arg-type]
        except ConfigError as exc:
            print(f"adapt: {exc}", file=sys.stderr)
            return 1
        if s.name == "repo":
            for k, v in discovery.markers.items():
                values[k] = v

    if getattr(args, "values_from", None):
        try:
            explicit = load_values_from(Path(args.values_from))
        except ConfigError as exc:
            print(f"adapt: {exc}", file=sys.stderr)
            return 1
        values.update(explicit)

    # ── Per-scope walk: substitute markers + emit pending report ─────────────
    for s in scopes:
        try:
            state = load_state(s.state_path) if s.state_path.exists() else None
        except ConfigError as exc:
            print(f"adapt: {exc}", file=sys.stderr)
            return 1
        projected = state.projected_paths() if state else set()

        # Substitute markers only when --values-from was given (preserve
        # the read-only-without-values-from contract).
        if getattr(args, "values_from", None) and values and projected:
            for relpath in sorted(projected):
                target = s.root / relpath
                if not target.exists() or not target.is_file():
                    continue
                try:
                    text = target.read_bytes().decode("utf-8")
                except (UnicodeDecodeError, ValueError):
                    print(f"adapt: skipping binary file: [{s.name}] {relpath}", file=sys.stderr)
                    continue
                substituted = _apply_markers(text, values, src_label=f"[{s.name}] {relpath}")
                if substituted != text:
                    try:
                        safety.write_jailed(
                            s.root, relpath, substituted,
                            scope=s.name,
                            allowed_prefixes=s.allowed_prefixes,
                        )
                    except safety.PathJailError as exc:
                        print(f"adapt: {exc}", file=sys.stderr)
                        return 1

        # Build the per-scope pending report.
        companions = _find_upstream_companions(s.root, projected)
        report_lines: list[str] = [
            f"# Adapt Pending Report ({s.name} scope)",
            "",
            "Companions awaiting human merge:",
            "",
        ]
        if companions:
            for cp in sorted(companions):
                try:
                    rel_companion = cp.relative_to(s.root)
                except ValueError:
                    rel_companion = cp
                original = _original_from_companion(cp)
                if original.exists():
                    summary = _diff_summary(original, cp)
                else:
                    summary = "original file not found"
                report_lines.append(f"- `{rel_companion}`: {summary}")
        else:
            report_lines.append("_No pending companions._")
        report_lines.append("")
        report_content = "\n".join(report_lines)

        # Write the pending report through the per-scope path-jail. At
        # user scope this routes through `allowed-prefixes.user` —
        # `.adapt-pending.md` lives at `.agent-ready/.adapt-pending.md`
        # under the user root, which the `.agent-ready/` prefix admits.
        report_relpath = s.pending_path.relative_to(s.root).as_posix()
        try:
            safety.write_jailed(
                s.root, report_relpath, report_content,
                scope=s.name,
                allowed_prefixes=s.allowed_prefixes,
            )
        except safety.PathJailError as exc:
            print(f"adapt: {exc}", file=sys.stderr)
            return 1

    return 0


def _original_from_companion(companion: Path) -> Path:
    """Derive the original file path from a companion path.

    Inverse of ``safety.companion_path``:
      - ``AGENTS.upstream.md``  → ``AGENTS.md``
      - ``Makefile.upstream``   → ``Makefile``
      - ``foo.upstream.md``     → ``foo.md``
    """
    name = companion.name
    parts = name.split(".")
    if "upstream" in parts:
        idx = parts.index("upstream")
        new_parts = parts[:idx] + parts[idx + 1:]
        new_name = ".".join(new_parts)
        return companion.parent / new_name
    return companion
