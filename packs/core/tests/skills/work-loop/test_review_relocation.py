"""The finding-adjudication commands live in `review-artifact.py`.

VI-6002 covers the run-id path: the retry budget, the owner override, `validate`
for `record` artifacts, and run-id and record-file confinement. VI-6003 covers a
replayed `--operation-id`. VI-6004 keeps the review cap in `review-rules.json`
and the guard layer's default in step.

Standard library and pytest only; the scripts load by path under unique names.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
import review_relocation_support as support

SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPTS = SKILL / "scripts"

NO_COHORT_RUN = "33333333-3333-4333-8333-333333333333"
OTHER_RUN = "44444444-4444-4444-8444-444444444444"
FP_1 = support.FP_A
FP_2 = support.FP_B
FP_3 = "e" * 64


@pytest.fixture(scope="module")
def artifact() -> ModuleType:
    """`review-artifact.py`, loaded once."""
    return support.load_script("core_work_loop_relocation_artifact", SCRIPTS / "review-artifact.py")


# ── review runs ────────────────────────────────────────────────────────────


class Repo:
    """A throwaway repository root and a runner for `review-artifact.py`."""

    def __init__(self, root: Path, module: ModuleType) -> None:
        self.root = root.resolve()
        self.module = module
        self.files = self.root / "files"
        self.files.mkdir()
        for name, text in support.FILES.items():
            (self.files / name).write_bytes(text.encode("utf-8"))

    def run(self, *argv: str) -> tuple[int, str, str]:
        """Run one command with this repository as `--root`."""
        return support.call_main(self.module, [*argv])

    def record(self, *extra: str, run: str = NO_COHORT_RUN) -> tuple[int, str, str]:
        """Record under `run`, defaulting to a findings round."""
        flags = list(extra)
        forms = ("--fingerprint", "--all-skipped", "--report", "--direct-clean-file", "--structural-clean-file")
        if not any(f in flags for f in forms):
            flags = ["--fingerprint", FP_1, *flags]
        return self.run("record", "--run-id", run, "--root", str(self.root), *flags)

    def inspect(self, report: str, *extra: str, run: str = NO_COHORT_RUN) -> tuple[int, str, str]:
        """Inspect an adjudication report against `run`'s previous round."""
        return self.run(
            "inspect", "--run-id", run, "--root", str(self.root),
            "--report", str(self.files / report), "--adjudication", "--json", *extra,
        )

    def run_dir(self, run: str = NO_COHORT_RUN) -> Path:
        """The run's artifact directory."""
        return self.root / ".context" / "reviews" / run

    def records(self, run: str = NO_COHORT_RUN) -> list[str]:
        """Names of the run's `record` artifacts."""
        directory = self.run_dir(run)
        return sorted(p.name for p in directory.glob("*-record.md")) if directory.is_dir() else []

    def body(self, round_number: int, run: str = NO_COHORT_RUN) -> dict[str, Any]:
        """One record artifact's parsed body."""
        return json.loads((self.run_dir(run) / f"{round_number}-record.md").read_text("utf-8"))


@pytest.fixture
def repo(tmp_path: Path, artifact: ModuleType, monkeypatch: pytest.MonkeyPatch) -> Repo:
    """A repository whose review cap is 2, the fixture cap the budget tests use."""
    rules = tmp_path / "review-rules.json"
    rules.write_text(json.dumps({"rules_version": "1", "max_review_retries": 2}), encoding="utf-8")
    monkeypatch.setattr(artifact, "REVIEW_RULES_PATH", rules)
    root = tmp_path / "repo"
    root.mkdir()
    return Repo(root, artifact)


def test_vi6002_third_round_is_refused_at_a_cap_of_two(repo: Repo) -> None:
    """VI-6002: the round that would exceed `max_review_retries` refuses."""
    assert repo.record("--fingerprint", FP_1)[0] == 0
    assert repo.record("--fingerprint", FP_2)[0] == 0
    code, out, _ = repo.record("--fingerprint", FP_3)

    assert (code, out) == (3, "INVALID retry-cap-reached\n")
    assert repo.records() == ["1-record.md", "2-record.md"]


