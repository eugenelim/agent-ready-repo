"""Construction tests for finding-response scorer parsing and correspondence."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from tools.score_finding_responses import (
    ScoringInputError,
    Transcript,
    _count_acceptance_criteria,
    parse_case,
    parse_transcript,
    render_score,
    score_case_and_transcript,
    validate_arm_control_pair,
    validate_case_and_transcript,
    validate_transcript_rendering,
)


_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_CASES_DIRECTORY = _REPOSITORY_ROOT / "docs/specs/finding-response-scoring/cases"
_TRANSCRIPTS_DIRECTORY = _REPOSITORY_ROOT / "docs/specs/finding-response-scoring/transcripts"
_FROZEN_CASE_NAMES = (
    "judgment-dominated.md",
    "large-mixed.md",
    "small-determined.md",
)


def _case_text(findings: str = "- F1 — first finding\n- F2 — second finding\n") -> str:
    """Return a syntactically valid case fixture."""
    return (
        "# Case: fixture\n"
        "Source: docs/specs/example/notes/adjudication.md\n"
        "Baseline: docs/specs/example/spec.md\n\n"
        f"{findings}"
    )


def _transcript_text(responses: str) -> str:
    """Return a syntactically valid transcript fixture with ``responses``."""
    return (
        "# Transcript: fixture / fix-grammar\n"
        "Arm: fix-grammar\n"
        "Grammar: Fix:\n"
        "Rendering: docs/specs/example/renderings/fix-grammar.md\n"
        "Rendering-sha256: " + "b" * 64 + "\n"
        "Baseline: docs/specs/example/spec.md\n"
        "Answered: docs/specs/example/answered.md\n"
        "Model: example-model\n"
        "Settings: temperature=0\n"
        "Instructions: " + "a" * 64 + "\n\n" + responses
    )


def _write(path: Path, contents: str) -> Path:
    """Write a UTF-8 fixture and return its path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")
    return path


def _write_rendering(repository_root: Path, relative_path: str, contents: str) -> str:
    """Write one repository-local rendering and return its SHA-256 digest."""
    rendering_path = repository_root / relative_path
    rendering_path.parent.mkdir(parents=True, exist_ok=True)
    _write(rendering_path, contents)
    return hashlib.sha256(contents.encode("utf-8")).hexdigest()


def _artifact_text(criteria_count: int) -> str:
    """Return an artifact with exactly ``criteria_count`` acceptance criteria."""
    criteria = "".join(
        f"- [ ] **AC-{number:04d}.** criterion {number}\n"
        for number in range(1, criteria_count + 1)
    )
    return f"# Artifact\n\n- [ ] ignored checkbox\n\n## Acceptance Criteria\n\n{criteria}\n## Follow-ons\n\n- [x] ignored checkbox\n"


def _metrics_transcript_text(baseline: Path, answered: Path, responses: str) -> str:
    """Return a transcript fixture that names its two metric artifacts."""
    return (
        "# Transcript: fixture / fix-grammar\n"
        "Arm: fix-grammar\n"
        "Grammar: Fix:\n"
        "Rendering: docs/specs/example/renderings/fix-grammar.md\n"
        "Rendering-sha256: " + "b" * 64 + "\n"
        f"Baseline: {baseline}\n"
        f"Answered: {answered}\n"
        "Model: example-model\n"
        "Settings: temperature=0\n"
        "Instructions: " + "a" * 64 + "\n\n" + responses
    )


def test_valid_case_and_transcript_correspond_exactly(tmp_path: Path) -> None:
    """A complete, unique response set with known dispositions is admitted."""
    case = parse_case(_write(tmp_path / "case.md", _case_text()))
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _transcript_text(
                "- F1 — repair — corrected the wording\n"
                "- F2 — route-to-owner — needs an owner decision\n"
            ),
        )
    )

    validate_case_and_transcript(case, transcript)


def test_missing_identifier_is_named_when_every_other_response_is_correct(
    tmp_path: Path,
) -> None:
    """A missing case identifier is reported without another violation."""
    case = parse_case(_write(tmp_path / "case.md", _case_text()))
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _transcript_text("- F1 — repair — complete response\n"),
        )
    )

    with pytest.raises(ScoringInputError, match="missing F2"):
        validate_case_and_transcript(case, transcript)


