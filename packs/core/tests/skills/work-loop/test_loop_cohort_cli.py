#!/usr/bin/env python3
"""Cross-platform CLI self-test for the Phase-1 loop-cohort contract.

The native cases from the former ``test-loop-cohort.sh`` suite each
construct the state they need, so failures do not cascade through a shared
counter or a mutable fixture. The suites that the shell wrapper invoked
recursively remain independent CI/test-all gates. This module uses only the
Python standard library.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
_SKILL_DIR = PACK_ROOT / ".apm" / "skills" / "work-loop"
if not _SKILL_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {_SKILL_DIR} — check the parents[] depth")
COHORT = _SKILL_DIR / "scripts" / "loop-cohort.py"
# The pack-owned asset, not its `.claude/` projection: this suite may not reach
# above packs/core, and projection parity is gated by the self-host drift check.
STATE_TEMPLATE = _SKILL_DIR / "assets" / "state.json"
EXPECTED_STATE_KEYS = {
    "schema_version",
    "run_id",
    "feature",
    "plan_review_status",
    "approved_spec_hash",
    "approved_plan_hash",
    "plan_hash",
    "schedule_waves",
    "current_wave_index",
    "implementation_retry_count",
    "max_implementation_retries",
    "last_record_attempt_cycle_id",
    "review_round_count",
    "review_retry_count",
    "max_review_retries",
    "finding_fingerprints",
    "previous_finding_fingerprints",
    # Clean-round provenance: which recording form closed the round, and the
    # digest of the artifact it rested on. Resumption reads these instead of
    # inferring the form from an artifact whose absence is ambiguous.
    "last_review_clean_source",
    "last_review_clean_digest",
    # Review-record idempotency: which round the counters belong to, and the
    # digest of the payload it was recorded with. Stored rather than derived,
    # because the next round overwrites whatever a derivation would read.
    "last_review_record_operation_id",
    "last_review_record_payload_digest",
    "auto_parallel",
    "last_commit_sha",
    "worktrees",
    # Controlled full-mode contract amendment: completed-task pins, their
    # bounded evidence, the append-only snapshot log, and the replay marker.
    "completed_task_ids",
    "completed_task_section_hashes",
    "completed_task_evidence",
    "amendment_history",
    "amendment_pending",
}
PHASE_TWO_KEYS = {
    "token_budget_used_pct",
    "token_budget_cap_pct",
    "consecutive_same_error_count",
    "consecutive_same_error_threshold",
    "iteration_count",
    "max_iterations",
}
SPEC_BODY = """# Spec

- **Status:** Approved

## Acceptance criteria

- [ ] AC1
"""
PLAN_BODY = """# Plan

- **Status:** Approved

### T1

**Depends on:** none

### T2

**Depends on:** T1
"""
PLAN_BODY_WITHOUT_STATUS = """# Plan

### T1

**Depends on:** none

### T2

**Depends on:** T1
"""
FINDINGS_REPORT = """## Blockers

**1. Missing null check.** `src/foo.py:42`. Value not validated. Fix: add guard.

**2. Typo.** `src/bar.py:10`. Spelling error. Fix: fix it.
"""
CLEAN_REPORT = "Review complete.\n\nClean — ready to commit.\n"
CLEAN_ADJUDICATION = """## Main-loop result
Clean — ready to commit.

## Refuted audit
None.

## Indeterminate audit
None.
"""
# A well-formed adjudication envelope that sustains findings. Distinct from
# FINDINGS_REPORT, which is a heading-free legacy body: this one satisfies the
# envelope check, so it reaches the classification guard rather than being
# turned away as `legacy-report` before classification runs.
FINDINGS_ADJUDICATION = """## Main-loop result

**1. [Blocker] Missing null check.** `src/foo.py:42`. Sustained: the value is not validated on the untrusted path. Proposed mechanism: adequate. Fix: add a guard.

## Refuted audit
None.

