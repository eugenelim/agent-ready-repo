"""T5/T6 (pure): the upgrade recap verdict and the shared drift counter.

The recap honestly distinguishes a version change from a same-version re-apply
(install-state-visibility AC9-AC11), and the drift counter underpins both the
``--check-drift`` column and the upgrade upfront notice (AC6/AC12).
"""

from __future__ import annotations

from agentbundle.commands._common import count_drifted_files
from agentbundle.commands.upgrade import _format_recap
from agentbundle.config import PackState
from agentbundle.safety import sha256_bytes


def test_recap_version_change_is_upgraded():
    assert (
        _format_recap("core", "repo", "0.1.0", "0.2.0",
                      already_current=False, companion_count=0)
        == "upgraded: core @ repo 0.1.0 -> 0.2.0"
    )


def test_recap_same_version_clean_is_reapplied_already_current():
    # The exact bug AC10 fixes: never `upgraded: X -> X`.
    out = _format_recap("core", "repo", "0.2.0", "0.2.0",
                        already_current=True, companion_count=0)
    assert out == "re-applied: core @ repo 0.2.0 (already current)"
    assert "->" not in out


def test_recap_same_version_with_companions_names_count():
    out = _format_recap("architect", "user", "0.9.0", "0.9.0",
                        already_current=True, companion_count=3)
    assert out == (
        "re-applied: architect @ user 0.9.0 — "
        "3 file(s) had local edits, kept as .upstream companions"
    )


def test_count_drifted_files_clean_edited_absent(tmp_path):
    sha = sha256_bytes(b"orig\n")
    (tmp_path / "x.md").write_bytes(b"orig\n")
    ps = PackState(
        installed_version="1.0",
        files={"x.md": {"sha": sha}, "gone.md": {"sha": "deadbeef"}},
    )
    # x.md present & matching, gone.md absent → 0 drift.
    assert count_drifted_files(ps, tmp_path) == 0
    # Edit x.md → 1 drift; gone.md still absent (not drift).
    (tmp_path / "x.md").write_bytes(b"edited\n")
    assert count_drifted_files(ps, tmp_path) == 1
