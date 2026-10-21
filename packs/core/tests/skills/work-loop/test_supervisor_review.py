"""The review rules resolver and the selection record (T2), over pure inputs.

VI-6011 (AC-0007, AC-0008): the obligation matrix over every role, selected and
omitted. VI-6012 (AC-0009, AC-0010, AC-0011): fingerprints, the repeated-key
refusal, and the selection commit. VI-6013 (AC-0021): each named refusal, and no
case resolves a role as optional. The git-backed runs that drive the same paths
through ``work-supervisor.py`` are in ``test_supervisor_review_gate.py``.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

_HELPER = Path(__file__).resolve().parent / "supervisor_harness.py"


def _harness() -> ModuleType:
    alias = "core_work_loop_supervisor_harness"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _harness()
review = h.cli._supervisor("_supervisor_review.py")
Refusal = review.Refusal

RULES: dict[str, Any] = review.load_rules()
KEY = "a" * 64
OTHER_KEY = "b" * 64
OWNER = "owner:0123456789ab"
RISK_OWNER = "risk-owner:0123456789ab"
DELIVERY = "docs/specs/calc/delivery"

# The obligation each role carries, from the role obligation definition.
EXPECTED_KIND = {
    "adversarial-reviewer": "mandatory",
    "security-reviewer": "mandatory",
    "experience-reviewer": "optional",
    "frontend-reviewer": "optional",
    "design-reviewer": "mandatory",
    "quality-engineer": "mandatory",
}


class FakeGit:
    """The two ``delivery/`` reads and the commit the review module uses."""

    delivery_rel = DELIVERY

    def __init__(self, files: dict[str, bytes] | None = None) -> None:
        self.files = {f"{DELIVERY}/{name}": raw for name, raw in (files or {}).items()}
        self.commits: list[dict[str, Any]] = []

    def show(self, path: str, rev: str = "HEAD") -> bytes | None:
        return self.files.get(path)

    def build_commit(self, **kwargs: Any) -> None:
        self.commits.append(kwargs)
        for name, extra in kwargs.get("appends", {}).items():
            path = f"{DELIVERY}/{name}"
            self.files[path] = self.files.get(path, b"") + extra


def workspace(files: dict[str, bytes] | None = None) -> Any:
    policy = h.admission.load_policy()
    return SimpleNamespace(git=FakeGit(files), policy=policy)


def selection(selected: tuple[str, ...] = (), reason: str = "not reached") -> dict[str, Any]:
    """A selection that selects *selected* and omits every other candidate."""
    candidates = review.candidates(RULES)
    return {
        "selected": [r for r in candidates if r in selected],
        "omitted": [{"role": r, "reason": reason} for r in candidates if r not in selected],
        "authority_ref": "controller:0123456789ab",
    }


def record(selected: tuple[str, ...] = (), key: str = KEY) -> dict[str, Any]:
    return {"selection_key": key, **selection(selected)}


def line(record_: dict[str, Any]) -> bytes:
    return h.admission.canonical_line(record_)


def kinds(policy: dict[str, Any]) -> dict[str, str]:
    return {r["role"]: r["kind"] for r in policy["roles"]}


# ── VI-6011: the obligation matrix ───────────────────────────────────────────


def test_vi6011_the_rules_cover_the_expected_roster() -> None:
    """VI-6011: the shipped roles and their mandatory classes are the ones the plan names."""
    assert {e["role"]: e["mandatory_when"] for e in RULES["roles"]} == {
        "adversarial-reviewer": "always",
        "security-reviewer": "selected",
        "experience-reviewer": "never",
        "frontend-reviewer": "never",
        "design-reviewer": "selected",
        "quality-engineer": "selected",
    }


@pytest.mark.parametrize("role", sorted(EXPECTED_KIND))
@pytest.mark.parametrize("work", ["infra work", "non-infra work"])
def test_vi6011_selected_role_kind_equals_its_obligation(role: str, work: str) -> None:
    """VI-6011: a selected role resolves to its obligation, on infra and on non-infra work."""
    entry = next(e for e in RULES["roles"] if e["role"] == role)
    chosen = () if entry["kind"] == "always" else (role,)
    policy = review.resolve_policy(RULES, {**selection(chosen, reason=work)})
    assert kinds(policy)[role] == EXPECTED_KIND[role]


@pytest.mark.parametrize("role", sorted(EXPECTED_KIND))
def test_vi6011_omitted_role_is_absent_and_always_role_stays(role: str) -> None:
    """VI-6011: an omitted conditional role is not in the policy; adversarial always is."""
    entry = next(e for e in RULES["roles"] if e["role"] == role)
    policy = review.resolve_policy(RULES, selection(()))
    if entry["kind"] == "always":
        assert kinds(policy)[role] == "mandatory"
    else:
        assert role not in kinds(policy)
    assert kinds(policy)["adversarial-reviewer"] == "mandatory"


def test_vi6011_every_selected_combination_keeps_the_obligations() -> None:
    """VI-6011: over every subset of conditional roles each kind still equals its obligation."""
    candidates = review.candidates(RULES)
    for mask in range(1 << len(candidates)):
        chosen = tuple(r for i, r in enumerate(candidates) if mask >> i & 1)
        policy = review.resolve_policy(RULES, selection(chosen))
        assert set(kinds(policy)) == {"adversarial-reviewer", *chosen}
        assert all(kinds(policy)[r] == EXPECTED_KIND[r] for r in kinds(policy))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda s: s["omitted"].pop(),  # a candidate neither selected nor omitted
        lambda s: s["omitted"][0].update(reason=""),
        lambda s: s["omitted"][0].update(reason="   "),
        lambda s: s["omitted"][0].pop("reason"),
        lambda s: s["omitted"][0].update(role="no-such-reviewer"),
        lambda s: s["selected"].append("no-such-reviewer"),
        lambda s: s["selected"].append("adversarial-reviewer"),
        lambda s: s["omitted"].append({"role": "adversarial-reviewer", "reason": "skip it"}),
        lambda s: s.update(selected="security-reviewer"),
        lambda s: s.pop("omitted"),
    ],
)
def test_vi6011_a_bad_record_is_refused(mutate: Any) -> None:
    """VI-6011: AC-0008: an omission without a reason, or an unknown role, is refused."""
    bad = selection(())
    mutate(bad)
    with pytest.raises(Refusal) as refused:
        review.resolve_policy(RULES, bad)
    assert refused.value.code == "review-selection-invalid"


def test_vi6011_a_role_named_twice_is_refused() -> None:
    """VI-6011: a role both selected and omitted is refused, never resolved either way."""
    bad = selection(("security-reviewer",))
    bad["omitted"].append({"role": "security-reviewer", "reason": "also omitted"})
    with pytest.raises(Refusal) as refused:
        review.resolve_policy(RULES, bad)
    assert refused.value.code == "review-selection-invalid"


# ── VI-6012: fingerprints, repeats, and the commit ───────────────────────────


def test_vi6012_different_selections_give_different_fingerprints() -> None:
    """VI-6012: two records resolving to different roles or kinds differ in fingerprint."""
    fingerprints = {
        review.resolve_policy(RULES, selection(chosen))["review_policy_fingerprint"]
        for chosen in (
            (),
            ("security-reviewer",),
            ("experience-reviewer",),
            ("security-reviewer", "experience-reviewer"),
        )
    }
    assert len(fingerprints) == 4
    same = [review.resolve_policy(RULES, selection(()))["review_policy_fingerprint"] for _ in "ab"]
    assert same[0] == same[1]


def test_vi6012_a_kind_change_alone_changes_the_fingerprint() -> None:
    """VI-6012: the same roles with another kind give another fingerprint."""
    changed = copy.deepcopy(RULES)
    for entry in changed["roles"]:
        if entry["role"] == "experience-reviewer":
            entry["mandatory_when"] = "selected"
    base = review.resolve_policy(RULES, selection(("experience-reviewer",)))
    flipped = review.resolve_policy(changed, selection(("experience-reviewer",)))
    assert [r["role"] for r in base["roles"]] == [r["role"] for r in flipped["roles"]]
    assert base["review_policy_fingerprint"] != flipped["review_policy_fingerprint"]


def test_vi6012_the_selection_key_follows_the_subject_and_the_changed_paths() -> None:
    """VI-6012: a repair that changes the product asks for a fresh selection."""
    base = review.selection_key("fp-1", ["b.py", "a.py"])
    assert base == review.selection_key("fp-1", ["a.py", "b.py"])
    assert base != review.selection_key("fp-2", ["a.py", "b.py"])
    assert base != review.selection_key("fp-1", ["a.py"])


def _status(ws: Any, key: str = KEY) -> Any:
    return review.selection_status(ws, RULES, key)


def test_vi6012_a_second_record_is_refused_until_the_owner_decides() -> None:
    """VI-6012: AC-0010: refused, refused with a non-owner decision, admitted with an owner one."""
    ws = workspace()
    first = review.admit_selection(RULES, _status(ws), selection(()))
    assert first["selection_key"] == KEY and first["sequence"] == 1
    assert "authorized_by" not in first
    ws.git.files[f"{DELIVERY}/review-selections.jsonl"] = line(first)

    with pytest.raises(Refusal) as again:
        review.admit_selection(RULES, _status(ws), selection(("security-reviewer",)))
    assert again.value.code == "review-selection-exists"

    request = {"request_id": "decide:review-not-eligible:abc", "reason": "review-not-eligible",
               "selection_key": KEY}
    state = SimpleNamespace(run_id="run-0123456789abcdef")
    wrong_role = {"decision": {"decision": "reselect-review", "authority_ref": RISK_OWNER,
                               "selection_key": KEY}}
    with pytest.raises(Refusal) as refused:
        review.admit_decision(ws, state, request, wrong_role)
    assert refused.value.code == "authority-refused"
    with pytest.raises(Refusal) as still:
        review.admit_selection(RULES, _status(ws), selection(("security-reviewer",)))
    assert still.value.code == "review-selection-exists"

    owner = {"decision": {"decision": "reselect-review", "authority_ref": OWNER,
                          "selection_key": KEY}}
    admitted = review.admit_decision(ws, state, request, owner)
    assert admitted["decision"] == "reselect-review" and admitted["authority_ref"] == OWNER
    ws.git.files[f"{DELIVERY}/review-decisions.jsonl"] = line(admitted)

    status = _status(ws)
    assert status.required and status.sequence == 2
    second = review.admit_selection(RULES, status, selection(("security-reviewer",)))
    assert second["sequence"] == 2 and second["authorized_by"] == request["request_id"]
    ws.git.files[f"{DELIVERY}/review-selections.jsonl"] += line(second)
    assert not _status(ws).required
    # The owner decision was spent: a third record needs another one.
    with pytest.raises(Refusal) as third:
        review.admit_selection(RULES, _status(ws), selection(()))
    assert third.value.code == "review-selection-exists"


def test_vi6012_a_decision_for_another_key_does_not_authorize() -> None:
    """VI-6012: an owner decision names one key, and authorizes only that key."""
    ws = workspace({"review-selections.jsonl": line(record())})
    ws.git.files[f"{DELIVERY}/review-decisions.jsonl"] = line({
        "run_id": "run-0123456789abcdef",
        "request_id": "decide:x:1",
        "decision": "reselect-review",
        "authority_ref": OWNER,
        "selection_key": OTHER_KEY,
    })
    assert not _status(ws).required


@pytest.mark.parametrize(
    "decision",
    [
        {"decision": "accept-risk", "authority_ref": OWNER, "finding_ids": ["f-1"]},
        {"decision": "waive-everything", "authority_ref": OWNER},
        {"decision": "reselect-review", "authority_ref": "owner", "selection_key": OTHER_KEY},
    ],
)
def test_vi6012_a_decision_outside_reselect_review_by_the_owner_is_refused(
    decision: dict[str, Any],
) -> None:
    """VI-6012: a wrong-role accept-risk, an unknown decision, and a wrong key are all refused."""
    request = {"request_id": "decide:review-not-eligible:abc", "reason": "review-not-eligible",
               "selection_key": KEY}
    with pytest.raises(Refusal) as refused:
        review.admit_decision(
            workspace(), SimpleNamespace(run_id="run-0123456789abcdef"), request,
            {"decision": decision},
        )
    assert refused.value.code in {"authority-refused", "invalid-result"}


def test_vi6012_only_a_review_not_eligible_request_takes_a_decision() -> None:
    """VI-6012: a human-decision request for any other reason refuses authority-refused."""
    request = {"request_id": "decide:retry-cap:abc", "reason": "retry-cap"}
    owner = {"decision": {"decision": "reselect-review", "authority_ref": OWNER,
                          "selection_key": KEY}}
    with pytest.raises(Refusal) as refused:
        review.admit_decision(
            workspace(), SimpleNamespace(run_id="run-0123456789abcdef"), request, owner
        )
    assert refused.value.code == "authority-refused"


def test_vi6012_an_admitted_selection_commits_as_a_review_step() -> None:
    """VI-6012: AC-0011: the record commit carries the review operation and appends the file."""
    readiness = h.cli._supervisor("_supervisor_readiness.py")
    ws = workspace()
    state = SimpleNamespace(run_id="run-0123456789abcdef", steps=set())
    request = {"request_id": f"select:{KEY[:24]}:1", "kind": "review-role",
               "candidates": review.candidates(RULES), "selection_key": KEY}
    outcome = readiness._report_selection(
        ws, state, request, {"selection": selection(("security-reviewer",))}, {}
    )
    assert outcome == "review"
    (commit,) = ws.git.commits
    assert commit["operation"] == "review"
    assert commit["step"] == request["request_id"]
    assert list(commit["appends"]) == ["review-selections.jsonl"]
    written = json.loads(commit["appends"]["review-selections.jsonl"])
    assert written["selected"] == ["security-reviewer"] and written["selection_key"] == KEY


# ── VI-6013: every refusal names its code, and none defaults a role ──────────


def _rules_file(tmp_path: Path, mutate: Any) -> Path:
    data = copy.deepcopy(RULES)
    mutate(data)
    path = tmp_path / "review-rules.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_vi6013_a_missing_rules_file_refuses(tmp_path: Path) -> None:
    """VI-6013: no rules file means review-rules-invalid, not a default policy."""
    with pytest.raises(Refusal) as refused:
        review.load_rules(tmp_path / "absent.json")
    assert refused.value.code == "review-rules-invalid"


def test_vi6013_invalid_json_refuses(tmp_path: Path) -> None:
    """VI-6013: a rules file that is not JSON refuses."""
    path = tmp_path / "review-rules.json"
    for body in ("{not json", '{"rules_version": NaN}', ""):
        path.write_text(body, encoding="utf-8")
        with pytest.raises(Refusal) as refused:
            review.load_rules(path)
        assert refused.value.code == "review-rules-invalid"


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["roles"][1].update(kind="sometimes"),
        lambda d: d["roles"][1].update(mandatory_when="maybe"),
        lambda d: d["roles"][1].update(mode_limit=["night"]),
        lambda d: d["roles"][1].pop("fallback"),
        lambda d: d["roles"][1].update(extra="field"),
        lambda d: d["roles"][1].update(role="adversarial-reviewer"),
        lambda d: d["roles"][0].update(kind="conditional"),
        lambda d: d.pop("rules_version"),
        lambda d: d.update(roles=[]),
    ],
)
def test_vi6013_a_value_outside_its_closed_set_refuses(tmp_path: Path, mutate: Any) -> None:
    """VI-6013: kind sometimes, mandatory_when maybe, and the other shape defects refuse."""
    with pytest.raises(Refusal) as refused:
        review.load_rules(_rules_file(tmp_path, mutate))
    assert refused.value.code == "review-rules-invalid"


def test_vi6013_current_policy_surfaces_a_rules_defect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """VI-6013: the rules defect reaches the caller as a refusal; no policy comes back."""
    monkeypatch.setattr(review, "RULES_PATH", tmp_path / "absent.json")
    ws = workspace({"review-selections.jsonl": line(record())})
    with pytest.raises(Refusal) as refused:
        review.current_policy(ws, None, KEY)
    assert refused.value.code == "review-rules-invalid"


def test_vi6013_a_truncated_selection_line_refuses() -> None:
    """VI-6013: a selection line that does not parse refuses review-selection-invalid."""
    whole = line(record())
    for raw in (whole[: len(whole) // 2], whole[:-1], b'{"selection_key": "x"}\n', b"[]\n"):
        ws = workspace({"review-selections.jsonl": raw})
        with pytest.raises(Refusal) as refused:
            review.current_policy(ws, None, KEY)
        assert refused.value.code == "review-selection-invalid"


def test_vi6013_an_unauthorized_repeated_key_refuses() -> None:
    """VI-6013: a key repeated without an owner decision refuses review-selection-exists."""
    ws = workspace({"review-selections.jsonl": line(record()) + line(record(("quality-engineer",)))})
    with pytest.raises(Refusal) as refused:
        review.current_policy(ws, None, KEY)
    assert refused.value.code == "review-selection-exists"
    ws.git.files[f"{DELIVERY}/review-decisions.jsonl"] = line({
        "run_id": "run-0123456789abcdef",
        "request_id": "decide:x:1",
        "decision": "reselect-review",
        "authority_ref": RISK_OWNER,
        "selection_key": KEY,
    })
    with pytest.raises(Refusal) as non_owner:
        review.current_policy(ws, None, KEY)
    assert non_owner.value.code == "review-selection-exists"


def test_vi6013_a_record_that_no_longer_resolves_refuses() -> None:
    """VI-6013: a committed record naming an unknown role refuses, never resolving it optional."""
    bad = record()
    bad["selected"] = ["no-such-reviewer"]
    ws = workspace({"review-selections.jsonl": line(bad)})
    with pytest.raises(Refusal) as refused:
        review.current_policy(ws, None, KEY)
    assert refused.value.code == "review-selection-invalid"


def test_vi6013_a_missing_record_needs_a_selection_and_yields_no_policy() -> None:
    """VI-6013: with no record for the key the status is `required` and no policy resolves."""
    for files in ({}, {"review-selections.jsonl": line(record(key=OTHER_KEY))}):
        ws = workspace(files)
        assert _status(ws).required
        with pytest.raises(Refusal) as refused:
            review.current_policy(ws, None, KEY)
        assert refused.value.code == "review-selection-missing"
    ws = workspace({"review-selections.jsonl": line(record(("security-reviewer",)))})
    assert not _status(ws).required
    assert kinds(review.current_policy(ws, None, KEY)) == {
        "adversarial-reviewer": "mandatory",
        "security-reviewer": "mandatory",
    }


def test_vi6013_no_refusal_case_returns_a_policy_with_an_optional_default() -> None:
    """VI-6013: every always role stays mandatory; only `never` roles are ever optional."""
    for chosen in ((), ("security-reviewer",), ("experience-reviewer", "frontend-reviewer")):
        policy = review.resolve_policy(RULES, selection(chosen))
        optional = {r["role"] for r in policy["roles"] if r["kind"] == "optional"}
        assert optional <= {"experience-reviewer", "frontend-reviewer"}
        assert kinds(policy)["adversarial-reviewer"] == "mandatory"
