"""T3 AC8: credentials_shim.load_credentials round-trip parity with
today's agentbundle.creds.loader.load_credentials.

The shim's behavioural contract is byte-equivalent to RFC-0006 § 2's
loader modulo the import-path delta. This test exercises the shim
directly (imported as a sibling-package member, the same shape a
consumer skill will use post-T11) and asserts:

- Tier 1 env-var resolution returns the same Credentials shape.
- Missing required key raises CredentialsMissingError with namespace +
  missing-keys in the message.
- Tier 3 dotfile read resolves a key the loader would also resolve.
- Credentials immutability + repr-redaction invariants hold post-shim.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[4]
SHARED_LIBS = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "shared-libs"


class _ShimImportBase(unittest.TestCase):
    """Plant the shim under a fixture package, redirect $HOME, force
    Tier-2 backend to None so the host's real keychain is never
    touched.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self._env = patch.dict(
            os.environ,
            {"HOME": str(self.home), "USERPROFILE": str(self.home)},
        )
        self._env.start()
        self.addCleanup(self._env.stop)
        pkg = self.tmp / "fixture_pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        for fname in (
            "credentials_shim.py",
            "_keychain_macos.py",
            "_credman_windows.py",
        ):
            shutil.copy(SHARED_LIBS / fname, pkg / fname)
        sys.path.insert(0, str(self.tmp))
        self.addCleanup(sys.path.remove, str(self.tmp))
        # Purge any cached fixture_pkg so reruns get a fresh shim.
        for mod in list(sys.modules):
            if mod.startswith("fixture_pkg"):
                del sys.modules[mod]
        from fixture_pkg import credentials_shim as shim
        # Force Tier-2 backend off — tests target Tier 1 + Tier 3 only;
        # the host's real keychain must never be exercised.
        shim._tier2_backend = None
        self.shim = shim
        self.addCleanup(self._purge_shim)

    def _purge_shim(self) -> None:
        for mod in list(sys.modules):
            if mod.startswith("fixture_pkg"):
                del sys.modules[mod]


class ShimTier1Tests(_ShimImportBase):
    """Tier-1 env-var resolution behaves like today's loader."""

    def test_tier1_resolves(self) -> None:
        with patch.dict(os.environ, {"SHIMNS_API_TOKEN": "shim-secret"}):
            creds = self.shim.load_credentials("shimns", required_keys=["API_TOKEN"])
        self.assertIsInstance(creds, self.shim.Credentials)
        self.assertEqual(creds.API_TOKEN, "shim-secret")

    def test_credentials_repr_redacts_values(self) -> None:
        with patch.dict(os.environ, {"SHIMNS_API_TOKEN": "should-never-leak"}):
            creds = self.shim.load_credentials("shimns", required_keys=["API_TOKEN"])
        r = repr(creds)
        self.assertNotIn("should-never-leak", r)
        self.assertIn("shimns", r)
        self.assertIn("API_TOKEN", r)

    def test_credentials_is_immutable(self) -> None:
        with patch.dict(os.environ, {"SHIMNS_API_TOKEN": "v"}):
            creds = self.shim.load_credentials("shimns", required_keys=["API_TOKEN"])
        with self.assertRaises(AttributeError):
            creds.API_TOKEN = "other"  # type: ignore[misc]


class ShimMissingKeyTests(_ShimImportBase):
    """Missing required key raises CredentialsMissingError with the
    same shape RFC-0006 § AC3 froze."""

    def test_missing_raises(self) -> None:
        # No env var, no dotfile, Tier-2 forced None.
        with self.assertRaises(self.shim.CredentialsMissingError) as ctx:
            self.shim.load_credentials("shimns", required_keys=["API_TOKEN"])
        msg = str(ctx.exception)
        self.assertIn("shimns", msg)
        self.assertIn("API_TOKEN", msg)
        # Exception also carries structured per-key trailers.
        self.assertEqual(ctx.exception.namespace, "shimns")
        self.assertEqual(ctx.exception.missing, ["API_TOKEN"])
        self.assertIn("API_TOKEN", ctx.exception.tiers_tried)


class ShimTier3Tests(_ShimImportBase):
    """Tier-3 dotfile read resolves a key the loader would also resolve."""

    def test_tier3_dotfile_resolves(self) -> None:
        agentbundle = self.home / ".agentbundle"
        agentbundle.mkdir(mode=0o700)
        dotfile = agentbundle / "credentials.env"
        dotfile.write_text(
            "SHIMNS_API_TOKEN=tier3-value\n",
            encoding="utf-8",
        )
        if os.name == "posix":
            os.chmod(dotfile, 0o600)
        creds = self.shim.load_credentials("shimns", required_keys=["API_TOKEN"])
        self.assertEqual(creds.API_TOKEN, "tier3-value")

    def test_tier3_dotfile_quoted_value(self) -> None:
        agentbundle = self.home / ".agentbundle"
        agentbundle.mkdir(mode=0o700)
        dotfile = agentbundle / "credentials.env"
        dotfile.write_text(
            'SHIMNS_API_TOKEN="value with spaces"\n',
            encoding="utf-8",
        )
        creds = self.shim.load_credentials("shimns", required_keys=["API_TOKEN"])
        self.assertEqual(creds.API_TOKEN, "value with spaces")


class ShimEnvParseSurfaceTests(_ShimImportBase):
    """parse_env_file is the same parser today's loader exposes."""

    def test_basic_parse(self) -> None:
        tmp = self.tmp / "fixture.env"
        tmp.write_text("KEY=value\n# comment\nOTHER=other\n", encoding="utf-8")
        out = self.shim.parse_env_file(tmp)
        self.assertEqual(out, {"KEY": "value", "OTHER": "other"})

    def test_refuses_export_prefix(self) -> None:
        tmp = self.tmp / "fixture.env"
        tmp.write_text("export KEY=value\n", encoding="utf-8")
        with self.assertRaises(self.shim.EnvParseError):
            self.shim.parse_env_file(tmp)


if __name__ == "__main__":
    unittest.main()