def test_extra_identifier_is_named_when_every_other_response_is_correct(
    tmp_path: Path,
) -> None:
    """An identifier absent from the case is reported without another violation."""
    case = parse_case(_write(tmp_path / "case.md", _case_text()))
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _transcript_text(
                "- F1 — repair — first response\n"
                "- F2 — route-to-owner — second response\n"
                "- F3 — repair — unexpected response\n"
            ),
        )
    )

    with pytest.raises(ScoringInputError, match="extra F3"):
        validate_case_and_transcript(case, transcript)


def test_repeated_identifier_is_named_when_every_other_response_is_correct(
    tmp_path: Path,
) -> None:
    """A duplicate response identifier is reported without another violation."""
    case = parse_case(_write(tmp_path / "case.md", _case_text()))
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _transcript_text(
                "- F1 — repair — first response\n"
                "- F1 — repair — duplicate response\n"
                "- F2 — route-to-owner — second response\n"
            ),
        )
    )

    with pytest.raises(ScoringInputError, match="repeated F1"):
        validate_case_and_transcript(case, transcript)


def test_invalid_disposition_is_named_when_correspondence_is_correct(
    tmp_path: Path,
) -> None:
    """An out-of-vocabulary disposition is reported without a set violation."""
    case = parse_case(_write(tmp_path / "case.md", _case_text()))
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _transcript_text(
                "- F1 — repair — first response\n"
                "- F2 — invent-a-response — invalid disposition\n"
            ),
        )
    )

    with pytest.raises(ScoringInputError, match="finding F2 has invalid disposition invent-a-response"):
        validate_case_and_transcript(case, transcript)


def test_correspondence_error_names_missing_extra_and_repeated_identifiers(
    tmp_path: Path,
) -> None:
    """AC-0001 reports every multiplicity and set-correspondence offender."""
    case = parse_case(_write(tmp_path / "case.md", _case_text()))
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _transcript_text(
                "- F1 — repair — first response\n"
                "- F1 — repair — repeated response\n"
                "- F3 — repair — unknown response\n"
            ),
        )
    )

    with pytest.raises(ScoringInputError) as raised:
        validate_case_and_transcript(case, transcript)

    message = str(raised.value)
    assert "missing F2" in message
    assert "extra F3" in message
    assert "repeated F1" in message


def test_aggregate_error_names_all_correspondence_and_disposition_offenders(
    tmp_path: Path,
) -> None:
    """AC-0001 and AC-0002 errors are aggregated across one bad fixture."""
    case = parse_case(_write(tmp_path / "case.md", _case_text()))
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _transcript_text(
                "- F1 — repair — first response\n"
                "- F1 — repair — repeated response\n"
                "- F3 — invent-a-response — unknown response\n"
            ),
        )
    )

    with pytest.raises(ScoringInputError) as raised:
        validate_case_and_transcript(case, transcript)

    message = str(raised.value)
    for expected in ("missing F2", "extra F3", "repeated F1", "F3", "invent-a-response"):
        assert expected in message


def test_score_reports_hand_calculated_metrics_from_both_artifacts(tmp_path: Path) -> None:
    """AC-0003 reports hand-calculated dispositions and both criteria counts."""
    baseline = _write(tmp_path / "baseline.md", _artifact_text(2))
    answered = _write(tmp_path / "answered.md", _artifact_text(4))
    case = parse_case(
        _write(
            tmp_path / "case.md",
            _case_text(
                "- F1 — first finding\n"
                "- F2 — second finding\n"
                "- F3 — third finding\n"
            ),
        )
    )
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _metrics_transcript_text(
                baseline,
                answered,
                "- F1 — repair — first response\n"
                "- F2 — route-to-owner — owner decision\n"
                "- F3 — cut-the-item — remove it\n",
            ),
        )
    )

    score = score_case_and_transcript(case, transcript)

    assert score.repair_count == 1
    assert score.finding_count == 3
    assert score.non_repair_counts == {
        "narrow-the-claim": 0,
        "cut-the-item": 1,
        "dismiss-and-re-present": 0,
        "repair-the-generator": 0,
        "route-to-owner": 1,
        "bound-out-of-scope": 0,
        "accept-as-proportionate": 0,
    }
    assert score.baseline_criteria_count == 2
    assert score.answered_criteria_count == 4
    assert score.criteria_change == 2


