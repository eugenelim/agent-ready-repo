"""SSO consumer-resolver contract (task T1).

``load_sso_cookies`` subprocess-invokes the ``sso-broker.py`` engine and returns
the on-disk jar path, proceeding only on exit-0-with-readable-path and failing
closed otherwise. The engine is faked here with a stub script returning canned
exit codes / stdout, plus monkeypatched ``subprocess.Popen`` for the branches a
real subprocess can't reach deterministically.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import credbroker
import pytest
from credbroker import _sso


def _install_fake_broker(home: Path, *, exit_code: int, stdout: str = "") -> Path:
    """Write a stub ``sso-broker.py`` under *home* that prints *stdout* and exits
    *exit_code* when run as ``python sso-broker.py get-cookies <profile>``."""
    bin_dir = home / ".agentbundle" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    broker = bin_dir / "sso-broker.py"
    broker.write_text(
        "import sys\n"
        f"sys.stdout.write({stdout!r})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    return broker


@pytest.fixture()
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point ``Path.home()`` (and thus the resolver's broker lookup) at tmp."""
    monkeypatch.setattr(_sso.Path, "home", staticmethod(lambda: tmp_path))
    return tmp_path


def test_exit0_readable_path_returns_path(fake_home: Path) -> None:
    jar = fake_home / "session.jar"
    jar.write_text("[]", encoding="utf-8")
    _install_fake_broker(fake_home, exit_code=0, stdout=f"{jar}\n")

    assert _sso.load_sso_cookies("corp") == jar


def test_exit2_raises_session_unavailable_with_verbatim_remediation(
    fake_home: Path,
) -> None:
    _install_fake_broker(fake_home, exit_code=2, stdout="")

    with pytest.raises(_sso.SsoSessionUnavailableError) as exc:
        _sso.load_sso_cookies("corp")
    # Verbatim remediation text; names the profile, never the session bytes.
    assert str(exc.value) == (
        "SSO session unavailable for profile corp; run 'sso-broker register corp'"
    )


def test_broker_absent_raises_not_installed(fake_home: Path) -> None:
    # No broker written under fake_home → install-the-pack remediation.
    with pytest.raises(_sso.SsoBrokerNotInstalledError) as exc:
        _sso.load_sso_cookies("corp")
    assert "install the credential-brokers pack" in str(exc.value)


def test_exit0_unreadable_path_fails_closed(fake_home: Path) -> None:
    # Engine exits 0 but the path it prints does not exist → fail closed.
    _install_fake_broker(
        fake_home, exit_code=0, stdout=f"{fake_home / 'missing.jar'}\n"
    )
    with pytest.raises(_sso.SsoSessionUnavailableError):
        _sso.load_sso_cookies("corp")


def test_unspawnable_engine_fails_closed_as_broker_unavailable(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A spawn failure is not an expired session — the stored session is
    # untouched — so it must not reach the consumer's recovery path.
    _install_fake_broker(fake_home, exit_code=0, stdout="ignored\n")

    def _boom(*_a, **_k):
        raise OSError("interpreter vanished")

    monkeypatch.setattr(subprocess, "Popen", _boom)
    with pytest.raises(_sso.SsoBrokerUnavailableError) as exc:
        _sso.load_sso_cookies("corp")
    assert not isinstance(exc.value, _sso.SsoSessionUnavailableError)


def test_argv_carries_only_profile_no_cookie_value(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_broker(fake_home, exit_code=2)
    seen: dict[str, list[str]] = {}

    real_popen = subprocess.Popen

    def _capture(argv, *a, **k):
        seen["argv"] = list(argv)
        return real_popen(argv, *a, **k)

    monkeypatch.setattr(subprocess, "Popen", _capture)
    with pytest.raises(_sso.SsoSessionUnavailableError):
        _sso.load_sso_cookies("corp")

    argv = seen["argv"]
    # Exactly: [interpreter, broker, "get-cookies", "corp"] — only the profile
    # name leaves the process; no cookie value crosses argv.
    assert argv[-2:] == ["get-cookies", "corp"]
    assert "sso-broker.py" in argv[1]
    for banned in ("--token", "--cookie", "--api-token", "Cookie", "JSESSIONID"):
        assert all(banned not in part for part in argv), argv


def test_spawn_is_argv_composed_and_never_shelled() -> None:
    # Structural: every engine invocation is a composed argv list — never a shell,
    # never os.system / os.exec*; and the resolver never writes or copies the jar
    # (it only reads the path the engine prints).
    #
    # ``subprocess.Popen`` *is* permitted, and is the point: AC3's wall-clock bound
    # has to kill the whole process tree on expiry, and ``subprocess.run``'s own
    # timeout kills only the direct child — leaving playwright's Chromium alive
    # holding a live corporate session. The ban that carries the security meaning
    # is on shelling out, not on the spawn primitive.
    src = Path(_sso.__file__).read_text(encoding="utf-8")
    assert "subprocess.Popen(" in src
    for banned in ("os.system(", "os.exec", "shell=True"):
        assert banned not in src, banned


def test_version_matches_pyproject() -> None:
    assert credbroker.__version__ == "0.6.0"
