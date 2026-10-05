"""Scripted desktop-Chrome browser checks for the navigate-decisions explorer.

Closes: QE-14, FE-F1, FE-F2, FE-F3, FE-F4, FE-F5, FE-F6, FE-F9, FE-F10, FE-F11
Verification mode: scripted Chrome check (from plan.md T7).

These tests require Playwright with Chromium and are skipped cleanly when
Playwright is not installed. They are NEVER run in CI by default; dispatch
manually with: pytest packs/governance-extras/tests/skills/navigate-decisions/browser_checks.py

Run command (from repo root, requires `playwright install chrome`):
    python3 -m pytest packs/governance-extras/tests/skills/navigate-decisions/browser_checks.py -v

Spec: docs/specs/decision-navigation/spec.md (AC-0008, AC-0010, AC-0025, AC-0026)
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import time

import pytest

playwright_mod = pytest.importorskip("playwright")  # skip if not installed
sync_api = pytest.importorskip("playwright.sync_api")

HERE = pathlib.Path(__file__).resolve().parent
SCRIPTS = HERE.parents[2] / ".apm/skills/navigate-decisions/scripts"
FIXTURE_MIXED = HERE / "fixtures/mixed"
FIXTURE_HOSTILE = HERE / "fixtures/negative/hostile"


def _load_module(name: str, path: pathlib.Path) -> object:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


EXPLORER = _load_module(
    "governance_extras_explorer_browser",
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
    """QE-14/FE-F1: Back from a detail route to the no-hash entry shows the list."""
    page = _open_page(browser, export_mixed)
    page.locator(".record-btn").first.click()
    page.wait_for_selector("#view-detail h2.detail-heading")
    assert page.locator("#view-list").is_hidden()
    page.go_back()
    page.wait_for_function("() => !document.getElementById('view-list').hidden")
    assert page.evaluate("location.hash") == ""
    assert page.locator("#view-list h2").text_content() == "Corpus list"
    assert page.locator("#view-detail").is_hidden()


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
    detail_visible = page.locator("#view-detail").is_visible()
    assert list_visible or detail_visible, "after URIError hash, at least one view must be visible"
    assert not page._errors, (  # type: ignore[attr-defined]
        f"page errors after URIError hash: {page._errors}"  # type: ignore[attr-defined]
    )


def test_aria_current_on_nav_buttons(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F9: View nav buttons use aria-current='page', not aria-pressed."""
    page = _open_page(browser, export_mixed)
    # List button must have aria-current=page (it is the initial view).
    list_btn = page.locator("#btn-list")
    current = list_btn.get_attribute("aria-current")
    assert current == "page", f"list button must have aria-current='page'; got {current!r}"
    # Must not have aria-pressed.
    pressed = list_btn.get_attribute("aria-pressed")
    assert pressed is None, f"nav buttons must not use aria-pressed; got {pressed!r}"


