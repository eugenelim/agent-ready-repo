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
_PARTS = {p.name: p for p in _PARTS_DIR.glob("*.js")}
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
        self._executable = False
        self.executable = 0
        self.executable_scripts: list[str] = []
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
            self.executable_scripts.append("")
        if tag == "style":
            self.style_elements += 1
        if tag in ("script", "style"):
            self._current = tag
            self.texts[tag].append("")
            self._executable = tag == "script" and mapping.get("type") != "application/json"

    def handle_endtag(self, tag: str) -> None:
        if tag == "head" and self._stack:
            self._stack.pop()
        if tag in ("script", "style"):
            self._current = None

    def handle_data(self, data: str) -> None:
        if self._current:
            self.texts[self._current][-1] += data
            if self._current == "script" and self._executable:
                self.executable_scripts[-1] += data


def _parse(html: str) -> _Shape:
    shape = _Shape()
    shape.feed(html)
    shape.close()
    return shape


def _digest(content: str) -> str:
    return base64.b64encode(hashlib.sha256(content.encode("utf-8")).digest()).decode("ascii")


def _joined(html: str) -> str:
    """Return the page's one executable script, as the builder joined it."""
    (script,) = _parse(html).executable_scripts
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
    return _PARTS[name].read_text(encoding="utf-8")


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
    assert sorted(listed) == sorted(_PARTS)
    for name in listed:
        assert name in _PARTS, name
        assert _PARTS[name].is_file() and not _PARTS[name].is_symlink(), name
        assert _part_text(name).endswith("\n"), name


def test_no_part_exceeds_400_lines() -> None:
    for part in _PARTS_DIR.glob("*.js"):
        assert part.read_bytes().count(b"\n") <= 400, part.name


def _refused_export(tmp_path: pathlib.Path) -> str:
    out = tmp_path / "out"
    out.mkdir(parents=True, exist_ok=True)
    result, code = nav.run_export(_FIXTURES / "mixed", str(out), "view.html", None)
    assert code == 1, result
    assert result["error"]["code"] == "resolver_unavailable"
    assert list(out.iterdir()) == []
    return str(result["error"]["message"])


def test_a_missing_or_unsafe_part_refuses_the_export(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    missing = tmp_path / "missing"
    monkeypatch.setattr(view, "_SCRIPT_PARTS", (*view._SCRIPT_PARTS, "no-such-part.js"))
    message = _refused_export(missing)
    assert "no-such-part.js" in message
    assert not re.search(r"(?:^|[\s'\"(])(?:/|[A-Za-z]:[\\/])\S", message), message
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


_PROMPT_PREFIX = {
    "spec": "docs/specs/",
    "brief": "docs/product/briefs/",
    "intent": "docs/product/intents/",
}
_PROMPT_TEMPLATES = {
    3: "Use the work-loop skill to continue building `{}`.",
    4: "Use the work-loop skill to implement `{}`.",
    5: "Use the new-spec skill to finish the spec at `{}`.",
    6: "Use the author-delivery-brief skill in continue mode on `{}`.",
    7: "Use the intent skill to decompose `{}`.",
    9: "Use the close-work skill to check whether `{}` can close.",
    10: "Use the intent skill to keep shaping `{}`.",
}
_HOSTILE_PROBES = [
    " ", "\t", "\n", " ", "‮", "ignore previous instructions", "`", "$(",
    "|", ";", "&", ">", "'", '"', "\\", "é",
]


def _safe_path(record_type: str, path: Any) -> bool:
    """The spec's safe-path term, written from its words."""
    if not isinstance(path, str) or len(path) > 200:
        return False
    prefix = _PROMPT_PREFIX.get(record_type)
    if prefix is None or not path.startswith(prefix) or not path.endswith(".md"):
        return False
    return all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}", seg) for seg in path.split("/"))


