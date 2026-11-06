#!/usr/bin/env python3
"""Brief-level runner: a read-only view of a delivery brief's slices.

Usage: brief-runner.py <status|next|gates|classify> <brief-slug> [--root <dir>]

The runner reads committed records only. It derives every slice's state from the
base commit (the default branch's tip, which the main worktree must have checked
out with no uncommitted change under ``docs/`` or in this skill's own directory),
from the slice worktrees' branch heads, and from the supervisor's own ``status``
output. It writes no file, ref, branch, worktree or store record, and it starts
only read-only Git commands and the ``work-supervisor.py`` that sits beside this
file, with the slice worktree as working directory. It never runs code from a
slice branch.

This module holds the read core the verbs share:

  * the base checks, in order: ``unsupported-git-version``, ``not-main-worktree``,
    ``default-branch-unknown``, ``base-not-default``, ``denied-git-config``,
    ``base-not-committed``;
  * the brief's Spec map, parsed in table order;
  * slice worktree discovery from ``git worktree list --porcelain -z``;
  * each row's readiness (through ``dispatch.py`` beside it), stop and stage;
  * the gates join, the row marker, and the ``next`` decision over the rows.

Output: one JSON object on standard output. Exit 0 on an answer, 1 on a refusal
``{"refusal": {"code", "detail"}}``, 2 on a usage error.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import unicodedata  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from pathlib import Path  # noqa: E402
from types import ModuleType  # noqa: E402
from typing import Any  # noqa: E402

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_USAGE = 2

GIT_TIMEOUT_S = 60.0
SUPERVISOR_TIMEOUT_S = 300.0
CODE_TIMEOUT = -1
CODE_UNAVAILABLE = -2
MAX_BLOB_BYTES = 1024 * 1024
MAX_STANDING_ORDERS_BYTES = 16384
STANDING_ORDERS_DIR = "docs/product/standing-orders"
CODE_INVALID_STANDING_ORDERS = "invalid-standing-orders"

SKILL_DIR = Path(__file__).resolve().parent.parent
SUPERVISOR = Path(__file__).resolve().parent / "work-supervisor.py"

SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_ORDER_LINE_RE = re.compile(r"(0|[1-9][0-9]*)\. (\S.*)")
_STATUS_RE = re.compile(r"^- \*\*Status:\*\*\s*(.+?)\s*$")
_SPEC_MAP_HEADING_RE = re.compile(r"^ {0,3}##[ \t]+Spec map\b", re.IGNORECASE)
_BOUNDING_HEADING_RE = re.compile(r"^ {0,3}##(?:[ \t]|$)")
_BRANCH_PREFIX = "refs/heads/brief/"

# The variables that would relocate a supervisor call; they are never inherited.
_RELOCATION_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE")
# The only variables a Git child inherits, as in the supervisor's Git launcher;
# every other one, ``GIT_*`` included, is dropped.
_GIT_INHERITED_ENV = ("PATH", "HOME", "LANG", "TMPDIR")
_GIT_INHERITED_ENV_WINDOWS = ("SYSTEMROOT", "TEMP", "TMP", "PATHEXT", "COMSPEC")
CODE_INVALID_POLICY = "invalid-policy"
MAX_DETAIL = 80
# Stages the supervisor never names; the runner derives them itself (AC-0032).
STAGE_DRAFTING = "drafting"
STAGE_SUPERVISOR_CHANGED = "supervisor-changed"
STAGE_REFUSED = "refused"
STAGE_AWAITING_DECISION = "awaiting-decision"
STAGE_UNREADABLE = "unreadable"

STOP_MERGED = "merged"
STOP_MERGE_READY = "merge-ready"
STOP_NONE = "none"

GATE_PENDING = "pending"
GATE_UNAVAILABLE = "unavailable"
# The stages from which a slice's own controller may carry on without a human.
RESUMABLE_STAGES = ("drafting", "admitted", "implementing", "gating", "reviewing")
STAGE_TERMINAL = "terminal"


class Refusal(Exception):
    """A verb that cannot answer: a stable *code* and a one-line *detail*."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


# ── hardened Git ────────────────────────────────────────────────────────────


def _clean_env() -> dict[str, str]:
    """The process environment without any variable that relocates a supervisor call."""
    return {k: v for k, v in os.environ.items() if k not in _RELOCATION_ENV}


def _git_env() -> dict[str, str]:
    """The environment of a Git call: an allowlist, no user or system config, no lazy fetch."""
    names = _GIT_INHERITED_ENV + (_GIT_INHERITED_ENV_WINDOWS if os.name == "nt" else ())
    env = {name: os.environ[name] for name in names if name in os.environ}
    env.update(
        GIT_NO_LAZY_FETCH="1",
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL="",
        GIT_TERMINAL_PROMPT="0",
    )
    return env


def _fixed_flags() -> list[str]:
    """The supervisor's ``-c`` overrides: no hooks, monitor, external diff or attributes file."""
    settings = {
        "core.hooksPath": os.devnull,
        "core.fsmonitor": "false",
        "diff.external": "",
        "core.attributesFile": os.devnull,
    }
    flags = ["--no-pager", "--no-replace-objects", "--no-optional-locks"]
    for key, value in settings.items():
        flags += ["-c", f"{key}={value}"]
    return flags


_LOADED: dict[str, ModuleType] = {}


def _load(filename: str, name: str) -> ModuleType:
    """The one by-path loader: a script beside this file, executed once per process.

    A load that fails leaves no half-loaded entry in ``sys.modules`` or the cache.
    """
    if name not in _LOADED:
        path = Path(__file__).resolve().parent / filename
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"{filename} cannot be loaded")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            sys.modules.pop(name, None)
            raise
        _LOADED[name] = module
    return _LOADED[name]


