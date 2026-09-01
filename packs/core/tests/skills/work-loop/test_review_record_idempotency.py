#!/usr/bin/env python3
"""`review record --operation-id`: one case per row of the writer case table.

The table lives in `docs/specs/review-record-idempotency/plan.md`; the six rows
are a total, non-overlapping partition over (recorded id, supplied id, payload
digest). Each test names its row so a failure points at the case rather than at
a symptom.

Each form's pre-existing payload validation runs before any row applies, so a
malformed fingerprint or a non-sentinel clean artifact still refuses exactly as
it does today — those refusals are the sibling suite's, not this one's.

Standard library only, and this suite never reads above `packs/core`.
"""

from __future__ import annotations

import hashlib
import json
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

CLEAN_SENTINEL = "Clean — ready to commit."
FP_A = "a" * 64
FP_B = "b" * 64
FP_C = "c" * 64

ADJUDICATION = f"""## Main-loop result

{CLEAN_SENTINEL}

## Refuted audit

None.

## Indeterminate audit

None.
"""

# The fields a recording round mutates. A no-op row must leave every one of them
# exactly as the first application left it.
ROUND_FIELDS = (
    "review_round_count",
    "review_retry_count",
    "finding_fingerprints",
    "previous_finding_fingerprints",
    "last_review_clean_source",
    "last_review_clean_digest",
)
RECORDED_FIELDS = (
    "last_review_record_operation_id",
    "last_review_record_payload_digest",
)


