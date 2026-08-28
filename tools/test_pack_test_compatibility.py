"""Contract tests for pack-test compatibility derivations."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pack_test_compatibility import (
    CLASSES,
    CompatibilityClass,
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


def test_classes_are_empty_and_sorted() -> None:
    """The declaration table remains typed-but-empty until T5."""

    assert CLASSES == ()
    unordered = (_class("packs/example/tests/skills/b", "packs/example/tests/skills/c", identifier="z"),
                 _class("packs/example/tests/skills/a", "packs/example/tests/skills/d", identifier="a"))
    assert [item.identifier for item in classes_by_identifier(unordered)] == ["a", "z"]


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
    ],
)
def test_validate_classes_rejects_bad_declarations(
    tmp_path: Path, classes: object, needle: str
) -> None:
    """Each declared class invariant has a synthetic red control."""

    assert needle in "\n".join(validate_classes(classes(tmp_path), tmp_path))  # type: ignore[operator]


def test_import_set_contains_conftests_and_local_imports_but_not_fixtures(tmp_path: Path) -> None:
    """Pytest-reachable imports include conftests and exclude fixture trees."""

    member = _member(tmp_path, "one", "from helper import VALUE\ndef test_ok() -> None: assert VALUE\n")
    _write(tmp_path / "conftest.py", "ROOT = True\n")
    _write(tmp_path / "packs/example/tests/conftest.py", "PACK = True\n")
    _write(tmp_path / member / "conftest.py", "LOCAL = True\n")
    _write(tmp_path / member / "helper.py", "VALUE = True\n")
    _write(tmp_path / member / "testdata/test_hidden.py", "def test_hidden() -> None: pass\n")
    paths = {path.relative_to(tmp_path).as_posix() for path in import_set_for(member, tmp_path)}
    assert f"{member}/test_contract.py" in paths
    assert f"{member}/conftest.py" in paths
    assert f"{member}/helper.py" in paths
    assert "conftest.py" in paths
    assert "packs/example/tests/conftest.py" in paths
    assert not any("testdata" in path for path in paths)
    assert f"{member}/conftest.py" in {
        path.relative_to(tmp_path).as_posix()
        for path in import_set_for(tmp_path / member / "test_contract.py", tmp_path)
    }


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

    candidates = (
        _class(
            "packs/agent-skill-engineering/tests/pack",
            "packs/agent-skill-engineering/tests/integration",
            "packs/agent-skill-engineering/tests/skills/author_or_update",
            "packs/agent-skill-engineering/tests/skills/review_or_optimize",
            identifier="agent-skill-engineering-contract",
            pack="agent-skill-engineering",
            basename_resolution="packages",
        ),
        _class(
            "packs/architect/tests/pack",
            "packs/architect/tests/skills/architect-assess",
            "packs/architect/tests/skills/architect-design",
            "packs/architect/tests/skills/architect-review",
            identifier="architect-contract",
            pack="architect",
            subject_imports="explicit-qualified",
        ),
        _class(
            "packs/desk-research/tests/pack",
            "packs/desk-research/tests/skills/desk-research-project-check",
            "packs/desk-research/tests/skills/desk-research-project-digest",
            "packs/desk-research/tests/skills/desk-research-project-status",
            "packs/desk-research/tests/skills/desk-research-project-synthesize",
            "packs/desk-research/tests/skills/devils-advocate",
            identifier="desk-research-content",
            pack="desk-research",
            import_mode="importlib",
            basename_resolution="import-mode",
        ),
        _class(
            "packs/converters/tests/skills/markdown-to-html",
            "packs/converters/tests/skills/mermaid-renderer",
            identifier="converters-invocation-contract",
            pack="converters",
            import_mode="importlib",
            basename_resolution="import-mode",
        ),
        _class(
            "packs/linear/tests/skills/linear",
            "packs/linear/tests/skills/linear-brief-intake",
            identifier="linear-intake",
            pack="linear",
            subject_imports="explicit-qualified",
        ),
    )
    for candidate in candidates:
        assert check_class_identity(candidate, ROOT) == []
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
    assert len(path_mutations_in(compile_okf, ROOT)) == 3
    assert len(sibling_test_imports_in(compile_okf, ROOT)) == 1
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
