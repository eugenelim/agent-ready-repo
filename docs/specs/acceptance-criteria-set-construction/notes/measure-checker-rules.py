#!/usr/bin/env python3
"""Recompute the false-positive rates this spec claims for its two new rules.

Exists so the numbers in `spec.md` and `plan.md` can be falsified later. A rate
quoted from a run that no longer exists cannot be checked, and three such
claims in this delivery turned out to be wrong.

    python3 docs/specs/acceptance-criteria-set-construction/notes/measure-checker-rules.py
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]
CHECKER = ROOT / "packs/core/.apm/skills/new-spec/scripts/lint-contract-item-alignment.py"


def subject():
    spec = importlib.util.spec_from_file_location(
        "measure_lint_contract_item_alignment", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def rule_8(m) -> tuple[int, int, int]:
    """Entries scanned, run-matching flags, naive-counting flags."""
    entries = run_hits = count_hits = 0
    for plan in sorted((ROOT / "docs/specs").glob("*/plan.md")):
        body = plan.read_text(errors="replace")
        for _task, task_body in m.TASK.findall(body):
            for entry in m.ENTRY.findall(task_body):
                entries += 1
                run_hits += m.unterminated(entry)
                count_hits += m.FENCE.sub("", entry).count("`") % 2 == 1
    return entries, run_hits, count_hits


def rule_9(m, base: str, head: str) -> tuple[int, list[str]]:
    """Criteria reworded between two revisions, and those the rule reports."""
    d = "docs/specs/acceptance-criteria-set-construction"

    def changed(path: str) -> set[int]:
        out = subprocess.run(["git", "-C", str(ROOT), "diff", "-U0", base, head, "--", path],
                             capture_output=True, text=True).stdout
        lines: set[int] = set()
        for hunk in re.finditer(r"^@@ -\S+ \+(\d+)(?:,(\d+))? @@", out, re.M):
            start = int(hunk.group(1))
            lines.update(range(start, start + int(hunk.group(2) or 1)))
        return lines

    def at(path: str) -> str:
        return subprocess.run(["git", "-C", str(ROOT), "show", f"{head}:{path}"],
                              capture_output=True, text=True).stdout

    spec_text, plan_text = at(f"{d}/spec.md"), at(f"{d}/plan.md")
    spans = m.criterion_spans(spec_text)
    reworded = {spans[n] for n in changed(f"{d}/spec.md") if n < len(spans) and spans[n]}
    followed = m._plan_owners(plan_text, changed(f"{d}/plan.md"))
    return len(reworded), sorted(reworded - followed)


def main() -> int:
    m = subject()
    entries, run_hits, count_hits = rule_8(m)
    print(f"rule 8  entries={entries}  run-matching flags={run_hits}  "
          f"naive-counting flags={count_hits}")
    base, head = (sys.argv[1:3] + ["1dd987ed6", "282bf12cb"])[:2]
    reworded, reported = rule_9(m, base, head)
    print(f"rule 9  {base}..{head}  reworded={reworded}  reported={len(reported)}  "
          f"{', '.join(reported) or 'none'}")
    print("\nThe five real gaps in that span, adjudicated by hand on 2026-09-11:")
    print("  AC-0009 AC-0023 AC-0024 AC-0027 AC-0035")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
