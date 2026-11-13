"""Exercise the standalone authoring journey with Terraform's built-in provider."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

SKILL = Path(__file__).resolve().parents[3] / ".apm/skills/generate-iac"
EXAMPLE = SKILL / "assets/native-adr-caller"
TERRAFORM = shutil.which("terraform")
pytestmark = pytest.mark.skipif(
    TERRAFORM is None, reason="Terraform binary required for the real built-in-provider journey"
)
NOW = "2026-01-01T12:30:00Z"
AREAS = ("decisions", "schema", "plan-effects", "privilege", "policy", "state-impact", "reversibility")
OPTIONAL = ("none", "integration", "reviewer", "both")


@pytest.fixture(scope="module")
def scripts() -> dict[str, Any]:
    """Load both shipped scripts without exposing their directory on sys.path."""
    modules = {}
    for name in ("authoring_gate", "plan_bundle"):
        spec = importlib.util.spec_from_file_location(
            f"iac_terraform_generate_iac_{name}_journey", SKILL / f"scripts/{name}.py"
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        modules[name] = module
    return modules


def digest(path: Path) -> str:
    """Identify the exact local artifact bytes."""
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(root: Path, name: str, value: Any) -> None:
    """Serialize one local input or observed result."""
    (root / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def invoke(module: Any, capsys: Any, root: Path, *args: str) -> tuple[int, dict[str, Any]]:
    """Drive the shipped argument boundary and require one quiet JSON result."""
    code = module.main([*args, "--root", str(root)])
    captured = capsys.readouterr()
    assert captured.err == ""
    return code, json.loads(captured.out)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Make an empty Git repository with native MADR decisions and no installed packs."""
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "--quiet", str(root)], check=True, capture_output=True)
    (root / "docs/adr").mkdir(parents=True)
    (root / "AGENTS.md").write_text("Use local state and built-in resources only.\n", encoding="utf-8")
    for name, requirement in (("local", "local"), ("second", "local")):
        (root / f"docs/adr/{name}.md").write_text(
            f"# Backend decision\n\n* Status: accepted\n\n"
            f"## Context and Problem Statement\n\nPlan without cloud access.\n\n"
            f"## Decision Outcome\n\nUse {requirement} state.\n",
            encoding="utf-8",
        )
    assert not any((root / name).exists() for name in (".apm", ".agents", ".claude"))
    return root


def summary(root: Path, optional: str) -> dict[str, Any]:
    """Bind accepted native decisions and effective instructions without an index."""
    paths = ("AGENTS.md", "docs/adr/local.md", "docs/adr/second.md")
    sources = []
    for index, name in enumerate(paths):
        source = {
            "id": f"source-{index}", "path": name, "sha256": digest(root / name),
            "authority": "instruction" if index == 0 else "accepted",
        }
        if index:
            source["status_line"] = "* Status: accepted"
        sources.append(source)
    return {
        "sources": sources,
        "constraints": [
            {"id": f"backend-{i}", "topic": "backend", "requirement": "local", "source": f"source-{i}"}
            for i in (1, 2)
        ],
        "unresolved": [],
        "integrations": [{"name": "core", "status": "used"}]
        if optional in ("integration", "both") else [],
    }


