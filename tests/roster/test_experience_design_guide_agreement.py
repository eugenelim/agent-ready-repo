"""Each experience-design guide step says what its skill actually does.

Every step page publishes an ``artifact_location`` obligation for each skill it
runs: ``**Where it lands:**`` with a backticked path, or ``**Writes no
artifact.**``. The obligation is what an adopter reads before waiting for a
file, so each one must be a path the owning skill declares, a path naming the
artifact the skill enriches, or an honest statement that nothing is written.

This test reads ``guides/`` as well as ``packs/``, so it is repository-level and
lives here rather than in the pack suite.

Two deliberate limits, both stated rather than worked around:

* Paths are compared with their templated segments normalized. The guides and
  the skills name the same file with different placeholder words — ``copy/
  <slug>.md`` against ``copy/<surface-slug>.md`` — and a byte comparison would
  report a disagreement that does not exist.
* A ``**Writes no artifact.**`` step is checked against the absence of a
  ``**Writes:**`` declaration line, not against the skill's prose. Only the four
  skills this contract covers declare a target on that line; the remaining
  writers state their target in prose, and no predicate over that prose
  separates a write from a read.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDES = ROOT / "guides" / "experience-design" / "how-to"
SKILLS = ROOT / "packs" / "experience-design" / ".apm" / "skills"

RUN_HEADING = re.compile(r"^## Run `([^`]+)`", re.MULTILINE)
WHERE_IT_LANDS = re.compile(r"^\*\*Where it lands:\*\*(.*)$", re.MULTILINE)
WRITES_NO_ARTIFACT = re.compile(r"^\*\*Writes no artifact\.\*\*", re.MULTILINE)
WRITES_LINE = re.compile(r"^\*\*Writes:\*\* `([^`]+)`$", re.MULTILINE)
OUTPUT_PATH = re.compile(r"`(<output_dir>/[^`\n]+)`")
TEMPLATED_SEGMENT = re.compile(r"<[^>/]+>")
ORDER_KEY = re.compile(r"^order:\s*\d+\s*$", re.MULTILINE)
TRAILING_HEADING = "\n## Where this leads"


def _normalize(path: str) -> str:
    """A path with each templated segment reduced to one marker.

    ``<slug>`` and ``<surface-slug>`` are the same hole in the same path.
    """
    return TEMPLATED_SEGMENT.sub("<>", path)


def _declared_paths() -> dict[str, set[str]]:
    """Every ``<output_dir>``-rooted path each skill names, normalized."""
    declared: dict[str, set[str]] = {}
    for directory in sorted(SKILLS.iterdir()):
        skill = directory / "SKILL.md"
        if skill.is_file():
            text = skill.read_text(encoding="utf-8")
            declared[directory.name] = {_normalize(p) for p in OUTPUT_PATH.findall(text)}
    return declared


def _writes_lines() -> dict[str, list[str]]:
    """The declaration line each skill carries, if it carries one."""
    return {
        directory.name: WRITES_LINE.findall(
            (directory / "SKILL.md").read_text(encoding="utf-8")
        )
        for directory in sorted(SKILLS.iterdir())
        if (directory / "SKILL.md").is_file()
    }


def _step_pages() -> list[Path]:
    """Guide pages carrying an ``order:`` key, which is what makes a page a step."""
    return [p for p in sorted(GUIDES.glob("*.md")) if ORDER_KEY.search(p.read_text(encoding="utf-8"))]


def _run_blocks(page: Path) -> list[tuple[str, str]]:
    """Each ``## Run `<skill>`` block on *page*, as (skill, body)."""
    text = page.read_text(encoding="utf-8")
    matches = list(RUN_HEADING.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end():end]
        blocks.append((match.group(1), body.split(TRAILING_HEADING)[0]))
    return blocks


DECLARED = _declared_paths()
WRITES = _writes_lines()
STEPS = _step_pages()
ANY_DECLARED = {path for paths in DECLARED.values() for path in paths}


def test_the_guide_steps_are_readable() -> None:
    """There are steps to check, so nothing below passes by finding nothing."""
    assert STEPS, f"no step page with an order: key under {GUIDES}"
    assert DECLARED, f"no skills found under {SKILLS}"


def test_every_run_block_carries_one_artifact_location() -> None:
    """Each skill a step runs states where its output lands, or that none does."""
    for page in STEPS:
        for skill, body in _run_blocks(page):
            lands = len(WHERE_IT_LANDS.findall(body))
            none = len(WRITES_NO_ARTIFACT.findall(body))
            assert lands + none == 1, (
                f"{page.name} § Run `{skill}`: {lands} **Where it lands:** and "
                f"{none} **Writes no artifact.** — expected exactly one obligation"
            )


def test_every_run_block_names_a_skill_the_pack_ships() -> None:
    """A step that runs a skill the pack does not ship cannot be checked at all."""
    for page in STEPS:
        for skill, _ in _run_blocks(page):
            assert skill in DECLARED, f"{page.name} runs `{skill}`, which this pack does not ship"


def test_every_published_path_is_one_a_skill_declares() -> None:
    """A published path is the owner's declared target, or the artifact it enriches.

    The enriched form is admitted only for a skill that declares no target of its
    own: that is what an enricher is, and admitting it generally would let any
    step publish any other skill's path.
    """
    for page in STEPS:
        for skill, body in _run_blocks(page):
            for line in WHERE_IT_LANDS.findall(body):
                published = [_normalize(p) for p in OUTPUT_PATH.findall(line)]
                assert published, (
                    f"{page.name} § Run `{skill}`: **Where it lands:** names no "
                    f"<output_dir>-rooted path"
                )
                admissible = DECLARED[skill] or ANY_DECLARED
                for path in published:
                    assert path in admissible, (
                        f"{page.name} § Run `{skill}` publishes {path!r}, which "
                        f"{'no skill' if not DECLARED[skill] else skill} declares; "
                        f"admissible: {sorted(admissible)}"
                    )


def test_every_writes_no_artifact_step_owns_a_skill_that_declares_none() -> None:
    """A step may deny a write only where its skill declares no write target."""
    for page in STEPS:
        for skill, body in _run_blocks(page):
            if WRITES_NO_ARTIFACT.search(body):
                assert not WRITES[skill], (
                    f"{page.name} § Run `{skill}` states **Writes no artifact.** "
                    f"while the skill declares **Writes:** {WRITES[skill]}"
                )
