"""Roster suites must not leave invented modules in `sys.modules`.

A module-scoped fixture that installs a stub under a real distribution's name
outlives its own file: within one pytest process the entry is still there when
the next file runs. `types.ModuleType` carries no `__spec__`, and
`importlib.util.find_spec` raises `ValueError` for a spec-less entry rather than
returning None — so a later test that merely *asks whether* the real package is
importable fails on a module it never heard of.

That is how `tests/roster/test_credential_brokers_atlassian_integration.py`
failed on CI while passing locally: `--dist loadfile` put the Linear file in the
same worker, ahead of it, and the outcome depended on which worker got which
file. Ordering decided it, so no single-file run could show it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# The polluter first, then the prober: the order that fails when the stub is
# left installed. The reverse order passes either way, which is why it is not
# the control here.
LEAK_ORDER = (
    "tests/roster/test_linear_refresh_processor.py",
    "tests/roster/test_credential_brokers_atlassian_integration.py",
)


def test_credbroker_stub_does_not_outlive_its_fixture() -> None:
    """Run the two files in the order that reproduced the CI failure."""
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", *LEAK_ORDER, "-q", "-p", "no:cacheprovider"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert "credbroker.__spec__ is None" not in completed.stdout, completed.stdout[-3000:]
    assert completed.returncode == 0, completed.stdout[-3000:]