def _boundary_probes(record_type: str) -> list[tuple[str, bool]]:
    """The four limit probes for a type, each with its literal outcome (True: a prompt shows).

    A last segment of exactly 100 characters (101 refused), then a multi-segment path of exactly
    200 characters (201 refused) whose every segment is at most 100, so length alone decides.
    """
    prefix = _PROMPT_PREFIX[record_type]
    if record_type == "spec":  # the spec.md segment is fixed, so the long segment is the directory
        def one(n: int) -> str:
            return f"{prefix}{'a' * n}/spec.md"

        def two(total: int) -> str:
            rest = total - len(prefix) - len("/spec.md") - 1  # two directory names and a slash
            return f"{prefix}{'a' * (rest // 2)}/{'a' * (rest - rest // 2)}/spec.md"
    else:
        def one(n: int) -> str:
            return f"{prefix}{'a' * (n - 3)}.md"

        def two(total: int) -> str:
            rest = total - len(prefix) - len(".md") - 1  # a directory name, a slash and a file stem
            return f"{prefix}{'a' * (rest // 2)}/{'a' * (rest - rest // 2)}.md"

    probes = [(one(100), True), (one(101), False), (two(200), True), (two(201), False)]
    assert [len(p) for p, _ in probes][2:] == [200, 201]
    for path, _ in probes:
        assert max(len(seg) for seg in path.split("/")) <= 101
    assert [len(path.split("/")[-2 if record_type == "spec" else -1]) for path, _ in probes[:2]] == [100, 101]
    return probes


