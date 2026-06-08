"""Behavioural-contract parity test, ported from the shim's
``test_credentials_shim_load_credentials.py`` (spec task T2).

The resolver's contract — first-hit-wins per key across Tier 1 (env) /
Tier 2 (keyring) / Tier 3 (dotfile), per RFC-0006 § 2 + RFC-0013 § 4 — is
pinned here against the installed ``credbroker`` package (the in-process shape
every ``auth: creds`` consumer now uses). It asserts the same invariants the
shim test did:

- Tier 1 env-var resolution returns the same ``Credentials`` shape.
- Missing required key raises ``CredentialsMissingError`` with namespace +
  missing-keys in the message and structured ``tiers_tried``.
- Tier 3 dotfile read resolves a key the loader would also resolve.
- ``Credentials`` immutability + repr-redaction invariants hold.
- ``parse_env_file`` is the same parser.

Porting note: the shim test planted the module under a throwaway
``fixture_pkg`` to mimic the projected sibling; ``credbroker`` is a real
installed package, so we import it directly and force the Tier-2 backend to
``None`` (this host may be macOS, whose backend would hit the real Keychain).
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import credbroker
from credbroker import _core


class _ResolverBase(unittest.TestCase):
    """Redirect $HOME to a tmp dir and force the Tier-2 backend off so the
    host's real keychain is never touched; restore on cleanup.
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
        # Tests target Tier 1 + Tier 3 only; the host's real keychain must
        # never be exercised. Save and restore the module-level backend.
        self._saved_backend = _core._tier2_backend
        _core._tier2_backend = None
        self.addCleanup(self._restore_backend)

    def _restore_backend(self) -> None:
        _core._tier2_backend = self._saved_backend


class Tier1Tests(_ResolverBase):
    """Tier-1 env-var resolution behaves like the shim's loader."""

    def test_tier1_resolves(self) -> None:
        with patch.dict(os.environ, {"SHIMNS_API_TOKEN": "shim-secret"}):
            creds = credbroker.load_credentials("shimns", required_keys=["API_TOKEN"])
        self.assertIsInstance(creds, credbroker.Credentials)
        self.assertEqual(creds.API_TOKEN, "shim-secret")

    def test_credentials_repr_redacts_values(self) -> None:
        with patch.dict(os.environ, {"SHIMNS_API_TOKEN": "should-never-leak"}):
            creds = credbroker.load_credentials("shimns", required_keys=["API_TOKEN"])
        r = repr(creds)
        self.assertNotIn("should-never-leak", r)
        self.assertIn("shimns", r)
        self.assertIn("API_TOKEN", r)

    def test_credentials_is_immutable(self) -> None:
        with patch.dict(os.environ, {"SHIMNS_API_TOKEN": "v"}):
            creds = credbroker.load_credentials("shimns", required_keys=["API_TOKEN"])
        with self.assertRaises(AttributeError):
            creds.API_TOKEN = "other"  # type: ignore[misc]


class MissingKeyTests(_ResolverBase):
    """Missing required key raises CredentialsMissingError with the
    same shape RFC-0006 § AC3 froze."""

    def test_missing_raises(self) -> None:
        with self.assertRaises(credbroker.CredentialsMissingError) as ctx:
            credbroker.load_credentials("shimns", required_keys=["API_TOKEN"])
        msg = str(ctx.exception)
        self.assertIn("shimns", msg)
        self.assertIn("API_TOKEN", msg)
        self.assertEqual(ctx.exception.namespace, "shimns")
        self.assertEqual(ctx.exception.missing, ["API_TOKEN"])
        self.assertIn("API_TOKEN", ctx.exception.tiers_tried)


class Tier3Tests(_ResolverBase):
    """Tier-3 dotfile read resolves a key the loader would also resolve."""

    def test_tier3_dotfile_resolves(self) -> None:
        agentbundle = self.home / ".agentbundle"
        agentbundle.mkdir(mode=0o700)
        dotfile = agentbundle / "credentials.env"
        dotfile.write_text("SHIMNS_API_TOKEN=tier3-value\n", encoding="utf-8")
        if os.name == "posix":
            os.chmod(dotfile, 0o600)
        creds = credbroker.load_credentials("shimns", required_keys=["API_TOKEN"])
        self.assertEqual(creds.API_TOKEN, "tier3-value")

    def test_tier3_dotfile_quoted_value(self) -> None:
        agentbundle = self.home / ".agentbundle"
        agentbundle.mkdir(mode=0o700)
        dotfile = agentbundle / "credentials.env"
        dotfile.write_text('SHIMNS_API_TOKEN="value with spaces"\n', encoding="utf-8")
        creds = credbroker.load_credentials("shimns", required_keys=["API_TOKEN"])
        self.assertEqual(creds.API_TOKEN, "value with spaces")


class EnvParseSurfaceTests(_ResolverBase):
    """parse_env_file is the same parser the shim exposed."""

    def test_basic_parse(self) -> None:
        tmp = self.tmp / "fixture.env"
        tmp.write_text("KEY=value\n# comment\nOTHER=other\n", encoding="utf-8")
        out = credbroker.parse_env_file(tmp)
        self.assertEqual(out, {"KEY": "value", "OTHER": "other"})

    def test_refuses_export_prefix(self) -> None:
        tmp = self.tmp / "fixture.env"
        tmp.write_text("export KEY=value\n", encoding="utf-8")
        with self.assertRaises(credbroker.EnvParseError):
            credbroker.parse_env_file(tmp)


if __name__ == "__main__":
    unittest.main()
