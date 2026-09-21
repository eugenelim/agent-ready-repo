# STUB: AC-0001, AC-0005, AC-0013, AC-0014
# Stored and validated in PLAN's T2 Tests: subsection. This is a roster test
# because it reads a second pack's script and the repository's own docs/, which
# a pack test may not reach (tests/AGENTS.md:22-25).
"""Cross-pack equivalence and owner-parity for the typed ordinal allocator."""

import importlib.util
import pathlib
import re
import subprocess
import sys

import pytest

sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[2]
OWNER = ROOT / "docs/product/intents/FEAT-0001-intent-identity-and-registration.md"
INTENTS = ROOT / "docs/product/intents"


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


TYPED = _load(
    "typed_intent_ordinal",
    ROOT / "packs/core/.apm/skills/work-intake/scripts/intent_ordinal.py",
)
UNTYPED = _load(
    "adr_next_ordinal",
    ROOT / "packs/governance-extras/.apm/skills/new-adr/scripts/next-ordinal.py",
)

_OWNER_ROW = re.compile(r"^\|\s*`([a-z-]+)`\s*\|\s*`([A-Z]+)`\s*\|")


def owner_table() -> dict[str, str]:
    """Parse the level-to-token table out of the intent's ## Boundary."""
    rows = {}
    for line in OWNER.read_text(encoding="utf-8").splitlines():
        match = _OWNER_ROW.match(line.strip())
        if match:
            rows[match.group(1)] = match.group(2)
    assert rows, "the owner's table did not parse; its shape changed"
    return rows


def test_the_mapping_matches_its_owner_in_both_directions() -> None:
    """AC-0014: no missing entry, no changed token, and no extra one."""
    assert owner_table() == TYPED.LEVEL_TOKENS


def test_the_parser_recognizes_exactly_the_owner_tokens() -> None:
    """AC-0014: the parser namespace cannot be widened past the table."""
    assert set(TYPED.NAMESPACE_TOKENS) == set(owner_table().values())


def test_every_live_typed_file_satisfies_the_owner_shape() -> None:
    """AC-0013: the narrowed grammar reclassifies nothing on disk."""
    introduced = [
        path.name
        for path in INTENTS.glob("*.md")
        if TYPED.classify(path.name) != "outside"
    ]
    assert introduced, "no typed intent found; the corpus or the classifier changed"
    assert [n for n in introduced if TYPED.classify(n) != "valid"] == []


@pytest.mark.parametrize("token", sorted(owner_table().values()))
def test_paired_fixtures_agree_with_the_untyped_allocator(
    token: str, tmp_path: pathlib.Path
) -> None:
    """AC-0005: one max+1 rule across both filename grammars."""
    typed_dir = tmp_path / f"typed-{token}"
    untyped_dir = tmp_path / f"untyped-{token}"
    typed_dir.mkdir()
    untyped_dir.mkdir()
    for ordinal in (3, 7):
        (typed_dir / f"{token}-{ordinal:04d}-x.md").write_text("", encoding="utf-8")
        (untyped_dir / f"{ordinal:04d}-x.md").write_text("", encoding="utf-8")
    assert TYPED.next_typed_ordinal(typed_dir, token) == UNTYPED.next_ordinal(
        str(untyped_dir)
    )


def _git(directory: pathlib.Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments], cwd=directory, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def test_origin_widens_the_view_but_not_to_an_unpushed_peer(
    tmp_path: pathlib.Path,
) -> None:
    """AC-0005: committed-and-pushed records count; a peer's unpushed work cannot."""
    token = sorted(owner_table().values())[0]
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git(upstream, "init", "--initial-branch=main")
    records = upstream / "records"
    records.mkdir()
    (records / f"{token}-0009-pushed.md").write_text("", encoding="utf-8")
    _git(upstream, "add", "-A")
    _git(upstream, "-c", "user.email=t@example.invalid", "-c", "user.name=t",
         "commit", "-m", "seed")

    clone = tmp_path / "clone"
    _git(tmp_path, "clone", "--quiet", str(upstream), str(clone))
    local_records = clone / "records"
    assert TYPED.next_typed_ordinal(local_records, token) == 10

    peer = tmp_path / "peer"
    _git(tmp_path, "clone", "--quiet", str(upstream), str(peer))
    (peer / "records" / f"{token}-0020-unpushed.md").write_text("", encoding="utf-8")
    _git(peer, "add", "-A")
    _git(peer, "-c", "user.email=t@example.invalid", "-c", "user.name=t",
         "commit", "-m", "peer")
    assert TYPED.next_typed_ordinal(local_records, token) == 10


def test_the_baseline_agrees_with_the_hand_authored_corpus() -> None:
    """AC-0001: the allocator's next number is one above the live maximum."""
    for token in sorted(owner_table().values()):
        live = [
            int(m.group(1))
            for path in INTENTS.glob(f"{token}-*.md")
            if (m := re.match(rf"^{token}-(\d{{4,}})-", path.name))
        ]
        expected = (max(live) + 1) if live else 1
        assert TYPED.next_typed_ordinal(INTENTS, token) == expected
