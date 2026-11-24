"""Run application-only release journeys with only the two installed skills."""

from __future__ import annotations

import base64
import copy
import hashlib
import importlib.util
import json
import shutil
import sys
import zipfile
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[2]


def load(path: Path, name: str) -> ModuleType:
    """Load a pack-qualified helper or installed script without changing sys.path."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


preparation = load(
    HERE / "test_release_admission_journey.py",
    "release_engineering_release_loop_github_journey_preparation",
)
settings = load(
    HERE / "test_github_release_readiness.py",
    "release_engineering_release_loop_github_journey_settings",
)
NOW = preparation.helpers.NOW


class GithubJourney(preparation.Journey):
    """Drive installed entry points, stopping on refusals and recovery pauses."""

    github: ModuleType
    controls: dict[str, Any]
    snapshot: dict[str, Any]

    def call(self, name: str, module: ModuleType, *args: str) -> bool:
        """Record one JSON response and let only successful, unpaused steps proceed."""
        timed = module is not self.github or args[0] in {"budget", "recheck", "summary"}
        code = module.main([*args, "--root", str(self.root), *(["--now", NOW] if timed else [])])
        output = self.capsys.readouterr()
        assert output.err == ""
        result = json.loads(output.out)
        self.trace.append((name, code, result))
        return code == 0 and result["status"] != "pause"

    def isolated(self) -> None:
        """Prove there is no link or other pack reachable inside the temporary root."""
        assert {p.name for p in (self.root / "skills").iterdir()} == {
            "release-loop", "prepare-release-handoff"
        }
        for path in self.root.rglob("*"):
            assert not path.is_symlink()
            assert path.resolve().is_relative_to(self.root.resolve())
            assert path.name not in {"packs", "core", "iac-terraform", ".claude", "work-loop"}
        for module in (self.collector, self.admission, self.admission.handoff,
                       self.github, self.github.admission, self.github.handoff):
            assert Path(module.__file__).resolve().is_relative_to(self.root.resolve())

    def check_reviews(self, stage: str) -> list[str]:
        """Validate both synthetic reviews against the installed, byte-pinned rubrics."""
        names: list[str] = self.reviews(stage)
        for name, role in zip(names, preparation.AREAS, strict=True):
            assert self.call(
                f"{stage}-{role}", self.admission, "check-review", name,
                "--admission", "admission.json", "--rubric",
                f"skills/release-loop/references/{role}-review.md",
            ), self.trace[-1]
            assert self.trace[-1][2]["status"] == "pass"
        return names

    def capture_job(self, reviews: list[str]) -> str:
        """Save GitHub captures with the deploy-job example's file names and shapes."""
        c = self.controls
        digest = hashlib.sha256((self.root / "admission.json").read_bytes()).hexdigest()
        environment = copy.deepcopy(self.snapshot["environment"])
        environment.update(id=5, name=c["environment"])
        context = {
            "GITHUB_REPOSITORY": c["repository"], "GITHUB_REPOSITORY_ID": str(c["repository_id"]),
            "GITHUB_RUN_ID": "42", "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_WORKFLOW_REF": c["repository"] + "/" + c["deploy_workflow"] + "@refs/heads/main",
            "GITHUB_WORKFLOW_SHA": "a" * 40, "GITHUB_REF": "refs/heads/main",
            "GITHUB_TRIGGERING_ACTOR": c["agent"]["login"], "environment": c["environment"],
        }
        attempt = {
            "id": 42, "run_attempt": 1, "path": c["deploy_workflow"], "head_branch": "main",
            "head_sha": "a" * 40, "event": "workflow_dispatch", "status": "in_progress",
            "conclusion": None, "repository": {"id": c["repository_id"], "full_name": c["repository"]},
            "triggering_actor": {"login": c["agent"]["login"], "id": 7},
            "actor": {"login": c["agent"]["login"], "id": 7},
        }
        prepare = copy.deepcopy(attempt)
        prepare.update(id=41, path=c["prepare_workflow"], status="completed", conclusion="success")
        # A real ZIP contains precisely the files allowed by verify-admission in the example.
        members = {"release-handoff.yaml", "admission.json", "image-manifest.json",
                   "provenance-attestation.json", "test-report.json", "security-report.json",
                   "approved-procedure.txt", "trusted-policy.json", "README.md", "ci-workflow.example.yml"}
        with zipfile.ZipFile(self.root / "artifact.zip", "w") as archive:
            for name in sorted(members):
                archive.write(self.root / name, name)
        self.write("prepare-artifacts.json", {"total_count": 1, "artifacts": [{
            "id": 19, "name": "release-candidate", "expired": False,
            "digest": preparation.helpers.digest((self.root / "artifact.zip").read_bytes()),
            "workflow_run": {"id": 41, "repository_id": c["repository_id"],
                             "head_branch": "main", "head_sha": "a" * 40},
        }]})
        records = [json.loads((self.root / name).read_bytes()) for name in reviews]
        encoded = base64.b64encode(json.dumps(records).encode()).decode()
        assert len(encoded) <= 60000
        for index, record in enumerate(json.loads(base64.b64decode(encoded, validate=True))):
            self.write(f"review-{index}.json", record)
        for name, value in {
            "environment": environment, "context": context, "attempt": attempt, "prepare-run": prepare,
            "approvals": [{"environments": [{"id": 5, "name": c["environment"]}],
                           "state": "approved", "user": {"login": "example-reviewer", "id": 789,
                                                         "type": "User"},
                           "comment": "Reviewed admission:" + digest}],
        }.items():
            self.write(name + ".json", value)
        return digest

    def capture_audit(self) -> None:
        """Model provider write receipt, locked head, listing and exact version read-back."""
        decision = (self.root / "decision.json").read_bytes()
        checksum = base64.b64encode(hashlib.sha256(decision).digest()).decode()
        key = "decisions/sandbox/42-1.json"
        self.write("receipt.json", {"Key": key, "VersionId": "example-version",
                                    "ChecksumSHA256": checksum, "ETag": "example-etag"})
        self.write("audit-head.json", {
            "VersionId": "example-version", "ChecksumSHA256": checksum,
            "LastModified": "2026-01-01T12:29:59+00:00", "ObjectLockMode": "COMPLIANCE",
            "ObjectLockRetainUntilDate": "2026-01-09T00:00:00Z", "Metadata": {},
        })
        self.write("listing.json", [{"Prefix": "decisions/sandbox/", "IsTruncated": False, "DeleteMarkers": [], "Versions": [{
            "Key": key, "VersionId": "example-version", "IsLatest": True, "LastModified": NOW,
        }]}, {"Prefix": "ops/sandbox/", "IsTruncated": False}])
        (self.root / "readback.json").write_bytes(decision)
        shutil.copyfile(self.root / "audit-head.json", self.root / "readback-head.json")

    def run(self, failure: str | None = None) -> None:
        """Collect through final, with a single injected fault at its real boundary."""
        self.isolated()
        self.write("request.json", self.request)
        if not self.call("collect", self.collector, "collect", "request.json", "--policy",
                         "trusted-policy.json", "--output", "release-handoff.yaml"):
            return
        assert self.trace[-1][2] == {"status": "ready", "gaps": []}
        if not self.call("admit", self.admission, "admit", "release-handoff.yaml", "--policy",
                         "trusted-policy.json", "--expect-environment", "sandbox",
                         "--expect-account", "example-sandbox", "--output", "admission.json"):
            return
        reviews = self.check_reviews("pre-deploy")
        if not self.stage("admission", []):
            return
        if not self.stage("pre-deploy", reviews):
            return
        if failure == "missing-protection":
            self.snapshot["environment"]["protection_rules"] = []
        elif failure == "missing-audit-settings":
            self.snapshot.pop("audit_store")
        self.write("snapshot.json", self.snapshot)
        args = ["readiness", "--controls", "controls.json", "--snapshot", "snapshot.json"]
        for name in ("prepare", "deploy", "deploy-job"):
            field = name.replace("-", "_") + "_workflow"
            args.extend(["--" + name + "-workflow", "checkout/" + self.controls[field]])
        if not self.call("readiness", self.github, *args):
            return
        digest = self.capture_job(reviews)
        if not self.call("verify-admission", self.admission, "verify", "admission.json"):
            return
        if not self.stage("pre-deploy", ["review-0.json", "review-1.json"]):
            return
        if failure == "wrong-candidate":
            digest = "b" * 64
        elif failure == "deleted-evidence":
            (self.root / "test-report.json").unlink()
        elif failure == "missing-approval":
            self.write("approvals.json", [])
        elif failure == "self-approval":
            approvals = json.loads((self.root / "approvals.json").read_bytes())
            approvals[0]["user"].update(login=self.controls["agent"]["login"], id=7)
            self.write("approvals.json", approvals)
        elif failure == "rerun":
            context = json.loads((self.root / "context.json").read_bytes())
            context["GITHUB_RUN_ATTEMPT"] = "2"
            self.write("context.json", context)
            attempt = json.loads((self.root / "attempt.json").read_bytes())
            attempt["run_attempt"] = 2
            self.write("attempt.json", attempt)
        elif failure == "protection-changed":
            environment = json.loads((self.root / "environment.json").read_bytes())
            environment["protection_rules"] = []
            self.write("environment.json", environment)
        if not self.call(
            "bind", self.github, "bind", "--admission", "admission.json", "--controls", "controls.json",
            "--context", "context.json", "--attempt", "attempt.json", "--approvals", "approvals.json",
            "--environment-settings", "environment.json", "--prepare-run", "prepare-run.json",
            "--prepare-artifacts", "prepare-artifacts.json", "--artifact-archive", "artifact.zip",
            "--expect-admission-sha256", digest, "--output", "binding.json",
            "--decision-output", "decision.json",
        ):
            return
        versions = []
        if failure == "execution-limit":
            for run in (38, 39, 40):
                versions.extend([
                    {"Key": f"decisions/sandbox/{run}-1.json", "VersionId": f"example-{run}",
                     "LastModified": NOW, "IsLatest": True},
                    {"Key": f"ops/sandbox/{run}-1.json", "VersionId": f"example-ops-{run}",
                     "LastModified": NOW, "IsLatest": True, "record": {
                         "run_id": run, "run_attempt": 1, "outcome": "no-mutation", "operations": []}},
                ])
        self.write("listing.json", [
            {"Prefix": prefix, "IsTruncated": False,
             "Versions": [item for item in versions if item["Key"].startswith(prefix)]}
            for prefix in ("decisions/sandbox/", "ops/sandbox/")])
        if not self.call("budget", self.github, "budget", "--controls", "controls.json",
                         "--listing", "listing.json"):
            return
        self.capture_audit()
        if failure == "missing-audit":
            self.write("receipt.json", {"Key": "decisions/sandbox/42-1.json",
                                       "VersionId": "example-version", "ChecksumSHA256": "", "ETag": ""})
        elif failure == "payload":
            # The admission remains byte-identical; only the file submitted for mutation changes.
            (self.root / "substituted.json").write_bytes(b"substituted payload")
        if not self.call(
            "recheck", self.github, "recheck", "--controls", "controls.json", "--binding", "binding.json",
            "--decision", "decision.json", "--admission", "admission.json", "--audit-receipt", "receipt.json",
            "--audit-head", "audit-head.json", "--audit-listing", "listing.json", "--live-snapshot", "live.json",
            "--workflows-root", "checkout", "--cloud-identity", "identity.json", "--payload",
            "example-payload=" + ("substituted.json" if failure == "payload" else "image-manifest.json"),
            "--expect-role-arn-env", "RELEASE_ROLE_ARN", "--expect-account-env", "RELEASE_CLOUD_ACCOUNT",
        ):
            return
        binding = json.loads((self.root / "binding.json").read_bytes())
        self.write("observed.json", [{
            "id": "example-payload", "state": "present", "marker": binding["marker"],
            "digest": preparation.helpers.digest((self.root / "image-manifest.json").read_bytes()),
            "write_time": NOW, "operation_id": "example-etag",
        }])
        self.write("run.json", {"id": 42, "run_attempt": 1,
                                "status": "in_progress" if failure == "run-active" else "completed"})
        self.write("jobs.json", {"jobs": [{"name": "deploy", "status": "completed", "conclusion": "success",
                                          "steps": [{"name": "mutate-object", "status": "completed",
                                                     "conclusion": "success", "number": 1}]}]})
        if failure == "unknown-effect":
            observed = json.loads((self.root / "observed.json").read_bytes())
            observed[0]["marker"] = "admission:" + "c" * 64
            self.write("observed.json", observed)
        if not self.call(
            "reconcile", self.github, "reconcile", "--binding", "binding.json", "--controls", "controls.json",
            "--run", "run.json", "--jobs", "jobs.json", "--observed", "observed.json",
            "--audit-listing", "listing.json",
        ):
            return
        self.write("ops.json", {"run_id": 42, "run_attempt": 1, "outcome": "torn-down", "operations": [{
            "effect_id": "example-payload", "request_id": "example-request", "version_id": "unversioned",
        }]})
        (self.root / "torn-down").touch()
        if failure == "missing-readback":
            (self.root / "readback.json").unlink()
        if not self.call(
            "summary", self.github, "summary", "--controls", "controls.json", "--binding", "binding.json",
            "--decision", "decision.json", "--audit-receipt", "receipt.json", "--audit-readback", "readback.json",
            "--audit-head", "readback-head.json", "--observed", "observed.json", "--ops", "ops.json",
        ):
            return
        result = self.trace[-1][2]
        assert result["status"] == "audited" and result["cleanup_state"] == "torn-down"
        self.write("summary.json", result)
        self.write("runtime.json", {"health": "pass", "cleanup": result["cleanup_state"]})
        reviews.extend(self.check_reviews("post-deploy"))
        if not self.stage("post-deploy", reviews):
            return
        reviews.extend(self.check_reviews("final"))
        self.write("final.json", {"budgets": "within execution and byte limits",
                                  "cleanup": result["cleanup_state"], "remaining_risks": []})
        args = ["check-stage", "--stage", "final", "--admission", "admission.json", "--final", "final.json"]
        for name in reviews:
            args.extend(["--review", name])
        self.call("final", self.admission, *args)


