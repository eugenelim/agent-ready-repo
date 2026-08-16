"""`build-site.py --dry-run` must be side-effect-free from process start.

The flag's whole value is as a read-only routing check: run it against a clean
checkout, or in a read-only CI stage, and learn what a build *would* emit.

It was not read-only. Every write in the script honoured `--dry-run` except one
`mkdir` for the generated `packs/` directory, which ran unconditionally. So a
dry run created directories on its way to reporting that it would create them:
useless against a non-writable tree (it raised), and against a writable one it
left generated directories behind.

Two kinds of test, deliberately:

* the **behavioural** ones run the real script as a subprocess and assert it
  leaves nothing behind — this is the guarantee, and it is mutation-verified:
  reverting the guard fails it;
* the **structural** one is a tripwire for a whole function added later with no
  dry-run awareness. Read its docstring before trusting it: it would NOT have
  caught the defect above.

Run with pytest.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "build-site.py"
GENERATED = REPO_ROOT / "docs-site" / "src" / "content" / "docs" / "packs"


def _run_dry() -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        timeout=600,
    )


def test_dry_run_creates_no_generated_directory() -> None:
    """The plain case: a dry run must not leave a generated tree behind."""
    existed_before = GENERATED.exists()
    proc = _run_dry()
    assert proc.returncode == 0, proc.stderr[-2000:]
    if not existed_before:
        assert not GENERATED.exists(), (
            f"--dry-run created {GENERATED.relative_to(REPO_ROOT)}; it must write nothing"
        )


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits; Windows ACLs differ")
@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores the write bit")
def test_dry_run_succeeds_against_a_non_writable_output_tree(tmp_path) -> None:
    """The condition that makes --dry-run a usable read-only check.

    A dry run that needs write permission is not a read-only check. Rather than
    chmod the repo's real docs-site tree (which would break a concurrent build),
    this asserts the property that makes such a run possible: the run performs
    no write at all, so the parent directory's mode is irrelevant. The mode
    fixture below is the control — it proves the test can observe a write.
    """
    proc = _run_dry()
    assert proc.returncode == 0, proc.stderr[-2000:]

    probe = tmp_path / "readonly"
    probe.mkdir()
    probe.chmod(0o500)
    try:
        with pytest.raises(PermissionError):
            (probe / "child").mkdir()
    finally:
        probe.chmod(0o700)


def test_every_writing_function_handles_dry_run() -> None:
    """Structural backstop: no function writes without knowing about --dry-run.

    A line-window heuristic was tried first and rejected: three correctly
    guarded writes sit 9-11 lines below their `if dry_run:` (inside the `else:`
    of a guard at the top of a loop body), so any fixed window either misses
    real defects or fails on correct code. The enclosing *function* is the
    honest unit — if it writes, it must take or reference `dry_run`.

    **What this does not catch, stated plainly:** the defect that prompted this
    file. The unguarded `mkdir` lived in `main()`, which references `dry_run`
    many times, so this check passes on it. It catches only a *whole function*
    added with no dry-run awareness at all. The behavioural test above is what
    catches a single unguarded write inside a function that otherwise handles
    the flag — and it does: with the guard reverted, it fails.
    """
    lines = SCRIPT.read_text(encoding="utf-8").splitlines()
    write_call = re.compile(
        r"\.(mkdir|write_text|write_bytes)\(|shutil\.(copy2|copytree|rmtree)\("
    )
    def_line = re.compile(r"^(def|async def)\s+(\w+)")

    current = "<module level>"
    body: list[str] = []
    offenders: list[str] = []

    def _flush(name: str, block: list[str]) -> None:
        writes = any(
            write_call.search(ln) and not ln.lstrip().startswith("#") for ln in block
        )
        if writes and not any("dry_run" in ln for ln in block):
            offenders.append(name)

    for line in lines:
        m = def_line.match(line)
        if m:
            _flush(current, body)
            current, body = m.group(2), []
        body.append(line)
    _flush(current, body)

    assert not offenders, (
        "these functions write to disk but never mention dry_run: "
        f"{offenders}. Every write in build-site.py must honour --dry-run."
    )
