"""Cross-adapter self-host metadata-preservation regressions."""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path

import pytest
from agentbundle.build import projection_io
from agentbundle.build.adapters import registry
from agentbundle.build.contract import load as load_contract
from agentbundle.build.self_host import _project_seeds
from agentbundle.scope import shipped_adapters_from_contract

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PACKAGE_ROOT / "agentbundle" / "_data" / "adapter.toml"
_SHIPPED_ADAPTERS = shipped_adapters_from_contract()


def _seed_hook_pack(root: Path) -> tuple[Path, Path]:
    pack = root / "core"
    hook = pack / ".apm" / "hooks" / "cross-owner.py"
    hook.parent.mkdir(parents=True)
    hook.write_bytes(b"print('first')\n")
    (pack / "pack.toml").write_text(
        "[pack]\n"
        'name = "core"\n'
        'version = "0.0.0"\n'
        "[pack.adapter-contract]\n"
        'version = "0.18"\n'
        "[pack.install]\n"
        'default-scope = "repo"\n'
        'allowed-scopes = ["repo"]\n',
        encoding="utf-8",
        newline="\n",
    )
    return pack, hook


@pytest.mark.parametrize("adapter", _SHIPPED_ADAPTERS)
def test_existing_direct_file_preserves_metadata_for_every_shipped_adapter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    adapter: str,
) -> None:
    contract = load_contract(CONTRACT_PATH)
    pack, source = _seed_hook_pack(tmp_path / "packs")
    output = tmp_path / "output"
    output.mkdir()
    adapter_module = registry[adapter.replace("-", "_")]
    adapter_module.project_packs([pack], contract, output)
    projected = [
        path
        for path in output.rglob("*")
        if path.is_file() and path.read_bytes() == b"print('first')\n"
    ]
    assert len(projected) == 1, (adapter, projected)
    target = projected[0]
    if os.name == "posix":
        target.chmod(0o664)
    before = target.stat()
    source.write_bytes(b"print('second')\n")

    def deny_metadata(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("metadata denied")

    monkeypatch.setattr(projection_io.shutil, "copymode", deny_metadata)
    monkeypatch.setattr(projection_io.shutil, "copystat", deny_metadata)
    monkeypatch.setattr(projection_io.os, "utime", deny_metadata)
    monkeypatch.setattr(projection_io.os, "chmod", deny_metadata)
    if hasattr(projection_io.os, "fchmod"):
        monkeypatch.setattr(projection_io.os, "fchmod", deny_metadata)
    adapter_module.project_packs(
        [pack],
        contract,
        output,
        preserve_existing_metadata=True,
    )

    after = target.stat()
    assert target.read_bytes() == b"print('second')\n"
    if sys.platform != "win32":
        assert stat.S_IMODE(after.st_mode) == stat.S_IMODE(before.st_mode)
        assert after.st_ino == before.st_ino
        assert after.st_uid == before.st_uid
        assert after.st_gid == before.st_gid


def test_existing_seed_file_preserves_metadata(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Seed projection is adapter-independent and needs no adapter matrix."""
    packs_dir = tmp_path / "packs"
    pack = packs_dir / "core"
    source = pack / "seeds" / "projected.txt"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"seed replacement\n")
    (pack / "pack.toml").write_text(
        '[pack]\nname = "core"\nversion = "0.0.0"\n',
        encoding="utf-8",
        newline="\n",
    )
    output = tmp_path / "output"
    output.mkdir()
    target = output / "projected.txt"
    target.write_bytes(b"existing\n")
    if os.name == "posix":
        target.chmod(0o664)
    before = target.stat()

    def deny_metadata(*_args: object, **_kwargs: object) -> None:
        raise PermissionError("metadata denied")

    monkeypatch.setattr(projection_io.shutil, "copymode", deny_metadata)
    monkeypatch.setattr(projection_io.shutil, "copystat", deny_metadata)
    monkeypatch.setattr(projection_io.os, "utime", deny_metadata)
    monkeypatch.setattr(projection_io.os, "chmod", deny_metadata)
    if hasattr(projection_io.os, "fchmod"):
        monkeypatch.setattr(projection_io.os, "fchmod", deny_metadata)
    _project_seeds(
        packs_dir,
        output,
        preserve_existing_metadata=True,
    )

    after = target.stat()
    assert target.read_bytes() == b"seed replacement\n"
    if sys.platform != "win32":
        assert stat.S_IMODE(after.st_mode) == stat.S_IMODE(before.st_mode)
        assert after.st_ino == before.st_ino
        assert after.st_uid == before.st_uid
        assert after.st_gid == before.st_gid