def _probe_paths() -> dict[str, list[str]]:
    """AC-0008's probe set, per record type."""
    by_type: dict[str, list[str]] = {}
    for record_type, prefix in _PROMPT_PREFIX.items():
        safe = f"{prefix}thing/spec.md"
        paths = [
            safe,
            *[path for path, _ in _boundary_probes(record_type)],
            safe[:-3],
            f"{prefix}x//spec.md",
            f"{prefix}./spec.md",
            f"{prefix}../spec.md",
            f"{prefix}x/./spec.md",
            f"{prefix}x/../spec.md",
            "/" + safe,
        ]
        paths += [pre + "thing/spec.md" for other, pre in _PROMPT_PREFIX.items() if other != record_type]
        for probe in _HOSTILE_PROBES:
            paths += [f"{prefix}th{probe}ing/spec.md", f"{prefix}thing/spec{probe}.md"]
        by_type[record_type] = paths
    return by_type


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_handover_prompt_matches_the_safe_path_rule(mixed_html: str, tmp_path: pathlib.Path) -> None:
    cases: list[list[Any]] = []
    for record_type, paths in _probe_paths().items():
        for rule in range(1, 11):
            cases += [[record_type, rule, path] for path in paths]
    for record_type in ("other", "__proto__", "constructor"):
        cases.append([record_type, 4, "docs/specs/thing/spec.md"])
    for path in (None, 7, ["docs/specs/a.md"]):
        cases.append(["spec", 4, path])
    for rule in ("__proto__", "constructor", "toString"):
        cases.append(["spec", rule, "docs/specs/thing/spec.md"])
    joined = tmp_path / "joined-view.js"
    joined.write_text(_joined(mixed_html), encoding="utf-8")
    script = (
        "const m = require(process.argv[1]);"
        "const cases = JSON.parse(process.argv[2]);"
        "process.stdout.write(JSON.stringify(cases.map(c => {"
        "  try { return m.handoverPrompt(c[0], c[1], c[2]); } catch (e) { return 'THREW'; }"
        "})));"
    )
    done = subprocess.run(
        ["node", "-e", script, str(joined), json.dumps(cases)],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    results = json.loads(done.stdout)
    assert len(results) == len(cases)
    for (record_type, rule, path), got in zip(cases, results, strict=True):
        label = (record_type, rule, path)
        assert got != "THREW", label
        if rule not in _PROMPT_TEMPLATES:
            assert got is None, label
        elif _safe_path(record_type, path):
            assert got == {"prompt": _PROMPT_TEMPLATES[rule].format(path)}, label
        else:
            assert got == {"refused": True}, label
            assert not (isinstance(got, dict) and "prompt" in got), label
    assert any(r not in (None, {"refused": True}) for r in results)
    literal = {(t, p): ok for t in _PROMPT_PREFIX for p, ok in _boundary_probes(t)}
    seen = 0
    for (record_type, rule, path), got in zip(cases, results, strict=True):
        if rule in _PROMPT_TEMPLATES and isinstance(path, str) and (record_type, path) in literal:
            assert (got != {"refused": True}) is literal[(record_type, path)], (record_type, len(path))
            seen += 1
    assert seen == 4 * 3 * len(_PROMPT_TEMPLATES)


def _uses_location_beyond_hash(code: str) -> bool:
    return re.search(r"(?<![A-Za-z0-9_$])location(?![A-Za-z0-9_$])(?!\.hash(?![A-Za-z0-9_$]))", code) is not None


def test_view_script_has_no_launch_api(mixed_html: str) -> None:
    assert _uses_location_beyond_hash("window.location = u") and _uses_location_beyond_hash("location.href")
    assert not _uses_location_beyond_hash("x = location.hash; window.location.hash = y")
    code = _strip_comments(_joined(mixed_html))
    assert not _uses_location_beyond_hash(code)
    for token in ("window.open", "open(", "execCommand", "showModalDialog", "navigator.share"):
        assert not _has_token(code, token), token


_DARK = "@media (prefers-color-scheme: dark)"
_MOTION = "@media (prefers-reduced-motion: no-preference)"
_Decl = tuple[tuple[str, ...], str, str, str]  # (at-rule chain, selector, property, value)


def _squash(text: str) -> str:
    """Collapse every run of whitespace to one space."""
    return re.sub(r"\s+", " ", text).strip()


def _walk_css(css: str) -> tuple[list[_Decl], list[tuple[tuple[str, ...], str]]]:
    """Walk braces and return each declaration and each at-rule with its enclosing at-rule chain."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    stack: list[str] = []
    decls: list[_Decl] = []
    at_rules: list[tuple[tuple[str, ...], str]] = []
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
            prelude = _squash("".join(buf))
            buf.clear()
            if prelude.startswith("@"):
                at_rules.append((tuple(b for b in stack if b.startswith("@")), prelude))
            stack.append(prelude)
        elif ch == "}" and paren == 0:
            flush()
            stack.pop()
        elif ch == ";" and paren == 0:
            flush()
        else:
            buf.append(ch)
    return decls, at_rules


def _both_sheets() -> list[_Decl]:
    return _walk_css(_BASE_CSS)[0] + _walk_css(_LAYOUT_CSS)[0]


def _root_values(css: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return the custom properties on :root, and those inside the dark-scheme block."""
    light: dict[str, str] = {}
    dark: dict[str, str] = {}
    for chain, selector, prop, value in _walk_css(css)[0]:
        if selector == ":root" and prop.startswith("--"):
            if chain == ():
                light[prop] = _squash(value)
            elif chain == (_DARK,):
                dark[prop] = _squash(value)
    return light, dark


def _declared_properties(css: str) -> set[str]:
    light, dark = _root_values(css)
    return set(light) | set(dark)


def _unresolved_vars(declared: set[str], css: str) -> set[str]:
    return {name for name in re.findall(r"var\(\s*(--[\w-]+)", css) if name not in declared}


def test_every_var_resolves_to_a_declared_property() -> None:
    """Every var() in either sheet resolves to a property view-base.css declares."""
    declared = _declared_properties(_BASE_CSS)
    assert declared
    assert _unresolved_vars(declared, _BASE_CSS) == set()
    assert _unresolved_vars(declared, _LAYOUT_CSS) == set()
    # The check can fail: an unknown var() is reported.
    assert _unresolved_vars(declared, ".a { color: var(--c-nope); }") == {"--c-nope"}


def test_forced_colors_marks_the_current_selection() -> None:
    """A forced-colors block gives the picked row and the current question an outline."""
    forced = [(s, p, v) for chain, s, p, v in _walk_css(_BASE_CSS)[0] if chain == ("@media (forced-colors: active)",)]
    assert forced
    for needle in ('.row-link[aria-current="true"]', '.question-link[aria-current="page"]'):
        assert any(needle in s and p == "outline" and "Highlight" in v for s, p, v in forced), needle
    assert not [1 for chain, *_ in _walk_css(_LAYOUT_CSS)[0] if any("forced-colors" in b for b in chain)]


def test_stylesheets_declare_no_external_loads() -> None:
    """Neither stylesheet may load a url or import another sheet."""
    for css in (_BASE_CSS, _LAYOUT_CSS):
        for word in ("url(", "@import"):
            assert word not in css


_COLOUR_VALUE = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|(?<![\w-])(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark)\("
    r"|(?<![\w-])(?:transparent|currentcolor|white|black|red|green|blue|gray|grey|orange|yellow|purple|pink|brown|silver|navy|teal|aqua|cyan|magenta)(?![\w-])"
)


def _layout_violations(css: str) -> list[str]:
    """Name each declaration in a layout sheet that a layout sheet may not make."""
    found = []
    for _chain, _selector, prop, value in _walk_css(css)[0]:
        if prop.startswith("--"):
            found.append(f"custom property {prop}")
        if _COLOUR_VALUE.search(value) or "var(--c-" in value:
            found.append(f"colour in {prop}: {value}")
        if prop in ("font", "font-family", "font-weight", "box-shadow") or re.match(r"(?:transition|animation)", prop):
            found.append(f"{prop} is the base's")
        if prop == "border-radius" and re.sub(r"var\(--r-\d\)|\b0\b|\s", "", value):
            found.append(f"border-radius {value}")
    return found


def test_layout_stylesheet_defines_no_colour_font_or_token() -> None:
    """The layout sheet arranges only: no colour, font, shadow, radius literal, motion, or token declaration."""
    assert _layout_violations(_LAYOUT_CSS) == []
    # The check can fail on each kind of declaration it bans.
    for bad in ("--x: 1px", "color: #fff", "background: rgb(0 0 0)", "border-color: red", "font-weight: 600",
                "font-family: serif", "box-shadow: none", "border-radius: 4px", "transition: color 1s", "animation-name: a"):
        assert _layout_violations(f".a {{ {bad}; }}"), bad
    assert _layout_violations(".a { border-radius: var(--r-2); padding: var(--s-1); }") == []


def test_layout_sheet_holds_no_new_style() -> None:
    """The rail-group label and the roadmap's rules put every colour and type choice in the base sheet."""
    assert _layout_violations(_LAYOUT_CSS) == []
    assert ".rail-group" in _BASE_CSS
    layout_rail = [(s, p) for _c, s, p, _v in _walk_css(_LAYOUT_CSS)[0] if "rail-group" in s]
    assert layout_rail
    assert not [p for _s, p in layout_rail if p in ("color", "font", "text-transform", "letter-spacing")]


def test_roadmap_cells_use_a_radius_token() -> None:
    """The bar's cells round with a radius token, never a literal (AC-0043)."""
    radii = [v for _c, s, p, v in _walk_css(_BASE_CSS)[0] if s == ".rm-cell" and p == "border-radius"]
    assert radii
    assert all(re.fullmatch(r"var\(--r-\d\)", v.strip()) for v in radii), radii


def test_pressed_choice_mark_has_a_plain_content_before_the_alt_text_form() -> None:
    """A browser that ignores the alt-text form still shows the mark: the plain declaration comes first."""
    selector = '.seg-btn[aria-pressed="true"]::before'
    contents = [v.strip() for _c, s, p, v in _walk_css(_BASE_CSS)[0] if s == selector and p == "content"]
    assert contents == ['"\\2713"', '"\\2713" / ""'], contents


def test_walker_records_the_enclosing_at_rule_chain() -> None:
    """The walker sees a declaration's whole chain, even through a keyframes block."""
    css = (
        ".a { transition: color 1s; }"
        f"{_MOTION} {{ .b {{ transition: color 1s; }} @keyframes k {{ from {{ opacity: 0; }} }} }}"
    )
    decls, at_rules = _walk_css(css)
    assert [(chain, prop) for chain, _s, prop, _v in decls] == [
        ((), "transition"),
        ((_MOTION,), "transition"),
        ((_MOTION, "@keyframes k"), "opacity"),
    ]
    assert at_rules == [((), _MOTION), ((_MOTION,), "@keyframes k")]


def _is_motion_prop(prop: str) -> bool:
    return bool(re.match(r"(?:transition|animation)(?:-|$)", prop))


def _outside_motion_block(css: str) -> list[str]:
    decls, at_rules = _walk_css(css)
    loose = [f"{prop}: {value}" for chain, _s, prop, value in decls if _is_motion_prop(prop) and _MOTION not in chain]
    loose += [prelude for chain, prelude in at_rules if prelude.startswith("@keyframes") and _MOTION not in chain]
    return loose


def test_motion_sits_behind_reduced_motion() -> None:
    """Every transition, animation and keyframes rule is inside the no-preference reduced-motion block."""
    assert any(_is_motion_prop(prop) for _c, _s, prop, _v in _both_sheets())
    for css in (_BASE_CSS, _LAYOUT_CSS):
        assert _outside_motion_block(css) == []
    # The check can fail: a transition or keyframes outside the block is found.
    assert _outside_motion_block(".a { transition: color 1s; }") == ["transition: color 1s"]
    assert _outside_motion_block("@keyframes k { from { opacity: 0; } }") == ["@keyframes k"]
    assert _outside_motion_block(f"{_MOTION} {{ .a {{ transition: color 1s; }} }}") == []


_PAINT = {"background-color", "color", "border-color", "box-shadow", "opacity"}
_TIME = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:ms|s)", re.IGNORECASE)
_EASING = {"ease", "ease-in", "ease-out", "ease-in-out", "linear", "step-start", "step-end", "allow-discrete", "normal"}


