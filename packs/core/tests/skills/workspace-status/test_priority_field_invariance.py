"""Adding `Priority:` lines changes neither `status` nor `outstanding` output.

Verification mode: TDD. One fixture tree gives `workspace-status status` at
least two ready specs, one active spec, one blocked spec, two ready shaping
entries and two captured items, and gives `navigate-intents query --operation
outstanding` two intents. Priority lines are then written into the same root,
with `low` on the first and `urgent` on the last of each ordered list, and both
commands are run again.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SKILLS = Path(__file__).resolve().parents[3] / ".apm/skills"

SPECS_READY = ("r1", "r2", "r3")
CAPTURED = ("cap-a", "cap-b", "cap-c")
INTENTS = ("int-a", "int-b")
BRIEF = "docs/product/briefs/brief-a.md"


def _load(name: str, path: Path) -> ModuleType:
    """Load a skill script by path under a unique module name."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


STATUS = _load(
    "core_workspace_status_priority_invariance",
    _SKILLS / "workspace-status/scripts/workspace_status.py",
)
NAVIGATE = _load(
    "core_navigate_intents_priority_invariance",
    _SKILLS / "navigate-intents/scripts/navigate_intents.py",
)


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _entry(path: str) -> str:
    return (
        f'{{path = "{path}", kind = "spec", source = {{mode = "repo-origin"}}, '
        'summary = "fixture", needs = []}'
    )


def _spec(slug: str, status: str, extra: str = "") -> str:
    return f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** none\n{extra}"


def _intent(slug: str) -> str:
    return (
        f"# Feature: {slug}\n\n- **Slug:** `{slug}`\n- **Status:** Draft\n"
        "- **Level:** feature\n- **Owner:** o\n- **Parent intent:** none\n\n"
        "## Outcome\n\nFixture intent.\n"
    )


def _build_tree(root: Path) -> None:
    """One registry with every list AC-0007 needs, and no `Priority:` line."""
    plan = "# Plan\n\n- **Status:** Approved\n"
    for slug in (*SPECS_READY, "act", "blk"):
        status = "Implementing" if slug == "act" else "Approved"
        extra = "- **Depends on:** spec:act\n" if slug == "blk" else ""
        _write(root, f"docs/specs/{slug}/spec.md", _spec(slug, status, extra))
        _write(root, f"docs/specs/{slug}/plan.md", plan)
    for slug in CAPTURED:
        _write(
            root,
            f"docs/product/captured/{slug}.md",
            "# Item\n\n- **Status:** Open\n- **Kind:** defect\n",
        )
    for slug in INTENTS:
        _write(root, f"docs/product/intents/{slug}.md", _intent(slug))
    _write(
        root,
        BRIEF,
        "# Brief: a\n\n- **Slug:** `brief-a`\n- **Received:** 2026-01-01\n"
        "- **Owner:** o\n- **Status:** Draft\n- **Parent intent:** none\n\n"
        "## Outcome\n\nFixture brief.\n",
    )
    queue = ", ".join(_entry(f"docs/specs/{s}/spec.md") for s in (*SPECS_READY, "blk"))
    _write(
        root,
        "workspace.toml",
        "\n".join([
            '["ini-001"]', 'name = "Priority invariance fixture"',
            'status = "active"', 'milestone = "m1"', "", '["ini-001".work]',
            f"queue = [{queue}]",
            f"active = [{_entry('docs/specs/act/spec.md')}]",
            "shipped = []", "", '["ini-001".shaping_queue]',
            'active = ["shape-one", "shape-two"]', "backlog = []", "",
            "[backlog]", "open = []", "closed = []", "",
        ]),
    )


def _run(capsys: pytest.CaptureFixture[str], module: ModuleType, argv: list[str]) -> str:
    """Run `main(argv)` in-process and return its stdout."""
    capsys.readouterr()
    assert module.main(argv) == 0
    return capsys.readouterr().out


def _status(capsys: pytest.CaptureFixture[str], root: Path) -> str:
    return _run(capsys, STATUS, ["status", "--root", str(root)])


