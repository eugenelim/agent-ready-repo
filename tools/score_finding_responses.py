"""Parse and validate recorded finding-response scoring inputs.

This module parses, validates, scores, and reports recorded finding responses.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
import stat
import sys


DISPOSITIONS = (
    "repair",
    "narrow-the-claim",
    "cut-the-item",
    "dismiss-and-re-present",
    "repair-the-generator",
    "route-to-owner",
    "bound-out-of-scope",
    "accept-as-proportionate",
)
"""The disposition vocabulary, in the report's canonical emission order."""

_FINDING_ID = re.compile(r"^F\d+$")
_CASE_FINDING = re.compile(r"^- (F\d+) — (.+)$")
_TRANSCRIPT_RESPONSE = re.compile(r"^- (F\d+) — ([a-z-]+) — (.+)$")
_ACCEPTANCE_CRITERIA_HEADING = "## Acceptance Criteria"
_CHECKBOX = re.compile(r"^- \[[ x]\]")
_SECTION_HEADING = re.compile(r"^## ")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_RENDERED_FINDING_CANDIDATE = re.compile(r"^- F")
_RENDERED_FINDING = re.compile(
    r"^- (?P<finding_id>F\d+) — (?P<finding>.+)\. "
    r"(?P<grammar>[^:]+:)(?: (?P<response>.+))$"
)


class ScoringInputError(ValueError):
    """Raised when a case or transcript does not meet the scorer contract."""


@dataclass(frozen=True)
class Case:
    """A parsed case and its ordered sustained-finding identifiers."""

    source: str
    baseline: str
    finding_ids: tuple[str, ...]


@dataclass(frozen=True)
class Response:
    """One transcript response, including its recorded disposition."""

    finding_id: str
    disposition: str


@dataclass(frozen=True)
class RenderedFinding:
    """One complete finding record parsed from a bound rendering."""

    finding_id: str
    grammar: str
    line_number: int


@dataclass(frozen=True)
class Transcript:
    """A parsed transcript and disposition validation errors found within it."""

    arm: str
    grammar: str
    rendering: str
    rendering_sha256: str
    baseline: str
    answered: str
    model: str
    settings: str
    instructions: str
    responses: tuple[Response, ...]
    disposition_errors: tuple[str, ...]


@dataclass(frozen=True)
class Score:
    """The metrics and canonical finding order for one validated transcript."""

    arm: str
    repair_count: int
    finding_count: int
    non_repair_counts: dict[str, int]
    baseline_criteria_count: int
    answered_criteria_count: int
    findings: tuple[Response, ...]

    @property
    def criteria_change(self) -> int:
        """Return the answered-artifact criterion change from the baseline."""
        return self.answered_criteria_count - self.baseline_criteria_count


def _read_lines(path: Path) -> list[str]:
    """Read a UTF-8 input file as lines without their trailing newlines."""
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ScoringInputError(f"cannot read {path}: {error}") from error


def _require_header(lines: list[str], index: int, prefix: str, path: Path) -> str:
    """Return one ordered header value or raise a useful grammar error."""
    if index >= len(lines) or not lines[index].startswith(prefix):
        raise ScoringInputError(f"{path}: expected header {prefix.rstrip(': ')}")
    value = lines[index][len(prefix) :]
    if not value:
        raise ScoringInputError(f"{path}: empty header {prefix.rstrip(': ')}")
    return value


def parse_case(path: Path) -> Case:
    """Parse one case file in the fixed, line-oriented case grammar."""
    lines = _read_lines(path)
    title = _require_header(lines, 0, "# Case: ", path)
    if not title:
        raise ScoringInputError(f"{path}: empty case title")
    source = _require_header(lines, 1, "Source: ", path)
    baseline = _require_header(lines, 2, "Baseline: ", path)
    if len(lines) < 4 or lines[3] != "":
        raise ScoringInputError(f"{path}: expected a blank line before findings")

    finding_ids: list[str] = []
    errors: list[str] = []
    for line_number, line in enumerate(lines[4:], start=5):
        match = _CASE_FINDING.fullmatch(line)
        if match is None:
            errors.append(f"{path}:{line_number}: invalid case finding line")
            continue
        finding_id = match.group(1)
        if not _FINDING_ID.fullmatch(finding_id):
            errors.append(f"{path}:{line_number}: invalid finding identifier {finding_id}")
            continue
        finding_ids.append(finding_id)
    if not finding_ids:
        errors.append(f"{path}: case has no findings")
    if errors:
        raise ScoringInputError("; ".join(errors))
    return Case(source=source, baseline=baseline, finding_ids=tuple(finding_ids))


