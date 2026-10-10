"""Regression tests for defects the specialist reviews found in the navigator.

Each test asserts the repaired property itself, through the interface an
agent uses, so it fails on the code that had the defect.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys

import pytest

sys.dont_write_bytecode = True

_PACK = pathlib.Path(__file__).resolve().parents[3]
_SCRIPTS = _PACK / ".apm" / "skills" / "navigate-intents" / "scripts"
_HERE = pathlib.Path(__file__).resolve().parent
_FIXTURES = _HERE / "fixtures"
_MIXED = _FIXTURES / "mixed"
_TERMINALITY = _FIXTURES / "terminality"


def _load(path: pathlib.Path, module_name: str):  # type: ignore[no-untyped-def]
    """Load a navigate-intents script by path under a pack-and-skill-unique name."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


nav = _load(_SCRIPTS / "navigate_intents.py", "core_navigate_intents_specialist_nav")
resolver = _load(
    _SCRIPTS / "intent_delivery_relations.py",
    "core_navigate_intents_specialist_resolver",
)

sys.path.insert(0, str(_HERE))
from navigate_intents_fixture_builders import (  # noqa: E402
    build_fifo_corpus,
    build_hardlink_corpus,
    build_input_too_large_corpus,
    build_symlinked_dir_corpus,
    build_symlinked_file_corpus,
)


def _query(root: pathlib.Path, *args: str, **seams):  # type: ignore[no-untyped-def]
    """Run one query through `run_query`; return (result, exit code)."""
    return nav.run_query(root, ["query", *args], **seams)


def _ids(result: dict) -> list[str]:  # type: ignore[type-arg]
    """Every item id in a JSON outstanding result."""
    return sorted(item["id"] for item in result["placed"] + result["no_parent"])


def _copy(src: pathlib.Path, tmp_path: pathlib.Path) -> pathlib.Path:
    """Copy a committed corpus into *tmp_path* and return the copy's root."""
    root = tmp_path / "corpus"
    shutil.copytree(src, root)
    return root


def _main(*argv: str) -> tuple[int, str]:
    """Call the CLI entry point the skill documents; return (exit code, stdout)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        code = nav.main(list(argv))
    return code, out.getvalue()


def _intent_file(root: pathlib.Path, name: str, slug: str, status: str, parent: str) -> None:
    """Write one feature intent into a corpus."""
    (root / "docs" / "product" / "intents" / name).write_text(
        f"# Feature: {slug}\n\n- **Slug:** {slug}\n- **Status:** {status}\n"
        f"- **Level:** feature\n- **Parent intent:** {parent}\n\n## Outcome\n",
        encoding="utf-8",
    )


# --- Terminality reaches the outstanding view for every type -------------------


def test_every_terminal_status_word_is_left_out_of_outstanding() -> None:
    """Live artifacts at every terminal word of every type stay out of the outstanding set."""
    result, code = _query(_TERMINALITY, "--operation", "outstanding")
    assert code == 0
    assert _ids(result) == [
        "brief:term-brief-open", "capability:term-root",
        "intent:term-open", "spec:term-spec-open",
    ]


# --- The documented CLI entry point --------------------------------------------


def test_main_returns_json_and_exit_zero_on_ok() -> None:
    """`main` writes the JSON envelope to stdout and exits 0 on `status: ok`."""
    code, out = _main("query", "--root", str(_MIXED), "--operation", "summary")
    assert code == 0
    assert json.loads(out)["status"] == "ok"


def test_main_forwards_from_and_scopes_outstanding() -> None:
    """`main` forwards `--from`, so the documented route returns the scoped set."""
    code, out = _main(
        "query", "--root", str(_MIXED), "--operation", "outstanding",
        "--from", "capability:alpha-cap",
    )
    assert code == 0
    assert _ids(json.loads(out)) == [
        "brief:bravo-delivery", "capability:alpha-cap", "intent:bravo-feat",
        "spec:bravo-spec", "spec:charlie-spec",
    ]


def test_main_exits_one_on_a_status_error() -> None:
    """`main` exits 1 and still writes an envelope when the query is refused."""
    code, out = _main("query", "--root", str(_MIXED), "--operation", "nonsense")
    assert code == 1
    assert json.loads(out)["error"]["code"] == "unknown_operation"


def test_main_exits_two_when_the_parser_rejects_the_arguments() -> None:
    """`main` exits 2 with no envelope when a required argument is missing."""
    code, out = _main("query", "--operation", "summary")
    assert code == 2
    assert out == ""


def test_non_utf8_argument_is_refused_as_invalid_query_with_no_traceback() -> None:
    """A non-UTF-8 argv byte returns a typed refusal through the real process, not a traceback."""
    proc = subprocess.run(
        [
            os.fsencode(sys.executable), os.fsencode(_SCRIPTS / "navigate_intents.py"),
            b"query", b"--root", os.fsencode(_MIXED), b"--operation", b"record",
            b"--id", b"\xff",
        ],
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 1
    assert proc.stderr == b""
    assert json.loads(proc.stdout)["error"]["code"] == "invalid_query"


# --- Deep chains do not exhaust the interpreter stack --------------------------


def test_a_chain_deeper_than_the_recursion_limit_still_answers(tmp_path: pathlib.Path) -> None:
    """A parent chain longer than Python's recursion limit returns normal results."""
    root = tmp_path / "deep"
    (root / "docs" / "product" / "intents").mkdir(parents=True)
    depth = sys.getrecursionlimit() + 200
    for i in range(depth):
        parent = "none" if i == 0 else f"intent:link-{i - 1:05d}"
        _intent_file(root, f"FEAT-{i:05d}-link.md", f"link-{i:05d}", "Draft", parent)
    limits = {"max_intents": 10 * depth, "max_edges": 10 * depth, "max_result_bytes": 1 << 26}
    for args in (
        ("--operation", "tree"),
        ("--operation", "tree", "--format", "text"),
        ("--operation", "outstanding", "--format", "text"),
    ):
        result, code = _query(root, *args, _limits=limits)
        assert code == 0, (args, result if isinstance(result, dict) else "")
    text, _ = _query(root, "--operation", "tree", "--format", "text", _limits=limits)
    lines = text.splitlines()
    assert len(lines) == depth
    assert lines[-1].startswith("  " * (depth - 1) + f"intent:link-{depth - 1:05d} · ")


