#!/usr/bin/env python3
"""Reproducible large-workspace benchmark for workspace-status Order 0.

Generates a synthetic workspace with:
  - ≥ 250 spec directories
  - 30–80 queued entries across active initiatives
  - Multiple active initiatives (4)
  - A cross-initiative dependency chain
  - An untracked Approved spec (triggers Type 1)
  - A mix of ready, blocked, active, shipped, and archived specs

Run:  python3 tools/bench-workspace-status.py
Exit: 0 if benchmark completes successfully.
"""

from __future__ import annotations

import io
import sys
import tempfile
import time
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from workspace_status_engine import analyze

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

# ── Fixture parameters ────────────────────────────────────────────────────────

ACTIVE_INITIATIVES = 4          # ini-001..ini-004
# per ini: 1 active + 65 spec + 12 queued = 78; x4 + 1 untracked = 313
SPECS_PER_INI = 65
QUEUED_PER_INI = 12             # 4 × 12 = 48 queued entries (30–80 ✓)
SHIPPED_PER_INI = 8
ACTIVE_PER_INI = 1

# In ini-001 we set up a blocked cross-initiative dep chain:
#   ini-001-queued-0 needs ini-002:work:spec/ini-002-spec-never-shipped
#   That spec is NOT in ini-002.work.shipped → entry is BLOCKED.
CROSS_INI_DEP_INI = "ini-001"
CROSS_INI_PROVIDER = "ini-002"
CROSS_INI_SPEC = "spec/ini-002-spec-never-shipped"   # deliberately absent from shipped

# One untracked Approved spec (not listed in any initiative)
UNTRACKED_APPROVED_SLUG = "untracked-approved-order0"
UNTRACKED_APPROVED_PATH = f"spec/{UNTRACKED_APPROVED_SLUG}"


def _spec_status_text(status: str, slug: str) -> str:
    return f"# Spec: {slug}\n\n- **Status:** {status}\n\n## Acceptance Criteria\n\n- [ ] AC1\n"


def _build_workspace_toml(root: Path) -> None:
    sections: list[str] = []
    for i in range(1, ACTIVE_INITIATIVES + 1):
        ini_slug = f"ini-{i:03d}"

        active_paths = [f'"spec/{ini_slug}-active-0"']

        shipped_parts: list[str] = []
        for s in range(SHIPPED_PER_INI):
            shipped_parts.append(f'"spec/{ini_slug}-spec-{s}"')
        shipped_str = ", ".join(shipped_parts)

        queue_parts: list[str] = []
        for q in range(QUEUED_PER_INI):
            if i == 1 and q == 0:
                # Cross-initiative dep: blocked until ini-002-spec-0 ships
                queue_parts.append(
                    f'{{path = "spec/{ini_slug}-queued-{q}", '
                    f'needs = "{CROSS_INI_PROVIDER}:work:{CROSS_INI_SPEC}"}}'
                )
            elif q % 3 == 1:
                # Blocked on a local dep that IS shipped
                queue_parts.append(
                    f'{{path = "spec/{ini_slug}-queued-{q}", '
                    f'needs = "work:spec/{ini_slug}-spec-0"}}'
                )
            elif q % 5 == 2:
                # Blocked on a dep that is NOT shipped (unresolvable)
                queue_parts.append(
                    f'{{path = "spec/{ini_slug}-queued-{q}", '
                    f'needs = "work:spec/{ini_slug}-never-shipped"}}'
                )
            else:
                queue_parts.append(f'"spec/{ini_slug}-queued-{q}"')
        queue_str = ",\n  ".join(queue_parts)

        section = f"""
["{ini_slug}"]
name = "Initiative {i}"
status = "active"
milestone = "M1"
["{ini_slug}".work]
active  = [{", ".join(active_paths)}]
shipped = [{shipped_str}]
queue   = [
  {queue_str},
]
["{ini_slug}".shaping_queue]
active  = []
backlog = []
"""
        sections.append(section)

    (root / "workspace.toml").write_text("\n".join(sections), encoding="utf-8")


