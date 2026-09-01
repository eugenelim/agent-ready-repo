"""A spec entry sits under the initiative that owns the brief it descends from.

`workspace.toml` records initiative membership positionally: an entry belongs to
whichever `[<ini>.work]` table it is written into. Nothing else in the file
restates that membership, so an edit anchored on the wrong table -- the same
`shipped = [` opening appears once per initiative -- files a spec under an
initiative it has no relation to. `workspace_status.py` reconcile reads the
placement as authority and reports no finding, so the mistake survives CI.

What this check can establish is bounded by what the file records. A spec entry
whose `source` names a brief, where that brief is itself declared in some
initiative's `brief_queue`, has an independent statement of its initiative and
can be cross-checked. Every other spec entry has no second source and is out of
reach here -- 15 of the repository's 113 spec entries are reachable today. This
check is therefore a floor on a subset, not a membership guarantee for the file.

It also assumes brief and spec share the *exact* initiative. No parent/child
initiative pair in the file separates them, so no allowance is made for one; if
that shape ever lands, this check fails loudly rather than passing quietly.
"""

from __future__ import annotations

import copy
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT / "workspace.toml"
BRIEF_PREFIX = "docs/product/briefs/"

# 15 reachable entries today. The floor keeps ample headroom so ordinary
# churn -- a brief closing out, a slice landing -- cannot red this file, while
# still failing if brief-sourced entries stop being written at all.
MINIMUM_REACHABLE_ENTRIES = 5


def _load(path: Path = WORKSPACE) -> dict[str, Any]:
    """Parse the repository workspace file."""
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _brief_owners(document: dict[str, Any]) -> dict[str, set[str]]:
    """Map each declared brief path to the initiatives whose queue declares it."""
    owners: dict[str, set[str]] = {}
    for slug, initiative in document.items():
        if not isinstance(initiative, dict):
            continue
        queue = initiative.get("brief_queue")
        if not isinstance(queue, dict):
            continue
        for entries in queue.values():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict) and entry.get("kind") == "brief":
                    owners.setdefault(str(entry["path"]), set()).add(slug)
    return owners


def _brief_provenance(entry: dict[str, Any]) -> str | None:
    """Return the brief an entry descends from, or None when it names none."""
    source = entry.get("source")
    if not isinstance(source, dict):
        return None
    parent = source.get("parent")
    if isinstance(parent, str) and parent.startswith(BRIEF_PREFIX):
        return parent
    ref = source.get("ref")
    if isinstance(ref, str) and ref.startswith(BRIEF_PREFIX):
        return ref
    return None


def _reachable_spec_entries(
    document: dict[str, Any],
) -> list[tuple[str, str, str, str]]:
    """Yield (initiative, collection, spec path, brief path) for cross-checkable specs."""
    owners = _brief_owners(document)
    reachable: list[tuple[str, str, str, str]] = []
    for slug, initiative in document.items():
        if not isinstance(initiative, dict):
            continue
        work = initiative.get("work")
        if not isinstance(work, dict):
            continue
        for collection, entries in work.items():
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict) or entry.get("kind") != "spec":
                    continue
                brief = _brief_provenance(entry)
                if brief is None or brief not in owners:
                    continue
                reachable.append((slug, collection, str(entry["path"]), brief))
    return reachable


def _misfiled(document: dict[str, Any]) -> list[str]:
    """Report every reachable spec filed under an initiative that owns no such brief."""
    owners = _brief_owners(document)
    findings: list[str] = []
    for slug, collection, path, brief in _reachable_spec_entries(document):
        if slug not in owners[brief]:
            findings.append(
                f"{path} is registered in [{slug}.work].{collection} "
                f"but descends from {brief}, owned by {sorted(owners[brief])}"
            )
    return findings


def test_every_brief_sourced_spec_sits_under_its_briefs_initiative() -> None:
    """The repository's own workspace file has no misfiled brief-sourced spec."""
    findings = _misfiled(_load())
    assert not findings, "misfiled spec entries:\n" + "\n".join(findings)


def test_the_check_reaches_enough_of_the_file_to_mean_something() -> None:
    """Anti-vacuity: an empty reachable set would pass the assertion above."""
    reachable = _reachable_spec_entries(_load())
    assert len(reachable) >= MINIMUM_REACHABLE_ENTRIES, (
        f"only {len(reachable)} spec entries carry cross-checkable brief provenance; "
        "below this floor the check above proves nothing"
    )
    assert len({slug for slug, _, _, _ in reachable}) >= 2, (
        "reachable entries all sit in one initiative, so a cross-initiative "
        "misfiling could not be observed"
    )


def test_a_spec_moved_to_the_wrong_initiative_is_reported() -> None:
    """Killing mutation: relocating a real entry to a foreign initiative must fail.

    This reproduces the defect the check exists for -- an entry appended to the
    first `shipped = [` in the file rather than its own initiative's -- against
    the real document, so the predicate is exercised on the shape it must catch.
    """
    document = copy.deepcopy(_load())
    reachable = _reachable_spec_entries(document)
    assert reachable, "no reachable entry to mutate"
    donor_slug, donor_collection, donor_path, _ = reachable[0]
    foreign = next(
        slug
        for slug, body in document.items()
        if slug != donor_slug
        and isinstance(body, dict)
        and isinstance(body.get("work"), dict)
    )

    work = document[donor_slug]["work"]
    entry = next(
        item for item in work[donor_collection] if item.get("path") == donor_path
    )
    work[donor_collection].remove(entry)
    document[foreign]["work"].setdefault("shipped", []).append(entry)

    findings = _misfiled(document)
    assert any(donor_path in finding for finding in findings), (
        f"moving {donor_path} into [{foreign}.work] was not reported: {findings}"
    )
