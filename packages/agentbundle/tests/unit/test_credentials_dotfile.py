"""T6: Tier-3 dotfile read + write (skill-secrets spec § AC13-AC15).

Tests are platform-aware:
- Path resolution and atomic-write contract run unguarded (POSIX + Windows).
- POSIX-specific permission assertions (0o600 file, 0o700 parent on
  create, shared-parent warning) are guarded with
  ``@pytest.mark.skipif(sys.platform == "win32", ...)``.
- Windows-specific ``icacls`` assertions are guarded the opposite way;
  this fixture host is Darwin so those tests skip locally — they are
  written for the eventual macos/windows CI matrix per the prompt's
  risk note.
"""

from __future__ import annotations

import os
import stat
import sys

import pytest

from agentbundle.creds import loader
from agent_ready.credentials import CredentialsMissingError, load_credentials


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Redirect HOME / USERPROFILE per spec § Boundaries; force Tier-2
    backend to None so this suite exercises only Tier 1 + Tier 3."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    for var in list(os.environ):
        if var.startswith("FIXTURE_T6_"):
            monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(loader, "_tier2_backend", None)


def test_dotfile_path_resolves_under_home(tmp_path):
    """AC13: path is ``$HOME/.agent-ready/credentials.env``."""
    assert loader._dotfile_path() == tmp_path / ".agent-ready" / "credentials.env"


def test_dotfile_write_creates_file_and_parent(tmp_path):
    loader._dotfile_write("fixture_t6", "API_TOKEN", "secret-1")
    path = tmp_path / ".agent-ready" / "credentials.env"
    assert path.is_file()
    assert path.parent.is_dir()
    assert "FIXTURE_T6_API_TOKEN=secret-1" in path.read_text(encoding="utf-8")


def test_dotfile_read_round_trips_value(tmp_path):
    loader._dotfile_write("fixture_t6", "API_TOKEN", "round-trip-value")
    assert loader._dotfile_read("fixture_t6", "API_TOKEN") == "round-trip-value"


def test_dotfile_read_missing_file_returns_none(tmp_path):
    """AC4 fallback: no dotfile → ``None`` → ``CredentialsMissingError``
    when the loader treats the key as required."""
    assert loader._dotfile_read("fixture_t6", "API_TOKEN") is None


def test_dotfile_read_missing_key_returns_none(tmp_path):
    loader._dotfile_write("fixture_t6", "API_TOKEN", "set")
    assert loader._dotfile_read("fixture_t6", "BASE_URL") is None


def test_dotfile_write_preserves_other_entries(tmp_path):
    loader._dotfile_write("fixture_t6", "API_TOKEN", "tok-1")
    loader._dotfile_write("fixture_t6", "BASE_URL", "https://example.com")
    assert loader._dotfile_read("fixture_t6", "API_TOKEN") == "tok-1"
    assert loader._dotfile_read("fixture_t6", "BASE_URL") == "https://example.com"


def test_dotfile_write_replaces_value_for_same_key(tmp_path):
    loader._dotfile_write("fixture_t6", "API_TOKEN", "old")
    loader._dotfile_write("fixture_t6", "API_TOKEN", "new")
    assert loader._dotfile_read("fixture_t6", "API_TOKEN") == "new"


def test_dotfile_delete_removes_key(tmp_path):
    loader._dotfile_write("fixture_t6", "API_TOKEN", "set")
    loader._dotfile_write("fixture_t6", "BASE_URL", "url")
    loader._dotfile_delete("fixture_t6", "API_TOKEN")
    assert loader._dotfile_read("fixture_t6", "API_TOKEN") is None
    assert loader._dotfile_read("fixture_t6", "BASE_URL") == "url"


def test_dotfile_delete_missing_file_is_noop(tmp_path):
    # No raise, no side effect.
    loader._dotfile_delete("fixture_t6", "API_TOKEN")
    assert not (tmp_path / ".agent-ready" / "credentials.env").exists()


def test_atomic_write_via_mkstemp_and_replace(tmp_path, monkeypatch):
    """AC14: the temp file lives in the target directory (so
    ``os.replace`` is a rename, atomic on POSIX), not in /tmp.
    """
    recorded = []
    real_replace = os.replace

    def recording_replace(src, dst):
        recorded.append((str(src), str(dst)))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", recording_replace)
    loader._dotfile_write("fixture_t6", "API_TOKEN", "secret")
    assert len(recorded) == 1
    src, dst = recorded[0]
    target_dir = str(tmp_path / ".agent-ready")
    assert src.startswith(target_dir + os.sep), (
        f"temp file {src!r} not in target dir {target_dir!r}"
    )
    assert dst == str(tmp_path / ".agent-ready" / "credentials.env")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX-only chmod path")
