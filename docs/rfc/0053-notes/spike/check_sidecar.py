#!/usr/bin/env python3
"""SPIKE DEMONSTRATOR (RFC-0053 Decision-7 prototype) — NOT a shipped tool.

The point this proves: the typed sidecar makes "everything holds together" *checkable*
by a ~60-line lint over plain JSON/markdown — no engine, no runtime, no daemon. This is
the same shape as child-4's traceability lint (docs/specs/traceability-lint/), run here
only to show the connectedness claim is empirical, not asserted. A real adopter consumes
child-4's lint; this file is evidence for the RFC, kept for reproducibility.

Usage:
    python3 check_sidecar.py traceability.json [open-questions.md]
"""
import json
import re
import sys
from pathlib import Path


def check_traceability(path: Path):
    """Orphan = a node missing a required edge along the chain.
    root (the vision) is exempt from needing an in-edge; leaf_kind (component) is exempt
    from needing an out-edge. Everything else needs both."""
    g = json.loads(path.read_text())
    root, leaf_kind = g["root"], g["leaf_kind"]
    ids = {n["id"]: n for n in g["nodes"]}
    has_in = {e["to"] for e in g["edges"]}
    has_out = {e["from"] for e in g["edges"]}
    orphans = []
    for nid, node in ids.items():
        missing = []
        if nid != root and nid not in has_in:
            missing.append("no producer (up-edge)")
        if node["kind"] != leaf_kind and nid not in has_out:
            missing.append("no consumer (down-edge)")
        if missing:
            orphans.append((nid, node["kind"], "; ".join(missing)))
    # dangling edge endpoints (an edge naming a node not in the inventory)
    dangling = sorted({p for e in g["edges"] for p in (e["from"], e["to"]) if p not in ids})
    return orphans, dangling, len(g["nodes"]), len(g["edges"])


def check_open_questions(path: Path):
    """Saturation OQ-clause: count rows whose status is open/routed (unsettled)."""
    rows = [r for r in path.read_text().splitlines() if r.startswith("| OQ-")]
    unsettled = []
    for r in rows:
        cells = [c.strip() for c in r.strip("|").split("|")]
        status = cells[4] if len(cells) > 4 else ""
        if status in ("open", "routed"):
            unsettled.append((cells[0], status))
    return len(rows), unsettled


def main():
    trace = Path(sys.argv[1])
    orphans, dangling, n_nodes, n_edges = check_traceability(trace)
    print(f"== traceability: {trace.name} ==")
    print(f"   {n_nodes} nodes, {n_edges} edges")
    if dangling:
        print(f"   DANGLING edge endpoints: {dangling}")
    if orphans:
        print(f"   ORPHANS ({len(orphans)}):")
        for nid, kind, why in orphans:
            print(f"     - {nid} [{kind}]: {why}")
    else:
        print("   no orphans — every node has a producer and a consumer")

    oq_clause_ok = True
    if len(sys.argv) > 2:
        oq = Path(sys.argv[2])
        total, unsettled = check_open_questions(oq)
        print(f"== open-questions: {oq.name} ==")
        print(f"   {total} rows, {len(unsettled)} unsettled (open/routed)")
        for qid, status in unsettled:
            print(f"     - {qid}: {status}")
        oq_clause_ok = not unsettled

    converged = not orphans and not dangling and oq_clause_ok
    print(f"== SATURATION: {'CONVERGED' if converged else 'NOT converged'} "
          f"(no-orphan AND oq-clause; the full-pass-no-edit clause is the human's eye) ==")
    sys.exit(0 if converged else 1)


if __name__ == "__main__":
    main()
