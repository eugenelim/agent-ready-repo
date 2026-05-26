"""T3 AC6: credentials_shim.py + Tier-2 helpers byte-equivalent to today's
agentbundle/creds/{loader,exceptions,_keychain_macos,_credman_windows}.py
modulo the documented import-path delta.

The "modulo" is computed deterministically: the test regenerates the
expected shim text by inlining exceptions.py into loader.py and
rewriting the helpers' `from .exceptions import Tier2HardFailError`
to `from .credentials_shim import Tier2HardFailError`. The shipped
files must equal the regeneration byte-for-byte.

When the loader changes upstream, this test fails until the shim is
regenerated. That is the contract — drift surfaces immediately.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
CREDS = REPO_ROOT / "packages" / "agentbundle" / "agentbundle" / "creds"
SHARED_LIBS = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "shared-libs"

_EXC_IMPORT_BLOCK = re.compile(
    r"from \.exceptions import \(\n(?:    [A-Za-z_][A-Za-z0-9_]*,\n)+\)\n",
    re.MULTILINE,
)


def _regenerate_shim() -> str:
    """Apply the deterministic source-to-shim transformation.

    Loader.py's `from .exceptions import (...)` block becomes the
    inlined contents of exceptions.py (sans its module docstring +
    future-import header — the loader already has those).
    """
    loader = (CREDS / "loader.py").read_text(encoding="utf-8")
    exc = (CREDS / "exceptions.py").read_text(encoding="utf-8")
    parts = exc.split("from __future__ import annotations\n", 1)
    if len(parts) != 2:
        raise AssertionError("exceptions.py shape changed; update the splitter")
    exc_classes = parts[1].lstrip("\n")
    match = _EXC_IMPORT_BLOCK.search(loader)
    if match is None:
        raise AssertionError(
            "loader.py no longer carries the multi-line `from .exceptions "
            "import (...)` block; update the regenerator"
        )
    return loader[:match.start()] + exc_classes + loader[match.end():]


def _regenerate_helper(name: str) -> str:
    src = (CREDS / name).read_text(encoding="utf-8")
    return src.replace(
        "from .exceptions import Tier2HardFailError",
        "from .credentials_shim import Tier2HardFailError",
    )


class CredentialsShimByteEquivalenceTests(unittest.TestCase):
    """AC6: shipped shim files match the deterministic regeneration."""

    def test_credentials_shim_byte_equivalent(self) -> None:
        expected = _regenerate_shim()
        actual = (SHARED_LIBS / "credentials_shim.py").read_text(encoding="utf-8")
        self.assertEqual(
            expected, actual,
            "credentials_shim.py has drifted from loader.py + exceptions.py; "
            "regenerate with the test's _regenerate_shim() recipe",
        )

    def test_keychain_macos_byte_equivalent(self) -> None:
        expected = _regenerate_helper("_keychain_macos.py")
        actual = (SHARED_LIBS / "_keychain_macos.py").read_text(encoding="utf-8")
        self.assertEqual(
            expected, actual,
            "_keychain_macos.py has drifted from agentbundle/creds/_keychain_macos.py",
        )

    def test_credman_windows_byte_equivalent(self) -> None:
        expected = _regenerate_helper("_credman_windows.py")
        actual = (SHARED_LIBS / "_credman_windows.py").read_text(encoding="utf-8")
        self.assertEqual(
            expected, actual,
            "_credman_windows.py has drifted from agentbundle/creds/_credman_windows.py",
        )

    def test_helper_import_rewrite_actually_fired(self) -> None:
        """Defence: confirm the rewrite produced a real delta. If the
        upstream loader / helpers no longer carry the `from .exceptions`
        import, the byte-equivalence above would still pass against a
        no-op transformation — and that no-op would hide a real
        regression in the shim's structure."""
        for name in ("_keychain_macos.py", "_credman_windows.py"):
            src = (CREDS / name).read_text(encoding="utf-8")
            self.assertIn(
                "from .exceptions import Tier2HardFailError", src,
                f"{name}: import the regenerator targets is gone; "
                "the byte-equivalence test would become a tautology",
            )


if __name__ == "__main__":
    unittest.main()
