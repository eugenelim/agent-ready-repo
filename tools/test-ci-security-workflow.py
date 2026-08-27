#!/usr/bin/env python3
"""Posture test for ``.github/workflows/ci-security.yml``.

Security-load-bearing invariants:

* pull-request and push triggers only; never ``pull_request_target``;
* top-level ``contents: read`` and no job-level ``permissions`` key at all —
  deliberately stricter than "no escalation", because AC12's posture is that a
  job inherits the top-level grant rather than restating it;
* full-history checkout for the gitleaks range scan;
* no Actions expression interpolation in the gitleaks shell body;
* ``--redact`` on every gitleaks detect invocation;
* a checksum command *naming the archive* before *every* archive extraction in
  a step, however the extraction is spelled; and
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


# Short flags a tar extraction can legitimately carry. Membership is checked as
# a set so `--exclude=` on a *create* invocation cannot be mistaken for the `x`
# in an extract cluster.
_TAR_SHORT_FLAGS = frozenset("xzjJfvkOCp")
_CHECKSUM_RE = re.compile(r"\b(?:sha256sum|shasum)\b")
_ARCHIVE_RE = re.compile(r"[\w.@/-]+\.(?:tar\.gz|tar\.xz|tar\.bz2|tgz|tar|zip)\b")


def _is_extraction(line: str) -> bool:
    """Return whether one shell line extracts an archive, however spelled.

    Structural, not substring. The two literal markers this replaced (``tar xz``
    and ``tar xzf``, the second subsumed by the first) matched one spelling, so
    respelling an extraction as ``tar -xzf`` dropped its step out of the audited
    set entirely — losing the assertion rather than failing it.
    """
    tokens = line.split()
    for index, token in enumerate(tokens):
        if token == "unzip":
            return True
        if token == "7z" and tokens[index + 1 : index + 2] in (["x"], ["e"]):
            return True
        if token not in ("tar", "bsdtar"):
            continue
        for candidate in tokens[index + 1 :]:
            if candidate == "--extract":
                return True
            flags = candidate.lstrip("-")
            if flags and set(flags) <= _TAR_SHORT_FLAGS and "x" in flags:
                return True
    return False


def _unverified_archives(run_body: str) -> list[str]:
    """Return archives this step extracts with no prior checksum naming them.

    Every extraction is checked, not just the first, and the checksum has to
    name the archive the extraction consumes — a bare ``sha256sum --version``
    earlier in the body verifies nothing. Deliberately no vacuously-true early
    return: a step with no extraction yields no extraction loop iterations and
    therefore an empty list, without a fail-open branch to reach.
    """
    lines = run_body.splitlines()
    checksum_at: dict[str, int] = {}
    for index, line in enumerate(lines):
        if not _CHECKSUM_RE.search(line):
            continue
        for archive in _ARCHIVE_RE.findall(line):
            checksum_at.setdefault(archive, index)

    unverified: list[str] = []
    for index, line in enumerate(lines):
        if not _is_extraction(line):
            continue
        archives = _ARCHIVE_RE.findall(line)
        if not archives:
            # An extraction naming no archive path cannot be tied to any
            # checksum, so it is reported rather than waved through.
            unverified.append(line.strip())
            continue
        for archive in archives:
            verified_at = checksum_at.get(archive)
            if verified_at is None or verified_at >= index:
                unverified.append(archive)
    return unverified


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
        if any(_is_extraction(line) for line in str(step.get("run", "")).splitlines())
    ]
    # Presence floor, matching `checkout-present` and `gitleaks-step-present`.
    # Without it the whole family can collapse to zero members and the
    # family-coverage rule — which compares evaluated labels against mutated
    # ones — reports nothing, because an unevaluated family is not uncovered.
    check("install-steps-present", bool(install_steps))
    for index, step in enumerate(install_steps):
        # Keyed on the index, not the step name: the name carries the pinned
        # tool version, so a routine bump would silently retarget the label.
        check(
            f"binary-checksum-before-extract[{index}]",
            not _unverified_archives(str(step.get("run", ""))),
        )

    return violations


def _baseline() -> str:
    """Return the real workflow, or the empty missing-file sentinel."""
    if WORKFLOW.is_file():
        return WORKFLOW.read_text(encoding="utf-8")
    return ""


def _checksum_extract_pairs(lines: list[str]) -> list[int]:
    """Return indexes of checksum lines immediately followed by an extraction.

    Every transform below is derived from these pairs rather than from a pinned
    digest or version string, so a routine tool bump cannot turn a mutation into
    a no-op and redden the gate with a message about the harness.
    """
    return [
        index
        for index in range(len(lines) - 1)
        if _CHECKSUM_RE.search(lines[index]) and _is_extraction(lines[index + 1])
    ]


def _swap_first_checksum_and_extract(text: str) -> str:
    """Move the first checksum line to after the extraction it guards."""
    lines = text.splitlines(keepends=True)
    pairs = _checksum_extract_pairs(lines)
    if not pairs:
        return text
    index = pairs[0]
    lines[index], lines[index + 1] = lines[index + 1], lines[index]
    return "".join(lines)


def _misname_first_checksum_archive(text: str) -> str:
    """Point the first checksum at an archive nothing extracts."""
    lines = text.splitlines(keepends=True)
    pairs = _checksum_extract_pairs(lines)
    if not pairs:
        return text
    index = pairs[0]
    lines[index] = _ARCHIVE_RE.sub("unrelated.tar.gz", lines[index], count=1)
    return "".join(lines)


def _respell_second_extraction_unverified(text: str) -> str:
    """Drop the second step's checksum and respell its extraction.

    This is the exact pair of edits the previous literal-marker filter could not
    see: the step left the audited set, so no label failed and no family was
    reported uncovered.
    """
    lines = text.splitlines(keepends=True)
    pairs = _checksum_extract_pairs(lines)
    if len(pairs) < 2:
        return text
    index = pairs[1]
    respelled = lines[index + 1].replace("tar xzf", "tar -xzf", 1)
    return "".join(lines[:index] + [respelled] + lines[index + 2 :])


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
        "binary-checksum-before-extract[0]",
        _swap_first_checksum_and_extract,
    ),
    (
        # Ordering alone is not verification: the checksum has to name the
        # archive the extraction consumes.
        "verify-an-archive-nothing-extracts",
        "binary-checksum-before-extract[0]",
        _misname_first_checksum_archive,
    ),
    (
        "respell-second-extraction-and-drop-its-checksum",
        "binary-checksum-before-extract[1]",
        _respell_second_extraction_unverified,
    ),
    (
        "remove-every-install-extraction",
        "install-steps-present",
        lambda text: text.replace("tar xzf", "tar czf"),
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
