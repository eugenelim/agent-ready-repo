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
    # The workflow body. Without it a result graded against a superseded body
    # satisfies every other guard here, which is what happened when T4 edited
    # this body after slice 2a recorded these two results: the staleness was
    # invisible because AC5 conditions re-measurement on a *pinned* digest
    # moving, and the body was not pinned. The results were re-taken blind.
    "SKILL.md",
    # The declaration itself, so rewording a prompt or an expectation cannot
    # silently re-point a recorded result at a run it never came from.
    "evals/evals.json",
    "evals/files/catchall-SKILL.md",
    "evals/files/nondeterministic-SKILL.md",
    "evals/files/nondeterministic-helper.py",
    "evals/files/nondeterministic-reference.md",
)
# Deliberately not part of `REVIEW_EVAL_FILES`. That tuple is the set whose
# digests a graded behaviour result must carry, and every member of it is
# parametrized into the digest test below. The readability corpus seeds no
# defect and is graded by the repository's readability gate rather than by a
# behaviour run, so listing it there would demand a recorded result that does
# not and should not exist.
REVIEW_READABILITY_FILES = ("evals/files/cognitive-load/ordinary-prose.md",)
UNGRADED_EVAL_IDS = frozenset({"cognitive-load-output-quality"})
# (eval_id, assertion text) pairs measured false by an independent adjudicating
# context and recorded as measured rather than reworded. Keyed by text, not
# index: an index migrates silently when an assertion is inserted above it --
# the length pin still passes, a real miss becomes exempt, and the true miss
# reads as a phantom pass. Reword or delete the assertion and this reddens.
KNOWN_REVIEW_MISSES = {
    (
        "detect-script-contract-failure",
        "Names the deterministic replay, exit, and cleanup contract "
        "ASE-DET-01 requires before optimization",
    ),
}
# Derived from the checklist the skill actually ships rather than restated, so
# retiring or adding a check cannot leave this bound describing a vocabulary
# the skill no longer has.
CHECKLIST_IDS = frozenset(
    re.findall(
        r"ASE-[A-Z]+-\d+",
        (REVIEW_ROOT / "references" / "review-checklist.md").read_text(
            encoding="utf-8"
        ),
    )
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

    assert set(cases) == REVIEW_EVAL_IDS | UNGRADED_EVAL_IDS
    seeded = {path for case in cases.values() for path in case["files"]}
    assert seeded <= set(REVIEW_EVAL_FILES) | set(REVIEW_READABILITY_FILES)
    assert "evals/files/catchall-SKILL.md" in seeded
    assert "evals/files/nondeterministic-helper.py" in seeded
    assert all(case["assertions"] for case in cases.values())
    # Scoped to the graded ids. An `expect.output_contains` is a marker a
    # recorded result has to attest; demanding one from the ungraded
    # readability case would declare a marker nothing measures, which is the
    # circular derivation this pack already had to remove twice.
    assert all(
        cases[eval_id]["expect"]["output_contains"] for eval_id in REVIEW_EVAL_IDS
    )
    assert not any("expect" in cases[eval_id] for eval_id in UNGRADED_EVAL_IDS)


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
    # Same containment reasoning as the per-result assertion below: every
    # seeded defect must be reported, and a sustained finding beyond the seeded
    # set is correct behaviour rather than a regression.
    assert seeded <= actual
    for result in review_results:
        case = behavior[result["eval_id"]]
        declared = set(case["expect"]["output_contains"])
        # The record splits the declaration in two: checklist ids land in
        # `actual_findings`, the mode marker in `actual_markers`. Bind the
        # union, so no declared element can go unattested by living in
        # whichever field the check does not read.
        # Containment, not equality. `expect.output_contains` is graded by the
        # runner as a substring check, so it declares a floor; asserting
        # equality here made the record stricter than the check it records and
        # turned a review finding a real defect beyond the seeded set into a
        # failure. An independent blind run sustained five findings against
        # four declared, and nine against six.
        declared_findings = {value for value in declared if value.startswith("ASE-")}
        assert declared_findings <= set(result["actual_findings"])
        # The floor cannot be padded into meaninglessness: every extra has to
        # be a checklist identifier the skill actually defines, so a result
        # cannot inflate its count with invented ids.
        assert set(result["actual_findings"]) <= CHECKLIST_IDS
        declared_assertions = case["assertions"]
        known_missing = {
            text
            for eval_id, text in KNOWN_REVIEW_MISSES
            if eval_id == result["eval_id"]
        }
        # The exemption must still describe a live assertion; otherwise a
        # reworded case would carry an exemption that matches nothing and
        # silently stops exempting anything.
        assert known_missing <= set(declared_assertions), (
            result["eval_id"],
            sorted(known_missing - set(declared_assertions)),
        )
        # One recorded miss, named rather than absorbed, in the same shape the
        # authoring side uses. Assertion index 5 -- 0-based, as the fixture and
        # the slice record both number it -- asks the review to name the replay,
        # exit and cleanup contract `ASE-DET-01` requires. The run named the
        # first two -- prescribing injected-input determinism and distinct exit
        # classes -- and never returned to cleanup, neither prescribing a path
        # nor disposing of it as vacuous. Naming the exact (case, index) means a
        # *different* miss still reddens while the known one does not read as a
        # pass.
        failing = {
            declared_assertions[index]
            for index, verdict in enumerate(result["assertions"])
            if not verdict
        }
        assert failing <= known_missing, (result["eval_id"], sorted(failing))
        # AC14: the values the graded runner emits, so a failure can be
        # attributed. Without these a re-record could drop them silently, and
        # `Mode: review` would again be attested by nothing the fixture holds.
        # A case carrying a known miss must record `assertions_ok` and `passed`
        # as False. Exempting them instead would let a re-record claim a clean
        # pass for a run that missed, which is the failure this pins shut.
        holds = all(result["assertions"])
        for value in ("produces_ok", "output_ok"):
            assert result[value] is True, (result["eval_id"], value)
        for value in ("assertions_ok", "passed"):
            assert result[value] is holds, (result["eval_id"], value)
        assert result["errored"] is False, result["eval_id"]
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
            "SKILL.md",
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
