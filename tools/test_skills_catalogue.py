"""Tests for tools/skills_catalogue.py and the pages it feeds."""
from __future__ import annotations

import importlib.util
import re
import sys
import tomllib
from pathlib import Path

import pytest

TOOLS = Path(__file__).parent
REPO = TOOLS.parent
_spec = importlib.util.spec_from_file_location("skills_catalogue", TOOLS / "skills_catalogue.py")
assert _spec and _spec.loader
sc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = sc
_spec.loader.exec_module(sc)


def _skill(root: Path, pack: str, name: str, extra: str = "") -> None:
    d = root / "packs" / pack / ".apm" / "skills" / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: x\n{extra}---\nbody\n")


def _entry(job: str = "Build it") -> str:
    return f'job = "{job}"\nwant = "w"\nask = "a"\ngets = "g"\n'


@pytest.fixture()
def tree(tmp_path: Path) -> Path:
    _skill(tmp_path, "alpha", "do-it")
    _skill(tmp_path, "alpha", "do-more")
    _skill(tmp_path, "alpha", "lens-reference", "metadata:\n  generated-by: compile-okf 1\n")
    _skill(tmp_path, "_hidden", "fixture")
    cat = tmp_path / "docs-site" / "src"
    cat.mkdir(parents=True)
    (cat / "skills-catalogue.toml").write_text(
        f"[skills.do-it]\n{_entry()}\n[skills.do-more]\n{_entry('Ship it')}"
    )
    return tmp_path


def _write(tree: Path, body: str) -> None:
    (tree / "docs-site" / "src" / "skills-catalogue.toml").write_text(body)


def test_internal_and_underscore_packs_are_not_user_invocable(tree: Path) -> None:
    public, internal = sc.discover_skills(tree / "packs")
    assert public == {"do-it": "alpha", "do-more": "alpha"}
    assert internal == {"lens-reference"}


def test_page_lists_each_skill_once_and_never_internal(tree: Path) -> None:
    page = sc.build(tree)
    assert page.count("| a |") == 2
    assert "lens-reference" not in page and "fixture" not in page
    assert page.index("## Build it") < page.index("## Ship it")


def test_output_is_deterministic(tree: Path) -> None:
    assert sc.build(tree) == sc.build(tree)


def test_missing_row_fails_and_names_the_skill(tree: Path) -> None:
    _write(tree, f"[skills.do-it]\n{_entry()}")
    assert any(p.startswith("do-more:") for p in sc.check(tree))
    with pytest.raises(ValueError, match="do-more"):
        sc.build(tree)


@pytest.mark.parametrize("field", sc.FIELDS)
def test_empty_field_fails(tree: Path, field: str) -> None:
    body = (tree / "docs-site/src/skills-catalogue.toml").read_text()
    _write(tree, re.sub(rf'^{field} = ".*"$', f'{field} = ""', body, count=1, flags=re.M))
    assert any(f"do-it: empty {field}" in p for p in sc.check(tree))


def test_stale_and_internal_entries_fail(tree: Path) -> None:
    body = (tree / "docs-site/src/skills-catalogue.toml").read_text()
    _write(tree, body + f"\n[skills.gone]\n{_entry()}\n[skills.lens-reference]\n{_entry()}")
    problems = sc.check(tree)
    assert any(p.startswith("gone:") for p in problems)
    assert any(p.startswith("lens-reference:") for p in problems)


def test_unknown_job_fails(tree: Path) -> None:
    _write(tree, f"[skills.do-it]\n{_entry('Elsewhere')}\n[skills.do-more]\n{_entry()}")
    assert any("unknown job" in p for p in sc.check(tree))


def test_stale_generated_page_fails(tree: Path) -> None:
    target = tree / "docs-site/src/content/docs/packs/skills.md"
    target.parent.mkdir(parents=True)
    target.write_text("old")
    assert any("out of date" in p for p in sc.check(tree))
    target.write_text(sc.build(tree))
    assert sc.check(tree) == []


def test_real_tree_is_complete_and_hides_the_compile_okf_skills() -> None:
    page = sc.build(REPO)  # raises on any input problem
    _, internal = sc.discover_skills(REPO / "packs")
    assert {"ase-okf-reference", "architecture-lenses-reference", "security-checklists-reference"} <= internal
    assert not any(f"`{n}`" in page for n in internal)
    assert "architecture-lenses-reference" not in (REPO / "packs/architect/README.md").read_text()


def test_packs_page_lists_every_active_pack_once() -> None:
    page = (REPO / "docs-site/src/packs-page.md").read_text()
    active = []
    for toml in sorted((REPO / "packs").glob("*/pack.toml")):
        pack = toml.parent.name
        meta = tomllib.loads(toml.read_text())["pack"]
        if not pack.startswith("_") and not meta["description"].startswith("Deprecated"):
            active.append(pack)
    for pack in active:
        assert len(re.findall(rf"\]\(/agent-ready-repo/docs/packs/{re.escape(pack)}/\)", page)) == 1, pack
    assert "packs/skills/" in page


def test_page_header_and_lead_sentences(tree: Path) -> None:
    page = sc.build(tree)
    assert "| I want to | Example ask | You get | Pack |" in page
    assert "Say this" not in page
    assert "grouped by job" in page and "A to Z by skill name" in page
    assert "Any wording that states your job works" in page


def _three(tree: Path, order: list[tuple[str, str]]) -> list[str]:
    """Write three Build it skills in the given (name, sequence) order; return problems."""
    if not (tree / "packs/alpha/.apm/skills/zeta").exists():
        _skill(tree, "alpha", "zeta")
    body = "".join(
        f"[skills.{n}]\njob = \"Build it\"\n" + (f'sequence = "{s}"\n' if s else "") + 'want = "w"\nask = "a"\ngets = "g"\n\n'
        for n, s in order
    )
    _write(tree, body + f"[skills.do-more]\n{_entry('Ship it')}")
    return sc.check(tree)