# --- Spec placement chains carry their values ---------------------------------


def test_spec_placement_chains_reach_the_root_with_terminal_flags() -> None:
    """Each spec placement lists its full chain to the root, terminal parents marked."""
    result, _ = _query(_TERMINALITY, "--operation", "outstanding")
    item = next(i for i in result["placed"] + result["no_parent"] if i["id"] == "spec:term-spec-open")
    by_field = {p["pointer_field"]: p["ancestors"] for p in item["placements"]}
    assert by_field["Brief"] == [
        {"id": "brief:term-brief-open", "terminal": False},
        {"id": "capability:term-root", "terminal": False},
    ]
    assert by_field["Discovery"] == [
        {"id": "intent:term-withdrawn", "terminal": True},
        {"id": "capability:term-root", "terminal": False},
    ]


# --- Outstanding byte limits sit at the boundary -------------------------------


def _non_ascii_corpus(tmp_path: pathlib.Path) -> pathlib.Path:
    """A terminality copy whose outstanding intent status holds non-ASCII text."""
    root = _copy(_TERMINALITY, tmp_path)
    path = root / "docs" / "product" / "intents" / "FEAT-0001-term-open.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("- **Status:** Draft", "- **Status:** Draft — révisé"),
        encoding="utf-8",
    )
    return root


def test_outstanding_text_limit_counts_utf8_bytes_at_the_boundary(tmp_path: pathlib.Path) -> None:
    """Text output exactly at the byte limit passes; one byte less refuses naming --from."""
    root = _non_ascii_corpus(tmp_path)
    text, _ = _query(root, "--operation", "outstanding", "--format", "text")
    size = len(text.encode("utf-8"))
    assert size > len(text), "the corpus must hold a non-ASCII value"
    _, ok = _query(root, "--operation", "outstanding", "--format", "text", _limits={"max_result_bytes": size})
    assert ok == 0
    refused, code = _query(
        root, "--operation", "outstanding", "--format", "text", _limits={"max_result_bytes": size - 1}
    )
    assert code == 1
    assert refused["error"]["code"] == "result_too_large"
    assert refused["error"]["limits"]["bounded_route"] == "--from"


