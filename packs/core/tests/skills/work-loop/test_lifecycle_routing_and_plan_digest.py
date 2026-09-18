"""T7 contract tests for in-flight routing and whole-plan approval pinning."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

WORK_LOOP = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
LIFECYCLE = WORK_LOOP / "references" / "delivery-contract-lifecycle.md"
GUARDS = WORK_LOOP / "scripts" / "_loop_guards.py"


def _load_guards():
    """Load the production digest helper under a pack-and-skill-specific name."""
    spec = importlib.util.spec_from_file_location(
        "core_work_loop_guards_t7", GUARDS
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _assert_lifecycle_routes(reference: str) -> None:
    """Assert the observation and error routes have distinct destinations."""

    assert "`no stub (implementation-discovered)`" in reference
    assert "goes in the verification ledger" in reference
    assert "amends neither approved artifact" in reference
    assert "approval settled a design decision and execution falsifies it" in reference
    assert "plan is wrong" in reference
    assert "controlled amendment procedure above" in reference
    assert "not a route for a settled decision that execution falsified" in reference


def _approval_digest(guards, text: str) -> str:
    """Use the production approval-digest helper against an in-memory plan."""
    original_reader = guards.read_managed_text
    guards.read_managed_text = lambda _path, _label: text
    try:
        return guards.sha256_canonical_contract(Path("plan.md"))
    finally:
        guards.read_managed_text = original_reader


def _assert_plan_digest_contract(guards) -> None:
    """Assert design prose is pinned while plan checkbox progress is bookkeeping."""
    base = """# Plan\n\n- **Status:** Approved\n\n## Design (LLD)\n\nUse an append-only ledger.\n\n## Tasks\n\n- [ ] Implement the ledger.\n\n## Acceptance Criteria\n\n- [ ] **AC-1.** The ledger is append-only.\n"""
    changed_design = base.replace("append-only ledger", "versioned ledger")
    completed_task = base.replace("- [ ] Implement the ledger.", "- [x] Implement the ledger.")

    base_digest = _approval_digest(guards, base)
    assert _approval_digest(guards, changed_design) != base_digest
    assert _approval_digest(guards, completed_task) == base_digest


def test_lifecycle_names_observation_and_error_routes() -> None:
    """Declared discovery records evidence; a falsified settled decision amends."""
    reference = " ".join(LIFECYCLE.read_text(encoding="utf-8").split())
    _assert_lifecycle_routes(reference)


def test_lifecycle_route_assertion_red_on_in_memory_mutation() -> None:
    """Removing the error-route wording makes the lifecycle assertion fail."""
    reference = " ".join(LIFECYCLE.read_text(encoding="utf-8").split())
    mutated = reference.replace(
        "The verification ledger is not a route for a settled decision that execution falsified.",
        "The verification ledger records the settled decision.",
    )

    with pytest.raises(AssertionError):
        _assert_lifecycle_routes(mutated)


def test_plan_digest_pins_design_and_normalizes_task_checkboxes() -> None:
    """A plan is whole-file pinned; changing its checkbox bookkeeping is harmless."""
    _assert_plan_digest_contract(_load_guards())


def test_plan_digest_assertion_red_when_plan_is_ac_section_only(monkeypatch) -> None:
    """The bookkeeping assertion fails if plan.md is mistakenly AC-section scoped."""
    guards = _load_guards()
    canonical = guards.canonical_contract

    def wrongly_scoped(text: str, *, ac_section_only: bool = True) -> str:
        return canonical(text, ac_section_only=True)

    monkeypatch.setattr(guards, "canonical_contract", wrongly_scoped)
    with pytest.raises(AssertionError):
        _assert_plan_digest_contract(guards)