def test_rows_without_a_sequence_must_be_a_to_z(tree: Path) -> None:
    assert _three(tree, [("do-it", ""), ("zeta", "")]) == []
    assert any("not A to Z" in p for p in _three(tree, [("zeta", ""), ("do-it", "")]))


def test_sequences_come_first_and_stay_together(tree: Path) -> None:
    assert _three(tree, [("zeta", "s"), ("do-it", "s")]) == []
    assert any("must come before" in p for p in _three(tree, [("do-it", ""), ("zeta", "s")]))


def test_sequence_steps_restart_for_each_sequence(tree: Path) -> None:
    _three(tree, [("zeta", "s"), ("do-it", "s")])
    page = sc.build(tree)
    assert "Step 1 of 2: w" in page and "Step 2 of 2: w" in page


def test_real_catalogue_rows_follow_the_stated_order() -> None:
    entries = sc.load_entries(sc.CATALOGUE_TOML)
    assert sc._order_errors(entries) == []
    for job in sc.JOBS:
        plain = [n for n, e in entries.items() if e["job"] == job and not e.get("sequence")]
        assert plain == sorted(plain), job


def _exclude(tree: Path, extra: str) -> None:
    body = (tree / "docs-site/src/skills-catalogue.toml").read_text()
    _write(tree, body + "\n" + extra)


def test_excluded_skill_is_skipped_and_needs_no_row(tree: Path) -> None:
    _skill(tree, "alpha", "old-name")
    _exclude(tree, '[exclude.old-name]\nreason = "Deprecated alias."\n')
    assert sc.check(tree) == []
    assert "old-name" not in sc.build(tree)


def test_empty_exclusion_reason_fails(tree: Path) -> None:
    _skill(tree, "alpha", "old-name")
    _exclude(tree, '[exclude.old-name]\nreason = " "\n')
    assert any(p.startswith("old-name: empty exclusion reason") for p in sc.check(tree))


def test_stale_exclusion_fails(tree: Path) -> None:
    _exclude(tree, '[exclude.gone]\nreason = "r"\n')
    assert any(p.startswith("gone: stale exclusion") for p in sc.check(tree))


def test_excluded_skill_with_a_row_fails(tree: Path) -> None:
    _exclude(tree, '[exclude.do-it]\nreason = "r"\n')
    assert any("do-it: excluded skill must not have a row" in p for p in sc.check(tree))


def test_excluded_skill_named_in_page_text_fails(tree: Path) -> None:
    _skill(tree, "alpha", "old-name")
    _exclude(tree, '[exclude.old-name]\nreason = "r"\n')
    body = (tree / "docs-site/src/skills-catalogue.toml").read_text()
    _write(tree, body.replace('ask = "a"', 'ask = "Use old-name."', 1))
    assert any("old-name: excluded skill appears in the page" in p for p in sc.check(tree))


def test_real_tree_excludes_five_skills_and_row_count_follows() -> None:
    page = sc.build(REPO)
    public, internal = sc.discover_skills(REPO / "packs")
    excluded = sc.load_exclusions(sc.CATALOGUE_TOML)
    assert set(excluded) == {
        "operational-safety", "security-checklists", "author-brief", "receive-brief", "new-guide"
    }
    assert not any(re.search(rf"(?<![\w-]){n}(?![\w-])", page) for n in excluded)
    rows = [ln for ln in page.splitlines() if re.search(r"\| \[[\w-]+\]\(/agent-ready-repo/docs/packs/", ln)]
    assert len(rows) == len(public) - len(excluded)


def test_empty_term_definition_fails(tree: Path) -> None:
    _exclude(tree, '[terms]\nspec = " "\n')
    assert any(p.startswith("spec: empty term definition") for p in sc.check(tree))


def test_terms_print_under_the_intro(tree: Path) -> None:
    body = (tree / "docs-site/src/skills-catalogue.toml").read_text()
    _write(tree, '[terms]\nspec = "A written plan."\n\n' + body)
    page = sc.build(tree)
    assert "- **spec**: A written plan." in page
    assert page.index("install that pack first") < page.index("- **spec**") < page.index("## Build it")


def test_real_tree_defines_the_required_terms() -> None:
    terms = sc.load_terms(sc.CATALOGUE_TOML)
    assert {"intent", "spec", "brief", "ADR", "RFC", "bet", "contract", "pack"} <= set(terms)
    assert all(text.strip() for text in terms.values())


def test_real_tree_moved_rows_and_research_project_sequence() -> None:
    entries = sc.load_entries(sc.CATALOGUE_TOML)
    job = "Build and curate a catalogue"
    assert sc.JOBS.index(job) == sc.JOBS.index("Ship it") + 1 == sc.JOBS.index("Any stage") - 1
    in_job = {n for n, e in entries.items() if e["job"] == job}
    assert in_job == {
        "assimilate-primitive", "assimilate-repo", "propose-catalogue-pack",
        "author-or-update-agent-skill", "review-or-optimize-agent-skill", "compile-okf",
    }
    for n in ("new-adr", "new-rfc", "navigate-decisions", "navigate-intents", "work-intake"):
        assert entries[n]["job"] == "Build it", n
    for n in ("github-brief-intake", "jira-brief-intake", "jira-align-brief-intake", "linear-brief-intake"):
        assert entries[n]["job"] == "Set up a repository", n
    names = list(entries)
    assert entries["desk-research-project-status"]["sequence"] == "research project"
    assert names.index("desk-research-project-status") == names.index("desk-research-project-start") + 1
