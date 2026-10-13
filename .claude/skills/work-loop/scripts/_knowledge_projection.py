"""_knowledge_projection — pure projection of one delivery fact into a knowledge candidate.

Projection policy v1 has exactly one eligible source: a ``review-failure``
receipt that no supersession names.  It becomes one ``gotcha``
``knowledge-observation.v1`` whose text comes only from the typed review report
and finding the receipt derives from, after the ``knowledge-observation``
content-safety profile.  Every other fact yields an explicit ``none`` with a
closed reason code.

Pure: the projector reads only its arguments plus the content-safety policy
constants, writes nothing, and holds no state.  The same facts and the same
projection and content-policy versions yield byte-identical identities and
payloads in any process.

It does not judge subject or review-policy freshness.  A candidate is a past
lesson, so both fingerprints travel in ``source`` instead.

Self-contained: standard library plus the sibling ``_content_safety`` module,
loaded by path.  It validates the ``knowledge-observation.v1`` constraints in
code; it never opens, copies, or loads a delivery schema.

Python 3.11+.
"""

from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Final, NamedTuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

__all__ = [
    "MAX_OBSERVATION_BYTES",
    "NONE_REASONS",
    "PATTERNS",
    "PROJECTION_POLICY_VERSION",
    "Projection",
    "canonical_json",
    "content_policy_version",
    "is_identifier",
    "is_review_failure_receipt",
    "observation_id",
    "project_record",
]

_SCRIPTS_DIR: Final[Path] = Path(__file__).resolve().parent

# The wire constants below restate knowledge-observation.v1.  A pack test pins
# each one to the canonical schema at test time; no runtime code reads it.
PROJECTION_POLICY_VERSION: Final[str] = "projection-v1"
MAX_OBSERVATION_BYTES: Final[int] = 4096
_MAX_SCOPE_PATHS: Final[int] = 10
_MAX_TEXT_CHARS: Final[int] = 600
_MAX_RULE_REF_CHARS: Final[int] = 120
_MAX_PATH_CHARS: Final[int] = 240
_MAX_IDENTIFIER_CHARS: Final[int] = 128

# End of string in both Python and ECMA 262; `$` would admit a trailing LF in Python.
_END: Final[str] = r"(?![\s\S])"
_BAD_TEXT_CHARS: Final[str] = (
    r"\u0000-\u001f\u007f-\u009f\u00ad\u034f\u061c\u115f-\u1160\u17b4-\u17b5\u180b-\u180f"
    r"\u200b-\u200f\u2028-\u202e\u2060-\u206f\u3164\ud800-\udfff\ufe00-\ufe0f\ufeff\uffa0"
    r"\ufff9-\ufffb\U000E0000-\U000E0FFF"
)
_SEGMENT: Final[str] = (
    r"(?!\.{1,2}(?:/|" + _END + r"))[A-Za-z0-9._@+~-]*[A-Za-z0-9_@+~-]"
)
PATTERNS: Final[dict[str, str]] = {
    "identifier": r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}" + _END,
    "repository_path": r"^" + _SEGMENT + r"(?:/" + _SEGMENT + r")*" + _END,
    "text": r"^[^" + _BAD_TEXT_CHARS + r"]+" + _END,
    "observation_id": r"^knowledge-observation-sha256-[0-9a-f]{64}" + _END,
    "version_label": r"^[a-z0-9][a-z0-9.-]{0,31}" + _END,
}
_IDENTIFIER_RE: Final[re.Pattern[str]] = re.compile(PATTERNS["identifier"])
_PATH_RE: Final[re.Pattern[str]] = re.compile(PATTERNS["repository_path"])
_TEXT_RE: Final[re.Pattern[str]] = re.compile(PATTERNS["text"])

# The closed set of reasons a fact yields no observation.
NONE_REASONS: Final[frozenset[str]] = frozenset({
    "ineligible-record-kind",
    "ineligible-receipt",
    "superseded",
    "source-unresolved",
    "content-refused",
    "unrepresentable",
    "oversized",
})

