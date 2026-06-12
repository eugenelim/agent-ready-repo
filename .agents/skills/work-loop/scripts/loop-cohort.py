#!/usr/bin/env python3
"""loop-cohort — work-loop state owner.

Single tool the work-loop skill (and its pre-PR hook) calls for every
deterministic state mutation: phase termination checks, plan approval,
review-finding fingerprints, and the parallel-implementer cohort
(worktree add/record/merge/cleanup). The skill body and supervisor-mode
reference describe *when* to call each verb; this script is *what* runs.

Cross-platform: Python 3 stdlib only, `subprocess` for git, `os.replace`
for atomic writes, `pathlib` for paths. No shell, no bash, no PATH
dependency.

Verb surface
------------
    loop-cohort init <spec-dir>
    loop-cohort check <spec-dir> --phase {plan,implement,review}
    loop-cohort approve-plan <spec-dir>
    loop-cohort review record <spec-dir> --report <path>
                              [--fingerprint <hex> ...]
    loop-cohort worktree preflight <spec-dir> [<task-id> ...]
    loop-cohort worktree add <spec-dir> <task-id>
    loop-cohort worktree record <spec-dir> <task-id>
                                --status {ready,blocked,failed}
                                --report <path>
    loop-cohort worktree list <spec-dir>
    loop-cohort worktree merge <spec-dir>
    loop-cohort worktree cleanup <spec-dir>

Exit contract: 0 on success; non-zero with a one-line reason on stderr.
The skill treats exit-1 from `check --phase plan` with reason "plan not
approved" as the expected first-invocation cue to run the spec-mode
reviewer; any other non-zero exit terminates the loop.

Schema reference: ../assets/state.json and ../references/state-schema.md.
"""

from __future__ import annotations

import argparse
import fnmatch
import glob as _glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "state.json"


def _template_max_iterations(_fallback: int = 5) -> int:
    """The iteration cap's single source of truth is the bundled `state.json`
    template (the adopter-visible per-spec knob); ``DEFAULTS`` derives from it so
    the value lives in exactly one place. ``_fallback`` is a last resort only for
    a missing/broken template (a broken install) — not an adopter-facing knob."""
    try:
        val = json.loads(TEMPLATE_PATH.read_text()).get("max_iterations")
    except (OSError, json.JSONDecodeError):
        val = None
    if isinstance(val, int) and val > 0:
        return val
    # Broken/missing template (a broken install) — fall back, but say so, so the
    # cap silently reverting isn't a 3am mystery. `_fallback` must be hand-synced
    # with the template's shipped value (a drift test pins this).
    print(
        f"loop-cohort: warning — could not read max_iterations from {TEMPLATE_PATH}; "
        f"defaulting to {_fallback}",
        file=sys.stderr,
    )
    return _fallback


DEFAULTS = {
    "max_iterations": _template_max_iterations(),
    "token_budget_cap_pct": 0.85,
    "consecutive_same_error_threshold": 3,
}

PHASES = ("plan", "implement", "review")
WORKTREE_STATUSES = ("ready", "blocked", "failed")


def stop(reason: str, code: int = 1) -> int:
    print(f"loop-cohort: stop — {reason}", file=sys.stderr)
    return code


def state_path_for(spec_dir: Path) -> Path:
    return spec_dir / "state.json"