def test_vi6002_owner_override_passes_and_is_stored(repo: Repo) -> None:
    """VI-6002: an `owner` reference lifts the cap and the artifact keeps both facts."""
    repo.record("--fingerprint", FP_1)
    repo.record("--fingerprint", FP_2)
    code, out, _ = repo.record(
        "--fingerprint", FP_3, "--allow-retry-cap-override", "--authority-ref", "owner:0123456789ab"
    )

    assert code == 0
    assert "round=3 retry=3" in out
    body = repo.body(3)
    assert body["override"] is True
    assert body["authority_ref"] == "owner:0123456789ab"
    assert body["review_retry_count"] == 3


@pytest.mark.parametrize(
    "extra",
    [
        ["--allow-retry-cap-override"],
        ["--allow-retry-cap-override", "--authority-ref", "risk-owner"],
        ["--allow-retry-cap-override", "--authority-ref", "owner:not-hex"],
        ["--allow-retry-cap-override", "--authority-ref", ""],
    ],
    ids=["no-reference", "risk-owner", "malformed-owner", "empty"],
)
def test_vi6002_override_without_an_owner_reference_is_refused(repo: Repo, extra: list[str]) -> None:
    """VI-6002: no reference, or any other role's, refuses and writes nothing."""
    repo.record("--fingerprint", FP_1)
    repo.record("--fingerprint", FP_2)
    code, out, _ = repo.record("--fingerprint", FP_3, *extra)

    assert (code, out) == (3, "INVALID authority-refused\n")
    assert repo.records() == ["1-record.md", "2-record.md"]


def test_vi6002_authority_reference_without_override_is_refused(repo: Repo) -> None:
    """VI-6002: an authority reference that nothing uses is a usage error, not ignored."""
    code, out, _ = repo.record("--authority-ref", "owner")

    assert (code, out) == (2, "INVALID invalid-metadata\n")
    assert repo.records() == []


def test_vi6002_unrecorded_round_does_not_count(repo: Repo) -> None:
    """VI-6002: persisted raw and adjudication reports are not `record` artifacts."""
    directory = repo.run_dir()
    directory.mkdir(parents=True)
    for round_number in (1, 2, 3):
        (directory / f"{round_number}-pre-execute-adversarial-reviewer-raw.md").write_text("x")
        (directory / f"{round_number}-pre-execute-adversarial-reviewer-adjudication.md").write_text("x")

    assert repo.record("--fingerprint", FP_1)[0] == 0
    assert repo.record("--fingerprint", FP_2)[0] == 0
    assert repo.records() == ["1-record.md", "2-record.md"]
    assert repo.record("--fingerprint", FP_3)[1] == "INVALID retry-cap-reached\n"


def test_vi6002_clean_rounds_do_not_spend_the_budget(repo: Repo) -> None:
    """VI-6002: only findings rounds count, as the earlier cohort writer counted them."""
    assert repo.record("--all-skipped")[0] == 0
    assert repo.record("--direct-clean-file", str(repo.files / "exact-sentinel.txt"))[0] == 0
    assert repo.record("--fingerprint", FP_1)[0] == 0
    assert repo.record("--fingerprint", FP_2)[0] == 0
    assert repo.record("--fingerprint", FP_3)[1] == "INVALID retry-cap-reached\n"
    assert repo.body(2)["clean_source"] == "direct-clean"
    assert repo.body(3)["review_retry_count"] == 1


def test_vi6002_inspect_reads_the_previous_round_from_the_record(repo: Repo) -> None:
    """VI-6002: `inspect --run-id` matches against the last `record` artifact (AC-0014)."""
    assert json.loads(repo.inspect("adj-findings-a.md")[1])["matches_previous_round"] is False
    repo.record("--fingerprint", FP_1)
    assert json.loads(repo.inspect("adj-findings-a.md")[1])["matches_previous_round"] is True
    assert json.loads(repo.inspect("adj-findings-b.md")[1])["matches_previous_round"] is False
    repo.record("--all-skipped")
    assert json.loads(repo.inspect("adj-findings-a.md")[1])["matches_previous_round"] is False


