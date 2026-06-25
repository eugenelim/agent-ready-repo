"""Unit tests for the four-layer catalogue-source default resolver
(`agentbundle.source_defaults`) — RFC-0046 / ADR-0036.

Covers T1 (packaged default reader), T3 (editable detection, hardened), and
T4 (the precedence/validation composer + negative invariants). The keystone
real-`pip install -e` integration test lives in
`tests/integration/test_editable_source_detection.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentbundle.catalogue import CatalogueError
from agentbundle import source_defaults
from agentbundle.source_defaults import (
    _source_from_install_defaults,
    _detect_editable_source,
    _is_valid_source,
    _load_distribution,
    read_packaged_default,
    resolve_default_source,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeDist:
    """Stand-in for an `importlib.metadata.Distribution` — `read_text` returns
    the supplied `direct_url.json` body (or `None` for a missing record)."""

    def __init__(self, direct_url_json: str | None):
        self._raw = direct_url_json

    def read_text(self, name: str) -> str | None:
        if name == "direct_url.json":
            return self._raw
        return None


def _direct_url(path: Path, *, editable: bool = True, host: str = "") -> str:
    url = f"file://{host}{path.as_posix()}"
    return json.dumps({"url": url, "dir_info": {"editable": editable}})


def _make_markers(root: Path) -> None:
    (root / "packs").mkdir(parents=True, exist_ok=True)
    cp = root / ".claude-plugin"
    cp.mkdir(parents=True, exist_ok=True)
    (cp / "marketplace.json").write_text("{}", encoding="utf-8")


def _make_git(root: Path, *, as_file: bool = False) -> None:
    if as_file:
        (root / ".git").write_text("gitdir: /elsewhere/.git/worktrees/wt\n", encoding="utf-8")
    else:
        (root / ".git").mkdir(parents=True, exist_ok=True)


def _clone(tmp_path: Path, *, git_as_file: bool = False) -> tuple[Path, Path]:
    """Build clone/ with markers + .git at the root and a pkg subdir; return
    (clone_root, pkg_dir)."""
    clone = tmp_path / "clone"
    pkg = clone / "packages" / "agentbundle"
    pkg.mkdir(parents=True)
    _make_markers(clone)
    _make_git(clone, as_file=git_as_file)
    return clone, pkg


# ---------------------------------------------------------------------------
# T1 — packaged default
# ---------------------------------------------------------------------------


def test_packaged_default_ships_upstream_url():
    # Goal-based: the real bundled _data/install-defaults.toml reads back.
    assert read_packaged_default() == "git+https://github.com/eugenelim/agent-ready-repo"


@pytest.mark.parametrize(
    "text",
    [
        "",  # blank file
        "[defaults]\n",  # no source key
        '[defaults]\nsource = ""\n',  # empty source — the private-fork blank
        '[defaults]\nsource = "   "\n',  # whitespace-only
        "[other]\nx = 1\n",  # no [defaults] table
        "not = valid = toml\n",  # malformed
        "[defaults]\nsource = 42\n",  # non-string
    ],
)
def test_packaged_default_absent_or_empty_is_none(text):
    assert _source_from_install_defaults(text) is None


def test_packaged_default_parses_source():
    assert (
        _source_from_install_defaults('[defaults]\nsource = "git+https://github.com/x/y"\n')
        == "git+https://github.com/x/y"
    )


# ---------------------------------------------------------------------------
# T4 — the scheme/marker validation gate
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "file:///etc/passwd",
        "file:/etc/passwd",  # single-slash, no authority — the differential case
        "http://evil.example",
        "https://example.com",
        "git+ssh://git@github.com/x/y",
        "GIT+HTTPS://github.com/x/y",  # mis-cased — sink is case-sensitive
        "ftp://host/x",
        "",  # empty
    ],
)
def test_scheme_gate_rejects_non_git_https_urls(value):
    assert _is_valid_source(value) is False


def test_scheme_gate_accepts_git_https():
    assert _is_valid_source("git+https://github.com/eugenelim/agent-ready-repo") is True


def test_scheme_gate_accepts_local_path_with_markers(tmp_path):
    _make_markers(tmp_path)
    assert _is_valid_source(str(tmp_path)) is True


def test_scheme_gate_rejects_local_path_without_markers(tmp_path):
    assert _is_valid_source(str(tmp_path)) is False


def test_scheme_gate_windows_drive_is_local_branch_not_scheme():
    # C:\... routes to the local-path branch (no markers on this host → False),
    # NOT rejected as a "c" scheme — proves the drive-letter guard fires first.
    assert _is_valid_source(r"C:\definitely\nonexistent") is False


# ---------------------------------------------------------------------------
# T3 — editable detection
# ---------------------------------------------------------------------------


def test_editable_dist_none_returns_none():
    assert _detect_editable_source(None) is None


def test_editable_missing_direct_url_returns_none():
    assert _detect_editable_source(_FakeDist(None)) is None


def test_editable_false_returns_none(tmp_path):
    _, pkg = _clone(tmp_path)
    dist = _FakeDist(_direct_url(pkg, editable=False))
    assert _detect_editable_source(dist) is None


def test_editable_non_file_scheme_returns_none(tmp_path):
    raw = json.dumps({"url": "https://github.com/x/y", "dir_info": {"editable": True}})
    assert _detect_editable_source(_FakeDist(raw)) is None


def test_editable_non_localhost_host_rejected(tmp_path):
    _, pkg = _clone(tmp_path)
    dist = _FakeDist(_direct_url(pkg, host="evil.example"))
    assert _detect_editable_source(dist) is None


def test_editable_localhost_host_ok(tmp_path):
    clone, pkg = _clone(tmp_path)
    dist = _FakeDist(_direct_url(pkg, host="localhost"))
    assert _detect_editable_source(dist) == str(clone.resolve())


def test_editable_resolves_to_clone_root_git_dir(tmp_path):
    clone, pkg = _clone(tmp_path, git_as_file=False)
    dist = _FakeDist(_direct_url(pkg))
    assert _detect_editable_source(dist) == str(clone.resolve())


def test_editable_resolves_with_git_as_file(tmp_path):
    # Conductor worktree: .git is a regular file, not a directory.
    clone, pkg = _clone(tmp_path, git_as_file=True)
    dist = _FakeDist(_direct_url(pkg))
    assert _detect_editable_source(dist) == str(clone.resolve())


def test_editable_catalogue_equals_git_root_resolves(tmp_path):
    # Closed-interval bound: markers sit AT the .git root (the only valid match
    # sits at the boundary) — must resolve, not fall through.
    clone, pkg = _clone(tmp_path)
    dist = _FakeDist(_direct_url(pkg))
    assert _detect_editable_source(dist) == str(clone.resolve())


def test_editable_stops_at_first_match_inside_clone(tmp_path):
    # Markers planted in an intermediate dir inside the clone stop the walk at
    # first match (accident-guard residual) — returns the intermediate, not the
    # clone root.
    clone = tmp_path / "clone"
    intermediate = clone / "sub"
    pkg = intermediate / "pkg"
    pkg.mkdir(parents=True)
    _make_markers(clone)
    _make_git(clone)
    _make_markers(intermediate)
    dist = _FakeDist(_direct_url(pkg))
    assert _detect_editable_source(dist) == str(intermediate.resolve())


def test_editable_markers_above_git_root_not_matched(tmp_path, capsys):
    # A packs/ + marketplace.json pair in a parent ABOVE the .git root is never
    # matched (repo-bounded ascent); the clone itself has no markers.
    parent = tmp_path / "parent"
    clone = parent / "clone"
    pkg = clone / "packages" / "agentbundle"
    pkg.mkdir(parents=True)
    _make_markers(parent)  # planted ABOVE the repo boundary
    _make_git(clone)  # clone has .git but NO markers
    dist = _FakeDist(_direct_url(pkg))
    assert _detect_editable_source(dist) is None
    err = capsys.readouterr().err
    assert "editable install detected" in err
    assert "deferring to packaged default" in err


def test_editable_no_git_root_defers_with_diagnostic(tmp_path, capsys):
    # No enclosing .git anywhere → cannot bound the walk → diagnostic + None.
    pkg = tmp_path / "loose" / "pkg"
    pkg.mkdir(parents=True)
    dist = _FakeDist(_direct_url(pkg))
    assert _detect_editable_source(dist) is None
    err = capsys.readouterr().err
    assert "editable install detected" in err
    assert "deferring to packaged default" in err


def test_editable_symlink_canonicalized_before_walk(tmp_path):
    # A symlink in the recorded URL is collapsed by resolve() before the walk,
    # so the matched root stays inside the real clone.
    clone, pkg = _clone(tmp_path)
    link = tmp_path / "linkpkg"
    try:
        link.symlink_to(pkg, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform/filesystem")
    dist = _FakeDist(_direct_url(link))
    assert _detect_editable_source(dist) == str(clone.resolve())


# ---------------------------------------------------------------------------
# T4 — the composer: precedence, validation-skip, negatives, error
# ---------------------------------------------------------------------------


def _resolving_dist(tmp_path: Path) -> _FakeDist:
    _, pkg = _clone(tmp_path)
    return _FakeDist(_direct_url(pkg))


def test_layer1_explicit_wins_verbatim(tmp_path):
    # Layer 1 is an unvalidated pass-through — even a value the gate would
    # reject is returned untouched (today's behaviour).
    out = resolve_default_source(
        "http://explicit-passthrough",
        config_source="git+https://github.com/x/y",
        dist=_resolving_dist(tmp_path),
        read_packaged=lambda: "git+https://github.com/a/b",
    )
    assert out == "http://explicit-passthrough"


def test_layer2_outranks_layer3(tmp_path):
    out = resolve_default_source(
        None,
        config_source="git+https://github.com/x/y",
        dist=_resolving_dist(tmp_path),
        read_packaged=lambda: "git+https://github.com/a/b",
    )
    assert out == "git+https://github.com/x/y"


def test_layer3_when_no_config(tmp_path):
    clone, pkg = _clone(tmp_path)
    out = resolve_default_source(
        None,
        config_source=None,
        dist=_FakeDist(_direct_url(pkg)),
        read_packaged=lambda: "git+https://github.com/a/b",
    )
    assert out == str(clone.resolve())


def test_layer4_when_no_editable():
    out = resolve_default_source(
        None,
        config_source=None,
        dist=None,
        read_packaged=lambda: "git+https://github.com/a/b",
    )
    assert out == "git+https://github.com/a/b"


def test_invalid_config_source_skipped_to_layer3(tmp_path, capsys):
    clone, pkg = _clone(tmp_path)
    out = resolve_default_source(
        None,
        config_source="http://not-allowed",
        dist=_FakeDist(_direct_url(pkg)),
        read_packaged=lambda: "git+https://github.com/a/b",
    )
    assert out == str(clone.resolve())
    err = capsys.readouterr().err
    assert "config unset source" in err  # names the recovery path


def test_invalid_packaged_default_skipped():
    with pytest.raises(CatalogueError):
        resolve_default_source(
            None,
            config_source=None,
            dist=None,
            read_packaged=lambda: "http://not-allowed",
        )


def test_all_layers_empty_raises_with_recovery_paths():
    with pytest.raises(CatalogueError) as exc:
        resolve_default_source(
            None, config_source=None, dist=None, read_packaged=lambda: None
        )
    msg = str(exc.value)
    assert (
        "no catalogue source: pass --catalogue, run 'agentbundle config set "
        "source …', or pip install -e the catalogue" in msg
    )
    assert "config unset source" in msg  # the stale-value recovery path


def test_no_implicit_cwd_fallback(tmp_path, monkeypatch):
    # A cwd that happens to hold the markers must NEVER be consulted when no
    # layer yielded a source.
    _make_markers(tmp_path)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(CatalogueError):
        resolve_default_source(
            None, config_source=None, dist=None, read_packaged=lambda: None
        )


def test_editable_detected_but_no_root_falls_through_to_layer4(tmp_path, capsys):
    # Composed path (AC): editable detected, no catalogue root below the repo
    # boundary → stderr diagnostic AND layer 4 is returned (resolution continues).
    parent = tmp_path / "parent"
    clone = parent / "clone"
    pkg = clone / "packages" / "agentbundle"
    pkg.mkdir(parents=True)
    _make_markers(parent)  # markers above the boundary — not matchable
    _make_git(clone)
    out = resolve_default_source(
        None,
        config_source=None,
        dist=_FakeDist(_direct_url(pkg)),
        read_packaged=lambda: "git+https://github.com/a/b",
    )
    assert out == "git+https://github.com/a/b"  # layer 4 returned
    err = capsys.readouterr().err
    assert "editable install detected" in err
    assert "deferring to packaged default" in err


def test_resolution_writes_nothing(tmp_path, monkeypatch):
    # No-write invariant: a config file present on disk is byte-unchanged after
    # resolution on the layer-2, editable-deferred, layer-4, and error paths.
    from agentbundle.user_config import write_setting

    cfg = tmp_path / "config.toml"
    write_setting(cfg, "source", "git+https://github.com/x/y")
    before = cfg.read_bytes()

    clone, pkg = _clone(tmp_path)
    # layer 2 hit
    resolve_default_source(None, config_source="git+https://github.com/x/y", dist=None,
                           read_packaged=lambda: None)
    # layer 3 hit
    resolve_default_source(None, config_source=None, dist=_FakeDist(_direct_url(pkg)),
                           read_packaged=lambda: None)
    # editable-deferred + layer 4
    resolve_default_source(None, config_source="http://bad", dist=None,
                           read_packaged=lambda: "git+https://github.com/a/b")
    # all-layers-empty error path
    with pytest.raises(CatalogueError):
        resolve_default_source(None, config_source=None, dist=None,
                               read_packaged=lambda: None)
    assert cfg.read_bytes() == before


def test_load_distribution_prefers_record_bearing_dist(monkeypatch):
    # _load_distribution must prefer the dist carrying direct_url.json over a
    # shadowing egg-info — regardless of iteration order (the gateway-fork case).
    class _Meta(dict):
        pass

    class _D:
        def __init__(self, name, du):
            self.metadata = _Meta(Name=name)
            self._du = du

        def read_text(self, n):
            return self._du if n == "direct_url.json" else None

    egg = _D("agentbundle", None)  # no direct_url — the shadowing egg-info
    distinfo = _D("agentbundle", '{"dir_info":{"editable":true},"url":"file:///x"}')
    other = _D("requests", None)

    import importlib.metadata as md
    # egg-info first in iteration order — the record-bearing dist must still win.
    monkeypatch.setattr(md, "distributions", lambda: iter([other, egg, distinfo]))
    assert _load_distribution() is distinfo
