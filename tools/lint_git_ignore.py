#!/usr/bin/env python3
"""Batched `git check-ignore` resolution for repository lint tooling.

This is the **only** approved home for constructing a `git check-ignore`
subprocess in production lint code; `tools/test-lint-no-direct-check-ignore.py`
enforces that. A lint that needs to know which of many paths Git ignores calls
`git_ignored_paths` once with the whole candidate set.

Repo-only by design. Portable `agentbundle` code must not import it, and shipped
pack/skill content must not depend on it — measurement found no caller on either
side of those boundaries that queries Git ignore at all, so a second
implementation would have no consumer.

Four decisions here are not obvious, and each was made against a probe rather
than a guess:

**Candidates go over stdin, NUL-delimited, as bytes.** Not argv. A path is
attacker-shaped data as far as an option parser is concerned, and NUL framing is
the only delimiter a filename cannot contain. Bytes (via ``os.fsencode``) rather
than ``str`` because a filename need not be valid UTF-8 on Linux, and
``str.encode`` on a surrogate-escaped name raises ``UnicodeEncodeError`` — a
``ValueError``, so neither ``OSError`` nor ``SubprocessError`` handling would
catch it.

**A non-0/1 exit is a hard error, never a policy outcome.** Git exits 128 for the
*whole* invocation on one unusable path — outside the repository, inside a nested
Git root, or carrying pathspec magic this subcommand rejects — while still
echoing the candidates it processed before reaching it. That partial result is
the trap: discarding it silently loses ignore information, and trusting it
silently under-reports. Batching makes the blast radius the entire set, where a
per-path call only ever lost one path, so the condition is raised rather than
absorbed.

**Containment is lexical, never ``resolve()``.** Callers own symlink handling and
owe a symlink *finding*; resolving here would silently relocate a candidate out
of the root and refuse it for the wrong reason.

**Precondition: prune links before batching.** Git will not answer for a path
whose ancestor chain crosses a symlink — it exits 128 with
``fatal: pathspec '…' is beyond a symbolic link`` — so such a candidate raises
:class:`GitIgnoreError` naming the path. This is a documented precondition rather
than a hidden landmine: both current callers already prune links while collecting
candidates, and detecting the condition here would mean an ``lstat`` walk per
candidate, reintroducing the per-path filesystem work this module exists to
remove. The error message says what to do.

**Degradation is representable.** "Git ran and nothing matched" and "Git never
answered" are different facts, and callers must be able to tell them apart. The
boundary lint *subtracts* the ignored set and two of its findings fire on the
emptiness of what remains, so an unresolved layer silently converts failures
into passes. Hence ``degraded`` and ``reason`` — the caller decides what to do,
this module never prints.
"""

from __future__ import annotations

import base64
import enum
import os
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

__all__ = [
    "DegradationReason",
    "GitIgnoreError",
    "IgnoreResolution",
    "MissingGitPolicy",
    "decode_stream",
    "encode_stream",
    "git_ignored_paths",
    "hermetic_git_env",
]

# Git environment variables that redirect resolution somewhere other than the
# root we were handed. Git sets several of these for hook processes, and these
# lints run from a pre-PR hook, so a hook-invoked run would otherwise resolve
# ignores against the real index while claiming to answer for a fixture.
_LEAKING_GIT_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_CEILING_DIRECTORIES",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_CONFIG",
    # The one channel that survives GIT_CONFIG_NOSYSTEM plus redirected global
    # and system config files, and the only one that leaks *silently*. Verified:
    # with GIT_CONFIG_COUNT=1 / KEY_0=core.excludesFile / VALUE_0=<file>,
    # `check-ignore --stdin -z` reports extra paths as ignored and exits 0. The
    # pathspec variables below fail closed instead (exit 128 -> GitIgnoreError),
    # which is why they are far less dangerous — but they are dropped too.
    "GIT_CONFIG_COUNT",
    "GIT_GLOB_PATHSPECS",
    "GIT_ICASE_PATHSPECS",
    "GIT_LITERAL_PATHSPECS",
    "GIT_NOGLOB_PATHSPECS",
)


class MissingGitPolicy(enum.Enum):
    """What to do when Git cannot answer at all.

    Distinct from "Git answered, nothing is ignored". Required at every call
    site — no default — so each caller states its posture in source rather than
    inheriting one.
    """

    FAIL_OPEN = "fail-open"
    """Report nothing as ignored, and set ``degraded``. The caller decides."""

    RAISE = "raise"
    """Propagate. For a caller whose result would be *unsound* — not merely
    noisier — without a real answer: one reporting only ignored files, say,
    where an empty set is a false clean."""


