from __future__ import annotations

import tomllib
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
APM = PACK_ROOT / ".apm"

SUPPORTING_SKILLS = (
    "build-outline",
    "source-map",
    "identify-perspectives",
    "compare-hypotheses",
    "decision-archaeology",
)
NON_GATE_PROJECT_SKILLS = (
    "desk-research-project-start",
    "desk-research-project-digest",
    "desk-research-project-check",
    "desk-research-project-status",
)
RETRIEVAL_AGENTS = ("evidence-retriever.md", "source-extractor.md")
RETRIEVER_SCRIPTS = ("arxiv-retriever.py", "perplexity-retriever.py")
DIRECT_OPERATIONS = (
    "project-knowledge --capture",
    "project-knowledge --distill",
    "project-knowledge --enquire",
)


def test_optional_core_handoff_has_exact_consumers_and_no_dependency() -> None:
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))
    integrations = {item["id"]: item for item in manifest["pack"]["integrations"]}
    handoff = integrations["project-knowledge-research-handoff"]

    assert handoff["pack"] == "core"
    assert handoff["kind"] == "handoff"
    assert handoff["consumers"] == [
        "skill:desk-research",
        "skill:desk-research-project-synthesize",
        "skill:devils-advocate",
    ]
    assert handoff["providers"] == ["skill:project-knowledge"]
    assert "exact terminal gate" in handoff["when"]
    assert "bounded CQ-REVIEW" in handoff["when"]
    assert "typed capture" in handoff["purpose"]
    assert "receipt-scoped distillation" in handoff["purpose"]
    assert "untrusted candidate checks" in handoff["purpose"]
    assert "project-knowledge unavailable" in handoff["fallback"]
    assert "without fallback persistence" in handoff["fallback"]

    required = manifest["pack"].get("dependencies", {}).get("required", [])
    assert all(item.get("pack") != "core" for item in required)


def test_supporting_research_primitives_never_call_project_knowledge() -> None:
    paths: list[Path] = []
    for name in SUPPORTING_SKILLS:
        paths.append(APM / "skills" / name / "SKILL.md")
    for name in RETRIEVAL_AGENTS:
        paths.append(APM / "agents" / name)
    for name in RETRIEVER_SCRIPTS:
        paths.append(APM / "skills" / "desk-research" / "scripts" / name)

    for path in paths:
        text = path.read_text(encoding="utf-8")
        for operation in DIRECT_OPERATIONS:
            assert operation not in text, f"{path} must not call {operation}"


def test_project_non_gates_are_explicit_and_operation_free() -> None:
    for name in NON_GATE_PROJECT_SKILLS:
        path = APM / "skills" / name / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        assert "## Project-knowledge non-gate" in text
        section = text.split("## Project-knowledge non-gate", 1)[1]
        assert "no capture, distillation, or enquiry" in " ".join(section.split())
        for operation in DIRECT_OPERATIONS:
            assert operation not in section


def test_all_six_adapters_remain_declared_without_new_runtime_dependency() -> None:
    manifest = tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))

    assert manifest["pack"]["install"]["allowed-adapters"] == [
        "claude-code",
        "kiro-ide",
        "codex",
        "copilot",
        "cursor",
        "gemini",
    ]
    assert "dependencies" not in manifest["pack"]
