"""Typed compatibility declarations and fail-closed pack-test derivations.

This module deliberately has no dependency on ``lint-pack-test-boundary``: the
lint consumes this model, never the other way around.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompatibilityClass:
    """A proven set of suites that may share one pytest interpreter."""

    identifier: str
    pack: str
    members: tuple[str, ...]
    import_mode: str
    basename_resolution: str
    subject_imports: str
    rationale: str


#: Every entry below was characterised before it was declared: the isolated
#: node-ID union was compared against the grouped one, and the group was run
#: forward, in reverse member order, and across repeated fresh processes. A
#: class is a permission plus its evidence, never a standing exemption — the
#: checks in `lint-pack-test-boundary.py` re-derive its safety from source on
#: every run, so a member that stops being safe reddens the gate.
#:
#: Isolation is the default. Adding a suite directory does not add it to a
#: class; someone has to characterise it and declare it here.
CLASSES: tuple[CompatibilityClass, ...] = (
    CompatibilityClass(
        identifier="agent-skill-engineering-contract",
        pack="agent-skill-engineering",
        members=(
            "packs/agent-skill-engineering/tests/pack",
            "packs/agent-skill-engineering/tests/integration",
            "packs/agent-skill-engineering/tests/skills/author_or_update",
            "packs/agent-skill-engineering/tests/skills/review_or_optimize",
        ),
        import_mode="prepend",
        basename_resolution="packages",
        subject_imports="none",
        rationale=(
            "Both skill suites ship a test_contract.py, but their directories "
            "carry __init__.py with underscored names while tests/skills/ does "
            "not, so prepend mode already gives them distinct dotted module "
            "names — no import-mode flag needed. Every import across all four "
            "suites is stdlib or installed; no conftest, no sys.path mutation, "
            "no skill-local subject. 78 node IDs, identical isolated and "
            "grouped."
        ),
    ),
    CompatibilityClass(
        identifier="architect-contract",
        pack="architect",
        members=(
            "packs/architect/tests/pack",
            "packs/architect/tests/skills/architect-assess",
            "packs/architect/tests/skills/architect-design",
            "packs/architect/tests/skills/architect-review",
        ),
        import_mode="prepend",
        basename_resolution="none",
        subject_imports="explicit-qualified",
        rationale=(
            "No basename collides. The one subject load goes through a "
            "same-module helper called with the literal "
            "'architect_profile_repo_test', which resolves to a single path. "
            "71 node IDs, identical isolated and grouped."
        ),
    ),
    CompatibilityClass(
        identifier="converters-invocation-contract",
        pack="converters",
        members=(
            "packs/converters/tests/skills/markdown-to-html",
            "packs/converters/tests/skills/mermaid-renderer",
        ),
        import_mode="importlib",
        basename_resolution="import-mode",
        subject_imports="none",
        rationale=(
            "Both ship test_invocation_contract.py, which prepend mode refuses "
            "outright. importlib mode resolves the test-module half and nothing "
            "else — neither suite imports a skill-local subject, and neither "
            "has a conftest or a cross-test import that the mode would break. "
            "12 node IDs, identical isolated and grouped."
        ),
    ),
    CompatibilityClass(
        identifier="desk-research-content",
        pack="desk-research",
        members=(
            "packs/desk-research/tests/pack",
            "packs/desk-research/tests/skills/desk-research-project-check",
            "packs/desk-research/tests/skills/desk-research-project-digest",
            "packs/desk-research/tests/skills/desk-research-project-status",
            "packs/desk-research/tests/skills/desk-research-project-synthesize",
            "packs/desk-research/tests/skills/devils-advocate",
        ),
        import_mode="importlib",
        basename_resolution="import-mode",
        subject_imports="none",
        rationale=(
            "Seven suites in this pack ship test_project_knowledge_boundary.py; "
            "five of them are here, and prepend mode reports five collection "
            "errors. importlib mode resolves it. The two floor-bearing suites "
            "are deliberately absent: pytest_collection_floor counts len(items) "
            "session-wide and --collection-floor-suite is only a label, so a "
            "per-suite floor holds only while that suite is the sole target of "
            "its invocation. 17 node IDs, identical isolated and grouped."
        ),
    ),
    CompatibilityClass(
        identifier="linear-intake",
        pack="linear",
        members=(
            "packs/linear/tests/skills/linear",
            "packs/linear/tests/skills/linear-brief-intake",
        ),
        import_mode="prepend",
        basename_resolution="none",
        subject_imports="explicit-qualified",
        rationale=(
            "No basename collides. Two subject loads under the distinct "
            "literals 'linear_script' and 'linear_intake_adapter', each "
            "resolving to one path. 32 node IDs, identical isolated and "
            "grouped."
        ),
    ),
)

_EXCLUDED_DIRS = frozenset({".pytest_cache", "__pycache__", "fixtures", "testdata"})
_IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_IMPORT_MODES = frozenset({"prepend", "importlib"})
_BASENAME_RESOLUTIONS = frozenset({"none", "import-mode", "packages"})
_SUBJECT_IMPORTS = frozenset({"none", "explicit-qualified"})


def _is_linked_dir(path: Path) -> bool:
    """Whether a directory entry redirects the walk to another tree."""

    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def classes_by_identifier(
    classes: tuple[CompatibilityClass, ...] = CLASSES,
) -> tuple[CompatibilityClass, ...]:
    """Return *classes* in deterministic identifier order."""

    return tuple(sorted(classes, key=lambda item: item.identifier))


def _path(member: str | Path, root: Path) -> Path:
    """Resolve a repository-relative member path beneath *root*."""

    value = Path(member)
    return value if value.is_absolute() else root / value


def _relative(path: Path, root: Path) -> str:
    """Render *path* relative to *root* where possible."""

    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _under_excluded(path: Path, base: Path) -> bool:
    """Whether a non-imported fixture helper lies below an excluded tree."""

    relative = path.relative_to(base)
    if _is_test_file(path) or path.name == "conftest.py":
        return False
    return any(part in _EXCLUDED_DIRS for part in relative.parts)


def _is_test_file(path: Path) -> bool:
    """Match the test-module predicate used by the pack-boundary lint."""

    name = path.name
    return (path.suffix == ".py" and (name.startswith("test") or name.endswith("_test.py"))) or (
        ".test." in name or ".spec." in name
    )


def _python_files(member: Path) -> list[Path]:
    """Return Python files below a member without pytest-inert fixture trees."""

    if member.is_file():
        return [member] if member.suffix == ".py" and not member.is_symlink() else []
    if not member.is_dir() or _is_linked_dir(member):
        return []
    paths: list[Path] = []
    for directory, directories, filenames in os.walk(member, followlinks=False):
        base = Path(directory)
        directories[:] = [
            name
            for name in directories
            if not _is_linked_dir(base / name)
        ]
        paths.extend(
            base / name
            for name in filenames
            if name.endswith(".py")
            and not (base / name).is_symlink()
            and not _under_excluded(base / name, member)
        )
    return sorted(paths)


def _parse(path: Path) -> tuple[ast.Module | None, str | None]:
    """Parse *path*, returning an explicit failure instead of skipping it."""

    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path)), None
    except (OSError, SyntaxError) as exc:
        return None, f"{path}:{getattr(exc, 'lineno', 0) or 0}: cannot parse: {exc}"


def _conftests_between(root: Path, directory: Path) -> tuple[Path, ...]:
    """Return pytest conftests from *root* through *directory*, inclusively."""

    try:
        parts = directory.relative_to(root).parts
    except ValueError:
        return ()
    current = root
    conftests: list[Path] = []
    for part in ("", *parts):
        if part:
            current /= part
        conftest = current / "conftest.py"
        if (
            conftest.is_file()
            and not conftest.is_symlink()
            and not _under_excluded(conftest, root)
        ):
            conftests.append(conftest)
    return tuple(conftests)


def import_set_for(member: str | Path, root: Path) -> tuple[Path, ...]:
    """Return pytest's reachable module set for one member.

    This includes test modules, root-to-member conftests, and same-directory
    modules directly imported by those modules. Fixture trees are excluded.
    """

    target = _path(member, root)
    paths = {path for path in _python_files(target) if _is_test_file(path)}
    for test_file in tuple(paths):
        paths.update(_conftests_between(root, test_file.parent))
    pending = list(paths)
    while pending:
        source = pending.pop()
        tree, _ = _parse(source)
        if tree is None:
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".", 1)[0]]
            for name in names:
                local = source.parent / f"{name}.py"
                if local.is_file() and local not in paths and not _under_excluded(local, root):
                    paths.add(local)
                    pending.append(local)
    return tuple(sorted(paths))


def test_basenames_for(members: tuple[str, ...], root: Path) -> set[str]:
    """Return test module basenames that collide across *members*."""

    seen: set[str] = set()
    duplicates: set[str] = set()
    for member in members:
        for path in _python_files(_path(member, root)):
            if _is_test_file(path) and path.name != "conftest.py":
                if path.name in seen:
                    duplicates.add(path.name)
                seen.add(path.name)
    return duplicates


test_basenames_for.__test__ = False


def _assigned_values(tree: ast.Module) -> dict[str, ast.expr]:
    """Collect module-level simple assignments for local constant resolution."""

    values: dict[str, ast.expr] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            values[node.targets[0].id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            values[node.target.id] = node.value
    return values


def _scope_values(scope: ast.AST, parent_values: dict[str, ast.expr]) -> dict[str, ast.expr]:
    """Return direct assignments in one scope, shadowing its parent values."""

    values = parent_values.copy()
    for node in getattr(scope, "body", ()):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        ):
            values[node.targets[0].id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            values[node.target.id] = node.value
    return values


def _calls_in_scope(node: ast.AST) -> list[ast.Call]:
    """Return calls in *node* without descending into a nested scope."""

    calls: list[ast.Call] = []

    def visit(current: ast.AST) -> None:
        if current is not node and isinstance(
            current, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            return
        if isinstance(current, ast.Call):
            calls.append(current)
        for child in ast.iter_child_nodes(current):
            visit(child)

    visit(node)
    return calls


def _scopes(
    scope: ast.AST, values: dict[str, ast.expr]
) -> list[tuple[ast.AST, dict[str, ast.expr]]]:
    """Return every lexical scope with its intraprocedural constants."""

    scoped_values = _scope_values(scope, values)
    result = [(scope, scoped_values)]

    def visit(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                result.extend(_scopes(child, scoped_values))
            else:
                visit(child)

    visit(scope)
    return result


def _path_join_operand(
    node: ast.expr, values: dict[str, ast.expr], source: Path
) -> Path | None:
    """Resolve a right-hand ``Path /`` operand without discarding segments."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return Path(node.value)
    if isinstance(node, ast.Name) and node.id != "__file__":
        value = values.get(node.id)
        return _path_join_operand(value, values, source) if value is not None else None
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Path":
        return _path_join_operand(node.args[0], values, source) if node.args else None
    return _path_value(node, values, source)


