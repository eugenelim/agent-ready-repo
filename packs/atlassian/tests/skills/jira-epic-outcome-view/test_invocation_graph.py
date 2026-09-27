"""What the view invokes is derived from the sources, and reaches no bridge.

A declaration cannot carry a read-only guarantee on its own, because an
undeclared invocation is exactly what a declaration fails to mention. So the
invoked-sibling set is derived from the sources here, and that derived set --
never `deps.skills` -- is what the outbound-mutation check and the coupling
walk both traverse. The declaration is then compared against it for equality,
which is what makes the declaration trustworthy rather than self-reported.

The coupling walk is transitive and starts from the derived set for the same
reason. A token scan alone would not establish it: a skill can invoke a
bridge while containing none of the confined terms, and would pass every
other check here.
"""

from __future__ import annotations

import json

import atlassian_jira_epic_outcome_view_guarantees as guarantees
import pytest


# ---------------------------------------------------------------------------
# The shared traversal, exercised by the real tree and by the fixtures
# ---------------------------------------------------------------------------
def undeclared_invocations(skill_dir, declared, *, skills_root) -> set[str]:
    """Siblings the sources invoke that the manifest does not declare."""
    derived = guarantees.derive_invoked_siblings(skill_dir, skills_root=skills_root)
    return derived - set(declared)


def paths_reaching_a_bridge(start, *, skills_root, bridges) -> list[list[str]]:
    """Every path from `start` through the invocation graph into a bridge.

    Breadth-first from the source-derived set, so the answer names the hops
    rather than reporting only that a bridge was reachable -- a bare boolean
    makes a real finding unactionable.
    """
    edges = guarantees.invocation_closure(start, skills_root=skills_root)
    found: list[list[str]] = []
    queue: list[list[str]] = [[start]]
    seen: set[str] = set()
    while queue:
        path = queue.pop(0)
        current = path[-1]
        if current in bridges and len(path) > 1:
            found.append(path)
            continue
        if current in seen:
            continue
        seen.add(current)
        for nxt in sorted(edges.get(current, set())):
            queue.append([*path, nxt])
    return found


# ---------------------------------------------------------------------------
# Fixture skill trees. Each is a tree the checks above must reject.
# ---------------------------------------------------------------------------
_INVOKING_SOURCE = '''"""A skill that reaches a sibling."""
from pathlib import Path
import subprocess
import sys


def run(skills_root: Path):
    script = skills_root / {target!r} / "scripts" / "run.py"
    return subprocess.run([sys.executable, str(script)], check=False)
'''


def _write_skill(skills_root, name, *, invokes=(), declares=None):
    skill = skills_root / name
    (skill / "scripts").mkdir(parents=True)
    for index, target in enumerate(invokes):
        (skill / "scripts" / f"call_{index}.py").write_text(
            _INVOKING_SOURCE.format(target=target), encoding="utf-8"
        )
    (skill / "scripts" / "run.py").write_text("print('ran')\n", encoding="utf-8")
    declared = list(invokes) if declares is None else list(declares)
    (skill / "manifest.json").write_text(
        json.dumps({"id": name, "deps": {"skills": [{"name": n} for n in declared]}}),
        encoding="utf-8",
    )
    return skill


# ---------------------------------------------------------------------------
# The derived set
# ---------------------------------------------------------------------------
def test_the_invoked_sibling_set_is_derived_from_the_sources() -> None:
    """Liveness for every check that traverses it. An empty derived set would
    satisfy the equality assertion, the outbound check and the coupling walk
    all at once, while proving nothing about any of them."""
    derived = guarantees.derive_invoked_siblings(guarantees.VIEW_SKILL_DIR)

    assert derived, "the sources invoke no sibling, so the traversal covers nothing"
    assert guarantees.VIEW_SKILL not in derived


def test_the_declaration_equals_the_derived_set() -> None:
    """Equality, not containment. Containment in one direction would excuse an
    undeclared call; in the other it would excuse a declaration nothing backs."""
    derived = guarantees.derive_invoked_siblings(guarantees.VIEW_SKILL_DIR)
    declared = guarantees.declared_dependency_skills()

    assert declared == derived, (
        f"declared {sorted(declared)} but the sources invoke {sorted(derived)}"
    )


