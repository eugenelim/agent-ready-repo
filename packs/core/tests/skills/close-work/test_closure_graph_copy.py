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


def _is_preamble_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_preamble"
    )


def _is_parent_key(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and node.value == "Parent intent"


def test_no_preamble_parent_read() -> None:
    """AC-0003 — the old parser is gone and nothing reads ``Parent intent`` from
    a ``_preamble`` result."""
    tree = ast.parse((CW / "closure_index.py").read_text(encoding="utf-8"))
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

    # Names bound to a _preamble result, anywhere in the module.
    bound: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and _is_preamble_call(n.value):
            bound |= {t.id for t in n.targets if isinstance(t, ast.Name)}

    def from_preamble(node: ast.AST) -> bool:
        return _is_preamble_call(node) or (
            isinstance(node, ast.Name) and node.id in bound
        )

    offenders: list[int] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and from_preamble(n.value) and _is_parent_key(n.slice) or (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == "get"
            and from_preamble(n.func.value)
            and n.args
            and _is_parent_key(n.args[0])
        ) or (
            isinstance(n, ast.Compare)
            and _is_parent_key(n.left)
            and any(isinstance(op, (ast.In, ast.NotIn)) for op in n.ops)
            and any(from_preamble(c) for c in n.comparators)
        ):
            offenders.append(n.lineno)
    assert not offenders, f"Parent intent read from a _preamble result at lines {offenders}"
