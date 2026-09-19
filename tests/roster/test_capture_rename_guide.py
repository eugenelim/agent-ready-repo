"""The adopter-facing guide must describe `## Capture` as shipped.

`guides/core/explanation/core-pack.md` sits above `packs/core/`, so a check
that reads it cannot live in `packs/core/tests/pack/` —
`tools/lint-pack-test-boundary.py`'s `pack-tests-stay-in-pack` check forbids a
pack test climbing out of its own pack, with no exemption. This roster file
carries the one clause of `packs/core/tests/pack/test_ride_along_admission_test.py`
that the pack test cannot: AC23, the renamed step's guide description.

`test_roster_step_precedes_the_bulk_pytest_step` guards a second, unrelated
hazard: `gate-main` collects every roster module through one bulk
`python -m pytest tests/ -q` step, so a new roster file runs on a pull request
even with no named step of its own — but if a named step attributing this
file's failure sits BELOW that bulk step, the job's fail-fast behaviour with no
step-level `if:` means the named step never runs and the failure is reported
under the bulk step's name instead. AC24 is that ordering, not the guide's
content.
"""
from __future__ import annotations

import pathlib

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guides/core/explanation/core-pack.md"
WORKFLOW = ROOT / ".github/workflows/build-check.yml"

THIS_ROSTER_FILE = "tests/roster/test_capture_rename_guide.py"
BULK_PYTEST_INVOCATION = "python -m pytest tests/ -q"


def test_guide_names_the_step_as_shipped() -> None:
    """AC23: the guide names the step `Capture` and describes it as routing.

    Reds today: the guide's step 10 reads "Capture learnings" and describes it
    as writing something to a skill, ADR, or pattern note — not as routing a
    scratch note. T4 owns the guide edit that turns this green.
    """
    body = GUIDE.read_text(encoding="utf-8")
    assert "**Capture.**" in body, (
        "the guide still names the step 'Capture learnings' rather than 'Capture'"
    )
    assert "Capture learnings" not in body, (
        "the guide still carries the retired step name 'Capture learnings'"
    )
    assert "routes" in body or "routing" in body, (
        "the guide describes recording a learning but not routing a scratch note"
    )


def _step_names(doc: dict) -> list[tuple[str, dict]]:
    """Every `(job, step)` pair across every job, in file order."""
    steps: list[tuple[str, dict]] = []
    for job in doc["jobs"].values():
        for step in job.get("steps", []):
            steps.append((job, step))
    return steps


def test_roster_step_precedes_the_bulk_pytest_step() -> None:
    """AC24: the named step for this file sits above the bulk `tests/ -q` step."""
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    all_steps: list[dict] = []
    for job in doc["jobs"].values():
        all_steps.extend(job.get("steps", []))

    named_index = next(
        (
            i
            for i, step in enumerate(all_steps)
            if THIS_ROSTER_FILE in (step.get("run") or "")
        ),
        None,
    )
    bulk_index = next(
        (
            i
            for i, step in enumerate(all_steps)
            if BULK_PYTEST_INVOCATION in (step.get("run") or "")
        ),
        None,
    )

    assert named_index is not None, (
        f"no step in {WORKFLOW} names {THIS_ROSTER_FILE}"
    )
    assert bulk_index is not None, (
        f"no step in {WORKFLOW} runs {BULK_PYTEST_INVOCATION!r}"
    )
    assert named_index < bulk_index, (
        f"the named step for {THIS_ROSTER_FILE} (index {named_index}) does not "
        f"precede the bulk pytest step (index {bulk_index})"
    )
