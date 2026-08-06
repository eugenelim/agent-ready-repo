"""Unit tests for catalogue_tooling/self_host_windows.py."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest
from agentbundle.catalogue_tooling.self_host_windows import run_windows_compat


@dataclass
class FakeResult:
    returncode: int


@pytest.fixture()
def fake_root(tmp_path: Path) -> Path:
    """Minimal directory structure run_windows_compat expects."""
    (tmp_path / "packages" / "agentbundle").mkdir(parents=True)
    (tmp_path / "packages" / "credbroker").mkdir(parents=True)
    # Pack tests live outside the runtime payload (ADR-0071), so the SSO steps'
    # cwds are the pack's test tree, not the skill's scripts/.
    (tmp_path / "packs" / "atlassian" / "tests" / "skills" / "jira").mkdir(parents=True)
    (
        tmp_path / "packs" / "atlassian" / "tests" / "skills" / "confluence-crawler"
    ).mkdir(parents=True)
    (tmp_path / "tools" / "hooks").mkdir(parents=True)
    return tmp_path


def test_all_steps_pass_returns_zero(fake_root: Path) -> None:
    calls: list = []

    def _capture(cmd, cwd):  # noqa: ANN001
        calls.append((cmd, cwd))
        return FakeResult(0)

    with patch(
        "agentbundle.catalogue_tooling.self_host_windows.subprocess.run",
        side_effect=_capture,
    ):
        rc = run_windows_compat(fake_root)
    assert rc == 0
    assert len(calls) == 16, f"Expected 16 steps, got {len(calls)}"
    # The SSO trios importorskip("credbroker") at module scope and _step
    # judges by return code alone, so the probe is what stops a missing
    # dependency from skipping both suites and reporting pass. Pin it by
    # shape, not only by the count above.
    assert any(
        cmd[1:] == ["-c", "import credbroker, httpx"] for cmd, _ in calls
    ), "the atlassian SSO dependency probe must run"
    # Likewise named rather than left to the count: credbroker's suite is here
    # because the cross-platform process-tree kill lives in it — the `taskkill`
    # arm is only verified once this run is green (jira-check-sso-auto-login
    # AC26).
    cwds = {str(cwd) for _cmd, cwd in calls}
    assert any(cwd.endswith(str(Path("packages") / "credbroker")) for cwd in cwds), (
        "the credbroker suite must run on the Windows parity runner"
    )


def test_stops_on_first_failure(fake_root: Path) -> None:
    call_count = 0

    def _fake_run(cmd, cwd):  # noqa: ANN001
        nonlocal call_count
        call_count += 1
        # Fail on the second call
        return FakeResult(0 if call_count < 2 else 1)

    with patch(
        "agentbundle.catalogue_tooling.self_host_windows.subprocess.run",
        side_effect=_fake_run,
    ):
        rc = run_windows_compat(fake_root)

    assert rc == 1
    assert call_count == 2, "Should stop immediately after the first failure"


def test_first_step_is_catalogue_build(fake_root: Path) -> None:
    calls: list = []

    def _capture(cmd, cwd):  # noqa: ANN001
        calls.append((cmd, cwd))
        return FakeResult(0)

    with patch(
        "agentbundle.catalogue_tooling.self_host_windows.subprocess.run",
        side_effect=_capture,
    ):
        run_windows_compat(fake_root)

    first_cmd, first_cwd = calls[0]
    assert first_cmd == [
        sys.executable, "-m", "agentbundle", "catalogue", "build",
        "--root", str(fake_root),
    ]
    assert first_cwd == fake_root


def test_second_step_is_self_host_check_without_windows(fake_root: Path) -> None:
    """Self-host --check must NOT carry --windows (no infinite recursion)."""
    calls: list = []

    def _capture(cmd, cwd):  # noqa: ANN001
        calls.append((cmd, cwd))
        return FakeResult(0)

    with patch(
        "agentbundle.catalogue_tooling.self_host_windows.subprocess.run",
        side_effect=_capture,
    ):
        run_windows_compat(fake_root)

    _, second_cmd = calls[0][0], calls[1][0]
    assert "--windows" not in second_cmd
    assert "--check" in second_cmd
    assert "self-host" in second_cmd


def test_uses_sys_executable_not_bare_python(fake_root: Path) -> None:
    calls: list = []

    def _capture(cmd, cwd):  # noqa: ANN001
        calls.append(cmd)
        return FakeResult(0)

    with patch(
        "agentbundle.catalogue_tooling.self_host_windows.subprocess.run",
        side_effect=_capture,
    ):
        run_windows_compat(fake_root)

    for cmd in calls:
        assert cmd[0] == sys.executable, (
            f"Expected sys.executable ({sys.executable!r}), got {cmd[0]!r} in {cmd}"
        )


def test_atlassian_steps_use_correct_cwd(fake_root: Path) -> None:
    calls: list = []

    def _capture(cmd, cwd):  # noqa: ANN001
        calls.append((cmd, cwd))
        return FakeResult(0)

    with patch(
        "agentbundle.catalogue_tooling.self_host_windows.subprocess.run",
        side_effect=_capture,
    ):
        run_windows_compat(fake_root)

    cwds = [str(cwd) for _, cwd in calls]
    jira_cwd = str(fake_root / "packs" / "atlassian" / "tests" / "skills" / "jira")
    confluence_cwd = str(
        fake_root / "packs" / "atlassian" / "tests" / "skills" / "confluence-crawler"
    )
    assert jira_cwd in cwds, "jira test tree must be a step cwd"
    assert confluence_cwd in cwds, "confluence-crawler test tree must be a step cwd"


def test_windows_flag_requires_check_via_cli() -> None:
    """--windows without --check exits 2 with a clear message."""
    from agentbundle.cli import main

    rc = main(["catalogue", "self-host", "--windows", "--root", "."])
    assert rc == 2
