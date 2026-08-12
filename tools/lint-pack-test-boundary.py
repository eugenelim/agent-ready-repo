#!/usr/bin/env python3
"""Asserts the runtime export boundary holds for every pack in the catalogue.

`.apm/` is what gets projected into an installed agent environment, so nothing
that is not runtime content may live there. That rule survived for a long time
only because the installer happens to read `seeds/` and `.apm/` and ignore
everything else — an implicit exclusion, not a structural one. This lint makes
it structural: it fails when a test file appears under any pack's `.apm/`, and
when one appears in a projected skill.

Checking the projection *positively* is the point. Inferring "no tests are
installed" from "the installer ignores those paths" is exactly the reasoning
that let the violation persist; a future adapter that copies `.apm/**` wholesale
would break the inference without breaking any test.

Cross-pack behaviour is not pack-owned (`catalogue-authoring-standards.md` § 4),
which is why this lives in `tools/` rather than in one pack's test tree.

`evals/` is deliberately not flagged: eval fixtures are skill-local runtime
content and are projected with the skill by design.

Six checks:

1. **apm-carries-no-tests** — no pack's `.apm/` holds test content.
2. **projection-carries-no-tests** — no projected skill does either, asserted
   per pack against the self-host recipe's include list so a pack dropping out
   of the projection fails rather than passing on an empty iteration.
3. **tests-live-in-the-pack-tree** — a pack that owns tests has them under
   `packs/<pack>/tests/`.
4. **runners-keep-suites-isolated** — no single pytest invocation covers two
   skill test directories. Suite-local imports can bind a sibling skill's
   same-named subject module and pass green, even when test basenames differ.
5. **every-suite-dir-has-a-runner** — every skill test directory is named by a
   runner or declared in `_NO_RUNNER` with a reason. Without this, "which suites
   actually run" has no living home and the next directory is unrun by default.
6. **pack-tests-stay-in-pack** — Python pack tests may inspect their owning pack
   and temporary fixtures, but may not climb to the repository root and inspect
   another source tree.
"""

from __future__ import annotations

import ast
import os
import re
import subprocess
import sys
import tomllib
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import NamedTuple

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "packs"
if not PACKS.is_dir():                      # wrong parents[] depth after a move
    raise SystemExit(f"packs/ not found at {PACKS} — check the parents[] depth")

RECIPE = (ROOT / "packages" / "agentbundle" / "agentbundle" / "build"
          / "recipes" / "self-host.toml")

# The shapes a test actually takes, across the languages this catalogue can grow
# into. Deliberately a superset of what the tree holds today: a matcher tuned to
# the current contents proves nothing about the next pack.
#
# Deliberate narrowings, each for a reason:
#   - no bare `test` substring — `test-fixtures.md` as reference material for a
#     skill *about* testing would be a false positive;
#   - `evals/` is runtime-adjacent by decision (ADR-0071) and is skipped;
#   - gitignored build residue is not authored content.
_TEST_FILE = re.compile(
    r"^(conftest\.py"
    r"|.+\.(test|spec)\.(py|sh|js|ts|tsx|mjs|cjs|go|ps1|rb)"
    r"|.+[-_]test\.(py|sh|js|ts|tsx|mjs|cjs|go|ps1|rb)"
    r"|test[-_].+\.(py|sh|js|ts|tsx|mjs|cjs|go|ps1|rb))$"
)
_TEST_DIR = frozenset({"tests", "test", "__tests__", "spec"})
_SKIP_DIR = frozenset({"evals"})

# `__pycache__` and friends are gitignored build residue, not authored content,
# so they are not a boundary violation. They were also a packaging problem —
# `package.py` walked `packs/**` and collected them — fixed in agentbundle
# 0.29.5, which prunes the same shapes from both archive flavours.
_TRANSIENT = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache",
                        ".ruff_cache", "node_modules"})

FAILURES: list[str] = []


class _ParentsPath(NamedTuple):
    """A ``Path.parents`` sequence that retains its ``__file__`` origin."""

    path: Path


class _UnresolvedPath(NamedTuple):
    """A source-derived path whose final location cannot be proved local."""

    path: Path


