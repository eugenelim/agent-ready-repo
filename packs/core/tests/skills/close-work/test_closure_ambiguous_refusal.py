# STUB: AC-0020
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

APM = Path(__file__).resolve().parents[3] / ".apm"


def _load(name: str, path: Path):
    module_spec = importlib.util.spec_from_file_location(name, path)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ac0020_path_form_ambiguous_discovery_refuses_named_feature(tmp_path: Path) -> None:
    resolver = _load(
        "_core_intent_delivery_relations_ac0020",
        APM / "adapter-root-bins" / "intent_delivery_relations.py",
    )
    closure = _load(
        "_core_close_work_closure_index_ac0020_path",
        APM / "skills" / "close-work" / "scripts" / "closure_index.py",
    )
    for slug in ("alpha", "beta"):
        _write(
            tmp_path / f"docs/product/intents/{slug}.md",
            f"# {slug}\n\n- **Slug:** `{slug}`\n- **Level:** feature\n"
            "- **Status:** Accepted\n- **Decomposed:** 2026-10-06 spec\n",
        )
        _write(
            tmp_path / f"docs/specs/{slug}-delivery/spec.md",
            f"# Spec\n\n- **Status:** Shipped\n- **Discovery:** `intent:{slug}`\n",
        )
    _write(
        tmp_path / "docs/specs/broken/spec.md",
        "# Spec\n\n- **Status:** Draft\n"
        "- **Discovery:** `intent:alpha`\n"
        "- **Discovery:** `docs/product/intents/beta.md`\n",
    )

    verdict = closure.check_ancestor_closure(
        "beta",
        "Accepted",
        "spec",
        tmp_path,
        _freshness_checker=lambda: True,
        _snapshot_provider=resolver.resolve_repository,
    )

    assert isinstance(verdict, closure.ClosureRefuse)
    assert "delivery-relation-ambiguous" in verdict.reason
