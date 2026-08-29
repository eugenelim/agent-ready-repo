"""Contract tests for pack-test compatibility derivations."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
from pack_test_compatibility import (
    CLASSES,
    CompatibilityClass,
    _loader_helpers,
    _path_value,
    check_class_identity,
    classes_by_identifier,
    import_set_for,
    path_mutations_in,
    sibling_test_imports_in,
    subject_loader_names_for,
    test_basenames_for,
    validate_classes,
)

ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str = "") -> Path:
    """Write *text* below a synthetic repository and return its path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _class(*members: str, **changes: str) -> CompatibilityClass:
    """Build a compact valid class declaration for test cases."""

    values = {
        "identifier": "example-class",
        "pack": "example",
        "members": tuple(members),
        "import_mode": "prepend",
        "basename_resolution": "none",
        "subject_imports": "none",
        "rationale": "test declaration",
    }
    values.update(changes)
    return CompatibilityClass(**values)  # type: ignore[arg-type]


def _member(root: Path, name: str, source: str = "def test_ok() -> None: pass\n") -> str:
    """Create a suite directory and return its repository-relative path."""

    relative = f"packs/example/tests/skills/{name}"
    _write(root / relative / "test_contract.py", source)
    return relative


def test_shipped_classes_are_well_formed_and_sorted() -> None:
    """The shipped declaration table has stable, valid identifiers."""

    assert len(CLASSES) >= 1, "declare at least one shipped compatibility class"
    identifiers = [item.identifier for item in CLASSES]
    assert len(identifiers) == len(set(identifiers))
    assert all(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item) for item in identifiers)
    assert validate_classes(CLASSES, ROOT) == []
    unordered = (_class("packs/example/tests/skills/b", "packs/example/tests/skills/c", identifier="z"),
                 _class("packs/example/tests/skills/a", "packs/example/tests/skills/d", identifier="a"))
    assert [item.identifier for item in classes_by_identifier(unordered)] == ["a", "z"]
    assert [item.identifier for item in classes_by_identifier()] == sorted(identifiers)


@pytest.mark.parametrize(
    ("classes", "needle"),
    [
        (lambda root: (_class(_member(root, "one")),), "fewer than two"),
        (lambda root: (_class(_member(root, "one"), "packs/example/tests/skills/missing"),), "does not exist"),
        (lambda root: (_class(_member(root, "one"), "packs/other/tests/skills/two"),), "outside pack"),
        (lambda root: (_class(_member(root, "one"), _member(root, "two")),
                       _class("packs/example/tests/skills/one", _member(root, "three"), identifier="other")),
         "appears in classes"),
        (lambda root: (_class(_member(root, "one"), _member(root, "two")),
                       _class(_member(root, "three"), _member(root, "four"))), "duplicate identifier"),
        (lambda root: (_class(_member(root, "one"), _member(root, "two"), import_mode="typo"),), "invalid import mode"),
        (lambda root: (_class(_member(root, "one"), _member(root, "two"), basename_resolution="typo"),), "invalid basename resolution"),
        (lambda root: (_class(_member(root, "one"), _member(root, "two"), subject_imports="typo"),), "invalid subject imports"),
    ],
)
def test_validate_classes_rejects_bad_declarations(
    tmp_path: Path, classes: object, needle: str
) -> None:
    """Each declared class invariant has a synthetic red control."""

    assert needle in "\n".join(validate_classes(classes(tmp_path), tmp_path))  # type: ignore[operator]


def test_import_set_includes_test_shaped_fixture_files_and_conftests(tmp_path: Path) -> None:
    """Fixture trees exclude helpers only, never pytest-imported modules."""

    member = _member(tmp_path, "one", "from helper import VALUE\ndef test_ok() -> None: assert VALUE\n")
    _write(tmp_path / "conftest.py", "ROOT = True\n")
    _write(tmp_path / "packs/example/tests/conftest.py", "PACK = True\n")
    _write(tmp_path / member / "conftest.py", "LOCAL = True\n")
    _write(tmp_path / member / "helper.py", "VALUE = True\n")
    _write(tmp_path / member / "testdata/test_hidden.py", "def test_hidden() -> None: pass\n")
    _write(tmp_path / member / "testdata/conftest.py", "FIXTURE_TREE = True\n")
    paths = {path.relative_to(tmp_path).as_posix() for path in import_set_for(member, tmp_path)}
    assert f"{member}/test_contract.py" in paths
    assert f"{member}/conftest.py" in paths
    assert f"{member}/helper.py" in paths
    assert "conftest.py" in paths
    assert "packs/example/tests/conftest.py" in paths
    assert f"{member}/testdata/test_hidden.py" in paths
    assert f"{member}/testdata/conftest.py" in paths
    assert f"{member}/conftest.py" in {
        path.relative_to(tmp_path).as_posix()
        for path in import_set_for(tmp_path / member / "test_contract.py", tmp_path)
    }


