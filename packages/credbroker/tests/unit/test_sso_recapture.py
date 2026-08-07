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

import ast
import contextlib
import functools
import importlib.util
import inspect
import json
import os
import signal
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import credbroker
import pytest
from credbroker import _sso

# The names without which a child CPython (and Chromium) fails to start. Tests
# assert these as real passthroughs rather than overwriting them with sentinels.
_PLATFORM_BASE_ENV = frozenset({
    "PATH", "PATHEXT", "COMSPEC", "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR",
    "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
    "APPDATA", "LOCALAPPDATA", "PROGRAMFILES",
})


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


def _process_alive(pid: int) -> bool:
    """True while *pid* is still running. Cross-platform."""
    if os.name == "posix":
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:  # pragma: no cover — alive, owned elsewhere
            return True
        return True
    # Windows: tasklist is the portable probe without a third-party dep. CSV so
    # the pid is matched in its own field — a bare substring also hits the
    # memory and session columns. A missing tasklist (Server Core) raises
    # FileNotFoundError, which `check=False` does not cover.
    try:
        out = subprocess.run(  # noqa: S603, S607
            ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
            capture_output=True, text=True, check=False,
        ).stdout
    except OSError:  # pragma: no cover — tasklist absent
        pytest.skip("tasklist unavailable; cannot probe process liveness")
    import csv as _csv
    for row in _csv.reader(out.splitlines()):
        if len(row) > 1 and row[1].strip() == str(pid):
            return True
    return False


def test_spawn_kills_process_tree(tmp_path):       # STUB: AC3
    # The fake broker spawns a grandchild that outlives it, then sleeps past the
    # timeout. Without the tree kill the grandchild survives — exactly how
    # playwright's Chromium leaks a live corporate session and keeps the
    # browser-state lock.
    #
    # Runs on **both** platforms deliberately. A POSIX-only assertion would leave
    # the Windows `taskkill` arm unexercised even on the Windows parity runner —
    # which would look like coverage while proving nothing about the arm that is
    # reasoned rather than executed. The grandchild is spawned via
    # `subprocess.Popen` rather than `os.fork` so the same test body runs on
    # Windows.
    marker = tmp_path / "grandchild.pid"
    fake = _write_fake_broker(tmp_path, f"""
        import subprocess
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
        open({str(marker)!r}, "w").write(str(child.pid))
        time.sleep(120)
    """)

    # 6 s, not 2: the timeout must not fire before the fake broker's interpreter
    # has started and reached its fork, or the grandchild never exists and the
    # test fails for a harness reason. Interpreter start plus fork is a few
    # hundred milliseconds; this is a ~20x margin, which a loaded CI box needs.
    with pytest.raises(credbroker.SsoBrokerUnavailableError):
        _sso._spawn_broker(
            [sys.executable, str(fake), "refresh", "p"],
            timeout=6.0, env_profile="browser", capture=False,
        )

    deadline = time.monotonic() + 5
    grandchild = None
    while time.monotonic() < deadline and grandchild is None:
        if marker.exists():
            grandchild = int(marker.read_text())
        else:
            time.sleep(0.05)
    assert grandchild is not None, (
        "fake broker never spawned its grandchild — the spawn timeout fired "
        "before the child got that far, so this run proved nothing"
    )
    # POSIX: the grandchild inherited the new session's process group, so the
    # group kill reaches it. Windows: `taskkill /T` walks the process tree.
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and _process_alive(grandchild):
        time.sleep(0.1)
    if _process_alive(grandchild):  # pragma: no cover — the regression to catch
        with contextlib.suppress(OSError):
            os.kill(grandchild, getattr(signal, "SIGKILL", signal.SIGTERM))
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
    # Sentinels only for the network/browser names. Overwriting the platform
    # base — SYSTEMROOT, COMSPEC, PATH, TEMP — is how you make the child fail to
    # start at all, which would fail the AC26 parity run for a harness reason on
    # the one platform it exists to prove.
    for name in _sso._BROWSER_ENV_ALLOWLIST - _PLATFORM_BASE_ENV:
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
    for name in _sso._BROWSER_ENV_ALLOWLIST - _PLATFORM_BASE_ENV:
        assert env.get(name) == f"value-of-{name}", f"{name} not forwarded"
    # The platform base is asserted as a real passthrough instead.
    for name in _PLATFORM_BASE_ENV & _sso._BROWSER_ENV_ALLOWLIST:
        if name in os.environ:
            assert env.get(name) == os.environ[name], f"{name} not forwarded"


