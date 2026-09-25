# Stored and validated in PLAN's T4 Tests: subsection. The subject is loaded
# under a pack-and-skill-qualified module name via `spec_from_file_location`,
# never by putting `scripts/` on `sys.path` — the catalogue authoring standard
# forbids the latter because one bare name would then bind to whichever pack's
# directory landed first.
from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import time
from pathlib import Path

import pytest

_PACK_ROOT = Path(__file__).resolve().parents[3]
_FM_PKG = _PACK_ROOT / ".apm" / "skills" / "flow-metrics" / "scripts" / "flow_metrics"
_FM_NAME = "atlassian_flow_metrics"


@pytest.fixture(scope="module")
def fm():
    """Load `flow_metrics` under a unique pack-and-skill-qualified name."""
    spec = importlib.util.spec_from_file_location(
        _FM_NAME, _FM_PKG / "__init__.py", submodule_search_locations=[str(_FM_PKG)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def fm_cache(fm):
    return importlib.import_module(f"{_FM_NAME}.cache")


def _seed_stale_temp(root: Path, fm_cache) -> Path:
    cache_dir = root / ".context" / "flow-metrics" / "cache"
    cache_dir.mkdir(parents=True)
    stale = cache_dir / "abc123.jsonl.999.tmp"
    stale.write_text("{}\n", encoding="utf-8", newline="\n")
    old = time.time() - (fm_cache.STALE_TMP_AGE_SECONDS + 60)
    os.utime(stale, (old, old))
    return stale


_SCOPE_ARGS = ["--project", "PROJ", "--from", "2026-01-01", "--to", "2026-01-31"]


def _stub_fetch(fm, monkeypatch) -> dict:
    """Substitute the Jira fetch so no test reaches the network.

    `packs/AGENTS.md` requires a seam in front of an external binary, and
    without one these runs would make real Jira calls on any credentialed
    machine — slow, non-deterministic, and dependent on someone's instance.
    The seam also gives the liveness signal directly: reaching it proves the
    run travelled past the whole cache section.
    """
    import importlib

    per_issue = importlib.import_module(f"{_FM_NAME}.per_issue")
    seen = {"fetched": 0}

    def fake_rows(*_args, **_kwargs):
        seen["fetched"] += 1
        return iter(())

    monkeypatch.setattr(per_issue, "iter_per_issue_rows", fake_rows)
    return seen


def _spy_cleanup(fm_cache, monkeypatch) -> dict:
    """Record whether the stale-temp cleanup was invoked.

    `flow_metrics` imports it from `.cache` inside the pipeline function, so
    the name resolves against the module object at call time and patching it
    here intercepts.
    """
    seen = {"cleanup": 0}
    monkeypatch.setattr(
        fm_cache, "cleanup_stale_tmps", lambda _dir: seen.__setitem__("cleanup", seen["cleanup"] + 1)
    )
    return seen


# STUB: AC39
def test_inert_mode_does_not_invoke_the_stale_temp_cleanup(fm, fm_cache, tmp_path, monkeypatch):
    """Observes the decision directly rather than inferring it from the
    filesystem, because an absent side effect cannot distinguish suppression
    from an execution that never arrived.

    Liveness is the substituted fetch being reached. That seam sits after the
    whole cache section, so reaching it proves the run did the normal work
    rather than returning early, while leaving an implementation free to
    bypass every cache operation — `cache_key` included. Pinning an internal
    cache seam would reject a conforming inert mode; pinning an exit code
    would fail on any machine with working Jira credentials, because
    `flow-metrics` inherits the ambient environment.

    Red three ways: today argparse rejects the flag; an implementation that
    accepts it and returns early never reaches the fetch; one that accepts it
    without suppressing the cleanup trips the spy.
    """
    monkeypatch.chdir(tmp_path)
    fetched = _stub_fetch(fm, monkeypatch)
    seen = _spy_cleanup(fm_cache, monkeypatch)

    try:
        fm.main([*_SCOPE_ARGS, "--inert-cache"])
    except SystemExit as exc:
        pytest.fail(f"--inert-cache was rejected by the parser (exit {exc.code})")

    assert fetched["fetched"] == 1, (
        "the run never reached the fetch, so it did not travel past the cache "
        "section and a suppressed cleanup here proves nothing"
    )
    assert seen["cleanup"] == 0, "inert mode must not invoke the stale-temp cleanup"


def test_no_cache_alone_still_invokes_the_cleanup(fm, fm_cache, tmp_path, monkeypatch):
    """The control that makes the assertion above falsifiable: `--no-cache`
    reaches the same fetch and still invokes the cleanup, which is the one
    mutation it does not suppress and the whole reason a separate mode is
    needed. Green today and must stay green."""
    monkeypatch.chdir(tmp_path)
    fetched = _stub_fetch(fm, monkeypatch)
    seen = _spy_cleanup(fm_cache, monkeypatch)

    fm.main([*_SCOPE_ARGS, "--no-cache"])

    assert fetched["fetched"] == 1
    assert seen["cleanup"] == 1, "--no-cache is expected to still run the cleanup"


def test_cleanup_is_a_noop_when_the_cache_directory_is_absent(fm_cache, tmp_path):
    """Pins the other half of the correction: a bypassed run does not
    materialise `.context/`, because the directory is created only on the
    write path. Guards against a fix that creates the directory to clean it."""
    absent = tmp_path / ".context" / "flow-metrics" / "cache"

    fm_cache.cleanup_stale_tmps(absent)

    assert not absent.exists()


def _spy_cache_io(fm_cache, monkeypatch) -> dict:
    """Record whether the cache was read from or written to.

    Separate from the cleanup spy because these are different properties: a
    mode that suppressed the cleanup while reintroducing a read would satisfy
    the stale-temp pairing above and still touch the cache.
    """
    seen = {"read": 0, "write": 0}
    monkeypatch.setattr(
        fm_cache, "read_cache", lambda *_a, **_k: seen.__setitem__("read", seen["read"] + 1) or None
    )

    def _tee(_dir, _key, source):
        seen["write"] += 1
        return iter(list(source))

    monkeypatch.setattr(fm_cache, "write_cache_tee", _tee)
    return seen


def test_inert_mode_performs_no_cache_read_and_no_cache_write(
    fm, fm_cache, tmp_path, monkeypatch
):
    """The deferred half of the mode's contract, held as a regression
    assertion rather than a control: `--no-cache` satisfies it too, so it
    discriminates nothing on its own. It is what stops a later change from
    suppressing the cleanup while quietly restoring the read or the tee.

    Needs a completed fetch, which is why it sits here rather than in the
    approved stub — the read is consulted and the tee wrapped only once the
    run reaches the fetch section.
    """
    monkeypatch.chdir(tmp_path)
    fetched = _stub_fetch(fm, monkeypatch)
    io = _spy_cache_io(fm_cache, monkeypatch)

    fm.main([*_SCOPE_ARGS, "--inert-cache"])

    assert fetched["fetched"] == 1, "the run never reached the fetch"
    assert io["read"] == 0, "inert mode must not read the cache"
    assert io["write"] == 0, "inert mode must not write the cache"


def test_inert_mode_creates_no_cache_directory(fm, tmp_path, monkeypatch):
    """The directory is made only on the write path, so an inert run must
    leave the invocation tree without a `.context/` at all. Asserted over the
    real filesystem rather than a seam, because the property the composing
    view depends on is that nothing appeared on disk."""
    monkeypatch.chdir(tmp_path)
    _stub_fetch(fm, monkeypatch)

    fm.main([*_SCOPE_ARGS, "--inert-cache"])

    assert not (tmp_path / ".context").exists(), (
        "an inert run must not materialise the cache directory"
    )
