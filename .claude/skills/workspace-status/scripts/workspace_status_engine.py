#!/usr/bin/env python3
"""workspace-status production backend — stdlib-only, read-only.

Entry points:
  analyze(root: Path) -> WorkspaceStatusResult          — full analysis (Type 1+2+3)
  analyze_bounded(root: Path) -> WorkspaceStatusResult  — bounded analysis (Type 2+3 only)
  explain_item(result, selector: str) -> dict           — focused projection from bounded result
  compute_type2_cleanup(ini_slug, source_list, spec_path, spec_status) -> dict

This engine is the canonical implementation invoked by the workspace-status skill
via scripts/workspace_status.py. It reads workspace.toml and docs/specs/** to
produce DAG resolution, reconciliation, and cleanup-planning results.

Known gaps (preserved from Phase 0 characterization):
  KD-01: `backlog:<slug>` prefix absent from SKILL.md table
  KD-02: No cycle detection
  KD-03: Missing dep targets not warned
  KD-04: No quick mode (reconciliation always runs)
  KD-05: work.active/shipped duplicate spec.md Status
  KD-06: shape: resolved against .active only; wording inconsistency in SKILL.md/schema
  KD-07: brief:<path> needs underspecified; brief_queue structure varies
  KD-08: strategy:<slug> needs prefix absent from SKILL.md; treated conservatively
  KD-09: research:<slug> checks only backlog; item in .active (in-progress) erroneously
         reports satisfied — research findings should be committed before unblocking dependents
"""

from __future__ import annotations

import dataclasses
import os
import re
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
class ShapingClassification:
    entry: ShapingEntry
    ini_slug: str
    is_signal: bool      # True for entry_type == "signal" (active context, not actionable)
    is_ready: bool       # True when needs satisfied; always False for signals
    blocking_needs: list[str]


@dataclasses.dataclass
class ReconciliationFinding:
    finding_type: int   # 1, 2, or 3
    spec_path: str
    spec_status: str
    ini_slug: str
    list_name: str      # "queue" | "active" | "shipped" | ""


@dataclasses.dataclass
class WorkLoopStaleWarning:
    """A warn-only stale-queue finding emitted by work-loop Step 0.

    Distinct from workspace-status Type 2 reconciliation:
      - Only active initiatives are checked
      - Only Shipped status triggers a warning (Archived/Approved/Implementing do not)
      - When a path is in both queue and active, ONE warning names both lists
      - No cleanup offer; work-loop only warns
    """
    spec_path: str
    ini_slug: str
    source_lists: list[str]  # ["queue"], ["active"], or ["queue", "active"]


@dataclasses.dataclass
class WorkspaceStatusResult:
    initiatives: list[Initiative]
    classifications: list[EntryClassification]        # work queue entries (ready + blocked)
    shaping_classifications: list[ShapingClassification]  # shaping queue entries
    reconciliation: list[ReconciliationFinding]
    elapsed_s: float  # wall-clock seconds for analyze()
    # [backlog].open typed shaping entries (workspace-level, not per-initiative).
    # Populated by extract_top_level_backlog(); work-loop's shaping-item guard reads these.
    top_level_backlog: list[ShapingEntry] = dataclasses.field(default_factory=list)
    global_scan_performed: bool = dataclasses.field(default=False)
    declared_spec_files_read: int = dataclasses.field(default=0)
    global_scan_files_read: int = dataclasses.field(default=0)

    @property
    def files_read(self) -> int:
        return self.declared_spec_files_read + self.global_scan_files_read

    @property
    def ready(self) -> list[EntryClassification]:
        return [c for c in self.classifications if c.is_ready]

    @property
    def blocked(self) -> list[EntryClassification]:
        return [c for c in self.classifications if not c.is_ready]

    @property
    def ready_shaping(self) -> list[ShapingClassification]:
        return [c for c in self.shaping_classifications if c.is_ready]

    @property
    def signals(self) -> list[ShapingClassification]:
        return [c for c in self.shaping_classifications if c.is_signal]

    @property
    def blocked_shaping(self) -> list[ShapingClassification]:
        return [
            c for c in self.shaping_classifications
            if not c.is_ready and not c.is_signal
        ]

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
        path = raw.get("path", "")   # work inline objects use `path`; `slug` is shaping-only
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
            status=section.get("status", ""),  # absent → "" (not silently promoted to active)
            milestone=section.get("milestone", ""),
            work=work,
            shaping=shaping,
            brief_queue=brief_queue,
        ))
    return initiatives


