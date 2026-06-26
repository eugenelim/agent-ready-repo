"""T7 (RFC-0052): end-to-end coexistence flows + concurrent-install race.

Installs the real shipped `core` pack for sibling adapters at repo scope and
asserts the footprint model's coexistence guarantees:

  - `.agents/skills/` cohort: codex then cursor → the shared skill is co-owned
    (not rewritten, not swept); cursor's private `.cursor/` primitives land.
  - kiro family: kiro-cli then kiro-ide → `.kiro/skills/` co-owned, `.json`
    (cli) + `.md` (ide) agents coexist; uninstall kiro-cli → `.json` removed,
    shared skills remain (RFC-0052 falsifier).
  - concurrency: two simultaneous installs of different adapter rows of one
    pack to the same state file — both rows land (the T0 lock prevents the
    lost-update that a naive read-modify-write would suffer).
"""

from __future__ import annotations

import io
import threading
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[4]


def _run(verb: str, argv: list[str]) -> tuple[int, str, str]:
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install, uninstall

    parser = _build_parser()
    args = parser.parse_args([verb] + argv)
    out_buf, err_buf = io.StringIO(), io.StringIO()
    with redirect_stdout(out_buf), redirect_stderr(err_buf):
        rc = (install if verb == "install" else uninstall).run(args)
    return rc, out_buf.getvalue(), err_buf.getvalue()


def _install(adopter: Path, adapter: str) -> tuple[int, str, str]:
    return _run(
        "install",
        ["--pack", "core", "--adapter", adapter, "--scope", "repo",
         "--yes", "--output", str(adopter), str(REPO_ROOT)],
    )


def _state(adopter: Path) -> dict:
    return tomllib.loads(
        (adopter / ".agentbundle-state.toml").read_text(encoding="utf-8")
    )


def _sha(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


class AgentsSkillsCohortCoexistenceTests(unittest.TestCase):
    def test_codex_then_cursor_co_own_shared_skill(self) -> None:
        from agentbundle.commands import install as _i

        _i._clear_inband_detection_seen()
        with TemporaryDirectory() as raw:
            adopter = Path(raw)
            rc, _, _ = _install(adopter, "codex")
            self.assertEqual(rc, 0)
            skill = next((adopter / ".agents" / "skills").glob("*/SKILL.md"))
            sha_before = _sha(skill)

            rc, _, err = _install(adopter, "cursor")
            self.assertEqual(rc, 0, err)

            # The shared skill survived, byte-unchanged (co-owned, not rewritten).
            self.assertTrue(skill.exists())
            self.assertEqual(_sha(skill), sha_before)
            # cursor's private primitives landed under .cursor/.
            self.assertTrue((adopter / ".cursor").is_dir())
            # Both adapter rows coexist, and both claim the shared skill.
            rows = _state(adopter)["pack"]["core"]["adapters"]
            self.assertEqual(sorted(rows), ["codex", "cursor"])
            skill_rel = skill.relative_to(adopter).as_posix()
            self.assertIn(skill_rel, rows["codex"]["files"])
            self.assertIn(skill_rel, rows["cursor"]["files"])


class KiroFamilyCoexistenceTests(unittest.TestCase):
    def test_kiro_cli_then_ide_then_uninstall_cli(self) -> None:
        from agentbundle.commands import install as _i

        _i._clear_inband_detection_seen()
        with TemporaryDirectory() as raw:
            adopter = Path(raw)
            rc, _, err = _install(adopter, "kiro-cli")
            self.assertEqual(rc, 0, err)
            skill = next((adopter / ".kiro" / "skills").glob("*/SKILL.md"))
            sha_before = _sha(skill)
            json_agents = list((adopter / ".kiro" / "agents").glob("*.json"))
            self.assertTrue(json_agents, "kiro-cli should write .json agents")

            rc, _, err = _install(adopter, "kiro-ide")
            self.assertEqual(rc, 0, err)
            # Shared skills co-owned (unchanged); .md agents now also present.
            self.assertEqual(_sha(skill), sha_before)
            md_agents = list((adopter / ".kiro" / "agents").glob("*.md"))
            self.assertTrue(md_agents, "kiro-ide should write .md agents")
            self.assertTrue(all(j.exists() for j in json_agents),
                            "kiro-cli .json agents must survive the kiro-ide install")

            # Uninstall kiro-cli → its .json agents go; shared skills remain
            # (kiro-ide still owns them). RFC-0052 falsifier.
            rc, _, err = _run(
                "uninstall",
                ["--pack", "core", "--adapter", "kiro-cli", "--scope", "repo",
                 "--yes", "--root", str(adopter)],
            )
            self.assertEqual(rc, 0, err)
            self.assertFalse(any(j.exists() for j in json_agents),
                             "kiro-cli .json agents should be removed")
            self.assertTrue(skill.exists(),
                            "shared skill must survive — kiro-ide still owns it")
            rows = _state(adopter)["pack"]["core"]["adapters"]
            self.assertEqual(sorted(rows), ["kiro-ide"])


class ConcurrentInstallTests(unittest.TestCase):
    def test_two_adapter_installs_race_both_rows_land(self) -> None:
        from agentbundle.commands import install as _i

        _i._clear_inband_detection_seen()
        with TemporaryDirectory() as raw:
            adopter = Path(raw)
            results: dict[str, int] = {}
            barrier = threading.Barrier(2)

            def worker(adapter: str) -> None:
                barrier.wait()
                rc, _, _ = _install(adopter, adapter)
                results[adapter] = rc

            threads = [
                threading.Thread(target=worker, args=(a,))
                for a in ("codex", "cursor")
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            self.assertEqual(results, {"codex": 0, "cursor": 0})
            # Both rows survived the race — neither overwrote the other (the
            # T0 lock + read-merge-write prevents the lost update).
            rows = _state(adopter)["pack"]["core"]["adapters"]
            self.assertEqual(sorted(rows), ["codex", "cursor"])


if __name__ == "__main__":
    unittest.main()
