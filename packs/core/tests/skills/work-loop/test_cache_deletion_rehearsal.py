"""The cache-deletion rehearsal (legacy-engine-cutover AC-0010).

A fixture run is admitted and records three steps (a stub, then two
implementations). The test first names what that run wrote:

* ``<spec>/.supervisor/``: ``run.json``, ``journal.jsonl``,
  ``security-events.jsonl`` and ``.gitignore``, the advisory local journal.
* ``.loop-run/events.jsonl``: the run's event projection under the repository root.
* ``<spec>/delivery/``: ``approvals.jsonl`` and ``evidence.jsonl``, the records
  that stay.
* ``<git-dir>/agentbundle-supervisor/<run-id>/``: the attempt store, run state
  rather than a cache, which also stays.

The fixture run installs no pack projection: nothing under ``.claude/``,
``.agents/`` or similar exists, so the deletion covers the two cache paths above.
It then deletes the caches and compares, byte for byte, ``status --check``, the
per-criterion acceptance verdicts (``acceptance-verdict.v1``) and
``delivery/evidence.jsonl``.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

# Each shared helper by literal path, so every file a suite loads stays visibly
# inside this pack.
_HELPER_PATHS = {
    "supervisor_harness": Path(__file__).resolve().parent / "supervisor_harness.py",
    "supervisor_support": Path(__file__).resolve().parent / "supervisor_support.py",
}


def _helper(name: str) -> ModuleType:
    """Load a shared supervisor test helper by path under a pack- and skill-qualified name."""
    alias = f"core_work_loop_{name}"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER_PATHS[name])
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _helper("supervisor_harness")

SPEC = h.SPEC_DIR


def _status_check(repo: Path) -> tuple[int, bytes]:
    """``status --check`` run in-process: its exit code and the exact bytes it printed."""
    out = io.StringIO()
    with h.git_identity(), contextlib.redirect_stdout(out):
        code = h.cli.main(["status", SPEC, "--check"], cwd=repo)
    return code, out.getvalue().encode("utf-8")


def _verdicts(repo: Path) -> bytes:
    """The ``acceptance-verdict.v1`` records for every criterion, evaluated from receipts."""
    ws = h.workspace(repo)
    state = h.loop.derive(ws)
    readiness = h.cli._supervisor("_supervisor_readiness.py")
    ids = readiness.criteria(ws)
    fingerprint = readiness.delivery_subject(ws, state)["acceptance_fingerprint"]
    records = ws.open_evidence().evaluate_verdicts(
        readiness._properties(state, ids), fingerprint, h.loop.sibling("_acceptance.py")
    )
    assert len(records) == len(ids) >= 1
    return json.dumps(records, sort_keys=True).encode("utf-8")


def _snapshot(repo: Path) -> dict[str, Any]:
    code, status = _status_check(repo)
    return {
        "status": (code, status),
        "verdicts": _verdicts(repo),
        "evidence": (repo / SPEC / "delivery" / "evidence.jsonl").read_bytes(),
    }


def _files(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_deleting_the_caches_changes_nothing_a_verb_reads(tmp_path: Path) -> None:
    repo = h.make_repo(tmp_path)
    code, started = h.start(repo)
    assert code == 0, started
    controller = h.Controller(repo, tmp_path / "effects.log")
    for _ in range(3):
        code, payload = h.run_cli(repo, "next", SPEC)
        assert code == 0, payload
        assert controller.report(controller.work(payload["request"]))[0] == 0

    # Step one: name what the run wrote, so the deletion is not near-empty.
    local = repo / SPEC / ".supervisor"
    events = repo / ".loop-run" / "events.jsonl"
    delivery = repo / SPEC / "delivery"
    store = repo / ".git" / "agentbundle-supervisor" / started["run_id"]
    assert {p.name for p in local.iterdir()} >= {"run.json", "journal.jsonl", "security-events.jsonl", ".gitignore"}
    assert events.is_file()
    assert {p.name for p in delivery.iterdir()} == {"approvals.jsonl", "evidence.jsonl"}
    assert (store / "pins.json").is_file() and any((store / "attempts").iterdir())
    assert delivery.joinpath("evidence.jsonl").stat().st_size > 0
    assert not (repo / ".claude").exists() and not (repo / ".agents").exists()

    before = _snapshot(repo)
    assert before["status"][0] == 0
    kept_before = {"delivery": _files(delivery), "store": _files(store)}

    shutil.rmtree(local)
    events.unlink()
    assert not local.exists() and not events.exists()

    after = _snapshot(repo)
    assert after["status"] == before["status"]
    assert after["verdicts"] == before["verdicts"]
    assert after["evidence"] == before["evidence"]
    assert _files(delivery) == kept_before["delivery"]
    assert _files(store) == kept_before["store"]
