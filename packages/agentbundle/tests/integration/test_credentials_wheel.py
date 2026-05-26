"""T15 / AC36 + AC39: ``agentbundle.credentials`` is NOT reachable from
the installed wheel — the module was removed in version 0.2.0 per
RFC-0013 § 9.

The test builds + installs ``packages/agentbundle`` into a
``tmp_path``-scoped site directory, then asserts that the import in a
subprocess raises ``ImportError`` / ``ModuleNotFoundError``. The prior
test (0.1.x baseline) asserted resolution; this rewrite pins the
absence.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


def test_agentbundle_credentials_is_removed_from_installed_wheel(tmp_path):
    site_dir = tmp_path / "site"
    pkg_root = pathlib.Path(__file__).resolve().parents[2]

    # Defensive clean before pip install — a stale `build/` or
    # `*.egg-info/` from a previous local build can shadow the
    # deletion (setuptools `find_packages` will pull `credentials.py`
    # from `build/lib/agentbundle/` and ship it in the wheel, making
    # the absence assertion fail intermittently on dev machines).
    # `feedback_gitignore_silent_skip` warns about this trap.
    import shutil
    for stale in (
        pkg_root / "build",
        pkg_root / "agentbundle.egg-info",
        pkg_root / "dist",
    ):
        shutil.rmtree(stale, ignore_errors=True)

    install = subprocess.run(
        [
            sys.executable, "-m", "pip", "install",
            "--target", str(site_dir),
            "--quiet", "--no-deps",
            str(pkg_root),
        ],
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, (
        f"pip install failed:\nstdout={install.stdout}\nstderr={install.stderr}"
    )

    # Import in a subprocess so a transient ``sys.modules`` cache from
    # another test cannot mask the absence.
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import agentbundle.credentials  # noqa: F401\n"
            "print('imported (regression — module should not exist)')\n",
        ],
        env={"PYTHONPATH": str(site_dir), "PATH": ""},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0, (
        f"agentbundle.credentials imported from the wheel — regression "
        f"against AC36 (the module was removed in 0.2.0):\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    assert (
        "ModuleNotFoundError" in result.stderr
        or "ImportError" in result.stderr
    ), (
        f"expected ImportError-shape failure, got:\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
