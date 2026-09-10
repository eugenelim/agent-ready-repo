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
# Transcribed from RFC-0097 D3: eight capability questions for the delegation
# floor, six distinctions for hooks, seven concerns for plugin packages. Held as
# module literals rather than read from the fixture, so deleting a subject and
# decrementing the fixture's own count together cannot pass.
SUBJECT_COUNTS = {
    "skills-and-subagents-common-floor": 8,
    "hooks-common-floor": 6,
    "plugin-package-common-floor": 7,
}

# Identifier CLASSES, not a member list. The set of runtime identifiers is open
# — every release adds more — so a literal list would be defeated by the next
# example. Each class carries its own isolating control below, and the tuple
# length is pinned so a class cannot be dropped silently.
FORBIDDEN_IDENTIFIER_CLASSES = (
    ("runtime-config-directory", re.compile(r"(?<![\w.])\.(?:claude|kiro|gemini|cursor|codex|antigravity)\b")),
    ("runtime-settings-file", re.compile(r"\b(?:settings|hooks|mcp_config)\.json\b|(?<!\w)\.[a-z][\w.-]*/plugin\.json\b")),
    ("lifecycle-event-token", re.compile(r"\b(?:Pre|Post|User|Session|Stop|Notification)[A-Z][A-Za-z]+\b")),
    ("runtime-environment-variable", re.compile(r"\b[A-Z][A-Z0-9]*_(?:CODE|CLI|AGENT|SUBAGENT)_[A-Z0-9_]+\b")),
    ("runtime-home-path", re.compile(r"~/\.[a-z][\w.-]*")),
)


def _fired(specimen: str) -> list[str]:
    """Return the forbidden identifier classes that match a specimen."""
    return [
        name
        for name, pattern in FORBIDDEN_IDENTIFIER_CLASSES
        if pattern.search(specimen)
    ]


def _collapse(text: str) -> str:
    """Collapse whitespace before comparing.

    Bodies are hard-wrapped, so a subject phrase spanning a line break is
    present to a reader and absent to a substring test. Comparing raw text here
    would fail on formatting rather than on coverage.
    """
    return " ".join(text.split())


def _bodies(root: Path) -> dict[str, str]:
    """Map topic slug to body, built by globbing rather than by joining a slug.

    The pack-test boundary lint cannot statically resolve a path joined from a
    variable, so `root / f"{slug}.md"` reads as an escape above the pack even
    though it never leaves it. Globbing the owning directory is the idiom the
    sibling suites already use and keeps the path provably pack-local.
    """
    return {
        path.stem: path.read_text(encoding="utf-8") for path in root.glob("*.md")
    }


def _body(slug: str) -> str:
    return _bodies(CONCEPTS)[slug]


@pytest.fixture(name="subjects")
def _subjects() -> dict:
    return json.loads(SUBJECTS.read_text(encoding="utf-8"))


# ── subject coverage ──────────────────────────────────────────────────────


def test_the_subject_transcription_names_the_authority_it_transcribes(subjects) -> None:
    assert subjects["source_ref"] == SUBJECT_SOURCE_REF
    assert set(subjects["floors"]) == set(FLOORS)
    for slug, floor in subjects["floors"].items():
        assert floor["expected_count"] == SUBJECT_COUNTS[slug], slug
        assert len(floor["subjects"]) == SUBJECT_COUNTS[slug], slug


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


def test_the_delegation_floor_does_not_require_a_profile_for_unanswered_questions() -> None:
    """An unavailable profile is not the sole resolution route."""
    body = _collapse(_body("skills-and-subagents-common-floor"))
    assert _collapse(
        "Record it as unresolved and consult the runtime profile."
    ) not in body


def test_the_delegation_floor_resolves_an_unanswerable_capability_conservatively() -> None:
    """An unanswerable capability remains with the parent as absent."""
    body = _collapse(_body("skills-and-subagents-common-floor"))
    assert _collapse(
        "A capability question the floor cannot answer and no runtime profile covers "
        "is treated as absent rather than assumed present."
    ) in body
    assert _collapse("The operation stays in the parent.") in body


