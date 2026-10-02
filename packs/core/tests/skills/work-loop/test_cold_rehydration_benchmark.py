"""AC-0019 benchmark: cold-rehydration latency for evidence-store replay.

Runs ``acceptance_benchmark_harness.run_cold_rehydration`` (via the harness's
``main`` entry point) and asserts that a fresh subprocess can read the evidence
log, build in-memory indexes, and evaluate NUM_CRITERIA verdicts within 10 seconds
(wall-clock time, parent side).

Verification mode: goal-based (plan.md T7 Done-when gate).
"""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

# ── Path anchor ───────────────────────────────────────────────────────────────

_HARNESS_PATH = Path(__file__).resolve().parent / "acceptance_benchmark_harness.py"


# ── Module loader ─────────────────────────────────────────────────────────────


def _load_module(name: str, path: Path) -> ModuleType:
    info = os.lstat(path)
    assert stat.S_ISREG(info.st_mode), f"not a regular file: {path}"
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod
    finally:
        sys.dont_write_bytecode = prev


# ── Benchmark test ────────────────────────────────────────────────────────────


def test_cold_rehydration_elapsed_within_bound(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-0019: cold rehydration of the evidence log completes within 10 seconds.

    Invokes the committed entry point (``acceptance_benchmark_harness.main``)
    with a ``tmp_path`` output path so no result file lands in the source tree.
    Verifies that:
      - ``cold_rehydration.elapsed_seconds < 10.0``
      - ``cold_rehydration.verdict_count == NUM_CRITERIA`` (all verdicts evaluated)
    """
    bm = _load_module("acc_crh_bm_wrapper", _HARNESS_PATH)

    output_path = tmp_path / "benchmark-cold-rehydration-result.json"
    exit_code = bm.main(["--output", str(output_path)])
    assert exit_code == 0, f"benchmark harness entry point exited {exit_code}"
    assert output_path.exists(), f"result file not written: {output_path}"

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["harness"] == "acceptance_benchmark"
    assert "cold_rehydration" in result, (
        "cold_rehydration key missing from result; run_cold_rehydration returned None "
        "(check stderr above for subprocess failure details)"
    )

    crh = result["cold_rehydration"]
    elapsed = crh["elapsed_seconds"]
    verdict_count = crh["verdict_count"]

    with capsys.disabled():
        print(
            f"\nAC-0019 cold-rehydration benchmark:\n"
            f"  criteria:   {crh['num_criteria']}\n"
            f"  verdicts:   {verdict_count}\n"
            f"  elapsed:    {elapsed:.3f} s  (bound: 10.0 s)"
        )

    # AC-0019: cold rehydration must complete within 10 seconds.
    assert elapsed < 10.0, (
        f"AC-0019 cold rehydration elapsed {elapsed:.3f} s exceeds the 10 s bound "
        f"({crh['num_criteria']} criteria, {verdict_count} verdicts evaluated)"
    )

    # Sanity: all NUM_CRITERIA verdicts were evaluated.
    assert verdict_count == bm.NUM_CRITERIA, (
        f"expected {bm.NUM_CRITERIA} verdicts, got {verdict_count}"
    )
