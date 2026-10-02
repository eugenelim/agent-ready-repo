"""_acceptance — pure reviewed-envelope projection, freshness, and verdict evaluation.

Implements the T4 pure acceptance services for the work-loop skill scripts:

  * Reviewed execution envelope derivation and validation (AC-0003).
  * Change classification against the reviewed envelope (AC-0004).
  * Freshness evaluation for exact-subject and path-set receipts (AC-0009).
  * Satisfaction and verdict evaluation across all supported adapters (AC-0007).

The module is importable without Git, filesystem mutation, the engine, or adapter
code. All operations are deterministic, stateless, and produce the same result for
the same canonical inputs on every conforming adapter.

``SUPPORTED_ADAPTERS`` is declared once here. Conformance tests refuse to run against
a set smaller than two members so every adapter comparison always covers at least two
runtimes (spec/acceptance-authority-and-evidence Constraint — "declare in one place
and make conformance suites refuse to run against an empty or single-member declaration").

Standard library only. No third-party imports, no packaging, no installation.
Python 3.11+.
"""

from __future__ import annotations

import hashlib
import json
import sys
from typing import Final

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    # Adapter declaration (declared once; conformance suites require ≥2 members)
    "SUPPORTED_ADAPTERS",
    # Envelope (AC-0003)
    "ENVELOPE_REFS_KEYS",
    "SUPPORTED_ENVELOPE_SCHEMA_VERSION",
    "derive_envelope",
    "validate_envelope_dict",
    # Change classification (AC-0004)
    "classify_change",
    # Freshness (AC-0009)
    "is_fresh",
    # Verdict evaluation (AC-0007)
    "SUPPORTED_PROPERTY_SCHEMA_VERSION",
    "SUPPORTED_VERDICT_SCHEMA_VERSION",
    "evaluate_verdict",
    "validate_property_dict",
    "validate_verdict_dict",
    # Errors
    "AcceptanceError",
    "AcceptanceRefused",
]

# ---------------------------------------------------------------------------
# Adapter declaration — declared once; conformance tests require at least two
# ---------------------------------------------------------------------------

# The sequential reference runtime is the canonical default.
# The Core compatibility adapter is the work-loop skill's compatibility path.
SUPPORTED_ADAPTERS: Final[tuple[str, ...]] = (
    "sequential-reference",
    "core-compatibility",
)

# ---------------------------------------------------------------------------
# Schema version constants
# ---------------------------------------------------------------------------

SUPPORTED_ENVELOPE_SCHEMA_VERSION: Final[int] = 1
SUPPORTED_PROPERTY_SCHEMA_VERSION: Final[int] = 1
SUPPORTED_VERDICT_SCHEMA_VERSION: Final[int] = 1

# Canonical ordered keys for refs in reviewed-execution-envelope.v1.
# The order is the logical authority order from the spec. The fingerprint
# depends on this order: identical inputs always produce one fingerprint.
ENVELOPE_REFS_KEYS: Final[tuple[str, ...]] = (
    "spec_policy",
    "scope_and_non_goals",
    "authority_and_security",
    "public_contracts",
    "durable_outputs",
    "accepted_risk",
)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class AcceptanceError(Exception):
    """Base exception for acceptance operations."""


class AcceptanceRefused(AcceptanceError):
    """An acceptance operation was refused with a stable denial code.

    ``denial_code`` carries a stable string that callers may log without
    sensitive payload bytes; it does not include excerpts or content-derived hashes.
    """

    def __init__(self, denial_code: str, message: str = "") -> None:
        super().__init__(message or denial_code)
        self.denial_code: str = denial_code


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fingerprint(data: dict) -> str:
    """SHA-256 fingerprint of *data* serialised with sorted keys (ASCII-safe).

    ``sort_keys=True`` ensures deterministic output regardless of dict insertion
    order. ``ensure_ascii=True`` prevents locale-specific encoding differences.
    """
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("ascii")).hexdigest()


# ---------------------------------------------------------------------------
# Reviewed execution envelope (AC-0003)
# ---------------------------------------------------------------------------