def parse_transcript(path: Path) -> Transcript:
    """Parse one transcript and retain all invalid-disposition errors for aggregation."""
    lines = _read_lines(path)
    _require_header(lines, 0, "# Transcript: ", path)
    arm = _require_header(lines, 1, "Arm: ", path)
    grammar = _require_header(lines, 2, "Grammar: ", path)
    rendering = _require_header(lines, 3, "Rendering: ", path)
    rendering_sha256 = _require_header(lines, 4, "Rendering-sha256: ", path)
    baseline = _require_header(lines, 5, "Baseline: ", path)
    answered = _require_header(lines, 6, "Answered: ", path)
    model = _require_header(lines, 7, "Model: ", path)
    settings = _require_header(lines, 8, "Settings: ", path)
    instructions = _require_header(lines, 9, "Instructions: ", path)
    if not _SHA256.fullmatch(rendering_sha256):
        raise ScoringInputError(f"{path}: invalid Rendering-sha256")
    if len(lines) < 11 or lines[10] != "":
        raise ScoringInputError(f"{path}: expected a blank line before responses")

    responses: list[Response] = []
    errors: list[str] = []
    for line_number, line in enumerate(lines[11:], start=12):
        match = _TRANSCRIPT_RESPONSE.fullmatch(line)
        if match is None:
            errors.append(f"{path}:{line_number}: invalid transcript response line")
            continue
        finding_id, disposition = match.group(1), match.group(2)
        responses.append(Response(finding_id=finding_id, disposition=disposition))
        if disposition not in DISPOSITIONS:
            errors.append(
                f"{path}:{line_number}: finding {finding_id} has invalid disposition {disposition}"
            )
    if not responses:
        errors.append(f"{path}: transcript has no responses")
    return Transcript(
        arm=arm,
        grammar=grammar,
        rendering=rendering,
        rendering_sha256=rendering_sha256,
        baseline=baseline,
        answered=answered,
        model=model,
        settings=settings,
        instructions=instructions,
        responses=tuple(responses),
        disposition_errors=tuple(errors),
    )


