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
discriminate. `product-engineering` legitimately documents three sections —
`[product]` for its intents and rollups, `[discovery]` (a different base) for
the discovery loop, and `[design]`, which `ux-writing` only *reads* from
`experience-design`. Section membership alone would admit
`section = "discovery"` carried on `output_dir = "docs/product"`: a pair no
document describes, installing a default under a section whose readers resolve
somewhere else.
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


def test_a_mismatched_pair_is_rejected() -> None:
    """The check must discriminate, not just pass on today's tree.

    `product-engineering` documents both `[product]`/`docs/product` and
    `[discovery]`/`docs/discovery`. The cross of the two is the exact defect
    the pair rule exists to catch, and it must not be in the documented set.
    """
    documented = _documented_pairs("product-engineering")
    assert ("product", "docs/product") in documented
    assert ("discovery", "docs/discovery") in documented
    assert ("discovery", "docs/product") not in documented
