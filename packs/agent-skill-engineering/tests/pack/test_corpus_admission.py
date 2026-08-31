"""Corpus admission and recorded retrieval assertions."""

import json
import re
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.skill_spec_lint import RE_ABS_PATH

PACK = Path(__file__).resolve().parents[2]
FIXTURES = PACK / "tests" / "fixtures"
ADMISSION = FIXTURES / "topic-admission.json"
CONCEPTS = PACK / "okf" / "agent-skill-engineering-foundation" / "concepts"
COMPILED_CONCEPTS = (
    PACK / ".apm" / "skills" / "ase-okf-reference" / "references" / "okf" / "concepts"
)
AUTHOR_EVALS = (
    PACK / ".apm" / "skills" / "author-or-update-agent-skill" / "evals" / "evals.json"
)
BEHAVIOR_RESULTS = FIXTURES / "behavior-results.json"
# Line-scoped, and matched per line rather than against the whole file. An
# unanchored `.search()` over the full text with `^...$` and no MULTILINE can
# only match a file whose entire content is one token, so a reviewer name
# embedded in a shipped body passed unnoticed.
ROLE_OR_PLACEHOLDER = re.compile(
    r"^(?:[a-z][a-z0-9]*(?:-[a-z0-9]+)*-(?:reviewer|maintainer)|<[^<>]+>)$"
)
ROLE_OR_PLACEHOLDER_ANYWHERE = re.compile(
    r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+)*-(?:reviewer|maintainer)\b|<[^<>\n]+>"
)
SCOPE_BOUND_STATEMENT = "It is not established beyond that population."
DOCTRINE_CLASSES = {
    "two-runtime-public-contract": ("clause", "runtimes"),
    "single-ecosystem-contract": (
        "clause",
        "ecosystem",
        "sources",
        "version_range",
        "fixture",
    ),
    "repeated-observed-failures": ("mechanism", "failures"),
    "severe-safety-failure": ("boundary", "reproduction"),
    "controlled-measurement": ("setup", "preserved_semantics", "repetitions"),
}
LANGUAGE_SPECIFIC_TOPICS = {
    "python-and-pytest",
    "typescript-node-and-javascript-test-runners",
}
SOURCE_IDENTITY = re.compile(r"\S.*\s+(?:—\s*)?https?://\S+")
ABSOLUTE_URL = re.compile(r"https?://[^\s)\]>]+")
VERSION_LOWER_BOUND = re.compile(r"(?:>=|>)\s*\d")
VERSION_UPPER_BOUND = re.compile(r"(?:<=|<)\s*\d|upper\s+bound\s+open", re.IGNORECASE)

# These strings are deliberately shared, but consumers take only the subset
# their obligation permits: recorded evidence may contain sanctioned internal
# references, while neither recorded evidence nor projections may identify a
# maintainer or host.
HOST_IDENTIFYING_PATTERN_STRINGS = (
    RE_ABS_PATH.pattern,
    r"/var/folders/[A-Za-z0-9_/-]+",
    r"@[A-Za-z0-9-]+|\b[A-Za-z0-9-]+\.local\b",
    r"\b\"?(?:username|user|login)\"?\s*[:=]\s*\"?[^\s,]+",
    r"\b\"?(?:hostname|host)\"?\s*[:=]\s*\"?[^\s,]+",
    r"\b\"?worktree(?:\s+name)?\"?\s*[:=]\s*\"?[^\s,]+",
)
REPOSITORY_REFERENCE_PATTERN_STRINGS = (
    r"\bdocs/(?:specs|rfc|adr)/",
    r"\bAC\d+\b",
    r"\bworkspace\.toml\b",
    r"\b[0-9a-f]{7,40}\b",
    r"\b(?:ADR|RFC)-\d{2,4}\b",
)
HOST_IDENTIFYING_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE) for pattern in HOST_IDENTIFYING_PATTERN_STRINGS
)
PROJECTED_REFERENCE_PATTERNS = tuple(
    re.compile(pattern) for pattern in REPOSITORY_REFERENCE_PATTERN_STRINGS
)


def _admitted_topics_from_compiled_tree() -> set[str]:
    """Return the admitted topic ids, read from the compiled bundle root.

    The root is iterated non-recursively and `index.md` is dropped by name, so
    the declared-unpopulated record -- authored in a subdirectory -- is excluded
    by where it lives, never by a marker field, section shape, or name pattern a
    topic body could reproduce.
    """
    return {
        path.stem
        for path in COMPILED_CONCEPTS.glob("*.md")
        if path.is_file() and path.stem != "index"
    }


UNPOPULATED_RECORD = COMPILED_CONCEPTS / "declared-absent" / "unpopulated-leaves.md"


def _unpopulated_leaves_from_compiled_record() -> set[str]:
    """Return the leaves the register declares absent.

    The register is identified by its exact compiled path -- one record, at one
    known location -- never by a marker field, section shape, or name pattern a
    topic body could reproduce. A body that copied its shape elsewhere would
    therefore not be read as the register, and would still be iterated as a
    concept by the walks that cover the tree.

    The unpopulated side is derived from the leaf names the register records,
    not from whatever the admitted-set walk happened to exclude, so a document
    cannot both escape iteration and satisfy the partition.
    """
    text = UNPOPULATED_RECORD.read_text(encoding="utf-8")
    leaves = {
        line[3:].strip()
        for line in text.split("\n")
        if line.startswith("## ")
    }
    assert leaves, "the register declares no leaves"
    return leaves


