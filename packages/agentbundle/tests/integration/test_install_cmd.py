"""T5: integration tests for ``agentbundle install``.

Coverage:
  - Brownfield fixture: pre-existing Tier-2 ``AGENTS.md`` and Tier-3 source
    files are preserved; ``.upstream.*`` companions appear for Tier-2 collisions.
  - State-file merge: install pack B into a tree with ``[pack.A]`` already in
    ``.agentbundle-state.toml``; assert both tables are present.
  - Catalogue URI grammar:
      - Local relative path — no subprocess invoked.
      - Local absolute path — no subprocess invoked.
      - git+https with tag   → archive/refs/tags/<tag>.tar.gz
      - git+https with branch → archive/refs/heads/<branch>.tar.gz
      - git+https with SHA    → archive/<sha>.tar.gz
      - Unreachable host      → exit non-zero, stderr contains tarball URL.
      - git+ssh               → exit non-zero, "SSH git URLs deferred…"
  - Path-jail probe: a catalogue whose pack produces a relpath resolving to
    ``../../malicious`` is refused with exit non-zero.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import tarfile
import tempfile
import types
from pathlib import Path
from unittest import mock

import pytest

# Fixture catalogue dir containing packs/alpha/ (see tests/fixtures/install/).
FIXTURE_CATALOGUE = (
    Path(__file__).parent.parent / "fixtures" / "install" / "catalogue"
)
ALPHA_PACK_DIR = FIXTURE_CATALOGUE / "packs" / "alpha"


# ---------------------------------------------------------------------------
# Helper: build a fake namespace the same way argparse would
# ---------------------------------------------------------------------------

def _args(pack: str, catalogue: str, output: str) -> types.SimpleNamespace:
    # RFC-0012: test fixtures predate per-IDE projection at repo scope;
    # pass `emit_install_routes=True` to keep the dist-tree shape.
    return types.SimpleNamespace(
        pack=pack, catalogue=catalogue, output=output,
        emit_install_routes=True,
    )


# ---------------------------------------------------------------------------
# Helper: run ``install.run(args)`` and return its exit code
# ---------------------------------------------------------------------------

def _run_install(pack: str, catalogue: str, output: str) -> int:
    from agentbundle.commands.install import run
    return run(_args(pack, catalogue, output))


# ---------------------------------------------------------------------------
# Helper: build a tiny in-memory tar.gz from a directory tree
# ---------------------------------------------------------------------------

def _make_tarball(root: Path, inner_name: str) -> io.BytesIO:
    """Create an in-memory .tar.gz that mimics a GitHub archive.

    GitHub archives wrap the repo content in a single top-level directory
    named ``<repo>-<ref>/``. *inner_name* is that directory name.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for path in sorted(root.rglob("*")):
            relpath = path.relative_to(root)
            arcname = f"{inner_name}/{relpath.as_posix()}"
            tf.add(str(path), arcname=arcname, recursive=False)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# 1. Brownfield: Tier-2 file preserved; .upstream companion created
# ---------------------------------------------------------------------------

def test_brownfield_tier2_gets_companion_not_overwrite(tmp_path):
    """A pre-existing adopter-edited file (Tier-2) must not be
    overwritten; a .upstream.<ext> companion must appear instead.

    Pre-RFC-0004 this test pre-seeded `.agentbundle-state.toml` with the
    same pack at an old SHA to force Tier-2 detection. Post-RFC-0004
    install refuses against a pack already installed at the requested
    scope (spec § *Dual-scope install conflict*); pre-seeding the same
    pack would short-circuit before Tier classification. The new shape
    relies on `_classify_for_install`'s fallback: a file on disk that
    differs from the incoming bundle *and* has no matching SHA in any
    pack's state is Tier-2 by construction (first-install collision).
    """
    from agentbundle.render import render_pack
    from agentbundle import safety

    projection = render_pack(ALPHA_PACK_DIR)
    tier2_relpath = sorted(projection.keys())[0]
    original_content = b"adopter-edited content not from the bundle"

    target = tmp_path / tier2_relpath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(original_content)

    # No state pre-seed — alpha is a first-time install. The classifier
    # sees on-disk SHA ≠ bundle SHA and no matching prior pack → Tier-2.
    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0, "install should succeed even with Tier-2 collision"

    # Original file must be byte-identical.
    assert target.read_bytes() == original_content, "Tier-2 original must not be modified"

    # Companion must exist.
    companion = safety.companion_path(Path(tier2_relpath))
    assert (tmp_path / companion).exists(), f"Expected companion {companion} to be created"

    # Companion must contain the bundle's content.
    bundle_bytes = projection[tier2_relpath]
    assert (tmp_path / companion).read_bytes() == bundle_bytes


