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

# Fixture workspace.toml for repair-plan/repair-apply tests
_REPAIR_TOML = """\
["ini-001"]
name      = "Repair Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/shipped-feature", "spec/archived-feature"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""


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
        "argparse", "dataclasses", "datetime", "hashlib", "importlib", "json",
        "os", "pathlib", "re", "stat", "sys", "tempfile", "time", "tomllib",
        "typing", "unittest", "__future__", "collections", "functools",
        "itertools", "abc", "contextlib", "io", "shutil", "traceback",
    })

    def _check_script(self, path: Path, allowed_extras: frozenset[str] = frozenset()) -> None:
        import ast
        allowed = self._STDLIB_MODULES | allowed_extras
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        forbidden: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top not in allowed:
                        forbidden.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import — allowed (script-relative)
                mod = node.module or ""
                top = mod.split(".")[0]
                if top and top not in allowed:
                    forbidden.append(mod)
        self.assertEqual(
            forbidden, [],
            f"{path.name} has non-stdlib imports: {forbidden}",
        )

    def test_cli_stdlib_only(self) -> None:
        if _CLI.exists():
            # tomlkit is a blessed CLI-only import (repair-apply write path)
            self._check_script(_CLI, allowed_extras=frozenset({"tomlkit"}))
        else:
            self.skipTest("CLI not yet created")

    def test_engine_stdlib_only(self) -> None:
        if _ENGINE.exists():
            # Engine must remain stdlib-only; tomlkit is NOT allowed here
            self._check_script(_ENGINE)
        else:
            self.skipTest("Engine not yet moved")

    def test_engine_has_no_tomlkit_import(self) -> None:
        """Engine must never import tomlkit — belt-and-suspenders for AC5/AC24."""
        if not _ENGINE.exists():
            self.skipTest("Engine not yet moved")
        text = _ENGINE.read_text(encoding="utf-8")
        self.assertNotIn(
            "tomlkit",
            text,
            "workspace_status_engine.py must not import tomlkit (stdlib-only rule)",
        )

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


# ── Test: Order 1B subcommands ────────────────────────────────────────────────

_SIMPLE_TOML = """\
["ini-001"]
name      = "Alpha"
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

_TWO_INI_SHARED_SLUG_TOML = """\
["ini-001"]
name      = "Alpha"
status    = "active"
milestone = "M1"

["ini-001".work]
active  = []
shipped = []
queue   = ["spec/shared-slug"]

["ini-001".shaping_queue]
active  = []
backlog = []

["ini-002"]
name      = "Beta"
status    = "active"
milestone = "M1"

["ini-002".work]
active  = []
shipped = []
queue   = ["spec/shared-slug"]

["ini-002".shaping_queue]
active  = []
backlog = []
"""


