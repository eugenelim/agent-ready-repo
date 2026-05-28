"""AC22c: documented bin/-load degradation of the shim's own
`_tier2_backend`.

When `credentials_shim.py` is loaded as a sibling under
`~/.agentbundle/bin/` per the AC22b companion projection, its own
platform-dispatch block (`from . import _keychain_macos as
_tier2_backend` on darwin / `from . import _credman_windows ...` on
win32) raises `ImportError` because the shim's platform backends are
intentionally NOT projected into `bin/` (sso-broker uses its own
`_sso_*` backends instead). The shim's existing `except ImportError:
_tier2_backend = None` clause swallows it. AC22c pins this as
documented, intentional behaviour so a future "improvement" of the
shim cannot silently break the contract.

Two cases:

  1. The shim source docstring contains the verbatim degradation note.
  2. When the shim is loaded from a bin/-style staging (no platform-
     backend siblings), `_tier2_backend is None` on every platform.

Case 2 spawns a subprocess against the shim file via `runpy.run_path`
— a deliberate carve-out from the project's general "test real
file-path invocation, not synthesised imports" rule. This test
exercises the SHIM's bin/-load behaviour, not the broker's documented
verb invocation; the broker's own bin/-load chain is covered by the
`show-tier2-backend` integration test in
`tests/integration/test_credential_user_scope_invocation.py`.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SHIM_SOURCE = (
    REPO_ROOT / "packs" / "credential-brokers" / ".apm"
    / "shared-libs" / "credentials_shim.py"
)

# Pinned phrases. Each clause carries a distinct part of the AC22c
# contract: the trigger condition (when), the resolved value (what),
# and the caller guidance (so what). A paraphrase of any single
# clause fails the test. Splitting the assertion this way means a
# future "improvement" that keeps the opening but drops the
# "don't-call-load_credentials" warning cannot slip through.
_PHRASE_OPENING = "When loaded outside a consumer-skill ``scripts/`` directory"
_PHRASE_BACKEND_NONE = "the shim's own ``_tier2_backend`` resolves\nto ``None``"
_PHRASE_CALLER_GUIDANCE = (
    "Callers in that context must not rely on ``load_credentials``\n"
    "for Tier-2 resolution"
)


class ShimDocstringRecordsBinLoadDegradationTests(unittest.TestCase):
    def test_docstring_contains_verbatim_degradation_note(self) -> None:
        text = SHIM_SOURCE.read_text(encoding="utf-8")
        for phrase in (
            _PHRASE_OPENING,
            _PHRASE_BACKEND_NONE,
            _PHRASE_CALLER_GUIDANCE,
        ):
            self.assertIn(
                phrase, text,
                f"AC22c: credentials_shim.py docstring must record the "
                f"bin/-load degradation note verbatim. Missing clause: "
                f"{phrase!r}",
            )


class ShimBinLoadTier2BackendIsNoneTests(unittest.TestCase):
    """AC22c case 2: load the shim from a bin/-style staging and
    assert `_tier2_backend is None` on every platform."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_bin_loaded_shim_tier2_backend_is_none(self) -> None:
        if not SHIM_SOURCE.is_file():
            self.skipTest("credentials_shim.py source not present")
        bin_dir = self.tmp_path / "bin"
        bin_dir.mkdir()
        # AC22b companion staging: shim only, NO platform-backend
        # siblings, NO __init__.py.
        shutil.copy(SHIM_SOURCE, bin_dir / "credentials_shim.py")
        self.assertFalse((bin_dir / "_keychain_macos.py").exists())
        self.assertFalse((bin_dir / "_credman_windows.py").exists())
        self.assertFalse((bin_dir / "__init__.py").exists())

        probe = textwrap.dedent(
            """
            import runpy, sys
            g = runpy.run_path("bin/credentials_shim.py", run_name="probe")
            backend = g.get("_tier2_backend")
            sys.stdout.write(f"backend={backend!r}\\n")
            sys.exit(0 if backend is None else 1)
            """
        )
        env = {
            k: v for k, v in os.environ.items()
            if k in {"PATH", "HOME", "USERPROFILE", "TMPDIR", "TEMP", "TMP"}
        }
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(self.tmp_path),
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        self.assertEqual(
            result.returncode, 0,
            f"AC22c: bin/-loaded shim's _tier2_backend should be None "
            f"on every platform.\nstdout: {result.stdout!r}\n"
            f"stderr: {result.stderr!r}",
        )
        self.assertIn("backend=None", result.stdout)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
