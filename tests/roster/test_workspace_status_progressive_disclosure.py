"""workspace-status ships as a dispatcher, not as one long body.

Roster-owned rather than pack-owned: three of these assertions read outside
`packs/core` — the backend source for the subcommand set, the prune source for
the refusal codes, and `.github/workflows/build-check.yml` plus `tests/AGENTS.md`
for the roster-placement claim. `tools/lint-pack-test-boundary.py` forbids a
pack test from reaching above its own pack.

Two expected sets are derived from the artifact under test at run time: the
backend's subcommand list and the prune source's refusal codes. A hard-coded
copy of either stays green after the source grows a ninth subcommand or a
fifteenth code, which is the regression those checks exist to catch. The
remaining enumerations — the reference filenames, the mode names, the stale
phrases, the backend digests — are deliberately fixed, because each is a term
of the contract rather than a fact about the tree, and deriving it would make
the check agree with whatever the tree currently holds.

Presence assertions run against comment-stripped text. A Markdown comment is
inert to the agent reading the skill, so a rule that survives only inside one
has been deleted in every sense that matters here.
"""

from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

import pytest
import yaml

_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "packs/core/.apm/skills/workspace-status"
SKILL = SKILL_DIR / "SKILL.md"
SCRIPTS = SKILL_DIR / "scripts"

REFERENCES = ("reconcile.md", "explain.md", "mutate.md")
MODES = ("status", "reconcile", "explain", "mutate")

# AC-0001. The linter warns above 500 body lines and errors above 1000; this
# holds the skill at the warning threshold rather than at the error one.
BODY_LINE_CEILING = 500

# AC-0008. Recorded at base commit 8ef829ab7947d7212dd814aa64af69fcfec6e764.
# This delivery moves prose; it changes no backend behaviour.
BACKEND_DIGESTS = {
    "workspace_status.py":
        "b07efea9132f1ddfeab8ce81554c65633d8fac3f5065fdeba31e40a0ef6d7484",
    "workspace_status_engine.py":
        "68c16e98439c24a7e50f10ef4eb9d9c60f3e0594367a2492f479755c93ca91f3",
    "workspace_status_prune.py":
        "65076e175c821f2818dfcf5ea762df3d6b9f29334216948e3aac502e2a6c0f98",
    "workspace_mcp_server.py":
        "c2b252f55c99d54558b253e3c14aa40a5feec5bbcaad1340154e57e3d2c03199",
}


def _skill_text() -> str:
    """The skill body with Markdown comments removed.

    A commented-out route or consent rule is not guidance an agent follows, so
    it must not satisfy a presence assertion either.
    """
    return _COMMENT.sub("", SKILL.read_text(encoding="utf-8"))


def _raw_skill_text() -> str:
    """The body exactly as written, for assertions about absence."""
    return SKILL.read_text(encoding="utf-8")


def _body_lines(text: str) -> list[str]:
    """Lines after the closing frontmatter delimiter, as CAT-S003 counts them."""
    lines = text.split("\n")
    closing = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    return lines[closing + 1:]


def _section(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin:text.index(end, begin)]


def test_ac0001_body_stays_under_the_dispatcher_ceiling() -> None:
    """AC-0001: the body is at most 500 lines."""
    count = len(_body_lines(_skill_text()))
    assert count <= BODY_LINE_CEILING, (
        f"SKILL.md body is {count} lines, above the {BODY_LINE_CEILING}-line "
        "ceiling. Move a section into references/ rather than raising this."
    )


@pytest.mark.parametrize("name", REFERENCES)
def test_ac0002_each_reference_file_exists(name: str) -> None:
    """AC-0002: the three mode references exist."""
    assert (SKILL_DIR / "references" / name).is_file()


@pytest.mark.parametrize("name", REFERENCES)
def test_ac0003_each_reference_is_linked_from_the_body(name: str) -> None:
    """AC-0003: the body routes to each reference by its skill-relative path.

    Separate from AC-0002 because a citation to a file nobody wrote passes a
    linkage check on its own, and a file nobody cites is dead weight.
    """
    assert f"references/{name}" in _skill_text()


def test_ac0004_every_backend_subcommand_maps_to_exactly_one_mode() -> None:
    """AC-0004: the mode table maps every subcommand the backend accepts.

    Scoped to the mode-selection section and asserted per row. A whole-file
    presence check passes when a subcommand is named under the wrong mode,
    which is the defect worth catching: the table's job is the mapping, not
    the vocabulary.
    """
    source = (SCRIPTS / "workspace_status.py").read_text(encoding="utf-8")
    literal = re.search(r"_SUBCOMMANDS = frozenset\((\{.*?\})\)", source, re.S)
    assert literal is not None, "the _SUBCOMMANDS literal moved; this check is blind"
    subcommands = ast.literal_eval(literal.group(1))
    assert subcommands, "no subcommands parsed"

    section = _section(_skill_text(), "## Mode selection", "## Invocation contract")
    rows = [line for line in section.split("\n") if line.startswith("|")]

    unmapped = []
    for subcommand in sorted(subcommands):
        owning = {
            row.split("|")[1].strip()
            for row in rows
            if f"`{subcommand}" in row and row.split("|")[1].strip() in MODES
        }
        if len(owning) != 1:
            unmapped.append((subcommand, sorted(owning)))
    assert unmapped == [], f"subcommands not mapped to exactly one mode: {unmapped}"


