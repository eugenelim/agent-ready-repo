"""Construction tests for splitting independent bundles and routing plain guidance edits.

Each test reads one bounded section and asserts the phrases its rule depends
on, so a rule removed or moved out of the procedure an agent follows turns a
test red. Sections are whitespace-flattened, so a re-wrap is not a failure.
"""

import json
from pathlib import Path

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
_WORK_LOOP = _SKILL_DIR / "SKILL.md"
_LIGHT_MODE = _SKILL_DIR / "references" / "light-mode.md"
_EVALS = _SKILL_DIR / "evals" / "evals.json"


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


def _split_section() -> str:
    """The bundle-split section, flattened."""
    raw = _LIGHT_MODE.read_text(encoding="utf-8")
    return _section(raw, "## Splitting a bundle", "## Editing existing agent guidance")


def _guidance_section() -> str:
    """The guidance-edit section, flattened."""
    raw = _LIGHT_MODE.read_text(encoding="utf-8")
    return _section(raw, "## Editing existing agent guidance", "## Loop deltas")


def _table_rows(raw: str, start: str, end: str) -> list[str]:
    """Body rows of the table between two markers, split as the intake suite splits them."""
    window = raw[raw.index(start) : raw.index(end)]
    return [
        line for line in window.splitlines() if line.startswith("| ") and "---" not in line
    ][1:]


def test_t2_split_test_has_three_parts_and_checks_the_diff() -> None:
    _assert_contains(
        _split_section(),
        (
            "No dependency edge",
            "Depends on:",
            "No shared write set",
            "Touches:",
            "counts as a write to its source path",
            "The diff agrees",
            "touches no file in another unit's set",
            "Part 3, the diff check,",
            "before the first write",
            "never by itself shows independence",
        ),
    )


def test_t2_each_unit_faces_every_trigger_and_runs_serially() -> None:
    _assert_contains(
        _split_section(),
        (
            "every eligibility row on its own",
            "its own branch and pull request",
            "a split is not parallel execution",
        ),
    )


def test_t2_bundle_still_passes_the_session_and_queue_rows() -> None:
    _assert_contains(
        _split_section(),
        (
            "Expected to complete in the current session",
            "Expected multi-session work",
            "Queueing for later",
            "goes to full mode whole",
        ),
    )


def test_t2_no_light_unit_merges_until_every_unit_passes() -> None:
    _assert_contains(
        _split_section(),
        (
            "No light unit merges until every unit still in the bundle has a finished diff "
            "that passes the diff check.",
        ),
    )


def test_t2_a_unit_that_fires_a_trigger_leaves_with_its_write_set() -> None:
    _assert_contains(
        _split_section(),
        (
            "leaves the bundle for full mode",
            "its spec and plan record that set",
            "run the diff check against that set",
            "without waiting for the full-mode unit",
        ),
    )


def test_t2_fallback_keeps_the_bundle_whole() -> None:
    _assert_contains(
        _split_section(),
        ("stays whole and goes to full mode", "stops the whole bundle", "kept as observed work"),
    )


def test_t2_guidance_edit_section_and_durability_row() -> None:
    _assert_contains(
        _guidance_section(),
        (
            "fires no trigger by being guidance",
            "still faces every trigger on its other effects",
            "does not count as a durable product contract",
            "content-pin test",
            "reads only the edited section",
        ),
    )
    raw = _LIGHT_MODE.read_text(encoding="utf-8")
    eligibility = _table_rows(raw, "| Required condition", "Durability is a disjunction")
    durability = _table_rows(raw, "| Durability trigger", "Direct execution being unavailable")
    assert (len(eligibility), len(durability)) == (8, 10)
    rows = [" ".join(r.split()) for r in durability]
    matching = [r for r in rows if r.startswith("| A public or durable product behavior contract")]
    assert len(matching) == 1, matching
    _assert_contains(
        matching[0],
        ("**tool surface**", "**authority or gate**", "**security boundary**", "**published schema**"),
    )


def _evals() -> dict[str, dict]:
    data = json.loads(_EVALS.read_text(encoding="utf-8"))
    return {case["id"]: case for case in data["evals"]}


def test_t3_nine_new_evals_carry_their_verdict_phrases() -> None:
    verdicts = {
        "bundle-split-independent-tasks": "one unit per task",
        "bundle-unsplittable-shared-file": "full mode",
        "bundle-late-unit-strays": "whole bundle",
        "guidance-edit-plain-runs-light": "light mode",
        "guidance-new-file-fires-structural": "structural trigger",
        "guidance-edit-tool-surface": "full mode",
        "guidance-edit-authority-or-gate": "full mode",
        "guidance-edit-security-boundary": "full mode",
        "guidance-edit-published-schema": "full mode",
    }
    cases = _evals()
    for case_id, phrase in verdicts.items():
        assert case_id in cases, case_id
        case = cases[case_id]
        for field in ("id", "prompt", "expected_output", "assertions"):
            assert field in case, (case_id, field)
        assert isinstance(case["assertions"], list) and case["assertions"], case_id
        assert phrase in case["expected_output"], (case_id, phrase)
    assert "content-pin" in cases["guidance-edit-plain-runs-light"]["expected_output"]


def test_t3_modify_not_touch_eval_states_the_narrowed_rule() -> None:
    case = _evals()["risk-trigger-modify-not-touch"]
    phrases = ("existing agent guidance", "only when it changes", "policy", "interface document")
    _assert_contains(case["expected_output"], phrases)
    assert any(all(p in entry for p in phrases) for entry in case["assertions"])
    whole = json.dumps(case, ensure_ascii=False)
    for banned in (
        "so editing it fires the trigger",
        "agent guidance, policy, an interface document -- fires the trigger",
    ):
        assert banned not in whole, banned
