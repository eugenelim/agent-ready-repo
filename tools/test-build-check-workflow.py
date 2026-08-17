#!/usr/bin/env python3
"""Posture test for `.github/workflows/build-check.yml`'s job graph.

# STUB: AC13 — red stub materialised at PLAN per CONVENTIONS § Stub → EXECUTE
handoff.

Pure stdlib, matching `tools/test-build-check-windows-workflow.py`, the repo's only
*wired* posture test. (`tools/test-ci-security-workflow.py` imports PyYAML and is
invoked nowhere.) Staying stdlib is load-bearing: this runs inside the aggregator
job that wears the sole required status check, and a test that can fail on a missing
import is a test someone import-guards under pressure.

## Controls are matched as shell COMMAND WORDS, never as substrings

`docs/knowledge/observations/antipattern/2026-08.jsonl`: *"A test that pins a
security control by substring-matching the source cannot detect that control's
removal... it names where the control is CALLED, not what it DOES... an unmutated
assertion is an unverified one."*

Two earlier drafts of this file broke that rule and were each demonstrated to print
`✓ posture OK` against a workflow that verified nothing:

- draft 1 — every required token supplied by whole-line YAML comments;
- draft 2 — `run: echo "make build-check … SAST_DELEGATED=1 -- disabled"` (no comment
  needed at all), plus trailing `#` comments, `set +e`, un-`pipefail`'d pipelines,
  and `[ "$X" != "success" ] || echo ok` — a comparison with no consequent, which
  lets the aggregator report success with every gate failed.

So: comments are stripped to the first *unquoted* `#`; a control must be the
**command word** of a shell statement (after `!` and any leading `VAR=val`), not a
token anywhere in it; guard statements are checked for their **consequent**, not
just their condition; `set +e` and bare pipelines are rejected on guarded bodies;
and `--self-test` runs a mutation matrix whose id set is derived from the
fully-populated baseline, so the coverage claim is not computed from an empty input.

Exit codes: 0 = pass, 1 = violations (or a self-test failure).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "build-check.yml"
SELF_NAME = "tools/test-build-check-workflow.py"

AGGREGATOR_JOB_ID = "build-check"
AGGREGATOR_NAME = "make build-check"
REQUIRED_WORK_JOBS = ("gate-main", "gate-sast", "gate-export-boundary")

EXPECTED_PYTHON = '"3.11"'
EXPECTED_CONCURRENCY_GROUP = (
    "build-check-${{ github.event_name == 'pull_request' "
    "&& github.ref || github.run_id }}"
)
# AC14(2): assert ZERO skips rather than matching skip REASONS. The three
# tree-shape guards in tools/test_check_artifact_contents.py say
# reason="engine package not present", which matches none of the reason tokens an
# earlier draft grepped for — so that draft's "standing signal" was blind to the
# exact skip it was written to catch. `^SKIPPED` in pytest's -rs summary is
# reason-agnostic and cannot be wrong about a reason nobody anticipated.
SKIP_ASSERT_PATTERN = "^SKIPPED"
_STRICT_SHELL = "set -euo pipefail"
# A control whose exit status is discarded gates nothing. Applied uniformly inside
# _invocation so every assertion inherits it — patching assertions one at a time
# is how three consecutive drafts each left a different one neuterable.
_DISCARDING_TAIL = re.compile(r"\|\||;\s*(true|:)\s*$|&\s*$")
_DRY_RUN_FLAGS = frozenset({"-n", "--dry-run", "--just-print", "--recon"})
# A guard body is a STRAIGHT LINE of allowlisted commands. This is deliberately an
# allowlist and not a denylist: three review rounds enumerated short-circuit forms
# (`exit 0`, `set +e`, `if false`, `exec`, `trap`) and each round found a sibling the
# last one missed — `exit` with no argument, `exit 00`, `while false; do`,
# `until true; do`, `for _ in ""; do`, `case x in`, `{ … } &`, `( … ) || true`. An
# allowlist makes the NEXT unenumerated form fail closed by default.
_GUARD_COMMANDS = frozenset({"[", "test", "echo", "python", "python3", "grep", "pytest"})
_BLOCK_WORDS = frozenset({
    "if", "then", "elif", "else", "fi", "while", "until", "for", "do", "done",
    "case", "esac", "select", "function", "{", "}", "(", ")", "exec", "trap",
    "eval", "source", ".", "return", "continue", "break",
})
_REDIRECT_FLAGS = frozenset({"-C", "--directory", "-f", "--file"})


def _key_re(key: str, indent: str = r"\s*") -> re.Pattern[str]:
    """A YAML key matcher that survives quoting and spacing.

    `'env':`, `"env":` and `env :` are the SAME key to YAML, to Actions, and to
    actionlint. Four separate regexes in this file matched only the bare spelling, so
    one quoted key defeated all of them — after the identical hole had already been
    found and fixed in `_has_if`, whose comment says "one edit would otherwise disable
    every if-check in this file". The fix stopped at that function. Every key
    assertion now shares this matcher so the CLASS is closed, not a spelling.
    """
    return re.compile(rf"^{indent}['\"]?{re.escape(key)}['\"]?\s*:", re.M)


# Step-level `env:` stays legal — the detect step and the guard need it — but its KEYS
# are pinned. `MAKEFLAGS: '-n'` on the anchor turns the whole chain into a recipe
# printer; `PYTHON: 'true'` wins over the Makefile's `PYTHON ?=` and substitutes the
# interpreter; `PYTHONOPTIMIZE: '1'` compiles out the inline asserts a step exists to
# guarantee. Allowlisted, so a new key fails closed.
_ALLOWED_STEP_ENV = frozenset({
    "PYTHONDONTWRITEBYTECODE", "PYTHONUTF8", "PYTHONIOENCODING",
    "BASE_SHA", "HEAD_SHA",
    "GATE_MAIN_RESULT", "GATE_SAST_RESULT", "GATE_EXPORT_BOUNDARY_RESULT",
})


def _step_env_keys(step: str) -> list[str]:
    """Keys nested under a step's `env:`, and nothing else.

    Scoped by indent: a flat 8-space scan also caught the step's SIBLING keys
    (`id`, `run`, `env` itself), which made the allowlist check fail on a clean
    baseline for the wrong reason.
    """
    out: list[str] = []
    lines = step.splitlines()
    for index, line in enumerate(lines):
        if not _key_re("env").match(line):
            continue
        base = len(line) - len(line.lstrip())
        for follow in lines[index + 1:]:
            if not follow.strip():
                continue
            indent = len(follow) - len(follow.lstrip())
            if indent <= base:
                break
            match = re.match(r"\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?\s*:", follow)
            if match:
                out.append(match.group(1))
    return out


def _strip_inline_comment(line: str) -> str:
    """Truncate at the first `#` that is outside single or double quotes."""
    out, quote = [], None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _strip_comments(text: str) -> str:
    return "\n".join(_strip_inline_comment(ln) for ln in text.splitlines())


def _result_var(job_id: str) -> str:
    """AC3's transform. `<J_UPPER>_RESULT` written literally for a hyphenated id
    gives `$GATE-MAIN_RESULT`, which is POSIX default-value syntax, not the
    variable intended — so the comparison never matches and the job is always red.
    """
    return job_id.upper().replace("-", "_") + "_RESULT"


def _job_ids(text: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip() == "jobs:")
    except StopIteration:
        return []
    ids = []
    for line in lines[start + 1:]:
        if line.strip() and not line.startswith(" "):
            break
        m = re.match(r"^  ([A-Za-z0-9_-]+):\s*$", line)
        if m:
            ids.append(m.group(1))
    return ids


def _job_block(text: str, job_id: str) -> str:
    m = re.search(
        rf"^  {re.escape(job_id)}:\s*$(.*?)(?=^  [A-Za-z0-9_-]+:\s*$|\Z)",
        text, re.M | re.S,
    )
    return m.group(1) if m else ""


def _steps(block: str) -> list[tuple[str, str]]:
    """(name, text) per step, parsed ONLY from under the `steps:` key.

    `needs:` entries live at the same 6-space indent as steps, so scanning the whole
    job block returned them as pseudo-steps — and the chunk for the final one ran on
    to swallow `runs-on`, `timeout-minutes` and the job-level `if:`, which made an
    if-check report against a dependency name.
    """
    marker = re.search(r"^    steps:\s*$", block, re.M)
    if not marker:
        return []
    block = block[marker.end():]
    out = []
    for chunk in re.findall(r"(?:^|\n)      - (.*?)(?=\n      - |\Z)", block, re.S):
        nm = re.search(r"^\s*name:\s*(.+)$", chunk, re.M)
        out.append((nm.group(1).strip().strip("\"'") if nm else "", chunk))
    return out


def _step_named(block: str, needle: str) -> str:
    """The single step whose name contains `needle`; "" if none OR MORE THAN ONE.

    Ambiguity must fail closed. Per-job suffixes mean a step can be named
    `Set up Python (gate-export-boundary)`, which contains the needle
    `export-boundary` — "first match wins" then audits the wrong step and every
    assertion about the real one fails for the wrong reason.
    """
    hits = [chunk for name, chunk in _steps(block) if needle in name]
    return hits[0] if len(hits) == 1 else ""


def _checkout_steps(block: str) -> list[str]:
    return [c for _, c in _steps(block) if "actions/checkout" in c]


def _run_body(step: str) -> str:
    m = re.search(r"run:\s*[|>][-+0-9]*\s*\n(.*?)(?=\n\s{0,8}\w[\w-]*:|\Z)", step, re.S)
    if m:
        return m.group(1)
    m = re.search(r"run:\s*(.+)", step)
    return m.group(1) if m else ""


def _all_run_bodies(text: str) -> str:
    """Every `run:` body in `text`, concatenated.

    `_run_body` returns only the FIRST run: it finds, so calling it on a whole job
    block made `gate-main-bandit` and the aggregator guard checks inspect one step —
    they passed only because of where the run steps sat in the fixture, and would
    have gone red for the wrong reason against the real ~40-step job.
    """
    steps = _steps(text)
    if steps:
        return "\n".join(_run_body(chunk) for _, chunk in steps)
    return _run_body(text)


def _run_lines(step: str) -> list[str]:
    """Run-body lines with backslash continuations JOINED first.

    bash joins a continued `make ...` line with the next into one statement; an earlier version of this
    function did not, so a flag on the continued line was invisible to argv checks
    while bash saw it. The old note claiming that divergence was "fail-closed" was
    true only of the guard body's comparisons, not of the anchor — where it was a
    green bypass.
    """
    joined: list[str] = []
    for raw in _all_run_bodies(step).splitlines():
        text = raw.strip()
        if not text:
            continue
        if joined and joined[-1].endswith("\\"):
            joined[-1] = joined[-1][:-1].rstrip() + " " + text
        else:
            joined.append(text)
    return [ln for ln in joined if ln]


UNPARSEABLE = "\x00unparseable"


# KNOWN DIVERGENCE, fail-closed: this splitter does not model backslash line
# continuations, so `echo a \` followed by a comparison is one bash statement (the
# comparison becomes echo's arguments) but two statements here. The consequence is a
# guard that exits 1 unconditionally — red, never green — so it wastes an
# implementer's time rather than shipping a hole. Fixing it means joining
# continuations before splitting; left undone deliberately because the failure
# direction is safe and a half-modelled continuation is worse than none.
def _split_line(line: str) -> list[str]:
    """Split on `;`, `&&`, `||` OUTSIDE quotes.

    A quote-unaware split is how draft 3 was defeated:
    `echo "off && make build-check … SAST_DELEGATED=1"` handed
    `make build-check … SAST_DELEGATED=1"` to the command-word matcher. Returns
    [UNPARSEABLE] on an unbalanced quote so the caller fails CLOSED rather than
    treating the remainder of the line as code.
    """
    out: list[str] = []
    cur: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            i += 1
        elif ch in "'\"":
            quote = ch
            cur.append(ch)
            i += 1
        elif ch == ";":
            out.append("".join(cur))
            cur = []
            i += 1
        elif line.startswith(("&&", "||"), i):
            out.append("".join(cur))
            cur = []
            i += 2
        else:
            cur.append(ch)
            i += 1
    if quote is not None:
        return [UNPARSEABLE]
    out.append("".join(cur))
    return [seg.strip() for seg in out if seg.strip()]


def _statements(step: str) -> list[tuple[str, str]]:
    """(statement, source line) for every shell statement in a step's run body."""
    out = []
    for line in _run_lines(step):
        for stmt in _split_line(line):
            out.append((stmt, line))
    return out