@pytest.mark.parametrize(
    ("baseline_count", "answered_count"),
    ((1, 1), (1, 3), (4, 1)),
)
def test_score_reads_baseline_and_answered_criteria_independently(
    tmp_path: Path,
    baseline_count: int,
    answered_count: int,
) -> None:
    """AC-0003 counts either named artifact even when only it changes."""
    baseline = _write(tmp_path / "baseline.md", _artifact_text(baseline_count))
    answered = _write(tmp_path / "answered.md", _artifact_text(answered_count))
    case = parse_case(_write(tmp_path / "case.md", _case_text("- F1 — first finding\n")))
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _metrics_transcript_text(
                baseline,
                answered,
                "- F1 — repair — corrected it\n",
            ),
        )
    )

    score = score_case_and_transcript(case, transcript)

    assert score.baseline_criteria_count == baseline_count
    assert score.answered_criteria_count == answered_count
    assert score.criteria_change == answered_count - baseline_count


def test_render_score_emits_exact_canonical_report_bytes(tmp_path: Path) -> None:
    """AC-0004 fixes disposition and numeric-finding report order as bytes."""
    baseline = _write(tmp_path / "baseline.md", _artifact_text(1))
    answered = _write(tmp_path / "answered.md", _artifact_text(2))
    case = parse_case(
        _write(
            tmp_path / "case.md",
            _case_text("- F10 — tenth finding\n- F2 — second finding\n- F1 — first finding\n"),
        )
    )
    transcript = parse_transcript(
        _write(
            tmp_path / "transcript.md",
            _metrics_transcript_text(
                baseline,
                answered,
                "- F10 — route-to-owner — owner decision\n"
                "- F2 — cut-the-item — remove it\n"
                "- F1 — repair — correct it\n",
            ),
        )
    )

    report = render_score(score_case_and_transcript(case, transcript))

    assert report == (
        "Arm: fix-grammar\n"
        "Repair share: 1/3\n"
        "Dispositions:\n"
        "- repair: 1\n"
        "- narrow-the-claim: 0\n"
        "- cut-the-item: 1\n"
        "- dismiss-and-re-present: 0\n"
        "- repair-the-generator: 0\n"
        "- route-to-owner: 1\n"
        "- bound-out-of-scope: 0\n"
        "- accept-as-proportionate: 0\n"
        "Acceptance criteria: baseline 1; answered 2; change +1\n"
        "Findings:\n"
        "- F1: repair\n"
        "- F2: cut-the-item\n"
        "- F10: route-to-owner\n"
    )


@pytest.mark.parametrize(
    ("relative_path", "expected_count"),
    (
        ("cases/judgment-dominated.baseline.md", 24),
        ("cases/large-mixed.baseline.md", 15),
        ("cases/small-determined.baseline.md", 36),
        ("spec.md", 6),
    ),
)
def test_acceptance_criteria_count_uses_the_named_section(
    relative_path: str,
    expected_count: int,
) -> None:
    """AC-0003 counts real checkbox criteria only in their named section."""
    artifact = _REPOSITORY_ROOT / "docs/specs/finding-response-scoring" / relative_path

    assert _count_acceptance_criteria(str(artifact)) == expected_count


def test_acceptance_criteria_count_excludes_checkboxes_outside_the_named_section(
    tmp_path: Path,
) -> None:
    """AC-0003 ignores checkbox lines that do not belong to acceptance criteria."""
    artifact = _write(
        tmp_path / "artifact.md",
        "# Artifact\n\n- [ ] outside before\n\n## Acceptance Criteria\n\n"
        "- [x] inside\n\n## Follow-ons\n\n- [ ] outside after\n",
    )

    assert _count_acceptance_criteria(str(artifact)) == 1


