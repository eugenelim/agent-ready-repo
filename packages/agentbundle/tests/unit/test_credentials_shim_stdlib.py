"""T3 AC7: credentials_shim.py is stdlib-only on import.

Spec AC7 verbatim: the verifying unit test runs the import in an
**isolated subprocess** and asserts the `sys.modules` delta contains
only stdlib module names plus the shim and its declared siblings.
The in-pytest snapshot approach is explicitly rejected because pytest
pollutes `sys.modules` with pluggy / _pytest / etc. — any in-process
assertion would compare against a polluted baseline.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SHARED_LIBS = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "shared-libs"

# Stdlib roots the shim is allowed to pull in transitively. Lifted
# from loader.py's top-level import list + dataclasses + tomllib +
# ctypes (Windows-only). Anything outside this set on a Linux/macOS
# host is a third-party dep and a regression.
_STDLIB_ROOTS = frozenset({
    "dataclasses", "os", "pathlib", "re", "subprocess", "sys",
    "tempfile", "tomllib", "ctypes",
})


class ShimStdlibOnlySubprocessTests(unittest.TestCase):
    """Spawn `python3 -c` in a subprocess, import the shim, and
    compare the sys.modules delta against the stdlib allow-list."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        pkg = self.tmp / "fixture_skill"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        for fname in (
            "credentials_shim.py",
            "_keychain_macos.py",
            "_credman_windows.py",
        ):
            shutil.copy(SHARED_LIBS / fname, pkg / fname)
        self.pkg = pkg

    def _run_subprocess_import(self) -> set[str]:
        """Return the sys.modules delta from a fresh subprocess that
        only imports the shim. The subprocess also captures
        ``sys.stdlib_module_names`` so the assertion can distinguish
        stdlib transitive imports (admissible) from third-party deps."""
        script = textwrap.dedent(
            """
            import json
            import sys
            before = set(sys.modules)
            from fixture_skill import credentials_shim  # noqa: F401
            after = set(sys.modules)
            print(json.dumps({
                "delta": sorted(after - before),
                "stdlib": sorted(sys.stdlib_module_names),
            }))
            """
        )
        proc = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(self.tmp),
            env={"PYTHONPATH": str(self.tmp), "PATH": "/usr/bin:/bin"},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode, 0,
            f"subprocess import failed: stdout={proc.stdout!r} "
            f"stderr={proc.stderr!r}",
        )
        return json.loads(proc.stdout.strip())

    def test_delta_contains_only_stdlib_and_shim_siblings(self) -> None:
        result = self._run_subprocess_import()
        delta = set(result["delta"])
        # Anything in `sys.stdlib_module_names` (Python 3.10+) is by
        # definition a stdlib module — admissible. The shim's own
        # files land under `fixture_skill.*` — also admissible.
        stdlib_names = set(result["stdlib"])
        non_stdlib: set[str] = set()
        for mod in delta:
            root = mod.split(".", 1)[0]
            if root in stdlib_names:
                continue
            # Stdlib implementation-detail submodules (`_frozen_importlib_external`,
            # `_collections_abc`, `_io`, etc.) are stdlib internals.
            if root.startswith("_") and root not in {"_keychain_macos", "_credman_windows"}:
                continue
            if root == "fixture_skill":
                continue
            non_stdlib.add(mod)
        self.assertEqual(
            non_stdlib, set(),
            f"shim subprocess import pulled non-stdlib modules: {non_stdlib}",
        )

    def test_no_third_party_modules_imported(self) -> None:
        """Tighten the contract: explicitly assert no modules under
        the known third-party names a credentialed primitive might
        accidentally pull (`agentbundle`, `keyring`, `dotenv`)."""
        result = self._run_subprocess_import()
        delta = set(result["delta"])
        forbidden_prefixes = ("agentbundle", "keyring", "dotenv")
        for mod in delta:
            for prefix in forbidden_prefixes:
                self.assertFalse(
                    mod == prefix or mod.startswith(prefix + "."),
                    f"shim pulled forbidden module {mod}",
                )


if __name__ == "__main__":
    unittest.main()
