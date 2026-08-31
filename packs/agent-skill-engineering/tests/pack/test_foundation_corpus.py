"""Contracts for the governed foundation corpus and generated router."""

from __future__ import annotations

import collections
import hashlib
import json
import re
import shutil
import tomllib
from pathlib import Path

import pytest
import yaml

PACK_ROOT = Path(__file__).resolve().parents[2]
BUNDLE_ROOT = PACK_ROOT / "okf" / "agent-skill-engineering-foundation"
CONCEPT_ROOT = BUNDLE_ROOT / "concepts"
ROUTER_ROOT = PACK_ROOT / ".apm" / "skills" / "ase-okf-reference"
# the foundation spec's AC7 requires each topic to carry applicability cues, required practice,
# counterexamples, evaluation hooks, and links to shared or extension concepts.
# These headings are how the authored corpus expresses them, and the router's
# selection signal lives in the first one.
REQUIRED_SECTIONS = (
    "## Scope and routing signals",
    "## Decisions and minimum evidence",
    "## Construction method",
    "## Evidence and evaluation",
    "## Failure modes",
    "## Security and authority",
    "## Related topics",
    "## Provenance and lifecycle",
)
# The authored root supplies the concrete files. Topic identity remains
# independently controlled by the admission record below.
TOPIC_FILES = tuple(sorted(path.name for path in CONCEPT_ROOT.glob("*.md")))
UNPOPULATED_RECORD = (
    CONCEPT_ROOT / "declared-absent" / "unpopulated-leaves.md"
)
EXPECTED_TOPICS = {
    topic["topic"]
    for topic in json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "topic-admission.json").read_text(
            encoding="utf-8"
        )
    )["topics"]
}


