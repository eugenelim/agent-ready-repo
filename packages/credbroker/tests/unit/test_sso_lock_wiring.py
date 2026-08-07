"""T4/T7 (sso-store-transition-serialization): wiring and process boundary.

T4 asserts *where* the lock sits — that `rm` and `test` take it, and that no
acquisition encloses a region bounded by something other than the store (the
Chromium launch, the validation request). T7 proves the lock survives a real
process boundary, which the thread harness in ``test_sso_store_concurrency.py``
cannot do.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import pathlib
import signal
import subprocess
import sys
import textwrap
import time
import types

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
BROKER_DIR = (
    REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "adapter-root-bins"
)
BROKER_PY = BROKER_DIR / "sso-broker.py"


def _load_broker(py_path: pathlib.Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(py_path.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(py_path.parent))
    return mod


@pytest.fixture
def broker(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    mod = _load_broker(BROKER_PY)
    mod._AGENTBUNDLE_HOME = home / ".agentbundle"
    mod._SSO_PROFILE_DIR = mod._AGENTBUNDLE_HOME / "sso-profiles"
    mod._SSO_COOKIE_FILE_FLOOR = mod._AGENTBUNDLE_HOME / "sso-cookies"
    mod._SSO_LOCK_DIR = mod._AGENTBUNDLE_HOME / "sso-locks"
    mod._tier2_backend = None  # file-floor path, as on Linux
    return mod


def _register(mod, profile="jira"):
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._write_profile(profile, {
        "name": profile,
        "login_url": "https://example.com/login",
        "success_url_pattern": "dashboard",
        "cookie_domains": ["example.com"],
        "session_filename": f"{profile}.jar",
        "validation_endpoint": "/rest/api/2/myself",
        "ttl_hint_minutes": 60,
    })
    with mod._profile_lock(profile):
        mod._store_cookie_jar(
            profile, b'[{"name":"sid","value":"v","domain":"example.com"}]'
        )


# ----------------------------------------------------------------------
# T4 / AC5 — the lock never encloses a region the store does not bound.
# ----------------------------------------------------------------------


def _enclosing_lock_scopes(tree: ast.AST) -> list[ast.With]:
    return [
        n for n in ast.walk(tree)
        if isinstance(n, ast.With)
        and any(
            isinstance(i.context_expr, ast.Call)
            and getattr(i.context_expr.func, "id", None) == "_profile_lock"
            for i in n.items
        )
    ]


def _calls_within(node: ast.AST) -> set[str]:
    names = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            names.add(getattr(f, "id", None) or getattr(f, "attr", ""))
    return names


def test_no_lock_scope_encloses_the_browser_or_the_validation_request():
    """AC5: released before anything the store does not bound.

    Holding across a capture bounded in minutes would starve every reader;
    holding across the 15 s validation request would block writers on a network
    round-trip. Parsed, not grepped — prose in this module names both.
    """
    tree = ast.parse(BROKER_PY.read_text(encoding="utf-8"))
    forbidden = {"sync_playwright", "urlopen", "launch_persistent_context", "launch"}
    for scope in _enclosing_lock_scopes(tree):
        overlap = _calls_within(scope) & forbidden
        assert not overlap, f"lock scope at line {scope.lineno} encloses {overlap}"


# What each lock scope must *enclose*, not merely which function owns one.
# The name-only version of this check is exactly what the original
# `_do_get_cookies` defect passed through: the function acquired a lock, so it
# was counted, while the materialisation sat outside the scope.
_REQUIRED_WITHIN_LOCK = {
    "_capture": {"_write_profile", "_store_cookie_jar"},
    "_do_get_cookies": {"_load_cookie_jar", "_file_floor_write"},
    "_do_rm": {"exists", "_delete_cookie_jar", "unlink"},
    "_do_test": {"_load_cookie_jar"},
}


def test_exactly_four_acquisition_sites_each_enclosing_its_whole_transition():
    """AC5: four acquisition sites, and each one covers the right region.

    A fifth site would mean a verb acquired somewhere the spec did not
    authorise; a third would mean one is missing; a scope that stops short of
    its own mutation is the defect this test exists to catch.
    """
    tree = ast.parse(BROKER_PY.read_text(encoding="utf-8"))
    owners = {}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        scopes = _enclosing_lock_scopes(fn)
        if scopes:
            owners[fn.name] = set().union(*(_calls_within(s) for s in scopes))
    assert set(owners) == set(_REQUIRED_WITHIN_LOCK), set(owners)
    for name, required in _REQUIRED_WITHIN_LOCK.items():
        missing = required - owners[name]
        assert not missing, f"{name}'s lock scope does not enclose {missing}"


def test_rm_takes_the_lock_before_its_existence_check(broker):
    """AC5: the check-then-act gap against a first `register`.

    Composed outside the lock so a rejected profile still raises
    ProfileConfinementError first — `rm` is grammar-exempt by design.
    """
    tree = ast.parse(BROKER_PY.read_text(encoding="utf-8"))
    fn = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_do_rm"
    )
    scope = _enclosing_lock_scopes(fn)[0]
    assert "exists" in _calls_within(scope), "existence check sits outside the lock"
    assert "unlink" in _calls_within(scope), "TOML unlink sits outside the lock"


def test_rm_removes_the_profile_and_the_jar(broker):
    """AC5: the ordinary path still works with the lock in place."""
    _register(broker)
    assert broker._do_rm("jira") == 0
    assert not broker._profile_path("jira").exists()
    with broker._profile_lock("jira"):
        assert broker._load_cookie_jar("jira") is None


def test_rm_on_an_unregistered_profile_is_a_no_op(broker):
    """AC5: the not-registered branch is inside the lock and still returns 0."""
    assert broker._do_rm("ghost") == 0


def test_get_cookies_still_materialises_end_to_end(broker):
    """A smoke check that the verb works with the lock in place.

    Not the AC4 artifact — that is the negative-control pair in
    `test_sso_store_concurrency.py`. This only shows the happy path still runs.
    """
    _register(broker)
    assert broker._do_get_cookies("jira") == 0
    assert broker._cookie_floor_path("jira").exists()


# ----------------------------------------------------------------------
# T7 / AC7, AC11 — the process boundary.
# ----------------------------------------------------------------------


def _child_source(home: pathlib.Path, profile: str, hold_s: float) -> str:
    """A child that takes the lock, signals, and holds it."""
    return textwrap.dedent(f"""
        import importlib.util, pathlib, sys, time
        p = pathlib.Path({str(BROKER_PY)!r})
        spec = importlib.util.spec_from_file_location("b", p)
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(p.parent))
        spec.loader.exec_module(mod)
        mod._AGENTBUNDLE_HOME = pathlib.Path({str(home)!r}) / ".agentbundle"
        mod._SSO_LOCK_DIR = mod._AGENTBUNDLE_HOME / "sso-locks"
        with mod._profile_lock({profile!r}):
            print("held", flush=True)
            time.sleep({hold_s})
    """)


def test_a_second_process_contends_with_a_real_holder(broker, tmp_path):
    """AC7: the lock crosses a process boundary, not just a thread boundary.

    **The load-bearing interprocess test**, and deliberately not `skipif`-ed:
    it sends no signal (the `child.kill()` below is cleanup), so it is
    platform-neutral, and Windows is the one platform where the contended path
    is reached through `EACCES` rather than `BlockingIOError`. Skipping it there
    would remove the only evidence on the platform that needs it most.

    The thread harness cannot stand in for this: if a refactor moved the lock to
    a per-process singleton, every thread test would still pass while
    interprocess serialisation was gone.
    """
    home = pathlib.Path(os.environ["HOME"])
    child = subprocess.Popen(
        [sys.executable, "-c", _child_source(home, "jira", 30)],
        stdout=subprocess.PIPE, text=True,
    )
    try:
        assert child.stdout.readline().strip() == "held"
        started = time.monotonic()
        with (
            pytest.raises(broker.StoreContendedError),
            broker._profile_lock("jira", budget_s=0.5),
        ):
            pass
        assert time.monotonic() - started >= 0.5
    finally:
        child.kill()
        child.wait(10)


@pytest.mark.skipif(os.name != "posix", reason="SIGKILL semantics")
def test_a_killed_holder_leaves_the_profile_usable(broker, tmp_path):
    """AC11: no profile is bricked by a lock, and nothing reaps one to achieve it.

    The kernel releases on process death, which is why there is no stale-lock
    handling anywhere in the engine — a reaper would only add a way to break a
    lock a live process still holds.
    """
    home = pathlib.Path(os.environ["HOME"])
    child = subprocess.Popen(
        [sys.executable, "-c", _child_source(home, "jira", 30)],
        stdout=subprocess.PIPE, text=True,
    )
    assert child.stdout.readline().strip() == "held"
    child.send_signal(signal.SIGKILL)
    child.wait(10)

    # No sleep, no retry loop, no cleanup step: the lock is simply free.
    with broker._profile_lock("jira", budget_s=2):
        pass
    assert broker._sso_lock_path("jira").exists(), (
        "the lockfile must survive; unlinking it would let two processes hold "
        "locks on different inodes for the same profile"
    )


@pytest.mark.skipif(os.name != "posix", reason="SIGKILL semantics")
def test_two_real_processes_leave_one_whole_jar(broker, tmp_path):
    """AC7: two real processes, end to end on the file-floor path.

    **What this does and does not prove, stated plainly.** It is a smoke test
    that the whole path runs across a process boundary without deadlock or
    error. It is *not* on its own evidence that the lock works: the file floor
    goes through `_file_floor_write`, which stages to a unique temp and
    `os.replace`s it, so two unsynchronised writers each land a whole jar and
    one simply wins. This assertion would hold with the lock removed.

    The tests that actually pin interprocess serialisation are
    `test_a_second_process_contends_with_a_real_holder` (a second process is
    genuinely blocked by the first) and `test_a_killed_holder_leaves_the_profile_usable`.
    The corruption this spec exists to prevent lives in the chunked-generation
    Tier-2 transition, which no subprocess can exercise — `_tier2_backend` binds
    at import from a platform sibling with no injection seam, so a child cannot
    be handed a fake keychain. That path is thread-verified in
    `test_sso_store_concurrency.py` and process-verified nowhere; AC7 records
    the limit rather than implying coverage it does not have.
    """
    home = pathlib.Path(os.environ["HOME"])
    _register(broker)

    def writer(tag: str) -> subprocess.Popen:
        src = textwrap.dedent(f"""
            import importlib.util, json, pathlib, sys
            p = pathlib.Path({str(BROKER_PY)!r})
            spec = importlib.util.spec_from_file_location("b", p)
            mod = importlib.util.module_from_spec(spec)
            sys.path.insert(0, str(p.parent))
            spec.loader.exec_module(mod)
            mod._AGENTBUNDLE_HOME = pathlib.Path({str(home)!r}) / ".agentbundle"
            mod._SSO_LOCK_DIR = mod._AGENTBUNDLE_HOME / "sso-locks"
            mod._SSO_COOKIE_FILE_FLOOR = mod._AGENTBUNDLE_HOME / "sso-cookies"
            mod._tier2_backend = None
            jar = json.dumps(
                [{{"name": "{tag}" + str(i), "value": "{tag}" * 40,
                   "domain": "example.com"}} for i in range(40)],
                separators=(",", ":"),
            ).encode()
            with mod._profile_lock("jira"):
                mod._store_cookie_jar("jira", jar)
        """)
        return subprocess.Popen([sys.executable, "-c", src])

    procs = [writer("a"), writer("b")]
    for pr in procs:
        assert pr.wait(30) == 0

    with broker._profile_lock("jira"):
        jar = broker._load_cookie_jar("jira")
    assert jar is not None
    tags = {c["name"][0] for c in json.loads(jar.decode("utf-8"))}
    assert len(tags) == 1, f"a jar with bytes from both writers: {tags}"
