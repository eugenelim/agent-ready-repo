# STUB: AC-0018
from __future__ import annotations

import importlib.util
from pathlib import Path

SOURCE = (
    Path(__file__).resolve().parents[2]
    / ".apm"
    / "adapter-root-bins"
    / "intent_delivery_relations.py"
)


def _load_resolver():
    module_spec = importlib.util.spec_from_file_location(
        "_core_intent_delivery_relations_ac0018",
        SOURCE,
    )
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_ac0018_ambiguous_targets_carry_no_raw_artifact_text(tmp_path: Path) -> None:
    intents = tmp_path / "docs" / "product" / "intents"
    intents.mkdir(parents=True)
    (intents / "alpha.md").write_text(
        "# Alpha\n\n"
        "- **Slug:** `alpha`\n"
        "- **Level:** feature\n"
        "- **Decomposed:** 2026-10-06 spec\x1b[31m\n"
        "- **Decomposed:** 2026-10-06 brief‮\n",
        encoding="utf-8",
    )

    snapshot = _load_resolver().resolve_repository(tmp_path)

    ambiguous = [
        d for d in snapshot["diagnostics"]
        if d["code"] == "delivery-relation-ambiguous" and d.get("subject") == "intent:alpha"
    ]
    assert ambiguous
    targets = [target for d in snapshot["diagnostics"] for target in d.get("targets", [])]
    assert all(target.isprintable() for target in targets)
