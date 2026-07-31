#!/usr/bin/env python3
"""Characterization tests for workspace-status algorithmic behavior.

Tests workspace_status_engine against deterministic fixtures.

IMPORTANT: workspace_status_engine is an executable reference model, NOT
a seam into the production implementation. The live skill is pure LLM
instructions; this engine is a manually transcribed Python interpretation.
These tests prove the Python model is internally consistent; they do not
prove parity with production behavior. See engine docstring for details.

The contract anchor test (test_skill_contract_anchor) will fail when the
DAG-resolution or reconciliation sections of SKILL.md change, signaling
that the engine must be reviewed and updated before re-approving the hash.

Run:  python3 tools/test_workspace_status.py
      python3 -m pytest tools/test_workspace_status.py -q
Exit: 0 if all pass, 1 if any fail.

Known-defect tests are marked with [KNOWN-DEFECT: KD-NN] and describe
intentional existing behavior — not desired future behavior.
"""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Prefer repo-local copy of the engine.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_status_engine import (
    _safe_spec_path,
    analyze,
    check_shaping_guard,
    classify_entries,
    classify_shaping_entries,
    collect_work_loop_stale_warnings,
    compute_type2_cleanup,
    extract_initiatives,
    extract_spec_status,
    extract_top_level_backlog,
    get_active_specs,
    normalize_for_shaping_guard,
    parse_workspace,
    run_reconciliation,
)

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# ── Test infrastructure ───────────────────────────────────────────────────────

FAILURES: list[str] = []


def expect(cond: bool, msg: str) -> None:
    if not cond:
        FAILURES.append(msg)


def write_workspace(root: Path, content: str) -> None:
    (root / "workspace.toml").write_text(textwrap.dedent(content), encoding="utf-8")


def write_spec(root: Path, slug: str, status: str = "Draft") -> None:
    p = root / "docs" / "specs" / slug / "spec.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = f"# Spec: {slug}\n\n- **Status:** {status}\n\n## Acceptance Criteria\n\n- [ ] AC1\n"
    p.write_text(body, encoding="utf-8")


# ── AC2a: Multiple active initiatives ────────────────────────────────────────

def case_multiple_active_initiatives() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Alpha"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = ["spec/alpha-feature"]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []

            ["ini-002"]
            name = "Beta"
            status = "active"
            milestone = "M1"
            ["ini-002".work]
            active  = []
            shipped = []
            queue   = ["spec/beta-feature"]
            ["ini-002".shaping_queue]
            active  = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        active = [i for i in initiatives if i.status == "active"]
        expect(len(active) == 2, f"[AC2a] expected 2 active initiatives, got {len(active)}")
        slugs = {i.slug for i in active}
        expect("ini-001" in slugs and "ini-002" in slugs, f"[AC2a] wrong slugs: {slugs}")


# ── AC2b: Paused and closed initiatives ──────────────────────────────────────

def case_paused_closed_initiatives() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Active"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = ["spec/active-feature"]
            ["ini-001".shaping_queue]
            active = []
            backlog = []

            ["ini-002"]
            name = "Paused"
            status = "paused"
            milestone = "M1"
            ["ini-002".work]
            active  = []
            shipped = []
            queue   = ["spec/paused-feature"]
            ["ini-002".shaping_queue]
            active = []
            backlog = []

            ["ini-003"]
            name = "Closed (documented)"
            status = "closed"
            milestone = "M1"
            ["ini-003".work]
            active  = []
            shipped = ["spec/closed-feature"]
            queue   = []
            ["ini-003".shaping_queue]
            active = []
            backlog = []

            ["ini-004"]
            name = "Complete (legacy)"
            status = "complete"
            milestone = "M1"
            ["ini-004".work]
            active  = []
            shipped = ["spec/complete-feature"]
            queue   = []
            ["ini-004".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        expect(len(initiatives) == 4, f"[AC2b] expected 4 initiatives, got {len(initiatives)}")
        by_status = {i.slug: i.status for i in initiatives}
        expect(by_status.get("ini-001") == "active", "[AC2b] ini-001 status wrong")
        expect(by_status.get("ini-002") == "paused", "[AC2b] ini-002 status wrong")
        # Schema drift: SKILL.md documents 'closed'; some workspace.toml files use 'complete'.
        # Both are exercised here to freeze the vocabulary inconsistency (behavior-map §2).
        expect(by_status.get("ini-003") == "closed",
               "[AC2b] ini-003 status wrong (documented 'closed')")
        expect(by_status.get("ini-004") == "complete",
               "[AC2b] ini-004 status wrong (legacy 'complete')")
        # Paused/closed/complete don't contribute to ready/blocked
        all_cls: list = []
        for ini in initiatives:
            if ini.status == "active":
                all_cls.extend(classify_entries(ini, initiatives))
        paths = {c.entry.path for c in all_cls}
        expect("spec/active-feature" in paths, "[AC2b] active feature should be classified")
        expect(
            "spec/paused-feature" not in paths,
            "[AC2b] paused feature should not be classified",
        )


# ── AC2c: Ordered queues ─────────────────────────────────────────────────────

def case_ordered_queues() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Ordered"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = ["spec/first", "spec/second", "spec/third"]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        ini = initiatives[0]
        paths = [e.path for e in ini.work.queue]
        expect(paths == ["spec/first", "spec/second", "spec/third"],
               f"[AC2c] queue order not preserved: {paths}")


# ── AC2d: Local work dependencies ────────────────────────────────────────────

def case_local_work_deps() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Deps"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = ["spec/prerequisite"]
            queue   = [
              {path = "spec/dependent", needs = "work:spec/prerequisite"},
              {path = "spec/unmet", needs = "work:spec/not-yet-shipped"},
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)
        by_path = {c.entry.path: c for c in cls}

        expect(by_path["spec/dependent"].is_ready,
               "[AC2d] spec/dependent should be ready (prerequisite shipped)")
        expect(not by_path["spec/unmet"].is_ready,
               "[AC2d] spec/unmet should be blocked (not-yet-shipped not in shipped)")
        expect("work:spec/not-yet-shipped" in by_path["spec/unmet"].blocking_needs,
               "[AC2d] blocking need should name the unmet dep")


# ── AC2d-active: work: dep on active item stays blocked until shipped ──────────

def case_local_work_dep_satisfied_by_active() -> None:
    """workspace-toml-schema.md §needs: work:<path> resolves to [work].shipped only.

    A queue entry whose prerequisite is in work.active is NOT yet satisfied —
    it stays blocked until the prerequisite moves to work.shipped.
    The SKILL.md parenthetical "active counts as in-progress" describes status,
    not satisfaction; schema.md:113 is the authoritative resolution rule.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Active Dep"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/in-progress"]
            shipped = []
            queue   = [
              {path = "spec/dependent", needs = "work:spec/in-progress"},
              {path = "spec/blocked-dep", needs = "work:spec/not-started"},
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)
        by_path = {c.entry.path: c for c in cls}

        expect("spec/dependent" in by_path,
               "[AC2d-active] spec/dependent should appear in classification")
        expect(not by_path["spec/dependent"].is_ready,
               "[AC2d-active] dep on active (not yet shipped) spec should be BLOCKED")
        expect(not by_path["spec/blocked-dep"].is_ready,
               "[AC2d-active] dep on absent spec should be blocked")


# ── AC2d-dup: queue entries already in active or shipped are excluded ──────────

def case_queue_entries_in_active_or_shipped_excluded() -> None:
    """SKILL.md §2: entry is ready 'unless already in active or shipped'.

    A path duplicated in both queue and active must NOT appear in the
    ready/blocked classification — it is already running. Similarly, a path
    in both queue and shipped must NOT appear as ready.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Dup Test"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/also-active"]
            shipped = ["spec/also-shipped"]
            queue   = ["spec/also-active", "spec/also-shipped", "spec/normal"]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)
        classified_paths = {c.entry.path for c in cls}

        expect("spec/also-active" not in classified_paths,
               "[AC2d-dup] queue entry already in active must be excluded")
        expect("spec/also-shipped" not in classified_paths,
               "[AC2d-dup] queue entry already in shipped must be excluded")
        expect("spec/normal" in classified_paths,
               "[AC2d-dup] normal queue entry should be classified")


# ── AC2e: Cross-initiative work dependencies ─────────────────────────────────

