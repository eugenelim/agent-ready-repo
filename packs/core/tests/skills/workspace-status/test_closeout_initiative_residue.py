"""Regression tests for closeout blockers from initiative-local residue."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parents[3]
_STATUS_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status.py"
)


def _load_status():
    spec = importlib.util.spec_from_file_location("workspace_status_residue", _STATUS_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module._bind_engine()
    return module


def _entry(path: str, kind: str) -> str:
    return (
        '{ path = "'
        + path
        + '", kind = "'
        + kind
        + '", source = { mode = "repo-origin" }, summary = "Test artifact", needs = [] }'
    )


def _shipped_spec_entry(root: Path, *, parent: str | None = None) -> str:
    """Write the one Shipped spec every fixture needs, optionally brief-owned.

    `parent` attributes the spec to a brief via `source.parent`. A
    `brief_queue.executing` entry is only valid when a child is `Implementing`
    or `Shipped`, so an executing-brief fixture without this is not an executing
    brief at all — it reconciles as `impossible_transition` and would prove
    nothing about residue. Attributing the already-Shipped spec satisfies the
    rule while keeping `all_specs_shipped` true, which is what isolates the
    residue blocker.
    """
    spec = root / "docs/specs/shipped/spec.md"
    spec.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text("# Shipped spec\n\n- **Status:** Shipped\n", encoding="utf-8")
    (spec.parent / "plan.md").write_text("# Plan\n", encoding="utf-8")
    source = '{ mode = "repo-origin" }'
    if parent is not None:
        source = f'{{ mode = "repo-origin", parent = "{parent}" }}'
    return (
        '{ path = "docs/specs/shipped/spec.md", kind = "spec", source = '
        + source
        + ', summary = "Shipped spec", needs = [] }'
    )


def _write_workspace(
    root: Path,
    *,
    shaping_backlog: bool = False,
    shaping_active: bool = False,
    legacy_shaping_backlog: bool = False,
    legacy_shaping_active: bool = False,
    brief_collection: str | None = None,
) -> None:
    """Write an all-shipped workspace with the requested initiative residue."""
    brief_path = None
    if brief_collection is not None:
        brief_path = f"docs/product/briefs/{brief_collection}-brief.md"
    # `executing` and `cancelled` are the two collections that assert execution
    # evidence is PRESENT, so only those two claim the shipped spec as a child.
    # The others assert it is absent and must not.
    shipped_entry = _shipped_spec_entry(
        root, parent=brief_path if brief_collection in {"executing", "cancelled"} else None
    )

    def _canonical_shaping() -> str:
        intent = root / "docs/product/intents/open-intent.md"
        intent.parent.mkdir(parents=True, exist_ok=True)
        intent.write_text("# Open intent\n\n- **Status:** Draft\n", encoding="utf-8")
        return _entry("docs/product/intents/open-intent.md", "intent")

    # A legacy-shaped record and a canonical one reach the projection through
    # different reconciled layers, so each shape needs its own fixture.
    legacy = '{slug = "legacy-shape-item", type = "shape"}'
    active = ""
    backlog = ""
    if shaping_backlog:
        backlog = _canonical_shaping()
    if shaping_active:
        active = _canonical_shaping()
    if legacy_shaping_backlog:
        backlog = legacy
    if legacy_shaping_active:
        active = legacy

    brief_section = ""
    if brief_collection is not None:
        brief = root / brief_path
        brief.parent.mkdir(parents=True, exist_ok=True)
        # The brief lifecycle status must match its collection exactly, or the
        # entry reconciles as `impossible_transition` and the fixture proves
        # nothing about residue.
        status = brief_collection.capitalize()
        brief.write_text(f"# Brief\n\n- **Status:** {status}\n", encoding="utf-8")
        brief_section = (
            '\n["ini-001".brief_queue]\n'
            f"{brief_collection} = [{_entry(brief_path, 'brief')}]\n"
        )

    (root / "workspace.toml").write_text(
        "\n".join(
            [
                '["ini-001"]',
                'name = "Closeout test"',
                'status = "active"',
                'milestone = "M1"',
                '',
                '["ini-001".work]',
                'queue = []',
                'active = []',
                f"shipped = [{shipped_entry}]",
                '',
                '["ini-001".shaping_queue]',
                f"active = [{active}]",
                f"backlog = [{backlog}]",
                brief_section,
            ]
        ),
        encoding="utf-8",
    )


def _closeout(root: Path) -> dict:
    module = _load_status()
    result = module.analyze(root, cooling_enabled=False)
    return json.loads(json.dumps(module._build_json(root, result, "status")))["closeout"]


def test_shaping_backlog_blocks_otherwise_shipped_initiative(tmp_path: Path) -> None:
    _write_workspace(tmp_path, shaping_backlog=True)

    closeout = _closeout(tmp_path)

    assert closeout["all_specs_shipped"] is True
    assert "initiative-residue" in closeout["closeout_blockers"]
    assert closeout["initiative_eligible"] is False
    assert closeout["next_action"] == "settle-closeout-blockers"


def test_removing_shaping_backlog_restores_closeout_eligibility(tmp_path: Path) -> None:
    _write_workspace(tmp_path)

    closeout = _closeout(tmp_path)

    assert closeout["closeout_blockers"] == []
    assert closeout["initiative_eligible"] is True
    assert closeout["next_action"] == "invoke-close-work"


def test_draft_brief_blocks_closeout(tmp_path: Path) -> None:
    _write_workspace(tmp_path, brief_collection="draft")

    assert "initiative-residue" in _closeout(tmp_path)["closeout_blockers"]


def test_shipped_brief_is_not_closeout_residue(tmp_path: Path) -> None:
    _write_workspace(tmp_path, brief_collection="shipped")

    closeout = _closeout(tmp_path)

    assert "initiative-residue" not in closeout["closeout_blockers"]
    assert closeout["initiative_eligible"] is True


def test_absent_brief_queue_is_not_closeout_residue(tmp_path: Path) -> None:
    _write_workspace(tmp_path)

    assert "initiative-residue" not in _closeout(tmp_path)["closeout_blockers"]


def test_legacy_shaping_backlog_blocks_closeout(tmp_path: Path) -> None:
    """The legacy half of the residue condition is separately load-bearing.

    Canonical and legacy shaping entries reach the projection through different
    layers, so a canonical-only fixture leaves this branch free to be deleted.
    """
    _write_workspace(tmp_path, legacy_shaping_backlog=True)

    closeout = _closeout(tmp_path)

    assert closeout["all_specs_shipped"] is True
    assert "initiative-residue" in closeout["closeout_blockers"]
    assert closeout["initiative_eligible"] is False


def test_executing_brief_blocks_closeout(tmp_path: Path) -> None:
    _write_workspace(tmp_path, brief_collection="executing")

    closeout = _closeout(tmp_path)

    assert "initiative-residue" in closeout["closeout_blockers"]
    assert closeout["initiative_eligible"] is False


def test_ready_brief_blocks_closeout(tmp_path: Path) -> None:
    _write_workspace(tmp_path, brief_collection="ready")

    assert "initiative-residue" in _closeout(tmp_path)["closeout_blockers"]


def test_canonical_active_shaping_blocks_closeout(tmp_path: Path) -> None:
    _write_workspace(tmp_path, shaping_active=True)

    closeout = _closeout(tmp_path)

    assert closeout["all_specs_shipped"] is True
    assert "initiative-residue" in closeout["closeout_blockers"]
    assert closeout["initiative_eligible"] is False


def test_legacy_active_shaping_blocks_closeout(tmp_path: Path) -> None:
    _write_workspace(tmp_path, legacy_shaping_active=True)

    assert "initiative-residue" in _closeout(tmp_path)["closeout_blockers"]


def test_withdrawn_brief_is_not_closeout_residue(tmp_path: Path) -> None:
    """`withdrawn` is terminal. Without this, adding it to the condition passes."""
    _write_workspace(tmp_path, brief_collection="withdrawn")

    closeout = _closeout(tmp_path)

    assert "initiative-residue" not in closeout["closeout_blockers"]
    assert closeout["initiative_eligible"] is True


def test_cancelled_brief_is_not_closeout_residue(tmp_path: Path) -> None:
    """`cancelled` is terminal. Without this, adding it to the condition passes."""
    _write_workspace(tmp_path, brief_collection="cancelled")

    closeout = _closeout(tmp_path)

    assert "initiative-residue" not in closeout["closeout_blockers"]
    assert closeout["initiative_eligible"] is True


def test_shaping_and_brief_residue_emit_one_blocker(tmp_path: Path) -> None:
    _write_workspace(tmp_path, shaping_backlog=True, brief_collection="draft")

    assert _closeout(tmp_path)["closeout_blockers"].count("initiative-residue") == 1
