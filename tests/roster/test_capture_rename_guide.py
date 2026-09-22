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

No test here compares the pack module's `C1`...`C7` constants against
`docs/specs/ride-along-admission-test/spec.md` § The shipped clauses. That
comparison (AC3) was removed: the spec is a frozen historical record of what
shipped at acceptance, so pinning live constants to it froze the shipped
artifact too — a correct repair to a clause could not land anywhere without
body-editing a frozen document. The clauses keep the byte-equality and
placement pins in `packs/core/tests/pack/test_ride_along_admission_test.py`,
which compare each site against the canonical constant. What that loses,
stated rather than implied: an identical reword applied to every site *and*
to the constants would now pass, because no source outside those files
asserts the wording.
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


# AC12: the retired step name, case-insensitively, across all three
# separators. The needles are assembled from parts below: AC12 allows exactly
# one exception and a `tests/` skip would be a second, so this file must not
# contain the retired name as a literal its own sweep would match.
RETIRED_STEP_RE = re.compile(r"capture[ _-]learnings", re.IGNORECASE)
# AC12 sweeps bytes so a binary under a swept root cannot force an exemption.
RETIRED_STEP_BYTES_RE = re.compile(rb"capture[ _-]learnings", re.IGNORECASE)
EVALS_JSON = (
    ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop"
    / "evals" / "evals.json"
)
SWEEP_ROOTS = ("packs", "tools", "guides")
# The one stable identifier the sweep exempts: the eval case id (an
# identifier, not a description of the step). `docs/knowledge/` records keep
# the retired name as a stable gate identifier too, but they sit outside
# `SWEEP_ROOTS`, so exempting them here would be unreachable — AC12 no
# longer names them as an exception.
# Assembled by a runtime call, not adjacent literals: the compiler
# constant-folds `"capt" "ure" + "-learnings"` into one literal, so the
# .pyc would carry the retired name this file must not contain.
_STEM = "".join(("capt", "ure"))
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
            yield path


def test_retired_step_name_is_absent_from_shipped_content() -> None:
    """AC12: no file under `packs/`, `tools/`, or `guides/` names the
    retired step name, in any casing or separator, except the `evals.json`
    case id — the control's only exemption.

    The sweep reads bytes, not decoded text. The retired name is ASCII, so a
    byte search finds it wherever it appears, and no file is ever one this
    control "cannot read" — which is how the fail-don't-skip obligation is
    met without exempting anything. Decoding as UTF-8 instead would raise on
    legitimate git-tracked binaries under a swept root, such as
    `packs/converters/.apm/skills/file-to-markdown/evals/files/sample.docx`,
    forcing an exemption the criterion does not allow.

    Named blind spot: a compressed container can hold the name in a form no
    byte search sees. A `.docx` is a zip, so a retired reference inside one
    is not detected. That is unchanged from any text-based sweep and is not
    what this control is for.
    """
    offenders: list[str] = []
    for path in _sweep_files():
        raw = path.read_bytes()
        # AC12 exempts one thing: the designated case's `id` value. Stripping
        # every occurrence of that string from every file named evals.json
        # would also blind the sweep to the name appearing in a prompt, an
        # expected output, an assertion, or another pack's register — a wider
        # exemption than the criterion grants.
        if path == EVALS_JSON:
            raw = raw.replace(b'"id": "' + EVALS_CASE_ID.encode() + b'"', b"")
        for match in RETIRED_STEP_BYTES_RE.finditer(raw):
            offenders.append(
                f"{path.relative_to(ROOT)}: {match.group(0).decode('ascii')!r}"
            )
    assert not offenders, (
        "the retired step name is still present outside its one stable-"
        f"identifier exception: {offenders}"
    )
