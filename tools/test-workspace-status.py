#!/usr/bin/env python3
"""Characterization tests for workspace-status algorithmic behavior.

Tests the workspace_status_engine module (Order 0 test seam) against
deterministic fixtures built in tempdir. Each fixture models a scenario
from the spec AC2 list.

Run:  python3 tools/test-workspace-status.py
Exit: 0 if all pass, 1 if any fail.

Known-defect tests are marked with [KNOWN-DEFECT: KD-NN] and describe
intentional existing behavior — not desired future behavior.
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
from pathlib import Path

# Prefer repo-local copy of the engine.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_status_engine import (
    analyze,
    check_shaping_guard,
    classify_entries,
    compute_done_step_mutation,
    extract_initiatives,
    extract_spec_status,
    get_active_specs,
    is_need_satisfied,
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
    p.write_text(f"# Spec: {slug}\n\n- **Status:** {status}\n\n## Acceptance Criteria\n\n- [ ] AC1\n", encoding="utf-8")


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
            name = "Closed"
            status = "complete"
            milestone = "M1"
            ["ini-003".work]
            active  = []
            shipped = ["spec/closed-feature"]
            queue   = []
            ["ini-003".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        expect(len(initiatives) == 3, f"[AC2b] expected 3 initiatives, got {len(initiatives)}")
        by_status = {i.slug: i.status for i in initiatives}
        expect(by_status.get("ini-001") == "active", f"[AC2b] ini-001 status wrong")
        expect(by_status.get("ini-002") == "paused", f"[AC2b] ini-002 status wrong")
        expect(by_status.get("ini-003") == "complete", f"[AC2b] ini-003 status wrong")
        # Paused/closed don't contribute to ready/blocked
        all_cls: list = []
        for ini in initiatives:
            if ini.status == "active":
                all_cls.extend(classify_entries(ini, initiatives))
        paths = {c.entry.path for c in all_cls}
        expect("spec/active-feature" in paths, "[AC2b] active feature should be classified")
        expect("spec/paused-feature" not in paths, "[AC2b] paused feature should not be classified")


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

        expect(by_path["spec/needs-active-shape"].is_ready,
               "[AC2f] shape:active-shape satisfied (in active)")
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
            extracted = extract_spec_status(root / "docs" / "specs" / f"spec-{status.lower()}" / "spec.md")
            expect(extracted == status, f"[AC2h] expected {status}, got {extracted}")

        transition_status = extract_spec_status(root / "docs" / "specs" / "spec-transition" / "spec.md")
        expect(transition_status == "Shipped",
               f"[AC2h] transition form should yield 'Shipped', got {transition_status}")

        # Multi-arrow form: last target wins (greedy regex)
        p_multi = root / "docs" / "specs" / "spec-multi-arrow" / "spec.md"
        p_multi.parent.mkdir(parents=True, exist_ok=True)
        p_multi.write_text("# M\n\n- **Status:** Draft → Approved → Shipped\n", encoding="utf-8")
        multi_status = extract_spec_status(p_multi)
        expect(multi_status == "Shipped",
               f"[AC2h] multi-arrow form last segment should be 'Shipped', got {multi_status}")


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
        expect(len(findings) == 0,
               f"[AC2i] missing spec files should be silently skipped, got {len(findings)} findings")


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
        expect(len(active_specs) == 0, f"[AC2o] branch-0: expected 0 active, got {len(active_specs)}")

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
        expect(len(active_specs) == 1, f"[AC2o] branch-1: expected 1 active, got {len(active_specs)}")
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
        expect(len(active_specs) == 2, f"[AC2o] branch-2+: expected 2 active, got {len(active_specs)}")

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
        expect(len(active_specs) == 2, f"[AC2o] cross-ini: expected 2 active, got {len(active_specs)}")


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


# ── AC3g: workspace-status Type 2 cleanup mutation shape ────────────────────────
# NOTE: work-loop (≥ a46d6f46) no longer writes active/shipped to workspace.toml.
# Its finish checklist only sets spec.md Status: Shipped. Cleanup of stale
# active/queue entries is workspace-status's Type 2 cleanup write.

def case_done_step_mutation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Cleanup"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/stale-active"]
            shipped = []
            queue   = ["spec/stale-queued"]
            ["ini-001".shaping_queue]
            active = []
            backlog = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)

        # Stale active entry: workspace-status cleanup moves active → shipped
        mut = compute_done_step_mutation("spec/stale-active", initiatives)
        expect(mut is not None, "[AC3g] stale active spec should have a cleanup mutation")
        expect(mut["source_list"] == "active", f"[AC3g] source should be active: {mut}")
        expect(mut["target_list"] == "shipped", f"[AC3g] target should be shipped: {mut}")
        expect(mut["written_form"] == '"spec/stale-active"',
               f"[AC3g] written form should be bare string: {mut}")

        # Stale queue entry: workspace-status cleanup moves queue → shipped
        mut2 = compute_done_step_mutation("spec/stale-queued", initiatives)
        expect(mut2 is not None, "[AC3g] stale queued spec should have a cleanup mutation")
        expect(mut2["source_list"] == "queue", f"[AC3g] source should be queue: {mut2}")
        expect(mut2["target_list"] == "shipped", f"[AC3g] target should be shipped: {mut2}")

        # Not present → no mutation
        mut3 = compute_done_step_mutation("spec/not-tracked", initiatives)
        expect(mut3 is None, "[AC3g] untracked spec should return no mutation")


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
            active  = [{slug = "active-shape", type = "shape"}]
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
              {path = "spec/p-shape",    needs = "shape:active-shape"},
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

        expect(by_path["spec/p-work"].is_ready,     "[AC3a] work: prefix satisfied")
        expect(by_path["spec/p-shape"].is_ready,    "[AC3a] shape: prefix satisfied")
        expect(by_path["spec/p-research"].is_ready, "[AC3a] research: prefix (not in backlog)")
        expect(by_path["spec/p-brief"].is_ready,    "[AC3a] brief: prefix satisfied")
        expect(by_path["spec/p-cross"].is_ready,    "[AC3a] cross-ini prefix satisfied")

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

        expect(not by_path2["spec/p-work-bad"].is_ready,     "[AC3a] work: prefix unsatisfied")
        expect(not by_path2["spec/p-research-bad"].is_ready, "[AC3a] research: in backlog → blocked")
        expect(not by_path2["spec/p-brief-bad"].is_ready,    "[AC3a] brief: not in ready → blocked")
        expect(not by_path2["spec/p-cross-bad"].is_ready,    "[AC3a] unknown ini → blocked")
        expect(not by_path2["spec/p-backlog-bad"].is_ready,  "[AC3a][KD-01] backlog: prefix blocked")


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
        write_spec(root, "ready-queued", "Approved")     # Type 2: still in queue but Shipped would be wrong; Approved is fine
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


# ── Runner ────────────────────────────────────────────────────────────────────

CASES = [
    ("AC2a multiple_active_initiatives",     case_multiple_active_initiatives),
    ("AC2b paused_closed_initiatives",       case_paused_closed_initiatives),
    ("AC2c ordered_queues",                  case_ordered_queues),
    ("AC2d local_work_deps",                 case_local_work_deps),
    ("AC2e cross_initiative_deps",           case_cross_initiative_deps),
    ("AC2f shape_research_brief_deps",       case_shape_research_brief_deps),
    ("AC2g ready_and_transitively_blocked",  case_ready_and_transitively_blocked),
    ("AC2h spec_statuses",                   case_spec_statuses),
    ("AC2i missing_spec_paths",              case_missing_spec_paths),
    ("AC2j missing_dep_targets",             case_missing_dep_targets),
    ("AC2k dependency_cycles",               case_dependency_cycles),
    ("AC2l type1_untracked_live_spec",       case_type1_untracked_live_spec),
    ("AC2m type2_stale_entries",             case_type2_stale_entries),
    ("AC2n type3_premature_shipped",         case_type3_premature_shipped),
    ("AC2o multiple_active_for_workloop",    case_multiple_active_for_workloop),
    ("AC2p deferred_backlog_anchors",        case_deferred_backlog_anchors),
    ("AC3f shaping_item_guard",              case_shaping_item_guard),
    ("AC3g done_step_mutation",              case_done_step_mutation),
    ("AC3a dag_all_needs_prefixes",          case_dag_all_needs_prefixes),
    ("integration full_analyze",             case_full_analyze),
]


def main() -> int:
    passed = 0
    failed = 0
    for label, fn in CASES:
        before = len(FAILURES)
        try:
            fn()
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

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
