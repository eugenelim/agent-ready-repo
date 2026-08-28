"""Integrated contracts for the core work-intake surface."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import tomllib
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parents[2]
_SKILLS = _PACK_ROOT / ".apm" / "skills"
_WORK_INTAKE = _SKILLS / "work-intake"
_SEEDS = _PACK_ROOT / "seeds"
_MATRIX = _WORK_INTAKE / "evals" / "files" / "routing" / "matrix.json"
_CONTRACT_FIXTURES = (
    _PACK_ROOT / "tests" / "pack" / "fixtures" / "work-intake-contracts"
)
_ENGINE_PATH = (
    _SKILLS / "workspace-status" / "scripts" / "workspace_status_engine.py"
)
_ROUTER_PATH = _WORK_INTAKE / "scripts" / "intake_router.py"
_SKILL_BODIES = {
    "work-intake": (_SKILLS / "work-intake" / "SKILL.md").read_text(encoding="utf-8"),
    "intake-intent": (_SKILLS / "intake-intent" / "SKILL.md").read_text(encoding="utf-8"),
    "capture-work": (_SKILLS / "capture-work" / "SKILL.md").read_text(encoding="utf-8"),
    "author-delivery-brief": (_SKILLS / "author-delivery-brief" / "SKILL.md").read_text(encoding="utf-8"),
    "author-brief": (_SKILLS / "author-brief" / "SKILL.md").read_text(encoding="utf-8"),
    "receive-brief": (_SKILLS / "receive-brief" / "SKILL.md").read_text(encoding="utf-8"),
    "new-spec": (_SKILLS / "new-spec" / "SKILL.md").read_text(encoding="utf-8"),
    "workspace-status": (_SKILLS / "workspace-status" / "SKILL.md").read_text(encoding="utf-8"),
    "work-loop": (_SKILLS / "work-loop" / "SKILL.md").read_text(encoding="utf-8"),
}
_EVAL_QUERY_FILES = {
    "new-spec": _SKILLS / "new-spec" / "evals" / "eval_queries.json",
    "bug-fix": _SKILLS / "bug-fix" / "evals" / "eval_queries.json",
    "init-project": _SKILLS / "init-project" / "evals" / "eval_queries.json",
    "adapt-to-project": _SKILLS / "adapt-to-project" / "evals" / "eval_queries.json",
    "workspace-status": _SKILLS / "workspace-status" / "evals" / "eval_queries.json",
    "project-knowledge": _SKILLS / "project-knowledge" / "evals" / "eval_queries.json",
    "work-intake": _SKILLS / "work-intake" / "evals" / "eval_queries.json",
    "intake-intent": _SKILLS / "intake-intent" / "evals" / "eval_queries.json",
    "author-delivery-brief": _SKILLS / "author-delivery-brief" / "evals" / "eval_queries.json",
    "author-brief": _SKILLS / "author-brief" / "evals" / "eval_queries.json",
    "receive-brief": _SKILLS / "receive-brief" / "evals" / "eval_queries.json",
    "capture-work": _SKILLS / "capture-work" / "evals" / "eval_queries.json",
    "close-work": _SKILLS / "close-work" / "evals" / "eval_queries.json",
}
_FIXTURE_PATHS = {
    "evals/files/routing/start-minimal-intent.json": (
        _WORK_INTAKE / "evals" / "files" / "routing" / "start-minimal-intent.json"
    ),
    "evals/files/routing/start-direct-light.json": (
        _WORK_INTAKE / "evals" / "files" / "routing" / "start-direct-light.json"
    ),
    "evals/files/routing/migration-selection.json": (
        _WORK_INTAKE / "evals" / "files" / "routing" / "migration-selection.json"
    ),
    "normalized-intake/valid/remember-repo-origin-prompt-like-data.json": (
        _CONTRACT_FIXTURES
        / "normalized-intake"
        / "valid"
        / "remember-repo-origin-prompt-like-data.json"
    ),
    "workspace/context/lifecycle.toml": (
        _CONTRACT_FIXTURES / "workspace" / "context" / "lifecycle.toml"
    ),
    "normalized-intake/valid/refresh-repo-origin.json": (
        _CONTRACT_FIXTURES
        / "normalized-intake"
        / "valid"
        / "refresh-repo-origin.json"
    ),
    "workspace/target/valid/spec-with-cross-repo-need.json": (
        _CONTRACT_FIXTURES
        / "workspace"
        / "target"
        / "valid"
        / "spec-with-cross-repo-need.json"
    ),
    "workspace/target/valid/brief-tracker-origin-coordination.json": (
        _CONTRACT_FIXTURES
        / "workspace"
        / "target"
        / "valid"
        / "brief-tracker-origin-coordination.json"
    ),
    "workspace/target/valid/defect-repo-origin.json": (
        _CONTRACT_FIXTURES
        / "workspace"
        / "target"
        / "valid"
        / "defect-repo-origin.json"
    ),
    "normalized-intake/valid/start-repo-origin.json": (
        _CONTRACT_FIXTURES
        / "normalized-intake"
        / "valid"
        / "start-repo-origin.json"
    ),
}
_CHANGED_SKILLS = {
    "work-intake": ("Read Write Edit Bash", {"filesystem_write", "filesystem_read_untrusted"}),
    "intake-intent": ("Read Write Edit", {"filesystem_write", "filesystem_read_untrusted"}),
    "capture-work": ("Read Write Edit Bash", {"filesystem_write", "filesystem_read_untrusted"}),
    "author-delivery-brief": ("Read Write Edit", {"filesystem_write", "filesystem_read_untrusted"}),
    "author-brief": ("Read", set()),
    "receive-brief": ("Read", set()),
    "new-spec": (
        "Read Write Edit Bash WebFetch WebSearch",
        {"filesystem_write", "filesystem_read_untrusted", "network_fetch"},
    ),
    "workspace-status": ("Read Write Edit Bash", {"filesystem_write", "filesystem_read_untrusted"}),
    "work-loop": ("Read Write Edit Bash Agent", {"filesystem_write", "filesystem_read_untrusted"}),
}


def _load_engine():
    spec = importlib.util.spec_from_file_location("workspace_status_engine", _ENGINE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["workspace_status_engine"] = module
    spec.loader.exec_module(module)
    return module


def _load_router():
    spec = importlib.util.spec_from_file_location("intake_router", _ROUTER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["intake_router"] = module
    spec.loader.exec_module(module)
    return module


def _frontmatter(body: str) -> str:
    assert body.startswith("---\n")
    return body.split("---\n", 2)[1]


def _boundaries(frontmatter: str) -> set[str]:
    if re.search(r"^  boundaries: \[\]$", frontmatter, re.MULTILINE):
        return set()
    match = re.search(r"^  boundaries:\n((?:    - .+\n)+)", frontmatter, re.MULTILINE)
    assert match is not None
    return {line.removeprefix("    - ") for line in match.group(1).splitlines()}


def _fixture_path(value: str) -> Path:
    return _FIXTURE_PATHS[value]


def test_routing_matrix_is_schema_valid_complete_and_deterministic() -> None:
    engine = _load_engine()
    router = _load_router()
    raw = _MATRIX.read_text(encoding="utf-8")
    matrix = json.loads(raw)
    cases = matrix["cases"]
    assert matrix["contract_version"] == "work-intake-routing-evals.v1"
    assert {
        "direct-light",
        "start-minimal-intent",
        "remember-draft",
        "status-passthrough",
        "refresh-unavailable",
        "direct-spec",
        "multi-spec-brief",
        "defect",
        "ambiguity",
        "alias-equivalence",
        "ready-brief-zero-specs",
        "cross-repo-brief",
        "incoherent-collection",
        "claimed-defect-without-evidence",
        "migration-read-only-plan",
    } <= {case["id"] for case in cases}

    for case in cases:
        fixture_name = case["fixture"]
        if fixture_name.startswith("profile-intake:"):
            continue
        if fixture_name == "evals/files/routing/migration-selection.json":
            selection = json.loads(_fixture_path(fixture_name).read_text())
            parsed, error = engine.validate_migration_selection(selection)
            assert parsed is not None and error is None
            continue
        fixture = _fixture_path(fixture_name)
        assert fixture.is_file(), case["id"]
        if "normalized-intake/" in fixture_name or fixture_name.startswith("evals/"):
            parsed, findings = engine.validate_normalized_intake(
                json.loads(fixture.read_text(encoding="utf-8"))
            )
            assert parsed is not None, case["id"]
            assert findings == [], case["id"]
        elif "workspace/target/" in case["fixture"]:
            parsed, findings = engine.parse_workspace_entry(
                json.loads(fixture.read_text(encoding="utf-8"))
            )
            assert parsed is not None, case["id"]
            assert findings == [], case["id"]

        if case["mode"] != "route":
            continue
        route = router.route_intake(router.RoutingSignals(**case["signals"]))
        for field in (
            "artifact",
            "artifact_kind",
            "lifecycle_membership",
            "processor",
            "authority_mode",
            "mutation",
        ):
            assert getattr(route, field) == case[field], (case["id"], field)

    first = json.dumps(matrix, sort_keys=True, separators=(",", ":"))
    second = json.dumps(json.loads(raw), sort_keys=True, separators=(",", ":"))
    assert first == second


def test_route_expectations_cover_no_mutation_and_alias_equivalence() -> None:
    cases = {case["id"]: case for case in json.loads(_MATRIX.read_text())["cases"]}
    for case_id in (
        "direct-light",
        "status-passthrough",
        "refresh-unavailable",
        "ready-brief-zero-specs",
    ):
        assert cases[case_id]["mutation"] == "none"

    alias = cases["alias-equivalence"]
    original = cases[alias["same_as"]]
    for field in (
        "fixture",
        "artifact",
        "artifact_kind",
        "lifecycle_membership",
        "processor",
        "authority_mode",
    ):
        assert alias[field] == original[field], field


def test_eval_allowlist_has_balanced_activation_sets() -> None:
    manifest = tomllib.loads((_PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    assert set(manifest["pack"]["evals"]["skills"]) == set(_EVAL_QUERY_FILES)
    for skill, path in _EVAL_QUERY_FILES.items():
        queries = json.loads(path.read_text(encoding="utf-8"))
        assert sum(item["should_trigger"] is True for item in queries) >= 8, skill
        assert sum(item["should_trigger"] is False for item in queries) >= 8, skill


def test_changed_skill_permissions_are_minimal() -> None:
    for skill, (allowed_tools, boundaries) in _CHANGED_SKILLS.items():
        frontmatter = _frontmatter(_SKILL_BODIES[skill])
        match = re.search(r"^allowed-tools:\s*(.+)$", frontmatter, re.MULTILINE)
        assert match is not None, skill
        assert match.group(1) == allowed_tools, skill
        assert _boundaries(frontmatter) == boundaries, skill


def test_installed_agents_guidance_has_no_dangling_relative_links() -> None:
    """Every relative link in the composed root guidance ships with core."""
    body = (_SEEDS / "AGENTS.md").read_text(encoding="utf-8")
    footer = (_SEEDS / "_agents-footer.md").read_text(encoding="utf-8")
    relative_links = {
        target.split("#", 1)[0]
        for target in re.findall(r"\]\(([^)]+)\)", body + footer)
        if not target.startswith(("#", "http://", "https://"))
    }
    # The seed no longer links the architecture overview: that section is
    # conditional, and the seed tells adopters to delete the file when it would
    # duplicate a source they already have. Core still ships it.
    assert relative_links == {"docs/CONVENTIONS.md"}
    assert (_SEEDS / "docs" / "architecture" / "overview.md").is_file()
    assert (_SEEDS / "docs" / "CONVENTIONS.md").is_file()


# STUB: AC19
def test_ac19_integrated_matrix_covers_routes_lifecycle_and_near_misses() -> None:
    cases = {case["id"]: case for case in json.loads(_MATRIX.read_text())[
        "cases"
    ]}
    required = {
        "cross-repo-brief",
        "incoherent-collection",
        "remember-repo-origin",
        "status-triage",
        "refresh-draft",
        "refresh-implementing",
        "refresh-shipped",
        "migration-read-only-plan",
    }
    assert required <= cases.keys()
    for case in cases.values():
        assert {
            "dispatchable",
            "next_action",
            "authority_mode",
            "mutation",
        } <= case.keys()


# STUB: AC19
def test_ac19_migration_matrix_row_invokes_only_the_read_only_planner() -> None:
    cases = {case["id"]: case for case in json.loads(_MATRIX.read_text())[
        "cases"
    ]}
    migration = cases["migration-read-only-plan"]
    assert migration["mutation"] == "none"
    assert migration["dispatchable"] is False
    assert migration["next_action"] == "review-migration-plan"
