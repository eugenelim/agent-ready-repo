#!/usr/bin/env python3
"""Posture test for ``.github/workflows/codeql.yml``.

The workflow supplies ADR-0017's interprocedural taint lens. This checker pins
only the security-extended query suite, the split between the read-only default
floor and the analyzer's elevated grant, both ``paths-ignore`` surfaces (the
trigger-level one and the analysis-config one, the latter as an exhaustive list
so a widening entry cannot silently exempt everything), the presence of the
analyze step that turns extraction into an uploaded result, Python language
containment, and the literal concurrency group and cancellation expressions.
Action SHA pinning remains zizmor-owned.

The concurrency group is pinned as a literal, not as a property: AC12 of
spec/ci-gate-parallelization requires PR runs to share a ref group while every
non-PR run keys on ``github.run_id``, and a substring test for ``github.ref``
would accept the bare-ref form that ADR-0086 lines 111-117 tells the next
author not to copy.

Recognition boundary, stated because a check that silently fails to enumerate
is worse than one that admits its edge: job headers and ``permissions`` blocks
are recognized only in block style — a bare ``  <name>:`` header line and a
``    permissions:`` mapping. A job written with a flow mapping
(``permissions: {security-events: write}``), a ``write-all`` scalar, or a header
carrying a trailing comment is not enumerated, so
``security-events-only-analyze`` is a claim about block-style jobs, not about
every spelling YAML admits. Widening it is registered follow-up work, not a
claim made here.

Known limitation: CodeQL is advisory until the repository owner makes it a
required branch-protection check. This posture test protects that advisory
signal; it does not claim to make the signal merge-blocking.

The real workflow is the self-test baseline. Every invocation runs a mutation
matrix that rejects no-op transforms, expects a specific label from each
mutant, and covers every assertion family evaluated by the clean baseline.
Pure stdlib, as required for new ``tools/`` additions.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "codeql.yml"
CONFIG_PATH_IGNORES = (
    "**/tests/**",
    "**/test_*.py",
    "**/test-*.py",
)
# Pinned as the literal expression, matching the ci-security sibling. AC12's
# shape is "PR runs share a ref group; every non-PR run is unique", which a
# property test cannot express.
EXPECTED_GROUP = (
    "codeql-${{ github.event_name == 'pull_request' && github.ref || "
    "github.run_id }}"
)
# Pinned by equality for the same reason as the group: a substring test for
# "pull_request" accepts the inverted `!=` form, which stops PR runs superseding
# one another while reading as if it were asserted.
EXPECTED_CANCEL = "${{ github.event_name == 'pull_request' }}"

Mutation = tuple[str, str, Callable[[str], str]]


def _indent(line: str) -> int:
    """Return a line's leading-space count."""
    return len(line) - len(line.lstrip(" "))


def _named_block(text: str, key: str, indent: int) -> str:
    """Return the body of one mapping key at ``indent``, or ``""``."""
    lines = text.splitlines(keepends=True)
    header = " " * indent + key + ":"
    for index, line in enumerate(lines):
        if line.rstrip("\n").rstrip() != header:
            continue
        body: list[str] = []
        for following in lines[index + 1 :]:
            if following.strip() and _indent(following) <= indent:
                break
            body.append(following)
        return "".join(body)
    return ""


def _child_blocks(block: str, indent: int) -> dict[str, str]:
    """Return direct child mapping blocks keyed by their unquoted names."""
    lines = block.splitlines(keepends=True)
    starts: list[tuple[int, str]] = []
    pattern = re.compile(rf"^ {{{indent}}}([a-zA-Z0-9_-]+):\s*$")
    for index, line in enumerate(lines):
        if match := pattern.match(line):
            starts.append((index, match.group(1)))
    result: dict[str, str] = {}
    for position, (start, name) in enumerate(starts):
        stop = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        result[name] = "".join(lines[start + 1 : stop])
    return result


def _mapping(block: str, indent: int) -> dict[str, str]:
    """Parse scalar entries directly beneath one known mapping block."""
    result: dict[str, str] = {}
    pattern = re.compile(rf"^ {{{indent}}}([a-zA-Z0-9_-]+):\s*([^#\n]+?)\s*$")
    for line in block.splitlines():
        if match := pattern.match(line):
            result[match.group(1)] = match.group(2).strip().strip("'\"")
    return result


def _sequence(block: str, key: str, key_indent: int) -> list[str]:
    """Return one block-style sequence beneath a known key."""
    lines = block.splitlines()
    header = " " * key_indent + key + ":"
    for index, line in enumerate(lines):
        if line.rstrip() != header:
            continue
        values: list[str] = []
        for following in lines[index + 1 :]:
            if following.strip() and _indent(following) <= key_indent:
                break
            item = re.match(r"^\s+-\s+(.+?)\s*$", following)
            if item:
                values.append(item.group(1).strip().strip("'\""))
        return values
    return []


