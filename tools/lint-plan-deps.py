#!/usr/bin/env python3
"""Lint the dependency graph of every `docs/specs/*/plan.md`.

FAILS on a dependency cycle (unschedulable — the plan is wrong); WARNS on a
forward-reference (a task whose declared dep is authored later — a valid
acyclic edge the topological scheduler reorders, but an authored-order smell
worth flagging). Reuses the tested scheduler in `loop-cohort.py` rather than
re-implementing the parser. The `new-spec` lint surface for RFC-0015 / spec
`docs/specs/wave-scheduled-supervisor/` (AC7).

Invoke via ``sys.executable`` (never a bash shim) for Windows portability:
    python3 tools/lint-plan-deps.py
"""
from __future__ import annotations

import glob
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LC_PATH = ROOT / "packs/core/.apm/skills/work-loop/scripts/loop-cohort.py"


def _load_loop_cohort():
    spec = importlib.util.spec_from_file_location("loop_cohort_lint", LC_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    lc = _load_loop_cohort()
    cycles = 0
    warnings = 0
    skipped: list[str] = []
    for plan in sorted(glob.glob(str(ROOT / "docs" / "specs" / "*" / "plan.md"))):
        name = Path(plan).parent.name
        ordered, deps = lc.parse_plan(Path(plan).read_text())
        if not ordered:
            skipped.append(name)  # e.g. kiro-ide-hook: no `### T<n>` headings
            continue
        cyc = lc.detect_cycles(ordered, deps)
        if cyc:
            print(f"ERROR  {name}: dependency cycle: {', '.join(cyc)}", file=sys.stderr)
            cycles += 1
        for task, dep in lc.detect_forward_refs(ordered, deps):
            print(f"warning  {name}: forward-reference {task} -> {dep} "
                  "(dep authored later; scheduler reorders)")
            warnings += 1
    if skipped:
        print(f"lint-plan-deps: skipped (no `### T<n>` tasks): {', '.join(skipped)}")
    print(f"lint-plan-deps: {cycles} cycle(s), {warnings} forward-ref warning(s)")
    return 1 if cycles else 0


if __name__ == "__main__":
    sys.exit(main())
