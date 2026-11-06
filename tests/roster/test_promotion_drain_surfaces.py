"""Roster coverage for the drain's durable surfaces and the real-store smoke.

Spec: ``docs/specs/work-item-promotion-handoff`` — task T8, goal-based
checks: the work-item guide names the routes and what closure means; the
knowledge-capture architecture entry names the drain, the terminal
disposition, and the execution envelope; the security entry records the
§ D10 prose residual as settled by the read-path re-run; the changelog
entry leads the release; and the verification ledger records the
real-store drain run.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GUIDE = REPO_ROOT / "docs" / "guides" / "reference" / "work-item-capture.md"
ARCHITECTURE = REPO_ROOT / "docs" / "architecture" / "knowledge-capture.md"
SECURITY = REPO_ROOT / "docs" / "architecture" / "security.md"
LEDGER = (
    REPO_ROOT
    / "docs"
    / "specs"
    / "work-item-promotion-handoff"
    / "notes"
    / "verification-ledger.md"
)
CHANGELOG = REPO_ROOT / "docs" / "product" / "changelog.d"


def _normalized(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_guide_names_the_routes_and_what_closure_means() -> None:
    guide = _normalized(GUIDE)
    assert "What happens to a captured record later" in guide
    assert "promotion drain" in guide
    # The routes: defect → bug-fix, question → the classify table, decision
    # held until the governance sibling ships, unroutable held.
    assert "bug-fix" in guide
    assert "classify table" in guide
    assert "governance routing sibling" in guide
    assert "held" in guide
    # Closure: the three grounds, the dispositions, the refused ground.
    assert "overtaken" in guide and "superseded" in guide and "falsified" in guide
    assert "`routed`" in guide
    assert "`rejected` or `superseded`" in guide
    assert "a ground whose test fails is refused and the item stays open" in guide


def test_architecture_entry_names_the_drain_disposition_and_envelope() -> None:
    entry = _normalized(ARCHITECTURE)
    assert "The promotion drain: reading a record to act on it" in entry
    assert "promotion_drain.py" in entry
    assert "The terminal disposition is the sole commit point" in entry
    assert "execution envelope" in entry
    assert "10-second wall-clock cap" in entry
    assert "64-KiB output cap" in entry
    assert "LC_ALL=C" in entry
    assert "identical-disposition no-op" in entry


def test_security_records_the_prose_residual_as_settled() -> None:
    security = _normalized(SECURITY)
    assert "§ D10's prose residual — settled by the promotion drain's read-path re-run" in security
    assert "re-runs the same three controls" in security
    assert "refused as a routing input and held" in security
    # The gap list no longer carries it as unowned.
    assert "screened by nothing" not in security


def test_changelog_entry_leads_the_release() -> None:
    fragments = [
        path
        for path in CHANGELOG.glob("*.md")
        if "name = \"core\"" in path.read_text(encoding="utf-8")
    ]
    matching = [
        path
        for path in fragments
        if "promotion drain" in path.read_text(encoding="utf-8")
        and "version = \"4.0.20\"" in path.read_text(encoding="utf-8")
    ]
    # The hardening's fragment — pinned to its released version — is the
    # one that now leads the release (T23, re-versioned 4.0.20 after main
    # shipped 4.0.18 and 4.0.19); the 4.0.15 fragment stays.
    assert len(matching) == 1
    text = matching[0].read_text(encoding="utf-8")
    assert "version = \"4.0.20\"" in text
    assert "## Highlights" in text
    assert "no dispatch wired holds the item" in text
    assert "classify table's six members" in text
    assert "required citation" in text
    assert "stale workspace lock" in text


def test_ledger_records_the_real_store_drain_run() -> None:
    ledger = _normalized(LEDGER)
    assert "Real-store drain (smoke)" in ledger
    assert "unattended drain over this repository's observation store" in ledger
    assert "completed and reported" in ledger


def _skill_sections(path: Path) -> dict[str, str]:
    """The skill's numbered sections, keyed by their heading number."""
    sections: dict[str, str] = {}
    current = ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### ") and ". " in line:
            current = line.split(".", 1)[0].removeprefix("### ").strip()
            sections[current] = line
        elif current:
            sections[current] += "\n" + line
    return sections


