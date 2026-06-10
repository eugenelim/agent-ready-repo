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


def _make_fixture_pack(
    packs_dir: Path,
    name: str,
    bins: dict[str, bytes],
    shared_libs: dict[str, bytes] | None = None,
) -> Path:
    pack = packs_dir / name
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.1.0"\ndescription = "fixture"\n'
        f'[pack.adapter-contract]\nversion = "0.7"\n'
        f'[pack.install]\ndefault-scope = "user"\n'
        f'allowed-scopes = ["user", "repo"]\n',
        encoding="utf-8",
    )
    if bins:
        bins_dir = pack / ".apm" / "adapter-root-bins"
        bins_dir.mkdir(parents=True)
        for basename, content in bins.items():
            (bins_dir / basename).write_bytes(content)
    if shared_libs:
        sl_dir = pack / ".apm" / "shared-libs"
        sl_dir.mkdir(parents=True)
        for basename, content in shared_libs.items():
            (sl_dir / basename).write_bytes(content)
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


class AdapterRootBinsShimCompanionTests(unittest.TestCase):
    """AC22b: shim-companion projection alongside adapter-root-bins/.

    Closes the deferred-projection gap from the credential
    user-install fix — under bare user-scope
    install, `_sso_*` modules' `from .credentials_shim import
    Tier2HardFailError` previously failed and `sso-broker.py`'s
    try/except cascade silently degraded `_tier2_backend` to `None`
    on macOS / Windows.
    """

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

    def test_apply_projection_writes_shim_companion(self) -> None:
        """AC22b: pack ships both adapter-root-bins/ and
        shared-libs/credentials_shim.py — companion projected as a
        sibling under bin/."""
        packs = self._packs()
        _make_fixture_pack(
            packs,
            "p1",
            bins={"sso-broker.py": b"# broker\n"},
            shared_libs={"credentials_shim.py": b"# shim\n"},
        )
        wt = self._wt()
        arb.apply_projection(wt, packs)
        bin_dir = wt / ".agentbundle" / "bin"
        self.assertEqual((bin_dir / "sso-broker.py").read_bytes(), b"# broker\n")
        self.assertEqual(
            (bin_dir / "credentials_shim.py").read_bytes(), b"# shim\n"
        )

    def test_apply_projection_omits_companion_when_adapter_root_bins_absent(
        self,
    ) -> None:
        """Opt-in by ship-both. A pack that ships only shared-libs/ —
        no adapter-root-bins/ — does NOT trigger the bin/ companion."""
        packs = self._packs()
        # Use ``bins={}`` then strip the empty dir so the fixture
        # really only has shared-libs/.
        _make_fixture_pack(
            packs,
            "p1",
            bins={},
            shared_libs={"credentials_shim.py": b"# shim\n"},
        )
        wt = self._wt()
        arb.apply_projection(wt, packs)
        bin_dir = wt / ".agentbundle" / "bin"
        # No adapter-root-bins source → no bin/ at all.
        self.assertFalse(
            (bin_dir / "credentials_shim.py").exists(),
            "companion projected without an adapter-root-bins/ trigger",
        )

    def test_apply_projection_hard_errors_on_shim_import_without_companion(
        self,
    ) -> None:
        """AC22b content-grep rail. A pack ships an adapter-root-bins
        module that imports the shim, but does NOT ship the shim
        source — refuse the build with the broker-agnostic message.
        Uses a non-`_sso_*` basename to exercise the generalised
        trigger (the rail must not be coupled to `_sso_*`)."""
        packs = self._packs()
        _make_fixture_pack(
            packs,
            "p1",
            bins={
                "oauth-broker.py": b"# stub\n",
                "_oauth_macos.py": (
                    b"from .credentials_shim import Tier2HardFailError\n"
                ),
            },
            shared_libs=None,  # NB: no credentials_shim.py in pack.
        )
        wt = self._wt()
        with self.assertRaises(ValueError) as cm:
            arb.apply_projection(wt, packs)
        msg = str(cm.exception)
        self.assertIn("_oauth_macos.py", msg)
        self.assertIn("credentials_shim.py is missing", msg)
        self.assertIn(
            "Tier-2 dispatch would degrade silently on macOS/Windows", msg,
            f"hard-error message must be broker-agnostic; got: {msg!r}",
        )

    def test_check_drift_modified_shim_companion_carries_prefix(self) -> None:
        """AC22b: companion drift descriptions use the
        `[adapter-root-bins:shim-companion]` prefix so the source-side
        reference (under `shared-libs/`) reads coherently."""
        packs = self._packs()
        _make_fixture_pack(
            packs,
            "p1",
            bins={"sso-broker.py": b"# broker\n"},
            shared_libs={"credentials_shim.py": b"# shim\n"},
        )
        wt = self._wt()
        arb.apply_projection(wt, packs)
        # Tamper the companion target.
        (wt / ".agentbundle" / "bin" / "credentials_shim.py").write_bytes(
            b"# tampered\n"
        )

        drifts = arb.check_drift(wt, packs)
        companion_drifts = [
            d for d in drifts if "[adapter-root-bins:shim-companion]" in d
        ]
        self.assertEqual(len(companion_drifts), 1, drifts)
        self.assertIn("modified", companion_drifts[0])
        # The companion source is rooted in shared-libs/ — the
        # diagnostic reference must name that.
        self.assertIn("shared-libs/credentials_shim.py", companion_drifts[0])

    def test_check_drift_missing_shim_companion_carries_prefix(self) -> None:
        """Companion target absent → missing drift with the
        shim-companion prefix."""
        packs = self._packs()
        _make_fixture_pack(
            packs,
            "p1",
            bins={"sso-broker.py": b"# broker\n"},
            shared_libs={"credentials_shim.py": b"# shim\n"},
        )
        wt = self._wt()
        # No apply_projection — every target is missing. We isolate
        # the companion's diagnostic shape.
        drifts = arb.check_drift(wt, packs)
        companion_missing = [
            d for d in drifts
            if "[adapter-root-bins:shim-companion]" in d and "missing" in d
        ]
        self.assertEqual(len(companion_missing), 1, drifts)

    def test_check_drift_orphaned_companion_not_misfiring(self) -> None:
        """The companion target must land in `expected_targets` so
        the orphan rail does not flag it. After `apply_projection`,
        `check_drift` returns no entries — and in particular no
        `orphaned` entry referencing `credentials_shim.py`."""
        packs = self._packs()
        _make_fixture_pack(
            packs,
            "p1",
            bins={"sso-broker.py": b"# broker\n"},
            shared_libs={"credentials_shim.py": b"# shim\n"},
        )
        wt = self._wt()
        arb.apply_projection(wt, packs)
        drifts = arb.check_drift(wt, packs)
        self.assertEqual(drifts, [])
        # Explicit invariant: even if a future contributor relaxes the
        # equality check above, the companion must never be reported
        # as orphaned.
        self.assertFalse(
            any("orphaned" in d and "credentials_shim.py" in d for d in drifts),
            f"orphan rail misfired on the shim companion: {drifts}",
        )

    def test_real_pack_projection_includes_shim_companion(self) -> None:
        """Smoke test: the real `credential-brokers` pack projects
        `credentials_shim.py` into `<wt>/.agentbundle/bin/` with the
        real shared-libs source bytes."""
        real_packs = Path(__file__).resolve().parents[5] / "packs"
        if not (real_packs / "credential-brokers").is_dir():
            self.skipTest("credential-brokers pack not present")
        wt = self.tmp_path / "real-wt"
        wt.mkdir()
        arb.apply_projection(wt, real_packs)
        target = wt / ".agentbundle" / "bin" / "credentials_shim.py"
        source = (
            real_packs / "credential-brokers" / ".apm"
            / "shared-libs" / "credentials_shim.py"
        )
        self.assertTrue(
            target.is_file(),
            "AC22b companion projection did not write "
            "credentials_shim.py into bin/ from the real pack",
        )
        self.assertEqual(target.read_bytes(), source.read_bytes())


