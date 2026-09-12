"""Mutation suite for the rendered-guidebook sweep.

Every case builds a small two-step site, mutates exactly one surface, and
requires the sweep to report it. The point is the cross-product: a step names
its position on several surfaces that are generated from one another, so the
suite mutates each in turn rather than trusting that checking one implies the
rest.

The green baseline is asserted first and separately. Without it a mutation case
can pass because the fixture was already dirty, which is how a sweep stops
checking anything without any case going red.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_guidebook_walk", REPO_ROOT / "tools" / "check-guidebook-walk.py"
)
check_guidebook_walk = importlib.util.module_from_spec(_spec)
import sys

sys.modules["check_guidebook_walk"] = check_guidebook_walk
_spec.loader.exec_module(check_guidebook_walk)

BASE = "/site/docs"


def _page(slug: str, title: str, step: int, total: int, walk: list[tuple[int, str, str]],
          onward: str | None) -> str:
    """One rendered step, carrying every surface the sweep reads."""
    items = "\n".join(
        f'<li><a href="{BASE}/{s}/"'
        f'{" aria-current=\"page\"" if s == slug else ""}>'
        f"<span>{n}</span><span>{t}</span></a></li>"
        for n, s, t in walk
    )
    next_link = (
        f'<p><strong>Next:</strong> <a href="{BASE}/{onward}/">onward</a></p>'
        if onward
        else ""
    )
    return f"""<!doctype html><html><head>
<link rel="canonical" href="https://example.test{BASE}/{slug}/">
</head><body>
<p class="guidebook-position"><strong>Step {step} of {total}</strong></p>
<nav class="guidebook-walk" aria-label="fixture guidebook, step {step} of {total}">
<h2 class="walk-heading">Step {step} of {total}</h2>
<ol>{items}</ol>
</nav>
<p><strong>Step {step} of {total} —</strong> {title}</p>
{next_link}
</body></html>"""


@pytest.fixture()
def site(tmp_path: Path) -> Path:
    """A built site holding one two-step guidebook."""
    build = tmp_path / "docs"
    walk = [(1, "one", "First step"), (2, "two", "Second step")]
    for number, slug, title in walk:
        page = build / slug
        page.mkdir(parents=True)
        (page / "index.html").write_text(
            _page(slug, title, number, 2, walk, "two" if number == 1 else None),
            encoding="utf-8",
        )
    return build


def _sweep(build: Path) -> list[str]:
    base = check_guidebook_walk.site_base(build)
    pages = sorted(build.rglob("index.html"))
    return [f.render() for f in check_guidebook_walk.check_guidebook(pages, build, base)]


def _mutate(build: Path, slug: str, before: str, after: str) -> None:
    page = build / slug / "index.html"
    text = page.read_text(encoding="utf-8")
    assert before in text, f"fixture does not contain {before!r} to mutate"
    page.write_text(text.replace(before, after, 1), encoding="utf-8")


def test_the_site_base_is_read_from_the_page_not_assumed(site: Path) -> None:
    """The sweep's own first defect: it compared build-relative paths to
    base-prefixed hrefs and called every real link unbuilt."""
    assert check_guidebook_walk.site_base(site) == BASE


def test_the_unmutated_site_is_clean(site: Path) -> None:
    """The baseline every mutation below is measured against."""
    assert _sweep(site) == []


def test_the_body_and_the_rail_must_agree(site: Path) -> None:
    _mutate(site, "two", '<h2 class="walk-heading">Step 2 of 2</h2>',
            '<h2 class="walk-heading">Step 1 of 2</h2>')
    assert any("rail" in f and "says 1 of 2" in f for f in _sweep(site))


def test_the_body_and_the_mobile_bar_must_agree(site: Path) -> None:
    _mutate(site, "two", "<strong>Step 2 of 2</strong>", "<strong>Step 1 of 2</strong>")
    assert any("mobile bar" in f for f in _sweep(site))


def test_the_total_must_match_the_pages_that_exist(site: Path) -> None:
    """`of M` is authored per page, so it drifts the moment a step is added."""
    for number, slug in ((1, "one"), (2, "two")):
        # Only the body's own declaration, which is the surface that states the
        # total. Replacing every "of 2" on the page would trip the rail and
        # mobile-bar agreement checks first and prove nothing about this one.
        _mutate(site, slug, f"<strong>Step {number} of 2 —</strong>",
                f"<strong>Step {number} of 3 —</strong>")
    assert any("the guidebook has 2 steps" in f for f in _sweep(site))


def test_a_repeated_step_number_is_reported(site: Path) -> None:
    _mutate(site, "two", "<strong>Step 2 of 2 —</strong>", "<strong>Step 1 of 2 —</strong>")
    assert any("also claimed by" in f for f in _sweep(site))


def test_exactly_one_entry_may_be_current(site: Path) -> None:
    _mutate(site, "one", ' aria-current="page"', "")
    assert any("marks 0 entries current" in f for f in _sweep(site))


def test_the_current_entry_must_be_this_page(site: Path) -> None:
    page = site / "one" / "index.html"
    text = page.read_text(encoding="utf-8").replace(' aria-current="page"', "", 1)
    page.write_text(text.replace(f'{BASE}/two/"', f'{BASE}/two/" aria-current="page"', 1),
                    encoding="utf-8")
    assert any("not this page" in f for f in _sweep(site))


def test_a_rail_link_must_resolve(site: Path) -> None:
    _mutate(site, "one", f'<a href="{BASE}/two/"', f'<a href="{BASE}/gone/"')
    assert any("is not built" in f for f in _sweep(site))


def test_every_step_must_list_the_same_walk(site: Path) -> None:
    """The rails are generated per page, so one can drift alone."""
    _mutate(site, "two", "Second step", "Renamed step")
    assert any("different walk" in f for f in _sweep(site))


def test_the_onward_link_must_resolve(site: Path) -> None:
    _mutate(site, "one", f'<strong>Next:</strong> <a href="{BASE}/two/"',
            f'<strong>Next:</strong> <a href="{BASE}/nowhere/"')
    assert any("does not resolve" in f for f in _sweep(site))


def test_a_missing_rail_is_reported(site: Path) -> None:
    page = site / "two" / "index.html"
    page.write_text(
        re.sub(r'<nav class="guidebook-walk.*?</nav>', "", page.read_text(encoding="utf-8"),
               flags=re.S),
        encoding="utf-8",
    )
    assert any("rail: is absent" in f for f in _sweep(site))


def test_a_missing_mobile_bar_is_reported(site: Path) -> None:
    """The defect that shipped: the desktop rail was overridden and the mobile
    surface was a different component, so a narrow window showed no position."""
    page = site / "two" / "index.html"
    page.write_text(
        re.sub(r'<p class="guidebook-position.*?</p>', "", page.read_text(encoding="utf-8"),
               flags=re.S),
        encoding="utf-8",
    )
    assert any("mobile bar: is absent" in f for f in _sweep(site))