def _assert_source_is_attributable(source: dict[str, object]) -> None:
    """Every cited source names itself, when it was read, and its version state."""
    assert source.get("identity"), source
    assert source.get("retrieved_at"), source
    exposed = source.get("version") or source.get("last_updated")
    assert exposed or source.get("version_state") == "none exposed", source


def _assert_doctrine_group_shape(topic: dict[str, object], group: dict[str, object]) -> None:
    """Assert the promotion-class predicates that doctrine groups must satisfy."""
    promotion_class = group["promotion_class"]
    assert promotion_class in DOCTRINE_CLASSES, promotion_class
    for field in DOCTRINE_CLASSES[promotion_class]:
        assert group.get(field), (promotion_class, field)
    if promotion_class == "two-runtime-public-contract":
        assert len({runtime["runtime"] for runtime in group["runtimes"]}) >= 2
        for runtime in group["runtimes"]:
            assert runtime["clause"] == group["clause"]
    if promotion_class == "single-ecosystem-contract":
        assert "eligibility" not in group, group["name"]
        assert topic["topic"] in LANGUAGE_SPECIFIC_TOPICS, topic["topic"]
        assert VERSION_LOWER_BOUND.search(group["version_range"]), group["version_range"]
        assert VERSION_UPPER_BOUND.search(group["version_range"]), group["version_range"]
    if promotion_class == "repeated-observed-failures":
        assert len(group["failures"]) >= 2
        assert {failure["mechanism"] for failure in group["failures"]} == {
            group["mechanism"]
        }
    if promotion_class == "controlled-measurement":
        assert int(group["repetitions"]) >= 2

    sources = group.get("sources", ())
    if promotion_class in {
        "two-runtime-public-contract",
        "single-ecosystem-contract",
    }:
        assert sources, (promotion_class, group["name"])
    if promotion_class == "repeated-observed-failures":
        assert not sources, group["name"]
    for source in sources:
        _assert_source_is_attributable(source)
        assert SOURCE_IDENTITY.fullmatch(source["identity"]), source["identity"]


def _provenance_section(body: str) -> str:
    """Return the provenance section without a following top-level section."""
    match = re.search(
        r"^## Provenance and lifecycle\s*$([\s\S]*?)(?=^## |\Z)",
        body,
        re.MULTILINE,
    )
    assert match is not None, "missing provenance and lifecycle section"
    return match.group(1)


def _group_provenance_block(body: str, group_name: str) -> str:
    """Return one doctrine group's labelled provenance block."""
    section = _provenance_section(body)
    label = re.compile(rf"^\*\*{re.escape(group_name)}:\*\*\s*$", re.MULTILINE)
    labels = list(label.finditer(section))
    assert len(labels) == 1, (group_name, len(labels))
    following = re.search(r"^\*\*[^*\n]+:\*\*\s*$", section[labels[0].end() :], re.MULTILINE)
    end = labels[0].end() + following.start() if following else len(section)
    return section[labels[0].end() : end]


def _source_version_state(source: dict[str, object]) -> object:
    """Return the source's required exposed-version projection."""
    return source.get("version") or source.get("last_updated") or source["version_state"]


def _assert_doctrine_projection(topic: dict[str, object], group: dict[str, object], body: str) -> None:
    """Assert record-to-body and body-to-record parity for one doctrine group."""
    block = _group_provenance_block(body, group["name"])
    claim = group["clause"] if "clause" in group else group["mechanism"]
    for value in (claim, topic["last_verified"], group["revalidation_trigger"]):
        assert _collapse(str(value)) in _collapse(block), (group["name"], value)
    if group["promotion_class"] == "single-ecosystem-contract":
        for field in ("ecosystem", "version_range"):
            assert _collapse(str(group[field])) in _collapse(block), (group["name"], field)
        assert group["fixture"] not in body, (group["name"], "fixture")
    source_urls: set[str] = set()
    for source in group.get("sources", ()):
        identity = source["identity"]
        assert _collapse(str(identity)) in _collapse(block), (group["name"], identity)
        assert str(source["retrieved_at"]) in block, (group["name"], "retrieved_at")
        assert str(_source_version_state(source)) in block, (group["name"], "version state")
        source_urls.update(ABSOLUTE_URL.findall(str(identity)))
    assert set(ABSOLUTE_URL.findall(block)) <= source_urls, group["name"]


def _assert_doctrine_projections(
    topic: dict[str, object], group: dict[str, object], authored: str, compiled: str
) -> None:
    """Require the doctrine record to project independently to both body forms."""
    _assert_doctrine_projection(topic, group, authored)
    _assert_doctrine_projection(topic, group, compiled)


def _assert_no_patterns(text: str, patterns: tuple[re.Pattern[str], ...]) -> None:
    """Reject the first forbidden structural form in text."""
    for pattern in patterns:
        assert pattern.search(text) is None, pattern.pattern


def _assert_reviewer_is_not_projected(topic: dict[str, object], bodies: tuple[str, str]) -> None:
    """Keep reviewer identities and placeholders out of both shipped projections."""
    for body, label in zip(bodies, ("authored", "compiled"), strict=True):
        hit = ROLE_OR_PLACEHOLDER_ANYWHERE.search(body)
        assert hit is None, (topic["topic"], label, hit.group(0))
        assert topic["reviewer"] not in body, topic["topic"]


