#!/usr/bin/env python3
"""Pin and mutation-test the split Windows workflow's blocking topology.

Two properties are asserted about the aggregate: it reads every work job's
result, and its guard exits non-zero when one of them is not `success`. The
guard must be the run body's first statement, its condition must equal
`GUARD_CONDITION` exactly, and the failing `exit 1` must be reached without
crossing an `else`/`elif` branch, a nested opener, or a subshell wrapper.

The aggregate's guard STEP is asserted too: `aggregate-step-unconditional`
refuses a `continue-on-error` or an `if:` on it, in either key position, because
either defeats the required check while the guard body stays perfectly correct.

Deliberately not asserted, and so not claimed: a JOB-level `continue-on-error`
on `build-check-windows` itself, and anything outside the aggregate job. Both
are registered.

The blocking property is additionally checked against bash rather than only
modelled, because a text model of a shell is not the shell: see
``_differential_failures``. That seam is ported from
``tools/test-build-check-workflow.py``, which found the same class by execution.
"""

from __future__ import annotations

import re
import sys
from collections.abc import Callable
from pathlib import Path

import posture_harness

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
# The guard body this harness owns. It is built here, pinned against the
# workflow by equality, and it — never workflow text — is what reaches `bash`.
# Handing file text to a shell would let a one-file PR run arbitrary commands on
# any machine executing `make build-check`; the sibling avoids that by
# construction and so does this.
GUARD_CONDITION = (
    "if "
    + " || ".join(f'[ "${variable}" != "success" ]' for variable in RESULT_VARIABLES)
    + "; then"
)
GUARD_FAIL_ECHO = (
    '  echo "Windows suites failed: agentbundle=$AGENTBUNDLE_RESULT '
    'credbroker=$CREDBROKER_RESULT lock-semantics=$LOCK_SEMANTICS_RESULT" >&2'
)
GUARD_FINAL_ECHO = 'echo "Windows suites passed"'
_GUARD_BASE = "\n".join(
    [GUARD_CONDITION, GUARD_FAIL_ECHO, "  exit 1", "fi", GUARD_FINAL_ECHO]
)


GUARD_RUN_MARKER = "        run: |\n"
# A statement that opens a block bash may never enter. An `exit 1` beneath one
# of these is conditional on something this checker does not model, so it is
# refused rather than guessed at.
_BLOCK_OPENERS = frozenset(
    {"if", "case", "while", "until", "for", "select", "else", "elif"}
)


def _bash_path() -> str | None:
    """Return the bash interpreter, or None where the platform has none."""
    import shutil

    return shutil.which("bash")


def _guard_body(aggregate: str) -> str:
    """Return the aggregate guard step's run body, dedented, or the empty string."""
    if GUARD_RUN_MARKER not in aggregate:
        return ""
    tail = aggregate[aggregate.index(GUARD_RUN_MARKER) + len(GUARD_RUN_MARKER) :]
    body: list[str] = []
    for line in tail.splitlines():
        if line.strip() and not line.startswith("          "):
            break
        body.append(line[10:])
    return "\n".join(body).rstrip("\n")


