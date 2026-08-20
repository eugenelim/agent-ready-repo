#!/usr/bin/env python3
"""Characterization tests for workspace-status algorithmic behavior.

Tests workspace_status_engine against deterministic fixtures.

Imports the production engine from its canonical location:
  packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py

Run:  python3 tools/test_workspace_status.py
      python3 -m pytest tools/test_workspace_status.py -q
Exit: 0 if all pass, 1 if any fail.

Known-defect tests are marked with [KNOWN-DEFECT: KD-NN] and describe
intentional existing behavior — not desired future behavior.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

# Load the production engine from its skill-local location.
_ENGINE_PATH = (
    Path(__file__).resolve().parent.parent
    / "packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py"
)
_engine_spec = importlib.util.spec_from_file_location("workspace_status_engine", _ENGINE_PATH)
_engine_mod = importlib.util.module_from_spec(_engine_spec)  # type: ignore[arg-type]
sys.modules.setdefault("workspace_status_engine", _engine_mod)
_engine_spec.loader.exec_module(_engine_mod)  # type: ignore[union-attr]

_safe_spec_path = _engine_mod._safe_spec_path
analyze = _engine_mod.analyze
analyze_bounded = _engine_mod.analyze_bounded
explain_item = _engine_mod.explain_item
check_shaping_guard = _engine_mod.check_shaping_guard
classify_entries = _engine_mod.classify_entries
classify_shaping_entries = _engine_mod.classify_shaping_entries
collect_work_loop_stale_warnings = _engine_mod.collect_work_loop_stale_warnings
compute_type2_cleanup = _engine_mod.compute_type2_cleanup
extract_initiatives = _engine_mod.extract_initiatives
extract_spec_status = _engine_mod.extract_spec_status
extract_spec_status_with_fingerprint = _engine_mod.extract_spec_status_with_fingerprint
extract_repo_backlog = _engine_mod.extract_repo_backlog
extract_top_level_backlog = _engine_mod.extract_top_level_backlog
get_active_specs = _engine_mod.get_active_specs
normalize_for_shaping_guard = _engine_mod.normalize_for_shaping_guard
parse_workspace = _engine_mod.parse_workspace
run_reconciliation = _engine_mod.run_reconciliation
compute_repair_plan = _engine_mod.compute_repair_plan
canonical_result_identity = _engine_mod.canonical_result_identity
canonical_result_snapshot = _engine_mod.canonical_result_snapshot
run_canonical_reconciliation = _engine_mod.run_canonical_reconciliation
RepairOperation = _engine_mod.RepairOperation
ManualFinding = _engine_mod.ManualFinding
RepairPlan = _engine_mod.RepairPlan

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

def case_local_work_dep_blocked_by_active() -> None:
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
            active  = [
              {slug = "active-shape",    type = "shape"},
              {slug = "active-research", type = "research"},
            ]
            backlog = [
              {slug = "backlog-research", type = "research"},
              {slug = "backlog-shape",    type = "shape"},
            ]
            ["ini-001".work]
            active  = []
            shipped = []
            queue   = [
              {path = "spec/needs-active-shape",    needs = "shape:active-shape"},
              {path = "spec/needs-absent-shape",    needs = "shape:never-existed"},
              {path = "spec/needs-backlog-shape",   needs = "shape:backlog-shape"},
              {path = "spec/needs-active-research", needs = "research:active-research"},
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
        expect(by_path["spec/needs-backlog-shape"].is_ready,
               "[AC2f] shape:backlog-shape satisfied (in backlog but not active)")
        expect(by_path["spec/needs-active-research"].is_ready,
               "[AC2f][KD-09] research:active-research — in active (not backlog) "
               "erroneously satisfies dep; RFC-0064 requires findings committed first")
        expect(by_path["spec/needs-research-done"].is_ready,
               "[AC2f] research:finished-research satisfied (not in backlog)")
        expect(not by_path["spec/needs-research-pending"].is_ready,
               "[AC2f] research:backlog-research blocked (in backlog)")


# ── AC2f-list: List-valued needs (logical AND) ────────────────────────────────

def case_list_valued_needs() -> None:
    """needs = [...] satisfies all entries; one unsatisfied dep blocks the whole entry."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "List Needs"
            status = "active"
            milestone = "M1"
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
            ["ini-001".work]
            active  = []
            shipped = ["spec/dep-a"]
            queue   = [
              {path = "spec/partial",   needs = ["work:spec/dep-a", "work:spec/dep-missing"]},
              {path = "spec/satisfied", needs = ["work:spec/dep-a",
                                                 "brief:docs/product/briefs/ready.md"]},
            ]
            ["ini-001".brief_queue]
            executing = ""
            ready     = ["docs/product/briefs/ready.md"]
            draft     = []
        """)
        ws = parse_workspace(root / "workspace.toml")
        initiatives = extract_initiatives(ws)
        cls = classify_entries(initiatives[0], initiatives)
        by_path = {c.entry.path: c for c in cls}

        expect(not by_path["spec/partial"].is_ready,
               "[AC2f-list] one unsatisfied dep → entry blocked")
        expect("work:spec/dep-missing" in by_path["spec/partial"].blocking_needs,
               "[AC2f-list] unsatisfied dep named in blocking_needs")
        expect(by_path["spec/satisfied"].is_ready,
               "[AC2f-list] mixed-prefix list with all deps satisfied → ready")


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


def case_spec_status_parser_boundaries() -> None:
    """Parser skips status fields inside code fences, HTML comments, and section bodies."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def write_raw(slug: str, body: str) -> Path:
            p = root / "docs" / "specs" / slug / "spec.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
            return p

        # Code-fence skip (backtick fence)
        p = write_raw("fence-backtick", "# S\n\n```\n- **Status:** Shipped\n```\n")
        got = extract_spec_status(p)
        expect(
            got is None,
            f"[parser-boundary] status inside ``` fence must yield None, got {got!r}",
        )

        # Code-fence skip (tilde fence)
        p = write_raw("fence-tilde", "# S\n\n~~~\n- **Status:** Shipped\n~~~\n")
        got = extract_spec_status(p)
        expect(
            got is None,
            f"[parser-boundary] status inside ~~~ fence must yield None, got {got!r}",
        )

        # Section-heading stop — status after first ## heading is body text, not a field
        p = write_raw("after-heading", "# S\n\n## Design\n\n- **Status:** Shipped\n")
        got = extract_spec_status(p)
        expect(got is None,
               f"[parser-boundary] status after ## heading must yield None, got {got!r}")

        # Multi-line HTML comment suppresses the status field
        p = write_raw(
            "ml-comment",
            "# S\n\n<!--\n- **Status:** Shipped\n-->\n",
        )
        got = extract_spec_status(p)
        expect(got is None,
               f"[parser-boundary] status inside multi-line comment must yield None, got {got!r}")

        # Close + open on same line: --> <!-- note --> must not leave in_ml_comment=True,
        # so the NEXT line IS scanned and the real status is found.
        p = write_raw(
            "ml-comment-close-open",
            "# S\n\n<!--\n- **Status:** Draft\n--> <!-- note -->\n- **Status:** Shipped\n",
        )
        got = extract_spec_status(p)
        expect(got == "Shipped",
               f"[parser-boundary] close+open on same line should not re-enter comment; "
               f"expected 'Shipped', got {got!r}")


