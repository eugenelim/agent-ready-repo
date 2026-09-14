"""The spec index stays retired.

ADR-0112 removed the index over `docs/specs/`. Nothing else reddens if a table
returns, if a skill starts instructing an agent to maintain one, or if the seed
regains its placeholder — these criteria were ticked on inspection alone, which
is what this file replaces.
"""
from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
LIVE = ROOT / "docs/specs/README.md"
SEED = ROOT / "packs/core/seeds/docs/specs/README.md"
# Two shapes, because GFM accepts a pipe table with or without outer pipes. The
# delimiter row is what makes a table render, so it is the reliable signal; the
# edge-piped row is kept for a table whose delimiter row is malformed.
# Not detected, and named so the blind spot is visible: an HTML <table>, and a
# delimiter row inside a fenced code block.
_EDGE_PIPED_ROW = re.compile(r"^\s*\|.*\|\s*$", re.MULTILINE)
_DELIMITER_ROW = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$",
                            re.MULTILINE)


def _table_signals(body: str) -> list[str]:
    return _EDGE_PIPED_ROW.findall(body) + _DELIMITER_ROW.findall(body)


@pytest.mark.parametrize("path", [LIVE, SEED], ids=["live", "seed"])
def test_the_spec_readme_carries_no_table(path: pathlib.Path) -> None:
    """AC28, AC30: a table here is the thing that was retired."""
    signals = _table_signals(path.read_text(encoding="utf-8"))
    assert signals == [], f"{path} regained a table: {signals[:3]}"


@pytest.mark.parametrize("path", [LIVE, SEED], ids=["live", "seed"])
def test_the_spec_readme_keeps_the_directory_convention(path: pathlib.Path) -> None:
    """AC29: retiring the index must not take the convention prose with it."""
    assert "docs/specs/<feature>" in path.read_text(encoding="utf-8")


_DENIAL = re.compile(r"\b(no|not|never|without)\b[^.]{0,40}?"
                     r"(spec index|index to maintain|index table)", re.IGNORECASE)


def test_no_shipped_surface_instructs_maintaining_a_spec_index() -> None:
    """AC24: the instruction ADR-0112 retired must not return to a shipped file.

    Detects an instruction naming the index within a two-line whitespace-
    normalised window, and skips a window that denies the index exists. Not
    detected, named so the blind spot is visible: an instruction more than two
    lines from the name, and one that names neither the path nor the phrase.
    """
    # A two-line window, whitespace-normalised: the instruction and the path it
    # names are routinely wrapped across lines in this repository's prose.
    verbs = re.compile(r"\b(update|add|edit|maintain|index|append|insert|record|list)\b",
                       re.IGNORECASE)
    names = re.compile(r"specs/README|spec index|index of specs", re.IGNORECASE)
    offenders = []
    for base in ("packs", "guides"):
        for path in (ROOT / base).rglob("*.md"):
            if "/tests/" in path.as_posix():
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for i in range(len(lines)):
                window = re.sub(r"\s+", " ", " ".join(lines[i:i + 2]))
                if not (names.search(window) and verbs.search(window)):
                    continue
                # Prose that *denies* the index exists reads the same to a verb
                # match. The retirement itself had to say so, in this very guide.
                if _DENIAL.search(window):
                    continue
                offenders.append(f"{path.relative_to(ROOT)}:{i + 1}: {window[:90]}")
    assert offenders == [], offenders


def test_the_seed_placeholder_map_drops_specs_and_keeps_adr_and_rfc() -> None:
    """AC31, AC32: the sentinel requirement moved, and the other two stayed."""
    from agentbundle.catalogue_tooling import lint

    required = lint._SEEDS_REQUIRED_PLACEHOLDERS
    assert required.get("docs/specs/README.md") == ()
    assert "<!-- no ADRs yet -->" in required["docs/adr/README.md"]
    assert "<!-- no RFCs yet -->" in required["docs/rfc/README.md"]


def test_the_governance_seeds_are_what_the_generator_writes() -> None:
    """AC32a: a seed that differs means an adopter's first run deletes something."""
    import importlib.util
    import sys
    import tempfile

    spec = importlib.util.spec_from_file_location(
        "index_records_seedcheck",
        ROOT / "packs/governance-extras/.apm/skills/new-adr/scripts/index-records.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    empty = pathlib.Path(tempfile.mkdtemp())
    for kind in ("adr", "rfc"):
        seed = ROOT / f"packs/governance-extras/seeds/docs/{kind}/README.md"
        assert seed.read_text(encoding="utf-8") == module.render(empty, record_type=kind), (
            f"{seed} differs from generator output; an adopter's first run would rewrite it"
        )


def test_conventions_names_both_generated_indexes() -> None:
    """AC34a: the guidance the generated files no longer carry lives here."""
    for path in (ROOT / "docs/CONVENTIONS.md",
                 ROOT / "packs/core/seeds/docs/CONVENTIONS.md"):
        body = path.read_text(encoding="utf-8")
        for name in ("adr/README.md", "rfc/README.md"):
            assert f"The `{name}` index is generated" in body, f"{path} lost {name}"