def case_cross_initiative_deps() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Provider"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = ["spec/provider-spec"]
            queue   = []
            ["ini-001".shaping_queue]
            active = []
            backlog = []

            ["ini-002"]
            name = "Consumer"
            status = "active"
            milestone = "M1"
            ["ini-002".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/consumer-ready", needs = "ini-001:work:spec/provider-spec"},
              {path = "spec/consumer-blocked", needs = "ini-001:work:spec/unshipped"},
            ]
            ["ini-002".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        ini2 = next(i for i in initiatives if i.slug == "ini-002")
        cls = classify_entries(ini2, initiatives)
        by_path = {c.entry.path: c for c in cls}

        expect(by_path["spec/consumer-ready"].is_ready,
               "[AC2e] cross-initiative dep satisfied (provider-spec shipped in ini-001)")
        expect(not by_path["spec/consumer-blocked"].is_ready,
               "[AC2e] cross-initiative dep unsatisfied (unshipped not in ini-001.shipped)")


# ── AC2f: Shape, research, and brief dependencies ────────────────────────────

def case_shape_research_brief_deps() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Shaping Deps"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = [{slug = "active-shape", type = "shape"}]
            backlog = [{slug = "backlog-research", type = "research"}]
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/needs-active-shape",    needs = "shape:active-shape"},
              {path = "spec/needs-absent-shape",    needs = "shape:never-existed"},
              {path = "spec/needs-research-done",   needs = "research:finished-research"},
              {path = "spec/needs-research-pending",needs = "research:backlog-research"},
            ]
            ["ini-001".brief_queue]
            executing = "docs/product/briefs/running-brief.md"
            ready     = ["docs/product/briefs/ready-brief.md"]
            draft     = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        ini = initiatives[0]
        cls = classify_entries(ini, initiatives)
        by_path = {c.entry.path: c for c in cls}

        expect(not by_path["spec/needs-active-shape"].is_ready,
               "[AC2f] shape:active-shape blocked (in active — not yet graduated)")
        expect(by_path["spec/needs-absent-shape"].is_ready,
               "[AC2f] shape:never-existed satisfied (absent from all lists → treated as done)")
        expect(by_path["spec/needs-research-done"].is_ready,
               "[AC2f] research:finished-research satisfied (not in backlog)")
        expect(not by_path["spec/needs-research-pending"].is_ready,
               "[AC2f] research:backlog-research blocked (in backlog)")


# ── AC2g: Ready and transitively blocked ─────────────────────────────────────

