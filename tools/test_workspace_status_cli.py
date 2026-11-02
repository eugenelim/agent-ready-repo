#!/usr/bin/env python3
"""CLI contract tests for scripts/workspace_status.py — Order 1A.

Tests the installed production CLI, not a copy of the engine.
The CLI lives at:
  packs/core/.apm/skills/workspace-status/scripts/workspace_status.py

All invocations use sys.executable and list-form subprocess calls.
Never shell=True. Tests are independent of the source checkout CWD.
"""

from __future__ import annotations

import hashlib
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
_REPO_BACKLOG_FIXTURES = (
    _REPO_ROOT / "packs/core/tests/skills/workspace-status"
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
# The shipped entry keeps a need the repair refuses, so it is no `spec-entry-drop`
# candidate and still gets its `queue-to-shipped` operation.
_REPAIR_TOML = """\
["ini-001"]
name      = "Repair Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "docs/specs/shipped-feature/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Structured shipped feature", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}, "spec/archived-feature"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""

_REPO_BACKLOG_ISOLATION_TOML = """\
["ini-001"]
name      = "Isolation Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue = [
  "spec/ready",
  {path = "spec/blocked", needs = "work:spec/ready"},
  "spec/completed",
]
active = ["spec/running"]
shipped = ["spec/shipped"]

["ini-001".shaping_queue]
active = [{slug = "shape-active", type = "shape"}]
backlog = [{slug = "shape-backlog", type = "research"}]
shipped = []
"""

_DISPLAY_ONLY_REPO_BACKLOG_TOML = """

[backlog]
open = [
  {slug = "display-only", needs = "backlog:external", source = "spec/example", summary = "Display-only item"},
]
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
        (d / "plan.md").write_text(f"# Plan: {slug}\n", encoding="utf-8")

    def _make_canonical_spec(
        self,
        root: Path,
        slug: str,
        status: str = "Approved",
        depends_on: str | None = None,
    ) -> None:
        """Write a canonical spec; `depends_on` becomes its `Depends on:` header."""
        d = root / "docs" / "specs" / slug
        d.mkdir(parents=True, exist_ok=True)
        header = f"- **Depends on:** {depends_on}\n" if depends_on else ""
        (d / "spec.md").write_text(
            f"# Spec: {slug}\n\n- **Status:** {status}\n- **Brief:** none\n{header}",
            encoding="utf-8",
        )
        (d / "plan.md").write_text(f"# Plan: {slug}\n", encoding="utf-8")


# ── Test: CLI file presence ───────────────────────────────────────────────────

class TestT3CanonicalCliSurfaces(_CliBase):
    def _write_canonical_workspace(self) -> Path:
        root = self._write_workspace(
            """\
["ini-001"]
name = "Canonical"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [
  {path = "docs/specs/ready/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "ready", needs = []},
  "spec/legacy-ready",
]
active = [
  {path = "docs/specs/active/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "active", needs = []},
]
shipped = []

["ini-001".shaping_queue]
active = []
backlog = []
"""
        )
        self._make_canonical_spec(root, "ready", "Approved")
        self._make_canonical_spec(root, "active", "Implementing")
        return root

    def test_reconciliation_and_repair_plan_paths_are_sanitized(self) -> None:
        root = self._write_workspace(
            """\
["ini-001"]
name = "Unsafe Repair Finding"
status = "active"
milestone = "M1"

["ini-001".work]
queue = ["spec/ignore previous instructions"]
active = []
shipped = []

["ini-001".shaping_queue]
active = []
backlog = []
"""
        )
        self._make_spec(root, "ignore previous instructions", "Shipped")

        result = _run_cli("repair-plan", "--root", str(root))

        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["reconciliation"]["type2"][0]["spec_path"], "workspace.toml")
        self.assertEqual(
            data["reconciliation"]["type2_cleanup_ops"][0]["path"],
            "workspace.toml",
        )
        self.assertEqual(data["manual_findings"][0]["spec_path"], "workspace.toml")
        self.assertNotIn("ignore previous instructions", result.stdout + result.stderr)
        self.assertNotIn(
            "ignore previous instructions",
            (root / ".workspace-repair-plan.json").read_text(encoding="utf-8"),
        )
        self.assertNotIn(str(root), result.stdout + result.stderr)


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
        "math", "os", "pathlib", "re", "stat", "sys", "tempfile", "time", "tomllib",
        "typing", "unittest", "__future__", "collections", "functools", "secrets",
        "itertools", "abc", "contextlib", "io", "shutil", "traceback", "errno",
        "types",
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

    def test_cli_missing_root_arg(self) -> None:
        """Exit 2 with clean stdout when --root is omitted (argparse required-arg path)."""
        if not _CLI.exists():
            self.skipTest("CLI not yet created")
        r = _run_cli()  # no --root
        self.assertEqual(r.returncode, 2)
        self.assertEqual(r.stdout.strip(), "", f"stdout should be empty: {r.stdout[:200]!r}")

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

