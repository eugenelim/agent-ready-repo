"""Exercise installed release skills together without core or external execution."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[2]
FIXTURES = HERE / "fixtures/journey"
SKILLS = "skills"
AREAS = {
    "reliability": [
        "ordering", "partial-failure", "mixed-versions", "runtime-health", "rollback", "cost", "cleanup"
    ],
    "security": ["provenance", "identity-permissions", "exposure", "secrets", "trust-boundaries"],
}


def load(path: Path, name: str) -> ModuleType:
    """Load a pack-and-skill-qualified module without changing sys.path."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


helpers = load(
    HERE / "test_release_admission.py", "release_engineering_release_loop_journey_helpers"
)


@dataclass
class Journey:
    """Hold an isolated installation and the ordered, short-circuiting CLI trace."""

    root: Path
    collector: ModuleType
    validator: ModuleType
    admission: ModuleType
    request: dict[str, Any]
    capsys: Any
    trace: list[tuple[str, int, dict[str, Any]]] = field(default_factory=list)

    def call(self, name: str, module: ModuleType, *args: str) -> bool:
        """Call a real entry point and report whether the next step may run."""
        code, result = helpers.invoke(module, self.root, self.capsys, *args)
        self.trace.append((name, code, result))
        return code == 0

    def isolated(self) -> None:
        """Require that no core pack, Claude adapter or work-loop file is present."""
        assert not (self.root / "packs/core").exists()
        assert not (self.root / ".claude").exists()
        assert not any(
            path.name in {"core", ".claude", "work-loop"} or "work-loop" in path.name
            for path in self.root.rglob("*")
        )
        for module in (self.collector, self.validator, self.admission, self.admission.handoff):
            assert Path(module.__file__).resolve().is_relative_to(self.root)

    def reviews(self, stage: str) -> list[str]:
        """Bind both local reviews to admission and the real installed checklists."""
        admitted = json.loads((self.root / "admission.json").read_bytes())
        names = []
        for role, areas in AREAS.items():
            rubric = self.root / SKILLS / f"release-loop/references/{role}-review.md"
            path = f"{role}.txt" if stage == "pre-deploy" else "runtime.json"
            evidence = {
                "id": f"{stage}-{role}-proof",
                "kind": "test-report" if stage == "pre-deploy" else "health-check",
                "path": path,
                "sha256": helpers.digest((self.root / path).read_bytes()),
                "observed_at": helpers.NOW if stage == "pre-deploy" else "2026-01-01T12:30:01Z",
            }
            record = {
                "subject": {key: admitted["candidate"][key] for key in ("id", "sha256")},
                "target": admitted["target"],
                "stage": stage,
                "rubric": {"id": role, "role": role, "sha256": helpers.digest(rubric.read_bytes())},
                "reviewer": {"id": f"local-{role}", "kind": "local"},
                "permissions_digest": helpers.digest(b"staging-only; no permission expansion"),
                "evidence": [evidence],
                "areas": [
                    {"area": area, "coverage": "covered", "evidence": [evidence["id"]], "findings": []}
                    for area in areas
                ],
                "result": "pass",
            }
            name = f"{stage}-{role}.json"
            self.write(name, record)
            names.append(name)
        return names

    def write(self, name: str, data: dict[str, Any]) -> None:
        """Write one mutable journey input as UTF-8 JSON."""
        (self.root / name).write_text(json.dumps(data), encoding="utf-8")

    def exemption(self) -> None:
        """Set up a policy-approved exemption before testing its basis binding."""
        policy = json.loads((self.root / "trusted-policy.json").read_bytes())
        policy["required_checks"][0]["allowed_not_applicable_reasons"] = ["synthetic-exemption"]
        self.write("trusted-policy.json", policy)
        self.request["checks"][0].update(
            status="not-applicable", reason="synthetic-exemption",
            policy_basis=policy["id"] + "/tests",
        )

    def stage(self, stage: str, names: list[str]) -> bool:
        """Check stage progression with only the supplied review history."""
        args = ["check-stage", "--stage", stage, "--admission", "admission.json"]
        for name in names:
            args.extend(["--review", name])
        return self.call(stage, self.admission, *args)

    def run(self, failure: str | None = None) -> None:
        """Run through pre-deploy, stopping immediately on any refused command."""
        self.isolated()
        self.write("request.json", self.request)
        if not self.call(
            "collect", self.collector, "collect", "request.json", "--policy", "trusted-policy.json",
            "--output", "candidate.yaml",
        ):
            return
        assert self.trace[-1][2] == {"status": "ready", "gaps": []}
        if not self.call(
            "validate", self.validator, "validate", "candidate.yaml", "--policy", "trusted-policy.json"
        ):
            return
        assert self.trace[-1][2]["status"] == "valid"
        if not self.call(
            "admit", self.admission, "admit", "candidate.yaml", "--policy", "trusted-policy.json",
            "--expect-environment", "staging", "--expect-account", "example-account",
            "--output", "admission.json",
        ):
            return
        names = self.reviews("pre-deploy")
        if failure == "subject":
            record = json.loads((self.root / names[0]).read_bytes())
            record["subject"]["sha256"] = "sha256:" + "0" * 64
            self.write(names[0], record)
        elif failure in ("absent-admission", "unreadable-admission"):
            (self.root / "admission.json").unlink()
            if failure == "unreadable-admission":
                # A directory is unreadable as a record even under privileged test users.
                (self.root / "admission.json").mkdir()
        elif failure == "missing-role":
            (self.root / names.pop()).unlink()
        for name in names:
            role = name.removeprefix("pre-deploy-").removesuffix(".json")
            if not self.call(
                role, self.admission, "check-review", name, "--admission", "admission.json",
                "--rubric", f"{SKILLS}/release-loop/references/{role}-review.md",
            ):
                return
            assert self.trace[-1][2]["status"] == "pass"
        if not self.stage("admission", []):
            return
        assert self.trace[-1][2]["progression"] == "preparation"
        assert self.trace[-1][2]["authority_checks_required"] is True
        if not self.stage("pre-deploy", names):
            return
        assert self.trace[-1][2]["progression"] == "execution-eligible"
        assert self.trace[-1][2]["authority_checks_required"] is True
        self.isolated()


