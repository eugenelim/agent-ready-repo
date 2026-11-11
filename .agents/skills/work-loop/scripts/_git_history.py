"""_git_history — answer "what was this path at the change base?" from committed objects.

``git_history`` runs only through a ``_supervisor_git.HardenedGit`` passed in
by the caller. No caller value (the path or the optional base) reaches a Git
launch until it has been checked against a trusted value computed from the
repository: the base must equal the change base, and the path must equal a
member of the change's path set. Nothing here starts a process itself.

The envelope's argument-vector hashes cover the Git arguments this module
passes to the helper (subcommand first), joined with NUL bytes; the helper adds
its own fixed flags in front. Base content is decoded as UTF-8 with
``errors="replace"``.

Standard library only. Python 3.11+.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

__all__ = ["CONTENT_CAP", "ENVELOPE_CAP", "GitHistoryRefused", "git_history", "supervisor_git"]

CONTENT_CAP = 256 * 1024
ENVELOPE_CAP = 1024 * 1024
COMMIT_CAP = 50
MINIMUM_GIT = (2, 44)

_SCRIPTS_DIR = Path(__file__).resolve().parent
_BASE_FORM = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
_DEFAULT_REF_FORM = re.compile(r"refs/remotes/[A-Za-z0-9_][A-Za-z0-9_./+-]*")
_FALSE_VALUES = frozenset({"false", "no", "off", "0"})

_REMEDIES = {
    "denied-ref-form": (
        "Pass --base as a full 40 or 64 digit lowercase hexadecimal commit ID, or omit it."
    ),
    "denied-artifact-path": "Ask about a changed path outside .context/.",
    "denied-object-source": (
        "Run from a repository with no alternates file, partial clone, promisor remote, "
        "or partial-clone filter."
    ),
    "denied-git-version": (
        "Use Git 2.44 or later, which honours GIT_NO_LAZY_FETCH, then retry."
    ),
    "denied-git-config": (
        "Remove the repository config entries that make Git run a program, then retry."
    ),
    "denied-no-change-base": (
        "Run `git remote set-head origin --auto` so refs/remotes/origin/HEAD exists, then retry."
    ),
    "denied-ref-outside-subject-history": (
        "Omit --base, or pass the change base this entry reports."
    ),
    "denied-path-not-in-change": (
        "Pass a path that appears in `git diff --name-only -z --no-renames <change base> HEAD`."
    ),
    "denied-git-history-unreadable": "Git did not return a usable answer; check the repository.",
}


class GitHistoryRefused(Exception):
    """The entry refused the request; *code* is the stable refusal code."""

    def __init__(self, code: str) -> None:
        self.code = code
        self.detail = _REMEDIES.get(code, "The request was refused.")
        super().__init__(code)


def _load_sibling(module_name: str, filename: str) -> ModuleType:
    """Load a sibling work-loop module by literal path under a name unique to this module."""
    path = _SCRIPTS_DIR / filename
    if not stat.S_ISREG(os.lstat(path).st_mode):
        raise RuntimeError(f"sibling module is not a regular file: {filename}")
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load sibling module: {filename}")
        module = importlib.util.module_from_spec(spec)
        # The module defines dataclasses, which look their module up by name while executing.
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


_SUPERVISOR_GIT: list[ModuleType] = []


def supervisor_git() -> ModuleType:
    """The one loaded ``_supervisor_git`` module, shared by every caller of this module."""
    if not _SUPERVISOR_GIT:
        _SUPERVISOR_GIT.append(_load_sibling("_git_history_supervisor_git", "_supervisor_git.py"))
    return _SUPERVISOR_GIT[0]


def _sha256_args(args: tuple[str, ...]) -> str:
    return hashlib.sha256("\0".join(args).encode("utf-8", "surrogateescape")).hexdigest()


def new_git(root: Path) -> Any:
    """A ``HardenedGit`` for *root* that tells Git never to fetch a missing object."""
    return supervisor_git().HardenedGit(root, no_lazy_fetch=True)


def run_environment() -> dict[str, str]:
    """The one environment every ``run`` launch of a ``new_git`` helper receives."""
    return supervisor_git().hardened_env(no_lazy_fetch=True)  # type: ignore[no-any-return]


def require_git_version(git: Any) -> None:
    """Refuse a Git older than 2.44, from the helper's own single ``version`` launch.

    The helper refuses a Git older than 2.32 itself while pinning; that is the
    same refusal here.
    """
    try:
        version = git.git_version
    except supervisor_git().SupervisorGitError as exc:
        if exc.code == "unsupported-git-version":
            raise GitHistoryRefused("denied-git-version") from exc
        raise
    if version < MINIMUM_GIT:
        raise GitHistoryRefused("denied-git-version")


def refuse_object_sources(git: Any) -> None:
    """Refuse a repository whose objects may come from outside its own object store."""
    if os.path.lexists(git.pins.common_dir / "objects" / "info" / "alternates"):
        raise GitHistoryRefused("denied-object-source")
    for entry in git.config_entries():
        parts = entry.key.split(".")
        if entry.key == "extensions.partialclone":
            raise GitHistoryRefused("denied-object-source")
        if len(parts) >= 3 and parts[0] == "remote" and parts[-1] == "partialclonefilter":
            raise GitHistoryRefused("denied-object-source")
        if (
            len(parts) >= 3
            and parts[0] == "remote"
            and parts[-1] == "promisor"
            and entry.value.strip().lower() not in _FALSE_VALUES
        ):
            raise GitHistoryRefused("denied-object-source")


def git_history(git: Any, *, base: str | None, path: str) -> dict[str, Any]:
    """The base-side facts for one changed *path*, as a JSON-ready envelope.

    Raises ``GitHistoryRefused`` for a malformed or untrusted *base*, a *path*
    that is not a member of the change's path set, or an unsafe repository.
    """
    module = supervisor_git()
    if base is not None and not _BASE_FORM.fullmatch(base):
        raise GitHistoryRefused("denied-ref-form")
    if path.split("/", 1)[0] == ".context":
        raise GitHistoryRefused("denied-artifact-path")
    require_git_version(git)
    refuse_object_sources(git)
    if module.code_running_keys(git.config_entries()):
        raise GitHistoryRefused("denied-git-config")

    sent: list[tuple[str, ...]] = []

    def run(*args: str, check: bool = True, literal: bool = False) -> bytes:
        sent.append(args)
        return git.run(*args, check=check, literal_pathspecs=literal)  # type: ignore[no-any-return]

    head = run("rev-parse", "--verify", "HEAD^{commit}").decode("ascii", "replace").strip()
    if not _BASE_FORM.fullmatch(head):
        raise GitHistoryRefused("denied-git-history-unreadable")
    # An absent or non-symbolic origin/HEAD exits non-zero; that is the answer, not an error.
    default_ref = (
        run("symbolic-ref", "-q", "refs/remotes/origin/HEAD", check=False)
        .decode("utf-8", "replace")
        .strip()
    )
    if not _DEFAULT_REF_FORM.fullmatch(default_ref):
        raise GitHistoryRefused("denied-no-change-base")
    # No merge base is a non-zero exit with empty output, which means no change base.
    change_base = (
        run("merge-base", head, default_ref, check=False).decode("ascii", "replace").strip()
    )
    if not _BASE_FORM.fullmatch(change_base):
        raise GitHistoryRefused("denied-no-change-base")
    if base is not None and base != change_base:
        raise GitHistoryRefused("denied-ref-outside-subject-history")

    listing = run("diff", "--name-only", "-z", "--no-renames", change_base, head)
    members = [m.decode("utf-8", "surrogateescape") for m in listing.split(b"\0") if m]
    member = next((m for m in members if m == path), None)
    if member is None:
        raise GitHistoryRefused("denied-path-not-in-change")

    at_base = f"{change_base}:{member}"
    # A path absent at the base makes cat-file exit non-zero; that means "not a blob there".
    kind = run("cat-file", "-t", at_base, check=False).strip()
    present = kind == b"blob"
    envelope: dict[str, Any] = {}
    if present:
        size = int(run("cat-file", "-s", at_base).strip())
        blob_id = run("rev-parse", "--verify", at_base).decode("ascii", "replace").strip()
        envelope["blob_id"] = blob_id
        envelope["size"] = size
        if size <= CONTENT_CAP:
            envelope["content"] = run("show", at_base).decode("utf-8", "replace")
            envelope["truncated"] = False
        else:
            envelope["truncated"] = True
    history = (
        run("log", "--no-show-signature", "--format=%H", "--max-count=51",
            f"{change_base}..{head}", "--", member, literal=True)
        .decode("ascii", "replace")
        .split()
    )

    envelope.update({
        "gate_id": "git-history",
        "argv_sha256": [_sha256_args(args) for args in sent],
        "environment_sha256": hashlib.sha256(
            json.dumps(
                run_environment(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
            ).encode("ascii")
        ).hexdigest(),
        "cwd": str(git.pins.root),
        "subject_commit": head,
        "change_base": change_base,
        "isolation": "git-object-store",
        "network": "no-remote-objects",
        "timeout_s": module.GIT_TIMEOUT_S,
        "exit_status": 0,
        "path": member,
        "present_at_base": present,
        "commits": history[:COMMIT_CAP],
        "log_truncated": len(history) > COMMIT_CAP,
    })
    if len(_serialize(envelope)) > ENVELOPE_CAP and "content" in envelope:
        del envelope["content"]
        envelope["truncated"] = True
    if len(_serialize(envelope)) > ENVELOPE_CAP:
        raise GitHistoryRefused("denied-git-history-unreadable")
    return envelope


def _serialize(envelope: dict[str, Any]) -> bytes:
    return json.dumps(envelope).encode("utf-8")