def test_topology_transcription_is_complete() -> None:
    """RFC-0097 D3's topology remains a complete, sourced enumeration."""
    leaves = json.loads(
        (FIXTURES / "topology-leaves.json").read_text(encoding="utf-8")
    )
    names = leaves["leaves"]

    assert leaves["source_ref"] == "docs/rfc/0097-agent-skill-engineering.md:D3"
    assert leaves["expected_count"] == 36
    assert isinstance(names, list)
    assert len(names) == 36
    assert len(set(names)) == 36


def test_foundation_pins_hold_the_shipped_cases() -> None:
    """Every inherited pin reproduces the current measurement.

    Not "reproduces the pre-change value": two of the 24 pins were re-taken
    under recorded owner authority when this slice admitted the language topics,
    and the slice `qa.md` names both with their prior and current values. The
    fixture is therefore not an untouched baseline, and reading it as one is how
    a future re-record passes unnoticed.
    """
    pins = json.loads(
        (FIXTURES / "foundation-retrieval-pins.json").read_text(encoding="utf-8")
    )
    results = json.loads(
        (FIXTURES / "router-results.json").read_text(encoding="utf-8")
    )
    recorded = pins["pins"]
    measured = results["results"]

    assert isinstance(recorded, list)
    assert isinstance(measured, list)
    assert len(recorded) == 24
    assert all("measured_topics" in pin for pin in recorded)

    # The corpus grows, so the result set is a superset of the pinned
    # foundation cases. Every pinned case must still be measured and must agree
    # with the pinned value as it now stands -- a case that quietly disappeared
    # from the fixture would otherwise satisfy a subset check. This compares the
    # pins to the current measurement, not to any earlier one, so it cannot by
    # itself detect an unrecorded re-take; the naming record is that control.
    actual = {result["id"]: result["actual_topics"] for result in measured}
    assert {pin["id"] for pin in recorded} <= set(actual)
    assert {pin["id"]: pin["measured_topics"] for pin in recorded} == {
        pin["id"]: actual[pin["id"]] for pin in recorded
    }


def test_every_claim_group_declares_a_basis_and_its_fields() -> None:
    """Each admitted group has the evidence shape its declared basis requires."""

    record = json.loads(ADMISSION.read_text(encoding="utf-8"))
    for topic in record["topics"]:
        assert ROLE_OR_PLACEHOLDER.fullmatch(topic["reviewer"])
        assert topic["last_verified"]
        for group in topic["claim_groups"]:
            assert group["basis"] in {"doctrine", "observed-practice"}
            assert group["revalidation_trigger"]
            if group["basis"] == "observed-practice":
                observations = group["observations"]
                assert len(observations) >= 2
                assert len({Path(path).parts[1] for path in observations}) >= 2
                assert SCOPE_BOUND_STATEMENT in group["applicability_limit"]
                # An observed-practice group states a limit, never a class.
                assert "promotion_class" not in group, group["name"]
            else:
                _assert_doctrine_group_shape(topic, group)


def _collapse(text: str) -> str:
    """Return *text* with every whitespace run reduced to one space."""
    return " ".join(text.split())


def _doctrine_topic(*groups: dict[str, object]) -> dict[str, object]:
    """Build a language-topic record that can exercise doctrine before T3."""
    return {
        "topic": "python-and-pytest",
        "last_verified": "2026-08-30",
        "claim_groups": list(groups),
    }


def _single_ecosystem_group(*, sources: tuple[dict[str, object], ...] | None = None) -> dict[str, object]:
    """Build the smallest valid single-ecosystem doctrine group."""
    return {
        "name": "pytest contract",
        "basis": "doctrine",
        "promotion_class": "single-ecosystem-contract",
        "clause": "Discovery follows the configured root.",
        "ecosystem": "pytest",
        "sources": list(
            sources
            if sources is not None
            else (
                {
                    "identity": "pytest documentation — https://docs.pytest.org/en/stable/",
                    "retrieved_at": "2026-08-29",
                    "version_state": "none exposed",
                },
            )
        ),
        "version_range": ">= 9.1.1; upper bound open",
        "fixture": "pytest-suite",
        "revalidation_trigger": "Revalidate when pytest changes discovery.",
    }


def _doctrine_body(topic: dict[str, object], *groups: dict[str, object]) -> str:
    """Render the record fields doctrine-side parity requires in a test body."""
    blocks = []
    for group in groups:
        lines = [
            f"**{group['name']}:**",
            str(group["clause"] if "clause" in group else group["mechanism"]),
            str(topic["last_verified"]),
            str(group["revalidation_trigger"]),
        ]
        if group["promotion_class"] == "single-ecosystem-contract":
            lines.extend((str(group["ecosystem"]), str(group["version_range"])))
        for source in group.get("sources", ()):
            lines.extend(
                (
                    str(source["identity"]),
                    str(source["retrieved_at"]),
                    str(_source_version_state(source)),
                )
            )
        blocks.append("\n".join(lines))
    return "## Provenance and lifecycle\n\n" + "\n\n".join(blocks) + "\n"


