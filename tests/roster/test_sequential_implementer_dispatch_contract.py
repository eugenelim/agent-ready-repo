"""Cross-surface checks for the sequential implementer dispatch contract."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUPERVISOR = ROOT / "packs/core/.apm/skills/work-loop/references/supervisor-mode.md"
EVALS = ROOT / "packs/core/.apm/skills/work-loop/evals/evals.json"
SEED = ROOT / "packs/core/seeds/docs/CONVENTIONS.md"
IMPLEMENTER = ROOT / "packs/core/.apm/agents/implementer.md"
GUIDE = ROOT / "guides/core/how-to/plan-and-execute-non-trivial-work.md"


def test_no_surface_denies_the_sequential_dispatch_envelope() -> None:
    """Former single-agent and mandatory-worktree claims cannot return."""
    for path in (SUPERVISOR, SEED):
        assert "single-agent, on every adapter" not in path.read_text(encoding="utf-8")
    # AC8's third recorded contradiction: the repo-profile description.
    assert "single-agent work-loop" not in SEED.read_text(encoding="utf-8")
    implementer = IMPLEMENTER.read_text(encoding="utf-8")
    assert ".worktrees/<task-id>/" not in implementer
    assert "all edits happen inside" not in implementer


def test_dispatch_surfaces_name_implementer_and_keep_the_fallback() -> None:
    """Omission is caught separately from removal of the former contradiction."""
    supervisor = SUPERVISOR.read_text(encoding="utf-8")
    seed = SEED.read_text(encoding="utf-8")
    implementer = IMPLEMENTER.read_text(encoding="utf-8")
    # Pin the dispatch clause per surface, not the bare token: every one of these
    # files names `implementer` for other reasons, so a token check stays green
    # when the dispatch rule itself is deleted.
    assert "dispatches each plan task in topological" in supervisor
    assert "one `implementer` at a time" in seed
    assert "controller-supplied execution root" in implementer
    fallback = supervisor.split("## Single-agent fallback", 1)[1].split(
        "## Cross-references", 1
    )[0]
    assert "no `implementer`-matching subagent is installed" in fallback
    assert "single-agent mode" in fallback
    record = next(
        item
        for item in json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
        if item["id"] == "phase1-disabled-parallel-commands"
    )
    # Pin the dispatch clause, not the bare token: `expected_output` mentions
    # `implementer` twice, so a token check survives deleting the dispatch half.
    expected = record["expected_output"]
    assert "Dispatch `implementer` tasks sequentially" in expected
    assert "one implementer at a time" in expected


def test_guide_keeps_the_phase_one_limit_and_explains_dispatch() -> None:
    """The public guide explains the current sequential behavior, not Phase 2."""
    guide = GUIDE.read_text(encoding="utf-8")
    assert (
        "Parallel fan-out (`dispatch-decision`, `worktree`, `auto-parallel`) is "
        "disabled in Phase 1"
    ) in guide
    assert "controller dispatches each plan task sequentially" in guide
    assert "one implementer at a time" in guide
