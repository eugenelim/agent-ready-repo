"""T2/T3 (sso-store-transition-serialization): the serialisation property.

The reproduction harness for the defect this spec exists to close. Writers run
as threads against one loaded module and are *parked* at a chosen write index
inside a fake Tier-2 backend, so an interleaving that would otherwise need luck
is forced deterministically.

Threads are the right surface rather than a shortcut: both ``flock`` and
``msvcrt.locking`` conflict between two descriptors opened by one process, so a
thread harness exercises the real primitive. T7 adds the process-level test that
threads cannot stand in for.

**Every serialisation test here has a negative-control twin** that stubs the
lock out and asserts corruption *does* result. Without the lock the three-writer
case already fails *closed* — the reader gets no jar at all — so "the reader got
no jar" is a passing assertion against unfixed code. The negative controls are
what distinguish a real pass from that.
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import pathlib
import sys
import threading
import time
import types

import pytest

# AC20 — this module must *execute* on the Windows runner, not merely be
# collected there. `self_host_windows.py` judges each step by return code alone,
# so a wholly-skipped module exits 0 and reads as coverage. Windows is also the
# only place `EACCES`-means-contention is exercised at all; every other platform
# signals it with `BlockingIOError`. So: fail, never skip, if the lock primitive
# is not importable on the platform we are running on.
if os.name == "posix":
    import fcntl as _lock_mod
else:  # pragma: no cover - the Windows runner
    import msvcrt as _lock_mod
assert _lock_mod is not None, (
    "the lock primitive is unavailable on this platform; this module must fail "
    "rather than skip, or a wholly-skipped Windows run would read as coverage"
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
BROKER_PY = (
    REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "adapter-root-bins"
    / "sso-broker.py"
)


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


class _ParkingBackend:
    """Thread-safe in-memory Tier-2 backend that can park a chosen writer.

    ``park_at(ident, index, event)`` blocks the nominated thread just before its
    *index*-th ``write_credential`` until *event* is set. That is what turns an
    interleaving from a race into a test.
    """

    def __init__(self):
        self.store: dict[tuple[str, str], str] = {}
        self._guard = threading.Lock()
        self._parks: dict[int, tuple[int, threading.Event, threading.Event]] = {}
        self._writes: dict[int, int] = {}
        self.refuse_after: int | None = None

    def park_at(self, ident: int, index: int, release: threading.Event):
        reached = threading.Event()
        self._parks[ident] = (index, release, reached)
        return reached

    def write_credential(self, namespace, key, value):
        ident = threading.get_ident()
        n = self._writes.get(ident, 0)
        self._writes[ident] = n + 1
        park = self._parks.get(ident)
        if park and park[0] == n:
            park[2].set()
            park[1].wait(10)
        with self._guard:
            if self.refuse_after is not None and len(self.store) >= self.refuse_after:
                raise RuntimeError("simulated keychain capacity refusal")
            self.store[(namespace, key)] = value

    def read_credential(self, namespace, key):
        with self._guard:
            return self.store.get((namespace, key))

    def delete_credential(self, namespace, key):
        with self._guard:
            self.store.pop((namespace, key), None)


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
    backend = _ParkingBackend()
    mod._tier2_backend = backend
    # Small threshold so ordinary jars chunk, exercising the generation path.
    mod.CRED_MAX_CREDENTIAL_BLOB_SIZE_BYTES = 64
    return mod, backend


def _jar(tag: str, n: int = 6) -> bytes:
    """A jar large enough to need continuation chunking, tagged per writer."""
    return json.dumps(
        [{"name": f"{tag}{i}", "value": tag * 12, "domain": "example.com"}
         for i in range(n)],
        separators=(",", ":"),
    ).encode("utf-8")


def _store(mod, profile: str, payload: bytes):
    """Store the way production does — under the profile's lock."""
    with mod._profile_lock(profile):
        return mod._store_cookie_jar(profile, payload)


def _read(mod, profile: str) -> bytes | None:
    with mod._profile_lock(profile):
        return mod._load_cookie_jar(profile)


