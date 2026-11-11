"""Compose the flow skill once, in per-issue mode, and read back its rows.

Two constraints shape this module. The flow skill's ``--per-issue`` mode
requires ``--output FILE`` and exits 2 without it, so this view writes a
JSONL file; that file lands outside both roots this view promises to
leave byte-identical, and is removed before the view returns -- including
when the run raises. And the flow skill is reached only through its inert
cache mode: its bypass flag still unlinks stale temporary files from a
cache directory relative to the working directory, and deleting a file is
a write.
"""
from __future__ import annotations

import contextlib
import json
import os
import shutil
import subprocess  # noqa: S404 -- list-form only, never shell=True
import sys
import tempfile
from collections.abc import Generator, Mapping, Sequence
from pathlib import Path
from typing import Any, Callable

#: The only mode through which this view composes the flow skill.
INERT_CACHE_FLAG = "--inert-cache"

_SCRATCH_PREFIX = "jira-epic-outcome-view-"
_PER_ISSUE_FILENAME = "per-issue.jsonl"


class ScratchLocationError(Exception):
    """The temporary directory resolved inside a root that must not change.

    Raised before anything is created: the location is checked, then the
    directory is made under the location that passed. A temporary
    directory configured to sit under the working directory would
    otherwise turn the one disclosed write into a breach of the
    read-only guarantee.
    """


class FlowMetricsError(Exception):
    """The flow skill exited non-zero, or returned output this view cannot read."""


@contextlib.contextmanager
def scratch_per_issue_path(*, cwd_root: Path, pack_root: Path) -> Generator[Path, None, None]:
    """Yield a per-issue JSONL path outside both protected roots.

    The configured temporary location is checked first and the directory
    is created only under a location that passed, so a location inside a
    protected root is refused with nothing created there. The directory
    is removed on the way out whether the body returned or raised: a
    failed run that leaves the file behind fails the same guarantee a
    successful one would, and a removal that fails is surfaced rather
    than swallowed, because a swallowed one is indistinguishable from a
    removal that worked.
    """
    base = Path(tempfile.gettempdir()).resolve()
    for root in (cwd_root, pack_root):
        if _is_within(base, root):
            raise ScratchLocationError(
                f"the temporary directory {base} sits under {root}, which this "
                "view must leave unchanged; set TMPDIR outside it"
            )
    scratch = Path(tempfile.mkdtemp(prefix=_SCRATCH_PREFIX, dir=base)).resolve()
    try:
        yield scratch / _PER_ISSUE_FILENAME
    finally:
        shutil.rmtree(scratch)


def _is_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def build_flow_argv(
    *,
    output: Path,
    scope_args: Sequence[str],
    window: Mapping[str, str],
    include_subtasks: bool,
) -> list[str]:
    """The flow skill invocation: one run, per-issue mode, cache inert."""
    argv = [
        sys.executable,
        "-m",
        "flow_metrics",
        *scope_args,
        "--from",
        window["from"],
        "--to",
        window["to"],
        "--per-issue",
        "--output",
        str(output),
        "--yes",
        INERT_CACHE_FLAG,
    ]
    if include_subtasks:
        argv.append("--include-subtasks")
    return argv


def run_flow_metrics(
    *,
    scripts_dir: Path,
    scope_args: Sequence[str],
    window: Mapping[str, str],
    include_subtasks: bool,
    cwd_root: Path,
    pack_root: Path,
    runner: Callable[..., Any] = subprocess.run,
) -> list[dict[str, Any]]:
    """Run the flow skill once and return its per-issue rows.

    The rows are returned in memory; the JSONL that carried them is gone
    by the time this function does.
    """
    # The flow skill ships as a package under its own `scripts/`, so it is
    # reached by import path rather than by a file path: running it as a
    # directory would strip its package context.
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    parts = [str(scripts_dir), existing] if existing else [str(scripts_dir)]
    env["PYTHONPATH"] = os.pathsep.join(parts)
    # A child interpreter caches bytecode beside the source it imports, which
    # would write `__pycache__` into the installed pack tree -- a tree this
    # view promises to leave byte-identical. The cache is the interpreter's
    # own convenience, not anything this view needs, so it is switched off
    # rather than excused in the guarantee.
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with scratch_per_issue_path(cwd_root=cwd_root, pack_root=pack_root) as output:
        argv = build_flow_argv(
            output=output,
            scope_args=scope_args,
            window=window,
            include_subtasks=include_subtasks,
        )
        completed = runner(argv, env=env, capture_output=True)
        returncode = getattr(completed, "returncode", 0)
        if returncode != 0:
            stderr = getattr(completed, "stderr", b"") or b""
            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")
            raise FlowMetricsError(f"flow reading failed (exit {returncode}): {stderr.strip()}")
        return read_rows(output)


def read_rows(path: Path) -> list[dict[str, Any]]:
    """Parse the per-issue JSONL the flow skill wrote."""
    try:
        text = path.read_text("utf-8")
    except OSError as exc:
        raise FlowMetricsError(f"flow reading produced no per-issue rows: {exc}") from exc
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise FlowMetricsError(f"unreadable per-issue row: {exc}") from exc
        if isinstance(row, dict):
            rows.append(row)
    return rows
