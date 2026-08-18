#!/usr/bin/env python3
"""Check WCAG 2.x contrast for the docs-site palette.

Reads docs-site/src/styles/starlight.css, resolves the --doc-* and
--ds-state-* custom properties per theme (declarations inside a
[data-theme='light'] block override the dark defaults), and fails if any
text/ground pair used by the docs-site-design-refresh spec (AC5/AC6)
measures below 4.5:1. Pure stdlib; run from the repo root:

    python3 tools/check-docs-contrast.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

CSS_PATH = Path("docs-site/src/styles/starlight.css")

# (foreground var, background var) — every pair is real text on a real
# ground; decorative fills (tints, rules, borders) are deliberately absent.
PAIRS = [
    ("--doc-heading", "--doc-ground"),
    ("--doc-text", "--doc-ground"),
    ("--doc-text-muted", "--doc-ground"),
    ("--doc-text-faint", "--doc-ground"),
    ("--doc-accent-strong", "--doc-ground"),
    ("--doc-accent-strong", "--doc-surface"),
    # Inline code — neutral text on the neutral surface (it is deliberately not
    # accent-tinted; see the inline-code rule in starlight.css).
    ("--doc-text", "--doc-surface"),
    # The page deck rendered by the PageTitle override.
    ("--sl-color-gray-3", "--doc-ground"),
    ("--doc-code-text", "--doc-code-ground"),
    ("--ds-state-success-fg", "--ds-state-success-bg"),
    ("--ds-state-danger-fg", "--ds-state-danger-bg"),
    ("--ds-state-warn-fg", "--ds-state-warn-bg"),
    ("--ds-state-info-fg", "--ds-state-info-bg"),
    ("--ds-state-neutral-fg", "--ds-state-neutral-bg"),
]

FLOOR = 4.5
DECL_RE = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")
VAR_RE = re.compile(r"var\((--[a-z0-9-]+)\)")
# Exactly six hex digits. Three-digit shorthand (`#abc`) is legal CSS but NOT
# accepted here: `int("ab", 16)` would parse it happily and return a
# plausible-but-wrong luminance, and a silently wrong contrast number is worse
# than a refusal.
HEX6_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class ColourError(ValueError):
    """A palette value this checker refuses to interpret.

    Raised instead of letting `int(..., 16)` or a `KeyError` escape, so a
    malformed palette produces a diagnostic and a non-zero exit rather than a
    traceback — the difference between a gate that reports and one that crashes.
    """


def split_blocks(css: str) -> list[tuple[str, str]]:
    """Return (selector, body) for every top-level block."""
    blocks, i = [], 0
    while True:
        brace = css.find("{", i)
        if brace == -1:
            return blocks
        selector = css[i:brace]
        depth, j = 1, brace + 1
        while depth and j < len(css):
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        blocks.append((selector.strip(), css[brace + 1 : j - 1]))
        i = j


def theme_tables(css: str) -> dict[str, dict[str, str]]:
    dark: dict[str, str] = {}
    light: dict[str, str] = {}
    for selector, body in split_blocks(css):
        target = light if "data-theme='light'" in selector else dark
        for name, value in DECL_RE.findall(body):
            target[name] = value.strip()
    return {"dark": dark, "light": {**dark, **light}}


def resolve(name: str, table: dict[str, str], depth: int = 0) -> str:
    if depth > 10:
        raise ColourError(f"var() chain too deep resolving {name} (cycle?)")
    try:
        value = table[name]
    except KeyError:
        raise ColourError(f"{name} is not defined in this theme") from None
    m = VAR_RE.fullmatch(value)
    return resolve(m.group(1), table, depth + 1) if m else value


def _linearize(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    if not HEX6_RE.match(hex_color.strip()):
        raise ColourError(
            f"{hex_color!r} is not a six-digit hex colour "
            "(three-digit shorthand is not supported)"
        )
    h = hex_color.strip().lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def passes(r: float) -> bool:
    """Whether a measured ratio clears the floor.

    Extracted so the boundary is testable: WCAG's threshold is inclusive, and a
    test asserting that against `FLOOR` alone is a tautology that stays green if
    this comparison is flipped to `>`.
    """
    return r >= FLOOR


def ratio(fg: str, bg: str) -> float:
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def main() -> int:
    try:
        css = CSS_PATH.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # A missing or unreadable sheet is a gate failure, not a crash: this runs as
        # a required CI step, and a traceback there reads as tooling breakage rather
        # than the contract violation it is.
        print(f"error  cannot read or decode {CSS_PATH}: {exc}")
        print("\ncheck-docs-contrast: palette unreadable")
        return 1
    tables = theme_tables(css)
    failures = 0
    for theme, table in tables.items():
        for fg_name, bg_name in PAIRS:
            try:
                fg, bg = resolve(fg_name, table), resolve(bg_name, table)
            except ColourError as exc:
                print(f"error  {theme}: {fg_name}/{bg_name} — {exc}")
                failures += 1
                continue
            if not (fg.startswith("#") and bg.startswith("#")):
                print(f"error  {theme}: {fg_name}/{bg_name} not plain hex ({fg!r}, {bg!r})")
                failures += 1
                continue
            try:
                r = ratio(fg, bg)
            except ColourError as exc:
                print(f"error  {theme}: {fg_name}/{bg_name} — {exc}")
                failures += 1
                continue
            ok = passes(r)
            status = "ok  " if ok else "FAIL"
            if not ok:
                failures += 1
            print(f"{status}  {theme:5} {fg_name} on {bg_name}: {r:.2f}")
    if failures:
        print(f"\ncheck-docs-contrast: {failures} pair(s) failed — "
              f"below {FLOOR}:1, or a value this checker refuses to interpret")
        return 1
    print("\ncheck-docs-contrast: all pairs pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
