"""Construction contracts for architect-design's justified-surface guidance."""

from pathlib import Path

import yaml

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "architect-design" / "SKILL.md"
RUBRIC = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "architect-design"
    / "references"
    / "design-doc-rubric.md"
)


class _NoDuplicateKeyLoader(yaml.SafeLoader):
    """A SafeLoader that refuses a repeated mapping key.

    `yaml.safe_load` keeps the last of two identical keys, so frontmatter
    declaring `boundaries` twice — once widened, once at the baseline — would
    satisfy an assertion about the parsed value while shipping the widened
    line. `agentbundle`'s skill-spec lint and catalogue verify both reject a
    duplicate frontmatter key, but a pack test may not import above its own
    pack, so this reuses that control's semantics rather than its code.
    """


def _no_duplicates(loader: yaml.SafeLoader, node: yaml.MappingNode) -> dict:
    """Construct a mapping, raising on the first repeated key."""
    mapping: dict = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=True)
        if key in mapping:
            raise AssertionError(
                f"duplicate frontmatter key {key!r} at line "
                f"{key_node.start_mark.line + 1}"
            )
        mapping[key] = loader.construct_object(value_node, deep=True)
    return mapping


_NoDuplicateKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_duplicates
)


def _flat(path: Path) -> str:
    """Return whitespace-normalized portable skill text."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_author_reuses_existing_answers_and_stops_before_full_design() -> None:
    """Adequate prior work ends authoring without a new design artifact."""
    text = _flat(SKILL)

    assert "adequate prior design or existing capability" in text
    assert "Reuse it when it resolves the current question." in text
    assert "If no real choice remains, create no new artifact." in text
    assert "Stage 0 is a valid stopping point" in text
    assert "Create a full design only when unresolved trade-offs still require it." in text


def test_full_design_justifies_its_surface_and_claims() -> None:
    """Every added design element and necessary external claim has a basis."""
    text = _flat(SKILL)
    rubric = _flat(RUBRIC)

    for required in (
        "For every component and boundary, name the current goal, constraint, or prioritized quality attribute that justifies it.",
        "Remove unsupported future-proofing and unnecessary claims.",
        "one bounded check of its named target",
        "assumption or discovery predicate",
    ):
        assert required in text
    assert "Every component and boundary names the current goal, constraint, or prioritized quality attribute that justifies it." in rubric
    assert "Removes unsupported future-proofing." in rubric
    assert "Each necessary cross-document assertion has one bounded check" in rubric


def test_author_save_contract_is_confined_to_the_configured_output_root() -> None:
    """The author guidance refuses unsafe destinations before a directed save."""
    text = _flat(SKILL)

    for required in (
        "A Stage-0 or full-design save stays inside the resolved configured output root.",
        "Before any mutation, refuse an unsafe, link-like, identity-changing, or out-of-root target.",
        "does not add a runtime save gate",
    ):
        assert required in text


def test_direct_architecture_requests_stay_with_the_architecture_author() -> None:
    """Direct design work neither needs synthetic intent nor shaping review."""
    text = _flat(SKILL)

    assert "A direct architecture request needs no synthetic intent" in text
    assert "does not dispatch shaping review" in text
    assert "shaping-review" not in text


def test_author_authority_is_exactly_the_declared_baseline() -> None:
    """The author has no tool list and only its declared metadata boundaries.

    Authority is asserted key by key rather than by matching the whole
    frontmatter as one string. Full-text equality also pinned the description's
    summary of what the skill produces, which carries no authority and is
    rewritten whenever that output changes. A key set plus an exact boundaries
    list fails on any widening of authority and stays silent on that wording;
    a new top-level or metadata key is caught by the key-set assertions.

    The description is not free prose, though. The schema calls it the trigger
    surface shown to IDEs, so the text deciding *which* skill answers is a
    routing boundary: the invocation scope and trigger list that open it, and
    the refusal that hands diagrams and critiques to `architect-diagram` and
    `architect-review` at the end. Both ends are pinned by equality, not by
    substring, so routing text can be neither prepended nor appended.

    The span between them is what the skill produces, and it is deliberately
    unguarded: rewriting it is the whole point of the scope-routed authoring
    model, and an exact pin there is the brittleness this assertion removes.

    Named blind spot, and the reason it is accepted: routing text inserted into
    that middle span passes. Bounding the middle needs either equality on the
    whole description — which is what was removed — or an exhaustive list of
    phrasings that widen routing, which cannot converge. So the claim is
    narrowed to what the check reaches: the routing boundary cannot grow at
    either end of the description without this assertion failing.
    """
    raw = SKILL.read_text(encoding="utf-8").split("---", 2)[1]

    assert "allowed-tools:" not in raw
    frontmatter = yaml.load(raw, Loader=_NoDuplicateKeyLoader)

    assert set(frontmatter) == {"name", "description", "metadata"}
    assert frontmatter["name"] == "architect-design"
    assert set(frontmatter["metadata"]) == {"boundaries"}
    assert frontmatter["metadata"]["boundaries"] == [
        "filesystem_read_untrusted",
        "filesystem_write",
        "network_fetch",
    ]
    description = frontmatter["description"]
    routing_head = (
        "Use when the user is framing a problem, weighing a technical choice, "
        "or designing a system or integration without a diagram as the "
        "headline ask. Triggers on \"how should we\", \"we need to\", "
        "\"what's the right way to build X\", tech-selection, integration "
        "design, NFR trade-offs. "
    )
    routing_tail = (
        " Do NOT use when the ask is a diagram (use `architect-diagram`) "
        "or a critique (use `architect-review`)."
    )
    assert description.startswith(routing_head)
    assert description.endswith(routing_tail)
