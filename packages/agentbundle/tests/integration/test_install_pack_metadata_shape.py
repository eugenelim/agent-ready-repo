"""TOML-injection hardening: install-side defence-in-depth validator.

The structural fix is the `_emit_basic_string` escaping in
`config.dump_state` and `commands.install._append_install_marker`. The
validator here is the bell-rings-loud companion: at the install
boundary, refuse any pack.toml whose name / version / projection
relpaths fall outside their canonical grammars, with a spec-shaped
stderr line, before any write to either scope's state.
"""

from __future__ import annotations

import types
from pathlib import Path

import pytest


def _args(
    pack: str, catalogue: Path, output: Path
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        pack=pack,
        catalogue=str(catalogue),
        output=str(output),
    )


def _write_pack(
    catalogue_dir: Path,
    *,
    name_key: str,
    manifest_name: str,
    manifest_version: str,
) -> None:
    """Build a minimal pack at ``<catalogue_dir>/packs/<name_key>/``.

    ``manifest_name`` and ``manifest_version`` go into ``pack.toml`` — they
    can be adversarial strings; the directory name (``name_key``) is what
    ``_locate_pack`` looks up via ``args.pack``.

    The manifest is emitted via ``_emit_basic_string`` so the on-disk
    pack.toml is a TOML **basic** string (double-quoted, escapes
    interpreted by ``tomllib``). That round-trips an adversarial value
    like ``'0.1.0"\\nname = "evil"'`` to the same Python string with a
    real ``\\n`` byte after parsing — i.e., the historical injection
    payload. Writing the manifest via Python's ``repr()`` would produce
    a TOML *literal* string instead, where ``\\n`` stays two literal
    characters and the validator would never see the actual control
    char.
    """
    from agentbundle.config import _emit_basic_string

    pack_dir = catalogue_dir / "packs" / name_key
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "pack.toml").write_text(
        f"[pack]\n"
        f"name = {_emit_basic_string(manifest_name)}\n"
        f"version = {_emit_basic_string(manifest_version)}\n",
        encoding="utf-8",
    )


def test_install_refuses_malformed_pack_name(tmp_path, capsys):
    """A manifest declaring ``name = "../etc/passwd"`` (or anything
    outside ``^[a-z0-9][a-z0-9-]*$``) must refuse with the spec-shaped
    stderr line; no state file is written."""
    from agentbundle.commands.install import run

    catalogue = tmp_path / "catalogue"
    output = tmp_path / "repo"
    output.mkdir()
    _write_pack(
        catalogue,
        name_key="badname",
        manifest_name="../etc/passwd",
        manifest_version="0.1.0",
    )

    rc = run(_args("badname", catalogue, output))
    captured = capsys.readouterr()

    assert rc != 0, "install must refuse a malformed pack.name"
    assert "invalid" in captured.err.lower()
    assert "name" in captured.err.lower()
    # No state file landed before refusal.
    assert not (output / ".agentbundle-state.toml").exists()
    assert not (output / ".adapt-install-marker.toml").exists()


def test_install_refuses_malformed_pack_version(tmp_path, capsys):
    """A manifest declaring ``version = "not-semver"`` must refuse
    with a spec-shaped stderr line; no state file is written."""
    from agentbundle.commands.install import run

    catalogue = tmp_path / "catalogue"
    output = tmp_path / "repo"
    output.mkdir()
    _write_pack(
        catalogue,
        name_key="alpha",
        manifest_name="alpha",
        manifest_version="not-semver",
    )

    rc = run(_args("alpha", catalogue, output))
    captured = capsys.readouterr()

    assert rc != 0, "install must refuse a malformed pack.version"
    assert "invalid" in captured.err.lower()
    assert "version" in captured.err.lower()
    assert not (output / ".agentbundle-state.toml").exists()
    assert not (output / ".adapt-install-marker.toml").exists()


def test_install_refuses_pack_version_with_injection_payload(
    tmp_path, capsys
):
    """The canonical pre-existing-vulnerability payload (`version`
    contains TOML metacharacters) is precisely the case the validator
    must refuse before any TOML emitter sees it."""
    from agentbundle.commands.install import run

    catalogue = tmp_path / "catalogue"
    output = tmp_path / "repo"
    output.mkdir()
    _write_pack(
        catalogue,
        name_key="alpha",
        manifest_name="alpha",
        manifest_version='0.1.0"\nname = "evil"',
    )

    rc = run(_args("alpha", catalogue, output))
    captured = capsys.readouterr()

    assert rc != 0
    assert "invalid" in captured.err.lower()
    assert not (output / ".agentbundle-state.toml").exists()


