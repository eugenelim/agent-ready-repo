"""Repository construction checks for the security-checklists OKF pilot."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPO_ROOT / "packs" / "core"
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "security-checklists"
GENERATED_SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "security-checklists-reference"
WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
OKF_ROOT = PACK_ROOT / "okf" / "security-checklists"
MANIFEST = PACK_ROOT / ".okf-generated.json"
RFC_NOTES = REPO_ROOT / "docs" / "rfc" / "0087-notes"

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
ROUTES = {
    "access-control": ("authz / object- & function-level access; a new or changed endpoint, handler, RPC", "OWASP A01:2025 + API Security Top 10:2023 (BOLA/BFLA)"),
    "agentic-skills": ("skill-file authoring / modification, skill metadata parsing, skill distribution packaging, skill execution sandbox config", "OWASP Agentic Skills Top 10 v1.0 (AST01–AST10)"),
    "authn-session": ("authentication, session, login, password, MFA, tokens (JWT / API key)", "OWASP A07:2025 + ASVS 5.0 V6/V7"),
    "config-misconfig": ("CORS, IAM, IaC, server / framework / deploy config", "OWASP A02:2025"),
    "exceptional-conditions": ("error handling, retries, fallbacks, fail-open paths", "**OWASP A10:2025 (new)** (+ A09 logging)"),
    "injection": ("untrusted input → interpreter / deserializer (SQL / shell / template / LDAP / HTML; deserialization)", "OWASP A05:2025 (+ A08 deserialization)"),
    "llm-agent": ("prompts, model / tool exposure, MCP, model-output handling, agentic action", "OWASP LLM Top 10:2025 + OWASP Top 10 for Agentic Applications:2026"),
    "outbound-ssrf": ("outbound HTTP / DNS / URL fetch, webhooks", "OWASP A01:2025 (SSRF) + ASVS 5.0 V13"),
    "path-and-file": ("filesystem path from input, file upload, archive extraction", "CWE-22 / CWE-73 + ASVS 5.0 V12"),
    "secrets-and-crypto": ("secrets, keys, hashing, signing, crypto, randomness", "OWASP A04:2025 + ASVS 5.0 V11"),
    "supply-chain": ("dependency / lockfile / manifest change, build-artifact fetch (build trust)", "**OWASP A03:2025 (new)**"),
}


def test_current_security_checklist_modules_are_frozen() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    work_loop = WORK_LOOP_SKILL.read_text(encoding="utf-8")

    assert "name: security-checklists" in skill
    assert "generated-by: compile-okf agentbundle-okf/v1" not in skill
    assert "<!-- agentbundle-okf: router-handoff=author-owned -->" in skill
    assert skill.count("| [`") == len(MODULES)
    assert "deterministic boundary→module routing authority" in skill
    assert "**`tool`**" in skill
    assert "**`hybrid`**" in skill
    assert "**`reason`**" in skill
    assert "Route via [`security-checklists` Module index]" in work_loop
    for module in MODULES:
        boundary, anchor = ROUTES[module]
        assert f"| [`{module}`](references/{module}.md) | {boundary} | {anchor} |" in skill
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
            GENERATED_SKILL_ROOT / "references" / "okf" / "concepts" / f"{module}.md"
        ).is_file(), module
    generated_router = (GENERATED_SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "generated-by: compile-okf agentbundle-okf/v1" in generated_router
    assert (GENERATED_SKILL_ROOT / "references" / "okf" / "index.md").is_file()
    assert MANIFEST.is_file()


def test_security_checklists_manifest_is_generic_okf_projection() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    records = {record["output_path"]: record for record in manifest["managed"]}
    router = records[".apm/skills/security-checklists-reference/SKILL.md"]

    assert manifest["profile"] == "agentbundle-okf/v1"
    assert manifest["router_skill"] == "security-checklists-reference"
    assert router["kind"] == "okf-router"
    assert router["source_path"] == "okf/security-checklists"
    assert router["source_digest"].startswith("sha256:")
    assert router["source_digest"] != "sha256:" + "0" * 64
    for module in MODULES:
        path = f".apm/skills/security-checklists-reference/references/okf/concepts/{module}.md"
        assert records[path]["kind"] == "okf-reference"
        assert records[path]["source_path"] == f"okf/security-checklists/concepts/{module}.md"


def test_core_version_and_okf_declaration_are_synchronized() -> None:
    pack = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    plugin = json.loads(
        (PACK_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )

    assert pack["pack"]["version"] == "2.12.0"
    assert plugin["version"] == "2.12.0"
    assert pack["pack"]["version"] == plugin["version"]
    assert pack["pack"]["metadata"]["okf"]["profile"] == "agentbundle-okf/v1"
    bundle = pack["pack"]["metadata"]["okf"]["bundles"][0]
    assert bundle["id"] == "security-checklists"
    assert bundle["path"] == "okf/security-checklists"
    assert bundle["router-skill"] == "security-checklists-reference"


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