class _StringValues(NamedTuple):
    """Literal or proven-confined filename values; empty means a safe glob."""

    values: tuple[str, ...]


class _PathConstructor(NamedTuple):
    """An alias of pathlib.Path."""

    name: str


_PathValue = (
    Path | _ParentsPath | _UnresolvedPath | _StringValues | _PathConstructor | None
)


def _is_linked_dir(path: Path) -> bool:
    """Whether a directory entry redirects the walk to another tree."""
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def _walk(base: Path) -> list[Path]:
    """Authored test content under *base*.

    Uses `os.walk(followlinks=False)` with an explicit symlink prune, matching
    `catalogue_tooling/package.py`'s archive walk. The lint and the walker that
    decides what actually ships must not hold two different definitions of what
    pack content is — and `Path.rglob`'s symlink behaviour changed across the
    3.12/3.13 boundary.
    """
    found: list[Path] = []
    if not base.is_dir() or _is_linked_dir(base):
        return found
    for dirpath, dirnames, filenames in os.walk(str(base), followlinks=False):
        dp = Path(dirpath)
        dirnames[:] = [
            dn for dn in dirnames
            if dn not in _TRANSIENT and dn not in _SKIP_DIR
            and not _is_linked_dir(dp / dn)
        ]
        for dn in dirnames:
            if dn in _TEST_DIR:
                found.append(dp / dn)
        for fn in filenames:
            p = dp / fn
            if _TEST_FILE.match(fn) and not p.is_symlink():
                found.append(p)
    return [p for p in found if not _is_ignored(p)]


def _is_ignored(path: Path) -> bool:
    """A locally-generated, gitignored file is not a boundary violation."""
    try:
        return subprocess.run(
            ["git", "check-ignore", "-q", "--", str(path)],
            cwd=ROOT, capture_output=True, check=False,
        ).returncode == 0
    except FileNotFoundError:
        return False  # no git available — judge every file on disk


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def _packs() -> list[Path]:
    return sorted(p for p in PACKS.iterdir()
                  if p.is_dir() and not p.name.startswith("_")
                  and (p / "pack.toml").is_file())


def _projected_packs() -> list[str]:
    """Packs this repo projects, per the self-host recipe's include list.

    Only these can be checked by the projection half; the rest are advertised
    through `marketplace.json` but never written into this tree.
    """
    if not RECIPE.is_file():
        FAILURES.append(f"self-host recipe not found at {_rel(RECIPE)}")
        return []
    data = tomllib.loads(RECIPE.read_text(encoding="utf-8"))
    return list(data.get("recipe", {}).get("packs", {}).get("include", []))


def case_apm_carries_no_tests() -> None:
    packs = _packs()
    if not packs:
        FAILURES.append("no packs found under packs/ — this must not pass "
                        "vacuously")
        return
    hits: list[Path] = []
    for pack in packs:
        hits += _walk(pack / ".apm")
    if hits:
        FAILURES.append(
            "a pack's .apm/ is the runtime export boundary but carries test "
            "content:\n    " + "\n    ".join(_rel(h) for h in hits)
            + "\n  Move it to packs/<pack>/tests/ — see "
              "catalogue-authoring-standards.md § 4."
        )
        return
    print(f"ok   [apm-carries-no-tests] ({len(packs)} packs)")


def case_projection_carries_no_tests() -> None:
    """The installed artifact, checked directly rather than inferred."""
    before = len(FAILURES)
    include = _projected_packs()
    if not include:
        FAILURES.append("self-host recipe lists no packs to project")
        return
    adapter_roots = [r for r in (ROOT / ".claude" / "skills",
                                 ROOT / ".agents" / "skills") if r.is_dir()]
    if not adapter_roots:
        FAILURES.append(
            "no projected skills tree found under .claude/skills or "
            ".agents/skills — run `make build-self`; this check must not pass "
            "vacuously"
        )
        return
    hits: list[Path] = []
    total = 0
    for name in include:
        skills_dir = PACKS / name / ".apm" / "skills"
        if not skills_dir.is_dir():
            continue
        skills = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())
        checked = 0
        for adapter_root in adapter_roots:
            for skill in skills:
                projected = adapter_root / skill
                if projected.is_dir():
                    checked += 1
                    hits += _walk(projected)
        if not checked:
            FAILURES.append(
                f"pack {name!r} is in the self-host include list but none of its "
                f"skills is projected — a pack dropping out of the projection "
                f"must fail here, not pass on an empty iteration"
            )
        total += checked
    if hits:
        FAILURES.append(
            f"projected skills carry test content ({total} checked):\n    "
            + "\n    ".join(_rel(h) for h in hits)
        )
        return
    if len(FAILURES) == before:
        print(f"ok   [projection-carries-no-tests] ({total} projected skills, "
              f"{len(include)} packs)")


