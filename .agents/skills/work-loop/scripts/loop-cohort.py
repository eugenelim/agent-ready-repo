#!/usr/bin/env python3
"""loop-cohort — work-loop execution-state owner (Phase 1).

Single tool the work-loop skill calls for every deterministic state mutation:
phase termination checks, plan approval, review-finding fingerprints, and wave
scheduling. Phase-1 parallel verbs (worktree, dispatch-decision, auto-parallel)
are disabled — they exit non-zero without touching state.json.

Cross-platform: Python 3 stdlib only, `subprocess` for git, `os.replace` for
atomic writes, `pathlib` for paths. No shell, no bash, no PATH dependency.

Verb surface
------------
    loop-cohort init <spec-dir> --run-id <uuid>
    loop-cohort identity <spec-dir> [--expect-run-id <uuid>] [--json]
    loop-cohort check <spec-dir> --phase {implement,review,gates-failed}
    loop-cohort approve-plan <spec-dir> --expect-run-id <uuid>
    loop-cohort plan check-current <spec-dir> [--require-schedule]
    loop-cohort schedule <spec-dir> --expect-run-id <uuid>
    loop-cohort schedule check-current <spec-dir>
    loop-cohort record-attempt <spec-dir> --phase implement
                               --cycle-id <run_id>:<seq> --expect-run-id <uuid>
    loop-cohort wave check <spec-dir> --expect {more,last} [--wave-index <n>]
    loop-cohort wave advance <spec-dir> --from-index <n> --expect-run-id <uuid>
    loop-cohort review inspect <spec-dir> --report <path> [--json]
    loop-cohort review record <spec-dir> (--report <path>
                               | --fingerprint <hex> ...) --expect-run-id <uuid>
    loop-cohort status <spec-dir> [--json]
    loop-cohort reset <spec-dir>
    loop-cohort worktree ...        (disabled in Phase 1 — exits non-zero)
    loop-cohort dispatch-decision   (disabled in Phase 1 — exits non-zero)
    loop-cohort auto-parallel ...   (disabled in Phase 1 — exits non-zero)

Exit contract: 0 on success; non-zero with a one-line reason on stderr.

Schema reference: ../assets/state.json and ../references/state-schema.md.
"""

from __future__ import annotations

import argparse
import contextlib
import fnmatch
import glob as _glob
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "state.json"

PHASES = ("implement", "review", "gates-failed")
WORKTREE_STATUSES = ("ready", "blocked", "failed")

CLEAN_SUBSTRING = "Clean — ready to commit."
# Specialist reviewers (experience-reviewer, frontend-reviewer) emit "SHIP IT"
# on its own line as their clean verdict instead of CLEAN_SUBSTRING.
_SHIP_IT_RE = re.compile(r"^SHIP IT\s*$", re.MULTILINE)
# Fingerprints are SHA-256 (64 hex). The 40-hex SHA-1 form is still accepted
# so a cohort that was mid-review when core upgraded can finish: its
# state.json holds SHA-1 values and `review record --fingerprint` would
# otherwise hard-reject them. Stasis detection compares sets computed by the
# same binary, so a straddling run misses a match for exactly one round and
# self-heals on the next. Drop the 40-hex alternative once no in-flight
# cohort predates core 2.3.0.
_RE_FINGERPRINT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def _template_max_implementation_retries(fallback: int = 5) -> int:
    """Read max_implementation_retries from the bundled state.json template."""
    try:
        return int(
            json.loads(
                TEMPLATE_PATH.read_text(encoding="utf-8")
            )["max_implementation_retries"]
        )
    except (FileNotFoundError, OSError, KeyError, TypeError, ValueError):
        return fallback


def _template_max_review_retries(fallback: int = 5) -> int:
    """Read max_review_retries from the bundled state.json template."""
    try:
        return int(
            json.loads(
                TEMPLATE_PATH.read_text(encoding="utf-8")
            )["max_review_retries"]
        )
    except (FileNotFoundError, OSError, KeyError, TypeError, ValueError):
        return fallback


DEFAULTS: dict = {
    "max_implementation_retries": _template_max_implementation_retries(),
    "max_review_retries": _template_max_review_retries(),
}


def stop(reason: str, code: int = 1) -> int:
    print(f"loop-cohort: stop — {reason}", file=sys.stderr)
    return code


def _disabled(verb: str) -> int:
    return stop(f"{verb} is disabled in Phase 1")


def _resolve_spec_dir(raw: str) -> Path:
    """Resolve <spec-dir> to an absolute path; reject `..` traversal."""
    p = Path(raw).resolve()
    parts = Path(raw).parts
    if ".." in parts:
        raise ValueError(f"spec-dir must not contain '..': {raw!r}")
    return p


def state_path_for(spec_dir: Path) -> Path:
    return spec_dir / "state.json"


