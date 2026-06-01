"""Tests for the kiro deprecated alias (T4 — RFC-0022).

The `kiro` adapter is retained as a deprecated alias for `kiro-ide`.
Packs declaring `allowed-adapters = ["kiro"]` keep working; a
build-time deprecation warning is emitted.
"""

from __future__ import annotations

import json
import tempfile
import unittest
import warnings
from pathlib import Path

from agentbundle.build.adapters import ADAPTERS, kiro_ide
from agentbundle.build.contract import load as load_contract

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = REPO_ROOT / "docs" / "contracts" / "adapter.toml"


def _seed_pack(root: Path) -> Path:
    pack = root / "pack"
    (pack / ".apm" / "agents").mkdir(parents=True)
    (pack / ".apm" / "agents" / "foo.md").write_text(
        "---\nname: foo\ntools: Read\n---\nbody\n",
        encoding="utf-8",
    )
    return pack


class KiroAliasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_contract(CONTRACT_PATH)

    def test_kiro_resolves_to_kiro_ide(self) -> None:
        """ADAPTERS["kiro"] dispatches to kiro-ide's projection logic.

        Project a minimal pack using both "kiro" and "kiro-ide" entries
        and verify they produce identical output.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out_kiro = tmp_path / "out-kiro"
            out_kiro_ide = tmp_path / "out-kiro-ide"

            kiro_func = ADAPTERS.get("kiro")
            self.assertIsNotNone(kiro_func, "ADAPTERS must register 'kiro'")

            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                kiro_func(pack, self.contract, out_kiro)

            kiro_ide.project(pack, self.contract, out_kiro_ide)

            alias_json = (out_kiro / ".kiro" / "agents" / "foo.json").read_bytes()
            ide_json = (out_kiro_ide / ".kiro" / "agents" / "foo.json").read_bytes()
            self.assertEqual(
                alias_json,
                ide_json,
                "kiro alias must produce identical output to kiro-ide",
            )

    def test_kiro_emits_deprecation_warning(self) -> None:
        """Calling the kiro alias emits a DeprecationWarning containing 'kiro-ide'."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            pack = _seed_pack(tmp_path)
            out = tmp_path / "out"
            kiro_func = ADAPTERS["kiro"]

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                kiro_func(pack, self.contract, out)

            dep_warnings = [
                w for w in caught if issubclass(w.category, DeprecationWarning)
            ]
            self.assertTrue(dep_warnings, "kiro alias must emit a DeprecationWarning")
            messages = " ".join(str(w.message) for w in dep_warnings)
            self.assertIn("kiro-ide", messages, "warning must mention 'kiro-ide'")

    def test_kiro_alias_in_shipped_for_cli(self) -> None:
        """'kiro' must appear in the shipped adapters derived from the contract.

        The [adapter.kiro] stub block in adapter.toml ensures the adapter
        key is present, so `_shipped_for_cli` (derived from the contract's
        adapter key set) continues to include 'kiro'.
        """
        from agentbundle.scope import shipped_adapters_from_contract

        shipped = shipped_adapters_from_contract()
        self.assertIn(
            "kiro",
            shipped,
            "'kiro' must be in shipped adapters (alias stub block keeps it in the contract)",
        )


if __name__ == "__main__":
    unittest.main()