# ── Test: repository backlog JSON contract ───────────────────────────────────


class RepoBacklogContractTests(_CliBase):
    def _fixture_root(self, name: str) -> Path:
        fixture = _REPO_BACKLOG_FIXTURES / f"repo_backlog_{name}.toml"
        shutil.copyfile(fixture, self.tmp / "workspace.toml")
        return self.tmp

    def _run_mode(self, mode: str, root: Path) -> dict:
        result = _run_cli(mode, "--root", str(root))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def _populated_root(self) -> Path:
        root = self._write_workspace(_REPO_BACKLOG_ISOLATION_TOML)
        self._make_spec(root, "ready", "Approved")
        self._make_spec(root, "blocked", "Approved")
        self._make_spec(root, "completed", "Shipped")
        self._make_spec(root, "running", "Implementing")
        self._make_spec(root, "shipped", "Shipped")
        return root

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

    def test_skill_no_quickfull(self) -> None:
        """AC15: No quick/full mode flags."""
        text = self._skill_text()
        self.assertNotIn("--quick", text)
        self.assertNotIn("--full", text)

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

_TWO_INI_CANONICAL_SHARED_TOML = """\
["ini-001"]
name      = "Alpha"
status    = "active"
milestone = "M1"

["ini-001".work]
active  = []
shipped = []
queue   = [{path = "docs/specs/shared-canonical/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Shared canonical", needs = []}]

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
queue   = [{path = "docs/specs/shared-canonical/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Shared canonical", needs = []}]

["ini-002".shaping_queue]
active  = []
backlog = []
"""


class RepairOnlyArgumentVectorTests(_CliBase):
    """The CLI keeps `repair-plan` and `repair-apply`; every other first argument exits 2."""

    _RETIRED = {
        "status": "work-loop dispatch.py",
        "reconcile": "work-loop dispatch.py",
        "explain": "work-loop dispatch.py",
        "selected-membership": "work-loop dispatch.py",
        "prune": "no replacement",
        "retirement-candidates": "no replacement",
        "repair-rollback": "no replacement",
    }

    def _snapshot(self) -> dict[str, bytes]:
        return {
            str(p.relative_to(self.tmp)): p.read_bytes()
            for p in sorted(self.tmp.rglob("*")) if p.is_file()
        }

    def _assert_refused(self, args: list[str]) -> subprocess.CompletedProcess:
        root = self._write_workspace(_MINIMAL_TOML)
        before = self._snapshot()
        r = _run_cli(*args, "--root", str(root))
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertEqual(r.stdout, "")
        self.assertEqual(before, self._snapshot(), "the tree changed")
        return r

    def test_each_retired_subcommand_names_itself_and_its_replacement(self) -> None:
        for name, replacement in self._RETIRED.items():
            with self.subTest(subcommand=name):
                r = self._assert_refused([name])
                self.assertTrue(
                    r.stderr.startswith(f"retired_subcommand: {name}"), r.stderr
                )
                self.assertIn(replacement, r.stderr)

    def test_retired_subcommand_exits_before_loading_the_engine(self) -> None:
        root = self._write_workspace(_MINIMAL_TOML)
        scripts = self.tmp / "scripts"
        scripts.mkdir()
        shutil.copy2(_CLI, scripts / _CLI.name)
        r = subprocess.run(
            [sys.executable, str(scripts / _CLI.name), "status", "--root", str(root)],
            capture_output=True, text=True, encoding="utf-8",
        )
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertTrue(r.stderr.startswith("retired_subcommand: status"), r.stderr)

    def test_a_bare_call_and_any_other_first_argument_exit_2(self) -> None:
        for args in ([], ["unknown-word"], ["--root", "."]):
            with self.subTest(args=args):
                r = _run_cli(*args)
                self.assertEqual(r.returncode, 2, r.stderr)
                self.assertEqual(r.stdout, "")
                self.assertIn("repair-plan", r.stderr)
                self.assertIn("repair-apply", r.stderr)

    def test_each_migration_form_exits_2_and_writes_nothing(self) -> None:
        forms = [
            ["repair-plan", "--migration-selection", "selection.json"],
            ["repair-apply", "--migration-selection", "selection.json"],
            ["repair-apply", "--operation-id", "migration-" + "a" * 64],
            ["repair-apply", "--confirmation-file", "confirmation.json"],
        ]
        for form in forms:
            with self.subTest(form=form):
                self._assert_refused(form)


