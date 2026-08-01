#!/usr/bin/env python3
"""CLI contract tests for scripts/workspace_status.py — Order 1A.

Tests the installed production CLI, not a copy of the engine.
The CLI lives at:
  packs/core/.apm/skills/workspace-status/scripts/workspace_status.py

All invocations use sys.executable and list-form subprocess calls.
Never shell=True. Tests are independent of the source checkout CWD.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# ── Locate the CLI ────────────────────────────────────────────────────────────


def _repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "workspace.toml").exists() and (p / "packs").is_dir():
            return p
    raise RuntimeError("cannot locate repo root")


_REPO_ROOT = _repo_root()
_CLI = (
    _REPO_ROOT
    / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
)
_ENGINE = (
    _REPO_ROOT
    / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
)


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_CLI), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
    )


# ── Fixtures ──────────────────────────────────────────────────────────────────

_MINIMAL_TOML = """\
["ini-001"]
name      = "Test"
status    = "active"
milestone = "M1"

["ini-001".work]
active  = []
shipped = []
queue   = ["spec/alpha"]

["ini-001".shaping_queue]
active  = []
backlog = []
"""

_RICH_TOML = """\
["ini-001"]
name      = "Active Initiative"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/alpha", {path = "spec/beta", needs = "work:spec/alpha"}]
active  = ["spec/gamma"]
shipped = ["spec/delta"]

["ini-001".shaping_queue]
active  = [{slug = "topic-x", type = "shape"}]
backlog = []

["ini-001".brief_queue]
executing = "briefs/brief-a"
ready     = ["briefs/brief-b"]
draft     = []

["ini-002"]
name      = "Paused Initiative"
status    = "paused"
milestone = "M2"

["ini-002".work]
queue   = []
active  = []
shipped = []

