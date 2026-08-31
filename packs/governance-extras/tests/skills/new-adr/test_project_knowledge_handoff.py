from __future__ import annotations

import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "new-adr" / "SKILL.md"


def _gate() -> str:
    return SKILL.read_text(encoding="utf-8").split(
        "## Project-knowledge gate: `adr-accepted`", 1
    )[1]


def test_adr_capture_requires_decision_maker_acceptance() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "boundaries: [filesystem_read_untrusted, filesystem_write]" in text
    proposed = text.index("10. Leave the status `Proposed`")
    gate = text.index("## Project-knowledge gate: `adr-accepted`")

    assert proposed < gate
    section = _gate()
    assert "decision-maker sign-off" in section
    assert "`Proposed` to `Accepted`" in section
    assert "Preview confirmation, Proposed-file creation" in section
    assert "rejected or abandoned" in section


def test_adr_gate_preserves_decision_authority_and_public_seam() -> None:
    section = _gate()

    for field in (
        "contract_version",
        "lesson",
        "kind",
        "project_scope",
        "competency_facets",
        "destination_hint",
        "producer",
        "semantic_gate",
        "provenance",
        "freshness_anchor",
        "observed_at",
        "privacy_attestation",
    ):
        assert f"`{field}`" in section
    assert "`producer.workflow: new-adr`" in section
    assert "`producer.workflow_version`" in section
    assert "`semantic_gate.name: adr-accepted`" in section
    assert "repository-relative ADR as the artifact" in section
    assert "project-knowledge --capture" in section
    assert "decision, context, consequences, alternatives, or rationale" in section
    assert "workflow-receipts" in section
    assert "same `adr-accepted` gate" in section
    assert "direct-maintainer-pending" in section
    assert "project-knowledge unavailable" in section
    assert "no fallback file" in section
    assert "native real-path" in section
    assert "Git relocation variables removed" in section
    assert "lexical dot-segment traversal" in section
    for refusal in ("link", "junction", "reparse-point", "non-file", "I/O", "containment uncertainty"):
        assert refusal in section
    assert "committed Git blob" in section
    assert "CQ-DESIGN" in section
    assert "one query plus at most one refinement" in section
    assert "knowledge_store.py" not in section
    assert "never imports a private writer" in section
    assert "invents IDs" in section
    assert "selects" in section
    assert "a partition" in section
    assert "verification and review barrier" in section


def test_instructed_producer_version_is_decoupled_from_the_pack_release() -> None:
    """The gate must instruct a contract identifier, not the pack release.

    Instructing the shipped release made every governance-extras bump a prose
    edit here, and recorded a release number in a field whose job is to say
    which producer contract emitted the observation — free text the schema
    never parses and no consumer branches on. Asserting the literal, and that
    the release string is absent, means re-introducing the mirror reddens this
    test instead of shipping.
    """
    release = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))[
        "pack"
    ]["version"]
    section = _gate()

    assert "`new-adr-producer-profile.v1`" in section
    assert release != "new-adr-producer-profile.v1"
    assert release not in section