def case_tests_live_in_the_pack_tree() -> None:
    """The positive half — a pack that owns tests has them where policy says."""
    before = len(FAILURES)
    owning = 0
    packs = _packs()
    if not packs:
        FAILURES.append("no packs found under packs/ — this must not pass "
                        "vacuously")
        return
    for pack in packs:
        tests = pack / "tests"
        if not tests.is_dir():
            continue                      # a pack may legitimately own no tests
        suites = _walk(tests)
        if not suites:
            FAILURES.append(
                f"{_rel(tests)} exists but holds no test content — an empty "
                f"test tree is a lost move, not a clean pack"
            )
            continue
        owning += 1
    if len(FAILURES) == before:
        print(f"ok   [tests-live-in-the-pack-tree] ({owning} packs own tests)")


def _path_value(
    node: ast.AST,
    test_file: Path,
    names: dict[str, _PathValue],
    path_names: set[str],
    path_modules: set[str],
) -> _PathValue:
    """Resolve source paths built from ``__file__`` without executing a test."""
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return test_file
        if node.id in path_names:
            return _PathConstructor(node.id)
        return names.get(node.id)
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "Path"
        and isinstance(node.value, ast.Name)
        and node.value.id in path_modules
    ):
        return _PathConstructor(ast.unparse(node))
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _StringValues((node.value,))
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        strings = tuple(
            item.value
            for item in node.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
        return _StringValues(strings) if len(strings) == len(node.elts) else None
    if isinstance(node, ast.GeneratorExp) and node.generators:
        return _path_value(
            node.generators[0].iter,
            test_file,
            names,
            path_names,
            path_modules,
        )
    if isinstance(node, ast.Call):
        called = _path_value(node.func, test_file, names, path_names, path_modules)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "cwd"
            and isinstance(
                _path_value(
                    node.func.value,
                    test_file,
                    names,
                    path_names,
                    path_modules,
                ),
                _PathConstructor,
            )
        ) or (
            (isinstance(node.func, ast.Attribute) and node.func.attr == "getcwd")
            or (isinstance(node.func, ast.Name) and node.func.id == "getcwd")
        ):
            return _UnresolvedPath(test_file)
        is_path_call = (
            isinstance(node.func, ast.Name) and node.func.id in path_names
        ) or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "Path"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in path_modules
        ) or isinstance(called, _PathConstructor)
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in {"list", "set", "sorted", "tuple"}
            and len(node.args) == 1
        ):
            return _path_value(
                node.args[0], test_file, names, path_names, path_modules
            )
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"abspath", "realpath"}
            and len(node.args) == 1
        ):
            value = _path_value(
                node.args[0], test_file, names, path_names, path_modules
            )
            return value if isinstance(value, (Path, _UnresolvedPath)) else None
        if node.args and is_path_call:
            values = [
                _path_value(
                    argument, test_file, names, path_names, path_modules
                )
                for argument in node.args
            ]
            source = next(
                (
                    value.path if isinstance(value, _UnresolvedPath) else value
                    for value in values
                    if isinstance(value, (Path, _UnresolvedPath))
                ),
                None,
            )
            if source is None:
                return None
            parts: list[Path | str] = []
            for value in values:
                if isinstance(value, Path):
                    parts.append(value)
                elif isinstance(value, _StringValues):
                    if any(_unsafe_path_segment(part) for part in value.values):
                        return _UnresolvedPath(source)
                    if value.values:
                        parts.append(value.values[0])
                else:
                    return _UnresolvedPath(source)
            return Path(*parts)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "joinpath":
            value = _path_value(
                node.func.value, test_file, names, path_names, path_modules
            )
            if isinstance(value, _UnresolvedPath):
                return value
            if not isinstance(value, Path):
                return None
            parts: list[str] = []
            for argument in node.args:
                part = _path_value(
                    argument, test_file, names, path_names, path_modules
                )
                if not isinstance(part, _StringValues):
                    return _UnresolvedPath(value)
                if any(_unsafe_path_segment(item) for item in part.values):
                    return _UnresolvedPath(value)
                if part.values:
                    parts.append(part.values[0])
            return value.joinpath(*parts)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"glob", "rglob"}
        ):
            value = _path_value(
                node.func.value, test_file, names, path_names, path_modules
            )
            if isinstance(value, _UnresolvedPath):
                return value
            if not isinstance(value, Path):
                return None
            if (
                len(node.args) != 1
                or not isinstance(node.args[0], ast.Constant)
                or not isinstance(node.args[0].value, str)
            ):
                return _UnresolvedPath(value)
            if _unsafe_path_segment(node.args[0].value):
                return _UnresolvedPath(value)
            if not _glob_tree_is_confined(value):
                return _UnresolvedPath(value)
            return _StringValues(())
        if (
            not node.args
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"absolute", "resolve"}
        ):
            return _path_value(
                node.func.value, test_file, names, path_names, path_modules
            )
        return None
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        value = _path_value(node.value, test_file, names, path_names, path_modules)
        return value.parent if isinstance(value, Path) else None
    if isinstance(node, ast.Attribute) and node.attr == "parents":
        value = _path_value(
            node.value, test_file, names, path_names, path_modules
        )
        return _ParentsPath(value) if isinstance(value, Path) else None
    if isinstance(node, ast.Subscript):
        value = _path_value(node.value, test_file, names, path_names, path_modules)
        index = _integer_literal(node.slice)
        if isinstance(value, _ParentsPath) and isinstance(index, int):
            try:
                return value.path.parents[index]
            except IndexError:
                return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        value = _path_value(node.left, test_file, names, path_names, path_modules)
        if isinstance(value, _UnresolvedPath):
            return value
        right = _path_value(
            node.right, test_file, names, path_names, path_modules
        )
        if isinstance(value, Path) and isinstance(right, _StringValues):
            if any(_unsafe_path_segment(part) for part in right.values):
                return _UnresolvedPath(value)
            return value / right.values[0] if right.values else value
        if isinstance(value, Path):
            return _UnresolvedPath(value)
    return None


