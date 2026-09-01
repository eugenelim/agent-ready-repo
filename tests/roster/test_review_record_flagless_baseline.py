"""The omitted-flag path still matches the baseline captured before the writer changed.

The baseline is the only oracle for "a caller who omits `--operation-id` sees no
change", and it is only an oracle because it was committed before
`cmd_review_record` was touched. Without a consumer it was a one-time eyeball; this
runs it.

It lives here rather than beside the work-loop suite because a pack test may not
read above its own pack and the artifact sits under `docs/specs/`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "docs/specs/review-record-idempotency/notes/capture-flagless-baseline.py"
BASELINE = SCRIPT.parent / "flagless-baseline.json"


def test_the_baseline_artifact_is_committed() -> None:
    assert BASELINE.is_file(), "the flagless baseline oracle is missing"


def test_the_flagless_forms_still_match_the_baseline() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--verify"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, (
        "omitting --operation-id changed observable behaviour:\n"
        f"{result.stdout}\n{result.stderr}"
    )


def test_verify_is_the_default_so_the_oracle_cannot_be_overwritten() -> None:
    """Assert the mode, not a byte compare.

    Comparing bytes cannot catch the mutation it names: a capture-by-default
    build re-renders a file byte-identical to the committed one whenever the
    writer matches, so the assertion would hold precisely when it needed to fail.
    The observable difference is which mode ran.
    """
    result = subprocess.run([sys.executable, str(SCRIPT)], cwd=ROOT,
                            capture_output=True, text=True, check=False)
    assert "matches the committed baseline" in result.stdout, result.stdout
    assert "captured" not in result.stdout, (
        "the default mode wrote the oracle instead of verifying it")