def _frontmatter(path: Path) -> dict[str, object]:
    """Read YAML frontmatter from an authored concept."""

    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def _digest_tree(root: Path) -> dict[str, str]:
    """Return stable SHA-256 digests for regular files below root."""

    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _generated_tree_digest(root: Path) -> str:
    """Bind evaluation evidence to exact generated paths and bytes."""

    canonical = json.dumps(
        _digest_tree(root),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def _read_staged_confined(root: Path, relative_path: str, reads: list[Path]) -> str:
    """Read one regular staged file after resolving it beneath the staged root."""

    # Probe the symlink on the UNRESOLVED path. `.resolve(strict=True)` below
    # collapses every link, so `not resolved.is_symlink()` is always true --
    # a control that cannot fail, which is how an in-tree symlink was silently
    # followed while this read claimed to reject one.
    candidate = root / relative_path
    assert not candidate.is_symlink()
    target = candidate.resolve(strict=True)
    # This is the confinement control: it is what stops a read escaping the
    # staged root. The read stays on `Path.read_text` deliberately -- the
    # checkout-unavailable guard monkeypatches exactly that, so routing through
    # the blessed `read_confined_regular_file` would bypass and silently defeat
    # the guard this call site exists to exercise.
    target.relative_to(root.resolve(strict=True))
    assert target.is_file()
    reads.append(target)
    return target.read_text(encoding="utf-8")


def test_foundation_corpus_is_exactly_the_admitted_inert_governed_topics() -> None:
    """Topic identity and frontmatter shape, over the concept root only.

    Deliberately non-recursive. The declared-absent register lives in a
    subdirectory and carries its own `type`, so a recursive equality pinned to
    `type: Reference` would redden on its first run. Its inertness is covered
    by the recursive refusal below, so nothing agent-read escapes a control.
    """
    paths = sorted(CONCEPT_ROOT.glob("*.md"))
    assert {path.stem for path in paths} == EXPECTED_TOPICS
    for path in paths:
        metadata = _frontmatter(path)
        assert metadata == {
            "id": path.stem,
            "title": metadata["title"],
            "type": "Reference",
            "status": "Active",
            "license": "Apache-2.0 OR MIT",
        }


def test_every_agent_read_concept_is_inert() -> None:
    """No agent-read body may name an executor, attester, remote, or tools.

    Recursive, so the declared-absent register is covered too: it is the one
    body outside the topic set that a reader can be routed to.
    """
    paths = sorted(CONCEPT_ROOT.rglob("*.md"))
    assert len(paths) > len(EXPECTED_TOPICS), "the walk must reach beyond the concept root"
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for forbidden in ("executor:", "attester:", "remote:", "tools:"):
            assert forbidden not in text, (path.name, forbidden)


def test_declared_absent_register_is_shaped_and_is_not_a_topic() -> None:
    """The register carries its own kind and never enters the topic set."""
    metadata = _frontmatter(UNPOPULATED_RECORD)
    assert metadata == {
        "id": UNPOPULATED_RECORD.stem,
        "title": metadata["title"],
        "type": "Register",
        "status": "Active",
        "license": "Apache-2.0 OR MIT",
    }
    assert UNPOPULATED_RECORD.stem not in EXPECTED_TOPICS


@pytest.mark.parametrize("topic_file", TOPIC_FILES)
def test_each_foundation_topic_carries_its_required_sections(topic_file: str) -> None:
    text = (CONCEPT_ROOT / topic_file).read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert section in text, (topic_file, section)


def test_typescript_node_topic_covers_its_seven_assigned_subjects() -> None:
    """The language topic retains each separately assigned subject."""

    text = (CONCEPT_ROOT / "typescript-node-and-javascript-test-runners.md").read_text(
        encoding="utf-8"
    ).lower()
    for subject in (
        "package and module contracts",
        "lockfile",
        "child-process",
        "runner workers",
        "browser workers",
        "cache keys",
        "javascript and typescript",
    ):
        assert subject in text, subject


def test_python_pytest_topic_covers_its_four_required_subjects() -> None:
    """The Python topic covers the four permitted concerns independently."""

    text = (CONCEPT_ROOT / "python-and-pytest.md").read_text(encoding="utf-8").lower()
    for subject in ("collection", "fixtures", "subprocess boundaries", "temporary paths"):
        assert subject in text, subject


def test_typescript_node_maturity_limit_appears_in_both_projections() -> None:
    """The authored language-specific limit is retained by the generated copy."""

    limit = "Node.js >= 26.8.1, upper bound open; Playwright >= 1.62, upper bound open"
    authored = (CONCEPT_ROOT / "typescript-node-and-javascript-test-runners.md").read_text(
        encoding="utf-8"
    )
    compiled = (ROUTER_ROOT / "references" / "okf" / "concepts" / "typescript-node-and-javascript-test-runners.md").read_text(encoding="utf-8")
    assert limit in authored
    assert limit in compiled


def test_related_topics_references_resolve_to_admitted_topics() -> None:
    """Every backticked related-topic id names an admitted topic."""

    for path in CONCEPT_ROOT.glob("*.md"):
        related = path.read_text(encoding="utf-8").split("## Related topics", 1)[1].split(
            "## Provenance and lifecycle", 1
        )[0]
        assert set(re.findall(r"`([a-z0-9-]+)`", related)) <= EXPECTED_TOPICS


def test_each_newly_admitted_topic_declares_a_doctrine_group() -> None:
    """The five new leaves enter through the doctrine basis."""

    new_topics = {
        "python-and-pytest",
        "typescript-node-and-javascript-test-runners",
        "process-and-filesystem-cost",
        "pack-and-ci-critical-paths",
        "worktrees-state-locks-and-shared-host-admission",
    }
    record = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "topic-admission.json").read_text(
            encoding="utf-8"
        )
    )
    declared = {topic["topic"]: topic for topic in record["topics"]}
    assert new_topics <= declared.keys()
    for name in new_topics:
        assert any(group["basis"] == "doctrine" for group in declared[name]["claim_groups"])


