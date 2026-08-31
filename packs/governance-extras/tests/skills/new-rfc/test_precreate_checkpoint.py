"""Static contract tests for the new-RFC pre-create checkpoint."""

from pathlib import Path


SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "new-rfc"
    / "SKILL.md"
)


def _checkpoint() -> str:
    """Return the pre-create section, excluding later authoring steps."""
    return SKILL.read_text(encoding="utf-8").split(
        "0. **Pre-create artifact checkpoint — mandatory.**", 1
    )[1].split("1. Find the next ordinal", 1)[0]


def test_precreate_checkpoint_precedes_ordinal_and_all_creation_work() -> None:
    """Cheaper routes return before identifiers, targets, or writes exist."""
    text = SKILL.read_text(encoding="utf-8")
    checkpoint = text.index("0. **Pre-create artifact checkpoint — mandatory.**")

    assert checkpoint < text.index("1. Find the next ordinal")
    assert checkpoint < text.index("2. **Resolve the target")
    assert checkpoint < text.index("5. **Preview the target, create the file")

    section = _checkpoint()
    compact = " ".join(section.split())
    for route in (
        "skip",
        "reuse",
        "amend",
        "reference",
        "ADR",
        "spec",
        "PR",
        "issue",
        "architect-design",
        "reversible, time-bounded trial",
    ):
        assert route in section
    assert compact.lower().count("report the selected route once and return") == 3
    assert "Do not resolve an ordinal, create a directory or index, choose a target, or draft body text." in compact


def test_warranted_rfc_retains_existing_authoring_and_review_gates() -> None:
    """The checkpoint only cuts cheaper routes; it does not weaken RFC gates."""
    text = SKILL.read_text(encoding="utf-8")

    for gate in (
        "**Research + de-risk checkpoint — gated.**",
        "Preview the target, create the file, then draft the body.",
        "**Pre-handoff gate — mandatory, before status → Open.**",
        "Dispatch `adversarial-reviewer`",
        "Set status to `Draft` until the user is ready to circulate",
        "Update the RFC index table",
    ):
        assert gate in text


def test_rfc_write_contract_refuses_unsafe_targets_before_mutation() -> None:
    """Every directed write stays under the resolved RFC owner root."""
    text = SKILL.read_text(encoding="utf-8")
    section = _checkpoint()

    assert "RFC owner root" in text
    for target in ("RFC target", "index", "companion-note"):
        assert target in text
    for refusal in ("unsafe", "link-like", "identity-changing", "out-of-root"):
        assert refusal in text
    assert "Refuse an unsafe, link-like," in text
    assert "out-of-root target before any mutation" in text
    assert section


def test_drafting_minimizes_claims_and_labels_ungrounded_necessary_claims() -> None:
    """Necessary cross-document claims are checked or explicitly qualified."""
    text = SKILL.read_text(encoding="utf-8")

    assert "Delete claims the decision does not need." in text
    assert "perform one bounded check of its named target" in text
    assert "mark the claim as an assumption or discovery predicate" in text


def test_direct_rfc_request_needs_no_synthetic_intent() -> None:
    """Direct requests do not require a shaping-parent artifact."""
    text = SKILL.read_text(encoding="utf-8")

    assert "A direct RFC request needs no synthetic intent; an accepted intent or design" in text


def test_frontmatter_has_exact_new_rfc_authority() -> None:
    """The skill retains only its declared write and untrusted-read boundaries."""
    frontmatter = SKILL.read_text(encoding="utf-8").split("---", 2)[1]
    boundary_lines = [
        line.strip()
        for line in frontmatter.splitlines()
        if line.strip().startswith("boundaries:")
    ]

    assert "allowed-tools:" not in frontmatter
    assert boundary_lines == [
        "boundaries: [filesystem_read_untrusted, filesystem_write]"
    ]