def _load_bearing(line: str) -> bool:
    """False when the statement's exit status is discarded, so it gates nothing.

    Checked inside _invocation so EVERY assertion inherits it. Three consecutive
    drafts each hardened one assertion and left the others neuterable by `|| true`,
    a trailing `&` (the step never waits), or `; true`.
    """
    return not _DISCARDING_TAIL.search(line)


def _command(stmt: str) -> tuple[str, list[str]]:
    """(command word, args) after stripping `!` and leading VAR=val assignments."""
    toks = stmt.split()
    i = 0
    if toks and toks[0] == "!":
        i = 1
    while i < len(toks) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[i]):
        i += 1
    return (toks[i], toks[i + 1:]) if i < len(toks) else ("", [])


def _invocation(step_or_block: str, command: str, *required_args: str,
                allow_negation: bool = False) -> str:
    """The load-bearing statement whose COMMAND WORD is `command` and whose ARG
    TOKENS include every `required_args` entry.

    Rejects, uniformly: a discarded exit status (`|| true`, trailing `&`, `; true`);
    a dry run (`-n`, `--dry-run`); a redirected target (`-C`, `-f`) which runs
    something other than what is pinned; and — unless allowed — a negated form,
    since `! test -d x` succeeds exactly when the tree is missing.
    """
    for stmt, line in _statements(step_or_block):
        if stmt == UNPARSEABLE:
            continue
        if not _load_bearing(line):
            continue
        if not allow_negation and stmt.split()[:1] == ["!"]:
            continue
        cmd, args = _command(stmt)
        if cmd != command:
            continue
        if _DRY_RUN_FLAGS & set(args) or _REDIRECT_FLAGS & set(args):
            continue
        if "$(" in stmt or "`" in stmt:
            continue  # substitution can reintroduce a flag no token equals
        if all(any(a == tok or a in tok for tok in args) for a in required_args):
            return stmt
    return ""


