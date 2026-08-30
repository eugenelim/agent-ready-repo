from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).with_name("check-output-readability.py")
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_output_readability", SCRIPT)
assert SPEC and SPEC.loader
readability = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(readability)


def test_standard_flesch_formulas_are_stable() -> None:
    score = readability.score_counts(words=100, sentences=5, syllables=150)
    assert score.reading_ease == 59.64
    assert score.grade_level == 9.91


@pytest.mark.parametrize(
    ("word", "expected"),
    (
        ("table", 2),
        ("simple", 2),
        ("file", 1),
        ("fixed", 1),
        ("needed", 2),
        ("passes", 2),
        ("tables", 2),
        ("makes", 1),
        ("cat", 1),
    ),
)
def test_syllable_estimate_handles_common_endings(word: str, expected: int) -> None:
    assert readability.estimate_syllables(word) == expected


def test_short_sample_is_insufficient_and_does_not_fail() -> None:
    result = readability.evaluate_corpus(["The cat sat on the mat."])
    assert result.status == "insufficient"
    assert result.reason == "below-word-floor"
    assert result.words == 6


def test_aggregate_plain_prose_passes_thresholds() -> None:
    text = (
        "We fixed the bug. The app now saves your work. You can close the page "
        "and come back later. Your work will still be here. All tests pass. "
        "No next step is needed. The change is safe to use now."
    )
    result = readability.evaluate_corpus([text])
    assert result.status == "pass"
    assert result.reading_ease >= 70
    assert result.grade_level <= 8


def test_aggregate_dense_prose_fails_thresholds() -> None:
    text = " ".join(
        [
            "Institutional interoperability necessitates comprehensive",
            "conceptualization and multidimensional synchronization.",
        ]
        * 6
    )
    result = readability.evaluate_corpus([text])
    assert result.status == "fail"
    assert result.reading_ease < 70
    assert result.grade_level > 8


def test_each_publishable_pack_has_a_passing_readability_fixture() -> None:
    results: dict[str, object] = {}
    pack_dirs = sorted(
        path.parent
        for path in (ROOT / "packs").glob("*/pack.toml")
        if not path.parent.name.startswith("_")
    )
    for pack in pack_dirs:
        cognitive_scenarios: list[tuple[Path, dict[str, object]]] = []
        for eval_path in pack.glob(".apm/skills/*/evals/evals.json"):
            payload = json.loads(eval_path.read_text(encoding="utf-8"))
            cognitive_scenarios.extend(
                (eval_path.parents[1], scenario)
                for scenario in payload.get("evals", [])
                if str(scenario.get("id", "")).startswith("cognitive-load-")
            )
        assert cognitive_scenarios, pack.name
        documents: list[str] = []
        for skill_root, scenario in cognitive_scenarios:
            for relative in scenario.get("files", []):
                if str(relative).endswith(".md"):
                    documents.append(
                        (skill_root / str(relative)).read_text(encoding="utf-8")
                    )
        assert documents, pack.name
        result = readability.evaluate_corpus(documents)
        assert result.status == "pass", (pack.name, result)
        results[pack.name] = result
    assert len(results) == 22


@pytest.mark.parametrize(
    "relative",
    (
        ".agents/rules/cognitive-load.md",
        "docs/AGENTS.md",
        "guides/_shared/reference/output-rendering.md",
    ),
)
def test_shipped_cognitive_load_guidance_meets_its_own_readability_gate(
    relative: str,
) -> None:
    document = (ROOT / relative).read_text(encoding="utf-8")
    result = readability.evaluate_corpus([document])
    assert result.status == "pass", (relative, result)
    assert result.reading_ease >= 70, (relative, result)
    assert result.grade_level <= 8, (relative, result)


def test_markdown_extractor_removes_protected_technical_text() -> None:
    markdown = """
# A clear result

The change is ready. You can use it now. The next save will keep your work.

`private_identifier` and src/example/file.py and https://example.com/a

```python
raise ComplexInternalFailure("private payload")
```

| Field | Value |
| --- | --- |
| account_id | hidden |

> ERROR: private failure text

[Internal citation](https://example.com/source)

<!-- readability:exclude:start -->
Mandatory security indemnification terminology.
<!-- readability:exclude:end -->
"""
    eligible = readability.extract_eligible_prose(markdown)
    assert "change is ready" in eligible
    for protected in (
        "private_identifier",
        "src/example/file.py",
        "example.com",
        "ComplexInternalFailure",
        "account_id",
        "private failure",
        "Internal citation",
        "indemnification",
    ):
        assert protected not in eligible


def test_indented_markdown_code_does_not_change_scores() -> None:
    prose = (
        "The fix is ready. The app now saves your work. You can close the page. "
        "Your work will stay safe. All checks pass. No next step is needed."
    )
    with_code = prose + "\n\n    DenseInstitutionalCode performs complex work.\n\tAnotherCodeCall runs."

    expected = readability.evaluate_corpus([prose])
    actual = readability.evaluate_corpus([with_code])

    assert actual.words == expected.words
    assert actual.sentences == expected.sentences
    assert actual.syllables == expected.syllables
    assert actual.reading_ease == expected.reading_ease
    assert actual.grade_level == expected.grade_level


