"""Envelope references, replan classification, and task projection (T2).

VI-4010 (AC-0007, AC-0009), VI-4011 (AC-0005), VI-4012 (AC-0006), VI-4013.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import supervisor_support as sup  # noqa: E402

proj = sup.load("_supervisor_projector.py")


def _refs(spec: str, adr: str = sup.ADR) -> dict[str, str]:
    records = {"docs/adr/0001-calculators-answer.md": adr}

    def read(path: str) -> str:
        if path not in records:
            raise OSError(path)
        return records[path]

    def listing(directory: str) -> list[str]:
        return [p.rsplit("/", 1)[1] for p in records if p.rsplit("/", 1)[0] == directory]

    return proj.envelope_references(spec, read_record=read, list_dir=listing).refs


def _envelope(spec: str = sup.SPEC) -> dict:
    return proj._sibling("_acceptance.py").derive_envelope(_refs(spec))


def _classify(spec: str, adr: str = sup.ADR) -> tuple[str, str] | None:
    return proj.classify_replan(
        approved_envelope=_envelope(),
        approved_intent="code",
        current_refs=_refs(spec, adr),
        current_intent=proj.terminal_intent(spec),
    )


def _edit(old: str, new: str, text: str = sup.SPEC) -> str:
    assert old in text, old
    return text.replace(old, new, 1)


# ── VI-4011: bookkeeping edits leave the fingerprint byte-identical ──────────

BOOKKEEPING: dict[str, Callable[[], str]] = {
    "outcome": lambda: _edit("calculator that answers.", "calculator that answers fast."),
    "what-changes": lambda: _edit(
        "- `calc.py` arrives.", "- `calc.py` and `calc_test.py` arrive."
    ),
    "follow-ons": lambda: _edit("## Follow-ons\n\nnone", "## Follow-ons\n\nA second calculator."),
    "assumptions": lambda: _edit("## Assumptions\n\nnone", "## Assumptions\n\nPython exists."),
    "criterion-checkbox": lambda: _edit("- [ ] **AC-0001.**", "- [x] **AC-0001.**"),
    "status-token": lambda: _edit("- **Status:** Approved", "- **Status:** Implementing"),
    "other-metadata": lambda: _edit("- **Owner:** Platform Core", "- **Owner:** Release Core"),
    "trailing-whitespace": lambda: _edit("no user interface.", "no user interface.   "),
}


@pytest.mark.parametrize("name", sorted(BOOKKEEPING))
def test_bookkeeping_edit_leaves_fingerprint_unchanged(name: str) -> None:
    before = _envelope()
    after = proj._sibling("_acceptance.py").derive_envelope(_refs(BOOKKEEPING[name]()))
    assert after == before


def test_cited_record_edit_outside_its_decision_leaves_fingerprint_unchanged() -> None:
    adr = sup.ADR.replace("Callers need an answer.", "Callers need a fast answer.")
    assert _refs(sup.SPEC, adr) == _refs(sup.SPEC)


def test_plan_text_is_not_part_of_the_envelope() -> None:
    # The envelope reads only the spec and its cited records, never the plan.
    assert _classify(sup.SPEC) is None


# ── VI-4010: the replan corpus is classified with its named owner ────────────

PROTECTED: dict[str, tuple[Callable[[], str], tuple[str, str]]] = {
    "criteria": (
        lambda: _edit("answers 42.", "answers 43."),
        ("criteria-changed", "spec-amendment owner"),
    ),
    "testing-strategy": (
        lambda: _edit("**Calculator (AC-0001):** TDD.", "**Calculator (AC-0001):** goal-based."),
        ("criteria-changed", "spec-amendment owner"),
    ),
    "agent-rules": (
        lambda: _edit("- Reach the network.", "- Reach the disk."),
        ("criteria-changed", "spec-amendment owner"),
    ),
    "scope": (
        lambda: _edit("no user interface.", "a small user interface."),
        ("scope-changed", "spec-amendment owner"),
    ),
    "constrained-by": (
        lambda: _edit(
            "- **Constrained by:** ADR-0001", "- **Constrained by:** ADR-0001, RFC-0002"
        ),
        ("authority-changed", "decision owner"),
    ),
    "contract": (
        lambda: _edit("`contracts/calc/`", "`contracts/calc/v2/`"),
        ("contract-changed", "contract owner"),
    ),
    "durable-outputs": (
        lambda: _edit("| Release history | changelog |", "| Release history | release notes |"),
        ("durable-outputs-changed", "spec-amendment owner"),
    ),
    "accepted-risk": (
        lambda: _edit("## Accepted Risk\n\nnone", "## Accepted Risk\n\nThe answer may drift."),
        ("accepted-risk-changed", "risk owner"),
    ),
    "terminal-intent": (
        lambda: _edit("`code` — build the calculator.", "`spec-plan` — stop at review."),
        ("terminal-intent-changed", "plan-review authority"),
    ),
}


@pytest.mark.parametrize("name", sorted(PROTECTED))
def test_protected_edit_refuses_with_its_owner(name: str) -> None:
    edit, expected = PROTECTED[name]
    if name == "constrained-by":
        # The newly cited record must be readable for the change to classify.
        spec = edit()
        records = {
            "docs/adr/0001-calculators-answer.md": sup.ADR,
            "docs/rfc/0002-answers.md": "# RFC\n\n## Proposal\n\nAnswer.\n",
        }
        refs = proj.envelope_references(
            spec,
            read_record=records.__getitem__,
            list_dir=lambda d: [p.rsplit("/", 1)[1] for p in records if p.startswith(d + "/")],
        ).refs
        result = proj.classify_replan(
            approved_envelope=_envelope(),
            approved_intent="code",
            current_refs=refs,
            current_intent="code",
        )
    else:
        result = _classify(edit())
    assert result == expected


def test_cited_decision_edit_refuses_with_the_decision_owner() -> None:
    adr = sup.ADR.replace("The calculator answers 42.", "The calculator answers 43.")
    assert _classify(sup.SPEC, adr) == ("authority-changed", "decision owner")


def test_terminal_intent_edit_keeping_the_value_needs_no_approval() -> None:
    spec = _edit("`code` — build the calculator.", "`code` — build the calculator quickly.")
    assert _classify(spec) is None


@pytest.mark.parametrize(
    "heading", ["Acceptance Criteria", "Scope and Non-goals", "Terminal Intent"]
)
def test_repeated_protected_heading_refuses_as_ambiguous(heading: str) -> None:
    spec = sup.SPEC + f"\n## {heading}\n\nagain\n"
    with pytest.raises(proj.ProjectionRefused) as info:
        _refs(spec)
    assert info.value.code == "ambiguous-reference"
    assert info.value.owner == heading


def test_unreadable_cited_record_refuses_naming_it() -> None:
    spec = _edit("- **Constrained by:** ADR-0001", "- **Constrained by:** ADR-0009")
    with pytest.raises(proj.ProjectionRefused) as info:
        _refs(spec)
    assert info.value.code == "unreadable-reference"
    assert info.value.owner == "ADR-0009"


IN_ENVELOPE_PLANS: dict[str, Callable[[], str]] = {
    "reorder": lambda: sup.plan(
        sup.TASKS["plain"]("T1"), sup.TASKS["calc"]("T2"), sup.TASKS["push"]("T3", depends="T2")
    ),
    "renumber": lambda: sup.plan(
        sup.TASKS["calc"]("T7"), sup.TASKS["push"]("T8", depends="T7"), sup.TASKS["plain"]("T9")
    ),
    "rewrite-depends-on": lambda: sup.plan(
        sup.TASKS["calc"](), sup.TASKS["push"](depends="T3"), sup.TASKS["plain"]()
    ),
    "split": lambda: sup.plan(
        sup.TASKS["calc"](),
        sup.TASKS["push"](),
        sup.task("T3", "Plain note is drafted", touches="`plain.txt`"),
        sup.task("T4", "Plain note is finished", touches="`plain.txt`"),
    ),
    "merge": lambda: sup.plan(
        sup.TASKS["calc"](),
        sup.task("T2", "Release and note ship", touches="`release.txt`, `plain.txt`"),
    ),
    "replace": lambda: sup.plan(
        sup.TASKS["calc"](), sup.TASKS["push"](), sup.task("T3", "Something else entirely")
    ),
    "delete": lambda: sup.plan(sup.TASKS["calc"](), sup.TASKS["push"]()),
    "change-tests": lambda: sup.plan(
        sup.TASKS["calc"](),
        sup.TASKS["push"](),
        sup.task(
            "T3",
            "Plain note is written",
            touches="`plain.txt`",
            mode="goal-based",
            tests="no stub (checked by reading the file)",
            done="plain.txt says done",
        ),
    ),
    "change-stubs": lambda: sup.plan(
        sup.task(
            "T1",
            "Calculator answers",
            tests="- **VI-1:** x\n\n" + sup.stub_fence(red_exit="1,2", indent="  "),
        ),
        sup.TASKS["push"](),
        sup.TASKS["plain"](),
    ),
    "change-effects": lambda: sup.plan(
        sup.TASKS["calc"](), sup.TASKS["push"](effects="publish"), sup.TASKS["plain"]()
    ),
}


@pytest.mark.parametrize("name", sorted(IN_ENVELOPE_PLANS))
def test_in_envelope_replan_projects_a_different_task_set(name: str) -> None:
    # The plan is outside the envelope, so each of these projects anew; that no
    # approval is requested mid-run is shown through `next` in the step-loop suite.
    projected = proj.project_plan(IN_ENVELOPE_PLANS[name]()).tasks
    base = proj.project_plan(sup.PLAN).tasks
    assert projected
    if name not in ("renumber", "reorder", "rewrite-depends-on"):
        assert [(t["task_id"], t["revision"]) for t in projected] != [
            (t["task_id"], t["revision"]) for t in base
        ]


# ── VI-4012: a template-shaped spec imports with six distinct values ─────────


def test_template_shaped_spec_imports_with_six_distinct_values(tmp_path: Path) -> None:
    assets = sup.SCRIPTS.parents[1] / "new-spec" / "assets"
    spec_path, plan_path = tmp_path / "spec.md", tmp_path / "plan.md"
    spec_path.write_bytes((assets / "spec.md").read_bytes())
    plan_path.write_bytes((assets / "plan.md").read_bytes())
    refs = proj.envelope_references(
        spec_path.read_text(encoding="utf-8"), read_record=lambda p: "", list_dir=lambda d: []
    ).refs
    assert len(set(refs.values())) == 6
    pi = sup.load("_policy_import.py")
    sc = sup.load("_security_capability.py")
    issuer = sc.CapabilityIssuer()
    grant = issuer.issue_root_grant(
        roots=["delivery"],
        operations=["append"],
        trust_class="trusted",
        writes_allowed_roots=["delivery/policy-import"],
        control_denies=[],
    )
    envelope = proj._sibling("_acceptance.py").derive_envelope(refs)
    approval, review = pi.import_policy(
        spec_path=spec_path,
        plan_path=plan_path,
        refs=refs,
        terminal_intent="code",
        writer_grant=grant,
        issuer=issuer,
        audit_sink=lambda event: None,
        store=pi.ImportStore(),
        approval_identity="owner",
        approval_role="owner",
        reviewer_identity="plan-reviewer",
        reviewer_role="plan-reviewer",
        approved_spec_digest=pi.compute_spec_digest(spec_path),
        approved_plan_digest=pi.compute_plan_digest(plan_path),
        approved_envelope_fingerprint=envelope["envelope_fingerprint"],
    )
    assert review["envelope_fingerprint"] == envelope["envelope_fingerprint"]
    assert approval["decision"] == "approved"


# ── VI-4013: revisions follow pinned fields only ─────────────────────────────


def _revisions(plan_text: str) -> dict[str, str]:
    return {t["task_id"]: t["revision"] for t in proj.project_plan(plan_text).tasks}


def test_renumber_reorder_and_approach_edits_keep_revisions() -> None:
    base = _revisions(sup.PLAN)
    assert _revisions(IN_ENVELOPE_PLANS["renumber"]()) == base
    assert _revisions(IN_ENVELOPE_PLANS["reorder"]()) == base
    approach = sup.plan(
        sup.TASKS["calc"](approach="another way"),
        sup.TASKS["push"](),
        sup.TASKS["plain"](approach="by hand"),
    )
    assert _revisions(approach) == base
    assert _revisions(IN_ENVELOPE_PLANS["rewrite-depends-on"]()) == base


def test_tests_edit_changes_the_revision() -> None:
    base = _revisions(sup.PLAN)
    edited = sup.plan(
        sup.TASKS["calc"](),
        sup.TASKS["push"](),
        sup.task(
            "T3",
            "Plain note is written",
            touches="`plain.txt`",
            mode="goal-based",
            tests="no stub (manual check)",
            done="plain.txt says done",
        ),
    )
    changed = _revisions(edited)
    plain = next(t for t in changed if t.startswith("plain-note"))
    assert changed[plain] != base[plain]
    assert {k: v for k, v in changed.items() if k != plain} == {
        k: v for k, v in base.items() if k != plain
    }


def test_stub_fence_projects_byte_identical_payload() -> None:
    calc = proj.project_plan(sup.PLAN).tasks[0]
    assert [s["content"] for s in calc["stubs"]] == [sup.STUB]
    assert calc["stubs"][0]["red_exit"] == [1]
    assert calc["stub_digest"] is not None


def test_finish_effects_come_from_plan_level_effects_lines() -> None:
    projection = proj.project_plan(sup.plan(sup.TASKS["calc"](), header_effects="ship"))
    assert projection.finish_effects == ["ship"]


@pytest.mark.parametrize("path", ["/abs.py", "../up.py", "a\\b.py", "a//b.py", "C:x.py"])
def test_unsafe_stub_path_refuses(path: str) -> None:
    bad = sup.plan(
        sup.task(
            "T1",
            "Calculator answers",
            tests="- **VI-1:** x\n\n" + sup.stub_fence(path=path, indent="  "),
        )
    )
    with pytest.raises(proj.ProjectionRefused) as info:
        proj.project_plan(bad)
    assert info.value.code == "invalid-stub-path"


def test_a_blank_line_before_the_closing_fence_is_refused() -> None:
    fence = sup.stub_fence(indent="  ")
    fence = fence[: fence.rindex("\n")] + "\n\n" + fence[fence.rindex("\n") + 1:]
    bad = sup.plan(sup.task("T1", "Calculator answers", tests="- **VI-1:** x\n\n" + fence))
    with pytest.raises(proj.ProjectionRefused) as info:
        proj.project_plan(bad)
    assert info.value.code == "invalid-stub-fence"


def test_a_crlf_plan_with_stub_fences_is_refused() -> None:
    with pytest.raises(proj.ProjectionRefused) as info:
        proj.project_plan(sup.PLAN.replace("\n", "\r\n"))
    assert info.value.code == "invalid-stub-fence"
