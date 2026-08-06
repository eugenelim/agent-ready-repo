"""SSO recapture API — profile grammar, spawn bounds, and the verb taxonomy.

Covers AC1–AC5 and AC10 of
``docs/specs/jira-check-sso-auto-login/spec.md``. Every spawn runs a **fake
broker executable** written into ``tmp_path``: real argv, real exit codes, real
process tree, no browser.

The single test seam is a redirected home. ``monkeypatch.setenv`` sets **both**
``HOME`` and ``USERPROFILE`` because ``Path.home()`` reads ``USERPROFILE`` on
Windows. Unlike ``test_sso_broker_verbs.py`` no module attribute needs
rebinding: ``credbroker._sso._broker_path()`` resolves at *call* time, while the
engine computes ``_AGENTBUNDLE_HOME`` at *import* time.
"""

from __future__ import annotations

import os
import signal
import sys
import textwrap
import time
from pathlib import Path

import credbroker
import pytest
from credbroker import _sso


def _write_fake_broker(tmp_path: Path, body: str, *, name: str = "sso-broker.py") -> Path:
    """Write an executable stand-in for the engine and return its path.

    *body* is dedented and appended to a preamble that exposes ``argv`` (the
    engine's own argv, minus the interpreter and script path).
    """
    script = tmp_path / name
    script.write_text(
        "import os, sys, time\nargv = sys.argv[1:]\n" + textwrap.dedent(body),
        encoding="utf-8",
    )
    return script


# ----------------------------------------------------------------------
# AC4 — validate_sso_profile: the canonical grammar.
# ----------------------------------------------------------------------


def test_profile_grammar_rejects_newline():        # STUB: AC4
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.validate_sso_profile("abc\n")   # re.match would accept this


def test_profile_grammar_rejects_windows_device():  # STUB: AC4
    for bad in ("CON", "con.toml", "NUL", "COM1"):
        with pytest.raises(credbroker.SsoConfigError):
            credbroker.validate_sso_profile(bad)


def test_profile_grammar_rejects_non_str():        # STUB: AC4
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.validate_sso_profile(5)


def test_profile_grammar_accepts_ordinary():       # STUB: AC4
    credbroker.validate_sso_profile("jira")


# ----------------------------------------------------------------------
# AC3 — the shared spawn helper: bounds, tree kill, environment allowlist.
# ----------------------------------------------------------------------


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group kill arm")
def test_spawn_kills_process_tree(tmp_path):       # STUB: AC3
    # The fake broker forks a grandchild that outlives it, then sleeps past the
    # timeout. Without the process-group kill the grandchild survives — exactly
    # how playwright's Chromium leaks a live corporate session.
    marker = tmp_path / "grandchild.pid"
    fake = _write_fake_broker(tmp_path, f"""
        pid = os.fork()
        if pid == 0:
            os.setpgid(0, os.getpgid(os.getppid()))
            open({str(marker)!r}, "w").write(str(os.getpid()))
            time.sleep(60)
            os._exit(0)
        time.sleep(60)
    """)

    with pytest.raises(credbroker.SsoBrokerUnavailableError):
        _sso._spawn_broker(
            [sys.executable, str(fake), "refresh", "p"],
            timeout=2.0, env_profile="browser", capture=False,
        )

    deadline = time.monotonic() + 5
    grandchild = None
    while time.monotonic() < deadline and grandchild is None:
        if marker.exists():
            grandchild = int(marker.read_text())
        else:
            time.sleep(0.05)
    assert grandchild is not None, "fake broker never forked its grandchild"
    # The grandchild joined the spawned session's group, so the group kill must
    # have reached it.
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        try:
            os.kill(grandchild, 0)
        except ProcessLookupError:
            break
        time.sleep(0.05)
    else:  # pragma: no cover — the regression this test exists to catch
        os.kill(grandchild, signal.SIGKILL)
        pytest.fail("grandchild survived the timeout kill")