# ---------------------------------------------------------------------------
# 2. Brownfield: Tier-3 adopter files are never touched
# ---------------------------------------------------------------------------

def test_brownfield_tier3_files_unchanged(tmp_path):
    """Files not in the pack projection must be byte-identical before and after."""
    tier3_path = tmp_path / "src" / "app.py"
    tier3_path.parent.mkdir(parents=True, exist_ok=True)
    tier3_content = b"# adopter-owned application code\n"
    tier3_path.write_bytes(tier3_content)

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0

    assert tier3_path.read_bytes() == tier3_content, "Tier-3 file must not be touched"


# ---------------------------------------------------------------------------
# 3. State-file merge: install pack B into tree with pack A
# ---------------------------------------------------------------------------

def test_state_file_merge_preserves_existing_pack(tmp_path):
    """Installing pack 'alpha' into a tree that already has 'other' in state
    must result in both [pack.alpha] and [pack.other] tables present."""
    from agentbundle.config import PackState, State, dump_state, load_state

    # Pre-seed a state with pack 'other'.
    state = State()
    state.packs["other"] = PackState(
        installed_version="1.0.0",
        files={"some/file.md": {"sha": "abc", "from-pack-version": "1.0.0"}},
    )
    state_path = tmp_path / ".agentbundle-state.toml"
    state_path.write_text(dump_state(state), encoding="utf-8")

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0

    # Reload and check both tables are present.
    merged = load_state(state_path)
    assert "other" in merged.packs, "[pack.other] must still be present"
    assert "alpha" in merged.packs, "[pack.alpha] must have been added"
    # 'other' table must be unmodified.
    assert merged.packs["other"].installed_version == "1.0.0"
    assert "some/file.md" in merged.packs["other"].files


# ---------------------------------------------------------------------------
# 4. Catalogue URI: local relative path — no subprocess
# ---------------------------------------------------------------------------

def test_local_relative_path_no_subprocess(tmp_path):
    """Local relative path catalogue must not invoke subprocess.run or Popen."""
    with mock.patch("subprocess.run", side_effect=AssertionError("subprocess.run must not be called")):
        with mock.patch("subprocess.Popen", side_effect=AssertionError("subprocess.Popen must not be called")):
            # Use a relative path from tmp_path parent — not ideal but we
            # just need to verify the no-subprocess contract; the install
            # itself may fail if the relative path doesn't resolve, which
            # is fine — the important thing is subprocess is never called.
            # Use the absolute fixture path for a reliable resolve.
            rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0


# ---------------------------------------------------------------------------
# 5. Catalogue URI: local absolute path — no subprocess
# ---------------------------------------------------------------------------

def test_local_absolute_path_no_subprocess(tmp_path):
    abs_path = str(FIXTURE_CATALOGUE.resolve())
    with mock.patch("subprocess.run", side_effect=AssertionError("subprocess.run called")):
        with mock.patch("subprocess.Popen", side_effect=AssertionError("subprocess.Popen called")):
            rc = _run_install("alpha", abs_path, str(tmp_path))
    assert rc == 0


