"""Contracts for the portable RFC template.

Roster-owned rather than pack-owned: `packs/governance-extras/tests/skills/
new-rfc` is declared in `_NO_RUNNER` as never gated, so a guard placed there
could not fail in CI.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "packs/governance-extras/.apm/skills/new-rfc"


def test_rfc_author_placeholder_is_platform_neutral() -> None:
    """The bundled RFC template must not assume a specific account host."""
    template = (SKILL_ROOT / "assets/rfc.md").read_text(encoding="utf-8")

    assert "- **Author:** <account-handle>" in template
    assert "<github-handle>" not in template


def test_rfc_template_placeholder_has_behavior_eval() -> None:
    """The platform-neutral placeholder must remain covered by an eval."""
    payload = json.loads(
        (SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8")
    )
    case = next(
        item
        for item in payload["evals"]
        if item["id"] == "template-platform-neutral-author"
    )

    assert "`<account-handle>`" in case["expected_output"]
    assert "Does not use `<github-handle>`" in case["assertions"]
