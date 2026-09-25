"""The admitted intent `intake-intent` renders satisfies the shape contract.

Covers the core half of T7 in
the intent metadata shape contract's plan. The product-engineering
template's half reads two packs and therefore lives in `tests/roster/`, which
runs on CI.

Both modules load by path under pack-and-skill-qualified names: skills are
independent, several may ship a same-named script, and a bare import binds
whichever directory reached the path first.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PACK = Path(__file__).resolve().parents[3]

# Literal segments, one constant per module. Both skills are this pack's own, so
# neither path leaves `packs/core` — but `tools/lint-pack-test-boundary.py`
# resolves these statically, and a path assembled from a parameter reads to it
# as a reach above the pack even when every value is in-pack.
_RENDERER_PATH = (
    PACK / ".apm" / "skills" / "intake-intent" / "scripts" / "intent_renderer.py"
)
_SHAPE_PATH = (
    PACK / ".apm" / "skills" / "work-intake" / "scripts" / "intent_shape.py"
)


def _load(path: Path, qualified: str):
    spec = importlib.util.spec_from_file_location(qualified, path)
    assert spec is not None and spec.loader is not None
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = loaded
    spec.loader.exec_module(loaded)
    return loaded


renderer = _load(_RENDERER_PATH, "core_intake_intent_intent_renderer")
shape = _load(_SHAPE_PATH, "core_work_intake_intent_shape_t7")


def _intake(*, mode: str = "repo-origin", owners: list[str] | None = None):
    return SimpleNamespace(
        content={
            "outcomes": ["Fewer avoidable artifacts"],
            "assumptions": [],
            "named_gaps": [],
            "boundary": ["Core repository admission only"],
            "owner": ["maintainer"] if owners is None else owners,
            "unresolved_questions": ["None"],
            "projection": ["spec"],
        },
        constraints={},
        source=SimpleNamespace(
            mode=mode,
            locator="docs/source.md",
            revision="sha256-bytes-v1:fixture",
            tracker_profile=None,
        ),
    )


def _render(**overrides):
    kwargs = {
        "intake": _intake(),
        "title": "A minimum intent",
        "slug": "a-minimum-intent",
        "level": "feature",
    }
    kwargs.update(overrides)
    return renderer.render_minimal_intent(**kwargs)


def _faults(text: str) -> set[str]:
    return {v.field for v in shape.validate_live_intent(text)}


# ── AC-0018: the renderer's output satisfies the contract ─────────────────────


def test_ac0018_rendered_output_is_accepted_by_the_validator() -> None:
    assert shape.validate_live_intent(_render()) == []


def test_ac0018_rendered_output_carries_every_required_field() -> None:
    names = dict(shape.read_preamble(_render()))
    for required in shape.REQUIRED_FIELDS:
        assert required in names, required
    assert names["Slug"] == "a-minimum-intent"
    assert names["Level"] == "feature"
    assert names["Owner"] == "maintainer"
    assert names["Status"] == "Draft"


def test_ac0018_owner_left_the_body_for_the_preamble() -> None:
    """`## Owner` was a body section; the contract puts owner in the preamble."""
    rendered = _render()
    assert "## Owner" not in rendered
    assert "- **Owner:** maintainer" in rendered


def test_ac0018_several_owners_render_as_one_preamble_line() -> None:
    """A preamble field is one line, so a list cannot be rendered as bullets."""
    rendered = _render(intake=_intake(owners=["maintainer", "a-second-owner"]))
    names = dict(shape.read_preamble(rendered))
    assert names["Owner"] == "maintainer, a-second-owner"
    assert shape.validate_live_intent(rendered) == []


@pytest.mark.parametrize("level", ["feature", "capability", "product-strategy"])
def test_ac0018_each_altitude_renders_and_validates(level: str) -> None:
    assert shape.validate_live_intent(_render(level=level)) == []


def test_ac0018_a_tracker_origin_admission_still_validates() -> None:
    """This mode appends an authority fence, changing the rendered body."""
    rendered = _render(intake=_intake(mode="tracker-origin"))
    assert shape.validate_live_intent(rendered) == []


def test_ac0018_the_source_authority_line_is_not_a_retired_preamble_field() -> None:
    """`## Source` carries an unbolded `Authority:` provenance token.

    It shares its name with a retired preamble field, so the preamble bound is
    what keeps a conforming rendered intent from being refused.
    """
    rendered = _render()
    assert "Authority:" in rendered
    assert "Authority" not in _faults(rendered)


# ── ADR-0121 D3: an altitude is required at admission ─────────────────────────


def test_adr0121_an_admission_with_no_altitude_is_refused() -> None:
    """Refused, not defaulted: a guessed altitude is a declared fact the
    artifact did not carry, and a wrong placement on the tree is harder to
    notice than a missing one."""
    with pytest.raises(renderer.IntentAdmissionError) as raised:
        _render(level=None)
    assert "level" in str(raised.value)


@pytest.mark.parametrize("value", ["", "   "])
def test_adr0121_an_empty_altitude_is_refused(value: str) -> None:
    with pytest.raises(renderer.IntentAdmissionError):
        _render(level=value)


def test_adr0121_admit_repository_intent_refuses_without_an_altitude() -> None:
    """The refusal reaches the admission entry point, not only the renderer."""
    with pytest.raises(renderer.IntentAdmissionError):
        renderer.admit_repository_intent(
            intake=_intake(),
            title="A minimum intent",
            slug="a-minimum-intent",
        )


def test_adr0121_admit_repository_intent_renders_a_conforming_intent() -> None:
    admission = renderer.admit_repository_intent(
        intake=_intake(),
        title="A minimum intent",
        slug="a-minimum-intent",
        level="feature",
    )
    assert admission.target == "docs/product/intents/a-minimum-intent.md"
    assert shape.validate_live_intent(admission.content) == []


def test_the_rendered_intent_also_satisfies_the_corpus_scoped_rules() -> None:
    """The corpus-scoped surface, because passing the live-intent surface alone
    is not passing the contract.

    ``validate_live_intent`` accepts a stranded ``Superseded by:`` by design —
    that pairing rule is corpus-scoped — so a renderer seeding one would pass
    every check above and still emit an intent the corpus lint refuses.
    ``validate_corpus_scoped`` is the single entry point for all corpus-only
    checks, covering both supersession and state-coherence rules.
    """
    rendered = _render()
    slugs = shape.resolvable_slugs([rendered])
    assert shape.validate_corpus_scoped(rendered, slugs) == []


def test_a_rendered_intent_seeding_a_stranded_pointer_would_be_caught() -> None:
    """Supersession mutation: the control above can fail on the supersession half.

    Calling an always-clean surface on a conforming render proves nothing: it
    passes just as well with the rule deleted. This feeds the same surface the
    output it is meant to reject.
    """
    seeded = _render().replace(
        "- **Status:**", "- **Superseded by:** a-successor\n- **Status:**", 1
    )
    assert shape.validate_corpus_scoped(seeded, {"a-successor"}) != []


def test_a_rendered_intent_seeding_an_accepted_record_would_be_caught() -> None:
    """State-coherence mutation: the corpus-scoped control can fail on the
    state-coherence half.

    A rendered Draft intent carries no ``Accepted:`` record. Seeding one
    beside ``Status: Draft`` must be refused, so ``validate_corpus_scoped``
    discriminates rather than passing on a surface that is always clean for
    conforming renders.
    """
    rendered = _render()
    # Insert Accepted: just before the first heading — inside the preamble.
    seeded = rendered.replace(
        "\n## Outcome", "\n- **Accepted:** 2026-09-20 by eugenelim\n## Outcome", 1
    )
    slugs = shape.resolvable_slugs([seeded])
    assert shape.validate_corpus_scoped(seeded, slugs) != []


def test_the_slug_reaches_the_rendered_preamble_and_the_target() -> None:
    """One slug decides both, so a divergence between them cannot hide."""
    admission = renderer.admit_repository_intent(
        intake=_intake(),
        title="A minimum intent",
        slug="a-distinct-slug",
        level="feature",
    )
    assert "a-distinct-slug" in admission.target
    assert dict(shape.read_preamble(admission.content))["Slug"] == "a-distinct-slug"


# ── Raised by security review ─────────────────────────────────────────────────


@pytest.mark.parametrize("field", ["title", "slug"])
def test_an_untrusted_value_cannot_open_an_html_comment(field: str) -> None:
    """An unclosed `<!--` would comment out the rest of the rendered document.

    Whitespace collapse defuses a forged field or heading, but not this: a
    comment opener hides everything after it, including the `## Source` block
    that carries the artifact's provenance. The rendered document must keep
    that section visible.
    """
    payload = "an-example <!-- "
    rendered = _render(**{field: payload})

    assert "<!--" not in rendered
    assert "## Source" in rendered
    assert "- Mode: repo-origin" in rendered


def test_an_untrusted_value_cannot_close_an_html_comment() -> None:
    """The closing delimiter is neutralized too, so a value cannot escape a
    comment the template itself opened."""
    rendered = _render(title="an-example --> and then prose")
    assert "-->" not in rendered
    assert "## Source" in rendered


def test_a_neutralized_comment_keeps_its_text_visible() -> None:
    """Inert, not deleted: a reader still sees what the value said."""
    rendered = _render(slug="a-slug")
    assert "a-slug" in rendered
    rendered = _render(title="before <!-- after")
    assert "before" in rendered and "after" in rendered


def test_the_owner_list_is_neutralized_too() -> None:
    """Owner reaches the preamble through `_inline_list`, a path this change
    introduced, so it carries the same obligation as the fields beside it."""
    rendered = _render(intake=_intake(owners=["maintainer", "second <!-- "]))
    assert "<!--" not in rendered
    assert "## Source" in rendered
