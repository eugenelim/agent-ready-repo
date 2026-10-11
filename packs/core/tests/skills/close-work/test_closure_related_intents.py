"""Closure verdicts ignore ``Related intents`` (related-intents-field AC-0017).

The corpus is written to disk and the bundled derivation reads it with no graph
provider injected, so the edges are really derived before the verdict is taken.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

_SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "close-work" / "scripts"
_FIELD = "Related intents"


def _load(key: str, path: Path) -> Any:
    """Load a close-work script by path under a unique sys.modules key."""
    spec = importlib.util.spec_from_file_location(key, path)
    assert spec and spec.loader, f"no module at {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


ci = _load("closure_index__related_intents", _SCRIPTS / "closure_index.py")
ig = _load("intent_graph__closure_related_intents", _SCRIPTS / "intent_graph.py")


def _write(root: Path, slug: str, *, status: str, extra: list[str], related: list[str]) -> None:
    directory = root / "docs" / "product" / "intents"
    directory.mkdir(parents=True, exist_ok=True)
    lines = [f"- **Slug:** {slug}", f"- **Status:** {status}", *extra]
    lines += [f"- **{_FIELD}:** {value}" for value in related]
    (directory / f"{slug}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _corpus(root: Path, *, with_related: bool) -> None:
    """Accepted `top` over a Fulfilled child; `outside` is live and not a descendant.

    Related edges run both ways between the closure and `outside`, so a reader
    that took either direction as a child or parent link would pull the
    non-terminal `outside` into the closure and change the verdict.
    """
    rel = (lambda *v: list(v)) if with_related else (lambda *v: [])
    _write(root, "top", status="Accepted", extra=["- **Decomposed:** 2026-10-01 children"],
           related=rel("intent:outside"))
    _write(root, "child", status="Fulfilled", extra=["- **Parent intent:** intent:top"],
           related=rel("intent:child, intent:ghost"))
    _write(root, "outside", status="Draft", extra=[], related=rel("intent:top"))


def _verdict(root: Path) -> Any:
    return ci.check_ancestor_closure(
        "top", "Accepted", "children", root, _freshness_checker=lambda: True
    )


def test_related_edges_never_change_the_closure_verdict(tmp_path: Path) -> None:
    """AC-0017: resolved, self_reference, and dangling edges leave ClosureEligible alone."""
    with_related = tmp_path / "with"
    without = tmp_path / "without"
    _corpus(with_related, with_related=True)
    _corpus(without, with_related=False)

    edges = [e for e in ig.derive(with_related)["edges"] if e["field"] == _FIELD]
    assert sorted((e["from"], e.get("to", ""), e.get("state", "")) for e in edges) == [
        ("intent:child", "", "dangling"),
        ("intent:child", "", "self_reference"),
        ("intent:outside", "intent:top", ""),
        ("intent:top", "intent:outside", ""),
    ]
    assert [e for e in ig.derive(without)["edges"] if e["field"] == _FIELD] == []

    assert isinstance(_verdict(without), ci.ClosureEligible), _verdict(without)
    assert isinstance(_verdict(with_related), ci.ClosureEligible), _verdict(with_related)