@pytest.fixture
def journey(tmp_path: Path, capsys: Any, monkeypatch: pytest.MonkeyPatch) -> GithubJourney:
    """Copy only pack-owned runtime skills; synthesize all service responses offline."""
    preparation.helpers.prohibit_execution(monkeypatch)
    # An empty search directory keeps both Terraform engines unavailable for every journey.
    binary_path = tmp_path / "empty-bin"
    binary_path.mkdir()
    monkeypatch.setenv("PATH", str(binary_path))
    assert shutil.which("terraform") is None
    assert shutil.which("tofu") is None
    for skill in ("release-loop", "prepare-release-handoff"):
        shutil.copytree(PACK / ".apm/skills" / skill, tmp_path / "skills" / skill,
                        ignore=shutil.ignore_patterns("__pycache__"))
    github = load(tmp_path / "skills/release-loop/scripts/github_release.py",
                  "release_engineering_release_loop_github_journey_runtime")
    admission = load(tmp_path / "skills/release-loop/scripts/release_admission.py",
                     "release_engineering_release_loop_github_journey_admission")
    collector = load(tmp_path / "skills/prepare-release-handoff/scripts/collect_evidence.py",
                     "release_engineering_prepare_release_handoff_github_journey_collector")
    monkeypatch.setattr(github.admission, "clock_time", lambda now: NOW)
    assets = tmp_path / "skills/release-loop/assets"
    for path in (assets / "image-only-ci-caller").iterdir():
        if path.is_file():
            shutil.copyfile(path, tmp_path / path.name)
    request = admission.handoff.parse_yaml((tmp_path / "release-handoff.yaml").read_bytes())
    (tmp_path / "release-handoff.yaml").unlink()
    request["target"] = {"environment": "sandbox", "account": "example-sandbox"}
    for evidence in request["evidence"]:
        evidence.pop("sha256")
    for item in request["evidence"] + request["checks"]:
        for subject in item["subjects"]:
            subject.pop("sha256")
    assert [item["kind"] for item in request["components"]] == ["oci-image"]
    instance = GithubJourney(tmp_path, collector, admission.handoff, admission, request, capsys)
    instance.github = github
    instance.controls = json.loads((assets / "github-actions/controls.example.json").read_text().replace(
        "__TARGET_BUCKET__", "example-release-target").replace(
        "__AUDIT_BUCKET__", "example-release-audit").replace("__ROLE_NAME__", "example-deploy"))
    _, snapshot, _ = settings.valid_case()
    raw = json.dumps(snapshot)
    for old, new in [("example-target/payload", "example-release-target/releases/current.json"),
                     ("example-target", "example-release-target"), ("example-audit", "example-release-audit"),
                     ("deploy-job.yml", "release-deploy-job.yml")]:
        raw = raw.replace(old, new)
    instance.snapshot = json.loads(raw)
    # The shipped job requires an unversioned target and deletes its only object.
    instance.snapshot["target_lifecycle"]["example-release-target"]["versioning"] = {}
    instance.write("controls.json", instance.controls)
    instance.write("live.json", instance.snapshot)
    for name in ("prepare", "deploy", "deploy-job"):
        destination = tmp_path / "checkout" / instance.controls[name.replace("-", "_") + "_workflow"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(assets / "github-actions" / f"release-{name}.example.yml", destination)
    instance.write("identity.json", {"Account": "123456789012", "UserId": "example-user:example-session",
                                     "Arn": "arn:aws:sts::123456789012:assumed-role/example-deploy/example-session"})
    monkeypatch.setenv("RELEASE_CLOUD_ACCOUNT", "123456789012")
    monkeypatch.setenv("RELEASE_ROLE_ARN", settings.ROLE)
    for role in preparation.AREAS:
        (tmp_path / f"{role}.txt").write_text(f"Synthetic {role} review evidence.\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    instance.isolated()
    return instance


STEPS = [
    "collect", "admit", "pre-deploy-reliability", "pre-deploy-security", "admission", "pre-deploy", "readiness",
    "verify-admission", "pre-deploy", "bind", "budget", "recheck", "reconcile", "summary",
    "post-deploy-reliability", "post-deploy-security", "post-deploy", "final-reliability", "final-security", "final",
]


def test_application_release_reaches_final(journey: GithubJourney) -> None:
    """The complete application journey ends torn down and awaiting a human decision."""
    journey.run()
    assert shutil.which("terraform") is None
    assert shutil.which("tofu") is None
    assert [name for name, _, _ in journey.trace] == STEPS
    assert all(code == 0 for _, code, _ in journey.trace)
    reports = {name: result for name, _, result in journey.trace}
    assert reports["readiness"]["status"] == "ready"
    assert reports["recheck"]["status"] == "current"
    assert reports["reconcile"]["status"] == "proceed-to-observe"
    assert reports["summary"]["cleanup_state"] == "torn-down"
    assert reports["final"]["progression"] == "human-decision-required"
    assert reports["final"]["authority_checks_required"] is True
    journey.isolated()


@pytest.mark.parametrize("failure,step,status,code", [
    ("wrong-candidate", "bind", "refused", "admission-digest-mismatch"),
    ("payload", "recheck", "refused", "payload-mismatch"),
    ("missing-protection", "readiness", "blocked", "reviewers-missing"),
    ("protection-changed", "bind", "refused", "protection-changed"),
    ("missing-audit-settings", "readiness", "blocked", None),
    ("missing-audit", "recheck", "refused", "binding-unaudited"),
    ("missing-readback", "summary", "audit-unconfirmed", "audit-unconfirmed"),
    ("missing-approval", "bind", "refused", "approval-missing"),
    ("self-approval", "bind", "refused", "approval-self"),
    ("rerun", "bind", "refused", "rerun-refused"),
    ("deleted-evidence", "bind", "refused", "admission-stale"),
    ("execution-limit", "budget", "refused", "execution-limit"),
    ("run-active", "reconcile", "pause", "run-not-terminal"),
    ("unknown-effect", "reconcile", "pause", "effect-unknown"),
])
def test_failure_stops_journey(journey: GithubJourney, failure: str, step: str,
                              status: str, code: str | None) -> None:
    """Each refusal or pause prevents all later commands and synthetic effect creation."""
    journey.run(failure)
    assert [name for name, _, _ in journey.trace] == STEPS[:STEPS.index(step) + 1]
    assert all(exit_code == 0 for _, exit_code, _ in journey.trace[:-1])
    _, exit_code, report = journey.trace[-1]
    assert exit_code == (0 if status == "pause" else 1)
    assert report["status"] == status
    if status == "blocked":
        assert report["blocked_mutations"] == ["deploy", "teardown"]
        if code:
            assert code in [value for row in report["controls"] for value in row["codes"]]
    elif code:
        assert code in [issue["code"] for issue in report["issues"]]
    if STEPS.index(step) <= STEPS.index("bind"):
        assert not (journey.root / "binding.json").exists()
        assert not (journey.root / "decision.json").exists()
    if STEPS.index(step) <= STEPS.index("budget"):
        assert not (journey.root / "receipt.json").exists()
    if STEPS.index(step) <= STEPS.index("recheck"):
        assert not (journey.root / "observed.json").exists()
    if STEPS.index(step) <= STEPS.index("reconcile"):
        assert not (journey.root / "torn-down").exists()
    assert not (journey.root / "final.json").exists()
    journey.isolated()
