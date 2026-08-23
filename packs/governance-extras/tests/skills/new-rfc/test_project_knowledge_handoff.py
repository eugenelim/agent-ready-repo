from __future__ import annotations

import tomllib
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "new-rfc"
    / "SKILL.md"
)


def _gate() -> str:
    return SKILL.read_text(encoding="utf-8").split(
        "### Project-knowledge gate: `rfc-handoff-ready`", 1
    )[1]


def test_rfc_gate_follows_every_mandatory_check_and_index_write() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "boundaries: [filesystem_read_untrusted, filesystem_write]" in text
    checks = text.index("6. **Pre-handoff gate — mandatory")
    index = text.index("8. Update the RFC index table")
    gate = text.index("### Project-knowledge gate: `rfc-handoff-ready`")
    receipt = text.index("9. **Return a completion receipt**")

    assert checks < index < gate < receipt
    section = _gate()
    assert "every mandatory pre-handoff check" in section
    assert "Research findings, preview, citation-unverified" in section
    assert "unclean review" in section
    assert "abandoned" in section


def test_rfc_gate_uses_public_typed_capture_and_same_gate_receipts() -> None:
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
    assert "`producer.workflow: new-rfc`" in section
    assert "`producer.workflow_version`" in section
    assert "`semantic_gate.name: rfc-handoff-ready`" in section
    assert "RFC as the artifact" in section
    assert "project-knowledge --capture" in section
    assert "workflow-receipts" in section
    assert "same `rfc-handoff-ready` gate" in section
    assert "direct-maintainer-pending" in section
    assert "project-knowledge unavailable" in section
    assert "no fallback file" in section
    assert "native real-path" in section
    assert "Git relocation variables removed" in section
    assert "lexical dot-segment traversal" in section
    for refusal in ("symlink", "junction", "reparse-point", "non-file", "I/O", "containment uncertainty"):
        assert refusal in section
    assert "committed Git blob" in section
    assert "research corpus" in section
    assert "recommendation, option decision, or open questions" in section
    assert "CQ-DESIGN" in section
    assert "one query plus at most one refinement" in section
    assert "knowledge_store.py" not in section
    # The full producer-prohibition list, not a subset. An earlier compression of this
    # section dropped "locates journals" and "creates storage" while every substring this
    # test then asserted still passed — the test reported green over a real loss of
    # security semantics. Assert all five so that cannot recur.
    assert "never imports a private writer" in section
    assert "locates journals" in section
    assert "invents IDs" in section
    assert "selects a partition" in section
    assert "creates storage" in section
    # Same compression dropped the privacy/instruction refusal entirely.
    assert "Privacy or instruction" in section
    assert "redacted diagnostic" in section
    assert "no persisted body" in section
    # A second compression pass then dropped four more path-confinement / retention
    # controls while every assertion above still passed: the hash-read trigger, the
    # repository-root discovery step, the committed-blob *identity* (not merely a blob),
    # and the bound on what may be retained after capture. Assert each one.
    # The complete load-bearing set, enumerated by diffing the compressed section against
    # its pre-compression text rather than added reactively one review round at a time.
    # Three review rounds found 15 separate semantic losses in this section while every
    # assertion added after the previous round still passed: strengthening a check in
    # response to a found defect calibrates it to that defect, not to the class. Any future
    # edit to this section should re-derive this list from the diff, not trust it.
    for clause in (
        # path confinement and hashing
        "sha256-bytes-v1",
        "discover the repository root",
        "committed Git blob identity",
        # retention and distillation
        "{capture_id, partition}",
        "gate-local memory",
        "selection_mode: workflow-receipts",
        "Never guess IDs",
        "drain another workflow",
        # what may be captured at all
        "reusable research-navigation",
        "shipped governance-extras pack version",
        # the verification barrier before the completion receipt
        "claim persistence or reconciliation",
        "no-diff outcome",
        # enquiry bounds
        "No automatic enquiry",
    ):
        assert clause in section, f"gate section lost load-bearing clause: {clause!r}"
    assert "verification and review barrier" in section
    assert "Before step 9 emits the completion receipt" in section


def test_governance_handoff_metadata_is_descriptive_and_keeps_absence() -> None:
    pack_root = Path(__file__).resolve().parents[3]
    manifest = tomllib.loads((pack_root / "pack.toml").read_text(encoding="utf-8"))

    dependency = next(
        item
        for item in manifest["pack"]["dependencies"]["required"]
        if item["pack"] == "core"
    )
    assert dependency["version"] == "^2.0"
    handoff = next(
        item
        for item in manifest["pack"]["integrations"]
        if item["id"] == "project-knowledge-authoring-handoff"
    )
    assert handoff["kind"] == "handoff"
    assert handoff["providers"] == ["skill:project-knowledge"]
    assert handoff["consumers"] == ["skill:new-rfc", "skill:new-adr"]
    assert "named skip" in handoff["fallback"]
    assert "without fallback persistence" in handoff["fallback"]
