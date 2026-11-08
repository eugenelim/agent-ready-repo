#!/usr/bin/env python3
"""Brief-level runner: a read-only view of a delivery brief's slices.

Usage: brief-runner.py <status|next|gates|classify> <brief-slug> [--root <dir>]
       brief-runner.py guard --from <rev> --to <rev> [--root <dir>]

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

Output: an answer is one JSON object on standard output with exit 0, a refusal is
``{"refusal": {"code", "detail"}}`` with exit 1, and a ``next`` answer or refusal also
carries ``schema_version``. A usage error exits 2 and ``--help`` exits 0; neither prints
JSON.

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
import stat  # noqa: E402
import subprocess  # noqa: E402
import tomllib  # noqa: E402
import traceback  # noqa: E402
import unicodedata  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from datetime import UTC, datetime, timedelta  # noqa: E402
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

RUN_GRANTS_DIR = "docs/product/run-grants"
MAX_GRANT_BYTES = 4096
GRANT_MAX_LIFETIME = timedelta(days=14)
# The pre-Ready exemption (AC-0002) ends at this fixed UTC time, whatever the host clock says.
PRE_READY_EXEMPTION_ENDS = datetime(2026, 11, 30, tzinfo=UTC)
BRIEF_STATUSES = ("Draft", "Ready", "Executing", "Shipped", "Withdrawn", "Cancelled")
RUNNABLE_STATUSES = ("Ready", "Executing")
CLOSED_STATUSES = ("Shipped", "Withdrawn", "Cancelled")
EXEMPTION = "pre-ready-in-flight"
STATUS_PLACEHOLDER = "<status>"
# The marker line the build-check step greps for in a base tree's runner: keep it verbatim.
GUARD_VERB = "guard"
CODE_GRANT_CHANGE_MIXED = "grant-change-mixed"
CODE_UNKNOWN_REVISION = "unknown-revision"
BRIEFS_DIR = "docs/product/briefs"
GUARD_SURFACE_PREFIXES = (
    "packs/core/.apm/skills/work-loop/scripts/",
    ".github/workflows/",
)
GUARD_SURFACE_FILES = (
    "packs/core/.apm/skills/work-loop/references/brief-runner.md",
    "packs/core/.apm/skills/author-delivery-brief/SKILL.md",
)
CONFIRM_SKEW = timedelta(minutes=5)
# Actions only a human takes; a fixed tuple in code, never read from a grant.
HUMAN_ONLY = (
    "accept-protected-class-risk",
    "approve-plan",
    "approve-spec",
    "irreversible-operation",
    "merge",
    "reapprove-after-material-change",
)
HELD_ACTIONS = ("open-pull-request", "push")
DONE_WHEN = ("all-granted-merged", "all-granted-stopped")
GRANT_KEYS = (
    "schema_version",
    "brief",
    "confirmed_by",
    "confirmed_at",
    "expires_at",
    "done_when",
    "slices",
    "retry_budget",
    "max_slices_in_flight",
    "held_actions",
)

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
# The longest supervisor refusal detail the runner relays; longer text is cut.
MAX_RELAYED_DETAIL = 400
# Stands in for relayed supervisor text that is not a plain slug or holds an unsafe character.
WITHHELD = "withheld"
CODE_INTERNAL_ERROR = "internal-error"
# The version of the `next` answer's shape; it changes only when that shape does.
NEXT_SCHEMA_VERSION = 2
# The most traceback characters an internal error writes to stderr.
MAX_TRACEBACK = 4000
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
        "core.excludesFile": os.devnull,
        # As the supervisor's launcher: repository config must not weaken the stat check.
        "core.checkStat": "default",
        "core.trustctime": "true",
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
    # The ignore files above those paths decide what counts as untracked under them.
    parents = parent_ignore_files(pathspecs)
    # A submodule's files are not in the base commit, yet dispatch.py would read them from the
    # working tree, so a base that holds one under these paths is refused.
    listing = git(main, "ls-tree", "-r", "-z", head, "--", *pathspecs)
    if any(
        entry.split(b" ", 2)[1:2] == [b"commit"] for entry in listing.stdout.split(b"\0") if entry
    ):
        raise Refusal(
            "base-not-committed",
            "a submodule sits under docs/, workspace.toml or this skill's directory",
        )
    # Ignoring submodule dirtiness keeps status from running inside a submodule, whose own
    # config and attributes this call cannot neutralize; a submodule at another commit shows.
    status = git(
        main,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=dirty",
        "--",
        *pathspecs,
        *(f":(icase){p}" for p in parents),
    )
    if status.stdout or hidden_change(main, head, pathspecs, parents):
        raise Refusal(
            "base-not-committed",
            "a file under docs/, workspace.toml or this skill's directory is modified, "
            "staged or untracked, or hidden from git status by an untracked .gitignore, "
            "a changed .gitignore in a folder above those paths, "
            "info/exclude, a sparse checkout or an index flag",
        )
    return head


_SUPERVISOR_IGNORE_RE = re.compile(r"docs/specs/[^/]+/\.supervisor/\.gitignore")


def _is_run_store_ignore_file(main: Path, path: str) -> bool:
    """True for the supervisor's own ``.supervisor/.gitignore`` holding exactly ``*``.

    That folder holds only the supervisor's local records, which no readiness read opens.
    """
    if _SUPERVISOR_IGNORE_RE.fullmatch(path) is None:
        return False
    try:
        if not stat.S_ISREG(os.lstat(main / path).st_mode):
            return False
    except OSError:
        return False
    hashed = git(main, "hash-object", "--no-filters", "--", path, check=False)
    found = _text(hashed.stdout)
    return hashed.returncode == 0 and found == _blob_id(b"*\n", found)


def _blob_id(data: bytes, like: str) -> str:
    """The Git blob id of *data* in the object format of the id *like*."""
    # Git's object id, not a security hash.
    digest = hashlib.sha256() if len(like) == 64 else hashlib.sha1(usedforsecurity=False)
    digest.update(b"blob %d\0" % len(data) + data)
    return digest.hexdigest()


def _glob_literal(path: str) -> str:
    """*path* with every glob metacharacter escaped, for use under ``:(glob)`` magic."""
    return re.sub(r"([*?\[\\])", r"\\\1", path)


def parent_ignore_files(pathspecs: list[str]) -> list[str]:
    """The ``.gitignore`` path of every folder above *pathspecs*, up to the repository root."""
    found: set[str] = set()
    for spec in pathspecs:
        parts = spec.split("/")[:-1]
        for depth in range(len(parts) + 1):
            found.add("/".join([*parts[:depth], ".gitignore"]))
    return sorted(found)


def hidden_change(
    main: Path, head: str, pathspecs: list[str], parents: list[str] | None = None
) -> bool:
    """True when Git state outside the base hides a change that ``git status`` leaves out.

    Three reads, none of which runs a filter or writes an object. Untracked files are listed
    against the in-tree ``.gitignore`` files only, never ``info/exclude`` or an excludes file.
    Untracked ``.gitignore`` files, in any letter case, are listed with no ignore rule applied;
    any but the supervisor's own counts, and so does one at a *parents* path. An index entry
    marked assume-unchanged or skip-worktree, a *parents* one included, is judged by its
    working-tree bytes, hashed with no filter, against the base blob.
    """
    others = git(
        main, "ls-files", "--others", "-z", "--exclude-per-directory=.gitignore", "--", *pathspecs
    )
    if others.stdout:
        return True
    # An untracked .gitignore can ignore itself and the files beside it, which dispatch.py
    # would still read, so one is a change whatever the ignore rules say.
    # icase: a case-insensitive filesystem reads `.GITIGNORE` as an ignore file too.
    folders = [p for p in pathspecs if p != "workspace.toml"]
    ignore_files = [f":(glob,icase){_glob_literal(p)}/**/.gitignore" for p in folders]
    ignore_files += [f":(icase){p}" for p in parents or []]
    found = git(main, "ls-files", "--others", "-z", "--", *ignore_files).stdout
    for raw in (item for item in found.split(b"\0") if item):
        if not _is_run_store_ignore_file(main, raw.decode("utf-8", "surrogateescape")):
            return True
    listing = git(
        main, "ls-files", "-v", "-z", "--", *pathspecs, *(f":(icase){p}" for p in parents or [])
    )
    for item in listing.stdout.split(b"\0"):
        tag, _, raw = item.partition(b" ")
        if not item or tag == b"H":
            continue  # an ordinary entry: git status has judged it
        path = raw.decode("utf-8", "surrogateescape")
        entry = tree_entry(main, head, path)
        if entry is None or not entry.regular:
            return True
        try:  # hash-object would follow a link, or block on a FIFO
            if not stat.S_ISREG(os.lstat(main / path).st_mode):
                return True
        except OSError:
            return True  # missing from disk, as a sparse checkout leaves it
        hashed = git(main, "hash-object", "--no-filters", "--", path, check=False)
        if hashed.returncode != 0 or _text(hashed.stdout) != entry.oid:
            return True
    return False


# ── committed reads ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TreeEntry:
    """One ``ls-tree --long`` entry; *size* is None for anything but a blob."""

    mode: str
    kind: str
    oid: str
    size: int | None

    @property
    def regular(self) -> bool:
        """True for a regular file blob, executable or not."""
        return self.kind == "blob" and self.mode in ("100644", "100755") and self.size is not None


# An entry that exists but whose listing cannot be parsed.
UNPARSED_ENTRY = TreeEntry("", "", "", None)


def tree_entry(root: Path, rev: str, path: str) -> TreeEntry | None:
    """The tree entry of *path* at commit *rev*: None when absent, ``UNPARSED_ENTRY`` when odd."""
    listing = git(root, "ls-tree", "-z", "--long", rev, "--", path, check=False)
    if listing.returncode != 0 or not listing.stdout:
        return None
    meta, _, name = listing.stdout.rstrip(b"\0").partition(b"\t")
    parts = meta.split()
    if name.decode("utf-8", "replace") != path or len(parts) != 4:
        return UNPARSED_ENTRY
    mode, kind, oid, size = (p.decode("ascii", "replace") for p in parts)
    return TreeEntry(mode, kind, oid, int(size) if size.isdigit() else None)


def read_entry_blob(root: Path, entry: TreeEntry) -> bytes | None:
    """The bytes of the blob *entry* names; None when the read fails."""
    blob = git(root, "cat-file", "blob", entry.oid, check=False)
    return blob.stdout if blob.returncode == 0 else None


def read_blob(root: Path, rev: str, path: str) -> bytes | None:
    """The bytes of regular file *path* at commit *rev*; None when absent or not a small file."""
    entry = tree_entry(root, rev, path)
    if entry is None or not entry.regular or (entry.size or 0) > MAX_BLOB_BYTES:
        return None
    return read_entry_blob(root, entry)


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
    entry = tree_entry(root, base, path)
    if entry is None:
        return None
    if entry is UNPARSED_ENTRY:
        raise Refusal(CODE_INVALID_STANDING_ORDERS, f"{path} has an unreadable tree entry")
    if not entry.regular or entry.size is None:
        raise Refusal(CODE_INVALID_STANDING_ORDERS, f"{path} is not a regular file blob")
    if entry.size > MAX_STANDING_ORDERS_BYTES:  # judged before the blob is read
        raise Refusal(
            CODE_INVALID_STANDING_ORDERS,
            f"{path}: larger than {MAX_STANDING_ORDERS_BYTES} bytes",
        )
    data = read_entry_blob(root, entry)
    if data is None:
        raise Refusal(CODE_INVALID_STANDING_ORDERS, f"{path} cannot be read")
    problem = standing_orders_problem(data)
    if problem is not None:
        raise Refusal(CODE_INVALID_STANDING_ORDERS, f"{path}: {problem}")
    text = data.decode("utf-8")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return {
        "path": path,
        "sha256": hashlib.sha256(data).hexdigest(),
        "fence": "`" * max(3, longest + 1),
        "text": text,
    }


def _live_spans(line: str, in_comment: bool) -> tuple[list[tuple[int, int]], bool]:
    """The ``(start, end)`` spans of *line* outside HTML comments, and the state after it."""
    spans: list[tuple[int, int]] = []
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
                spans.append((pos, len(line)))
                break
            spans.append((pos, opened))
            in_comment = True
            pos = opened + 4
    return spans, in_comment


def _live(line: str, in_comment: bool) -> tuple[str, bool]:
    """The text of *line* outside HTML comments, and the comment state after it."""
    spans, in_comment = _live_spans(line, in_comment)
    return "".join(line[a:b] for a, b in spans), in_comment


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


def _status_token_span(text: str) -> tuple[int, int] | None:
    """The ``(start, end)`` character span in *text* of the token ``parse_status`` reads."""
    in_comment = False
    offset = 0
    for part in text.splitlines(keepends=True):
        lines = part.splitlines()
        line = lines[0] if lines else ""
        before = in_comment
        spans, in_comment = _live_spans(line, in_comment)
        if not before and _BOUNDING_HEADING_RE.match(line):
            return None
        live = "".join(line[a:b] for a, b in spans)
        original = [i for a, b in spans for i in range(a, b)]
        lead = len(live) - len(live.lstrip())
        match = _STATUS_RE.match(live.strip())
        if match:
            raw = match.group(1)
            cut = raw
            for delim in (" (", " →", "<!--"):
                cut = cut.split(delim, 1)[0]
            words = cut.split()
            if not words:
                return None
            word = words[0]
            token = word.strip("`")
            if not token:
                return None
            begin = lead + match.start(1) + cut.index(word) + (len(word) - len(word.lstrip("`")))
            return offset + original[begin], offset + original[begin + len(token) - 1] + 1
        offset += len(part)
    return None


def bound_form(data: bytes) -> bytes:
    """The brief's bytes with only the status token of its one ``Status:`` line replaced.

    The token is the one ``parse_status`` reads; every other byte, the rest of that line
    included, is kept. A brief with no readable status line is returned unchanged.
    """
    text = data.decode("utf-8", "surrogateescape")
    span = _status_token_span(text)
    if span is None:
        return data
    return (text[: span[0]] + STATUS_PLACEHOLDER + text[span[1] :]).encode(
        "utf-8", "surrogateescape"
    )


# ── run grants ──────────────────────────────────────────────────────────────

_CONFIRMED_BY_RE = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*")
_RECORD_MARK = "**Run grant:**"
_RECORD_LINE_RE = re.compile(
    r"- \*\*Run grant:\*\* required \(confirmed (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z\)"
)


def _now() -> datetime:
    """The runner host's current UTC time; the one clock, so tests patch it."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class Grant:
    """A validated run grant. ``confirmed_by`` is checked and then dropped; it is never emitted."""

    confirmed_at: datetime
    expires_at: datetime
    done_when: str
    slices: tuple[str, ...]
    retry_budget: int
    max_slices_in_flight: int
    held_actions: tuple[str, ...]