def test_doctrine_group_source_parity_holds_in_both_projections() -> None:
    """AC6: a constructed doctrine group projects all required source fields."""
    group = _single_ecosystem_group()
    topic = _doctrine_topic(group)
    body = _doctrine_body(topic, group)

    _assert_doctrine_group_shape(topic, group)
    _assert_doctrine_projections(topic, group, body, f"{body}\n")
    assert group["fixture"] not in body
    with pytest.raises(AssertionError):
        _assert_doctrine_projections(topic, group, body, f"{body}{group['fixture']}")


def test_doctrine_parity_rejects_a_source_missing_from_one_projection() -> None:
    """AC6: a projection cannot omit a cited source's identity, date, or state."""
    group = _single_ecosystem_group()
    topic = _doctrine_topic(group)
    body = _doctrine_body(topic, group)

    _assert_doctrine_projections(topic, group, body, f"{body}\n")
    for projected_field in (
        "pytest documentation — https://docs.pytest.org/en/stable/\n",
        "2026-08-29\n",
        "none exposed\n",
    ):
        with pytest.raises(AssertionError):
            _assert_doctrine_projections(
                topic, group, body, body.replace(projected_field, "", 1)
            )
        with pytest.raises(AssertionError):
            _assert_doctrine_projections(
                topic, group, body.replace(projected_field, "", 1), body
            )
    for source, state_field in (
        (
            {
                "identity": "Versioned documentation — https://example.test/versioned",
                "retrieved_at": "2026-08-29",
                "version": "9.1.1",
            },
            "version",
        ),
        (
            {
                "identity": "Dated documentation — https://example.test/dated",
                "retrieved_at": "2026-08-29",
                "last_updated": "2026-08-28",
            },
            "last_updated",
        ),
    ):
        dated_group = _single_ecosystem_group(sources=(source,))
        dated_body = _doctrine_body(_doctrine_topic(dated_group), dated_group)
        for bodies in (
            (dated_body.replace(str(source[state_field]), "", 1), dated_body),
            (dated_body, dated_body.replace(str(source[state_field]), "", 1)),
        ):
            with pytest.raises(AssertionError):
                _assert_doctrine_projections(
                    _doctrine_topic(dated_group), dated_group, *bodies
                )


def test_public_contract_group_cites_at_least_one_attributable_source() -> None:
    """AC6: a public-contract class cannot satisfy its source floor vacuously."""
    single_ecosystem = _single_ecosystem_group(sources=())
    two_runtime = {
        "name": "two runtime contract",
        "basis": "doctrine",
        "promotion_class": "two-runtime-public-contract",
        "clause": "Both runners honour the declared dependency.",
        "runtimes": [
            {"runtime": "runner-a", "clause": "Both runners honour the declared dependency."},
            {"runtime": "runner-b", "clause": "Both runners honour the declared dependency."},
        ],
        "sources": [],
        "revalidation_trigger": "Revalidate when either runner changes.",
    }

    for group in (single_ecosystem, two_runtime):
        with pytest.raises(AssertionError):
            _assert_doctrine_group_shape(_doctrine_topic(group), group)

    unknown_class = _single_ecosystem_group()
    unknown_class["promotion_class"] = "unapproved-class"
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(unknown_class), unknown_class)

    clause_mismatch = {**two_runtime, "sources": [_single_ecosystem_group()["sources"][0]]}
    clause_mismatch["runtimes"] = [
        *two_runtime["runtimes"][:-1],
        {"runtime": "runner-b", "clause": "A different clause."},
    ]
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(clause_mismatch), clause_mismatch)

    unattributable = {**two_runtime, "sources": [{"identity": "Runner docs — https://example.test/"}]}
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(unattributable), unattributable)

    ineligible = _single_ecosystem_group()
    ineligible_topic = {**_doctrine_topic(ineligible), "topic": "pack-and-ci-critical-paths"}
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(ineligible_topic, ineligible)

    self_eligible = _single_ecosystem_group()
    self_eligible["eligibility"] = "language-specific"
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(self_eligible), self_eligible)

    bare_version = _single_ecosystem_group()
    bare_version["version_range"] = "9.1.1"
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(bare_version), bare_version)

    lower_only = _single_ecosystem_group()
    lower_only["version_range"] = ">= 9.1.1"
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(lower_only), lower_only)

    upper_only = _single_ecosystem_group()
    upper_only["version_range"] = "< 10"
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(upper_only), upper_only)

    for field in ("ecosystem", "fixture"):
        missing_field = _single_ecosystem_group()
        missing_field.pop(field)
        with pytest.raises(AssertionError):
            _assert_doctrine_group_shape(_doctrine_topic(missing_field), missing_field)


def test_public_contract_group_needs_two_distinct_runtimes() -> None:
    """AC6: two entries naming one runtime are one runtime, not two.

    Added because mutating the distinct-runtime floor from `>= 2` to `>= 0` left
    the suite green: every constructed group happened to carry two distinct
    names, so nothing exercised the floor. A clause stated twice by one project
    is the shape the class exists to exclude.
    """
    clause = "Both runners honour the declared dependency."
    group = {
        "name": "one runtime wearing two hats",
        "basis": "doctrine",
        "promotion_class": "two-runtime-public-contract",
        "clause": clause,
        "runtimes": [
            {"runtime": "runner-a", "clause": clause},
            {"runtime": "runner-a", "clause": clause},
        ],
        "sources": [_single_ecosystem_group()["sources"][0]],
        "revalidation_trigger": "Revalidate when either runner changes.",
    }

    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(group), group)


