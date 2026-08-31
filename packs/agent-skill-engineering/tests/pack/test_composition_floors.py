"""Composition-floor portability and subject coverage.

Two properties, deliberately separated. Subject coverage is mechanizable: a
floor either names a subject or it does not. Whether a named subject is
adequately *answered* is a review judgment RFC-0097 D3's Errata assigns to a
named slice reviewer, and no assertion here claims to establish it.
"""

import json
import re
from pathlib import Path

import pytest

PACK = Path(__file__).resolve().parents[2]
CONCEPTS = PACK / "okf" / "agent-skill-engineering-foundation" / "concepts"
COMPILED = PACK / ".apm" / "skills" / "ase-okf-reference" / "references" / "okf" / "concepts"
SUBJECTS = PACK / "tests" / "fixtures" / "composition-floor-subjects.json"

FLOORS = (
    "skills-and-subagents-common-floor",
    "hooks-common-floor",
    "plugin-package-common-floor",
)
SUBJECT_SOURCE_REF = "docs/rfc/0097-agent-skill-engineering.md:D3"

# Identifier CLASSES, not a member list. The set of runtime identifiers is open
# — every release adds more — so a literal list would be defeated by the next
# example. Each class carries its own isolating control below, and the tuple
# length is pinned so a class cannot be dropped silently.
FORBIDDEN_IDENTIFIER_CLASSES = (
    ("runtime-config-directory", re.compile(r"(?<![\w.])\.(?:claude|kiro|gemini|cursor|codex|antigravity)\b")),
    ("runtime-settings-file", re.compile(r"\b(?:settings|hooks|plugin|mcp_config)\.json\b")),
    ("lifecycle-event-token", re.compile(r"\b(?:Pre|Post|User|Session|Stop|Notification)[A-Z][A-Za-z]+\b")),
    ("runtime-environment-variable", re.compile(r"\b[A-Z][A-Z0-9]*_(?:CODE|CLI|AGENT|SUBAGENT)_[A-Z0-9_]+\b")),
    ("runtime-home-path", re.compile(r"~/\.[a-z][\w.-]*")),
)


def _collapse(text: str) -> str:
    """Collapse whitespace before comparing.

    Bodies are hard-wrapped, so a subject phrase spanning a line break is
    present to a reader and absent to a substring test. Comparing raw text here
    would fail on formatting rather than on coverage.
    """
    return " ".join(text.split())


def _body(slug: str) -> str:
    return (CONCEPTS / f"{slug}.md").read_text(encoding="utf-8")


@pytest.fixture(name="subjects")
def _subjects() -> dict:
    return json.loads(SUBJECTS.read_text(encoding="utf-8"))


# ── subject coverage ──────────────────────────────────────────────────────


def test_the_subject_transcription_names_the_authority_it_transcribes(subjects) -> None:
    assert subjects["source_ref"] == SUBJECT_SOURCE_REF
    assert set(subjects["floors"]) == set(FLOORS)
    for slug, floor in subjects["floors"].items():
        assert len(floor["subjects"]) == floor["expected_count"], slug


@pytest.mark.parametrize("slug", FLOORS)
def test_each_floor_names_every_subject_its_authority_assigns(slug, subjects) -> None:
    body = _body(slug)
    floor = subjects["floors"][slug]
    collapsed = _collapse(body)
    missing = [
        name
        for name, phrase in floor["subjects"].items()
        if _collapse(phrase) not in collapsed
    ]
    assert not missing, (slug, missing)


def test_the_delegation_floor_states_its_conservative_default(subjects) -> None:
    floor = subjects["floors"]["skills-and-subagents-common-floor"]
    body = _collapse(_body("skills-and-subagents-common-floor"))
    assert _collapse(floor["conservative_default"]) in body


def test_the_hooks_floor_states_its_degradation_behaviour(subjects) -> None:
    """RFC-0097 D3 requires a hook recommendation to state the degradation when
    a runtime lacks the capability. Without this the floor can pass subject
    coverage while telling a reader nothing about the unsupported case."""
    floor = subjects["floors"]["hooks-common-floor"]
    body = _collapse(_body("hooks-common-floor"))
    assert _collapse(floor["degradation"]) in body


# ── portability ───────────────────────────────────────────────────────────


@pytest.mark.parametrize("slug", FLOORS)
def test_no_floor_names_a_runtime_specific_identifier(slug) -> None:
    body = _body(slug)
    hits = {
        name: match.group(0)
        for name, pattern in FORBIDDEN_IDENTIFIER_CLASSES
        for match in [pattern.search(body)]
        if match
    }
    assert not hits, (slug, hits)


@pytest.mark.parametrize("slug", FLOORS)
def test_the_compiled_floor_copy_is_also_portable(slug) -> None:
    body = (COMPILED / f"{slug}.md").read_text(encoding="utf-8")
    hits = {
        name: match.group(0)
        for name, pattern in FORBIDDEN_IDENTIFIER_CLASSES
        for match in [pattern.search(body)]
        if match
    }
    assert not hits, (slug, hits)


@pytest.mark.parametrize(
    ("name", "specimen"),
    [
        ("runtime-config-directory", "configure it under .claude/hooks and it runs"),
        ("runtime-settings-file", "declare the matcher in settings.json"),
        ("lifecycle-event-token", "register against the PreToolUse event"),
        ("runtime-environment-variable", "raise CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"),
        ("runtime-home-path", "user scope lives at ~/.claude/settings.json"),
    ],
)
def test_each_forbidden_class_fires_on_its_own_specimen(name, specimen) -> None:
    """Class-isolating control. A control asserting only that *some* pattern
    fires is satisfied by one broad member and says nothing about the rest, so
    each class is resolved here by name against a specimen only it matches."""
    matched = [
        cls_name
        for cls_name, pattern in FORBIDDEN_IDENTIFIER_CLASSES
        if pattern.search(specimen)
    ]
    assert name in matched, (name, specimen, matched)


def test_the_forbidden_class_tuple_is_pinned() -> None:
    """Erosion control: dropping a class would silently narrow every scan above."""
    assert len(FORBIDDEN_IDENTIFIER_CLASSES) == 5
    assert len({name for name, _ in FORBIDDEN_IDENTIFIER_CLASSES}) == 5