class GrantProblem(Exception):
    """A grant or record is malformed; ``detail`` is one fixed-vocabulary value.

    The detail never holds grant text or a parser message.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


def _is_int(value: object) -> bool:
    """True for an integer that is not a boolean."""
    return type(value) is int


def _is_utc_seconds(value: object) -> bool:
    """True for an aware datetime at UTC offset zero with whole seconds."""
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() == timedelta(0)
        and value.microsecond == 0
    )


def _distinct_strings(value: object) -> bool:
    """True for a list of distinct strings."""
    return (
        isinstance(value, list)
        and all(isinstance(v, str) for v in value)
        and len(set(value)) == len(value)
    )


def judge_grant(
    data: bytes,
    *,
    brief_slug: str,
    spec_map: list[str],
    retry_budget_cap: int,
    now: datetime,
) -> Grant:
    """Validate the grant file bytes, or raise ``GrantProblem`` with a fixed detail.

    Check order: size, UTF-8, hidden text, TOML, any table, any extra key, then each
    AC-0003 key in order (a missing key or a bad value is ``key:<name>``), then
    ``expiry-order``, ``expiry-too-long`` and ``confirmed-in-future``. Nothing is clamped.
    """
    if len(data) > MAX_GRANT_BYTES:
        raise GrantProblem("oversize")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        raise GrantProblem("not-utf8") from None
    if _hidden_text_problem(text) is not None:
        raise GrantProblem("hidden-text")
    try:
        table = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        raise GrantProblem("not-toml") from None
    if any(isinstance(v, dict) for v in table.values()):
        raise GrantProblem("table")
    if any(k not in GRANT_KEYS for k in table):
        raise GrantProblem("unknown-key")
    for key in GRANT_KEYS:
        if key not in table:
            raise GrantProblem(f"key:{key}")
    slices = table["slices"]
    checks = {
        "schema_version": _is_int(table["schema_version"]) and table["schema_version"] == 1,
        "brief": table["brief"] == brief_slug,
        "confirmed_by": isinstance(table["confirmed_by"], str)
        and len(table["confirmed_by"]) <= 39
        and table["confirmed_by"].isascii()
        and _CONFIRMED_BY_RE.fullmatch(table["confirmed_by"]) is not None,
        "confirmed_at": _is_utc_seconds(table["confirmed_at"]),
        "expires_at": _is_utc_seconds(table["expires_at"]),
        "done_when": isinstance(table["done_when"], str) and table["done_when"] in DONE_WHEN,
        "slices": _distinct_strings(slices)
        and bool(slices)
        and all(SLUG_RE.fullmatch(s) is not None and s in spec_map for s in slices),
        "retry_budget": _is_int(table["retry_budget"])
        and 0 <= table["retry_budget"] <= retry_budget_cap,
        "max_slices_in_flight": _is_int(table["max_slices_in_flight"])
        and table["max_slices_in_flight"] == 1,
        "held_actions": _distinct_strings(table["held_actions"])
        and all(a in HELD_ACTIONS for a in table["held_actions"]),
    }
    for key in GRANT_KEYS:
        if not checks[key]:
            raise GrantProblem(f"key:{key}")
    confirmed_at: datetime = table["confirmed_at"]
    expires_at: datetime = table["expires_at"]
    if expires_at <= confirmed_at:
        raise GrantProblem("expiry-order")
    if expires_at - confirmed_at > GRANT_MAX_LIFETIME:
        raise GrantProblem("expiry-too-long")
    if confirmed_at > now + CONFIRM_SKEW:
        raise GrantProblem("confirmed-in-future")
    return Grant(
        confirmed_at=confirmed_at,
        expires_at=expires_at,
        done_when=table["done_when"],
        slices=tuple(slices),
        retry_budget=table["retry_budget"],
        max_slices_in_flight=1,
        held_actions=tuple(sorted(table["held_actions"])),
    )


def record_evidence(text: str) -> bool:
    """True when the brief holds a ``**Run grant:**`` mark anywhere, comments included."""
    return _RECORD_MARK in text


def judge_record(text: str) -> datetime | None:
    """The UTC time of the brief's run-grant record line, None when the brief has no mark.

    Two marks are ``record-repeated``. The one mark must be a preamble line (before the first
    ``##`` heading), outside any HTML comment, and read exactly
    ``- **Run grant:** required (confirmed YYYY-MM-DDTHH:MM:SSZ)``, else ``record-form``.
    """
    if text.count(_RECORD_MARK) == 0:
        return None
    if text.count(_RECORD_MARK) > 1:
        raise GrantProblem("record-repeated")
    in_comment = False
    for line in text.splitlines():
        before = in_comment
        live, in_comment = _live(line, in_comment)
        if not before and _BOUNDING_HEADING_RE.match(line):
            break
        if _RECORD_MARK in live:
            match = _RECORD_LINE_RE.fullmatch(live)
            if match is None:
                raise GrantProblem("record-form")
            try:
                stamp = datetime.strptime(match.group(1), "%Y-%m-%dT%H:%M:%S")
            except ValueError:
                raise GrantProblem("record-form") from None
            return stamp.replace(tzinfo=UTC)
    raise GrantProblem("record-form")


def check_record_matches(grant: Grant, record_ts: datetime) -> None:
    """Raise ``record-mismatch`` unless the grant's confirmation time is the record's."""
    if grant.confirmed_at != record_ts:
        raise GrantProblem("record-mismatch")


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


def brief_path(brief_slug: str) -> str:
    """The repository path of the brief."""
    return f"docs/product/briefs/{brief_slug}.md"


def read_brief_text(root: Path, base: str, brief_slug: str) -> str:
    """The brief text at the base; refuses ``invalid-spec-map`` when absent or not UTF-8."""
    data = read_blob(root, base, brief_path(brief_slug))
    if data is None:
        raise Refusal("invalid-spec-map", f"{brief_path(brief_slug)} is not at the base")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refusal("invalid-spec-map", "the brief is not UTF-8") from exc


def read_spec_map(root: Path, base: str, brief_slug: str) -> list[str]:
    """The brief's Spec map slugs, read from the base commit's blob."""
    return parse_spec_map(read_brief_text(root, base, brief_slug))


def brief_status(text: str) -> str | None:
    """The brief's ``Status:`` token when it is a known brief status, else None."""
    token = parse_status(text)
    return token if token in BRIEF_STATUSES else None


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


def supervisor_argv(*argv: str) -> list[str]:
    """The supervisor command line: an isolated interpreter, UTF-8 mode, no bytecode.

    ``-I`` keeps every inherited ``PYTHON*`` variable, the user site directory and the working
    directory out of the import path, so a module committed in a slice worktree never loads.
    """
    return [sys.executable, "-I", "-X", "utf8", "-B", str(SUPERVISOR), *argv]


def run_supervisor(worktree: str, *argv: str) -> tuple[int, Any]:
    """Run the supervisor beside this file in *worktree*; return (exit code, parsed JSON or None).

    A call that timed out answers ``CODE_TIMEOUT``; one that could not start, ``CODE_UNAVAILABLE``.

    Never the slice branch's copy: the path is fixed from this file's own location.
    """
    try:
        done = subprocess.run(
            supervisor_argv(*argv),
            cwd=worktree,
            env=_clean_env(),
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


def spec_dir_present(root: Path, rev: str, spec_slug: str) -> bool:
    """True when ``docs/specs/<spec_slug>`` exists at *rev*, whatever it holds."""
    return tree_entry(root, rev, f"docs/specs/{spec_slug}") is not None


def read_slice(root: Path, spec_slug: str, found: Slice) -> Reading:
    """The stage of one slice worktree; no ``spec.md`` on its branch head means ``drafting``.

    A ``spec.md`` that is there but is not a small regular file is unreadable.
    """
    if not found.readable or found.head is None or found.worktree is None:
        return Reading(STAGE_UNREADABLE, detail=found.detail or "unreadable-worktree")
    spec_dir = f"docs/specs/{spec_slug}"
    if tree_entry(root, found.head, f"{spec_dir}/spec.md") is None:
        return Reading(STAGE_DRAFTING)
    if read_blob(root, found.head, f"{spec_dir}/spec.md") is None:
        return Reading(STAGE_UNREADABLE, detail="spec-unreadable")
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
    # Why the gate entries are unavailable, when they are.
    gates_detail: str | None = None

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


def read_rows(
    root: Path, base: str, brief_slug: str, slugs: list[str], *, runnable: bool = True
) -> list[Row]:
    """Every row's spec status, worktree, stop, stage and readiness, in Spec map order.

    On a brief that is not runnable (AC-0001) no row without a slice worktree is ready.
    """
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
            elif spec_blob is None and not spec_dir_present(root, base, slug):
                mode, ready = "author-spec", earlier_stopped
            elif spec_blob is None:
                detail = "spec-unreadable"
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
                ready=ready and runnable,
                mode=mode if ready and runnable else None,
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
    text = read_brief_text(resolved, base, brief_slug)
    slugs = parse_spec_map(text)
    runnable = brief_status(text) in RUNNABLE_STATUSES
    return base, read_rows(resolved, base, brief_slug, slugs, runnable=runnable)


# ── gates, marker, status ───────────────────────────────────────────────────


def read_gates_answer(worktree: str) -> tuple[list[dict[str, Any]] | None, str | None]:
    """The supervisor's ``gates`` entries in *worktree*, or None and a short fixed cause.

    A non-zero exit or any output that is not ``{"gates": [<object with a state>, ...]}``
    is unavailable, never an empty or a pending listing.
    """
    code, payload = run_supervisor(worktree, "gates")
    if code != 0:
        return None, _exit_detail(code, payload)
    entries = payload.get("gates") if isinstance(payload, dict) else None
    if not isinstance(entries, list) or not all(
        isinstance(e, dict) and isinstance(e.get("state"), str) for e in entries
    ):
        return None, "supervisor-bad-output"
    return entries, None


def read_gates(worktree: str) -> list[dict[str, Any]] | None:
    """The entries the supervisor's ``gates`` verb prints in *worktree*; None when unavailable."""
    return read_gates_answer(worktree)[0]


def attach_gates(rows: list[Row]) -> None:
    """Fill each slice row's gate entries; a row with no worktree has none."""
    for row in rows:
        if not row.present:
            row.gates = []
        elif row.worktree is None or row.head is None:
            row.gates, row.gates_detail = None, row.detail or "unreadable-worktree"
        else:
            row.gates, row.gates_detail = read_gates_answer(row.worktree)


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
    entry = tree_entry(root, head, f"docs/specs/{slug}/delivery")
    return entry.oid if entry is not None and entry.kind == "tree" else ""


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
    if skill is None:
        raise Refusal(
            CODE_INVALID_POLICY, "the runner's skill directory is not inside this repository"
        )
    path = f"{skill}/supervisor-policy.json"
    data = read_blob(root, base, path)
    if data is None:
        raise Refusal(CODE_INVALID_POLICY, f"{path} is not a small regular file at the base")
    try:
        policy = json.loads(data.decode("utf-8"))
    except ValueError as exc:
        raise Refusal(CODE_INVALID_POLICY, f"{path} is not UTF-8 JSON at the base") from exc
    lease = policy.get("lease") if isinstance(policy, dict) else None
    if not isinstance(lease, dict):
        raise Refusal(CODE_INVALID_POLICY, f"{path} has no lease table at the base")
    admission = _admission()
    try:
        admission._check_lease(lease)
    except admission.Refusal as exc:
        raise Refusal(
            CODE_INVALID_POLICY, _bounded(f"the base lease table is invalid: {exc.detail}")
        ) from exc
    return lease


def read_lease_cap(root: Path, base: str) -> int:
    """``lease.max_slices_in_flight`` from the policy beside the runner, at the base."""
    return int(read_lease(root, base)["max_slices_in_flight"])


# ── grant state ─────────────────────────────────────────────────────────────

GRANT_VALID = "valid"
GRANT_REFUSED = "refused"
GRANT_SPENT = "spent"
_COMMIT_ID_RE = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?")


@dataclass(frozen=True)
class GrantView:
    """The grant's state for one call: ``reason`` and ``detail`` are fixed-vocabulary values."""

    state: str
    reason: str | None = None
    detail: str | None = None
    grant: Grant | None = None
    anchor: str | None = None


def grant_path(brief_slug: str) -> str:
    """The repository path of the brief's grant file."""
    return f"{RUN_GRANTS_DIR}/{brief_slug}.toml"


def _blob_oid(root: Path, rev: str, path: str) -> str | None:
    entry = tree_entry(root, rev, path)
    return None if entry is None else entry.oid


def binding_problem(
    root: Path, base: str, brief_slug: str, record_at: datetime
) -> tuple[str | None, str | None]:
    """``(anchor, None)`` when the grant is bound to the base, else ``(None, stale detail)``.

    The anchor is the last first-parent commit to change the grant file. Any Git or blob
    failure fails closed as ``anchor-not-found``.
    """
    try:
        return _binding(root, base, brief_slug, record_at)
    except Refusal:
        return None, "anchor-not-found"


def _binding(
    root: Path, base: str, brief_slug: str, record_at: datetime
) -> tuple[str | None, str | None]:
    done = git(
        root, "log", "-1", "--first-parent", "--format=%H", base, "--", grant_path(brief_slug),
        check=False,
    )
    anchor = done.stdout.decode("ascii", "replace").strip()
    if done.returncode != 0 or _COMMIT_ID_RE.fullmatch(anchor) is None:
        return None, "anchor-not-found"
    path = brief_path(brief_slug)
    now_brief = read_blob(root, base, path)
    then_brief = read_blob(root, anchor, path)
    if now_brief is None or then_brief is None:
        return None, "brief-changed"
    if bound_form(now_brief) != bound_form(then_brief):
        return None, "brief-changed"
    orders = f"{STANDING_ORDERS_DIR}/{brief_slug}.md"
    if _blob_oid(root, base, orders) != _blob_oid(root, anchor, orders):
        return None, "standing-orders-changed"
    parent = read_blob(root, f"{anchor}^1", path)
    stamp = record_at.strftime("%Y-%m-%dT%H:%M:%S")
    if parent is not None and any(
        m.group(1) == stamp
        for m in _RECORD_LINE_RE.finditer(parent.decode("utf-8", "replace"))
    ):
        return None, "not-reconfirmed"
    return anchor, None


def _granted_stops_met(grant: Grant, rows: list[Row]) -> bool:
    """True when every granted slice has reached the stop the grant's ``done_when`` names."""
    stops = {row.slice: row.stop for row in rows}
    wanted = (STOP_MERGED,) if grant.done_when == "all-granted-merged" else (
        STOP_MERGE_READY, STOP_MERGED,
    )
    return all(stops.get(slug) in wanted for slug in grant.slices)


def read_grant(
    root: Path,
    base: str,
    brief_slug: str,
    rows: list[Row],
    lease: dict[str, Any],
    now: datetime,
) -> GrantView | None:
    """The grant's state at the base (AC-0006), or None for a no-grant run.

    The first rule that applies decides: brief closed, brief not runnable, missing, malformed,
    stale, expired, done, else valid. Nothing here reads a file outside the base commit.
    """
    text = read_brief_text(root, base, brief_slug)
    status = brief_status(text)
    entry = tree_entry(root, base, grant_path(brief_slug))
    evidence = record_evidence(text)
    if not evidence and entry is None:
        return None
    if status in CLOSED_STATUSES:
        return GrantView(GRANT_SPENT, "brief-closed")
    if status not in RUNNABLE_STATUSES:
        return GrantView(GRANT_REFUSED, "brief-not-ready")
    if entry is None:
        return GrantView(GRANT_REFUSED, "missing")
    try:
        grant = _judged(root, entry, text, brief_slug, [row.slice for row in rows], lease, now)
    except GrantProblem as problem:
        return GrantView(GRANT_REFUSED, "malformed", problem.detail)
    anchor, stale = binding_problem(root, base, brief_slug, grant.confirmed_at)
    if stale is not None:
        return GrantView(GRANT_REFUSED, "stale", stale)
    if now >= grant.expires_at:
        return GrantView(GRANT_SPENT, "expired", None, grant, anchor)
    if _granted_stops_met(grant, rows):
        return GrantView(GRANT_SPENT, "done", None, grant, anchor)
    return GrantView(GRANT_VALID, None, None, grant, anchor)


def _judged(
    root: Path,
    entry: TreeEntry,
    text: str,
    brief_slug: str,
    spec_map: list[str],
    lease: dict[str, Any],
    now: datetime,
) -> Grant:
    """The validated grant for the base's grant-path *entry*, or ``GrantProblem``."""
    if not record_evidence(text):
        raise GrantProblem("no-record")
    if not entry.regular:
        raise GrantProblem("not-regular")
    if (entry.size or 0) > MAX_GRANT_BYTES:
        raise GrantProblem("oversize")
    data = read_entry_blob(root, entry)
    if data is None:
        raise GrantProblem("not-regular")
    grant = judge_grant(
        data,
        brief_slug=brief_slug,
        spec_map=spec_map,
        retry_budget_cap=int(lease["retry_budget"]),
        now=now,
    )
    record_at = judge_record(text)
    if record_at is None:
        raise GrantProblem("record-form")
    check_record_matches(grant, record_at)
    return grant


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def grant_answer(view: GrantView | None) -> dict[str, Any] | None:
    """The ``grant`` object of a ``next`` or ``status`` answer; None for a no-grant run.

    Typed fields only: never the grant file's text, ``confirmed_by`` or a parser message.
    """
    if view is None:
        return None
    out: dict[str, Any] = {
        "state": view.state,
        "reason": view.reason,
        "detail": view.detail,
        "human_only": list(HUMAN_ONLY),
    }
    grant = view.grant
    if grant is None:
        out["held_actions"] = list(HELD_ACTIONS)
        return out
    out.update(
        anchor=view.anchor,
        expires_at=_iso(grant.expires_at),
        done_when=grant.done_when,
        slices=list(grant.slices),
        retry_budget=grant.retry_budget,
        max_slices_in_flight=grant.max_slices_in_flight,
        held_actions=list(grant.held_actions),
    )
    return out


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


def _relayed_slug(value: Any) -> str | None:
    """A supervisor code or owner as relayed: itself when a plain slug, else ``WITHHELD``."""
    if value is None:
        return None
    return value if isinstance(value, str) and SLUG_RE.fullmatch(value) else WITHHELD


def _relayed_detail(value: Any) -> str | None:
    """A supervisor detail as relayed: cut to ``MAX_RELAYED_DETAIL``, or ``WITHHELD``.

    Text holding a control, hidden or line-separator character is never relayed.
    """
    if value is None:
        return None
    if not isinstance(value, str) or unsafe_path_char(value):
        return WITHHELD
    return value[:MAX_RELAYED_DETAIL]


def _reason(
    row: Row,
    rows: list[Row],
    cap_reached: bool,
    *,
    runnable: bool = True,
    granted: frozenset[str] | None = None,
) -> dict[str, Any]:
    """The first reason, in the stated order, that *row* is not named by an action.

    With *granted* (a valid grant's slices) a non-granted row reads ``not-granted`` after its
    slice-state reasons, and a granted row a non-granted row holds back reads
    ``waits-on-ungranted``. A brief that is not *runnable* reads ``brief-not-ready`` for a row
    without a worktree.
    """

    def ungranted(r: Row) -> bool:
        return granted is not None and r.slice not in granted

    earlier_open = [e for e in rows[: rows.index(row)] if e.stop == STOP_NONE]
    pilot = _pilot(rows)
    out: dict[str, Any] = {"slice": row.slice}
    refusal = row.refusal or {}
    if row.stage == STAGE_UNREADABLE:
        out.update(reason="unreadable", detail=row.detail)
    elif row.stage == STAGE_SUPERVISOR_CHANGED:
        out["reason"] = "supervisor-changed"
    elif row.stage == STAGE_REFUSED:
        out.update(
            reason="refused",
            code=_relayed_slug(refusal.get("code")),
            owner=_relayed_slug(refusal.get("owner")),
            detail=_relayed_detail(refusal.get("detail")),
        )
    elif row.stage == STAGE_AWAITING_DECISION:
        out["reason"] = "awaiting-decision"
    elif row.present and not _gate_clean(row):
        out["reason"] = "gate-not-clean"
        if row.gates is None and row.gates_detail is not None:
            out["detail"] = row.gates_detail
    elif row.present and row.stage == STAGE_TERMINAL:
        out["reason"] = "terminal-not-ready"
    elif ungranted(row):
        out["reason"] = "not-granted"
    elif row.ready and cap_reached:
        filled = any(ungranted(r) for r in rows if r.present and r.stop == STOP_NONE)
        out["reason"] = "waits-on-ungranted" if filled else "in-flight-cap"
    elif row.ready:
        held = any(r.slice == pilot and ungranted(r) for r in rows)
        out["reason"] = "waits-on-ungranted" if held else "pilot-in-flight"
    elif not runnable and not row.present:
        out["reason"] = "brief-not-ready"
    elif not row.present and row.spec_status in (None, "Draft") and earlier_open:
        held = any(ungranted(e) for e in earlier_open)
        out["reason"] = "waits-on-ungranted" if held else "earlier-row-not-stopped"
    else:
        out["reason"] = "not-dispatchable"
        if row.detail is not None:
            out["detail"] = row.detail
    return out


def _resumable(row: Row) -> bool:
    """The no-grant resume predicate: a worktree, no stop, a resumable stage, no gate entry."""
    return (
        row.worktree is not None
        and row.stop == STOP_NONE
        and row.stage in RESUMABLE_STAGES
        and row.gates == []
    )


def _pending_gates(rows: list[Row]) -> list[dict[str, Any]]:
    """Every ``pending`` gate, as ``await-gates`` lists them."""
    return [
        g for row in rows if _has_pending(row) for g in joined_gates(row)
        if g.get("state") == GATE_PENDING
    ]


def decide_next(
    rows: list[Row],
    max_in_flight: int,
    *,
    runnable: bool = True,
    granted: frozenset[str] | None = None,
    exempt: frozenset[str] = frozenset(),
) -> dict[str, Any]:
    """The one action ``next`` answers, the first that applies in the stated order.

    A brief that is not *runnable* starts nothing and resumes only the *exempt* slices
    (AC-0002). With a valid grant, *granted* holds its slices and *max_in_flight* is already
    capped at 1: the pilot, the earlier-row rule and the in-flight count run over every row,
    and a non-granted row is only skipped when a slice is chosen.
    """
    for row in rows:
        allowed = row.slice in exempt if not runnable else granted is None or row.slice in granted
        if allowed and _resumable(row):
            action = {
                "kind": "resume-slice",
                "slice": row.slice,
                "worktree": row.worktree,
                "stage": row.stage,
            }
            return {**action, "exemption": EXEMPTION} if not runnable else action
    in_flight = sum(1 for r in rows if r.present and r.stop == STOP_NONE)
    cap_reached = in_flight >= max_in_flight
    pilot = _pilot(rows)
    if runnable and not cap_reached:
        for row in rows:
            if row.ready and (pilot is None or row.slice == pilot) and (
                granted is None or row.slice in granted
            ):
                return {
                    "kind": "start-slice",
                    "slice": row.slice,
                    "branch": row.branch,
                    "mode": row.mode,
                    "spec_status": row.spec_status,
                    "plan_status": row.plan_status,
                }
    pending = _pending_gates(rows)
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
            _reason(row, rows, cap_reached, runnable=runnable, granted=granted)
            for row in rows
            if row.stop != STOP_MERGED
        ],
    }


