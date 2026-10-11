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
_VIEWS = ["tree", "outstanding", "refused", "parentless"]
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


def _visit_everything(item: Opened, payload: dict[str, Any]) -> None:
    for key in _VIEWS:
        item.go(f"view={key}")
        item.page.wait_for_selector("#view-heading")
        for node in payload["nodes"]:
            item.go(f"view={key}&node=" + node["id"].replace(":", "%3A"))
            item.page.wait_for_function(
                "id => document.getElementById('detail-heading').textContent === id",
                arg=node["id"],
            )


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
# AC-0028 .. AC-0036: links, inertness, labels
# ---------------------------------------------------------------------------


def test_ac_0028_source_links_are_labelled_or_inert(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    latest = opener(exports["latest"])
    for key in _VIEWS:
        latest.go(f"view={key}&node=capability%3Aalpha-cap")
        hrefs = latest.page.eval_on_selector_all(
            "[href]", "els => els.map(e => e.getAttribute('href'))"
        )
        assert all(h.startswith("#") or h.startswith("https://github.com/") for h in hrefs), hrefs
    latest.go("view=tree&node=capability%3Aalpha-cap")
    link = latest.page.locator("#detail-body a.source-link")
    assert link.count() == 1 and "/blob/HEAD/" in link.get_attribute("href")
    assert link.get_attribute("rel") == "noopener noreferrer"
    assert "may be newer than this export" in _text(latest.page, "#detail-body .source")
    inert = opener(exports["inert"])
    inert.go("view=tree&node=capability%3Aalpha-cap")
    assert inert.page.locator("#detail-body a.source-link").count() == 0
    path = payload_of(exports["inert"])["source_links"]["capability:alpha-cap"]["path"]
    assert path in _text(inert.page, "#detail-body .source")
    assert not inert.page.eval_on_selector_all(
        "[href]", "els => els.filter(e => !e.getAttribute('href').startsWith('#')).length"
    )


def test_ac_0034_unsafe_code_points_show_as_escapes(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["hostile"])
    payload = payload_of(exports["hostile"])
    seen = ""
    for key in _VIEWS:
        item.go(f"view={key}")
        _expand_all(item.page)
        for node in payload["nodes"]:
            item.go(f"view={key}&node=" + node["id"].replace(":", "%3A"))
            seen += "".join(item.page.evaluate(_TEXT_NODES))
    assert _unsafe_present(seen) == []
    raw = json.dumps(payload, ensure_ascii=False)
    expected = {f"[U+{ord(c):04X}]" for c in _unsafe_present(raw)}
    assert expected and all(code in seen for code in expected)


def test_ac_0035_labels_come_from_the_closed_set(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    rendered = {"label-group": set(), "label-state": set(), "label-trust": set()}
    for name in (
        "hostile",
        "cycle",
        "multiple",
        "self_reference",
        "dangling",
        "retired",
        "kind_mismatch",
        "out_of_type",
        "unparseable",
        "coordinated",
        "related",
    ):
        item = opener(exports[name])
        payload = payload_of(exports[name])
        for key in _VIEWS:
            item.go(f"view={key}")
            for node in payload["nodes"]:
                item.go(f"view={key}&node=" + node["id"].replace(":", "%3A"))
                for cls in rendered:
                    rendered[cls] |= set(
                        item.page.eval_on_selector_all(f".{cls}", "e => e.map(x => x.textContent)")
                    )
        item.close()
    assert rendered["label-group"] <= set(_GROUPS) and len(rendered["label-group"]) == 9
    assert rendered["label-state"] <= set(_STATES) and len(rendered["label-state"]) == 8
    assert rendered["label-trust"] <= set(_TRUST) and len(rendered["label-trust"]) == 3


def test_ac_0036_no_network_and_no_policy_violation(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name in ("hostile", "latest"):
        item = opener(exports[name])
        _visit_everything(item, payload_of(exports[name]))
        assert set(item.requests) == {item.url}, item.requests
        assert item.page.evaluate("window.__csp") == []
        assert not [m for m in item.console if "Content Security Policy" in m or "Refused" in m]
        assert item.errors == []


# ---------------------------------------------------------------------------
# AC-0037 .. AC-0046: views and detail
# ---------------------------------------------------------------------------


def test_ac_0037_summary_strip_equals_the_summary(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name, root in (("mixed", _FIXTURES / "mixed"), ("cycle", _FIXTURES / "negative/cycle")):
        item = opener(exports[name])
        summary = _query(root, "--operation", "summary")["summary"]
        shown = {
            li.locator(".stat-label").inner_text(): int(li.locator(".stat-value").inner_text())
            for li in item.page.locator("#summary-list li").all()
        }
        assert shown == {
            "Outstanding items": summary["outstanding"],
            "Refused edges": sum(summary["refused_edges_by_state"].values()),
            "Parentless intents": summary["parentless_intents"],
            "Intents": sum(summary["intents_by_level"].values()),
            "Briefs": summary["briefs"],
            "Specs": summary["specs"],
        }


_TREE_JS = """() => {
  const row = (li) => li.querySelector(':scope > .row');
  const idOf = (li) => row(li).querySelector('a.row-link').dataset.node;
  const roots = Array.from(document.querySelectorAll('#list > ul > li')).map(idOf);
  const all = Array.from(document.querySelectorAll('#list li.item')).map(idOf);
  const out = {};
  for (const li of document.querySelectorAll('#list li.item')) {
    const t = (s) => { const e = row(li).querySelector(s); return e ? e.textContent : null; };
    out[idOf(li)] = { level: t('.f-level'), kind: t('.f-kind'), status: t('.f-status'),
      refused: t('.f-refused'), state: t('.label-state'),
      kids: Array.from(li.querySelectorAll(':scope > ul.subtree > li.item')).map(idOf) };
  }
  return { roots, all, out };
}"""


def _resolved_parent(record: dict[str, Any]) -> str | None:
    edge = record["parent_edge"]
    return edge["to"] if edge and "to" in edge and "state" not in edge else None


def test_ac_0038_tree_lists_every_intent_once(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name in ("mixed", "dangling", "cycle", "terminality"):
        item = opener(exports[name])
        payload = payload_of(exports[name])
        records = payload["records"]
        _expand_all(item.page)
        tree = item.page.evaluate(_TREE_JS)
        assert sorted(tree["all"]) == sorted(records) and len(tree["all"]) == len(set(tree["all"]))
        roots = sorted(i for i, r in records.items() if _resolved_parent(r) is None)
        assert tree["roots"] == roots
        for node_id, record in records.items():
            shown = tree["out"][node_id]
            assert shown["kids"] == sorted(record["children"])
            assert shown["level"] == (record["level"] or "unrecorded")
            assert shown["kind"] == (record["kind"] or None)
            assert shown["status"] == record["status"]
            edge = record["parent_edge"]
            if edge and "state" in edge:
                assert shown["refused"] and shown["state"] == edge["state"]
            else:
                assert shown["refused"] is None
    refused = payload_of(exports["dangling"])
    assert any(
        r["parent_edge"] and "state" in r["parent_edge"] for r in refused["records"].values()
    )


def _chain_ids(page: Page, li_selector: str) -> list[list[str]]:
    return page.eval_on_selector_all(  # type: ignore[no-any-return]
        li_selector,
        "els => els.map(l => Array.from(l.querySelectorAll('.chain a.node-link, .chain .outside .value')).map(a => a.dataset.node || a.textContent))",
    )


def test_ac_0039_outstanding_lists_every_item_under_its_chain(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name in ("mixed", "terminality", "coordinated"):
        item = opener(exports[name])
        payload = payload_of(exports[name])
        item.go("view=outstanding")
        out = payload["outstanding"]
        sections = item.page.locator("#list section")
        assert sections.count() == 2
        terminal = 0
        for index, group in enumerate(("placed", "no_parent")):
            shown = item.page.eval_on_selector_all(
                f"#list section:nth-of-type({index + 1}) > ul > li > .row a.row-link",
                "els => els.map(e => e.dataset.node)",
            )
            assert shown == [i["id"] for i in out[group]]
            for entry in out[group]:
                lists = (
                    [entry["ancestors"]]
                    if "ancestors" in entry
                    else [p["ancestors"] for p in entry["placements"]]
                )
                terminal += sum(1 for chain in lists for a in chain if a["terminal"])
        assert item.page.locator("#list .mark-terminal").count() == terminal
        if name == "terminality":
            assert terminal > 0
        placed = item.page.locator("#list section:nth-of-type(1) > ul > li").all()
        for li, entry in zip(placed, out["placed"], strict=True):
            if "ancestors" in entry and entry["ancestors"]:
                ids = li.locator(".chain a.node-link").evaluate_all(
                    "e => e.map(x => x.dataset.node)"
                )
                assert ids == [a["id"] for a in reversed(entry["ancestors"])]


def test_ac_0040_refused_view_lists_every_refused_edge(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name, root in (
        ("hostile", _FIXTURES / "hostile"),
        ("cycle", _FIXTURES / "negative/cycle"),
    ):
        item = opener(exports[name])
        payload = payload_of(exports[name])
        item.go("view=refused")
        expected = [e for e in payload["edges"] if "state" in e]
        assert len(expected) == sum(
            _query(root, "--operation", "summary")["summary"]["refused_edges_by_state"].values()
        )
        rows = item.page.locator("#list li.edge").all()
        assert len(rows) == len(expected)
        assert item.page.inner_text("#view-count").startswith(str(len(expected)))
        for row, edge in zip(rows, expected, strict=True):
            text = row.inner_text()
            assert edge["from"] in text and edge["field"] in text
            assert row.locator(".label-state").inner_text() == edge["state"]
            value = row.locator(".pointer-value").inner_text()
            assert value == nav._escape_display(edge.get("value", value))


def test_ac_0041_parentless_view_lists_intents_without_a_resolved_parent(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name, root in (("mixed", _FIXTURES / "mixed"), ("cycle", _FIXTURES / "negative/cycle")):
        item = opener(exports[name])
        item.go("view=parentless")
        expected = _search_ids(root, {"parentless": True})
        assert _ids(item.page) == expected
        assert expected == sorted(
            i
            for i, r in payload_of(exports[name])["records"].items()
            if _resolved_parent(r) is None
        )


def test_ac_0042_intent_detail_shows_facts_and_groups(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["related"])
    payload = payload_of(exports["related"])
    item.go("view=tree&node=capability%3Aalpha-cap")
    detail = item.page.locator("#detail-body")
    record, node = (
        payload["records"]["capability:alpha-cap"],
        next(n for n in payload["nodes"] if n["id"] == "capability:alpha-cap"),
    )
    assert item.page.inner_text("#detail-heading") == "capability:alpha-cap"
    facts = {
        r.locator("dt").inner_text(): r.locator("dd").inner_text()
        for r in detail.locator(".fact").all()
    }
    assert facts["Heading"] == node["heading"] and facts["Path"] == record["path"]
    assert facts["Level"] == record["level"] and facts["Status"] == record["status"]
    assert "Kind" in facts and "Source" in facts
    assert detail.locator("h3.label-group").all_inner_texts() == [
        "Parent",
        "Child intents",
        "Briefs",
        "Specs",
        "Delivery relations",
        "Delivery diagnostics",
        "Related, written here",
        "Related, written elsewhere",
    ]
    assert (
        "intent:bravo-feat" in detail.inner_text()
        and "brief:bravo-delivery" in detail.inner_text()
    )
    elsewhere = detail.locator("section.group").nth(7)
    assert "intent:zulu-rel" in elsewhere.inner_text()
    item.go("view=tree&node=outcome%3Acharlie-out")
    assert (
        "intent:bravo-feat" in item.page.locator("#detail-body section.group").nth(7).inner_text()
    )
    item.go("view=tree&node=capability%3Aalpha-cap")
    item.go("view=tree&node=intent%3Azulu-rel")
    here = item.page.locator("#detail-body section.group").nth(6)
    assert "capability:alpha-cap" in here.inner_text()
    item.go("view=tree&node=intent%3Abravo-feat")
    parent = item.page.locator("#detail-body section.group").nth(0)
    assert (
        "capability:alpha-cap" in parent.inner_text()
        and "pointer_unchecked" in parent.inner_text()
    )
    deliver = opener(exports["coordinated"])
    deliver.go("view=tree&node=intent%3Aalpha-feat")
    relations = deliver.page.locator("#detail-body section.group").nth(4).inner_text()
    assert "coordinated-delivery" in relations and "delivery_contract" in relations
    assert "spec:alpha-spec" in relations
    refused = opener(exports["hostile"])
    refused.go("view=tree&node=intent%3Ahostile-child")
    related = refused.page.locator("#detail-body section.group").nth(6)
    assert "unparseable" in related.inner_text() and "refused" in related.inner_text()
    pointer = opener(exports["hostile"])
    pointer.go("view=tree&node=intent%3Ahostile-pointer")
    assert "refused" in pointer.page.locator("#detail-body section.group").nth(0).inner_text()


def test_ac_0043_brief_and_spec_detail(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["coordinated"])
    payload = payload_of(exports["coordinated"])
    for node_id in ("brief:alpha-brief", "spec:alpha-spec"):
        item.go("view=outstanding&node=" + node_id.replace(":", "%3A"))
        node = next(n for n in payload["nodes"] if n["id"] == node_id)
        detail = item.page.locator("#detail-body")
        assert item.page.inner_text("#detail-heading") == node_id
        facts = {
            r.locator("dt").inner_text(): r.locator("dd").inner_text()
            for r in detail.locator(".fact").all()
        }
        assert (
            facts["Path"] == node["path"]
            and facts["Status"] == node["status"]
            and "Source" in facts
        )
        pointers = detail.locator("section.group").nth(0)
        assert pointers.locator("h3").inner_text() == "Pointers"
        for edge in (e for e in payload["edges"] if e["from"] == node_id):
            assert edge["field"] in pointers.inner_text()
        relations = detail.locator("section.group").nth(1)
        assert relations.locator("h3").inner_text() == "Delivery relations"
        assert "coordinated-delivery" in relations.inner_text()
        assert "delivery_contract" in relations.inner_text()


def test_ac_0044_legend_names_every_group(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["mixed"])
    for fragment in (
        "view=tree",
        "view=tree&node=capability%3Aalpha-cap",
        "view=tree&node=brief%3Abravo-delivery",
    ):
        item.go(fragment)
        legend = item.page.locator("#detail-legend")
        assert legend.locator("dt.label-group").all_inner_texts() == _GROUPS
        for row in legend.locator(".fact").all():
            assert row.locator("dd").inner_text().strip()


def test_ac_0045_out_of_scope_targets_are_plain_text(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["from_related"])
    payload = payload_of(exports["from_related"])
    in_scope = {n["id"] for n in payload["nodes"]}
    item.go("view=tree&node=intent%3Abravo-feat")
    detail = item.page.locator("#detail-body")
    outside = detail.locator(".outside")
    shown = {o.locator(".value").inner_text() for o in outside.all()}
    assert {"capability:alpha-cap", "outcome:charlie-out"} <= shown
    for target in shown:
        assert target not in in_scope
        assert (
            "outside this export" in detail.locator(".outside", has_text=target).first.inner_text()
        )
        assert detail.locator("a", has_text=target).count() == 0
    links = item.page.eval_on_selector_all("a[data-node]", "e => e.map(x => x.dataset.node)")
    assert set(links) <= in_scope
    item.go("view=tree&node=spec%3Abravo-spec")
    assert "brief:bravo-delivery" in item.page.locator("#detail-body .outside").first.inner_text()


def test_ac_0046_scoped_export_shows_banner_and_whole_corpus_counts(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["from_mixed"])
    assert "capability:alpha-cap" in item.page.inner_text("#scope-banner")
    assert "whole corpus" in item.page.inner_text("#summary-scope")
    whole = _query(_FIXTURES / "mixed", "--operation", "summary")["summary"]
    assert item.page.locator("#summary-list li").first.locator(".stat-value").inner_text() == str(
        whole["outstanding"]
    )
    plain = opener(exports["mixed"])
    assert plain.page.locator("#scope-banner").is_hidden()


def test_ac_0069_scoped_tree_has_one_root(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["from_mixed"])
    _expand_all(item.page)
    tree = item.page.evaluate(_TREE_JS)
    assert tree["roots"] == ["capability:alpha-cap"]
    assert sorted(tree["all"]) == sorted(payload_of(exports["from_mixed"])["records"])
    assert len(tree["all"]) == len(set(tree["all"])) == 2


def test_ac_0070_scoped_refused_view_lists_every_stated_edge(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["from_hostile"])
    payload = payload_of(exports["from_hostile"])
    expected = [e for e in payload["edges"] if "state" in e]
    assert expected
    item.go("view=refused")
    assert item.page.locator("#list li.edge").count() == len(expected)
    assert item.page.inner_text("#view-count").startswith(str(len(expected)))


def test_ac_0071_scoped_search_lists_only_in_scope_intents(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["from_mixed"])
    in_scope = set(payload_of(exports["from_mixed"])["records"])
    root = _FIXTURES / "mixed"
    for fragment, selectors in (
        ("q=a", {"text": "a"}),
        ("level=feature", {"level": "feature"}),
        ("level=capability", {"level": "capability"}),
        ("status=Draft", {"exact_status": "Draft"}),
        ("status=Accepted", {"exact_status": "Accepted"}),
    ):
        item.go("view=tree&" + fragment)
        expected = [i for i in _search_ids(root, selectors) if i in in_scope]
        if expected:
            assert _ids(item.page) == expected, fragment
        else:
            assert item.page.locator("#list a.row-link").count() == 0
        assert set(_ids(item.page)) <= in_scope


# ---------------------------------------------------------------------------
# AC-0047 .. AC-0055: filters and states
# ---------------------------------------------------------------------------


def test_ac_0047_detail_states_delivery_was_unavailable(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["incomplete"])
    for node_id in ("capability:alpha-cap", "brief:bravo-delivery"):
        item.go("view=tree&node=" + node_id.replace(":", "%3A"))
        detail = item.page.locator("#detail-body")
        assert "delivery mapping was unavailable" in detail.inner_text().lower()
        assert "resource_limit" in detail.inner_text()
        titles = detail.locator("h3.label-group").all_inner_texts()
        assert "Delivery relations" not in titles and "Delivery diagnostics" not in titles


def test_ac_0048_search_and_filters_match_the_query(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    root = _FIXTURES / "mixed"
    item = opener(exports["mixed"])
    page = item.page
    page.locator("#filter-q").click()
    page.keyboard.type("bravo")
    assert _ids(page) == _search_ids(root, {"text": "bravo"})
    page.locator("#filter-q").fill("Alpha CAPABILITY")
    assert _ids(page) == _search_ids(root, {"text": "Alpha CAPABILITY"}) and _ids(page)
    page.locator("#filter-q").fill("")
    for select, key, values in (
        ("#filter-level", "level", ["capability", "feature", "unrecorded"]),
        ("#filter-kind", "kind", ["outcome", "opportunity"]),
        ("#filter-status", "exact_status", ["Draft", "Accepted", "Fulfilled — 2026-01-01"]),
    ):
        for value in values:
            page.select_option(select, value)
            assert _ids(page) == _search_ids(root, {key: value}), (key, value)
            assert _ids(page)
        page.select_option(select, "")
    page.select_option("#filter-level", "feature")
    page.select_option("#filter-status", "Draft")
    assert _ids(page) == _search_ids(root, {"level": "feature", "exact_status": "Draft"})


def test_ac_0049_empty_filter_result_names_filters_and_clears(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["mixed"])
    page = item.page
    page.locator("#filter-q").fill("zzzz-nothing")
    page.select_option("#filter-level", "feature")
    message = _text(page, "#list .empty")
    assert "zzzz-nothing" in message and "level feature" in message
    page.get_by_role("button", name="Clear filters").click()
    assert (
        page.locator("#filter-q").input_value() == ""
        and page.locator("#filter-level").input_value() == ""
    )
    assert len(_ids(page)) > 0 and page.locator("#list .empty").count() == 0
    assert "q=" not in page.evaluate("location.hash")


def test_ac_0050_outstanding_unavailable_states_reason(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["incomplete"])
    item.go("view=outstanding")
    text = _text(item.page, "#list").lower()
    assert "delivery mapping was unavailable" in text and "resource_limit" in text
    assert item.page.locator("#list li").count() == 0


def test_ac_0051_empty_corpus_states_no_intents(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["empty"])
    assert "no intents were found" in _text(item.page, "#list").lower()


def test_ac_0052_no_refused_edge_states_every_pointer_resolved(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["mixed"])
    item.go("view=refused")
    assert "every pointer resolved" in _text(item.page, "#list").lower()


def test_ac_0053_all_parented_states_every_intent_has_a_parent(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name in ("empty", "all_parented"):
        item = opener(exports[name])
        item.go("view=parentless")
        assert "every intent has a parent" in _text(item.page, "#list").lower()


def test_ac_0054_damaged_data_shows_one_alert_and_no_view(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name in ("bad_json", "bad_schema"):
        item = opener(exports[name])
        page = item.page
        assert page.locator("[role=alert]").count() == 1
        text = page.locator("[role=alert]").inner_text().lower()
        assert "damaged" in text and "export" in text
        for selector in (
            "nav",
            "#view-list a",
            "#list *",
            "button",
            "#summary-list li",
            "input",
            "select",
        ):
            assert page.locator(selector).count() == 0, selector
        assert item.errors == []


def test_ac_0055_scripting_disabled_shows_notice(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["mixed"], js=False)
    assert "needs javascript" in item.page.inner_text("body").lower()


# ---------------------------------------------------------------------------
# AC-0056 .. AC-0064: accessibility
# ---------------------------------------------------------------------------


def _tab_to(page: Page, predicate: str, limit: int = 400) -> None:
    for _ in range(limit):
        page.keyboard.press("Tab")
        if page.evaluate(
            f"(() => {{ const e = document.activeElement; return !!e && ({predicate}); }})()"
        ):
            return
    raise AssertionError(f"keyboard never reached: {predicate}")


def test_ac_0056_keyboard_alone_reaches_every_function(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = opener(exports["related"])
    page = item.page
    page.evaluate("document.body.focus()")
    for key, name in (
        ("outstanding", "Outstanding"),
        ("refused", "Refused edges"),
        ("parentless", "Parentless"),
        ("tree", "Tree"),
    ):
        _tab_to(page, f"e.dataset.view === '{key}'")
        page.keyboard.press("Enter")
        page.wait_for_function(
            "n => document.getElementById('view-heading').textContent === n", arg=name
        )
        assert page.evaluate("document.activeElement.id") == "view-heading"
        page.evaluate("document.body.focus()")
    _tab_to(page, "e.id === 'filter-q'")
    page.keyboard.type("bravo")
    assert _ids(page) == _search_ids(_related_root(exports), {"text": "bravo"})
    for _ in range(5):
        page.keyboard.press("Backspace")
    assert page.locator("#filter-q").input_value() == ""
    _tab_to(page, "e.id === 'filter-level'")
    page.keyboard.press("f")
    value = page.locator("#filter-level").input_value()
    assert value == "feature" and _ids(page) == _search_ids(
        _related_root(exports), {"level": value}
    )
    page.select_option("#filter-level", "")
    page.evaluate("document.body.focus()")
    _tab_to(page, "e.classList.contains('toggle')")
    assert page.evaluate("document.activeElement.getAttribute('aria-expanded')") == "false"
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.getAttribute('aria-expanded')") == "true"
    page.keyboard.press("Space")
    assert page.evaluate("document.activeElement.getAttribute('aria-expanded')") == "false"
    page.keyboard.press("Enter")
    _tab_to(page, "e.classList.contains('row-link') && e.dataset.node === 'capability:alpha-cap'")
    page.keyboard.press("Enter")
    page.wait_for_function(
        "() => document.getElementById('detail-heading').textContent === 'capability:alpha-cap'"
    )
    assert page.evaluate("document.activeElement.id") == "detail-heading"
    _tab_to(page, "e.dataset.node === 'intent:bravo-feat' && !!e.closest('#detail-body')")
    page.keyboard.press("Enter")
    page.wait_for_function(
        "() => document.getElementById('detail-heading').textContent === 'intent:bravo-feat'"
    )
    page.go_back()
    page.wait_for_function(
        "() => document.getElementById('detail-heading').textContent === 'capability:alpha-cap'"
    )
    assert "view=tree" in page.evaluate("location.hash")
    page.go_back()
    page.wait_for_function(
        "() => document.getElementById('detail-heading').textContent === 'Details'"
    )
    assert page.inner_text("#view-heading") == "Tree"
    page.go_forward()
    page.wait_for_function(
        "() => document.getElementById('detail-heading').textContent === 'capability:alpha-cap'"
    )


def _related_root(exports: dict[str, pathlib.Path]) -> pathlib.Path:
    return exports["related"].parent.parent / "related"


_FOCUS_INFO = """() => {
  const e = document.activeElement;
  if (!e || e === document.body) return null;
  if (e.__seen) return { repeat: true };
  e.__seen = true;
  const r = e.getBoundingClientRect();
  const cs = getComputedStyle(e);
  const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
  let p = e.parentElement, bg = 'rgb(255, 255, 255)';
  while (p) { const c = getComputedStyle(p).backgroundColor;
    const m = c.match(/[\\d.]+/g);
    if (m && (m.length === 3 || parseFloat(m[3]) > 0.99)) { bg = c; break; } p = p.parentElement; }
  return { repeat: false, tag: e.tagName, text: (e.textContent || '').slice(0, 30), width: r.width,
    height: r.height, outlineStyle: cs.outlineStyle, outlineWidth: parseFloat(cs.outlineWidth),
    outlineColor: cs.outlineColor, bg, hit: hit === e || e.contains(hit),
    visible: r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth };
}"""


def _sweep(page: Page, limit: int = 300) -> list[dict[str, Any]]:
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


def _busy_page(opener: Any, exports: dict[str, pathlib.Path], **kw: Any) -> Opened:
    item = opener(exports["related"], **kw)
    _expand_all(item.page)
    item.go("view=tree&node=capability%3Aalpha-cap")
    return item


def test_ac_0057_focus_is_visible_and_moves_to_headings(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = _busy_page(opener, exports)
    page = item.page
    stops = _sweep(page)
    assert len(stops) > 20
    for stop in stops:
        assert stop["outlineStyle"] == "solid" and stop["outlineWidth"] >= 3, stop
    page.locator('a[data-view="refused"]').click()
    page.wait_for_function("() => document.activeElement.id === 'view-heading'")
    assert page.evaluate("getComputedStyle(document.activeElement).outlineStyle") == "solid"
    page.locator('a[data-view="tree"]').click()
    page.locator("#list a.row-link", has_text="intent:bravo-feat").first.click()
    page.wait_for_function("() => document.activeElement.id === 'detail-heading'")
    assert page.evaluate("getComputedStyle(document.activeElement).outlineStyle") == "solid"


@pytest.mark.parametrize("width", [320, 1280])
def test_ac_0058_focused_elements_are_never_hidden(
    opener: Any, exports: dict[str, pathlib.Path], width: int
) -> None:
    item = _busy_page(opener, exports, width=width, height=700)
    stops = _sweep(item.page)
    assert len(stops) > 20
    for stop in stops:
        assert stop["hit"] and stop["visible"], stop


@pytest.mark.parametrize("width", [320, 1280])
def test_ac_0059_targets_are_at_least_24_px(
    opener: Any, exports: dict[str, pathlib.Path], width: int
) -> None:
    for name in ("related", "hostile"):
        item = opener(exports[name], width=width)
        payload = payload_of(exports[name])
        for key in _VIEWS:
            item.go(f"view={key}&node=" + payload["nodes"][0]["id"].replace(":", "%3A"))
            _expand_all(item.page)
            small = item.page.evaluate(
                """() => Array.from(document.querySelectorAll('a[href], button, input, select, summary'))
                  .map(e => [e, e.getBoundingClientRect()])
                  .filter(([e, r]) => r.width > 0 && (r.width < 24 || r.height < 24))
                  .map(([e, r]) => e.outerHTML.slice(0, 80) + ' ' + r.width + 'x' + r.height)"""
            )
            assert small == [], (name, key, small)


def test_ac_0060_no_horizontal_scroll_at_320(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    for name in ("related", "hostile", "latest", "coordinated"):
        item = opener(exports[name], width=320, height=800)
        payload = payload_of(exports[name])
        for key in _VIEWS:
            for node in payload["nodes"][:6]:
                item.go(f"view={key}&node=" + node["id"].replace(":", "%3A"))
                _expand_all(item.page)
                wide = item.page.evaluate(
                    "[document.documentElement.scrollWidth, document.documentElement.clientWidth]"
                )
                assert wide[0] <= wide[1], (name, key, node["id"], wide)


def test_ac_0061_landmarks_and_one_h1(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    for name in ("mixed", "empty", "hostile", "incomplete"):
        page = opener(exports[name]).page
        for tag in ("h1", "header", "nav", "main"):
            assert page.locator(tag).count() == 1, (name, tag)


def test_ac_0062_live_region_announces_view_and_count(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    root = _FIXTURES / "mixed"
    page = opener(exports["mixed"]).page
    assert page.locator("#live").get_attribute("aria-live") == "polite"
    page.locator('a[data-view="parentless"]').click()
    expected = len(_search_ids(root, {"parentless": True}))
    assert f"Parentless view, {expected} intents" in _live(page, "Parentless view")
    page.locator('a[data-view="refused"]').click()
    assert "Refused edges view, 0" in _live(page, "Refused edges view")
    page.locator('a[data-view="tree"]').click()
    page.locator("#filter-q").click()
    page.keyboard.type("bravo")
    count = len(_search_ids(root, {"text": "bravo"}))
    assert _live(page, "Tree view") == f"Tree view, {count} intent" + ("" if count == 1 else "s")
    page.select_option("#filter-level", "capability")
    count = len(_search_ids(root, {"text": "bravo", "level": "capability"}))
    assert f"Tree view, {count} " in _live(page, "Tree view")


def _accessible_names(page: Page) -> list[tuple[str, str]]:
    cdp = page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("Accessibility.enable")
    doc = cdp.send("DOM.getDocument", {"depth": 0})
    found = cdp.send(
        "DOM.querySelectorAll",
        {"nodeId": doc["root"]["nodeId"], "selector": "a[href], button, input, select"},
    )
    names: list[str] = []
    for node_id in found["nodeIds"]:
        tree = cdp.send(
            "Accessibility.getPartialAXTree", {"nodeId": node_id, "fetchRelatives": False}
        )
        node = next(n for n in tree["nodes"] if not n.get("ignored"))
        names.append(node["name"]["value"])
    labels = page.evaluate(
        """() => {
          const visible = (n) => Array.from(n.childNodes).map((c) =>
            c.nodeType === 3 ? c.textContent
            : (c.classList && c.classList.contains('visually-hidden') ? '' : visible(c))).join('');
          return Array.from(document.querySelectorAll('a[href], button, input, select')).map((e) =>
            (e.tagName === 'INPUT' || e.tagName === 'SELECT') ? e.labels[0].textContent : visible(e).trim());
        }"""
    )
    assert len(names) == len(labels)
    cdp.detach()
    return list(zip(names, labels, strict=True))


def test_ac_0063_names_contain_visible_labels(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    item = _busy_page(opener, exports)
    page = item.page
    pairs = _accessible_names(page)
    assert len(pairs) > 25
    for name, label in pairs:
        assert name.strip() and label.strip(), (name, label)
        assert _squash(label) in _squash(name), (name, label)
    toggles = page.evaluate(
        """() => Array.from(document.querySelectorAll('button.toggle')).map(
          (b) => b.closest('li').querySelector('a.row-link').dataset.node)"""
    )
    toggle_names = [n for n, _ in pairs if "Children (" in n]
    assert len(toggle_names) == len(toggles) > 0
    for name, node_id in zip(toggle_names, toggles, strict=True):
        assert node_id in name


def _contrast_report(page: Page) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    raw = page.evaluate(
        """() => {
          const parse = (c) => c.match(/[\\d.]+/g).map(Number);
          const bgOf = (el) => { for (let p = el; p; p = p.parentElement) {
              const m = parse(getComputedStyle(p).backgroundColor);
              if (m.length === 3 || m[3] > 0.99) return m.slice(0, 3); }
            return [255, 255, 255]; };
          const texts = []; const controls = [];
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) {
            const n = walker.currentNode; const el = n.parentElement;
            if (!n.textContent.trim() || el.closest('select, option, script, noscript')) continue;
            if (!el.getClientRects().length) continue;
            const cs = getComputedStyle(el);
            if (cs.visibility !== 'visible' || el.closest('.visually-hidden')) continue;
            texts.push([n.textContent.trim().slice(0, 30), parse(cs.color).slice(0, 3), bgOf(el)]);
          }
          for (const el of document.querySelectorAll('input, select')) {
            const cs = getComputedStyle(el);
            controls.push([el.id, parse(cs.color).slice(0, 3), bgOf(el)]);
          }
          return { texts, controls };
        }"""
    )
    rows = [
        (f"{label}", _ratio(tuple(fg), tuple(bg)))
        for label, fg, bg in raw["texts"] + raw["controls"]
    ]  # type: ignore[arg-type]
    return rows, []


@pytest.mark.parametrize(
    ("scheme", "theme"), [("light", None), ("dark", None), ("light", "dark"), ("dark", "light")]
)
def test_ac_0064_contrast_in_both_themes(
    opener: Any, exports: dict[str, pathlib.Path], scheme: str, theme: str | None
) -> None:
    effective = theme or scheme
    for name in ("hostile", "related"):
        item = opener(exports[name], scheme=scheme, theme=theme)
        page = item.page
        assert page.evaluate("getComputedStyle(document.body).backgroundColor") == (
            "rgb(15, 17, 23)" if effective == "dark" else "rgb(244, 245, 249)"
        )
        payload = payload_of(exports[name])
        checked = 0
        for key in _VIEWS:
            for node in payload["nodes"][:3]:
                item.go(f"view={key}&node=" + node["id"].replace(":", "%3A"))
                _expand_all(page)
                rows, _ = _contrast_report(page)
                checked += len(rows)
                low = [r for r in rows if r[1] < 4.5]
                assert not low, (name, key, effective, low[:5])
        assert checked > 200
        stops = _sweep(page)
        assert stops
        for stop in stops:
            ratio = _ratio(_rgb(stop["outlineColor"]), _rgb(stop["bg"]))
            assert ratio >= 3, (stop, ratio)


# ---------------------------------------------------------------------------
# Review round 1: relations on non-intent nodes, focus return, wording, and cues
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
    page = opener(path).page
    for node, group in (("opportunity:beta-feat", 4), ("brief:beta-brief", 1)):
        page.evaluate("id => { location.hash = 'view=tree&node=' + encodeURIComponent(id); }", node)
        page.wait_for_function("id => document.getElementById('detail-heading').textContent === id", arg=node)
        relations = page.locator("#detail-body section.group").nth(group)
        assert relations.locator("h3").inner_text() == "Delivery relations"
        assert relations.locator('a[data-node="opportunity:beta-feat"]').count() == 1
        assert "outside this export" not in relations.inner_text()
    page.locator('#detail-body a[data-node="opportunity:beta-feat"]').first.click()
    page.wait_for_function(
        "() => document.getElementById('detail-heading').textContent === 'opportunity:beta-feat'"
    )


def test_back_to_list_returns_focus_to_the_selected_row(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    page = opener(exports["related"]).page
    # bravo-feat sits under a collapsed capability: its row does not exist yet.
    page.evaluate("location.hash = 'view=tree&node=intent%3Abravo-feat'")
    page.wait_for_function("() => document.activeElement.id === 'detail-heading'")
    assert _ids(page).count("intent:bravo-feat") == 0
    button = page.locator("#detail-body button.back-link")
    box = button.bounding_box()
    assert box is not None and box["width"] >= 24 and box["height"] >= 24
    assert button.text_content().strip() == "Back to list (row intent:bravo-feat)"
    assert button.locator(".visually-hidden").count() == 1
    button.click()
    assert page.evaluate("document.activeElement.dataset.node") == "intent:bravo-feat"
    assert page.evaluate("document.activeElement.getAttribute('aria-current')") == "true"
    toggle = page.locator("#list li.item", has=page.locator('a[data-node="capability:alpha-cap"]')).first.locator("button.toggle").first
    assert toggle.get_attribute("aria-expanded") == "true"
    # Keyboard: Enter on the focused button does the same from a fresh selection.
    page.evaluate("location.hash = 'view=tree&node=outcome%3Acharlie-out'")
    page.wait_for_function("() => document.activeElement.id === 'detail-heading'")
    page.locator("#detail-body button.back-link").focus()
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.dataset.node") == "outcome:charlie-out"
    # A filtered flat list holds the row directly; a row the filter hides falls back to the heading.
    page.evaluate("location.hash = 'view=tree&q=bravo&node=intent%3Abravo-feat'")
    page.wait_for_function("() => document.activeElement.id === 'detail-heading'")
    page.locator("#detail-body button.back-link").click()
    assert page.evaluate("document.activeElement.dataset.node") == "intent:bravo-feat"
    page.evaluate("location.hash = 'view=tree&q=bravo&node=outcome%3Acharlie-out'")
    page.wait_for_function("() => document.activeElement.id === 'detail-heading'")
    page.locator("#detail-body button.back-link").click()
    assert page.evaluate("document.activeElement.id") == "view-heading"


def test_detail_panel_stays_in_view_on_wide_screens_only(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    wide = _busy_page(opener, exports, width=1280, height=400).page
    style = wide.evaluate("(() => { const c = getComputedStyle(document.querySelector('.detail')); return [c.position, c.top, c.overflowY]; })()")
    assert style == ["sticky", "0px", "auto"]
    assert wide.evaluate("document.documentElement.scrollHeight > innerHeight")
    wide.evaluate("window.scrollTo(0, 300)")
    lower = wide.evaluate(
        "Array.from(document.querySelectorAll('#list a.row-link')).find(a => a.getBoundingClientRect().top > 200 && a.getAttribute('aria-current') !== 'true').dataset.node"
    )
    wide.locator(f'#list a.row-link[data-node="{lower}"]').click()
    wide.wait_for_function("() => document.activeElement.id === 'detail-heading'")
    rect = wide.evaluate("(() => { const r = document.querySelector('.detail').getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; })()")
    assert 0 <= rect[0] < 1 and rect[1] <= rect[2] + 1, rect
    heading = wide.evaluate("(() => { const r = document.getElementById('detail-heading').getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; })()")
    assert heading[0] >= 0 and heading[1] <= heading[2], heading
    narrow = _busy_page(opener, exports, width=320, height=700).page
    assert narrow.evaluate("getComputedStyle(document.querySelector('.detail')).position") == "static"


def test_state_and_trust_badges_keep_their_key_and_point_to_their_explanation(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    page = opener(exports["hostile"]).page
    page.evaluate("location.hash = 'view=refused'")
    page.wait_for_selector("#list .label-state")
    pairs = page.evaluate(
        """() => Array.from(document.querySelectorAll('#list .label-state, #list .label-trust')).map((c) => {
          const d = document.getElementById(c.getAttribute('aria-describedby'));
          return [c.textContent, d ? d.textContent : null, c.getAttribute('title')]; })"""
    )
    assert pairs and all(key in _STATES + _TRUST and text and text == title for key, text, title in pairs)
    legend = page.evaluate(
        "Array.from(document.querySelectorAll('#detail-legend dt .chip')).map(c => [c.className, c.textContent])"
    )
    assert [k for _, k in legend] == _STATES + _TRUST
    assert page.locator("#detail-legend dt.label-state, #detail-legend dt.label-trust").count() == 0


def test_status_chip_has_a_cue_that_is_not_colour(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    page = opener(exports["mixed"]).page
    cue = page.evaluate(
        """() => { const s = document.querySelector('#list .f-status'); const l = document.querySelector('#list .f-level');
          return [getComputedStyle(s).borderTopStyle, getComputedStyle(s, '::before').content,
                  getComputedStyle(l).borderTopStyle]; }"""
    )
    assert cue == ["dashed", '"status "', "none"]


def test_childless_tree_rows_line_up_with_rows_that_have_a_toggle(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    page = opener(exports["mixed"]).page
    lefts = page.evaluate(
        """() => Array.from(document.querySelectorAll('#list > ul > li.item > .row > a.row-link'))
          .map(a => Math.round(a.getBoundingClientRect().left))"""
    )
    kids = page.evaluate("document.querySelectorAll('#list > ul > li.item > .row > button.toggle').length")
    assert len(lefts) > kids > 0 and len(set(lefts)) == 1, lefts


def test_outstanding_says_filters_apply_to_intents_before_any_filter(
    opener: Any, exports: dict[str, pathlib.Path]
) -> None:
    page = opener(exports["mixed"]).page
    page.evaluate("location.hash = 'view=outstanding'")
    page.wait_for_selector("#list .subsection")
    notes = page.locator("#list > p.note").all_inner_texts()
    assert notes == ["Filters apply to intents only. Briefs and specs are hidden while a filter is set."]
    page.select_option("#filter-level", "capability")
    assert page.locator("#list > p.note").all_inner_texts() == notes


def test_page_text_is_written_for_readers(opener: Any, exports: dict[str, pathlib.Path]) -> None:
    item = opener(exports["related"])
    page = item.page
    assert re.fullmatch(
        r"Read-only snapshot generated \d{4}-\d{2}-\d{2} \d{2}:\d{2} UTC\. "
        r"Record text in this file is shown as plain text and is never run\.",
        page.inner_text("#meta"),
    )
    provenance = payload_of(exports["related"])["provenance"]
    assert "untrusted" in provenance["untrusted_data"] and provenance["generated_at"].count(":") == 3
    page.evaluate("location.hash = 'view=tree&node=capability%3Aalpha-cap'")
    face = page.evaluate(
        "getComputedStyle(Array.from(document.querySelectorAll('#detail-body .fact')).find(r => r.querySelector('dt').textContent === 'Heading').querySelector('dd span')).fontFamily"
    )
    assert "monospace" not in face
    assert "Parent intent field" in page.inner_text("#detail-legend")


def test_startup_render_failure_shows_the_alert_and_logs_the_error(
    opener: Any, exports: dict[str, pathlib.Path], tmp_path: pathlib.Path
) -> None:
    broken = _rewrite(
        exports["mixed"], tmp_path / "broken.html", lambda p: {**p, "records": {"intent:bad": 1}}
    )
    item = opener(broken)
    assert "damaged" in item.page.inner_text("#main .alert")
    assert any("could not render" in line for line in item.console)