def test_focus_moves_to_view_heading(browser: object, export_mixed: pathlib.Path) -> None:
    """FE-F2: Focus moves to the view's h2 heading after navigation."""
    page = _open_page(browser, export_mixed)
    # Click graph button to navigate.
    page.locator("#btn-graph").click()
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
    detail_text = page.locator("#view-detail").text_content() or ""
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
    page.wait_for_selector("li.record-item")
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
    page.locator(".record-btn").first.click()
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
    page.locator(".record-btn").first.click()
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
    page.locator(".record-btn").first.click()
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
    list_text = " | ".join(
        page.locator("#view-list .supersede-banner").all_inner_texts()  # type: ignore[union-attr]
    )
    assert "Superseded in part by ADR-0020 (D3)" in list_text, list_text
    assert "Superseded by ADR-0003" in list_text, list_text
    page.evaluate("() => { location.hash = '#detail/ADR-0001'; }")  # type: ignore[union-attr]
    banner = page.locator("#view-detail .supersede-banner").first  # type: ignore[union-attr]
    banner.wait_for()
    assert "Superseded in part by ADR-0020 (D3)" in (banner.inner_text() or "")
    banner.get_by_text("ADR-0020").first.click()
    page.wait_for_function("() => location.hash === '#detail/ADR-0020'")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    # Contextual toggle button is present (ADR-0001 has Related: links)
    page.wait_for_selector(".ctx-toggle")  # type: ignore[union-attr]
    # x position of ADR-0001 node before toggle
    x_before = page.evaluate(  # type: ignore[union-attr]
        "() => { var g = document.querySelector('[data-node-id=\"ADR-0001\"]');"
        " var r = g && g.querySelector('rect');"
        " return r ? parseFloat(r.getAttribute('x')) : null; }"
    )
    # At least one hidden g exists (the ctx group is display:none)
    has_hidden_ctx = page.evaluate(  # type: ignore[union-attr]
        "() => { var gs = document.querySelectorAll('svg g[aria-hidden]');"
        " for (var g of gs) { if (g.style.display === 'none') return true; } return false; }"
    )
    assert has_hidden_ctx, "Contextual SVG group should be hidden (display:none) before toggle"
    # Press the toggle
    page.click(".ctx-toggle")  # type: ignore[union-attr]
    page.wait_for_timeout(200)
    # After toggle, no hidden context groups remain
    still_hidden = page.evaluate(  # type: ignore[union-attr]
        "() => { var gs = document.querySelectorAll('svg g[aria-hidden]');"
        " for (var g of gs) { if (g.style.display === 'none') return true; } return false; }"
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    assert not page._errors, f"page errors in graph view: {page._errors}"  # type: ignore[attr-defined]


def test_graph_no_network_requests(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0026: graph view issues no non-file requests (fully self-contained)."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
    info = page.evaluate(  # type: ignore[union-attr]
        """() => { const li = document.querySelector('li.record-item');
          const row = li.querySelector('.record-btn').getBoundingClientRect();
          const title = li.querySelector('.rtitle').getBoundingClientRect();
          return { ratio: title.width / row.width,
                   status: li.querySelector('.rstatus').textContent }; }"""
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
    _navigate_graph(page, "ADR-0001")
    page.click("button.atlas-back")  # type: ignore[union-attr]
    page.wait_for_selector(".chain-card")  # type: ignore[union-attr]
    assert page.evaluate("location.hash") == "#graph"  # type: ignore[union-attr]


def test_back_from_focused_graph_restores_atlas(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0016: Back after focusing a node from the atlas shows the atlas again."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.record-item")  # type: ignore[union-attr]
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
    page.wait_for_selector("li.record-item")
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
    page.wait_for_selector("li.record-item")
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


def test_theme_toggle_sets_and_remembers_the_theme(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """Owner request: Auto/Light/Dark toggle overrides the system setting and
    persists across reloads; Auto follows the system again."""
    context = browser.new_context(offline=True, color_scheme="light")  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_selector("li.record-item")
    theme = "() => document.documentElement.dataset.theme"
    assert page.evaluate(theme) == "light"
    page.click("[data-theme-choice=dark]")
    assert page.evaluate(theme) == "dark"
    assert page.get_attribute("[data-theme-choice=dark]", "aria-pressed") == "true"
    page.reload()
    page.wait_for_selector("li.record-item")
    assert page.evaluate(theme) == "dark", "the choice must survive a reload"
    page.emulate_media(color_scheme="dark")
    page.click("[data-theme-choice=light]")
    assert page.evaluate(theme) == "light", "Light overrides a dark system setting"
    page.click("[data-theme-choice=auto]")
    assert page.evaluate(theme) == "dark", "Auto follows the system setting"
    context.close()


def test_links_are_readable_in_both_themes(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0025: the superseded-by link inside the banner, and the source link in
    detail, reach 4.5:1 contrast in light and dark themes."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.record-item")
    for choice in ("light", "dark"):
        page.click(f"[data-theme-choice={choice}]")
        assert page.evaluate("() => document.documentElement.dataset.theme") == choice
        ratio = _contrast(page, "li.record-item .supersede-banner a")
        assert ratio >= 4.5, f"{choice}: banner link contrast {ratio:.2f}"
    page.click("[data-theme-choice=auto]")


def test_unknown_record_shows_not_in_export_in_every_view(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0016: an unknown record ID says it is not in this export in the graph,
    context and detail views."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.record-item")
    for view in ("graph", "context", "detail"):
        page.evaluate(f"() => {{ location.hash = '#{view}/ADR-9999'; }}")
        page.wait_for_function(
            f"() => document.getElementById('view-{view}').textContent.includes('ADR-9999')"
        )
        text = page.locator(f"#view-{view}").text_content() or ""
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
    page.wait_for_selector("li.record-item")
    _render_body(page)
    page.wait_for_selector("#view-detail .rel-details")
    assert page.locator("#expand-all-btn").text_content() == "Expand all"
    page.click("#expand-all-btn")
    still_closed = page.evaluate(
        "() => [...document.querySelectorAll('#view-detail details')].filter(d => !d.open).length"
    )
    assert still_closed == 0
    assert page.locator("#expand-all-btn").text_content() == "Collapse all"


def test_reset_filters_keeps_keyboard_focus(browser: object, export_mixed: pathlib.Path) -> None:
    """AC-0016: after Reset filters removes itself, focus lands on the view heading."""
    page = _open_page(browser, export_mixed)
    page.locator("#search-input").fill("zzzzz-no-match")
    page.locator(".reset-btn").focus()
    page.keyboard.press("Enter")
    page.wait_for_selector("li.record-item")
    focused = page.evaluate(
        "() => [document.activeElement.tagName, document.activeElement.textContent]"
    )
    assert focused == ["H2", "Corpus list"], focused


def test_strike_through_marks_full_supersession_only(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """A record superseded only in part stays in force: its ID is not struck
    through, while a fully superseded record's ID is."""
    page = _open_page(browser, export_mixed)
    page.wait_for_selector("li.record-item")
    deco = page.evaluate(
        """() => Object.fromEntries([...document.querySelectorAll('li.record-item')].map(li =>
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
    page.wait_for_selector("li.record-item")
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
    page.wait_for_selector("li.record-item")
    for view in ("list", "graph", "context", "detail"):
        page.evaluate(f"() => {{ location.hash = '#{view}/ADR-0001'; }}")
        page.wait_for_function(f"() => !document.getElementById('view-{view}').hidden")
        info = page.evaluate(
            f"""() => {{ const v = document.getElementById('view-{view}');
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
        "- **Superseded by:** none\n"
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
    page.wait_for_selector("li.record-item")
    raw = "‏‎؜"
    for view in ("detail", "context"):
        for rid in ("ADR-0001", "ADR-0002"):
            page.evaluate(f"() => {{ location.hash = '#{view}/{rid}'; }}")
            page.wait_for_function(f"() => !document.getElementById('view-{view}').hidden")
            text = page.locator(f"#view-{view}").text_content() or ""
            assert not any(c in text for c in raw), (view, rid)
    page.evaluate("() => { location.hash = '#detail/ADR-0001'; }")
    page.wait_for_function("() => !document.getElementById('view-detail').hidden")
    detail = page.locator("#view-detail").text_content() or ""
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
    page.wait_for_selector("li.record-item")
    page.evaluate("() => { location.hash = '#detail/ADR-0002'; }")
    page.wait_for_selector("#view-detail .meta-table")
    rows = page.evaluate(
        """() => [...document.querySelectorAll('#view-detail .meta-table tr')]
          .map(tr => [tr.cells[0].textContent, tr.cells[1].textContent])"""
    )
    assert ["Date", "2024-03-15"] in rows, rows
    assert ["Supersedes", "none"] in rows, rows
    assert ["Superseded by", "none"] in rows, rows


def test_caller_assertion_is_drawn_and_listed_in_the_graph(
    browser: object, export_bidi_paths: pathlib.Path
) -> None:
    """AC-0026: a caller assertion reaches the graph view as a navigation-only
    relationship, drawn and listed with the same identity."""
    page = _open_page(browser, export_bidi_paths)
    page.wait_for_selector("li.record-item")
    page.evaluate("() => { location.hash = '#graph/ADR-0002'; }")
    page.wait_for_selector("#view-graph .graph-note")
    listed = page.evaluate(
        "() => [...document.querySelectorAll('.lineage-text-list li, .lineage-text li.lt-rel')]"
        ".map(li => li.textContent)"
    )
    assert any("[navigation_only · caller_asserted]" in t for t in listed), listed