def test_vi6002_validate_accepts_a_record_and_refuses_any_other_name(repo: Repo) -> None:
    """VI-6002: `validate --kind record` reads `<round>-record.md` and nothing else (AC-0018)."""
    repo.record("--fingerprint", FP_1)
    validate = ["validate", "--root", str(repo.root), "--run-id", NO_COHORT_RUN, "--kind", "record"]

    code, out, _ = repo.run(*validate, "--round", "1")
    assert code == 0 and out.startswith("VALID size=")

    # A stage or role would name a different file, so it refuses.
    code, out, _ = repo.run(
        *validate, "--round", "1", "--review-stage", "pre-execute",
        "--reviewer-role", "adversarial-reviewer",
    )
    assert (code, out) == (2, "INVALID invalid-metadata\n")

    # The same bytes under another name are not a record.
    directory = repo.run_dir()
    (directory / "1-record.md").rename(directory / "record-1.md")
    code, out, _ = repo.run(*validate, "--round", "1")
    assert (code, out) == (3, "INVALID unsafe-artifact\n")


def test_vi6002_validate_still_requires_a_stage_and_role_for_report_kinds(repo: Repo) -> None:
    """VI-6002: making the flags optional did not loosen `raw`, `adjudication`, `evidence`."""
    code, out, _ = repo.run(
        "validate", "--root", str(repo.root), "--run-id", NO_COHORT_RUN, "--round", "1",
        "--kind", "raw",
    )
    assert (code, out) == (2, "INVALID invalid-metadata\n")


@pytest.mark.parametrize("command", ["record", "inspect"])
@pytest.mark.parametrize(
    "run_id",
    ["../x", "/etc", "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA", "not-a-uuid", f"{NO_COHORT_RUN}/.."],
    ids=["traversal", "absolute", "uppercase", "not-a-uuid", "nested"],
)
def test_vi6002_run_id_must_be_a_canonical_lowercase_uuid(repo: Repo, command: str, run_id: str) -> None:
    """VI-6002: no other spelling of a run id reaches the filesystem (AC-0022)."""
    before = sorted(p.name for p in repo.root.iterdir())
    if command == "record":
        code, out, _ = repo.record("--fingerprint", FP_1, run=run_id)
    else:
        code, out, _ = repo.inspect("adj-findings-a.md", run=run_id)

    assert (code, out) == (2, "INVALID invalid-metadata\n")
    assert sorted(p.name for p in repo.root.iterdir()) == before


@pytest.mark.parametrize("command", ["record", "inspect"])
def test_vi6002_symlinked_run_directory_is_refused(
    repo: Repo, tmp_path: Path, command: str
) -> None:
    """VI-6002: a symlinked run directory refuses and the target stays untouched."""
    outside = tmp_path / "outside"
    outside.mkdir()
    reviews = repo.root / ".context" / "reviews"
    reviews.mkdir(parents=True)
    try:
        (reviews / NO_COHORT_RUN).symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable ({exc})")

    if command == "record":
        code, out, _ = repo.record("--fingerprint", FP_1)
    else:
        code, out, _ = repo.inspect("adj-findings-a.md")

    assert (code, out) == (3, "INVALID unsafe-artifact\n")
    assert list(outside.iterdir()) == []


def test_vi6002_symlinked_record_file_is_refused(repo: Repo, tmp_path: Path) -> None:
    """VI-6002: a record that is a symlink refuses, as does a non-regular file."""
    repo.record("--fingerprint", FP_1)
    target = tmp_path / "elsewhere.md"
    target.write_text((repo.run_dir() / "1-record.md").read_text("utf-8"), encoding="utf-8")
    (repo.run_dir() / "1-record.md").unlink()
    try:
        (repo.run_dir() / "1-record.md").symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink creation unavailable ({exc})")

    assert repo.record("--fingerprint", FP_2)[1] == "INVALID unsafe-artifact\n"


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFO unavailable")
def test_vi6002_non_regular_record_is_refused_without_blocking(repo: Repo) -> None:
    """VI-6002: a FIFO named like a record refuses before any read can block."""
    repo.run_dir().mkdir(parents=True)
    os.mkfifo(repo.run_dir() / "1-record.md")

    assert repo.inspect("adj-findings-a.md")[1] == "INVALID unsafe-artifact\n"