def _path_value(node: ast.expr, values: dict[str, ast.expr], source: Path) -> Path | None:
    """Resolve the small, static ``Path`` expression vocabulary used in tests."""

    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        value = Path(node.value)
        return value if value.is_absolute() else source.parent / value
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return source
        value = values.get(node.id)
        return _path_value(value, values, source) if value is not None else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _path_value(node.left, values, source)
        right = _path_join_operand(node.right, values, source)
        return left / right if left is not None and right is not None else None
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Path"
        and node.args
    ):
        return _path_value(node.args[0], values, source)
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "resolve"
    ):
        return _path_value(node.func.value, values, source)
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        value = _path_value(node.value, values, source)
        return value.parent if value is not None else None
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parents"
    ):
        value = _path_value(node.value.value, values, source)
        index = node.slice
        if value is not None and isinstance(index, ast.Constant) and isinstance(index.value, int):
            return value.parents[index.value]
    return None


def _literal_name(node: ast.expr) -> str | None:
    """Return a loader name only when it is a literal string."""

    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _string_value(node: ast.expr, values: dict[str, ast.expr]) -> str | None:
    """Resolve a literal string or a same-scope constant name."""

    if isinstance(node, ast.Name):
        value = values.get(node.id)
        return _string_value(value, values) if value is not None else None
    return _literal_name(node)


