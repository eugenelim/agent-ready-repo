"""Usage: python screenshots.py <repo root> <out dir>

Takes the 32 AC-0045 screenshots: four states across the readiness matrix (widths 320, 1280,
1680 and 2560 CSS px, each in the light and the dark theme), over real exports of the `mixed`
fixture made with the shipped command (`export --readiness -`, a status object on standard
input).  Prints each file's SHA-256.  Needs Playwright and Chromium.

States, each named `<state>-<width>-<theme>.png`:
- `checked-start`: checked, one ready item carries the start tag, one blocked item shows codes.
- `checked-ask`: checked, more than one item is active, so no row is tagged and a line says why.
- `check-failed`: the piped input was not JSON, so the page shows its failure notice.
- `broken-findings`: "What is broken?" with workspace findings from the checked blocked items.
"""

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

from playwright.sync_api import sync_playwright

root, out = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
script = root / "packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py"
fixture = root / "packs/core/tests/skills/navigate-intents/fixtures/mixed"

BRAVO, CHARLIE, GOLF = (
    f"docs/specs/{s}/spec.md" for s in ("bravo-spec", "charlie-spec", "golf-new")
)
ACTION = "Complete or explicitly revise the dependency."


def entry(path, dispatchable=True, codes=()):
    findings = [{"code": c, "dispatchable": False, "next_action": ACTION} for c in codes]
    return {"path": path, "dispatchable": dispatchable, "findings": findings}


def status(ready=(), active=(), blocked=()):
    return json.dumps({
        "schema_version": 1, "mode": "status", "workspace_present": True, "workspace_root": ".",
        "canonical": {"performed": True, "bounded": True, "findings": [],
                      "ready": list(ready), "active": list(active), "blocked": list(blocked)},
    }).encode("utf-8")


blocked_golf = entry(GOLF, False, ("unsatisfied_dependency", "missing_plan"))
INPUTS = {
    "checked-start": status(ready=[entry(BRAVO), entry(CHARLIE)], blocked=[blocked_golf]),
    "checked-ask": status(active=[entry(BRAVO), entry(CHARLIE)], blocked=[blocked_golf]),
    "check-failed": b"{not json",
}
INPUTS["broken-findings"] = INPUTS["checked-start"]
# state -> (input, fragment that opens its question)
STATES = {
    "checked-start": ("checked-start", "#q=next"),
    "checked-ask": ("checked-ask", "#q=next"),
    "check-failed": ("check-failed", "#q=next"),
    "broken-findings": ("broken-findings", "#q=broken"),
}
WIDTHS = {320: 900, 1280: 900, 1680: 1000, 2560: 1400}

READY = "() => performance.getEntriesByName('view-ready').length > 0"
out.mkdir(parents=True, exist_ok=True)
tmp = pathlib.Path(tempfile.mkdtemp())
pages = {}
for state, (key, _fragment) in STATES.items():
    proc = subprocess.run(
        [sys.executable, str(script), "export", "--root", str(fixture), "--destination", str(tmp),
         "--name", f"{state}.html", "--readiness", "-"],
        input=INPUTS[key], capture_output=True, check=True)
    result = json.loads(proc.stdout)
    assert result["status"] == "ok", result
    pages[state] = pathlib.Path(result["path"])

with sync_playwright() as pw:
    browser = pw.chromium.launch()
    for state, (_key, fragment) in STATES.items():
        for width, height in WIDTHS.items():
            for theme in ("light", "dark"):
                viewport = {"width": width, "height": height}
                ctx = browser.new_context(viewport=viewport, color_scheme=theme)
                page = ctx.new_page()
                page.goto(pages[state].as_uri() + fragment)
                page.wait_for_function(READY)
                page.screenshot(path=str(out / f"{state}-{width}-{theme}.png"))
                ctx.close()
    browser.close()
for png in sorted(out.glob("*.png")):
    print(hashlib.sha256(png.read_bytes()).hexdigest(), png.name)