def _arm_transcript_text(
    arm: str,
    *,
    grammar: str | None = None,
    rendering: str | None = None,
    rendering_sha256: str | None = None,
    baseline: str = "docs/specs/example/spec.md",
    model: str = "example-model",
    settings: str = "temperature=0",
    instructions: str = "a" * 64,
) -> str:
    """Return a valid one-response transcript for an arm-control comparison."""
    if grammar is None:
        grammar = "Fix:" if arm == "fix-grammar" else "Required outcome and constraints:"
    if rendering is None:
        rendering = f"docs/specs/example/renderings/{arm}.md"
    if rendering_sha256 is None:
        rendering_sha256 = "b" * 64 if arm == "fix-grammar" else "c" * 64
    return (
        f"# Transcript: fixture / {arm}\n"
        f"Arm: {arm}\n"
        f"Grammar: {grammar}\n"
        f"Rendering: {rendering}\n"
        f"Rendering-sha256: {rendering_sha256}\n"
        f"Baseline: {baseline}\n"
        "Answered: docs/specs/example/answered.md\n"
        f"Model: {model}\n"
        f"Settings: {settings}\n"
        f"Instructions: {instructions}\n\n"
        "- F1 — repair — corrected it\n"
    )


def _arm_pair(tmp_path: Path, **second_changes: str) -> tuple[Transcript, Transcript]:
    """Parse a valid arm pair after applying one optional second-header change."""
    first = parse_transcript(
        _write(tmp_path / "first.md", _arm_transcript_text("fix-grammar"))
    )
    second = parse_transcript(
        _write(
            tmp_path / "second.md",
            _arm_transcript_text("neutral-grammar", **second_changes),
        )
    )
    return first, second


def _corpus_transcript_text(
    repository_root: Path,
    arm: str,
    case_name: str = "fixture",
    finding_id: str = "F1",
) -> str:
    """Return a valid transcript whose rendering exists beneath ``repository_root``."""
    rendering = f"renderings/{case_name}.{arm}.md"
    grammar = "Fix:" if arm == "fix-grammar" else "Required outcome and constraints:"
    digest = _write_rendering(
        repository_root, rendering, f"- {finding_id} — finding. {grammar} response\n"
    )
    return _arm_transcript_text(arm, rendering=rendering, rendering_sha256=digest).replace(
        "- F1 — repair — corrected it", f"- {finding_id} — repair — corrected it"
    )


def test_arm_pair_with_matched_controls_and_distinct_arms_is_admitted(tmp_path: Path) -> None:
    """AC-0006 accepts a pair whose recorded controls all agree."""
    first, second = _arm_pair(tmp_path)

    validate_arm_control_pair(first, second)


def test_arm_pair_rejects_matching_grammar(tmp_path: Path) -> None:
    """AC-0006 requires the two recorded terminal-clause labels to differ."""
    first, second = _arm_pair(tmp_path, grammar="Fix:")

    with pytest.raises(ScoringInputError, match="Grammar"):
        validate_arm_control_pair(first, second)


def test_transcript_rejects_an_invalid_rendering_sha256(tmp_path: Path) -> None:
    """Transcript grammar requires a lowercase 64-character rendering digest."""
    path = _write(
        tmp_path / "transcript.md",
        _arm_transcript_text("fix-grammar", rendering_sha256="A" * 64),
    )

    with pytest.raises(ScoringInputError, match="invalid Rendering-sha256"):
        parse_transcript(path)


def test_rendering_digest_mismatch_names_the_transcript_path_and_both_digests(
    tmp_path: Path,
) -> None:
    """Corpus validation rejects a digest that differs from the rendering bytes."""
    rendering = "renderings/fixture.fix-grammar.md"
    computed_digest = _write_rendering(tmp_path, rendering, "recorded rendering\n")
    expected_digest = "a" * 64
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text(
            "fix-grammar", rendering=rendering, rendering_sha256=expected_digest
        ),
    )

    with pytest.raises(ScoringInputError) as raised:
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )

    message = str(raised.value)
    assert str(transcript_path) in message
    assert rendering in message
    assert expected_digest in message
    assert computed_digest in message


def test_rendering_path_must_be_canonical_for_its_transcript_case_and_arm(
    tmp_path: Path,
) -> None:
    """A correct digest for the other arm cannot bind that arm's rendering."""
    other_rendering = "renderings/fixture.neutral-grammar.md"
    other_digest = _write_rendering(
        tmp_path,
        other_rendering,
        "- F1 — finding. Fix: response\n",
    )
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text(
            "fix-grammar", rendering=other_rendering, rendering_sha256=other_digest
        ),
    )

    with pytest.raises(ScoringInputError) as raised:
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )

    message = str(raised.value)
    assert "renderings/fixture.fix-grammar.md" in message
    assert other_rendering in message


