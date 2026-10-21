"""Contract tests for the offline view export: payload, parity, and command.

The payload is built from the same derivation and query builders ``query``
uses, so every check compares the exported data block with ``run_query`` and
the derivation over the same corpus.  Exports are written under ``tmp_path``.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"
_HERE = pathlib.Path(__file__).resolve().parent
_FIXTURES = _HERE / "fixtures"
_MIXED = _FIXTURES / "mixed"
_NEG = _FIXTURES / "negative"
_HOSTILE = _FIXTURES / "hostile"


def _load(path: pathlib.Path, module_name: str) -> Any:
    """Load a navigate-intents script by path under a pack-and-skill-unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_export_payload_nav")
view = _load(_SCRIPTS / "intent_view.py", "core_navigate_intents_export_payload_view")

sys.path.insert(0, str(_HERE))
from navigate_intents_fixture_builders import (  # noqa: E402
    build_input_too_large_corpus,
    build_unsafe_input_corpus,
)

_DATA_BLOCK = re.compile(
    r'<script type="application/json" id="intent-data">(.*?)</script>', re.DOTALL
)
_KEYS = [
    "schema", "scope", "provenance", "summary", "records", "outstanding",
    "nodes", "edges", "source_links", "dependencies", "readiness",
]

# Corpora on which a whole-operation failure applies: no payload exists.
_WHOLE_OPERATION_FAILURES = frozenset(
    {
        "negative/duplicate_identity",
        "negative/duplicate_slug",
        "negative/malformed_record_bad_slug",
        "negative/malformed_record_utf8",
    }
)
_CLEAN_CORPORA = sorted(
    {
        path.parent
        for path in _FIXTURES.glob("**/expected-outstanding.json")
        if path.parent.relative_to(_FIXTURES).as_posix() not in _WHOLE_OPERATION_FAILURES
    }
)


def _norm(value: Any) -> Any:
    """Round-trip through JSON so tuples and lists compare as the data block does."""
    return json.loads(json.dumps(value))


def _data(html: str) -> dict[str, Any]:
    """Return the parsed data block of an exported file."""
    blocks = _DATA_BLOCK.findall(html)
    assert len(blocks) == 1
    return json.loads(blocks[0])  # type: ignore[no-any-return]


def _export(
    capsys: pytest.CaptureFixture[str],
    root: pathlib.Path,
    dest: pathlib.Path,
    *extra: str,
) -> tuple[dict[str, Any], int]:
    """Run ``main(["export", ...])``; return the stdout object and exit code."""
    dest.mkdir(parents=True, exist_ok=True)
    capsys.readouterr()
    code = nav.main(["export", "--root", str(root), "--destination", str(dest), *extra])
    out = capsys.readouterr().out
    return json.loads(out), code


def _exported(
    capsys: pytest.CaptureFixture[str],
    root: pathlib.Path,
    dest: pathlib.Path,
    *extra: str,
) -> tuple[dict[str, Any], str]:
    """Export successfully; return the data block and the raw HTML."""
    result, code = _export(capsys, root, dest, *extra)
    assert code == 0, result
    html = pathlib.Path(result["path"]).read_text(encoding="utf-8")
    return _data(html), html


def _query(root: pathlib.Path, *args: str, **seams: Any) -> tuple[dict[str, Any], int]:
    result, code = nav.run_query(root, ["query", *args], **seams)
    return result, code  # type: ignore[return-value]