PINNED_SAST_IF = "if: steps.changes.outputs.skip_sast != 'true'"


def _has_if(step: str) -> bool:
    """Does this step carry ANY step-level `if:`?

    `if: ${{ false }}` disables a step as completely as `continue-on-error`, which
    Boundaries forbids — and neither actionlint nor zizmor at --min-severity high
    flags a falsy condition. Every load-bearing step must therefore carry none, and
    the single step that legitimately has one is compared for EQUALITY, since
    `… != 'true' && false` passes any substring test.
    """
    # `'if': ${{ false }}` is valid YAML with identical semantics and defeats a bare
    # `^\s*if:` — one edit would otherwise disable every if-check in this file.
    return _key_re("if").search(step) is not None


def _body_is_straight_line(step: str) -> bool:
    """Is this body `set -euo pipefail` followed only by allowlisted plain commands?

    Rejects: any control-flow opener, any backgrounded statement, any `set` after the
    first line, any `exit` whose argument is not exactly `1`, and any command word
    outside `_GUARD_COMMANDS`. A body that cannot short-circuit cannot leave its
    comparisons unevaluated.
    """
    lines = _run_lines(step)
    if not lines or lines[0] != _STRICT_SHELL:
        return False
    for index, (stmt, line) in enumerate(_statements(step)):
        if stmt == UNPARSEABLE:
            return False
        stripped = line.rstrip()
        if stripped.endswith("&") and not stripped.endswith("&&"):
            return False  # backgrounded: the parent runs on regardless
        cmd, args = _command(stmt)
        if index == 0:
            if stmt != _STRICT_SHELL:
                return False
            continue
        if cmd == "set":
            return False  # only the mandatory first line may touch shell options
        if cmd == "exit":
            if args != ["1"]:
                return False  # `exit`, `exit 0`, `exit 00` all short-circuit green
            continue
        if cmd in _BLOCK_WORDS or cmd not in _GUARD_COMMANDS:
            return False
    return True