def test_rendering_finding_lines_must_carry_the_declared_grammar(tmp_path: Path) -> None:
    """A correct canonical path and digest still reject the wrong terminal-clause label."""
    rendering = "renderings/fixture.fix-grammar.md"
    digest = _write_rendering(
        tmp_path,
        rendering,
        "- F1 — finding. Required outcome and constraints: response\n",
    )
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text("fix-grammar", rendering=rendering, rendering_sha256=digest),
    )

    with pytest.raises(ScoringInputError) as raised:
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )

    assert "line 1" in str(raised.value)
    assert "Required outcome and constraints" in str(raised.value)


def test_empty_rendering_is_rejected_even_with_its_own_matching_digest(tmp_path: Path) -> None:
    """A bound rendering must contain at least one complete finding record."""
    rendering = "renderings/fixture.fix-grammar.md"
    digest = _write_rendering(tmp_path, rendering, "")
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text("fix-grammar", rendering=rendering, rendering_sha256=digest),
    )

    with pytest.raises(ScoringInputError, match="has no finding records"):
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )


def test_malformed_rendering_finding_record_is_rejected_before_correspondence(
    tmp_path: Path,
) -> None:
    """A finding-record candidate cannot evade validation by failing to parse."""
    rendering = "renderings/fixture.fix-grammar.md"
    digest = _write_rendering(tmp_path, rendering, "- F1 malformed finding record\n")
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text("fix-grammar", rendering=rendering, rendering_sha256=digest),
    )

    with pytest.raises(ScoringInputError, match="line 1 has malformed finding record"):
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )


def test_rendering_missing_a_transcript_finding_is_rejected_before_grammar(
    tmp_path: Path,
) -> None:
    """A complete record set must correspond exactly to transcript responses."""
    rendering = "renderings/fixture.fix-grammar.md"
    digest = _write_rendering(tmp_path, rendering, "- F1 — finding. Fix: response\n")
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text("fix-grammar", rendering=rendering, rendering_sha256=digest).replace(
            "- F1 — repair — corrected it\n",
            "- F1 — repair — corrected it\n- F2 — repair — second response\n",
        ),
    )

    with pytest.raises(ScoringInputError, match="missing F2"):
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )


def test_rendering_path_must_not_be_a_symlink_even_when_its_digest_matches(
    tmp_path: Path,
) -> None:
    """A canonical symlink is rejected before its valid target can be read."""
    rendering = "renderings/fixture.fix-grammar.md"
    target_contents = "- F1 — finding. Fix: response\n"
    digest = _write_rendering(tmp_path, "renderings/target.md", target_contents)
    rendering_path = tmp_path / rendering
    rendering_path.symlink_to("target.md")
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text("fix-grammar", rendering=rendering, rendering_sha256=digest),
    )

    with pytest.raises(ScoringInputError, match="must not be a symlink"):
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )


def test_missing_rendering_path_is_rejected_by_corpus_validation(tmp_path: Path) -> None:
    """Corpus validation rejects an otherwise valid transcript with no rendering file."""
    rendering = "renderings/fixture.fix-grammar.md"
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text("fix-grammar", rendering=rendering),
    )

    with pytest.raises(ScoringInputError, match="not an existing regular file inside repository"):
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )


def test_rendering_path_that_escapes_the_repository_is_rejected(tmp_path: Path) -> None:
    """Corpus validation rejects a rendering path outside the repository root."""
    outside_rendering = tmp_path.parent / "outside-rendering.md"
    _write(outside_rendering, "outside rendering\n")
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text(
            "fix-grammar", rendering="../outside-rendering.md", rendering_sha256="b" * 64
        ),
    )

    with pytest.raises(ScoringInputError, match="not an existing regular file inside repository"):
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )


