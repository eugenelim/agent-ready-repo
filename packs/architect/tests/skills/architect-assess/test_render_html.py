"""Construction tests for the architect-assess HTML renderer.

Loads `render_html.py` by path under a pack-unique module name, per
`packs/AGENTS.md` § Writing pack tests, and drives the real entry point
in-process with resolved temporary directories.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import html
import importlib.util
import io
import os
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from types import ModuleType

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "architect-assess"
SCRIPT = SKILL_ROOT / "scripts" / "render_html.py"
TEMPLATE = SKILL_ROOT / "assets" / "assessment.md"

TABLE_HEAD = "| Source | Locator | Evidence class | Limit |\n| --- | --- | --- | --- |\n"
ROW = "| README | `README.md` | Observed | two sentences |\n"
SOURCES = f"Sources checked:\n\n{TABLE_HEAD}{ROW}"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "architect_assess_render_html_under_test", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def mod() -> ModuleType:
    return _load()


def report(
    checkpoints: str | None = "Checkpoints: confirmed",
    overall: str | None = None,
    extra: str = "",
) -> str:
    """Build a report with the real template's section shapes."""
    charter = "Target: demo\n" + (f"{checkpoints}\n" if checkpoints else "")
    overall = overall if overall is not None else f"One view.\n\n{SOURCES}"
    return (
        "# Architecture assessment: demo\n\n## Bottom line\n\nIt works.\n\n"
        f"## Assessment charter\n\n{charter}\n"
        f"## Conceptual current state\n\nContext.\n\n### Overall architecture\n\n{overall}\n"
        f"### Architecture by subsystem\n\nParts.\n\n{SOURCES}\n"
        f"### Physical architecture\n\nnot assessed\n\nNo deployment files.\n\n{SOURCES}\n"
        "### Map checkpoint\n\ncontinue\n\n"
        "## Attention heat map\n\n"
        "| Area | Consequence | Pressure | Concentration / coupling | Verification weakness "
        "| Ops/data/security exposure | Confidence | Evidence |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
        "| core | High | low | medium | unknown | LOW | high | unknown |\n\n"
        f"## Findings\n\n{extra}"
    )


def run(
    tmp: Path, text: str | bytes | None, mod: ModuleType, capsys, name: str = "effort"
) -> tuple[int, str, str]:
    effort = tmp / name
    effort.mkdir(exist_ok=True)
    if text is not None:
        data = text if isinstance(text, bytes) else text.encode("utf-8")
        (effort / "assessment.md").write_bytes(data)
    code = mod.main([str(effort)])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def page(tmp: Path, text: str, mod: ModuleType, capsys) -> str:
    code, _, err = run(tmp, text, mod, capsys)
    assert code == 0, err
    return (tmp / "effort" / "assessment.html").read_text(encoding="utf-8")


class Tree(HTMLParser):
    """Collect elements and attributes of the rendered page."""

    def __init__(self) -> None:
        super().__init__()
        self.elements: list[str] = []
        self.attrs: list[tuple[str, str, str | None]] = []
        self.order: list[str] = []
        self.style = ""
        self.classes: list[tuple[str, str]] = []
        self._in_style = False
        self.cells: list[tuple[str, str]] = []
        self.anchor_attrs: list[list[tuple[str, str | None]]] = []
        self._cell: str | None = None

    def handle_starttag(self, tag, attrs):
        self.elements.append(tag)
        self.order.append(tag)
        for name, value in attrs:
            self.attrs.append((tag, name, value))
            if name == "class":
                self.classes.append((tag, value or ""))
        if tag == "a":
            self.anchor_attrs.append(attrs)
        if tag == "style":
            self._in_style = True
        if tag == "td":
            self._cell = dict(attrs).get("class") or ""

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_style:
            self.style += data
        if self._cell is not None:
            self.cells.append((self._cell, data))
            self._cell = None


ALLOWED_ELEMENTS = {
    "html",
    "head",
    "meta",
    "title",
    "style",
    "body",
    "main",
    "section",
    "div",
    "span",
    "p",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ul",
    "ol",
    "li",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "pre",
    "code",
    "strong",
    "em",
    "a",
    "details",
    "summary",
    "br",
    "hr",
    "header",
    "nav",
}
GLOBAL_ATTRS = {"class", "id", "lang", "charset", "http-equiv", "content"}
ALLOWED_TAG_ATTRS = {
    ("a", "href"),
    ("nav", "aria-label"),
    ("div", "aria-label"),
    ("div", "role"),
    ("div", "tabindex"),
    ("span", "data-mark"),
    ("span", "aria-hidden"),
}


def class_tokens(parsed: Tree) -> set[str]:
    return {token for _, value in parsed.classes for token in value.split()}


def content_hrefs(parsed: Tree) -> list[str]:
    """Hrefs of links in the report text, not the skip link or the contents links."""
    chrome = {"skip-link", "question-link"}
    anchors = [(dict(attrs)) for attrs in parsed.anchor_attrs]
    return [
        a["href"] for a in anchors if "href" in a and not chrome & set(a.get("class", "").split())
    ]


def banner_present(html_text: str) -> bool:
    return "banner-unconfirmed" in class_tokens(tree(html_text))


def tree(html_text: str) -> Tree:
    parsed = Tree()
    parsed.feed(html_text)
    return parsed


# ---- output, structure, links, escaping ------------------------------------------


