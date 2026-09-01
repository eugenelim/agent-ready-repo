"""Self-consistency of the frozen guide blockquote conversion ledger.

The ledger at `docs/specs/guide-typed-asides-conversion/notes/` records a
one-time conversion completed in 2026-08. It is history: nothing here reads
`guides/`, so no guide edit can redden this module. That is what makes it safe
to gate, and it is the whole reason these assertions live apart from the
release tripwires in `tools/test_guide_typed_asides.py`.

`check_ledger` is a pure function over already-parsed rows so every rule can be
killed against a mutated copy. `test_each_rule_is_falsifiable` does exactly
that, and each case names the violation substring its rule must produce.
Asserting only that *some* violation came back would not kill a rule: several
mutations also perturb a `(path, line, content_sha256)` tuple, so the baseline
comparison fires for them too and three rules could be deleted with the suite
still green.
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
    """Identity triples, tolerating a row that is missing one of the three.

    `.get` rather than indexing: a row that failed the field-set rule still
    reaches here, and a corrupted JSONL merge should surface as a violation
    rather than as a traceback out of a function that promises a list.
    """
    return [
        (row.get("path"), row.get("line"), row.get("content_sha256"))
        for row in rows
    ]


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
    """One killing mutation per rule, each asserting its own violation.

    Every case starts from a fresh deep copy, so an earlier mutation cannot
    satisfy a later case, and each asserts the substring only its own rule
    emits — otherwise a mutation that also perturbs an identity tuple would be
    "killed" by the baseline comparison while its own rule went unproven.
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

    def drop_identity_field(rows: list[Row]) -> None:
        del rows[0]["path"]

    ledger_mutations = (
        ("item numbering", renumber, "item numbers are not 1..N in order"),
        ("missing field", drop_field, "field set is not the recorded eight"),
        ("extra field", add_field, "field set is not the recorded eight"),
        ("non-terminal status", bad_status, "is not terminal"),
        ("unknown classification", bad_classification, "is not allowed"),
        ("blank reason", blank_reason, "reason is empty"),
        ("blank anchor", blank_anchor, "anchor is empty"),
        ("malformed digest", bad_digest, "is not a sha256 digest"),
        (
            "duplicate identity",
            duplicate_identity,
            "duplicate (path, line, content_sha256) identities",
        ),
        ("duplicate anchor", duplicate_anchor, "anchors are not unique within a guide"),
        (
            "row missing an identity field",
            drop_identity_field,
            "field set is not the recorded eight",
        ),
    )

    survivors: list[str] = []
    for name, mutate, expected in ledger_mutations:
        mutated = copy.deepcopy(ledger)
        mutate(mutated)
        assert mutated != ledger, f"{name}: mutation did not apply"
        violations = check_ledger(mutated, copy.deepcopy(baseline))
        if not any(expected in violation for violation in violations):
            survivors.append(f"{name} (expected {expected!r}, got {violations[:3]})")

    # Baseline drift is the one rule a ledger-side mutation cannot reach.
    drifted = copy.deepcopy(baseline)
    drifted[0]["content_sha256"] = "0" * 64
    assert drifted != baseline, "baseline drift: mutation did not apply"
    violations = check_ledger(copy.deepcopy(ledger), drifted)
    if not any("drifted from the frozen baseline" in v for v in violations):
        survivors.append("baseline drift")

    assert survivors == [], f"rules with no killing mutation: {survivors}"
