#!/usr/bin/env python3
"""
contract.py — the shared, versioned output-contract frontmatter builder.

Every extraction `file-to-markdown` produces — across both of its output
shapes (``convert.py``'s document + image-via-Docling path, and
``reconcile.py``'s diagram/image branch) — carries one YAML frontmatter block
recording provenance and a quality/confidence signal. This module is the single
builder that emits it, so the call sites cannot drift.

Design notes:
  * **No PyYAML.** The emitter is the skill's existing hand-rolled stdlib
    emitter (lifted from ``reconcile.py``), extended here. ``yaml.safe_dump``
    would add a dependency the skill deliberately avoids *and* reorder keys
    alphabetically, breaking the image branch's byte-stability.
  * **Injection-safe.** Every string *value* is escaped/quoted —
    backslash, double-quote, and (the load-bearing fix over the original
    emitter) newline / carriage-return / tab — so extracted content containing
    ``---``, a newline, or a ``key:`` line cannot break out of its scalar and
    forge or truncate the contract. The contract is the *leading* ``---``-fenced
    block only; the extracted body sits below it, and a compliant frontmatter
    parser stops at the first closing ``---``.
  * **Additive + byte-stable.** The two new keys (``contract-version``,
    ``tier``) are top-level; the quality signal stays nested under
    ``ingestion-quality`` on both branches. A caller passes its own ordered
    top-level ``fields`` (so the image branch's existing key order is preserved
    verbatim); the builder owns only the two new keys, the quality block, and
    validation.
"""
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Mapping

# The frontmatter contract version. Consumers key on this to detect the shape;
# changing its *meaning* is a contract change (hence the field). Starts at 1.0.
CONTRACT_VERSION = "1.0"

# Tier enum. The skill only ever emits 0/1/2; Tier 3 (managed API)
# is unreachable from this code — there is no network egress.
TIER_0 = "0-no-ml"           # stdlib / ordinary parsers, no model
TIER_1 = "1-agent-vision"    # in-session agent vision read (the image branch)
TIER_2 = "2-approved-ml"     # Docling (approved ML)
TIER_3 = "3-managed-api"     # managed OCR/extraction API — never reached here
TIERS = frozenset({TIER_0, TIER_1, TIER_2, TIER_3})

CONFIDENCE_LEVELS = frozenset({"high", "medium", "low"})

# Keys the builder owns; a caller's `fields` must not carry them, or it could
# forge the contract by shadowing a builder-set key.
_RESERVED = frozenset({"contract-version", "tier", "ingestion-quality"})


def build_frontmatter(
    *,
    tier: str,
    extraction_confidence: str,
    requires_review: bool,
    fields: Mapping[str, Any],
    ingestion_quality_extra: Mapping[str, Any] | None = None,
) -> str:
    """Return the fenced YAML frontmatter block (no trailing newline).

    ``fields`` is the branch's ordered top-level keys and MUST include
    ``source-file``, ``content-type``, and ``ingestion-date`` (the required
    fields whose position differs per branch, so the caller owns their order).
    The builder prepends ``contract-version`` + ``tier`` and appends the
    ``ingestion-quality`` block ({extraction-confidence, *extras, requires-review}),
    so the quality signal is builder-owned and identical across branches.
    """
    if tier not in TIERS:
        raise ValueError(f"unknown tier {tier!r}; expected one of {sorted(TIERS)}")
    if extraction_confidence not in CONFIDENCE_LEVELS:
        raise ValueError(
            f"unknown extraction-confidence {extraction_confidence!r}; "
            f"expected one of {sorted(CONFIDENCE_LEVELS)}"
        )
    reserved_in_fields = _RESERVED & set(fields)
    if reserved_in_fields:
        raise ValueError(
            f"fields must not carry builder-owned keys {sorted(reserved_in_fields)}"
        )
    for required in ("source-file", "content-type", "ingestion-date"):
        if required not in fields:
            raise ValueError(f"fields is missing required key {required!r}")

    block: "OrderedDict[str, Any]" = OrderedDict()
    block["contract-version"] = CONTRACT_VERSION
    block["tier"] = tier
    for k, v in fields.items():
        block[k] = v

    iq: "OrderedDict[str, Any]" = OrderedDict()
    iq["extraction-confidence"] = extraction_confidence
    if ingestion_quality_extra:
        for k, v in ingestion_quality_extra.items():
            iq[k] = v
    iq["requires-review"] = bool(requires_review)
    block["ingestion-quality"] = iq

    return _yaml_block(block)


def now_iso() -> str:
    """UTC ingestion timestamp, matching the image branch's format."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- Hand-rolled stdlib YAML emitter (no PyYAML) ---------------------------
# Lifted from reconcile.py and extended with newline/CR/tab escaping.


def _yaml_block(d: Mapping[str, Any]) -> str:
    """Minimal YAML emitter for flat-with-nesting frontmatter.

    No anchors, no multi-line strings — every scalar is a double-quoted,
    fully-escaped single line, so a value can never break out of its scalar."""
    lines = ["---"]
    _emit(d, lines, 0)
    lines.append("---")
    return "\n".join(lines)


def _emit(d: Mapping[str, Any], lines: list[str], indent: int) -> None:
    pad = "  " * indent
    for k, v in d.items():
        if isinstance(v, Mapping):
            lines.append(f"{pad}{k}:")
            _emit(v, lines, indent + 1)
        elif isinstance(v, bool):
            lines.append(f"{pad}{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{pad}{k}: null")
        elif isinstance(v, (int, float)):
            lines.append(f"{pad}{k}: {v}")
        else:
            lines.append(f'{pad}{k}: "{_escape(str(v))}"')


def _escape(s: str) -> str:
    """Escape a string for a YAML double-quoted scalar.

    Backslash first (so we don't double-escape the backslashes the later
    replacements insert), then the double-quote, then the whitespace escapes.
    Escaping the newline is the load-bearing fix over the original emitter: a
    raw newline inside a ``"..."`` scalar would break the fence."""
    return (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
