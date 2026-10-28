"""Construction tests for the work-loop evidence-mode contract."""

import json
import re
import tomllib
from pathlib import Path

_WORK_LOOP = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "SKILL.md"


def _section(text: str, start: str, end: str) -> str:
    """Return the text between two markers; fail if either is missing."""
    assert start in text, f"missing start marker: {start!r}"
    head = text.index(start) + len(start)
    assert end in text[head:], f"missing end marker: {end!r}"
    return text[head : text.index(end, head)]


def test_t1_unfamiliar_trigger_permits_one_bounded_spike() -> None:
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    block = _section(raw, "<!-- risk-triggers:start", "<!-- risk-triggers:end -->")
    bullet = " ".join(_section(block, "- **Unfamiliar**", "- **").split())

    assert "one spike" in bullet
    assert "outside the tracked tree" in bullet
    assert "`new-spec`'s side-effect-free probe constraint" in bullet
    assert "never committed" in bullet
    assert "Record what it observed as the grounding" in bullet
    assert "settles only this trigger" in bullet


_BUG_FIX = _WORK_LOOP.parents[1] / "bug-fix" / "SKILL.md"
_GUIDES = Path(__file__).resolve().parents[5] / "guides" / "core"


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_t2_description_names_established_cause_and_bug_fix() -> None:
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    description = next(
        line.removeprefix("description:").strip()
        for line in raw.split("---", 2)[1].splitlines()
        if line.startswith("description:")
    )
    assert "behavior-changing fix" not in description
    assert "fix whose cause is established" in description
    assert "`bug-fix`" in description
    assert "cause is not" in description


def test_t2_plan_routes_unestablished_defects_through_bug_fix() -> None:
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    plan = _flat(_section(raw, "## Step 1. PLAN", "## Step 2. EXECUTE"))
    step = _flat(_section(plan, "1b. ", "2. **Select light or full mode"))
    assert "`bug-fix` diagnosis first" in step
    assert "disposable scratch" in step
    assert "full mode records it as the task's plan stub" in step
    assert "light mode writes it at its real test path during EXECUTE" in step
    assert "never a repository test file during PLAN" in step


def test_t2_bug_fix_skill_hands_the_fix_to_work_loop() -> None:
    raw = _BUG_FIX.read_text(encoding="utf-8")
    assert "AC-0003" not in raw
    step2 = _flat(
        _section(raw, "**Write the failing test (red).", "**Investigate before narrowing.")
    )
    assert "disposable scratch" in step2
    invoke = _flat(_section(raw, "## When to invoke", "## Procedure"))
    assert "`work-loop`" in invoke
    assert "materialization rule" in invoke
    assert "steps 8 to 11" in invoke
    assert "`new-spec`" not in invoke
    assert "opportunistic restructuring" in invoke
    step10 = _flat(
        _section(raw, "**Regression test stays.", "**Commit body documents the root cause.")
    )
    assert "`work-loop` materializes" in step10
    assert "stays in the suite" in step10
    assert "failing test from step 2 remains" not in step10


def test_t2_guides_state_the_handoff_and_drop_old_phrases() -> None:
    for name in ("how-to/bug-fix.md", "explanation/core-pack.md"):
        text = _flat((_GUIDES / name).read_text(encoding="utf-8"))
        assert "`bug-fix` hands the fix to the build loop" in text, name
        for banned in (
            "without entering the spec / loop pipeline",
            "several files",
            "past one file",
        ):
            assert banned not in text, (name, banned)


_WL_REFS = _WORK_LOOP.parent / "references"
_REPO = Path(__file__).resolve().parents[5]
_COUNT = r"(?:two|three|four|five|six|seven|eight|nine|ten|\d+)"


def _step7(raw: str) -> str:
    return _section(raw, "7. **Pick the verification mode", "8. **Design construction tests")