def test_rendering_bytes_changed_after_recording_are_rejected(tmp_path: Path) -> None:
    """Corpus validation detects rendering-byte changes after a digest is recorded."""
    rendering = "renderings/fixture.fix-grammar.md"
    expected_digest = _write_rendering(tmp_path, rendering, "original rendering\n")
    transcript_path = _write(
        tmp_path / "transcripts/fixture.fix-grammar.md",
        _arm_transcript_text(
            "fix-grammar", rendering=rendering, rendering_sha256=expected_digest
        ),
    )
    _write(tmp_path / rendering, "changed rendering\n")

    with pytest.raises(ScoringInputError, match="digest mismatch"):
        validate_transcript_rendering(
            transcript_path, parse_transcript(transcript_path), tmp_path
        )


@pytest.mark.parametrize(
    ("change", "value", "expected_control"),
    (
        ("rendering", "docs/specs/example/renderings/fix-grammar.md", "Rendering"),
        ("rendering_sha256", "b" * 64, "Rendering-sha256"),
    ),
)
def test_arm_pair_rejects_each_matching_rendering_control(
    tmp_path: Path,
    change: str,
    value: str,
    expected_control: str,
) -> None:
    """Each delivered-rendering control must vary independently between arms."""
    first, second = _arm_pair(tmp_path, **{change: value})

    with pytest.raises(ScoringInputError, match=expected_control):
        validate_arm_control_pair(first, second)


@pytest.mark.parametrize(
    ("change", "value", "expected_control"),
    (
        ("baseline", "docs/specs/example/other.md", "Baseline"),
        ("model", "other-model", "Model"),
        ("settings", "temperature=1", "Settings"),
        ("instructions", "b" * 64, "Instructions"),
    ),
)
def test_arm_pair_rejects_each_individual_control_mismatch(
    tmp_path: Path,
    change: str,
    value: str,
    expected_control: str,
) -> None:
    """AC-0006 names each control when it is the pair's sole mismatch."""
    first, second = _arm_pair(tmp_path, **{change: value})

    with pytest.raises(ScoringInputError, match=expected_control):
        validate_arm_control_pair(first, second)


def test_arm_pair_rejects_matching_arms(tmp_path: Path) -> None:
    """AC-0006 requires the two compared transcript arms to differ."""
    first = parse_transcript(
        _write(tmp_path / "first.md", _arm_transcript_text("fix-grammar"))
    )
    second = parse_transcript(
        _write(tmp_path / "second.md", _arm_transcript_text("fix-grammar"))
    )

    with pytest.raises(ScoringInputError, match="Arm"):
        validate_arm_control_pair(first, second)


def _transcript_path(transcripts_directory: Path, case_path: Path, arm: str) -> Path:
    """Return the canonical transcript path for one frozen case and arm."""
    return transcripts_directory / f"{case_path.stem}.{arm}.md"


def _validate_frozen_case_corpus(
    cases_directory: Path,
    transcripts_directory: Path,
    expected_case_names: tuple[str, ...],
    repository_root: Path,
) -> None:
    """Assert that each frozen case has matching, control-checked transcript arms."""
    case_paths = sorted(
        path for path in cases_directory.glob("*.md") if not path.name.endswith(".baseline.md")
    )
    actual_case_names = tuple(path.name for path in case_paths)
    expected_case_set = set(expected_case_names)
    actual_case_set = set(actual_case_names)
    missing_case_names = sorted(expected_case_set - actual_case_set)
    unexpected_case_names = sorted(actual_case_set - expected_case_set)
    assert not missing_case_names and not unexpected_case_names, (
        "case files differ: "
        f"missing {', '.join(missing_case_names) or 'none'}; "
        f"unexpected {', '.join(unexpected_case_names) or 'none'}"
    )

    for case_path in case_paths:
        case = parse_case(case_path)
        transcripts: list[Transcript] = []
        for arm in ("fix-grammar", "neutral-grammar"):
            transcript_path = _transcript_path(transcripts_directory, case_path, arm)
            assert transcript_path.is_file(), (
                f"missing transcript for {case_path.name} / {arm}: {transcript_path}"
            )
            transcript = parse_transcript(transcript_path)
            assert transcript.arm == arm
            validate_transcript_rendering(transcript_path, transcript, repository_root)
            validate_case_and_transcript(case, transcript)
            transcripts.append(transcript)
        validate_arm_control_pair(transcripts[0], transcripts[1])

    expected_transcript_paths = {
        _transcript_path(transcripts_directory, case_path, arm)
        for case_path in case_paths
        for arm in ("fix-grammar", "neutral-grammar")
    }
    actual_transcript_paths = {
        path
        for path in transcripts_directory.glob("*.md")
        if not path.name.endswith((".raw.md", ".answered.md"))
    }
    unexpected_transcript_paths = sorted(actual_transcript_paths - expected_transcript_paths)
    assert not unexpected_transcript_paths, (
        "unaccounted transcript files: "
        + ", ".join(str(path) for path in unexpected_transcript_paths)
    )