def test_file_mode_is_0o600_on_posix(tmp_path):
    """AC15: file mode is exactly ``0o600``."""
    loader._dotfile_write("fixture_t6", "API_TOKEN", "secret")
    path = tmp_path / ".agent-ready" / "credentials.env"
    mode = path.stat().st_mode & 0o777
    assert mode == 0o600, f"expected 0o600, got {oct(mode)}"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX-only mkdir path")
def test_parent_mode_is_0o700_on_create_on_posix(tmp_path):
    """AC15: when the parent is created, it's at mode ``0o700``."""
    loader._dotfile_write("fixture_t6", "API_TOKEN", "secret")
    parent = tmp_path / ".agent-ready"
    mode = parent.stat().st_mode & 0o777
    assert mode == 0o700, f"expected 0o700, got {oct(mode)}"


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX-only chmod path")
def test_existing_parent_mode_is_not_rewritten_on_posix(tmp_path, capsys):
    """AC15: a brownfield parent (shared with install state) keeps its
    mode; the helper warns on stderr if more permissive than 0o755."""
    parent = tmp_path / ".agent-ready"
    parent.mkdir(mode=0o755)
    os.chmod(parent, 0o775)  # group-write — more permissive than 0o755
    loader._dotfile_write("fixture_t6", "API_TOKEN", "secret")
    # Parent mode preserved.
    final_mode = parent.stat().st_mode & 0o777
    assert final_mode == 0o775
    captured = capsys.readouterr()
    assert "more permissive than 0o755" in captured.err
    assert str(parent) in captured.err


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only icacls path")
def test_windows_icacls_does_not_call_chmod(tmp_path, monkeypatch):
    """AC15: on Windows, ``os.chmod`` is not used — the file's DACL is
    inherited from the parent and verified post-write via ``icacls``."""
    calls = []
    # ``os.fchmod`` is POSIX-only — on Windows the module doesn't define
    # the name. Skip the unused ``real_*`` captures and pass
    # ``raising=False`` so ``monkeypatch.setattr`` installs the spy
    # without insisting the attribute already exists on this platform.
    monkeypatch.setattr(
        os, "chmod", lambda *a, **kw: calls.append(("chmod", a)), raising=False,
    )
    monkeypatch.setattr(
        os, "fchmod", lambda *a, **kw: calls.append(("fchmod", a)), raising=False,
    )
    # icacls invocation succeeds with empty stdout (no suspect ACEs).
    monkeypatch.setattr(loader, "_verify_icacls", lambda *a, **kw: None)
    loader._dotfile_write("fixture_t6", "API_TOKEN", "secret")
    assert not calls, f"chmod / fchmod called on Windows: {calls}"


def test_tier3_fallback_via_load_credentials(tmp_path):
    """AC4: Tier 1 absent + Tier 2 absent → loader reads Tier 3."""
    loader._dotfile_write("fixture_t6", "API_TOKEN", "from-dotfile")
    creds = load_credentials("fixture_t6", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == "from-dotfile"


def test_tier1_wins_over_tier3(tmp_path, monkeypatch):
    """AC4 first-hit-wins: env present + dotfile present → env value."""
    loader._dotfile_write("fixture_t6", "API_TOKEN", "from-dotfile")
    monkeypatch.setenv("FIXTURE_T6_API_TOKEN", "from-env")
    creds = load_credentials("fixture_t6", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == "from-env"


def test_tier3_miss_raises_credentials_missing(tmp_path):
    """AC4: no Tier-1, no Tier-2, no Tier-3 → CredentialsMissingError."""
    with pytest.raises(CredentialsMissingError) as exc:
        load_credentials("fixture_t6", required_keys=["API_TOKEN"])
    assert "fixture_t6" in str(exc.value)
    assert "API_TOKEN" in str(exc.value)


def test_malformed_dotfile_returns_none_not_raise(tmp_path):
    """A corrupt dotfile is treated as a miss (parser ``EnvParseError``
    swallowed). The loader surface still raises
    ``CredentialsMissingError`` for a required key — never propagates
    the parser error to the primitive author."""
    path = tmp_path / ".agent-ready" / "credentials.env"
    path.parent.mkdir(mode=0o700)
    path.write_text("export FIXTURE_T6_API_TOKEN=secret\n", encoding="utf-8")
    assert loader._dotfile_read("fixture_t6", "API_TOKEN") is None


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX permission shape")
def test_value_with_spaces_round_trips_via_quoting(tmp_path):
    """Values containing spaces round-trip via the parser's quoted form."""
    loader._dotfile_write("fixture_t6", "BASE_URL", "https://jira example com")
    assert loader._dotfile_read("fixture_t6", "BASE_URL") == "https://jira example com"