def _is_loader(call: ast.Call) -> bool:
    """Whether *call* is ``importlib.util.spec_from_file_location``."""

    return isinstance(call.func, ast.Attribute) and call.func.attr == "spec_from_file_location"


def _loader_helpers(tree: ast.Module) -> dict[str, tuple[int, int]]:
    """Map supported wrapper functions to their loader name and path arguments."""

    helpers: dict[str, tuple[int, int]] = {}
    for function in (node for node in tree.body if isinstance(node, ast.FunctionDef)):
        parameters = [argument.arg for argument in function.args.args]
        for call in ast.walk(function):
            if (
                isinstance(call, ast.Call)
                and _is_loader(call)
                and len(call.args) >= 2
                and isinstance(call.args[0], ast.Name)
                and isinstance(call.args[1], ast.Name)
                and call.args[0].id in parameters
                and call.args[1].id in parameters
            ):
                helpers[function.name] = (
                    parameters.index(call.args[0].id),
                    parameters.index(call.args[1].id),
                )
    return helpers


def _subject_loader_records_for(
    member: str | Path, root: Path
) -> tuple[tuple[str, Path | None, Path], ...]:
    """Return static subject-loader pairs with the source that derives each one."""

    results: list[tuple[str, Path | None, Path]] = []
    for source in import_set_for(member, root):
        tree, _ = _parse(source)
        if tree is None:
            continue
        values = _assigned_values(tree)
        helpers = _loader_helpers(tree)
        scoped_calls: list[tuple[ast.Call, dict[str, ast.expr], ast.AST]] = [
            (call, scope_values, scope)
            for scope, scope_values in _scopes(tree, values)
            for call in _calls_in_scope(scope)
        ]
        for call, call_values, scope in scoped_calls:
            if _is_loader(call):
                if len(call.args) < 2:
                    results.append((
                        f"<unresolved:{_relative(source, root)}:{call.lineno}>",
                        None,
                        source,
                    ))
                    continue
                if isinstance(scope, ast.FunctionDef) and scope.name in helpers:
                    continue
                name = _string_value(call.args[0], call_values)
                results.append((
                    name or f"<unresolved:{_relative(source, root)}:{call.lineno}>",
                    _path_value(call.args[1], call_values, source) if name else None,
                    source,
                ))
            elif isinstance(call.func, ast.Name) and call.func.id in helpers:
                name_index, path_index = helpers[call.func.id]
                if len(call.args) <= max(name_index, path_index):
                    results.append((
                        f"<unresolved:{_relative(source, root)}:{call.lineno}>",
                        None,
                        source,
                    ))
                    continue
                name = _string_value(call.args[name_index], call_values)
                path = _path_value(call.args[path_index], call_values, source)
                unresolved = f"<unresolved:{_relative(source, root)}:{call.lineno}>"
                results.append((name or unresolved, path if name else None, source))
    return tuple(results)


