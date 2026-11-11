"""The Windows executable-path judgement, which runs on every host.

A Windows launch refuses an NTFS stream name and a UNC or device path before it
pins the executable's identity; the judgement itself is plain string logic.
"""

from __future__ import annotations

import importlib.util
import os
import stat
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"


def _load() -> ModuleType:
    path = Path(os.environ.get("PROCESS_SAFETY_UNDER_TEST", SCRIPTS / "_process_safety.py"))
    assert stat.S_ISREG(os.lstat(path).st_mode)
    name = "core_work_loop_process_safety_windows_paths"
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


@pytest.fixture(scope="module")
def ps() -> ModuleType:
    return _load()


@pytest.mark.parametrize("path", [
    r"C:\tools\tool.cmd::$DATA",
    r"C:\tools\tool.exe:hidden",
    r"C:\tools:stream\tool.exe",
    r"\\server\share\tool.exe",
    r"\\?\C:\tools\tool.exe",
    r"\\.\C:\tools\tool.exe",
    "//server/share/tool.exe",
])
def test_a_stream_name_or_a_network_or_device_path_is_unsafe(ps: ModuleType, path: str) -> None:
    assert ps._is_unsafe_windows_path(path)


@pytest.mark.parametrize("path", [
    r"C:\Program Files\Python\python.exe",
    "C:/tools/tool.exe",
    r"D:\a\b.exe",
])
def test_a_local_absolute_path_is_safe(ps: ModuleType, path: str) -> None:
    assert not ps._is_unsafe_windows_path(path)