def test_cited_source_states_its_version_or_declares_none_exposed() -> None:
    """AC6: attributability is not satisfied by a source that says nothing.

    Added because mutating the attributability assertion left the suite green:
    every constructed source already carried `version_state`, so the branch that
    rejects a silent source never ran. A source with no version, no last-updated
    date, and no explicit `none exposed` records when it was read but not what
    was read, which is the gap the inherited rule closes.
    """
    silent = {
        "identity": "pytest documentation — https://docs.pytest.org/en/stable/",
        "retrieved_at": "2026-08-29",
    }
    group = _single_ecosystem_group(sources=(silent,))

    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(group), group)

    for stated in ({"version": "9.1.1"}, {"last_updated": "2026-06-19"},
                   {"version_state": "none exposed"}):
        ok = _single_ecosystem_group(sources=({**silent, **stated},))
        _assert_doctrine_group_shape(_doctrine_topic(ok), ok)


def test_repeated_failure_group_cites_no_external_source() -> None:
    """AC6: repeated failures keep internal evidence in the non-projected record."""
    source = {
        "identity": "External documentation — https://example.test/contract",
        "retrieved_at": "2026-08-30",
        "version_state": "none exposed",
    }
    group = {
        "name": "internal failure pattern",
        "basis": "doctrine",
        "promotion_class": "repeated-observed-failures",
        "mechanism": "The same ownership gap recurred.",
        "failures": [
            {"mechanism": "The same ownership gap recurred."},
            {"mechanism": "The same ownership gap recurred."},
        ],
        "sources": [source],
        "revalidation_trigger": "Revalidate after another independent failure.",
    }
    topic = _doctrine_topic(group)

    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(topic, group)

    group["sources"] = []
    group["failures"][1]["mechanism"] = "A different mechanism."
    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(topic, group)


def test_each_doctrine_group_has_its_own_labelled_provenance_block() -> None:
    """AC6: sibling groups cannot share a labelled provenance block."""
    first = _single_ecosystem_group()
    second = _single_ecosystem_group()
    second["name"] = "pytest lifecycle"
    topic = _doctrine_topic(first, second)
    body = _doctrine_body(topic, first)

    assert _group_provenance_block(_doctrine_body(topic, first, second), first["name"])
    with pytest.raises(AssertionError):
        _group_provenance_block(body, second["name"])


def test_body_carries_no_external_reference_the_group_record_does_not_cite() -> None:
    """AC6: a non-citing group cannot borrow a sibling group's URL."""
    citing = _single_ecosystem_group()
    internal = {
        "name": "internal failure pattern",
        "basis": "doctrine",
        "promotion_class": "repeated-observed-failures",
        "mechanism": "The same ownership gap recurred.",
        "failures": [
            {"mechanism": "The same ownership gap recurred."},
            {"mechanism": "The same ownership gap recurred."},
        ],
        "sources": [],
        "revalidation_trigger": "Revalidate after another independent failure.",
    }
    topic = _doctrine_topic(citing, internal)
    body = _doctrine_body(topic, citing, internal).replace(
        "Revalidate after another independent failure.",
        "Revalidate after another independent failure. https://docs.pytest.org/en/stable/",
    )

    with pytest.raises(AssertionError):
        _assert_doctrine_projection(topic, internal, body)


def test_every_doctrine_group_projects_its_verification_date_and_trigger() -> None:
    """AC6: even a non-citing group projects its record-backed lifecycle basis."""
    group = {
        "name": "internal failure pattern",
        "basis": "doctrine",
        "promotion_class": "repeated-observed-failures",
        "mechanism": "The same ownership gap recurred.",
        "failures": [
            {"mechanism": "The same ownership gap recurred."},
            {"mechanism": "The same ownership gap recurred."},
        ],
        "sources": [],
        "revalidation_trigger": "Revalidate after another independent failure.",
    }
    topic = _doctrine_topic(group)
    body = _doctrine_body(topic, group)

    _assert_doctrine_projection(topic, group, body)
    with pytest.raises(AssertionError):
        _assert_doctrine_projection(topic, group, body.replace(topic["last_verified"], ""))
    with pytest.raises(AssertionError):
        _assert_doctrine_projection(
            topic, group, body.replace(group["revalidation_trigger"], "")
        )


def test_doctrine_parity_rejects_a_repository_internal_source_identity() -> None:
    """AC6: both projected roots reject internal references and source identities."""
    projected_files = [
        *CONCEPTS.rglob("*.md"),
        *COMPILED_CONCEPTS.rglob("*.md"),
    ]
    assert projected_files
    for path in projected_files:
        _assert_no_patterns(
            path.read_text(encoding="utf-8"),
            HOST_IDENTIFYING_PATTERNS + PROJECTED_REFERENCE_PATTERNS,
        )

    fixture_files = [path for path in FIXTURES.rglob("*") if path.is_file()]
    assert fixture_files
    for path in fixture_files:
        _assert_no_patterns(path.read_text(encoding="utf-8"), HOST_IDENTIFYING_PATTERNS)
    for seeded in (
        "/Users/recorded-author/worktree",
        '"username": "recorded-author"',
        '"hostname": "recorded-host"',
        '"worktree": "recorded-worktree"',
    ):
        with pytest.raises(AssertionError):
            _assert_no_patterns(seeded, HOST_IDENTIFYING_PATTERNS)
    group = _single_ecosystem_group(
        sources=(
            {
                "identity": "deadbeef",
                "retrieved_at": "2026-08-30",
                "version_state": "none exposed",
            },
        )
    )

    with pytest.raises(AssertionError):
        _assert_doctrine_group_shape(_doctrine_topic(group), group)


