"""Whole-surface durable-output and release checks for RFC-0096 Wave 4."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "docs/specs/close-work-extraction-and-immediate-disposition"
SURVEY = ROOT / "docs/rfc/0096-notes/open-source-context-lifecycle-survey.md"


def _read(relative: str) -> str:
    """Read one UTF-8 repository surface."""
    return (ROOT / relative).read_text(encoding="utf-8")


def test_every_planned_durable_output_exists_at_its_owner() -> None:
    """The delivery pair is not the sole owner of lasting Wave 4 truth."""
    paths = (
        "docs/rfc/0096-portable-delivery-artifact-lifecycle.md",
        "docs/architecture/work-intake-and-artifact-routing.md",
        "guides/core/how-to/close-and-disposition-work.md",
        "guides/core/reference/work-intake-routing-and-lifecycle.md",
        "guides/core/reference/spec-shape-and-lld.md",
        "docs/CONVENTIONS.md",
        "guides/core/reference/workspace-toml-schema.md",
        "packs/core/README.md",
        "packs/core/JOURNEY.md",
        "docs/product/changelog.md",
    )
    assert all((ROOT / path).is_file() for path in paths)
    assert SURVEY.is_file()
    assert not (SPEC_DIR / "notes/open-source-context-lifecycle-survey.md").exists()

    plan = (SPEC_DIR / "plan.md").read_text(encoding="utf-8")
    assert "../../rfc/0096-notes/open-source-context-lifecycle-survey.md" in plan
    assert "](notes/open-source-context-lifecycle-survey.md)" not in plan


def test_current_docs_form_one_closeout_story() -> None:
    """Architecture, reference, how-to, and navigation agree on ownership."""
    architecture = _read("docs/architecture/work-intake-and-artifact-routing.md")
    lifecycle = _read("guides/core/reference/work-intake-routing-and-lifecycle.md")
    workspace = _read("guides/core/reference/workspace-toml-schema.md")
    how_to = _read("guides/core/how-to/close-and-disposition-work.md")
    readme = _read("packs/core/README.md")
    journey = _read("packs/core/JOURNEY.md")

    for text in (architecture, lifecycle, how_to):
        assert "disposition is intent" in text.lower()
        assert "workspace-status" in text
        assert "cool-30-days" in text
    assert "close_work.py" in architecture
    assert "behavior tests" in architecture
    assert "live coordination, not the artifact-retention unit" in workspace
    assert "status: draft" not in how_to
    assert "close-work" in readme
    assert "close-work" in journey


def test_work_loop_keeps_detail_in_a_linked_reference() -> None:
    """Main workflow remains scannable while the delivery contract stays exact."""
    skill = _read("packs/core/.apm/skills/work-loop/SKILL.md")
    reference = _read(
        "packs/core/.apm/skills/work-loop/references/delivery-contract-lifecycle.md"
    )
    assert len(skill.splitlines()) <= 1000
    assert skill.count("references/delivery-contract-lifecycle.md") >= 3
    for token in (
        "contract-amendment",
        "completed-evidence-ref",
        "Completion evidence handoff",
        "local-only",
        "PR-only",
        "Spec-plan mode",
    ):
        assert token in reference


def test_core_release_metadata_and_history_agree() -> None:
    """The invokable workflow, eval roster, plugin, and release entry ship together."""
    pack = tomllib.loads(_read("packs/core/pack.toml"))
    plugin = json.loads(_read("packs/core/.claude-plugin/plugin.json"))
    changelog = _read("docs/product/changelog.md")
    skill = _read("packs/core/.apm/skills/close-work/SKILL.md")

    assert pack["pack"]["version"] == "2.13.0"
    assert plugin["version"] == "2.13.0"
    assert "close-work" in pack["pack"]["evals"]["skills"]
    assert "## [core][2.13.0] — 2026-08-26" in changelog
    assert "allowed-tools: Read Write Edit Bash" in skill
    for forbidden in ("WebFetch", "WebSearch", "MCP", "Browser", "Task"):
        assert forbidden not in skill.split("---", 2)[1]


def test_wave4_docs_do_not_claim_later_wave_engines() -> None:
    """Cooling classification does not become retirement or context exclusion."""
    architecture = _read("docs/architecture/work-intake-and-artifact-routing.md")
    lifecycle = _read("guides/core/reference/work-intake-routing-and-lifecycle.md")
    how_to = _read("guides/core/how-to/close-and-disposition-work.md")
    combined = "\n".join((architecture, lifecycle, how_to))
    for statement in (
        "Wave 5 owns dates, clocks, due state, and retirement",
        "no clock, date,\ndue-state, retirement, ordinary-context exclusion",
        "It does not calculate dates, start a timer, or retire anything",
    ):
        assert statement in combined


def test_bookkeeping_agrees_without_closing_the_rfc_family() -> None:
    """Spec, plan, index, and workspace move together while the pair is retained."""
    spec_path = "docs/specs/close-work-extraction-and-immediate-disposition/spec.md"
    spec = _read(spec_path)
    plan = _read("docs/specs/close-work-extraction-and-immediate-disposition/plan.md")
    index = _read("docs/specs/README.md")
    workspace = tomllib.loads(_read("workspace.toml"))["ini-002"]["work"]

    active = [entry for entry in workspace["active"] if isinstance(entry, dict)]
    shipped = [entry for entry in workspace["shipped"] if isinstance(entry, dict)]
    status = next(
        line.removeprefix("- **Status:** ")
        for line in spec.splitlines()
        if line.startswith("- **Status:** ")
    )
    expected = {
        "Implementing": ("Executing", "active"),
        "Shipped": ("Done", "shipped"),
    }
    assert status in expected
    plan_status, workspace_state = expected[status]
    assert f"- **Status:** {plan_status}" in plan
    assert (
        f"| {status} | RFC-0096; Waves 1–3 (Shipped); Waves 5–7"
        in index
    )
    if status == "Shipped":
        assert "- [ ] **AC" not in spec

    memberships = {"active": active, "shipped": shipped}
    matching = [
        entry
        for entry in memberships[workspace_state]
        if entry.get("path") == spec_path
    ]
    assert len(matching) == 1
    other_state = "shipped" if workspace_state == "active" else "active"
    assert not any(
        entry.get("path") == spec_path for entry in memberships[other_state]
    )
    assert matching[0]["source"] == {
        "mode": "repo-origin",
        "ref": "docs/rfc/0096-portable-delivery-artifact-lifecycle.md",
        "revision": "6e984d67b583b36798efddbb2717ce5784572a49",
    }
    assert matching[0]["needs"] == []