_RECEIPT_KIND: Final[str] = "evidence-receipt.v1"
_TEXT_FIELDS: Final[tuple[tuple[str, str, int], ...]] = (
    # (observation field, finding field, max characters)
    ("rule_ref", "rule_ref", _MAX_RULE_REF_CHARS),
    ("observed", "observation", _MAX_TEXT_CHARS),
    ("reachable_path", "reachable_path", _MAX_TEXT_CHARS),
    ("actual_failure", "actual_failure", _MAX_TEXT_CHARS),
)


class Projection(NamedTuple):
    """The outcome for one fact: an observation, or ``None`` plus a closed reason."""

    observation: dict[str, Any] | None
    none_reason: str | None


_content_safety_module: ModuleType | None = None


def _content_safety() -> ModuleType:
    """Lazily load the sibling content-safety module by path, unregistered."""
    global _content_safety_module
    if _content_safety_module is None:
        path = _SCRIPTS_DIR / "_content_safety.py"
        if not stat.S_ISREG(os.lstat(path).st_mode):
            raise ImportError("_content_safety.py is not a regular file")
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            spec = importlib.util.spec_from_file_location("_kp_content_safety", str(path))
            if spec is None or spec.loader is None:
                raise ImportError(f"no import spec for {path}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.dont_write_bytecode = previous
        _content_safety_module = module
    return _content_safety_module


def content_policy_version() -> str:
    """Return the content-safety policy version the projection applies."""
    return str(_content_safety().POLICY_VERSION)


def canonical_json(value: object) -> str:
    """Serialize *value* with sorted keys, no extra whitespace, and ASCII escapes."""
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def is_identifier(value: object) -> bool:
    """Return True when *value* satisfies the identifier length and character class."""
    return (
        isinstance(value, str)
        and len(value) <= _MAX_IDENTIFIER_CHARS
        and _IDENTIFIER_RE.search(value) is not None
    )


def observation_id(spec_path: str, receipt_id: str, content_version: str) -> str:
    """Return the deterministic candidate identity for one source and version pair.

    The source identity is the spec directory plus the evidence receipt identity.
    """
    payload = canonical_json({
        "content_policy_version": content_version,
        "projection_policy_version": PROJECTION_POLICY_VERSION,
        "receipt_id": receipt_id,
        "spec_path": spec_path,
    })
    return "knowledge-observation-sha256-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_review_failure_receipt(receipt: dict) -> bool:
    """Return True for a receipt the review bridge wrote for a supported failure."""
    observation = receipt.get("observation")
    selector = receipt.get("selector")
    producer = receipt.get("producer")
    return (
        isinstance(observation, dict)
        and observation.get("type") == "review-failure"
        and isinstance(selector, dict)
        and selector.get("term") == "supported-review-failure"
        and isinstance(producer, dict)
        and producer.get("class") == "review-bridge"
    )


def _normalized_text(value: object, limit: int) -> tuple[str | None, str | None]:
    """Return ``(text, None)`` or ``(None, reason)`` for one free-text value.

    Whitespace runs, including every line terminator, collapse to one space so a
    candidate field is a single line.  A control, bidi, zero-width, or surrogate
    character, or an empty result, is refused; an over-long value is never cut.
    """
    if not isinstance(value, str):
        return None, "unrepresentable"
    text = " ".join(value.split())
    if not text or _TEXT_RE.search(text) is None:
        return None, "unrepresentable"
    if len(text) > limit:
        return None, "oversized"
    return text, None


def _scope_paths(finding: dict) -> list[str]:
    """Return the path-shaped evidence references of *finding*, sorted and bounded."""
    refs = finding.get("evidence_refs")
    if not isinstance(refs, list):
        return []
    paths = {
        ref for ref in refs
        if isinstance(ref, str) and len(ref) <= _MAX_PATH_CHARS and _PATH_RE.search(ref)
    }
    return sorted(paths)[:_MAX_SCOPE_PATHS]


def _build_observation(
    receipt: dict,
    *,
    spec_path: str,
    transaction_id: str,
    report: dict,
    finding: dict,
) -> Projection:
    """Build and bound one observation from a receipt and its source report and finding."""
    cs = _content_safety()
    version = content_policy_version()
    lineage = report.get("lineage")
    lineage = lineage if isinstance(lineage, dict) else {}
    identities = {
        "receipt_id": receipt.get("receipt_id"),
        "report_id": report.get("report_id"),
        "finding_id": finding.get("finding_id"),
        "criterion_ref": (receipt.get("lineage") or {}).get("criterion_ref"),
        "acceptance_fingerprint": receipt.get("acceptance_fingerprint"),
        "review_policy_fingerprint": lineage.get("review_policy_fingerprint"),
    }
    if not all(is_identifier(value) for value in identities.values()):
        return Projection(None, "unrepresentable")

    raw_texts = [finding.get(source_field) for _, source_field, _ in _TEXT_FIELDS]
    if not all(isinstance(text, str) for text in raw_texts):
        return Projection(None, "unrepresentable")
    normalized: list[str] = []
    for (_, _, limit), raw in zip(_TEXT_FIELDS, raw_texts, strict=True):
        text, reason = _normalized_text(raw, limit)
        if text is None:
            return Projection(None, reason)
        normalized.append(text)
    # The profile runs on the raw text, before normalization, so a control
    # character is refused rather than escaped away by JSON serialization.
    decision = cs.check_content_safety(
        "knowledge-observation",
        "\n".join(raw_texts).encode("utf-8", errors="surrogatepass"),
        source_record_id=str(identities["receipt_id"]),
    )
    if not decision.accepted:
        return Projection(None, "content-refused")

    obs_id = observation_id(spec_path, str(identities["receipt_id"]), version)
    wrapped: dict[str, dict[str, Any]] = {}
    for (field, _, _), text in zip(_TEXT_FIELDS, normalized, strict=True):
        untrusted = dataclasses.asdict(cs.wrap_as_untrusted(obs_id, field, text))
        wrapped[field] = {"schema_version": 1, **untrusted}

    observation: dict[str, Any] = {
        "schema_version": 1,
        "observation_id": obs_id,
        "kind": "gotcha",
        "projection_policy_version": PROJECTION_POLICY_VERSION,
        "content_policy_version": version,
        "source": {
            "spec_path": spec_path,
            "transaction_id": transaction_id,
            "receipt_id": identities["receipt_id"],
            "report_id": identities["report_id"],
            "finding_id": identities["finding_id"],
            "criterion_ref": identities["criterion_ref"],
            "acceptance_fingerprint": identities["acceptance_fingerprint"],
            "review_policy_fingerprint": identities["review_policy_fingerprint"],
        },
        "scope_paths": _scope_paths(finding),
        **wrapped,
    }
    if len(canonical_json(observation).encode("utf-8")) > MAX_OBSERVATION_BYTES:
        return Projection(None, "oversized")
    return Projection(observation, None)


def project_record(
    record_kind: str,
    record: dict,
    *,
    spec_path: str,
    transaction_id: str,
    superseded: bool,
    report: dict | None,
    finding: dict | None,
) -> Projection:
    """Project one delivery fact into an observation or an explicit ``none``.

    *record_kind* and *record* name the fact.  *superseded* says whether an
    admitted supersession in the same log names the receipt.  *report* and
    *finding* are the typed source records the receipt's supported assessment
    derives from, or ``None`` when the log does not resolve them.
    """
    if record_kind != _RECEIPT_KIND:
        return Projection(None, "ineligible-record-kind")
    if not is_review_failure_receipt(record):
        return Projection(None, "ineligible-receipt")
    if superseded:
        return Projection(None, "superseded")
    if report is None or finding is None:
        return Projection(None, "source-unresolved")
    if not is_identifier(transaction_id):
        return Projection(None, "unrepresentable")
    return _build_observation(
        record,
        spec_path=spec_path,
        transaction_id=transaction_id,
        report=report,
        finding=finding,
    )
