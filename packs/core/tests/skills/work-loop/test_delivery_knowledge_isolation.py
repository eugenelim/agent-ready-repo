"""Delivery decisions ignore knowledge tooling: what the work-loop source may name.

The work-loop hands the knowledge producer only the two retained capture gates, and
no delivery runtime script reaches for knowledge tooling. A full run reaching
readiness with project-knowledge absent is proved by the supervisor's synthetic
run, not here.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"

_SOURCE_PROBE = re.compile(
    r"\bknowledge\b.{0,24}(queue|cursor|retry|acknowledg|skip|admission|retention|revocation)"
    r"|capture.{0,16}gate",
    re.IGNORECASE,
)
_SKILL_ROOTS = (_SKILLS / "work-loop", _SKILLS / "close-work")
# The one retained mention: the work-loop capture instruction for the existing gates.
RETAINED_PROBE_HITS = {
    ("work-loop/SKILL.md", "At each capture gate, admit only generalizable practice; dis"),
}
# Scripts that name the knowledge skill or store.  The engine, cohort, and shadow
# facade are deliberately absent: delivery never reaches for knowledge tooling.
KNOWLEDGE_AWARE_SCRIPTS = frozenset({
    "append-knowledge.py", "delivery-fact-feed.py", "lint-knowledge.py", "_delivery_feed.py",
    "_knowledge_projection.py",
})
_KNOWLEDGE_REFERENCE = re.compile(r"project[-_]knowledge|docs/knowledge|knowledge_store")


def _skill_files() -> list[Path]:
    found: list[Path] = []
    for root in _SKILL_ROOTS:
        for current, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d not in {"__pycache__"}]
            for name in names:
                path = Path(current) / name
                if stat.S_ISREG(os.lstat(path).st_mode) and path.suffix in {".md", ".py", ".json"}:
                    found.append(path)
    return found


def test_source_inventory_finds_only_the_retained_capture_gate_mention() -> None:
    """The plan's disconfirming probe finds no lifecycle store and no new capture gate."""
    hits: set[tuple[str, str]] = set()
    for path in _skill_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _SOURCE_PROBE.search(line)
            if match and "evals.json" not in path.name:
                rel = path.relative_to(_SKILLS).as_posix()
                hits.add((rel, line.strip().lstrip("- ")[:60]))
    assert hits == RETAINED_PROBE_HITS


def test_the_work_loop_names_only_the_retained_capture_gates() -> None:
    """spec-approved and plan-locked are the only gate names the skill hands to the producer."""
    text = (_SKILLS / "work-loop" / "SKILL.md").read_text(encoding="utf-8")
    section = text.split("### Project-knowledge integration", 1)[1].split("For durable work", 1)[0]
    assert "spec-approved" in section and "plan-locked" in section
    gates = set(re.findall(r"--semantic-gate[ =]([\w-]+)", text))
    assert gates <= {"spec-approved", "plan-locked"}


def test_no_delivery_runtime_script_references_knowledge_tooling() -> None:
    """Only the feed, projector, and legacy knowledge lint or retired writer name knowledge."""
    aware = {
        path.name
        for path in (_SKILLS / "work-loop" / "scripts").glob("*.py")
        if _KNOWLEDGE_REFERENCE.search(path.read_text(encoding="utf-8"))
    }
    assert aware <= KNOWLEDGE_AWARE_SCRIPTS, sorted(aware - KNOWLEDGE_AWARE_SCRIPTS)
    assert "_acceptance.py" not in aware
