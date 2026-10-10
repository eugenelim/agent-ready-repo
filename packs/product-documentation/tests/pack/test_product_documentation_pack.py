"""Pack-local contracts for product-documentation."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = PACK_ROOT / ".apm" / "skills" / "author-product-docs"
AUTHOR_SKILL = SKILL_DIR / "SKILL.md"
REFS = SKILL_DIR / "references"
EVALS = SKILL_DIR / "evals"

REPO_SPECIFIC = (
    "agent-ready-repo",
    "guides/<pack>",
    "docs/guides/",
    "web/src/content",
    "docs-site/",
)
SURFACES = (
    "## Library or SDK",
    "## CLI",
    "## HTTP or RPC API",
    "## App (web, desktop, or mobile)",
    "## Service",
    "## Plugin or extension",
    "## Framework or extension points",
    "## Agent-context pack",
)
STAGES = (
    "discover and evaluate",
    "install",
    "first success",
    "daily tasks",
    "look up",
    "understand",
    "troubleshoot",
    "upgrade",
    "contribute",
)
PAGES = (
    "## README",
    "## Quickstart",
    "## Installation guide",
    "## Troubleshooting",
    "## Changelog and release notes",
    "## Migration guide",
    "## Contributing guide",
    "## Docs landing page",
)
SIBLINGS = (
    "information-architecture",
    "journey-mapping",
    "design-review",
    "content-design",
    "ux-writing",
)


@pytest.fixture(scope="module")
def author_skill_body() -> str:
    assert AUTHOR_SKILL.is_file(), f"author-product-docs skill not found at {AUTHOR_SKILL}"
    return AUTHOR_SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pack_toml() -> dict:
    return tomllib.loads((PACK_ROOT / "pack.toml").read_text(encoding="utf-8"))


def test_author_product_docs_skill_exists() -> None:
    assert AUTHOR_SKILL.is_file()


def test_product_documentation_has_no_seeds_dir() -> None:
    assert not (PACK_ROOT / "seeds").exists()


def test_author_skill_declares_portability(author_skill_body: str) -> None:
    assert "This skill is portable" in author_skill_body


def test_author_skill_anti_patterns_state_generic_rule(author_skill_body: str) -> None:
    """The anti-patterns section names the maintainer and user-facing split."""
    lower = author_skill_body.lower()
    start = lower.find("anti-pattern")
    assert start >= 0, "author-product-docs SKILL.md is missing an Anti-patterns section"
    section = lower[start:]
    assert "maintainer" in section
    assert "user-facing" in section


def test_product_documentation_allowed_scopes(pack_toml: dict) -> None:
    install = pack_toml.get("pack", {}).get("install", {})
    assert install.get("allowed-scopes") == ["repo", "user"]


def _read(path: Path) -> str:
    """Return the text of ``path``, failing with a clear message if absent."""
    assert path.is_file(), f"missing {path}"
    return path.read_text(encoding="utf-8")


def _sections(text: str) -> dict[str, str]:
    """Split ``text`` on ``## `` headings into heading line -> body."""
    out: dict[str, str] = {}
    parts = re.split(r"(?m)^(?=## )", text)
    for part in parts:
        if part.startswith("## "):
            head, _, body = part.partition("\n")
            out[head.strip()] = body
    return out


def _description(body: str) -> str:
    """Return the frontmatter ``description:`` value (single or folded line)."""
    lines = body.split("\n")
    assert lines[0].strip() == "---"
    end = lines[1:].index("---") + 1
    front = lines[1:end]
    for i, line in enumerate(front):
        if line.startswith("description:"):
            value = [line[len("description:"):].strip()]
            for extra in front[i + 1:]:
                if extra[:1] in (" ", "\t"):
                    value.append(extra.strip())
                else:
                    break
            return " ".join(value)
    raise AssertionError("no description in frontmatter")


@pytest.fixture(scope="module")
def skill_and_refs_text() -> dict[str, str]:
    """Map each SKILL.md and references/*.md path to its text."""
    files = [AUTHOR_SKILL, *sorted(REFS.glob("*.md"))]
    return {str(f): f.read_text(encoding="utf-8") for f in files}


@pytest.fixture(scope="module")
def eval_files_text() -> dict[str, str]:
    """Map every file under evals/ (recursive) to its text."""
    return {
        str(f): f.read_text(encoding="utf-8", errors="replace")
        for f in sorted(EVALS.rglob("*"))
        if f.is_file()
    }


@pytest.fixture(scope="module")
def queries() -> list[dict]:
    """Parsed evals/eval_queries.json."""
    return json.loads(_read(EVALS / "eval_queries.json"))


@pytest.fixture(scope="module")
def eval_cases() -> list[dict]:
    """Parsed cases from evals/evals.json."""
    return json.loads(_read(EVALS / "evals.json"))["evals"]


def test_skill_and_references_are_repo_neutral(skill_and_refs_text: dict[str, str]) -> None:
    hits = [(p, t) for p, t in skill_and_refs_text.items() for t in REPO_SPECIFIC if t in skill_and_refs_text[p]]
    assert not hits, f"repo-specific strings remain: {hits}"


def test_evals_are_repo_neutral(eval_files_text: dict[str, str]) -> None:
    hits = [(p, t) for p, txt in eval_files_text.items() for t in REPO_SPECIFIC if t in txt]
    assert not hits, f"repo-specific strings remain: {hits}"