def test_ac0005_is_owned_by_the_prune_closure_suite() -> None:
    """AC-0005 has one owner, and it is not this file.

    `tests/roster/test_two_sided_prune_closure_invariant.py` already derives the
    emitted refusal codes from the prune source, finds the anchor, slices the
    documented list and asserts closure. Re-implementing that here would give
    one criterion two homes whose extraction logic can drift apart, so this
    asserts only that the owning control still points at the file the content
    moved into.
    """
    owner = (
        ROOT / "tests/roster/test_two_sided_prune_closure_invariant.py"
    ).read_text(encoding="utf-8")
    assert "workspace-status/references/mutate.md" in owner, (
        "the refusal-code control no longer names references/mutate.md; "
        "AC-0005 may have lost its owner"
    )


def test_ac0006_the_initialisation_template_is_an_asset() -> None:
    """AC-0006: the template ships as a file the skill writes out."""
    asset = SKILL_DIR / "assets/workspace.toml.template"
    assert asset.is_file()
    content = asset.read_text(encoding="utf-8")
    assert content.startswith("# workspace.toml"), "the asset is not the template"
    assert "[backlog]" in content, "the asset is truncated"


def test_ac0007_the_body_cites_the_template_instead_of_inlining_it() -> None:
    """AC-0007: the body points at the asset and no longer carries its text.

    Separate from AC-0006 because copying the block out and forgetting to
    delete the original leaves both halves green under one combined assertion.
    """
    assert "assets/workspace.toml.template" in _skill_text()
    # Absence is checked against the raw body: text hidden in a comment still
    # ships, so stripping comments first would excuse the very thing this
    # assertion exists to catch. Two distinctive lines rather than one, so a
    # partial re-inlining is caught too.
    raw = _raw_skill_text()
    asset = (SKILL_DIR / "assets/workspace.toml.template").read_text(encoding="utf-8")
    inlined = [
        line for line in asset.splitlines()
        if len(line) > 40 and line in raw
    ]
    assert inlined == [], f"template content is still inlined in the body: {inlined[:3]}"


@pytest.mark.parametrize("name,digest", sorted(BACKEND_DIGESTS.items()))
def test_ac0008_backend_scripts_are_unchanged(name: str, digest: str) -> None:
    """AC-0008: this delivery moves prose and touches no backend behaviour."""
    actual = hashlib.sha256((SCRIPTS / name).read_bytes()).hexdigest()
    assert actual == digest, (
        f"{name} changed. This spec's contract is that the backend does not move; "
        "if a later change edits it deliberately, that change owns updating this."
    )


def _roster_steps_are_guarded() -> bool:
    """Whether every gate-main step running a roster path carries an `if:` guard.

    Derived rather than assumed: AC-0009 constrains the guidance only while the
    workflow actually behaves this way, so removing the guards later must
    change what this check demands.
    """
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/build-check.yml").read_text(encoding="utf-8")
    )
    steps = workflow["jobs"]["gate-main"]["steps"]
    roster = [
        step for step in steps
        if isinstance(step.get("run"), str) and "tests/roster/" in step["run"]
    ]
    return bool(roster) and all("if" in step for step in roster)


def _placement_section() -> str:
    text = (ROOT / "tests/AGENTS.md").read_text(encoding="utf-8")
    return _section(text, "## Roster steps are named and placed by hand",
                    "## Essential commands")


def test_ac0009_placement_guidance_does_not_claim_a_later_step_is_skipped() -> None:
    """AC-0009: the guidance agrees with how gate-main actually runs."""
    if not _roster_steps_are_guarded():
        pytest.skip("gate-main roster steps are no longer guarded; AC-0009 is inert")

    section = _placement_section()
    for stale in ("fail-fast", "never runs"):
        assert stale not in section, (
            f"tests/AGENTS.md still says {stale!r}, but every gate-main roster step "
            "carries an `if:` guard, so a step below the bulk step does run."
        )


def test_the_placement_instruction_and_its_reason_survive() -> None:
    """Content pin, not a criterion.

    Correcting the false claim in AC-0009 is one edit away from deleting the
    true instruction sitting in the same sentence. Nothing else notices that.
    """
    section = _placement_section()
    assert "**above**" in section and "that bulk step" in section
    assert "attribution" in section


def test_the_body_keeps_the_mutation_consent_rule_always_loaded() -> None:
    """Content pin, not a criterion.

    The mutating flow's depth lives in references/mutate.md, which loads only
    once the agent has routed to it. A consent rule that arrives at that point
    is guarding a decision already taken, so the rule itself stays in the body.
    """
    never = _section(_skill_text(), "## Never", "## Conditional references")
    assert "references/mutate.md" in never
    for subcommand in ("prune", "repair-apply", "repair-rollback"):
        assert f"`{subcommand}`" in never, f"{subcommand} is not named in Never"
    assert "confirmation" in never.lower()


def test_shipped_reference_and_asset_content_stays_portable() -> None:
    """Content pin, not a criterion.

    Shipped pack content may not cite this catalogue's internal records. The
    pattern is the one the pack's maintainer guidance defines.
    """
    internal = re.compile(
        r"\b(?:RFC|ADR)-0[0-9]{3}\b"
        r"|\bAC-?[0-9]+[a-z]?(?:\([a-z]\))?\b"
        r"|docs/(?:specs|rfc|adr|contracts)/[a-z0-9]"
    )
    shipped = [SKILL_DIR / "references" / name for name in REFERENCES]
    shipped.append(SKILL_DIR / "assets/workspace.toml.template")

    offenders = {
        path.name: sorted(set(internal.findall(path.read_text(encoding="utf-8"))))
        for path in shipped
        if internal.search(path.read_text(encoding="utf-8"))
    }
    assert offenders == {}, f"internal-governance citations in shipped content: {offenders}"