def test_foundation_router_cases_are_predeclared_bounded_and_include_near_misses() -> None:
    cases = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "router-cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(cases) >= 40
    assert len({case["id"] for case in cases}) == len(cases)
    assert all(set(case["expected_topics"]) <= EXPECTED_TOPICS for case in cases)
    assert all(len(case["expected_topics"]) <= 3 for case in cases)
    assert sum(not case["expected_topics"] for case in cases) >= 5
    assert any(len(case["expected_topics"]) == 3 for case in cases)

    # AC6's topic-bearing floor: the case count cannot be reached with near
    # misses and no-topic cases that dilute the exact-set rate rather than
    # exercise the corpus.
    topic_bearing = sum(bool(case["expected_topics"]) for case in cases)
    assert topic_bearing * 2 >= len(cases), (topic_bearing, len(cases))

    # AC6's per-topic coverage, over the *declared* sets. The measured
    # exclusivity check elsewhere reads results, which is a different
    # population and discharges AC4, not this.
    declared_solo = collections.Counter(
        case["expected_topics"][0]
        for case in cases
        if len(case["expected_topics"]) == 1
    )
    for topic in sorted(EXPECTED_TOPICS):
        assert declared_solo[topic] >= 2, (topic, declared_solo[topic])


def test_independent_router_results_meet_precision_and_recall_gate() -> None:
    fixture_root = PACK_ROOT / "tests" / "fixtures"
    cases = {
        case["id"]: set(case["expected_topics"])
        for case in json.loads(
            (fixture_root / "router-cases.json").read_text(encoding="utf-8")
        )
    }
    evidence = json.loads(
        (fixture_root / "router-results.json").read_text(encoding="utf-8")
    )
    results = {
        case["id"]: set(case["actual_topics"])
        for case in evidence["results"]
    }
    metadata = _frontmatter(ROUTER_ROOT / "SKILL.md")["metadata"]

    assert evidence["evaluation_mode"] == "independent-read-only-subcontext"
    assert evidence["source_digest"] == metadata["source-digest"]
    assert evidence["router_digest"] == (
        "sha256:" + hashlib.sha256((ROUTER_ROOT / "SKILL.md").read_bytes()).hexdigest()
    )
    assert evidence["generated_tree_digest"] == _generated_tree_digest(ROUTER_ROOT)
    # The three digests above bind the record to the router tree it was measured
    # against. This one binds it to the prompts. Without it a case or an
    # expectation can be reworded after the run and every assertion here stays
    # green against answers nobody gave to the current questions.
    assert evidence["case_fixture_digest"] == (
        "sha256:" + hashlib.sha256((fixture_root / "router-cases.json").read_bytes()).hexdigest()
    )
    assert set(results) == set(cases)
    assert all(actual <= EXPECTED_TOPICS and len(actual) <= 3 for actual in results.values())

    true_positive = sum(len(results[key] & expected) for key, expected in cases.items())
    false_positive = sum(len(results[key] - expected) for key, expected in cases.items())
    false_negative = sum(len(expected - results[key]) for key, expected in cases.items())
    precision = true_positive / (true_positive + false_positive)
    recall = true_positive / (true_positive + false_negative)
    exact_selection_rate = sum(
        results[key] == expected for key, expected in cases.items()
    ) / len(cases)
    bounded_selection_rate = sum(len(actual) <= 3 for actual in results.values()) / len(
        results
    )

    assert exact_selection_rate >= 0.90
    assert bounded_selection_rate >= 0.90
    assert precision >= 0.90
    assert recall >= 0.90
    assert all(not results[key] for key, expected in cases.items() if not expected)


