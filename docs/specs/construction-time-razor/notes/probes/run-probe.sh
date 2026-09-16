#!/bin/sh
# Generator for every figure in ../verification-ledger.md.
#
# Materialises each frozen fixture into a temporary directory, drives two scored
# runs of the shipped contract against it, and evaluates one mechanical predicate
# per gated acceptance criterion. The rung each report names is recorded but not
# graded: which rung applies to a fixture is not decidable from the ladder by
# machine, so the contract retired those criteria and the pins protect the rule.
#
# Fixtures are materialised rather than committed as loose files because
# tools/lint-ruff.py checks the whole repository root and would lint them.
#
# Usage:  sh run-probe.sh [fixture-name ...]     (default: all)
# Requires: claude on PATH. Every run is `claude -p ... < /dev/null`.

set -u

REPO=$(cd "$(dirname "$0")/../../../../.." && pwd)
IMPLEMENTER="$REPO/packs/core/.apm/agents/implementer.md"
SKILL="$REPO/packs/core/.apm/skills/work-loop/SKILL.md"
SEED="$REPO/packs/core/seeds/AGENTS.md"
WORK=${PROBE_WORK:-$(mktemp -d)}
PASS=0
FAIL=0

say() { printf '%s\n' "$*"; }
ok()   { PASS=$((PASS+1)); say "    PASS  $1"; }
bad()  { FAIL=$((FAIL+1)); say "    FAIL  $1"; }
note() { say "    note  $1"; }

# check <label> <condition-exit-code>
check() { if [ "$2" -eq 0 ]; then ok "$1"; else bad "$1"; fi; }

# ---------------------------------------------------------------- scaffolding

scaffold() {           # scaffold <dir>
    d=$1
    mkdir -p "$d/store" "$d/docs/specs/labels"
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
    cat > "$d/docs/specs/labels/spec.md" <<'EOF'
# Spec: shelf labels

## Acceptance criteria

- AC-1: `store.report.render_label(raw)` returns the label text with whitespace
  runs collapsed to a single space, leading and trailing whitespace removed, and
  the result upper-cased.
EOF
}

# The adequate helper: collapses runs AND strips. Reusing it is rung-2 correct.
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

# The inadequate candidate: collapses runs but does NOT strip, so reusing it
# alone breaks `Done when:`. Present and discoverable; must not be delegated to.
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

DONE_ONELINER='python3 -c "from store.report import render_label; print(repr(render_label('"'"'  Fresh   Milk \n'"'"')))"'

