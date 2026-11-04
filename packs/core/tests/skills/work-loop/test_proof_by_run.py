"""Construction tests for the proof-by-run predicate.

Mode: TDD (proof-by-run-evidence plan T1). The suite loads the shipped
work-loop script by literal path and calls the predicate directly.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)
COMMIT = "a" * 40
OTHER_COMMIT = "b" * 40


def _load_module(module_name: str, path: Path) -> ModuleType:
    """Load a work-loop script by literal path for pack-boundary tests."""
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


@pytest.fixture(scope="module")
def review_assessment() -> ModuleType:
    """Load the assessment module under a unique name."""
    return _load_module(
        "review_assessment_proof_by_run", SCRIPTS / "_review_assessment.py"
    )


@pytest.fixture(scope="module")
def review_contracts() -> ModuleType:
    """Load the review contract validators."""
    return _load_module("review_contracts_proof_by_run", SCRIPTS / "_review_contracts.py")


def _review_subject() -> dict:
    """Build the current review subject."""
    return {
        "schema_version": 1,
        "review_subject_id": "review-subject-pbr",
        "review_subject_fingerprint": "review-subject-fp-pbr",
        "delivery_subject_ref": {
            "subject_id": "delivery-subject-pbr",
            "acceptance_fingerprint": "acceptance-fp-pbr",
        },
        "normalized_paths": ["packs/core/.apm/skills/work-loop/scripts/_review_assessment.py"],
        "normalized_statuses": ["added"],
        "review_policy_fingerprint": "review-policy-pbr",
        "lineage": {"provider": "proof-by-run-test", "projection_version": "1.0"},
    }


def _finding() -> dict:
    """Build a valid structured finding."""
    return {
        "schema_version": 1,
        "finding_id": "finding-pbr",
        "rule_ref": "AC-0001",
        "observation": "A command reproduces the failure.",
        "reachable_path": "command to failing exit",
        "actual_failure": "The command exits non-zero before the fix.",
        "affected_acceptance_criteria": ["AC-0001"],
        "evidence_refs": ["evidence:observation"],
        "material": True,
    }


def _report(subject: dict, finding: dict) -> dict:
    """Build a findings report containing one finding."""
    return {
        "schema_version": 1,
        "report_id": "report-pbr",
        "role": "quality-engineer",
        "subject": copy.deepcopy(subject),
        "terminal_status": "findings",
        "lineage": {
            "sequence": 1,
            "review_policy_fingerprint": subject["review_policy_fingerprint"],
            "source_event_id": "source-report-pbr",
            "producer": "synthetic-reviewer",
        },
        "findings": [copy.deepcopy(finding)],
    }


def _sha(text: str) -> str:
    """Return the SHA-256 hex digest of text."""
    return hashlib.sha256(text.encode()).hexdigest()


def _envelope(commit: str = COMMIT, exit_status: int = 1) -> dict:
    """Build a run envelope bound to a commit."""
    return {
        "command_sha256": _sha("pytest -q"),
        "exit_status": exit_status,
        "stderr_sha256": _sha("err"),
        "stdout_sha256": _sha("out"),
        "subject_commit": commit,
    }


def _call(module: ModuleType, **overrides: object) -> dict:
    """Call the predicate with a consistent fixture, applying overrides."""
    subject = _review_subject()
    report = _report(subject, _finding())
    kwargs: dict = {
        "assessment_id": "assessment-pbr",
        "report_id": report["report_id"],
        "finding_id": report["findings"][0]["finding_id"],
        "review_subject_fingerprint": subject["review_subject_fingerprint"],
        "observed": "fail",
        "envelope": _envelope(),
        "current_subject_commit": COMMIT,
        "judgment_authority": "authority:controller",
    }
    kwargs.update(overrides)
    return module.proof_by_run_assessment(**kwargs)


def _digest(envelope: dict) -> str:
    """Recompute the envelope digest independently of the implementation."""
    text = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode()).hexdigest()


def test_t1_fail_is_supported_with_one_recomputable_reference(
    review_assessment: ModuleType, review_contracts: ModuleType
) -> None:
    """AC-0001: a bound fail maps to supported with one proof-run reference."""
    envelope = _envelope()
    record = _call(review_assessment, envelope=envelope)
    ok, code = review_contracts.validate_finding_assessment_dict(record)
    assert ok, code
    assert record["assessment"] == "supported"
    assert record["lineage"] == {
        "predicate_version": "proof-by-run.v1",
        "judgment_authority": "authority:controller",
    }
    assert record["evidence_refs"] == [f"proof-run:v1:{COMMIT}:fail:{_digest(envelope)}"]


def test_t1_envelope_digest_ignores_key_order_and_covers_five_fields(
    review_assessment: ModuleType,
) -> None:
    """AC-0001: the digest is canonical over exactly the five fields."""
    envelope = _envelope()
    reordered = dict(reversed(list(envelope.items())))
    ref = review_assessment.proof_run_reference("fail", reordered)
    assert ref == f"proof-run:v1:{COMMIT}:fail:{_digest(envelope)}"
    changed = review_assessment.proof_run_reference("fail", _envelope(exit_status=2))
    assert changed != ref


def test_t1_pass_is_unsupported_opinion(
    review_assessment: ModuleType, review_contracts: ModuleType
) -> None:
    """AC-0002: a bound pass maps to unsupported-opinion, never supported."""
    envelope = _envelope(exit_status=0)
    record = _call(review_assessment, observed="pass", envelope=envelope)
    ok, code = review_contracts.validate_finding_assessment_dict(record)
    assert ok, code
    assert record["assessment"] == "unsupported-opinion"
    assert record["evidence_refs"] == [f"proof-run:v1:{COMMIT}:pass:{_digest(envelope)}"]


def test_t1_stale_envelope_is_refused(review_assessment: ModuleType) -> None:
    """AC-0003: an envelope for another commit is refused as stale."""
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, envelope=_envelope(OTHER_COMMIT))
    assert caught.value.denial_code == "denied-proof-run-stale"


@pytest.mark.parametrize("observed", ["", "FAIL", "error", None, True])
def test_t1_invalid_observation_is_refused(
    review_assessment: ModuleType, observed: object
) -> None:
    """AC-0004: only fail or pass are accepted observations."""
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, observed=observed)
    assert caught.value.denial_code == "denied-invalid-proof-run-observation"


@pytest.mark.parametrize("commit", ["a" * 39, "A" * 40, "g" * 40, "a" * 41, "", "a" * 40 + "\n"])
def test_t1_invalid_commit_is_refused_on_either_side(
    review_assessment: ModuleType, commit: str
) -> None:
    """AC-0004: both commits must be 40 or 64 lowercase hex characters."""
    for overrides in (
        {"current_subject_commit": commit},
        {"envelope": _envelope(commit), "current_subject_commit": commit},
    ):
        with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
            _call(review_assessment, **overrides)
        assert caught.value.denial_code == "denied-invalid-proof-run-commit"


def test_t1_sha256_length_commit_is_accepted(review_assessment: ModuleType) -> None:
    """AC-0004: a 64-character lowercase hex commit is valid."""
    commit = "c" * 64
    record = _call(
        review_assessment, envelope=_envelope(commit), current_subject_commit=commit
    )
    assert record["assessment"] == "supported"


@pytest.mark.parametrize(
    "field",
    ["command_sha256", "exit_status", "stderr_sha256", "stdout_sha256", "subject_commit"],
)
def test_t1_envelope_missing_field_is_refused(
    review_assessment: ModuleType, field: str
) -> None:
    """AC-0004: an envelope missing any of its five fields is refused."""
    envelope = _envelope()
    del envelope[field]
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, envelope=envelope)
    assert caught.value.denial_code == "denied-invalid-proof-run-envelope"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda e: e.update(extra="x"),
        lambda e: e.update(exit_status="1"),
        lambda e: e.update(exit_status=True),
        lambda e: e.update(stdout_sha256="nothex"),
        lambda e: e.update(subject_commit=7),
    ],
)
def test_t1_envelope_extra_or_mistyped_field_is_refused(
    review_assessment: ModuleType, mutate: object
) -> None:
    """AC-0004: extra fields and wrong types are refused."""
    envelope = _envelope()
    mutate(envelope)  # type: ignore[operator]
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, envelope=envelope)
    assert caught.value.denial_code == "denied-invalid-proof-run-envelope"


def test_t1_non_dict_envelope_is_refused(review_assessment: ModuleType) -> None:
    """AC-0004: a non-mapping envelope is refused."""
    with pytest.raises(review_assessment.ReviewAssessmentRefused) as caught:
        _call(review_assessment, envelope=[])
    assert caught.value.denial_code == "denied-invalid-proof-run-envelope"


# --- Supervisor consistency check (plan T2, integration) -------------------

_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")
sup = _helper("supervisor_support")


def _result(request: dict, **fields: object) -> dict:
    """Wrap a controller result for a request."""
    return {
        "schema_version": 1,
        "request_id": request["request_id"],
        "run_id": request["run_id"],
        "kind": request["kind"],
        **fields,
    }


def _next(repo: Path) -> dict:
    """Return the current request."""
    code, payload = h.run_cli(repo, "next", h.SPEC_DIR)
    assert code == 0, payload
    return payload["request"]


def _assess_request(tmp_path: Path) -> tuple[Path, object, dict]:
    """Drive a real run to its first assess-finding request."""
    repo = h.make_repo(tmp_path)
    assert h.start(repo)[0] == 0
    controller = h.Controller(repo, tmp_path / "effects.log")
    request: dict = {}
    for _ in range(60):
        request = _next(repo)
        if request["kind"] == "review-role":
            break
        if request["kind"] == "external-effect":
            controller.handle_effect(request)
            continue
        code, admitted = controller.report(controller.work(request))
        assert code == 0, admitted
    assert request["kind"] == "review-role"
    code, admitted = controller.report(
        _result(request, selection=h.select_none(request))
    )
    assert code == 0, admitted
    role_request = _next(repo)
    report = h.report_review("adversarial-reviewer", role_request["review_subject"], 1)
    report["findings"][0]["material"] = True
    code, admitted = controller.report(_result(role_request, report=report))
    assert code == 0, admitted
    assess = _next(repo)
    assert assess["kind"] == "assess-finding"
    return repo, controller, assess


def _pbr(review_assessment: ModuleType, request: dict, observed: str, commit: str) -> dict:
    """Build a proof-by-run assessment for a request."""
    return review_assessment.proof_by_run_assessment(
        assessment_id="assessment-pbr",
        report_id=request["report_id"],
        finding_id=request["finding_id"],
        review_subject_fingerprint=request["review_subject_fingerprint"],
        observed=observed,
        envelope=_envelope(commit, 1 if observed == "fail" else 0),
        current_subject_commit=commit,
        judgment_authority="reviewer:test",
    )


def _ref(observed: str, commit: str) -> str:
    """Build a well-formed proof-run reference."""
    return f"proof-run:v1:{commit}:{observed}:{'c' * 64}"


def _bad_none(a: dict, head: str) -> None:
    a["evidence_refs"] = ["calc.py"]


def _bad_two(a: dict, head: str) -> None:
    a["evidence_refs"] = [a["evidence_refs"][0], _ref("fail", head)]


def _bad_commit(a: dict, head: str) -> None:
    a["evidence_refs"] = [_ref("fail", OTHER_COMMIT)]


def _bad_fail_unsupported(a: dict, head: str) -> None:
    a["evidence_refs"] = [_ref("fail", head)]
    a["assessment"] = "unsupported-opinion"


def _bad_pass_supported(a: dict, head: str) -> None:
    a["evidence_refs"] = [_ref("pass", head)]
    a["assessment"] = "supported"


@sup.INTEGRATION
@pytest.mark.parametrize(
    "corrupt",
    [_bad_none, _bad_two, _bad_commit, _bad_fail_unsupported, _bad_pass_supported],
)
def test_t2_inconsistent_proof_by_run_assessment_is_refused(
    tmp_path: Path, review_assessment: ModuleType, corrupt: object
) -> None:
    """An inconsistent proof-by-run assessment is refused and writes nothing."""
    repo, controller, assess = _assess_request(tmp_path)
    head = h.git(repo, "rev-parse", "HEAD").strip()
    record = _pbr(review_assessment, assess, "fail", head)
    corrupt(record, head)  # type: ignore[operator]
    code, refused = controller.report(_result(assess, assessment=record))
    assert code == 1, refused
    assert refused["refusal"]["code"] == "review-record-refused", refused
    assert h.git(repo, "rev-parse", "HEAD").strip() == head


@sup.INTEGRATION
def test_t2_consistent_proof_by_run_assessment_is_admitted(
    tmp_path: Path, review_assessment: ModuleType
) -> None:
    """A consistent supported proof-by-run assessment is admitted and repair is requested."""
    repo, controller, assess = _assess_request(tmp_path)
    head = h.git(repo, "rev-parse", "HEAD").strip()
    record = _pbr(review_assessment, assess, "fail", head)
    code, admitted = controller.report(_result(assess, assessment=record))
    assert code == 0, admitted
    assert h.git(repo, "rev-parse", "HEAD").strip() != head
    evidence = h.git(repo, "show", f"HEAD:{h.SPEC_DIR}/delivery/evidence.jsonl")
    assert "repair-request" in evidence


@sup.INTEGRATION
def test_t2_default_v1_assessment_is_admitted_unchanged(tmp_path: Path) -> None:
    """The harness's predicate_version v1 assessment still passes the check."""
    repo, controller, assess = _assess_request(tmp_path)
    code, admitted = controller.report(_result(assess, assessment=h.assessment(assess)))
    assert code == 0, admitted


