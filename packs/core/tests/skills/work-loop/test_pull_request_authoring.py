"""Contract tests for the shipped pull-request template and authoring reference.

Scope note the criteria depend on: the content pins below catch **deletion** of
a required element. They do not certify its wording, and a green run is not
evidence that the prose is good — only that it is still there. The template's
and the reference's wording, and the Finish item's instruction, are living
design corrected in place without an amendment.
"""

from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop"
TEMPLATE = SKILL / "assets" / "pull-request-template.md"
REFERENCE = SKILL / "references" / "pr-authoring.md"
SKILL_MD = SKILL / "SKILL.md"
SUPERVISOR = SKILL / "references" / "supervisor-mode.md"

EXPECTED_HEADINGS = [
    "What does this change?",
    "Why?",
    "Review focus",
    "How do I verify it?",
    "What did you not change that you considered?",
]
DESTINATIONS = {
    ".github/pull_request_template.md",
    ".gitlab/merge_request_templates/Default.md",
}
TASK_LIST_MARKER = re.compile(r"^\s*- \[[ x]\]", re.M)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _preamble(text: str) -> str:
    """The region above the first rendered heading, where the bans live."""
    first = text.index("\n## ")
    return text[:first]


# ---------------------------------------------------------------- AC-0001..4

def test_the_template_exists():
    assert TEMPLATE.is_file()


def test_the_templates_headings_are_the_five_sections_in_order():
    found = re.findall(r"^## (.+)$", _read(TEMPLATE), re.M)
    assert found == EXPECTED_HEADINGS


def test_the_template_carries_no_task_list_marker():
    assert not TASK_LIST_MARKER.search(_read(TEMPLATE))


def test_the_templates_install_block_names_both_destinations():
    install = _read(TEMPLATE).split("Install:", 1)[1].split("\n\n", 1)[0]
    for destination in DESTINATIONS:
        assert destination in install, destination


# ------------------------------------------------------------------- AC-0005

def _candidate_paths(text: str) -> set[str]:
    """The criterion's extraction grammar, stated once and applied to both files.

    Blind spot, named rather than implied: a path written in bare prose without
    a code span and outside a fence is not extracted.
    """
    candidates = set(re.findall(r"`([^`\n]+)`", text))
    for block in re.findall(r"```[a-z]*\n(.*?)```", text, re.S):
        candidates |= set(block.split())
    return {
        c for c in candidates
        if "/" in c and not any(ch.isspace() for ch in c)
        and "<" not in c and ">" not in c
    }


def test_shipped_prose_cites_no_path_that_exists_only_in_this_repository():
    repo_root = PACK_ROOT.parents[1]
    for path in (TEMPLATE, REFERENCE):
        for candidate in sorted(_candidate_paths(_read(path))):
            if candidate in DESTINATIONS:
                continue
            target = repo_root / candidate
            assert not (target.exists() or target.is_symlink()), (
                f"{path.name}: {candidate!r} resolves in this repository"
            )


# ---------------------------------------------------------------- AC-0006..7

def test_the_reference_exists():
    assert REFERENCE.is_file()


def test_the_reference_carries_exactly_two_worked_bodies():
    fences = re.findall(r"```[a-z]*\n(.*?)```", _read(REFERENCE), re.S)
    worked = [f for f in fences if "## What does this change?" in f]
    assert len(worked) == 2


def test_exactly_one_worked_body_omits_review_focus():
    fences = re.findall(r"```[a-z]*\n(.*?)```", _read(REFERENCE), re.S)
    worked = [f for f in fences if "## What does this change?" in f]
    assert sum("## Review focus" not in f for f in worked) == 1


# ------------------------------------------------------------------- AC-0008

def test_exactly_one_routing_row_targets_the_reference_under_its_predicate():
    rows = [
        r for r in re.findall(r"^\|(.+?)\|(.+?)\|\s*$", _read(SKILL_MD), re.M)
        if "pr-authoring.md" in r[1]
    ]
    assert len(rows) == 1
    assert " ".join(rows[0][0].split()) == "Authoring a pull-request body"
    targets = re.findall(r"\]\(([^)]+)\)", rows[0][1])
    assert targets == ["references/pr-authoring.md"]