@pytest.mark.parametrize("word", ["library", "CLI", "API", "app", "service"])
def test_description_names_surface(author_skill_body: str, word: str) -> None:
    desc = _description(author_skill_body)
    assert re.search(rf"\b{word}s?\b", desc, re.IGNORECASE), f"description lacks {word}"


def test_surface_discovery_sections() -> None:
    sections = _sections(_read(REFS / "surface-discovery.md"))
    assert tuple(sections) == SURFACES
    for head, body in sections.items():
        for label in ("Evidence:", "Canonical sources:", "Reference artifact:", "Verification:"):
            assert label in body, f"{head} lacks {label}"


def test_docs_journey_stage_rows() -> None:
    rows = [
        [c.strip() for c in line.strip().strip("|").split("|")]
        for line in _read(REFS / "docs-journey.md").splitlines()
        if line.startswith("|")
    ]
    for stage in STAGES:
        match = [r for r in rows if r and r[0].lower().strip("* `") == stage]
        assert match, f"no journey row for {stage}"
        assert sum(1 for c in match[0] if c) >= 3, f"{stage} row has under 3 cells"


def test_skill_defines_gap_report(author_skill_body: str) -> None:
    start = author_skill_body.index("### Step 15")
    step15 = author_skill_body[start : author_skill_body.index("### Step 16")]
    paragraphs = [p for p in step15.split("\n\n") if p.strip()]
    audit = [p for p in paragraphs if p.startswith("**Audit mode**")]
    retrofit = [p for p in paragraphs if p.startswith("**Retrofit mode**")]
    assert audit and retrofit, "Step 15 lacks audit or retrofit paragraph"
    assert "one row per journey stage" in audit[0]
    for state in ("covered", "partial", "missing", "not applicable"):
        assert f"`{state}`" in audit[0], f"audit paragraph lacks {state}"
    assert "journey gap report" in retrofit[0]


def test_audit_scopes_per_surface_and_site_navigation(author_skill_body: str) -> None:
    start = author_skill_body.index("### Step 15")
    step15 = author_skill_body[start : author_skill_body.index("### Step 16")]
    assert "one journey gap report per surface or audience" in step15
    assert "site configuration's navigation" in step15
    assert "is the docs index" in step15


def test_untrusted_repository_rule(author_skill_body: str) -> None:
    assert "Never run project code, builds, or installs from an untrusted repository" in author_skill_body
    assert "checked against source only" in author_skill_body


def test_page_contracts_sections() -> None:
    sections = _sections(_read(REFS / "page-contracts.md"))
    for head in PAGES:
        assert head in sections, f"missing {head}"
        for field in (
            "First screen must answer",
            "Required content",
            "Move lower or link out",
            "Anti-patterns to refuse",
        ):
            assert field in sections[head], f"{head} lacks {field}"


def test_sibling_skills_are_conditional(author_skill_body: str) -> None:
    for name in SIBLINGS:
        lines = [ln for ln in author_skill_body.splitlines() if name in ln]
        assert lines, f"SKILL.md does not name {name}"
        for ln in lines:
            assert "if installed" in ln.lower(), f"unconditional mention: {ln}"


def test_trigger_queries_cover_non_pack_surfaces(queries: list[dict]) -> None:
    pos = [q for q in queries if q["should_trigger"]]
    neg = [q for q in queries if not q["should_trigger"]]
    assert len(pos) >= 8 and len(neg) >= 8
    generic = [
        q
        for q in pos
        if re.search(r"\b(CLI|library|API|apps?)\b", q["query"], re.IGNORECASE)
        and not re.search(r"\bpacks?\b", q["query"], re.IGNORECASE)
    ]
    assert len(generic) >= 4


def test_release_notes_query_triggers(queries: list[dict]) -> None:
    match = [q for q in queries if q["query"] == "Write release notes for the 2.0 release"]
    assert match and match[0]["should_trigger"] is True


EVAL_FILES = SKILL_DIR / "evals" / "files"
GENERIC_EVAL_FIXTURES = {
    "cli-readme-audit": {
        "evals/files/cli/README.md": EVAL_FILES / "cli" / "README.md",
    },
    "library-journey-gap-audit": {
        "evals/files/library-docs/README.md": EVAL_FILES / "library-docs" / "README.md",
        "evals/files/library-docs/docs/api.md": EVAL_FILES / "library-docs" / "docs" / "api.md",
        "evals/files/library-docs/docs/faq.md": EVAL_FILES / "library-docs" / "docs" / "faq.md",
    },
}


def test_generic_eval_cases(eval_cases: list[dict]) -> None:
    """AC10: the non-pack cases exist and name fixtures that carry no pack manifest."""
    by_id = {c["id"]: c for c in eval_cases}
    for case_id, fixtures in GENERIC_EVAL_FIXTURES.items():
        assert case_id in by_id, f"missing eval case {case_id}"
        assert sorted(by_id[case_id].get("files", [])) == sorted(fixtures)
        for rel, path in fixtures.items():
            assert path.is_file(), f"{case_id} file missing: {rel}"
            assert "pack.toml" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "needle",
    ["standalone FAQ", "llms.txt", "first runnable action"],
)
def test_content_rules_pinned(skill_and_refs_text: dict[str, str], needle: str) -> None:
    assert any(needle in t for t in skill_and_refs_text.values()), f"no rule mentions {needle}"


@pytest.mark.parametrize("field", ["surface:", "journey stage:"])
def test_documentation_contract_fields(author_skill_body: str, field: str) -> None:
    assert field in author_skill_body