def grant_action(view: GrantView, rows: list[Row]) -> dict[str, Any]:
    """The action for a refused or spent grant: it names no slice to start or resume."""
    if view.reason == "brief-closed" and all(row.stop == STOP_MERGED for row in rows):
        return {"kind": "complete"}
    merge_ready = [row.slice for row in rows if row.stop == STOP_MERGE_READY]
    return {
        "kind": "grant-refused" if view.state == GRANT_REFUSED else "grant-spent",
        "reason": view.reason,
        "detail": view.detail,
        "gates": _pending_gates(rows),
        "merge_ready": merge_ready,
        "spec_paths": [spec_path(slug) for slug in merge_ready],
    }


def exempt_slices(root: Path, rows: list[Row], now: datetime) -> frozenset[str]:
    """The slices a not-runnable brief with no grant evidence may still resume (AC-0002).

    Only before ``PRE_READY_EXEMPTION_ENDS``, and only a row that meets the resume predicate
    and whose slice branch head holds its ``spec.md``.
    """
    if now >= PRE_READY_EXEMPTION_ENDS:
        return frozenset()
    return frozenset(
        row.slice
        for row in rows
        if _resumable(row)
        and row.head is not None
        and tree_entry(root, row.head, f"docs/specs/{row.slice}/spec.md") is not None
    )


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
    root: Path,
    base: str,
    rows: list[Row],
    slice_slug: str,
    task_id: str,
    failure_class: str,
    grant: GrantView | None = None,
) -> dict[str, Any]:
    """Classify one failed ``implement-task`` dispatch of a slice.

    A valid *grant*'s retry budget replaces the lease's; a refused or spent grant surfaces
    every class to a human.
    """
    row = next((r for r in rows if r.slice == slice_slug), None)
    if row is None:
        raise Refusal("unknown-slice", f"{slice_slug} is not a Spec map row")
    if not row.present:
        raise Refusal("no-slice-worktree", f"{slice_slug} has no slice worktree")
    budget = (
        grant.grant.retry_budget
        if grant is not None and grant.state == GRANT_VALID and grant.grant is not None
        else read_retry_budget(root, base)
    )
    n = read_failed_attempts(row, task_id)
    action = classify_action(failure_class, n, budget)
    if grant is not None and grant.state != GRANT_VALID:
        action = ACTION_SURFACE
    return {"base": base, "action": action, "failed_attempts": n}