def test_t3_step7_lists_behavior_pin_and_measurement() -> None:
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    step = _flat(_step7(raw))
    assert "**Behavior pin** — a behavior-preserving restructure" in step
    assert "type check and lint are not a pin" in step
    assert "**Measurement** — a change whose claim is a number" in step
    assert "Baseline first, same command both sides" in step

    execute = _flat(
        _section(raw, "Match discipline to verification mode:", "**Controlled full-mode")
    )
    assert "**Behavior pin** — pin green on the base commit first" in execute
    assert "revert a restructure that removes no branch, layer, or invalid state" in execute
    assert "**Measurement** — baseline on the base commit" in execute
    assert "same command, data, and environment" in execute

    row = next(line for line in raw.splitlines() if line.startswith("| Task picks Visual"))
    assert "Behavior pin" in row and "Measurement" in row


def test_t3_no_stub_regions_point_at_step7() -> None:
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    stubs = (_WL_REFS / "tdd-stubs.md").read_text(encoding="utf-8")
    step8 = _flat(_section(raw, "8. **Design construction tests", "8a. **Anchor-test sweep"))
    opening = _flat(_section(stubs, "# TDD stub generation", "## Lifecycle"))
    bullet = _flat(stubs.split("**Full-mode, TDD-tasks-only.**", 1)[1])
    for region in (step8, opening, bullet):
        assert "PLAN step 7" in region
        assert "Goal-based and manual-QA tasks" not in region
    for region in (step8, opening):
        assert "behavior pin" in region and "measurement" in region


def test_t3_behavior_pin_section_states_the_doctrine() -> None:
    text = (_WL_REFS / "verification-modes.md").read_text(encoding="utf-8")
    sec = _flat(_section(text + "\n## END", "## Behavior pin", "## Measurement"))
    assert "passes on the base commit before any structure moves" in sec
    assert "stays green after each step" in sec
    assert "Lint and typecheck are not a pin" in sec
    assert "names no branch, layer, or invalid state it removed is reverted" in sec


def test_t3_measurement_section_states_the_doctrine() -> None:
    text = (_WL_REFS / "verification-modes.md").read_text(encoding="utf-8")
    sec = _flat(text.split("## Measurement", 1)[1])
    assert "same command, data, and environment as the after run" in sec
    assert "at least 5 times, alternating" in sec
    assert "median, the range, and the run count" in sec
    assert "inside the run-to-run range is reported as no measurable difference" in sec
    assert "error count" in sec and "count of the work done" in sec


def test_t3_no_closed_mode_list_outside_work_loop_skill() -> None:
    count_re = re.compile(rf"\b{_COUNT}\s+(?:other\s+)?verification[\s-]+modes?\b", re.I)
    list_re = re.compile(r"TDD\s*(?:/|,)\s*goal-based", re.I)
    hits = []
    for root in (_WORK_LOOP.parents[2], _REPO / "guides" / "core"):
        for path in root.rglob("*.md"):
            if path == _WORK_LOOP:
                continue
            text = _flat(path.read_text(encoding="utf-8"))
            if count_re.search(text) or list_re.search(text):
                hits.append(str(path))
    assert not hits, hits


def test_t3_named_files_point_at_step7_without_a_count() -> None:
    apm = _WORK_LOOP.parents[2]
    files = [
        apm / "agents" / "adversarial-reviewer.md",
        apm / "agents" / "implementer.md",
        _WL_REFS / "infra-verification.md",
        _WL_REFS / "verification-modes.md",
        apm / "skills" / "new-spec" / "SKILL.md",
        apm / "skills" / "new-spec" / "references" / "spec-and-plan-contract.md",
        apm / "skills" / "new-spec" / "assets" / "spec.md",
        _GUIDES / "explanation" / "core-pack.md",
    ]
    for path in files:
        text = _flat(path.read_text(encoding="utf-8"))
        assert not re.search(rf"\b{_COUNT}\s+modes\b", text, re.I), path
        assert not re.search(rf"\bdefines\s+{_COUNT}\b", text, re.I), path
        assert "PLAN step 7" in text, path


_ADV = _WORK_LOOP.parents[2] / "agents" / "adversarial-reviewer.md"
_ADJ = _WORK_LOOP.parents[2] / "agents" / "finding-adjudicator.md"