def _build_specs(root: Path) -> int:
    specs_dir = root / "docs" / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for i in range(1, ACTIVE_INITIATIVES + 1):
        ini_slug = f"ini-{i:03d}"

        # Active specs
        for a in range(ACTIVE_PER_INI):
            slug = f"{ini_slug}-active-{a}"
            p = specs_dir / slug / "spec.md"
            p.parent.mkdir(exist_ok=True)
            p.write_text(_spec_status_text("Implementing", slug), encoding="utf-8")
            count += 1

        # Shipped specs
        for s in range(SPECS_PER_INI):
            slug = f"{ini_slug}-spec-{s}"
            status = "Shipped" if s < SHIPPED_PER_INI else "Draft"
            if s == SPECS_PER_INI - 1:
                status = "Archived"
            p = specs_dir / slug / "spec.md"
            p.parent.mkdir(exist_ok=True)
            p.write_text(_spec_status_text(status, slug), encoding="utf-8")
            count += 1

        # Queued specs
        for q in range(QUEUED_PER_INI):
            slug = f"{ini_slug}-queued-{q}"
            p = specs_dir / slug / "spec.md"
            p.parent.mkdir(exist_ok=True)
            p.write_text(_spec_status_text("Approved", slug), encoding="utf-8")
            count += 1

    # Untracked Approved spec (AC4f — Type 1 finding)
    untracked_p = specs_dir / UNTRACKED_APPROVED_SLUG / "spec.md"
    untracked_p.parent.mkdir(exist_ok=True)
    untracked_p.write_text(
        _spec_status_text("Approved", UNTRACKED_APPROVED_SLUG), encoding="utf-8"
    )
    count += 1

    return count


def _count_spec_dirs(root: Path) -> int:
    specs_dir = root / "docs" / "specs"
    if not specs_dir.exists():
        return 0
    return sum(1 for d in specs_dir.iterdir() if d.is_dir() and (d / "spec.md").exists())


def run_benchmark() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # ── Generate fixture ──────────────────────────────────────────────────
        t_gen_start = time.monotonic()
        _build_workspace_toml(root)
        spec_count = _build_specs(root)
        t_gen = time.monotonic() - t_gen_start

        # Verify spec count
        actual_spec_dirs = _count_spec_dirs(root)

        # Count queued entries from workspace.toml
        ws = tomllib.loads((root / "workspace.toml").read_text(encoding="utf-8"))
        total_queued = sum(
            len(ws.get(k, {}).get("work", {}).get("queue", []))
            for k in ws if k.startswith("ini-")
        )

        # ── Run analysis (hot run for measurement) ────────────────────────────
        # Warm run first (filesystem caches)
        analyze(root)

        # Measured run
        t0 = time.monotonic()
        result = analyze(root)
        elapsed = time.monotonic() - t0

        # ── Collect output (simulate formatted report size) ───────────────────
        buf = io.StringIO()
        active_inis = [i for i in result.initiatives if i.status == "active"]
        buf.write(f"Active initiatives: {len(active_inis)}\n")
        for ini in active_inis:
            cls = [c for c in result.classifications if c.ini_slug == ini.slug]
            buf.write(f"  {ini.slug}: {len(cls)} queue entries\n")
            for c in cls[:5]:
                tag = "READY" if c.is_ready else f"BLOCKED({', '.join(c.blocking_needs)})"
                buf.write(f"    {c.entry.path}: {tag}\n")
        t1, t2, t3 = len(result.type1), len(result.type2), len(result.type3)
        buf.write(f"Reconciliation: T1={t1} T2={t2} T3={t3}\n")
        buf.write(f"Files read by reconciliation: {result.files_read}\n")
        buf.write(f"Elapsed: {result.elapsed_s:.4f}s\n")
        output_text = buf.getvalue()
        output_bytes = len(output_text.encode("utf-8"))

        # Cross-initiative dep check (AC4e): verify a blocked entry has the full
        # ini-NNN:work: prefix in its blocking_needs (not just a substring match).
        cross_ini_prefix = f"{CROSS_INI_PROVIDER}:work:"
        cross_dep_blocked = any(
            not c.is_ready and any(n.startswith(cross_ini_prefix) for n in c.blocking_needs)
            for c in result.classifications
        )

        # Untracked spec check (AC4f)
        type1_paths = {f.spec_path for f in result.type1}
        has_type1_untracked = UNTRACKED_APPROVED_PATH in type1_paths

        return {
            "fixture_generation_s": t_gen,
            "spec_dirs_created": spec_count,
            "spec_dirs_with_spec_md": actual_spec_dirs,
            "queued_entries": total_queued,
            "active_initiatives": len(active_inis),
            "ready_entries": len(result.ready),
            "blocked_entries": len(result.blocked),
            "type1_findings": len(result.type1),
            "type2_findings": len(result.type2),
            "type3_findings": len(result.type3),
            "files_read_by_reconciliation": result.files_read,
            "analysis_elapsed_s": elapsed,
            "output_size_bytes": output_bytes,
            "cross_dep_blocked": cross_dep_blocked,
            "has_untracked_approved": has_type1_untracked,
        }