def case_ready_and_transitively_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # A → B → C: C blocks B blocks A; D is ready
        write_workspace(root, """
            ["ini-001"]
            name = "Chain"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/A", needs = "work:spec/B"},
              {path = "spec/B", needs = "work:spec/C"},
              {path = "spec/C"},
              "spec/D",
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)
        by_path = {c.entry.path: c for c in cls}

        expect(not by_path["spec/A"].is_ready, "[AC2g] A should be blocked (B not shipped)")
        expect(not by_path["spec/B"].is_ready, "[AC2g] B should be blocked (C not shipped)")
        expect(by_path["spec/C"].is_ready, "[AC2g] C should be ready (no deps)")
        expect(by_path["spec/D"].is_ready, "[AC2g] D should be ready (no deps)")
        # Note: transitive blocking is not deep-resolved by the engine;
        # A is blocked because its immediate dep B is not shipped, not because C is unshipped.
        expect("work:spec/B" in by_path["spec/A"].blocking_needs,
               "[AC2g] A's blocking need should name spec/B directly")


# ── AC2h: Spec status vocabulary ─────────────────────────────────────────────

def case_spec_statuses() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for status in ("Draft", "Approved", "Implementing", "Shipped", "Archived"):
            write_spec(root, f"spec-{status.lower()}", status)
        # Transition form
        p = root / "docs" / "specs" / "spec-transition" / "spec.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# T\n\n- **Status:** Approved → Shipped\n", encoding="utf-8")

        for status in ("Draft", "Approved", "Implementing", "Shipped", "Archived"):
            spec_file = root / "docs" / "specs" / f"spec-{status.lower()}" / "spec.md"
            extracted = extract_spec_status(spec_file)
            expect(extracted == status, f"[AC2h] expected {status}, got {extracted}")

        transition_status = extract_spec_status(
            root / "docs" / "specs" / "spec-transition" / "spec.md"
        )
        expect(transition_status == "Shipped",
               f"[AC2h] transition form should yield 'Shipped', got {transition_status}")

        # Multi-arrow form: last target wins (greedy regex)
        p_multi = root / "docs" / "specs" / "spec-multi-arrow" / "spec.md"
        p_multi.parent.mkdir(parents=True, exist_ok=True)
        p_multi.write_text("# M\n\n- **Status:** Draft → Approved → Shipped\n", encoding="utf-8")
        multi_status = extract_spec_status(p_multi)
        expect(multi_status == "Shipped",
               f"[AC2h] multi-arrow form last segment should be 'Shipped', got {multi_status}")

        # Arrow in annotation comment must not poison the status
        p_annot = root / "docs" / "specs" / "spec-annot-arrow" / "spec.md"
        p_annot.parent.mkdir(parents=True, exist_ok=True)
        p_annot.write_text(
            "# A\n\n- **Status:** Shipped (tracing: root→leaf)\n", encoding="utf-8"
        )
        annot_status = extract_spec_status(p_annot)
        expect(annot_status == "Shipped",
               f"[AC2h] arrow in annotation should not override status, got {annot_status}")

        # Unknown final segment must not backtrack to an earlier known status
        p_unk = root / "docs" / "specs" / "spec-unknown-final" / "spec.md"
        p_unk.parent.mkdir(parents=True, exist_ok=True)
        p_unk.write_text(
            "# U\n\n- **Status:** Approved → Cancelled\n", encoding="utf-8"
        )
        unk_status = extract_spec_status(p_unk)
        expect(unk_status is None,
               f"[AC2h] unknown final segment should yield None, got {unk_status}")

        # Spaced arrow inside parenthetical annotation must not be read as a transition
        p_spaced = root / "docs" / "specs" / "spec-spaced-annot" / "spec.md"
        p_spaced.parent.mkdir(parents=True, exist_ok=True)
        p_spaced.write_text(
            "# S\n\n- **Status:** Shipped (root → leaf)\n", encoding="utf-8"
        )
        spaced_status = extract_spec_status(p_spaced)
        expect(spaced_status == "Shipped",
               f"[AC2h] spaced annotation arrow should not override status,"
               f" got {spaced_status}")

        # No-space transition arrow must be treated as a transition, not a simple word
        p_nospace = root / "docs" / "specs" / "spec-nospace-trans" / "spec.md"
        p_nospace.parent.mkdir(parents=True, exist_ok=True)
        p_nospace.write_text(
            "# N\n\n- **Status:** Approved→Shipped\n", encoding="utf-8"
        )
        nospace_status = extract_spec_status(p_nospace)
        expect(nospace_status == "Shipped",
               f"[AC2h] no-space transition should yield last segment, got {nospace_status}")


# ── AC2i: Missing spec paths ──────────────────────────────────────────────────

def case_missing_spec_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Missing"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = ["spec/missing-shipped"]
            queue   = [
              {path = "spec/missing-dep", needs = "work:spec/missing-shipped"},
              "spec/missing-nodeps",
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        # No spec files created — all paths are missing
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)
        by_path = {c.entry.path: c for c in cls}

        # missing-dep: prerequisite is in shipped, so ready even if spec.md absent
        expect(by_path["spec/missing-dep"].is_ready,
               "[AC2i] missing-dep ready (dep is shipped, spec absence irrelevant to DAG)")
        expect(by_path["spec/missing-nodeps"].is_ready,
               "[AC2i] missing-nodeps ready (no deps)")

        # Reconciliation: missing spec files silently skipped (no warning per SKILL.md)
        findings, _ = run_reconciliation(root, initiatives)
        expect(
            len(findings) == 0,
            f"[AC2i] missing spec files should be silently skipped, got {len(findings)} findings",
        )


# ── AC2j: Missing dependency targets ─────────────────────────────────────────

def case_missing_dep_targets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "MissingDep"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/needs-ghost", needs = "work:spec/ghost-spec"},
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        # spec/ghost-spec is not in queue, active, or shipped — it doesn't exist at all
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)

        # [KNOWN-DEFECT: KD-03] Missing dep targets are silently treated as unsatisfied.
        # No warning is issued. The entry is blocked forever with no diagnostic.
        expect(not cls[0].is_ready,
               "[AC2j][KD-03] spec/needs-ghost should be blocked (ghost-spec never satisfied)")
        expect("work:spec/ghost-spec" in cls[0].blocking_needs,
               "[AC2j][KD-03] blocking need should name ghost-spec")


# ── AC2k: Dependency cycles ───────────────────────────────────────────────────

def case_dependency_cycles() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Cycle"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/cycle-a", needs = "work:spec/cycle-b"},
              {path = "spec/cycle-b", needs = "work:spec/cycle-a"},
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)
        by_path = {c.entry.path: c for c in cls}

        # [KNOWN-DEFECT: KD-02] No cycle detection: both entries show as blocked forever.
        # No error is raised, no cycle diagnostic is emitted.
        expect(not by_path["spec/cycle-a"].is_ready,
               "[AC2k][KD-02] cycle-a blocked (cycle-b not shipped)")
        expect(not by_path["spec/cycle-b"].is_ready,
               "[AC2k][KD-02] cycle-b blocked (cycle-a not shipped)")


# ── AC2l: Untracked Approved/Implementing spec (Type 1) ──────────────────────

def case_type1_untracked_live_spec() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Tracked"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = ["spec/tracked-shipped"]
            queue   = ["spec/tracked-queued"]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        # Tracked specs
        write_spec(root, "tracked-shipped", "Shipped")
        write_spec(root, "tracked-queued", "Draft")
        # Untracked specs that SHOULD generate Type 1
        write_spec(root, "untracked-approved", "Approved")
        write_spec(root, "untracked-implementing", "Implementing")
        # Untracked spec with non-live status (should NOT generate Type 1)
        write_spec(root, "untracked-draft", "Draft")
        write_spec(root, "untracked-shipped", "Shipped")

        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        findings, _ = run_reconciliation(root, initiatives)
        type1 = [f for f in findings if f.finding_type == 1]
        type1_paths = {f.spec_path for f in type1}

        expect("spec/untracked-approved" in type1_paths,
               "[AC2l] untracked-approved should be Type 1")
        expect("spec/untracked-implementing" in type1_paths,
               "[AC2l] untracked-implementing should be Type 1")
        expect("spec/untracked-draft" not in type1_paths,
               "[AC2l] untracked-draft should NOT be Type 1 (Draft is not live)")
        expect("spec/untracked-shipped" not in type1_paths,
               "[AC2l] untracked-shipped should NOT be Type 1 (Shipped is not live)")
        expect("spec/tracked-shipped" not in type1_paths,
               "[AC2l] tracked-shipped should NOT be Type 1 (tracked)")


# ── AC2m: Stale queue/active entries (Type 2) ────────────────────────────────

def case_type2_stale_entries() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Stale"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/active-but-shipped", "spec/active-but-archived"]
            shipped = ["spec/correctly-shipped"]
            queue   = ["spec/queue-but-shipped", "spec/queue-still-draft"]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        write_spec(root, "active-but-shipped", "Shipped")
        write_spec(root, "active-but-archived", "Archived")
        write_spec(root, "correctly-shipped", "Shipped")
        write_spec(root, "queue-but-shipped", "Shipped")
        write_spec(root, "queue-still-draft", "Draft")

        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        findings, _ = run_reconciliation(root, initiatives)
        type2 = [f for f in findings if f.finding_type == 2]
        type2_paths = {(f.spec_path, f.list_name) for f in type2}

        expect(("spec/active-but-shipped", "active") in type2_paths,
               "[AC2m] active-but-shipped should be Type 2 (in active, Status=Shipped)")
        expect(("spec/active-but-archived", "active") in type2_paths,
               "[AC2m] active-but-archived should be Type 2 (in active, Status=Archived)")
        expect(("spec/queue-but-shipped", "queue") in type2_paths,
               "[AC2m] queue-but-shipped should be Type 2 (in queue, Status=Shipped)")
        expect(("spec/queue-still-draft", "queue") not in type2_paths,
               "[AC2m] queue-still-draft should NOT be Type 2 (Status=Draft)")
        expect(("spec/correctly-shipped", "shipped") not in type2_paths,
               "[AC2m] correctly-shipped in shipped list should NOT be Type 2")


# ── AC2n: Prematurely shipped entries (Type 3) ───────────────────────────────

def case_type3_premature_shipped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Premature"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = [
              "spec/shipped-but-approved",
              "spec/shipped-but-implementing",
              "spec/correctly-shipped",
              "spec/shipped-draft",
            ]
            queue = []
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        write_spec(root, "shipped-but-approved", "Approved")
        write_spec(root, "shipped-but-implementing", "Implementing")
        write_spec(root, "correctly-shipped", "Shipped")
        write_spec(root, "shipped-draft", "Draft")

        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        findings, _ = run_reconciliation(root, initiatives)
        type3 = [f for f in findings if f.finding_type == 3]
        type3_paths = {f.spec_path for f in type3}

        expect("spec/shipped-but-approved" in type3_paths,
               "[AC2n] shipped-but-approved should be Type 3")
        expect("spec/shipped-but-implementing" in type3_paths,
               "[AC2n] shipped-but-implementing should be Type 3")
        expect("spec/correctly-shipped" not in type3_paths,
               "[AC2n] correctly-shipped should NOT be Type 3")
        expect("spec/shipped-draft" not in type3_paths,
               "[AC2n] shipped-draft should NOT be Type 3 (Draft is not live)")


# ── AC2o: Multiple active items for argless work-loop ────────────────────────

def case_multiple_active_for_workloop() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # Branch 0: no active
        write_workspace(root, """
            ["ini-001"]
            name = "Zero Active"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = ["spec/queued"]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        active_specs = get_active_specs(initiatives)
        n = len(active_specs)
        expect(n == 0, f"[AC2o] branch-0: expected 0 active, got {n}")

        # Branch 1: exactly one active
        write_workspace(root, """
            ["ini-001"]
            name = "One Active"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/current-work"]
            shipped = []
            queue   = []
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        active_specs = get_active_specs(initiatives)
        n = len(active_specs)
        expect(n == 1, f"[AC2o] branch-1: expected 1 active, got {n}")
        expect(active_specs[0][1] == "spec/current-work", f"[AC2o] wrong path: {active_specs[0]}")

        # Branch 2+: multiple active (two in one initiative)
        write_workspace(root, """
            ["ini-001"]
            name = "Two Active"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/work-a", "spec/work-b"]
            shipped = []
            queue   = []
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        active_specs = get_active_specs(initiatives)
        n = len(active_specs)
        expect(n == 2, f"[AC2o] branch-2+: expected 2 active, got {n}")

        # Branch 2+: across two initiatives
        write_workspace(root, """
            ["ini-001"]
            name = "Ini One"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/work-in-ini1"]
            shipped = []
            queue   = []
            ["ini-001".shaping_queue]
            active = []
            backlog = []

            ["ini-002"]
            name = "Ini Two"
            status = "active"
            milestone = "M1"
            ["ini-002".work]
            active  = ["spec/work-in-ini2"]
            shipped = []
            queue   = []
            ["ini-002".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        active_specs = get_active_specs(initiatives)
        n = len(active_specs)
        expect(n == 2, f"[AC2o] cross-ini: expected 2 active, got {n}")


# ── AC2p: Deferred backlog anchors ───────────────────────────────────────────

def case_deferred_backlog_anchors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Backlog"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/needs-backlog", needs = "backlog:some-backlog-item"},
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []

            [backlog]
            open = [
              {slug = "some-backlog-item"},
              {slug = "another-item"},
            ]
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)

        # [KNOWN-DEFECT: KD-01] backlog:<slug> not in SKILL.md table;
        # treated conservatively as unsatisfied.
        expect(not cls[0].is_ready,
               "[AC2p][KD-01] needs backlog:some-backlog-item treated as unsatisfied (known gap)")

        # Verify the backlog section is parseable
        backlog = ws.get("backlog", {}).get("open", [])
        slugs = [e.get("slug") if isinstance(e, dict) else e for e in backlog]
        expect("some-backlog-item" in slugs, "[AC2p] backlog.open parseable")
        expect("another-item" in slugs, "[AC2p] backlog.open second entry parseable")


def case_strategy_prefix_gap() -> None:
    """[KD-08] strategy:<slug> prefix is documented but absent from SKILL.md table.

    Treated conservatively as unsatisfied — same pattern as backlog: (KD-01).
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Strategy gap"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/needs-strategy", needs = "strategy:some-strategy-item"},
              {path = "spec/no-strategy-dep"},
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)
        by_path = {c.entry.path: c for c in cls}

        # [KNOWN-DEFECT: KD-08] strategy:<slug> not in SKILL.md table;
        # treated conservatively as unsatisfied.
        expect(
            not by_path["spec/needs-strategy"].is_ready,
            "[KD-08] strategy: prefix treated as unsatisfied (known gap)",
        )
        expect(
            by_path["spec/no-strategy-dep"].is_ready,
            "[KD-08] entry without strategy: dep is unaffected",
        )


# ── AC3e: Argless work-loop resume (covered by AC2o above) ───────────────────
# AC3e is satisfied by case_multiple_active_for_workloop.


# ── AC3f: work-loop shaping-item guard ───────────────────────────────────────

def case_shaping_item_guard() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Guard Test"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = [
              {slug = "needs-shaping",    type = "shape"},
              {slug = "needs-research",   type = "research"},
              {slug = "needs-strategy",   type = "strategy"},
              {slug = "needs-design",     type = "design"},
            ]
            backlog = [
              {slug = "backlog-signal",   type = "signal"},
            ]
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)

        expect(check_shaping_guard("needs-shaping", initiatives) == "frame-intent",
               "[AC3f] shape → frame-intent")
        expect(check_shaping_guard("needs-research", initiatives) == "desk-research-project-start",
               "[AC3f] research → desk-research-project-start")
        expect(check_shaping_guard("needs-strategy", initiatives) == "frame-situation",
               "[AC3f] strategy → frame-situation")
        expect(check_shaping_guard("needs-design", initiatives) == "experience-status",
               "[AC3f] design → experience-status")
        expect(check_shaping_guard("backlog-signal", initiatives) == "(signal — no action)",
               "[AC3f] signal → no-action marker")
        expect(check_shaping_guard("not-a-shaping-item", initiatives) is None,
               "[AC3f] non-shaping spec → None (not guarded)")


