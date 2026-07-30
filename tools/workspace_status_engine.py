#!/usr/bin/env python3
"""workspace-status executable reference model — Order 0 characterization.

This module is a MANUALLY TRANSCRIBED Python interpretation of the algorithmic
sections of packs/core/.apm/skills/workspace-status/SKILL.md. It is NOT a seam
into the production implementation: the live skill is pure model instructions
executed by an LLM; this module is a Python parallel that the model does not call.

Relationship to production:

  SKILL.md semantics ──────► model execution  (production path)
         │
         └── manually transcribed ──► this engine ──► tests

Tests against this engine prove the Python interpretation is internally
consistent with its expected values. They do NOT prove parity with production
behavior. Order 1 will wire this engine (or a successor) as the actual backend;
only then will these become true production-path unit tests.

SKILL.md contract anchor:
  SHA-256 of SKILL.md lines 75–180 (DAG resolution + reconciliation sections):
  61ad933bdb40c5020aa88cc6a3276abe85f4a5f13a745777f2decfb43df62597
  Tested by test_workspace_status.py::test_skill_contract_anchor.
  If that test fails, re-read the changed sections and update this engine before
  editing the fingerprint.

Known gaps (documented in behavior-map.md, not fixed here):
  KD-01: `backlog:<slug>` prefix absent from SKILL.md table
  KD-02: No cycle detection
  KD-03: Missing dep targets not warned
  KD-04: No quick mode (reconciliation always runs)
  KD-05: work.active/shipped duplicate spec.md Status
"""

from __future__ import annotations

import dataclasses
import re
import sys
import time
import tomllib
from pathlib import Path

# ── Data types ────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class WorkEntry:
    path: str    # e.g. "spec/m1-workspace-core"
    slug: str    # path with "spec/" stripped
    needs: list[str]


@dataclasses.dataclass
class ShapingEntry:
    slug: str
    entry_type: str   # shape | research | strategy | signal | design
    needs: list[str]


@dataclasses.dataclass
class BriefQueue:
    executing: str
    ready: list[str]
    draft: list[str]


@dataclasses.dataclass
class InitiativeWork:
    active: list[WorkEntry]
    shipped: list[WorkEntry]
    queue: list[WorkEntry]


@dataclasses.dataclass
class InitiativeShaping:
    active: list[ShapingEntry]
    backlog: list[ShapingEntry]


@dataclasses.dataclass
class Initiative:
    slug: str
    name: str
    status: str      # active | paused | closed | complete
    milestone: str
    work: InitiativeWork
    shaping: InitiativeShaping
    brief_queue: BriefQueue | None


@dataclasses.dataclass
class EntryClassification:
    entry: WorkEntry
    ini_slug: str
    is_ready: bool
    blocking_needs: list[str]   # unsatisfied needs (empty when is_ready)


@dataclasses.dataclass
class ReconciliationFinding:
    finding_type: int   # 1, 2, or 3
    spec_path: str
    spec_status: str
    ini_slug: str
    list_name: str      # "queue" | "active" | "shipped" | ""


@dataclasses.dataclass
class WorkspaceStatusResult:
    initiatives: list[Initiative]
    classifications: list[EntryClassification]   # all queue entries (ready + blocked)
    reconciliation: list[ReconciliationFinding]
    files_read: int   # count of spec.md files read by reconciliation
    elapsed_s: float  # wall-clock seconds for analyze()

    @property
    def ready(self) -> list[EntryClassification]:
        return [c for c in self.classifications if c.is_ready]

    @property
    def blocked(self) -> list[EntryClassification]:
        return [c for c in self.classifications if not c.is_ready]

    @property
    def type1(self) -> list[ReconciliationFinding]:
        return [f for f in self.reconciliation if f.finding_type == 1]

    @property
    def type2(self) -> list[ReconciliationFinding]:
        return [f for f in self.reconciliation if f.finding_type == 2]

    @property
    def type3(self) -> list[ReconciliationFinding]:
        return [f for f in self.reconciliation if f.finding_type == 3]


# ── TOML parsing helpers ──────────────────────────────────────────────────────

def _parse_needs(raw) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return list(raw)


def _parse_work_entry(raw) -> WorkEntry:
    if isinstance(raw, str):
        path = raw
        needs: list[str] = []
    else:
        path = raw.get("path", raw.get("slug", ""))
        needs = _parse_needs(raw.get("needs"))
    slug = path.removeprefix("spec/")
    return WorkEntry(path=path, slug=slug, needs=needs)


