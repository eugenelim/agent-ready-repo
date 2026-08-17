#!/usr/bin/env python3
"""One-shot: capture pre-change golden fixtures (spec/work-loop-in-process-guards T0).

Run ONCE, against the tree BEFORE T1a moves anything. Not shipped; not re-run.
A golden captured after the relocation is the tautology this task exists to
prevent — see `docs/knowledge/topics/
a-test-that-moves-with-the-code-cannot-catch-the-code-being-wrong.json`.

Two outputs:

  fixtures/golden_digests.json      sha256_canonical_contract per frozen corpus file
  fixtures/golden_cli_streams.json  returncode/stdout/stderr per CLI failure branch

`before` is what the pre-change CLI actually did. `after` is authored by hand, and
only for rows whose verdict this change intentionally alters; each such row must
declare a `change_reason` from `golden_support.CHANGE_REASONS`. The parity test
asserts `after` where present and `before` everywhere else, so an intentional
change is recorded rather than discovered, and an unintentional one still fails.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
TESTS = REPO / "packs" / "core" / "tests" / "skills" / "work-loop"
SCRIPTS = REPO / "packs" / "core" / ".apm" / "skills" / "work-loop" / "scripts"
COHORT = SCRIPTS / "loop-cohort.py"
CHECK_STATUS = SCRIPTS / "check-spec-status.py"

sys.path.insert(0, str(TESTS))
import golden_support as gs  # noqa: E402


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── digests ────────────────────────────────────────────────────────────────

def capture_digests() -> dict:
    """One digest per corpus artifact, from the pre-change implementation.

    No line-ending variants: `Path.read_text()` folds CR and CRLF to LF before
    `canonical_contract` runs, so a CRLF-on-disk artifact hashes identically to its
    LF twin regardless of the fold — a digest-level assertion about it can never
    fail. The fold is covered directly, on strings, in the test module.
    """
    cohort = _load(COHORT, "_cohort_pre_change")
    out = {}
    for path in gs.corpus_entries():
        out[gs.corpus_key(path)] = cohort.sha256_canonical_contract(path)
    return {
        "_note": (
            "sha256_canonical_contract over fixtures/corpus/, captured from "
            "loop-cohort.py BEFORE the guard extraction. The moved implementation "
            "must reproduce these exactly; perturbing the line-rstrip or the status "
            "splice in the relocated canonical_contract must break this "
            "(mutation-verified)."
        ),
        "digests": out,
    }


# ── CLI streams ────────────────────────────────────────────────────────────

SPEC_MD = """# Spec: fixture

- **Status:** {status} <!-- Draft | Approved | Implementing | Shipped | Archived -->

## Acceptance Criteria

- [ ] AC1
"""
PLAN_MD = """# Plan: fixture

- **Status:** {status} <!-- Drafting | Approved | Executing | Done -->

## T1 First

**Depends on:** none

