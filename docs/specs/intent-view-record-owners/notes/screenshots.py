# ruff: noqa: E501
"""Usage: python -I screenshots.py <export.html> <out dir>

AC-0029. Takes the 24 screenshots of a real export of this repository: three states at true
viewport widths 320, 1280, 1680 and 2560 CSS px, each in the light and the dark theme, named
`<state>-<width>-<theme>.png`.  Prints the owner chosen for each state, then each file's SHA-256.
Needs Playwright and Chromium.

States:
- `next`: "What can I work on next?" with an owner chosen.
- `browse`: "Browse all intents" with an owner chosen, "Expand all" pressed so context rows are open.
- `roadmap`: "How far along is each capability?" with an owner chosen.

The owner chosen for a state is the option with the most non-context rows, leaving out the option with
the most rows overall (the dominant owner), so narrowing shows.  A viewport, not a window, sets the width.
Each context uses reduced motion so the detail zone is not caught mid-fade, and each capture starts at the top of the page.
"""

import hashlib
import pathlib
import sys
import urllib.parse

from playwright.sync_api import Page, sync_playwright

export, out = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
WIDTHS = {320: 900, 1280: 900, 1680: 1000, 2560: 1400}
READY = "() => performance.getEntriesByName('view-ready').length > 0"
QUESTIONS = {"next": "next", "browse": "browse", "roadmap": "roadmap"}
ROWS = "#list a.row-link:not(:has(.ctx-tag, .c-context-flag))"


def fragment(question: str, value: str) -> str:
    return f"#q={question}&owner={urllib.parse.quote(value, safe='')}"


def prepare(page: Page, question: str, value: str) -> None:
    page.goto(export.as_uri() + fragment(question, value))
    page.wait_for_function(READY)
    if question == "browse":
        page.get_by_role("button", name="Expand all").click()
        for summary in page.locator("#list details:not([open]) > summary").all():
            summary.click()


def choose(browser, question: str) -> str:
    """The non-dominant option with the most non-context rows."""
    page = browser.new_page(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
    page.goto(export.as_uri() + f"#q={question}")
    page.wait_for_function(READY)
    values = [v for v in page.eval_on_selector_all("#owner option", "os => os.map(o => o.value)") if v]
    counts = {}
    for value in values:
        prepare(page, question, value)
        counts[value] = page.locator(ROWS).count()
    page.close()
    ranked = sorted(counts, key=lambda v: (-counts[v], v))
    print(f"{question}: rows by owner, top three {[(v, counts[v]) for v in ranked[:3]]}")
    return ranked[1]


out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as pw:
    browser = pw.chromium.launch()
    chosen = {state: choose(browser, q) for state, q in QUESTIONS.items()}
    for state, value in chosen.items():
        print(f"{state}: owner {value}")
        for width, height in WIDTHS.items():
            for theme in ("light", "dark"):
                ctx = browser.new_context(viewport={"width": width, "height": height}, color_scheme=theme, reduced_motion="reduce")
                page = ctx.new_page()
                prepare(page, QUESTIONS[state], value)
                assert page.evaluate("() => window.innerWidth") == width
                page.evaluate("() => window.scrollTo(0, 0)")  # the header shows the Owner control and the owner line
                page.mouse.move(0, 0)  # no row keeps a hover band from the clicks above
                page.screenshot(path=str(out / f"{state}-{width}-{theme}.png"))
                ctx.close()
    browser.close()
for png in sorted(out.glob("*.png")):
    print(hashlib.sha256(png.read_bytes()).hexdigest(), png.name)