["ini-002".shaping_queue]
active  = []
backlog = []
"""

_MALFORMED_TOML = "this is not valid toml {{{ ]]"


class _CliBase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def _write_workspace(self, content: str) -> Path:
        p = self.tmp / "workspace.toml"
        p.write_text(content, encoding="utf-8")
        return self.tmp

    def _make_spec(self, root: Path, slug: str, status: str = "Approved") -> None:
        d = root / "docs" / "specs" / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "spec.md").write_text(
            f"# Spec: {slug}\n\n- **Status:** {status}\n",
            encoding="utf-8",
        )


# ── Test: CLI file presence ───────────────────────────────────────────────────

class CLIPresenceTests(unittest.TestCase):
    def test_cli_script_exists(self) -> None:
        self.assertTrue(_CLI.exists(), f"CLI not found: {_CLI}")

    def test_engine_script_exists(self) -> None:
        self.assertTrue(_ENGINE.exists(), f"Engine not found: {_ENGINE}")

    def test_engine_not_in_tools(self) -> None:
        stale = _REPO_ROOT / "tools" / "workspace_status_engine.py"
        self.assertFalse(
            stale.exists(),
            f"Old engine copy still exists: {stale} — should have been moved",
        )

    def test_engine_module_importable(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("workspace_status_engine", _ENGINE)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        sys.modules.setdefault("workspace_status_engine", mod)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        self.assertTrue(callable(mod.analyze))
        self.assertTrue(callable(mod.compute_type2_cleanup))


# ── Test: CLI stdlib-only imports ─────────────────────────────────────────────

class CLIImportPurityTests(unittest.TestCase):
    """AC12/AC13: runtime scripts must be stdlib-only, no cross-skill imports."""

    _STDLIB_MODULES = frozenset({
        "argparse", "dataclasses", "importlib", "json", "os", "pathlib",
        "re", "sys", "tempfile", "time", "tomllib", "typing", "unittest",
        "__future__", "collections", "functools", "itertools", "abc",
        "contextlib", "io", "shutil", "traceback",
    })

    def _check_script(self, path: Path) -> None:
        import ast
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        forbidden: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in self._STDLIB_MODULES:
                        forbidden.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import — allowed (script-relative)
                mod = node.module or ""
                top = mod.split(".")[0]
                if top and top not in self._STDLIB_MODULES:
                    forbidden.append(mod)
        self.assertEqual(
            forbidden, [],
            f"{path.name} has non-stdlib imports: {forbidden}",
        )

    def test_cli_stdlib_only(self) -> None:
        if _CLI.exists():
            self._check_script(_CLI)
        else:
            self.skipTest("CLI not yet created")

    def test_engine_stdlib_only(self) -> None:
        if _ENGINE.exists():
            self._check_script(_ENGINE)
        else:
            self.skipTest("Engine not yet moved")

    def test_no_tools_packs_sibling_imports(self) -> None:
        """No import of tools/, packs/, or sibling skill paths."""
        for script in (_CLI, _ENGINE):
            if not script.exists():
                continue
            text = script.read_text(encoding="utf-8")
            for forbidden in ("tools.", "packs.", "shared-libs", "shared_libs"):
                self.assertNotIn(
                    forbidden, text,
                    f"{script.name} imports from forbidden path ({forbidden!r})",
                )


# ── Test: CLI contract ────────────────────────────────────────────────────────

class CLIContractTests(_CliBase):

    def test_cli_success(self) -> None:
        """AC5: exit 0, valid JSON, schema_version == 1."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MINIMAL_TOML)
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        data = json.loads(r.stdout)
        self.assertEqual(data.get("schema_version"), 1)
        self.assertIn("work", data)
        self.assertIn("shaping", data)
        self.assertIn("reconciliation", data)

    def test_cli_workspace_present_field(self) -> None:
        """AC5: workspace_present is True when workspace.toml exists."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MINIMAL_TOML)
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data.get("workspace_present"))

    def test_cli_deterministic(self) -> None:
        """AC5: two unchanged runs produce byte-identical output."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MINIMAL_TOML)
        r1 = _run_cli("--root", str(root))
        r2 = _run_cli("--root", str(root))
        self.assertEqual(r1.returncode, 0)
        self.assertEqual(r1.stdout, r2.stdout)

    def test_cli_workspace_absent(self) -> None:
        """AC5/AC8: exit 1 with workspace_present == false and schema_version == 1 when absent."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        empty = self.tmp / "empty"
        empty.mkdir()
        r = _run_cli("--root", str(empty))
        self.assertEqual(r.returncode, 1)
        data = json.loads(r.stdout)
        self.assertFalse(data.get("workspace_present"))
        self.assertEqual(data.get("schema_version"), 1)

    def test_cli_malformed_toml(self) -> None:
        """AC20: exit 2, no traceback on stdout, for malformed TOML."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MALFORMED_TOML)
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stdout)
        # stdout should be empty or valid JSON, never a raw traceback
        if r.stdout.strip():
            try:
                json.loads(r.stdout)
            except json.JSONDecodeError:
                self.fail(f"stdout is neither empty nor valid JSON: {r.stdout[:200]!r}")

    def test_cli_generic_exception(self) -> None:
        """AC20: exit 2, no traceback/absolute paths on stdout for generic errors.

        Uses workspace.toml-as-directory trick (raises IsADirectoryError) — works
        regardless of UID (no reliance on chmod/permission bits).
        """
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self.tmp / "dirtoml"
        root.mkdir()
        # Create workspace.toml as a DIRECTORY — open() raises IsADirectoryError
        (root / "workspace.toml").mkdir()
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stdout)
        # No absolute paths should appear on stdout
        self.assertNotIn(str(root), r.stdout)

    def test_cli_no_writes(self) -> None:
        """AC8: CLI does not write any files (membership + mtime snapshot)."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MINIMAL_TOML)
        scripts_dir = _CLI.parent

        def _snapshot(d: Path) -> set[Path]:
            return {p for p in d.rglob("*") if p.is_file()}

        fixture_before = _snapshot(root)
        scripts_before = _snapshot(scripts_dir)
        _run_cli("--root", str(root))
        fixture_after = _snapshot(root)
        scripts_after = _snapshot(scripts_dir)
        new_in_fixture = fixture_after - fixture_before
        new_in_scripts = scripts_after - scripts_before
        self.assertFalse(new_in_fixture, f"CLI created files in fixture: {new_in_fixture}")
        self.assertFalse(
            new_in_scripts,
            f"CLI created files in skill scripts/ (bytecode leak?): {new_in_scripts}",
        )

    def test_cli_non_repo_cwd(self) -> None:
        """AC11: CLI succeeds when invoked from an unrelated cwd."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MINIMAL_TOML)
        external_cwd = tempfile.gettempdir()
        r = _run_cli("--root", str(root), cwd=external_cwd)
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")

    def test_cli_unicode(self) -> None:
        """AC11: CLI handles Unicode paths and content."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        uni_dir = self.tmp / "ünïcödé"
        uni_dir.mkdir()
        (uni_dir / "workspace.toml").write_text(
            _MINIMAL_TOML + '\n# Üñïcödé comment\n',
            encoding="utf-8",
        )
        r = _run_cli("--root", str(uni_dir))
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        data = json.loads(r.stdout)
        self.assertEqual(data.get("schema_version"), 1)

    def test_cli_missing_root_arg(self) -> None:
        """Exit 2 with clean stdout when --root is omitted (argparse required-arg path)."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        r = _run_cli()  # no --root
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout.strip(), "", f"stdout should be empty: {r.stdout[:200]!r}")

    def test_cli_rich_fixture_shapes(self) -> None:
        """AC5: assert serialized shapes for initiatives, brief_queue, work.blocked,
        work.active, work.shipped, and shaping entries using a rich fixture."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_RICH_TOML)
        # Spec files for active/shipped entries so Type 2/3 scans don't error.
        self._make_spec(root, "gamma", status="Implementing")
        self._make_spec(root, "delta", status="Shipped")
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        data = json.loads(r.stdout)

        # initiatives[] — only the active initiative appears (ini-002 is paused)
        inis = data.get("initiatives", [])
        self.assertEqual(len(inis), 1, f"expected 1 active initiative, got {inis}")
        ini = inis[0]
        self.assertEqual(ini["slug"], "ini-001")
        self.assertEqual(ini["name"], "Active Initiative")
        self.assertEqual(ini["status"], "active")
        self.assertEqual(ini["milestone"], "M1")
        # queue_empty: ini-001 has spec/alpha and spec/beta in queue → not empty
        self.assertIn("queue_empty", ini, "queue_empty field must be present in initiative dict")
        self.assertFalse(ini["queue_empty"], "ini-001 queue is non-empty")

        # brief_queue shape
        bq = ini.get("brief_queue")
        self.assertIsNotNone(bq, "brief_queue must be present for ini-001")
        self.assertIn("executing", bq)
        self.assertIn("ready", bq)
        self.assertIn("draft", bq)
        self.assertEqual(bq["executing"], "briefs/brief-a")
        self.assertEqual(bq["ready"], ["briefs/brief-b"])
        self.assertEqual(bq["draft"], [])

        # work.ready — spec/alpha (no deps)
        ready = data.get("work", {}).get("ready", [])
        ready_paths = {e["path"] for e in ready}
        self.assertIn("spec/alpha", ready_paths, f"spec/alpha not ready; got={ready_paths}")
        alpha = next(e for e in ready if e["path"] == "spec/alpha")
        self.assertIn("ini_slug", alpha)
        self.assertIn("blocking_needs", alpha)

        # work.blocked — spec/beta (needs work:spec/alpha still in queue)
        blocked = data.get("work", {}).get("blocked", [])
        self.assertGreater(len(blocked), 0, "spec/beta should be blocked by spec/alpha")
        beta = next((e for e in blocked if e["path"] == "spec/beta"), None)
        self.assertIsNotNone(beta, f"spec/beta not in blocked: {blocked}")
        self.assertIn("blocking_needs", beta)
        self.assertIsInstance(beta["blocking_needs"], list)
        self.assertGreater(len(beta["blocking_needs"]), 0)
        self.assertIn("ini_slug", beta)

        # work.active entry shape
        active = data.get("work", {}).get("active", [])
        self.assertTrue(any(e["path"] == "spec/gamma" for e in active), f"active={active}")
        if active:
            self.assertIn("ini_slug", active[0])

        # work.shipped entry shape
        shipped = data.get("work", {}).get("shipped", [])
        self.assertTrue(any(e["path"] == "spec/delta" for e in shipped), f"shipped={shipped}")
        if shipped:
            self.assertIn("ini_slug", shipped[0])

        # shaping.ready — topic-x (type=shape, no needs)
        shaping_ready = data.get("shaping", {}).get("ready", [])
        topic_x = next((e for e in shaping_ready if e.get("slug") == "topic-x"), None)
        self.assertIsNotNone(topic_x, f"topic-x not in shaping.ready: {shaping_ready}")
        self.assertIn("entry_type", topic_x)
        self.assertIn("ini_slug", topic_x)
        self.assertIn("blocking_needs", topic_x)

    def test_cli_no_writes_with_specs(self) -> None:
        """AC8: CLI does not write any files even when docs/specs/ subtree is present."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MINIMAL_TOML)
        # Add docs/specs/ with Type 1 (Approved, not in queue) and Type 2 (Shipped, in queue)
        # to exercise the spec-reading paths absent from test_cli_no_writes.
        self._make_spec(root, "alpha", status="Shipped")    # Type 2: in queue
        self._make_spec(root, "orphan", status="Approved")  # Type 1: not in any work list

        def _snapshot(d: Path) -> dict[str, float]:
            return {
                str(p.relative_to(d)): p.stat().st_mtime
                for p in d.rglob("*") if p.is_file()
            }

        before = _snapshot(root)
        _run_cli("--root", str(root))
        after = _snapshot(root)
        self.assertEqual(before, after, "CLI created or modified files with spec subtree present")

    def test_cli_type2_cleanup_ops_populated(self) -> None:
        """AC5/AC7: type2_cleanup_ops is non-empty when a Type 2 finding exists."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        # Create workspace with a queue entry whose spec is Shipped (Type 2)
        root = self._write_workspace(_MINIMAL_TOML)
        # Make spec/alpha with Shipped status
        self._make_spec(root, "alpha", status="Shipped")
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 0, f"stderr: {r.stderr}")
        data = json.loads(r.stdout)
        cleanup_ops = data.get("reconciliation", {}).get("type2_cleanup_ops", [])
        self.assertGreater(
            len(cleanup_ops), 0,
            "Expected non-empty type2_cleanup_ops for Type 2 finding",
        )

    def test_shaping_schema_has_signals(self) -> None:
        """AC5: shaping output has ready, signals, blocked keys."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MINIMAL_TOML)
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        shaping = data.get("shaping", {})
        self.assertIn("ready", shaping)
        self.assertIn("signals", shaping)
        self.assertIn("blocked", shaping)
        self.assertIn("active_entries", shaping)
        self.assertNotIn("active", shaping)  # unsourced key must not appear

    def test_cli_diagnostics_present(self) -> None:
        """AC5: diagnostics has workspace_files_read and spec_files_read."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        root = self._write_workspace(_MINIMAL_TOML)
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        diag = data.get("diagnostics", {})
        self.assertIn("workspace_files_read", diag)
        self.assertIn("spec_files_read", diag)
        self.assertEqual(diag["workspace_files_read"], 1)


# ── Test: symlink confinement guard (AC19) ────────────────────────────────────

class SymlinkConfinementTests(_CliBase):
    """AC19: Type-1 scan does not follow symlinked spec dirs escaping root."""

    @unittest.skipIf(sys.platform == "win32", "symlink test not portable on Windows")
    def test_symlink_escape_not_read(self) -> None:
        """Plant a symlink under docs/specs/ pointing outside root; assert not read."""
        if not _ENGINE.exists():
            self.skipTest("Engine not yet moved")

        root = self._write_workspace(_MINIMAL_TOML)
        specs = root / "docs" / "specs"
        specs.mkdir(parents=True)

        # External directory with an Approved spec.md
        external = self.tmp / "external"
        external.mkdir()
        (external / "spec.md").write_text(
            "# Spec: external\n\n- **Status:** Approved\n",
            encoding="utf-8",
        )

        # Symlink under docs/specs/ pointing outside repo root
        link = specs / "escape-link"
        link.symlink_to(external)

        # The engine must not return a Type 1 finding for this symlinked dir
        import importlib.util
        spec = importlib.util.spec_from_file_location("workspace_status_engine_sym", _ENGINE)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        sys.modules.setdefault("workspace_status_engine_sym", mod)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        result = mod.analyze(root)
        type1_paths = {f.spec_path for f in result.type1}
        self.assertNotIn(
            "spec/escape-link", type1_paths,
            "Type-1 scan followed a symlink escaping the docs/specs/ boundary",
        )


# ── Test: SKILL.md wiring (structural) ───────────────────────────────────────

class SkillWiringTests(unittest.TestCase):
    """Structural checks that SKILL.md invokes the CLI and has no duplicate DAG."""

    _SKILL_PATH = _REPO_ROOT / "packs/core/.apm/skills/workspace-status/SKILL.md"

    def _skill_text(self) -> str:
        return self._SKILL_PATH.read_text(encoding="utf-8")

    def test_skill_invokes_cli(self) -> None:
        """AC4: SKILL.md contains scripts/workspace_status.py."""
        text = self._skill_text()
        self.assertIn("scripts/workspace_status.py", text)

    def test_skill_no_dag_prose(self) -> None:
        """AC4/AC15: No embedded DAG resolution procedure or readiness recompute."""
        text = self._skill_text()
        for forbidden in (
            "### 2. Resolve the DAG",
            "resolve the DAG",
            "whose `needs` are all satisfied",
        ):
            self.assertNotIn(forbidden, text, f"SKILL.md still contains: {forbidden!r}")

    def test_skill_cleanup_preserved(self) -> None:
        """AC7: Cleanup confirmation language is preserved."""
        text = self._skill_text()
        self.assertIn("Reply Y", text)

    def test_skill_no_quickfull(self) -> None:
        """AC15: No quick/full mode flags."""
        text = self._skill_text()
        self.assertNotIn("--quick", text)
        self.assertNotIn("--full", text)

    def test_skill_parallel_graph_preserved(self) -> None:
        """AC6: §6b/§6c parallel-opportunity graph strings are present."""
        text = self._skill_text()
        self.assertIn("parallel opportunities", text)
        self.assertIn("--bg", text)

    def test_skill_quoted_root(self) -> None:
        """Boundaries: SKILL.md passes --root safely (quoted or discrete argv)."""
        text = self._skill_text()
        # Argv form: "--root" as a quoted array element (canonical).
        # Shell form: --root "<path>" or --root '<path>' (fallback uses --root .).
        self.assertTrue(
            '"--root"' in text or '--root "' in text or "--root '" in text,
            "SKILL.md must pass --root as a quoted shell arg or discrete argv element",
        )


if __name__ == "__main__":
    unittest.main()
