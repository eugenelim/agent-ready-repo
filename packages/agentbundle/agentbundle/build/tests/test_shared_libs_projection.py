"""T4: shared-libs/ build-pipeline primitive projection tests.

Covers AC20 (project per skill declaring metadata.auth: creds),
AC20 trailing clause (scripts/ created if absent), AC21 (inter-pack
collision), AC23 (drift gate: modified/missing/orphaned), AC25
(no projection into skills NOT declaring auth: creds).
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from agentbundle.build import shared_libs


def _write_pack(
    packs_dir: Path,
    name: str,
    *,
    shared_libs_files: dict[str, str] | None = None,
    skills: dict[str, dict] | None = None,
) -> Path:
    """Build a fixture pack tree.

    skills entries: {skill_name: {"auth": "creds"|"env", "scripts": {basename: text}}}
    """
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
    if skills:
        skills_dir = pack / ".apm" / "skills"
        skills_dir.mkdir(parents=True)
        for skill_name, opts in skills.items():
            sd = skills_dir / skill_name
            sd.mkdir()
            auth = opts.get("auth")
            if auth is None:
                fm = f"---\nname: {skill_name}\ndescription: x\n---\nBody.\n"
            else:
                fm = (
                    f"---\nname: {skill_name}\n"
                    f"description: x\n"
                    f"metadata:\n"
                    f"  credentialed: true\n"
                    f"  auth: {auth}\n"
                    f"---\nBody.\n"
                )
            (sd / "SKILL.md").write_text(fm, encoding="utf-8")
            if "scripts" in opts:
                scripts = sd / "scripts"
                scripts.mkdir()
                for basename, text in opts["scripts"].items():
                    (scripts / basename).write_text(text, encoding="utf-8")
    return pack


class _FixtureBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.packs_dir = self.tmp / "packs"
        self.packs_dir.mkdir()


class ProjectionMechanicsTests(_FixtureBase):
    """AC20 / AC25: project into auth: creds skills; skip auth: env skills."""

    def test_projects_into_creds_skills_only(self) -> None:
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={"credentials_shim.py": "shim-body\n"},
        )
        _write_pack(
            self.packs_dir, "consumer",
            skills={
                "secret-skill": {"auth": "creds"},
                "env-skill": {"auth": "env"},
            },
        )
        shared_libs.apply_projection(self.packs_dir)
        creds_scripts = (
            self.packs_dir / "consumer" / ".apm" / "skills"
            / "secret-skill" / "scripts" / "credentials_shim.py"
        )
        env_scripts = (
            self.packs_dir / "consumer" / ".apm" / "skills"
            / "env-skill" / "scripts" / "credentials_shim.py"
        )
        self.assertTrue(creds_scripts.is_file())
        self.assertEqual(creds_scripts.read_text(encoding="utf-8"), "shim-body\n")
        self.assertFalse(env_scripts.exists())

    def test_creates_scripts_dir_if_absent(self) -> None:
        """AC20 trailing: receiving skill without scripts/ — the
        projection creates the directory."""
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={"credentials_shim.py": "x"},
        )
        _write_pack(
            self.packs_dir, "consumer",
            skills={"s": {"auth": "creds"}},
        )
        consumer_scripts = (
            self.packs_dir / "consumer" / ".apm" / "skills" / "s" / "scripts"
        )
        self.assertFalse(consumer_scripts.exists())
        shared_libs.apply_projection(self.packs_dir)
        self.assertTrue(consumer_scripts.is_dir())
        self.assertTrue((consumer_scripts / "credentials_shim.py").is_file())

    def test_projects_multiple_files(self) -> None:
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={
                "credentials_shim.py": "shim",
                "_keychain_macos.py": "kc",
                "_credman_windows.py": "cw",
            },
        )
        _write_pack(
            self.packs_dir, "consumer",
            skills={"s": {"auth": "creds"}},
        )
        shared_libs.apply_projection(self.packs_dir)
        scripts = (
            self.packs_dir / "consumer" / ".apm" / "skills" / "s" / "scripts"
        )
        for name in ("credentials_shim.py", "_keychain_macos.py", "_credman_windows.py"):
            self.assertTrue((scripts / name).is_file(), name)


class InterPackCollisionTests(_FixtureBase):
    """AC21: two packs shipping the same shared-libs basename is a
    hard error at projection time."""

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

    def test_check_drift_surfaces_collision(self) -> None:
        _write_pack(
            self.packs_dir, "broker-a",
            shared_libs_files={"credentials_shim.py": "a"},
        )
        _write_pack(
            self.packs_dir, "broker-b",
            shared_libs_files={"credentials_shim.py": "b"},
        )
        drifts = shared_libs.check_drift(self.packs_dir)
        self.assertEqual(len(drifts), 1)
        self.assertIn("collision", drifts[0])
        self.assertIn("credentials_shim.py", drifts[0])


class DriftGateTests(_FixtureBase):
    """AC23: build-check detects three drift outcomes; build-self resolves."""

    def _setup_baseline(self) -> None:
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={"credentials_shim.py": "source-body\n"},
        )
        _write_pack(
            self.packs_dir, "consumer",
            skills={"s": {"auth": "creds"}},
        )

    def test_clean_tree_no_drift(self) -> None:
        self._setup_baseline()
        shared_libs.apply_projection(self.packs_dir)
        self.assertEqual(shared_libs.check_drift(self.packs_dir), [])

    def test_modified_drift_detected(self) -> None:
        self._setup_baseline()
        shared_libs.apply_projection(self.packs_dir)
        # Tamper with the projected copy.
        target = (
            self.packs_dir / "consumer" / ".apm" / "skills" / "s"
            / "scripts" / "credentials_shim.py"
        )
        target.write_text("tampered-body\n", encoding="utf-8")
        drifts = shared_libs.check_drift(self.packs_dir)
        self.assertEqual(len(drifts), 1)
        self.assertIn("modified", drifts[0])
        self.assertIn("credentials_shim.py", drifts[0])
        self.assertIn("make build-self", drifts[0])

    def test_missing_drift_detected(self) -> None:
        self._setup_baseline()
        # No projection applied yet.
        drifts = shared_libs.check_drift(self.packs_dir)
        self.assertEqual(len(drifts), 1)
        self.assertIn("missing", drifts[0])
        self.assertIn("credentials_shim.py", drifts[0])

    def test_orphan_drift_detected(self) -> None:
        self._setup_baseline()
        shared_libs.apply_projection(self.packs_dir)
        # Strip the consumer's auth: creds declaration so the projected
        # file is now orphaned.
        skill_md = (
            self.packs_dir / "consumer" / ".apm" / "skills" / "s" / "SKILL.md"
        )
        skill_md.write_text(
            "---\nname: s\ndescription: x\n---\nBody.\n",
            encoding="utf-8",
        )
        drifts = shared_libs.check_drift(self.packs_dir)
        self.assertEqual(len(drifts), 1)
        self.assertIn("orphan", drifts[0])
        self.assertIn("credentials_shim.py", drifts[0])

    def test_build_self_resolves_drift(self) -> None:
        """After any drift outcome, apply_projection produces a clean tree."""
        self._setup_baseline()
        # Mix of outcomes — modified-and-missing across two files.
        _write_pack(
            self.packs_dir, "broker-2",
            shared_libs_files={},  # extend broker tree below
        )
        # broker already has credentials_shim.py; add a second helper.
        (self.packs_dir / "broker" / ".apm" / "shared-libs" / "_helper.py").write_text(
            "helper-source", encoding="utf-8",
        )
        shutil.rmtree(self.packs_dir / "broker-2")  # cleanup the unused pack
        # Pre-state: modified + missing across the two basenames.
        scripts = (
            self.packs_dir / "consumer" / ".apm" / "skills" / "s" / "scripts"
        )
        scripts.mkdir()
        (scripts / "credentials_shim.py").write_text("stale", encoding="utf-8")
        # _helper.py is missing entirely.
        pre_drift = shared_libs.check_drift(self.packs_dir)
        self.assertGreaterEqual(len(pre_drift), 2)
        shared_libs.apply_projection(self.packs_dir)
        self.assertEqual(shared_libs.check_drift(self.packs_dir), [])


class OrphanRemovalTests(_FixtureBase):
    """AC23 build-self resolves orphan drift by removing the file."""

    def test_apply_projection_removes_orphan(self) -> None:
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={"credentials_shim.py": "src\n"},
        )
        _write_pack(
            self.packs_dir, "consumer",
            skills={"s": {"auth": "creds"}},
        )
        shared_libs.apply_projection(self.packs_dir)
        target = (
            self.packs_dir / "consumer" / ".apm" / "skills" / "s"
            / "scripts" / "credentials_shim.py"
        )
        self.assertTrue(target.is_file())
        # Strip the consumer's auth: creds declaration.
        skill_md = target.parent.parent / "SKILL.md"
        skill_md.write_text(
            "---\nname: s\ndescription: x\n---\nBody.\n",
            encoding="utf-8",
        )
        shared_libs.apply_projection(self.packs_dir)
        self.assertFalse(
            target.exists(),
            "apply_projection should remove orphans after auth: creds is stripped",
        )
        self.assertEqual(shared_libs.check_drift(self.packs_dir), [])

    def test_orphan_surfaces_when_sources_dropped(self) -> None:
        """If a future PR drops the shared-libs source pack entirely,
        stale projected copies under consumer skills must still surface
        as drift (not silent)."""
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={"credentials_shim.py": "src\n"},
        )
        _write_pack(
            self.packs_dir, "consumer",
            skills={"s": {"auth": "creds"}},
        )
        shared_libs.apply_projection(self.packs_dir)
        # Drop the broker's shared-libs source entirely.
        import shutil as _sh
        _sh.rmtree(self.packs_dir / "broker" / ".apm" / "shared-libs")
        drifts = shared_libs.check_drift(self.packs_dir)
        self.assertTrue(
            any("orphan" in d for d in drifts),
            f"orphan rail silent when sources dropped; got {drifts!r}",
        )


class IdempotenceTests(_FixtureBase):
    """apply_projection is idempotent: running twice produces identical
    filesystem state."""

    def test_apply_projection_byte_identical_on_second_run(self) -> None:
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={
                "credentials_shim.py": "shim-source\n",
                "_keychain_macos.py": "kc-source\n",
                "_credman_windows.py": "cw-source\n",
            },
        )
        _write_pack(
            self.packs_dir, "consumer",
            skills={
                "s1": {"auth": "creds"},
                "s2": {"auth": "creds"},
            },
        )
        shared_libs.apply_projection(self.packs_dir)
        # Capture every projected file's bytes after the first run.
        first_pass: dict[Path, bytes] = {}
        for proj in shared_libs.compute_projections(self.packs_dir):
            first_pass[proj.target] = proj.target.read_bytes()
        # Re-run; assert byte-identical output.
        shared_libs.apply_projection(self.packs_dir)
        for target, expected_bytes in first_pass.items():
            self.assertTrue(target.is_file(), f"target lost on second run: {target}")
            self.assertEqual(
                target.read_bytes(), expected_bytes,
                f"apply_projection produced different bytes on second run for {target}",
            )
        # Drift gate stays clean.
        self.assertEqual(shared_libs.check_drift(self.packs_dir), [])


class EmptyTreeTests(_FixtureBase):
    """No source pack carrying shared-libs → no projection, no drift."""

    def test_no_sources_no_drift(self) -> None:
        _write_pack(
            self.packs_dir, "consumer",
            skills={"s": {"auth": "creds"}},
        )
        self.assertEqual(shared_libs.check_drift(self.packs_dir), [])
        shared_libs.apply_projection(self.packs_dir)  # no-op
        scripts = (
            self.packs_dir / "consumer" / ".apm" / "skills" / "s" / "scripts"
        )
        # No scripts dir created, no files written.
        self.assertFalse(scripts.exists())


class AuthDetectionTests(_FixtureBase):
    """Frontmatter regex correctly admits / refuses the auth value."""

    def test_auth_creds_with_comment(self) -> None:
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={"credentials_shim.py": "x"},
        )
        pack = _write_pack(
            self.packs_dir, "consumer",
            skills={"s": {"auth": "creds"}},
        )
        # Inject a trailing comment after auth: creds.
        skill_md = pack / ".apm" / "skills" / "s" / "SKILL.md"
        text = skill_md.read_text(encoding="utf-8")
        skill_md.write_text(
            text.replace("auth: creds", "auth: creds  # broker shape"),
            encoding="utf-8",
        )
        consumers = shared_libs.find_creds_consumers(self.packs_dir)
        self.assertEqual(len(consumers), 1)

    def test_body_only_match_does_not_count(self) -> None:
        """A body mention (not frontmatter) does not declare auth."""
        _write_pack(
            self.packs_dir, "broker",
            shared_libs_files={"credentials_shim.py": "x"},
        )
        skill_dir = self.packs_dir / "p" / ".apm" / "skills" / "s"
        skill_dir.mkdir(parents=True)
        (self.packs_dir / "p" / "pack.toml").write_text(
            '[pack]\nname = "p"\nversion = "0.1.0"\n',
            encoding="utf-8",
        )
        (skill_dir / "SKILL.md").write_text(
            "---\nname: s\ndescription: x\n---\n"
            "The skill body mentions `  auth: creds` in prose.\n",
            encoding="utf-8",
        )
        consumers = shared_libs.find_creds_consumers(self.packs_dir)
        self.assertEqual(consumers, [])


if __name__ == "__main__":
    unittest.main()
