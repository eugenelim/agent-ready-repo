"""RFC-0012 AC24: in-band detection of pre-RFC-0012 state at install start.

Three triggers evaluated per-pack in precedence ``(b) → (a) → (c)``; only the
first match emits. Detection runs once per ``(repo, pack)`` per session and
short-circuits to silence on subsequent calls.

  - **(b) Shape-mismatch.** ``state.toml`` has a row for the pack AND
    dist-tree files exist at ``<repo>/claude-plugins/<pack>/`` or
    ``<repo>/apm/<pack>/``. Pinned stderr names the dist-tree paths to
    remove. ``--force`` cleans dist-tree and proceeds (AC25(vi)).

  - **(a) Adapter disagreement.** ``state.toml`` has a row for the pack
    with a recorded ``adapter`` AND resolver's pick disagrees AND no
    dist-tree files. Pinned stderr names recorded vs. resolved adapter.
    ``--force`` does NOT clear this trigger; uninstall + reinstall is
    the corrective action.

  - **(c) Orphan recovery.** No state row but per-IDE artifacts exist
    under the resolved adapter's ``allowed-prefixes.repo``. The AC22
    refusal path (already covered in :mod:`test_install_messages_repo_scope`)
    extended here to pin precedence-chain semantics and once-per-session
    short-circuit.

Detection runs only on the per-IDE install code path —
``--scope repo`` without ``--emit-install-routes`` (spec AC24
narrowed-inference rule). ``--emit-install-routes`` short-circuits
before detection.
"""

from __future__ import annotations

import io
import textwrap
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory


def _make_pack(
    packs_dir: Path,
    *,
    name: str = "demo",
    allowed_adapters: list[str] | None = None,
) -> Path:
    """A minimal v0.7 repo-scope pack the resolver can dispatch."""
    pack_dir = packs_dir / name
    pack_dir.mkdir(parents=True)
    aa_line = ""
    if allowed_adapters is not None:
        aa_line = f"allowed-adapters = {allowed_adapters!r}\n"
    (pack_dir / "pack.toml").write_text(
        textwrap.dedent(
            f"""\
            [pack]
            name = "{name}"
            version = "0.1.0"
            spec-version = "0.6"

            [pack.adapter-contract]
            version = "0.7"

            [pack.install]
            default-scope = "repo"
            allowed-scopes = ["repo"]
            {aa_line}"""
        ),
        encoding="utf-8",
    )
    skill_dir = pack_dir / ".apm" / "skills" / f"{name}-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}-skill\ndescription: {name}\n---\nBody.",
        encoding="utf-8",
    )
    return pack_dir


def _plant_state(adopter: Path, *, pack_name: str, adapter: str = "claude-code") -> None:
    """Write a minimal v0.3 state.toml carrying a single ``[pack.<name>]`` row.

    The fixture mirrors a pre-RFC-0012 install — the row exists but no
    repo-scope per-IDE files match it on disk (dist-tree or orphan
    artifacts are planted by the caller).
    """
    adapter_line = ""
    if adapter != "claude-code":
        adapter_line = f'adapter = "{adapter}"\n'
    state_path = adopter / ".agentbundle-state.toml"
    state_path.write_text(
        textwrap.dedent(
            f"""\
            schema-version = "0.3"

            [pack.{pack_name}]
            installed-version = "0.1.0"
            source = "agent-ready-repo"
            install-route = "cli"
            scope = "repo"
            {adapter_line}"""
        ),
        encoding="utf-8",
    )


def _run_install(argv: list[str]) -> tuple[int, str]:
    """Invoke install via the argparse layer; return ``(rc, stderr)``."""
    from agentbundle.cli import _build_parser
    from agentbundle.commands import install

    parser = _build_parser()
    args = parser.parse_args(["install"] + argv)
    buf = io.StringIO()
    with redirect_stderr(buf):
        rc = install.run(args)
    return rc, buf.getvalue()


def _clear_session_set() -> None:
    """Reset the once-per-session detection set between tests."""
    from agentbundle.commands import install

    install._clear_inband_detection_seen()