def case_spec_status_sister_function_parity() -> None:
    """extract_spec_status and extract_spec_status_with_fingerprint agree on status."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        def write_raw(slug: str, body: str) -> Path:
            p = root / "docs" / "specs" / slug / "spec.md"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
            return p

        cases = [
            ("normal-shipped", "# S\n\n- **Status:** Shipped\n"),
            ("inside-fence", "# S\n\n```\n- **Status:** Shipped\n```\n"),
            ("inside-ml-comment", "# S\n\n<!--\n- **Status:** Shipped\n-->\n"),
            ("after-heading", "# S\n\n## Body\n\n- **Status:** Shipped\n"),
        ]
        for slug, body in cases:
            p = write_raw(slug, body)
            simple = extract_spec_status(p)
            with_fp, _ = extract_spec_status_with_fingerprint(p)
            expect(
                simple == with_fp,
                f"[sister-parity] {slug}: extract_spec_status={simple!r} "
                f"but extract_spec_status_with_fingerprint returned {with_fp!r}",
            )


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
        # Nested spec under a grouping directory — must also be discovered
        write_spec(root, "group/nested-approved", "Approved")

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
        expect("spec/group/nested-approved" in type1_paths,
               "[AC2l] nested spec (group/nested-approved) should be Type 1")


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


def case_extract_repo_backlog_preserves_declared_display_data() -> None:
    workspace = {
        "backlog": {
            "open": [
                {
                    "slug": "build-item",
                    "needs": "backlog:prerequisite",
                    "source": "spec/example",
                    "summary": "Build item",
                },
                {
                    "slug": "shape-item",
                    "type": "research",
                    "needs": ["backlog:build-item"],
                    "source": {"mode": "repo-origin"},
                    "summary": "Shape item",
                },
                {
                    "path": "docs/product/intents/example.md",
                    "kind": "intent",
                    "source": {"mode": "repo-origin"},
                    "summary": "Target item",
                    "needs": [{
                        "type": "local",
                        "kind": "research",
                        "path": "docs/product/research/example.md",
                    }],
                },
                {"slug": "minimal-build"},
            ],
        },
    }

    entries = extract_repo_backlog(workspace)
    expect([entry.slug or entry.path for entry in entries] == [
        "build-item", "shape-item", "docs/product/intents/example.md",
        "minimal-build",
    ], "repo backlog preserves source order")
    expect(entries[0].room == "build", "untyped legacy backlog entry is build")
    expect(entries[0].needs == ["backlog:prerequisite"],
           "legacy scalar need is normalized without losing the dependency")
    expect(entries[1].room == "shape" and entries[1].entry_type == "research",
           "typed legacy backlog entry preserves shaping room and subtype")
    expect(entries[1].source == {"mode": "repo-origin"},
           "legacy structured source is preserved")
    expect(entries[2].room == "shape" and entries[2].kind == "intent",
           "target upstream kind maps to shape without losing kind")
    expect(entries[2].needs == workspace["backlog"]["open"][2]["needs"],
           "target structured dependencies are preserved")
    expect(entries[3].room == "build" and entries[3].needs == [],
           "legacy entry without optional fields remains visible")
    expect(entries[3].source is None and entries[3].summary is None,
           "missing optional display metadata is not fabricated")
    expect(extract_repo_backlog({}) == [], "absent repo backlog is empty")
    expect(extract_repo_backlog({"backlog": {"open": []}}) == [],
           "empty repo backlog is empty")


# ── AC3g: workspace-status Type 2 cleanup ownership ───────────────────────────
# NOTE: work-loop (≥ a46d6f46) no longer writes active/shipped to workspace.toml.
# Its finish checklist only sets spec.md Status: Shipped. Cleanup of stale
# active/queue entries is workspace-status's repair-plan/repair-apply write.

def case_type2_cleanup_ownership() -> None:
    """AC3g: workspace-status owns Type 2 cleanup; work-loop does not mutate queue/active/shipped.

    work-loop (≥ a46d6f46) only sets spec.md Status: Shipped at completion.
    Stale queue/active entries are workspace-status's responsibility (Type 2).
    compute_type2_cleanup is display-only; repair-plan/repair-apply owns writes.

    Caller provides exact (ini_slug, source_list) from the ReconciliationFinding;
    the function does not search and never emits mutation instructions.
    """
    descriptors = [
        compute_type2_cleanup("ini-001", "active", "spec/stale-active", "Shipped"),
        compute_type2_cleanup("ini-001", "queue", "spec/stale-queued", "Shipped"),
        compute_type2_cleanup(
            "ini-001", "active", "spec/stale-active-archived", "Archived"
        ),
        compute_type2_cleanup(
            "ini-001", "queue", "spec/stale-queued-archived", "Archived"
        ),
    ]
    for descriptor in descriptors:
        expect(descriptor["authoritative"] is False, f"[AC3g] display only: {descriptor}")
        expect(descriptor["next_action"] == "repair-plan", f"[AC3g] repair route: {descriptor}")
        expect("target_list" not in descriptor, f"[AC3g] no write target: {descriptor}")
        expect("written_form" not in descriptor, f"[AC3g] no bare write: {descriptor}")


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
        expect(by_path["spec/p-shape"].is_ready, "[AC3a] shape: satisfied (absent = graduated)")
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
# Uses section-heading markers instead of absolute line numbers so edits to
# frontmatter or intro paragraphs before the anchored blocks do not shift the
# hashed window and trigger false build-check failures.
#
# workspace-status: §1 Read workspace.toml through §5 Missing fields (the full
# algorithmic contract: schema vocabulary, DAG resolution, reconciliation,
# signal output, skill routing, missing-field defaults).
# work-loop: Step 0 ORIENT (active-spec resolution, stale-queue check, shaping
# guard) and Finish checklist (owns only spec.md Status: Shipped write).
#
# When a test fails, the SKILL.md section changed. Read the changed content
# and reconcile workspace_status_engine.py before updating the hash constant.
_SKIP_ANCHOR_ENV = "WORKSPACE_STATUS_SKIP_ANCHOR"

# Section-heading markers for the work-loop contract anchors (regex patterns).
_WL_STEP0_START = r'^## Step 0\. ORIENT'
_WL_STEP0_END = r'^## Step 1\. PLAN'
_WL_FINISH_START = r'^## Finish checklist'
_WL_FINISH_END = r'Conventional commit format'

_WORK_LOOP_CONTRACT_HASH = (
    "38593877057bc728a185fd15a9b04de733abe9f9e2ace6665184f234faf62518"
)
_WORK_LOOP_FINISH_HASH = (
    "830b64d157a2cda09b031d7db424689e2ec701664b7aa4c56e7f1d21f68ba438"
)
_WORK_LOOP_MD = (
    Path(__file__).resolve().parent.parent
    / "packs/core/.apm/skills/work-loop/SKILL.md"
)


def _check_section_anchor(
    skill_path: Path,
    start_marker: str,
    end_marker: str,
    expected_hash: str,
    label: str,
) -> None:
    """Hash content between section markers; fail if the hash differs.

    Finds the first line matching start_marker, then extracts up to (not
    including) the next line matching end_marker. Layout-stable: edits before
    or after the anchored section don't shift the window.

    Fails hard when the skill file is absent in the canonical repo.
    Set WORKSPACE_STATUS_SKIP_ANCHOR=1 to raise unittest.SkipTest.
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
    raw = skill_path.read_bytes().split(b'\n')
    start_idx = next(
        (i for i, ln in enumerate(raw) if re.search(start_marker.encode(), ln)),
        None,
    )
    if start_idx is None:
        expect(False,
               f"[{label}] start marker {start_marker!r} not found in "
               f"{skill_path.name}")
        return
    end_idx = next(
        (i for i, ln in enumerate(raw)
         if i > start_idx and re.search(end_marker.encode(), ln)),
        len(raw),
    )
    contract = b'\n'.join(raw[start_idx:end_idx])
    actual = hashlib.sha256(contract).hexdigest()
    expect(
        actual == expected_hash,
        f"[{label}] skill contract changed "
        f"(expected {expected_hash[:12]}…, got {actual[:12]}…). "
        "Review the changed sections and update workspace_status_engine.py "
        f"before updating the hash constant.",
    )


