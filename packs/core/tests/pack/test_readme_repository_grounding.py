"""Documentation checks for the repository-grounding README section.

Contract: packs/core/README.md describes the optional-intelligence seam.

The README must name `repository-grounding`, state that the baseline needs no
provider, and avoid naming a specific provider as a requirement. These checks
pin the public-facing documentation against the contract without reading above
packs/core.
"""

from __future__ import annotations

from pathlib import Path

# PACK_ROOT = packs/core/
# File location: packs/core/tests/pack/test_readme_repository_grounding.py
#   parents[0] = packs/core/tests/pack/
#   parents[1] = packs/core/tests/
#   parents[2] = packs/core/
PACK_ROOT = Path(__file__).resolve().parents[2]
README = PACK_ROOT / "README.md"

_SECTION_HEADING = "## Repository grounding"


def _read() -> str:
    """Read the README as UTF-8."""
    return README.read_text(encoding="utf-8")


def _section() -> str:
    """Return the collapsed repository-grounding section text.

    Collapsed so line wrapping does not affect phrase assertions.
    """
    body = _read()
    if _SECTION_HEADING not in body:
        raise AssertionError(
            f"packs/core/README.md has no section {_SECTION_HEADING!r}; "
            "the repository-grounding section must be present"
        )
    start = body.index(_SECTION_HEADING)
    # Slice to the next `---` separator or end of file.
    rest = body[start:]
    sep_idx = rest.find("\n---\n", len(_SECTION_HEADING))
    if sep_idx != -1:
        rest = rest[:sep_idx]
    return " ".join(rest.split())


def test_readme_names_repository_grounding_skill() -> None:
    """The README section names repository-grounding as a skill.

    A future edit that renames or removes the section, or that drops the skill
    name, fails this test, so the contract stays visible in the README.
    """
    section = _section()
    assert "`repository-grounding`" in section, (
        "packs/core/README.md § Repository grounding must name the "
        "`repository-grounding` skill"
    )


def test_readme_states_baseline_needs_no_provider() -> None:
    """The section states the baseline works without a provider.

    The key adopter-facing contract: installing Core gives useful grounding
    results even when no code-intelligence tool is present. The section must
    say so explicitly so adopters know no extra install step is required.
    """
    section = _section()
    assert "no provider" in section.lower(), (
        "packs/core/README.md § Repository grounding must state that the "
        "baseline works without a provider (no provider, index, language server, "
        "or optional pack is required)"
    )


def test_readme_states_no_provider_index_or_optional_pack_required() -> None:
    """The section says no provider, index, or optional pack is required.

    This pins the specific phrasing that makes the contract machine-checkable:
    an edit that softens the claim to 'usually not required' or drops the
    sentence fails this test.
    """
    section = " ".join(_section().split())
    assert (
        "No provider, index, language server, or optional pack is required."
        in section
    ), (
        "packs/core/README.md § Repository grounding must keep the exact "
        "no-provider-required sentence"
    )


def test_readme_does_not_name_golden_provider_as_requirement() -> None:
    """The section does not name a specific provider as a requirement.

    Naming a golden provider — Wicked Estate, code-intelligence pack, or any
    specific product — as required would contradict the provider-neutral
    contract. The section may describe what any exposed provider can add, but
    must not make one a prerequisite.
    """
    section = _section()
    # These phrases would indicate a specific provider is required.
    for phrase in (
        "wicked estate",
        "code-intelligence pack",
        "install wicked",
        "require wicked",
        "require code-intelligence",
    ):
        assert phrase not in section.lower(), (
            f"packs/core/README.md § Repository grounding must not name a "
            f"golden provider as a requirement; found {phrase!r}"
        )


def test_readme_states_providers_used_in_native_shape() -> None:
    """The section states providers are used in their native shape.

    This pins the no-common-schema contract from the adopter perspective: a
    capability that the active host exposes is called in whatever form that
    host provides, not through a normalized wrapper.
    """
    section = _section()
    assert "native shape" in section, (
        "packs/core/README.md § Repository grounding must state that providers "
        "are used in their native shape (no common schema)"
    )


def test_readme_states_provider_output_is_data() -> None:
    """The section states provider output is treated as attributed data.

    This pins the AC-0014 consumer-facing rule: provider output cannot be
    instruction or authority. The README must say so so adopters know the
    skill's safety model.
    """
    section = _section()
    flat = " ".join(section.split())
    assert "never as instruction or authority" in flat, (
        "packs/core/README.md § Repository grounding must state that provider "
        "output is treated as attributed data"
    )


def test_readme_states_locators_read_through_locator_reader() -> None:
    """The section states provider-returned locators go through the locator reader.

    This pins the confinement contract: raw locator text never reaches a shell
    or host file tool. The README must name this boundary.
    """
    section = _section()
    assert "locator reader" in section, (
        "packs/core/README.md § Repository grounding must state that "
        "provider-returned locators are read only through the locator reader"
    )
