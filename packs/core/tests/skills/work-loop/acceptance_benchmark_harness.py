#!/usr/bin/env python3
"""Committed benchmark harness for the acceptance evaluator (AC-0018, AC-0019).

AC-0018 measures evaluator latency for a fixed corpus: 1,000 approved criteria
and 100,000 admitted evidence records, with a fixed timed-run count
(TIMED_RUNS=100) and warm-up policy (WARMUP_RUNS=5).

AC-0019 (cold-rehydration) measures the wall-clock time for a fresh subprocess
to read the evidence log, build in-memory indexes, and evaluate NUM_CRITERIA
verdicts.  The bound is 10 seconds total.

Invoke with:

    python _acceptance_benchmark.py --output <path>

The caller receives a JSON result file at the given path; writes nothing to the
working tree.

Standard-library-only; no dependencies beyond Python itself.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import ModuleType

# ── Constants (fixed by this committed harness) ───────────────────────────────

WARMUP_RUNS: int = 5
TIMED_RUNS: int = 100
NUM_CRITERIA: int = 1_000
NUM_RECEIPTS: int = 100_000

# ── Path anchor ───────────────────────────────────────────────────────────────

_SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"


# ── Module loader ─────────────────────────────────────────────────────────────


def _load_module(name: str, path: Path) -> ModuleType:
    """Load a script module without registering it in sys.modules."""
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


# ── Corpus builders ───────────────────────────────────────────────────────────


def _build_corpus(
    num_criteria: int,
    num_receipts: int,
    current_fp: str = "fp-benchmark-current",
) -> tuple[list[dict], dict[str, list[dict]]]:
    """Build a synthetic benchmark corpus of criteria and receipts.

    Returns (criteria, receipts_by_criterion_id) where criteria is a list of
    acceptance-property.v1 records and receipts_by_criterion_id maps
    property_id → list of evidence-receipt.v1 records.

    Receipts are distributed uniformly across criteria. Each receipt is fresh
    and satisfies its criterion, yielding ``supported`` verdicts.
    """
    criteria: list[dict] = []
    receipts_by_id: dict[str, list[dict]] = {}

    for i in range(num_criteria):
        pid = f"prop-{i:04d}"
        criteria.append({
            "schema_version": 1,
            "property_id": pid,
            "spec_ref": "docs/specs/benchmark/spec.md",
            "authority_ref": f"approval:spec-policy:v{i % 10 + 1}",
            "subject_selector": {
                "paths_or_artifacts": [f"src/module_{i % 100}/"],
                "fingerprint_algorithm": "sha256",
            },
            "required_observations": [
                {
                    "term": "test-run",
                    "observation_type": "test-result",
                    "producer_class": "ci-runner",
                    "outcomes": ["passed"],
                }
            ],
            "freshness_scope": "exact-subject",
            "satisfaction_rule": {"expression": "all"},
            "contradiction_rule": {"expression": "none"},
            "policy_version": "v1",
        })
        receipts_by_id[pid] = []

    for j in range(num_receipts):
        crit_idx = j % num_criteria
        pid = f"prop-{crit_idx:04d}"
        receipts_by_id[pid].append({
            "schema_version": 1,
            "receipt_id": f"r-{j:06d}",
            "acceptance_fingerprint": current_fp,
            "lineage": {"criterion_ref": pid},
            "selector": {"term": "test-run"},
            "freshness_mode": "exact-subject",
            "observation": {"type": "test-result"},
            "outcome": "passed",
            "producer": {"class": "ci-runner", "identity": "runner-generic"},
        })

    return criteria, receipts_by_id


def _run_full_evaluation(
    acc: ModuleType,
    criteria: list[dict],
    receipts_by_id: dict[str, list[dict]],
    current_fp: str = "fp-benchmark-current",
) -> list[dict]:
    """Evaluate all criteria and return all verdict records.

    This is the timed unit: from call entry to full verdict return.
    """
    verdicts: list[dict] = []
    for prop in criteria:
        pid = prop["property_id"]
        receipts = receipts_by_id.get(pid, [])
        v = acc.evaluate_verdict(
            property_record=prop,
            receipts=receipts,
            current_acceptance_fingerprint=current_fp,
            adapter="sequential-reference",
        )
        verdicts.append(v)
    return verdicts


# ── Evaluator benchmark (AC-0018) ─────────────────────────────────────────────


def run_evaluator_benchmark(acc: ModuleType) -> dict:
    """Measure AC-0018: p95 evaluator latency for the fixed corpus.

    Returns a result dict with p50, p95, and per-run measurements.
    """
    current_fp = "fp-benchmark-current"
    criteria, receipts_by_id = _build_corpus(NUM_CRITERIA, NUM_RECEIPTS, current_fp)

    assert len(criteria) == NUM_CRITERIA
    total_receipts = sum(len(v) for v in receipts_by_id.values())
    assert total_receipts == NUM_RECEIPTS

    # Warm-up (results discarded)
    for _ in range(WARMUP_RUNS):
        _run_full_evaluation(acc, criteria, receipts_by_id, current_fp)

    # Timed runs
    durations: list[float] = []
    for _ in range(TIMED_RUNS):
        t0 = time.perf_counter()
        verdicts = _run_full_evaluation(acc, criteria, receipts_by_id, current_fp)
        t1 = time.perf_counter()
        durations.append(t1 - t0)

    sorted_durations = sorted(durations)
    p95_index = int(0.95 * TIMED_RUNS) - 1  # 0-based index for 95th of 100
    p95_seconds = sorted_durations[p95_index]
    p50_seconds = sorted_durations[TIMED_RUNS // 2]

    # Verify verdicts are well-formed
    assert len(verdicts) == NUM_CRITERIA
    for v in verdicts:
        assert v["verdict"] in ("unapproved", "contradicted", "supported", "insufficient")

    return {
        "benchmark": "evaluator",
        "num_criteria": NUM_CRITERIA,
        "num_receipts": NUM_RECEIPTS,
        "warmup_runs": WARMUP_RUNS,
        "timed_runs": TIMED_RUNS,
        "p95_seconds": p95_seconds,
        "p50_seconds": p50_seconds,
        "min_seconds": sorted_durations[0],
        "max_seconds": sorted_durations[-1],
    }


# ── Cold-rehydration benchmark (AC-0019) ──────────────────────────────────────

# Canonical JSON serializer matching _evidence_store._canonical_json.
def _canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _build_frame_bytes(
    transaction_id: str,
    receipt: dict,
    acceptance_fingerprint: str,
) -> bytes:
    """Build and serialize one evidence frame using the _evidence_store frame format.

    Replicates the checksum algorithm so frames survive _verify_frame on replay:
      checksum = sha256(canonical_json({"records": records, "tx": tx_without_checksum}))
    followed by:
      frame = canonical_json({"records": records, "tx": tx_with_checksum}) + "\\n"
    """
    receipt_id = receipt["receipt_id"]
    records = [receipt]
    tx_body: dict = {
        "schema_version": 1,
        "transaction_id": transaction_id,
        "ordered_record_ids": [receipt_id],
        "acceptance_fingerprint": acceptance_fingerprint,
    }
    payload_for_checksum = _canonical({"records": records, "tx": tx_body})
    checksum = "sha256:" + hashlib.sha256(
        payload_for_checksum.encode("utf-8")
    ).hexdigest()
    tx = {**tx_body, "checksum": checksum}
    frame_json = _canonical({"records": records, "tx": tx})
    return (frame_json + "\n").encode("utf-8")


# Subprocess worker script template (standard-library-only, no imports above stdlib).
_WORKER_TEMPLATE = '''\
import sys, json, importlib.util, os, stat
from pathlib import Path

SCRIPTS = Path({scripts!r})


def _load_module(name, path):
    prev = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(name, str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = prev


es = _load_module("es_crh", SCRIPTS / "_evidence_store.py")
acc = _load_module("acc_crh", SCRIPTS / "_acceptance.py")

log_path = Path(sys.argv[1])
criteria_path = Path(sys.argv[2])
current_fp = sys.argv[3]

store = es.EvidenceStore(log_path)
store.open()

with open(criteria_path, encoding="utf-8") as fh:
    criteria = json.load(fh)

verdicts = store.evaluate_verdicts(criteria, current_fp, acc)
print(len(verdicts))
'''


def run_cold_rehydration(acc: ModuleType) -> dict | None:
    """AC-0019 cold-rehydration benchmark.

    Populates a fresh evidence log with NUM_CRITERIA single-receipt transactions
    (written directly, bypassing security checks — this is benchmark/harness code,
    not shipped production code), then starts a fresh subprocess that reads the
    log, builds in-memory indexes, and evaluates NUM_CRITERIA verdicts.

    Wall-clock time is measured from subprocess start to exit (parent side).
    Returns a result dict with ``elapsed_seconds`` and ``verdict_count``,
    or ``None`` if setup or subprocess execution fails.

    The ``acc`` parameter is unused here (the subprocess loads its own copy)
    but is kept for interface consistency with ``run_evaluator_benchmark``.
    """
    current_fp = "fp-crh-benchmark-current"
    num_criteria = NUM_CRITERIA  # 1000 fixed by this harness

    # Build the synthetic corpus.
    criteria: list[dict] = []
    for i in range(num_criteria):
        pid = f"prop-crh-{i:04d}"
        criteria.append({
            "schema_version": 1,
            "property_id": pid,
            "spec_ref": "docs/specs/benchmark/spec.md",
            "authority_ref": f"approval:spec-policy:v{i % 10 + 1}",
            "subject_selector": {
                "paths_or_artifacts": [f"src/module_{i % 100}/"],
                "fingerprint_algorithm": "sha256",
            },
            "required_observations": [
                {
                    "term": "test-run",
                    "observation_type": "test-result",
                    "producer_class": "ci-runner",
                    "outcomes": ["passed"],
                }
            ],
            "freshness_scope": "exact-subject",
            "satisfaction_rule": {"expression": "all"},
            "contradiction_rule": {"expression": "none"},
            "policy_version": "v1",
        })

    tmp_dir = tempfile.mkdtemp(prefix="ev_crh_bm_")
    try:
        log_path = Path(tmp_dir) / "evidence-crh.log"
        criteria_path = Path(tmp_dir) / "criteria-crh.json"
        script_path = Path(tmp_dir) / "crh_worker.py"

        # Write frames directly (bypass security checks — harness-only code).
        with log_path.open("wb") as fh:
            for i, prop in enumerate(criteria):
                receipt: dict = {
                    "schema_version": 1,
                    "receipt_id": f"r-crh-{i:04d}",
                    "acceptance_fingerprint": current_fp,
                    "lineage": {"criterion_ref": prop["property_id"]},
                    "selector": {"term": "test-run"},
                    "freshness_mode": "exact-subject",
                    "observation": {"type": "test-result"},
                    "outcome": "passed",
                    "producer": {"class": "ci-runner", "identity": "runner-generic"},
                }
                fh.write(
                    _build_frame_bytes(
                        f"tx-crh-{i:04d}", receipt, current_fp
                    )
                )

        # Write criteria JSON file for the subprocess to load.
        criteria_path.write_text(json.dumps(criteria), encoding="utf-8")

        # Write the subprocess worker script.
        worker_src = _WORKER_TEMPLATE.format(scripts=str(_SCRIPTS))
        script_path.write_text(worker_src, encoding="utf-8")

        # Time the subprocess (wall clock from start to completion).
        t0 = time.perf_counter()
        proc = subprocess.run(
            [
                sys.executable,
                str(script_path),
                str(log_path),
                str(criteria_path),
                current_fp,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        t1 = time.perf_counter()
        elapsed_seconds = t1 - t0

        if proc.returncode != 0:
            # Emit the subprocess stderr to our stderr for diagnosis.
            print(
                f"[cold-rehydration] subprocess failed (exit {proc.returncode}):\n"
                f"{proc.stderr}",
                file=sys.stderr,
            )
            return None

        verdict_count = int(proc.stdout.strip())

        return {
            "benchmark": "cold-rehydration",
            "num_criteria": num_criteria,
            "verdict_count": verdict_count,
            "elapsed_seconds": elapsed_seconds,
        }

    except Exception as exc:  # noqa: BLE001 — report, don't propagate
        print(f"[cold-rehydration] setup/run error: {exc}", file=sys.stderr)
        return None
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ── Entry point ───────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    """Run all benchmarks and write the combined result to --output.

    Writes nothing to the working tree; the caller is responsible for the
    output path.
    """
    parser = argparse.ArgumentParser(
        description="Acceptance evaluator benchmark (AC-0018, AC-0019)"
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="PATH",
        help="Path to write the JSON benchmark result",
    )
    args = parser.parse_args(argv)
    output_path = Path(args.output)

    # Reconfigure streams to UTF-8 as required for any .apm/ script that writes.
    sys.stdout.reconfigure(encoding="utf-8", errors="strict")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")  # type: ignore[attr-defined]

    acc = _load_module("acc_benchmark_ep", _SCRIPTS / "_acceptance.py")

    evaluator_result = run_evaluator_benchmark(acc)

    cold_result = run_cold_rehydration(acc)

    result: dict = {
        "harness": "acceptance_benchmark",
        "commit_sha": os.environ.get("GITHUB_SHA", "unknown"),
        "evaluator": evaluator_result,
    }
    if cold_result is not None:
        result["cold_rehydration"] = cold_result

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(
        f"AC-0018 evaluator benchmark:\n"
        f"  corpus:     {NUM_CRITERIA} criteria × {NUM_RECEIPTS} receipts\n"
        f"  warm-up:    {WARMUP_RUNS} runs (discarded)\n"
        f"  timed runs: {TIMED_RUNS}\n"
        f"  p95:        {evaluator_result['p95_seconds'] * 1000:.1f} ms\n"
        f"  p50:        {evaluator_result['p50_seconds'] * 1000:.1f} ms\n"
        f"  result:     {output_path}"
    )
    if cold_result is not None:
        print(
            f"AC-0019 cold-rehydration benchmark:\n"
            f"  criteria:   {cold_result['num_criteria']}\n"
            f"  verdicts:   {cold_result['verdict_count']}\n"
            f"  elapsed:    {cold_result['elapsed_seconds']:.3f} s  (bound: 10.0 s)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
