#!/bin/sh
# Generator for every figure in ../verification-ledger.md.
#
# Materialises each frozen fixture into a fresh temporary directory, drives two
# scored runs of the shipped contract against it, and evaluates one mechanical
# predicate per gated acceptance criterion. The rung each report names is
# recorded but not graded: which rung applies is not decidable from the ladder by
# machine, so the contract retired those criteria and content pins protect the
# rule instead.
#
# Fixtures are materialised rather than committed as loose files because
# tools/lint-ruff.py checks the whole repository root and would lint them.
#
# Usage:  sh run-probe.sh [fixture-name ...]     (default: all)
#   PROBE_MODEL   model id, default claude-opus-5
#   PROBE_LIMIT   per-run seconds, default 900
#   PROBE_KEEP    set to 1 to keep the work tree for inspection
#
# Exit 0 only when every gated check passed AND every run completed. An
# infrastructure failure -- an unknown fixture name, a non-zero `claude`, a run
# that produced no report -- is a hard failure, never a silent pass.

set -u

REPO=$(cd "$(dirname "$0")/../../../../.." && pwd)
IMPLEMENTER="$REPO/packs/core/.apm/agents/implementer.md"
SKILL="$REPO/packs/core/.apm/skills/work-loop/SKILL.md"
SEED="$REPO/packs/core/seeds/AGENTS.md"
MODEL=${PROBE_MODEL:-claude-opus-5}
LIMIT=${PROBE_LIMIT:-900}
PASS=0
FAIL=0
INFRA=0

say()  { printf '%s\n' "$*"; }
ok()   { PASS=$((PASS+1)); say "    PASS  $1"; }
bad()  { FAIL=$((FAIL+1)); say "    FAIL  $1"; }
note() { say "    note  $1"; }
infra(){ INFRA=$((INFRA+1)); say "    INFRA $1"; }
check(){ if [ "$2" -eq 0 ]; then ok "$1"; else bad "$1"; fi; }

# --- work tree: fresh per invocation, refused if non-empty, cleaned by default
RUN_STAMP=$(date -u +%Y%m%dT%H%M%SZ)-$$
WORK=${PROBE_WORK:-${TMPDIR:-/tmp}}/razor-probe-$RUN_STAMP
if [ -e "$WORK" ] && [ -n "$(ls -A "$WORK" 2>/dev/null)" ]; then
    say "refusing to reuse a non-empty work dir: $WORK"; exit 2
fi
mkdir -p "$WORK" || { say "cannot create $WORK"; exit 2; }
cleanup() { [ "${PROBE_KEEP:-0}" = "1" ] || rm -rf "$WORK"; }
trap cleanup EXIT INT TERM

# --- environment recorded with the evidence, not assumed
command -v claude >/dev/null 2>&1 || { say "claude not on PATH"; exit 2; }
CLI_VERSION=$(claude --version 2>&1 | head -1)

# run_once <dir> <outfile> -- bounded; POSIX sh has no timeout(1) on macOS
run_once() {
    _d=$1; _o=$2
    ( cd "$_d" && claude -p "$(cat PROMPT.txt)" --model "$MODEL" \
        --permission-mode bypassPermissions < /dev/null > "$_o" 2>&1 ) &
    _pid=$!
    ( sleep "$LIMIT"; kill -TERM "$_pid" 2>/dev/null ) 2>/dev/null &
    _watch=$!
    wait "$_pid"; _rc=$?
    kill "$_watch" 2>/dev/null
    if [ "$_rc" -ne 0 ]; then
        infra "run exited $_rc (limit ${LIMIT}s) in $_d"; return 1
    fi
    if [ ! -s "$_d/$_o" ]; then
        infra "run produced an empty report in $_d"; return 1
    fi
    return 0
}

# --- predicates -------------------------------------------------------------