def read_state(spec_dir: Path) -> dict:
    path = state_path_for(spec_dir)
    if not path.exists():
        raise FileNotFoundError(f"state.json missing at {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ValueError(f"state.json malformed: {exc.msg} at line {exc.lineno}") from exc
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
        Path(tmp).replace(path)
    except Exception:
        with contextlib.suppress(OSError):
            Path(tmp).unlink()
        raise


def run_git(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        check=False,
    )


# ── hashing helpers ───────────────────────────────────────────────────────

# Lazy handle on the sibling lint-spec-status.py. Status and acceptance-criterion
# recognition has exactly one implementation in this repo — a shipped spec
# (docs/specs/loop-approved-spec-state, Constrained by ADR-0061) requires every
# status read to go through its `parse_status`, and a second copy of the AC
# regexes is how the two silently disagree about what an AC line is.
_lint_module: object | None = None


def _lint_spec_status():
    global _lint_module
    if _lint_module is None:
        lint_path = Path(__file__).resolve().parent / "lint-spec-status.py"
        spec = importlib.util.spec_from_file_location("_lint_spec_status", str(lint_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"loop-cohort: cannot load {lint_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _lint_module = module
    return _lint_module


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# The approved baseline pins the *scope a human approved*. It deliberately does
# not pin the two field families this skill mandates writing after approval —
# the preamble status token (SKILL.md: `Implementing` before code, `Shipped` at
# finish, plan `Done`) and progress checkboxes (every AC to `[x]`). Pinning
# those made `plan check-current` and `schedule check-current` fail by
# construction, one mandated step after `approve-plan`.
#
# Everything else stays pinned, including anything else on the status line: a
# `- **Status:** Implementing — scope now also covers X` still moves the digest.
_STATUS_PLACEHOLDER = "<loop-cohort:status>"
# A heading, or the bold prose lead-in two specs here use instead. Missing the
# latter would leave those specs with no normalization at all — i.e. AC5
# failing for them by construction, the defect this spec exists to fix.
_AC_HEADING_RE = re.compile(
    r"^ {0,3}(?:#{2,3}\s+|\*\*)Acceptance\s+Criteria\b", re.IGNORECASE
)
_ANY_SECTION_RE = re.compile(r"^ {0,3}#{1,2}[ \t]")

# AC10: a mismatch has two possible causes and the verb cannot tell them apart,
# so it names both rather than asserting the one that is usually wrong.
_BOTH_CAUSES = (
    "either the approved scope changed, or this baseline was pinned before "
    "canonical hashing landed. For the second case, recover the cohort only: "
    "(1) restore `Status: Approved` in BOTH spec.md and plan.md — approve-plan "
    "refuses unless both read Approved; (2) `loop-cohort reset`; "
    "(3) `loop-cohort init <spec-dir> --run-id <the engine's existing run_id>`, "
    "read from `loop-engine status --json`; (4) `approve-plan` then `schedule`; "
    "(5) restore the Status you were on. Do NOT run `loop-engine reset` — "
    "`plan-locked` is legal only from SPEC-PLAN-APPROVED and the engine has no "
    "state-setting verb, so resetting it strands the run. Note the reset clears "
    "the retry counters and the stasis baseline, and re-running approve-plan "
    "re-pins whatever is on disk, so it is a re-approval in substance"
)


def canonical_contract(text: str, *, ac_section_only: bool = True) -> str:
    """Canonical form of spec.md / plan.md for approval pinning.

    Normalizes exactly four things: CRLF/CR → LF; per-line trailing whitespace;
    the preamble status *token*; and the bracket contents of a checkbox.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")

    lint = _lint_spec_status()
    # Newline-preserving comment strip. `parse_status` uses a plain sub() with
    # re.DOTALL, which collapses a multiline comment to nothing and shifts every
    # later line index — fine when you only want the token, wrong here, where
    # the index has to map back to the raw line being rewritten.
    cleaned = lint._HTML_COMMENT_RE.sub(
        lambda m: "\n" * m.group(0).count("\n"), text
    ).split("\n")

    for i, cleaned_line in enumerate(cleaned):
        if lint._SECTION_HEADING_RE.match(cleaned_line):
            break  # preamble ends at the first section heading
        if cleaned_line.lstrip().startswith("#"):
            continue
        if not lint._STATUS_RE.search(cleaned_line):
            continue
        # Rewrite the *raw* line, not the comment-stripped one.
        raw = lines[i]
        m = lint._STATUS_RE.search(raw)
        if m is None:
            break
        token = lint.extract_status_token(m.group(1))
        if token:
            # Span-bounded splice of the token only. A str.replace would also
            # rewrite the token where it recurs inside the trailing vocabulary
            # comment (`<!-- Draft | Approved | Implementing | ... -->`), which
            # 158 spec/plan files in this repo carry — making each status
            # normalize differently. Splicing _STATUS_RE's whole group(1) span
            # would swallow appended free text and defeat the pin.
            start = m.start(1)
            lines[i] = raw[:start] + _STATUS_PLACEHOLDER + raw[start + len(token):]
        break

    # Which checkboxes count as bookkeeping depends on the artifact, so the
    # caller says. A spec's progress marks live in its Acceptance Criteria
    # section; a checkbox under `## Boundaries` is a `Never do` item, which is
    # precisely the scope the pin protects — two specs in this repo have one.
    # A plan has no such section: every checkbox in it is task progress, and
    # four plans here carry them, so a plan is normalized file-wide.
    #
    # Case-insensitive on purpose: `lint-spec-status.py` matches `Acceptance
    # Criteria` exactly, so its own AC extraction silently returns nothing for
    # the specs that spell it with a lowercase `c`. Inheriting that bug here
    # would break this normalization for exactly those specs. Tracked as
    # `spec-ac-heading-casing-silent-gate`.
    in_ac = not ac_section_only
    fenced = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if fenced:
            continue
        if ac_section_only and _AC_HEADING_RE.match(line):
            in_ac = True
            continue
        if ac_section_only and in_ac and _ANY_SECTION_RE.match(line):
            in_ac = False
        if in_ac and lint._AC_DONE_RE.match(line):
            # Bracket contents only — leading whitespace and the bullet run stay
            # byte-for-byte, so re-indenting a criterion still moves the digest.
            j = line.index("[")
            lines[i] = line[:j + 1] + " " + line[j + 2:]

    return "\n".join(line.rstrip() for line in lines)


def sha256_canonical_contract(path: Path) -> str:
    """SHA-256 of canonical_contract(<spec.md | plan.md>)."""
    return _sha256_bytes(
        canonical_contract(
            path.read_text(encoding="utf-8"),
            ac_section_only=(path.name != "plan.md"),
        ).encode("utf-8")
    )


# ── run_id / schema_version validation ───────────────────────────────────


def _validate_run_id(state: dict, expect_run_id: str, *, verb: str) -> int | None:
    """Return None on success, or a stop() error code on schema/identity mismatch."""
    sv = state.get("schema_version")
    if sv != 1:
        return stop(
            f"{verb}: unsupported schema_version={sv!r} (expected 1); run reset pair"
        )
    stored = state.get("run_id")
    if stored != expect_run_id:
        return stop(
            f"{verb}: --expect-run-id mismatch (stored={stored!r}, "
            f"supplied={expect_run_id!r})"
        )
    return None


# ── scheduler (wave-scheduled supervisor mode) ────────────────────────────
#
# Pure functions over a plan's `Depends on:` graph. Sequential by default.

# Accepts both '## T<n>' (level-2) and '### T<n>' (level-3) headings for
# backward compatibility with existing plans that predate the Phase-1 spec.
TASK_HEADING_RE = re.compile(r"^#{2,3}\s+(T\d+[a-z]?)\b", re.MULTILINE)
DEPENDS_LINE_RE = re.compile(r"^\*\*Depends on:\*\*\s*(.+)$", re.MULTILINE)
TOUCHES_LINE_RE = re.compile(r"^\*\*Touches:\*\*\s*(.+)$", re.MULTILINE)
_RANGE_RE = re.compile(r"(T\d+)\s*-\s*(T\d+)")
_TASK_ID_RE = re.compile(r"T\d+[a-z]?")
_CROSS_MARKER_RE = re.compile(r"spec:([A-Za-z0-9._-]+)/(T\d+[a-z]?)")
_CROSS_LEGACY_RE = re.compile(r"`(?!T\d+[a-z]?`)([A-Za-z0-9._-]+)`\s*(T\d+[a-z]?)")


def parse_depends_on(field: str, local_task_ids):
    """Parse a 'Depends on:' field value into local task IDs and cross-spec markers."""
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
    """Extract ordered task IDs and dependency map from plan.md text."""
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


def parse_touches(field: str):
    head = field.split("(")[0]
    return {g.strip() for g in head.split(",") if g.strip()}


def parse_touches_by_task(text: str):
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
    return _glob.escape(seg) == seg


def _seg_provably_disjoint(x: str, y: str) -> bool:
    xl, yl = _is_literal_seg(x), _is_literal_seg(y)
    if xl and yl:
        return x != y
    if xl and not yl:
        return not fnmatch.fnmatch(x, y)
    if yl and not xl:
        return not fnmatch.fnmatch(y, x)
    return False


def globs_overlap(a: str, b: str) -> bool:
    if "**" in a or "**" in b:
        return True
    sa, sb = a.split("/"), b.split("/")
    if len(sa) != len(sb):
        return False
    return not any(_seg_provably_disjoint(x, y) for x, y in zip(sa, sb, strict=False))


def wave_touches_disjoint(per_task_globs) -> str:
    declared = [g for g in per_task_globs if g]
    for i in range(len(declared)):
        for j in range(i + 1, len(declared)):
            if any(globs_overlap(x, y) for x in declared[i] for y in declared[j]):
                return "no"
    if any(not g for g in per_task_globs):
        return "unknown"
    return "yes"


def build_dag(ordered, deps):
    taskset = set(ordered)
    indeg = dict.fromkeys(ordered, 0)
    children = defaultdict(list)
    for t in ordered:
        for d in deps.get(t, ()):
            if d in taskset:
                indeg[t] += 1
                children[d].append(t)
    return indeg, children


def topological_waves(ordered, deps):
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
    """Return task IDs that form cycles (topological sort excludes them)."""
    waves, placed = topological_waves(ordered, deps)
    if placed == len(ordered):
        return []
    scheduled = {t for w in waves for t in w}
    return [t for t in ordered if t not in scheduled]


def detect_forward_refs(ordered, deps):
    """Return (task, dep) pairs where dep appears after task in the declared order."""
    order = {t: i for i, t in enumerate(ordered)}
    return [
        (t, d)
        for t in ordered
        for d in deps.get(t, ())
        if d in order and order[d] > order[t]
    ]


# ── auto-classification helpers (kept; dispatch-decision verb disabled) ───

SAFE_CATEGORIES = frozenset({"cannot-collide", "typed-group-b", "textual-loud"})

_DANGER_PATH_RE = re.compile(
    r"(^|/)(poetry\.lock|package-lock\.json|Cargo\.lock|go\.sum|uv\.lock"
    r"|yarn\.lock|requirements\.txt|pyproject\.toml|package\.json|__init__\.py"
    r"|index\.(ts|js|tsx|jsx|mjs|cjs)|mod\.rs|barrel\.\w+|registry\.\w+"
    r"|Makefile|marketplace\.json)$"
    r"|(^|/)migrations?/|(^|/)\.github/workflows/"
)


def classify_task(name_status) -> str:
    statuses = [row[0][0] for row in name_status]
    paths = [p for row in name_status for p in row[1:]]
    if any(s in ("R", "C", "D") for s in statuses):
        return "move-or-delete"
    if any(_DANGER_PATH_RE.search(p) for p in paths):
        return "danger-path"
    if statuses and all(s == "A" for s in statuses):
        return "cannot-collide"
    return "modified-existing"


def dispatch_decision(categories, *, merge_tree_clean):
    if not merge_tree_clean:
        return "serial"
    if any(c not in SAFE_CATEGORIES for c in categories):
        return "serial"
    return "parallel"


# ── init ──────────────────────────────────────────────────────────────────


def cmd_init(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    dest = state_path_for(spec_dir)
    if dest.exists():
        return stop(
            f"state.json already exists at {dest}; run 'loop-cohort reset' first"
        )
    if not TEMPLATE_PATH.exists():
        return stop(f"template missing at {TEMPLATE_PATH}")
    template = json.loads(TEMPLATE_PATH.read_text())
    template["run_id"] = args.run_id
    template["feature"] = Path(spec_dir).resolve().name
    write_state_atomic(spec_dir, template)
    print(f"loop-cohort: initialised {dest} (feature={template['feature']} run_id={args.run_id})")
    return 0


# ── identity ──────────────────────────────────────────────────────────────


def cmd_identity(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    if state.get("schema_version") != 1:
        sv = state.get("schema_version")
        return stop(f"identity: unsupported schema_version={sv!r} (expected 1)")
    stored_run_id = state.get("run_id")
    if args.expect_run_id is not None and stored_run_id != args.expect_run_id:
        return stop(
            f"identity: run_id mismatch (stored={stored_run_id!r}, "
            f"expected={args.expect_run_id!r})"
        )
    result = {"run_id": stored_run_id, "schema_version": state.get("schema_version")}
    if args.json:
        print(json.dumps(result))
    else:
        print(f"loop-cohort: run_id={stored_run_id} schema_version={result['schema_version']}")
    return 0


# ── status ────────────────────────────────────────────────────────────────


def cmd_status(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    if state.get("schema_version") != 1:
        sv = state.get("schema_version")
        return stop(f"status: unsupported schema_version={sv!r} (expected 1)")
    result = {
        "schema_version": state.get("schema_version"),
        "run_id": state.get("run_id"),
        "plan_review_status": state.get("plan_review_status", "pending"),
        "approved_spec_hash": state.get("approved_spec_hash"),
        "approved_plan_hash": state.get("approved_plan_hash"),
        "plan_hash": state.get("plan_hash"),
        "schedule_waves": state.get("schedule_waves", []),
        "current_wave_index": state.get("current_wave_index", 0),
        "implementation_retry_count": state.get("implementation_retry_count", 0),
        "review_round_count": state.get("review_round_count", 0),
        "review_retry_count": state.get("review_retry_count", 0),
        "finding_fingerprints": state.get("finding_fingerprints", []),
        "previous_finding_fingerprints": state.get("previous_finding_fingerprints", []),
    }
    if args.json:
        print(json.dumps(result))
    else:
        print(f"loop-cohort status for {spec_dir.name}:")
        for k, v in result.items():
            print(f"  {k}: {v!r}")
    return 0


# ── reset ─────────────────────────────────────────────────────────────────


def cmd_reset(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    path = state_path_for(spec_dir)
    if path.exists():
        path.unlink()
        print(f"loop-cohort: deleted {path}")
    else:
        print(f"loop-cohort: reset — state.json already absent at {path}")
    return 0


# ── approve-plan ──────────────────────────────────────────────────────────

class UnreadableArtifact(Exception):
    """The artifact exists but could not be read as UTF-8 markdown."""


def _read_md_status(path: Path) -> str | None:
    """Return the canonical status token, or None when the file has none.

    None means "no status line", which callers legitimately skip. A file that
    cannot be *read* is a different thing and must not be silently skipped —
    it raises, so the caller stops with a reason instead of proceeding on a
    guard that quietly did nothing.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise UnreadableArtifact(f"{path.name}: {exc}") from exc
    try:
        return _lint_spec_status().parse_status(text)
    except ImportError:
        return None


# Normalizing the status token out of the hash also removed the incidental
# detection of a *regressed* status: an approved run whose spec.md went back to
# Draft used to trip the byte compare. Assert it directly instead, at every verb
# that reads a pinned artifact — a compensating control that covers one of three
# call sites is not a compensating control.
#
# An absent or unparseable token is skipped, not stopped: plan fixtures
# legitimately carry no status line, and this must not become a new way for a
# CODE-* pre-guard to go red.
_LEGAL_AFTER_APPROVAL = {
    "spec.md": ("Approved", "Implementing", "Shipped"),
    "plan.md": ("Approved", "Executing", "Done"),
}


def _assert_status_legal(verb: str, *paths: Path) -> int | None:
    """Return a stop() code when a pinned artifact's status has regressed."""
    for path in paths:
        allowed = _LEGAL_AFTER_APPROVAL.get(path.name)
        if allowed is None or not path.exists():
            continue
        try:
            token = _read_md_status(path)
        except UnreadableArtifact as exc:
            return stop(f"{verb}: {exc}")
        if token is not None and token not in allowed:
            return stop(
                f"{verb}: {path.name} Status is {token!r}; expected one of "
                f"{list(allowed)} after approval"
            )
    return None


def cmd_approve_plan(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, args.expect_run_id, verb="approve-plan")
    if err is not None:
        return err

    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"
    if not spec_path.exists():
        return stop(f"approve-plan: spec.md not found at {spec_path}")
    if not plan_path.exists():
        return stop(f"approve-plan: plan.md not found at {plan_path}")

    # Idempotency: if already approved, verify hashes before writing.
    current_status = state.get("plan_review_status", "pending")
    if current_status == "approved":
        spec_hash = sha256_canonical_contract(spec_path)
        plan_hash = sha256_canonical_contract(plan_path)
        stored_spec_hash = state.get("approved_spec_hash", "")
        stored_plan_hash = state.get("approved_plan_hash", "")
        if spec_hash == stored_spec_hash and plan_hash == stored_plan_hash:
            # The crash-window guard below sits on the pending branch only, so
            # without this a replay after a status regression reports a clean
            # no-op against a spec that no longer claims to be approved.
            err = _assert_status_legal("approve-plan", spec_path, plan_path)
            if err is not None:
                return err
            print(
                f"loop-cohort: approve-plan already recorded for {spec_dir.name} (no-op)"
            )
            return 0
        spec_changed = spec_hash != stored_spec_hash
        plan_changed = plan_hash != stored_plan_hash
        return stop(
            f"approve-plan: artifact changed since approval — "
            f"spec_changed={spec_changed}, plan_changed={plan_changed}; "
            + _BOTH_CAUSES
        )

    # Crash-window guard: verify that both spec.md and plan.md still carry
    # Status: Approved before recording the baseline.  This detects the common
    # crash-window scenario (a file reverted to an earlier status while
    # plan_review_status was still "pending") but does NOT detect content
    # changes that leave the Status token unchanged.
    try:
        spec_status = _read_md_status(spec_path)
        plan_status_now = _read_md_status(plan_path)
    except UnreadableArtifact as exc:
        return stop(f"approve-plan: {exc}")
    if spec_status != "Approved":
        return stop(
            f"approve-plan: spec.md Status is {spec_status!r}; expected Approved "
            "(files may have changed in the crash window after plan-approved)"
        )
    if plan_status_now != "Approved":
        return stop(
            f"approve-plan: plan.md Status is {plan_status_now!r}; expected Approved "
            "(files may have changed in the crash window after plan-approved)"
        )

    state["plan_review_status"] = "approved"
    state["approved_spec_hash"] = sha256_canonical_contract(spec_path)
    state["approved_plan_hash"] = sha256_canonical_contract(plan_path)
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: approve-plan for {spec_dir.name} "
        f"(approved_spec_hash={state['approved_spec_hash'][:12]}… "
        f"approved_plan_hash={state['approved_plan_hash'][:12]}…)"
    )
    return 0


# ── plan check-current ────────────────────────────────────────────────────


def cmd_plan_check_current(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))

    if state.get("plan_review_status") != "approved":
        return stop("plan_review_status: pending")

    spec_path = spec_dir / "spec.md"
    plan_path = spec_dir / "plan.md"
    if not spec_path.exists():
        return stop(f"plan check-current: spec.md not found at {spec_path}")
    if not plan_path.exists():
        return stop(f"plan check-current: plan.md not found at {plan_path}")

    err = _assert_status_legal("plan check-current", spec_path, plan_path)
    if err is not None:
        return err

    current_spec_hash = sha256_canonical_contract(spec_path)
    if state.get("approved_spec_hash") != current_spec_hash:
        return stop(
            "plan check-current: spec.md no longer matches the approved baseline — "
            + _BOTH_CAUSES
            + f" (approved={state.get('approved_spec_hash', 'null')!r} "
            f"current={current_spec_hash!r})"
        )

    current_plan_hash = sha256_canonical_contract(plan_path)
    if state.get("approved_plan_hash") != current_plan_hash:
        return stop(
            "plan check-current: plan.md no longer matches the approved baseline — "
            + _BOTH_CAUSES
            + f" (approved={state.get('approved_plan_hash', 'null')!r} "
            f"current={current_plan_hash!r})"
        )

    if args.require_schedule:
        if state.get("plan_hash") != state.get("approved_plan_hash"):
            return stop(
                "plan check-current: plan_hash != approved_plan_hash "
                "(schedule not run or run on a different plan version); "
                + _BOTH_CAUSES
            )
        waves = state.get("schedule_waves", [])
        if not waves:
            return stop("plan check-current: schedule_waves is empty (run schedule first)")
        idx = state.get("current_wave_index", 0)
        if not (0 <= idx < len(waves)):
            return stop(
                f"plan check-current: current_wave_index={idx} out of range "
                f"[0, {len(waves)})"
            )

    print(f"loop-cohort: plan check-current OK for {spec_dir.name}")
    return 0


# ── schedule ──────────────────────────────────────────────────────────────


def _schedule_check_current_impl(spec_dir: Path) -> int:
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    plan_path = spec_dir / "plan.md"
    if not plan_path.exists():
        return stop(f"schedule check-current: plan.md not found at {plan_path}")
    err = _assert_status_legal("schedule check-current", plan_path)
    if err is not None:
        return err

    current_hash = sha256_canonical_contract(plan_path)
    stored = state.get("plan_hash")
    if stored != current_hash:
        return stop(
            "schedule check-current: plan.md no longer matches the scheduled "
            "baseline — " + _BOTH_CAUSES
            + f" (stored={stored!r} current={current_hash!r})"
        )
    print(f"loop-cohort: schedule check-current OK for {spec_dir.name}")
    return 0


def _schedule_run_impl(spec_dir: Path, expect_run_id: str, plan_override: str | None) -> int:
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, expect_run_id, verb="schedule")
    if err is not None:
        return err

    plan_path_canonical = spec_dir / "plan.md"
    if plan_override and Path(plan_override).resolve() != plan_path_canonical.resolve():
        return stop(
            f"schedule: --plan must point to {plan_path_canonical}; alternate paths create "
            "unusable state because schedule check-current always hashes plan.md"
        )
    plan_path = plan_path_canonical
    if not plan_path.exists():
        return stop(f"plan not found at {plan_path}")
    plan_text = plan_path.read_text(encoding="utf-8")
    ordered, deps = parse_plan(plan_text)
    if not ordered:
        return stop(f"no '## T<n>' or '### T<n>' tasks found in {plan_path}")

    cyc = detect_cycles(ordered, deps)
    if cyc:
        return stop(
            f"dependency cycle among tasks: {', '.join(cyc)} — unschedulable; "
            "the plan is wrong, fix Depends on:"
        )
    fwd = detect_forward_refs(ordered, deps)
    if fwd:
        pairs = ", ".join(f"{a}->{b}" for a, b in fwd)
        print(
            f"loop-cohort: warning — forward-reference(s) in {spec_dir.name} "
            f"(dep authored later; reordered below): {pairs}",
            file=sys.stderr,
        )

    waves, _ = topological_waves(ordered, deps)
    touches = parse_touches_by_task(plan_text)
    print(
        f"loop-cohort: topological order for {spec_dir.name} "
        "(run sequentially by default; waves mark what *could* parallelize):"
    )
    for i, wave in enumerate(waves, 1):
        print(f"  wave {i}: {', '.join(wave)}")
        if len(wave) > 1:
            verdict = wave_touches_disjoint([touches.get(t) for t in wave])
            print(
                f"    predicted-disjoint: {verdict}  "
                "(Touches: screen — serialize-only, never a greenlight)"
            )

    plan_hash = sha256_canonical_contract(plan_path)
    state["plan_hash"] = plan_hash
    state["schedule_waves"] = waves
    state["current_wave_index"] = 0
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: schedule persisted for {spec_dir.name} "
        f"({len(waves)} wave(s), plan_hash={plan_hash[:12]}…)"
    )
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    first = args.schedule_first
    second = getattr(args, "schedule_second", None)
    if first == "check-current":
        if not second:
            return stop("schedule check-current: <spec-dir> required")
        try:
            spec_dir = _resolve_spec_dir(second)
        except ValueError as exc:
            return stop(str(exc))
        return _schedule_check_current_impl(spec_dir)
    # first is the spec-dir
    try:
        spec_dir = _resolve_spec_dir(first)
    except ValueError as exc:
        return stop(str(exc))
    if not args.expect_run_id:
        return stop("schedule: --expect-run-id is required")
    plan_override = getattr(args, "plan", None)
    return _schedule_run_impl(spec_dir, args.expect_run_id, plan_override)


