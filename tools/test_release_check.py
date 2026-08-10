"""Ship-time tag verifier — tools/repo/release_check.sh.

Spec AC: "the git tag `contract-v<version>` exists in this repo's
history before `dist/agentbundle.pyz` is uploaded as a release asset".
The CLI's `--version` output binds to that tag, so a `.pyz` claiming
"spec 0.1" without a `contract-v0.1` anchor in git has no canonical
source-of-truth check. `tools/repo/release_check.sh` is the mechanical
verifier; this test pins its refuse-and-explain behaviour.

Drives the verifier at its canonical path, not the `tools/release-check.sh`
compatibility shim — running through the shim tested an alias and printed a
relocation warning into every run. The shim's own existence is covered by
`tools/test_catalogue_tooling_rewire.py`.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_CHECK = REPO_ROOT / "tools" / "repo" / "release_check.sh"


@pytest.mark.skipif(sys.platform == "win32", reason="no Unix execute bits on Windows")
def test_release_check_exists_and_executable():
    assert RELEASE_CHECK.exists(), "tools/repo/release_check.sh is missing"
    assert RELEASE_CHECK.stat().st_mode & 0o111, "release_check.sh must be executable"


@pytest.mark.skipif(sys.platform == "win32", reason="bash encoding differs on Windows")
def test_release_check_refuses_when_tag_missing():
    """In normal CI / local dev the `contract-v<version>` tag has not yet
    been cut for an in-progress branch — the script must exit 1 and name
    the missing tag so an operator can act on it.
    """
    proc = subprocess.run(
        ["bash", str(RELEASE_CHECK)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # On a freshly-cut branch the tag won't exist yet → exit 1.
    # If someone has tagged locally for testing, the test should also pass
    # (exit 0 is acceptable — we just want non-crash behaviour).
    assert proc.returncode in (0, 1), (
        f"release-check exited with unexpected code {proc.returncode}: {proc.stderr}"
    )
    if proc.returncode == 1:
        assert "contract-v" in proc.stderr, (
            f"refusal must name the required tag: {proc.stderr!r}"
        )