def case_work_loop_contract_anchor() -> None:
    """Fail when the Step 0 or finish-checklist contract of work-loop SKILL.md changes.

    Two section anchors:
    - '## Step 0. ORIENT' → '## Step 1. PLAN': active-spec resolution,
      stale-queue check (warn-only; does NOT update workspace.toml), and
      shaping-item guard.
    - '## Finish checklist' → 'Conventional commit format': the ownership-relevant
      checklist items including the doc-drift invariant (sets spec.md Status: Shipped)
      but excluding commit format, learnings, and PR-opening guidance — which are
      routine maintenance that should not fail build-check. workspace-status (not
      work-loop) owns workspace.toml queue/active/shipped updates (AC3g invariant).
    """
    _check_section_anchor(
        _WORK_LOOP_MD,
        _WL_STEP0_START, _WL_STEP0_END,
        _WORK_LOOP_CONTRACT_HASH, "work-loop Step-0 contract",
    )
    _check_section_anchor(
        _WORK_LOOP_MD,
        _WL_FINISH_START, _WL_FINISH_END,
        _WORK_LOOP_FINISH_HASH, "work-loop finish-checklist contract",
    )


def test_work_loop_contract_anchor() -> None:
    """pytest entry point for the work-loop Step 0 contract anchor."""
    before = len(FAILURES)
    case_work_loop_contract_anchor()
    after = len(FAILURES)
    assert after == before, "\n".join(FAILURES[before:])


# ── Type 2 cleanup compatibility projection ──────────────────────────────────
#
# The legacy status field remains descriptive only. It must route every eligible
# Type 2 finding to repair-plan without exposing a mutation target or serialized
# bare-string form. Repair-plan/repair-apply owns all actual writes.

def case_type2_cleanup_mutation_contract() -> None:
    descriptors = [
        compute_type2_cleanup(
            "ini-001", "active", "spec/stale-active-shipped", "Shipped"
        ),
        compute_type2_cleanup(
            "ini-001", "queue", "spec/stale-queue-shipped", "Shipped"
        ),
        compute_type2_cleanup(
            "ini-001", "active", "spec/stale-active-archived", "Archived"
        ),
    ]
    for descriptor in descriptors:
        expect(descriptor["authoritative"] is False, "[cleanup] descriptor is display-only")
        expect(descriptor["next_action"] == "repair-plan", "[cleanup] routes to repair-plan")
        expect("target_list" not in descriptor, "[cleanup] no mutation target")
        expect("written_form" not in descriptor, "[cleanup] no bare-string write")


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
    """Duplicate findings remain visible without authorizing either write.

    run_reconciliation emits two Type 2 findings (one list_name='active',
    one list_name='queue'). compute_type2_cleanup's caller-provides-source API
    can describe both, while repair-plan keeps duplicate membership manual.
    """
    mut_active = compute_type2_cleanup("ini-001", "active", "spec/in-both", "Shipped")
    mut_queue = compute_type2_cleanup("ini-001", "queue", "spec/in-both", "Shipped")

    expect(mut_active["source_list"] == "active",
           "[dup] active-source mutation representable")
    expect(mut_queue["source_list"] == "queue",
           "[dup] queue-source mutation representable")
    expect(mut_active["authoritative"] is False,
           "[dup] active descriptor is display-only")
    expect(mut_queue["authoritative"] is False,
           "[dup] queue descriptor is display-only")
    expect("target_list" not in mut_active and "target_list" not in mut_queue,
           "[dup] descriptors do not authorize writes")
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
        # Compact multi-hop (no spaces): "Draft→Approved→Shipped" → "Shipped"
        p.write_text("# B\n\n- **Status:** Draft→Approved→Shipped\n", encoding="utf-8")
        compact_status = extract_spec_status(p)
        expect(compact_status == "Shipped",
               f"[F4f] compact multi-hop should yield Shipped, got {compact_status}")


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


# ── Order 1B: analyze_bounded + explain_item ─────────────────────────────────

def case_analyze_bounded_skips_type1() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Alpha"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/alpha-active"]
            shipped = []
            queue   = ["spec/alpha-queue"]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        write_spec(root, "alpha-active", "Implementing")
        write_spec(root, "alpha-queue", "Approved")
        write_spec(root, "untracked-live", "Implementing")  # M=1 untracked live spec

        result = analyze_bounded(root)
        expect(result.type1 == [], f"[bounded-type1] expected type1==[], got {result.type1}")
        expect(not result.global_scan_performed,
               "[bounded-type1] global_scan_performed should be False")
        expect(result.global_scan_files_read == 0,
               f"[bounded-type1] global_scan_files_read={result.global_scan_files_read}")


