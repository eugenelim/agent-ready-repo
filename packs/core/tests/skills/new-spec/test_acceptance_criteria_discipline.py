"""Acceptance-criteria authoring contracts for the new-spec skill."""

import json
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
REPO_ROOT = PACK_ROOT.parents[1]
SKILL = PACK_ROOT / ".apm/skills/new-spec/SKILL.md"
SPEC = PACK_ROOT / ".apm/skills/new-spec/assets/spec.md"
PLAN = PACK_ROOT / ".apm/skills/new-spec/assets/plan.md"
EVALS = PACK_ROOT / ".apm/skills/new-spec/evals/evals.json"
PLANNING_GUIDE = REPO_ROOT / "guides/core/how-to/plan-and-execute-non-trivial-work.md"
CORE_EXPLANATION = REPO_ROOT / "guides/core/explanation/core-pack.md"

SOURCES = {"skill": SKILL, "spec": SPEC, "plan": PLAN}
RULES = (
    (
        "criterion-independence",
        "spec",
        "A criterion is more than one when its parts have separate failure modes with separate remedies.",
    ),
    (
        "template-citation",
        "skill",
        "`assets/spec.md`'s `## Acceptance Criteria` guidance owns the criterion-shape rules, including the independence boundary, worked examples, limits, claim minimality, and the mechanism give-away",
    ),
    (
        "bound-ledger",
        "spec",
        "For every numeric limit a criterion states, record the input that makes the limit fire first and the enforcement mechanism that makes that ordering true; a limit missing **either** fact is not yet a criterion.",
    ),
    (
        "two-limits",
        "spec",
        "Where one quantity has two limits, either order them so each is reachable for some input, or declare one non-binding on that route and name the limit that fires instead.",
    ),
    (
        "corpus-trigger",
        "skill",
        "When the spec's subject is third-party, untrusted, or otherwise externally authored input and a criterion specifies a refusal",
    ),
    (
        "corpus-oracle",
        "skill",
        "draft into the plan's first tasks a corpus task that runs the specified rules against recorded real inputs and records the resulting accept and reject counts before finalising that criterion.",
    ),
    (
        "unreachable-corpus",
        "skill",
        "When no corpus of real inputs is reachable for a refusal contract over third-party, untrusted, or otherwise externally authored input, record that absence as an Unverified assumption.",
    ),
    (
        "cite-owner",
        "skill",
        "When a criterion depends on a rule owned elsewhere, cite its document and identifier rather than restating it.",
    ),
    (
        "resolve-duplicate",
        "skill",
        "When one rule is found stated in two places, record which statement is the owner and reduce the other to a cross-reference.",
    ),
    (
        "step-four-pointers",
        "skill",
        "See step 9 for citation discipline and step 5 for the corpus obligation.",
    ),
    (
        "deletion-pass",
        "skill",
        "After review rounds converge and before requesting human approval, run one deletion pass over every criterion and task added during review.",
    ),
    (
        "claim-minimality",
        "spec",
        "Make every claim earn its place by making a wrong implementation detectable.",
    ),
    (
        "limit-origin",
        "spec",
        "A criterion stating a limit names the reference point it is measured from.",
    ),
    (
        "limit-value",
        "spec",
        "A criterion requiring a limit states its value and never asks an implementer to supply one:",
    ),
    (
        "observable-outcome",
        "spec",
        "A criterion names an observable outcome. Naming a function's parameters, a helper, or a call sequence is the give-away that the content belongs in the plan.",
    ),
    (
        "plan-mechanism",
        "skill",
        "Carry mechanism, never a restatement of a criterion.",
    ),
    (
        "reduce-over-specified-plan",
        "skill",
        "the plan is over-specified: reduce it rather than extending it before the existing three-pass escalation.",
    ),
    (
        "conjunction-cue",
        "spec",
        "A criterion that needs \"and\" to join two **different predicates** is two criteria:",
    ),
)
EXAMPLES = (
    ('E1', 'splits', 'Two different predicates; no single sentence covers both.', '`writer.py` emits `manifest.json` with keys in byte-sorted order, and `--dry-run` prints that manifest without writing a file.'),
    ('E2', 'stays one', 'One predicate substituted at each member of an enumerated set, checkable as written at every member.', 'no sensitive data reaches stdout, stderr, logs, or skill output surfaced to the agent.'),
    ('E3', 'stays one', 'One comparison value expressed in parts — the split test never engages, because there is one failure and one remedy.', 'the digest preimage is the u64be path length, the path bytes, the execute byte, the u64be content length, then the content bytes.'),
    ('E4', 'splits', '"X is correct" is not checkable as written: it expands into a different check per member.', 'the same constraint, correctness, holds across stdout and the exit code.'),
    ('E5', 'stays one', 'Different failure modes (interception, script access) but one substitutable predicate and one remedy.', 'session cookies are set `Secure` and `HttpOnly`.'),
)


