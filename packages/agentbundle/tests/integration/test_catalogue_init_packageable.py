"""A blank catalogue from `catalogue init` packages and verifies with no hand edits."""

from __future__ import annotations

import os
import subprocess
import sys
import tarfile
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(PACKAGE_ROOT), env.get("PYTHONPATH")]))
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-m", "agentbundle", *args],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_init_creates_root_agents_md_and_claude_shim(tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling.initialise import init_catalogue
    from agentbundle.catalogue_tooling.results import FileAction

    target = tmp_path / "cat"
    result = init_catalogue(target=target, name="demo-cat")

    assert result.ok, result.diagnostics
    assert (target / "AGENTS.md").is_file()
    assert (target / "CLAUDE.md").read_bytes() == b"@AGENTS.md\n"
    actions = {fp.path: fp.action for fp in result.files}
    assert actions["AGENTS.md"] == FileAction.CREATE
    assert actions["CLAUDE.md"] == FileAction.CREATE


def test_blank_catalogue_inits_verifies_packages_and_verifies_archive(tmp_path: Path) -> None:
    cat = tmp_path / "cat"
    out = tmp_path / "out"

    steps = [
        ("catalogue", "init", str(cat), "--name", "demo-cat"),
        ("catalogue", "verify", "--root", str(cat)),
        (
            "catalogue", "package", "--root", str(cat), "--bundle", "demo",
            "--release", "0.1.0", "--channel", "stable", "--output", str(out),
        ),
    ]
    for step in steps:
        proc = _cli(*step)
        assert proc.returncode == 0, (step, proc.stdout, proc.stderr)

    archive = out / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    sidecar = archive.with_name(archive.name + ".sha256")
    proc = _cli("catalogue", "verify", "--archive", str(archive), "--sha256-file", str(sidecar))
    assert proc.returncode == 0, (proc.stdout, proc.stderr)

    with tarfile.open(archive, "r:gz") as tf:
        names = tf.getnames()
    assert "AGENTS.md" in names
    assert not [n for n in names if n.startswith(("packs/_example/", "profiles/_example/"))]


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and not p.is_symlink()
    }


def test_root_agents_md_names_catalogue_and_links_exactly_three_files(tmp_path: Path) -> None:
    import re

    from agentbundle.catalogue_tooling.initialise import init_catalogue

    target = tmp_path / "cat"
    assert init_catalogue(target=target, name="demo-cat").ok
    text = (target / "AGENTS.md").read_text(encoding="utf-8")

    assert "demo-cat" in text
    links = re.findall(r"\]\(([^)]*)\)", text)
    assert sorted(links) == sorted([
        "packs/AGENTS.md",
        "profiles/AGENTS.md",
        "guides/_shared/reference/catalogue-authoring-standards.md",
    ])


def test_existing_root_files_are_kept_and_reported_already_present(tmp_path: Path) -> None:
    import hashlib

    from agentbundle.catalogue_tooling.initialise import init_catalogue
    from agentbundle.catalogue_tooling.results import FileAction

    target = tmp_path / "cat"
    target.mkdir()
    agents = b"# my own rules\n"
    claude = b"my own claude notes\n"
    (target / "AGENTS.md").write_bytes(agents)
    (target / "CLAUDE.md").write_bytes(claude)

    result = init_catalogue(target=target, name="demo-cat")

    assert result.ok, result.diagnostics
    assert (target / "AGENTS.md").read_bytes() == agents
    assert (target / "CLAUDE.md").read_bytes() == claude
    by_path = {fp.path: fp for fp in result.files}
    for rel, data in (("AGENTS.md", agents), ("CLAUDE.md", claude)):
        assert by_path[rel].action == FileAction.ALREADY_PRESENT
        assert by_path[rel].sha256 == hashlib.sha256(data).hexdigest()


def test_symlinked_root_agents_md_is_a_conflict_and_writes_nothing(tmp_path: Path) -> None:
    import pytest
    from agentbundle.catalogue_tooling.initialise import init_catalogue

    target = tmp_path / "cat"
    target.mkdir()
    real = tmp_path / "real.md"
    real.write_bytes(b"x\n")
    try:
        (target / "AGENTS.md").symlink_to(real)
    except OSError:
        pytest.skip("symlinks unavailable")
    before = _snapshot(target)

    result = init_catalogue(target=target, name="demo-cat")

    assert not result.ok
    assert any(d.code == "CAT-INIT-007" and d.path == "AGENTS.md" for d in result.diagnostics)
    assert _snapshot(target) == before


def test_changed_nested_guidance_file_still_conflicts(tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling.initialise import init_catalogue

    for rel in ("packs/AGENTS.md", "profiles/CLAUDE.md"):
        target = tmp_path / rel.replace("/", "-")
        (target / rel).parent.mkdir(parents=True)
        (target / rel).write_bytes(b"custom\n")
        before = _snapshot(target)

        result = init_catalogue(target=target, name="demo-cat")

        assert not result.ok, rel
        assert any(d.code == "CAT-INIT-007" and d.path == rel for d in result.diagnostics), rel
        assert _snapshot(target) == before, rel


def test_name_with_trailing_newline_is_refused(tmp_path: Path) -> None:
    """`$` matches before a final newline, so the name check must be a full match."""
    from agentbundle.catalogue_tooling.initialise import init_catalogue

    target = tmp_path / "cat"
    result = init_catalogue(target=target, name="foo\n")

    assert not result.ok
    assert [d.code for d in result.diagnostics] == ["CAT-INIT-003"]
    assert not target.exists()
