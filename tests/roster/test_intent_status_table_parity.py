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


def _says_required(cell: str) -> bool:
    return "required" in cell and "neither" not in cell


def test_both_adopter_pages_state_the_rules_the_validator_applies() -> None:
    shape = _load_validator()
    for page in (REFERENCE, HOW_TO):
        text = page.read_text(encoding="utf-8")
        for status, (required, _) in shape._STATE_COHERENCE_RULES.items():
            accepted_cell, fulfilled_cell = _documented_row(text, status)
            assert _says_required(accepted_cell) == ("Accepted" in required), (
                page.name,
                status,
                "Accepted:",
            )
            assert _says_required(fulfilled_cell) == ("Fulfilled" in required), (
                page.name,
                status,
                "Fulfilled:",
            )


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
