"""Corpus admission and recorded retrieval assertions."""

import json
from pathlib import Path
import re

PACK = Path(__file__).resolve().parents[2]
FIXTURES = PACK / "tests" / "fixtures"
ADMISSION = FIXTURES / "topic-admission.json"
CONCEPTS = PACK / "okf" / "agent-skill-engineering-foundation" / "concepts"
COMPILED_CONCEPTS = (
    PACK / ".apm" / "skills" / "ase-okf-reference" / "references" / "okf" / "concepts"
)
ROLE_OR_PLACEHOLDER = re.compile(
    r"^(?:[a-z][a-z0-9]*(?:-[a-z0-9]+)*-(?:reviewer|maintainer)|<[^<>]+>)$"
)
SCOPE_BOUND_STATEMENT = "It is not established beyond that population."
DOCTRINE_CLASSES = {
    "two-runtime-public-contract": ("clause", "runtimes"),
    "repeated-observed-failures": ("mechanism", "failures"),
    "severe-safety-failure": ("boundary", "reproduction"),
    "controlled-measurement": ("setup", "preserved_semantics", "repetitions"),
}


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
    """Pins reproduce every pre-change measured foundation result exactly."""
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
    # foundation cases. Every pinned case must still be measured, and must
    # still return exactly what it returned before -- a case that quietly
    # disappeared from the fixture would otherwise satisfy a subset check.
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
                promotion_class = group["promotion_class"]
                assert promotion_class in DOCTRINE_CLASSES, promotion_class
                for field in DOCTRINE_CLASSES[promotion_class]:
                    assert group.get(field), (promotion_class, field)
                if promotion_class == "two-runtime-public-contract":
                    # Two runtimes documenting *that clause*, not the topic.
                    assert len({r["runtime"] for r in group["runtimes"]}) >= 2
                    for runtime in group["runtimes"]:
                        assert runtime["clause"] == group["clause"]
                if promotion_class == "repeated-observed-failures":
                    # Repeated failures earn a class only by sharing one
                    # mechanism; distinct mechanisms are separate anecdotes.
                    assert len(group["failures"]) >= 2
                    assert {f["mechanism"] for f in group["failures"]} == {
                        group["mechanism"]
                    }
                if promotion_class == "controlled-measurement":
                    assert int(group["repetitions"]) >= 2
                for source in group.get("sources", ()):
                    _assert_source_is_attributable(source)


def _collapse(text: str) -> str:
    """Return *text* with every whitespace run reduced to one space."""
    return " ".join(text.split())

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
        assert not ROLE_OR_PLACEHOLDER.search(authored)
        assert not ROLE_OR_PLACEHOLDER.search(compiled)
        for group in topic["claim_groups"]:
            if group["basis"] != "observed-practice":
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