def test_vi6002_truncated_record_refuses_rather_than_being_skipped(repo: Repo) -> None:
    """VI-6002: a malformed record is an error in the count, never a silent zero."""
    repo.record("--fingerprint", FP_1)
    path = repo.run_dir() / "1-record.md"
    path.write_bytes(path.read_bytes()[:40])

    assert repo.record("--fingerprint", FP_2)[1] == "INVALID invalid-record\n"
    assert repo.inspect("adj-findings-a.md")[1] == "INVALID invalid-record\n"
    assert repo.records() == ["1-record.md"]


@pytest.mark.parametrize(
    "mutate",
    [
        lambda b: b.update(run_id=OTHER_RUN),
        lambda b: b.update(round=7),
        lambda b: b.update(form="sometimes"),
        lambda b: b.update(fingerprints=["xyz"]),
        lambda b: b.update(review_retry_count=-1),
        lambda b: b.update(override="yes"),
        lambda b: b.pop("stdout"),
    ],
    ids=["run-id", "round", "form", "fingerprint", "counter", "override", "missing-field"],
)
def test_vi6002_record_with_the_wrong_shape_refuses(repo: Repo, mutate: Any) -> None:
    """VI-6002: a well-formed JSON body that is not a record for this run refuses."""
    repo.record("--fingerprint", FP_1)
    path = repo.run_dir() / "1-record.md"
    body = json.loads(path.read_text("utf-8"))
    mutate(body)
    path.write_text(json.dumps(body), encoding="utf-8")

    assert repo.record("--fingerprint", FP_2)[1] == "INVALID invalid-record\n"


def test_vi6002_non_finite_number_in_a_record_refuses(repo: Repo) -> None:
    """VI-6002: `NaN` is not JSON, so it is not a record."""
    repo.record("--fingerprint", FP_1)
    path = repo.run_dir() / "1-record.md"
    path.write_text(path.read_text("utf-8").replace('"round": 1', '"round": NaN'), encoding="utf-8")

    assert repo.record("--fingerprint", FP_2)[1] == "INVALID invalid-record\n"


def test_vi6002_gap_in_the_round_sequence_refuses(repo: Repo) -> None:
    """VI-6002: records for rounds 1 and 3 refuse the count; they are not 2 rounds."""
    repo.record("--fingerprint", FP_1)
    repo.record("--fingerprint", FP_2)
    (repo.run_dir() / "2-record.md").rename(repo.run_dir() / "3-record.md")

    assert repo.record("--fingerprint", FP_3)[1] == "INVALID invalid-record\n"
    assert repo.inspect("adj-findings-a.md")[1] == "INVALID invalid-record\n"


def test_vi6002_non_canonical_record_name_refuses(repo: Repo) -> None:
    """VI-6002: `01-record.md` is a second spelling of round 1, not an ignorable file."""
    repo.record("--fingerprint", FP_1)
    (repo.run_dir() / "01-record.md").write_text("{}", encoding="utf-8")

    assert repo.record("--fingerprint", FP_2)[1] == "INVALID invalid-record\n"