# --- proof-run CLI (plan T4) -----------------------------------------------

_T4_ALLOWED = {"rev-parse", "status"}
_T4_FLAG_PREFIXES = ("--git-dir=", "--work-tree=", "--no-replace-objects", "--literal-pathspecs")
_T4_MIB = 1024 * 1024


@pytest.fixture(scope="module")
def t4_gate() -> ModuleType:
    """The shipped evidence-gate CLI under a name unique to this suite."""
    return _load_module("work_loop_proof_by_run_evidence_gate", SCRIPTS / "evidence-gate.py")


def _t4_subcommand(argv: list[str]) -> str:
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "-c":
            index += 2
        elif token.startswith(_T4_FLAG_PREFIXES):
            index += 1
        else:
            return token
    raise AssertionError(f"no subcommand in {argv}")


def _t4_helper_call(argv: list[str]) -> bool:
    sub = _t4_subcommand(argv)
    if sub in {"version", "config"}:
        return True
    return sub == "rev-parse" and "--show-toplevel" in argv and "--git-common-dir" in argv


class _T4Launches(list):
    """Recorded Git vectors; a test of a refusal made before the first launch sets ``expect_empty``."""

    expect_empty = False


@pytest.fixture
def t4_launches(t4_gate: ModuleType, monkeypatch: pytest.MonkeyPatch):
    """Record every launch; at teardown only rev-parse and status may appear besides helper reads."""
    module = t4_gate.supervisor_git()
    recorded = _T4Launches()
    real = module._launch

    def spy(argv: list[str], **kwargs: object) -> object:
        recorded.append(list(argv))
        return real(argv, **kwargs)

    monkeypatch.setattr(module, "_launch", spy)
    yield recorded
    if recorded.expect_empty:
        assert recorded == [], "a refusal made before the first launch launched Git"
    else:
        assert recorded, "no Git launch was recorded"
    for argv in recorded:
        if not _t4_helper_call(argv):
            assert _t4_subcommand(argv) in _T4_ALLOWED, argv