def _split_top(value: str, sep: str) -> list[str]:
    """Split on a separator that sits outside parentheses."""
    parts, depth, cur = [], 0, ""
    for ch in value:
        depth += (ch == "(") - (ch == ")")
        if ch == sep and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    return parts + [cur]


def _transitioned_properties(decls: list[_Decl]) -> list[str]:
    names: list[str] = []
    for _chain, _selector, prop, value in decls:
        if prop == "transition-property":
            names += [n.strip() for n in value.split(",")]
        elif prop == "transition":
            for item in _split_top(value, ","):
                tokens = [t for t in _split_top(item.strip(), " ") if t]
                named = [t for t in tokens if not _TIME.fullmatch(t) and t not in _EASING and "(" not in t]
                names.append(named[0] if named else "all")
    return names


def test_transitions_name_only_paint_properties() -> None:
    """A transition names only background-color, color, border-color, box-shadow or opacity."""
    names = _transitioned_properties(_both_sheets())
    assert names
    assert set(names) <= _PAINT, set(names) - _PAINT
    # The check can fail: a shorthand with no property counts as all, and a layout property is refused.
    assert _transitioned_properties(_walk_css(".a { transition: 120ms ease; }")[0]) == ["all"]
    assert _transitioned_properties(_walk_css(".a { transition: width 1s, color 1s; }")[0]) == ["width", "color"]
    assert _transitioned_properties(_walk_css(".a { transition-property: height; }")[0]) == ["height"]


