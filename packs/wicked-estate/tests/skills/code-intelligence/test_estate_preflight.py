"""Behaviour of the Tier-1/Tier-2 preflight script.

The script is loaded under a pack- and skill-qualified module name so it cannot
collide with a same-named module in another pack.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "code-intelligence"


def _load():
    spec = importlib.util.spec_from_file_location(
        "wicked_estate_code_intelligence_estate_preflight",
        SKILL / "scripts" / "estate_preflight.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


preflight = _load()


def test_absent_binary_exits_two_with_the_install_command(monkeypatch) -> None:
    """Tier 1 requires a clean failure carrying the exact remediation."""
    monkeypatch.setattr(preflight, "find_binary", lambda: None)
    code, report = preflight.build_report(root=Path("/nonexistent"), explicit_db=None)
    assert code == preflight.EXIT_BINARY_ABSENT
    assert report["status"] == "binary-absent"
    assert "cargo install wicked-estate" in report["remediation"]


def test_present_binary_without_index_exits_three(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(preflight, "find_binary", lambda: "/usr/bin/wicked-estate")
    monkeypatch.setattr(preflight, "read_version", lambda _b: (0, 16, 7))
    monkeypatch.delenv(preflight.DB_ENV_VAR, raising=False)
    code, report = preflight.build_report(root=tmp_path, explicit_db=None)
    assert code == preflight.EXIT_INDEX_ABSENT
    assert report["remediation"] == f"wicked-estate index {tmp_path}"


def test_ready_when_binary_and_index_both_present(monkeypatch, tmp_path) -> None:
    db = tmp_path / ".wicked-estate" / "graph.db"
    db.parent.mkdir(parents=True)
    db.write_bytes(b"")
    monkeypatch.setattr(preflight, "find_binary", lambda: "/usr/bin/wicked-estate")
    monkeypatch.setattr(preflight, "read_version", lambda _b: (0, 16, 7))
    monkeypatch.delenv(preflight.DB_ENV_VAR, raising=False)
    code, report = preflight.build_report(root=tmp_path, explicit_db=None)
    assert code == preflight.EXIT_READY
    assert report["status"] == "ready"


def test_version_below_floor_exits_four(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(preflight, "find_binary", lambda: "/usr/bin/wicked-estate")
    monkeypatch.setattr(preflight, "read_version", lambda _b: (0, 15, 2))
    code, report = preflight.build_report(root=tmp_path, explicit_db=None)
    assert code == preflight.EXIT_VERSION_BELOW
    assert report["required"] == "0.16"


def test_unparseable_version_does_not_block_a_working_binary(monkeypatch, tmp_path) -> None:
    """A future `--version` format change must degrade, not fail closed."""
    db = tmp_path / ".wicked-estate" / "graph.db"
    db.parent.mkdir(parents=True)
    db.write_bytes(b"")
    monkeypatch.setattr(preflight, "find_binary", lambda: "/usr/bin/wicked-estate")
    monkeypatch.setattr(preflight, "read_version", lambda _b: None)
    monkeypatch.delenv(preflight.DB_ENV_VAR, raising=False)
    code, _ = preflight.build_report(root=tmp_path, explicit_db=None)
    assert code == preflight.EXIT_READY


@pytest.mark.parametrize("explicit", [True, False])
def test_db_resolution_follows_the_cli_precedence(monkeypatch, tmp_path, explicit) -> None:
    """Explicit --db beats WICKED_ESTATE_DB, which beats the default path."""
    monkeypatch.setenv(preflight.DB_ENV_VAR, str(tmp_path / "from-env.db"))
    resolved = preflight.resolve_db(str(tmp_path / "explicit.db") if explicit else None, tmp_path)
    expected = "explicit.db" if explicit else "from-env.db"
    assert resolved.name == expected


def test_default_db_path_is_used_when_nothing_overrides(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv(preflight.DB_ENV_VAR, raising=False)
    assert preflight.resolve_db(None, tmp_path) == tmp_path / ".wicked-estate" / "graph.db"


@pytest.mark.parametrize(
    "hostile",
    ["../../etc/passwd", "/etc/passwd", "~/.ssh/id_rsa", "  ", ""],
)
def test_env_override_outside_the_root_is_refused(monkeypatch, tmp_path, hostile) -> None:
    """CWE-22 / CWE-73: an ambient env var must not steer this at any file.

    Refusal falls back to the trusted default rather than erroring, so a stray
    value degrades instead of blocking the workflow.
    """
    monkeypatch.setenv(preflight.DB_ENV_VAR, hostile)
    assert preflight.resolve_db(None, tmp_path) == tmp_path / ".wicked-estate" / "graph.db"


def test_env_override_escaping_via_symlink_is_refused(monkeypatch, tmp_path) -> None:
    """Containment is checked after resolve(), so a symlink cannot smuggle."""
    outside = tmp_path.parent / "outside-target.db"
    outside.write_bytes(b"")
    inside_link = tmp_path / "looks-local.db"
    inside_link.symlink_to(outside)
    monkeypatch.setenv(preflight.DB_ENV_VAR, str(inside_link))
    assert preflight.resolve_db(None, tmp_path) == tmp_path / ".wicked-estate" / "graph.db"


def test_env_override_inside_the_root_is_honoured(monkeypatch, tmp_path) -> None:
    """The guard must not break the legitimate case it exists to protect."""
    legit = tmp_path / "custom" / "graph.db"
    legit.parent.mkdir()
    monkeypatch.setenv(preflight.DB_ENV_VAR, str(legit))
    assert preflight.resolve_db(None, tmp_path) == legit.resolve()


def test_install_refuses_without_cargo(monkeypatch, capsys) -> None:
    """Tier 2 permits a manager the user already has; it never bootstraps one."""
    monkeypatch.setattr(preflight.shutil, "which", lambda _name: None)
    assert preflight.install_with_consent(assume_yes=True) is False
    assert "cargo is not on PATH" in capsys.readouterr().err


def test_install_requires_explicit_consent(monkeypatch, capsys) -> None:
    """Without --yes the script proposes the command and installs nothing."""
    monkeypatch.setattr(preflight.shutil, "which", lambda name: "/usr/bin/cargo")

    def fail(*_args, **_kwargs):  # pragma: no cover - must never run
        raise AssertionError("install ran without consent")

    monkeypatch.setattr(preflight.subprocess, "run", fail)
    assert preflight.install_with_consent(assume_yes=False) is False
    assert "--install --yes" in capsys.readouterr().err


def test_install_command_is_pinned_and_unprivileged() -> None:
    assert "--version" in preflight.INSTALL_COMMAND
    assert "sudo" not in preflight.INSTALL_COMMAND
    assert preflight.INSTALL_COMMAND[0] == "cargo"
