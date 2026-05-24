"""Pytest config — put `agentbundle` on PYTHONPATH for subprocess invocations.

Several tests run `python -m agentbundle.build ...` via subprocess.run with
`cwd=REPO_ROOT` (the manila repo root, not packages/agentbundle/). From that
cwd, the `agentbundle` package isn't on sys.path and Python raises
ModuleNotFoundError. Setting PYTHONPATH in this process's os.environ makes
subprocess children inherit it.

This is a test-only convenience — it does not modify how production code
discovers the package (which is via pip-install or the build pipeline's
own sys.path management).
"""

from __future__ import annotations

import os
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parent

_existing = os.environ.get("PYTHONPATH", "")
_paths = _existing.split(os.pathsep) if _existing else []
if str(_PACKAGE_ROOT) not in _paths:
    _paths.insert(0, str(_PACKAGE_ROOT))
    os.environ["PYTHONPATH"] = os.pathsep.join(_paths)
