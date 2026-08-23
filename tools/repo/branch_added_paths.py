"""Which paths did *this branch* add?

A check that asks "did this change create a forbidden artifact" needs the set of paths
the branch added. The obvious implementation — diff against a commit hash pinned when the
work started — answers a different question: "what has *anyone* added since that commit".
The two agree only until someone else merges.

They stopped agreeing in `agent-ready-repo`. An RFC-0088 control pinned its base and used
that base for two different checks. One compares the text of a single governed document,
where pinning is right: only that RFC's own rounds touch the file, and a moving ref would
fabricate phantom hunks. The other asked what the round created. When an unrelated pull
request merged an ADR, the second check reported that ADR as the round's own work, and
failed on a clean checkout of the default branch with no round work in the tree at all.
It would have stayed red for every later round.

The branch's own additions are the paths added since its **merge-base with the upstream
default branch**. Unlike the pinned-document case, upstream movement makes this *more*
accurate rather than less: unrebased, the merge-base stays at the divergence point;
rebased, it follows to the new tip. Either way the answer is the branch's own additions.

Nothing here knows about RFC-0088, ADRs, or any particular forbidden shape. Callers
supply the shapes; this module supplies the scope.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

#: Refs tried, in order, when resolving the upstream default branch.
DEFAULT_UPSTREAM_REFS: tuple[str, ...] = ("origin/main", "origin/HEAD")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


def upstream_merge_base(
    repo: Path,
    fallback: str | None = None,
    upstream_refs: tuple[str, ...] = DEFAULT_UPSTREAM_REFS,
) -> tuple[str, str]:
    """Resolve the base for "what did this branch add", with a named provenance.

    Returns ``(base, how)``. ``how`` is a short human-readable description of where the
    base came from, and callers are expected to print it: a fallback that silently
    reinstated a pinned base would restore the defect on exactly the checkouts least able
    to notice it.

    Raises ``RuntimeError`` when no ref resolves and no ``fallback`` is supplied, rather
    than returning a base that means something other than what the caller asked for.
    """
    for ref in upstream_refs:
        if not ref:
            continue
        probe = _git(repo, "merge-base", "HEAD", ref)
        if probe.returncode == 0 and probe.stdout.strip():
            return probe.stdout.strip(), f"merge-base with {ref}"
    if fallback is None:
        raise RuntimeError(
            "no upstream ref resolved and no fallback supplied, so the branch's own "
            f"additions cannot be scoped (tried: {', '.join(r for r in upstream_refs if r)})"
        )
    return fallback, f"fallback base {fallback} (NO UPSTREAM REF RESOLVED)"


def added_paths(repo: Path, base: str) -> list[str]:
    """Repository-relative paths added between ``base`` and the **working tree**.

    Working tree rather than ``base..HEAD``: comparing commits alone misses a
    staged-but-uncommitted file entirely, which is how a decoy artifact once sat in a tree
    that a control reported clean. Untracked paths are collected separately because
    ``git diff`` does not see them at all.

    Raises ``RuntimeError`` on a git failure instead of returning an empty list — an
    absence check whose scan silently returned nothing would pass for the worst reason.
    """
    added = _git(repo, "diff", "--name-only", "--diff-filter=A", base)
    untracked = _git(repo, "ls-files", "--others", "--exclude-standard")
    if added.returncode != 0 or untracked.returncode != 0:
        detail = f"{added.stderr.strip()} {untracked.stderr.strip()}".strip()
        raise RuntimeError(f"cannot list paths added against {base}: {detail}")
    return sorted({p for p in (added.stdout + untracked.stdout).split() if p})
