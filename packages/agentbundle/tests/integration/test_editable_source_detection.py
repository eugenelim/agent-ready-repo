"""Keystone integration test (RFC-0046 T3): editable detection resolves to the
real clone root against a **real** `pip install -e`, not a mocked
`direct_url.json`.

Builds its own throwaway venv, editable-installs `packages/agentbundle` into
it, then runs `_detect_editable_source` against the real PEP 610 record and
asserts it walks up to the clone root (the dir holding `packs/` +
`.claude-plugin/marketplace.json`).

Slow (venv + editable build). `make build-check` runs no pytest, so this is
wired into CI explicitly in `build-check.yml`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
PKG = REPO_ROOT / "packages" / "agentbundle"


def _venv_env() -> dict[str, str]:
    """Env for the venv subprocesses with the parent's `PYTHONPATH` /
    `VIRTUAL_ENV` / `PYTHONHOME` stripped, so the throwaway venv's
    site-packages (the editable install) is authoritative — otherwise an
    inherited source-tree `PYTHONPATH` shadows the editable metadata and
    `importlib.metadata` finds no `direct_url.json`. This drop-set is the
    known-necessary minimum, not exhaustive — if this ever flakes on a macOS
    framework build, `__PYVENV_LAUNCHER__` is the next suspect."""
    drop = {"PYTHONPATH", "VIRTUAL_ENV", "PYTHONHOME"}
    return {k: v for k, v in os.environ.items() if k not in drop}


def test_editable_detection_against_real_install(tmp_path):
    assert (REPO_ROOT / "packs").is_dir(), f"clone markers missing at {REPO_ROOT}"
    assert (REPO_ROOT / ".claude-plugin" / "marketplace.json").is_file()

    # Defensive clean — a stale build/ or egg-info from a prior local build can
    # shadow the editable install (see feedback_gitignore_silent_skip).
    for stale in (PKG / "build", PKG / "agentbundle.egg-info", PKG / "dist"):
        shutil.rmtree(stale, ignore_errors=True)

    venv_dir = tmp_path / "venv"
    venv.create(venv_dir, with_pip=True)
    bindir = venv_dir / ("Scripts" if sys.platform == "win32" else "bin")
    py = bindir / ("python.exe" if sys.platform == "win32" else "python")

    env = _venv_env()
    install = subprocess.run(
        [str(py), "-m", "pip", "install", "-e", str(PKG), "--quiet"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert install.returncode == 0, (
        f"editable install failed:\nstdout={install.stdout}\nstderr={install.stderr}"
    )

    # Run detection inside the venv against the real installed metadata,
    # through the production loader path (`_load_distribution` prefers the
    # record-bearing dist over a shadowing egg-info).
    snippet = (
        "from agentbundle.source_defaults import "
        "_detect_editable_source, _load_distribution\n"
        "print(_detect_editable_source(_load_distribution()))\n"
    )
    detect = subprocess.run(
        [str(py), "-c", snippet], capture_output=True, text=True, env=env
    )
    assert detect.returncode == 0, (
        f"detection run failed:\nstdout={detect.stdout}\nstderr={detect.stderr}"
    )
    detected = detect.stdout.strip()
    assert detected == str(REPO_ROOT.resolve()), (
        f"editable detection resolved to {detected!r}, expected the clone root "
        f"{str(REPO_ROOT.resolve())!r}"
    )
