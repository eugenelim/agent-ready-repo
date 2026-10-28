"""Scripted desktop-Chrome browser checks for the navigate-decisions explorer.

Closes: QE-14, FE-F1, FE-F2, FE-F3, FE-F4, FE-F5, FE-F6, FE-F9, FE-F10, FE-F11
Verification mode: scripted Chrome check (from plan.md T7).

These tests require Playwright with Chromium and are skipped cleanly when
Playwright is not installed. They are NEVER run in CI by default; dispatch
manually with: pytest packs/repo-governance/tests/skills/navigate-decisions/browser_checks.py

Run command (from repo root, requires `playwright install chrome`):
    python3 -m pytest packs/repo-governance/tests/skills/navigate-decisions/browser_checks.py -v

Spec: docs/specs/decision-navigation/spec.md (AC-0008, AC-0010, AC-0025, AC-0026, AC-0027)
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
import time

import pytest

playwright_mod = pytest.importorskip("playwright")  # skip if not installed
sync_api = pytest.importorskip("playwright.sync_api")

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / ".apm/skills/navigate-decisions/scripts"
FIXTURE_MIXED = HERE / "fixtures/mixed"
FIXTURE_HOSTILE = HERE / "fixtures/negative/hostile"
FIXTURE_QUESTIONS = HERE / "fixtures/questions"
FIXTURE_CHAIN = HERE / "fixtures/lineage-chain"


def _load_module(name: str, path: pathlib.Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


EXPLORER = _load_module(
    "repo_governance_explorer_browser",
    SCRIPTS / "explorer.py",
)


@pytest.fixture(scope="module")
def export_mixed(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export the mixed fixture to a temp file for browser tests."""
    out_dir = tmp_path_factory.mktemp("browser_mixed")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        FIXTURE_MIXED,
        destination=out_dir,
        mode="full",
        name="mixed.html",
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