def validate_transcript_rendering(
    transcript_path: Path, transcript: Transcript, repository_root: Path
) -> None:
    """Bind a transcript to its canonical local rendering and its declared grammar."""
    resolved_repository_root = repository_root.resolve()
    recorded_path = resolved_repository_root / transcript.rendering
    resolved_rendering_path = recorded_path.resolve()
    if not resolved_rendering_path.is_relative_to(resolved_repository_root):
        raise ScoringInputError(
            f"{transcript_path}: Rendering {transcript.rendering!r} is not an existing "
            f"regular file inside repository {resolved_repository_root}"
        )

    expected_rendering = _canonical_rendering_path(
        transcript_path, transcript.arm, resolved_repository_root
    )
    if transcript.rendering != expected_rendering:
        raise ScoringInputError(
            f"{transcript_path}: Rendering path mismatch: expected {expected_rendering!r}; "
            f"given {transcript.rendering!r}"
        )

    try:
        file_mode = recorded_path.lstat().st_mode
    except OSError as error:
        raise ScoringInputError(
            f"{transcript_path}: Rendering {transcript.rendering!r} is not an existing "
            f"regular file inside repository {resolved_repository_root}"
        ) from error
    if stat.S_ISLNK(file_mode):
        raise ScoringInputError(
            f"{transcript_path}: Rendering {transcript.rendering!r} must not be a symlink"
        )
    if not stat.S_ISREG(file_mode):
        raise ScoringInputError(
            f"{transcript_path}: Rendering {transcript.rendering!r} is not an existing "
            f"regular file inside repository {resolved_repository_root}"
        )

    computed_digest = hashlib.sha256(recorded_path.read_bytes()).hexdigest()
    if computed_digest != transcript.rendering_sha256:
        raise ScoringInputError(
            f"{transcript_path}: Rendering {transcript.rendering!r} digest mismatch: "
            f"expected {transcript.rendering_sha256}; computed {computed_digest}"
        )

    rendering_lines = _read_lines(recorded_path)
    rendered_findings: list[RenderedFinding] = []
    for line_number, line in enumerate(rendering_lines, start=1):
        if _RENDERED_FINDING_CANDIDATE.match(line) is None:
            continue
        match = _RENDERED_FINDING.fullmatch(line)
        if match is None:
            raise ScoringInputError(
                f"{transcript_path}: Rendering {transcript.rendering!r} line {line_number} "
                f"has malformed finding record: {line}"
            )
        rendered_findings.append(
            RenderedFinding(
                finding_id=match.group("finding_id"),
                grammar=match.group("grammar"),
                line_number=line_number,
            )
        )

    if not rendered_findings:
        raise ScoringInputError(
            f"{transcript_path}: Rendering {transcript.rendering!r} has no finding records"
        )

    response_counts = Counter(response.finding_id for response in transcript.responses)
    rendering_counts = Counter(finding.finding_id for finding in rendered_findings)
    correspondence_errors: list[str] = []
    for finding_id in sorted(response_counts.keys() - rendering_counts.keys()):
        correspondence_errors.append(f"missing {finding_id}")
    for finding_id in sorted(rendering_counts.keys() - response_counts.keys()):
        correspondence_errors.append(f"extra {finding_id}")
    for finding_id in sorted(
        finding_id for finding_id, count in rendering_counts.items() if count > 1
    ):
        correspondence_errors.append(f"repeated {finding_id}")
    if correspondence_errors:
        raise ScoringInputError(
            f"{transcript_path}: Rendering {transcript.rendering!r} finding identifiers "
            f"do not correspond to transcript responses: {'; '.join(correspondence_errors)}"
        )

    for finding in rendered_findings:
        if finding.grammar != transcript.grammar:
            raise ScoringInputError(
                f"{transcript_path}: Rendering {transcript.rendering!r} line "
                f"{finding.line_number} finding "
                f"{finding.finding_id} does not carry Grammar {transcript.grammar!r}: "
                f"{finding.grammar!r}"
            )

def _canonical_rendering_path(
    transcript_path: Path, arm: str, repository_root: Path
) -> str:
    """Derive the sole rendering path from a transcript's case filename and arm."""
    resolved_transcript_path = transcript_path.resolve()
    try:
        transcript_relative_path = resolved_transcript_path.relative_to(repository_root)
    except ValueError as error:
        raise ScoringInputError(
            f"{transcript_path}: transcript is outside repository {repository_root}"
        ) from error
    if transcript_relative_path.parent.name != "transcripts":
        raise ScoringInputError(
            f"{transcript_path}: transcript must be stored in a transcripts directory"
        )

    suffix = f".{arm}"
    transcript_stem = transcript_relative_path.stem
    if not transcript_stem.endswith(suffix) or transcript_stem == suffix:
        raise ScoringInputError(
            f"{transcript_path}: filename does not name arm {arm!r}"
        )
    case_name = transcript_stem[: -len(suffix)]
    return (
        transcript_relative_path.parent.parent
        / "renderings"
        / f"{case_name}.{arm}.md"
    ).as_posix()