def test_engine_env_profile_drops_the_browser_variables(monkeypatch, tmp_path):  # STUB: AC3
    # load_sso_cookies takes the allowlist *minus* the display/browser variables:
    # get-cookies never launches a browser.
    browser_only = _sso._BROWSER_ENV_ALLOWLIST - _sso._ENGINE_ENV_ALLOWLIST
    assert "PLAYWRIGHT_BROWSERS_PATH" in browser_only
    for name in _sso._BROWSER_ENV_ALLOWLIST - _PLATFORM_BASE_ENV:
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
    for name in _sso._ENGINE_ENV_ALLOWLIST - _PLATFORM_BASE_ENV:
        assert env.get(name) == f"value-of-{name}", f"{name} not forwarded"


def test_spawn_failure_is_broker_unavailable(tmp_path):    # STUB: AC3
    with pytest.raises(credbroker.SsoBrokerUnavailableError):
        _sso._spawn_broker(
            [str(tmp_path / "does-not-exist")],
            timeout=30.0, env_profile="engine", capture=True,
        )


# ----------------------------------------------------------------------
# The fake engine: a real executable at the real resolved path, so argv, exit
# codes and the process tree are real and no browser is involved.
# ----------------------------------------------------------------------


_FAKE_ENGINE = '''\
import json, pathlib, sys
here = pathlib.Path(__file__).resolve().parent
(here / "argv.json").write_text(json.dumps(sys.argv), encoding="utf-8")
out = here / "stdout"
if out.exists():
    sys.stdout.write(out.read_text(encoding="utf-8"))
sys.exit(int((here / "exit_code").read_text(encoding="utf-8").strip()))
'''


class _FakeBroker:
    def __init__(self, bin_dir: Path) -> None:
        self._dir = bin_dir
        self.exit_code = 0

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name == "exit_code":
            (self._dir / "exit_code").write_text(str(value), encoding="utf-8")

    @property
    def last_argv(self) -> list[str]:
        return json.loads((self._dir / "argv.json").read_text(encoding="utf-8"))

    @property
    def was_invoked(self) -> bool:
        return (self._dir / "argv.json").exists()

    def set_stdout(self, text: str) -> None:
        (self._dir / "stdout").write_text(text, encoding="utf-8")