def test_recorded_evidence_fields_carry_no_host_identifying_data() -> None:
    """AC3: recorded and authored evidence reject structural host identifiers."""

    # Every root the plan extends this test over, each with its own floor. One
    # combined floor let a whole root contribute zero files without failing, and
    # the eval declarations and their payloads were reached by no host scan at
    # all -- clean today, so the gap was prospective rather than a live leak.
    roots = {
        "admission record": [ADMISSION],
        "authored concepts": sorted(CONCEPTS.rglob("*.md")),
        "compiled concepts": sorted(COMPILED_CONCEPTS.rglob("*.md")),
        "recorded fixtures": sorted(
            path for path in FIXTURES.rglob("*") if path.is_file()
        ),
        "eval declarations and payloads": sorted(
            path
            for path in (PACK / ".apm" / "skills").rglob("evals/**/*")
            if path.is_file()
        ),
    }
    FLOORS = {
        "admission record": 1,
        "authored concepts": 12,
        "compiled concepts": 12,
        "recorded fixtures": 8,
        "eval declarations and payloads": 8,
    }
    # Each root's expected parent, so a floor cannot be satisfied by files from
    # somewhere else. A count alone cannot see a repointed root: aiming the eval
    # walk at the concepts tree met its floor while the declared root went
    # unscanned.
    PARENTS = {
        "admission record": FIXTURES,
        "authored concepts": CONCEPTS,
        "compiled concepts": COMPILED_CONCEPTS,
        "recorded fixtures": FIXTURES,
        "eval declarations and payloads": PACK / ".apm" / "skills",
    }
    # The root *set* is pinned, not just each root's floor and parent. Three
    # empty dicts satisfy a three-way set equality, and so do three consistently
    # narrowed ones -- which would put back the exact defect this scan was
    # widened to fix, a declared root reached by nothing.
    SCANNED_ROOTS = frozenset(
        {
            "admission record",
            "authored concepts",
            "compiled concepts",
            "recorded fixtures",
            "eval declarations and payloads",
        }
    )
    assert set(roots) == set(FLOORS) == set(PARENTS) == SCANNED_ROOTS
    for name, paths in roots.items():
        assert len(paths) >= FLOORS[name], (name, len(paths))
        for path in paths:
            assert PARENTS[name] in path.parents or PARENTS[name] == path.parent, (
                name,
                str(path),
            )
        for path in paths:
            _assert_no_patterns(
                path.read_text(encoding="utf-8", errors="strict"),
                HOST_IDENTIFYING_PATTERNS,
            )
    for seeded in (
        "/opt/foreign-user/project",
        "/var/folders/foreign-id/T/work",
        "worker@foreign-host",
        "foreign-host.local",
    ):
        with pytest.raises(AssertionError):
            _assert_no_patterns(seeded, HOST_IDENTIFYING_PATTERNS)


def test_reviewer_identity_is_rejected_from_both_projections() -> None:
    """T2 mutation proof: neither reviewer scan can move into the doctrine arm."""
    topic = {"topic": "constructed-topic", "reviewer": "recorded reviewer value"}
    clean = "## Provenance and lifecycle\n"

    for leaked in ("draft-reviewer", topic["reviewer"]):
        for bodies in ((leaked, clean), (clean, leaked)):
            with pytest.raises(AssertionError):
                _assert_reviewer_is_not_projected(topic, bodies)


def test_shipped_body_matches_the_admission_record() -> None:
    """Observed-practice limits remain portable and equal in both projections."""

    record = json.loads(ADMISSION.read_text(encoding="utf-8"))
    # Resolve by globbing each root and indexing by stem rather than joining a
    # fixture-supplied name onto a path. The join is in-pack either way, but a
    # variable operand cannot be shown to be, and the boundary linter is right
    # that the form does not prove it.
    authored_by_stem = {
        path.stem: path for path in CONCEPTS.glob("*.md") if path.is_file()
    }
    compiled_by_stem = {
        path.stem: path for path in COMPILED_CONCEPTS.glob("*.md") if path.is_file()
    }
    for topic in record["topics"]:
        name = topic["topic"]
        assert name in authored_by_stem, name
        assert name in compiled_by_stem, name
        authored = authored_by_stem[name].read_text(encoding="utf-8")
        compiled = compiled_by_stem[name].read_text(encoding="utf-8")
        _assert_reviewer_is_not_projected(topic, (authored, compiled))
        for group in topic["claim_groups"]:
            if group["basis"] != "observed-practice":
                _assert_doctrine_group_shape(topic, group)
                _assert_doctrine_projections(topic, group, authored, compiled)
                continue
            limit = group["applicability_limit"]
            assert SCOPE_BOUND_STATEMENT in limit
            # Both projections wrap prose; the claim is about the text, not its
            # line breaks, so compare with whitespace collapsed on both sides.
            assert _collapse(limit) in _collapse(authored)
            assert _collapse(limit) in _collapse(compiled)
            for repository_marker in ("packs/", ".apm/skills/", "agent-skill-engineering"):
                assert repository_marker not in limit


