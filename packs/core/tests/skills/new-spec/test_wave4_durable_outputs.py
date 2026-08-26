"""Wave 4 durable-output planning contracts for new-spec."""

from __future__ import annotations

import json
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm/skills/new-spec/SKILL.md"
SPEC_ASSET = PACK_ROOT / ".apm/skills/new-spec/assets/spec.md"
PLAN_ASSET = PACK_ROOT / ".apm/skills/new-spec/assets/plan.md"
EVALS = PACK_ROOT / ".apm/skills/new-spec/evals/evals.json"


def _compact(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_new_spec_requires_repository_specific_durable_outputs() -> None:
    text = _compact(SKILL)

    assert "Durable outputs" in text
    assert "repository-specific" in text
    for role in (
        "user-facing promise",
        "current product truth",
        "current architecture",
        "decision rationale",
        "interface compatibility",
        "operations",
        "maintainer procedure",
        "release history",
        "reusable learning",
    ):
        assert role in text
    assert "explicit destination; declared repository policy or optional configuration" in text
    assert "established in-repository convention" in text
    assert "confirmation-required ambiguity" in text
    assert "destination-required" in text
    assert "`none` requires an explicit rationale" in text


def test_new_spec_shaping_freshness_and_user_docs_first_are_explicit() -> None:
    text = _compact(SKILL)

    assert "read each applicable existing surface as a whole" in text
    assert "isolated snippet" in text
    assert "established user-documentation surface exists" in text
    assert "draft or update that surface before implementation approval" in text
    assert "whole-surface refresh work" in text
    assert "Architecture and maintainer outputs stay terse" in text
    assert "link to implementation, contracts, tests, and verified commands" in text


def test_temporary_full_mode_records_keep_rigor_and_explicit_retention() -> None:
    text = _compact(SKILL)

    for field in (
        "intended retention class",
        "local-only",
        "PR-only",
        "repository-durable",
        "exact locator and fingerprint",
        "every required reader",
        "stable post-closeout evidence owner",
        "intended retention or immediate-disposition boundary",
    ):
        assert field in text
    assert "another person, worktree, CI job, or external control plane" in text
    assert "approval record, not a new published schema" in text


def test_new_spec_templates_carry_output_plan_and_follow_on_contract() -> None:
    spec = _compact(SPEC_ASSET)
    plan = _compact(PLAN_ASSET)

    assert "## Durable Outputs" in spec
    for field in (
        "Semantic role",
        "Applicability",
        "Destination",
        "Owner",
        "Expected evidence",
        "Closeout condition",
    ):
        assert field in spec
    assert "## Follow-ons" in spec
    assert "A newly Shipped spec has no open Acceptance Criteria" in spec
    assert "Do not use `(deferred: <slug>)` as a new shipping exception" in spec

    assert "## Durable-output map" in plan
    assert "maps each task to the spec's Durable Outputs" in plan
    assert "planned output, implementation evidence, and closeout evidence" in plan
    assert "non-inferable design fact" in plan
    assert "semantic owner" in plan


def test_new_spec_evals_cover_wave4_output_and_amendment_rules() -> None:
    evals = json.loads(EVALS.read_text(encoding="utf-8"))["evals"]
    by_id = {case["id"]: case for case in evals}

    durable = by_id["wave4-durable-output-plan-before-approval"]
    assert "applicable semantic roles" in durable["expected_output"]
    assert "whole surfaces" in durable["expected_output"]
    assert "user documentation" in durable["expected_output"]
    assert "unresolved destinations" in durable["expected_output"]

    amendment = by_id["wave4-ship-requires-checked-acs-and-follow-ons"]
    assert "every final AC checked" in amendment["expected_output"]
    assert "Follow-ons" in amendment["expected_output"]
    assert "(deferred:" not in amendment["expected_output"]

    temporary = by_id["wave4-temporary-full-mode-retains-approval-rigor"]
    assert "normal full-mode approval, gate, and review rigor" in temporary["expected_output"]
    assert "exact locator and fingerprint" in temporary["expected_output"]
    assert "stable post-closeout evidence owner" in temporary["expected_output"]