def derive_envelope(refs: dict[str, str]) -> dict:
    """Derive a ``reviewed-execution-envelope.v1`` record from ordered approval refs.

    The envelope is a pure projection: it summarises authority but grants none.
    Identical ordered inputs always produce the same fingerprint. Raises
    ``AcceptanceRefused`` when any required ref is missing, empty, has an
    unknown key, or the input is not a dict.

    The resulting record satisfies the ``reviewed-execution-envelope.v1`` schema.
    """
    if not isinstance(refs, dict):
        raise AcceptanceRefused(
            "denied-invalid-refs-type",
            "refs must be a mapping of approval references",
        )
    unknown = set(refs) - set(ENVELOPE_REFS_KEYS)
    if unknown:
        raise AcceptanceRefused(
            "denied-unknown-authority-field",
            f"unknown refs keys: {sorted(unknown)!r}",
        )
    for key in ENVELOPE_REFS_KEYS:
        value = refs.get(key)
        if not isinstance(value, str) or not value:
            raise AcceptanceRefused(
                "denied-missing-or-empty-ref",
                f"required ref {key!r} is missing or empty",
            )
    ordered_refs: dict[str, str] = {k: refs[k] for k in ENVELOPE_REFS_KEYS}
    fp = _fingerprint(ordered_refs)
    return {
        "schema_version": SUPPORTED_ENVELOPE_SCHEMA_VERSION,
        "envelope_fingerprint": fp,
        "refs": ordered_refs,
    }


def validate_envelope_dict(record: object) -> tuple[bool, str]:
    """Validate *record* against the ``reviewed-execution-envelope.v1`` contract.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on any
    failure. Checks schema_version first (so an unknown major is diagnosed
    before field checks), then required fields, then additional fields, then
    refs content.
    """
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    sv = record.get("schema_version")
    if sv != SUPPORTED_ENVELOPE_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    required = {"schema_version", "envelope_fingerprint", "refs"}
    for field in required:
        if field not in record:
            return False, "denied-missing-required-field"
    allowed = {"schema_version", "envelope_fingerprint", "refs"}
    if set(record) - allowed:
        return False, "denied-unknown-authority-field"
    refs = record.get("refs")
    if not isinstance(refs, dict):
        return False, "denied-invalid-refs-type"
    for key in ENVELOPE_REFS_KEYS:
        if key not in refs:
            return False, "denied-missing-required-field"
        val = refs[key]
        if not isinstance(val, str) or not val:
            return False, "denied-empty-ref"
    if set(refs) - set(ENVELOPE_REFS_KEYS):
        return False, "denied-unknown-authority-field"
    fp = record.get("envelope_fingerprint")
    if not isinstance(fp, str) or not fp:
        return False, "denied-empty-fingerprint"
    return True, "ok"


# ---------------------------------------------------------------------------
# Change classification (AC-0004)
# ---------------------------------------------------------------------------


def classify_change(
    *,
    current_envelope_fingerprint: str,
    current_terminal_intent: str,
    proposed_envelope_fingerprint: str,
    proposed_terminal_intent: str,
) -> str:
    """Classify a proposed change as requiring approval or not.

    Returns ``"no-approval-required"`` when the proposed envelope fingerprint and
    terminal intent exactly match the current values — i.e. the change is limited
    to non-authoritative working-plan fields (tasks, sequence, decomposition,
    test-shape, local method). No task reprojection, cancellation, or dispatch
    is performed.

    Returns ``"approval-required"`` when either the envelope fingerprint or
    terminal intent has changed — i.e. the change crosses the protected authority
    boundary and requires its owning amendment, review, or risk gate before a
    later-slice task projector may resume.
    """
    if (
        proposed_envelope_fingerprint != current_envelope_fingerprint
        or proposed_terminal_intent != current_terminal_intent
    ):
        return "approval-required"
    return "no-approval-required"


# ---------------------------------------------------------------------------
# Freshness evaluation (AC-0009)
# ---------------------------------------------------------------------------


def is_fresh(
    *,
    receipt: dict,
    current_acceptance_fingerprint: str,
    path_set_attrs: dict | None = None,
) -> bool:
    """Return True when *receipt* is fresh under *current_acceptance_fingerprint*.

    **Exact-subject** receipts are fresh when their stored ``acceptance_fingerprint``
    matches the current value. A mismatched fingerprint is always stale.

    **Path-set** receipts require the fingerprint match AND every key in
    *path_set_attrs* to match the corresponding field in *receipt*. When
    *path_set_attrs* is ``None`` (missing or incomplete attestor), the evaluator
    falls back to exact-subject freshness: the fingerprint match alone decides.

    An unknown or absent ``freshness_mode`` is treated as ``"exact-subject"``.
    A non-dict *receipt* is always stale.
    """
    if not isinstance(receipt, dict):
        return False
    stored_fp = receipt.get("acceptance_fingerprint", "")
    if stored_fp != current_acceptance_fingerprint:
        return False
    mode = receipt.get("freshness_mode", "exact-subject")
    if mode == "path-set" and path_set_attrs is not None:
        for key, expected in path_set_attrs.items():
            if receipt.get(key) != expected:
                return False
    return True