class RepoWithoutMigrationReadersTests(unittest.TestCase):
    """No skill or package script reads a migration authorization table or ledger."""

    def test_no_script_reads_the_migration_table_or_ledger(self) -> None:
        roots = (
            _REPO_ROOT / "packs/core/.apm/skills",
            _REPO_ROOT / "packages/agentbundle/agentbundle",
        )
        needles = ("authorization.migration", ".workspace-migrations.json")
        offenders = [
            f"{path.relative_to(_REPO_ROOT)}: {needle}"
            for root in roots
            for path in root.rglob("*.py")
            for needle in needles
            if needle in path.read_text(encoding="utf-8", errors="replace")
        ]
        self.assertEqual(offenders, [])


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
        root = self._make_repair_fixture()
        before = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        r = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r.returncode, 0)
        after = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        self.assertEqual(before, after, "repair-plan must not modify workspace.toml")

    def test_repair_plan_stdout_emitted_on_plan_file_write_failure(self) -> None:
        """AC26: stdout emitted even if plan file write fails; exit 2 on failure."""
        root = self._make_repair_fixture()
        # Use a regular file where the plan file's parent directory would be.
        # mkstemp(dir=<regular-file>) raises NotADirectoryError on every platform
        # and even when running as root, unlike chmod-based permission removal.
        not_a_dir = root / "not-a-dir"
        not_a_dir.write_text("regular file, not a directory")
        custom = not_a_dir / "plan.json"
        r = _run_cli("repair-plan", "--root", str(root), "--plan-file", str(custom))
        self.assertEqual(r.returncode, 2, "must exit 2 on write failure")
        # stdout must still be valid JSON (plan emitted before file write)
        data = json.loads(r.stdout)
        self.assertEqual(data["mode"], "repair-plan")

    def test_repair_plan_plan_file_confinement(self) -> None:
        """AC16d: --plan-file via symlink → exit 2 (is_symlink guard fires before confinement)."""
        root = self._make_repair_fixture()
        import tempfile as _tmp
        with _tmp.TemporaryDirectory() as outside:
            link = root / "escape-link.json"
            Path(str(link)).symlink_to(str(Path(outside) / "escape.json"))
            r = _run_cli("repair-plan", "--root", str(root), "--plan-file", str(link))
            self.assertEqual(r.returncode, 2)
            data = json.loads(r.stdout)
            # is_symlink() guard fires before confinement for repair-plan write path
            self.assertEqual(data.get("reason"), "plan_file_is_symlink")
            self.assertFalse(data.get("applied"), "symlink guard must carry applied:false")

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

    @unittest.skipIf(sys.platform == "win32", "symlink needs elevated privs on Windows")
    def test_repair_plan_plan_file_is_symlink(self) -> None:
        """AC16d write-path: in-root symlink → exit 2, plan_file_is_symlink; target intact."""
        root = self._make_repair_fixture()
        # Create an in-root file that a symlink could clobber
        innocent = root / "innocent.toml"
        innocent.write_text("# must not be clobbered\n", encoding="utf-8")
        # Create a symlink pointing at that in-root file
        link = root / "plan-link.json"
        link.symlink_to(innocent)
        r = _run_cli("repair-plan", "--root", str(root), "--plan-file", str(link))
        self.assertEqual(r.returncode, 2)
        data = json.loads(r.stdout)
        self.assertEqual(data.get("reason"), "plan_file_is_symlink")
        self.assertFalse(data.get("applied"))
        # The in-root target must not have been overwritten
        self.assertEqual(innocent.read_text(encoding="utf-8"), "# must not be clobbered\n")


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

    def test_repair_plan_queue_to_shipped_bare_string_is_manual(self) -> None:
        """T4: bare legacy shipped entries are not automatic repair operations."""
        bare_toml = """\
["ini-001"]
name      = "Bare Repair"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/shipped-feature"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(bare_toml)
        self._make_spec(root, "shipped-feature", "Shipped")
        r = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r.returncode, 0, f"exit: {r.stderr}")
        data = json.loads(r.stdout)
        auto_paths = {op["spec_path"] for op in data["automatic_operations"]}
        manual = {
            (finding["spec_path"], finding["reason"])
            for finding in data["manual_findings"]
        }
        self.assertNotIn("spec/shipped-feature", auto_paths)
        self.assertIn(("spec/shipped-feature", "type2-queue-structured-entry-required"), manual)

    def test_repair_apply_queue_remove_archived(self) -> None:
        """AC13: archived entry removed from queue; structured Shipped entry is moved."""
        root, _ = self._make_repair_fixture()
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        queue = ws["ini-001"]["work"]["queue"]
        self.assertNotIn("spec/archived-feature", queue)
        shipped_paths = [
            e.get("path", "") if isinstance(e, dict) else e
            for e in ws["ini-001"]["work"]["shipped"]
        ]
        self.assertEqual(shipped_paths, ["docs/specs/shipped-feature/spec.md"])

    def test_repair_apply_queue_to_shipped_inline_object(self) -> None:
        """AC13/AC17: inline object entry removed in place; other entries intact."""
        inline_toml = """\
