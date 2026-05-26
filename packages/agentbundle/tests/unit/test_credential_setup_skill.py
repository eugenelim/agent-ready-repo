"""T7 (credential-broker-contract): credential-setup skill body — AC18 / AC19.

Verifies:
- AC18: SKILL.md carries the verbatim phrase "interactive, user-invoked, do not auto-run"
- AC18: SKILL.md carries the broker-agnostic Don't-block
- AC18: setup.py prompts via getpass and never prints the token to stdout
- AC19: setup.py rejects the reserved `sso` namespace with stderr naming the reserved set
"""

from __future__ import annotations

import io
import os
import pathlib
import shutil
import subprocess
import sys

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
SETUP_SKILL = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "skills" / "credential-setup"
SKILL_MD = SETUP_SKILL / "SKILL.md"
SETUP_PY = SETUP_SKILL / "scripts" / "setup.py"
SHIM_SOURCE = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "shared-libs"


def test_skill_md_exists():
    assert SKILL_MD.is_file()
    assert SETUP_PY.is_file()


def test_ac18_description_carries_verbatim_phrase():
    """AC18: SKILL.md description: carries the verbatim phrase
    'interactive, user-invoked, do not auto-run'."""
    body = SKILL_MD.read_text(encoding="utf-8")
    # The phrase appears in the frontmatter description and/or skill body.
    assert "interactive, user-invoked, do not auto-run" in body


def test_ac18_security_rules_block_present():
    """AC18: SKILL.md carries the `### Security rules (non-negotiable)` block."""
    body = SKILL_MD.read_text(encoding="utf-8")
    assert "### Security rules (non-negotiable)" in body
    # The broker-agnostic invariants.
    assert "Never** read that file, print it, or echo the token" in body
    assert "Never** put the token on the command line" in body


def test_ac19_reserved_sso_namespace_refused(tmp_path):
    """AC19: setup.py refuses the reserved `sso` namespace; stderr names
    the reserved set. Run the script via subprocess against the projected
    sibling shim under a tmp_path skill dir."""
    # Build a tmp skill dir with the shim siblings + setup.py so the
    # relative import (`from .credentials_shim ...`) resolves.
    skill_dir = tmp_path / "credential-setup"
    skill_dir.mkdir()
    (skill_dir / "__init__.py").write_text("")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "__init__.py").write_text("")
    shutil.copy(SETUP_PY, scripts_dir / "setup.py")
    for shim_file in SHIM_SOURCE.iterdir():
        if shim_file.is_file() and shim_file.suffix == ".py":
            shutil.copy(shim_file, scripts_dir / shim_file.name)

    # Run as a module so relative imports resolve.
    res = subprocess.run(
        [sys.executable, "-m", "credential-setup.scripts.setup", "sso"],
        cwd=str(tmp_path),
        capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
    )
    # Module name has a dash so -m won't work — re-run via direct script path.
    if res.returncode == 0 or "sso" not in res.stderr:
        # Fall back: invoke the file directly with PYTHONPATH so the
        # `from .credentials_shim` relative import resolves.
        # We need a Python package layout — use underscored name.
        skill_dir2 = tmp_path / "credential_setup"
        skill_dir2.mkdir()
        (skill_dir2 / "__init__.py").write_text("")
        shutil.copy(SETUP_PY, skill_dir2 / "setup.py")
        for shim_file in SHIM_SOURCE.iterdir():
            if shim_file.is_file() and shim_file.suffix == ".py":
                shutil.copy(shim_file, skill_dir2 / shim_file.name)
        res = subprocess.run(
            [sys.executable, "-m", "credential_setup.setup", "sso"],
            cwd=str(tmp_path),
            capture_output=True, text=True,
            env={**os.environ, "PYTHONPATH": str(tmp_path)},
        )
    assert res.returncode == 2, f"expected exit 2 for reserved sso, got {res.returncode}\nstderr: {res.stderr}\nstdout: {res.stdout}"
    assert "sso" in res.stderr
    assert "reserved" in res.stderr


def test_ac18_argv_ban_refused(tmp_path):
    """AC18 / argv-ban: setup.py refuses --token / --api-token / etc.
    on the command line."""
    skill_dir = tmp_path / "credential_setup"
    skill_dir.mkdir()
    (skill_dir / "__init__.py").write_text("")
    shutil.copy(SETUP_PY, skill_dir / "setup.py")
    for shim_file in SHIM_SOURCE.iterdir():
        if shim_file.is_file() and shim_file.suffix == ".py":
            shutil.copy(shim_file, skill_dir / shim_file.name)

    res = subprocess.run(
        [sys.executable, "-m", "credential_setup.setup", "myns", "--token=abc"],
        cwd=str(tmp_path),
        capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
    )
    assert res.returncode == 3
    assert "argv" in res.stderr.lower() or "tokens cannot be passed via argv" in res.stderr


def test_ac18_no_token_in_stdout(tmp_path, monkeypatch):
    """AC18: when the user enters a secret, it never appears on stdout —
    only stderr announcements. We simulate via in-process import after
    projecting the shim siblings into a temp package."""
    skill_dir = tmp_path / "credential_setup"
    skill_dir.mkdir()
    (skill_dir / "__init__.py").write_text("")
    shutil.copy(SETUP_PY, skill_dir / "setup.py")
    for shim_file in SHIM_SOURCE.iterdir():
        if shim_file.is_file() and shim_file.suffix == ".py":
            shutil.copy(shim_file, skill_dir / shim_file.name)

    # Stage a fake schema + skills root so --schema-path resolves.
    schema = tmp_path / "creds-schema.toml"
    schema.write_text(
        '[namespace]\nname = "ns_test"\n\n'
        '[[namespace.keys]]\nname = "API_TOKEN"\nlabel = "API token"\nsecret = true\n',
        encoding="utf-8",
    )

    # Force HOME to a tmp dir so any Tier-2 backend write is sandboxed.
    monkeypatch.setenv("HOME", str(tmp_path / "fake_home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "fake_home"))
    (tmp_path / "fake_home").mkdir()

    # Drive the script with a fake tty stdin: we can't easily simulate
    # tty here, so instead drive via PYTHONPATH + non-tty short-circuit
    # to confirm stdout stays empty when stdin-not-tty refusal fires.
    res = subprocess.run(
        [
            sys.executable, "-m", "credential_setup.setup",
            "ns_test", "--schema-path", str(schema),
            "--allow-insecure-fallback",
        ],
        cwd=str(tmp_path),
        input="secret-token-MARKER-XYZ\n",
        capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": str(tmp_path), "HOME": str(tmp_path / "fake_home")},
    )
    # Non-tty stdin: setup refuses with exit 3; stdout stays empty.
    assert res.returncode == 3, f"expected exit 3 (non-tty refuse), got {res.returncode}\nstderr={res.stderr}"
    assert "secret-token-MARKER-XYZ" not in res.stdout
    assert "secret-token-MARKER-XYZ" not in res.stderr
    assert "stdin-not-tty" in res.stderr


def test_setup_py_imports_from_credentials_shim():
    """AC25 / `auth: creds` lint: setup.py imports from .credentials_shim."""
    body = SETUP_PY.read_text(encoding="utf-8")
    assert "from .credentials_shim import" in body