def _unsafe_path_segment(value: str) -> bool:
    """Whether one literal can reset or traverse a path on POSIX or Windows."""
    for path in (PurePosixPath(value), PureWindowsPath(value)):
        if path.drive or path.root or ".." in path.parts:
            return True
    return False


def _glob_tree_is_confined(base: Path) -> bool:
    """Prove a glob base cannot redirect traversal outside itself."""
    if _is_linked_dir(base):
        return False
    try:
        resolved_base = base.resolve()
    except (OSError, RuntimeError):
        return False
    if not base.is_dir():
        return True
    for dirpath, dirnames, filenames in os.walk(str(base), followlinks=False):
        directory = Path(dirpath)
        kept_dirs: list[str] = []
        for name in dirnames:
            child = directory / name
            if _is_linked_dir(child):
                return False
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in filenames:
            child = directory / name
            if child.is_symlink():
                return False
            try:
                resolved_child = child.resolve()
            except (OSError, RuntimeError):
                return False
            if (
                resolved_child != resolved_base
                and resolved_base not in resolved_child.parents
            ):
                return False
    return True


def _integer_literal(node: ast.AST) -> int | None:
    """Return a signed integer literal without executing its expression."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.UAdd, ast.USub))
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, int)
    ):
        return (
            node.operand.value
            if isinstance(node.op, ast.UAdd)
            else -node.operand.value
        )
    return None


class _PackTestPathVisitor(ast.NodeVisitor):
    """Find checkout paths while respecting Python's lexical name scopes."""

    def __init__(self, test_file: Path, pack: Path, tree: ast.AST) -> None:
        self._test_file = test_file
        self._resolved_pack = pack.resolve()
        self._name_scopes: list[dict[str, _PathValue]] = [{}]
        self._path_names = {"Path"}
        self._path_modules = {"pathlib"}
        self._hits: list[tuple[int, str]] = []
        self._seen: set[tuple[int, int]] = set()
        self._node_stack: list[ast.AST] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "pathlib":
                self._path_names.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name == "Path"
                )
            elif isinstance(node, ast.Import):
                self._path_modules.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name == "pathlib"
                )

    @property
    def hits(self) -> list[tuple[int, str]]:
        return sorted(set(self._hits))

    def _names(self) -> dict[str, _PathValue]:
        names: dict[str, _PathValue] = {}
        for scope in self._name_scopes:
            names.update(scope)
        return names

    def _value(self, node: ast.AST) -> _PathValue:
        return _path_value(
            node,
            self._test_file,
            self._names(),
            self._path_names,
            self._path_modules,
        )

    def _record(self, node: ast.AST) -> None:
        value = self._value(node)
        if isinstance(value, _UnresolvedPath):
            self._add_hit(node)
            return
        if isinstance(value, (_StringValues, _PathConstructor)):
            return
        if isinstance(value, _ParentsPath):
            parent = self._node_stack[-1] if self._node_stack else None
            is_subscript_source = (
                isinstance(parent, ast.Subscript) and parent.value is node
            )
            is_alias_source = (
                isinstance(parent, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
                and parent.value is node
            )
            if not is_subscript_source and not is_alias_source:
                self._add_hit(node)
            return
        if value is None:
            if (
                isinstance(node, ast.Subscript)
                and isinstance(self._value(node.value), _ParentsPath)
            ):
                self._add_hit(node)
            return
        try:
            resolved_value = value.resolve()
        except (OSError, RuntimeError):
            self._add_hit(node)
            return
        if (
            resolved_value == self._resolved_pack
            or self._resolved_pack in resolved_value.parents
        ):
            return
        self._add_hit(node)

    def _add_hit(self, node: ast.AST) -> None:
        key = (getattr(node, "lineno", 1), getattr(node, "col_offset", 0))
        if key not in self._seen:
            self._seen.add(key)
            self._hits.append((key[0], ast.unparse(node)))

    def visit(self, node: ast.AST) -> None:
        self._record(node)
        self._node_stack.append(node)
        try:
            super().visit(node)
        finally:
            self._node_stack.pop()

    def _bind(self, target: ast.AST, value: _PathValue) -> None:
        if isinstance(target, ast.Name):
            self._name_scopes[-1][target.id] = value

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        value = self._value(node.value)
        for target in node.targets:
            self._bind(target, value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
            self._bind(node.target, self._value(node.value))

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.visit(node.value)
        self._bind(node.target, self._value(node.value))

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._bind(node.target, self._value(node.iter))
        for statement in (*node.body, *node.orelse):
            self.visit(statement)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit_For(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)
        if node.returns is not None:
            self.visit(node.returns)
        parameter_values: dict[str, _PathValue] = {}
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "parametrize"
                and len(decorator.args) >= 2
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
                and "," not in decorator.args[0].value
            ):
                value = self._value(decorator.args[1])
                if isinstance(value, _StringValues):
                    parameter_values[decorator.args[0].value] = value
        self._name_scopes.append(parameter_values)
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self._name_scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for expression in (*node.decorator_list, *node.bases, *node.keywords):
            self.visit(expression)
        self._name_scopes.append({})
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self._name_scopes.pop()


def _pack_test_escapes(test_file: Path, source: str) -> list[tuple[int, str]]:
    """Return ``(line, expression)`` pairs that climb above the owning pack."""
    try:
        tree = ast.parse(source, filename=str(test_file))
    except SyntaxError as exc:
        return [(exc.lineno or 1, f"unparseable Python: {exc.msg}")]
    pack = next(
        (parent for parent in test_file.parents if parent.parent == PACKS),
        None,
    )
    if pack is None:
        return [(1, "test is not below packs/<pack>/")]

    visitor = _PackTestPathVisitor(test_file, pack, tree)
    visitor.visit(tree)
    hits = visitor.hits

    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)):
            values = node.elts
        elif isinstance(node, ast.Call):
            values = node.args
        else:
            continue
        strings = {
            item.value
            for item in values
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        }
        if {"rev-parse", "--show-toplevel"}.issubset(strings):
            hits.append((node.lineno, ast.unparse(node)))
    return sorted(set(hits))


