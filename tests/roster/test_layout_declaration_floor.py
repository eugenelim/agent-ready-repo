"""This catalogue supplies the evidence the conformance rule checks.

`tests/conformance/test_pack_layout_declared_section.py` ships into adopter
catalogues via `catalogue init`, so each of its tree-derived cases skips when
its evidence is absent — an adopter may hold no packs, or packs that declare
no layout, and neither is a defect there.

That leaves one gap this file closes: in the *source* catalogue a mis-rooted
glob or a renamed tree would make those cases skip rather than fail, and the
suite would stay green while checking nothing. These assertions are claims
about this repository specifically, which is why they are not in the shipped
file.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_CONFORMANCE = (
    REPO_ROOT / "tests" / "conformance" / "test_pack_layout_declared_section.py"
)


def _rule():
    spec = importlib.util.spec_from_file_location("_layout_rule", _CONFORMANCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_this_catalogue_has_declaring_packs() -> None:
    """The enumeration the conformance cases walk is not empty here."""
    declared = _rule()._declaring_packs()
    assert len(declared) >= 5, (
        f"expected at least five declaring packs in this catalogue, found "
        f"{[d[0] for d in declared]} — a mis-rooted enumeration would make "
        "every conformance case skip instead of fail"
    )


def test_the_scope_split_is_exercised_here() -> None:
    """At least one pack documents one section at both scopes.

    Without that, the conformance case proving a repo declaration is not
    validated by a user-scope example skips, and the split stops being
    checked against a real tree.
    """
    rule = _rule()
    both = [
        pack
        for pack, _scope, _section, _base in rule._declaring_packs()
        if rule._documented_pairs(pack, repo_scope=True)
        and rule._documented_pairs(pack, repo_scope=False)
    ]
    assert both, "no pack documents one section at both scopes"


def test_every_declaring_pack_is_covered_by_the_rule() -> None:
    """Each declaring pack's pair is admitted — the rule, run here for real."""
    rule = _rule()
    for pack, scope, section, output_dir in rule._declaring_packs():
        documented = rule._documented_pairs(pack, repo_scope=scope == "repo")
        assert rule._is_admitted(section, output_dir, documented), (
            f"{pack} declares ({section!r}, {output_dir!r}) at {scope} scope, "
            f"documented: {sorted(documented)}"
        )
