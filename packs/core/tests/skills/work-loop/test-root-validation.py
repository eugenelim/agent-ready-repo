#!/usr/bin/env python3
"""Tests for the CLI path-argument boundary validator (spec/pack-script-root-boundary-validation).

Covers the three scripts that read a filesystem path from argv:
`lint-traceability.py --root`, `lint-spec-status.py --root`, and
`loop-cohort.py review inspect --report`.

Two properties are asserted, and they pull in opposite directions:

  1. *Parity* (AC5) — every currently-valid invocation keeps its exit code.
     The validator must not narrow what the linters can scan; `--root` is the
     caller-supplied scan scope, not a confined subdirectory.
  2. *Diagnostic* (AC6) — an unusable path exits non-zero naming the offending
     path, rather than surfacing a traceback.

Every case invokes the real script through `subprocess`, never a synthesised
import, so the test exercises the documented invocation path.

Run: python3 test-root-validation.py
Exit 0 = all pass; exit non-zero = at least one failure.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# The pack ships tests under packs/<pack>/tests/ and runtime primitives under
# packs/<pack>/.apm/ — tests are visible in the catalogue and never installed.
_SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop"
SCRIPT_DIR = _SKILL_DIR / "scripts"

if not SCRIPT_DIR.is_dir():  # wrong parents[] depth after a move
    raise SystemExit(f"subject dir not found at {SCRIPT_DIR} — check the parents[] depth")

TRACEABILITY = SCRIPT_DIR / "lint-traceability.py"
SPEC_STATUS = SCRIPT_DIR / "lint-spec-status.py"
LOOP_COHORT = SCRIPT_DIR / "loop-cohort.py"

# The two `--root` scripts. `loop-cohort.py` takes `--report` and is driven
# separately because it needs a subcommand and cohort state.
ROOT_SCRIPTS = [("lint-traceability", TRACEABILITY), ("lint-spec-status", SPEC_STATUS)]

failures: list[str] = []
ran = 0


def ok(name: str) -> None:
    global ran
    ran += 1
    print(f"ok   [{name}]")


def fail(name: str, reason: str) -> None:
    global ran
    ran += 1
    failures.append(name)
    print(f"FAIL [{name}]: {reason}", file=sys.stderr)


def run(script: Path, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(script)] + list(args),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        cwd=str(cwd) if cwd else None,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


# ---------------------------------------------------------------------------
# AC6 — an unusable --root is a diagnostic, not a traceback
# ---------------------------------------------------------------------------

def test_nonexistent_root_exits_nonzero_with_diagnostic() -> None:
    """A --root that does not exist must exit non-zero and name the path.

    Guards the failure mode the boundary validator introduces: turning an
    unusable path into an explicit refusal rather than letting it flow into a
    walk that silently yields nothing.
    """
    with tempfile.TemporaryDirectory() as td:
        missing = Path(td) / "no-such-directory"
        for label, script in ROOT_SCRIPTS:
            name = f"{label}: nonexistent --root exits non-zero with diagnostic"
            rc, out, err = run(script, "--root", str(missing))
            combined = f"{out}\n{err}"
            if rc == 0:
                fail(name, f"expected non-zero exit, got 0 (stdout={out!r} stderr={err!r})")
            elif "Traceback" in combined:
                fail(name, f"raised a traceback instead of a diagnostic:\n{combined}")
            elif "no-such-directory" not in combined:
                fail(name, f"diagnostic does not name the offending path: {combined!r}")
            else:
                ok(name)


def test_file_valued_root_exits_nonzero() -> None:
    """A --root pointing at a file rather than a directory must be refused."""
    with tempfile.TemporaryDirectory() as td:
        a_file = Path(td) / "not-a-dir.txt"
        a_file.write_text("x", encoding="utf-8")
        for label, script in ROOT_SCRIPTS:
            name = f"{label}: file-valued --root exits non-zero"
            rc, out, err = run(script, "--root", str(a_file))
            combined = f"{out}\n{err}"
            if rc == 0:
                fail(name, f"expected non-zero exit, got 0 (stdout={out!r} stderr={err!r})")
            elif "Traceback" in combined:
                fail(name, f"raised a traceback instead of a diagnostic:\n{combined}")
            elif "not-a-dir.txt" not in combined:
                fail(name, f"diagnostic does not name the offending path: {combined!r}")
            else:
                ok(name)


def test_missing_report_classifies_invalid_not_crash() -> None:
    """`review inspect --report <missing>` yields `invalid`, and still exits 0.

    `--report` is normalise-only at the boundary, unlike the two `--root`
    scripts. SKILL.md defines `invalid` as a Surface signal for a malformed
    reviewer report, and `review inspect` exits 0 for every report-content
    outcome. Raising on an unreadable path would convert that defined outcome
    into an operational error.

    This case needs a REAL initialised cohort. Pointing at an empty directory
    would exit non-zero on the missing `state.json` before the report path is
    ever read — green for a reason that has nothing to do with `--report`.
    """
    name = "loop-cohort: missing --report classifies invalid (exit 0)"
    with tempfile.TemporaryDirectory() as td:
        spec_dir = Path(td) / "spec"
        spec_dir.mkdir()
        run_id = "00000000-1111-2222-3333-444444444444"
        rc, out, err = run(LOOP_COHORT, "init", str(spec_dir), "--run-id", run_id)
        if rc != 0 or not (spec_dir / "state.json").is_file():
            fail(name, f"could not initialise a cohort fixture (rc={rc} err={err!r})")
            return

        rc, out, err = run(
            LOOP_COHORT, "review", "inspect", str(spec_dir),
            "--report", "no-such-report.md", "--json",
            cwd=Path(td),
        )
        combined = f"{out}\n{err}"
        if "Traceback" in combined:
            fail(name, f"raised a traceback instead of classifying:\n{combined}")
        elif rc != 0:
            fail(name, f"expected exit 0 for a report-content outcome, got {rc}: {combined!r}")
        else:
            try:
                classification = json.loads(out)["classification"]
            except (ValueError, KeyError) as exc:
                fail(name, f"could not read classification from {out!r} ({exc})")
                return
            if classification != "invalid":
                fail(name, f"expected classification 'invalid', got {classification!r}")
            else:
                ok(name)


def test_report_sites_route_through_resolver() -> None:
    """Both `--report` call sites go through `_resolved_report` — a STRUCTURAL
    check, deliberately, because there is no behavioural one to make.

    `_resolved_report` only calls `.resolve()`. `_classify_report` returns
    `invalid` for an unreadable path whether or not it was resolved, and a
    readable report reads the same through either form — so reverting the
    helper changes no observable output. Verified: with both call sites
    reverted to bare `Path(args.report)`, every behavioural case in this file
    still passed.

    The helper exists for scanner legibility, not behaviour, so the honest
    guard is that the call sites still use it. Do not replace this with a
    behavioural assertion that appears stronger; it would be green either way.
    """
    name = "loop-cohort: both --report sites route through _resolved_report"
    src = LOOP_COHORT.read_text(encoding="utf-8")
    # Match assignment form only: `_resolved_report`'s own docstring names
    # `Path(args.report)` in prose, and a substring count would score that as
    # a live call site.
    routed = src.count("= _resolved_report(args.report)")
    bare = src.count("= Path(args.report)")
    if routed != 2:
        fail(name, f"expected 2 routed call sites, found {routed}")
    elif bare:
        fail(name, f"found {bare} bare Path(args.report) call site(s) — should be 0")
    else:
        ok(name)


# ---------------------------------------------------------------------------
# AC5 — every currently-valid invocation is unchanged
# ---------------------------------------------------------------------------

def _repo_root() -> Path:
    """The repository root — parents[5], NOT parents[4].

    parents[4] is `<repo>/packs`, which both linters also happily accept, so
    the off-by-one produced green parity tests that were not exercising the
    repo at all.
    """
    root = Path(__file__).resolve().parents[5]
    if not (root / "docs" / "specs").is_dir():
        raise SystemExit(f"repo root not found at {root} — check the parents[] depth")
    return root


def test_valid_root_unchanged() -> None:
    """An explicit, valid --root behaves exactly as before the validator.

    Baseline is this repository, which both linters are expected to accept.
    """
    root = _repo_root()
    for label, script in ROOT_SCRIPTS:
        name = f"{label}: valid explicit --root is accepted"
        rc, out, err = run(script, "--root", str(root))
        combined = f"{out}\n{err}"
        # AC5 promises "same exit codes". Asserting rc is what makes this a
        # parity test — without it the case passes against an implementation
        # whose exit codes changed entirely.
        if rc != 0:
            fail(name, f"expected exit 0 on a valid invocation, got {rc}: {combined!r}")
        elif "Traceback" in combined:
            fail(name, f"raised a traceback on a valid root:\n{combined}")
        elif "is not a directory" in combined or "does not exist" in combined:
            fail(name, f"validator rejected a legitimate root: {combined!r}")
        else:
            ok(name)


def test_omitted_root_unchanged() -> None:
    """With --root omitted, the script still falls back to its repo-root discovery."""
    root = _repo_root()
    for label, script in ROOT_SCRIPTS:
        name = f"{label}: omitted --root still resolves via fallback"
        rc, out, err = run(script, cwd=root)
        combined = f"{out}\n{err}"
        # AC5 promises "same exit codes". Asserting rc is what makes this a
        # parity test — without it the case passes against an implementation
        # whose exit codes changed entirely.
        if rc != 0:
            fail(name, f"expected exit 0 on a valid invocation, got {rc}: {combined!r}")
        elif "Traceback" in combined:
            fail(name, f"raised a traceback with --root omitted:\n{combined}")
        elif "is not a directory" in combined or "does not exist" in combined:
            fail(name, f"fallback root was rejected by the validator: {combined!r}")
        else:
            ok(name)


def test_relative_root_unchanged() -> None:
    """A relative --root resolves against cwd and is accepted.

    The validator normalises with resolve(); this is the case that would break
    if it instead compared the raw, unresolved string.
    """
    root = _repo_root()
    for label, script in ROOT_SCRIPTS:
        name = f"{label}: relative --root is resolved and accepted"
        rc, out, err = run(script, "--root", ".", cwd=root)
        combined = f"{out}\n{err}"
        # AC5 promises "same exit codes". Asserting rc is what makes this a
        # parity test — without it the case passes against an implementation
        # whose exit codes changed entirely.
        if rc != 0:
            fail(name, f"expected exit 0 on a valid invocation, got {rc}: {combined!r}")
        elif "Traceback" in combined:
            fail(name, f"raised a traceback on a relative root:\n{combined}")
        elif "is not a directory" in combined or "does not exist" in combined:
            fail(name, f"validator rejected a relative root: {combined!r}")
        else:
            ok(name)


def main() -> int:
    test_nonexistent_root_exits_nonzero_with_diagnostic()
    test_file_valued_root_exits_nonzero()
    test_missing_report_classifies_invalid_not_crash()
    test_report_sites_route_through_resolver()
    test_valid_root_unchanged()
    test_omitted_root_unchanged()
    test_relative_root_unchanged()

    total = ran
    passed = total - len(failures)
    print(f"\n{passed}/{total} passed")
    if failures:
        print("Failed:", ", ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