def case_analyze_bounded_file_counts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Alpha"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/alpha-active"]
            shipped = ["spec/alpha-shipped"]
            queue   = ["spec/alpha-queue"]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        write_spec(root, "alpha-active", "Implementing")
        # alpha-shipped: no spec.md — confinement returns None → not read
        write_spec(root, "alpha-queue", "Approved")
        write_spec(root, "untracked-1", "Implementing")
        write_spec(root, "untracked-2", "Approved")

        result = analyze_bounded(root)
        N = 3  # active + shipped + queue entries declared
        expect(result.declared_spec_files_read <= N,
               f"[bounded-counts] declared={result.declared_spec_files_read} > N={N}")
        expect(result.global_scan_files_read == 0,
               f"[bounded-counts] global_scan_files_read={result.global_scan_files_read}")
        expect(result.files_read == result.declared_spec_files_read,
               f"[bounded-counts] files_read={result.files_read} "
               f"!= declared={result.declared_spec_files_read}")


def case_analyze_full_file_counts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Alpha"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/alpha-active"]
            shipped = []
            queue   = ["spec/alpha-queue"]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        write_spec(root, "alpha-active", "Implementing")
        write_spec(root, "alpha-queue", "Approved")
        write_spec(root, "untracked-live-1", "Implementing")
        write_spec(root, "untracked-live-2", "Approved")

        result = analyze(root)
        M = 2  # untracked live specs
        expect(result.global_scan_performed, "[full-counts] global_scan_performed should be True")
        expect(result.global_scan_files_read >= M,
               f"[full-counts] global_scan_files_read={result.global_scan_files_read} < M={M}")
        expect(
            result.files_read == result.declared_spec_files_read + result.global_scan_files_read,
            f"[full-counts] files_read={result.files_read} != declared+global",
        )


def case_explain_item_ready() -> None:
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
            queue   = ["spec/alpha-ready"]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "spec/alpha-ready")
        expect(out.get("selector_status") == "matched",
               f"[explain-ready] selector_status={out.get('selector_status')!r}")
        item = out.get("explained_item", {})
        expect(item.get("classification") == "ready",
               f"[explain-ready] classification={item.get('classification')!r}")
        expect(item.get("blocking_needs") == [],
               f"[explain-ready] blocking_needs={item.get('blocking_needs')!r}")
        expect(item.get("list") == "queue",
               f"[explain-ready] list={item.get('list')!r}")


def case_explain_item_blocked() -> None:
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
            queue   = [
                "spec/alpha-dep",
                {path = "spec/alpha-blocked", needs = ["work:spec/alpha-dep"]},
            ]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "spec/alpha-blocked")
        expect(out.get("selector_status") == "matched",
               f"[explain-blocked] selector_status={out.get('selector_status')!r}")
        item = out.get("explained_item", {})
        expect(item.get("classification") == "blocked",
               f"[explain-blocked] classification={item.get('classification')!r}")
        expect("work:spec/alpha-dep" in item.get("blocking_needs", []),
               f"[explain-blocked] blocking_needs={item.get('blocking_needs')!r}")
        deps = item.get("dependencies", [])
        expect(
            len(deps) == 1
            and deps[0]["need"] == "work:spec/alpha-dep"
            and not deps[0]["satisfied"],
            f"[explain-blocked] deps={deps!r}",
        )


def case_explain_item_active() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Alpha"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/alpha-active"]
            shipped = []
            queue   = []
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "alpha-active")  # slug form — tests normalization
        expect(out.get("selector_status") == "matched",
               f"[explain-active] selector_status={out.get('selector_status')!r}")
        item = out.get("explained_item", {})
        expect(item.get("list") == "active",
               f"[explain-active] list={item.get('list')!r}")
        expect(item.get("classification") == "active",
               f"[explain-active] classification={item.get('classification')!r}")


def case_explain_item_active_downstream() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Alpha"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/item-b"]
            shipped = []
            queue   = [
                {path = "spec/item-a", needs = ["work:spec/item-b"]},
            ]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "spec/item-b")
        expect(out.get("selector_status") == "matched",
               f"[explain-active-downstream] selector_status={out.get('selector_status')!r}")
        item = out.get("explained_item", {})
        downstream = item.get("downstream_unblocked", [])
        expect("spec/item-a" in downstream,
               f"[explain-active-downstream] downstream_unblocked={downstream!r} (want item-a)")


def case_explain_item_shipped() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Alpha"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = []
            shipped = ["spec/alpha-shipped"]
            queue   = []
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "spec/alpha-shipped")
        expect(out.get("selector_status") == "matched",
               f"[explain-shipped] selector_status={out.get('selector_status')!r}")
        item = out.get("explained_item", {})
        expect(item.get("list") == "shipped",
               f"[explain-shipped] list={item.get('list')!r}")
        expect(item.get("classification") == "shipped",
               f"[explain-shipped] classification={item.get('classification')!r}")


def case_explain_item_not_found() -> None:
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
            queue   = ["spec/alpha-only"]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "spec/unknown-slug")
        expect(out.get("selector_status") == "not_found",
               f"[explain-not-found] selector_status={out.get('selector_status')!r}")


def case_explain_item_ambiguous_cross_initiative() -> None:
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
            queue   = ["spec/shared-slug"]
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
            queue   = ["spec/shared-slug"]
            ["ini-002".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "shared-slug")
        expect(out.get("selector_status") == "ambiguous",
               f"[explain-ambiguous] selector_status={out.get('selector_status')!r}")
        matches = out.get("matches", [])
        expect(len(matches) == 2,
               f"[explain-ambiguous] len(matches)={len(matches)} (want 2)")
        ini_slugs = {m["ini_slug"] for m in matches}
        expect("ini-001" in ini_slugs and "ini-002" in ini_slugs,
               f"[explain-ambiguous] ini_slugs={ini_slugs!r}")


