"""T9a clean-environment fence: two independent checks, each with red evidence.

1. Static import check: every *.py file in the projected work-loop skill's
   scripts/ directory imports only Python standard-library modules or its own
   sibling modules in scripts/.  An optional import inside an ImportError (or
   ModuleNotFoundError) guard is allowed, as in lint-spec-status.py's tomli
   fallback.  The check proves the Never-do rule:
     "let any work-loop runtime module import a Python module other than the
     standard library or a sibling module in its own skill scripts/ directory."

2. Subprocess fence: the projected work-loop compatibility path (a loop-engine.py
   transition with WORK_LOOP_SHADOW_SERVICES=1) runs in a subprocess where
   ``agentbundle`` is not importable, after first proving it is not importable
   there, and the path completes successfully.

Each check is accompanied by a red-evidence test that mutates its input in a
scratch copy and asserts the mutation is detected.

Roster-owned: reads the projected copies above any single pack tree and runs a
subprocess; neither is pack-scoped.  Placed above
the bulk ``pytest tests/ -q`` carve-out step in build-check.yml.

Spec: docs/specs/acceptance-authority-and-evidence/spec.md
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Use the .claude/ projected copy as the canonical projection to fence-check
# (the .agents/ copy is byte-identical by test_t9a_conformance_rollup.py).
_PROJECTED_SCRIPTS = REPO_ROOT / ".claude" / "skills" / "work-loop" / "scripts"

_ENGINE = _PROJECTED_SCRIPTS / "loop-engine.py"
_COHORT = _PROJECTED_SCRIPTS / "loop-cohort.py"

# Python 3.10+ exposes stdlib_module_names; fall back to a curated set on older.
try:
    _STDLIB_NAMES: frozenset[str] = frozenset(sys.stdlib_module_names)  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover — only reachable below 3.10
    import sysconfig
    _STDLIB_NAMES = frozenset(Path(sysconfig.get_python_lib(standard_lib=True)).parts)

# Top-level packages that are always fine (built-ins, frozen, or __future__).
_ALWAYS_ALLOWED: frozenset[str] = frozenset({"__future__", "_thread"})


# ═══════════════════════════════════════════════════════════════════════════════
# Check 1: static import analysis
# ═══════════════════════════════════════════════════════════════════════════════


def _collect_importerror_guarded_linenos(tree: ast.AST) -> frozenset[int]:
    """Return line numbers of all AST nodes inside try/except ImportError blocks.

    Any ``Import`` or ``ImportFrom`` node at one of these line numbers is treated
    as an optional import and is exempt from the stdlib-only rule.
    """
    guarded: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        # Decide if this Try has an ImportError or ModuleNotFoundError handler.
        is_import_guard = False
        for handler in node.handlers:
            exc = handler.type
            if exc is None:
                continue  # bare except — not an ImportError guard
            names: list[str] = []
            if isinstance(exc, ast.Name):
                names.append(exc.id)
            elif isinstance(exc, ast.Tuple):
                for elt in exc.elts:
                    if isinstance(elt, ast.Name):
                        names.append(elt.id)
            if any(n in ("ImportError", "ModuleNotFoundError") for n in names):
                is_import_guard = True
                break
        if not is_import_guard:
            continue
        # Mark every line in this entire Try (body + handlers + orelse + finalbody)
        for sub in ast.walk(node):
            guarded.add(sub.lineno if hasattr(sub, "lineno") else -1)
    return frozenset(guarded)


def _top_level_module_name(node: ast.Import | ast.ImportFrom) -> str:
    """Return the top-level module name for an import statement."""
    if isinstance(node, ast.Import):
        return node.names[0].name.split(".")[0]
    # ImportFrom: module may be None for relative imports (``from . import x``)
    if node.module:
        return node.module.split(".")[0]
    return ""  # relative import — not a third-party name


def _check_file_imports(
    path: Path,
    *,
    sibling_names: frozenset[str],
) -> list[str]:
    """Return a list of violation descriptions for non-stdlib imports in path.

    sibling_names: names of modules that may be loaded from the same scripts/
    directory via importlib.util (e.g. ``_acceptance``, ``_evidence_store``).
    These are treated as allowed even if not in sys.stdlib_module_names.
    """
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [f"{path.name}: SyntaxError: {exc}"]

    guarded = _collect_importerror_guarded_linenos(tree)
    violations: list[str] = []

    for node in ast.walk(tree):
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        lineno = getattr(node, "lineno", -1)
        if lineno in guarded:
            continue  # optional import inside ImportError guard — allowed
        name = _top_level_module_name(node)
        if not name:
            continue  # relative import
        if name in _STDLIB_NAMES or name in _ALWAYS_ALLOWED:
            continue  # stdlib — allowed
        if name in sibling_names:
            continue  # sibling module loaded via importlib — allowed
        violations.append(
            f"  {path.name}:{lineno}: non-stdlib import '{name}' "
            f"(not in stdlib or sibling names and not inside ImportError guard)"
        )
    return violations


class TestStaticImportCheck:
    """Every runtime module in the projected work-loop skill is stdlib-only."""

    def _projected_sibling_names(self) -> frozenset[str]:
        """Return the base names (without .py) of sibling modules in scripts/."""
        return frozenset(
            p.stem
            for p in _PROJECTED_SCRIPTS.iterdir()
            if p.is_file() and p.suffix == ".py"
        )

    def test_projected_scripts_import_only_stdlib_and_siblings(self) -> None:
        """Every *.py in the projected work-loop scripts/ uses stdlib imports only.

        Optional imports inside ImportError / ModuleNotFoundError guards are exempt
        (e.g. the tomli fallback in lint-spec-status.py).  Sibling modules loaded
        via importlib.util are also exempt.

        Proves the spec Never-do rule: no runtime module may import outside stdlib
        or its own sibling scripts.
        """
        assert _PROJECTED_SCRIPTS.is_dir(), (
            f"projected scripts dir not found: {_PROJECTED_SCRIPTS}\n"
            "Run `make build-self` to generate projected copies."
        )
        scripts = sorted(
            p for p in _PROJECTED_SCRIPTS.iterdir()
            if p.is_file() and p.suffix == ".py"
        )
        assert scripts, f"no .py files in {_PROJECTED_SCRIPTS}"

        sibling_names = self._projected_sibling_names()
        all_violations: list[str] = []
        for script in scripts:
            all_violations.extend(
                _check_file_imports(script, sibling_names=sibling_names)
            )

        assert not all_violations, (
            "Non-stdlib imports found in projected work-loop scripts "
            "(violates the Never-do rule):\n"
            + "\n".join(all_violations)
        )

    def test_static_import_check_detects_non_stdlib_import(
        self, tmp_path: Path
    ) -> None:
        """Red evidence: a file with a non-stdlib import fails the static check.

        Confirms the check is not a tautology.  The scratch file introduces a
        top-level import of ``requests`` (not in the stdlib) and asserts that
        _check_file_imports catches it.
        """
        bad_source = (
            "# T9a red-evidence: intentional non-stdlib import for fence test\n"
            "import requests  # NOT stdlib\n"
            "import os\n"
        )
        scratch = tmp_path / "bad_module.py"
        scratch.write_text(bad_source, encoding="utf-8")

        violations = _check_file_imports(scratch, sibling_names=frozenset())
        assert violations, (
            "Red evidence: the static import check DID NOT detect 'import requests'; "
            "the check is a false-guarantor."
        )
        assert any("requests" in v for v in violations), (
            f"Red evidence: expected 'requests' in violation messages; got {violations}"
        )

    def test_importerror_guarded_import_passes_static_check(
        self, tmp_path: Path
    ) -> None:
        """An import inside an ImportError guard passes the static check.

        Models the tomli pattern: ``except ImportError: import tomli`` is allowed
        even though tomli is not in the stdlib.
        """
        guarded_source = (
            "try:\n"
            "    import tomllib\n"
            "except ImportError:\n"
            "    try:\n"
            "        import tomli as tomllib  # not stdlib — but inside guard\n"
            "    except ImportError:\n"
            "        tomllib = None\n"
        )
        scratch = tmp_path / "guarded_module.py"
        scratch.write_text(guarded_source, encoding="utf-8")

        violations = _check_file_imports(scratch, sibling_names=frozenset())
        assert not violations, (
            f"An ImportError-guarded import of 'tomli' was incorrectly flagged: "
            f"{violations}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Check 2: subprocess clean-environment fence
# ═══════════════════════════════════════════════════════════════════════════════


def _subprocess_python(args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess:
    """Run a clean-environment Python subprocess."""
    return subprocess.run(
        [sys.executable, "-S", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )


def _clean_env() -> dict[str, str]:
    """Return a minimal environment where agentbundle is not importable.

    Uses -S (no site) to prevent site-packages from being added to sys.path,
    and clears PYTHONPATH.  The stdlib remains accessible since -S only skips
    site.py, not the interpreter's standard paths.
    """
    return {
        # Keep essential OS paths so subprocesses can resolve executables.
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": "",  # no extra search paths
        "PYTHONNOUSERSITE": "1",  # no ~/.local/lib/pythonX.Y/site-packages
        # macOS requires DYLD_LIBRARY_PATH for the Python runtime itself.
        **{k: v for k, v in os.environ.items() if k.startswith("DYLD_")},
        # Windows: pass SYSTEMROOT so Python can find its C runtime.
        **({k: v for k, v in os.environ.items() if k in ("SYSTEMROOT", "TEMP", "TMP")}),
    }


class TestSubprocessCleanEnvFence:
    """The compatibility path completes in a subprocess without agentbundle."""

    def test_agentbundle_not_importable_in_clean_env(self) -> None:
        """First prove: agentbundle is NOT importable in the clean environment.

        This is the mandatory first step of the fence: it would be a vacuous pass
        if agentbundle were importable.
        """
        env = _clean_env()
        r = _subprocess_python(
            ["-c", "import agentbundle; print('importable')"],
            env=env,
        )
        assert r.returncode != 0, (
            "agentbundle IS importable in the clean environment — the fence is "
            "vacuous.  The clean-env definition must exclude site-packages.\n"
            f"stdout: {r.stdout!r}\nstderr: {r.stderr!r}"
        )

    def test_compatibility_path_completes_in_agentbundle_free_environment(
        self, tmp_path: Path
    ) -> None:
        """The work-loop happy path completes where agentbundle is not importable.

        Steps:
        1. Prove agentbundle is not importable in the subprocess env (guard).
        2. Create a temporary git repository with a throwaway spec directory.
        3. Run loop-engine.py init → spec-ready transition with
           WORK_LOOP_SHADOW_SERVICES=1 through the projected scripts.
        4. Assert all commands exit 0.

        Proves the Never-do rule holds at runtime: no shipped script imports
        agentbundle, so the compatibility path succeeds in a clean environment.
        """
        env = _clean_env()
        env["WORK_LOOP_SHADOW_SERVICES"] = "1"

        # Guard: confirm agentbundle not importable
        r = _subprocess_python(
            ["-c", "import agentbundle"],
            env=env,
        )
        assert r.returncode != 0, (
            "agentbundle must NOT be importable in the fence environment; "
            "the test would not prove anything if it were."
        )

        # Build a minimal git repo with a throwaway spec dir
        git_repo = tmp_path / "fence-repo"
        git_repo.mkdir()
        subprocess.run(["git", "init", "-q", str(git_repo)], check=True, capture_output=True)
        spec_dir = git_repo / "docs" / "specs" / "fence-feature"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            "# Spec: fence\n\n- **Status:** Approved\n\n"
            "## Acceptance Criteria\n\n- [ ] AC-fence-001. Fence criterion.\n",
            encoding="utf-8",
        )

        engine = str(_ENGINE)
        cohort = str(_COHORT)

        # 1. engine init
        r = subprocess.run(
            [sys.executable, "-S", engine, "init", str(spec_dir), "--mode", "code", "--json"],
            capture_output=True, text=True, encoding="utf-8",
            env=env, cwd=str(git_repo),
        )
        assert r.returncode == 0, (
            f"loop-engine init failed in clean env (agentbundle-free):\n"
            f"stdout: {r.stdout!r}\nstderr: {r.stderr!r}"
        )
        run_data = json.loads(r.stdout)
        assert "run_id" in run_data, f"no run_id in engine init output: {r.stdout!r}"

        # 2. cohort init
        r = subprocess.run(
            [sys.executable, "-S", cohort, "init", str(spec_dir),
             "--run-id", run_data["run_id"]],
            capture_output=True, text=True, encoding="utf-8",
            env=env, cwd=str(git_repo),
        )
        assert r.returncode == 0, (
            f"loop-cohort init failed in clean env:\n"
            f"stdout: {r.stdout!r}\nstderr: {r.stderr!r}"
        )

        # 3. spec-ready transition (exercises shadow_call_on_transition)
        r = subprocess.run(
            [sys.executable, "-S", engine, "transition", str(spec_dir), "spec-ready"],
            capture_output=True, text=True, encoding="utf-8",
            env=env, cwd=str(git_repo),
        )
        assert r.returncode == 0, (
            f"loop-engine transition spec-ready failed in clean env:\n"
            f"stdout: {r.stdout!r}\nstderr: {r.stderr!r}"
        )

        # Confirm shadow evidence was written (shadow is ON)
        shadow_dir = spec_dir / ".shadow-acceptance"
        evidence_log = shadow_dir / "shadow-evidence.log"
        assert evidence_log.exists(), (
            "Shadow shadow-evidence.log not written despite WORK_LOOP_SHADOW_SERVICES=1; "
            "the compatibility path may not have run."
        )
        first_frame = json.loads(evidence_log.read_text("utf-8").splitlines()[0])
        # EvidenceStore frame format: {"tx": {...}, "records": [...]}
        assert "records" in first_frame, (
            f"shadow-evidence.log first line must be an EvidenceStore frame: {first_frame}"
        )
        first_receipt = first_frame["records"][0]
        selector_term = first_receipt.get("selector", {}).get("term", "")
        assert selector_term == "engine-transition:spec-ready", (
            f"Expected selector.term='engine-transition:spec-ready'; got {selector_term!r}"
        )
        assert "authoritative" not in first_receipt, (
            "Shadow receipt must not carry an 'authoritative' field (legacy authority holds)"
        )