def _copy(src: pathlib.Path, tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "corpus"
    shutil.copytree(src, root)
    return root


# ---------------------------------------------------------------------------
# AC-0001 .. AC-0005: payload shape and parity over every clean corpus
# ---------------------------------------------------------------------------


def test_clean_corpus_discovery_is_not_vacuous() -> None:
    names = {p.relative_to(_FIXTURES).as_posix() for p in _CLEAN_CORPORA}
    assert {"mixed", "hostile", "terminality", "coordinated_delivery"} <= names
    assert len(names) >= 20


@pytest.mark.parametrize(
    "corpus", _CLEAN_CORPORA, ids=lambda p: p.relative_to(_FIXTURES).as_posix()
)
def test_payload_matches_query_over_clean_corpus(
    corpus: pathlib.Path, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload, html = _exported(capsys, corpus, tmp_path / "out")

    # AC-0001
    assert len(_DATA_BLOCK.findall(html)) == 1
    assert list(payload) == _KEYS
    assert payload["schema"] == "intent-navigation.view.v1"
    assert payload["scope"] == {"from": None}

    # AC-0002
    summary, code = _query(corpus, "--operation", "summary")
    assert code == 0
    assert payload["summary"] == _norm(summary["summary"])

    # AC-0003
    graph = nav._load_graph_mod().derive(corpus)
    live = sorted(n["id"] for n in graph["nodes"] if n["type"] == "intent")
    assert sorted(payload["records"]) == live
    for node_id in live:
        rec, rc = _query(corpus, "--operation", "record", "--id", node_id)
        assert rc == 0
        assert payload["records"][node_id] == _norm(rec["record"]), node_id

    # AC-0004
    out, oc = _query(corpus, "--operation", "outstanding")
    if oc == 0:
        assert payload["outstanding"] == _norm(
            {"placed": out["placed"], "no_parent": out["no_parent"]}
        )
    else:
        assert payload["outstanding"] == {
            "available": False,
            "reason": out["error"]["observed"]["reason"],
            "limit": out["error"]["observed"]["limit"],
        }

    # AC-0005
    assert payload["nodes"] == _norm(graph["nodes"])
    assert payload["edges"] == _norm(graph["edges"])
    assert set(payload["source_links"]) == {n["id"] for n in graph["nodes"]}


# ---------------------------------------------------------------------------
# AC-0006: incomplete delivery
# ---------------------------------------------------------------------------


def _incomplete(_root: pathlib.Path) -> dict[str, Any]:
    return {
        "complete": False,
        "relations": [],
        "diagnostics": [{"code": "delivery-resource-limit", "limit": 7}],
    }


def test_incomplete_delivery_exports_unavailable_outstanding(tmp_path: pathlib.Path) -> None:
    payload = nav.build_view_payload(_MIXED, None, _delivery_provider=_incomplete)
    query, code = _query(
        _MIXED, "--operation", "outstanding", _delivery_provider=_incomplete
    )
    assert code == 1 and query["error"]["code"] == "delivery_incomplete"
    observed = query["error"]["observed"]
    assert payload["outstanding"] == {
        "available": False, "reason": observed["reason"], "limit": observed["limit"],
    }
    assert payload["outstanding"]["reason"] == "resource_limit"

    result, rc = nav.run_export(
        _MIXED, str(tmp_path), None, None, _delivery_provider=_incomplete
    )
    assert rc == 0 and result["status"] == "ok"


# ---------------------------------------------------------------------------
# AC-0007 / AC-0008: --from
# ---------------------------------------------------------------------------


def test_from_accepts_every_identity_form(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for i, identity in enumerate(("capability:alpha-cap", "alpha-cap", "CAP-0001")):
        payload, _ = _exported(capsys, _MIXED, tmp_path / f"o{i}", "--from", identity)
        assert payload["scope"] == {"from": "capability:alpha-cap"}


def test_from_refusals(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    result, code = _export(capsys, _MIXED, tmp_path / "a", "--from", "no-such-intent")
    assert code == 1 and result["error"]["code"] == "not_found"
    # A brief is not a live intent.
    result, code = _export(capsys, _MIXED, tmp_path / "b", "--from", "brief:bravo-delivery")
    assert code == 1 and result["error"]["code"] == "not_found"
    result, code = _export(
        capsys, _NEG / "ambiguous_ordinal", tmp_path / "c", "--from", "FEAT-0001"
    )
    assert code == 1 and result["error"]["code"] == "ambiguous_identity"
    assert not list((tmp_path / "a").iterdir()) and not list((tmp_path / "c").iterdir())


def _edge_keys(edges: list[dict[str, Any]]) -> list[tuple[str, str, str | None]]:
    return [(e["from"], e["field"], e.get("to")) for e in edges]


def test_from_scope_on_mixed_with_a_related_edge_leaving_the_subtree(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy(_MIXED, tmp_path)
    bravo = root / "docs/product/intents/FEAT-0001-bravo-feat.md"
    text = bravo.read_text(encoding="utf-8")
    anchor = "- **Parent intent:** capability:alpha-cap\n"
    assert anchor in text
    bravo.write_text(
        text.replace(anchor, anchor + "- **Related intents:** outcome:charlie-out\n"),
        encoding="utf-8",
    )

    payload, _ = _exported(capsys, root, tmp_path / "out", "--from", "alpha-cap")

    # Hand-derived from the fixture files: alpha-cap, its child bravo-feat, the
    # brief placed under alpha-cap, and the two specs that name bravo-feat
    # (bravo-spec by Discovery and by its Brief, charlie-spec by Discovery).
    assert payload["scope"] == {"from": "capability:alpha-cap"}
    assert [n["id"] for n in payload["nodes"]] == [
        "capability:alpha-cap", "intent:bravo-feat", "brief:bravo-delivery",
        "spec:bravo-spec", "spec:charlie-spec",
    ]
    assert sorted(payload["records"]) == ["capability:alpha-cap", "intent:bravo-feat"]
    # Derivation order: parent edges, then Related edges, then spec pointers.
    assert _edge_keys(payload["edges"]) == [
        ("intent:bravo-feat", "Parent intent", "capability:alpha-cap"),
        ("intent:bravo-feat", "Related intents", "outcome:charlie-out"),
        ("brief:bravo-delivery", "Parent intent", "capability:alpha-cap"),
        ("spec:bravo-spec", "Brief", "brief:bravo-delivery"),
        ("spec:bravo-spec", "Discovery", "intent:bravo-feat"),
        ("spec:charlie-spec", "Discovery", "intent:bravo-feat"),
    ]
    # The related edge's target lies outside the scope, so it is not a node.
    assert "outcome:charlie-out" not in {n["id"] for n in payload["nodes"]}

    query, code = _query(root, "--operation", "outstanding", "--from", "alpha-cap")
    assert code == 0
    assert payload["outstanding"] == _norm(
        {"placed": query["placed"], "no_parent": query["no_parent"]}
    )
    whole, _ = _query(root, "--operation", "summary")
    assert payload["summary"] == _norm(whole["summary"])  # stays whole-corpus


def test_from_a_leaf_includes_only_what_it_owns(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload, _ = _exported(capsys, _MIXED, tmp_path / "out", "--from", "golf-new")
    # golf-new has no children or briefs; spec:golf-new names it by Discovery.
    assert [n["id"] for n in payload["nodes"]] == ["intent:golf-new", "spec:golf-new"]
    assert _edge_keys(payload["edges"]) == [("spec:golf-new", "Discovery", "intent:golf-new")]
    assert list(payload["records"]) == ["intent:golf-new"]


# ---------------------------------------------------------------------------
# AC-0009: provenance and no path leakage
# ---------------------------------------------------------------------------


def test_provenance_and_no_absolute_paths(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _copy(_MIXED, tmp_path)
    dest = tmp_path / "elsewhere"
    payload, html = _exported(capsys, root, dest)
    prov = payload["provenance"]
    assert set(prov) == {"generated_at", "counts", "untrusted_data", "commit"}
    assert prov["counts"] == {"intents": 9, "briefs": 3, "specs": 3}
    assert "untrusted data" in prov["untrusted_data"]
    assert prov["commit"] is None
    for leaked in (str(root), str(root.resolve()), str(dest), str(dest.resolve())):
        assert leaked not in html


# ---------------------------------------------------------------------------
# AC-0010 / AC-0011: the command through main()
# ---------------------------------------------------------------------------


def test_main_ok_object_and_exit_zero(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dest = tmp_path / "out"
    dest.mkdir()
    code = nav.main(
        ["export", "--root", str(_MIXED), "--destination", str(dest), "--name", "view.html"]
    )
    captured = capsys.readouterr()
    assert code == 0 and captured.err == ""
    assert captured.out.count("\n") > 1 and captured.out.endswith("}\n")
    result = json.loads(captured.out)
    written = dest.resolve() / "view.html"
    assert result == {
        "schema": "intent-navigation.export.v1",
        "status": "ok",
        "path": str(written),
        "bytes": written.stat().st_size,
        "scope": {"from": None},
        "readiness": {"checked": False, "reason": "not_requested"},
    }


def test_main_error_object_and_exit_one(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result, code = _export(capsys, _MIXED, tmp_path / "out", "--from", "nope")
    assert code == 1
    assert list(result) == ["schema", "status", "error"]
    assert result["schema"] == "intent-navigation.export.v1" and result["status"] == "error"
    assert set(result["error"]) == {"code", "message", "limits", "observed"}
    assert isinstance(result["error"]["limits"], dict)
    assert isinstance(result["error"]["observed"], dict)


@pytest.mark.parametrize(
    "argv",
    [
        ["export"],
        ["export", "--root", "x", "--bogus"],
        ["export", "--root"],
    ],
)
def test_main_exit_two_on_parser_rejection(argv: list[str]) -> None:
    assert nav.main(argv) == 2


# ---------------------------------------------------------------------------
# AC-0012: nothing on standard error
# ---------------------------------------------------------------------------


def _run_export(
    script: pathlib.Path, root: pathlib.Path, dest: pathlib.Path, *extra: str
) -> subprocess.CompletedProcess[bytes]:
    dest.mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, str(script), "export", "--root", str(root),
         "--destination", str(dest), *extra],
        capture_output=True, check=False, timeout=120,
    )


def test_stderr_is_empty_for_a_non_git_root(tmp_path: pathlib.Path) -> None:
    root = _copy(_MIXED, tmp_path)
    done = _run_export(_SCRIPTS / "navigate_intents.py", root, tmp_path / "out")
    assert done.returncode == 0 and done.stderr == b""
    assert json.loads(done.stdout)["status"] == "ok"


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_stderr_is_empty_for_a_git_root(tmp_path: pathlib.Path) -> None:
    root = _copy(_MIXED, tmp_path)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "init", "-q", str(root)], check=True, env=env, capture_output=True)
    done = _run_export(_SCRIPTS / "navigate_intents.py", root, tmp_path / "out")
    assert done.returncode == 0 and done.stderr == b""
    assert json.loads(done.stdout)["status"] == "ok"


def test_stderr_is_empty_on_a_refusal(tmp_path: pathlib.Path) -> None:
    done = _run_export(
        _SCRIPTS / "navigate_intents.py", _MIXED, tmp_path / "out", "--from", "nope"
    )
    assert done.returncode == 1 and done.stderr == b""


# ---------------------------------------------------------------------------
# AC-0013: corpus failures refuse with query's codes
# ---------------------------------------------------------------------------


def _query_code(root: pathlib.Path) -> str:
    result, code = _query(root, "--operation", "summary")
    assert code == 1
    return result["error"]["code"]  # type: ignore[no-any-return]


@pytest.mark.parametrize(
    ("corpus", "expected"),
    [
        (_NEG / "duplicate_identity", "duplicate_identity"),
        (_NEG / "malformed_record_bad_slug", "malformed_record"),
    ],
    ids=["duplicate_identity", "malformed_record"],
)
def test_committed_corpus_failures(
    corpus: pathlib.Path, expected: str, tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert _query_code(corpus) == expected
    result, code = _export(capsys, corpus, tmp_path / "out")
    assert code == 1 and result["error"]["code"] == expected
    assert not list((tmp_path / "out").iterdir())


def test_generated_corpus_failures(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for name, builder, expected in (
        ("unsafe", build_unsafe_input_corpus, "unsafe_input"),
        ("large", build_input_too_large_corpus, "input_too_large"),
    ):
        root = builder(tmp_path / name)
        assert _query_code(root) == expected
        result, code = _export(capsys, root, tmp_path / f"out-{name}")
        assert code == 1 and result["error"]["code"] == expected
        assert not list((tmp_path / f"out-{name}").iterdir())


def test_resolver_unavailable_without_the_bundled_resolver(tmp_path: pathlib.Path) -> None:
    scripts = tmp_path / "scripts"
    shutil.copytree(
        _SCRIPTS, scripts,
        ignore=shutil.ignore_patterns("__pycache__", "intent_delivery_relations.py"),
    )
    dest = tmp_path / "out"
    done = _run_export(scripts / "navigate_intents.py", _MIXED, dest)
    assert done.returncode == 1 and done.stderr == b""
    assert json.loads(done.stdout)["error"]["code"] == "resolver_unavailable"
    assert not list(dest.iterdir())


# ---------------------------------------------------------------------------
# Hostile corpus and data-block escaping (AC-0031's inputs; T4 reuses them)
# ---------------------------------------------------------------------------


def test_hostile_corpus_derives_and_carries_the_hostile_values() -> None:
    graph = nav._load_graph_mod().derive(_HOSTILE)
    text = json.dumps(graph, ensure_ascii=False)
    for needle in (
        "</script><script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
        '"><svg onload=alert(1)>',
        "\u202e",  # right-to-left override
        "\u2066",  # left-to-right isolate
        "\u200b",  # zero-width space
        "\u200f",  # right-to-left mark
    ):
        assert needle in text, needle


def test_hostile_export_keeps_markup_inside_the_escaped_data_block(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload, html = _exported(capsys, _HOSTILE, tmp_path / "out")
    block = _DATA_BLOCK.findall(html)[0]
    assert not any(ch in block for ch in "<>&\u2028\u2029")
    assert "\\u003c/script\\u003e\\u003cscript\\u003e" in block
    outside = _DATA_BLOCK.sub("", html)
    for needle in ("</script><script>", "<img", "javascript:", "<svg", "onerror"):
        assert needle not in outside
    graph = nav._load_graph_mod().derive(_HOSTILE)
    assert payload["nodes"] == _norm(graph["nodes"])


def test_build_html_escapes_line_separators_and_markup() -> None:
    payload = {"schema": "x", "v": "a\u2028b\u2029c<d>e&f</script>"}
    html = view.build_html(payload)
    block = _DATA_BLOCK.findall(html)[0]
    assert not any(ch in block for ch in "<>&\u2028\u2029")
    assert all(esc in block for esc in ("\\u2028", "\\u2029", "\\u003c", "\\u003e", "\\u0026"))
    assert json.loads(block) == payload


# ---------------------------------------------------------------------------
# Dependencies member
# ---------------------------------------------------------------------------

# SHA-256 of each pre-existing payload member's canonical JSON, recorded by running the
# navigator as committed before the dependencies member existed over a copy of each
# fixture (generated_at excluded). Canonical form: json.dumps(value, sort_keys=True,
# separators=(",", ":"), ensure_ascii=False).
_GOLDEN = {
    "mixed": {
        "schema": "a7358164ceb4876f507dea10e2dcfce650962d9d05a4dfe9705400b6279ce4b3",
        "scope": "1470350dec7071fced53d4628441c14660cc01b051a7ef97f72dbe88e3dc0cc7",
        "provenance": "87f7e7c39ceb126bc81b1f1fe65b9fdad6332ff15e0f3a8a5b5509c35f5a0256",
        "summary": "fbe60056ad39814d81ff99dc5213b66c8a6a882d07bea2efa14005d9f586a2f6",
        "records": "0ec3064fdd08bedf8890a11544ac75299eee7baa88aef009008038270abc8825",
        "outstanding": "3ef153aa16953aa14d8489922ed642441c94a83fba027368e073b44306ac11c0",
        "nodes": "d1672ff6f62443d4dd08bf3fdc8315201b3ffead73f0c181c80228ce39fb0fe1",
        "edges": "e03387e40ac999e95e664e44e33e20a15bff9d36daa5f2820e92e9cf782f3c9e",
        "source_links": "265fabef77066b94ff830e89f4b13ed3af669c56bc20cbec071fd613b71adaab"
    },
    "dependency": {
        "schema": "a7358164ceb4876f507dea10e2dcfce650962d9d05a4dfe9705400b6279ce4b3",
        "scope": "1470350dec7071fced53d4628441c14660cc01b051a7ef97f72dbe88e3dc0cc7",
        "provenance": "6d3d63d002ce89dbb03a4bb1a92ada84898f6d2ae1c338e949ef5afbfffdf49a",
        "summary": "9f2b452e8a719273c577754f5d3a7249b606d0332e1bf867e19ab478c5f6affc",
        "records": "e58ba90b7ffddbdc2efc854f3b1964e305d31e3f58be6d9013bba7db59d17181",
        "outstanding": "89646595935a5e0d8d1e0a4482b079e7f550192c08a41d01a35be9f455ace9c7",
        "nodes": "4e677bde1279b5bd012aa557112f57dcb560d1e0d77736bbf4abf7a5e6ad110b",
        "edges": "66378f8ab857fb875cfbcb4964e4d97c7f4e671df017b25aa72c86406a690cb9",
        "source_links": "026194806312e92a5b8bbea67bd1349206e1d3e10c2088bca11805c422d95274"
    }
}
_DEP = _FIXTURES / "dependency"
_DEP_MANIFEST = json.loads((_DEP / "expected-dependencies.json").read_text(encoding="utf-8"))


def _expected_edge(m: dict[str, Any]) -> dict[str, Any]:
    """The full edge record a manifest edge stands for."""
    return {
        "from": m["from"], "to": m["to"], "field": "Depends on", "trust_class": "pointer_unchecked",
        "basis": {"field": "Depends on", "values": [
            {"value": v, "form": f, "position": p} for v, f, p in m["values"]
        ]},
    }


def _expected_diag(m: dict[str, Any]) -> dict[str, Any]:
    """The full pointer-diagnostic record a manifest entry stands for."""
    diag = {"from": m["from"], "field": "Depends on", "value": m["value"], "form": m["form"],
            "position": m["position"], "state": m["state"], "trust_class": "pointer_unchecked"}
    if "reissued_as" in m:
        diag["reissued_as"] = m["reissued_as"]
    return diag


def _without_owner(value: Any) -> Any:
    """Return *value* with every ``owner`` member removed at any depth."""
    if isinstance(value, dict):
        return {k: _without_owner(v) for k, v in value.items() if k != "owner"}
    if isinstance(value, list):
        return [_without_owner(v) for v in value]
    return value


def _digest(value: Any) -> str:
    """SHA-256 of the canonical JSON of *value*."""
    import hashlib

    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_dependencies_member_holds_the_whole_corpus_records_in_record_order(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    payload, _ = _exported(capsys, _DEP, tmp_path / "out")
    dependencies = payload["dependencies"]
    assert list(dependencies) == ["edges", "diagnostics"]
    assert dependencies["edges"] == [_expected_edge(m) for m in _DEP_MANIFEST["edges"]]
    pointer = [d for d in dependencies["diagnostics"] if "from" in d]
    cycles = [d for d in dependencies["diagnostics"] if "from" not in d]
    assert pointer == [_expected_diag(m) for m in _DEP_MANIFEST["pointer_diagnostics"]]
    assert [c["members"] for c in cycles] == _DEP_MANIFEST["cycles"]
    # Record order: pointer diagnostics first, then cycles.
    assert dependencies["diagnostics"] == pointer + cycles


def test_dependencies_member_with_from_holds_exactly_the_linked_set(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    whole, _ = _exported(capsys, _DEP, tmp_path / "whole")
    scoped, _ = _exported(capsys, _DEP, tmp_path / "scoped", "--from", "capability:root-a")
    linked = {
        "capability:root-a", "intent:alpha", "intent:bravo", "intent:charlie", "intent:india",
        "intent:juliet", "intent:kilo", "capability:root-b", "outcome:quebec", "opportunity:romeo",
    }
    pairs = {(e["from"], e["to"]) for e in scoped["dependencies"]["edges"]}
    assert pairs == {
        (e["from"], e["to"]) for e in whole["dependencies"]["edges"]
        if e["from"] in linked and e["to"] in linked
    }
    assert ("intent:juliet", "intent:kilo") in pairs
    assert ("intent:delta", "intent:echo") not in pairs
    members = [d["members"] for d in scoped["dependencies"]["diagnostics"] if "members" in d]
    assert ["intent:india", "intent:juliet", "intent:kilo"] in members
    assert all("intent:hotel" not in m for m in members)
    assert len(scoped["dependencies"]["edges"]) < len(whole["dependencies"]["edges"])
    assert len(scoped["dependencies"]["diagnostics"]) < len(whole["dependencies"]["diagnostics"])
    # Surviving records keep the whole corpus's relative order.
    for key in ("edges", "diagnostics"):
        kept = [r for r in whole["dependencies"][key] if r in scoped["dependencies"][key]]
        assert kept == scoped["dependencies"][key]


@pytest.mark.parametrize("corpus", ["mixed", "dependency"])
def test_other_members_equal_the_golden_recorded_before_dependencies(
    corpus: str, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / corpus
    shutil.copytree(_FIXTURES / corpus, root)
    payload, _ = _exported(capsys, root, tmp_path / "out")
    payload["provenance"].pop("generated_at")
    # The golden predates the `owner` member, so compare with every `owner` removed.
    digests = {
        k: _digest(_without_owner(v))
        for k, v in payload.items()
        if k not in ("dependencies", "readiness")
    }
    assert digests == _GOLDEN[corpus]