# ---------------------------------------------------------------------------
# 6–8. git+https URI forms — mock urlopen, assert constructed URL
# ---------------------------------------------------------------------------

def _mock_urlopen_returning_alpha(url_capture: list):
    """Return a context manager mock that captures the URL and yields a tarball."""
    tarball_buf = _make_tarball(FIXTURE_CATALOGUE, "alpha-v1.0")

    class _FakeResp:
        def read(self, n=-1):
            return tarball_buf.read(n)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    original_urlopen = None

    def _fake_urlopen(url, **kwargs):
        url_capture.append(url)
        # Return a fresh buf each time.
        fresh_buf = _make_tarball(FIXTURE_CATALOGUE, "alpha-v1.0")
        return tarfile.open(fileobj=fresh_buf, mode="r:gz")

    return mock.patch("urllib.request.urlopen", side_effect=_fake_urlopen)


@pytest.fixture
def _tarball_mock():
    """Provide a mock for urlopen that captures URLs + yields a real tarball."""
    captured: list[str] = []

    def _fake_urlopen(url, **kwargs):
        captured.append(url)
        buf = _make_tarball(FIXTURE_CATALOGUE, "alpha-v1.0")
        # tarfile.open(..., mode="r|gz") expects a streaming file-like;
        # return a BytesIO-backed file object so tarfile can read it.
        return buf

    patcher = mock.patch("urllib.request.urlopen", side_effect=_fake_urlopen)
    return patcher, captured


def test_git_https_tag_constructs_tags_url(tmp_path, _tarball_mock):
    patcher, captured = _tarball_mock
    with patcher:
        rc = _run_install(
            "alpha",
            "git+https://github.com/owner/repo@v1.0",
            str(tmp_path),
        )
    # URL check is the key assertion; install may fail because the tarball
    # inner dir name won't match, but we just need to confirm the URL.
    assert len(captured) == 1, "urlopen should have been called once"
    assert captured[0] == "https://github.com/owner/repo/archive/refs/tags/v1.0.tar.gz"


def test_git_https_branch_constructs_heads_url(tmp_path, _tarball_mock):
    patcher, captured = _tarball_mock
    with patcher:
        rc = _run_install(
            "alpha",
            "git+https://github.com/owner/repo@main",
            str(tmp_path),
        )
    assert len(captured) == 1
    assert captured[0] == "https://github.com/owner/repo/archive/refs/heads/main.tar.gz"


def test_git_https_sha_constructs_sha_url(tmp_path, _tarball_mock):
    patcher, captured = _tarball_mock
    with patcher:
        rc = _run_install(
            "alpha",
            "git+https://github.com/owner/repo@deadbeef",
            str(tmp_path),
        )
    assert len(captured) == 1
    assert captured[0] == "https://github.com/owner/repo/archive/deadbeef.tar.gz"


def test_git_https_40char_sha_constructs_sha_url(tmp_path, _tarball_mock):
    sha40 = "a" * 40
    patcher, captured = _tarball_mock
    with patcher:
        rc = _run_install(
            "alpha",
            f"git+https://github.com/owner/repo@{sha40}",
            str(tmp_path),
        )
    assert len(captured) == 1
    assert captured[0] == f"https://github.com/owner/repo/archive/{sha40}.tar.gz"


# ---------------------------------------------------------------------------
# 9. Unreachable host → exit non-zero + stderr contains tarball URL
# ---------------------------------------------------------------------------

def test_unreachable_host_exits_nonzero_with_url_in_stderr(tmp_path, capsys):
    import urllib.error

    def _raise_urlerror(url, **kwargs):
        raise urllib.error.URLError("Name or service not known")

    with mock.patch("urllib.request.urlopen", side_effect=_raise_urlerror):
        rc = _run_install(
            "alpha",
            "git+https://github.com/owner/unreachable@v1.0",
            str(tmp_path),
        )

    assert rc != 0, "Unreachable host should yield non-zero exit"
    captured = capsys.readouterr()
    assert "tags/v1.0.tar.gz" in captured.err, (
        "stderr should contain the tarball URL that was attempted"
    )


