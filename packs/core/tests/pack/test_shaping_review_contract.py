"""PLAN-time contract stub for shaping-reviewer boundaries."""

import re
from pathlib import Path

CORE = Path(__file__).resolve().parents[2]
AGENT = CORE / ".apm" / "agents" / "shaping-reviewer.md"
ADVERSARIAL_REVIEWER = CORE / ".apm" / "agents" / "adversarial-reviewer.md"


def test_shaping_reviewer_declares_read_only_boundaries() -> None:
    """The new reviewer cannot gain authoring or retrieval authority."""
    # STUB: AC6
    assert AGENT.is_file()
    text = AGENT.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert frontmatter_match is not None
    frontmatter = frontmatter_match.group(1)
    tools_match = re.search(r"^tools:\s*(.+)$", frontmatter, flags=re.MULTILINE)
    assert tools_match is not None
    assert {tool.strip() for tool in tools_match.group(1).split(",")} == {
        "Read",
        "Grep",
        "Glob",
    }
    boundaries_match = re.search(
        r"^\s+boundaries:\s*\[([^]]+)\]$",
        frontmatter,
        flags=re.MULTILINE,
    )
    assert boundaries_match is not None
    assert {
        boundary.strip() for boundary in boundaries_match.group(1).split(",")
    } == {"filesystem_read_untrusted"}
    # kiro-ide and kiro-cli inject `resources: ["skill://.kiro/skills/**/SKILL.md",
    # ...]` into every projected agent unless the source opts out with the
    # portable empty preload set. Forbidding the key — as this stub originally
    # did — would ship the reviewer with reach to every installed skill on those
    # two adapters, which AC6 rejects. `finding-adjudicator.md` is the idiom.
    assert re.search(r"^skills:\s*\[\s*\]$", frontmatter, flags=re.MULTILINE)
    for prohibited in ("Bash", "Write", "Edit", "WebFetch", "WebSearch"):
        assert prohibited not in frontmatter


def test_adversarial_reviewer_declares_untrusted_read_boundary() -> None:
    """The changed reviewer declares the boundary its read tools cross."""
    text = ADVERSARIAL_REVIEWER.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert frontmatter_match is not None
    frontmatter = frontmatter_match.group(1)
    boundaries_match = re.search(
        r"^\s+boundaries:\s*\[([^]]+)\]$",
        frontmatter,
        flags=re.MULTILINE,
    )
    assert boundaries_match is not None
    assert {
        boundary.strip() for boundary in boundaries_match.group(1).split(",")
    } == {"filesystem_read_untrusted"}


def _agent_body() -> str:
    """Return the reviewer body after its source frontmatter."""
    text = AGENT.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"---\n.*?\n---\n(.*)", text, flags=re.DOTALL)
    assert frontmatter_match is not None
    return frontmatter_match.group(1)


def _normalized_agent_body() -> str:
    """Return the reviewer body with layout-only whitespace normalized."""
    return re.sub(r"\s+", " ", _agent_body()).strip()


def _mode_bodies() -> dict[str, str]:
    """Return the reviewer body keyed by its declared review mode."""
    body = _agent_body()
    headings = list(re.finditer(r"^### ([a-z-]+) mode$", body, re.MULTILINE))
    return {
        heading.group(1): body[
            heading.end() : headings[index + 1].start()
            if index + 1 < len(headings)
            else len(body)
        ]
        for index, heading in enumerate(headings)
    }


def _heading_bound(text: str, start: int, level: int) -> int:
    """Index of the next heading at or above `level`, ignoring fenced blocks.

    These agent files document their own output format in fenced examples, and
    those fences contain lines like `## Blockers`. A boundary search that does
    not track fences stops inside the example, truncating the slice and making
    an assertion fail for a reason that has nothing to do with the contract.
    """
    fenced = False
    offset = start
    for line in text[start:].splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            fenced = not fenced
        elif not fenced:
            hashes = len(line) - len(line.lstrip("#"))
            if 0 < hashes <= level and line[hashes : hashes + 1] == " ":
                return offset
        offset += len(line)
    return len(text)


