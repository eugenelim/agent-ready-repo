"""An invalid [catalogue.package].include entry is a CAT-PKG-001 diagnostic, not a traceback."""

from __future__ import annotations

from pathlib import Path


def _blank_catalogue(tmp_path: Path) -> Path:
    from agentbundle.catalogue_tooling.initialise import init_catalogue

    root = tmp_path / "cat"
    assert init_catalogue(target=root, name="demo-cat").ok
    return root


def test_include_entry_outside_packs_is_a_diagnostic(tmp_path: Path) -> None:
    from agentbundle.catalogue_tooling.package import package_catalogue

    root = _blank_catalogue(tmp_path)
    toml = root / "catalogue.toml"
    toml.write_text(
        toml.read_text(encoding="utf-8").replace("include  = []", 'include  = ["AGENTS.md"]'),
        encoding="utf-8",
    )
    out = tmp_path / "out"

    result = package_catalogue(
        root=root, bundle="demo", release="0.1.0", channel="stable", output=out,
    )

    assert not result.ok
    assert [d.code for d in result.diagnostics] == ["CAT-PKG-001"]
    assert "AGENTS.md" in result.diagnostics[0].message
    assert not out.exists()


def _set_include(root: Path, entries: list[str]) -> None:
    toml = root / "catalogue.toml"
    rendered = "[" + ", ".join(f'"{e}"' for e in entries) + "]"
    toml.write_text(
        toml.read_text(encoding="utf-8").replace("include  = []", f"include  = {rendered}"),
        encoding="utf-8",
    )


def _assert_single_diagnostic(tmp_path: Path, root: Path, entry: str) -> None:
    from agentbundle.catalogue_tooling.package import package_catalogue

    out = tmp_path / "out"
    result = package_catalogue(
        root=root, bundle="demo", release="0.1.0", channel="stable", output=out,
    )

    assert not result.ok
    assert [d.code for d in result.diagnostics] == ["CAT-PKG-001"]
    assert entry in result.diagnostics[0].message
    assert not out.exists()


def test_missing_include_entry_is_a_diagnostic(tmp_path: Path) -> None:
    root = _blank_catalogue(tmp_path)
    _set_include(root, ["packs/nope"])
    _assert_single_diagnostic(tmp_path, root, "packs/nope")


def test_build_residue_include_entry_is_a_diagnostic(tmp_path: Path) -> None:
    root = _blank_catalogue(tmp_path)
    (root / "packs" / "__pycache__").mkdir()
    _set_include(root, ["packs/__pycache__"])
    _assert_single_diagnostic(tmp_path, root, "packs/__pycache__")


def test_scaffold_template_include_entry_is_a_diagnostic(tmp_path: Path) -> None:
    root = _blank_catalogue(tmp_path)
    _set_include(root, ["packs/_example"])
    _assert_single_diagnostic(tmp_path, root, "packs/_example")


def test_bare_packs_include_entry_still_packages(tmp_path: Path) -> None:
    """`packs/` names the whole packs directory, so it walks every pack as before."""
    from agentbundle.catalogue_tooling.package import package_catalogue

    root = _blank_catalogue(tmp_path)
    _set_include(root, ["packs/"])

    result = package_catalogue(
        root=root, bundle="demo", release="0.1.0", channel="stable", output=tmp_path / "out",
    )

    assert result.ok, result.diagnostics


def test_cli_reports_bad_include_without_a_traceback(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys

    root = _blank_catalogue(tmp_path)
    _set_include(root, ["packs/nope"])
    env = os.environ.copy()
    package_root = Path(__file__).resolve().parents[2]
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(package_root), env.get("PYTHONPATH")]))
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        [
            sys.executable, "-m", "agentbundle", "catalogue", "package",
            "--root", str(root), "--bundle", "demo", "--release", "0.1.0",
            "--channel", "stable", "--output", str(tmp_path / "out"),
        ],
        env=env, capture_output=True, text=True, encoding="utf-8",
    )

    assert proc.returncode == 1, (proc.stdout, proc.stderr)
    assert "CAT-PKG-001" in proc.stderr
    assert "Traceback" not in proc.stderr
    assert "Traceback" not in proc.stdout


def test_underscore_directory_inside_a_real_pack_is_packaged(tmp_path: Path) -> None:
    import json
    import shutil
    import tarfile

    from agentbundle.catalogue_tooling.package import package_catalogue

    root = _blank_catalogue(tmp_path)
    pack = root / "packs" / "demo-pack"
    shutil.copytree(root / "packs" / "_example", pack)
    for rel in ("pack.toml", ".claude-plugin/plugin.json"):
        f = pack / rel
        if f.is_file():
            f.write_text(f.read_text(encoding="utf-8").replace("example-pack", "demo-pack"), encoding="utf-8")
    plugin = pack / ".claude-plugin" / "plugin.json"
    if plugin.is_file():
        assert json.loads(plugin.read_text(encoding="utf-8"))["name"] == "demo-pack"
    (pack / "_sub").mkdir()
    (pack / "_sub" / "note.md").write_text("note\n", encoding="utf-8")
    _set_include(root, ["packs/demo-pack"])
    out = tmp_path / "out"

    result = package_catalogue(
        root=root, bundle="demo", release="0.1.0", channel="stable", output=out,
    )

    assert result.ok, result.diagnostics
    archive = out / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(archive, "r:gz") as tf:
        names = set(tf.getnames())
    expected = {
        p.relative_to(root).as_posix() for p in pack.rglob("*") if p.is_file() and not p.is_symlink()
    }
    assert "packs/demo-pack/_sub/note.md" in expected
    assert expected <= names
