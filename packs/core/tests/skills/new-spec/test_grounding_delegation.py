"""Static delegation and absence checks for the new-spec grounding step.

Contract: new-spec delegates grounding to repository-grounding (AC-0008)

new-spec step 3 names `repository-grounding` as the skill that runs the
grounding inquiry. The step must contain no provider identity, provider setup
instructions, provider invocation steps, index-freshness instructions, or
provider fallback branches. It must also carry no direct reference to the
implementation scripts that now belong to repository-grounding (they moved in
T1 and new-spec now delegates, not calls).

All paths are anchored inside packs/core and never climb above it.
"""

from __future__ import annotations

from pathlib import Path

# PACK_ROOT = packs/core/
# File location: packs/core/tests/skills/new-spec/test_grounding_delegation.py
#   parents[0] = packs/core/tests/skills/new-spec/
#   parents[1] = packs/core/tests/skills/
#   parents[2] = packs/core/tests/
#   parents[3] = packs/core/
PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "new-spec" / "SKILL.md"


def _flat(path: Path) -> str:
    """Return the file's text with whitespace collapsed for phrase matching."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_new_spec_delegates_grounding_to_repository_grounding_by_skill_name() -> None:
    """Step 3 names repository-grounding as the skill to run.

    The delegation wording must survive intact; its absence means new-spec
    stopped delegating and the consumer owns the grounding step again.
    """
    text = _flat(SKILL)
    assert "repository-grounding` inquiry" in text, (
        "packs/core/.apm/skills/new-spec/SKILL.md step 3 must delegate the "
        "grounding inquiry to `repository-grounding` by skill name; the phrase "
        "`repository-grounding` inquiry` is gone"
    )


def test_new_spec_step_3_names_discovery_seeds() -> None:
    """Step 3 passes discovery seeds to repository-grounding.

    A delegation without seeds would hand the skill nothing to probe,
    making the call a no-op rather than a grounding inquiry.
    """
    text = _flat(SKILL)
    assert "discovery seeds" in text, (
        "packs/core/.apm/skills/new-spec/SKILL.md step 3 must name the discovery "
        "seeds passed to repository-grounding; the phrase `discovery seeds` is gone"
    )


def test_new_spec_carries_no_explore_grounding_script_reference() -> None:
    """No direct reference to explore-grounding.py appears in new-spec.

    The script moved to repository-grounding in T1. Any surviving reference
    here would mean new-spec is calling the script directly instead of
    delegating, breaking AC-0008.
    """
    text = _flat(SKILL)
    assert "explore-grounding.py" not in text, (
        "packs/core/.apm/skills/new-spec/SKILL.md must not reference "
        "explore-grounding.py directly; that script now belongs to "
        "repository-grounding and new-spec delegates to the skill, not the script"
    )


def test_new_spec_carries_no_read_locator_script_reference() -> None:
    """No direct reference to read-locator.py appears in new-spec.

    read-locator.py is a repository-grounding script. new-spec has no
    reason to invoke it directly; doing so would embed locator-reading
    logic in a consuming workflow (AC-0008 violation).
    """
    text = _flat(SKILL)
    assert "read-locator.py" not in text, (
        "packs/core/.apm/skills/new-spec/SKILL.md must not reference "
        "read-locator.py directly; that script belongs to repository-grounding"
    )


def test_new_spec_carries_no_provider_setup_instructions() -> None:
    """Step 3 contains no provider setup instructions.

    Provider setup means installing, configuring, or authenticating to a
    provider. Those steps belong in repository-grounding's SKILL.md; putting
    them in new-spec would violate AC-0008.
    """
    text = _flat(SKILL)
    for phrase in ("provider setup", "install the provider", "configure the provider"):
        assert phrase not in text.lower(), (
            f"packs/core/.apm/skills/new-spec/SKILL.md must not contain provider "
            f"setup instructions ({phrase!r}); provider lifecycle belongs in "
            f"repository-grounding, not new-spec"
        )


def test_new_spec_carries_no_provider_invocation_steps() -> None:
    """Step 3 contains no provider invocation steps.

    Provider invocation — calling, invoking, or sending a request to a named
    provider — must not appear in new-spec. The skill delegates; it does not
    operate the provider.
    """
    text = _flat(SKILL)
    for phrase in ("provider invocation", "invoke the provider", "call the provider"):
        assert phrase not in text.lower(), (
            f"packs/core/.apm/skills/new-spec/SKILL.md must not contain provider "
            f"invocation steps ({phrase!r}); invocation belongs in "
            f"repository-grounding, not new-spec"
        )


def test_new_spec_carries_no_index_freshness_instructions() -> None:
    """Step 3 contains no index-freshness instructions.

    Index freshness — refreshing an index, checking staleness, or updating
    a provider's index — must not appear in new-spec. new-spec must delegate
    grounding and receive results; it does not manage provider lifecycle.
    """
    text = _flat(SKILL)
    for phrase in ("index freshness", "index refresh", "refresh the index", "stale index"):
        assert phrase not in text.lower(), (
            f"packs/core/.apm/skills/new-spec/SKILL.md must not contain "
            f"index-freshness instructions ({phrase!r}); index lifecycle belongs "
            f"in repository-grounding, not new-spec"
        )


def test_new_spec_carries_no_provider_fallback_branch() -> None:
    """Step 3 contains no provider fallback branch.

    A fallback branch — conditional logic that handles provider failure,
    unavailability, or poor fit — must not appear in new-spec. That logic
    belongs in repository-grounding. new-spec receives the grounding result,
    whatever its source.
    """
    text = _flat(SKILL)
    for phrase in (
        "provider fallback",
        "provider is unavailable",
        "if the provider fails",
        "if the provider",
        "provider identity",
    ):
        assert phrase not in text.lower(), (
            f"packs/core/.apm/skills/new-spec/SKILL.md must not contain a "
            f"provider fallback branch ({phrase!r}); fallback logic belongs "
            f"in repository-grounding, not new-spec"
        )