class SubcommandTests(_CliBase):
    """Order 1B: status / reconcile / no-subcommand / explain routing."""

    def _run_status(self, root: Path) -> dict:
        r = _run_cli("status", "--root", str(root))
        self.assertEqual(r.returncode, 0, f"status failed: {r.stderr}")
        return json.loads(r.stdout)

    def _run_reconcile(self, root: Path) -> dict:
        r = _run_cli("reconcile", "--root", str(root))
        self.assertEqual(r.returncode, 0, f"reconcile failed: {r.stderr}")
        return json.loads(r.stdout)

    def _run_explain(self, root: Path, item: str):
        return _run_cli("explain", "--root", str(root), "--item", item)

    def test_status_subcommand_mode_field(self) -> None:
        root = self._write_workspace(_SIMPLE_TOML)
        data = self._run_status(root)
        self.assertEqual(data.get("mode"), "status")

    def test_status_subcommand_no_global_scan(self) -> None:
        root = self._write_workspace(_SIMPLE_TOML)
        data = self._run_status(root)
        scan = data.get("scan", {})
        self.assertFalse(scan.get("global_spec_scan_performed"),
                         "status mode must not perform global scan")
        self.assertEqual(scan.get("global_scan_spec_files_read"), 0)

    def test_status_bounded_type1_absent(self) -> None:
        root = self._write_workspace(_SIMPLE_TOML)
        self._make_spec(root, "untracked-live", "Implementing")
        data = self._run_status(root)
        recon = data.get("reconciliation", {})
        self.assertEqual(recon.get("type1"), [],
                         "status mode must not find any Type 1 findings")
        self.assertEqual(recon.get("types_performed"), [2, 3])

    def test_reconcile_subcommand_mode_field(self) -> None:
        root = self._write_workspace(_SIMPLE_TOML)
        data = self._run_reconcile(root)
        self.assertEqual(data.get("mode"), "reconcile")

    def test_reconcile_subcommand_global_scan(self) -> None:
        root = self._write_workspace(_SIMPLE_TOML)
        data = self._run_reconcile(root)
        scan = data.get("scan", {})
        self.assertTrue(scan.get("global_spec_scan_performed"),
                        "reconcile mode must perform global scan")
        self.assertEqual(data.get("reconciliation", {}).get("types_performed"), [1, 2, 3])

    def test_ac10_bounded_structural_cost(self) -> None:
        """AC10: status mode never reads the global spec tree."""
        root = self._write_workspace(_SIMPLE_TOML)
        self._make_spec(root, "alpha", "Approved")
        # M untracked live specs not in workspace
        for i in range(3):
            self._make_spec(root, f"untracked-{i}", "Implementing")
        N = 1  # one declared queue entry
        data = self._run_status(root)
        scan = data.get("scan", {})
        self.assertEqual(scan.get("global_scan_spec_files_read"), 0)
        self.assertLessEqual(scan.get("declared_spec_files_read", N + 1), N)

    def test_ac11_full_structural_cost(self) -> None:
        """AC11: reconcile mode reads all live specs including untracked."""
        root = self._write_workspace(_SIMPLE_TOML)
        self._make_spec(root, "alpha", "Approved")
        M = 3  # M untracked live specs
        for i in range(M):
            self._make_spec(root, f"untracked-{i}", "Implementing")
        data = self._run_reconcile(root)
        scan = data.get("scan", {})
        self.assertGreaterEqual(scan.get("global_scan_spec_files_read", 0), M)

    def test_no_subcommand_compatibility(self) -> None:
        """AC9: no subcommand → reconcile mode, exit 0."""
        root = self._write_workspace(_SIMPLE_TOML)
        r = _run_cli("--root", str(root))
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data.get("mode"), "reconcile")
        self.assertEqual(data.get("reconciliation", {}).get("types_performed"), [1, 2, 3])

    def test_no_subcommand_stderr_warning(self) -> None:
        """AC9: deprecation warning appears only on stderr."""
        root = self._write_workspace(_SIMPLE_TOML)
        r = _run_cli("--root", str(root))
        self.assertIn("no subcommand", r.stderr.lower())
        self.assertNotIn("no subcommand", r.stdout.lower())

    def test_explain_matched(self) -> None:
        """AC8/AC10: explain matched entry; global_scan_spec_files_read == 0."""
        root = self._write_workspace(_SIMPLE_TOML)
        r = self._run_explain(root, "spec/alpha")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data.get("mode"), "explain")
        self.assertEqual(data.get("selector_status"), "matched")
        item = data.get("explained_item", {})
        for key in ("path", "slug", "ini_slug", "list", "classification",
                    "blocking_needs", "dependencies", "downstream_unblocked"):
            self.assertIn(key, item, f"explained_item missing key: {key!r}")
        # AC10 explain coverage
        self.assertEqual(data.get("scan", {}).get("global_scan_spec_files_read"), 0)

    def test_explain_not_found(self) -> None:
        """explain with unknown selector → exit 0, not_found."""
        root = self._write_workspace(_SIMPLE_TOML)
        r = self._run_explain(root, "spec/does-not-exist")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data.get("selector_status"), "not_found")

    def test_explain_cli_ambiguous_exit0(self) -> None:
        """AC14: ambiguous selector → exit 0, ambiguous status."""
        root = self._write_workspace(_TWO_INI_SHARED_SLUG_TOML)
        r = self._run_explain(root, "shared-slug")
        self.assertEqual(r.returncode, 0,
                         f"ambiguous must be exit 0, got {r.returncode}: {r.stderr}")
        data = json.loads(r.stdout)
        self.assertEqual(data.get("selector_status"), "ambiguous")
        self.assertGreaterEqual(len(data.get("matches", [])), 2)

    def test_reconciliation_metadata_fields(self) -> None:
        """AC12: status and reconcile include performed/complete/types_performed."""
        root = self._write_workspace(_SIMPLE_TOML)
        for mode_fn in (self._run_status, self._run_reconcile):
            data = mode_fn(root)
            recon = data.get("reconciliation", {})
            for key in ("performed", "complete", "types_performed"):
                self.assertIn(key, recon,
                              f"{data.get('mode')} reconciliation missing {key!r}")
        # explain mode must NOT include a reconciliation object
        r = self._run_explain(root, "spec/alpha")
        explain_data = json.loads(r.stdout)
        self.assertNotIn("reconciliation", explain_data,
                         "explain mode must not include reconciliation object")

    def test_scan_field_present(self) -> None:
        """All modes include scan object with four required keys."""
        required = {
            "global_spec_scan_performed", "workspace_files_read",
            "declared_spec_files_read", "global_scan_spec_files_read",
        }
        root = self._write_workspace(_SIMPLE_TOML)
        for label, proc in [
            ("status", _run_cli("status", "--root", str(root))),
            ("reconcile", _run_cli("reconcile", "--root", str(root))),
            ("explain", _run_cli("explain", "--root", str(root), "--item", "spec/alpha")),
        ]:
            data = json.loads(proc.stdout)
            scan_keys = set(data.get("scan", {}).keys())
            missing = required - scan_keys
            self.assertFalse(missing, f"{label} scan missing keys: {missing}")

    def test_diagnostics_compat(self) -> None:
        """AC13: diagnostics present in status/reconcile; absent in explain."""
        root = self._write_workspace(_SIMPLE_TOML)
        for mode_fn in (self._run_status, self._run_reconcile):
            data = mode_fn(root)
            diag = data.get("diagnostics", {})
            self.assertIn("workspace_files_read", diag)
            self.assertIn("spec_files_read", diag)
            scan = data.get("scan", {})
            expected = (scan.get("declared_spec_files_read", 0)
                        + scan.get("global_scan_spec_files_read", 0))
            self.assertEqual(diag.get("spec_files_read"), expected,
                             f"{data.get('mode')} diagnostics.spec_files_read mismatch")
        # explain mode must not include diagnostics
        r = self._run_explain(root, "spec/alpha")
        explain_data = json.loads(r.stdout)
        self.assertNotIn("diagnostics", explain_data,
                         "explain mode must not include diagnostics")

    def test_absent_workspace_mode_field(self) -> None:
        """AC9: absent-workspace JSON includes mode for each subcommand."""
        empty = self.tmp / "empty-dir"
        empty.mkdir(exist_ok=True)
        for subcmd, extra in [
            (["status"], []),
            (["reconcile"], []),
            (["explain", "--item", "spec/x"], []),
            ([], []),
        ]:
            r = _run_cli(*subcmd, "--root", str(empty), *extra)
            self.assertEqual(r.returncode, 1)
            data = json.loads(r.stdout)
            self.assertIn("mode", data,
                          f"absent-workspace missing 'mode' for subcmd={subcmd!r}")

    def test_cli_no_writes_all_modes(self) -> None:
        """AC19: CLI is read-only in all three modes."""
        root = self._write_workspace(_SIMPLE_TOML)
        before = {
            str(p): p.stat().st_mtime_ns
            for p in root.rglob("*") if p.is_file()
        }
        for subcmd, extra in [
            (["status"], []),
            (["reconcile"], []),
            (["explain", "--item", "spec/alpha"], []),
        ]:
            _run_cli(*subcmd, "--root", str(root), *extra)
        after = {
            str(p): p.stat().st_mtime_ns
            for p in root.rglob("*") if p.is_file()
        }
        self.assertEqual(before, after, "CLI wrote to the fixture directory")

    def test_explain_missing_item_arg(self) -> None:
        """AC14b: explain without --item exits 2, stderr non-empty, stdout empty."""
        root = self._write_workspace(_SIMPLE_TOML)
        r = _run_cli("explain", "--root", str(root))
        self.assertEqual(r.returncode, 2,
                         f"explain without --item must exit 2, got {r.returncode}")
        self.assertTrue(r.stderr.strip(), "stderr must be non-empty for missing --item")
        self.assertEqual(r.stdout.strip(), "",
                         "stdout must be empty when --item is missing")


