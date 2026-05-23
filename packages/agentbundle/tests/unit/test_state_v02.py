"""T13: .agent-ready-state.toml v0.2 + init-state --migrate.

Verifies AC #17 (RFC-0004) for the distribution-adapters spec:
  - Read of a v0.1 file returns every entry with implicit scope="repo".
  - Write-capable invocations against a v0.1 file refuse-and-explain.
  - `init-state --migrate` rewrites v0.1 → v0.2 idempotently.
  - User-scope state file lives at `~/.agent-ready/state.toml` (a
    namespaced dot-directory; the dir is created with 0o700 if absent).
"""

from __future__ import annotations

import argparse
import io
import contextlib
import os
import stat
import tempfile
import unittest
from pathlib import Path

import pytest

from agentbundle import config, safety
from agentbundle.commands import init_state


V01_FIXTURE = """
schema-version = "0.1"

[pack.core]
installed-version = "0.1.0"
source = "agent-ready-repo"
install-route = "cli"
primitives = ["skill"]

[pack.core.files]
"AGENTS.md" = { sha = "deadbeef", from-pack-version = "0.1.0" }
"""

V01_TWO_PACKS = """
schema-version = "0.1"

[pack.core]
installed-version = "0.1.0"
source = "agent-ready-repo"
install-route = "cli"
primitives = ["skill"]

[pack.core.files]
"AGENTS.md" = { sha = "aa", from-pack-version = "0.1.0" }

[pack.governance-extras]
installed-version = "0.1.0"
source = "agent-ready-repo"
install-route = "cli"
primitives = ["skill"]

[pack.governance-extras.files]
"docs/CHARTER.md" = { sha = "bb", from-pack-version = "0.1.0" }
"""


