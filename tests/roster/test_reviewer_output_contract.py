"""Both reviewers state an output contract the review classifier and schemas accept.

`adversarial-reviewer` (core) and `experience-reviewer` (experience-design) each
show a concrete finding line; those lines must parse through core's classifier
exactly as a controller would read them. Each Typed report section must name
the fields `finding.v1` requires and the statuses `review-report.v1` allows.
Roster-owned because it reads core's classifier, a second pack, and `contracts/`.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]
ADVERSARIAL = ROOT / "packs/core/.apm/agents/adversarial-reviewer.md"
EXPERIENCE = ROOT / "packs/experience-design/.apm/agents/experience-reviewer.md"
CLASSIFIER = ROOT / "packs/core/.apm/skills/work-loop/scripts/review-artifact.py"
DELIVERY = ROOT / "contracts/delivery"
FINDING_MARKER = re.compile(r"^\*\*\d+\.")


def _classifier() -> ModuleType:
    """Load core's review classifier under a pack-and-skill-unique name."""
    spec = importlib.util.spec_from_file_location(
        "core_work_loop_review_artifact_for_reviewer_contract", CLASSIFIER
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Dataclasses resolve their module through `sys.modules` while executing.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _flat(text: str) -> str:
    """Collapse whitespace so a prose pin survives a reflow."""
    return " ".join(text.split())


def _section(text: str, heading: str) -> str:
    """Return one `## ` section, up to the next `## ` heading outside a fence."""
    lines = text.splitlines()
    start = lines.index(heading)
    in_fence = False
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("```"):
            in_fence = not in_fence
        elif not in_fence and lines[index].startswith("## "):
            return "\n".join(lines[start:index])
    return "\n".join(lines[start:])


def _concrete_finding_lines(path: Path) -> list[str]:
    """Finding-marker lines holding no `<` placeholder, stripped."""
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return [line for line in lines if FINDING_MARKER.match(line) and "<" not in line]


@pytest.mark.parametrize("path", [ADVERSARIAL, EXPERIENCE], ids=lambda p: p.stem)
def test_every_concrete_finding_line_parses_once(path: Path) -> None:
    """Each shown finding is one finding to the parser and a strict sustained line."""
    classifier = _classifier()
    lines = _concrete_finding_lines(path)

    assert lines, path
    for line in lines:
        assert len(classifier.parse_findings(line)) == 1, line
        assert classifier.STRICT_SUSTAINED_FINDING_LINE_RE.fullmatch(line), line


def test_experience_reviewer_shows_both_anchor_forms() -> None:
    """One concrete line uses a backticked `path:line`, another a `Where:` location."""
    lines = _concrete_finding_lines(EXPERIENCE)

    assert any(re.search(r"\*\* `[^`]+:\d+`\.", line) for line in lines), lines
    assert any("** Where: " in line for line in lines), lines


def test_experience_reviewer_states_the_anchor_rule() -> None:
    """The rule names both forms and what an unanchored report costs."""
    output = _flat(
        _section(EXPERIENCE.read_text(encoding="utf-8"), "## Output — the findings block only")
    )

    assert "A finding in a file takes a backticked `path:line` right after its bold title" in output
    assert "Any other finding takes `Where: <screen/stage/brief>` there, with no period inside the location" in output
    assert "refused as `finding-unanchored`" in output


@pytest.mark.parametrize("path", [ADVERSARIAL, EXPERIENCE], ids=lambda p: p.stem)
def test_typed_report_names_the_schema_fields_and_statuses(path: Path) -> None:
    """Each Typed report section names every required finding field and status."""
    typed = _section(path.read_text(encoding="utf-8"), "## Typed report")
    finding = json.loads((DELIVERY / "finding.v1.schema.json").read_text(encoding="utf-8"))
    report = json.loads(
        (DELIVERY / "review-report.v1.schema.json").read_text(encoding="utf-8")
    )

    for field in finding["required"]:
        assert f"`{field}`" in typed, (path.name, field)
    for status in report["properties"]["terminal_status"]["enum"]:
        assert f"`{status}`" in typed, (path.name, status)


def test_experience_typed_report_states_its_rules() -> None:
    """Material scope, the indeterminate rule, and the no-request output are stated."""
    typed = _flat(_section(EXPERIENCE.read_text(encoding="utf-8"), "## Typed report"))

    assert "The typed report carries only material findings." in typed
    assert (
        "A material finding is a Blocker or Major whose defect something outside the "
        "finding establishes"
    ) in typed
    assert "A request that names none returns `indeterminate` with no findings." in typed
    assert (
        "When a material finding has no identifier in the caller-named spec to name, "
        "the status is `indeterminate` with no findings."
    ) in typed
    assert (
        "Without a typed-report request, the output block above, unchanged, is the "
        "whole output."
    ) in typed
