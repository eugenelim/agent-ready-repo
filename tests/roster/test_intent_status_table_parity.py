"""The adopter pages and the validator agree about status-conditional records.

Reads `guides/` and `packs/core/`, so it is a repository-level assertion and
lives here per `tests/AGENTS.md`, beside its sibling
`test_intent_field_reference_parity.py`.

Two surfaces a refused reader is sent to restate the rule table:
`intent-fields-and-modes.md` and `fix-a-refused-intent.md`. Neither is covered
by the field-reference parity suite — that one bounds itself to table rows
whose first cell is a backticked field name, and these tables' first cells are
deliberately unbackticked so they are not read as field rows. Without this,
changing a rule updates the module and leaves both adopter pages quietly wrong.

The refusal-message half matters for the same reason: four reason strings are
quoted byte-for-byte on the how-to page, and no other test asserts reason text
at all.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT / "packs/core/.apm/skills/work-intake/scripts/intent_shape.py"
)
REFERENCE = (
    ROOT / "guides/product-engineering/reference/intent-fields-and-modes.md"
)
HOW_TO = ROOT / "guides/product-engineering/how-to/fix-a-refused-intent.md"


def _load_validator():
    name = "roster_intent_status_table_parity"
    spec = importlib.util.spec_from_file_location(name, VALIDATOR)
    assert spec and spec.loader, VALIDATOR
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _intent(status: str, extra: str = "") -> str:
    return (
        "- **Owner:** o\n"
        "- **Slug:** `p`\n"
        "- **Level:** feature\n"
        f"- **Status:** {status}\n"
        f"{extra}\n"
        "\n## Body\n"
    )


def _status_table(text: str) -> dict[str, tuple[str, str]]:
    """Rows of the per-status table, keyed by status.

    Located by its header rather than by row shape. The field table on the
    reference page also carries rows named `Accepted` and `Fulfilled` — those
    are the *fields* — so matching on the first cell alone reads the wrong
    table. The header is the only unambiguous landmark, and it is the one
    thing both pages share: the two record names as the second and third
    columns.
    """
    lines = text.splitlines()
    for index, line in enumerate(lines):
        cells = [c.strip().strip("`") for c in line.split("|")[1:-1]]
        if len(cells) == 3 and cells[1] == "Accepted:" and cells[2] == "Fulfilled:":
            rows: dict[str, tuple[str, str]] = {}
            for row in lines[index + 2 :]:
                if not row.startswith("|"):
                    break
                parts = [c.strip() for c in row.split("|")[1:-1]]
                if len(parts) == 3:
                    rows[parts[0].strip("`")] = (
                        parts[1].lower(),
                        parts[2].lower(),
                    )
            assert rows, "per-status table header found but no rows parsed"
            return rows
    raise AssertionError("no per-status table found on this page")


def _documented_row(text: str, status: str) -> tuple[str, str]:
    rows = _status_table(text)
    assert status in rows, f"no documented row for status {status!r}"
    return rows[status]


def _documented_verdict(cell: str) -> str:
    """The cell's verdict as one of `required`, `refused` or `optional`.

    All three are distinguished. An earlier version asked only whether the
    cell said "required", which made `refused` and `optional` the same answer
    — so a page could tell a refused reader a record was optional where the
    lint refuses it, and this control would pass.
    """
    if "neither" in cell:
        return "undecided"
    if "required" in cell:
        return "required"
    if "refused" in cell:
        return "refused"
    if "optional" in cell:
        return "optional"
    raise AssertionError(f"unrecognised verdict in documented cell: {cell!r}")


def _expected_verdict(record: str, required: tuple, forbidden: tuple) -> str:
    if record in required:
        return "required"
    if record in forbidden:
        return "refused"
    return "optional"


def test_both_adopter_pages_state_the_rules_the_validator_applies() -> None:
    shape = _load_validator()
    for page in (REFERENCE, HOW_TO):
        text = page.read_text(encoding="utf-8")
        for status, (required, forbidden) in shape._STATE_COHERENCE_RULES.items():
            cells = dict(
                zip(
                    ("Accepted", "Fulfilled"),
                    _documented_row(text, status),
                    strict=True,
                )
            )
            for record, cell in cells.items():
                assert _documented_verdict(cell) == _expected_verdict(
                    record, required, forbidden
                ), (page.name, status, f"{record}:", cell)


def test_every_status_the_validator_decides_has_a_documented_row() -> None:
    """A status added to the rules but not to the pages fails here."""
    shape = _load_validator()
    for page in (REFERENCE, HOW_TO):
        text = page.read_text(encoding="utf-8")
        for status in shape._STATE_COHERENCE_RULES:
            _documented_row(text, status)


def test_the_how_to_quotes_the_refusal_messages_the_module_emits() -> None:
    shape = _load_validator()
    how_to = HOW_TO.read_text(encoding="utf-8")

    required = shape._check_state_coherence(_intent("Fulfilled"))
    forbidden = shape._check_state_coherence(
        _intent("Draft", "- **Accepted:** 2026-09-20 ratified by the owner")
    )
    assert required and forbidden

    for violation in (*required, *forbidden):
        assert violation.reason in how_to, violation.reason


def test_a_status_the_rules_leave_undecided_is_documented_as_undecided() -> None:
    """`Superseded` is encoded as absence, so iterating the rules misses it.

    Both controls above walk `_STATE_COHERENCE_RULES`, and the statuses this
    spec deliberately does not decide are exactly the ones that are not keys.
    That left the single row describing them unasserted on both pages: it
    could have read `required` for either record and nothing would have
    noticed.
    """
    shape = _load_validator()
    undecided = set(shape.STATUS_VALUES) - set(shape._STATE_COHERENCE_RULES)
    assert undecided, "expected at least one status the rules leave undecided"

    for page in (REFERENCE, HOW_TO):
        text = page.read_text(encoding="utf-8")
        for status in undecided:
            for cell in _documented_row(text, status):
                assert _documented_verdict(cell) == "undecided", (
                    page.name,
                    status,
                    cell,
                )
