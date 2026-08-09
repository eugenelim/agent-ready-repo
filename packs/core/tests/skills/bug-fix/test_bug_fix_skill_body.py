import json
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "bug-fix"
    / "SKILL.md"
)
EVAL_QUERIES = SKILL.parent / "evals" / "eval_queries.json"


def _body() -> str:
    return SKILL.read_text(encoding="utf-8")


# STUB: AC1 — the normal path keeps reproduction and red before a fix
def test_ac1_normal_path_keeps_the_regression_test_before_the_fix() -> None:
    body = _body()
    ordered_markers = [
        "**Reproduce first.",
        "**Write the failing test (red).",
        "**Investigate before narrowing.",
        "**Minimum fix.",
    ]
    positions = [body.index(marker) for marker in ordered_markers]
    assert positions == sorted(positions)


# STUB: AC2 — rival hypotheses retain evidence fields and one-factor probes
def test_ac2_rival_hypotheses_keep_evidence_and_one_factor_experiments() -> None:
    body = _body()
    hypothesis_start = body.index("**List candidate causes, then falsify each.")
    root_cause_start = body.index("**Trace the root cause backward.")
    hypothesis_section = body[hypothesis_start:root_cause_start]
    assert "2–3" in hypothesis_section or "2-3" in hypothesis_section
    assert "Expected / Actual / Verdict" in hypothesis_section
    assert "one factor at a time" in hypothesis_section


# STUB: AC3 — multi-component localization precedes narrowing
def test_ac3_multicomponent_localization_observes_boundaries_before_narrowing() -> None:
    body = _body()
    investigation_start = body.index("**Investigate before narrowing.")
    hypothesis_start = body.index("**List candidate causes, then falsify each.")
    investigation_section = body[investigation_start:hypothesis_start]
    assert "inputs, outputs, state, and configuration" in investigation_section
    assert "run the reproduction once" in investigation_section
    assert "locate the failing component" in investigation_section
    assert "before narrowing" in investigation_section


# STUB: AC11 — retained scope, coverage, commit, and tracker disciplines
def test_ac11_preserves_minimum_diff_and_release_hygiene() -> None:
    body = _body()
    for preserved in (
        "Validate at boundaries the request crosses",
        "independent bypass path",
        "concrete safety consequence",
        "coverage gap",
        "Refuse to fix adjacent issues",
        "Commit body documents the root cause",
        "Loop back to the tracker",
    ):
        assert preserved in body


# STUB: AC17 — router description and activation queries cover the same boundary
def test_ac17_description_and_queries_pin_natural_debugging_language() -> None:
    body = _body()
    frontmatter = body.split("---", 2)[1]
    description = next(
        line.removeprefix("description:").strip().lower()
        for line in frontmatter.splitlines()
        if line.startswith("description:")
    )
    for signal in (
        "root cause",
        "ci-only",
        "intermittent",
        "flaky",
        "production incident",
        "new features",
        "behavior-preserving refactors",
        "postmortems",
        "skill maintenance",
    ):
        assert signal in description

    queries = json.loads(EVAL_QUERIES.read_text(encoding="utf-8"))
    original_queries = {
        ("Fix the bug where saving a draft loses the title", True),
        ("The search returns stale results — diagnose and fix it", True),
        ("This is broken: clicking submit twice creates duplicate orders", True),
        ("Investigate this regression in the CSV parser", True),
        ("Users report the avatar upload fails silently — fix it", True),
        ("The date picker shows the wrong month, please fix it", True),
        ("Our nightly job started crashing yesterday — find and fix the cause", True),
        (
            "Fix this: the total doesn't update when I remove an item from the cart",
            True,
        ),
        ("There's a defect in the rounding logic, track it down and fix it", True),
        ("Let's spec out a new feature to let users export their data", False),
        (
            "Refactor this module to be cleaner — behavior should stay the same",
            False,
        ),
        ("Add a new endpoint for listing invoices", False),
        ("Record why we chose to retry failed webhooks", False),
        ("Write a spec for improved error messages", False),
        ("Bootstrap a new service repo from scratch", False),
        ("Decompose this requirements packet into specs", False),
        ("Upgrade us from React 17 to React 18", False),
        ("Document the deployment runbook", False),
    }
    actual_queries = {
        (item["query"], item["should_trigger"])
        for item in queries
    }
    assert original_queries <= actual_queries

    positives = "\n".join(
        item["query"].lower() for item in queries if item["should_trigger"]
    )
    negatives = "\n".join(
        item["query"].lower() for item in queries if not item["should_trigger"]
    )
    for signal in (
        "root cause",
        "only fails in ci",
        "intermittent",
        "flaky",
        "production incident",
    ):
        assert signal in positives
    for boundary in (
        "new retry feature",
        "behavior-preserving refactor",
        "resolved incident postmortem",
        "improve the bug-fix skill",
    ):
        assert boundary in negatives