def read_state(spec_dir: Path) -> dict:
    path = state_path_for(spec_dir)
    if not path.exists():
        raise FileNotFoundError(f"state.json missing at {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"state.json malformed: {exc.msg} at line {exc.lineno}")
    if not isinstance(data, dict):
        raise ValueError("state.json root must be an object")
    return data


def write_state_atomic(spec_dir: Path, state: dict) -> None:
    path = state_path_for(spec_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(
        prefix=".state-", suffix=".json.tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(state, fh, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )


# ── scheduler (wave-scheduled supervisor mode) ─────────────────────────────
#
# Pure functions over a plan's `Depends on:` graph. The supervisor mode runs
# tasks in topological order *sequentially by default* on every adapter;
# parallel writes are opt-in and gated (`dispatch_decision`). `Depends on:` is
# made machine-parseable here — prose, ranges, letter-suffixed IDs, and a
# cross-spec marker.

TASK_HEADING_RE = re.compile(r"^###\s+(T\d+[a-z]?)\b", re.MULTILINE)
DEPENDS_LINE_RE = re.compile(r"^\*\*Depends on:\*\*\s*(.+)$", re.MULTILINE)
TOUCHES_LINE_RE = re.compile(r"^\*\*Touches:\*\*\s*(.+)$", re.MULTILINE)
_RANGE_RE = re.compile(r"(T\d+)\s*-\s*(T\d+)")
_TASK_ID_RE = re.compile(r"T\d+[a-z]?")
# Cross-spec deps, two accepted forms — both excluded from the intra-plan
# edge set so a cross-spec TN can't collide with a local TN:
#   marker : spec:<name>/TN              (the documented going-forward grammar)
#   legacy : `distribution-adapters` TN  (backtick-quoted spec name + id)
_CROSS_MARKER_RE = re.compile(r"spec:([A-Za-z0-9._-]+)/(T\d+[a-z]?)")
# The backtick group is a spec *name*; the negative-lookahead rejects a
# backtick-quoted bare task ID (e.g. `T1`) so a local dep written `` `T1` T2 ``
# isn't mis-read as a cross-spec dep and silently dropped from local edges.
_CROSS_LEGACY_RE = re.compile(r"`(?!T\d+[a-z]?`)([A-Za-z0-9._-]+)`\s*(T\d+[a-z]?)")


def parse_depends_on(field: str, local_task_ids):
    """Parse one `Depends on:` field body.

    Returns ``(local_edges: set[str], cross_spec: list[tuple[str, str]])``.
    Strips parenthetical prose, expands ranges (``T1-T6``), admits
    letter-suffixed IDs (``T1a``), and recognizes cross-spec deps in either
    the ``spec:<name>/TN`` marker or the legacy `` `<name>` TN `` form,
    excluding them from the local edge set.
    """
    head = field.split("(")[0]
    cross = _CROSS_MARKER_RE.findall(head) + _CROSS_LEGACY_RE.findall(head)
    cleaned = _CROSS_MARKER_RE.sub("", head)
    cleaned = _CROSS_LEGACY_RE.sub("", cleaned)
    if not cleaned.strip() or re.fullmatch(r"\s*none\s*", cleaned, re.IGNORECASE):
        return set(), cross
    ids: set[str] = set()
    for lo, hi in _RANGE_RE.findall(cleaned):
        ids.update(f"T{i}" for i in range(int(lo[1:]), int(hi[1:]) + 1))
    ids.update(_TASK_ID_RE.findall(cleaned))
    return {t for t in ids if t in local_task_ids}, cross


def parse_plan(text: str):
    """Parse a plan.md body into ``(ordered_task_ids, deps_by_task)``.

    ``ordered_task_ids`` preserves authored (file) order — required for
    forward-reference detection. ``deps_by_task[tid]`` is the set of local
    task IDs ``tid`` depends on.
    """
    matches = list(TASK_HEADING_RE.finditer(text))
    ordered = [m.group(1) for m in matches]
    taskset = set(ordered)
    deps: dict[str, set] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        dm = DEPENDS_LINE_RE.search(text[m.end():end])
        local, _ = parse_depends_on(dm.group(1), taskset) if dm else (set(), [])
        deps[m.group(1)] = local
    return ordered, deps


# ── supervisor-predict-disjointness (follow-on 3): optional `Touches:` globs ──
# A per-task `**Touches:**` line declares the file globs the task expects to
# touch. Parsed like `Depends on:` but kept in a SEPARATE accessor so
# `parse_plan`'s (ordered, deps) signature — and its ~8 callers — stay
# unchanged. The globs drive a *screen-only* pre-dispatch disjointness
# prediction in `schedule`; they never greenlight parallel (the post-write
# `git merge-tree` stays authoritative).


def parse_touches(field: str):
    """Parse one `Touches:` field body into a set of path globs. Tolerates
    trailing parenthetical prose, like `parse_depends_on`."""
    head = field.split("(")[0]
    return {g.strip() for g in head.split(",") if g.strip()}


def parse_touches_by_task(text: str):
    """Map each ``### T<n>`` task to its declared `Touches:` globs. A task with
    no `**Touches:**` line is **absent from the map** (optional — never an
    empty-set key, never an error)."""
    matches = list(TASK_HEADING_RE.finditer(text))
    out: dict[str, set] = {}
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        tm = TOUCHES_LINE_RE.search(text[m.end():end])
        if tm:
            globs = parse_touches(tm.group(1))
            if globs:
                out[m.group(1)] = globs
    return out


def _is_literal_seg(seg: str) -> bool:
    """A path segment is a *pure literal* iff it carries no glob metacharacter
    (`* ? [`). `glob.escape(seg) == seg` is the exact test."""
    return _glob.escape(seg) == seg


def _seg_provably_disjoint(x: str, y: str) -> bool:
    """Two aligned path segments are *provably* non-co-matching only when both
    are pure literals that differ, or one is a literal the other (a pattern)
    cannot `fnmatch`. Two patterns are never provably disjoint (could co-match)."""
    xl, yl = _is_literal_seg(x), _is_literal_seg(y)
    if xl and yl:
        return x != y
    if xl and not yl:
        return not fnmatch.fnmatch(x, y)
    if yl and not xl:
        return not fnmatch.fnmatch(y, x)
    return False  # both patterns → conservatively could overlap


def globs_overlap(a: str, b: str) -> bool:
    """Conservative, segment-wise: **return True (overlap) unless provably
    disjoint** (so a both-ways match-miss is NOT taken as proof of disjointness).
    `*`/`?` match within one `/`-segment and never across `/`; any `**` →
    conservatively True. Disjoint only when (a) no `**` and the segment counts
    differ, or (b) some aligned segment pair is provably disjoint."""
    if "**" in a or "**" in b:
        return True
    sa, sb = a.split("/"), b.split("/")
    if len(sa) != len(sb):
        return False  # different depth, no `**` → no shared path
    return not any(_seg_provably_disjoint(x, y) for x, y in zip(sa, sb))


def wave_touches_disjoint(per_task_globs) -> str:
    """Screen verdict for a wave from declared `Touches:` globs. Each element is
    a set of globs or a falsy value (task omitted `Touches:`). Returns ``"no"``
    if any pair of *declared* globs overlaps (even when other tasks omit
    `Touches:` — a provable overlap is always worth serializing early),
    ``"unknown"`` if no overlap is found and at least one task omitted, else
    ``"yes"``. Screen-only: never feeds the authoritative dispatch gate."""
    declared = [g for g in per_task_globs if g]
    for i in range(len(declared)):
        for j in range(i + 1, len(declared)):
            if any(globs_overlap(x, y) for x in declared[i] for y in declared[j]):
                return "no"
    if any(not g for g in per_task_globs):
        return "unknown"
    return "yes"


def build_dag(ordered, deps):
    """Return ``(indegree, children)`` over local edges only."""
    taskset = set(ordered)
    indeg = {t: 0 for t in ordered}
    children = defaultdict(list)
    for t in ordered:
        for d in deps.get(t, ()):
            if d in taskset:
                indeg[t] += 1
                children[d].append(t)
    return indeg, children


def topological_waves(ordered, deps):
    """Kahn level-ordering → ``(waves, placed_count)``.

    Each wave is a list of mutually-independent task IDs; ``placed_count <
    len(ordered)`` signals a cycle. Ties break by authored order.
    """
    indeg, children = build_dag(ordered, deps)
    order = {t: i for i, t in enumerate(ordered)}
    work = dict(indeg)
    frontier = sorted([t for t in ordered if work[t] == 0], key=order.get)
    waves = []
    while frontier:
        waves.append(frontier)
        nxt = []
        for t in frontier:
            for c in children[t]:
                work[c] -= 1
                if work[c] == 0:
                    nxt.append(c)
        frontier = sorted(nxt, key=order.get)
    return waves, sum(len(w) for w in waves)


def detect_cycles(ordered, deps):
    """Return the unschedulable task IDs (the cycle), or [] if acyclic."""
    waves, placed = topological_waves(ordered, deps)
    if placed == len(ordered):
        return []
    scheduled = {t for w in waves for t in w}
    return [t for t in ordered if t not in scheduled]


def detect_forward_refs(ordered, deps):
    """Return ``(task, dep)`` pairs whose dep is authored *later* — a valid
    edge that would run before its input in authored order."""
    order = {t: i for i, t in enumerate(ordered)}
    return [
        (t, d)
        for t in ordered
        for d in deps.get(t, ())
        if d in order and order[d] > order[t]
    ]


# The only categories whose conflicts fail *loud* (caught by merge or a
# post-merge compile) and so are eligible for opt-in parallel writes. Every
# other category — dynamic-semantic interference, shared mutable state,
# move/extract-vs-edit, migration ordering, shared fixtures — fails *silent*
# and stays serial.
SAFE_CATEGORIES = frozenset({"cannot-collide", "typed-group-b", "textual-loud"})


def dispatch_decision(categories, *, merge_tree_clean):
    """Decide whether a wave of writes may run in parallel.

    Parallel only when **every** task is in a safe category **and** the wave
    is file-disjoint (a clean ``git merge-tree``). Fail closed: any non-safe
    category, or any merge-tree conflict, serializes.
    This gates *writes* only; reviewer (read) fan-out is unaffected.
    """
    if not merge_tree_clean:
        return "serial"
    if any(c not in SAFE_CATEGORIES for c in categories):
        return "serial"
    return "parallel"


def _dispatch_rationale(categories, *, merge_tree_clean, decision, source=None) -> str:
    """Human-readable one-line rationale for a `dispatch-decision` outcome —
    the cleared-gate surface. On ``parallel`` it names the wave as
    parallel-eligible + the task count; on ``serial`` it names the
    disqualifying reason, **merge-tree conflict first** to match
    `dispatch_decision`'s short-circuit order (so a both-fail wave names the
    conflict, not the category). ``source`` (``"auto"`` | ``"human"`` | None)
    names whether categories were auto-derived from branch diffs or
    human-supplied; **None preserves the original output verbatim** so
    existing output-shape tests stay green (additive change)."""
    if decision == "parallel":
        msg = (
            f"wave is PARALLEL-ELIGIBLE — {len(categories)} task(s), all "
            "safe-category and file-disjoint. Present this to the human for "
            "opt-in before fan-out; absent an explicit opt-in, run the wave "
            "sequentially (the safe default)."
        )
    else:
        if not merge_tree_clean:
            reason = "the wave's branches conflict under git merge-tree"
        else:
            unsafe = [c for c in categories if c not in SAFE_CATEGORIES]
            plural = "ies" if len(unsafe) != 1 else "y"
            reason = f"non-safe categor{plural} present: {', '.join(unsafe)}"
        msg = f"wave is SERIAL — {reason}; run it sequentially."
    if source == "auto":
        msg += " (categories auto-derived from branch diffs)"
    elif source == "human":
        msg += " (categories human-supplied)"
    return msg


# ── auto-classification (supervisor-auto-classify) ───────────────────────────
# Auto-derive a task's conflict category from its committed branch diff so the
# supervisor stops hand-feeding `--category`. FAIL-CLOSED: only an all-added,
# no-danger-path diff is `cannot-collide` (the lone auto-safe label); every
# other shape gets a named non-safe label that serializes. This establishes
# file-additive ∧ (with the gate's merge-tree half) file-disjoint — NOT
# a full disjoint-no-shared-symbol guarantee; the cross-branch guard below
# shrinks that residual, and the irreducible string-key/cross-file-symbol case
# is backstopped by the post-merge test gate, not claimed here.
_DANGER_PATH_RE = re.compile(
    r"(^|/)(poetry\.lock|package-lock\.json|Cargo\.lock|go\.sum|uv\.lock"
    r"|yarn\.lock|requirements\.txt|pyproject\.toml|package\.json|__init__\.py"
    r"|index\.(ts|js|tsx|jsx|mjs|cjs)|mod\.rs|barrel\.\w+|registry\.\w+"
    r"|Makefile|marketplace\.json)$"
    r"|(^|/)migrations?/|(^|/)\.github/workflows/"
)


def classify_task(name_status) -> str:
    """Classify one task's diff into a conflict category from parsed
    ``git diff --name-status`` rows. Each row is a tuple whose first element is
    the status code (``A``/``M``/``D``/``R100``/``C``…) and whose remaining
    elements are path operands (two for rename/copy). Precedence (fail-closed):
    rename/copy/delete → ``move-or-delete``; any danger-path → ``danger-path``;
    all-added → ``cannot-collide`` (the only auto label in SAFE_CATEGORIES);
    else → ``modified-existing``."""
    statuses = [row[0][0] for row in name_status]
    paths = [p for row in name_status for p in row[1:]]
    if any(s in ("R", "C", "D") for s in statuses):
        return "move-or-delete"
    if any(_DANGER_PATH_RE.search(p) for p in paths):
        return "danger-path"
    if statuses and all(s == "A" for s in statuses):
        return "cannot-collide"
    return "modified-existing"


def _resolve_diff_base(explicit, branches):
    """Resolve the ref to diff each branch against. ``--base`` wins; else the
    `git merge-base` of the wave's branches. Returns ``(base, err)`` — fail
    closed: ``err`` is set (and base None) when there are <2 branches and no
    explicit base, or the merge base is empty/ambiguous (multiple bases)."""
    if explicit:
        return explicit, None
    if len(branches) < 2:
        return None, "need >=2 branches (or an explicit --base) to resolve a merge base"
    proc = run_git(["merge-base", "--all", *branches])
    bases = proc.stdout.split() if proc.returncode == 0 else []
    if not bases:
        return None, "no common merge base among the wave's branches (unrelated histories?)"
    if len(bases) > 1:
        return None, "ambiguous base: multiple merge bases among the wave's branches"
    return bases[0], None


def _branch_name_status(base, branch):
    """Parse ``git diff --name-status <base>...<branch>`` into a list of
    ``(status, *paths)`` tuples (two paths for rename/copy)."""
    proc = run_git(["diff", "--name-status", f"{base}...{branch}"])
    rows = []
    for line in proc.stdout.splitlines():
        if line.strip():
            rows.append(tuple(line.split("\t")))
    return rows


def added_paths_may_share_symbol(per_branch_added) -> bool:
    """Cross-branch symbol guard: True iff two branches' **added** paths share a
    basename or an immediate parent directory — a likely symbol/registration
    collision that file-level ``git merge-tree`` cannot see. Conservative
    (over-serializes, never under). ``per_branch_added`` is a list of sets of
    repo-relative paths (git's forward-slash form)."""
    def _bn(p):  # basename, git-path semantics (always '/')
        return p.rsplit("/", 1)[-1]

    def _dir(p):
        return p.rsplit("/", 1)[0] if "/" in p else ""

    for i in range(len(per_branch_added)):
        for j in range(i + 1, len(per_branch_added)):
            a, b = per_branch_added[i], per_branch_added[j]
            if {_bn(p) for p in a} & {_bn(p) for p in b}:
                return True
            # only *real* shared subdirectories count — exclude repo root (""),
            # so two distinct-basename root additions aren't needlessly serial
            # (a same-named root add is already a merge-tree conflict anyway).
            dirs_a = {_dir(p) for p in a} - {""}
            dirs_b = {_dir(p) for p in b} - {""}
            if dirs_a & dirs_b:
                return True
    return False


def wave_is_disjoint(branches) -> bool:
    """True iff the wave's branches merge without conflict, via read-only
    ``git merge-tree`` (no working-tree mutation). Pairwise over the wave;
    called by the ``dispatch-decision`` verb (and the worktree dry-run)."""
    for i in range(len(branches)):
        for j in range(i + 1, len(branches)):
            proc = run_git(
                ["merge-tree", "--write-tree", "--name-only", branches[i], branches[j]]
            )
            if proc.returncode != 0:  # git merge-tree exits non-zero on conflict
                return False
    return True


# ── init ──────────────────────────────────────────────────────────────────


def cmd_init(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    dest = state_path_for(spec_dir)
    if dest.exists() and not args.force:
        return stop(f"state.json already exists at {dest} (use --force to overwrite)")
    if not TEMPLATE_PATH.exists():
        return stop(f"template missing at {TEMPLATE_PATH}")
    template = json.loads(TEMPLATE_PATH.read_text())
    template["feature"] = spec_dir.name
    write_state_atomic(spec_dir, template)
    print(f"loop-cohort: initialised {dest} (feature={spec_dir.name})")
    return 0


# ── schedule (topological order; sequential by default) ───────────────────


def cmd_schedule(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    plan_path = Path(args.plan) if args.plan else spec_dir / "plan.md"
    if not plan_path.exists():
        return stop(f"plan not found at {plan_path}")
    ordered, deps = parse_plan(plan_path.read_text())
    if not ordered:
        return stop(f"no '### T<n>' tasks found in {plan_path}")

    cyc = detect_cycles(ordered, deps)
    if cyc:
        return stop(
            f"dependency cycle among tasks: {', '.join(cyc)} — unschedulable; "
            "the plan is wrong, fix Depends on:"
        )
    # A forward-reference is a *valid* acyclic edge (a task declares a dep
    # authored later); the topological order below reorders it correctly, so
    # it is a WARNING (authored-order smell), not a hard error. Only a cycle
    # is unschedulable. (Surfaced during EXECUTE — see plan.md changelog.)
    fwd = detect_forward_refs(ordered, deps)
    if fwd:
        pairs = ", ".join(f"{a}->{b}" for a, b in fwd)
        print(
            f"loop-cohort: warning — forward-reference(s) in {spec_dir.name} "
            f"(dep authored later; reordered below): {pairs}",
            file=sys.stderr,
        )

    waves, _ = topological_waves(ordered, deps)
    # Optional `Touches:` globs drive a SCREEN-ONLY pre-dispatch disjointness
    # prediction per multi-task wave. Advisory: a `no` is a reason to serialize
    # early; `yes`/`unknown` never greenlight — the authoritative post-write
    # `git merge-tree` (in `dispatch-decision`) is untouched. (Follow-on 3.)
    touches = parse_touches_by_task(plan_path.read_text())
    print(
        f"loop-cohort: topological order for {spec_dir.name} "
        "(run sequentially by default; waves mark what *could* parallelize):"
    )
    for i, wave in enumerate(waves, 1):
        print(f"  wave {i}: {', '.join(wave)}")
        if len(wave) > 1:
            verdict = wave_touches_disjoint([touches.get(t) for t in wave])
            print(f"    predicted-disjoint: {verdict}  "
                  "(Touches: screen — serialize-only, never a greenlight)")
    return 0


def cmd_dispatch_decision(args: argparse.Namespace) -> int:
    """Gate one write wave: print ``parallel`` or ``serial``. The wave's
    conflict categories are **auto-derived** from
    each ``--branch``'s committed diff when ``--category`` is omitted, else the
    explicit ``--category`` list is used verbatim (human override). Combined
    with a mechanical ``git merge-tree`` file-disjointness check; fail closed:
    any non-safe category, any merge-tree conflict, or (auto path) an
    unresolvable diff base or cross-branch symbol collision → serial. stdout is
    the machine-readable token; stderr carries the cleared-gate rationale."""
    clean = wave_is_disjoint(args.branch) if len(args.branch) > 1 else True

    if args.category:  # human override — used verbatim (still the only typed-group-b path)
        categories, source = args.category, "human"
    else:  # auto-classify each branch from its committed diff
        source = "auto"
        base, err = _resolve_diff_base(args.base, args.branch)
        if err:
            print("serial")
            print(
                f"dispatch-decision: wave is SERIAL — diff base unresolved ({err}); "
                "run it sequentially. (categories auto-derived from branch diffs)",
                file=sys.stderr,
            )
            return 0
        categories, added_sets = [], []
        for br in args.branch:
            rows = _branch_name_status(base, br)
            categories.append(classify_task(rows))
            added_sets.append({row[-1] for row in rows if row[0][0] == "A"})
        # cross-branch symbol guard: an all-cannot-collide wave whose added
        # files share a basename/parent-dir injects a non-safe marker so the
        # unchanged gate serializes it and the rationale names the cause.
        if (categories and all(c == "cannot-collide" for c in categories)
                and added_paths_may_share_symbol(added_sets)):
            categories = categories + ["cross-branch-symbol"]

    decision = dispatch_decision(categories, merge_tree_clean=clean)
    print(decision)  # stdout: the machine-readable token (scripted reads)
    # stderr: the human-facing cleared-gate surface — so the agent has
    # something to present to the human for opt-in, never fanning out silently.
    print(
        "dispatch-decision: " + _dispatch_rationale(
            categories, merge_tree_clean=clean, decision=decision, source=source
        ),
        file=sys.stderr,
    )
    return 0


# ── check (formerly check-done.py) ────────────────────────────────────────


def cmd_check(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
    except FileNotFoundError as exc:
        return stop(str(exc))
    except ValueError as exc:
        return stop(str(exc))

    return _evaluate(state, args.phase)


def _evaluate(state: dict, phase: str) -> int:
    if state.get("plan_review_status", "pending") == "pending":
        return stop("plan not approved (plan_review_status=pending)")
    if phase == "plan":
        return 0

    iter_count = state.get("iteration_count", 0)
    max_iter = state.get("max_iterations", DEFAULTS["max_iterations"])
    if iter_count >= max_iter:
        return stop(f"iteration cap reached ({iter_count}/{max_iter})")

    used = state.get("token_budget_used_pct", 0.0)
    cap = state.get("token_budget_cap_pct", DEFAULTS["token_budget_cap_pct"])
    if used >= cap:
        return stop(f"token budget exhausted ({used:.2%}/{cap:.2%})")

    same_err = state.get("consecutive_same_error_count", 0)
    same_err_threshold = state.get(
        "consecutive_same_error_threshold",
        DEFAULTS["consecutive_same_error_threshold"],
    )
    if same_err >= same_err_threshold:
        return stop(f"stuck on same error ({same_err} consecutive iterations)")

    if phase == "review":
        current = sorted(state.get("finding_fingerprints", []))
        previous = sorted(state.get("previous_finding_fingerprints", []))
        if current and current == previous:
            return stop(
                f"no progress — same {len(current)} finding(s) two iterations in a row"
            )

    return 0


# ── approve-plan ──────────────────────────────────────────────────────────


def cmd_approve_plan(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    state["plan_review_status"] = "approved"
    write_state_atomic(spec_dir, state)
    print(f"loop-cohort: plan_review_status=approved for {spec_dir.name}")
    return 0


# ── auto-parallel (per-run unattended pre-authorization) ────────────────────


def cmd_auto_parallel(args: argparse.Namespace) -> int:
    """Per-run pre-authorization for unattended supervisor runs (follow-on 4).
    Sets `state.json.auto_parallel` (default off; `--off` clears it). When set,
    the supervisor proceeds in parallel on a wave that has ALREADY cleared the
    gate, skipping only the follow-on-1 human opt-in — it is never a gate input
    and never causes auto-recovery (a failed wave still Surfaces). Per-run
    session scratch: a fresh run defaults off."""
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    state["auto_parallel"] = not args.off
    write_state_atomic(spec_dir, state)
    print(f"loop-cohort: auto_parallel={state['auto_parallel']} for {spec_dir.name}")
    return 0


# ── review record ─────────────────────────────────────────────────────────

# Anchors on the adversarial-reviewer's documented format:
#   ## Blockers / ## Concerns / ## Nits headings (empty sections omitted)
#   **N. <title>.** `path/to/file.ext:line`. <what's wrong>. Fix: <fix>.
FINDING_LINE_RE = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*`(?P<citation>[^`]+)`"
)
LINE_FROM_CITATION_RE = re.compile(r":(\d+)")


def parse_findings(report_text: str) -> list[str]:
    """Return SHA1 fingerprints for findings in a reviewer report.

    Algorithm pinned by the work-loop SKILL §REVIEW:
        sha1("<file>|<line>|<title>")
    where <file> is the cited path exactly as written, <line> is the first
    integer after the first colon in the citation, and <title> is the
    bolded heading including the surrounding `**` markers.
    """
    fingerprints: list[str] = []
    for raw in report_text.splitlines():
        line = raw.strip()
        if not line.startswith("**"):
            continue
        m = FINDING_LINE_RE.match(line)
        if not m:
            continue
        title = m.group("title").strip()
        citation = m.group("citation").strip()
        if ":" not in citation:
            continue
        file_part, _, rest = citation.partition(":")
        line_match = re.match(r"\d+", rest)
        if not line_match:
            continue
        line_num = line_match.group(0)
        key = f"{file_part}|{line_num}|{title}"
        fingerprints.append(hashlib.sha1(key.encode("utf-8"), usedforsecurity=False).hexdigest())
    return fingerprints


def cmd_review_record(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))

    if args.fingerprint:
        fingerprints = list(args.fingerprint)
    else:
        report_path = Path(args.report)
        if not report_path.exists():
            return stop(f"report not found at {report_path}")
        report_text = report_path.read_text()
        if "Clean — ready to commit." in report_text:
            fingerprints = []
        else:
            fingerprints = parse_findings(report_text)
            if not fingerprints:
                return stop(
                    f"parsed zero findings from {report_path} and report is not "
                    "marked clean; pass --fingerprint <hex> repeated to bypass"
                )

    state["previous_finding_fingerprints"] = list(state.get("finding_fingerprints", []))
    state["finding_fingerprints"] = fingerprints
    state["iteration_count"] = int(state.get("iteration_count", 0)) + 1
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: review iter={state['iteration_count']} "
        f"findings={len(fingerprints)} for {spec_dir.name}"
    )
    return 0


# ── worktree subcommands ──────────────────────────────────────────────────


def worktree_path_for(task_id: str) -> Path:
    return Path(".worktrees") / task_id


def branch_name_for(base: str, task_id: str) -> str:
    return f"{base}-{task_id}"


def current_branch() -> str:
    proc = run_git(["branch", "--show-current"])
    if proc.returncode != 0:
        raise RuntimeError(f"git branch --show-current failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def cmd_worktree_preflight(args: argparse.Namespace) -> int:
    # Surface any stale worktree directories or pre-existing branches
    # for the cohort's task IDs — do not silently reuse or destroy.
    spec_dir = Path(args.spec_dir)
    try:
        base = current_branch()
    except RuntimeError as exc:
        return stop(str(exc))

    run_git(["worktree", "prune"])
    listing = run_git(["worktree", "list", "--porcelain"])
    if listing.returncode != 0:
        return stop(f"git worktree list failed: {listing.stderr.strip()}")

    collisions: list[str] = []
    for task_id in args.task_ids:
        wt = worktree_path_for(task_id)
        if wt.exists():
            collisions.append(f"worktree directory {wt} already exists")
        branch = branch_name_for(base, task_id)
        verify = run_git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"])
        if verify.returncode == 0:
            collisions.append(f"branch {branch} already exists")

    if collisions:
        for line in collisions:
            print(f"loop-cohort: {line}", file=sys.stderr)
        return stop(
            f"stale cohort state for {spec_dir.name}; resolve manually "
            "(do not silently reuse)"
        )
    print(f"loop-cohort: preflight clean for {spec_dir.name}")
    return 0


def cmd_worktree_add(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
        base = current_branch()
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        return stop(str(exc))

    entries = state.setdefault("worktrees", [])
    if any(e.get("task_id") == args.task_id for e in entries):
        return stop(f"worktree entry for task {args.task_id} already exists")

    wt = worktree_path_for(args.task_id)
    branch = branch_name_for(base, args.task_id)
    proc = run_git(["worktree", "add", str(wt), "-b", branch])
    if proc.returncode != 0:
        return stop(f"git worktree add failed: {proc.stderr.strip()}")

    entries.append(
        {
            "task_id": args.task_id,
            "branch": branch,
            "path": str(wt),
            "status": "in-progress",
            "report_path": None,
        }
    )
    write_state_atomic(spec_dir, state)
    print(f"loop-cohort: worktree add task={args.task_id} branch={branch} path={wt}")
    return 0


REPORT_HEADING_RE = re.compile(r"^##\s+Task\s+([^\s:.,]+)", re.MULTILINE)


def cmd_worktree_record(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))

    entries = state.get("worktrees", [])
    target = next((e for e in entries if e.get("task_id") == args.task_id), None)
    if target is None:
        return stop(f"no worktree entry for task {args.task_id}")

    report_src = Path(args.report)
    if not report_src.exists():
        return stop(f"report not found at {report_src}")
    report_text = report_src.read_text()

    # Match first — confirm the report's heading references the task ID
    # we were told to record. Never write under an unvalidated name.
    m = REPORT_HEADING_RE.search(report_text)
    if not m:
        return stop(
            f"report at {report_src} has no '## Task <task-id>' heading"
        )
    declared = m.group(1)
    if declared != args.task_id:
        return stop(
            f"report at {report_src} declares task '{declared}', "
            f"expected '{args.task_id}'"
        )

    # Write second — persist the report under notes/.
    iteration = int(state.get("iteration_count", 0))
    notes_dir = spec_dir / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    report_dst = notes_dir / f"implementer-{args.task_id}-{iteration}.md"
    report_dst.write_text(report_text)

    # State-update last — flip status + report_path on the matched entry.
    target["status"] = args.status
    target["report_path"] = str(report_dst)
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: worktree record task={args.task_id} status={args.status} "
        f"report={report_dst}"
    )
    return 0


def cmd_worktree_list(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    entries = state.get("worktrees", [])
    if not entries:
        print("loop-cohort: no worktree entries")
        return 0
    width = max(len(e.get("task_id", "")) for e in entries)
    for e in entries:
        print(
            f"{e.get('task_id', ''):<{width}}  {e.get('status', ''):<12}"
            f"  {e.get('branch', ''):<40}  {e.get('report_path') or '-'}"
        )
    return 0


def _task_id_sort_key(task_id: str):
    m = re.fullmatch(r"T(\d+)", task_id)
    if m:
        return (0, int(m.group(1)))
    return (1, task_id)


def cmd_worktree_merge(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))

    ready = [
        e for e in state.get("worktrees", []) if e.get("status") == "ready"
    ]
    if not ready:
        return stop("no ready worktrees to merge")

    ready.sort(key=lambda e: _task_id_sort_key(e.get("task_id", "")))
    for e in ready:
        branch = e.get("branch")
        proc = run_git(["merge", "--no-ff", branch])
        if proc.returncode != 0:
            run_git(["merge", "--abort"])
            return stop(
                f"merge conflict on task {e.get('task_id')} (branch {branch}); "
                "tasks weren't actually independent — return to PLAN and "
                "fix Depends on:"
            )
        print(f"loop-cohort: merged task={e.get('task_id')} branch={branch}")
    return 0


def cmd_worktree_cleanup(args: argparse.Namespace) -> int:
    spec_dir = Path(args.spec_dir)
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))

    stuck: list[str] = []
    for e in state.get("worktrees", []):
        path = e.get("path")
        if not path:
            continue
        proc = run_git(["worktree", "remove", path])
        if proc.returncode != 0:
            forced = run_git(["worktree", "remove", "--force", path])
            if forced.returncode != 0:
                stuck.append(path)
                continue
        print(f"loop-cohort: worktree removed {path}")
    if stuck:
        for path in stuck:
            print(f"loop-cohort: could not remove {path} (left in place)", file=sys.stderr)
        # Non-zero so the supervisor sees and reports the stuck paths in
        # the end-of-loop summary, but the entries keep their terminal
        # status — the loop should still proceed to gates.
        return 2
    return 0


# ── dispatcher ────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="loop-cohort", description=__doc__)
    sub = p.add_subparsers(dest="verb", required=True)

    sp = sub.add_parser("init", help="initialise state.json from the bundled template")
    sp.add_argument("spec_dir")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser(
        "schedule",
        help="parse the plan DAG; detect cycles/forward-refs; print topological order",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--plan", help="path to plan.md (default: <spec-dir>/plan.md)")
    sp.set_defaults(func=cmd_schedule)

    sp = sub.add_parser(
        "dispatch-decision",
        help="gate a write wave: safe-category ∧ git merge-tree disjointness → parallel|serial",
    )
    sp.add_argument(
        "--category", action="append", default=[],
        help="one task's conflict category (repeat per task); OMIT to "
             "auto-classify each --branch from its committed diff",
    )
    sp.add_argument(
        "--branch", action="append", default=[],
        help="one task's worktree branch (repeat per task; merge-tree "
             "disjointness + auto-classification source)",
    )
    sp.add_argument(
        "--base",
        help="ref to diff each branch against for auto-classification "
             "(default: git merge-base of the --branches)",
    )
    sp.set_defaults(func=cmd_dispatch_decision)

    sp = sub.add_parser("check", help="phase termination check")
    sp.add_argument("spec_dir")
    sp.add_argument("--phase", required=True, choices=PHASES)
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("approve-plan", help="flip plan_review_status to approved")
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_approve_plan)

    sp = sub.add_parser(
        "auto-parallel",
        help="per-run: pre-authorize unattended parallel on already-cleared waves "
             "(default off; --off clears)",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--off", action="store_true", help="clear auto_parallel (set false)")
    sp.set_defaults(func=cmd_auto_parallel)

    sp_review = sub.add_parser("review", help="review-phase state mutations")
    review_sub = sp_review.add_subparsers(dest="review_verb", required=True)
    sp = review_sub.add_parser(
        "record",
        help="rotate fingerprints from a reviewer report and bump iteration",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--report", help="path to the reviewer's markdown report")
    sp.add_argument(
        "--fingerprint",
        action="append",
        default=[],
        help="explicit fingerprint (hex sha1); escape hatch when parsing fails",
    )
    sp.set_defaults(func=cmd_review_record)

    sp_wt = sub.add_parser("worktree", help="cohort worktree coordination")
    wt_sub = sp_wt.add_subparsers(dest="worktree_verb", required=True)

    sp = wt_sub.add_parser(
        "preflight",
        help="surface stale worktree dirs or pre-existing branches",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("task_ids", nargs="*")
    sp.set_defaults(func=cmd_worktree_preflight)

    sp = wt_sub.add_parser("add", help="create a cohort worktree for one task")
    sp.add_argument("spec_dir")
    sp.add_argument("task_id")
    sp.set_defaults(func=cmd_worktree_add)

    sp = wt_sub.add_parser(
        "record",
        help="persist an implementer's report and update the cohort entry",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("task_id")
    sp.add_argument("--status", required=True, choices=WORKTREE_STATUSES)
    sp.add_argument("--report", required=True)
    sp.set_defaults(func=cmd_worktree_record)

    sp = wt_sub.add_parser("list", help="show cohort entries")
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_worktree_list)

    sp = wt_sub.add_parser(
        "merge",
        help="merge every ready worktree in task-id order; abort on conflict",
    )
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_worktree_merge)

    sp = wt_sub.add_parser(
        "cleanup",
        help="git worktree remove each entry; retry --force, then surface stuck paths",
    )
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_worktree_cleanup)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return stop("interrupted")


if __name__ == "__main__":
    sys.exit(main())