def _t4_git(cwd: Path, *args: str) -> str:
    import subprocess

    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@example.invalid",
    }
    done = subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, check=True)
    return done.stdout.decode().strip()


class _T4Repo:
    """A temporary repository with one commit and a populated ``.context/``."""

    def __init__(self, root: Path) -> None:
        self.path = root.resolve() / "work"
        self.path.mkdir()
        _t4_git(self.path, "init", "-q", "-b", "main")
        (self.path / ".gitignore").write_text(".context/\n")
        self.commit("tracked.txt", "one\n")
        self.context = self.path / ".context"
        self.context.mkdir()
        self.files = {}
        for name, text in (("cmd.txt", "pytest -q"), ("out.txt", "out"), ("err.txt", "err")):
            (self.context / name).write_text(text)
            self.files[name] = self.context / name

    def commit(self, name: str, text: str) -> str:
        (self.path / name).write_text(text)
        _t4_git(self.path, "add", "--", name)
        _t4_git(self.path, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "c")
        return _t4_git(self.path, "rev-parse", "HEAD")

    def args(self, **over: str) -> list[str]:
        values = {
            "--report-id": "report-pbr", "--finding-id": "finding-pbr",
            "--assessment-id": "assessment-pbr",
            "--review-subject-fingerprint": "review-subject-fp-pbr",
            "--observed": "fail", "--exit-status": "1",
            "--authority": "authority:controller",
            "--command-file": str(self.files["cmd.txt"]),
            "--stdout-file": str(self.files["out.txt"]),
            "--stderr-file": str(self.files["err.txt"]),
            **over,
        }
        return ["proof-run", *[x for pair in values.items() for x in pair]]

    def envelopes(self) -> list[Path]:
        folder = self.context / "proof-runs"
        return sorted(folder.iterdir()) if folder.is_dir() and not folder.is_symlink() else []