@pytest.fixture
def fake_broker(tmp_path, monkeypatch):
    """Install a fake engine at the path ``_broker_path()`` resolves to.

    Both ``HOME`` and ``USERPROFILE`` are redirected — ``Path.home()`` reads
    ``USERPROFILE`` on Windows. No module attribute needs rebinding here:
    ``_broker_path()`` resolves at call time.
    """
    home = tmp_path / "home"
    bin_dir = home / ".agentbundle" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "sso-broker.py").write_text(_FAKE_ENGINE, encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    return _FakeBroker(bin_dir)


# ----------------------------------------------------------------------
# AC5 — load_sso_cookies validates too, and runs under the same bounds.
# ----------------------------------------------------------------------


def test_load_sso_cookies_validates_profile():     # STUB: AC5
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.load_sso_cookies("../../../../tmp/pwn")


def test_load_sso_cookies_validates_before_spawning(fake_broker):   # STUB: AC5
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.load_sso_cookies("abc\n")
    assert not fake_broker.was_invoked


def test_probe_timeout_is_not_recoverable(fake_broker, monkeypatch, tmp_path):  # STUB: AC3
    # `load_sso_cookies` ran with no timeout at all. A slow or locked keychain
    # holding a perfectly valid session must not look like a missing one, or
    # the consumer opens a browser for nothing.
    slow = tmp_path / "home" / ".agentbundle" / "bin" / "sso-broker.py"
    slow.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    monkeypatch.setattr(_sso, "_TIMEOUT_GET_COOKIES_S", 1.0)

    with pytest.raises(credbroker.SsoBrokerUnavailableError) as excinfo:
        credbroker.load_sso_cookies("jira")
    # The type is the whole point: SsoSessionUnavailableError is what the
    # consumer's recovery path keys on.
    assert not isinstance(excinfo.value, credbroker.SsoSessionUnavailableError)


def test_get_cookies_captures_stdout_but_not_stderr(fake_broker, tmp_path, capfd):  # STUB: AC3
    jar = tmp_path / "jira.jar"
    jar.write_text("[]", encoding="utf-8")
    engine = tmp_path / "home" / ".agentbundle" / "bin" / "sso-broker.py"
    engine.write_text(
        f"import sys\n"
        f"sys.stdout.write({str(jar)!r} + chr(10))\n"
        f"sys.stderr.write('keychain unlocked' + chr(10))\n",
        encoding="utf-8",
    )
    assert credbroker.load_sso_cookies("jira") == jar
    assert "keychain unlocked" in capfd.readouterr().err


def test_load_sso_cookies_drops_the_browser_env(fake_broker, monkeypatch, tmp_path):  # STUB: AC3
    monkeypatch.setenv("JIRA_API_TOKEN", "secret-should-not-cross")
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", "/browsers")
    dump = tmp_path / "env.json"
    engine = tmp_path / "home" / ".agentbundle" / "bin" / "sso-broker.py"
    engine.write_text(
        f"import json, os, sys\n"
        f"json.dump(dict(os.environ), open({str(dump)!r}, 'w'))\n"
        f"sys.exit(2)\n",
        encoding="utf-8",
    )
    with pytest.raises(credbroker.SsoSessionUnavailableError):
        credbroker.load_sso_cookies("jira")
    env = json.loads(dump.read_text())
    assert "JIRA_API_TOKEN" not in env
    assert "PLAYWRIGHT_BROWSERS_PATH" not in env


def test_get_cookies_exit_2_stays_session_unavailable(fake_broker):   # STUB: AC1
    fake_broker.exit_code = 2
    with pytest.raises(credbroker.SsoSessionUnavailableError):
        credbroker.load_sso_cookies("jira")


def test_get_cookies_exit_3_is_broker_unavailable(fake_broker):       # STUB: AC1
    # Engine-internal failure — including a materialisation write failure —
    # must not present as a missing session.
    fake_broker.exit_code = 3
    with pytest.raises(credbroker.SsoBrokerUnavailableError):
        credbroker.load_sso_cookies("jira")


# ----------------------------------------------------------------------
# AC1 / AC2 — the recapture verbs and the per-verb exit taxonomy.
# ----------------------------------------------------------------------


_REGISTER_KWARGS = {
    "login_url": "https://idp.example.com/login",
    "success_url_pattern": r"https://jira\.example\.com/secure/.*",
    "cookie_domains": ("jira.example.com",),
    "validation_endpoint": "/rest/api/2/myself",
}


def test_per_operation_timeouts_match_ac3_table(fake_broker, monkeypatch, tmp_path):  # STUB: AC3
    # Lives here because T3 is where all three callers exist. One value for
    # "both functions" would be wrong for two of them: register carries a 300 s
    # human sign-in poll and a second seeding launch, refresh carries neither.
    seen: dict[str, float] = {}
    real = _sso._spawn_broker

    def _record(argv, *, timeout, env_profile, capture):
        seen[_sso._verb_of(argv)] = timeout
        return real(argv, timeout=timeout, env_profile=env_profile, capture=capture)

    monkeypatch.setattr(_sso, "_spawn_broker", _record)

    jar = tmp_path / "jira.jar"
    jar.write_text("[]", encoding="utf-8")
    fake_broker.set_stdout(f"{jar}\n")
    credbroker.load_sso_cookies("jira")
    credbroker.refresh_sso_session("jira")
    credbroker.register_sso_session("jira", **_REGISTER_KWARGS)

    assert seen == {"get-cookies": 30.0, "refresh": 180.0, "register": 540.0}


def test_refresh_argv_carries_no_destination(fake_broker):   # STUB: AC1
    credbroker.refresh_sso_session("jira")
    argv = fake_broker.last_argv
    assert argv[-2:] == ["refresh", "jira"]
    assert not any(a.startswith("--") for a in argv)


def test_refresh_signature_has_no_destination_param():       # STUB: AC1
    params = set(inspect.signature(credbroker.refresh_sso_session).parameters)
    assert params == {"profile"}


def test_refresh_validates_the_profile_before_spawning(fake_broker):   # STUB: AC1/AC4
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.refresh_sso_session("../../../../tmp/pwn")
    assert not fake_broker.was_invoked


def test_exit4_is_not_registered(fake_broker):               # STUB: AC1
    fake_broker.exit_code = 4
    with pytest.raises(credbroker.SsoProfileNotRegisteredError):
        credbroker.refresh_sso_session("jira")


def test_not_registered_still_catchable_as_session_unavailable(fake_broker):  # STUB: AC1
    # Subclassing the existing type keeps every current handler working.
    fake_broker.exit_code = 4
    with pytest.raises(credbroker.SsoSessionUnavailableError):
        credbroker.refresh_sso_session("jira")


@pytest.mark.parametrize("verb", ["refresh", "register"])
def test_exit3_is_generic_failure(fake_broker, verb):        # STUB: AC1
    # `3` is playwright-absent / sign-in-incomplete / any engine-internal
    # failure — never "not registered".
    fake_broker.exit_code = 3
    with pytest.raises(credbroker.SsoRecaptureFailedError):
        if verb == "refresh":
            credbroker.refresh_sso_session("jira")
        else:
            credbroker.register_sso_session("jira", **_REGISTER_KWARGS)


@pytest.mark.parametrize("verb", ["refresh", "register"])
def test_unknown_exit_is_generic_failure(fake_broker, verb):   # STUB: AC1
    fake_broker.exit_code = 42
    with pytest.raises(credbroker.SsoRecaptureFailedError):
        if verb == "refresh":
            credbroker.refresh_sso_session("jira")
        else:
            credbroker.register_sso_session("jira", **_REGISTER_KWARGS)


def test_exit5_maps_to_interaction_required(fake_broker):         # STUB: AC14a
    fake_broker.exit_code = 5
    with pytest.raises(credbroker.SsoInteractionRequiredError):
        credbroker.refresh_sso_session("jira")


def test_interaction_required_is_not_recoverable(fake_broker):    # STUB: AC14a
    # Only the two recoverable rows of AC1's table may reach a consumer's
    # recovery path; "a human is needed" is terminal.
    fake_broker.exit_code = 5
    with pytest.raises(credbroker.SsoError) as excinfo:
        credbroker.refresh_sso_session("jira")
    assert not isinstance(excinfo.value, credbroker.SsoSessionUnavailableError)


def test_timeout_is_broker_unavailable(fake_broker, monkeypatch, tmp_path):   # STUB: AC1
    slow = tmp_path / "home" / ".agentbundle" / "bin" / "sso-broker.py"
    slow.write_text("import time\ntime.sleep(60)\n", encoding="utf-8")
    monkeypatch.setattr(_sso, "_TIMEOUT_REFRESH_S", 1.0)
    with pytest.raises(credbroker.SsoBrokerUnavailableError):
        credbroker.refresh_sso_session("jira")


def test_broker_absent_is_not_installed(tmp_path, monkeypatch):   # STUB: AC1
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    with pytest.raises(credbroker.SsoBrokerNotInstalledError):
        credbroker.refresh_sso_session("jira")
    with pytest.raises(credbroker.SsoBrokerNotInstalledError):
        credbroker.register_sso_session("jira", **_REGISTER_KWARGS)


def test_register_argv_is_ephemeral_and_carries_no_secret(fake_broker):   # STUB: AC2
    credbroker.register_sso_session(
        "jira", session_filename="jira-session.jar", ttl_hint_minutes=480,
        **_REGISTER_KWARGS,
    )
    argv = fake_broker.last_argv
    assert "register" in argv
    assert "--ephemeral" in argv, "register_sso_session is --ephemeral's only user"
    assert argv[argv.index("register") + 1] == "jira"
    assert "--login-url" in argv
    assert argv[argv.index("--login-url") + 1] == _REGISTER_KWARGS["login_url"]
    assert argv[argv.index("--cookie-domain") + 1] == "jira.example.com"
    assert argv[argv.index("--ttl-hint-minutes") + 1] == "480"
    for banned in ("--token", "--api-token", "--cookie-value", "Cookie:", "JSESSIONID"):
        assert all(banned not in part for part in argv), argv
    # A jar *path* must never cross argv; --session-filename is a bare name.
    assert argv[argv.index("--session-filename") + 1] == "jira-session.jar"
    store = str(Path.home() / ".agentbundle" / "sso-cookies")
    assert all(store not in part for part in argv), argv


def test_register_omits_absent_optionals(fake_broker):        # STUB: AC2
    credbroker.register_sso_session("jira", **_REGISTER_KWARGS)
    argv = fake_broker.last_argv
    assert "--session-filename" not in argv
    assert "--ttl-hint-minutes" not in argv


def test_register_is_the_only_function_taking_a_destination():   # STUB: AC1/AC2
    register = set(inspect.signature(credbroker.register_sso_session).parameters)
    assert "login_url" in register
    assert set(inspect.signature(credbroker.refresh_sso_session).parameters) == {"profile"}


def test_register_validates_the_profile_before_spawning(fake_broker):  # STUB: AC2/AC4
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.register_sso_session("CON", **_REGISTER_KWARGS)
    assert not fake_broker.was_invoked


def test_recapture_success_returns_none(fake_broker):         # STUB: AC1/AC2
    assert credbroker.refresh_sso_session("jira") is None
    assert credbroker.register_sso_session("jira", **_REGISTER_KWARGS) is None


# ----------------------------------------------------------------------
# AC10 — the grammar is enforced in two implementations and cannot drift.
# ----------------------------------------------------------------------
#
# The engine cannot import this package (`credbroker` subprocesses it), so the
# grammar is deliberately duplicated and pinned equal here. Drift is a
# fail-open: a name `credbroker` accepts and the engine rejects would make
# every `check` attempt a recapture. Under AC1's taxonomy a grammar rejection
# is a non-recoverable `SsoBrokerUnavailableError`, so the drift surfaces as a
# hard exit 2 rather than a recapture loop — but this test is what stops it
# arising at all.
#
# The pack source is canonical; the projected `.agentbundle/bin/` copy is
# covered by the build's own drift gate.

_REPO_ROOT = Path(__file__).resolve().parents[4]
BROKER_PY = (
    _REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "adapter-root-bins"
    / "sso-broker.py"
)


def _engine_literal(name: str):
    """Literal-evaluate the engine's module-level assignment to *name*.

    Read from source rather than imported: the engine is not on the package
    path, and a textual read is what makes this a *drift* test rather than a
    second import of the same object.
    """
    tree = ast.parse(BROKER_PY.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(t, ast.Name) and t.id == name for t in node.targets
        ):
            continue
        value = node.value
        # `frozenset({...})` — literal_eval cannot evaluate the call, so take
        # the set literal it wraps.
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "frozenset"
        ):
            return frozenset(ast.literal_eval(value.args[0]))
        return ast.literal_eval(value)
    raise AssertionError(f"{name} not found in {BROKER_PY}")