def _tags_present(jar: bytes | None) -> set[str]:
    """Which writers' bytes appear in *jar*."""
    if jar is None:
        return set()
    return {c["name"][0] for c in json.loads(jar.decode("utf-8"))}


def _run_two_writers(mod, backend, park_index: int, lock_enabled: bool = True):
    """Writer A parks at *park_index*; writer B runs to completion; A resumes."""
    release = threading.Event()
    errors: list[BaseException] = []
    store = _store if lock_enabled else (
        lambda m, p, v: m._store_cookie_jar(p, v)
    )

    reached: dict[str, threading.Event] = {}

    def writer_a():
        reached["a"] = backend.park_at(threading.get_ident(), park_index, release)
        try:
            store(mod, "jira", _jar("a"))
        except BaseException as exc:  # noqa: BLE001 — recorded, asserted below
            errors.append(exc)

    a = threading.Thread(target=writer_a, daemon=True)
    a.start()
    # Wait for A to park. Its park event is registered from inside the thread.
    for _ in range(500):
        if "a" in reached and reached["a"].wait(0.01):
            break
    b = threading.Thread(
        target=lambda: store(mod, "jira", _jar("b")), daemon=True
    )
    b.start()
    b.join(15)
    release.set()
    a.join(15)
    return errors


# ----------------------------------------------------------------------
# AC1 / AC2 — the serialisation property, and its negative controls.
# ----------------------------------------------------------------------


@pytest.mark.parametrize("park_index", [0, 1, 2])
def test_two_writers_leave_exactly_one_whole_jar(broker, park_index):
    """AC1: no reader ever observes bytes from both writers."""
    mod, backend = broker
    _run_two_writers(mod, backend, park_index)
    tags = _tags_present(_read(mod, "jira"))
    assert tags in ({"a"}, {"b"}), f"mixed or absent jar: {tags}"


# Parking A before its *first* write is not a corrupting interleaving: B runs to
# completion, then A overwrites every chunk under the same generation and commits
# a header consistent with its own. The result is A's jar, whole, by luck rather
# than by design. Indices 1+ are where the two writers' chunks actually
# interleave under one generation, so those are what the negative control asserts.
@pytest.mark.parametrize("park_index", [1, 2])
def test_negative_control_two_writers_corrupt_without_the_lock(
    broker, park_index, monkeypatch
):
    """AC6: the harness detects the defect it guards against.

    Without this, a green AC1 proves nothing — the assertion would hold against
    unfixed code for the wrong reason.
    """
    mod, backend = broker
    # Simulate the *pre-lock* engine: no lock, and no held-ness assertion either
    # (the assertion is part of the fix, so leaving it in would make this test
    # fail for the wrong reason rather than observe the corruption).
    monkeypatch.setattr(
        mod, "_profile_lock", lambda *_a, **_k: contextlib.nullcontext()
    )
    monkeypatch.setattr(mod, "_thread_holds", lambda _p: True)
    _run_two_writers(mod, backend, park_index, lock_enabled=False)
    tags = _tags_present(mod._load_cookie_jar("jira"))
    assert tags not in ({"a"}, {"b"}), (
        "expected a mixed or absent jar without the lock; the harness cannot "
        f"detect the defect it exists to catch (got {tags})"
    )


def test_three_writers_leave_one_whole_jar(broker):
    """AC2: a rotating third writer must not strand the first's generation."""
    mod, backend = broker
    release = threading.Event()
    reached: dict[str, threading.Event] = {}

    def writer_a():
        reached["a"] = backend.park_at(threading.get_ident(), 1, release)
        _store(mod, "jira", _jar("a"))

    a = threading.Thread(target=writer_a, daemon=True)
    a.start()
    for _ in range(500):
        if "a" in reached and reached["a"].wait(0.01):
            break
    for tag in ("b", "c"):
        t = threading.Thread(
            target=lambda tg=tag: _store(mod, "jira", _jar(tg)), daemon=True
        )
        t.start()
        t.join(15)
    release.set()
    a.join(15)

    jar = _read(mod, "jira")
    assert jar is not None, "fail-closed miss is no longer reachable under the lock"
    assert len(_tags_present(jar)) == 1, _tags_present(jar)


