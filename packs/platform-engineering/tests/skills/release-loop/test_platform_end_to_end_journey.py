"""Join installed plan authoring, release execution and recovery without core."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[2]
spec = importlib.util.spec_from_file_location(
    "platform_engineering_release_loop_end_to_end_helpers", HERE / "test_github_release_journeys.py"
)
assert spec and spec.loader
helpers = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = helpers
spec.loader.exec_module(helpers)
# Reuse the installed-copy fixture, including its no-process and no-network sentinels.
journey = helpers.journey
load = helpers.load
digest = helpers.preparation.helpers.digest


class PlatformJourney(helpers.GithubJourney):
    """Extend the image journey with a plan skill and its archived evidence."""

    def isolated(self) -> None:
        """Require exactly the three platform skills, with all code inside this root."""
        helpers.preparation.Journey.isolated(self)
        assert {path.name for path in (self.root / "skills").iterdir()} == {
            "generate-iac", "prepare-release-handoff", "release-loop",
        }
        for path in self.root.rglob("*"):
            assert not path.is_symlink()
            assert path.resolve().is_relative_to(self.root.resolve())
        for module in (self.github, self.github.admission, self.github.handoff):
            assert Path(module.__file__).resolve().is_relative_to(self.root)

    def capture_job(self, reviews: list[str]) -> str:
        """Include the plan and its local evidence in the synthetic prepare archive."""
        admission_digest: str = super().capture_job(reviews)
        with zipfile.ZipFile(self.root / "artifact.zip", "a") as archive:
            for path in sorted((self.root / "iac").iterdir()):
                if path.is_file():
                    archive.write(path, path.relative_to(self.root).as_posix())
        artifacts = json.loads((self.root / "prepare-artifacts.json").read_bytes())
        artifacts["artifacts"][0]["digest"] = digest((self.root / "artifact.zip").read_bytes())
        self.write("prepare-artifacts.json", artifacts)
        return admission_digest


def build_plan(journey: PlatformJourney) -> None:
    """Build a reviewed bundle from synthetic saved-plan bytes and a recorded schema."""
    root = journey.root
    skill = root / "skills/generate-iac"
    shutil.copytree(
        PACK / ".apm/skills/generate-iac", skill,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(skill / "assets/native-adr-caller", root / "iac")
    gate = load(skill / "scripts/authoring_gate.py", "platform_engineering_generate_iac_journey_gate")
    bundle_tool = load(skill / "scripts/plan_bundle.py", "platform_engineering_generate_iac_journey_bundle")
    for module in (gate, bundle_tool):
        assert Path(module.__file__).resolve().is_relative_to(root)
    shutil.copyfile(HERE / "fixtures/journey/providers-schema.json", root / "iac/schema.json")
    schema = json.loads((root / "iac/schema.json").read_bytes())
    provider = "terraform.io/builtin/terraform"
    assert "terraform_data" in schema["provider_schemas"][provider]["resource_schemas"]
    journey.write("iac/main.tf.json", {
        "resource": {"terraform_data": {"example": {"input": "local-only"}}},
    })
    bundle = json.loads((root / "iac/iac-plan-bundle.v1.json").read_bytes())
    inspection = json.loads((root / "iac/inspection.json").read_bytes())
    inspection["resource_changes"] = [{
        "address": "terraform_data.example", "mode": "managed", "type": "terraform_data",
        "name": "example", "provider_name": provider,
        "change": {"actions": ["create"], "before": None, "after": {"input": "local-only"}},
    }]
    journey.write("iac/inspection.json", inspection)
    journey.write("iac/summary.json", {
        "sources": [{"id": "native-decision", "path": "iac/decision.md",
                     "sha256": digest((root / "iac/decision.md").read_bytes()),
                     "authority": "accepted", "status_line": "* Status: accepted"}],
        "constraints": [{"id": "local-backend", "topic": "backend", "requirement": "local",
                         "source": "native-decision"}],
        "unresolved": [], "integrations": [],
    })
    code = gate.main(["check-summary", "iac/summary.json", "--root", str(root)])
    captured = journey.capsys.readouterr()
    assert captured.err == ""
    report = json.loads(captured.out)
    assert (code, report) == (0, {"status": "ready", "issues": []})
    rubric = "skills/generate-iac/references/infrastructure-review.md"
    areas = {
        "decisions": "summary.json", "schema": "schema.json", "plan-effects": "inspection.json",
        "privilege": "security.txt", "policy": "policy.txt", "state-impact": "inspection.json",
        "reversibility": "security.txt",
    }
    journey.write("iac/review.json", {
        "subject": {"id": "saved-plan", "sha256": digest((root / "iac/saved-plan.synthetic").read_bytes())},
        "rubric": {"id": "infrastructure", "sha256": digest((root / rubric).read_bytes())},
        "reviewers": [{"id": "local-infrastructure-review", "kind": "local"}],
        "evidence": [{"id": area, "path": "iac/" + path,
                      "sha256": digest((root / "iac" / path).read_bytes())}
                     for area, path in areas.items()],
        "areas": [{"area": area, "coverage": "covered", "evidence": [area], "findings": []}
                  for area in areas],
        "result": "pass",
    })
    code = gate.main([
        "check-review", "iac/review.json", "--root", str(root),
        "--saved-plan", "iac/saved-plan.synthetic", "--checklist", rubric,
    ])
    captured = journey.capsys.readouterr()
    assert captured.err == ""
    report = json.loads(captured.out)
    assert (code, report) == (0, {"status": "pass", "issues": []})
    journey.write("iac/review-result.json", report)
    for evidence in bundle["evidence"]:
        if evidence["id"] == "review-proof":
            evidence.update(locator="review-result.json", media_type="application/json")
        evidence["locator"] = "iac/" + evidence["locator"]
        evidence["sha256"] = digest((root / evidence["locator"]).read_bytes())
    bundle["toolchain"]["providers"] = [{"source": provider, "version": inspection["terraform_version"]}]
    bundle["effects"]["changes"] = [{"address": "terraform_data.example", "actions": ["create"]}]
    bundle["target"] = copy.deepcopy(journey.request["target"])
    journey.write("iac/bundle.json", bundle)
    code, report = helpers.preparation.helpers.invoke(
        bundle_tool, root, journey.capsys, "validate", "iac/bundle.json",
        "--policy", "iac/trusted-policy.json",
    )
    assert code == 0 and report["status"] == "valid", report
    assert report["issues"] == []
    assert all(item["verification"] == "verified" for item in report["evidence"])


def add_plan_component(journey: PlatformJourney) -> None:
    """Bind the produced bundle beside the image, with checks covering both subjects."""
    request = journey.request
    subject = {"id": "infrastructure"}
    request["components"].append({
        "id": subject["id"], "kind": "terraform-plan", "plan_bundle": "plan-bundle",
    })
    for evidence in request["evidence"]:
        if evidence["id"] != "image-artifact":
            evidence["subjects"].append(copy.deepcopy(subject))
    request["evidence"].append({
        "id": "plan-bundle", "kind": "terraform-plan-bundle", "locator": "iac/bundle.json",
        "media_type": "application/json", "producer": "generate-iac-offline-journey",
        "observed_at": request["created_at"], "subjects": [subject],
    })
    plan_checks = copy.deepcopy(request["checks"])
    for check in plan_checks:
        check["id"] = "plan-" + check["id"]
        check["subjects"] = [copy.deepcopy(subject)]
    request["checks"].extend(plan_checks)
    request["phases"][0]["components"].append(subject["id"])
    policy = json.loads((journey.root / "trusted-policy.json").read_bytes())
    plan_checks = copy.deepcopy(policy["required_checks"])
    for check in plan_checks:
        check["component_kind"] = "terraform-plan"
        check["id"] = "plan-" + check["id"]
    policy["required_checks"].extend(plan_checks)
    journey.write("trusted-policy.json", policy)


def test_plan_to_release_and_recovery(journey: Any) -> None:
    """One candidate reaches torn-down final, routes repair and pauses an interrupted retry."""
    platform = PlatformJourney(
        journey.root, journey.collector, journey.validator, journey.admission,
        journey.request, journey.capsys,
    )
    platform.github = journey.github
    platform.controls = journey.controls
    platform.snapshot = journey.snapshot
    build_plan(platform)
    add_plan_component(platform)
    platform.run()
    assert [name for name, _, _ in platform.trace] == helpers.STEPS, platform.trace
    assert all(code == 0 for _, code, _ in platform.trace)
    reports = {name: report for name, _, report in platform.trace}
    assert reports["readiness"]["status"] == "ready"
    assert reports["recheck"]["status"] == "current"
    assert reports["reconcile"]["status"] == "proceed-to-observe"
    assert reports["summary"]["cleanup_state"] == "torn-down"
    assert reports["final"]["progression"] == "human-decision-required"
    admitted = json.loads((platform.root / "admission.json").read_bytes())
    candidate = platform.validator.parse_yaml((platform.root / "release-handoff.yaml").read_bytes())
    assert {item["kind"] for item in candidate["components"]} == {"oci-image", "terraform-plan"}
    plan_digest = digest((platform.root / "iac/bundle.json").read_bytes())
    assert next(item for item in candidate["evidence"] if item["id"] == "plan-bundle")["sha256"] == plan_digest
    assert plan_digest in json.dumps(admitted)
    with zipfile.ZipFile(platform.root / "artifact.zip") as archive:
        assert digest(archive.read("iac/bundle.json")) == plan_digest

    # A new failed runtime observation binds to the same admitted candidate.
    (platform.root / "failure.log").write_text("health check failed\n", encoding="utf-8")
    platform.write("failure.json", {
        "candidate_sha256": admitted["candidate"]["sha256"], "target": admitted["target"],
        "stage": "post-deploy", "check": {"id": "health", "status": "fail"},
        "observed_at": helpers.NOW,
        "evidence": [{"id": "runtime-failure", "path": "failure.log",
                      "sha256": digest((platform.root / "failure.log").read_bytes())}],
    })
    assert platform.call("repair-handoff", platform.admission, "repair-handoff",
                         "--admission", "admission.json", "--failure", "failure.json")
    repaired = platform.trace[-1][2]
    assert repaired["status"] == "human-handoff"
    assert repaired["repair_owner"] == candidate["repair_owner"]["id"]
    assert repaired["excerpts"][0]["text"] == "health check failed\n"

    # Reconstruct an interrupted attempt: mutation started, effect absent, no terminal ops.
    (platform.root / "ops.json").unlink()
    platform.write("run.json", {"id": 42, "run_attempt": 1, "status": "completed"})
    platform.write("jobs.json", {"jobs": [{"name": "deploy", "status": "completed",
        "conclusion": "cancelled", "steps": [{"name": "mutate-object", "number": 1,
                                                  "status": "completed", "conclusion": "cancelled"}]}]})
    platform.write("observed.json", [{"id": "example-payload", "state": "absent"}])
    assert not platform.call(
        "interrupted-reconcile", platform.github, "reconcile", "--binding", "binding.json",
        "--controls", "controls.json", "--run", "run.json", "--jobs", "jobs.json",
        "--observed", "observed.json", "--audit-listing", "listing.json",
    )
    _, code, paused = platform.trace[-1]
    assert code == 0 and paused["status"] == "pause"
    assert {issue["code"] for issue in paused["issues"]} == {"ops-missing"}
    assert "retry-allowed" not in json.dumps(paused)
    assert not (platform.root / "ops.json").exists()
    platform.isolated()
