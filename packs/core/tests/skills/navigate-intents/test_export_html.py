"""Static contract tests for the offline view's HTML, script, and stylesheet.

These read the generated file and the two assets without a browser: the
content-security policy and its digests, the element and attribute bans, the
data-block escaping over a hostile corpus, the forbidden script tokens, the
escape parity with the text output (through ``node``), and the absence of motion
in the stylesheet.  Exports are written under ``tmp_path``.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from typing import Any

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"
_ASSETS = _SCRIPTS / "view_assets"
_FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
_REPO = pathlib.Path(__file__).resolve().parents[5]
_TOKENS = _REPO / "docs" / "design" / "tokens" / "skill-html-views.md"
_BASE_CSS = (_ASSETS / "view-base.css").read_text(encoding="utf-8")
_LAYOUT_CSS = (_ASSETS / "view.css").read_text(encoding="utf-8")
_STYLE_TEXT = _BASE_CSS + "\n" + _LAYOUT_CSS


def _load(path: pathlib.Path, module_name: str) -> Any:
    """Load a navigate-intents script by path under a pack-and-skill-unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_export_html_nav")

_DATA_BLOCK = re.compile(
    r'<script type="application/json" id="intent-data">(.*?)</script>', re.DOTALL
)


def _export(corpus: pathlib.Path, out: pathlib.Path) -> str:
    out.mkdir(parents=True, exist_ok=True)
    result, code = nav.run_export(corpus, str(out), "view.html", None)
    assert code == 0, result
    return pathlib.Path(result["path"]).read_text(encoding="utf-8")


