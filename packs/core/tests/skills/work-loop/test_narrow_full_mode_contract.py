"""Construction tests for splitting independent bundles and routing plain guidance edits.

Each test reads one bounded section and asserts the phrases its rule depends
on, so a rule removed or moved out of the procedure an agent follows turns a
test red. Sections are whitespace-flattened, so a re-wrap is not a failure.
"""

from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
_WORK_LOOP = _SKILL_DIR / "SKILL.md"
_LIGHT_MODE = _SKILL_DIR / "references" / "light-mode.md"


def _section(text: str, start: str, end: str) -> str:
    """Return the text between two markers, whitespace-flattened; fail if either is missing."""
    assert start in text, f"missing start marker: {start!r}"
    head = text.index(start) + len(start)
    assert end in text[head:], f"missing end marker: {end!r}"
    return " ".join(text[head : text.index(end, head)].split())


def _block() -> str:
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    return _section(raw, "<!-- risk-triggers:start", "risk-triggers:end -->")


def _assert_contains(section: str, phrases: tuple[str, ...]) -> None:
    missing = [phrase for phrase in phrases if phrase not in section]
    assert not missing, missing


def test_t1_multi_feature_trigger_splits_an_independent_bundle() -> None:
    bullet = _section(_block(), "- **Multi-feature or dependent tasks**", "No trigger fires")
    _assert_contains(
        bullet,
        (
            "decomposes a multi-feature brief",
            "cannot show independent",
            "references/light-mode.md",
            "splits into one unit per task",
            "faces every other trigger here on its own",
            "A bundle whose independence cannot be shown fires this trigger.",
        ),
    )


def test_t1_guidance_sentence_names_the_four_exclusions_and_fails_closed() -> None:
    sentence = _section(_block(), "Merely touching unchanged existing I/O", "- **Compliance")
    _assert_contains(
        sentence,
        (
            "an edit to an existing agent-guidance file",
            "only when the edit changes",
            "**tool surface**",
            "which tools, commands, hooks, or scripts an agent may run, or how they are invoked",
            "**authority or gate**",
            "who or what may approve, decide, merge, or skip a gate",
            "what a gate requires",
            "what counts as clean",
            "what evidence the finish checklist needs",
            "what a finding may block",
            "which text an agent treats as instruction",
            "**security boundary**",
            "untrusted input, secrets, confinement, or LLM authority",
            "**published schema**",
            "a format other tools or adopters parse",
            "Compliance and policy prose keeps its trigger",
            "still fires the structural trigger",
            "An edit you cannot place outside the four is inside them.",
            "Where you cannot tell whether the change reached the thing, it did.",
        ),
    )
    assert "agent guidance, policy, an interface document — is the thing itself" not in sentence