def case_explain_item_within_ini_duplicate_not_ambiguous() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_workspace(root, """
            ["ini-001"]
            name = "Alpha"
            status = "active"
            milestone = "M1"
            ["ini-001".work]
            active  = ["spec/dup-slug"]
            shipped = ["spec/dup-slug"]
            queue   = []
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "dup-slug")
        expect(out.get("selector_status") == "matched",
               f"[explain-dup] selector_status={out.get('selector_status')!r}")
        item = out.get("explained_item", {})
        expect(item.get("list") == "active",
               f"[explain-dup] list={item.get('list')!r} (want active > shipped)")
        expect(item.get("classification") == "active",
               f"[explain-dup] classification={item.get('classification')!r}")


def case_explain_item_shaping_only_not_found() -> None:
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
            queue   = []
            ["ini-001".shaping_queue]
            active  = [{slug = "shape-only", type = "shape"}]
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "shape-only")
        expect(out.get("selector_status") == "not_found",
               f"[explain-shaping-only] selector_status={out.get('selector_status')!r}")


def case_explain_item_downstream_sole_blocker() -> None:
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
            queue   = [
                "spec/item-b",
                {path = "spec/item-a", needs = ["work:spec/item-b"]},
            ]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "spec/item-b")
        expect(out.get("selector_status") == "matched",
               f"[downstream-sole] selector_status={out.get('selector_status')!r}")
        item = out.get("explained_item", {})
        downstream = item.get("downstream_unblocked", [])
        expect("spec/item-a" in downstream,
               f"[downstream-sole] downstream_unblocked={downstream!r} (want item-a)")


def case_explain_item_downstream_not_sole_blocker() -> None:
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
            queue   = [
                "spec/item-b",
                "spec/item-c",
                {path = "spec/item-a", needs = ["work:spec/item-b", "work:spec/item-c"]},
            ]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "spec/item-b")
        item = out.get("explained_item", {})
        downstream = item.get("downstream_unblocked", [])
        expect("spec/item-a" not in downstream,
               f"[downstream-not-sole] item-a should not be in downstream: {downstream!r}")


def case_explain_item_downstream_cross_ini_excluded() -> None:
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
            queue   = ["spec/item-b"]
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
            queue   = [{path = "spec/item-a", needs = ["ini-001:work:spec/item-b"]}]
            ["ini-002".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        out = explain_item(result, "spec/item-b")
        item = out.get("explained_item", {})
        downstream = item.get("downstream_unblocked", [])
        expect("spec/item-a" not in downstream,
               f"[downstream-cross-ini] item-a should not be in downstream: {downstream!r}")


def case_analyze_bounded_path_traversal_entry() -> None:
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
            queue   = ["spec/../../../etc/passwd"]
            ["ini-001".shaping_queue]
            active  = []
            backlog = []
        """)
        result = analyze_bounded(root)
        expect(result.declared_spec_files_read == 0,
               f"[traversal] declared_spec_files_read={result.declared_spec_files_read} (want 0)")
        expect(isinstance(result.reconciliation, list),
               "[traversal] result must be structurally valid")


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


def test_ac2f_list_valued_needs() -> None:
    _run_case(case_list_valued_needs)


def test_ac2g_ready_and_transitively_blocked() -> None:
    _run_case(case_ready_and_transitively_blocked)


def test_ac2h_spec_statuses() -> None:
    _run_case(case_spec_statuses)


def test_ac2h_spec_status_parser_boundaries() -> None:
    _run_case(case_spec_status_parser_boundaries)


def test_ac2h_spec_status_sister_function_parity() -> None:
    _run_case(case_spec_status_sister_function_parity)


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


def test_extract_repo_backlog_preserves_declared_display_data() -> None:
    _run_case(case_extract_repo_backlog_preserves_declared_display_data)


def test_ac3g_type2_cleanup_ownership() -> None:
    _run_case(case_type2_cleanup_ownership)


def test_ac2d_active_local_dep() -> None:
    _run_case(case_local_work_dep_blocked_by_active)


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


def test_analyze_bounded_skips_type1() -> None:
    _run_case(case_analyze_bounded_skips_type1)


def test_analyze_bounded_file_counts() -> None:
    _run_case(case_analyze_bounded_file_counts)


def test_analyze_full_file_counts() -> None:
    _run_case(case_analyze_full_file_counts)


def test_explain_item_ready() -> None:
    _run_case(case_explain_item_ready)


def test_explain_item_blocked() -> None:
    _run_case(case_explain_item_blocked)


def test_explain_item_active() -> None:
    _run_case(case_explain_item_active)


def test_explain_item_active_downstream() -> None:
    _run_case(case_explain_item_active_downstream)


def test_explain_item_shipped() -> None:
    _run_case(case_explain_item_shipped)


def test_explain_item_not_found() -> None:
    _run_case(case_explain_item_not_found)


def test_explain_item_ambiguous_cross_initiative() -> None:
    _run_case(case_explain_item_ambiguous_cross_initiative)


def test_explain_item_within_ini_duplicate_not_ambiguous() -> None:
    _run_case(case_explain_item_within_ini_duplicate_not_ambiguous)


def test_explain_item_shaping_only_not_found() -> None:
    _run_case(case_explain_item_shaping_only_not_found)


def test_explain_item_downstream_sole_blocker() -> None:
    _run_case(case_explain_item_downstream_sole_blocker)


def test_explain_item_downstream_not_sole_blocker() -> None:
    _run_case(case_explain_item_downstream_not_sole_blocker)


def test_explain_item_downstream_cross_ini_excluded() -> None:
    _run_case(case_explain_item_downstream_cross_ini_excluded)


def test_analyze_bounded_path_traversal_entry() -> None:
    _run_case(case_analyze_bounded_path_traversal_entry)


# ── Order 2B: compute_repair_plan ─────────────────────────────────────────────

def test_compute_repair_plan_queue_shipped() -> None:
    _run_case(case_compute_repair_plan_queue_shipped)


def test_compute_repair_plan_queue_archived() -> None:
    _run_case(case_compute_repair_plan_queue_archived)


def test_compute_repair_plan_bare_archived_duplicate_is_manual() -> None:
    _run_case(case_compute_repair_plan_bare_archived_duplicate_is_manual)


def test_compute_repair_plan_bare_archived_unsupported_string_is_manual() -> None:
    _run_case(case_compute_repair_plan_bare_archived_unsupported_string_is_manual)


def test_compute_repair_plan_bare_archived_top_level_duplicate_is_manual() -> None:
    _run_case(case_compute_repair_plan_bare_archived_top_level_duplicate_is_manual)


def test_compute_repair_plan_bare_archived_cross_initiative_duplicate_is_manual() -> None:
    _run_case(case_compute_repair_plan_bare_archived_cross_initiative_duplicate_is_manual)


def test_compute_repair_plan_bare_archived_second_queue_duplicate_is_manual() -> None:
    _run_case(case_compute_repair_plan_bare_archived_second_queue_duplicate_is_manual)


def test_compute_repair_plan_active_source_is_manual() -> None:
    _run_case(case_compute_repair_plan_active_source_is_manual)


def test_compute_repair_plan_type1_manual() -> None:
    _run_case(case_compute_repair_plan_type1_manual)


def test_compute_repair_plan_type3_manual() -> None:
    _run_case(case_compute_repair_plan_type3_manual)


def test_compute_repair_plan_approved_not_eligible() -> None:
    _run_case(case_compute_repair_plan_approved_not_eligible)


def test_compute_repair_plan_path_in_queue_and_active() -> None:
    _run_case(case_compute_repair_plan_path_in_queue_and_active)


def test_compute_repair_plan_duplicate_path_in_queue() -> None:
    _run_case(case_compute_repair_plan_duplicate_path_in_queue)


def test_compute_repair_plan_fingerprint_is_sha256() -> None:
    _run_case(case_compute_repair_plan_fingerprint_is_sha256)


def test_compute_repair_plan_empty_reconciliation() -> None:
    _run_case(case_compute_repair_plan_empty_reconciliation)


def test_compute_repair_plan_has_plan_id() -> None:
    _run_case(case_compute_repair_plan_has_plan_id)


