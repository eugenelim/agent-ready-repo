"""Safety and evidence contracts for the optional repository profiler."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = PACK_ROOT / ".apm" / "skills" / "architect-assess" / "scripts" / "profile_repo.py"


def _load(path: Path, name: str) -> ModuleType:
    """Load a module from a repository path without package installation."""

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def profiler() -> ModuleType:
    """Return the profiler module in projected-install fallback mode."""

    module = _load(SCRIPT_PATH, "architect_profile_repo_test")
    module.catalogue_read_confined_regular_file = None
    module.catalogue_validate_confined_directory = None
    return module


def _fixture_repo(root: Path) -> None:
    """Create a mixed, language-diverse repository evidence fixture."""

    files = {
        "README.md": "# Demo\n",
        "pyproject.toml": "[project]\nname='demo'\n",
        "src/app.py": "import json as js\nfrom .service import run as execute\n",
        "src/service.py": "def run() -> None:\n    pass\n",
        "src/Main.java": "package demo; class Main {}\n",
        "tests/test_app.py": "from src import app\n",
        ".github/workflows/ci.yml": "name: ci\n",
        "deploy/terraform/main.tf": 'resource "null_resource" "demo" {}\n',
        "migrations/001.sql": "create table demo(id int);\n",
        "ops/runbooks/recovery.md": "# Recovery\n",
        "generated/client.py": "import generated_dependency\n",
        "vendor/lib/third_party.py": "import vendor_dependency\n",
        "examples/demo.py": "import example_dependency\n",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def test_profile_is_deterministic_language_neutral_and_ast_exact(
    tmp_path: Path, profiler: ModuleType
) -> None:
    target = tmp_path / "repo"
    target.mkdir()
    _fixture_repo(target)
    limits = profiler.Limits(max_files=100, max_file_bytes=100_000, max_seconds=5, git_commits=0)

    first = profiler.build_profile(target, limits)
    second = profiler.build_profile(target, limits)
    assert profiler.render_json(first) == profiler.render_json(second)
    assert first["root"] == "."
    assert first["interpretation"]["architecture_model"] == "not produced"
    assert first["interpretation"]["composite_risk_score"] == "not produced"
    assert "src/Main.java" in first["evidence_surfaces"]["source"]
    assert "pyproject.toml" in first["evidence_surfaces"]["manifest"]
    assert "deployment_iac" in first["evidence_surfaces"]
    assert first["content_tags"] == {"example": 1, "generated": 1, "vendored": 1}

    imports = first["signals"]["python_imports"]
    assert {
        (item["file"], item["kind"], item["module"], item.get("name"), item["alias"])
        for item in imports
    } == {
        ("src/app.py", "import", "json", None, "js"),
        ("src/app.py", "from", ".service", "run", "execute"),
        ("tests/test_app.py", "from", "src", "app", None),
    }
    assert all(
        not item["file"].startswith(("generated/", "vendor/", "examples/")) for item in imports
    )


def test_limits_return_partial_with_exact_uncovered_reason(
    tmp_path: Path, profiler: ModuleType
) -> None:
    target = tmp_path / "repo"
    target.mkdir()
    for index in range(5):
        (target / f"file_{index}.py").write_text("import os\n", encoding="utf-8")
    result = profiler.build_profile(
        target,
        profiler.Limits(max_files=2, max_file_bytes=1_000, max_seconds=5, git_commits=0),
    )
    assert result["status"] == "partial"
    assert result["coverage"]["files_seen"] == 2
    assert result["coverage"]["limit_reasons"] == [
        "file count limit reached; remaining entries uncovered"
    ]


def test_directory_entry_budget_bounds_enumeration_before_file_limit(
    tmp_path: Path, profiler: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Large directories stop at the entry budget rather than materializing all names."""

    target = tmp_path / "repo"
    target.mkdir()
    for index in range(10):
        (target / f"file_{index}.py").write_text("import os\n", encoding="utf-8")
    real_scandir = profiler.os.scandir
    yielded = 0

    class CountingScandir:
        """Count entries requested from the underlying directory iterator."""

        def __init__(self, path: Path) -> None:
            self.iterator = real_scandir(path)

        def __enter__(self) -> CountingScandir:
            return self

        def __exit__(self, *_args: object) -> None:
            self.iterator.close()

        def __iter__(self) -> CountingScandir:
            return self

        def __next__(self) -> os.DirEntry[str]:
            nonlocal yielded
            item = next(self.iterator)
            yielded += 1
            return item

    monkeypatch.setattr(profiler.os, "scandir", CountingScandir)
    result = profiler.build_profile(
        target,
        profiler.Limits(
            max_files=100,
            max_file_bytes=1_000,
            max_seconds=5,
            git_commits=0,
            max_entries=3,
        ),
    )
    assert result["status"] == "partial"
    assert result["coverage"]["files_seen"] <= 3
    assert yielded <= 4  # one look-ahead detects the exhausted budget
    assert result["coverage"]["limit_reasons"] == [
        "directory entry limit reached; remaining entries uncovered"
    ]