# ── AC3f ext: shaping guard — paused initiative and top-level backlog ─────────

def case_shaping_guard_paused_initiative() -> None:
    """Paused initiative's shaping items must NOT be guarded (filter: status == "active" only)."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Paused Initiative"
            status = "paused"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = [{slug = "paused-shape", type = "shape"}]
            backlog = []
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)

        result = check_shaping_guard("paused-shape", initiatives)
        expect(result is None,
               f"[AC3f-paused] paused initiative shaping item → None (not guarded),"
               f" got {result!r}")


def case_shaping_guard_top_level_backlog() -> None:
    """Top-level [backlog].open typed entries must be checked by check_shaping_guard."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Active Initiative"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = []

            [backlog]
            open = [
              {slug = "top-shape",    type = "shape"},
              {slug = "top-research", type = "research"},
            ]
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        top_backlog = extract_top_level_backlog(ws)

        # Without top_level_backlog parameter → not guarded (shows the gap the param fills)
        expect(check_shaping_guard("top-shape", initiatives) is None,
               "[AC3f-toplevel] top-level backlog item → None without top_level_backlog param")

        # With top_level_backlog parameter → correctly routed
        result = check_shaping_guard("top-shape", initiatives, top_level_backlog=top_backlog)
        expect(result == "frame-intent",
               f"[AC3f-toplevel] top-level shape → frame-intent, got {result!r}")

        result2 = check_shaping_guard("top-research", initiatives, top_level_backlog=top_backlog)
        expect(result2 == "desk-research-project-start",
               f"[AC3f-toplevel] top-level research → desk-research-project-start,"
               f" got {result2!r}")

        # Non-shaping slug → still None
        result3 = check_shaping_guard("not-here", initiatives, top_level_backlog=top_backlog)
        expect(result3 is None,
               f"[AC3f-toplevel] non-shaping slug → None, got {result3!r}")


# ── AC3g: workspace-status Type 2 cleanup mutation shape ────────────────────────
# NOTE: work-loop (≥ a46d6f46) no longer writes active/shipped to workspace.toml.
# Its finish checklist only sets spec.md Status: Shipped. Cleanup of stale
# active/queue entries is workspace-status's Type 2 cleanup write.

def case_type2_cleanup_ownership() -> None:
    """AC3g: workspace-status owns Type 2 cleanup; work-loop does not mutate queue/active/shipped.

    work-loop (≥ a46d6f46) only sets spec.md Status: Shipped at completion.
    Stale queue/active entries are workspace-status's responsibility (Type 2).
    compute_type2_cleanup describes the write the skill would perform after Y confirmation.

    Caller provides exact (ini_slug, source_list) from the ReconciliationFinding;
    the function does not search — it maps the finding to the mutation shape.
    """
    # Shipped, in active → remove from active, append to shipped
    mut = compute_type2_cleanup("ini-001", "active", "spec/stale-active", "Shipped")
    expect(mut["source_list"] == "active", f"[AC3g] source=active: {mut}")
    expect(mut["target_list"] == "shipped", f"[AC3g] target=shipped: {mut}")
    expect(mut["written_form"] == '"spec/stale-active"', f"[AC3g] bare string form: {mut}")

    # Shipped, in queue → remove from queue, append to shipped
    mut2 = compute_type2_cleanup("ini-001", "queue", "spec/stale-queued", "Shipped")
    expect(mut2["source_list"] == "queue", f"[AC3g] source=queue: {mut2}")
    expect(mut2["target_list"] == "shipped", f"[AC3g] target=shipped: {mut2}")

    # Archived, in active → remove from active, NOT added to shipped
    mut3 = compute_type2_cleanup("ini-001", "active", "spec/stale-active-archived",
                                  "Archived")
    expect(mut3["source_list"] == "active", f"[AC3g] Archived source=active: {mut3}")
    expect(mut3["target_list"] is None,
           f"[AC3g] Archived target=None (remove only): {mut3}")

    # Archived, in queue → remove from queue, NOT added to shipped
    mut4 = compute_type2_cleanup("ini-001", "queue", "spec/stale-queued-archived",
                                  "Archived")
    expect(mut4["source_list"] == "queue", f"[AC3g] Archived source=queue: {mut4}")
    expect(mut4["target_list"] is None,
           f"[AC3g] Archived target=None (remove only): {mut4}")


# ── AC3a: DAG all needs prefix forms ─────────────────────────────────────────

def case_dag_all_needs_prefixes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "All Prefixes"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = []
            backlog = [{slug = "pending-research", type = "research"}]
            ["ini-001".brief_queue]
            executing = ""
            ready     = ["docs/product/briefs/ready.md"]
            draft     = []
            ["ini-001".work]
            active  = []
            shipped = ["spec/shipped-work"]
            queue   = [
              {path = "spec/p-work",     needs = "work:spec/shipped-work"},
              {path = "spec/p-shape",    needs = "shape:graduated-shape"},
              {path = "spec/p-research", needs = "research:done-research"},
              {path = "spec/p-brief",    needs = "brief:docs/product/briefs/ready.md"},
              {path = "spec/p-cross",    needs = "ini-001:work:spec/shipped-work"},
            ]

            ["ini-002"]
            name = "Provider"
            status = "active"
            milestone = "M1"
            ["ini-002".shaping_queue]
            active  = []
            backlog = []
            ["ini-002".work]
            active  = []
            shipped = []
            queue   = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        ini = next(i for i in initiatives if i.slug == "ini-001")
        cls = classify_entries(ini, initiatives)
        by_path = {c.entry.path: c for c in cls}

        expect(by_path["spec/p-work"].is_ready, "[AC3a] work: prefix satisfied")
        expect(by_path["spec/p-shape"].is_ready, "[AC3a] shape: prefix satisfied (absent = graduated)")
        expect(by_path["spec/p-research"].is_ready, "[AC3a] research: prefix (not in backlog)")
        expect(by_path["spec/p-brief"].is_ready, "[AC3a] brief: prefix satisfied")
        expect(by_path["spec/p-cross"].is_ready, "[AC3a] cross-ini prefix satisfied")

        # Unsatisfied variants
        write_workspace(root, """
            ["ini-001"]
            name = "Unsatisfied"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = []
            backlog = [{slug = "pending-research", type = "research"}]
            ["ini-001".brief_queue]
            executing = ""
            ready     = []
            draft     = []
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/p-work-bad",     needs = "work:spec/not-shipped"},
              {path = "spec/p-research-bad", needs = "research:pending-research"},
              {path = "spec/p-brief-bad",    needs = "brief:docs/product/briefs/not-ready.md"},
              {path = "spec/p-cross-bad",    needs = "ini-999:work:spec/not-shipped"},
              {path = "spec/p-backlog-bad",  needs = "backlog:some-item"},
            ]

            ["ini-002"]
            name = "Provider"
            status = "active"
            milestone = "M1"
            ["ini-002".shaping_queue]
            active  = []
            backlog = []
            ["ini-002".work]
            active  = []
            shipped = []
            queue   = []
        """)
        ws2 = parse_workspace(root / "workspace.toml")
        initiatives2 = extract_initiatives(ws2)
        ini2 = next(i for i in initiatives2 if i.slug == "ini-001")
        cls2 = classify_entries(ini2, initiatives2)
        by_path2 = {c.entry.path: c for c in cls2}

        expect(not by_path2["spec/p-work-bad"].is_ready, "[AC3a] work: prefix unsatisfied")
        expect(
            not by_path2["spec/p-research-bad"].is_ready, "[AC3a] research: in backlog -> blocked"
        )
        expect(not by_path2["spec/p-brief-bad"].is_ready, "[AC3a] brief: not in ready -> blocked")
        expect(not by_path2["spec/p-cross-bad"].is_ready, "[AC3a] unknown ini -> blocked")
        expect(
            not by_path2["spec/p-backlog-bad"].is_ready, "[AC3a][KD-01] backlog: prefix blocked"
        )


