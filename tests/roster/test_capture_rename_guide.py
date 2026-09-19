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
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
GUIDE = ROOT / "guides/core/explanation/core-pack.md"
WORKFLOW = ROOT / ".github/workflows/build-check.yml"

THIS_ROSTER_FILE = "tests/roster/test_capture_rename_guide.py"
BULK_PYTEST_INVOCATION = "python -m pytest tests/ -q"

# AC27: the guide's numbered `Capture` step entry, bound by its own line —
# `**Capture.**` at the start of a numbered list item — so `routes`/`routing`
# appearing elsewhere in the guide cannot satisfy the routing assertion.
CAPTURE_STEP_ENTRY_RE = re.compile(r"^\d+\.\s+\*\*Capture\.\*\*.*$", re.MULTILINE)

# AC28: the retired step name, case-insensitively, across all three
# separators. The needles are assembled from parts below: AC28 allows two
# exceptions and a `tests/` skip would be a third, so this file must not
# contain the retired name as a literal its own sweep would match.
RETIRED_STEP_RE = re.compile(r"capture[ _-]learnings", re.IGNORECASE)
SWEEP_ROOTS = ("packs", "tools", "guides")
# The two stable identifiers the sweep exempts: the eval case id (an
# identifier, not a description of the step) and any path under
# `docs/knowledge/` (seeded knowledge records naming a prior semantic gate).
_STEM = "capt" "ure"                            # never one literal; see above
_RETIRED_SPACED = _STEM.capitalize() + " learnings"
EVALS_CASE_ID = _STEM + "-learnings-quality-attributes"


def test_guide_names_the_step_as_shipped() -> None:
    """AC23, AC27: the guide names the step `Capture` and its own numbered
    step entry — not the file at large — describes it as routing."""
    body = GUIDE.read_text(encoding="utf-8")
    assert "**Capture.**" in body, (
        f"the guide still names the step {_RETIRED_SPACED!r} rather than 'Capture'"
    )
    assert _RETIRED_SPACED not in body, (
        f"the guide still carries the retired step name {_RETIRED_SPACED!r}"
    )
    match = CAPTURE_STEP_ENTRY_RE.search(body)
    assert match is not None, "the guide has no numbered 'Capture' step entry"
    entry = match.group(0)
    assert "routes" in entry or "routing" in entry, (
        "the guide's 'Capture' step entry describes recording a learning but "
        "not routing a scratch note"
    )


def test_roster_step_precedes_the_bulk_pytest_step() -> None:
    """AC24: every step naming this file, in every job, precedes that job's
    bulk `pytest tests/ -q` step, and no such step exists in any job that has
    no bulk step for it to precede — checked per job, not by flattening every
    job's steps into one list and comparing only the first matches."""
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    jobs_naming_the_file: list[str] = []

    for job_name, job in doc["jobs"].items():
        steps = job.get("steps", [])
        naming_indices = [
            i for i, step in enumerate(steps) if THIS_ROSTER_FILE in (step.get("run") or "")
        ]
        if not naming_indices:
            continue
        jobs_naming_the_file.append(job_name)

        bulk_indices = [
            i
            for i, step in enumerate(steps)
            if BULK_PYTEST_INVOCATION in (step.get("run") or "")
        ]
        assert bulk_indices, (
            f"job {job_name!r} names {THIS_ROSTER_FILE} but has no "
            f"{BULK_PYTEST_INVOCATION!r} step for it to precede"
        )
        for named_index in naming_indices:
            assert all(named_index < bulk_index for bulk_index in bulk_indices), (
                f"job {job_name!r}: the step naming {THIS_ROSTER_FILE} at "
                f"index {named_index} does not precede every bulk pytest "
                f"step at {bulk_indices}"
            )

    assert jobs_naming_the_file, f"no job in {WORKFLOW} names {THIS_ROSTER_FILE}"
    assert len(jobs_naming_the_file) == 1, (
        f"{THIS_ROSTER_FILE} is named in more than one job: {jobs_naming_the_file}"
    )


def _sweep_files():
    for root_name in SWEEP_ROOTS:
        for path in sorted((ROOT / root_name).rglob("*")):
            if not path.is_file():
                continue
            if "__pycache__" in path.relative_to(ROOT).parts:
                continue
            if "docs/knowledge" in path.as_posix():
                continue
            yield path


def test_retired_step_name_is_absent_from_shipped_content() -> None:
    """AC28: no file under `packs/`, `tools/`, or `guides/` names the
    retired step name, in any casing or separator, except the
    `evals.json` case id and `docs/knowledge/` records — both stable
    identifiers."""
    offenders: list[str] = []
    for path in _sweep_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if path.name == "evals.json":
            text = text.replace(EVALS_CASE_ID, "")
        for match in RETIRED_STEP_RE.finditer(text):
            offenders.append(f"{path.relative_to(ROOT)}: {match.group(0)!r}")
    assert not offenders, (
        "the retired step name is still present outside its two stable-"
        f"identifier exceptions: {offenders}"
    )