def test_shared_deadline_stops_semantic_inspection(
    tmp_path: Path, profiler: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AST work consumes the same deadline as traversal and Git collection."""

    target = tmp_path / "repo"
    target.mkdir()
    for index in range(3):
        (target / f"file_{index}.py").write_text("import os\n", encoding="utf-8")
    original = profiler._python_imports

    def slow_imports(source: str, relative: str) -> tuple[list[dict[str, object]], str | None]:
        time.sleep(0.02)
        return original(source, relative)

    monkeypatch.setattr(profiler, "_python_imports", slow_imports)
    result = profiler.build_profile(
        target,
        profiler.Limits(
            max_files=100,
            max_file_bytes=1_000,
            max_seconds=0.01,
            git_commits=1,
        ),
    )
    assert result["status"] == "partial"
    assert "elapsed work limit reached; semantic inspection incomplete" in result["coverage"][
        "limit_reasons"
    ]
    assert "git history skipped because elapsed work limit was reached" in result["coverage"][
        "diagnostics"
    ]


def test_links_hardlinks_and_special_files_are_excluded_without_reading(
    tmp_path: Path, profiler: ModuleType
) -> None:
    target = tmp_path / "repo"
    outside = tmp_path / "outside.txt"
    target.mkdir()
    outside.write_text("do not read", encoding="utf-8")
    (target / "safe.py").write_text("import os\n", encoding="utf-8")
    (target / "escape.py").symlink_to(outside)
    os.link(target / "safe.py", target / "hard.py")
    fifo = target / "events.pipe"
    os.mkfifo(fifo)

    result = profiler.build_profile(
        target,
        profiler.Limits(max_files=100, max_file_bytes=1_000, max_seconds=5, git_commits=0),
    )
    excluded = {item["path"]: item["reason"] for item in result["coverage"]["excluded"]}
    assert excluded == {
        "escape.py": "link-like entry",
        "events.pipe": "non-regular or hard-linked entry",
        "hard.py": "non-regular or hard-linked entry",
        "safe.py": "non-regular or hard-linked entry",
    }
    rendered = profiler.render_json(result)
    assert str(tmp_path) not in rendered
    assert "do not read" not in rendered


def test_protected_and_unsafe_display_paths_are_redacted_before_inventory(
    tmp_path: Path, profiler: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Credential classes and hostile display names never enter profile evidence."""

    target = tmp_path / "repo"
    target.mkdir()
    (target / "safe.py").write_text("import os\n", encoding="utf-8")
    assert profiler._is_protected_path(target / ".aws" / "credentials", target)
    assert profiler._is_protected_path(target / ".env.local", target)
    assert profiler._is_protected_path(target / ".ssh" / "id_example", target)
    assert profiler._is_protected_path(target / "client.pem", target)

    protected = target / "credential-box" / "payload"
    protected.parent.mkdir()
    protected.write_text("secret", encoding="utf-8")
    (target / "unsafe-display.py").write_text("import sys\n", encoding="utf-8")
    assert not profiler._is_safe_display("bad`name.py")
    assert not profiler._is_safe_display("bad\nname.py")
    assert not profiler._is_safe_display("bad\x1bname.py")
    original_protected = profiler._is_protected_path
    original_display = profiler._is_safe_display
    monkeypatch.setattr(
        profiler,
        "_is_protected_path",
        lambda path, root: "credential-box" in path.parts or original_protected(path, root),
    )
    monkeypatch.setattr(
        profiler,
        "_is_safe_display",
        lambda value: "unsafe-display" not in value and original_display(value),
    )

    result = profiler.build_profile(
        target,
        profiler.Limits(max_files=100, max_file_bytes=1_000, max_seconds=5, git_commits=0),
    )
    rendered = profiler.render_json(result)
    assert "credential-box" not in rendered
    assert "unsafe-display.py" not in rendered
    excluded_paths = {item["path"] for item in result["coverage"]["excluded"]}
    assert excluded_paths == {"[protected]", "[unsafe-path]"}


@pytest.mark.parametrize(
    "relative",
    (
        ".aws/credentials",
        ".ssh/id_example",
        ".kube/config",
        ".mozilla/profile/data",
        ".config/gcloud/application_default_credentials.json",
        ".config/google-chrome/Profile 1/data",
        ".config/chromium/Profile 1/data",
        "Library/Keychains/login-db",
        "Library/Application Support/Google Chrome/Profile 1/data",
        "AppData/Microsoft/Edge/Profile/data",
        ".docker/config.json",
        ".cargo/credentials",
        ".pip/pip.conf",
        ".npmrc",
        ".pypirc",
        ".env.local",
        "client.pem",
        "client.key",
        "client.p12",
        "client.pfx",
        "client.keystore",
        "privatekey-material",
    ),
)
def test_every_protected_path_class_is_rejected_without_access(
    tmp_path: Path, profiler: ModuleType, relative: str
) -> None:
    """The deny policy can classify protected paths without touching them."""

    assert profiler._is_protected_path(tmp_path / relative, tmp_path)


@pytest.mark.parametrize(
    "root_name",
    (".aws", ".ssh", ".kube", ".mozilla", "google-chrome", "gcloud"),
)
def test_selected_protected_root_is_classified_without_access(
    profiler: ModuleType, root_name: str
) -> None:
    """The root's own canonical components participate in protected classification."""

    root = (
        Path("/synthetic/.config") / root_name
        if root_name == "gcloud"
        else Path("/synthetic") / root_name
    )
    assert profiler._is_protected_path(root, root)


def test_resolve_root_refuses_when_selected_root_is_protected(
    tmp_path: Path, profiler: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Root validation invokes the protected-path policy before traversal."""

    selected = tmp_path / "credential-box"
    selected.mkdir()
    original = profiler._is_protected_path
    monkeypatch.setattr(
        profiler,
        "_is_protected_path",
        lambda path, root: path == root == selected.resolve() or original(path, root),
    )

    with pytest.raises(profiler.ProfileError, match="root is protected"):
        profiler.resolve_root(selected)


def test_git_history_capture_stops_at_byte_budget(
    tmp_path: Path, profiler: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git collection streams through an explicit byte cap and marks partial data."""

    class FakeStdout:
        def __init__(self) -> None:
            self.sent = False

        def read(self, _size: int) -> bytes:
            if self.sent:
                return b""
            self.sent = True
            return b"src/a.py\0src/b.py\0src/c.py\0"

    class FakeProcess:
        def __init__(self) -> None:
            self.stdout = FakeStdout()
            self.returncode = 0

        def poll(self) -> int:
            return self.returncode

        def wait(self, timeout: float) -> int:
            assert timeout > 0
            return self.returncode

        def kill(self) -> None:
            self.returncode = -9

    monkeypatch.setattr(profiler.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    budget = profiler.WorkBudget(time.monotonic() + 5, max_entries=10)
    churn, diagnostic = profiler._git_churn(
        tmp_path,
        commits=10,
        budget=budget,
        max_bytes=10,
        max_paths=10,
    )
    assert churn == [{"path": "src/a.py", "changes": 1, "source": "git_log_last_10_commits"}]
    assert diagnostic == "git history partial: byte limit reached"


def test_git_history_capture_stops_at_distinct_path_budget(
    tmp_path: Path, profiler: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git collection cannot retain more distinct paths than the declared cap."""

    class FakeStdout:
        chunks = iter((b"src/a.py\0src/b.py\0", b""))

        def read(self, _size: int) -> bytes:
            return next(self.chunks)

    class FakeProcess:
        stdout = FakeStdout()
        returncode = 0

        def poll(self) -> int:
            return self.returncode

        def wait(self, timeout: float) -> int:
            assert timeout > 0
            return self.returncode

        def kill(self) -> None:
            self.returncode = -9

    monkeypatch.setattr(profiler.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    churn, diagnostic = profiler._git_churn(
        tmp_path,
        commits=10,
        budget=profiler.WorkBudget(time.monotonic() + 5, max_entries=10),
        max_bytes=1_000,
        max_paths=1,
    )
    assert churn == [{"path": "src/a.py", "changes": 1, "source": "git_log_last_10_commits"}]
    assert diagnostic == "git history partial: path count limit reached"


def test_output_requires_and_stays_within_an_approved_root(
    tmp_path: Path, profiler: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    destination = profiler._confine_output(Path("profile.json"), approved)
    profiler._write_output(destination, "{}\n", approved)
    assert destination.read_text(encoding="utf-8") == "{}\n"

    with pytest.raises(profiler.ProfileError):
        profiler._confine_output(Path("../escape.json"), approved)
    with pytest.raises(profiler.ProfileError):
        profiler._confine_output(tmp_path / "outside.json", approved)

    outside = tmp_path / "outside.json"
    outside.write_text("preserve", encoding="utf-8")
    symlink = approved / "linked.json"
    symlink.symlink_to(outside)
    with pytest.raises(profiler.ProfileError):
        profiler._write_output(symlink, "replace\n", approved)
    assert outside.read_text(encoding="utf-8") == "preserve"

    source = approved / "source.json"
    source.write_text("preserve", encoding="utf-8")
    hardlink = approved / "hardlink.json"
    os.link(source, hardlink)
    with pytest.raises(profiler.ProfileError):
        profiler._write_output(hardlink, "replace\n", approved)
    assert source.read_text(encoding="utf-8") == "preserve"

    fifo = approved / "events.pipe"
    os.mkfifo(fifo)
    with pytest.raises(profiler.ProfileError):
        profiler._write_output(fifo, "replace\n", approved)

    monkeypatch.setattr(profiler.secrets, "token_hex", lambda _size: "known")
    staged_link = approved / ".new.json.tmp-known"
    staged_link.symlink_to(outside)
    with pytest.raises(profiler.ProfileError):
        profiler._write_output(approved / "new.json", "replace\n", approved)
    assert outside.read_text(encoding="utf-8") == "preserve"


def test_cli_stdout_is_strict_json_and_does_not_write_target(tmp_path: Path) -> None:
    target = tmp_path / "repo"
    target.mkdir()
    _fixture_repo(target)
    before = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--root",
            str(target),
            "--git-commits",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    parsed = json.loads(completed.stdout)
    assert parsed["schema_version"] == "architect-repo-profile.v1"
    assert "NaN" not in completed.stdout and "Infinity" not in completed.stdout
    assert str(target) not in completed.stdout
    after = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
    assert after == before
