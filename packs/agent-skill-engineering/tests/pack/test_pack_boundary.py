"""Portable-pack and external-wrapper boundary contracts."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from pathlib import Path

import pytest
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
        # Catalogue-facing links; `repository` is what derives the marketplace
        # entry's `source`, without which the published install cannot fetch.
        "links",
        # Required of every non-underscore pack by tests/conformance, and the
        # source of the published marketplace entry's `author`.
        "maintainers",
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


def _names_mode(description: str, mode: str) -> bool:
    """Does `description` name `mode`, in any ordinary surface form?

    The foundation spec's AC4 obligation is mode-level, so matching one
    spelling is not enough.
    Three earlier versions were each defeated by the next form a reviewer
    tried: `\\b<mode>\\b` missed the plural ("plugins"), `\\b<mode>s?\\b`
    missed the space-separated spelling of the hyphenated modes ("knowledge
    providers") and the split spelling of a closed one ("sub-agents"), and an
    unbounded separator-free containment test then over-matched ordinary prose
    -- "plug into" read as `plugin`, "unhook" as `hook`, and the comma list
    "a runtime, profile, and package review" as `runtime-profile`.

    So the comparison is bounded on both sides. The description is split into
    segments at punctuation, because a mode name never spans a comma or a full
    stop; each segment is tokenized to alphanumeric runs; and a mode matches
    only when some window of at most one more token than the mode has parts
    joins to exactly the mode's own joined letters, allowing a single trailing
    plural `s`. Bounding the window is what keeps "plug into" from joining to
    `plugin`, and splitting at punctuation is what keeps a comma list from
    forming a mode that was never written.
    """

    parts = re.findall(r"[a-z0-9]+", mode.lower())
    target = "".join(parts)
    for segment in re.split(r"[^\w\s-]+", description.lower()):
        words = re.findall(r"[a-z0-9]+", segment)
        for size in range(1, len(parts) + 2):
            for start in range(len(words) - size + 1):
                joined = "".join(words[start:start + size])
                if joined == target or joined.removesuffix("s") == target:
                    return True
    return False


def test_no_unsupported_mode_name_leaks_into_either_activation_description() -> None:
    """The foundation spec's AC4 absence clause, over every mode and both
    workflow descriptions.

    The per-workflow suites check the SKILL.md *bodies*, where these names are
    required to appear in the unavailable-response contract. The absence
    obligation is the opposite and belongs to the description, and it is
    pack-scoped rather than per-workflow: naming an unsupported mode on either
    activation surface is what would route an unavailable request into a
    workflow. Modes come from the fixture that already defines the closed
    vocabulary. The count assert below is an anti-vacuity floor pinned to
    the closed enumeration: a mode appearing or disappearing reddens it
    deliberately, so changing coverage is a synced decision rather than
    something that happens silently. It is five now that knowledge-provider is
    advertised.
    """

    modes = {
        case["mode"]
        for case in json.loads(
            (
                PACK_ROOT / "tests" / "fixtures" / "unsupported-mode-cases.json"
            ).read_text(encoding="utf-8")
        )["cases"]
    }
    assert len(modes) == 5

    for name, root in WORKFLOW_ROOTS.items():
        text = (root / "SKILL.md").read_text(encoding="utf-8")
        _, raw, _ = text.split("---\n", 2)
        parsed = yaml.safe_load(raw)
        description = str(parsed["description"]).lower()
        for mode in modes:
            assert not _names_mode(description, mode), (
                f"{name} description names unsupported mode {mode!r}"
            )


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


# A durable positive control for the mode matcher. Without it a matcher that
# silently stopped detecting anything would leave the guard above green while
# proving nothing -- the guard only ever asserts that a form is *absent*.
DETECTED_FORMS = [
    ("runtime-package", "use for runtime-package work"),
    ("runtime-package", "use for knowledge providers and runtime packages"),
    ("subagent", "handles sub-agents too"),
    ("plugin", "use for plugins, hooks, and subagents"),
    ("hook", "use for plugins, hooks, and subagents"),
    ("runtime-profile", "covers runtime profiles as well"),
]


@pytest.mark.parametrize("mode,description", DETECTED_FORMS)
def test_matcher_detects_forbidden_surface_forms(mode: str, description: str) -> None:
    """Plural, space-separated, and hyphen-split spellings all count."""
    assert _names_mode(description, mode), (mode, description)


def test_matcher_does_not_fire_on_neutral_prose() -> None:
    """A reworded opening naming no mode is not a match."""
    assert not _names_mode("Use when a user asks for help with a skill", "plugin")
    assert not _names_mode("Use when a user asks for help with a skill", "subagent")


def test_knowledge_provider_is_no_longer_in_the_unsupported_enumeration() -> None:
    """The advertised mode left the closed unavailable set."""
    modes = {
        case["mode"]
        for case in json.loads(
            (
                PACK_ROOT / "tests" / "fixtures" / "unsupported-mode-cases.json"
            ).read_text(encoding="utf-8")
        )["cases"]
    }
    assert "knowledge-provider" not in modes
    assert modes == {"runtime-package", "runtime-profile", "plugin", "hook", "subagent"}
