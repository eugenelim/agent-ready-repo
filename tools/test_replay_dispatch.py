#!/usr/bin/env python3
"""Tests for tools/replay-dispatch.py: both exit codes over trees planted in tmp_path."""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

_TOOLS = Path(__file__).resolve().parent
_TOOL = _TOOLS / "replay-dispatch.py"
_ENGINE = _TOOLS.parent / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
_REGISTRY = "schema_version = 1\n[work]\nqueue = []\n"


def _tree(root: Path, status: str = "Approved") -> Path:
    spec = root / "docs/specs/a"
    spec.mkdir(parents=True)
    (spec / "spec.md").write_text(f"# Spec: a\n\n- **Status:** {status}\n- **Brief:** none\n", encoding="utf-8")
    (spec / "plan.md").write_text("# Plan\n\n- **Status:** Approved\n", encoding="utf-8")
    (root / "workspace.toml").write_text(_REGISTRY, encoding="utf-8")
    return root


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(_TOOL), *args], capture_output=True, text=True, check=False,
    )


def test_exit_zero_lists_the_four_lists_digest_count_and_the_difference(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    (root / "docs/lifecycle").mkdir()
    (root / "docs/lifecycle/d-1.json").write_text("{}", encoding="utf-8")
    done = _run("--root", str(root), "--base-engine", str(_ENGINE))
    assert done.returncode == 0, done.stderr
    lines = done.stdout.splitlines()
    assert "base canonical.ready 0 []" in lines
    assert "base canonical.active 0 []" in lines
    assert 'dispatch ready 1 ["docs/specs/a/spec.md"]' in lines
    assert "dispatch active 0 []" in lines
    assert f"workspace.toml sha256 {hashlib.sha256(_REGISTRY.encode()).hexdigest()}" in lines
    assert "lifecycle records 1" in lines
    ready_diff = "DIFF docs/specs/a/spec.md ready base=false dispatch=true"
    assert any(line.startswith(ready_diff) for line in lines)
    assert not any("class" in line.lower() for line in lines)  # it never classifies


def test_exit_zero_with_no_difference_writes_none(tmp_path: Path) -> None:
    root = _tree(tmp_path, status="Shipped")
    done = _run("--root", str(root), "--base-engine", str(_ENGINE))
    assert done.returncode == 0, done.stderr
    assert "differing specs 0" in done.stdout.splitlines()
    assert "DIFF" not in done.stdout


def test_exit_two_on_usage_error() -> None:
    done = _run("--root", "somewhere")
    assert done.returncode == 2
    assert done.stdout == ""
    assert done.stderr.startswith("refused: arguments:")


def test_exit_two_on_unreadable_root(tmp_path: Path) -> None:
    done = _run("--root", str(tmp_path / "absent"), "--base-engine", str(_ENGINE))
    assert done.returncode == 2
    assert done.stdout == ""
    assert done.stderr.startswith("refused: root:")


def test_exit_two_when_the_registry_is_missing(tmp_path: Path) -> None:
    done = _run("--root", str(tmp_path), "--base-engine", str(_ENGINE))
    assert done.returncode == 2
    assert done.stdout == ""
    assert done.stderr.startswith("refused: workspace.toml:")


def test_exit_two_when_the_base_engine_is_missing(tmp_path: Path) -> None:
    done = _run("--root", str(_tree(tmp_path)), "--base-engine", str(tmp_path / "none.py"))
    assert done.returncode == 2
    assert done.stdout == ""
    assert done.stderr.startswith("refused: base-engine:")


def test_a_selector_dispatch_refuses_is_recorded_not_fatal(tmp_path: Path) -> None:
    root = _tree(tmp_path)
    dotted = root / "docs/specs/v1.2"
    dotted.mkdir()
    (dotted / "spec.md").write_text("# Spec: v\n\n- **Status:** Shipped\n", encoding="utf-8")
    done = _run("--root", str(root), "--base-engine", str(_ENGINE))
    assert done.returncode == 0, done.stderr
    assert 'DIFF docs/specs/v1.2/spec.md start base={"action": "refuse"' in done.stdout
    assert '"action": "invalid_selector"' in done.stdout


# --- the base decision agrees with the replay suite's transcription -----------------

_SUITE = (
    _TOOLS.parent / "packs/core/tests/skills/work-loop/test_header_derived_dispatch_replay.py"
)


def _load(path: Path, stem: str) -> ModuleType:
    """Load a module by file path under a unique name."""
    name = f"tools_replay_dispatch_parity_{stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def _item(path: str) -> dict[str, Any]:
    return {"path": path}


def _blocked(path: str) -> dict[str, Any]:
    return {"path": path, "findings": [{"code": "missing_plan"}]}


def _canonical(
    ready: list[str] = (), active: list[str] = (), blocked: list[dict[str, Any]] = (),  # type: ignore[assignment]
    findings: list[dict[str, Any]] = (),  # type: ignore[assignment]
) -> dict[str, Any]:
    paths = [*ready, *active]
    return {
        "ready": [_item(p) for p in ready], "active": [_item(p) for p in active],
        "blocked": list(blocked), "findings": list(findings),
        "evaluations": [_item(p) for p in paths],
    }


_A, _B, _C = (f"docs/specs/{n}/spec.md" for n in "abc")
_CANONICALS = {
    "empty": _canonical(),
    "one ready": _canonical(ready=[_A]),
    "two ready": _canonical(ready=[_A, _B]),
    "ready and blocked": _canonical(ready=[_A], blocked=[_blocked(_A)]),
    "ready, slug-spelled finding": _canonical(
        ready=[_A], findings=[{"path": "spec/a", "code": "unsupported_legacy"}]
    ),
    "ready, bare-slug block": _canonical(ready=[_A], blocked=[_blocked("a")]),
    "first ready blocked, second not": _canonical(ready=[_A, _B], blocked=[_blocked(_A)]),
    "one active": _canonical(active=[_B]),
    "two active": _canonical(active=[_B, _C]),
    "active beside ready": _canonical(ready=[_A], active=[_B]),
    "active and blocked": _canonical(active=[_B], blocked=[_blocked(_B)]),
}


def test_base_decision_matches_the_replay_suite() -> None:
    tool = _load(_TOOL, "tool")
    suite = _load(_SUITE, "suite")
    for label, canonical in _CANONICALS.items():
        assert tool.base_argless(canonical) == suite.base_argless(canonical), label
        for mode in ("start", "resume"):
            for target in (_A, _B, _C):
                assert tool.base_named(canonical, mode, target) == (
                    suite.base_named(canonical, mode, target)[0]
                ), (label, mode, target)