def _parse_shaping_entry(raw) -> ShapingEntry:
    if isinstance(raw, str):
        return ShapingEntry(slug=raw, entry_type="shape", needs=[])
    return ShapingEntry(
        slug=raw.get("slug", ""),
        entry_type=raw.get("type", "shape"),
        needs=_parse_needs(raw.get("needs")),
    )


def parse_workspace(path: Path) -> dict:
    """Parse workspace.toml; return raw TOML dict. Raises on parse error."""
    with Path(path).open("rb") as f:
        return tomllib.load(f)


def extract_initiatives(workspace: dict) -> list[Initiative]:
    """Extract all initiatives (ini-*) from a parsed workspace TOML dict."""
    initiatives: list[Initiative] = []
    for key, section in workspace.items():
        if not key.startswith("ini-"):
            continue
        if not isinstance(section, dict):
            continue
        work_raw = section.get("work", {})
        shaping_raw = section.get("shaping_queue", {})
        brief_raw = section.get("brief_queue")

        work = InitiativeWork(
            active=[_parse_work_entry(e) for e in work_raw.get("active", [])],
            shipped=[_parse_work_entry(e) for e in work_raw.get("shipped", [])],
            queue=[_parse_work_entry(e) for e in work_raw.get("queue", [])],
        )
        shaping = InitiativeShaping(
            active=[_parse_shaping_entry(e) for e in shaping_raw.get("active", [])],
            backlog=[_parse_shaping_entry(e) for e in shaping_raw.get("backlog", [])],
        )
        brief_queue: BriefQueue | None = None
        if brief_raw is not None:
            brief_queue = BriefQueue(
                executing=brief_raw.get("executing", ""),
                ready=list(brief_raw.get("ready", [])),
                draft=list(brief_raw.get("draft", [])),
            )
        initiatives.append(Initiative(
            slug=key,
            name=section.get("name", ""),
            status=section.get("status", "active"),
            milestone=section.get("milestone", ""),
            work=work,
            shaping=shaping,
            brief_queue=brief_queue,
        ))
    return initiatives


# ── Status extraction ─────────────────────────────────────────────────────────

# Transition form: "... **Status:** Draft → Approved → Shipped ..."
# Greedy middle match captures the LAST arrow segment (e.g. multi-hop transitions).
_TRANSITION_RE = re.compile(
    r'\*\*Status:\*\*\s+\S.*→\s*([A-Za-z]+)'
)
# Simple form: "... **Status:** Shipped ..."
_SIMPLE_RE = re.compile(
    r'\*\*Status:\*\*\s+([A-Za-z]+)'
)

VALID_STATUSES = frozenset({"Draft", "Approved", "Implementing", "Shipped", "Archived"})


def extract_spec_status(spec_path: Path) -> str | None:
    """Read spec.md and return the Status vocabulary word, or None if absent/unreadable."""
    if not spec_path.exists():
        return None
    try:
        text = spec_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        if "**Status:**" not in line:
            continue
        # Try transition form first ("X → Y")
        m = _TRANSITION_RE.search(line)
        if m:
            return m.group(1).strip()
        m = _SIMPLE_RE.search(line)
        if m:
            return m.group(1).strip()
    return None


# ── DAG / needs resolution ────────────────────────────────────────────────────

_CROSS_INI_RE = re.compile(r'^(ini-[^:]+):work:(.+)$')


