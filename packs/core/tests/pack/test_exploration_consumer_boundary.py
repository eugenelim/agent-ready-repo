"""Absence scan: consuming procedures gain no repository-exploration wiring.

Contract: packs/core main-procedure skills and review agents must not name
repository-exploration and must not gain provider discovery, setup, invocation,
freshness, or fallback phrases. Exploration is an optional caller-invoked
method, not a wired phase.

Phrase set reused from test_grounding_delegation.py (packs/core/tests/skills/
new-spec/test_grounding_delegation.py), covering the same provider-lifecycle
surfaces.
"""

from __future__ import annotations

from pathlib import Path

# PACK_ROOT = packs/core/
# File location: packs/core/tests/pack/test_exploration_consumer_boundary.py
#   parents[0] = packs/core/tests/pack/
#   parents[1] = packs/core/tests/
#   parents[2] = packs/core/
PACK_ROOT = Path(__file__).resolve().parents[2]

# Literal paths within the pack — satisfies lint-pack-test-boundary.py.
_WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
_NEW_SPEC_SKILL = PACK_ROOT / ".apm" / "skills" / "new-spec" / "SKILL.md"
_BUG_FIX_SKILL = PACK_ROOT / ".apm" / "skills" / "bug-fix" / "SKILL.md"
_EXPLAIN_DIFF_SKILL = PACK_ROOT / ".apm" / "skills" / "explain-diff" / "SKILL.md"
_ADVERSARIAL_REVIEWER = PACK_ROOT / ".apm" / "agents" / "adversarial-reviewer.md"
_QUALITY_ENGINEER = PACK_ROOT / ".apm" / "agents" / "quality-engineer.md"
_SECURITY_REVIEWER = PACK_ROOT / ".apm" / "agents" / "security-reviewer.md"
_SHAPING_REVIEWER = PACK_ROOT / ".apm" / "agents" / "shaping-reviewer.md"
_FINDING_ADJUDICATOR = PACK_ROOT / ".apm" / "agents" / "finding-adjudicator.md"

# All files subject to the absence check.
_SUBJECT_FILES = (
    _WORK_LOOP_SKILL,
    _NEW_SPEC_SKILL,
    _BUG_FIX_SKILL,
    _EXPLAIN_DIFF_SKILL,
    _ADVERSARIAL_REVIEWER,
    _QUALITY_ENGINEER,
    _SECURITY_REVIEWER,
    _SHAPING_REVIEWER,
    _FINDING_ADJUDICATOR,
)

# Provider-lifecycle phrase sets, identical to test_grounding_delegation.py.
_PROVIDER_SETUP_PHRASES = ("provider setup", "install the provider", "configure the provider")
_PROVIDER_INVOCATION_PHRASES = ("provider invocation", "invoke the provider", "call the provider")
_INDEX_FRESHNESS_PHRASES = ("index freshness", "index refresh", "refresh the index", "stale index")
_PROVIDER_FALLBACK_PHRASES = (
    "provider fallback",
    "provider is unavailable",
    "if the provider fails",
    "if the provider",
    "provider identity",
)


def _flat(path: Path) -> str:
    """Return the file's text with whitespace collapsed for phrase matching."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_all_subject_files_exist() -> None:
    """Every subject file is present so absence checks are not vacuous."""
    for path in _SUBJECT_FILES:
        assert path.is_file(), (
            f"{path.relative_to(PACK_ROOT)} must exist for the absence check "
            "to be meaningful; a renamed or deleted file should update this test"
        )


def test_subject_files_do_not_name_repository_exploration() -> None:
    """None of the consuming procedures names repository-exploration.

    Naming repository-exploration in a consuming workflow procedure would wire
    it as a required phase, violating the optional caller-invoked contract.
    Each file is checked independently so a failure names the offending file.
    """
    for path in _SUBJECT_FILES:
        text = _flat(path)
        rel = str(path.relative_to(PACK_ROOT))
        assert "repository-exploration" not in text, (
            f"{rel} must not name `repository-exploration`; adding it would "
            "wire the optional method as a required phase in a consuming procedure"
        )


def test_subject_files_carry_no_provider_setup_phrases() -> None:
    """None of the subject files contains provider setup instructions.

    Provider setup — installing, configuring, or authenticating to a provider —
    belongs in the exploration skill, not in consuming procedures.
    """
    for path in _SUBJECT_FILES:
        text = _flat(path)
        rel = str(path.relative_to(PACK_ROOT))
        for phrase in _PROVIDER_SETUP_PHRASES:
            assert phrase not in text.lower(), (
                f"{rel} must not contain provider setup phrase {phrase!r}; "
                "provider lifecycle belongs in repository-exploration, not here"
            )


def test_subject_files_carry_no_provider_invocation_phrases() -> None:
    """None of the subject files contains provider invocation steps.

    Provider invocation steps in a consuming procedure would embed exploration
    provider logic in workflows that must remain provider-neutral.
    """
    for path in _SUBJECT_FILES:
        text = _flat(path)
        rel = str(path.relative_to(PACK_ROOT))
        for phrase in _PROVIDER_INVOCATION_PHRASES:
            assert phrase not in text.lower(), (
                f"{rel} must not contain provider invocation phrase {phrase!r}; "
                "invocation belongs in repository-exploration, not here"
            )


def test_subject_files_carry_no_index_freshness_phrases() -> None:
    """None of the subject files contains index-freshness instructions.

    Index freshness management must not appear in consuming procedures; it
    belongs in the exploration skill's own guidance.
    """
    for path in _SUBJECT_FILES:
        text = _flat(path)
        rel = str(path.relative_to(PACK_ROOT))
        for phrase in _INDEX_FRESHNESS_PHRASES:
            assert phrase not in text.lower(), (
                f"{rel} must not contain index-freshness phrase {phrase!r}; "
                "index lifecycle belongs in repository-exploration, not here"
            )


def test_subject_files_carry_no_provider_fallback_phrases() -> None:
    """None of the subject files contains a provider fallback branch.

    Fallback logic — handling provider failure, unavailability, or poor fit —
    must not appear in consuming procedures; it belongs in repository-exploration.
    """
    for path in _SUBJECT_FILES:
        text = _flat(path)
        rel = str(path.relative_to(PACK_ROOT))
        for phrase in _PROVIDER_FALLBACK_PHRASES:
            assert phrase not in text.lower(), (
                f"{rel} must not contain provider fallback phrase {phrase!r}; "
                "fallback logic belongs in repository-exploration, not here"
            )