def _keyframe_problems(decls: list[_Decl]) -> list[str]:
    found = []
    for chain, _selector, prop, value in decls:
        if not any(b.startswith("@keyframes") for b in chain):
            continue
        if prop not in ("opacity", "transform"):
            found.append(f"{prop}: {value}")
        elif prop == "transform":
            rise = re.fullmatch(r"translateY\((-?(?:\d+\.?\d*|\.\d+))px\)", value)
            if value != "none" and not (rise and abs(float(rise.group(1))) <= 4):
                found.append(f"{prop}: {value}")
    return found


def test_keyframes_fade_and_rise_only() -> None:
    """A keyframes rule sets only opacity and a transform of none or a rise of at most 4px."""
    decls = _both_sheets()
    assert any(b.startswith("@keyframes") for chain, *_ in decls for b in chain)
    assert _keyframe_problems(decls) == []
    # The check can fail on another property or a larger or different transform.
    for bad in ("width: 1px", "transform: translateY(5px)", "transform: scale(2)", "transform: translateX(2px)"):
        assert _keyframe_problems(_walk_css(f"@keyframes k {{ to {{ {bad}; }} }}")[0]), bad


def _timing_problems(decls: list[_Decl]) -> list[str]:
    found = []
    for _chain, _selector, prop, value in decls:
        if re.match(r"(?:scroll|view)-timeline|animation-timeline|scroll-behavior", prop):
            found.append(prop)
        if not _is_motion_prop(prop):
            continue
        if prop == "animation-iteration-count" and "infinite" in value or prop == "animation" and "infinite" in value.split():
            found.append(f"{prop}: {value}")
        if "var(" in value.lower():
            found.append(f"{prop}: {value}")
        if prop.startswith("animation") and re.search(r"(?<![\w-])(?:scroll|view)\(", value):
            found.append(f"{prop}: {value}")
        for amount in _TIME.findall(value):
            unit = amount.lower()
            ms = float(unit.rstrip("ms")) * (1 if unit.endswith("ms") else 1000)
            if ms > 200:
                found.append(f"{prop}: {amount}")
    return found


