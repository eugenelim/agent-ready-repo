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
the tree rather than naming any.
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


def test_the_catalogue_has_declaring_packs() -> None:
    """A non-empty floor.

    Every check below is a `for` over a glob, and a glob that matches nothing
    satisfies "for every pack ..." vacuously. A mis-rooted or renamed tree must
    go red here rather than pass everything downstream.
    """
    assert len(_declaring_packs()) >= 5


@pytest.mark.parametrize("pack,section,output_dir", _declaring_packs())
def test_declared_pair_is_documented_by_the_pack(
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


def test_a_crossed_pair_is_never_itself_documented() -> None:
    """The rule must discriminate, not merely pass on today's tree.

    Wherever a pack documents two distinct pairs, crossing them — one pair's
    section carried on the other's base — must not appear in the documented
    set. If it did, the pair rule would admit exactly the drift it exists to
    reject. The crossing packs are derived, not named, so this stays portable.
    """
    crossings = 0
    for pack, _section, _base in _declaring_packs():
        pairs = _documented_pairs(pack)
        for one_section, one_base in pairs:
            for other_section, other_base in pairs:
                if one_section == other_section or one_base == other_base:
                    continue
                assert (one_section, other_base) not in pairs, (
                    f"{pack} documents both ({one_section}, {one_base}) and "
                    f"({other_section}, {other_base}), and also their cross"
                )
                crossings += 1
    assert crossings, (
        "no pack documents two distinct pairs, so the discrimination this "
        "rule provides is untested — the assertion above never ran"
    )
