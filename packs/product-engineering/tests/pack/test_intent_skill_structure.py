"""Structure, route mode, lifecycle map, and next-step contracts for `intent`."""

from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILLS = PACK_ROOT / ".apm" / "skills"
INTENT = SKILLS / "intent"
SKILL = INTENT / "SKILL.md"
REFERENCES = INTENT / "references"
EVAL_QUERIES = INTENT / "evals" / "eval_queries.json"
MODES = ("frame", "de-risk", "decompose")
# Source skills the fold retired; no `intent` file may name them.
RETIRED_SHAPING_SKILLS = (
    "frame-intent",
    "de-risk-intent",
    "decompose-intent",
)
# A merged positive query is owned by the mode that now carries its skill.
FOLDED_OWNERS = tuple(f"intent {mode}" for mode in MODES)

# Names a skill may carry that are not skill references.
ROUTES = {
    "short": "intent frame",
    "longer": "frame-situation",
    "supervised": "discovery-loop",
}
OUT_OF_STAGE = ("bug-fix", "work-intake", "architect-design")


def _flat(text: str) -> str:
    """Collapse presentation-only whitespace."""
    return " ".join(text.split())


def _section(text: str, heading: str, level: str = "##") -> str:
    """Return one Markdown section, bounded by the next heading of its level."""
    match = re.search(
        rf"^{re.escape(level)} {re.escape(heading)}\n(?P<body>.*?)(?=^{re.escape(level)} |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, f"missing section {heading!r}"
    return match.group("body")


def _frontmatter() -> dict[str, str]:
    """Top-level scalar keys of the skill's YAML frontmatter."""
    match = re.match(r"\A---\n(?P<fm>.*?)\n---\n", SKILL.read_text("utf-8"), re.DOTALL)
    assert match
    return {
        m.group(1): m.group(2)
        for m in re.finditer(r"^([a-z-]+):\s*(.+)$", match.group("fm"), re.MULTILINE)
    }


def _numbered_names(section: str) -> list[str]:
    """First backticked token of each top-level numbered item."""
    return re.findall(r"^\d+\. `([^`]+)`", section, re.MULTILINE)


def test_sections_appear_in_order_and_modes_table_has_four_rows() -> None:
    body = SKILL.read_text("utf-8")
    headings = [
        h
        for h in re.findall(r"^## (.+)$", body, re.MULTILINE)
        if h != "Output rendering"
    ]
    assert headings == [
        "When to invoke",
        "The intent lifecycle",
        "Route mode",
        "Modes",
    ]
    modes = _section(body, "Modes")
    rows = [
        line for line in modes.splitlines() if line.startswith("|") and "---" not in line
    ][1:]
    assert [r.split("|")[1].strip(" `") for r in rows] == ["route", *MODES]
    assert len([r for r in modes.splitlines() if r.startswith("| ---")]) == 1


def test_each_verb_row_names_its_reference_file() -> None:
    modes = _section(SKILL.read_text("utf-8"), "Modes")
    for mode in MODES:
        row = next(line for line in modes.splitlines() if line.startswith(f"| `{mode}`"))
        assert f"`references/{mode}.md`" in row
        assert f"{mode}.md" in {path.name for path in REFERENCES.iterdir()}


def test_description_fits_and_names_the_verbs_as_whole_words() -> None:
    description = _frontmatter()["description"]
    assert len(description) <= 1024
    for word in ("frame", "de-risk", "decompose"):
        assert re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", description), word
    for target in ("intake-intent", "new-spec", "frame-situation"):
        assert f"`{target}`" in description


def test_frontmatter_pre_approves_no_tools_and_boundaries_are_exact() -> None:
    """No `allowed-tools`: on Claude Code it pre-approves, so no mode writes unprompted."""
    assert "allowed-tools" not in _frontmatter()
    fm = re.match(r"\A---\n(.*?)\n---\n", SKILL.read_text("utf-8"), re.DOTALL).group(1)
    block = fm.split("boundaries:\n", 1)[1]
    assert re.findall(r"^\s+- (\S+)", block, re.MULTILINE) == [
        "filesystem_write",
        "filesystem_read_untrusted",
    ]
    assert _frontmatter()["name"] == "intent"


def test_route_mode_names_three_routes_and_three_out_of_stage_owners() -> None:
    route = _section(SKILL.read_text("utf-8"), "Route mode")
    rows = [
        line.split("|")
        for line in route.splitlines()
        if line.startswith("| ") and "---" not in line
    ][1:]
    assert {r[1].strip(): r[3].strip(" `") for r in rows} == ROUTES
    flat = _flat(route)
    for owner in OUT_OF_STAGE:
        assert f"`{owner}`" in flat
    named = set(re.findall(r"`([a-z]+(?:-[a-z]+)+)`", route))
    assert named == {"frame-situation", "discovery-loop", *OUT_OF_STAGE}


def test_route_mode_text_matches_none_of_the_forbidden_stems() -> None:
    route = _section(SKILL.read_text("utf-8"), "Route mode")
    stems = (
        r"writ|save|saving|creat|remember|retr(y|ie)|gate|record|persist|updat|"
        r"append|stor|edit"
    )
    assert re.findall(rf"\b(?:{stems})", route, re.IGNORECASE) == []


def test_route_mode_offers_instead_of_acting_and_asks_one_question() -> None:
    route = _flat(_section(SKILL.read_text("utf-8"), "Route mode"))
    assert "where it starts on the lifecycle map" in route
    assert "offer its first step as an option" in route
    assert "Do not start the step" in route
    assert "ask one question" in route


# The files the fold moved under `intent/`, plus the three mode files. A rename
# or deletion here must be a deliberate edit to this list.
MOVED_FILES = (
    "assets/intent-template.md",
    "examples/feature-intent-to-brief.md",
    "references/agentbundle-layout.md",
    "references/current-state-inputs.md",
    "references/digital-experience-contract.md",
    "references/intent-model.md",
    "references/jtbd-job-categories.md",
    "references/kill-condition.md",
    "references/knowledge-surfaces.md",
    "references/prototype-approach.md",
    "references/recursive-decomposition.md",
    "references/reversibility-triage.md",
    "references/scale-intake.md",
    "references/tracker-projection.md",
) + tuple(f"references/{mode}.md" for mode in MODES)


def test_moved_files_land_under_intent() -> None:
    """The shipped files under `intent/` are exactly the moved files and mode files."""
    assert len(MOVED_FILES) == len(set(MOVED_FILES))
    shipped = {
        path.relative_to(INTENT).as_posix()
        for tree in (REFERENCES, INTENT / "assets", INTENT / "examples")
        for path in tree.rglob("*")
        if path.is_file()
    }
    assert shipped == set(MOVED_FILES), sorted(shipped ^ set(MOVED_FILES))


# --- lifecycle map -----------------------------------------------------------


def test_longer_route_matches_frame_situation_step_four() -> None:
    longer = _section(SKILL.read_text("utf-8"), "Longer route", "###")
    situation = (SKILLS / "frame-situation" / "SKILL.md").read_text("utf-8")
    step = _flat(situation.split("**4. Recommend entry point.**", 1)[1].split(
        "Recommend where to enter", 1
    )[0])
    sequence = step.split("PE six-step sequence:", 1)[1].split(".", 1)[0]
    expected = [re.sub(r"[^a-z-]", "", n) for n in sequence.split("→")]
    # `frame-situation` calls the fourth step "validate"; the map shows `de-risk`.
    assert expected[3] == "validate"
    expected[3] = "de-risk"
    assert _numbered_names(longer) == expected


def test_short_and_supervised_routes_and_stage_kinds() -> None:
    life = _section(SKILL.read_text("utf-8"), "The intent lifecycle")
    short = _section(life, "Short route", "###")
    flat = _flat(short)
    for stage in ("`frame` (intent mode)", "`de-risk` (intent mode)", "`decompose` (intent mode)"):
        assert stage in flat
    assert "Hand-off to build through `work-intake` (separate skill)" in flat
    supervised = _flat(_section(life, "Supervised route", "###"))
    assert "`discovery-loop` (separate skill)" in supervised
    longer = _flat(_section(life, "Longer route", "###"))
    assert longer.count("(separate skill)") == 5
    assert "`de-risk` (intent mode;" in longer


def test_review_gates_are_marked_where_they_fall() -> None:
    short = _section(SKILL.read_text("utf-8"), "Short route", "###")
    frame, rest = short.split("2. `de-risk`", 1)
    frame = _flat(frame)
    assert "`shaping-reviewer` intent-mode well-formedness check" in frame
    assert "gate when a review route is available, and optional otherwise" in frame
    assert "`adversarial-reviewer` intent-mode assumption read comes before `de-risk`" in frame
    assert "advisory" in frame
    handoff = _flat(rest.split("4. Hand-off", 1)[1])
    assert "`author-delivery-brief` for a brief and `new-spec` for a spec" in handoff
    order = [frame.index("`shaping-reviewer`"), frame.index("`adversarial-reviewer`")]
    assert order == sorted(order)


# --- orientation lines and Next sections -------------------------------------


def _mode(mode: str) -> str:
    """Return one mode reference's text, read from the `references/` listing."""
    path = next(path for path in REFERENCES.iterdir() if path.name == f"{mode}.md")
    return path.read_text("utf-8")


def test_each_mode_opens_with_an_orientation_line_that_matches_the_map() -> None:
    life = SKILL.read_text("utf-8")
    short = _numbered_names(_section(life, "Short route", "###"))
    longer = _numbered_names(_section(life, "Longer route", "###"))
    for mode in MODES:
        first = _mode(mode).split("\n\n")[1]
        assert first.startswith(f"Stage: `{mode}`"), first
        flat = _flat(first)
        assert "\n" not in first
        assert "short route" in flat
        assert "supervised route" in flat
        assert mode in short
        if mode in longer:
            assert "longer route it is" in flat, mode
        else:
            assert "longer route" in flat and "does not use it" in flat, mode
    # step positions are stated on each route that includes the mode
    assert "step 1 of 3" in _mode("frame")
    assert "step 2 of 3" in _mode("de-risk") and "step 4 of 6" in _mode("de-risk")
    assert "step 3 of 3" in _mode("decompose")


def _next(mode: str) -> str:
    text = _mode(mode)
    assert text.rstrip().split("\n## ")[-1].startswith("Next"), mode
    return _section(text, "Next")


def test_every_next_section_opens_with_the_discovery_loop_deferral() -> None:
    deferral = (
        "When `discovery-loop` or its `discovery-lead` agent called this mode, "
        "control returns to the loop's next gate and no offer is made."
    )
    for mode in MODES:
        first = _flat(_next(mode).strip().split("\n\n")[0])
        assert first == deferral, mode


def test_every_offer_is_a_known_stage_and_at_most_three_per_state() -> None:
    known = {"intent frame", "intent de-risk", "intent decompose", "place-bet",
             "work-intake", "shaping-reviewer", "adversarial-reviewer",
             "author-delivery-brief", "new-spec", "discovery-loop",
             "discovery-lead"}
    for mode in MODES:
        text = _next(mode)
        for token in re.findall(r"`([a-z-]+(?: [a-z-]+)?)`", text):
            if token in {"intent frame", "intent de-risk", "intent decompose"} or "-" in token:
                assert token in known, (mode, token)
        for bullet in re.split(r"^- ", text, flags=re.MULTILINE)[1:]:
            offers = set(re.findall(r"`(intent \w[\w-]*|place-bet|work-intake|shaping-reviewer|adversarial-reviewer)`", bullet))
            assert len(offers) <= 3, (mode, bullet)


def test_frame_next_states() -> None:
    text = _flat(_next("frame"))
    assert "No shaping review for the current revision, or a material edit invalidated the last one" in text
    assert "Recommend the `shaping-reviewer` intent-mode review" in text
    assert "A review finished with no unresolved `MALFORMED` token" in text
    assert "Recommend `intent de-risk` first. Also offer the `adversarial-reviewer` intent-mode read" in text
    assert "The review is unavailable, or its dispatch did not complete" in text
    assert "`Optional Core intent shaping review: unavailable`" in text
    assert "`Optional Core intent shaping review: dispatch did not complete`" in text
    assert "claim no review result" in text
    assert "only when `adversarial-reviewer` is installed" in text
    assert "already survived `intent de-risk`.** Offer `intent decompose`" in text
    assert "Offer it for no other bet" in text


def test_de_risk_next_offers_both_labelled_routes_and_decides_or_asks() -> None:
    text = _flat(_next("de-risk"))
    assert "`intent decompose` (short route)" in text
    assert "`place-bet` (longer route)" in text
    assert "Recommend the one for the route the conversation shows" in text
    assert "shows no route, recommend neither and ask which route applies" in text
    assert "**Kill.** Offer `intent frame`" in text
    # both offers sit on the lifecycle map
    life = SKILL.read_text("utf-8")
    assert "`place-bet`" in _section(life, "Longer route", "###")
    assert "`decompose`" in _section(life, "Short route", "###")


def test_decompose_next_names_but_does_not_run_the_owner_review_gates() -> None:
    text = _flat(_next("decompose"))
    assert "hand-off to build through `work-intake`" in text
    assert "run none of them here" in text
    assert "`author-delivery-brief`" in text and "`new-spec`" in text
    assert "Recommend `intent decompose` for a child, and also offer `intent frame` for a child" in text


def test_no_mode_reference_names_a_retired_skill() -> None:
    for path in INTENT.rglob("*.md"):
        text = path.read_text("utf-8")
        for retired in RETIRED_SHAPING_SKILLS:
            assert retired not in text, f"{path}: {retired}"


# --- Eval carry-over ---

INTAKE_NEGATIVES = (
    "Add this goal to the repo as a bare-bones intent: halve onboarding time for new admins",
    "Log a one-sentence intent for faster invoice approval in the repository, no framing needed",
    "Capture the stated outcome 'customers self-serve their plan changes' as a minimal intent file",
    "Register this outcome as a minimum viable intent so it is tracked: lift trial conversion by 10%",
    "Put the outcome we agreed, fewer failed payments, into the repo as a minimal intent record",
)


def _eval_queries() -> list[dict]:
    """Return the merged `intent` eval queries."""
    return json.loads(EVAL_QUERIES.read_text("utf-8"))


def test_merged_queries_have_no_duplicates_and_the_sources_are_gone() -> None:
    """The source-query carry-over was checked before deletion (ledger, AC-0016)."""
    merged = [q["query"] for q in _eval_queries()]
    assert len(merged) == len(set(merged))
    for source in RETIRED_SHAPING_SKILLS:
        assert not (SKILLS / source).exists(), source


def test_merged_queries_carry_a_mode_only_when_positive() -> None:
    for q in _eval_queries():
        if q["should_trigger"]:
            assert q.get("mode") in MODES, q
            assert q.get("owner") in FOLDED_OWNERS, q
        else:
            assert "mode" not in q, q
            assert q.get("owner") not in FOLDED_OWNERS, q


def test_merged_queries_hold_the_intake_intent_negatives() -> None:
    by_text = {q["query"]: q for q in _eval_queries()}
    for text in INTAKE_NEGATIVES:
        assert by_text[text]["should_trigger"] is False
        assert by_text[text]["owner"] == "intake-intent"
    assert len(INTAKE_NEGATIVES) >= 4