def is_need_satisfied(
    need: str,
    ini_slug: str,
    all_initiatives: list[Initiative],
) -> bool:
    """Return True if `need` is satisfied given the current workspace state.

    Implements the needs-resolution table from SKILL.md §2.

    Known gaps (KD-01, KD-03):
      - `backlog:<slug>` prefix: not in SKILL.md table; treated as unsatisfied here.
      - Missing targets: silently treated as unsatisfied (no warning).
    """
    # Cross-initiative: "ini-002:work:spec/..."
    m = _CROSS_INI_RE.match(need)
    if m:
        target_ini_slug, path = m.group(1), m.group(2)
        for ini in all_initiatives:
            if ini.slug == target_ini_slug:
                return any(e.path == path for e in ini.work.shipped)
        return False  # Target initiative not found

    # Local work: "work:<path>"
    if need.startswith("work:"):
        path = need[len("work:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                return any(e.path == path for e in ini.work.shipped)
        return False

    # Shape: "shape:<slug>" — satisfied when active OR absent from all shaping lists
    if need.startswith("shape:"):
        slug = need[len("shape:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                active_slugs = {e.slug for e in ini.shaping.active}
                backlog_slugs = {e.slug for e in ini.shaping.backlog}
                if slug not in active_slugs and slug not in backlog_slugs:
                    return True   # Not present → treated as shipped (KD-06)
                return slug in active_slugs
        return True  # Initiative not found → assume satisfied

    # Research: "research:<slug>" — satisfied when NOT in shaping backlog
    if need.startswith("research:"):
        slug = need[len("research:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                backlog_slugs = {e.slug for e in ini.shaping.backlog}
                return slug not in backlog_slugs
        return True

    # Brief: "brief:<path>" — satisfied if in brief_queue.ready or executing
    if need.startswith("brief:"):
        path = need[len("brief:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug and ini.brief_queue is not None:
                bq = ini.brief_queue
                if bq.executing == path:
                    return True
                return path in bq.ready
        return False

    # `backlog:<slug>` — KD-01: not in SKILL.md table; treated conservatively as unsatisfied
    if need.startswith("backlog:"):
        return False

    # Unknown prefix — conservatively unsatisfied
    return False


def classify_entries(
    ini: Initiative,
    all_initiatives: list[Initiative],
) -> list[EntryClassification]:
    """Classify all queue entries for an initiative as ready or blocked."""
    results: list[EntryClassification] = []
    for entry in ini.work.queue:
        if not entry.needs:
            results.append(EntryClassification(
                entry=entry, ini_slug=ini.slug, is_ready=True, blocking_needs=[],
            ))
        else:
            blocking = [
                n for n in entry.needs
                if not is_need_satisfied(n, ini.slug, all_initiatives)
            ]
            results.append(EntryClassification(
                entry=entry,
                ini_slug=ini.slug,
                is_ready=len(blocking) == 0,
                blocking_needs=blocking,
            ))
    return results


# ── Reconciliation ────────────────────────────────────────────────────────────

def run_reconciliation(
    root: Path,
    initiatives: list[Initiative],
) -> tuple[list[ReconciliationFinding], int]:
    """Run all three reconciliation scan types. Returns (findings, files_read)."""
    findings: list[ReconciliationFinding] = []
    files_read = 0

    # Build set of all tracked paths across all initiatives
    all_tracked: set[str] = set()
    for ini in initiatives:
        for e in ini.work.queue + ini.work.active + ini.work.shipped:
            all_tracked.add(e.path)

    specs_dir = root / "docs" / "specs"

    # ── Type 1: Forward scan — untracked live specs ───────────────────────────
    if specs_dir.exists():
        for spec_dir in sorted(specs_dir.iterdir()):
            if not spec_dir.is_dir():
                continue
            spec_file = spec_dir / "spec.md"
            if not spec_file.exists():
                continue
            files_read += 1
            status = extract_spec_status(spec_file)
            if status not in ("Approved", "Implementing"):
                continue
            canonical_path = f"spec/{spec_dir.name}"
            if canonical_path not in all_tracked:
                findings.append(ReconciliationFinding(
                    finding_type=1,
                    spec_path=canonical_path,
                    spec_status=status or "",
                    ini_slug="",
                    list_name="",
                ))

    # ── Type 2: Backward scan — stale queue/active entries ────────────────────
    for ini in initiatives:
        for list_name, entries in [("queue", ini.work.queue), ("active", ini.work.active)]:
            for entry in entries:
                spec_file = root / "docs" / "specs" / entry.slug / "spec.md"
                if not spec_file.exists():
                    continue
                files_read += 1
                status = extract_spec_status(spec_file)
                if status in ("Shipped", "Archived"):
                    findings.append(ReconciliationFinding(
                        finding_type=2,
                        spec_path=entry.path,
                        spec_status=status or "",
                        ini_slug=ini.slug,
                        list_name=list_name,
                    ))

    # ── Type 3: Shipped scan — prematurely shipped entries ────────────────────
    for ini in initiatives:
        for entry in ini.work.shipped:
            spec_file = root / "docs" / "specs" / entry.slug / "spec.md"
            if not spec_file.exists():
                continue
            files_read += 1
            status = extract_spec_status(spec_file)
            if status in ("Approved", "Implementing"):
                findings.append(ReconciliationFinding(
                    finding_type=3,
                    spec_path=entry.path,
                    spec_status=status or "",
                    ini_slug=ini.slug,
                    list_name="shipped",
                ))

    return findings, files_read


# ── Main analysis entry point ─────────────────────────────────────────────────

def analyze(root: Path) -> WorkspaceStatusResult:
    """Run full workspace-status analysis from a repo root.

    Reads workspace.toml, extracts initiatives, classifies queue entries,
    and runs the three reconciliation scans.

    Only active initiatives contribute to ready/blocked classifications.
    All initiatives (including paused/closed) participate in reconciliation
    scans (behavior per SKILL.md which does not filter by status in scans).
    """
    t0 = time.monotonic()

    workspace_path = root / "workspace.toml"
    workspace = parse_workspace(workspace_path)
    initiatives = extract_initiatives(workspace)

    all_classifications: list[EntryClassification] = []
    for ini in initiatives:
        if ini.status not in ("active",):
            continue   # Only active initiatives for ready/blocked
        all_classifications.extend(classify_entries(ini, initiatives))

    reconciliation, files_read = run_reconciliation(root, initiatives)

    elapsed = time.monotonic() - t0
    return WorkspaceStatusResult(
        initiatives=initiatives,
        classifications=all_classifications,
        reconciliation=reconciliation,
        files_read=files_read,
        elapsed_s=elapsed,
    )


# ── Argless work-loop resume helper ──────────────────────────────────────────

def get_active_specs(initiatives: list[Initiative]) -> list[tuple[str, str]]:
    """Return (ini_slug, spec_path) pairs for all active specs across active initiatives.

    Used by work-loop argless resume (3-branch logic):
      - len == 0: no active spec; point to workspace-status
      - len == 1: exactly one; begin on it
      - len >= 2: list all; ask user to pick
    """
    result: list[tuple[str, str]] = []
    for ini in initiatives:
        if ini.status != "active":
            continue
        for entry in ini.work.active:
            result.append((ini.slug, entry.path))
    return result


# ── work-loop shaping-item guard helper ──────────────────────────────────────

_SHAPING_TYPE_TO_SKILL: dict[str, str] = {
    "shape":    "frame-intent",
    "research": "desk-research-project-start",
    "strategy": "frame-situation",
    "design":   "experience-status",
    "signal":   "(signal — no action)",
}


def check_shaping_guard(
    spec_slug: str,
    initiatives: list[Initiative],
) -> str | None:
    """Return the routing skill if spec_slug is in a shaping queue; None otherwise.

    work-loop checks this guard at Step 0. If the spec is a shaping item,
    work-loop stops and suggests the appropriate skill instead.
    """
    for ini in initiatives:
        for entry in ini.shaping.active + ini.shaping.backlog:
            if entry.slug == spec_slug:
                return _SHAPING_TYPE_TO_SKILL.get(entry.entry_type, "frame-intent")
    return None


# ── workspace-status Type 2 cleanup mutation shape ────────────────────────────
#
# work-loop (as of commit a46d6f46) no longer writes to workspace.toml
# active/shipped arrays. Its finish checklist only sets spec.md Status: Shipped.
# Cleanup of stale active/queue entries is workspace-status's responsibility
# (Type 2 cleanup write after user confirmation).
#
# This function models that cleanup mutation: given a spec_path that
# workspace-status has identified as stale (Status: Shipped/Archived in spec.md
# but still in active/queue), describe what the cleanup write WOULD do.

def compute_done_step_mutation(
    spec_path: str,
    initiatives: list[Initiative],
) -> dict | None:
    """Describe what workspace-status's Type 2 cleanup WOULD write to workspace.toml.

    This does not perform the write (the engine is read-only).
    Returns a dict describing the mutation, or None if no mutation applies.

    workspace-status Type 2 cleanup (after user confirmation Y):
      - In active (Status Shipped): remove from active → append bare string to shipped
      - In queue (Status Shipped): remove from queue → append bare string to shipped
      - In active/queue (Status Archived): remove only — do NOT add to shipped
      - In neither: no write

    NOTE: work-loop (≥ a46d6f46) no longer performs this write. Cleanup is
    workspace-status's responsibility exclusively.
    """
    for ini in initiatives:
        if any(e.path == spec_path for e in ini.work.active):
            return {
                "ini_slug": ini.slug,
                "source_list": "active",
                "target_list": "shipped",
                "path": spec_path,
                "written_form": f'"{spec_path}"',  # bare string
            }
        if any(e.path == spec_path for e in ini.work.queue):
            return {
                "ini_slug": ini.slug,
                "source_list": "queue",
                "target_list": "shipped",
                "path": spec_path,
                "written_form": f'"{spec_path}"',  # bare string
            }
    return None


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    result = analyze(root)
    active = [i for i in result.initiatives if i.status == "active"]
    print(f"Active initiatives: {len(active)}")
    print(f"Ready queue entries: {len(result.ready)}")
    print(f"Blocked queue entries: {len(result.blocked)}")
    print(f"Reconciliation findings: "
          f"T1={len(result.type1)} T2={len(result.type2)} T3={len(result.type3)}")
    print(f"Spec files read: {result.files_read}")
    print(f"Elapsed: {result.elapsed_s:.3f}s")