def test_frozen_case_corpus_rejects_a_missing_arm(tmp_path: Path) -> None:
    """AC-0005 does not let a missing transcript arm pass discovery vacuously."""
    cases_directory = tmp_path / "cases"
    transcripts_directory = tmp_path / "transcripts"
    cases_directory.mkdir()
    case_path = _write(cases_directory / "fixture.md", _case_text("- F1 — finding\n"))

    with pytest.raises(AssertionError, match="missing transcript.*fix-grammar"):
        _validate_frozen_case_corpus(cases_directory, transcripts_directory, (case_path.name,), tmp_path)


def test_frozen_case_corpus_rejects_a_missing_case_file(tmp_path: Path) -> None:
    """AC-0005 names an expected case file that discovery cannot find."""
    cases_directory = tmp_path / "cases"
    transcripts_directory = tmp_path / "transcripts"
    cases_directory.mkdir()
    _write(cases_directory / "first.md", _case_text("- F1 — finding\n"))

    with pytest.raises(AssertionError, match="missing second.md"):
        _validate_frozen_case_corpus(
            cases_directory, transcripts_directory, ("first.md", "second.md"), tmp_path
        )


def test_frozen_case_corpus_rejects_transcript_findings_that_differ_from_its_case(
    tmp_path: Path,
) -> None:
    """AC-0005 names a response finding absent from its source case."""
    cases_directory = tmp_path / "cases"
    transcripts_directory = tmp_path / "transcripts"
    cases_directory.mkdir()
    transcripts_directory.mkdir()
    case_path = _write(cases_directory / "fixture.md", _case_text("- F1 — finding\n"))
    _write(
        transcripts_directory / "fixture.fix-grammar.md",
        _corpus_transcript_text(tmp_path, "fix-grammar"),
    )
    _write(
        transcripts_directory / "fixture.neutral-grammar.md",
        _corpus_transcript_text(tmp_path, "neutral-grammar", finding_id="F2").replace(
            "corrected it", "incorrect finding"
        ),
    )

    with pytest.raises(ScoringInputError, match="extra F2"):
        _validate_frozen_case_corpus(cases_directory, transcripts_directory, (case_path.name,), tmp_path)


def test_frozen_case_corpus_rejects_an_unaccounted_transcript(tmp_path: Path) -> None:
    """AC-0005 rejects a stale transcript outside every expected case-and-arm pair."""
    cases_directory = tmp_path / "cases"
    transcripts_directory = tmp_path / "transcripts"
    cases_directory.mkdir()
    transcripts_directory.mkdir()
    case_path = _write(cases_directory / "fixture.md", _case_text("- F1 — finding\n"))
    _write(
        transcripts_directory / "fixture.fix-grammar.md",
        _corpus_transcript_text(tmp_path, "fix-grammar"),
    )
    _write(
        transcripts_directory / "fixture.neutral-grammar.md",
        _corpus_transcript_text(tmp_path, "neutral-grammar"),
    )
    extra = _write(
        transcripts_directory / "discarded-run.md",
        _corpus_transcript_text(tmp_path, "fix-grammar"),
    )

    with pytest.raises(AssertionError, match=extra.name):
        _validate_frozen_case_corpus(cases_directory, transcripts_directory, (case_path.name,), tmp_path)


def test_frozen_case_corpus_has_both_parsable_arms() -> None:
    """AC-0005 requires all three frozen cases and both parsable transcript arms."""
    _validate_frozen_case_corpus(
        _CASES_DIRECTORY, _TRANSCRIPTS_DIRECTORY, _FROZEN_CASE_NAMES, _REPOSITORY_ROOT
    )