def test_every_declared_sibling_is_a_skill_this_pack_ships() -> None:
    """A declared name that matches no directory resolves to nothing at run
    time, and would make the equality above agree about a skill that is not
    there."""
    siblings = guarantees.sibling_skill_names()

    assert guarantees.declared_dependency_skills() <= siblings


def test_a_sibling_invoked_but_undeclared_fails_the_check(tmp_path) -> None:
    """The control. Run against a tree where a skill calls a sibling it does
    not declare, the same derivation must name it -- otherwise the equality
    assertion above is green because nothing could ever make it red."""
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    _write_skill(skills_root, "some-client")
    _write_skill(skills_root, "undeclared-client")
    subject = _write_skill(
        skills_root,
        "a-view",
        invokes=("some-client", "undeclared-client"),
        declares=("some-client",),
    )

    missing = undeclared_invocations(subject, {"some-client"}, skills_root=skills_root)

    assert missing == {"undeclared-client"}


def test_the_real_view_declares_every_sibling_it_invokes() -> None:
    """The same check the control above proves can fail, against the ship."""
    missing = undeclared_invocations(
        guarantees.VIEW_SKILL_DIR,
        guarantees.declared_dependency_skills(),
        skills_root=guarantees.SKILLS_ROOT,
    )

    assert missing == set()


# ---------------------------------------------------------------------------
# The coupling walk
# ---------------------------------------------------------------------------
def test_the_pack_declares_bridges_and_the_view_is_not_one() -> None:
    """The walk needs a non-empty bridge list to mean anything: with none
    declared, no path could reach one and the assertion below would hold for
    a view that called every bridge in the pack."""
    bridges = guarantees.declared_bridge_skills()

    assert bridges, "the pack declares no bridges, so the coupling walk is vacuous"
    assert guarantees.VIEW_SKILL not in bridges


def test_no_path_from_the_derived_set_reaches_a_declared_bridge() -> None:
    """Transitive, because a sibling's own reach is still this view's reach."""
    bridges = guarantees.declared_bridge_skills()

    reaching = paths_reaching_a_bridge(
        guarantees.VIEW_SKILL, skills_root=guarantees.SKILLS_ROOT, bridges=bridges
    )

    assert reaching == [], f"the view reaches a bridge: {reaching}"


def test_the_walk_visits_more_than_the_first_hop() -> None:
    """A walk that stopped at the direct dependencies would report no bridge
    for a view whose sibling calls one, which is the case the transitive
    requirement exists for."""
    edges = guarantees.invocation_closure(
        guarantees.VIEW_SKILL, skills_root=guarantees.SKILLS_ROOT
    )
    direct = guarantees.derive_invoked_siblings(guarantees.VIEW_SKILL_DIR)

    assert set(edges) - {guarantees.VIEW_SKILL} > direct, (
        "the closure visited nothing beyond the first hop"
    )


@pytest.mark.parametrize("depth", [1, 2])
def test_a_bridge_calling_fixture_fails_the_walk(tmp_path, depth) -> None:
    """The control, at both depths that matter.

    At depth one the view calls the bridge itself; at depth two a sibling it
    calls does. Neither fixture contains any of the confined machinery terms,
    which is the point: a token scan passes both while the coupling is real.
    """
    skills_root = tmp_path / "skills"
    skills_root.mkdir()
    _write_skill(skills_root, "a-bridge")
    if depth == 1:
        _write_skill(skills_root, "a-view", invokes=("a-bridge",))
    else:
        _write_skill(skills_root, "a-client", invokes=("a-bridge",))
        _write_skill(skills_root, "a-view", invokes=("a-client",))

    for source in (skills_root / "a-view").rglob("*.py"):
        assert "work-intake" not in source.read_text(encoding="utf-8")

    reaching = paths_reaching_a_bridge(
        "a-view", skills_root=skills_root, bridges={"a-bridge"}
    )

    assert reaching, "a bridge-calling fixture passed the walk"
    assert reaching[0][-1] == "a-bridge"
    assert len(reaching[0]) == depth + 1