def subject_loader_names_for(
    member: str | Path, root: Path
) -> tuple[tuple[str, Path | None], ...]:
    """Return static subject-loader ``(name, path)`` pairs, unresolved as ``None``."""

    return tuple(
        (name, path) for name, path, _ in _subject_loader_records_for(member, root)
    )


def path_mutations_in(member: str | Path, root: Path) -> tuple[str, ...]:
    """Return every reachable ``sys.path`` mutation as ``file:line``."""

    findings: list[str] = []
    for source in import_set_for(member, root):
        tree, _ = _parse(source)
        if tree is None:
            continue
        for node in ast.walk(tree):
            def is_sys_path(value: ast.expr) -> bool:
                """Whether *value* is the ``sys.path`` expression."""

                return (
                    isinstance(value, ast.Attribute)
                    and isinstance(value.value, ast.Name)
                    and value.value.id == "sys"
                    and value.attr == "path"
                )

            mutation = isinstance(node, (ast.Assign, ast.AnnAssign)) and any(
                is_sys_path(target)
                or isinstance(target, ast.Subscript) and is_sys_path(target.value)
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            )
            call = (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in {"append", "insert"}
                and is_sys_path(node.func.value)
            )
            if mutation or call:
                findings.append(f"{_relative(source, root)}:{node.lineno}")
    return tuple(sorted(findings))