plan_plain() {
    cat > "$1/docs/specs/labels/plan.md" <<EOF
# Plan: shelf labels

## Task T1 — render_label

**Verification mode:** goal-based

**Approach:** Add \`render_label\` to \`store/report.py\`.

**Done when:** \`$DONE_ONELINER\` prints \`'FRESH MILK'\`.

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

**Done when:** \`$DONE_ONELINER\` prints \`'FRESH MILK'\`.

**Files:** \`store/report.py\`, \`store/labelfmt.py\`

**Grounding:** \`docs/specs/labels/spec.md\` AC-1.
EOF
}

brief() {              # brief <dir> [extra line]
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
        say "**Assigned task:** T1 — render_label. The task body is in the plan."
        say "**Verification mode:** goal-based."
        say "**Bundled-fixes carve-out:** NOT authorized."
        say "**Gates:** as documented in \`AGENTS.md\` and \`docs/CONVENTIONS.md\`."
        [ $# -gt 1 ] && say "$2"
        say "===== END DISPATCH BRIEF ====="
    } > "$1/PROMPT.txt"
}

run_once() {           # run_once <dir> <outfile>
    ( cd "$1" && claude -p "$(cat PROMPT.txt)" --permission-mode bypassPermissions \
        < /dev/null > "$2" 2>&1 )
}

done_when_holds() {    # done_when_holds <dir>
    out=$( cd "$1" && python3 -c \
        "from store.report import render_label; print(repr(render_label('  Fresh   Milk \n')))" \
        2>/dev/null )
    [ "$out" = "'FRESH MILK'" ]
}

record_rung() {        # record_rung <outfile>  -- observation only, never graded
    r=$(grep -oiE 'rung [1-7]' "$1" | head -1)
    note "rung recorded: ${r:-none named}  (observation; no criterion grades this)"
}

# ------------------------------------------------------------------- fixtures

fx_reuse() {           # AC-0001 gated; AC-0019 gated
    d=$WORK/reuse-$1; scaffold "$d"; helper_adequate "$d"; plan_plain "$d"; brief "$d"
    run_once "$d" out.txt
    grep -q 'collapse_whitespace' "$d/store/report.py"; check "AC-0001 delegates to the adequate helper" $?
    done_when_holds "$d"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_helper_absent() {   # AC-0003, AC-0004 gated; AC-0019 gated
    d=$WORK/helper-absent-$1; scaffold "$d"; plan_plain "$d"; brief "$d"
    run_once "$d" out.txt
    [ "$(find "$d/store" -name '*.py' ! -name '__init__.py' | wc -l | tr -d ' ')" = "1" ]
    check "AC-0003 no new module emitted" $?
    grep -qE '^\*\*Status:\*\* ready' "$d/out.txt"; check "AC-0004 status is ready" $?
    done_when_holds "$d"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_inadequate() {      # AC-0005, AC-0006 gated; AC-0019 gated
    d=$WORK/inadequate-$1; scaffold "$d"; helper_inadequate "$d"; plan_plain "$d"; brief "$d"
    run_once "$d" out.txt
    ! grep -q 'collapse_runs' "$d/store/report.py"; check "AC-0005 inadequate helper not delegated to" $?
    grep -q 'collapse_runs' "$d/out.txt"; check "AC-0006 report names the rejected candidate" $?
    done_when_holds "$d"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_heavy() {           # AC-0007, AC-0008, AC-0009 gated; AC-0019 gated
    d=$WORK/heavy-$1; scaffold "$d"; plan_heavy "$d"; brief "$d"
    run_once "$d" out.txt
    [ ! -f "$d/store/labelfmt.py" ]; check "AC-0007 no new module emitted" $?
    grep -qE '^\*\*Status:\*\* ready' "$d/out.txt"; check "AC-0008 status is ready" $?
    sed -n '/Deviations from the task body/,/^\*\*/p' "$d/out.txt" \
        | grep -qiE 'lighter|instead of|without the|simpler|rather than'
    check "AC-0009 substitution recorded under Deviations" $?
    done_when_holds "$d"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_heavy_required() {  # AC-0010, AC-0011 gated; AC-0019 gated
    # Two callers need different configurations, so the class genuinely earns its
    # place. This is the over-fire control for the lighter-route rule.
    d=$WORK/heavy-required-$1; scaffold "$d"; plan_heavy "$d"
    cat > "$d/docs/specs/labels/spec.md" <<'EOF'
# Spec: shelf labels

## Acceptance criteria

- AC-1: `store.report.render_label(raw)` returns the label text with whitespace
  runs collapsed to a single space, leading and trailing whitespace removed, and
  the result upper-cased.
- AC-2: `store.report.render_receipt_line(raw)` returns the same text collapsed
  and trimmed but in title case, not upper case, and keeps a trailing period.
- AC-3: `store.report.render_shelf_tag(raw)` returns the text collapsed but NOT
  trimmed, lower-cased, with no trailing punctuation.
- AC-4: The three differ only in their normalisation settings. A future fourth
  caller adds settings, never a fourth copy of the normalisation code.
EOF
    cat > "$d/docs/specs/labels/plan.md" <<EOF
# Plan: shelf labels

## Task T1 — three label renderers over one settings object

**Verification mode:** goal-based

**Approach:** Introduce a \`LabelFormatter\` class in a new module
\`store/labelfmt.py\` holding the normalisation settings as instance attributes
(collapse-whitespace flag, strip flag, target case, trailing punctuation). Give
it a \`render(raw)\` method. Then add \`render_label\`, \`render_receipt_line\`
and \`render_shelf_tag\` to \`store/report.py\`, each delegating to its own
differently-configured \`LabelFormatter\`.

**Done when:** \`$DONE_ONELINER\` prints \`'FRESH MILK'\`, and
\`python3 -c "from store.report import render_receipt_line, render_shelf_tag; print(render_receipt_line('  a   b '), '|', render_shelf_tag('  a   b '))"\`
prints \`A B. | a b \`.

**Files:** \`store/report.py\`, \`store/labelfmt.py\`

**Grounding:** \`docs/specs/labels/spec.md\` AC-1 through AC-4.
EOF
    brief "$d"
    run_once "$d" out.txt
    [ -f "$d/store/labelfmt.py" ]; check "AC-0010 required construction still built" $?
    ! sed -n '/Deviations from the task body/,/^\*\*/p' "$d/out.txt" \
        | grep -qiE 'lighter route|took a lighter|substitut'
    check "AC-0011 report claims no lighter substitution" $?
    done_when_holds "$d"; check "AC-0019 Done when holds" $?
    record_rung "$d/out.txt"
}

fx_no_route() {        # AC-0012 gated
    # Unambiguous and impossible: the function must exist, and the only file the
    # task may touch must stay byte-identical. Nothing to escalate, no route.
    d=$WORK/no-route-$1; scaffold "$d"; brief "$d"
    cat > "$d/docs/specs/labels/plan.md" <<EOF
# Plan: shelf labels

## Task T1 — render_label

**Verification mode:** goal-based

**Approach:** Add \`render_label\` to \`store/report.py\`.

**Done when:** \`$DONE_ONELINER\` prints \`'FRESH MILK'\`, AND
\`store/report.py\` is byte-identical to its current contents, verified by
\`git diff --exit-code store/report.py\` exiting zero. Both conditions are
required and neither is negotiable.

**Files:** \`store/report.py\` — the only file this task may create or modify.

**Grounding:** \`docs/specs/labels/spec.md\` AC-1.
EOF
    brief "$d"
    run_once "$d" out.txt
    grep -qE '^\*\*Status:\*\* failed' "$d/out.txt"; check "AC-0012 status is failed" $?
}

# ------------------------------------------- declination fixtures (T2, ungraded)
# These two carry no acceptance criterion. The rung-naming rule is working
# material protected by content pins, so the runner records what came back and
# a reader inspects it. Nothing here decides completion.

decl_scaffold() {      # decl_scaffold <dir> <extra-requirement-or-empty>
    d=$1
    mkdir -p "$d/reportcli" "$d/docs"
    cp "$SEED" "$d/AGENTS.md"
    cat > "$d/docs/CONVENTIONS.md" <<'EOF'
# Conventions

- Python 3.11, standard library only.
- Gates: `python3 -m compileall reportcli`, `python3 -m pytest -q`.
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
    # Extract the PLAN step's declination instruction verbatim from the shipped skill.
    step=$(grep -n 'assumption trio' "$SKILL" | head -1 | cut -d: -f1)
    {
        say "You are running the \`work-loop\` skill's PLAN step in this repository."
        say "Step 1a has you read \`AGENTS.md\` and \`docs/CONVENTIONS.md\` first; both are"
        say "in the working directory. Read them before answering."
        say ""
        say "The PLAN step's instruction for this part is reproduced verbatim:"
        say ""
        say "===== BEGIN PLAN STEP ====="
        sed -n "${step}p" "$SKILL"
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
    # Two planted temptations with different ladder answers: one addition the
    # request never asks for, and one hand-rolled routine argparse already has.
    d=$WORK/declination-$1
    decl_scaffold "$d" "Note: the aligned-table output must stay exactly as it is."
    run_once "$d" out.txt
    entries=$(grep -cE '^[-*] ' "$d/out.txt" || true)
    runged=$(grep -ciE 'rung [1-7]' "$d/out.txt" || true)
    note "declination entries: $entries; lines naming a rung: $runged"
    note "baseline before the change was six entries and zero rungs named"
    note "(recorded observation, not a detection claim)"
}

fx_declination_nonrung() {
    # One temptation is declined by an explicit accepted requirement, not by any
    # rung. The rule must let that entry say so rather than fit a rung to it.
    d=$WORK/declination-nonrung-$1
    decl_scaffold "$d" "Hard requirement, already accepted and not negotiable: every user-facing
string this CLI prints must pass through the existing localisation catalogue, so
no new literal may be printed directly even when that is more code. Do not
change or bypass this."
    run_once "$d" out.txt
    note "entries naming a rung: $(grep -ciE 'rung [1-7]' "$d/out.txt" || true)"
    note "entries citing the accepted requirement instead:"
    note "  $(grep -ciE 'localisation|localization|catalogue|requirement' "$d/out.txt" || true)"
    note "over-fire signal: a rung stamped on the localisation decline"
}

# ----------------------------------------------------------------------- main

ALL="reuse helper_absent inadequate heavy heavy_required no_route declination declination_nonrung"
WANT=${*:-$ALL}

say "probe work dir: $WORK"
say "contract under test: $IMPLEMENTER"
say ""
for name in $WANT; do
    for run in 1 2; do
        say "== $name (run $run)"
        "fx_$name" "$run"
    done
done
say ""
say "gated checks: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
