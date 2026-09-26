"""End-to-end and corpus checks for retirement-candidates (T8)."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.file_safety import (
    list_confined_regular_files,
    read_confined_regular_file,
)

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "packs/core/.apm/skills/workspace-status/scripts"
CLI = SCRIPTS / "workspace_status.py"
SCHEMA = ROOT / "contracts/jsonschema/spec-retirement-candidates.schema.json"
RUN_DATE = "2026-09-25"


def _load(name: str, filename: str):
    """Load one workspace-status module under a roster-unique name."""
    module_name = f"workspace_status_{name}_t8_roster"
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, SCRIPTS / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _schema() -> dict:
    """Read the live output schema through the blessed confined reader."""
    return json.loads(read_confined_regular_file(ROOT, SCHEMA, max_bytes=1024 * 1024))


def _spec_dir(root: Path, slug: str) -> Path:
    """Build a fixture spec path without pinning a real delivery slug."""
    return root.joinpath("docs", "specs", slug)


def _workspace_entry(slug: str, *, collection: str = "shipped", needs: str = "[]") -> str:
    """Build one workspace entry without a literal protected-directory path."""
    spec_path = "/".join(("docs", "specs", slug, "spec.md"))
    return (
        f"[[ini-001.work.{collection}]]\n"
        f'path = "{spec_path}"\n'
        f"needs = {needs}\n"
    )


def _write_clean_fixture(root: Path) -> None:
    """Create the smallest clean repository accepted by the command."""
    spec_dir = _spec_dir(root, "alpha")
    spec_dir.mkdir(parents=True)
    (spec_dir / "spec.md").write_text(
        "# Spec: Alpha\n\n- **Status:** Shipped\n\nOwns widgets/runtime.py.\n",
        encoding="utf-8",
    )
    (root / "widgets").mkdir()
    (root / "widgets" / "runtime.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "workspace.toml").write_text(
        _workspace_entry("alpha"),
        encoding="utf-8",
    )
    (root / ".workspace-prune-protected.toml").write_text(
        "protected = []\n", encoding="utf-8"
    )
    contracts = root / "contracts" / "jsonschema"
    contracts.mkdir(parents=True)
    (contracts / "fixture.json").write_text("{}\n", encoding="utf-8")
    (contracts / "spec-retirement-candidates.schema.json").write_bytes(
        read_confined_regular_file(ROOT, SCHEMA, max_bytes=1024 * 1024)
    )
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "fixture@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "Fixture"], check=True
    )
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "commit",
            "-q",
            "--date=2020-01-01T00:00:00Z",
            "-m",
            "fixture",
        ],
        check=True,
        env={**os.environ, "GIT_COMMITTER_DATE": "2020-01-01T00:00:00Z"},
    )


def _invoke(root: Path) -> subprocess.CompletedProcess[bytes]:
    """Invoke the shipped CLI exactly as an adopter does."""
    return subprocess.run(
        [
            sys.executable,
            str(CLI),
            "retirement-candidates",
            "--root",
            str(root),
            "--run-date",
            RUN_DATE,
        ],
        check=False,
        capture_output=True,
    )


def test_end_to_end_read_only_invocation_is_schema_valid(tmp_path: Path) -> None:
    """The real read-only subcommand exits zero and emits its schema contract."""
    root = tmp_path / "repo"
    root.mkdir()
    _write_clean_fixture(root)
    before = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }
    paths = [root, *root.rglob("*")]
    original_modes = {
        path: stat.S_IMODE(path.lstat().st_mode)
        for path in paths
        if not path.is_symlink()
    }
    for path in reversed(paths):
        if path.is_symlink():
            continue
        path.chmod(0o555 if path.is_dir() else 0o444)
    try:
        result = _invoke(root)
    finally:
        for path in paths:
            if path in original_modes:
                path.chmod(original_modes[path])

    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    document = json.loads(result.stdout)
    validator = _load("retirement_contract", "workspace_status_retirement_contract.py")
    assert validator.validate_document(document, _schema()) == []
    after = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.parts
    }
    assert after == before


def test_two_unchanged_invocations_are_byte_identical(tmp_path: Path) -> None:
    """The supplied run date makes the whole emitted document deterministic."""
    root = tmp_path / "repo"
    root.mkdir()
    _write_clean_fixture(root)

    first = _invoke(root)
    second = _invoke(root)

    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr == b""


def _emitted_refusal_codes() -> set[str]:
    """Enumerate refusal codes from this command's dedicated schema surface."""
    schema = _schema()
    assert schema["properties"]["schema"]["const"] == "spec-retirement-candidates.v1"
    return set(schema["$defs"]["refusal"]["properties"]["code"]["enum"])