def case_pack_tests_stay_in_pack() -> None:
    """Pack tests may inspect only their owning pack and temporary fixtures."""
    before = len(FAILURES)
    checked = 0
    for pack in _packs():
        tests = pack / "tests"
        if _is_linked_dir(tests):
            FAILURES.append(
                f"{_rel(tests)}: pack test root is linked — linked test "
                "sources are not inspected"
            )
            continue
        if not tests.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(str(tests), followlinks=False):
            directory = Path(dirpath)
            kept_dirs: list[str] = []
            for name in dirnames:
                child = directory / name
                if name in _TRANSIENT:
                    continue
                if _is_linked_dir(child):
                    FAILURES.append(
                        f"{_rel(child)}: pack test tree contains a linked "
                        "directory — linked test sources are not inspected"
                    )
                    continue
                kept_dirs.append(name)
            dirnames[:] = kept_dirs
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                test_file = directory / name
                if test_file.is_symlink():
                    FAILURES.append(
                        f"{_rel(test_file)}: pack test is a symlink — linked "
                        "test sources are not inspected"
                    )
                    continue
                checked += 1
                source = test_file.read_text(encoding="utf-8", errors="replace")
                for lineno, expression in _pack_test_escapes(test_file, source):
                    FAILURES.append(
                        f"{_rel(test_file)}:{lineno}: pack test reaches above "
                        f"{_rel(pack)} via `{expression}` — move repository-level "
                        "coverage to tests/conformance or tests/roster, or anchor "
                        "pack-local coverage directly at its owning pack"
                    )
    if len(FAILURES) == before:
        print(f"ok   [pack-tests-stay-in-pack] ({checked} Python files checked)")


