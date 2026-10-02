"""AC-0012 for the experience-design visual-target field.

Lives in tests/roster/ and not in the pack contract suite: AC-0012 is a claim
about guides/experience-design/how-to/establish-design-intent.md, and
tools/lint-pack-test-boundary.py forbids a pack test from reading above its own
pack. The spec's Testing Strategy records why the original home could not
satisfy both. tests/AGENTS.md names tests/roster/ as the repository-level home.

Run mode: build-check.yml triggers on pull_request and its carve-out step runs
`python -m pytest tests/ -q`, so the PR gate runs this.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/roster/ -> repo root
GUIDE = (
    REPO_ROOT
    / "guides"
    / "experience-design"
    / "how-to"
    / "establish-design-intent.md"
)
TICKS = "`" * 3  # written this way so the literal survives a fenced code block
FENCE = TICKS + "markdown"


def _template_fence(text: str) -> str:
    """The one markdown fence reproducing the creative-direction template.

    Selected by a property, not by ordinal: this guide carries three such
    fences and the first is a design-principles block.
    """
    bodies = [part.split(TICKS, 1)[0] for part in text.split(FENCE)[1:]]
    matching = [b for b in bodies if "type: creative-direction" in b]
    assert len(matching) == 1, "AC-0012: exactly one creative-direction fence"
    return matching[0]


KEY_LINE = 'visual_target: "<none | unconfirmed | confirmed>"'
RECORD_LINE = (
    "**Confirmation record:** <YYYY-MM-DD> — "
    "<where the confirmation was recorded>"
)


# STUB: AC-0012  (spec: visual-target-field)
def test_visual_target_guide_excerpt() -> None:
    """visual-target-field AC-0012."""
    excerpt = _template_fence(GUIDE.read_text(encoding="utf-8"))
    lines = [line.rstrip() for line in excerpt.split("\n")]
    for pinned in (KEY_LINE, RECORD_LINE):
        assert lines.count(pinned) == 1, (
            f"AC-0012: {pinned!r} must appear exactly once in the template "
            "fence. Containment over the bare words does not decide this: the "
            "fence carries `visual_target` four times and "
            "`**Confirmation record:**` twice, because the section comment "
            "discusses both, so a word check passes on an excerpt that "
            "reproduces the comment and omits the key and the record line."
        )
