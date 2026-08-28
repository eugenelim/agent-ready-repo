"""Pack-surface contracts for the optional shaping-to-Core handoff."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "packs" / "core"
PRODUCT = ROOT / "packs" / "product-engineering"
CAPABILITY = "normalized-intake.v1#handoff"
NORMALIZED_INTAKE_SCHEMA = ROOT / "contracts/jsonschema/normalized-intake.schema.json"


def _manifest(pack: Path) -> dict[str, object]:
    return tomllib.loads((pack / "pack.toml").read_text(encoding="utf-8"))


def _skill(pack: Path, name: str) -> str:
    return (pack / ".apm" / "skills" / name / "SKILL.md").read_text(
        encoding="utf-8"
    )


def _evals(pack: Path, name: str) -> dict[str, object]:
    return json.loads(
        (pack / ".apm" / "skills" / name / "evals" / "evals.json").read_text(
            encoding="utf-8"
        )
    )


def _boundaries(skill: str) -> set[str]:
    match = re.search(
        r"^  boundaries:\n((?:    - .+\n)+)", skill, flags=re.MULTILINE
    )
    assert match is not None
    return {
        line.removeprefix("    - ")
        for line in match.group(1).splitlines()
    }


def test_product_engineering_declares_optional_exact_handoff() -> None:
    manifest = _manifest(PRODUCT)
    integrations = manifest["pack"]["integrations"]
    handoff = next(item for item in integrations if item["id"] == "core-delivery-handoff")

    assert handoff == {
        "id": "core-delivery-handoff",
        "pack": "core",
        "kind": "handoff",
        "role": "Confirmed shaping-to-delivery handoff",
        # CAT-V-019 resolves `consumers` inside the declaring pack and
        # `providers` inside the target pack: Core's work-intake provides the
        # handoff capability that these product-engineering skills consume.
        "consumers": ["skill:discovery-loop", "skill:decompose-intent"],
        "providers": ["skill:work-intake"],
        "when": (
            "A confirmed shaping gate produces a delivery contract or delivery "
            "brief and the current Core invocation advertises "
            "normalized-intake.v1#handoff."
        ),
        "purpose": (
            "Pass bounded shaping context into Core intake without changing "
            "downstream lifecycle, authoring, or approval gates."
        ),
        "fallback": (
            "If Core is absent, unknown, or predates the handoff capability, "
            "render the same bounded portable handoff and omit the unsupported "
            "top-level object."
        ),
    }
    assert "dependencies" not in manifest["pack"]


def test_producers_and_consumers_declare_untrusted_read_boundary() -> None:
    for pack, name in (
        (PRODUCT, "discovery-loop"),
        (PRODUCT, "decompose-intent"),
        (CORE, "work-intake"),
        (CORE, "new-spec"),
        (CORE, "intake-intent"),
        (CORE, "author-delivery-brief"),
    ):
        assert "filesystem_read_untrusted" in _boundaries(_skill(pack, name))


def test_skill_contracts_pin_role_capability_and_fallback() -> None:
    discovery = _skill(PRODUCT, "discovery-loop")
    decompose = _skill(PRODUCT, "decompose-intent")
    intake = _skill(CORE, "work-intake")

    for body in (discovery, decompose, intake):
        assert CAPABILITY in body
        assert "delivery contract" in body
        assert "delivery brief" in body
    assert "Core absence" in discovery
    assert "portable rendered" in discovery
    assert "Absence preserves standalone Core behavior" in intake


def test_evals_cover_negotiation_routes_and_no_external_dereference() -> None:
    producer = json.dumps(_evals(PRODUCT, "discovery-loop"), sort_keys=True)
    intake_evals = _evals(CORE, "work-intake")["evals"]

    for phrase in ("Core is absent", "capability is unknown", "predates"):
        assert phrase in producer
    for phrase in (
        "repository handoff",
        "cross-repository outcome",
        "already-acquired external",
        "equally ranked",
        "without a handoff",
        "optional configured",
    ):
        assert phrase in json.dumps(intake_evals, sort_keys=True)

    acquired_external = next(
        case
        for case in intake_evals
        if "already-acquired external" in case["prompt"]
    )
    assert (
        "performs no network, tracker, shell, credential, DNS, search, probe, "
        "filesystem, or fetch operation derived from it"
        in acquired_external["expected_output"]
    )
    assert "Keeps the external locator opaque" in acquired_external["assertions"]

    external_cases = {
        "new-spec": next(
            case
            for case in _evals(CORE, "new-spec")["evals"]
            if "external locator" in case["prompt"]
        ),
        "intake-intent": next(
            case
            for case in _evals(CORE, "intake-intent")["evals"]
            if case["id"] == "passive-external-source"
        ),
        "author-delivery-brief": next(
            case
            for case in _evals(CORE, "author-delivery-brief")["evals"]
            if case["id"] == "create-hostile-external-source"
        ),
    }
    for name, external in external_cases.items():
        rendered = json.dumps(external, sort_keys=True)
        assert "external-locator" in rendered or "external locator" in rendered, name
        assert "no external-locator access" in rendered or "performs no fetch" in rendered


def test_pack_and_plugin_versions_match_once() -> None:
    for pack in (CORE, PRODUCT):
        manifest_version = _manifest(pack)["pack"]["version"]
        plugin_version = json.loads(
            (pack / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )["version"]
        assert manifest_version == plugin_version


def test_normalized_intake_digest_matches_source_and_projections() -> None:
    expected = hashlib.sha256(NORMALIZED_INTAKE_SCHEMA.read_bytes()).hexdigest()
    engines = (
        CORE / ".apm/skills/workspace-status/scripts/workspace_status_engine.py",
        ROOT / ".agents/skills/workspace-status/scripts/workspace_status_engine.py",
        ROOT / ".claude/skills/workspace-status/scripts/workspace_status_engine.py",
        ROOT / "packages/agentbundle/agentbundle/_data/workspace_status_engine.py",
    )

    for engine in engines:
        assert f'"{expected}"' in engine.read_text(encoding="utf-8")
