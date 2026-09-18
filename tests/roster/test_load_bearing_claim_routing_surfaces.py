"""Repository-level arms of the load-bearing-claim routing contract.

Spec: docs/specs/load-bearing-claim-grounding/spec.md — AC-0001 and AC-0002.

Roster-owned rather than pack-owned. AC-0001 sweeps every Markdown file under
two roots, one of which is `guides/`, and AC-0002's second consuming surface is
the adopter how-to under `guides/core/`. `lint-pack-test-boundary` forbids a
`packs/core/tests/` suite from reading either, so these two arms live here while
the rest of the contract stays pack-local in
`packs/core/tests/skills/new-spec/test_load_bearing_claim_grounding.py`.

The split follows the boundary the repository enforces — pack-local versus
repository-level — not an arbitrary one, and neither half silently covers the
other's criteria.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_SKILL = _REPO / "packs" / "core" / ".apm" / "skills" / "new-spec" / "SKILL.md"

# AC-0001's two scan roots, as paths rather than descriptions.
_SCAN_ROOTS = ("packs/core/.apm/skills", "guides")

# AC-0002's consuming surfaces and the anchor each must carry.
_ANCHOR = "load-bearing-claim-routing"
_POINTER_SURFACES = (
    "packs/core/.apm/skills/work-loop/SKILL.md",
    "guides/core/how-to/plan-and-execute-non-trivial-work.md",
)

# AC-0006's routing-input key set. Written here, never read from the table:
# a domain taken from the artifact under test cannot fail.
_ROUTING_KEYS = frozenset(
    {"reaches-the-contract", "unstarted-task-method", "cheap-with-an-oracle"}
)


def _routing_rows(text: str) -> list[tuple[str, str, str]]:
    """Parse a routing table into ordered (key, input cell, destination).

    Lines are stripped before matching because the table is indented inside a
    numbered list item; a regex anchored at the line start with a literal pipe
    matches nothing there. A list rather than a mapping, so a duplicated row
    stays visible.
    """
    rows: list[tuple[str, str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != 2 or cells[0] == "Routing input":
            continue
        m = re.match(r"`([a-z-]+)`", cells[0])
        if m:
            rows.append((m.group(1), cells[0], cells[1]))
    return rows


def _routing_table(text: str) -> dict[str, str]:
    """The same parse as key -> destination."""
    return {k: dest for k, _, dest in _routing_rows(text)}


class RoutingRuleIsSingleHomed(unittest.TestCase):
    """AC-0001. Driven from two named roots, not a hand list of directories."""

    def _markdown_under_roots(self) -> list[Path]:
        found: list[Path] = []
        for root in _SCAN_ROOTS:
            base = _REPO / root
            self.assertTrue(base.is_dir(), f"scan root missing: {root}")
            found.extend(p for p in base.rglob("*.md") if p.is_file())
        return found

    def test_exactly_one_shipped_surface_carries_the_routing_table(self) -> None:
        carriers = [
            p for p in self._markdown_under_roots()
            if set(_routing_table(p.read_text(encoding="utf-8"))) >= _ROUTING_KEYS
        ]
        self.assertEqual(
            [_SKILL], carriers,
            "the routing table must live in exactly one shipped surface",
        )

    def test_the_scan_reaches_a_nontrivial_corpus(self) -> None:
        # Guards the vacuous pass: an empty or tiny sweep would satisfy the
        # negative above while proving nothing.
        self.assertGreater(len(self._markdown_under_roots()), 50)


class PointerSurfacesCarryTheAnchorAndNoRow(unittest.TestCase):
    """AC-0002. A presence-and-absence pair on the same two surfaces."""

    def test_each_surface_carries_the_anchor_identifier_verbatim(self) -> None:
        for rel in _POINTER_SURFACES:
            with self.subTest(surface=rel):
                body = (_REPO / rel).read_text(encoding="utf-8")
                self.assertIn(_ANCHOR, body)

    def test_no_surface_carries_a_routing_table_row(self) -> None:
        for rel in _POINTER_SURFACES:
            with self.subTest(surface=rel):
                rows = _routing_table((_REPO / rel).read_text(encoding="utf-8"))
                self.assertEqual({}, rows, "a pointer carries no table row")
