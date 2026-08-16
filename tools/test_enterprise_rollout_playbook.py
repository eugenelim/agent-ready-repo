"""Construction checks for the P5 enterprise rollout playbook."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
GUIDE = (
    REPO_ROOT
    / "guides"
    / "_shared"
    / "how-to"
    / "roll-out-agent-ready-repo-across-an-enterprise.md"
)

# STUB: AC1-AC10 — these assertions define the red contract before the guide exists.


def _require_all(text: str, required: tuple[str, ...], contract: str) -> None:
    missing = [value for value in required if value.casefold() not in text.casefold()]
    assert not missing, f"{contract} is missing: {', '.join(missing)}"


def _guide_text() -> str:
    assert GUIDE.is_file(), f"missing enterprise rollout playbook: {GUIDE}"
    return GUIDE.read_text(encoding="utf-8")


def _section(text: str, heading: str) -> str:
    marker = f"## {heading}"
    assert marker in text, f"missing section: {marker}"
    section = text.split(marker, 1)[1]
    return section.split("\n## ", 1)[0]


def test_frontmatter_and_outcome_first_opening() -> None:
    text = _guide_text()
    frontmatter = text.split("---", 2)[1]
    _require_all(
        frontmatter,
        (
            'title: "Roll out agent-ready-repo across an enterprise"',
            "summary:",
            "pack: _shared",
            "kind: how-to",
        ),
        "frontmatter",
    )

    body = text.split("---", 2)[2].lstrip()
    words = list(re.finditer(r"\b[\w'-]+\b", body))
    opening_end = words[120].start() if len(words) > 120 else len(body)
    opening = body[:opening_end]
    _require_all(
        opening,
        (
            "Use this when",
            "Prerequisites",
            "Result",
            "Champion request",
        ),
        "first 120 words",
    )
    assert "```" in opening, "the opening must include a copyable champion request"


def test_role_handoffs_and_stage_gates() -> None:
    text = _guide_text()
    handoff = _section(text, "Role handoff")
    _require_all(
        handoff,
        (
            "Champion",
            "CTO or executive sponsor",
            "Platform team",
            "Engineers and participating practitioners",
            "accepts the handoff",
            "No role silently accepts another role's decision",
        ),
        "role handoff",
    )

    stage_fields = (
        "Scope",
        "Prerequisites",
        "Participant-verifiable task",
        "Human controls",
        "Measurement",
        "Rollback",
        "Shareable artifact",
        "Recipient",
        "Exit evidence",
        "stop",
        "revise",
        "hold",
        "advance",
    )
    for stage in ("Pilot", "Wave", "Organization-wide"):
        _require_all(_section(text, stage), stage_fields, f"{stage} stage")


def test_track_and_adopter_research_constraints() -> None:
    text = _guide_text()
    _require_all(
        _section(text, "Technical track"),
        (
            "solo engineers",
            "technical PMs",
            "short activation path",
            "outcome-first language",
            "gate-based review",
            "brief or spec another engineer can act on",
        ),
        "technical track",
    )
    _require_all(
        _section(text, "Enterprise track"),
        (
            "FDE-mediated",
            "enterprise AI champions",
            "handoff completeness",
            "governance depth",
            "measurement infrastructure",
            "named internal owner",
            "independently executed client run",
            "before external support exits",
        ),
        "enterprise track",
    )
    _require_all(
        _section(text, "Non-technical track"),
        (
            "AI-naive knowledge workers",
            "UX/experience designers",
            "same-role peer champion",
            "identity-safe framing",
            "source provenance",
            "familiar deliverable",
            "quality the participant owns",
        ),
        "non-technical track",
    )
    _require_all(
        _section(text, "Research constraints"),
        (
            "Decision-point prerequisites",
            "Outcome-first vocabulary",
            "Artifact status",
            "Credential lifecycle",
            "Mutation status",
            "Participant-verifiable first task",
            "Explicit human controls",
            "Peer champion",
            "Shareable-artifact value",
        ),
        "adopter-persona research constraints",
    )


def test_reusable_checklist_decision_record_and_retrospective() -> None:
    text = _guide_text()
    _require_all(
        _section(text, "Rollout checklist"),
        (
            "Sponsor and champion ownership",
            "Participant consultation",
            "Track choice",
            "Environment and repository readiness",
            "Permissions and credentials",
            "Safe inputs",
            "Expected reads and writes",
            "Support and escalation",
            "Measurement",
            "Recovery",
            "Artifact recipient",
            "Stage-gate evidence",
            "Rollback",
        ),
        "rollout checklist",
    )
    _require_all(
        _section(text, "Stage decision record"),
        (
            "Stage and track",
            "Scope",
            "Champion",
            "Executive sponsor",
            "Platform owner",
            "Participating roles",
            "Baseline",
            "Shareable artifact and recipient",
            "Quality result",
            "Adoption measure",
            "Support burden",
            "Exceptions",
            "Unresolved risks",
            "External mutations",
            "Rollback readiness",
            "stop | revise | hold | advance",
        ),
        "stage decision record",
    )
    _require_all(
        _section(text, "Retrospective"),
        (
            "Outcome evidence",
            "Adoption evidence",
            "Quality and verification",
            "Human-control effectiveness",
            "Platform and support burden",
            "Participant voice",
            "Identity or craft concerns",
            "Incidents and external mutations",
            "Unresolved risks",
            "Changes required before another stage",
        ),
        "retrospective",
    )
    _require_all(
        _section(text, "Completion receipt"),
        (
            "Artifact status",
            "Repository writes",
            "External mutations",
            "Rollback status",
            "Unresolved risks",
            "Next allowed action",
        ),
        "stage receipt",
    )


def test_mid_market_gap_and_distribution_boundary() -> None:
    text = _guide_text()
    _require_all(
        text,
        (
            "mid-market enterprise",
            "uncharacterized",
            "FDE-outcome",
            "self-service gap",
            "no reliable self-service path",
            "live demo",
            "enterprise distribution",
            "technical distribution",
        ),
        "research gap and ownership boundary",
    )
    mid_market = _section(text, "Mid-market enterprise is uncharacterized")
    _require_all(
        mid_market,
        (
            "Do not widen a mid-market pilot",
            "requires new evidence",
        ),
        "mid-market expansion refusal",
    )
    assert re.search(r"\]\(\.\./\.\./core/how-to/run-a-live-demo\.md\)", text), (
        "missing exact Markdown link to the live-demo guide"
    )
    assert re.search(r"\]\(configure-catalogue-enterprise-distribution\.md\)", text), (
        "missing exact Markdown link to the technical enterprise-distribution guide"
    )
    assert re.search(r"\]\(build-an-org-stack-pack\.md\)", text), (
        "missing exact Markdown link to the org-stack implementation guide"
    )
    forbidden_procedure_markers = (
        "## Configure Artifactory",
        "## Configure a catalogue source",
        "## Build an org-stack pack",
        "agentbundle source add",
        "agentbundle profile",
    )
    repeated = [value for value in forbidden_procedure_markers if value in text]
    assert not repeated, (
        "the adoption playbook duplicates technical distribution procedures: "
        + ", ".join(repeated)
    )


if __name__ == "__main__":
    test_frontmatter_and_outcome_first_opening()
    test_role_handoffs_and_stage_gates()
    test_track_and_adopter_research_constraints()
    test_reusable_checklist_decision_record_and_retrospective()
    test_mid_market_gap_and_distribution_boundary()