def engine(root: Path, resource: str) -> dict[str, Any]:
    """Initialize offline, ground resource types and run the documented gated chain."""
    assert TERRAFORM is not None
    (root / "main.tf").write_text(
        f'resource "{resource}" "example" {{\n  input = "local-only"\n}}\n', encoding="utf-8"
    )
    config = root.parent / "empty.tfrc"
    config.write_text("", encoding="utf-8")
    env = {
        **os.environ, "TF_IN_AUTOMATION": "1", "CHECKPOINT_DISABLE": "1",
        "TF_DATA_DIR": str(root.parent / "terraform-data"), "TF_CLI_CONFIG_FILE": str(config),
    }
    # Disallow ambient CLI arguments from changing the isolated command contract.
    env = {key: value for key, value in env.items() if not key.startswith("TF_CLI_ARGS")}

    def run(*args: str) -> subprocess.CompletedProcess[str]:
        """Run the real engine with bounded execution and no provider downloads."""
        return subprocess.run(
            [TERRAFORM, *args], cwd=root, env=env, capture_output=True,
            text=True, encoding="utf-8", timeout=60, check=False,
        )

    initialized = run("init", "-backend=false")
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    schema = run("providers", "schema", "-json")
    assert schema.returncode == 0, schema.stderr
    (root / "schema.json").write_text(schema.stdout, encoding="utf-8")
    providers = json.loads(schema.stdout)["provider_schemas"]
    available = {kind for provider in providers.values() for kind in provider["resource_schemas"]}
    used = set(re.findall(r'resource\s+"([^"]+)"', (root / "main.tf").read_text(encoding="utf-8")))
    if resource == "terraform_data":
        assert used and used <= available
    else:
        assert used - available == {resource}
    binary = shlex.quote(TERRAFORM)
    # One shell chain: neither plan nor its output file is created after validate fails.
    chain = (
        f"{binary} fmt -check >fmt.txt 2>&1 && "
        f"{binary} validate >validation.txt 2>&1 && "
        f"{binary} plan -out=tfplan >plan.txt 2>&1"
    )
    completed = subprocess.run(
        ["/bin/sh", "-c", chain], cwd=root, env=env, capture_output=True,
        text=True, encoding="utf-8", timeout=60, check=False,
    )
    assert (root / "fmt.txt").read_text(encoding="utf-8") == ""
    if resource != "terraform_data":
        assert completed.returncode != 0
        assert "Invalid resource type" in (root / "validation.txt").read_text(encoding="utf-8")
        assert not (root / "tfplan").exists() and not (root / "plan.txt").exists()
        return {"status": "validate-failed"}
    assert completed.returncode == 0, (root / "validation.txt").read_text() + (root / "plan.txt").read_text()
    assert "Success!" in (root / "validation.txt").read_text(encoding="utf-8")
    shown = run("show", "-json", "tfplan")
    assert shown.returncode == 0, shown.stderr
    (root / "inspection.json").write_text(shown.stdout, encoding="utf-8")
    inspection = json.loads(shown.stdout)
    changes = inspection["resource_changes"]
    assert [(item["type"], item["change"]["actions"]) for item in changes] == [("terraform_data", ["create"])]
    assert all(item["provider_name"] == "terraform.io/builtin/terraform" for item in changes)
    # Built-in providers produce no lock file; record that fact rather than inventing a pin.
    if not (root / ".terraform.lock.hcl").exists():
        (root / ".terraform.lock.hcl").write_text(
            "# Built-in terraform provider ships with the engine; no external provider lock entries.\n"
            f"# Engine version: {inspection['terraform_version']}\n", encoding="utf-8",
        )
    return inspection


def review(root: Path, optional: str, gap: bool) -> dict[str, Any]:
    """Cover the local-only plan with real evidence and explicit fixture review findings."""
    shutil.copyfile(SKILL / "references/infrastructure-review.md", root / "checklist.md")
    write_json(root, "policy.json", {
        "backend": "local", "summary": "ready", "resources": ["terraform_data.example"],
    })
    write_json(root, "security.json", {
        "provider": "terraform.io/builtin/terraform", "cloud_privileges": [],
        "state": "new local state", "reversal": "discard unapplied plan; no live resources changed",
    })
    evidence = {
        "decisions": "summary.json", "schema": "schema.json", "plan-effects": "inspection.json",
        "privilege": "security.json", "policy": "policy.json", "state-impact": "inspection.json",
        "reversibility": "security.json",
    }
    reviewers = [{"id": "fixture-review", "kind": "local"}]
    if optional in ("reviewer", "both"):
        reviewers.append({"id": "additional-review", "kind": "core-agent"})
    return {
        "subject": {"id": "saved-plan", "sha256": digest(root / "tfplan")},
        "rubric": {"id": "local-checklist", "sha256": digest(root / "checklist.md")},
        "reviewers": reviewers,
        "evidence": [{"id": area, "path": path, "sha256": digest(root / path)} for area, path in evidence.items()],
        "areas": [
            {"area": area, "coverage": "gap" if gap and area == "policy" else "covered",
             "evidence": [area], "findings": []} for area in AREAS
        ],
        "result": "insufficient-evidence" if gap else "pass",
    }


