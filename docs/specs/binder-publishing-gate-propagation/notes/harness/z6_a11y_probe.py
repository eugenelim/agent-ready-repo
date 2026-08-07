import contextlib
from pathlib import Path

from playwright.sync_api import sync_playwright

site = Path(
    "z6-shim/stage/site/003-docs-product-research-payments-landscape-survey/index.html"
).resolve()
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    p = b.new_page()
    reqs = []
    p.on("request", lambda r: reqs.append(r.url))
    p.route(
        "**/*",
        lambda ro, rq: ro.continue_() if rq.url.startswith("file://") else ro.abort("failed"),
    )
    errs = []
    p.on("pageerror", lambda e: errs.append(str(e)[:200]))
    p.goto(site.as_uri(), wait_until="load")
    p.wait_for_timeout(6000)
    cdp = p.context.new_cdp_session(p)
    ax = cdp.send("Accessibility.getFullAXTree")["nodes"]
    print("=== AX nodes for graphics ===")
    for n in ax:
        r = n.get("role", {}).get("value")
        nm = n.get("name", {}).get("value", "")
        d = n.get("description", {}).get("value", "") if n.get("description") else ""
        if r in {"graphics-document", "group", "image", "figure"}:
            print(f"   role={r!r:20} name={nm!r} desc={d!r}")
    # pierce closed shadow root for the SVG's title/desc
    doc = cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})
    sh = []

    def walk(n):
        for s in n.get("shadowRoots", []) or []:
            with contextlib.suppress(Exception):
                sh.append(cdp.send("DOM.getOuterHTML", {"nodeId": s["nodeId"]})["outerHTML"])
            walk(s)
        for c in n.get("children", []) or []:
            walk(c)

    walk(doc["root"])
    import re

    blob = "\n".join(sh)
    print("=== SVG <title>/<desc> inside the closed shadow root ===")
    for m in re.findall(r"<(?:title|desc)[^>]*>[^<]{0,90}", blob):
        print("   ", m)
    print(
        "=== diagram rendered? div heights:",
        p.evaluate("()=>[...document.querySelectorAll('div.mermaid')].map(d=>d.offsetHeight)"),
    )
    print("=== remote requests:", [r for r in reqs if not r.startswith("file://")])
    print("=== page errors:", errs)
    b.close()
