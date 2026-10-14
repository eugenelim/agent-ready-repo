"""Projector and CLI suites for Slice 3 task T1 (AC-0002, AC-0004, AC-0012).

Table-driven replay of source facts through the pure projector, byte-identity
across fresh processes, and the ``delivery-fact-feed.py`` command line.

Mode: TDD through contract and integration tests.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import delivery_feed_support as dfs
import pytest

RECEIPT_ID = "review-failure-sha256-" + "c" * 64


@pytest.fixture(scope="module")
def kp() -> ModuleType:
    """The projector module, loaded by path under a unique name."""
    return dfs.load_script("dfp_table_projection", "_knowledge_projection.py")


def receipt() -> dict:
    return {
        "schema_version": 1, "receipt_id": RECEIPT_ID, "acceptance_fingerprint": "acceptance-fp-1",
        "lineage": {"criterion_ref": "AC-0001"}, "selector": {"term": "supported-review-failure"},
        "freshness_mode": "exact-subject", "observation": {"type": "review-failure"},
        "outcome": "review-failure",
        "producer": {"class": "review-bridge", "identity": "structured-review-boundary"},
    }


def finding(**over: object) -> dict:
    base = {
        "schema_version": 1, "finding_id": "finding-1", "rule_ref": "AC-0001",
        "observation": "Input is accepted unchecked.", "reachable_path": "Caller to writer.",
        "actual_failure": "Bad data is persisted.", "affected_acceptance_criteria": ["AC-0001"],
        "evidence_refs": ["src/a.py", "evidence:x", "src/../b.py", "src/a.py"], "material": True,
    }
    return {**base, **over}


def report(**over: object) -> dict:
    return {"report_id": "report-1", "role": "r", "lineage": {
        "sequence": 1, "review_policy_fingerprint": "policy-fp-1", "source_event_id": "e",
        "producer": "p"}, **over}


def run(kp: ModuleType, kind: str = "evidence-receipt.v1", rec: dict | None = None, **over: object):
    args = {"spec_path": "docs/specs/s", "transaction_id": "tx-1", "superseded": False,
            "report": report(), "finding": finding(), **over}
    return kp.project_record(kind, rec if rec is not None else receipt(), **args)


@pytest.mark.parametrize("kind", [
    "reviewed-execution-envelope.v1", "initial-plan-review.v1", "plan", "task-projection",
    "mutation-classification", "evidence-supersession.v1", "review-report.v1",
    "finding-assessment.v1", "approval-record.v1",
])
def test_ineligible_record_kinds_yield_none(kp: ModuleType, kind: str) -> None:
    assert run(kp, kind) == (None, "ineligible-record-kind")


def test_non_review_failure_receipts_yield_none(kp: ModuleType) -> None:
    engine = receipt()
    engine["observation"] = {"type": "engine-transition"}
    engine["selector"] = {"term": "engine-transition:plan-locked"}
    assert run(kp, rec=engine) == (None, "ineligible-receipt")
    forged = receipt()
    forged["producer"] = {"class": "ci-runner", "identity": "x"}
    assert run(kp, rec=forged) == (None, "ineligible-receipt")


def test_superseded_and_unresolved_sources_yield_none(kp: ModuleType) -> None:
    assert run(kp, superseded=True) == (None, "superseded")
    assert run(kp, report=None) == (None, "source-unresolved")
    assert run(kp, finding=None) == (None, "source-unresolved")


@pytest.mark.parametrize("over,reason", [
    ({"observation": "x" * 601}, "oversized"),
    ({"rule_ref": "r" * 121}, "oversized"),
    ({"observation": "ghp_" + "a" * 36}, "content-refused"),
    ({"observation": "mail me at someone@example.com"}, "content-refused"),
    ({"observation": "evil \u202e text"}, "unrepresentable"),
    ({"observation": "zero\u200bwidth"}, "unrepresentable"),
    ({"observation": "\x1b[2J"}, "unrepresentable"),
    ({"observation": "   "}, "unrepresentable"),
    ({"observation": 7}, "unrepresentable"),
    ({"finding_id": "bad id"}, "unrepresentable"),
    ({"finding_id": "ok\n"}, "unrepresentable"),
])
def test_refused_text_yields_no_observation(kp: ModuleType, over: dict, reason: str) -> None:
    assert run(kp, finding=finding(**over)) == (None, reason)


_INVISIBLE_FAMILIES = {
    "soft-hyphen": "\u00ad",
    "combining-grapheme-joiner": "\u034f",
    "hangul-choseong-filler": "\u115f",
    "hangul-jungseong-filler": "\u1160",
    "khmer-inherent-vowel": "\u17b4",
    "khmer-inherent-aa": "\u17b5",
    "mongolian-selector": "\u180b",
    "mongolian-vowel-separator": "\u180e",
    "mongolian-selector-last": "\u180f",
    "hangul-filler": "\u3164",
    "variation-selector": "\ufe00",
    "variation-selector-last": "\ufe0f",
    "halfwidth-hangul-filler": "\uffa0",
    "tag-first": "\U000e0000",
    "tag-latin-a": "\U000e0041",
    "tag-last": "\U000e0fff",
}


@pytest.mark.parametrize("char", sorted(_INVISIBLE_FAMILIES.values()), ids=sorted(_INVISIBLE_FAMILIES))
def test_default_ignorable_characters_yield_no_observation(kp: ModuleType, char: str) -> None:
    """Soft hyphen, fillers, selectors, and tag characters render as nothing, so they are refused."""
    assert run(kp, finding=finding(observation=f"before{char}after")) == (None, "unrepresentable")


def test_total_size_bound_is_enforced_on_the_whole_observation(kp: ModuleType) -> None:
    refs = [f"d{i}/{'p' * 230}.py" for i in range(10)]
    big = finding(observation="a" * 600, reachable_path="b" * 600, actual_failure="c" * 600,
                  evidence_refs=refs)
    assert run(kp, finding=big) == (None, "oversized")


def test_successful_projection_shape_and_normalization(kp: ModuleType) -> None:
    obs, reason = run(kp, finding=finding(observation="line one\r\n\tline  two three"))
    assert reason is None and obs is not None
    assert obs["observed"]["value"] == "line one line two three"
    assert obs["scope_paths"] == ["src/a.py"]
    assert obs["source"]["review_policy_fingerprint"] == "policy-fp-1"
    assert obs["source"]["acceptance_fingerprint"] == "acceptance-fp-1"
    assert obs["observation_id"].startswith("knowledge-observation-sha256-")
    assert len(kp.canonical_json(obs).encode()) <= 4096


def test_identity_ignores_text_but_follows_source_and_versions(
    kp: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    base, _ = run(kp)
    edited, _ = run(kp, finding=finding(observation="Different words."))
    other_spec, _ = run(kp, spec_path="docs/specs/t")
    assert base["observation_id"] == edited["observation_id"] != other_spec["observation_id"]
    monkeypatch.setattr(kp, "PROJECTION_POLICY_VERSION", "projection-v2")
    assert run(kp)[0]["observation_id"] != base["observation_id"]
    monkeypatch.undo()
    cs = kp._content_safety()
    monkeypatch.setattr(cs, "POLICY_VERSION", "slice-9.v1")
    bumped, _ = run(kp)
    assert bumped["observation_id"] != base["observation_id"]
    assert bumped["observed"]["policy_version"] == "slice-9.v1"


def test_projection_is_pure(kp: ModuleType) -> None:
    rec, rep, fin = receipt(), report(), finding()
    snapshot = copy.deepcopy((rec, rep, fin))
    run(kp, rec=rec, report=rep, finding=fin)
    assert (rec, rep, fin) == snapshot


def test_replay_is_byte_identical_across_fresh_processes(kp: ModuleType) -> None:
    """AC-0002: identities and payloads do not depend on the process."""
    inproc = kp.canonical_json(run(kp)[0])
    code = (
        "import importlib.util,json,sys;"
        f"s=importlib.util.spec_from_file_location('p',{str(dfs.SCRIPTS / '_knowledge_projection.py')!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        f"r={receipt()!r};f={finding()!r};rep={report()!r};"
        "o=m.project_record('evidence-receipt.v1',r,spec_path='docs/specs/s',transaction_id='tx-1',"
        "superseded=False,report=rep,finding=f).observation;"
        "sys.stdout.write(m.canonical_json(o))"
    )
    outs = {
        subprocess.run([sys.executable, "-I", "-c", code], capture_output=True, check=True,
                       env={"PYTHONHASHSEED": seed}).stdout.decode()
        for seed in ("1", "2", "random")
    }
    assert outs == {inproc}


# ── The command line ─────────────────────────────────────────────────────────

CLI = dfs.SCRIPTS / "delivery-fact-feed.py"


def cli(root: Path, *args: str, shadow: bool = True) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k != "WORK_LOOP_SHADOW_SERVICES"}
    if shadow:
        env["WORK_LOOP_SHADOW_SERVICES"] = "1"
    env["PYTHONIOENCODING"] = "cp1252"
    return subprocess.run([sys.executable, "-I", str(CLI), "--root", str(root), *args],
                          capture_output=True, env=env)


def test_cli_prints_one_deterministic_page_and_pages_through_continuations(tmp_path: Path) -> None:
    repo = dfs.FeedRepo(tmp_path)
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one")
    for _ in range(1001):
        repo.add_engine_transition("alpha", store)
    before = repo.tree_state()
    first = cli(repo.root)
    again = cli(repo.root)
    assert first.returncode == 0 and first.stderr == b""
    assert first.stdout == again.stdout and first.stdout.endswith(b"\n")
    page = json.loads(first.stdout)
    assert len(page["entries"]) == 1000 and page["continuation"]
    nxt = json.loads(cli(repo.root, "--continuation", page["continuation"]).stdout)
    assert nxt["continuation"] is None and nxt["first_ordinal"] == 1000
    assert repo.tree_state() == before


def test_cli_with_the_flag_unset_prints_a_complete_empty_snapshot(tmp_path: Path) -> None:
    repo = dfs.FeedRepo(tmp_path)
    store = repo.open_store("alpha")
    repo.add_review_failure("alpha", store, "one")
    result = cli(repo.root, shadow=False)
    page = json.loads(result.stdout)
    assert result.returncode == 0
    assert page["entries"] == [] and page["continuation"] is None
    assert page["shadow_services"] == "disabled"


def test_cli_refusal_prints_a_closed_code_and_nothing_on_stdout(tmp_path: Path) -> None:
    repo = dfs.FeedRepo(tmp_path)
    repo.open_store("alpha")
    (repo.root / "docs" / "specs" / "linked").symlink_to(tmp_path, target_is_directory=True)
    result = cli(repo.root)
    assert (result.returncode, result.stdout) == (2, b"")
    assert result.stderr == b"delivery-fact-feed: refused: specs-entry-refused\n"
    bad = cli(repo.root, "--continuation", "nonsense")
    assert (bad.returncode, bad.stdout) == (2, b"")
    assert b"token-invalid" in bad.stderr and b"Traceback" not in bad.stderr
