"""Public ingress surfaces reject hazardous Claude-shaped wiring pre-write."""

from __future__ import annotations

import argparse
import contextlib
import io
import tomllib
from pathlib import Path
from types import SimpleNamespace

import pytest
from agentbundle import config
from agentbundle.build.adapters import claude_code
from agentbundle.build.lint_packs import lint_pack
from agentbundle.build.main import _read_bundled
from agentbundle.commands import diff, init_state, install, render, upgrade, validate
from agentbundle.render import render_pack_to_dir


def _hazardous_pack(tmp_path: Path, *, consent: bool = True) -> Path:
    pack = tmp_path / "hazardous"
    (pack / ".apm" / "hooks").mkdir(parents=True)
    (pack / ".apm" / "hook-wiring").mkdir(parents=True)
    (pack / ".apm" / "hooks" / "run.py").write_text("pass\n", encoding="utf-8")
    (pack / ".apm" / "hook-wiring" / "run.toml").write_text(
        "[[hooks.SessionStart]]\n"
        'hooks = [{ type = "command", command = '
        '"python3 -c tools/hooks/run.py" }]\n',
        encoding="utf-8",
    )
    pack_toml = (
        "[pack]\n"
        'name = "hazardous"\n'
        'version = "0.1.0"\n'
        'description = "hazardous fixture"\n'
        "[pack.adapter-contract]\n"
        'version = "0.18"\n'
        "[pack.install]\n"
        'default-scope = "user"\n'
        'allowed-scopes = ["repo", "user"]\n'
        'allowed-adapters = ["claude-code"]\n'
    )
    if consent:
        pack_toml += "user-scope-hooks = true\n"
    (pack / "pack.toml").write_text(
        pack_toml,
        encoding="utf-8",
    )
    plugin = pack / ".claude-plugin"
    plugin.mkdir()
    (plugin / "plugin.json").write_text(
        '{"name":"hazardous","version":"0.1.0",'
        '"description":"hazardous fixture"}\n',
        encoding="utf-8",
    )
    return pack


def test_validate_cli_rejects_hazardous_command(tmp_path: Path) -> None:
    pack = _hazardous_pack(tmp_path)
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        rc = validate.run(argparse.Namespace(pack_path=str(pack), strict=False))
    assert rc == 1
    assert "python3 -c" in stderr.getvalue()
    assert "run.toml" in stderr.getvalue()


def _run_public_consumer(name: str, tmp_path: Path) -> tuple[int, Path]:
    catalogue = tmp_path / "catalogue"
    pack = _hazardous_pack(catalogue / "packs")
    output = tmp_path / "output"
    if name == "render":
        return render.run(
            SimpleNamespace(
                pack_path=str(pack),
                output=str(output),
                target=None,
                self_host=False,
            )
        ), output
    if name == "install":
        return install.run(
            SimpleNamespace(
                pack="hazardous",
                profile=None,
                catalogue=str(catalogue),
                output=str(output),
                scope="repo",
                adapter=None,
                emit_install_routes=True,
                dry_run=True,
                force=False,
                force_merge=False,
                yes=True,
            )
        ), output
    if name == "upgrade":
        output.mkdir()
        state = config.State()
        state.packs[("hazardous", "claude-code")] = config.PackState(
            installed_version="0.0.1",
            adapter="claude-code",
            files={
                "apm/hazardous/pack.toml": {
                    "sha": "deadbeef",
                    "from-pack-version": "0.0.1",
                }
            },
        )
        state_path = output / ".agentbundle-state.toml"
        state_path.write_text(config.dump_state(state), encoding="utf-8")
        before = state_path.read_bytes()
        result = upgrade.run(
            SimpleNamespace(
                pack="hazardous",
                all=False,
                catalogue=str(catalogue),
                root=str(output),
                scope="repo",
                adapter=None,
                skill=None,
                agent=None,
                hook=None,
                seed=None,
                command=None,
                format="table",
                dry_run=True,
                yes=True,
                _user_config=None,
            )
        )
        assert state_path.read_bytes() == before
        return result, output
    if name == "diff":
        return diff.run(
            SimpleNamespace(
                pack_path=str(pack),
                root=str(output),
                scope=None,
                adapter=None,
            )
        ), output
    if name == "validate":
        return validate.run(
            SimpleNamespace(pack_path=str(pack), strict=False)
        ), output
    if name == "init-state":
        return init_state.run(
            SimpleNamespace(
                pack="hazardous",
                packs_dir=str(catalogue / "packs"),
                root=str(output),
                migrate=False,
                scope=None,
            )
        ), output
    raise AssertionError(f"unknown consumer fixture {name}")


@pytest.mark.parametrize(
    "consumer",
    ("render", "install", "upgrade", "diff", "validate", "init-state"),
)
def test_every_render_pack_consumer_rejects_before_projection(
    consumer: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A plugin-route pack is refused before adapter dispatch.

    The fixture qualifies for the Claude-plugin route. Adapter parametrization
    is intentionally inapplicable: reaching an adapter is the failure this test
    guards against.
    """
    rc, output = _run_public_consumer(consumer, tmp_path)
    captured = capsys.readouterr()
    assert rc == 1
    assert "python3 -c" in captured.err
    assert "run.toml" in captured.err
    projected = [
        path
        for path in output.rglob("*")
        if path.is_file() and path.name != ".agentbundle-state.toml"
    ] if output.exists() else []
    assert projected == []


def test_render_boundary_rejects_before_output_creation(tmp_path: Path) -> None:
    pack = _hazardous_pack(tmp_path)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match=r"run\.toml.*command"):
        render_pack_to_dir(pack, output)
    assert not output.exists()


def test_plugin_route_requires_hook_consent_before_output_creation(
    tmp_path: Path,
) -> None:
    pack = _hazardous_pack(tmp_path, consent=False)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match=r"user-scope-hooks = true"):
        render_pack_to_dir(pack, output)
    assert not output.exists()


def test_direct_adapter_preserves_its_existing_wiring_contract(tmp_path: Path) -> None:
    pack = _hazardous_pack(tmp_path, consent=False)
    output = tmp_path / "direct"
    contract = tomllib.loads(_read_bundled("adapter.toml"))
    claude_code.project(pack, contract, output)
    settings = output / ".claude" / "settings.local.json"
    assert settings.is_file()
    assert "python3 -c tools/hooks/run.py" in settings.read_text(encoding="utf-8")


def test_repository_lint_converts_compiler_raise_to_finding(tmp_path: Path) -> None:
    pack = _hazardous_pack(tmp_path)
    findings = lint_pack(pack)
    assert len(findings) == 1
    assert "python3 -c" in findings[0]
