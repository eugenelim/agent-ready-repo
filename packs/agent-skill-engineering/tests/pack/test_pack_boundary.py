"""Portable-pack and external-wrapper boundary contracts."""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import yaml

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills"
ROUTER_SKILL = "ase-okf-reference"
# Anchored literally rather than joined from the evidence file's keys, so every
# path this module opens is statically confined to its owning pack.
WORKFLOW_ROOTS = {
    "author-or-update-agent-skill": SKILL_ROOT / "author-or-update-agent-skill",
    "review-or-optimize-agent-skill": SKILL_ROOT / "review-or-optimize-agent-skill",
}


def _boundaries(path: Path) -> list[str]:
    """Return declared skill boundaries."""

    text = path.read_text(encoding="utf-8")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return list(parsed["metadata"]["boundaries"])


def test_external_manifest_contains_registration_not_workflow_behavior() -> None:
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    pack = manifest["pack"]
    assert set(pack) == {
        "name",
        "version",
        "description",
        "display_name",
        "readme",
        "license",
        "categories",
        "keywords",
        "adapter-contract",
        "install",
        "evals",
        "metadata",
    }
    serialized = (PACK_ROOT / "pack.toml").read_text(encoding="utf-8").lower()
    for forbidden in ("procedure", "canonicalize", "provider response", "credential"):
        assert forbidden not in serialized


def test_portable_tree_contains_no_adapter_or_publication_implementation() -> None:
    portable = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(SKILL_ROOT.rglob("*"))
        if path.is_file() and path.suffix in {".md", ".json", ".toml"}
    ).lower()
    for forbidden in (
        "packages/agentbundle",
        "agentbundle install",
        ".claude-plugin/plugin.json",
        "adapter projection code",
        "catalogue admission workflow",
    ):
        assert forbidden not in portable


def test_skill_boundaries_match_the_least_authority_contract() -> None:
    assert _boundaries(SKILL_ROOT / "author-or-update-agent-skill" / "SKILL.md") == [
        "filesystem_read_untrusted",
        "filesystem_write",
    ]
    assert _boundaries(SKILL_ROOT / "review-or-optimize-agent-skill" / "SKILL.md") == [
        "filesystem_read_untrusted",
        "filesystem_write",
    ]
    assert _boundaries(SKILL_ROOT / "ase-okf-reference" / "SKILL.md") == [
        "filesystem_read_untrusted"
    ]


def test_independent_activation_results_bind_all_queries_and_descriptions() -> None:
    evidence = json.loads(
        (PACK_ROOT / "tests" / "fixtures" / "activation-results.json").read_text(
            encoding="utf-8"
        )
    )

    # The recorded classification must come from the headless detector that
    # observes the real Skill tool_use event, not from a self-reported
    # in-harness claim that cannot contradict itself.
    assert evidence["evaluation_mode"] == "headless-observed"
    assert evidence["adapter"] == "claude-code"
    assert evidence["runs"] >= 1
    assert set(evidence["skills"]) == set(WORKFLOW_ROOTS)
    for skill, result in evidence["skills"].items():
        skill_root = WORKFLOW_ROOTS[skill]
        skill_digest = hashlib.sha256((skill_root / "SKILL.md").read_bytes()).hexdigest()
        query_path = skill_root / "evals" / "eval_queries.json"
        query_digest = hashlib.sha256(query_path.read_bytes()).hexdigest()
        queries = json.loads(query_path.read_text(encoding="utf-8"))

        assert result["skill_digest"] == "sha256:" + skill_digest
        assert result["query_fixture_digest"] == "sha256:" + query_digest
        assert len(result["cases"]) == len(queries)
        for index, (case, query) in enumerate(zip(result["cases"], queries, strict=True)):
            expected = skill if query["should_trigger"] else None
            assert case["query_id"] == f"q{index:02d}"
            assert case["query"] == query["query"]
            assert case["expected"] == expected
            # `actual` names whichever in-pack skill fired, so the router being
            # selected *instead of* a workflow fails here.
            assert case["actual"] == expected
            assert case["errored_runs"] == 0
            # The eval runner's own `passed` flag ignores co-firing, so it is
            # asserted separately. A positive query may also select the
            # generated router — the workflow is allowed an explicit provider
            # call — but nothing may fire on a negative query.
            allowed = {ROUTER_SKILL} if query["should_trigger"] else set()
            assert set(case["exclusivity_violations"]) <= allowed