def test_compute_repair_plan_operation_has_spec_status_fingerprint() -> None:
    _run_case(case_compute_repair_plan_operation_has_spec_status_fingerprint)


def test_compute_repair_plan_invalid_structured_source_is_manual() -> None:
    _run_case(case_compute_repair_plan_invalid_structured_source_is_manual)


def test_compute_repair_plan_malformed_structured_needs_is_manual() -> None:
    _run_case(case_compute_repair_plan_malformed_structured_needs_is_manual)


def test_compute_repair_plan_provenance_mismatch_is_manual() -> None:
    _run_case(case_compute_repair_plan_provenance_mismatch_is_manual)


def _make_finding(finding_type: int, spec_path: str, spec_status: str,
                  ini_slug: str, list_name: str):
    from workspace_status_engine import ReconciliationFinding
    return ReconciliationFinding(
        finding_type=finding_type, spec_path=spec_path, spec_status=spec_status,
        ini_slug=ini_slug, list_name=list_name,
    )


def _make_result(type1=None, type2=None, type3=None):
    """Minimal WorkspaceStatusResult stub for compute_repair_plan tests."""
    from workspace_status_engine import WorkspaceStatusResult
    reconciliation = list(type1 or []) + list(type2 or []) + list(type3 or [])
    return WorkspaceStatusResult(
        initiatives=[], classifications=[], shaping_classifications=[],
        reconciliation=reconciliation, elapsed_s=0.0,
    )


def case_compute_repair_plan_queue_shipped():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [{path = "docs/specs/foo/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Foo", needs = []}]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "foo"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        f = _make_finding(2, "docs/specs/foo/spec.md", "Shipped", "ini-001", "queue")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 1, "2B shipped: expected 1 auto op")
        op = plan.automatic_operations[0]
        expect(
            op.operation_type == "queue-to-shipped",
            f"2B shipped: op_type={op.operation_type!r}",
        )
        expect(
            op.spec_path == "docs/specs/foo/spec.md",
            f"2B shipped: spec_path={op.spec_path!r}",
        )
        expect(op.spec_status == "Shipped", f"2B shipped: spec_status={op.spec_status!r}")
        expect(op.ini_slug == "ini-001", f"2B shipped: ini_slug={op.ini_slug!r}")
        expect(len(plan.manual_findings) == 0, "2B shipped: expected 0 manual findings")


def case_compute_repair_plan_queue_archived():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = ["spec/bar"]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "bar"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Archived\n", encoding="utf-8")
        f = _make_finding(2, "spec/bar", "Archived", "ini-001", "queue")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 1, "2B archived: expected 1 auto op")
        op = plan.automatic_operations[0]
        expect(op.operation_type == "queue-remove", f"2B archived: op_type={op.operation_type!r}")
        expect(op.spec_status == "Archived", f"2B archived: spec_status={op.spec_status!r}")
        expect(len(plan.manual_findings) == 0, "2B archived: expected 0 manual")


def case_compute_repair_plan_bare_archived_duplicate_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = ["spec/bar"]
active = ["docs/specs/bar/spec.md"]
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "bar"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Archived\n", encoding="utf-8")
        f = _make_finding(2, "spec/bar", "Archived", "ini-001", "queue")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B dup archived: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B dup archived: expected 1 manual")
        expect(
            plan.manual_findings[0].reason == "type2-queue-canonical-blocked",
            f"2B dup archived: reason={plan.manual_findings[0].reason!r}",
        )


def case_compute_repair_plan_bare_archived_unsupported_string_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = ["foo"]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "foo"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Archived\n", encoding="utf-8")
        f = _make_finding(2, "foo", "Archived", "ini-001", "queue")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B unsupported: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B unsupported: expected 1 manual")
        expect(
            plan.manual_findings[0].reason == "type2-queue-canonical-blocked",
            f"2B unsupported: reason={plan.manual_findings[0].reason!r}",
        )


def case_compute_repair_plan_bare_archived_top_level_duplicate_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
[backlog]
open = [{slug = "bar", type = "spec", source = "repo-origin", summary = "Backlog alias", needs = []}]
closed = []

["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = ["spec/bar"]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "bar"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Archived\n", encoding="utf-8")
        f = _make_finding(2, "spec/bar", "Archived", "ini-001", "queue")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B top dup: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B top dup: expected 1 manual")
        expect(
            plan.manual_findings[0].reason == "type2-queue-canonical-blocked",
            f"2B top dup: reason={plan.manual_findings[0].reason!r}",
        )


def case_compute_repair_plan_bare_archived_cross_initiative_duplicate_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = ["spec/bar"]
active = []
shipped = []

["ini-002"]
name = "Other"
status = "active"
milestone = "M2"

["ini-002".work]
queue = []
active = []
shipped = ["docs/specs/bar/spec.md"]
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "bar"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Archived\n", encoding="utf-8")
        f = _make_finding(2, "spec/bar", "Archived", "ini-001", "queue")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B cross dup: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B cross dup: expected 1 manual")
        expect(
            plan.manual_findings[0].reason == "type2-queue-canonical-blocked",
            f"2B cross dup: reason={plan.manual_findings[0].reason!r}",
        )


def case_compute_repair_plan_bare_archived_second_queue_duplicate_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = ["spec/bar", "docs/specs/bar/spec.md"]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "bar"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Archived\n", encoding="utf-8")
        f = _make_finding(2, "spec/bar", "Archived", "ini-001", "queue")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B queue dup: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B queue dup: expected 1 manual")
        expect(
            plan.manual_findings[0].reason == "type2-queue-canonical-blocked",
            f"2B queue dup: reason={plan.manual_findings[0].reason!r}",
        )


def case_compute_repair_plan_active_source_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_bytes(b"[ini-001]\n")
        f = _make_finding(2, "spec/active-thing", "Shipped", "ini-001", "active")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B active: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B active: expected 1 manual")
        mf = plan.manual_findings[0]
        expect(mf.reason == "type2-active-source", f"2B active: reason={mf.reason!r}")


