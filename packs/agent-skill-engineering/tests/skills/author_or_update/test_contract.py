"""Construction contracts for the progressive authoring workflow."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml

PACK_ROOT = Path(__file__).resolve().parents[3]
AUTHOR_ROOT = PACK_ROOT / ".apm" / "skills" / "author-or-update-agent-skill"
# Literal so every path this suite opens is statically confined to its own
# pack; the routes the SKILL.md actually names are asserted against these.
AUTHOR_ROUTES = (
    "references/create.md",
    "references/frame.md",
    "references/knowledge-surfaces.md",
    "references/language-extension-seams.md",
    "references/provider-contract.md",
    "references/safety-and-authority.md",
    "references/update.md",
)
AUTHOR_EVIDENCE_SOURCES = (
    "evals/evals.json",
    "evals/files/update-existing-SKILL.md",
)


def _frontmatter(text: str) -> dict[str, object]:
    """Parse skill YAML frontmatter."""

    assert text.startswith("---\n")
    _, raw, _ = text.split("---\n", 2)
    parsed = yaml.safe_load(raw)
    assert isinstance(parsed, dict)
    return parsed


def test_authoring_skill_exposes_only_the_progressive_foundation_modes() -> None:
    text = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata = _frontmatter(text)
    assert metadata["name"] == "author-or-update-agent-skill"
    assert metadata["metadata"] == {
        "boundaries": ["filesystem_read_untrusted", "filesystem_write"]
    }
    description = str(metadata["description"]).lower()
    for positive in ("frame", "create", "update", "agent skill"):
        assert positive in description
    assert "use when the user asks" in description
    assert "skill.md" in description
    for internal in ("knowledge-provider", "runtime-package", "agentbundle"):
        assert internal not in description
    # An unnamed or ambiguous target must route into this workflow rather than
    # producing a clarifying refusal that never selects it.
    assert "select it first and resolve the target inside the workflow" in description
    assert "with nothing attached" in description
    assert "do not use for review-only requests" in description
    # Outcome, not vocabulary, separates the two adjacent workflows.
    assert "any request whose outcome is a changed skill file belongs here" in description
    assert "resolving an ambiguous target is this workflow's first step" in text
    assert "`frame` is the default and is read-only" in text
    assert "explicit mode transition" in text
    for unavailable in (
        "`knowledge-provider`",
        "`runtime-package`",
        "`runtime-profile`",
        "`plugin`",
        "`hook`",
        "`subagent`",
    ):
        assert unavailable in text
    assert "contract_version: agent-skill-engineering-foundation/v1" in text
    assert "status: unavailable" in text


def test_every_unsupported_mode_has_the_exact_versioned_unavailable_result() -> None:
    fixture = json.loads(
        (
            PACK_ROOT / "tests" / "fixtures" / "unsupported-mode-cases.json"
        ).read_text(encoding="utf-8")
    )
    text = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    modes = {case["mode"] for case in fixture["cases"]}

    assert modes == {
        "knowledge-provider",
        "runtime-package",
        "runtime-profile",
        "plugin",
        "hook",
        "subagent",
    }
    assert all(case["expected_status"] == "unavailable" for case in fixture["cases"])
    assert fixture["contract_version"] in text
    assert f"reason: {fixture['reason']}" in text
    assert f"baseline: {fixture['baseline']}" in text
    assert all(f"`{mode}`" in text for mode in modes)


def test_authoring_skill_routes_progressively_and_keeps_local_links_valid() -> None:
    text = (AUTHOR_ROOT / "SKILL.md").read_text(encoding="utf-8")
    routes = re.findall(r"\((references/[^)]+\.md)\)", text)
    assert set(routes) == set(AUTHOR_ROUTES)
    assert text.index("references/frame.md") < text.index("references/create.md")
    assert text.index("references/create.md") < text.index("references/update.md")


@pytest.mark.parametrize("route", AUTHOR_ROUTES)
def test_authoring_reference_route_resolves(route: str) -> None:
    assert (AUTHOR_ROOT / route).is_file()


def test_boundary_contract_confines_before_read_and_isolates_authentication() -> None:
    safety = (AUTHOR_ROOT / "references" / "safety-and-authority.md").read_text(
        encoding="utf-8"
    )
    assert "Canonicalize and symlink-resolve" in safety
    assert "without reading" in safety
    assert "candidate's contents" in safety
    assert "immediately before mutation" in safety
    assert "filesystem_read_untrusted" in safety
    assert "filesystem_write" in safety
    assert "Do not inspect credentials" in safety
    assert "least-authority broker" in safety


def test_activation_examples_are_discriminating_and_versionable() -> None:
    cases = json.loads(
        (AUTHOR_ROOT / "evals" / "eval_queries.json").read_text(encoding="utf-8")
    )
    assert len(cases) >= 8
    assert any(case["should_trigger"] for case in cases)
    assert any(not case["should_trigger"] for case in cases)
    assert all(set(case) == {"query", "should_trigger"} for case in cases)


def test_authoring_behavior_evals_cover_frame_and_existing_update() -> None:
    payload = json.loads(
        (AUTHOR_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
    )
    cases = {case["id"]: case for case in payload["evals"]}

    assert set(cases) == {"frame-new-skill", "update-existing-skill"}
    assert cases["frame-new-skill"].get("files") is None
    update_files = cases["update-existing-skill"]["files"]
    assert update_files == ["evals/files/update-existing-SKILL.md"]
    assert (AUTHOR_ROOT / "evals" / "files" / "update-existing-SKILL.md").is_file()
    assert all(case["assertions"] for case in cases.values())
    assert all(case["expect"]["output_contains"] for case in cases.values())


def test_independent_behavior_results_cover_both_authoring_cases() -> None:
    evidence = json.loads(
        (
            PACK_ROOT / "tests" / "fixtures" / "behavior-results.json"
        ).read_text(encoding="utf-8")
    )
    results = {result["eval_id"]: result for result in evidence["results"]}
    cases = {
        case["id"]: case
        for case in json.loads(
            (AUTHOR_ROOT / "evals" / "evals.json").read_text(encoding="utf-8")
        )["evals"]
    }

    assert set(results) == {
        "frame-new-skill",
        "update-existing-skill",
        "detect-activation-failure",
        "detect-script-contract-failure",
    }
    for eval_id in ("frame-new-skill", "update-existing-skill"):
        result = results[eval_id]
        case = cases[eval_id]
        assert all(result["assertions"])
        # Bind the record to what the eval declares, not merely to truthiness.
        # Without this a recorded run could claim any markers at all -- the
        # negation of the frame mode's read-only contract included -- and stay
        # green, because the digests below bind the eval *inputs* and never the
        # recorded outcome. Mirrors the review side's `actual_findings` check.
        assert set(result["actual_markers"]) == set(case["expect"]["output_contains"])
        assert len(result["assertions"]) == len(case["assertions"])
        # Every source the evidence binds must be one this suite digests below,
        # so a newly named source cannot arrive unverified.
        assert set(result["source_files"]) <= set(AUTHOR_EVIDENCE_SOURCES)


@pytest.mark.parametrize("relative_path", AUTHOR_EVIDENCE_SOURCES)
def test_authoring_behavior_evidence_matches_its_source_digest(
    relative_path: str,
) -> None:
    evidence = json.loads(
        (
            PACK_ROOT / "tests" / "fixtures" / "behavior-results.json"
        ).read_text(encoding="utf-8")
    )
    path = AUTHOR_ROOT / relative_path
    assert path.is_file()
    digest = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    recorded = {
        result["source_files"][relative_path]
        for result in evidence["results"]
        if relative_path in result.get("source_files", {})
    }
    assert recorded == {digest}


def test_portable_workflow_contains_no_delivery_or_runtime_coupling() -> None:
    content = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(AUTHOR_ROOT.rglob("*.md"))
    ).lower()
    for forbidden in (
        "packages/agentbundle",
        "agentbundle install",
        "agentbundle-manifest",
        ".claude-plugin",
        ".codex/skills",
    ):
        assert forbidden not in content