def audit(text: str, evaluated: list[str] | None = None) -> list[str]:
    bad: list[str] = []

    def check(label: str, ok: bool) -> None:
        if evaluated is not None:
            evaluated.append(label)
        if not ok:
            bad.append(label)

    text = _strip_comments(text)
    job_ids = _job_ids(text)
    check("jobs-parsed", bool(job_ids))
    work_jobs = [j for j in job_ids if j != AGGREGATOR_JOB_ID]

    # AC13: derived set-equality (catches a job ADDED unwired) + a literal floor
    # (catches a job DELETED entirely, which derivation alone cannot see).
    check("work-jobs-floor", all(j in work_jobs for j in REQUIRED_WORK_JOBS))
    check("aggregator-present", AGGREGATOR_JOB_ID in job_ids)

    agg = _job_block(text, AGGREGATOR_JOB_ID)
    _name_re = rf"^\s*name:\s*\"?{re.escape(AGGREGATOR_NAME)}\"?\s*$"
    check("one-required-name", len(re.findall(_name_re, text, re.M)) == 1)
    # ...and it must be THIS job's name. Otherwise renaming the aggregator and
    # putting the required-check name on a trivial `noop` job — wired into needs:,
    # env: and a comparison so every derived check still passes — makes the sole
    # required check a job whose only step is `echo ok`.
    check("required-name-is-aggregator", re.search(_name_re, agg, re.M) is not None)
    _agg_job_ifs = re.findall(r"^    if:\s*(.+?)\s*$", agg, re.M)
    check("aggregator-always", _agg_job_ifs == ["${{ always() }}"])
    # A job-level `if:` skips the whole job. On a work job that surfaces as
    # `skipped`, which the aggregator's != "success" catches — but a second `if:` on
    # the aggregator itself is a duplicate YAML key whose winner is parser-dependent,
    # so require exactly one and require it to be always().

    # AC13: the guard must RUN here, as a python invocation — not appear as a
    # filename in an echo, a needs: entry or a with: value. Two distinct
    # invocations are required, and the audit one must NOT carry --self-test:
    # otherwise the aggregator could run only the mutation matrix (which passes
    # against synthetic fixtures) and never audit the real workflow at all.
    def _guard_invocations() -> tuple[bool, bool]:
        audit_run = self_run = False
        for stmt, line in _statements(agg):
            if stmt == UNPARSEABLE or not _load_bearing(line):
                continue
            cmd, args = _command(stmt)
            if cmd not in ("python3", "python") or SELF_NAME not in args:
                continue
            if "--self-test" in args:
                self_run = True
            else:
                audit_run = True
        return audit_run, self_run

    # Both aggregator steps must be unconditional: `if: ${{ false }}` on them merges
    # a PR with every gate red, since the aggregator is the required check.
    # Indexed labels, so an UNNAMED step still gets checked — dropping a step's name
    # previously made it invisible to this loop AND emitted no label to notice.
    for _i, (_nm, _st) in enumerate(_steps(agg)):
        check(f"aggregator-step-no-if[{_nm or f'#{_i}'}]", not _has_if(_st))
    check("aggregator-steps-all-named",
          all(nm for nm, st in _steps(agg) if "run:" in st))
    # The guard body must reach its comparisons. Present-and-load-bearing is not
    # enough: a prepended `exit 0`, a `set +e`, or wrapping them in `if false; then`
    # leaves every comparison intact and never evaluates one. Same shape as
    # export-boundary-strict-shell / -no-set-relax, applied here because this body
    # decides the required check.
    check("no-env-file-writes-in-aggregator", not any(
        "GITHUB_ENV" in ln or "GITHUB_OUTPUT" in ln
        for _n, st in _steps(agg) for ln in _run_lines(st)))
    guard_step = _step_named(agg, "Require every gate")
    guard_lines = _run_lines(guard_step)
    check("guard-strict-shell", bool(guard_lines) and guard_lines[0] == _STRICT_SHELL)
    check("guard-straight-line", bool(guard_step) and _body_is_straight_line(guard_step))
    _agg_audit, _ = _guard_invocations()
    # One invocation is enough: this file runs its mutation matrix on EVERY
    # invocation (see main()), so a separate `--self-test` call would be redundant
    # and an assertion demanding one would pin a shape the design dropped.
    check("guard-runs-in-aggregator", _agg_audit)

    # AC3: three-way binding, and each comparison's CONSEQUENT.
    # `[ "$X" != "success" ] || echo ok` carries the comparison and gates nothing.
    agg_flat = _strip_comments(agg)
    for job_id in work_jobs:
        var = _result_var(job_id)
        check(f"needs[{job_id}]",
              re.search(rf"^\s*- {re.escape(job_id)}\s*$", agg_flat, re.M) is not None)
        # On the GUARD step, not merely somewhere in the job: moving the bindings to
        # an earlier step lets that step's body write GATE_*_RESULT=success into
        # $GITHUB_ENV, and the guard then reads forged values while every assertion
        # about its body still holds.
        check(f"env-binding[{job_id}]",
              re.search(rf"{var}:\s*\$\{{\{{\s*needs\.{re.escape(job_id)}\.result\s*\}}\}}",
                        _step_named(agg, "Require every gate")) is not None)
        # Command-word model, not a block regex: an earlier draft's whole-block
        # search was satisfied by `echo '[ "$X" != "success" ] && exit 1'`, which
        # greens the required check with every gate failed. The consequent must sit
        # on the same source line as the test.
        # EQUALITY against the pinned form, and the rest of the line may only be
        # `&& echo …` segments terminating in `&& exit 1`. Existence was not enough:
        # `[ "$X" != "success" -a -f /nonexistent ]` satisfies "contains the var and
        # !=" while never being true, and a trailing `&& exit 1` elsewhere on the line
        # satisfied a line-wide search without being that test's consequent.
        pinned = f'[ "${var}" != "success" ]'
        found = ""
        for stmt, line in _statements(agg):
            if stmt == UNPARSEABLE or not _load_bearing(line):
                continue
            if " ".join(stmt.split()) != pinned:
                continue
            segments = [seg.strip() for seg in re.split(r"&&", line) if seg.strip()]
            if segments[-1].split()[:2] != ["exit", "1"]:
                continue
            if " ".join(segments[0].split()) != pinned:
                continue
            # Between the test and `exit 1`, only diagnostics. A second `[` here is
            # how an always-false test chains in and the exit becomes unreachable.
            if any(_command(seg)[0] != "echo" for seg in segments[1:-1]):
                continue
            found = stmt
            break
        check(f"comparison[{job_id}]", bool(found))

    # A one-line total bypass: greens a job with its chain failed, or greens the
    # required check regardless of every needs.*.result.
    check("no-continue-on-error", "continue-on-error" not in text)
    # `env: MAKEFLAGS: '-n'` turns gate-main's ~40-gate chain AND gate-sast's
    # `make sast` into recipe printers that exit 0. `env: PYTHON: 'true'` substitutes
    # the interpreter for the whole chain, because the Makefile uses `PYTHON ?=`.
    # `env: PYTHONOPTIMIZE: '1'` compiles out inline asserts. All three are one line,
    # invisible to argv-level checks, and report success.
    check("no-workflow-env", _key_re("env", "").search(text) is None)
    # `shell: 'true {0}'` on a step — or `defaults: run: shell:` at workflow level —
    # runs `true <script>` and leaves the body untouched. actionlint accepts any
    # value containing `{0}`; zizmor has no rule for it.
    check("no-defaults-block", _key_re("defaults", "").search(text) is None)
    # Never do: no ${{ }} interpolation in a run: body this change writes or moves.
    check("no-interpolation-in-run", not any(
        "${{" in ln for jid in job_ids for _, st in _steps(_job_block(text, jid))
        for ln in _run_lines(st)))
    # A parse miss must be reported AS a parse miss: otherwise every negative
    # assertion below passes vacuously and the violation list understates the gap.
    for jid in job_ids:
        blk = _job_block(text, jid)
        check(f"steps-parsed[{jid}]", bool(_steps(blk)))
        check(f"shell-parseable[{jid}]",
              not any(st == UNPARSEABLE for st, _ in _statements(blk)))

    # AC12
    check("top-permissions", re.search(
        r"^permissions:\s*\n  contents: read\s*\n(?=\S|\Z)", text, re.M) is not None)
    check("no-pull-request-target", "pull_request_target" not in text)
    check("trigger-pull-request",
          re.search(r"^  pull_request:\s*$", text, re.M) is not None)
    check("trigger-push-main",
          re.search(r"^  push:\s*\n    branches: \[main\]\s*$", text, re.M) is not None)
    check("concurrency-group", EXPECTED_CONCURRENCY_GROUP in text)
    check("concurrency-cancel",
          "cancel-in-progress: ${{ github.event_name == 'pull_request' }}" in text)
    for job_id in job_ids:
        blk = _job_block(text, job_id)
        check(f"timeout[{job_id}]", "timeout-minutes:" in blk)
        check(f"runs-on[{job_id}]", "runs-on: ubuntu-latest" in blk)
        # Same class as runs-on: an environment substitution the gates then execute
        # inside. A container missing make/python fails closed, but the substitution
        # itself is unreviewed by anything else in this repo.
        check(f"no-container[{job_id}]",
              re.search(r"^    (container|services):", blk, re.M) is None)
        # A job-level concurrency group can SERIALISE these jobs — green, but the
        # whole point of the split undone, and AC11's measurement is post-merge so
        # nothing else would notice.
        check(f"no-job-concurrency[{job_id}]",
              re.search(r"^    concurrency:", blk, re.M) is None)
        check(f"python-version[{job_id}]",
              f"python-version: {EXPECTED_PYTHON}" in blk)
        check(f"no-job-permissions[{job_id}]", "permissions:" not in blk)
        # Job-level env: only (4 spaces). Step-level env: at 8 is legitimate and used.
        check(f"no-job-env[{job_id}]", _key_re("env", "    ").search(blk) is None)
        check(f"no-step-shell[{job_id}]", _key_re("shell").search(blk) is None)
        # Step-level env: is legal, its KEYS are not free-form (see _ALLOWED_STEP_ENV).
        _env_keys = [k for _n, st in _steps(blk) for k in _step_env_keys(st)]
        check(f"step-env-keys-allowlisted[{job_id}]",
              all(k in _ALLOWED_STEP_ENV for k in _env_keys))
        checkouts = _checkout_steps(blk)
        check(f"checkout-present[{job_id}]", bool(checkouts))
        # Per CHECKOUT, not per job: a second unhardened checkout otherwise passes.
        check(f"persist-credentials[{job_id}]",
              bool(checkouts) and all("persist-credentials: false" in c for c in checkouts))
        if job_id != AGGREGATOR_JOB_ID:
            check(f"no-job-if[{job_id}]", _key_re("if", "    ").search(blk) is None)
            check(f"no-needs[{job_id}]", not re.search(r"^\s+needs:", blk, re.M))
            check(f"fetch-depth[{job_id}]",
                  bool(checkouts) and all("fetch-depth: 0" in c for c in checkouts))

    # AC4/AC5b: delegation must be a make ARGUMENT. As an env prefix, $(origin) is
    # `environment`, so AC5c runs the SAST leg in gate-main too — silent double scan.
    main_blk = _job_block(text, "gate-main")
    anchor = _step_named(main_blk, "Run make build-check")
    check("anchor-step", bool(_invocation(anchor, "make", "build-check")))
    check("anchor-no-if", bool(anchor) and not _has_if(anchor))
    check("delegation-is-argument",
          bool(_invocation(anchor, "make", "build-check", "SAST_DELEGATED=1")))
    check("delegation-not-prefix", not any(
        re.match(r"^SAST_DELEGATED=1\s+make\b", st) for st, _ in _statements(anchor)))
    # AC14(1): lint-nosec-form sets a caveat and exits 0 without bandit, so the
    # install must be in THIS job — it runs inside make build-check's chain, and the
    # split moved the SAST provisioning to gate-sast.
    #
    # This asserts PLACEMENT, not efficacy. #986 landed the install independently
    # with a pinned version plus a runtime probe that bandit's registry resolves as
    # lint-nosec-form's id_checker() expects; that probe is the real guarantee and
    # is stronger than anything a text matcher can claim. What the split can break —
    # and all this needs to catch — is the step ending up in the wrong job.
    # _step_named fails closed on ambiguity; the previous first-match lookup let an
    # earlier step merely MENTIONING bandit satisfy this while the real install was
    # deleted. Also require the pinned-version read and the registry probe, which are
    # what make the install load-bearing rather than nominal.
    bandit_step = _step_named(main_blk, "bandit")
    check("gate-main-bandit", bool(bandit_step)
          and bool(_invocation(bandit_step, "pip", "install"))
          and "requirements-sast.txt" in bandit_step
          and bool(_invocation(bandit_step, "python") or "extension_loader" in bandit_step))

    # AC4: the predicate has exactly one consumer.
    sast_blk = _job_block(text, "gate-sast")
    sast_step = _step_named(sast_blk, "make sast")
    check("sast-step-present", bool(_invocation(sast_step, "make", "sast")))
    # EQUALITY, not substring: `… != 'true' && false` satisfies a substring test
    # while `make sast` never runs.
    _sast_ifs = re.findall(r"^\s*if:\s*(.+?)\s*$", sast_step, re.M)
    check("sast-step-condition",
          _sast_ifs == [PINNED_SAST_IF.split("if: ", 1)[1]])
    install = _step_named(sast_blk, "SAST/SCA tools")
    check("sast-install-present", bool(_invocation(install, "pip", "requirements-sast.txt")))
    check("sast-install-unconditional", bool(install) and not _has_if(install))

    # AC14(2): the export-boundary suite's silent tree-shape skip.
    exp_blk = _job_block(text, "gate-export-boundary")
    exp_step = _step_named(exp_blk, "pytest export-boundary gate")
    check("export-boundary-full-checkout", "sparse-checkout" not in exp_blk)
    check("export-boundary-no-if", bool(exp_step) and not _has_if(exp_step))
    exp_lines = _run_lines(exp_step)
    check("export-boundary-strict-shell",
          bool(exp_lines) and exp_lines[0] == _STRICT_SHELL)
    check("export-boundary-straight-line",
          bool(exp_step) and _body_is_straight_line(exp_step))
    check("export-boundary-tree-probe",
          bool(_invocation(exp_step, "test", "-d", "packages/agentbundle")))
    check("export-boundary-probe-not-negated", not any(
        st.split()[:1] == ["!"] and "packages/agentbundle" in st
        for st, _ in _statements(exp_step)))
    pytest_stmt = (_invocation(exp_step, "python", "-m", "pytest",
                               "tools/test_check_artifact_contents.py", "-rs")
                   or _invocation(exp_step, "pytest",
                                  "tools/test_check_artifact_contents.py", "-rs"))
    check("export-boundary-skip-flag", bool(pytest_stmt))
    # `--co` / `--collect-only` executes nothing while still exiting 0.
    check("export-boundary-not-collect-only",
          not any(f in pytest_stmt.split() for f in ("--co", "--collect-only")))
    # (An earlier draft had an "export-boundary-no-bare-pipe" check here. Its second
    # conjunct was loop-invariant, so it could never fail independently of
    # export-boundary-strict-shell and its mutation passed only for that co-fired
    # reason — it inflated the matrix without adding a proof. Pipeline safety is now
    # covered by requiring `set -euo pipefail` as the FIRST statement.)
    # The grep must read the file `tee` wrote. Untied, pointing it at a path nothing
    # creates passes: grep exits 2 on a missing file and `!` inverts that to 0, so
    # every skip becomes invisible.
    _tee_target = ""
    for _st, _ in _statements(exp_step):
        _toks = _st.split()
        if "tee" in _toks:
            _idx = _toks.index("tee")
            if _idx + 1 < len(_toks):
                _tee_target = _toks[_idx + 1]
            break
    grep_stmt = next((st for st, ln in _statements(exp_step)
                      if st != UNPARSEABLE and _command(st)[0] == "grep"
                      and SKIP_ASSERT_PATTERN in st and _load_bearing(ln)
                      and _tee_target and _tee_target in st), "")
    check("export-boundary-skip-check", bool(grep_stmt))
    # The grep must be negated: `grep -q` exits 0 when it FINDS a skip, so a bare
    # `grep … && exit 1` as the last line is red on healthy runs and green on skips.
    check("export-boundary-skip-negated", bool(grep_stmt) and any(
        ln.lstrip().startswith("!") and "grep" in ln for ln in _run_lines(exp_step)))

    return bad


