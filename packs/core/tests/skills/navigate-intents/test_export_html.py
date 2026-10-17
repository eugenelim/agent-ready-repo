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
_PARTS_DIR = _SCRIPTS / "view_src"
_FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
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
view = nav._load_view_mod()

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


def _joined(html: str) -> str:
    """Return the page's one executable script, as the builder joined it."""
    (script,) = [t for t in _parse(html).texts["script"] if t.strip() and "function" in t]
    return script


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
    assert script == _joined(mixed_html)
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


def _has_token(code: str, token: str) -> bool:
    """Match *token* on identifier boundaries: no letter, digit, _ or $ touches an identifier end."""
    before = r"(?<![A-Za-z0-9_$])" if re.match(r"[A-Za-z0-9_$]", token) else ""
    after = r"(?![A-Za-z0-9_$])" if re.search(r"[A-Za-z0-9_$]$", token) else ""
    return re.search(before + re.escape(token) + after, code) is not None


def test_script_holds_no_forbidden_api(mixed_html: str) -> None:
    code = _strip_comments(_joined(mixed_html))
    for token in (
        "innerHTML",
        "outerHTML",
        "insertAdjacentHTML",
        "document.write",
        "eval(",
        "Function(",
        "srcdoc",
        "javascript:",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
        "sendBeacon",
        "import(",
        "require(",
        ".style",
        "cssText",
        ".animate(",
        "requestAnimationFrame",
        "startViewTransition",
        "scrollIntoView",
    ):
        assert not _has_token(code, token), token
    assert not re.search(r"set(Timeout|Interval)\(\s*['\"`]", code)
    assert not re.search(r"setAttribute\(\s*['\"]style['\"]", code)


def test_the_token_match_respects_identifier_boundaries() -> None:
    assert _has_token("a.style.x", ".style") and not _has_token("a.styles", ".style")
    assert _has_token("x = fetch(u)", "fetch(") and not _has_token("prefetch(u)", "fetch(")
    assert _has_token("import(x)", "import(") and not _has_token("reimport(x)", "import(")


def test_joined_script_is_printable_ascii(mixed_html: str) -> None:
    for char in _joined(mixed_html):
        assert not (ord(char) > 0x7E or (ord(char) < 0x20 and char not in "\n\t")), hex(ord(char))


def _part_text(name: str) -> str:
    return (_PARTS_DIR / name).read_text(encoding="utf-8")


def test_joined_script_is_prologue_parts_epilogue(mixed_html: str) -> None:
    expected = (
        "'use strict';\n(function () {\n"
        + "".join(_part_text(name) for name in view._SCRIPT_PARTS)
        + "})();\n"
    )
    assert _joined(mixed_html) == expected


def test_script_digest_covers_the_joined_script(mixed_html: str) -> None:
    shape = _parse(mixed_html)
    _tag, attrs = shape.head_children[0]
    script = _joined(mixed_html)
    assert f"script-src 'sha256-{_digest(script)}';" in attrs["content"]


def test_part_list_matches_view_src() -> None:
    listed = list(view._SCRIPT_PARTS)
    assert len(listed) == len(set(listed))
    assert sorted(listed) == sorted(p.name for p in _PARTS_DIR.glob("*.js"))
    for name in listed:
        assert (_PARTS_DIR / name).is_file() and not (_PARTS_DIR / name).is_symlink(), name
        assert _part_text(name).endswith("\n"), name


def test_no_part_exceeds_400_lines() -> None:
    for part in _PARTS_DIR.glob("*.js"):
        assert part.read_bytes().count(b"\n") <= 400, part.name


def _refused_export(tmp_path: pathlib.Path) -> None:
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    result, code = nav.run_export(_FIXTURES / "mixed", str(out), "view.html", None)
    assert code == 1, result
    assert result["error"]["code"] == "resolver_unavailable"
    assert list(out.iterdir()) == []