class TriggerBShapeMismatchTests(unittest.TestCase):
    """(b) shape-mismatch: state row + dist-tree files on disk."""

    def setUp(self) -> None:
        _clear_session_set()

    def test_b_fires_when_state_row_and_dist_tree_present(self) -> None:
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, allowed_adapters=["claude-code", "kiro"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            _plant_state(adopter, pack_name="demo")
            # Plant dist-tree files (pre-RFC-0012 shape).
            (adopter / "claude-plugins" / "demo").mkdir(parents=True)
            (adopter / "claude-plugins" / "demo" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )
            (adopter / "apm" / "demo").mkdir(parents=True)
            (adopter / "apm" / "demo" / "pack.toml").write_text(
                "", encoding="utf-8"
            )

            rc, stderr = _run_install(
                ["--pack", "demo", "--scope", "repo",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertNotEqual(rc, 0)
            self.assertIn("pre-RFC-0012 dist-tree files for pack demo", stderr)
            # Platform-portable: assert path segments separately so the
            # Windows path-separator (``\\``) doesn't break substring
            # matching on the joined ``claude-plugins/demo`` literal.
            self.assertIn("claude-plugins", stderr)
            self.assertIn("apm", stderr)
            self.assertIn("demo", stderr)
            self.assertIn("rerun with --force", stderr)

    def test_b_force_cleans_dist_tree_and_proceeds(self) -> None:
        """AC25(vi): ``--force`` is the corrective action for (b). It
        must (1) delete the dist-tree subtrees, (2) drop the stale
        state row so Step 4 doesn't re-refuse with "use 'upgrade'",
        and (3) let the install complete cleanly with the per-IDE
        projection landing in place of the dist-tree shape."""
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, allowed_adapters=["claude-code", "kiro"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            _plant_state(adopter, pack_name="demo")
            (adopter / "claude-plugins" / "demo").mkdir(parents=True)
            (adopter / "claude-plugins" / "demo" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )

            rc, stderr = _run_install(
                ["--pack", "demo", "--scope", "repo", "--force",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertEqual(
                rc, 0,
                f"install did not complete after --force; stderr={stderr!r}",
            )
            self.assertNotIn("pre-RFC-0012 dist-tree files", stderr)
            # Dist-tree subtree gone.
            self.assertFalse(
                (adopter / "claude-plugins" / "demo").exists(),
                "expected claude-plugins/demo/ subtree to be removed by --force",
            )
            # Per-IDE projection landed in its place.
            self.assertTrue(
                (adopter / ".claude" / "skills").exists(),
                "expected per-IDE projection at .claude/skills/ after reinstall",
            )
            # State.toml carries a fresh row pointing at the per-IDE
            # paths (not the dist-tree paths). A regression that left
            # the stale row's ``files`` map intact would surface here.
            import tomllib

            state = tomllib.loads(
                (adopter / ".agentbundle-state.toml").read_text(encoding="utf-8")
            )
            pack_row = state.get("pack", {}).get("demo", {})
            self.assertEqual(
                pack_row.get("installed-version"), "0.1.0",
                f"state row not refreshed after (b)+--force: {pack_row!r}",
            )
            files_recorded = list((pack_row.get("files") or {}).keys())
            self.assertTrue(
                any(p.startswith(".claude/") for p in files_recorded),
                f"state.files missing per-IDE entries: {files_recorded!r}",
            )
            self.assertFalse(
                any(
                    p.startswith("claude-plugins/") or p.startswith("apm/")
                    for p in files_recorded
                ),
                f"state.files still tracks dist-tree paths: {files_recorded!r}",
            )


class TriggerAAdapterDisagreementTests(unittest.TestCase):
    """(a) adapter disagreement: state row + resolver disagreement +
    no dist-tree files (precedence (b) → (a))."""

    def setUp(self) -> None:
        _clear_session_set()

    def test_a_fires_when_recorded_adapter_disagrees_with_resolver(self) -> None:
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, allowed_adapters=["claude-code", "kiro"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            # State records claude-code; resolver picks kiro via --adapter.
            _plant_state(adopter, pack_name="demo", adapter="claude-code")
            # NO dist-tree files — (b) must not fire.

            rc, stderr = _run_install(
                ["--pack", "demo", "--scope", "repo", "--adapter", "kiro",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertNotEqual(rc, 0)
            self.assertIn(
                "state records adapter 'claude-code' for pack demo", stderr
            )
            self.assertIn("resolver picked 'kiro'", stderr)
            self.assertIn("uninstall", stderr)

    def test_a_does_not_fire_when_dist_tree_present_b_takes_precedence(self) -> None:
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, allowed_adapters=["claude-code", "kiro"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            _plant_state(adopter, pack_name="demo", adapter="claude-code")
            # Plant dist-tree files: (b) fires before (a).
            (adopter / "claude-plugins" / "demo").mkdir(parents=True)
            (adopter / "claude-plugins" / "demo" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )

            rc, stderr = _run_install(
                ["--pack", "demo", "--scope", "repo", "--adapter", "kiro",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertNotEqual(rc, 0)
            # (b) fired, not (a).
            self.assertIn("pre-RFC-0012 dist-tree files", stderr)
            self.assertNotIn("state records adapter", stderr)

    def test_a_not_cleared_by_force(self) -> None:
        """--force is NOT the corrective action for (a); uninstall + reinstall
        is. The refusal text must still appear with --force passed."""
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, allowed_adapters=["claude-code", "kiro"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            _plant_state(adopter, pack_name="demo", adapter="claude-code")

            rc, stderr = _run_install(
                ["--pack", "demo", "--scope", "repo", "--adapter", "kiro",
                 "--force",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertNotEqual(rc, 0)
            self.assertIn("state records adapter 'claude-code'", stderr)


class PrecedenceAndSessionShortCircuitTests(unittest.TestCase):
    """Per-pack precedence and the once-per-session short-circuit."""

    def setUp(self) -> None:
        _clear_session_set()

    def test_per_pack_evaluation_b_for_a_then_c_for_b(self) -> None:
        """Spec AC24 (b)+(c) overlap fixture. Two packs share the adopter:
        pack A has a state row + dist-tree files (fires (b)); pack B has
        orphan per-IDE files but no state row (fires (c)).

        The detection key is ``(root, pack_name)``, so each pack lands
        on its own trigger. As of the per-pack-scoping amendment (2026-
        05-26) ``safety.scan_for_pack_artifacts`` filters to pack-owned
        primitive names when ``pack_dir`` + ``pack_name`` are threaded
        through, so (c) only fires when pack B's *own* primitives are
        on disk — see ``test_cross_pack_orphan_does_not_trigger_c``
        below for the negative case."""
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, name="apack", allowed_adapters=["claude-code"])
            _make_pack(packs_dir, name="bpack", allowed_adapters=["claude-code"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            # Pack A: state row + dist-tree files → (b) should fire.
            _plant_state(adopter, pack_name="apack")
            (adopter / "claude-plugins" / "apack").mkdir(parents=True)
            (adopter / "claude-plugins" / "apack" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )
            # Pack B: no state row but a GENUINE non-projection orphan under
            # its skill dir → (c) should fire when installing B. Issue #190 —
            # a file that *is* a projection path (SKILL.md) is now companion-
            # protected; `STALE.md` matches the `bpack-skill` segment but is
            # not a projected relpath, so it stays an orphan.
            orphan = adopter / ".claude" / "skills" / "bpack-skill" / "STALE.md"
            orphan.parent.mkdir(parents=True)
            orphan.write_text("stale", encoding="utf-8")

            # Install pack A first — (b) fires.
            rc_a, stderr_a = _run_install(
                ["--pack", "apack", "--scope", "repo",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertNotEqual(rc_a, 0)
            self.assertIn("pre-RFC-0012 dist-tree files for pack apack", stderr_a)

            # Install pack B in the same session — (c) fires.
            rc_b, stderr_b = _run_install(
                ["--pack", "bpack", "--scope", "repo",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertNotEqual(rc_b, 0)
            self.assertIn(
                "unrecognized files at projection paths not shipped by pack bpack",
                stderr_b,
            )

    def test_cross_pack_orphan_does_not_trigger_c(self) -> None:
        """**Regression pin for the per-pack-scoping amendment.**

        Pack A's orphan files under ``.claude/skills/apack-skill/``
        must NOT trigger (c) when installing pack B (which has no state
        row, no on-disk files of its own). Before per-pack scoping
        landed, the AC24(c) trigger surfaced pack A's paths with pack
        B's name in the stderr line — the cross-pack false positive
        ROADMAP named as the only open RFC-0012 follow-on.

        Post-fix, the scan walks pack B's source for owned primitive
        names (``bpack``, ``bpack-skill``), finds no match against
        pack A's orphan path, and returns an empty list. (c) does not
        fire; the install completes cleanly.
        """
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, name="apack", allowed_adapters=["claude-code"])
            _make_pack(packs_dir, name="bpack", allowed_adapters=["claude-code"])
            adopter = tmp / "adopter"
            adopter.mkdir()

            # Plant pack A's orphan under the shared adapter prefix.
            # No state row for A (or B); pack B is greenfield.
            a_orphan = (
                adopter / ".claude" / "skills" / "apack-skill" / "SKILL.md"
            )
            a_orphan.parent.mkdir(parents=True)
            a_orphan.write_text("stale apack content", encoding="utf-8")

            # Install pack B. (c) must NOT fire on pack A's leftovers.
            rc, stderr = _run_install(
                ["--pack", "bpack", "--scope", "repo",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertEqual(
                rc, 0,
                f"install refused despite cross-pack scan; stderr={stderr!r}",
            )
            self.assertNotIn(
                "orphan projection files for pack bpack", stderr,
                "(c) fired for pack B with pack A's orphan present — "
                "cross-pack false positive not fixed",
            )
            # Pack A's orphan is untouched (the install didn't sweep it).
            self.assertTrue(
                a_orphan.exists(),
                "install should not have deleted pack A's orphan",
            )

    def test_short_circuit_on_repeat_invocation_same_pack(self) -> None:
        """Re-invoking install for the same ``(root, pack)`` within the
        same Python process does NOT re-emit the detection line."""
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, allowed_adapters=["claude-code", "kiro"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            _plant_state(adopter, pack_name="demo")
            (adopter / "claude-plugins" / "demo").mkdir(parents=True)
            (adopter / "claude-plugins" / "demo" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )

            rc1, stderr1 = _run_install(
                ["--pack", "demo", "--scope", "repo",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertIn("pre-RFC-0012 dist-tree files", stderr1)

            # Second call within the same process — detection short-circuits.
            rc2, stderr2 = _run_install(
                ["--pack", "demo", "--scope", "repo",
                 "--output", str(adopter), str(packs_dir)]
            )
            self.assertNotIn("pre-RFC-0012 dist-tree files", stderr2)


class EmitInstallRoutesBypassesDetectionTests(unittest.TestCase):
    """Spec AC24 narrowed-inference rule: detection runs only on the
    per-IDE install code path (``--scope repo`` without
    ``--emit-install-routes``). The dist-tree producer must NOT trigger
    (b) on its own legitimate output."""

    def setUp(self) -> None:
        _clear_session_set()

    def test_emit_install_routes_does_not_trigger_b(self) -> None:
        with TemporaryDirectory() as raw:
            tmp = Path(raw)
            packs_dir = tmp / "packs"
            packs_dir.mkdir()
            _make_pack(packs_dir, allowed_adapters=["claude-code", "kiro"])
            adopter = tmp / "adopter"
            adopter.mkdir()
            _plant_state(adopter, pack_name="demo")
            (adopter / "claude-plugins" / "demo").mkdir(parents=True)
            (adopter / "claude-plugins" / "demo" / "plugin.json").write_text(
                "{}", encoding="utf-8"
            )

            rc, stderr = _run_install(
                ["--pack", "demo", "--scope", "repo",
                 "--emit-install-routes",
                 "--output", str(adopter), str(packs_dir)]
            )
            # The detection block is bypassed; the already-installed
            # refusal at install.py:314 fires instead.
            self.assertNotIn("pre-RFC-0012 dist-tree files", stderr)


if __name__ == "__main__":
    unittest.main()