def test_writes_exactly_one_file_and_exits_zero(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    code, out, err = run(tmp_path, report(), mod, capsys)
    assert (code, err) == (0, "")
    assert out.strip() == "render_html: ok"
    assert sorted(p.name for p in (tmp_path / "effort").iterdir()) == [
        "assessment.html",
        "assessment.md",
    ]


def test_rerun_replaces_an_existing_regular_output(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    page(tmp_path, report(), mod, capsys)
    second = page(tmp_path, report(extra="MARKER-SECOND"), mod, capsys)
    assert "MARKER-SECOND" in second


def test_markdown_subset_renders_as_elements(mod, tmp_path, capsys) -> None:
    body = "- item one\n- item two\n\n**bold** and `code`\n\n```\nfenced\n```\n"
    parsed = tree(page(tmp_path.resolve(), report(extra=body), mod, capsys))
    for tag in ("h2", "ul", "table", "pre", "strong", "code"):
        assert tag in parsed.elements


def test_allowed_links_become_anchors_and_others_do_not(mod, tmp_path, capsys) -> None:
    extra = (
        "[a](https://example.com/x) [b](#top) [c]( HTTP://example.com ) "
        "[d](javascript:alert(1)) [e](JavaScript:x) [f](data:text/html,x) [g](/rel)\n"
    )
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    hrefs = content_hrefs(tree(text))
    assert hrefs == ["https://example.com/x", "#top", "HTTP://example.com"]
    assert "[d](javascript:alert(1))" in text


def test_hostile_corpus_and_untrusted_values_are_escaped(mod, tmp_path, capsys) -> None:
    hostile = (
        '<script>alert(1)</script> <img src=x onerror="alert(2)"> "quoted" x" onmouseover="y\n\n'
        "```\n</script><!-- <b>\n```\n"
    )
    code, _, err = run(tmp_path.resolve(), report(extra=hostile), mod, capsys, name="a<b>&c")
    assert code == 0, err
    text = (tmp_path.resolve() / "a<b>&c" / "assessment.html").read_text(encoding="utf-8")
    assert "<script" not in text.lower()
    assert "&lt;script&gt;" in text and "&lt;img" in text
    assert "a&lt;b&gt;&amp;c" in text
    assert "a<b>" not in text
    assert "</script" not in text.lower()


def test_title_is_escaped(mod, tmp_path, capsys) -> None:
    title = report().replace("# Architecture assessment: demo", '# <i>T</i> & "t"', 1)
    text = page(tmp_path.resolve(), title, mod, capsys)
    assert "<title>&lt;i&gt;T&lt;/i&gt; &amp; &quot;t&quot;</title>" in text


def test_only_allowed_elements_and_attributes_are_emitted(mod, tmp_path, capsys) -> None:
    hostile = (
        '<meta http-equiv="refresh" content="0;url=http://x"> <base href="//x"> <form></form>\n'
    )
    parsed = tree(page(tmp_path.resolve(), report(extra=hostile), mod, capsys))
    assert set(parsed.elements) <= ALLOWED_ELEMENTS
    for tag, name, _ in parsed.attrs:
        assert (tag, name) in ALLOWED_TAG_ATTRS or name in GLOBAL_ATTRS, (tag, name)
    assert parsed.elements.count("meta") == 2


def test_style_body_has_no_import_or_url(mod, tmp_path, capsys) -> None:
    parsed = tree(page(tmp_path.resolve(), report(), mod, capsys))
    assert parsed.style and "@import" not in parsed.style and "url(" not in parsed.style


def test_csp_is_second_head_element_with_style_hash(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    parsed = tree(text)
    assert parsed.order[:5] == ["html", "head", "meta", "meta", "title"]
    assert parsed.order.index("style") > parsed.order.index("title")
    content = {n: v for _, n, v in parsed.attrs if n == "content"}["content"]
    directives = dict(d.strip().split(" ", 1) for d in content.split(";"))
    for name in ("default-src", "base-uri", "form-action"):
        assert directives[name] == "'none'"
    digest = base64.b64encode(hashlib.sha256(parsed.style.encode("utf-8")).digest()).decode()
    assert directives["style-src"] == f"'sha256-{digest}'"


# ---- provenance gate --------------------------------------------------------------


def _refused(mod, tmp_path, capsys, text: str) -> tuple[int, str]:
    tmp_path = tmp_path.resolve()
    code, out, err = run(tmp_path, text, mod, capsys)
    assert not (tmp_path / "effort" / "assessment.html").exists()
    assert out == ""
    return code, err


@pytest.mark.parametrize(
    "overall",
    [
        "View only.\n",
        f"View.\n\n{TABLE_HEAD}{ROW}",
        f"View.\n\nSources checked:\n\n| Source | Locator | Evidence | Limit |\n| --- | --- | --- | --- |\n{ROW}",
        f"View.\n\nSources checked:\n\n{TABLE_HEAD}",
        f"View.\n\n{SOURCES}\nTrailing paragraph.\n",
    ],
)
def test_orientation_subsection_without_usable_table_is_refused(
    mod, tmp_path, capsys, overall
) -> None:
    code, err = _refused(mod, tmp_path, capsys, report(overall=overall))
    assert code == 2
    assert (
        err.strip()
        == "render_html: refused: no usable Sources checked table in Overall architecture"
    )


def test_unfilled_template_is_refused_with_canonical_heading(mod, tmp_path, capsys) -> None:
    code, err = _refused(mod, tmp_path, capsys, TEMPLATE.read_text(encoding="utf-8"))
    assert code == 2 and err.strip().endswith("Overall architecture")


def test_heading_match_is_case_insensitive_but_token_is_canonical(mod, tmp_path, capsys) -> None:
    text = report().replace("### Physical architecture", "### PHYSICAL ARCHITECTURE")
    text = text.replace(SOURCES, "x\n", 3)
    code, err = _refused(mod, tmp_path, capsys, text)
    assert code == 2 and "Overall architecture" in err


def test_not_assessed_subsection_with_a_row_renders(mod, tmp_path, capsys) -> None:
    assert "not assessed" in page(tmp_path.resolve(), report(), mod, capsys)


def test_report_without_subsections_renders(mod, tmp_path, capsys) -> None:
    text = "# Title\n\n## Assessment charter\n\nCheckpoints: confirmed\n\n## Notes\n\nplain\n"
    assert "plain" in page(tmp_path.resolve(), text, mod, capsys)


def test_evidence_classes_render_by_case_insensitive_value(mod, tmp_path, capsys) -> None:
    rows = "".join(
        f"| s | l | {v} | x |\n" for v in ("OBSERVED", " inferred ", "Reported", "unknown")
    )
    overall = f"View.\n\nSources checked:\n\n{TABLE_HEAD}{rows}"
    parsed = tree(page(tmp_path.resolve(), report(overall=overall), mod, capsys))
    assert {"ev-observed", "ev-inferred", "ev-reported", "ev-unknown"} <= class_tokens(parsed)


def test_evidence_class_outside_the_set_is_refused(mod, tmp_path, capsys) -> None:
    overall = f"View.\n\nSources checked:\n\n{TABLE_HEAD}| s | l | <img src=x> | x |\n"
    code, err = _refused(mod, tmp_path, capsys, report(overall=overall))
    assert code == 2
    assert err.strip() == "render_html: refused: evidence class outside the allowed set"


# ---- heat, banner, diagrams, notice -----------------------------------------------


def test_heat_classes_attach_by_header_and_skip_confidence(mod, tmp_path, capsys) -> None:
    parsed = tree(page(tmp_path.resolve(), report(), mod, capsys))
    heat = [c for c, _ in parsed.cells if c.startswith("heat-")]
    assert heat == ["heat-high", "heat-low", "heat-medium", "heat-unknown", "heat-low"]


def test_confidence_cell_never_carries_a_heat_class(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert re.search(r"<td>high</td>", text)


@pytest.mark.parametrize(
    "checkpoints",
    [
        None,
        "Checkpoints: accepted-without-pause",
        "Checkpoints: confirmed extra",
        "Checkpoints: Confirmed",
    ],
)
def test_banner_shows_unless_charter_says_exactly_confirmed(
    mod, tmp_path, capsys, checkpoints
) -> None:
    text = page(tmp_path.resolve(), report(checkpoints=checkpoints), mod, capsys)
    assert banner_present(text)
    assert "Map and hotspot set not user-confirmed" in text
    assert text.index("banner-unconfirmed") < text.index("<h2")


def test_banner_absent_when_charter_confirms_once(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert not banner_present(text)


def test_confirmed_line_outside_charter_or_duplicated_does_not_suppress(
    mod, tmp_path, capsys
) -> None:
    outside = report(checkpoints=None, extra="Checkpoints: confirmed\n")
    assert banner_present(page(tmp_path.resolve(), outside, mod, capsys))
    twice = report(checkpoints="Checkpoints: confirmed\nCheckpoints: confirmed")
    assert banner_present(page(tmp_path.resolve(), twice, mod, capsys))
    fenced = report(checkpoints=None).replace(
        "Target: demo\n", "Target: demo\n```\nCheckpoints: confirmed\n```\n"
    )
    assert banner_present(page(tmp_path.resolve(), fenced, mod, capsys))


def test_mermaid_fence_is_a_labeled_escaped_source_block(mod, tmp_path, capsys) -> None:
    extra = "```mermaid\nflowchart TD\n  A[<b>x</b>] --> B\n```\n"
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    assert (
        'class="diagram-label">Diagram source (not rendered)</p><div class="source-scroll"' in text
    )
    assert "<pre><code>flowchart" in text
    assert "A[&lt;b&gt;x&lt;/b&gt;]" in text
    assert "<script" not in text.lower()


def test_notice_and_metadata(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert "notice-untrusted" in class_tokens(tree(text))
    assert ">Unverified: built from repository text and model analysis; not redacted<" in text
    assert re.search(r"Generated \d{4}-\d{2}-\d{2} UTC", text)
    assert f"Renderer version {mod.RENDERER_VERSION}" in text
    assert "Source: effort/assessment.md" in text


# ---- exit codes, tokens, confinement ---------------------------------------------


def _only_fixed_tokens(out: str, err: str) -> None:
    allowed = {
        "render_html: ok",
        "render_html: usage: render_html.py <effort-dir> [--diagrams]",
        "render_html: failed: script asset missing or unsafe",
        "render_html: failed: script asset over the size cap",
        "render_html: failed: script asset unreadable",
        "render_html: failed: script asset holds forbidden text",
        "render_html: refused: unsafe or missing path",
        "render_html: refused: source over the size cap",
        "render_html: refused: rendered page over the size cap",
        "render_html: refused: source is not valid UTF-8",
        "render_html: refused: evidence class outside the allowed set",
        "render_html: failed: internal error",
        "render_html: failed: stylesheet asset missing",
        "render_html: failed: stylesheet asset over the size cap",
        "render_html: failed: stylesheet asset is not valid UTF-8",
        "render_html: failed: stylesheet asset holds forbidden text",
    }
    for heading in ("Overall architecture", "Architecture by subsystem", "Physical architecture"):
        allowed.add(f"render_html: refused: no usable Sources checked table in {heading}")
    for name in ("open", "stat", "rename", "follow-symlinks", "O_DIRECTORY", "O_NOFOLLOW"):
        allowed.add(f"render_html: refused: host lacks descriptor walking: {name}")
    for line in (out + err).splitlines():
        assert line in allowed, line


def test_missing_source_and_directory_exit_three(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    (tmp_path / "effort").mkdir()
    assert mod.main([str(tmp_path / "effort")]) == 3
    _only_fixed_tokens(*capsys.readouterr())
    assert mod.main([str(tmp_path / "absent")]) == 3
    assert mod.main([str(tmp_path / "effort" / "assessment.md")]) == 3
    _only_fixed_tokens(*capsys.readouterr())


def test_wrong_argument_count_exits_two(mod, capsys) -> None:
    assert mod.main([]) == 2 and mod.main(["a", "b"]) == 2
    _only_fixed_tokens(*capsys.readouterr())


def test_unexpected_exception_exits_three_with_a_fixed_token(
    mod, tmp_path, capsys, monkeypatch
) -> None:
    tmp_path = tmp_path.resolve()
    monkeypatch.setattr(mod, "render", lambda *a: (_ for _ in ()).throw(RuntimeError("SECRET /x")))
    code, out, err = run(tmp_path, report(), mod, capsys)
    assert code == 3 and "SECRET" not in out + err
    _only_fixed_tokens(out, err)


def test_every_path_exits_zero_two_or_three_with_fixed_tokens(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    for text in (report(), b"\xff\xfe", "x" * (2 * 1024 * 1024 + 1), report(overall="v\n")):
        code, out, err = run(tmp_path, text, mod, capsys)
        assert code in (0, 2, 3)
        _only_fixed_tokens(out, err)


def test_invalid_utf8_and_oversized_regular_source_exit_two(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    code, _, err = run(tmp_path, b"\xff\xfe\x00", mod, capsys)
    assert code == 2 and err.strip() == "render_html: refused: source is not valid UTF-8"
    code, _, err = run(tmp_path, "x" * (2 * 1024 * 1024 + 1), mod, capsys)
    assert code == 2 and "size cap" in err
    assert not (tmp_path / "effort" / "assessment.html").exists()


def test_symlinked_source_output_and_ancestor_exit_three(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    real = tmp_path / "real.md"
    real.write_text("x" * (2 * 1024 * 1024 + 1))
    effort = tmp_path / "effort"
    effort.mkdir()
    Path(effort / "assessment.md").symlink_to(real)
    assert mod.main([str(effort)]) == 3  # confinement beats the size cap
    assert not (effort / "assessment.html").exists()
    capsys.readouterr()
    (effort / "assessment.md").unlink()
    (effort / "assessment.md").write_text(report())
    target = tmp_path / "elsewhere.html"
    target.write_text("keep")
    Path(effort / "assessment.html").symlink_to(target)
    assert mod.main([str(effort)]) == 3
    assert target.read_text() == "keep"
    capsys.readouterr()
    (effort / "assessment.html").unlink()
    link = tmp_path / "link"
    Path(link).symlink_to(effort)
    assert mod.main([str(link)]) == 3
    assert mod.main([str(link / "." / "x")]) == 3
    assert not (effort / "assessment.html").exists()


@pytest.mark.parametrize(
    "missing", ["open", "stat", "rename", "follow-symlinks", "O_DIRECTORY", "O_NOFOLLOW"]
)
def test_missing_descriptor_capability_exits_three(
    mod, tmp_path, capsys, monkeypatch, missing
) -> None:
    tmp_path = tmp_path.resolve()
    dir_fd = set(os.supports_dir_fd)
    follow = set(os.supports_follow_symlinks)
    if missing == "open":
        dir_fd.discard(os.open)
    elif missing == "stat":
        dir_fd.discard(os.stat)
    elif missing == "rename":
        dir_fd.discard(os.rename)
    elif missing == "follow-symlinks":
        follow.discard(os.stat)
    else:
        monkeypatch.delattr(os, missing)
    monkeypatch.setattr(os, "supports_dir_fd", dir_fd)
    monkeypatch.setattr(os, "supports_follow_symlinks", follow)
    code, out, err = run(tmp_path, report(), mod, capsys)
    assert code == 3 and missing in err
    assert not (tmp_path / "effort" / "assessment.html").exists()


def test_renders_when_agentbundle_is_not_importable(mod, tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "agentbundle", None)
    monkeypatch.setitem(sys.modules, "agentbundle.catalogue_tooling", None)
    assert 'class="page-title"' in page(tmp_path.resolve(), report(), mod, capsys)


def test_imports_and_calls_stay_inside_the_allow_list() -> None:
    tree_ = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    allowed = {
        "argparse",
        "base64",
        "datetime",
        "hashlib",
        "html",
        "importlib.util",
        "os",
        "pathlib",
        "re",
        "stat",
        "sys",
        "typing",
        "unicodedata",
    }
    for node in ast.walk(tree_):
        if isinstance(node, ast.Import):
            assert {alias.name for alias in node.names} <= allowed
        if isinstance(node, ast.ImportFrom):
            assert node.module in allowed
        if (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
        ):
            name = node.attr
            assert name not in {"system", "popen", "fork", "posix_spawn"}
            assert not name.startswith(("spawn", "exec"))


def test_utf8_streams_are_set_before_the_first_print(mod, tmp_path, monkeypatch) -> None:
    out = io.TextIOWrapper(io.BytesIO(), encoding="latin-1")
    err = io.TextIOWrapper(io.BytesIO(), encoding="latin-1")
    monkeypatch.setattr(sys, "stdout", out)
    monkeypatch.setattr(sys, "stderr", err)
    tmp_path = tmp_path.resolve()
    (tmp_path / "e").mkdir()
    (tmp_path / "e" / "assessment.md").write_text(report(), encoding="utf-8")
    assert mod.main([str(tmp_path / "e")]) == 0
    assert out.encoding == "utf-8" and err.encoding == "utf-8"


def test_symlink_above_the_effort_directory_exits_three(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    real = tmp_path / "real"
    (real / "effort").mkdir(parents=True)
    (real / "effort" / "assessment.md").write_text(report(), encoding="utf-8")
    Path(tmp_path / "link").symlink_to(real)
    assert mod.main([str(tmp_path / "link" / "effort")]) == 3
    assert not (real / "effort" / "assessment.html").exists()
    _only_fixed_tokens(*capsys.readouterr())


def test_charter_lines_render_on_separate_lines_and_prose_wraps_into_one_paragraph(
    mod, tmp_path, capsys
) -> None:
    text = page(tmp_path.resolve(), report(extra="first half\nsecond half\n"), mod, capsys)
    assert "Target: demo<br>Checkpoints: confirmed" in text
    assert "<p>first half second half</p>" in text


# ---- review repairs --------------------------------------------------------------


def test_planted_fence_cannot_hide_the_real_charter_line(mod, tmp_path, capsys) -> None:
    real = "## Assessment charter\nCheckpoints: accepted-without-pause\n## Notes\nplain\n"
    fake = "## Assessment charter\nCheckpoints: confirmed\n"
    planted = f"# T\n## Bottom line\n```\n```x\n{fake}```\n{real}"
    longer = f"# T\n## Bottom line\n````\n```\n{fake}````\n{real}"
    for source in (planted, longer):
        text = page(tmp_path.resolve(), source, mod, capsys)
        assert banner_present(text)
        assert "<pre><code>## Assessment charter\nCheckpoints: accepted-without-pause" not in text


def test_confirmed_once_in_charter_and_again_elsewhere_shows_no_banner(
    mod, tmp_path, capsys
) -> None:
    text = page(tmp_path.resolve(), report(extra="Checkpoints: confirmed\n"), mod, capsys)
    assert not banner_present(text)


@pytest.mark.parametrize(
    "heading",
    ["### Overall architecture ###", "## Overall architecture", "#### Overall architecture"],
)
def test_heading_variants_still_hit_the_provenance_gate(mod, tmp_path, capsys, heading) -> None:
    source = f"# T\n\n## C\n\n{heading}\n\nno table\n"
    code, err = _refused(mod, tmp_path, capsys, source)
    assert code == 2 and err.strip().endswith("Overall architecture")


def test_every_sources_table_is_validated_not_only_the_last(mod, tmp_path, capsys) -> None:
    bad = f"Sources checked:\n\n{TABLE_HEAD}| q | q | guessed | y |\n\nMore.\n\n{SOURCES}"
    code, err = _refused(mod, tmp_path, capsys, report(overall=bad))
    assert code == 2 and "evidence class" in err


def test_mermaid_fence_with_a_trailing_info_string_keeps_its_label(mod, tmp_path, capsys) -> None:
    text = page(
        tmp_path.resolve(), report(extra="```mermaid {title}\nA --> B\n```\n"), mod, capsys
    )
    assert "Diagram source (not rendered)" in text and "A --&gt; B" in text


def test_links_with_bidi_or_format_characters_render_as_text(mod, tmp_path, capsys) -> None:
    extra = (
        "[evil\u202etxt](https://example.com) [ok](https://exa\u200bmple.com) "
        "[a\u061cb](https://x.example) [c](https://y.example\u061c)\n"
    )
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    assert content_hrefs(tree(text)) == []


def test_existing_output_over_the_cap_is_refused(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    effort = tmp_path / "effort"
    effort.mkdir()
    (effort / "assessment.md").write_text(report(), encoding="utf-8")
    (effort / "assessment.html").write_bytes(b"x" * (mod.MAX_EXISTING_OUTPUT_BYTES + 1))
    assert mod.main([str(effort)]) == 3
    _only_fixed_tokens(*capsys.readouterr())


def test_hostile_directory_name_never_reaches_stdout_or_stderr(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    marker = "SECRET-MARKER-42"
    (tmp_path / marker).mkdir()
    assert mod.main([str(tmp_path / marker)]) == 3  # no assessment.md
    out, err = capsys.readouterr()
    assert marker not in out + err
    _only_fixed_tokens(out, err)
    Path(tmp_path / (marker + "-link")).symlink_to(tmp_path / marker)
    assert mod.main([str(tmp_path / (marker + "-link"))]) == 3
    out, err = capsys.readouterr()
    assert marker not in out + err


@pytest.mark.parametrize(
    "hostile",
    [
        "# a" + " " * 300_000 + "b\n",
        "[" * 300_000 + "\n",
        "[a](" * 60_000 + "\n",
        "| a |\n| --- |\n" + " " * 300_000,
        "|a\n---" + " " * 300_000 + "x\n",
        "## a\n" * 30_000,
        "`" * 300_000 + "\n",
        "**a " * 60_000 + "\n",
    ],
    ids=[
        "heading-spaces",
        "unclosed-brackets",
        "unclosed-links",
        "separator-header-spaces",
        "separator-spaces",
        "repeated-headings",
        "backticks",
        "unclosed-bold",
    ],
)
def test_parsing_stays_linear_on_hostile_input(mod, hostile) -> None:
    started = time.perf_counter()
    mod.render(hostile, "e", "2026-01-01")
    assert time.perf_counter() - started < 3.0


# ---- round-two review repairs ------------------------------------------------------


def test_table_under_a_child_heading_is_validated_and_shaded(mod, tmp_path, capsys) -> None:
    source = (
        "# T\n\n## Current\n\n### Overall architecture\n\ntext\n\n#### Detail\n\nmore\n\n"
        f"Sources checked:\n\n{TABLE_HEAD}| a | b | observed | c |\n"
    )
    parsed = tree(page(tmp_path.resolve(), source, mod, capsys))
    assert "ev-observed" in class_tokens(parsed)


def test_second_level_one_heading_ends_the_charter_section(mod, tmp_path, capsys) -> None:
    source = report().replace(
        "## Conceptual current state",
        "# Appendix\n\nCheckpoints: confirmed\n\n## Conceptual current state",
        1,
    )
    text = page(tmp_path.resolve(), source, mod, capsys)
    assert not banner_present(text)


def test_non_title_level_one_orientation_heading_is_gated(mod, tmp_path, capsys) -> None:
    code, err = _refused(mod, tmp_path, capsys, "# T\n\n# Overall architecture\n\nno table\n")
    assert code == 2 and err.strip().endswith("Overall architecture")


def test_long_links_and_code_spans_render_as_elements(mod, tmp_path, capsys) -> None:
    target = "https://example.com/" + "a" * 600
    extra = f"[long]({target}) `{'c' * 300}` [wiki](https://example.com/a_(b))\n"
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    hrefs = [v for tag, n, v in tree(text).attrs if tag == "a"]
    assert target in hrefs and "https://example.com/a_(b)" in hrefs
    assert "<code>" + "c" * 300 + "</code>" in text


def test_indented_mermaid_fence_gets_the_diagram_label(mod, tmp_path, capsys) -> None:
    extra = "- Diagram:\n\n  ```mermaid\n  A --> B\n  ```\n"
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    assert "Diagram source (not rendered)" in text


def test_a_page_over_the_output_cap_is_refused_without_writing(
    mod, tmp_path, capsys, monkeypatch
) -> None:
    monkeypatch.setattr(mod, "MAX_EXISTING_OUTPUT_BYTES", 1000)
    tmp_path = tmp_path.resolve()
    code, out, err = run(tmp_path, report(), mod, capsys)
    assert code == 2 and err.strip() == "render_html: refused: rendered page over the size cap"
    assert not (tmp_path / "effort" / "assessment.html").exists()


@pytest.mark.parametrize(
    "hostile",
    [
        "- i\n" + "  a\n" * 500_000,
        "[" * 200_000 + "](" + "\n",
        "[a](" * 60_000 + "\n",
        "[a](http://x/(" * 40_000 + "\n",
        "`a" + "*" * 200_000 + "\n",
        "*a" * 150_000 + "\n",
    ],
    ids=[
        "list-continuations",
        "brackets-then-link",
        "unclosed-links",
        "nested-parens",
        "code-star",
        "stars",
    ],
)
def test_round_two_hostile_shapes_stay_linear(mod, hostile) -> None:
    started = time.perf_counter()
    mod.render(hostile, "e", "2026-01-01")
    assert time.perf_counter() - started < 3.0


# ---- round-three review repairs -----------------------------------------------------


def test_a_fence_inside_a_list_item_cannot_swallow_a_later_orientation_subsection(
    mod, tmp_path, capsys
) -> None:
    source = "# T\n\n- item\n   ```\ncode\n   ```\n\n## Overall architecture\n\nno table\n"
    code, err = _refused(mod, tmp_path, capsys, source)
    assert code == 2 and err.strip().endswith("Overall architecture")


def test_mermaid_fence_attached_to_a_list_item_gets_the_diagram_label(
    mod, tmp_path, capsys
) -> None:
    extra = "- Diagram:\n  ```mermaid\n  A --> B\n  ```\n- next\n"
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    assert "Diagram source (not rendered)" in text and "<li>next</li>" in text


@pytest.mark.parametrize(
    "source",
    [
        f"# T\n\n## Overall architecture\n\nx\n\n### Notes\n\n{SOURCES}",
        f"# T\n\n# Overall architecture\n\nx\n\n## Notes\n\n{SOURCES}",
    ],
    ids=["deeper-child-heading", "level-one-orientation-heading"],
)
def test_one_range_rule_validates_and_shades_the_same_table(mod, tmp_path, capsys, source) -> None:
    parsed = tree(page(tmp_path.resolve(), source, mod, capsys))
    assert "ev-observed" in class_tokens(parsed)


def test_a_later_shallower_heading_ends_the_orientation_range(mod, tmp_path, capsys) -> None:
    source = f"# T\n\n### Overall architecture\n\nx\n\n## Later\n\n{SOURCES}"
    code, err = _refused(mod, tmp_path, capsys, source)
    assert code == 2 and err.strip().endswith("Overall architecture")


def test_only_the_first_heading_block_can_be_the_title(mod) -> None:
    with pytest.raises(mod.Refusal):
        mod.render("## Bottom\n\nx\n\n# Physical architecture\n\nno table\n", "e", "2026-01-01")


def test_unterminated_link_target_stays_under_the_memory_bound(mod) -> None:
    import tracemalloc

    tracemalloc.start()
    try:
        mod.render("[a](" + "b" * 400_000, "e", "2026-01-01")
        peak = tracemalloc.get_traced_memory()[1]
    finally:
        tracemalloc.stop()
    assert peak < 16 * 1024 * 1024


@pytest.mark.parametrize(
    ("source", "anchor"),
    [
        ("[a](https://e.x/a b)", False),
        ("[a](https://e.x/a\u00a0b)", False),
        ("[a\x01b](https://e.x)", False),
        ("[a](https://e.x/\x85)", False),
        ("[a](https://e.x/\u00ad)", False),
        ("[a\U000e0041](https://e.x)", False),
        ("[a](https://e.x/((y)))", False),
        ("[a](https://e.x/(y))", True),
        ("[a](\u00a0https://e.x)", True),
    ],
)
def test_link_exclusions_by_character_class_and_depth(mod, source, anchor) -> None:
    assert ("<a href=" in mod._inline(source)) is anchor


def test_reference_lists_every_exit_two_reason() -> None:
    lines = (SKILL_ROOT / "references" / "html-report.md").read_text(encoding="utf-8").splitlines()
    row = next(line for line in lines if line.startswith("| 2 |"))
    for reason in (
        "wrong argument count",
        "Sources checked",
        "evidence class",
        "2 MiB",
        "not UTF-8",
        "16 MiB",
    ):
        assert reason in row


# ---- round-four review repairs ------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        "# T\n\n- a\n  - b\n    ```mermaid\n    A --> B\n    ```\n",
        "# T\n\n1. a\n   - b\n     ```mermaid\n     A --> B\n     ```\n",
    ],
    ids=["four-spaces", "five-spaces"],
)
def test_deeply_nested_mermaid_fence_renders_as_a_labeled_block(mod, source) -> None:
    out = mod.render(source, "e", "2026-01-01")
    assert "Diagram source (not rendered)" in out and "<pre><code>A --&gt; B" in out


def test_refused_existing_output_is_left_unchanged(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    effort = tmp_path / "effort"
    effort.mkdir()
    (effort / "assessment.md").write_text(report(), encoding="utf-8")
    big = b"x" * (mod.MAX_EXISTING_OUTPUT_BYTES + 1)
    (effort / "assessment.html").write_bytes(big)
    assert mod.main([str(effort)]) == 3
    assert (effort / "assessment.html").read_bytes() == big
    _only_fixed_tokens(*capsys.readouterr())


def test_reference_exit_three_row_names_every_reason() -> None:
    lines = (SKILL_ROOT / "references" / "html-report.md").read_text(encoding="utf-8").splitlines()
    row = next(line for line in lines if line.startswith("| 3 |"))
    for reason in (
        "missing source",
        "non-directory",
        "over 16 MiB",
        "symlink",
        "unexpected error",
        "descriptor walking",
    ):
        assert reason in row


# ---- round-five review repairs --------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    [
        "# T\n\n- a\n\t```mermaid\n\tA --> B\n\t```\n- next\n",
        "# T\n\n- a\n  \t```mermaid\n  \tA --> B\n  \t```\n- next\n",
    ],
    ids=["tab", "spaces-then-tab"],
)
def test_tab_indented_mermaid_fence_under_a_list_item_is_labeled(mod, source) -> None:
    out = mod.render(source, "e", "2026-01-01")
    assert "Diagram source (not rendered)" in out and "<pre><code>A --&gt; B" in out
    assert "<li>next</li>" in out


# ---- style slice: stylesheet assets ----------------------------------------------------

ASSETS = SKILL_ROOT / "scripts" / "report_assets"


def test_style_body_is_base_newline_layout(mod, tmp_path, capsys) -> None:
    expected = (
        (ASSETS / "view-base.css").read_text("utf-8")
        + "\n"
        + (ASSETS / "report.css").read_text("utf-8")
    )
    parsed = tree(page(tmp_path.resolve(), report(), mod, capsys))
    assert parsed.style == expected


def _assets(tmp_path: Path, base: bytes | None, layout: bytes | None) -> Path:
    directory = tmp_path / "assets_root" / "report_assets"
    directory.mkdir(parents=True)
    for name, data in (("view-base.css", base), ("report.css", layout)):
        if data is not None:
            (directory / name).write_bytes(data)
    return directory


@pytest.mark.parametrize(
    ("base", "layout", "token"),
    [
        (None, b"a{}", "stylesheet asset missing"),
        (b"a{}", None, "stylesheet asset missing"),
        (b"x" * (64 * 1024 + 1), b"a{}", "stylesheet asset over the size cap"),
        (b"a{}", b"x" * (64 * 1024 + 1), "stylesheet asset over the size cap"),
        (b"\xff\xfe", b"a{}", "stylesheet asset is not valid UTF-8"),
        (b"a{}", b"/* </STYLE> */", "stylesheet asset holds forbidden text"),
        (b"a{}", b"/* <!-- */", "stylesheet asset holds forbidden text"),
        (b"a{ background: URL(x) }", b"b{}", "stylesheet asset holds forbidden text"),
        (b"a{}", b"@IMPORT 'x';", "stylesheet asset holds forbidden text"),
    ],
    ids=[
        "base-missing",
        "layout-missing",
        "base-large",
        "layout-large",
        "not-utf8",
        "style-close",
        "comment-open",
        "url",
        "import",
    ],
)
def test_an_unsafe_stylesheet_asset_exits_three_without_a_file(
    mod, tmp_path, capsys, monkeypatch, base, layout, token
) -> None:
    tmp_path = tmp_path.resolve()
    monkeypatch.setattr(mod, "ASSET_DIR", _assets(tmp_path, base, layout))
    code, out, err = run(tmp_path, report(), mod, capsys)
    assert code == 3 and err.strip() == f"render_html: failed: {token}"
    assert not (tmp_path / "effort" / "assessment.html").exists()
    _only_fixed_tokens(out, err)


def test_no_stylesheet_asset_holds_a_url_or_import() -> None:
    for name in ("view-base.css", "report.css"):
        text = (ASSETS / name).read_text("utf-8").lower()
        assert "url(" not in text and "@import" not in text


# ---- style slice: document-view markup ------------------------------------------------

FIXTURE = PACK_ROOT / "tests" / "skills" / "architect-assess" / "testdata" / "html-style-sample.md"


def _ids(html_text: str) -> list[str]:
    return re.findall(r' id="([^"]+)"', html_text)


def test_skip_link_comes_first_and_targets_the_main_id(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    body = text[text.index("<body>") :]
    assert body.startswith('<body><a class="skip-link" href="#report">')
    assert '<main id="report">' in text


def test_no_heading_can_take_the_main_id(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(extra="## Report\n\nx\n"), mod, capsys)
    ids = _ids(text)
    assert ids.count("report") == 1 and "report-2" in ids
    assert len(ids) == len(set(ids))


def test_header_holds_the_title_and_the_meta_line(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert (
        '<header class="page-header"><h1 class="page-title">Architecture assessment: demo</h1>'
        in text
    )
    assert re.search(r'</h1><p class="meta">Source: effort/assessment\.md', text)


def test_meta_line_holds_name_date_version_state_and_the_source_tally(
    mod, tmp_path, capsys
) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    meta = re.search(r'<p class="meta">(.*?)</p>', text, re.S).group(1)
    assert "effort/assessment.md" in meta and f"Renderer version {mod.RENDERER_VERSION}" in meta
    assert re.search(r"Generated \d{4}-\d{2}-\d{2} UTC", meta)
    assert re.search(
        r'<span class="mark" data-mark="approved"><span class="mark-g" aria-hidden="true">[^<]*</span> Confirmed</span>',
        meta,
    )
    assert meta.endswith("Sources: 3 observed, 0 inferred, 0 reported, 0 unknown")
    unconfirmed = page(tmp_path.resolve(), report(checkpoints=None), mod, capsys)
    meta = re.search(r'<p class="meta">(.*?)</p>', unconfirmed, re.S).group(1)
    assert re.search(
        r'<span class="mark" data-mark="draft"><span class="mark-g" aria-hidden="true">[^<]*</span> Unconfirmed</span>',
        meta,
    )


def test_the_tally_counts_every_class_across_all_labeled_orientation_tables(
    mod, tmp_path, capsys
) -> None:
    # Three labeled tables (overall, one subsystem, physical) hold 14, 4, and 3 rows; the
    # evidence-coverage table is unlabeled and its observed rows stay out of the count.
    source = FIXTURE.read_text(encoding="utf-8")
    text = page(tmp_path.resolve(), source, mod, capsys)
    assert "Sources: 8 observed, 4 inferred, 4 reported, 5 unknown</p>" in text


def test_the_tally_counts_only_labeled_orientation_tables(mod, tmp_path, capsys) -> None:
    extra = f"Sources checked:\n\n{TABLE_HEAD}| a | b | guessed | c |\n"
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    assert "Sources: 3 observed, 0 inferred, 0 reported, 0 unknown</p>" in text


def test_banner_and_notice_carry_the_family_classes(mod, tmp_path, capsys) -> None:
    tokens = class_tokens(tree(page(tmp_path.resolve(), report(checkpoints=None), mod, capsys)))
    assert {"alert", "banner-unconfirmed", "note", "notice-untrusted"} <= tokens


def _rail(text: str) -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    narrow = re.search(
        r'<details class="key"><summary>(.*?)</summary><ul[^>]*>(.*?)</ul></details>', text, re.S
    )
    wide = re.search(r'<ul class="rail-wide plain">(.*?)</ul>', text, re.S)
    pattern = r'<a class="([^"]*)" href="#([^"]*)">(.*?)</a>'
    return (
        [(c, h, tx) for c, h, tx in re.findall(pattern, narrow.group(2))],
        [(c, h, tx) for c, h, tx in re.findall(pattern, wide.group(1))],
    )


def test_the_contents_nav_holds_a_details_list_and_a_wide_list_of_the_same_links(
    mod, tmp_path, capsys
) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert (
        '<nav class="rail" aria-label="Report sections"><details class="key"><summary>Contents ('
        in text
    )
    narrow, wide = _rail(text)
    assert narrow == wide and narrow
    assert re.search(rf"<summary>Contents \({len(narrow)} sections\)</summary>", text)
    assert all("question-link" in c.split() for c, _, _ in narrow)
    ids = set(_ids(text))
    assert all(href in ids for _, href, _ in narrow)


def test_rail_links_follow_source_order_with_plain_text_and_nesting(mod, tmp_path, capsys) -> None:
    source = (
        "# T\n\n## See [docs](https://x)\n\nx\n\n"
        f"## Overall architecture\n\nx\n\n{SOURCES}\n"
        "## Later `code`\n\n#### Overall architecture\n\ny\n\n"
        f"{SOURCES}"
    )
    text = page(tmp_path.resolve(), source, mod, capsys)
    narrow, _ = _rail(text)
    assert [tx for _, _, tx in narrow] == [
        "See docs",
        "Overall architecture",
        "Later code",
        "Overall architecture",
    ]
    assert [("rail-sub" in c.split()) for c, _, _ in narrow] == [False, False, False, True]
    nav = re.search(r"<nav.*?</nav>", text, re.S).group(0)
    assert nav.count("<a ") == 2 * len(narrow)  # no anchor nests inside a link


def test_sections_carry_their_heading_id_and_hold_their_blocks(mod, tmp_path, capsys) -> None:
    source = "# T\n\nlead text\n\n## One\n\nbody one\n\n# Two\n\n### Sub\n\nbody two\n"
    text = page(tmp_path.resolve(), source, mod, capsys)
    assert (
        '<section class="doc-section"><div class="doc-body"><p>lead text</p></div></section>'
        in text
    )
    assert '<section class="doc-section" id="one"><h2 class="margin-head">One</h2>' in text
    assert '<section class="doc-section" id="two"><h2 class="margin-head">Two</h2>' in text
    assert '<h3 id="sub">Sub</h3>' in text
    assert text.count('<h2 class="margin-head">') == 2
    assert 'id="one"><h2 class="margin-head" id' not in text
    assert text.index("body two") > text.index('id="two"')


def test_no_leading_section_when_nothing_precedes_the_first_heading(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), "# T\n\n## One\n\nx\n", mod, capsys)
    assert 'class="doc-section"><div' not in text


def test_marks_replace_the_cell_class_and_hold_the_cell_text(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert '<td><span class="mark ev-observed">Observed</span></td>' in text
    assert 'td class="ev-' not in text


def test_tables_sit_in_labeled_keyboard_scrollable_regions(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    regions = re.findall(
        r'<div class="table-scroll" role="region" tabindex="0" aria-label="([^"]*)">', text
    )
    assert regions.count("Table: Overall architecture") == 1
    assert "Table: Attention heat map" in regions
    assert text.count("<table>") == len(regions)
    bare = page(tmp_path.resolve(), "| a |\n| --- |\n| 1 |\n", mod, capsys)
    assert 'aria-label="Table">' in bare
    hostile = page(
        tmp_path.resolve(), '# T\n\n## a "b" <i>\n\n| a |\n| --- |\n| 1 |\n', mod, capsys
    )
    assert 'aria-label="Table: a &quot;b&quot; &lt;i&gt;"' in hostile


def test_the_sources_checked_label_has_the_part_head_class(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert '<p class="part-head">Sources checked:</p>' in text


def test_renderer_version_is_two(mod) -> None:
    assert mod.RENDERER_VERSION == "2"


def test_the_fixture_models_a_multi_subsystem_system() -> None:
    src = FIXTURE.read_text(encoding="utf-8")
    subsystems = re.split(
        r"(?m)^#### ", src.split("### Architecture by subsystem")[1].split("### Physical")[0]
    )[1:]
    assert len(subsystems) >= 6
    assert sum(1 for entry in subsystems if "##### " in entry) >= 2
    overall = src.split("### Overall architecture")[1].split("### Architecture by subsystem")[0]
    rows = [r for r in overall.splitlines() if r.startswith("| ") and "| --- |" not in r][1:]
    assert len(rows) >= 12
    assert {
        c for r in rows for c in ("observed", "inferred", "reported", "unknown") if f"| {c} |" in r
    } == {"observed", "inferred", "reported", "unknown"}
    heat = src.split("## Attention heat map")[1].split("###")[0]
    heat_rows = [r for r in heat.splitlines() if r.startswith("| ") and "| --- |" not in r][1:]
    assert len(heat_rows) >= 8
    assert {
        v for r in heat_rows for v in ("low", "medium", "high", "unknown") if f"| {v} |" in r
    } == {"low", "medium", "high", "unknown"}
    assert re.search(r"[^\s|`]{80,}", src)
    assert "Checkpoints: accepted-without-pause" in src
    fences = re.findall(r"```mermaid\n(.*?)```", src, re.S)
    assert len(fences) >= 2 and all(len(f.strip().splitlines()) >= 8 for f in fences)
    assert any(f.startswith("flowchart") for f in fences) and any(
        f.startswith("sequenceDiagram") for f in fences
    )


def test_the_fixture_renders_to_a_complete_document(mod, tmp_path, capsys) -> None:
    tmp_path = tmp_path.resolve()
    effort = tmp_path / "effort"
    effort.mkdir()
    (effort / "assessment.md").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    assert mod.main([str(effort)]) == 0
    text = (effort / "assessment.html").read_text(encoding="utf-8")
    parsed = tree(text)
    assert {
        "alert",
        "banner-unconfirmed",
        "doc-section",
        "margin-head",
        "table-scroll",
    } <= class_tokens(parsed)
    assert text.count("Diagram source (not rendered)") == 2
    ids = _ids(text)
    assert len(ids) == len(set(ids))
    narrow, wide = _rail(text)
    assert narrow == wide and len(narrow) >= 10


# ---- style slice: the layout file ----------------------------------------------------

LAYOUT = ASSETS / "report.css"
BASE = ASSETS / "view-base.css"


def parse_css(css: str) -> list[tuple[tuple[str, ...], str, list[tuple[str, str]]]]:
    """Return (media chain, selector, declarations) for every declaration block."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules, stack, buf = [], [], ""
    for char in css:
        if char == "{":
            stack.append(buf.strip())
            buf = ""
        elif char == "}":
            prelude = stack.pop()
            if buf.strip():
                decls = []
                for part in re.split(r";(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)", buf):
                    if ":" in part:
                        prop, value = part.split(":", 1)
                        decls.append((prop.strip().lower(), value.strip()))
                media = tuple(p for p in stack if p.startswith("@"))
                rules.append((media, prelude, decls))
            buf = ""
        else:
            buf += char
    return rules


def layout_rules():
    return parse_css(LAYOUT.read_text(encoding="utf-8"))


def declared(selector_part: str, prop: str, media: str | None = None) -> list[str]:
    """Values of *prop* in rules whose selector list holds *selector_part* exactly."""
    found = []
    for chain, selector, decls in layout_rules():
        if media is not None and not any(media in m for m in chain):
            continue
        if media is None and chain:
            continue
        if selector_part in [piece.strip() for piece in selector.split(",")]:
            found += [v for p, v in decls if p == prop]
    return found


COLOUR = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|(?<![\w-])(?:rgba?|hsla?|hwb|lab|lch|oklab|oklch|color|color-mix|light-dark)\("
    r"|(?<![\w-])(?:transparent|currentcolor|white|black|red|green|blue|gray|grey|orange|yellow"
    r"|purple|pink|brown|silver|navy|teal|aqua|cyan|magenta)(?![\w-])"
)


def test_layout_file_obeys_the_layout_rules() -> None:
    assert layout_rules()
    for _, selector, decls in layout_rules():
        for prop, value in decls:
            where = f"{selector} {{ {prop}: {value} }}"
            assert not COLOUR.search(value), where
            assert not prop.startswith("--"), where
            assert prop not in {
                "font",
                "font-family",
                "font-weight",
                "box-shadow",
                "scroll-behavior",
            }, where
            assert not prop.startswith("transition"), where
            if prop.startswith("animation"):
                assert prop == "animation" and value == "none !important", where
            if prop == "border-radius":
                assert re.fullmatch(r"var\(--r-\d\)|0", value), where


def test_layout_file_spacing_properties_hold_tokens_only() -> None:
    spacing = re.compile(
        r"^(margin|padding)(-(top|right|bottom|left|inline|block)[\w-]*)?$|^(row-|column-)?gap$"
    )
    for _, selector, decls in layout_rules():
        for prop, value in decls:
            if spacing.match(prop):
                for piece in value.split():
                    assert piece in {"0", "auto"} or re.fullmatch(r"var\(--s-\d\)", piece), (
                        selector,
                        prop,
                        value,
                    )


def test_layout_file_sets_the_document_density_literals() -> None:
    for selector, size, height in (
        (".page-title", "1.75rem", "1.2"),
        (".doc-body h3", "1.3125rem", "1.3"),
        (".doc-body", "1.0625rem", "1.6"),
        (".meta", "0.875rem", "1.5"),
        (".margin-head", "0.75rem", "1.3"),
        (".part-head", "0.75rem", "1.3"),
    ):
        assert declared(selector, "font-size") == [size], selector
        assert declared(selector, "line-height") == [height], selector
    assert declared(".margin-head", "text-transform") == ["uppercase"]
    assert declared(".part-head", "text-transform") == ["uppercase"]


def test_layout_file_arranges_the_pieces_the_markup_depends_on() -> None:
    assert declared(".page-title::before", "display")
    assert declared(".mark", "padding")
    assert declared(".rail-sub", "padding-left")
    assert declared("table", "border-collapse") == ["collapse"]
    assert declared("pre", "overflow") == ["auto"]
    assert declared("pre", "width") == ["max-content"] and declared("pre", "min-width") == ["100%"]
    assert declared(".table-scroll", "overflow-x") == ["auto"]
    assert declared(".page-title", "overflow-wrap") == ["anywhere"]
    assert declared(".notice-untrusted", "border-width") and declared(
        ".notice-untrusted", "padding"
    )


@pytest.mark.parametrize(
    ("name", "glyph"),
    [
        ("observed", "\\25AE\\25AE\\25AE"),
        ("inferred", "\\25AE\\25AE\\25AF"),
        ("reported", "\\25AE\\25AF\\25AF"),
        ("unknown", "\\25AF\\25AF\\25AF"),
    ],
)
def test_each_evidence_class_has_its_own_silent_glyph_and_a_neutral_pill(name, glyph) -> None:
    content = declared(f".ev-{name}::before", "content")
    assert content == ["none", f'"{glyph}" / ""'], content
    assert declared(f".ev-{name}", "background") == ["var(--c-bg)"]
    assert declared(f".ev-{name}", "border-color") == ["var(--c-rule-strong)"]


def test_provenance_and_heat_rules_use_no_state_colour_roles() -> None:
    for _, selector, decls in layout_rules():
        if "ev-" in selector or "heat-" in selector:
            for prop, value in decls:
                assert not re.search(r"--c-(bad|warn|ok|active|accent)", value), (selector, prop)
    glyphs = {
        declared(f".ev-{n}::before", "content")[-1]
        for n in ("observed", "inferred", "reported", "unknown")
    }
    assert len(glyphs) == 4


def test_heat_ramp_is_as_specified_and_distinct() -> None:
    expected = {
        "low": ("var(--c-bg)", "\\2582"),
        "medium": ("var(--c-raised)", "\\2584"),
        "high": ("var(--c-rule)", "\\2586"),
        "unknown": ("var(--c-bg)", "?"),
    }
    glyphs = set()
    for level, (background, glyph) in expected.items():
        assert declared(f".heat-{level}", "background") == [background]
        content = declared(f".heat-{level}::before", "content")
        assert content[0] == "none" and content[-1] == f'"{glyph}" / ""'
        glyphs.add(glyph)
    assert len(glyphs) == 4
    assert declared(".heat-unknown", "font-style") == ["italic"]
    assert not declared(".heat-low", "font-style")


def test_heat_cells_keep_glyph_and_word_on_one_line() -> None:
    for level in ("low", "medium", "high", "unknown"):
        assert declared(f".heat-{level}", "white-space") == ["nowrap"], level


def test_no_rule_for_a_heat_class_declares_a_border_or_outline() -> None:
    seen = 0
    for _, selector, decls in layout_rules():
        if "heat-" in selector:
            seen += 1
            for prop, _value in decls:
                assert not prop.startswith(("border", "outline")), (selector, prop)
    assert seen >= 8


def test_heat_glyphs_match_no_evidence_or_state_glyph() -> None:
    heat = set()
    for level in ("low", "medium", "high", "unknown"):
        value = declared(f".heat-{level}::before", "content")[-1]
        literal = re.fullmatch(r'"(.+)" / ""', value).group(1)
        heat.add(re.sub(r"\\([0-9a-fA-F]{1,6})", lambda m: chr(int(m.group(1), 16)), literal))
    taken = set("\u25ae\u25af\u25cf\u25b6\u25c6\u25c7\u25a0\u2715\u25b3\u2713")
    assert len(heat) == 4 and not heat & taken


def _tokens() -> dict[str, dict[str, str]]:
    themes = {"light": {}, "dark": {}}
    for media, selector, decls in parse_css(BASE.read_text(encoding="utf-8")):
        if selector.strip() == ":root":
            theme = "dark" if any("prefers-color-scheme: dark" in m for m in media) else "light"
            for prop, value in decls:
                if prop.startswith("--c-"):
                    themes[theme][prop] = value
    themes["dark"] = {**themes["light"], **themes["dark"]}
    return themes


def _luminance(hex_colour: str) -> float:
    channels = [int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(a: str, b: str) -> float:
    high, low = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_heat_cells_keep_text_contrast_in_both_themes(theme) -> None:
    tokens = _tokens()[theme]
    for level in ("low", "medium", "high", "unknown"):
        background = declared(f".heat-{level}", "background")[0]
        role = re.fullmatch(r"var\((--c-[\w-]+)\)", background).group(1)
        assert _contrast(tokens["--c-text"], tokens[role]) >= 4.5, (level, theme)


def test_contrast_check_can_fail() -> None:
    assert _contrast("#777777", "#888888") < 4.5
    assert _contrast("#000000", "#ffffff") > 20


def test_rail_and_skip_links_reach_the_target_floor_and_the_skip_link_shows_on_focus() -> None:
    for selector in (".question-link", ".skip-link"):
        assert declared(selector, "display") == ["inline-flex"], selector
        assert declared(selector, "align-items") == ["center"], selector
        assert declared(selector, "min-height") == ["var(--target)"], selector
    assert declared(".skip-link:focus", "position") == ["static"]
    assert declared(".skip-link:focus", "clip-path") == ["none"]
    assert declared(".skip-link:focus", "overflow") == ["visible"]


def test_tracks_breakpoints_and_the_contents_switch() -> None:
    tracks = declared(".doc-section", "grid-template-columns", "min-width: 64rem")
    assert tracks == ["10rem minmax(0, 68ch) minmax(0, 1fr)"]
    assert declared(".doc-section", "grid-template-columns") == []
    assert declared(".doc-body > .table-scroll", "grid-column", "min-width: 64rem") == ["1 / -1"]
    assert declared(".doc-body > .source-scroll", "grid-column", "min-width: 64rem") == ["2 / -1"]
    assert declared("th", "overflow-wrap") == [] and declared("td", "overflow-wrap") == []
    assert declared("body", "grid-template-columns", "min-width: 64rem") == [
        "minmax(0, 1fr) 16rem"
    ]
    assert declared(".rail-wide", "display") == ["none"]
    assert declared(".rail-wide", "display", "min-width: 64rem") == ["block"]
    assert declared(".rail details", "display", "min-width: 64rem") == ["none"]


def test_contents_rail_is_sticky_and_scrolls_from_64rem() -> None:
    assert declared(".rail", "position", "min-width: 64rem") == ["sticky"]
    assert declared(".rail", "max-height", "min-width: 64rem")
    assert declared(".rail", "overflow-y", "min-width: 64rem") == ["auto"]
    assert declared(".rail", "grid-column", "min-width: 64rem") == ["2"]


def test_target_bar_and_print_block() -> None:
    assert declared(".doc-section:target", "border-left-width") == ["3px"]
    assert declared(".doc-section:target", "border-left-style") == ["solid"]
    assert declared(".doc-section:target", "border-left-color") == ["var(--c-accent)"]
    for hidden in (".rail", ".skip-link", ".rail details"):
        assert declared(hidden, "display", "print") == ["none"], hidden
    assert declared(".table-scroll", "overflow", "print") == ["visible"]
    assert declared(".source-scroll", "overflow", "print") == ["visible"]


def test_focused_skip_link_stays_small_in_the_page_grid() -> None:
    assert declared(".skip-link:focus", "grid-column", "min-width: 64rem") == ["1 / -1"]
    assert declared(".skip-link:focus", "justify-self", "min-width: 64rem") == ["start"]
    assert declared(".skip-link:focus", "align-self", "min-width: 64rem") == ["start"]


def test_source_blocks_sit_in_keyboard_scrollable_regions(mod, tmp_path, capsys) -> None:
    extra = "```\nplain block\n```\n\n```mermaid\nA --> B\n```\n"
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    regions = re.findall(
        r'<div class="source-scroll" role="region" tabindex="0" aria-label="([^"]*)">', text
    )
    assert regions == ["Source: Findings", "Source: Findings"]
    assert text.count("<pre>") == len(regions)
    assert declared(".source-scroll", "overflow-x") == ["auto"]


def test_a_source_block_before_any_heading_is_labelled_plain_source(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), "```\nplain\n```\n\n" + report(), mod, capsys)
    assert 'role="region" tabindex="0" aria-label="Source">' in text


def test_print_uses_light_system_colours_one_column_and_wrapped_tables() -> None:
    assert declared(":root", "color-scheme", "print") == ["light"]
    for selector in ("body", "main", ".doc-section", ".page-header"):
        assert declared(selector, "display", "print") == ["block"], selector
        assert declared(selector, "color", "print") == ["CanvasText"], selector
        assert declared(selector, "background", "print") == ["Canvas"], selector
    for level in ("low", "medium", "high", "unknown"):
        assert declared(f".heat-{level}", "white-space", "print") == ["normal"], level
    assert declared("table", "table-layout", "print") == ["fixed"]
    assert declared("table", "overflow-wrap", "print") == ["anywhere"]


def test_print_lets_source_blocks_wrap_and_keeps_rows_together() -> None:
    assert declared("pre", "overflow", "print") == ["visible"]
    assert declared("pre", "white-space", "print") == ["pre-wrap"]
    assert declared("tr", "break-inside", "print") == ["avoid"]


def test_contents_control_meets_the_target_floor_and_the_page_is_centred_when_wide() -> None:
    assert declared(".rail summary", "min-height") == ["var(--target)"]
    assert declared(".rail summary", "gap") == ["var(--s-2)"]
    assert declared("body", "max-width", "min-width: 100rem") == ["110rem"]
    assert declared("body", "margin-left", "min-width: 100rem") == ["auto"]


# ---- diagrams mode ---------------------------------------------------------------

USAGE = "render_html: usage: render_html.py <effort-dir> [--diagrams]"
SCRIPT_FILE = Path(__file__).resolve().parents[3] / (
    ".apm/skills/architect-assess/scripts/report_assets/diagrams.js"
)
FLOW = "flowchart LR\n  A --> B"


def fence(body: str = FLOW) -> str:
    return f"```mermaid\n{body}\n```\n"


def run_diagrams(tmp: Path, text: str, mod: ModuleType, capsys, flag: bool = True):
    effort = tmp / "effort"
    effort.mkdir(exist_ok=True)
    (effort / "assessment.md").write_text(text, encoding="utf-8")
    code = mod.main([str(effort), "--diagrams"] if flag else [str(effort)])
    captured = capsys.readouterr()
    return code, captured.err, (effort / "assessment.html")


def diagrams_page(tmp: Path, text: str, mod: ModuleType, capsys) -> str:
    code, err, out = run_diagrams(tmp.resolve(), text, mod, capsys)
    assert code == 0, err
    return out.read_text(encoding="utf-8")


def labels(text: str) -> list[tuple[str, str]]:
    return re.findall(r'<div class="(diagram[^"]*)"><p class="diagram-label">([^<]*)</p>', text)


def test_flag_and_no_flag_both_exit_zero(mod, tmp_path, capsys) -> None:
    for flag in (False, True):
        code, err, _ = run_diagrams(tmp_path.resolve(), report(), mod, capsys, flag)
        assert code == 0 and err == ""


def test_wrong_arguments_exit_two_with_the_usage_token(mod, capsys) -> None:
    for argv in ([], ["a", "b"], ["a", "--diagrams", "x"], ["a", "--diagram"]):
        assert mod.main(argv) == 2
        assert capsys.readouterr().err.strip() == USAGE


def test_a_first_argument_of_the_flag_is_just_a_path(mod, capsys) -> None:
    assert mod.main(["--diagrams"]) == 3
    assert capsys.readouterr().err.strip() == "render_html: refused: unsafe or missing path"


def test_default_page_has_no_script_or_src_and_the_stated_policy(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(extra=fence()), mod, capsys)
    parsed = tree(text)
    assert "script" not in parsed.elements
    assert not [a for a in parsed.attrs if a[1] == "src"]
    policy = re.search(r'Content-Security-Policy" content="([^"]*)"', text).group(1)
    digest = base64.b64encode(hashlib.sha256(parsed.style.encode()).digest()).decode()
    assert policy == (
        f"default-src 'none'; style-src 'sha256-{digest}'; base-uri 'none'; form-action 'none'"
    )


def test_default_run_never_reads_the_script(mod, tmp_path, capsys, monkeypatch) -> None:
    baseline = page(tmp_path.resolve(), report(extra=fence()), mod, capsys)
    monkeypatch.setattr(mod, "SCRIPT_NAME", "absent.js")
    monkeypatch.setattr(mod, "load_script", lambda helper: (_ for _ in ()).throw(AssertionError))
    assert page(tmp_path.resolve(), report(extra=fence()), mod, capsys) == baseline


def test_diagrams_page_ends_with_the_two_pinned_scripts(mod, tmp_path, capsys) -> None:
    text = diagrams_page(tmp_path, report(extra=fence()), mod, capsys)
    script = SCRIPT_FILE.read_text(encoding="utf-8")
    tail = (
        f'</main><script src="{mod.MERMAID_URL}" integrity="{mod.MERMAID_SRI}" '
        'crossorigin="anonymous" referrerpolicy="no-referrer" defer></script>'
        f"<script>{script}</script></body></html>\n"
    )
    assert text.endswith(tail)
    assert tree(text).order[-2:] == ["script", "script"]
    assert (
        f"https://cdn.jsdelivr.net/npm/mermaid@{mod.MERMAID_VERSION}/dist/mermaid.min.js"
    ) == mod.MERMAID_URL


def test_diagrams_policy_adds_only_the_script_sources(mod, tmp_path, capsys) -> None:
    text = diagrams_page(tmp_path, report(extra=fence()), mod, capsys)
    script = SCRIPT_FILE.read_text(encoding="utf-8")
    style = tree(text).style
    s_hash = base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()
    c_hash = base64.b64encode(hashlib.sha256(style.encode()).digest()).decode()
    policy = re.search(r'Content-Security-Policy" content="([^"]*)"', text).group(1)
    assert policy == (
        f"default-src 'none'; script-src 'sha256-{s_hash}' {mod.MERMAID_URL}; "
        f"style-src 'sha256-{c_hash}'; base-uri 'none'; form-action 'none'"
    )


def test_diagrams_note_follows_the_untrusted_notice(mod, tmp_path, capsys) -> None:
    text = diagrams_page(tmp_path, report(), mod, capsys)
    note = (
        f'<div class="note notice-diagrams">Diagrams are drawn by Mermaid {mod.MERMAID_VERSION}, '
        "loaded from cdn.jsdelivr.net. Opening this report sends your IP address, the time, "
        "and your browser details to that host, and the report's web address if it is served "
        "from a web host; no report text is sent.</div>"
    )
    assert f"not redacted</div>\n{note}" in text
    assert "notice-diagrams" not in class_tokens(
        tree(page(tmp_path.resolve(), report(), mod, capsys))
    )


def test_script_element_and_attributes_exist_only_in_diagrams_output(
    mod, tmp_path, capsys
) -> None:
    corpus = fence() + fence(REFUSED["click"]) + fence(REFUSED["frontmatter"])
    parsed = tree(diagrams_page(tmp_path, report(extra=corpus), mod, capsys))
    assert parsed.elements.count("script") == 2
    script_attrs = {name for tag, name, _ in parsed.attrs if tag == "script"}
    assert script_attrs == {"src", "integrity", "crossorigin", "referrerpolicy", "defer"}
    default = tree(page(tmp_path.resolve(), report(extra=corpus), mod, capsys))
    assert set(parsed.elements) - set(default.elements) == {"script"}
    assert set(parsed.elements) <= ALLOWED_ELEMENTS | {"script"}
    for tag, name, _ in parsed.attrs:
        if tag != "script":
            assert (tag, name) in ALLOWED_TAG_ATTRS or name in GLOBAL_ATTRS, (tag, name)


DRAWABLE = [
    FLOW,
    "graph TD\n  A --> B",
    "  \n\t\nsequenceDiagram\n  A->>B: hi",
    "classDiagram\n  A <|-- B",
    "stateDiagram-v2\n  [*] --> A",
    "erDiagram\n  A ||--o{ B : has",
    "  flowchart LR\n  A --> B",
    "flowchart LR\n  A --> B\n  linkStyle 0 stroke:red",
    "flowchart LR\n  A --> B\n  linkStyle default stroke:red",
]
REFUSED = {
    "node named like link": "flowchart LR\n linkerd --> api",
    "node named like click": "flowchart LR\n clicker --> api",
    "linkStyle lookalike": "flowchart LR\n linkStyles 0 stroke:red",
    "frontmatter": "---\ntitle: x\n---\nflowchart LR\n A --> B",
    "no keyword": 'pie title x\n  "a": 1',
    "wrong case": "Flowchart LR\n A --> B",
    "directive": "flowchart LR\n%%{init: {}}%%\n A --> B",
    "nul-split directive": "flowchart LR\n%%\x00{init: {}}%%\n A --> B",
    "nul-split click": 'flowchart LR\n A --> B\ncl\x00ick A href "x"',
    "bom first line": "\ufeffflowchart LR\n A --> B",
    "bom before click": 'flowchart LR\n A --> B;\ufeffclick A href "x"',
    "nbsp first line": "\u00a0flowchart LR\n A --> B",
    "nbsp click": 'flowchart LR\n A --> B;\u00a0click A href "x"',
    "ideographic link": "flowchart LR\n A --> B;\u3000link A: x",
    "click": 'flowchart LR\n A --> B\n click A href "x"',
    "semicolon click": 'flowchart LR\n A --> B; click A href "x"',
    "upper click": "flowchart LR\n A --> B\nCLICK A call f()",
    "link": 'classDiagram\n A <|-- B\n link A "https://x"',
    "links": 'sequenceDiagram\n A->>B: x\n links A: {"a": "b"}',
    "callback": 'classDiagram\n A <|-- B\n callback A "f"',
    "carriage return": "flowchart LR\r\n A --> B",
    "control": "flowchart LR\n A --> B\x07",
    "oversize": "flowchart LR\n" + " A --> B\n" * 6000,
}


def test_eligibility_accepts_each_allowlisted_diagram(mod) -> None:
    for text in DRAWABLE:
        assert mod.diagram_drawable(text), text


def test_eligibility_refuses_each_hostile_or_unlisted_fence(mod) -> None:
    for name, text in REFUSED.items():
        assert not mod.diagram_drawable(text), name


def test_eligibility_size_boundary_is_in_utf8_bytes(mod) -> None:
    base = "flowchart LR\n"
    fits = base + "A" * (50_000 - len(base))
    assert mod.diagram_drawable(fits)
    assert not mod.diagram_drawable(fits + "A")
    wide = base + "\u00e9" * ((50_000 - len(base)) // 2 + 1)
    assert not mod.diagram_drawable(wide)


def test_labels_and_markers_by_state(mod, tmp_path, capsys) -> None:
    extra = fence() + fence(REFUSED["click"])
    text = diagrams_page(tmp_path, report(extra=extra), mod, capsys)
    assert labels(text) == [
        ("diagram diagram-drawn", "Diagram source (not drawn yet)"),
        ("diagram", "Diagram source (not drawn: unsafe)"),
    ]
    plain = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    assert labels(plain) == [("diagram", "Diagram source (not rendered)")] * 2


def test_the_first_twenty_passing_fences_are_drawn_and_refusals_are_not_counted(
    mod, tmp_path, capsys
) -> None:
    extra = "".join(fence(REFUSED["click"]) for _ in range(3)) + fence() * 22
    text = diagrams_page(tmp_path, report(extra=extra), mod, capsys)
    found = labels(text)
    assert [label for _, label in found[:3]] == ["Diagram source (not drawn: unsafe)"] * 3
    assert [label for _, label in found[3:23]] == ["Diagram source (not drawn yet)"] * 20
    assert [label for _, label in found[23:]] == ["Diagram source (not drawn: limit)"] * 2
    assert sum(1 for css, _ in found if css == "diagram diagram-drawn") == 20


def test_the_text_the_rules_read_equals_the_emitted_code_text(mod, tmp_path, capsys) -> None:
    body = 'flowchart LR\n  A["x &amp; y #35; <b>"] --> B'
    text = diagrams_page(tmp_path, report(extra=fence(body)), mod, capsys)
    emitted = re.search(r"<pre><code>(.*?)</code></pre>", text, re.S).group(1)
    assert html.unescape(emitted) == body
    assert mod.diagram_drawable(body)


def test_fence_text_stays_escaped_in_both_modes(mod, tmp_path, capsys) -> None:
    body = 'flowchart LR\n  A["<img src=x onerror=alert(1)>"] --> B'
    for text in (
        page(tmp_path.resolve(), report(extra=fence(body)), mod, capsys),
        diagrams_page(tmp_path, report(extra=fence(body)), mod, capsys),
    ):
        assert "<img" not in text
        assert "&lt;img src=x onerror=alert(1)&gt;" in text


@pytest.fixture
def asset_dir(mod, tmp_path, monkeypatch) -> Path:
    """A copy of the asset directory the renderer reads, safe to damage."""
    root = tmp_path / "scripts"
    copy = root / "report_assets"
    copy.mkdir(parents=True)
    for source in mod.ASSET_DIR.iterdir():
        (copy / source.name).write_bytes(source.read_bytes())
    monkeypatch.setattr(mod, "ASSET_DIR", copy)
    return copy


def _mk(path: Path) -> Path:
    path.mkdir()
    return path.resolve()


def _script_refused(mod, tmp_path, capsys, name: str) -> tuple[int, str]:
    code, err, _ = run_diagrams(_mk(tmp_path / name), report(), mod, capsys)
    return code, err.strip()


def test_script_asset_refusals_have_distinct_tokens(mod, tmp_path, capsys, asset_dir) -> None:
    target = asset_dir / "diagrams.js"
    unsafe = "render_html: failed: script asset missing or unsafe"
    target.unlink()
    assert _script_refused(mod, tmp_path, capsys, "missing") == (3, unsafe)
    real = tmp_path / "real.js"
    real.write_text("/* ok */\n", encoding="utf-8")
    target.symlink_to(real)
    assert _script_refused(mod, tmp_path, capsys, "symlink") == (3, unsafe)
    target.unlink()
    target.write_bytes(b"/" + b"*" * 70_000)
    assert _script_refused(mod, tmp_path, capsys, "large") == (
        3,
        "render_html: failed: script asset over the size cap",
    )
    target.write_bytes(b"\xff\xfe not utf8")
    assert _script_refused(mod, tmp_path, capsys, "bytes") == (
        3,
        "render_html: failed: script asset unreadable",
    )


@pytest.mark.parametrize("text", ["x </SCRIPT> y", "x <!-- y", "line\r\nline"])
def test_script_asset_with_forbidden_text_is_script_refused(
    mod, tmp_path, capsys, asset_dir, text
) -> None:
    (asset_dir / "diagrams.js").write_bytes(text.encode("utf-8"))
    code, err, _ = run_diagrams(_mk(tmp_path / "w"), report(), mod, capsys)
    assert (code, err.strip()) == (3, "render_html: failed: script asset holds forbidden text")


def test_non_regular_script_asset_is_script_refused(mod, tmp_path, capsys, asset_dir) -> None:
    target = asset_dir / "diagrams.js"
    target.unlink()
    target.mkdir()
    code, err, _ = run_diagrams(_mk(tmp_path / "w"), report(), mod, capsys)
    assert (code, err.strip()) == (3, "render_html: failed: script asset missing or unsafe")


def test_caps_hold_with_the_flag(mod, tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.setattr(mod, "MAX_EXISTING_OUTPUT_BYTES", 1000)
    code, err, _ = run_diagrams(_mk(tmp_path / "w1"), report(), mod, capsys)
    assert (code, err.strip()) == (2, "render_html: refused: rendered page over the size cap")
    monkeypatch.undo()
    monkeypatch.setattr(mod, "MAX_SOURCE_BYTES", 100)
    code, err, _ = run_diagrams(_mk(tmp_path / "w2"), report(), mod, capsys)
    assert (code, err.strip()) == (2, "render_html: refused: source over the size cap")


# ---- the drawing script ------------------------------------------------------------


def _script_text() -> str:
    return SCRIPT_FILE.read_text(encoding="utf-8")


def test_script_initializes_mermaid_exactly_once_with_the_fixed_options() -> None:
    text = _script_text()
    assert text.count("mermaid.initialize(") == 1
    body = re.search(r"mermaid\.initialize\(\{(.*?)\}\)", text, re.S).group(1)
    assert "..." not in body
    pairs = dict(re.findall(r"(\w+):\s*([^,\n]+)", body))
    assert pairs == {
        "startOnLoad": "false",
        "securityLevel": "'strict'",
        "suppressErrorRendering": "true",
        "htmlLabels": "false",
        "maxTextSize": "50000",
        "maxEdges": "500",
        "theme": "'neutral'",
    }


def test_script_draws_only_marked_blocks_and_reads_the_code_text_content() -> None:
    text = _script_text()
    assert text.count("querySelectorAll(") == 1 and ".diagram.diagram-drawn" in text
    assert "window.mermaid.render(id, code.textContent)" in text
    assert "matchMedia" not in text


def test_script_render_ids_cannot_equal_a_heading_slug(mod) -> None:
    assert "var id = 'mmd_d' + (n + 1);" in _script_text()
    render_ids = {f"mmd_d{n}" for n in range(1, 30)} | {f"dmmd_d{n}" for n in range(1, 30)}
    for heading in ("mmd_d1", "dmmd_d1", "Mmd_D1", "mmd-d1", "Mmd D1"):
        slug = mod._slug(heading, set(), {})
        assert "_" not in slug and slug not in render_ids, heading


@pytest.mark.parametrize(
    "pattern",
    [
        r"\.innerHTML",
        r"insertAdjacentHTML",
        r"outerHTML",
        r"\beval\s*\(",
        r"\bFunction\s*\(",
        r"new\s+Function",
        r"document\s*\.\s*write",
        r"setTimeout\s*\(",
        r"setInterval\s*\(",
    ],
)
def test_script_has_no_html_string_sink_or_dynamic_code(pattern) -> None:
    assert not re.search(pattern, _script_text())


NODE_TABLE = r"""
const s = require(process.argv[1]);
const rule = (names) => ({ style: { length: names.length, ...Object.fromEntries(names.map((n, i) => [i, n])) } });
const out = {
  list: [
    s.selectorList('#a .x, #a .y'),
    s.selectorList('#a [x=")"], .notice'),
    s.selectorList('#a .b\\(, body'),
    s.selectorList('#a :is(.x, .y), #a .z'),
    s.selectorList('#a "unterminated'),
    s.selectorList('#a [x'),
    s.selectorList('#a .x\\'),
  ],
  confined: [
    s.selectorsConfined(['#mmd_d1'], 'mmd_d1'),
    s.selectorsConfined(['#mmd_d1 .a'], 'mmd_d1'),
    s.selectorsConfined(['#mmd_d1 > g'], 'mmd_d1'),
    s.selectorsConfined(['#mmd_d10 .a'], 'mmd_d1'),
    s.selectorsConfined(['#mmd_d1 ~ *'], 'mmd_d1'),
    s.selectorsConfined(['#mmd_d1 + g'], 'mmd_d1'),
    s.selectorsConfined(['.notice'], 'mmd_d1'),
    s.selectorsConfined(['#mmd_d1 .a', 'body'], 'mmd_d1'),
    s.selectorsConfined(['#mmd_d1:not(.x) ~ g'], 'mmd_d1'),
  ],
  root: [
    s.targetsTheRoot(['#mmd_d1'], 'mmd_d1'),
    s.targetsTheRoot(['#mmd_d1 svg'], 'mmd_d1'),
    s.targetsTheRoot(['#mmd_d1 > svg'], 'mmd_d1'),
    s.targetsTheRoot(['#mmd_d1 .a'], 'mmd_d1'),
    s.targetsTheRoot(['#mmd_d1 g'], 'mmd_d1'),
    s.targetsTheRoot(['#mmd_d1 div.tip'], 'mmd_d1'),
  ],
  owns: ['mmd_d1', 'mmd_d1-x', 'mmd_d1_x', 'mmd_d10', 'mmd_d10-x', 'actor1', 'xmmd_d1'].map((v) => s.ownsId(v, 'mmd_d1')),
  refs: ['url(#a)', 'url("#a")', "url('#a')", 'url(https://x/y)', 'url( #a )', 'fill: red', 'url(#a) url(x.png)'].map(s.referencesOnlyTheDocument),
  attrs: [
    s.attributeRefused('href', '#a'), s.attributeRefused('xlink:href', '#a'), s.attributeRefused('x:href', '#a'),
    s.attributeRefused('src', 'a'), s.attributeRefused('onclick', 'f()'), s.attributeRefused('xlink:onload', 'f()'),
    s.attributeRefused('fill', 'url(https://x)'), s.attributeRefused('fill', 'url(#a)'), s.attributeRefused('d', 'M0 0'),
  ],
  banned: ['position', 'inset', 'top', 'right', 'bottom', 'left', 'float', 'transform', 'z-index', 'translate', 'rotate', 'scale',
    'margin', 'margin-top', 'margin-inline-start', 'margin-block-end', 'inset-inline-start', 'inset-block', 'offset', 'offset-anchor',
    'offset-rotate', 'fill', 'stroke', 'font-size', 'text-anchor', 'marginal', 'stroke-dashoffset', 'opacity'].map(s.propertyBanned),
  rules: [
    s.propertiesAllowed(rule(['fill', 'stroke'])),
    s.propertiesAllowed(rule(['margin-inline-start'])),
    s.propertiesAllowed({}),
  ],
};
console.log(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def node_table() -> dict:
    import json
    import shutil
    import subprocess

    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    done = subprocess.run(  # noqa: S603 - fixed argv, reads only the shipped script
        [node, "-e", NODE_TABLE, str(SCRIPT_FILE)], capture_output=True, text=True, timeout=60
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_script_selector_splitting_treats_quotes_and_escapes_as_data(node_table) -> None:
    assert node_table["list"] == [
        ["#a .x", "#a .y"],
        ['#a [x=")"]', ".notice"],
        ["#a .b\\(", "body"],
        ["#a :is(.x, .y)", "#a .z"],
        None,
        None,
        ["#a .x\\"],
    ]


def test_script_confines_selectors_to_the_drawing_by_exact_id(node_table) -> None:
    assert node_table["confined"] == [True, True, True, False, False, False, False, False, False]


def test_script_applies_the_positioning_ban_to_the_root_rule_only(node_table) -> None:
    assert node_table["root"] == [True, True, True, False, False, False]


def test_script_owns_an_id_only_by_exact_match_or_a_separator(node_table) -> None:
    assert node_table["owns"] == [True, True, True, False, False, False, False]


def test_script_allows_only_fragment_references(node_table) -> None:
    assert node_table["refs"] == [True, True, True, False, True, True, False]


def test_script_refuses_links_loaders_and_handlers_by_local_name(node_table) -> None:
    assert node_table["attrs"] == [True, True, True, True, True, True, True, False, False]


def test_script_bans_every_movement_and_margin_family_property(node_table) -> None:
    banned = [True] * 21 + [False] * 7
    assert node_table["banned"] == banned
    assert node_table["rules"] == [True, False, True]


def test_drawn_diagrams_scroll_inside_their_own_region() -> None:
    assert declared(".diagram-render", "overflow-x") == ["auto"]
    assert declared(".diagram-render", "max-width") == ["100%"]
    assert declared(".diagram-render svg", "min-width") == ["32rem"]
    assert declared(".diagram-render svg", "height") == ["auto"]


def test_script_keyframe_names_are_a_fixed_list() -> None:
    text = _script_text()
    names = re.search(r"var KEYFRAME_NAMES = \[(.*?)\];", text).group(1)
    assert re.findall(r"'([^']+)'", names) == ["dash", "edge-animation-frame"]


def test_drawings_never_animate_and_print_light_on_one_page() -> None:
    assert declared(".diagram-render svg *", "animation") == ["none !important"]
    assert declared(".diagram-render svg", "animation") == ["none !important"]
    assert declared(".diagram-render svg", "filter", "prefers-color-scheme: dark") == [
        "invert(1) hue-rotate(180deg)"
    ]
    assert declared(".diagram-render svg", "filter", "print") == ["none"]
    assert declared(".diagram-render", "break-inside", "print") == ["avoid"]


def test_the_privacy_note_is_laid_out_like_the_untrusted_notice() -> None:
    for prop in ("margin", "padding"):
        assert declared(".notice-diagrams", prop) == declared(".notice-untrusted", prop)
    assert declared(".notice-diagrams", "border-width") == declared(
        ".notice-untrusted", "border-width"
    )
    assert declared(".notice-diagrams", "grid-column", "min-width: 64rem") == ["1 / -1"]
