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
    "author-delivery-brief": (_SKILLS / "author-delivery-brief" / "SKILL.md").read_text(encoding="utf-8"),
    "author-brief": (_SKILLS / "author-brief" / "SKILL.md").read_text(encoding="utf-8"),
    "receive-brief": (_SKILLS / "receive-brief" / "SKILL.md").read_text(encoding="utf-8"),
    "new-spec": (_SKILLS / "new-spec" / "SKILL.md").read_text(encoding="utf-8"),
    "workspace-status": (_SKILLS / "workspace-status" / "SKILL.md").read_text(encoding="utf-8"),
    "work-loop": (_SKILLS / "work-loop" / "SKILL.md").read_text(encoding="utf-8"),
    "explain-diff": (_SKILLS / "explain-diff" / "SKILL.md").read_text(encoding="utf-8"),
}
_EXPLAIN_DIFF_EVALS = _SKILLS / "explain-diff" / "evals" / "evals.json"
_EXPLAIN_DIFF_REFERENCES = _SKILLS / "explain-diff" / "references"
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
    "close-work": _SKILLS / "close-work" / "evals" / "eval_queries.json",
    "explain-diff": _SKILLS / "explain-diff" / "evals" / "eval_queries.json",
    "navigate-intents": _SKILLS / "navigate-intents" / "evals" / "eval_queries.json",
    "repository-exploration": _SKILLS / "repository-exploration" / "evals" / "eval_queries.json",
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
    "intake-intent": ("Read Write Edit Agent", {"filesystem_write", "filesystem_read_untrusted"}),
    "author-delivery-brief": ("Read Write Edit Agent", {"filesystem_write", "filesystem_read_untrusted"}),
    "author-brief": ("Read", set()),
    "receive-brief": ("Read", set()),
    "new-spec": (
        "Read Write Edit Bash WebFetch WebSearch Agent",
        {"filesystem_write", "filesystem_read_untrusted", "network_fetch"},
    ),
    "workspace-status": ("Read Write Edit Bash", {"filesystem_write", "filesystem_read_untrusted"}),
    "work-loop": (
        "Read Write Edit Bash Agent",
        {"filesystem_write", "filesystem_read_untrusted", "network_fetch"},
    ),
    "explain-diff": ("Read Write Bash", {"filesystem_write", "filesystem_read_untrusted"}),
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


def test_route_expectations_cover_no_mutation() -> None:
    cases = {case["id"]: case for case in json.loads(_MATRIX.read_text())["cases"]}
    for case_id in (
        "direct-light",
        "status-passthrough",
        "refresh-unavailable",
        "ready-brief-zero-specs",
    ):
        assert cases[case_id]["mutation"] == "none"


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


def test_explain_diff_workflow_pins_model_owned_html_contract() -> None:
    body = _SKILL_BODIES["explain-diff"]
    frontmatter = _frontmatter(body)
    assert re.search(r"^allowed-tools:\s*Read Write Bash$", frontmatter, re.MULTILINE)
    assert "version-2" not in body
    assert "archetype" not in body.lower()
    assert "references/html-authoring.md" in body
    assert "scripts/publish_explanation.py" in body
    assert "Name the page's teaching concept" in body
    assert "visual system, and reading sequence" in body
    assert "Author one complete HTML document directly" in body
    assert "reviewer fast path" in body
    assert "repository-relative file" in body
    assert "minimal before/after excerpt or concrete worked behavior" in body
    assert "literal technical thesis before using a metaphor" in body
    assert "No palette, font stack, light/dark mode, density" in body
    assert "fallback font with different metrics" in body
    assert "inline paths wrap without widening" in body
    assert "never color an incorrect or unanswered result as\n   success" in body
    assert "Never treat a sample page, prior output, palette, type stack, or theme" in body
    assert "data-quiz-rationale" in body
    assert "one non-empty `name` that is unique to that question" in body
    assert "session-specific open or inspection result in the handoff" in body
    assert "EXPLAIN_DIFF_CSP" in body
    assert "EXPLAIN_DIFF_RUNTIME" in body
    assert "No package install, network request, external asset, browser runtime, or other\npack is required" in body

    contract = (_EXPLAIN_DIFF_REFERENCES / "html-authoring.md").read_text(encoding="utf-8")
    for required in (
        "Teaching concept",
        "Central visual",
        "data-explain-role=\"background\"",
        "data-explain-role=\"intuition\"",
        "data-explain-role=\"code\"",
        "data-explain-role=\"quiz\"",
        "data-evidence=\"observed\"",
        ":focus-visible",
        "prefers-reduced-motion",
        "fast path near the start",
        "why the difference matters",
        "one dominant analogy",
        "No sample output establishes a cream editorial theme",
        "Do not copy CSS from a previous explainer",
        "Grid and flex children can shrink",
        "Compose for the whole fallback stack",
        "Inline `code`, file paths, and identifiers",
        "Tables keep short headers and labels readable",
        "Quiz feedback is neutral before evaluation",
        "one non-empty name unique to that question",
        "This is an audience\ndecision, not a rule",
        "data-quiz-rationale",
        "purple",
        "gradient",
    ):
        assert required in contract
    assert "Do not include `script`, event-handler attributes" in contract