def _admission() -> ModuleType:
    """The supervisor's admission module, which loads the one shared supervisor Git module."""
    return _load("_supervisor_admission.py", "core_work_loop_brief_runner_admission")


def _supervisor_git() -> ModuleType:
    """The supervisor's Git module: the instance the admission module itself uses."""
    return _admission()._git


def _git_version_output() -> tuple[int, bytes]:
    """The exit code and output of ``git version``: the one read the version check makes."""
    done = _launch(["git", *_fixed_flags(), "version"])
    return done.returncode, done.stdout


def require_git_version() -> None:
    """Refuse ``unsupported-git-version`` below the supervisor's minimum Git version.

    Runs before any other Git command, as the supervisor does: an older Git ignores the
    empty ``GIT_CONFIG_GLOBAL`` that keeps user config out of every call here.
    """
    code, out = _git_version_output()
    found = re.match(rb"git version (\d+)\.(\d+)", out)
    minimum = _supervisor_git()._MINIMUM_GIT
    if found is None or code != 0 or (int(found[1]), int(found[2])) < minimum:
        raise Refusal(
            "unsupported-git-version",
            f"Git {minimum[0]}.{minimum[1]} or later is needed",
        )


_FILTER_FLAGS: dict[str, list[str]] = {}


def _filter_names(root: Path) -> set[str]:
    """Every ``filter.<name>`` the repository config defines, each checked by the supervisor.

    Uses the supervisor's own ``HardenedGit.repository_filters``: its ``--get-regexp "."``
    read of the repository config reaches every key Git honours, whatever bytes it holds, and
    its filter-name rule refuses ``denied-git-config`` for a name ``-c`` cannot empty. No
    filter override is on this read, so a bad name cannot break it. Any other supervisor Git
    failure on this read is the runner's ``git-unavailable``, as for every other Git call.
    """
    module = _supervisor_git()
    try:
        return set(module.HardenedGit(root).repository_filters())
    except module.SupervisorGitError as exc:
        if exc.code == "denied-git-config":
            raise Refusal(exc.code, str(exc)) from exc
        raise Refusal("git-unavailable", f"git config could not be read: {exc.code}") from exc


def _filter_flags(root: Path) -> list[str]:
    """``-c`` overrides that empty every ``filter.<name>`` program the repository config defines.

    An attribute file can still map a path to a configured filter, so the program itself is
    emptied; an empty command is not run. Read once per root from the repository's own config,
    with the supervisor's filter settings.
    """
    key = str(root)
    if key not in _FILTER_FLAGS:
        flags: list[str] = []
        for name in sorted(_filter_names(root)):
            for setting in _supervisor_git()._FILTER_SETTINGS:
                flags += ["-c", f"filter.{name}.{setting}="]
            flags += ["-c", f"filter.{name}.required=false"]
        _FILTER_FLAGS[key] = flags
    return _FILTER_FLAGS[key]