# Runner call sites: one invocation per line is close enough, because every
# runner in this repo puts one pytest command on one line.
_RUNNER_FILES = (
    "Makefile",
    ".github/workflows/build-check.yml",
    ".github/workflows/catalogue-tooling-ci-gates.yml",
    ".github/workflows/docs.yml",
    "tools/test-all.py",
    "packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py",
)
# Two shapes, because runners write paths two ways. A shell/Make/argv form
# (`packs/converters/tests/skills/x`), possibly with a `*` in the pack segment;
# and `self_host_windows.py`'s `root / "packs" / "atlassian" / "tests" / …`
# Path-part sequence, which no substring match can see — the spec records that
# same fact about grepping it.
_DEST = re.compile(r"packs/[A-Za-z0-9_*-]+/tests(?:/[A-Za-z0-9_.*/-]*)?")
_DEST_PARTS = re.compile(
    r'"packs"\s*/\s*"([A-Za-z0-9_-]+)"\s*/\s*"tests"((?:\s*/\s*"[A-Za-z0-9_-]+")*)'
)
_PART = re.compile(r'"([A-Za-z0-9_-]+)"')
_PYTEST = re.compile(r"(?:^|[\s\"'])pytest(?:$|[\s\"'])")

# Directories with no runner, and why. A destination directory must either be
# named by a runner or appear here — that is what keeps "which suites actually
# run" answerable from the tree rather than from a frozen spec note. Removing an
# entry whose directory is gone is part of deleting the suite.
_NO_RUNNER = {
    "packs/architect/tests/skills/architect-diagram":
        "needs the Mermaid CLI (mmdc); never gated",
    "packs/atlassian/tests/skills/confluence-publisher": "never gated",
    "packs/atlassian/tests/skills/jira-align": "never gated",
    "packs/atlassian/tests/skills/jira-team-status":
        "run by tools/check-atlassian-phase3-readiness.py, which no workflow invokes",
    "packs/converters/tests/skills/render-proof":
        "no CI exists for pack-level JavaScript; see pack-js-ci-workflow",
    "packs/figma/tests/skills/figma": "never gated",
    "packs/governance-extras/tests/skills/new-adr": "never gated",
    "packs/governance-extras/tests/skills/new-rfc": "never gated",
}


