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
    # Asserted as a *set of steps*, not a count. A bare count tells you a step
    # was dropped but not which, and a floor is weaker still — remove any other
    # step and the total stays put. Each entry is (cwd suffix, a token that must
    # appear in the command).
    #
    # `packages/credbroker` is here because the cross-platform process-tree kill
    # lives in that suite; the `taskkill` arm is only verified once this run is
    # green (jira-check-sso-auto-login AC26).
    #
    # The dependency probe is here because both SSO trios `importorskip`
    # `credbroker` at module scope and the step runner judges by return code
    # alone — without it, a machine missing the dependency skips both suites
    # and the step reports pass.
    #
    # Pack tests live outside the runtime payload (ADR-0071), so the SSO cwds
    # are the pack's test tree rather than the skill's `scripts/`.
    expected = {
        ("", "catalogue"),
        ("", "import credbroker, httpx"),
        (str(Path("packages") / "agentbundle"), "test_install_converters_user_scope.py"),
        (str(Path("packages") / "agentbundle"), "test_shared_libs_projection.py"),
        (str(Path("packages") / "agentbundle"), "test_self_host_recipe_config.py"),
        (str(Path("packages") / "agentbundle"), "test_self_host_fixture_guard.py"),
        (str(Path("packages") / "agentbundle"), "test_user_libs_projection.py"),
        (str(Path("packages") / "agentbundle"), "test_credential_brokers_pack_install.py"),
        (str(Path("packages") / "credbroker"), "pytest"),
        (str(Path("tests") / "skills" / "jira"), "test_check_sso_login.py"),
        (str(Path("tests") / "skills" / "confluence-crawler"), "test_sso_config.py"),
    }
    observed = [(str(cwd), " ".join(str(part) for part in cmd)) for cmd, cwd in calls]
    for cwd_suffix, token in sorted(expected):
        assert any(
            cwd.endswith(cwd_suffix) and token in command for cwd, command in observed
        ), f"parity step missing: {token} in a cwd ending {cwd_suffix!r}"


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