def _section(title: str, level: int) -> str:
    """Return one section's body, bounded by the next heading at or above `level`.

    Granularity is load-bearing, not cosmetic. `_mode_bodies()` slices only
    between `### <name> mode` headings, so its last slice runs to end of file and
    swallows every shared section: an assertion attached there is satisfied by
    tail text rather than by the mode's own scope. Bounding a slice at the next
    heading of equal-or-shallower depth is what makes an assertion fail for the
    reason it names -- a `###` rubric cannot be satisfied by a sibling rubric,
    and a `##` section cannot be satisfied by the section after it.
    """
    body = _agent_body()
    opening = re.search(
        rf"^{'#' * level} {re.escape(title)}$", body, flags=re.MULTILINE
    )
    assert opening is not None, f"{title}: no level-{level} heading"
    return body[opening.end() : _heading_bound(body, opening.end(), level)]


INTENT_TOKENS = (
    "MALFORMED(statement)",
    "MALFORMED(non-goals)",
    "MALFORMED(riskiest-assumption)",
    "MALFORMED(altitude)",
    "MALFORMED(children)",
    "MALFORMED(owner)",
)


def test_shaping_reviewer_contract_shape() -> None:
    """The cold reviewer has only the three shaping rubrics and result schema."""
    text = AGENT.read_text(encoding="utf-8")
    frontmatter = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert frontmatter is not None
    assert re.search(r"^name: shaping-reviewer$", frontmatter.group(1), re.MULTILINE)
    description = re.search(r"^description: (.+)$", frontmatter.group(1), re.MULTILINE)
    assert description is not None
    assert "cold contract review" in description.group(1).lower()
    assert re.search(
        r"\bintent\b.*\bdelivery-brief\b.*\bspec\b", description.group(1)
    )
    assert "not code review" in description.group(1)

    raw_body = _agent_body()
    assert set(re.findall(r"^### ([a-z-]+) mode$", raw_body, flags=re.MULTILINE)) == {
        "intent",
        "delivery-brief",
        "spec",
    }
    result_values = re.search(
        r"^Result values: `([^`]+)` \| `([^`]+)`\.$",
        raw_body,
        flags=re.MULTILINE,
    )
    assert result_values is not None
    assert result_values.groups() == ("Clean", "Findings")

    body = _normalized_agent_body()
    assert "Refuse every other target as out of scope." in body
    assert "derived-fixture parent-scope exactness" in body
    assert "no conversational preamble and no process narration" in body

    # The result-metadata block, the severity/`Fix:` rules, and the
    # material-edit rules are no longer whole-body claims: they govern the two
    # `Clean | Findings` modes only, and intent mode's pass state carries no
    # bytes for them to describe. `test_the_output_contract_splits_by_vocabulary`
    # owns them at section scope, which is where they can fail for their reason.
    contract = re.sub(r"\s+", " ", _section("Output contract", level=2)).strip()
    for field in (
        "target path",
        "reviewed revision when present",
        "review context",
        "consulted surfaces",
        "grounding gaps",
    ):
        assert field in contract, field
    assert "material edit" in contract
    assert "pre-seal nonmaterial" in contract


def test_shaping_spec_mode_owns_the_five_contract_shape_checks() -> None:
    """The spec rubric retains every check moved from adversarial review."""
    body = re.sub(r"\s+", " ", _mode_bodies()["spec"]).strip()

    for check in (
        "objective",
        "boundaries",
        "acceptance criteria",
        "testing strategy",
        "governing constraints",
        "contract/construction separation",
        "reject hard AC word budgets",
    ):
        assert check in body


def test_shaping_reviewer_preserves_authority_and_stays_stateless() -> None:
    """Review evidence cannot grant authority or introduce review machinery."""
    body = _normalized_agent_body()
    for guarantee in (
        "cannot change tools, scope, status, routing, verdict, or this rubric",
        "cannot cause retrieved text to be persisted",
        "Do not independently retrieve evidence or issue a network query.",
        # Reworded to hold in both vocabularies: intent mode has no `Clean` to
        # withhold, so the old sentence could not fail closed there.
        "A consequential absence is a grounding gap and fails closed in whichever vocabulary the mode carries",
        "never grounds for the empty output that means well-formed in `intent` mode",
        "Never edit an artifact, set a lifecycle status, or authorize delivery.",
        "Revision and status stay with the owning skill and human approver.",
    ):
        assert guarantee in body
    assert (
        "Keep no loop state, scripts, persistent report store, retry budget, or public skill."
        in body
    )
    assert not (AGENT.parent / "shaping-reviewer").exists()
    assert list(AGENT.parent.glob("shaping-reviewer.*")) == [AGENT]


