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
    ]
    assert len(matching) == 1
    text = matching[0].read_text(encoding="utf-8")
    assert "version = \"4.0.13\"" in text
    assert "## Highlights" in text


def test_ledger_records_the_real_store_drain_run() -> None:
    ledger = _normalized(LEDGER)
    assert "Real-store drain (smoke)" in ledger
    assert "unattended drain over this repository's observation store" in ledger
    assert "completed and reported" in ledger