def test_routine_tool_sequence_has_no_optional_chatter() -> None:
    transcript = [
        {"kind": "user"},
        {"kind": "tool_call"},
        {"kind": "tool_result"},
        {"kind": "tool_call"},
        {"kind": "tool_result"},
        {"kind": "assistant", "phase": "final"},
    ]
    result = readability.evaluate_quiet_transcript(transcript)
    assert result.status == "pass"
    assert result.optional_messages == 0


@pytest.mark.parametrize(
    "reason",
    (
        "safety",
        "blocker",
        "user-decision",
        "material-scope-change",
        "long-wait",
        "host-requirement",
    ),
)
def test_required_interruptions_preserve_quiet_contract(reason: str) -> None:
    transcript = [
        {"kind": "tool_call"},
        {"kind": "assistant", "phase": "commentary", "reason": reason},
        {"kind": "tool_call"},
    ]
    result = readability.evaluate_quiet_transcript(transcript)
    assert result.status == "pass"
    assert result.required_messages == 1


def test_optional_message_between_tool_calls_fails() -> None:
    transcript = [
        {"kind": "tool_call"},
        {"kind": "assistant", "phase": "commentary", "reason": "progress"},
        {"kind": "tool_call"},
    ]
    result = readability.evaluate_quiet_transcript(transcript)
    assert result.status == "fail"
    assert result.optional_messages == 1


def test_failed_quiet_transcript_dominates_insufficient_batch() -> None:
    failed = readability.evaluate_quiet_transcript(
        [
            {"kind": "tool_call"},
            {"kind": "assistant", "reason": "progress"},
            {"kind": "tool_call"},
        ]
    )
    insufficient = readability.evaluate_quiet_transcript([{"kind": "tool_call"}])

    result = readability.aggregate_quiet_results([failed, insufficient])

    assert result.status == "fail"
    assert result.optional_messages == 1
    assert result.transcripts == 2


def test_ordinary_blockquote_is_scored_but_quoted_error_is_not() -> None:
    ordinary = "> This plain note is part of the answer. It should count in the score."
    quoted_error = "> ERROR: DenseInstitutionalFailure must stay exact."

    eligible = readability.extract_eligible_prose(ordinary + "\n" + quoted_error)

    assert "plain note is part of the answer" in eligible
    assert "DenseInstitutionalFailure" not in eligible


def test_json_output_is_aggregate_and_content_free(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "private-name.md"
    source.write_text(
        "We fixed the bug. The app now saves your work. " * 8,
        encoding="utf-8",
    )
    assert readability.main(["--json", str(source)]) == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["files"] == 1
    assert payload["status"] == "pass"
    assert "private-name" not in output
    assert "fixed the bug" not in output


@pytest.mark.parametrize(
    "case",
    ("symlink", "hardlink", "directory", "oversized", "fifo"),
)
def test_text_inputs_refuse_unsafe_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source.md"
    if case == "symlink":
        target = tmp_path / "target.md"
        target.write_text("plain prose\n", encoding="utf-8")
        try:
            source.symlink_to(target)
        except OSError:
            pytest.skip("symlinks unavailable")
    elif case == "hardlink":
        source.write_text("plain prose\n", encoding="utf-8")
        try:
            os.link(source, tmp_path / "second.md")
        except OSError:
            pytest.skip("hard links unavailable")
    elif case == "directory":
        source.mkdir()
    elif case == "oversized":
        source.write_bytes(b"x" * (readability.MAX_INPUT_BYTES + 1))
    else:
        if not hasattr(os, "mkfifo"):
            pytest.skip("FIFOs unavailable")
        os.mkfifo(source)

    with pytest.raises(ValueError, match="input-unreadable"):
        readability._read_text_inputs(["source.md"])


def test_dot_segment_input_is_refused_before_the_reader_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    class UnsafeContentError(ValueError):
        pass

    def unexpected_read(*_args: object, **_kwargs: object) -> bytes:
        raise AssertionError("dot-segment path reached the file reader")

    fake = SimpleNamespace(
        UnsafeContentError=UnsafeContentError,
        read_confined_regular_file=unexpected_read,
    )
    monkeypatch.setattr(readability, "_file_safety", lambda: fake)

    with pytest.raises(ValueError, match="input-unreadable"):
        readability._read_text_inputs(["nested/../source.md"])


def test_text_inputs_delegate_bounds_to_the_blessed_reader(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "source.md"
    source.write_text("Plain words make this easy to read.\n", encoding="utf-8")
    calls: list[tuple[Path, Path, int | None]] = []

    class UnsafeContentError(ValueError):
        pass

    def read(root: Path, path: Path, *, max_bytes: int | None = None) -> bytes:
        calls.append((root, path, max_bytes))
        return source.read_bytes()

    fake = SimpleNamespace(
        UnsafeContentError=UnsafeContentError,
        read_confined_regular_file=read,
    )
    monkeypatch.setattr(readability, "_file_safety", lambda: fake)

    assert readability._read_text_inputs(["source.md"])
    assert calls == [(tmp_path, source, readability.MAX_INPUT_BYTES)]