def flattened(path: Path) -> str:
    """Read a source file while making wrapped prose assertion-stable."""
    return " ".join(path.read_text(encoding="utf-8").split())


@pytest.mark.parametrize(("rule_id", "owner", "phrase"), RULES, ids=[rule[0] for rule in RULES])
def test_acceptance_criterion_rule_has_one_owner(
    rule_id: str, owner: str, phrase: str
) -> None:
    assert phrase in flattened(SOURCES[owner])
    for other_name, other_path in SOURCES.items():
        if other_name != owner:
            assert phrase not in flattened(other_path)


@pytest.mark.parametrize(
    ("identifier", "verdict", "example", "criterion"),
    EXAMPLES,
    ids=[example[0] for example in EXAMPLES],
)
def test_worked_example_has_one_owner_and_occurs_once(
    identifier: str, verdict: str, example: str, criterion: str
) -> None:
    """Pin the exemplar too, not just its rationale.

    The examples are normative — they, not an adjective in the rule, decide the
    boundary. Pinning only the reason lets an edit replace the quoted criterion
    an example exists to demonstrate while every assertion stays green.
    """
    owner_text = flattened(SPEC)
    assert f"**{identifier} — {verdict}.**" in owner_text
    assert owner_text.count(example) == 1
    assert owner_text.count(criterion) == 1, f"{identifier} exemplar missing or duplicated"
    for other_path in (SKILL, PLAN):
        other_text = flattened(other_path)
        assert f"**{identifier} — {verdict}.**" not in other_text
        assert example not in other_text
        assert criterion not in other_text, f"{identifier} exemplar duplicated"


def test_unreachable_corpus_rule_is_not_duplicated_within_its_owner() -> None:
    phrase = next(phrase for rule_id, _, phrase in RULES if rule_id == "unreachable-corpus")
    assert flattened(SKILL).count(phrase) == 1


# A deny-list guard for the retired formulations ("related", "cohesive", "the
# same constraint", "unified", "coherent") was removed: it scanned this module's
# own RULES constants, not the shipped prose, so it could only ever fail in the
# commit that introduced an offending pin. Retargeting it at the shipped files is
# also wrong -- "the same constraint" ships once, inside E4 (assets/spec.md), as
# the phrase being warned against, so a deny-list there reds on correct text.
# Enforced at review instead.


def test_acceptance_criteria_eval_has_required_shape_and_behaviour() -> None:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    matches = [entry for entry in data["evals"] if entry["id"] == "acceptance-criteria-discipline"]
    assert len(matches) == 1
    entry = matches[0]
    assert set(entry) == {"id", "prompt", "expected_output", "assertions"}
    assert len({candidate["id"] for candidate in data["evals"]}) == len(data["evals"])
    assert "bundles two contracts" in entry["prompt"]
    assert "no stated firing order" in entry["prompt"]
    assert "owned by another document" in entry["prompt"]
    assert "split" in entry["expected_output"].lower()
    assert "input that makes the limit fire first" in entry["expected_output"]
    assert "enforcement mechanism" in entry["expected_output"]
    assert "cite the owning document and identifier" in entry["expected_output"]
    assert any("split" in assertion.lower() for assertion in entry["assertions"])
    assert any("input" in assertion.lower() and "enforcement" in assertion.lower() for assertion in entry["assertions"])
    assert any("cite" in assertion.lower() and "rather than restat" in assertion.lower() for assertion in entry["assertions"])


def test_step_pointers_name_headings_that_still_exist() -> None:
    """A renumbering that strands step 4's pointers must red, not pass silently.

    The pointer text is pinned above, but text alone cannot notice that step 8
    became step 9. Anchor both ordinals to the headings they name.

    Inserting the shaping-review gate as step 6 pushed every later step down
    one, so citation discipline is now step 9. This test caught that; the
    pointer and this anchor moved together.
    """
    body = SKILL.read_text(encoding="utf-8")
    assert "5. Fill in the plan second" in body
    assert "9. **Keep the spec the single source of truth" in body