def test_assert_pack_metadata_shape_refuses_projection_relpath_with_quote(
    tmp_path,
):
    """Unit-level check on the validator: a projection relpath that
    contains a quote, backslash, or control char must refuse.

    The full-install variant of this test is gated on whether
    ``render_pack`` allows such a relpath through; the helper itself
    is the load-bearing line of defence and we pin its behaviour here
    independently."""
    from agentbundle.commands.install import _assert_pack_metadata_shape

    pack_toml = {"pack": {"name": "alpha", "version": "0.1.0"}}
    adversarial_projection = {'AGENTS.md"\nx = "y': b"hi"}

    with pytest.raises(RuntimeError, match="invalid"):
        _assert_pack_metadata_shape(pack_toml, projection=adversarial_projection)


def test_assert_pack_metadata_shape_refuses_relpath_with_backslash():
    from agentbundle.commands.install import _assert_pack_metadata_shape

    pack_toml = {"pack": {"name": "alpha", "version": "0.1.0"}}
    with pytest.raises(RuntimeError, match="invalid"):
        _assert_pack_metadata_shape(
            pack_toml, projection={"AGENTS\\.md": b"x"}
        )


def test_assert_pack_metadata_shape_refuses_relpath_with_control_char():
    from agentbundle.commands.install import _assert_pack_metadata_shape

    pack_toml = {"pack": {"name": "alpha", "version": "0.1.0"}}
    with pytest.raises(RuntimeError, match="invalid"):
        _assert_pack_metadata_shape(
            pack_toml, projection={"AGENTS\x01.md": b"x"}
        )


def test_assert_pack_metadata_shape_accepts_canonical_inputs():
    """The happy path: legal name, legal version, legal relpaths."""
    from agentbundle.commands.install import _assert_pack_metadata_shape

    pack_toml = {"pack": {"name": "core", "version": "1.2.3"}}
    _assert_pack_metadata_shape(
        pack_toml,
        projection={
            "AGENTS.md": b"x",
            "docs/CHARTER.md": b"y",
            ".claude/skills/work-loop/SKILL.md": b"z",
        },
    )


@pytest.mark.parametrize(
    "version",
    [
        "0.1.0",
        "1.2.3",
        "10.20.30",
        "0.1.0-alpha",
        "0.1.0-alpha.1",
        "1.0.0+build.1",
    ],
)
def test_assert_pack_metadata_shape_accepts_semver_versions(version):
    from agentbundle.commands.install import _assert_pack_metadata_shape

    _assert_pack_metadata_shape(
        {"pack": {"name": "core", "version": version}}
    )


@pytest.mark.parametrize(
    "version",
    [
        "",
        "0",
        "0.1",
        "v0.1.0",
        "0.1.0 ",
        " 0.1.0",
        "not-semver",
        "0.1.0\n",
        '0.1.0"',
    ],
)
def test_assert_pack_metadata_shape_refuses_non_semver_versions(version):
    from agentbundle.commands.install import _assert_pack_metadata_shape

    with pytest.raises(RuntimeError, match="invalid"):
        _assert_pack_metadata_shape(
            {"pack": {"name": "core", "version": version}}
        )


@pytest.mark.parametrize(
    "name",
    [
        "core",
        "agentbundle",
        "user-guide-diataxis",
        "a",
        "a1",
        "0core",
    ],
)
def test_assert_pack_metadata_shape_accepts_canonical_pack_names(name):
    from agentbundle.commands.install import _assert_pack_metadata_shape

    _assert_pack_metadata_shape(
        {"pack": {"name": name, "version": "0.1.0"}}
    )


@pytest.mark.parametrize(
    "name",
    [
        "",
        "-core",
        "Core",
        "core_pack",
        "core pack",
        "../etc/passwd",
        "core/sub",
        'core"',
        "core\n",
    ],
)
def test_assert_pack_metadata_shape_refuses_malformed_pack_names(name):
    from agentbundle.commands.install import _assert_pack_metadata_shape

    with pytest.raises(RuntimeError, match="invalid"):
        _assert_pack_metadata_shape(
            {"pack": {"name": name, "version": "0.1.0"}}
        )
