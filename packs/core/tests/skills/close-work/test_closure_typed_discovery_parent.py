"""A registered typed Discovery keeps the spec's intent parent in close-work.

Drives the real parent lookup (``resolve_intent_ancestors``) with the real
delivery resolver subprocess and the real intent-graph derivation: replacing a
valid path-valued ``Discovery:`` with a registered typed form must resolve the
same intent parent.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[3]
    / ".apm" / "skills" / "close-work" / "scripts"
)


def _load(key: str, path: Path):
    spec = importlib.util.spec_from_file_location(key, path)
    assert spec and spec.loader, f"no module at {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


ci = _load("closure_index__typed_discovery_parent", _SCRIPTS / "closure_index.py")


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _intent(root: Path, slug: str, *, level: str, decomposed: str) -> None:
    _write(
        root,
        f"docs/product/intents/{slug}.md",
        f"- **Slug:** {slug}\n- **Status:** Accepted\n- **Kind:** outcome\n"
        f"- **Level:** {level}\n- **Decomposed:** 2026-10-01 {decomposed}\n",
    )


def _spec(root: Path, name: str, discovery: str) -> None:
    _write(
        root,
        f"docs/specs/{name}/spec.md",
        f"- **Status:** Implementing\n- **Discovery:** {discovery}\n",
    )


_TARGETS = [
    pytest.param("target-alpha", "feature", "spec", id="feature-alpha"),
    pytest.param("target-beta", "feature", "spec", id="feature-beta"),
    pytest.param("target-umbrella", "capability", "children", id="non-feature"),
]


@pytest.mark.parametrize("slug,level,decomposed", _TARGETS)
@pytest.mark.parametrize("prefix", ["outcome", "opportunity", "capability", "intent"])
def test_typed_discovery_keeps_the_same_intent_parent(
    tmp_path: Path, slug: str, level: str, decomposed: str, prefix: str
) -> None:
    _intent(tmp_path, slug, level=level, decomposed=decomposed)
    spec_name = f"{slug}-delivery"
    _spec(tmp_path, spec_name, f"docs/product/intents/{slug}.md")
    before = ci.resolve_intent_ancestors(spec_name, "spec", {}, tmp_path)
    assert [a[0] for a in before] == [slug]

    _spec(tmp_path, spec_name, f"{prefix}:{slug}")
    after = ci.resolve_intent_ancestors(spec_name, "spec", {}, tmp_path)

    assert after == before