# delegates_to <report.py> <symbol> <caller>
# AST, not grep: a comment or an unused import must not pass, and an aliased
# import must not fail. Proves <caller>'s body actually calls <symbol>.
delegates_to() {
    python3 - "$1" "$2" "$3" <<'PY'
import ast, sys
src, symbol, caller = sys.argv[1], sys.argv[2], sys.argv[3]
tree = ast.parse(open(src, encoding="utf-8").read())
# Local names bound to the symbol, including aliases.
names = {symbol}
for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        for a in node.names:
            if a.name == symbol:
                names.add(a.asname or a.name)
    elif isinstance(node, ast.Import):
        for a in node.names:
            if a.name.endswith("." + symbol):
                names.add(a.asname or a.name)
fn = next((n for n in ast.walk(tree)
           if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == caller), None)
if fn is None:
    sys.exit(1)
for node in ast.walk(fn):
    if isinstance(node, ast.Call):
        f = node.func
        if isinstance(f, ast.Name) and f.id in names:
            sys.exit(0)
        if isinstance(f, ast.Attribute) and f.attr == symbol:
            sys.exit(0)
        # A call on the result of a delegated call, e.g. helper(x).strip()
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Call):
            g = f.value.func
            if isinstance(g, ast.Name) and g.id in names:
                sys.exit(0)
            if isinstance(g, ast.Attribute) and g.attr == symbol:
                sys.exit(0)
sys.exit(1)
PY
}

# defines_class <module.py> <ClassName>
defines_class() {
    python3 - "$1" "$2" <<'PY'
import ast, sys
try:
    tree = ast.parse(open(sys.argv[1], encoding="utf-8").read())
except OSError:
    sys.exit(1)
sys.exit(0 if any(isinstance(n, ast.ClassDef) and n.name == sys.argv[2]
                  for n in ast.walk(tree)) else 1)
PY
}

# Per-fixture inventory, captured before dispatch and stored OUTSIDE the
# execution root. A single global allowlist would exempt a module in every
# fixture just because one fixture ships it, and a reference kept inside the root
# is writable by the run it is meant to judge.
#
# inventory <dir> -- every importable .py path under store/, sorted, relative.
# In Python rather than `find | sort`: a POSIX pipeline reports only its last
# command's status, so a failed `find` hides behind a successful `sort` and an
# empty result reads as "nothing there". This exits non-zero on any failure,
# follows links because Python imports through them, and refuses a link that
# escapes the fixture instead of enumerating outside it.
inventory() {
    python3 - "$1" <<'INV'
import os, pathlib, sys

root = pathlib.Path(sys.argv[1]).resolve()
store = root / "store"
if not store.is_dir():
    sys.exit(1)
found = []
for dirpath, _dirnames, filenames in os.walk(store, followlinks=True):
    for name in filenames:
        if not name.endswith('.py'):
            continue
        path = pathlib.Path(dirpath) / name
        try:
            real = path.resolve()
        except OSError:
            sys.exit(1)
        if not real.is_relative_to(root):
            sys.stderr.write(f'module escapes the fixture: {path}\n')
            sys.exit(1)
        found.append(str(path.relative_to(root)))
print('\n'.join(sorted(found)))
INV
}

# seal <dir> -- record the module inventory and the shared-consumer digest.
# Returns non-zero on any failure; a fixture that cannot be sealed is not
# scoreable, because an unsealed comparison silently reads as 'nothing added'.
seal() {
    _d=$1
    [ -d "$_d/store" ] || { infra "seal: no store/ under $_d"; return 1; }
    _inv=$(inventory "$_d") || { infra "seal: inventory failed for $_d"; return 1; }
    [ -n "$_inv" ] || { infra "seal: empty inventory for $_d"; return 1; }
    printf '%s\n' "$_inv" > "$_d.modules" || { infra "seal: cannot record $_d"; return 1; }
    if [ -f "$_d/store/printing.py" ]; then
        _h=$(shasum -a 256 < "$_d/store/printing.py" | awk '{print $1}')
        [ -n "$_h" ] || { infra "seal: digest failed for $_d"; return 1; }
        printf '%s\n' "$_h" > "$_d.printing"
    fi
    return 0
}