# ── guard ───────────────────────────────────────────────────────────────────


def resolve_commit(root: Path, rev: str) -> str:
    """The full commit id *rev* names; refuses ``unknown-revision`` when it names none."""
    if not rev or rev.startswith("-"):
        raise Refusal(CODE_UNKNOWN_REVISION, "a revision does not name a commit")
    done = git(root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}", check=False)
    found = _text(done.stdout)
    if done.returncode != 0 or _COMMIT_ID_RE.fullmatch(found) is None:
        raise Refusal(CODE_UNKNOWN_REVISION, "a revision does not name a commit")
    return found


def merge_base(root: Path, left: str, right: str) -> str:
    """The merge base of two commit ids; refuses ``unknown-revision`` when there is none."""
    done = git(root, "merge-base", left, right, check=False)
    found = _text(done.stdout)
    if done.returncode != 0 or _COMMIT_ID_RE.fullmatch(found) is None:
        raise Refusal(CODE_UNKNOWN_REVISION, "the revisions have no merge base")
    return found


def changed_paths(root: Path, base: str, head: str) -> list[str]:
    """Paths changed from *base* to *head*, rename detection off, so a rename lists both sides."""
    done = git(root, "diff", "--name-only", "-z", "--no-renames", "--no-ext-diff", base, head)
    return sorted(
        {p.decode("utf-8", "surrogateescape") for p in done.stdout.split(b"\0") if p}
    )


