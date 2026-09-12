"""Decision-record ordinal uniqueness, walked against the recorded repository.

Governing contract: `docs/specs/decision-record-ordinal-uniqueness/spec.md`.

This suite reads the real `docs/adr` and `docs/rfc` rather than a fixture. A
tmp_path fixture proves the predicate; only the recorded corpus proves the
repository. The distinction matters because the failure this work addresses —
two records sharing an ordinal — is invisible inside any single branch and shows
up only against the accumulated tree.

Every walk asserts a non-empty floor before asserting its property. Without the
floor, a walk that reached nothing reports exactly like a clean tree, which is
the shape of a control that cannot fail.

The predicate is loaded from the projected copy by explicit path under a
pack-and-skill-unique module name, so a stale editable install cannot satisfy
the suite and a second `next-ordinal.py` elsewhere cannot be bound by accident.
"""

import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RECORD_DIRECTORIES = ("docs/adr", "docs/rfc")

# This spec's own directory is excluded from the stale-filename sweep: it is the
# audit record of the rename and has to name what moved. Every other path that
# still carries a pre-repair filename is a stale reference.
RENAME_RECORD = "docs/specs/decision-record-ordinal-uniqueness"

# Built from parts at run time, never stored contiguously, so this file does not
# match its own sweep and turn a clean tree red.
RENAMES = (
    ("docs/adr", "0055", "0109", "starlight-replaces-mkdocs-for-reference-docs"),
    ("docs/adr", "0106", "0110",
     "cooled-child-scope-is-declared-on-the-entry-not-inferred-from-absence"),
    ("docs/rfc", "0047", "0100", "adopter-and-org-supplied-grounding"),
    ("docs/rfc", "0074", "0101", "pack-config-and-oplog"),
)

# The member of each collided pair that reached the default branch first and so
# keeps its ordinal.
RETAINED = (
    ("docs/adr", "0055", "wave1-docs-restructure-contracts-and-guides-to-repo-root"),
    ("docs/adr", "0106", "direct-skill-identity-and-upgrade-revision-route"),
    ("docs/rfc", "0047", "default-source-on-discovery-verbs"),
    ("docs/rfc", "0074", "fidelity-ladder-and-ephemeral-env-qualification"),
)


def _load_predicate():
    """Load the projected allocator under a unique module name."""
    path = ROOT / ".claude/skills/new-adr/scripts/next-ordinal.py"
    assert path.is_file(), f"projected allocator missing: {path}"
    spec = importlib.util.spec_from_file_location(
        "governance_extras_new_adr_next_ordinal_roster", path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MODULE = _load_predicate()


def _groups(directory: Path) -> dict[int, list[str]]:
    """Group every entry in a record directory by its ordinal prefix."""
    grouped: dict[int, list[str]] = {}
    for entry in directory.iterdir():
        match = MODULE._PREFIX.match(entry.name)
        if match:
            grouped.setdefault(int(match.group(1)), []).append(entry.name)
    return grouped


@pytest.mark.parametrize("relative", RECORD_DIRECTORIES)
def test_every_shared_ordinal_group_is_a_companion(relative: str, capsys) -> None:
    """No ordinal is held by two records; shared prefixes are all companions."""
    directory = ROOT / relative
    grouped = _groups(directory)
    assert grouped, f"{relative}: walk reached no records at all"

    shared = {o: sorted(n) for o, n in grouped.items() if len(n) > 1}
    duplicates = MODULE.duplicate_ordinals(directory)

    # The cross-product, printed rather than sampled: a reader can tell a clean
    # tree from a walk that reached nothing.
    with capsys.disabled():
        print(f"\n{relative}: {len(grouped)} ordinals, {len(shared)} shared")
        for ordinal, names in sorted(shared.items()):
            verdict = "DUPLICATE" if ordinal in duplicates else "companion"
            print(f"  {ordinal:04d}  {verdict:<9} {', '.join(names)}")

    assert duplicates == {}, f"{relative}: ordinals held by two records: {duplicates}"


def test_the_companion_groups_are_actually_present() -> None:
    """The companion walk has something to classify.

    Without this the previous test passes on a corpus with no shared prefixes,
    which would mean the companion branch of the predicate was never exercised.
    """
    shared = sum(
        len([n for n in _groups(ROOT / d).values() if len(n) > 1])
        for d in RECORD_DIRECTORIES
    )
    assert shared >= 20, f"expected at least 20 companion groups, found {shared}"


@pytest.mark.parametrize(
    ("relative", "ordinal", "slug"), RETAINED, ids=[f"{d}-{o}" for d, o, _ in RETAINED]
)
def test_the_retained_member_keeps_its_ordinal(
    relative: str, ordinal: str, slug: str
) -> None:
    """Each collided pair is reported separately, so a partial repair names itself."""
    assert (ROOT / relative / f"{ordinal}-{slug}.md").is_file()


@pytest.mark.parametrize(
    ("relative", "old", "new", "slug"), RENAMES,
    ids=[f"{d}-{o}-to-{n}" for d, o, n, _ in RENAMES],
)
def test_the_moved_record_is_at_its_new_ordinal(
    relative: str, old: str, new: str, slug: str
) -> None:
    """The renumbered record exists at its new ordinal and not at its old one."""
    assert (ROOT / relative / f"{new}-{slug}.md").is_file()
    assert not (ROOT / relative / f"{old}-{slug}.md").exists()


def test_no_tracked_path_references_a_pre_repair_filename() -> None:
    """The decisive sweep: a stale reference in a file no repair task opened."""
    needles = [f"{old}-{slug}" for _, old, _, slug in RENAMES]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    assert tracked, "git ls-files returned nothing; the sweep reached no files"

    stale: list[str] = []
    for relative in tracked:
        if relative.startswith(RENAME_RECORD):
            continue
        try:
            body = (ROOT / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        stale.extend(
            f"{relative} -> {needle}" for needle in needles if needle in body
        )

    assert not stale, "pre-repair filenames still referenced:\n" + "\n".join(stale)
