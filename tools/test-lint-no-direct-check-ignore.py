#!/usr/bin/env python3
"""Self-test for `tools/lint-no-direct-check-ignore.py`.

T3 of `docs/specs/lint-performance-p0`. The gate under test is a **drift guard**,
not a proof: an AST allowlist cannot see `"check-" "ignore"` assembled at
runtime, `shlex.split`, or starred args. The strong property lives in
`tools/test-lint-boundary-structural.py`, which counts actual processes. What
this gate buys is that the obvious way to reintroduce a per-path probe fails
loudly in CI.

Two design points are asserted here because both are easy to get wrong in a way
that leaves the gate looking green while enforcing nothing:

* **`check-ignore` is matched anywhere in an argv sequence**, not only at
  position 1 — `["git", "-C", root, "check-ignore", …]` is the most idiomatic way
  to write it and would otherwise sail through.

* **Exemptions are an explicit file allowlist, never a filename pattern.** In
  this repository `tools/test-*.py` files *are* CI gates, and one of them is a
  file this very spec changes, so a pattern exemption would carve out exactly the
  class being policed. The gate also fails on a file it cannot read or parse
  rather than skipping it, since a silent skip is a self-inflicted bypass.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "tools" / "lint-no-direct-check-ignore.py"
if not GATE.is_file():
    raise SystemExit(f"gate not found at {GATE}")

_spec = importlib.util.spec_from_file_location("lint_no_direct_check_ignore", GATE)
M = importlib.util.module_from_spec(_spec)
sys.modules["lint_no_direct_check_ignore"] = M
_spec.loader.exec_module(M)

_FAILURES: list[str] = []
_CASES = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global _CASES
    _CASES += 1
    if not ok:
        _FAILURES.append(f"{name}: {detail}" if detail else name)


# Each shape a reviewer or a hurried author might reach for.
_OFFENDING = {
    "argv at position 1": '''
import subprocess
def probe(p):
    return subprocess.run(["git", "check-ignore", "-q", "--", str(p)])
''',
    "argv behind -C (not at position 1)": '''
import subprocess
def probe(root, p):
    return subprocess.run(["git", "-C", str(root), "check-ignore", "-q", str(p)])
''',
    "argv built through a variable": '''
import subprocess
def probe(p):
    argv = ["git", "check-ignore", "-q", str(p)]
    return subprocess.run(argv)
''',
    "shell string": '''
import subprocess
def probe(p):
    return subprocess.run(f"git check-ignore -q {p}", shell=True)
''',
    "os.system": '''
import os
def probe(p):
    return os.system(f"git check-ignore -q {p}")
''',
    "os.popen": '''
import os
def probe(p):
    return os.popen(f"git check-ignore -q {p}").read()
''',
    "Popen": '''
import subprocess
def probe(p):
    return subprocess.Popen(["git", "check-ignore", str(p)])
''',
}

_CLEAN = '''
import lint_git_ignore
def probe(root, paths):
    return lint_git_ignore.git_ignored_paths(
        root, paths,
        missing_git_policy=lint_git_ignore.MissingGitPolicy.FAIL_OPEN,
        timeout=30.0,
    )
'''


def main() -> int:
    # ---- each offending shape is detected --------------------------------
    for label, source in _OFFENDING.items():
        hits = M.scan_source("fake/offender.py", source)
        check(f"detects: {label}", bool(hits), f"no hit for:\n{source}")

    # ---- the blessed call is not flagged ---------------------------------
    check("does not flag the approved helper call",
          not M.scan_source("fake/caller.py", _CLEAN),
          repr(M.scan_source("fake/caller.py", _CLEAN)))

    # ---- an unparseable or undecodable file FAILS, never skipped ---------
    hits = M.scan_source("fake/broken.py", "def broken(:\n")
    check("an unparseable file is a finding, not a skip", bool(hits), repr(hits))
    check("the unparseable finding names the file",
          any("broken.py" in h for h in hits), repr(hits))

    # ---- the real tree passes -------------------------------------------
    result = M.audit(ROOT)
    check("the repository passes the gate", not result.findings,
          "\n".join(result.findings[:6]))

    # ---- the approved helper is IN the scanned set, not merely exempt ----
    check("the approved helper was actually scanned",
          any(p.name == "lint_git_ignore.py" for p in result.scanned),
          "the helper is exempt but never inspected — 'exempt' must not mean "
          "'never looked at'")
    check("the approved helper is on the allowlist",
          "tools/lint_git_ignore.py" in M.ALLOWLIST)

    # ---- allowlist entries are real files, each with a reason -----------
    for rel, reason in M.ALLOWLIST.items():
        check(f"allowlist entry exists: {rel}", (ROOT / rel).exists(), rel)
        check(f"allowlist entry has a reason: {rel}", bool(reason.strip()), rel)
    check("the pack-evals self-test is allowlisted",
          "tools/test-run-pack-evals.py" in M.ALLOWLIST,
          "it holds a real single-path check-ignore call asserting a "
          "genuine .gitignore fact")

    # ---- exemption is a file list, not a filename pattern ---------------
    # A `test-*` pattern would exempt this repo's actual CI gates, one of which
    # this spec changes. Assert non-allowlisted test files are still scanned.
    scanned_rel = {str(p.relative_to(ROOT)) for p in result.scanned}
    sample = "tools/test-lint-boundary-structural.py"
    check("a non-allowlisted tools/test-*.py file is still scanned",
          sample in scanned_rel,
          f"{sample} was skipped — exemption looks pattern-based")

    # ---- the scanned set is tracked files, and meets a floor ------------
    check("the scanned set meets the recorded floor",
          len(result.scanned) >= M.SCANNED_FLOOR,
          f"{len(result.scanned)} < floor {M.SCANNED_FLOOR}")
    check("the scan is not vacuous", len(result.scanned) > 100,
          str(len(result.scanned)))

    # ---- non-Python surface is covered or explicitly recorded -----------
    check("the non-Python surface is scanned too",
          any(p.suffix in {".sh", ""} or p.name == "Makefile"
              for p in result.scanned)
          or M.NON_PYTHON_DISPOSITION,
          "neither scanned nor dispositioned")

    # ---- end to end: a planted offender fails the CLI -------------------
    with tempfile.TemporaryDirectory(prefix="check-ignore-gate-") as td:
        fake = Path(td) / "repo"
        (fake / "tools").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", "."], cwd=str(fake),
                       capture_output=True, check=True)
        (fake / "tools" / "lint-planted.py").write_text(
            _OFFENDING["argv behind -C (not at position 1)"], encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=str(fake),
                       capture_output=True, check=True)
        proc = subprocess.run(
            [sys.executable, str(GATE), "--root", str(fake)],
            capture_output=True, text=True, check=False,
        )
        check("CLI exits non-zero on a planted offender", proc.returncode != 0,
              f"rc={proc.returncode}\n{proc.stdout}\n{proc.stderr}")
        check("CLI names the planted file",
              "lint-planted.py" in proc.stdout + proc.stderr,
              proc.stdout + proc.stderr)

    # ---- CLI on the real tree ------------------------------------------
    proc = subprocess.run([sys.executable, str(GATE)], cwd=str(ROOT),
                          capture_output=True, text=True, check=False)
    check("CLI exits 0 on the repository", proc.returncode == 0,
          f"rc={proc.returncode}\n{proc.stdout[-800:]}\n{proc.stderr[-800:]}")

    for f in _FAILURES:
        sys.stderr.write(f"FAIL {f}\n")
    if _FAILURES:
        sys.stderr.write(
            f"✖ no-direct-check-ignore: {len(_FAILURES)} of {_CASES} failed\n"
        )
        return 1
    sys.stderr.write(f"ok — {_CASES} cases passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