**Touches:** `a.py`
"""
RID = "11111111-2222-3333-4444-555555555555"
OTHER_RID = "99999999-8888-7777-6666-555555555555"


def _state(**over) -> dict:
    st = {
        "schema_version": 1, "run_id": RID, "feature": "fixture",
        "plan_review_status": "pending",
        "approved_spec_hash": None, "approved_plan_hash": None, "plan_hash": None,
        "schedule_waves": [], "current_wave_index": 0,
        "implementation_retry_count": 0, "review_round_count": 0,
        "review_retry_count": 0, "finding_fingerprints": [],
        "previous_finding_fingerprints": [],
        "max_implementation_retries": 5, "max_review_retries": 5,
    }
    st.update(over)
    return st


def build_case(root: Path, name: str, *, spec_status="Approved", plan_status="Approved",
               state_over=None, no_state=False, no_spec=False, no_plan=False,
               approve=False, schedule=None, spec_body=None, cohort=None) -> Path:
    """Materialise one spec dir. `approve` pins real hashes so drift is meaningful."""
    d = root / name
    d.mkdir(parents=True)
    if not no_spec:
        (d / "spec.md").write_text(
            spec_body if spec_body is not None else SPEC_MD.format(status=spec_status),
            encoding="utf-8")
    if not no_plan:
        (d / "plan.md").write_text(PLAN_MD.format(status=plan_status), encoding="utf-8")
    if no_state:
        return d
    over = dict(state_over or {})
    if approve:
        over.setdefault("plan_review_status", "approved")
        over.setdefault("approved_spec_hash", cohort.sha256_canonical_contract(d / "spec.md"))
        over.setdefault("approved_plan_hash", cohort.sha256_canonical_contract(d / "plan.md"))
        over.setdefault("plan_hash", cohort.sha256_canonical_contract(d / "plan.md"))
        over.setdefault("schedule_waves", schedule if schedule is not None else [["T1"], ["T2"]])
    (d / "state.json").write_text(json.dumps(_state(**over), indent=2), encoding="utf-8")
    return d


def run(script: Path, *args, cwd: Path) -> tuple[int, str, str]:
    p = subprocess.run(
        [sys.executable, str(script), *[str(a) for a in args]],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False, cwd=str(cwd),
    )
    return p.returncode, p.stdout, p.stderr


def capture_cli(root: Path) -> dict:
    cohort = _load(COHORT, "_cohort_fixture_builder")
    rows: list[dict] = []

    def emit(key: str, script: Path, argv: list, spec_dir: Path, *,
             change_reason=None, after=None, note=None):
        rc, out, err = run(script, *argv, cwd=root)
        row = {
            "key": key,
            "tool": script.name,
            "argv": [a if not isinstance(a, Path) else "<SPEC_DIR>" for a in argv],
            "before": {
                "returncode": rc,
                "stdout": gs.normalize(out, spec_dir=spec_dir),
                "stderr": gs.normalize(err, spec_dir=spec_dir),
            },
        }
        if note:
            row["note"] = note
        if change_reason:
            row["change_reason"] = change_reason
            row["after"] = after
        rows.append(row)

    C, S = COHORT, CHECK_STATUS

    # ── identity ───────────────────────────────────────────────────────────
    d = build_case(root, "id-ok", cohort=cohort)
    emit("identity/ok", C, ["identity", d, "--expect-run-id", RID], d)
    emit("identity/ok-json", C, ["identity", d, "--expect-run-id", RID, "--json"], d)
    d = build_case(root, "id-mismatch", cohort=cohort)
    emit("identity/run-id-mismatch", C, ["identity", d, "--expect-run-id", OTHER_RID], d)
    d = build_case(root, "id-badschema", state_over={"schema_version": 99}, cohort=cohort)
    emit("identity/unsupported-schema", C, ["identity", d, "--expect-run-id", RID], d)
    d = build_case(root, "id-nostate", no_state=True, cohort=cohort)
    emit("identity/absent-state", C, ["identity", d, "--expect-run-id", RID], d)

    # ── plan check-current ─────────────────────────────────────────────────
    d = build_case(root, "plan-pending", cohort=cohort)
    emit("plan-check-current/pending", C, ["plan", "check-current", d], d,
         note="the one refusal with no verb prefix")
    d = build_case(root, "plan-ok", approve=True, cohort=cohort)
    emit("plan-check-current/ok", C, ["plan", "check-current", d], d)
    emit("plan-check-current/ok-require-schedule", C,
         ["plan", "check-current", d, "--require-schedule"], d)
    d = build_case(root, "plan-specdrift", approve=True, cohort=cohort)
    (d / "spec.md").write_text(SPEC_MD.format(status="Approved") + "\ndrifted\n", encoding="utf-8")
    emit("plan-check-current/spec-drift", C, ["plan", "check-current", d], d)
    d = build_case(root, "plan-plandrift", approve=True, cohort=cohort)
    (d / "plan.md").write_text(PLAN_MD.format(status="Approved") + "\ndrifted\n", encoding="utf-8")
    emit("plan-check-current/plan-drift", C, ["plan", "check-current", d], d)
    d = build_case(root, "plan-nospec", approve=True, cohort=cohort)
    (d / "spec.md").unlink()
    emit("plan-check-current/missing-spec", C, ["plan", "check-current", d], d)
    d = build_case(root, "plan-noplan", approve=True, cohort=cohort)
    (d / "plan.md").unlink()
    emit("plan-check-current/missing-plan", C, ["plan", "check-current", d], d)
    d = build_case(root, "plan-statusregress", approve=True, cohort=cohort)
    (d / "spec.md").write_text(SPEC_MD.format(status="Draft"), encoding="utf-8")
    emit("plan-check-current/status-regressed", C, ["plan", "check-current", d], d)
    d = build_case(root, "plan-noschedule", approve=True, schedule=[], cohort=cohort)
    emit("plan-check-current/empty-waves-require-schedule", C,
         ["plan", "check-current", d, "--require-schedule"], d)
    d = build_case(root, "plan-waveoor", approve=True,
                   state_over={"current_wave_index": 9}, cohort=cohort)
    emit("plan-check-current/wave-index-out-of-range", C,
         ["plan", "check-current", d, "--require-schedule"], d)
    d = build_case(root, "plan-hashmismatch", approve=True,
                   state_over={"plan_hash": "0" * 64}, cohort=cohort)
    emit("plan-check-current/plan-hash-not-scheduled", C,
         ["plan", "check-current", d, "--require-schedule"], d)

    # ── schedule check-current ─────────────────────────────────────────────
    d = build_case(root, "sched-ok", approve=True, cohort=cohort)
    emit("schedule-check-current/ok", C, ["schedule", "check-current", d], d)
    d = build_case(root, "sched-drift", approve=True,
                   state_over={"plan_hash": "0" * 64}, cohort=cohort)
    emit("schedule-check-current/plan-hash-drift", C, ["schedule", "check-current", d], d)
    d = build_case(root, "sched-noplan", approve=True, cohort=cohort)
    (d / "plan.md").unlink()
    emit("schedule-check-current/missing-plan", C, ["schedule", "check-current", d], d)
    d = build_case(root, "sched-badstatus", approve=True, cohort=cohort)
    (d / "plan.md").write_text(PLAN_MD.format(status="Drafting"), encoding="utf-8")
    emit("schedule-check-current/plan-status-illegal", C, ["schedule", "check-current", d], d)
    d = build_case(root, "sched-nostate", no_state=True, cohort=cohort)
    emit("schedule-check-current/absent-state", C, ["schedule", "check-current", d], d)

    # ── check --phase ──────────────────────────────────────────────────────
    d = build_case(root, "chk-impl", cohort=cohort)
    emit("check/implement-ok", C, ["check", d, "--phase", "implement"], d)
    d = build_case(root, "chk-impl-nostate", no_state=True, cohort=cohort)
    emit("check/implement-absent-state", C, ["check", d, "--phase", "implement"], d,
         note="read_state refuses BEFORE the implement stub — not a total no-op")
    d = build_case(root, "chk-review-under", state_over={"review_retry_count": 1}, cohort=cohort)
    emit("check/review-under-cap", C, ["check", d, "--phase", "review"], d)
    d = build_case(root, "chk-review-at", state_over={"review_retry_count": 5}, cohort=cohort)
    emit("check/review-at-cap", C, ["check", d, "--phase", "review"], d)
    d = build_case(root, "chk-gf-under",
                   state_over={"implementation_retry_count": 1}, cohort=cohort)
    emit("check/gates-failed-under-cap", C, ["check", d, "--phase", "gates-failed"], d)
    d = build_case(root, "chk-gf-at", state_over={"implementation_retry_count": 5}, cohort=cohort)
    emit("check/gates-failed-at-cap", C, ["check", d, "--phase", "gates-failed"], d)
    d = build_case(root, "chk-badschema", state_over={"schema_version": 99}, cohort=cohort)
    emit("check/unsupported-schema-non-implement", C, ["check", d, "--phase", "review"], d)

    # AC16 — coercible numerics. int() absorbs these today; AC8 refuses them after.
    d = build_case(root, "chk-strcount", state_over={"review_retry_count": "1"}, cohort=cohort)
    emit("check/review-string-typed-count", C, ["check", d, "--phase", "review"], d,
         change_reason="numeric-coercion", after={"returncode": 1},
         note="int('1') coerces today; AC8 validates type and refuses")
    d = build_case(root, "chk-floatcount", state_over={"review_retry_count": 1.7}, cohort=cohort)
    emit("check/review-float-typed-count", C, ["check", d, "--phase", "review"], d,
         change_reason="numeric-coercion", after={"returncode": 1},
         note="int(1.7) truncates to 1 today; AC8 refuses a non-int")
    d = build_case(root, "chk-negcount", state_over={"review_retry_count": -3}, cohort=cohort)
    emit("check/review-negative-count", C, ["check", d, "--phase", "review"], d,
         change_reason="numeric-coercion", after={"returncode": 1},
         note="negative passes the cap comparison today; AC8 requires non-negative")

    # ── wave check ─────────────────────────────────────────────────────────
    d = build_case(root, "wave-more-ok", approve=True, cohort=cohort)
    emit("wave-check/more-ok", C, ["wave", "check", d, "--expect", "more"], d)
    emit("wave-check/more-ok-with-index", C,
         ["wave", "check", d, "--expect", "more", "--wave-index", "0"], d)
    emit("wave-check/last-not-last", C, ["wave", "check", d, "--expect", "last"], d)
    emit("wave-check/index-mismatch", C,
         ["wave", "check", d, "--expect", "more", "--wave-index", "1"], d)
    d = build_case(root, "wave-last-ok", approve=True,
                   state_over={"current_wave_index": 1}, cohort=cohort)
    emit("wave-check/last-ok", C, ["wave", "check", d, "--expect", "last"], d)
    emit("wave-check/more-no-more", C, ["wave", "check", d, "--expect", "more"], d)
    d = build_case(root, "wave-nostate", no_state=True, cohort=cohort)
    emit("wave-check/absent-state", C, ["wave", "check", d, "--expect", "last"], d)

    # ── check-spec-status ──────────────────────────────────────────────────
    d = build_case(root, "css-shipped", spec_status="Shipped", cohort=cohort)
    emit("check-spec-status/default-shipped-ok", S, [d], d)
    d = build_case(root, "css-draft", spec_status="Draft", cohort=cohort)
    emit("check-spec-status/default-draft-refuses", S, [d], d)
    d = build_case(root, "css-approved", spec_status="Approved", cohort=cohort)
    emit("check-spec-status/expect-approved-ok", S, [d, "--expect", "Approved"], d)
    emit("check-spec-status/expect-approved-plan-ok", S,
         [d, "--expect", "Approved", "--file", "plan.md"], d)
    d = build_case(root, "css-nospec", no_spec=True, cohort=cohort)
    emit("check-spec-status/absent-spec", S, [d, "--expect", "Approved"], d)
    d = build_case(root, "css-nostatusline", spec_body="# Spec\n\nno status here\n", cohort=cohort)
    emit("check-spec-status/no-status-line", S, [d], d)
    d = build_case(root, "css-outside", cohort=cohort)
    emit("check-spec-status/file-escapes-spec-dir", S, [d, "--file", "../outside.md"], d)
    # AC9 — a multi-component --file inside spec_dir succeeds today, refuses after.
    d = build_case(root, "css-subdir", cohort=cohort)
    (d / "sub").mkdir()
    (d / "sub" / "spec.md").write_text(SPEC_MD.format(status="Approved"), encoding="utf-8")
    emit("check-spec-status/file-multi-component-inside", S,
         [d, "--expect", "Approved", "--file", "sub/spec.md"], d,
         change_reason="file-narrowing", after={"returncode": 1},
         note="succeeds today (is_relative_to passes); AC9 requires a single component")

    # ── AC15(3) artifact-integrity ─────────────────────────────────────────
    # Today these reads are plain `path.read_text()`, which follows symlinks and
    # has no size cap. After the change they go through `read_managed_text`
    # (O_NOFOLLOW + O_NONBLOCK + S_ISREG + 8 MiB), so each refuses.
    d = build_case(root, "integ-symlink-spec", spec_status="Approved", cohort=cohort)
    real = d / "real-spec.md"
    real.write_text(SPEC_MD.format(status="Approved"), encoding="utf-8")
    (d / "spec.md").unlink()
    (d / "spec.md").symlink_to(real)          # symlink to a file INSIDE spec_dir:
    emit("check-spec-status/symlinked-spec-md", S, [d, "--expect", "Approved"], d,
         change_reason="artifact-integrity", after={"returncode": 1},
         note="resolves inside spec_dir so is_relative_to passes and read_text "
              "follows it today; O_NOFOLLOW refuses it after")

    d = build_case(root, "integ-symlink-plan", approve=True, cohort=cohort)
    realp = d / "real-plan.md"
    realp.write_text((d / "plan.md").read_text(encoding="utf-8"), encoding="utf-8")
    (d / "plan.md").unlink()
    (d / "plan.md").symlink_to(realp)
    emit("plan-check-current/symlinked-plan-md", C, ["plan", "check-current", d], d,
         change_reason="artifact-integrity", after={"returncode": 1},
         note="sha256_canonical_contract reads through the symlink today")

    d = build_case(root, "integ-oversized-spec", spec_status="Approved", cohort=cohort)
    filler = "\n<!-- " + ("x" * 4096) + " -->\n"
    with (d / "spec.md").open("a", encoding="utf-8") as fh:
        written = 0
        while written < 8 * 1024 * 1024 + 4096:
            fh.write(filler)
            written += len(filler)
    emit("check-spec-status/oversized-spec-md", S, [d, "--expect", "Approved"], d,
         change_reason="artifact-integrity", after={"returncode": 1},
         note="just over the 8 MiB managed-read cap; unbounded read_text accepts "
              "it today")

    return {
        "_note": (
            "Captured from the pre-change CLIs. `before` is observed; `after` is "
            "authored and present only on rows declaring a change_reason from "
            "golden_support.CHANGE_REASONS. Streams are normalized through "
            "golden_support.normalize at capture and compare time."
        ),
        "_not_capturable": (
            "One artifact-integrity case has NO recordable `before`: a FIFO at "
            "spec.md or plan.md. The pre-change `read_text()` blocks on it "
            "indefinitely (verified with SIGALRM), so there is no exit code to "
            "capture — which is itself the strongest evidence for the bounded "
            "reader, since that unbounded block would sit inside the engine's "
            "critical section once the guards run in-process. It is covered by "
            "T1a's direct API tests rather than by a golden row."
        ),
        "rows": rows,
    }


def main() -> int:
    import tempfile
    gs.FIXTURES.mkdir(parents=True, exist_ok=True)

    digests = capture_digests()
    gs.GOLDEN_DIGESTS.write_text(json.dumps(digests, indent=2, sort_keys=True) + "\n",
                                 encoding="utf-8")
    print(f"digests: {len(digests['digests'])} corpus artifacts")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "init", "-q", str(root)], check=True, capture_output=True)
        cli = capture_cli(root)
    gs.GOLDEN_CLI_STREAMS.write_text(json.dumps(cli, indent=2) + "\n", encoding="utf-8")
    changed = [r["key"] for r in cli["rows"] if "after" in r]
    print(f"cli rows: {len(cli['rows'])} ({len(changed)} with an authored `after`)")
    for k in changed:
        print(f"    after: {k}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