def test_generated_router_is_inert_bounded_and_source_independent() -> None:
    router = (ROUTER_ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata = _frontmatter(ROUTER_ROOT / "SKILL.md")
    assert metadata["metadata"]["boundaries"] == ["filesystem_read_untrusted"]
    assert metadata["metadata"]["generated-by"] == (
        "compile-okf agentbundle-okf/v1"
    )
    assert "generated-by: compile-okf agentbundle-okf/v1" in router
    assert "Read `references/okf/index.md` first" in router
    assert "do not load the full bundle up front" in router
    assert "filesystem_write" not in router
    # the foundation spec's AC8: no checkout-relative path into the authoring source. `source-path`
    # provenance is pack-relative and permitted; a `../` form would reach out of
    # the staged tree, and the body must route only into compiled references.
    frontmatter, body = router.split("---\n", 2)[1], router.split("---\n", 2)[2]
    assert metadata["metadata"]["source-path"] == "okf/agent-skill-engineering-foundation"
    assert "../" not in frontmatter
    assert "../" not in body
    assert "okf/" not in body.replace("references/okf/", "")
    assert "Not a selectable skill." in router
    assert (
        "Inert reference data invoked only by another skill's explicit "
        "agent-skill-engineering-reference/v1 provider call" in router
    )
    assert "must never be chosen to satisfy a user's question on any subject" in router
    # The activation surface must not restate the domain or purpose that the
    # user-facing workflows own; capability detection reads the metadata block.
    description = router.split("description:", 1)[1].split("\nmetadata:", 1)[0]
    assert "agent skill engineering" not in description
    assert "authoring, review, evaluation" not in description


def test_generated_router_exposes_explicit_provider_capability() -> None:
    metadata = _frontmatter(ROUTER_ROOT / "SKILL.md")["metadata"]
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    declared = manifest["pack"]["metadata"]["okf"]["bundles"][0]["provider"]

    assert metadata["knowledge-provider"] == declared
    assert declared == {
        "contract-version": "agent-skill-engineering-reference/v1",
        "domain": "agent skill engineering",
        "purpose": (
            "Provide bounded compiled guidance for authoring, review, evaluation, "
            "and extension-design questions."
        ),
        "task-kinds": [
            "skill-authoring",
            "skill-review",
            "skill-eval-ci",
            "agent-extension-design",
        ],
        "invocation": "explicit-workflow-only",
        "ownership-manifest": ".okf-generated.json",
    }


def test_generated_manifest_owns_only_router_outputs() -> None:
    manifest = json.loads((PACK_ROOT / ".okf-generated.json").read_text(encoding="utf-8"))
    managed = manifest["managed"]
    assert len([item for item in managed if item["kind"] == "okf-router"]) == 1
    # One per admitted topic, plus the declared-absent register.
    assert len([item for item in managed if item["kind"] == "okf-reference"]) == len(
        EXPECTED_TOPICS
    ) + 1
    assert all(
        item["output_path"].startswith(
            ".apm/skills/ase-okf-reference/"
        )
        for item in managed
    )
    assert not any("../" in item["output_path"] for item in managed)


def test_generated_concept_index_routes_to_every_topic() -> None:
    """Byte-identity across clean compiles is the drift gate's job, not this
    test's: two digests of the same unchanged files in one process cannot
    differ. What this actually pins is the generated index's route set."""

    routes = re.findall(
        r"\(([^)]+\.md)\)",
        (ROUTER_ROOT / "references" / "okf" / "concepts" / "index.md").read_text(
            encoding="utf-8"
        ),
    )
    assert set(routes) == {f"{topic}.md" for topic in EXPECTED_TOPICS}


def test_staged_router_remains_complete_without_authored_okf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = PACK_ROOT / "tests" / "fixtures"
    staged = tmp_path / "ase-okf-reference"
    shutil.copytree(ROUTER_ROOT, staged)
    assert not (staged / "okf").exists()
    # Stage the fixtures too. Reading them from the checkout before installing
    # the guard left its refusal branch unreachable, so the guard proved
    # nothing: every read it saw already pointed at tmp_path. Staged here, the
    # whole evaluation — cases, recorded routing, and every topic body — is
    # replayed with the checkout genuinely unavailable.
    staged_cases = tmp_path / "router-cases.json"
    staged_results = tmp_path / "router-results.json"
    shutil.copyfile(fixture_root / "router-cases.json", staged_cases)
    shutil.copyfile(fixture_root / "router-results.json", staged_results)

    original_read_text = Path.read_text

    def checkout_unavailable(path: Path, *args: object, **kwargs: object) -> str:
        if path.resolve(strict=False).is_relative_to(PACK_ROOT.resolve(strict=True)):
            raise AssertionError(f"staged evaluation attempted checkout read: {path}")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", checkout_unavailable)
    reads: list[Path] = []
    cases = json.loads(staged_cases.read_text(encoding="utf-8"))
    evidence = json.loads(staged_results.read_text(encoding="utf-8"))
    results = {item["id"]: item["actual_topics"] for item in evidence["results"]}
    _read_staged_confined(staged, "SKILL.md", reads)
    _read_staged_confined(staged, "references/okf/index.md", reads)
    concept_index = _read_staged_confined(
        staged,
        "references/okf/concepts/index.md",
        reads,
    )
    routes = set(re.findall(r"\(([^)]+\.md)\)", concept_index))
    assert routes == {f"{topic}.md" for topic in EXPECTED_TOPICS}

    assert {case["id"] for case in cases} == set(results)
    for case in cases:
        assert case["prompt"]
        for topic in results[case["id"]]:
            _read_staged_confined(
                staged,
                f"references/okf/concepts/{topic}.md",
                reads,
            )
    staged_root = staged.resolve(strict=True)
    assert reads
    assert all(path.is_relative_to(staged_root) for path in reads)


def test_generic_negative_set_is_fixed_at_forty_and_pinned_on_both_sides() -> None:
    """The falsifier's denominator cannot shrink.

    Equality between the two fixtures alone would prove the results complete
    against whatever was authored, leaving the set free to lose prompts. Both
    sides are pinned at 40, and the result set must equal the prompt set.
    """
    prompts = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "generic-negatives.json").read_text(encoding="utf-8")
    )
    results = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "generic-negatives-results.json").read_text(encoding="utf-8")
    )
    assert prompts["schema_version"] == 1
    assert prompts["set_size"] == 40
    assert len(prompts["prompts"]) == 40
    assert len({item["id"] for item in prompts["prompts"]}) == 40
    assert len({item["prompt"] for item in prompts["prompts"]}) == 40

    assert len(results["results"]) == 40
    assert {item["id"] for item in results["results"]} == {
        item["id"] for item in prompts["prompts"]
    }