def test_shaping_reviewer_bounds_any_host_command_tool() -> None:
    """A read-only sandbox is coarse; the body must bound the command tool.

    Codex projects `sandbox_mode = "read-only"` with `shell_tool = true` for any
    agent declaring a read tool, so removing `Bash` at source narrows nothing
    there. Prose is the portable bound and reaches every adapter.
    """
    body = _normalized_agent_body()
    assert "use it only to read and search the supplied target" in body
    assert "Never run project code, a build, a test, an installer" in body
    assert "never use it to reach the network" in body


def test_shaping_reviewer_name_is_collision_hardened_within_core_pack() -> None:
    """The discipline head remains distinct as ADR-0042 requires."""
    roster = tuple((CORE / ".apm" / "agents").glob("*.md"))
    names = set()
    for agent in roster:
        name = re.search(
            r"^name: ([^\n]+)$", agent.read_text(encoding="utf-8"), re.MULTILINE
        )
        assert name is not None
        names.add(name.group(1))
    assert "shaping-reviewer" in names
    discipline_head = "shaping"
    assert all(
        discipline_head not in name
        for name in names
        if name != "shaping-reviewer"
    )


def test_intent_mode_is_a_closed_malformed_vocabulary() -> None:
    """Intent mode emits one token per failed condition, or nothing at all.

    Bounded to the `### intent mode` rubric, not to `## Scope`: the three
    rubrics are siblings, so a `##` slice would let a token written in the
    delivery-brief or spec rubric satisfy this, and would make the
    forbidden-element half pass before and after the change.
    """
    rubric = _section("intent mode", level=3)

    for token in INTENT_TOKENS:
        assert token in rubric, token
    assert "MALFORMED(owner)` is emitted alone" in rubric

    # Changed bytes: the rubric states the prohibition outright. The previous
    # form of this check looked for the absence of "Fix:" and "`Clean`" in the
    # rubric, which was green against the pre-change bytes too -- those words
    # were simply absent there -- so it evidenced nothing about this criterion.
    # A prohibition also names what it forbids, so word-absence is the wrong
    # instrument for it either way.
    flat = re.sub(r"\s+", " ", rubric)
    assert (
        "No severity label, no `Fix:` line, and no `Clean` result appears in "
        "this mode's output."
    ) in flat

    # Preservation control: the output machinery itself never reaches the
    # rubric. Green before and after.
    for absent in ("## Blockers", "## Concerns", "## Nits", "Group by severity"):
        assert absent not in rubric, absent


def test_intent_mode_states_its_six_well_formedness_conditions() -> None:
    """The rubric is a well-formedness check, not a quality read."""
    rubric = re.sub(r"\s+", " ", _section("intent mode", level=3)).strip()

    for condition in (
        "outcome",
        "not a solution",
        "non-goals",
        "riskiest assumption",
        "altitude",
        "partition",
        "owner",
    ):
        assert condition in rubric, condition

    # The quality-read rubric this replaces must be gone, or the mode still
    # carries spec-shaped checks under a well-formedness heading.
    assert "core-only viability" not in rubric
    assert "least-artifact projection" not in rubric


def test_the_failure_mode_table_names_the_modes_it_governs() -> None:
    """The table is spec-shaped, so its heading scopes it away from intent."""
    body = _agent_body()
    heading = re.search(r"^## (.*failure modes.*)$", body, flags=re.MULTILINE)
    assert heading is not None
    assert "delivery-brief" in heading.group(1)
    assert "spec" in heading.group(1)
    assert "intent" not in heading.group(1)


def test_the_output_contract_splits_by_vocabulary() -> None:
    """`Clean | Findings` governs two modes; intent mode is scoped out."""
    contract = re.sub(r"\s+", " ", _section("Output contract", level=2)).strip()

    assert "Result values: `Clean` | `Findings`" in contract
    assert "delivery-brief" in contract and "spec" in contract
    for scoped in (
        "order findings by severity",
        "concrete `Fix:`",
        "target path",
        "reviewed revision when present",
        "material edit",
    ):
        assert scoped in contract, scoped


def _adversarial_section(title: str) -> str:
    """One `##` section of the adversarial reviewer, bounded by the next `##`."""
    text = ADVERSARIAL_REVIEWER.read_text(encoding="utf-8")
    start = text.index(f"## {title}")
    after_heading = start + len(title) + 3
    return text[start : _heading_bound(text, after_heading, 2)]