# ── Self-test ────────────────────────────────────────────────────────────────

_FIXTURE = REPO_ROOT / "tools" / "fixtures" / "build-check-good.yml"


def _baseline() -> str:
    """The clean four-job baseline every proof runs against.

    It must be SHAPE-REPRESENTATIVE of the real workflow, not merely valid: an
    earlier fixture had four single-line steps per job and no `push:` trigger, which
    hid two defects (a job-block/step-block confusion, and the unasserted push run
    that AC12 calls load-bearing) and mutation-proved the file against a workflow
    with that mitigation already absent.
    """
    if _FIXTURE.is_file():
        return _FIXTURE.read_text(encoding="utf-8")
    raise SystemExit(
        f"missing baseline fixture {_FIXTURE.relative_to(REPO_ROOT)} — "
        "the self-test cannot prove anything without it"
    )


def _job_span(text: str, job_id: str) -> tuple[int, int]:
    m = re.search(rf"^  {re.escape(job_id)}:\s*$", text, re.M)
    if not m:
        return (-1, -1)
    nxt = re.search(r"^  [A-Za-z0-9_-]+:\s*$", text[m.end():], re.M)
    return (m.end(), m.end() + nxt.start() if nxt else len(text))


def _reindent_job_steps(text: str, job_id: str) -> str:
    """Reindent every step in one job to 4 spaces — still valid YAML, but the
    6-space step scan finds nothing, which must be reported as a parse miss rather
    than silently vacuuming every negative assertion in that job."""
    lo, hi = _job_span(text, job_id)
    if lo < 0:
        return text
    return text[:lo] + text[lo:hi].replace("\n      - ", "\n    - ") + text[hi:]


def _sub_in_job(text: str, job_id: str, old: str, new: str) -> str:
    lo, hi = _job_span(text, job_id)
    if lo < 0:
        return text
    return text[:lo] + text[lo:hi].replace(old, new, 1) + text[hi:]


