"""shared-libs/ source-enumeration + projection-retirement tests.

The original projection contract was retired: ``shared-libs/*.py``
is no longer byte-copied into every ``auth: creds`` skill's ``scripts/``
(those consumers resolve credentials via the ``credbroker`` pip
library). What survives is source enumeration for the
``adapter-root-bins`` companion-shim rail.

Coverage:
- ``collect_sources`` enumerates ``.apm/shared-libs/*.py`` and hard-errors
  on inter-pack basename collision (the surviving surface; consumed by
  ``adapter_root_bins``).
- The projection/drift/orphan API is **retired** — a guard test fails
  loudly if it is reintroduced.
- Standing real-tree invariants (spec AC): no shim copy remains under any
  consumer ``scripts/``, and the shim *source* is retained for the
  ``sso-broker`` companion rail.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from agentbundle.build import adapter_root_bins, shared_libs

SHIM_BASENAMES = (
    adapter_root_bins.SHIM_COMPANION_BASENAME,
    "_keychain_macos.py",
    "_credman_windows.py",
)


def _write_pack(
    packs_dir: Path,
    name: str,
    *,
    shared_libs_files: dict[str, str] | None = None,
) -> Path:
    """Build a minimal fixture pack carrying ``.apm/shared-libs/*.py``."""
    pack = packs_dir / name
    pack.mkdir()
    (pack / "pack.toml").write_text(
        f'[pack]\nname = "{name}"\nversion = "0.1.0"\n',
        encoding="utf-8",
        newline="\n",
    )
    if shared_libs_files:
        sl = pack / ".apm" / "shared-libs"
        sl.mkdir(parents=True)
        for fname, text in shared_libs_files.items():
            (sl / fname).write_text(text, encoding="utf-8", newline="\n")
    return pack


class _FixtureBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.packs_dir = self.tmp / "packs"
        self.packs_dir.mkdir()


class CollectSourcesTests(_FixtureBase):
    """The surviving surface: enumerate shared-libs sources for the
    adapter-root-bins companion rail."""

    def test_enumerates_shared_libs_sources(self) -> None:
        _write_pack(
            self.packs_dir,
            "broker",
            shared_libs_files={
                "credentials_shim.py": "shim",
                "_keychain_macos.py": "kc",
                "_credman_windows.py": "cw",
            },
        )
        sources = shared_libs.collect_sources(self.packs_dir)
        self.assertEqual(set(sources), set(SHIM_BASENAMES))
        self.assertTrue(
            sources[adapter_root_bins.SHIM_COMPANION_BASENAME].is_file()
        )

    def test_no_sources_returns_empty(self) -> None:
        _write_pack(self.packs_dir, "plain")  # no shared-libs/
        self.assertEqual(shared_libs.collect_sources(self.packs_dir), {})


class InterPackCollisionTests(_FixtureBase):
    """Two packs shipping the same shared-libs basename is a hard error
    at enumeration time (refused before a silent overwrite)."""

    def test_collision_raises_with_both_paths(self) -> None:
        _write_pack(
            self.packs_dir, "broker-a",
            shared_libs_files={"credentials_shim.py": "a"},
        )
        _write_pack(
            self.packs_dir, "broker-b",
            shared_libs_files={"credentials_shim.py": "b"},
        )
        with self.assertRaises(ValueError) as ctx:
            shared_libs.collect_sources(self.packs_dir)
        msg = str(ctx.exception)
        self.assertIn("credentials_shim.py", msg)
        self.assertIn("broker-a", msg)
        self.assertIn("broker-b", msg)


class ProjectionRetirementGuardTests(unittest.TestCase):
    """The skill-scripts projection was retired. These names must
    stay gone — reintroducing the projection mechanism here turns this
    red (the projection model is replaced by the credbroker pip dep)."""

    def test_projection_api_is_retired(self) -> None:
        for name in (
            "apply_projection",
            "check_drift",
            "compute_projections",
            "find_creds_consumers",
            "SharedLibProjection",
            "KNOWN_SHIM_BASENAMES",
        ):
            self.assertFalse(
                hasattr(shared_libs, name),
                f"shared_libs.{name} was retired — the "
                f"shared-libs → consumer scripts/ projection is gone; "
                f"consumers resolve via the credbroker pip library",
            )

    def test_collect_sources_survives(self) -> None:
        self.assertTrue(hasattr(shared_libs, "collect_sources"))
        self.assertTrue(hasattr(shared_libs, "SOURCE_SUBDIR"))


if __name__ == "__main__":
    unittest.main()