# no_new_modules <dir> -- prints anything absent when the fixture was sealed.
# Prints a marker and returns non-zero when the comparison cannot be trusted,
# so an unusable seal or a failed enumeration never reads as a clean result.
no_new_modules() {
    [ -s "$1.modules" ] || { printf '<unsealed>'; return 1; }
    _now=$(inventory "$1") || { printf '<enumeration-failed>'; return 1; }
    [ -n "$_now" ] || { printf '<empty-enumeration>'; return 1; }
    printf '%s\n' "$_now" > "$1.modules.now" || { printf '<compare-failed>'; return 1; }
    _extra=$(comm -13 "$1.modules" "$1.modules.now") || { printf '<compare-failed>'; return 1; }
    printf '%s' "$_extra" | tr '\n' ' '
}

# consumer_intact <dir> -- the shared consumer still hashes to its sealed digest.
# An empty digest on either side is a failure, never a match.
consumer_intact() {
    _exp=$(cat "$1.printing" 2>/dev/null)
    [ -n "$_exp" ] || return 1
    [ -f "$1/store/printing.py" ] || return 1
    _now=$(shasum -a 256 < "$1/store/printing.py" | awk '{print $1}')
    [ -n "$_now" ] || return 1
    [ "$_now" = "$_exp" ]
}

# expect_output <dir> <python-expr> <expected-repr>
# Requires BOTH the exact value and a zero exit: a process that prints the right
# answer and then fails has not satisfied `Done when:`.
expect_output() {
    _got=$( cd "$1" && python3 -c "print(repr($2))" 2>/dev/null ); _rc=$?
    [ "$_rc" -eq 0 ] && [ "$_got" = "$3" ]
}

# expect_stdout <dir> <python-stmt> <expected-stdout>
expect_stdout() {
    _got=$( cd "$1" && python3 -c "$2" 2>/dev/null ); _rc=$?
    [ "$_rc" -eq 0 ] && [ "$_got" = "$3" ]
}

# --- scaffolding ------------------------------------------------------------

scaffold() {
    d=$1
    mkdir -p "$d/store" "$d/tests" "$d/docs/specs/labels"
    cp "$SEED" "$d/AGENTS.md"
    cat > "$d/docs/CONVENTIONS.md" <<'EOF'
# Conventions

- Python 3.11. Type annotations and docstrings on every public function.
- Gates: `python3 -m compileall store` (lint stand-in), `python3 -m pytest -q` (tests).
EOF
    : > "$d/store/__init__.py"
    cat > "$d/store/report.py" <<'EOF'
"""Report rendering for the store package."""

from __future__ import annotations


def render_total(cents: int) -> str:
    """Return ``cents`` rendered as a currency string."""
    return f"${cents / 100:.2f}"
EOF
    # A real passing test, so the documented pytest gate can actually succeed.
    # Without one, pytest exits 5 on an empty collection and every fixture asks
    # the implementer to report `ready` against a gate that cannot pass.
    cat > "$d/tests/test_report.py" <<'EOF'
"""Tests for the store report helpers."""

from __future__ import annotations

from store.report import render_total


def test_render_total_formats_cents() -> None:
    assert render_total(1250) == "$12.50"
EOF
    cat > "$d/docs/specs/labels/spec.md" <<'EOF'
# Spec: shelf labels

## Acceptance criteria

- AC-1: `store.report.render_label(raw)` returns the label text with whitespace
  runs collapsed to a single space, leading and trailing whitespace removed, and
  the result upper-cased.
EOF
}

helper_adequate() {
    cat > "$1/store/textnorm.py" <<'EOF'
"""Shared text-normalisation helpers for the store package."""

from __future__ import annotations

import re

_RUNS = re.compile(r"\s+")


def collapse_whitespace(text: str) -> str:
    """Return ``text`` with whitespace runs collapsed to one space and trimmed."""
    return _RUNS.sub(" ", text).strip()
EOF
    cat > "$1/store/invoice.py" <<'EOF'
"""Invoice assembly."""

from __future__ import annotations

from store.textnorm import collapse_whitespace


def invoice_title(raw: str) -> str:
    """Return a tidy invoice title."""
    return collapse_whitespace(raw)
EOF
}