def _text_at(root: Path, rev: str, path: str) -> str | None:
    """The text of a small regular file at *rev*, or None when absent or unreadable."""
    data = read_blob(root, rev, path)
    return None if data is None else data.decode("utf-8", "replace")


def _rows_of(text: str | None) -> list[str] | None:
    """The Spec map slugs of *text*; None when absent or when the map does not parse."""
    if text is None:
        return None
    try:
        return parse_spec_map(text)
    except Refusal:
        return None


def _grant_evidence(root: Path, rev: str, slug: str, text: str | None) -> bool:
    """True when the brief at *rev* has a run-grant record or a grant file for its slug."""
    if text is not None and record_evidence(text):
        return True
    return tree_entry(root, rev, f"{RUN_GRANTS_DIR}/{slug}.toml") is not None


def brief_change_kind(
    root: Path, base: str, head: str, slug: str
) -> tuple[str | None, set[str]]:
    """The one grant-change kind of a changed brief, and the Spec map slugs it adds.

    Precedence when a brief matches several: ``brief-granted``, then ``brief-made-runnable``,
    then ``brief-spec-map``. None when the brief is not a grant change.
    """
    path = brief_path(slug)
    before, after = _text_at(root, base, path), _text_at(root, head, path)
    was = brief_status(before) if before is not None else None
    now = brief_status(after) if after is not None else None
    old_rows, new_rows = _rows_of(before), _rows_of(after)
    added = set(new_rows or ()) - set(old_rows or ())
    granted = (
        (_grant_evidence(root, base, slug, before) or _grant_evidence(root, head, slug, after))
        and bound_form((before or "").encode("utf-8", "surrogateescape"))
        != bound_form((after or "").encode("utf-8", "surrogateescape"))
        and now not in CLOSED_STATUSES
    )
    if granted:
        return "brief-granted", added
    if now in RUNNABLE_STATUSES and was not in RUNNABLE_STATUSES:
        return "brief-made-runnable", added
    if (was in RUNNABLE_STATUSES or now in RUNNABLE_STATUSES) and old_rows != new_rows:
        return "brief-spec-map", added
    return None, added


