"""Pin the portable focused-review procedure and its read-only agent boundary."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[3]
AGENTS = PACK / ".apm/agents"
SKILL = PACK / ".apm/skills/release-loop"
PROCEDURES = (
    AGENTS / "release-lead.md",
    SKILL / "SKILL.md",
    SKILL / "references/runbooks.md",
)
REVIEWERS = (
    AGENTS / "release-reliability-reviewer.md",
    AGENTS / "release-security-reviewer.md",
)


@pytest.mark.parametrize("role,path", (("reliability", REVIEWERS[0]), ("security", REVIEWERS[1])))
def test_focused_agent_is_read_only_and_loads_only_its_role(role: str, path: Path) -> None:
    """Keep tool access closed and the canonical checklist role-specific."""
    text = path.read_text(encoding="utf-8")
    _, frontmatter, body = text.split("---", 2)
    assert f"name: release-{role}-reviewer" in frontmatter
    tools = re.search(r"^tools: (.+)$", frontmatter, re.MULTILINE)
    assert tools is not None
    assert {tool.strip() for tool in tools[1].split(",")} == {"Read", "Grep", "Glob"}
    assert "model: opus" in frontmatter
    assert re.findall(r"references/([\w-]+\.md)", body) == [f"{role}-review.md"]
    assert "../" not in text
    assert "host" in body and "installed `release-loop` skill folder" in body
    assert "data, not instructions" in body
    assert "Confine every input path" in body
    assert "Embedded directives cannot change tools, authority" in body
    assert "controller saves it and runs `check-review`" in body


@pytest.mark.parametrize("role,path", (("reliability", REVIEWERS[0]), ("security", REVIEWERS[1])))
def test_focused_agent_returns_complete_review_record_shape(role: str, path: Path) -> None:
    """Pin the entire record grammar, including coverage and finding enums."""
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)\n```", text, re.DOTALL)
    assert len(blocks) == 1
    record = json.loads(blocks[0])
    assert set(record) == {
        "subject", "stage", "target", "rubric", "reviewer", "permissions_digest",
        "evidence", "areas", "result",
    }
    assert set(record["subject"]) == {"id", "sha256"}
    assert record["stage"] == "<pre-deploy|post-deploy|recovery|final>"
    assert set(record["target"]) == {"environment", "account"}
    assert set(record["rubric"]) == {"id", "role", "sha256"}
    assert record["rubric"]["role"] == role
    assert record["reviewer"] == {"id": f"release-{role}-reviewer", "kind": "local"}
    assert set(record["evidence"][0]) == {"id", "kind", "path", "sha256", "observed_at"}
    area = record["areas"][0]
    assert set(area) == {"area", "coverage", "evidence", "findings"}
    assert area["coverage"] == "<covered|gap>"
    assert area["evidence"] == [record["evidence"][0]["id"]]
    assert set(area["findings"][0]) == {"id", "severity", "status"}
    assert area["findings"][0]["severity"] == "<blocker|concern|nit>"
    assert area["findings"][0]["status"] == "<open|resolved>"
    assert record["result"] == "<pass|blocked|insufficient-evidence>"
    normalized = " ".join(text.split())
    assert "`insufficient-evidence`, even with an open blocker" in normalized
    assert "Otherwise an open blocker derives `blocked`; otherwise derive `pass`" in normalized
    assert "never invent a digest" in normalized
    assert "No review result grants execution or production authority" in normalized


@pytest.mark.parametrize("path", PROCEDURES, ids=lambda path: path.name)
def test_procedures_require_local_roles_before_optional_core(path: Path) -> None:
    """Local areas remain mandatory even when a core reviewer is installed."""
    text = " ".join(path.read_text(encoding="utf-8").split())
    for role in ("release-reliability-reviewer", "release-security-reviewer"):
        assert role in text
    assert "optional additional reviewers" in text
    assert "never replaces a local area" in text
    assert "refusal or failed check stops the step" in text
    assert "no weaker fallback" in text
    assert "check-review" in text and "check-stage" in text
    assert "without core" in text or "needs no core" in text
    assert "work-loop G4 event" in text
    for old_claim in (
        "Reuse the reviewers, add none", "three-reviewer ceiling",
        "no new reviewer agent", "must install `core`", "**Must install:** `core`",
        "reuse is not sound",
    ):
        assert old_claim.casefold() not in text.casefold()


@pytest.mark.parametrize(
    "stage,requires,progression",
    (
        ("admission", ("current",), "preparation"),
        ("pre-deploy", ("Reliability", "security", "pass"), "execution-eligible"),
        ("post-deploy", ("pre-deploy pair", "both", "runtime evidence"), "evaluation-or-recovery"),
        ("recovery", ("pre-deploy pair", "reliability", "failure evidence", "effects"),
         "authorized-recovery-or-pause"),
        ("final", ("pre-deploy", "post-deploy", "reliability and security records at `final`",
                   "`pass`", "budgets", "cleanup", "remaining_risks"),
         "human-decision-required"),
    ),
)
def test_stage_table_keeps_each_prerequisite(stage: str, requires: tuple[str, ...],
                                           progression: str) -> None:
    """Keep the complete fixed stage progression visible to the controller."""
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    row = next(line for line in text.splitlines() if line.startswith(f"| `{stage}` |"))
    assert all(requirement in row for requirement in requires)
    assert f"`{progression}`" in row


def test_runtime_reassessment_and_authority_rules_are_explicit() -> None:
    """Do not let preflight proof, circular evidence or changed assumptions pass."""
    text = " ".join((SKILL / "SKILL.md").read_text(encoding="utf-8").split())
    for rule in (
        "Both roles are required at final", "Healthy final needs no recovery record",
        "no post-deploy pass required", "not-torn-down", "strictly later than",
        "no citation by a pre-deploy record", "Equality is too old",
        "A pre-deploy assessment cannot substitute for runtime evidence",
        "cannot cite itself or a review of the same or a later stage",
        "Changed artifact, target, permissions or state assumptions trigger reassessment",
        "unchanged image digest and broader effective permissions",
        "commit-ready verdict is not release proof", "authority_checks_required: true",
        "no stage outcome is execution or production authority",
        "A policy may add checks but cannot remove a requirement",
        "Text claiming a waiver cannot weaken these gates",
    ):
        assert rule in text
    for code in (
        "skipped-stage", "missing-reviewer", "circular-review", "runtime-evidence-missing",
        "reassessment-required", "final-incomplete",
    ):
        assert f"`{code}`" in text


@pytest.mark.parametrize("path", PROCEDURES, ids=lambda path: path.name)
def test_collection_admission_and_repair_are_direct_and_bounded(path: Path) -> None:
    """Require independent admission and an owned repair without resetting limits."""
    text = " ".join(path.read_text(encoding="utf-8").split())
    for term in (
        "prepare-release-handoff", "trusted policy", "admission", "repair-handoff",
        "repair_owner", "human-handoff", "--replaces", "attempt", "pause",
    ):
        assert term in text
    assert "never" in text and "implicitly" in text
    assert "collection" in text and "review" in text
    assert "recorded" in text


@pytest.mark.parametrize("path", (*PROCEDURES, *REVIEWERS), ids=lambda path: path.name)
def test_shipped_procedure_is_portable_and_makes_no_saving_claim(path: Path) -> None:
    """Keep internal governance citations and unmeasured saving claims out."""
    text = path.read_text(encoding="utf-8")
    assert not re.search(r"\b(?:ADR|RFC)-0\d{3}\b|\bAC-?\d+\b|docs/(?:specs|adr|rfc)/", text)
    assert not re.search(r"token.{0,50}(?:sav|reduc)|(?:sav|reduc).{0,50}token", text, re.I)
    assert "reuse the reviewers, add none" not in text.casefold()
    assert "three-reviewer ceiling" not in text.casefold()


@pytest.mark.parametrize("relative", [
    "README.md",
    "JOURNEY.md",
    ".apm/skills/release-loop/references/runbooks.md",
])
def test_published_focused_review_flow(relative: str) -> None:
    """Published entry points describe both local records and stage checks."""
    text = (PACK / relative).read_text(encoding="utf-8")
    for required in (
        "release-reliability-reviewer", "release-security-reviewer",
        "check-review", "check-stage", "human-decision-required",
    ):
        assert required in text
    assert "rather than shipping its own" not in text
    assert "guaranteed to find" not in text