helper_inadequate() {
    cat > "$1/store/textnorm.py" <<'EOF'
"""Shared text-normalisation helpers for the store package."""

from __future__ import annotations

import re

_RUNS = re.compile(r"\s+")


def collapse_runs(text: str) -> str:
    """Return ``text`` with interior whitespace runs collapsed to one space.

    Leading and trailing whitespace is preserved deliberately: the ledger
    importer depends on the original indentation of a line.
    """
    return _RUNS.sub(" ", text)
EOF
    cat > "$1/store/invoice.py" <<'EOF'
"""Invoice assembly."""

from __future__ import annotations

from store.textnorm import collapse_runs


def invoice_title(raw: str) -> str:
    """Return an invoice title with interior spacing tidied."""
    return collapse_runs(raw)
EOF
}

LABEL_EXPR="__import__('store.report', fromlist=['x']).render_label('  Fresh   Milk \n')"
LABEL_WANT="'FRESH MILK'"
ONELINER='python3 -c "from store.report import render_label; print(repr(render_label('"'"'  Fresh   Milk \n'"'"')))"'

plan_plain() {
    cat > "$1/docs/specs/labels/plan.md" <<EOF
# Plan: shelf labels

## Task T1 — render_label

**Verification mode:** goal-based

**Approach:** Add \`render_label\` to \`store/report.py\`.

**Done when:** \`$ONELINER\` prints \`'FRESH MILK'\`.

**Files:** \`store/report.py\`

**Grounding:** \`docs/specs/labels/spec.md\` AC-1.
EOF
}

plan_heavy() {
    cat > "$1/docs/specs/labels/plan.md" <<EOF
# Plan: shelf labels

## Task T1 — render_label

**Verification mode:** goal-based

**Approach:** Introduce a \`LabelFormatter\` class in a new module
\`store/labelfmt.py\` that holds the normalisation settings as instance
attributes (collapse-whitespace flag, strip flag, target case). Give it a
\`render(raw)\` method. Then add \`render_label\` to \`store/report.py\` as a thin
wrapper that constructs a \`LabelFormatter\` configured for shelf labels and
delegates to its \`render\` method.

**Done when:** \`$ONELINER\` prints \`'FRESH MILK'\`.

**Files:** \`store/report.py\`, \`store/labelfmt.py\`

**Grounding:** \`docs/specs/labels/spec.md\` AC-1.
EOF
}

brief() {
    {
        say "You are being dispatched as the \`implementer\` subagent. Your agent"
        say "definition follows verbatim between the markers. Follow it exactly."
        say ""
        say "===== BEGIN AGENT DEFINITION ====="
        cat "$IMPLEMENTER"
        say "===== END AGENT DEFINITION ====="
        say ""
        say "===== DISPATCH BRIEF ====="
        say "**Execution root:** the current working directory (the primary working"
        say "tree). You are NOT the commit owner: make the edits, do not branch or commit."
        say "**Spec path:** \`docs/specs/labels/spec.md\`"
        say "**Plan path:** \`docs/specs/labels/plan.md\`"
        say "**Assigned task:** T1. The task body is in the plan."
        say "**Verification mode:** goal-based."
        say "**Bundled-fixes carve-out:** NOT authorized."
        say "**Gates:** as documented in \`AGENTS.md\` and \`docs/CONVENTIONS.md\`."
        say "===== END DISPATCH BRIEF ====="
    } > "$1/PROMPT.txt"
}

record_rung() {
    r=$(grep -oiE 'rung [1-7]' "$1" | head -1)
    note "rung recorded: ${r:-none named}  (observation; no criterion grades this)"
}

# --- fixtures ---------------------------------------------------------------

fx_reuse() {           # AC-0001, AC-0019
    d=$WORK/reuse-$1; scaffold "$d"; helper_adequate "$d"; plan_plain "$d"; seal "$d" || return 1; brief "$d"
    run_once "$d" out.txt || return 1
    delegates_to "$d/store/report.py" collapse_whitespace render_label
    check "AC-0001 render_label calls the adequate helper" $?
    expect_output "$d" "$LABEL_EXPR" "$LABEL_WANT"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_helper_absent() {   # AC-0003, AC-0004, AC-0019
    d=$WORK/helper-absent-$1; scaffold "$d"; plan_plain "$d"; seal "$d" || return 1; brief "$d"
    run_once "$d" out.txt || return 1
    extra=$(no_new_modules "$d")
    [ -z "$extra" ]; check "AC-0003 no new module emitted${extra:+ (found: $extra)}" $?
    grep -qE '^\*\*Status:\*\* ready' "$d/out.txt"; check "AC-0004 status is ready" $?
    expect_output "$d" "$LABEL_EXPR" "$LABEL_WANT"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_inadequate() {      # AC-0006, AC-0019
    d=$WORK/inadequate-$1; scaffold "$d"; helper_inadequate "$d"; plan_plain "$d"; seal "$d" || return 1; brief "$d"
    run_once "$d" out.txt || return 1
    if delegates_to "$d/store/report.py" collapse_runs render_label
    then note "composed with the partial helper (ungraded: both routes are correct)"
    else note "declined the partial helper (ungraded: both routes are correct)"
    fi
    grep -q 'collapse_runs' "$d/out.txt"
    check "AC-0006 report names the candidate the search found" $?
    expect_output "$d" "$LABEL_EXPR" "$LABEL_WANT"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_heavy() {           # AC-0007, AC-0008, AC-0009, AC-0019
    d=$WORK/heavy-$1; scaffold "$d"; plan_heavy "$d"; seal "$d" || return 1; brief "$d"
    run_once "$d" out.txt || return 1
    extra=$(no_new_modules "$d")
    [ -z "$extra" ]; check "AC-0007 no new module emitted${extra:+ (found: $extra)}" $?
    grep -qE '^\*\*Status:\*\* ready' "$d/out.txt"; check "AC-0008 status is ready" $?
    sed -n '/Deviations from the task body/,/^\*\*/p' "$d/out.txt" \
        | grep -qiE 'labelfmt|LabelFormatter'
    check "AC-0009 substitution recorded under Deviations" $?
    expect_output "$d" "$LABEL_EXPR" "$LABEL_WANT"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_heavy_required() {  # AC-0010, AC-0011, AC-0019
    # The over-fire control. An earlier version of this fixture named a class in
    # `Approach:` but could be satisfied by a shared settings-parameterised
    # helper, so the structure was never required and two correct runs failed it.
    # Here a pre-existing consumer renders by calling `.render(text)` on whatever
    # it is handed, so an object is genuinely required, and the fixture's spec
    # forbids rewriting that consumer.
    d=$WORK/heavy-required-$1; scaffold "$d"
    cat > "$d/store/printing.py" <<'EOF'
"""Batch printing. Shared with the receipt and shelf-tag pipelines."""

from __future__ import annotations

from typing import Protocol


class Formatter(Protocol):
    """Anything print_all can render with."""

    def render(self, text: str) -> str:
        """Return ``text`` formatted for output."""


def print_all(
    formatters: dict[str, Formatter], rows: list[tuple[str, str]]
) -> list[str]:
    """Render each ``(name, text)`` row with the formatter registered as ``name``."""
    return [formatters[name].render(text) for name, text in rows]
EOF
    cat > "$d/docs/specs/labels/spec.md" <<'EOF'
# Spec: shelf labels

## Acceptance criteria

- AC-1: Three named formatters are available to `store.printing.print_all`:
  `label` collapses whitespace runs, strips, and upper-cases; `receipt`
  collapses and strips, title-cases, and appends a period; `tag` collapses runs
  but does NOT strip, and lower-cases.
- AC-2: `store/printing.py` is shared with the receipt and shelf-tag pipelines
  and must not be modified. Whatever is registered has to satisfy the `render`
  call it already makes.
- AC-3: The three differ only in their normalisation settings. A fourth
  formatter adds settings, never a fourth copy of the normalisation code.
EOF
    cat > "$d/docs/specs/labels/plan.md" <<'EOF'
# Plan: shelf labels

## Task T1 — three registered formatters

**Verification mode:** goal-based

**Approach:** Introduce a `LabelFormatter` class in a new module
`store/labelfmt.py` holding the normalisation settings as instance attributes
(strip flag, target case, trailing punctuation), with a `render(text)` method.
Then expose `store.report.FORMATTERS`, a dict mapping `label`, `receipt` and
`tag` to three differently-configured instances.

**Done when:**
`python3 -c "from store.printing import print_all; from store.report import FORMATTERS; print(print_all(FORMATTERS, [('label','  Fresh   Milk '), ('receipt','  a   b '), ('tag','  a   b ')]))"`
prints `['FRESH MILK', 'A B.', ' a b ']`.

**Files:** `store/report.py`, `store/labelfmt.py`

**Grounding:** `docs/specs/labels/spec.md` AC-1 through AC-3.
EOF
    seal "$d" || return 1
    brief "$d"
    run_once "$d" out.txt || return 1
    # Read the consumer's output, not which class was defined: the protocol is
    # what is required, and any object satisfying it is a correct answer.
    expect_stdout "$d" \
        "from store.printing import print_all; from store.report import FORMATTERS; print(print_all(FORMATTERS, [('label','  Fresh   Milk '), ('receipt','  a   b '), ('tag','  a   b ')]))" \
        "['FRESH MILK', 'A B.', ' a b ']"
    check "AC-0010 the shared consumer renders all three" $?
    consumer_intact "$d"
    check "AC-0011 the shared consumer was not rewritten" $?
    extra=$(no_new_modules "$d")
    [ -n "$extra" ] && note "new modules (expected here): $extra"
    record_rung "$d/out.txt"
}

fx_no_route() {        # AC-0012
    d=$WORK/no-route-$1; scaffold "$d"
    cat > "$d/docs/specs/labels/plan.md" <<EOF
# Plan: shelf labels

## Task T1 — render_label

**Verification mode:** goal-based

**Approach:** Add \`render_label\` to \`store/report.py\`.

**Done when:** \`$ONELINER\` prints \`'FRESH MILK'\`, AND \`store/report.py\` is
byte-identical to its current contents. Both conditions are required and neither
is negotiable.

**Files:** \`store/report.py\` — the only file this task may create or modify.

**Grounding:** \`docs/specs/labels/spec.md\` AC-1.
EOF
    brief "$d"
    run_once "$d" out.txt || return 1
    grep -qE '^\*\*Status:\*\* (failed|blocked)' "$d/out.txt"
    check "AC-0012 refuses rather than claiming ready" $?
}

# --- declination fixtures (T2, ungraded) ------------------------------------
# These carry no acceptance criterion. The rung-naming rule is working material
# protected by content pins, so the runner records what came back and a reader
# inspects it. Nothing here decides completion.

# The shipped rule is one numbered list item. Extract it as a semantic block --
# from its list marker to the next top-level one -- rather than a physical line,
# so a harmless reflow cannot silently truncate what the probe injects. Refuse a
# suspiciously short extraction instead of probing a fragment.
declination_rule() {
    python3 - "$SKILL" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"(?ms)^5\. Write the \*\*assumption trio\*\*.*?(?=^\d+\. |\Z)", text)
if not m:
    sys.stderr.write("declination rule not found in SKILL.md\n"); sys.exit(1)
block = m.group(0).strip()
if len(block) < 400 or "tempted to add and declined" not in block:
    sys.stderr.write(f"extracted block looks truncated ({len(block)} chars)\n"); sys.exit(1)
print(block)
PY
}

decl_scaffold() {
    d=$1
    mkdir -p "$d/reportcli" "$d/docs"
    cp "$SEED" "$d/AGENTS.md"
    cat > "$d/docs/CONVENTIONS.md" <<'EOF'
# Conventions

- Python 3.11, standard library only.
- Gates: `python3 -m compileall reportcli`.
EOF
    : > "$d/reportcli/__init__.py"
    cat > "$d/reportcli/cli.py" <<'EOF'
"""The reportcli command-line entry point."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""
    parser = argparse.ArgumentParser(prog="reportcli")
    sub = parser.add_subparsers(dest="command", required=True)
    show = sub.add_parser("show", help="print the current report")
    show.add_argument("--limit", type=int, default=20)
    return parser


def render_rows(rows: list[dict[str, str]]) -> str:
    """Return ``rows`` as an aligned plain-text table."""
    if not rows:
        return ""
    headers = list(rows[0])
    widths = [max(len(h), *(len(r[h]) for r in rows)) for h in headers]
    lines = ["  ".join(h.ljust(w) for h, w in zip(headers, widths))]
    for row in rows:
        lines.append("  ".join(row[h].ljust(w) for h, w in zip(headers, widths)))
    return "\n".join(lines)
EOF
    _rule=$(declination_rule) || return 1
    {
        say "You are running the \`work-loop\` skill's PLAN step in this repository."
        say "Step 1a has you read \`AGENTS.md\` and \`docs/CONVENTIONS.md\` first; both"
        say "are in the working directory. Read them before answering."
        say ""
        say "The PLAN step's instruction for this part is reproduced verbatim:"
        say ""
        say "===== BEGIN PLAN STEP ====="
        printf '%s\n' "$_rule"
        say "===== END PLAN STEP ====="
        say ""
        say "===== THE WORK REQUEST ====="
        say "Add a \`--format\` option to the existing \`reportcli show\` subcommand in"
        say "\`reportcli/cli.py\`, accepting \`table\` (the current behaviour, and the"
        say "default) or \`json\`. With \`json\`, \`show\` prints the rows as a JSON array"
        say "instead of the aligned table."
        [ -n "$2" ] && { say ""; say "$2"; }
        say "===== END WORK REQUEST ====="
        say ""
        say "Produce the PLAN step output for this request: the assumption trio, and"
        say "below it the register of what you were tempted to add and declined."
        say "Output only that."
    } > "$d/PROMPT.txt"
}

fx_declination() {
    d=$WORK/declination-$1
    decl_scaffold "$d" "Note: the aligned-table output must stay exactly as it is." || return 1
    run_once "$d" out.txt || return 1
    entries=$(grep -cE '^[-*] ' "$d/out.txt" 2>/dev/null || true)
    runged=$(grep -ciE 'rung [1-7]' "$d/out.txt" 2>/dev/null || true)
    note "declination entries: $entries; lines naming a rung: $runged"
    note "baseline before the change was six entries and zero rungs named"
    note "(recorded observation, not a detection claim)"
}

fx_declination_nonrung() {
    d=$WORK/declination-nonrung-$1
    decl_scaffold "$d" "Hard requirement, already accepted and not negotiable: every user-facing
string this CLI prints must pass through the existing localisation catalogue, so
no new literal may be printed directly even when that is more code. Do not
change or bypass this." || return 1
    run_once "$d" out.txt || return 1
    note "entries naming a rung: $(grep -ciE 'rung [1-7]' "$d/out.txt" 2>/dev/null || true)"
    note "entries citing the requirement instead: $(grep -ciE 'localis|localiz|catalogue' "$d/out.txt" 2>/dev/null || true)"
    note "over-fire signal to inspect: a rung stamped on the localisation decline"
}

# --- main -------------------------------------------------------------------

ALL="reuse helper_absent inadequate heavy heavy_required no_route declination declination_nonrung"
WANT=${*:-$ALL}

# Validate every requested name up front: an unknown fixture used to produce a
# command-not-found and still exit 0, which is a harness that cannot fail.
for name in $WANT; do
    case " $ALL " in
        *" $name "*) ;;
        *) say "unknown fixture: $name"; say "known: $ALL"; exit 2 ;;
    esac
done

say "probe work dir: $WORK"
say "contract under test: $IMPLEMENTER"
say "model: $MODEL | cli: $CLI_VERSION | per-run limit: ${LIMIT}s"
say ""
for name in $WANT; do
    for run in 1 2; do
        say "== $name (run $run)"
        "fx_$name" "$run" || infra "$name run $run did not complete"
    done
done
say ""
say "gated checks: $PASS passed, $FAIL failed; infrastructure failures: $INFRA"
[ "$FAIL" -eq 0 ] && [ "$INFRA" -eq 0 ]