def test_admitted_topics_are_topology_leaves() -> None:
    """Nothing enters the corpus that the governing taxonomy does not name."""
    leaves = set(
        json.loads((FIXTURES / "topology-leaves.json").read_text(encoding="utf-8"))["leaves"]
    )
    admitted = _admitted_topics_from_compiled_tree()

    assert admitted, "the compiled bundle root carries no admitted topic"
    assert admitted <= leaves, sorted(admitted - leaves)


def test_admitted_topics_are_measurably_distinguishable() -> None:
    """Each admitted topic is selected alone by at least two measured prompts."""
    results = json.loads(
        (FIXTURES / "router-results.json").read_text(encoding="utf-8")
    )["results"]
    admitted = _admitted_topics_from_compiled_tree()
    recorded = {topic["topic"] for topic in json.loads(
        ADMISSION.read_text(encoding="utf-8")
    )["topics"]}

    # A topic cannot be admitted on a declaration alone: the fixture must also
    # hold a measured outcome for it, so an unmeasured claim cannot pass.
    assert admitted <= recorded, sorted(admitted - recorded)
    for topic in sorted(admitted):
        exclusive = [r for r in results if r["actual_topics"] == [topic]]
        assert len(exclusive) >= 2, (topic, len(exclusive))


# Class-isolating positive controls. The negative scans above pass because both
# trees are clean, and without these that same green would follow from a pattern
# that matches nothing -- which was true of every member of
# REPOSITORY_REFERENCE_PATTERN_STRINGS: substituting an empty tuple reddened
# nothing.
#
# Isolating matters as much as seeding. `_assert_no_patterns` raises on the first
# member that matches, so a control asserting "the tuple as a whole fires" is
# satisfied by one broad member and says nothing about the rest -- which is how
# `/var/folders/...` sat fully shadowed by `RE_ABS_PATH`'s `/var/` branch, and
# how the `<placeholder>` alternative had no control at all. Each case below
# names the member it exercises and asserts *that* pattern fires.
REPOSITORY_REFERENCE_CONTROLS = (
    (r"\bdocs/(?:specs|rfc|adr)/", "see docs/specs/some-other-slice/spec.md"),
    (r"\bAC\d+\b", "this follows from AC7 of another spec"),
    (r"\bworkspace\.toml\b", "registered in workspace.toml elsewhere"),
    (r"\b[0-9a-f]{7,40}\b", "introduced in 4f2c9ab"),
    (r"\b(?:ADR|RFC)-\d{2,4}\b", "governed by RFC-0097"),
)
# Isolation comes from the by-name lookup in each case body, not from seed
# uniqueness. An earlier comment here claimed this seed was chosen so no other
# member could match it, which is false -- `RE_ABS_PATH`'s `/var/` branch matches
# it too. Resolving the compiled pattern by its own string makes shadowing
# structurally impossible and seed uniqueness unnecessary; reverting to an
# `any(...)` form on the belief that the seed is doing the work would silently
# restore the shadowing defect.
HOST_IDENTIFYING_CONTROLS = (
    (r"/var/folders/[A-Za-z0-9_/-]+", "/var/folders/zz9foreign/T/scratch"),
    (r"@[A-Za-z0-9-]+|\b[A-Za-z0-9-]+\.local\b", "someone@example-host"),
    (r"\b\"?(?:username|user|login)\"?\s*[:=]\s*\"?[^\s,]+", "username: not-a-real-person"),
    (r"\b\"?(?:hostname|host)\"?\s*[:=]\s*\"?[^\s,]+", "hostname: not-a-real-box"),
    (r"\b\"?worktree(?:\s+name)?\"?\s*[:=]\s*\"?[^\s,]+", "worktree: some-other-tree"),
)


def test_every_scanned_pattern_has_an_isolating_control() -> None:
    """One control per pattern member, pinned outside the parametrized cases.

    The coverage equality inside those cases only runs if a case exists, so
    dropping a control row removed a pattern's control silently, and emptying a
    control tuple gave pytest an empty parameter set -- reported as skipped, exit
    zero, the whole control gone from a green run. Third level of the same
    defect: the guards were pinned, then their subject sets, and these are the
    subject set of those pins.
    """
    assert {pattern for pattern, _ in REPOSITORY_REFERENCE_CONTROLS} == set(
        REPOSITORY_REFERENCE_PATTERN_STRINGS
    )
    assert {pattern for pattern, _ in HOST_IDENTIFYING_CONTROLS} == set(
        HOST_IDENTIFYING_PATTERN_STRINGS
    ) - {RE_ABS_PATH.pattern}
    assert len(REPOSITORY_REFERENCE_CONTROLS) == 5
    assert len(HOST_IDENTIFYING_CONTROLS) == 5
    assert len(PLACEHOLDER_CONTROLS) == 3


@pytest.mark.parametrize("pattern_string, seeded", REPOSITORY_REFERENCE_CONTROLS)
def test_each_repository_reference_pattern_matches_a_foreign_example(
    pattern_string: str, seeded: str
) -> None:
    """Each projected-reference pattern fires on its own seeded example.

    Exercised through the compiled tuple the scan actually consumes, not through
    the source strings. Compiling the string here would leave the consumed tuple
    free to be emptied while these cases still passed -- the first version of this
    control did exactly that.
    """
    assert pattern_string in REPOSITORY_REFERENCE_PATTERN_STRINGS, pattern_string
    compiled = {pattern.pattern: pattern for pattern in PROJECTED_REFERENCE_PATTERNS}
    assert set(compiled) == set(REPOSITORY_REFERENCE_PATTERN_STRINGS), sorted(compiled)
    assert compiled[pattern_string].search(seeded), (pattern_string, seeded)


