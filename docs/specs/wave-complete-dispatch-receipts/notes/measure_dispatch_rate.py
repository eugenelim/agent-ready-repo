#!/usr/bin/env python3
"""Measure how often an engine-driven work-loop run dispatches an implementer.

This is the generator for the dispatch-rate figures this spec rests on. The
figures are not copied into the spec: the spec cites this script, and
`notes/verification-ledger.md` records one run of it with its output. Re-running
it is how the claim is checked, because the session count grows over time and a
transcribed number silently goes stale.

Usage, from the repository root:

    python3 docs/specs/wave-complete-dispatch-receipts/notes/measure_dispatch_rate.py \
        --since 2026-09-15

What counts, and why:

* A *session* is one transcript file under the project directories the `--glob`
  option selects. Its timestamp is the earliest record in the file.
* An *engine-driven run* is a session containing a Bash tool call whose command
  invokes `loop-cohort[.py] schedule <arg>`. The subcommand and an argument are
  both required. A looser match — any command mentioning both "loop-cohort" and
  "schedule" — over-counts: it matches this script, a `--help` listing, and
  prose in a heredoc. The tight and loose counts are both reported so the gap
  is visible rather than assumed away.
* A *dispatch* is a Task/Agent tool call whose `subagent_type` contains
  "implementer".
* A *controller edit* is an Edit, Write, MultiEdit, or NotebookEdit tool call
  made by the controller itself.

Limits, stated because they bound the claim:

* Transcripts are per-machine and per-user. This measures one workstation's
  history, not every run of the loop anywhere.
* A session that ran `schedule` and then crashed counts as engine-driven.
* `--self-exclude` drops the transcript of the session running the script, which
  would otherwise match on this file's own text.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

# `loop-cohort` or `loop-cohort.py`, an optional closing quote from the shell
# invocation, whitespace, the literal subcommand, whitespace, then an argument.
TIGHT = re.compile(r"""loop-cohort(?:\.py)?['"]?\s+schedule\s+(\S+)""")
# Deliberately over-broad, reported alongside the tight count as a control.
LOOSE = re.compile(r"loop-cohort")

EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})
AGENT_TOOLS = frozenset({"Task", "Agent"})


def iter_tool_calls(path: str):
    """Yield (tool_name, input_dict) for every tool call in one transcript."""
    with Path(path).open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            yield record


def earliest_timestamp(records) -> dt.datetime | None:
    stamps = []
    for record in records:
        raw = record.get("timestamp")
        if not raw:
            continue
        try:
            stamps.append(dt.datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except ValueError:
            continue
    return min(stamps) if stamps else None


def scan(path: str) -> dict:
    records = list(iter_tool_calls(path))
    result = {
        "path": path,
        "timestamp": earliest_timestamp(records),
        "schedule_args": [],
        "loose_hits": 0,
        "implementer_dispatches": 0,
        "controller_edits": 0,
        "agents": collections.Counter(),
    }
    for record in records:
        message = record.get("message") or {}
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            name = block.get("name")
            payload = block.get("input") or {}
            if name == "Bash":
                command = payload.get("command") or ""
                result["schedule_args"] += [m.group(1) for m in TIGHT.finditer(command)]
                result["loose_hits"] += len(LOOSE.findall(command))
            elif name in EDIT_TOOLS:
                result["controller_edits"] += 1
            elif name in AGENT_TOOLS:
                kind = str(payload.get("subagent_type") or payload.get("agent_type") or "?")
                result["agents"][kind] += 1
                if "implementer" in kind:
                    result["implementer_dispatches"] += 1
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--glob",
        default="~/.claude/projects/*agent-ready-repo*/*.jsonl",
        help="transcript glob (default: this repository's project directories)",
    )
    parser.add_argument(
        "--since",
        required=True,
        help="ISO date; sessions whose earliest record is on or after it",
    )
    parser.add_argument(
        "--self-exclude",
        default=os.environ.get("CLAUDE_SESSION_ID", ""),
        help="substring of the running session's transcript path, excluded",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)

    cutoff = dt.datetime.fromisoformat(args.since).replace(tzinfo=dt.UTC)
    # Split the expanded pattern into an anchor and a relative glob so the walk
    # goes through Path.glob rather than the os-path glob module.
    expanded = Path(args.glob).expanduser()
    anchor = Path(expanded.anchor) if expanded.anchor else Path()
    relative = expanded.relative_to(anchor) if expanded.anchor else expanded
    paths = sorted(str(match) for match in anchor.glob(str(relative)))
    if args.self_exclude:
        paths = [p for p in paths if args.self_exclude not in p]
    if not paths:
        print(f"no transcripts matched {args.glob}", file=sys.stderr)
        return 2

    scanned = [scan(p) for p in paths]
    in_window = [s for s in scanned if s["timestamp"] and s["timestamp"] >= cutoff]
    engine_driven = [s for s in in_window if s["schedule_args"]]
    loose_only = [
        s for s in in_window if s["loose_hits"] and not s["schedule_args"]
    ]
    dispatched = [s for s in engine_driven if s["implementer_dispatches"]]
    silent = [s for s in engine_driven if not s["implementer_dispatches"]]

    report = {
        "glob": args.glob,
        "since": args.since,
        "transcripts_scanned": len(scanned),
        "sessions_in_window": len(in_window),
        "engine_driven_runs": len(engine_driven),
        "engine_driven_runs_loose_match_only": len(loose_only),
        "runs_dispatching_implementer": len(dispatched),
        "runs_not_dispatching": len(silent),
        "controller_edits_in_non_dispatching_runs": sum(
            s["controller_edits"] for s in silent
        ),
        "dispatches_per_dispatching_run": sorted(
            s["implementer_dispatches"] for s in dispatched
        ),
        "spec_dirs_scheduled": sorted(
            {a for s in engine_driven for a in s["schedule_args"]}
        ),
    }
    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print(f"transcript glob            : {report['glob']}")
    print(f"window start               : {report['since']}")
    print(f"transcripts scanned        : {report['transcripts_scanned']}")
    print(f"sessions in window         : {report['sessions_in_window']}")
    print(f"engine-driven runs (tight) : {report['engine_driven_runs']}")
    loose_only_count = report["engine_driven_runs_loose_match_only"]
    print(
        f"  loose-match-only sessions: {loose_only_count}"
        "   <- the over-count a loose regex would add"
    )
    print(f"  dispatched an implementer: {report['runs_dispatching_implementer']}")
    print(f"  did not dispatch         : {report['runs_not_dispatching']}")
    print(f"controller edits in those  : {report['controller_edits_in_non_dispatching_runs']}")
    print(f"dispatches per dispatching run: {report['dispatches_per_dispatching_run']}")
    print("\nper engine-driven run:")
    for s in sorted(engine_driven, key=lambda s: s["timestamp"]):
        mark = "dispatch" if s["implementer_dispatches"] else "  none  "
        project = Path(s["path"]).parent.name[-34:]
        print(
            f"  {s['timestamp'].date()}  {mark}"
            f"  implementers={s['implementer_dispatches']:<3}"
            f" edits={s['controller_edits']:<5} {project}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