# ── Order 2B: repair-plan ─────────────────────────────────────────────────────

class RepairPlanTests(_CliBase):
    """AC6–AC10, AC19, AC21a, AC25, AC26: repair-plan subcommand."""

    def _make_repair_fixture(self) -> Path:
        root = self._write_workspace(_REPAIR_TOML)
        self._make_spec(root, "shipped-feature", "Shipped")
        self._make_spec(root, "archived-feature", "Archived")
        return root

    def test_repair_plan_json_contract(self) -> None:
        """AC6: stdout has all required top-level fields."""
        root = self._make_repair_fixture()
        r = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r.returncode, 0, f"exit code: {r.stderr}")
        data = json.loads(r.stdout)
        for field in ("schema_version", "mode", "workspace_present", "workspace_root",
                      "workspace_fingerprint", "plan_id",
                      "automatic_operations", "manual_findings"):
            self.assertIn(field, data, f"missing field: {field}")
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["mode"], "repair-plan")
        self.assertTrue(data["workspace_present"])

    def test_repair_plan_uses_full_reconcile(self) -> None:
        """AC10: repair-plan uses analyze() (full reconciliation, not bounded)."""
        root = self._make_repair_fixture()
        r = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertTrue(data["scan"]["global_spec_scan_performed"])
        self.assertIn(1, data["reconciliation"]["types_performed"])

    def test_repair_plan_writes_plan_file(self) -> None:
        """AC8: default plan file written; matches stdout except workspace_root is omitted."""
        root = self._make_repair_fixture()
        r = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r.returncode, 0)
        plan_file = root / ".workspace-repair-plan.json"
        self.assertTrue(plan_file.exists(), "plan file must be created")
        file_data = json.loads(plan_file.read_text(encoding="utf-8"))
        stdout_data = json.loads(r.stdout)
        # workspace_root is an absolute path — kept in transient stdout but omitted
        # from the persisted file to avoid privacy leaks if the file is committed.
        self.assertNotIn("workspace_root", file_data, "plan file must not contain workspace_root")
        expected = {k: v for k, v in stdout_data.items() if k != "workspace_root"}
        self.assertEqual(file_data, expected, "plan file must match stdout (minus workspace_root)")

    def test_repair_plan_custom_plan_file(self) -> None:
        """AC8: --plan-file overrides output path."""
        root = self._make_repair_fixture()
        custom = root / "my-plan.json"
        r = _run_cli("repair-plan", "--root", str(root), "--plan-file", str(custom))
        self.assertEqual(r.returncode, 0)
        self.assertTrue(custom.exists())

    def test_repair_plan_empty_automatic_ops_exits_0(self) -> None:
        """AC7: empty automatic_operations → exit 0, plan still written."""
        root = self._write_workspace(_MINIMAL_TOML)
        self._make_spec(root, "alpha", "Approved")
        r = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["automatic_operations"], [])
        plan_file = root / ".workspace-repair-plan.json"
        self.assertTrue(plan_file.exists())

    def test_repair_plan_absent_workspace_exits_1(self) -> None:
        """AC9: absent workspace.toml → exit 1, mode=repair-plan in JSON."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            r = _run_cli("repair-plan", "--root", td)
            self.assertEqual(r.returncode, 1)
            data = json.loads(r.stdout)
            self.assertEqual(data["mode"], "repair-plan")
            self.assertFalse(data["workspace_present"])

    def test_repair_plan_no_writes_to_workspace_toml(self) -> None:
        """AC19: repair-plan must not write to workspace.toml."""
        import hashlib
        root = self._make_repair_fixture()
        before = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        r = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r.returncode, 0)
        after = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        self.assertEqual(before, after, "repair-plan must not modify workspace.toml")

    def test_repair_plan_stdout_emitted_on_plan_file_write_failure(self) -> None:
        """AC26: stdout emitted even if plan file write fails; exit 2 on failure."""
        root = self._make_repair_fixture()
        unwritable_dir = root / "no-write"
        unwritable_dir.mkdir()
        unwritable_dir.chmod(0o555)
        try:
            custom = unwritable_dir / "plan.json"
            r = _run_cli("repair-plan", "--root", str(root), "--plan-file", str(custom))
            self.assertEqual(r.returncode, 2, "must exit 2 on write failure")
            # stdout must still be valid JSON (plan emitted before file write)
            data = json.loads(r.stdout)
            self.assertEqual(data["mode"], "repair-plan")
        finally:
            unwritable_dir.chmod(0o755)

    def test_repair_plan_plan_file_confinement(self) -> None:
        """AC16d: --plan-file via symlink escaping root → exit 2, plan_file_outside_root."""
        root = self._make_repair_fixture()
        import tempfile as _tmp
        with _tmp.TemporaryDirectory() as outside:
            link = root / "escape-link.json"
            Path(str(link)).symlink_to(str(Path(outside) / "escape.json"))
            r = _run_cli("repair-plan", "--root", str(root), "--plan-file", str(link))
            self.assertEqual(r.returncode, 2)
            data = json.loads(r.stdout)
            # Confinement check fires: resolves symlink → outside root → plan_file_outside_root
            self.assertEqual(data.get("reason"), "plan_file_outside_root")
            self.assertFalse(data.get("applied"), "confinement error must carry applied:false")

    def test_repair_plan_plan_file_confinement_direct_path(self) -> None:
        """AC16d: --plan-file direct path outside root → exit 2."""
        import tempfile as _tmp
        root = self._make_repair_fixture()
        with _tmp.TemporaryDirectory() as outside:
            evil = Path(outside) / "evil.json"
            r = _run_cli("repair-plan", "--root", str(root), "--plan-file", str(evil))
            self.assertEqual(r.returncode, 2)
            data = json.loads(r.stdout)
            self.assertEqual(data.get("reason"), "plan_file_outside_root")
            self.assertFalse(data.get("applied"), "confinement error must carry applied:false")

    def test_repair_plan_plan_file_is_workspace_toml(self) -> None:
        """AC27: --plan-file == workspace.toml → exit 2, reason=plan_file_is_workspace_toml."""
        root = self._make_repair_fixture()
        workspace_toml = root / "workspace.toml"
        r = _run_cli("repair-plan", "--root", str(root), "--plan-file", str(workspace_toml))
        self.assertEqual(r.returncode, 2)
        data = json.loads(r.stdout)
        self.assertEqual(data.get("reason"), "plan_file_is_workspace_toml")
        self.assertFalse(data.get("applied"), "guard error must carry applied:false")
        # workspace.toml must not be clobbered
        self.assertIn("ini-001", workspace_toml.read_text(encoding="utf-8"))


# ── Order 2B: repair-apply ────────────────────────────────────────────────────

class RepairApplyTests(_CliBase):
    """AC11–AC20c, AC25: repair-apply subcommand."""

    def _make_repair_fixture(self, shipped: bool = False) -> tuple[Path, Path]:
        """Returns (root, plan_file_path) with plan already generated."""
        root = self._write_workspace(_REPAIR_TOML)
        self._make_spec(root, "shipped-feature", "Shipped")
        self._make_spec(root, "archived-feature", "Archived")
        # Generate plan
        r = _run_cli("repair-plan", "--root", str(root))
        assert r.returncode == 0, f"plan generation failed: {r.stderr}"
        plan_file = root / ".workspace-repair-plan.json"
        return root, plan_file

    def test_repair_apply_queue_to_shipped_bare_string(self) -> None:
        """AC13: bare string entry removed from queue; appended to shipped."""
        root, _ = self._make_repair_fixture()
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0, f"exit: {r.stderr}")
        data = json.loads(r.stdout)
        self.assertTrue(data["applied"])
        applied_paths = [p["path"] for p in data["per_operation"] if p["applied"]]
        self.assertIn("spec/shipped-feature", applied_paths)
        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        queue = ws["ini-001"]["work"]["queue"]
        shipped = ws["ini-001"]["work"]["shipped"]
        self.assertNotIn("spec/shipped-feature", queue)
        self.assertIn("spec/shipped-feature", shipped)

    def test_repair_apply_queue_remove_archived(self) -> None:
        """AC13: archived entry removed from queue; shipped unchanged."""
        root, _ = self._make_repair_fixture()
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        queue = ws["ini-001"]["work"]["queue"]
        self.assertNotIn("spec/archived-feature", queue)
        shipped_before = 1  # spec/shipped-feature was added
        self.assertEqual(len(ws["ini-001"]["work"]["shipped"]), shipped_before)

    def test_repair_apply_queue_to_shipped_inline_object(self) -> None:
        """AC13/AC17: inline object entry removed in place; other entries intact."""
        inline_toml = """\
