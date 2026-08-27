#!/usr/bin/env python3
"""Posture test for ``.github/workflows/ci-security.yml``.

Security-load-bearing invariants:

* pull-request and push triggers only; never ``pull_request_target``;
* top-level ``contents: read`` and no job-level permission escalation;
* full-history checkout for the gitleaks range scan;
* no Actions expression interpolation in the gitleaks shell body;
* ``--redact`` on every gitleaks detect invocation;
* checksum verification before every binary archive extraction; and
* pull-request-only concurrency cancellation with unique non-PR groups.

The mutation matrix runs on every invocation.  It uses the real workflow as its
baseline, rejects no-op transforms, expects a specific label from each mutant,
and covers every assertion family evaluated by the clean baseline.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import yaml

# Windows cp1252 guard — the parent gate does not force UTF-8 for child Python.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci-security.yml"
EXPECTED_GROUP = (
    "ci-security-${{ github.event_name == 'pull_request' && github.ref || "
    "github.run_id }}"
)

Mutation = tuple[str, str, Callable[[str], str]]


def _steps(jobs: object) -> Iterable[tuple[str, dict[Any, Any]]]:
    """Yield mapping-shaped steps with their owning job name."""
    if not isinstance(jobs, dict):
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            continue
        for step in steps:
            if isinstance(step, dict):
                yield str(job_name), step


def _checksum_precedes_extract(run_body: str) -> bool:
    """Return whether a checksum command occurs before the first tar extract."""
    extract_positions = [
        position
        for marker in ("tar xz", "tar xzf")
        if (position := run_body.find(marker)) != -1
    ]
    if not extract_positions:
        return True
    extract_at = min(extract_positions)
    checksum_positions = [
        position
        for marker in ("sha256sum", "shasum")
        if (position := run_body.find(marker)) != -1
    ]
    return bool(checksum_positions) and min(checksum_positions) < extract_at


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

    try:
        loaded: Any = yaml.safe_load(text)
    except yaml.YAMLError:
        check("yaml-parses", False)
        return violations
    check("yaml-parses", isinstance(loaded, dict))
    if not isinstance(loaded, dict):
        return violations
    doc: dict[Any, Any] = loaded

    # PyYAML 1.1 resolves the bareword ``on`` as boolean True.
    triggers = doc.get("on", doc.get(True))
    check("triggers-mapping", isinstance(triggers, dict))
    if isinstance(triggers, dict):
        check(
            "triggers-required",
            "pull_request" in triggers and "push" in triggers,
        )
        check(
            "trigger-forbidden[pull_request_target]",
            "pull_request_target" not in triggers,
        )

    check("permissions-read", doc.get("permissions") == {"contents": "read"})

    jobs = doc.get("jobs")
    check("jobs-present", isinstance(jobs, dict) and bool(jobs))
    check(
        "jobs-mapping",
        isinstance(jobs, dict)
        and bool(jobs)
        and all(isinstance(job, dict) for job in jobs.values()),
    )
    if isinstance(jobs, dict):
        for job_name, job in jobs.items():
            if isinstance(job, dict):
                check(
                    f"job-steps-list[{job_name}]",
                    isinstance(job.get("steps", []), list),
                )
                check(
                    f"job-permissions[{job_name}]",
                    job.get("permissions") is None,
                )

    concurrency = doc.get("concurrency")
    concurrency = concurrency if isinstance(concurrency, dict) else {}
    check("concurrency-group", concurrency.get("group") == EXPECTED_GROUP)
    cancel = str(concurrency.get("cancel-in-progress", ""))
    check("concurrency-cancel", "pull_request" in cancel)

    secret_job = jobs.get("secret-scan") if isinstance(jobs, dict) else None
    check("secret-job-present", isinstance(secret_job, dict))
    secret_steps = (
        secret_job.get("steps", []) if isinstance(secret_job, dict) else []
    )
    secret_steps = secret_steps if isinstance(secret_steps, list) else []

    checkout_steps = [
        step
        for step in secret_steps
        if isinstance(step, dict) and "checkout" in str(step.get("uses", ""))
    ]
    check("checkout-present", bool(checkout_steps))
    for index, step in enumerate(checkout_steps):
        with_block = step.get("with")
        fetch_depth = with_block.get("fetch-depth") if isinstance(with_block, dict) else None
        check(f"checkout-depth[{index}]", fetch_depth == 0)

    gitleaks_steps = [
        step
        for step in secret_steps
        if isinstance(step, dict)
        and "gitleaks" in str(step.get("run", "")).lower()
        and "detect" in str(step.get("run", "")).lower()
    ]
    check("gitleaks-step-present", bool(gitleaks_steps))
    for index, step in enumerate(gitleaks_steps):
        run_body = str(step.get("run", ""))
        check(f"gitleaks-no-expression[{index}]", "${{" not in run_body)
        check(f"gitleaks-redact[{index}]", "--redact" in run_body)

    install_steps = [
        step
        for _job_name, step in _steps(jobs)
        if "tar xz" in str(step.get("run", ""))
        or "tar xzf" in str(step.get("run", ""))
    ]
    for index, step in enumerate(install_steps):
        name = str(step.get("name", index))
        check(
            f"binary-checksum-before-extract[{name}]",
            _checksum_precedes_extract(str(step.get("run", ""))),
        )

    return violations


def _baseline() -> str:
    """Return the real workflow, or the empty missing-file sentinel."""
    if WORKFLOW.is_file():
        return WORKFLOW.read_text(encoding="utf-8")
    return ""


_MUTATIONS: list[Mutation] = [
    ("remove-workflow-file", "workflow-file-present", lambda _text: ""),
    ("break-yaml", "yaml-parses", lambda _text: "[unterminated\n"),
    (
        "replace-trigger-map-with-list",
        "triggers-mapping",
        lambda text: text.replace("on:\n", "on: []\nlegacy-on:\n", 1),
    ),
    (
        "drop-push-trigger",
        "triggers-required",
        lambda text: text.replace("  push:\n", "  publish:\n", 1),
    ),
    (
        "add-pull-request-target",
        "trigger-forbidden[pull_request_target]",
        lambda text: text.replace(
            "  pull_request:\n    branches: [main]\n",
            "  pull_request:\n    branches: [main]\n"
            "  pull_request_target:\n    branches: [main]\n",
            1,
        ),
    ),
    (
        "widen-top-level-permissions",
        "permissions-read",
        lambda text: text.replace("  contents: read\n", "  contents: write\n", 1),
    ),
    (
        "remove-jobs-map",
        "jobs-present",
        lambda text: text.replace("jobs:\n", "disabled-jobs:\n", 1),
    ),
    (
        "add-malformed-job",
        "jobs-mapping",
        lambda text: text.replace("jobs:\n", "jobs:\n  malformed: true\n", 1),
    ),
    (
        "add-job-with-malformed-steps",
        "job-steps-list[malformed]",
        lambda text: text.replace(
            "jobs:\n", "jobs:\n  malformed:\n    steps: true\n", 1
        ),
    ),
    (
        "add-job-permission-escalation",
        "job-permissions[secret-scan]",
        lambda text: text.replace(
            "  secret-scan:\n",
            "  secret-scan:\n    permissions:\n      contents: write\n",
            1,
        ),
    ),
    (
        "make-concurrency-group-per-ref-only",
        "concurrency-group",
        lambda text: text.replace(EXPECTED_GROUP, "ci-security-${{ github.ref }}", 1),
    ),
    (
        "cancel-non-pr-runs",
        "concurrency-cancel",
        lambda text: text.replace(
            "cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
            "cancel-in-progress: true",
            1,
        ),
    ),
    (
        "rename-secret-scan-job",
        "secret-job-present",
        lambda text: text.replace("  secret-scan:\n", "  secrets-scan:\n", 1),
    ),
    (
        "remove-secret-scan-checkout",
        "checkout-present",
        lambda text: text.replace("actions/checkout@", "actions/source-copy@", 1),
    ),
    (
        "shallow-secret-scan-checkout",
        "checkout-depth[0]",
        lambda text: text.replace("          fetch-depth: 0\n", "          fetch-depth: 1\n", 1),
    ),
    (
        "remove-gitleaks-detect-step",
        "gitleaks-step-present",
        lambda text: text.replace("gitleaks detect", "gitleaks scan"),
    ),
    (
        "interpolate-context-in-gitleaks-shell",
        "gitleaks-no-expression[0]",
        lambda text: text.replace(
            "          ZEROS=",
            "          echo '${{ github.ref }}' >/dev/null\n          ZEROS=",
            1,
        ),
    ),
    (
        "remove-gitleaks-redaction",
        "gitleaks-redact[0]",
        lambda text: text.replace("--redact", "--no-redact"),
    ),
    (
        "move-first-binary-checksum-after-extract",
        "binary-checksum-before-extract[Install gitleaks v8.30.1]",
        lambda text: text.replace(
            "          echo \"551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  gl.tar.gz\" | sha256sum -c\n"
            "          tar xzf gl.tar.gz -C /usr/local/bin gitleaks\n",
            "          tar xzf gl.tar.gz -C /usr/local/bin gitleaks\n"
            "          echo \"551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb  gl.tar.gz\" | sha256sum -c\n",
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
        print(f"✖ ci-security.yml: {len(violations)} posture violation(s):", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1
    print("✓ ci-security.yml posture OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
