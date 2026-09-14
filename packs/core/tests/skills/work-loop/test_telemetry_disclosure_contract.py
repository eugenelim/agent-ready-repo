"""T5's documentation criteria, checked against the files rather than by reading.

AC-0020, AC-0021, AC-0022, AC-0042, AC-0045, AC-0051 and AC-0054 of
`docs/specs/loop-telemetry-export`.

Most of these are literal-string criteria, and a literal does not care about
Markdown: a phrase broken across two source lines is absent as far as the
criterion is concerned. That is not hypothetical -- AC-0054's third string was
introduced wrapped and this file is what caught it.

AC-0051 is the one that cannot be satisfied by editing prose alone: the integer
written in section 5.1 is compared against the key count of a line the engine
actually emits, so the sentence cannot drift from the envelope it describes.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[5]
_TELEMETRY = _REPO / "docs/architecture/telemetry.md"
_AGENTBUNDLE = _REPO / "docs/architecture/agentbundle.md"
_GUIDE = _REPO / "guides/core/how-to/export-loop-telemetry.md"

_NUMBER_WORDS = {
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20,
}


def _section(text: str, heading: str) -> str:
    """The body under one heading, stopping at the next heading of any level."""
    marker = f"\n{heading}\n"
    assert marker in text, f"heading {heading!r} not found"
    body = text.split(marker, 1)[1]
    return re.split(r"\n#{1,6} ", body, maxsplit=1)[0]


def _emitted_line_key_count(tmp_path: Path) -> int:
    from test_loop_engine_events_jsonl import (
        _LOOP_ENGINE,
        _engine_init,
        _init_git_repo,
        _make_spec_dir,
        _run,
    )

    repo = _init_git_repo(tmp_path)
    spec_dir = _make_spec_dir(repo)
    _engine_init(repo, spec_dir)
    _run(_LOOP_ENGINE, "transition", str(spec_dir), "spec-ready", cwd=repo)
    line = (repo / ".loop-run" / "events.jsonl").read_text().splitlines()[-1]
    return len(json.loads(line))


# --- AC-0020 -----------------------------------------------------------------

@pytest.mark.parametrize(
    "literal",
    [".loop-run/events.jsonl", "OTLP logs", "nothing is sent until you configure an endpoint"],
)
def test_guide_discloses_what_leaves_the_machine(literal: str) -> None:
    section = _section(_GUIDE.read_text(encoding="utf-8"), "## What leaves your machine")
    assert literal in section, (
        f"{literal!r} is not in the disclosure section. A phrase wrapped across "
        "two source lines does not count -- keep it on one line."
    )


# --- AC-0021 / AC-0022 / AC-0054 ---------------------------------------------

@pytest.mark.parametrize("retired", ["does not work today", "writes nothing for any pack"])
def test_telemetry_page_has_dropped_its_retired_claims(retired: str) -> None:
    assert retired not in _TELEMETRY.read_text(encoding="utf-8")


@pytest.mark.parametrize("retired", ["No exporter ships", "Nothing transmits"])
def test_entrypoints_section_has_dropped_its_retired_claims(retired: str) -> None:
    assert retired not in _section(_TELEMETRY.read_text(encoding="utf-8"), "## 2. Entrypoints")


@pytest.mark.parametrize(
    "literal",
    ["jsonl-otlp-exporter", "separately installed", "sends nothing until an endpoint is configured"],
)
def test_entrypoints_section_says_what_is_true_now(literal: str) -> None:
    """AC-0054 is the positive half.

    AC-0021 and AC-0022 only delete. Without this, a section 2 gutted to a bare
    heading would satisfy both of them.
    """
    assert literal in _section(_TELEMETRY.read_text(encoding="utf-8"), "## 2. Entrypoints")


# --- AC-0045 -----------------------------------------------------------------

def test_every_agentbundle_anchor_cited_by_telemetry_resolves() -> None:
    def slug(heading: str) -> str:
        s = re.sub(r"[^\w\s-]", "", heading.strip().lower())
        return re.sub(r"\s+", "-", s).strip("-")

    headings = {
        slug(m.group(1))
        for m in re.finditer(r"^#{1,6}\s+(.*)$", _AGENTBUNDLE.read_text(encoding="utf-8"), re.M)
    }
    cited = set(re.findall(r"agentbundle\.md#([a-z0-9\-]+)", _TELEMETRY.read_text(encoding="utf-8")))
    assert cited, "no agentbundle.md anchor is cited — this guard would pass vacuously"
    dead = sorted(a for a in cited if a not in headings)
    assert not dead, f"dead agentbundle.md anchors: {dead}"


# --- AC-0051 -----------------------------------------------------------------

def test_section_5_1_field_count_equals_what_the_engine_emits(tmp_path: Path) -> None:
    section = _section(_TELEMETRY.read_text(encoding="utf-8"), "### 5.1 What a line holds")
    match = re.search(r"Each line carries (\w+) fields", section)
    assert match, "section 5.1 no longer states a field count in the expected form"
    word = match.group(1).lower()
    stated = int(word) if word.isdigit() else _NUMBER_WORDS.get(word)
    assert stated is not None, f"unrecognised field count {word!r}"
    assert stated == _emitted_line_key_count(tmp_path)


# --- AC-0042 -----------------------------------------------------------------

def test_guide_names_no_exit_code_in_the_reserved_band() -> None:
    """2 through 9 belong to the credentialed-CLI exit-code contract.

    A consumer reading an exit code documented here must never be misled into
    reading it as one of those.
    """
    text = _GUIDE.read_text(encoding="utf-8")
    codes: list[int] = []
    # Prose: "exit 3", "exits 3", "exit code 3", "status code 3", "returns status 3".
    codes += [
        int(n)
        for n in re.findall(
            r"(?:exit|exits|exit code|exit status|status code|returns status)\s+(\d+)",
            text,
            re.I,
        )
    ]
    # A table row such as `| 3 | usage error |` names a code with no prose at all,
    # which the prose pattern above cannot see.
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        if not re.search(r"exit|status|code", line, re.I):
            probe = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
            if not any(re.fullmatch(r"\d+", c) for c in probe):
                continue
        # strip Markdown code ticks: `| `3` | refused |` names a code too
        cells = [c.strip().strip("`").strip() for c in line.strip().strip("|").split("|")]
        codes += [int(c) for c in cells if re.fullmatch(r"\d+", c)]
    reserved = sorted({c for c in codes if 2 <= c <= 9})
    assert not reserved, f"guide names exit codes in the reserved 2-9 band: {reserved}"