def _refusal_fixture(
    code: str, root: Path, monkeypatch: pytest.MonkeyPatch
) -> Callable[[], dict]:
    """Construct the fixture for one schema-derived command refusal code."""
    command = _load("retirement_command", "workspace_status_retirement_command.py")
    root.mkdir()
    _write_clean_fixture(root)

    if code == "spec-directory-absent":
        (root / "workspace.toml").write_text(
            _workspace_entry("missing"),
            encoding="utf-8",
        )
    elif code == "spec-file-absent":
        missing = _spec_dir(root, "missing")
        missing.mkdir()
        (root / "workspace.toml").write_text(
            _workspace_entry("missing"),
            encoding="utf-8",
        )
    elif code == "spec-unreadable":
        spec = _spec_dir(root, "alpha") / "spec.md"
        spec.unlink()
        spec.mkdir()
    elif code == "input-unreadable":
        manifest = root / ".workspace-prune-protected.toml"
        manifest.unlink()
        manifest.mkdir()
    elif code == "input-unparseable":
        (root / "workspace.toml").write_bytes(b"[[[ invalid")
    elif code == "spec-status-unrecognised":
        (_spec_dir(root, "alpha") / "spec.md").write_text(
            "# Spec\n\n- **Status:** Unknown\n", encoding="utf-8"
        )
    elif code == "needs-shape-unrecognised":
        (root / "workspace.toml").write_text(
            _workspace_entry("alpha", needs="7"),
            encoding="utf-8",
        )
    elif code == "collection-unrecognised":
        (root / "workspace.toml").write_text(
            _workspace_entry("alpha", collection="mystery"),
            encoding="utf-8",
        )
    elif code == "path-escapes-root":
        outside = root.parent / "outside"
        outside.mkdir()
        _spec_dir(root, "escape").symlink_to(outside, target_is_directory=True)
        (root / "workspace.toml").write_text(
            _workspace_entry("escape"),
            encoding="utf-8",
        )
    elif code == "input-too-large":
        (_spec_dir(root, "alpha") / "spec.md").write_bytes(b"x" * (8 * 1024 * 1024 + 1))
    elif code == "subprocess-timeout":
        def timeout(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
            raise subprocess.TimeoutExpired(cmd="git", timeout=30)

        monkeypatch.setattr(command, "_run_git", timeout)
    elif code == "evidence-ungathered":
        def failed(*args: object, **kwargs: object) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(args=["git"], returncode=1, stdout=b"", stderr=b"")

        monkeypatch.setattr(command, "_run_git", failed)
    else:  # a schema/source code added without a fixture must fail here
        pytest.fail(f"no retirement-candidates fixture for schema refusal code {code!r}")

    return lambda: command.retirement_candidates_document(
        root, run_date=RUN_DATE, stale_after_days=30
    )


def test_every_command_refusal_code_has_a_producing_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Schema enum codes on this command surface each have a live fixture."""
    schema_codes = set(_schema()["$defs"]["refusal"]["properties"]["code"]["enum"])
    command_codes = _emitted_refusal_codes()
    assert command_codes <= schema_codes
    assert command_codes, "the command source must expose its refusal surface"

    for index, code in enumerate(sorted(command_codes)):
        produce = _refusal_fixture(code, tmp_path / f"fixture-{index}", monkeypatch)
        document = produce()
        actual = {refusal["code"] for refusal in document["refusals"]}
        assert code in actual, f"fixture for {code!r} emitted {sorted(actual)!r}"
        validator = _load(
            "retirement_contract", "workspace_status_retirement_contract.py"
        )
        assert validator.validate_document(document, _schema()) == []


def test_real_corpus_namespaced_specs_are_attributed() -> None:
    """No real spec that names an inferred namespace remains unattributed."""
    retirement = _load("retirement", "workspace_status_retirement.py")
    tracked = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8").split("\0")
    namespaces = retirement.infer_namespaces(path for path in tracked if path)
    spec_files = [
        path
        for path in list_confined_regular_files(
            ROOT,
            ROOT.joinpath("docs", "specs"),
            max_files=10000,
            max_depth=8,
            max_entries=20000,
        )
        if path.name == "spec.md"
    ]
    unattributed: list[str] = []
    for path in spec_files:
        body = read_confined_regular_file(ROOT, path, max_bytes=8 * 1024 * 1024).decode(
            "utf-8"
        )
        names_namespace = any(f"{namespace}/" in body for namespace in namespaces)
        if names_namespace and retirement.attribute_spec(body, namespaces) == "unscoped":
            unattributed.append(path.relative_to(ROOT).as_posix())

    assert unattributed == []


def test_in_root_symlinked_spec_is_read_by_the_command(tmp_path: Path) -> None:
    """A spec.md that is an in-root link is read, at the CAPABILITY level.

    The confined reader was fixed for this and its own unit test passed, while
    the command kept a second, earlier guard that refused every link whatever
    its target.  A helper-level test cannot see that: this one drives the
    shipped command so both guards must agree.
    """
    root = tmp_path / "repo"
    root.mkdir()
    _write_clean_fixture(root)
    linked = _spec_dir(root, "linked-spec")
    linked.mkdir(parents=True)
    (linked / "AGENTS.md").write_text(
        "# Spec: Linked\n\n- **Status:** Shipped\n", encoding="utf-8"
    )
    (linked / "spec.md").symlink_to("AGENTS.md")

    result = _invoke(root)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    doc = json.loads(result.stdout)

    slugs = {c["slug"] for c in doc["candidates"]}
    assert "linked-spec" in slugs, (
        "an in-root symlinked spec.md must be read, not refused: "
        f"candidates={sorted(slugs)} refusals={doc['refusals']}"
    )
    escaping = [r for r in doc["refusals"] if r["code"] == "path-escapes-root"]
    assert not escaping, f"no path escaped the root, yet: {escaping}"