def _companions(root: Path, base: str, head: str, slugs: set[str], changed: set[str]) -> list[str]:
    """New Draft ``spec.md`` and Drafting ``plan.md`` files of the slugs a change adds to a map."""
    found: list[str] = []
    for slug in sorted(slugs):
        for name, status in (("spec.md", "Draft"), ("plan.md", "Drafting")):
            path = f"{spec_path(slug)}/{name}"
            if path not in changed or tree_entry(root, base, path) is not None:
                continue
            text = _text_at(root, head, path)
            if text is not None and parse_status(text) == status:
                found.append(path)
    return sorted(found)


def guard_surface_prefixes(root: Path) -> tuple[str, ...]:
    """The path prefixes the guard lists as its own surface.

    The work-loop scripts directory in the pack, plus this runner's own skill directory when
    it lives inside *root* (a self-hosted copy), plus ``.github/workflows/``. A changed
    path counts when it starts with a prefix or equals one of ``GUARD_SURFACE_FILES``.
    Informational only: listing a path never changes the verdict.
    """
    try:
        own = SKILL_DIR.relative_to(root.resolve()).as_posix() + "/scripts/"
    except ValueError:
        return GUARD_SURFACE_PREFIXES
    return (*GUARD_SURFACE_PREFIXES, own)


