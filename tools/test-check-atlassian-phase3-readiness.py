#!/usr/bin/env python3
"""Tests for check-atlassian-phase3-readiness.py.

Acceptance Criteria (from spec.md):
  AC7  — script exists and exits non-zero (Phase 2C not implemented)
  AC8  — --json produces ready: false with checks array
  AC9  — Phase 2C check reports fail with evidence
  AC10 — All other verifiable checks report pass
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys

_TOOL = pathlib.Path(__file__).parent / "check-atlassian-phase3-readiness.py"
_PY = sys.executable

_passed = 0
_failed = 0


def _pass(label: str) -> None:
    global _passed
    _passed += 1
    print(f"  PASS  {label}")


def _fail(label: str, reason: str) -> None:
    global _failed
    _failed += 1
    print(f"  FAIL  {label}: {reason}")


def _run(extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    cmd = [_PY, str(_TOOL)] + (extra_args or [])
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


# ── AC7 — script exists and exits non-zero ────────────────────────────────────

def test_script_exists() -> None:
    if _TOOL.exists():
        _pass("test_script_exists")
    else:
        _fail("test_script_exists", f"tool not found: {_TOOL}")


def test_exits_nonzero() -> None:
    r = _run()
    if r.returncode != 0:
        _pass("test_exits_nonzero (Phase 2C not implemented)")
    else:
        _fail("test_exits_nonzero", "exited 0 — Phase 2C must block readiness")


def test_human_readable_by_default() -> None:
    r = _run()
    combined = r.stdout + r.stderr
    if "NOT READY FOR PHASE 3" in combined or "READY FOR PHASE 3" in combined:
        _pass("test_human_readable_by_default")
    else:
        _fail("test_human_readable_by_default",
              f"expected readiness verdict in output; got: {combined[:200]!r}")


# ── AC8 — --json produces ready: false with checks array ─────────────────────

def test_json_flag_produces_json() -> None:
    r = _run(["--json"])
    try:
        data = json.loads(r.stdout)
        _pass("test_json_flag_produces_json")
        return data
    except json.JSONDecodeError as exc:
        _fail("test_json_flag_produces_json",
              f"stdout is not valid JSON: {exc}; got: {r.stdout[:200]!r}")
        return None


def _load_json() -> dict | None:
    r = _run(["--json"])
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return None


def test_json_ready_is_false() -> None:
    data = _load_json()
    if data is None:
        _fail("test_json_ready_is_false", "could not parse JSON output")
        return
    if data.get("ready") is False:
        _pass("test_json_ready_is_false")
    else:
        _fail("test_json_ready_is_false", f"expected ready=false, got: {data.get('ready')!r}")


def test_json_phase_field() -> None:
    data = _load_json()
    if data is None:
        _fail("test_json_phase_field", "could not parse JSON output")
        return
    if data.get("phase") == "atlassian-phase3":
        _pass("test_json_phase_field")
    else:
        _fail("test_json_phase_field",
              f"expected phase='atlassian-phase3', got: {data.get('phase')!r}")


def test_json_head_field_present() -> None:
    data = _load_json()
    if data is None:
        _fail("test_json_head_field_present", "could not parse JSON output")
        return
    if "head" in data and isinstance(data["head"], str):
        _pass("test_json_head_field_present")
    else:
        _fail("test_json_head_field_present", f"head field absent or wrong type: {data!r}")


def test_json_checks_array_present() -> None:
    data = _load_json()
    if data is None:
        _fail("test_json_checks_array_present", "could not parse JSON output")
        return
    checks = data.get("checks", [])
    if isinstance(checks, list) and len(checks) > 0:
        _pass(f"test_json_checks_array_present ({len(checks)} checks)")
    else:
        _fail("test_json_checks_array_present", f"checks array absent or empty: {checks!r}")


def test_json_checks_have_required_fields() -> None:
    data = _load_json()
    if data is None:
        _fail("test_json_checks_have_required_fields", "could not parse JSON output")
        return
    checks = data.get("checks", [])
    bad = [c for c in checks if not (isinstance(c.get("id"), str)
                                     and isinstance(c.get("status"), str)
                                     and isinstance(c.get("evidence"), list))]
    if not bad:
        _pass("test_json_checks_have_required_fields")
    else:
        _fail("test_json_checks_have_required_fields",
              f"{len(bad)} checks missing required fields: {bad[:2]!r}")


# ── Coverage: expected check IDs are all present ──────────────────────────────

_EXPECTED_CHECK_IDS = [
    "product-documentation-canonical",
    "compatibility-pack-deprecated",
    "site-grouping-canonical",
    "guide-doctrine-metadata-based",
    "journey-pack-lint",
    "journey-contract-lint",
    "journey-generated-parity",
    "journey-subset-journeys-allowed",
    "phase2c-ui-primitives",
    "atlassian-version-metadata",
    "atlassian-first-value-team-oriented",
    "atlassian-team-status-read-only",
    "atlassian-story-triage-draft-only",
    "atlassian-team-agent-readiness-separate",
    "atlassian-activation-evals",
    "atlassian-deterministic-tests",
    "atlassian-readme-accuracy",
]


def test_all_expected_check_ids_present() -> None:
    data = _load_json()
    if data is None:
        _fail("test_all_expected_check_ids_present", "could not parse JSON output")
        return
    present = {c["id"] for c in data.get("checks", [])}
    missing = [cid for cid in _EXPECTED_CHECK_IDS if cid not in present]
    if not missing:
        _pass("test_all_expected_check_ids_present")
    else:
        _fail("test_all_expected_check_ids_present",
              f"missing check IDs: {missing}")


# ── AC9 — Phase 2C check reports fail with evidence ──────────────────────────

def test_phase2c_check_status_fail() -> None:
    data = _load_json()
    if data is None:
        _fail("test_phase2c_check_status_fail", "could not parse JSON output")
        return
    checks = {c["id"]: c for c in data.get("checks", [])}
    c2c = checks.get("phase2c-ui-primitives")
    if c2c is None:
        _fail("test_phase2c_check_status_fail", "phase2c-ui-primitives check not found")
        return
    if c2c.get("status") == "fail":
        _pass("test_phase2c_check_status_fail")
    else:
        _fail("test_phase2c_check_status_fail",
              f"expected status=fail, got: {c2c.get('status')!r}")


def test_phase2c_evidence_nonempty() -> None:
    data = _load_json()
    if data is None:
        _fail("test_phase2c_evidence_nonempty", "could not parse JSON output")
        return
    checks = {c["id"]: c for c in data.get("checks", [])}
    c2c = checks.get("phase2c-ui-primitives")
    if c2c is None:
        _fail("test_phase2c_evidence_nonempty", "phase2c-ui-primitives check not found")
        return
    evidence = c2c.get("evidence", [])
    if evidence:
        _pass(f"test_phase2c_evidence_nonempty ({len(evidence)} evidence item(s))")
    else:
        _fail("test_phase2c_evidence_nonempty", "evidence list is empty")


# ── AC10 — other verifiable checks report pass ────────────────────────────────

_MUST_PASS_CHECK_IDS = [
    "product-documentation-canonical",
    "compatibility-pack-deprecated",
    "site-grouping-canonical",
    "guide-doctrine-metadata-based",
    "journey-pack-lint",
    "journey-contract-lint",
    "journey-generated-parity",
    "journey-subset-journeys-allowed",
    "atlassian-version-metadata",
    "atlassian-first-value-team-oriented",
    "atlassian-team-status-read-only",
    "atlassian-story-triage-draft-only",
    "atlassian-team-agent-readiness-separate",
    "atlassian-activation-evals",
    "atlassian-deterministic-tests",
    "atlassian-readme-accuracy",
]


def test_verifiable_checks_pass() -> None:
    data = _load_json()
    if data is None:
        _fail("test_verifiable_checks_pass", "could not parse JSON output")
        return
    checks = {c["id"]: c for c in data.get("checks", [])}
    failing = [cid for cid in _MUST_PASS_CHECK_IDS
               if checks.get(cid, {}).get("status") not in ("pass", "skipped")]
    if not failing:
        _pass("test_verifiable_checks_pass")
    else:
        details = [
            (cid, checks.get(cid, {}).get("status"), checks.get(cid, {}).get("evidence", []))
            for cid in failing
        ]
        _fail("test_verifiable_checks_pass",
              f"{len(failing)} check(s) not passing: {details[:3]!r}")


# ── human-readable output shape ───────────────────────────────────────────────

def test_human_output_contains_check_ids() -> None:
    r = _run()
    combined = r.stdout + r.stderr
    # At least one of the expected check IDs should appear in human output
    found = [cid for cid in _EXPECTED_CHECK_IDS[:4] if cid in combined]
    if found:
        _pass("test_human_output_contains_check_ids")
    else:
        _fail("test_human_output_contains_check_ids",
              f"none of {_EXPECTED_CHECK_IDS[:4]} found in output: {combined[:300]!r}")


def test_human_output_not_json() -> None:
    r = _run()
    combined = (r.stdout + r.stderr).strip()
    # Human output should NOT be a bare JSON object
    if combined.startswith("{"):
        _fail("test_human_output_not_json", "default output looks like raw JSON")
    else:
        _pass("test_human_output_not_json")


# ── runner ─────────────────────────────────────────────────────────────────────

def main() -> int:
    tests = [
        test_script_exists,
        test_exits_nonzero,
        test_human_readable_by_default,
        test_json_flag_produces_json,
        test_json_ready_is_false,
        test_json_phase_field,
        test_json_head_field_present,
        test_json_checks_array_present,
        test_json_checks_have_required_fields,
        test_all_expected_check_ids_present,
        test_phase2c_check_status_fail,
        test_phase2c_evidence_nonempty,
        test_verifiable_checks_pass,
        test_human_output_contains_check_ids,
        test_human_output_not_json,
    ]

    print(f"\ncheck-atlassian-phase3-readiness tests ({len(tests)} tests)\n")
    for t in tests:
        t()

    print(f"\n{_passed + _failed} tests, {_failed} failed\n")
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