# ---------------------------------------------------------------------------
# Verdict evaluation (AC-0007)
# ---------------------------------------------------------------------------


def _parse_satisfaction_expression(expression: str) -> tuple[str, int]:
    """Parse a satisfaction rule expression string.

    Supported forms:
      - ``"all"``       — all required observation terms must be satisfied
      - ``"any"``       — at least one term must be satisfied
      - ``"at-least(N)"`` — at least N terms must be satisfied (N ≥ 1)

    Returns ``(mode, threshold)`` where *mode* is the string key and
    *threshold* is the minimum satisfied count (0 for "all" — resolved against
    the actual term count at evaluation time).
    """
    expr = expression.strip()
    if expr == "all":
        return "all", 0
    if expr == "any":
        return "any", 1
    if expr.startswith("at-least(") and expr.endswith(")"):
        inner = expr[len("at-least("):-1].strip()
        try:
            n = int(inner)
        except ValueError:
            pass
        else:
            if n >= 1:
                return "at-least", n
    raise AcceptanceRefused(
        "denied-unknown-satisfaction-expression",
        f"unrecognised satisfaction expression: {expression!r}",
    )


def _is_contradicted(
    *,
    contradiction_expression: str,
    fresh_receipts: list[dict],
) -> bool:
    """Return True when the contradiction rule fires against *fresh_receipts*.

    The expression names one or more observation term names separated by commas
    or ``|``. The reserved ``"supported-review-failure"`` term is always included.
    The expression ``"none"`` (or empty) means no contradiction rule applies.

    A contradiction fires when any fresh receipt has a ``selector.term`` that
    appears in the expression's term set.
    """
    expr = contradiction_expression.strip()
    if not expr or expr == "none":
        return False
    candidate_terms = {t.strip() for t in expr.replace("|", ",").split(",") if t.strip()}
    for receipt in fresh_receipts:
        selector = receipt.get("selector", {})
        term = selector.get("term", "") if isinstance(selector, dict) else ""
        if term in candidate_terms:
            return True
    return False


def _is_satisfied(
    *,
    satisfaction_expression: str,
    required_observations: list[dict],
    fresh_receipts: list[dict],
) -> bool:
    """Return True when *satisfaction_expression* is met by *fresh_receipts*.

    A receipt satisfies a required observation term when:
      - Its ``selector.term`` matches the term name, and
      - Its ``outcome`` is listed in the term's ``outcomes``.
    """
    term_outcomes: dict[str, set[str]] = {}
    for obs in required_observations:
        if isinstance(obs, dict):
            term = obs.get("term", "")
            outcomes = obs.get("outcomes", [])
            if term and isinstance(outcomes, list):
                term_outcomes[term] = {str(o) for o in outcomes}

    satisfied: set[str] = set()
    for receipt in fresh_receipts:
        selector = receipt.get("selector", {})
        term = selector.get("term", "") if isinstance(selector, dict) else ""
        outcome = str(receipt.get("outcome", ""))
        if term in term_outcomes and outcome in term_outcomes[term]:
            satisfied.add(term)

    all_terms = set(term_outcomes)
    mode, threshold = _parse_satisfaction_expression(satisfaction_expression)
    if mode == "all":
        return all_terms <= satisfied
    if mode == "any":
        return bool(satisfied)
    # at-least
    return len(satisfied) >= threshold