def sibling_test_imports_in(member: str | Path, root: Path) -> tuple[str, ...]:
    """Return bare imports of a sibling test module from the import set."""

    target = _path(member, root)
    siblings = {path.stem for path in _python_files(target) if _is_test_file(path)}
    findings: list[str] = []
    for source in import_set_for(member, root):
        tree, _ = _parse(source)
        if tree is None:
            continue
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name.split(".", 1)[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".", 1)[0]]
            if any(name in siblings for name in names):
                findings.append(f"{_relative(source, root)}:{node.lineno}")
    return tuple(sorted(findings))


def validate_classes(classes: tuple[CompatibilityClass, ...], root: Path) -> list[str]:
    """Return declaration-shape findings; an empty list means valid."""

    findings: list[str] = []
    identifiers: set[str] = set()
    members: dict[str, str] = {}
    for cls in classes:
        if cls.identifier in identifiers:
            findings.append(f"duplicate identifier: {cls.identifier}")
        identifiers.add(cls.identifier)
        if not _IDENTIFIER.fullmatch(cls.identifier):
            findings.append(f"identifier is not kebab-case: {cls.identifier}")
        if cls.import_mode not in _IMPORT_MODES:
            findings.append(f"{cls.identifier} has invalid import mode: {cls.import_mode}")
        if cls.basename_resolution not in _BASENAME_RESOLUTIONS:
            findings.append(
                f"{cls.identifier} has invalid basename resolution: {cls.basename_resolution}"
            )
        if cls.subject_imports not in _SUBJECT_IMPORTS:
            findings.append(f"{cls.identifier} has invalid subject imports: {cls.subject_imports}")
        if len(cls.members) < 2:
            findings.append(f"{cls.identifier} has fewer than two members")
        for member in cls.members:
            path = _path(member, root)
            expected = root / "packs" / cls.pack / "tests"
            if not path.is_relative_to(expected):
                findings.append(f"{member} is outside pack {cls.pack}")
            if not path.is_dir():
                findings.append(f"{member} does not exist as a directory")
            prior = members.setdefault(member, cls.identifier)
            if prior != cls.identifier:
                findings.append(f"{member} appears in classes {prior} and {cls.identifier}")
    return findings


def _common_parent(paths: list[Path]) -> Path:
    """Return the deepest shared parent of non-empty *paths*."""

    common = list(paths[0].parts)
    for path in paths[1:]:
        common = [left for left, right in zip(common, path.parts, strict=False) if left == right]
    return Path(*common)


def _dotted_module_name(path: Path) -> str:
    """Derive pytest's package-mode module name for one test module."""

    names = [path.stem]
    current = path.parent
    while (current / "__init__.py").is_file():
        names.append(current.name)
        current = current.parent
    return ".".join(reversed(names))


