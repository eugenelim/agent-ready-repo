#!/usr/bin/env python3
"""Pin the blocking topology of the split Windows compatibility workflow."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = ROOT / ".github" / "workflows" / "build-check-windows.yml"


def fail(message: str) -> None:
    print(f"build-check-windows workflow: {message}", file=sys.stderr)
    raise SystemExit(1)


def job_block(workflow: str, job_name: str) -> str:
    """Return one top-level job block from the repository-owned workflow."""
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n(.*?)(?=^  [a-z0-9_-]+:\n|\Z)",
        workflow,
    )
    if match is None:
        fail(f"job {job_name!r} is missing")
    return match.group(1)


def main() -> int:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    agentbundle = job_block(workflow, "agentbundle-windows")
    credbroker = job_block(workflow, "credbroker-tests-windows")
    aggregate = job_block(workflow, "build-check-windows")

    if "    runs-on: windows-latest\n" not in agentbundle:
        fail("AgentBundle compatibility job must run on windows-latest")
    if "    runs-on: windows-latest\n" not in credbroker:
        fail("CredBroker test job must run on windows-latest")
    for job_name, block, expected_timeout in (
        ("AgentBundle", agentbundle, 15),
        ("CredBroker", credbroker, 10),
        ("aggregate", aggregate, 5),
    ):
        if f"    timeout-minutes: {expected_timeout}\n" not in block:
            fail(f"{job_name} job must retain its bounded timeout")

    suite_step = (
        "      - name: Run CredBroker suite\n"
        "        working-directory: packages/credbroker\n"
        "        run: python -m pytest\n"
    )
    if credbroker.count(suite_step) != 1:
        fail("CredBroker job must run its complete package suite")

    if "    name: make build-check (windows)\n" not in aggregate:
        fail("aggregate must preserve the required check name")
    required_needs = (
        "    needs:\n"
        "      - agentbundle-windows\n"
        "      - credbroker-tests-windows\n"
    )
    if required_needs not in aggregate:
        fail("aggregate must depend on both Windows jobs")
    if "    if: ${{ always() }}\n" not in aggregate:
        fail("aggregate must run even when a dependency fails or is cancelled")

    for result in (
        "needs.agentbundle-windows.result",
        "needs.credbroker-tests-windows.result",
    ):
        if result not in aggregate:
            fail(f"aggregate does not check {result}")
    for result_variable in ("AGENTBUNDLE_RESULT", "CREDBROKER_RESULT"):
        comparison = f'[ "${result_variable}" != "success" ]'
        if comparison not in aggregate:
            fail(f"aggregate does not require {result_variable} to succeed")

    print("build-check-windows workflow: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
