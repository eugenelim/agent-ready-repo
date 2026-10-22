"""Every contract a catalogue command reads comes from the bundled copy.

Each command runs in a fresh subprocess under a recorder that logs the real path
of every file it opens. Invalid copies of every manifest contract are planted
beside the catalogue and inside it, so a read from either would be visible. The
recorded contract reads must resolve under the package's `_data/` (AC 16) and
must be a specification member or a named exclusion (AC 17).

Spec: the catalogue-spec-manifest feature (ACs 16 and 17).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
_SYNC = REPO / "tools" / "catalogue" / "sync_contract_inventory.py"
_PACKAGE_DIR = REPO / "packages" / "agentbundle" / "agentbundle"
_DATA = (_PACKAGE_DIR / "_data").resolve()

_CLASSES = {"host projection", "engine setting", "other record"}

# Bundled or vendored contracts a command may read from `_data/` without being a
# specification member, each with the reason it is not a member.
EXCLUSIONS: dict[str, str] = {
    "marketplace-entry.schema.json": "host projection",
    "plugin-manifest.derived.schema.json": "host projection",
    "vendor/agent-plugins/1.0.0/plugin.schema.json": "host projection",
    "distribution-routes.toml": "engine setting",
    "distribution-routes.schema.json": "engine setting",
}

_RECORDER = r"""
import fcntl, json, os, sys

_paths = set()
_real_open = os.open


def _note(path):
    if isinstance(path, (str, bytes, os.PathLike)):
        _paths.add(os.path.realpath(os.path.abspath(os.fsdecode(path))))


def _descriptor_path(fd):
    if sys.platform == "darwin":
        buf = fcntl.fcntl(fd, fcntl.F_GETPATH, b"\0" * 1024)
        return os.fsdecode(buf.split(b"\0", 1)[0])
    return os.readlink(f"/proc/self/fd/{fd}")


def _open(path, *args, **kwargs):
    fd = _real_open(path, *args, **kwargs)
    try:
        _paths.add(os.path.realpath(_descriptor_path(fd)))
    except OSError:
        _note(path)
    return fd


def _hook(event, args):
    if event == "open":
        _note(args[0])


os.open = _open
sys.addaudithook(_hook)

from agentbundle.cli import main

try:
    code = main(json.loads(os.environ["RECORDER_ARGV"]))
except SystemExit as exc:
    code = exc.code
finally:
    with open(os.environ["RECORDER_OUT"], "w") as handle:
        json.dump(sorted(_paths), handle)
sys.exit(code)
"""


def _manifest_rows():
    spec = importlib.util.spec_from_file_location("sync_contract_inventory", _SYNC)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.load_manifest(REPO / "contracts")


def _plant(contracts: Path, rows) -> None:
    for row in rows:
        target = contracts / row.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("planted invalid copy, not a contract\n", encoding="utf-8")


def _is_contract_read(path: str, rows) -> bool:
    posix = Path(path).as_posix()
    for row in rows:
        if row.role == "vendored":
            if posix.endswith("/" + row.path):
                return True
        elif Path(path).name == row.data_name:
            return True
    return False


@pytest.fixture(scope="module")
def recorded(tmp_path_factory: pytest.TempPathFactory) -> dict[str, list[str]]:
    rows = _manifest_rows()
    parent = tmp_path_factory.mktemp("parent")
    cat = parent / "cat"
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    init = subprocess.run(
        [sys.executable, "-m", "agentbundle", "catalogue", "init", str(cat)],
        capture_output=True,
        text=True,
        env=env,
        cwd=parent,
    )
    assert init.returncode == 0, init.stdout + init.stderr
    _plant(parent / "contracts", rows)

    commands = {
        "package": [
            "catalogue",
            "package",
            "--root",
            str(cat),
            "--bundle",
            "probe",
            "--release",
            "0.0.1",
            "--channel",
            "stable",
            "--output",
            str(parent / "out"),
        ],
        "lint": ["catalogue", "lint", "--root", str(cat)],
        "verify": ["catalogue", "verify", "--root", str(cat)],
        "index": ["catalogue", "index", "--root", str(cat), "--dry-run"],
    }
    results: dict[str, list[str]] = {}
    for name, argv in commands.items():
        if name == "lint":
            # `package` archives the catalogue's own folder, so it runs before
            # the catalogue-root contracts/ folder exists and the rest after.
            _plant(cat / "contracts", rows)
        out = parent / f"{name}.json"
        run_env = {**env, "RECORDER_ARGV": json.dumps(argv), "RECORDER_OUT": str(out)}
        subprocess.run(
            [sys.executable, "-c", _RECORDER],
            capture_output=True,
            text=True,
            env=run_env,
            cwd=parent,
        )
        assert out.is_file(), f"{name} recorded nothing"
        results[name] = json.loads(out.read_text(encoding="utf-8"))
    return results


def _reads(recorded: dict[str, list[str]], command: str) -> list[str]:
    rows = _manifest_rows()
    return [p for p in recorded[command] if _is_contract_read(p, rows)]


@pytest.mark.parametrize("command", ["lint", "verify", "package", "index"])
def test_each_command_reads_a_contract(recorded, command: str) -> None:
    assert _reads(recorded, command), f"{command} recorded no contract read"


@pytest.mark.parametrize("command", ["lint", "verify", "package", "index"])
def test_contract_reads_resolve_under_bundled_data(recorded, command: str) -> None:
    outside = [p for p in _reads(recorded, command) if not Path(p).is_relative_to(_DATA)]
    assert not outside, f"{command} read contracts outside {_DATA}: {outside}"


@pytest.mark.parametrize("command", ["lint", "verify", "package", "index"])
def test_contract_reads_are_members_or_exclusions(recorded, command: str) -> None:
    rows = _manifest_rows()
    members = {r.data_name for r in rows if r.role == "member"}
    unexplained = []
    for path in _reads(recorded, command):
        relative = (
            Path(path).relative_to(_DATA).as_posix() if Path(path).is_relative_to(_DATA) else path
        )
        if relative not in members and relative not in EXCLUSIONS:
            unexplained.append(relative)
    assert not unexplained, f"{command} read non-member contracts with no exclusion: {unexplained}"


def test_exclusions_are_bundled_or_vendored_rows_with_known_classes() -> None:
    rows = {r.data_name: r.role for r in _manifest_rows()}
    for name, reason in EXCLUSIONS.items():
        assert rows.get(name) in {"bundled", "vendored"}, name
        assert reason in _CLASSES, (name, reason)