# ── Integration: full analyze() on a multi-initiative workspace ───────────────

def case_full_analyze() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Main"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/in-progress"]
            shipped = ["spec/done"]
            queue   = [
              "spec/ready-queued",
              {path = "spec/blocked-queued", needs = "work:spec/not-done"},
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []

            ["ini-002"]
            name = "Secondary"
            status = "paused"
            milestone = "M1"
            ["ini-002".work]
            active  = []
            shipped = []
            queue   = ["spec/paused-work"]
            ["ini-002".shaping_queue]
            active = []
            backlog = []
        """)
        write_spec(root, "in-progress", "Implementing")
        write_spec(root, "done", "Shipped")
        write_spec(root, "ready-queued", "Approved")   # in queue with Approved status — not stale
        write_spec(root, "blocked-queued", "Draft")
        write_spec(root, "untracked-approved", "Approved")   # Type 1

        result = analyze(root)

        # Active initiatives
        active_inis = [i for i in result.initiatives if i.status == "active"]
        expect(len(active_inis) == 1, f"[integration] 1 active initiative, got {len(active_inis)}")

        # Ready/blocked
        ready_paths = {c.entry.path for c in result.ready}
        blocked_paths = {c.entry.path for c in result.blocked}
        expect("spec/ready-queued" in ready_paths,
               f"[integration] spec/ready-queued should be ready; ready={ready_paths}")
        expect("spec/blocked-queued" in blocked_paths,
               f"[integration] spec/blocked-queued should be blocked; blocked={blocked_paths}")

        # Type 1: untracked-approved
        type1_paths = {f.spec_path for f in result.type1}
        expect("spec/untracked-approved" in type1_paths,
               f"[integration] untracked-approved should be Type 1; type1={type1_paths}")


# ── Contract anchor — SKILL.md drift guard ───────────────────────────────────
#
# SHA-256 of SKILL.md lines 66–180 (ready/blocked definitions, DAG resolution,
# reconciliation sections — the full algorithmic contract).
# When this test fails, the engine's interpretation may be stale. Read the
# changed sections and reconcile before updating the constant.
_SKIP_ANCHOR_ENV = "WORKSPACE_STATUS_SKIP_ANCHOR"

_SKILL_CONTRACT_HASH = (
    "c0c2166e2a12472c1255602ccaad750cf6290646a510d83151a4a46e5a6f8984"
)
_SKILL_MD = (
    Path(__file__).resolve().parent.parent
    / "packs/core/.apm/skills/workspace-status/SKILL.md"
)

_WORK_LOOP_CONTRACT_HASH = (
    "d2d59e668a8b3003eba484026e9057c31bdd8dedc858384a8a5ceffc2d3b78bc"
)
_WORK_LOOP_MD = (
    Path(__file__).resolve().parent.parent
    / "packs/core/.apm/skills/work-loop/SKILL.md"
)


def _check_anchor(
    skill_path: Path,
    line_slice: tuple[int, int],
    expected_hash: str,
    label: str,
) -> None:
    """Shared logic for contract-anchor cases.

    Fails hard when the skill file is absent in the canonical repo.
    Set WORKSPACE_STATUS_SKIP_ANCHOR=1 to raise unittest.SkipTest, which
    pytest surfaces as a skip and the custom runner counts as 'skipped' —
    never as passed.
    """
    if not skill_path.exists():
        if os.environ.get(_SKIP_ANCHOR_ENV, "").lower() in ("1", "true", "yes"):
            raise unittest.SkipTest(
                f"{label}: skill absent, {_SKIP_ANCHOR_ENV} set"
            )
        expect(
            False,
            f"[{label}] skill file not found at {skill_path}. "
            f"Set {_SKIP_ANCHOR_ENV}=1 to skip in isolated environments.",
        )
        return
    raw = skill_path.read_bytes().splitlines(keepends=True)
    start, end = line_slice
    contract = b"".join(raw[start:end])
    actual = hashlib.sha256(contract).hexdigest()
    expect(
        actual == expected_hash,
        f"[{label}] skill contract changed "
        f"(expected {expected_hash[:12]}…, got {actual[:12]}…). "
        "Review the changed sections and update workspace_status_engine.py "
        f"before updating the hash constant.",
    )


def case_skill_contract_anchor() -> None:
    """Fail when the DAG/reconciliation contract of workspace-status SKILL.md changes.

    Anchors lines 66–180 (0-indexed 65–179): ready/blocked definitions, DAG
    resolution, and reconciliation sections.
    """
    _check_anchor(_SKILL_MD, (65, 180), _SKILL_CONTRACT_HASH,
                  "workspace-status contract")


def case_work_loop_contract_anchor() -> None:
    """Fail when the Step 0 ORIENT contract of work-loop SKILL.md changes.

    The engine characterizes work-loop Step 0 behaviors (lines 69–88):
      - Argless active-spec resolution (get_active_specs)
      - Stale-queue check
      - Shaping-item guard (check_shaping_guard / extract_top_level_backlog)
    """
    _check_anchor(_WORK_LOOP_MD, (68, 88), _WORK_LOOP_CONTRACT_HASH,
                  "work-loop Step-0 contract")


def test_skill_contract_anchor() -> None:
    """pytest entry point for the workspace-status contract anchor."""
    before = len(FAILURES)
    case_skill_contract_anchor()
    after = len(FAILURES)
    assert after == before, "\n".join(FAILURES[before:])


def test_work_loop_contract_anchor() -> None:
    """pytest entry point for the work-loop Step 0 contract anchor."""
    before = len(FAILURES)
    case_work_loop_contract_anchor()
    after = len(FAILURES)
    assert after == before, "\n".join(FAILURES[before:])


# ── Type 2 cleanup mutation contract ─────────────────────────────────────────
#
# The engine is read-only; it describes the SHAPE of the cleanup write but does
# not perform it. The following cases cover:
#   - Shipped entry in queue → mutation: queue removed, appended to shipped
#   - Shipped entry in active → mutation: active removed, appended to shipped
#   - Archived entry in queue → mutation: queue removed, NOT added to shipped
#   - Entry absent → no mutation
#
# Acceptance gaps (not exercised here; to be covered in Order 1):
#   - Comment-preserving TOML write (tomlkit) — engine is read-only
#   - Y-confirmation boundary — model-layer behavior, not algorithmic
#   - Deduplication in [work].shipped — tomlkit write path, not engine
#   - Type 1/Type 3 findings do NOT trigger a cleanup offer — not tested here

def case_type2_cleanup_mutation_contract() -> None:
    # Shipped in active → active removed, appended to shipped
    mut = compute_type2_cleanup("ini-001", "active", "spec/stale-active-shipped", "Shipped")
    expect(mut["source_list"] == "active", "[cleanup] source=active for shipped-in-active")
    expect(mut["target_list"] == "shipped", "[cleanup] target=shipped for shipped-in-active")
    expect(
        mut["written_form"] == '"spec/stale-active-shipped"',
        "[cleanup] bare string form for shipped entry",
    )

    # Shipped in queue → queue removed, appended to shipped
    mut2 = compute_type2_cleanup("ini-001", "queue", "spec/stale-queue-shipped", "Shipped")
    expect(mut2["source_list"] == "queue", "[cleanup] source=queue for shipped-in-queue")
    expect(mut2["target_list"] == "shipped", "[cleanup] target=shipped")

    # Archived in active → removed only, NOT added to shipped
    mut3 = compute_type2_cleanup("ini-001", "active", "spec/stale-active-archived",
                                  "Archived")
    expect(mut3["source_list"] == "active", "[cleanup] Archived source=active")
    expect(mut3["target_list"] is None, "[cleanup] Archived target=None (remove only)")


def case_type1_type3_no_cleanup() -> None:
    """Negative assertions: compute_type2_cleanup rejects ineligible statuses and sources.

    Type 1 findings have spec_status Approved or Implementing (untracked live spec).
    Type 3 findings have spec_status Approved or Implementing (spec in shipped but
    not yet actually done). Neither is eligible for Type 2 cleanup.

    The function raises ValueError for:
      - spec_status outside {"Shipped", "Archived"}  — catches Type 1 / Type 3 callers
      - source_list outside {"active", "queue"}       — catches Type 3 shipped-list source
    """
    # Type 1 guard: Approved status → ValueError
    try:
        compute_type2_cleanup("ini-001", "queue", "spec/untracked", "Approved")
        expect(False, "[type1] Approved spec_status should raise ValueError")
    except ValueError:
        pass  # expected

    # Type 3 guard: Implementing status → ValueError
    try:
        compute_type2_cleanup("ini-001", "queue", "spec/premature", "Implementing")
        expect(False, "[type3-status] Implementing spec_status should raise ValueError")
    except ValueError:
        pass  # expected

    # Type 3 guard: source_list='shipped' → ValueError
    try:
        compute_type2_cleanup("ini-001", "shipped", "spec/premature", "Shipped")
        expect(False, "[type3-source] source_list='shipped' should raise ValueError")
    except ValueError:
        pass  # expected


# ── F1a: research: prefix type filter ────────────────────────────────────────

def case_research_type_filter() -> None:
    """research: need is only blocked by backlog entries with type='research'.

    A shape/signal/design/strategy entry with the same slug does NOT block a
    research: need (those are different kinds of shaping work).
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Research Filter"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = []
            backlog = [{slug = "same-slug", type = "shape"}]
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [{path = "spec/needs-research", needs = "research:same-slug"}]
        """)
        ws = parse_workspace(root / "workspace.toml")
        inits = extract_initiatives(ws)
        ini = next(i for i in inits if i.slug == "ini-001")
        cls = classify_entries(ini, inits)
        entry = next(c for c in cls if c.entry.path == "spec/needs-research")

        # "same-slug" is in backlog as type="shape", not "research" → not blocking
        expect(
            entry.is_ready,
            f"[F1a] research:same-slug ready when backlog entry is type=shape, "
            f"blocking={entry.blocking_needs!r}",
        )


# ── F1b: untyped backlog entries not treated as shaping ───────────────────────

def case_untyped_backlog_not_shaping() -> None:
    """Untyped [backlog].open entries (build backlog) are NOT routed as shaping work."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Active"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active = []
            backlog = []
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = []

            [backlog]
            open = [
              {slug = "build-item",  source = "spec/x AC1"},
              {slug = "typed-shape", type   = "shape"},
            ]
        """)
        ws = parse_workspace(root / "workspace.toml")
        inits = extract_initiatives(ws)
        top_backlog = extract_top_level_backlog(ws)

        # Untyped build-backlog entry must not trigger the shaping guard
        r = check_shaping_guard("build-item", inits, top_level_backlog=top_backlog)
        expect(
            r is None,
            f"[F1b] untyped build backlog entry → None (not shaping), got {r!r}",
        )

        # Explicitly typed shape entry must still route correctly
        r2 = check_shaping_guard("typed-shape", inits, top_level_backlog=top_backlog)
        expect(
            r2 == "frame-intent",
            f"[F1b] typed shape entry → frame-intent, got {r2!r}",
        )


# ── F2: shaping DAG classification ───────────────────────────────────────────

def case_shaping_classifications() -> None:
    """Shaping entries are classified: ready, signal, blocked; routing type preserved."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Shaping"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active = [
              {slug = "active-shape",    type = "shape"},
              {slug = "active-research", type = "research"},
              {slug = "active-signal",   type = "signal"},
            ]
            backlog = [
              {slug = "backlog-no-needs",  type = "strategy"},
              {slug = "backlog-blocked",   type = "design",  needs = "work:spec/not-shipped"},
              {slug = "backlog-satisfied", type = "shape",   needs = "work:spec/already-shipped"},
            ]
            ["ini-001".work]
            active  = []
            shipped = ["spec/already-shipped"]
            queue   = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        inits = extract_initiatives(ws)
        ini = next(i for i in inits if i.slug == "ini-001")

        cls = classify_shaping_entries(ini, inits)
        by_slug = {c.entry.slug: c for c in cls}

        # shaping_queue.active: non-signals are ready, signals are active context
        expect("active-shape" in by_slug, "[shaping] active-shape classified")
        expect(by_slug["active-shape"].is_ready,
               "[shaping] active-shape is ready")
        expect(not by_slug["active-shape"].is_signal,
               "[shaping] active-shape is not signal")
        expect(by_slug["active-shape"].entry.entry_type == "shape",
               "[shaping] active-shape routing type preserved")

        expect("active-research" in by_slug, "[shaping] active-research classified")
        expect(by_slug["active-research"].is_ready,
               "[shaping] active-research is ready")
        expect(by_slug["active-research"].entry.entry_type == "research",
               "[shaping] active-research routing type preserved")

        expect("active-signal" in by_slug, "[shaping] active-signal classified")
        expect(by_slug["active-signal"].is_signal,
               "[shaping] active-signal is_signal=True")
        expect(not by_slug["active-signal"].is_ready,
               "[shaping] active-signal not ready (active context only)")

        # shaping_queue.backlog entries classified by needs
        expect("backlog-no-needs" in by_slug, "[shaping] backlog-no-needs classified")
        expect(by_slug["backlog-no-needs"].is_ready,
               "[shaping] backlog-no-needs ready (no needs)")

        expect("backlog-blocked" in by_slug, "[shaping] backlog-blocked classified")
        expect(not by_slug["backlog-blocked"].is_ready,
               "[shaping] backlog-blocked not ready (needs unsatisfied)")
        expect("work:spec/not-shipped" in by_slug["backlog-blocked"].blocking_needs,
               "[shaping] backlog-blocked has correct blocking_need")

        expect("backlog-satisfied" in by_slug, "[shaping] backlog-satisfied classified")
        expect(by_slug["backlog-satisfied"].is_ready,
               "[shaping] backlog-satisfied ready (needs satisfied)")


# ── F3: duplicate-source cleanup representability ─────────────────────────────

def case_type2_cleanup_duplicate_source() -> None:
    """When a path appears in both active AND queue, both cleanup operations are representable.

    run_reconciliation emits two Type 2 findings (one list_name='active',
    one list_name='queue'). compute_type2_cleanup's caller-provides-source API
    can describe both — the old search-based API returned only 'active'.
    """
    mut_active = compute_type2_cleanup("ini-001", "active", "spec/in-both", "Shipped")
    mut_queue = compute_type2_cleanup("ini-001", "queue", "spec/in-both", "Shipped")

    expect(mut_active["source_list"] == "active",
           "[dup] active-source mutation representable")
    expect(mut_queue["source_list"] == "queue",
           "[dup] queue-source mutation representable")
    expect(mut_active["target_list"] == "shipped",
           "[dup] active mutation target=shipped")
    expect(mut_queue["target_list"] == "shipped",
           "[dup] queue mutation target=shipped")
    expect(
        mut_active["path"] == mut_queue["path"] == "spec/in-both",
        "[dup] same path in both mutations",
    )


# ── F2: shaping duplicate deduplication ──────────────────────────────────────

def case_shaping_deduplication() -> None:
    """Active shaping entries take precedence; backlog duplicates are suppressed."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Dedup"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = [
              {slug = "same-shape", type = "shape"},
              {slug = "same-signal", type = "signal"},
            ]
            backlog = [
              {slug = "same-shape",  type = "shape"},
              {slug = "same-signal", type = "signal"},
              {slug = "same-cross",  type = "research"},
              {slug = "unique",      type = "design"},
            ]
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = []
        """)
        # Note: same-cross appears only in backlog (different slug to active entries)
        ws = parse_workspace(root / "workspace.toml")
        inits = extract_initiatives(ws)
        ini = next(i for i in inits if i.slug == "ini-001")
        cls = classify_shaping_entries(ini, inits)

        # Count occurrences of each slug
        slug_counts: dict[str, int] = {}
        for c in cls:
            slug_counts[c.entry.slug] = slug_counts.get(c.entry.slug, 0) + 1

        expect(slug_counts.get("same-shape", 0) == 1,
               f"[dedup] same-shape appears once (got {slug_counts.get('same-shape', 0)})")
        expect(slug_counts.get("same-signal", 0) == 1,
               f"[dedup] same-signal appears once (got {slug_counts.get('same-signal', 0)})")
        expect(slug_counts.get("unique", 0) == 1,
               "[dedup] unique backlog entry still visible")
        expect(slug_counts.get("same-cross", 0) == 1,
               "[dedup] same-cross (backlog-only) still visible")

        # Active classification is preserved when backlog duplicate suppressed
        by_slug = {c.entry.slug: c for c in cls}
        expect(by_slug["same-shape"].is_ready,
               "[dedup] same-shape is ready (from active, not backlog)")
        expect(not by_slug["same-shape"].is_signal,
               "[dedup] same-shape is not signal")
        expect(by_slug["same-signal"].is_signal,
               "[dedup] same-signal is signal (from active)")

        # Cross-type: active shape + backlog research with the SAME slug both survive
        write_workspace(root, """
            ["ini-002"]
            name = "CrossType"
            status = "active"
            milestone = "M1"
            ["ini-002".shaping_queue]
            active  = [{slug = "cross-dup", type = "shape"}]
            backlog = [{slug = "cross-dup", type = "research"}]
            ["ini-002".work]
            active  = []
            shipped = []
            queue   = []
        """)
        ws2 = parse_workspace(root / "workspace.toml")
        inits2 = extract_initiatives(ws2)
        ini2 = next(i for i in inits2 if i.slug == "ini-002")
        cls2 = classify_shaping_entries(ini2, inits2)
        cross_slugs = [c.entry.slug for c in cls2]
        expect(cross_slugs.count("cross-dup") == 2,
               f"[dedup] cross-type: shape+research with same slug should both appear"
               f" (got {cross_slugs.count('cross-dup')})")
        cross_types = {c.entry.entry_type for c in cls2 if c.entry.slug == "cross-dup"}
        expect(cross_types == {"shape", "research"},
               f"[dedup] cross-type: both shape and research visible (got {cross_types})")


