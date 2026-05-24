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
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULTS = {
    "max_iterations": 5,
    "token_budget_cap_pct": 0.85,
    "consecutive_same_error_threshold": 3,
}

PHASES = ("plan", "implement", "review")
WORKTREE_STATUSES = ("ready", "blocked", "failed")

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "assets" / "state.json"


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
        fingerprints.append(hashlib.sha1(key.encode("utf-8")).hexdigest())
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

    sp = sub.add_parser("check", help="phase termination check")
    sp.add_argument("spec_dir")
    sp.add_argument("--phase", required=True, choices=PHASES)
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("approve-plan", help="flip plan_review_status to approved")
    sp.add_argument("spec_dir")
    sp.set_defaults(func=cmd_approve_plan)

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
