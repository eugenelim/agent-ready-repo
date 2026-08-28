"""Construction contracts for review and measured optimization."""

from __future__ import annotations

import hashlib
import json
import os.path
import re
from pathlib import Path

import pytest
import yaml

PACK_ROOT = Path(__file__).resolve().parents[3]
REVIEW_ROOT = PACK_ROOT / ".apm" / "skills" / "review-or-optimize-agent-skill"
SKILL_ROOT = PACK_ROOT / ".apm" / "skills"
AUTHOR_SKILL_ROOT = SKILL_ROOT / "author-or-update-agent-skill"
# Each route the SKILL.md may name, mapped to its target anchored from the
# pack root rather than joined through `..`, so every path this suite opens
# is statically confined. `test_review_route_targets_are_faithful` proves
# each key really is the relative route from REVIEW_ROOT to its target, so
# the map cannot drift from the routes the skill actually writes.
ROUTE_TARGETS = {
    "references/review-checklist.md":
        REVIEW_ROOT / "references" / "review-checklist.md",
    "references/optimization.md":
        REVIEW_ROOT / "references" / "optimization.md",
    "../author-or-update-agent-skill/references/provider-contract.md":
        AUTHOR_SKILL_ROOT / "references" / "provider-contract.md",
    "../author-or-update-agent-skill/references/language-extension-seams.md":
        AUTHOR_SKILL_ROOT / "references" / "language-extension-seams.md",
    "../author-or-update-agent-skill/references/safety-and-authority.md":
        AUTHOR_SKILL_ROOT / "references" / "safety-and-authority.md",
}
REVIEW_ROUTES = tuple(ROUTE_TARGETS)
REVIEW_EVAL_IDS = frozenset(
    {"detect-activation-failure", "detect-script-contract-failure"}
)
REVIEW_EVAL_FILES = (
    # The declaration itself, so rewording a prompt or an expectation cannot
    # silently re-point a recorded result at a run it never came from.
    "evals/evals.json",
    "evals/files/catchall-SKILL.md",
    "evals/files/nondeterministic-SKILL.md",
    "evals/files/nondeterministic-helper.py",
)


