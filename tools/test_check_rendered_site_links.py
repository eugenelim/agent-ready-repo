"""Focused tests for the generated-HTML internal-link checker."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CHECKER = REPO_ROOT / "tools" / "check-rendered-site-links.py"


def load_checker_module():
    """Load the hyphenated checker script for focused internal tests."""
    spec = importlib.util.spec_from_file_location("rendered_site_link_checker", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rendered_fixture(tmp_path: Path, files: dict[str, str | bytes]) -> Path:
    """Create a minimal rendered site and return its build root."""
    build = tmp_path / "build"
    build.mkdir()
    for relative, content in files.items():
        target = build / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8")
    return build


def run_checker(build: Path) -> subprocess.CompletedProcess[str]:
    """Invoke the checker through its documented CLI surface."""
    return subprocess.run(
        [sys.executable, str(CHECKER), "--build-dir", str(build)],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


# STUB: AC3, AC5 — the checker reports a missing internal page deterministically.
def test_missing_page_exits_one_with_stable_diagnostic(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {"index.html": '<a href="missing/">Missing</a>'},
    )

    result = run_checker(build)

    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        "BROKEN index.html: missing/ -> missing/index.html (missing page)",
        "rendered-site-links: 1 broken target across 1 page",
    ]
    assert result.stderr == ""


# STUB: AC4, AC6 — Pages-base, encoded paths, queries, and fragments resolve.
def test_pages_base_encoded_path_query_and_fragment_resolve(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {
            "index.html": ('<a href="/agent-ready-repo/docs/a%20b/?view=demo#result">Result</a>'),
            "docs/a b/index.html": '<h2 id="result">Result</h2>',
        },
    )

    result = run_checker(build)

    assert result.returncode == 0
    assert result.stdout == "rendered-site-links: 1 link across 2 pages; clean\n"
    assert result.stderr == ""


@pytest.mark.parametrize(
    "href",
    (
        "guide/",
        "/docs/guide/",
        "/agent-ready-repo/docs/guide/",
        "guide/index.html?mode=demo",
    ),
)
def test_relative_and_root_relative_directory_routes_resolve(
    tmp_path: Path,
    href: str,
) -> None:
    build = rendered_fixture(
        tmp_path,
        {
            "docs/index.html": f'<a href="{href}">Guide</a>',
            "docs/guide/index.html": "<h1>Guide</h1>",
        },
    )

    result = run_checker(build)

    assert result.returncode == 0, result.stdout + result.stderr


def test_fragments_accept_id_legacy_name_and_duplicates(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {
            "index.html": ('<a href="page/#same">ID</a><a href="page/#legacy">Legacy</a>'),
            "page/index.html": (
                '<h2 id="same">One</h2><div id="same">Two</div><a name="legacy"></a>'
            ),
        },
    )

    result = run_checker(build)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == "rendered-site-links: 2 links across 2 pages; clean\n"


def test_non_anchor_name_does_not_satisfy_fragment(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {
            "index.html": '<a href="form/#email">Email</a>',
            "form/index.html": '<input name="email">',
        },
    )

    result = run_checker(build)

    assert result.returncode == 1
    assert "form/index.html#email (missing fragment)" in result.stdout


def test_missing_fragment_reports_page_and_decoded_fragment(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {
            "index.html": '<a href="page/#missing%20section">Section</a>',
            "page/index.html": '<h2 id="present">Present</h2>',
        },
    )

    result = run_checker(build)

    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        (
            "BROKEN index.html: page/#missing%20section -> "
            "page/index.html#missing section (missing fragment)"
        ),
        "rendered-site-links: 1 broken target across 1 page",
    ]


def test_external_and_non_navigation_schemes_are_ignored(tmp_path: Path) -> None:
    hrefs = (
        "https://example.com/page",
        "//example.com/page",
        "mailto:user@example.com",
        "tel:+15555550100",
        "javascript:void(0)",
        "data:text/plain,example",
    )
    links = "".join(f'<a href="{href}">Outside</a>' for href in hrefs)
    build = rendered_fixture(tmp_path, {"index.html": links})

    result = run_checker(build)

    assert result.returncode == 0
    assert result.stdout == "rendered-site-links: 0 links across 1 page; clean\n"


def test_diagnostics_are_sorted_by_source_then_href(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {
            "z/index.html": '<a href="z-missing/">Z</a>',
            "a/index.html": ('<a href="b-missing/">B</a><a href="a-missing/">A</a>'),
        },
    )

    result = run_checker(build)

    assert result.returncode == 1
    diagnostics = result.stdout.splitlines()[:-1]
    assert diagnostics == sorted(diagnostics)


def test_traversal_above_build_root_exits_two(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {"index.html": '<a href="../outside.html">Outside</a>'},
    )

    result = run_checker(build)

    assert result.returncode == 2
    assert "escapes build root" in result.stderr
    assert result.stdout == ""


# STUB: AC3, AC5, AC6 — a symlink target outside the build root fails closed.
def test_symlink_escape_exits_two_without_reading_target(tmp_path: Path) -> None:
    if not hasattr(os, "symlink"):
        pytest.skip("symlinks are unavailable")
    build = rendered_fixture(
        tmp_path,
        {"index.html": '<a href="escape/secret.html">Secret</a>'},
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.html").write_text("outside", encoding="utf-8")
    try:
        (build / "escape").symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"symlink creation is unavailable: {exc}")

    result = run_checker(build)

    assert result.returncode == 2
    assert "escapes build root" in result.stderr
    assert "outside" not in result.stderr


def test_revisited_resolved_directory_is_pruned(monkeypatch, tmp_path: Path) -> None:
    checker = load_checker_module()
    build = rendered_fixture(tmp_path, {"index.html": "<h1>Home</h1>"})

    def repeated_walk(root: Path, followlinks: bool, onerror):
        assert followlinks is False
        assert onerror is not None
        yield str(root), [], ["index.html"]
        yield str(root), [], ["index.html"]

    monkeypatch.setattr(checker.os, "walk", repeated_walk)

    assert checker._discover_html(build.resolve()) == [build.resolve() / "index.html"]


def test_unreadable_subtree_exits_two(tmp_path: Path) -> None:
    build = rendered_fixture(tmp_path, {"index.html": "<h1>Home</h1>"})
    unreadable = build / "private"
    unreadable.mkdir()
    (unreadable / "hidden.html").write_text("<h1>Hidden</h1>", encoding="utf-8")
    unreadable.chmod(0)
    try:
        result = run_checker(build)
    finally:
        unreadable.chmod(0o700)

    if result.returncode == 0:
        pytest.skip("this platform cannot create an unreadable test directory")
    assert result.returncode == 2
    assert "cannot read discovered directory: private" in result.stderr
    assert result.stdout == ""


def test_duplicate_broken_href_has_one_diagnostic(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {"index.html": '<a href="missing/">One</a><a href="missing/">Two</a>'},
    )

    result = run_checker(build)

    assert result.returncode == 1
    assert result.stdout.splitlines() == [
        "BROKEN index.html: missing/ -> missing/index.html (missing page)",
        "rendered-site-links: 1 broken target across 1 page",
    ]


def test_invalid_link_error_names_source_and_href(tmp_path: Path) -> None:
    build = rendered_fixture(
        tmp_path,
        {"guide/index.html": '<a href="bad%escape/">Bad</a>'},
    )

    result = run_checker(build)

    assert result.returncode == 2
    assert (
        "page guide/index.html, href 'bad%escape/': malformed percent escape in link path"
    ) in result.stderr
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("files", "expected"),
    (
        ({}, "contains no HTML pages"),
        ({"index.html": b"\xff\xfe"}, "is not valid UTF-8"),
    ),
)
def test_structurally_invalid_build_tree_exits_two(
    tmp_path: Path,
    files: dict[str, str | bytes],
    expected: str,
) -> None:
    build = rendered_fixture(tmp_path, files)

    result = run_checker(build)

    assert result.returncode == 2
    assert expected in result.stderr
    assert result.stdout == ""


def test_missing_build_directory_exits_two(tmp_path: Path) -> None:
    result = run_checker(tmp_path / "absent")

    assert result.returncode == 2
    assert "does not exist" in result.stderr
    assert result.stdout == ""


def test_local_site_gate_builds_before_audit_and_aggregates_focused_tests() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "site-link-check: site-build" in makefile
    assert "$(PYTHON) tools/check-rendered-site-links.py --build-dir build" in makefile
    assert "tools/test_check_rendered_site_links.py" in makefile


def test_pages_gate_runs_after_both_builds_before_upload_and_has_path_filters() -> None:
    workflow = (REPO_ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")

    marketing_build = workflow.index("run: npm run build --prefix web")
    docs_build = workflow.index("run: npm run build --prefix docs-site")
    link_check = workflow.index(
        "run: python3 tools/check-rendered-site-links.py --build-dir build"
    )
    upload = workflow.index("uses: actions/upload-pages-artifact@")

    assert marketing_build < docs_build < link_check < upload
    assert workflow.count("- 'tools/check-rendered-site-links.py'") == 2
    assert workflow.count("- 'tools/test_check_rendered_site_links.py'") == 2
