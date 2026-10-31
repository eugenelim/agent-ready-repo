"""Construction tests for the architect-assess HTML renderer.

Loads `render_html.py` by path under a pack-unique module name, per
`packs/AGENTS.md` § Writing pack tests, and drives the real entry point
in-process with resolved temporary directories.
"""

from __future__ import annotations

import ast
import base64
import hashlib
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
REPO_ROOT = PACK_ROOT.parents[1]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "architect-assess"
SCRIPT = SKILL_ROOT / "scripts" / "render_html.py"
HELPER_COPY = SKILL_ROOT / "scripts" / "file_safety.py"
HELPER_SOURCE = (
    REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "catalogue_tooling" / "file_safety.py"
)
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
        self._cell: str | None = None

    def handle_starttag(self, tag, attrs):
        self.elements.append(tag)
        self.order.append(tag)
        for name, value in attrs:
            self.attrs.append((tag, name, value))
            if name == "class":
                self.classes.append((tag, value or ""))
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
    hrefs = [v for tag, n, v in tree(text).attrs if tag == "a" and n == "href"]
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
    allowed = {
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
    }
    assert set(parsed.elements) <= allowed
    names = {name for _, name, _ in parsed.attrs}
    assert names <= {"class", "id", "lang", "charset", "http-equiv", "content", "href"}
    assert all(tag == "a" for tag, name, _ in parsed.attrs if name == "href")
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
    classes = {c for t, c in parsed.classes if t == "td"}
    assert {"ev-observed", "ev-inferred", "ev-reported", "ev-unknown"} <= classes


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
    assert 'class="banner-unconfirmed"' in text
    assert "Map and hotspot set not user-confirmed" in text
    assert text.index("banner-unconfirmed") < text.index("<h2")


def test_banner_absent_when_charter_confirms_once(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert "banner-unconfirmed" not in text.replace(".banner-unconfirmed{", "")


def test_confirmed_line_outside_charter_or_duplicated_does_not_suppress(
    mod, tmp_path, capsys
) -> None:
    outside = report(checkpoints=None, extra="Checkpoints: confirmed\n")
    assert 'class="banner-unconfirmed"' in page(tmp_path.resolve(), outside, mod, capsys)
    twice = report(checkpoints="Checkpoints: confirmed\nCheckpoints: confirmed")
    assert 'class="banner-unconfirmed"' in page(tmp_path.resolve(), twice, mod, capsys)
    fenced = report(checkpoints=None).replace(
        "Target: demo\n", "Target: demo\n```\nCheckpoints: confirmed\n```\n"
    )
    assert 'class="banner-unconfirmed"' in page(tmp_path.resolve(), fenced, mod, capsys)


def test_mermaid_fence_is_a_labeled_escaped_source_block(mod, tmp_path, capsys) -> None:
    extra = "```mermaid\nflowchart TD\n  A[<b>x</b>] --> B\n```\n"
    text = page(tmp_path.resolve(), report(extra=extra), mod, capsys)
    assert 'class="diagram-label">Diagram source (not rendered)</p><pre><code>flowchart' in text
    assert "A[&lt;b&gt;x&lt;/b&gt;]" in text
    assert "<script" not in text.lower()


def test_notice_and_metadata(mod, tmp_path, capsys) -> None:
    text = page(tmp_path.resolve(), report(), mod, capsys)
    assert (
        'class="notice-untrusted">Unverified: built from repository text and model analysis; not redacted<'
        in text
    )
    assert re.search(r"Generated \d{4}-\d{2}-\d{2} UTC", text)
    assert f"Renderer version {mod.RENDERER_VERSION}" in text
    assert "Source: effort/assessment.md" in text


# ---- exit codes, tokens, confinement ---------------------------------------------


def _only_fixed_tokens(out: str, err: str) -> None:
    allowed = {
        "render_html: ok",
        "render_html: usage: render_html.py <effort-dir>",
        "render_html: refused: unsafe or missing path",
        "render_html: refused: source over the size cap",
        "render_html: refused: rendered page over the size cap",
        "render_html: refused: source is not valid UTF-8",
        "render_html: refused: evidence class outside the allowed set",
        "render_html: failed: internal error",
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


def test_helper_copy_is_byte_identical_to_the_agentbundle_original() -> None:
    assert HELPER_COPY.read_bytes() == HELPER_SOURCE.read_bytes()


def test_renders_when_agentbundle_is_not_importable(mod, tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "agentbundle", None)
    monkeypatch.setitem(sys.modules, "agentbundle.catalogue_tooling", None)
    assert "<h1>" in page(tmp_path.resolve(), report(), mod, capsys)


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
        assert 'class="banner-unconfirmed"' in text
        assert "<pre><code>## Assessment charter\nCheckpoints: accepted-without-pause" not in text


def test_confirmed_once_in_charter_and_again_elsewhere_shows_no_banner(
    mod, tmp_path, capsys
) -> None:
    text = page(tmp_path.resolve(), report(extra="Checkpoints: confirmed\n"), mod, capsys)
    assert 'class="banner-unconfirmed"' not in text


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
    hrefs = [v for tag, n, v in tree(text).attrs if tag == "a"]
    assert hrefs == []


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
    assert "ev-observed" in {c for _, c in parsed.classes}


def test_second_level_one_heading_ends_the_charter_section(mod, tmp_path, capsys) -> None:
    source = report().replace(
        "## Conceptual current state",
        "# Appendix\n\nCheckpoints: confirmed\n\n## Conceptual current state",
        1,
    )
    text = page(tmp_path.resolve(), source, mod, capsys)
    assert 'class="banner-unconfirmed"' not in text


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
    assert "ev-observed" in {c for _, c in parsed.classes}


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