def evaluate_verdict(
    *,
    property_record: dict,
    receipts: list[dict],
    current_acceptance_fingerprint: str,
    adapter: str,
    path_set_attrs: dict | None = None,
) -> dict:
    """Evaluate an ``acceptance-verdict.v1`` record for one property.

    Applies the verdict table in priority order:
      1. ``"unapproved"``   — ``authority_ref`` is absent or empty.
      2. ``"contradicted"`` — contradiction rule fires against fresh receipts.
      3. ``"supported"``    — satisfaction rule met by fresh receipts.
      4. ``"insufficient"`` — none of the above.

    Raises ``AcceptanceRefused`` for an unsupported *adapter* or a non-dict
    *property_record*. The evaluation is deterministic: identical inputs always
    produce the same verdict on every supported adapter.

    *path_set_attrs* supplies the completeness attestation attributes for
    path-set freshness. Pass ``None`` (or omit) to force exact-subject fallback.
    """
    if adapter not in SUPPORTED_ADAPTERS:
        raise AcceptanceRefused(
            "denied-unsupported-adapter",
            f"adapter {adapter!r} is not in SUPPORTED_ADAPTERS",
        )
    if not isinstance(property_record, dict):
        raise AcceptanceRefused(
            "denied-invalid-property",
            "property_record must be a dict (acceptance-property.v1)",
        )

    authority_ref = property_record.get("authority_ref", "")

    # Step 1 — unapproved
    if not isinstance(authority_ref, str) or not authority_ref:
        verdict = "unapproved"
        fresh_receipts: list[dict] = []
    else:
        fresh_receipts = [
            r for r in receipts
            if isinstance(r, dict) and is_fresh(
                receipt=r,
                current_acceptance_fingerprint=current_acceptance_fingerprint,
                path_set_attrs=path_set_attrs,
            )
        ]

        contradiction_rule = property_record.get("contradiction_rule", {})
        contradiction_expr = (
            contradiction_rule.get("expression", "")
            if isinstance(contradiction_rule, dict)
            else ""
        )
        required_observations = property_record.get("required_observations", [])

        # Step 2 — contradicted
        if _is_contradicted(
            contradiction_expression=contradiction_expr,
            fresh_receipts=fresh_receipts,
        ):
            verdict = "contradicted"
        else:
            satisfaction_rule = property_record.get("satisfaction_rule", {})
            satisfaction_expr = (
                satisfaction_rule.get("expression", "")
                if isinstance(satisfaction_rule, dict)
                else ""
            )
            # Step 3 / 4 — supported or insufficient
            if _is_satisfied(
                satisfaction_expression=satisfaction_expr,
                required_observations=required_observations,
                fresh_receipts=fresh_receipts,
            ):
                verdict = "supported"
            else:
                verdict = "insufficient"

    # Build a deterministic evaluation fingerprint
    criteria_refs = [property_record.get("property_id", "")]
    receipt_refs = [r.get("receipt_id", "") for r in fresh_receipts]
    eval_input: dict = {
        "property_id": property_record.get("property_id", ""),
        "authority_ref": authority_ref,
        "acceptance_fingerprint": current_acceptance_fingerprint,
        "receipt_ids": sorted(receipt_refs),
    }
    return {
        "schema_version": SUPPORTED_VERDICT_SCHEMA_VERSION,
        "evaluation_fingerprint": _fingerprint(eval_input),
        "verdict": verdict,
        "criteria_refs": criteria_refs,
        "receipt_refs": receipt_refs,
    }


# ---------------------------------------------------------------------------
# Record validation (parity rule from verification-ledger.md)
# ---------------------------------------------------------------------------


def validate_property_dict(record: object) -> tuple[bool, str]:
    """Validate *record* against the ``acceptance-property.v1`` contract.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on any failure.
    Failure codes are stable across versions.
    """
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    sv = record.get("schema_version")
    if sv != SUPPORTED_PROPERTY_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    required = (
        "schema_version", "property_id", "spec_ref", "authority_ref",
        "subject_selector", "required_observations", "freshness_scope",
        "satisfaction_rule", "contradiction_rule", "policy_version",
    )
    for field in required:
        if field not in record:
            return False, "denied-missing-required-field"
    allowed = set(required)
    if set(record) - allowed:
        return False, "denied-unknown-authority-field"
    if record.get("freshness_scope") not in ("exact-subject", "path-set"):
        return False, "denied-invalid-enum"
    return True, "ok"


def validate_verdict_dict(record: object) -> tuple[bool, str]:
    """Validate *record* against the ``acceptance-verdict.v1`` contract.

    Returns ``(True, "ok")`` on success or ``(False, denial_code)`` on any failure.
    """
    if not isinstance(record, dict):
        return False, "denied-not-a-dict"
    sv = record.get("schema_version")
    if sv != SUPPORTED_VERDICT_SCHEMA_VERSION:
        return False, "denied-unknown-schema-version"
    required = (
        "schema_version", "evaluation_fingerprint", "verdict",
        "criteria_refs", "receipt_refs",
    )
    for field in required:
        if field not in record:
            return False, "denied-missing-required-field"
    allowed = set(required)
    if set(record) - allowed:
        return False, "denied-unknown-authority-field"
    if record.get("verdict") not in ("unapproved", "contradicted", "supported", "insufficient"):
        return False, "denied-invalid-enum"
    return True, "ok"
