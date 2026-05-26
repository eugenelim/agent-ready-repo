"""T6 (credential-broker-contract): adapter-root-bins/ build-pipeline
primitive class — AC22 / AC23.

Verifies:
- AC22: source-to-target projection at `<working_tree>/.agentbundle/bin/<basename>.py`
- AC22: POSIX mode 0o755
- AC22: path-jail compliance — the target falls under the v0.7
  contract's `allowed-prefixes.repo` for `.agentbundle/`
- AC22: no PATH manipulation — `os.environ["PATH"]` unchanged
- AC23: drift gate distinguishes modified / missing / orphaned;
  build-self resolves all three; inter-pack basename collision is hard-error
"""

from __future__ import annotations

import os
import stat
import tempfile
import tomllib
import unittest
from pathlib import Path

from agentbundle.build import adapter_root_bins as arb


def _make_fixture_pack(packs_dir: Path, name: str, bins: dict[str, bytes]) -> Path:
    pack = packs_dir / name
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.1.0"\ndescription = "fixture"\n'
        f'[pack.adapter-contract]\nversion = "0.7"\n'
        f'[pack.install]\ndefault-scope = "user"\n'
        f'allowed-scopes = ["user", "repo"]\n',
        encoding="utf-8",
    )
    bins_dir = pack / ".apm" / "adapter-root-bins"
    bins_dir.mkdir(parents=True)
    for basename, content in bins.items():
        (bins_dir / basename).write_bytes(content)
    return pack


class AdapterRootBinsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _packs(self) -> Path:
        packs = self.tmp_path / "packs"
        packs.mkdir(exist_ok=True)
        return packs

    def _wt(self) -> Path:
        wt = self.tmp_path / "wt"
        wt.mkdir(exist_ok=True)
        return wt

    def test_collect_sources_returns_basename_map(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# stub\n"})
        sources = arb.collect_sources(packs)
        self.assertEqual(set(sources.keys()), {"sso-broker.py"})
        self.assertEqual(sources["sso-broker.py"].read_bytes(), b"# stub\n")

    def test_collect_sources_collision_hard_errors(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# p1\n"})
        _make_fixture_pack(packs, "p2", {"sso-broker.py": b"# p2\n"})
        with self.assertRaisesRegex(ValueError, "adapter-root-bins collision"):
            arb.collect_sources(packs)

    def test_apply_projection_writes_target_with_0755(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# real broker\n"})
        wt = self._wt()

        arb.apply_projection(wt, packs)

        target = wt / ".agentbundle" / "bin" / "sso-broker.py"
        self.assertTrue(target.is_file())
        self.assertEqual(target.read_bytes(), b"# real broker\n")
        if os.name == "posix":
            mode = stat.S_IMODE(target.stat().st_mode)
            self.assertEqual(
                mode & 0o777, 0o755, f"expected mode 0755, got {oct(mode)}"
            )

    def test_apply_projection_creates_target_dir(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# stub\n"})
        wt = self._wt()
        arb.apply_projection(wt, packs)
        self.assertTrue((wt / ".agentbundle" / "bin").is_dir())

    def test_apply_projection_overwrites_modified_target(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# source\n"})
        wt = self._wt()
        bin_dir = wt / ".agentbundle" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "sso-broker.py").write_bytes(b"# stale\n")

        arb.apply_projection(wt, packs)

        self.assertEqual(
            (bin_dir / "sso-broker.py").read_bytes(), b"# source\n"
        )

    def test_apply_projection_removes_orphan(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# real\n"})
        wt = self._wt()
        bin_dir = wt / ".agentbundle" / "bin"
        bin_dir.mkdir(parents=True)
        (bin_dir / "stale.py").write_bytes(b"# orphan\n")

        arb.apply_projection(wt, packs)

        self.assertFalse((bin_dir / "stale.py").exists())
        self.assertTrue((bin_dir / "sso-broker.py").is_file())

    def test_check_drift_clean_after_apply(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# real\n"})
        wt = self._wt()
        arb.apply_projection(wt, packs)
        self.assertEqual(arb.check_drift(wt, packs), [])

    def test_check_drift_modified_outcome(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# source\n"})
        wt = self._wt()
        arb.apply_projection(wt, packs)
        target = wt / ".agentbundle" / "bin" / "sso-broker.py"
        target.write_bytes(b"# tampered\n")

        drifts = arb.check_drift(wt, packs)
        self.assertEqual(len(drifts), 1)
        self.assertIn("modified", drifts[0])
        self.assertIn("make build-self", drifts[0])

    def test_check_drift_missing_outcome(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# source\n"})
        wt = self._wt()
        # No apply_projection — target missing.

        drifts = arb.check_drift(wt, packs)
        self.assertEqual(len(drifts), 1)
        self.assertIn("missing", drifts[0])
        self.assertIn("make build-self", drifts[0])

    def test_check_drift_orphaned_outcome(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# real\n"})
        wt = self._wt()
        arb.apply_projection(wt, packs)
        orphan = wt / ".agentbundle" / "bin" / "phantom.py"
        orphan.write_bytes(b"# orphan\n")

        drifts = arb.check_drift(wt, packs)
        self.assertTrue(any("orphaned" in d for d in drifts))

    def test_check_drift_collision_short_circuits(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# p1\n"})
        _make_fixture_pack(packs, "p2", {"sso-broker.py": b"# p2\n"})
        wt = self._wt()
        drifts = arb.check_drift(wt, packs)
        self.assertEqual(len(drifts), 1)
        self.assertIn("collision", drifts[0])

    def test_no_path_manipulation(self) -> None:
        """AC22: os.environ['PATH'] is unchanged before/after apply_projection."""
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# real\n"})
        wt = self._wt()
        path_before = os.environ.get("PATH", "")
        arb.apply_projection(wt, packs)
        path_after = os.environ.get("PATH", "")
        self.assertEqual(path_before, path_after)

    def test_path_jail_compliance_against_contract(self) -> None:
        """AC22 path-jail: `.agentbundle/` is in `allowed-prefixes.repo`
        for the named user-scope adapters in the v0.7 contract."""
        contract_path = (
            Path(__file__).resolve().parents[2] / "_data" / "adapter.toml"
        )
        with contract_path.open("rb") as fh:
            contract = tomllib.load(fh)
        for adapter_name in ("claude-code", "kiro"):
            prefixes = contract["adapter"][adapter_name]["scope"][
                "allowed-prefixes"
            ]["repo"]
            target_prefix = str(arb.TARGET_SUBDIR.parts[0]) + "/"
            self.assertIn(
                target_prefix, prefixes,
                f"adapter {adapter_name!r}: {target_prefix!r} not in {prefixes!r}",
            )

    def test_real_pack_projection_against_credential_brokers(self) -> None:
        """Smoke test: the real credential-brokers pack source projects
        into <tmp>/.agentbundle/bin/sso-broker.py with the real bytes."""
        real_packs = Path(__file__).resolve().parents[5] / "packs"
        if not (real_packs / "credential-brokers").is_dir():
            self.skipTest("credential-brokers pack not present")
        wt = self.tmp_path / "real-wt"
        wt.mkdir()
        arb.apply_projection(wt, real_packs)
        target = wt / ".agentbundle" / "bin" / "sso-broker.py"
        source = (
            real_packs / "credential-brokers" / ".apm"
            / "adapter-root-bins" / "sso-broker.py"
        )
        self.assertEqual(target.read_bytes(), source.read_bytes())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