["ini-001"]
name      = "Inline Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "spec/inline-shipped", needs = "work:spec/other"}, "spec/keep-me"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(inline_toml)
        self._make_spec(root, "inline-shipped", "Shipped")
        self._make_spec(root, "keep-me", "Approved")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        queue = ws["ini-001"]["work"]["queue"]
        paths_in_queue = [
            e if isinstance(e, str) else e.get("path", "") for e in queue
        ]
        self.assertNotIn("spec/inline-shipped", paths_in_queue)
        self.assertIn("spec/keep-me", paths_in_queue)

    def test_repair_apply_fingerprint_mismatch(self) -> None:
        """AC12: fingerprint mismatch → exit 2, applied:false, reason:fingerprint_mismatch."""
        root, plan_file = self._make_repair_fixture()
        # Modify workspace.toml after plan was generated
        (root / "workspace.toml").write_text(
            _REPAIR_TOML + "\n# modified\n", encoding="utf-8"
        )
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2, f"must exit 2: {r.stderr}")
        data = json.loads(r.stdout)
        self.assertFalse(data["applied"])
        self.assertEqual(data["reason"], "fingerprint_mismatch")
        self.assertIn("fingerprint mismatch", r.stderr)
        self.assertNotIn(str(root.resolve()), r.stderr, "must not leak absolute path")

    def test_repair_apply_plan_not_found(self) -> None:
        """AC15: plan file not found → exit 2, reason:plan_file_not_found."""
        root = self._write_workspace(_REPAIR_TOML)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        data = json.loads(r.stdout)
        self.assertEqual(data["reason"], "plan_file_not_found")
        self.assertIn("plan file not found", r.stderr)
        self.assertNotIn(str(root.resolve()), r.stderr, "must not leak absolute path")

    def test_repair_apply_malformed_plan(self) -> None:
        """AC16: malformed plan JSON → exit 2, reason:plan_file_parse_error."""
        root = self._write_workspace(_REPAIR_TOML)
        (root / ".workspace-repair-plan.json").write_text("{{{not json", encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        data = json.loads(r.stdout)
        self.assertEqual(data["reason"], "plan_file_parse_error")
        self.assertNotIn(str(root.resolve()), r.stderr, "must not leak absolute path")

    def test_repair_apply_invalid_plan_schema(self) -> None:
        """AC12a: unknown operation_type → exit 2, reason:plan_invalid."""
        root = self._write_workspace(_REPAIR_TOML)
        bad_plan = json.dumps({
            "schema_version": 1,
            "workspace_fingerprint": "x",
            "automatic_operations": [
                {"operation_type": "delete-everything", "spec_path": "spec/foo",
                 "spec_status": "Shipped", "ini_slug": "ini-001"}
            ],
        })
        (root / ".workspace-repair-plan.json").write_text(bad_plan, encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        data = json.loads(r.stdout)
        self.assertEqual(data["reason"], "plan_invalid")

    def test_repair_apply_plan_invalid_spec_path_traversal(self) -> None:
        """AC12a: spec_path with .. → exit 2, reason:plan_invalid."""
        root, plan_file = self._make_repair_fixture()
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        plan_data["automatic_operations"] = [
            {"operation_type": "queue-to-shipped", "spec_path": "spec/../../evil",
             "spec_status": "Shipped", "ini_slug": "ini-001"}
        ]
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["reason"], "plan_invalid")

    def test_repair_apply_plan_invalid_spec_path_absolute(self) -> None:
        """AC12a: absolute spec_path → exit 2, reason:plan_invalid."""
        root, plan_file = self._make_repair_fixture()
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        plan_data["automatic_operations"] = [
            {"operation_type": "queue-to-shipped", "spec_path": "/etc/passwd",
             "spec_status": "Shipped", "ini_slug": "ini-001"}
        ]
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["reason"], "plan_invalid")

    def test_repair_apply_plan_invalid_coupling(self) -> None:
        """AC12a: operation_type/spec_status coupling mismatch → exit 2, plan_invalid."""
        root, plan_file = self._make_repair_fixture()
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        plan_data["automatic_operations"] = [
            {"operation_type": "queue-to-shipped", "spec_path": "spec/foo",
             "spec_status": "Archived", "ini_slug": "ini-001"}
        ]
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["reason"], "plan_invalid")

    def test_repair_apply_plan_invalid_empty_ini_slug(self) -> None:
        """AC12a: empty ini_slug → exit 2, plan_invalid."""
        root, plan_file = self._make_repair_fixture()
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        plan_data["automatic_operations"] = [
            {"operation_type": "queue-to-shipped", "spec_path": "spec/foo",
             "spec_status": "Shipped", "ini_slug": ""}
        ]
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["reason"], "plan_invalid")

    def test_repair_apply_plan_invalid_non_dict_json(self) -> None:
        """AC12a: top-level non-dict JSON (list) → exit 2, plan_invalid."""
        root, plan_file = self._make_repair_fixture()
        plan_file.write_text("[]", encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["reason"], "plan_invalid")

    def test_repair_apply_plan_invalid_windows_path(self) -> None:
        """AC12a: Windows-style spec_path (backslash) → exit 2, plan_invalid."""
        root, plan_file = self._make_repair_fixture()
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        plan_data["automatic_operations"] = [
            {"operation_type": "queue-to-shipped", "spec_path": "spec\\shipped-feature",
             "spec_status": "Shipped", "ini_slug": "ini-001"}
        ]
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(json.loads(r.stdout)["reason"], "plan_invalid")

    def test_repair_apply_empty_operations_exits_0_no_write(self) -> None:
        """AC14: empty automatic_operations → exit 0, workspace.toml SHA-256 unchanged."""
        import hashlib
        root = self._write_workspace(_MINIMAL_TOML)
        self._make_spec(root, "alpha", "Approved")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        before = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        after = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        self.assertEqual(before, after, "must not write workspace.toml for empty ops")
        data = json.loads(r.stdout)
        self.assertEqual(data["operations_applied"], 0)
        self.assertEqual(data["per_operation"], [])
        # No stray tmp files
        tmp_files = list(root.glob(".workspace.toml.*.tmp"))
        self.assertEqual(tmp_files, [], f"stray tmp files: {tmp_files}")

    def test_repair_apply_workspace_absent(self) -> None:
        """AC16a: absent workspace.toml → exit 2, reason:workspace_absent."""
        import tempfile as _tmp
        with _tmp.TemporaryDirectory() as td:
            r = _run_cli("repair-apply", "--root", td, "--yes")
            self.assertEqual(r.returncode, 2)
            data = json.loads(r.stdout)
            self.assertEqual(data["reason"], "workspace_absent")

    def test_repair_apply_workspace_toml_symlink_escape(self) -> None:
        """AC16c: workspace.toml symlinked outside root → exit 2, workspace_outside_root."""
        import tempfile as _tmp
        root = Path(self.tmp / "repo")
        root.mkdir()
        with _tmp.TemporaryDirectory() as outside:
            target = Path(outside) / "real_workspace.toml"
            target.write_text(_REPAIR_TOML, encoding="utf-8")
            Path(str(root / "workspace.toml")).symlink_to(str(target))
            r = _run_cli("repair-apply", "--root", str(root), "--yes")
            self.assertEqual(r.returncode, 2)
            data = json.loads(r.stdout)
            self.assertEqual(data["reason"], "workspace_outside_root")

    def test_repair_apply_no_writes_to_active_list(self) -> None:
        """AC20: active-source findings never touch work.active."""
        import hashlib
        active_toml = """\
["ini-001"]
name      = "Active Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = []
active  = ["spec/live-work"]
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(active_toml)
        self._make_spec(root, "live-work", "Shipped")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        before = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        # Empty ops (active-source is manual) → exit 0, no write
        self.assertEqual(r.returncode, 0)
        after = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        self.assertEqual(before, after, "must not touch work.active")

    def test_repair_apply_atomic_write_no_stray_temp(self) -> None:
        """AC13: no stray .workspace.toml.*.tmp after successful apply."""
        root, _ = self._make_repair_fixture()
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        tmp_files = list(root.glob(".workspace.toml.*.tmp"))
        self.assertEqual(tmp_files, [], f"stray tmp files: {tmp_files}")

    def test_repair_apply_spec_status_changed(self) -> None:
        """AC12b: spec status changes between plan and apply → skipped with spec_status_changed."""
        root, plan_file = self._make_repair_fixture()
        # Change shipped-feature spec from Shipped to Approved after plan
        spec_dir = root / "docs" / "specs" / "shipped-feature"
        (spec_dir / "spec.md").write_text(
            "# Spec: shipped-feature\n\n- **Status:** Approved\n", encoding="utf-8"
        )
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        skipped = [p for p in data["per_operation"] if not p["applied"]]
        self.assertTrue(any(p["reason"] == "spec_status_changed" for p in skipped))
        # workspace.toml SHA must be unchanged for the skipped op
        # (archived-feature may still have been applied)
        # Find if shipped-feature was skipped and archived still applied
        shipped_op = next(
            (p for p in data["per_operation"] if p["path"] == "spec/shipped-feature"), None
        )
        self.assertIsNotNone(shipped_op)
        self.assertFalse(shipped_op["applied"])
        self.assertEqual(shipped_op["reason"], "spec_status_changed")

    def test_repair_apply_multiple_operations(self) -> None:
        """AC19a: multiple operations across initiatives both applied."""
        multi_toml = """\
