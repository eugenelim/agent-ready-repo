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


def test_ac0020_every_parent_of_a_named_brief_is_refused(tmp_path: Path) -> None:
    resolver = _load(
        "_core_intent_delivery_relations_brief_parents",
        APM / "adapter-root-bins" / "intent_delivery_relations.py",
    )
    closure = _load(
        "_core_close_work_closure_index_brief_parents",
        APM / "skills" / "close-work" / "scripts" / "closure_index.py",
    )
    for slug in ("alpha", "beta", "gamma"):
        _write(
            tmp_path / f"docs/product/intents/{slug}.md",
            f"# {slug}\n\n- **Slug:** `{slug}`\n- **Level:** feature\n"
            "- **Status:** Accepted\n- **Decomposed:** 2026-10-07 spec\n",
        )
        _write(
            tmp_path / f"docs/specs/{slug}-delivery/spec.md",
            f"# Spec\n\n- **Status:** Shipped\n- **Discovery:** `intent:{slug}`\n",
        )
    _write(
        tmp_path / "docs/product/briefs/BRF-0001-shared.md",
        "# Shared\n\n- **Slug:** `shared`\n- **Status:** Executing\n"
        "- **Parent intent:** intent:alpha\n- **Parent intent:** intent:beta\n",
    )
    _write(
        tmp_path / "docs/specs/broken/spec.md",
        "# Spec\n\n- **Status:** Draft\n"
        "- **Brief:** `brief:shared`\n- **Brief:** `brief:missing`\n",
    )

    def verdict(slug: str):
        return closure.check_ancestor_closure(
            slug,
            "Accepted",
            "spec",
            tmp_path,
            _freshness_checker=lambda: True,
            _snapshot_provider=resolver.resolve_repository,
        )

    for named in ("alpha", "beta"):
        refused = verdict(named)
        assert isinstance(refused, closure.ClosureRefuse), (named, refused)
        assert "delivery-relation-ambiguous" in refused.reason
    assert isinstance(verdict("gamma"), closure.ClosureEligible)