def case_compute_repair_plan_type1_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_bytes(b"[ini-001]\n")
        f = _make_finding(1, "spec/untracked", "Approved", "ini-001", "")
        result = _make_result(type1=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B type1: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B type1: expected 1 manual")
        expect(plan.manual_findings[0].reason == "type1-untracked", "2B type1: reason")


def case_compute_repair_plan_type3_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_bytes(b"[ini-001]\n")
        f = _make_finding(3, "spec/premature", "Implementing", "ini-001", "shipped")
        result = _make_result(type3=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B type3: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B type3: expected 1 manual")
        expect(plan.manual_findings[0].reason == "type3-premature", "2B type3: reason")


def case_compute_repair_plan_approved_not_eligible():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_bytes(b"[ini-001]\n")
        # Type 2 finding with Approved in queue (defensive: engine emits this only if it finds it)
        f = _make_finding(2, "spec/live", "Approved", "ini-001", "queue")
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B approved: must NOT be automatic")
        expect(len(plan.manual_findings) == 1, "2B approved: expected 1 manual")
        expect("approved" in plan.manual_findings[0].reason,
               f"2B approved: reason={plan.manual_findings[0].reason!r}")


def case_compute_repair_plan_path_in_queue_and_active():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [{path = "docs/specs/dual/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Dual", needs = []}]
active = ["spec/dual"]
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "dual"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        fq = _make_finding(2, "docs/specs/dual/spec.md", "Shipped", "ini-001", "queue")
        fa = _make_finding(2, "spec/dual", "Shipped", "ini-001", "active")
        result = _make_result(type2=[fq, fa])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B dual: expected 0 auto ops")
        expect(len(plan.manual_findings) == 2, "2B dual: expected 2 manual findings")
        reasons = {mf.reason for mf in plan.manual_findings}
        expect("type2-queue-canonical-blocked" in reasons, f"2B dual: reasons={reasons}")
        expect("type2-active-source" in reasons, f"2B dual: reasons={reasons}")


def case_compute_repair_plan_duplicate_path_in_queue():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_bytes(b"[ini-001]\n")
        f1 = _make_finding(2, "spec/dup", "Shipped", "ini-001", "queue")
        f2 = _make_finding(2, "spec/dup", "Shipped", "ini-001", "queue")
        result = _make_result(type2=[f1, f2])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B dup: expected 0 auto ops")
        expect(len(plan.manual_findings) == 2, "2B dup: expected 2 manual findings")
        reasons = [mf.reason for mf in plan.manual_findings]
        expect(all(r == "type2-queue-duplicate" for r in reasons),
               f"2B dup: reasons={reasons}")


def case_compute_repair_plan_fingerprint_is_sha256():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        content = b"[ini-001]\nname = \"Test\"\n"
        (root / "workspace.toml").write_bytes(content)
        result = _make_result()
        plan = compute_repair_plan(result, root / "workspace.toml")
        expected = hashlib.sha256(content).hexdigest()
        expect(plan.workspace_fingerprint == expected,
               f"2B fingerprint: got {plan.workspace_fingerprint!r}, expected {expected!r}")


def case_compute_repair_plan_empty_reconciliation():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_bytes(b"[ini-001]\n")
        result = _make_result()
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B empty: expected 0 auto ops")
        expect(len(plan.manual_findings) == 0, "2B empty: expected 0 manual findings")


def case_compute_repair_plan_has_plan_id():
    """2B: plan_id is a non-empty SHA-256 hex string; identical inputs produce same plan_id."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_bytes(b"[ini-001]\n")
        result = _make_result()
        plan1 = compute_repair_plan(result, root / "workspace.toml")
        plan2 = compute_repair_plan(result, root / "workspace.toml")
        expect(plan1.plan_id == plan2.plan_id,
               f"2B plan_id: should be deterministic, got {plan1.plan_id!r} vs {plan2.plan_id!r}")
        expect(len(plan1.plan_id) == 64,
               f"2B plan_id: expected 64-char SHA-256, got len={len(plan1.plan_id)}")


def case_compute_repair_plan_operation_has_spec_status_fingerprint():
    """2B: auto operations include spec_status_fingerprint (SHA-256 of status line)."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [{path = "docs/specs/my-feature/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "My feature", needs = []}]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "my-feature"
        spec_dir.mkdir(parents=True)
        status_line = "- **Status:** Shipped"
        (spec_dir / "spec.md").write_text(
            f"# My Feature\n\n{status_line}\n", encoding="utf-8"
        )
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        f = _make_finding(
            2, "docs/specs/my-feature/spec.md", "Shipped", "ini-001", "queue"
        )
        result = _make_result(type2=[f])
        plan = compute_repair_plan(result, root / "workspace.toml")
        expect(len(plan.automatic_operations) == 1,
               f"2B op-fp: expected 1 auto op, got {len(plan.automatic_operations)}")
        op = plan.automatic_operations[0]
        expected_fp = hashlib.sha256(status_line.encode("utf-8")).hexdigest()
        expect(op.spec_status_fingerprint == expected_fp,
               f"2B op-fp: got {op.spec_status_fingerprint!r}, expected {expected_fp!r}")


