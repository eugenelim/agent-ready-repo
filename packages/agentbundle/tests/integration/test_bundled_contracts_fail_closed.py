"""A relocated copy of the package fails closed when a bundled contract is gone.

The copy sits at `<tmp>/cat/x/y/agentbundle`, so four parent folders above its
`build/` folder is `<tmp>/cat`. That catalogue holds invalid `contracts/`
copies of three contracts; none may be used in place of the bundled file.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import agentbundle
import pytest

_BOOTSTRAP = """
import os, runpy, sys
sys.path.insert(0, os.environ["COPY_SITE"])
import agentbundle
assert os.path.realpath(agentbundle.__file__).startswith(
    os.path.realpath(os.environ["COPY_SITE"])
), agentbundle.__file__
sys.argv = ["agentbundle"] + sys.argv[1:]
mode = os.environ["MODE"]
if mode == "lint-packs":
    import argparse
    from agentbundle.build.lint_packs import cmd_lint_packs
    raise SystemExit(cmd_lint_packs(argparse.Namespace(packs_dir=os.environ["PACKS_DIR"])))
runpy.run_module("agentbundle", run_name="__main__")
"""


@pytest.fixture()
def relocated(tmp_path: Path) -> dict[str, Path]:
    cat = tmp_path / "cat"
    site = cat / "x" / "y"
    site.mkdir(parents=True)
    source = Path(agentbundle.__file__).resolve().parent
    shutil.copytree(source, site / "agentbundle", ignore=shutil.ignore_patterns("__pycache__"))
    contracts = cat / "contracts"
    contracts.mkdir()
    for name in ("adapter.toml", "target-vocab.toml", "pack.schema.json"):
        (contracts / name).write_text("{ invalid [[[\n", encoding="utf-8", newline="\n")
    pack = tmp_path / "packs" / "demo"
    pack.mkdir(parents=True)
    (pack / "pack.toml").write_text(
        '[pack]\nname = "demo"\nversion = "0.1.0"\ndescription = "d"\n',
        encoding="utf-8",
        newline="\n",
    )
    return {"site": site, "pack": pack, "packs": pack.parent}


def _run(mode: str, relocated: dict[str, Path], *argv: str) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.update(
        COPY_SITE=str(relocated["site"]),
        MODE=mode,
        PACKS_DIR=str(relocated["packs"]),
        PYTHONIOENCODING="utf-8",
        PYTHONUTF8="1",
    )
    return subprocess.run(
        [sys.executable, "-c", _BOOTSTRAP, *argv],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )


@pytest.mark.parametrize(
    ("mode", "removed", "argv"),
    [
        ("cli", "adapter.toml", ("--version",)),
        ("lint-packs", "target-vocab.toml", ()),
        ("cli", "pack.schema.json", ("validate", "@pack")),
    ],
)
def test_missing_bundled_contract_fails_closed(
    relocated: dict[str, Path], mode: str, removed: str, argv: tuple[str, ...]
) -> None:
    (relocated["site"] / "agentbundle" / "_data" / removed).unlink()
    args = tuple(str(relocated["pack"]) if a == "@pack" else a for a in argv)
    result = _run(mode, relocated, *args)
    assert result.returncode != 0, result.stdout + result.stderr
    assert f"_data/{removed}" in result.stdout + result.stderr
