"""AC-0002: each byte-identical ``intent_graph.py`` copy binds its own helpers."""
from __future__ import annotations

import ast
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


_REMOVED = {
    "_is_parent_edge",
    "REFERENCE_KIND_VOCABULARY",
    "reference_kind_parity_disagreements",
}


def _is_parent_key(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value == "Parent intent"


def _parent_read_offenders(source: str) -> list[int]:
    """Line numbers of any ``.get("Parent intent", ...)``, ``x["Parent intent"]``
    or ``"Parent intent" in x``, whatever the receiver."""
    offenders: list[int] = []
    for n in ast.walk(ast.parse(source)):
        if (
            (isinstance(n, ast.Subscript) and _is_parent_key(n.slice))
            or (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and n.func.attr == "get"
                and n.args
                and _is_parent_key(n.args[0])
            )
            or (
                isinstance(n, ast.Compare)
                and _is_parent_key(n.left)
                and any(isinstance(op, (ast.In, ast.NotIn)) for op in n.ops)
            )
        ):
            offenders.append(n.lineno)
    return offenders


def test_no_preamble_parent_read() -> None:
    """AC-0003 — the old parser is gone and nothing reads ``Parent intent`` from
    a mapping in ``closure_index.py``."""
    source = (CW / "closure_index.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    defined = {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.ClassDef))
    } | {
        t.id
        for n in ast.walk(tree)
        for t in (
            n.targets
            if isinstance(n, ast.Assign)
            else [n.target] if isinstance(n, ast.AnnAssign) else []
        )
        if isinstance(t, ast.Name)
    }
    assert not defined & _REMOVED, f"removed symbols still defined: {defined & _REMOVED}"
    offenders = _parent_read_offenders(source)
    assert not offenders, f"Parent intent read from a mapping at lines {offenders}"


def test_parent_read_scan_positive_control() -> None:
    """The scan reports a receiver it cannot trace to ``_preamble``."""
    snippet = 'fields = _get_fields(p)\nv = fields.get("Parent intent", "")\n'
    assert _parent_read_offenders(snippet) == [2]