def test_outstanding_json_limit_counts_compact_utf8_bytes(tmp_path: pathlib.Path) -> None:
    """JSON output is counted compactly in UTF-8: its own size passes, one byte less refuses."""
    root = _non_ascii_corpus(tmp_path)
    full, _ = _query(root, "--operation", "outstanding")
    # Counted independently: compact separators, UTF-8, no ASCII escaping.
    # generated_at keeps its length between runs, so the size carries over.
    size = len(json.dumps(full, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))
    assert size > len(json.dumps(full, separators=(",", ":"), ensure_ascii=False))
    _, ok = _query(root, "--operation", "outstanding", _limits={"max_result_bytes": size})
    assert ok == 0
    refused, code = _query(root, "--operation", "outstanding", _limits={"max_result_bytes": size - 1})
    assert code == 1
    assert refused["error"]["limits"]["bounded_route"] == "--from"


def test_outstanding_ignores_the_intent_and_edge_counts() -> None:
    """`outstanding` is exempt from the intent and edge limits that bound `tree`."""
    result, code = _query(_MIXED, "--operation", "outstanding", _limits={"max_intents": 0, "max_edges": 0})
    assert code == 0
    assert result["status"] == "ok"


# --- delivery_incomplete carries reason and limit ------------------------------


def test_delivery_incomplete_carries_unsafe_reason() -> None:
    """An incomplete resolver with no limit diagnostic refuses with reason `unsafe`."""
    def _unsafe(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return {"complete": False, "relations": [], "diagnostics": []}

    result, code = _query(_MIXED, "--operation", "outstanding", _delivery_provider=_unsafe)
    assert code == 1
    assert result["error"]["code"] == "delivery_incomplete"
    assert result["error"]["observed"] == {"reason": "unsafe", "limit": None}
    assert "placed" not in result and "no_parent" not in result


def test_delivery_incomplete_carries_resource_limit_from_a_lowered_limit() -> None:
    """A real resolver run under a lowered limit refuses with reason `resource_limit` and the limit."""
    def _lowered(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return resolver.resolve_repository(root, limits={"files": 1})

    snapshot = _lowered(_MIXED)
    limit_diag = next(d for d in snapshot["diagnostics"] if d["code"] == "delivery-resource-limit")
    result, code = _query(_MIXED, "--operation", "outstanding", _delivery_provider=_lowered)
    assert code == 1
    assert result["error"]["observed"] == {"reason": "resource_limit", "limit": limit_diag["limit"]}


def test_integrity_failure_takes_precedence_over_delivery_incomplete(tmp_path: pathlib.Path) -> None:
    """An intent over the size limit refuses `outstanding` with `input_too_large`, not delivery."""
    root = build_input_too_large_corpus(tmp_path)

    def _unsafe(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        return {"complete": False, "relations": [], "diagnostics": []}

    result, code = _query(root, "--operation", "outstanding", _delivery_provider=_unsafe)
    assert code == 1
    assert result["error"]["code"] == "input_too_large"


# --- Brief and spec status escaping in outstanding text ------------------------


def test_outstanding_text_escapes_brief_and_spec_status(tmp_path: pathlib.Path) -> None:
    """A placed brief's and spec's status print with bidi controls and tabs escaped."""
    root = _copy(_TERMINALITY, tmp_path)
    brief = root / "docs" / "product" / "briefs" / "BRIEF-0001-term-brief-open.md"
    brief.write_text(
        brief.read_text(encoding="utf-8").replace("- **Status:** Executing", "- **Status:** Executing ‮x\ty"),
        encoding="utf-8",
    )
    spec = root / "docs" / "specs" / "term-spec-open" / "spec.md"
    spec.write_text(
        spec.read_text(encoding="utf-8").replace("- **Status:** Implementing", "- **Status:** Implementing ⁦z\tw"),
        encoding="utf-8",
    )
    text, code = _query(root, "--operation", "outstanding", "--format", "text")
    assert code == 0
    assert "‮" not in text and "⁦" not in text and "\t" not in text
    brief_line = next(ln for ln in text.splitlines() if ln.strip().startswith("brief:term-brief-open · "))
    spec_line = next(ln for ln in text.splitlines() if ln.strip().startswith("spec:term-spec-open · "))
    assert brief_line.strip() == "brief:term-brief-open · " + nav._escape_display("Executing ‮x\ty")
    assert spec_line.strip() == "spec:term-spec-open · " + nav._escape_display("Implementing ⁦z\tw")


# --- Confinement refusals come from the derivation's own check -----------------


@pytest.mark.parametrize(
    "builder",
    [build_symlinked_file_corpus, build_symlinked_dir_corpus, build_fifo_corpus, build_hardlink_corpus],
    ids=["symlinked-file", "symlinked-dir", "fifo", "hardlink"],
)
def test_confinement_refusal_names_the_offending_repository_path(builder, tmp_path: pathlib.Path) -> None:  # type: ignore[no-untyped-def]
    """An unsafe file refuses with a message naming its repository-relative path."""
    root = builder(tmp_path)
    result, code = _query(root, "--operation", "summary")
    assert code == 1
    assert result["error"]["code"] == "unsafe_input"
    message = result["error"]["message"]
    assert "docs/product/intents" in message
    assert str(tmp_path) not in message


def test_an_unexpected_derivation_failure_does_not_echo_its_exception_text(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A crash inside the derivation refuses with a fixed message, not the exception's own text."""
    graph_mod = nav._load_graph_mod()

    def _boom(root: pathlib.Path) -> dict:  # type: ignore[type-arg]
        raise KeyError("secret-internal-detail")

    monkeypatch.setattr(graph_mod, "derive", _boom)
    monkeypatch.setattr(nav, "_load_graph_mod", lambda: graph_mod)
    result, code = _query(_MIXED, "--operation", "summary")
    assert code == 1
    assert "secret-internal-detail" not in result["error"]["message"]


# --- Helper symbols and listing errors -----------------------------------------


def _scripts_copy(tmp_path: pathlib.Path) -> pathlib.Path:
    """Copy the skill's scripts directory so a helper can be altered in isolation."""
    dest = tmp_path / "scripts"
    shutil.copytree(_SCRIPTS, dest, ignore=shutil.ignore_patterns("__pycache__"))
    return dest


def test_a_helper_missing_validate_confined_directory_is_resolver_unavailable(tmp_path: pathlib.Path) -> None:
    """A confinement helper without the symbol the spec listing uses refuses at load, not at use."""
    scripts = _scripts_copy(tmp_path)
    helper = scripts / "_file_safety.py"
    text = helper.read_text(encoding="utf-8")
    assert text.count("def validate_confined_directory(") == 1
    helper.write_text(
        text.replace("def validate_confined_directory(", "def _renamed_validate_confined_directory("),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(scripts / "navigate_intents.py"), "query", "--root", str(_MIXED), "--operation", "summary"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    assert proc.stderr == ""
    assert json.loads(proc.stdout)["error"]["code"] == "resolver_unavailable"


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root ignores directory permissions")
def test_an_unlistable_spec_root_refuses_with_a_repository_relative_message(tmp_path: pathlib.Path) -> None:
    """A spec root that cannot be listed refuses as unsafe_input without the OS's absolute path."""
    root = _copy(_MIXED, tmp_path)
    specs = root / "docs" / "specs"
    specs.chmod(0)
    try:
        result, code = _query(root, "--operation", "summary")
    finally:
        specs.chmod(stat.S_IRWXU)
    assert code == 1
    assert result["error"]["code"] == "unsafe_input"
    assert result["error"]["message"] == "cannot list docs/specs"


# --- Root ordering in outstanding text -----------------------------------------


def test_outstanding_text_orders_several_depth_zero_roots_by_node_id(tmp_path: pathlib.Path) -> None:
    """Several terminal context roots print at depth 0 in node-id order."""
    root = tmp_path / "roots"
    (root / "docs" / "product" / "intents").mkdir(parents=True)
    for name, slug in (("CAP-0002-zulu-done.md", "zulu-done"), ("CAP-0001-alpha-done.md", "alpha-done")):
        (root / "docs" / "product" / "intents" / name).write_text(
            f"# Capability: {slug}\n\n- **Slug:** {slug}\n- **Status:** Fulfilled\n"
            "- **Level:** capability\n- **Parent intent:** none\n\n## Outcome\n",
            encoding="utf-8",
        )
    _intent_file(root, "FEAT-0001-under-zulu.md", "under-zulu", "Draft", "capability:zulu-done")
    _intent_file(root, "FEAT-0002-under-alpha.md", "under-alpha", "Draft", "capability:alpha-done")
    text, code = _query(root, "--operation", "outstanding", "--format", "text")
    assert code == 0
    roots = [ln.split(" · ")[0] for ln in text.splitlines() if ln and not ln.startswith(" ")]
    assert roots == ["capability:alpha-done", "capability:zulu-done"]