def _destinations() -> list[Path]:
    """Every skill test directory that holds a suite."""
    out: list[Path] = []
    for pack in _packs():
        skills = pack / "tests" / "skills"
        if not skills.is_dir():
            continue
        for d in sorted(skills.iterdir()):
            if d.is_dir() and _walk(d):
                out.append(d)
    return out


def _test_basenames(d: Path) -> set[str]:
    """Test module basenames in *d*.

    `conftest.py` is excluded deliberately: one per directory is pytest's design
    and every destination has one, so including it would make every multi-
    directory invocation look like a collision for a reason that is not true.
    """
    return {p.name for p in _walk(d)
            if p.is_file() and p.name != "conftest.py"}


def _covered(line_paths: set[str], destinations: list[Path]) -> set[Path]:
    """Destination directories a set of matched path tokens covers.

    A token may be a glob (`packs/*/tests/`) or an ancestor
    (`packs/converters/tests/`); either way it covers every destination beneath
    it, which is exactly how one invocation ends up spanning several skills.
    """
    covered: set[Path] = set()
    for token in line_paths:
        for d in destinations:
            rel = str(d.relative_to(ROOT))
            if fnmatch(rel, token.rstrip("/")) or fnmatch(rel, token.rstrip("/") + "/*") \
               or rel.startswith(token.rstrip("/") + "/") or rel == token.rstrip("/"):
                covered.add(d)
    return covered


def _path_tokens(text: str) -> set[str]:
    """Pack-test paths named by one command or structured invocation."""
    tokens = set(_DEST.findall(text))
    normalized = text.replace("'", '"')
    for pack, tail in _DEST_PARTS.findall(normalized):
        parts = _PART.findall(tail)
        tokens.add("/".join(["packs", pack, "tests", *parts]))
    return tokens


def _workflow_runner_lines(
    rel: str,
    source: str,
) -> list[tuple[str, int, set[str]]]:
    """Pytest commands in a workflow, paired with their step working directory."""
    out: list[tuple[str, int, set[str]]] = []
    working_tokens: set[str] = set()
    lines = source.splitlines()
    pytest_helpers: set[str] = set()
    for index, line in enumerate(lines):
        definition = re.match(r"^\s*([A-Za-z_]\w*)\(\)\s*\(", line)
        if definition is None:
            continue
        indent = len(line) - len(line.lstrip())
        body: list[str] = []
        for candidate in lines[index + 1:]:
            if candidate.strip() == ")" and len(candidate) - len(candidate.lstrip()) == indent:
                break
            body.append(candidate)
        if any(_PYTEST.search(candidate) for candidate in body):
            pytest_helpers.add(definition.group(1))

    for lineno, line in enumerate(lines, 1):
        if re.match(r"^\s*-\s+name:", line):
            working_tokens = set()
        if re.match(r"^\s*working-directory:", line):
            working_tokens = _path_tokens(line)
        stripped = line.lstrip()
        helper_call = next(
            (name for name in pytest_helpers if stripped.startswith(name + " ")),
            None,
        )
        if not stripped.startswith("#") and (
            _PYTEST.search(line) or helper_call is not None
        ):
            tokens = _path_tokens(line) | working_tokens
            if tokens:
                out.append((rel, lineno, tokens))
    return out


