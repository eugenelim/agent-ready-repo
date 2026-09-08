"""Acceptance-criteria authoring contracts for the new-spec skill."""

import json
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm/skills/new-spec/SKILL.md"
SPEC = PACK_ROOT / ".apm/skills/new-spec/assets/spec.md"
PLAN = PACK_ROOT / ".apm/skills/new-spec/assets/plan.md"
EVALS = PACK_ROOT / ".apm/skills/new-spec/evals/evals.json"
RUBRIC = PACK_ROOT / ".apm/skills/new-spec/references/spec-authoring-rubric.md"
# The brief quotes the rubric's altitude tell; the pair is pinned below.
BRIEF = PACK_ROOT.parents[1] / "docs/product/briefs/agent-authoring-input-quality.md"

# The rubric joins SOURCES so every pinned rule below also asserts its absence
# there. The rubric points at the owning surface for criterion shape; a future
# edit that pastes an owned rule into it reds here rather than at review.
SOURCES = {"skill": SKILL, "spec": SPEC, "plan": PLAN, "rubric": RUBRIC}
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
    # Two rules the rubric paraphrased on its first draft. Pinned here so a
    # future edit that reintroduces either phrasing reds rather than shipping a
    # second home for a rule SKILL.md owns.
    (
        "retcon-rationale",
        "skill",
        "Mixed tenses make an agent reading the spec guess wrong about what is current",
    ),
    (
        "disconfirming-evidence",
        "skill",
        "Take the cheapest disconfirming evidence before review.",
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
    for other_path in (SKILL, PLAN, RUBRIC):
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


def test_spec_review_accepts_only_exact_clean_before_adjudication() -> None:
    """Persistence is unconditional; an exact clean skips adjudication.

    That exception has exactly one clean sentence, no findings, and no footer;
    every other report dispatches.
    """
    body = flattened(SKILL)
    # 9b9d470ef superseded the previous contract; pin the current prose here.
    unconditional_persistence = (
        "Persist and validate every completed reviewer report first — persistence is unconditional"
    )
    strict_clean_exception = (
        "A report is clean when the clean sentence appears exactly once, no findings parse, "
        "and nothing else but blank lines surrounds it; that skips `finding-adjudicator`"
    )
    footer_dispatch = (
        "A report carrying a `## Not checked` footer always dispatches, because the footer is prose"
    )
    findings_or_malformed_dispatch = (
        "A report with findings dispatches; a malformed one is a loud stop"
    )
    repair = "Before repairing each sustained finding"
    for phrase in (
        unconditional_persistence,
        strict_clean_exception,
        footer_dispatch,
        findings_or_malformed_dispatch,
        repair,
    ):
        assert phrase in body
    assert (
        body.index(unconditional_persistence)
        < body.index(strict_clean_exception)
        < body.index(footer_dispatch)
        < body.index(findings_or_malformed_dispatch)
        < body.index(repair)
    )
    assert "Revise the spec or plan only from sustained findings" in body
    assert "Reuse its reachability predicate; do not restate or reimplement it here" in body


def test_spec_review_adjudication_has_an_executable_artifact_path() -> None:
    """The gateway must supply the adjudicator's validated path inputs."""
    body = flattened(SKILL)
    step = body.split("7. Spec-mode adversarial review.", 1)[1].split(
        "8. Update `docs/specs/README.md`", 1
    )[0]
    protocol = (
        "[`work-loop` pre-EXECUTE review protocol]"
        "(../work-loop/references/pre-execute-review.md)"
    )
    ignored = "prove `.context/reviews/` is ignored"
    persist = "persist the complete non-exact raw report"
    validate = "validate that artifact before dispatch"
    dispatch = "dispatch `finding-adjudicator` by the validated path"
    context = (
        "unchanged review target, structural scope, reviewer role, and governing "
        "authority paths"
    )
    consume = "Classify and act only on the paired adjudication artifact"
    for phrase in (protocol, ignored, persist, validate, dispatch, context, consume):
        assert phrase in body
    assert "../work-loop/references/finding-adjudication.md" not in step
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
    assert "pre-EXECUTE review protocol" in expected
    assert "validated path" in expected
    assert "paired adjudication artifact" in expected
    assert any("clean" in assertion.lower() for assertion in entry["assertions"])
    assert any("origin" in assertion.lower() for assertion in entry["assertions"])
    assert any("blind spot" in assertion.lower() for assertion in entry["assertions"])
    assert any("validated path" in assertion.lower() for assertion in entry["assertions"])
    assert any("pre-execute" in assertion.lower() for assertion in entry["assertions"])


RUBRIC_CLASSES = (
    "## 1. The design should have delegated",
    "## 2. The criterion cannot fail",
    "## 3. The criterion is unsatisfiable, or contradicts a sibling",
    "## 4. The criterion decays",
    "## 5. The criterion is too big",
    "## 6. The property is not mechanizable",
)


def test_rubric_classes_ship_in_precedence_order() -> None:
    """Order is the rubric's contract, not its formatting.

    Class 1 precedes the rest because no criterion craft repairs an obligation
    authored where an owner already exists. A heading-set assertion alone would
    stay green through a reordering that inverts that, so pin the offsets.
    """
    body = RUBRIC.read_text(encoding="utf-8")
    offsets = []
    for heading in RUBRIC_CLASSES:
        assert heading in body, f"missing rubric class heading: {heading}"
        offsets.append(body.index(heading))
    assert offsets == sorted(offsets), "rubric classes are out of precedence order"
    text = flattened(RUBRIC)
    assert "stop at the first that fires" in text
    assert "Class 1 precedes every other" in text
    assert "Shortening or single-homing a long restatement is the *wrong* fix" in text


def test_rubric_defers_criterion_shape_and_stays_authoring_guidance() -> None:
    """The rubric must route shape questions out and refuse reviewer use.

    Both are load-bearing: a rubric that restates shape rules creates a second
    home for them, and one handed to a reviewer becomes the nit source it
    exists to reduce.
    """
    text = flattened(RUBRIC)
    # Pin the deferral map, not a universal claim about it: an earlier draft
    # said "each class below points there", which was false for four of six.
    assert "Classes 2 and 5 defer criterion *shape* to `../assets/spec.md`" in text
    assert "classes 1, 3 and 6 defer their repair mechanics to `SKILL.md`" in text
    assert "class 4 owns its own clauses outright" in text
    # And pin that the rubric does not claim parity with the review check set.
    assert "as part of a **larger** cold check set" in text
    assert "working\nthese six is not parity with review" in RUBRIC.read_text(encoding="utf-8")
    assert "authoring guidance, not a review checklist" in text
    assert "The shape rule is not here." in text
    # The count threshold screens; it never refuses. Pin both halves.
    assert "never as a refusal" in text
    assert "a ceiling and a stall point, never a floor" in text


ALTITUDE_TELL = (
    "a design position, an evidence base, an inventory, or a governance concern "
    "rather than citing one"
)


def test_altitude_tell_lives_whole_in_the_rubric_and_nowhere_else() -> None:
    """The four-clause tell must survive its re-homing, and stay single-homed.

    Moving the three altitude tells out of the brief and into the rubric
    silently dropped the fourth clause, "or a governance concern", and left the
    brief quoting a third wording that matched neither. A phrase pin on the
    rubric alone did not notice, because a clause can go missing from the
    middle of the phrase it pins.

    So pin both halves of the contract the owning brief now declares: the whole
    clause list is present in the rubric, and the brief describes no part of the
    rubric's content, so the tell text must not appear there at all. Truncating
    the rubric reds the first assertion; pasting the tell back into the brief
    reds the second.
    """
    assert ALTITUDE_TELL in flattened(RUBRIC), (
        "the altitude tell lost a clause in its own home"
    )
    assert ALTITUDE_TELL not in flattened(BRIEF), (
        "the brief restates the rubric's tell; it must cite the class, not its text"
    )


# The owning brief declares that it describes no part of the rubric's content.
# Eight words is where that stops being a coincidence: at the time this guard
# landed the two files shared 3 seven-word runs (all incidental phrasing such as
# "an implementation loop with gates between") and 0 of eight or more.
RESTATEMENT_RUN_WORDS = 8


def test_the_brief_restates_no_run_of_the_rubrics_text() -> None:
    """Enforce the cut, not just perform it.

    Five review rounds produced nine findings about which document owned or
    described which rule, because each repair moved text and left a sentence
    describing where it went. The brief now declares it describes no part of the
    rubric's content; this makes that declaration checkable instead of another
    claim that can go stale.

    Named blind spot: a paraphrase short of the run length passes, and so does a
    restatement in any file other than these two. This catches verbatim drift
    between the declared owner and its brief, which is the failure that actually
    recurred.
    """
    rubric_words = flattened(RUBRIC).split()
    brief = flattened(BRIEF)
    n = RESTATEMENT_RUN_WORDS
    shared = sorted(
        {
            run
            for i in range(len(rubric_words) - n + 1)
            if (run := " ".join(rubric_words[i : i + n])) in brief
        }
    )
    assert not shared, (
        f"the brief restates {len(shared)} run(s) of {n}+ words from the rubric; "
        f"cite the class by number instead. First: {shared[0]!r}"
    )


def test_rubric_ships_derivations_and_cites_no_internal_locator() -> None:
    """Shipped pack guidance stays portable.

    A percentile of this catalogue's corpus is wrong for every adopter on day
    one, and an internal path does not resolve in an installed skill. So assert
    the derivation instruction is present, and that no repository-only locator
    is.

    Two named blind spots, both enforced at review instead. First, this checks
    *locators*, not figures: a bare-numeral assertion is not available because
    the rubric's own class headings (`## 1.` … `## 6.`) are numerals, so a
    repo-derived percentile written without a path would pass. Second, the
    locator tuple below is a sample of the prefixes seen in practice, not a
    closed set — the prohibition it enforces is stated generally, so a locator
    shape nobody has written yet passes.
    """
    text = flattened(RUBRIC)
    assert "Ship the derivation, not the value" in text
    assert "measure your own shipped corpus" in text
    # A deny-list of the repository-only prefixes seen in practice. It is a
    # sample, not a closed set: the prohibition it enforces is stated generally,
    # so a locator shape absent from this tuple still passes. Widen on sight.
    for locator in (
        "docs/",
        "guides/",
        "packs/",
        "packages/",
        "profiles/",
        "tools/",
        "tests/",
        "web/",
        "contracts/",
        ".context/",
        "workspace.toml",
        "Makefile",
        "AGENT_RULES.md",
        "AGENTS.md",
        "CONVENTIONS.md",
        "CHARTER.md",
        "ARCHITECTURE.md",
        "RFC-00",
        "ADR-00",
    ):
        assert locator not in text, f"internal locator in shipped guidance: {locator}"


def test_rubric_is_reachable_from_both_authoring_surfaces() -> None:
    """An unreferenced reference is content nobody reads."""
    skill_body = flattened(SKILL)
    assert (
        "[`references/spec-authoring-rubric.md`](references/spec-authoring-rubric.md)"
        in skill_body
    )
    assert "class 1 —" in skill_body
    spec_body = flattened(SPEC)
    assert "`references/spec-authoring-rubric.md`" in spec_body
    assert "This section owns criterion *shape*." in spec_body


def test_rubric_eval_has_required_shape_and_behaviour() -> None:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    matches = [
        entry
        for entry in data["evals"]
        if entry["id"] == "spec-authoring-rubric-classes-precede-criterion-shape"
    ]
    assert len(matches) == 1
    entry = matches[0]
    assert set(entry) == {"id", "prompt", "expected_output", "assertions"}
    assert len({candidate["id"] for candidate in data["evals"]}) == len(data["evals"])
    # The graded actor must be the author checking their own pre-seal draft.
    # A review posture would exercise the one use the rubric disclaims, so pin
    # the authoring frame, not just the seeded defects.
    assert "I am drafting" in entry["prompt"]
    assert "I have not sealed the contract yet" in entry["prompt"]
    assert "my own draft" in entry["prompt"]
    assert "Review these" not in entry["prompt"]
    # Each seeded defect must survive in the prompt, or the case stops grading it.
    for seeded in (
        "14 permissions",
        "build/audit-report.json",
        "No manifest in the audited set produces an unhandled exception",
        "path-traversal validation, deferred",
        "already owns",
    ):
        assert seeded in entry["prompt"], f"seeded defect dropped: {seeded}"
    expected = entry["expected_output"]
    for demand in (
        "an obligation authored where an owner already exists",
        "derivation that reads the registry",
        "regeneration mechanism",
        "holds on an empty audited set",
        "representative valid manifest",
        "named owner waiver",
    ):
        assert demand in expected, f"expected_output drops: {demand}"
    assert any("wrong-owner" in item and "before" in item for item in entry["assertions"])
    assert any("empty state" in item for item in entry["assertions"])
    assert any("word budget" in item for item in entry["assertions"])
