#!/usr/bin/env python3
"""Z6 -- does vendored Mermaid render in a real browser with egress blocked?

Three runs, so the harness proves itself before it is trusted:

  positive  baseline site (no vendored bundle), egress ALLOWED
            -> must log the unpkg request AND render an SVG.
               Proves both detectors work.
  degraded  baseline site (no vendored bundle), egress BLOCKED
            -> must log an ABORTED unpkg attempt and NOT render.
               Establishes the fallback behaviour the design claims is benign.
  gate      vendored site, egress BLOCKED
            -> must log NO unpkg attempt and MUST render an SVG.

Asserted per run: SVG presence, request log, and the accessible name of the
rendered diagram. The bundle moves the SVG into a **closed** shadow root, so the
DOM is read through CDP `DOM.getDocument(pierce=True)`, which sees closed roots;
page-level JS cannot. The accessible name is read from the CDP accessibility
tree, not inferred from attributes.
"""

from __future__ import annotations

import contextlib
import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

CHAPTER = "003-docs-product-research-payments-landscape-survey/index.html"


def run(site: Path, *, block_egress: bool, label: str) -> dict:
    url = (site / CHAPTER).resolve().as_uri()
    requests: list[dict] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()

        page.on(
            "request",
            lambda r: requests.append({"url": r.url, "type": r.resource_type}),
        )
        page.on(
            "requestfailed",
            lambda r: requests.append({
                "url": r.url,
                "type": r.resource_type,
                "failed": r.failure,
            }),
        )

        if block_egress:

            def handler(route, request):  # noqa: ANN001, ANN202
                if request.url.startswith("file://"):
                    route.continue_()
                else:
                    route.abort("failed")

            page.route("**/*", handler)

        page.goto(url, wait_until="load")
        # Mermaid renders asynchronously after load; give it real time either way
        # so a blocked run is not mistaken for a slow one.
        page.wait_for_timeout(6000)

        cdp = page.context.new_cdp_session(page)
        doc = cdp.send("DOM.getDocument", {"depth": -1, "pierce": True})
        root_id = doc["root"]["nodeId"]
        pierced = cdp.send("DOM.getOuterHTML", {"nodeId": root_id})["outerHTML"]

        # `getOuterHTML` on the document root does not serialize shadow content,
        # so collect every shadow root the pierced tree exposes and serialize
        # each one. This is the only route to a closed shadow root.
        shadow_html: list[str] = []

        def walk(node: dict) -> None:
            for sr in node.get("shadowRoots", []) or []:
                with contextlib.suppress(Exception):
                    shadow_html.append(
                        cdp.send("DOM.getOuterHTML", {"nodeId": sr["nodeId"]})["outerHTML"]
                    )
                walk(sr)
            for child in node.get("children", []) or []:
                walk(child)
            if node.get("contentDocument"):
                walk(node["contentDocument"])

        walk(doc["root"])
        pierced = pierced + "\n<!--SHADOW-->\n" + "\n".join(shadow_html)

        # Accessible name of each rendered diagram container, from the AX tree.
        ax_names: list[str] = []
        divs = page.query_selector_all("div.mermaid")
        for d in divs:
            desc = d.evaluate("e => e.outerHTML")
            ax_names.append(desc[:200])

        ax = cdp.send("Accessibility.getFullAXTree")
        ax_img = [
            n
            for n in ax["nodes"]
            if n.get("role", {}).get("value") in {"img", "graphics-document", "image"}
        ]

        pre_count = len(page.query_selector_all("pre.mermaid"))
        pre_any = page.query_selector_all("pre")
        div_count = len(divs)
        # Visible text of the first <pre> tells us whether the reader sees source.
        first_pre_text = pre_any[0].inner_text()[:120] if pre_any else ""

        browser.close()

    shadow_part = pierced.split("<!--SHADOW-->", 1)[1] if "<!--SHADOW-->" in pierced else ""
    svgs = re.findall(r"<svg[^>]*>", pierced)
    shadow_svgs = re.findall(r"<svg[^>]*>", shadow_part)
    aria_svgs = [s for s in svgs if "aria-label" in s or "aria-roledescription" in s]
    unpkg = [r for r in requests if "unpkg.com" in r["url"]]
    remote = [r for r in requests if not r["url"].startswith("file://")]

    return {
        "label": label,
        "url": url,
        "pre_mermaid_remaining": pre_count,
        "div_mermaid": div_count,
        "svg_count_pierced": len(svgs),
        "diagram_svgs_in_shadow": len(shadow_svgs),
        "diagram_svg_tags": shadow_svgs[:4],
        "shadow_root_count": len(shadow_html),
        "shadow_title_desc": re.findall(r"<(?:title|desc)[^>]*>[^<]{0,80}", shadow_part)[:6],
        "svg_with_aria": aria_svgs[:4],
        "aria_label_in_pierced_dom": "Diagram 3.2" in pierced,
        "ax_image_nodes": [
            {
                "role": n.get("role", {}).get("value"),
                "name": n.get("name", {}).get("value"),
            }
            for n in ax_img
        ],
        "div_outer_html": ax_names,
        "first_pre_visible_text": first_pre_text,
        "unpkg_requests": unpkg,
        "remote_requests": remote,
    }


if __name__ == "__main__":
    site = Path(sys.argv[1])
    block = sys.argv[2] == "block"
    label = sys.argv[3]
    print(json.dumps(run(site, block_egress=block, label=label), indent=2))