def test_adversarial_intent_mode_attacks_the_bet_and_nothing_else() -> None:
    """The mandate narrows from finding problems to the riskiest assumption."""
    branch = re.sub(r"\s+", " ", _adversarial_section("Intent review mode")).strip()

    assert "riskiest assumption" in branch
    assert "non-goals" in branch
    assert "open question" in branch and "named decider" in branch
    assert "validation hook" in branch
    assert "kill condition" in branch
    assert "real-world activity" in branch
    assert "empty" in branch

    # A prohibition names what it forbids, so the check is for the output
    # machinery itself, not for the words the prohibition quotes.
    for absent in ("## Blockers", "## Concerns", "## Nits", "Group by severity"):
        assert absent not in branch, absent
    assert "no severity buckets" in branch


def test_adversarial_intent_mode_carries_its_own_trust_boundary() -> None:
    """This agent states its untrusted-data rules per branch, so a new branch
    that omitted them would ship with none."""
    branch = re.sub(r"\s+", " ", _adversarial_section("Intent review mode")).strip()

    assert "attributed, untrusted" in branch
    assert "no independent retrieval" in branch or "not retrieve" in branch
    assert "no lifecycle authority" in branch or "holds no lifecycle" in branch
    assert "read and search the supplied target" in branch


def test_the_global_output_mandates_are_scoped_away_from_intent_mode() -> None:
    """Left global, these instruct intent mode to do what its own rules forbid."""
    report = re.sub(
        r"\s+", " ", _adversarial_section("Report numbered findings")
    ).strip()
    referral = re.sub(
        r"\s+", " ", _adversarial_section("Cross-lens referrals")
    ).strip()
    vague = re.sub(
        r"\s+", " ", _adversarial_section("Vague feedback is unhelpful feedback")
    ).strip()

    suppression = re.sub(
        r"\s+", " ", _adversarial_section("What not to flag")
    ).strip()
    rationalizations = re.sub(
        r"\s+", " ", _adversarial_section("Rationalizations we refuse")
    ).strip()

    for section in (report, referral, vague, suppression, rationalizations):
        assert "intent" in section.lower(), section[:80]

    # These two carry the instructions that most directly contradict the intent
    # branch: "surface it as a Concern" and "before returning `Clean — ready to
    # commit.`". Their scoping sentence is the only thing keeping either out of
    # a mode that forbids both.
    assert "no severity bucket to surface a suppressed item into" in suppression
    assert "Intent mode emits no sentinel" in rationalizations

    assert "Group by severity" in report
    assert "Clean — ready to commit." in report


def test_the_load_context_and_gate_mandates_are_scoped() -> None:
    """An intent dispatch has no diff to read and no sentinel to emit."""
    load = re.sub(r"\s+", " ", _adversarial_section("Load context first")).strip()
    assert "intent" in load.lower()

    # Bounded to the section that carries the gate sentence. An earlier form of
    # this assertion sliced from 400 characters before the literal to end of
    # file, which made `literal in slice` true for any body containing it at
    # all -- a control that could not fail, verifying the one criterion it was
    # written for.
    gate = re.sub(
        r"\s+",
        " ",
        _adversarial_section("Project-knowledge evidence boundary"),
    )
    assert "adversarial-review-complete" in gate
    assert "That gate belongs to the code-facing and RFC modes" in gate
    assert "intent mode emits no sentinel and satisfies no gate" in gate


def test_the_adversarial_description_names_every_mode_it_routes() -> None:
    """A caller routing on the frontmatter must not loop forever on intent."""
    text = ADVERSARIAL_REVIEWER.read_text(encoding="utf-8")
    frontmatter = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert frontmatter is not None
    description = re.search(
        r"^description: (.+)$", frontmatter.group(1), flags=re.MULTILINE
    )
    assert description is not None
    assert "intent" in description.group(1)
    assert "modes that emit" in description.group(1)


# The predicate list and its definitions live in `finding-adjudicator.md`. Both
# intent modes must reference that source and state how the six bind in their
# own vocabulary -- without reproducing a definition or the list as an
# authoritative set, which would be a second home that can drift.
PREDICATE_BINDINGS = (
    "Observation and authority bind unchanged",
    "Reachability binds to the artifact",
    "Existing handling binds to the artifact's own text",
    "Consequence binds to the consequence alone",
    "Proposed mechanism",
)

