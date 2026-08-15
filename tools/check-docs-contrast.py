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
        raise ValueError(f"var() chain too deep resolving {name}")
    value = table[name]
    m = VAR_RE.fullmatch(value)
    return resolve(m.group(1), table, depth + 1) if m else value


def _linearize(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def ratio(fg: str, bg: str) -> float:
    hi, lo = sorted((luminance(fg), luminance(bg)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def main() -> int:
    css = CSS_PATH.read_text(encoding="utf-8")
    tables = theme_tables(css)
    failures = 0
    for theme, table in tables.items():
        for fg_name, bg_name in PAIRS:
            fg, bg = resolve(fg_name, table), resolve(bg_name, table)
            if not (fg.startswith("#") and bg.startswith("#")):
                print(f"error  {theme}: {fg_name}/{bg_name} not plain hex ({fg!r}, {bg!r})")
                failures += 1
                continue
            r = ratio(fg, bg)
            status = "ok  " if r >= FLOOR else "FAIL"
            if r < FLOOR:
                failures += 1
            print(f"{status}  {theme:5} {fg_name} on {bg_name}: {r:.2f}")
    if failures:
        print(f"\ncheck-docs-contrast: {failures} pair(s) below {FLOOR}:1")
        return 1
    print("\ncheck-docs-contrast: all pairs pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