def test_import_set_prunes_symlinked_directories_and_files(tmp_path: Path) -> None:
    """Import derivation matches the boundary lint's non-following tree walk."""

    member = _member(tmp_path, "one")
    outside = tmp_path / "outside"
    _write(outside / "test_external.py", "def test_external() -> None: pass\n")
    _write(outside / "test_link_target.py", "def test_link_target() -> None: pass\n")
    try:
        (tmp_path / member / "linked").symlink_to(outside, target_is_directory=True)
        (tmp_path / member / "test_link.py").symlink_to(outside / "test_link_target.py")
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    paths = {path.relative_to(tmp_path).as_posix() for path in import_set_for(member, tmp_path)}
    assert f"{member}/test_contract.py" in paths
    assert f"{member}/linked/test_external.py" not in paths
    assert f"{member}/test_link.py" not in paths


def test_identity_controls_for_basenames_loader_paths_and_parse_errors(tmp_path: Path) -> None:
    """Identity checks reject each unsafe static-analysis result."""

    one = _member(tmp_path, "one", "def test_same() -> None: pass\n")
    two = _member(tmp_path, "two", "def test_same() -> None: pass\n")
    cls = _class(one, two)
    assert test_basenames_for(cls.members, tmp_path) == {"test_contract.py"}
    assert "duplicate test basename" in "\n".join(check_class_identity(cls, tmp_path))
    _write(tmp_path / one / "__init__.py")
    _write(tmp_path / two / "__init__.py")
    packaged = _class(one, two, basename_resolution="packages")
    assert not check_class_identity(packaged, tmp_path)
    _write(tmp_path / "packs/example/tests/skills/__init__.py")
    assert "shared parent" in "\n".join(check_class_identity(packaged, tmp_path))
    _write(tmp_path / one / "test_contract.py", "import broken\ndef test_same() -> None: pass\n")
    _write(tmp_path / one / "broken.py", "def nope(:\n")
    assert "cannot parse" in "\n".join(check_class_identity(packaged, tmp_path))


def test_package_basename_resolution_requires_unique_dotted_module_names(tmp_path: Path) -> None:
    """Separate package roots with the same basename still collide in pytest."""

    one = "packs/example/tests/skills/p/x"
    two = "packs/example/tests/skills/q/x"
    for member in (one, two):
        _write(tmp_path / member / "__init__.py")
        _write(tmp_path / member / "test_contract.py", "def test_ok() -> None: pass\n")
    cls = _class(one, two, basename_resolution="packages")
    assert "colliding package module names" in "\n".join(check_class_identity(cls, tmp_path))


def test_loader_name_path_and_import_safety_controls(tmp_path: Path) -> None:
    """Load names, path mutation, and importlib sibling imports fail closed."""

    one = _member(
        tmp_path,
        "one",
        "import importlib.util\n"
        "spec = importlib.util.spec_from_file_location('shared', 'one.py')\n"
        "def test_ok() -> None: pass\n",
    )
    two = _member(
        tmp_path,
        "two",
        "import importlib.util\n"
        "spec = importlib.util.spec_from_file_location('shared', 'two.py')\n"
        "def test_ok() -> None: pass\n",
    )
    cls = _class(one, two)
    _write(tmp_path / one / "one.py")
    _write(tmp_path / two / "two.py")
    assert "two different paths" in "\n".join(check_class_identity(cls, tmp_path))
    _write(tmp_path / two / "test_contract.py", "import sys\nsys.path.insert(0, 'x')\ndef test_ok() -> None: pass\n")
    assert path_mutations_in(two, tmp_path)
    assert "sys.path mutation" in "\n".join(check_class_identity(cls, tmp_path))
    _write(tmp_path / two / "test_contract.py", "from test_contract import helper\ndef test_ok() -> None: pass\n")
    importlib_cls = _class(one, two, import_mode="importlib", basename_resolution="import-mode")
    assert sibling_test_imports_in(two, tmp_path)
    assert "sibling test import" in "\n".join(check_class_identity(importlib_cls, tmp_path))
    _write(tmp_path / two / "test_contract.py", "import importlib.util\nname = dynamic\nspec = importlib.util.spec_from_file_location(name, 'two.py')\n")
    assert "unresolvable loader name" in "\n".join(check_class_identity(cls, tmp_path))
    _write(
        tmp_path / two / "test_contract.py",
        "import importlib.util\n"
        "path = dynamic\n"
        "spec = importlib.util.spec_from_file_location('resolved_name', path)\n",
    )
    assert "unresolvable loader path: resolved_name" in "\n".join(
        check_class_identity(cls, tmp_path)
    )