def validate_case_and_transcript(case: Case, transcript: Transcript) -> None:
    """Raise one error naming every disposition and correspondence offender."""
    case_counts = Counter(case.finding_ids)
    response_counts = Counter(response.finding_id for response in transcript.responses)
    errors = list(transcript.disposition_errors)

    for finding_id in sorted(case_counts.keys() - response_counts.keys()):
        errors.append(f"missing {finding_id}")
    for finding_id in sorted(response_counts.keys() - case_counts.keys()):
        errors.append(f"extra {finding_id}")
    for finding_id in sorted(
        finding_id for finding_id, count in response_counts.items() if count > 1
    ):
        errors.append(f"repeated {finding_id}")

    if errors:
        raise ScoringInputError("; ".join(errors))


def validate_arm_control_pair(first: Transcript, second: Transcript) -> None:
    """Raise an error when a two-arm pair lacks the required control variation."""
    errors: list[str] = []
    if first.arm == second.arm:
        errors.append("Arm must differ")
    if first.grammar == second.grammar:
        errors.append("Grammar must differ")
    if first.rendering == second.rendering:
        errors.append("Rendering must differ")
    if first.rendering_sha256 == second.rendering_sha256:
        errors.append("Rendering-sha256 must differ")
    for control, first_value, second_value in (
        ("Baseline", first.baseline, second.baseline),
        ("Model", first.model, second.model),
        ("Settings", first.settings, second.settings),
        ("Instructions", first.instructions, second.instructions),
    ):
        if first_value != second_value:
            errors.append(f"{control} differs")
    if errors:
        raise ScoringInputError("; ".join(errors))


def _count_acceptance_criteria(artifact: str) -> int:
    """Count checked or unchecked criteria within the acceptance-criteria section."""
    in_section = False
    count = 0
    for line in _read_lines(Path(artifact)):
        if line == _ACCEPTANCE_CRITERIA_HEADING:
            in_section = True
            continue
        if in_section and _SECTION_HEADING.match(line) is not None:
            break
        if in_section and _CHECKBOX.match(line) is not None:
            count += 1
    return count


def _finding_number(response: Response) -> int:
    """Return the numeric portion of a validated finding identifier."""
    return int(response.finding_id[1:])


def score_case_and_transcript(case: Case, transcript: Transcript) -> Score:
    """Validate and score one case/transcript pair using both named artifacts."""
    validate_case_and_transcript(case, transcript)
    disposition_counts = Counter(response.disposition for response in transcript.responses)
    non_repair_counts = {
        disposition: disposition_counts[disposition]
        for disposition in DISPOSITIONS
        if disposition != "repair"
    }
    return Score(
        arm=transcript.arm,
        repair_count=disposition_counts["repair"],
        finding_count=len(transcript.responses),
        non_repair_counts=non_repair_counts,
        baseline_criteria_count=_count_acceptance_criteria(transcript.baseline),
        answered_criteria_count=_count_acceptance_criteria(transcript.answered),
        findings=tuple(sorted(transcript.responses, key=_finding_number)),
    )


def render_score(score: Score) -> str:
    """Render one score in the stable report order required by AC-0004."""
    disposition_counts = {"repair": score.repair_count, **score.non_repair_counts}
    change = score.criteria_change
    change_text = f"+{change}" if change >= 0 else str(change)
    lines = [
        f"Arm: {score.arm}",
        f"Repair share: {score.repair_count}/{score.finding_count}",
        "Dispositions:",
    ]
    lines.extend(f"- {disposition}: {disposition_counts[disposition]}" for disposition in DISPOSITIONS)
    lines.extend(
        (
            "Acceptance criteria: "
            f"baseline {score.baseline_criteria_count}; "
            f"answered {score.answered_criteria_count}; change {change_text}",
            "Findings:",
        )
    )
    lines.extend(f"- {response.finding_id}: {response.disposition}" for response in score.findings)
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """Score one case/transcript pair from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_file", type=Path)
    parser.add_argument("transcript_file", type=Path)
    args = parser.parse_args(argv)
    try:
        case = parse_case(args.case_file)
        transcript = parse_transcript(args.transcript_file)
        score = score_case_and_transcript(case, transcript)
    except ScoringInputError as error:
        print(error, file=sys.stderr)
        return 2
    print(render_score(score), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