# ── Status extraction ─────────────────────────────────────────────────────────

# Captures the status content before any annotation (parenthetical or HTML comment).
# A spaced arrow inside "(root → leaf)" must never be read as a transition.
_STATUS_FIELD_RE = re.compile(r'\*\*Status:\*\*\s+(.*?)(?:\s*\(|\s*<!--|$)')
# Finds ALL segments after → (non-whitespace, non-arrow chars), so compact multi-hop
# "Draft→Approved→Shipped" yields ["Approved", "Shipped"] and a non-letter final
# segment (e.g. "→ 2026", trailing "→") still forces None instead of backtracking.
_TRANSITION_ARROW_RE = re.compile(r'→\s*([^→\s]+)')


def _safe_spec_path(root: Path, slug: str) -> Path | None:
    """Return the spec.md Path only if it resolves within root/docs/specs/.

    Rejects slugs containing `..` or absolute paths before joining — resolve()
    alone normalises traversal so the relative_to check would silently accept
    "foo/../bar"; the pre-join rejection closes that gap.
    """
    slug_path = Path(slug)
    if slug_path.is_absolute() or ".." in slug_path.parts:
        return None
    # RuntimeError guards against circular symlinks on Python 3.11/3.12.
    try:
        specs_dir = (root / "docs" / "specs").resolve()
        specs_dir.relative_to(root.resolve())
    except (OSError, RuntimeError, ValueError):
        return None
    try:
        candidate = (specs_dir / slug / "spec.md").resolve()
        candidate.relative_to(specs_dir)
        return candidate
    except (OSError, RuntimeError, ValueError):
        return None


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
        # Anchor to the canonical list-item field form: "- **Status:** ..."
        # A prose line containing **Status:** (example, comment) is not the field.
        if not line.startswith("- **Status:**"):
            continue
        # Strip annotations before scanning — a spaced arrow in "(root → leaf)"
        # must never be read as a transition arrow.
        m = _STATUS_FIELD_RE.search(line)
        if not m:
            continue
        content = m.group(1).strip()
        if "→" in content:
            # Transition form: "Draft → Approved → Shipped" (any arrow spacing).
            # A trailing bare arrow ("Draft → Approved →") has no final segment;
            # reject it explicitly so the preceding segment is never backtracked to.
            if content.rstrip().endswith("→"):
                return None
            # Take the LAST segment; if not a known status, return None — no backtrack.
            segments = _TRANSITION_ARROW_RE.findall(content)
            if segments:
                last = segments[-1]
                return last if last in VALID_STATUSES else None
        else:
            word = content.split()[0] if content.split() else ""
            return word if word in VALID_STATUSES else None
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

    # Local work: "work:<path>" — satisfied only by shipped (schema.md:113).
    # An entry in work.active is "in-progress" but NOT yet satisfied;
    # its dependents remain blocked until the path reaches work.shipped.
    if need.startswith("work:"):
        path = need[len("work:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                return any(e.path == path for e in ini.work.shipped)
        return False

    # Shape: "shape:<slug>" — satisfied when no longer in active (graduated from active shaping).
    # SKILL.md:90, schema.md:114: resolves against .active only.
    # Backlog = scheduled but not yet started; absent from active = treated as done.
    if need.startswith("shape:"):
        slug = need[len("shape:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                active_slugs = {e.slug for e in ini.shaping.active}
                return slug not in active_slugs
        return True  # Initiative not found → assume satisfied

    # Research: "research:<slug>" — satisfied when NOT in shaping backlog as type="research"
    if need.startswith("research:"):
        slug = need[len("research:"):]
        for ini in all_initiatives:
            if ini.slug == ini_slug:
                # Only entries explicitly typed "research" can block a research: need.
                # A shape/signal/design entry with the same slug does NOT block it.
                research_slugs = {
                    e.slug for e in ini.shaping.backlog if e.entry_type == "research"
                }
                return slug not in research_slugs
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

    # `strategy:<slug>` — KD-08: documented in workspace-toml-deps.md but absent from
    # SKILL.md needs-resolution table; treated conservatively as unsatisfied
    if need.startswith("strategy:"):
        return False

    # Unknown prefix — conservatively unsatisfied
    return False


def classify_entries(
    ini: Initiative,
    all_initiatives: list[Initiative],
) -> list[EntryClassification]:
    """Classify queue entries as ready or blocked.

    Entries already in active or shipped are excluded — they are not surfaced
    as ready/blocked in the DAG output (SKILL.md §2: "unconditionally ready
    unless already in active or shipped").
    """
    active_paths = {e.path for e in ini.work.active}
    shipped_paths = {e.path for e in ini.work.shipped}
    results: list[EntryClassification] = []
    for entry in ini.work.queue:
        if entry.path in active_paths or entry.path in shipped_paths:
            continue  # already running or done — not classified
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


def classify_shaping_entries(
    ini: Initiative,
    all_initiatives: list[Initiative],
) -> list[ShapingClassification]:
    """Classify shaping queue entries for an active initiative.

    shaping_queue.active — non-signals are ready; signals are active context.
    shaping_queue.backlog — classified by needs (same resolution as work entries).
    """
    results: list[ShapingClassification] = []

    # Active entries take precedence; deduplicate on (slug, type) so a shape:X active
    # entry does not suppress a research:X backlog entry — they are distinct items.
    active_typed = {(e.slug, e.entry_type) for e in ini.shaping.active}

    for entry in ini.shaping.active:
        is_sig = entry.entry_type == "signal"
        results.append(ShapingClassification(
            entry=entry,
            ini_slug=ini.slug,
            is_signal=is_sig,
            is_ready=not is_sig,
            blocking_needs=[],
        ))

    for entry in ini.shaping.backlog:
        if (entry.slug, entry.entry_type) in active_typed:
            continue  # Same slug + same type: active takes precedence
        is_sig = entry.entry_type == "signal"
        if is_sig:
            results.append(ShapingClassification(
                entry=entry, ini_slug=ini.slug,
                is_signal=True, is_ready=False, blocking_needs=[],
            ))
        elif not entry.needs:
            results.append(ShapingClassification(
                entry=entry, ini_slug=ini.slug,
                is_signal=False, is_ready=True, blocking_needs=[],
            ))
        else:
            blocking = [
                n for n in entry.needs
                if not is_need_satisfied(n, ini.slug, all_initiatives)
            ]
            results.append(ShapingClassification(
                entry=entry,
                ini_slug=ini.slug,
                is_signal=False,
                is_ready=len(blocking) == 0,
                blocking_needs=blocking,
            ))

    return results


# ── Reconciliation ────────────────────────────────────────────────────────────

def _run_type1_scan(
    root: Path,
    all_tracked: set[str],
) -> tuple[list[ReconciliationFinding], int]:
    """Type 1: Forward scan — untracked live specs. Returns (findings, files_read).

    Two callers: run_reconciliation and analyze. Never called by analyze_bounded.
    """
    findings: list[ReconciliationFinding] = []
    files_read = 0
    specs_dir = root / "docs" / "specs"

    # Recurse the full specs tree so nested specs (e.g. docs/specs/group/live/)
    # are discovered; slug is the parent path relative to specs_dir.
    # os.walk(followlinks=False) prevents escaping the repo via symlinked dirs
    # found DURING traversal (rglob follows symlinks on Python 3.11/3.12).
    # The root-confinement check guards against docs/specs or docs/ itself being
    # a symlink — followlinks=False does not apply to the initial top directory.
    _specs_root_safe = False
    if specs_dir.exists():
        try:
            specs_dir.resolve().relative_to(root.resolve())
            _specs_root_safe = True
        except ValueError:
            pass  # docs/specs resolved outside repo root (symlink) — skip walk
    if _specs_root_safe:
        _specs_root_resolved = specs_dir.resolve()
        _visited: set[Path] = set()
        for dirpath, dirnames, filenames in os.walk(str(specs_dir), followlinks=False):
            # Guard: skip this directory if already visited (in-root junction to a
            # previously-scanned sibling). Must run before processing filenames so a
            # junction alias doesn't produce duplicate Type 1 findings for the
            # real directory's spec.md. dirnames.clear() prevents further descent.
            # RuntimeError guards against circular symlinks on Python 3.11/3.12.
            try:
                _current_resolved = Path(dirpath).resolve()
            except (OSError, RuntimeError):
                dirnames.clear()
                continue
            if _current_resolved in _visited:
                dirnames.clear()
                continue
            _visited.add(_current_resolved)
            # Prune subdirs that escape the specs root OR have already been visited.
            # is_relative_to guards against junctions pointing outside the root;
            # the visited set guards against in-root cycles (a junction whose
            # resolved target is an ancestor within the tree).
            # RuntimeError guards against circular symlinks during resolve().
            safe: list[str] = []
            for d in dirnames:
                try:
                    resolved = (Path(dirpath) / d).resolve()
                    if (
                        resolved.is_relative_to(_specs_root_resolved)
                        and resolved not in _visited
                    ):
                        safe.append(d)
                except (OSError, ValueError, RuntimeError):
                    pass
            dirnames[:] = sorted(safe)  # deterministic traversal order
            if "spec.md" not in filenames:
                continue
            spec_file = Path(dirpath) / "spec.md"
            if spec_file.is_symlink():
                continue
            # Derive the slug from the resolved path so NTFS junction aliases
            # that sort before their real target still produce the canonical slug.
            try:
                rel = _current_resolved.relative_to(_specs_root_resolved)
            except ValueError:
                continue
            slug = rel.as_posix()
            slug_path = Path(slug)
            if slug_path.is_absolute() or ".." in slug_path.parts:
                continue
            files_read += 1
            status = extract_spec_status(spec_file)
            if status not in ("Approved", "Implementing"):
                continue
            canonical_path = f"spec/{slug}"
            if canonical_path not in all_tracked:
                findings.append(ReconciliationFinding(
                    finding_type=1,
                    spec_path=canonical_path,
                    spec_status=status or "",
                    ini_slug="",
                    list_name="",
                ))
    return findings, files_read


def _run_type23_scan(
    root: Path,
    initiatives: list[Initiative],
) -> tuple[list[ReconciliationFinding], int]:
    """Type 2 + 3: Backward and shipped scans. Returns (findings, files_read).

    Three callers: run_reconciliation, analyze, and analyze_bounded.
    All declared-spec path resolution goes through _safe_spec_path() — no
    confinement bypass in bounded mode.
    """
    findings: list[ReconciliationFinding] = []
    files_read = 0

    # ── Type 2: Backward scan — stale queue/active entries ────────────────────
    for ini in initiatives:
        for list_name, entries in [("queue", ini.work.queue), ("active", ini.work.active)]:
            for entry in entries:
                spec_file = _safe_spec_path(root, entry.slug)
                if spec_file is None or not spec_file.exists():
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
            spec_file = _safe_spec_path(root, entry.slug)
            if spec_file is None or not spec_file.exists():
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


def run_reconciliation(
    root: Path,
    initiatives: list[Initiative],
) -> tuple[list[ReconciliationFinding], int]:
    """Run all three reconciliation scan types. Returns (findings, files_read)."""
    all_tracked: set[str] = set()
    for ini in initiatives:
        for e in ini.work.queue + ini.work.active + ini.work.shipped:
            all_tracked.add(e.path)

    type1_findings, type1_files = _run_type1_scan(root, all_tracked)
    type23_findings, type23_files = _run_type23_scan(root, initiatives)
    return type1_findings + type23_findings, type1_files + type23_files


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
    all_shaping: list[ShapingClassification] = []
    for ini in initiatives:
        if ini.status not in ("active",):
            continue   # Only active initiatives for ready/blocked and shaping
        all_classifications.extend(classify_entries(ini, initiatives))
        all_shaping.extend(classify_shaping_entries(ini, initiatives))

    # Build all_tracked for the Type 1 scan
    all_tracked: set[str] = set()
    for ini in initiatives:
        for e in ini.work.queue + ini.work.active + ini.work.shipped:
            all_tracked.add(e.path)

    # Call helpers directly (not via run_reconciliation) to obtain split file counts
    type1_findings, type1_files = _run_type1_scan(root, all_tracked)
    type23_findings, type23_files = _run_type23_scan(root, initiatives)
    reconciliation = type1_findings + type23_findings

    top_level_backlog = extract_top_level_backlog(workspace)

    elapsed = time.monotonic() - t0
    return WorkspaceStatusResult(
        initiatives=initiatives,
        classifications=all_classifications,
        shaping_classifications=all_shaping,
        reconciliation=reconciliation,
        elapsed_s=elapsed,
        top_level_backlog=top_level_backlog,
        global_scan_performed=True,
        declared_spec_files_read=type23_files,
        global_scan_files_read=type1_files,
    )


def analyze_bounded(root: Path) -> WorkspaceStatusResult:
    """Run bounded workspace-status analysis (Type 2+3 only; no global spec walk).

    Used by 'status' and 'explain' subcommands. Structurally guarantees no Type 1
    scan: calls _run_type23_scan only, never _run_type1_scan. Path confinement is
    preserved — _run_type23_scan routes all path resolution through _safe_spec_path().
    """
    t0 = time.monotonic()

    workspace_path = root / "workspace.toml"
    workspace = parse_workspace(workspace_path)
    initiatives = extract_initiatives(workspace)

    all_classifications: list[EntryClassification] = []
    all_shaping: list[ShapingClassification] = []
    for ini in initiatives:
        if ini.status not in ("active",):
            continue
        all_classifications.extend(classify_entries(ini, initiatives))
        all_shaping.extend(classify_shaping_entries(ini, initiatives))

    type23_findings, declared_files = _run_type23_scan(root, initiatives)
    top_level_backlog = extract_top_level_backlog(workspace)

    elapsed = time.monotonic() - t0
    return WorkspaceStatusResult(
        initiatives=initiatives,
        classifications=all_classifications,
        shaping_classifications=all_shaping,
        reconciliation=type23_findings,
        elapsed_s=elapsed,
        top_level_backlog=top_level_backlog,
        global_scan_performed=False,
        declared_spec_files_read=declared_files,
        global_scan_files_read=0,
    )


def explain_item(result: WorkspaceStatusResult, selector: str) -> dict:
    """Focused projection of one work-queue item from a bounded status result.

    Lookup is restricted to active initiatives' work queues (queue/active/shipped).
    Shaping entries are not searched. No file I/O; selector is never used as a
    filesystem path component.

    Returns one of:
      {"selector_status": "matched", "explained_item": {...}}
      {"selector_status": "not_found"}
      {"selector_status": "ambiguous", "matches": [...]}
    """
    slug = normalize_for_shaping_guard(selector)
    target_path = f"spec/{slug}"

    # Collect matching active initiatives (one entry per initiative)
    matches: list[dict] = []
    for ini in result.initiatives:
        if ini.status != "active":
            continue
        found_in: list[str] = []
        for list_name, entries in [
            ("active", ini.work.active),
            ("shipped", ini.work.shipped),
            ("queue", ini.work.queue),
        ]:
            if any(e.path == target_path for e in entries):
                found_in.append(list_name)
        if found_in:
            matches.append({"ini_slug": ini.slug, "found_in": found_in})

    if len(matches) == 0:
        return {"selector_status": "not_found"}

    if len(matches) > 1:
        return {
            "selector_status": "ambiguous",
            "matches": [{"path": target_path, "ini_slug": m["ini_slug"]} for m in matches],
        }

    # Exactly one active initiative matched
    match = matches[0]
    ini_slug = match["ini_slug"]
    found_in = match["found_in"]
    ini = next(i for i in result.initiatives if i.slug == ini_slug)

    # Resolve list and classification: active > shipped > queue precedence
    if "active" in found_in:
        item_list = "active"
        classification = "active"
        entry = next(e for e in ini.work.active if e.path == target_path)
        blocking_needs: list[str] = []
        dependencies: list[dict] = []
        sole_blocker = f"work:{target_path}"
        downstream_unblocked: list[str] = [
            c.entry.path
            for c in result.blocked
            if c.ini_slug == ini_slug and c.blocking_needs == [sole_blocker]
        ]
    elif "shipped" in found_in:
        item_list = "shipped"
        classification = "shipped"
        entry = next(e for e in ini.work.shipped if e.path == target_path)
        blocking_needs = []
        dependencies = []
        downstream_unblocked = []
    else:
        item_list = "queue"
        entry = next(e for e in ini.work.queue if e.path == target_path)
        cls = next(
            (
                c for c in result.classifications
                if c.entry.path == target_path and c.ini_slug == ini_slug
            ),
            None,
        )
        if cls is not None:
            classification = "ready" if cls.is_ready else "blocked"
            blocking_needs = cls.blocking_needs
        else:
            classification = "ready"
            blocking_needs = []
        dependencies = [
            {"need": need, "satisfied": need not in blocking_needs}
            for need in entry.needs
        ]
        sole_blocker = f"work:{target_path}"
        downstream_unblocked = [
            c.entry.path
            for c in result.blocked
            if c.ini_slug == ini_slug and c.blocking_needs == [sole_blocker]
        ]

    return {
        "selector_status": "matched",
        "explained_item": {
            "path": target_path,
            "slug": slug,
            "ini_slug": ini_slug,
            "list": item_list,
            "classification": classification,
            "blocking_needs": blocking_needs,
            "dependencies": dependencies,
            "downstream_unblocked": downstream_unblocked,
        },
    }


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

# Explicitly recognised shaping types. Only entries with one of these types
# in [backlog].open are treated as shaping work by check_shaping_guard.
# Untyped entries (ordinary build-backlog items) are excluded.
_SHAPING_TYPES: frozenset[str] = frozenset(
    {"shape", "research", "strategy", "signal", "design"}
)


def extract_top_level_backlog(workspace: dict) -> list[ShapingEntry]:
    """Extract typed shaping entries from [backlog].open.

    work-loop's shaping-item guard (SKILL.md §0 step 2) checks this list in addition
    to per-initiative shaping queues. Only entries with an explicit shaping type
    (shape | research | strategy | signal | design) are returned; untyped dict entries
    and ordinary build-backlog items without a type field are excluded.
    """
    backlog_section = workspace.get("backlog", {})
    if not isinstance(backlog_section, dict):
        return []
    entries = []
    for e in backlog_section.get("open", []):
        if isinstance(e, dict) and e.get("type") in _SHAPING_TYPES:
            entries.append(_parse_shaping_entry(e))
    return entries


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
    top_level_backlog: list[ShapingEntry] | None = None,
) -> str | None:
    """Return the routing skill if spec_slug is in a shaping queue; None otherwise.

    work-loop checks this guard at Step 0 (SKILL.md §0 step 2). Checks:
      - active initiatives' [shaping_queue].active and .backlog
      - top-level [backlog].open typed entries (pass via extract_top_level_backlog)

    Only active initiatives are checked; paused/closed/complete initiatives are skipped.
    If the spec is a shaping item, work-loop stops and suggests the appropriate skill.
    """
    for ini in initiatives:
        if ini.status != "active":
            continue
        for entry in ini.shaping.active + ini.shaping.backlog:
            if entry.slug == spec_slug:
                return _SHAPING_TYPE_TO_SKILL.get(entry.entry_type, "frame-intent")
    for entry in (top_level_backlog or []):
        if entry.slug == spec_slug:
            return _SHAPING_TYPE_TO_SKILL.get(entry.entry_type, "frame-intent")
    return None


def normalize_for_shaping_guard(raw_path: str) -> str:
    """Normalize a spec path to slug form for the shaping-item guard.

    Per work-loop SKILL.md §0 step 2: "Derive slug (strip docs/specs/ prefix + trailing /)."

    Accepted input forms:
      'docs/specs/example/'  → 'example'
      'docs/specs/example'   → 'example'
      'spec/example'         → 'example'
      'example'              → 'example'  (already normalized)
    """
    s = raw_path.rstrip("/")
    if s.startswith("docs/specs/"):
        return s[len("docs/specs/"):]
    if s.startswith("spec/"):
        return s[len("spec/"):]
    return s


# ── work-loop Step 0 stale-queue check ───────────────────────────────────────

def collect_work_loop_stale_warnings(
    root: Path,
    initiatives: list[Initiative],
) -> list[WorkLoopStaleWarning]:
    """Characterize work-loop Step 0 stale-queue check (SKILL.md §0 step 1).

    Checks active initiatives' queue and active entries. Emits a warn-only
    WorkLoopStaleWarning when the entry's spec.md Status is 'Shipped'.

    Differs from workspace-status Type 2 reconciliation:
      - Only active initiatives (paused/closed/complete skipped)
      - Only Shipped triggers a warning; Archived, Approved, Implementing do not
      - When a path appears in both queue and active, emits ONE warning naming both
      - Does not offer or perform cleanup (warn-only)
      - Missing spec.md → skipped without error
    """
    warnings: list[WorkLoopStaleWarning] = []
    for ini in initiatives:
        if ini.status != "active":
            continue
        # Collect all paths with their source lists; a path may appear in both
        path_sources: dict[str, list[str]] = {}
        for list_name, entries in [("queue", ini.work.queue), ("active", ini.work.active)]:
            for entry in entries:
                if entry.path not in path_sources:
                    path_sources[entry.path] = []
                path_sources[entry.path].append(list_name)

        for path, sources in path_sources.items():
            slug = path.removeprefix("spec/")
            spec_file = _safe_spec_path(root, slug)
            if spec_file is None or not spec_file.exists():
                continue
            status = extract_spec_status(spec_file)
            if status != "Shipped":
                continue  # Only Shipped warns; Archived/Approved/Implementing skip
            warnings.append(WorkLoopStaleWarning(
                spec_path=path,
                ini_slug=ini.slug,
                source_lists=sources,
            ))
    return warnings


def _toml_basic_string(s: str) -> str:
    """Return a TOML basic-string literal (with surrounding quotes) for value s.

    json.dumps would emit surrogate-pair escapes (\\ud800\\udc00) for non-BMP
    code points, which are not valid TOML \\u escapes (must be scalar values).
    This helper includes non-BMP characters as UTF-8 literals instead.
    """
    _esc = {
        "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f",
        "\r": "\\r", '"': '\\"', "\\": "\\\\",
    }
    buf = ['"']
    for ch in s:
        e = _esc.get(ch)
        if e:
            buf.append(e)
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            buf.append(f"\\u{ord(ch):04X}")
        else:
            buf.append(ch)
    buf.append('"')
    return "".join(buf)


# ── workspace-status Type 2 cleanup mutation shape ────────────────────────────
#
# work-loop no longer writes to workspace.toml
# active/shipped arrays. Its finish checklist only sets spec.md Status: Shipped.
# Cleanup of stale active/queue entries is workspace-status's responsibility
# (Type 2 cleanup write after user confirmation).
#
# This function models that cleanup mutation: caller provides the exact finding
# fields from run_reconciliation() and receives the mutation shape.

_TYPE2_VALID_STATUSES: frozenset[str] = frozenset({"Shipped", "Archived"})
_TYPE2_VALID_SOURCES: frozenset[str] = frozenset({"active", "queue"})


def compute_type2_cleanup(
    ini_slug: str,
    source_list: str,
    spec_path: str,
    spec_status: str,
) -> dict:
    """Describe what workspace-status Type 2 cleanup WOULD write to workspace.toml.

    Caller must supply the exact fields from a Type 2 ReconciliationFinding:
      ini_slug   — the initiative slug (e.g. "ini-001")
      source_list — "active" | "queue" (the list the finding came from)
      spec_path  — the spec path (e.g. "spec/my-feature")
      spec_status — "Shipped" | "Archived" (from the spec.md Status field)

    Raises ValueError for spec_status outside {"Shipped", "Archived"} or
    source_list outside {"active", "queue"} — these signal a caller bug
    (Type 1 / Type 3 findings should never reach this function).

    workspace-status Type 2 cleanup (after user confirmation Y):
      - Shipped, in active/queue → remove, append bare string to [work].shipped
      - Archived, in active/queue → remove only; do NOT add to shipped

    This engine is read-only; it describes the write shape, not performs it.
    """
    if spec_status not in _TYPE2_VALID_STATUSES:
        raise ValueError(
            f"compute_type2_cleanup: spec_status must be 'Shipped' or 'Archived', "
            f"got {spec_status!r}. Type 1 / Type 3 findings are not eligible."
        )
    if source_list not in _TYPE2_VALID_SOURCES:
        raise ValueError(
            f"compute_type2_cleanup: source_list must be 'active' or 'queue', "
            f"got {source_list!r}."
        )
    if spec_status == "Archived":
        return {
            "ini_slug": ini_slug,
            "source_list": source_list,
            "target_list": None,   # remove only — not added to shipped
            "path": spec_path,
        }
    return {
        "ini_slug": ini_slug,
        "source_list": source_list,
        "target_list": "shipped",
        "path": spec_path,
        "written_form": _toml_basic_string(spec_path),
    }
