#!/usr/bin/env python3
"""Pytest coverage for the contract-item alignment checker.

Builds fixture spec directories in a tempdir and runs the checker as a
subprocess against its documented invocation, following the precedent in
`packs/core/tests/skills/author-delivery-brief/test_lint_brief_coverage.py` --
the real entry point, not a synthesised import, so the shipped argument parsing
and stream configuration are exercised.

Every rule gets a green case and a red case. Two of them carry an explicit
mutation proof, because a check that passes on correct input proves nothing
about whether it can fail:

  * `test_task_entry_rule_is_stronger_than_a_mention` is the one that matters.
    The weaker form of rule 5 -- "does this identifier appear anywhere in
    plan.md" -- went green on this repository's own contract while a criterion
    had no implementing bullet. The fixture keeps the identifier in the document
    and removes it only from the task entries, which is the case that separates
    the two forms. Three earlier mutation attempts failed to red: two left the
    identifier inside the scope being checked, and one removed it everywhere so
    the weak form would also have caught it.

  * `test_unlabelled_spec_is_skipped_not_failed` is the adoption case. Without
    it, the commit introducing this checker fails every spec authored before the
    convention existed.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# The pack ships tests under packs/<pack>/tests/ and runtime primitives under
# packs/<pack>/.apm/ — tests are visible in the catalogue and never installed.
_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "new-spec"
CHECKER = _SKILL_DIR / "scripts" / "lint-contract-item-alignment.py"
if not CHECKER.is_file():  # wrong parents[] depth after a move
    raise SystemExit(f"subject not found at {CHECKER} — check the parents[] depth")

SPEC = """\
# Spec: fixture

- **Status:** Draft

## Testing Strategy

- **The first group (AC-0001):** goal-based check.
- **The second group (AC-0002):** TDD.

## Acceptance Criteria

- [ ] **AC-0001.** The first thing holds.
- [ ] **AC-0002.** The second thing holds.
"""

PLAN = """\
# Plan: fixture

### T1: Do the first thing

**Tests:**
- **AC-0001.** Assert the first thing.

**Approach:**
- Write it.

**Done when:** the AC-0001 bullet lands.

### T2: Do the second thing

**Tests:**
- **AC-0002.** Assert the second thing.