## Indeterminate audit
None.
"""
# The exact sentinel and nothing else. Written as bytes so the fixture cannot
# acquire a trailing newline from an editor or a text-mode write.
DIRECT_CLEAN_BYTES = "Clean — ready to commit.".encode()


class LoopCohortCliTest(unittest.TestCase):
    """Exercise projected CLI behavior with an isolated fixture per case."""

    maxDiff = None

    def _temp_root(self) -> Path:
        temporary = tempfile.TemporaryDirectory(
            prefix="loop-cohort-cli-", ignore_cleanup_errors=True
        )
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        self._cwd = root
        return root

    def _spec_dir(self) -> Path:
        spec_dir = self._temp_root() / "spec1"
        spec_dir.mkdir()
        return spec_dir

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(COHORT), *map(str, args)],
            cwd=getattr(self, "_cwd", PACK_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def _assert_cli(
        self,
        expected_exit: int,
        *args: str,
        stderr_contains: str = "",
    ) -> subprocess.CompletedProcess[str]:
        result = self._run(*args)
        self.assertEqual(
            result.returncode,
            expected_exit,
            f"args={args!r}\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        if stderr_contains:
            self.assertIn(stderr_contains, result.stderr)
        return result

    def _initialized(self) -> tuple[Path, str]:
        spec_dir = self._spec_dir()
        run_id = str(uuid.uuid4())
        self._assert_cli(0, "init", str(spec_dir), "--run-id", run_id)
        return spec_dir, run_id

    def _write_contract(self, spec_dir: Path, *, plan_status: bool = True) -> None:
        (spec_dir / "spec.md").write_text(SPEC_BODY, encoding="utf-8")
        plan = PLAN_BODY if plan_status else PLAN_BODY_WITHOUT_STATUS
        (spec_dir / "plan.md").write_text(plan, encoding="utf-8")

    def _approved(self) -> tuple[Path, str]:
        spec_dir, run_id = self._initialized()
        self._write_contract(spec_dir)
        self._assert_cli(
            0,
            "approve-plan",
            str(spec_dir),
            "--expect-run-id",
            run_id,
        )
        return spec_dir, run_id

    def _scheduled(self) -> tuple[Path, str]:
        spec_dir, run_id = self._approved()
        self._assert_cli(0, "schedule", str(spec_dir), "--expect-run-id", run_id)
        return spec_dir, run_id

    def _reports(self, spec_dir: Path) -> tuple[Path, Path]:
        findings = spec_dir.parent / "findings.md"
        clean = spec_dir.parent / "clean.md"
        findings.write_text(FINDINGS_REPORT, encoding="utf-8")
        clean.write_text(CLEAN_REPORT, encoding="utf-8")
        return findings, clean

    def _clean_adjudication(self, spec_dir: Path) -> Path:
        report = spec_dir.parent / "clean-adjudication.md"
        report.write_text(CLEAN_ADJUDICATION, encoding="utf-8")
        return report

    def _findings_adjudication(self, spec_dir: Path) -> Path:
        report = spec_dir.parent / "findings-adjudication.md"
        report.write_text(FINDINGS_ADJUDICATION, encoding="utf-8")
        return report

    def _direct_clean_file(self, spec_dir: Path, body: bytes = DIRECT_CLEAN_BYTES) -> Path:
        artifact = spec_dir.parent / "raw-clean.md"
        artifact.write_bytes(body)
        return artifact

    def _raw_classification(self, report: Path) -> dict[str, object]:
        result = self._assert_cli(0, "review", "raw-classify", "--report", str(report), "--json")
        return json.loads(result.stdout)

    @staticmethod
    def _state(spec_dir: Path) -> dict[str, object]:
        return json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))

    def _write_state(self, spec_dir: Path, **changes: object) -> None:
        state = self._state(spec_dir)
        state.update(changes)
        (spec_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

    def test_01_schema_phase_one_keys_match(self) -> None:
        template = json.loads(STATE_TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(set(template), EXPECTED_STATE_KEYS)
        self.assertFalse(PHASE_TWO_KEYS & set(template))

    def test_02_template_init_defaults(self) -> None:
        template = json.loads(STATE_TEMPLATE.read_text(encoding="utf-8"))
        self.assertEqual(template["schema_version"], 1)
        self.assertIsNone(template["run_id"])
        self.assertEqual(template["plan_review_status"], "pending")

    def test_03_init_without_run_id_fails(self) -> None:
        self._assert_cli(2, "init", str(self._spec_dir()))

    def test_04_init_with_run_id_succeeds(self) -> None:
        spec_dir = self._spec_dir()
        self._assert_cli(0, "init", str(spec_dir), "--run-id", str(uuid.uuid4()))

    def test_05_init_state_has_run_id_and_schema(self) -> None:
        spec_dir, run_id = self._initialized()
        state = self._state(spec_dir)
        self.assertEqual(state["run_id"], run_id)
        self.assertEqual(state["schema_version"], 1)
        self.assertEqual(state["plan_review_status"], "pending")

    def test_06_init_refuses_existing_state(self) -> None:
        spec_dir, run_id = self._initialized()
        self._assert_cli(1, "init", str(spec_dir), "--run-id", run_id)

    def test_07_identity_succeeds(self) -> None:
        spec_dir, run_id = self._initialized()
        self._assert_cli(0, "identity", str(spec_dir), "--expect-run-id", run_id)

    def test_08_identity_mismatch_fails(self) -> None:
        spec_dir, _ = self._initialized()
        self._assert_cli(1, "identity", str(spec_dir), "--expect-run-id", "wrong-id")

    def test_09_identity_absent_state_fails(self) -> None:
        self._assert_cli(1, "identity", str(self._spec_dir()))

    def test_10_plan_check_current_is_pending_before_approval(self) -> None:
        spec_dir, _ = self._initialized()
        self._write_contract(spec_dir, plan_status=False)
        self._assert_cli(1, "plan", "check-current", str(spec_dir))

    def test_11_approve_plan_without_expected_run_id_fails(self) -> None:
        spec_dir, _ = self._initialized()
        self._write_contract(spec_dir)
        self._assert_cli(2, "approve-plan", str(spec_dir))

    def test_12_approve_plan_with_expected_run_id_succeeds(self) -> None:
        self._approved()

    def test_13_approve_plan_writes_hashes(self) -> None:
        spec_dir, _ = self._approved()
        state = self._state(spec_dir)
        self.assertEqual(state["plan_review_status"], "approved")
        self.assertEqual(len(str(state["approved_spec_hash"])), 64)
        self.assertEqual(len(str(state["approved_plan_hash"])), 64)

    def test_14_plan_check_current_passes_after_approval(self) -> None:
        spec_dir, _ = self._approved()
        self._assert_cli(0, "plan", "check-current", str(spec_dir))

    def test_15_check_implement_stub_passes(self) -> None:
        spec_dir, _ = self._approved()
        self._assert_cli(0, "check", str(spec_dir), "--phase", "implement")

    def test_16_check_gates_failed_detects_cap(self) -> None:
        spec_dir, _ = self._approved()
        self._write_state(
            spec_dir, implementation_retry_count=5, max_implementation_retries=5
        )
        self._assert_cli(
            1, "check", str(spec_dir), "--phase", "gates-failed", stderr_contains="cap"
        )

    def test_17_check_gates_failed_passes_below_cap(self) -> None:
        spec_dir, _ = self._approved()
        self._write_state(
            spec_dir, implementation_retry_count=0, max_implementation_retries=5
        )
        self._assert_cli(0, "check", str(spec_dir), "--phase", "gates-failed")

    def test_18_check_review_detects_cap(self) -> None:
        spec_dir, _ = self._approved()
        self._write_state(spec_dir, review_retry_count=5, max_review_retries=5)
        self._assert_cli(1, "check", str(spec_dir), "--phase", "review")

    def test_19_schedule_without_expected_run_id_fails(self) -> None:
        spec_dir, _ = self._approved()
        self._assert_cli(1, "schedule", str(spec_dir))

    def test_20_schedule_with_expected_run_id_succeeds(self) -> None:
        self._scheduled()

    def test_21_schedule_persists_waves_and_hash(self) -> None:
        spec_dir, _ = self._scheduled()
        state = self._state(spec_dir)
        self.assertIsInstance(state["schedule_waves"], list)
        self.assertTrue(state["schedule_waves"])
        self.assertIsNotNone(state["plan_hash"])
        self.assertEqual(state["current_wave_index"], 0)

    def test_22_schedule_check_current_passes(self) -> None:
        spec_dir, _ = self._scheduled()
        self._assert_cli(0, "schedule", "check-current", str(spec_dir))

    def test_23_schedule_check_current_detects_plan_change(self) -> None:
        spec_dir, _ = self._scheduled()
        (spec_dir / "plan.md").write_text("# Plan (modified)\n", encoding="utf-8")
        self._assert_cli(1, "schedule", "check-current", str(spec_dir))

    def test_24_dispatch_decision_is_disabled(self) -> None:
        self._assert_cli(1, "dispatch-decision", "--branch", "main", stderr_contains="disabled")

    def test_25_auto_parallel_is_disabled(self) -> None:
        spec_dir, _ = self._scheduled()
        self._assert_cli(1, "auto-parallel", str(spec_dir), stderr_contains="disabled")

    def test_26_worktree_add_is_disabled(self) -> None:
        spec_dir, _ = self._scheduled()
        self._assert_cli(1, "worktree", "add", str(spec_dir), "T1", stderr_contains="disabled")

    def test_27_wave_check_reports_more_at_index_zero(self) -> None:
        spec_dir, _ = self._scheduled()
        self._assert_cli(0, "wave", "check", str(spec_dir), "--expect", "more")

    def test_28_wave_advance_from_zero_succeeds(self) -> None:
        spec_dir, run_id = self._scheduled()
        self._assert_cli(
            0, "wave", "advance", str(spec_dir), "--from-index", "0", "--expect-run-id", run_id
        )

    def test_29_wave_advance_updates_current_index(self) -> None:
        spec_dir, run_id = self._scheduled()
        self._assert_cli(
            0, "wave", "advance", str(spec_dir), "--from-index", "0", "--expect-run-id", run_id
        )
        self.assertEqual(self._state(spec_dir)["current_wave_index"], 1)

    def test_30_wave_check_reports_last_at_index_one(self) -> None:
        spec_dir, run_id = self._scheduled()
        self._assert_cli(
            0, "wave", "advance", str(spec_dir), "--from-index", "0", "--expect-run-id", run_id
        )
        self._assert_cli(0, "wave", "check", str(spec_dir), "--expect", "last")

    def test_31_wave_advance_refuses_final_wave(self) -> None:
        spec_dir, run_id = self._scheduled()
        self._assert_cli(
            0, "wave", "advance", str(spec_dir), "--from-index", "0", "--expect-run-id", run_id
        )
        self._assert_cli(
            1, "wave", "advance", str(spec_dir), "--from-index", "1", "--expect-run-id", run_id
        )

    def test_32_record_attempt_increment_succeeds(self) -> None:
        spec_dir, run_id = self._scheduled()
        self._assert_cli(
            0,
            "record-attempt",
            str(spec_dir),
            "--phase",
            "implement",
            "--cycle-id",
            f"{run_id}:1",
            "--expect-run-id",
            run_id,
        )

    def test_33_record_attempt_increments_counter(self) -> None:
        spec_dir, run_id = self._scheduled()
        self._assert_cli(
            0,
            "record-attempt",
            str(spec_dir),
            "--phase",
            "implement",
            "--cycle-id",
            f"{run_id}:1",
            "--expect-run-id",
            run_id,
        )
        self.assertEqual(self._state(spec_dir)["implementation_retry_count"], 1)

    def test_34_record_attempt_idempotent_replay_succeeds(self) -> None:
        spec_dir, run_id = self._scheduled()
        args = (
            "record-attempt",
            str(spec_dir),
            "--phase",
            "implement",
            "--cycle-id",
            f"{run_id}:1",
            "--expect-run-id",
            run_id,
        )
        self._assert_cli(0, *args)
        self._assert_cli(0, *args)

    def test_35_record_attempt_idempotent_replay_keeps_counter(self) -> None:
        spec_dir, run_id = self._scheduled()
        args = (
            "record-attempt",
            str(spec_dir),
            "--phase",
            "implement",
            "--cycle-id",
            f"{run_id}:1",
            "--expect-run-id",
            run_id,
        )
        self._assert_cli(0, *args)
        self._assert_cli(0, *args)
        self.assertEqual(self._state(spec_dir)["implementation_retry_count"], 1)

    def test_36_review_inspect_classifies_findings(self) -> None:
        spec_dir, _ = self._scheduled()
        findings, _ = self._reports(spec_dir)
        result = self._assert_cli(
            0, "review", "inspect", str(spec_dir), "--report", str(findings), "--json"
        )
        self.assertEqual(json.loads(result.stdout)["classification"], "findings")

    def test_37_review_inspect_classifies_clean(self) -> None:
        spec_dir, _ = self._scheduled()
        _, clean = self._reports(spec_dir)
        result = self._assert_cli(
            0, "review", "inspect", str(spec_dir), "--report", str(clean), "--json"
        )
        self.assertEqual(json.loads(result.stdout)["classification"], "clean")

    def test_37a_raw_classify_uses_closed_footer_grammar(self) -> None:
        """Only the sentinel and an inert Not checked footer are raw-clean."""
        root = self._temp_root()
        cases = (
            ("bare", "Clean — ready to commit.", "clean", 0, False),
            (
                "footer",
                "Clean — ready to commit.\n## Not checked\n- Did not fuzz the parser.\n",
                "clean",
                0,
                True,
            ),
            (
                "crlf-footer",
                "Clean — ready to commit.\r\n## Not checked\r\n- Did not fuzz the parser.\r\n",
                "clean",
                0,
                True,
            ),
            (
                "second-section",
                "Clean — ready to commit.\n## Not checked\n- Not tested.\n## Other\n- Prose.\n",
                "invalid",
                0,
                True,
            ),
            ("free-prose", "Clean — ready to commit.\nLooks good.\n", "invalid", 0, False),
            (
                "finding-and-footer",
                "Clean — ready to commit.\n**1. Missing guard.** `src/a.py:2`. Bad. Fix: add it.\n## Not checked\n- None.\n",
                "findings",
                1,
                True,
            ),
            (
                "three-findings",
                "**1. One.** `src/a.py:1`. Bad. Fix: fix.\n**2. Two.** `src/b.py:2`. Bad. Fix: fix.\n**3. Three.** `src/c.py:3`. Bad. Fix: fix.\n",
                "findings",
                3,
                False,
            ),
            ("no-sentinel", "## Not checked\n- Did not fuzz.\n", "invalid", 0, True),
            (
                "anchor-in-footer",
                "Clean — ready to commit.\n## Not checked\n- `src/a.py:2` was not inspected.\n",
                "clean",
                0,
                True,
            ),
            ("sentinel-code-fence", "```\nClean — ready to commit.\n```\n", "invalid", 0, False),
            ("sentinel-whitespace", "Clean — ready to commit. \n", "invalid", 0, False),
            ("sentinel-bom", "\ufeffClean — ready to commit.\n", "invalid", 0, False),
            ("sentinel-lookalike", "Clean – ready to commit.\n", "invalid", 0, False),
            # A real finding written as free prose in the footer carries no
            # numbered marker, backticked anchor, or `Fix:` token. Only the
            # closed opener form keeps it out of the clean fast path.
            # Footer content is never trusted for the fast path, so these
            # classify `clean` and are disqualified by `not_checked_present`.
            # `test_37b_footer_reports_never_take_the_clean_fast_path` owns that.
            (
                "prose-finding-in-footer",
                "Clean — ready to commit.\n## Not checked\n"
                "- Did not complete authorization review: unauthenticated requests "
                "can set is_admin=true on the invite endpoint.\n",
                "clean",
                0,
                True,
            ),
            (
                "footer-heading-repeated",
                "Clean — ready to commit.\n## Not checked\n- Did not fuzz.\n"
                "## Not checked\n- Did not scan.\n",
                "invalid",
                0,
                True,
            ),
            # str.splitlines() also breaks on these, which would let one visual
            # line split into a grammar that reads clean.
            (
                "vertical-tab-terminator",
                "Clean — ready to commit.\v## Not checked\v- Did not fuzz.\n",
                "invalid",
                0,
                False,
            ),
            (
                "line-separator-terminator",
                "Clean — ready to commit.\u2028## Not checked\u2028- Did not fuzz.\n",
                "invalid",
                0,
                False,
            ),
            (
                "lone-cr-terminator",
                "Clean — ready to commit.\r## Not checked\r- Did not fuzz.\n",
                "invalid",
                0,
                False,
            ),
        )
        for name, body, classification, finding_count, footer_present in cases:
            with self.subTest(name=name):
                report = root / f"{name}.md"
                report.write_text(body, encoding="utf-8", newline="")
                self.assertEqual(
                    self._raw_classification(report),
                    {
                        "classification": classification,
                        "finding_count": finding_count,
                        "not_checked_present": footer_present,
                    },
                )

    def test_37b_raw_classify_refuses_unreadable_nonutf_oversized_and_fifo(self) -> None:
        root = self._temp_root()
        unreadable = root / "missing.md"
        non_utf = root / "non-utf.md"
        non_utf.write_bytes(b"\xff")
        oversized = root / "oversized.md"
        oversized.write_bytes(b"x" * (8 * 1024 * 1024 + 1))
        paths = [unreadable, non_utf, oversized]
        fifo = root / "report.fifo"
        if hasattr(os, "mkfifo"):
            os.mkfifo(fifo)
            paths.append(fifo)
        for path in paths:
            with self.subTest(path=path.name):
                self.assertEqual(
                    self._raw_classification(path),
                    {"classification": "invalid", "finding_count": 0, "not_checked_present": False},
                )

    def test_37c_raw_classify_keeps_disclosure_metadata_out_of_routing(self) -> None:
        root = self._temp_root()
        report = root / "footer-without-sentinel.md"
        report.write_text("## Not checked\n- Did not fuzz the parser.\n", encoding="utf-8")
        self.assertEqual(
            self._raw_classification(report),
            {"classification": "invalid", "finding_count": 0, "not_checked_present": True},
        )

    def test_38_review_record_fingerprint_succeeds(self) -> None:
        spec_dir, run_id = self._scheduled()
        self._assert_cli(
            0,
            "review",
            "record",
            str(spec_dir),
            "--fingerprint",
            "aabbccdd112233445566778899001122334455aa",
            "--expect-run-id",
            run_id,
        )

    def test_39_review_record_fingerprint_increments_both_counters(self) -> None:
        spec_dir, run_id = self._scheduled()
        self._assert_cli(
            0,
            "review",
            "record",
            str(spec_dir),
            "--fingerprint",
            "aabbccdd112233445566778899001122334455aa",
            "--expect-run-id",
            run_id,
        )
        state = self._state(spec_dir)
        self.assertEqual((state["review_round_count"], state["review_retry_count"]), (1, 1))

    def test_40_review_record_clean_report_succeeds(self) -> None:
        spec_dir, run_id = self._scheduled()
        clean = self._clean_adjudication(spec_dir)
        result = self._assert_cli(
            0,
            "review",
            "record",
            str(spec_dir),
            "--report",
            str(clean),
            "--adjudication",
            "--expect-run-id",
            run_id,
        )
        self.assertIn("review record (clean:report)", result.stdout)
        state = self._state(spec_dir)
        self.assertEqual(state["last_review_clean_source"], "report")
        self.assertEqual(
            state["last_review_clean_digest"],
            hashlib.sha256(clean.read_bytes()).hexdigest(),
        )

    def test_41_review_record_clean_report_only_increments_round(self) -> None:
        spec_dir, run_id = self._scheduled()
        clean = self._clean_adjudication(spec_dir)
        self._assert_cli(
            0,
            "review",
            "record",
            str(spec_dir),
            "--fingerprint",
            "aabbccdd112233445566778899001122334455aa",
            "--expect-run-id",
            run_id,
        )
        self._assert_cli(
            0,
            "review",
            "record",
            str(spec_dir),
            "--report",
            str(clean),
            "--adjudication",
            "--expect-run-id",
            run_id,
        )
        state = self._state(spec_dir)
        self.assertEqual((state["review_round_count"], state["review_retry_count"]), (2, 1))

    def test_42_review_record_rejects_nonclean_report(self) -> None:
        spec_dir, run_id = self._scheduled()
        findings, _ = self._reports(spec_dir)
        # `--adjudication` is required for the call to reach classification at
        # all; without it the precondition turns it away first and this case
        # would silently guard a different branch.
        self._assert_cli(
            1,
            "review",
            "record",
            str(spec_dir),
            "--report",
            str(findings),
            "--adjudication",
            "--expect-run-id",
            run_id,
            stderr_contains="classified as",
        )

    def test_42d_review_record_rejects_findings_bearing_adjudication(self) -> None:
        """A well-formed envelope carrying findings must not close the round.

        This is the case the classification guard exists for. `test_42` reaches
        the same guard through `legacy-report`/`invalid`; only a valid envelope
        whose findings parse reaches it through the `findings` classification.
        """
        spec_dir, run_id = self._scheduled()
        findings = self._findings_adjudication(spec_dir)
        state_path = spec_dir / "state.json"
        before = state_path.read_bytes()
        self._assert_cli(
            1,
            "review",
            "record",
            str(spec_dir),
            "--report",
            str(findings),
            "--adjudication",
            "--expect-run-id",
            run_id,
            stderr_contains="classified as 'findings'",
        )
        self.assertEqual(state_path.read_bytes(), before)

    def test_42a_review_record_accepts_exact_direct_clean_file(self) -> None:
        spec_dir, run_id = self._scheduled()
        artifact = self._direct_clean_file(spec_dir)
        result = self._assert_cli(
            0,
            "review",
            "record",
            str(spec_dir),
            "--direct-clean-file",
            str(artifact),
            "--expect-run-id",
            run_id,
        )
        self.assertIn("review record (clean:direct-clean)", result.stdout)
        state = self._state(spec_dir)
        self.assertEqual((state["review_round_count"], state["review_retry_count"]), (1, 0))
        self.assertEqual(state["last_review_clean_source"], "direct-clean")
        self.assertEqual(
            state["last_review_clean_digest"],
            hashlib.sha256(DIRECT_CLEAN_BYTES).hexdigest(),
        )

    def test_42aa_review_record_reclassifies_structural_clean_file(self) -> None:
        spec_dir, run_id = self._scheduled()
        # Footer-free: a trailing newline is what byte equality rejects and this
        # form exists to admit. A footer-bearing report is refused — see
        # test_42ac.
        artifact = self._direct_clean_file(
            spec_dir, b"Clean \xe2\x80\x94 ready to commit.\n"
        )
        result = self._assert_cli(
            0,
            "review",
            "record",
            str(spec_dir),
            "--structural-clean-file",
            str(artifact),
            "--expect-run-id",
            run_id,
        )
        self.assertIn("review record (clean:structural-clean)", result.stdout)
        state = self._state(spec_dir)
        self.assertEqual(state["last_review_clean_source"], "structural-clean")
        self.assertEqual(state["last_review_clean_digest"], hashlib.sha256(artifact.read_bytes()).hexdigest())

    def test_42ac_review_record_refuses_a_footer_bearing_report(self) -> None:
        """A `## Not checked` footer always takes the adjudicator path.

        The footer is prose and prose is what the adjudicator reads. Two attempts
        to make footer content safe to fast-path were defeated, so its content is
        no longer inspected — its presence alone disqualifies the fast path.
        """
        spec_dir, run_id = self._scheduled()
        artifact = self._direct_clean_file(
            spec_dir,
            b"Clean \xe2\x80\x94 ready to commit.\n## Not checked\n"
            b"- Did not complete authorization review: unauthenticated requests "
            b"can set is_admin=true on the invite endpoint.\n",
        )
        result = self._assert_cli(
            1,
            "review",
            "record",
            str(spec_dir),
            "--structural-clean-file",
            str(artifact),
            "--expect-run-id",
            run_id,
        )
        self.assertIn("not eligible for the clean fast path", result.stdout + result.stderr)
        self.assertIsNone(self._state(spec_dir)["last_review_clean_source"])

    def test_42ab_review_record_rejects_invalid_structural_clean_file(self) -> None:
        spec_dir, run_id = self._scheduled()
        artifact = self._direct_clean_file(
            spec_dir,
            # Genuinely malformed, not merely footer-bearing: the footer path is
            # a separate refusal with its own message (test_42ac).
            b"Clean \xe2\x80\x94 ready to commit.\nLooks good.\n",
        )
        state_path = spec_dir / "state.json"
        before = state_path.read_bytes()
        self._assert_cli(
            1,
            "review",
            "record",
            str(spec_dir),
            "--structural-clean-file",
            str(artifact),
            "--expect-run-id",
            run_id,
            stderr_contains="requires a clean raw-report classification",
        )
        self.assertEqual(state_path.read_bytes(), before)

    def test_42b_review_record_rejects_near_miss_without_state_change(self) -> None:
        spec_dir, run_id = self._scheduled()
        artifact = self._direct_clean_file(spec_dir, DIRECT_CLEAN_BYTES + b"\n")
        state_path = spec_dir / "state.json"
        before = state_path.read_bytes()
        result = self._assert_cli(
            1,
            "review",
            "record",
            str(spec_dir),
            "--direct-clean-file",
            str(artifact),
            "--expect-run-id",
            run_id,
            stderr_contains="--direct-clean-file requires the exact clean sentinel",
        )
        self.assertEqual(state_path.read_bytes(), before)
        # Kept alongside the positive assertion: the refusal must name the rule
        # without echoing the caller's near-miss value back into the log.
        self.assertNotIn("Clean — ready to commit.", result.stderr)

    def test_42c_review_record_rejects_raw_wrapped_clean_without_state_change(self) -> None:
        spec_dir, run_id = self._scheduled()
        _, clean = self._reports(spec_dir)
        state_path = spec_dir / "state.json"
        before = state_path.read_bytes()
        self._assert_cli(
            1,
            "review",
            "record",
            str(spec_dir),
            "--report",
            str(clean),
            "--expect-run-id",
            run_id,
            stderr_contains="--report requires --adjudication",
        )
        self.assertEqual(state_path.read_bytes(), before)

    def test_42e_review_record_rejects_direct_clean_file_with_adjudication(self) -> None:
        spec_dir, run_id = self._scheduled()
        artifact = self._direct_clean_file(spec_dir)
        state_path = spec_dir / "state.json"
        before = state_path.read_bytes()
        self._assert_cli(
            1,
            "review",
            "record",
            str(spec_dir),
            "--direct-clean-file",
            str(artifact),
            "--adjudication",
            "--expect-run-id",
            run_id,
            stderr_contains="two different recording forms",
        )
        self.assertEqual(state_path.read_bytes(), before)

    def test_42f_review_record_rejects_unreadable_direct_clean_file(self) -> None:
        spec_dir, run_id = self._scheduled()
        state_path = spec_dir / "state.json"
        before = state_path.read_bytes()
        self._assert_cli(
            1,
            "review",
            "record",
            str(spec_dir),
            "--direct-clean-file",
            str(spec_dir.parent / "never-written.md"),
            "--expect-run-id",
            run_id,
            stderr_contains="--direct-clean-file is unreadable",
        )
        self.assertEqual(state_path.read_bytes(), before)

    def test_43_status_is_read_only(self) -> None:
        spec_dir, _ = self._scheduled()
        state_path = spec_dir / "state.json"
        before = hashlib.sha256(state_path.read_bytes()).hexdigest()
        self._assert_cli(0, "status", str(spec_dir), "--json")
        after = hashlib.sha256(state_path.read_bytes()).hexdigest()
        self.assertEqual(after, before)

    def test_44_reset_succeeds(self) -> None:
        spec_dir, _ = self._initialized()
        self._assert_cli(0, "reset", str(spec_dir))

    def test_45_reset_deletes_state(self) -> None:
        spec_dir, _ = self._initialized()
        self._assert_cli(0, "reset", str(spec_dir))
        self.assertFalse((spec_dir / "state.json").exists())

    def test_46_reset_is_idempotent(self) -> None:
        spec_dir, _ = self._initialized()
        self._assert_cli(0, "reset", str(spec_dir))
        self._assert_cli(0, "reset", str(spec_dir))
