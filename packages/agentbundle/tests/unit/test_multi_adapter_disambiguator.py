"""T4: multi-adapter disambiguator names each adapter's version (AC8).

`upgrade`, `diff`, and `uninstall` all refuse with "pass --adapter" when a pack
is installed for more than one adapter at the resolved scope and none is named.
The refusal now lists each adapter *with its installed version* so the next
command is actionable without a second lookup.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from agentbundle.commands import diff, uninstall, upgrade
from agentbundle.commands._common import format_adapter_versions
from agentbundle.config import PackState, State, dump_state


def test_format_adapter_versions_sorted_pairs():
    rows = {
        "codex": PackState(installed_version="0.9.0"),
        "claude-code": PackState(installed_version="0.8.1"),
    }
    assert format_adapter_versions(rows) == "claude-code (0.8.1), codex (0.9.0)"


def _two_adapter_state() -> State:
    return State(
        packs={
            ("foo", "claude-code"): PackState(installed_version="0.9.0"),
            ("foo", "codex"): PackState(installed_version="0.8.0"),
        }
    )


def _write_repo_state(root: Path) -> None:
    (root / ".agentbundle-state.toml").write_text(
        dump_state(_two_adapter_state()), encoding="utf-8"
    )


def test_upgrade_disambiguator_includes_versions(tmp_path, capsys):
    _write_repo_state(tmp_path)
    args = SimpleNamespace(
        pack="foo", skill=None, agent=None, hook=None, seed=None, command=None,
        catalogue=None, root=str(tmp_path), scope="repo", adapter=None,
        yes=False, dry_run=False,
    )
    rc = upgrade.run(args)
    err = capsys.readouterr().err
    assert rc == 1
    assert "pass --adapter to pick one:" in err
    assert "claude-code (0.9.0)" in err and "codex (0.8.0)" in err


def test_uninstall_disambiguator_includes_versions(tmp_path, capsys):
    _write_repo_state(tmp_path)
    args = SimpleNamespace(
        pack="foo", root=str(tmp_path), scope="repo", adapter=None,
        yes=False, dry_run=False,
    )
    rc = uninstall.run(args)
    err = capsys.readouterr().err
    assert rc == 1
    assert "pass --adapter to pick one:" in err
    assert "claude-code (0.9.0)" in err and "codex (0.8.0)" in err


def test_diff_disambiguator_includes_versions(tmp_path, capsys):
    _write_repo_state(tmp_path)
    pack_dir = tmp_path / "pack"
    pack_dir.mkdir()
    (pack_dir / "pack.toml").write_text(
        '[pack]\nname = "foo"\nversion = "0.9.0"\n', encoding="utf-8"
    )
    args = SimpleNamespace(
        pack_path=str(pack_dir), root=str(tmp_path), scope="repo", adapter=None,
    )
    rc = diff.run(args)
    err = capsys.readouterr().err
    assert rc == 1
    assert "pass --adapter to pick one:" in err
    assert "claude-code (0.9.0)" in err and "codex (0.8.0)" in err