@pytest.fixture
def t4_repo(tmp_path: Path) -> _T4Repo:
    return _T4Repo(tmp_path)


@pytest.fixture
def t4_run(t4_gate, t4_repo, t4_launches, capsys, monkeypatch):
    """Run ``proof-run`` in the repository; return ``(exit code, parsed stdout)``."""
    monkeypatch.chdir(t4_repo.path)

    def invoke(**over: str) -> tuple[int, dict]:
        code = t4_gate.main(t4_repo.args(**over))
        return code, json.loads(capsys.readouterr().out)

    return invoke


def test_t4_happy_path_writes_envelope_and_prints_recomputable_reference(
    t4_run, t4_repo, t4_launches
) -> None:
    code, out = t4_run()
    assert code == 0, out
    head = _t4_git(t4_repo.path, "rev-parse", "HEAD")
    files = t4_repo.envelopes()
    assert len(files) == 1
    stored = json.loads(files[0].read_text())
    assert stored["stdout"] == "out" and stored["stderr"] == "err"
    assert stored["command"] == "pytest -q"
    five = {k: stored[k] for k in (
        "command_sha256", "exit_status", "stderr_sha256", "stdout_sha256", "subject_commit")}
    assert five["subject_commit"] == head and five["exit_status"] == 1
    assert five["stdout_sha256"] == _sha("out")
    digest = _digest(five)
    sha_assessment = hashlib.sha256(b"assessment-pbr").hexdigest()
    assert files[0].name == f"{sha_assessment}-{digest}.json"
    assessment = out["assessment"]
    assert assessment["assessment"] == "supported"
    assert assessment["evidence_refs"] == [f"proof-run:v1:{head}:fail:{digest}"]
    subs = {_t4_subcommand(a) for a in t4_launches if not _t4_helper_call(a)}
    assert subs == {"rev-parse", "status"}


