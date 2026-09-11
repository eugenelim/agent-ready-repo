"""A pack's declared layout section must be one it documents (spec AC6).

`agentbundle install` appends `[<section>] output_dir = <output_dir>` to an
adopter's `agentbundle-layout.toml`, taking both values from the pack manifest.
Every consuming skill then reads that section by prose instruction in its own
`SKILL.md` — no skill calls Python, so nothing at runtime can reconcile a
manifest that names a section the pack's own documentation does not.

That is exactly how the original defect survived two releases: the writer and
the readers were each exercised against their own idea of the shape. So this
check derives **both** sides from the repository and compares them. It carries
no list of expected section names; a list is the hand-maintained table the
design rejects.

Matching the *pair* rather than the section alone is what makes the check
discriminate. A pack may legitimately document several sections: one per
output tree it owns, plus any it only *reads* from a sibling pack. Section
membership alone would then admit a declaration that crosses two of them — a
section from one documented pair carried on the base from another — which
installs a default under a section whose readers resolve somewhere else. No
document describes that combination, and the pair rule is what rejects it.

This file is pack-portable by rule: it derives every pack and every pair from
the tree rather than naming any. It also ships — `catalogue init` writes it
into an adopter's catalogue, which may hold no packs at all — so the
tree-derived cases skip on an empty catalogue while the rule's own
discrimination is proven against synthetic input that is always present.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = REPO_ROOT / "packs"

# `[section]` immediately followed by an `output_dir = "..."` assignment, inside
# one fenced block. Intervening comment lines are allowed; a blank line is not,
# so two unrelated examples cannot be read as one pair.
_PAIR = re.compile(
    r"^\[([a-z0-9][a-z0-9-]*)\]\n(?:#[^\n]*\n)*output_dir = \"([^\"]+)\"",
    re.MULTILINE,
)


def _declaring_packs() -> list[tuple[str, str, str]]:
    """(pack, section, output_dir) for every pack declaring a repo-scope layout."""
    found = []
    for manifest in sorted(PACKS_DIR.glob("*/pack.toml")):
        layout = (
            tomllib.loads(manifest.read_text(encoding="utf-8"))
            .get("pack", {})
            .get("layout", {})
            .get("repo")
        )
        if not layout:
            continue
        section, output_dir = layout.get("section"), layout.get("output_dir")
        if section is None and output_dir is None:
            continue
        found.append((manifest.parent.name, section, output_dir))
    return found


def _documented_pairs(pack: str) -> set[tuple[str, str]]:
    """Every (section, base) pair this pack's own reference docs state."""
    pairs: set[tuple[str, str]] = set()
    for doc in (PACKS_DIR / pack).rglob("references/agentbundle-layout.md"):
        pairs |= set(_PAIR.findall(doc.read_text(encoding="utf-8")))
    return pairs


def _catalogue_has_packs() -> bool:
    return PACKS_DIR.is_dir() and any(PACKS_DIR.glob("*/pack.toml"))


def test_a_populated_catalogue_declares_at_least_one_layout() -> None:
    """A non-empty floor, scoped to a catalogue that has packs.

    The tree-derived case below is a `for` over a glob, and a glob matching
    nothing satisfies "for every pack ..." vacuously — so a mis-rooted or
    renamed tree must go red rather than pass everything downstream. An
    adopter's catalogue with no packs yet is a different thing from a broken
    enumeration, and only the second is a defect.
    """
    if not _catalogue_has_packs():
        pytest.skip("no packs in this catalogue")
    assert _declaring_packs(), "packs are present but none declares a layout"


@pytest.mark.parametrize("pack,section,output_dir", _declaring_packs())
def test_declared_pair_is_documented_by_the_pack(  # noqa: D103
    pack: str, section: str | None, output_dir: str | None
) -> None:
    assert section, f"{pack} declares a repo layout without a section"
    assert output_dir, f"{pack} declares a repo layout without an output_dir"

    documented = _documented_pairs(pack)
    assert documented, f"{pack} declares a layout but documents no section"
    assert (section, output_dir) in documented, (
        f"{pack} declares ({section!r}, {output_dir!r}); its reference docs "
        f"document {sorted(documented)}. The installer writes the declared "
        f"pair, so a pair no document describes installs a default the pack's "
        f"own skills will not read."
    )


def _crossed_pairs(pairs: set[tuple[str, str]]) -> set[tuple[str, str]]:
    """Every (section, base) formed from two *different* documented pairs."""
    return {
        (one_section, other_base)
        for one_section, one_base in pairs
        for other_section, other_base in pairs
        if one_section != other_section and one_base != other_base
    }


def test_the_rule_rejects_a_crossed_pair() -> None:
    """The rule must discriminate, proven without depending on the tree.

    Section membership alone would admit a declaration that takes its section
    from one documented pair and its base from another. This is the property
    that makes the pair rule worth having, so it is asserted against synthetic
    input rather than against whichever packs happen to document two pairs
    today — on an empty catalogue that evidence would simply be absent, and
    the guarantee would silently stop being checked.
    """
    documented = {("alpha", "one/alpha"), ("beta", "two/beta")}
    crossed = _crossed_pairs(documented)

    assert crossed == {("alpha", "two/beta"), ("beta", "one/alpha")}
    assert not (crossed & documented), "a crossed pair must never be documented"


def test_no_pack_documents_a_crossing_of_its_own_pairs() -> None:
    """The same property over the real tree, where there is one."""
    if not _catalogue_has_packs():
        pytest.skip("no packs in this catalogue")
    for pack, _section, _base in _declaring_packs():
        pairs = _documented_pairs(pack)
        assert not (_crossed_pairs(pairs) & pairs), (
            f"{pack} documents a pair and also a crossing of it, so the rule "
            "cannot discriminate for that pack"
        )
