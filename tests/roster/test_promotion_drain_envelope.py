"""Roster coverage for the drain's execution envelope (spec § D7–§ D9).

Spec: ``docs/specs/work-item-promotion-handoff`` — task T3. A stored
verification command runs confined (every member of the stored-path set
resolved against the repository root, symlinks followed), neutralised (no
inherited environment, standard input closed, ``LC_ALL=C`` pinned, tool
locations resolved without ambient ``PATH``), capped (10 s wall clock,
64 KiB captured output), under ``-F`` for ``grep``, and its output crosses
toward any durable sink only through § D8's privacy-scan seam, reaching
presentation as delimited data.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = (
    REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "project-knowledge" / "scripts"
)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DRAIN = _load_module("_roster_promotion_drain_envelope", SCRIPTS_DIR / "promotion_drain.py")


def _write_script(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def _fake_env_dump_cat(marker: Path) -> Path:
    """A stand-in `cat` that records its environment and stdin state."""
    return _write_script(
        marker.with_name(marker.name + ".fake-cat"),
        "#!/bin/sh\n"
        f"/usr/bin/env > {marker}\n"
        f"if read -r _line; then printf 'stdin-open\\n' >> {marker}; "
        f"else printf 'stdin-closed\\n' >> {marker}; fi\n"
        "printf 'fake output\\n'\n",
    )


def _fake_sleeper(repo: Path) -> Path:
    return _write_script(
        repo.with_name(repo.name + "-sleeper"),
        "#!/bin/sh\n/bin/sleep 30\n",
    )


def test_symlink_resolving_outside_the_repository_refuses_the_command(
    git_repo: Path,
) -> None:
    (git_repo / "real.txt").write_text("inside\n", encoding="utf-8")
    (git_repo / "alias.txt").symlink_to(git_repo / "real.txt")
    (git_repo / "final.txt").symlink_to("/etc/passwd")
    (git_repo / "outside").symlink_to("/tmp")

    cases = [
        ({"command": ["cat", "final.txt"], "path": "real.txt"}, "final.txt"),
        ({"command": ["cat", "outside/x.md"], "path": "real.txt"}, "outside/x.md"),
        ({"command": ["ls", "docs", "outside"], "path": "real.txt"}, "outside"),
        ({"command": ["cat", "real.txt"], "path": "final.txt"}, "final.txt"),
    ]
    for route, member in cases:
        result = DRAIN.run_stored_command(git_repo, route)
        assert result["outcome"] == "refused", (route, result)
        assert result["refusal"] == {"control": "confinement", "member": member}

    # A symlink pointing inside the repository is not refused.
    admitted = DRAIN.run_stored_command(
        git_repo, {"command": ["cat", "alias.txt"], "path": "real.txt"}
    )
    assert admitted["outcome"] == "completed"
    assert admitted["exit_status"] == 0
    assert admitted["output"] == "inside\n"


def test_subprocess_environment_is_neutralised_and_stdin_closed(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (git_repo / "x.txt").write_text("content\n", encoding="utf-8")
    marker = git_repo.with_name(git_repo.name + "-marker.txt")
    marker.unlink(missing_ok=True)
    fake_cat = _fake_env_dump_cat(marker)
    poison_dir = git_repo.with_name(git_repo.name + "-poison-bin")
    poison_dir.mkdir()
    _write_script(poison_dir / "cat", "#!/bin/sh\nprintf 'poisoned\\n'\n")
    for name, value in (
        ("PATH", str(poison_dir)),
        ("HOME", str(git_repo.parent / "poison-home")),
        ("GIT_DIR", str(git_repo.parent / "poison-git")),
        ("GIT_CONFIG_GLOBAL", str(git_repo.parent / "poison-gitconfig")),
        ("LANG", "en_US.UTF-8"),
        ("LC_ALL", "en_US.UTF-8"),
    ):
        monkeypatch.setenv(name, value)

    result = DRAIN.run_stored_command(
        git_repo,
        {"command": ["cat", "x.txt"], "path": "x.txt"},
        tool_locations={"cat": str(fake_cat)},
    )

    assert result["outcome"] == "completed"
    assert result["exit_status"] == 0
    lines = marker.read_text(encoding="utf-8").splitlines()
    assert lines[-1] == "stdin-closed"
    # The shell adds its own bookkeeping (PWD, SHLVL, _); what must not
    # appear is any of the poisoned ambient keys, and LC_ALL is pinned.
    env_lines = lines[:-1]
    env_keys = {line.partition("=")[0] for line in env_lines}
    assert "LC_ALL=C" in env_lines
    assert not (env_keys & {"PATH", "HOME", "LANG", "GIT_DIR", "GIT_CONFIG_GLOBAL"})


def test_tool_resolution_ignores_a_poisoned_ambient_path(
    git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (git_repo / "x.txt").write_text("real content\n", encoding="utf-8")
    locations = DRAIN.default_tool_locations()
    if "cat" not in locations:
        pytest.skip("cat not found in the declared tool locations")
    poison_dir = git_repo.with_name(git_repo.name + "-poison-bin")
    poison_dir.mkdir()
    _write_script(poison_dir / "cat", "#!/bin/sh\nprintf 'poisoned\\n'\n")
    monkeypatch.setenv("PATH", str(poison_dir))

    result = DRAIN.run_stored_command(
        git_repo, {"command": ["cat", "x.txt"], "path": "x.txt"}
    )

    assert result["outcome"] == "completed"
    assert result["output"] == "real content\n"


def test_wall_clock_cap_terminates_the_command(git_repo: Path) -> None:
    (git_repo / "x.txt").write_text("content\n", encoding="utf-8")
    sleeper = _fake_sleeper(git_repo)

    result = DRAIN.run_stored_command(
        git_repo,
        {"command": ["cat", "x.txt"], "path": "x.txt"},
        tool_locations={"cat": str(sleeper)},
        wall_clock_seconds=0.5,
    )

    assert result["outcome"] == "wall_clock_exceeded"
    assert result["exit_status"] is None


def test_output_cap_truncates_and_flags(git_repo: Path) -> None:
    locations = DRAIN.default_tool_locations()
    if "cat" not in locations:
        pytest.skip("cat not found in the declared tool locations")
    (git_repo / "big.txt").write_bytes(b"x" * 131072)

    result = DRAIN.run_stored_command(
        git_repo, {"command": ["cat", "big.txt"], "path": "big.txt"}
    )

    assert result["outcome"] == "completed"
    assert result["exit_status"] == 0
    assert len(result["output"].encode("utf-8")) == 65536
    assert result["output_truncated"] is True


def test_grep_patterns_match_literals_under_F(git_repo: Path) -> None:
    locations = DRAIN.default_tool_locations()
    if "grep" not in locations:
        pytest.skip("grep not found in the declared tool locations")
    (git_repo / "lines.txt").write_text(
        "a.b\naxb\na+b\naab\n", encoding="utf-8"
    )

    for pattern, expected in (("a.b", "a.b\n"), ("a+b", "a+b\n")):
        result = DRAIN.run_stored_command(
            git_repo,
            {"command": ["grep", pattern, "lines.txt"], "path": "lines.txt"},
        )
        assert result["outcome"] == "completed"
        assert result["exit_status"] == 0
        assert result["output"] == expected, pattern


def test_output_is_privacy_scanned_at_the_durable_write_seam() -> None:
    dirty = "the token Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 leaked"
    assert DRAIN.scan_output_for_durable_write(dirty) == {
        "verdict": "refused",
        "control": "privacy_scan",
    }
    assert DRAIN.scan_output_for_durable_write("clean output") == {"verdict": "pass"}


def test_output_presentation_frames_bytes_as_delimited_data() -> None:
    dirty = "the token Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 leaked"
    message = DRAIN.render_output_presentation(dirty)
    instruction_region, _, rest = message.partition(
        DRAIN.KS.PK.REASONING_DISPATCH_DATA_START
    )
    data_region = rest.partition(DRAIN.KS.PK.REASONING_DISPATCH_DATA_END)[0]
    assert message.startswith(DRAIN.OUTPUT_PRESENTATION_INSTRUCTION)
    assert dirty in data_region
    assert dirty not in instruction_region