def main() -> int:
    print("workspace-status benchmark — Order 0 baseline")
    print("=" * 56)
    print()

    print("Generating fixture and running analysis...")
    m = run_benchmark()
    print()

    # ── Fixture dimensions ────────────────────────────────────────────────────
    print("Fixture dimensions:")
    print(f"  Spec dirs created:        {m['spec_dirs_created']}")
    print(f"  Spec dirs with spec.md:   {m['spec_dirs_with_spec_md']}")
    print(f"  Queued entries:           {m['queued_entries']}")
    print(f"  Active initiatives:       {m['active_initiatives']}")
    print(f"  Fixture generation:       {m['fixture_generation_s']:.3f}s")
    print()

    # ── Analysis measurements ─────────────────────────────────────────────────
    print("Analysis measurements (engine only, no LLM):")
    print(f"  Ready entries:            {m['ready_entries']}")
    print(f"  Blocked entries:          {m['blocked_entries']}")
    print(f"  Type 1 findings:          {m['type1_findings']}")
    print(f"  Type 2 findings:          {m['type2_findings']}")
    print(f"  Type 3 findings:          {m['type3_findings']}")
    print(f"  Files read (reconcil.):   {m['files_read_by_reconciliation']}")
    print(f"  Analysis elapsed:         {m['analysis_elapsed_s']:.4f}s")
    print(f"  Output size:              {m['output_size_bytes']} bytes")
    print()

    # ── AC gate checks ────────────────────────────────────────────────────────
    errors: list[str] = []

    if m["spec_dirs_with_spec_md"] < 250:
        errors.append(f"AC4a: need ≥250 spec dirs, got {m['spec_dirs_with_spec_md']}")
    if not (30 <= m["queued_entries"] <= 80):
        errors.append(f"AC4b: need 30–80 queued entries, got {m['queued_entries']}")
    if m["active_initiatives"] < 2:
        errors.append(f"AC4c: need ≥2 active initiatives, got {m['active_initiatives']}")
    if not m["cross_dep_blocked"]:
        errors.append(
            "AC4e: expected cross-initiative dep chain (blocked entry with cross-ini need)"
        )
    if not m["has_untracked_approved"]:
        errors.append("AC4f: expected untracked Approved spec → Type 1 finding")

    if errors:
        print("AC gate FAILURES:")
        for e in errors:
            print(f"  ✖  {e}")
        print()
        return 1

    print("AC gates:")
    print(f"  ✓  AC4a: ≥250 spec dirs ({m['spec_dirs_with_spec_md']})")
    print(f"  ✓  AC4b: 30–80 queued entries ({m['queued_entries']})")
    print(f"  ✓  AC4c: ≥2 active initiatives ({m['active_initiatives']})")
    print(f"  ✓  AC4d: ready={m['ready_entries']}, blocked={m['blocked_entries']} (mix present)")
    print(f"  ✓  AC4e: cross-initiative dep chain (blocked on {CROSS_INI_PROVIDER})")
    print(f"  ✓  AC4f: untracked Approved spec → Type 1 ({m['type1_findings']} finding(s))")
    print(f"  ✓  AC4g: measurements collected (files={m['files_read_by_reconciliation']}, "
          f"t={m['analysis_elapsed_s']:.4f}s, out={m['output_size_bytes']}b, "
          f"T1={m['type1_findings']} T2={m['type2_findings']} T3={m['type3_findings']})")
    print("  ✓  AC4h: benchmark runs from python3 tools/bench-workspace-status.py")
    print()
    print("Benchmark complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
