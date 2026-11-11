#!/usr/bin/env python3
"""Posture test for ``.github/workflows/release-agentbundle.yml`` (check 4 wiring).

RFC-0109 D7 check 4 stops a CLI shipping a specification version the site does
not serve. It only gates a release if (a) a job runs it, (b) that job is
tag-only, and (c) BOTH publish jobs list it in ``needs``. Each is asserted from
the workflow text. A mutation matrix runs on every invocation, so the audit is
shown to fail when a property is removed. The run line is pinned to the script
path, so the job cannot keep its name and stop calling the check.

Parse-free: a block-style job header and its ``needs:``/``if:`` lines, which is
the form this workflow uses. A flow-style or reordered job would fail closed
(the job reads as absent), not pass.
Pure stdlib, as required for new ``tools/`` additions.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "release-agentbundle.yml"
GATE_JOB = "release-gate"
PUBLISH_JOBS = ("publish-pypi", "publish-artifactory")
GATE_RUN = "run: python3 tools/catalogue/check_release_gate.py"


def _jobs(text: str) -> dict[str, str]:
    """Map each job name to its block text (from its header to the next header)."""
    _, _, tail = text.partition("\njobs:\n")
    blocks: dict[str, list[str]] = {}
    current = None
    for line in tail.splitlines():
        header = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if header:
            current = header.group(1)
            blocks[current] = []
        elif current is not None:
            blocks[current].append(line)
    return {name: "\n".join(lines) for name, lines in blocks.items()}


def _needs(block: str) -> list[str]:
    match = re.search(r"^    needs:\s*\[([^\]]*)\]\s*$", block, re.M)
    return [n.strip() for n in match.group(1).split(",") if n.strip()] if match else []


def audit(text: str) -> list[str]:
    """Violation labels for the workflow text (empty = clean)."""
    jobs = _jobs(text)
    out: list[str] = []
    gate = jobs.get(GATE_JOB)
    if gate is None:
        out.append(f"gate-job-exists ({GATE_JOB} is absent)")
    else:
        if not re.search(r"^    if: github\.ref_type == 'tag'\s*$", gate, re.M):
            out.append("gate-job-tag-only (if: github.ref_type == 'tag' is absent)")
        if not any(line.strip() == GATE_RUN for line in gate.splitlines()):
            out.append(f"gate-job-runs-check ({GATE_RUN!r} is absent)")
    for name in PUBLISH_JOBS:
        if name not in jobs:
            out.append(f"publish-job-exists ({name} is absent)")
        elif GATE_JOB not in _needs(jobs[name]):
            out.append(f"publish-needs-gate ({name} does not list {GATE_JOB} in needs)")
    return out


def _mutations() -> list[tuple[str, str, object]]:
    return [
        ("drop the gate job", "gate-job-exists",
         lambda t: t.replace(f"\n  {GATE_JOB}:\n", "\n  renamed-job:\n", 1)),
        ("drop the tag condition", "gate-job-tag-only",
         lambda t: re.sub(r"(  release-gate:\n(?:.*\n)*?)    if: github\.ref_type == 'tag'\n",
                          r"\1", t, count=1)),
        ("stop running the script", "gate-job-runs-check",
         lambda t: t.replace(GATE_RUN, "run: echo skipped", 1)),
        ("pypi stops needing the gate", "publish-needs-gate",
         lambda t: re.sub(r"(  publish-pypi:\n    needs: \[[^\]]*?), release-gate\]", r"\1]", t, count=1)),
        ("artifactory stops needing the gate", "publish-needs-gate",
         lambda t: re.sub(r"(  publish-artifactory:\n    needs: \[[^\]]*?), release-gate\]", r"\1]", t, count=1)),
        ("drop a publish job", "publish-job-exists",
         lambda t: t.replace("\n  publish-artifactory:\n", "\n  other-job:\n", 1)),
    ]


def self_test(text: str) -> list[str]:
    """Baseline must be clean and every mutation must be caught for its label."""
    problems = [f"baseline: {v}" for v in audit(text)]
    for name, label, transform in _mutations():
        mutated = transform(text)  # type: ignore[operator]
        if mutated == text:
            problems.append(f"mutation {name!r} is a no-op")
        elif not any(v.startswith(label) for v in audit(mutated)):
            problems.append(f"mutation {name!r} was not caught as {label}")
    return problems


def main() -> int:
    if not WORKFLOW.is_file():
        print(f"FAIL: {WORKFLOW} not found", file=sys.stderr)
        return 1
    problems = self_test(WORKFLOW.read_text(encoding="utf-8"))
    if problems:
        print(f"FAIL: {len(problems)} problem(s)", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1
    print(f"OK: release-agentbundle.yml gate wired; {len(_mutations())} mutations each caught")
    return 0


if __name__ == "__main__":
    sys.exit(main())