@pytest.mark.parametrize("pattern_string, seeded", HOST_IDENTIFYING_CONTROLS)
def test_each_host_identifying_pattern_matches_a_foreign_example(
    pattern_string: str, seeded: str
) -> None:
    """Each host pattern fires on its own seeded example.

    Not "an example only it can match" -- several seeds are matched by more than
    one member. The case resolves its pattern by name below, so shadowing cannot
    make it pass on the wrong member.

    `RE_ABS_PATH` is excluded because its local control is the
    `/opt/foreign-user/project` seed in the negative scan, the one string only it
    matches, and its own positive control lives with the boundary scan that owns
    the pattern.
    """
    assert pattern_string in HOST_IDENTIFYING_PATTERN_STRINGS, pattern_string
    compiled = {pattern.pattern: pattern for pattern in HOST_IDENTIFYING_PATTERNS}
    assert set(compiled) == set(HOST_IDENTIFYING_PATTERN_STRINGS), sorted(compiled)
    assert compiled[pattern_string].search(seeded), (pattern_string, seeded)


# Module level, not inline in the decorator: an inline tuple is pinned by nothing,
# and emptying it gives pytest an empty parameter set -- reported as skipped, exit
# zero -- so the control disappears from a green run. Exactly the defect the
# coverage test below describes, on the one control tuple it did not reach.
PLACEHOLDER_CONTROLS = ("<placeholder-reviewer>", "<some-role>", "<redacted>")


@pytest.mark.parametrize("seeded", PLACEHOLDER_CONTROLS)
def test_the_placeholder_alternative_matches_a_bracketed_token(seeded: str) -> None:
    """The `<...>` branch of the reviewer matcher has its own control.

    Both existing reviewer controls are absorbed by the role-token branch, so
    this alternative was carried by nothing and could have been deleted silently.
    """
    assert ROLE_OR_PLACEHOLDER_ANYWHERE.search(seeded), seeded


def test_every_leaf_is_in_exactly_one_set() -> None:
    """Each taxonomy leaf is admitted or declared absent -- never both, never neither."""
    leaves = json.loads(
        (FIXTURES / "topology-leaves.json").read_text(encoding="utf-8")
    )["leaves"]
    admitted = _admitted_topics_from_compiled_tree()
    unpopulated = _unpopulated_leaves_from_compiled_record()

    assert UNPOPULATED_RECORD.stem not in admitted
    for leaf in leaves:
        assert (leaf in admitted) ^ (leaf in unpopulated), leaf
    # Neither set may carry a name the taxonomy does not have.
    assert admitted <= set(leaves), sorted(admitted - set(leaves))
    assert unpopulated <= set(leaves), sorted(unpopulated - set(leaves))


def _declared_eval_ids() -> set[str]:
    return {
        case["id"]
        for case in json.loads(AUTHOR_EVALS.read_text(encoding="utf-8"))["evals"]
    }


def _graded_eval_ids() -> set[str]:
    return {
        result["eval_id"]
        for result in json.loads(BEHAVIOR_RESULTS.read_text(encoding="utf-8"))["results"]
        if result.get("assertions")
    }


def _fixture_resolves(fixture: str, declared: set[str], graded: set[str]) -> bool:
    """A fixture reference resolves only if its case is both declared and graded.

    Taken as a pure function of the two sets so the seeded control can supply
    constructed ones. Deriving the negative case from the shipped record instead
    would make the control vacuous whenever every declared case has been graded,
    which is the normal healthy state.
    """
    return fixture in declared and fixture in graded


def test_single_ecosystem_fixture_reference_resolves_to_a_graded_fixture() -> None:
    """A single-ecosystem group's fixture names a case that was actually graded.

    The promotion class is the cheapest by evidence cost, so its one non-textual
    obligation is that the fixture exists as measured work. Declaration alone is
    not enough: an id in `evals.json` with no graded result names a case nobody
    ran.
    """
    declared, graded = _declared_eval_ids(), _graded_eval_ids()
    # Anti-vacuity: empty sets would satisfy nothing meaningfully.
    assert len(declared) >= 2 and len(graded) >= 2, (len(declared), len(graded))

    checked = 0
    for topic in json.loads(ADMISSION.read_text(encoding="utf-8"))["topics"]:
        for group in topic.get("claim_groups", []):
            if group.get("promotion_class") != "single-ecosystem-contract":
                continue
            checked += 1
            assert _fixture_resolves(group["fixture"], declared, graded), (
                topic["topic"],
                group["name"],
                group["fixture"],
            )
    assert checked == 2, checked


def test_fixture_resolution_rejects_both_ways_a_reference_can_be_empty() -> None:
    """Seeded control over constructed sets: resolution can fail, two ways.

    An id absent everywhere and an id declared but never graded fail for
    different reasons; a check that read only `evals.json` would pass the second.
    """
    declared = {"real-and-graded", "declared-but-never-run"}
    graded = {"real-and-graded"}

    assert _fixture_resolves("real-and-graded", declared, graded)
    assert not _fixture_resolves("declared-but-never-run", declared, graded)
    assert not _fixture_resolves("absent-everywhere", declared, graded)