def _guard_blocks_on_failure(aggregate: str) -> bool:
    """Return whether one guard makes every work job's failure exit non-zero.

    The comparisons alone prove only that the aggregate reads the results, and a
    first-match scan proves only that some guard exits. Splitting the guard into
    one blocking `if` plus two advisory ones satisfied both, leaving two of three
    Windows suites non-blocking behind the required check.

    Three structural requirements, the first two fail-closed, each answering a
    body bash takes green that a looser reading accepted: the guard is the run
    body's first statement (anything before it can `exit 0`, reassign a result,
    or open a wrapper); its condition equals `GUARD_CONDITION` exactly; and the
    `exit 1` is reached without crossing a nested opener, an `else`/`elif`
    branch, or a subshell.

    The condition is compared by equality, not by containment of the three
    comparisons: substring containment accepted `] && [` in place of `] || [`, a
    two-character edit that leaves the required Windows check green over any one
    failed suite. Same treatment the concurrency literals get in the siblings.

    A leading `set -euo pipefail`, comment, or line continuation therefore fails
    this check. That is the documented rule, not an oversight — the guard is
    then not the first statement — and it errs toward reporting a blocking guard
    as unproven rather than the reverse.

    The first two requirements are fail-closed. The third, the reachability
    scan, is permissive for a line it does not recognize: it passes over such a
    line and keeps looking for `exit 1`. A heredoc'd exit and a backslash
    continuation that swallows the next line are both unmodelled and would be
    accepted; they are not claimed.
    """
    body = [line for line in _guard_body(aggregate).splitlines() if line.strip()]
    if not body:
        return False
    if body[0].strip() != GUARD_CONDITION:
        return False
    for line in body[1:]:
        stripped = line.strip()
        if stripped == "fi":
            return False
        if stripped == "exit 1":
            return True
        if stripped.startswith(("(", "{")):
            return False
        # Compared as a token, not a prefix: `else true`, `else # advisory`, and
        # a tab-separated `elif`/`if`/`while`/`case` all walked past a
        # spelling-specific test and put the exit on a branch bash need not take.
        head = stripped.split(maxsplit=1)[0].rstrip(";")
        if head in _BLOCK_OPENERS:
            return False
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
    # The guard body can be perfectly correct and still not block: a step-level
    # `continue-on-error: true` or `if:` on the step that runs it leaves every
    # assertion above satisfied while the required check reports success over
    # three failed Windows suites.
    # The WHOLE step, not just what precedes `run:`. YAML mapping keys are
    # unordered, so `continue-on-error: true` written under the final echo has
    # identical effect and the earlier slice never looked there — while both
    # mutations happened to insert above `run:`, the one position it did look at.
    # The 8-space anchor cannot match the run body, which is indented 10.
    guard_step = ""
    if GUARD_RUN_MARKER in aggregate:
        marker = aggregate.index(GUARD_RUN_MARKER)
        head = aggregate[:marker]
        if "      - " in head:
            start = head.rindex("      - ")
            stop = aggregate[marker:].find("\n      - ")
            guard_step = (
                aggregate[start:] if stop == -1 else aggregate[start : marker + stop]
            )
    check(
        "aggregate-step-unconditional",
        bool(guard_step)
        # Optional quote: `"continue-on-error": true` resolves to the same active
        # key. The ci-security sibling reads the parsed step dict and is immune;
        # this one reads text, so it has to admit the spelling explicitly.
        and not re.search(
            r"^        [\"']?(?:continue-on-error|if)[\"']?:", guard_step, re.M
        ),
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
        "bump-agentbundle-timeout-past-the-pin",
        "bounded-timeout[agentbundle-windows]",
        lambda text: text.replace("    timeout-minutes: 15\n", "    timeout-minutes: 16\n", 1),
    ),
    (
        "add-args-to-credbroker-suite",
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
        "make-the-guard-step-advisory",
        "aggregate-step-unconditional",
        lambda text: text.replace(
            "      - name: Require all Windows suites\n",
            "      - name: Require all Windows suites\n        continue-on-error: true\n",
            1,
        ),
    ),
    (
        # Deliberately AFTER the run block: key order is irrelevant to Actions,
        # and this is the position the previous slice could not see.
        "gate-the-guard-step-off-after-the-run-block",
        "aggregate-step-unconditional",
        lambda text: posture_harness.replace_once(
            text,
            '          echo "Windows suites passed"\n',
            '          echo "Windows suites passed"\n        if: ${{ false }}\n',
            WORKFLOW.name,
        ),
    ),
    (
        "quote-the-guard-step-key",
        "aggregate-step-unconditional",
        lambda text: posture_harness.replace_once(
            text,
            "      - name: Require all Windows suites\n",
            '      - name: Require all Windows suites\n        "continue-on-error": true\n',
            WORKFLOW.name,
        ),
    ),
    (
        # Exercises the bounded branch of the step slice, dead while the guard is
        # the aggregate's only step: appends a trailing step so `stop` is no
        # longer -1, and defeats the guard from the post-run position.
        "add-a-trailing-step-and-gate-the-guard-off",
        "aggregate-step-unconditional",
        lambda text: posture_harness.replace_once(
            text,
            '          echo "Windows suites passed"\n',
            '          echo "Windows suites passed"\n        if: ${{ false }}\n'
            "      - name: Trailing step\n        run: echo trailing\n",
            WORKFLOW.name,
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


# ── Differential check: this file's model of bash, against bash ──────────────
#
# `aggregate-blocks-on-failure` encodes a BELIEF about what a shell does with a
# guard body. The mutation matrix proves the assertion fires; it cannot prove
# the belief is true. So for the one body whose behaviour decides the required
# Windows status check, ask bash directly.
#
# The property is an implication, not an equality: if bash exits 0 with a suite
# reported `failure`, `audit` MUST reject. The converse is not required —
# rejecting a body bash would also fail is merely conservative. That asymmetry
# is what makes this a safety check rather than a brittle equivalence test.
_EXIT_LINE = "  exit 1"

_DIFFERENTIAL_VARIANTS: list[tuple[str, Callable[[str], str]]] = [
    ("baseline", lambda body: body),
    ("exit-0-prefix", lambda body: f"exit 0\n{body}"),
    ("bare-exit-prefix", lambda body: f"exit\n{body}"),
    ("exit-000-prefix", lambda body: f"exit 000\n{body}"),
    (
        "reassign-every-result",
        lambda body: "".join(f"{name}=success\n" for name in RESULT_VARIABLES) + body,
    ),
    (
        "default-if-unset",
        lambda body: "".join(
            f"{name}=${{{name}:+success}}\n" for name in RESULT_VARIABLES
        )
        + body,
    ),
    (
        "unreachable-nested-exit",
        lambda body: body.replace(
            _EXIT_LINE, "  if false; then\n    exit 1\n  fi", 1
        ),
    ),
    (
        "unmatched-case-arm-exit",
        lambda body: body.replace(
            _EXIT_LINE, "  case unmatched in matched)\n    exit 1\n  ;;\n  esac", 1
        ),
    ),
    (
        # The advisory echo takes the `then` arm and the exit moves to `else`, so
        # bash never reaches it with a suite failed.
        "else-branch-exit",
        lambda body: body.replace(
            f"{GUARD_FAIL_ECHO}\n{_EXIT_LINE}",
            f"{GUARD_FAIL_ECHO}\nelse\n  exit 1",
            1,
        ),
    ),
    (
        # Proves the condition-equality pin: with `&&`, the first conjunct is
        # false for a succeeding suite, so the guard is skipped and bash exits 0.
        # Nothing else in the matrix perturbs the condition line.
        "or-to-and",
        lambda body: body.replace("] || [", "] && ["),
    ),
    (
        "subshell-or-true",
        lambda body: body.replace("if [", "( if [", 1).replace(
            "\nfi", "\nfi ) || true", 1
        ),
    ),
]


def _differential_failures() -> list[str]:
    """Guard bodies bash takes green with a suite failed, that `audit` accepts.

    `audit` encodes a BELIEF about what a shell does with the guard. The mutation
    matrix proves the assertion fires; it cannot prove the belief. So ask bash —
    but ask it only about `_GUARD_BASE`, which this module builds from its own
    constants. Workflow text is never executed; it is tied to `_GUARD_BASE` by
    the round-trip assertion below, so drift shows up as a blind harness rather
    than as a shell running whatever a PR put in the file.

    The property is an implication, not an equality: if bash exits 0 with a suite
    reported `failure`, `audit` MUST reject. The converse is not required —
    rejecting a body bash would also fail is merely conservative.
    """
    import os
    import subprocess

    good = _baseline()
    indented = "\n".join(
        f"          {line}".rstrip() for line in _GUARD_BASE.splitlines()
    )
    # Ordered before the bash check on purpose: this is string containment and
    # needs no shell, so a bash-less platform still gets the drift diagnostic.
    if indented not in good:
        return [
            "differential: the constructed guard body is not in "
            f"{WORKFLOW.name} — re-pin GUARD_CONDITION/GUARD_FAIL_ECHO against it"
        ]
    if _bash_path() is None:
        # Announced, never fatal. `build_gate_chain.py build-check` is the shipped
        # make-free Windows contributor entry point, so turning an absent shell
        # into a gate failure would fail a gate it has no business failing — the
        # same call the build-check sibling and assert-sast-chain-reachable make.
        # The success line reports the skip so it cannot read as a pass.
        print(
            "differential: SKIPPED — bash unavailable, shell model unproven",
            file=sys.stderr,
        )
        return []
    # Every result variable is bound: an unset one changes which comparison
    # short-circuits rather than signalling failure. The environment is minimal
    # rather than inherited, so nothing the parent holds reaches the child.
    env = dict.fromkeys(RESULT_VARIABLES, "success")
    env["LOCK_SEMANTICS_RESULT"] = "failure"
    env["PATH"] = os.environ.get("PATH", "")

    out: list[str] = []
    for name, transform in _DIFFERENTIAL_VARIANTS:
        variant = transform(_GUARD_BASE)
        if name != "baseline" and variant == _GUARD_BASE:
            out.append(f"differential[{name}]: transform was a no-op — proves nothing")
            continue
        spliced = good.replace(
            indented,
            "\n".join(f"          {line}".rstrip() for line in variant.splitlines()),
            1,
        )
        accepted = not audit(spliced)
        green = (
            subprocess.run(
                [str(_bash_path()), "-c", variant],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            ).returncode
            == 0
        )
        if name == "baseline":
            # The harness's own premise. If an unmodified guard is green with a
            # suite failed, every verdict below is vacuous.
            if green:
                out.append(
                    "differential[baseline]: the clean guard exits 0 with "
                    "lock-semantics failed — the harness proves nothing"
                )
            if not accepted:
                out.append("differential[baseline]: the clean guard is rejected by audit")
            continue
        if not green:
            # A variant that is never green is never reported green-and-accepted,
            # so it silently stops proving anything — the class the no-op rule
            # catches only for an identical transform.
            out.append(
                f"differential[{name}]: variant is not green under bash "
                "— proves nothing"
            )
            continue
        if accepted:
            out.append(
                f"differential[{name}]: bash exits 0 with lock-semantics failed, "
                "and audit accepts it"
            )
    return out


def self_test() -> int:
    """Prove the baseline, the mutation matrix, and the model against bash."""
    return posture_harness.run(
        workflow=WORKFLOW,
        baseline=_baseline,
        audit=audit,
        mutations=_MUTATIONS,
        extra_failures=_differential_failures,
        extra_summary=lambda: (
            f"{len(_DIFFERENTIAL_VARIANTS) - 1} guard bodies agreed with bash"
            if _bash_path() is not None
            else "differential skipped, bash unavailable"
        ),
    )


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
