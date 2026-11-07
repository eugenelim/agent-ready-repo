"""Supersession flow over fixture RFCs: the mirrors make a checked edge both ways."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
from typing import Any

import pytest

sys.dont_write_bytecode = True

NAV_SCRIPTS = (
    pathlib.Path(__file__).resolve().parents[3]
    / ".apm/skills/navigate-decisions/scripts"
)
_SPEC = importlib.util.spec_from_file_location(
    "repo_governance_new_rfc_supersession_nav", NAV_SCRIPTS / "navigate_decisions.py"
)
assert _SPEC is not None and _SPEC.loader is not None
NAV = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = NAV
_SPEC.loader.exec_module(NAV)

OLD_BODY = "## Summary\n\nOld proposal.\n\n## Proposal\n\nOld text.\n"
OLD = (
    "# RFC-0001: Old\n\n- **Status:** Accepted\n- **Supersedes:** none\n"
    "- **Supersedes in part:** none\n- **Superseded by:** none\n"
    "- **Superseded in part:** none\n\n" + OLD_BODY
)
NEW = (
    "# RFC-0002: New\n\n- **Status:** {status}\n- **Supersedes:** none\n"
    "- **Supersedes in part:** RFC-0001 D1,D3\n- **Superseded by:** none\n"
    "- **Superseded in part:** none\n\n## Summary\n\nNew proposal.\n"
)


def _edges(root: pathlib.Path, record: str, direction: str) -> list[dict[str, Any]]:
    payload = NAV.run_query(
        root, {"operation": "lineage", "id": record, "direction": direction, "depth": 1}
    )
    assert payload["status"] == "ok"
    return [r for r in payload["relationships"] if r.get("trust_class") == "checked"]


@pytest.fixture
def root(tmp_path: pathlib.Path) -> pathlib.Path:
    """A repository with a frozen RFC and a draft that supersedes part of it."""
    rfc = tmp_path / "docs/rfc"
    rfc.mkdir(parents=True)
    (rfc / "0001-old.md").write_text(OLD, encoding="utf-8")
    (rfc / "0002-new.md").write_text(NEW.format(status="Draft"), encoding="utf-8")
    return tmp_path


def test_draft_alone_makes_no_checked_edge_and_leaves_the_frozen_rfc(
    root: pathlib.Path,
) -> None:
    assert _edges(root, "RFC-0002", "older") == []
    assert (root / "docs/rfc/0001-old.md").read_text(encoding="utf-8") == OLD


def test_mirrors_after_acceptance_make_a_checked_edge_in_both_directions(
    root: pathlib.Path,
) -> None:
    new = root / "docs/rfc/0002-new.md"
    new.write_text(NEW.format(status="Accepted"), encoding="utf-8")
    old = root / "docs/rfc/0001-old.md"
    text = OLD.replace(
        "- **Superseded in part:** none", "- **Superseded in part:** RFC-0002 D1,D3"
    )
    old.write_text(
        text + "\n## Errata\n\n- RFC-0002 supersedes decisions D1 and D3.\n",
        encoding="utf-8",
    )
    # Only the one header line changed and an Errata entry was appended.
    assert OLD_BODY in old.read_text(encoding="utf-8")

    for record, direction in (("RFC-0002", "older"), ("RFC-0001", "newer")):
        edges = _edges(root, record, direction)
        assert len(edges) == 1
        assert edges[0]["relation"] == "supersedes_in_part"
        assert edges[0]["scope"] == ["D1", "D3"]
        assert {edges[0]["from"], edges[0]["to"]} == {"RFC-0001", "RFC-0002"}
