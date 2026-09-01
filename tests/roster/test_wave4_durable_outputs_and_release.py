"""Whole-surface durable-output and release checks for RFC-0096 Wave 4."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "docs/specs/close-work-extraction-and-immediate-disposition"
SURVEY = ROOT / "docs/rfc/0096-notes/open-source-context-lifecycle-survey.md"


def _read(relative: str) -> str:
    """Read one UTF-8 repository surface."""
    return (ROOT / relative).read_text(encoding="utf-8")


def _assert_core_manifest_versions_agree(
    pack: dict[str, object], plugin: dict[str, object]
) -> None:
    """Require the shipped pack and plugin manifests to carry one version."""
    assert pack["pack"]["version"] == plugin["version"]


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

    # AC14: the user-facing how-to must keep naming every required record field
    # for the two non-deleting dispositions; without this they are deletable
    # table prose.
    # Whitespace-normalized: these phrases are long enough to wrap, and a
    # reflow must not silently disarm the pin.
    how_to_flat = " ".join(how_to.split())
    for phrase in (
        "Record a bounded reason, an owner role, and a human-supplied review date",
        "Report the target, evidence, and missing authority without probing",
        # AC11/AC20: the maintainer-facing recovery instruction must carry the
        # same residue-identity contract the skill and the code do, or a
        # maintainer can restore residue the tool proved is not the confirmed
        # inode.
        "identity-confirmed",
        "identity-mismatch",
        "unverified",
        "Restore only an `identity-confirmed` residue",
    ):
        assert phrase in how_to_flat, phrase


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

    _assert_core_manifest_versions_agree(pack, plugin)
    assert "close-work" in pack["pack"]["evals"]["skills"]
    # Assert the invariant, not the calendar day. The release date is not this
    # test's to own — it moved twice while this branch was in review, and each
    # slip reddened a suite for a reason unrelated to the declaration here. The
    # version coupling above is the real contract; a dated top-level heading in
    # the documented shape is all this line needs.
    assert re.search(
        r"^## \[core\]\[2\.15\.0\] — \d{4}-\d{2}-\d{2}$", changelog, re.M
    ), "no dated top-level core changelog heading for this wave's release"
    assert "allowed-tools: Read Write Edit Bash" in skill
    for forbidden in ("WebFetch", "WebSearch", "MCP", "Browser", "Task"):
        assert forbidden not in skill.split("---", 2)[1]


def test_core_release_metadata_rejects_manifest_version_drift() -> None:
    """Mutation guard: a one-sided manifest-version change must be rejected."""
    pack = {"pack": {"version": "2.15.1"}}
    plugin = {"version": "2.15.0"}

    with pytest.raises(AssertionError):
        _assert_core_manifest_versions_agree(pack, plugin)


def test_wave4_docs_keep_the_remaining_wave_boundary() -> None:
    """Waves 5 and 6 have shipped; Wave 7 retains its stated boundary."""
    # Asserted against the architecture document alone. The earlier form joined
    # three files, so the mutation clause held only because these strings
    # happened to appear nowhere else; scoping it to the owning document makes
    # deleting a statement from that document the thing that reddens this test.
    architecture = _read("docs/architecture/work-intake-and-artifact-routing.md")
    # Whitespace-normalized for the same reason as the AC11/AC14 pin above: these
    # statements are long enough to wrap, and a reflow must not redden a doctrine
    # test whose meaning is unchanged.
    normalized = " ".join(architecture.split())
    for statement in (
        "Wave 5 has shipped the lifecycle record, review-date, due-state, and retirement engine",
        "Wave 6 has shipped ordinary-context exclusion",
        "Wave 7 owns historical migration and pruning behavior",
    ):
        assert statement in normalized, statement
    assert "Wave 6 and 7 own ordinary-context exclusion" not in normalized