["ini-001"]
name      = "Initiative One"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/feat-a"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []

["ini-002"]
name      = "Initiative Two"
status    = "active"
milestone = "M2"

["ini-002".work]
queue   = ["spec/feat-b"]
active  = []
shipped = []

["ini-002".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(multi_toml)
        self._make_spec(root, "feat-a", "Shipped")
        self._make_spec(root, "feat-b", "Shipped")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertGreaterEqual(data["operations_applied"], 2)

    def test_repair_apply_plan_file_confinement(self) -> None:
        """AC16d: --plan-file via symlink outside root → exit 2, plan_file_outside_root."""
        import tempfile as _tmp
        root = self._make_repair_fixture()[0]
        with _tmp.TemporaryDirectory() as outside:
            link = root / "escape.json"
            Path(str(link)).symlink_to(str(Path(outside) / "x.json"))
            r = _run_cli("repair-apply", "--root", str(root), "--plan-file", str(link), "--yes")
            self.assertEqual(r.returncode, 2)
            data = json.loads(r.stdout)
            self.assertEqual(data.get("reason"), "plan_file_outside_root")

    def test_repair_apply_plan_file_confinement_direct_path(self) -> None:
        """AC16d: --plan-file direct path outside root → exit 2."""
        import tempfile as _tmp
        root = self._make_repair_fixture()[0]
        with _tmp.TemporaryDirectory() as outside:
            evil = Path(outside) / "evil.json"
            r = _run_cli("repair-apply", "--root", str(root), "--plan-file", str(evil), "--yes")
            self.assertEqual(r.returncode, 2)
            data = json.loads(r.stdout)
            self.assertEqual(data.get("reason"), "plan_file_outside_root")

    def test_repair_apply_deduplication(self) -> None:
        """AC13: spec_path already in shipped → not appended again."""
        already_shipped_toml = """\
["ini-001"]
name      = "Dedup Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/already-there"]
active  = []
shipped = ["spec/already-there"]

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(already_shipped_toml)
        self._make_spec(root, "already-there", "Shipped")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        shipped = ws["ini-001"]["work"]["shipped"]
        self.assertEqual(shipped.count("spec/already-there"), 1, "must not duplicate")

    def test_repair_apply_spec_status_unreadable(self) -> None:
        """AC20a: missing spec.md → op skipped with spec_status_unreadable."""
        root, plan_file = self._make_repair_fixture()
        # Delete spec for shipped-feature after plan
        import shutil
        shutil.rmtree(root / "docs" / "specs" / "shipped-feature")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        skipped = [p for p in data["per_operation"] if not p["applied"]]
        self.assertTrue(
            any(p["reason"] == "spec_status_unreadable" for p in skipped),
            f"expected spec_status_unreadable, got: {skipped}"
        )

    def test_repair_apply_initiative_not_found(self) -> None:
        """AC20b: ini_slug absent from workspace.toml → per_operation initiative_not_found;
        workspace.toml unchanged (all ops skipped)."""
        import hashlib
        root, plan_file = self._make_repair_fixture()
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        # Compute spec_status_fingerprint from the actual spec file
        spec_file = root / "docs" / "specs" / "shipped-feature" / "spec.md"
        import hashlib as _hashlib
        status_line = next(
            ln for ln in spec_file.read_text(encoding="utf-8").splitlines()
            if ln.startswith("- **Status:**")
        )
        fp = _hashlib.sha256(status_line.encode("utf-8")).hexdigest()
        # Inject an op with a nonexistent ini_slug but real spec_path/status
        plan_data["automatic_operations"] = [
            {"operation_type": "queue-to-shipped", "spec_path": "spec/shipped-feature",
             "spec_status": "Shipped", "ini_slug": "ini-nonexistent",
             "finding_id": "type2:ini-nonexistent:queue:spec/shipped-feature",
             "operation_id": "aa" * 32,
             "spec_status_fingerprint": fp}
        ]
        # Recompute fingerprint for the current workspace.toml bytes
        plan_data["workspace_fingerprint"] = hashlib.sha256(
            (root / "workspace.toml").read_bytes()
        ).hexdigest()
        # Recompute plan_id to match the new operations
        _canon = json.dumps({
            "automatic_operations": plan_data["automatic_operations"],
            "manual_findings": plan_data.get("manual_findings", []),
            "schema_version": 1,
            "workspace_fingerprint": plan_data["workspace_fingerprint"],
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        plan_data["plan_id"] = hashlib.sha256(_canon.encode("ascii")).hexdigest()
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
        before = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        reasons = [p["reason"] for p in data["per_operation"] if not p["applied"]]
        self.assertIn("initiative_not_found", reasons)
        # Guard: all-skipped write-suppression — workspace.toml must be byte-unchanged
        after = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        self.assertEqual(before, after, "all-skipped: workspace.toml must not be rewritten")
        self.assertEqual(list(root.glob(".workspace.toml.*.tmp")), [],
                         "all-skipped: no stray temp files")

    def test_repair_apply_entry_not_found_in_queue(self) -> None:
        """AC20b: queue entry absent (fingerprint still matches) → entry_not_found_in_queue."""
        import hashlib
        root, plan_file = self._make_repair_fixture()
        # Create spec BEFORE injecting into the plan (fingerprint must match the real file)
        self._make_spec(root, "not-in-queue", "Shipped")
        spec_file2 = root / "docs" / "specs" / "not-in-queue" / "spec.md"
        import hashlib as _hashlib
        status_line2 = next(
            ln for ln in spec_file2.read_text(encoding="utf-8").splitlines()
            if ln.startswith("- **Status:**")
        )
        fp2 = _hashlib.sha256(status_line2.encode("utf-8")).hexdigest()
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        # Inject an op for a path not actually in the queue
        plan_data["automatic_operations"] = [
            {"operation_type": "queue-to-shipped", "spec_path": "spec/not-in-queue",
             "spec_status": "Shipped", "ini_slug": "ini-001",
             "finding_id": "type2:ini-001:queue:spec/not-in-queue",
             "operation_id": "bb" * 32,
             "spec_status_fingerprint": fp2}
        ]
        plan_data["workspace_fingerprint"] = hashlib.sha256(
            (root / "workspace.toml").read_bytes()
        ).hexdigest()
        # Recompute plan_id to match the new operations
        _canon = json.dumps({
            "automatic_operations": plan_data["automatic_operations"],
            "manual_findings": plan_data.get("manual_findings", []),
            "schema_version": 1,
            "workspace_fingerprint": plan_data["workspace_fingerprint"],
        }, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        plan_data["plan_id"] = hashlib.sha256(_canon.encode("ascii")).hexdigest()
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        reasons = [p["reason"] for p in data["per_operation"] if not p["applied"]]
        self.assertIn("entry_not_found_in_queue", reasons)

    def test_repair_apply_preserves_file_permissions(self) -> None:
        """AC28: Path.chmod preserves workspace.toml mode after atomic replace."""
        import stat
        root, _ = self._make_repair_fixture()
        ws = root / "workspace.toml"
        ws.chmod(0o644)
        orig_mode = stat.S_IMODE(ws.stat().st_mode)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        new_mode = stat.S_IMODE(ws.stat().st_mode)
        self.assertEqual(orig_mode, new_mode, "workspace.toml mode must survive atomic replace")

    def test_repair_apply_comment_preservation(self) -> None:
        """AC17: inline comments on kept entries survive in-place queue removal."""
        comment_toml = """\
["ini-001"]
name      = "Comment Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [
    "spec/remove-me",
    # keep this one
    "spec/keep-me",
]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(comment_toml)
        self._make_spec(root, "remove-me", "Shipped")
        self._make_spec(root, "keep-me", "Approved")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        raw = (root / "workspace.toml").read_text(encoding="utf-8")
        self.assertIn("# keep this one", raw,
                      "inline comment on kept entry must survive removal")
        # spec/remove-me must be gone from queue (it moves to shipped as bare string)
        import tomllib as _tl
        ws = _tl.loads(raw)
        queue = ws["ini-001"]["work"]["queue"]
        queue_paths = [e if isinstance(e, str) else e.get("path", "") for e in queue]
        self.assertNotIn("spec/remove-me", queue_paths,
                         "removed entry must not remain in queue")
        self.assertIn("spec/keep-me", queue_paths, "kept entry must remain in queue")

    def test_repair_apply_ac20_concurrent_write_through_apply(self) -> None:
        """AC20: path in queue (Shipped) AND active → queue op applied; active untouched."""
        dual_toml = """\
["ini-001"]
name      = "Dual-list Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/live-shipped"]
active  = ["spec/live-shipped"]
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(dual_toml)
        self._make_spec(root, "live-shipped", "Shipped")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        plan_json = json.loads(r_plan.stdout)
        # Engine routes queue finding as auto-op; active finding as manual
        auto_paths = [op["spec_path"] for op in plan_json["automatic_operations"]]
        self.assertIn("spec/live-shipped", auto_paths)
        manual_reasons = [f["reason"] for f in plan_json["manual_findings"]]
        self.assertIn("type2-active-source", manual_reasons)

        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertGreater(data["operations_applied"], 0, "queue op must be applied")

        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        # Queue entry removed
        queue = ws["ini-001"]["work"]["queue"]
        queue_paths = [e if isinstance(e, str) else e.get("path", "") for e in queue]
        self.assertNotIn("spec/live-shipped", queue_paths)
        # Shipped entry added
        self.assertIn("spec/live-shipped", ws["ini-001"]["work"]["shipped"])
        # Active list untouched
        self.assertIn("spec/live-shipped", ws["ini-001"]["work"]["active"])

    def test_repair_apply_round_trip(self) -> None:
        """AC20c: end-to-end repair-plan → repair-apply pipeline."""
        root, _ = self._make_repair_fixture()
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        r_apply = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r_apply.returncode, 0)
        data = json.loads(r_apply.stdout)
        self.assertGreater(data["operations_applied"], 0)

    def test_repair_apply_missing_shipped_key_created(self) -> None:
        """AC13: initiative with no shipped key → key created; path appended."""
        no_shipped_toml = """\
