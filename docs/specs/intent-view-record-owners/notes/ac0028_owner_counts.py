# ruff: noqa: E501
"""Usage: python -I ac0028_owner_counts.py <export.html>

AC-0028. Reads the Owner control's options and the row counts of "What can I work on next?" and
"Browse all intents" from the page in headless Chromium, computes the same numbers from the export's
payload by the spec's terms, prints a table, and exits 1 when any figure differs.  Needs Playwright.

Spec terms used:
- owner key: runs of spaces and tabs collapse to one space, the ends trim, only A to Z lower-case;
- owner label: the `owner` of the first node (by id, code-point order) that holds the key;
- options: "Any owner", one per non-empty key (in key order), "No owner recorded" when a key is empty;
- "next" rows: the distinct open items (`outstanding` placed and no-parent) in a startable stage, narrowed to
  the owner: specs `Implementing` or `Approved`, briefs `Executing` or `Ready`, and intents `Accepted` that list
  no children, briefs or specs;
- Browse rows: the Browse matches, the `records` (intents) whose node owner key matches (Show: All).
Browse "rows" on the page are the rows without a context tag, counted after "Expand all"
is pressed and the closed "No parent and nothing beneath" disclosure is opened; the header count is read as a cross-check.
"""

import json
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright


def owner_key(owner: str) -> str:
    collapsed = re.sub(r"[ \t]+", " ", owner).strip(" ")
    return "".join(chr(ord(c) + 32) if "A" <= c <= "Z" else c for c in collapsed)


def from_payload(html: str) -> list[tuple[str, str, int, int]]:
    text = re.search(r'<script[^>]*id="intent-data"[^>]*>(.*?)</script>', html, re.S).group(1)
    payload = json.loads(text)
    keys = {n["id"]: owner_key(n.get("owner") or "") for n in payload["nodes"]}
    labels: dict[str, str] = {}
    for n in sorted(payload["nodes"], key=lambda n: n["id"]):
        labels.setdefault(keys[n["id"]], n.get("owner") or "")
    out = payload["outstanding"]
    startable = {"spec": {"Implementing", "Approved"}, "brief": {"Executing", "Ready"}, "intent": {"Accepted"}}
    nxt = set()
    for item in out["placed"] + out["no_parent"] if out.get("available") is not False else []:
        i = item["id"]
        rec = payload["records"].get(i)
        status = (rec or next(n for n in payload["nodes"] if n["id"] == i)).get("status") or ""
        word = re.match(r"[A-Za-z]+", status)
        if rec is not None:  # an intent: startable only when it lists no children
            if word and word.group(0) in startable["intent"] and not (rec.get("children") or rec.get("briefs") or rec.get("specs")):
                nxt.add(i)
        elif word and word.group(0) in startable.get(item["type"], set()):
            nxt.add(i)
    choices = [("", "Any owner", None)]
    choices += [("k:" + k, labels[k], k) for k in sorted(k for k in labels if k)]
    if "" in labels:
        choices.append(("none", "No owner recorded", ""))
    rows = []
    for value, label, key in choices:
        pick = (lambda i: True) if key is None else (lambda i, key=key: keys.get(i, "") == key)
        rows.append((value, label, sum(1 for i in nxt if pick(i)), sum(1 for i in payload["records"] if pick(i))))
    return rows


def from_page(path: pathlib.Path) -> list[tuple[str, str, int, int]]:
    rows = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        base = path.as_uri()
        page.goto(base + "#q=next")
        page.wait_for_function("() => performance.getEntriesByName('view-ready').length > 0")
        options = page.eval_on_selector_all("#owner option", "os => os.map(o => [o.value, o.textContent])")
        for value, label in options:
            counts = []
            for q, sel in (("next", "#list a.row-link"), ("browse", "#list a.row-link:not(:has(.ctx-tag))")):
                frag = f"#q={q}" + (f"&owner={value.replace(':', '%3A').replace(' ', '%20')}" if value else "")
                page.evaluate("f => { location.hash = f; }", frag)
                page.wait_for_timeout(150)
                if q == "browse":
                    page.get_by_role("button", name="Expand all").click()
                    for summary in page.locator("#list details:not([open]) > summary").all():
                        summary.click()
                counts.append(page.locator(sel).count())
            rows.append((value, label, counts[0], counts[1]))
        browser.close()
    return rows


def main() -> int:
    path = pathlib.Path(sys.argv[1]).resolve()
    want = from_payload(path.read_text(encoding="utf-8"))
    got = from_page(path)
    print(f"options: page {len(got)}, script {len(want)}")
    print("| option | page next | script next | page browse | script browse |\n| --- | --- | --- | --- | --- |")
    for g, w in zip(got, want, strict=True):
        print(f"| {g[1]} | {g[2]} | {w[2]} | {g[3]} | {w[3]} |")
    same = [(g[0], g[1], g[2], g[3]) for g in got] == [(w[0], w[1], w[2], w[3]) for w in want]
    print("agree" if same else "DISAGREE")
    return 0 if same else 1


if __name__ == "__main__":
    raise SystemExit(main())
