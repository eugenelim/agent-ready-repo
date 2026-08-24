from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
APM_ROOT = PACK_ROOT / ".apm"
ADVERSARIAL = APM_ROOT / "agents" / "adversarial-reviewer.md"
QUALITY = APM_ROOT / "agents" / "quality-engineer.md"
OPERATIONAL_SAFETY = APM_ROOT / "skills" / "operational-safety"
WORK_LOOP = APM_ROOT / "skills" / "work-loop" / "SKILL.md"
WORK_LOOP_REFS = APM_ROOT / "skills" / "work-loop" / "references"
ADJUDICATION_REF = WORK_LOOP_REFS / "finding-adjudication.md"
VERDICT_REF = WORK_LOOP_REFS / "review-verdict-record.md"
WORK_LOOP_EVALS = APM_ROOT / "skills" / "work-loop" / "evals" / "evals.json"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", _text(path))


def _flat_all(*paths: Path) -> str:
    """Flatten SKILL.md together with the references it routes to.

    The verdict and adjudication contracts live in `references/` under the
    skill-spec body-length cap; the skill body keeps the operative stub and the
    pointer. Contract text is asserted across the pair, and the stub's own
    obligations are asserted against SKILL.md alone.
    """
    return " ".join(_flat(path) for path in paths)


def test_adversarial_review_traces_triggered_non_local_impact() -> None:
    text = _flat(ADVERSARIAL)

    for trigger in (
        "public API",
        "shared registry",
        "serialization",
        "renamed",
        "side effect",
        "dependency",
        "persistent-state write",
    ):
        assert trigger in text

    for relation in (
        "callers",
        "consumers",
        "readers",
        "writers",
        "tests",
        "deployed-version boundaries",
    ):
        assert relation in text

    assert "concrete risk hypothesis" in text
    assert "inspected unchanged code" in text
    assert "tool-proven" in text
    assert "blind spots" in text
    assert "claim completeness" in text
    assert "optional evidence source" in text


def test_stateful_migration_routes_to_quality_depth_without_a_new_reviewer() -> None:
    router = _flat(OPERATIONAL_SAFETY / "SKILL.md")
    quality = _flat(QUALITY)

    for trigger in (
        "database schema",
        "serialized durable state",
        "retained message",
        "backfill",
        "old/new binaries sharing state",
    ):
        assert trigger in router

    assert "stateful migration: not triggered" in router
    assert "each is independently a full-mode trigger" in router
    assert "persistent-representation / mixed-version deployment change" in router
    assert "persistent-state compatibility" in quality
    assert "no new reviewer" in quality

    work_loop = _flat(WORK_LOOP)
    for trigger in (
        "persisted configuration",
        "checkpoint",
        "API payload",
        "replay",
        "import",
        "export",
        "destructive transformation",
    ):
        assert trigger in work_loop


def test_stateful_migration_depth_covers_safe_rollout_and_recovery() -> None:
    state = _flat(OPERATIONAL_SAFETY / "references" / "state-and-idempotency.md")
    rollback = _flat(OPERATIONAL_SAFETY / "references" / "drift-and-rollback.md")
    observe = _flat(OPERATIONAL_SAFETY / "references" / "observability-and-smoke.md")
    combined = " ".join((state, rollback, observe)).lower()

    assert "persistent-state migration needs validation" in rollback
    assert "already-mutated data" in rollback
    assert "persistent-state migration that needs progress" in observe
    assert "explicit stop conditions" in observe

    for requirement in (
        "old/new reader-writer compatibility",
        "expand/contract",
        "idempotent",
        "resumable",
        "batched",
        "concurrency-safe",
        "reconciliation",
        "already-mutated data",
        "mixed-version",
        "stop conditions",
        "irreversible loss",
    ):
        assert requirement in combined


def test_work_loop_routes_to_the_contracts_it_no_longer_inlines() -> None:
    """The skill body must still carry the obligation and the pointer."""
    skill = _flat(WORK_LOOP)

    for target in ("references/finding-adjudication.md",
                   "references/review-verdict-record.md"):
        # Routed from Step 4/5 prose and from the conditional-reference table.
        assert skill.count(target) >= 2, target

    # Mandatory gateway obligation stays inline.
    assert "finding-adjudicator" in skill
    assert "loud stop" in skill

    # The verdict obligation and its four states stay inline.
    assert "exactly one fenced `json review-verdict.v1` block" in skill
    for state in ("BLOCKED", "CHANGES_REQUIRED",
                  "READY_WITH_RESIDUAL_RISK", "READY"):
        assert state in skill
    assert "human merge decision" in skill