class CollectPackRootBinsTests(unittest.TestCase):
    """credbroker-user-scope T4: the single-pack, companion-aware
    enumeration `agentbundle install` uses (it owns its own scope jail and
    can't call the multi-pack, working-tree-folding `compute_projections`)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp_path = Path(self._tmp.name)

    def test_empty_when_pack_ships_no_adapter_root_bins(self) -> None:
        pack = _make_fixture_pack(self.tmp_path / "packs", "no-bins", bins={})
        self.assertEqual(arb.collect_pack_root_bins(pack), {})

    def test_bins_without_companion_when_no_shim_shipped(self) -> None:
        pack = _make_fixture_pack(
            self.tmp_path / "packs", "bins-only", bins={"sso-broker.py": b"x\n"}
        )
        got = arb.collect_pack_root_bins(pack)
        self.assertEqual(set(got), {"sso-broker.py"})

    def test_includes_companion_shim_on_ship_both(self) -> None:
        # Ship both adapter-root-bins/ AND shared-libs/credentials_shim.py →
        # the companion rides along (a bare glob would miss it, landing the
        # _sso_* backends' `from .credentials_shim import` broken).
        pack = _make_fixture_pack(
            self.tmp_path / "packs",
            "both",
            bins={
                "sso-broker.py": b"a\n",
                "_sso_keychain_macos.py": b"from .credentials_shim import X\n",
            },
            shared_libs={"credentials_shim.py": b"shim\n"},
        )
        got = arb.collect_pack_root_bins(pack)
        self.assertEqual(
            set(got),
            {"sso-broker.py", "_sso_keychain_macos.py", "credentials_shim.py"},
        )
        self.assertEqual(
            got["credentials_shim.py"],
            pack / ".apm" / "shared-libs" / "credentials_shim.py",
        )

    def test_skips_symlinked_bin_source(self) -> None:
        # install resolves pack_dir from an untrusted catalogue and lands these
        # bytes executable — a symlinked *.py pointing out of tree must not be
        # read into the floor.
        if os.name != "posix":
            self.skipTest("symlink creation needs privilege on Windows")
        secret = self.tmp_path / "secret.txt"
        secret.write_bytes(b"SECRET\n")
        pack = _make_fixture_pack(
            self.tmp_path / "packs", "sneaky", bins={"sso-broker.py": b"ok\n"}
        )
        link = pack / ".apm" / "adapter-root-bins" / "evil.py"
        link.symlink_to(secret)
        got = arb.collect_pack_root_bins(pack)
        self.assertEqual(set(got), {"sso-broker.py"}, "symlinked bin must be skipped")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