def guard(root: Path, from_rev: str, to_rev: str) -> dict[str, Any]:
    """The guard answer for the change from the merge base of the two revisions to *to_rev*."""
    require_git_version()
    top = root.resolve()
    head = resolve_commit(top, to_rev)
    base = merge_base(top, resolve_commit(top, from_rev), head)
    paths = changed_paths(top, base, head)
    changed = set(paths)
    changes: dict[str, str] = {}
    added: set[str] = set()
    for path in paths:
        if path.startswith(f"{RUN_GRANTS_DIR}/"):
            changes[path] = "grant-file"
        elif path.startswith(f"{STANDING_ORDERS_DIR}/"):
            changes[path] = "standing-orders"
        elif path.startswith(f"{BRIEFS_DIR}/") and path.endswith(".md"):
            slug = path[len(BRIEFS_DIR) + 1 : -3]
            if SLUG_RE.fullmatch(slug) is None:
                continue
            kind, adds = brief_change_kind(top, base, head, slug)
            if kind is not None:
                changes[path] = kind
                added |= adds
    companions = _companions(top, base, head, added, changed) if changes else []
    prefixes = guard_surface_prefixes(top)
    surface = [p for p in paths if p.startswith(prefixes) or p in GUARD_SURFACE_FILES]
    other = len(changed - set(changes) - set(companions))

    def shown(path: str) -> str:
        return WITHHELD if unsafe_path_char(path) else path

    mixed = bool(changes) and other > 0
    answer: dict[str, Any] = {
        "merge_base": base,
        "to": head,
        "grant_changes": [{"path": shown(p), "kind": changes[p]} for p in sorted(changes)],
        "companions": [shown(p) for p in companions],
        "guard_surface": [shown(p) for p in surface],
        "other_paths": other,
        "verdict": "fail" if mixed else "pass",
    }
    if mixed:
        answer["refusal"] = {
            "code": CODE_GRANT_CHANGE_MIXED,
            "detail": "grant changes are mixed with other paths",
        }
    return answer


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
    verb = verbs.add_parser(GUARD_VERB)
    verb.add_argument("--from", dest="from_rev", required=True)
    verb.add_argument("--to", dest="to_rev", required=True)
    verb.add_argument("--root", default=".")
    return parser


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def spec_path(slug: str) -> str:
    """The repository path of the spec directory a Spec map row names."""
    return f"docs/specs/{slug}"