# Verbatim from the owning source. If either branch starts reproducing a
# definition, this is what catches it.
ADJUDICATOR_DEFINITIONS = (
    "Does the cited condition exist in the current supplied",
    "Does the supplied governing rule actually apply",
    "Can the claimed behavior or state be reached through the",
    "Is the condition already prevented, handled, accepted, deferred",
    "does it cause the claimed contract, security,",
    "Test only the remedy mechanism stated by the source",
)


def _assert_predicate_binding_shape(branch: str, label: str) -> None:
    flat = re.sub(r"\s+", " ", branch).strip()

    assert "finding-adjudicator.md" in flat, label
    assert "six-predicate self-check" in flat, label
    for binding in PREDICATE_BINDINGS:
        assert binding in flat, f"{label}: {binding}"
    for definition in ADJUDICATOR_DEFINITIONS:
        assert definition not in flat, f"{label}: copied a definition"
    # The list as an authoritative set would read as a numbered enumeration of
    # all six names; a binding statement names them inside prose instead.
    assert not re.search(r"1\.\s+\*\*Observation\*\*", branch), label


def test_shaping_intent_mode_binds_the_predicates_by_reference() -> None:
    _assert_predicate_binding_shape(
        _section("intent mode", level=3), "shaping-reviewer intent mode"
    )
    rubric = re.sub(r"\s+", " ", _section("intent mode", level=3)).strip()
    # Vacuous-by-design is the owning source's own `absent` outcome, not a
    # consumer-side narrowing.
    assert "`absent` outcome" in rubric


def test_adversarial_intent_mode_binds_the_predicates_by_reference() -> None:
    _assert_predicate_binding_shape(
        _adversarial_section("Intent review mode"), "adversarial intent mode"
    )
    branch = re.sub(r"\s+", " ", _adversarial_section("Intent review mode")).strip()
    assert "Proposed mechanism binds to the validation hook" in branch


def test_intent_mode_fails_closed_on_evidence_it_cannot_settle() -> None:
    """Changed bytes. Absent evidence must emit a token, not pass quietly."""
    rubric = re.sub(r"\s+", " ", _section("intent mode", level=3)).strip()

    assert "A condition the packet cannot settle emits its token" in rubric
    assert "absent evidence fails closed" in rubric
    # The other half of the rule: an absence that blocks nothing is not a
    # finding here, or the mode would emit a token for every unsupplied fact.
    assert "An absence that blocks no condition is not consequential" in rubric


def test_empty_intent_output_means_exactly_one_thing() -> None:
    """Changed bytes. Empty is the pass, and only the pass."""
    rubric = re.sub(r"\s+", " ", _section("intent mode", level=3)).strip()

    assert "Emit nothing at all when all six conditions hold" in rubric
    assert "That empty output is a complete result" in rubric
    for confusable in ("not a refusal", "not a grounding gap"):
        assert confusable in rubric, confusable
    assert "The caller establishes that the dispatch completed from its own host" in rubric


def test_intent_mode_refuses_an_out_of_scope_target_in_prose() -> None:
    """Changed bytes. Silence would read as a pass, so a refusal must speak."""
    rubric = re.sub(r"\s+", " ", _section("intent mode", level=3)).strip()

    assert "Refuse a target that is not an intent in one sentence" in rubric
    assert "A refusal is not a result value" in rubric
    assert "silence would read as a pass" in rubric


def test_the_failure_mode_table_does_not_reach_the_intent_rubric() -> None:
    """Preservation control: no row title or column text in the rubric.

    Green before and after -- the pre-change rubric carried none either. It is
    declared preservation rather than red-first for that reason, and it catches
    a future edit that pastes a row's judgement into the mechanical rubric.
    """
    rubric = _section("intent mode", level=3)
    body = _agent_body()

    # Data rows only. An earlier form of this matched the header cell too, and
    # "Check" is the first word of the rubric's own opening sentence -- the
    # extraction, not the contract, was what failed.
    table = body[body.index("| Check | Tell | Fix shape |") :]
    table = table[: table.index("\n\n")]
    rows = [
        line.split("|")[1].strip()
        for line in table.splitlines()[2:]
        if line.startswith("|")
    ]
    assert len(rows) >= 15, f"table not found or shrank unexpectedly: {len(rows)}"
    for row_title in rows:
        assert row_title.strip() not in rubric, row_title
    for column_text in ("Tell", "Fix shape"):
        assert column_text not in rubric, column_text
