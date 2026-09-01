"""Self-consistency of the frozen guide blockquote conversion ledger.

The ledger at `docs/specs/guide-typed-asides-conversion/notes/` records a
one-time conversion completed in 2026-08. It is history: nothing here reads
`guides/`, so no guide edit can redden this module. That is what makes it safe
to gate, and it is the whole reason these assertions live apart from the
release tripwires in `tools/test_guide_typed_asides.py`.

`check_ledger` is a pure function over already-parsed rows so every rule can be
killed against a mutated copy. `test_each_rule_is_falsifiable` does exactly
that, one mutation per rule, with a positive control on the unmutated copy — so
the falsifiability evidence re-runs in CI instead of living in a note.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTES = REPO_ROOT / "docs/specs/guide-typed-asides-conversion/notes"
LEDGER_PATH = NOTES / "blockquote-classification.jsonl"
BASELINE_PATH = NOTES / "blockquote-baseline-identities.jsonl"

ALLOWED_CLASSIFICATIONS = {"quotation", "note", "tip", "caution", "danger"}
ALLOWED_STATUSES = {"done", "superseded"}
REQUIRED_FIELDS = {
    "item",
    "path",
    "line",
    "content_sha256",
    "anchor",
    "classification",
    "status",
    "reason",
}
SHA256 = re.compile(r"[0-9a-f]{64}")

Row = dict[str, object]


def load_rows(path: Path) -> list[Row]:
    """Parse one JSONL file into rows, ignoring blank lines."""
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _identities(rows: list[Row]) -> list[tuple[object, object, object]]:
    return [(row["path"], row["line"], row["content_sha256"]) for row in rows]


def check_ledger(ledger: list[Row], baseline: list[Row]) -> list[str]:
    """Return every self-consistency violation, or an empty list."""
    violations: list[str] = []

    expected_items = list(range(1, len(ledger) + 1))
    if [row.get("item") for row in ledger] != expected_items:
        violations.append("ledger item numbers are not 1..N in order")
    if [row.get("item") for row in baseline] != list(range(1, len(baseline) + 1)):
        violations.append("baseline item numbers are not 1..N in order")

    for row in ledger:
        item = row.get("item")
        if set(row) != REQUIRED_FIELDS:
            violations.append(f"item {item}: field set is not the recorded eight")
            continue
        if row["status"] not in ALLOWED_STATUSES:
            violations.append(f"item {item}: status {row['status']!r} is not terminal")
        if row["classification"] not in ALLOWED_CLASSIFICATIONS:
            violations.append(
                f"item {item}: classification {row['classification']!r} is not allowed"
            )
        for field in ("reason", "anchor"):
            value = row[field]
            if not isinstance(value, str) or not value.strip():
                violations.append(f"item {item}: {field} is empty")
        if not SHA256.fullmatch(str(row["content_sha256"])):
            violations.append(f"item {item}: content_sha256 is not a sha256 digest")

    identities = _identities(ledger)
    if len(identities) != len(set(identities)):
        violations.append("duplicate (path, line, content_sha256) identities")

    anchors = [(row.get("path"), row.get("anchor")) for row in ledger]
    if len(anchors) != len(set(anchors)):
        violations.append("anchors are not unique within a guide")

    if identities != _identities(baseline):
        violations.append("ledger identities drifted from the frozen baseline")

    return violations


def test_the_frozen_ledger_is_self_consistent() -> None:
    """The shipped ledger satisfies every rule. Also the positive control."""
    violations = check_ledger(load_rows(LEDGER_PATH), load_rows(BASELINE_PATH))
    assert violations == [], "\n".join(violations)


def test_each_rule_is_falsifiable() -> None:
    """One killing mutation per rule, each against its own deep copy.

    Sharing one mutated structure across cases would let an earlier mutation
    satisfy a later case, so every case starts from a fresh copy.
    """
    ledger = load_rows(LEDGER_PATH)
    baseline = load_rows(BASELINE_PATH)

    def renumber(rows: list[Row]) -> None:
        rows[0]["item"] = 999

    def drop_field(rows: list[Row]) -> None:
        del rows[0]["reason"]

    def add_field(rows: list[Row]) -> None:
        rows[0]["unexpected"] = "x"

    def bad_status(rows: list[Row]) -> None:
        rows[0]["status"] = "pending"

    def bad_classification(rows: list[Row]) -> None:
        rows[0]["classification"] = "warning"

    def blank_reason(rows: list[Row]) -> None:
        rows[0]["reason"] = "   "

    def blank_anchor(rows: list[Row]) -> None:
        rows[0]["anchor"] = ""

    def bad_digest(rows: list[Row]) -> None:
        rows[0]["content_sha256"] = "not-a-digest"

    def duplicate_identity(rows: list[Row]) -> None:
        rows[1]["path"] = rows[0]["path"]
        rows[1]["line"] = rows[0]["line"]
        rows[1]["content_sha256"] = rows[0]["content_sha256"]

    def duplicate_anchor(rows: list[Row]) -> None:
        rows[1]["path"] = rows[0]["path"]
        rows[1]["anchor"] = rows[0]["anchor"]

    ledger_mutations = (
        ("item numbering", renumber),
        ("missing field", drop_field),
        ("extra field", add_field),
        ("non-terminal status", bad_status),
        ("unknown classification", bad_classification),
        ("blank reason", blank_reason),
        ("blank anchor", blank_anchor),
        ("malformed digest", bad_digest),
        ("duplicate identity", duplicate_identity),
        ("duplicate anchor", duplicate_anchor),
    )

    survivors: list[str] = []
    for name, mutate in ledger_mutations:
        mutated = copy.deepcopy(ledger)
        mutate(mutated)
        assert mutated != ledger, f"{name}: mutation did not apply"
        if not check_ledger(mutated, copy.deepcopy(baseline)):
            survivors.append(name)

    # Baseline drift is the one rule a ledger-side mutation cannot reach.
    drifted = copy.deepcopy(baseline)
    drifted[0]["content_sha256"] = "0" * 64
    assert drifted != baseline, "baseline drift: mutation did not apply"
    if not check_ledger(copy.deepcopy(ledger), drifted):
        survivors.append("baseline drift")

    assert survivors == [], f"rules with no killing mutation: {survivors}"