@pytest.fixture(scope="module")
def export_questions(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export the questions fixture: every list's membership, order and hostile-name case."""
    out_dir = tmp_path_factory.mktemp("browser_questions")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        FIXTURE_QUESTIONS,
        destination=out_dir,
        mode="full",
        name="questions.html",
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


@pytest.fixture(scope="module")
def export_hostile(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export the hostile fixture to a temp file for browser tests."""
    out_dir = tmp_path_factory.mktemp("browser_hostile")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        FIXTURE_HOSTILE,
        destination=out_dir,
        mode="full",
        name="hostile.html",
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


_BODY_ELEMENTS = {
    "H3",
    "H4",
    "H5",
    "H6",
    "P",
    "UL",
    "OL",
    "LI",
    "PRE",
    "CODE",
    "BLOCKQUOTE",
    "TABLE",
    "THEAD",
    "TBODY",
    "TR",
    "TH",
    "TD",
    "HR",
    "EM",
    "STRONG",
    "SPAN",
    "BR",
}


def _pathological_body() -> str:
    """A hostile body near the 2 MiB admission bound: deep nesting, unclosed
    emphasis, long backtick runs, raw HTML, and a 40-level list."""
    parts = [
        ">" * 10000 + " deep quote\n\n",
        "*a " * 60000 + "\n\n",
        "`" * 50000 + "\n\n",
        "<script>alert(1)</script> <img src=x onerror=alert(1)> "
        "[click](javascript:alert(1)) ![alt\u202etxt](http://example.invalid/x.png)\n\n",
        "".join("  " * i + "- level\n" for i in range(40)),
    ]
    text = "".join(parts)
    pad = 2 * 1024 * 1024 - 4096 - len(text.encode("utf-8"))
    return text + ("word " * (pad // 5 + 1))[:pad]


def _write_single_record(root: pathlib.Path, body: str) -> None:
    adr_dir = root / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    (adr_dir / "0001-record.md").write_text(
        f"# ADR-0001: Body under test\n\n- **Status:** Accepted\n\n## Context\n\n{body}",
        encoding="utf-8",
    )


@pytest.fixture(scope="module")
def export_pathological(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export one record whose body is a hostile near-2 MiB Markdown document."""
    fixture_dir = tmp_path_factory.mktemp("pathological_fixture")
    _write_single_record(fixture_dir, _pathological_body())
    out_dir = tmp_path_factory.mktemp("browser_pathological")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        fixture_dir, destination=out_dir, mode="full", name="pathological.html"
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


@pytest.fixture(scope="module")
def export_markdown(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export one record whose body uses every allowlisted Markdown construct."""
    body = (
        "### Heading three\n\nA paragraph with *emphasis*, **strong**, and `code`.\n\n"
        "- one\n- two\n  - nested\n\n1. first\n2. second\n\n"
        "> quoted text\n\n```python\nprint('x')\n```\n\n"
        "| a | b |\n| :-- | --: |\n| 1 | 2 |\n\n---\n\n"
        "See [the docs](https://example.invalid/docs) and ![a diagram](d.png).\n"
    )
    fixture_dir = tmp_path_factory.mktemp("markdown_fixture")
    _write_single_record(fixture_dir, body)
    out_dir = tmp_path_factory.mktemp("browser_markdown")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        fixture_dir, destination=out_dir, mode="full", name="markdown.html"
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


def _render_body(page: object) -> None:
    """Open the only record's detail view and wait until its body has rendered."""
    page.evaluate("() => { location.hash = '#detail/ADR-0001'; }")  # type: ignore[union-attr]
    page.wait_for_function(  # type: ignore[union-attr]
        "() => { const c = document.querySelector('.record-content');"
        " return c && c.childNodes.length > 0; }",
        timeout=5000,
    )


def _open_page(
    browser: object,
    html_path: pathlib.Path,
) -> object:
    """Open an HTML file in a new page with offline context."""
    context = browser.new_context(offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    non_file_requests: list[str] = []
    page.on(
        "request",
        lambda r: non_file_requests.append(r.url) if not r.url.startswith("file://") else None,
    )
    page.goto(f"file://{html_path}")
    page.wait_for_load_state("networkidle")
    page._errors = errors  # type: ignore[attr-defined]
    page._non_file_requests = non_file_requests  # type: ignore[attr-defined]
    return page


@pytest.fixture(scope="module")
def browser():
    """Launch headless Chrome for the test module."""
    from playwright.sync_api import sync_playwright  # type: ignore[import-not-found]

    with sync_playwright() as p:
        br = p.chromium.launch(channel="chrome", headless=True)
        yield br
        br.close()


def test_no_page_errors_mixed(browser: object, export_mixed: pathlib.Path) -> None:
    """QE-14/FE-F4: Mixed export opens without page errors."""
    page = _open_page(browser, export_mixed)
    assert not page._errors, (  # type: ignore[attr-defined]
        f"page errors in mixed export: {page._errors}"  # type: ignore[attr-defined]
    )


def test_no_network_requests(browser: object, export_mixed: pathlib.Path) -> None:
    """Security: self-contained export must not issue network requests."""
    page = _open_page(browser, export_mixed)
    non_file = page._non_file_requests  # type: ignore[attr-defined]
    assert not non_file, f"export triggered non-file requests: {non_file}"


def test_hash_routing_empty_hash_shows_list(browser: object, export_mixed: pathlib.Path) -> None:
    """QE-14/FE-F1: Back from a detail route to the no-hash entry shows the default list."""
    page = _open_page(browser, export_mixed)
    page.locator(".row-link").first.click()
    page.wait_for_selector("#detail-body h2.detail-heading")
    assert page.locator("#view-recent").is_visible(), "the list stays beside the detail"
    assert page.locator("#detail-body h2.detail-heading").text_content() != "Record detail"
    page.go_back()
    page.wait_for_function(
        "() => document.querySelector('#detail-body h2.detail-heading').textContent"
        " === 'Record detail'"
    )
    assert page.evaluate("location.hash") == ""
    assert page.locator("#view-recent h2").text_content() == "Decided records"
    assert page.locator("#app-main[data-picked]").count() == 0


def test_hash_routing_bogus_hash_shows_list(browser: object, export_mixed: pathlib.Path) -> None:
    """QE-14/FE-F1: Unknown route hash navigates to list view."""
    page = _open_page(browser, export_mixed)
    page.evaluate("window.location.hash = '#bogus-unknown-view'")
    page.wait_for_timeout(200)
    list_view = page.locator("#view-list")
    assert list_view.is_visible(), "list view must be visible after unknown hash"
    assert not page._errors, f"page errors after bogus hash: {page._errors}"  # type: ignore[attr-defined]


def test_hash_routing_uri_error_safe(browser: object, export_mixed: pathlib.Path) -> None:
    """QE-14/FE-F1: Malformed percent-encoding in hash does not crash."""
    page = _open_page(browser, export_mixed)
    # %E0 alone is an invalid UTF-8 sequence — decodeURIComponent throws URIError.
    page.evaluate("window.location.hash = '#detail/%E0'")
    page.wait_for_timeout(200)
    # Must not crash; either list or detail view must be visible.
    list_visible = page.locator("#view-list").is_visible()
    detail_visible = page.locator("#detail-body").is_visible()
    assert list_visible or detail_visible, "after URIError hash, at least one view must be visible"
    assert not page._errors, (  # type: ignore[attr-defined]
        f"page errors after URIError hash: {page._errors}"  # type: ignore[attr-defined]
    )


def test_aria_current_on_nav_buttons(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F9: View nav buttons use aria-current='page', not aria-pressed."""
    page = _open_page(browser, export_mixed)
    # The Recently decided link must have aria-current=page (it is the initial view).
    list_btn = page.locator("#q-recent")
    current = list_btn.get_attribute("aria-current")
    assert current == "page", f"list button must have aria-current='page'; got {current!r}"
    # Must not have aria-pressed.
    pressed = list_btn.get_attribute("aria-pressed")
    assert pressed is None, f"nav buttons must not use aria-pressed; got {pressed!r}"


def test_focus_moves_to_view_heading(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F2: Focus moves to the view's h2 heading after navigation."""
    page = _open_page(browser, export_mixed)
    # Click graph button to navigate.
    page.locator("#q-graph").click()
    page.wait_for_timeout(200)
    # The focused element should be the h2 inside #view-graph.
    focused_tag = page.evaluate("document.activeElement.tagName.toLowerCase()")
    focused_parent = page.evaluate("document.activeElement.closest('[id^=view-]')?.id || ''")
    assert focused_tag in ("h1", "h2"), (
        f"focus must be on a heading after navigation; got <{focused_tag}>"
    )
    assert "graph" in focused_parent, (
        f"focused heading must be inside graph view; parent id={focused_parent!r}"
    )


def test_live_region_updates_on_filter(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F3: Polite live region text updates when result count changes."""
    page = _open_page(browser, export_mixed)
    page.wait_for_timeout(300)
    # The live region must have content after the initial render.
    live = page.locator("#live-region")
    assert live.count() > 0, "live region element must be present"
    initial_text = live.text_content() or ""
    # Type a search that returns fewer results.
    page.locator("#search-input").fill("zzzzz-no-match")
    page.wait_for_timeout(300)
    updated_text = live.text_content() or ""
    assert initial_text.endswith("records shown."), initial_text
    assert updated_text == 'No records match search: "zzzzz-no-match".', updated_text


def test_no_results_shows_reset_control(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F5: No-results state echoes query and shows a reset control."""
    page = _open_page(browser, export_mixed)
    page.locator("#search-input").fill("zzzzz-no-match")
    page.wait_for_timeout(300)
    # A reset button or link must be visible.
    reset_btn = page.locator(".reset-btn")
    assert reset_btn.is_visible(), "a reset button must appear in the no-results state"
    # Empty message must echo the query.
    empty_msg = page.locator(".empty-msg").text_content() or ""
    assert "zzzzz-no-match" in empty_msg, (
        f"no-results message must echo the active query; got {empty_msg!r}"
    )


def test_missing_id_shows_not_in_export(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F10: Unknown record ID in route shows 'not in this export', not 'nothing selected'."""
    page = _open_page(browser, export_mixed)
    page.evaluate("window.location.hash = '#detail/' + encodeURIComponent('ADR-9999')")
    page.wait_for_timeout(300)
    detail_text = page.locator("#detail-body").text_content() or ""
    assert "not in this export" in detail_text.lower() or "ADR-9999" in detail_text, (
        f"missing ID detail view must say the record is not in this export; "
        f"got: {detail_text[:200]!r}"
    )
    # Must NOT say the generic 'nothing selected' message.
    assert "nothing selected" not in detail_text.lower(), (
        "missing ID must not show the generic 'nothing selected' message"
    )


def test_24px_min_targets(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F6: every visible button, link, select and input in the list view is at
    least 24×24 CSS px."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    buttons = page.locator("button, a, select, input").all()
    assert len(buttons) > 10
    for btn in buttons:
        box = btn.bounding_box()
        if box is None:
            continue  # hidden button
        w, h = box["width"], box["height"]
        assert w >= 24 and h >= 24, (
            f"button '{btn.text_content()}' is smaller than 24×24: {w:.1f}×{h:.1f}"
        )


def test_relationships_section_folded_by_default(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0026: Relationships <details> in detail view is closed by default."""
    page = _open_page(browser, export_mixed)
    # Click the first record button to go to detail.
    page.locator(".row-link").first.click()
    page.wait_for_timeout(300)
    # Check that rel-details is present and closed.
    rel_details = page.locator(".rel-details")
    assert rel_details.count() == 1, (
        "the first record has relationships, so the section must exist"
    )
    open_attr = rel_details.first.get_attribute("open")
    assert open_attr is None, (
        "Relationships <details> must be closed by default; found open attribute"
    )
    # Summary must contain counts.
    summary_text = rel_details.first.locator("summary").text_content() or ""
    counts = page.evaluate(
        """() => { const d = JSON.parse(document.getElementById('nav-data').textContent);
          const id = d.records[0].id, c = {checked: 0, candidate: 0, contextual: 0,
            navigation_only: 0};
          d.relationships.forEach(r => { if (r.from === id || r.to === id) c[r.trust_class]++; });
          return c; }"""
    )
    expected = (
        f"Relationships — {counts['checked']} checked · {counts['candidate']} candidate · "
        f"{counts['contextual']} contextual · {counts['navigation_only']} navigation-only"
    )
    assert summary_text == expected, summary_text


def test_long_body_folded(browser: object, export_pathological: pathlib.Path) -> None:
    """FE-F11: Long record bodies use progressive disclosure (<details>)."""
    page = _open_page(browser, export_pathological)
    page.locator(".row-link").first.click()
    page.wait_for_timeout(300)
    # The body must be inside a <details> element (body-details class).
    body_details = page.locator(".body-details")
    assert body_details.count() == 1, "a long record body must sit in one <details> element"
    assert body_details.get_attribute("open") is not None, "the record body opens by default"
    summary = body_details.locator("summary").text_content() or ""
    assert summary.startswith("Record content (") and summary.endswith(" chars)"), summary


def test_no_horizontal_overflow_640px(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0010: No horizontal scroll at 640 CSS px viewport width."""
    context = browser.new_context(viewport={"width": 640, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_load_state("networkidle")
    overflow = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, "Horizontal overflow at 640 px viewport width — reflow is broken"


def test_no_horizontal_overflow_320px(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0010: No horizontal scroll at 320 CSS px viewport width."""
    context = browser.new_context(viewport={"width": 320, "height": 600}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_load_state("networkidle")
    overflow = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, "Horizontal overflow at 320 px viewport width — reflow is broken"


def test_reduced_motion_rule_present(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0010: CSS contains a prefers-reduced-motion rule."""
    html = export_mixed.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in html, "HTML must contain a prefers-reduced-motion CSS rule"


def test_record_content_border_differs_from_evidence_rail(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0010: .record-content border style differs from evidence-rail border styles.

    The record body container must not reuse the trust-class border styles
    (solid/dashed/dotted/double left borders of rel-checked/candidate/etc.).
    """
    page = _open_page(browser, export_mixed)
    # Navigate to a record with a body.
    page.locator(".row-link").first.click()
    page.wait_for_timeout(300)
    # Evidence rail checked uses solid; candidate dashed; contextual dotted; nav double.
    # The record-content uses a uniform 2px solid all-around border (not left only).
    rc_border_left_width = page.evaluate(
        "getComputedStyle(document.querySelector('.record-content'))?.borderLeftWidth || '0px'"
    )
    # rel-checked has borderLeftWidth of 4px; record-content has 2px.
    assert rc_border_left_width != "4px", (
        f"record-content left border width must not match evidence-rail (4px); "
        f"got {rc_border_left_width!r}"
    )


def test_supersession_banners_in_list_and_detail(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0025: checked supersession shows a banner in the list row and the detail
    view, with partial scope, and its link opens the superseding record."""
    page = _open_page(browser, export_mixed)
    page.evaluate("() => { location.hash = '#list'; }")  # type: ignore[union-attr]
    page.wait_for_selector("#view-list li.row")  # type: ignore[union-attr]
    list_text = " | ".join(
        page.locator("#view-list .supersede-banner").all_inner_texts()  # type: ignore[union-attr]
    )
    assert "Superseded in part by ADR-0020 (D3)" in list_text, list_text
    assert "Superseded by ADR-0003" in list_text, list_text
    page.evaluate("() => { location.hash = '#detail/ADR-0001'; }")  # type: ignore[union-attr]
    banner = page.locator("#detail-body .supersede-banner").first  # type: ignore[union-attr]
    banner.wait_for()
    assert "Superseded in part by ADR-0020 (D3)" in (banner.inner_text() or "")
    banner.get_by_text("ADR-0020").first.click()
    page.wait_for_function("() => location.hash === '#list/ADR-0020'")  # type: ignore[union-attr]
    assert not page._errors  # type: ignore[attr-defined]


def test_markdown_renders_allowlisted_structure(
    browser: object, export_markdown: pathlib.Path
) -> None:
    """AC-0010: Markdown bodies render as allowlisted elements with inert links."""
    page = _open_page(browser, export_markdown)
    _render_body(page)
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const c = document.querySelector('.record-content');
        const tags = new Set(); const attrs = new Set();
        c.querySelectorAll('*').forEach(e => { tags.add(e.tagName);
          for (const a of e.attributes) attrs.add(a.name); });
        return { tags: [...tags], attrs: [...attrs],
          loaders: c.querySelectorAll('img,a,iframe,object,embed').length,
          text: c.textContent }; }"""
    )
    assert {"H3", "H4", "H5", "H6"} & set(info["tags"]), info["tags"]
    expected = ("UL", "OL", "LI", "BLOCKQUOTE", "PRE", "CODE", "TABLE", "HR", "EM", "STRONG")
    for tag in expected:
        assert tag in info["tags"], f"{tag} not rendered: {info['tags']}"
    assert set(info["tags"]) <= _BODY_ELEMENTS, set(info["tags"]) - _BODY_ELEMENTS
    assert set(info["attrs"]) <= {"class", "aria-label"}, info["attrs"]
    assert info["loaders"] == 0
    assert "https://example.invalid/docs" in info["text"]
    assert "a diagram" in info["text"]
    assert not page._errors  # type: ignore[attr-defined]


def test_pathological_body_renders_fully_and_inertly(
    browser: object, export_pathological: pathlib.Path
) -> None:
    """AC-0010: a hostile near-2 MiB body renders within 2 s, falls back to plain
    text past 32 nesting levels, keeps raw HTML literal, and loads nothing."""
    page = _open_page(browser, export_pathological)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    start = time.monotonic()
    _render_body(page)
    elapsed_ms = (time.monotonic() - start) * 1000
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const c = document.querySelector('.record-content');
        const tags = new Set(); let attrs = 0;
        c.querySelectorAll('*').forEach(e => {
          tags.add(e.tagName); attrs += e.attributes.length; });
        return { tags: [...tags], attrs, length: c.textContent.length,
          loaders: c.querySelectorAll('img,a,iframe,object,embed,script').length,
          literal: c.textContent.includes('<script>alert(1)</script>'),
          note: c.textContent.includes('nesting deeper than 32 levels') }; }"""
    )
    assert elapsed_ms < 2000, f"rendered in {elapsed_ms:.0f} ms"
    assert info["length"] > 1_900_000, info["length"]
    assert info["note"], "the 32-level fallback note is missing"
    assert info["literal"], "raw HTML must render as literal text"
    assert info["loaders"] == 0 and info["attrs"] == 0
    assert set(info["tags"]) <= _BODY_ELEMENTS
    assert not page._errors  # type: ignore[attr-defined]
    assert not page._non_file_requests  # type: ignore[attr-defined]


def test_typing_in_search_keeps_focus(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F2 regression: filtering re-renders the list without stealing focus."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    page.click("#search-input")  # type: ignore[union-attr]
    page.keyboard.type("adr")  # type: ignore[union-attr]
    assert page.evaluate("() => document.activeElement.id") == "search-input"  # type: ignore[union-attr]
    assert page.input_value("#search-input") == "adr"  # type: ignore[union-attr]


# ── AC-0026: SVG lineage diagram browser checks ───────────────────────────────


def _write_adr(adr_dir: pathlib.Path, ordinal: int, title: str, body: str) -> None:
    """Write a minimal ADR file into adr_dir."""
    adr_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{ordinal:04d}-{title.lower().replace(' ', '-')}.md"
    content = f"# ADR-{ordinal:04d}: {title}\n\n{body}\n## Context\n\nTest record.\n"
    (adr_dir / filename).write_text(content, encoding="utf-8")


def _build_corpus(root: pathlib.Path, records: list[tuple[int, str, str]]) -> None:
    """Build a minimal corpus from (ordinal, title, header_body) tuples."""
    adr_dir = root / "docs" / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)
    for ordinal, title, header in records:
        slug = title.lower().replace(" ", "-").replace("/", "-")
        fname = f"{ordinal:04d}-{slug}.md"
        content = f"# ADR-{ordinal:04d}: {title}\n\n{header}\n## Context\n\nTest.\n"
        (adr_dir / fname).write_text(content, encoding="utf-8")


def _export(
    tmp_path_factory: pytest.TempPathFactory, fixture_root: pathlib.Path, tag: str
) -> pathlib.Path:
    """Publish a fixture to a temp HTML file and return its path."""
    out = tmp_path_factory.mktemp(f"browser_{tag}")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        fixture_root, destination=out, mode="full", name=f"{tag}.html"
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


@pytest.fixture(scope="module")
def export_cycle(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """3-record cycle: ADR-0001 ↔ ADR-0002 ↔ ADR-0003 (all in one SCC)."""
    root = tmp_path_factory.mktemp("cycle_fixture")
    # Edges (from=newer→to=older): 0001→0003, 0002→0001, 0003→0002 → one SCC
    _build_corpus(
        root,
        [
            (
                1,
                "Cycle A",
                "- **Status:** Accepted\n"
                "- **Supersedes:** ADR-0003\n"
                "- **Superseded by:** ADR-0002\n",
            ),
            (
                2,
                "Cycle B",
                "- **Status:** Accepted\n"
                "- **Supersedes:** ADR-0001\n"
                "- **Superseded by:** ADR-0003\n",
            ),
            (
                3,
                "Cycle C",
                "- **Status:** Accepted\n"
                "- **Supersedes:** ADR-0002\n"
                "- **Superseded by:** ADR-0001\n",
            ),
        ],
    )
    return _export(tmp_path_factory, root, "cycle")


@pytest.fixture(scope="module")
def export_branching(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """4-record branching chain: ADR-0002 and ADR-0003 both supersede ADR-0001;
    ADR-0004 supersedes ADR-0002."""
    root = tmp_path_factory.mktemp("branch_fixture")
    _build_corpus(
        root,
        [
            (
                1,
                "Branch Root",
                "- **Status:** Accepted\n"
                "- **Superseded by:** ADR-0002\n"
                "- **Superseded in part:** ADR-0003 D1\n",
            ),
            (
                2,
                "Branch Mid A",
                "- **Status:** Accepted\n"
                "- **Supersedes:** ADR-0001\n"
                "- **Superseded by:** ADR-0004\n",
            ),
            (3, "Branch Mid B", "- **Status:** Accepted\n- **Supersedes in part:** ADR-0001 D1\n"),
            (4, "Branch Tip", "- **Status:** Accepted\n- **Supersedes:** ADR-0002\n"),
        ],
    )
    return _export(tmp_path_factory, root, "branching")


@pytest.fixture(scope="module")
def export_five_chain(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """5-record linear chain: ADR-0005 → ADR-0004 → ADR-0003 → ADR-0002 → ADR-0001."""
    root = tmp_path_factory.mktemp("five_fixture")
    _build_corpus(
        root,
        [
            (1, "Five A", "- **Status:** Accepted\n- **Superseded by:** ADR-0002\n"),
            (
                2,
                "Five B",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"
                "- **Superseded by:** ADR-0003\n",
            ),
            (
                3,
                "Five C",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0002\n"
                "- **Superseded by:** ADR-0004\n",
            ),
            (
                4,
                "Five D",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0003\n"
                "- **Superseded by:** ADR-0005\n",
            ),
            (5, "Five E", "- **Status:** Accepted\n- **Supersedes:** ADR-0004\n"),
        ],
    )
    return _export(tmp_path_factory, root, "five_chain")


def _navigate_graph(page: object, record_id: str | None = None) -> None:
    """Navigate to the graph view, optionally focused on record_id."""
    hash_val = f"#graph/{record_id}" if record_id else "#graph"
    page.evaluate(f"() => {{ location.hash = '{hash_val}'; }}")  # type: ignore[union-attr]
    page.wait_for_function(  # type: ignore[union-attr]
        "() => document.querySelector('[data-node-id], .chain-card, .empty-msg') !== null",
        timeout=5000,
    )


def test_graph_focused_svg_has_nodes_and_d3_label(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0026: focused #graph/ADR-0001 renders ≥2 node groups and a visible
    'in part · D3' label that sets partial supersession apart from full."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    # At least 2 node groups (ADR-0001 and ADR-0020 in mixed fixture's checked chain)
    node_count = page.evaluate(  # type: ignore[union-attr]
        "document.querySelectorAll('[data-node-id]').length"
    )
    assert node_count >= 2, f"expected ≥2 node groups in focused graph, got {node_count}"
    # Partial supersession is named in words on the edge, with its scope
    has_d3 = page.evaluate(  # type: ignore[union-attr]
        "() => { var texts = document.querySelectorAll('svg text');"
        " for (var t of texts) { if (t.textContent.trim() === 'in part · D3') return true; }"
        " return false; }"
    )
    assert has_d3, "Edge label 'in part · D3' not found in focused graph SVG"
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_layout_older_left_of_newer(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: the older superseded record (ADR-0001) renders left of the newer (ADR-0020)."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    x_vals = page.evaluate(  # type: ignore[union-attr]
        "() => {"
        "  function nodeX(id) {"
        "    var g = document.querySelector('[data-node-id=\"' + id + '\"]');"
        "    if (!g) return null;"
        "    var r = g.querySelector('rect'); return r ? parseFloat(r.getAttribute('x')) : null;"
        "  }"
        "  return { adr0001: nodeX('ADR-0001'), adr0020: nodeX('ADR-0020') };"
        "}"
    )
    assert x_vals["adr0001"] is not None, "ADR-0001 node not found in SVG"
    assert x_vals["adr0020"] is not None, "ADR-0020 node not found in SVG"
    assert x_vals["adr0001"] < x_vals["adr0020"], (
        f"Older ADR-0001 (x={x_vals['adr0001']}) must be left of newer "
        f"ADR-0020 (x={x_vals['adr0020']})"
    )
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_contextual_toggle(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: contextual group is hidden until the toggle is pressed; chain node
    x-positions do not change when contextual edges are shown."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    # Contextual toggle button is present (ADR-0001 has Related: links)
    page.wait_for_selector(".ctx-toggle")  # type: ignore[union-attr]
    # x position of ADR-0001 node before toggle
    x_before = page.evaluate(  # type: ignore[union-attr]
        "() => { var g = document.querySelector('[data-node-id=\"ADR-0001\"]');"
        " var r = g && g.querySelector('rect');"
        " return r ? parseFloat(r.getAttribute('x')) : null; }"
    )
    # At least one hidden g exists: the ctx group carries `hidden` and computes display:none
    has_hidden_ctx = page.evaluate(  # type: ignore[union-attr]
        "() => { var gs = document.querySelectorAll('svg g[aria-hidden]');"
        " for (var g of gs) { if (g.hasAttribute('hidden')"
        " && getComputedStyle(g).display === 'none') return true; } return false; }"
    )
    assert has_hidden_ctx, "Contextual SVG group should be hidden (display:none) before toggle"
    # Press the toggle
    page.click(".ctx-toggle")  # type: ignore[union-attr]
    page.wait_for_timeout(200)
    # After toggle, no hidden context groups remain
    still_hidden = page.evaluate(  # type: ignore[union-attr]
        "() => { var gs = document.querySelectorAll('svg g[aria-hidden]');"
        " for (var g of gs) { if (g.hasAttribute('hidden')) return true; } return false; }"
    )
    assert not still_hidden, "Contextual SVG group should be visible after toggle"
    # Chain node x position must be unchanged after toggle
    x_after = page.evaluate(  # type: ignore[union-attr]
        "() => { var g = document.querySelector('[data-node-id=\"ADR-0001\"]');"
        " var r = g && g.querySelector('rect');"
        " return r ? parseFloat(r.getAttribute('x')) : null; }"
    )
    assert x_before == x_after, (
        f"ADR-0001 x changed from {x_before} to {x_after} after contextual toggle"
    )
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_cycle_members_share_x_and_have_cycle_labels(
    browser: object, export_cycle: pathlib.Path
) -> None:
    """AC-0026: cycle SCC members share the same x-column; 'cycle' labels appear in the SVG."""
    page = _open_page(browser, export_cycle)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    # All 3 records are in the chain
    node_count = page.evaluate(  # type: ignore[union-attr]
        "document.querySelectorAll('[data-node-id]').length"
    )
    assert node_count == 3, f"expected 3 nodes in cycle graph, got {node_count}"
    # All nodes share the same x-coordinate (same SCC → same column)
    x_vals = page.evaluate(  # type: ignore[union-attr]
        "() => Array.from(document.querySelectorAll('[data-node-id]')).map("
        "  g => { var r = g.querySelector('rect');"
        "  return r ? parseFloat(r.getAttribute('x')) : null; })"
    )
    assert all(x is not None for x in x_vals), f"some node rects missing x: {x_vals}"
    assert len(set(x_vals)) == 1, (
        f"cycle SCC members must share the same x-column, got distinct x values: {x_vals}"
    )
    # 'cycle' text elements appear (arc labels + node badges)
    cycle_texts = page.evaluate(  # type: ignore[union-attr]
        "() => Array.from(document.querySelectorAll('svg text'))"
        ".filter(t => t.textContent.trim() === 'cycle').length"
    )
    assert cycle_texts >= 2, f"expected ≥2 'cycle' text elements, got {cycle_texts}"
    # Nodes in kind-and-ordinal order top-to-bottom: ADR-0001 row < ADR-0002 row < ADR-0003 row
    rows = page.evaluate(  # type: ignore[union-attr]
        "() => {"
        "  function nodeY(id) {"
        "    var g = document.querySelector('[data-node-id=\"' + id + '\"]');"
        "    var r = g && g.querySelector('rect');"
        "    return r ? parseFloat(r.getAttribute('y')) : null;"
        "  }"
        "  return { adr1: nodeY('ADR-0001'), adr2: nodeY('ADR-0002'), adr3: nodeY('ADR-0003') };"
        "}"
    )
    assert rows["adr1"] is not None and rows["adr2"] is not None and rows["adr3"] is not None
    assert rows["adr1"] < rows["adr2"] < rows["adr3"], (
        f"cycle members must be sorted top-to-bottom by kind then ordinal: {rows}"
    )
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_branching_renders_all_members(
    browser: object, export_branching: pathlib.Path
) -> None:
    """AC-0026: a branching chain (4 records) renders all members as node groups."""
    page = _open_page(browser, export_branching)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    node_count = page.evaluate(  # type: ignore[union-attr]
        "document.querySelectorAll('[data-node-id]').length"
    )
    assert node_count == 4, f"expected 4 nodes in branching graph, got {node_count}"
    for rid in ("ADR-0001", "ADR-0002", "ADR-0003", "ADR-0004"):
        present = page.evaluate(  # type: ignore[union-attr]
            f"document.querySelector('[data-node-id=\"{rid}\"]') !== null"
        )
        assert present, f"{rid} node group missing from branching chain SVG"
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_five_chain_renders_all_members(
    browser: object, export_five_chain: pathlib.Path
) -> None:
    """AC-0026: a 5-record linear chain renders all 5 members in column order."""
    page = _open_page(browser, export_five_chain)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    node_count = page.evaluate(  # type: ignore[union-attr]
        "document.querySelectorAll('[data-node-id]').length"
    )
    assert node_count == 5, f"expected 5 nodes in linear chain, got {node_count}"
    # Columns increase from ADR-0001 (oldest) to ADR-0005 (newest)
    x_order = page.evaluate(  # type: ignore[union-attr]
        "() => ['ADR-0001','ADR-0002','ADR-0003','ADR-0004','ADR-0005'].map(id => {"
        "  var g = document.querySelector('[data-node-id=\"' + id + '\"]');"
        "  var r = g && g.querySelector('rect');"
        "  return r ? parseFloat(r.getAttribute('x')) : null;})"
    )
    assert all(v is not None for v in x_order), f"some nodes missing: {x_order}"
    for i in range(len(x_order) - 1):
        assert x_order[i] < x_order[i + 1], (
            f"x must increase from oldest to newest; failed at index {i}: {x_order}"
        )
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_keyboard_navigation(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: Tab reaches the focused node (tabindex=0); ArrowRight moves focus to newer
    connected node; Enter navigates to that node's graph view."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    # ADR-0001 is the selected node and must have tabindex=0 (Tab-reachable)
    ti = page.evaluate(  # type: ignore[union-attr]
        "() => { var g = document.querySelector('[data-node-id=\"ADR-0001\"]');"
        " return g ? parseInt(g.getAttribute('tabindex'), 10) : null; }"
    )
    assert ti == 0, f"ADR-0001 must have tabindex=0 in focused graph; got {ti}"
    # Focus the node and press ArrowRight to move to ADR-0020 (newer)
    page.evaluate(  # type: ignore[union-attr]
        "() => document.querySelector('[data-node-id=\"ADR-0001\"]').focus()"
    )
    page.keyboard.press("ArrowRight")  # type: ignore[union-attr]
    page.wait_for_timeout(100)
    focused_id = page.evaluate(  # type: ignore[union-attr]
        "() => document.activeElement && document.activeElement.dataset.nodeId"
    )
    assert focused_id == "ADR-0020", (
        f"ArrowRight from ADR-0001 should focus ADR-0020 (newer); focused {focused_id!r}"
    )
    # Press Enter to navigate to ADR-0020's graph view
    page.keyboard.press("Enter")  # type: ignore[union-attr]
    page.wait_for_function(  # type: ignore[union-attr]
        "() => location.hash === '#graph/ADR-0020'", timeout=3000
    )
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_text_equivalent_matches_svg_nodes(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0026: the text equivalent lists the same node IDs that appear as SVG nodes."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    # Node IDs from SVG
    svg_ids = page.evaluate(  # type: ignore[union-attr]
        "() => Array.from(document.querySelectorAll('[data-node-id]')).map(g => g.dataset.nodeId)"
    )
    assert svg_ids, "no node groups found in SVG"
    # Node IDs in the text equivalent (li items starting with 'ADR-' or 'RFC-')
    text_ids = page.evaluate(  # type: ignore[union-attr]
        "() => Array.from(document.querySelectorAll('.lineage-text li.lt-node'))"
        ".map(li => li.textContent.split(':')[0].trim())"
    )
    assert set(svg_ids) == set(text_ids), (
        f"SVG node IDs {sorted(svg_ids)} differ from text-equivalent IDs {sorted(text_ids)}"
    )
    rel_lines = page.evaluate(  # type: ignore[union-attr]
        "() => Array.from(document.querySelectorAll('.lineage-text li.lt-rel'))"
        ".map(li => li.textContent)"
    )
    assert "ADR-0020 supersedes in part (D3) ADR-0001" in rel_lines, rel_lines
    drawn = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph svg [data-rel]')]"
        ".map(e => e.dataset.rel)"
    )
    listed = page.evaluate(
        "() => [...document.querySelectorAll('.lineage-text li.lt-rel')].map(e => e.dataset.rel)"
    )
    assert drawn and sorted(drawn) == sorted(listed), (drawn, listed)
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_atlas_shows_one_card_per_chain(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: the atlas view (#graph) shows one chain card per checked-supersession chain
    with ≥2 records."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page)  # #graph — no focused record
    card_count = page.evaluate(  # type: ignore[union-attr]
        "document.querySelectorAll('.chain-card').length"
    )
    # The mixed fixture has three checked chains: ADR-0001/0020, ADR-0002/0003, ADR-0010/0011.
    assert card_count == 3, f"atlas must show one card per chain; got {card_count}"
    # Each card contains an SVG
    svgs_in_cards = page.evaluate(  # type: ignore[union-attr]
        "() => Array.from(document.querySelectorAll('.chain-card'))"
        ".every(c => c.querySelector('svg') !== null)"
    )
    assert svgs_in_cards, "every chain card must contain an SVG element"
    assert not page._errors  # type: ignore[attr-defined]


def test_graph_no_page_errors(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: graph view opens without page errors."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    assert not page._errors, f"page errors in graph view: {page._errors}"  # type: ignore[attr-defined]


def test_graph_no_network_requests(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: graph view issues no non-file requests (fully self-contained)."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    non_file = page._non_file_requests  # type: ignore[attr-defined]
    assert not non_file, f"graph view triggered non-file requests: {non_file}"


def test_graph_no_horizontal_overflow_640px(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: graph view has no horizontal overflow at 640 px viewport."""
    context = browser.new_context(viewport={"width": 640, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_load_state("networkidle")
    page.evaluate("() => { location.hash = '#graph/ADR-0001'; }")
    page.wait_for_timeout(300)
    overflow = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, "Horizontal overflow at 640 px in graph view"


def test_graph_no_horizontal_overflow_320px(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: graph view has no horizontal overflow at 320 px viewport."""
    context = browser.new_context(viewport={"width": 320, "height": 600}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_load_state("networkidle")
    page.evaluate("() => { location.hash = '#graph/ADR-0001'; }")
    page.wait_for_timeout(300)
    overflow = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, "Horizontal overflow at 320 px in graph view"


def test_long_qualified_status_does_not_squeeze_title(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """A long qualified lifecycle value wraps inside its pill and leaves the title
    at least a third of the row, while the exact value stays visible."""
    status = (
        "Accepted (superseded in part by ADR-0111 \u2014 \u00a7 5's intent-mode rubric and "
        "its single `Clean` | `Findings` result vocabulary; everything else stands)"
    )
    root = tmp_path_factory.mktemp("long_status")
    rfc_dir = root / "docs" / "rfc"
    rfc_dir.mkdir(parents=True)
    (rfc_dir / "0099-long-status.md").write_text(
        f"# RFC-0099: Cut before adding and artifact shaping\n\n- **Status:** {status}\n\n"
        "## Summary\n\nBody.\n",
        encoding="utf-8",
    )
    out = tmp_path_factory.mktemp("long_status_out")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        root, destination=out, mode="full", name="long.html"
    )
    assert r["status"] == "ok", r.get("error")
    page = _open_page(browser, pathlib.Path(r["path"]))
    page.set_viewport_size({"width": 1440, "height": 900})  # type: ignore[union-attr]
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const li = document.querySelector('li.row');
          const row = li.querySelector('.row-link').getBoundingClientRect();
          const title = li.querySelector('.c-title').getBoundingClientRect();
          const mark = li.querySelector('.mark');
          return { ratio: title.width / row.width,
                   status: mark.textContent.slice(mark.querySelector('.mark-g').textContent.length)
                 }; }"""
    )
    assert info["ratio"] >= 0.33, info
    assert info["status"] == status, info


def test_rendered_page_never_shows_raw_bidi_controls(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """AC-0010: no visible text anywhere in the rendered page carries a raw
    bidirectional or zero-width control; each appears as a visible [U+XXXX] marker."""
    root = tmp_path_factory.mktemp("bidi_page")
    adr = root / "docs" / "adr"
    adr.mkdir(parents=True)
    (adr / "0001-bidi.md").write_text(
        "# ADR-0001: Safe‮title‬ with​hidden\n\n"
        "- **Status:** Accepted‮detcepecca‬\n"
        "- **Superseded by:** ADR-0002\n\n## Context\n\nBody.\n",
        encoding="utf-8",
    )
    (adr / "0002-next.md").write_text(
        "# ADR-0002: Next\n\n- **Status:** Accepted\n- **Supersedes:** ADR-0001\n\n"
        "## Context\n\nB.\n",
        encoding="utf-8",
    )
    out = tmp_path_factory.mktemp("bidi_page_out")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        root, destination=out, mode="full", name="bidi.html"
    )
    assert r["status"] == "ok", r.get("error")
    page = _open_page(browser, pathlib.Path(r["path"]))
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    raw = "‮‬​"
    for frag in ("#list/ADR-0001", "#detail/ADR-0001", "#graph/ADR-0001", "#context/ADR-0001"):
        page.evaluate(f"() => {{ location.hash = '{frag}'; }}")  # type: ignore[union-attr]
        page.wait_for_timeout(300)  # type: ignore[union-attr]
        text = page.evaluate(  # type: ignore[union-attr]
            "() => { const parts = [document.body.innerText];"
            " document.querySelectorAll('svg text, option')"
            ".forEach(e => parts.push(e.textContent));"
            " return parts.join('\\n'); }"
        )
        leaked = [hex(ord(ch)) for ch in raw if ch in text]
        assert not leaked, f"{frag}: raw controls {leaked} visible"
        assert "[U+202E]" in text, f"{frag}: the escaped marker is missing"
    assert not page._errors  # type: ignore[attr-defined]


def test_lineage_edges_run_between_facing_sides(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0026: a checked edge leaves the newer node's left side and ends at the
    older node's right side, so no edge crosses its own endpoints."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    geo = page.evaluate(  # type: ignore[union-attr]
        """() => { const box = id => document.querySelector(`[data-node-id="${id}"] rect`)
            .getBBox();
          const newer = box('ADR-0020'), older = box('ADR-0001');
          const path = [...document.querySelectorAll('#view-graph svg path[marker-end]')][0];
          const len = path.getTotalLength();
          const a = path.getPointAtLength(0), b = path.getPointAtLength(len);
          return { newerLeft: newer.x, olderRight: older.x + older.width,
                   start: a.x, end: b.x }; }"""
    )
    assert abs(geo["start"] - geo["newerLeft"]) < 2, geo
    assert abs(geo["end"] - geo["olderRight"]) < 2, geo


def test_focused_graph_returns_to_atlas(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: the atlas of every chain stays reachable after a record is focused."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    page.click("button.atlas-back")  # type: ignore[union-attr]
    page.wait_for_selector(".chain-card")  # type: ignore[union-attr]
    assert page.evaluate("location.hash") == "#graph"  # type: ignore[union-attr]


def test_back_from_focused_graph_restores_atlas(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0016: Back after focusing a node from the atlas shows the atlas again."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    page.click("button.atlas-back")  # type: ignore[union-attr]
    page.wait_for_selector(".chain-card")  # type: ignore[union-attr]
    page.locator('.chain-card g[data-node-id="ADR-0020"]').click()  # type: ignore[union-attr]
    page.wait_for_selector("button.atlas-back")  # type: ignore[union-attr]
    page.go_back()  # type: ignore[union-attr]
    page.wait_for_selector(".chain-card")  # type: ignore[union-attr]
    assert page.locator("button.atlas-back").count() == 0  # type: ignore[union-attr]


# ── Review round 2: renderer bounds, theming, and view-state checks ───────────


def _inline_pathological_body() -> str:
    """A near-2 MiB body that stays under the nesting limit, so every inline and
    heading path runs: long heading whitespace, unmatched openers of every kind."""
    parts = [
        ("# a" + " " * 2000 + "#a\n") * 100,
        "\n" + "[" * 200_000 + "\n\n",
        "![x" * 60_000 + "\n\n",
        "<" * 200_000 + "\n\n",
        "_a" * 100_000 + "\n\n",
        "".join("`" * (k % 40 + 1) + "x " for k in range(20_000)) + "\n\n",
        "[a](" * 50_000 + "\n\n",
    ]
    text = "".join(parts)
    pad = 2 * 1024 * 1024 - 4096 - len(text.encode("utf-8"))
    return text + ("word " * (pad // 5 + 1))[:pad]


@pytest.fixture(scope="module")
def export_inline_pathological(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export one record whose body exercises every inline scan near 2 MiB."""
    fixture_dir = tmp_path_factory.mktemp("inline_pathological_fixture")
    _write_single_record(fixture_dir, _inline_pathological_body())
    return _export(tmp_path_factory, fixture_dir, "inline_pathological")


def test_inline_pathological_body_renders_in_linear_time(
    browser: object, export_inline_pathological: pathlib.Path
) -> None:
    """AC-0010: heading whitespace and unmatched [, ![, <, _, ` and ]( openers in a
    near-2 MiB body render within 2 s, without the plain-text fallback."""
    page = _open_page(browser, export_inline_pathological)
    page.wait_for_selector("li.row")
    start = time.monotonic()
    _render_body(page)
    elapsed_ms = (time.monotonic() - start) * 1000
    info = page.evaluate(
        """() => { const c = document.querySelector('.record-content');
        return { length: c.textContent.length, headings: c.querySelectorAll('h3').length,
          fallback: c.textContent.includes('nesting deeper than 32 levels') }; }"""
    )
    assert elapsed_ms < 2000, f"rendered in {elapsed_ms:.0f} ms"
    assert not info["fallback"], "this body must parse, not fall back to plain text"
    assert info["headings"] == 100, info
    # The 200,000 characters of heading padding are trimmed; the rest is all text.
    assert info["length"] > 1_650_000, info["length"]


@pytest.fixture(scope="module")
def export_wrapped_list(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export one record whose list items wrap onto indented continuation lines."""
    body = (
        "- **Reviewer brief** — entry points with two modes of\n"
        "    operation, each wrapped onto a continuation line\n"
        "- second item\n"
        "  continues here too\n\n"
        "After the list.\n"
    )
    fixture_dir = tmp_path_factory.mktemp("wrapped_list_fixture")
    _write_single_record(fixture_dir, body)
    return _export(tmp_path_factory, fixture_dir, "wrapped_list")


def test_wrapped_list_item_stays_in_its_bullet(
    browser: object, export_wrapped_list: pathlib.Path
) -> None:
    """AC-0010: an indented continuation line joins its list item instead of
    becoming a code block or a separate paragraph."""
    page = _open_page(browser, export_wrapped_list)
    page.wait_for_selector("li.row")
    _render_body(page)
    info = page.evaluate(
        """() => { const c = document.querySelector('.record-content');
        return { items: [...c.querySelectorAll('li')].map(l => l.textContent),
          pres: c.querySelectorAll('pre').length }; }"""
    )
    assert info["pres"] == 0, info
    assert info["items"] == [
        "Reviewer brief — entry points with two modes of operation, each wrapped onto a "
        "continuation line",
        "second item continues here too",
    ], info["items"]


def _contrast(page: object, selector: str) -> float:
    """WCAG contrast ratio between an element's text colour and the nearest
    opaque background behind it."""
    return page.evaluate(  # type: ignore[union-attr, no-any-return]
        """(sel) => { const el = document.querySelector(sel);
        const rgb = s => s.match(/[\\d.]+/g).map(Number);
        const lum = c => { const v = c.slice(0, 3).map(x => { x /= 255;
          return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
          return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
        let bg = null, n = el;
        while (n && n.nodeType === 1) { const c = rgb(getComputedStyle(n).backgroundColor);
          if (c.length < 4 || c[3] > 0.95) { if (c.length >= 3 && !(c.length === 4 && c[3] === 0))
            { bg = c; break; } } n = n.parentElement; }
        if (!bg) bg = rgb(getComputedStyle(document.body).backgroundColor);
        const fg = rgb(getComputedStyle(el).color);
        const a = lum(fg), b = lum(bg);
        return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); }""",
        selector,
    )


def _region(view: str) -> str:
    """CSS selector of the region that shows `view`: the detail zone is not a view."""
    return "#detail-body" if view == "detail" else f"#view-{view}"


def _show(page: object, view: str, record_id: str) -> None:
    """Route to `view` with `record_id` picked and wait until that region shows it."""
    page.evaluate(f"() => {{ location.hash = '#{view}/{record_id}'; }}")  # type: ignore[union-attr]
    if view == "detail":
        page.wait_for_function(  # type: ignore[union-attr]
            "(id) => document.getElementById('detail-body').textContent.includes(id)",
            arg=record_id,
        )
    else:
        page.wait_for_function(  # type: ignore[union-attr]
            f"() => !document.getElementById('view-{view}').hidden"
        )


def test_links_are_readable_in_both_themes(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0025: the superseded-by link inside the list banner reaches 4.5:1
    contrast in light and dark themes. (Test exports have no source links.)"""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    for choice in ("light", "dark"):
        page.emulate_media(color_scheme=choice)
        ratio = _contrast(page, "li.row .supersede-banner a")
        assert ratio >= 4.5, f"{choice}: banner link contrast {ratio:.2f}"


def test_unknown_record_shows_not_in_export_in_every_view(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0016: an unknown record ID says it is not in this export in the graph,
    context and detail views."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    for view in ("graph", "context", "detail"):
        page.evaluate(f"() => {{ location.hash = '#{view}/ADR-9999'; }}")
        page.wait_for_function(
            f"() => document.querySelector('{_region(view)}').textContent.includes('ADR-9999')"
        )
        text = page.locator(_region(view)).text_content() or ""
        assert "ADR-9999 is not in this export." in text, (view, text[:200])


@pytest.fixture(scope="module")
def export_long_and_related(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """ADR-0001 has a long body (opened by default) and is superseded by ADR-0002,
    so its detail view mixes an open body with a closed relationships section."""
    root = tmp_path_factory.mktemp("long_related_fixture")
    adr = root / "docs" / "adr"
    adr.mkdir(parents=True)
    head = "- **Status:** Accepted\n- **Supersedes:** {s}\n- **Superseded by:** {b}\n"
    (adr / "0001-old.md").write_text(
        "# ADR-0001: Old\n\n"
        + head.format(s="none", b="ADR-0002")
        + "\n## Context\n\n"
        + "Long body text. " * 400
        + "\n",
        encoding="utf-8",
    )
    (adr / "0002-new.md").write_text(
        "# ADR-0002: New\n\n" + head.format(s="ADR-0001", b="none") + "\n## Context\n\nNew.\n",
        encoding="utf-8",
    )
    return _export(tmp_path_factory, root, "long_related")


def test_expand_all_opens_every_section_on_first_click(
    browser: object, export_long_and_related: pathlib.Path
) -> None:
    """AC-0016: with the long body open and relationships closed, the button says
    Expand all and its first activation opens every section."""
    page = _open_page(browser, export_long_and_related)
    page.wait_for_selector("li.row")
    _render_body(page)
    page.wait_for_selector("#detail-body .rel-details")
    assert page.locator("#expand-all-btn").text_content() == "Expand all"
    page.click("#expand-all-btn")
    still_closed = page.evaluate(
        "() => [...document.querySelectorAll('#detail-body details')].filter(d => !d.open).length"
    )
    assert still_closed == 0
    assert page.locator("#expand-all-btn").text_content() == "Collapse all"


def test_reset_filters_keeps_keyboard_focus(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0016: after Reset filters removes itself, focus lands on the view heading."""
    page = _open_page(browser, export_mixed)
    page.locator("#search-input").fill("zzzzz-no-match")
    page.locator(".reset-btn").focus()
    page.keyboard.press("Enter")
    page.wait_for_selector("li.row")
    focused = page.evaluate(
        "() => [document.activeElement.tagName, document.activeElement.textContent]"
    )
    assert focused == ["H2", "Decided records"], focused


def test_strike_through_marks_full_supersession_only(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """A record superseded only in part stays in force: its ID is not struck
    through, while a fully superseded record's ID is."""
    page = _open_page(browser, export_mixed)
    page.evaluate("() => { location.hash = '#list'; }")
    page.wait_for_selector("#view-list li.row")
    deco = page.evaluate(
        """() => Object.fromEntries([...document.querySelectorAll('#view-list li.row')].map(li =>
          [li.querySelector('.rid').textContent,
           getComputedStyle(li.querySelector('.rid')).textDecorationLine]))"""
    )
    assert deco["ADR-0002"] == "line-through", deco  # fully superseded by ADR-0003
    assert deco["ADR-0001"] == "underline", deco  # superseded in part by ADR-0020
    assert deco["ADR-0005" if "ADR-0005" in deco else "ADR-0030"] == "none", deco


def test_atlas_draws_and_labels_cycle_relationships(
    browser: object, export_cycle: pathlib.Path
) -> None:
    """AC-0026: a cyclic chain's atlas card draws its cycle relationships and
    labels each one "cycle"."""
    page = _open_page(browser, export_cycle)
    page.wait_for_selector("li.row")
    _navigate_graph(page)
    page.wait_for_selector(".chain-card svg")
    info = page.evaluate(
        """() => { const svg = document.querySelector('.chain-card svg');
        return { arcs: svg.querySelectorAll('path[stroke-dasharray]').length,
          labels: [...svg.querySelectorAll('text')].filter(t => t.textContent === 'cycle'
            && !t.closest('[data-node-id]')).length }; }"""
    )
    assert info["arcs"] == 3 and info["labels"] == 3, info


def test_hostile_titles_and_status_stay_inert_in_every_view(
    browser: object, export_hostile: pathlib.Path
) -> None:
    """Hostile H1 and Status values render as literal text in list, graph,
    context and detail, and never execute or load anything."""
    page = _open_page(browser, export_hostile)
    page.wait_for_selector("li.row")
    for view in ("list", "graph", "context", "detail"):
        _show(page, view, "ADR-0001")
        info = page.evaluate(
            f"""() => {{ const v = document.querySelector('{_region(view)}');
            return {{ scripts: v.querySelectorAll('script, img, iframe').length,
              text: v.textContent }}; }}"""
        )
        assert info["scripts"] == 0, view
        if view in ("list", "detail"):
            assert '<script>alert("xss")</script>' in info["text"], view
    assert page.evaluate("() => document.cookie") == ""
    assert not page._errors  # type: ignore[attr-defined]
    assert not page._non_file_requests  # type: ignore[attr-defined]


@pytest.fixture(scope="module")
def export_bidi_paths(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """A record whose file name carries RLM and ALM marks, exported with a caller
    assertion whose endpoint carries an RLM mark."""
    root = tmp_path_factory.mktemp("bidi_paths_fixture")
    adr = root / "docs" / "adr"
    adr.mkdir(parents=True)
    head = (
        "- **Status:** Accepted\n- **Date:** 2024-03-15\n- **Supersedes:** none\n"
        "- **Superseded by:** none\n- **Related:** a wrapped value\n  that continues here\n"
    )
    (adr / "0001-left‏right؜.md").write_text(
        "# ADR-0001: Marked name\n\n" + head + "\n## Context\n\nBody.\n", encoding="utf-8"
    )
    (adr / "0002-plain.md").write_text(
        "# ADR-0002: Plain\n\n" + head + "\n## Context\n\nBody.\n", encoding="utf-8"
    )
    out = tmp_path_factory.mktemp("browser_bidi_paths")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        root,
        destination=out,
        mode="full",
        name="bidi_paths.html",
        assertions=[{"from": "ADR-0002", "to": "ADR-0001‏", "text": "wider‎guidance"}],
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


def test_paths_and_assertion_endpoints_escape_directional_marks(
    browser: object, export_bidi_paths: pathlib.Path
) -> None:
    """AC-0010: source paths and caller-assertion endpoints beside trust labels show
    RLM, ALM and LRM as visible escapes in detail and context views."""
    page = _open_page(browser, export_bidi_paths)
    page.wait_for_selector("li.row")
    raw = "‏‎؜"
    for view in ("detail", "context"):
        for rid in ("ADR-0001", "ADR-0002"):
            _show(page, view, rid)
            text = page.locator(_region(view)).text_content() or ""
            assert not any(c in text for c in raw), (view, rid)
    _show(page, "detail", "ADR-0001")
    detail = page.locator("#detail-body").text_content() or ""
    assert "0001-left[U+200F]right[U+061C].md" in detail, detail[:400]
    page.evaluate("() => { location.hash = '#context/ADR-0002'; }")
    page.wait_for_function("() => !document.getElementById('view-context').hidden")
    context = page.locator("#view-context .assert-list").text_content() or ""
    assert "ADR-0001[U+200F]" in context and "wider[U+200E]guidance" in context, context


def test_detail_shows_every_header_field_exactly(
    browser: object, export_bidi_paths: pathlib.Path
) -> None:
    """Exact headers: the detail view lists each header-region field by its label
    and recorded value, including `none` supersession values."""
    page = _open_page(browser, export_bidi_paths)
    page.wait_for_selector("li.row")
    page.evaluate("() => { location.hash = '#detail/ADR-0002'; }")
    page.wait_for_selector("#detail-body .meta-table")
    rows = page.evaluate(
        """() => [...document.querySelectorAll('#detail-body .meta-table tr')]
          .map(tr => [tr.cells[0].textContent, tr.cells[1].textContent])"""
    )
    assert ["Date", "2024-03-15"] in rows, rows
    assert ["Related", "a wrapped value\n  that continues here"] in rows, rows
    assert [r[0] for r in rows].count("Status") == 1, rows
    assert ["Supersedes", "none"] in rows, rows
    assert ["Superseded by", "none"] in rows, rows


def test_caller_assertion_is_drawn_and_listed_in_the_graph(
    browser: object, export_bidi_paths: pathlib.Path
) -> None:
    """AC-0026: a caller assertion reaches the graph view as a navigation-only
    relationship, drawn and listed with the same identity."""
    page = _open_page(browser, export_bidi_paths)
    page.wait_for_selector("li.row")
    page.evaluate("() => { location.hash = '#graph/ADR-0002'; }")
    page.wait_for_selector("#view-graph .graph-note")
    listed = page.evaluate(
        "() => [...document.querySelectorAll('.lineage-text-list li, .lineage-text li.lt-rel')]"
        ".map(li => li.textContent)"
    )
    assert any("[navigation_only · caller_asserted]" in t for t in listed), listed


# ── Review round 3 ─────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def export_chain_assertions(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """ADR-0002 supersedes ADR-0001; ADR-0003 stands alone. Assertions join two
    chain members (0002→0001) and a chain member to an outside record (0002→0003)."""
    root = tmp_path_factory.mktemp("chain_assert_fixture")
    _build_corpus(
        root,
        [
            (1, "Old", "- **Status:** Superseded\n- **Superseded by:** ADR-0002\n"),
            (2, "New", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"),
            (3, "Other", "- **Status:** Accepted\n"),
        ],
    )
    out = tmp_path_factory.mktemp("browser_chain_assert")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        root,
        destination=out,
        mode="full",
        name="chain_assert.html",
        assertions=[
            {"from": "ADR-0002", "to": "ADR-0001", "text": "in chain"},
            {"from": "ADR-0002", "to": "ADR-0003", "text": "outside"},
        ],
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


def test_caller_assertions_are_drawn_in_chain_and_as_satellites(
    browser: object, export_chain_assertions: pathlib.Path
) -> None:
    """AC-0026: both caller assertions touching the selected record are drawn in
    the diagram — one between chain members, one to a satellite — and listed with
    the same identities in the text equivalent."""
    page = _open_page(browser, export_chain_assertions)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0002")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    drawn = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph svg [data-rel]')]"
        ".map(e => e.dataset.rel)"
    )
    listed = page.evaluate(
        "() => [...document.querySelectorAll('.lineage-text li.lt-rel')].map(e => e.dataset.rel)"
    )
    assert sorted(drawn) == sorted(listed), (drawn, listed)
    assert "ADR-0002|guidance|ADR-0001|navigation_only" in drawn, drawn
    assert "ADR-0002|guidance|ADR-0003|navigation_only" in drawn, drawn


def test_partial_edges_differ_by_line_style_in_focus_and_atlas(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0026: partial supersession is a hollow double line with an "in part"
    label in the focused diagram and in the atlas, not colour alone."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    widths = page.evaluate(
        """() => Object.fromEntries([...document.querySelectorAll('#view-graph svg [data-rel]')]
          .map(e => [e.dataset.rel.split('|')[1], e.getAttribute('stroke-width')]))"""
    )
    assert widths.get("supersedes_in_part") == "4", widths
    page.click("button.atlas-back")
    page.wait_for_selector(".chain-card svg")
    info = page.evaluate(
        """() => { const card = [...document.querySelectorAll('.chain-card')]
            .find(c => c.querySelector('[data-node-id="ADR-0020"]'));
          return { labels: [...card.querySelectorAll('text')].map(t => t.textContent),
            wide: card.querySelectorAll('path[stroke-width="3.5"]').length }; }"""
    )
    assert "in part" in info["labels"] and info["wide"] == 1, info


@pytest.fixture(scope="module")
def export_bidi_status(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """One record whose Status carries an RLO control."""
    root = tmp_path_factory.mktemp("bidi_status_fixture")
    _build_corpus(root, [(1, "Bidi status", "- **Status:** Acc‮epted\n")])
    return _export(tmp_path_factory, root, "bidi_status")


def test_status_filter_text_is_escaped_in_no_results(
    browser: object, export_bidi_status: pathlib.Path
) -> None:
    """AC-0006/AC-0010: the active status shown in the no-results message and the
    live region uses the visible escape, never the raw control."""
    page = _open_page(browser, export_bidi_status)
    page.evaluate("() => { location.hash = '#list'; }")
    page.wait_for_selector("#view-list li.row")
    page.select_option("#status-filter", index=1)
    page.locator("#search-input").fill("zzzz-no-match")
    page.wait_for_selector("#view-list .empty-msg")
    msg = page.locator("#view-list .empty-msg").text_content() or ""
    live = page.locator("#live-region").text_content() or ""
    for text in (msg, live):
        assert "‮" not in text and "Acc[U+202E]epted" in text, text


def test_unknown_route_id_is_escaped_and_capped(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """A record ID taken from the URL is untrusted: its controls are escaped and
    its length capped in every not-in-export message."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    hostile = "ADR-‮" + "x" * 300
    for view in ("graph", "context", "detail"):
        page.evaluate(
            "([v, h]) => { location.hash = '#' + v + '/' + encodeURIComponent(h); }",
            [view, hostile],
        )
        page.wait_for_function(
            f"() => document.querySelector('{_region(view)}').textContent"
            ".includes('is not in this export.')"
        )
        text = page.locator(f"{_region(view)} :is(.empty-msg, .empty)").first.text_content() or ""
        assert "‮" not in text and "[U+202E]" in text, (view, text[:80])
        assert len(text) < 100, (view, len(text))


def test_damaged_data_island_shows_a_recovery_alert(
    browser: object, export_mixed: pathlib.Path, tmp_path: pathlib.Path
) -> None:
    """FE-F4: an export whose data island cannot be parsed shows a role=alert
    message inside the main area and raises no page error."""
    html = export_mixed.read_text(encoding="utf-8")
    start = html.index('<script type="application/json" id="nav-data">')
    end = html.index("</script>", start)
    damaged = html[:start] + '<script type="application/json" id="nav-data">{bad' + html[end:]
    target = tmp_path / "damaged.html"
    target.write_text(damaged, encoding="utf-8")
    page = _open_page(browser, target)
    alert = page.locator('#app-main [role="alert"]')
    alert.wait_for()
    assert "Run the export again" in (alert.text_content() or "")
    assert not page._errors  # type: ignore[attr-defined]


def test_expand_label_follows_sections_toggled_by_hand(
    browser: object, export_long_and_related: pathlib.Path
) -> None:
    """After Expand all, closing one section by hand flips the label back to
    Expand all, so the button always names what it will do."""
    page = _open_page(browser, export_long_and_related)
    page.wait_for_selector("li.row")
    _render_body(page)
    page.wait_for_selector("#detail-body .rel-details")
    page.click("#expand-all-btn")
    assert page.locator("#expand-all-btn").text_content() == "Collapse all"
    page.locator("#detail-body .rel-details summary").click()
    page.wait_for_function(
        "() => document.getElementById('expand-all-btn').textContent === 'Expand all'"
    )


def test_supersession_state_is_named_and_marked_in_both_graph_views(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """Graph nodes name their supersession state in their accessible name, and
    the atlas marks IDs like the list: struck through for full, underlined for
    partial."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    label = page.get_attribute('[data-node-id="ADR-0001"]', "aria-label") or ""
    assert label.endswith(", superseded in part"), label
    page.click("button.atlas-back")
    page.wait_for_selector(".chain-card svg")
    deco = page.evaluate(
        """() => Object.fromEntries(['ADR-0001', 'ADR-0002', 'ADR-0020'].map(id =>
          [id, document.querySelector(`.chain-card [data-node-id="${id}"] text.ln-id`)
            .getAttribute('text-decoration')]))"""
    )
    assert deco == {"ADR-0001": "underline", "ADR-0002": "line-through", "ADR-0020": None}, deco


@pytest.fixture(scope="module")
def export_tag_title(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """One record whose title hides ASCII in Unicode tag characters."""
    root = tmp_path_factory.mktemp("tag_title_fixture")
    _build_corpus(root, [(1, "Visible\U000e0068\U000e0069 title", "- **Status:** Accepted\n")])
    return _export(tmp_path_factory, root, "tag_title")


def test_tag_characters_are_visibly_escaped(
    browser: object, export_tag_title: pathlib.Path
) -> None:
    """Tag characters (above U+FFFF) render as visible escapes in list and detail."""
    page = _open_page(browser, export_tag_title)
    page.wait_for_selector("li.row")
    for view in ("list", "detail"):
        _show(page, view, "ADR-0001")
        text = page.locator(_region(view)).text_content() or ""
        assert "\U000e0068" not in text and "[U+E0068]" in text, (view, text[:200])


def test_bounded_notice_is_readable_in_dark_mode(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """The bounded-mode body notice and its source link keep 4.5:1 contrast in the
    dark theme. Git is faked so the export carries a source link."""
    import unittest.mock as _mock

    def fake_git(args: list, cwd: str, timeout: int = 5) -> str | None:
        if args == ["config", "--get", "remote.origin.url"]:
            return "https://github.com/owner/repo.git"
        if args == ["rev-parse", "HEAD"]:
            return "e" * 40
        if args[0] == "status":
            return " M docs/adr/0001-alpha.md"
        if args[:3] == ["branch", "-r", "--contains"]:
            return ""
        return None

    out = tmp_path_factory.mktemp("browser_bounded")
    with (
        _mock.patch.object(EXPLORER, "_run_git", side_effect=fake_git),
        _mock.patch.object(EXPLORER, "_git_root_matches", return_value=True),
    ):
        r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
            FIXTURE_MIXED, destination=out, mode="bounded", name="bounded.html"
        )
    assert r["status"] == "ok", r.get("error")
    page = _open_page(browser, pathlib.Path(r["path"]))
    page.wait_for_selector("li.row")
    page.emulate_media(color_scheme="dark")
    page.evaluate("() => { location.hash = '#detail/ADR-0001'; }")
    page.wait_for_selector("#detail-body .bounded-notice a")
    assert _contrast(page, "#detail-body .bounded-notice") >= 4.5
    assert _contrast(page, "#detail-body .bounded-notice a") >= 4.5


# ── Review round 4 (T8) ───────────────────────────────────────────────────────

_BOXES_JS = """(scope) => {
  const root = document.querySelector(scope);
  const box = e => { const b = e.getBBox(); return {x: b.x, y: b.y, w: b.width, h: b.height}; };
  const plates = [...root.querySelectorAll('rect')].filter(r =>
    r.nextSibling && r.nextSibling.classList && r.nextSibling.classList.contains('edge-label'))
    .map(box);
  const nodes = [...root.querySelectorAll('[data-node-id] > rect:first-child')].map(box);
  const heads = [...root.querySelectorAll('path[marker-end]')].map(p => {
    const n = p.getTotalLength(), a = p.getPointAtLength(n);
    const b = p.getPointAtLength(Math.max(0, n - 10));
    return {x: Math.min(a.x, b.x), y: Math.min(a.y, b.y) - 3.5,
            w: Math.abs(a.x - b.x), h: Math.abs(a.y - b.y) + 7}; });
  const vb = root.viewBox.baseVal;
  return {plates, nodes, heads, view: {x: vb.x, y: vb.y, w: vb.width, h: vb.height}};
}"""


def _hit(a: dict, b: dict) -> bool:
    return (
        a["x"] < b["x"] + b["w"]
        and b["x"] < a["x"] + a["w"]
        and a["y"] < b["y"] + b["h"]
        and b["y"] < a["y"] + a["h"]
    )


def _assert_plates_clear(geo: dict, where: str) -> None:
    plates = geo["plates"]
    assert plates, f"{where}: no label plates drawn"
    for i, p in enumerate(plates):
        for q in plates[i + 1 :]:
            assert not _hit(p, q), (where, "plate overlaps plate", p, q)
        for n in geo["nodes"]:
            assert not _hit(p, n), (where, "plate overlaps node", p, n)
        for h in geo["heads"]:
            assert not _hit(p, h), (where, "plate overlaps arrowhead", p, h)
        v = geo["view"]
        inside = (
            p["x"] >= v["x"]
            and p["y"] >= v["y"]
            and p["x"] + p["w"] <= v["x"] + v["w"]
            and p["y"] + p["h"] <= v["y"] + v["h"]
        )
        assert inside, (where, "plate clipped by the drawing edge", p, v)


@pytest.fixture(scope="module")
def export_fan_in(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """ADR-0001 is superseded in part by ADR-0002..ADR-0005, each with its own
    scope, so four partial edges enter one node."""
    root = tmp_path_factory.mktemp("fan_in_fixture")
    parts = "; ".join(f"ADR-000{k} D{k}" for k in range(2, 6))
    records = [(1, "Base", f"- **Status:** Accepted\n- **Superseded in part:** {parts}\n")]
    records += [
        (k, f"Part {k}", f"- **Status:** Accepted\n- **Supersedes in part:** ADR-0001 D{k}\n")
        for k in range(2, 6)
    ]
    _build_corpus(root, records)
    return _export(tmp_path_factory, root, "fan_in")


def test_fan_in_labels_stay_clear_in_focus_and_atlas(
    browser: object, export_fan_in: pathlib.Path
) -> None:
    """R4-FE-1: on fan-in, no two `in part` plates intersect, and no plate meets a
    node box or an arrowhead box, in the focused graph and the atlas."""
    page = _open_page(browser, export_fan_in)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    _assert_plates_clear(page.evaluate(_BOXES_JS, "#view-graph .lineage-wrap svg"), "focused")
    page.click("button.atlas-back")
    page.wait_for_selector(".chain-card svg")
    _assert_plates_clear(page.evaluate(_BOXES_JS, ".chain-card svg"), "atlas")


def test_arrowheads_keep_one_size_on_full_and_partial_edges(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """R4-FE-2: markers use user-space units, so partial (thicker) edges do not
    get larger arrowheads than full edges."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    units = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph marker')]"
        ".map(m => m.getAttribute('markerUnits'))"
    )
    assert units and set(units) == {"userSpaceOnUse"}, units


@pytest.fixture(scope="module")
def export_column_assertion(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """ADR-0004 supersedes ADR-0001..0003, which share one column; a caller
    assertion joins ADR-0001 and ADR-0003 with ADR-0002 between them."""
    root = tmp_path_factory.mktemp("column_assert_fixture")
    recs = [
        (k, f"Old {k}", "- **Status:** Superseded\n- **Superseded by:** ADR-0004\n")
        for k in range(1, 4)
    ]
    recs.append((
        4,
        "New",
        "- **Status:** Accepted\n- **Supersedes:** ADR-0001; ADR-0002; ADR-0003\n",
    ))
    _build_corpus(root, recs)
    out = tmp_path_factory.mktemp("browser_column_assert")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        root,
        destination=out,
        mode="full",
        name="column_assert.html",
        assertions=[{"from": "ADR-0001", "to": "ADR-0003", "text": "same column"}],
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


def test_in_chain_assertion_never_passes_beneath_a_node(
    browser: object, export_column_assertion: pathlib.Path
) -> None:
    """R4-FE-3: an asserted edge between two same-column chain members has no
    point inside another node's box, and its label plate is clear."""
    page = _open_page(browser, export_column_assertion)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    inside = page.evaluate(
        """() => { const svg = document.querySelector('#view-graph .lineage-wrap svg');
          const p = svg.querySelector('[data-rel="ADR-0001|guidance|ADR-0003|navigation_only"]');
          const others = [...svg.querySelectorAll('[data-node-id]')]
            .filter(g => !['ADR-0001', 'ADR-0003'].includes(g.dataset.nodeId))
            .map(g => g.querySelector('rect').getBBox());
          const n = p.getTotalLength(), hits = [];
          for (let s = 0; s <= n; s += 2) { const q = p.getPointAtLength(s);
            for (const b of others)
              if (q.x > b.x && q.x < b.x + b.width && q.y > b.y && q.y < b.y + b.height)
                hits.push([q.x, q.y]); }
          return hits; }"""
    )
    assert inside == [], inside[:5]
    _assert_plates_clear(page.evaluate(_BOXES_JS, "#view-graph .lineage-wrap svg"), "asserted")


def test_expand_all_label_is_unchanged_on_a_view_without_sections(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """R4-FE-4: on the list view there is nothing to expand, so the control is disabled and
    the label stays."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    assert page.locator("#expand-all-btn").is_disabled()
    assert page.locator("#expand-all-btn").text_content() == "Expand all"


def test_text_list_node_buttons_align_to_the_top(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """R4-FE-5: node buttons in the text list align to the top of their item."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    align = page.evaluate(
        "() => getComputedStyle(document.querySelector('.lt-node-btn')).verticalAlign"
    )
    assert align == "top", align


def test_partial_edges_are_hollow_and_labelled_in_both_views(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """R4-QE-4: partial edges carry the white inner stroke and an `in part` label
    in the focused graph and the atlas; full edges carry neither."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    focused = page.evaluate(
        """() => { const svg = document.querySelector('#view-graph .lineage-wrap svg');
          return { inner: svg.querySelectorAll('[data-inner="part"]').length,
            labels: [...svg.querySelectorAll('.edge-label')].map(t => t.textContent) }; }"""
    )
    assert focused["inner"] == 1, focused
    assert any(t.startswith("in part") for t in focused["labels"]), focused
    page.click("button.atlas-back")
    page.wait_for_selector(".chain-card svg")
    atlas = page.evaluate(
        """() => [...document.querySelectorAll('.chain-card')].map(c => ({
          ids: [...c.querySelectorAll('[data-node-id]')].map(g => g.dataset.nodeId),
          inner: c.querySelectorAll('[data-inner="part"]').length,
          labels: [...c.querySelectorAll('.edge-label')].map(t => t.textContent) }))"""
    )
    part = next(c for c in atlas if "ADR-0020" in c["ids"])
    full = next(c for c in atlas if "ADR-0003" in c["ids"])
    assert part["inner"] == 1 and "in part" in part["labels"], part
    assert full["inner"] == 0 and not full["labels"], full


def test_graph_focus_ring_reaches_3_to_1_and_clears_the_supersession_ring(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """R4-EXP-1: the focus indicator's outer ring reaches 3:1 against the canvas
    in both themes and sits outside the selected node's supersession ring."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    for choice in ("light", "dark"):
        page.emulate_media(color_scheme=choice)
        _navigate_graph(page, "ADR-0001")
        info = page.evaluate(
            """() => { const g = document.querySelector('#view-graph [data-node-id="ADR-0001"]');
              const outer = g.querySelector('.focus-ring rect');
              const ring = g.querySelector('.sup-ring');
              const wrap = document.querySelector('#view-graph .lineage-wrap');
              let bg = 'rgba(0, 0, 0, 0)';
              for (let e = wrap; e && bg === 'rgba(0, 0, 0, 0)'; e = e.parentElement)
                bg = getComputedStyle(e).backgroundColor;
              return { stroke: getComputedStyle(outer).stroke, bg,
                gap: ring ? +ring.getAttribute('x') - (+outer.getAttribute('x') + 1) : 99 }; }"""
        )
        rgb = [float(v) for v in info["stroke"][info["stroke"].index("(") + 1 : -1].split(",")[:3]]
        bg = [float(v) for v in info["bg"][info["bg"].index("(") + 1 : -1].split(",")[:3]]

        def lum(c: list[float]) -> float:
            v = [x / 255 for x in c]
            v = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in v]
            return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]

        a, b = lum(rgb), lum(bg)
        ratio = (max(a, b) + 0.05) / (min(a, b) + 0.05)
        assert ratio >= 3, (choice, info, ratio)
        assert info["gap"] >= 1, (choice, info)


def test_dark_first_paint_without_scripts(browser: object, export_mixed: pathlib.Path) -> None:
    """R4-EXP-2: with scripts off and a dark system preference, the page paints
    its dark styles: the header and page backgrounds (the stylesheet declares both schemes)."""
    context = browser.new_context(  # type: ignore[union-attr]
        offline=True, java_script_enabled=False, color_scheme="dark"
    )
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    info = page.evaluate(
        """() => ({ scheme: getComputedStyle(document.documentElement).colorScheme,
          header: getComputedStyle(document.querySelector('.page-header')).backgroundColor,
          page: getComputedStyle(document.body).backgroundColor })"""
    )
    context.close()
    assert info["scheme"] == "light dark", info
    assert info["header"] == "rgb(22, 24, 29)", info
    assert info["page"] == "rgb(15, 17, 20)", info


def test_partial_id_underline_style_matches_across_views(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """R4-EXP-4: the partially superseded ID uses a solid underline in the list
    and in both graph views."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    style = page.evaluate(
        """() => { const rid = [...document.querySelectorAll('li.row .rid')]
            .find(e => e.textContent === 'ADR-0001');
          const cs = getComputedStyle(rid);
          return [cs.textDecorationLine, cs.textDecorationStyle]; }"""
    )
    assert style == ["underline", "solid"], style
    _navigate_graph(page, "ADR-0001")
    deco = page.evaluate(
        "() => document.querySelector('#view-graph [data-node-id=\"ADR-0001\"] text.ln-id')"
        ".getAttribute('text-decoration')"
    )
    assert deco == "underline", deco


def test_wrapped_status_shows_its_own_row(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """R4-ADV-2: a wrapped Status shows the header Status row beside the
    lifecycle row; a one-line Status shows a single Status row."""
    root = tmp_path_factory.mktemp("wrapped_status_fixture")
    _build_corpus(
        root,
        [
            (1, "Wrapped", "- **Status:** Accepted\n  with a wrapped qualifier\n"),
            (2, "Plain", "- **Status:** Accepted <!-- note -->\n"),
        ],
    )
    page = _open_page(browser, _export(tmp_path_factory, root, "wrapped_status"))
    page.wait_for_selector("li.row")
    counts = {}
    for rid in ("ADR-0001", "ADR-0002"):
        page.evaluate(f"() => {{ location.hash = '#detail/{rid}'; }}")
        page.wait_for_function(
            "(rid) => (document.querySelector('#detail-body .state-line') || {}).textContent"
            "?.includes(rid)",
            arg=rid,
        )
        counts[rid] = page.evaluate(
            """() => [...document.querySelectorAll('#detail-body .meta-table tr')]
              .filter(tr => tr.cells[0].textContent === 'Status').length"""
        )
    assert counts == {"ADR-0001": 2, "ADR-0002": 1}, counts


# ── Review round 5 ────────────────────────────────────────────────────────────

_NEAREST_EDGE_JS = """(scope) => {
  const root = document.querySelector(scope);
  const paths = [...root.querySelectorAll('path[data-rel]')];
  const dist = (p, x, y) => { const n = p.getTotalLength(); let best = Infinity;
    for (let s = 0; s <= n; s += 1) { const q = p.getPointAtLength(s);
      best = Math.min(best, Math.hypot(q.x - x, q.y - y)); }
    return best; };
  return [...root.querySelectorAll('.edge-label[data-for]')].map(t => {
    const x = +t.getAttribute('x'), y = +t.getAttribute('y');
    const nearest = paths.map(p => [dist(p, x, y), p.dataset.rel]).sort((a, b) => a[0] - b[0])[0];
    return {own: t.dataset.for, nearest: nearest[1], text: t.textContent}; });
}"""


def test_fan_in_labels_sit_on_their_own_edges(
    browser: object, export_fan_in: pathlib.Path
) -> None:
    """On fan-in, the edge nearest each scope label is the edge the label names,
    and in the focused graph the label carries that edge's own scope."""
    page = _open_page(browser, export_fan_in)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    focused = page.evaluate(_NEAREST_EDGE_JS, "#view-graph .lineage-wrap svg")
    assert len(focused) == 4, focused
    for label in focused:
        assert label["nearest"] == label["own"], label
        source = label["own"].split("|")[0]  # e.g. ADR-0003 carries scope D3
        assert label["text"] == f"in part · D{int(source[-4:])}", label
    page.click("button.atlas-back")
    page.wait_for_selector(".chain-card svg")
    atlas = page.evaluate(_NEAREST_EDGE_JS, ".chain-card svg")
    assert len(atlas) == 4, atlas
    for label in atlas:
        assert label["nearest"] == label["own"], label


@pytest.fixture(scope="module")
def export_partial_and_asserted(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """ADR-0001 is superseded in part by ADR-0003 with a long scope; ADR-0002
    shares ADR-0001's column, and a caller assertion targets ADR-0001 from it."""
    root = tmp_path_factory.mktemp("partial_asserted_fixture")
    _build_corpus(
        root,
        [
            (
                1,
                "Base",
                "- **Status:** Accepted\n- **Superseded in part:** ADR-0003 D10, D11, D12, D13\n",
            ),
            (2, "Sibling", "- **Status:** Superseded\n- **Superseded by:** ADR-0003\n"),
            (
                3,
                "New",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0002\n"
                "- **Supersedes in part:** ADR-0001 D10, D11, D12, D13\n",
            ),
        ],
    )
    out = tmp_path_factory.mktemp("browser_partial_asserted")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        root,
        destination=out,
        mode="full",
        name="partial_asserted.html",
        assertions=[{"from": "ADR-0002", "to": "ADR-0001", "text": "same column"}],
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


def test_asserted_and_long_partial_labels_stay_clear(
    browser: object, export_partial_and_asserted: pathlib.Path
) -> None:
    """The `asserted` label and the long `in part` label on the same target
    node never overlap each other, a node or an arrowhead; the long label is
    a number whose key entry gives its full scope."""
    page = _open_page(browser, export_partial_and_asserted)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    labels = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph .edge-label')].map(t => t.textContent)"
    )
    assert sorted(labels) == ["1", "asserted"], labels
    key = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph .lineage-key li')]"
        ".map(l => l.textContent)"
    )
    full = "in part · D10, D11, D12, D13 — ADR-0003 supersedes in part ADR-0001"
    assert key == [full], key
    _assert_plates_clear(page.evaluate(_BOXES_JS, "#view-graph .lineage-wrap svg"), "focused")
    _assert_labels_sound(page, "#view-graph .lineage-wrap svg", "partial and asserted")


def test_partial_edges_have_a_white_narrower_inner_stroke(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """In both views the hollow line of a partial edge is a stroke in the list zone's
    own background colour, narrower than its edge, along the same path and drawn on top of it."""
    probe = """(scope) => [...document.querySelectorAll(scope + ' [data-inner="part"]')].map(i => {
        const outer = i.previousElementSibling;
        return { color: getComputedStyle(i).stroke, inner: +i.getAttribute('stroke-width'),
          outer: +outer.getAttribute('stroke-width'),
          same: outer.getAttribute('d') === i.getAttribute('d'),
          partial: (outer.dataset.rel || '').includes('|supersedes_in_part|') }; })"""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    page.click("button.atlas-back")
    page.wait_for_selector(".chain-card svg")
    lines = page.evaluate(probe, ".chain-card")
    assert lines, "atlas"
    page_bg = page.evaluate(
        "() => getComputedStyle(document.querySelector('.worklist')).backgroundColor"
    )
    for line in lines:
        assert line["color"] == page_bg, (line, page_bg)
        assert line["same"] and line["partial"] and line["inner"] < line["outer"], line
    _navigate_graph(page, "ADR-0001")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    lines = page.evaluate(probe, "#view-graph")
    assert len(lines) == 1, lines
    line = lines[0]
    assert line["color"] == "rgb(255, 255, 255)", line
    assert line["same"] and line["partial"] and line["inner"] < line["outer"], line


def test_full_and_partial_arrowheads_render_at_one_size(
    browser: object, export_partial_and_asserted: pathlib.Path
) -> None:
    """The arrowhead drawn on a full edge and on a thicker partial edge has the
    same rendered size: marker size times the stroke width when the marker
    scales with the stroke, the marker size alone otherwise."""
    page = _open_page(browser, export_partial_and_asserted)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0003")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    sizes = page.evaluate(
        """() => [...document.querySelectorAll('#view-graph path[data-rel][marker-end]')]
          .map(p => {
          const id = p.getAttribute('marker-end').slice(5, -1);
          const m = document.getElementById(id);
          const k = m.getAttribute('markerUnits') === 'userSpaceOnUse' ? 1
            : +p.getAttribute('stroke-width');
          return { sw: +p.getAttribute('stroke-width'), solid: !p.getAttribute('stroke-dasharray'),
            w: +m.getAttribute('markerWidth') * k, h: +m.getAttribute('markerHeight') * k }; })"""
    )
    solid = [s for s in sizes if s["solid"]]
    assert {s["sw"] for s in solid} >= {2.0, 4.0}, sizes
    assert len({(s["w"], s["h"]) for s in solid}) == 1, solid


def test_partial_id_is_underlined_in_the_atlas(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """The partially superseded ID keeps the same underline in the atlas."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    _navigate_graph(page)
    page.wait_for_selector(".chain-card svg")
    deco = page.evaluate(
        "() => document.querySelector('.chain-card [data-node-id=\"ADR-0001\"] text.ln-id')"
        ".getAttribute('text-decoration')"
    )
    assert deco == "underline", deco


@pytest.mark.parametrize(
    "tail",
    [" " * 1_900_000 + "x", " " + "<!--" * 470_000],
    ids=["whitespace-run", "unclosed-openers"],
)
def test_hostile_status_line_detail_renders_in_linear_time(
    browser: object, tmp_path_factory: pytest.TempPathFactory, tail: str
) -> None:
    """A near-2 MiB single-line Status value of a hostile shape renders its
    detail view in under 2 seconds."""
    root = tmp_path_factory.mktemp("hostile_status_fixture")
    _build_corpus(root, [(1, "Hostile", f"- **Status:** Accepted{tail}\n")])
    page = _open_page(browser, _export(tmp_path_factory, root, "hostile_status"))
    page.wait_for_selector("li.row")
    page.evaluate(
        """() => { window.__t0 = performance.now(); setTimeout(() => {
          location.hash = '#detail/ADR-0001'; }, 0); }"""
    )
    # A super-linear regression fails here by name instead of hanging the run.
    page.wait_for_selector("#detail-body .meta-table", timeout=6000)
    elapsed = page.evaluate("() => performance.now() - window.__t0")
    assert elapsed < 2000, elapsed


# ── Review round 6 ────────────────────────────────────────────────────────────

_LABEL_GEOMETRY_JS = """(scope) => {
  const svg = document.querySelector(scope);
  const sample = (p, step) => { const n = p.getTotalLength(), out = [];
    for (let s = 0; s <= n; s += step) { const q = p.getPointAtLength(s); out.push([q.x, q.y]); }
    return out; };
  const lines = [...svg.querySelectorAll('path[data-rel], path[data-trunk]')]
    .map(p => ({key: p.dataset.rel || 'trunk:' + p.dataset.trunk, pts: sample(p, 1)}));
  const dist = (pts, x, y) =>
    pts.reduce((m, q) => Math.min(m, Math.hypot(q[0] - x, q[1] - y)), Infinity);
  return [...svg.querySelectorAll('.edge-label')].map(t => {
    const x = +t.getAttribute('x'), y = +t.getAttribute('y');
    const own = lines.find(l => l.key === t.dataset.for);
    const other = lines.filter(l => l !== own)
      .reduce((m, l) => Math.min(m, dist(l.pts, x, y)), Infinity);
    return {for: t.dataset.for, text: t.firstChild.textContent,
            own: own ? dist(own.pts, x, y) : null, other}; });
}"""

_HARD_CROSSINGS_JS = """(scope) => {
  const svg = document.querySelector(scope);
  const plates = [...svg.querySelectorAll('rect')].filter(r =>
    r.nextSibling && r.nextSibling.classList && r.nextSibling.classList.contains('edge-label'));
  const out = [];
  for (const p of svg.querySelectorAll('path[data-trunk], path[data-sat]')) {
    if (getComputedStyle(p.closest('g')).display === 'none') continue;
    const n = p.getTotalLength();
    for (let s = 0; s <= n; s += 1) { const q = p.getPointAtLength(s);
      for (const r of plates) { if (r.nextSibling.dataset.for === p.dataset.rel) continue;
        const b = r.getBBox();
        const inX = q.x > b.x + 0.5 && q.x < b.x + b.width - 0.5;
        if (inX && q.y > b.y + 0.5 && q.y < b.y + b.height - 0.5) {
          out.push({line: p.dataset.trunk || p.dataset.sat, label: r.nextSibling.textContent});
          s = n + 1; break; } } } }
  return out; }"""

_NEAREST_END_JS = """(scope) => {
  const svg = document.querySelector(scope);
  const ends = [...svg.querySelectorAll('path[data-rel][marker-end]')].map(p => {
    const e = p.getPointAtLength(p.getTotalLength());
    return {rel: p.dataset.rel, x: e.x, y: e.y}; });
  return [...svg.querySelectorAll('.edge-label[data-for]')].map(t => {
    const x = +t.getAttribute('x'), y = +t.getAttribute('y');
    const near = ends.map(e => [Math.hypot(e.x - x, e.y - y), e.rel])
      .sort((a, b) => a[0] - b[0])[0];
    return {own: t.dataset.for, nearest: near && near[1], text: t.firstChild.textContent}; });
}"""

_RINGS_JS = """(scope) => [...document.querySelectorAll(scope + ' .sup-ring')].map(r => {
  const b = r.getBBox(); return {x: b.x, y: b.y, w: b.width, h: b.height}; })"""


def _assert_labels_sound(page: object, scope: str, where: str) -> list[dict]:
    """Every label is clear of plates, nodes, rings, arrowheads and the border,
    lies within one plate height of its own edge, and no other line is as near
    its centre as its own line is."""
    geo = page.evaluate(_BOXES_JS, scope)  # type: ignore[union-attr]
    if geo["plates"]:
        _assert_plates_clear(geo, where)
    for ring in page.evaluate(_RINGS_JS, scope):  # type: ignore[union-attr]
        for plate in geo["plates"]:
            assert not _hit(plate, ring), (where, "plate overlaps a supersession ring", plate)
    crossings = page.evaluate(_HARD_CROSSINGS_JS, scope)  # type: ignore[union-attr]
    assert crossings == [], (
        where,
        "a bus, satellite or contextual line crosses a plate",
        crossings,
    )
    labels = page.evaluate(_LABEL_GEOMETRY_JS, scope)  # type: ignore[union-attr]
    for label in labels:
        assert label["own"] is not None, (where, "label names no drawn edge", label)
        assert label["own"] <= 13, (where, "label is away from its own edge", label)
        assert label["own"] + 0.5 < label["other"], (where, "another line is as near", label)
    return labels


@pytest.fixture(scope="module")
def export_fan_out(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """ADR-0005 supersedes three records in part, ADR-0004 also supersedes
    ADR-0001 in part with a scope too long to draw whole, and ADR-0006
    supersedes ADR-0005 in part with a 16-character label on one straight
    edge — the crowded shape of a real corpus."""
    root = tmp_path_factory.mktemp("fan_out_fixture")
    _build_corpus(
        root,
        [
            (
                1,
                "One",
                "- **Status:** Accepted\n"
                "- **Superseded in part:** ADR-0005 D6, D7; ADR-0004 D7, D8, D9\n",
            ),
            (2, "Two", "- **Status:** Accepted\n- **Superseded in part:** ADR-0005 D6\n"),
            (3, "Three", "- **Status:** Accepted\n- **Superseded in part:** ADR-0005 D2\n"),
            (4, "Four", "- **Status:** Accepted\n- **Supersedes in part:** ADR-0001 D7, D8, D9\n"),
            (
                5,
                "Five",
                "- **Status:** Accepted\n"
                "- **Supersedes in part:** ADR-0001 D6, D7; ADR-0002 D6; ADR-0003 D2\n"
                "- **Superseded in part:** ADR-0006 D1, D2\n",
            ),
            (6, "Six", "- **Status:** Accepted\n- **Supersedes in part:** ADR-0005 D1, D2\n"),
        ],
    )
    return _export(tmp_path_factory, root, "fan_out")


@pytest.mark.parametrize("selected", ["ADR-0001", "ADR-0002", "ADR-0005", "ADR-0006"])
def test_crowded_labels_stay_on_their_own_edges(
    browser: object, export_fan_out: pathlib.Path, selected: str
) -> None:
    """In a crowded chain every scope label stays beside its own edge, clear of
    every plate, node, ring and arrowhead; any label with no room is a numbered
    marker listed in the key under the drawing."""
    page = _open_page(browser, export_fan_out)
    page.wait_for_selector("li.row")
    _navigate_graph(page, selected)
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    labels = _assert_labels_sound(page, "#view-graph .lineage-wrap svg", selected)
    # Each whole label sits nearest an arrowhead at the record its own edge
    # points at; a keyed number is held only to its key entry.
    for near in page.evaluate(_NEAREST_END_JS, "#view-graph .lineage-wrap svg"):
        if near["text"].isdigit():
            continue
        target = near["own"].split("|")[2]
        assert near["nearest"].split("|")[2] == target, (selected, "label by another record", near)
    markers = [x for x in labels if x["text"].isdigit()]
    unmarked = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph .lineage-key li')]"
        ".filter(l => l.textContent.includes('no room')).map(l => l.textContent)"
    )
    assert unmarked == [], (selected, "an edge has no mark on the diagram", unmarked)
    key = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph .lineage-key li')]"
        ".map(l => l.textContent)"
    )
    partial = page.evaluate(
        "() => document.querySelectorAll("
        "'#view-graph path[data-rel*=\"supersedes_in_part\"]').length"
    )
    assert len(labels) + (len(key) - len(markers)) == partial, (labels, key)
    assert len(key) >= len(markers), (markers, key)
    page.click("button.atlas-back")
    page.wait_for_selector(".chain-card svg")
    _assert_labels_sound(page, ".chain-card svg", "atlas")


def test_maximum_length_label_sits_on_a_straight_edge(
    browser: object, export_fan_out: pathlib.Path
) -> None:
    """A label at the 16-character limit sits whole on a straight one-column edge."""
    page = _open_page(browser, export_fan_out)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0006")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    labels = _assert_labels_sound(page, "#view-graph .lineage-wrap svg", "straight")
    six = [x for x in labels if x["for"].startswith("ADR-0006|")]
    assert len(six) == 1 and len(six[0]["text"]) == 16, labels
    assert six[0]["own"] <= 1, six


@pytest.fixture(scope="module")
def export_satellites(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """ADR-0003 supersedes ADR-0002, which supersedes ADR-0001; ADR-0001 also
    names an unknown record and a caller assertion links it outside the chain,
    so its satellites must pass the checked edges to its right."""
    root = tmp_path_factory.mktemp("satellite_fixture")
    _build_corpus(
        root,
        [
            (
                1,
                "Old",
                "- **Status:** Superseded\n- **Superseded by:** ADR-0002\n"
                "- **Supersedes:** ADR-0099\n",
            ),
            (
                2,
                "Mid",
                "- **Status:** Superseded\n- **Supersedes:** ADR-0001\n"
                "- **Superseded by:** ADR-0003\n",
            ),
            (3, "New", "- **Status:** Accepted\n- **Supersedes:** ADR-0002\n"),
        ],
    )
    out = tmp_path_factory.mktemp("browser_satellites")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        root,
        destination=out,
        mode="full",
        name="satellites.html",
        assertions=[{"from": "ADR-0001", "to": "ADR-0077", "text": "outside the chain"}],
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


_SAT_RUNS_JS = """(scope) => {
  const svg = document.querySelector(scope);
  const sample = (p, step) => { const n = p.getTotalLength(), out = [];
    for (let s = 0; s <= n; s += step) {
      const q = p.getPointAtLength(s); out.push([q.x, q.y]); }
    return out; };
  const sats = [...svg.querySelectorAll('path[data-trunk], path[data-sat]')];
  const others = [...svg.querySelectorAll('path')]
    .filter(p => !p.closest('defs') && !p.dataset.trunk && !p.dataset.sat)
    .map(p => ({key: p.dataset.rel || 'inner', pts: sample(p, 1)}));
  const runOf = (limit) => { let longest = 0, worst = null;
    for (const p of sats) {
      const pts = sample(p, 2);
      for (const o of others) { let run = 0;
        for (const [x, y] of pts) {
          run = o.pts.some(q => Math.hypot(q[0] - x, q[1] - y) < limit) ? run + 1 : 0;
          if (run > longest) { longest = run; worst = o.key; } } } }
    return {longest, worst}; };
  const along = runOf(1.5), beside = runOf(4.5);
  return {sats: sats.length, longest: along.longest, worst: along.worst,
          beside: beside.longest, besideWorst: beside.worst}; }"""


def _satellite_page(browser: object, export: pathlib.Path, selected: str) -> object:
    page = _open_page(browser, export)
    page.wait_for_selector("li.row")
    _navigate_graph(page, selected)
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    return page


def _assert_satellites_clear(page: object, where: str) -> None:
    """No satellite line runs along any other line (4 consecutive 2 px samples
    within 1.5 px, about 6 px) or beside one (8 consecutive samples within
    4.5 px, about 14 px), and every label stays sound."""
    runs = page.evaluate(_SAT_RUNS_JS, "#view-graph .lineage-wrap svg")  # type: ignore[union-attr]
    assert runs["sats"] >= 1, (where, runs)
    assert runs["longest"] < 4, (where, runs)
    assert runs["beside"] < 8, (where, runs)
    _assert_labels_sound(page, "#view-graph .lineage-wrap svg", where)


def test_satellite_links_never_run_along_a_checked_edge(
    browser: object, export_satellites: pathlib.Path
) -> None:
    """With the oldest record selected, its one-sided and asserted satellite
    links and their labels never lie along another relationship's line."""
    page = _satellite_page(browser, export_satellites, "ADR-0001")
    labels = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph .edge-label')].map(t => t.textContent)"
    )
    assert sorted(labels) == ["asserted", "one-sided"], labels
    _assert_satellites_clear(page, "chain")


def _publish_with(
    tmp_path_factory: pytest.TempPathFactory,
    tag: str,
    records: list[tuple[int, str, str]],
    assertions: list[dict[str, str]],
) -> pathlib.Path:
    root = tmp_path_factory.mktemp(f"{tag}_fixture")
    _build_corpus(root, records)
    out = tmp_path_factory.mktemp(f"browser_{tag}")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        root, destination=out, mode="full", name=f"{tag}.html", assertions=assertions
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


_SAT_LAYOUTS = {
    # A cycle member with satellites, selected in the cycle's shared layer.
    "cycle": (
        [
            (
                1,
                "One",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0003; ADR-0099\n"
                "- **Superseded by:** ADR-0002\n",
            ),
            (
                2,
                "Two",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"
                "- **Superseded by:** ADR-0003\n",
            ),
            (
                3,
                "Three",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0002\n"
                "- **Superseded by:** ADR-0001\n",
            ),
        ],
        [{"from": "ADR-0001", "to": "ADR-0077", "text": "out"}],
    ),
    # Four supersessors arrive on the selected record's right side.
    "fan_in": (
        [
            (
                1,
                "Base",
                "- **Status:** Superseded\n- **Supersedes:** ADR-0099\n"
                "- **Superseded by:** ADR-0002; ADR-0003; ADR-0004; ADR-0005\n",
            )
        ]
        + [
            (k, f"New {k}", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n")
            for k in range(2, 6)
        ],
        [
            {"from": "ADR-0001", "to": "ADR-0077", "text": "out"},
            {"from": "ADR-0078", "to": "ADR-0001", "text": "in"},
        ],
    ),
    # An in-chain assertion whose route would share the bus's row gap.
    "asserted_in_chain": (
        [
            (
                1,
                "Base",
                "- **Status:** Superseded\n- **Supersedes:** ADR-0099\n"
                "- **Superseded by:** ADR-0003; ADR-0004\n",
            ),
            (3, "Three", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"),
            (4, "Four", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"),
        ],
        [{"from": "ADR-0001", "to": "ADR-0004", "text": "in chain"}],
    ),
}


@pytest.mark.parametrize("layout", sorted(_SAT_LAYOUTS))
def test_satellites_stay_clear_in_every_layout(
    browser: object, tmp_path_factory: pytest.TempPathFactory, layout: str
) -> None:
    """In a cycle, under a fan-in and beside an in-chain assertion, no
    satellite line runs along another relationship's line and every label,
    `cycle` included, stays beside its own line."""
    records, assertions = _SAT_LAYOUTS[layout]
    export = _publish_with(tmp_path_factory, f"sat_{layout}", records, assertions)
    page = _satellite_page(browser, export, "ADR-0001")
    _assert_satellites_clear(page, layout)


def test_an_incoming_assertion_points_at_the_selected_record(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """A satellite link draws each assertion in its own direction: an outgoing
    one ends at the satellite, an incoming one ends at the bus that leads to
    the selected record."""
    records, assertions = _SAT_LAYOUTS["fan_in"]
    export = _publish_with(tmp_path_factory, "sat_direction", records, assertions)
    page = _satellite_page(browser, export, "ADR-0001")
    ends = page.evaluate(
        """() => [...document.querySelectorAll(
            '#view-graph path[data-sat="as"], #view-graph path[data-sat="asIn"]')]
          .map(p => { const n = p.getTotalLength();
            const a = p.getPointAtLength(0), b = p.getPointAtLength(n);
            return {rel: p.dataset.rel, dx: b.x - a.x,
                    marker: !!p.getAttribute('marker-end')}; })"""
    )
    by_from = {e["rel"].split("|")[0]: e for e in ends}
    assert by_from["ADR-0001"]["dx"] > 0 and by_from["ADR-0001"]["marker"], ends
    assert by_from["ADR-0078"]["dx"] < 0 and by_from["ADR-0078"]["marker"], ends


def test_shown_contextual_links_never_cross_a_label(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Contextual links hang off the bus: hidden, they reserve no height; shown,
    the canvas grows to hold them, no bus or contextual line crosses a label,
    and the toggle, above the diagram, does not move on screen."""
    peers = "; ".join(f"ADR-00{k}" for k in range(10, 16))
    records = [
        (
            1,
            "Base",
            "- **Status:** Accepted\n- **Superseded in part:** ADR-0002 D1; ADR-0003 D2\n"
            f"- **Related:** {peers}\n",
        ),
        (2, "New", "- **Status:** Accepted\n- **Supersedes in part:** ADR-0001 D1\n"),
        (3, "Newer", "- **Status:** Accepted\n- **Supersedes in part:** ADR-0001 D2\n"),
    ] + [(k, f"Peer {k}", "- **Status:** Accepted\n") for k in range(10, 16)]
    export = _publish_with(tmp_path_factory, "ctx_shown", records, [])
    page = _satellite_page(browser, export, "ADR-0001")
    height = (
        "() => +document.querySelector('#view-graph .lineage-wrap svg').getAttribute('height')"
    )
    top = "() => document.querySelector('button.ctx-toggle').getBoundingClientRect().top"
    hidden = page.evaluate(height)
    rows = page.evaluate(
        "() => Math.max(...[...document.querySelectorAll('#view-graph [data-node-id] rect')]"
        ".map(r => r.getBBox().y + r.getBBox().height))"
    )
    assert hidden <= rows + 60, (hidden, rows)  # no room is held for hidden peers
    page.focus("button.ctx-toggle")
    before = page.evaluate(top)
    page.keyboard.press("Enter")
    shown = page.evaluate(height)
    assert shown > hidden, (hidden, shown)
    assert abs(page.evaluate(top) - before) < 1, "the toggle moved when links were shown"
    _assert_satellites_clear(page, "contextual shown")
    page.keyboard.press("Enter")
    assert page.evaluate(height) == hidden
    assert abs(page.evaluate(top) - before) < 1, "the toggle moved when links were hidden"


def test_an_in_chain_assertion_never_runs_on_the_contextual_bus(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """With contextual links but no satellites, an in-chain assertion still
    keeps out of the bus's row gap once the links are shown."""
    export = _publish_with(
        tmp_path_factory,
        "ctx_in_chain",
        [
            (
                1,
                "Base",
                "- **Status:** Superseded\n- **Superseded by:** ADR-0003; ADR-0004\n"
                "- **Related:** ADR-0009\n",
            ),
            (3, "Three", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"),
            (4, "Four", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"),
            (9, "Peer", "- **Status:** Accepted\n"),
        ],
        [{"from": "ADR-0001", "to": "ADR-0004", "text": "in chain"}],
    )
    page = _satellite_page(browser, export, "ADR-0001")
    page.click("button.ctx-toggle")
    _assert_satellites_clear(page, "contextual with an in-chain assertion")


def test_a_two_record_cycle_labels_both_relationships(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Each relationship of a two-record cycle has its own `cycle` label, or a
    keyed number, on its own arc."""
    export = _publish_with(
        tmp_path_factory,
        "two_cycle",
        [
            (
                1,
                "One",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0002\n"
                "- **Superseded by:** ADR-0002\n",
            ),
            (
                2,
                "Two",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"
                "- **Superseded by:** ADR-0001\n",
            ),
        ],
        [],
    )
    page = _satellite_page(browser, export, "ADR-0001")
    per_rel = page.evaluate(
        """() => { const svg = document.querySelector('#view-graph .lineage-wrap svg');
          return [...svg.querySelectorAll('path[data-rel]')].map(p => ({rel: p.dataset.rel,
            labels: [...svg.querySelectorAll('.edge-label')]
              .filter(t => t.dataset.for === p.dataset.rel).map(t => t.textContent)})); }"""
    )
    assert len(per_rel) == 2, per_rel
    for rel in per_rel:
        assert len(rel["labels"]) == 1 and rel["labels"][0] in ("cycle", "1", "2"), per_rel
    _assert_labels_sound(page, "#view-graph .lineage-wrap svg", "two-record cycle")


def test_many_one_sided_targets_render_the_focused_view_quickly(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """A record naming 10,000 unknown records renders its focused graph, with a
    label on every satellite link, in under 2 seconds: label placement reads
    every geometry first and tests only nearby boxes."""
    root = tmp_path_factory.mktemp("many_one_sided_fixture")
    targets = "; ".join(f"RFC-{n:04d}" for n in range(1, 10_001))
    _build_corpus(
        root,
        [
            (
                1,
                "Old",
                "- **Status:** Superseded\n- **Superseded by:** ADR-0002\n"
                f"- **Supersedes:** {targets}\n",
            ),
            (2, "New", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"),
        ],
    )
    page = _open_page(browser, _export(tmp_path_factory, root, "many_one_sided"))
    page.wait_for_selector("li.row")
    page.evaluate(
        """() => { window.__t0 = performance.now(); setTimeout(() => {
          location.hash = '#graph/ADR-0001'; }, 0); }"""
    )
    # A super-linear regression fails here by name instead of hanging the run.
    page.wait_for_function(
        "() => document.querySelectorAll('#view-graph .edge-label').length === 10000",
        timeout=6000,
    )
    elapsed = page.evaluate("() => performance.now() - window.__t0")
    assert elapsed < 2000, elapsed


def test_a_near_cap_record_of_one_sided_entries_still_renders_its_lineage(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """A record just under the 2 MiB cap naming 125,000 unknown target-and-scope
    pairs still renders its checked edge, every satellite label and the text
    list, with no script error."""
    root = tmp_path_factory.mktemp("near_cap_fixture")
    pairs = "; ".join(f"RFC-{1 + n // 9999:04d} D{1 + n % 9999}" for n in range(125_000))
    _build_corpus(
        root,
        [
            (
                1,
                "Old",
                "- **Status:** Superseded\n- **Superseded by:** ADR-0002\n"
                f"- **Supersedes in part:** {pairs}\n",
            ),
            (2, "New", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"),
        ],
    )
    page = _open_page(browser, _export(tmp_path_factory, root, "near_cap"))
    page.wait_for_selector("li.row")
    page.evaluate("() => { setTimeout(() => { location.hash = '#graph/ADR-0001'; }, 0); }")
    page.wait_for_selector("#view-graph .lineage-text", state="attached", timeout=60_000)
    drawn = page.evaluate(
        """() => ({ nodes: document.querySelectorAll('#view-graph svg [data-node-id]').length,
          labels: document.querySelectorAll('#view-graph .edge-label').length })"""
    )
    assert drawn == {"nodes": 2, "labels": 125_000}, drawn
    assert page._errors == [], page._errors  # type: ignore[attr-defined]


def test_a_label_too_long_to_draw_whole_becomes_a_keyed_number(
    browser: object, export_fan_out: pathlib.Path
) -> None:
    """A label longer than 16 characters is never cut: its edge shows a number,
    sitting on that edge, and the key under the graph gives the same number
    with the full label and the relationship it belongs to."""
    page = _open_page(browser, export_fan_out)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    labels = _assert_labels_sound(page, "#view-graph .lineage-wrap svg", "keyed")
    assert not any(x["text"].endswith("…") for x in labels), labels
    four = [x for x in labels if x["for"].startswith("ADR-0004|")]
    assert len(four) == 1 and four[0]["text"].isdigit(), labels
    key = page.evaluate(
        """() => [...document.querySelectorAll('#view-graph .lineage-key li')]
          .map(l => ({value: l.value, text: l.textContent}))"""
    )
    entry = next(k for k in key if k["value"] == int(four[0]["text"]))
    assert entry["text"].startswith(
        "in part · D7, D8, D9 — ADR-0004 supersedes in part ADR-0001"
    ), key


_NEWEST_CYCLES = {
    "two": [
        (1, "Old", "- **Status:** Superseded\n- **Superseded by:** ADR-0002; ADR-0003\n"),
        (
            2,
            "Two",
            "- **Status:** Accepted\n- **Supersedes:** ADR-0001; ADR-0003\n"
            "- **Superseded by:** ADR-0003\n",
        ),
        (
            3,
            "Three",
            "- **Status:** Accepted\n- **Supersedes:** ADR-0001; ADR-0002\n"
            "- **Superseded by:** ADR-0002\n",
        ),
    ],
    "three": [
        (1, "Old", "- **Status:** Superseded\n- **Superseded by:** ADR-0002\n"),
        (
            2,
            "Two",
            "- **Status:** Accepted\n- **Supersedes:** ADR-0001; ADR-0004\n"
            "- **Superseded by:** ADR-0003\n",
        ),
        (
            3,
            "Three",
            "- **Status:** Accepted\n- **Supersedes:** ADR-0002\n- **Superseded by:** ADR-0004\n",
        ),
        (
            4,
            "Four",
            "- **Status:** Accepted\n- **Supersedes:** ADR-0003\n- **Superseded by:** ADR-0002\n",
        ),
    ],
}


@pytest.mark.parametrize("size", sorted(_NEWEST_CYCLES))
def test_a_cycle_in_the_newest_column_keeps_its_arcs_and_labels(
    browser: object, tmp_path_factory: pytest.TempPathFactory, size: str
) -> None:
    """A two- or three-record cycle right of an older record, with no
    satellites, keeps every arc inside the drawing and its own `cycle` label
    on each."""
    export = _publish_with(tmp_path_factory, f"cycle_newest_{size}", _NEWEST_CYCLES[size], [])
    page = _satellite_page(browser, export, "ADR-0002")
    info = page.evaluate(
        """() => { const svg = document.querySelector('#view-graph .lineage-wrap svg');
          const vb = svg.viewBox.baseVal;
          const arcs = [...svg.querySelectorAll('path[data-rel][stroke-dasharray="8 4"]')];
          const out = arcs.map(p => { const n = p.getTotalLength(); let maxX = 0;
            for (let s = 0; s <= n; s += 1) maxX = Math.max(maxX, p.getPointAtLength(s).x);
            return {rel: p.dataset.rel, maxX,
              labels: [...svg.querySelectorAll('.edge-label')]
                .filter(t => t.dataset.for === p.dataset.rel).map(t => t.textContent)}; });
          return {width: vb.width, arcs: out}; }"""
    )
    assert len(info["arcs"]) == (2 if size == "two" else 3), info
    for arc in info["arcs"]:
        assert arc["maxX"] <= info["width"], (arc, info["width"])
        assert arc["labels"] == ["cycle"], info


def test_a_same_column_assertion_runs_straight_between_its_records(
    browser: object, export_partial_and_asserted: pathlib.Path
) -> None:
    """An assertion between two records in one column never climbs above the
    higher of its two ends and never doubles back on itself."""
    page = _open_page(browser, export_partial_and_asserted)
    page.wait_for_selector("li.row")
    _navigate_graph(page, "ADR-0001")
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    route = page.evaluate(
        """() => { const p = document.querySelector(
            '#view-graph path[data-rel="ADR-0002|guidance|ADR-0001|navigation_only"]');
          const n = p.getTotalLength(), pts = [];
          for (let s = 0; s <= n; s += 2) {
            const q = p.getPointAtLength(s); pts.push([q.x, q.y]); }
          return pts; }"""
    )
    top = min(route[0][1], route[-1][1])
    assert min(y for _, y in route) >= top - 1, "the route climbs past its target"
    ys = [y for _, y in route]
    steps = [b - a for a, b in zip(ys, ys[1:], strict=False) if abs(b - a) > 0.5]
    assert all(d < 0 for d in steps) or all(d > 0 for d in steps), "the route doubles back"


# A dense chain shaped like a real corpus: one record supersedes five others in
# part, and four more partial edges converge on the same older records.
_DENSE_EDGES = [
    (7, 2, "D8"),
    (8, 2, "D3"),
    (8, 4, "D7"),
    (8, 6, ""),
    (9, 1, "D2"),
    (9, 3, "D6, D7"),
    (9, 4, "D1, D2"),
    (9, 5, "D1"),
    (9, 6, "D6"),
    (10, 2, "D4"),
    (11, 9, "D3"),
]


@pytest.fixture(scope="module")
def export_dense(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    root = tmp_path_factory.mktemp("dense_fixture")

    def field(pairs: list[tuple[int, str]]) -> str:
        return "; ".join(f"ADR-{n:04d}" + (f" {sc}" if sc else "") for n, sc in pairs)

    records = []
    for k in range(1, 12):
        newer = [(f, sc) for f, t, sc in _DENSE_EDGES if t == k]
        older = [(t, sc) for f, t, sc in _DENSE_EDGES if f == k]
        header = "- **Status:** Accepted\n"
        if older:
            header += f"- **Supersedes in part:** {field(older)}\n"
        if newer:
            header += f"- **Superseded in part:** {field(newer)}\n"
        records.append((k, f"Dense {k}", header))
    _build_corpus(root, records)
    return _export(tmp_path_factory, root, "dense")


@pytest.mark.parametrize("selected", [f"ADR-{k:04d}" for k in range(1, 12)])
def test_every_edge_of_a_dense_chain_is_marked(
    browser: object, export_dense: pathlib.Path, selected: str
) -> None:
    """In a dense chain, whichever record is selected, every relationship has
    its whole label or a keyed number on the diagram, and no whole label sits
    by another record's arrowhead."""
    page = _open_page(browser, export_dense)
    page.wait_for_selector("li.row")
    _navigate_graph(page, selected)
    page.wait_for_selector("#view-graph svg [data-rel]", state="attached")
    _assert_labels_sound(page, "#view-graph .lineage-wrap svg", selected)
    unmarked = page.evaluate(
        "() => [...document.querySelectorAll('#view-graph .lineage-key li')]"
        ".filter(l => l.textContent.includes('no room')).map(l => l.textContent)"
    )
    assert unmarked == [], (selected, unmarked)
    for near in page.evaluate(_NEAREST_END_JS, "#view-graph .lineage-wrap svg"):
        if not near["text"].isdigit():
            assert near["nearest"].split("|")[2] == near["own"].split("|")[2], (selected, near)


def test_a_selected_cycle_member_keeps_a_readable_cycle_tag(
    browser: object, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """The node-level `cycle` tag reaches 4.5:1 against its node's fill on the
    selected node and on an unselected one."""
    export = _publish_with(
        tmp_path_factory,
        "cycle_tag",
        [
            (
                1,
                "One",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0002\n"
                "- **Superseded by:** ADR-0002\n",
            ),
            (
                2,
                "Two",
                "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"
                "- **Superseded by:** ADR-0001\n",
            ),
        ],
        [],
    )
    page = _satellite_page(browser, export, "ADR-0001")
    pairs = page.evaluate(
        """() => [...document.querySelectorAll('#view-graph [data-node-id]')].map(g => {
          const tag = [...g.querySelectorAll('text')].find(t => t.textContent === 'cycle');
          let bg = getComputedStyle(g.querySelector('rect')).fill;
          for (let e = g; e && bg === 'none'; e = e.parentElement) {
            const c = getComputedStyle(e).backgroundColor;
            if (c !== 'rgba(0, 0, 0, 0)') bg = c; }
          return {id: g.dataset.nodeId, fg: getComputedStyle(tag).fill, bg,
                  focus: g.querySelector('rect').classList.contains('ln-node-focus')}; })"""
    )

    def lum(colour: str) -> float:
        rgb = [float(v) / 255 for v in colour[colour.index("(") + 1 : -1].split(",")[:3]]
        lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]

    assert {p["id"] for p in pairs} == {"ADR-0001", "ADR-0002"}, pairs
    selected = [p["id"] for p in pairs if p["focus"]]
    assert selected == ["ADR-0001"], pairs  # the selected case is really measured
    for pair in pairs:
        # An unfilled (superseded) node shows the list zone's background behind it.
        a, b = lum(pair["fg"]), lum(pair["bg"])
        ratio = (max(a, b) + 0.05) / (min(a, b) + 0.05)
        assert ratio >= 4.5, (pair, round(ratio, 2))


# ── Record-ID search (T9) ────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def export_search(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export a corpus with ADR-0098, RFC-0098, and ADR-0001 for ID-search tests."""
    root = tmp_path_factory.mktemp("search_fixture")
    adr_dir = root / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    rfc_dir = root / "docs" / "rfc"
    rfc_dir.mkdir(parents=True)
    (adr_dir / "0001-baseline-record.md").write_text(
        "# ADR-0001: Baseline record\n\n- **Status:** Accepted\n\n## Context\n\nTest.\n",
        encoding="utf-8",
    )
    (adr_dir / "0098-alpha-record.md").write_text(
        "# ADR-0098: Alpha record\n\n- **Status:** Accepted\n\n## Context\n\nTest.\n",
        encoding="utf-8",
    )
    (rfc_dir / "0098-alpha-proposal.md").write_text(
        "# RFC-0098: Alpha proposal\n\n- **Status:** Accepted\n\n## Summary\n\nTest.\n",
        encoding="utf-8",
    )
    return _export(tmp_path_factory, root, "search")


def test_search_by_record_id(browser: object, export_search: pathlib.Path) -> None:
    """Search by full ID, lowercase ID, bare ordinal, and zero-padded ordinal each
    leave ADR-0098 in the list; bare ordinals also leave RFC-0098; a title-only
    term still matches; a non-matching term shows the no-result state."""
    page = _open_page(browser, export_search)
    page.wait_for_selector("li.row")

    def visible_ids() -> list[str]:
        return page.evaluate(
            "() => [...document.querySelectorAll('li.row .rid')].map(e => e.textContent)"
        )

    # Full uppercase ID — substring match on r.id, kind-restricted to ADR
    page.locator("#search-input").fill("ADR-0098")
    page.wait_for_timeout(300)
    ids = visible_ids()
    assert "ADR-0098" in ids, ("ADR-0098 not found for query 'ADR-0098'", ids)
    assert "RFC-0098" not in ids, ("RFC-0098 must not match 'ADR-0098'", ids)

    # Lowercase ID — same substring match, case-insensitive
    page.locator("#search-input").fill("adr-0098")
    page.wait_for_timeout(300)
    ids = visible_ids()
    assert "ADR-0098" in ids, ("ADR-0098 not found for query 'adr-0098'", ids)
    assert "RFC-0098" not in ids, ("RFC-0098 must not match 'adr-0098'", ids)

    # Bare ordinal — ordinal match, both kinds
    page.locator("#search-input").fill("98")
    page.wait_for_timeout(300)
    ids = visible_ids()
    assert "ADR-0098" in ids, ("ADR-0098 not found for query '98'", ids)
    assert "RFC-0098" in ids, ("RFC-0098 not found for query '98'", ids)

    # Zero-padded ordinal — leading zeros stripped, both kinds
    page.locator("#search-input").fill("0098")
    page.wait_for_timeout(300)
    ids = visible_ids()
    assert "ADR-0098" in ids, ("ADR-0098 not found for query '0098'", ids)
    assert "RFC-0098" in ids, ("RFC-0098 not found for query '0098'", ids)

    # Title-only term — matches ADR-0001 by title
    page.locator("#search-input").fill("Baseline")
    page.wait_for_timeout(300)
    ids = visible_ids()
    assert "ADR-0001" in ids, ("ADR-0001 not found for title-only query 'Baseline'", ids)

    # Non-matching term — shows the no-result state
    page.locator("#search-input").fill("zzzzz-no-match-xqz")
    page.wait_for_timeout(300)
    assert page.locator(".empty-msg").is_visible(), (
        "no-result state must be visible for a non-matching query"
    )


def test_search_label_names_ids_titles_statuses(
    browser: object, export_search: pathlib.Path
) -> None:
    """The search box's placeholder, the text a sighted user sees in it, names IDs,
    titles and statuses, and its computed accessible name names them too and
    contains the label."""
    page = _open_page(browser, export_search)
    page.wait_for_selector("li.row")

    placeholder = page.locator("#search-input").get_attribute("placeholder") or ""
    for word in ("ids", "titles", "statuses"):
        assert word in placeholder.lower(), (word, placeholder)
    label_text = page.evaluate(
        "() => { const lbl = document.querySelector('label[for=search-input]');"
        " return lbl ? lbl.textContent.trim() : ''; }"
    )

    # Computed accessible name, as assistive technology reads it. It must
    # contain the visible label so a speech-input user can say what they see.
    snapshot = page.locator("#search-input").aria_snapshot()
    assert snapshot.startswith("- searchbox "), snapshot
    name = snapshot.split('"')[1] if '"' in snapshot else ""
    assert label_text in name, (label_text, name)
    for word in ("id", "title", "status"):
        assert word in name.lower(), (word, name)


# ── decision-view-style: two soft zones across the width and theme matrix ─────

_WIDTHS = (320, 1280, 1680, 2560)
_SCHEMES = ("light", "dark")
_ZONE_VIEWS = ("list", "graph", "context", "recent")
_MATRIX = [(w, s) for w in _WIDTHS for s in _SCHEMES]
_MATRIX_IDS = [f"{w}-{s}" for w, s in _MATRIX]


def _zone_page(
    browser: object, html_path: pathlib.Path, width: int, scheme: str, view: str
) -> object:
    """Open `html_path` at `width` in `scheme` with the first record picked in `view`."""
    context = browser.new_context(  # type: ignore[union-attr]
        viewport={"width": width, "height": 900}, color_scheme=scheme, offline=True
    )
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page._errors = errors  # type: ignore[attr-defined]
    page.goto(f"file://{html_path}")
    page.wait_for_selector("li.row")
    first = page.evaluate(
        "() => JSON.parse(document.getElementById('nav-data').textContent).records[0].id"
    )
    if view == "graph":
        # The first chain in the atlas's display order, or the atlas as it first opens.
        _navigate_graph(page)
        chain = page.evaluate(
            "() => { const c = document.querySelector('.chain-card');"
            " return c ? c.querySelector('[data-node-id]').dataset.nodeId : null; }"
        )
        if chain is None:
            return page
        first = chain
    _show(page, view, first)
    if view == "areas":
        # The By area list is checked with every section open.
        page.evaluate(
            "() => document.querySelectorAll('#view-areas details')"
            ".forEach(d => { d.open = true; })"
        )
    page.wait_for_function(
        "(id) => document.querySelector('#detail-body .state-line').textContent.includes(id)",
        arg=first,
    )
    return page


@pytest.fixture(params=("mixed", "hostile"))
def zone_export(request: pytest.FixtureRequest) -> pathlib.Path:
    """The `mixed` and `negative/hostile` exports."""
    return request.getfixturevalue(f"export_{request.param}")  # type: ignore[no-any-return]


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_IDS)
@pytest.mark.parametrize("view", _ZONE_VIEWS)
def test_zones_are_soft_and_rows_are_flat(
    browser: object, zone_export: pathlib.Path, width: int, scheme: str, view: str
) -> None:
    """AC-0008: both zones have a radius and a shadow; list rows have none or inset only."""
    page = _zone_page(browser, zone_export, width, scheme, view)
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const z = s => { const c = getComputedStyle(document.querySelector(s));
            return { radius: c.borderRadius, shadow: c.boxShadow }; };
          const rows = [...document.querySelectorAll('.row-link')].map(r =>
            getComputedStyle(r).boxShadow).filter(s => s !== 'none'
              && !s.split(/,(?![^(]*\\))/).every(p => p.includes('inset')));
          return { list: z('.worklist'), detail: z('.detail'), badRows: rows }; }"""
    )
    for zone in ("list", "detail"):
        assert info[zone]["radius"] not in ("0px", ""), (zone, info)
        assert info[zone]["shadow"] != "none", (zone, info)
    assert info["badRows"] == [], info


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_IDS)
@pytest.mark.parametrize("view", _ZONE_VIEWS)
def test_zones_do_not_overflow_their_edges(
    browser: object, zone_export: pathlib.Path, width: int, scheme: str, view: str
) -> None:
    """AC-0010: nothing inside a zone passes its edge by more than 1px, and the page
    never scrolls sideways; a keyboard-scrollable named container is the one exception."""
    page = _zone_page(browser, zone_export, width, scheme, view)
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const bad = [];
          const scroller = e => { const o = getComputedStyle(e).overflowX;
            return (o === 'auto' || o === 'scroll') && e.getAttribute('tabindex') === '0'
              && (e.getAttribute('aria-label') || e.getAttribute('aria-labelledby')); };
          for (const sel of ['.worklist', '.detail']) {
            const zone = document.querySelector(sel), zr = zone.getBoundingClientRect();
            if (getComputedStyle(zone).display === 'none') continue;
            for (const e of zone.querySelectorAll('*')) {
              let skip = false;
              for (let p = e.parentElement; p && p !== zone; p = p.parentElement)
                if (scroller(p)) { skip = true; break; }
              if (skip) continue;
              const r = e.getBoundingClientRect();
              if (r.width === 0 && r.height === 0) continue;
              if (r.left < zr.left - 1 || r.right > zr.right + 1)
                bad.push([sel, e.tagName, String(e.getAttribute('class')),
                  Math.round(r.left - zr.left), Math.round(r.right - zr.right)]);
            } }
          return { bad: bad.slice(0, 5),
            scroll: document.documentElement.scrollWidth, view: innerWidth }; }"""
    )
    assert info["bad"] == [], info
    assert info["scroll"] <= info["view"], info


@pytest.mark.parametrize("scheme", _SCHEMES)
@pytest.mark.parametrize("width", _WIDTHS)
@pytest.mark.parametrize("view", _ZONE_VIEWS)
def test_detail_sits_beside_the_list_or_below_it(
    browser: object, export_mixed: pathlib.Path, width: int, scheme: str, view: str
) -> None:
    """AC-0009: from 1280 the detail is right of the list and overlaps it vertically;
    at 320 it is below the list or the list is hidden."""
    page = _zone_page(browser, export_mixed, width, scheme, view)
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const l = document.querySelector('.worklist'),
            d = document.querySelector('.detail');
          const lr = l.getBoundingClientRect(), dr = d.getBoundingClientRect();
          return { hidden: getComputedStyle(l).display === 'none',
            beside: dr.left >= lr.right - 0.5, below: dr.top >= lr.bottom - 0.5,
            overlap: dr.top < lr.bottom && lr.top < dr.bottom }; }"""
    )
    if width >= 1280:
        assert info["beside"] and info["overlap"], info
    else:
        assert info["hidden"] or info["below"], info


@pytest.mark.parametrize("scheme", _SCHEMES)
def test_zones_fill_the_width_at_2560(
    browser: object, export_mixed: pathlib.Path, scheme: str
) -> None:
    """AC-0011: header and zones together span the viewport less twice the page padding."""
    page = _zone_page(browser, export_mixed, 2560, scheme, "list")
    span = page.evaluate(  # type: ignore[union-attr]
        """() => { const r = ['.page-header', '.worklist', '.detail'].map(s =>
            document.querySelector(s).getBoundingClientRect());
          return Math.max(...r.map(x => x.right)) - Math.min(...r.map(x => x.left)); }"""
    )
    assert span >= 2560 - (2 * 24 + 2), span


@pytest.mark.parametrize("view", _ZONE_VIEWS)
@pytest.mark.parametrize("key", ("Enter", "Space"))
def test_back_to_list_returns_to_the_current_view_at_320(
    browser: object, export_mixed: pathlib.Path, view: str, key: str
) -> None:
    """AC-0026: at 320 the detail's "Back to list" button, by keyboard, shows the list
    zone again in the view that was current, with the picked row marked."""
    page = _zone_page(browser, export_mixed, 320, "light", view)
    assert (
        page.evaluate(  # type: ignore[union-attr]
            "() => getComputedStyle(document.querySelector('.worklist')).display"
        )
        == "none"
    )
    back = page.get_by_role("button", name="Back to list")  # type: ignore[union-attr]
    back.focus()
    page.keyboard.press(key)  # type: ignore[union-attr]
    assert (
        page.evaluate(  # type: ignore[union-attr]
            "() => getComputedStyle(document.querySelector('.worklist')).display"
        )
        != "none"
    )
    if view == "context":
        assert _current_links(page) == []
    else:
        assert page.get_attribute(f"#q-{view}", "aria-current") == "page"  # type: ignore[union-attr]
    if view == "list":
        assert page.locator("#view-list .row-link[aria-current=true]").count() == 1  # type: ignore[union-attr]
    if view == "graph":
        assert page.locator("#view-graph [data-node-id][aria-current=true]").count() == 1  # type: ignore[union-attr]


def test_record_body_headings_are_smaller_than_page_headings(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0025: headings inside the record content are smaller than the page h1 and
    the detail heading."""
    page = _zone_page(browser, export_mixed, 1280, "light", "list")
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const px = e => parseFloat(getComputedStyle(e).fontSize);
          const hs = [...document.querySelectorAll('.record-content h3, .record-content h4,'
            + '.record-content h5, .record-content h6')];
          return { count: hs.length, largest: Math.max(...hs.map(px)),
            h1: px(document.querySelector('h1')),
            detail: px(document.querySelector('.detail-heading')) }; }"""
    )
    assert info["count"] > 0, info
    assert info["largest"] < info["h1"] and info["largest"] < info["detail"], info


# ── decision-view-style: names lead, state marks and token-coloured lineage ───

FIXTURE_MARKS = HERE / "fixtures/lifecycle-marks"
_MARK_OF = {
    "accepted": "approved",
    "experimental": "active",
    "proposed": "draft",
    "draft": "draft",
    "open": "draft",
    "final": "draft",
    "superseded": "done",
    "deprecated": "done",
    "rejected": "done",
    "withdrawn": "done",
}
_GLYPH = {"active": "●", "approved": "◆", "draft": "◇", "done": "✓"}


@pytest.fixture(scope="module")
def export_marks(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export the `lifecycle-marks` fixture: one record for each lifecycle value."""
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        FIXTURE_MARKS,
        destination=tmp_path_factory.mktemp("browser_marks"),
        mode="full",
        name="marks.html",
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


def _records(page: object) -> list[dict[str, object]]:
    return page.evaluate(  # type: ignore[union-attr, no-any-return]
        "() => JSON.parse(document.getElementById('nav-data').textContent).records"
    )


def _expected_mark(rec: dict[str, object]) -> tuple[str, str]:
    """The AC-0013 mark and visible text for a record's lifecycle."""
    import re as _re

    life = rec["lifecycle"]
    assert isinstance(life, dict)
    if life.get("missing"):
        return "draft", _GLYPH["draft"] + "No status"
    word = _re.search(r"[A-Za-z]+", str(life["raw_value"]))
    mark = _MARK_OF.get(word.group(0).lower(), "draft") if word else "draft"
    return mark, _GLYPH[mark] + str(life["display_value"])


_MARK_PROBE = """(sel) => [...document.querySelectorAll(sel)].map(m => ({
  mark: m.dataset.mark, text: m.textContent,
  glyphHidden: !!m.querySelector('.mark-g[aria-hidden="true"]') }))"""


@pytest.mark.parametrize("fixture_name", ("export_mixed", "export_marks"))
def test_every_row_and_the_detail_line_carry_one_mark_by_the_lifecycle_map(
    browser: object, request: pytest.FixtureRequest, fixture_name: str
) -> None:
    """AC-0013: each list row and the detail state line holds one `.mark` whose `data-mark`
    follows the lifecycle map and whose text is a hidden glyph then the display value."""
    page = _open_page(browser, request.getfixturevalue(fixture_name))
    page.evaluate("() => { location.hash = '#list'; }")  # type: ignore[union-attr]
    page.wait_for_selector("#view-list li.row")  # type: ignore[union-attr]
    records = _records(page)
    rows = page.evaluate(  # type: ignore[union-attr]
        """() => [...document.querySelectorAll('#view-list li.row')].map(li => ({
          id: li.querySelector('.row-link').dataset.id,
          marks: [...li.querySelectorAll('.mark')].map(m => ({ mark: m.dataset.mark,
            text: m.textContent, glyphHidden: !!m.querySelector('.mark-g[aria-hidden="true"]'),
            inRow: !!m.closest('.row-link'), inNotice: !!m.closest('.notice') })) }))"""
    )
    assert [r["id"] for r in rows] == [r["id"] for r in records]
    seen = set()
    for row, rec in zip(rows, records, strict=True):
        want_mark, want_text = _expected_mark(rec)
        assert len(row["marks"]) == 1, row
        got = row["marks"][0]
        assert (got["mark"], got["text"]) == (want_mark, want_text), (rec["id"], got)
        assert got["glyphHidden"] and got["inRow"] and not got["inNotice"], got
        seen.add(want_mark)
        page.evaluate(f"() => {{ location.hash = '#detail/{rec['id']}'; }}")  # type: ignore[union-attr]
        page.wait_for_function(  # type: ignore[union-attr]
            "(id) => (document.querySelector('#detail-body .state-line') || {})"
            ".textContent?.includes(id)",
            arg=rec["id"],
        )
        line = page.evaluate(_MARK_PROBE, "#detail-body .state-line .mark")  # type: ignore[union-attr]
        want = [{"mark": want_mark, "text": want_text, "glyphHidden": True}]
        assert line == want, (rec["id"], line)
        assert page.locator("#detail-body .notice .mark").count() == 0  # type: ignore[union-attr]
    if fixture_name == "export_marks":
        by_id = {r["id"]: _expected_mark(r)[0] for r in records}
        assert by_id["ADR-0011"] == "draft", by_id  # "Constructor" is no inherited-name mark
        constructor = page.evaluate(  # type: ignore[union-attr]
            "() => document.querySelector('.row-link[data-id=\"ADR-0011\"]')"
            ".parentElement.querySelector('.mark').dataset.mark"
        )
        assert constructor == "draft", constructor
        assert seen == {"active", "approved", "draft", "done"}, seen
        assert len(records) == 13  # AC-0013's 11 values plus Draft and Constructor
    else:
        assert "approved" in seen


@pytest.mark.parametrize("fixture_name", ("export_mixed", "export_marks", "export_hostile"))
def test_a_row_leads_with_its_title_then_its_id(
    browser: object, request: pytest.FixtureRequest, fixture_name: str
) -> None:
    """AC-0012: in every list row the title is the first text in DOM order, and the id
    appears in the row only after it. The detail heading is the title too."""
    page = _open_page(browser, request.getfixturevalue(fixture_name))
    page.evaluate("() => { location.hash = '#list'; }")  # type: ignore[union-attr]
    page.wait_for_selector("#view-list li.row")  # type: ignore[union-attr]
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const data = JSON.parse(
            document.getElementById('nav-data').textContent).records;
          return [...document.querySelectorAll('#view-list li.row')].map((li, i) => {
            const texts = [];
            const w = document.createTreeWalker(li, NodeFilter.SHOW_TEXT);
            while (w.nextNode()) {
              const t = w.currentNode.textContent;
              if (t.trim()) texts.push(t); }
            const id = data[i].id, title = data[i].display_title || data[i].title;
            return { id, title, first: texts[0],
              idAt: texts.findIndex(t => t.includes(id)) }; }); }"""
    )
    assert info
    for row in info:
        assert row["first"] == row["title"], row
        assert row["idAt"] > 0, row
    first = info[0]["id"]
    _show(page, "detail", first)
    heading = page.locator("#detail-body h2.detail-heading").text_content()  # type: ignore[union-attr]
    assert heading == info[0]["title"], heading


@pytest.mark.parametrize("reduced", (True, False))
def test_motion_follows_the_reduced_motion_preference(
    browser: object, export_mixed: pathlib.Path, reduced: bool
) -> None:
    """AC-0015: under `reduce` every element computes a zero transition and animation
    duration; under `no-preference` a list row computes a transition longer than zero."""
    context = browser.new_context(  # type: ignore[union-attr]
        reduced_motion="reduce" if reduced else "no-preference", offline=True
    )
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_selector("li.row")
    _show(page, "list", "ADR-0001")
    if reduced:
        moving = page.evaluate(
            """() => [...document.querySelectorAll('*')].flatMap(e => {
              const cs = getComputedStyle(e);
              const bad = ['transitionDuration', 'animationDuration'].filter(p =>
                cs[p].split(',').some(d => d.trim() !== '0s'));
              return bad.length ? [e.tagName + '.' + e.className + ' ' + bad.join()] : []; })"""
        )
        assert moving == [], moving[:5]
    else:
        durations = page.eval_on_selector(
            ".row-link", "e => getComputedStyle(e).transitionDuration"
        )
        assert any(float(d.strip().removesuffix("s")) > 0 for d in durations.split(",")), durations
    context.close()


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_IDS)
@pytest.mark.parametrize("view", _ZONE_VIEWS)
def test_no_element_carries_a_style_attribute_through_pick_toggle_and_focus(
    browser: object, zone_export: pathlib.Path, width: int, scheme: str, view: str
) -> None:
    """AC-0027: after a pick, after the Graph view's contextual links are shown, and with a
    diagram node focused, no element in the document has a `style` attribute."""
    page = _zone_page(browser, zone_export, width, scheme, view)
    count = "() => document.querySelectorAll('[style]').length"
    assert page.evaluate(count) == 0  # type: ignore[union-attr]
    record = page.evaluate(  # type: ignore[union-attr]
        "() => JSON.parse(document.getElementById('nav-data').textContent).records[0].id"
    )
    _show(page, "graph", record)
    page.evaluate("() => { const t = document.querySelector('.ctx-toggle'); if (t) t.click(); }")  # type: ignore[union-attr]
    assert page.evaluate(count) == 0  # type: ignore[union-attr]
    page.evaluate(  # type: ignore[union-attr]
        "() => { const g = document.querySelector('[data-node-id]'); if (g) g.focus(); }"
    )
    assert page.evaluate(count) == 0  # type: ignore[union-attr]
    # The toggle's control text and the contextual group show the toggled state, not a style.
    state = page.evaluate(  # type: ignore[union-attr]
        "() => { const t = document.querySelector('.ctx-toggle');"
        " return t ? t.getAttribute('aria-expanded') : null; }"
    )
    assert state in (None, "true"), state


_CONTRAST_JS = """() => {
  const rgb = s => (s.match(/[\\d.]+/g) || []).map(Number);
  const lum = c => { const v = c.slice(0, 3).map(x => { x /= 255;
    return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const ratio = (a, b) => { const x = lum(a), y = lum(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const backdrop = e => { for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      const c = rgb(getComputedStyle(n).backgroundColor);
      if (c.length >= 3 && (c.length < 4 || c[3] > 0)) return c; }
    return rgb(getComputedStyle(document.body).backgroundColor); };
  const inside = (a, b) => a.left >= b.left - 0.5 && a.right <= b.right + 0.5
    && a.top >= b.top - 0.5 && a.bottom <= b.bottom + 0.5;
  const SHAPES = new Set(['rect', 'path', 'polygon', 'circle', 'ellipse', 'polyline']);
  const svgBackdrop = t => { const box = t.getBoundingClientRect(); let found = null;
    const svg = t.ownerSVGElement;
    for (const s of svg.querySelectorAll('*')) {
      if (!SHAPES.has(s.localName) || s === t) continue;
      if (!(s.compareDocumentPosition(t) & Node.DOCUMENT_POSITION_FOLLOWING)) continue;
      if (!s.parentNode.contains(t)) continue;
      const f = getComputedStyle(s).fill;
      if (f === 'none' || !inside(box, s.getBoundingClientRect())) continue;
      found = rgb(f); }
    return found || backdrop(svg); };
  const bad = []; let checked = 0;
  for (const root of document.querySelectorAll('.page-header, .worklist, .detail')) {
    if (getComputedStyle(root).display === 'none') continue;
    for (const e of root.querySelectorAll('*')) {
      const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
      if (!own) continue;
      const r = e.getBoundingClientRect();
      if ((r.width <= 1 && r.height <= 1) || getComputedStyle(e).visibility === 'hidden') continue;
      if (e.closest('select')) continue;
      const svgText = e instanceof SVGElement;
      const fg = rgb(getComputedStyle(e)[svgText ? 'fill' : 'color']);
      const bg = svgText ? svgBackdrop(e) : backdrop(e);
      const q = ratio(fg, bg); checked++;
      if (q < 4.5) bad.push(['text', e.tagName, String(e.getAttribute('class')),
        e.textContent.trim().slice(0, 24), Math.round(q * 100) / 100]);
    }
    for (const e of root.querySelectorAll('input, select, button')) {
      const cs = getComputedStyle(e), r = e.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      const side = ['Top', 'Right', 'Bottom', 'Left'].find(
        s => parseFloat(cs['border' + s + 'Width']) > 0);
      if (!side) continue;
      const q = ratio(rgb(cs['border' + side + 'Color']), backdrop(e.parentElement)); checked++;
      if (q < 3) bad.push(['border', e.tagName, String(e.getAttribute('class')), e.id,
        Math.round(q * 100) / 100]);
    }
  }
  return { bad: bad.slice(0, 8), checked }; }"""


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_IDS)
@pytest.mark.parametrize("view", _ZONE_VIEWS)
def test_text_and_control_borders_have_enough_contrast(
    browser: object, zone_export: pathlib.Path, width: int, scheme: str, view: str
) -> None:
    """AC-0014: every text element (SVG text against its own backdrop shape) reaches 4.5:1,
    and the border of the search field, each select and each bordered button reaches 3:1."""
    page = _zone_page(browser, zone_export, width, scheme, view)
    info = page.evaluate(_CONTRAST_JS)  # type: ignore[union-attr]
    assert info["checked"] > 10, info
    assert info["bad"] == [], info


@pytest.mark.parametrize("scheme", _SCHEMES)
@pytest.mark.parametrize("width", _WIDTHS)
def test_diagram_shapes_draw_only_in_token_colours(
    browser: object, zone_export: pathlib.Path, width: int, scheme: str
) -> None:
    """AC-0023: every SVG element under the diagram computes a fill and a stroke that is
    `none` or equals a `--c-` custom property declared on `:root` in this theme."""
    page = _zone_page(browser, zone_export, width, scheme, "graph")
    probe = """() => { const names = [...document.styleSheets].flatMap(s => [...s.cssRules])
        .flatMap(r => r.selectorText === ':root' ? [...r.style] : r.cssRules
          ? [...r.cssRules].flatMap(q => q.selectorText === ':root' ? [...q.style] : []) : [])
        .filter(n => n.startsWith('--c-'));
      const p = document.createElement('span'); document.body.appendChild(p);
      const tokens = new Set(names.map(n => { p.style.color = 'var(' + n + ')';
        return getComputedStyle(p).color; })); p.remove();
      const bad = []; let n = 0;
      for (const e of document.querySelectorAll('#view-graph svg, #view-graph svg *')) {
        const cs = getComputedStyle(e); n++;
        for (const k of ['fill', 'stroke']) if (cs[k] !== 'none' && !tokens.has(cs[k]))
          bad.push([e.localName, String(e.getAttribute('class')), k, cs[k]]); }
      return { tokens: tokens.size, n, bad: bad.slice(0, 6) }; }"""
    # The probe sets an inline style on a throwaway element; the page itself never does.
    info = page.evaluate(probe)  # type: ignore[union-attr]
    assert info["tokens"] >= 10, info
    assert info["bad"] == [], info
    # Also with the atlas of every chain.
    if page.locator("button.atlas-back").count():  # type: ignore[union-attr]
        page.evaluate("() => document.querySelector('button.atlas-back').click()")  # type: ignore[union-attr]
        page.wait_for_selector(".chain-card svg")  # type: ignore[union-attr]
        info = page.evaluate(probe)  # type: ignore[union-attr]
        assert info["n"] > 10 and info["bad"] == [], info


def test_lineage_scroll_wrappers_are_named_keyboard_regions(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """The focused diagram's and each atlas card's scroll wrapper is a named keyboard region."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    probe = """(sel) => [...document.querySelectorAll(sel)].map(w => ({
        tab: w.getAttribute('tabindex'), role: w.getAttribute('role'),
        name: w.getAttribute('aria-label'), overflow: getComputedStyle(w).overflowX }))"""
    focused = page.evaluate(probe, "#view-graph .lineage-wrap")  # type: ignore[union-attr]
    assert len(focused) == 1, focused
    page.click("button.atlas-back")  # type: ignore[union-attr]
    page.wait_for_selector(".chain-card svg")  # type: ignore[union-attr]
    atlas = page.evaluate(probe, ".chain-svg-wrap")  # type: ignore[union-attr]
    assert atlas, atlas
    for w in focused + atlas:
        assert w["tab"] == "0" and w["role"] == "group" and w["name"], w
        assert w["overflow"] == "auto", w


# ── decision-view-style review fixes: history, clipping, node size, header ────


def _hash_state(page: object) -> dict[str, object]:
    return page.evaluate(  # type: ignore[union-attr, no-any-return]
        """() => ({ hash: location.hash,
          view: (document.querySelector('#question-list a[aria-current=page]')
            || { id: 'q-context' }).id.slice(2),
          picked: document.getElementById('app-main').hasAttribute('data-picked'),
          listShown: getComputedStyle(document.querySelector('.worklist')).display !== 'none',
          detailShown: getComputedStyle(document.querySelector('.detail')).display !== 'none' })"""
    )


def _first_superseded(page: object) -> tuple[str, str]:
    return page.evaluate(  # type: ignore[union-attr, no-any-return]
        """() => { const r = JSON.parse(document.getElementById('nav-data').textContent)
            .records.find(r => (r.superseded_by || []).some(s => !s.partial));
          return [r.id, r.superseded_by.find(s => !s.partial).by]; }"""
    )


def test_history_returns_to_the_view_recorded_with_each_entry(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """Every back and forward entry restores the view and the picked state recorded with it:
    a supersession link follows the current view, and Back and forward agree."""
    context = browser.new_context(viewport={"width": 1280, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_selector("li.row")
    old, new = _first_superseded(page)
    _show(page, "graph", old)
    page.locator("#detail-body .supersede-banner a").first.click()
    page.wait_for_function("(id) => location.hash.includes(id)", arg=new)
    after_link = _hash_state(page)
    assert after_link["view"] == "graph" and after_link["picked"], after_link
    page.click("#q-list")
    page.wait_for_function("() => !document.getElementById('view-list').hidden")
    listed = _hash_state(page)
    assert listed["view"] == "list" and not listed["picked"], listed
    page.go_back()
    page.wait_for_function("() => !document.getElementById('view-graph').hidden")
    assert _hash_state(page) == after_link
    page.go_forward()
    page.wait_for_function("() => !document.getElementById('view-list').hidden")
    assert _hash_state(page) == listed
    page.go_back()
    page.go_back()
    page.wait_for_function("(id) => location.hash.includes(id)", arg=old)
    assert _hash_state(page)["view"] == "graph"
    context.close()


def test_history_after_back_to_list_keeps_the_list_zone_at_320(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """At 320: pick a row, Back to list, Graph, then back and forward; the entry recorded
    with no pick shows the list zone, never the detail."""
    context = browser.new_context(viewport={"width": 320, "height": 800}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_selector("li.row")
    page.locator("li.row .row-link").first.click()
    page.wait_for_selector("#app-main[data-picked]")
    picked = _hash_state(page)
    assert picked["detailShown"] and not picked["listShown"], picked
    page.click("#back-btn")
    page.wait_for_selector("#app-main:not([data-picked])")
    unpicked = _hash_state(page)
    assert unpicked["listShown"] and not unpicked["detailShown"], unpicked
    page.click("#q-graph")
    page.wait_for_function("() => !document.getElementById('view-graph').hidden")
    graph = _hash_state(page)
    assert graph["listShown"] and not graph["detailShown"], graph
    page.go_back()
    page.wait_for_function("() => !document.getElementById('view-recent').hidden")
    assert _hash_state(page) == unpicked
    page.go_back()
    page.wait_for_selector("#app-main[data-picked]")
    assert _hash_state(page) == picked
    page.go_forward()
    page.go_forward()
    page.wait_for_function("() => !document.getElementById('view-graph').hidden")
    assert _hash_state(page) == graph
    context.close()


def test_an_old_detail_bookmark_still_opens_the_record(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """A `#detail/<id>` bookmark opens in the List view with the record picked."""
    context = browser.new_context(viewport={"width": 320, "height": 800}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}#detail/ADR-0001")
    page.wait_for_selector("#detail-body .state-line")
    state = _hash_state(page)
    assert state["view"] == "list" and state["picked"] and state["detailShown"], state
    context.close()


def test_back_to_an_old_detail_bookmark_restores_the_view_it_opened_in(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """Load `#detail/<id>`, switch to Graph, go Back: List with the record picked."""
    context = browser.new_context(viewport={"width": 1280, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}#detail/ADR-0001")
    page.wait_for_selector("#detail-body .state-line")
    page.click("#q-graph")
    page.wait_for_function("location.hash.indexOf('#graph/') === 0")
    page.go_back()
    page.wait_for_function("location.hash.indexOf('#graph/') !== 0")
    state = _hash_state(page)
    assert state["view"] == "list" and state["picked"], state
    context.close()


def test_a_focused_lineage_node_shows_one_focus_ring(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """A keyboard-focused node draws its SVG accent ring and no CSS outline."""
    context = browser.new_context(viewport={"width": 1280, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}#graph/ADR-0001")
    node = page.locator('.lineage-wrap g[role="button"]').first
    node.wait_for()
    node.focus()
    page.keyboard.press("Shift+Tab")
    page.keyboard.press("Tab")
    focused = page.evaluate(
        "() => { const g = document.activeElement;"
        " const ring = g.querySelector('.focus-ring');"
        " return { role: g.getAttribute('role'), outline: getComputedStyle(g).outlineStyle,"
        " ringShown: !!ring && !ring.hasAttribute('hidden') }; }"
    )
    assert focused["role"] == "button", focused
    assert focused["outline"] == "none" and focused["ringShown"], focused
    context.close()


_OUTLINE_CLIP_JS = """(el) => {
  const cs = getComputedStyle(el), r = el.getBoundingClientRect();
  const grow = parseFloat(cs.outlineWidth) + parseFloat(cs.outlineOffset);
  const box = { l: r.left - grow, t: r.top - grow, r: r.right + grow, b: r.bottom + grow };
  const clipped = [];
  for (let a = el.parentElement; a; a = a.parentElement) {
    const o = getComputedStyle(a);
    if (o.overflowX === 'visible' && o.overflowY === 'visible') continue;
    const p = a.getBoundingClientRect();
    if (box.l < p.left - 0.5 || box.t < p.top - 0.5 || box.r > p.right + 0.5
        || box.b > p.bottom + 0.5)
      clipped.push(a.localName + '.' + a.className);
  }
  return { grow, clipped }; }"""


@pytest.mark.parametrize("width", (320, 1280))
def test_focus_outlines_are_not_clipped_by_an_ancestor(
    browser: object, tmp_path_factory: pytest.TempPathFactory, width: int
) -> None:
    """A focused Relationships summary and a focused record-content region each have their
    whole outline inside every ancestor that clips."""
    export = _publish_with(
        tmp_path_factory,
        f"outline_clip_{width}",
        [
            (1, "Old", "- **Status:** Accepted\n- **Superseded by:** ADR-0002\n"),
            (2, "New", "- **Status:** Accepted\n- **Supersedes:** ADR-0001\n"),
        ],
        [],
    )
    context = browser.new_context(viewport={"width": width, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export}")
    page.wait_for_selector("li.row")
    _show(page, "list", "ADR-0001")
    page.wait_for_selector("#detail-body .rel-details > summary")
    page.wait_for_selector("#detail-body section.record-content")
    for sel in ("#detail-body .rel-details > summary", "#detail-body section.record-content"):
        page.locator(sel).focus()
        page.keyboard.press("Shift+Tab")
        page.keyboard.press("Tab")  # focus-visible by keyboard
        info = page.evaluate(_OUTLINE_CLIP_JS, page.locator(sel).element_handle())
        assert info["grow"] >= 4, (sel, info)
        assert info["clipped"] == [], (sel, info)
    context.close()


@pytest.mark.parametrize("width", (320, 1280))
def test_diagram_nodes_hold_their_size_and_their_text(
    browser: object, zone_export: pathlib.Path, width: int
) -> None:
    """Every diagram node is at least 24 by 24 CSS px; its first text is its record's title
    and the id follows; node text is at least the shared label size."""
    page = _zone_page(browser, zone_export, width, "light", "graph")
    if page.locator("#back-btn").is_visible():  # one column: a pick hides the list zone
        page.click("#back-btn")
    seen = 0
    for _ in range(2):  # the focused chain, then the atlas
        info = page.evaluate(
            """() => { const recs = JSON.parse(
                document.getElementById('nav-data').textContent).records;
              const p = document.createElement('span'); p.style.font = 'var(--t-label)';
              document.body.appendChild(p);
              const label = parseFloat(getComputedStyle(p).fontSize); p.remove();
              const gs = [...document.querySelectorAll('#view-graph svg [role=button]')];
              return { label, nodes: gs.map(g => {
                const r = g.getBoundingClientRect();
                const rec = recs.find(x => x.id === g.dataset.nodeId);
                const texts = [...g.querySelectorAll('text')];
                return { id: g.dataset.nodeId, w: r.width, h: r.height,
                  first: texts[0].textContent, title: rec.display_title || rec.title,
                  idAt: texts.findIndex(t => t.textContent === g.dataset.nodeId),
                  sizes: texts.map(t => parseFloat(getComputedStyle(t).fontSize)) }; }) }; }"""
        )
        for node in info["nodes"]:
            assert node["w"] >= 24 and node["h"] >= 24, node
            head = node["first"].removesuffix("…")
            assert node["title"].startswith(head) and head, node
            assert node["idAt"] > 0, node
            assert min(node["sizes"]) >= info["label"] - 0.01, (info["label"], node)
        seen += len(info["nodes"])
        if not page.locator("button.atlas-back").count():
            break
        page.evaluate("() => document.querySelector('button.atlas-back').click()")
        page.wait_for_selector(".chain-card svg")
    assert seen or zone_export.name.startswith("hostile"), zone_export
    page.context.close()


def test_name_track_stops_growing_at_2560(browser: object, export_mixed: pathlib.Path) -> None:
    """From 120rem the row's name track is at most 34rem."""
    context = browser.new_context(viewport={"width": 2560, "height": 1200}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_selector("li.row")
    track = page.evaluate(
        "() => parseFloat(getComputedStyle(document.querySelector('.row-link'))"
        ".gridTemplateColumns.split(' ')[0])"
    )
    assert track <= 34 * 16 + 0.5, track
    context.close()


def test_header_order_and_expand_all_state(browser: object, export_mixed: pathlib.Path) -> None:
    """The header reads title, search, Kind, Status; Expand all is disabled while nothing
    can expand and enabled once a record with sections is shown."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.row")
    order = page.evaluate(
        """() => ['.page-title', '#search-input', '#kind-filter', '#status-filter'].map(s => {
          const r = document.querySelector(s).getBoundingClientRect();
          return [r.top, r.left]; })"""
    )
    ids = page.evaluate(
        """() => { const q = s => document.querySelector(s);
          const pairs = [['.page-title', '#search-input'], ['#search-input', '#kind-filter'],
            ['#kind-filter', '#status-filter']];
          return pairs.map(([a, b]) => !!(q(a).compareDocumentPosition(q(b))
            & Node.DOCUMENT_POSITION_FOLLOWING)); }"""
    )
    assert ids == [True, True, True], ids
    assert order[1][0] <= order[2][0] + 1, order  # the search sits on or above the filters
    assert page.locator("#search-input").get_attribute("placeholder")
    assert page.locator("#expand-all-btn").is_disabled()
    page.locator("li.row .row-link").first.click()
    page.wait_for_selector("#detail-body details")
    assert page.locator("#expand-all-btn").is_enabled()


# ── decision-view-questions T1: the question rail, route grammar and list head ──

_RAIL = (
    ("Decisions", "recent", "Recently decided", "What was decided most recently?"),
    ("Decisions", "deciding", "Still being decided", "What is still being decided?"),
    ("Changes", "replaced", "Replaced", "Which decisions were replaced?"),
    ("Changes", "graph", "Lineage", "How did decisions replace each other?"),
    ("Browse", "areas", "By area", "What does each area hold?"),
    ("Browse", "list", "Browse all", "Browse every record"),
)
_HEADS = {
    "recent": ("Decided records", "Newest decision first (ADR Date, RFC Date closed)"),
    "deciding": ("Records still open", "Oldest first (ADR Date, RFC Date opened)"),
    "replaced": (
        "Replaced records",
        "Replaced in full first, then in part; by id within each",
    ),
    "graph": ("Lifecycle graph", "Largest chain first, then by lowest record number"),
    "areas": ("Records by area", "Areas A to Z; newest decision first within each"),
    "list": ("All records", "By kind, then number"),
}
_DECIDED_WORDS = {"accepted", "superseded", "deprecated", "rejected", "withdrawn"}
_DECIDING_WORDS = {"draft", "proposed", "open", "final", "experimental"}


def _island(page: object) -> dict[str, object]:
    """The page's data island, parsed by the browser's JSON reader only."""
    return page.evaluate(  # type: ignore[union-attr, no-any-return]
        "() => JSON.parse(document.getElementById('nav-data').textContent)"
    )


def _word(rec: dict[str, object]) -> str | None:
    """A record's word: the first run of letters in its lifecycle raw value, lowercased."""
    life = rec.get("lifecycle") or {}
    raw = life.get("raw_value") if isinstance(life, dict) and not life.get("missing") else None
    found = re.search(r"[A-Za-z]+", raw or "")
    return found.group(0).lower() if found else None


def _areas_of(rec: dict[str, object]) -> list[str]:
    """A record's areas, as the spec's Terms define them."""
    for field in rec.get("header_fields") or []:  # type: ignore[attr-defined]
        if str(field.get("label", "")).lower() == "areas":
            out: list[str] = []
            for part in str(field.get("display_value") or "").split(","):
                part = part.strip()
                if part and part not in out:
                    out.append(part)
            return out
    return []


def _chain_count(data: dict[str, object]) -> int:
    """Connected groups of two or more records joined by checked relationships."""
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for rel in data["relationships"]:  # type: ignore[attr-defined]
        if rel["trust_class"] == "checked":
            parent[find(rel["from"])] = find(rel["to"])
    return len({find(x) for x in list(parent)})


def _rail_counts(data: dict[str, object]) -> dict[str, int]:
    """The five rail counts computed from the data island."""
    recs = data["records"]  # type: ignore[assignment]
    return {
        "recent": sum(1 for r in recs if _word(r) in _DECIDED_WORDS),  # type: ignore[attr-defined]
        "deciding": sum(1 for r in recs if _word(r) in _DECIDING_WORDS),  # type: ignore[attr-defined]
        "replaced": sum(1 for r in recs if r.get("superseded_by")),  # type: ignore[attr-defined]
        "graph": _chain_count(data),
        "areas": len({a for r in recs for a in _areas_of(r)}),  # type: ignore[attr-defined]
    }


def _visible_regions(page: object) -> list[str]:
    return page.evaluate(  # type: ignore[union-attr, no-any-return]
        "() => ['recent','deciding','replaced','graph','areas','list','context']"
        ".filter(v => !document.getElementById('view-' + v).hidden)"
    )


def _is_picked(page: object) -> bool:
    return page.evaluate(  # type: ignore[union-attr, no-any-return]
        "() => document.getElementById('app-main').hasAttribute('data-picked')"
    )


def _current_links(page: object) -> list[str]:
    return page.evaluate(  # type: ignore[union-attr, no-any-return]
        "() => [...document.querySelectorAll('#question-list a[aria-current]')].map(a => a.id)"
    )


def test_rail_holds_six_links_under_three_headings_with_full_questions(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0001: labels, order, group headings and each link's description."""
    page = _open_page(browser, export_mixed)
    info = page.evaluate(
        """() => { const nav = document.querySelector('nav#questions-nav.questions');
          const rail = nav && nav.querySelector('div#question-list.rail');
          if (!rail) return null;
          return { label: nav.getAttribute('aria-label'),
            groups: [...rail.querySelectorAll('h2.rail-group')].map(h => h.textContent),
            links: [...rail.querySelectorAll('a.question-link')].map(a => ({
              id: a.id, href: a.getAttribute('href'),
              name: a.querySelector('.q-name').textContent,
              desc: document.getElementById(a.getAttribute('aria-describedby')).textContent,
              group: a.closest('ul').previousElementSibling.textContent })) }; }"""
    )
    assert info, "no rail"
    assert info["label"] == "Questions"
    assert info["groups"] == ["Decisions", "Changes", "Browse"]
    assert [(link["group"], link["id"], link["name"], link["desc"]) for link in info["links"]] == [
        (g, f"q-{k}", label, q) for g, k, label, q in _RAIL
    ]
    assert [link["href"] for link in info["links"]] == [f"#{k}" for _, k, _, _ in _RAIL]
    assert page.locator(".worklist .tools nav.seg").count() == 0
    assert page.locator("#btn-list, #btn-graph, #btn-context").count() == 0
    page.context.close()


def test_rail_counts_match_the_data_and_ignore_search_and_filters(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0002: five counts, none on Browse all, unchanged by search, Kind and Status."""
    page = _open_page(browser, export_mixed)
    want = _rail_counts(_island(page))

    def shown() -> dict[str, str | None]:
        return page.evaluate(  # type: ignore[no-any-return]
            """() => Object.fromEntries([...document.querySelectorAll('a.question-link')]
              .map(a => {
              const c = a.querySelector('.q-count');
              return [a.id.slice(2), c ? c.textContent : null]; }))"""
        )

    expect = {k: str(v) for k, v in want.items()} | {"list": None}
    assert shown() == expect
    page.fill("#search-input", "zzzzz-no-match")
    assert shown() == expect
    page.fill("#search-input", "ADR-0001")
    page.click('#kind-filter button[data-kind="RFC"]')
    page.select_option("#status-filter", index=1)
    assert shown() == expect
    page.context.close()


def test_the_page_opens_on_recently_decided(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0003: no hash shows the Recently decided list and marks its link."""
    page = _open_page(browser, export_mixed)
    assert _visible_regions(page) == ["recent"]
    assert _current_links(page) == ["q-recent"]
    assert page.get_attribute("#q-recent", "aria-current") == "page"
    page.context.close()


@pytest.mark.parametrize("view", ("graph", "list"))
def test_list_head_reads_question_then_heading_then_sort_line(
    browser: object, export_mixed: pathlib.Path, view: str
) -> None:
    """AC-0004 (Browse all and Lineage): the region's head in DOM order."""
    page = _open_page(browser, export_mixed)
    page.evaluate(f"() => {{ location.hash = '#{view}'; }}")
    page.wait_for_function(f"() => !document.getElementById('view-{view}').hidden")
    head = page.evaluate(
        f"""() => {{ const r = document.getElementById('view-{view}');
          const q = r.querySelector('p.list-question'), h = r.querySelector('h2.list-title'),
            s = r.querySelector('.list-sort');
          const after = (a, b) =>
            !!(a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
          return {{ q: q && q.textContent, h: h && h.textContent, s: s && s.textContent,
            order: !!q && !!h && !!s && after(q, h) && after(h, s),
            label: r.getAttribute('aria-label'), role: r.getAttribute('role'),
            h2s: r.querySelectorAll('h2').length }}; }}"""
    )
    heading, sort = _HEADS[view]
    question = next(q for _, k, _, q in _RAIL if k == view)
    assert head["q"] == question and head["h"] == heading and head["s"] == sort, head
    assert head["order"] and head["role"] == "region" and head["label"] == heading, head
    assert head["h2s"] == 1, head
    page.context.close()


def test_lineage_shows_every_chain_and_browse_all_every_record_in_export_order(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0011, AC-0012."""
    page = _open_page(browser, export_mixed)
    data = _island(page)
    page.evaluate("() => { location.hash = '#graph'; }")
    page.wait_for_selector("#view-graph .chain-card svg")
    assert page.locator("#view-graph .chain-card").count() == _chain_count(data)
    page.evaluate("() => { location.hash = '#list'; }")
    page.wait_for_selector("#view-list .row-link")
    rows = page.eval_on_selector_all(
        "#view-list .row-link", "els => els.map(e => e.getAttribute('data-id'))"
    )
    assert rows == [r["id"] for r in data["records"]]  # type: ignore[attr-defined]
    page.context.close()


_ROUTES = (
    ("#recent", "recent", None, False),
    ("#deciding", "deciding", None, False),
    ("#replaced", "replaced", None, False),
    ("#graph", "graph", None, False),
    ("#areas", "areas", None, False),
    ("#list", "list", None, False),
    ("#list/ADR-0002", "list", "ADR-0002", True),
    ("#recent/ADR-0002/unpicked", "recent", "ADR-0002", False),
    ("#graph/ADR-0002", "graph", "ADR-0002", True),
    ("#areas/ADR-0002/unpicked", "areas", "ADR-0002", False),
    ("#bogus-view/ADR-0002", "list", None, False),
    ("#constructor", "list", None, False),
    ("#__proto__/ADR-0002", "list", None, False),
)


@pytest.mark.parametrize(("route", "view", "sel", "picked"), _ROUTES)
def test_every_route_form_opens_its_question(
    browser: object,
    export_mixed: pathlib.Path,
    route: str,
    view: str,
    sel: str | None,
    picked: bool,
) -> None:
    """AC-0014: question keys, their selection forms, an unknown first part."""
    context = browser.new_context(viewport={"width": 1280, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"file://{export_mixed}{route}")
    page.wait_for_selector(f"#view-{view}:not([hidden])")
    assert _visible_regions(page) == [view]
    assert _current_links(page) == [f"q-{view}"]
    assert _is_picked(page) is picked
    detail = page.locator("#detail-body h2").text_content()
    assert (detail != "Record detail") is (sel is not None), detail
    assert not errors, errors
    context.close()


def test_a_cold_detail_link_opens_browse_all_with_the_record_picked_and_is_rewritten(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0014: `#detail/<id>` on a cold load."""
    context = browser.new_context(viewport={"width": 320, "height": 800}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}#detail/ADR-0002")
    page.wait_for_selector("#detail-body .state-line")
    assert _visible_regions(page) == ["list"]
    assert _current_links(page) == ["q-list"]
    assert page.evaluate("() => location.hash") == "#list/ADR-0002"
    assert page.evaluate("() => document.getElementById('app-main').hasAttribute('data-picked')")
    context.close()


def test_context_routes_show_guidance_and_mark_no_rail_link(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0015: `#context/<id>` and bare `#context`."""
    page = _open_page(browser, export_mixed)
    page.evaluate("() => { location.hash = '#context/ADR-0001'; }")
    page.wait_for_function("() => !document.getElementById('view-context').hidden")
    assert "Guidance context: ADR-0001" in (page.locator("#view-context").text_content() or "")
    assert _current_links(page) == []
    page.evaluate("() => { location.hash = '#context'; }")
    page.wait_for_function(
        "() => document.getElementById('view-context').textContent.includes('Pick')"
    )
    assert _visible_regions(page) == ["context"]
    assert "Pick a record, then choose Guidance context in its detail." in (
        page.locator("#view-context").text_content() or ""
    )
    assert _current_links(page) == []
    page.context.close()


@pytest.mark.parametrize("how", ("Enter", "click"))
def test_rail_activation_shows_the_list_focuses_its_heading_and_keeps_the_selection(
    browser: object, export_mixed: pathlib.Path, how: str
) -> None:
    """AC-0016: focus, unpicked selection, one history entry per route change, Back."""
    context = browser.new_context(viewport={"width": 1280, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_selector("li.row")
    _show(page, "list", "ADR-0001")
    before = page.evaluate("() => history.length")

    def activate(key: str) -> None:
        if how == "Enter":
            page.focus(f"#q-{key}")
            page.keyboard.press("Enter")
        else:
            page.click(f"#q-{key}")

    activate("graph")
    page.wait_for_function("() => !document.getElementById('view-graph').hidden")
    focus = page.evaluate(
        "() => [document.activeElement.tagName, document.activeElement.closest('[id^=view-]').id]"
    )
    assert focus == ["H2", "view-graph"], focus
    assert page.evaluate("() => location.hash") == "#graph/ADR-0001/unpicked"
    assert page.evaluate("() => history.length") == before + 1
    assert not _is_picked(page)
    assert "ADR-0001" in (page.locator("#detail-body .state-line").text_content() or "")
    activate("graph")  # the same route: no new entry
    assert page.evaluate("() => history.length") == before + 1
    page.go_back()
    page.wait_for_function("() => !document.getElementById('view-list').hidden")
    assert page.evaluate("() => location.hash") == "#list/ADR-0001"
    assert _current_links(page) == ["q-list"]
    assert page.evaluate("() => document.getElementById('app-main').hasAttribute('data-picked')")
    context.close()


def test_the_default_page_is_recent_so_activating_it_adds_no_entry(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0016: the empty hash is the Recently decided route."""
    page = _open_page(browser, export_mixed)
    before = page.evaluate("() => history.length")
    page.click("#q-recent")
    assert page.evaluate("() => history.length") == before
    page.context.close()


@pytest.mark.parametrize("width", _WIDTHS)
def test_rail_rectangles_at_each_width(
    browser: object, export_mixed: pathlib.Path, width: int
) -> None:
    """AC-0022: beside the zones from 90rem, a tab row above them below it."""
    context = browser.new_context(viewport={"width": width, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_selector("li.row")
    info = page.evaluate(
        """() => { const rc = s => document.querySelector(s).getBoundingClientRect();
          const rail = rc('#question-list'), list = rc('.worklist'), zones = rc('#app-main');
          const links = [...document.querySelectorAll('a.question-link')]
            .map(a => a.getBoundingClientRect());
          return { rail: { l: rail.left, r: rail.right, t: rail.top, b: rail.bottom,
              w: rail.width },
            list: { l: list.left, t: list.top, b: list.bottom },
            zonesTop: zones.top, tops: links.map(x => Math.round(x.top)),
            rem: parseFloat(getComputedStyle(document.documentElement).fontSize) }; }"""
    )
    rail, lst = info["rail"], info["list"]
    if width >= 1680:
        assert rail["r"] <= lst["l"] + 0.5, info
        assert abs(rail["w"] - 16.5 * info["rem"]) <= 1, info
        assert rail["t"] < lst["b"] and lst["t"] < rail["b"], info
    elif width == 1280:
        assert len(set(info["tops"])) == 1, info
        assert rail["b"] <= info["zonesTop"] + 0.5, info
    else:
        assert rail["b"] <= info["zonesTop"] + 0.5, info
    context.close()


_RAIL_JS = """() => { const nav = document.getElementById('questions-nav');
  const nr = nav.getBoundingClientRect(), bad = [], small = [];
  const rgb = s => (s.match(/[\\d.]+/g) || []).map(Number);
  const lum = c => { const v = c.slice(0, 3).map(x => { x /= 255;
    return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); });
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const backdrop = e => { for (let n = e; n && n.nodeType === 1; n = n.parentElement) {
      const c = rgb(getComputedStyle(n).backgroundColor);
      if (c.length >= 3 && (c.length < 4 || c[3] > 0)) return c; }
    return rgb(getComputedStyle(document.body).backgroundColor); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  for (const e of nav.querySelectorAll('*')) {
    const r = e.getBoundingClientRect();
    if (r.width <= 1 && r.height <= 1) continue;
    if (r.left < nr.left - 1 || r.right > nr.right + 1) bad.push(['edge', e.className]);
    const own = [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());
    if (own) { const q = ratio(rgb(getComputedStyle(e).color), backdrop(e));
      if (q < 4.5) bad.push(['contrast', e.className, Math.round(q * 100) / 100]); }
  }
  for (const a of nav.querySelectorAll('a.question-link')) {
    const r = a.getBoundingClientRect();
    if (r.width < 24 || r.height < 24) small.push([a.id, r.width, r.height]); }
  return { bad, small, scroll: document.documentElement.scrollWidth, view: innerWidth,
    links: nav.querySelectorAll('a.question-link').length }; }"""


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_IDS)
def test_rail_fits_reads_and_is_large_enough_across_the_matrix(
    browser: object, zone_export: pathlib.Path, width: int, scheme: str
) -> None:
    """AC-0023: no element past the rail's edge, no sideways page scroll, text at 4.5:1,
    every link at least 24 by 24 CSS px."""
    page = _zone_page(browser, zone_export, width, scheme, "list")
    info = page.evaluate(_RAIL_JS)  # type: ignore[union-attr]
    assert info["links"] == 6, info
    assert info["bad"] == [] and info["small"] == [], info
    assert info["scroll"] <= info["view"], info
    page.context.close()  # type: ignore[union-attr]


# ── decision-view-questions T2: the four new question lists ─────────────────────

_LIST_KEYS = ("recent", "deciding", "replaced", "areas")
_QUESTION_LISTS = (*_LIST_KEYS, "list")
_EMPTY_TEXT = {
    "recent": (
        "No record has a decided status: Accepted, Superseded, Deprecated, Rejected or Withdrawn."
    ),
    "deciding": (
        "Nothing is being decided: no record has a Draft, Proposed, Open, Final Comment Period"
        " or Experimental status."
    ),
    "replaced": "No record is replaced in full or in part.",
    "areas": "No record has an Areas field.",
}


@pytest.fixture(scope="module")
def export_chain(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """The lineage-chain fixture: three decided records, one chain, no Areas field."""
    return _export(tmp_path_factory, FIXTURE_CHAIN, "chain")


@pytest.fixture(scope="module")
def export_proposed_only(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """One `Proposed` ADR: nothing decided, nothing replaced."""
    return _publish_with(
        tmp_path_factory, "proposed_only", [(1, "Only proposal", "- **Status:** Proposed\n")], []
    )


@pytest.fixture(scope="module")
def export_every_record_has_an_area(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Two records, both with an area."""
    return _publish_with(
        tmp_path_factory,
        "all_areas",
        [
            (1, "First", "- **Status:** Accepted\n- **Areas:** Alpha\n"),
            (2, "Second", "- **Status:** Accepted\n- **Areas:** Beta, Alpha\n"),
        ],
        [],
    )


@pytest.fixture(scope="module")
def export_one_without_area(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Four records: one with no area, one carrying an unresolved claim, one superseded."""
    return _publish_with(
        tmp_path_factory,
        "one_no_area",
        [
            (
                1,
                "Claimant",
                "- **Status:** Accepted\n- **Superseded by:** ADR-0099\n- **Areas:** Alpha\n",
            ),
            (2, "Plain", "- **Status:** Accepted\n- **Date:** 2025-01-01\n"),
            (
                3,
                "Old",
                "- **Status:** Superseded\n- **Superseded by:** ADR-0004\n- **Areas:** Alpha\n",
            ),
            (4, "New", "- **Status:** Accepted\n- **Supersedes:** ADR-0003\n- **Areas:** Alpha\n"),
        ],
        [],
    )


def _header_date(rec: dict[str, object], label: str) -> str | None:
    """A header date as the spec's Terms define it."""
    for field in rec.get("header_fields") or []:  # type: ignore[attr-defined]
        if str(field.get("label", "")).lower() == label:
            head = str(field.get("raw_value") or "")[:10]
            return head if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", head) else None
    return None


def _decision_date(rec: dict[str, object]) -> str | None:
    return _header_date(rec, "date closed" if rec["kind"] == "RFC" else "date")


def _opened_date(rec: dict[str, object]) -> str | None:
    return _header_date(rec, "date opened" if rec["kind"] == "RFC" else "date")


def _decision_order(recs: list[dict[str, object]], pos: dict[str, int]) -> list[dict[str, object]]:
    """Dated records newest first (ties in reverse export order), then the undated."""
    dated = sorted(
        (r for r in recs if _decision_date(r)),
        key=lambda r: (_decision_date(r), pos[str(r["id"])]),
        reverse=True,
    )
    return dated + [r for r in recs if not _decision_date(r)]


def _expected_sections(data: dict[str, object], key: str) -> list[list[object]]:
    """Each list's sections from the data island: [head or area, [ids]] in display order,
    before search and filters. Built in Python, independent of the page script."""
    recs: list[dict[str, object]] = data["records"]  # type: ignore[assignment]
    pos = {str(r["id"]): i for i, r in enumerate(recs)}
    if key == "recent":
        decided = [r for r in recs if _word(r) in _DECIDED_WORDS]
        ordered = _decision_order(decided, pos)
        return [
            [None, [r["id"] for r in ordered if _decision_date(r)]],
            ["No decision date", [r["id"] for r in ordered if not _decision_date(r)]],
        ]
    if key == "deciding":
        deciding = [r for r in recs if _word(r) in _DECIDING_WORDS]
        dated = sorted(
            (r for r in deciding if _opened_date(r)),
            key=lambda r: (_opened_date(r), pos[str(r["id"])]),
        )
        return [
            [None, [r["id"] for r in dated]],
            ["No opened date", [r["id"] for r in deciding if not _opened_date(r)]],
        ]
    if key == "replaced":
        full = [r for r in recs if any(not s["partial"] for s in r.get("superseded_by") or [])]
        part = [r for r in recs if r.get("superseded_by") and r not in full]
        return [
            ["Replaced in full", [r["id"] for r in full]],
            ["Replaced in part", [r["id"] for r in part]],
        ]
    if key == "areas":
        names = sorted({a for r in recs for a in _areas_of(r)}, key=lambda a: (a.lower(), a))
        return [
            [a, [r["id"] for r in _decision_order([r for r in recs if a in _areas_of(r)], pos)]]
            for a in names
        ]
    return [[None, [r["id"] for r in recs]]]


def _matches(rec: dict[str, object], search: str, kind: str, status: str) -> bool:
    """Whether the page's search, Kind filter and Status filter keep a record."""
    life = rec.get("lifecycle") or {}
    raw = None if life.get("missing") else life.get("raw_value")  # type: ignore[attr-defined]
    if kind and rec["kind"] != kind:
        return False
    if status and raw != status:
        return False
    if search:
        shown = str(life.get("display_value") or raw or "(missing)")  # type: ignore[attr-defined]
        hay = (str(rec["id"]), str(rec["title"]), shown)
        return any(search.lower() in h.lower() for h in hay)
    return True


_STRUCT_JS = """(key) => { const r = document.getElementById('view-' + key); const out = [];
  const ids = n => [...n.querySelectorAll('.row-link')].map(b => b.dataset.id);
  for (const n of r.children) {
    if (n.classList.contains('list-head')) continue;
    if (n.matches('h3.group-head')) out.push({ head: n.textContent });
    else if (n.matches('ul.rows')) out.push({ ids: ids(n) });
    else if (n.matches('details.key.area-group')) out.push({
      area: n.querySelector('summary').textContent, open: n.open, ids: ids(n),
      kids: [...n.children].map(c => c.localName) });
    else out.push({ other: n.localName + '.' + n.className });
  }
  return out; }"""


def _go(page: object, key: str, record_id: str | None = None) -> None:
    """Route to a list, with a record selected when given, and wait for its region."""
    page.evaluate(  # type: ignore[union-attr]
        f"() => {{ location.hash = '#{key}{'/' + record_id if record_id else ''}'; }}"
    )
    page.wait_for_function(  # type: ignore[union-attr]
        f"() => !document.getElementById('view-{key}').hidden"
        f" && document.querySelector('#view-{key} h2.list-title')"
    )


def _structure(page: object, key: str) -> list[dict[str, object]]:
    return page.evaluate(_STRUCT_JS, key)  # type: ignore[union-attr, no-any-return]


def _expected_structure(sections: list[list[object]], key: str) -> list[dict[str, object]]:
    """The region's children for `sections`, empty sections left out."""
    out: list[dict[str, object]] = []
    for head, ids in sections:
        if not ids:
            continue
        if key == "areas":
            out.append({"area": f"{head} ({len(ids)})", "ids": ids})
        else:
            if head:
                out.append({"head": head})
            out.append({"ids": ids})
    return out


def _flat(structure: list[dict[str, object]]) -> list[dict[str, object]]:
    """Drop the area sections' `open` and `kids` keys so a structure compares to the oracle."""
    return [{k: v for k, v in s.items() if k in ("head", "ids", "area")} for s in structure]


def _row_ids(page: object, key: str) -> list[str]:
    return page.eval_on_selector_all(  # type: ignore[union-attr, no-any-return]
        f"#view-{key} .row-link", "els => els.map(e => e.getAttribute('data-id'))"
    )


@pytest.mark.parametrize("fixture_name", ("export_questions", "export_mixed"))
def test_recently_decided_rows_follow_decision_order_with_an_undated_tail(
    browser: object, request: pytest.FixtureRequest, fixture_name: str
) -> None:
    """AC-0005: decided records newest first, equal dates in reverse export order, then a
    "No decision date" heading and the undated in export order; each dated row's context
    starts with its date."""
    page = _open_page(browser, request.getfixturevalue(fixture_name))
    _go(page, "recent")
    data = _island(page)
    sections = _expected_sections(data, "recent")
    assert _flat(_structure(page, "recent")) == _expected_structure(sections, "recent")
    dates = {str(r["id"]): _decision_date(r) for r in data["records"]}  # type: ignore[attr-defined]
    ctx = page.eval_on_selector_all(
        "#view-recent .row",
        "els => els.map(e => [e.querySelector('.row-link').dataset.id,"
        " e.querySelector('.c-context').textContent])",
    )
    for rid, text in ctx:
        want = f"{dates[rid]} · " if dates[rid] else ""
        assert text.startswith(want), (rid, text)
        assert want or not re.match(r"[0-9]{4}-", text), (rid, text)
    if fixture_name == "export_questions":
        assert sections[0][1] == [
            "ADR-0004", "RFC-0004", "ADR-0002", "ADR-0001", "ADR-0005",
            "ADR-0014", "ADR-0013", "ADR-0012", "ADR-0011",
        ]  # fmt: skip
        assert sections[1][1] == ["ADR-0003", "RFC-0001"]
    assert page._errors == []  # type: ignore[attr-defined]
    page.context.close()  # type: ignore[union-attr]


def test_still_being_decided_rows_run_oldest_first_and_leave_out_odd_words(
    browser: object, export_questions: pathlib.Path
) -> None:
    """AC-0006: one record per being-decided word, dated oldest first with ties in export
    order, then a "No opened date" heading; `constructor` and `tostring` appear only in
    Browse all and By area."""
    page = _open_page(browser, export_questions)
    _go(page, "deciding")
    data = _island(page)
    sections = _expected_sections(data, "deciding")
    assert _flat(_structure(page, "deciding")) == _expected_structure(sections, "deciding")
    assert sections[0][1] == ["ADR-0007", "ADR-0006", "RFC-0002", "RFC-0003"]
    assert sections[1][1] == ["ADR-0008"]
    words = {str(r["id"]): _word(r) for r in data["records"]}  # type: ignore[attr-defined]
    assert sorted(
        w for w in words.values() if w and w not in _DECIDED_WORDS | _DECIDING_WORDS
    ) == [
        "constructor",
        "tostring",
    ]
    odd = [i for i, w in words.items() if w in ("constructor", "tostring")]
    ctx = page.eval_on_selector_all(
        "#view-deciding .row",
        "els => els.map(e => [e.querySelector('.row-link').dataset.id,"
        " e.querySelector('.c-context').textContent])",
    )
    dates = {str(r["id"]): _opened_date(r) for r in data["records"]}  # type: ignore[attr-defined]
    for rid, text in ctx:
        assert text.startswith(
            f"{dates[rid]} · " if dates[rid] else "ADR · " if rid.startswith("ADR") else "RFC · "
        ), text
    for key in ("recent", "deciding", "replaced"):
        _go(page, key)
        assert not set(odd) & set(_row_ids(page, key)), key
    for key in ("list", "areas"):
        _go(page, key)
        assert set(odd) <= set(_row_ids(page, key)), key
    page.context.close()  # type: ignore[union-attr]


@pytest.mark.parametrize(
    ("fixture_name", "key"),
    (
        ("export_chain", "deciding"),
        ("export_chain", "areas"),
        ("export_proposed_only", "recent"),
        ("export_proposed_only", "replaced"),
    ),
)
def test_an_empty_question_shows_its_own_text_never_the_no_match_message(
    browser: object, request: pytest.FixtureRequest, fixture_name: str, key: str
) -> None:
    """AC-0007: a list holding no record before search and filters has no rows, shows its
    empty text and no Reset control."""
    page = _open_page(browser, request.getfixturevalue(fixture_name))
    _go(page, key)
    assert _row_ids(page, key) == []
    assert page.locator(f"#view-{key} p.empty").all_inner_texts() == [_EMPTY_TEXT[key]]  # type: ignore[union-attr]
    assert "No records match" not in page.inner_text(f"#view-{key}")  # type: ignore[union-attr]
    assert page.locator(f"#view-{key} .reset-btn").count() == 0  # type: ignore[union-attr]
    assert page.locator(f"#view-{key} details, #view-{key} .group-head").count() == 0  # type: ignore[union-attr]
    assert page._errors == []  # type: ignore[attr-defined]
    page.context.close()  # type: ignore[union-attr]


@pytest.mark.parametrize("fixture_name", ("export_questions", "export_mixed"))
def test_replaced_rows_sit_under_in_full_and_in_part_headings(
    browser: object, request: pytest.FixtureRequest, fixture_name: str
) -> None:
    """AC-0008: full first, then part, each in export order, a heading shown only when it
    has records, and each row keeping its supersession notice."""
    page = _open_page(browser, request.getfixturevalue(fixture_name))
    _go(page, "replaced")
    data = _island(page)
    sections = _expected_sections(data, "replaced")
    assert _flat(_structure(page, "replaced")) == _expected_structure(sections, "replaced")
    if fixture_name == "export_questions":
        assert sections == [["Replaced in full", ["ADR-0011"]], ["Replaced in part", ["ADR-0013"]]]
    rows = page.locator("#view-replaced li.row")  # type: ignore[union-attr]
    assert rows.count() == sum(len(ids) for _, ids in sections)  # type: ignore[arg-type]
    for i in range(rows.count()):
        assert rows.nth(i).locator(".supersede-banner").count() >= 1
    page.context.close()  # type: ignore[union-attr]


def test_by_area_has_one_closed_section_per_area_in_name_order(
    browser: object, export_questions: pathlib.Path
) -> None:
    """AC-0009: sections ordered case-insensitively then by code point, closed at first
    show, summary "<area> (<count>)", rows in decision order, no heading inside, a record
    with several areas in each, and a section a search empties hidden."""
    page = _open_page(browser, export_questions)
    _go(page, "areas")
    data = _island(page)
    sections = _expected_sections(data, "areas")
    got = _structure(page, "areas")
    assert _flat(got) == _expected_structure(sections, "areas")
    assert [s["area"].rsplit(" (", 1)[0] for s in got] == [  # type: ignore[attr-defined]
        "<img src=x onerror=alert(1)>", "__proto__", "Auth", "auth", "Billing",
        "constructor", "Platform",
    ]  # fmt: skip
    assert all(s["open"] is False for s in got)
    assert all(s["kids"] == ["summary", "ul"] for s in got)  # no heading inside a section
    by_area = {str(s[0]): s[1] for s in sections}
    assert "ADR-0001" in by_area["Billing"] and "ADR-0001" in by_area["Auth"]  # type: ignore[operator]
    assert by_area["Billing"].count("ADR-0005") == 1  # type: ignore[attr-defined]
    ctx = page.eval_on_selector_all(
        "#view-areas .row", "els => els.map(e => e.querySelector('.c-context').textContent)"
    )
    assert len(ctx) == sum(len(s["ids"]) for s in got)  # type: ignore[arg-type]
    # Search narrows the counts and hides a section left empty, with the list keeping records.
    page.fill("#search-input", "invoice")
    kept = {str(r["id"]) for r in data["records"] if _matches(r, "invoice", "", "")}  # type: ignore[attr-defined]
    want = [
        {"area": f"{a} ({len(n)})", "ids": n}
        for a, ids in by_area.items()
        if (n := [i for i in ids if i in kept])  # type: ignore[attr-defined]
    ]
    narrowed = _flat(_structure(page, "areas"))
    assert narrowed == want
    assert {"area": "Billing (2)", "ids": ["ADR-0001", "ADR-0003"]} in narrowed
    assert not any(s["area"].startswith("auth ") for s in narrowed)  # type: ignore[attr-defined]
    assert len(narrowed) < len(sections) and narrowed
    page.fill("#search-input", "")
    page.click("#expand-all-btn")
    assert page.eval_on_selector_all("#view-areas details", "els => els.every(e => e.open)")
    assert page._errors == []  # type: ignore[attr-defined]
    page.context.close()  # type: ignore[union-attr]


def test_by_area_head_counts_the_records_with_no_area(
    browser: object,
    export_questions: pathlib.Path,
    export_one_without_area: pathlib.Path,
    export_every_record_has_an_area: pathlib.Path,
    export_chain: pathlib.Path,
) -> None:
    """AC-0010: "<n> records have no area; Browse all lists them." when some but not all
    records have an area; absent when every record has one and when none does."""
    page = _open_page(browser, export_questions)
    _go(page, "areas")
    recs = _island(page)["records"]
    n = sum(1 for r in recs if not _areas_of(r))  # type: ignore[attr-defined]
    assert n == 8
    line = f"{n} records have no area; Browse all lists them."
    assert page.locator("#view-areas .list-head").inner_text().count(line) == 1  # type: ignore[union-attr]
    page.context.close()  # type: ignore[union-attr]
    page = _open_page(browser, export_one_without_area)
    _go(page, "areas")
    assert page.locator("#view-areas .list-noarea").all_inner_texts() == [  # type: ignore[union-attr]
        "1 record has no area; Browse all lists them."
    ]
    page.context.close()  # type: ignore[union-attr]
    for export in (export_every_record_has_an_area, export_chain):
        page = _open_page(browser, export)
        _go(page, "areas")
        assert "have no area" not in page.inner_text("#view-areas")  # type: ignore[union-attr]
        assert "has no area" not in page.inner_text("#view-areas")  # type: ignore[union-attr]
        page.context.close()  # type: ignore[union-attr]


@pytest.mark.parametrize("key", _QUESTION_LISTS)
def test_each_list_narrows_and_counts_its_records_once(
    browser: object, export_questions: pathlib.Path, key: str
) -> None:
    """AC-0013: search, Kind and Status narrow a list's rows, and the count line reads
    "<shown> of <total> records shown" over distinct records; an emptied list shows the
    no-match message and Reset."""
    page = _open_page(browser, export_questions)
    _go(page, key)
    data = _island(page)
    recs: list[dict[str, object]] = data["records"]  # type: ignore[assignment]
    by_id = {str(r["id"]): r for r in recs}
    members = {str(i) for _, ids in _expected_sections(data, key) for i in ids}  # type: ignore[attr-defined]
    counts = page.locator(f"#view-{key} .list-count")  # type: ignore[union-attr]
    assert counts.inner_text() == f"{len(members)} of {len(members)} records shown"
    cases = (("invoice", "", ""), ("", "RFC", ""), ("", "", "Accepted"), ("a", "ADR", "Accepted"))
    for search, kind, status in cases:
        page.fill("#search-input", search)
        page.click(f'#kind-filter button[data-kind="{kind}"]')
        page.select_option("#status-filter", value=status)
        want = {i for i in members if _matches(by_id[i], search, kind, status)}
        assert set(_row_ids(page, key)) == want, (key, search, kind, status)
        if want:
            assert counts.inner_text() == f"{len(want)} of {len(members)} records shown"
        else:
            assert page.locator(f"#view-{key} p.empty").inner_text().startswith("No records match")  # type: ignore[union-attr]
            assert page.locator(f"#view-{key} .reset-btn").count() == 1  # type: ignore[union-attr]
    page.fill("#search-input", "zzzzz-no-match")
    page.click('#kind-filter button[data-kind=""]')
    page.select_option("#status-filter", value="")
    assert page.locator(f"#view-{key} p.empty").inner_text().startswith("No records match")  # type: ignore[union-attr]
    page.click(f"#view-{key} .reset-btn")
    assert set(_row_ids(page, key)) == members
    assert page._errors == []  # type: ignore[attr-defined]
    page.context.close()  # type: ignore[union-attr]


def test_a_record_under_two_areas_counts_once(
    browser: object, export_questions: pathlib.Path
) -> None:
    """AC-0013: By area's counts are over distinct records, though ADR-0001 has two rows."""
    page = _open_page(browser, export_questions)
    _go(page, "areas")
    rows = _row_ids(page, "areas")
    assert rows.count("ADR-0001") == 2
    total = len(set(rows))
    assert total < len(rows)
    assert page.locator("#view-areas .list-count").inner_text() == (
        f"{total} of {total} records shown"
    )
    page.context.close()  # type: ignore[union-attr]


@pytest.mark.parametrize("key", _QUESTION_LISTS)
def test_every_row_of_the_selected_record_is_marked_current(
    browser: object, export_questions: pathlib.Path, key: str
) -> None:
    """AC-0017: each row of the selected record carries aria-current="true", and no other row."""
    page = _open_page(browser, export_questions)
    _go(page, key, "ADR-0001")
    rows = page.eval_on_selector_all(
        f"#view-{key} .row-link",
        "els => els.map(e => [e.dataset.id, e.getAttribute('aria-current')])",
    )
    assert all((cur == "true") == (rid == "ADR-0001") for rid, cur in rows), rows
    want = {"recent": 1, "deciding": 0, "replaced": 0, "areas": 2, "list": 1}[key]
    assert sum(1 for rid, _ in rows if rid == "ADR-0001") == want
    page.context.close()  # type: ignore[union-attr]


def _narrow_page(browser: object, export: pathlib.Path, record_id: str, key: str) -> object:
    """A 320 px page on `key` with `record_id` picked, so the detail replaces the list."""
    context = browser.new_context(viewport={"width": 320, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page._errors = errors  # type: ignore[attr-defined]
    page.goto(f"file://{export}")
    page.wait_for_selector("li.row")
    _go(page, key, record_id)
    assert _is_picked(page)
    return page


_FOCUS_JS = """() => { const a = document.activeElement;
  return { id: a.dataset && a.dataset.id, cur: a.getAttribute('aria-current'),
    tag: a.localName, inH2: a.matches('#view-' + %s + ' h2'),
    first: a === [...document.querySelectorAll('#view-' + %s + ' .row-link')]
      .find(b => b.dataset.id === a.dataset.id) }; }"""


@pytest.mark.parametrize(
    ("record_id", "closed"),
    (
        ("ADR-0001", ("Auth", "Billing")),
        ("ADR-0004", ("<img src=x onerror=alert(1)>", "constructor", "__proto__")),
    ),
)
def test_back_to_list_in_by_area_focuses_the_first_row_and_opens_its_sections(
    browser: object, export_questions: pathlib.Path, record_id: str, closed: tuple[str, ...]
) -> None:
    """AC-0017, AC-0024: at 320 px Back to list focuses the first row of the picked record and
    opens every section holding it, with no page error, hostile area names included."""
    page = _narrow_page(browser, export_questions, record_id, "areas")
    assert page.eval_on_selector_all(  # type: ignore[union-attr]
        "#view-areas details", "els => els.every(e => !e.open)"
    )
    page.get_by_role("button", name="Back to list").click()  # type: ignore[union-attr]
    info = page.evaluate(_FOCUS_JS % ("'areas'", "'areas'"))  # type: ignore[union-attr]
    assert info["id"] == record_id and info["cur"] == "true" and info["first"], info
    opened = page.eval_on_selector_all(  # type: ignore[union-attr]
        "#view-areas details",
        "els => els.filter(e => e.open).map(e => e.querySelector('summary').textContent)",
    )
    assert [o.rsplit(" (", 1)[0] for o in opened] == sorted(closed, key=lambda a: (a.lower(), a))
    assert page._errors == []  # type: ignore[attr-defined]
    page.context.close()  # type: ignore[union-attr]


def test_back_to_list_falls_back_to_the_heading_when_the_list_has_no_such_row(
    browser: object, export_questions: pathlib.Path
) -> None:
    """AC-0017: a record the current list does not hold leaves focus on the list's h2."""
    page = _narrow_page(browser, export_questions, "ADR-0001", "deciding")
    page.get_by_role("button", name="Back to list").click()  # type: ignore[union-attr]
    info = page.evaluate(_FOCUS_JS % ("'deciding'", "'deciding'"))  # type: ignore[union-attr]
    assert info["inH2"], info
    page.context.close()  # type: ignore[union-attr]


def test_hostile_area_names_are_sections_of_literal_text_and_add_no_elements(
    browser: object, export_questions: pathlib.Path
) -> None:
    """AC-0024 (By area): markup-shaped and inherited-property area names each form their own
    section as literal text, add no element beyond the list markup and raise no error."""
    page = _open_page(browser, export_questions)
    dialogs: list[str] = []
    page.on("dialog", lambda d: dialogs.append(d.message))
    _go(page, "areas", "ADR-0004")
    sums = page.locator("#view-areas details > summary").all_inner_texts()  # type: ignore[union-attr]
    for name in ("<img src=x onerror=alert(1)>", "constructor", "__proto__"):
        assert f"{name} (1)" in sums, sums
    tags = set(page.eval_on_selector_all("#view-areas *", "els => els.map(e => e.localName)"))
    assert tags <= {
        "div",
        "p",
        "h2",
        "h3",
        "details",
        "summary",
        "ul",
        "li",
        "button",
        "span",
        "a",
    }, tags
    assert (
        page.locator(
            "#view-areas :is(img, script, svg), #detail-body :is(img, script, svg)"
        ).count()
        == 0
    )  # type: ignore[union-attr]
    assert page.evaluate("() => ({}).constructor === Object && ({}).x === undefined")  # type: ignore[union-attr]
    assert dialogs == [] and page._errors == []  # type: ignore[attr-defined]
    page.context.close()  # type: ignore[union-attr]


@pytest.mark.parametrize("key", _LIST_KEYS)
def test_a_marked_row_carries_its_supersession_marker_or_unresolved_note(
    browser: object,
    export_questions: pathlib.Path,
    export_one_without_area: pathlib.Path,
    export_mixed: pathlib.Path,
    key: str,
) -> None:
    """AC-0030: every row of a superseded record has the criterion-0025 marker, and every row
    of a record with only unresolved claims has the unresolved note, as Browse all's do."""
    seen = 0
    for export in (export_questions, export_mixed, export_one_without_area):
        page = _open_page(browser, export)
        _go(page, key)
        recs = {str(r["id"]): r for r in _island(page)["records"]}  # type: ignore[attr-defined]
        rows = page.eval_on_selector_all(
            f"#view-{key} li.row",
            """els => els.map(e => [e.querySelector('.row-link').dataset.id,
              [...e.querySelectorAll(':scope > .supersede-banner')].map(b =>
                [b.textContent, b.classList.contains('is-unresolved')])])""",
        )
        for rid, notes in rows:
            rec = recs[rid]
            if rec["superseded_by"]:
                assert notes and not any(u for _, u in notes), (rid, notes)
                assert len(notes) == len(rec["superseded_by"])  # type: ignore[arg-type]
                seen += 1
            elif rec["unresolved_claims"]:
                assert len(notes) == 1 and notes[0][1], (rid, notes)
                assert notes[0][0].startswith("Unresolved supersession claim: ")
                seen += 1
            else:
                assert notes == [], (rid, notes)
        page.context.close()  # type: ignore[union-attr]
    assert seen >= 2 or key == "deciding", key


def test_unresolved_claim_note_appears_in_by_area_rows(
    browser: object, export_one_without_area: pathlib.Path
) -> None:
    """AC-0030: the unresolved note on a By area row."""
    page = _open_page(browser, export_one_without_area)
    _go(page, "areas")
    assert page.locator("#view-areas .row .is-unresolved").count() == 1  # type: ignore[union-attr]
    page.context.close()  # type: ignore[union-attr]


def test_rail_counts_on_the_questions_fixture_match_the_data_and_ignore_search(
    browser: object, export_questions: pathlib.Path
) -> None:
    """AC-0002: decided, being decided, replaced, chains and distinct areas on `questions`,
    where `constructor` and `tostring` records count only in the area count."""
    page = _open_page(browser, export_questions)
    want = _rail_counts(_island(page))
    assert want == {"recent": 11, "deciding": 5, "replaced": 2, "graph": 2, "areas": 7}

    def shown() -> dict[str, str]:
        return page.evaluate(  # type: ignore[no-any-return]
            """() => Object.fromEntries([...document.querySelectorAll('a.question-link .q-count')]
              .map(c => [c.closest('a').id.slice(2), c.textContent]))"""
        )

    expect = {k: str(v) for k, v in want.items()}
    assert shown() == expect
    page.fill("#search-input", "invoice")
    page.click('#kind-filter button[data-kind="RFC"]')
    assert shown() == expect
    page.context.close()  # type: ignore[union-attr]


@pytest.mark.parametrize("view", _LIST_KEYS)
def test_list_head_for_the_four_new_questions_reads_question_heading_sort_line(
    browser: object, export_mixed: pathlib.Path, view: str
) -> None:
    """AC-0004 (Recently decided, Still being decided, Replaced, By area)."""
    test_list_head_reads_question_then_heading_then_sort_line(browser, export_mixed, view)


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_IDS)
@pytest.mark.parametrize(
    "check",
    (
        test_zones_are_soft_and_rows_are_flat,
        test_zones_do_not_overflow_their_edges,
        test_no_element_carries_a_style_attribute_through_pick_toggle_and_focus,
        test_text_and_control_borders_have_enough_contrast,
    ),
    ids=lambda f: f.__name__,
)
def test_by_area_list_meets_the_matrix_checks_with_every_section_open(
    browser: object, export_questions: pathlib.Path, width: int, scheme: str, check: object
) -> None:
    """decision-view-style AC-0008, 0010, 0014 and 0027, with "each view" extended to By area:
    the slice-1 checks run over the `questions` export with every section open."""
    check(browser, export_questions, width, scheme, "areas")  # type: ignore[operator]