@pytest.fixture(params=["application-only", "infrastructure-only"])
def journey(
    request: pytest.FixtureRequest, tmp_path: Path, capsys: Any, monkeypatch: pytest.MonkeyPatch
) -> Journey:
    """Install only two pack-owned skill folders and synthetic local evidence."""
    helpers.prohibit_execution(monkeypatch)
    for skill in ("release-loop", "prepare-release-handoff"):
        shutil.copytree(
            PACK / ".apm/skills" / skill, tmp_path / SKILLS / skill,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
    validator = load(
        tmp_path / SKILLS / "release-loop/scripts/release_handoff.py",
        "release_engineering_release_loop_journey_validator",
    )
    if request.param == "application-only":
        for path in helpers.EXAMPLE.iterdir():
            if path.is_file():
                shutil.copyfile(path, tmp_path / path.name)
        data = validator.parse_yaml((tmp_path / "release-handoff.yaml").read_bytes())
        for evidence in data["evidence"]:
            evidence.pop("sha256")
        for item in data["evidence"] + data["checks"]:
            for subject in item["subjects"]:
                subject.pop("sha256")
        expected = "oci-image"
    else:
        for path in (FIXTURES / "infrastructure-only").iterdir():
            shutil.copyfile(path, tmp_path / path.name)
        data = json.loads((tmp_path / "request.json").read_bytes())
        expected = "terraform-plan"
    assert [component["kind"] for component in data["components"]] == [expected]
    for name in ("reliability.txt", "security.txt", "runtime.json"):
        shutil.copyfile(FIXTURES / name, tmp_path / name)
    collector = load(
        tmp_path / SKILLS / "prepare-release-handoff/scripts/collect_evidence.py",
        "release_engineering_prepare_release_handoff_journey_collector",
    )
    admission = load(
        tmp_path / SKILLS / "release-loop/scripts/release_admission.py",
        "release_engineering_release_loop_journey_admission",
    )
    assert tmp_path / SKILLS / "release-loop/scripts/release_handoff.py" == collector.VALIDATOR
    return Journey(tmp_path, collector, validator, admission, data, capsys)


@pytest.mark.parametrize("exemption", [False, True])
def test_core_absent_journey(journey: Journey, exemption: bool) -> None:
    """An image alone or plan bundle alone reaches pre-deploy without core."""
    if exemption:
        journey.exemption()
    journey.run()
    assert [name for name, _, _ in journey.trace] == [
        "collect", "validate", "admit", "reliability", "security", "admission", "pre-deploy"
    ]
    assert all(code == 0 for _, code, _ in journey.trace)
    candidate = journey.validator.parse_yaml((journey.root / "candidate.yaml").read_bytes())
    for evidence in candidate["evidence"]:
        assert evidence["sha256"] == helpers.digest((journey.root / evidence["locator"]).read_bytes())
    if candidate["components"][0]["kind"] == "terraform-plan":
        component = candidate["components"][0]
        assert "image_ref" not in component
        bundle = next(item for item in candidate["evidence"] if item["id"] == component["plan_bundle"])
        assert bundle["locator"] == "plan-bundle.json"


@pytest.mark.parametrize(
    "failure,expected,steps",
    [
        ("stale", "stale", ["collect"]),
        ("provenance", "missing-provenance", ["collect"]),
        ("applicability", "invalid-applicability", ["collect"]),
        ("subject", "subject-mismatch", ["collect", "validate", "admit", "reliability"]),
        ("missing-role", "missing-reviewer", ["collect", "validate", "admit", "reliability", "admission", "pre-deploy"]),
        ("absent-admission", "admission-stale", ["collect", "validate", "admit", "reliability"]),
        ("unreadable-admission", "admission-stale", ["collect", "validate", "admit", "reliability"]),
    ],
)
def test_journey_stops_at_failure(
    journey: Journey, failure: str, expected: str, steps: list[str]
) -> None:
    """A single bad input stops the chain before any later review or progression."""
    if failure == "stale":
        journey.request["evidence"][0]["observed_at"] = "2025-01-01T00:00:00Z"
    elif failure == "provenance":
        journey.request["provenance"] = []
    elif failure == "applicability":
        journey.exemption()
        journey.request["checks"][0]["policy_basis"] = "untrusted-policy/tests"
    journey.run(failure)
    assert [name for name, _, _ in journey.trace] == steps
    assert all(code == 0 for _, code, _ in journey.trace[:-1])
    _, code, result = journey.trace[-1]
    assert code == 1
    assert expected in [issue["code"] for issue in result.get("gaps", result.get("issues", []))]
    assert "progression" not in result
    if steps == ["collect"]:
        assert not (journey.root / "candidate.yaml").exists()
        assert not (journey.root / "admission.json").exists()
        assert not list(journey.root.glob("pre-deploy-*.json"))
    journey.isolated()


@pytest.mark.parametrize(
    "failure,expected",
    [("skipped", "skipped-stage"), ("circular", "circular-review"), ("reused", "runtime-evidence-missing")],
)
def test_post_deploy_refusals(journey: Journey, failure: str, expected: str) -> None:
    """Complete preparation cannot authorize a skipped, circular or reused review."""
    journey.run()
    assert all(code == 0 for _, code, _ in journey.trace)
    pre = [f"pre-deploy-{role}.json" for role in AREAS]
    post = journey.reviews("post-deploy")
    record = json.loads((journey.root / post[0]).read_bytes())
    if failure == "skipped":
        pre = []
    elif failure == "circular":
        record["evidence"][0].update(
            path=post[1], sha256=helpers.digest((journey.root / post[1]).read_bytes())
        )
        journey.write(post[0], record)
    else:
        earlier = json.loads((journey.root / pre[0]).read_bytes())
        evidence = copy.deepcopy(earlier["evidence"][0])
        evidence.update(kind="health-check", observed_at="2026-01-01T12:30:01Z")
        record["evidence"] = [evidence]
        for area in record["areas"]:
            area["evidence"] = [evidence["id"]]
        journey.write(post[0], record)
    before = len(journey.trace)
    for stage in ("post-deploy", "final"):
        if not journey.stage(stage, pre + post):
            break
    assert len(journey.trace) == before + 1
    name, code, result = journey.trace[-1]
    assert name == "post-deploy" and code == 1
    helpers.assert_code(result, expected)
    assert "progression" not in result
    journey.isolated()
