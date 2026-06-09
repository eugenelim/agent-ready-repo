"""T3 (credbroker-user-scope): user-libs/ build-pipeline primitive class.

Verifies:
- ``collect_sources``: posix-relpath map, excludes ``__pycache__``/``tests``
- ``apply_projection``: byte-faithful projection to **both** committed
  targets (pack-vendored copy + self-host floor staging); default file
  mode (no exec bit, unlike adapter-root-bins' 0o755); creates dirs;
  overwrites modified; removes orphans
- ``check_drift``: clean / modified / missing / orphaned; ``__pycache__``
  under a target never registers as drift
- no-op when the package source is absent (non-monorepo invocation)
- real-repo smoke: both targets match ``packages/credbroker/credbroker/``
- purity: the vendored floor's base import reaches no third-party module
  (reuses credbroker's import-graph assertion against the vendored copy)
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentbundle.build import user_libs as ul

# Repo root: tests/ -> build/ -> agentbundle/ -> agentbundle/ -> packages/ -> repo
REPO_ROOT = Path(__file__).resolve().parents[5]

# A minimal stand-in package: a pure-base module, a lazily-importing module,
# plus an ``__init__`` — enough to exercise the walk + the purity gate shape.
_FAKE_PACKAGE: dict[str, bytes] = {
    "__init__.py": b"from ._core import value\n",
    "_core.py": b"value = 1\n",
    "_vault.py": b"def crypto():\n    import json  # stand-in lazy import\n    return json\n",
}


def _seed_source(repo_root: Path, files: dict[str, bytes]) -> Path:
    """Lay down ``<repo_root>/packages/credbroker/credbroker/`` with *files*."""
    src = repo_root / ul.PACKAGE_SUBPATH
    src.mkdir(parents=True)
    for rel, content in files.items():
        path = src / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return src


class UserLibsProjectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.packs = self.repo / "packs"
        self.packs.mkdir()
        self.wt = self.repo  # real self-host: working_tree == repo root

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _pack_copy(self) -> Path:
        return (
            self.packs / ul.PACK_NAME / ul.PACK_TARGET_SUBDIR / ul.VENDORED_MODULE
        )

    def _floor(self) -> Path:
        return self.wt / ul.TARGET_SUBDIR / ul.VENDORED_MODULE

    # -- collect_sources -----------------------------------------------------

    def test_collect_sources_returns_relpath_map(self) -> None:
        src = _seed_source(self.repo, _FAKE_PACKAGE)
        sources = ul.collect_sources(src)
        self.assertEqual(set(sources), set(_FAKE_PACKAGE))
        self.assertEqual(sources["_core.py"].read_bytes(), b"value = 1\n")

    def test_collect_sources_excludes_pycache_and_tests(self) -> None:
        files = dict(_FAKE_PACKAGE)
        files["__pycache__/_core.cpython-311.pyc"] = b"\x00bytecode"
        files["tests/test_thing.py"] = b"# test\n"
        src = _seed_source(self.repo, files)
        sources = ul.collect_sources(src)
        self.assertEqual(set(sources), set(_FAKE_PACKAGE))

    def test_collect_sources_absent_source_is_empty(self) -> None:
        self.assertEqual(ul.collect_sources(self.repo / "nope"), {})

    # -- apply_projection ----------------------------------------------------

    def test_apply_projects_both_targets_byte_faithfully(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        for root in (self._pack_copy(), self._floor()):
            for rel, content in _FAKE_PACKAGE.items():
                self.assertEqual((root / rel).read_bytes(), content, f"{root}/{rel}")

    def test_apply_writes_default_mode_no_exec_bit(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        if os.name == "posix":
            for root in (self._pack_copy(), self._floor()):
                mode = stat.S_IMODE((root / "_core.py").stat().st_mode)
                self.assertEqual(
                    mode & 0o111, 0, f"floor must not be executable: {oct(mode)}"
                )

    def test_apply_creates_target_dirs(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        self.assertTrue(self._pack_copy().is_dir())
        self.assertTrue(self._floor().is_dir())

    def test_apply_overwrites_modified_target(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        stale = self._floor() / "_core.py"
        stale.write_bytes(b"value = 999\n")
        ul.apply_projection(self.wt, self.packs)
        self.assertEqual(stale.read_bytes(), b"value = 1\n")

    def test_apply_removes_orphan(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        orphan = self._floor() / "_gone.py"
        orphan.write_bytes(b"# removed upstream\n")
        ul.apply_projection(self.wt, self.packs)
        self.assertFalse(orphan.exists())
        self.assertTrue((self._floor() / "_core.py").is_file())

    def test_apply_noop_when_source_absent(self) -> None:
        # No _seed_source — package source missing.
        ul.apply_projection(self.wt, self.packs)
        self.assertFalse(self._pack_copy().exists())
        self.assertFalse(self._floor().exists())

    # -- check_drift ---------------------------------------------------------

    def test_check_drift_clean_after_apply(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        self.assertEqual(ul.check_drift(self.wt, self.packs), [])

    def test_check_drift_modified_outcome(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        (self._floor() / "_core.py").write_bytes(b"value = 666\n")
        drifts = ul.check_drift(self.wt, self.packs)
        self.assertTrue(any("modified" in d for d in drifts), drifts)
        self.assertTrue(all("make build-self" in d for d in drifts), drifts)

    def test_check_drift_missing_outcome(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        # No apply — every target missing.
        drifts = ul.check_drift(self.wt, self.packs)
        self.assertTrue(drifts)
        self.assertTrue(all("missing" in d for d in drifts), drifts)

    def test_check_drift_orphaned_outcome(self) -> None:
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        (self._floor() / "phantom.py").write_bytes(b"# orphan\n")
        drifts = ul.check_drift(self.wt, self.packs)
        self.assertTrue(any("orphaned" in d and "phantom.py" in d for d in drifts), drifts)

    def test_check_drift_ignores_pycache_under_target(self) -> None:
        """Importing the floor writes ``__pycache__/`` — it must never
        register as orphaned drift."""
        _seed_source(self.repo, _FAKE_PACKAGE)
        ul.apply_projection(self.wt, self.packs)
        cache = self._floor() / "__pycache__"
        cache.mkdir()
        (cache / "_core.cpython-311.pyc").write_bytes(b"\x00bytecode")
        self.assertEqual(ul.check_drift(self.wt, self.packs), [])

    def test_check_drift_noop_when_source_absent(self) -> None:
        self.assertEqual(ul.check_drift(self.wt, self.packs), [])


class UserLibsRealRepoTests(unittest.TestCase):
    """Smoke + purity against the committed repo artifacts."""

    def _floor_dir(self) -> Path:
        return REPO_ROOT / ul.TARGET_SUBDIR / ul.VENDORED_MODULE

    def _package_dir(self) -> Path:
        return REPO_ROOT / ul.PACKAGE_SUBPATH

    def test_real_repo_targets_match_package_source(self) -> None:
        """Both committed targets are byte-faithful to the package source."""
        package = self._package_dir()
        if not package.is_dir():
            self.skipTest("credbroker package source not present")
        pack_copy = (
            REPO_ROOT / "packs" / ul.PACK_NAME / ul.PACK_TARGET_SUBDIR
            / ul.VENDORED_MODULE
        )
        floor = self._floor_dir()
        sources = ul.collect_sources(package)
        self.assertTrue(sources, "no source files collected")
        for rel, src in sources.items():
            self.assertEqual(
                (pack_copy / rel).read_bytes(), src.read_bytes(),
                f"pack copy diverges: {rel}",
            )
            self.assertEqual(
                (floor / rel).read_bytes(), src.read_bytes(),
                f"floor diverges: {rel}",
            )

    def test_vendored_floor_base_import_is_third_party_free(self) -> None:
        """Purity: importing credbroker from the vendored floor pulls no
        third-party module (cryptography/argon2/keyring/agentbundle/…) —
        the floor is stdlib-base, the vault import stays lazy. Subprocess
        with the floor prepended to sys.path so the vendored copy wins over
        any installed credbroker (asserted via ``__file__``)."""
        floor = self._floor_dir()
        if not floor.is_dir():
            self.skipTest("vendored floor not present; run make build-self")
        floor_parent = str(floor.parent)
        script = (
            "import json, sys\n"
            f"sys.path.insert(0, {floor_parent!r})\n"
            "before = set(sys.modules)\n"
            "import credbroker\n"
            "after = set(sys.modules)\n"
            "print(json.dumps({\n"
            "    'file': credbroker.__file__,\n"
            "    'delta': sorted(after - before),\n"
            "    'stdlib': sorted(sys.stdlib_module_names),\n"
            "}))\n"
        )
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        proc = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True, text=True, check=False, env=env,
        )
        self.assertEqual(
            proc.returncode, 0,
            f"floor import failed: stdout={proc.stdout!r} stderr={proc.stderr!r}",
        )
        result = json.loads(proc.stdout.strip())
        self.assertTrue(
            Path(result["file"]).resolve().is_relative_to(floor.resolve()),
            f"imported credbroker from {result['file']!r}, not the floor {floor!r}",
        )
        stdlib = set(result["stdlib"])
        leaked: set[str] = set()
        for mod in result["delta"]:
            root = mod.split(".", 1)[0]
            if root in stdlib or root.startswith("_") or root == "credbroker":
                continue
            leaked.add(mod)
        self.assertEqual(
            leaked, set(),
            f"vendored floor base import pulled non-stdlib modules: {leaked}",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