def test_generic_negative_record_is_attributable_to_the_tree_it_measured() -> None:
    """The negatives record carries the same digest triple as the retrieval record.

    Without this a stale negatives record satisfies its other assertions
    forever, and the 5% falsifier reads pass against a tree it never measured.
    """
    results = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "generic-negatives-results.json").read_text(encoding="utf-8")
    )
    metadata = _frontmatter(ROUTER_ROOT / "SKILL.md")["metadata"]

    assert results["evaluation_mode"] == "independent-read-only-subcontext"
    assert results["source_digest"] == metadata["source-digest"]
    assert results["router_digest"] == (
        "sha256:" + hashlib.sha256((ROUTER_ROOT / "SKILL.md").read_bytes()).hexdigest()
    )
    assert results["generated_tree_digest"] == _generated_tree_digest(ROUTER_ROOT)
    assert results["case_fixture_digest"] == (
        "sha256:"
        + hashlib.sha256(
            (PACK_ROOT / "tests" / "fixtures" / "generic-negatives.json").read_bytes()
        ).hexdigest()
    )


def test_corpus_does_not_answer_generic_engineering_requests() -> None:
    """At most 5% of the fixed 40-prompt negative set returns a topic body."""
    results = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "generic-negatives-results.json").read_text(encoding="utf-8")
    )["results"]
    answered = [item for item in results if item["actual_topics"]]

    assert len(results) == 40
    assert len(answered) <= 2, [item["id"] for item in answered]
