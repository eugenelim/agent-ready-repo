# ruff: noqa: E501
"""Scale benchmark for the offline intent graph view.

Not collected by pytest: the file name does not match ``test_*.py``.  Run it
locally; it needs Playwright and Chromium:

    python packs/core/tests/skills/navigate-intents/view_bench.py --source <repo-root> [--counts 1 10 25 50]

It builds N renumbered copies of the source repository's intents, briefs, and spec
directories (each copied whole) in a scratch repository under the system
temporary directory.  Every copy suffixes its slugs, directory names, and file
stems with ``-cNN`` and rewrites each pointer header, so each copy is a
self-consistent graph.  It exports each corpus with the real command, opens the
file from ``file://`` in headless Chromium, and prints a Markdown table.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from typing import Any

from playwright.sync_api import Browser, sync_playwright

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPT = _PACK / ".apm/skills/navigate-intents/scripts/navigate_intents.py"

# Thresholds frozen by the spec.
MAX_BYTES = 104_857_600
MAX_STARTUP_MS = 3_000.0
MAX_SEARCH_MS = 300.0
MAX_HEAP_BYTES = 1_024 * 1024 * 1024

_POINTER_LINE = re.compile(
    r"^(- \*\*(?:Slug|Parent intent|Brief|Discovery|Related intents|Superseded by):\*\*)(.*)$"
)
_COMMENT = re.compile(r"<!--.*?-->")
_TOKEN = re.compile(
    r"(?P<path>[A-Za-z0-9._/-]*\.md)"
    r"|(?P<typed>(?<![\w/.:-])[a-z]+:[a-z0-9][a-z0-9-]*)"
    r"|(?P<bare>(?<![\w/.:-])[a-z0-9][a-z0-9-]*(?![\w/.:-]))"
)
_KEEP = {"none"}


def _suffix_path(path: str, tag: str) -> str:
    """Suffix the spec directory, or else the file stem, of a repository path."""
    parts = path.split("/")
    if "specs" in parts[:-1]:
        i = parts.index("specs")
        if i + 1 < len(parts) - 1:
            parts[i + 1] += tag
        return "/".join(parts)
    if "intents" in parts[:-1] or "briefs" in parts[:-1]:
        parts[-1] = parts[-1][: -len(".md")] + tag + ".md"
    return "/".join(parts)


def _rewrite_value(value: str, tag: str) -> str:
    """Suffix every slug, typed ref, and path in one pointer header value."""
    value = _COMMENT.sub("", value)

    def sub(m: re.Match[str]) -> str:
        if m.group("path"):
            return _suffix_path(m.group("path"), tag)
        text = m.group("typed") or m.group("bare")
        return text if text in _KEEP else text + tag

    return _TOKEN.sub(sub, value).rstrip()


def rewrite_text(text: str, tag: str) -> str:
    """Rewrite the pointer header lines of one record, leaving the body alone."""
    out = []
    for line in text.split("\n"):
        m = _POINTER_LINE.match(line)
        out.append(m.group(1) + _rewrite_value(m.group(2), tag) if m else line)
    return "\n".join(out)


def build_corpus(dest: pathlib.Path, copies: int, source: pathlib.Path) -> None:
    """Write *copies* renumbered copies of the records in repository *source* under *dest*."""
    intents = dest / "docs/product/intents"
    briefs = dest / "docs/product/briefs"
    specs = dest / "docs/specs"
    for d in (intents, briefs, specs):
        d.mkdir(parents=True)
    for n in range(1, copies + 1):
        tag = f"-c{n:02d}"
        for src_dir, out_dir in (
            (source / "docs/product/intents", intents),
            (source / "docs/product/briefs", briefs),
        ):
            for f in sorted(src_dir.glob("*.md")):
                text = f.read_text(encoding="utf-8")
                (out_dir / f"{f.stem}{tag}.md").write_text(rewrite_text(text, tag), encoding="utf-8")
        for d in sorted((source / "docs/specs").iterdir()):
            if not d.is_dir():
                continue
            target = specs / f"{d.name}{tag}"
            shutil.copytree(d, target)
            spec = target / "spec.md"
            if spec.is_file():
                spec.write_text(rewrite_text(spec.read_text(encoding="utf-8"), tag), encoding="utf-8")


def _git(root: pathlib.Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def init_repo(root: pathlib.Path) -> None:
    """Make the scratch tree a repository with a recognised remote and one empty commit.

    Every corpus file is then untracked, so each source link is a ``latest``
    link, the larger of the two link shapes.
    """
    _git(root, "init", "-q")
    _git(root, "remote", "add", "origin", "https://github.com/example/scale-bench")
    _git(root, "-c", "user.name=bench", "-c", "user.email=bench@example.invalid",
         "commit", "-q", "--allow-empty", "-m", "bench")


def export(root: pathlib.Path, out_dir: pathlib.Path) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT), "export", "--root", str(root),
         "--destination", str(out_dir), "--name", "bench.html"],
        capture_output=True, text=True, check=False,
    )
    return json.loads(proc.stdout)  # type: ignore[no-any-return]


def _startup(browser: Browser, url: str) -> float:
    ctx = browser.new_context()
    try:
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_function("() => performance.getEntriesByName('view-ready').length > 0")
        return float(page.evaluate("() => performance.getEntriesByName('view-ready')[0].startTime"))
    finally:
        ctx.close()


_TYPE_SCRIPT = """() => {
  window.__t0 = null;
  document.getElementById('filter-q').addEventListener('keydown', () => {
    if (window.__t0 === null) { window.__t0 = performance.now(); }
  }, true);
}"""


def _search_and_heap(browser: Browser, url: str) -> tuple[float, float, dict[str, Any]]:
    ctx = browser.new_context()
    try:
        page = ctx.new_page()
        page.goto(url)
        page.wait_for_function("() => performance.getEntriesByName('view-ready').length > 0")
        facts = page.evaluate(
            "() => { const d = JSON.parse(document.getElementById('intent-data').textContent);"
            " return {available: d.outstanding.available !== false,"
            " reason: d.outstanding.reason || null, limit: d.outstanding.limit || null, summary: d.summary,"
            " intents: Object.keys(d.records).length}; }"
        )
        page.evaluate(_TYPE_SCRIPT)
        times = []
        for _ in range(5):
            page.fill("#filter-q", "")
            page.evaluate("() => { window.__t0 = null; performance.clearMarks('list-updated'); }")
            page.keyboard.type("graph")
            page.wait_for_function("() => performance.getEntriesByName('list-updated').length > 0")
            times.append(float(page.evaluate(
                "() => { const m = performance.getEntriesByName('list-updated');"
                " return m[m.length - 1].startTime - window.__t0; }"
            )))
        facts["search_count"] = page.evaluate(
            "() => document.getElementById('view-count').textContent"
        )
        heap = float(page.evaluate("() => performance.memory.usedJSHeapSize"))
        return statistics.median(times), heap, facts
    finally:
        ctx.close()


def measure(copies: int, browser: Browser, work: pathlib.Path, source: pathlib.Path) -> dict[str, Any]:
    root = work / f"corpus-{copies}"
    build_corpus(root, copies, source)
    init_repo(root)
    out = work / f"out-{copies}"
    out.mkdir()
    result = export(root, out)
    row: dict[str, Any] = {"copies": copies, "status": result.get("status")}
    if result.get("status") != "ok":
        row["error"] = result.get("error")
        return row
    url = pathlib.Path(result["path"]).as_uri()
    row["bytes"] = result["bytes"]
    row["startup_ms"] = statistics.median(_startup(browser, url) for _ in range(3))
    search_ms, heap, facts = _search_and_heap(browser, url)
    row.update(search_ms=search_ms, heap_bytes=heap, outstanding_available=facts["available"],
               outstanding_reason=[facts["reason"], facts["limit"]],
               intents=facts["intents"], summary=facts["summary"],
               search_count=facts["search_count"])
    row["meets_all"] = (
        row["bytes"] <= MAX_BYTES and row["startup_ms"] <= MAX_STARTUP_MS
        and search_ms <= MAX_SEARCH_MS and heap <= MAX_HEAP_BYTES
    )
    shutil.rmtree(root, ignore_errors=True)
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--counts", type=int, nargs="+", default=[1, 10, 25, 50])
    ap.add_argument("--source", type=pathlib.Path, required=True,
                    help="repository whose intents, briefs, and specs are copied")
    args = ap.parse_args()
    work = pathlib.Path(tempfile.mkdtemp(prefix="intent-view-bench-"))
    rows = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(args=["--enable-precise-memory-info"])
            try:
                for n in args.counts:
                    row = measure(n, browser, work, args.source.resolve())
                    print(json.dumps(row), file=sys.stderr, flush=True)
                    rows.append(row)
            finally:
                browser.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("| copies | outstanding available | file bytes | startup ms | search ms | heap MiB | meets all |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        if r["status"] != "ok":
            print(f"| {r['copies']} | export refused: {r.get('error')} | | | | | no |")
            continue
        avail = "yes" if r["outstanding_available"] else "no ({}, limit {})".format(*r["outstanding_reason"])
        print(f"| {r['copies']} | {avail} | {r['bytes']:,} "
              f"| {r['startup_ms']:.0f} | {r['search_ms']:.0f} | {r['heap_bytes'] / 2**20:.0f} "
              f"| {'yes' if r['meets_all'] else 'no'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