@pytest.mark.parametrize(
    "source",
    [
        "class TestLoader:\n    spec = importlib.util.spec_from_file_location('shared', 'one.py')\n",
        "async def load() -> None:\n    spec = importlib.util.spec_from_file_location('shared', 'one.py')\n",
        "def outer() -> None:\n    def inner() -> None:\n        spec = importlib.util.spec_from_file_location('shared', 'one.py')\n",
    ],
    ids=("class-body", "async-function", "nested-function"),
)
def test_loader_calls_in_every_scope_are_fail_closed(tmp_path: Path, source: str) -> None:
    """A loader hidden in any lexical scope still contributes identity proof."""

    one = _member(tmp_path, "one", "import importlib.util\n" + source)
    two = _member(
        tmp_path,
        "two",
        "import importlib.util\nspec = importlib.util.spec_from_file_location('shared', 'two.py')\n",
    )
    _write(tmp_path / one / "one.py")
    _write(tmp_path / two / "two.py")
    assert "two different paths" in "\n".join(check_class_identity(_class(one, two), tmp_path))


def test_loader_helpers_identify_only_supported_wrappers() -> None:
    """Wrapper detection is independently testable from source traversal."""

    tree = ast.parse(
        "def load(name, path):\n"
        "    return importlib.util.spec_from_file_location(name, path)\n"
        "def unrelated(value):\n"
        "    return value\n"
    )
    assert _loader_helpers(tree) == {"load": (0, 1)}


def test_loader_declaration_and_missing_subject_controls(tmp_path: Path) -> None:
    """Subject-import declarations and paths cannot overclaim safety."""

    one = _member(
        tmp_path,
        "one",
        "import importlib.util\nspec = importlib.util.spec_from_file_location('one', 'gone.py')\n",
    )
    two = _member(tmp_path, "two")
    none = _class(one, two)
    assert "subject imports none" in "\n".join(check_class_identity(none, tmp_path))
    qualified = _class(one, two, subject_imports="explicit-qualified")
    assert "loader path does not exist" in "\n".join(check_class_identity(qualified, tmp_path))


def test_unparseable_sources_report_only_the_parse_failure(tmp_path: Path) -> None:
    """Syntax errors are not misclassified as loader or declaration failures."""

    one = _member(tmp_path, "one", "def broken(:\n")
    two = _member(tmp_path, "two")
    findings = check_class_identity(_class(one, two), tmp_path)
    assert sum("cannot parse" in finding for finding in findings) == 1
    assert not any("subject imports none" in finding for finding in findings)

    _write(
        tmp_path / two / "test_contract.py",
        "import importlib.util\n"
        "spec = importlib.util.spec_from_file_location('loader', 'two.py')\n",
    )
    _write(tmp_path / two / "two.py")
    findings = check_class_identity(_class(one, two), tmp_path)
    assert any("source" in finding and "loader" in finding for finding in findings)


def test_identity_findings_name_affected_locations_and_remedy(tmp_path: Path) -> None:
    """Identity failures point maintainers to the concrete repair surface."""

    one = _member(
        tmp_path,
        "one",
        "import importlib.util\n"
        "spec = importlib.util.spec_from_file_location('loader', 'one.py')\n",
    )
    two = _member(tmp_path, "two")
    _write(tmp_path / one / "one.py")
    findings = check_class_identity(_class(one, two), tmp_path)
    assert any(
        one in finding
        and f"{one}/test_contract.py" in finding
        and "loader" in finding
        and "explicit-qualified" in finding
        for finding in findings
    )
    qualified = _class(one, two, subject_imports="explicit-qualified")
    _write(tmp_path / one / "test_contract.py", "def test_ok() -> None: pass\n")
    qualified_findings = check_class_identity(qualified, tmp_path)
    assert any(
        one in finding
        and f"{one}/test_contract.py" in finding
        and "declare one or drop the member" in finding
        for finding in qualified_findings
    )


