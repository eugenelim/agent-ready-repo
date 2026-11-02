"""Roster test: verify-entry receipt mapping fits evidence-receipt.v1.

Parses the ``### Receipt mapping`` sub-section of the shipped
verification-modes reference and validates a receipt built from every table row
against ``contracts/delivery/evidence-receipt.v1.schema.json``.

Spec: docs/specs/verify-entries/spec.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
MODES = ROOT / "packs/core/.apm/skills/work-loop/references/verification-modes.md"
SCHEMA = ROOT / "contracts/delivery/evidence-receipt.v1.schema.json"
GRADES = {"live-verified", "build-only", "blocked", "failed", "test-verified"}


def _section() -> str:
    """Return the Receipt mapping sub-section text."""
    text = MODES.read_text(encoding="utf-8")
    start = text.index("### Receipt mapping")
    end = text.find("\n### ", start + 1)
    return text[start : end if end != -1 else len(text)]


def _rows(section: str) -> list[tuple[str, str, str]]:
    """Return (grade, observation.type, outcome) for each table row."""
    rows = []
    for line in section.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and not set(cells[0]) <= set("-: ") and cells[0] != "Grade":
            rows.append((cells[0], cells[1], cells[2]))
    return rows


def _span(section: str, prefix: str) -> str:
    """Return the first code-span value on the field line starting with prefix."""
    for line in section.splitlines():
        if line.startswith(prefix):
            return re.findall(r"`([^`]*)`", line)[-1]
    raise AssertionError(f"field line missing: {prefix}")


def test_receipt_mapping_rows_fit_schema() -> None:
    """Every mapping row yields a schema-valid evidence receipt."""
    section = _section()
    rows = _rows(section)
    assert {grade for grade, _, _ in rows} == GRADES
    version = int(_span(section, "- `schema_version`"))
    receipt_id = (
        _span(section, "- `receipt_id`")
        .replace("<surface>", "agentbundle-cli")
        .replace("<run-id>", "run-1")
    )
    freshness = _span(section, "- `freshness_mode`")
    producer_line = next(
        line for line in section.splitlines() if line.startswith("- The producer")
    )
    match = re.search(r"`(\{.*\})`", producer_line)
    assert match is not None
    producer: dict[str, Any] = json.loads(match.group(1).replace("<surface>", "agentbundle-cli"))
    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    for _grade, obs_type, outcome in rows:
        receipt = {
            "schema_version": version,
            "receipt_id": receipt_id,
            "acceptance_fingerprint": "git:0000000",
            "lineage": {"criterion_ref": "criterion-placeholder"},
            "selector": {"term": "verify"},
            "freshness_mode": freshness,
            "observation": {"type": obs_type},
            "outcome": outcome,
            "producer": producer,
        }
        errors = [e.message for e in validator.iter_errors(receipt)]
        assert not errors, (obs_type, outcome, errors)


VERIFICATION = ROOT / "docs/VERIFICATION.md"
LEDGER = ROOT / "docs/specs/verify-entries/notes/verification-ledger.md"
FIELDS = [
    "Surface",
    "Launch",
    "Ready",
    "Doctor",
    "Isolation",
    "Drive",
    "Features",
    "Evidence",
    "Proof limits",
    "Cleanup",
    "Helpers",
    "Stand-in gap",
]
FORBIDDEN = ("/Users/", "/home/", "/private/var/", "/var/folders/", "C:\\Users")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _entry() -> str:
    """Return the agentbundle CLI entry text from docs/VERIFICATION.md."""
    text = VERIFICATION.read_text(encoding="utf-8")
    start = text.index("## Verify: agentbundle CLI")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else len(text)]


def _field(name: str) -> str:
    """Return the body of one ``### `` field in the entry."""
    parts = re.split(r"^### ", _entry(), flags=re.M)[1:]
    return next(p for p in parts if p.startswith(name + "\n"))


def test_dogfood_entry_has_twelve_fields_in_order() -> None:
    """The agentbundle CLI entry carries every template field, in order."""
    headings = re.findall(r"^### (.+)$", _entry(), flags=re.M)
    assert headings == FIELDS


def test_dogfood_drive_holds_render_install_and_diff() -> None:
    """The Drive field names the render, codex install, and diff commands."""
    drive = _field("Drive")
    for needle in ("agentbundle render", "--adapter codex", "install", " diff --root"):
        assert needle in drive, needle


def test_verification_and_notes_hold_no_paths_or_emails() -> None:
    """The entry (and the notes file, once it exists) names no host path or email."""
    files = [VERIFICATION] + ([LEDGER] if LEDGER.exists() else [])
    for path in files:
        text = path.read_text(encoding="utf-8")
        for bad in FORBIDDEN:
            assert bad not in text, (path.name, bad)
        assert not EMAIL.search(text), path.name


def _ledger_receipts() -> list[dict[str, Any]]:
    """Every fenced json block under the ledger's `## Receipts` heading."""
    text = LEDGER.read_text(encoding="utf-8")
    assert "## Receipts" in text, "ledger has no ## Receipts heading"
    section = text.split("## Receipts", 1)[1].split("\n## ", 1)[0]
    return [json.loads(block) for block in re.findall(r"```json\n(.*?)\n```", section, re.S)]


def test_ledger_records_a_live_verified_receipt_that_fits_schema() -> None:
    """The ledger's live run yields a schema-valid, verify-entry receipt."""
    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    receipts = _ledger_receipts()
    assert receipts, "ledger records no receipt"
    for receipt in receipts:
        validator.validate(receipt)
        assert receipt["producer"]["class"] == "verify-entry"
        assert receipt["acceptance_fingerprint"].startswith("git:")
    assert any(r["outcome"] == "live-verified" for r in receipts)


def test_ledger_records_the_failing_proof_run() -> None:
    """The ledger's mutation proof names the catching check and its failure."""
    text = " ".join(LEDGER.read_text(encoding="utf-8").split())
    for needle in ("Catching test", "agentbundle diff", "Exact mutation", "exit 1"):
        assert needle in text, needle