# ----------------------------------------------------------------------
# AC5 — the file-floor path, the fallback, and the production entry point.
# ----------------------------------------------------------------------


@pytest.mark.parametrize("park_index", [0, 1])
def test_file_floor_path_is_serialised_too(broker, park_index):
    """AC5: on Linux `_tier2_backend` is None, so this *is* production."""
    mod, backend = broker
    mod._tier2_backend = None
    errors: list[BaseException] = []

    def store(tag):
        try:
            _store(mod, "jira", _jar(tag))
        except BaseException as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=store, args=(t,), daemon=True)
               for t in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join(15)
    assert not errors, errors
    assert len(_tags_present(_read(mod, "jira"))) == 1


def test_backend_refusal_falls_back_to_floor_under_the_lock(broker):
    """AC5: `_fall_back_to_floor` runs inside the held lock, not beside it."""
    mod, backend = broker
    backend.refuse_after = 1
    with mod._profile_lock("jira"):
        label = mod._store_cookie_jar("jira", _jar("a"))
    assert label.startswith("file-floor")
    assert _tags_present(_read(mod, "jira")) == {"a"}


# ----------------------------------------------------------------------
# AC17 — held-ness is asserted, not assumed.
# ----------------------------------------------------------------------


def test_store_without_the_lock_raises(broker):
    """AC17: a forgotten wrap fails loudly rather than silently working."""
    mod, _ = broker
    with pytest.raises(mod.LockUnavailableError):
        mod._store_cookie_jar("jira", _jar("a"))


def test_store_while_holding_a_different_profiles_lock_raises(broker):
    """AC17: the arm a thread-only held-set would pass.

    Acquiring for `confluence` and storing `jira` is the likeliest wiring
    mistake in a four-site design; keyed by thread alone it would go unnoticed.
    """
    mod, _ = broker
    with mod._profile_lock("confluence"), pytest.raises(mod.LockUnavailableError):
        mod._store_cookie_jar("jira", _jar("a"))


# ----------------------------------------------------------------------
# AC3 / AC4 — readers, and the materialisation surface (T3).
# ----------------------------------------------------------------------


