"""Roster coverage for the drain's per-item decision function (§ D2–§ D6).

Spec: ``docs/specs/work-item-promotion-handoff`` — task T5. The pure
decision function maps one offer to a route proposal, a hold, or a closure
verdict: § D2's shape-to-family map, § D10's defect readiness, § D11's
attended-only rule, § D5's closure grounds, § D6's disposition mapping and
the promoted-or-pruned split. No effect, no store write, no dispatch.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = (
    REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "project-knowledge" / "scripts"
)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DRAIN = _load_module("_roster_promotion_drain_decide", SCRIPTS_DIR / "promotion_drain.py")


def _request(
    shape: str,
    *,
    observed: bool = False,
    intended: bool = False,
    route: dict[str, Any] | None = None,
) -> dict[str, Any]:
    work_item: dict[str, Any] = {
        "statement": "The drain leaves this item unplaced.",
        "shape": shape,
        "blocker": "dependency",
        "finished_state": "The item sits with its owning route.",
        "necessity_rationale": "The route decides what happens to the item.",
    }
    if shape == "question":
        work_item["answered_by"] = "docs/knowledge/reference/work-items.md"
    if observed:
        work_item["observed"] = "The drain reports the item as unplaced today."
    if intended:
        work_item["intended"] = "The drain reports the item at its owner."
    request: dict[str, Any] = {
        "contract_version": "knowledge-captured-observation.v2",
        "kind": "work-item",
        "work_item": work_item,
        "project_scope": {"paths": ["docs"], "audience": "project"},
        "competency_facets": ["CQ-ROUTE"],
        "destination_hint": {
            "type": "route-suggestion",
            "path": "docs/knowledge/reference/work-items.md",
        },
        "producer": {"workflow": "work-loop", "workflow_version": "2.6.0"},
        "semantic_gate": {"name": "plan-locked", "artifact": "docs/specs/example/plan.md"},
        "provenance": {
            "sources": [
                {"path": "docs/specs/example/plan.md", "line_start": 10, "line_end": 20}
            ]
        },
        "freshness_anchor": {
            "path": "docs/specs/example/plan.md",
            "digest": {"kind": "sha256-bytes-v1", "sha256": "a" * 64, "byte_length": 100},
        },
        "observed_at": "2026-11-04T10:00:00Z",
        "privacy_attestation": {
            "reviewed": True,
            "contains_private_data": False,
            "contains_secrets": False,
            "contains_instructions": False,
        },
    }
    if route is not None:
        request["verification_route"] = route
    return request


def _capture(request: dict[str, Any]) -> dict[str, Any]:
    return {
        "capture_id": "kco-202611-" + "0" * 64,
        "partition": "observations/work-item/2026-11.jsonl",
        "captured_at": "2026-11-04T10:00:00Z",
        "request": request,
        "terminal_disposition": None,
    }


def test_ready_defect_routes(git_repo: Path) -> None:
    offer = DRAIN.assemble_offer(_capture(_request("defect", observed=True, intended=True)))

    decision = DRAIN.decide(offer, attended=True)

    assert decision["action"] == "route"
    assert decision["route"] == "defect-processor"
    assert decision["terminal_disposition"] == {
        "disposition": "routed",
        "reason_code": "routed-to-defect-processor",
    }


def test_defect_failing_readiness_holds(git_repo: Path) -> None:
    # Neither § D10 evidence shape: no observed/intended pair, no route.
    offer = DRAIN.assemble_offer(_capture(_request("defect")))

    decision = DRAIN.decide(offer, attended=True)

    assert decision["action"] == "hold"
    assert decision["reason"] == "defect-readiness"
    assert decision["terminal_disposition"] is None


def test_governance_item_holds_while_a_non_governance_item_routes(git_repo: Path) -> None:
    offers = [
        DRAIN.assemble_offer(_capture(_request("decision"))),
        DRAIN.assemble_offer(_capture(_request("question"))),
    ]

    decisions = [DRAIN.decide(offer, attended=True, classification="spec") for offer in offers]

    assert decisions[0]["action"] == "hold"
    assert decisions[0]["reason"] == "governance-route-absent"
    assert decisions[0]["terminal_disposition"] is None
    assert decisions[1]["action"] == "route"
    assert decisions[1]["route"] == "work-intake"
    assert decisions[1]["classification"] == "spec"


def test_unroutable_item_holds(git_repo: Path) -> None:
    offer = DRAIN.assemble_offer(_capture(_request("question")))

    decision = DRAIN.decide(offer, attended=True)

    assert decision["action"] == "hold"
    assert decision["reason"] == "unroutable"
    assert decision["terminal_disposition"] is None


def test_envelope_refused_stored_path_holds_the_item(git_repo: Path) -> None:
    (git_repo / "real.txt").write_text("inside\n", encoding="utf-8")
    (git_repo / "escape.txt").symlink_to("/etc/passwd")
    offer = DRAIN.assemble_offer(
        _capture(
            _request(
                "defect",
                route={"command": ["cat", "escape.txt"], "path": "real.txt"},
            )
        ),
        repo_root=git_repo,
    )

    assert offer["envelope_result"]["outcome"] == "refused"
    decision = DRAIN.decide(offer, attended=True)

    assert decision["action"] == "hold"
    assert decision["terminal_disposition"] is None


def test_untrusted_command_field_is_refused_as_input_and_carried_unexecuted(
    git_repo: Path,
) -> None:
    # The stored command is the field the trust-boundary rules classify as
    # untrusted: it never reaches a classification payload, and the envelope
    # runs it only after the re-check passes — a refused re-check leaves it
    # unexecuted and the item held.
    request = _request(
        "defect",
        route={"command": ["bash", "-c", "printf pwned"], "path": "docs/x.md"},
    )
    offer = DRAIN.assemble_offer(_capture(request))

    assert offer["recheck"]["verdict"] == "refused"
    assert offer["envelope_result"] is None
    payload = DRAIN.classification_payload(request)
    assert "printf pwned" not in str(payload)
    assert "bash" not in str(payload)

    decision = DRAIN.decide(offer, attended=True)

    assert decision["action"] == "hold"
    assert decision["terminal_disposition"] is None


def test_unattended_run_holds_every_item_and_writes_no_disposition(git_repo: Path) -> None:
    ready_defect = DRAIN.assemble_offer(_capture(_request("defect", observed=True, intended=True)))
    question = DRAIN.assemble_offer(_capture(_request("question")))

    for offer in (ready_defect, question):
        decision = DRAIN.decide(offer, attended=False, classification="spec")
        assert decision["action"] == "hold", offer
        assert decision["reason"] == "unattended"
        assert decision["terminal_disposition"] is None


def test_each_closure_ground_with_its_test_passing_records_the_ground() -> None:
    expected = {
        "overtaken": ("rejected", "closed_overtaken"),
        "falsified": ("rejected", "closed_falsified"),
        "superseded": ("superseded", "closed_superseded"),
    }
    for ground, (disposition, reason_code) in expected.items():
        citation = {"capture_id": "kco-202611-" + "0" * 64} if ground == "superseded" else None
        closure = DRAIN.decide_closure(
            ground, test_passes=True, evidence={"what": "the deviation no longer shows"},
            citation=citation,
        )
        assert closure["verdict"] == "closed", ground
        assert closure["terminal_disposition"] == {
            "disposition": disposition,
            "reason_code": reason_code,
        }
        assert closure["evidence"] == {"what": "the deviation no longer shows"}
    # § D5 (AC-0027): the closed superseded verdict carries its citation;
    # the other two grounds never do.
    superseded = DRAIN.decide_closure(
        "superseded",
        test_passes=True,
        evidence={},
        citation={"capture_id": "kco-202611-" + "0" * 64},
    )
    assert superseded["citation"] == {"capture_id": "kco-202611-" + "0" * 64}
    assert "citation" not in DRAIN.decide_closure("overtaken", test_passes=True, evidence={})


def test_each_closure_ground_with_its_test_failing_is_refused() -> None:
    for ground in ("overtaken", "falsified", "superseded"):
        closure = DRAIN.decide_closure(ground, test_passes=False, evidence={})
        assert closure["verdict"] == "refused", ground
        assert closure["terminal_disposition"] is None


def test_every_disposition_falls_on_exactly_one_side_of_the_split(git_repo: Path) -> None:
    routed_defect = DRAIN.decide(
        DRAIN.assemble_offer(_capture(_request("defect", observed=True, intended=True))),
        attended=True,
    )
    routed_question = DRAIN.decide(
        DRAIN.assemble_offer(_capture(_request("question"))),
        attended=True,
        classification="spec",
    )
    closures = [
        DRAIN.decide_closure(
            ground,
            test_passes=True,
            evidence={},
            citation={"capture_id": "kco-202611-" + "0" * 64} if ground == "superseded" else None,
        )
        for ground in ("overtaken", "falsified", "superseded")
    ]
    dispositions = [
        routed_defect["terminal_disposition"],
        routed_question["terminal_disposition"],
        *[closure["terminal_disposition"] for closure in closures],
    ]
    for terminal in dispositions:
        assert terminal is not None
        sides = [
            side
            for side in (DRAIN.PROMOTED_SIDE, DRAIN.PRUNED_SIDE)
            if terminal["disposition"] in side
        ]
        assert len(sides) == 1, terminal
        assert terminal["disposition"] != "promoted"
    for closure in closures:
        assert closure["terminal_disposition"]["disposition"] in DRAIN.PRUNED_SIDE


def test_capped_envelope_run_holds_rather_than_reporting_verified() -> None:
    # A route whose envelope run was terminated at the wall clock or
    # truncated at the output cap does not meet § D10's readiness, so the
    # item is held rather than reported verified (AC-0015).
    for outcome in ("wall_clock_exceeded", "completed"):
        envelope = {
            "outcome": outcome,
            "exit_status": None if outcome == "wall_clock_exceeded" else 0,
            "output": "x",
            "output_truncated": outcome == "completed",
            "refusal": None,
        }
        offer = DRAIN.assemble_offer(
            _capture(
                _request("defect", route={"command": ["cat", "big.txt"], "path": "big.txt"})
            )
        )
        offer["envelope_result"] = envelope

        decision = DRAIN.decide(offer, attended=True)

        assert decision["action"] == "hold", outcome
        assert decision["reason"] == "defect-readiness", outcome
        assert decision["terminal_disposition"] is None, outcome


@pytest.mark.parametrize(
    "member,routes",
    [
        ("direct-light", True),
        ("spec", True),
        ("brief", True),
        ("defect", True),
        ("remember", False),
        ("incomplete", False),
    ],
)
def test_each_classify_member_routes_or_holds_by_dispatchability(
    git_repo: Path, member: str, routes: bool
) -> None:
    # § D3 (AC-0026): a question's classification must be one of the six
    # classify-table members by name; a non-dispatchable member — `remember`
    # or `incomplete`, rows whose processor is `none` — names no route, so
    # the item holds the same way a non-member does.
    offer = DRAIN.assemble_offer(_capture(_request("question")))

    decision = DRAIN.decide(offer, attended=True, classification=member)

    if routes:
        assert decision["action"] == "route"
        assert decision["classification"] == member
        assert decision["terminal_disposition"] is not None
    else:
        assert decision["action"] == "hold"
        assert decision["reason"] == "unroutable"
        assert decision["terminal_disposition"] is None


def test_non_member_classification_holds_as_unroutable(git_repo: Path) -> None:
    # § D3 (AC-0026): a classification that is not one of the six members is
    # not a classification — no table row owns it — and no non-empty string
    # can route a question.
    offer = DRAIN.assemble_offer(_capture(_request("question")))

    decision = DRAIN.decide(offer, attended=True, classification="deploy-checklist")

    assert decision["action"] == "hold"
    assert decision["reason"] == "unroutable"
    assert decision["terminal_disposition"] is None


def test_superseded_closure_requires_a_well_formed_citation() -> None:
    # § D5 (AC-0027): the citation is a required field — absent or
    # malformed citations are refused before any test verdict, whatever the
    # operator attests; the other two grounds never require one.
    absent = DRAIN.decide_closure("superseded", test_passes=True, evidence={})
    assert absent == {
        "verdict": "refused",
        "reason": "citation-required",
        "ground": "superseded",
        "terminal_disposition": None,
    }
    for malformed in ({}, {"capture_id": ""}, {"capture_id": 7}, {"path": ""},
                      {"capture_id": "x", "path": "y"}, "kco-202611-0"):
        refused = DRAIN.decide_closure("superseded", test_passes=True, evidence={}, citation=malformed)
        assert refused["verdict"] == "refused", malformed
        assert refused["reason"] == "citation-malformed"
    # The operator's veto still refuses a well-formed citation.
    vetoed = DRAIN.decide_closure(
        "superseded", test_passes=False, evidence={}, citation={"path": "docs/example.md"}
    )
    assert vetoed["verdict"] == "refused"
    assert vetoed["reason"] == "ground-test-failed"


def test_non_superseded_grounds_ignore_the_citation_field() -> None:
    # § D5 (AC-0027): overtaken and falsified stay operator-attested,
    # byte-for-byte their current behavior — a citation rides neither.
    for ground in ("overtaken", "falsified"):
        closure = DRAIN.decide_closure(
            ground, test_passes=True, evidence={"what": "named"}, citation={"path": "docs/x.md"}
        )
        assert closure["verdict"] == "closed"
        assert "citation" not in closure