["ini-001"]
name      = "No Shipped Key"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/new-shipped"]
active  = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(no_shipped_toml)
        self._make_spec(root, "new-shipped", "Shipped")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        shipped = ws["ini-001"]["work"].get("shipped", [])
        self.assertIn("spec/new-shipped", shipped)

    def test_repair_apply_queue_remove_archived_inline_object(self) -> None:
        """AC13/AC17: Archived entry as inline object removed in place."""
        inline_archived_toml = """\
["ini-001"]
name      = "Inline Archived"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "spec/inline-archived", needs = "work:spec/other"}, "spec/keep"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(inline_archived_toml)
        self._make_spec(root, "inline-archived", "Archived")
        self._make_spec(root, "keep", "Approved")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        queue = ws["ini-001"]["work"]["queue"]
        paths = [e if isinstance(e, str) else e.get("path", "") for e in queue]
        self.assertNotIn("spec/inline-archived", paths)
        self.assertIn("spec/keep", paths)
        shipped = ws["ini-001"]["work"].get("shipped", [])
        self.assertNotIn("spec/inline-archived", shipped)

    def test_repair_apply_confirmation_required(self) -> None:
        """AC13: missing --yes → exit 2, reason:confirmation_required."""
        root, _ = self._make_repair_fixture()
        r = _run_cli("repair-apply", "--root", str(root))
        self.assertEqual(r.returncode, 2)
        data = json.loads(r.stdout)
        self.assertFalse(data["applied"])
        self.assertEqual(data["reason"], "confirmation_required")

    def test_repair_apply_plan_id_invalid(self) -> None:
        """AC10: tampered operation in plan → plan_id_invalid."""
        root, plan_file = self._make_repair_fixture()
        plan_data = json.loads(plan_file.read_text(encoding="utf-8"))
        # Tamper with an operation (change a field)
        if plan_data.get("automatic_operations"):
            plan_data["automatic_operations"][0]["ini_slug"] = "ini-tampered"
        plan_file.write_text(json.dumps(plan_data), encoding="utf-8")
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 2)
        data = json.loads(r.stdout)
        self.assertFalse(data["applied"])
        self.assertEqual(data["reason"], "plan_id_invalid")

    def test_repair_apply_before_after_digest(self) -> None:
        """AC18: successful apply includes before_workspace_digest and after_workspace_digest."""
        import hashlib
        root, _ = self._make_repair_fixture()
        before = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["before_workspace_digest"], before,
                         "before_workspace_digest must match pre-apply hash")
        after = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        self.assertEqual(data["after_workspace_digest"], after,
                         "after_workspace_digest must match post-apply hash")
        self.assertNotEqual(before, after, "workspace must have changed")


class TomlkitUnavailableTests(_CliBase):
    """AC16b: repair-apply exits 2 with tomlkit_unavailable when tomlkit import fails."""

    def test_repair_apply_tomlkit_unavailable(self) -> None:
        """AC16b: subprocess with tomlkit shadowed by ImportError stub → exit 2."""
        import os
        import subprocess
        import sys
        import tempfile as _tmp

        root = self._write_workspace(_REPAIR_TOML)
        self._make_spec(root, "shipped-feature", "Shipped")
        self._make_spec(root, "archived-feature", "Archived")
        # Generate a valid plan first (tomlkit not needed for repair-plan)
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)

        # Build a stub directory that shadows tomlkit with a module raising ImportError
        with _tmp.TemporaryDirectory() as stub_dir:
            stub_tomlkit = Path(stub_dir) / "tomlkit.py"
            stub_tomlkit.write_text(
                "raise ImportError('tomlkit stubbed out for testing')\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            # Prepend stub dir to PYTHONPATH so the stub shadows the real tomlkit
            env["PYTHONPATH"] = stub_dir + os.pathsep + env.get("PYTHONPATH", "")

            cli_path = Path(__file__).parent.parent
            script = (
                cli_path
                / "packs/core/.apm/skills/workspace-status/scripts/workspace_status.py"
            )
            result = subprocess.run(
                [sys.executable, str(script), "repair-apply", "--root", str(root), "--yes"],
                capture_output=True,
                text=True,
                env=env,
            )

        self.assertEqual(
            result.returncode, 2,
            f"expected exit 2, got {result.returncode}: {result.stderr}",
        )
        import json as _json
        data = _json.loads(result.stdout)
        self.assertEqual(data.get("reason"), "tomlkit_unavailable")
        self.assertFalse(data.get("applied"))


if __name__ == "__main__":
    unittest.main()