def _write(p: Path, text: str) -> Path:
    p.write_text(text, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Read-time compatibility — v0.1 file loads as all-repo-scope
# ---------------------------------------------------------------------------


def test_load_state_reads_v01_as_repo_scope(tmp_path):
    """Every [pack.<name>] entry in a v0.1 file gets implicit scope='repo'."""
    p = _write(tmp_path / "s.toml", V01_TWO_PACKS)
    state = config.load_state(p)
    assert state.schema_version == "0.1"
    assert state.packs["core"].scope == "repo"
    assert state.packs["governance-extras"].scope == "repo"


# ---------------------------------------------------------------------------
# Write-time refusal on v0.1
# ---------------------------------------------------------------------------


def test_load_state_for_write_refuses_v01(tmp_path):
    p = _write(tmp_path / "s.toml", V01_FIXTURE)
    with pytest.raises(config.StateFileLegacy) as ei:
        config.load_state(p, for_write=True)
    # Documented stderr text must appear in the exception message.
    assert "schema-version 0.1" in str(ei.value)
    assert "init-state --migrate" in str(ei.value)


def test_load_state_for_write_accepts_v02(tmp_path):
    """A v0.2 file does not raise on for_write=True."""
    p = _write(
        tmp_path / "s.toml",
        'schema-version = "0.2"\n\n[pack.demo]\ninstalled-version = "0.1.0"\nscope = "repo"\nprimitives = []\n[pack.demo.files]\n',
    )
    state = config.load_state(p, for_write=True)
    assert state.schema_version == "0.2"
    assert state.packs["demo"].scope == "repo"


def test_init_state_refuses_v01_state_file(tmp_path):
    """The init-state hash-mode (no --migrate) is a *write* — refuse v0.1."""
    _write(tmp_path / ".agent-ready-state.toml", V01_FIXTURE)
    # Build a minimal pack so the loader doesn't trip earlier.
    packs_dir = tmp_path / "packs"
    pack = packs_dir / "demo"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    args = argparse.Namespace(
        pack="demo",
        packs_dir=str(packs_dir),
        root=str(tmp_path),
        migrate=False,
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = init_state.run(args)
    assert rc == 1
    err = buf.getvalue()
    assert "schema-version 0.1" in err
    assert "init-state --migrate" in err


# ---------------------------------------------------------------------------
# `init-state --migrate` semantics
# ---------------------------------------------------------------------------


def test_migrate_rewrites_v01_to_v02(tmp_path):
    """Every pack gains `scope = "repo"`; schema-version flips to 0.2."""
    state_path = _write(tmp_path / ".agent-ready-state.toml", V01_TWO_PACKS)
    args = argparse.Namespace(
        root=str(tmp_path),
        migrate=True,
        pack=None,
        packs_dir="packs",
        scope=None,
    )
    rc = init_state.run(args)
    assert rc == 0

    migrated = config.load_state(state_path)
    assert migrated.schema_version == "0.2"
    assert all(ps.scope == "repo" for ps in migrated.packs.values())
    # SHAs preserved.
    assert migrated.packs["core"].file_sha("AGENTS.md") == "aa"
    assert migrated.packs["governance-extras"].file_sha("docs/CHARTER.md") == "bb"


def test_migrate_is_idempotent(tmp_path):
    """Running --migrate twice against the same file is a no-op."""
    state_path = _write(tmp_path / ".agent-ready-state.toml", V01_FIXTURE)
    args = argparse.Namespace(
        root=str(tmp_path), migrate=True, pack=None, packs_dir="packs", scope=None
    )
    assert init_state.run(args) == 0
    first_pass = state_path.read_bytes()
    assert init_state.run(args) == 0
    second_pass = state_path.read_bytes()
    assert first_pass == second_pass, "migration is not idempotent"


def test_migrate_refuses_absent_file(tmp_path):
    """Migration of an absent file surfaces — silent no-op would hide drift."""
    args = argparse.Namespace(
        root=str(tmp_path), migrate=True, pack=None, packs_dir="packs", scope=None
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = init_state.run(args)
    assert rc == 1
    assert "no state file" in buf.getvalue()


# ---------------------------------------------------------------------------
# User-scope state file path + permissions
# ---------------------------------------------------------------------------


def test_user_state_path_creates_dot_directory(tmp_path):
    """safety.user_state_path() creates ~/.agent-ready with mode 0o700."""
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    p = safety.user_state_path(home=fake_home)
    assert p == fake_home / ".agent-ready" / "state.toml"
    assert (fake_home / ".agent-ready").is_dir()
    # On POSIX the mode bits are observable. On platforms that don't
    # respect mode in mkdir (e.g. NTFS), we soften this to "creates the
    # directory" — the file is still under $HOME.
    if os.name == "posix":
        st = (fake_home / ".agent-ready").stat()
        assert stat.S_IMODE(st.st_mode) == 0o700, (
            f"expected 0o700, got {oct(stat.S_IMODE(st.st_mode))}"
        )


def test_user_state_path_idempotent_when_dir_exists(tmp_path):
    """Re-calling does not raise even if the dir is already there."""
    fake_home = tmp_path / "home"
    (fake_home / ".agent-ready").mkdir(parents=True)
    p = safety.user_state_path(home=fake_home)
    assert p == fake_home / ".agent-ready" / "state.toml"


# ---------------------------------------------------------------------------
# Round-trip: a v0.2 dump emits the scope column
# ---------------------------------------------------------------------------


def test_dump_state_v02_emits_scope_column():
    state = config.State(schema_version="0.2")
    state.packs["demo"] = config.PackState(
        installed_version="0.1.0",
        scope="user",
        files={"x": {"sha": "0"}},
    )
    serialised = config.dump_state(state)
    assert 'scope = "user"' in serialised


def test_dump_state_v01_omits_scope_column():
    state = config.State(schema_version="0.1")
    state.packs["demo"] = config.PackState(
        installed_version="0.1.0", files={"x": {"sha": "0"}}
    )
    serialised = config.dump_state(state)
    # Round-trip preserves v0.1 shape (no scope column).
    assert "scope" not in serialised
