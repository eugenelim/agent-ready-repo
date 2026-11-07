"""``max_review_retries`` keeps its merge-base value (review-obligation-policy AC-0031).

The review-tier work adds keys to the work-loop review rules but must leave the
shared pre-approval review budget alone. Repository-level, so it lives here
rather than in the core pack's tests.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RULES = "packs/core/.apm/skills/work-loop/review-rules.json"


def _git(*args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )
    return done.stdout.strip() if done.returncode == 0 else ""


def test_max_review_retries_equals_its_merge_base_value() -> None:
    """AC-0031: the shipped ``max_review_retries`` equals its value at the merge base."""
    base = _git("merge-base", "origin/main", "HEAD")
    if not base:
        pytest.skip("no origin/main merge base in this checkout")
    blob = _git("show", f"{base}:{RULES}")
    if not blob:
        pytest.skip("review-rules.json is absent at the merge base")
    shipped = json.loads((ROOT / RULES).read_text(encoding="utf-8"))
    assert shipped["max_review_retries"] == json.loads(blob)["max_review_retries"]