def test_the_delegation_floor_states_the_outbound_context_boundary() -> None:
    """A worker receives only the context its parent passes."""
    body = _collapse(_body("skills-and-subagents-common-floor"))
    outbound = (
        "The worker receives only the context the parent passes it, not the "
        "parent's conversation."
    )
    assert _collapse(outbound) in body


def test_the_delegation_floor_states_the_inbound_result_boundary() -> None:
    """A parent receives only the worker's declared result."""
    body = _collapse(_body("skills-and-subagents-common-floor"))
    inbound = (
        "The parent receives only the worker's declared result, and the worker's "
        "intermediate reads do not return."
    )
    assert _collapse(inbound) in body


def _reader_facing(slug: str) -> str:
    """Return a floor body with its provenance section removed.

    A provenance block restates its group's clause verbatim, so an assertion
    over the whole file is discharged by that copy and cannot fail on the
    reader-facing placement it claims to guard. These checks are about what a
    reader of the floor is told, which is everything above
    `## Provenance and lifecycle`.
    """
    return _collapse(_body(slug).split("## Provenance and lifecycle")[0])


@pytest.mark.parametrize(
    ("behavior", "expected"),
    [
        pytest.param(
            "root-manifest",
            "The manifest is `plugin.json` at the plugin root.",
            id="root-manifest",
        ),
        pytest.param(
            "path-confinement",
            "Every package-supplied path a client reads or executes resolves "
            "within the filesystem-resolved plugin root.",
            id="path-confinement",
        ),
        pytest.param(
            "recommended-semantic-versioning",
            "`version` uses semantic versioning as a recommendation, and a client "
            "does not reject a plugin for a version string that fails it.",
            id="recommended-semantic-versioning",
        ),
        pytest.param(
            "isolated-failure",
            "A failure isolated to a component type, entry, or process still "
            "leaves independently valid components loadable.",
            id="isolated-failure",
        ),
    ],
)
def test_the_plugin_floor_states_each_portable_core_behavior(
    behavior: str, expected: str
) -> None:
    """Each specification-fixed behavior remains independently detectable."""
    assert _collapse(expected) in _reader_facing("plugin-package-common-floor"), behavior


def test_the_plugin_floor_does_not_defer_manifest_shape() -> None:
    """Neither retired manifest-deferral sentence survives in the floor."""
    body = _collapse(_body("plugin-package-common-floor"))
    forbidden = (
        "leaves the manifest to the runtime profile",
        "manifest shape, install commands, and enablement behavior are "
        "runtime-specific and are deliberately absent here",
    )
    present = [sentence for sentence in forbidden if _collapse(sentence) in body]
    assert not present, present


@pytest.mark.parametrize(
    "concern",
    (
        "installation",
        "discovery location",
        "distribution",
        "enablement",
        "permissions",
        "sandboxing",
        "user experience",
    ),
)
def test_the_plugin_floor_keeps_each_delegated_concern_client_owned(
    concern: str,
) -> None:
    """Each client-delegated concern has its own regression signal."""
    body = _collapse(_body("plugin-package-common-floor"))
    assert _collapse(f"A client owns {concern}.") in body, concern


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
    body = _bodies(COMPILED)[slug]
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
        ("runtime-home-path", "user scope lives at ~/.somewhere/config"),
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
    assert matched == [name], (name, specimen, matched)


def test_the_guard_admits_the_specification_filename() -> None:
    # red at the accepted base: `runtime-settings-file` fires on the bare name
    assert _fired("the manifest is plugin.json at the plugin root") == []


def test_the_guard_flags_a_runtime_owned_manifest() -> None:
    # green before and after: the erosion control on the narrowed class.
    # Membership, not equality: this specimen names a runtime directory too,
    # so `runtime-config-directory` fires on it as well, correctly and
    # irrelevantly to this control. A measured probe of the base predicate
    # returned both class names for it, which is how the first draft of this
    # stub — asserting an exact single-element list — was caught.
    assert "runtime-settings-file" in _fired(
        "its manifest lives at .claude-plugin/plugin.json"
    )


def test_the_forbidden_class_tuple_is_pinned() -> None:
    """Erosion control: dropping a class would silently narrow every scan above."""
    assert len(FORBIDDEN_IDENTIFIER_CLASSES) == 5
    assert len({name for name, _ in FORBIDDEN_IDENTIFIER_CLASSES}) == 5