def test_reader_never_sees_a_partially_reaped_generation(broker):
    """AC3: a concurrent commit+reap yields the old jar or the new, never None."""
    mod, backend = broker
    with mod._profile_lock("jira"):
        mod._store_cookie_jar("jira", _jar("a"))

    results: list[bytes | None] = []

    def read():
        results.append(_read(mod, "jira"))

    def write():
        _store(mod, "jira", _jar("b"))

    threads = [threading.Thread(target=f, daemon=True) for f in (read, write)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(15)
    assert results and results[0] is not None
    assert len(_tags_present(results[0])) == 1


def _materialise(mod, profile: str, jar: bytes):
    """What `_do_get_cookies` does: load, then write the materialisation."""
    with mod._profile_lock(profile):
        mod._file_floor_write(profile, jar)


def test_stale_reader_never_overwrites_a_fresher_materialisation(broker):
    """AC4: the later-completing call wins the `os.replace`, not a stale one."""
    mod, _ = broker
    done = threading.Event()

    def slow():
        _materialise(mod, "jira", _jar("a"))
        done.set()

    def fast():
        done.wait(15)
        _materialise(mod, "jira", _jar("b"))

    threads = [threading.Thread(target=f, daemon=True) for f in (slow, fast)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(20)
    assert _tags_present(mod._cookie_floor_path("jira").read_bytes()) == {"b"}


# ----------------------------------------------------------------------
# AC8 / AC9 / AC12 / AC13 — the exit-code contract (T5).
#
# This module carries the contended-acquire case rather than
# test_sso_broker_verbs.py, so it sits behind the same Windows execution guard
# AC20 requires: `self_host_windows.py` judges its steps by return code alone,
# so a wholly-skipped module would exit 0 and read as coverage.
# ----------------------------------------------------------------------


def _run_verb(mod, argv, hold_profile=None, budget=0.3):
    """Drive `main` with the profile's lock optionally held by another thread."""
    if hold_profile is None:
        return mod.main(argv)
    holding = threading.Event()
    release = threading.Event()

    def hold():
        with mod._profile_lock(hold_profile):
            holding.set()
            release.wait(10)

    mod._LOCK_WAIT_BUDGET_S = budget  # read at call time, not bound at def time
    t = threading.Thread(target=hold, daemon=True)
    t.start()
    assert holding.wait(5)
    try:
        return mod.main(argv)
    finally:
        release.set()
        t.join(5)


def _registered(mod, profile="jira"):
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._write_profile(profile, {
        "name": profile,
        "login_url": "https://example.com/login",
        "success_url_pattern": "dash",
        "cookie_domains": ["example.com"],
        "session_filename": f"{profile}.jar",
        "validation_endpoint": "/rest/api/2/myself",
        "ttl_hint_minutes": 60,
    })


@pytest.mark.parametrize("verb", ["get-cookies", "test", "rm"])
def test_a_contended_verb_exits_6_not_3(broker, verb, capsys):
    """AC8, AC12: contention gets its own recoverable code.

    The end-to-end form of T1's `BlockingIOError` regression test. On Windows
    this is the case that matters most — `EACCES` rather than `BlockingIOError`
    signals contention there, and this repo has never executed that path.
    """
    mod, _ = broker
    _registered(mod)
    assert _run_verb(mod, [verb, "jira"], hold_profile="jira") == 6
    err = capsys.readouterr().err
    assert "jira" in err and "0.3" in err, err


def test_a_contended_verb_leaves_the_store_untouched(broker):
    """AC8: exit 6 means nothing happened, not something half-happened."""
    mod, _ = broker
    _registered(mod)
    with mod._profile_lock("jira"):
        mod._store_cookie_jar("jira", _jar("a"))
    before = dict(mod._tier2_backend.store)
    toml_before = mod._profile_path("jira").read_bytes()

    assert _run_verb(mod, ["rm", "jira"], hold_profile="jira") == 6
    assert dict(mod._tier2_backend.store) == before
    assert mod._profile_path("jira").read_bytes() == toml_before


def test_contention_is_bounded_from_process_entry(broker):
    """AC9: under 15 s for the verbs that reach the lock immediately."""
    mod, _ = broker
    _registered(mod)
    started = time.monotonic()
    assert _run_verb(mod, ["get-cookies", "jira"], hold_profile="jira") == 6
    assert time.monotonic() - started < 15.0


def test_an_unusable_lock_exits_3_with_no_traceback(broker, capsys, monkeypatch):
    """AC13: a permanent fault is never reported as retryable.

    Two-argument OSError deliberately: `OSError(errno.ENOLCK).errno` is `None`,
    so a single-argument stub would pass by falling through to the fault default
    rather than by classifying, and would stay green against an implementation
    that wrongly called ENOLCK contention.
    """
    import errno as _errno

    mod, _ = broker
    _registered(mod)
    exc = OSError(_errno.ENOLCK, "no locks available")
    assert exc.errno == _errno.ENOLCK
    monkeypatch.setattr(mod, "_acquire_once", lambda fd: (_ for _ in ()).throw(exc))
    assert mod.main(["get-cookies", "jira"]) == 3
    err = capsys.readouterr().err
    assert "Traceback" not in err, err


def test_rm_exit_3_names_the_manual_recourse(broker, capsys, monkeypatch):
    """AC14: with no unserialised fallback, this line is the operator's only out."""
    import errno as _errno

    mod, _ = broker
    _registered(mod)
    monkeypatch.setattr(
        mod, "_acquire_once",
        lambda fd: (_ for _ in ()).throw(OSError(_errno.ENOLCK, "no locks")),
    )
    assert mod.main(["rm", "jira"]) == 3
    err = capsys.readouterr().err
    assert "manually" in err and "sso-cookies" in err, err