def _steps(job_block: str) -> list[str]:
    """Return step-shaped chunks from one job block."""
    lines = job_block.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.startswith("      - ")]
    if not starts:
        return []
    return [
        "".join(lines[start:stop])
        for start, stop in zip(starts, starts[1:] + [len(lines)], strict=True)
    ]


def _field_tokens(block: str, key: str, indent: int) -> set[str]:
    """Normalize a scalar, inline-list, or block-list action input."""
    pattern = re.compile(rf"^ {{{indent}}}{re.escape(key)}:\s*(.*?)\s*$", re.MULTILINE)
    match = pattern.search(block)
    if match is None:
        return set()
    value = match.group(1).strip()
    if value:
        return {
            token
            for token in re.split(r"[\s,\[\]'\"]+", value)
            if token
        }
    return set(_sequence(block, key, indent))


def _block_scalar(block: str, key: str, indent: int) -> str:
    """Return a literal block scalar's indented body."""
    lines = block.splitlines(keepends=True)
    pattern = re.compile(rf"^ {{{indent}}}{re.escape(key)}:\s*[|>]\s*$")
    for index, line in enumerate(lines):
        if not pattern.match(line):
            continue
        body: list[str] = []
        for following in lines[index + 1 :]:
            if following.strip() and _indent(following) <= indent:
                break
            body.append(following)
        return "".join(body)
    return ""


def audit(text: str, evaluated: list[str] | None = None) -> list[str]:
    """Return stable violation labels for one CodeQL workflow text."""
    violations: list[str] = []

    def check(label: str, condition: bool) -> None:
        if evaluated is not None:
            evaluated.append(label)
        if not condition:
            violations.append(label)

    check("workflow-file-present", bool(text))
    if not text:
        return violations

    on_block = _named_block(text, "on", 0)
    check("on-block-present", bool(on_block))
    trigger_blocks = _child_blocks(on_block, 2)
    for trigger_name in ("pull_request", "push"):
        ignored = _sequence(trigger_blocks.get(trigger_name, ""), "paths-ignore", 4)
        check(
            f"trigger-docs-path-ignore[{trigger_name}]",
            "docs/**" in ignored,
        )

    permissions_block = _named_block(text, "permissions", 0)
    check(
        "permissions-read",
        _mapping(permissions_block, 2) == {"contents": "read"},
    )

    jobs_block = _named_block(text, "jobs", 0)
    check("jobs-block-present", bool(jobs_block))
    jobs = _child_blocks(jobs_block, 2)
    analyze = jobs.get("analyze", "")
    check("analyze-job-present", bool(analyze))

    security_writers = [
        job_name
        for job_name, job_block in jobs.items()
        if _mapping(_named_block(job_block, "permissions", 4), 6).get(
            "security-events"
        )
        == "write"
    ]
    check("security-events-only-analyze", security_writers == ["analyze"])

    init_steps = [
        step
        for step in _steps(analyze)
        if re.search(r"^        uses: github/codeql-action/init@", step, re.MULTILINE)
    ]
    check("init-step-present", len(init_steps) == 1)
    if init_steps:
        init_step = init_steps[0]
        check(
            "languages-contain-python",
            "python" in _field_tokens(init_step, "languages", 10),
        )
        queries = _mapping(init_step, 10).get("queries")
        check("queries-security-extended", queries == "security-extended")

        config = _block_scalar(init_step, "config", 10)
        check("config-block-present", bool(config))
        ignored = _sequence(config, "paths-ignore", 12)
        for path in CONFIG_PATH_IGNORES:
            check(f"config-path-ignore[{path}]", path in ignored)
        # Presence alone is not enough: one added `- '**'` exempts the whole
        # repository while every per-glob check above still passes, which would
        # zero the analysis and leave this gate green.
        check(
            "config-path-ignore-exhaustive",
            set(ignored) == set(CONFIG_PATH_IGNORES),
        )

    analyze_steps = [
        step
        for step in _steps(analyze)
        if re.search(r"^        uses: github/codeql-action/analyze@", step, re.MULTILINE)
    ]
    # Initialization extracts; only the analyze step uploads a result. Without
    # this, a workflow that inits and never analyzes reports no violation.
    check("analyze-step-present", len(analyze_steps) == 1)

    concurrency_block = _named_block(text, "concurrency", 0)
    check("concurrency-block-present", bool(concurrency_block))
    concurrency = _mapping(concurrency_block, 2)
    check("concurrency-group", concurrency.get("group") == EXPECTED_GROUP)
    check(
        "concurrency-cancel",
        concurrency.get("cancel-in-progress") == EXPECTED_CANCEL,
    )

    return violations


def _baseline() -> str:
    """Return the real workflow, or the empty missing-file sentinel."""
    if WORKFLOW.is_file():
        return WORKFLOW.read_text(encoding="utf-8")
    return ""