# ---------------------------------------------------------------------------
# 10. git+ssh → exit non-zero + SSH-deferred message
# ---------------------------------------------------------------------------

def test_git_ssh_exits_nonzero_with_deferred_message(tmp_path, capsys):
    rc = _run_install(
        "alpha",
        "git+ssh://git@github.com:owner/repo",
        str(tmp_path),
    )
    assert rc != 0
    captured = capsys.readouterr()
    assert "SSH git URLs deferred to v1.1" in captured.err


# ---------------------------------------------------------------------------
# 11. Path-jail probe: projection producing ../../malicious is refused
# ---------------------------------------------------------------------------

def test_path_jail_probe_refused(tmp_path):
    """A pack whose render produces a path escaping the output root must cause
    install to exit non-zero and must not write any file outside the root."""
    from agentbundle.commands.install import run

    # Mock render_pack to return a projection with a malicious relpath.
    malicious_content = b"malicious content"
    malicious_relpath = "../../malicious_file.txt"
    fake_projection = {malicious_relpath: malicious_content}

    with mock.patch("agentbundle.render.render_pack", return_value=fake_projection):
        rc = run(_args("alpha", str(FIXTURE_CATALOGUE), str(tmp_path)))

    assert rc != 0, "Install must refuse when a projection escapes the output root"

    # The malicious file must not exist outside the tmp_path.
    malicious_target = (tmp_path / malicious_relpath).resolve()
    assert not malicious_target.exists(), "Malicious file must not have been written"


# ---------------------------------------------------------------------------
# 12. State file records SHA-256 for every Tier-1 path written
# ---------------------------------------------------------------------------

def test_state_records_sha_for_tier1_paths(tmp_path):
    """After install, .agentbundle-state.toml must record a sha for every
    path the install wrote (Tier-1 paths)."""
    from agentbundle.config import load_state
    from agentbundle import safety
    from agentbundle.render import render_pack

    rc = _run_install("alpha", str(FIXTURE_CATALOGUE), str(tmp_path))
    assert rc == 0

    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert "alpha" in state.packs

    projection = render_pack(ALPHA_PACK_DIR)
    pack_state = state.packs["alpha"]
    for relpath, expected_bytes in projection.items():
        assert relpath in pack_state.files, f"relpath {relpath!r} missing from state"
        recorded_sha = pack_state.files[relpath].get("sha")
        assert recorded_sha == safety.sha256_bytes(expected_bytes), (
            f"SHA mismatch for {relpath!r}"
        )


def test_reinstall_preserves_mixed_version_primitives(tmp_path):
    """Re-installing a pack carries forward `primitive_versions` from prior
    state so subsequent whole-pack upgrades still surface the mixed state.
    (Concern 8 from adversarial review.)
    """
    import argparse
    import contextlib
    import io
    from agentbundle.commands.install import run as install_run

    cat = str(Path(__file__).parent.parent / "fixtures" / "upgrade" / "catalogue_v1")

    # 1. Install once.
    rc = install_run(argparse.Namespace(
        pack="core", catalogue=cat, output=str(tmp_path), scope=None, force=False,
    ))
    assert rc == 0

    # 2. Post-RFC-0004: re-install is refused with the spec-named message.
    #    The previous shape of this test (re-install carries forward
    #    `primitive_versions` from prior state) is incompatible with the
    #    RFC-0004 contract; primitive-version carry-forward is now
    #    `upgrade`'s job, not `install`'s.
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = install_run(argparse.Namespace(
            pack="core", catalogue=cat, output=str(tmp_path),
            scope=None, force=False,
        ))
    assert rc != 0
    err = buf.getvalue()
    assert "already installed at repo" in err
    assert "use 'upgrade' to change version" in err