# ── F4e: Missing initiative status not promoted to active ─────────────────────

def case_missing_status_not_active() -> None:
    """An initiative without a status field must NOT be treated as active."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "NoStatus"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = ["spec/queued-item"]
        """)
        ws = parse_workspace(root / "workspace.toml")
        inits = extract_initiatives(ws)
        ini = next(i for i in inits if i.slug == "ini-001")
        expect(ini.status != "active",
               f"[missing-status] omitted status must not default to 'active', got {ini.status!r}")
        # classify_shaping_entries processes all entries; the key check is
        # that the upstream callers (analyze) skip non-active initiatives.
        result_ini_active = [i for i in inits if i.status == "active"]
        expect(len(result_ini_active) == 0,
               f"[missing-status] no-status initiative must not appear in active set"
               f" (got {len(result_ini_active)})")


# ── F4f: Non-letter final transition segment → None ──────────────────────────

def case_nonletter_transition_segment() -> None:
    """A non-letter final transition target must return None, not backtrack."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        p = root / "docs" / "specs" / "spec-bad-trans" / "spec.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        # Non-letter final segment (year, numeric) must not backtrack to Approved
        p.write_text("# B\n\n- **Status:** Approved → 2026\n", encoding="utf-8")
        status = extract_spec_status(p)
        expect(status is None,
               f"[AC2h] non-letter final segment should yield None, got {status}")
        # Trailing arrow (simple): "Approved →" → None (no backtrack to "Approved")
        p.write_text("# B\n\n- **Status:** Approved →\n", encoding="utf-8")
        trailing_status = extract_spec_status(p)
        expect(trailing_status is None,
               f"[AC2h] trailing arrow (simple) should yield None, got {trailing_status}")
        # Trailing arrow (multi-step): "Draft → Approved →" → None (no backtrack)
        p.write_text("# B\n\n- **Status:** Draft → Approved →\n", encoding="utf-8")
        trailing_multi_status = extract_spec_status(p)
        expect(trailing_multi_status is None,
               f"[AC2h] trailing arrow (multi-step) should yield None,"
               f" got {trailing_multi_status}")


# ── F4g: _safe_spec_path dot-segment rejection ────────────────────────────────

def case_safe_spec_path_dot_segments() -> None:
    """_safe_spec_path rejects slugs with '..' or absolute paths before resolve()."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # Dot-traversal slug must be rejected even when the resolved path stays in-tree
        result_dotdot = _safe_spec_path(root, "foo/../bar")
        expect(result_dotdot is None,
               f"[confinement] 'foo/../bar' slug should be rejected, got {result_dotdot}")
        # Absolute path slug must be rejected
        result_abs = _safe_spec_path(root, "/etc/passwd")
        expect(result_abs is None,
               f"[confinement] absolute slug should be rejected, got {result_abs}")
        # Normal slug must be accepted (returns a path, not necessarily existing)
        result_ok = _safe_spec_path(root, "workspace-core")
        expect(result_ok is not None,
               f"[confinement] normal slug should not be rejected, got {result_ok}")


