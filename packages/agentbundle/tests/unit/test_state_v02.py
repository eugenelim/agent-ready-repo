"""State-file legacy handling under v0.4 (greenfield, RFC-0052 D8).

The v0.4 schema (ADR-0039) made cross-version handling a hard refusal: every
legacy version (v0.1/v0.2/v0.3) is refused on read AND write with re-install
guidance, and ``init-state --migrate`` no longer converts — it refuses. (The
pure-loader refusal matrix lives in ``test_state_v0_4_schema.py``; this file
covers the command-level surfaces and the user-scope state path.)
"""

from __future__ import annotations

import argparse
import io
import contextlib
import os
import stat
from pathlib import Path

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


def _write(p: Path, text: str) -> Path:
    p.write_text(text, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# init-state (hash mode, no --migrate) refuses a legacy file
# ---------------------------------------------------------------------------


def test_init_state_refuses_legacy_state_file(tmp_path):
    """init-state hash-mode is a *write* — a legacy file refuses with the
    greenfield re-install guidance (not the old --migrate hint)."""
    _write(tmp_path / ".agentbundle-state.toml", V01_FIXTURE)
    packs_dir = tmp_path / "packs"
    pack = packs_dir / "demo"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    args = argparse.Namespace(
        pack="demo", packs_dir=str(packs_dir), root=str(tmp_path), migrate=False,
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = init_state.run(args)
    assert rc == 1
    err = buf.getvalue()
    assert "schema-version 0.1" in err
    assert "reinstall" in err.lower()
    assert "init-state --migrate" not in err


# ---------------------------------------------------------------------------
# init-state --migrate: greenfield refusal of legacy; no-op on current
# ---------------------------------------------------------------------------


def test_migrate_refuses_legacy_version(tmp_path):
    """Greenfield (RFC-0052 D8): --migrate refuses a legacy file rather than
    converting — the old header-only bump would relabel a v0.3 body as v0.4."""
    state_path = _write(tmp_path / ".agentbundle-state.toml", V01_FIXTURE)
    args = argparse.Namespace(
        root=str(tmp_path), migrate=True, pack=None, packs_dir="packs", scope=None,
    )
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        rc = init_state.run(args)
    assert rc == 1
    assert "reinstall" in buf.getvalue().lower()
    # The file is untouched (no conversion).
    assert 'schema-version = "0.1"' in state_path.read_text(encoding="utf-8")


def test_migrate_on_current_is_noop(tmp_path):
    """A v0.4 file needs no migration — --migrate is an idempotent no-op."""
    current = config.State()
    current.packs[("core", "claude-code")] = config.PackState(
        installed_version="0.1.0", adapter="claude-code", scope="repo",
        files={"AGENTS.md": {"sha": "aa"}},
    )
    state_path = _write(
        tmp_path / ".agentbundle-state.toml", config.dump_state(current)
    )
    before = state_path.read_bytes()
    args = argparse.Namespace(
        root=str(tmp_path), migrate=True, pack=None, packs_dir="packs", scope=None,
    )
    assert init_state.run(args) == 0
    assert state_path.read_bytes() == before


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
# User-scope state file path + permissions (unchanged by v0.4)
# ---------------------------------------------------------------------------


def test_user_state_path_creates_dot_directory(tmp_path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    p = safety.user_state_path(home=fake_home)
    assert p == fake_home / ".agentbundle" / "state.toml"
    assert (fake_home / ".agentbundle").is_dir()
    if os.name == "posix":
        st = (fake_home / ".agentbundle").stat()
        assert stat.S_IMODE(st.st_mode) == 0o700, (
            f"expected 0o700, got {oct(stat.S_IMODE(st.st_mode))}"
        )


def test_user_state_path_idempotent_when_dir_exists(tmp_path):
    fake_home = tmp_path / "home"
    (fake_home / ".agentbundle").mkdir(parents=True)
    p = safety.user_state_path(home=fake_home)
    assert p == fake_home / ".agentbundle" / "state.toml"


# ---------------------------------------------------------------------------
# Round-trip: a v0.4 dump emits the per-row scope column
# ---------------------------------------------------------------------------


def test_dump_state_v04_emits_scope_column():
    state = config.State()
    state.packs[("demo", "codex")] = config.PackState(
        installed_version="0.1.0", adapter="codex", scope="user",
        files={"x": {"sha": "0"}},
    )
    serialised = config.dump_state(state)
    assert 'scope = "user"' in serialised
    assert "[pack.demo.adapters.codex]" in serialised
