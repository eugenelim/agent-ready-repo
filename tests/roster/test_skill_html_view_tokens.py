"""The skill HTML view's stylesheets agree with the design token file.

The token file sits under `docs/design/`, above the pack, so a pack test may
not read it. The pack-local half (every `var()` resolves to a property
`view-base.css` declares) stays in the pack suite.
"""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_TOKEN_FILE = _ROOT / "docs" / "design" / "tokens" / "skill-html-views.md"
_ASSETS = _ROOT / "packs" / "core" / ".apm" / "skills" / "navigate-intents" / "scripts" / "view_assets"
_BASE_CSS = (_ASSETS / "view-base.css").read_text(encoding="utf-8")
_DARK = "@media (prefers-color-scheme: dark)"
_Decl = tuple[tuple[str, ...], str, str, str]  # (at-rule chain, selector, property, value)


def _squash(text: str) -> str:
    """Collapse every run of whitespace to one space."""
    return re.sub(r"\s+", " ", text).strip()


def _walk_css(css: str) -> list[_Decl]:
    """Walk braces and return each declaration with its enclosing at-rule chain."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    stack: list[str] = []
    decls: list[_Decl] = []
    buf: list[str] = []
    quote = ""
    paren = 0

    def flush() -> None:
        text = _squash("".join(buf))
        buf.clear()
        if ":" in text:
            prop, value = text.split(":", 1)
            chain = tuple(b for b in stack if b.startswith("@"))
            selector = next((b for b in reversed(stack) if not b.startswith("@")), "")
            decls.append((chain, selector, prop.strip().lower(), value.strip()))

    for ch in css:
        if quote:
            buf.append(ch)
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            buf.append(ch)
            quote = ch
        elif ch == "(":
            paren += 1
            buf.append(ch)
        elif ch == ")":
            paren -= 1
            buf.append(ch)
        elif ch == "{" and paren == 0:
            stack.append(_squash("".join(buf)))
            buf.clear()
        elif ch == "}" and paren == 0:
            flush()
            stack.pop()
        elif ch == ";" and paren == 0:
            flush()
        else:
            buf.append(ch)
    return decls


def _token_tables() -> dict[str, dict[str, tuple[str, str]]]:
    """Read each Role, Light, Dark row of the token file's Colour, Radius and Elevation tables."""
    tables: dict[str, dict[str, tuple[str, str]]] = {}
    section = ""
    for line in _TOKEN_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if section in ("Colour", "Radius", "Elevation") and len(cells) >= 3 and re.fullmatch(r"`--[\w-]+`", cells[0]):
            tables.setdefault(section, {})[cells[0].strip("`")] = (cells[1].strip("`"), cells[2].strip("`"))
    return tables


def _root_values(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return the custom properties on :root, and those inside the dark-scheme block."""
    light: dict[str, str] = {}
    dark: dict[str, str] = {}
    for chain, selector, prop, value in _walk_css(css):
        if selector == ":root" and prop.startswith("--"):
            if chain == ():
                light[prop] = _squash(value)
            elif chain == (_DARK,):
                dark[prop] = _squash(value)
    return light, dark


def _token_misses(css: str, tables: dict[str, dict[str, tuple[str, str]]]) -> list[str]:
    light, dark = _root_values(css)
    misses = []
    for section, roles in tables.items():
        for role, (want_light, want_dark) in roles.items():
            if light.get(role) != _squash(want_light):
                misses.append(f"{section} {role}: light {light.get(role)!r} != {want_light!r}")
            if want_dark and dark.get(role) != _squash(want_dark):
                misses.append(f"{section} {role}: dark {dark.get(role)!r} != {want_dark!r}")
    return misses


def test_base_declares_token_tables() -> None:
    """Every Colour, Radius and Elevation role of the token file is declared on :root and in the dark block."""
    tables = _token_tables()
    assert {k: len(v) for k, v in tables.items()} == {"Colour": 20, "Radius": 3, "Elevation": 2}
    assert _token_misses(_BASE_CSS, tables) == []
    # The check can fail: a sheet that drops a role or its dark value is reported.
    assert _token_misses(":root { --c-bg: #ffffff; }", {"Colour": {"--c-bg": ("#ffffff", "#16181d")}})
    assert _token_misses(":root { --c-bg: #fffffe; }", {"Colour": {"--c-bg": ("#ffffff", "")}})


def test_token_file_names_every_property_the_base_sheet_declares() -> None:
    """Every property view-base.css declares is named in the token file."""
    light, dark = _root_values(_BASE_CSS)
    declared = set(light) | set(dark)
    assert declared
    token_text = _TOKEN_FILE.read_text(encoding="utf-8")
    undocumented = sorted(n for n in declared if not re.search(re.escape(n) + r"(?![\w-])", token_text))
    assert undocumented == [], undocumented


_MARKS = ("active", "approved", "draft", "done", "broken", "stale")


def _mark_colours(css: str, colour: dict[str, str]) -> dict[str, str]:
    """Resolve each state mark's background through a role table."""
    resolved = {}
    for _chain, selector, prop, value in _walk_css(css):
        for sel in selector.split(","):
            found = re.fullmatch(r'\.mark\[data-mark="(\w+)"\]', sel.strip())
            if found and prop == "background":
                role = re.fullmatch(r"var\((--[\w-]+)\)", value)
                assert role, (selector, value)
                resolved[found.group(1)] = colour[role.group(1)]
    return resolved


def test_state_mark_backgrounds_differ() -> None:
    """The six state marks each declare a background, and the six resolve to six different colours per theme."""
    colours = _token_tables()["Colour"]
    for index, theme in enumerate(("light", "dark")):
        resolved = _mark_colours(_BASE_CSS, {role: pair[index] for role, pair in colours.items()})
        assert sorted(resolved) == sorted(_MARKS), theme
        assert len(set(resolved.values())) == len(_MARKS), (theme, resolved)
    # The check can fail: two marks that resolve to one colour are caught.
    same = _mark_colours(
        '.mark[data-mark="done"] { background: var(--c-a); } .mark[data-mark="draft"] { background: var(--c-b); }',
        {"--c-a": "#eee", "--c-b": "#eee"},
    )
    assert len(set(same.values())) < len(same)