# ── F1: work-loop Step 0 stale-queue check ───────────────────────────────────

def case_work_loop_stale_warnings() -> None:
    """collect_work_loop_stale_warnings: characterizes work-loop Step 0 stale-queue check."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Active"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/stale-active"]
            shipped = []
            queue   = [
              "spec/stale-queue",
              "spec/archived-entry",
              {path = "spec/inline-shipped", needs = "work:spec/stale-queue"},
              "spec/approved-entry",
              "spec/no-spec",
            ]
            ["ini-001".shaping_queue]
            active = []
            backlog = []

            ["ini-002"]
            name = "Paused"
            status = "paused"
            milestone = "M1"
            ["ini-002".work]
            active  = []
            shipped = []
            queue   = ["spec/paused-stale"]
            ["ini-002".shaping_queue]
            active = []
            backlog = []
        """)
        # Write spec files
        write_spec(root, "stale-queue", "Shipped")
        write_spec(root, "stale-active", "Shipped")
        write_spec(root, "archived-entry", "Archived")
        write_spec(root, "inline-shipped", "Shipped")
        write_spec(root, "approved-entry", "Approved")
        write_spec(root, "paused-stale", "Shipped")
        # spec/no-spec deliberately has no spec.md

        ws = parse_workspace(root / "workspace.toml")
        inits = extract_initiatives(ws)
        warnings = collect_work_loop_stale_warnings(root, inits)
        warned_paths = {w.spec_path for w in warnings}

        # Shipped queue entry → warns
        expect("spec/stale-queue" in warned_paths,
               "[stale] Shipped queue entry warns")
        # Shipped active entry → warns
        expect("spec/stale-active" in warned_paths,
               "[stale] Shipped active entry warns")
        # Shipped inline-object queue entry → warns (path field used, not slug)
        expect("spec/inline-shipped" in warned_paths,
               "[stale] Shipped inline-object queue entry warns")
        # Archived → does NOT warn
        expect("spec/archived-entry" not in warned_paths,
               "[stale] Archived entry does NOT warn")
        # Approved → does NOT warn
        expect("spec/approved-entry" not in warned_paths,
               "[stale] Approved entry does NOT warn")
        # Missing spec.md → skipped without error
        expect("spec/no-spec" not in warned_paths,
               "[stale] missing spec.md → no warning")
        # Paused initiative → ignored
        expect("spec/paused-stale" not in warned_paths,
               "[stale] paused initiative ignored")
        # Exactly 3 warnings (stale-queue, stale-active, inline-shipped)
        expect(len(warnings) == 3,
               f"[stale] expected 3 warnings, got {len(warnings)}: "
               f"{[w.spec_path for w in warnings]}")


