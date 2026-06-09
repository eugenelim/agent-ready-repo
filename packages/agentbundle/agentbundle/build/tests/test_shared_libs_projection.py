"""shared-libs/ source-enumeration + projection-retirement tests.

RFC-0023 retired the original projection contract: ``shared-libs/*.py``
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

import re
import shutil
import tempfile
import unittest
from pathlib import Path

from agentbundle.build import shared_libs

SHIM_BASENAMES = ("credentials_shim.py", "_keychain_macos.py", "_credman_windows.py")
# `credentials_shim` import forms, assembled from parts so this test's own
# source isn't mistaken for a consumer importing the retired shim. Matches
# any import shape — relative (`from .` / `from ..`), dotted-package, or bare
# — so a future re-introduction in any form is caught.
_SHIM_IMPORT_RE = re.compile(
    r"(?:from\s+\.{0,2}(?:[\w.]+\.)?" + "credentials_shim" + r"\s+import"
    r"|import\s+(?:[\w.]+\.)?" + "credentials_shim" + r"\b)"
)


def _repo_root() -> Path:
    """Walk up from this file until a tree carrying the
    ``credential-brokers`` pack is found — robust to test CWD."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "packs" / "credential-brokers").is_dir():
            return parent
    raise RuntimeError("could not locate repo root (packs/credential-brokers)")


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
    )
    if shared_libs_files:
        sl = pack / ".apm" / "shared-libs"
        sl.mkdir(parents=True)
        for fname, text in shared_libs_files.items():
            (sl / fname).write_text(text, encoding="utf-8")
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
        self.assertTrue(sources["credentials_shim.py"].is_file())

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
    """RFC-0023 retired the skill-scripts projection. These names must
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
                f"shared_libs.{name} was retired in RFC-0023 — the "
                f"shared-libs → consumer scripts/ projection is gone; "
                f"consumers resolve via the credbroker pip library",
            )

    def test_collect_sources_survives(self) -> None:
        self.assertTrue(hasattr(shared_libs, "collect_sources"))
        self.assertTrue(hasattr(shared_libs, "SOURCE_SUBDIR"))


class RealTreeInvariantTests(unittest.TestCase):
    """Standing regression against the real repo tree (spec AC for T9)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = _repo_root()

    def test_no_shim_copies_in_any_consumer_scripts(self) -> None:
        """No projected shim copy remains in any pack skill's scripts/
        (the projection was retired; the credbroker pip dep replaces it)."""
        offenders: list[str] = []
        for scripts_dir in self.repo_root.glob("packs/*/.apm/skills/*/scripts"):
            for basename in SHIM_BASENAMES:
                if (scripts_dir / basename).exists():
                    offenders.append(
                        str((scripts_dir / basename).relative_to(self.repo_root))
                    )
        self.assertEqual(
            offenders, [],
            f"retired shim projection reappeared under consumer scripts/: "
            f"{offenders}",
        )

    def test_no_consumer_scripts_imports_the_shim(self) -> None:
        """No `.py` under any consumer `scripts/` imports `credentials_shim`
        — the resolver moved to the `credbroker` pip library (spec AC: the
        six consumers import credbroker and **none** imports the shim). The
        shim files are gone, so a surviving import would also be a dangling
        reference; assert against the import line directly."""
        offenders: list[str] = []
        for py in self.repo_root.glob("packs/*/.apm/skills/*/scripts/*.py"):
            try:
                text = py.read_text(encoding="utf-8")
            except OSError:
                continue
            if _SHIM_IMPORT_RE.search(text):
                offenders.append(str(py.relative_to(self.repo_root)))
        self.assertEqual(
            offenders, [],
            f"consumer scripts/ still import the retired shim "
            f"(resolve via `from credbroker import …` instead): {offenders}",
        )

    def test_shim_source_retained_for_companion_rail(self) -> None:
        """The shim source (`credentials_shim.py` + per-platform backends)
        under credential-brokers/shared-libs/ is KEPT — the adapter-root-bins
        rail projects it into `.agentbundle/bin/` so the sso-broker's
        per-platform Tier-2 backends can `from .credentials_shim import
        Tier2HardFailError` (adapter_root_bins._assert_shim_companion_present
        hard-fails build-check if it's gone)."""
        shared = (
            self.repo_root
            / "packs" / "credential-brokers" / ".apm" / "shared-libs"
        )
        for basename in SHIM_BASENAMES:
            self.assertTrue(
                (shared / basename).is_file(),
                f"companion-rail source {basename} must be retained",
            )

    def test_collect_sources_finds_the_companion_source(self) -> None:
        """collect_sources still locates the shim source on the real tree
        — the input the adapter-root-bins companion rail depends on."""
        sources = shared_libs.collect_sources(self.repo_root / "packs")
        self.assertIn("credentials_shim.py", sources)


if __name__ == "__main__":
    unittest.main()
