#!/usr/bin/env python3
"""Instruction roster for the tracker-origin registration stop.

Spec: docs/specs/tracker-origin-registration-stop/spec.md

Closed lists of files and phrases a writer, guide or page must no longer hold
(each present at commit ``e8679a9a3``, so an absence cannot come from a typo in
the list) and the phrases they must hold. Standard library only; the checks read
files and git history and write nothing.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_BASELINE = "e8679a9a3"

_INTAKE = "packs/core/.apm/skills/work-intake/SKILL.md"
_BRIEF = "packs/core/.apm/skills/author-delivery-brief/SKILL.md"
_SCHEMA_GUIDE = "guides/core/reference/workspace-toml-schema.md"
_ARCH = "docs/architecture/work-intake-and-artifact-routing.md"

# AC-0017 and AC-0018: file -> phrases it must not hold (each present at the baseline).
_ABSENT: dict[str, tuple[str, ...]] = {
    _INTAKE: (
        "is registered as before, because refresh checks its tracker profile through the entry alone",
        "register a tracker-origin intent as a Draft",
        "resolve the existing entry and its exact tracker profile",
        "register a tracker-origin artifact in",
        "(a tracker-origin intent is registered)",
        "In each registered case the artifact comes first",
        "write the canonical artifact first, then register the schema-valid workspace entry",
        "Use the same helper to sequence registration",
    ),
    _BRIEF: (
        "add its one schema-valid Draft entry",
        "move the complete structured brief entry",
        "tracker-origin brief's workspace entry",
        "Only a tracker-origin brief's entry moves",
        "its existing structured workspace entry",
    ),
    "packs/core/.apm/skills/close-work/SKILL.md": ("for a tracker-origin brief it also moves",),
    "packs/core/.apm/skills/intake-intent/SKILL.md": (
        "let the calling intake workflow add its one non-dispatchable",
    ),
    "packs/github/JOURNEY.md": ("registered tracker-origin artifact",),
    "packs/linear/JOURNEY.md": ("registered tracker-origin artifact",),
    _SCHEMA_GUIDE: (
        "tracker-origin intent and brief entries stay",
        "A tracker-origin spec keeps its entry",
        "For a tracker-origin brief entry",
        "tracker-origin entry moves to the matching collection",
    ),
    "guides/core/how-to/intake-an-external-brief.md": (
        "keeps a registry entry",
        "Brief file created and registered in",
        "If registration fails",
    ),
    "guides/core/reference/work-intake-routing-and-lifecycle.md": (
        "Only a spec or a tracker-origin intent or brief is registered",
        "register it only when it is a spec or a tracker-origin",
        "A tracker-origin brief's entry sits in the collection that matches its status",
    ),
    "guides/_shared/reference/work-intake-routing-and-lifecycle.md": (
        "`work.queue` for a tracker-origin one",
        "`brief_queue.draft` for a tracker-origin one",
        "repository backlog for a tracker-origin one",
        "A spec, and a tracker-origin intent or brief, is registered",
    ),
    "guides/catalogue-curation/tutorials/your-first-skill.md": ("registers a tracker-origin item",),
    "guides/_shared/how-to/use-work-intake.md": (
        "A spec or a tracker-origin item also gets a non-dispatchable entry",
        "is registered as tracker-origin",
    ),
    "guides/core/how-to/capture-work.md": (
        "A spec or a tracker-origin item also gets a non-dispatchable entry",
    ),
    "guides/core/how-to/start-or-remember-work.md": ("unless it is tracker-origin",),
    "guides/core/explanation/two-room-model.md": (
        "only a spec or a tracker-origin item is also registered",
        "a tracker-origin one is registered in",
        "a tracker-origin entry moves to",
    ),
    "guides/product-engineering/how-to/hand-an-intent-to-build.md": (
        "a spec or a tracker-origin artifact is also registered",
    ),
    "guides/atlassian/how-the-atlassian-pack-works.md": ("For registered tracker-origin work",),
    "guides/atlassian/work-with-jira.md": ("created and registered a tracker-origin",),
    _ARCH: (
        "a tracker-origin brief's entry carries the same state",
        "for a tracker-origin brief, its entry",
        "mirrored by structured workspace source fields",
        "Refresh processors receive an existing registered artifact",
    ),
}

# AC-0028: file -> phrases it must hold.
_PRESENT: dict[str, tuple[str, ...]] = {
    _INTAKE: (
        "tracker_profile",
        "never infer a processor from the artifact kind, tracker content, labels, or prose",
    ),
    _BRIEF: ("keep an existing source-authority block byte for byte",),
    "packs/core/.apm/skills/new-spec/SKILL.md": (
        "keep an existing source-authority block byte for byte",
    ),
    "packs/core/.apm/skills/workspace-status/SKILL.md": ("tracker-entry-drop",),
    "packs/core/.apm/skills/workspace-status/references/mutate.md": ("tracker-entry-drop",),
    _SCHEMA_GUIDE: ("tracker-entry-drop",),
    _ARCH: ("tracker_profile",),
}

# AC-0028: one paragraph of work-intake holds all three.
_PARAGRAPH = ("add-record-tracker-profile", "tracker-entry-drop", "ask the owner for the profile")
# AC-0028: under the `### 5.` heading of work-intake.
_SECTION_5_PHRASE = (
    "pass the tracker source to the transaction for a tracker-origin brief or spec, never for an intent"
)

_ABSENT_CASES = [
    pytest.param(rel, phrase, id=f"absent:{rel}:{n}")
    for rel, phrases in _ABSENT.items()
    for n, phrase in enumerate(phrases)
]
_PRESENT_CASES = [
    pytest.param(rel, phrase, id=f"present:{rel}:{n}")
    for rel, phrases in _PRESENT.items()
    for n, phrase in enumerate(phrases)
]


def _flat_text(text: str) -> str:
    """The text with each run of whitespace, line breaks included, read as one space."""
    return " ".join(text.split())


def _flat(rel: str) -> str:
    return _flat_text((_REPO / rel).read_text(encoding="utf-8"))


def _baseline(rel: str) -> str:
    """The file's text at the baseline commit, whitespace-normalised."""
    result = subprocess.run(
        ["git", "show", f"{_BASELINE}:{rel}"],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"commit {_BASELINE} is not available in this checkout")
    return _flat_text(result.stdout)