def test_t4_redo_after_new_commit_adds_envelope_and_identical_rerun_does_not_write(
    t4_run, t4_repo
) -> None:
    assert t4_run()[0] == 0
    (first,) = t4_repo.envelopes()
    before = first.stat().st_mtime_ns
    assert t4_run()[0] == 0
    assert t4_repo.envelopes() == [first]
    assert first.stat().st_mtime_ns == before
    t4_repo.commit("tracked.txt", "two\n")
    assert t4_run()[0] == 0
    assert len(t4_repo.envelopes()) == 2


def _t4_refused(result: tuple[int, dict], code: str, repo: _T4Repo, before: list[Path]) -> None:
    assert result[0] == 2, result
    assert result[1]["refused"] == code
    assert repo.envelopes() == before


def test_t4_dirty_tracked_file_is_refused(t4_run, t4_repo) -> None:
    (t4_repo.path / "tracked.txt").write_text("dirty\n")
    _t4_refused(t4_run(), "denied-tree-dirty", t4_repo, [])


def test_t4_existing_envelope_with_different_bytes_is_refused(t4_run, t4_repo) -> None:
    assert t4_run()[0] == 0
    (target,) = t4_repo.envelopes()
    target.write_text("different")
    _t4_refused(t4_run(), "denied-envelope-exists", t4_repo, [target])
    assert target.read_text() == "different"


def test_t4_envelope_path_that_is_a_symlink_is_refused(t4_run, t4_repo) -> None:
    assert t4_run()[0] == 0
    (target,) = t4_repo.envelopes()
    keep = t4_repo.context / "keep.json"
    target.rename(keep)
    target.symlink_to(keep)
    _t4_refused(t4_run(), "denied-envelope-exists", t4_repo, [target])
    assert target.is_symlink()


def test_t4_symlinked_proof_runs_directory_is_refused(t4_run, t4_repo) -> None:
    elsewhere = t4_repo.path.parent / "elsewhere"
    elsewhere.mkdir()
    (t4_repo.context / "proof-runs").symlink_to(elsewhere)
    result = t4_run()
    assert result[0] == 2 and result[1]["refused"] == "denied-proof-runs-dir"
    assert list(elsewhere.iterdir()) == []