def test_corpus_absence_rule_precedes_the_sign_off_gate() -> None:
    """The rule must enter the Unverified list before that list is signed off.

    It once shipped below the gate, where the assumption it records could never
    reach the wait loop it exists for: textually present, operationally dead.
    Every phrase pin stayed green through that, because a pin proves a sentence
    exists in a file and nothing about where in the file it sits.
    """
    body = flattened(SKILL)
    rule = "When no corpus of real inputs is reachable"
    gate = "Surface the Unverified list and wait"
    assert rule in body and gate in body
    assert body.index(rule) < body.index(gate), (
        "the corpus-absence rule must precede the sign-off gate, "
        "or the assumption it records cannot enter the list being signed off"
    )


def test_spec_review_adjudicates_every_report_before_action() -> None:
    """A raw finding or clean claim must never drive the authoring loop."""
    body = flattened(SKILL)
    report = "Every completed reviewer report, including one that claims clean"
    gateway = "passes through `finding-adjudicator` before the author classifies or acts on it"
    repair = "Before repairing each sustained finding"
    assert report in body
    assert gateway in body
    assert repair in body
    assert body.index(report) < body.index(gateway) < body.index(repair)
    assert "Revise the spec or plan only from sustained findings" in body
    assert "Reuse its reachability predicate; do not restate or reimplement it here" in body


def test_spec_review_adjudication_has_an_executable_artifact_path() -> None:
    """The gateway must supply the adjudicator's validated path inputs."""
    body = flattened(SKILL)
    ignored = "prove `.context/reviews/` is ignored"
    persist = "persist the complete raw report"
    validate = "validate that artifact before dispatch"
    dispatch = "dispatch `finding-adjudicator` by the validated path"
    context = (
        "unchanged review target, structural scope, reviewer role, and governing "
        "authority paths"
    )
    consume = "Classify and act only on the paired adjudication artifact"
    for phrase in (ignored, persist, validate, dispatch, context, consume):
        assert phrase in body
    assert body.index(ignored) < body.index(persist) < body.index(validate)
    assert body.index(validate) < body.index(dispatch) < body.index(consume)


def test_spec_review_origin_is_binary_and_unresolved_history_stops() -> None:
    body = flattened(SKILL)
    assert "mark its origin as `draft-origin` or `prior-round-repair`" in body
    assert "If the available review history cannot establish either origin, stop and ask the owner" in body
    assert "Unresolved origin never authorizes a repair" in body


def test_green_gate_claim_is_bounded_by_scope_and_blind_spot() -> None:
    body = flattened(SKILL)
    assert "state what the gate proves and one relevant blind spot" in body
    assert "[`lint-spec-status.py`](../work-loop/scripts/lint-spec-status.py) module contract" in body
    assert "Do not copy its invariant list into this skill" in body


def test_spec_review_triage_eval_has_required_shape_and_behaviour() -> None:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    matches = [
        entry for entry in data["evals"] if entry["id"] == "spec-review-triage-before-repair"
    ]
    assert len(matches) == 1
    entry = matches[0]
    assert set(entry) == {"id", "prompt", "expected_output", "assertions"}
    assert len({candidate["id"] for candidate in data["evals"]}) == len(data["evals"])
    assert "previous repair" in entry["prompt"]
    assert "unreachable route" in entry["prompt"]
    assert "green spec-status lint" in entry["prompt"]
    expected = entry["expected_output"]
    assert "adjudicator" in expected
    assert "sustained" in expected
    assert "draft-origin" in expected
    assert "prior-round-repair" in expected
    assert "blind spot" in expected
    assert "persist" in expected
    assert "validated path" in expected
    assert "paired adjudication artifact" in expected
    assert any("clean" in assertion.lower() for assertion in entry["assertions"])
    assert any("origin" in assertion.lower() for assertion in entry["assertions"])
    assert any("blind spot" in assertion.lower() for assertion in entry["assertions"])
    assert any("validated path" in assertion.lower() for assertion in entry["assertions"])


def test_planning_guide_explains_spec_review_triage() -> None:
    body = flattened(PLANNING_GUIDE)
    assert "Every completed report, including a clean claim, goes through `finding-adjudicator`" in body
    assert "Only sustained findings can change the spec or plan" in body
    assert "`draft-origin` or `prior-round-repair`" in body
    assert "unresolved origin stops for your direction" in body
    assert "what that gate proves and one relevant blind spot" in body


def test_core_explanation_places_adjudication_before_repair() -> None:
    body = flattened(CORE_EXPLANATION)
    assert "**`finding-adjudicator`**" in body
    report = "Every completed spec-review report, including a clean claim"
    gateway = "passes through `finding-adjudicator` before it can change the spec or plan"
    assert report in body
    assert gateway in body
    assert body.index(report) < body.index(gateway)