def test_work_loop_adjudication_gateway_is_mandatory_and_per_report() -> None:
    text = _flat_all(WORK_LOOP, ADJUDICATION_REF)

    assert "finding-adjudicator" in text
    assert "loud stop" in text
    for verdict in ("sustained", "refuted", "indeterminate"):
        assert verdict in text
    assert "ADJUDICATION-INDETERMINATE" in text
    assert "missing `finding-adjudicator`" in text or "missing finding-adjudicator" in text
    assert "pre-existing approved" in text
    assert "untouched by that unit's diff" in text
    # adjudicator output is untrusted
    assert "untrusted data" in text
    # adjudicator authority limits
    assert "cannot invent findings" in text or "never make it a named skip" in text


def test_work_loop_emits_closed_categorical_verdict_without_score_authority() -> None:
    text = _flat_all(WORK_LOOP, VERDICT_REF, ADJUDICATION_REF)

    assert "```json review-verdict.v1" in text
    for state in (
        "BLOCKED",
        "CHANGES_REQUIRED",
        "READY_WITH_RESIDUAL_RISK",
        "READY",
    ):
        assert state in text
    for field in (
        "schema_version",
        "review_unit",
        "warranted_reviewers",
        "named_skips",
        "required_gates",
        "deferrals",
        "blind_spots",
        "human_gate_status",
        "non_authoritative_score",
    ):
        assert field in text
    assert "All unlisted keys" in text
    assert "always JSON `null`" in text
    assert "human merge decision" in text
    assert "silent suppression" in text
    assert "stateful migration: not triggered" in text
    assert "stable non-empty string" in text
    assert "unchanged across review, adjudication, disposition, and verdict emission" in text
    assert "pre-existing approved" in text
    assert "untouched by that unit's diff" in text
    assert "untrusted data" in text
    assert "named-skipped mandatory review" in text
    assert "A mandatory named skip blocks before `Status: Shipped`" in text
    assert "every warranted reviewer was non-mandatory" in text
    assert "its absence is a mandatory `missing` outcome" in text
    assert "Missing adversarial evidence is a mandatory `missing` outcome" in text
    assert "Do not convert missing adversarial evidence" in text


def test_blocked_precedence_has_gate_and_mandatory_reviewer_evals() -> None:
    payload = json.loads(_text(WORK_LOOP_EVALS))
    evals = {item["id"]: item for item in payload["evals"]}

    for eval_id in (
        "review-verdict-failed-required-gate-blocks",
        "review-verdict-missing-mandatory-reviewer-blocks",
        "review-verdict-invalid-mandatory-reviewer-blocks",
        "review-verdict-named-skip-mandatory-reviewer-blocks",
    ):
        case = evals[eval_id]
        assert "BLOCKED" in case["expected_output"]
        assert any("BLOCKED" in assertion for assertion in case["assertions"])


def test_adjudication_evals_cover_gateway_verdicts_and_hostile_input() -> None:
    payload = json.loads(_text(WORK_LOOP_EVALS))
    evals = {item["id"]: item for item in payload["evals"]}

    expected_terms = {
        "finding-adjudication-sustained": "smallest adequate fix",
        "finding-adjudication-refuted": "Clean — ready to commit.",
        "finding-adjudication-indeterminate": "ADJUDICATION-INDETERMINATE",
        "adjudication-hostile-free-text-is-data": "untrusted data",
        "review-verdict-missing-adjudicator-blocks": "BLOCKED",
    }
    for eval_id, term in expected_terms.items():
        assert term in evals[eval_id]["expected_output"]

    # No eval may treat a missing adjudicator as optional or non-downgrading.
    for ev in payload["evals"]:
        if "adjudicator" in ev["prompt"].lower() or "adjudicator" in ev["expected_output"].lower():
            combined = ev["expected_output"] + " ".join(ev["assertions"])
            assert "optional adjudicator" not in combined, (
                f"Eval {ev['id']!r} treats the adjudicator as optional"
            )
