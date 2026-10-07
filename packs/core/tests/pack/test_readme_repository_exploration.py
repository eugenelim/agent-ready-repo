"""Documentation checks for the repository-exploration README section.

Contract: packs/core/README.md describes the optional exploration method.

The README must name `repository-exploration`, state that the skill is optional
and caller-invoked, that the caller keeps its question and stopping rule, that
providers are used in their native shape with no common schema, that examples
are illustrative, that no provider is required, that path-seeded governance
questions go to repository-grounding, and that locators go through the locator
reader. These checks pin the public-facing documentation so each claim is
machine-verifiable.
"""

from __future__ import annotations

from pathlib import Path

# PACK_ROOT = packs/core/
# File location: packs/core/tests/pack/test_readme_repository_exploration.py
#   parents[0] = packs/core/tests/pack/
#   parents[1] = packs/core/tests/
#   parents[2] = packs/core/
PACK_ROOT = Path(__file__).resolve().parents[2]
README = PACK_ROOT / "README.md"

_SECTION_HEADING = "## Repository exploration"


def _read() -> str:
    """Read the README as UTF-8."""
    return README.read_text(encoding="utf-8")


def _section() -> str:
    """Return the collapsed repository-exploration section text.

    Collapsed so line wrapping does not affect phrase assertions.
    """
    body = _read()
    if _SECTION_HEADING not in body:
        raise AssertionError(
            f"packs/core/README.md has no section {_SECTION_HEADING!r}; "
            "the repository-exploration section must be present"
        )
    start = body.index(_SECTION_HEADING)
    # Slice to the next `---` separator or end of file.
    rest = body[start:]
    sep_idx = rest.find("\n---\n", len(_SECTION_HEADING))
    if sep_idx != -1:
        rest = rest[:sep_idx]
    return " ".join(rest.split())


def test_readme_names_repository_exploration_skill() -> None:
    """The README section names repository-exploration as a skill.

    A future edit that renames or removes the section, or that drops the skill
    name, fails this test, so the contract stays visible in the README.
    """
    section = _section()
    assert "`repository-exploration`" in section, (
        "packs/core/README.md § Repository exploration must name the "
        "`repository-exploration` skill"
    )


def test_readme_states_skill_is_optional_and_caller_invoked() -> None:
    """The section states the skill is optional and caller-invoked.

    The key adopter-facing contract: the skill runs only when a caller invokes
    it; no workflow phase or automatic step triggers it. The section must say so
    explicitly so adopters know no automatic wiring exists.
    """
    section = _section()
    assert "optional" in section.lower() and "caller-invoked" in section.lower(), (
        "packs/core/README.md § Repository exploration must state that the skill "
        "is optional and caller-invoked"
    )


def test_readme_states_caller_keeps_question_and_stopping_rule() -> None:
    """The section states the caller keeps its question and stopping rule.

    This pins the caller-owned-decision contract: the skill does not override
    the caller's question, rule, or conclusion.
    """
    section = _section()
    flat = section.lower()
    assert "question" in flat and "stopping rule" in flat, (
        "packs/core/README.md § Repository exploration must state that the "
        "caller keeps its question and stopping rule"
    )


def test_readme_states_no_provider_required() -> None:
    """The section states no provider, index, language server, or optional pack is required.

    This pins the standalone contract: an adopter installing only Core gets
    useful exploration results without any extra install step.
    """
    section = _section()
    assert "no provider, index, language server, or optional pack is required" in section.lower(), (
        "packs/core/README.md § Repository exploration must state that no "
        "provider, index, language server, or optional pack is required"
    )


def test_readme_states_providers_used_in_native_shape() -> None:
    """The section states providers are used in their native shape.

    This pins the no-common-schema contract: a capability exposed by the active
    host is called in whatever form it provides, not through a normalized wrapper.
    """
    section = _section()
    assert "native shape" in section, (
        "packs/core/README.md § Repository exploration must state that providers "
        "are used in their native shape (no common schema)"
    )


def test_readme_states_examples_are_illustrative() -> None:
    """The section states that question types and provider shapes are illustrative.

    This pins the open-taxonomy contract: the section must not present a closed
    list of question types or provider shapes as the exhaustive set.
    """
    section = _section()
    assert "illustrative" in section.lower(), (
        "packs/core/README.md § Repository exploration must state that the "
        "question types and provider shapes are illustrative"
    )


def test_readme_routes_path_seeded_questions_to_grounding() -> None:
    """The section routes path-seeded governance questions to repository-grounding.

    This pins the separation-of-owners contract: exploration does not take over
    grounding work. The section must name repository-grounding as the route for
    path-seeded governance questions.
    """
    section = _section()
    assert "`repository-grounding`" in section, (
        "packs/core/README.md § Repository exploration must name "
        "`repository-grounding` as the route for path-seeded governance questions"
    )


def test_readme_states_locators_read_through_locator_reader() -> None:
    """The section states provider-returned locators go through the locator reader.

    This pins the confinement contract: raw locator text never reaches a shell
    or host file tool. The README must name this boundary.
    """
    section = _section()
    assert "locator reader" in section, (
        "packs/core/README.md § Repository exploration must state that "
        "provider-returned locators are read only through the locator reader"
    )