def test_spawn_timeout_raises_broker_unavailable(tmp_path):   # STUB: AC3
    # A timeout is NOT an expired session: it must map to the non-recoverable
    # subtype so AC11's recovery path cannot fire on a slow keychain.
    fake = _write_fake_broker(tmp_path, "time.sleep(60)\n")
    with pytest.raises(credbroker.SsoBrokerUnavailableError) as excinfo:
        _sso._spawn_broker(
            [sys.executable, str(fake), "get-cookies", "p"],
            timeout=1.0, env_profile="engine", capture=True,
        )
    assert not isinstance(excinfo.value, credbroker.SsoSessionUnavailableError)


def test_spawn_capture_mode_returns_stdout_and_leaves_stderr(tmp_path, capfd):  # STUB: AC3
    # get-cookies returns the materialised jar path on stdout, which the caller
    # parses; its stderr diagnostics must still reach the operator.
    fake = _write_fake_broker(tmp_path, """
        sys.stdout.write("/tmp/jar-path\\n")
        sys.stderr.write("engine diagnostic\\n")
    """)
    cp = _sso._spawn_broker(
        [sys.executable, str(fake), "get-cookies", "p"],
        timeout=30.0, env_profile="engine", capture=True,
    )
    assert cp.returncode == 0
    assert cp.stdout.strip() == "/tmp/jar-path"
    assert "engine diagnostic" in capfd.readouterr().err


def test_spawn_inherit_mode_returns_no_stdout(tmp_path, capfd):   # STUB: AC3
    fake = _write_fake_broker(tmp_path, 'sys.stdout.write("visible\\n")\n')
    cp = _sso._spawn_broker(
        [sys.executable, str(fake), "refresh", "p"],
        timeout=30.0, env_profile="browser", capture=False,
    )
    assert cp.returncode == 0
    assert cp.stdout is None
    assert "visible" in capfd.readouterr().out


def test_spawn_env_is_allowlisted(monkeypatch, tmp_path):  # STUB: AC3
    monkeypatch.setenv("JIRA_API_TOKEN", "secret-should-not-cross")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "also-should-not-cross")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/etc/ssl/corp.pem")
    for name in _sso._BROWSER_ENV_ALLOWLIST:
        monkeypatch.setenv(name, f"value-of-{name}")

    dump = tmp_path / "env.json"
    fake = _write_fake_broker(tmp_path, f"""
        import json
        json.dump(dict(os.environ), open({str(dump)!r}, "w"))
    """)
    _sso._spawn_broker(
        [sys.executable, str(fake), "refresh", "p"],
        timeout=30.0, env_profile="browser", capture=False,
    )
    import json
    env = json.loads(dump.read_text())

    assert "JIRA_API_TOKEN" not in env
    assert "ANTHROPIC_API_KEY" not in env
    for name in _sso._BROWSER_ENV_ALLOWLIST:
        assert env.get(name) == f"value-of-{name}", f"{name} not forwarded"


def test_engine_env_profile_drops_the_browser_variables(monkeypatch, tmp_path):  # STUB: AC3
    # load_sso_cookies takes the allowlist *minus* the display/browser variables:
    # get-cookies never launches a browser.
    browser_only = _sso._BROWSER_ENV_ALLOWLIST - _sso._ENGINE_ENV_ALLOWLIST
    assert "PLAYWRIGHT_BROWSERS_PATH" in browser_only
    for name in _sso._BROWSER_ENV_ALLOWLIST:
        monkeypatch.setenv(name, f"value-of-{name}")

    dump = tmp_path / "env.json"
    fake = _write_fake_broker(tmp_path, f"""
        import json
        json.dump(dict(os.environ), open({str(dump)!r}, "w"))
    """)
    _sso._spawn_broker(
        [sys.executable, str(fake), "get-cookies", "p"],
        timeout=30.0, env_profile="engine", capture=True,
    )
    import json
    env = json.loads(dump.read_text())
    for name in browser_only:
        assert name not in env, f"{name} must not reach the non-browser spawn"
    for name in _sso._ENGINE_ENV_ALLOWLIST:
        assert env.get(name) == f"value-of-{name}", f"{name} not forwarded"


def test_spawn_failure_is_broker_unavailable(tmp_path):    # STUB: AC3
    with pytest.raises(credbroker.SsoBrokerUnavailableError):
        _sso._spawn_broker(
            [str(tmp_path / "does-not-exist")],
            timeout=30.0, env_profile="engine", capture=True,
        )
