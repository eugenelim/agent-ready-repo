"""Environment, isolation, and parity proofs for per-record read quarantine.

Mode: TDD through integration tests.  A fault in the Git or operating-system
read is never a record fault, the quarantine paths run with no repository
package available and open no delivery schema, a named lookup explains its own
excluded entry, and the strict and excluding readers agree on valid records.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest
import quarantine_support as qs
from knowledge_test_support import PROJECT_KNOWLEDGE_SCRIPT, load_knowledge_store_module

PENDING = {"selection_mode": "direct-maintainer-pending", "scope": "packs/core"}
SECOND = "contracts/second-contract"


@pytest.fixture
def store():
    return load_knowledge_store_module()


@pytest.fixture
def repo(tmp_path: Path, store) -> Path:
    return qs.knowledge_repo(tmp_path / "repo", store)


def _two_topics(store, repo: Path) -> None:
    qs.publish(
        store,
        repo,
        qs.topic(store, repo),
        qs.topic(store, repo, topic_key=SECOND, title="A second durable contract"),
    )


# ── A Git or operating-system fault is not a record fault ────────────────────


@pytest.mark.parametrize("fault", ("nonzero-exit", "spawn-failure", "size-probe-failure"))
def test_a_git_read_failure_on_one_topic_blob_refuses_the_whole_enquiry(
    repo: Path, store, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    _two_topics(store, repo)
    assert len(store.enquire(repo, qs.QUERY)["receipt"]["selected_topics"]) == 2

    real_run = subprocess.run
    real_check_output = subprocess.check_output
    probes = {"count": 0}

    def run(command: list[str], *args: Any, **kwargs: Any) -> Any:
        if fault != "size-probe-failure" and command[1:2] == ["show"] and "public-contracts" in command[-1]:
            if fault == "spawn-failure":
                raise OSError("injected spawn failure")
            return subprocess.CompletedProcess(command, 128)
        return real_run(command, *args, **kwargs)

    def check_output(command: list[str], *args: Any, **kwargs: Any) -> Any:
        if fault == "size-probe-failure" and command[1:3] == ["cat-file", "-s"]:
            probes["count"] += 1
            if probes["count"] > 1:  # the first probe sizes the topic map
                raise subprocess.CalledProcessError(128, command)
        return real_check_output(command, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "check_output", check_output)

    with pytest.raises(store.KnowledgeStoreError) as refused:
        store.enquire(repo, qs.QUERY)

    assert refused.value.diagnostic["reason_code"] == "map_mismatch"
    assert refused.value.environmental is True


def test_writers_still_see_the_same_code_for_a_git_read_failure(
    repo: Path, store, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_args: Any, **_kwargs: Any) -> Any:
        raise subprocess.CalledProcessError(128, ["git"])

    monkeypatch.setattr(subprocess, "check_output", broken)
    with pytest.raises(store.KnowledgeStoreError) as refused:
        store._head_snapshot(repo)
    assert refused.value.diagnostic["reason_code"] == "map_mismatch"


# ── A named lookup explains its own excluded entry ───────────────────────────


def test_a_named_lookup_of_an_excluded_entry_reports_its_closed_reason_and_locator(
    repo: Path, store
) -> None:
    _two_topics(store, repo)
    topic_map = qs.read_map(repo)
    first = topic_map["entries"][0]
    topic_map["entries"].append(
        {**first, "topic_key": "contracts/ghost", "path": "topics/contracts/ghost.json"}
    )
    qs.write_map(repo, topic_map)
    qs.commit(repo, "test: a map entry with no topic file")

    for lookup in (store.read_committed_topic, store.read_freshness_source):
        with pytest.raises(store.KnowledgeStoreError) as refused:
            lookup(repo, "contracts/ghost")
        error = refused.value
        assert error.diagnostic["reason_code"] == "map_mismatch"
        assert error.diagnostic["path"] == "docs/knowledge/topics.index.json"
        assert [(e["reason_code"], e["path"], e["entry"]) for e in error.quarantine] == [
            ("orphaned", "docs/knowledge/topics.index.json", 3)
        ]
        assert set(error.quarantine[0]) == {"version", "reason_code", "path", "entry"}

    with pytest.raises(store.KnowledgeStoreError) as unknown:
        store.read_committed_topic(repo, "contracts/never-listed")
    assert unknown.value.quarantine is None
    assert "path" not in unknown.value.diagnostic


# ── The strict and excluding readers agree on valid records ──────────────────


def test_strict_and_excluding_readers_agree_on_every_valid_record(repo: Path, store) -> None:
    _two_topics(store, repo)
    first = qs.capture(repo, store, "A first lesson the readers must agree on.")
    qs.capture(repo, store, "A second lesson the readers must agree on.")
    store.write_terminal_disposition(
        repo,
        first["capture_id"],
        "rejected",
        reason_code="not_reusable",
        recorded_at="2026-08-13T12:41:00Z",
    )
    snapshot = store._head_snapshot(repo)

    strict_map = store._read_committed_topic_map(repo, snapshot)
    quarantine = store._Quarantine()
    lenient_map = store._read_committed_topic_map_excluding(repo, snapshot, quarantine)
    assert {k: v for k, v in lenient_map.items() if k != "positions"} == strict_map
    assert lenient_map["positions"] == {
        entry["path"]: position for position, entry in enumerate(strict_map["entries"], start=1)
    }
    for entry in strict_map["entries"]:
        strict_topic = store._read_committed_topic(repo, snapshot, entry, body_budget=[0])
        assert strict_topic["topic_key"] == entry["topic_key"]

    partitions = store._observation_partitions(repo)
    assert store._observation_partitions(repo, quarantine=quarantine) == partitions
    strict_window = store._load_pending_partition_window(repo, partitions)
    lenient_window = store._load_pending_partitions_excluding(repo, partitions, quarantine)
    assert lenient_window == strict_window
    assert quarantine.report() == []


# ── Quarantine paths run with no repository package and open no delivery schema ──

_DRIVER = textwrap.dedent(
    """
    import builtins, contextlib, importlib.util, io, json, os, sys

    script, repo, *argv = sys.argv[1:]
    opened = []
    real_open, real_os_open = builtins.open, os.open

    def open_spy(file, *args, **kwargs):
        opened.append(os.fspath(file) if not isinstance(file, int) else "<fd>")
        return real_open(file, *args, **kwargs)

    def os_open_spy(path, *args, **kwargs):
        opened.append(os.fspath(path))
        return real_os_open(path, *args, **kwargs)

    builtins.open, io.open, os.open = open_spy, open_spy, os_open_spy
    spec = importlib.util.spec_from_file_location("isolated_project_knowledge", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules["isolated_project_knowledge"] = module
    spec.loader.exec_module(module)
    raw = io.BytesIO()
    captured = io.TextIOWrapper(raw, encoding="utf-8", write_through=True)
    with contextlib.redirect_stdout(captured):
        code = module.main([*argv, "--repo-root", repo])
    json.dump(
        {
            "code": code,
            "stdout": raw.getvalue().decode("utf-8"),
            "opened": opened,
            "modules": sorted(name for name in sys.modules if name.split(".")[0] in
                              {"agentbundle", "credbroker", "jsonschema", "referencing"}),
        },
        sys.__stdout__,
    )
    """
)


def _isolated(tmp_path: Path, repo: Path, args: list[str], stdin: dict[str, Any]) -> dict[str, Any]:
    driver = tmp_path / "driver.py"
    driver.write_text(_DRIVER, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, "-I", "-S", str(driver), str(PROJECT_KNOWLEDGE_SCRIPT), str(repo), *args],
        input=json.dumps(stdin).encode("utf-8"),
        capture_output=True,
        cwd=repo,
        env={"PATH": os.environ.get("PATH", "")},
    )
    assert done.returncode == 0, done.stderr.decode("utf-8", errors="replace")
    return json.loads(done.stdout)


@pytest.mark.parametrize("path", ("enquire", "pending"))
def test_the_quarantine_paths_run_isolated_and_open_no_delivery_schema(
    tmp_path: Path, repo: Path, store, path: str
) -> None:
    _two_topics(store, repo)
    kept = qs.capture(repo, store, "A lesson the pending page must keep.")
    topic_map = qs.read_map(repo)
    topic_map["entries"].append({"topic_key": "x"})  # a malformed entry, excluded on its own
    qs.write_map(repo, topic_map)
    qs.commit(repo, "test: a malformed map entry")
    first = qs.event_lines(repo, kept["partition"])[0]
    qs.append_line(repo, kept["partition"], qs.dumps(qs.tampered_capture(first, "identity-mismatch")))

    if path == "enquire":
        result = _isolated(tmp_path, repo, ["--enquire"], qs.QUERY)
        marker = "<knowledge-quarantine"
    else:
        result = _isolated(tmp_path, repo, ["--distill", "--pending"], PENDING)
        marker = '"reason_code": "inconsistent"'

    assert result["code"] == 0
    assert marker in result["stdout"] or marker.replace(": ", ":") in result["stdout"]
    assert result["modules"] == []
    assert result["opened"], "the file-open spy saw no open, so the assertion below proves nothing"
    assert not [name for name in result["opened"] if "contracts/delivery" in name]


@pytest.mark.parametrize("char", ("­", "ㅤ", "️", "\U000e0041"))
def test_a_locator_with_a_default_ignorable_character_falls_back_to_an_ordinal(
    repo: Path, store, char: str
) -> None:
    _two_topics(store, repo)
    (repo / "docs/knowledge/topics/contracts" / f"stray{char}name.json").write_bytes(b"{}\n")
    qs.commit(repo, "test: an unlisted topic file with an invisible character in its name")

    result = store.enquire(repo, qs.QUERY)

    orphan = [entry for entry in result["quarantine"] if entry["reason_code"] == "orphaned"]
    assert len(orphan) == 1
    assert "path" not in orphan[0] and "ordinal" in orphan[0]