class _Shape(HTMLParser):
    """Record the element tree facts the static checks need."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.tags: list[tuple[str, dict[str, str | None]]] = []
        self.head_children: list[tuple[str, dict[str, str | None]]] = []
        self.texts: dict[str, list[str]] = {"script": [], "style": []}
        self._stack: list[str] = []
        self._current: str | None = None
        self.executable = 0
        self.style_elements = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        mapping = dict(attrs)
        self.tags.append((tag, mapping))
        if self._stack and self._stack[-1] == "head":
            self.head_children.append((tag, mapping))
        if tag == "head":
            self._stack.append("head")
        if tag == "script" and mapping.get("type") != "application/json":
            self.executable += 1
        if tag == "style":
            self.style_elements += 1
        if tag in ("script", "style"):
            self._current = tag
            self.texts[tag].append("")

    def handle_endtag(self, tag: str) -> None:
        if tag == "head" and self._stack:
            self._stack.pop()
        if tag in ("script", "style"):
            self._current = None

    def handle_data(self, data: str) -> None:
        if self._current:
            self.texts[self._current][-1] += data


def _parse(html: str) -> _Shape:
    shape = _Shape()
    shape.feed(html)
    shape.close()
    return shape


def _digest(content: str) -> str:
    return base64.b64encode(hashlib.sha256(content.encode("utf-8")).digest()).decode("ascii")


@pytest.fixture(scope="module")
def mixed_html(tmp_path_factory: pytest.TempPathFactory) -> str:
    return _export(_FIXTURES / "mixed", tmp_path_factory.mktemp("mixed"))


@pytest.fixture(scope="module")
def hostile_html(tmp_path_factory: pytest.TempPathFactory) -> str:
    return _export(_FIXTURES / "hostile", tmp_path_factory.mktemp("hostile"))


def test_csp_is_first_head_child_and_pins_both_digests(mixed_html: str) -> None:
    shape = _parse(mixed_html)
    tag, attrs = shape.head_children[0]
    assert tag == "meta" and attrs["http-equiv"] == "Content-Security-Policy"
    (script,) = [t for t in shape.texts["script"] if t.strip() and "function" in t]
    (style,) = shape.texts["style"]
    assert attrs["content"] == (
        f"default-src 'none'; script-src 'sha256-{_digest(script)}'; "
        f"style-src 'sha256-{_digest(style)}'; img-src 'none'; base-uri 'none'; "
        "form-action 'none'"
    )
    assert shape.executable == 1 and shape.style_elements == 1
    assert script == (_ASSETS / "view.js").read_text(encoding="utf-8")
    assert style == _STYLE_TEXT


def test_page_has_no_banned_elements_attributes_or_urls(mixed_html: str) -> None:
    shape = _parse(mixed_html)
    names = {t for t, _ in shape.tags}
    assert not names & {"link", "img", "iframe", "object", "embed", "base"}
    assert all("style" not in attrs for _, attrs in shape.tags)
    assert not any(name.startswith("on") for _, attrs in shape.tags for name in attrs)
    (style,) = shape.texts["style"]
    assert "url(" not in style and "@import" not in style


def test_hostile_strings_stay_inside_the_data_block(hostile_html: str) -> None:
    block = _DATA_BLOCK.search(hostile_html)
    assert block is not None
    outside = hostile_html.replace(block.group(1), "")
    for needle in (
        "</script><script>",
        "<img src=x",
        "onerror",
        "javascript:",
        '"><svg',
        "alert(1)",
        "\u2028",
        "\u2029",
        "\u202e",
        "\u200f",
    ):
        assert needle not in outside, needle
    raw = block.group(1)
    for char in "<>&\u2028\u2029":
        assert char not in raw
    payload = json.loads(raw)
    assert payload["schema"] == "intent-navigation.view.v1"
    root = _FIXTURES / "hostile"
    summary, code = nav.run_query(root, ["query", "--operation", "summary"])
    assert code == 0 and payload["summary"] == summary["summary"]
    assert list(payload["records"]) == sorted(payload["records"])
    for node_id, record in payload["records"].items():
        got, code = nav.run_query(root, ["query", "--operation", "record", "--id", node_id])
        assert code == 0 and record == got["record"]
    assert "</script><script>alert(1)</script>" in json.dumps(payload["records"])


def _strip_comments(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    return re.sub(r"(?m)^\s*//.*$", "", source)


def test_script_holds_no_forbidden_api() -> None:
    code = _strip_comments((_ASSETS / "view.js").read_text(encoding="utf-8"))
    for token in (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "Function(",
        "srcdoc",
        "javascript:",
    ):
        assert token not in code, token
    assert not re.search(r"set(Timeout|Interval)\(\s*['\"`]", code)
    # No inline style writes: a property write, a cssText write, or a style attribute.
    assert not re.search(r"\.style\b", code)
    assert "cssText" not in code
    assert not re.search(r"setAttribute\(\s*['\"]style['\"]", code)
    for char in code:
        assert not (ord(char) > 0x7E or (ord(char) < 0x20 and char not in "\n\t")), hex(ord(char))


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_escape_function_matches_the_text_output() -> None:
    unsafe = sorted(nav._UNSAFE_CHARS)
    near = sorted(
        {chr(c + d) for c in map(ord, unsafe) for d in (-1, 1) if 0 <= c + d < 0x110000}
        - set(unsafe)
    )
    probes = (
        [chr(c) for c in map(ord, unsafe)]
        + near
        + [
            "plain text",
            "",
            "a\u202eb\u200fc",
            "tab\there",
            "line\nfeed",
            "emoji \U0001f600",
            "mix\u00ad\ufeff\U000e0001end",
        ]
    )
    script = (
        "const m = require(process.argv[1]);"
        "const probes = JSON.parse(process.argv[2]);"
        "process.stdout.write(JSON.stringify(probes.map(m.escapeDisplay)));"
    )
    done = subprocess.run(
        ["node", "-e", script, str(_ASSETS / "view.js"), json.dumps(probes)],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
    )
    assert json.loads(done.stdout) == [nav._escape_display(p) for p in probes]


def test_stylesheets_declare_no_motion_or_external_loads() -> None:
    """Neither stylesheet may animate, load a url, or import another sheet."""
    for css in (_BASE_CSS, _LAYOUT_CSS):
        for word in ("transition", "animation", "@keyframes", "url(", "@import"):
            assert word not in css


def test_base_stylesheet_carries_every_colour_token() -> None:
    """Each documented role's light value is on :root and its dark value in the dark query."""
    rows = re.findall(
        r"^\| `(--c-[a-z-]+)` \| `(#[0-9a-f]{6})` \| `(#[0-9a-f]{6})` \|",
        _TOKENS.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert len(rows) >= 9
    marker = "@media (prefers-color-scheme: dark)"
    light_part, dark_part = _BASE_CSS.split(marker, 1)
    dark_block = dark_part.split("\n}\n", 1)[0]
    for role, light, dark in rows:
        assert f"{role}: {light};" in light_part
        assert f"{role}: {dark};" in dark_block


def test_layout_stylesheet_defines_no_colour_font_or_token() -> None:
    """The layout sheet arranges only: no colour literal, font family, or token declaration."""
    css = re.sub(r"/\*.*?\*/", "", _LAYOUT_CSS, flags=re.DOTALL)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\b(?:hwb|lab|lch|oklab|oklch)\(", css)
    assert not re.search(
        r"(?<![\w-])(?:transparent|currentcolor|white|black|red|green|blue|gray|grey)(?![\w-])", css
    )
    assert "font-family" not in css
    assert not re.search(r"(?<![\w(])--(?:c|t)-[\w-]*\s*:", css)
