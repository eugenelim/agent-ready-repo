"""AC-0018 benchmark harness: evaluator latency for 1,000 criteria × 100,000 receipts.

Runs the committed entry point
``packs/core/.apm/skills/work-loop/scripts/_acceptance_benchmark.py``
with a ``tmp_path`` output path so no result file lands in the source tree.

AC-0018 asserts that p95 evaluation latency is within 2 seconds across
exactly 1,000 approved criteria and 100,000 admitted evidence records,
with a fixed timed-run count (TIMED_RUNS=100) and warm-up policy
(WARMUP_RUNS=5).
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

SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "scripts"
)


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


def test_evaluator_p95_latency_benchmark(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC-0018: p95 evaluator latency must be within 2 seconds.

    Invokes the committed entry point with a ``tmp_path`` output path so no
    result file lands in the source tree.  Verifies the result JSON structure
    and asserts the AC-0018 p95 bound.
    """
    bm = _load_module("acc_bm_wrapper", SCRIPTS / "_acceptance_benchmark.py")

    output_path = tmp_path / "benchmark-acceptance-result.json"
    exit_code = bm.main(["--output", str(output_path)])
    assert exit_code == 0, f"entry point exited {exit_code}"
    assert output_path.exists(), f"result file not written: {output_path}"

    result = json.loads(output_path.read_text(encoding="utf-8"))
    assert result["harness"] == "acceptance_benchmark"
    assert "evaluator" in result
    ev = result["evaluator"]
    assert ev["num_criteria"] == bm.NUM_CRITERIA
    assert ev["num_receipts"] == bm.NUM_RECEIPTS
    p95 = ev["p95_seconds"]
    p50 = ev["p50_seconds"]

    with capsys.disabled():
        print(
            f"\nAC-0018 evaluator benchmark:\n"
            f"  corpus:     {bm.NUM_CRITERIA} criteria × {bm.NUM_RECEIPTS} receipts\n"
            f"  warm-up:    {bm.WARMUP_RUNS} runs (discarded)\n"
            f"  timed runs: {bm.TIMED_RUNS}\n"
            f"  p95:        {p95 * 1000:.1f} ms  (bound: 2000.0 ms)\n"
            f"  p50:        {p50 * 1000:.1f} ms"
        )

    # AC-0018: p95 from call entry to full verdict return must be within 2 seconds.
    assert p95 <= 2.0, (
        f"AC-0018 p95 latency {p95 * 1000:.1f} ms exceeds the 2000 ms bound "
        f"({bm.NUM_CRITERIA} criteria × {bm.NUM_RECEIPTS} receipts, "
        f"{bm.TIMED_RUNS} timed runs after {bm.WARMUP_RUNS} warm-up runs)"
    )
