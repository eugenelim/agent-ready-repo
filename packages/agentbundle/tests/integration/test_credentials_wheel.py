"""T3 / AC4c: ``agent_ready.credentials`` is reachable from an installed wheel.

The test builds + installs ``packages/agentbundle`` into a ``tmp_path``-scoped
site directory, then runs the import in a subprocess whose ``PYTHONPATH``
points at that site. Exit 0 from the import is the AC4c contract.

This is slow (~5–30s for the PEP 517 build); it lives under
``tests/integration`` so the default ``pytest -q`` over ``tests/unit/`` stays
fast, while CI's full-suite invocation still picks it up.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

def test_agent_ready_credentials_resolves_from_installed_wheel(tmp_path):
    site_dir = tmp_path / "site"
    # __file__: packages/agentbundle/tests/integration/test_credentials_wheel.py
    # parents[2] resolves to packages/agentbundle/ — the package root pip
    # should pick up.
    pkg_root = pathlib.Path(__file__).resolve().parents[2]
    install = subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "--target", str(site_dir),
            "--quiet", "--no-deps",
            str(pkg_root),
        ],
        capture_output=True, text=True,
    )
    assert install.returncode == 0, (
        f"pip install failed (rc={install.returncode}):\n"
        f"stdout: {install.stdout}\nstderr: {install.stderr}"
    )
    # Confirm the shim package actually landed in the wheel.
    assert (site_dir / "agent_ready" / "credentials.py").is_file(), (
        f"agent_ready/credentials.py missing from installed target; "
        f"listing: {sorted(p.name for p in site_dir.iterdir())}"
    )
    # PEP 668-friendly: don't inherit the parent's PYTHONPATH; point it
    # only at the freshly-installed target.
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(site_dir),
        # Windows runs need SYSTEMROOT for subprocess.run to find DLLs.
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    }
    res = subprocess.run(
        [sys.executable, "-c",
         "from agent_ready.credentials import load_credentials; "
         "from agent_ready.credentials import Credentials, "
         "CredentialsMissingError, Tier2HardFailError"],
        env=env,
        capture_output=True, text=True,
    )
    assert res.returncode == 0, (
        f"import from installed wheel failed (rc={res.returncode}):\n"
        f"stdout: {res.stdout}\nstderr: {res.stderr}"
    )