def _load_gate():
    """Import `_review_operation_gate` from the pack-owned script by path."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_loop_cohort_under_test", COHORT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._review_operation_gate


class ReviewRecordIdempotency(unittest.TestCase):
    maxDiff = None

    # ── harness ───────────────────────────────────────────────────────────

    def _spec_dir(self) -> Path:
        temporary = tempfile.TemporaryDirectory(
            prefix="review-record-idem-", ignore_cleanup_errors=True
        )
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        self._cwd = root
        spec_dir = root / "spec1"
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

    def _initialized(self) -> tuple[Path, str]:
        spec_dir = self._spec_dir()
        run_id = str(uuid.uuid4())
        result = self._run("init", str(spec_dir), "--run-id", run_id)
        self.assertEqual(result.returncode, 0, result.stderr)
        return spec_dir, run_id

    def _state(self, spec_dir: Path) -> dict:
        return json.loads((spec_dir / "state.json").read_text(encoding="utf-8"))

    def _fields(self, spec_dir: Path, names: tuple[str, ...]) -> dict:
        state = self._state(spec_dir)
        return {name: state.get(name) for name in names}

    def _record(self, spec_dir: Path, run_id: str, *form: str,
                operation_id: str | None = None) -> subprocess.CompletedProcess[str]:
        argv = ["review", "record", str(spec_dir), *form, "--expect-run-id", run_id]
        if operation_id is not None:
            argv += ["--operation-id", operation_id]
        return self._run(*argv)

    def _clean_file(self, spec_dir: Path) -> list[str]:
        path = spec_dir / "clean.md"
        path.write_text(CLEAN_SENTINEL, encoding="utf-8")
        return ["--direct-clean-file", str(path)]

    def _report(self, spec_dir: Path) -> list[str]:
        path = spec_dir / "adjudication.md"
        path.write_text(ADJUDICATION, encoding="utf-8")
        return ["--report", str(path), "--adjudication"]

    # ── R1: no id supplied — unchanged, and the recorded fields untouched ──

    def test_r1_flagless_leaves_the_recorded_fields_alone(self) -> None:
        spec_dir, run_id = self._initialized()
        self.assertEqual(
            self._record(spec_dir, run_id, "--fingerprint", FP_A,
                         operation_id=f"{run_id}:1").returncode, 0)
        recorded = self._fields(spec_dir, RECORDED_FIELDS)

        # A flagless round lands afterwards and must not displace the pair: it
        # names the last round recorded *under an id*, which this is not.
        self.assertEqual(self._record(spec_dir, run_id, "--all-skipped").returncode, 0)
        self.assertEqual(self._fields(spec_dir, RECORDED_FIELDS), recorded)
        self.assertEqual(self._state(spec_dir)["review_round_count"], 2)

    # ── R2: first application under an id records it ──────────────────────

    def test_r2_records_the_id_and_a_digest_for_every_form(self) -> None:
        for label, form in (
            ("fingerprint", ["--fingerprint", FP_A, "--fingerprint", FP_B]),
            ("all-skipped", ["--all-skipped"]),
            ("direct-clean", None),
            ("report", None),
        ):
            with self.subTest(form=label):
                spec_dir, run_id = self._initialized()
                argv = form or (self._clean_file(spec_dir) if label == "direct-clean"
                                else self._report(spec_dir))
                result = self._record(spec_dir, run_id, *argv,
                                      operation_id=f"{run_id}:1")
                self.assertEqual(result.returncode, 0, result.stderr)
                state = self._state(spec_dir)
                self.assertEqual(state["last_review_record_operation_id"], f"{run_id}:1")
                self.assertRegex(state["last_review_record_payload_digest"], r"^[0-9a-f]{64}$")

    def test_r2_two_distinct_ids_each_count_a_round(self) -> None:
        spec_dir, run_id = self._initialized()
        self._record(spec_dir, run_id, "--fingerprint", FP_A, operation_id=f"{run_id}:1")
        self._record(spec_dir, run_id, "--fingerprint", FP_B, operation_id=f"{run_id}:2")
        self.assertEqual(self._state(spec_dir)["review_round_count"], 2)

    # ── R3: same id, same payload — a completed write ─────────────────────

    def test_r3_replay_changes_nothing_and_says_so(self) -> None:
        spec_dir, run_id = self._initialized()
        op = f"{run_id}:7"
        self._record(spec_dir, run_id, "--fingerprint", FP_A, "--fingerprint", FP_B,
                     operation_id=op)
        after_first = self._fields(spec_dir, ROUND_FIELDS + RECORDED_FIELDS)

        replay = self._record(spec_dir, run_id, "--fingerprint", FP_A, "--fingerprint", FP_B,
                              operation_id=op)
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertEqual(self._fields(spec_dir, ROUND_FIELDS + RECORDED_FIELDS), after_first)
        self.assertIn("already recorded", replay.stdout)

    def test_r3_fingerprint_order_and_duplicates_are_one_payload(self) -> None:
        spec_dir, run_id = self._initialized()
        op = f"{run_id}:3"
        self._record(spec_dir, run_id, "--fingerprint", FP_A, "--fingerprint", FP_B,
                     operation_id=op)
        rounds = self._state(spec_dir)["review_round_count"]
        # Same set, reordered and with a duplicate.
        replay = self._record(spec_dir, run_id, "--fingerprint", FP_B,
                              "--fingerprint", FP_A, "--fingerprint", FP_B,
                              operation_id=op)
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertEqual(self._state(spec_dir)["review_round_count"], rounds)

    # ── R4: same id, different payload — refused ──────────────────────────

    def test_r4_conflicting_payload_refuses_and_mutates_nothing(self) -> None:
        spec_dir, run_id = self._initialized()
        op = f"{run_id}:4"
        self._record(spec_dir, run_id, "--fingerprint", FP_A, operation_id=op)
        before = (spec_dir / "state.json").read_bytes()

        conflict = self._record(spec_dir, run_id, "--fingerprint", FP_C, operation_id=op)
        self.assertNotEqual(conflict.returncode, 0)
        self.assertEqual((spec_dir / "state.json").read_bytes(), before)
        self.assertIn("different payload", conflict.stderr)

    def test_r4_a_different_form_under_the_same_id_is_a_conflict(self) -> None:
        # Pins cross-form conflict detection. It does NOT pin the digest's form
        # prefix: `--all-skipped` and `--fingerprint` carry different payload
        # bytes, so their digests differ with or without it. The prefix's mutation
        # proof is `test_the_digest_preimage_carries_its_form`.
        spec_dir, run_id = self._initialized()
        op = f"{run_id}:5"
        self._record(spec_dir, run_id, "--all-skipped", operation_id=op)
        before = (spec_dir / "state.json").read_bytes()
        conflict = self._record(spec_dir, run_id, "--fingerprint", FP_A, operation_id=op)
        self.assertNotEqual(conflict.returncode, 0)
        self.assertEqual((spec_dir / "state.json").read_bytes(), before)

    # ── R5: no computable digest — refuse rather than record ──────────────

    def test_r5_refuses_to_record_without_a_comparison_value(self) -> None:
        """A null payload digest must refuse, not record.

        R5's only production trigger is the report becoming unreadable between
        `_classify_report`'s read and the re-read that hashes it, which a
        subprocess cannot induce. The gate is therefore exercised directly: what
        matters is that a `None` digest never reaches the recorded fields, because
        an id stored without a comparison value leaves every later repeat
        undecidable.
        """
        gate = _load_gate()
        outcome, code = gate(
            {}, "run:1", None, expect_run_id="run", spec_name="spec1",
        )
        self.assertEqual(outcome, "refuse")
        self.assertNotEqual(code, 0)

    def test_r5_precedes_the_conflict_check(self) -> None:
        # Ordering matters: a round recorded with a null digest must not be
        # reported as a payload conflict, which would send an operator to the
        # wrong diagnosis.
        gate = _load_gate()
        outcome, _ = gate(
            {"last_review_record_operation_id": "run:1",
             "last_review_record_payload_digest": "deadbeef"},
            "run:1", None, expect_run_id="run", spec_name="spec1",
        )
        self.assertEqual(outcome, "refuse")

    # ── R6: malformed id — refused before anything else ───────────────────

    def test_r6_malformed_ids_refuse_and_mutate_nothing(self) -> None:
        spec_dir, run_id = self._initialized()
        before = (spec_dir / "state.json").read_bytes()
        for bad in ("no-colon", f"{run_id}:", f"{run_id}:abc", "wrong-run:1", f":{1}",
                    # Accepted by the original `^...$`/`\d` pattern and unequal to
                    # the canonical spelling, so each recorded the same round again.
                    f"{run_id}:1\n", f"{run_id}:\u0661", f"{run_id}:01",
                    f"{run_id}:{'9' * 19}"):
            with self.subTest(operation_id=bad):
                result = self._record(spec_dir, run_id, "--fingerprint", FP_A,
                                      operation_id=bad)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((spec_dir / "state.json").read_bytes(), before)

    # ── cross-row: the refusals are tellable apart ────────────────────────

    def test_the_three_refusal_reasons_are_distinct(self) -> None:
        """All three outcomes AC7 names, not two.

        The uncomputable-digest reason is only reachable through the gate, so it
        is captured there; comparing two of three would let that message be made
        identical to the conflict message without reddening anything.
        """
        import contextlib
        import io

        spec_dir, run_id = self._initialized()
        op = f"{run_id}:6"
        self._record(spec_dir, run_id, "--fingerprint", FP_A, operation_id=op)

        malformed = self._record(spec_dir, run_id, "--fingerprint", FP_A,
                                 operation_id="nope").stderr.strip()
        conflict = self._record(spec_dir, run_id, "--fingerprint", FP_C,
                                operation_id=op).stderr.strip()
        # Load before redirecting: the module reconfigures the real streams at
        # import time and a StringIO has no `reconfigure`.
        gate = _load_gate()
        buffer = io.StringIO()
        with contextlib.redirect_stderr(buffer):
            gate({}, f"{run_id}:1", None,
                 expect_run_id=run_id, spec_name=spec_dir.name)
        undecidable = buffer.getvalue().strip()

        reasons = [malformed, conflict, undecidable]
        self.assertTrue(all(reasons), f"an empty refusal reason: {reasons}")
        self.assertEqual(len(set(reasons)), 3, f"reasons not pairwise distinct: {reasons}")

    # ── the persisted schema ──────────────────────────────────────────────

    def test_a_pre_change_state_file_still_works(self) -> None:
        spec_dir, run_id = self._initialized()
        state = self._state(spec_dir)
        for name in RECORDED_FIELDS:
            state.pop(name, None)
        (spec_dir / "state.json").write_text(json.dumps(state, indent=2) + "\n",
                                             encoding="utf-8")
        result = self._record(spec_dir, run_id, "--all-skipped",
                              operation_id=f"{run_id}:1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self._state(spec_dir)["last_review_record_operation_id"], f"{run_id}:1")

    def test_the_digest_preimage_carries_its_form(self) -> None:
        # The stored digest must equal sha256(form + "\n" + payload); pinning it
        # here is what makes the "two forms never collide" claim checkable.
        spec_dir, run_id = self._initialized()
        self._record(spec_dir, run_id, "--fingerprint", FP_A, "--fingerprint", FP_B,
                     operation_id=f"{run_id}:1")
        expected = hashlib.sha256(
            f"fingerprint\n{FP_A}\n{FP_B}".encode()).hexdigest()
        self.assertEqual(
            self._state(spec_dir)["last_review_record_payload_digest"], expected)


if __name__ == "__main__":
    unittest.main()