def test_vi6002_missing_rules_file_refuses_rather_than_defaulting(
    repo: Repo, artifact: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """VI-6002: with no readable cap the budget is unknown, so nothing is recorded."""
    monkeypatch.setattr(artifact, "REVIEW_RULES_PATH", tmp_path / "absent.json")

    assert repo.record("--fingerprint", FP_1)[1] == "INVALID rules-unavailable\n"
    assert repo.records() == []


def test_vi6002_record_body_is_strict_json_with_every_field(repo: Repo) -> None:
    """VI-6002: one artifact per round, strict JSON, round numbered from the highest."""
    repo.record("--fingerprint", FP_2, "--fingerprint", FP_1)
    body = repo.body(1)

    assert body == {
        "record_version": 1,
        "run_id": NO_COHORT_RUN,
        "round": 1,
        "form": "findings",
        "fingerprints": sorted([FP_1, FP_2]),
        "clean_source": None,
        "clean_digest": None,
        "operation_id": None,
        "payload_digest": body["payload_digest"],
        "review_round_count": 1,
        "review_retry_count": 1,
        "max_review_retries": 2,
        "override": False,
        "authority_ref": None,
        "stdout": f"review-artifact: review record (findings) round=1 retry=1 fingerprints=2 for {NO_COHORT_RUN}",
    }


def test_vi6003_replayed_operation_returns_the_first_result_and_one_artifact(repo: Repo) -> None:
    """VI-6003: same id and payload replays; a different payload under that id refuses."""
    operation = ["--operation-id", f"{NO_COHORT_RUN}:1"]
    first = repo.record("--fingerprint", FP_1, *operation)
    replay = repo.record("--fingerprint", FP_1, *operation)

    assert first[0] == 0
    assert replay == first
    assert repo.records() == ["1-record.md"]

    conflict = repo.record("--fingerprint", FP_2, *operation)
    assert conflict[:2] == (3, "INVALID operation-refused\n")
    assert repo.records() == ["1-record.md"]

    # An earlier id still replays after a later round, which cohort state cannot do.
    later = repo.record("--fingerprint", FP_2, "--operation-id", f"{NO_COHORT_RUN}:2")
    assert later[0] == 0
    assert repo.record("--fingerprint", FP_1, *operation) == first
    assert repo.records() == ["1-record.md", "2-record.md"]


def test_vi6003_replay_returns_even_when_the_budget_is_spent(repo: Repo) -> None:
    """VI-6003: a completed write is not re-judged against the cap."""
    operation = ["--operation-id", f"{NO_COHORT_RUN}:2"]
    repo.record("--fingerprint", FP_1)
    first = repo.record("--fingerprint", FP_2, *operation)

    assert repo.record("--fingerprint", FP_2, *operation) == first
    assert repo.records() == ["1-record.md", "2-record.md"]


def test_vi6003_operation_id_must_name_this_run(repo: Repo) -> None:
    """VI-6003: the legacy id rules hold: the run part must be this run's id."""
    code, out, _ = repo.record("--fingerprint", FP_1, "--operation-id", f"{OTHER_RUN}:1")

    assert (code, out) == (3, "INVALID operation-refused\n")
    assert repo.records() == []


def _cap_parity_problems(skill: Path, default_cap: int) -> list[str]:
    """Return what is wrong with the review cap in `skill/review-rules.json`."""
    rules = json.loads((skill / "review-rules.json").read_text(encoding="utf-8"))
    problems = []
    if not isinstance(rules.get("rules_version"), str) or not rules["rules_version"]:
        problems.append("review-rules.json has no rules_version")
    if rules.get("max_review_retries") != default_cap:
        problems.append(
            "review-rules.json and the guard layer's default disagree on "
            "max_review_retries; change both together"
        )
    return problems


def _guard_default_cap() -> int:
    guards = support.load_script("core_work_loop_relocation_guards", SCRIPTS / "_loop_guards.py")
    return int(guards.DEFAULTS["max_review_retries"])


def test_vi6004_the_two_copies_of_the_review_cap_agree() -> None:
    """VI-6004: `review-rules.json` and the guard layer hold one `max_review_retries`."""
    assert _cap_parity_problems(SKILL, _guard_default_cap()) == []


def test_vi6004_a_one_sided_edit_fails_the_parity_check(tmp_path: Path) -> None:
    """VI-6004: changing the cap in the rules file alone fails the same check."""
    rules = json.loads((SKILL / "review-rules.json").read_text(encoding="utf-8"))
    rules["max_review_retries"] += 1
    (tmp_path / "review-rules.json").write_text(json.dumps(rules), encoding="utf-8")
    assert _cap_parity_problems(tmp_path, _guard_default_cap()) == [
        "review-rules.json and the guard layer's default disagree on "
        "max_review_retries; change both together"
    ]


def test_vi6002_override_reference_form_matches_the_supervisor(artifact: ModuleType) -> None:
    """VI-6002: the override's authority-reference pattern equals the supervisor's.

    `review-artifact.py` keeps its own copy so the dark-launched supervisor is
    never loaded outside itself; this pins the two forms together.
    """
    admission = support.load_script(
        "core_work_loop_relocation_admission", SCRIPTS / "_supervisor_admission.py"
    )
    assert artifact._AUTHORITY_RE.pattern == admission._AUTHORITY_RE.pattern
