"""The supervisor CI lanes list their suites and shard them so nothing is skipped or run twice.

Roster-owned: it reads the repository's workflow files, which a pack suite may not
reach. The POSIX lane runs the crash corpus in shards chosen by test name; the Windows
lane runs three slow suites in legs that each keep every ``n``th collected test.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORK_LOOP_TESTS = REPO_ROOT / "packs" / "core" / "tests" / "skills" / "work-loop"
CORPUS = WORK_LOOP_TESTS / "test_supervisor_crash_corpus.py"
WINDOWS_SUITES = {
    "product-ref": "test_supervisor_product_ref.py",
    "attempt": "test_supervisor_attempt.py",
    "pinning": "test_supervisor_pinning.py",
}


def _workflow(name: str) -> str:
    path = REPO_ROOT / ".github" / "workflows" / name
    if not path.exists():
        pytest.skip("the repository's workflows are not part of this checkout")
    return path.read_text("utf-8")


def _job(text: str, name: str) -> str:
    match = re.search(rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  [a-z0-9_-]+:\n|^  # ──|\Z)", text)
    assert match is not None, f"job {name} is missing"
    return match.group(1)


def _collect(path: Path, selector: str | None = None, shard: str | None = None) -> list[str]:
    """The test ids pytest collects for *path* as a CI leg would, after ``-k`` and sharding."""
    ids: list[str] = []

    class Collect:
        def pytest_collection_finish(self, session: Any) -> None:
            ids.extend(item.nodeid for item in session.items)

    args = [str(path), "--collect-only", "-q", "-p", "no:cacheprovider"]
    if selector is not None:
        args += ["-k", selector]
    saved = os.environ.get("WORK_SUPERVISOR_SHARD")
    if shard is None:
        os.environ.pop("WORK_SUPERVISOR_SHARD", None)
    else:
        os.environ["WORK_SUPERVISOR_SHARD"] = shard
    try:
        assert pytest.main(args, plugins=[Collect()]) in (0, 5)
    finally:
        if saved is None:
            os.environ.pop("WORK_SUPERVISOR_SHARD", None)
        else:
            os.environ["WORK_SUPERVISOR_SHARD"] = saved
    return ids


def test_the_ci_jobs_list_the_product_ref_suites() -> None:
    posix = _job(_workflow("catalogue-tooling-ci-gates.yml"), "supervisor-integration")
    assert "test_supervisor_product_ref.py" in posix
    assert 'WORK_SUPERVISOR_INTEGRATION: "1"' in posix and "timeout-minutes:" in posix
    windows_text = _workflow("build-check-windows.yml")
    windows = _job(windows_text, "supervisor-windows")
    for suite in WINDOWS_SUITES.values():
        assert f"python -m pytest packs/core/tests/skills/work-loop/{suite} " in windows
    assert 'WORK_SUPERVISOR_INTEGRATION: "1"' in windows and "timeout-minutes:" in windows
    assert "- supervisor-windows" in _job(windows_text, "build-check-windows")


def test_the_crash_corpus_shards_are_disjoint_nonempty_and_cover_every_test() -> None:
    job = _job(_workflow("catalogue-tooling-ci-gates.yml"), "supervisor-integration-corpus")
    selectors = re.findall(r'test_supervisor_crash_corpus\.py -k "([^"]+)"', job)
    assert len(selectors) == 3, selectors
    assert 'WORK_SUPERVISOR_INTEGRATION: "1"' in job
    everything = _collect(CORPUS)
    shards = [_collect(CORPUS, selector) for selector in selectors]
    assert all(shards), [len(shard) for shard in shards]
    flat = [item for shard in shards for item in shard]
    assert len(flat) == len(set(flat)), "two shards run the same test"
    assert sorted(flat) == sorted(everything), "a corpus test runs in no shard"


@pytest.mark.parametrize("suite", sorted(WINDOWS_SUITES))
def test_the_windows_legs_of_a_suite_are_disjoint_nonempty_and_cover_it(suite: str) -> None:
    job = _job(_workflow("build-check-windows.yml"), "supervisor-windows")
    legs = re.findall(rf'- suite: {suite}\n\s+shard: "(\d+)/(\d+)"', job)
    assert legs, f"no leg runs {suite}"
    counts = {int(count) for _, count in legs}
    assert len(counts) == 1, f"{suite} legs disagree on the shard count: {legs}"
    count = counts.pop()
    assert sorted(int(index) for index, _ in legs) == list(range(count)), legs
    path = WORK_LOOP_TESTS / WINDOWS_SUITES[suite]
    everything = _collect(path)
    parts = [_collect(path, shard=f"{index}/{count}") for index in range(count)]
    assert all(parts), [len(part) for part in parts]
    flat = [item for part in parts for item in part]
    assert len(flat) == len(set(flat)), "two legs run the same test"
    assert sorted(flat) == sorted(everything), "a test runs in no leg"