SKILL = REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "work-intake" / "SKILL.md"


def test_classify_member_constant_pins_the_skill_classify_table() -> None:
    # § D3 (AC-0026): the drain's member constant and work-intake's § 4
    # classify table cannot drift apart silently — every member appears by
    # name in the table's section, and the table's row count equals the
    # constant's size, so a row added or renamed fails until the constant
    # follows.
    import importlib.util
    import re
    import sys

    scripts_dir = (
        REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "project-knowledge" / "scripts"
    )
    spec = importlib.util.spec_from_file_location(
        "_surfaces_promotion_drain", scripts_dir / "promotion_drain.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    section = _skill_sections(SKILL)["4"]
    table_rows = [
        line
        for line in section.splitlines()
        if line.startswith("|") and not line.startswith("| Input shape") and "---" not in line
    ]
    assert len(table_rows) == len(module.CLASSIFY_TABLE_MEMBERS), table_rows
    for member in module.CLASSIFY_TABLE_MEMBERS:
        assert re.search(rf"\b{re.escape(member)}\b", section, re.IGNORECASE), member


def test_skill_section_8_records_the_dispatch_wiring_rule() -> None:
    # § D1 (AC-0025): work-intake's § 8 records how the operator wires the
    # dispatch at invocation — the wiring note names `dispatch_processor`
    # and states that a drain without it holds every routable item.
    section = _normalized_sections = " ".join(
        _skill_sections(SKILL)["8"].split()
    )
    assert "dispatch_processor" in section
    assert "holds every routable item" in section
    assert "no lock taken and no artifact written" in section


def test_closure_sentences_carry_the_citation_rule() -> None:
    # § D5 (AC-0027), the T21 pins: the guide's closure sentence and
    # work-intake § 8's closure sentence each name the required `citation`
    # field and the drain-run resolution test.
    guide = _normalized(GUIDE)
    assert "required `citation` field" in guide
    assert "`{\"capture_id\": <id>}` or `{\"path\": <repository-relative path>}`" in guide
    assert "the drain itself resolves it before committing" in guide
    assert "refuses the closure whatever the operator attests" in guide

    skill_section_8 = " ".join(_skill_sections(SKILL)["8"].split())
    assert "required `citation` field" in skill_section_8
    assert "the drain itself runs" in skill_section_8
    assert "resolution test before committing" in skill_section_8
    assert "refuses the closure whatever the operator attests" in skill_section_8


def test_hardened_sentences_pin_the_durable_surfaces() -> None:
    # T23: the durable surfaces the hardening falsifies carry its rules —
    # the architecture entry's confirmed-route sentence gains the
    # no-dispatch hold, and the guide's question-routing sentence gains the
    # non-dispatchable-member hold.
    entry = _normalized(ARCHITECTURE)
    assert "a route with no dispatch wired holds the item" in entry
    assert "never recorded as routed without its handoff" in entry
    guide = _normalized(GUIDE)
    assert "only a classification that is one of the table's six members routes" in guide
    assert "`remember` or `incomplete` — is held as unroutable" in guide


def test_gitignores_cover_the_acquisition_temporary() -> None:
    # T23: the acquisition temporary's root glob sits beside the lock in
    # both the repository's own ignore and the adopter-facing seed copy —
    # the shipped `intake_transaction.py` creates the temporary in adopter
    # trees too.
    for path in (REPO_ROOT / ".gitignore", REPO_ROOT / "packs" / "core" / "seeds" / ".gitignore"):
        lines = path.read_text(encoding="utf-8").splitlines()
        lock = lines.index(".workspace-repair.lock")
        assert lines[lock + 1] == ".workspace-repair.lock.*.tmp", path


def test_admission_record_defect_note_carries_the_correction() -> None:
    # T26 (finding adv-hardening-002): the admission-record defect for the
    # T19/T20 gate receipts is recorded durably in the repository — the
    # note names both receipts, their cause, and the correction.
    note = _normalized(
        REPO_ROOT / "docs" / "product" / "captured" / "admission-record-defect-t19-t20-gate-receipts.md"
    )
    assert "a-route-with-no-dispatch-wired-holds-the-item-1646c3a2" in note
    assert "a-classification-is-one-of-the-six-classify-tabl-9aef571e" in note
    assert "0b8454304" in note and "a51b1aee8" in note
    assert "false at admission time" in note
    assert "automation script" in note
    assert "adv-hardening-002" in note
    assert "correction" in note


def test_repair_round_record_is_accurate() -> None:
    # T28 (findings adv-hardening-101..103): the note names the sole
    # implementation carrier and distinguishes the receipt-only commits;
    # the plan's repair tasks declare their dependencies; the captured
    # item the CI pin cites records the pin.
    note = _normalized(
        REPO_ROOT / "docs" / "product" / "captured" / "admission-record-defect-t19-t20-gate-receipts.md"
    )
    assert "all of it in the single commit labeled" in note
    assert "receipt-only commits recorded after their implementations" in note
    plan_text = (REPO_ROOT / "docs" / "specs" / "work-item-promotion-handoff" / "plan.md").read_text(
        encoding="utf-8"
    )
    import re as _re

    for task in ("T24:", "T25:", "T26:", "T27:", "T28:"):
        block = _re.search(rf"### {task}.*?(?=^### |^## )", plan_text, _re.DOTALL | _re.MULTILINE)
        assert block is not None, task
        assert "Depends on:" in block.group(0), task
    captured = _normalized(
        REPO_ROOT / "docs" / "product" / "captured" / "pre-existing-closure-index-collapsible-if.md"
    )
    assert "0.17.4 reports one" in captured
    assert "passes every check under ruff 0.14.0, 0.16.10, and 0.17.2" in captured
    assert "between 0.17.2 and 0.17.4" in captured


def test_ruff_parity_record_has_one_declared_source() -> None:
    # T29: the parity record is reconciled through its declared single
    # source — the workflow's ruff install is bare, the pin lives once in
    # tools/requirements.txt, and the workflow comment points at the
    # recorded version facts rather than restating a range claim.
    workflow = (REPO_ROOT / ".github" / "workflows" / "build-check.yml").read_text(
        encoding="utf-8"
    )
    assert "pip install ruff mypy" in workflow
    assert "ruff==0.14.0 mypy" not in workflow
    requirements = (REPO_ROOT / "tools" / "requirements.txt").read_text(encoding="utf-8")
    assert "ruff==0.16.10" in requirements
    assert "Declared here rather than pinned inline" in requirements


def test_parity_record_citations_resolve_and_no_stale_sections() -> None:
    # T30: every citation in the parity record resolves to a step that
    # exists, and the captured note carries no section describing the
    # removed inline pin.
    for rel in (
        ".github/workflows/build-check.yml",
        "tools/requirements.txt",
        "docs/product/captured/pre-existing-closure-index-collapsible-if.md",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "Install tools requirements" not in text, rel
    workflow = (REPO_ROOT / ".github" / "workflows" / "build-check.yml").read_text(
        encoding="utf-8"
    )
    assert "Install tools dependencies" in workflow
    captured = _normalized(
        REPO_ROOT / "docs" / "product" / "captured" / "pre-existing-closure-index-collapsible-if.md"
    )
    assert "Known-skip treatment" not in captured
    assert "pin ruff 0.14.0" not in captured
    assert "No skip treatment is in force" in captured