def test_motion_is_short_and_not_scroll_driven() -> None:
    """Every duration and delay is at most 200ms; nothing repeats, scrolls smoothly or follows scroll.

    The 200ms limit, and the 4px rise in the keyframes test, are fixed by the spec's criteria, not chosen here.
    No motion value may use var(), so the limits cannot be dodged through a custom property.
    """
    decls = _both_sheets()
    assert any(_TIME.search(value) for _c, _s, prop, value in decls if _is_motion_prop(prop))
    assert _timing_problems(decls) == []
    # The check can fail on a long duration or delay, a repeat, and each scroll-driven property.
    for bad in ("transition: color 0.3s", "animation: k 160ms ease 1s", "transition-delay: 250ms",
                "animation: k 100ms infinite", "animation-iteration-count: infinite", "scroll-behavior: smooth",
                "animation-timeline: scroll()", "view-timeline: --x", "animation: k 100ms linear view()", "transition: color 0.3S", "animation-delay: 250MS",
                "transition: color var(--t)", "animation-duration: VAR(--d)"):
        assert _timing_problems(_walk_css(f".a {{ {bad}; }}")[0]), bad
    assert _timing_problems(_walk_css(".a { transition: color 0.2s, opacity 120ms; }")[0]) == []


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


def test_view_source_names_no_health_words() -> None:
    """The view's source and the roadmap fixture's records never state a health judgement."""
    words = ("on track", "at risk", "off track")
    files = [*_PARTS_DIR.glob("*.js"), *_FIXTURES.glob("roadmap/docs/**/*.md")]
    assert any(f.name == "roadmap.js" for f in files) and any(f.name == "spec.md" for f in files)
    for path in files:
        text = path.read_text(encoding="utf-8").lower()
        assert not [w for w in words if w in text], path.name