# ── check (phase termination) ─────────────────────────────────────────────


def cmd_check(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    # The `implement` phase is a no-op stub (returns 0 for any state); skip
    # schema validation there so pre-Phase-1 state files don't break the hook.
    # For phases that actually evaluate counters, reject incompatible state.
    if args.phase != "implement" and state.get("schema_version") != 1:
        sv = state.get("schema_version")
        return stop(f"check: unsupported schema_version={sv!r} (expected 1); run reset pair")
    return _evaluate(state, args.phase)


def _evaluate(state: dict, phase: str) -> int:
    if phase == "implement":
        # Phase-1 compatibility stub: exits 0 unconditionally for any
        # valid Phase-1 state. Token-budget and same-error fields are
        # Phase-2 reserved — no Phase-1 writers or guards defined.
        return 0

    if phase == "gates-failed":
        count = int(state.get("implementation_retry_count", 0))
        cap = int(state.get("max_implementation_retries", DEFAULTS["max_implementation_retries"]))
        if count >= cap:
            return stop(
                f"implementation retry cap reached ({count}/{cap}); "
                "reset and start a new run"
            )
        return 0

    if phase == "review":
        count = int(state.get("review_retry_count", 0))
        cap = int(state.get("max_review_retries", DEFAULTS["max_review_retries"]))
        if count >= cap:
            return stop(
                f"review retry cap reached ({count}/{cap}); "
                "reset and start a new run"
            )
        return 0

    return stop(f"unknown phase {phase!r}")


# ── wave check / advance ──────────────────────────────────────────────────


def cmd_wave_check(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))

    waves = state.get("schedule_waves", [])
    idx = int(state.get("current_wave_index", 0))
    n = len(waves)

    # Optional index check (used by wave-passed guard)
    if args.wave_index is not None and idx != args.wave_index:
        return stop(
            f"wave check: current_wave_index={idx} does not match "
            f"--wave-index {args.wave_index}"
        )

    if args.expect == "more":
        if idx < n - 1:
            print(f"loop-cohort: wave check more — wave_index={idx} has more waves (total={n})")
            return 0
        return stop(f"wave check more: no more waves (current={idx}, total={n})")

    if args.expect == "last":
        if idx == n - 1:
            print(f"loop-cohort: wave check last — wave_index={idx} is the last wave (total={n})")
            return 0
        return stop(f"wave check last: not the last wave (current={idx}, total={n})")

    return stop(f"wave check: unknown --expect value {args.expect!r}")