def with_contract_fields(action: dict[str, Any], base: str) -> dict[str, Any]:
    """*action* plus the fields a program controller reads without deriving them.

    Every action carries ``base``; one that names a slice carries its ``spec_path``,
    ``await-merge`` carries ``spec_paths`` beside ``slices``, and each ``blocked`` row
    carries its own ``spec_path``.
    """
    out = {**action, "base": base}
    if "slice" in out:
        out["spec_path"] = spec_path(out["slice"])
    if out["kind"] == "await-merge":
        out["spec_paths"] = [spec_path(slug) for slug in out["slices"]]
    if out["kind"] == "blocked":
        out["rows"] = [{**row, "spec_path": spec_path(row["slice"])} for row in out["rows"]]
    return out


def _versioned(verb: str, answer: dict[str, Any]) -> dict[str, Any]:
    """*answer* with ``schema_version`` first when the verb is ``next``."""
    return {"schema_version": NEXT_SCHEMA_VERSION, **answer} if verb == "next" else answer


def internal_error_trace(exc: BaseException) -> str:
    """Each failing frame's file, line number and function, then the exception type.

    Never a message or source text. Walks to the cause, or else to an unsuppressed context,
    naming each exception once, root first; group members are not walked. Bounded to the
    last ``MAX_TRACEBACK`` characters: a long trace loses the root cause's frames first and
    keeps the raised exception's innermost frames and type.
    """
    chain: list[BaseException] = []
    current: BaseException | None = exc
    while current is not None and all(current is not seen for seen in chain):
        chain.append(current)
        if current.__cause__ is not None:
            current = current.__cause__
        else:
            current = None if current.__suppress_context__ else current.__context__
    lines: list[str] = []
    for item in reversed(chain):
        for frame in traceback.extract_tb(item.__traceback__):
            lines.append(f"  {frame.filename}:{frame.lineno} in {frame.name}\n")
        lines.append(f"{type(item).__name__}\n")
    return "".join(lines)[-MAX_TRACEBACK:]


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
        if args.verb == GUARD_VERB:
            answer = guard(root, args.from_rev, args.to_rev)
            _emit(answer)
            return EXIT_REFUSED if answer["verdict"] == "fail" else EXIT_OK
        base, rows = read_brief(root, args.brief_slug, lease=args.verb != "gates")
        view: GrantView | None = None
        lease: dict[str, Any] = {}
        now = _now()
        if args.verb != "gates":
            lease = read_lease(root, base)
            view = read_grant(root.resolve(), base, args.brief_slug, rows, lease, now)
        if args.verb == "classify":
            _emit(
                classify(
                    root, base, rows, args.slice_slug, args.task, args.failure_class, view
                )
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
            return EXIT_OK
        status = brief_status(read_brief_text(root.resolve(), base, args.brief_slug))
        shared = {"brief_status": status, "grant": grant_answer(view)}
        if args.verb == "status":
            _emit(
                {
                    "base": base,
                    "rows": status_entries(root.resolve(), rows),
                    "standing_orders": orders,
                    **shared,
                }
            )
        else:
            cap = int(lease["max_slices_in_flight"])
            if view is not None and view.state != GRANT_VALID:
                chosen = grant_action(view, rows)
            elif view is not None:
                slices = frozenset(view.grant.slices) if view.grant is not None else frozenset()
                chosen = decide_next(rows, min(cap, 1), granted=slices)
            elif status in RUNNABLE_STATUSES:
                chosen = decide_next(rows, cap)
            else:
                exempt = exempt_slices(root.resolve(), rows, now)
                chosen = decide_next(rows, cap, runnable=False, exempt=exempt)
            _emit(
                {
                    "schema_version": NEXT_SCHEMA_VERSION,
                    "base": base,
                    "action": with_contract_fields(chosen, base),
                    "standing_orders": orders,
                    **shared,
                }
            )
    except Refusal as exc:
        _emit(_versioned(args.verb, {"refusal": {"code": exc.code, "detail": exc.detail}}))
        return EXIT_REFUSED
    except Exception as exc:  # noqa: BLE001 - every failure still answers one JSON refusal
        # Stdout stays one JSON object; the location goes to stderr, bounded.
        sys.stderr.write(internal_error_trace(exc))
        failure = Refusal(
            CODE_INTERNAL_ERROR,
            _bounded(f"the runner failed unexpectedly: {type(exc).__name__}"),
        )
        _emit(_versioned(args.verb, {"refusal": {"code": failure.code, "detail": failure.detail}}))
        return EXIT_REFUSED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