def _python_runner_lines(
    rel: str,
    source: str,
) -> list[tuple[str, int, set[str]]]:
    """Structured Python argv lists whose enclosing call record invokes pytest."""
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as exc:
        FAILURES.append(f"runner file {rel} is not parseable: {exc}")
        return []
    out: list[tuple[str, int, set[str]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Tuple):
            continue
        command_lists = [item for item in node.elts if isinstance(item, ast.List)]
        if not any(
            any(
                isinstance(item, ast.Constant) and item.value == "pytest"
                for item in command.elts
            )
            for command in command_lists
        ):
            continue
        tokens = _path_tokens(ast.unparse(node))
        if tokens:
            out.append((rel, node.lineno, tokens))
    return out


def _runner_lines() -> list[tuple[str, int, set[str]]]:
    """(file, lineno, matched path tokens) for every pytest invocation."""
    out: list[tuple[str, int, set[str]]] = []
    for rel in _RUNNER_FILES:
        f = ROOT / rel
        if not f.is_file():
            FAILURES.append(
                f"runner file {rel} does not exist — the collision and coverage "
                f"checks silently stop reading it; update _RUNNER_FILES"
            )
            continue
        source = f.read_text(encoding="utf-8", errors="replace")
        if f.suffix in {".yml", ".yaml"}:
            out.extend(_workflow_runner_lines(rel, source))
            continue
        if f.suffix == ".py":
            out.extend(_python_runner_lines(rel, source))
            continue
        for lineno, line in enumerate(source.splitlines(), 1):
            if line.lstrip().startswith("#") or not _PYTEST.search(line):
                continue
            if tokens := _path_tokens(line):
                out.append((rel, lineno, tokens))
    return out


def case_runners_keep_suites_isolated() -> None:
    """One pytest process per skill test directory — a correctness requirement.

    Overlapping basenames *across* destination directories are expected, and a
    newly added collision must not be what finally makes a broad runner fail.
    The assertion is therefore about invocation shape, not today's filenames.
    """
    before = len(FAILURES)
    destinations = _destinations()
    checked = 0
    for rel, lineno, tokens in _runner_lines():
        covered = sorted(_covered(tokens, destinations))
        if len(covered) < 2:
            continue
        checked += 1
        FAILURES.append(
            f"{rel}:{lineno}: one pytest invocation covers multiple skill "
            f"suites {[str(_rel(path)) for path in covered]} — split it into "
            "one process per skill directory before a test or subject module "
            "collision can pass green"
        )
    if len(FAILURES) == before:
        print(f"ok   [runners-keep-suites-isolated] "
              f"({checked} multi-directory invocation(s) checked)")


def case_every_suite_dir_has_a_runner() -> None:
    """Every destination is named by a runner, or declared unrun with a reason.

    Without this the answer to "which suites actually run" lives only in a spec
    note, which freezes when the spec ships — so the next pack's test directory
    is unrun by default and nothing says so.
    """
    before = len(FAILURES)
    destinations = _destinations()
    if not destinations:
        FAILURES.append("no skill test directories found — this must not pass "
                        "vacuously")
        return
    run: set[Path] = set()
    for _, _, tokens in _runner_lines():
        run |= _covered(tokens, destinations)
    for d in destinations:
        rel = str(d.relative_to(ROOT))
        if d in run:
            if rel in _NO_RUNNER:
                FAILURES.append(
                    f"{rel} is declared unrun in _NO_RUNNER but a runner names "
                    f"it — drop the entry"
                )
            continue
        if rel not in _NO_RUNNER:
            FAILURES.append(
                f"{rel} holds a suite that no runner names. Wire it, or add it "
                f"to _NO_RUNNER with the reason — a suite nobody runs must be "
                f"declared, not discovered."
            )
    live = {str(d.relative_to(ROOT)) for d in destinations}
    for rel in sorted(set(_NO_RUNNER) - live):
        FAILURES.append(
            f"_NO_RUNNER names {rel}, which holds no suite — a stale exemption "
            f"hides the next directory that goes missing"
        )
    if len(FAILURES) == before:
        print(f"ok   [every-suite-dir-has-a-runner] "
              f"({len(destinations)} destinations, {len(_NO_RUNNER)} declared unrun)")


def main() -> int:
    for case in (case_apm_carries_no_tests,
                 case_projection_carries_no_tests,
                 case_tests_live_in_the_pack_tree,
                 case_pack_tests_stay_in_pack,
                 case_runners_keep_suites_isolated,
                 case_every_suite_dir_has_a_runner):
        case()
    print()
    if FAILURES:
        for f in FAILURES:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"✖ lint-pack-test-boundary: {len(FAILURES)} failure(s)",
              file=sys.stderr)
        return 1
    print("✓ lint-pack-test-boundary: passed (6 cases).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