class DegradationReason(enum.Enum):
    """Why Git failed to answer. Lets a caller name the cause accurately."""

    GIT_ABSENT = "git-absent"
    TIMED_OUT = "timed-out"
    EXECUTION_ERROR = "execution-error"


class GitIgnoreError(RuntimeError):
    """Git rejected the batch. Not a degradation — the answer is unusable.

    Raised for any exit code other than 0 or 1, which in practice means Git
    refused a candidate and returned a partial echo.
    """


@dataclass(frozen=True)
class IgnoreResolution:
    """Which candidates Git ignores, and whether it actually answered."""

    ignored: tuple[Path, ...]
    """The ignored subset, deterministically sorted, holding **the caller's own
    path objects** so membership can be tested against what was passed in."""

    degraded: bool = False
    """True when Git never answered. ``ignored`` is empty and means nothing."""

    reason: DegradationReason | None = None
    detail: str | None = None
    """Diagnostic text, relativized and length-bounded. Never printed here."""


_DETAIL_LIMIT = 2000


def hermetic_git_env(base: Mapping[str, str]) -> dict[str, str]:
    """A Git environment that cannot inherit host ignore configuration.

    A `git init`-ed directory still honours ``core.excludesFile`` from the user
    and system config, and still respects an ambient ``GIT_DIR``. Both would
    silently change which paths come back ignored — and because the boundary
    lint subtracts that set, a host ignore rule matching a fixture path can turn
    a genuine failure into a pass.
    """
    env = dict(base)
    for name in _LEAKING_GIT_VARS:
        env.pop(name, None)
    # GIT_CONFIG_COUNT indexes GIT_CONFIG_KEY_n / GIT_CONFIG_VALUE_n pairs;
    # dropping the count alone would leave them addressable if a later git
    # learned to infer it, so remove the whole family.
    for name in [k for k in env
                 if k.startswith(("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_"))]:
        env.pop(name, None)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    # os.devnull is an empty, always-readable config on every supported host.
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return env


def encode_stream(raw: bytes) -> str:
    """Encode a captured stream for JSON storage without losing a byte."""
    return base64.b64encode(raw).decode("ascii")


def decode_stream(encoded: str) -> bytes:
    """Inverse of :func:`encode_stream`."""
    return base64.b64decode(encoded.encode("ascii"))


def _relative_posix(repo_root: Path, candidate: Path) -> str:
    """The candidate as a root-relative POSIX path, decided lexically.

    Deliberately no ``resolve()``: see the module docstring. ``normpath``
    collapses ``.`` and redundant separators but does not consult the
    filesystem, so a path reachable through a symlink stays inside the root and
    reaches Git — where the caller's symlink handling can see it.
    """
    root_text = os.path.normpath(str(repo_root))
    # `Path.__truediv__` joins lexically and, like os.path.join, lets an absolute
    # candidate replace the root — which is exactly what must then fail the
    # containment check below. `normpath` collapses `..` without touching disk.
    raw = os.path.normpath(Path(root_text) / candidate)
    try:
        relative = Path(raw).relative_to(root_text)
    except ValueError:
        raise ValueError(
            f"candidate {candidate.name!r} lies outside the repository root "
            f"({candidate} is not under {repo_root}); a candidate outside the "
            f"root makes git exit 128 with a partial result, so it is refused "
            f"here rather than silently degrading the whole batch"
        ) from None
    text = PurePosixPath(*relative.parts).as_posix() if relative.parts else "."
    if text.startswith(":"):
        # `check-ignore --stdin` parses pathspec magic: `:!x`, `:(glob)x` and
        # friends exit 128 with a partial echo. `:(literal)` is itself rejected
        # by this subcommand, so escaping is not available — refuse instead.
        raise ValueError(
            f"candidate {candidate.name!r} begins with ':' after "
            f"root-relativisation, which git parses as pathspec magic and "
            f"rejects with exit 128; this subcommand does not accept a "
            f"':(literal)' prefix, so such a candidate cannot be batched"
        )
    return text


def _bound_detail(repo_root: Path, text: str) -> str:
    """Redact and bound diagnostic text before a caller can print or record it.

    Git's fatal messages embed absolute paths, and this text reaches printed
    diagnostics. Two substitutions are possible and both matter: the repository
    root (so the message is portable) and the user's home directory (a
    user-specific filesystem path, which `AGENTS.md` § Privacy forbids in any git
    artifact).

    Deliberately *not* claimed: that no absolute path survives. Git may name a
    path we know nothing about, and pretending to scrub it would be an overclaim.
    What keeps such a message out of a committed golden baseline is that a
    non-0/1 exit raises instead of being captured.
    """
    cleaned = text.strip()
    for original, placeholder in (
        (os.path.normpath(str(repo_root)), "<root>"),
        (str(repo_root), "<root>"),
        (os.path.normpath(str(Path.home())), "<home>"),
    ):
        if original and original not in {os.sep, ""}:
            cleaned = cleaned.replace(original, placeholder)
    if len(cleaned) > _DETAIL_LIMIT:
        cleaned = cleaned[:_DETAIL_LIMIT] + "… (truncated)"
    return cleaned


