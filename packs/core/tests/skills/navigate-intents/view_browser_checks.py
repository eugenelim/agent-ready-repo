# ruff: noqa: E501, PIE810
"""Scripted headless-Chromium checks for the offline intent graph view.

Not collected by the default pytest run: the file name does not match
``test_*.py``.  Run it locally and name it explicitly:

    python -m pytest packs/core/tests/skills/navigate-intents/view_browser_checks.py -q -rs

The suite needs Playwright and Chromium.  It fails, rather than skips, when
either is missing: the imports below are plain, and the browser launches in a
fixture.  Every export is written under ``tmp_path``.
"""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.parse
from typing import Any

import pytest
from playwright.sync_api import Browser, Page, sync_playwright

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"
_FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"

_GROUPS = [
    "Depends on, written here",
    "Depends on, written elsewhere",
    "Parent",
    "Child intents",
    "Briefs",
    "Specs",
    "Delivery relations",
    "Delivery diagnostics",
    "Related, written here",
    "Related, written elsewhere",
    "Pointers",
]
_STATES = [
    "dangling",
    "retired_target",
    "kind_mismatch",
    "out_of_type",
    "multiple_values",
    "cycle",
    "unparseable",
    "self_reference",
    "outside_scope",
]
_FORMS = ["typed", "path", "bare_slug", "markdown_link", "unrecognized"]
_TRUST = ["delivery_contract", "pointer_checked", "pointer_unchecked"]
_QUESTIONS = ["next", "broken", "roadmap", "capabilities", "noparent", "browse"]
# The questions that list rows from the outstanding map: each row is one link with three cells.
_ROW_QUESTIONS = ["next", "capabilities", "noparent", "broken"]
# The questions whose rail link shows a count.
_COUNTED = ["next", "broken", "roadmap", "capabilities", "noparent"]
_RAIL_GROUPS = [
    ("Work", ["next", "broken"]),
    ("Progress", ["roadmap", "capabilities"]),
    ("Tidy", ["noparent"]),
    ("Browse", ["browse"]),
]
_DATA_BLOCK = re.compile(
    r'(<script type="application/json" id="intent-data">)(.*?)(</script>)', re.DOTALL
)


def _load(path: pathlib.Path, module_name: str) -> Any:
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_browser_nav")
view_mod = nav._load_view_mod()


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


def _incomplete(_root: pathlib.Path) -> dict[str, Any]:
    return {
        "complete": False,
        "relations": [],
        "diagnostics": [{"code": "delivery-resource-limit", "limit": 7}],
    }


def _hostile_diagnostic(_root: pathlib.Path) -> dict[str, Any]:
    """A complete delivery snapshot with one diagnostic for a hostile intent."""
    return {
        "complete": True,
        "relations": [],
        "diagnostics": [{"code": "delivery-relation-ambiguous", "subject": "intent:hostile-child"}],
    }


def _export(
    root: pathlib.Path, out: pathlib.Path, name: str, from_id: str | None = None, **seams: Any
) -> pathlib.Path:
    out.mkdir(parents=True, exist_ok=True)
    result, code = nav.run_export(root, str(out), name, from_id, **seams)
    assert code == 0, result
    return pathlib.Path(result["path"])


def payload_of(path: pathlib.Path) -> dict[str, Any]:
    found = _DATA_BLOCK.search(path.read_text(encoding="utf-8"))
    assert found is not None
    return json.loads(found.group(2))  # type: ignore[no-any-return]


def _rewrite(src: pathlib.Path, dst: pathlib.Path, edit: Any) -> pathlib.Path:
    """Write a copy of *src* whose data block text is replaced by ``edit(payload)``."""
    html = src.read_text(encoding="utf-8")
    found = _DATA_BLOCK.search(html)
    assert found is not None
    result = edit(json.loads(found.group(2)))
    block = result if isinstance(result, str) else view_mod.data_block_json(result)
    dst.write_text(html[: found.start(2)] + block + html[found.end(2) :], encoding="utf-8")
    return dst


def _related_corpus(tmp: pathlib.Path) -> pathlib.Path:
    """The mixed corpus plus a related edge leaving bravo-feat's subtree and one pointing in."""
    root = tmp / "related"
    shutil.copytree(_FIXTURES / "mixed", root)
    feat = root / "docs/product/intents/FEAT-0001-bravo-feat.md"
    feat.write_text(
        feat.read_text(encoding="utf-8").replace(
            "- **Parent intent:** capability:alpha-cap\n",
            "- **Parent intent:** capability:alpha-cap\n"
            "- **Related intents:** outcome:charlie-out\n",
        ),
        encoding="utf-8",
    )
    (root / "docs/product/intents/FEAT-0007-zulu-rel.md").write_text(
        "# Feature: Zulu related\n\n- **Slug:** `zulu-rel`\n- **Status:** Draft\n"
        "- **Level:** feature\n- **Owner:** placeholder-owner\n- **Parent intent:** none\n"
        "- **Related intents:** capability:alpha-cap\n\n## Outcome\n\nPlaceholder.\n",
        encoding="utf-8",
    )
    return root


def _india_parent_corpus(tmp: pathlib.Path) -> pathlib.Path:
    """The mixed corpus where the terminal juliet-done names india-none as its parent."""
    root = tmp / "india_parent"
    shutil.copytree(_FIXTURES / "mixed", root)
    juliet = root / "docs/product/intents/FEAT-0006-juliet-done.md"
    text = juliet.read_text(encoding="utf-8")
    edited = re.sub(r"- \*\*Parent intent:\*\* none.*\n", "- **Parent intent:** intent:india-none\n", text)
    assert edited != text
    juliet.write_text(edited, encoding="utf-8")
    return root


_LONG_TITLE = "Show an intent's dependencies in the offline view for reviewers"


def _long_title_corpus(tmp: pathlib.Path) -> pathlib.Path:
    """The dependency fixture with Golf and Echo, two diagnostic sources, given realistic long titles."""
    root = tmp / "dependency_long"
    shutil.copytree(_FIXTURES / "dependency", root)
    for name, old in (("FEAT-0007-golf.md", "# Feature: Golf"), ("FEAT-0005-echo.md", "# Feature: Echo")):
        path = root / "docs" / "product" / "intents" / name
        path.write_text(path.read_text(encoding="utf-8").replace(old, "# Feature: " + _LONG_TITLE, 1), encoding="utf-8")
    return root


def _git_corpus(tmp: pathlib.Path) -> pathlib.Path:
    """A Git repository with a GitHub origin and an unpushed commit: every link is ``latest``."""
    root = tmp / "gitrepo"
    shutil.copytree(_FIXTURES / "mixed", root)
    for args in (
        ["init", "-q"],
        ["config", "user.name", "tester"],
        ["config", "user.email", "t@example.invalid"],
        ["add", "-A"],
        ["commit", "-q", "-m", "fixture"],
        ["remote", "add", "origin", "https://github.com/example-org/example-repo.git"],
    ):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)  # noqa: S603, S607
    return root


@pytest.fixture(scope="module")
def exports(tmp_path_factory: pytest.TempPathFactory) -> dict[str, pathlib.Path]:
    tmp = tmp_path_factory.mktemp("exports")
    out = tmp / "out"
    neg = _FIXTURES / "negative"
    found: dict[str, pathlib.Path] = {}
    for name, root in (
        ("mixed", _FIXTURES / "mixed"),
        ("hostile", _FIXTURES / "hostile"),
        ("dependency", _FIXTURES / "dependency"),
        ("empty", _FIXTURES / "empty"),
        ("terminality", _FIXTURES / "terminality"),
        ("roadmap", _FIXTURES / "roadmap"),
        ("coordinated", _FIXTURES / "coordinated_delivery"),
        ("cycle", neg / "cycle"),
        ("dangling", neg / "dangling"),
        ("multiple", neg / "multiple_values"),
        ("self_reference", neg / "self_reference"),
        ("retired", neg / "retired_target"),
        ("kind_mismatch", neg / "kind_mismatch"),
        ("out_of_type", neg / "out_of_type"),
        ("unparseable", neg / "unparseable"),
    ):
        found[name] = _export(root, out, f"{name}.html")
    related = _related_corpus(tmp)
    found["related"] = _export(related, out, "related.html")
    found["from_related"] = _export(related, out, "from_related.html", "bravo-feat")
    found["from_mixed"] = _export(
        _FIXTURES / "mixed", out, "from_mixed.html", "capability:alpha-cap"
    )
    found["from_hostile"] = _export(
        _FIXTURES / "hostile", out, "from_hostile.html", "intent:hostile-root"
    )
    found["dependency_from"] = _export(
        _FIXTURES / "dependency", out, "dependency_from.html", "capability:root-a"
    )
    found["dependency_incomplete"] = _export(
        _FIXTURES / "dependency", out, "dependency_incomplete.html", _delivery_provider=_incomplete
    )
    found["incomplete"] = _export(
        _FIXTURES / "mixed", out, "incomplete.html", _delivery_provider=_incomplete
    )
    found["hostile_incomplete"] = _export(
        _FIXTURES / "hostile", out, "hostile_incomplete.html", _delivery_provider=_incomplete
    )
    found["roadmap_incomplete"] = _export(
        _FIXTURES / "roadmap", out, "roadmap_incomplete.html", _delivery_provider=_incomplete
    )
    found["from_roadmap_cap"] = _export(_FIXTURES / "roadmap", out, "from_roadmap_cap.html", "capability:anchor-cap")
    found["from_roadmap_strategy"] = _export(
        _FIXTURES / "roadmap", out, "from_roadmap_strategy.html", "intent:atlas-direction"
    )
    found["from_roadmap_leaf"] = _export(
        _FIXTURES / "roadmap", out, "from_roadmap_leaf.html", "intent:birch-feat"
    )
    found["hostile_diag"] = _export(
        _FIXTURES / "hostile", out, "hostile_diag.html", _delivery_provider=_hostile_diagnostic
    )
    found["india_parent"] = _export(_india_parent_corpus(tmp), out, "india_parent.html")
    found["dependency_long"] = _export(_long_title_corpus(tmp), out, "dependency_long.html")
    found["latest"] = _export(_git_corpus(tmp), out, "latest.html")
    inert_root = tmp / "inert"
    shutil.copytree(_FIXTURES / "mixed", inert_root)
    found["inert"] = _export(inert_root, out, "inert.html")
    found["bad_json"] = _rewrite(found["mixed"], out / "bad_json.html", lambda _p: "{not json")
    found["bad_schema"] = _rewrite(
        found["mixed"], out / "bad_schema.html", lambda p: {**p, "schema": "other.v9"}
    )

    def all_parented(p: dict[str, Any]) -> dict[str, Any]:
        for node_id, record in p["records"].items():
            record["parent_edge"] = {
                "from": node_id,
                "field": "Parent intent",
                "form": "typed",
                "trust_class": "pointer_unchecked",
                "value": node_id,
                "to": node_id + "-up",
            }
        return p

    found["all_parented"] = _rewrite(found["mixed"], out / "all_parented.html", all_parented)
    return found


# ---------------------------------------------------------------------------
# Browser plumbing
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def browser() -> Any:
    with sync_playwright() as pw:
        chromium = pw.chromium.launch()
        yield chromium
        chromium.close()


_INIT = """
window.__csp = [];
document.addEventListener('securitypolicyviolation', (e) => window.__csp.push(e.violatedDirective));
"""


class Opened:
    """A page over one export plus the network, console, and policy evidence it raised."""

    def __init__(
        self,
        browser: Browser,
        path: pathlib.Path,
        *,
        width: int = 1280,
        height: int = 900,
        scheme: str = "light",
        js: bool = True,
        theme: str | None = None,
        fragment: str = "",
        reduced_motion: str | None = None,
    ) -> None:
        self.url = path.as_uri()
        self.context = browser.new_context(
            viewport={"width": width, "height": height},
            color_scheme=scheme,  # type: ignore[arg-type]
            java_script_enabled=js,
            reduced_motion=reduced_motion,  # type: ignore[arg-type]
        )
        self.context.set_default_timeout(8000)
        self.page: Page = self.context.new_page()
        self.requests: list[str] = []
        self.console: list[str] = []
        self.errors: list[str] = []
        self.page.on("request", lambda r: self.requests.append(r.url))
        self.page.on("console", lambda m: self.console.append(m.text))
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.add_init_script(_INIT)
        self.page.goto(self.url + fragment)
        if theme:
            self.page.evaluate(
                f"document.documentElement.setAttribute('data-theme', {json.dumps(theme)})"
            )

    def go(self, fragment: str) -> None:
        self.page.evaluate(
            """f => new Promise((done) => {
              if (location.hash === '#' + f) { done(); return; }
              addEventListener('hashchange', () => done(), { once: true });
              location.hash = f;
            })""",
            fragment,
        )

    def close(self) -> None:
        self.context.close()


@pytest.fixture
def opener(browser: Browser) -> Any:
    opened: list[Opened] = []

    def make(path: pathlib.Path, **kw: Any) -> Opened:
        item = Opened(browser, path, **kw)
        opened.append(item)
        return item

    yield make
    for item in opened:
        item.close()


def _text(page: Page, selector: str) -> str:
    return page.locator(selector).first.inner_text()


def _ids(page: Page, selector: str = "#list a.row-link") -> list[str]:
    return page.eval_on_selector_all(selector, "els => els.map(e => e.dataset.node)")  # type: ignore[no-any-return]


def _expand_all(page: Page) -> None:
    page.evaluate(
        """() => { let b;
          while ((b = document.querySelector('button.toggle[aria-expanded="false"]'))) b.click(); }"""
    )


def _open_disclosures(page: Page) -> None:
    """Open every section disclosure, so the rows inside are rendered on screen."""
    page.evaluate("() => document.querySelectorAll('#list details.loose').forEach((d) => { d.open = true; })")


def _live(page: Page, contains: str = "") -> str:
    """The live region's text, once it holds *contains* (the page updates it after the event)."""
    page.wait_for_function(
        "t => document.getElementById('live').textContent.includes(t)", arg=contains
    )
    return page.text_content("#live") or ""


def _query(root: pathlib.Path, *args: str) -> dict[str, Any]:
    result, code = nav.run_query(root, ["query", *args])
    assert code == 0, result
    return result  # type: ignore[return-value]


def _search_ids(root: pathlib.Path, selectors: dict[str, Any]) -> list[str]:
    result = _query(root, "--operation", "search", "--selectors", json.dumps(selectors))
    return [i["id"] for i in result["intents"]]


def _unsafe_present(text: str) -> list[str]:
    return [c for c in text if c in nav._UNSAFE_CHARS]


def _frag(**route: str) -> str:
    """A URL fragment for a route: question, node, search and filters."""
    return urllib.parse.urlencode({k: v for k, v in route.items() if v})


def _visit_everything(item: Opened, payload: dict[str, Any]) -> None:
    for key in _QUESTIONS:
        item.go(_frag(q=key))
        item.page.wait_for_selector("#list-title")
        for node in payload["nodes"]:
            item.go(_frag(q=key, node=node["id"]))


_TEXT_NODES = """() => {
  const out = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    if (!walker.currentNode.parentElement.closest('script, noscript')) out.push(walker.currentNode.textContent);
  }
  return out;
}"""


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def _lum(rgb: tuple[float, float, float]) -> float:
    def chan(v: float) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    return 0.2126 * chan(rgb[0]) + 0.7152 * chan(rgb[1]) + 0.0722 * chan(rgb[2])