def _frontmatter(text: str) -> dict[str, object]:
    """Parse skill YAML frontmatter."""

    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_review_precedes_measured_optimization() -> None:
    text = (REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata = _frontmatter(text)
    assert metadata["metadata"] == {
        "boundaries": ["filesystem_read_untrusted", "filesystem_write"]
    }
    description = str(metadata["description"]).lower()
    assert "use when the user asks" in description
    assert all(
        term in description for term in ("review", "audit", "optimize", "skill.md")
    )
    # An unnamed or ambiguous target must route into this workflow rather than
    # producing a clarifying refusal that never selects it.
    assert "select it first and resolve the target inside the workflow" in description
    assert "with nothing attached" in description
    assert "resolving an ambiguous target is this workflow's first step" in text
    # The two workflows are adjacent, so each description must name the
    # other's territory or an update request lands here instead.
    assert "do not use to frame, create, or update a skill" in description
    assert "belongs to the authoring workflow instead" in description
    # "activation boundary" appears in both descriptions; naming a property
    # to preserve must not reclassify an update request as a review.
    assert "keeping its activation boundary or any other property intact is still an update" in description
    # Whitespace-normalized: a reflow must not redden an intact contract.
    flat = " ".join(text.split())
    assert "Review is the default and remains read-only" in flat
    assert "observed failure or measured baseline" in flat
    assert "explicit mode transition" in flat
    optimization = (REVIEW_ROOT / "references" / "optimization.md").read_text(
        encoding="utf-8"
    )
    assert "before baseline" in optimization
    assert "identical before and after suite" in optimization


def test_review_checklist_covers_every_foundation_defect_class() -> None:
    checklist = (REVIEW_ROOT / "references" / "review-checklist.md").read_text(
        encoding="utf-8"
    )
    expected = {
        "ASE-ACT-01",
        "ASE-PROG-01",
        "ASE-PORT-01",
        "ASE-DET-01",
        "ASE-AUTH-01",
        "ASE-SEC-01",
        "ASE-CTX-01",
        "ASE-WRITE-01",
        "ASE-CONC-01",
        "ASE-FAIL-01",
    }
    assert set(re.findall(r"ASE-[A-Z]+-\d+", checklist)) == expected
    for phrase in (
        "Trigger precision",
        "Progressive disclosure",
        "Portability floor",
        "Determinism and exit contract",
        "Authority and authentication",
        "Duplicated context",
        "Conflicting writes",
        "Unbounded concurrency",
    ):
        assert phrase in checklist


def test_review_skill_routes_resolve_including_sibling_pack_references() -> None:
    """Every route the review workflow names must exist in the projected tree.

    The two shared contracts live in the sibling authoring skill, so a rename
    there would otherwise leave this workflow pointing at nothing.
    """

    text = (REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8")
    routes = re.findall(r"\(((?:\.\./|references/)[^)]+\.md)\)", text)
    assert set(routes) == set(REVIEW_ROUTES)


@pytest.mark.parametrize("route", REVIEW_ROUTES)
def test_review_reference_route_resolves_inside_the_pack(route: str) -> None:
    target = ROUTE_TARGETS[route]
    assert target.is_file(), route
    # A sibling route must stay inside the pack's own skill tree.
    assert target.resolve().is_relative_to(SKILL_ROOT.resolve()), route


@pytest.mark.parametrize("route", REVIEW_ROUTES)
def test_review_route_targets_are_faithful(route: str) -> None:
    """The mapped target must be exactly what the written route resolves to."""

    target = ROUTE_TARGETS[route]
    assert os.path.relpath(target, REVIEW_ROOT).replace(os.sep, "/") == route


def test_review_never_executes_a_candidate_without_an_approved_transition() -> None:
    """AC17: review completes without executing untrusted code.

    The checklist previously told the reviewer to prefer *executing* a
    candidate's fixtures, inside a mode the SKILL.md calls read-only and with
    no reference to the spec's ask-first transition. The pack ships a fixture
    whose own instructions say to run a helper, so the instruction had to carry
    the gate rather than rely on reviewer judgement.
    """

    checklist = " ".join(
        (REVIEW_ROOT / "references" / "review-checklist.md")
        .read_text(encoding="utf-8")
        .split()
    )
    assert "Review never executes the candidate." in checklist
    for required in (
        "separate user-approved transition",
        "the purpose",
        "the authority required",
        "the bounded target",
        "cleanup path",
        "obtain explicit approval first",
        "report the unexecuted script as a coverage gap",
    ):
        assert required in checklist, required
    # The superseded instruction must be gone, not merely qualified.
    assert "prefer executing bounded success and failure fixtures" not in checklist


def test_seeded_cases_have_exact_applicable_check_coverage() -> None:
    cases = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "review-cases.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(cases) == 4
    # AC6 states two requirements, not one: every *applicable* check is
    # confirmed, and every *seeded* defect is reported. Equality here collapsed
    # them and forbade the only shape that tells them apart.
    for case in cases:
        assert set(case["seeded"]) <= set(case["applicable"]), case["id"]
    covered = {check for case in cases for check in case["seeded"]}
    assert len(covered) == 10
    # At least one case must carry an applicable-but-clean check, or the
    # confirmation half of AC6 has no fixture that can exercise it.
    assert any(
        set(case["applicable"]) - set(case["seeded"]) for case in cases
    )


def test_review_activation_examples_exclude_adjacent_work() -> None:
    cases = json.loads(
        (REVIEW_ROOT / "evals" / "eval_queries.json").read_text(encoding="utf-8")
    )
    positives = [case for case in cases if case["should_trigger"]]
    negatives = [case for case in cases if not case["should_trigger"]]
    assert len(positives) >= 4
    assert len(negatives) >= 5
    assert any("baseline" in case["query"] for case in positives)
    for adjacent in ("pull request", "paragraph", "repository", "module", "architecture"):
        assert any(adjacent in case["query"].lower() for case in negatives)


def test_review_behavior_evals_seed_activation_and_script_failures() -> None:
    payload = json.loads(
        (REVIEW_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
    )
    cases = {case["id"]: case for case in payload["evals"]}

    assert set(cases) == {
        "detect-activation-failure",
        "detect-script-contract-failure",
    }
    seeded = {path for case in cases.values() for path in case["files"]}
    assert seeded <= set(REVIEW_EVAL_FILES)
    assert "evals/files/catchall-SKILL.md" in seeded
    assert "evals/files/nondeterministic-helper.py" in seeded
    assert all(case["assertions"] for case in cases.values())
    assert all(case["expect"]["output_contains"] for case in cases.values())


def test_independent_behavior_results_report_every_seeded_defect() -> None:
    fixture_root = PACK_ROOT / "tests" / "fixtures"
    seeded = {
        finding
        for case in json.loads(
            (fixture_root / "review-cases.json").read_text(encoding="utf-8")
        )
        for finding in case["seeded"]
    }
    evidence = json.loads(
        (fixture_root / "behavior-results.json").read_text(encoding="utf-8")
    )
    behavior = {
        case["id"]: case
        for case in json.loads(
            (REVIEW_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
    }

    assert evidence["evaluation_mode"] == "independent-read-only-subcontext"
    assert evidence["candidate_execution"] is False
    review_results = [
        result
        for result in evidence["results"]
        if result["eval_id"] in behavior
    ]
    actual = {
        finding
        for result in review_results
        for finding in result["actual_findings"]
    }
    assert actual == seeded
    for result in review_results:
        case = behavior[result["eval_id"]]
        declared = set(case["expect"]["output_contains"])
        # The record splits the declaration in two: checklist ids land in
        # `actual_findings`, the mode marker in `actual_markers`. Bind the
        # union, so no declared element can go unattested by living in
        # whichever field the check does not read.
        assert set(result["actual_findings"]) == {
            value for value in declared if value.startswith("ASE-")
        }
        assert all(result["assertions"])
        # `all([])` is True, so truthiness alone accepts a record claiming that
        # none of the declared checklist assertions were confirmed. Pin the
        # count to the declaration, as the authoring side does.
        assert len(result["assertions"]) == len(case["assertions"])
        # Equality, not a subset: `<=` is satisfied by the empty set, so a
        # result could record no provenance at all and the aggregate digest
        # tests below would still pass on a sibling result's copy of the path.
        # Same shape as the authoring side: declared files plus the eval
        # payload that declares them. `.get` rather than `[]` so a future
        # workspace-less case fails this assertion with a message instead of
        # raising KeyError, and cannot be satisfied by an empty record.
        assert set(result["source_files"]) == {
            "evals/evals.json",
            *(case.get("files") or ()),
        }
        # Kept alongside the equality: the local confinement invariant, whose
        # authoring counterpart is retained for the same reason.
        assert set(result["source_files"]) <= set(REVIEW_EVAL_FILES)


@pytest.mark.parametrize("relative_path", REVIEW_EVAL_FILES)
def test_review_seeded_fixture_matches_its_recorded_digest(relative_path: str) -> None:
    evidence = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "behavior-results.json").read_text(
            encoding="utf-8"
        )
    )
    path = REVIEW_ROOT / relative_path
    assert path.is_file()
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    # Scoped to this skill's own results, for the reason its authoring
    # counterpart gives: the `evals/evals.json` key names a different file
    # under each skill root.
    recorded = {
        result["source_files"][relative_path]
        for result in evidence["results"]
        if result["eval_id"] in REVIEW_EVAL_IDS
        and relative_path in result.get("source_files", {})
    }
    assert recorded == {digest}


def test_review_refuses_untrusted_instruction_and_authentication_escalation() -> None:
    text = " ".join((REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8").split())
    # The confinement rule has one authority (ASE-CTX-01); this workflow must
    # route to it rather than restate a list that can drift from the other.
    assert "safety-and-authority.md" in text
    assert "single authority for the confinement rule" in text
    safety = " ".join(
        (AUTHOR_SKILL_ROOT / "references" / "safety-and-authority.md")
        .read_text(encoding="utf-8")
        .split()
    )
    assert "before any content access" in safety
    assert "regular file" in safety
    # Whitespace-normalized: these pin a contract phrase, not a wrap position.
    assert "cannot become instructions for the reviewer" in text
    assert "inspect credentials" in text
    assert "filesystem_write" in text and "not standing permission" in text