def git_ignored_paths(
    repo_root: Path,
    candidates: Iterable[Path],
    *,
    missing_git_policy: MissingGitPolicy,
    timeout: float,
) -> IgnoreResolution:
    """Resolve which of *candidates* Git ignores, in one subprocess.

    Args:
        repo_root: the Git worktree the candidates belong to. Used verbatim as
            the subprocess working directory and as the lexical containment
            root; canonicalise it once before calling if that matters to you.
        candidates: paths either absolute under *repo_root* or relative to it.
            Duplicates are collapsed. An empty iterable launches no subprocess.
        missing_git_policy: what to do when Git cannot answer. Required.
        timeout: seconds, covering the whole batch. Required — the batch is as
            large as the caller's candidate set, so the bound is a caller
            decision, and because callers treat degradation as fatal an
            under-sized value turns a loaded machine into a red gate.

    Returns:
        An :class:`IgnoreResolution` whose ``ignored`` tuple holds the caller's
        own path objects, sorted.

    Raises:
        ValueError: a candidate lies outside *repo_root*, or would be parsed as
            pathspec magic.
        GitIgnoreError: Git exited with something other than 0 or 1.
        Exception: whatever Git raised, when the policy is
            :attr:`MissingGitPolicy.RAISE`.
    """
    # Preserve first-seen order into the payload for a stable, diffable request,
    # and keep every original object so the answer is keyed to what was passed.
    by_relative: dict[str, Path] = {}
    for candidate in candidates:
        relative = _relative_posix(repo_root, candidate)
        by_relative.setdefault(relative, candidate)

    if not by_relative:
        return IgnoreResolution(ignored=())

    payload = b"\0".join(os.fsencode(name) for name in by_relative) + b"\0"

    try:
        completed = subprocess.run(  # noqa: S603 — argv list, no shell
            ["git", "check-ignore", "--stdin", "-z"],
            input=payload,
            cwd=str(repo_root),
            capture_output=True,
            check=False,
            timeout=timeout,
            env=hermetic_git_env(os.environ),
        )
    except FileNotFoundError as exc:
        return _degrade(missing_git_policy, DegradationReason.GIT_ABSENT,
                        _bound_detail(repo_root,
                                      "git executable not found on PATH"), exc)
    except subprocess.TimeoutExpired as exc:
        return _degrade(missing_git_policy, DegradationReason.TIMED_OUT,
                        _bound_detail(repo_root,
                                      f"git check-ignore exceeded {timeout}s "
                                      f"for {len(by_relative)} candidate(s)"),
                        exc)
    except OSError as exc:
        # `{exc}` interpolates an absolute path for e.g. a bad cwd
        # (NotADirectoryError names it), so this must be redacted like any other
        # diagnostic that reaches operator output or a committed baseline.
        return _degrade(missing_git_policy, DegradationReason.EXECUTION_ERROR,
                        _bound_detail(repo_root,
                                      f"git could not be executed: {exc}"), exc)

    # 0 = at least one ignored, 1 = none ignored. Both are real answers.
    if completed.returncode not in (0, 1):
        said = _bound_detail(
            repo_root, completed.stderr.decode("utf-8", "replace")
        )
        hint = ""
        if "beyond a symbolic link" in said:
            hint = (
                " A candidate's ancestor chain crosses a symlink; git cannot "
                "answer for it. Prune links while collecting candidates — this "
                "module deliberately does not lstat every path to find out."
            )
        raise GitIgnoreError(
            f"git check-ignore exited {completed.returncode} for "
            f"{len(by_relative)} candidate(s); the result is partial and cannot "
            f"be trusted. git said: {said}{hint}"
        )

    ignored = [
        by_relative[name]
        for name in (
            os.fsdecode(chunk) for chunk in completed.stdout.split(b"\0") if chunk
        )
        if name in by_relative
    ]
    return IgnoreResolution(ignored=tuple(sorted(ignored, key=str)))


def _degrade(
    policy: MissingGitPolicy,
    reason: DegradationReason,
    detail: str,
    exc: BaseException,
) -> IgnoreResolution:
    """Apply the caller's missing-Git policy to a Git that never answered."""
    if policy is MissingGitPolicy.RAISE:
        raise exc
    return IgnoreResolution(
        ignored=(), degraded=True, reason=reason, detail=detail,
    )
