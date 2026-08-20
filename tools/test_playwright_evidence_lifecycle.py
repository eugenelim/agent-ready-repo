"""Falsification tests for bounded Playwright failure-evidence retention."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent / "repo"))
import frontend_runtime  # noqa: E402
import worktree_hygiene as hygiene  # noqa: E402


class EvidenceGit:
    """Model only the Git facts the evidence lifecycle must establish."""

    def __init__(
        self,
        root: Path,
        *,
        worktrees: list[Path] | None = None,
        replace_before_status: Path | None = None,
    ) -> None:
        self.root = root
        self.worktrees = worktrees or [root]
        self.replace_before_status = replace_before_status
        self.calls: list[list[str]] = []

    def __call__(
        self,
        argv: list[str],
        *,
        input: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del env
        self.calls.append(argv)
        if "worktree" in argv:
            output = "".join(
                f"worktree {worktree}\0HEAD abc\0branch refs/heads/test\0\0"
                for worktree in self.worktrees
            )
            return subprocess.CompletedProcess(argv, 0, output, "")
        if "rev-parse" in argv:
            return subprocess.CompletedProcess(
                argv, 0, str(self.root / ".git") + "\n", ""
            )
        paths = [Path(value) for value in (input or "").split("\0") if value]
        if "ls-files" in argv:
            paths = [Path(value) for value in argv[argv.index("--") + 1 :]]
        ignored = [
            path
            for path in paths
            if str(path).startswith("web/test-results")
            or str(path).startswith("web/playwright-report")
            or str(path).startswith("web/.playwright-failure-evidence")
        ]
        if "check-ignore" in argv:
            if self.replace_before_status is not None:
                target = self.replace_before_status
                self.replace_before_status = None
                shutil.rmtree(target)
                target.symlink_to(
                    self.root
                    / "web"
                    / hygiene.PLAYWRIGHT_EVIDENCE_DIRECTORY
                    / "failed-newest",
                    target_is_directory=True,
                )
            output = "\0".join(map(str, ignored))
            return subprocess.CompletedProcess(
                argv,
                0 if output else 1,
                output + ("\0" if output else ""),
                "",
            )
        return subprocess.CompletedProcess(argv, 0, "", "")


@pytest.fixture
def evidence_root() -> Path:
    with tempfile.TemporaryDirectory() as directory:
        # Canonicalise once here, not per assertion: on macOS /var is a symlink
        # to /private/var, and the module under test resolves the paths it
        # reports, so an unresolved fixture root never matches its receipt.
        root = Path(directory).resolve() / "worktree"
        (root / ".git").mkdir(parents=True)
        (root / "web" / "test-results").mkdir(parents=True)
        (root / "web" / "test-results" / "trace.zip").write_text(
            "failure", encoding="utf-8"
        )
        yield root


def _failed_run(
    root: Path, name: str, age_seconds: int, *, pinned: bool = False
) -> Path:
    run = root / "web" / hygiene.PLAYWRIGHT_EVIDENCE_DIRECTORY / name
    run.mkdir(parents=True)
    (run / "trace.zip").write_text(name, encoding="utf-8")
    if pinned:
        (run / hygiene.PLAYWRIGHT_EVIDENCE_PIN).write_text("", encoding="utf-8")
    timestamp = time.time() - age_seconds
    os.utime(run, (timestamp, timestamp))
    return run


def test_failed_gate_keeps_live_ci_output_and_archives_newest_failure(
    evidence_root: Path,
) -> None:
    git = EvidenceGit(evidence_root)

    result = hygiene.manage_playwright_failure_evidence(
        evidence_root,
        gate_returncode=1,
        max_age_seconds=60,
        runner=git,
    )

    archive = evidence_root / "web" / hygiene.PLAYWRIGHT_EVIDENCE_DIRECTORY
    retained = list(archive.iterdir())
    assert result.archived == 1
    assert any(
        line.startswith(f"archived {evidence_root / 'web' / 'test-results'}:")
        and " bytes to " in line
        for line in result.receipt
    )
    assert (evidence_root / "web" / "test-results" / "trace.zip").exists()
    assert len(retained) == 1
    assert (retained[0] / "trace.zip").read_text(encoding="utf-8") == "failure"


def test_success_removes_live_run_artifacts_but_keeps_retained_failure(
    evidence_root: Path,
) -> None:
    git = EvidenceGit(evidence_root)
    retained = _failed_run(evidence_root, "failed-old", 10)
    report = evidence_root / "web" / "playwright-report"
    report.mkdir()
    (report / "index.html").write_text("success", encoding="utf-8")

    result = hygiene.manage_playwright_failure_evidence(
        evidence_root,
        gate_returncode=0,
        max_age_seconds=60,
        runner=git,
    )

    assert result.cleaned == 2
    assert f"cleaned {evidence_root / 'web' / 'test-results'}:" in "\n".join(
        result.receipt
    )
    assert f"cleaned {report}:" in "\n".join(result.receipt)
    assert not (evidence_root / "web" / "test-results").exists()
    assert not report.exists()
    assert retained.exists()


def test_newest_failed_run_survives_the_age_budget(evidence_root: Path) -> None:
    git = EvidenceGit(evidence_root)
    oldest = _failed_run(evidence_root, "failed-oldest", 120)
    newest = _failed_run(evidence_root, "failed-newest", 61)

    hygiene.manage_playwright_failure_evidence(
        evidence_root,
        gate_returncode=0,
        max_age_seconds=60,
        runner=git,
    )

    assert not oldest.exists()
    assert newest.exists()


def test_pinned_failed_run_survives_the_age_budget(evidence_root: Path) -> None:
    git = EvidenceGit(evidence_root)
    pinned = _failed_run(evidence_root, "failed-pinned", 120, pinned=True)
    newest = _failed_run(evidence_root, "failed-newest", 61)

    hygiene.manage_playwright_failure_evidence(
        evidence_root,
        gate_returncode=0,
        max_age_seconds=60,
        runner=git,
    )

    assert pinned.exists()
    assert newest.exists()


def test_refuses_deletion_when_selected_entry_becomes_a_symlink(
    evidence_root: Path,
) -> None:
    expired = _failed_run(evidence_root, "failed-expired", 120)
    newest = _failed_run(evidence_root, "failed-newest", 61)
    shutil.rmtree(evidence_root / "web" / "test-results")
    git = EvidenceGit(evidence_root, replace_before_status=expired)

    result = hygiene.manage_playwright_failure_evidence(
        evidence_root,
        gate_returncode=0,
        max_age_seconds=60,
        runner=git,
    )

    assert expired.is_symlink()
    assert newest.exists()
    # The prefix, not the reason text: the reason comes from
    # `_candidate_safety_reason`, which `clean` owns and shares. Pinning its
    # exact wording here would couple this test to that message. The prefix
    # still discriminates -- with the pre-delete re-assertion removed the entry
    # is deleted and no `aborted` line is emitted at all.
    assert any(
        line.startswith(f"aborted {expired}: safety changed:")
        for line in result.receipt
    )


def test_git_status_work_is_bounded_for_retained_archive_entries(
    evidence_root: Path,
) -> None:
    shutil.rmtree(evidence_root / "web" / "test-results")
    git = EvidenceGit(evidence_root)

    for count in (6, 12):
        for index in range(count):
            _failed_run(evidence_root, f"failed-old-{count}-{index}", 120)
        _failed_run(evidence_root, f"failed-newest-{count}", 61)
        git.calls.clear()

        hygiene.manage_playwright_failure_evidence(
            evidence_root,
            gate_returncode=0,
            max_age_seconds=60,
            runner=git,
        )

        assert len(git.calls) == 4


def test_unregistered_invocation_refuses_without_touching_peer_worktree(
    evidence_root: Path,
) -> None:
    peer = evidence_root.parent / "peer"
    (peer / ".git").mkdir(parents=True)
    target = peer / "web" / "test-results"
    target.mkdir(parents=True)
    (target / "trace.zip").write_text("peer", encoding="utf-8")
    git = EvidenceGit(evidence_root, worktrees=[peer])

    result = hygiene.manage_playwright_failure_evidence(
        evidence_root,
        gate_returncode=0,
        max_age_seconds=60,
        runner=git,
    )

    assert result.refused
    assert target.exists()


def test_age_budget_is_configurable_without_a_ci_switch() -> None:
    assert frontend_runtime.playwright_evidence_max_age({}) == 7 * 24 * 60 * 60
    assert frontend_runtime.playwright_evidence_max_age(
        {frontend_runtime.PLAYWRIGHT_EVIDENCE_MAX_AGE_ENV: "60"}
    ) == 60
    with pytest.raises(frontend_runtime.FrontendRuntimeError, match="whole number"):
        frontend_runtime.playwright_evidence_max_age(
            {frontend_runtime.PLAYWRIGHT_EVIDENCE_MAX_AGE_ENV: "one"}
        )
    with pytest.raises(frontend_runtime.FrontendRuntimeError, match="not be negative"):
        frontend_runtime.playwright_evidence_max_age(
            {frontend_runtime.PLAYWRIGHT_EVIDENCE_MAX_AGE_ENV: "-1"}
        )


def test_playwright_failure_diagnostics_remain_enabled() -> None:
    config = (Path(__file__).resolve().parent.parent / "web" / "playwright.config.ts")
    source = config.read_text(encoding="utf-8")

    assert "trace: 'retain-on-failure'" in source
    assert "screenshot: 'only-on-failure'" in source


def test_gate_wrapper_applies_lifecycle_after_the_pinned_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    common_dir = tmp_path / "common"
    common_dir.mkdir()
    observed: dict[str, object] = {}

    class Lease:
        port = 5432

        def release(self) -> None:
            return None

    def manage(repository: Path, **kwargs: object) -> hygiene.PlaywrightEvidenceResult:
        observed["repository"] = repository
        observed.update(kwargs)
        return hygiene.PlaywrightEvidenceResult(receipt=("cleaned test evidence",))

    monkeypatch.setattr(
        frontend_runtime.worktree_hygiene,
        "manage_playwright_failure_evidence",
        manage,
    )
    monkeypatch.setattr(frontend_runtime, "lease_preview_port", lambda *_: Lease())
    monkeypatch.setattr(frontend_runtime, "_run_child", lambda *_: 0)

    assert frontend_runtime.run_gate(
        environ={frontend_runtime.PLAYWRIGHT_EVIDENCE_MAX_AGE_ENV: "60"},
        repo_root=tmp_path,
        common_dir=common_dir,
        gate_command=(sys.executable, "-c", "raise SystemExit(0)"),
    ) == 0
    assert observed == {
        "repository": tmp_path,
        "gate_returncode": 0,
        "max_age_seconds": 60,
    }
    assert "cleaned test evidence" in capsys.readouterr().out
