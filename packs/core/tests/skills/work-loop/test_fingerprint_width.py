#!/usr/bin/env python3
"""Pytest fingerprint algorithm + width contract for loop-cohort.py (core 2.3.0).

Review-finding fingerprints moved from SHA-1 to SHA-256. They are opaque
tokens compared set-wise for stasis detection, never displayed and never a key
into anything external, so the switch is behaviour-preserving — with one edge:
a cohort that was mid-review when core upgraded holds 40-hex values in its
state.json, and `review record --fingerprint` would hard-reject them if the
validator only accepted the new width.

These cases live here rather than in test-loop-cohort.sh because that fixture
is sequential and its counter assertions accumulate — inserting a successful
`review record` there shifts every downstream expected count.

Run with pytest.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
COHORT = _SKILL_DIR / "scripts" / "loop-cohort.py"
if not COHORT.is_file():
    raise SystemExit(f"subject not found at {COHORT} — check the parents[] depth")

_spec = importlib.util.spec_from_file_location("loop_cohort_under_test", COHORT)
lc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lc)


def ok(name: str) -> None:
    """Pytest reports the independently collected case."""


def fail(name: str, reason: str) -> None:
    pytest.fail(f"{name}: {reason}")


def test_parse_findings_emits_sha256() -> None:
    """A parsed finding yields a 64-hex digest, not 40-hex."""
    name = "parse_findings emits 64-hex (SHA-256)"
    fps = lc.parse_findings("**1. Broken thing** `foo/bar.py:42`\n")
    if len(fps) != 1:
        fail(name, f"expected 1 fingerprint, got {len(fps)}: {fps}")
    elif len(fps[0]) != 64:
        fail(name, f"expected width 64, got {len(fps[0])}: {fps[0]}")
    elif not re.fullmatch(r"[0-9a-f]{64}", fps[0]):
        fail(name, f"not lowercase hex: {fps[0]}")
    else:
        ok(name)


def test_fingerprint_is_stable() -> None:
    """The same finding hashes identically across calls — stasis detection
    compares sets between rounds, so an unstable digest would break it."""
    name = "fingerprint is deterministic across calls"
    report = "**1. Broken thing** `foo/bar.py:42`\n"
    if lc.parse_findings(report) != lc.parse_findings(report):
        fail(name, "same report produced different fingerprints")
    else:
        ok(name)


def test_distinct_findings_differ() -> None:
    """Different findings must not collide, or stasis fires spuriously."""
    name = "distinct findings produce distinct fingerprints"
    a = lc.parse_findings("**1. Thing A** `foo/bar.py:42`\n")
    b = lc.parse_findings("**1. Thing B** `foo/bar.py:42`\n")
    if a == b:
        fail(name, f"collision: {a} == {b}")
    else:
        ok(name)


def test_validator_accepts_both_widths() -> None:
    """64-hex is current; 40-hex stays valid for cohorts straddling the upgrade."""
    for width, label in ((64, "sha256 (current)"), (40, "sha1 (legacy, in-flight)")):
        name = f"validator accepts {width}-hex — {label}"
        if lc._RE_FINGERPRINT.match("a" * width):
            ok(name)
        else:
            fail(name, f"{width}-hex rejected; an in-flight cohort would hard-fail")


def test_validator_rejects_other_widths() -> None:
    """The widened validator must not have degraded to 'any hex string'."""
    for bad in ("a" * 8, "a" * 39, "a" * 41, "a" * 63, "a" * 65, "", "z" * 64):
        name = f"validator rejects {bad[:6]!r}(len={len(bad)})"
        if lc._RE_FINGERPRINT.match(bad):
            fail(name, "accepted a value that is neither sha1 nor sha256 hex")
        else:
            ok(name)