# ------------------------------------------------------------------- AC-0010

def test_the_standard_template_sentence_links_to_the_asset():
    sentence = next(
        line for line in _read(SUPERVISOR).splitlines()
        if "standard template" in line
    )
    assert "](../assets/pull-request-template.md)" in sentence


# --------------------------------------------------- deletion pins (no AC)

def test_the_template_still_states_its_three_prohibitions():
    """Deletion pin. Catches removal; does not certify wording."""
    preamble = _preamble(_read(TEMPLATE))
    for fragment in (
        "no round counts",
        "no findings tallies",
        "a result is evidence",
        "The reviewer has it",
    ):
        assert fragment.lower() in preamble.lower(), fragment


def test_the_template_still_states_the_keep_your_own_convention_clause():
    """Deletion pin. Catches removal; does not certify wording."""
    assert "keep it and delete this file" in _preamble(_read(TEMPLATE))


def test_the_template_still_states_its_line_budget_as_a_convention():
    """Deletion pin. Catches removal; does not certify wording."""
    preamble = _preamble(_read(TEMPLATE))
    assert re.search(r"Budget:\s*\d+ lines", preamble), "no numeric budget"
    assert "house convention" in preamble


def test_every_template_section_still_carries_a_non_rendering_comment():
    """Deletion pin. Catches removal; does not certify wording."""
    body = _read(TEMPLATE)
    for heading in EXPECTED_HEADINGS:
        after = body.split(f"## {heading}\n", 1)[1]
        assert after.lstrip().startswith("<!--"), heading
        comment = after.split("-->", 1)[0]
        # An empty comment satisfies "starts with <!--" while guiding nobody.
        assert len(comment.split()) >= 8, f"{heading}: comment carries no guidance"


def test_the_review_focus_comment_still_carries_its_discriminator():
    """Deletion pin. Catches removal; does not certify wording."""
    block = _read(TEMPLATE).split("## Review focus\n", 1)[1].split("\n## ", 1)[0]
    assert "question about the code" in block
    assert "Not what was hard" in block


def test_the_reference_still_states_seven_writing_rules():
    """Deletion pin over the named section only. Catches removal, not wording."""
    section = _read(REFERENCE).split("## Writing rules\n", 1)[1].split("\n## ", 1)[0]
    rules = re.findall(r"^\d+\. \*\*(.+?)\*\*", section, re.M)
    assert len(rules) == 7
    # Count alone passes after the seven rules are replaced wholesale, so bind
    # each to a distinctive fragment of the rule it guards.
    for fragment in (
        "Lead with the result",
        "Ground every claim",
        "intended work as done",
        "bullets carry independent items",
        "table earns its place",
        "Collapse only the optional",
        "edit once",
    ):
        assert fragment in section, fragment


def test_the_finish_item_still_states_its_probe_and_branches():
    """Deletion pin. Catches removal; does not observe the loop's behavior."""
    item = _read(SKILL_MD).split("- [ ] **Pull request opened", 1)[1]
    item = item.split("\n- [ ]", 1)[0]
    for cue in ("gh api user", "viewerPermission", "WRITE", "MAINTAIN", "ADMIN"):
        assert cue in item, cue
    # Cue words survive the branches being deleted, so bind each branch too.
    for branch in ("exits\n  non-zero", "make no offer", "stay silent", "offer to open"):
        assert re.search(branch, item), branch


def test_the_finish_item_decides_from_exit_status_not_from_message_text():
    """A presence pin cannot establish an absence; this is the absence half.

    Comparing the documented `viewerPermission` enum is required and therefore
    permitted. What is forbidden is deciding from prose a blocked credential
    store can forge.
    """
    item = _read(SKILL_MD).split("- [ ] **Pull request opened", 1)[1]
    item = item.split("\n- [ ]", 1)[0]
    decisive = item.split("A blocked", 1)[0]
    assert "gh auth status" not in decisive
