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
]
_TRUST = ["delivery_contract", "pointer_checked", "pointer_unchecked"]
_QUESTIONS = ["next", "capabilities", "noparent", "broken", "browse"]
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
        ("empty", _FIXTURES / "empty"),
        ("terminality", _FIXTURES / "terminality"),
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
    found["incomplete"] = _export(
        _FIXTURES / "mixed", out, "incomplete.html", _delivery_provider=_incomplete
    )
    found["hostile_incomplete"] = _export(
        _FIXTURES / "hostile", out, "hostile_incomplete.html", _delivery_provider=_incomplete
    )
    found["hostile_diag"] = _export(
        _FIXTURES / "hostile", out, "hostile_diag.html", _delivery_provider=_hostile_diagnostic
    )
    found["india_parent"] = _export(_india_parent_corpus(tmp), out, "india_parent.html")
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
    ) -> None:
        self.url = path.as_uri()
        self.context = browser.new_context(
            viewport={"width": width, "height": height},
            color_scheme=scheme,  # type: ignore[arg-type]
            java_script_enabled=js,
        )
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
        return sorted(entries, key=lambda e: (self.display(e[0]).lower(), e[0]))

    def mark(self, node_id: str) -> tuple[str, str]:
        word = self.word(node_id)
        if word in ("Implementing", "Executing"):
            return "●", word
        if word in ("Approved", "Accepted", "Ready"):
            return "◆", word
        if self.available and node_id not in self.open:
            return "✓", word
        return "◇", word


def _marks(page: Page, selector: str) -> list[tuple[str, str, str | None]]:
    """(glyph, word, aria-hidden of the glyph) for every state mark under *selector*."""
    return page.eval_on_selector_all(  # type: ignore[no-any-return]
        f"{selector} .mark",
        """els => els.map(m => [m.querySelector('.mark-g').textContent,
          m.querySelector('.mark-w').textContent, m.querySelector('.mark-g').getAttribute('aria-hidden')])""",
    )


def _choose(item: Opened, question: str, **route: str) -> None:
    item.go(_frag(q=question, **route))


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


