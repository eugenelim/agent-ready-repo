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


def test_missing_plan_does_not_crash(root):
    """A spec authored before its plan exists is checked for what it can be."""
    result = _run(_tree(root, plan=None))
    assert result.returncode in (0, 1), result.stdout
    assert "Traceback" not in result.stderr