def test_grammar_literal_matches_engine():         # STUB: AC10
    assert _engine_literal("_SSO_PROFILE_PATTERN") == _sso._PROFILE_RE.pattern
    assert _engine_literal("_RESERVED_DEVICE_NAMES") == _sso._RESERVED_DEVICE_NAMES


@pytest.mark.parametrize("profile", [
    "abc\n", "abc\r\n", "x" * 65, "café", "", ".", "..", "CON", "con.toml",
    "-x", "../../../../tmp/pwn", ".hidden", "a" * 64, "ok.name-1_2",
])
def test_the_two_implementations_agree_per_vector(profile):    # STUB: AC10
    # Literal equality is necessary but not sufficient: the two could apply the
    # same literals differently (re.match vs re.fullmatch, whole-name vs stem
    # for the device check). Drive both and compare the verdicts.
    library_ok = True
    try:
        credbroker.validate_sso_profile(profile)
    except credbroker.SsoConfigError:
        library_ok = False

    engine = _load_engine_module()
    engine_ok = engine._profile_grammar_error(profile) is None

    assert library_ok == engine_ok, (
        f"{profile!r}: credbroker says {library_ok}, engine says {engine_ok}"
    )


@functools.lru_cache(maxsize=1)
def _load_engine_module():
    """Import the engine from its real path (it is outside the package tree).

    Cached: the engine's own bootstrap does `sys.path.insert` and nothing here
    undoes it, so re-executing it once per parametrised case accumulates
    duplicate entries pointing at `adapter-root-bins/`, from which
    `_sso_keychain_macos` can then shadow imports for later tests.
    """
    spec = importlib.util.spec_from_file_location("_sso_broker_parity", BROKER_PY)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    sys.path.insert(0, str(BROKER_PY.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path[:] = before
    return mod