def _outstanding(capsys: pytest.CaptureFixture[str], root: Path) -> dict[str, Any]:
    out = _run(
        capsys, NAVIGATE,
        ["query", "--root", str(root), "--operation", "outstanding"],
    )
    return json.loads(out)


def _without_generated_at(value: Any) -> Any:
    """Drop every `generated_at` key, wherever it appears."""
    if isinstance(value, dict):
        return {k: _without_generated_at(v) for k, v in value.items() if k != "generated_at"}
    if isinstance(value, list):
        return [_without_generated_at(v) for v in value]
    return value


def _outstanding_intents(payload: dict[str, Any]) -> list[str]:
    """Outstanding intent slugs, in output order."""
    slugs: list[str] = []
    for section in ("placed", "no_parent"):
        for item in payload[section]:
            if item.get("type") == "intent":
                slugs.append(item["id"].removeprefix("intent:"))
    return slugs


def _add_priority(root: Path, rel: str, value: str) -> None:
    """Insert one `Priority:` line at the end of the preamble, before the first `## `."""
    path = root / rel
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    at = next((i for i, line in enumerate(lines) if line.startswith("## ")), len(lines))
    while at > 0 and lines[at - 1].strip() == "":
        at -= 1  # keep the line against the last field, above the blank separator
    lines.insert(at, f"- **Priority:** {value}\n")
    path.write_text("".join(lines), encoding="utf-8")


def _ordered(items: list[dict[str, Any]], key: str = "path") -> list[str]:
    return [item[key] for item in items]


def test_priority_lines_change_neither_status_nor_outstanding(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _build_tree(tmp_path)
    before_text = _status(capsys, tmp_path)
    before = json.loads(before_text)
    before_outstanding = _outstanding(capsys, tmp_path)

    assert len(before["canonical"]["ready"]) >= 2
    assert len(before["canonical"]["active"]) >= 1
    assert len(before["canonical"]["blocked"]) >= 1
    assert len(before["shaping"]["ready"]) >= 2
    assert len(before["captured"]["items"]) >= 2
    intents = _outstanding_intents(before_outstanding)
    assert len(intents) >= 2

    ready = _ordered(before["canonical"]["ready"])
    captured = _ordered(before["captured"]["items"])
    middle = ("medium", "high")
    plan: dict[str, str] = {}
    for paths, mid in ((ready, middle[0]), (captured, middle[1])):
        plan.update(dict.fromkeys(paths, mid))
        plan[paths[0]], plan[paths[-1]] = "low", "urgent"
    intent_paths = [f"docs/product/intents/{s}.md" for s in intents]
    plan.update(dict.fromkeys(intent_paths, "high"))
    plan[intent_paths[0]], plan[intent_paths[-1]] = "low", "urgent"
    plan[_ordered(before["canonical"]["active"])[0]] = "high"
    plan[_ordered(before["canonical"]["blocked"])[0]] = "medium"
    plan[BRIEF] = "low"

    assert set(plan.values()) == {"urgent", "high", "medium", "low"}
    for rel, value in plan.items():
        _add_priority(tmp_path, rel, value)
    assert all("Priority:" in (tmp_path / rel).read_text(encoding="utf-8") for rel in plan)

    assert _status(capsys, tmp_path) == before_text
    after_outstanding = _outstanding(capsys, tmp_path)
    assert _without_generated_at(after_outstanding) == _without_generated_at(
        before_outstanding
    )


def test_a_reordered_ready_list_would_fail_the_comparison(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Sensitivity: the byte comparison notices a change in `canonical.ready` order."""
    _build_tree(tmp_path)
    before = _status(capsys, tmp_path)
    toml = tmp_path / "workspace.toml"
    text = toml.read_text(encoding="utf-8")
    first, second = (_entry(f"docs/specs/{s}/spec.md") for s in SPECS_READY[:2])
    assert first + ", " + second in text
    toml.write_text(text.replace(first + ", " + second, second + ", " + first), encoding="utf-8")
    assert _status(capsys, tmp_path) != before