def bundle(root: Path, inspection: dict[str, Any], module: Any) -> None:
    """Reuse the native caller shape, replacing synthetic evidence with observed artifacts."""
    value = module.parse_json(module.read_manifest(EXAMPLE, "iac-plan-bundle.v1.json"))
    paths = {
        "native-decision": "docs/adr/local.md", "saved-plan": "tfplan",
        "plan-inspection": "inspection.json", "dependency-lock": ".terraform.lock.hcl",
        "validation-proof": "validation.txt", "policy-proof": "policy.json",
        "security-proof": "security.json", "review-proof": "review-result.json",
    }
    subject = {"id": "saved-plan", "sha256": digest(root / "tfplan")}
    for item in value["evidence"]:
        item.update(locator=paths[item["id"]], sha256=digest(root / paths[item["id"]]),
                    producer="terraform-only-journey", subjects=[subject])
    value["evidence"].append({
        "id": "input-snapshot", "kind": "source-snapshot", "locator": "main.tf",
        "sha256": digest(root / "main.tf"), "media_type": "text/plain",
        "producer": "terraform-only-journey", "observed_at": value["created_at"], "subjects": [subject],
    })
    value["source"] = {"repository": "temporary-repository", "snapshot": "input-snapshot"}
    value["toolchain"].update(
        version=inspection["terraform_version"],
        providers=[{"source": "terraform.io/builtin/terraform", "version": inspection["terraform_version"]}],
    )
    value["state"] = {"backend": "local", "workspace": "default", "new_workspace": "native-decision"}
    value["target"] = {"environment": "local", "account": "no-cloud-account"}
    value["effects"]["changes"] = [
        {"address": item["address"], "actions": item["change"]["actions"]}
        for item in inspection["resource_changes"]
    ]
    for check in value["checks"]:
        check["subjects"] = [subject]
    write_json(root, "bundle.json", value)
    (root / "trusted-policy.json").write_bytes(module.read_manifest(EXAMPLE, "trusted-policy.json"))


@pytest.mark.parametrize("optional", OPTIONAL)
@pytest.mark.parametrize("scenario", ["ready", "conflict", "unsafe", "invented", "gap"])
def test_terraform_only_journey(
    scripts: dict[str, Any], capsys: Any, repository: Path, optional: str, scenario: str,
) -> None:
    """Optional additions preserve the happy path and every direct-path stop outcome."""
    root = repository
    gate = scripts["authoring_gate"]
    if scenario == "unsafe":
        outside = root.parent / "outside.md"
        outside.write_text("External decision\n", encoding="utf-8")
        (root / "docs/adr/external.md").symlink_to(outside)
    code, discovered = invoke(gate, capsys, root, "discover", "--target", "main.tf")
    if scenario == "unsafe":
        assert code == 1 and discovered["status"] == "stop"
        assert {item["code"] for item in discovered["issues"]} == {"unsafe-path"}
        assert not list(root.rglob("*.tf"))
        assert not (root / "tfplan").exists() and not (root / "bundle.json").exists()
        return
    assert code == 0
    assert {item["path"] for item in discovered["sources"]} == {
        "AGENTS.md", "docs/adr/local.md", "docs/adr/second.md",
    }
    if scenario == "conflict":
        path = root / "docs/adr/second.md"
        path.write_text(path.read_text(encoding="utf-8").replace("Use local state", "Use remote state"), encoding="utf-8")
    governance = summary(root, optional)
    if scenario == "conflict":
        governance["constraints"][1]["requirement"] = "remote"
    write_json(root, "summary.json", governance)
    code, checked = invoke(gate, capsys, root, "check-summary", "summary.json")
    if scenario == "conflict":
        assert (code, checked) == (1, {"status": "stop", "issues": [{"code": "conflict"}]})
        assert not (root / "tfplan").exists() and not (root / "bundle.json").exists()
        return
    assert (code, checked) == (0, {"status": "ready", "issues": []})
    inspection = engine(root, "terraform_invented_resource" if scenario == "invented" else "terraform_data")
    if scenario == "invented":
        assert inspection == {"status": "validate-failed"}
        assert not (root / "bundle.json").exists()
        return
    write_json(root, "review.json", review(root, optional, scenario == "gap"))
    code, checked = invoke(
        gate, capsys, root, "check-review", "review.json", "--saved-plan", "tfplan", "--checklist", "checklist.md",
    )
    if scenario == "gap":
        assert (code, checked) == (1, {"status": "insufficient-evidence", "issues": []})
        assert not (root / "bundle.json").exists()
        return
    assert (code, checked) == (0, {"status": "pass", "issues": []})
    write_json(root, "review-result.json", checked)
    bundle(root, inspection, scripts["plan_bundle"])
    code, checked = invoke(
        scripts["plan_bundle"], capsys, root, "validate", "bundle.json",
        "--policy", "trusted-policy.json", "--now", NOW,
    )
    assert code == 0 and checked["status"] == "valid", checked
    assert checked["issues"] == []
    assert all(item["verification"] == "verified" for item in checked["evidence"])
