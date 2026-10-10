"""AC-0002: each byte-identical ``intent_graph.py`` copy binds its own helpers."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

_SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"
NAV = _SKILLS / "navigate-intents" / "scripts"
CW = _SKILLS / "close-work" / "scripts"


def _load(name: str, path: Path) -> ModuleType:
    """Load ``path`` under the unique module name ``name``."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_each_copy_binds_its_own_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-0002 — each copy's helper loaders resolve to its own scripts folder,
    in either load order."""
    for first, second in ((NAV, CW), (CW, NAV)):
        monkeypatch.setattr(sys, "modules", dict(sys.modules))
        mods = {
            d: _load(f"_t_ig_{d.parent.name}_{first.parent.name}", d / "intent_graph.py")
            for d in (first, second)
        }
        for d, m in mods.items():
            assert Path(m._get_file_safety().__file__).parent == d
            assert Path(m._get_resolver().__file__).parent == d
