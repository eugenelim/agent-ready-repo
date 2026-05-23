"""``agentbundle adapt`` — marker resolution and pending-companion report.

Two modes:

  **Default (``--values-from`` optional):**
  1. Load values from ``--values-from <file.toml>`` (if supplied) via
     ``config.load_values_from``.
  2. Merge with ``.adapt-discovery.toml`` accepted entries from
     ``config.load_adapt_discovery`` (CLI never writes this file).
  3. Walk every file recorded in ``.agent-ready-state.toml``; substitute
     ``<adapt:NAME>`` markers with the merged dict.  Skip binary files
     (decode error → warning + skip). Leave unresolved markers in place
     and warn to stderr.
  4. Write substituted content via ``safety.write_jailed`` (atomic).
  5. Walk for ``.upstream.*`` companions and produce ``.adapt-pending.md``
     listing each with a one-line diff summary.
  6. ``.adapt-pending.md`` is written via ``safety.write_jailed``.

  Without ``--values-from``, steps 3–4 are skipped (read-only walk; only
  the pending report is emitted).

  **``--ci`` mode (read-only):**
  Walk ``args.root`` for any ``*.upstream.*`` (or ``*.upstream``)
  companion file.  If any are found, list them on stderr and exit 1.
  If none, exit 0.

Spec rail: ``.adapt-discovery.toml`` is **never written** here.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

# Marker regex: <adapt:UPPER_CASE_IDENTIFIER>
_MARKER_RE = re.compile(r"<adapt:([A-Z_][A-Z0-9_]*)>")


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
    """
    def _replace(m: re.Match) -> str:
        name = m.group(1)
        if name in values:
            return values[name]
        print(
            f"adapt: warning: no value for marker <adapt:{name}> in {src_label}; leaving in place",
            file=sys.stderr,
        )
        return m.group(0)  # leave unchanged

    return _MARKER_RE.sub(_replace, text)


def run(args: "argparse.Namespace") -> int:
    """Entry point for ``agentbundle adapt``.

    Args:
        args.values_from  — optional path to a ``--values-from`` TOML file.
        args.ci           — bool; ``--ci`` gate mode.
        args.root         — repo root directory (default ``'.'``).

    Returns 0 on success; 1 on ``--ci`` with pending companions or path-jail
    refusal.
    """
    from agentbundle.config import (
        ConfigError,
        load_adapt_discovery,
        load_state,
        load_values_from,
    )
    from agentbundle import safety

    root = Path(args.root).resolve()
    state_path = root / ".agent-ready-state.toml"
    discovery_path = root / ".adapt-discovery.toml"

    # Load state up-front so both --ci and default modes can scope the
    # companion walk to projected paths only (Concern 11).
    try:
        _state_for_ci = load_state(state_path) if state_path.exists() else None
    except ConfigError as exc:
        print(f"adapt: {exc}", file=sys.stderr)
        return 1
    _projected_for_ci = _state_for_ci.projected_paths() if _state_for_ci else None

    # ── --ci mode ─────────────────────────────────────────────────────────────
    if args.ci:
        companions = _find_upstream_companions(root, _projected_for_ci)
        if companions:
            print("adapt --ci: pending .upstream.* companions found:", file=sys.stderr)
            for cp in companions:
                try:
                    rel = cp.relative_to(root)
                except ValueError:
                    rel = cp
                print(f"  {rel}", file=sys.stderr)
            return 1
        return 0

    # ── Default mode ──────────────────────────────────────────────────────────

    # Load state: walk projected paths for marker substitution.
    try:
        state = load_state(state_path)
    except ConfigError as exc:
        print(f"adapt: {exc}", file=sys.stderr)
        return 1

    # Merge values: --values-from (higher priority) merged with discovery accepted.
    values: dict[str, str] = {}

    # Layer 1: .adapt-discovery.toml accepted entries (lower priority).
    try:
        discovery = load_adapt_discovery(discovery_path)
    except ConfigError as exc:
        print(f"adapt: {exc}", file=sys.stderr)
        return 1

    accepted = discovery.get("accepted", {})
    if isinstance(accepted, dict):
        for k, v in accepted.items():
            if isinstance(v, str):
                values[str(k)] = v

    # Layer 2: --values-from (higher priority; overrides discovery).
    if getattr(args, "values_from", None):
        try:
            explicit = load_values_from(Path(args.values_from))
        except ConfigError as exc:
            print(f"adapt: {exc}", file=sys.stderr)
            return 1
        values.update(explicit)

    # ── Marker substitution (only when --values-from supplied) ────────────────
    if getattr(args, "values_from", None) and values:
        projected = state.projected_paths()
        for relpath in sorted(projected):
            target = root / relpath
            if not target.exists() or not target.is_file():
                continue
            try:
                text = target.read_bytes().decode("utf-8")
            except (UnicodeDecodeError, ValueError):
                print(f"adapt: skipping binary file: {relpath}", file=sys.stderr)
                continue
            substituted = _apply_markers(text, values, src_label=relpath)
            if substituted != text:
                try:
                    safety.write_jailed(root, relpath, substituted)
                except safety.PathJailError as exc:
                    print(f"adapt: {exc}", file=sys.stderr)
                    return 1

    # ── Build .adapt-pending.md ───────────────────────────────────────────────
    companions = _find_upstream_companions(root, state.projected_paths())
    report_lines: list[str] = [
        "# Adapt Pending Report",
        "",
        "Companions awaiting human merge:",
        "",
    ]
    if companions:
        for cp in sorted(companions):
            try:
                rel_companion = cp.relative_to(root)
            except ValueError:
                rel_companion = cp

            # Derive the original path: AGENTS.upstream.md → AGENTS.md
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

    try:
        safety.write_jailed(root, ".adapt-pending.md", report_content)
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
    # Find "upstream" in parts and remove it.
    if "upstream" in parts:
        idx = parts.index("upstream")
        new_parts = parts[:idx] + parts[idx + 1:]
        new_name = ".".join(new_parts)
        return companion.parent / new_name
    return companion
