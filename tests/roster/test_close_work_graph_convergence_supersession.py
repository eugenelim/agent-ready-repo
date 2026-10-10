"""AC-0014: the closure check's frozen spec points at its partial supersession."""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = REPO_ROOT / "docs/specs/closure-eligibility-check/spec.md"
STATUS_PREFIX = "- **Status:**"

# SHA-256 of the spec with its Status line removed, computed at base commit aa5a5048e.
BODY_SHA256 = "327d62776d5e8145f173264b0d80b32d59a6b0cb4b7a2b2f1b7d59fd7006e5ec"


def _lines() -> list[str]:
    return SPEC.read_text(encoding="utf-8").splitlines(keepends=True)


def test_status_line_names_the_superseding_spec_and_criteria() -> None:
    status = next(line for line in _lines() if line.startswith(STATUS_PREFIX))
    value = status[len(STATUS_PREFIX) :].strip()
    assert value.startswith("Shipped (superseded in part by")
    assert "close-work-intent-graph-convergence/spec.md" in value
    for criterion in ("0024", "0025", "0037"):
        assert criterion in value


def test_body_is_unchanged_apart_from_the_status_line() -> None:
    body = "".join(line for line in _lines() if not line.startswith(STATUS_PREFIX))
    assert hashlib.sha256(body.encode("utf-8")).hexdigest() == BODY_SHA256