def test_a_missing_or_unsafe_part_refuses_the_export(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing"
    monkeypatch.setattr(view, "_SCRIPT_PARTS", (*view._SCRIPT_PARTS, "no-such-part.js"))
    _refused_export(missing)
    monkeypatch.undo()
    for index, injected in enumerate(("</script>", "</SCRIPT >", "<!--")):
        parts = tmp_path / f"parts{index}"
        shutil.copytree(_PARTS_DIR, parts)
        victim = parts / view._SCRIPT_PARTS[1]
        victim.write_text(victim.read_text(encoding="utf-8") + f"// {injected}\n", encoding="utf-8")
        monkeypatch.setattr(view, "_SOURCE_DIR", parts)
        _refused_export(tmp_path / f"case{index}")
        monkeypatch.undo()


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_escape_function_matches_the_text_output(mixed_html: str, tmp_path: pathlib.Path) -> None:
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
    joined = tmp_path / "joined-view.js"
    joined.write_text(_joined(mixed_html), encoding="utf-8")
    script = (
        "const m = require(process.argv[1]);"
        "const probes = JSON.parse(process.argv[2]);"
        "process.stdout.write(JSON.stringify(probes.map(m.escapeDisplay)));"
    )
    done = subprocess.run(
        ["node", "-e", script, str(joined), json.dumps(probes)],
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


def test_layout_stylesheet_defines_no_colour_font_or_token() -> None:
    """The layout sheet arranges only: no colour literal, font family, or token declaration."""
    css = re.sub(r"/\*.*?\*/", "", _LAYOUT_CSS, flags=re.DOTALL)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(|\b(?:hwb|lab|lch|oklab|oklch)\(", css)
    assert not re.search(
        r"(?<![\w-])(?:transparent|currentcolor|white|black|red|green|blue|gray|grey)(?![\w-])", css
    )
    assert "font-family" not in css
    assert not re.search(r"(?<![\w(])--(?:c|t)-[\w-]*\s*:", css)
    # Colour roles and type weight belong to the shared base, not to the layout.
    assert "var(--c-" not in css
    assert not re.search(r"font-weight|(?<![\w-])font\s*:", css)


def test_hostile_export_keeps_the_csp_string_and_the_script_stays_clean(hostile_html: str, mixed_html: str) -> None:
    """The dependency work leaves the policy unchanged and the joined script free of banned APIs."""
    for html in (hostile_html, mixed_html):
        shape = _parse(html)
        _tag, attrs = shape.head_children[0]
        (script,) = [t for t in shape.texts["script"] if t.strip() and "function" in t]
        (style,) = shape.texts["style"]
        assert attrs["content"] == (
            f"default-src 'none'; script-src 'sha256-{_digest(script)}'; "
            f"style-src 'sha256-{_digest(style)}'; img-src 'none'; base-uri 'none'; "
            "form-action 'none'"
        )
    code = _strip_comments(_joined(mixed_html))
    for token in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write", "eval(", "Function(", "srcdoc", "javascript:", "fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "import("):
        assert token not in code, token


def test_a_symlinked_intent_file_is_refused_by_the_query_and_the_export(tmp_path: pathlib.Path) -> None:
    corpus = tmp_path / "dependency"
    shutil.copytree(_FIXTURES / "dependency", corpus)
    intents = corpus / "docs" / "product" / "intents"
    (intents / "FEAT-0099-link.md").symlink_to(intents / "FEAT-0001-alpha.md")
    result, code = nav.run_query(
        corpus, ["query", "--operation", "dependencies", "--id", "intent:alpha", "--direction", "both", "--depth", "2"]
    )
    assert code != 0 and result["error"]["code"] == "unsafe_input", result
    out = tmp_path / "out"
    out.mkdir()
    result, code = nav.run_export(corpus, str(out), "view.html", None)
    assert code != 0 and result["error"]["code"] == "unsafe_input", result
    assert not (out / "view.html").exists()