def test_t4_input_outside_context_is_refused(t4_run, t4_repo) -> None:
    outside = t4_repo.path / "outside.txt"
    outside.write_text("x")
    _t4_refused(t4_run(**{"--stdout-file": str(outside)}), "denied-input-path", t4_repo, [])


def test_t4_input_under_reviews_is_refused(t4_run, t4_repo) -> None:
    (t4_repo.context / "reviews").mkdir()
    held = t4_repo.context / "reviews" / "r.txt"
    held.write_text("x")
    _t4_refused(t4_run(**{"--stderr-file": str(held)}), "denied-input-path", t4_repo, [])


def test_t4_fifo_input_is_refused(t4_run, t4_repo) -> None:
    fifo = t4_repo.context / "pipe"
    os.mkfifo(fifo)
    _t4_refused(t4_run(**{"--stdout-file": str(fifo)}), "denied-input-unreadable", t4_repo, [])


def test_t4_oversized_stdout_is_refused(t4_run, t4_repo) -> None:
    big = t4_repo.context / "big.txt"
    big.write_bytes(b"x" * (_T4_MIB + 1))
    _t4_refused(t4_run(**{"--stdout-file": str(big)}), "denied-input-too-large", t4_repo, [])


def test_t4_unknown_argument_is_refused_before_any_launch(
    t4_gate, t4_repo, t4_launches, capsys, monkeypatch
) -> None:
    t4_launches.expect_empty = True
    monkeypatch.chdir(t4_repo.path)
    assert t4_gate.main([*t4_repo.args(), "--extra", "x"]) == 2
    assert json.loads(capsys.readouterr().out)["refused"] == "denied-not-in-catalog"
    assert not t4_launches


# --- T5: shipped guidance and eval cases (content checks) -------------------

_SKILL_DIR = SCRIPTS.parent
_AGENT = SCRIPTS.parents[2] / "agents" / "finding-adjudicator.md"


def _section(path: Path, heading: str) -> str:
    """Return text from ``heading`` to the next heading of the same level."""
    text = path.read_text(encoding="utf-8")
    level = heading.split(" ", 1)[0]
    start = text.index("\n" + heading + "\n") + 1
    following = text.find("\n" + level + " ", start + len(heading))
    return text[start : following if following != -1 else len(text)]


def test_t5_fix_section_points_at_recorded_before_run() -> None:
    section = _section(_SKILL_DIR / "SKILL.md", "## FIX")
    assert "already recorded as the finding's assessment" in section
    assert "references/supervisor.md#review" in section
    assert "passes before the fix is Surfaced instead of fixed" in section
    assert "Failing means its exit status or printed output shows the defect" in section
    assert "passing means it no longer does" in section


def test_t5_supervisor_review_section_names_predicate_and_run_order() -> None:
    section = " ".join(
        _section(_SKILL_DIR / "references" / "supervisor.md", "### Review").split()
    )
    assert "`proof-by-run.v1`" in section
    assert "`supported`" in section and "`unsupported-opinion`" in section
    assert "evidence-gate.py' proof-run" in section
    assert "`assess-finding` request" in section
    assert "before the controller reports it" in section
    assert "controller's attestation" in section
    assert "only for consistency and for the current commit" in section
    assert "refuses an inconsistent proof-by-run assessment" in section
    assert "`review-record-refused`" in section


def test_t5_adjudicator_tools_unchanged() -> None:
    lines = _AGENT.read_text(encoding="utf-8").splitlines()
    assert "tools: Read, Grep" in lines