_MUTATIONS: list[Mutation] = [
    ("remove-workflow-file", "workflow-file-present", lambda _text: ""),
    (
        "rename-on-block",
        "on-block-present",
        lambda text: text.replace("on:\n", "triggers:\n", 1),
    ),
    (
        "drop-pr-docs-ignore",
        "trigger-docs-path-ignore[pull_request]",
        lambda text: text.replace('      - "docs/**"\n', "", 1),
    ),
    (
        "drop-push-docs-ignore",
        "trigger-docs-path-ignore[push]",
        lambda text: text.replace(
            '  push:\n    branches: [main]\n    paths-ignore:\n      - "docs/**"\n',
            "  push:\n    branches: [main]\n    paths-ignore:\n",
            1,
        ),
    ),
    (
        "widen-top-level-permissions",
        "permissions-read",
        lambda text: text.replace("  contents: read\n", "  contents: write\n", 1),
    ),
    (
        "rename-jobs-block",
        "jobs-block-present",
        lambda text: text.replace("jobs:\n", "disabled-jobs:\n", 1),
    ),
    (
        "rename-analyze-job",
        "analyze-job-present",
        lambda text: text.replace("  analyze:\n", "  analysis:\n", 1),
    ),
    (
        "grant-security-events-to-another-job",
        "security-events-only-analyze",
        lambda text: text.replace(
            "jobs:\n",
            "jobs:\n  advisory:\n    permissions:\n      security-events: write\n",
            1,
        ),
    ),
    (
        "remove-init-step",
        "init-step-present",
        lambda text: text.replace("github/codeql-action/init@", "github/codeql-action/setup@", 1),
    ),
    (
        "drop-python-language",
        "languages-contain-python",
        lambda text: text.replace("          languages: python\n", "          languages: ruby\n", 1),
    ),
    (
        "drop-security-extended-queries",
        "queries-security-extended",
        lambda text: text.replace(
            "          queries: security-extended\n",
            "          queries: security-and-quality\n",
            1,
        ),
    ),
    (
        "remove-config-block",
        "config-block-present",
        lambda text: text.replace("          config: |\n", "          configuration: |\n", 1),
    ),
    (
        "drop-tests-tree-ignore",
        "config-path-ignore[**/tests/**]",
        lambda text: text.replace("              - '**/tests/**'\n", "", 1),
    ),
    (
        "drop-test-underscore-ignore",
        "config-path-ignore[**/test_*.py]",
        lambda text: text.replace("              - '**/test_*.py'\n", "", 1),
    ),
    (
        "drop-test-hyphen-ignore",
        "config-path-ignore[**/test-*.py]",
        lambda text: text.replace("              - '**/test-*.py'\n", "", 1),
    ),
    (
        "widen-config-path-ignores",
        "config-path-ignore-exhaustive",
        lambda text: text.replace(
            "              - '**/test-*.py'\n",
            "              - '**/test-*.py'\n              - '**'\n",
            1,
        ),
    ),
    (
        "remove-analyze-step",
        "analyze-step-present",
        lambda text: text.replace(
            "github/codeql-action/analyze@", "github/codeql-action/upload@", 1
        ),
    ),
    (
        "remove-concurrency-block",
        "concurrency-block-present",
        lambda text: text.replace("concurrency:\n", "run-concurrency:\n", 1),
    ),
    (
        "make-concurrency-group-constant",
        "concurrency-group",
        lambda text: re.sub(
            r"^  group: .*github\.ref.*$",
            "  group: codeql",
            text,
            count=1,
            flags=re.MULTILINE,
        ),
    ),
    (
        # The specific regression ADR-0086 lines 111-117 warns about: a bare-ref
        # group lets a third queued non-PR run evict the pending one.
        "make-concurrency-group-bare-ref",
        "concurrency-group",
        lambda text: text.replace(EXPECTED_GROUP, "codeql-${{ github.ref }}", 1),
    ),
    (
        "cancel-non-pr-runs",
        "concurrency-cancel",
        lambda text: text.replace(
            "  cancel-in-progress: ${{ github.event_name == 'pull_request' }}\n",
            "  cancel-in-progress: true\n",
            1,
        ),
    ),
    (
        # A one-character inversion the previous substring test walked past: PR
        # runs stop superseding one another while the line still names the
        # trigger the assertion looked for.
        "invert-cancel-condition",
        "concurrency-cancel",
        lambda text: text.replace(EXPECTED_CANCEL, "${{ github.event_name != 'pull_request' }}", 1),
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
        print(f"✖ codeql.yml: {len(violations)} posture violation(s):", file=sys.stderr)
        for violation in violations:
            print(f"  - {violation}", file=sys.stderr)
        return 1
    print("✓ codeql.yml posture OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
