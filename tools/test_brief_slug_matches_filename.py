"""AC-0021: a brief's derived identity must equal its filename stem.

`brief:<slug>` is the canonical `Brief:` value, and every consumer resolves it
by joining the slug back to `docs/product/briefs/<slug>.md`. That join is only
correct while a brief's identity and its filename agree. Nothing enforced the
agreement: it held for all briefs when the typed form shipped, by coincidence
rather than by construction, and a brief whose `Slug:` field disagreed with its
filename would make its typed pointer resolve to the wrong artifact — or to
none — with no error anywhere.

The recognizer keys a brief on its `Slug:` field and falls back to the stem, so
a mismatch is silent by design: both values are legitimate, they simply are not
the same artifact. This is the tripwire for that.

Run directly when adding or renaming a brief:
`python3 -m pytest tools/test_brief_slug_matches_filename.py -q`.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BRIEFS = REPO_ROOT / "docs" / "product" / "briefs"

# The recognizer's own field pattern: a preamble bullet naming `Slug`.
_SLUG_RE = re.compile(r"^- \*\*Slug:\*\*\s*`?([^`\n]+?)`?\s*$", re.M)


def _briefs() -> list[Path]:
    return sorted(p for p in BRIEFS.glob("*.md") if not p.name.startswith("_"))


def test_every_brief_slug_matches_its_filename_stem() -> None:
    """A declared `Slug:` that disagrees with the filename breaks the typed form."""
    mismatched: list[str] = []
    for path in _briefs():
        match = _SLUG_RE.search(path.read_text(encoding="utf-8"))
        if match is None:
            continue  # no declared slug: the recognizer falls back to the stem
        slug = match.group(1).strip()
        if slug != path.stem:
            mismatched.append(f"{path.name}: Slug: {slug!r} != stem {path.stem!r}")
    assert not mismatched, (
        "a brief's identity must equal its filename stem, because every consumer "
        "resolves `brief:<slug>` by joining the slug back to "
        "`docs/product/briefs/<slug>.md`:\n  " + "\n  ".join(mismatched)
    )


def test_the_brief_corpus_is_not_empty() -> None:
    """Guard the guard: an empty glob would make the check above vacuous."""
    assert _briefs(), f"no briefs found under {BRIEFS} — the check above proves nothing"