def cmd_wave_advance(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, args.expect_run_id, verb="wave advance")
    if err is not None:
        return err

    n_arg = args.from_index
    waves = state.get("schedule_waves", [])
    n = len(waves)

    if n == 0:
        return stop("wave advance: schedule_waves is empty")
    if n_arg < 0:
        return stop(f"wave advance: --from-index must be >= 0 (got {n_arg})")
    if n_arg >= n:
        return stop(
            f"wave advance: --from-index {n_arg} >= len(schedule_waves) {n}"
        )
    if n_arg == n - 1:
        return stop(
            f"wave advance: cannot advance from the final wave (index={n_arg}); "
            "use gates-clean to exit the final wave"
        )

    idx = int(state.get("current_wave_index", 0))
    if idx == n_arg:
        state["current_wave_index"] = n_arg + 1
        write_state_atomic(spec_dir, state)
        print(
            f"loop-cohort: wave advance {n_arg} → {n_arg + 1} for {spec_dir.name}"
        )
        return 0
    if idx == n_arg + 1:
        print(
            f"loop-cohort: wave advance already applied "
            f"(current_wave_index={idx}) for {spec_dir.name}"
        )
        return 0
    return stop(
        f"wave advance: current_wave_index={idx} does not match "
        f"--from-index {n_arg} or {n_arg + 1}"
    )