def _launch(argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    """Start one Git process with the allowlisted environment."""
    try:
        return subprocess.run(
            argv,
            env=_git_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Refusal("git-unavailable", f"git could not run: {type(exc).__name__}") from exc


def git(
    root: Path, *args: str, check: bool = True, filters: bool = True
) -> subprocess.CompletedProcess[bytes]:
    """Run one read-only Git command in *root*, hardened as the supervisor's launcher is.

    A caller passes only read commands; nothing here fetches, adds or commits. *filters* is
    False only for a command that runs no filter and that must precede the filter-name check.
    """
    extra = _filter_flags(root) if filters else []
    done = _launch(["git", *_fixed_flags(), *extra, "-C", str(root), *args])
    if check and done.returncode != 0:
        raise Refusal("git-unavailable", f"git {args[0]} exited {done.returncode}")
    return done


def _text(data: bytes) -> str:
    return data.decode("utf-8", "replace").strip()


# ── worktrees ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WorktreeRecord:
    """One ``git worktree list --porcelain -z`` record."""

    path: str
    branch: str
    prunable: bool


def parse_worktrees(raw: bytes) -> list[WorktreeRecord]:
    """The records of ``git worktree list --porcelain -z``, main worktree first.

    Fields end at NUL and a record ends at an empty field.
    """
    records: list[WorktreeRecord] = []
    fields: list[str] = []

    def close() -> None:
        if not fields:
            return
        values = {}
        for item in fields:
            key, _, value = item.partition(" ")
            values.setdefault(key, value)
        records.append(
            WorktreeRecord(
                values.get("worktree", ""), values.get("branch", ""), "prunable" in values
            )
        )
        fields.clear()

    for item in raw.split(b"\0"):
        if item:
            fields.append(item.decode("utf-8", "replace"))
        else:
            close()
    close()
    return records


def list_worktrees(root: Path, *, filters: bool = True) -> list[WorktreeRecord]:
    """Every worktree of the repository at *root*, the main one first."""
    done = git(root, "worktree", "list", "--porcelain", "-z", filters=filters)
    return parse_worktrees(done.stdout)


# ── base checks ─────────────────────────────────────────────────────────────


def _skill_pathspec(top: Path) -> str | None:
    """The skill directory relative to the main worktree, or None when it lies outside it."""
    try:
        return SKILL_DIR.relative_to(top).as_posix()
    except ValueError:
        return None


def base_checks(root: Path) -> str:
    """Run the base checks in order and return the base commit id.

    Refuses ``unsupported-git-version``, ``not-main-worktree``, ``default-branch-unknown``,
    ``base-not-default``, ``denied-git-config`` and ``base-not-committed``, in that order,
    before any supervisor call. The commands before ``denied-git-config`` carry no filter
    override, so a filter name Git cannot take as one cannot break them.
    """
    require_git_version()
    resolved = root.resolve()
    main: Path | None
    try:
        main = Path(list_worktrees(resolved, filters=False)[0].path).resolve()
    except (Refusal, IndexError, OSError):
        main = None
    if main is None or main != resolved:
        raise Refusal("not-main-worktree", "--root is not the repository's main worktree")
    symbolic = git(
        main, "symbolic-ref", "-q", "refs/remotes/origin/HEAD", check=False, filters=False
    )
    target = _text(symbolic.stdout)
    prefix = "refs/remotes/origin/"
    tip = (
        git(
            main, "rev-parse", "--verify", "-q", f"{target}^{{commit}}", check=False, filters=False
        )
        if symbolic.returncode == 0 and target.startswith(prefix) and len(target) > len(prefix)
        else None
    )
    if tip is None or tip.returncode != 0:
        raise Refusal("default-branch-unknown", "refs/remotes/origin/HEAD names no branch")
    head = _text(git(main, "rev-parse", "--verify", "HEAD^{commit}", filters=False).stdout)
    if head != _text(tip.stdout):
        raise Refusal("base-not-default", "HEAD is not the default branch's commit")
    _filter_flags(main)  # refuses denied-git-config before any filter-capable command
    # workspace.toml is read from the working tree by dispatch.py, so it must match the base too.
    pathspecs = ["docs", "workspace.toml"]
    skill = _skill_pathspec(main)
    if skill is not None:
        pathspecs.append(skill)
    status = git(main, "status", "--porcelain=v1", "-z", "--untracked-files=all", "--", *pathspecs)
    if status.stdout:
        raise Refusal(
            "base-not-committed",
            "a file under docs/, workspace.toml or this skill's directory is modified, "
            "staged or untracked",
        )
    return head


# ── committed reads ─────────────────────────────────────────────────────────


def read_blob(root: Path, rev: str, path: str) -> bytes | None:
    """The bytes of regular file *path* at commit *rev*; None when absent or not a small file."""
    listing = git(root, "ls-tree", "-z", "--long", rev, "--", path, check=False)
    if listing.returncode != 0 or not listing.stdout:
        return None
    meta, _, name = listing.stdout.rstrip(b"\0").partition(b"\t")
    parts = meta.split()
    if name.decode("utf-8", "replace") != path or len(parts) != 4:
        return None
    mode, kind, oid, size = (p.decode("ascii", "replace") for p in parts)
    if kind != "blob" or mode not in ("100644", "100755") or not size.isdigit():
        return None
    if int(size) > MAX_BLOB_BYTES:
        return None
    blob = git(root, "cat-file", "blob", oid, check=False)
    return blob.stdout if blob.returncode == 0 else None


# ── standing orders ─────────────────────────────────────────────────────────


def _lint_knowledge() -> ModuleType:
    """Sibling ``lint-knowledge.py``: one definition of the field rules."""
    return _load("lint-knowledge.py", "core_work_loop_brief_runner_lint_knowledge")


def _hidden_text_problem(text: str) -> str | None:
    """The first thing the knowledge lint's multi-line field rules refuse in *text*, or None.

    Its length ceiling is left to this file's own size limit.
    """
    lint = _lint_knowledge()
    problems = [p for p in lint.field_problems(text, "body") if "the gate's ceiling" not in p]
    return problems[0] if problems else None


def standing_orders_problem(data: bytes) -> str | None:
    """Why *data* is not a valid standing-orders file, or None when it is valid.

    Every non-empty line must be ``<N>. <text>`` with N counting 1, 2, 3 without a gap; empty
    lines may sit between. A line without that prefix is refused, never read as a wrapped
    continuation of the line before it.
    """
    if len(data) > MAX_STANDING_ORDERS_BYTES:
        return f"larger than {MAX_STANDING_ORDERS_BYTES} bytes"
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return "not UTF-8"
    refused = _hidden_text_problem(text)
    if refused is not None:
        return refused
    expected = 1
    for number, line in enumerate(text.split("\n"), start=1):
        if not line:
            continue
        match = _ORDER_LINE_RE.fullmatch(line)
        if match is None:
            return f"line {number} is not '<N>. <text>'"
        if int(match.group(1)) != expected:
            return f"line {number} is numbered {match.group(1)}, expected {expected}"
        expected += 1
    return None


def read_standing_orders(root: Path, base: str, brief_slug: str) -> dict[str, str] | None:
    """The base commit's standing orders for *brief_slug*, None when it has no such file.

    Read from the base commit's tree through the hardened launcher, never from the working
    tree. An entry that is not a regular file blob (a symlink, gitlink or tree) is refused.
    """
    path = f"{STANDING_ORDERS_DIR}/{brief_slug}.md"
    listing = git(root, "ls-tree", "-z", "--long", base, "--", path, check=False)
    if listing.returncode != 0 or not listing.stdout:
        return None
    meta, _, name = listing.stdout.rstrip(b"\0").partition(b"\t")
    parts = meta.split()
    if name.decode("utf-8", "replace") != path or len(parts) != 4:
        raise Refusal(CODE_INVALID_STANDING_ORDERS, f"{path} has an unreadable tree entry")
    mode, kind, oid, _size = (p.decode("ascii", "replace") for p in parts)
    if kind != "blob" or mode != "100644":
        raise Refusal(CODE_INVALID_STANDING_ORDERS, f"{path} is not a regular file blob")
    blob = git(root, "cat-file", "blob", oid, check=False)
    if blob.returncode != 0:
        raise Refusal(CODE_INVALID_STANDING_ORDERS, f"{path} cannot be read")
    problem = standing_orders_problem(blob.stdout)
    if problem is not None:
        raise Refusal(CODE_INVALID_STANDING_ORDERS, f"{path}: {problem}")
    text = blob.stdout.decode("utf-8")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return {
        "path": path,
        "sha256": hashlib.sha256(blob.stdout).hexdigest(),
        "fence": "`" * max(3, longest + 1),
        "text": text,
    }


def _live(line: str, in_comment: bool) -> tuple[str, bool]:
    """The text of *line* outside HTML comments, and the comment state after it."""
    parts: list[str] = []
    pos = 0
    while pos < len(line):
        if in_comment:
            close = line.find("-->", pos)
            if close == -1:
                break
            in_comment = False
            pos = close + 3
        else:
            opened = line.find("<!--", pos)
            if opened == -1:
                parts.append(line[pos:])
                break
            parts.append(line[pos:opened])
            in_comment = True
            pos = opened + 4
    return "".join(parts), in_comment


def _token(raw: str) -> str:
    """The leading word of a header value, cut at ``(``, an arrow or a comment."""
    for delim in (" (", " →", "<!--"):
        raw = raw.split(delim, 1)[0]
    words = raw.split()
    return words[0].strip("`") if words else ""


def parse_status(text: str) -> str | None:
    """The ``Status:`` token of a spec or plan header, or None when it has none."""
    in_comment = False
    for line in text.splitlines():
        before = in_comment
        live, in_comment = _live(line, in_comment)
        if not before and _BOUNDING_HEADING_RE.match(line):
            return None
        match = _STATUS_RE.match(live.strip() if live.strip() else "")
        if match:
            return _token(match.group(1)) or None
    return None


def _is_separator(cells: list[str]) -> bool:
    """True for a table's ``| --- | :-: |`` row."""
    return all(re.fullmatch(r":?-+:?", c) for c in cells)


def parse_spec_map(text: str) -> list[str]:
    """The spec slugs of the ``## Spec map`` table, in table order.

    The table row just before the separator row is the header; every other row is a slice.
    Refuses ``invalid-spec-map`` when the brief has no Spec map rows, a first cell is empty, a
    slug repeats, or a slug is not lowercase ASCII letters, digits and single hyphens.
    """
    table: list[list[str]] = []
    in_section = False
    in_comment = False
    for line in text.splitlines():
        before = in_comment
        _, in_comment = _live(line, in_comment)
        if not in_section:
            if not before and _SPEC_MAP_HEADING_RE.match(line):
                in_section = True
            continue
        if not before and _SPEC_MAP_HEADING_RE.match(line):
            continue
        if not before and _BOUNDING_HEADING_RE.match(line):
            break
        if before or in_comment or not line.lstrip().startswith("|"):
            continue
        table.append([c.strip() for c in line.strip().strip("|").split("|")])
    slugs: list[str] = []
    for index, cells in enumerate(table):
        if _is_separator(cells):
            continue
        if index + 1 < len(table) and _is_separator(table[index + 1]):
            continue  # the header
        first = cells[0].strip("` ")
        if not first:
            raise Refusal("invalid-spec-map", "a Spec map row has an empty first cell")
        if SLUG_RE.fullmatch(first) is None:
            raise Refusal("invalid-spec-map", f"Spec map slug {first!r} is not a valid slug")
        if first in slugs:
            raise Refusal("invalid-spec-map", f"Spec map slug {first!r} is repeated")
        slugs.append(first)
    if not slugs:
        raise Refusal("invalid-spec-map", "the brief has no Spec map rows")
    return slugs


def read_spec_map(root: Path, base: str, brief_slug: str) -> list[str]:
    """The brief's Spec map slugs, read from the base commit's blob."""
    data = read_blob(root, base, f"docs/product/briefs/{brief_slug}.md")
    if data is None:
        raise Refusal(
            "invalid-spec-map", f"docs/product/briefs/{brief_slug}.md is not at the base"
        )
    try:
        return parse_spec_map(data.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise Refusal("invalid-spec-map", "the brief is not UTF-8") from exc


# ── slice worktrees ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Slice:
    """A slice worktree for one Spec map row.

    *readable* is false for a prunable, missing, ambiguous or oddly named one; *detail* then
    names the cause. *worktree* is None when the path holds a character that must not be
    emitted or used as a working directory.
    """

    worktree: str | None
    branch: str
    head: str | None
    readable: bool
    detail: str | None = None


def unsafe_path_char(path: str) -> bool:
    """True when *path* holds a control, hidden or line-separator character."""
    is_hidden = _lint_knowledge().is_hidden_char
    return any(
        unicodedata.category(ch) in ("Cc", "Zl", "Zp") or is_hidden(ch) or ch == "\ufffd"
        for ch in path
    )


def discover_slices(root: Path, brief_slug: str, slugs: list[str]) -> dict[str, Slice]:
    """The slice worktrees by spec slug: linked worktrees on ``brief/<brief>/<spec>`` only.

    A slug with two matching worktrees is unreadable, since no one of them is the slice.
    """
    found: dict[str, Slice] = {}
    ambiguous: set[str] = set()
    for record in list_worktrees(root)[1:]:
        for slug in slugs:
            branch = f"{_BRANCH_PREFIX}{brief_slug}/{slug}"
            if record.branch != branch:
                continue
            head = None
            detail: str | None = None
            path: str | None = record.path
            if unsafe_path_char(record.path):
                path, detail = None, "bad-path-chars"
            elif record.prunable:
                detail = "prunable"
            elif not Path(record.path).is_dir():
                detail = "missing-dir"
            else:
                ref = f"{branch}^{{commit}}"
                done = git(root, "rev-parse", "--verify", "-q", ref, check=False)
                head = _text(done.stdout) if done.returncode == 0 else None
                detail = None if head is not None else "head-unresolved"
            if slug in found:
                ambiguous.add(slug)
            found[slug] = Slice(path, branch, head, detail is None, detail)
    for slug in ambiguous:
        prior = found[slug]
        found[slug] = Slice(prior.worktree, prior.branch, None, False, "ambiguous-worktrees")
    return found


# ── supervisor reads ────────────────────────────────────────────────────────


def run_supervisor(worktree: str, *argv: str) -> tuple[int, Any]:
    """Run the supervisor beside this file in *worktree*; return (exit code, parsed JSON or None).

    A call that timed out answers ``CODE_TIMEOUT``; one that could not start, ``CODE_UNAVAILABLE``.

    Never the slice branch's copy: the path is fixed from this file's own location.
    """
    env = _clean_env()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    try:
        done = subprocess.run(
            [sys.executable, str(SUPERVISOR), *argv],
            cwd=worktree,
            env=env,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=SUPERVISOR_TIMEOUT_S,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return CODE_TIMEOUT, None
    except OSError:
        return CODE_UNAVAILABLE, None
    try:
        return done.returncode, json.loads(done.stdout.decode("utf-8"))
    except ValueError:
        return done.returncode, None


def _is_view(payload: Any) -> bool:
    """True when *payload* has the supervisor ``status`` view's shape."""
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("run"), dict)
        and isinstance(payload.get("terminal"), bool)
    )


def _refusal_of(payload: Any) -> dict[str, Any] | None:
    """The non-empty top-level refusal of a supervisor answer, or None."""
    refusal = payload.get("refusal") if isinstance(payload, dict) else None
    if isinstance(refusal, dict) and isinstance(refusal.get("code"), str):
        return refusal
    return None


@dataclass
class Reading:
    """What the supervisor said about one slice: its stage and whether it is merge-ready."""

    stage: str
    merge_ready: bool = False
    refusal: dict[str, Any] | None = None
    detail: str | None = None


def _bounded(text: str) -> str:
    """*text* cut to ``MAX_DETAIL`` characters."""
    return text[:MAX_DETAIL]


def _refusal_detail(refusal: dict[str, Any] | None) -> str:
    """``supervisor-refusal:<code>`` when the code is a plain slug, else the bare cause."""
    code = refusal["code"] if refusal else ""
    if SLUG_RE.fullmatch(code) is None:
        return "supervisor-refusal"
    return _bounded(f"supervisor-refusal:{code}")


def _exit_detail(code: int, payload: Any) -> str:
    """The cause of an unusable supervisor answer, as a short fixed phrase."""
    if code == CODE_TIMEOUT:
        return "supervisor-timeout"
    if code == CODE_UNAVAILABLE:
        return "supervisor-unavailable"
    if code != 0:
        refusal = _refusal_of(payload)
        return _refusal_detail(refusal) if refusal is not None else f"supervisor-exit-{code}"
    return "supervisor-bad-output"


def derive_stage(code: int, payload: Any) -> Reading:
    """The AC-0032 stage of a slice from a ``status --json`` exit code and parsed output."""
    refusal = _refusal_of(payload)
    if code == 1 and not _is_view(payload):
        if refusal is not None and refusal["code"] == "supervisor-changed":
            return Reading(STAGE_SUPERVISOR_CHANGED, refusal=refusal)
        return Reading(STAGE_UNREADABLE, detail=_exit_detail(code, payload))
    if code != 0 or not _is_view(payload):
        return Reading(STAGE_UNREADABLE, detail=_exit_detail(code, payload))
    if refusal is not None:
        if refusal["code"] == "no-approval":
            return Reading(STAGE_DRAFTING)
        return Reading(STAGE_REFUSED, refusal=refusal)
    run = payload["run"]
    if run.get("gate_pending") is True:
        return Reading(STAGE_AWAITING_DECISION)
    stage = run.get("stage")
    if not isinstance(stage, str) or not stage:
        return Reading(STAGE_UNREADABLE, detail="supervisor-no-stage")
    readiness = payload.get("readiness")
    ready = isinstance(readiness, dict) and readiness.get("ready") is True
    return Reading(stage, merge_ready=payload["terminal"] is True and ready)


def read_slice(root: Path, spec_slug: str, found: Slice) -> Reading:
    """The stage of one slice worktree; no spec on its branch head means ``drafting``."""
    if not found.readable or found.head is None or found.worktree is None:
        return Reading(STAGE_UNREADABLE, detail=found.detail or "unreadable-worktree")
    spec_dir = f"docs/specs/{spec_slug}"
    if read_blob(root, found.head, f"{spec_dir}/spec.md") is None:
        return Reading(STAGE_DRAFTING)
    code, payload = run_supervisor(found.worktree, "status", spec_dir, "--json")
    return derive_stage(code, payload)


# ── rows ────────────────────────────────────────────────────────────────────


@dataclass
class Row:
    """One Spec map row as the runner reads it at the base."""

    slice: str
    spec_status: str | None
    plan_status: str | None
    worktree: str | None
    branch: str
    head: str | None
    stop: str
    stage: str | None
    ready: bool
    mode: str | None
    refusal: dict[str, Any] | None = field(default=None)
    # The supervisor's gate entries as printed; None when they are unavailable.
    gates: list[dict[str, Any]] | None = field(default_factory=list)
    # True when a slice worktree exists for the row, even one whose path is never emitted.
    present: bool = False
    # A bounded cause for ``next``'s blocked rows: why the row is unreadable or not dispatchable.
    detail: str | None = None

    def __post_init__(self) -> None:
        self.present = self.present or self.worktree is not None

    def as_dict(self) -> dict[str, Any]:
        """The row as JSON fields."""
        return {
            "slice": self.slice,
            "spec_status": self.spec_status,
            "plan_status": self.plan_status,
            "worktree": self.worktree,
            "branch": self.branch,
            "head": self.head,
            "stop": self.stop,
            "stage": self.stage,
            "ready": self.ready,
            "mode": self.mode,
        }


def _load_dispatch() -> ModuleType:
    """Sibling ``dispatch.py`` through the one loader."""
    return _load("dispatch.py", "core_work_loop_brief_runner_dispatch")


def dispatch_answer(root: Path) -> set[str] | None:
    """The spec paths ``dispatch.py`` lists as ready; None when it cannot answer."""
    try:
        result = _load_dispatch().dispatch(root)
        return {
            item["path"] for item in result["ready"] if isinstance(item.get("path"), str)
        }
    except Exception:  # noqa: BLE001 - an unreadable answer makes no row ready
        return None


def _status_at(root: Path, base: str, path: str) -> str | None:
    data = read_blob(root, base, path)
    if data is None:
        return None
    return parse_status(data.decode("utf-8", "replace"))


def read_rows(root: Path, base: str, brief_slug: str, slugs: list[str]) -> list[Row]:
    """Every row's spec status, worktree, stop, stage and readiness, in Spec map order."""
    slices = discover_slices(root, brief_slug, slugs)
    answer = dispatch_answer(root)
    approved_ready = answer or set()
    rows: list[Row] = []
    earlier_stopped = True
    for slug in slugs:
        spec_path = f"docs/specs/{slug}/spec.md"
        spec_blob = read_blob(root, base, spec_path)
        spec_status = _status_at(root, base, spec_path)
        plan_status = _status_at(root, base, f"docs/specs/{slug}/plan.md")
        found = slices.get(slug)
        reading = read_slice(root, slug, found) if found is not None else None
        if spec_status == "Shipped":
            stop = STOP_MERGED
        elif reading is not None and reading.merge_ready:
            stop = STOP_MERGE_READY
        else:
            stop = STOP_NONE
        mode: str | None = None
        ready = False
        detail: str | None = None
        if found is None:
            if spec_status == "Approved":
                mode, ready = "run", spec_path in approved_ready
                if answer is None:
                    detail = "dispatch-unavailable"
            elif spec_blob is None:
                mode, ready = "author-spec", earlier_stopped
            elif spec_status == "Draft":
                mode, ready = "shape", earlier_stopped
        rows.append(
            Row(
                slice=slug,
                spec_status=spec_status,
                plan_status=plan_status,
                worktree=found.worktree if found is not None else None,
                branch=f"brief/{brief_slug}/{slug}",
                head=found.head if found is not None else None,
                stop=stop,
                stage=reading.stage if reading is not None else None,
                ready=ready,
                mode=mode if ready else None,
                refusal=reading.refusal if reading is not None else None,
                present=found is not None,
                detail=reading.detail if reading is not None else detail,
            )
        )
        earlier_stopped = earlier_stopped and stop != STOP_NONE
    return rows


def read_brief(
    root: Path, brief_slug: str, *, lease: bool = False
) -> tuple[str, list[Row]]:
    """Run the base checks, then read the brief: the base commit id and every row.

    With *lease*, the base policy's lease table is judged right after the base checks and
    before the Spec map: ``invalid-policy`` follows every base refusal and precedes the rest.
    """
    base = base_checks(root)
    if lease:
        read_lease(root, base)
    resolved = root.resolve()
    slugs = read_spec_map(resolved, base, brief_slug)
    return base, read_rows(resolved, base, brief_slug, slugs)


# ── gates, marker, status ───────────────────────────────────────────────────


def read_gates(worktree: str) -> list[dict[str, Any]] | None:
    """The entries the supervisor's ``gates`` verb prints in *worktree*; None when unavailable.

    A non-zero exit or any output that is not ``{"gates": [<object with a state>, ...]}``
    is unavailable, never an empty or a pending listing.
    """
    code, payload = run_supervisor(worktree, "gates")
    entries = payload.get("gates") if isinstance(payload, dict) else None
    if (
        code != 0
        or not isinstance(entries, list)
        or not all(isinstance(e, dict) and isinstance(e.get("state"), str) for e in entries)
    ):
        return None
    return entries


def attach_gates(rows: list[Row]) -> None:
    """Fill each slice row's gate entries; a row with no worktree has none."""
    for row in rows:
        if not row.present:
            row.gates = []
        elif row.worktree is None or row.head is None:
            row.gates = None
        else:
            row.gates = read_gates(row.worktree)


def joined_gates(row: Row) -> list[dict[str, Any]]:
    """The row's entries each plus ``slice`` and ``worktree``, or one ``unavailable`` entry.

    Entries with a ``spec_dir`` come first, by spec directory; entries without one come last
    in the order the supervisor printed them.
    """
    base = {"slice": row.slice, "worktree": row.worktree}
    if row.gates is None:
        return [{**base, "state": GATE_UNAVAILABLE}]
    entries = [{**entry, **base} for entry in row.gates]
    dated = sorted(
        (e for e in entries if isinstance(e.get("spec_dir"), str)), key=lambda e: e["spec_dir"]
    )
    return dated + [e for e in entries if not isinstance(e.get("spec_dir"), str)]


def row_marker(head: str, delivery_tree: str, gates: list[dict[str, Any]] | None) -> str:
    """SHA-256 over the branch head, the delivery tree id and the gate entries as printed.

    *gates* None (unavailable) folds in the literal ``unavailable``.
    """
    listing = (
        GATE_UNAVAILABLE
        if gates is None
        else json.dumps(gates, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    )
    return hashlib.sha256("\0".join((head, delivery_tree, listing)).encode("utf-8")).hexdigest()


def delivery_tree(root: Path, head: str, slug: str) -> str:
    """The tree id of the slice's committed ``delivery/`` records at *head*, or empty."""
    path = f"docs/specs/{slug}/delivery"
    done = git(root, "ls-tree", "-z", head, "--", path, check=False)
    meta, _, name = done.stdout.rstrip(b"\0").partition(b"\t")
    parts = meta.split()
    if done.returncode != 0 or name.decode("utf-8", "replace") != path or len(parts) != 3:
        return ""
    return parts[2].decode("ascii", "replace") if parts[1] == b"tree" else ""


def status_entries(root: Path, rows: list[Row]) -> list[dict[str, Any]]:
    """One entry per row: the AC-0013 fields, with the marker only for a row with a worktree."""
    entries: list[dict[str, Any]] = []
    for row in rows:
        marker = None
        if row.present:
            tree = delivery_tree(root, row.head, row.slice) if row.head else ""
            marker = row_marker(row.head or "", tree, row.gates)
        entries.append(
            {
                "slice": row.slice,
                "spec_status": row.spec_status,
                "worktree": row.worktree,
                "branch": row.branch,
                "head": row.head,
                "stop": row.stop,
                "stage": row.stage,
                "gates": joined_gates(row) if row.present else [],
                "marker": marker,
            }
        )
    return entries


def all_gates(rows: list[Row]) -> list[dict[str, Any]]:
    """Every slice's joined gate entries, in Spec map order."""
    return [entry for row in rows if row.present for entry in joined_gates(row)]


# ── next ────────────────────────────────────────────────────────────────────


def read_lease(root: Path, base: str) -> dict[str, Any]:
    """The ``lease`` table of the policy beside the runner, at the base, judged by the supervisor.

    Refuses ``invalid-policy`` when the policy is missing, unreadable or not JSON, or when its
    ``lease`` table fails the supervisor's ``_check_lease``: a guess would misreport the cap or
    abandon a task early.
    """
    skill = _skill_pathspec(root.resolve())
    data = read_blob(root, base, f"{skill}/supervisor-policy.json") if skill else None
    admission = _admission()
    try:
        if data is None:
            raise ValueError("missing")
        lease = json.loads(data.decode("utf-8"))["lease"]
        admission._check_lease(lease)
    except (ValueError, KeyError, TypeError, admission.Refusal) as exc:
        detail = "the base lease policy is unreadable or invalid"
        raise Refusal(CODE_INVALID_POLICY, detail) from exc
    assert isinstance(lease, dict)
    return lease


def read_lease_cap(root: Path, base: str) -> int:
    """``lease.max_slices_in_flight`` from the policy beside the runner, at the base."""
    return int(read_lease(root, base)["max_slices_in_flight"])


def _has_pending(row: Row) -> bool:
    return any(g.get("state") == GATE_PENDING for g in row.gates or [])


def _gate_clean(row: Row) -> bool:
    """True when every gate entry is pending (or there is none); unavailable is not clean."""
    return row.gates is not None and all(g.get("state") == GATE_PENDING for g in row.gates)


def _pilot(rows: list[Row]) -> str | None:
    """The pilot's slug while no row has reached its stop, else None (no hold)."""
    if any(row.stop != STOP_NONE for row in rows):
        return None
    for row in rows:
        if row.present:
            return row.slice
    return next((row.slice for row in rows if row.ready), None)


def _reason(row: Row, rows: list[Row], cap_reached: bool) -> dict[str, Any]:
    """The first reason, in the stated order, that *row* is not named by an action."""
    out: dict[str, Any] = {"slice": row.slice}
    refusal = row.refusal or {}
    if row.stage == STAGE_UNREADABLE:
        out.update(reason="unreadable", detail=row.detail)
    elif row.stage == STAGE_SUPERVISOR_CHANGED:
        out["reason"] = "supervisor-changed"
    elif row.stage == STAGE_REFUSED:
        out.update(
            reason="refused",
            code=refusal.get("code"),
            owner=refusal.get("owner"),
            detail=refusal.get("detail"),
        )
    elif row.stage == STAGE_AWAITING_DECISION:
        out["reason"] = "awaiting-decision"
    elif row.present and not _gate_clean(row):
        out["reason"] = "gate-not-clean"
    elif row.present and row.stage == STAGE_TERMINAL:
        out["reason"] = "terminal-not-ready"
    elif row.ready and cap_reached:
        out["reason"] = "in-flight-cap"
    elif row.ready:
        out["reason"] = "pilot-in-flight"
    elif (
        not row.present
        and row.spec_status in (None, "Draft")
        and any(earlier.stop == STOP_NONE for earlier in rows[: rows.index(row)])
    ):
        out["reason"] = "earlier-row-not-stopped"
    else:
        out["reason"] = "not-dispatchable"
        if row.detail is not None:
            out["detail"] = row.detail
    return out


def decide_next(rows: list[Row], max_in_flight: int) -> dict[str, Any]:
    """The one action ``next`` answers, the first that applies in the stated order."""
    for row in rows:
        if (
            row.worktree is not None
            and row.stop == STOP_NONE
            and row.stage in RESUMABLE_STAGES
            and row.gates == []
        ):
            return {
                "kind": "resume-slice",
                "slice": row.slice,
                "worktree": row.worktree,
                "stage": row.stage,
            }
    in_flight = sum(1 for r in rows if r.present and r.stop == STOP_NONE)
    cap_reached = in_flight >= max_in_flight
    pilot = _pilot(rows)
    if not cap_reached:
        for row in rows:
            if row.ready and (pilot is None or row.slice == pilot):
                return {
                    "kind": "start-slice",
                    "slice": row.slice,
                    "branch": row.branch,
                    "mode": row.mode,
                    "spec_status": row.spec_status,
                    "plan_status": row.plan_status,
                }
    pending = [g for row in rows if _has_pending(row) for g in joined_gates(row)
               if g.get("state") == GATE_PENDING]
    if pending:
        return {"kind": "await-gates", "gates": pending}
    merge_ready = [row.slice for row in rows if row.stop == STOP_MERGE_READY]
    if merge_ready:
        return {"kind": "await-merge", "slices": merge_ready}
    if all(row.stop == STOP_MERGED for row in rows):
        return {"kind": "complete"}
    return {
        "kind": "blocked",
        "rows": [
            _reason(row, rows, cap_reached) for row in rows if row.stop != STOP_MERGED
        ],
    }


# ── classify ────────────────────────────────────────────────────────────────

ACTION_SURFACE = "surface-to-human"
ACTION_ABANDON = "abandon-and-replan"
CLASS_ACTIONS = {
    "cap-hit": "split-task",
    "network": "retry",
    "tool-error": "retry-other-model",
    "stuck": "replace-worker",
}


def read_retry_budget(root: Path, base: str) -> int:
    """``lease.retry_budget`` from the policy beside the runner, at the base."""
    return int(read_lease(root, base)["retry_budget"])


def classify_action(failure_class: str, failed_attempts: int, retry_budget: int) -> str:
    """The AC-0020 action: an unknown class first, then the budget, then the class table."""
    if failure_class not in CLASS_ACTIONS:
        return ACTION_SURFACE
    if failed_attempts > retry_budget:
        return ACTION_ABANDON
    return CLASS_ACTIONS[failure_class]


def read_failed_attempts(row: Row, task_id: str) -> int:
    """The task's ``failed_attempts`` from the slice worktree's supervisor ``status --json``."""
    if row.worktree is None:
        raise Refusal("status-unavailable", "the slice worktree path cannot be used")
    code, payload = run_supervisor(row.worktree, "status", f"docs/specs/{row.slice}", "--json")
    if code != 0 or not _is_view(payload) or _refusal_of(payload) is not None:
        raise Refusal("status-unavailable", "the supervisor status of the slice is unusable")
    tasks = payload.get("tasks")
    for task in tasks if isinstance(tasks, list) else []:
        if isinstance(task, dict) and task.get("task_id") == task_id:
            n = task.get("failed_attempts")
            if isinstance(n, int) and not isinstance(n, bool) and n >= 0:
                return n
            raise Refusal("status-unavailable", "the task carries no failed-attempt count")
    raise Refusal("unknown-task", f"the slice has no task {task_id}")


def classify(
    root: Path, base: str, rows: list[Row], slice_slug: str, task_id: str, failure_class: str
) -> dict[str, Any]:
    """Classify one failed ``implement-task`` dispatch of a slice."""
    row = next((r for r in rows if r.slice == slice_slug), None)
    if row is None:
        raise Refusal("unknown-slice", f"{slice_slug} is not a Spec map row")
    if not row.present:
        raise Refusal("no-slice-worktree", f"{slice_slug} has no slice worktree")
    budget = read_retry_budget(root, base)
    n = read_failed_attempts(row, task_id)
    action = classify_action(failure_class, n, budget)
    return {"base": base, "action": action, "failed_attempts": n}


# ── command line ────────────────────────────────────────────────────────────


def _slug(value: str) -> str:
    if SLUG_RE.fullmatch(value) is None:
        raise argparse.ArgumentTypeError("must be lowercase letters, digits and single hyphens")
    return value


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise SystemExit(EXIT_USAGE)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="brief-runner.py")
    verbs = parser.add_subparsers(dest="verb", required=True, parser_class=_Parser)
    for name in ("status", "next", "gates", "classify"):
        verb = verbs.add_parser(name)
        verb.add_argument("brief_slug", type=_slug)
        verb.add_argument("--root", default=".")
        if name == "classify":
            verb.add_argument("--slice", dest="slice_slug", required=True, type=_slug)
            verb.add_argument("--task", required=True)
            verb.add_argument("--class", dest="failure_class", required=True)
    return parser


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    """Run one verb and print its one JSON answer."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")
    try:
        args = _parser().parse_args(argv)
    except SystemExit as exc:
        return EXIT_USAGE if exc.code not in (0, None) else EXIT_OK
    try:
        root = Path(args.root)
        base, rows = read_brief(root, args.brief_slug, lease=args.verb != "gates")
        if args.verb in ("status", "next"):
            cap = read_lease_cap(root, base)
        if args.verb == "classify":
            _emit(
                classify(root, base, rows, args.slice_slug, args.task, args.failure_class)
            )
            return EXIT_OK
        orders = (
            read_standing_orders(root.resolve(), base, args.brief_slug)
            if args.verb in ("status", "next")
            else None
        )
        attach_gates(rows)
        if args.verb == "gates":
            _emit({"base": base, "gates": all_gates(rows)})
        elif args.verb == "status":
            _emit(
                {
                    "base": base,
                    "rows": status_entries(root.resolve(), rows),
                    "standing_orders": orders,
                }
            )
        else:
            action = decide_next(rows, cap)
            _emit({"base": base, "action": action, "standing_orders": orders})
    except Refusal as exc:
        _emit({"refusal": {"code": exc.code, "detail": exc.detail}})
        return EXIT_REFUSED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
