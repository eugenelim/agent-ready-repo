"""Construction checks for the security-checklists OKF pilot projection."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "security-checklists"
OKF_ROOT = PACK_ROOT / "okf" / "security-checklists"
MANIFEST = PACK_ROOT / ".okf-generated.json"
RFC_NOTES = PACK_ROOT.parents[1] / "docs" / "rfc" / "0087-notes"

MODULES = [
    "access-control",
    "agentic-skills",
    "authn-session",
    "config-misconfig",
    "exceptional-conditions",
    "injection",
    "llm-agent",
    "outbound-ssrf",
    "path-and-file",
    "secrets-and-crypto",
    "supply-chain",
]


def test_current_security_checklist_modules_are_frozen() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "name: security-checklists" in skill
    assert "generated-by: compile-okf agentbundle-okf/v1" in skill
    assert "Read `references/okf/index.md` first." in skill
    assert "do not load the full bundle up front" in skill
    for module in MODULES:
        reference = SKILL_ROOT / "references" / f"{module}.md"
        assert reference.is_file(), module
        body = reference.read_text(encoding="utf-8")
        assert "## Spec-stage" in body
        assert "## Implementation checks" in body
        assert "## Established-helper bypass" in body


def test_security_checklists_okf_source_and_generated_tree_exist() -> None:
    assert (OKF_ROOT / "index.md").is_file()
    for module in MODULES:
        assert (OKF_ROOT / "concepts" / f"{module}.md").is_file(), module
        assert (
            SKILL_ROOT / "references" / "okf" / "concepts" / f"{module}.md"
        ).is_file(), module
    assert (SKILL_ROOT / "references" / "okf" / "index.md").is_file()
    assert MANIFEST.is_file()


def test_security_checklists_manifest_is_generic_okf_projection() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = {record["output_path"]: record for record in manifest["managed"]}
    router = records[".apm/skills/security-checklists/SKILL.md"]

    assert manifest["profile"] == "agentbundle-okf/v1"
    assert manifest["router_skill"] == "security-checklists"
    assert router["kind"] == "okf-router"
    assert router["source_path"] == "okf/security-checklists"
    assert router["source_digest"].startswith("sha256:")
    assert router["source_digest"] != "sha256:" + "0" * 64
    for module in MODULES:
        path = f".apm/skills/security-checklists/references/okf/concepts/{module}.md"
        assert records[path]["kind"] == "okf-reference"
        assert records[path]["source_path"] == f"okf/security-checklists/concepts/{module}.md"


def test_core_version_and_okf_declaration_are_synchronized() -> None:
    pack = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    plugin = json.loads(
        (PACK_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    assert pack["pack"]["version"] == "2.8.0"
    assert plugin["version"] == "2.8.0"
    assert pack["pack"]["metadata"]["okf"]["profile"] == "agentbundle-okf/v1"
    bundle = pack["pack"]["metadata"]["okf"]["bundles"][0]
    assert bundle["id"] == "security-checklists"
    assert bundle["path"] == "okf/security-checklists"
    assert bundle["router-skill"] == "security-checklists"


def test_security_checklists_cases_and_pending_baseline_are_frozen() -> None:
    cases = json.loads(
        (RFC_NOTES / "pilot-cases" / "security-checklists.json").read_text(
            encoding="utf-8"
        )
    )
    baseline = json.loads(
        (
            RFC_NOTES
            / "pilot-baselines"
            / "security-checklists-pending-model-e2e.json"
        ).read_text(encoding="utf-8")
    )

    case_items = cases["cases"]
    assert cases["status"] == "frozen"
    assert len(case_items) == 20
    assert sum(1 for item in case_items if item["security_critical"]) >= 5
    assert {item["expected_path"] for item in case_items} == {
        f"concepts/{module}.md" for module in MODULES
    }
    assert baseline["status"] == "pending"
    assert baseline["harness"] == cases["harness"]
    assert baseline["summary"]["case_count"] == 20
    assert baseline["summary"]["top_1_expected_path_success"] is None
    assert baseline["results"] == []