def case_compute_repair_plan_invalid_structured_source_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [{path = "docs/specs/bad-source/spec.md", kind = "spec", source = {mode = "tracker-origin"}, summary = "Bad source", needs = []}]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "bad-source"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        f = _make_finding(2, "docs/specs/bad-source/spec.md", "Shipped", "ini-001", "queue")
        plan = compute_repair_plan(_make_result(type2=[f]), root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B bad source: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B bad source: expected 1 manual")
        expect(
            plan.manual_findings[0].reason == "type2-queue-canonical-blocked",
            f"2B bad source: reason={plan.manual_findings[0].reason!r}",
        )


def case_compute_repair_plan_malformed_structured_needs_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [{path = "docs/specs/bad-needs/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "Bad needs", needs = [{type = "local", kind = "spec"}]}]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "bad-needs"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text("- **Status:** Archived\n", encoding="utf-8")
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        f = _make_finding(2, "docs/specs/bad-needs/spec.md", "Archived", "ini-001", "queue")
        plan = compute_repair_plan(_make_result(type2=[f]), root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B bad needs: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B bad needs: expected 1 manual")
        expect(
            plan.manual_findings[0].reason == "type2-queue-canonical-blocked",
            f"2B bad needs: reason={plan.manual_findings[0].reason!r}",
        )


def case_compute_repair_plan_provenance_mismatch_is_manual():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "workspace.toml").write_text(
            """\
["ini-001"]
name = "Test"
status = "active"
milestone = "M1"

["ini-001".work]
queue = [{path = "docs/specs/prov/spec.md", kind = "spec", source = {mode = "repo-origin", parent = "docs/product/briefs/right.md"}, summary = "Provenance", needs = []}]
active = []
shipped = []
""",
            encoding="utf-8",
        )
        spec_dir = root / "docs" / "specs" / "prov"
        spec_dir.mkdir(parents=True)
        (spec_dir / "spec.md").write_text(
            "- **Status:** Shipped\n- **Brief:** docs/product/briefs/wrong.md\n",
            encoding="utf-8",
        )
        (spec_dir / "plan.md").write_text("# Plan\n", encoding="utf-8")
        brief_dir = root / "docs" / "product" / "briefs"
        brief_dir.mkdir(parents=True)
        (brief_dir / "right.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        (brief_dir / "wrong.md").write_text("- **Status:** Shipped\n", encoding="utf-8")
        f = _make_finding(2, "docs/specs/prov/spec.md", "Shipped", "ini-001", "queue")
        plan = compute_repair_plan(_make_result(type2=[f]), root / "workspace.toml")
        expect(len(plan.automatic_operations) == 0, "2B provenance: expected 0 auto ops")
        expect(len(plan.manual_findings) == 1, "2B provenance: expected 1 manual")
        expect(
            plan.manual_findings[0].reason == "type2-queue-canonical-blocked",
            f"2B provenance: reason={plan.manual_findings[0].reason!r}",
        )


# ── Runner ────────────────────────────────────────────────────────────────────

CASES = [
    ("AC2a multiple_active_initiatives", case_multiple_active_initiatives),
    ("AC2b paused_closed_initiatives", case_paused_closed_initiatives),
    ("AC2c ordered_queues", case_ordered_queues),
    ("AC2d local_work_deps", case_local_work_deps),
    ("AC2d-active work_dep_on_active_stays_blocked", case_local_work_dep_blocked_by_active),
    ("AC2d-dup queue_entries_in_active_or_shipped_excluded",
     case_queue_entries_in_active_or_shipped_excluded),
    ("AC2e cross_initiative_deps", case_cross_initiative_deps),
    ("AC2f shape_research_brief_deps", case_shape_research_brief_deps),
    ("AC2f-list list_valued_needs", case_list_valued_needs),
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
    ("repo backlog display projection", case_extract_repo_backlog_preserves_declared_display_data),
    ("AC3g type2_cleanup_ownership", case_type2_cleanup_ownership),
    ("AC3a dag_all_needs_prefixes", case_dag_all_needs_prefixes),
    ("type2_cleanup_mutation_contract", case_type2_cleanup_mutation_contract),
    ("type1_type3_no_cleanup", case_type1_type3_no_cleanup),
    ("F1a research_type_filter", case_research_type_filter),
    ("F1b untyped_backlog_not_shaping", case_untyped_backlog_not_shaping),
    ("F2 shaping_classifications", case_shaping_classifications),
    ("F3 type2_cleanup_duplicate_source", case_type2_cleanup_duplicate_source),
    ("work_loop_contract_anchor", case_work_loop_contract_anchor),
    ("integration full_analyze", case_full_analyze),
    ("F4a shaping_deduplication", case_shaping_deduplication),
    ("F4b work_loop_stale_warnings", case_work_loop_stale_warnings),
    ("F4c work_loop_stale_both_lists", case_work_loop_stale_both_lists),
    ("F4d work_loop_slug_normalization", case_work_loop_slug_normalization),
    ("F4e missing_status_not_active", case_missing_status_not_active),
    ("F4f nonletter_transition_segment", case_nonletter_transition_segment),
    ("F4g safe_spec_path_dot_segments", case_safe_spec_path_dot_segments),
    ("1B analyze_bounded_skips_type1", case_analyze_bounded_skips_type1),
    ("1B analyze_bounded_file_counts", case_analyze_bounded_file_counts),
    ("1B analyze_full_file_counts", case_analyze_full_file_counts),
    ("1B explain_item_ready", case_explain_item_ready),
    ("1B explain_item_blocked", case_explain_item_blocked),
    ("1B explain_item_active", case_explain_item_active),
    ("1B explain_item_active_downstream", case_explain_item_active_downstream),
    ("1B explain_item_shipped", case_explain_item_shipped),
    ("1B explain_item_not_found", case_explain_item_not_found),
    ("1B explain_item_ambiguous_cross_initiative",
     case_explain_item_ambiguous_cross_initiative),
    ("1B explain_item_within_ini_duplicate_not_ambiguous",
     case_explain_item_within_ini_duplicate_not_ambiguous),
    ("1B explain_item_shaping_only_not_found", case_explain_item_shaping_only_not_found),
    ("1B explain_item_downstream_sole_blocker", case_explain_item_downstream_sole_blocker),
    ("1B explain_item_downstream_not_sole_blocker",
     case_explain_item_downstream_not_sole_blocker),
    ("1B explain_item_downstream_cross_ini_excluded",
     case_explain_item_downstream_cross_ini_excluded),
    ("1B analyze_bounded_path_traversal_entry", case_analyze_bounded_path_traversal_entry),
    # ── Order 2B: compute_repair_plan ─────────────────────────────────────────
    ("2B compute_repair_plan_queue_shipped", case_compute_repair_plan_queue_shipped),
    ("2B compute_repair_plan_queue_archived", case_compute_repair_plan_queue_archived),
    (
        "2B compute_repair_plan_bare_archived_duplicate_is_manual",
        case_compute_repair_plan_bare_archived_duplicate_is_manual,
    ),
    (
        "2B compute_repair_plan_bare_archived_unsupported_string_is_manual",
        case_compute_repair_plan_bare_archived_unsupported_string_is_manual,
    ),
    (
        "2B compute_repair_plan_bare_archived_top_level_duplicate_is_manual",
        case_compute_repair_plan_bare_archived_top_level_duplicate_is_manual,
    ),
    (
        "2B compute_repair_plan_bare_archived_cross_initiative_duplicate_is_manual",
        case_compute_repair_plan_bare_archived_cross_initiative_duplicate_is_manual,
    ),
    (
        "2B compute_repair_plan_bare_archived_second_queue_duplicate_is_manual",
        case_compute_repair_plan_bare_archived_second_queue_duplicate_is_manual,
    ),
    (
        "2B compute_repair_plan_active_source_is_manual",
        case_compute_repair_plan_active_source_is_manual,
    ),
    ("2B compute_repair_plan_type1_manual", case_compute_repair_plan_type1_manual),
    ("2B compute_repair_plan_type3_manual", case_compute_repair_plan_type3_manual),
    (
        "2B compute_repair_plan_approved_not_eligible",
        case_compute_repair_plan_approved_not_eligible,
    ),
    (
        "2B compute_repair_plan_path_in_queue_and_active",
        case_compute_repair_plan_path_in_queue_and_active,
    ),
    (
        "2B compute_repair_plan_duplicate_path_in_queue",
        case_compute_repair_plan_duplicate_path_in_queue,
    ),
    (
        "2B compute_repair_plan_fingerprint_is_sha256",
        case_compute_repair_plan_fingerprint_is_sha256,
    ),
    (
        "2B compute_repair_plan_empty_reconciliation",
        case_compute_repair_plan_empty_reconciliation,
    ),
    (
        "2B compute_repair_plan_has_plan_id",
        case_compute_repair_plan_has_plan_id,
    ),
    (
        "2B compute_repair_plan_operation_has_spec_status_fingerprint",
        case_compute_repair_plan_operation_has_spec_status_fingerprint,
    ),
    (
        "2B compute_repair_plan_invalid_structured_source_is_manual",
        case_compute_repair_plan_invalid_structured_source_is_manual,
    ),
    (
        "2B compute_repair_plan_malformed_structured_needs_is_manual",
        case_compute_repair_plan_malformed_structured_needs_is_manual,
    ),
    (
        "2B compute_repair_plan_provenance_mismatch_is_manual",
        case_compute_repair_plan_provenance_mismatch_is_manual,
    ),
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