def test_explain_diff_workflow_evals_cover_model_authored_html_cases() -> None:
    evals = json.loads(_EXPLAIN_DIFF_EVALS.read_text(encoding="utf-8"))["evals"]
    by_id = {case["id"]: case for case in evals}
    expected = {
        "local-diff-model-authored-html-boundary",
        "architecture-boundary-page-uses-component-map",
        "data-flow-page-uses-transformation-path",
        "fail-closed-lifecycle-page-uses-state-story",
        "mixed-audience-reviewer-fast-path",
        "sensitive-literals-are-placeholdered-before-publication",
        "installed-skill-remains-independent",
        "browser-capability-offered-only-after-consent",
        "no-browser-capability-local-open-instructions",
    }
    assert expected <= by_id.keys()

    all_assertions = "\n".join(
        assertion for case in evals for assertion in case["assertions"]
    )
    assert "complete HTML document directly rather than JSON" in all_assertions
    assert "repository-relative files and symbols" in all_assertions
    assert "question-specific teaching rationale" in all_assertions
    assert "default or prior-page theme" in all_assertions
    assert "publish_explanation.py" in all_assertions
    assert "credential-shaped values" in all_assertions
    assert "does NOT reference or require any other pack or skill" in all_assertions
    assert "does NOT claim browser rendering or visual QA happened" in all_assertions

    queries = json.loads(_EVAL_QUERY_FILES["explain-diff"].read_text(encoding="utf-8"))
    false_queries = {item["query"] for item in queries if item["should_trigger"] is False}
    assert "Review this diff for bugs, missing tests, and security issues." in false_queries
    assert "Convert this Markdown guide into HTML." in false_queries
    assert "Build a polished product UI for comparing two code snippets." in false_queries


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
    # `docs/AGENTS.md` is deliberately no longer linked. Naming one scoped file
    # in the lookup read as discharging the obligation for that whole subtree,
    # so a scoped file nested deeper went unread; the lookup now describes the
    # walk instead. It also stops the seed hard-coding a path an adopter
    # repository need not have. Core still ships the file.
    assert relative_links == {
        "AGENT_RULES.md",
        "docs/README.md",
        "docs/CHARTER.md",
        "docs/architecture/README.md",
        "docs/specs/README.md",
        "docs/product/README.md",
        "docs/knowledge/README.md",
    }
    # Every linked target is a seeded file, or the link dangles on install.
    # Spelled out one literal at a time: a computed join reads to
    # `pack-tests-stay-in-pack` as a reach above packs/core, and the set
    # assertion above already fixes exactly which literals belong here.
    assert (_SEEDS / "AGENT_RULES.md").is_file()
    assert (_SEEDS / "docs" / "README.md").is_file()
    assert (_SEEDS / "docs" / "CHARTER.md").is_file()
    assert (_SEEDS / "docs" / "architecture" / "README.md").is_file()
    assert (_SEEDS / "docs" / "specs" / "README.md").is_file()
    assert (_SEEDS / "docs" / "product" / "README.md").is_file()
    assert (_SEEDS / "docs" / "knowledge" / "README.md").is_file()
    assert (_SEEDS / "docs" / "AGENTS.md").is_file()
    assert (_SEEDS / "docs" / "architecture" / "overview.md").is_file()


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