_MUTATIONS: list[tuple[str, str, object]] = [
    # -- the neutering class, applied to EVERY control (round-8 blocker 1) --------
    ("or-true-anchor", "anchor-step",
     lambda t: t.replace("make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         "make build-check PACKS_DIR=packs SAST_DELEGATED=1 || true")),
    ("background-anchor", "anchor-step",
     lambda t: t.replace("make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         "make build-check PACKS_DIR=packs SAST_DELEGATED=1 &")),
    ("dry-run-anchor", "anchor-step",
     lambda t: t.replace("make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         "make -n build-check PACKS_DIR=packs SAST_DELEGATED=1")),
    ("redirect-anchor", "anchor-step",
     lambda t: t.replace("make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         "make -C /tmp build-check PACKS_DIR=packs SAST_DELEGATED=1")),
    ("or-true-sast", "sast-step-present",
     lambda t: t.replace("make sast", "make sast || true")),
    ("or-true-guard", "guard-runs-in-aggregator",
     lambda t: t.replace(f"python3 {SELF_NAME}\n", f"python3 {SELF_NAME} || true\n")),
    ("or-true-tree-probe", "export-boundary-tree-probe",
     lambda t: t.replace("test -d packages/agentbundle", "test -d packages/agentbundle || true")),
    ("or-true-grep", "export-boundary-skip-check",
     lambda t: t.replace('! grep -Eq "^SKIPPED" "$RUNNER_TEMP/out.txt"',
                         'grep -Eq "^SKIPPED" "$RUNNER_TEMP/out.txt" || true')),
    # -- quoted-separator smuggling (round-8 blocker 2) --------------------------
    ("quoted-and-anchor", "anchor-step",
     lambda t: t.replace("run: make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         'run: echo "off && make build-check PACKS_DIR=packs SAST_DELEGATED=1"')),
    ("quoted-semi-tree-probe", "export-boundary-tree-probe",
     lambda t: t.replace("          test -d packages/agentbundle",
                         '          echo "x; test -d packages/agentbundle"')),
    ("unbalanced-quote", "shell-parseable[gate-main]",
     lambda t: t.replace("run: make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         'run: echo "unterminated')),
    # -- echo-spoofing (rounds 7-8) ---------------------------------------------
    ("echo-wrap-anchor", "anchor-step",
     lambda t: t.replace("run: make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         'run: echo "make build-check PACKS_DIR=packs SAST_DELEGATED=1"')),
    ("echo-wrap-comparisons", "comparison[gate-main]",
     lambda t: t.replace('[ "$GATE_MAIN_RESULT" != "success" ] && exit 1',
                         """echo '[ "$GATE_MAIN_RESULT" != "success" ] && exit 1'""")),
    ("echo-wrap-guard", "guard-runs-in-aggregator",
     lambda t: t.replace(f"          python3 {SELF_NAME}\n",
                         f'          echo "python3 {SELF_NAME}"\n')),
    ("echo-wrap-bandit", "gate-main-bandit",
     lambda t: t.replace('          pip install "$pin"', '          echo "pip install $pin"')),
    ("drop-bandit-pin-read", "gate-main-bandit",
     lambda t: t.replace("tools/requirements-sast.txt", "elsewhere.txt", 1)),
    ("echo-wrap-sast-install", "sast-install-present",
     lambda t: t.replace("pip install -r tools/requirements-sast.txt",
                         'echo "pip install -r tools/requirements-sast.txt"')),
    # -- consequents and negation ------------------------------------------------
    ("drop-consequent", "comparison[gate-sast]",
     lambda t: t.replace('[ "$GATE_SAST_RESULT" != "success" ] && exit 1',
                         '[ "$GATE_SAST_RESULT" != "success" ] || echo ok')),
    ("negate-tree-probe", "export-boundary-probe-not-negated",
     lambda t: t.replace("test -d packages/agentbundle", "! test -d packages/agentbundle")),
    ("un-negate-grep", "export-boundary-skip-negated",
     lambda t: t.replace('! grep -Eq "^SKIPPED"', 'grep -Eq "^SKIPPED"')),
    ("multi-hyphen-comparison", "comparison[gate-export-boundary]",
     lambda t: t.replace('[ "$GATE_EXPORT_BOUNDARY_RESULT" != "success" ] && exit 1',
                         '[ "$GATE_EXPORT_BOUNDARY_RESULT" != "success" ] || echo ok')),
    ("multi-hyphen-env", "env-binding[gate-export-boundary]",
     lambda t: t.replace("GATE_EXPORT_BOUNDARY_RESULT: ${{ needs.gate-export-boundary.result }}",
                         "GATE_EXPORT_BOUNDARY_RESULT: ${{ needs.gate-main.result }}")),
    # -- shell hardening ---------------------------------------------------------
    # The six short-circuit siblings the re-review executed. Each audits clean under a
    # denylist and returns exit 0 in bash with GATE_MAIN_RESULT=failure.
    ("bare-exit-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"', '          exit\n          [ "$GATE_MAIN_RESULT"')),
    ("exit-double-zero-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"', '          exit 00\n          [ "$GATE_MAIN_RESULT"')),
    ("while-false-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"', '          while false; do\n          [ "$GATE_MAIN_RESULT"')),
    ("until-true-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"', '          until true; do\n          [ "$GATE_MAIN_RESULT"')),
    ("case-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"', '          case x in y)\n          [ "$GATE_MAIN_RESULT"')),
    ("background-block-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"', '          { true; } &\n          [ "$GATE_MAIN_RESULT"')),
    ("while-false-in-export-body", "export-boundary-straight-line",
     lambda t: t.replace("          test -d packages/agentbundle",
                         "          while false; do\n          test -d packages/agentbundle")),
    ("drop-strict-shell", "export-boundary-strict-shell",
     lambda t: t.replace("          set -euo pipefail\n", "", 1)),
    ("strict-shell-late", "export-boundary-strict-shell",
     lambda t: t.replace("          set -euo pipefail\n          test -d",
                         "          test -d")),
    ("set-relax", "export-boundary-straight-line",
     lambda t: t.replace("          test -d packages/agentbundle",
                         "          set +o pipefail\n          test -d packages/agentbundle")),
    ("collect-only", "export-boundary-not-collect-only",
     lambda t: t.replace("-q -rs", "--co -q -rs")),
    ("drop-suite-path", "export-boundary-skip-flag",
     lambda t: t.replace("tools/test_check_artifact_contents.py -q -rs", "-q -rs")),
    # -- graph shape -------------------------------------------------------------
    ("delete-work-job", "work-jobs-floor",
     lambda t: re.sub(r"^  gate-main:.*?(?=^  gate-sast:)", "", t, flags=re.M | re.S)),
    ("unwire-dependency", "needs[gate-main]", lambda t: t.replace("      - gate-main\n", "")),
    ("rename-aggregator-id", "aggregator-present",
     lambda t: t.replace("  build-check:\n", "  aggregate:\n", 1)),
    # The whole-workflow no-ops (post-implementation re-review blockers 2 and 3).
    # The quoted-key class (final review blocker 1): every variant of every banned key.
    ("quoted-workflow-env", "no-workflow-env",
     lambda t: t.replace("\npermissions:\n", "\n'env':\n  MAKEFLAGS: '-n'\npermissions:\n", 1)),
    ("spaced-workflow-env", "no-workflow-env",
     lambda t: t.replace("\npermissions:\n", "\nenv :\n  MAKEFLAGS: '-n'\npermissions:\n", 1)),
    ("quoted-job-env", "no-job-env[gate-main]",
     lambda t: t.replace("  gate-main:\n", "  gate-main:\n    'env':\n      PYTHON: 'true'\n", 1)),
    ("quoted-defaults", "no-defaults-block",
     lambda t: t.replace("\npermissions:\n", "\n'defaults':\n  run:\n    shell: 'true {0}'\npermissions:\n", 1)),
    ("quoted-step-shell", "no-step-shell[gate-main]",
     lambda t: t.replace("      - name: Run make build-check\n",
                         "      - name: Run make build-check\n        'shell': 'true {0}'\n", 1)),
    # Blocker 2: step-level env: keys are allowlisted.
    ("step-env-makeflags", "step-env-keys-allowlisted[gate-main]",
     lambda t: t.replace("      - name: Run make build-check\n",
                         "      - name: Run make build-check\n        env:\n          MAKEFLAGS: '-n'\n", 1)),
    # Blocker 4: forge the results from an earlier step via $GITHUB_ENV.
    ("forge-results-via-github-env", "no-env-file-writes-in-aggregator",
     lambda t: t.replace("          python3 tools/test-build-check-workflow.py\n",
                         '          echo "GATE_MAIN_RESULT=success" >> "$GITHUB_ENV"\n'
                         "          python3 tools/test-build-check-workflow.py\n", 1)),
    # Blocker 3: a comparison that exists but can never be true.
    ("chained-false-test", "comparison[gate-main]",
     lambda t: t.replace('[ "$GATE_MAIN_RESULT" != "success" ] &&',
                         '[ "$GATE_MAIN_RESULT" != "success" ] && [ -f /nonexistent ] &&', 1)),
    ("grep-untied-from-tee", "export-boundary-skip-check",
     lambda t: t.replace('grep -Eq "^SKIPPED" "$RUNNER_TEMP/out.txt"',
                         'grep -Eq "^SKIPPED" "$RUNNER_TEMP/other.txt"', 1)),
    ("vacuous-comparison", "comparison[gate-main]",
     lambda t: t.replace('[ "$GATE_MAIN_RESULT" != "success" ]',
                         '[ "$GATE_MAIN_RESULT" != "success" -a -f /nonexistent ]', 1)),
    # Blocker 5: a flag hidden behind a continuation, and behind substitution.
    ("continuation-hides-dry-run", "delegation-is-argument",
     lambda t: t.replace("        run: make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         "        run: |\n          make build-check PACKS_DIR=packs SAST_DELEGATED=1 \\\n          -n")),
    ("substitution-hides-dry-run", "delegation-is-argument",
     lambda t: t.replace("run: make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         "run: make build-check PACKS_DIR=packs SAST_DELEGATED=1 $(printf -- -n)")),
    ("container-override", "no-container[gate-main]",
     lambda t: t.replace("  gate-main:\n", "  gate-main:\n    container: alpine\n", 1)),
    ("job-concurrency-serialises", "no-job-concurrency[gate-sast]",
     lambda t: t.replace("  gate-sast:\n", "  gate-sast:\n    concurrency: solo\n", 1)),
    ("workflow-env-makeflags", "no-workflow-env",
     lambda t: t.replace("\npermissions:\n", "\nenv:\n  MAKEFLAGS: '-n'\npermissions:\n", 1)),
    ("job-env-python", "no-job-env[gate-main]",
     lambda t: t.replace("  gate-main:\n", "  gate-main:\n    env:\n      PYTHON: 'true'\n", 1)),
    ("defaults-shell-override", "no-defaults-block",
     lambda t: t.replace("\npermissions:\n", "\ndefaults:\n  run:\n    shell: 'true {0}'\npermissions:\n", 1)),
    ("step-shell-override", "no-step-shell[gate-main]",
     lambda t: t.replace("      - name: Run make build-check\n",
                         "      - name: Run make build-check\n        shell: 'true {0}'\n", 1)),
    ("unname-aggregator-run-step", "aggregator-steps-all-named",
     lambda t: t.replace("      - name: Require every gate\n", "      - env:\n", 1)),
    ("no-jobs-block", "jobs-parsed", lambda t: t.replace("\njobs:\n", "\ndisabled:\n")),
    ("drop-always", "aggregator-always", lambda t: t.replace("    if: ${{ always() }}\n", "")),
    ("always-on-step", "aggregator-always",
     lambda t: t.replace("    if: ${{ always() }}\n", "").replace(
         "      - name: Require every gate\n",
         "      - name: Require every gate\n        if: ${{ always() }}\n")),
    ("duplicate-required-name", "one-required-name",
     lambda t: t.replace("  gate-sast:\n", "  gate-sast:\n    name: make build-check\n")),
    ("add-needs-to-work-job", "no-needs[gate-sast]",
     lambda t: t.replace("  gate-sast:\n", "  gate-sast:\n    needs: [gate-main]\n")),
    ("reindent-steps", "steps-parsed[gate-sast]",
     lambda t: _reindent_job_steps(t, "gate-sast")),
    # -- job-level settings ------------------------------------------------------
    ("continue-on-error", "no-continue-on-error",
     lambda t: t.replace("        run: make sast", "        continue-on-error: true\n        run: make sast")),
    ("interpolation-in-run", "no-interpolation-in-run",
     lambda t: t.replace("run: make sast", "run: make sast ${{ github.sha }}")),
    ("job-permissions", "no-job-permissions[gate-sast]",
     lambda t: t.replace("  gate-sast:\n", "  gate-sast:\n    permissions:\n      contents: write\n")),
    ("extra-permission-scope", "top-permissions",
     lambda t: t.replace("permissions:\n  contents: read\n", "permissions:\n  contents: read\n  packages: write\n")),
    # Scoped to gate-main: an unqualified replace now lands in gate-sast, whose
    # step of the same name comes first in the file.
    ("second-unhardened-checkout", "persist-credentials[gate-main]",
     lambda t: _sub_in_job(t, "gate-main", "      - name: Run make build-check",
                           "      - uses: actions/checkout@v4\n      - name: Run make build-check")),
    ("drop-fetch-depth", "fetch-depth[gate-main]",
     lambda t: t.replace("          fetch-depth: 0\n", "", 1)),
    ("drop-timeout", "timeout[gate-sast]",
     lambda t: t.replace("  gate-sast:\n    runs-on: ubuntu-latest\n    timeout-minutes: 25\n",
                         "  gate-sast:\n    runs-on: ubuntu-latest\n")),
    ("drop-runs-on", "runs-on[gate-sast]",
     lambda t: t.replace("  gate-sast:\n    runs-on: ubuntu-latest\n", "  gate-sast:\n")),
    ("drop-python-version", "python-version[gate-sast]",
     lambda t: t.replace('          python-version: "3.11"\n', "", 2)),
    ("drop-checkout", "checkout-present[gate-sast]",
     lambda t: t.replace("      - uses: actions/checkout@v4\n        with:\n"
                         "          fetch-depth: 0\n          persist-credentials: false\n", "", 2)),
    ("head-ref-concurrency", "concurrency-group",
     lambda t: t.replace(EXPECTED_CONCURRENCY_GROUP, "build-check-${{ github.head_ref }}")),
    ("drop-cancel-gate", "concurrency-cancel",
     lambda t: t.replace("cancel-in-progress: ${{ github.event_name == 'pull_request' }}",
                         "cancel-in-progress: true")),
    ("pull-request-target", "no-pull-request-target",
     lambda t: t.replace("  pull_request:\n", "  pull_request_target:\n")),
    ("drop-push-trigger", "trigger-push-main",
     lambda t: re.sub(r"\n  push:\n    branches: \[main\]", "", t)),
    # The `if:`-disables-a-step class (post-implementation security review). A falsy
    # step-level `if:` is as total as continue-on-error and no scanner flags it.
    ("if-false-on-anchor", "anchor-no-if",
     lambda t: t.replace("      - name: Run make build-check\n",
                         "      - name: Run make build-check\n        if: ${{ false }}\n")),
    ("if-false-on-export-step", "export-boundary-no-if",
     lambda t: t.replace("      - name: pytest export-boundary gate\n",
                         "      - name: pytest export-boundary gate\n        if: ${{ false }}\n")),
    ("if-false-on-aggregator-step", "aggregator-step-no-if[Require every gate]",
     lambda t: t.replace("      - name: Require every gate\n",
                         "      - name: Require every gate\n        if: ${{ false }}\n")),
    ("sast-if-and-false", "sast-step-condition",
     lambda t: t.replace("if: steps.changes.outputs.skip_sast != 'true'",
                         "if: steps.changes.outputs.skip_sast != 'true' && false")),
    ("exec-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"',
                         '          exec true\n          [ "$GATE_MAIN_RESULT"')),
    ("trap-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"',
                         '          trap "exit 0" ERR\n          [ "$GATE_MAIN_RESULT"')),
    ("job-if-on-work-job", "no-job-if[gate-sast]",
     lambda t: t.replace("  gate-sast:\n", "  gate-sast:\n    if: ${{ false }}\n", 1)),
    ("second-if-on-aggregator", "aggregator-always",
     lambda t: t.replace("    if: ${{ always() }}\n",
                         "    if: ${{ always() }}\n    if: ${{ false }}\n", 1)),
    ("early-exit-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"',
                         '          exit 0\n          [ "$GATE_MAIN_RESULT"')),
    ("set-relax-in-guard", "guard-straight-line",
     lambda t: t.replace('          [ "$GATE_MAIN_RESULT"',
                         '          set +e\n          [ "$GATE_MAIN_RESULT"')),
    ("drop-guard-strict-shell", "guard-strict-shell",
     lambda t: t.replace("          set -euo pipefail\n          python3", "          python3", 1)),
    # The required-check name must be bound to the AGGREGATOR, not merely unique.
    ("relocate-required-name", "required-name-is-aggregator",
     lambda t: t.replace("  build-check:\n    name: make build-check\n", "  build-check:\n", 1)
                .replace("  gate-sast:\n", "  gate-sast:\n    name: make build-check\n", 1)),
    # The comparison loop must inherit _load_bearing like every other assertion.
    ("background-comparison", "comparison[gate-main]",
     lambda t: t.replace('[ "$GATE_MAIN_RESULT" != "success" ] && exit 1',
                         '[ "$GATE_MAIN_RESULT" != "success" ] && exit 1 &')),
    ("drop-pull-request-trigger", "trigger-pull-request",
     lambda t: t.replace("  pull_request:\n    branches: [main]\n", "")),
    ("drop-delegation-flag", "delegation-is-argument",
     lambda t: t.replace(" SAST_DELEGATED=1", "", 1)),
    ("delegation-as-prefix", "delegation-not-prefix",
     lambda t: t.replace("run: make build-check PACKS_DIR=packs SAST_DELEGATED=1",
                         "run: SAST_DELEGATED=1 make build-check PACKS_DIR=packs")),
    ("drop-sast-condition", "sast-step-condition",
     lambda t: t.replace("        if: steps.changes.outputs.skip_sast != 'true'\n", "")),
    ("condition-on-sast-install", "sast-install-unconditional",
     lambda t: t.replace("      - name: Install SAST/SCA tools\n        run: pip install -r tools/requirements-sast.txt",
                         "      - name: Install SAST/SCA tools\n        if: steps.changes.outputs.skip_sast != 'true'\n        run: pip install -r tools/requirements-sast.txt")),
    ("sparse-checkout-export", "export-boundary-full-checkout",
     lambda t: _sub_in_job(t, "gate-export-boundary",
                           "          persist-credentials: false",
                           "          persist-credentials: false\n          sparse-checkout: tools")),
    ("rebind-env-var", "env-binding[gate-sast]",
     lambda t: t.replace("GATE_SAST_RESULT: ${{ needs.gate-sast.result }}",
                         "GATE_SAST_RESULT: ${{ needs.gate-main.result }}")),
]


def _family(check_id: str) -> str:
    """Collapse a parameterised id to its family.

    Proving `needs[*]` catches an unwired gate-main also proves it for gate-sast —
    identical code path, different loop variable. EXCEPT where the parameter changes
    a transform's output shape: `_result_var` exists because MULTI-hyphen ids are the
    hazard (`GATE_EXPORT_BOUNDARY_RESULT`), so those keep their own mutation cases
    and are not collapsed.
    """
    if check_id.startswith(("comparison[", "env-binding[")) and \
            "gate-export-boundary" in check_id:
        return check_id
    return re.sub(r"\[.*\]$", "[*]", check_id)


def self_test() -> int:
    failures: list[str] = []
    good = _baseline()

    evaluated: list[str] = []
    base = audit(good, evaluated)
    if base:
        failures.append(f"baseline should be clean, got {base}")

    for mut_id, expected, transform in _MUTATIONS:
        mutated = transform(good)  # type: ignore[operator]
        if mutated == good:
            failures.append(f"{mut_id}: transform was a no-op — proves nothing")
            continue
        got = audit(mutated)
        if expected not in got:
            failures.append(f"{mut_id}: expected {expected!r}, got {got}")

    # Coverage from every label the CLEAN baseline EVALUATES — not from mutation
    # output, which cannot see an assertion no mutation trips (that gap left
    # `checkout-present[*]` asserted, unmutated, and the self-test still green).
    covered = {_family(e) for _, e, _ in _MUTATIONS}
    uncovered = sorted({_family(i) for i in evaluated} - covered)
    if uncovered:
        failures.append(f"assertion families evaluated but unmutated: {uncovered}")

    if failures:
        print(f"\u2716 self-test: {len(failures)} problem(s):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print(f"\u2713 self-test: baseline clean; {len(_MUTATIONS)} mutations each caught; "
          f"{len(covered)} assertion families mutation-proven")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    # The mutation matrix runs on EVERY invocation, not behind an opt-in flag: an
    # earlier draft wired `--self-test` nowhere, so every assertion it claimed to
    # prove was decorative and `audit()` could be weakened unnoticed.
    if self_test() != 0:
        return 1
    if not WORKFLOW.is_file():
        print(f"✖ {WORKFLOW} not found", file=sys.stderr)
        return 1
    violations = audit(WORKFLOW.read_text(encoding="utf-8"))
    if violations:
        print(f"✖ {len(violations)} posture violation(s):", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print("✓ build-check.yml posture OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
