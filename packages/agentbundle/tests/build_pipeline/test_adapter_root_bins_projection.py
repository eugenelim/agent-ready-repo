"""T6 (credential-broker-contract): adapter-root-bins/ build-pipeline
primitive class.

Verifies:
- Source-to-target projection at `<working_tree>/.agentbundle/bin/<basename>.py`
- POSIX mode 0o755
- Path-jail compliance — the target falls under the v0.7
  contract's `allowed-prefixes.repo` for `.agentbundle/`
- No PATH manipulation — `os.environ["PATH"]` unchanged
- Drift gate distinguishes modified / missing / orphaned;
  build-self resolves all three; inter-pack basename collision is hard-error
"""

from __future__ import annotations

import os
import stat
import tempfile
import tomllib
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agentbundle.build import adapter_root_bins as arb
from agentbundle.build.main import CONTRACT_PATH


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
        newline="\n",
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

    @unittest.skipIf(os.name != "posix", "control-byte filenames require POSIX")
    def test_collision_hard_error_escapes_control_characters(self) -> None:
        """Collision basenames and both source paths remain one-line."""
        filename = "line\nbreak\r\x1b.py"
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {filename: b"# p1\n"})
        _make_fixture_pack(packs, "p2", {filename: b"# p2\n"})

        with self.assertRaises(ValueError) as caught:
            arb.collect_sources(packs)

        rendered = str(caught.exception)
        self.assertIn("line\\nbreak\\r\\u001b.py", rendered)
        self.assertNotIn("line\nbreak", rendered)

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

    @unittest.skipIf(os.name != "posix", "symlink semantics require POSIX")
    def test_check_drift_rejects_symlink_target(self) -> None:
        """The executable drift gate never follows an on-disk target symlink."""
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# source\n"})
        wt = self._wt()
        outside = self.tmp_path / "outside.py"
        outside.write_bytes(b"# source\n")
        target = wt / ".agentbundle" / "bin" / "sso-broker.py"
        target.parent.mkdir(parents=True)
        target.symlink_to(outside)

        drifts = arb.check_drift(wt, packs)

        self.assertTrue(any("type mismatch" in drift for drift in drifts))
        self.assertTrue(target.is_symlink())

    @unittest.skipIf(os.name != "posix", "symlink semantics require POSIX")
    def test_apply_replaces_symlink_target_without_touching_referent(self) -> None:
        """The advertised repair replaces a link instead of following it."""
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# source\n"})
        wt = self._wt()
        outside = self.tmp_path / "outside.py"
        outside.write_bytes(b"# outside\n")
        target = wt / ".agentbundle" / "bin" / "sso-broker.py"
        target.parent.mkdir(parents=True)
        target.symlink_to(outside)

        arb.apply_projection(wt, packs)

        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_bytes(), b"# source\n")
        self.assertEqual(outside.read_bytes(), b"# outside\n")

    @unittest.skipIf(os.name != "posix", "symlink semantics require POSIX")
    def test_apply_replaces_symlinked_target_root(self) -> None:
        """Repair replaces the owned bin-root link without following it."""
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# source\n"})
        wt = self._wt()
        outside = self.tmp_path / "outside-bin"
        outside.mkdir()
        target_dir = wt / ".agentbundle" / "bin"
        target_dir.parent.mkdir()
        target_dir.symlink_to(outside, target_is_directory=True)

        drifts = arb.check_drift(wt, packs)
        arb.apply_projection(wt, packs)

        self.assertTrue(any("type mismatch" in drift for drift in drifts), drifts)
        self.assertFalse(target_dir.is_symlink())
        self.assertEqual(
            (target_dir / "sso-broker.py").read_bytes(), b"# source\n"
        )
        self.assertEqual(list(outside.iterdir()), [])

    @unittest.skipIf(os.name != "posix", "dir-fd semantics require POSIX")
    def test_atomic_replace_defeats_leaf_symlink_swap(self) -> None:
        """A link swapped in immediately before replace cannot redirect bytes."""
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# source\n"})
        wt = self._wt()
        arb.apply_projection(wt, packs)
        target = wt / ".agentbundle" / "bin" / "sso-broker.py"
        outside = self.tmp_path / "outside.py"
        outside.write_bytes(b"# outside\n")
        real_replace = os.replace
        swapped = False

        def racing_replace(source, destination, **kwargs):
            nonlocal swapped
            if destination == "sso-broker.py" and not swapped:
                swapped = True
                target.unlink()
                target.symlink_to(outside)
            return real_replace(source, destination, **kwargs)

        with patch(
            "agentbundle.build.projection_io.os.replace",
            side_effect=racing_replace,
        ):
            arb.apply_projection(wt, packs)

        self.assertTrue(swapped)
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_bytes(), b"# source\n")
        self.assertEqual(outside.read_bytes(), b"# outside\n")

    def test_orphan_scan_continues_after_disappearing_entry(self) -> None:
        """One raced-away entry does not hide the remaining orphan names."""
        target_dir = self._wt() / ".agentbundle" / "bin"
        with (
            patch.object(os, "listdir", return_value=["gone.py", "orphan.py"]),
            patch.object(
                os,
                "stat",
                side_effect=[
                    FileNotFoundError("gone"),
                    SimpleNamespace(st_mode=stat.S_IFREG),
                ],
            ),
        ):
            names = arb._target_python_names(target_dir, 42)

        self.assertEqual(names, ["orphan.py"])

    def test_orphan_root_permission_error_becomes_drift(self) -> None:
        """An exceptional orphan-root read is actionable, not a traceback."""
        packs = self._packs()
        wt = self._wt()
        (wt / ".agentbundle" / "bin").mkdir(parents=True)
        with patch.object(
            arb,
            "open_directory_no_follow",
            side_effect=PermissionError("denied"),
        ):
            drifts = arb.check_drift(wt, packs)

        self.assertTrue(
            any(
                '[adapter-root-bins] unreadable: ".agentbundle/bin"' in drift
                and "denied" in drift
                and "make build-self" in drift
                for drift in drifts
            ),
            drifts,
        )

    @unittest.skipIf(os.name != "posix", "control-byte filenames require POSIX")
    def test_orphan_diagnostic_escapes_control_characters(self) -> None:
        """A filesystem-discovered orphan cannot forge another log line."""
        packs = self._packs()
        wt = self._wt()
        target_dir = wt / ".agentbundle" / "bin"
        target_dir.mkdir(parents=True)
        (target_dir / "line\nbreak\r\x1b.py").write_bytes(b"orphan\n")

        drifts = arb.check_drift(wt, packs)
        rendered = "\n".join(drifts)

        self.assertIn('".agentbundle/bin/line\\nbreak\\r\\u001b.py"', rendered)
        self.assertNotIn("line\nbreak", rendered)

    @unittest.skipIf(os.name != "posix", "control-byte filenames require POSIX")
    def test_all_drift_outcomes_escape_control_characters(self) -> None:
        """Missing/type/mode/modified target and source paths stay one-line."""
        filename = "line\nbreak\r\x1b.py"
        escaped = "line\\nbreak\\r\\u001b.py"
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {filename: b"# source\n"})
        wt = self._wt()

        missing = "\n".join(arb.check_drift(wt, packs))
        arb.apply_projection(wt, packs)
        target = wt / ".agentbundle" / "bin" / filename
        target.chmod(0o644)
        target.write_bytes(b"# modified\n")
        mode_and_modified = "\n".join(arb.check_drift(wt, packs))
        outside = self.tmp_path / "outside-control.py"
        outside.write_bytes(b"# source\n")
        target.unlink()
        target.symlink_to(outside)
        type_mismatch = "\n".join(arb.check_drift(wt, packs))

        for rendered in (missing, mode_and_modified, type_mismatch):
            self.assertIn(escaped, rendered)
            self.assertNotIn("line\nbreak", rendered)
        self.assertIn("missing", missing)
        self.assertIn("mode drift", mode_and_modified)
        self.assertIn("modified", mode_and_modified)
        self.assertIn("type mismatch", type_mismatch)

    @unittest.skipIf(os.name != "posix", "POSIX mode bits are unavailable")
    def test_check_drift_rejects_posix_mode_drift(self) -> None:
        """The executable drift gate enforces the projected 0o755 mode."""
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# source\n"})
        wt = self._wt()
        arb.apply_projection(wt, packs)
        target = wt / ".agentbundle" / "bin" / "sso-broker.py"
        target.chmod(0o644)

        drifts = arb.check_drift(wt, packs)

        self.assertTrue(any("mode drift" in drift for drift in drifts))
        self.assertTrue(
            any("0o644" in drift and "0o755" in drift for drift in drifts)
        )

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
        """os.environ['PATH'] is unchanged before/after apply_projection."""
        packs = self._packs()
        _make_fixture_pack(packs, "p1", {"sso-broker.py": b"# real\n"})
        wt = self._wt()
        path_before = os.environ.get("PATH", "")
        arb.apply_projection(wt, packs)
        path_after = os.environ.get("PATH", "")
        self.assertEqual(path_before, path_after)

    def test_path_jail_compliance_against_contract(self) -> None:
        """Path-jail: `.agentbundle/` is in `allowed-prefixes.repo`
        for the named user-scope adapters in the v0.7 contract."""
        with CONTRACT_PATH.open("rb") as fh:
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

    def test_fixture_pack_projection_preserves_broker_bytes(self) -> None:
        packs = self._packs()
        _make_fixture_pack(packs, "broker", {"sso-broker.py": b"# broker\n"})
        wt = self._wt()
        arb.apply_projection(wt, packs)
        target = wt / ".agentbundle" / "bin" / "sso-broker.py"
        self.assertEqual(target.read_bytes(), b"# broker\n")