["ini-001"]
name      = "Inline Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "docs/specs/inline-shipped/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Keep structured context", needs = [{type = "local", kind = "spec", path = "docs/specs/other/spec.md"}]}, "spec/keep-me"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(inline_toml)
        self._make_spec(root, "inline-shipped", "Shipped")
        self._make_spec(root, "other", "Shipped")
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
        self.assertNotIn("docs/specs/inline-shipped/spec.md", paths_in_queue)
        self.assertIn("spec/keep-me", paths_in_queue)
        # The same plan migrates the entry's typed `needs` to the waiting item, which
        # empties them, so the entry is dropped rather than moved to shipped.
        self.assertEqual(ws["ini-001"]["work"]["shipped"], [])
        self.assertIn(
            "- **Depends on:** spec:other",
            (root / "docs/specs/inline-shipped/spec.md").read_text(encoding="utf-8"),
        )

    def test_repair_apply_revalidates_spec_status_before_replace(self) -> None:
        """Security: spec status/fingerprint drift before replace aborts the whole write."""
        import importlib.util

        root = self._write_workspace(
            """\
["ini-001"]
name      = "Race Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "docs/specs/racy/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Racy", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        )
        self._make_spec(root, "racy", "Shipped")
        workspace_path = root / "workspace.toml"
        before = workspace_path.read_bytes()
        spec_file = root / "docs" / "specs" / "racy" / "spec.md"
        status_line = next(
            line for line in spec_file.read_text(encoding="utf-8").splitlines()
            if line.startswith("- **Status:**")
        )
        op = {
            "operation_type": "queue-to-shipped",
            "spec_path": "docs/specs/racy/spec.md",
            "spec_status": "Shipped",
            "ini_slug": "ini-001",
            "finding_id": "type2:ini-001:queue:docs/specs/racy/spec.md",
            "operation_id": "cc" * 32,
            "spec_status_fingerprint": hashlib.sha256(
                status_line.encode("utf-8")
            ).hexdigest(),
        }

        spec = importlib.util.spec_from_file_location("workspace_status_cli_race", _CLI)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        sys.modules.setdefault("workspace_status_cli_race", mod)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        self.assertTrue(mod._bind_engine())
        real_reader = mod.extract_spec_status_with_fingerprint
        reads = 0

        def racing_reader(path: Path) -> tuple[str | None, str | None]:
            nonlocal reads
            reads += 1
            if reads == 2:
                path.write_text(
                    "# Spec: racy\n\n- **Status:** Approved\n",
                    encoding="utf-8",
                )
            return real_reader(path)

        mod.extract_spec_status_with_fingerprint = racing_reader

        with self.assertRaisesRegex(RuntimeError, "workspace_concurrent_write"):
            mod._apply_operations(root, [op], before, workspace_path)

        self.assertEqual(workspace_path.read_bytes(), before)
        self.assertEqual(list(root.glob(".workspace.toml.*.tmp")), [])

    def test_repair_apply_revalidates_canonical_eligibility_before_replace(self) -> None:
        """Security: canonical eligibility drift before replace aborts the whole write."""
        import importlib.util

        root = self._write_workspace(
            """\
["ini-001"]
name      = "Eligibility Race"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "docs/specs/racy-eligibility/spec.md", kind = "spec", source = {mode = "repo-origin", parent = "docs/product/briefs/right.md"}, summary = "Racy eligibility", needs = []}]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        )
        spec_dir = root / "docs" / "specs" / "racy-eligibility"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "spec.md"
        spec_file.write_text(
            "# Spec: racy eligibility\n\n"
            "- **Status:** Shipped\n"
            "- **Brief:** docs/product/briefs/right.md\n",
            encoding="utf-8",
        )
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        brief_dir = root / "docs" / "product" / "briefs"
        brief_dir.mkdir(parents=True)
        (brief_dir / "right.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        (brief_dir / "wrong.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        workspace_path = root / "workspace.toml"
        before = workspace_path.read_bytes()
        status_line = next(
            line for line in spec_file.read_text(encoding="utf-8").splitlines()
            if line.startswith("- **Status:**")
        )
        op = {
            "operation_type": "queue-to-shipped",
            "spec_path": "docs/specs/racy-eligibility/spec.md",
            "spec_status": "Shipped",
            "ini_slug": "ini-001",
            "finding_id": "type2:ini-001:queue:docs/specs/racy-eligibility/spec.md",
            "operation_id": "dd" * 32,
            "spec_status_fingerprint": hashlib.sha256(
                status_line.encode("utf-8")
            ).hexdigest(),
        }

        spec = importlib.util.spec_from_file_location(
            "workspace_status_cli_eligibility_race", _CLI
        )
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        sys.modules["workspace_status_cli_eligibility_race"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        self.assertTrue(mod._bind_engine())
        real_eligibility = mod._repair_entry_eligibility
        eligibility_checks = 0

        def racing_eligibility(
            workspace_arg: Path,
            ini_arg: str,
            spec_path_arg: str,
            op_type_arg: str,
        ) -> tuple[bool, str | None]:
            nonlocal eligibility_checks
            eligibility_checks += 1
            if eligibility_checks == 2:
                spec_file.write_text(
                    "# Spec: racy eligibility\n\n"
                    "- **Status:** Shipped\n"
                    "- **Brief:** docs/product/briefs/wrong.md\n",
                    encoding="utf-8",
                )
            return real_eligibility(workspace_arg, ini_arg, spec_path_arg, op_type_arg)

        mod._repair_entry_eligibility = racing_eligibility

        with self.assertRaisesRegex(RuntimeError, "workspace_concurrent_write"):
            mod._apply_operations(root, [op], before, workspace_path)

        self.assertEqual(workspace_path.read_bytes(), before)
        self.assertEqual(list(root.glob(".workspace.toml.*.tmp")), [])

    def test_repair_apply_skips_if_provenance_changes_after_plan(self) -> None:
        root = self._write_workspace(
            """\
["ini-001"]
name      = "Provenance Drift"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "docs/specs/prov-drift/spec.md", kind = "spec", source = {mode = "repo-origin", parent = "docs/product/briefs/right.md"}, summary = "Provenance drift", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        )
        spec_dir = root / "docs" / "specs" / "prov-drift"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            "# Spec: provenance\n\n- **Status:** Shipped\n- **Brief:** docs/product/briefs/right.md\n",
            encoding="utf-8",
        )
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        brief_dir = root / "docs" / "product" / "briefs"
        brief_dir.mkdir(parents=True)
        (brief_dir / "right.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        (brief_dir / "wrong.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0, r_plan.stderr)
        self.assertEqual(
            [op["spec_path"] for op in json.loads(r_plan.stdout)["automatic_operations"]],
            ["docs/specs/prov-drift/spec.md"],
        )
        before = (root / "workspace.toml").read_bytes()
        (spec_dir / "spec.md").write_text(
            "# Spec: provenance\n\n- **Status:** Shipped\n- **Brief:** docs/product/briefs/wrong.md\n",
            encoding="utf-8",
        )

        r = _run_cli("repair-apply", "--root", str(root), "--yes")

        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["operations_applied"], 0)
        self.assertIn(
            ("docs/specs/prov-drift/spec.md", "canonical_repair_ineligible"),
            {(item["path"], item["reason"]) for item in data["per_operation"]},
        )
        self.assertEqual((root / "workspace.toml").read_bytes(), before)

    def test_repair_apply_skips_if_plan_disappears_after_plan(self) -> None:
        root = self._write_workspace(
            """\
["ini-001"]
name      = "Plan Drift"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "docs/specs/plan-drift/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Plan drift", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        )
        self._make_spec(root, "plan-drift", "Shipped")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0, r_plan.stderr)
        self.assertEqual(
            [op["spec_path"] for op in json.loads(r_plan.stdout)["automatic_operations"]],
            ["docs/specs/plan-drift/spec.md"],
        )
        before = (root / "workspace.toml").read_bytes()
        (root / "docs" / "specs" / "plan-drift" / "plan.md").unlink()

        r = _run_cli("repair-apply", "--root", str(root), "--yes")

        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["operations_applied"], 0)
        self.assertIn(
            ("docs/specs/plan-drift/spec.md", "canonical_repair_ineligible"),
            {(item["path"], item["reason"]) for item in data["per_operation"]},
        )
        self.assertEqual((root / "workspace.toml").read_bytes(), before)

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
            (
                p for p in data["per_operation"]
                if p["path"] == "docs/specs/shipped-feature/spec.md"
            ),
            None,
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
queue   = [{path = "docs/specs/feat-a/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Feature A", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]
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
queue   = [{path = "docs/specs/feat-b/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Feature B", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]
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
        """AC16d: --plan-file symlink resolving outside root → exit 2, plan_file_outside_root."""
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
queue   = [{path = "docs/specs/already-there/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Already there", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]
active  = []
shipped = [{path = "docs/specs/already-there/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Already there", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]

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
        shipped_paths = [e.get("path", "") if isinstance(e, dict) else e for e in shipped]
        self.assertEqual(
            shipped_paths.count("docs/specs/already-there/spec.md"),
            1,
            "must not duplicate",
        )

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
        """Tampered noncanonical operation fails before initiative lookup."""
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
            {"operation_type": "queue-to-shipped",
             "spec_path": "docs/specs/shipped-feature/spec.md",
             "spec_status": "Shipped", "ini_slug": "ini-nonexistent",
             "finding_id": "type2:ini-nonexistent:queue:docs/specs/shipped-feature/spec.md",
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
        self.assertEqual(data["operations_applied"], 0)
        reasons = {p["reason"] for p in data["per_operation"] if not p["applied"]}
        self.assertIn("canonical_repair_ineligible", reasons)
        # Guard: all-skipped write-suppression — workspace.toml must be byte-unchanged
        after = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        self.assertEqual(before, after, "all-skipped: workspace.toml must not be rewritten")
        self.assertEqual(list(root.glob(".workspace.toml.*.tmp")), [],
                         "all-skipped: no stray temp files")

    def test_repair_apply_entry_not_found_in_queue(self) -> None:
        """Tampered operation for unregistered queue path fails closed canonically."""
        root, plan_file = self._make_repair_fixture()
        before = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
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
            {"operation_type": "queue-to-shipped",
             "spec_path": "docs/specs/not-in-queue/spec.md",
             "spec_status": "Shipped", "ini_slug": "ini-001",
             "finding_id": "type2:ini-001:queue:docs/specs/not-in-queue/spec.md",
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
        self.assertEqual(data["operations_applied"], 0)
        reasons = {p["reason"] for p in data["per_operation"] if not p["applied"]}
        self.assertIn("canonical_repair_ineligible", reasons)
        after = hashlib.sha256((root / "workspace.toml").read_bytes()).hexdigest()
        self.assertEqual(before, after, "all-skipped: workspace.toml must not be rewritten")

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
        self._make_spec(root, "remove-me", "Archived")
        self._make_spec(root, "keep-me", "Approved")
        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0)
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        raw = (root / "workspace.toml").read_text(encoding="utf-8")
        self.assertIn("# keep this one", raw,
                      "inline comment on kept entry must survive removal")
        # spec/remove-me must be gone from queue (Archived entries are removed only).
        import tomllib as _tl
        ws = _tl.loads(raw)
        queue = ws["ini-001"]["work"]["queue"]
        queue_paths = [e if isinstance(e, str) else e.get("path", "") for e in queue]
        self.assertNotIn("spec/remove-me", queue_paths,
                         "removed entry must not remain in queue")
        self.assertIn("spec/keep-me", queue_paths, "kept entry must remain in queue")

    def test_repair_apply_duplicate_queue_active_stays_manual(self) -> None:
        """Duplicate queue+active membership blocks automatic repair."""
        dual_toml = """\
["ini-001"]
name      = "Dual-list Test"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "docs/specs/live-shipped/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Live shipped", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]
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
        self.assertEqual(plan_json["automatic_operations"], [])
        manual_reasons = {
            (f["spec_path"], f["reason"]) for f in plan_json["manual_findings"]
        }
        self.assertIn(
            ("docs/specs/live-shipped/spec.md", "type2-queue-canonical-blocked"),
            manual_reasons,
        )
        self.assertIn(("spec/live-shipped", "type2-active-source"), manual_reasons)

        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        data = json.loads(r.stdout)
        self.assertEqual(data["operations_applied"], 0)

        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        queue = ws["ini-001"]["work"]["queue"]
        queue_paths = [e if isinstance(e, str) else e.get("path", "") for e in queue]
        self.assertIn("docs/specs/live-shipped/spec.md", queue_paths)
        self.assertIn("spec/live-shipped", ws["ini-001"]["work"]["active"])
        self.assertEqual(ws["ini-001"]["work"]["shipped"], [])

    def test_repair_apply_bare_archived_duplicate_active_stays_manual(self) -> None:
        """Bare Archived queue cleanup is blocked when the same spec is active."""
        dual_toml = """\
["ini-001"]
name      = "Bare Archived Duplicate"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/archived-dupe"]
active  = ["docs/specs/archived-dupe/spec.md"]
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(dual_toml)
        self._make_spec(root, "archived-dupe", "Archived")
        before = (root / "workspace.toml").read_bytes()

        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0, r_plan.stderr)
        plan_json = json.loads(r_plan.stdout)
        self.assertEqual(plan_json["automatic_operations"], [])
        self.assertIn(
            ("spec/archived-dupe", "type2-queue-canonical-blocked"),
            {(f["spec_path"], f["reason"]) for f in plan_json["manual_findings"]},
        )

        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["operations_applied"], 0)
        self.assertEqual((root / "workspace.toml").read_bytes(), before)

        import tomllib

        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        self.assertIn("spec/archived-dupe", ws["ini-001"]["work"]["queue"])
        self.assertIn(
            "docs/specs/archived-dupe/spec.md",
            ws["ini-001"]["work"]["active"],
        )
        self.assertEqual(ws["ini-001"]["work"]["shipped"], [])

    def test_repair_apply_bare_archived_unsupported_string_stays_manual(self) -> None:
        """Unsupported bare queue strings are never auto-removed."""
        workspace_toml = """\
["ini-001"]
name      = "Unsupported Bare"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["foo"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(workspace_toml)
        self._make_spec(root, "foo", "Archived")
        before = (root / "workspace.toml").read_bytes()

        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0, r_plan.stderr)
        plan_json = json.loads(r_plan.stdout)
        self.assertEqual(plan_json["automatic_operations"], [])
        self.assertIn(
            ("foo", "type2-queue-canonical-blocked"),
            {(f["spec_path"], f["reason"]) for f in plan_json["manual_findings"]},
        )

        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["operations_applied"], 0)
        self.assertEqual((root / "workspace.toml").read_bytes(), before)

    def test_repair_apply_bare_archived_top_level_duplicate_stays_manual(self) -> None:
        """Accepted top-level legacy slug aliases block bare Archived cleanup."""
        workspace_toml = """\
[backlog]
open = [{slug = "top-archived", type = "spec", source = "repo-origin", summary = "Backlog alias", needs = []}]
closed = []

["ini-001"]
name      = "Top Duplicate"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/top-archived"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(workspace_toml)
        self._make_spec(root, "top-archived", "Archived")
        before = (root / "workspace.toml").read_bytes()

        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0, r_plan.stderr)
        plan_json = json.loads(r_plan.stdout)
        self.assertEqual(plan_json["automatic_operations"], [])
        self.assertIn(
            ("spec/top-archived", "type2-queue-canonical-blocked"),
            {(f["spec_path"], f["reason"]) for f in plan_json["manual_findings"]},
        )

        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["operations_applied"], 0)
        self.assertEqual((root / "workspace.toml").read_bytes(), before)

    def test_repair_apply_bare_archived_cross_initiative_duplicate_stays_manual(self) -> None:
        """Bare Archived cleanup is blocked by aliases in another initiative."""
        dual_toml = """\
["ini-001"]
name      = "Bare Archived Duplicate"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/cross-archived"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []

["ini-002"]
name      = "Other Initiative"
status    = "active"
milestone = "M2"

["ini-002".work]
queue   = []
active  = []
shipped = ["docs/specs/cross-archived/spec.md"]

["ini-002".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(dual_toml)
        self._make_spec(root, "cross-archived", "Archived")
        before = (root / "workspace.toml").read_bytes()

        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0, r_plan.stderr)
        plan_json = json.loads(r_plan.stdout)
        self.assertEqual(plan_json["automatic_operations"], [])
        self.assertIn(
            ("spec/cross-archived", "type2-queue-canonical-blocked"),
            {(f["spec_path"], f["reason"]) for f in plan_json["manual_findings"]},
        )

        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["operations_applied"], 0)
        self.assertEqual((root / "workspace.toml").read_bytes(), before)

    def test_repair_apply_bare_archived_second_queue_duplicate_stays_manual(self) -> None:
        """Bare Archived cleanup is blocked by a second queue alias."""
        dual_toml = """\
["ini-001"]
name      = "Bare Archived Duplicate"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = ["spec/queue-archived", "docs/specs/queue-archived/spec.md"]
active  = []
shipped = []

["ini-001".shaping_queue]
active  = []
backlog = []
"""
        root = self._write_workspace(dual_toml)
        self._make_spec(root, "queue-archived", "Archived")
        before = (root / "workspace.toml").read_bytes()

        r_plan = _run_cli("repair-plan", "--root", str(root))
        self.assertEqual(r_plan.returncode, 0, r_plan.stderr)
        plan_json = json.loads(r_plan.stdout)
        self.assertEqual(plan_json["automatic_operations"], [])
        self.assertIn(
            ("spec/queue-archived", "type2-queue-canonical-blocked"),
            {(f["spec_path"], f["reason"]) for f in plan_json["manual_findings"]},
        )

        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0, r.stderr)
        data = json.loads(r.stdout)
        self.assertEqual(data["operations_applied"], 0)
        self.assertEqual((root / "workspace.toml").read_bytes(), before)

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
        """AC13: initiative with no shipped key → key created; structured entry moved."""
        no_shipped_toml = """\
["ini-001"]
name      = "No Shipped Key"
status    = "active"
milestone = "M1"

["ini-001".work]
queue   = [{path = "docs/specs/new-shipped/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "New shipped", needs = [{type = "local", kind = "brief", path = "docs/product/briefs/absent.md"}]}]
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
        shipped_paths = [e.get("path", "") if isinstance(e, dict) else e for e in shipped]
        self.assertIn("docs/specs/new-shipped/spec.md", shipped_paths)

    def test_repair_apply_queue_remove_archived_inline_object(self) -> None:
        """Malformed archived inline objects stay manual and unchanged."""
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
        plan_data = json.loads(r_plan.stdout)
        self.assertEqual(plan_data["automatic_operations"], [])
        self.assertIn(
            ("spec/inline-archived", "type2-queue-canonical-blocked"),
            {
                (finding["spec_path"], finding["reason"])
                for finding in plan_data["manual_findings"]
            },
        )
        r = _run_cli("repair-apply", "--root", str(root), "--yes")
        self.assertEqual(r.returncode, 0)
        import tomllib
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        queue = ws["ini-001"]["work"]["queue"]
        paths = [e if isinstance(e, str) else e.get("path", "") for e in queue]
        self.assertIn("spec/inline-archived", paths)
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