def case_work_loop_stale_both_lists() -> None:
    """Path in both queue and active → ONE warning naming both lists."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Active"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/in-both"]
            shipped = []
            queue   = ["spec/in-both"]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        write_spec(root, "in-both", "Shipped")

        ws = parse_workspace(root / "workspace.toml")
        inits = extract_initiatives(ws)
        warnings = collect_work_loop_stale_warnings(root, inits)

        expect(len(warnings) == 1,
               f"[stale-both] one warning for path in both lists, got {len(warnings)}")
        w = warnings[0]
        expect(w.spec_path == "spec/in-both", "[stale-both] correct path")
        expect(sorted(w.source_lists) == ["active", "queue"],
               f"[stale-both] both lists named: {w.source_lists!r}")


def case_work_loop_slug_normalization() -> None:
    """normalize_for_shaping_guard converts various path forms to canonical slug."""
    cases = [
        ("docs/specs/example/", "example"),
        ("docs/specs/example", "example"),
        ("spec/example", "example"),
        ("example", "example"),
        ("docs/specs/a/b", "a/b"),
    ]
    for raw, expected in cases:
        got = normalize_for_shaping_guard(raw)
        expect(got == expected,
               f"[normalize] {raw!r} → {expected!r}, got {got!r}")

    # End-to-end: normalization + shaping guard
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Active"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = [{slug = "my-feature", type = "shape"}]
            backlog = []
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        inits = extract_initiatives(ws)

        # All these raw paths should route to the same shaping entry
        for raw in ["docs/specs/my-feature/", "docs/specs/my-feature",
                    "spec/my-feature", "my-feature"]:
            slug = normalize_for_shaping_guard(raw)
            result = check_shaping_guard(slug, inits)
            expect(result == "frame-intent",
                   f"[normalize+guard] {raw!r} → slug={slug!r} → {result!r} (want 'frame-intent')")


# ── pytest wrappers for custom-runner cases ───────────────────────────────────
# Allow `pytest tools/test_workspace_status.py` to discover all cases.

def _run_case(fn) -> None:  # noqa: ANN001
    before = len(FAILURES)
    fn()
    after = len(FAILURES)
    assert after == before, "\n".join(FAILURES[before:])


def test_ac2a_multiple_active_initiatives() -> None:
    _run_case(case_multiple_active_initiatives)


def test_ac2b_paused_closed_initiatives() -> None:
    _run_case(case_paused_closed_initiatives)


def test_ac2c_ordered_queues() -> None:
    _run_case(case_ordered_queues)


def test_ac2d_local_work_deps() -> None:
    _run_case(case_local_work_deps)


def test_ac2e_cross_initiative_deps() -> None:
    _run_case(case_cross_initiative_deps)


def test_ac2f_shape_research_brief_deps() -> None:
    _run_case(case_shape_research_brief_deps)


def test_ac2g_ready_and_transitively_blocked() -> None:
    _run_case(case_ready_and_transitively_blocked)


def test_ac2h_spec_statuses() -> None:
    _run_case(case_spec_statuses)


def test_ac2i_missing_spec_paths() -> None:
    _run_case(case_missing_spec_paths)


def test_ac2j_missing_dep_targets() -> None:
    _run_case(case_missing_dep_targets)


def test_ac2k_dependency_cycles() -> None:
    _run_case(case_dependency_cycles)


def test_ac2l_type1_untracked_live_spec() -> None:
    _run_case(case_type1_untracked_live_spec)


def test_ac2m_type2_stale_entries() -> None:
    _run_case(case_type2_stale_entries)


def test_ac2n_type3_premature_shipped() -> None:
    _run_case(case_type3_premature_shipped)


def test_ac2o_multiple_active_for_workloop() -> None:
    _run_case(case_multiple_active_for_workloop)


def test_ac2p_deferred_backlog_anchors() -> None:
    _run_case(case_deferred_backlog_anchors)


def test_strategy_prefix_gap() -> None:
    _run_case(case_strategy_prefix_gap)


def test_ac3f_shaping_item_guard() -> None:
    _run_case(case_shaping_item_guard)


def test_ac3f_shaping_guard_paused_initiative() -> None:
    _run_case(case_shaping_guard_paused_initiative)


def test_ac3f_shaping_guard_top_level_backlog() -> None:
    _run_case(case_shaping_guard_top_level_backlog)


def test_ac3g_type2_cleanup_ownership() -> None:
    _run_case(case_type2_cleanup_ownership)


def test_ac2d_active_local_dep() -> None:
    _run_case(case_local_work_dep_satisfied_by_active)


def test_ac2d_dup_queue_excluded() -> None:
    _run_case(case_queue_entries_in_active_or_shipped_excluded)


def test_ac3a_dag_all_needs_prefixes() -> None:
    _run_case(case_dag_all_needs_prefixes)


def test_type2_cleanup_mutation_contract() -> None:
    _run_case(case_type2_cleanup_mutation_contract)


def test_type1_type3_no_cleanup() -> None:
    _run_case(case_type1_type3_no_cleanup)


def test_research_type_filter() -> None:
    _run_case(case_research_type_filter)


def test_untyped_backlog_not_shaping() -> None:
    _run_case(case_untyped_backlog_not_shaping)


def test_shaping_classifications() -> None:
    _run_case(case_shaping_classifications)


def test_type2_cleanup_duplicate_source() -> None:
    _run_case(case_type2_cleanup_duplicate_source)


def test_integration_full_analyze() -> None:
    _run_case(case_full_analyze)


def test_shaping_deduplication() -> None:
    _run_case(case_shaping_deduplication)


def test_work_loop_stale_warnings() -> None:
    _run_case(case_work_loop_stale_warnings)


def test_work_loop_stale_both_lists() -> None:
    _run_case(case_work_loop_stale_both_lists)


def test_work_loop_slug_normalization() -> None:
    _run_case(case_work_loop_slug_normalization)


def test_missing_status_not_active() -> None:
    _run_case(case_missing_status_not_active)


def test_nonletter_transition_segment() -> None:
    _run_case(case_nonletter_transition_segment)


def test_safe_spec_path_dot_segments() -> None:
    _run_case(case_safe_spec_path_dot_segments)


# ── Runner ────────────────────────────────────────────────────────────────────

CASES = [
    ("AC2a multiple_active_initiatives", case_multiple_active_initiatives),
    ("AC2b paused_closed_initiatives", case_paused_closed_initiatives),
    ("AC2c ordered_queues", case_ordered_queues),
    ("AC2d local_work_deps", case_local_work_deps),
    ("AC2d-active work_dep_on_active_stays_blocked", case_local_work_dep_satisfied_by_active),
    ("AC2d-dup queue_entries_in_active_or_shipped_excluded",
     case_queue_entries_in_active_or_shipped_excluded),
    ("AC2e cross_initiative_deps", case_cross_initiative_deps),
    ("AC2f shape_research_brief_deps", case_shape_research_brief_deps),
    ("AC2g ready_and_transitively_blocked", case_ready_and_transitively_blocked),
    ("AC2h spec_statuses", case_spec_statuses),
    ("AC2i missing_spec_paths", case_missing_spec_paths),
    ("AC2j missing_dep_targets", case_missing_dep_targets),
    ("AC2k dependency_cycles", case_dependency_cycles),
    ("AC2l type1_untracked_live_spec", case_type1_untracked_live_spec),
    ("AC2m type2_stale_entries", case_type2_stale_entries),
    ("AC2n type3_premature_shipped", case_type3_premature_shipped),
    ("AC2o multiple_active_for_workloop", case_multiple_active_for_workloop),
    ("AC2p deferred_backlog_anchors", case_deferred_backlog_anchors),
    ("KD-08 strategy_prefix_gap", case_strategy_prefix_gap),
    ("AC3f shaping_item_guard", case_shaping_item_guard),
    ("AC3f shaping_guard_paused_initiative", case_shaping_guard_paused_initiative),
    ("AC3f shaping_guard_top_level_backlog", case_shaping_guard_top_level_backlog),
    ("AC3g type2_cleanup_ownership", case_type2_cleanup_ownership),
    ("AC3a dag_all_needs_prefixes", case_dag_all_needs_prefixes),
    ("type2_cleanup_mutation_contract", case_type2_cleanup_mutation_contract),
    ("type1_type3_no_cleanup", case_type1_type3_no_cleanup),
    ("F1a research_type_filter", case_research_type_filter),
    ("F1b untyped_backlog_not_shaping", case_untyped_backlog_not_shaping),
    ("F2 shaping_classifications", case_shaping_classifications),
    ("F3 type2_cleanup_duplicate_source", case_type2_cleanup_duplicate_source),
    ("skill_contract_anchor", case_skill_contract_anchor),
    ("work_loop_contract_anchor", case_work_loop_contract_anchor),
    ("integration full_analyze", case_full_analyze),
    ("F4a shaping_deduplication", case_shaping_deduplication),
    ("F4b work_loop_stale_warnings", case_work_loop_stale_warnings),
    ("F4c work_loop_stale_both_lists", case_work_loop_stale_both_lists),
    ("F4d work_loop_slug_normalization", case_work_loop_slug_normalization),
    ("F4e missing_status_not_active", case_missing_status_not_active),
    ("F4f nonletter_transition_segment", case_nonletter_transition_segment),
    ("F4g safe_spec_path_dot_segments", case_safe_spec_path_dot_segments),
]


def main() -> int:
    passed = 0
    failed = 0
    skipped = 0
    for label, fn in CASES:
        before = len(FAILURES)
        try:
            fn()
        except unittest.SkipTest as exc:
            print(f"  ⊘  {label}: {exc}")
            skipped += 1
            continue
        except Exception as exc:
            FAILURES.append(f"{label}: exception: {exc}")
        after = len(FAILURES)
        if after == before:
            print(f"  ✓  {label}")
            passed += 1
        else:
            for msg in FAILURES[before:]:
                print(f"  ✖  {msg}")
            failed += 1

    summary = f"{passed} passed, {failed} failed"
    if skipped:
        summary += f", {skipped} skipped"
    print(f"\n{summary}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
