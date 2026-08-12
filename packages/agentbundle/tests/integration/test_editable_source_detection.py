"""Keystone integration test: editable detection resolves to a staged
clone root against a **real** `pip install -e`, not a mocked
`direct_url.json`.

Builds its own throwaway venv, editable-installs a copy of agentbundle into
it, then runs `_detect_editable_source` against the real PEP 610 record and
asserts it walks up to the clone root (the dir holding `catalogue.toml` +
`packs/`).

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

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


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
    clone = tmp_path / "clone"
    package = clone / "packages" / "agentbundle"
    shutil.copytree(
        PACKAGE_ROOT,
        package,
        ignore=shutil.ignore_patterns("build", "dist", "*.egg-info", "__pycache__"),
    )
    # Production intentionally accepts editable source roots only from a Git
    # checkout.  The staged clone needs that boundary marker as well as the
    # catalogue markers below; no repository metadata is otherwise required.
    (clone / ".git").mkdir()
    (clone / "packs").mkdir()
    (clone / "catalogue.toml").write_text(
        "schema = 1\n", encoding="utf-8", newline="\n"
    )

    venv_dir = tmp_path / "venv"
    # Keep the metadata corpus isolated. With system site-packages enabled, a
    # second editable agentbundle install can win `_load_distribution()`'s
    # record-bearing scan and point detection at an unrelated workspace.
    venv.create(venv_dir, with_pip=True, system_site_packages=False)
    bindir = venv_dir / ("Scripts" if sys.platform == "win32" else "bin")
    py = bindir / ("python.exe" if sys.platform == "win32" else "python")

    env = _venv_env()
    # `--no-build-isolation` builds against the venv's own backend, so the
    # backend must be present: a bare `venv` (Python 3.12+) ships pip but not
    # setuptools, and `pyproject.toml`'s SPDX `license` string needs
    # setuptools>=77. Provision it explicitly rather than relying on inherited
    # system site-packages, which the CI runner's interpreter does not carry.
    provision = subprocess.run(
        [str(py), "-m", "pip", "install", "--quiet", "setuptools>=77", "wheel"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert provision.returncode == 0, (
        f"backend provisioning failed:\nstdout={provision.stdout}\nstderr={provision.stderr}"
    )
    install = subprocess.run(
        [
            str(py),
            "-m",
            "pip",
            "install",
            "-e",
            str(package),
            "--quiet",
            "--no-deps",
            "--no-build-isolation",
        ],
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
    assert detected == str(clone.resolve()), (
        f"editable detection resolved to {detected!r}, expected the clone root "
        f"{str(clone.resolve())!r}; stderr={detect.stderr!r}"
    )