def test_t5_eval_cases_have_required_fields() -> None:
    data = json.loads((_SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8"))
    cases = {case["id"]: case for case in data["evals"]}
    for case_id in (
        "proof-by-run-passing-command-not-fixed",
        "git-history-settles-base-versus-change",
        "adjudicator-git-tool-refused",
    ):
        case = cases[case_id]
        assert case["prompt"].strip() and case["expected_output"].strip()
        assert case["assertions"] and all(a.strip() for a in case["assertions"])
    assert "unsupported-opinion" in cases["proof-by-run-passing-command-not-fixed"]["expected_output"]
    assert "git-history" in cases["git-history-settles-base-versus-change"]["expected_output"]
    assert "Refused" in cases["adjudicator-git-tool-refused"]["expected_output"]


def test_t9_identical_rerun_holds_for_maximal_inflating_input(t4_run, t4_repo) -> None:
    """Three 1 MiB inputs of control and non-ASCII bytes inflates in the file yet reruns cleanly."""
    unit = b"\x1b[31m\xe2\x9c\x93\x00"
    size = 1024 * 1024
    for name in ("cmd.txt", "out.txt", "err.txt"):
        t4_repo.files[name].write_bytes((unit * (size // len(unit) + 1))[:size])
    assert t4_run()[0] == 0
    (first,) = t4_repo.envelopes()
    data, before = first.read_bytes(), first.stat().st_mtime_ns
    assert len(data) > 4 * size
    assert t4_run()[0] == 0
    assert t4_repo.envelopes() == [first]
    assert first.read_bytes() == data and first.stat().st_mtime_ns == before


# --- T10: the tree check runs no configured program -------------------------


def _t10_submodule(repo: _T4Repo, tmp_path: Path) -> Path:
    """Add a one-file submodule to *repo*, commit it, and return the submodule path."""
    origin = tmp_path / "origin"
    origin.mkdir()
    _t4_git(origin, "init", "-q", "-b", "main")
    (origin / "f.txt").write_text("one\n")
    (origin / ".gitattributes").write_text("f.txt filter=x\n")
    _t4_git(origin, "add", "--", ".")
    _t4_git(origin, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "s")
    _t4_git(repo.path, "-c", "protocol.file.allow=always", "submodule", "add", "-q",
            str(origin), "s")
    _t4_git(repo.path, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "add s")
    return repo.path / "s"


def test_t10_submodule_filter_config_is_never_run(t4_run, t4_repo, tmp_path: Path) -> None:
    sub = _t10_submodule(t4_repo, tmp_path)
    marker = tmp_path / "marker"
    script = tmp_path / "filter.sh"
    script.write_text(f"#!/bin/sh\ntouch {marker}\ncat\n")
    script.chmod(0o755)
    _t4_git(sub, "config", "filter.x.clean", str(script))
    (sub / "f.txt").write_text("one\n")  # same bytes, new stat data
    os.utime(sub / "f.txt", (1, 1))
    code, out = t4_run()
    assert code == 0, out
    assert not marker.exists()


def test_t10_submodule_at_other_commit_is_dirty(t4_run, t4_repo, tmp_path: Path) -> None:
    sub = _t10_submodule(t4_repo, tmp_path)
    (sub / "f.txt").write_text("two\n")
    _t4_git(sub, "add", "--", "f.txt")
    _t4_git(sub, "-c", "commit.gpgsign=false", "commit", "-q", "-m", "moved")
    _t4_refused(t4_run(), "denied-tree-dirty", t4_repo, [])


def test_t10_code_running_config_is_refused_before_any_run(
    t4_run, t4_repo, t4_launches
) -> None:
    _t4_git(t4_repo.path, "config", "gpg.program", "/bin/true")
    _t4_refused(t4_run(), "denied-git-config", t4_repo, [])
    assert all(_t4_helper_call(argv) for argv in t4_launches), t4_launches


# --- T11: input exclusion by directory identity -----------------------------


def _t11_folds_case(folder: Path) -> bool:
    probe = folder / "CaseProbe"
    probe.write_text("x")
    try:
        return (folder / "caseprobe").exists()
    finally:
        probe.unlink()


@pytest.mark.parametrize(("real", "alias"), [("reviews", "Reviews"), ("proof-runs", "Proof-Runs")])
def test_t11_case_folded_excluded_folder_is_refused(
    t4_run, t4_repo, real: str, alias: str
) -> None:
    if not _t11_folds_case(t4_repo.context):
        pytest.skip("file system is case-sensitive: probe found no case folding")
    (t4_repo.context / real).mkdir()
    (t4_repo.context / real / "x").write_text("held")
    result = t4_run(**{"--stdout-file": str(t4_repo.context / alias / "x")})
    assert result[0] == 2 and result[1]["refused"] == "denied-input-path"
    assert [f.name for f in t4_repo.envelopes() if f.name != "x"] == []


def test_t11_identity_helper_compares_device_and_inode_not_names(t4_gate) -> None:
    barred = (7, 100)
    other = (7, 200)
    check = t4_gate._passes_through_excluded
    assert check([other, barred], [barred, (7, 300)])  # any name, excluded identity
    assert not check([other, (8, 100)], [barred, None])  # same inode, other device
    assert not check([None, other], [barred])
    assert not check([], [barred])