def test_ac_0001_five_destinations_with_counts(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    assert page.locator("nav").count() == 1
    links = page.locator("nav a")
    names = page.eval_on_selector_all("nav a .q-name", "els => els.map(e => e.textContent)")
    assert links.count() == 5
    assert names == [
        "What can I work on next?",
        "What is still open under a capability?",
        "What has no parent?",
        "What is broken?",
        "Browse all intents",
    ]
    counts = page.eval_on_selector_all("nav a .q-count", "els => els.map(e => e.textContent)")
    assert counts == ["3", "2", "6", "0"]
    assert links.nth(0).get_attribute("aria-current") == "page"
    assert [links.nth(i).get_attribute("aria-current") for i in range(1, 5)] == [None] * 4
    assert page.locator("#list a.row-link").count() == 3
    assert _text(page, "#list-title") == "In a startable stage"
    assert _count_text(page) == "3 items" and _text(page, "#list-sort") == "By stage, then name"
    for key, shown in zip(_QUESTIONS[:4], counts, strict=True):
        _choose(item, key)
        assert str(page.locator("#list a.row-link").count()) == shown, key


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
    assert list(contexts) == [f"{n} open" for _, n in expected]


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
    assert len(expected) == len(states) + 1 and states
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
    nothing = _rewrite(
        exports["mixed"], tmp_path / "nothing.html", lambda p: {**p, "outstanding": {"placed": [], "no_parent": []}}
    )
    wanted = {
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
        node = next(n for n in tree["nodes"] if not n.get("ignored"))
        names.append(node["name"]["value"])
    cdp.detach()
    return names


def test_ac_0009_row_is_one_link_with_three_cells(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    model = Model(payload_of(exports["mixed"]))
    for key in _QUESTIONS[:4]:
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
    for key in ("next", "noparent"):
        _choose(item, key)
        contexts = page.eval_on_selector_all("#list .c-context", "els => els.map(e => e.textContent)")
        for node_id, context in zip(_ids(page), contexts, strict=True):
            node = model.nodes[node_id]
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
        text = _detail_part(page, "What is broken").inner_text()
        if held or held_diag:
            assert "Nothing broken here." not in text
            assert _detail_part(page, "What is broken").locator("li.edge").count() == len(held) + len(held_diag)
        else:
            assert "Nothing broken here." in text
    unavailable = opener(exports["hostile_incomplete"])
    um = Model(payload_of(exports["hostile_incomplete"]))
    for node_id in um.nodes:
        page = _pick(unavailable, node_id)
        held = [e for e in um.p["edges"] if e["from"] == node_id and e.get("state")]
        section = _detail_part(page, "What is broken")
        assert "Delivery diagnostics were unavailable." in section.inner_text()
        assert section.locator("li.edge").count() == len(held)


def test_ac_0018_where_it_sits(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    model = Model(payload_of(exports["mixed"]))
    page = _pick(item, "spec:golf-new", "browse")
    trail = _detail_part(page, "Where it sits").locator("p.trail")
    assert trail.count() == len(model.ancestor_lists("spec:golf-new"))
    last = trail.first.locator("a[data-node]").last
    assert last.get_attribute("data-node") == "intent:golf-new"
    assert trail.first.locator(".mark").count() == trail.first.locator("a[data-node]").count()
    page = _pick(item, "spec:bravo-spec")
    trails = _detail_part(page, "Where it sits").locator("p.trail")
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
        ("intent:bravo-feat", ["Parent", "Child intents", "Briefs", "Specs", "Delivery relations", "Delivery diagnostics", "Related, written here", "Related, written elsewhere"]),
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


def test_ac_0021_focus_after_an_action(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    page = item.page
    page.locator('nav a[data-q="noparent"]').click()
    assert page.evaluate("document.activeElement.dataset.q") == "noparent"
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
    rendered = {"label-group": set(), "label-state": set(), "label-trust": set()}
    glyphs: set[str] = set()
    for name in ("hostile", "cycle", "multiple", "self_reference", "dangling", "retired", "kind_mismatch", "out_of_type", "unparseable", "coordinated", "related", "latest"):
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
    return page.evaluate(  # type: ignore[no-any-return]
        """() => {
          const all = Array.from(document.querySelectorAll('#list a.row-link')).map(a => a.dataset.node);
          const roots = Array.from(document.querySelectorAll('#list > ul > li')).map(li => li.querySelector('a.row-link').dataset.node);
          const kids = {};
          for (const li of document.querySelectorAll('#list li.tree-row')) {
            const id = li.querySelector(':scope > a.row-link').dataset.node;
            kids[id] = Array.from(li.querySelectorAll(':scope > ul > li')).map(c => c.querySelector('a.row-link').dataset.node);
          }
          return { all, roots, kids };
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
    assert tree["roots"] == model.by_name(roots)
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
    assert page.locator("#list button").count() == 1
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
        for key in _QUESTIONS[:3]:
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
    counts = page.eval_on_selector_all("nav a .q-count", "els => els.map(e => e.textContent)")
    assert counts[:3] == ["unknown"] * 3 and counts[3] == str(len([e for e in payload["edges"] if e.get("state")]))
    for key in _QUESTIONS[:3]:
        _choose(item, key)
        text = _text(page, "#list")
        assert "Can't list open work: delivery mapping incomplete." in text and reason in text, key
        assert page.locator("#list a.row-link").count() == 0
    _choose(item, "broken")
    states = [e for e in payload["edges"] if e.get("state")]
    assert states and len(_ids(page)) == len(states)
    assert "Delivery diagnostics were unavailable" in _text(page, "#list")
    _choose(item, "browse")
    _expand_all(page)
    assert sorted(_ids(page)) == sorted(payload["records"])


def test_ac_0043_empty_corpus(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["empty"])
    page = item.page
    assert "No intents, briefs or specs found under this root." in _text(page, "#list")
    assert page.eval_on_selector_all("nav a .q-count", "els => els.map(e => e.textContent)") == ["0"] * 4
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