def check_class_identity(cls: CompatibilityClass, root: Path) -> list[str]:
    """Return fail-closed identity and import-safety findings for one class."""

    findings = validate_classes((cls,), root)
    collisions = test_basenames_for(cls.members, root)
    if collisions:
        if cls.basename_resolution == "import-mode":
            if cls.import_mode != "importlib":
                findings.append("import-mode basename resolution requires importlib import mode")
        elif cls.basename_resolution == "packages":
            for basename in collisions:
                directories = [
                    path.parent
                    for member in cls.members
                    for path in _python_files(_path(member, root))
                    if _is_test_file(path) and path.name == basename
                ]
                shared = _common_parent(directories)
                if not all((directory / "__init__.py").is_file() for directory in directories):
                    missing = [
                        _relative(directory, root)
                        for directory in directories
                        if not (directory / "__init__.py").is_file()
                    ]
                    findings.append(
                        f"duplicate test basename {basename} lacks package __init__.py in "
                        f"{sorted(missing)}"
                    )
                if (shared / "__init__.py").is_file():
                    findings.append(
                        f"duplicate test basename {basename} shared parent has __init__.py"
                    )
                module_names = [_dotted_module_name(path) for path in (
                    path
                    for member in cls.members
                    for path in _python_files(_path(member, root))
                    if _is_test_file(path) and path.name == basename
                )]
                if len(module_names) != len(set(module_names)):
                    findings.append(
                        f"duplicate test basename {basename} has colliding package module names"
                    )
        else:
            findings.extend(f"duplicate test basename: {name}" for name in sorted(collisions))
    names: dict[str, Path] = {}
    loaders: list[tuple[str, Path | None]] = []
    loader_members: list[tuple[str, str, Path]] = []
    parsed_sources_by_member: dict[str, list[str]] = {}
    has_unparseable_source = False
    for member in cls.members:
        records = _subject_loader_records_for(member, root)
        loaders.extend((name, path) for name, path, _ in records)
        loader_members.extend((member, name, source) for name, _, source in records)
        for name, path, _ in records:
            if path is None:
                if name.startswith("<unresolved:"):
                    findings.append(f"unresolvable loader name: {name}")
                else:
                    findings.append(f"unresolvable loader path: {name}")
                continue
            resolved = path.resolve()
            if not resolved.is_file():
                findings.append(f"loader path does not exist: {name}: {resolved}")
                continue
            prior = names.setdefault(name, resolved)
            if prior != resolved:
                findings.append(
                    f"loader name {name} maps to two different paths: {prior} and {resolved}"
                )
        findings.extend(f"sys.path mutation: {item}" for item in path_mutations_in(member, root))
        if cls.import_mode == "importlib":
            findings.extend(
                f"sibling test import: {item}"
                for item in sibling_test_imports_in(member, root)
            )
        parsed_sources: list[str] = []
        for source in import_set_for(member, root):
            _, error = _parse(source)
            if error:
                findings.append(error)
                has_unparseable_source = True
            else:
                parsed_sources.append(_relative(source, root))
        parsed_sources_by_member[member] = parsed_sources
    if cls.subject_imports == "none" and loaders:
        member, name, source = loader_members[0]
        findings.append(
            f"{cls.identifier}: subject imports none but {member} source "
            f"{_relative(source, root)} derives loader {name}; "
            "declare explicit-qualified or drop the member in "
            "tools/pack_test_compatibility.py"
        )
    if cls.subject_imports == "explicit-qualified":
        if not loaders and not has_unparseable_source:
            members = ", ".join(cls.members)
            checked = "; ".join(
                f"{member}: {', '.join(sources) if sources else 'no parsed source files'}"
                for member, sources in parsed_sources_by_member.items()
            )
            findings.append(
                f"{cls.identifier}: members {members} declare explicit-qualified but derive "
                f"no loader from their parsed sources ({checked}); declare one or drop "
                "the member in tools/pack_test_compatibility.py"
            )
        elif any(path is None for _, path in loaders):
            findings.append("explicit-qualified subject imports require resolvable loaders")
    return findings
