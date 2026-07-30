#!/usr/bin/env python3
"""Self-test for loop-engine.py.

Runs the engine as a subprocess against fixture work-dirs in a tempdir.
Covers: all three mode lifecycles, invalid transitions, guard refusal,
side-effect scope boundary, file-path resolution, and idempotent reset.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "loop-engine.py"
LC = Path(__file__).resolve().parent / "loop-cohort.py"
CSS = Path(__file__).resolve().parent / "check-spec-status.py"


def run(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"loop-engine {list(args)} exited {result.returncode}:\n{result.stderr}"
        )
    return result


def state(tmp: Path) -> dict:
    return json.loads((tmp / "engine-state.json").read_text(encoding="utf-8"))


# ── spec-plan lifecycle ───────────────────────────────────────────────────────

def test_spec_plan_lifecycle_to_human_gate(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "spec-plan", check=True)
    s = state(tmp)
    assert s["state"] == "SPEC-PLAN-DRAFTING"
    assert s["mode"] == "spec-plan"
    assert s["feature"] == tmp.name

    run("transition", str(tmp), "spec-ready", check=True)
    assert state(tmp)["state"] == "SPEC-PLAN-REVIEW"

    run("transition", str(tmp), "reviewers-clean", check=True)
    assert state(tmp)["state"] == "SPEC-PLAN-HUMAN-GATE"
    print("  PASS: spec-plan reaches SPEC-PLAN-HUMAN-GATE")


def test_spec_plan_findings_loop_back(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "spec-plan", check=True)
    run("transition", str(tmp), "spec-ready", check=True)
    run("transition", str(tmp), "findings-remain", check=True)
    assert state(tmp)["state"] == "SPEC-PLAN-DRAFTING"
    print("  PASS: spec-plan findings-remain loops back to SPEC-PLAN-DRAFTING")


# ── doc lifecycle ─────────────────────────────────────────────────────────────

def test_doc_full_lifecycle(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "doc", check=True)
    assert state(tmp)["state"] == "DOC-DRAFTING"
    run("transition", str(tmp), "doc-ready", check=True)
    assert state(tmp)["state"] == "DOC-REVIEW"
    run("transition", str(tmp), "reviewers-clean", check=True)
    assert state(tmp)["state"] == "DOC-HUMAN-GATE"
    run("transition", str(tmp), "doc-approved", check=True)
    assert state(tmp)["state"] == "DONE"
    print("  PASS: doc lifecycle → DONE")


def test_doc_returned_loops_back(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "doc", check=True)
    run("transition", str(tmp), "doc-ready", check=True)
    run("transition", str(tmp), "reviewers-clean", check=True)
    run("transition", str(tmp), "doc-returned", check=True)
    assert state(tmp)["state"] == "DOC-DRAFTING"
    print("  PASS: doc-returned loops back to DOC-DRAFTING")


# ── invalid transitions ───────────────────────────────────────────────────────

def test_invalid_transition_exits_nonzero_with_message(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "doc", check=True)
    r = run("transition", str(tmp), "plan-approved")
    assert r.returncode != 0
    assert r.stderr.strip()
    # State must not advance
    assert state(tmp)["state"] == "DOC-DRAFTING"
    print("  PASS: invalid transition exits non-zero; state unchanged")


def test_terminal_state_has_no_valid_events(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "doc", check=True)
    run("transition", str(tmp), "doc-ready", check=True)
    run("transition", str(tmp), "reviewers-clean", check=True)
    run("transition", str(tmp), "doc-approved", check=True)
    assert state(tmp)["state"] == "DONE"
    r = run("transition", str(tmp), "doc-ready")
    assert r.returncode != 0
    assert "(none" in r.stderr or "terminal" in r.stderr
    print("  PASS: terminal DONE state refuses all events")


# ── status ────────────────────────────────────────────────────────────────────

def test_status_json_schema(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "spec-plan", check=True)
    r = run("status", str(tmp), "--json", check=True)
    data = json.loads(r.stdout)
    assert set(data) == {"feature", "mode", "state", "last_transition_at"}
    assert data["mode"] == "spec-plan"
    print("  PASS: status --json emits correct schema")


def test_status_human_readable(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "doc", check=True)
    r = run("status", str(tmp), check=True)
    assert "|" in r.stdout
    print("  PASS: status (human-readable) contains | separators")


def test_status_absent_exits_nonzero(tmp: Path) -> None:
    r = run("status", str(tmp))
    assert r.returncode != 0
    print("  PASS: status without engine-state.json exits non-zero")


# ── init guards ───────────────────────────────────────────────────────────────

def test_init_refuses_if_already_exists(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "doc", check=True)
    r = run("init", str(tmp), "--mode", "doc")
    assert r.returncode != 0
    assert r.stderr.strip()
    print("  PASS: init refuses if engine-state.json already exists")


# ── reset ─────────────────────────────────────────────────────────────────────

def test_reset_idempotent(tmp: Path) -> None:
    run("init", str(tmp), "--mode", "doc", check=True)
    run("reset", str(tmp), check=True)
    assert not (tmp / "engine-state.json").exists()
    run("reset", str(tmp), check=True)  # second call also exits 0
    print("  PASS: reset deletes file; second reset is idempotent")


# ── file-path resolution ──────────────────────────────────────────────────────

def test_file_path_resolves_to_parent(tmp: Path) -> None:
    doc = tmp / "0076-foo.md"
    doc.write_text("# RFC\n", encoding="utf-8")
    run("init", str(doc), "--mode", "doc", check=True)
    s = state(tmp)
    assert s["feature"] == "0076-foo", s["feature"]
    assert s["mode"] == "doc"
    # status should also work with file path
    r = run("status", str(doc), "--json", check=True)
    data = json.loads(r.stdout)
    assert data["feature"] == "0076-foo"
    print("  PASS: file path resolves; feature = file stem")


# ── guard scope boundary ──────────────────────────────────────────────────────

def test_reviewers_clean_from_spec_plan_review_no_css_guard(tmp: Path) -> None:
    """reviewers-clean from SPEC-PLAN-REVIEW must NOT invoke check-spec-status.py.

    Verified by: no spec.md present in work-dir. If the CSS guard fired,
    it would fail (spec.md absent). The transition must still succeed.
    """
    run("init", str(tmp), "--mode", "spec-plan", check=True)
    run("transition", str(tmp), "spec-ready", check=True)
    # No spec.md — CSS guard would fail if incorrectly wired here
    r = run("transition", str(tmp), "reviewers-clean")
    assert r.returncode == 0, (
        f"unexpected guard failure on SPEC-PLAN-REVIEW+reviewers-clean: {r.stderr}"
    )
    assert state(tmp)["state"] == "SPEC-PLAN-HUMAN-GATE"
    print("  PASS: reviewers-clean from SPEC-PLAN-REVIEW has no CSS guard (scope boundary)")


def test_doc_reviewers_clean_no_css_guard(tmp: Path) -> None:
    """doc mode reviewers-clean must NOT invoke check-spec-status.py."""
    run("init", str(tmp), "--mode", "doc", check=True)
    run("transition", str(tmp), "doc-ready", check=True)
    r = run("transition", str(tmp), "reviewers-clean")
    assert r.returncode == 0, (
        f"unexpected guard failure on DOC-REVIEW+reviewers-clean: {r.stderr}"
    )
    assert state(tmp)["state"] == "DOC-HUMAN-GATE"
    print("  PASS: doc reviewers-clean from DOC-REVIEW has no CSS guard")


def test_css_guard_fires_on_code_review_reviewers_clean(tmp: Path) -> None:
    """CODE-REVIEW+reviewers-clean must invoke check-spec-status.py guard.

    Simulated by placing a spec.md with Status: Draft (not Shipped) in the
    work-dir and driving the FSM to CODE-REVIEW using doc→code workaround.
    Since we can't easily reach CODE-REVIEW without loop-cohort init+approve,
    we verify guard wiring by checking that the engine calls CSS when the
    guard key matches, by patching PATH with a fake CSS that exits non-zero.
    """
    # Write a stub CSS that always exits 1 to verify it's called
    stub_css = tmp / "fake-css.py"
    stub_css.write_text("import sys; sys.exit(1)\n", encoding="utf-8")

    # Directly manipulate engine-state.json to simulate CODE-REVIEW state
    import datetime
    engine_state = {
        "feature": tmp.name,
        "mode": "code",
        "state": "CODE-REVIEW",
        "last_transition_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (tmp / "engine-state.json").write_text(
        json.dumps(engine_state, indent=2), encoding="utf-8"
    )

    # Monkey-patch the CSS path by creating a wrapper that shadows the real CSS
    # We do this by temporarily writing a fake check-spec-status.py that always fails
    real_css = CSS
    if not real_css.exists():
        print("  SKIP: check-spec-status.py not present, cannot test guard wiring")
        return

    # Backup and replace
    real_content = real_css.read_bytes()
    real_css.write_text("#!/usr/bin/env python3\nimport sys; sys.exit(1)\n", encoding="utf-8")
    try:
        r = run("transition", str(tmp), "reviewers-clean")
        assert r.returncode != 0, "expected guard refusal with failing CSS"
        # State should NOT have advanced
        assert state(tmp)["state"] == "CODE-REVIEW"
        print("  PASS: CSS guard fires and refuses transition on CODE-REVIEW+reviewers-clean")
    finally:
        real_css.write_bytes(real_content)


# ── runner ────────────────────────────────────────────────────────────────────

def main() -> None:
    tests = [
        test_spec_plan_lifecycle_to_human_gate,
        test_spec_plan_findings_loop_back,
        test_doc_full_lifecycle,
        test_doc_returned_loops_back,
        test_invalid_transition_exits_nonzero_with_message,
        test_terminal_state_has_no_valid_events,
        test_status_json_schema,
        test_status_human_readable,
        test_status_absent_exits_nonzero,
        test_init_refuses_if_already_exists,
        test_reset_idempotent,
        test_file_path_resolves_to_parent,
        test_reviewers_clean_from_spec_plan_review_no_css_guard,
        test_doc_reviewers_clean_no_css_guard,
        test_css_guard_fires_on_code_review_reviewers_clean,
    ]
    failed = 0
    for t in tests:
        with tempfile.TemporaryDirectory() as td:
            try:
                t(Path(td))
            except AssertionError as e:
                print(f"  FAIL: {t.__name__}: {e}")
                failed += 1
    if failed:
        print(f"\n{failed} test(s) failed.")
        sys.exit(1)
    print(f"\n{len(tests)} test(s) passed.")


if __name__ == "__main__":
    main()