def test_path_value_preserves_all_segments_in_a_join(tmp_path: Path) -> None:
    """A multi-segment right operand has ordinary pathlib join semantics."""

    base = ast.parse('BASE = Path("base")\nBASE / "a/b/c.py"')
    expression = base.body[1].value
    assert isinstance(expression, ast.expr)
    values = {"BASE": base.body[0].value}
    assert _path_value(expression, values, tmp_path / "test_loader.py") == (
        tmp_path / "base/a/b/c.py"
    )


def test_real_loader_paths_are_exact_existing_files_and_candidate_classes_are_safe() -> None:
    """Real loader derivations retain every path segment and local binding."""

    expected = {
        "packs/architect/tests/skills/architect-assess": (
            "architect_profile_repo_test",
            ROOT / "packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py",
        ),
        "packs/linear/tests/skills/linear-brief-intake": (
            "linear_intake_adapter",
            ROOT / "packs/linear/.apm/skills/linear-brief-intake/scripts/intake_adapter.py",
        ),
        "packs/atlassian/tests/skills/jira-brief-intake": (
            "jira_intake_adapter",
            ROOT / "packs/atlassian/.apm/skills/jira-brief-intake/scripts/intake_adapter.py",
        ),
    }
    for member, pair in expected.items():
        assert pair[1].is_file()
        assert pair in subject_loader_names_for(member, ROOT)

    linear_pairs = subject_loader_names_for("packs/linear/tests/skills/linear", ROOT)
    linear_script = next(path for name, path in linear_pairs if name == "linear_script")
    assert linear_script is not None and linear_script.is_file()

    for candidate in CLASSES:
        assert check_class_identity(candidate, ROOT) == [], candidate.identifier
        for member in candidate.members:
            assert all(
                path is None or path.is_file()
                for _, path in subject_loader_names_for(member, ROOT)
            )


def test_real_tree_import_safety_shapes() -> None:
    """The real examples protect the derivations from toy-fixture drift."""

    architect = "packs/architect/tests/skills/architect-assess"
    loaders = subject_loader_names_for(architect, ROOT)
    assert ("architect_profile_repo_test", ROOT / "packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py") in loaders
    compile_okf = "packs/catalogue-curation/tests/skills/compile-okf"
    assert {
        "packs/catalogue-curation/tests/skills/compile-okf/test_apply.py:22",
        "packs/catalogue-curation/tests/skills/compile-okf/test_parser.py:18",
        "packs/catalogue-curation/tests/skills/compile-okf/test_render.py:21",
    }.issubset(path_mutations_in(compile_okf, ROOT))
    assert "packs/catalogue-curation/tests/skills/compile-okf/test_cli.py:9" in (
        sibling_test_imports_in(compile_okf, ROOT)
    )
    assert "packs/atlassian/tests/skills/jira/conftest.py:17" in path_mutations_in(
        "packs/atlassian/tests/skills/jira/test_intake_policy.py", ROOT
    )
    core_members = ("packs/core/tests/pack", "packs/core/tests/skills/workspace-status")
    pairs = [pair for member in core_members for pair in subject_loader_names_for(member, ROOT)]
    shared = [path for name, path in pairs if name == "workspace_status_engine"]
    assert len(shared) >= 2 and len(set(shared)) == 1
    core_class = _class(*core_members, pack="core")
    assert not any(
        "workspace_status_engine maps to two different paths" in finding
        for finding in check_class_identity(core_class, ROOT)
    )
    agent_members = (
        "packs/agent-skill-engineering/tests/skills/author_or_update",
        "packs/agent-skill-engineering/tests/skills/review_or_optimize",
    )
    assert all((ROOT / member / "__init__.py").is_file() for member in agent_members)
    assert not (ROOT / "packs/agent-skill-engineering/tests/skills/__init__.py").exists()