class AdapterRootBinsShimCompanionTests(unittest.TestCase):
    """Shim-companion projection alongside adapter-root-bins/.

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
        """Pack ships both adapter-root-bins/ and
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
        """Content-grep rail. A pack ships an adapter-root-bins
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

    @unittest.skipIf(os.name != "posix", "control-byte filenames require POSIX")
    def test_shim_hard_error_escapes_control_characters(self) -> None:
        """Shim offender lists cannot forge lines before drift checking."""
        filename = "line\nbreak\r\x1b.py"
        packs = self._packs()
        _make_fixture_pack(
            packs,
            "p1",
            bins={
                filename: b"from .credentials_shim import Tier2HardFailError\n"
            },
        )

        with self.assertRaises(ValueError) as caught:
            arb.apply_projection(self._wt(), packs)

        rendered = str(caught.exception)
        self.assertIn("line\\nbreak\\r\\u001b.py", rendered)
        self.assertNotIn("line\nbreak", rendered)

    def test_check_drift_modified_shim_companion_carries_prefix(self) -> None:
        """Companion drift descriptions use the
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

    def test_fixture_pack_projection_includes_shim_companion(self) -> None:
        packs = self._packs()
        _make_fixture_pack(
            packs,
            "broker",
            bins={"sso-broker.py": b"# broker\n"},
            shared_libs={arb.SHIM_COMPANION_BASENAME: b"# shim\n"},
        )
        wt = self._wt()
        arb.apply_projection(wt, packs)
        target = wt / ".agentbundle" / "bin" / "credentials_shim.py"
        self.assertTrue(target.is_file())
        self.assertEqual(target.read_bytes(), b"# shim\n")


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
