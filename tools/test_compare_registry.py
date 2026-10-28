#!/usr/bin/env python3
"""Tests for tools/compare-registry.py, over fixture roots built in tmp_path."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

_TOOLS = Path(__file__).resolve().parent
_ROOT = _TOOLS.parent
_TOOL = _TOOLS / "compare-registry.py"

CLASSES = [
    "captured_item", "legacy_shape", "registry_stale", "registry_closed_stale",
    "registry_omission", "registry_live_only", "result_terminal", "unclassified",
]
SEVEN_KEYS = {"class", "failing", "target", "location", "id", "collections", "status"}


def _tool() -> Any:
    spec = importlib.util.spec_from_file_location("compare_registry_under_test", _TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["compare_registry_under_test"] = module
    spec.loader.exec_module(module)
    return module


# ── Fixture builders ──────────────────────────────────────────────────────────


def _intent(root: Path, slug: str, status: str = "Draft") -> Path:
    path = root / "docs/product/intents" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {slug}\n\n- **Slug:** `{slug}`\n- **Status:** {status}\n", encoding="utf-8")
    return path


def _brief(root: Path, slug: str, status: str = "Draft") -> Path:
    path = root / "docs/product/briefs" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# {slug}\n\n- **Slug:** `{slug}`\n- **Status:** {status}\n", encoding="utf-8")
    return path


def _spec(root: Path, name: str, status: str | None = "Implementing") -> Path:
    path = root / "docs/specs" / name / "spec.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"- **Status:** {status}\n" if status is not None else ""
    path.write_text(f"# Spec: {name}\n\n{line}", encoding="utf-8")
    return path


def _captured(root: Path, slug: str, status: str = "Open") -> Path:
    path = root / "docs/product/captured" / f"{slug}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    # A Closed captured item of any kind carries a Resolution: line.
    resolution = "- **Resolution:** fixed\n" if status == "Closed" else ""
    path.write_text(
        f"# {slug}\n\n- **Status:** {status}\n- **Kind:** intent\n{resolution}",
        encoding="utf-8",
    )
    return path


def _registry(root: Path, body: str) -> None:
    (root / "workspace.toml").write_text(body, encoding="utf-8")


def _entries(collection: str, *items: str) -> str:
    """A `[ini-001.<section>]` table with one collection holding raw TOML *items*."""
    section, name = collection.split(".")
    return f"[ini-001.{section}]\n{name} = [{', '.join(items)}]\n"


def _path(rel: str) -> str:
    return f'{{ path = "{rel}" }}'


def _run(root: Path | str, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_TOOL), "--root", str(root), *args],
        capture_output=True, text=True, check=False, env=env,
    )


def _rows(root: Path) -> list[dict[str, Any]]:
    out = _run(root, "--format", "json")
    assert out.returncode in (0, 1), out.stderr
    return json.loads(out.stdout)["differences"]


def _classes(root: Path) -> list[str]:
    return [row["class"] for row in _rows(root)]


def _refused(out: subprocess.CompletedProcess[str], input_name: str) -> None:
    assert out.returncode == 2
    assert out.stdout == ""
    lines = out.stderr.splitlines()
    assert len(lines) == 1 and lines[0].startswith(f"refused: {input_name}: "), out.stderr


def _hash_tree(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*")) if p.is_file()
    }


# ── The stub (red before the tool existed) ───────────────────────────────────


def test_registry_omission_for_unregistered_intent(tmp_path):
    _intent(tmp_path, "a", status="Draft")
    _registry(tmp_path, "")
    out = _run(tmp_path)
    assert out.returncode == 0
    assert "registry_omission 1" in out.stdout.splitlines()


# ── Class rules ───────────────────────────────────────────────────────────────


def test_no_difference_for_registered_nonterminal_and_terminal_only_entries(tmp_path):
    """AC-0002: registered non-terminal item, and a terminal-only entry, give no row."""
    _intent(tmp_path, "a")
    _spec(tmp_path, "done", status="Shipped")
    _registry(tmp_path, _entries("work.queue", _path("docs/product/intents/a.md"))
              + _entries("work.shipped", _path("docs/specs/done/spec.md")).replace("ini-001", "ini-002"))
    out = _run(tmp_path)
    assert out.returncode == 0
    assert _rows(tmp_path) == []
    assert out.stdout.splitlines()[0] == "registry comparison: pass"


def test_result_terminal_through_classify_with_synthesized_envelope(tmp_path):
    """AC-0003: no real navigator run yields a terminal outstanding item."""
    tool = _tool()
    _intent(tmp_path, "a", status="Fulfilled")
    item = tool.Outstanding("docs/product/intents/a.md", "intent:a", "intent", "Fulfilled")
    for registry in ({}, {"ini-001": {"work": {"queue": [{"path": item.path}]}}}):
        rows = tool.classify(registry, [item], [], tmp_path)
        assert [r.cls for r in rows] == ["result_terminal"]
        assert rows[0].failing and rows[0].target == item.path and rows[0].id == "intent:a"


def test_registry_closed_stale(tmp_path):
    _intent(tmp_path, "a")
    _registry(tmp_path, _entries("work.shipped", _path("docs/product/intents/a.md")))
    assert _classes(tmp_path) == ["registry_closed_stale"]


def test_registry_omission_row_carries_item_path(tmp_path):
    _intent(tmp_path, "a")
    _captured(tmp_path, "c")
    _registry(tmp_path, "")
    rows = _rows(tmp_path)
    assert [(r["class"], r["target"], r["id"], r["status"]) for r in rows] == [
        ("registry_omission", "docs/product/captured/c.md", "", "Open"),
        ("registry_omission", "docs/product/intents/a.md", "intent:a", "Draft"),
    ]
    assert all(set(r) == SEVEN_KEYS and r["location"] == "" and not r["failing"] for r in rows)


def test_legacy_shape_string_and_slug_table(tmp_path):
    _registry(tmp_path, _entries("work.queue", '"spec/foo"', '{ slug = "no-such-file" }'))
    rows = _rows(tmp_path)
    assert [r["class"] for r in rows] == ["legacy_shape", "legacy_shape"]
    assert [r["location"] for r in rows] == ["ini-001.work.queue[0]", "ini-001.work.queue[1]"]
    assert all(r["target"] == "" and r["collections"] == ["work.queue"] for r in rows)


def test_legacy_spec_path_with_dot_is_unclassified(tmp_path):
    _registry(tmp_path, _entries("work.queue", '"spec/a.b"'))
    assert _classes(tmp_path) == ["unclassified"]


def test_captured_item_class_for_other_existing_file(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/notes.txt").write_text("x", encoding="utf-8")
    _registry(tmp_path, _entries("work.queue", _path("docs/notes.txt")))
    rows = _rows(tmp_path)
    assert [r["class"] for r in rows] == ["captured_item"] and not rows[0]["failing"]


def test_registry_stale_for_terminal_files(tmp_path):
    _spec(tmp_path, "not_admitted", status="Shipped")  # typed file, not a graph node
    _captured(tmp_path, "gone", status="Closed")
    _captured(tmp_path, "gone2", status="Closed")
    _registry(tmp_path, _entries(
        "work.queue", _path("docs/specs/not_admitted/spec.md"),
        _path("docs/product/captured/gone.md"), '{ slug = "gone2" }',
    ))
    rows = _rows(tmp_path)
    assert [r["class"] for r in rows] == ["registry_stale"] * 3
    assert {r["target"] for r in rows} == {
        "docs/specs/not_admitted/spec.md", "docs/product/captured/gone.md",
        "docs/product/captured/gone2.md",
    }


def test_registry_live_only_fails_with_exit_1(tmp_path):
    _spec(tmp_path, "not_admitted", status="Draft")
    _registry(tmp_path, _entries("work.queue", _path("docs/specs/not_admitted/spec.md")))
    out = _run(tmp_path)
    assert out.returncode == 1
    lines = out.stdout.splitlines()
    assert lines[0] == "registry comparison: fail"
    assert "registry_live_only 1" in lines
    assert 'FAIL registry_live_only "docs/specs/not_admitted/spec.md" "" ["work.queue"]' in lines


def test_registry_live_only_for_typed_file_with_no_status_line(tmp_path):
    _spec(tmp_path, "not_admitted", status=None)
    _registry(tmp_path, _entries("work.queue", _path("docs/specs/not_admitted/spec.md")))
    assert _classes(tmp_path) == ["registry_live_only"]


def test_unclassified_cases(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/dir").mkdir()
    real = tmp_path / "docs/real.txt"
    real.write_text("x", encoding="utf-8")
    (tmp_path / "docs/link.txt").symlink_to(real)
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_text("x", encoding="utf-8")
    (tmp_path / "docs/escape.txt").symlink_to(outside)
    _registry(tmp_path, _entries(
        "work.queue",
        _path("docs/missing.md"), _path("docs/dir"), _path("docs/link.txt"),
        _path("docs/escape.txt"), _path("../outside.txt"),
        "{ kind = 1 }", '"not-a-path"', '{ path = 3 }',
    ))
    rows = _rows(tmp_path)
    assert [r["class"] for r in rows] == ["unclassified"] * 8
    assert all(r["failing"] for r in rows)
    assert sum(1 for r in rows if r["location"]) == 3


def test_non_utf8_typed_file_is_unclassified(tmp_path):
    tool = _tool()
    bad = _spec(tmp_path, "not_admitted", status="Draft")
    bad.write_bytes(b"\xff\xfe- **Status:** Draft\n")
    registry = {"ini-001": {"work": {"queue": [{"path": "docs/specs/not_admitted/spec.md"}]}}}
    assert [r.cls for r in tool.classify(registry, [], [], tmp_path)] == ["unclassified"]


def test_terminal_collection_entries_are_not_classified(tmp_path):
    _registry(tmp_path, _entries("work.shipped", '"nonsense"', _path("docs/missing.md")))
    assert _rows(tmp_path) == []


def test_shared_target_gives_one_row_with_union_of_collections(tmp_path):
    _spec(tmp_path, "not_admitted", status="Draft")
    target = _path("docs/specs/not_admitted/spec.md")
    _registry(tmp_path, f"[ini-001.work]\nqueue = [{target}]\nshipped = [{target}]\n"
              + f"[backlog]\nopen = [{target}]\n")
    rows = _rows(tmp_path)
    assert len(rows) == 1
    assert rows[0]["collections"] == ["backlog.open", "work.queue", "work.shipped"]


def test_no_target_entries_each_give_own_row(tmp_path):
    _registry(tmp_path, _entries("work.queue", "{ kind = 1 }", "{ kind = 2 }"))
    assert [r["location"] for r in _rows(tmp_path)] == ["ini-001.work.queue[0]", "ini-001.work.queue[1]"]


def test_top_level_location_has_no_initiative(tmp_path):
    _registry(tmp_path, "[backlog]\nopen = [{ kind = 1 }]\n")
    assert [r["location"] for r in _rows(tmp_path)] == ["backlog.open[0]"]


def test_missing_path_target_and_no_target_entry_stay_distinct_and_ordered(tmp_path):
    _registry(tmp_path, _entries("work.queue", "{ kind = 1 }", _path("ini-001.work.queue[0]")))
    rows = _rows(tmp_path)
    assert [(r["class"], r["target"], r["location"]) for r in rows] == [
        ("unclassified", "", "ini-001.work.queue[0]"),
        ("unclassified", "ini-001.work.queue[0]", ""),
    ]


def test_non_canonical_path_gives_unclassified_and_omission(tmp_path):
    _intent(tmp_path, "a")
    _registry(tmp_path, _entries("work.queue", _path("./docs/product/intents/a.md")))
    assert _classes(tmp_path) == ["registry_omission", "unclassified"]


def test_hostile_path_stays_on_one_json_quoted_fail_line(tmp_path):
    _registry(tmp_path, _entries("work.queue", '{ path = "a b\\nFAIL x\\u00e9" }'))
    out = _run(tmp_path)
    fails = [line for line in out.stdout.splitlines() if line.startswith("FAIL")]
    assert fails == ['FAIL unclassified "a b\\nFAIL x\\u00e9" "" ["work.queue"]']
    assert len(out.stdout.splitlines()) == 1 + 8 + 1 + 2


def test_collection_tables_pin_the_thirteen_collections():
    tool = _tool()
    eng = tool.engine()
    names = {f"{s}.{c}" for s, cs in eng._INITIATIVE_ENTRY_COLLECTIONS.items() for c in cs}
    names |= {f"{s}.{c}" for s, cs in eng._TOP_LEVEL_ENTRY_COLLECTIONS.items() for c in cs}
    assert len(names) == 13
    assert names == tool.NON_TERMINAL | tool.TERMINAL
    assert not tool.NON_TERMINAL & tool.TERMINAL


# ── Output, exit codes, help ──────────────────────────────────────────────────


def test_text_output_shape_and_registry_digest(tmp_path):
    _intent(tmp_path, "a")
    _registry(tmp_path, "")
    lines = _run(tmp_path).stdout.splitlines()
    assert lines[0] == "registry comparison: pass"
    assert [line.split()[0] for line in lines[1:9]] == CLASSES
    assert lines[9] == "commit unknown"
    assert lines[10] == "workspace.toml sha256 " + hashlib.sha256(b"").hexdigest()
    assert len(lines) == 11


def test_commit_line_reads_git_head(tmp_path):
    _registry(tmp_path, "")
    env = {**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com"}
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, env=env)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "x"], cwd=tmp_path, check=True, env=env)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True,
                          text=True, check=True).stdout.strip()
    assert f"commit {head}" in _run(tmp_path).stdout.splitlines()


def test_json_output_shape(tmp_path):
    _intent(tmp_path, "a")
    _registry(tmp_path, "")
    out = _run(tmp_path, "--format", "json")
    data = json.loads(out.stdout)
    assert set(data) == {"schema", "result", "counts", "differences", "inputs"}
    assert data["schema"] == "registry-comparison.v1" and data["result"] == "pass"
    assert list(data["counts"]) == CLASSES and data["counts"]["registry_omission"] == 1
    assert all(set(row) == SEVEN_KEYS for row in data["differences"])
    assert set(data["inputs"]) == {"commit", "workspace_sha256", "generated_at"}
    assert data["inputs"]["generated_at"]


def test_help_names_classes_failing_ones_and_exit_codes():
    out = _run(".", "--help")
    assert out.returncode == 0
    text = out.stdout
    for name in CLASSES:
        assert name in text
    lines = {line.split()[0]: line for line in text.splitlines() if line.split() and line.split()[0] in CLASSES}
    for name in ("registry_live_only", "result_terminal", "unclassified"):
        assert "FAILS" in lines[name]
    for name in CLASSES[:5]:
        assert "allowed" in lines[name]
    for code in ("0", "1", "2"):
        assert any(line.strip().startswith(code + " ") for line in text.splitlines())


# ── Navigator location, bytecode, and read-only ───────────────────────────────


def test_decoy_navigator_under_root_is_never_run(tmp_path):
    _intent(tmp_path, "a")
    _registry(tmp_path, "")
    decoy = tmp_path / "packs/core/.apm/skills/navigate-intents/scripts/navigate_intents.py"
    decoy.parent.mkdir(parents=True)
    decoy.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    out = _run(tmp_path)
    assert out.returncode == 0 and "registry_omission 1" in out.stdout.splitlines()


def test_run_leaves_every_file_byte_identical(tmp_path):
    _intent(tmp_path, "a")
    _captured(tmp_path, "c")
    _registry(tmp_path, _entries("work.queue", _path("docs/product/intents/a.md")))
    before = _hash_tree(tmp_path)
    assert _run(tmp_path).returncode == 0
    assert _run(tmp_path, "--format", "json").returncode == 0
    assert _hash_tree(tmp_path) == before


def _mirrors(prefix: Path, *sources: Path) -> list[Path]:
    """Cache files under *prefix* that mirror a source below any of *sources*."""
    found: list[Path] = []
    for cache in prefix.rglob("*.pyc"):
        mirrored = "/" + cache.relative_to(prefix).parent.as_posix()
        if "/site-packages/" in mirrored + "/":
            continue  # the interpreter's own startup hooks, before the tool runs
        if any(mirrored == str(s) or mirrored.startswith(str(s) + "/") for s in sources):
            found.append(cache)
    return found


def test_run_writes_no_bytecode_and_the_check_has_a_control(tmp_path):
    _intent(tmp_path, "a")
    _registry(tmp_path, "")
    prefix = tmp_path.parent / f"{tmp_path.name}-pycache"
    prefix.mkdir()
    env = {**os.environ, "PYTHONPYCACHEPREFIX": str(prefix)}
    env.pop("PYTHONDONTWRITEBYTECODE", None)
    assert _run(tmp_path, env=env).returncode == 0
    sources = (_ROOT, Path(__file__).parent.parent)
    assert _mirrors(prefix, *sources) == []  # site-packages startup caches are not the tool's

    control = tmp_path.parent / f"{tmp_path.name}-control"
    control.mkdir()
    code = (
        "import importlib.util,sys\n"
        f"s=importlib.util.spec_from_file_location('ct',{str(_ROOT / 'packs/core/.apm/skills/close-work/scripts/closure_terminality.py')!r})\n"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n"
    )
    env2 = {**env, "PYTHONPYCACHEPREFIX": str(control)}
    subprocess.run([sys.executable, "-c", code], env=env2, check=True)
    assert _mirrors(control, *sources), "the control must be flagged"


# ── Refusals ──────────────────────────────────────────────────────────────────


def test_refuses_missing_workspace_toml(tmp_path):
    _refused(_run(tmp_path), "workspace.toml")


def test_refuses_workspace_toml_link_directory_non_utf8_and_bad_toml(tmp_path):
    real = tmp_path / "real.toml"
    real.write_text("", encoding="utf-8")
    (tmp_path / "workspace.toml").symlink_to(real)
    _refused(_run(tmp_path), "workspace.toml")
    (tmp_path / "workspace.toml").unlink()
    (tmp_path / "workspace.toml").mkdir()
    _refused(_run(tmp_path), "workspace.toml")
    (tmp_path / "workspace.toml").rmdir()
    (tmp_path / "workspace.toml").write_bytes(b"\xff\xfe")
    _refused(_run(tmp_path), "workspace.toml")
    _registry(tmp_path, "x = = 1\n")
    _refused(_run(tmp_path), "workspace.toml")


@pytest.mark.parametrize("body", [
    "backlog = 1\n",
    "[ini-001]\nwork = 1\n",
    "ini-001 = 1\n",
    "[backlog]\nopen = 1\n",
    "[ini-001.work]\nqueue = { path = 'x' }\n",
])
def test_refuses_registry_structure_defects(tmp_path, body):
    _registry(tmp_path, body)
    _refused(_run(tmp_path), "workspace.toml")


def test_navigator_failure_wins_over_graph_failure(tmp_path):
    path = tmp_path / "docs/product/intents/noslug.md"
    path.parent.mkdir(parents=True)
    path.write_text("# x\n\n- **Status:** Draft\n", encoding="utf-8")
    _registry(tmp_path, "")
    _refused(_run(tmp_path), "navigator")


def _in_process(tool: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                capsys: pytest.CaptureFixture[str], **patches: Any) -> tuple[int, str, str]:
    for name, value in patches.items():
        monkeypatch.setattr(tool, name, value)
    code = tool.main(["--root", str(tmp_path)])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_refuses_ok_envelope_missing_placed(tmp_path, monkeypatch, capsys):
    _registry(tmp_path, "")
    envelope = {"schema": "intent-navigation.query.v1", "status": "ok", "no_parent": []}
    code, out, err = _in_process(_tool(), tmp_path, monkeypatch, capsys, run_outstanding=lambda root: envelope)
    assert (code, out) == (2, "") and err.startswith("refused: navigator: ") and err.count("\n") == 1


@pytest.mark.parametrize("envelope", [
    [], {"schema": "other", "status": "ok", "placed": [], "no_parent": []},
    {"schema": "intent-navigation.query.v1", "status": "error", "placed": [], "no_parent": []},
    {"schema": "intent-navigation.query.v1", "status": "ok", "placed": [{"id": 1}], "no_parent": []},
])
def test_refuses_other_envelope_defects(tmp_path, monkeypatch, capsys, envelope):
    _registry(tmp_path, "")
    code, out, err = _in_process(_tool(), tmp_path, monkeypatch, capsys, run_outstanding=lambda root: envelope)
    assert (code, out) == (2, "") and err.startswith("refused: navigator: ")


def test_refuses_graph_failure_and_missing_id(tmp_path, monkeypatch, capsys):
    _registry(tmp_path, "")
    tool = _tool()
    ok = {"schema": "intent-navigation.query.v1", "status": "ok", "no_parent": [],
          "placed": [{"id": "intent:a", "type": "intent", "status": "Draft"}]}

    def boom(root: Path) -> dict[str, str]:
        raise tool.Refusal("graph", "cannot be derived: malformed_record")

    code, out, err = _in_process(tool, tmp_path, monkeypatch, capsys,
                                 run_outstanding=lambda root: ok, graph_paths=boom)
    assert (code, out) == (2, "") and err.startswith("refused: graph: ")
    code, out, err = _in_process(tool, tmp_path, monkeypatch, capsys,
                                 run_outstanding=lambda root: ok, graph_paths=lambda root: {})
    assert (code, out) == (2, "") and err.startswith("refused: graph: ")


def test_refuses_unreadable_and_invalid_captured_files_no_entry_needed(tmp_path):
    _registry(tmp_path, "")
    invalid = tmp_path / "docs/product/captured/bad.md"
    invalid.parent.mkdir(parents=True)
    invalid.write_text("# bad\n\n- **Status:** Maybe\n- **Kind:** intent\n", encoding="utf-8")
    _refused(_run(tmp_path), "captured-items")
    invalid.unlink()
    (tmp_path / "docs/product/captured/link.md").symlink_to(tmp_path / "workspace.toml")
    _refused(_run(tmp_path), "captured-items")


def test_registry_refusal_wins_over_later_inputs(tmp_path):
    bad = tmp_path / "docs/product/intents/noslug.md"
    bad.parent.mkdir(parents=True)
    bad.write_text("# x\n", encoding="utf-8")
    _registry(tmp_path, "backlog = 1\n")
    _refused(_run(tmp_path), "workspace.toml")


def test_usage_errors_are_one_refusal_line(tmp_path):
    for args in ([], ["--root", str(tmp_path), "--format", "xml"], ["--bogus"]):
        out = subprocess.run([sys.executable, str(_TOOL), *args], capture_output=True, text=True, check=False)
        _refused(out, "arguments")


def test_internal_error_is_exit_2(tmp_path, monkeypatch, capsys):
    _registry(tmp_path, "")

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("boom\nsecond line")

    code, out, err = _in_process(_tool(), tmp_path, monkeypatch, capsys, classify=boom)
    assert (code, out) == (2, "")
    assert err.startswith("refused: internal: ") and err.count("\n") == 1


def test_graph_paths_refuses_a_malformed_corpus(tmp_path):
    tool = _tool()
    path = tmp_path / "docs/product/intents/noslug.md"
    path.parent.mkdir(parents=True)
    path.write_text("# x\n\n- **Status:** Draft\n", encoding="utf-8")
    with pytest.raises(tool.Refusal) as caught:
        tool.graph_paths(tmp_path)
    assert caught.value.input_name == "graph"


def test_non_typed_file_over_the_read_cap_is_still_captured_item(tmp_path, monkeypatch):
    tool = _tool()
    monkeypatch.setattr(tool, "MAX_FILE_BYTES", 4)
    note = tmp_path / "docs" / "design" / "note.md"
    note.parent.mkdir(parents=True)
    note.write_text("longer than four bytes\n", encoding="utf-8")
    _spec(tmp_path, "big", status="Draft")
    registry = {"ini-001": {"work": {"queue": [
        {"path": "docs/design/note.md"}, {"path": "docs/specs/big/spec.md"},
    ]}}}
    assert [(r.cls, r.target) for r in tool.classify(registry, [], [], tmp_path)] == [
        ("captured_item", "docs/design/note.md"),
        ("unclassified", "docs/specs/big/spec.md"),
    ]


def test_alias_spelling_of_a_live_typed_file_is_unclassified(tmp_path):
    _spec(tmp_path, "live", status="Draft")
    probe = tmp_path / "DOCS"
    if not probe.exists():
        pytest.skip("case-sensitive filesystem: an alias spelling cannot open the file")
    tool = _tool()
    registry = {"ini-001": {"work": {"queue": [{"path": "DOCS/specs/live/spec.md"}]}}}
    assert [r.cls for r in tool.classify(registry, [], [], tmp_path)] == ["unclassified"]


def test_exact_spelling_check_rejects_a_case_alias_on_any_filesystem(tmp_path):
    _spec(tmp_path, "live", status="Draft")
    tool = _tool()
    assert tool._spelled_as_on_disk(tmp_path, "docs/specs/live/spec.md")
    assert not tool._spelled_as_on_disk(tmp_path, "DOCS/specs/live/spec.md")