def _sections(text: str) -> list[tuple[str, list[str]]]:
    """Raw lines split at each heading: a line starting `#` outside a fenced code block."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if not fenced and line.startswith("#"):
            sections.append((line, []))
        else:
            sections[-1][1].append(line)
    return sections


def test_roster_lists_are_well_formed() -> None:
    for table in (_ABSENT, _PRESENT):
        for rel, phrases in table.items():
            assert (_REPO / rel).is_file(), rel
            assert phrases and all(isinstance(p, str) and p for p in phrases), rel


@pytest.mark.parametrize(("rel", "phrase"), _ABSENT_CASES)
def test_no_listed_phrase_remains(rel: str, phrase: str) -> None:
    assert phrase not in _flat(rel), f"{rel} holds {phrase!r}"


@pytest.mark.parametrize(("rel", "phrase"), _ABSENT_CASES)
def test_every_banned_phrase_was_present_at_the_baseline(rel: str, phrase: str) -> None:
    assert phrase in _baseline(rel), f"{rel} did not hold {phrase!r} at {_BASELINE}"


@pytest.mark.parametrize(("rel", "phrase"), _PRESENT_CASES)
def test_every_required_phrase_is_present(rel: str, phrase: str) -> None:
    assert phrase in _flat(rel), f"{rel} lacks {phrase!r}"


def test_one_intake_paragraph_maps_the_refresh_next_action() -> None:
    text = (_REPO / _INTAKE).read_text(encoding="utf-8")
    paragraphs = [_flat_text(p) for p in re.split(r"\n\s*\n", text)]
    assert any(all(phrase in p for phrase in _PARAGRAPH) for p in paragraphs)


def test_section_5_names_when_to_pass_the_tracker_source() -> None:
    text = (_REPO / _INTAKE).read_text(encoding="utf-8")
    bodies = [_flat_text("\n".join(lines)) for head, lines in _sections(text) if head.startswith("### 5.")]
    assert len(bodies) == 1
    assert _SECTION_5_PHRASE in bodies[0]


def test_every_tracker_origin_example_sits_in_a_section_that_names_the_repair() -> None:
    text = (_REPO / _SCHEMA_GUIDE).read_text(encoding="utf-8")
    seen = 0
    for _head, lines in _sections(text):
        if any('mode = "tracker-origin"' in line for line in lines):
            seen += 1
            assert "tracker-entry-drop" in "\n".join(lines), lines[:3]
    assert seen > 0


_DELIVERY_BRIEF = "docs/product/briefs/workspace-registry-retirement-delivery.md"
# AC-0023: the brief's slice 9 names the work after the execution-supervisor cutover.
_SLICE_9_AFTER_CUTOVER = (
    "move the engine rules `dispatch.py` still needs into `work-loop`",
    "shrink `workspace-status` to the repair",
    "remove the legacy registry entries",
    "re-point the spec-status lint's deferral anchors",
    "give the `[authorization.refresh]` and `[authorization.migration]` policy tables a home",
    "record the certification",
    "then delete `workspace.toml`",
)


def _slice_9(text: str) -> str:
    """The brief's slice 9 item, read up to the next heading."""
    start = text.index("9. **Compatibility closure and deletion.**")
    return text[start : text.index("\n## ", start)]


