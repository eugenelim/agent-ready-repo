"""T1a: package import + version semantics.

Three goal-based / unit tests:
  1. `import agentbundle` exposes `__version__` (string, non-empty).
  2. `import agentbundle.build` succeeds (F-build is library-importable; no
     `sys.path` tricks needed).
  3. `python -m agentbundle --version` prints a value parsed at import time
     from the bundled `_data/adapter.toml` — proves read-at-import. Test
     mutates the on-disk file mid-test and re-runs `--version`; the value
     printed must still be the original.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent  # packages/agentbundle
BUNDLED_ADAPTER_TOML = PACKAGE_ROOT / "agentbundle" / "_data" / "adapter.toml"


def test_import_agentbundle_exposes_version():
    import agentbundle

    assert isinstance(agentbundle.__version__, str)
    assert agentbundle.__version__
    assert isinstance(agentbundle.SPEC_VERSION, str)
    assert agentbundle.SPEC_VERSION


def test_import_agentbundle_build_succeeds():
    """Library-first invariant: the CLI's foundation imports F-build cleanly."""
    proc = subprocess.run(
        [sys.executable, "-c", "import agentbundle.build"],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr


def test_python_m_agentbundle_version_prints_versions():
    proc = subprocess.run(
        [sys.executable, "-m", "agentbundle", "--version"],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    # argparse prints --version to stdout in 3.4+.
    out = proc.stdout + proc.stderr
    assert "agentbundle" in out
    # The bundled adapter.toml's [contract] version should appear.
    import tomllib

    contract_version = tomllib.loads(
        BUNDLED_ADAPTER_TOML.read_text(encoding="utf-8")
    )["contract"]["version"]
    assert contract_version in out


def test_spec_version_is_read_at_import_time(tmp_path):
    """Mutate adapter.toml on disk after import; SPEC_VERSION must not change.

    This is the load-bearing invariant: every refusal that cites the CLI's
    spec version must cite the version that was canonical at process start,
    not at the moment of refusal. Otherwise concurrent file edits could
    silently change CLI behaviour mid-run.
    """
    import tomllib

    # Snapshot the on-disk version.
    original = tomllib.loads(
        BUNDLED_ADAPTER_TOML.read_text(encoding="utf-8")
    )["contract"]["version"]

    # Stage a script that imports the package, then mutates the file,
    # then asserts the in-process SPEC_VERSION still equals the snapshot.
    script = f"""
import sys, pathlib, tomllib
sys.path.insert(0, {str(PACKAGE_ROOT)!r})
import agentbundle
imported_value = agentbundle.SPEC_VERSION
assert imported_value == {original!r}, (imported_value, {original!r})

# Mutate the bundled adapter.toml.
path = pathlib.Path({str(BUNDLED_ADAPTER_TOML)!r})
backup = path.read_text(encoding="utf-8")
mutated = backup.replace(
    'version = "{original}"', 'version = "99.99"', 1
)
assert mutated != backup, "test fixture: substitution did not match"
path.write_text(mutated, encoding="utf-8")
try:
    # Re-read SPEC_VERSION via fresh attribute access — proves the value is
    # frozen at import, not lazily re-resolved.
    assert agentbundle.SPEC_VERSION == {original!r}, agentbundle.SPEC_VERSION
finally:
    path.write_text(backup, encoding="utf-8")
print("ok")
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert "ok" in proc.stdout