# ── record-attempt ────────────────────────────────────────────────────────


def cmd_record_attempt(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    if args.phase != "implement":
        return stop(f"record-attempt: --phase must be 'implement' (got {args.phase!r})")
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, args.expect_run_id, verb="record-attempt")
    if err is not None:
        return err

    # The cycle-id must be <run_id>:<decimal-sequence>; the run_id prefix must match.
    cycle_id = args.cycle_id
    _parts = cycle_id.split(":", 1)
    if len(_parts) != 2 or not _parts[1].isdigit():
        return stop(
            f"record-attempt: --cycle-id must be '<run_id>:<decimal-sequence>' "
            f"(got {cycle_id!r})"
        )
    run_id_prefix = _parts[0]
    if run_id_prefix != args.expect_run_id:
        return stop(
            f"record-attempt: run_id prefix in --cycle-id ({run_id_prefix!r}) "
            f"does not match --expect-run-id ({args.expect_run_id!r})"
        )

    last_id = state.get("last_record_attempt_cycle_id")
    if last_id == cycle_id:
        print(
            f"loop-cohort: record-attempt already applied for cycle {cycle_id!r} "
            f"(idempotent no-op)"
        )
        return 0

    state["implementation_retry_count"] = int(state.get("implementation_retry_count", 0)) + 1
    state["last_record_attempt_cycle_id"] = cycle_id
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: record-attempt implementation_retry_count="
        f"{state['implementation_retry_count']} cycle={cycle_id!r} "
        f"for {spec_dir.name}"
    )
    return 0


