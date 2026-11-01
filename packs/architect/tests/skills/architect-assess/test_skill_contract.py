"""Contract tests for the progressive repository architecture assessment skill."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "architect-assess"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
CORPUS_ROOT = PACK_ROOT / "okf" / "architecture-lenses" / "concepts"


def _frontmatter(text: str) -> dict[str, object]:
    """Return parsed YAML frontmatter from a Markdown file."""

    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_activation_and_boundaries_route_current_state_assessment() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    metadata = _frontmatter(text)
    assert metadata["name"] == "architect-assess"
    assert metadata["metadata"] == {
        "boundaries": [
            "filesystem_read_untrusted",
            "filesystem_write",
            "network_fetch",
        ]
    }
    description = str(metadata["description"])
    assert "assess architecture and provide an action plan" in description
    for route in ("architect-design", "architect-diagram", "architect-review"):
        assert route in description
    assert "credential" not in str(metadata["metadata"])


def test_progressive_stages_modes_and_correction_points_are_explicit() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    positions = [
        text.index(f"### {index}. {stage}")
        for index, stage in enumerate(
            ("Frame", "Map", "Focus", "Investigate", "Act", "Close"), start=1
        )
    ]
    assert positions == sorted(positions)
    for mode in ("**Survey**", "**Standard (default)**", "**Deep**"):
        assert mode in text
    assert "In survey mode, stop here" in text
    assert "Map checkpoint" in text and "Focus checkpoint" in text
    assert text.count("say **continue**") == 2


def test_map_focus_investigation_and_action_contracts_are_complete() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    for view in (
        "context and external actors/systems",
        "repositories versus deployables and runtime units",
        "modules, capabilities, and dependency direction",
        "data stores, schemas, ownership, movement, and lifecycle",
        "synchronous, asynchronous, batch, and control interactions",
        "build, test, release, infrastructure, and operational paths",
        "identity, policy, secrets, trust, tenant, and privilege boundaries",
    ):
        assert view in text

    for dimension in (
        "consequence",
        "change/runtime pressure",
        "concentration/coupling",
        "verification weakness",
        "operational/data/security exposure",
        "evidence confidence",
    ):
        assert dimension in text
    assert "Heat selects drill-down priority" in text
    assert "not proof of a defect" in text

    for path_kind in (
        "one normal/happy path",
        "one high-risk mutation or external side effect",
        "one failure, retry, cancellation, restart, or recovery path",
    ):
        assert path_kind in text
    for action_field in (
        "intended outcome",
        "included finding IDs",
        "prerequisites",
        "completion proof",
        "rollback or containment",
        "owner class",
        "non-goals",
    ):
        assert action_field in text


def test_evidence_and_enterprise_context_fail_closed_without_overclaim() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    evidence = (SKILL_ROOT / "references" / "evidence-method.md").read_text(encoding="utf-8")
    enterprise = (SKILL_ROOT / "references" / "enterprise-context.md").read_text(encoding="utf-8")
    for surface in (
        "documentation",
        "source",
        "tests",
        "manifests/dependencies",
        "CI/CD",
        "deployment/release/IaC",
        "schemas/migrations",
        "runtime configuration",
        "operational evidence",
        "read-only history",
    ):
        assert surface.lower() in evidence.lower()
    for plane in ("Target evidence", "Enterprise context", "Pack knowledge"):
        assert plane in text
    for rejected in (
        "public web",
        "generic browser",
        "arbitrary URL",
        "repository-supplied URLs",
    ):
        assert rejected.lower() in enterprise.lower()
    assert "ask the user to authorize" in enterprise
    assert "Do not create a connector, log in, inspect credentials" in enterprise
    assert "instruction-like content" in enterprise


def test_concept_routing_is_bounded_and_resolves_to_canonical_paths() -> None:
    routing = (SKILL_ROOT / "references" / "concept-routing.md").read_text(encoding="utf-8")
    routed_paths = set(re.findall(r"`((?:[a-z0-9-]+/)+[a-z0-9-]+\.md)`", routing))
    actual_concepts = {
        path.relative_to(CORPUS_ROOT).as_posix()
        for path in CORPUS_ROOT.rglob("*.md")
        if path.name != "index.md"
    }
    assert routed_paths
    for relative in routed_paths:
        assert relative in actual_concepts, relative
    assert "Never load all branches" in routing
    assert "selected, skipped, unavailable, stale, or not applicable" in routing


def test_report_template_groups_sections_into_five_parts_in_reader_order() -> None:
    report = (SKILL_ROOT / "assets" / "assessment.md").read_text(encoding="utf-8")
    expected = (
        "## Part 1: Summary",
        "### Bottom line",
        "### How to read this report",
        "## Part 2: What was assessed",
        "### Assessment charter",
        "### Conceptual current state",
        "## Part 3: What matters and what to do",
        "### Key themes",
        "### Prioritized recommendations",
        "### Action waves",
        "### Next decision",
        "## Part 4: Findings in detail",
        "### Findings by area",
        "### Findings",
        "### Strengths and evidence-backed non-risks",
        "### Material unknowns",
        "## Part 5: Evidence and method",
        "### Evidence coverage",
        "### Attention heat map",
        "### Hotspot drill-downs",
        "### Coverage and confidence",
    )
    positions = [report.index(heading) for heading in expected]
    assert positions == sorted(positions)
    for finding_field in (
        "Classification:",
        "Stakeholder / scenario:",
        "Evidence:",
        "Counter-evidence:",
        "Mechanism:",
        "Consequence:",
        "Severity:",
        "Confidence:",
        "Validation gap:",
        "Smallest safe response:",
        "Theme:",
        "Area:",
    ):
        assert finding_field in report
    for recommendation_column in ("ID", "Priority", "Recommendation", "Why now", "Addresses", "Effort"):
        assert f"| {recommendation_column} |" in report or f"| {recommendation_column} " in report
    assert "Included recommendations:" in report
    assert "Included findings:" in report
    assert "Completion proof:" in report


def test_all_local_markdown_routes_resolve_and_saving_is_optional() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    references = re.findall(r"`((?:references|assets)/[^`]+\.md)`", text)
    local_markdown = {path.relative_to(SKILL_ROOT).as_posix() for path in SKILL_ROOT.rglob("*.md")}
    assert references
    for relative in references:
        assert relative in local_markdown, relative
    assert "Offer to save only after rendering" in text
    assert "Result: chat only; no file was created." in text


def _template() -> str:
    return (SKILL_ROOT / "assets" / "assessment.md").read_text(encoding="utf-8")


def test_template_orientation_subsections_precede_map_checkpoint() -> None:
    report = _template()
    current_state = report.index("### Conceptual current state")
    headings = (
        "#### Overall architecture",
        "#### Architecture by subsystem",
        "#### Technology and dependencies",
        "#### Physical architecture",
        "#### Map checkpoint",
    )
    positions = [report.index(heading) for heading in headings]
    assert current_state < positions[0]
    assert positions == sorted(positions)
    assert positions[-1] < report.index("### Evidence coverage")


def test_each_orientation_subsection_ends_with_a_sources_checked_table() -> None:
    report = _template()
    for start, end in (
        ("#### Overall architecture", "#### Architecture by subsystem"),
        ("#### Architecture by subsystem", "#### Technology and dependencies"),
        ("#### Technology and dependencies", "#### Physical architecture"),
        ("#### Physical architecture", "#### Map checkpoint"),
    ):
        lines = report[report.index(start) : report.index(end)].rstrip().splitlines()
        assert lines[-1].startswith("| --- |")
        assert lines[-2] == "| Source | Locator | Evidence class | Limit |"
        assert lines[-3] == ""
        assert lines[-4] == "Sources checked:"


def test_template_cites_the_one_evidence_class_definition() -> None:
    report = " ".join(_template().split())
    for word in ("observed", "inferred", "reported", "unknown"):
        assert word in report
    assert "references/evidence-method.md" in report
    assert "Claim calibration" in report
    assert "begins with the line `not assessed` on its own" in report
    assert "still ends with its table" in report


def test_no_second_definition_of_the_evidence_classes() -> None:
    pattern = re.compile(
        r"^\s*(?:[-*]\s+|\d+\.\s+)?\*\*(Observed|Inferred|Reported|Unknown)\*\*",
        re.MULTILINE,
    )
    owner = SKILL_ROOT / "references" / "evidence-method.md"
    assert pattern.search(owner.read_text(encoding="utf-8"))
    for path in SKILL_ROOT.rglob("*.md"):
        if path != owner:
            assert not pattern.search(path.read_text(encoding="utf-8")), path


def test_charter_records_checkpoint_state() -> None:
    report = _template()
    assert "Checkpoints: <confirmed | accepted-without-pause>" in report


def test_cannot_pause_exception_is_stated_at_each_checkpoint_rule() -> None:
    text = SKILL_PATH.read_text(encoding="utf-8")
    assert "no interactive channel" in text
    assert "an interactive session never skips the pause" in text
    for heading in ("### 2. Map", "### 3. Focus"):
        start = text.index(heading)
        section = text[start : text.index("\n### ", start + 1)]
        assert "Checkpoints: accepted-without-pause" in section
        assert "not user-confirmed" in section


def test_orientation_reference_routes_to_the_owning_skills() -> None:
    text = (SKILL_ROOT / "references" / "orientation-views.md").read_text(encoding="utf-8")
    assert "architect-diagram" in text
    assert "physical-bom.md" in text
    assert "not assessed" in text


def test_orientation_evals_exist() -> None:
    import json

    evals = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text("utf-8"))["evals"]
    by_prompt = {case["prompt"]: case for case in evals}
    pause = next(c for p, c in by_prompt.items() if "cannot ask me anything" in p)
    assertions = " ".join(pause["assertions"])
    assert "Checkpoints: accepted-without-pause" in assertions
    assert assertions.count("not user-confirmed") == 2
    assert "Writes no file" in assertions
    physical = next(c for p, c in by_prompt.items() if "no Dockerfile" in p)
    assertions = " ".join(physical["assertions"])
    assert "begins with the line `not assessed`" in assertions
    assert "Names no host, cluster, cloud service, or network component" in assertions
    assert "ends with a Sources checked table" in assertions


def test_html_mode_is_named_with_its_script_and_preconditions() -> None:
    text = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    assert "## HTML report mode" in text
    assert "`scripts/render_html.py <effort-dir>`" in text
    assert "Run the script only on a user request" in text
    assert "offer to save one first" in text and "run nothing" in text
    assert (SKILL_ROOT / "scripts" / "render_html.py").is_file()


def test_html_reference_states_the_path_and_host_limits() -> None:
    text = " ".join(
        (SKILL_ROOT / "references" / "html-report.md").read_text(encoding="utf-8").split()
    )
    assert "Pass the resolved effort directory" in text
    assert "Windows included" in text and "| 3 |" in text


def test_html_eval_case_checks_the_sources_checked_table() -> None:
    import json

    evals = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text("utf-8"))["evals"]
    case = next(c for c in evals if "HTML report" in c["prompt"])
    assert any("Sources checked table" in a for a in case["assertions"])


def test_html_reference_names_the_style_the_rail_and_the_asset_refusals() -> None:
    text = " ".join(
        (SKILL_ROOT / "references" / "html-report.md").read_text(encoding="utf-8").split()
    )
    assert "maintainer-view style" in text and "contents rail" in text
    lines = (SKILL_ROOT / "references" / "html-report.md").read_text(encoding="utf-8").splitlines()
    row = next(line for line in lines if line.startswith("| 3 |"))
    for reason in (
        "missing",
        "over 64 KiB",
        "not UTF-8",
        "`</style`",
        "`<!--`",
        "`url(`",
        "`@import`",
    ):
        assert reason in row


def test_html_eval_case_checks_the_style_the_rail_and_the_marks() -> None:
    import json

    evals = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text("utf-8"))["evals"]
    case = next(c for c in evals if "HTML report" in c["prompt"])
    assert any(
        "maintainer-view style" in a and "contents rail" in a and "provenance marks" in a
        for a in case["assertions"]
    )


def test_html_reference_and_skill_name_the_diagrams_flag_and_host() -> None:
    reference = " ".join(
        (SKILL_ROOT / "references" / "html-report.md").read_text(encoding="utf-8").split()
    )
    skill = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())
    for text in (reference, skill):
        assert "`--diagrams`" in text and "cdn.jsdelivr.net" in text
    assert "render_html: usage: render_html.py <effort-dir> [--diagrams]" in reference
    assert "only when the user asks for drawn diagrams" in reference
    assert "Pass `--diagrams` only when the user asks for drawn diagrams" in skill
    assert "should not be shared with readers who expect the offline default" in skill
    assert "Share a drawn report only with readers who accept that" in reference
    assert "on the default page" in reference and "default page runs no script" in reference


def test_html_reference_exit_rows_name_the_new_refusals() -> None:
    lines = (SKILL_ROOT / "references" / "html-report.md").read_text(encoding="utf-8").splitlines()
    two = next(line for line in lines if line.startswith("| 2 |"))
    three = next(line for line in lines if line.startswith("| 3 |"))
    assert "second argument other than `--diagrams`" in two
    for token in (
        "render_html: failed: script asset missing or unsafe",
        "render_html: failed: script asset over the size cap",
        "render_html: failed: script asset unreadable",
        "render_html: failed: script asset holds forbidden text",
    ):
        assert token in three, token
    for reason in ("diagrams script asset", "`</script`", "a carriage return"):
        assert reason in three


def test_diagrams_evals_assert_the_flag_and_its_absence() -> None:
    import json

    evals = json.loads((SKILL_ROOT / "evals" / "evals.json").read_text("utf-8"))["evals"]
    drawn = next(c for c in evals if "diagrams drawn" in c["prompt"])
    plain = next(c for c in evals if c["prompt"].endswith("Render it to HTML."))
    assert any("with --diagrams as the second argument" in a for a in drawn["assertions"])
    assert any("without the --diagrams flag" in a for a in plain["assertions"])


def test_every_part_opens_with_a_line_on_what_the_reader_can_do() -> None:
    report = _template()
    parts = re.split(r"(?m)^## ", report)[1:]
    assert len(parts) == 5
    for part in parts:
        outcome = part.split("\n\n", 2)[1]
        assert outcome.startswith("Read this part to "), outcome


def test_template_carries_the_area_index_the_working_well_field_and_the_wave_horizon() -> None:
    report = _template()
    assert "Working well:" in report
    assert "Indicative horizon:" in report
    index = report[report.index("### Findings by area") : report.index("### Findings\n")]
    for area in (
        "Architecture and boundaries",
        "Technology and dependencies",
        "Code quality and testing",
        "Delivery, security and governance",
        "Data and contracts",
        "Documentation and agent readiness",
    ):
        assert f"| {area} |" in index, area
    assert "| Area | Status | Findings | Worth keeping | Limit |" in index
    assert "none found" in index and "not assessed" in index