def test_brief_spec_map_lists_this_spec() -> None:
    assert "| `tracker-origin-registration-stop` |" in (_REPO / _DELIVERY_BRIEF).read_text(
        encoding="utf-8"
    )


@pytest.mark.parametrize("phrase", _SLICE_9_AFTER_CUTOVER, ids=lambda p: p[:40])
def test_brief_slice_9_names_the_post_cutover_work(phrase: str) -> None:
    slice_9 = _slice_9((_REPO / _DELIVERY_BRIEF).read_text(encoding="utf-8"))
    after = slice_9[slice_9.index("**After the cutover:**") :]
    assert phrase in _flat_text(after)


# AC-0019: each § Errata holds a 2026-10-30-or-later entry that links RFC-0106 and its literals.
_ERRATA: dict[str, tuple[str, ...]] = {
    "docs/rfc/0106-stop-registering-derivable-work.md": (
        "tracker-entry-drop",
        "tracker_profile",
        "source-authority",
    ),
    "docs/rfc/0083-work-intake-and-artifact-routing.md": ("tracker_profile", "refresh"),
}
_ENTRY_DATE = re.compile(r"^- (?:\*\*)?(\d{4}-\d{2}-\d{2})")


def _errata_entries(text: str) -> list[str]:
    """Each top-level bullet of the § Errata section, with its continuation lines."""
    body = text[text.index("\n## Errata") :].split("\n## ", 2)[1]
    entries: list[str] = []
    for line in body.splitlines():
        if line.startswith("- "):
            entries.append(line)
        elif entries and (line.startswith("  ") or not line.strip()):
            entries[-1] += "\n" + line
    return entries


@pytest.mark.parametrize("rel", sorted(_ERRATA), ids=lambda r: Path(r).stem[:20])
def test_errata_entry_names_the_stop(rel: str) -> None:
    entries = _errata_entries((_REPO / rel).read_text(encoding="utf-8"))
    matching = [
        entry
        for entry in entries
        if (m := _ENTRY_DATE.match(entry)) is not None
        and m.group(1) >= "2026-10-30"
        and "0106-stop-registering-derivable-work.md" in entry
        and all(literal in entry for literal in _ERRATA[rel])
    ]
    assert matching, rel


_LEDGER = "docs/specs/tracker-origin-registration-stop/notes/verification-ledger.md"
_APPROVAL = re.compile(r"eugenelim \(owner\), (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}[+-]\d{2}:\d{2})")
# AC-0020: the file each approved text lands in, and a phrase that pins that text.
_APPROVED_TEXT = {
    "docs/rfc/0106-stop-registering-derivable-work.md": "tracker-entry-drop",
    "docs/rfc/0083-work-intake-and-artifact-routing.md": "lives on the artifact, not in `workspace.toml`",
    _DELIVERY_BRIEF: "lands in parts around the execution-supervisor cutover",
}


def _first_commit_adding(rel: str, phrase: str) -> str:
    """Author date (ISO 8601) of the earliest commit whose diff adds *phrase* to *rel*."""
    out = subprocess.run(
        ["git", "log", "--reverse", "--format=%aI", "-S", phrase, "--", rel],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert out, (rel, phrase)
    return out[0]


@pytest.mark.parametrize("rel", sorted(_APPROVED_TEXT), ids=lambda r: Path(r).stem[:20])
def test_ledger_approval_predates_the_commit_adding_the_text(rel: str) -> None:
    from datetime import datetime

    rows = [
        line
        for line in (_REPO / _LEDGER).read_text(encoding="utf-8").splitlines()
        if line.startswith(f"| `{rel}`")
    ]
    assert len(rows) == 1, rel
    approved = _APPROVAL.search(rows[0])
    assert approved, rows[0]
    committed = _first_commit_adding(rel, _APPROVED_TEXT[rel])
    assert datetime.fromisoformat(approved.group(1)) < datetime.fromisoformat(committed)


_RECORD = "docs/specs/workspace-retirement/retirement-record.md"


def test_retirement_record_names_the_profile_home_and_the_closure() -> None:
    text = (_REPO / _RECORD).read_text(encoding="utf-8")
    disposition = text[text.index("## Disposition") : text.index("## Equivalence")]
    for row in ("source.tracker_profile", "source.tracker_profile.id", "source.tracker_profile.version"):
        line = next(l for l in disposition.splitlines() if l.startswith(f"| `{row}` |"))
        assert "`tracker_profile` table" in line and "`source-authority` record" in line, row
    for stale in (
        "tracker-origin spec entries, and their writers, stay until slice 9",
        "tracker-origin intent and brief entries stay until slice 9",
    ):
        assert stale not in disposition
    closure = text[text.index("## Compatibility closure") : text.index("## Certification")]
    assert "tracker-origin-registration-stop/spec.md" in closure
    assert "tracker-entry-drop" in closure and "verification-ledger.md" in closure