**Done when:** the AC-0002 bullet lands.
"""


def _tree(root: Path, spec: str = SPEC, plan: str | None = PLAN) -> Path:
    """Write one fixture spec directory and return the repository root."""
    spec_dir = root / "docs" / "specs" / "fixture"
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text(spec, encoding="utf-8")
    if plan is not None:
        (spec_dir / "plan.md").write_text(plan, encoding="utf-8")
    return root


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root)],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture()
def root():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def test_aligned_contract_has_no_findings(root):
    result = _run(_tree(root))
    assert result.returncode == 0, result.stdout
    assert "0 finding(s)" in result.stdout
    assert "1 spec(s) checked" in result.stdout


def test_unlabelled_spec_is_skipped_not_failed(root):
    """Forward-only adoption: a pre-convention spec is skipped, and says so.

    The count must distinguish skipped from checked. A caller that cannot tell
    them apart reads "0 findings" over a wholly skipped corpus as a clean run.
    """
    spec = SPEC.replace("**AC-0001.** ", "").replace("**AC-0002.** ", "")
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 0, result.stdout
    assert "0 spec(s) checked, 1 skipped as unlabelled" in result.stdout


def test_task_entry_rule_is_stronger_than_a_mention(root):
    """Rule 5's mutation proof, and the reason the rule is scoped to entries.

    AC-0002 stays in the document — in prose under Approach — and leaves every
    task entry. The weak form passes here; this checker must not.
    """
    plan = PLAN.replace("- **AC-0002.** Assert the second thing.", "- Assert the second thing.")
    plan = plan.replace("**Done when:** the AC-0002 bullet lands.", "**Done when:** it lands.")
    plan = plan.replace("### T2: Do the second thing\n", "### T2: Do the second thing\n\n**Approach:**\n- AC-0002 is what this is for.\n")
    assert "AC-0002" in plan, "the mutation must leave the identifier in the document"
    result = _run(_tree(root, plan=plan))
    assert result.returncode == 1, result.stdout
    assert "AC-0002 is named by no task entry" in result.stdout
    assert "mentioned in plan, but not in a task entry" in result.stdout


def test_document_tail_after_the_last_task_is_not_a_task_entry(root):
    """The killing case for rule 5's scope, which the fixture could not reach.

    The last task's body ran to end-of-file, so a criterion named in Rollout, in
    Risks or in the Changelog was credited to that task's entry — the
    mention-anywhere form rule 5 exists to eliminate, reappearing inside rule 5.
    The suite's own fixture plan ended at its last task, so nothing reached it.
    """
    plan = PLAN.replace("- **AC-0002.** Assert the second thing.", "- Assert the second thing.")
    plan = plan.replace("**Done when:** the AC-0002 bullet lands.", "**Done when:** it lands.")
    plan += "\n## Changelog\n\n- 2026-09-11: AC-0002 was discussed here.\n"
    assert "AC-0002" in plan, "the mutation must leave the identifier in the document"
    result = _run(_tree(root, plan=plan))
    assert result.returncode == 1, result.stdout
    assert "AC-0002 is named by no task entry" in result.stdout


def test_a_case_bullet_does_not_truncate_its_own_tests_block(root):
    """A bold-capital bullet is not a field label.

    `ENTRY` stopped at any column-0 bold capital, so a task's Tests block ended
    at its first `**AC-NNNN.**` bullet and every later bullet was invisible.
    """
    plan = PLAN.replace(
        "**Tests:**\n- **AC-0001.** Assert the first thing.",
        "**Tests:**\n- **Some heading.** Prose first.\n- **AC-0001.** Assert the first thing.")
    result = _run(_tree(root, plan=plan))
    assert result.returncode == 0, f"AC-0001 must still be found after a bold bullet:\n{result.stdout}"


def test_partially_labelled_spec_names_the_unlabelled_criterion(root):
    """Rule 1's red case, and the branch `test_unlabelled_spec_is_skipped` inverts.

    Stripping *both* labels exercises the skip path. Stripping one exercises the
    finding, and only this case proves the checker looks at the criteria at all
    rather than keying on the reference side.
    """
    spec = SPEC.replace("**AC-0002.** ", "")
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 1, result.stdout
    assert "criterion carries no identifier" in result.stdout


def test_a_checkbox_outside_the_criteria_section_is_not_a_criterion(root):
    """A spec legitimately carries checkboxes elsewhere.

    Scanning the whole document reported a rollout step as an unlabelled
    criterion and failed a valid spec, which is the inverse of the forward-only
    property the adoption case proves.
    """
    spec = SPEC + "\n## Rollout\n\n- [ ] Announce the change\n"
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 0, result.stdout
    assert "carries no identifier" not in result.stdout


def test_duplicate_identifier_is_a_finding(root):
    spec = SPEC.replace("**AC-0002.** The second", "**AC-0001.** The second")
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 1, result.stdout
    assert "AC-0001 is assigned twice" in result.stdout


def test_unresolved_reference_is_a_finding(root):
    plan = PLAN.replace("- **AC-0002.** Assert", "- **AC-0009.** Assert")
    result = _run(_tree(root, plan=plan))
    assert result.returncode == 1, result.stdout
    assert "AC-0009 resolves to no criterion" in result.stdout


def test_malformed_identifier_is_a_finding(root):
    result = _run(_tree(root, plan=PLAN + "\nSee AC-12 for detail.\n"))
    assert result.returncode == 1, result.stdout
    assert "malformed identifier AC-12" in result.stdout


def test_retired_identifier_may_not_be_reused(root):
    spec = SPEC + "\n## Retired identifiers\n\n- AC-0002\n"
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 1, result.stdout
    assert "AC-0002 is retired and must not be reused" in result.stdout


def test_a_correctly_retired_criterion_passes(root):
    """The operation the retired list exists for, which used to fail.

    Rule 4 resolved every identifier against the live criteria only, so retiring
    one — removing the criterion and recording the identifier — reported it as an
    unresolved reference and failed a correctly retired spec. The existing
    retirement case keeps the identifier live, which is the only shape producing
    the *intended* finding, so nothing reached this branch.
    """
    spec = (SPEC.replace("- [ ] **AC-0002.** The second thing holds.\n", "")
                .replace("- **The second group (AC-0002):** TDD.\n", "")
            + "\n## Retired identifiers\n\n- AC-0002\n")
    plan = PLAN.split("### T2:")[0]
    result = _run(_tree(root, spec=spec, plan=plan))
    assert result.returncode == 0, result.stdout
    assert "resolves to no criterion" not in result.stdout


def test_a_plan_less_spec_is_reported_as_partial(root):
    """Two rules have no input without a plan; the summary must say so.

    Counting it under "checked" is the skipped-reads-as-clean failure this
    module exists to detect in other artifacts.
    """
    result = _run(_tree(root, plan=None))
    assert "partial (rules with no input:" in result.stdout, result.stdout
    assert "task-entry" in result.stdout and "derived-item" in result.stdout


def test_absent_retired_heading_is_an_empty_list(root):
    """Omitting the heading while nothing is retired is the convention."""
    result = _run(_tree(root))
    assert "retired" not in result.stdout
    assert result.returncode == 0, result.stdout


def test_criterion_in_no_verification_group_is_a_finding(root):
    spec = SPEC.replace("- **The second group (AC-0002):** TDD.\n", "")
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 1, result.stdout
    assert "AC-0002 appears in no verification group" in result.stdout


def test_criterion_in_two_verification_groups_is_a_finding(root):
    spec = SPEC.replace(
        "- **The second group (AC-0002):** TDD.",
        "- **The second group (AC-0002):** TDD.\n- **A third group (AC-0002):** manual QA.",
    )
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 1, result.stdout
    assert "AC-0002 appears in 2 verification groups" in result.stdout


def test_verification_item_may_not_derive_its_identifier(root):
    """Rule 7: VI-0001 mirroring AC-0001 is the derivation ADR-0107 forbids."""
    plan = PLAN.replace("- **AC-0001.** Assert the first thing.",
                        "- **AC-0001.** Assert the first thing. **VI-0001** covers it.")
    result = _run(_tree(root, plan=plan))
    assert result.returncode == 1, result.stdout
    assert "VI-0001 mirrors AC-0001" in result.stdout


def test_independent_verification_item_is_accepted(root):
    """The negative of rule 7: an item whose identifier is its own passes."""
    plan = PLAN.replace("- **AC-0001.** Assert the first thing.",
                        "- **AC-0001.** Assert the first thing. **VI-0042** covers it.")
    result = _run(_tree(root, plan=plan))
    assert result.returncode == 0, result.stdout


def test_a_shipped_spec_with_checked_criteria_is_still_checked(root):
    """A Shipped spec has every criterion ticked; the rules still apply to it."""
    spec = SPEC.replace("- [ ] **AC-", "- [x] **AC-")
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 0, result.stdout
    assert "1 spec(s) checked" in result.stdout


def test_an_indented_checkbox_is_not_a_criterion(root):
    """A nested list under a criterion is part of it, not a sibling criterion."""
    spec = SPEC + "      - [ ] a nested detail under the criterion above\n"
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 0, result.stdout
    assert "carries no identifier" not in result.stdout


def test_a_retired_identifier_may_be_backticked(root):
    """The convention shows bare identifiers; a backticked one is the same list."""
    spec = SPEC + "\n## Retired identifiers\n\n- `AC-0002`\n"
    result = _run(_tree(root, spec=spec))
    assert result.returncode == 1, result.stdout
    assert "AC-0002 is retired" in result.stdout


def test_crlf_line_endings_do_not_defeat_the_rules(root):
    """An adopter on Windows must get the same findings as one on POSIX."""
    spec = SPEC.replace("**AC-0002.** The second", "**AC-0001.** The second").replace("\n", "\r\n")
    plan = PLAN.replace("\n", "\r\n")
    result = _run(_tree(root, spec=spec, plan=plan))
    assert result.returncode == 1, result.stdout
    assert "AC-0001 is assigned twice" in result.stdout


def test_several_spec_directories_are_checked_independently(root):
    """The corpus case: one bad spec must not mask or infect a good one."""
    _tree(root)
    other = root / "docs" / "specs" / "other"
    other.mkdir(parents=True)
    (other / "spec.md").write_text(SPEC.replace("**AC-0002.** The second",
                                                "**AC-0001.** The second"), encoding="utf-8")
    (other / "plan.md").write_text(PLAN, encoding="utf-8")
    result = _run(root)
    assert result.returncode == 1, result.stdout
    assert "2 spec(s) checked" in result.stdout
    assert "docs/specs/other/spec.md: AC-0001 is assigned twice" in result.stdout
    assert "docs/specs/fixture" not in result.stdout.split("assigned twice")[0].rsplit("\n", 2)[-1]


def test_a_spec_dir_outside_the_root_is_refused(root):
    """The confinement refusal, which had no case until the catalogue named it."""
    _tree(root)
    result = subprocess.run(
        [sys.executable, str(CHECKER), "--root", str(root), str(root.parent)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 2, result.stdout
    assert "refusing path outside root" in result.stdout


def test_missing_plan_does_not_crash(root):
    """A spec authored before its plan exists is checked for what it can be."""
    result = _run(_tree(root, plan=None))
    assert result.returncode in (0, 1), result.stdout
    assert "Traceback" not in result.stderr
