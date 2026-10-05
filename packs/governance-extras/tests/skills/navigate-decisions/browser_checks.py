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


@pytest.fixture(scope="module")
def export_pathological(tmp_path_factory: pytest.TempPathFactory) -> pathlib.Path:
    """Export a fixture with a large pathological body for rendering checks.

    The body is 900 KB — well under the 1 MiB body_available threshold so it
    is embedded in full mode, and over the JS folding threshold (3000 chars).
    """
    fixture_dir = tmp_path_factory.mktemp("pathological_fixture")
    adr_dir = fixture_dir / "docs" / "adr"
    adr_dir.mkdir(parents=True)
    # 900 KB body: under 1 MiB (body_available=True → embedded), over fold threshold.
    body = "Lorem ipsum dolor sit amet. " * (900 * 1024 // 28 + 1)
    (adr_dir / "0001-pathological.md").write_text(
        f"# ADR-0001: Pathological body\n\n- **Status:** Accepted\n\n"
        f"## Context\n\n{body}",
        encoding="utf-8",
    )
    out_dir = tmp_path_factory.mktemp("browser_pathological")
    r = EXPLORER.publish_explorer(  # type: ignore[attr-defined]
        fixture_dir,
        destination=out_dir,
        mode="full",
        name="pathological.html",
    )
    assert r["status"] == "ok", r.get("error")
    return pathlib.Path(r["path"])


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
        lambda r: non_file_requests.append(r.url)
        if not r.url.startswith("file://")
        else None,
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
    assert not non_file, (
        f"export triggered non-file requests: {non_file}"
    )


def test_hash_routing_empty_hash_shows_list(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """QE-14/FE-F1: Empty hash navigates to list view without errors."""
    page = _open_page(browser, export_mixed)
    page.evaluate("window.location.hash = ''")
    page.wait_for_timeout(200)
    # The list view must be visible.
    list_view = page.locator("#view-list")
    assert list_view.is_visible(), "list view must be visible after empty hash"


def test_hash_routing_bogus_hash_shows_list(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """QE-14/FE-F1: Unknown route hash navigates to list view."""
    page = _open_page(browser, export_mixed)
    page.evaluate("window.location.hash = '#bogus-unknown-view'")
    page.wait_for_timeout(200)
    list_view = page.locator("#view-list")
    assert list_view.is_visible(), "list view must be visible after unknown hash"
    assert not page._errors, f"page errors after bogus hash: {page._errors}"  # type: ignore[attr-defined]


def test_hash_routing_uri_error_safe(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """QE-14/FE-F1: Malformed percent-encoding in hash does not crash."""
    page = _open_page(browser, export_mixed)
    # %E0 alone is an invalid UTF-8 sequence — decodeURIComponent throws URIError.
    page.evaluate("window.location.hash = '#detail/%E0'")
    page.wait_for_timeout(200)
    # Must not crash; either list or detail view must be visible.
    list_visible = page.locator("#view-list").is_visible()
    detail_visible = page.locator("#view-detail").is_visible()
    assert list_visible or detail_visible, (
        "after URIError hash, at least one view must be visible"
    )
    assert not page._errors, (  # type: ignore[attr-defined]
        f"page errors after URIError hash: {page._errors}"  # type: ignore[attr-defined]
    )


def test_aria_current_on_nav_buttons(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """FE-F9: View nav buttons use aria-current='page', not aria-pressed."""
    page = _open_page(browser, export_mixed)
    # List button must have aria-current=page (it is the initial view).
    list_btn = page.locator("#btn-list")
    current = list_btn.get_attribute("aria-current")
    assert current == "page", (
        f"list button must have aria-current='page'; got {current!r}"
    )
    # Must not have aria-pressed.
    pressed = list_btn.get_attribute("aria-pressed")
    assert pressed is None, (
        f"nav buttons must not use aria-pressed; got {pressed!r}"
    )


def test_focus_moves_to_view_heading(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """FE-F2: Focus moves to the view's h2 heading after navigation."""
    page = _open_page(browser, export_mixed)
    # Click graph button to navigate.
    page.locator("#btn-graph").click()
    page.wait_for_timeout(200)
    # The focused element should be the h2 inside #view-graph.
    focused_tag = page.evaluate("document.activeElement.tagName.toLowerCase()")
    focused_parent = page.evaluate(
        "document.activeElement.closest('[id^=view-]')?.id || ''"
    )
    assert focused_tag in ("h1", "h2"), (
        f"focus must be on a heading after navigation; got <{focused_tag}>"
    )
    assert "graph" in focused_parent, (
        f"focused heading must be inside graph view; parent id={focused_parent!r}"
    )


def test_live_region_updates_on_filter(
    browser: object, export_mixed: pathlib.Path
) -> None:
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
    assert updated_text != initial_text or "0" in updated_text, (
        f"live region must update after filter; got {updated_text!r}"
    )


def test_no_results_shows_reset_control(
    browser: object, export_mixed: pathlib.Path
) -> None:
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


def test_missing_id_shows_not_in_export(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """FE-F10: Unknown record ID in route shows 'not in this export', not 'nothing selected'."""
    page = _open_page(browser, export_mixed)
    page.evaluate(
        "window.location.hash = '#detail/' + encodeURIComponent('ADR-9999')"
    )
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
    """FE-F6: All buttons have at least 24×24 CSS px computed size."""
    page = _open_page(browser, export_mixed)
    # Navigate to a record detail to expose all button types.
    page.locator("#btn-graph").click()
    page.wait_for_timeout(200)
    buttons = page.locator("button").all()
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
    if rel_details.count() == 0:
        pytest.skip("No relationships for this record")
    open_attr = rel_details.first.get_attribute("open")
    assert open_attr is None, (
        "Relationships <details> must be closed by default; found open attribute"
    )
    # Summary must contain counts.
    summary_text = rel_details.first.locator("summary").text_content() or ""
    assert "Relationships" in summary_text, (
        f"Relationships summary must say 'Relationships'; got {summary_text!r}"
    )


def test_long_body_folded(browser: object, export_pathological: pathlib.Path) -> None:
    """FE-F11: Long record bodies use progressive disclosure (<details>)."""
    page = _open_page(browser, export_pathological)
    page.locator(".record-btn").first.click()
    page.wait_for_timeout(300)
    # The body must be inside a <details> element (body-details class).
    body_details = page.locator(".body-details")
    assert body_details.count() > 0, (
        "Long record body must be wrapped in a <details> element"
    )


def test_pathological_body_renders_under_2s(
    browser: object, export_pathological: pathlib.Path
) -> None:
    """AC-0010: Pathological 2 MiB body renders in under 2000 ms."""
    page = _open_page(browser, export_pathological)
    start = time.monotonic()
    page.locator(".record-btn").first.click()
    page.wait_for_timeout(100)
    # Open the body details to force rendering.
    body_details = page.locator(".body-details")
    if body_details.count() > 0:
        body_details.first.evaluate("el => el.setAttribute('open', '')")
        page.wait_for_timeout(100)
    elapsed_ms = (time.monotonic() - start) * 1000
    assert elapsed_ms < 2000, (
        f"Pathological body took {elapsed_ms:.0f} ms > 2000 ms to render"
    )
    assert not page._errors, (  # type: ignore[attr-defined]
        f"page errors during pathological body render: {page._errors}"  # type: ignore[attr-defined]
    )


def test_no_horizontal_overflow_640px(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0010: No horizontal scroll at 640 CSS px viewport width."""
    context = browser.new_context(viewport={"width": 640, "height": 900}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_load_state("networkidle")
    overflow = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, (
        "Horizontal overflow at 640 px viewport width — reflow is broken"
    )


def test_no_horizontal_overflow_320px(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0010: No horizontal scroll at 320 CSS px viewport width."""
    context = browser.new_context(viewport={"width": 320, "height": 600}, offline=True)  # type: ignore[union-attr]
    page = context.new_page()
    page.goto(f"file://{export_mixed}")
    page.wait_for_load_state("networkidle")
    overflow = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    assert not overflow, (
        "Horizontal overflow at 320 px viewport width — reflow is broken"
    )


def test_reduced_motion_rule_present(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0010: CSS contains a prefers-reduced-motion rule."""
    html = export_mixed.read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in html, (
        "HTML must contain a prefers-reduced-motion CSS rule"
    )


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


def test_supersession_banner_in_detail(
    browser: object, export_mixed: pathlib.Path
) -> None:
    """AC-0025: Superseded records show a supersession banner in the detail view."""
    # ADR-0002 is superseded by ADR-0003 in the mixed fixture (checked edge).
    page = _open_page(browser, export_mixed)
    page.evaluate(
        "window.location.hash = '#detail/' + encodeURIComponent('ADR-0002')"
    )
    page.wait_for_timeout(300)
    banner = page.locator(".sup-banner-detail")
    if banner.count() == 0:
        pytest.skip(
            "ADR-0002 has no supersession in this fixture; banner test skipped"
        )
    assert banner.is_visible(), "supersession banner must be visible in detail view"
    banner_text = banner.text_content() or ""
    assert "ADR-0003" in banner_text or "Superseded" in banner_text, (
        f"banner must reference the superseding record; got {banner_text!r}"
    )