# ── review inspect / record ───────────────────────────────────────────────

FINDING_LINE_RE = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*`(?P<citation>[^`]+)`"
)
# frontend-reviewer: **title.** file:line. (unquoted file:line after title)
FINDING_LINE_RE_UNQUOTED = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*(?P<citation>\S+:\d+)"
)
# experience-reviewer: **title.** Where: <location>. (no file:line)
FINDING_LINE_RE_WHERE = re.compile(
    r"^(?P<title>\*\*\d+\.[^*]+\*\*)\s*[\.\s]*\s*Where:\s*(?P<location>[^.]+)"
)


def parse_findings(report_text: str) -> list[str]:
    """Return SHA-256 fingerprints for findings in a reviewer report.

    Algorithm pinned by the work-loop SKILL §REVIEW:
        sha256("<file>|<line>|<title>")
    where <file> is the cited path exactly as written, <line> is the first
    integer after the first colon in the citation, and <title> is the
    bolded heading including the surrounding `**` markers.

    Supports three formats:
    - adversarial-reviewer: **title** `file:line`  (backtick-quoted citation)
    - frontend-reviewer:    **title.** file:line.  (unquoted file:line)
    - experience-reviewer:  **title.** Where: loc. (location; key uses loc|0|title)
    """
    fingerprints: list[str] = []
    for raw in report_text.splitlines():
        line = raw.strip()
        if not line.startswith("**"):
            continue
        # Try backtick-quoted citation first (adversarial-reviewer)
        m = FINDING_LINE_RE.match(line)
        if m:
            title = m.group("title").strip()
            citation = m.group("citation").strip()
            if ":" not in citation:
                continue
            file_part, _, rest = citation.partition(":")
            line_match = re.match(r"\d+", rest)
            if not line_match:
                continue
            key = f"{file_part}|{line_match.group(0)}|{title}"
            fingerprints.append(
                hashlib.sha256(key.encode("utf-8")).hexdigest()
            )
            continue
        # Try Where: <location> (experience-reviewer)
        m = FINDING_LINE_RE_WHERE.match(line)
        if m:
            title = m.group("title").strip()
            location = m.group("location").strip()
            key = f"{location}|0|{title}"
            fingerprints.append(
                hashlib.sha256(key.encode("utf-8")).hexdigest()
            )
            continue
        # Try unquoted file:line (frontend-reviewer)
        m = FINDING_LINE_RE_UNQUOTED.match(line)
        if m:
            title = m.group("title").strip()
            citation = m.group("citation").strip()
            file_part, _, rest = citation.partition(":")
            line_match = re.match(r"\d+", rest)
            if not line_match:
                continue
            key = f"{file_part}|{line_match.group(0)}|{title}"
            fingerprints.append(
                hashlib.sha256(key.encode("utf-8")).hexdigest()
            )
    return fingerprints


def _resolved_report(candidate: str) -> Path:
    """Normalise the CLI-supplied `--report` path at the argv boundary.

    Normalise-only, deliberately. The two `--root` linters in this skill raise
    on an unusable path, but `--report` must not: `review inspect` classifies an
    unreadable report as `invalid`, which the work-loop SKILL documents as a
    Surface signal rather than a crash. Raising here would convert a defined
    outcome into an operational error.

    The `resolve()` still does the job it is here for — it puts the
    normalisation adjacent to the argv read, where a taint analyser can see it,
    instead of leaving a raw `Path(args.report)` as the boundary.
    """
    try:
        return Path(candidate).resolve()
    except (OSError, ValueError, RuntimeError):
        # resolve() raises on an embedded null (ValueError) and on Windows
        # reserved names (OSError). Falling back to the unresolved path keeps
        # the value flowing to _classify_report, which classifies it `invalid`
        # at exit 0 — the defined outcome. Raising here would reintroduce
        # exactly the operational error this helper's docstring rules out.
        return Path(candidate)


def _classify_report(report_path: Path, state: dict) -> dict:
    """Classify a reviewer report. Exits 0 for all report-content outcomes.

    Returns a dict with keys: classification, fingerprints, matches_previous_round.
    """
    try:
        report_text = report_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {
            "classification": "invalid",
            "fingerprints": [],
            "matches_previous_round": False,
        }

    fps = parse_findings(report_text)
    has_clean = (
        CLEAN_SUBSTRING in report_text
        or _SHIP_IT_RE.search(report_text) is not None
    )

    if fps:
        classification = "findings"
    elif has_clean:
        classification = "clean"
    else:
        classification = "invalid"

    canonical_fps = sorted(set(fps))
    previous = sorted(set(state.get("finding_fingerprints", [])))

    # Empty-vs-empty is always false (not stasis — no meaningful comparison)
    matches_prev = bool(canonical_fps and canonical_fps == previous)

    return {
        "classification": classification,
        "fingerprints": canonical_fps,
        "matches_previous_round": matches_prev,
    }


def cmd_review_inspect(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        # Operational error (spec-dir unresolvable or state.json unreadable)
        return stop(str(exc))

    report_path = _resolved_report(args.report)
    result = _classify_report(report_path, state)

    if args.json:
        print(json.dumps(result))
    else:
        print(
            f"loop-cohort: review inspect "
            f"classification={result['classification']} "
            f"fingerprints={len(result['fingerprints'])} "
            f"matches_previous_round={result['matches_previous_round']}"
        )
    return 0  # content outcomes always exit 0


def cmd_review_record(args: argparse.Namespace) -> int:
    try:
        spec_dir = _resolve_spec_dir(args.spec_dir)
    except ValueError as exc:
        return stop(str(exc))
    try:
        state = read_state(spec_dir)
    except (FileNotFoundError, ValueError) as exc:
        return stop(str(exc))
    err = _validate_run_id(state, args.expect_run_id, verb="review record")
    if err is not None:
        return err

    if getattr(args, "all_skipped", False):
        # All-skipped branch: every warranted reviewer was a named skip
        state["previous_finding_fingerprints"] = list(state.get("finding_fingerprints", []))
        state["finding_fingerprints"] = []
        state["review_round_count"] = int(state.get("review_round_count", 0)) + 1
        write_state_atomic(spec_dir, state)
        print(
            f"loop-cohort: review record (all-skipped) "
            f"round={state['review_round_count']} for {spec_dir.name}"
        )
        return 0

    if args.fingerprint:
        # Findings branch: --fingerprint <hex> ...
        fingerprints = sorted(set(args.fingerprint))
        bad = [fp for fp in fingerprints if not _RE_FINGERPRINT.match(fp)]
        if bad:
            return stop(
                f"review record: --fingerprint must be lowercase 64-char SHA-256 hex "
                f"(40-char SHA-1 still accepted for a run that predates core 2.3.0); "
                f"invalid: {bad!r}"
            )
        state["previous_finding_fingerprints"] = list(state.get("finding_fingerprints", []))
        state["finding_fingerprints"] = fingerprints
        state["review_retry_count"] = int(state.get("review_retry_count", 0)) + 1
        state["review_round_count"] = int(state.get("review_round_count", 0)) + 1
        write_state_atomic(spec_dir, state)
        print(
            f"loop-cohort: review record (findings) "
            f"round={state['review_round_count']} retry={state['review_retry_count']} "
            f"fingerprints={len(fingerprints)} for {spec_dir.name}"
        )
        return 0

    # Clean branch: --report <path>
    if not args.report:
        return stop("review record: one of --report or --fingerprint is required")
    report_path = _resolved_report(args.report)
    result = _classify_report(report_path, state)
    if result["classification"] != "clean":
        cls = result["classification"]
        return stop(
            f"review record --report: report classified as {cls!r}; "
            "use --fingerprint for a findings round"
        )

    state["previous_finding_fingerprints"] = list(state.get("finding_fingerprints", []))
    state["finding_fingerprints"] = []
    state["review_round_count"] = int(state.get("review_round_count", 0)) + 1
    # review_retry_count unchanged on clean review
    write_state_atomic(spec_dir, state)
    print(
        f"loop-cohort: review record (clean) "
        f"round={state['review_round_count']} "
        f"retry={state['review_retry_count']} for {spec_dir.name}"
    )
    return 0


# ── disabled Phase-1 verbs ────────────────────────────────────────────────


def cmd_dispatch_decision(args: argparse.Namespace) -> int:
    return _disabled("dispatch-decision")


def cmd_auto_parallel(args: argparse.Namespace) -> int:
    return _disabled("auto-parallel")


def cmd_worktree_preflight(args: argparse.Namespace) -> int:
    return _disabled("worktree preflight")


def cmd_worktree_add(args: argparse.Namespace) -> int:
    return _disabled("worktree add")


def cmd_worktree_record(args: argparse.Namespace) -> int:
    return _disabled("worktree record")


def cmd_worktree_list(args: argparse.Namespace) -> int:
    return _disabled("worktree list")


def cmd_worktree_merge(args: argparse.Namespace) -> int:
    return _disabled("worktree merge")


def cmd_worktree_cleanup(args: argparse.Namespace) -> int:
    return _disabled("worktree cleanup")


# ── dispatcher ────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="loop-cohort", description=__doc__)
    sub = p.add_subparsers(dest="verb", required=True)

    # init
    sp = sub.add_parser("init", help="initialise state.json from the bundled template")
    sp.add_argument("spec_dir")
    sp.add_argument("--run-id", required=True, dest="run_id",
                    help="UUID generated by loop-engine init")
    sp.set_defaults(func=cmd_init)

    # identity
    sp = sub.add_parser(
        "identity",
        help="read-only: verify schema_version=1 and optionally run_id match",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--expect-run-id", dest="expect_run_id", default=None)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_identity)

    # status
    sp = sub.add_parser(
        "status",
        help="read-only: return cohort fields for session resumption",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_status)

    # reset
    sp = sub.add_parser("reset", help="delete state.json; idempotent")
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_reset)

    # check
    sp = sub.add_parser("check", help="phase termination check")
    sp.add_argument("spec_dir")
    sp.add_argument("--phase", required=True, choices=PHASES)
    sp.set_defaults(func=cmd_check)

    # approve-plan
    sp = sub.add_parser(
        "approve-plan",
        help="record plan_review_status=approved and hash spec/plan",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--expect-run-id", required=True, dest="expect_run_id")
    sp.set_defaults(func=cmd_approve_plan)

    # plan (namespace with sub-verbs)
    sp_plan = sub.add_parser("plan", help="plan-approval guard verbs")
    plan_sub = sp_plan.add_subparsers(dest="plan_verb", required=True)
    sp = plan_sub.add_parser(
        "check-current",
        help="verify plan_review_status, spec/plan hashes, and optionally schedule",
    )
    sp.add_argument("spec_dir")
    sp.add_argument(
        "--require-schedule", action="store_true", dest="require_schedule",
        help="also verify plan_hash matches approved_plan_hash and schedule_waves non-empty",
    )
    sp.set_defaults(func=cmd_plan_check_current)

    # schedule (custom dispatch: first positional is spec-dir or "check-current")
    sp_sched = sub.add_parser(
        "schedule",
        help="DAG-order schedule (persists plan_hash + waves) or 'check-current'",
    )
    sp_sched.add_argument(
        "schedule_first",
        metavar="<spec-dir> | check-current",
        help="spec directory path, or 'check-current' for the read-only hash check",
    )
    sp_sched.add_argument(
        "schedule_second",
        nargs="?",
        metavar="<spec-dir>",
        help="spec directory path when first arg is 'check-current'",
    )
    sp_sched.add_argument("--expect-run-id", dest="expect_run_id", default=None)
    sp_sched.add_argument(
        "--plan", default=None,
        help="path to plan.md (default: <spec-dir>/plan.md)",
    )
    sp_sched.set_defaults(func=cmd_schedule)

    # record-attempt
    sp = sub.add_parser(
        "record-attempt",
        help="record a gates-failed repair attempt (idempotent per cycle-id)",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--phase", required=True, choices=["implement"])
    sp.add_argument("--cycle-id", required=True, dest="cycle_id")
    sp.add_argument("--expect-run-id", required=True, dest="expect_run_id")
    sp.set_defaults(func=cmd_record_attempt)

    # wave (namespace with sub-verbs)
    sp_wave = sub.add_parser("wave", help="wave-advance and guard verbs")
    wave_sub = sp_wave.add_subparsers(dest="wave_verb", required=True)

    sp = wave_sub.add_parser(
        "check",
        help="read-only: verify more/last wave guard",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--expect", required=True, choices=["more", "last"])
    sp.add_argument("--wave-index", type=int, dest="wave_index", default=None)
    sp.set_defaults(func=cmd_wave_check)

    sp = wave_sub.add_parser(
        "advance",
        help="idempotent: advance current_wave_index from n to n+1",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--from-index", required=True, type=int, dest="from_index")
    sp.add_argument("--expect-run-id", required=True, dest="expect_run_id")
    sp.set_defaults(func=cmd_wave_advance)

    # review (namespace with sub-verbs)
    sp_review = sub.add_parser("review", help="review-phase state mutations")
    review_sub = sp_review.add_subparsers(dest="review_verb", required=True)

    sp = review_sub.add_parser(
        "inspect",
        help="read-only: classify a reviewer report (clean/findings/invalid)",
    )
    sp.add_argument("spec_dir")
    sp.add_argument("--report", required=True)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_review_inspect)

    sp = review_sub.add_parser(
        "record",
        help="rotate fingerprints and bump counters after a CODE-REVIEW round",
    )
    sp.add_argument("spec_dir")
    _rr_grp = sp.add_mutually_exclusive_group(required=True)
    _rr_grp.add_argument("--report", default=None,
                         help="path to a clean reviewer report")
    _rr_grp.add_argument(
        "--fingerprint",
        action="append",
        default=None,
        help="explicit fingerprint (hex sha256); use for findings rounds",
    )
    _rr_grp.add_argument(
        "--all-skipped",
        action="store_true",
        default=False,
        dest="all_skipped",
        help="all warranted reviewers were named skips; bumps round count, clears fingerprints",
    )
    sp.add_argument("--expect-run-id", required=True, dest="expect_run_id")
    sp.set_defaults(func=cmd_review_record)

    # dispatch-decision (disabled)
    sp = sub.add_parser(
        "dispatch-decision",
        help="(disabled in Phase 1 — exits non-zero)",
    )
    sp.add_argument("--category", action="append", default=[])
    sp.add_argument("--branch", action="append", default=[])
    sp.add_argument("--base", default=None)
    sp.set_defaults(func=cmd_dispatch_decision)

    # auto-parallel (disabled)
    sp = sub.add_parser(
        "auto-parallel",
        help="(disabled in Phase 1 — exits non-zero)",
    )
    sp.add_argument("spec_dir", nargs="?")
    sp.add_argument("--off", action="store_true")
    sp.set_defaults(func=cmd_auto_parallel)

    # worktree (disabled)
    sp_wt = sub.add_parser("worktree", help="(disabled in Phase 1 — exits non-zero)")
    wt_sub = sp_wt.add_subparsers(dest="worktree_verb", required=True)

    for wt_verb, wt_func, wt_help in [
        ("preflight", cmd_worktree_preflight, "disabled"),
        ("add", cmd_worktree_add, "disabled"),
        ("record", cmd_worktree_record, "disabled"),
        ("list", cmd_worktree_list, "disabled"),
        ("merge", cmd_worktree_merge, "disabled"),
        ("cleanup", cmd_worktree_cleanup, "disabled"),
    ]:
        sp = wt_sub.add_parser(wt_verb, help=wt_help)
        sp.add_argument("spec_dir", nargs="?")
        if wt_verb == "record":
            # Preserve original signature so callers get the "disabled" message
            # instead of an argparse "unrecognized arguments" error.
            sp.add_argument("task_id", nargs="?")
            sp.add_argument("--status", choices=WORKTREE_STATUSES)
            sp.add_argument("--report")
        else:
            sp.add_argument("args", nargs="*")
        sp.set_defaults(func=wt_func)

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