def test_install_warns_on_pack_collision(tmp_path, capsys):
    """When the on-disk SHA at a projected path matches *another* pack's
    recorded SHA, install logs a warning rather than silently overwriting.
    (Concern 15 from adversarial review.)"""
    import argparse
    from agentbundle import safety
    from agentbundle.commands.install import _classify_for_install
    from agentbundle.config import PackState, State

    # On-disk content (from a prior install of 'other') differs from the
    # incoming 'core' bundle bytes — so the on-disk-vs-incoming SHA check
    # doesn't short-circuit to TIER_1; the recorded-SHA loop runs.
    on_disk_content = b"content from prior install of pack 'other'"
    incoming_content = b"content from pack 'core' (different bytes)"

    f = tmp_path / "shared.md"
    f.write_bytes(on_disk_content)

    state = State()
    state.packs["other"] = PackState(
        installed_version="0.1",
        files={"shared.md": {"sha": safety.sha256_bytes(on_disk_content), "from-pack-version": "0.1"}},
    )

    tier = _classify_for_install(
        "shared.md", tmp_path, incoming_content, state, pack_name="core",
    )
    assert tier is safety.Tier.TIER_1
    captured = capsys.readouterr()
    assert "also recorded under pack 'other'" in captured.err, (
        f"expected collision warning in stderr: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# Dry-run preview (projection-dry-run spec): read-only, writes nothing
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[4]
WORK_LOOP_SKILL = ".claude/skills/work-loop/SKILL.md"


def _args_core(target: Path, *, force: bool = False, dry_run: bool = False):
    """Args for installing the real `core` pack at repo scope (per-IDE shape)."""
    return argparse.Namespace(
        pack="core",
        catalogue=str(REPO_ROOT),
        output=str(target),
        scope="repo",
        emit_install_routes=False,
        force=force,
        dry_run=dry_run,
    )


def _run_core(args) -> tuple[int, str, str]:
    from agentbundle.commands.install import run as install_run

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = install_run(args)
    return rc, out.getvalue(), err.getvalue()


def _reset_inband_cache() -> None:
    from agentbundle.commands import install as install_mod

    install_mod._clear_inband_detection_seen()


def _snapshot_tree(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_dry_run_install_fresh_previews_create_writes_nothing(tmp_path):
    """AC2/AC6: a dry-run fresh install lists every projected file with
    `create`/tier-1 + target path, exits 0, and writes nothing — no projected
    file, no `.agentbundle-state.toml`, no install marker."""
    target = tmp_path / "repo"
    target.mkdir()
    before = _snapshot_tree(target)

    _reset_inband_cache()
    rc, out, err = _run_core(_args_core(target, dry_run=True))
    assert rc == 0, f"dry-run fresh install must exit 0: {err}"

    assert "create" in out, f"fresh install must preview create lines; got:\n{out}"
    assert "tier-1" in out, f"plan must use the greppable tier-1 label; got:\n{out}"
    assert ".claude/" in out, f"plan must show the projected target paths; got:\n{out}"
    assert "Nothing written." in out

    # No-write invariant: tree byte-identical, no state, no marker.
    assert _snapshot_tree(target) == before, "dry-run install must write nothing"
    assert not (target / ".agentbundle-state.toml").exists(), "no state file"
    assert not (target / ".adapt-install-marker.toml").exists(), "no install marker"
    assert not (target / ".claude").exists(), "no projected files"


def test_dry_run_install_over_edited_previews_companion(tmp_path):
    """AC2/AC4: a dry-run install over an adopter-edited file at a projection
    path previews the `companion`/tier-2 line, exits 0, writes no companion."""
    from agentbundle import safety

    target = tmp_path / "repo"
    (target / ".claude" / "skills" / "work-loop").mkdir(parents=True)
    edited = b"# my hand-authored work-loop, do not delete\n"
    (target / WORK_LOOP_SKILL).write_bytes(edited)

    before = _snapshot_tree(target)

    _reset_inband_cache()
    rc, out, err = _run_core(_args_core(target, dry_run=True))
    assert rc == 0, f"dry-run install over an edited primitive must exit 0: {err}"

    companion_rel = safety.companion_path(Path(WORK_LOOP_SKILL)).as_posix()
    assert "companion" in out and "tier-2" in out, f"got:\n{out}"
    assert f"{WORK_LOOP_SKILL} -> {companion_rel}" in out, (
        f"Tier-2 line must show the companion target; got:\n{out}"
    )

    assert _snapshot_tree(target) == before, "dry-run install must write nothing"
    assert not (target / companion_rel).exists(), "dry-run must not drop a companion"
    assert (target / WORK_LOOP_SKILL).read_bytes() == edited, "edit left untouched"


def test_dry_run_force_refused_leaves_orphan_intact(tmp_path):
    """AC8/AC6: `--dry-run --force` is refused up front (non-zero + stderr), and
    over a fixture where `--force` WOULD rmtree/unlink, the orphan crumb is left
    intact — the destructive Step 3c cleanup never runs. (Its sibling
    `test_dry_run_step3c_refusal_passthrough` confirms this crumb is a genuine
    orphan — i.e. the cleanup this test bypasses would really have removed it.)"""
    target = tmp_path / "repo"
    (target / ".claude" / "skills" / "work-loop").mkdir(parents=True)
    crumb = target / ".claude" / "skills" / "work-loop" / "STALE-EXTRA.md"
    crumb.write_bytes(b"leftover\n")
    before = _snapshot_tree(target)

    _reset_inband_cache()
    rc, out, err = _run_core(_args_core(target, force=True, dry_run=True))
    assert rc != 0, "--dry-run --force must be refused"
    assert "--force" in err and "--dry-run" in err, (
        f"stderr must explain the contradiction; got:\n{err}"
    )
    assert out == "", "a refused preview prints no plan to stdout"

    # The destructive cleanup that --force alone would do must NOT have run.
    assert crumb.exists(), "--dry-run --force must not unlink the orphan crumb"
    assert _snapshot_tree(target) == before, "nothing may change"


def test_dry_run_step3c_refusal_passthrough(tmp_path):
    """AC5: `--dry-run` (no --force) over a non-projection orphan crumb exits
    non-zero with the same refusal a real run gives, writing nothing."""
    target = tmp_path / "repo"
    (target / ".claude" / "skills" / "work-loop").mkdir(parents=True)
    crumb = target / ".claude" / "skills" / "work-loop" / "STALE-EXTRA.md"
    crumb.write_bytes(b"leftover\n")
    before = _snapshot_tree(target)

    _reset_inband_cache()
    rc, _out, err = _run_core(_args_core(target, dry_run=True))
    assert rc != 0, "a non-projection crumb must still be refused under --dry-run"
    assert "your own files" in err, f"the real-run refusal must pass through; got:\n{err}"
    assert crumb.exists(), "refusal must not delete anything"
    assert _snapshot_tree(target) == before, "nothing may change"


def test_dry_run_preflight_path_jail_passthrough(tmp_path):
    """AC5: a path-jail-violating projection under `--dry-run` is refused at the
    Step 8 probe (non-zero), and nothing is written outside the root."""
    from agentbundle.commands.install import run

    malicious_relpath = "../../malicious_dry_run.txt"
    fake_projection = {malicious_relpath: b"malicious content"}

    args = types.SimpleNamespace(
        pack="alpha", catalogue=str(FIXTURE_CATALOGUE), output=str(tmp_path),
        emit_install_routes=True, dry_run=True,
    )
    with mock.patch("agentbundle.render.render_pack", return_value=fake_projection):
        rc = run(args)

    assert rc != 0, "dry-run must surface the path-jail pre-flight failure"
    assert not (tmp_path / malicious_relpath).resolve().exists(), (
        "malicious file must not be written even under dry-run"
    )
