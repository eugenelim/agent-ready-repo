#!/usr/bin/env python3
"""Pin and mutation-test the split Windows workflow's blocking topology.

Blocking means two things and both are asserted: the aggregate reads every work
job's result, and its guard exits non-zero when one of them is not `success`.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "build-check-windows.yml"

Mutation = tuple[str, str, Callable[[str], str]]


def _job_block(workflow: str, job_name: str) -> str:
    """Return one top-level job block, or the empty string when absent."""
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n(.*?)(?=^  [a-z0-9_-]+:\n|\Z)",
        workflow,
    )
    return match.group(1) if match is not None else ""


RESULT_VARIABLES = (
    "AGENTBUNDLE_RESULT",
    "CREDBROKER_RESULT",
    "LOCK_SEMANTICS_RESULT",
)


def _guard_blocks_on_failure(aggregate: str) -> bool:
    """Return whether one guard makes *every* work job's failure exit non-zero.

    The comparisons alone prove only that the aggregate reads the results, and
    a first-match scan proves only that *some* guard exits. Splitting the guard
    into one blocking `if` plus two advisory ones satisfied both, leaving two of
    three Windows suites non-blocking behind the required check. So the matched
    condition must carry all three comparisons itself before the body is
    scanned for `exit 1`.
    """
    lines = aggregate.splitlines()
    for index, line in enumerate(lines):
        if not line.rstrip().endswith("; then"):
            continue
        if any(
            f'[ "${variable}" != "success" ]' not in line
            for variable in RESULT_VARIABLES
        ):
            continue
        for following in lines[index + 1 :]:
            stripped = following.strip()
            if stripped == "fi":
                return False
            if stripped == "exit 1":
                return True
    return False


def audit(text: str, evaluated: list[str] | None = None) -> list[str]:
    """Return stable violation labels for one workflow text."""
    violations: list[str] = []

    def check(label: str, condition: bool) -> None:
        if evaluated is not None:
            evaluated.append(label)
        if not condition:
            violations.append(label)

    check("workflow-file-present", bool(text))
    if not text:
        return violations

    blocks = {
        "agentbundle-windows": _job_block(text, "agentbundle-windows"),
        "credbroker-tests-windows": _job_block(text, "credbroker-tests-windows"),
        "lock-semantics-windows": _job_block(text, "lock-semantics-windows"),
        "build-check-windows": _job_block(text, "build-check-windows"),
    }
    for job_name, block in blocks.items():
        check(f"job-present[{job_name}]", bool(block))

    for job_name in (
        "agentbundle-windows",
        "credbroker-tests-windows",
        "lock-semantics-windows",
    ):
        check(
            f"windows-runner[{job_name}]",
            "    runs-on: windows-latest\n" in blocks[job_name],
        )

    for job_name, expected_timeout in (
        ("agentbundle-windows", 15),
        ("credbroker-tests-windows", 10),
        ("build-check-windows", 5),
    ):
        check(
            f"bounded-timeout[{job_name}]",
            f"    timeout-minutes: {expected_timeout}\n" in blocks[job_name],
        )

    suite_step = (
        "      - name: Run CredBroker suite\n"
        "        working-directory: packages/credbroker\n"
        "        run: python -m pytest\n"
    )
    check(
        "credbroker-full-suite",
        blocks["credbroker-tests-windows"].count(suite_step) == 1,
    )

    lease_suite_step = "        run: python -m pytest tools/test_coordination_lease.py -q\n"
    check(
        "lock-semantics-real-suite",
        blocks["lock-semantics-windows"].count(lease_suite_step) == 1,
    )

    aggregate = blocks["build-check-windows"]
    check(
        "aggregate-required-name",
        "    name: make build-check (windows)\n" in aggregate,
    )
    required_needs = (
        "    needs:\n"
        "      - agentbundle-windows\n"
        "      - credbroker-tests-windows\n"
        "      - lock-semantics-windows\n"
    )
    check("aggregate-needs-all", required_needs in aggregate)
    check("aggregate-always-runs", "    if: ${{ always() }}\n" in aggregate)

    for result in (
        "needs.agentbundle-windows.result",
        "needs.credbroker-tests-windows.result",
        "needs.lock-semantics-windows.result",
    ):
        check(f"aggregate-result-reference[{result}]", result in aggregate)

    for result_variable in RESULT_VARIABLES:
        comparison = f'[ "${result_variable}" != "success" ]'
        check(
            f"aggregate-requires-success[{result_variable}]",
            comparison in aggregate,
        )

    check("aggregate-blocks-on-failure", _guard_blocks_on_failure(aggregate))

    return violations


def _baseline() -> str:
    """Return the real workflow, or the empty missing-file sentinel."""
    if WORKFLOW.is_file():
        return WORKFLOW.read_text(encoding="utf-8")
    return ""


_MUTATIONS: list[Mutation] = [
    ("remove-workflow-file", "workflow-file-present", lambda _text: ""),
    (
        "rename-agentbundle-job",
        "job-present[agentbundle-windows]",
        lambda text: text.replace(
            "  agentbundle-windows:\n", "  agentbundle-windows-disabled:\n", 1
        ),
    ),
    (
        "move-agentbundle-off-windows",
        "windows-runner[agentbundle-windows]",
        lambda text: text.replace("    runs-on: windows-latest\n", "    runs-on: ubuntu-latest\n", 1),
    ),
    (
        "remove-agentbundle-timeout",
        "bounded-timeout[agentbundle-windows]",
        lambda text: text.replace("    timeout-minutes: 15\n", "    timeout-minutes: 16\n", 1),
    ),
    (
        "narrow-credbroker-suite",
        "credbroker-full-suite",
        lambda text: text.replace(
            "        run: python -m pytest\n",
            "        run: python -m pytest -q\n",
            1,
        ),
    ),
    (
        "replace-real-lease-suite",
        "lock-semantics-real-suite",
        lambda text: text.replace(
            "python -m pytest tools/test_coordination_lease.py -q",
            "python -m pytest tools/test_windows_lock_semantics.py -q",
            1,
        ),
    ),
    (
        "rename-required-check",
        "aggregate-required-name",
        lambda text: text.replace(
            "    name: make build-check (windows)\n",
            "    name: Windows aggregate\n",
            1,
        ),
    ),
    (
        "drop-lock-semantics-need",
        "aggregate-needs-all",
        lambda text: text.replace("      - lock-semantics-windows\n", "", 1),
    ),
    (
        "make-aggregate-conditional",
        "aggregate-always-runs",
        lambda text: text.replace(
            "    if: ${{ always() }}\n", "    if: ${{ success() }}\n", 1
        ),
    ),
    (
        "drop-lock-result-reference",
        "aggregate-result-reference[needs.lock-semantics-windows.result]",
        lambda text: text.replace(
            "${{ needs.lock-semantics-windows.result }}",
            "${{ needs.agentbundle-windows.result }}",
            1,
        ),
    ),
    (
        "stop-requiring-lock-success",
        "aggregate-requires-success[LOCK_SEMANTICS_RESULT]",
        lambda text: text.replace(
            '[ "$LOCK_SEMANTICS_RESULT" != "success" ]',
            '[ "$LOCK_SEMANTICS_RESULT" = "failure" ]',
            1,
        ),
    ),
    (
        # The fail-open shape: the guard still reads every result, still logs,
        # and still reports the required check green.
        "make-the-guard-exit-zero",
        "aggregate-blocks-on-failure",
        lambda text: text.replace("            exit 1\n", "            exit 0\n", 1),
    ),
    (
        # The subtler fail-open: every comparison string survives, so the
        # per-variable family stays satisfied, but only agentbundle blocks —
        # credbroker and lock-semantics merely log. Replacing the whole guard
        # block matters: substituting only the `if` line would leave the
        # original `exit 1` body attached to the second branch, and the mutant
        # would still block on all three.
        "split-the-guard-so-only-one-job-blocks",
        "aggregate-blocks-on-failure",
        lambda text: text.replace(
            '          if [ "$AGENTBUNDLE_RESULT" != "success" ]'
            ' || [ "$CREDBROKER_RESULT" != "success" ]'
            ' || [ "$LOCK_SEMANTICS_RESULT" != "success" ]; then\n'
            '            echo "Windows suites failed: agentbundle='
            "$AGENTBUNDLE_RESULT credbroker=$CREDBROKER_RESULT "
            'lock-semantics=$LOCK_SEMANTICS_RESULT" >&2\n'
            "            exit 1\n"
            "          fi\n",
            '          if [ "$AGENTBUNDLE_RESULT" != "success" ]; then\n'
            '            echo "agentbundle failed" >&2\n'
            "            exit 1\n"
            "          fi\n"
            '          if [ "$CREDBROKER_RESULT" != "success" ]'
            ' || [ "$LOCK_SEMANTICS_RESULT" != "success" ]; then\n'
            '            echo "credbroker/lock-semantics failed (advisory)" >&2\n'
            "          fi\n",
            1,
        ),
    ),
]


def _family(label: str) -> str:
    """Collapse repeated indexed assertions into one mutation family."""
    return re.sub(r"\[.*\]$", "[*]", label)


def self_test() -> int:
    """Prove the real baseline and every evaluated assertion family."""
    failures: list[str] = []
    good = _baseline()
    evaluated: list[str] = []
    baseline_violations = audit(good, evaluated)
    if baseline_violations:
        failures.append(f"baseline should be clean, got {baseline_violations}")

    for mutation_id, expected, transform in _MUTATIONS:
        mutated = transform(good)
        if mutated == good:
            failures.append(f"{mutation_id}: transform was a no-op — proves nothing")
            continue
        got = audit(mutated)
        if expected not in got:
            failures.append(f"{mutation_id}: expected {expected!r}, got {got}")

    covered = {_family(expected) for _, expected, _ in _MUTATIONS}
    uncovered = sorted({_family(label) for label in evaluated} - covered)
    if uncovered:
        failures.append(f"assertion families evaluated but unmutated: {uncovered}")

    if failures:
        print(f"✖ self-test: {len(failures)} problem(s):", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1
    print(
        f"✓ self-test: baseline clean; {len(_MUTATIONS)} mutations each caught; "
        f"every one of {len(covered)} assertion families has ≥1 mutation"
    )
    return 0


def main(argv: list[str]) -> int:
    """Run the harness, then audit the repository workflow."""
    if "--self-test" in argv:
        return self_test()
    if self_test() != 0:
        return 1

    violations = audit(_baseline())
    if violations:
        print(
            f"✖ build-check-windows.yml: {len(violations)} posture violation(s):",
            file=sys.stderr,
        )
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1
    print("✓ build-check-windows.yml posture OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