def _t4_report_section() -> str:
    raw = _ADV.read_text(encoding="utf-8")
    return _flat(_section(raw, "## Report numbered findings", "### Output format"))


def test_t4_behavior_claim_carries_its_run() -> None:
    sec = _t4_report_section()
    assert "**A behavior claim carries its run.**" in sec
    assert "an output, an exit status, a raised error, a state change" in sec
    assert "put the command and the output it printed beside the finding" in sec


def test_t4_feasibility_has_four_conditions_and_timeout() -> None:
    sec = _t4_report_section()
    assert "it runs in this checkout" in sec
    assert "it writes nothing outside ignored scratch" in sec
    assert "it uses no network and no credentials" in sec
    assert "60-second wall-clock timeout you apply" in sec
    assert "A run that hits the timeout is not feasible." in sec


def test_t4_missing_run_caps_at_concern_and_is_named() -> None:
    sec = _t4_report_section()
    assert "is a Concern at most, with the missing run named" in sec


def test_t4_no_run_list_is_closed_and_named() -> None:
    sec = _t4_report_section()
    assert "Exactly these cases owe no run" in sec
    assert "the finding names the one that applies" in sec
    for case in (
        "a dangling reference",
        "a missing artifact",
        "a contract the target contradicts",
        "a rename that left a reference behind",
        "spec-stage, RFC, and intent review",
        "a model evaluation",
        "a run that is not feasible",
    ):
        assert case in sec, case


def test_t4_targeted_reproduction_is_not_a_gate_run() -> None:
    raw = _ADV.read_text(encoding="utf-8")
    sec = _flat(_section(raw, "## What you do not do", "- **Approve work"))
    assert "Run the mechanical gates yourself" in sec
    assert "targeted reproduction for one finding is not a gate run" in sec
    assert "behavior-claim rule" in sec


def test_t4_fix_runs_command_before_and_after() -> None:
    raw = _WORK_LOOP.read_text(encoding="utf-8")
    sec = _flat(_section(raw, "## FIX", "## Capture"))
    assert "carrying a command" in sec
    assert "before the fix and record it failing" in sec
    assert "after the fix and record it passing" in sec
    assert "passes before the fix is Surfaced instead of fixed" in sec
    assert "Failing means its exit status or printed output shows the defect" in sec


def test_t4_adjudicator_tools_stay_read_grep() -> None:
    raw = _ADJ.read_text(encoding="utf-8")
    line = next(ln for ln in raw.splitlines() if ln.startswith("tools:"))
    assert line == "tools: Read, Grep"


_PACK = Path(__file__).resolve().parents[3]


def test_t5_new_eval_cases_exist_with_required_fields() -> None:
    wanted = {
        _PACK / ".apm/skills/work-loop/evals/evals.json": {
            "unfamiliar-design-bounded-spike",
            "undiagnosed-defect-routes-to-bug-fix",
            "refactor-behavior-pin-mode",
            "perf-claim-measurement-mode",
        },
        _PACK / ".apm/skills/bug-fix/evals/evals.json": {"fix-hands-off-to-work-loop"},
    }
    for path, ids in wanted.items():
        cases = {c["id"]: c for c in json.loads(path.read_text(encoding="utf-8"))["evals"]}
        for case_id in ids:
            assert case_id in cases, f"{path.name}: missing {case_id}"
            case = cases[case_id]
            assert case["prompt"] and case["expected_output"]
            assert isinstance(case["assertions"], list) and case["assertions"]


def test_t5_pack_versions_are_3_1_27() -> None:
    manifest = tomllib.loads((_PACK / "pack.toml").read_text(encoding="utf-8"))
    plugin = json.loads((_PACK / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert manifest["pack"]["version"] == "3.1.27"
    assert plugin["version"] == "3.1.27"


def test_t2_step_1b_renders_as_its_own_block() -> None:
    text = _WORK_LOOP.read_text(encoding="utf-8")
    assert "\n\n1b. **Route an undiagnosed defect" in text