def _ratio(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _rgb(css: str) -> tuple[float, float, float]:
    nums = re.findall(r"[\d.]+", css)
    return float(nums[0]), float(nums[1]), float(nums[2])


def _canvas_rgb(scheme: str) -> str:
    """The page-canvas colour view-base.css gives for a theme, as the browser reports it."""
    css = (_SCRIPTS / "view_assets" / "view-base.css").read_text(encoding="utf-8")
    dark_at = css.index("@media (prefers-color-scheme: dark)")
    block = css[dark_at:] if scheme == "dark" else css[:dark_at]
    row = re.search(r"--c-canvas:\s*#(\w{6})\s*;", block)
    assert row, f"view-base.css has no {scheme} --c-canvas declaration"
    hex6 = row.group(1)
    return "rgb({}, {}, {})".format(*(int(hex6[i : i + 2], 16) for i in (0, 2, 4)))


# ---------------------------------------------------------------------------
# The payload model the checks compare the page against (the spec's Terms)
# ---------------------------------------------------------------------------

_NAME_LABELS = ("Spec: ", "Brief: ", "Intent: ", "Feature: ", "Capability: ", "Outcome: ", "Opportunity: ")
_STAGES = [
    ("spec", "Implementing"),
    ("spec", "Approved"),
    ("brief", "Executing"),
    ("brief", "Ready"),
    ("intent", "Accepted"),
]
_TYPE_HEADS = [("intent", "Intents"), ("brief", "Briefs"), ("spec", "Specs")]


def _slug(node: dict[str, Any]) -> str:
    """A node's slug; briefs and specs carry none, so it is the id after its first colon."""
    return node.get("slug") or node["id"].split(":", 1)[1]


class Model:
    """The spec's terms, computed from a payload without reading any page code."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.p = payload
        self.nodes = {n["id"]: n for n in payload["nodes"]}
        self.records = payload["records"]
        out = payload["outstanding"]
        self.available = out.get("available") is not False
        self.open: dict[str, Any] = {}
        if self.available:
            for item in out["placed"] + out["no_parent"]:
                self.open.setdefault(item["id"], item)

    def display(self, node_id: str) -> str:
        node = self.nodes[node_id]
        heading = (node.get("heading") or "").strip()
        for label in _NAME_LABELS:
            if heading.startswith(label):
                heading = heading[len(label) :].strip()
                break
        return heading or _slug(node)

    def by_name(self, ids: Any) -> list[str]:
        return sorted(ids, key=lambda i: (self.display(i).lower(), i))

    def word(self, node_id: str) -> str:
        status = self.records[node_id]["status"] if node_id in self.records else self.nodes[node_id]["status"]
        found = re.match(r"[A-Za-z]+", status or "")
        return found.group(0) if found else ""

    def lists_children(self, node_id: str) -> bool:
        rec = self.records.get(node_id, {})
        return bool(rec.get("children") or rec.get("briefs") or rec.get("specs"))

    def ancestor_lists(self, node_id: str) -> list[list[str]]:
        item = self.open.get(node_id)
        if item is not None:
            if item["type"] == "spec":
                found = [[a["id"] for a in pl["ancestors"]] for pl in item["placements"]]
            else:
                found = [[a["id"] for a in item["ancestors"]]]
            return [lst for lst in found if lst]
        starts: list[str] = []
        for edge in self.p["edges"]:
            if edge["from"] != node_id or edge.get("state") or "to" not in edge:
                continue
            if edge["field"] in ("Parent intent", "Brief", "Discovery"):
                starts.append(edge["to"])
        lists = []
        for start in starts:
            chain, seen, at = [], {node_id}, start
            while at is not None and at not in seen:
                seen.add(at)
                chain.append(at)
                up = [
                    e["to"]
                    for e in self.p["edges"]
                    if e["from"] == at and e["field"] == "Parent intent" and not e.get("state") and "to" in e
                ]
                at = up[0] if up else None
            lists.append(chain)
        return lists

    def beneath(self, node_id: str) -> list[str]:
        return [i for i in self.open if any(node_id in lst for lst in self.ancestor_lists(i))]

    def startable(self) -> list[str]:
        def stage(i: str) -> int:
            key = (self.open[i]["type"], self.word(i))
            if key not in _STAGES or (key[0] == "intent" and self.lists_children(i)):
                return -1
            return _STAGES.index(key)

        ids = [i for i in self.open if stage(i) >= 0]
        return sorted(ids, key=lambda i: (stage(i), self.display(i).lower(), i))

    def capabilities(self) -> list[tuple[str, int]]:
        found = [
            (i, len(self.beneath(i))) for i, r in self.records.items() if r["level"] == "capability"
        ]
        found = [(i, n) for i, n in found if n > 0]
        return sorted(found, key=lambda t: (-t[1], self.display(t[0]).lower(), t[0]))

    def no_parent(self) -> list[str]:
        return [i["id"] for i in self.p["outstanding"]["no_parent"]] if self.available else []

    def broken(self) -> list[tuple[str, str]]:
        """Broken entries as (holder id, context text), in holder name order."""
        entries = [(e["from"], f"{e['field']}: {e['state']}") for e in self.p["edges"] if e.get("state")]
        if self.available:
            for node_id, rec in self.records.items():
                entries += [
                    (node_id, f"Delivery diagnostic: {d['code']}")
                    for d in rec.get("delivery_diagnostics", [])
                ]
        entries += self.dependency_broken()
        return sorted(entries, key=lambda e: (self.display(e[0]).lower(), e[0]))

    def dependency_broken(self) -> list[tuple[str, str]]:
        """Dependency broken entries (holder id, context): faults by position, then the cycle.

        A fault is held by its source and a cycle by each member, only by an intent with a record
        (so in scope), whether or not delivery mapping is available.
        """
        deps = self.p["dependencies"]
        found: list[tuple[str, str]] = []
        for d in sorted((d for d in deps["diagnostics"] if "from" in d), key=lambda d: d["position"]):
            if d["state"] != "outside_scope" and d["from"] in self.records:
                found.append((d["from"], f"Depends on: {d['state']}"))
        for d in deps["diagnostics"]:
            if d["state"] == "cycle":
                found += [(m, "Depends on: cycle") for m in d["members"] if m in self.records]
        return found

    def mark(self, node_id: str) -> tuple[str, str]:
        word = self.word(node_id)
        if word in ("Implementing", "Executing"):
            return "●", word
        if word in ("Approved", "Accepted", "Ready"):
            return "◆", word
        if self.available and node_id not in self.open:
            return "✓", word
        return "◇", word


# ---------------------------------------------------------------------------
# The roadmap question and the Browse tree, from the payload alone
# ---------------------------------------------------------------------------

_BANDS = ("delivered", "in progress", "not started", "stopped")
_BAR_CELLS = 24
_NO_STRATEGY = "Not under a product strategy in this export"


def _band_of(model: Model, node_id: str) -> str:
    """The delivery band of an intent, brief or spec, while ``outstanding`` is available."""
    word = model.word(node_id)
    if node_id in model.open:
        return "in progress" if word in ("Implementing", "Executing") else "not started"
    return "delivered" if word in ("Fulfilled", "Shipped") else "stopped"


def _up(model: Model, node_id: str) -> str | None:
    """The intent a record's resolved parent edge names, or None when absent, refused or outside."""
    edge = (model.records.get(node_id) or {}).get("parent_edge")
    if not edge or edge.get("state") or edge.get("to") not in model.records:
        return None
    return str(edge["to"])


def _nearest(model: Model, node_id: str, level: str) -> str | None:
    """The first intent of *level* met walking resolved parent edges upward from *node_id*."""
    seen = {node_id}
    at = _up(model, node_id)
    while at is not None and at not in seen:
        if model.records[at]["level"] == level:
            return at
        seen.add(at)
        at = _up(model, at)
    return None


def _work_beneath(model: Model, node_id: str) -> set[str]:
    """Every intent, brief and spec reached by children, briefs, specs and ``Brief:`` edges."""
    specs_of: dict[str, list[str]] = {}
    for edge in model.p["edges"]:
        if edge["field"] == "Brief" and not edge.get("state") and "to" in edge:
            specs_of.setdefault(edge["to"], []).append(edge["from"])
    reached: set[str] = set()
    todo = [node_id]
    while todo:
        at = todo.pop()
        rec = model.records.get(at)
        found = [*rec["children"], *rec["briefs"], *rec["specs"]] if rec else specs_of.get(at, [])
        for nxt in found:
            if nxt not in reached:
                reached.add(nxt)
                todo.append(nxt)
    reached.discard(node_id)
    return reached


def _apportion(counts: tuple[int, int, int]) -> tuple[int, int, int]:
    """Largest-remainder apportionment of the bar's cells; ties go to the earlier band."""
    current = sum(counts)
    cells = [_BAR_CELLS * n // current for n in counts]
    order = sorted(range(3), key=lambda i: (-(_BAR_CELLS * counts[i] % current), i))
    for i in order[: _BAR_CELLS - sum(cells)]:
        cells[i] += 1
    return cells[0], cells[1], cells[2]


def _progress(model: Model, node_id: str) -> dict[str, Any]:
    """Band counts over the work beneath, current work, delivered share and bar cells."""
    beneath = _work_beneath(model, node_id)
    counts = {b: sum(1 for i in beneath if _band_of(model, i) == b) for b in _BANDS}
    current = counts["delivered"] + counts["in progress"] + counts["not started"]
    share = (200 * counts["delivered"] + current) // (2 * current) if current else None
    cells: tuple[int, ...] | None = None
    if current:
        cells = (*_apportion((counts["delivered"], counts["in progress"], counts["not started"])), 0)
    elif beneath:
        cells = (0, 0, 0, _BAR_CELLS)
    return {"counts": counts, "current": current, "share": share, "cells": cells, "nothing_beneath": not beneath}


def _tree_roots(model: Model) -> list[str]:
    """The Full hierarchy roots: parentless, refused or outside-parent intents, then parent loops."""
    scope = model.p["scope"].get("from")
    if scope:
        return [str(scope)]

    def reach(starts: list[str], into: set[str]) -> None:
        todo = list(starts)
        while todo:
            at = todo.pop()
            if at not in into:
                into.add(at)
                todo += model.records[at]["children"]

    roots = [i for i in model.records if _up(model, i) is None]
    reached: set[str] = set()
    reach(roots, reached)
    for member in model.by_name(i for i in model.records if i not in reached):
        path: list[str] = []
        at: str | None = member
        while at is not None and at not in path:
            path.append(at)
            at = _up(model, at)
        on_loop = at is not None and member in path[path.index(at) :]
        if on_loop and member not in reached:
            roots.append(member)
            reach([member], reached)
    assert reached == set(model.records), "an intent is under no tree root"
    return model.by_name(roots)


def _roadmap_expectations(payload: dict[str, Any]) -> dict[str, Any]:
    """The spec's roadmap and tree terms, read from a payload without any page code.

    ``bands`` maps every node to its band (None while ``outstanding`` is unavailable); ``sections``
    lists ``{"heading", "strategy", "capabilities"}`` in the order shown, each capability as
    ``{"id", "children"}`` with nested capabilities under their nearest capability ancestor;
    ``progress`` maps each capability and strategy to ``_progress``; ``roots`` are the tree roots.
    """
    model = Model(payload)
    caps = [i for i, r in model.records.items() if r["level"] == "capability"]
    strategies = [i for i, r in model.records.items() if r["level"] == "product-strategy"]
    heads: dict[str | None, list[str]] = {}
    nested: dict[str, list[str]] = {}
    for cap in caps:
        above = _nearest(model, cap, "capability")
        if above is None:
            heads.setdefault(_nearest(model, cap, "product-strategy"), []).append(cap)
        else:
            nested.setdefault(above, []).append(cap)

    def entry(cap: str) -> dict[str, Any]:
        return {"id": cap, "children": [entry(c) for c in model.by_name(nested.get(cap, []))]}

    sections = [
        {"heading": model.display(s), "strategy": s, "capabilities": [entry(c) for c in model.by_name(heads[s])]}
        for s in model.by_name(i for i in heads if i is not None)
    ]
    if None in heads:
        sections.append(
            {"heading": _NO_STRATEGY, "strategy": None, "capabilities": [entry(c) for c in model.by_name(heads[None])]}
        )
    available = model.available
    return {
        "available": available,
        "bands": {i: _band_of(model, i) if available else None for i in model.nodes},
        "sections": sections,
        "progress": {i: _progress(model, i) for i in [*caps, *strategies]} if available else {},
        "roots": _tree_roots(model),
    }


def _marks(page: Page, selector: str) -> list[tuple[str, str, str | None]]:
    """(glyph, word, aria-hidden of the glyph) for every state mark under *selector*."""
    return page.eval_on_selector_all(  # type: ignore[no-any-return]
        f"{selector} .mark",
        """els => els.map(m => [m.querySelector('.mark-g').textContent,
          m.querySelector('.mark-w').textContent, m.querySelector('.mark-g').getAttribute('aria-hidden')])""",
    )


def _choose(item: Opened, question: str, **route: str) -> None:
    item.go(_frag(q=question, **route))


def _rail_counts(page: Page) -> dict[str, str]:
    """The visible count on each rail link, by its ``data-q`` key (Browse shows none)."""
    return page.evaluate(  # type: ignore[no-any-return]
        """() => Object.fromEntries(Array.from(document.querySelectorAll('nav a[data-q]')).filter(
          (a) => a.querySelector('.q-count')).map((a) => [a.dataset.q, a.querySelector('.q-count').textContent]))"""
    )


def _capability_total(payload: dict[str, Any]) -> int:
    return sum(1 for r in payload["records"].values() if r.get("level") == "capability")


def _count_text(page: Page) -> str:
    return _text(page, "#list-count")


def _row_names(page: Page) -> list[str]:
    return page.eval_on_selector_all("#list a.row-link .c-name", "els => els.map(e => e.textContent)")  # type: ignore[no-any-return]


def _search_intents(root: pathlib.Path, selectors: dict[str, Any]) -> list[str]:
    return sorted(_search_ids(root, selectors))


def _detail_part(page: Page, title: str) -> Any:
    return page.locator("#detail-body section.part", has=page.locator("h3.part-head", has_text=title)).first


def _pick(item: Opened, node: str, question: str = "next") -> Page:
    item.go(_frag(q=question, node=node))
    item.page.wait_for_function("() => document.querySelector('#detail-body .state-line') !== null")
    return item.page


def _related_root(exports: dict[str, pathlib.Path]) -> pathlib.Path:
    return exports["related"].parent.parent / "related"


def _wait_focus_id(page: Page, element_id: str) -> None:
    page.wait_for_function("i => document.activeElement.id === i", arg=element_id)


def _wait_heading(page: Page, text: str) -> None:
    page.wait_for_function(
        "t => document.getElementById('detail-heading').textContent === t", arg=text
    )


_MIXED_ROOT = _FIXTURES / "mixed"


# ---------------------------------------------------------------------------
# The first screen: AC-0001 .. AC-0008, AC-0050
# ---------------------------------------------------------------------------


def test_ac_0001_six_destinations_with_counts(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    assert page.locator("nav").count() == 1
    links = page.locator("nav a")
    names = page.eval_on_selector_all("nav a .q-name", "els => els.map(e => e.textContent)")
    assert links.count() == 6
    assert names == [
        "What can I work on next?",
        "What is broken?",
        "How far along is each capability?",
        "What is still open under a capability?",
        "What has no parent?",
        "Browse all intents",
    ]
    assert page.eval_on_selector_all("nav a", "els => els.map(e => e.dataset.q)") == _QUESTIONS
    counts = _rail_counts(page)
    assert counts == {
        "next": "3",
        "broken": "0",
        "roadmap": str(_capability_total(payload_of(exports["mixed"]))),
        "capabilities": "2",
        "noparent": "6",
    }
    current = page.eval_on_selector_all("nav a", "els => els.map(e => [e.dataset.q, e.getAttribute('aria-current')])")
    assert current == [[k, "page" if k == "next" else None] for k in _QUESTIONS]
    assert page.locator("#list a.row-link").count() == 3
    assert _text(page, "#list-title") == "In a startable stage"
    assert _count_text(page) == "3 items" and _text(page, "#list-sort") == "By stage, then name"
    for key in [*_ROW_QUESTIONS, "roadmap"]:
        _choose(item, key)
        assert str(page.locator("#list a.row-link").count()) == counts[key], key


_RAIL_EXPORTS = ["roadmap", "hostile_incomplete", "empty"]


@pytest.mark.parametrize("width", [1280, 1680])
@pytest.mark.parametrize("name", _RAIL_EXPORTS)
def test_rail_order_groups_and_counts(opener: Any, exports: dict[str, pathlib.Path], name: str, width: int) -> None:
    item = opener(exports[name], width=width, height=900)
    page = item.page
    payload = payload_of(exports[name])
    assert page.locator("nav").count() == 1
    assert page.eval_on_selector_all("nav a", "els => els.map(e => e.dataset.q)") == _QUESTIONS
    assert page.locator("nav").get_by_role("list").count() == len(_RAIL_GROUPS)
    for label, keys in _RAIL_GROUPS:
        group = page.locator("nav").get_by_role("list", name=label, exact=True)
        assert group.count() == 1, label
        assert group.locator("a[data-q]").evaluate_all("els => els.map(e => e.dataset.q)") == keys
    counts = _rail_counts(page)
    capabilities = str(_capability_total(payload))
    if name == "empty":
        assert counts == dict.fromkeys(_COUNTED, "0")
    elif name == "hostile_incomplete":
        assert [counts[k] for k in ("next", "capabilities", "noparent")] == ["unknown"] * 3
        assert counts["roadmap"] == capabilities
    else:
        assert counts["roadmap"] == capabilities and int(capabilities) > 0
        assert all(v.isdigit() for v in counts.values()), counts
    # The count is visible text inside the link, after the question's name.
    for key in _COUNTED:
        assert _text(page, f'nav a[data-q="{key}"] .q-count') == counts[key]
    assert page.locator('nav a[data-q="browse"] .q-count').count() == 0
    assert page.locator('nav a[aria-current="page"]').evaluate_all("els => els.map(e => e.dataset.q)") == ["next"]
    _choose(item, "roadmap")
    assert _text(page, "#list-title") == "Capability progress"
    assert _text(page, "#list-sort") == "By strategy, then name"
    assert _count_text(page) == f"{capabilities} {'capability' if capabilities == '1' else 'capabilities'}"


@pytest.mark.parametrize("width", [1280, 1439, 1440, 1680])
def test_rail_group_labels_by_width(opener: Any, exports: dict[str, pathlib.Path], width: int) -> None:
    page = opener(exports["roadmap"], width=width, height=900).page
    boxes = page.eval_on_selector_all(
        "nav .rail-group", "els => els.map(e => [e.textContent, e.getBoundingClientRect().width, e.getBoundingClientRect().height])"
    )
    assert [b[0] for b in boxes] == [label for label, _ in _RAIL_GROUPS]
    for label, w, h in boxes:
        if width >= 1440:
            assert w > 20 and h > 8, (label, w, h)  # visible
        else:
            assert w <= 1 and h <= 1, (label, w, h)  # visually hidden
    # The lists keep their accessible names at every width.
    for label, keys in _RAIL_GROUPS:
        group = page.locator("nav").get_by_role("list", name=label, exact=True)
        assert group.count() == 1
        assert group.locator("a[data-q]").evaluate_all("els => els.map(e => e.dataset.q)") == keys


def test_list_header_shows_title_count_and_sort_for_every_question(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    for key in _QUESTIONS:
        _choose(item, key)
        title, count, sort = (_text(page, f"#list-{k}") for k in ("title", "count", "sort"))
        assert title and count and sort, key
        assert page.evaluate(
            "() => { const h = document.querySelector('.list-head').getBoundingClientRect().bottom;"
            " return h <= document.getElementById('list').getBoundingClientRect().top + 1; }"
        ), key


def test_ac_0002_startable_stage_list(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    expected = Model(payload_of(exports["mixed"])).startable()
    assert expected == ["spec:bravo-spec", "brief:bravo-delivery", "intent:india-none"]
    assert _ids(item.page) == expected


def test_ac_0003_title_lead_and_no_readiness_glyph(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    assert _text(page, "#list-title") == "In a startable stage"
    assert _text(page, "#list-lead") == "Readiness not checked in this snapshot."
    for key in _QUESTIONS:
        _choose(item, key)
        assert "▶" not in page.inner_text("body")
        assert "ready to start" not in page.inner_text("body").lower()
    for name in ("hostile", "incomplete"):
        assert "▶" not in opener(exports[name]).page.inner_text("body")


def test_ac_0004_capabilities_with_open_counts(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    _choose(item, "capabilities")
    model = Model(payload_of(exports["mixed"]))
    expected = model.capabilities()
    assert expected == [("capability:alpha-cap", 4), ("outcome:charlie-out", 2)]
    assert _ids(item.page) == [i for i, _ in expected]
    contexts = item.page.eval_on_selector_all("#list .c-context", "els => els.map(e => e.textContent)")
    assert len(contexts) == len(expected)
    for context, (_, n) in zip(contexts, expected, strict=True):
        assert context.endswith(f" \u00b7 {n} open"), context


def test_ac_0005_no_parent_groups_and_filters(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    model = Model(payload_of(exports["mixed"]))
    _choose(item, "noparent")
    ids = _ids(page)
    assert sorted(ids) == sorted(model.no_parent()) and len(ids) == 6
    heads = page.eval_on_selector_all("#list h3", "els => els.map(e => e.textContent)")
    assert heads == [h for t, h in _TYPE_HEADS if any(model.nodes[i]["type"] == t for i in ids)]
    expected_order = [i for t, _ in _TYPE_HEADS for i in model.by_name(j for j in ids if model.nodes[j]["type"] == t)]
    assert ids == expected_order
    assert page.locator("#filters select").count() == 2
    assert page.eval_on_selector_all("#filters label", "els => els.map(e => e.textContent)") == ["Type", "Level"]
    for select, key in (("#filter-type", "type"), ("#filter-level", "level")):
        values = [v for v in page.eval_on_selector_all(f"{select} option", "els => els.map(e => e.value)") if v]
        assert values
        for value in values:
            page.select_option(select, value)
            shown = _ids(page)
            if key == "type":
                want = [i for i in expected_order if model.nodes[i]["type"] == value]
            else:
                want = [i for i in expected_order if model.records.get(i, {}).get("level") == value]
            assert shown == want, (key, value)
            assert shown
        page.select_option(select, "")
    assert _ids(page) == expected_order


def test_ac_0006_broken_list(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["hostile_diag"])
    page = item.page
    _choose(item, "broken")
    model = Model(payload_of(exports["hostile_diag"]))
    expected = model.broken()
    states = [e for e in model.p["edges"] if e.get("state")]
    assert len(expected) == len(states) + 1 + len(model.dependency_broken()) and states
    assert _ids(page) == [h for h, _ in expected]
    contexts = page.eval_on_selector_all("#list .c-context", "els => els.map(e => e.textContent)")
    assert contexts == [c for _, c in expected]
    assert "Delivery diagnostic: delivery-relation-ambiguous" in contexts
    assert page.locator("#list .mark-w", has_text="Broken").count() == len(expected)
    assert _count_text(page) == f"{len(expected)} entries"


def test_ac_0007_sort_keys(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    keys = {
        "next": "By stage, then name",
        "capabilities": "By open count, then name",
        "noparent": "By type, then name",
        "broken": "By name",
        "roadmap": "By strategy, then name",
        "browse": "Under each parent, by name",
    }
    for key, sort in keys.items():
        _choose(item, key)
        assert _text(item.page, "#list-sort") == sort, key


def test_ac_0050_meta_line_totals(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in ("mixed", "from_mixed", "hostile"):
        page = opener(exports[name]).page
        summary = payload_of(exports[name])["summary"]
        meta = _text(page, "#meta")
        total = sum(summary["intents_by_level"].values())
        assert f"{total} intents, {summary['briefs']} briefs and {summary['specs']} specs" in meta
        assert "Read-only snapshot generated" in meta


def test_ac_0008_positive_empty_lines(opener: Any, exports: dict[str, pathlib.Path], tmp_path: pathlib.Path) -> None:
    def no_work_no_capability(p: dict[str, Any]) -> dict[str, Any]:
        records = {k: {**v, "level": "feature" if v.get("level") == "capability" else v.get("level")} for k, v in p["records"].items()}
        return {**p, "records": records, "outstanding": {"placed": [], "no_parent": []}}

    nothing = _rewrite(exports["mixed"], tmp_path / "nothing.html", no_work_no_capability)
    wanted = {
        "roadmap": "No capability is recorded.",
        "next": "Nothing is in a startable stage.",
        "capabilities": "No capability has open work beneath it.",
        "noparent": "Every open item has a parent.",
        "broken": "Nothing is broken.",
    }
    item = opener(nothing)
    page = item.page
    for key, line in wanted.items():
        _choose(item, key)
        assert _text(page, "#list") == line, key
        assert page.locator("#list a.row-link").count() == 0


# ---------------------------------------------------------------------------
# Rows and marks: AC-0009 .. AC-0012
# ---------------------------------------------------------------------------


def _row_ax_names(page: Page) -> list[str]:
    cdp = page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("Accessibility.enable")
    doc = cdp.send("DOM.getDocument", {"depth": 0})
    found = cdp.send("DOM.querySelectorAll", {"nodeId": doc["root"]["nodeId"], "selector": "#list a.row-link"})
    names = []
    for node_id in found["nodeIds"]:
        tree = cdp.send("Accessibility.getPartialAXTree", {"nodeId": node_id, "fetchRelatives": False})
        live = [n for n in tree["nodes"] if not n.get("ignored")]
        names.append(live[0]["name"]["value"] if live else None)  # None: not rendered (display: none)
    cdp.detach()
    return names


def test_ac_0009_row_is_one_link_with_three_cells(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    model = Model(payload_of(exports["mixed"]))
    for key in _ROW_QUESTIONS:  # a roadmap row holds progress in place of a context cell
        _choose(item, key)
        shape = page.eval_on_selector_all(
            "#list a.row-link",
            "els => els.map(e => [e.tagName, Array.from(e.children).map(c => c.className)])",
        )
        assert all(s == ["A", ["c-name", "c-state", "c-context"]] for s in shape), key
        assert page.locator("#list li.row").count() == len(shape)
        assert not page.locator("#list li.row a").count() - len(shape)
    _choose(item, "next")
    ids = _ids(page)
    for node_id, name in zip(ids, _row_ax_names(page), strict=True):
        assert name.startswith(model.display(node_id)), (node_id, name)
        assert model.word(node_id) in name
    for node_id, text in zip(ids, page.eval_on_selector_all("#list a.row-link", "e => e.map(x => x.textContent)"), strict=True):
        assert node_id not in text  # the display name is a heading, not the slug
    # A node whose heading is empty is named by its slug, and its row may show the id.
    nameless = _rewrite(
        exports["mixed"],
        exports["mixed"].parent / "nameless.html",
        lambda p: {**p, "nodes": [{**n, "heading": ""} if n["id"] == "spec:bravo-spec" else n for n in p["nodes"]]},
    )
    row = opener(nameless).page.locator('#list a.row-link[data-node="spec:bravo-spec"] .c-name')
    assert row.inner_text() == "bravo-spec"


def test_ac_0010_state_marks(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    model = Model(payload_of(exports["mixed"]))
    seen = set()
    for key in ("next", "capabilities", "noparent"):
        _choose(item, key)
        marks = _marks(page, "#list")
        ids = _ids(page)
        assert len(marks) == len(ids) == page.locator("#list .mark").count()
        for node_id, (glyph, word, hidden) in zip(ids, marks, strict=True):
            assert (glyph, word) == model.mark(node_id), node_id
            assert hidden == "true"
            seen.add(glyph)
    _choose(item, "broken")
    hostile = opener(exports["hostile_diag"])
    _choose(hostile, "broken")
    marks = _marks(hostile.page, "#list")
    assert marks and all(tuple(m) == ("✕", "Broken", "true") for m in marks)
    # The detail state line and every trail entry inside the export carry a mark too.
    page = _pick(item, "spec:golf-new")
    assert [tuple(m) for m in _marks(page, ".state-line")] == [("✓", "Shipped", "true")]
    assert _marks(page, ".trail-step") and all(g in "●◆◇✓" for g, _, _ in _marks(page, ".trail-step"))
    assert {"●", "◆", "◇"} <= seen or {"◆", "◇"} <= seen
    page = _pick(item, "intent:golf-new")
    assert [tuple(m) for m in _marks(page, ".state-line")] == [("◇", "Draft", "true")]
    incomplete = opener(exports["incomplete"])
    _choose(incomplete, "browse", node="capability:hotel-done")
    assert _marks(incomplete.page, ".state-line")[0][0] == "◇"


def test_ac_0011_context_cell(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    model = Model(payload_of(exports["mixed"]))
    for key in ("next", "noparent", "capabilities"):
        _choose(item, key)
        contexts = page.eval_on_selector_all("#list .c-context", "els => els.map(e => e.textContent)")
        for node_id, context in zip(_ids(page), contexts, strict=True):
            node = model.nodes[node_id]
            if key == "capabilities":
                assert context.endswith(f" \u00b7 {len(model.beneath(node_id))} open"), context
            label = {"intent": "Intent", "brief": "Brief", "spec": "Spec"}[node["type"]]
            assert context.startswith(label), context
            if node["type"] == "intent":
                assert model.records[node_id]["level"] in context
            lists = model.ancestor_lists(node_id)
            if lists:
                assert f"under {model.display(lists[0][0])}" in context, (node_id, context)
            else:
                assert "under" not in context
    scoped = opener(exports["from_related"])
    _choose(scoped, "browse")
    ancestors = Model(payload_of(exports["from_related"])).ancestor_lists("intent:bravo-feat")
    assert ancestors and ancestors[0][0] == "capability:alpha-cap"
    context = scoped.page.locator('#list a.row-link[data-node="intent:bravo-feat"] .c-context').inner_text()
    assert "capability:alpha-cap outside this export" in context


def test_ac_0012_browse_row_shows_refused_parent(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in ("dangling", "hostile"):
        item = opener(exports[name])
        payload = payload_of(exports[name])
        refused = {i: r["parent_edge"]["state"] for i, r in payload["records"].items() if (r["parent_edge"] or {}).get("state")}
        assert refused
        _choose(item, "browse")
        _expand_all(item.page)
        _open_disclosures(item.page)
        for node_id, state in refused.items():
            context = item.page.locator(f'#list a.row-link[data-node="{node_id}"] .c-context').inner_text()
            assert f"refused parent: {state}" in context, (node_id, context)
        others = [i for i in payload["records"] if i not in refused]
        for node_id in others:
            assert "refused parent" not in item.page.locator(f'#list a.row-link[data-node="{node_id}"] .c-context').inner_text()
        item.close()


# ---------------------------------------------------------------------------
# Detail: AC-0013 .. AC-0021
# ---------------------------------------------------------------------------


def test_ac_0013_detail_parts_in_order(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    page.locator('#list a.row-link[data-node="spec:bravo-spec"]').click()
    _wait_heading(page, "Bravo spec")
    assert page.locator("#detail-heading").evaluate("e => e.tagName") == "H2"
    order = page.eval_on_selector_all(
        "#detail-body > *",
        "els => els.map(e => e.classList.contains('state-line') ? 'state-line' : e.tagName === 'SECTION' ? e.querySelector('h3').textContent : e.tagName === 'DETAILS' ? 'details' : 'other')",
    )
    assert [o for o in order if o != "other"] == [
        "state-line", "Next step", "Open beneath", "What is broken", "Where it sits", "Open the file", "details",
    ]
    details = page.locator("#detail-body details.record")
    assert details.get_attribute("open") is None
    assert details.locator("summary").inner_text() == "Record details"
    details.locator("summary").click()
    assert details.get_attribute("open") is not None


def test_ac_0014_state_line_counts(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    model = Model(payload_of(exports["mixed"]))
    page = _pick(item, "capability:alpha-cap")
    line = _text(page, ".state-line")
    assert f"Intent · {len(model.beneath('capability:alpha-cap'))} open beneath · 0 broken" in line
    assert "Accepted" in line and len(model.beneath("capability:alpha-cap")) == 4
    hostile = opener(exports["hostile_diag"])
    hm = Model(payload_of(exports["hostile_diag"]))
    page = _pick(hostile, "intent:hostile-child", "broken")
    held = [c for h, c in hm.broken() if h == "intent:hostile-child"]
    assert held
    assert f"{len(held)} broken" in _text(page, ".state-line")
    unknown = opener(exports["hostile_incomplete"])
    um = Model(payload_of(exports["hostile_incomplete"]))
    for node_id in um.nodes:
        page = _pick(unknown, node_id)
        states = [e for e in um.p["edges"] if e["from"] == node_id and e.get("state")]
        states += [h for h, _ in um.dependency_broken() if h == node_id]
        line = _text(page, ".state-line")
        assert "open work unknown" in line and "open beneath" not in line
        assert f"{len(states)} broken" in line


_NEXT = {
    "none": "No next step shown: delivery mapping was incomplete, so this snapshot cannot tell what is open.",
    2: "Nothing to do. It is {word}.",
    3: "Continue building it with the work-loop skill. It is already being built.",
    4: "Build it with the work-loop skill. It is approved, and work-loop checks readiness before it starts.",
    5: "Finish the spec with the new-spec skill. It needs approval before it is built.",
    6: "Work on it with the author-delivery-brief skill in continue mode. Briefs are delivered through their slices.",
    7: "Decompose it with the intent skill. It is accepted but has nothing beneath it yet.",
    8: "Pick an item from Open beneath. Its work is already decomposed.",
    9: "Close it with the close-work skill if its outcome is met. Everything beneath it is finished.",
    10: "Keep shaping it with the intent skill. It is not accepted yet.",
}


def _next_step(page: Page) -> Any:
    section = _detail_part(page, "Next step")
    assert section.locator("p").count() == 1
    assert section.locator("code, button, a, input").count() == 0
    return section.locator("p").inner_text()


def test_ac_0015_next_step_sentences(opener: Any, exports: dict[str, pathlib.Path], tmp_path: pathlib.Path) -> None:
    item = opener(exports["incomplete"])
    assert _next_step(_pick(item, "intent:golf-new")) == _NEXT["none"]
    mixed = opener(exports["mixed"])
    word = Model(payload_of(exports["mixed"])).word("capability:hotel-done")
    assert _next_step(_pick(mixed, "capability:hotel-done", "browse")) == _NEXT[2].format(word=word)
    assert _next_step(_pick(mixed, "spec:golf-new", "browse")) == "Nothing to do. It is Shipped."
    assert _next_step(_pick(mixed, "spec:bravo-spec")) == _NEXT[3]
    approved = _rewrite(
        exports["mixed"],
        tmp_path / "approved.html",
        lambda p: {
            **p,
            "nodes": [{**n, "status": "Approved"} if n["id"] == "spec:bravo-spec" else n for n in p["nodes"]],
            "outstanding": {
                **p["outstanding"],
                "placed": [{**i, "status": "Approved"} if i["id"] == "spec:bravo-spec" else i for i in p["outstanding"]["placed"]],
            },
        },
    )
    assert _next_step(_pick(opener(approved), "spec:bravo-spec")) == _NEXT[4]
    assert _next_step(_pick(mixed, "spec:charlie-spec", "broken")) == _NEXT[5]
    assert _next_step(_pick(mixed, "brief:bravo-delivery")) == _NEXT[6]
    assert _next_step(_pick(mixed, "intent:india-none")) == _NEXT[7]
    assert _next_step(_pick(mixed, "capability:alpha-cap", "noparent")) == _NEXT[8]
    assert _next_step(_pick(mixed, "intent:golf-new", "noparent")) == _NEXT[10]
    parented = opener(exports["india_parent"])
    model = Model(payload_of(exports["india_parent"]))
    assert model.word("intent:india-none") == "Accepted" and model.lists_children("intent:india-none")
    assert not model.beneath("intent:india-none")
    assert _next_step(_pick(parented, "intent:india-none", "browse")) == _NEXT[9]


def test_ac_0016_open_beneath(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    model = Model(payload_of(exports["mixed"]))
    page = _pick(item, "capability:alpha-cap")
    section = _detail_part(page, "Open beneath")
    expected = model.beneath("capability:alpha-cap")
    heads = section.locator("h4").all_inner_texts()
    assert heads == [h for t, h in _TYPE_HEADS if any(model.nodes[i]["type"] == t for i in expected)]
    shown = section.locator("a[data-node]").evaluate_all("els => els.map(e => e.dataset.node)")
    want = [i for t, _ in _TYPE_HEADS for i in model.by_name(j for j in expected if model.nodes[j]["type"] == t)]
    assert shown == want and len(shown) == 4
    assert len(_marks(page, "#detail-body section.part:nth-of-type(2)")) == 4
    page = _pick(item, "intent:golf-new", "noparent")
    assert _detail_part(page, "Open beneath").locator("p").inner_text() == "Nothing open beneath."
    page = _pick(opener(exports["incomplete"]), "capability:alpha-cap")
    assert _detail_part(page, "Open beneath").locator("p").inner_text() == "Open work unknown: delivery mapping incomplete."


def test_ac_0017_what_is_broken_in_detail(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["hostile_diag"])
    page = _pick(item, "intent:hostile-child", "broken")
    section = _detail_part(page, "What is broken")
    assert "delivery-relation-ambiguous" in section.inner_text()
    key_text = page.text_content("#key-body") or ""
    model = Model(payload_of(exports["hostile_diag"]))
    states = [e for e in model.p["edges"] if e["from"] == "intent:hostile-child" and e.get("state")]
    for edge in states:
        meaning = section.locator(".meaning").all_inner_texts()
        assert any(m and m in key_text for m in meaning), edge
    for node_id in model.nodes:
        page = _pick(item, node_id, "broken")
        held = [e for e in model.p["edges"] if e["from"] == node_id and e.get("state")]
        held_diag = [c for h, c in model.broken() if h == node_id and c.startswith("Delivery diagnostic")]
        held_dep = [c for h, c in model.broken() if h == node_id and c.startswith("Depends on:")]
        text = _detail_part(page, "What is broken").inner_text()
        if held or held_diag or held_dep:
            assert "Nothing broken here." not in text
            assert _detail_part(page, "What is broken").locator("li.edge").count() == len(held) + len(held_diag) + len(held_dep)
        else:
            assert "Nothing broken here." in text
    unavailable = opener(exports["hostile_incomplete"])
    um = Model(payload_of(exports["hostile_incomplete"]))
    for node_id in um.nodes:
        page = _pick(unavailable, node_id)
        held = [e for e in um.p["edges"] if e["from"] == node_id and e.get("state")]
        held_dep = [h for h, _ in um.dependency_broken() if h == node_id]
        section = _detail_part(page, "What is broken")
        assert "Delivery diagnostics were unavailable." in section.inner_text()
        assert section.locator("li.edge").count() == len(held) + len(held_dep)


def test_ac_0018_where_it_sits(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    model = Model(payload_of(exports["mixed"]))
    page = _pick(item, "spec:golf-new", "browse")
    trail = _detail_part(page, "Where it sits").locator("ol.trail")
    assert trail.count() == len(model.ancestor_lists("spec:golf-new"))
    last = trail.first.locator("a[data-node]").last
    assert last.get_attribute("data-node") == "intent:golf-new"
    assert trail.first.locator(".mark").count() == trail.first.locator("a[data-node]").count()
    page = _pick(item, "spec:bravo-spec")
    trails = _detail_part(page, "Where it sits").locator("ol.trail")
    assert trails.count() == 2
    for i, chain in enumerate(model.ancestor_lists("spec:bravo-spec")):
        shown = trails.nth(i).locator("a[data-node]").evaluate_all("els => els.map(e => e.dataset.node)")
        assert shown == list(reversed(chain))
    page = _pick(item, "capability:alpha-cap", "noparent")
    assert _detail_part(page, "Where it sits").locator("p").inner_text() == "No parent."
    scoped = opener(exports["from_related"])
    page = _pick(scoped, "intent:bravo-feat")
    outside = _detail_part(page, "Where it sits").locator(".outside")
    assert outside.count() == 1
    assert outside.locator(".value").inner_text() == "capability:alpha-cap"
    assert "outside this export" in outside.inner_text()
    assert _detail_part(page, "Where it sits").locator("a[data-node]").count() == 0


def test_ac_0019_record_details(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["related"])
    page = item.page
    for node_id, groups in (
        ("intent:bravo-feat", ["Parent", "Child intents", "Briefs", "Specs", "Delivery relations", "Delivery diagnostics", "Related, written here", "Related, written elsewhere", "Depends on, written here", "Depends on, written elsewhere"]),
        ("brief:bravo-delivery", ["Pointers", "Delivery relations"]),
        ("spec:bravo-spec", ["Pointers", "Delivery relations"]),
    ):
        _pick(item, node_id)
        page.locator("#detail-body details.record summary").click()
        record = page.locator("#detail-body details.record")
        facts = record.locator(".fact-name").all_inner_texts()
        want = ["Id", "Path", "Type"] + (["Level", "Kind"] if node_id.startswith("intent") else []) + ["Status"]
        assert facts == want, node_id
        assert node_id in record.locator("dl.facts").inner_text()
        assert record.locator("h4.label-group").all_inner_texts() == groups, node_id
    for node_id in ("capability:alpha-cap", "brief:bravo-delivery"):
        unavailable = opener(exports["incomplete"])
        _pick(unavailable, node_id)
        unavailable.page.locator("#detail-body details.record summary").click()
        text = unavailable.page.locator("#detail-body details.record").inner_text()
        titles = unavailable.page.locator("#detail-body details.record h4.label-group").all_inner_texts()
        assert "Delivery mapping was unavailable" in text
        assert "Delivery relations" not in titles and "Delivery diagnostics" not in titles


def test_ac_0020_unknown_node_names_the_gap_and_keeps_the_list(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    _choose(item, "next", node="intent:not-in-snapshot")
    page = item.page
    assert "That item is not in this snapshot." in _text(page, "#detail-body")
    assert page.locator("#list a.row-link").count() == 3 and page.locator("#list a.row-link").first.is_visible()


def _wait_title(page: Page, title: str) -> None:
    page.wait_for_function("t => document.getElementById('list-title').textContent === t", arg=title)


def test_ac_0021_focus_after_an_action(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    page.locator('nav a[data-q="noparent"]').click()
    _wait_title(page, "Open with no parent")
    assert page.evaluate("document.activeElement.dataset.q") == "noparent"
    # The same by keyboard: the link keeps focus once the route has rendered.
    page.locator('nav a[data-q="broken"]').focus()
    page.keyboard.press("Enter")
    _wait_title(page, "Broken pointers and delivery problems")
    assert page.evaluate("document.activeElement.dataset.q") == "broken"
    assert page.evaluate("document.querySelectorAll('nav a[aria-current]').length") == 1
    page.locator('nav a[data-q="noparent"]').click()
    _wait_title(page, "Open with no parent")
    page.locator('#list a.row-link[data-node="capability:alpha-cap"]').click()
    assert page.evaluate("document.activeElement.dataset.node") == "capability:alpha-cap"
    assert _live(page, "Showing Alpha capability") == "Showing Alpha capability"
    page.locator('#detail-body a[data-node="intent:bravo-feat"]').first.click()
    _wait_focus_id(page, "detail-heading")
    narrow = opener(exports["mixed"], width=390)
    narrow.page.locator('#list a.row-link[data-node="spec:bravo-spec"]').click()
    _wait_focus_id(narrow.page, "detail-heading")
    narrow.page.locator('#detail-body a[data-node="intent:bravo-feat"]').first.click()
    _wait_focus_id(narrow.page, "detail-heading")
    # A narrow page that picks a question keeps focus on its link too.
    narrow.page.locator('nav a[data-q="broken"]').click()
    _wait_title(narrow.page, "Broken pointers and delivery problems")
    assert narrow.page.evaluate("document.activeElement.dataset.q") == "broken"


# ---------------------------------------------------------------------------
# Key, search and browse: AC-0022 .. AC-0025
# ---------------------------------------------------------------------------


def test_ac_0022_key_and_closed_label_set(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    assert page.locator("#key").get_attribute("open") is None
    assert page.locator("#key").evaluate("e => e.parentElement.classList.contains('list-head')")
    page.locator("#key summary").click()
    key = page.inner_text("#key")
    for glyph in "●◆◇✕△✓":
        assert glyph in key
    assert page.locator("dl.key-list").count() == 1 and page.locator("#key dl.key-list").count() == 1
    rendered = {"label-group": set(), "label-state": set(), "label-trust": set(), "label-form": set()}
    glyphs: set[str] = set()
    for name in ("hostile", "dependency", "dependency_from", "cycle", "multiple", "self_reference", "dangling", "retired", "kind_mismatch", "out_of_type", "unparseable", "coordinated", "related", "latest"):
        opened = opener(exports[name])
        payload = payload_of(exports[name])
        for key_name in ("browse", "broken"):
            _choose(opened, key_name)
            for node in payload["nodes"]:
                _choose(opened, key_name, node=node["id"])
                for cls in rendered:
                    rendered[cls] |= set(opened.page.eval_on_selector_all(f".{cls}", "e => e.map(x => x.textContent)"))
                glyphs |= {g for g, _, _ in _marks(opened.page, "body")}
        opened.close()
    assert rendered["label-group"] == set(_GROUPS)
    assert rendered["label-state"] == set(_STATES)
    assert rendered["label-trust"] == set(_TRUST)
    assert rendered["label-form"] == set(_FORMS)
    assert glyphs <= set("●◆◇✕△✓")
    latest = opener(exports["latest"])
    _pick(latest, "capability:alpha-cap")
    stale = latest.page.locator("#detail-body .source .mark")
    assert stale.count() == 1 and stale.inner_text().startswith("△")
    assert "may be newer than this export" in stale.inner_text()
    others = [g for g, _, _ in _marks(latest.page, "#list, .state-line, .trail")]
    assert "△" not in others
    outside_key = latest.page.locator("dl.key-list").evaluate_all("els => els.filter(e => !e.closest('#key')).length")
    assert outside_key == 0


def test_ac_0023_search(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    model = Model(payload_of(exports["mixed"]))
    assert page.locator("#search").is_visible()
    for key in _QUESTIONS:
        _choose(item, key)
        assert page.locator("#search").is_visible(), key
    _choose(item, "noparent")
    for text in ("bravo", "Alpha CAPABILITY", "a"):
        page.locator("#search").fill(text)
        ids = _ids(page)
        want = [i for i, n in model.nodes.items() if text.lower() in _slug(n).lower() or text.lower() in n["heading"].lower()]
        assert ids == model.by_name(want), text
        intents = [i for i in ids if model.nodes[i]["type"] == "intent"]
        assert sorted(intents) == _search_intents(_MIXED_ROOT, {"text": text}), text
    page.locator("#search").fill("bravo")
    page.locator("#search").press("Escape")
    assert page.locator("#search").input_value() == ""
    assert _text(page, "#list-title") == "Open with no parent" and len(_ids(page)) == 6
    page.locator("#search").fill("zzzz-nothing")
    assert "zzzz-nothing" in _text(page, "#list")
    assert page.get_by_role("button", name="Clear search").count() == 1
    assert page.locator("#list button").count() == 1
    page.get_by_role("button", name="Clear search").click()
    assert page.locator("#search").input_value() == "" and len(_ids(page)) == 6


def _tree_ids(page: Page) -> dict[str, Any]:
    """Every row inside each ``#list .tree`` after opening each disclosure: ids, per-section roots, children."""
    _open_disclosures(page)
    return page.evaluate(  # type: ignore[no-any-return]
        """() => {
          const all = Array.from(document.querySelectorAll('#list .tree a.row-link')).map(a => a.dataset.node);
          const sections = Array.from(document.querySelectorAll('#list .tree')).map(
            ul => Array.from(ul.children).map(li => li.querySelector('a.row-link').dataset.node));
          const roots = sections.flat();
          const kids = {};
          for (const li of document.querySelectorAll('#list li.tree-row')) {
            const id = li.querySelector(':scope > a.row-link').dataset.node;
            kids[id] = Array.from(li.querySelectorAll(':scope > ul > li')).map(c => c.querySelector('a.row-link').dataset.node);
          }
          return { all, roots, sections, kids };
        }"""
    )


def _resolved_parent(record: dict[str, Any]) -> str | None:
    edge = record.get("parent_edge")
    return edge["to"] if edge and "to" in edge and not edge.get("state") else None


def test_ac_0024_browse_all_intents(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    model = Model(payload_of(exports["mixed"]))
    _choose(item, "browse")
    _expand_all(page)
    tree = _tree_ids(page)
    assert sorted(tree["all"]) == sorted(model.records) and len(tree["all"]) == len(set(tree["all"]))
    roots = [i for i, r in model.records.items() if _resolved_parent(r) not in model.records]
    assert sorted(tree["roots"]) == sorted(roots)
    assert all(section == model.by_name(section) for section in tree["sections"])
    for node_id, kids in tree["kids"].items():
        assert kids == model.by_name(i for i, r in model.records.items() if _resolved_parent(r) == node_id)
    for select, key, values in (
        ("#filter-level", "level", ["capability", "feature", "unrecorded"]),
        ("#filter-kind", "kind", ["outcome", "opportunity"]),
        ("#filter-status", "exact_status", ["Draft", "Accepted", "Fulfilled — 2026-01-01"]),
    ):
        for value in values:
            page.select_option(select, value)
            assert sorted(_ids(page)) == _search_intents(_MIXED_ROOT, {key: value}), (key, value)
            assert _ids(page)
        page.select_option(select, "")
    page.select_option("#filter-level", "feature")
    page.select_option("#filter-status", "Draft")
    assert sorted(_ids(page)) == _search_intents(_MIXED_ROOT, {"level": "feature", "exact_status": "Draft"})
    page.select_option("#filter-kind", "outcome")
    message = _text(page, "#list")
    assert 'level "feature"' in message and 'kind "outcome"' in message and 'status "Draft"' in message
    assert page.locator("#list .empty button").count() == 1
    page.get_by_role("button", name="Clear filters").click()
    assert all(page.locator(f"#filter-{k}").input_value() == "" for k in ("level", "kind", "status"))
    assert len(_ids(page)) == len(model.records)


def test_ac_0025_scoped_export(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name, root_dir, scope in (("from_mixed", _MIXED_ROOT, "capability:alpha-cap"), ("from_related", None, "intent:bravo-feat")):
        item = opener(exports[name])
        page = item.page
        payload = payload_of(exports[name])
        in_scope = set(payload["records"])
        banner = page.inner_text("#scope-banner")
        assert page.locator("#scope-banner").is_visible()
        assert page.locator(f'#scope-banner [data-node="{scope}"], #scope-banner .outside').count() == 1
        assert "whole corpus" in banner and "totals above cover the whole corpus" in banner
        assert "whole corpus" in page.inner_text("#meta")
        whole = _query(root_dir or _related_root(exports), "--operation", "summary")["summary"]
        assert str(sum(whole["intents_by_level"].values())) in page.inner_text("#meta")
        model = Model(payload)
        for key in [k for k in _ROW_QUESTIONS if k != "broken"]:
            _choose(item, key)
            shown = set(_ids(page))
            assert shown <= set(model.nodes), key
        _choose(item, "next")
        assert _ids(page) == model.startable()
        _choose(item, "browse")
        _expand_all(page)
        tree = _tree_ids(page)
        assert tree["roots"] == [scope] and sorted(tree["all"]) == sorted(in_scope)
        root = root_dir or _related_root(exports)
        for fragment, selectors in (
            ({"search": "a"}, {"text": "a"}),
            ({"q": "browse", "level": "feature"}, {"level": "feature"}),
            ({"q": "browse", "level": "capability"}, {"level": "capability"}),
            ({"q": "browse", "status": "Draft"}, {"exact_status": "Draft"}),
            ({"q": "browse", "status": "Accepted"}, {"exact_status": "Accepted"}),
        ):
            item.go(_frag(**fragment))
            shown_intents = sorted(i for i in _ids(page) if model.nodes[i]["type"] == "intent")
            expected = sorted(i for i in _search_ids(root, selectors) if i in in_scope)
            assert shown_intents == expected, (name, fragment)


# ---------------------------------------------------------------------------
# Behaviour and states: AC-0030, AC-0042, AC-0043
# ---------------------------------------------------------------------------


def _history_length(page: Page) -> int:
    return page.evaluate("history.length")  # type: ignore[no-any-return]


def test_ac_0030_fragment_holds_state_and_history(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    item.go(_frag(q="browse", level="feature", status="Draft", node="intent:golf-new"))
    shown = _ids(page)
    page.reload()
    assert page.locator("#filter-level").input_value() == "feature"
    assert page.locator("#filter-status").input_value() == "Draft"
    assert _ids(page) == shown and _text(page, "#detail-heading") == "Golf new"
    item.go(_frag(q="noparent", search="bravo"))
    page.reload()
    assert page.locator("#search").input_value() == "bravo"
    assert _text(page, "#list-title") == 'Search results for "bravo"'
    fresh = opener(exports["mixed"])
    page = fresh.page
    start = _history_length(page)
    page.locator('nav a[data-q="capabilities"]').click()
    assert _history_length(page) == start + 1
    page.locator('#list a.row-link[data-node="capability:alpha-cap"]').click()
    assert _history_length(page) == start + 2
    _wait_heading(page, "Alpha capability")
    page.locator("#search").fill("alpha")
    page.locator("#search").fill("alpha c")
    assert _history_length(page) == start + 2
    page.locator("#search").fill("")
    page.locator('nav a[data-q="browse"]').click()
    before = _history_length(page)
    page.select_option("#filter-level", "feature")
    page.select_option("#filter-status", "Draft")
    assert _history_length(page) == before
    page.go_back()
    page.wait_for_function("() => document.querySelector('nav a[aria-current]').dataset.q === 'capabilities'")
    _wait_heading(page, "Alpha capability")
    page.go_back()
    page.wait_for_function("() => document.querySelector('nav a[aria-current]').dataset.q === 'capabilities'")
    assert _text(page, "#detail-heading") == "Details"
    page.go_back()
    page.wait_for_function("() => document.querySelector('nav a[aria-current]').dataset.q === 'next'")


def test_ac_0042_unavailable_open_work(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["hostile_incomplete"])
    page = item.page
    payload = payload_of(exports["hostile_incomplete"])
    reason = payload["outstanding"]["reason"]
    counts = _rail_counts(page)
    assert [counts[k] for k in ("next", "capabilities", "noparent")] == ["unknown"] * 3
    assert counts["broken"] == str(len(Model(payload).broken()))
    assert counts["roadmap"] == str(_capability_total(payload))
    for key in ("next", "capabilities", "noparent"):
        _choose(item, key)
        text = _text(page, "#list")
        assert "Can't list open work: delivery mapping incomplete." in text and reason in text, key
        assert page.locator("#list a.row-link").count() == 0
    _choose(item, "broken")
    states = [e for e in payload["edges"] if e.get("state")]
    assert states and len(_ids(page)) == len(states) + len(Model(payload).dependency_broken())
    assert "Delivery diagnostics were unavailable" in _text(page, "#list")
    _choose(item, "browse")
    _expand_all(page)
    assert sorted(_ids(page)) == sorted(payload["records"])


def test_ac_0043_empty_corpus(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["empty"])
    page = item.page
    assert "No intents, briefs or specs found under this root." in _text(page, "#list")
    assert _rail_counts(page) == dict.fromkeys(_COUNTED, "0")
    for key in _QUESTIONS:
        _choose(item, key)
        assert "No intents, briefs or specs found under this root." in _text(page, "#list")


# ---------------------------------------------------------------------------
# Carried checks: source links, escapes, no network, outside targets, damage, no script
# ---------------------------------------------------------------------------


def test_ac_0028_source_links_are_labelled_or_inert(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    latest = opener(exports["latest"])
    for key in _QUESTIONS:
        latest.go(_frag(q=key, node="capability:alpha-cap"))
        hrefs = latest.page.eval_on_selector_all("[href]", "els => els.map(e => e.getAttribute('href'))")
        assert all(h.startswith("#") or h.startswith("https://github.com/") for h in hrefs), hrefs
    latest.go(_frag(q="browse", node="capability:alpha-cap"))
    link = latest.page.locator("#detail-body a.source-link")
    assert link.count() == 1 and "/blob/HEAD/" in link.get_attribute("href")
    assert link.get_attribute("rel") == "noopener noreferrer"
    assert "may be newer than this export" in _text(latest.page, "#detail-body .source")
    inert = opener(exports["inert"])
    inert.go(_frag(q="browse", node="capability:alpha-cap"))
    assert inert.page.locator("#detail-body a.source-link").count() == 0
    path = payload_of(exports["inert"])["source_links"]["capability:alpha-cap"]["path"]
    assert path in _text(inert.page, "#detail-body .source")
    assert not inert.page.eval_on_selector_all("[href]", "els => els.filter(e => !e.getAttribute('href').startsWith('#')).length")


def test_ac_0034_unsafe_code_points_show_as_escapes(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["hostile_diag"])
    payload = payload_of(exports["hostile_diag"])
    seen = ""
    for key in _QUESTIONS:
        item.go(_frag(q=key))
        _expand_all(item.page)
        seen += "".join(item.page.evaluate(_TEXT_NODES))
        for node in payload["nodes"]:
            item.go(_frag(q=key, node=node["id"]))
            item.page.locator("#detail-body details.record summary").click()
            seen += "".join(item.page.evaluate(_TEXT_NODES))
    item.page.locator("#search").fill("hostile")
    seen += "".join(item.page.evaluate(_TEXT_NODES))
    assert _unsafe_present(seen) == []
    raw = json.dumps(payload["nodes"] + list(payload["records"].values()), ensure_ascii=False)
    expected = {f"[U+{ord(c):04X}]" for c in _unsafe_present(raw)}
    assert expected and all(code in seen for code in expected)


def test_ac_0036_no_network_and_no_policy_violation(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in ("hostile_diag", "latest"):
        item = opener(exports[name])
        _visit_everything(item, payload_of(exports[name]))
        for key in _QUESTIONS:
            _choose(item, key)
            for href in item.page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
                assert href.startswith("#") or href.startswith("https://github.com/")
        assert set(item.requests) == {item.url}, item.requests
        assert item.page.evaluate("window.__csp") == []
        assert not [m for m in item.console if "Content Security Policy" in m or "Refused" in m]
        assert item.errors == []


def test_ac_0045_out_of_scope_targets_are_plain_text(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["from_related"])
    payload = payload_of(exports["from_related"])
    in_scope = {n["id"] for n in payload["nodes"]}
    _pick(item, "intent:bravo-feat", "browse")
    item.page.locator("#detail-body details.record summary").click()
    detail = item.page.locator("#detail-body")
    shown = {o.locator(".value").inner_text() for o in detail.locator(".outside").all()}
    assert {"capability:alpha-cap", "outcome:charlie-out"} <= shown
    for target in shown:
        assert target not in in_scope
        assert "outside this export" in detail.locator(".outside", has_text=target).first.inner_text()
        assert detail.locator("a", has_text=target).count() == 0
    links = item.page.eval_on_selector_all("a[data-node]", "e => e.map(x => x.dataset.node)")
    assert set(links) <= in_scope
    _pick(item, "spec:bravo-spec", "browse")
    item.page.locator("#detail-body details.record summary").click()
    outside = item.page.locator("#detail-body .outside").all_inner_texts()
    assert any("brief:bravo-delivery" in o for o in outside), outside


def test_ac_0054_damaged_data_shows_one_alert_and_no_view(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in ("bad_json", "bad_schema"):
        item = opener(exports[name])
        page = item.page
        assert page.locator("[role=alert]").count() == 1
        text = page.locator("[role=alert]").inner_text().lower()
        assert "damaged" in text and "export" in text
        for selector in ("nav a", "#list", "#list *", "button", "input", "select", "details"):
            assert page.locator(selector).count() == 0, selector
        assert item.errors == []


def test_ac_0055_scripting_disabled_shows_notice(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"], js=False)
    assert "needs javascript" in item.page.inner_text("body").lower()


# ---------------------------------------------------------------------------
# Regressions kept from earlier review rounds
# ---------------------------------------------------------------------------


def _opportunity_corpus(tmp: pathlib.Path) -> pathlib.Path:
    """The coordinated-delivery corpus with beta-feat as an opportunity: its node id is
    ``opportunity:beta-feat`` while its delivery relation still writes ``intent:beta-feat``."""
    root = tmp / "opportunity"
    shutil.copytree(_FIXTURES / "coordinated_delivery", root)
    feat = root / "docs/product/intents/FEAT-0002-beta-feat.md"
    feat.write_text(
        feat.read_text(encoding="utf-8").replace(
            "- **Level:** feature\n", "- **Level:** feature\n- **Kind:** opportunity\n"
        ),
        encoding="utf-8",
    )
    return root


def test_delivery_relation_on_a_non_intent_node_renders_as_a_link(
    opener: Any, tmp_path: pathlib.Path
) -> None:
    path = _export(_opportunity_corpus(tmp_path), tmp_path / "out", "opportunity.html")
    payload = payload_of(path)
    relation = payload["records"]["opportunity:beta-feat"]["delivery_relations"][0]
    assert relation["intent"] == "intent:beta-feat"
    assert "intent:beta-feat" not in {n["id"] for n in payload["nodes"]}
    item = opener(path)
    page = item.page
    for node in ("opportunity:beta-feat", "brief:beta-brief"):
        item.go(_frag(q="browse", node=node))
        page.locator("#detail-body details.record summary").click()
        relations = page.locator("#detail-body section.group", has=page.locator("h4", has_text="Delivery relations"))
        assert relations.count() == 1
        assert relations.locator('a[data-node="opportunity:beta-feat"]').count() >= 1
        assert "outside this export" not in relations.inner_text()
    page.locator('#detail-body details.record a[data-node="opportunity:beta-feat"]').first.click()
    page.wait_for_function("() => document.getElementById('detail-heading').textContent === 'Beta feature'")


def test_startup_render_failure_shows_the_alert_and_logs_the_error(
    opener: Any, exports: dict[str, pathlib.Path], tmp_path: pathlib.Path
) -> None:
    broken = _rewrite(
        exports["mixed"], tmp_path / "broken.html", lambda p: {**p, "records": {"intent:bad": 1}}
    )
    item = opener(broken)
    assert "damaged" in item.page.inner_text("#main .alert")
    assert any("could not render" in line for line in item.console)


# ---------------------------------------------------------------------------
# Layout, reach and names: AC-0031 .. AC-0041
# ---------------------------------------------------------------------------

_WIDTHS = [320, 1280, 1680, 2560]
_SCHEMES = ["light", "dark"]
_MATRIX = [(w, s) for w in _WIDTHS for s in _SCHEMES]
_MATRIX_EXPORTS = ["mixed", "hostile"]
_MATRIX_ID = [f"{w}-{s}" for w, s in _MATRIX]


def _rect(page: Page, selector: str) -> dict[str, float]:
    return page.eval_on_selector(  # type: ignore[no-any-return]
        selector,
        "e => { const r = e.getBoundingClientRect(); return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height }; }",
    )


def _tab_to(page: Page, predicate: str, limit: int = 400) -> None:
    for _ in range(limit):
        page.keyboard.press("Tab")
        if page.evaluate(f"(() => {{ const e = document.activeElement; return !!e && ({predicate}); }})()"):
            return
    raise AssertionError(f"keyboard never reached: {predicate}")


def _pick_first(page: Page) -> str:
    """Open the browse list, click its first row and wait until the detail zone shows it."""
    page.locator('nav a[data-q="browse"]').click()
    _wait_title(page, "All intents")  # the earlier list's rows are still there until the route renders
    page.wait_for_selector("#list a.row-link")
    first = page.locator("#list a.row-link").first
    node = first.get_attribute("data-node")
    first.click()
    page.wait_for_function("() => document.getElementById('main').hasAttribute('data-picked')")
    page.wait_for_function("n => document.querySelector('#detail-body .state-line') !== null", arg=node)
    return node or ""


def _no_overflow(page: Page) -> list[int]:
    return page.evaluate("[document.documentElement.scrollWidth, document.documentElement.clientWidth]")  # type: ignore[no-any-return]


def test_ac_0031_narrow_is_one_column_with_back_to_list(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in _MATRIX_EXPORTS:
        item = opener(exports[name], width=320, height=800)
        page = item.page
        wide = _no_overflow(page)
        assert wide[0] <= wide[1], (name, wide)
        page.locator('nav a[data-q="browse"]').click()
        page.wait_for_selector("#list a.row-link")
        nav, list_ = _rect(page, "#question-list"), _rect(page, "#list-title")
        assert nav["bottom"] <= list_["top"], (name, nav, list_)
        links = page.eval_on_selector_all("#question-list a", "els => els.map(e => Math.round(e.getBoundingClientRect().left))")
        assert len(set(links)) == 1, (name, links)
        node = _pick_first(page)
        _wait_focus_id(page, "detail-heading")
        assert not page.locator("#list").is_visible()
        assert page.locator("#detail-heading").is_visible()
        wide = _no_overflow(page)
        assert wide[0] <= wide[1], (name, "detail", wide)
        page.get_by_role("button", name="Back to list").click()
        page.wait_for_function("() => document.getElementById('list').offsetParent !== null")
        page.wait_for_function("() => !document.querySelector('#detail-body .back-link')")
        page.wait_for_function("n => document.activeElement.dataset.node === n", arg=node)
        wide = _no_overflow(page)
        assert wide[0] <= wide[1], (name, "list", wide)


def test_ac_0031_back_to_list_restores_scroll(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    page = opener(exports["mixed"], width=320, height=400).page
    page.locator('nav a[data-q="browse"]').click()
    _expand_all(page)
    page.wait_for_selector("#list a.row-link")
    last = page.locator("#list .tree").first.locator("a.row-link").last  # the first section's last row
    last.evaluate("e => e.scrollIntoView({ block: 'center' })")
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    page.wait_for_function(  # programmatic scrolls animate: wait until the last row is on screen and still
        "() => { const r = Array.from(document.querySelector('#list .tree').querySelectorAll('a.row-link')).pop().getBoundingClientRect();"
        " const ok = r.bottom <= innerHeight && window.__y === scrollY; window.__y = scrollY; return ok; }"
    )
    before = page.evaluate("scrollY")
    assert before > 0
    node = last.get_attribute("data-node")
    last.evaluate("e => e.click()")  # no scroll: the reader's position is the one measured above
    _wait_focus_id(page, "detail-heading")
    page.get_by_role("button", name="Back to list").click()
    page.wait_for_function("n => document.activeElement.dataset.node === n", arg=node)
    assert abs(page.evaluate("scrollY") - before) <= 2


def test_ac_0032_mid_width_questions_row_above_list_beside_detail(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in _MATRIX_EXPORTS:
        page = opener(exports[name], width=1280).page
        _pick_first(page)
        tops = page.eval_on_selector_all("#question-list a", "els => els.map(e => Math.round(e.getBoundingClientRect().top))")
        assert len(set(tops)) == 1, (name, tops)
        nav, work, detail = _rect(page, "#question-list"), _rect(page, ".worklist"), _rect(page, ".detail")
        assert nav["bottom"] <= work["top"] and nav["bottom"] <= detail["top"], name
        assert work["right"] <= detail["left"] + 1, (name, work, detail)
        assert abs(work["top"] - detail["top"]) <= 2, (name, work, detail)
        assert page.locator("#list").is_visible() and page.locator("#detail-heading").is_visible()


@pytest.mark.parametrize("width", [1680, 2560])
def test_ac_0033_wide_is_rail_list_detail(opener: Any, exports: dict[str, pathlib.Path], width: int) -> None:
    for name in _MATRIX_EXPORTS:
        page = opener(exports[name], width=width).page
        _pick_first(page)
        nav, work, detail = _rect(page, "#question-list"), _rect(page, ".worklist"), _rect(page, ".detail")
        assert nav["right"] <= work["left"] + 1 and work["right"] <= detail["left"] + 1, (name, nav, work, detail)
        tops = [nav["top"], work["top"], detail["top"]]
        assert max(tops) - min(tops) <= 120 and nav["bottom"] > work["top"], (name, nav, work, detail)
        assert width - detail["right"] <= 48, (name, width, detail)
        assert abs(page.evaluate("document.documentElement.scrollWidth") - width) <= 0


_FOCUS_INFO = """() => {
  const e = document.activeElement;
  if (!e || e === document.body) return null;
  if (e.__seen) return { repeat: true };
  e.__seen = true;
  const r = e.getBoundingClientRect();
  const cs = getComputedStyle(e);
  const vy = (Math.max(r.top, 0) + Math.min(r.bottom, innerHeight)) / 2;
  const vx = (Math.max(r.left, 0) + Math.min(r.right, innerWidth)) / 2;
  const hit = document.elementFromPoint(vx, vy);
  // The nearest opaque ancestor background (the page when none is painted).
  let p = e.parentElement, bg = getComputedStyle(document.body).backgroundColor;
  while (p) { const c = getComputedStyle(p).backgroundColor;
    const m = c.match(/[\\d.]+/g);
    if (m && (m.length === 3 || parseFloat(m[3]) > 0.99)) { bg = c; break; } p = p.parentElement; }
  return { repeat: false, tag: e.tagName, text: (e.textContent || '').slice(0, 30), width: r.width,
    height: r.height, outlineStyle: cs.outlineStyle, outlineWidth: parseFloat(cs.outlineWidth),
    outlineColor: cs.outlineColor, bg, hit: hit === e || e.contains(hit),
    visible: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth };
}"""


def _sweep(page: Page, limit: int = 400) -> list[dict[str, Any]]:
    page.evaluate(
        """() => { const s = document.createElement('span'); s.tabIndex = -1; s.id = 'sweep-start';
          document.body.prepend(s); window.scrollTo(0, 0); s.focus(); }"""
    )
    stops: list[dict[str, Any]] = []
    for _ in range(limit):
        page.keyboard.press("Tab")
        info = page.evaluate(_FOCUS_INFO)
        if info is None or info["repeat"]:
            break
        stops.append(info)
    return stops


def _busy(item: Opened, payload: dict[str, Any], name: str, *, picked: bool) -> None:
    """Browse list fully expanded; optionally with a detail open, the Key and Record details open."""
    page = item.page
    node = "intent:bravo-feat" if name == "mixed" else payload["nodes"][0]["id"]
    item.go(_frag(q="browse"))
    page.wait_for_selector("#list a.row-link")
    _expand_all(page)
    page.locator("#key summary").click()  # open while the list is on screen (a narrow page hides it once picked)
    if picked:
        item.go(_frag(q="browse", node=node))
        page.wait_for_selector("#detail-body details.record summary")
        page.locator("#detail-body details.record summary").click()


def _matrix_states(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> Any:
    for name in _MATRIX_EXPORTS:
        payload = payload_of(exports[name])
        for picked in (False, True):
            item = opener(exports[name], width=width, height=700, scheme=scheme)
            _busy(item, payload, name, picked=picked)
            yield name, picked, item.page


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_ID)
def test_ac_0034_focus_is_never_hidden(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    for name, picked, page in _matrix_states(opener, exports, width, scheme):
        stops = _sweep(page)
        assert len(stops) > 10, (name, picked, len(stops))
        for stop in stops:
            assert stop["hit"] and stop["visible"], (name, picked, stop)


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_ID)
def test_ac_0035_targets_are_at_least_24_px(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    for name, picked, page in _matrix_states(opener, exports, width, scheme):
        small = page.evaluate(
            """() => Array.from(document.querySelectorAll('a[href], button, input, select, summary'))
              .map(e => [e, e.getBoundingClientRect()])
              .filter(([e, r]) => r.width > 0 && !e.classList.contains('skip') && (r.width < 24 || r.height < 24))
              .map(([e, r]) => e.outerHTML.slice(0, 80) + ' ' + r.width + 'x' + r.height)"""
        )
        assert small == [], (name, picked, small)


def _contrast_report(page: Page) -> list[tuple[str, float]]:
    raw = page.evaluate(
        """() => {
          const parse = (c) => c.match(/[\\d.]+/g).map(Number);
          const bgOf = (el) => { for (let p = el; p; p = p.parentElement) {
              const m = parse(getComputedStyle(p).backgroundColor);
              if (m.length === 3 || m[3] > 0.99) return m.slice(0, 3); }
            return parse(getComputedStyle(document.body).backgroundColor).slice(0, 3); };
          const out = [];
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) {
            const n = walker.currentNode; const el = n.parentElement;
            if (!n.textContent.trim() || el.closest('select, option, script, noscript')) continue;
            if (!el.getClientRects().length) continue;
            const cs = getComputedStyle(el);
            if (cs.visibility !== 'visible' || el.closest('.visually-hidden, .skip:not(:focus)')) continue;
            out.push([n.textContent.trim().slice(0, 30), parse(cs.color).slice(0, 3), bgOf(el)]);
          }
          for (const el of document.querySelectorAll('input, select')) {
            const cs = getComputedStyle(el);
            out.push([el.id, parse(cs.color).slice(0, 3), bgOf(el)]);
          }
          return out;
        }"""
    )
    return [(label, _ratio(tuple(fg), tuple(bg))) for label, fg, bg in raw]  # type: ignore[arg-type]


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_ID)
def test_ac_0036_text_contrast(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    checked = 0
    for name, picked, page in _matrix_states(opener, exports, width, scheme):
        expected = _canvas_rgb(scheme)
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == expected
        rows = _contrast_report(page)
        checked += len(rows)
        low = [r for r in rows if r[1] < 4.5]
        assert not low, (name, picked, low[:5])
    assert checked > 100


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_ID)
def test_ac_0037_focus_indicator_contrast(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    for name, picked, page in _matrix_states(opener, exports, width, scheme):
        stops = _sweep(page)
        assert stops
        for stop in stops:
            assert stop["outlineStyle"] == "solid" and stop["outlineWidth"] >= 2, (name, picked, stop)
            ratio = _ratio(_rgb(stop["outlineColor"]), _rgb(stop["bg"]))
            assert ratio >= 3, (name, picked, stop, ratio)


def test_ac_0038_keyboard_alone_reaches_every_function(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["related"])
    page = item.page
    page.evaluate("document.body.focus()")
    for key in _QUESTIONS:
        _tab_to(page, f"e.dataset.q === '{key}'")
        page.keyboard.press("Enter")
        page.wait_for_function("k => document.querySelector('nav a[aria-current]').dataset.q === k", arg=key)
    _tab_to(page, "e.id === 'search'")
    page.keyboard.type("bravo")
    page.wait_for_function("() => document.getElementById('list-title').textContent.includes('bravo')")
    page.keyboard.press("Escape")
    page.wait_for_function("() => !document.getElementById('list-title').textContent.includes('bravo')")
    _tab_to(page, "e.id === 'filter-level'")
    page.keyboard.type("f")  # type-ahead picks "feature" without opening the native popup
    page.wait_for_function("() => document.getElementById('filter-level').value === 'feature'")
    page.wait_for_function("() => document.activeElement.id === 'filter-level'")
    page.select_option("#filter-level", "")
    _tab_to(page, "e.matches('button.toggle')")
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.getAttribute('aria-expanded')") == "true"
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.getAttribute('aria-expanded')") == "false"
    _tab_to(page, "e.matches('#list a.row-link')")
    page.keyboard.press("Enter")
    page.wait_for_function("() => document.getElementById('main').hasAttribute('data-picked')")
    _tab_to(page, "e.matches('#detail-body a[data-node]')")
    hash_before = page.evaluate("location.hash")
    page.keyboard.press("Enter")
    _wait_focus_id(page, "detail-heading")
    assert page.evaluate("location.hash") != hash_before
    page.evaluate("document.body.focus()")
    _tab_to(page, "e.matches('#key summary')")
    page.keyboard.press("Enter")
    assert page.evaluate("document.getElementById('key').open") is True
    _tab_to(page, "e.matches('#detail-body details.record summary')")
    page.keyboard.press("Enter")
    assert page.evaluate("document.querySelector('#detail-body details.record').open") is True
    page.go_back()
    page.wait_for_function("h => location.hash === h", arg=hash_before)


def test_ac_0039_landmarks_and_one_h1(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in ("mixed", "empty", "hostile", "incomplete"):
        page = opener(exports[name]).page
        for tag in ("h1", "header", "nav", "main"):
            assert page.locator(tag).count() == 1, (name, tag)


def test_ac_0040_live_region_announces_list_title_and_count(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    page = opener(exports["mixed"]).page
    assert page.locator("#live").get_attribute("aria-live") == "polite"

    def announced() -> str:
        return " ".join(_text(page, "#live").split())

    def expect_matches_list(key: str = "") -> None:
        if key:  # the live text of the previous step still matches its list: wait for the route first
            page.wait_for_selector(f'nav a[data-q="{key}"][aria-current="page"]')
        page.wait_for_function(
            """() => { const t = (id) => document.getElementById(id).textContent;
              return t('live') !== '' && t('live') === t('list-title') + ', ' + t('list-count'); }"""
        )
        assert announced().startswith(_text(page, "#list-title"))

    page.locator('nav a[data-q="roadmap"]').click()
    expect_matches_list("roadmap")
    assert _text(page, "#live").startswith("Capability progress, ")
    page.locator('nav a[data-q="capabilities"]').click()
    expect_matches_list("capabilities")
    page.locator('nav a[data-q="browse"]').click()
    expect_matches_list("browse")
    page.locator("#search").click()
    page.keyboard.type("bravo")
    page.wait_for_function("() => document.getElementById('list-title').textContent.includes('bravo')")
    expect_matches_list()
    page.locator("#search").fill("")
    page.locator('nav a[data-q="browse"]').click()
    page.select_option("#filter-level", "feature")
    expect_matches_list()


def _accessible_names(page: Page) -> list[tuple[str, str]]:
    cdp = page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("Accessibility.enable")
    doc = cdp.send("DOM.getDocument", {"depth": 0})
    found = cdp.send(
        "DOM.querySelectorAll",
        {"nodeId": doc["root"]["nodeId"], "selector": "a[href], button, input, select, summary"},
    )
    names: list[str] = []
    for node_id in found["nodeIds"]:
        tree = cdp.send("Accessibility.getPartialAXTree", {"nodeId": node_id, "fetchRelatives": False})
        live = [n for n in tree["nodes"] if not n.get("ignored")]
        names.append(live[0]["name"]["value"] if live else None)  # None: not rendered (display: none)
    labels = page.evaluate(
        """() => {
          const visible = (n) => Array.from(n.childNodes).map((c) =>
            c.nodeType === 3 ? c.textContent
            : (c.classList && c.classList.contains('visually-hidden')) || c.getAttribute && c.getAttribute('aria-hidden') === 'true' ? '' : visible(c)).join('');
          return Array.from(document.querySelectorAll('a[href], button, input, select, summary')).map((e) =>
            (e.tagName === 'INPUT' || e.tagName === 'SELECT') ? e.labels[0].textContent : visible(e).trim());
        }"""
    )
    cdp.detach()
    assert len(names) == len(labels)
    return [(n, lab) for n, lab in zip(names, labels, strict=True) if n is not None]


def test_ac_0041_names_contain_visible_labels(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in _MATRIX_EXPORTS:
        item = opener(exports[name])
        _busy(item, payload_of(exports[name]), name, picked=True)
        page = item.page
        pairs = _accessible_names(page)
        assert len(pairs) > 15
        for accessible, label in pairs:
            assert accessible.strip(), (name, label)
            # A toggle's glyph is aria-hidden, so its visible label is empty and checked below.
            assert _squash(label) in _squash(accessible), (name, accessible, label)
        toggles = page.evaluate(
            """() => Array.from(document.querySelectorAll('button.toggle')).map(
              (b) => [b.getAttribute('aria-label') || b.textContent,
                      b.closest('li').querySelector('a.row-link .c-name').textContent])"""
        )
        assert toggles, name
    roadmap = opener(exports["roadmap"])
    roadmap.go(_frag(q="roadmap"))
    for accessible, label in _accessible_names(roadmap.page):
        assert accessible.strip() and _squash(label) in _squash(accessible), (accessible, label)
    page = opener(exports["mixed"]).page
    page.locator('nav a[data-q="browse"]').click()
    page.wait_for_selector("button.toggle")
    names = page.evaluate(
        """() => Array.from(document.querySelectorAll('button.toggle')).map(
          (b) => [b.closest('li').querySelector('a.row-link .c-name').textContent])"""
    )
    toggle_names = [n for n, _ in _accessible_names(page) if n.startswith("Show ")]
    assert len(toggle_names) == len(names) > 0
    for accessible, (display,) in zip(toggle_names, names, strict=True):
        assert _squash(display) in _squash(accessible), (accessible, display)


# ---------------------------------------------------------------------------
# Review round 1: focus, row layout, narrow search, skip link, first-screen summary
# ---------------------------------------------------------------------------


def test_fix_filter_change_keeps_focus_and_clear_controls_leave_focus(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    page = opener(exports["related"]).page
    _choose_via(page, "browse")
    page.locator("#filter-level").focus()
    page.keyboard.type("f")
    page.wait_for_function("() => document.getElementById('filter-level').value === 'feature'")
    page.wait_for_function("() => document.activeElement.id === 'filter-level'")
    # Clear filters: the button vanishes with the re-render, so focus must be placed on purpose.
    item = opener(exports["related"])
    item.go(_frag(q="browse", level="feature", status="No-such-status"))
    item.page.get_by_role("button", name="Clear filters").click()
    item.page.wait_for_function("() => document.querySelector('#list .tree') !== null")
    assert item.page.evaluate("document.activeElement.id") == "list-title"
    # Clear search lands on the search field.
    item.page.locator("#search").fill("zzzz-nothing")
    item.page.get_by_role("button", name="Clear search").click()
    item.page.wait_for_function("() => document.getElementById('search').value === ''")
    assert item.page.evaluate("document.activeElement.id") == "search"


def _choose_via(page: Page, key: str) -> None:
    page.locator(f'nav a[data-q="{key}"]').click()
    page.wait_for_selector("#filters:not([hidden]) select")


def test_fix_rows_stay_inside_their_row_from_640_to_1440(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for width in (640, 700, 730, 800, 900, 1024, 1280, 1440):
        page = opener(exports["mixed"], width=width, height=900).page
        _pick_first(page)
        rows = page.evaluate(
            """() => Array.from(document.querySelectorAll('#list a.row-link')).map((row) => {
              const r = row.getBoundingClientRect();
              const cells = Array.from(row.children).map((c) => c.getBoundingClientRect());
              return { right: r.right, cells: cells.map((c) => c.right), name: cells[0].width,
                       height: r.height };
            })"""
        )
        assert rows, width
        for row in rows:
            assert all(c <= row["right"] + 0.5 for c in row["cells"]), (width, row)
            assert row["name"] >= 100, (width, row)
        wide = _no_overflow(page)
        assert wide[0] <= wide[1], (width, wide)


def test_fix_narrow_search_while_picked_shows_the_results(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    page = opener(exports["mixed"], width=320, height=800).page
    _pick_first(page)
    assert not page.locator("#list").is_visible()
    page.locator("#detail-body .back-link").click()
    _pick_first_row = page.locator("#list a.row-link").first
    _pick_first_row.click()
    page.wait_for_function("() => document.getElementById('main').hasAttribute('data-picked')")
    assert not page.locator("#list").is_visible()
    page.locator("#search").evaluate("e => e.scrollIntoView()")
    page.locator("#search").fill("bravo")
    page.wait_for_function("() => document.getElementById('list').offsetParent !== null")
    assert page.locator("#list a.row-link").count() > 0
    assert page.evaluate("document.activeElement.id") == "search"


def test_fix_skip_link_is_a_control_only_when_the_detail_is_beside_the_list(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    narrow = opener(exports["mixed"], width=320).page
    assert narrow.evaluate("getComputedStyle(document.getElementById('skip-details')).display") == "none"
    wide = opener(exports["mixed"], width=1280).page
    wide.locator("#skip-details").focus()
    assert wide.locator("#skip-details").is_visible()
    wide.keyboard.press("Enter")
    _wait_focus_id(wide, "detail-heading")


def test_fix_detail_link_to_the_current_item_does_not_stick(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"], width=1280)
    page = item.page
    _choose(item, "capabilities")
    page.locator('#list a.row-link[data-node="capability:alpha-cap"]').click()
    page.wait_for_function("() => document.querySelector('#detail-body .state-line') !== null")
    # A detail link back to the same item changes nothing; the next list pick must still be announced.
    page.evaluate(
        """() => { const a = document.createElement('a'); a.className = 'node-link';
          a.href = location.hash; a.id = 'self-link'; a.textContent = 'self';
          document.getElementById('detail-body').appendChild(a); }"""
    )
    page.locator("#self-link").click()
    page.locator('#list a.row-link[data-node="outcome:charlie-out"]').click()
    assert _live(page, "Showing Charlie").startswith("Showing")


def test_fix_browser_back_below_40rem_keeps_focus(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    page = opener(exports["mixed"], width=390, height=800).page
    node = _pick_first(page)
    page.go_back()
    page.wait_for_function("() => document.getElementById('list').offsetParent !== null")
    page.wait_for_function("n => document.activeElement.dataset.node === n", arg=node)


def test_fix_detail_zone_is_keyboard_scrollable(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    page = opener(exports["mixed"], width=1280).page
    assert page.locator("section.detail").get_attribute("tabindex") == "0"


def test_fix_first_screen_detail_summarises_the_list(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"], width=1280)
    page = item.page
    assert "Pick an item to see its next step." in _text(page, "#detail-body")
    summary = _text(page, "#detail-body .list-summary")
    counts = [int(n) for n in re.findall(r"(\d+) ", summary)]
    assert sum(counts) == len(_ids(page)) > 0, summary
    assert "brief" in summary or "spec" in summary or "intent" in summary, summary
    _choose(item, "broken")
    # An empty list adds no summary beside its positive line.
    assert page.locator("#detail-body .list-summary").count() == 0
    assert page.locator("#main[data-picked]").count() == 0
    broken = opener(exports["hostile_diag"], width=1280)
    _choose(broken, "broken")
    broken.page.wait_for_function("() => document.querySelector('#detail-body .list-summary') !== null")
    text = _text(broken.page, "#detail-body .list-summary")
    counts = [int(n) for n in re.findall(r"(\d+) ", text)]
    assert sum(counts) == len(_ids(broken.page)) and "1 delivery diagnostic" in text, text


def test_fix_broken_summary_states_no_count_it_cannot_know(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["hostile_incomplete"], width=1280)
    _choose(item, "broken")
    item.page.wait_for_function("() => document.querySelector('#detail-body .list-summary') !== null")
    text = _text(item.page, "#detail-body .list-summary")
    assert "Delivery diagnostics were unavailable." in text and "delivery diagnostic," not in text, text
    assert " 0 " not in f" {text} ", text


def test_fix_context_cell_is_never_clipped(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    """The count, the ancestor and the diagnostic code stay visible at every three-track width."""
    for width in (1024, 1280, 1440, 1680, 2560):
        for name, question in (("mixed", "next"), ("mixed", "capabilities"), ("hostile_diag", "broken")):
            item = opener(exports[name], width=width)
            _choose(item, question)
            clipped = item.page.eval_on_selector_all(
                "#list .c-context", "els => els.filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.textContent)"
            )
            assert clipped == [], (width, question, clipped)


def test_fix_open_beneath_aligns_name_and_state(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    page = _pick(opener(exports["mixed"], width=1280), "capability:alpha-cap")
    section = _detail_part(page, "Open beneath")
    rows = section.locator("li").evaluate_all(
        """els => els.map(li => [Math.round(li.querySelector('a[data-node]').getBoundingClientRect().left),
          Math.round(li.querySelector('.mark').getBoundingClientRect().left)])"""
    )
    assert len(rows) == 4
    assert len({r[1] for r in rows}) == 1, rows  # the state column starts at the same place on every row


def test_fix_broken_row_diagnostic_code_is_mono_and_unbroken(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["hostile_diag"], width=1280)
    _choose(item, "broken")
    code = item.page.locator("#list .c-context .value", has_text="delivery-relation-ambiguous").first
    assert code.count() == 1
    assert "mono" in code.evaluate("e => getComputedStyle(e).fontFamily").lower() or "Menlo" in code.evaluate("e => getComputedStyle(e).fontFamily")
    assert code.evaluate("e => getComputedStyle(e).overflowWrap") == "normal"
    assert code.evaluate("e => getComputedStyle(e).whiteSpace") == "nowrap"


def test_fix_approved_glyph_uses_the_text_colour(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    page = opener(exports["mixed"]).page
    colours = page.evaluate(
        """() => { const g = document.querySelector('.mark[data-mark="approved"] .mark-g');
          return g ? [getComputedStyle(g).color, getComputedStyle(document.body).color] : null; }"""
    )
    assert colours is not None and colours[0] == colours[1], colours


# ---------------------------------------------------------------------------
# Intent dependency graphs: the "Dependencies" part, broken entries, record groups, Key, routing
# ---------------------------------------------------------------------------

_DEP_ROOT = _FIXTURES / "dependency"
_DIRS = {"prerequisites": "What it waits for", "dependents": "What waits for it", "both": "Both"}
_STEPS = ["1", "2", "3", "all"]
_DEP_LEAD = "From Depends on: headers only. This does not check whether work can start."
_PART_ID = """el => { const a = el.querySelector('a[data-node]');
  return a ? a.dataset.node : el.querySelector('.outside .value').textContent; }"""


def _dep_frag(node: str, dep: str = "prerequisites", steps: str = "1", q: str = "browse") -> str:
    """A fragment holding the choices only when they are not the defaults."""
    return _frag(q=q, node=node, dir="" if dep == "prerequisites" else dep, steps="" if steps == "1" else steps)


def _dep_pick(item: Opened, node: str, dep: str = "prerequisites", steps: str = "1") -> Page:
    item.go(_dep_frag(node, dep, steps))
    item.page.wait_for_selector("#detail-body .state-line")
    return item.page


def _depth(payload: dict[str, Any], steps: str) -> int:
    """The query depth for a "Steps" choice; All is the number of live intents."""
    live = payload["summary"]["intents_by_level"]
    return sum(live.values()) if steps == "all" else int(steps)


def _page_part(page: Page) -> dict[str, Any]:
    """What the "Dependencies" part shows, read as ids: lines, pointer diagnostics, cycles."""
    return page.evaluate(  # type: ignore[no-any-return]
        """() => {
          const id = (el) => { const a = el.querySelector('a[data-node]');
            return a ? a.dataset.node : el.querySelector('.outside .value').textContent; };
          const part = [...document.querySelectorAll('#detail-body section.part')]
            .find(s => s.querySelector('h3').textContent === 'Dependencies');
          const lines = [...part.querySelectorAll('.dep-line')].map(li =>
            [id(li.querySelector('.dep-waiting')), id(li.querySelector('.dep-prereq'))]);
          const pointers = [], cycles = [];
          part.querySelectorAll('.dep-diag').forEach(li => {
            const members = li.querySelector('.dep-members');
            if (members) { cycles.push([...members.children].map(id)); return; }
            const chip = li.querySelector('.label-state');
            pointers.push([id(li.querySelector('.dep-source')), li.querySelector('code.value').textContent,
              chip ? chip.textContent : 'outside_scope']);
          });
          return { lines, pointers, cycles };
        }"""
    )


class _DepModel:
    """A reference for the part, written from the spec's terms and not from the page code."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.model = Model(payload)
        deps = payload["dependencies"]
        self.edges = [(e["from"], e["to"]) for e in deps["edges"]]
        self.pointers = [d for d in deps["diagnostics"] if "from" in d]
        self.cycles = [d["members"] for d in deps["diagnostics"] if d["state"] == "cycle"]

    def name(self, node_id: str) -> tuple[str, str]:
        label = self.model.display(node_id) if node_id in self.model.nodes else node_id
        return label.lower(), node_id

    def steps(self, start: str, direction: str, depth: int) -> dict[str, int]:
        found: dict[str, int] = {}
        for forward in (True, False):
            if direction == ("dependents" if forward else "prerequisites"):
                continue
            seen = {start: 0}
            frontier = [start]
            for hop in range(1, depth + 1):
                nxt = []
                for at in frontier:
                    for waiting, prerequisite in self.edges:
                        near, far = (waiting, prerequisite) if forward else (prerequisite, waiting)
                        if near == at and far not in seen:
                            seen[far] = hop
                            nxt.append(far)
                frontier = nxt
            for node_id, hop in seen.items():
                found[node_id] = min(hop, found.get(node_id, hop))
        return found

    def expect(self, start: str, direction: str, depth: int) -> dict[str, Any]:
        counts = self.steps(start, direction, depth)
        lines = sorted(
            ((w, p) for w, p in self.edges if w in counts and p in counts),
            key=lambda e: (max(counts[e[0]], counts[e[1]]), self.name(e[0]), self.name(e[1])),
        )
        pointers = sorted(
            (d for d in self.pointers if d["from"] in counts), key=lambda d: (self.name(d["from"]), d["position"])
        )
        cycles = sorted(
            (sorted(c, key=self.name) for c in self.cycles if any(m in counts for m in c)),
            key=lambda c: self.name(c[0]),
        )
        return {
            "counts": counts,
            "lines": [list(line) for line in lines],
            "pointers": [[d["from"], d["value"], d["state"]] for d in pointers],
            "cycles": cycles,
        }


def test_vi_3001_part_placement_lead_and_controls(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["dependency"])
    page = _dep_pick(item, "intent:alpha")
    order = page.eval_on_selector_all(
        "#detail-body > *",
        "els => els.map(e => e.classList.contains('state-line') ? 'state-line' : e.tagName === 'SECTION' ? e.querySelector('h3').textContent : e.tagName === 'DETAILS' ? 'details' : 'other')",
    )
    assert [o for o in order if o != "other"] == [
        "state-line", "Next step", "Open beneath", "What is broken", "Where it sits", "Dependencies", "Open the file", "details",
    ]
    part = _detail_part(page, "Dependencies")
    assert part.locator("h3").evaluate("e => e.tagName") == "H3"
    assert part.locator("p.lead").inner_text() == _DEP_LEAD
    assert part.evaluate("e => e.querySelector('h3').nextElementSibling.classList.contains('lead')")
    labels = part.locator("label").all_inner_texts()
    assert labels == ["Show", "Steps"]
    for label, expected in (("Show", list(_DIRS.values())), ("Steps", ["1", "2", "3", "All"])):
        select = part.locator("label", has_text=label).evaluate("l => document.getElementById(l.htmlFor)")
        assert select is not None
        control = page.locator(f"#{part.locator('label', has_text=label).get_attribute('for')}")
        assert control.evaluate("e => e.tagName") == "SELECT"
        assert control.locator("option").all_inner_texts() == expected
    assert page.locator("#dep-dir").input_value() == "prerequisites"
    assert page.locator("#dep-steps").input_value() == "1"
    assert page.locator("#dep-dir option").evaluate_all("els => els.map(e => e.value)") == list(_DIRS)
    assert page.locator("#dep-steps option").evaluate_all("els => els.map(e => e.value)") == _STEPS
    # A brief or spec has no such part, and an intent of any export has it.
    mixed = opener(exports["mixed"])
    for node_id, has_part in (("brief:bravo-delivery", False), ("spec:bravo-spec", False), ("intent:bravo-feat", True)):
        page = _pick(mixed, node_id)
        titles = page.eval_on_selector_all("#detail-body h3.part-head", "els => els.map(e => e.textContent)")
        assert ("Dependencies" in titles) is has_part, node_id
        assert titles[:2] == ["Next step", "Open beneath"]
    assert titles.index("Dependencies") == titles.index("Where it sits") + 1
    assert titles.index("Open the file") == titles.index("Dependencies") + 1


def test_vi_3002_edge_lines_order_named_intents_and_empty_lines(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["dependency"])
    payload = payload_of(exports["dependency"])
    ref = _DepModel(payload)
    model = ref.model
    # One line per edge, "<waiting> waits for <prerequisite>", nearest first and then by name.
    page = _dep_pick(item, "intent:delta", "prerequisites", "all")
    lines = _detail_part(page, "Dependencies").locator("li.dep-line")
    assert lines.count() == 4
    first = lines.first
    assert first.locator(".dep-word").inner_text() == "waits for"
    assert first.locator(".dep-waiting a").inner_text() == "Delta"
    assert first.locator(".dep-prereq a").inner_text() == "Echo"
    assert first.locator(".dep-waiting .mark").count() == 1 and first.locator(".dep-prereq .mark").count() == 1
    assert re.fullmatch(r"Delta\s*◇\s*Draft\s+waits for\s+Echo\s*◇\s*Draft", first.inner_text().strip()), first.inner_text()
    assert _page_part(page)["lines"] == [
        ["intent:delta", "intent:echo"], ["intent:delta", "intent:foxtrot"],
        ["intent:echo", "intent:golf"], ["intent:foxtrot", "intent:golf"],
    ]
    assert _detail_part(page, "Dependencies").locator("p.dep-sort").inner_text() == "Nearest first, then by name"
    # Both directions across a cycle: every edge of the group is one line, by name.
    page = _dep_pick(item, "intent:november", "both", "all")
    shown = _page_part(page)
    assert shown["lines"] == [
        ["intent:mike", "intent:november"], ["intent:november", "intent:mike"],
        ["intent:november", "intent:oscar"], ["intent:oscar", "intent:november"],
    ]
    assert shown["cycles"] == [["intent:mike", "intent:november", "intent:oscar"]]
    # Step count orders lines: the chain's nearest edge comes first, and an edge's count is its larger end.
    page = _dep_pick(item, "intent:alpha", "prerequisites", "3")
    assert _page_part(page)["lines"] == [
        ["intent:alpha", "intent:bravo"], ["intent:bravo", "intent:charlie"],
        ["intent:charlie", "outcome:quebec"], ["intent:charlie", "opportunity:romeo"], ["intent:charlie", "capability:root-b"],
    ]
    # The whole reference model agrees for every choice of every intent.
    for node_id in model.nodes:
        for direction in _DIRS:
            for steps in _STEPS:
                page = _dep_pick(item, node_id, direction, steps)
                want = ref.expect(node_id, direction, _depth(payload, steps))
                got = _page_part(page)
                assert got["lines"] == want["lines"], (node_id, direction, steps)
                assert got["pointers"] == want["pointers"], (node_id, direction, steps)
                assert got["cycles"] == want["cycles"], (node_id, direction, steps)
    # Named intents outside the export are plain text marked so, in id name order.
    scoped = opener(exports["dependency_from"])
    page = _dep_pick(scoped, "intent:india", "both", "all")
    part = _detail_part(page, "Dependencies")
    outside = part.locator("li.dep-line .outside")
    assert outside.count() >= 2
    assert {o.locator(".value").inner_text() for o in outside.all()} == {"intent:juliet", "intent:kilo"}
    for o in outside.all():
        assert "outside this export" in o.inner_text()
        assert o.locator("a").count() == 0 and o.locator(".mark").count() == 0
    assert _page_part(page)["lines"] == [
        ["intent:india", "intent:juliet"], ["intent:juliet", "intent:kilo"], ["intent:kilo", "intent:india"],
    ]
    # The three empty lines, and the line for an intent with values but no edge.
    for direction, line in (
        ("prerequisites", "It waits for nothing in its Depends on: header."),
        ("dependents", "No intent's Depends on: header names it."),
        ("both", "No dependencies recorded."),
    ):
        page = _dep_pick(item, "capability:root-a", direction, "all")
        part = _detail_part(page, "Dependencies")
        assert part.locator("p.empty").inner_text() == line
        assert part.locator("li").count() == 0 and part.locator("p.dep-sort").count() == 0
    page = _dep_pick(item, "intent:golf", "prerequisites", "1")
    part = _detail_part(page, "Dependencies")
    assert part.locator("p.empty").inner_text() == "No line to show. Its Depends on: values are listed below."
    assert part.locator("li.dep-line").count() == 0 and part.locator("li.dep-diag").count() > 0


def test_vi_3002_diagnostics_order_marks_and_code_values(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["dependency"])
    payload = payload_of(exports["dependency"])
    page = _dep_pick(item, "intent:golf", "prerequisites", "1")
    part = _detail_part(page, "Dependencies")
    golf = [d for d in payload["dependencies"]["diagnostics"] if d.get("from") == "intent:golf"]
    items = part.locator("li.dep-diag")
    assert items.count() == len(golf) == 19
    shown = _page_part(page)["pointers"]
    assert shown == [[d["from"], d["value"], d["state"]] for d in golf]  # written order
    for i, d in enumerate(golf):
        li = items.nth(i)
        assert li.locator("code.value").all_inner_texts() == [d["value"]]
        assert li.locator(".dep-source a").get_attribute("data-node") == "intent:golf"
        if d["state"] == "outside_scope":
            assert li.locator(".edge-line > .mark").count() == 0 and li.locator(".label-state").count() == 0
            assert "not an intent, outside this view" in li.inner_text()
            assert "✕" not in li.inner_text()
        else:
            assert li.locator(".edge-line > .mark").count() == 1
            assert li.locator(".edge-line > .mark .mark-g").inner_text() == "✕"
            assert li.locator(".edge-line > .mark .mark-g").get_attribute("aria-hidden") == "true"
            assert li.locator(".edge-line > .mark .mark-w").inner_text() == "Broken"
            assert li.locator(".label-state").inner_text() == d["state"]
            # Generated words never sit inside the value's own element.
            assert d["state"] not in li.locator("code.value").inner_text() or d["state"] in d["value"]
    # Pointer diagnostics by source name then position, then cycles by their first member by name.
    page = _dep_pick(item, "intent:india", "both", "all")
    part = _detail_part(page, "Dependencies")
    cycle = part.locator("li.dep-diag", has=page.locator(".dep-members"))
    assert cycle.count() == 1
    assert cycle.locator(".edge-line > .mark .mark-w").inner_text() == "Broken" and cycle.locator(".label-state").inner_text() == "cycle"
    members = cycle.locator(".dep-members > *")
    assert members.evaluate_all("els => els.map(e => e.querySelector('a').dataset.node)") == [
        "intent:india", "intent:juliet", "intent:kilo",
    ]
    assert cycle.locator("code").count() == 0
    kinds = part.locator("li.dep-diag").evaluate_all("els => els.map(e => !!e.querySelector('.dep-members'))")
    assert kinds == sorted(kinds)  # cycles after every pointer diagnostic
    # Only the cycle's own members are named: a self-dependency is a one-member cycle.
    page = _dep_pick(item, "intent:hotel", "both", "1")
    part = _detail_part(page, "Dependencies")
    assert _page_part(page)["lines"] == [["intent:hotel", "intent:hotel"]]
    assert _page_part(page)["cycles"] == [["intent:hotel"]]
    # The picked intent's own dependency record names an intent outside the export in plain text.
    scoped = opener(exports["dependency_from"])
    page = _dep_pick(scoped, "intent:india", "prerequisites", "1")
    cyc = _page_part(page)["cycles"]
    assert cyc == [["intent:india", "intent:juliet", "intent:kilo"]]


def _query_part(root: pathlib.Path, node_id: str, direction: str, depth: int) -> dict[str, Any]:
    result = _query(root, "--operation", "dependencies", "--id", node_id, "--direction", direction, "--depth", str(depth))
    return {
        "pairs": {(e["from"], e["to"]) for e in result["edges"]},
        "intents": {i["id"] for i in result["intents"]},
        "pointers": {(d["from"], d["value"], d["state"]) for d in result["diagnostics"] if "from" in d},
        "cycles": {tuple(d["members"]) for d in result["diagnostics"] if d["state"] == "cycle"},
    }


@pytest.mark.parametrize("export_name", ["dependency", "dependency_from"])
def test_vi_3003_part_equals_the_query(opener: Any, exports: dict[str, pathlib.Path], export_name: str) -> None:
    payload = payload_of(exports[export_name])
    scoped = export_name == "dependency_from"
    whole = payload_of(exports["dependency"])
    if scoped:
        # The scope's linked set holds an intent outside nodes, and the whole corpus holds
        # an edge and a diagnostic this export does not.
        edge_keys = {(e["from"], e["to"]) for e in payload["dependencies"]["edges"]}
        outside = {i for e in edge_keys for i in e} - {n["id"] for n in payload["nodes"]}
        assert outside
        assert len(whole["dependencies"]["edges"]) > len(payload["dependencies"]["edges"])
        assert len(whole["dependencies"]["diagnostics"]) > len(payload["dependencies"]["diagnostics"])
    item = opener(exports[export_name])
    seen = 0
    for node in payload["nodes"]:
        node_id = node["id"]
        for direction in _DIRS:
            for steps in _STEPS:
                page = _dep_pick(item, node_id, direction, steps)
                shown = _page_part(page)
                want = _query_part(_DEP_ROOT, node_id, direction, _depth(whole, steps))
                assert {tuple(p) for p in shown["lines"]} == want["pairs"], (node_id, direction, steps)
                assert len(shown["lines"]) == len(want["pairs"])
                assert {node_id} | {i for line in shown["lines"] for i in line} == want["intents"], (node_id, direction, steps)
                assert {tuple(p) for p in shown["pointers"]} == want["pointers"], (node_id, direction, steps)
                assert {tuple(c) for c in shown["cycles"]} == want["cycles"], (node_id, direction, steps)
                seen += 1
    assert seen == len(payload["nodes"]) * len(_DIRS) * len(_STEPS)


def _holder_contexts(page: Page) -> list[tuple[str, str]]:
    found = page.eval_on_selector_all(
        "#list a.row-link", "els => els.map(e => [e.dataset.node, e.querySelector('.c-context').textContent])"
    )
    return [(h, c) for h, c in found]


@pytest.mark.parametrize("export_name", ["dependency", "dependency_from", "dependency_incomplete", "hostile_diag"])
def test_vi_3004_broken_rows_and_state_line(opener: Any, exports: dict[str, pathlib.Path], export_name: str) -> None:
    payload = payload_of(exports[export_name])
    model = Model(payload)
    item = opener(exports[export_name])
    page = item.page
    _choose(item, "broken")
    expected = model.broken()
    assert _holder_contexts(page) == expected
    assert _count_text(page) == f"{len(expected)} entries"
    assert page.locator("nav a[data-q='broken'] .q-count").inner_text() == str(len(expected))
    assert page.locator("#list .mark-w", has_text="Broken").count() == len(expected)
    deps = model.dependency_broken()
    assert deps and {h for h, _ in deps} <= set(model.records)
    if export_name == "dependency_from":
        # Only in-scope intents hold an entry: the linked set's other members hold none here.
        assert {h for h, _ in expected} <= {n["id"] for n in payload["nodes"]}
        assert [c for h, c in expected if h == "intent:india"] == [
            "Depends on: dangling", "Depends on: kind_mismatch", "Depends on: cycle",
        ]
        assert "intent:juliet" not in {h for h, _ in expected}
    if export_name == "dependency_incomplete":
        assert payload["outstanding"]["available"] is False
        assert "Delivery diagnostics were unavailable" in _text(page, "#list")
        counts = _rail_counts(page)
        assert [counts[k] for k in ("next", "capabilities", "noparent")] == ["unknown"] * 3
        assert counts["broken"] == str(len(expected))
    for node_id in model.nodes:
        page = _pick(item, node_id, "broken")
        held = [c for h, c in expected if h == node_id]
        assert f"{len(held)} broken" in _text(page, ".state-line"), node_id
        section = _detail_part(page, "What is broken")
        dep_items = section.locator("li.edge", has=page.locator(".field", has_text="Depends on:"))
        assert dep_items.count() == len([c for c in held if c.startswith("Depends on:")]), node_id


def test_vi_3004_holder_order_and_detail_rendering(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["dependency"])
    page = item.page
    _choose(item, "broken")
    rows = _holder_contexts(page)
    assert [c for h, c in rows if h == "intent:india"] == ["Depends on: dangling", "Depends on: kind_mismatch", "Depends on: cycle"]
    assert [c for h, c in rows if h == "intent:golf"][:2] == ["Depends on: unparseable", "Depends on: dangling"]
    assert [c for h, c in rows if h == "intent:hotel"] == ["Depends on: cycle"]
    # A cycle is one entry for each of its members.
    assert {h for h, c in rows if c == "Depends on: cycle"} == {
        "intent:hotel", "intent:india", "intent:juliet", "intent:kilo", "intent:mike", "intent:november", "intent:oscar",
    }
    # The detail part: field, the Key's meaning of the state, then the value or the other members.
    page = _pick(item, "intent:india", "broken")
    key_text = page.text_content("#key-body") or ""
    section = _detail_part(page, "What is broken")
    entries = section.locator("li.edge")
    assert entries.count() == 3
    assert [entries.nth(i).locator(".field").inner_text() for i in range(3)] == ["Depends on:"] * 3
    assert [entries.nth(i).locator(".label-state").inner_text() for i in range(3)] == ["dangling", "kind_mismatch", "cycle"]
    for i in range(3):
        meaning = entries.nth(i).locator("p.meaning").inner_text()
        assert meaning in key_text
    assert entries.nth(0).locator("code.value").all_inner_texts() == ["intent:ghost"]
    assert entries.nth(1).locator("code.value").all_inner_texts() == ["capability:alpha"]
    cyc = entries.nth(2)
    assert cyc.locator("code").count() == 0
    assert cyc.locator("a[data-node]").evaluate_all("els => els.map(e => e.dataset.node)") == ["intent:juliet", "intent:kilo"]
    assert "0 open beneath · 3 broken" in _text(page, ".state-line") or "3 broken" in _text(page, ".state-line")
    # A one-member cycle names no other member.
    page = _pick(item, "intent:hotel", "broken")
    only = _detail_part(page, "What is broken").locator("li.edge")
    assert only.count() == 1 and only.locator("a[data-node]").count() == 0
    # Inherited entries come first: a refused parent, then dependency faults by position, then the cycle.
    hostile = opener(exports["hostile_diag"])
    _choose(hostile, "broken")
    contexts = [c for h, c in _holder_contexts(hostile.page) if h == "intent:hostile-child"]
    inherited = [c for c in contexts if not c.startswith("Depends on:")]
    assert contexts == inherited + ["Depends on: unparseable"] * 4 + ["Depends on: cycle"]
    assert any(c.startswith("Delivery diagnostic") for c in inherited)
    page = _pick(hostile, "intent:hostile-pointer", "broken")
    fields = _detail_part(page, "What is broken").locator("li.edge .field").all_inner_texts()
    assert fields == ["Parent intent", "Depends on:"]
    # Entries come from intent headers: all of this holds with outstanding unavailable.
    gone = opener(exports["hostile_incomplete"])
    _choose(gone, "broken")
    held = [c for h, c in _holder_contexts(gone.page) if h == "intent:hostile-child" and c.startswith("Depends on:")]
    assert held == ["Depends on: unparseable"] * 4 + ["Depends on: cycle"]


def test_vi_3004_mixed_counts_are_unchanged(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    counts = _rail_counts(item.page)
    assert [counts[k] for k in ("next", "capabilities", "noparent", "broken")] == ["3", "2", "6", "0"]
    assert payload_of(exports["mixed"])["dependencies"] == {"edges": [], "diagnostics": []}


def _open_record(page: Page) -> Any:
    page.locator("#detail-body details.record summary").click()
    return page.locator("#detail-body details.record")


def test_vi_3004_record_detail_groups(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["dependency"])
    page = _dep_pick(item, "intent:alpha")
    record = _open_record(page)
    groups = record.locator("h4.label-group").all_inner_texts()
    assert groups[-2:] == ["Depends on, written here", "Depends on, written elsewhere"]
    assert groups[groups.index("Related, written elsewhere") + 1 :] == groups[-2:]
    here = record.locator("section.group", has=page.locator("h4", has_text="Depends on, written here")).first
    rows = here.locator("li.edge")
    assert rows.count() == 3  # intent:bravo once, its path, and the spec value: each distinct value once
    assert here.locator("code.value").all_inner_texts() == [
        "intent:bravo", "docs/product/intents/FEAT-0002-bravo.md", "spec:some-spec",
    ]
    assert here.locator(".label-form").all_inner_texts() == ["typed", "path", "typed"]
    assert here.locator(".label-trust").all_inner_texts() == ["pointer_unchecked"] * 3
    assert rows.nth(0).locator("a[data-node]").get_attribute("data-node") == "intent:bravo"
    assert rows.nth(1).locator("a[data-node]").get_attribute("data-node") == "intent:bravo"
    assert rows.nth(2).locator(".label-state").inner_text() == "outside_scope"
    assert rows.nth(2).locator("a").count() == 0
    # A refused value shows its state label in place of a target.
    page = _dep_pick(item, "intent:delta")
    here = _open_record(page).locator("section.group", has=page.locator("h4", has_text="Depends on, written here")).first
    assert here.locator("code.value").all_inner_texts() == ["intent:echo", "intent:foxtrot", "feature:typo"]
    assert here.locator("li.edge").nth(2).locator(".label-state").inner_text() == "unparseable"
    assert here.locator("li.edge").nth(2).locator(".label-form").inner_text() == "unrecognized"
    # Written elsewhere: named intents in name order, each with its trust class.
    page = _dep_pick(item, "intent:golf")
    elsewhere = _open_record(page).locator("section.group", has=page.locator("h4", has_text="Depends on, written elsewhere")).first
    assert elsewhere.locator("a[data-node]").evaluate_all("els => els.map(e => e.dataset.node)") == ["intent:echo", "intent:foxtrot"]
    assert elsewhere.locator(".label-trust").all_inner_texts() == ["pointer_unchecked"] * 2
    page = _dep_pick(item, "capability:root-a")
    elsewhere = _open_record(page).locator("section.group", has=page.locator("h4", has_text="Depends on, written elsewhere")).first
    assert elsewhere.locator("p.empty").inner_text() == "None."
    # A brief or spec gains neither group.
    mixed = opener(exports["mixed"])
    page = _pick(mixed, "spec:bravo-spec")
    titles = _open_record(page).locator("h4.label-group").all_inner_texts()
    assert not [t for t in titles if t.startswith("Depends on")]
    # Under --from, a dependent outside the export is named in plain text.
    scoped = opener(exports["dependency_from"])
    page = _dep_pick(scoped, "intent:india")
    elsewhere = _open_record(page).locator("section.group", has=page.locator("h4", has_text="Depends on, written elsewhere")).first
    assert elsewhere.locator(".outside .value").all_inner_texts() == ["intent:kilo"]
    assert "outside this export" in elsewhere.inner_text()


def test_vi_3004_key_additions(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    page.locator("#key summary").click()
    key = page.locator("#key dl.key-list")
    terms = key.locator("dt").all_inner_texts()
    for name in ("Depends on, written here", "Depends on, written elsewhere", "outside_scope", "waits for", *_FORMS):
        assert any(name in t for t in terms), name
    waits = key.locator(".fact", has=page.locator("dt", has_text="waits for")).locator("dd").inner_text()
    assert waits == "The first intent's Depends on: header names the second. The view does not decide whether either can start."
    for form in _FORMS:
        row = key.locator(".fact", has=page.locator(".label-form", has_text=re.compile(f"^{form}$")))
        assert row.count() == 1 and row.locator("dd").inner_text().strip() != ""
    cycle = key.locator(".fact", has=page.locator(".label-state", has_text=re.compile("^cycle$"))).locator("dd").inner_text()
    assert "parent loop" in cycle and "dependency loop" in cycle
    assert "outside_scope" in key.inner_text()
    cross = key.locator(".fact", has=page.locator(".mark[data-mark='broken']")).locator("dd").inner_text()
    assert "dependency loop" in cross
    _choose(item, "broken")
    assert "dependency loops" in _text(page, "#list-lead")
    assert _text(page, "#list-lead") == "Pointers that did not resolve, parent or dependency loops made of resolved pointers, and problems the delivery resolver found."


def test_vi_3004_closed_label_set_over_the_hostile_export(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["hostile"])
    assert payload["dependencies"]["diagnostics"]
    item = opener(exports["hostile"])
    rendered = {"label-group": set(), "label-state": set(), "label-trust": set(), "label-form": set()}
    glyphs: set[str] = set()
    for node in payload["nodes"]:
        for direction in _DIRS:
            page = _dep_pick(item, node["id"], direction, "all")
            if node["type"] == "intent":
                _open_record(page)
            for cls in rendered:
                rendered[cls] |= set(page.eval_on_selector_all(f".{cls}", "e => e.map(x => x.textContent)"))
            glyphs |= {g for g, _, _ in _marks(page, "body")}
    assert rendered["label-group"] <= set(_GROUPS)
    assert rendered["label-state"] <= set(_STATES)
    assert rendered["label-trust"] <= set(_TRUST)
    assert rendered["label-form"] <= set(_FORMS)
    assert {"outside_scope", "unparseable", "cycle"} <= rendered["label-state"]
    assert glyphs <= set("●◆◇✕△✓")
    # Values that copy a glyph, a state label or the phrase never become a mark, chip or line.
    page = _dep_pick(item, "intent:hostile-child", "prerequisites", "1")
    part = _detail_part(page, "Dependencies")
    codes = part.locator("code.value").all_inner_texts()
    assert "✕ waits for pointer_checked" in codes and "dangling" in codes
    assert part.locator(".dep-line").count() == 2  # child waits for root, root waits for child
    states = part.locator(".label-state").all_inner_texts()
    assert states[-1] == "cycle" and set(states[:-1]) == {"unparseable"} and len(states) == 7
    assert "pointer_checked" not in part.locator(".label-trust, .label-state, .label-form").all_inner_texts()
    broken_marks = [m for m in _marks(page, "#detail-body section.part") if m[0] == "✕"]
    assert len(broken_marks) == len(states) and all(m[1] == "Broken" and m[2] == "true" for m in broken_marks)
    # No link target anywhere but an in-page fragment, and no markup built from a value.
    for href in page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
        assert href.startswith("#") or href.startswith("https://github.com/")
    assert page.locator("#detail-body script, #detail-body img, #detail-body svg").count() == 0
    assert item.errors == [] and set(item.requests) == {item.url}


def _fragment(page: Page) -> dict[str, str]:
    return dict(urllib.parse.parse_qsl(page.evaluate("location.hash").lstrip("#")))


def test_vi_3004_fragment_reload_and_history(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["dependency"])
    page = _dep_pick(item, "intent:charlie")
    assert "dir" not in _fragment(page) and "steps" not in _fragment(page)
    start = _history_length(page)
    page.select_option("#dep-dir", "both")
    assert _fragment(page)["dir"] == "both" and "steps" not in _fragment(page)
    page.select_option("#dep-steps", "all")
    assert _fragment(page)["steps"] == "all"
    assert _history_length(page) == start  # a change adds no history entry
    shown = _page_part(page)["lines"]
    assert ["intent:bravo", "intent:charlie"] in shown and ["intent:charlie", "capability:root-b"] in shown
    page.reload()
    assert page.locator("#dep-dir").input_value() == "both" and page.locator("#dep-steps").input_value() == "all"
    assert _page_part(page)["lines"] == shown
    # Choosing the defaults drops the keys.
    page.select_option("#dep-dir", "prerequisites")
    page.select_option("#dep-steps", "1")
    assert "dir" not in _fragment(page) and "steps" not in _fragment(page)
    assert _history_length(page) == start
    # Following a link picks that intent with a history entry and keeps the choices; Back returns.
    page.select_option("#dep-dir", "both")
    page.select_option("#dep-steps", "2")
    before = _history_length(page)
    page.locator("#detail-body section.part", has=page.locator("h3", has_text="Dependencies")).locator("a[data-node='intent:bravo']").first.click()
    _wait_heading(page, "Bravo")
    assert _history_length(page) == before + 1
    assert _fragment(page)["node"] == "intent:bravo" and _fragment(page)["dir"] == "both" and _fragment(page)["steps"] == "2"
    assert page.locator("#dep-dir").input_value() == "both" and page.locator("#dep-steps").input_value() == "2"
    page.go_back()
    _wait_heading(page, "Charlie")
    assert _fragment(page)["node"] == "intent:charlie" and page.locator("#dep-dir").input_value() == "both"
    # A change keeps the control in use focused.
    page.focus("#dep-dir")
    page.keyboard.press("ArrowUp")
    assert page.evaluate("document.activeElement.id") == "dep-dir"


@pytest.mark.parametrize(
    "bad",
    ["steps=-1", "steps=1e12", "steps=abc", "steps=0", "steps=99999999999999999999", "dir=__proto__", "dir=constructor", "dir=<b>x</b>"],
)
def test_vi_3004_invalid_fragment_values_read_as_defaults(opener: Any, exports: dict[str, pathlib.Path], bad: str) -> None:
    item = opener(exports["dependency"], fragment=f"#q=browse&node=intent%3Aalpha&{bad}")
    page = item.page
    page.wait_for_selector("#dep-dir")
    assert page.locator("#dep-dir").input_value() == "prerequisites" and page.locator("#dep-steps").input_value() == "1"
    value = bad.split("=", 1)[1]
    if not value.lstrip("-").isdigit() or len(value) > 3:
        assert value not in page.inner_text("body")
    assert bad not in page.inner_text("body")
    assert _page_part(page)["lines"] == [["intent:alpha", "intent:bravo"]]
    # The next fragment the page writes drops the invalid value.
    page.select_option("#dep-dir", "dependents")
    assert bad.split("=", 1)[0] not in _fragment(page) or _fragment(page)[bad.split("=", 1)[0]] != value
    assert bad not in page.evaluate("location.hash")
    other = opener(exports["dependency"], fragment=f"#q=browse&node=intent%3Aalpha&{bad}")
    other.page.wait_for_selector("#dep-dir")
    other.page.locator("a[data-node='intent:bravo']").first.click()
    other.page.wait_for_function("() => location.hash.includes('bravo')")
    assert bad not in other.page.evaluate("location.hash")
    assert other.errors == [] and item.errors == []


def test_vi_3002_edge_lines_wrap_their_names_at_320_px(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["dependency_from"], width=320, height=700)
    page = _dep_pick(item, "intent:india", "both", "all")
    assert _page_part(page)["cycles"]
    scroll, client = _no_overflow(page)
    assert scroll <= client
    lines = page.locator("#detail-body li.dep-line")
    assert lines.count() == 3
    for box in lines.evaluate_all("els => els.map(e => e.getBoundingClientRect().right - document.documentElement.clientWidth)"):
        assert box <= 0.5


# ---------------------------------------------------------------------------
# Keyboard, width, theme and inert content for the "Dependencies" part
# ---------------------------------------------------------------------------


def _back_to(page: Page, node: str) -> None:
    """Browser back until the fragment names *node* again."""
    for _ in range(8):
        page.go_back()
        page.wait_for_timeout(50)
        if _fragment(page).get("node") == node:
            return
    raise AssertionError(f"browser back never returned to {node}")


def _open_part_by_keyboard(item: Opened, node: str) -> Page:
    """Pick *node* from the browse list with the keyboard alone."""
    page = item.page
    page.evaluate("document.body.focus()")
    _tab_to(page, "e.dataset.q === 'browse'")
    page.keyboard.press("Enter")
    _tab_to(page, "e.id === 'search'")
    page.keyboard.type(node.split(":")[1])
    page.wait_for_selector(f"#list a.row-link[data-node='{node}']")
    _tab_to(page, f"e.matches('#list a.row-link') && e.dataset.node === '{node}'")
    page.keyboard.press("Enter")
    page.wait_for_selector("#detail-body #dep-dir")
    return page


def test_vi_4001_keyboard_alone_drives_the_part(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["dependency"])
    page = _open_part_by_keyboard(item, "intent:alpha")
    _tab_to(page, "e.id === 'dep-dir'")
    page.keyboard.type("b")  # type-ahead picks "Both" without opening the native popup
    page.wait_for_function("() => document.getElementById('dep-dir').value === 'both'")
    page.wait_for_function("() => document.activeElement.id === 'dep-dir'")
    _tab_to(page, "e.id === 'dep-steps'")
    page.keyboard.type("a")
    page.wait_for_function("() => document.getElementById('dep-steps').value === 'all'")
    page.wait_for_function("() => document.activeElement.id === 'dep-steps'")
    assert _fragment(page).get("dir") == "both" and _fragment(page).get("steps") == "all"
    expect = _DepModel(payload_of(exports["dependency"])).expect("intent:alpha", "both", _depth(payload_of(exports["dependency"]), "all"))
    assert _page_part(page)["lines"] == expect["lines"]
    chosen = _fragment(page)

    def follow(selector: str) -> str:
        """Tab to the first matching link that is not the current intent and press Enter on it."""
        target = page.evaluate(
            f"""() => {{ const a = [...document.querySelectorAll('#detail-body {selector}')]
              .find(x => x.dataset.node !== 'intent:alpha'); return a ? a.dataset.node : null; }}"""
        )
        assert target, selector
        _tab_to(page, f"e.matches('#detail-body {selector}') && e.dataset.node === '{target}'")
        page.keyboard.press("Enter")
        _wait_focus_id(page, "detail-heading")
        assert _fragment(page)["node"] == target
        return str(target)

    prerequisite = follow("section.part .dep-prereq a[data-node]")
    assert prerequisite != "intent:alpha"
    _back_to(page, "intent:alpha")
    assert _fragment(page) == chosen
    assert page.locator("#dep-dir").input_value() == "both" and page.locator("#dep-steps").input_value() == "all"
    dependent = follow("section.part .dep-waiting a[data-node]")
    assert dependent != "intent:alpha"
    _back_to(page, "intent:alpha")
    assert _fragment(page) == chosen
    assert page.locator("#dep-dir").input_value() == "both" and page.locator("#dep-steps").input_value() == "all"
    assert _page_part(page)["lines"] == expect["lines"]
    # No trap: Tab leaves the part forwards and Shift+Tab leaves it backwards.
    page.evaluate("document.getElementById('dep-dir').focus()")
    inside = "document.activeElement.closest('section.part') && document.activeElement.closest('section.part').querySelector('#dep-dir')"
    left = False
    for _ in range(80):
        page.keyboard.press("Tab")
        if not page.evaluate(f"!!({inside})"):
            left = True
            break
    assert left
    page.evaluate("document.getElementById('dep-dir').focus()")
    left = False
    for _ in range(80):
        page.keyboard.press("Shift+Tab")
        if not page.evaluate(f"!!({inside})"):
            left = True
            break
    assert left
    assert page.evaluate("document.activeElement !== document.body")


_CYCLE_NODE = "intent:india"


def _cycle_state(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> Page:
    item = opener(exports["dependency"], width=width, height=700, scheme=scheme)
    page = _dep_pick(item, _CYCLE_NODE, "both", "all")
    assert page.locator("#detail-body .dep-diag .dep-members").count() >= 1  # the part shows a cycle
    _open_record(page)
    page.locator("#key summary").click() if page.locator("#key summary").is_visible() else None
    return page


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_ID)
def test_vi_4001_part_across_width_and_theme(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    page = _cycle_state(opener, exports, width, scheme)
    scroll, client = _no_overflow(page)
    assert scroll <= client, (width, scroll, client)
    stops = _sweep(page)
    assert len(stops) > 10
    for stop in stops:
        assert stop["hit"] and stop["visible"], stop
        assert stop["outlineStyle"] == "solid" and stop["outlineWidth"] >= 2, stop
        assert _ratio(_rgb(stop["outlineColor"]), _rgb(stop["bg"])) >= 3, stop
    small = page.evaluate(
        """() => Array.from(document.querySelectorAll('a[href], button, input, select, summary'))
          .map(e => [e, e.getBoundingClientRect()])
          .filter(([e, r]) => r.width > 0 && !e.classList.contains('skip') && (r.width < 24 || r.height < 24))
          .map(([e, r]) => e.outerHTML.slice(0, 80) + ' ' + r.width + 'x' + r.height)"""
    )
    assert small == []
    low = [r for r in _contrast_report(page) if r[1] < 4.5]
    assert not low, low[:5]
    # The part's own controls and lines are inside the viewport width.
    right = page.evaluate(
        "Math.max(...[...document.querySelectorAll('#detail-body section.part *')].map(e => e.getBoundingClientRect().right))"
    )
    assert right <= width + 0.5


# 2000 to 2240 CSS px keep the part's result between the 40rem line breakpoint and the 51rem problem-row
# breakpoint, so problem rows stack; 2440 and 2480 put it just above 51rem, where the problem-row columns
# are tightest; 2560 is the widest matrix width.
@pytest.mark.parametrize("width", [320, 1280, 1680, 2000, 2080, 2160, 2240, 2440, 2480, 2560])
@pytest.mark.parametrize("corpus", ["dependency_long", "dependency"])
def test_vi_4001_long_source_titles_keep_values_readable(
    opener: Any, exports: dict[str, pathlib.Path], width: int, corpus: str,
) -> None:
    """A source title, long or short, never squeezes a problem row's cells into each other (AC-0010, AC-0019)."""
    item = opener(exports[corpus], width=width, height=900)
    page = _dep_pick(item, "intent:golf", "both", "1")
    assert page.locator("#detail-body li.dep-diag").count() >= 19
    detail = page.evaluate("(() => { const d = document.querySelector('.detail'); return [d.scrollWidth, d.clientWidth]; })()")
    assert detail[0] <= detail[1], detail
    scroll, client = _no_overflow(page)
    assert scroll <= client, (scroll, client)
    # A squeezed value breaks one character per line; a readable one takes at most three lines.
    tall = page.evaluate(
        """() => [...document.querySelectorAll('#detail-body li.dep-diag code.value')]
          .map(c => [c.textContent, c.getBoundingClientRect().height, parseFloat(getComputedStyle(c).lineHeight) || 20])
          .filter(([t, h, lh]) => h > 3.5 * lh)"""
    )
    assert tall == [], tall[:3]
    # Each cell keeps its children inside it: no name or state mark runs into the value beside it.
    clash = page.evaluate(
        """() => [...document.querySelectorAll('#detail-body li.dep-diag')].flatMap(li => {
          const src = li.querySelector('.dep-source'), val = li.querySelector('code.value');
          if (!src || !val) { return []; }
          const s = src.getBoundingClientRect(), v = val.getBoundingClientRect();
          const right = Math.max(...[...src.querySelectorAll('*')].map(e => e.getBoundingClientRect().right), s.right);
          const sameRow = v.top < s.bottom - 1 && s.top < v.bottom - 1;
          const lines = s.height / (parseFloat(getComputedStyle(src).lineHeight) || 24);
          return (right > s.right + 0.5 || (sameRow && right > v.left + 0.5) || lines > 6)
            ? [[val.textContent, Math.round(s.width), Math.round(right - s.right), Math.round(s.height)]] : [];
        })"""
    )
    assert clash == [], clash[:3]


_BANNED_TAGS = {"img", "svg", "iframe", "object", "embed", "link", "style", "base", "form", "math", "video", "audio", "canvas", "template", "textarea", "frame"}


def test_vi_4002_hostile_values_stay_inert(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    path = exports["hostile"]
    payload = payload_of(path)
    item = opener(path)
    page = item.page
    values = {d["value"] for d in payload["dependencies"]["diagnostics"] if "value" in d}
    for record in payload["records"].values():
        for key in ("related_written_here", "related_written_elsewhere"):
            values |= {e["value"] for e in record[key] if "value" in e}
        if record.get("parent_edge"):
            values.add(record["parent_edge"]["value"])
    escaped = {nav._escape_display(v) for v in values}
    assert len(values) >= 8 and any("waits for" in v for v in values)
    shown = ""
    seen_values: set[str] = set()
    for node in payload["nodes"]:
        for direction in _DIRS:
            page = _dep_pick(item, node["id"], direction, "all")
            if node["type"] == "intent":
                _open_record(page)
            shown += "".join(page.evaluate(_TEXT_NODES))
            # Every dependency value (the part and the record groups) shows only inside its own code element.
            stray = page.evaluate(
                """escaped => { const out = []; const hit = [];
                  for (const root of document.querySelectorAll('#detail-body section.part, #detail-body section.group')) {
                    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
                    while (w.nextNode()) { const n = w.currentNode; const t = n.textContent.trim();
                      if (escaped.includes(t)) { hit.push(t); if (!n.parentElement.closest('code')) out.push(t); } } }
                  return { out, hit }; }""",
                sorted(escaped),
            )
            assert stray["out"] == [], stray
            seen_values |= set(stray["hit"])
            # Marks and labels never carry a value.
            marks = {t for g, w, _ in _marks(page, "body") for t in (g, w)}
            assert not marks & escaped, marks & escaped
            for cls, closed in (("label-state", _STATES), ("label-trust", _TRUST), ("label-form", _FORMS), ("label-group", _GROUPS)):
                assert set(page.eval_on_selector_all(f"#detail-body .{cls}", "e => e.map(x => x.textContent)")) <= set(closed)
            tags = set(page.evaluate("[...document.querySelectorAll('body *')].map(e => e.tagName.toLowerCase())"))
            assert not tags & _BANNED_TAGS, tags & _BANNED_TAGS
            assert page.locator("script").count() == 2  # the data block and the view script, as exported
            bad_attrs = page.evaluate(
                """needles => { const out = [];
                  for (const e of document.querySelectorAll('body *')) for (const a of e.attributes) {
                    const inPage = a.name === 'href' && a.value.startsWith('#');
                    if (a.name.startsWith('on') || a.name === 'style' || a.name === 'srcdoc') out.push(a.name);
                    else if (e.tagName === 'OPTION') continue;  // the shared filter controls set their own values
                    else if (!inPage && needles.some(n => a.value.includes(n))) out.push(a.name + '=' + a.value);
                  } return out; }""",
                sorted({v for v in values if re.search(r"[<>]|alert\(|javascript:", v)} | {"alert(1)", "javascript:", "onerror", "<img", "<svg", "</script"}),
            )
            assert bad_attrs == [], bad_attrs
            for href in page.eval_on_selector_all("a[href]", "els => els.map(e => e.getAttribute('href'))"):
                assert href.startswith("#") or href.startswith("https://github.com/"), href
    assert _unsafe_present(shown) == []
    assert any("waits for" in v for v in seen_values) and any(v.startswith("<img") for v in seen_values)
    assert set(item.requests) == {item.url}, item.requests
    assert page.evaluate("window.__csp") == [] and item.errors == []
    html = path.read_text(encoding="utf-8")
    meta = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', html)
    builder = nav._load_view_mod()
    parts = {p.name: p for p in (_SCRIPTS / "view_src").glob("*.js")}
    script = builder._SCRIPT_PROLOGUE + "".join(
        parts[name].read_text(encoding="utf-8") for name in builder._SCRIPT_PARTS
    ) + builder._SCRIPT_EPILOGUE
    style = (_SCRIPTS / "view_assets" / "view-base.css").read_text(encoding="utf-8") + "\n" + (_SCRIPTS / "view_assets" / "view.css").read_text(encoding="utf-8")

    def digest(text: str) -> str:
        return base64.b64encode(hashlib.sha256(text.encode("utf-8")).digest()).decode("ascii")

    assert meta is not None and meta.group(1) == (
        f"default-src 'none'; script-src 'sha256-{digest(script)}'; style-src 'sha256-{digest(style)}'; "
        "img-src 'none'; base-uri 'none'; form-action 'none'"
    )


# ---------------------------------------------------------------------------
# Refined style: motion, elevation, edges and colour, read from computed style and geometry
# ---------------------------------------------------------------------------

# The colour an element sits on: its own background-color, or the nearest ancestor's with a non-zero alpha,
# composited over the layers beneath it until one is opaque.
_BACKDROP = """(el) => {
  const parse = (c) => { const m = c.match(/[\\d.]+/g).map(Number); return m.length === 3 ? [...m, 1] : m; };
  const layers = [];
  for (let p = el; p; p = p.parentElement) {
    const c = parse(getComputedStyle(p).backgroundColor);
    if (c[3] > 0) { layers.push(c); if (c[3] >= 1) break; }
  }
  let out = [255, 255, 255];
  for (const c of layers.reverse()) out = out.map((v, i) => c[i] * c[3] + v * (1 - c[3]));
  return out;
}"""


def _over(css: str, backdrop: tuple[float, float, float]) -> tuple[float, float, float]:
    """An ``rgb()`` or ``rgba()`` colour composited over an opaque backdrop."""
    nums = [float(n) for n in re.findall(r"[\d.]+", css)]
    alpha = nums[3] if len(nums) > 3 else 1.0
    return tuple(c * alpha + b * (1 - alpha) for c, b in zip(nums[:3], backdrop, strict=True))  # type: ignore[return-value]


def _backdrop(page: Page, selector: str, index: int = 0) -> tuple[float, float, float]:
    found = page.locator(selector).nth(index).evaluate(_BACKDROP)
    return float(found[0]), float(found[1]), float(found[2])


def _inset_bars(page: Page, selector: str) -> list[list[tuple[float, str]]]:
    """Per element, its inset shadows as (bar width, colour): the x offset plus the spread."""
    raw = page.eval_on_selector_all(selector, "els => els.map(e => getComputedStyle(e).boxShadow)")
    bars: list[list[tuple[float, str]]] = []
    for shadow in raw:
        found: list[tuple[float, str]] = []
        for part in re.split(r",\s*(?![^(]*\))", shadow):
            if "inset" not in part:
                continue
            colour = re.search(r"rgba?\([^)]*\)", part)
            lengths = [float(n) for n in re.findall(r"(-?[\d.]+)px", part)]
            assert colour and len(lengths) >= 2, part
            spread = lengths[3] if len(lengths) > 3 else 0.0
            found.append((lengths[0] + spread, colour.group(0)))
        bars.append(found)
    return bars


def test_reduced_motion_is_still(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"], reduced_motion="reduce")
    page = _pick(item, "intent:bravo-feat")
    moving = page.evaluate(
        """() => [...document.querySelectorAll('*')].flatMap((e) => {
          const cs = getComputedStyle(e);
          const bad = [];
          for (const prop of ['transitionDuration', 'animationDuration']) {
            if (cs[prop].split(',').some((d) => d.trim() !== '0s')) bad.push(prop + '=' + cs[prop]);
          }
          if (cs.animationName !== 'none') bad.push('animationName=' + cs.animationName);
          return bad.length ? [e.tagName + '.' + e.className + ' ' + bad.join(' ')] : [];
        })"""
    )
    assert moving == [], moving[:5]
    assert page.evaluate("document.querySelectorAll('*').length") > 100  # the detail has rendered


def test_rows_transition_when_motion_allowed(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"], reduced_motion="no-preference")
    item.go(_frag(q="browse"))
    item.page.wait_for_selector("#list a.row-link")
    durations = item.page.eval_on_selector("#list a.row-link", "e => getComputedStyle(e).transitionDuration")
    assert any(float(d.strip().removesuffix("s")) > 0 for d in durations.split(",")), durations


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_ID)
def test_zones_are_raised(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    for name, picked, page in _matrix_states(opener, exports, width, scheme):
        for zone in (".worklist", ".detail"):
            radius, shadow = page.eval_on_selector(
                zone, "e => { const cs = getComputedStyle(e); return [cs.borderTopLeftRadius, cs.boxShadow]; }"
            )
            assert radius not in ("0px", ""), (name, picked, zone, radius)
            assert shadow != "none", (name, picked, zone)


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_ID)
def test_rows_are_flat(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    seen = 0
    for name, picked, page in _matrix_states(opener, exports, width, scheme):
        shadows = page.eval_on_selector_all("a.row-link", "els => els.map(e => getComputedStyle(e).boxShadow)")
        seen += len(shadows)
        for shadow in shadows:
            parts = [] if shadow == "none" else re.split(r",\s*(?![^(]*\))", shadow)
            assert all("inset" in part for part in parts), (name, picked, shadow)
    assert seen > 10


@pytest.mark.parametrize(("width", "scheme"), _MATRIX, ids=_MATRIX_ID)
def test_control_borders_clear_3_to_1(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    kinds: set[str] = set()
    for name, picked, page in _matrix_states(opener, exports, width, scheme):
        controls = page.evaluate(
            """(src) => {
              const backdrop = eval(src);
              return [...document.querySelectorAll('#search, select, button')].flatMap((e) => {
                const cs = getComputedStyle(e);
                const side = ['Top', 'Right', 'Bottom', 'Left'].find((s) => parseFloat(cs['border' + s + 'Width']) > 0);
                if (!side) return [];
                return [{ tag: e.tagName.toLowerCase(), id: e.id, border: cs['border' + side + 'Color'], bg: backdrop(e) }];
              });
            }""",
            _BACKDROP,
        )
        for control in controls:
            bg = (float(control["bg"][0]), float(control["bg"][1]), float(control["bg"][2]))
            ratio = _ratio(_over(control["border"], bg), bg)
            kinds.update((control["id"], control["tag"]))
            assert ratio >= 3, (name, picked, control, ratio)
    assert {"search", "select"} <= kinds, kinds


@pytest.mark.parametrize("scheme", _SCHEMES)
def test_search_placeholder(opener: Any, exports: dict[str, pathlib.Path], scheme: str) -> None:
    page = opener(exports["mixed"], scheme=scheme).page
    field = page.locator("#search")
    assert field.get_attribute("placeholder") == "Search names and ids"
    assert page.get_by_role("searchbox", name="Search names and ids").count() == 1
    colour, opacity = field.evaluate(
        "e => { const cs = getComputedStyle(e, '::placeholder'); return [cs.color, cs.opacity]; }"
    )
    assert opacity == "1", opacity
    bg = _backdrop(page, "#search")
    assert _ratio(_over(colour, bg), bg) >= 4.5, (colour, bg)


def test_state_line_reads_word_then_type(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    model = Model(payload_of(exports["mixed"]))
    checked: set[str] = set()
    for node_id in model.nodes:
        page = _pick(item, node_id)
        glyph, word, _hidden = _marks(page, ".state-line")[0]
        full = page.locator(".state-line").evaluate("e => e.textContent")
        line = " ".join(full.replace(glyph, "", 1).split())
        found = re.fullmatch(rf"{re.escape(word)} (Intent|Brief|Spec)(?: .*)?", line)
        assert found, (node_id, line)
        assert not re.search(r"[·|/:,-]\s*" + found.group(1), line), line
        checked.add(found.group(1))
    assert checked == {"Intent", "Brief", "Spec"}, checked


def _pick_first_broken(item: Opened) -> Page:
    """Open the broken question and pick the first record it lists; it has broken entries to show."""
    item.go(_frag(q="broken"))
    item.page.wait_for_selector("#list a.row-link")
    node = item.page.locator("#list a.row-link").first.get_attribute("data-node")
    page = _pick(item, node or "", "broken")
    assert page.locator(".has-broken > ul > li.edge").count() >= 1
    return page


@pytest.mark.parametrize("scheme", _SCHEMES)
def test_broken_entries_are_tinted(opener: Any, exports: dict[str, pathlib.Path], scheme: str) -> None:
    page = _pick_first_broken(opener(exports["hostile"], scheme=scheme))
    zone = _backdrop(page, ".detail")
    count = page.locator(".has-broken > ul > li.edge").count()
    tints = [_backdrop(page, ".has-broken > ul > li.edge", i) for i in range(count)]
    assert tints and all(t != zone for t in tints), (zone, tints)


@pytest.mark.parametrize("scheme", _SCHEMES)
def test_broken_entries_have_a_bar(opener: Any, exports: dict[str, pathlib.Path], scheme: str) -> None:
    page = _pick_first_broken(opener(exports["hostile"], scheme=scheme))
    zone = _backdrop(page, ".detail")
    bars = page.eval_on_selector_all(
        ".has-broken > ul > li.edge",
        "els => els.map(e => { const cs = getComputedStyle(e); return [parseFloat(cs.borderLeftWidth), cs.borderLeftStyle, cs.borderLeftColor]; })",
    )
    assert bars
    for width, style, colour in bars:
        assert width >= 3 and style != "none", (width, style)
        assert _ratio(_over(colour, zone), zone) >= 3, (colour, zone)


@pytest.mark.parametrize("scheme", _SCHEMES)
def test_current_question_has_a_bar(opener: Any, exports: dict[str, pathlib.Path], scheme: str) -> None:
    page = opener(exports["mixed"], scheme=scheme).page
    links = "nav a[data-q]"
    bars = _inset_bars(page, links)
    current = page.eval_on_selector_all(links, "els => els.map(e => e.getAttribute('aria-current') === 'page')")
    assert current.count(True) == 1
    for index, (is_current, found) in enumerate(zip(current, bars, strict=True)):
        if not is_current:
            assert found == [], (index, found)
            continue
        assert len(found) == 1 and found[0][0] >= 3, found
        bg = _backdrop(page, links, index)
        assert _ratio(_over(found[0][1], bg), bg) >= 3, (found, bg)


_SPILL_WIDTHS = [320, 1280, 1440, 1500, 1680, 2560]
_SPILL = """() => {
  const out = [];
  for (const zone of document.querySelectorAll('.worklist, .detail')) {
    const z = zone.getBoundingClientRect();
    if (!zone.getClientRects().length) continue;  // the zone is not shown in this state
    for (const e of zone.querySelectorAll('*')) {
      if (!e.getClientRects().length) continue;
      const r = e.getBoundingClientRect();
      if (r.left < z.left - 1 || r.right > z.right + 1) {
        out.push(zone.className + ' > ' + e.tagName.toLowerCase() + '.' + e.className + ' ' + r.left + '..' + r.right + ' in ' + z.left + '..' + z.right);
      }
    }
  }
  return out;
}"""


@pytest.mark.parametrize("scheme", _SCHEMES)
@pytest.mark.parametrize("width", _SPILL_WIDTHS)
def test_nothing_spills_out_of_a_zone(opener: Any, exports: dict[str, pathlib.Path], width: int, scheme: str) -> None:
    picks = 0
    for name in _MATRIX_EXPORTS:
        page = opener(exports[name], width=width, height=700, scheme=scheme).page
        for question in _QUESTIONS:
            page.locator(f'nav a[data-q="{question}"]').click()
            page.wait_for_selector(f'nav a[data-q="{question}"][aria-current="page"]')
            states = ["list"]
            if page.locator("#list a.row-link").count():
                states.append("picked")
            for state in states:
                if state == "picked":
                    page.locator("#list a.row-link").first.click()
                    page.wait_for_function("() => document.getElementById('main').hasAttribute('data-picked')")
                    page.wait_for_selector("#detail-body .state-line")
                    picks += 1
                spill = page.evaluate(_SPILL)
                assert spill == [], (name, question, state, spill[:5])
                scroll = page.evaluate("document.documentElement.scrollWidth")
                assert scroll <= width, (name, question, state, scroll)
                if state == "picked" and width < 640:
                    page.locator(".back-link").first.click()  # back to the list for the next destination
                    page.wait_for_function("() => !document.getElementById('main').hasAttribute('data-picked')")
    assert picks >= 6, picks


# ---------------------------------------------------------------------------
# The roadmap fixture: hand-stated bands against the payload reading
# ---------------------------------------------------------------------------


def _readme_tables() -> dict[str, list[list[str]]]:
    """The fixture README's tables as cell lists, keyed by the heading above each."""
    (path,) = _FIXTURES.glob("roadmap/README.md")
    found: dict[str, list[list[str]]] = {}
    heading = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
        elif line.startswith("| ") and not line.startswith("| ---") and not line.startswith("| Node id"):
            found.setdefault(heading, []).append([c.strip().strip("`") for c in line.strip("|").split("|")])
    return found


def _placements(found: dict[str, Any]) -> dict[str, str]:
    """Each capability's and strategy's placement, worded as the README states it."""
    out: dict[str, str] = {}

    def walk(items: list[dict[str, Any]], above: str | None, heading: str) -> None:
        for item in items:
            out[item["id"]] = f"nested under {above}" if above else f'section "{heading}"'
            walk(item["children"], item["id"], heading)

    for section in found["sections"]:
        if section["strategy"]:
            out[section["strategy"]] = f'heads section "{section["heading"]}"'
        walk(section["capabilities"], None, section["heading"])
    return out


def test_roadmap_fixture_matches_hand_stated_bands(exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    found = _roadmap_expectations(payload)
    tables = _readme_tables()

    stated_bands = {n: band for n, band, _ in tables["Records"]}
    assert len(stated_bands) == len(tables["Records"]) == len(payload["nodes"])
    assert found["bands"] == stated_bands
    assert set(stated_bands.values()) == set(_BANDS)

    placements = _placements(found)
    assert {n: place for n, _, place in tables["Records"] if place != "-"} == placements
    assert [s["heading"] for s in found["sections"]] == [
        "Atlas direction",
        "Boreal direction",
        _NO_STRATEGY,
    ]

    def stated(row: list[str]) -> tuple[Any, ...]:
        cells = None if row[6] == "no bar" else tuple(int(c) for c in row[6].split("/"))
        return (*map(int, row[1:5]), None if row[5] == "-" else int(row[5].rstrip("%")), cells)

    def read(node: str) -> tuple[Any, ...]:
        prog = found["progress"][node]
        counts = prog["counts"]
        cells = None if prog["nothing_beneath"] else prog["cells"]
        return (*(counts[b] for b in _BANDS), prog["share"], cells)

    assert {r[0] for r in tables["Progress"]} == set(found["progress"])
    for row in tables["Progress"]:
        assert read(row[0]) == stated(row), row[0]
        assert found["progress"][row[0]]["nothing_beneath"] == (row[6] == "no bar")

    model = Model(payload)
    stated_roots = dict(tables["Tree roots"])
    assert found["roots"] == model.by_name(stated_roots)
    for node, place in stated_roots.items():
        assert place == ("root, intents beneath" if model.records[node]["children"] else "root, nothing beneath")


def test_roadmap_tree_roots_take_the_first_loop_member_when_no_edge_is_refused(
    exports: dict[str, pathlib.Path],
) -> None:
    """A payload whose loop has no refused edge still roots each intent once, by name order."""
    payload = payload_of(exports["roadmap"])
    alpha = payload["records"]["intent:loop-alpha"]
    gamma = payload["records"]["intent:loop-gamma"]
    alpha["parent_edge"] = {**alpha["parent_edge"], "to": "intent:loop-gamma"}
    del alpha["parent_edge"]["state"]
    gamma["children"] = ["intent:loop-alpha"]
    roots = _roadmap_expectations(payload)["roots"]
    assert "intent:loop-alpha" in roots and "intent:acorn-tail" not in roots
    assert len([r for r in roots if r.startswith("intent:loop-")]) == 1


# ---------------------------------------------------------------------------
# The roadmap question: the page against the payload reading
# ---------------------------------------------------------------------------

_READ_ROADMAP = """() => {
  const prog = (p) => p === null ? null : {
    words: Array.from(p.querySelectorAll('.rm-w')).map((e) => e.textContent),
    pct: p.querySelector('.rm-pct') ? p.querySelector('.rm-pct').textContent : null,
    cells: Array.from(p.querySelectorAll('.rm-cell')).map((c) => c.className.replace('rm-cell ', '')),
    barHidden: p.querySelector('.rm-bar') ? p.querySelector('.rm-bar').getAttribute('aria-hidden') : null,
    none: p.querySelector('.rm-none') ? p.querySelector('.rm-none').textContent : null,
    unknown: p.querySelector('.rm-unknown') ? p.querySelector('.rm-unknown').textContent : null,
  };
  const row = (li) => {
    const a = li.firstElementChild;
    return {
      id: a.dataset.node,
      linkFirst: a.matches('a.row-link'),
      name: a.querySelector('.c-name').textContent,
      parts: Array.from(a.children).map((c) => c.className),
      mark: a.querySelector('.c-state .mark-w').textContent,
      progress: prog(a.querySelector(':scope > .rm-progress')),
      children: Array.from(li.querySelectorAll(':scope > ul > li')).map(row),
      subLists: li.querySelectorAll(':scope > ul').length,
    };
  };
  return Array.from(document.querySelectorAll('#list > section.rm-section')).map((s) => ({
    heading: s.querySelector('.rm-title').textContent,
    progress: prog(s.querySelector('.rm-head > .rm-progress')),
    rows: Array.from(s.querySelectorAll(':scope > ul > li')).map(row),
  }));
}"""
_UNKNOWN_PROGRESS = "Progress unknown: delivery mapping incomplete."
_CELL_CLASS = ("rm-delivered", "rm-inprogress", "rm-notstarted", "rm-empty")


def _read_roadmap(item: Opened) -> list[dict[str, Any]]:
    _choose(item, "roadmap")
    item.page.wait_for_selector("#list section.rm-section")
    return item.page.evaluate(_READ_ROADMAP)  # type: ignore[no-any-return]


def _expected_progress(found: dict[str, Any], node: str) -> dict[str, Any]:
    """What the page must show for *node*, worded by AC-0013 to AC-0017 and AC-0048."""
    prog = found["progress"][node]
    if prog["nothing_beneath"]:
        return {"words": [], "pct": None, "cells": [], "none": "Nothing beneath yet", "unknown": None}
    counts = prog["counts"]
    words = [f"{counts['delivered']} delivered"]
    words += [f"{counts[b]} {b}" for b in ("in progress", "not started", "stopped") if counts[b]]
    cells = [c for cls, n in zip(_CELL_CLASS, prog["cells"], strict=True) for c in [cls] * n]
    current = counts["delivered"] + counts["in progress"] + counts["not started"]
    pct = None if prog["share"] is None else f"{prog['share']}% delivered of {current} {'item' if current == 1 else 'items'}"
    return {"words": words, "pct": pct, "cells": cells, "none": None, "unknown": None}


def _shown_progress(prog: dict[str, Any] | None) -> dict[str, Any] | None:
    if prog is None:
        return None
    return {k: prog[k] for k in ("words", "pct", "cells", "none", "unknown")}


def _walk_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for row in rows for r in (row, *_walk_rows(row["children"]))]


def _shape(rows: list[dict[str, Any]]) -> list[Any]:
    return [[r["id"], _shape(r["children"])] for r in rows]


def test_roadmap_sections_and_nesting(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    found = _roadmap_expectations(payload)
    model = Model(payload)
    item = opener(exports["roadmap"])
    page = item.page
    sections = _read_roadmap(item)
    assert [s["heading"] for s in sections] == [s["heading"] for s in found["sections"]]
    assert sections[-1]["heading"] == _NO_STRATEGY
    for shown, want in zip(sections, found["sections"], strict=True):
        assert _shape(shown["rows"]) == _expected_shape(want["capabilities"])
    every = [r["id"] for s in sections for r in _walk_rows(s["rows"])]
    caps = [i for i, r in model.records.items() if r["level"] == "capability"]
    assert sorted(every) == sorted(caps) and len(every) == len(set(every))
    for s in sections:
        for r in _walk_rows(s["rows"]):
            assert r["linkFirst"] and r["name"] == model.display(r["id"])
            assert r["subLists"] == (1 if r["children"] else 0)
    assert _text(page, "#list-sort") == "By strategy, then name"
    # Picking a nested row shows its detail as other rows do.
    nested = "capability:anchor-sub-cap"
    page.locator(f'#list a.row-link[data-node="{nested}"]').click()
    _wait_heading(page, model.display(nested))
    assert page.locator(f'#list a.row-link[data-node="{nested}"][aria-current="true"]').count() == 1


def _expected_shape(caps: list[dict[str, Any]]) -> list[Any]:
    return [[c["id"], _expected_shape(c["children"])] for c in caps]


def test_roadmap_progress_text(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    found = _roadmap_expectations(payload)
    model = Model(payload)
    sections = _read_roadmap(opener(exports["roadmap"]))
    rows = {r["id"]: r for s in sections for r in _walk_rows(s["rows"])}
    assert rows
    for node, row in rows.items():
        assert row["parts"] == ["c-name", "c-state", "rm-progress"], node
        assert row["mark"] == model.word(node), node
        assert _shown_progress(row["progress"]) == _expected_progress(found, node), node
    # Three rows stated outright: a share, an all-stopped row and a row with nothing beneath.
    assert rows["capability:birch-cap"]["progress"]["pct"] == "100% delivered of 1 item"
    assert rows["capability:dune-cap"]["progress"]["words"] == ["0 delivered", "2 stopped"]
    assert rows["capability:dune-cap"]["progress"]["pct"] is None
    assert rows["capability:cinder-cap"]["progress"]["none"] == "Nothing beneath yet"
    assert rows["capability:cinder-cap"]["progress"]["cells"] == []


def test_roadmap_cells(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    found = _roadmap_expectations(payload_of(exports["roadmap"]))
    sections = _read_roadmap(opener(exports["roadmap"]))
    bars = 0
    for node, row in {r["id"]: r for s in sections for r in _walk_rows(s["rows"])}.items():
        prog = row["progress"]
        if found["progress"][node]["nothing_beneath"]:
            assert prog["cells"] == [] and prog["barHidden"] is None, node
            continue
        bars += 1
        assert prog["barHidden"] == "true" and len(prog["cells"]) == _BAR_CELLS, node
        assert tuple(prog["cells"].count(c) for c in _CELL_CLASS) == tuple(found["progress"][node]["cells"]), node
    assert bars == sum(1 for p in found["progress"].values() if not p["nothing_beneath"]) - 2  # minus the two strategies


def test_roadmap_strategy_headings(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    found = _roadmap_expectations(payload_of(exports["roadmap"]))
    sections = _read_roadmap(opener(exports["roadmap"]))
    assert [s["heading"] for s in sections] == ["Atlas direction", "Boreal direction", _NO_STRATEGY]
    for shown, want in zip(sections[:2], found["sections"][:2], strict=True):
        assert _shown_progress(shown["progress"]) == _expected_progress(found, want["strategy"])
        assert shown["progress"]["pct"] is not None and shown["progress"]["barHidden"] == "true"
    assert sections[0]["progress"]["pct"].startswith("33% delivered of ") and sections[1]["progress"]["pct"].startswith("17% delivered of ")
    assert sections[2]["progress"] is None


def test_roadmap_without_outstanding(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    whole = _roadmap_expectations(payload_of(exports["roadmap"]))
    payload = payload_of(exports["roadmap_incomplete"])
    assert payload["outstanding"]["available"] is False
    item = opener(exports["roadmap_incomplete"])
    sections = _read_roadmap(item)
    assert [s["heading"] for s in sections] == [s["heading"] for s in whole["sections"]]
    assert _shape([r for s in sections for r in s["rows"]]) == _expected_shape(
        [c for s in whole["sections"] for c in s["capabilities"]]
    )
    for s in sections:
        if s["heading"] != _NO_STRATEGY:
            assert s["progress"]["unknown"] == _UNKNOWN_PROGRESS
        for r in _walk_rows(s["rows"]):
            assert _shown_progress(r["progress"]) == {
                "words": [], "pct": None, "cells": [], "none": None, "unknown": _UNKNOWN_PROGRESS,
            }, r["id"]
    assert _rail_counts(item.page)["roadmap"] == str(_capability_total(payload))


def test_roadmap_no_capability(opener: Any, tmp_path: pathlib.Path) -> None:
    root = tmp_path / "no_capability"
    shutil.copytree(_FIXTURES / "mixed", root)
    for path in (root / "docs/product/intents").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("- **Level:** capability", "- **Level:** feature"), encoding="utf-8")
    export = _export(root, tmp_path / "out", "no_capability.html")
    payload = payload_of(export)
    assert payload["records"] and _capability_total(payload) == 0
    item = opener(export)
    _choose(item, "roadmap")
    assert _text(item.page, "#list") == "No capability is recorded."
    assert item.page.locator("#list a.row-link").count() == 0
    assert _rail_counts(item.page)["roadmap"] == "0"


@pytest.mark.parametrize("name", ["from_roadmap_cap", "from_roadmap_strategy"])
def test_roadmap_scoped_export(opener: Any, exports: dict[str, pathlib.Path], name: str) -> None:
    payload = payload_of(exports[name])
    assert payload["scope"].get("from")
    found = _roadmap_expectations(payload)
    sections = _read_roadmap(opener(exports[name]))
    assert [s["heading"] for s in sections] == [s["heading"] for s in found["sections"]]
    assert [_shape(s["rows"]) for s in sections] == [_expected_shape(s["capabilities"]) for s in found["sections"]]
    in_export = {i for i, r in payload["records"].items() if r["level"] == "capability"}
    assert {r["id"] for s in sections for r in _walk_rows(s["rows"])} == in_export
    for s, want in zip(sections, found["sections"], strict=True):
        if want["strategy"]:
            assert _shown_progress(s["progress"]) == _expected_progress(found, want["strategy"])
        for r in _walk_rows(s["rows"]):
            assert _shown_progress(r["progress"]) == _expected_progress(found, r["id"]), r["id"]
    if name == "from_roadmap_cap":  # the strategy above the scope is outside the export
        assert [s["heading"] for s in sections] == [_NO_STRATEGY]


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_roadmap_cell_colours(opener: Any, exports: dict[str, pathlib.Path], scheme: str) -> None:
    item = opener(exports["roadmap"], scheme=scheme)
    _read_roadmap(item)
    colours = item.page.evaluate(
        """classes => classes.map((c) => getComputedStyle(document.querySelector('.rm-cell.' + c)).backgroundColor)""",
        list(_CELL_CLASS),
    )
    assert len(colours) == 4 and len(set(colours)) == 4, (scheme, colours)


# ---------------------------------------------------------------------------
# Browse all intents: Show, Group, expand controls and the tree, against the payload reading
# ---------------------------------------------------------------------------

_LEVEL_WORDS = {"product-vision": "Vision", "product-strategy": "Strategy", "capability": "Capability", "feature": "Feature", "": "Unrecorded"}
_UNKNOWN_OPEN = "Open and done are unknown: delivery mapping incomplete."


def _browse_expectations(payload: dict[str, Any], show: str = "all", group: str = "hierarchy") -> dict[str, Any]:
    """The Browse tree the spec's terms give for a Show and Group choice, read from the payload alone.

    ``sections`` lists ``{"title", "disclosure", "rows"}``; a row is ``{"id", "name", "tag", "context",
    "roll", "open", "refused", "children"}``, children being the shown rows beneath it. ``count`` is the
    number of intents matching Show.
    """
    model = Model(payload)
    available = model.available
    if not available:
        show = "all"

    def matches(i: str) -> bool:
        return show == "all" or (i in model.open) == (show == "open")

    kids: dict[str, list[str]] = {}
    if group == "hierarchy":
        roots = _tree_roots(model)
        claimed = set(roots)
        todo = list(roots)
        while todo:
            at = todo.pop()
            mine = model.by_name(c for c in model.records if _up(model, c) == at and c not in claimed)
            claimed.update(mine)
            todo += mine
            kids[at] = mine
        parents = [r for r in roots if payload["scope"].get("from") or kids[r]]
        lists = (parents, [r for r in roots if r not in parents])
        titles = ("Hierarchy roots", "No parent and nothing beneath")
    else:
        tops: list[str] = []
        loose: list[str] = []
        for i, record in model.records.items():
            anchor = _nearest(model, i, "capability")
            if anchor is not None:
                kids.setdefault(anchor, []).append(i)
            elif record["level"] == "capability":
                tops.append(i)
            else:
                loose.append(i)
        kids = {k: model.by_name(v) for k, v in kids.items()}
        lists = (model.by_name(tops), model.by_name(loose))
        titles = ("Top-level capabilities", "Not under a capability")

    def beneath(i: str) -> list[str]:
        return [x for k in kids.get(i, []) for x in (k, *beneath(k))]

    def shown(i: str) -> bool:
        return matches(i) or any(shown(k) for k in kids.get(i, []))

    def row(i: str) -> dict[str, Any]:
        below = beneath(i)
        open_items = len(model.beneath(i))
        state = (model.records[i].get("parent_edge") or {}).get("state")
        return {
            "id": i,
            "name": model.display(i),
            "tag": _LEVEL_WORDS.get(model.records[i]["level"], model.records[i]["level"]),
            "context": not matches(i),
            "roll": f"{sum(1 for x in below if x not in model.open)}/{len(below)} closed" if below and available else None,
            "open": f"{open_items} open items" if open_items and available else None,
            "refused": f"refused parent: {state}" if state else None,
            "children": [row(k) for k in kids.get(i, []) if shown(k)],
        }

    sections = []
    for index, (title, ids) in enumerate(zip(titles, lists, strict=True)):
        rows = [row(i) for i in ids if shown(i)]
        if rows:
            sections.append({"title": title, "disclosure": index == 1, "rows": rows})
    return {"sections": sections, "count": sum(1 for i in model.records if matches(i)), "show": show}


_READ_TREE = """() => {
  const row = (li) => {
    const a = li.querySelector(':scope > a.row-link');
    const ctx = a.querySelector('.c-context');
    const text = (sel) => { const e = ctx.querySelector(sel); return e ? e.textContent : null; };
    const tag = a.querySelector('.level-tag');
    const toggle = li.querySelector(':scope > button.toggle');
    return {
      id: a.dataset.node,
      name: a.querySelector('.c-name').textContent,
      tag: tag ? tag.textContent : null,
      tagAfterName: !!tag && tag.previousSibling.nodeValue === ' ' && tag.previousSibling.previousSibling === a.querySelector('.c-name'),
      context: text('.ctx-tag') !== null,
      ctxText: text('.ctx-tag'),
      hidden: text('.visually-hidden'),
      roll: text('.tree-roll'),
      open: text('.tree-open'),
      where: text('.tree-where'),
      toggle: toggle ? toggle.getAttribute('aria-expanded') : null,
      toggleName: toggle ? toggle.textContent : null,
      children: Array.from(li.querySelectorAll(':scope > ul > li')).map(row),
    };
  };
  const out = [];
  for (const head of document.querySelectorAll('#list > h3.tree-head, #list > details.loose')) {
    const disclosure = head.tagName === 'DETAILS';
    const list = disclosure ? head.querySelector(':scope > ul.tree') : head.nextElementSibling;
    out.push({
      title: (disclosure ? head.querySelector(':scope > summary') : head).textContent,
      disclosure,
      open: disclosure ? head.open : null,
      listClass: list.className,
      rows: Array.from(list.children).map(row),
    });
  }
  return out;
}"""


def _browse_route(show: str, group: str) -> dict[str, str]:
    return {"show": "" if show == "all" else show, "group": "" if group == "hierarchy" else group}


def _open_browse(item: Opened, show: str = "all", group: str = "hierarchy", *, expand: bool = True) -> list[dict[str, Any]]:
    """Open Browse with a Show and Group choice, expand every subtree, open the disclosures and read the tree."""
    _choose(item, "browse", **_browse_route(show, group))
    item.page.wait_for_selector("#list .tree", state="attached")  # a lone disclosure is closed, so hidden
    if expand:
        item.page.get_by_role("button", name="Expand all").click()
        _open_disclosures(item.page)
    return item.page.evaluate(_READ_TREE)  # type: ignore[no-any-return]


def _shown_row(row: dict[str, Any]) -> dict[str, Any]:
    """The fields a page row and an expected row share, children included."""
    keys = ("id", "name", "tag", "context", "roll", "open")
    return {**{k: row[k] for k in keys}, "children": [_shown_row(c) for c in row["children"]]}


def _flatten(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for row in rows for r in (row, *_flatten(row["children"]))]


def _compare_tree(sections: list[dict[str, Any]], want: dict[str, Any]) -> None:
    assert [(s["title"], s["disclosure"]) for s in sections] == [(s["title"], s["disclosure"]) for s in want["sections"]]
    for got, exp in zip(sections, want["sections"], strict=True):
        assert [_shown_row(r) for r in got["rows"]] == [_shown_row(r) for r in exp["rows"]], got["title"]
        assert "tree" in got["listClass"].split()
        refused = {r["id"]: r["refused"] for r in _flatten(exp["rows"])}
        for r in _flatten(got["rows"]):
            if refused[r["id"]]:
                assert refused[r["id"]] in r["where"], r["id"]
            else:
                assert "refused parent" not in r["where"], r["id"]


_BROWSE_CHOICES = [(show, group) for show in ("all", "open", "done") for group in ("hierarchy", "capability")]
_BROWSE_IDS = [f"{show}-{group}" for show, group in _BROWSE_CHOICES]


def _pressed(page: Page, group: str) -> list[str]:
    return page.get_by_role("group", name=group).get_by_role("button", pressed=True).all_inner_texts()


def test_browse_toolbar_and_defaults(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["roadmap"])
    page = item.page
    _choose(item, "browse")
    page.wait_for_selector("#list .tree")
    show, group = page.get_by_role("group", name="Show"), page.get_by_role("group", name="Group")
    assert show.get_by_role("button").all_inner_texts() == ["All", "Open", "Done"]
    assert group.get_by_role("button").all_inner_texts() == ["Full hierarchy", "By capability"]
    assert _pressed(page, "Show") == ["All"] and _pressed(page, "Group") == ["Full hierarchy"]
    for name in ("Show", "Group"):
        values = page.get_by_role("group", name=name).get_by_role("button").evaluate_all(
            "els => els.map(e => e.getAttribute('aria-pressed'))"
        )
        assert sorted(values) == ["false"] * (len(values) - 1) + ["true"]
    bar = page.locator("#tools > .tree-bar")
    assert bar.get_by_role("button", name=re.compile(r"^(Expand|Collapse) all$")).all_inner_texts() == ["Expand all", "Collapse all"]
    assert page.evaluate(
        """() => !!(document.querySelector('#tools > .tree-bar').compareDocumentPosition(
          document.querySelector('#list .tree')) & Node.DOCUMENT_POSITION_FOLLOWING)"""
    )
    sizes = bar.locator("button").evaluate_all(
        "els => els.map(e => { const r = e.getBoundingClientRect(); return [r.width, r.height]; })"
    )
    assert len(sizes) == 7 and all(w >= 24 and h >= 24 for w, h in sizes), sizes
    for route, expected in (
        ({"show": "open", "group": "capability"}, (["Open"], ["By capability"])),
        ({"show": "done"}, (["Done"], ["Full hierarchy"])),
        ({"show": "bogus", "group": "bogus"}, (["All"], ["Full hierarchy"])),
    ):
        _choose(item, "browse", **route)
        assert (_pressed(page, "Show"), _pressed(page, "Group")) == expected, route


def test_browse_summary_follows_show_and_group(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["roadmap"])
    page = item.page
    for route, lead, sort in (
        ({}, "Every intent in the export, under its parent.", "Under each parent, by name"),
        ({"show": "open", "group": "capability"}, "Open work only. Every intent in the export, under its nearest capability.", "Under each capability, by name"),
        ({"show": "done"}, "Done work only. Every intent in the export, under its parent.", "Under each parent, by name"),
    ):
        _choose(item, "browse", **route)
        assert (_text(page, "#list-lead"), _text(page, "#list-sort")) == (lead, sort), route


def test_browse_filter_turns_grouping_and_expanding_off(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["roadmap"])
    page = item.page
    _choose(item, "browse", group="capability", level="feature")
    page.wait_for_selector("#tools .tree-bar")
    states = page.eval_on_selector_all("#tools button", "els => els.map(e => [e.textContent, e.disabled])")
    assert dict(states) == {"All": False, "Open": False, "Done": False, "Full hierarchy": True, "By capability": True, "Expand all": True, "Collapse all": True}
    assert "Grouping and expanding are off while a filter is set." in _text(page, "#tools")
    assert _pressed(page, "Group") == ["By capability"]


def test_trailing_tracks_hold_one_x_at_every_depth(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["roadmap"], width=1680, height=1000)
    page = item.page
    _open_browse(item, "all", "hierarchy")
    xs = page.evaluate(
        """() => { const by = {};
          document.querySelectorAll('#list .tree-row').forEach((li) => {
            let d = 0; for (let e = li.parentElement; e; e = e.parentElement) { if (e.classList && e.classList.contains('subtree')) d++; }
            const a = li.querySelector(':scope > a.row-link');
            (by[d] = by[d] || new Set()).add(Math.round(a.querySelector('.c-state .mark').getBoundingClientRect().left) + '/' +
              Math.round(a.querySelector('.c-context').getBoundingClientRect().left));
          });
          return Object.values(by).map((s) => Array.from(s)); }"""
    )
    assert len(xs) >= 2 and all(len(group) == 1 for group in xs) and len({group[0] for group in xs}) == 1, xs


def test_roadmap_bars_and_counts_share_one_left_edge(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["roadmap"], width=1680, height=1000)
    _read_roadmap(item)
    lefts = item.page.evaluate(
        """() => { const bars = new Set(), words = new Set();
          document.querySelectorAll('#list .rm-bar').forEach((b) => bars.add(Math.round(b.getBoundingClientRect().left)));
          document.querySelectorAll('#list .rm-words').forEach((b) => words.add(Math.round(b.getBoundingClientRect().left)));
          return [Array.from(bars), Array.from(words)]; }"""
    )
    assert len(lefts[0]) == 1 and lefts[0] == lefts[1], lefts


def test_expand_and_collapse_all(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    for group in ("hierarchy", "capability"):
        want = _browse_expectations(payload, "all", group)
        parents = sum(1 for r in _flatten(want["sections"][0]["rows"]) if r["children"])
        top = sum(1 for r in want["sections"][0]["rows"] if r["children"])
        assert parents > top > 0
        item = opener(exports["roadmap"])
        page = item.page
        _choose(item, "browse", **_browse_route("all", group))
        page.wait_for_selector("#list .tree")
        first = "document.querySelector('#list .tree')"
        states = f"() => Array.from({first}.querySelectorAll('button.toggle')).map(b => b.getAttribute('aria-expanded'))"
        disclosure = page.locator("#list details.loose")
        assert page.evaluate(states) == ["false"] * top and not disclosure.evaluate("d => d.open")
        page.get_by_role("button", name="Expand all").click()
        assert page.evaluate(states) == ["true"] * parents
        assert page.evaluate("document.activeElement.textContent") == "Expand all"
        assert not disclosure.evaluate("d => d.open")  # a disclosure is left as it was
        disclosure.locator("> summary").click()
        page.get_by_role("button", name="Collapse all").click()
        assert page.evaluate(states) == ["false"] * parents
        assert page.evaluate("document.activeElement.textContent") == "Collapse all"
        assert disclosure.evaluate("d => d.open")
        assert page.evaluate(f"() => Array.from({first}.querySelectorAll('ul.subtree')).every(u => u.hidden)")
        page.get_by_role("button", name="Expand all").click()
        assert page.evaluate(states) == ["true"] * parents
        assert disclosure.evaluate("d => d.open")
        assert page.evaluate("() => document.querySelectorAll('#list details.loose button.toggle').length") == 0


@pytest.mark.parametrize("group", ["hierarchy", "capability"])
def test_tree_row_tag_and_counts(opener: Any, exports: dict[str, pathlib.Path], group: str) -> None:
    payload = payload_of(exports["roadmap"])
    item = opener(exports["roadmap"])
    sections = _open_browse(item, "all", group)
    want = _browse_expectations(payload, "all", group)
    _compare_tree(sections, want)
    rows = _flatten([r for s in sections for r in s["rows"]])
    assert all(r["tag"] and r["tagAfterName"] for r in rows)
    assert {r["tag"] for r in rows} >= {"Strategy", "Capability", "Feature"}
    assert any(r["roll"] for r in rows) and any(r["open"] for r in rows)
    # An open-items count reads the same in either grouping.
    other = _browse_expectations(payload, "all", "capability" if group == "hierarchy" else "hierarchy")
    here = {r["id"]: r["open"] for r in _flatten([r for s in want["sections"] for r in s["rows"]])}
    there = {r["id"]: r["open"] for r in _flatten([r for s in other["sections"] for r in s["rows"]])}
    assert here == there
    # The link's accessible name holds the name and the tag.
    item.page.get_by_role("button", name="Expand all").click()
    ids = _ids(item.page)
    for node_id, accessible in zip(ids, _row_ax_names(item.page), strict=True):
        row = next(r for r in rows if r["id"] == node_id)
        assert accessible is not None and _squash(row["name"] + row["tag"]) in _squash(accessible), node_id


def test_tree_row_tag_texts_for_every_level(opener: Any, exports: dict[str, pathlib.Path], tmp_path: pathlib.Path) -> None:
    levels = {"intent:orphan-feat": "", "intent:dangling-feat": "product-vision", "intent:anchor-feat-open": "initiative"}

    def edit(p: dict[str, Any]) -> dict[str, Any]:
        for node, level in levels.items():
            p["records"][node]["level"] = level
        return p

    path = _rewrite(exports["roadmap"], tmp_path / "levels.html", edit)
    payload = payload_of(path)
    sections = _open_browse(opener(path))
    _compare_tree(sections, _browse_expectations(payload))
    tags = {r["id"]: r["tag"] for s in sections for r in _flatten(s["rows"])}
    assert tags["intent:orphan-feat"] == "Unrecorded" and tags["intent:dangling-feat"] == "Vision"
    assert tags["intent:anchor-feat-open"] == "initiative"
    assert tags["intent:atlas-direction"] == "Strategy" and tags["capability:anchor-cap"] == "Capability"
    assert tags["intent:birch-feat"] == "Feature"


def test_full_hierarchy_sections(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    item = opener(exports["roadmap"])
    _choose(item, "browse")
    item.page.wait_for_selector("#list .tree")
    assert item.page.evaluate(_READ_TREE)[1]["open"] is False  # the disclosure starts closed
    sections = _open_browse(item)
    want = _browse_expectations(payload)
    _compare_tree(sections, want)
    assert [(s["title"], s["disclosure"]) for s in sections] == [
        ("Hierarchy roots", False),
        ("No parent and nothing beneath", True),
    ]
    stated = dict(_readme_tables()["Tree roots"])
    model = Model(payload)
    assert [r["id"] for r in sections[0]["rows"]] == model.by_name(n for n, p in stated.items() if p == "root, intents beneath")
    assert [r["id"] for r in sections[1]["rows"]] == model.by_name(n for n, p in stated.items() if p == "root, nothing beneath")
    ids = _ids(item.page, "#list .tree a.row-link")
    assert sorted(ids) == sorted(payload["records"]) and len(ids) == len(set(ids))


def test_by_capability_sections(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    item = opener(exports["roadmap"])
    sections = _open_browse(item, "all", "capability")
    _compare_tree(sections, _browse_expectations(payload, "all", "capability"))
    assert [(s["title"], s["disclosure"]) for s in sections] == [
        ("Top-level capabilities", False),
        ("Not under a capability", True),
    ]
    stated = {n for n, _, place in _readme_tables()["Records"] if place.startswith('section "')}
    assert {r["id"] for r in sections[0]["rows"]} == stated
    loose = {r["id"] for r in sections[1]["rows"]}
    assert "intent:atlas-direction" in loose and "intent:boreal-direction" in loose  # strategies are listed there
    assert all(not r["children"] for r in sections[1]["rows"]) and not any(r["id"].startswith("capability:") for r in sections[1]["rows"])
    nested = {r["id"]: [c["id"] for c in r["children"]] for r in _flatten(sections[0]["rows"])}
    assert "capability:anchor-sub-cap" in nested["capability:anchor-cap"]
    assert "intent:anchor-sub-feat-a" in nested["capability:anchor-sub-cap"]
    ids = _ids(item.page, "#list .tree a.row-link")
    assert sorted(ids) == sorted(payload["records"]) and len(ids) == len(set(ids))


@pytest.mark.parametrize(("show", "group"), [c for c in _BROWSE_CHOICES if c[0] != "all"], ids=[i for i in _BROWSE_IDS if not i.startswith("all")])
def test_show_open_and_done_with_context_rows(opener: Any, exports: dict[str, pathlib.Path], show: str, group: str) -> None:
    payload = payload_of(exports["roadmap"])
    item = opener(exports["roadmap"])
    page = item.page
    sections = _open_browse(item, show, group, expand=False)
    # Every subtree that holds a shown row is open on render, with no Expand all pressed.
    toggles = [r["toggle"] for s in sections for r in _flatten(s["rows"]) if r["toggle"] is not None]
    assert toggles and set(toggles) == {"true"}
    _open_disclosures(page)
    sections = page.evaluate(_READ_TREE)
    want = _browse_expectations(payload, show, group)
    _compare_tree(sections, want)
    rows = _flatten([r for s in sections for r in s["rows"]])
    model = Model(payload)
    for r in rows:
        assert (r["id"] in model.open) == (show == "open") or r["context"], r["id"]
    names = dict(zip(_ids(page), _row_ax_names(page), strict=True))
    for r in rows:
        if r["context"]:
            assert r["ctxText"] == "context" and r["hidden"] == "shown for context", r["id"]
            assert "shown for context" in names[r["id"]]
        else:
            assert r["ctxText"] is None and r["hidden"] is None and "shown for context" not in names[r["id"]], r["id"]


def test_context_rows_exist_where_a_choice_hides_a_parent(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    found = {
        (show, group): any(r["context"] for r in _flatten([x for s in _browse_expectations(payload, show, group)["sections"] for x in s["rows"]]))
        for show, group in _BROWSE_CHOICES
    }
    assert found[("open", "hierarchy")] and found[("done", "hierarchy")] and found[("open", "capability")]
    assert not found[("all", "hierarchy")] and not found[("all", "capability")]


def test_browse_count_and_announcements(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    item = opener(exports["roadmap"])
    page = item.page
    _choose(item, "browse")
    page.wait_for_selector("#list .tree")
    assert _count_text(page) == f"{len(payload['records'])} intents"
    live = "document.getElementById('live').textContent = ''"
    for label, show, group in (("Open", "open", "hierarchy"), ("Done", "done", "hierarchy"), ("By capability", "done", "capability"), ("All", "all", "capability"), ("Full hierarchy", "all", "hierarchy")):
        page.evaluate(live)
        page.get_by_role("button", name=label, exact=True).click()
        count = _browse_expectations(payload, show, group)["count"]
        announced = _live(page, "All intents, ")
        assert announced == f"All intents, {count} {'intent' if count == 1 else 'intents'}", (label, announced)
        assert _count_text(page) == f"{count} {'intent' if count == 1 else 'intents'}"
    # A filter narrows the count together with Show.
    model = Model(payload)
    for show in ("all", "open", "done"):
        _choose(item, "browse", level="capability", **_browse_route(show, "hierarchy"))
        want = [i for i, r in model.records.items() if r["level"] == "capability" and (show == "all" or (i in model.open) == (show == "open"))]
        assert _count_text(page) == f"{len(want)} intent{'' if len(want) == 1 else 's'}", show


def test_browse_without_outstanding(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap_incomplete"])
    assert payload["outstanding"]["available"] is False
    item = opener(exports["roadmap_incomplete"])
    page = item.page
    for route in ({}, {"show": "open"}, {"show": "done", "group": "capability"}):
        group = route.get("group", "")
        _choose(item, "browse", **route)
        page.wait_for_selector("#list .tree")
        shown = page.get_by_role("group", name="Show")
        assert shown.get_by_role("button", name="Open").is_disabled() and shown.get_by_role("button", name="Done").is_disabled()
        assert shown.get_by_role("button", name="All").is_enabled()
        assert _pressed(page, "Show") == ["All"]  # a show choice in the fragment reads as All
        assert page.locator("#tools .tree-note").inner_text() == _UNKNOWN_OPEN
        assert page.locator("#list .tree-roll, #list .tree-open").count() == 0
        body = _text(page, "#list")
        assert "closed" not in body and "open items" not in body
        page.get_by_role("button", name="Expand all").click()
        _open_disclosures(page)
        want = _browse_expectations(payload, "all", "capability" if group else "hierarchy")
        _compare_tree(page.evaluate(_READ_TREE), want)
        assert _count_text(page) == f"{len(payload['records'])} intents"


def test_filters_flatten_and_intersect_show(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    model = Model(payload)
    root = _FIXTURES / "roadmap"
    status = payload["records"]["intent:anchor-feat-open"]["status"]
    item = opener(exports["roadmap"])
    page = item.page
    for filters, selectors in (
        ({"level": "capability"}, {"level": "capability"}),
        ({"level": "feature"}, {"level": "feature"}),
        ({"status": status}, {"exact_status": status}),
        ({"level": "feature", "status": status}, {"level": "feature", "exact_status": status}),
    ):
        for show in ("all", "open", "done"):
            for group in ("hierarchy", "capability"):
                query = set(_search_ids(root, selectors))
                want = model.by_name(i for i in query if show == "all" or (i in model.open) == (show == "open"))
                assert want or show != "all"
                _choose(item, "browse", **filters, **_browse_route(show, group))
                if not want:
                    page.wait_for_selector("#list .empty")
                    continue
                page.wait_for_selector("#list .row")
                assert _ids(page) == want, (filters, show, group)
                assert page.locator("#list .tree, #list details, #list h3.tree-head, #list .context-only, #list .ctx-tag").count() == 0
                assert _count_text(page) == f"{len(want)} intent{'' if len(want) == 1 else 's'}"
                if show == "all":
                    assert set(_ids(page)) == query  # query parity for the filters alone
    _choose(item, "browse", level="capability", show="open", group="capability")
    assert page.get_by_role("group", name="Show").get_by_role("button", pressed=True).all_inner_texts() == ["Open"]
    page.get_by_role("group", name="Show").get_by_role("button", name="All").click()
    assert _ids(page) == model.by_name(i for i, r in model.records.items() if r["level"] == "capability")
    _choose(item, "browse", level="feature", status="No-such-status")
    page.get_by_role("button", name="Clear filters").click()
    page.wait_for_selector("#list .tree")
    assert len(_ids(page, "#list .tree a.row-link")) >= 1 and page.locator("#list .empty").count() == 0


def test_show_and_group_in_fragment(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    payload = payload_of(exports["roadmap"])
    item = opener(exports["roadmap"])
    page = item.page
    _choose(item, "browse")
    page.wait_for_selector("#list .tree")
    start = _history_length(page)
    page.get_by_role("button", name="Open", exact=True).click()
    assert _fragment(page).get("show") == "open"
    assert page.evaluate("document.activeElement.dataset.ctl") == "show-open"
    page.get_by_role("button", name="By capability").click()
    assert _fragment(page).get("group") == "capability" and _fragment(page).get("show") == "open"
    assert page.evaluate("document.activeElement.dataset.ctl") == "group-capability"
    assert _history_length(page) == start
    page.reload()
    page.wait_for_selector("#list .tree")
    assert _pressed(page, "Show") == ["Open"] and _pressed(page, "Group") == ["By capability"]
    _compare_tree(page.evaluate(_READ_TREE), _browse_expectations(payload, "open", "capability"))
    page.get_by_role("button", name="All", exact=True).click()
    page.get_by_role("button", name="Full hierarchy").click()
    assert "show" not in _fragment(page) and "group" not in _fragment(page)
    assert _history_length(page) == start
    # A picked row keeps both choices in its own link.
    item.go(_frag(q="browse", show="done", group="capability"))
    href = page.locator("#list a.row-link").first.get_attribute("href")
    assert "show=done" in href and "group=capability" in href


@pytest.mark.parametrize("name", ["from_roadmap_leaf", "from_roadmap_cap"])
def test_browse_scoped_export(opener: Any, exports: dict[str, pathlib.Path], name: str) -> None:
    payload = payload_of(exports[name])
    scope = payload["scope"]["from"]
    item = opener(exports[name])
    sections = _open_browse(item, "all", "hierarchy")
    _compare_tree(sections, _browse_expectations(payload, "all", "hierarchy"))
    assert [s["title"] for s in sections] == ["Hierarchy roots"]
    assert [r["id"] for r in sections[0]["rows"]] == [scope]
    assert item.page.locator("#list details").count() == 0
    assert "No parent and nothing beneath" not in _text(item.page, "#list")
    ids = _ids(item.page, "#list .tree a.row-link")
    assert sorted(ids) == sorted(payload["records"]) and len(ids) == len(set(ids))
    by_cap = _open_browse(item, "all", "capability")
    _compare_tree(by_cap, _browse_expectations(payload, "all", "capability"))
    ids = _ids(item.page, "#list .tree a.row-link")
    assert sorted(ids) == sorted(payload["records"]) and len(ids) == len(set(ids))
    placed = {s["title"]: [r["id"] for r in s["rows"]] for s in by_cap}
    if name == "from_roadmap_leaf":  # the capability above the scope is outside the export
        assert placed == {"Not under a capability": [scope]}
    else:
        assert placed["Top-level capabilities"] == [scope]
        assert "Not under a capability" not in placed


def test_browse_parent_loop_roots_each_intent_once(opener: Any, exports: dict[str, pathlib.Path], tmp_path: pathlib.Path) -> None:
    """A loop whose edges all resolve is rooted at its first member by name; a tail hangs beneath it."""

    def edit(p: dict[str, Any]) -> dict[str, Any]:
        alpha, gamma = p["records"]["intent:loop-alpha"], p["records"]["intent:loop-gamma"]
        alpha["parent_edge"] = {**alpha["parent_edge"], "to": "intent:loop-gamma"}
        del alpha["parent_edge"]["state"]
        gamma["children"] = ["intent:loop-alpha"]
        return p

    path = _rewrite(exports["roadmap"], tmp_path / "loop.html", edit)
    payload = payload_of(path)
    item = opener(path)
    sections = _open_browse(item)
    _compare_tree(sections, _browse_expectations(payload))
    tops = [r["id"] for s in sections for r in s["rows"]]
    assert sorted(tops) == sorted(_roadmap_expectations(payload)["roots"])
    assert "intent:loop-alpha" in tops and "intent:acorn-tail" not in tops
    assert len([t for t in tops if t.startswith("intent:loop-")]) == 1
    ids = _ids(item.page, "#list .tree a.row-link")
    assert sorted(ids) == sorted(payload["records"]) and len(ids) == len(set(ids))
    loop_root = next(r for s in sections for r in s["rows"] if r["id"] == "intent:loop-alpha")
    assert "intent:acorn-tail" in {r["id"] for r in _flatten([loop_root])}
