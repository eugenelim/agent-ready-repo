#!/usr/bin/env python3
"""Refuse an editable install of this repo's packages that points elsewhere.

An editable install is global to the interpreter. Nine worktrees share one here,
so `pip install -e packages/agentbundle` from worktree A rewrites what every
other worktree's *subprocesses* import — and rewriting it while a peer's gates
are running is what kills them mid-flight. Almost nothing here needs that
install: `Makefile`'s PYTHONPATH and `pyproject.toml`'s pytest `pythonpath`
supply both packages from source, and `python3 -m agentbundle` runs the CLI with
no install at all. The exception is a gate whose child runs under `-I`, which
ignores PYTHONPATH and resolves only site-packages —
`tools/test_marketplace_envelope_parity.py` is one. That wants a *plain*
install, never an editable: a snapshot in site-packages tracks no worktree, so
it cannot move this failure onto a peer.

What this refuses is narrow and unambiguous:

    an EDITABLE install of `agentbundle` or `credbroker` whose recorded source
    directory is not this worktree

A regular (wheel) install never trips it — that is a deliberate, legitimate
setup, and it is how the `agentbundle` console script exists. An editable
install pointing at *this* worktree does not trip it either: it leaks nothing
into a peer that this worktree does not already own.

Standard-library only, and it reads PEP 610 `direct_url.json` rather than
importing either package: the whole point is to describe installs without
loading code from them.
"""

from __future__ import annotations

import argparse
import importlib.metadata as md
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlparse

PACKAGES = ("agentbundle", "credbroker")


@dataclass(frozen=True)
class Verdict:
    """One package's install shape, as recorded rather than inferred."""

    name: str
    kind: str  # absent | regular | editable-here | editable-elsewhere | unreadable
    source: Path | None = None
    detail: str = ""


def _resolve(path: Path) -> Path | None:
    try:
        return path.resolve()
    except (OSError, RuntimeError, ValueError):
        return None


def worktree_root(start: Path) -> Path | None:
    """The nearest ancestor holding a `.git` entry.

    `.git` is a *file* in a linked worktree (it carries a `gitdir:` pointer), so
    presence is tested, never directory-ness.
    """
    here = _resolve(start)
    if here is None:
        return None
    for candidate in (here, *here.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _editable_source(raw: str) -> tuple[Path | None, str]:
    """Parse a PEP 610 record into its editable source directory, if any."""
    try:
        info = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, "direct_url.json is not valid JSON"
    if not isinstance(info, dict):
        return None, "direct_url.json is not an object"
    dir_info = info.get("dir_info")
    if not isinstance(dir_info, dict) or dir_info.get("editable") is not True:
        # A PEP 610 record without `dir_info.editable == true` is a non-editable
        # direct install (a local wheel, a VCS pin). Not the harm state.
        return None, ""
    url = info.get("url")
    if not isinstance(url, str):
        return None, "direct_url.json records no url"
    parsed = urlparse(url)
    if parsed.scheme != "file":
        return None, f"unsupported url scheme {parsed.scheme!r}"
    if parsed.netloc not in ("", "localhost"):
        return None, f"refusing a non-local url host {parsed.netloc!r}"
    raw_path = parsed.path
    decoded = unquote(raw_path)
    if decoded.count("/") != raw_path.count("/"):
        return None, "url path smuggles an encoded separator"
    if not decoded.startswith("/"):
        return None, f"url path is not absolute: {decoded!r}"
    return _resolve(Path(decoded)), ""


def _canon(value: str | None) -> str:
    return (value or "").strip().lower().replace("_", "-")


def _contains(root: Path, candidate: Path) -> bool:
    """Component-wise containment, case-folded.

    Two independent traps. Containment is never a string prefix: `<root>-peer`
    starts with `<root>` but is a different worktree, so the comparison walks
    path components. And case is folded explicitly, because `Path.resolve()`
    does not normalise case on a case-insensitive volume and
    `os.path.normcase` is a no-op everywhere except Windows — so a record
    naming `/users/...` for `/Users/...` describes THIS worktree and would
    otherwise read as elsewhere, a permanent false alarm on a correct setup.

    Folding always, rather than probing the filesystem's case sensitivity, is
    deliberate: on a case-sensitive volume two worktrees differing only by case
    would compare equal, which costs a missed detection rather than a false
    alarm. Given the constraint that this must never fire on a legitimate
    setup, that is the right direction to be wrong in.
    """
    r = [part.casefold() for part in root.parts]
    c = [part.casefold() for part in candidate.parts]
    return c[: len(r)] == r


def _installed_records(name: str, root: Path) -> tuple[list[md.Distribution], str]:
    """Every distribution named `name` whose metadata lives OUTSIDE this worktree.

    Discovery cannot use `md.distribution(name)`: that returns the first match on
    `sys.path`, and `Makefile:7` puts `packages/agentbundle` first for every make
    target — so the in-worktree `*.egg-info` (expected; see the spec's Assumption
    2) would answer instead of the real install, and an egg-info carries no
    `direct_url.json`, making every verdict "regular". Measured: the guard was
    blind in exactly the invocation that registers it.

    Source-tree metadata is therefore skipped by location, which also makes this
    independent of `site` module quirks and of how the caller set PYTHONPATH.
    """
    found: list[md.Distribution] = []
    try:
        candidates = list(md.distributions())
    except Exception as error:  # noqa: BLE001 - a broken environment must not crash a gate
        return [], type(error).__name__
    for dist in candidates:
        try:
            if _canon(dist.metadata["Name"]) != _canon(name):
                continue
            location = _resolve(Path(str(dist.locate_file(""))))
        except Exception:  # noqa: BLE001, S112 - skip an unreadable sibling
            continue
        if location is None or _contains(root, location):
            continue  # source-tree metadata, not an install
        found.append(dist)
    return found, ""


def inspect(name: str, root: Path) -> Verdict:
    """Classify one package's install without importing it."""
    dists, error = _installed_records(name, root)
    if error:
        return Verdict(name, "unreadable", detail=error)
    if not dists:
        return Verdict(name, "absent")

    for dist in dists:
        raw = dist.read_text("direct_url.json")
        if raw is None:
            # `read_text` suppresses OSError internally, so an unreadable or
            # directory-shaped record is indistinguishable from an absent one
            # here. Probe the path so the reported-not-failed branch is real.
            recorded = Path(str(dist.locate_file(""))) / "direct_url.json"
            if recorded.exists():
                return Verdict(name, "unreadable", detail="direct_url.json unreadable")
            continue  # no PEP 610 record: a wheel install, deliberate
        if not raw.strip():
            return Verdict(name, "unreadable", detail="direct_url.json is empty")

        source, detail = _editable_source(raw)
        if detail:
            return Verdict(name, "unreadable", detail=detail)
        if source is None:
            continue  # a non-editable direct install
        if _contains(root, source):
            return Verdict(name, "editable-here", source=source)
        return Verdict(name, "editable-elsewhere", source=source)
    return Verdict(name, "regular")


def _second_repair(name: str, root: Path) -> list[str]:
    """The keep-the-install option, described accurately per package.

    `agentbundle` ships a console script; `credbroker` is a pure library with no
    `[project.scripts]` and no `__main__`, so an install buys nothing there and
    uninstall is the only honest repair.
    """
    if name != "agentbundle":
        return [
            f"      ({name} is a library with no console script — an install buys",
            "       nothing here, so the uninstall above is the only repair.)",
        ]
    return [
        f"      python3 -m pip install {root}/packages/{name}",
        "        Note the missing `-e`. A plain install copies a snapshot into",
        "        site-packages, so it tracks no worktree and cannot move this",
        "        failure onto a peer — which an editable pointing here would do.",
        "        `python3 -m agentbundle ...` already runs from source without any",
        "        install; take this one for the console script on PATH, or when a",
        "        gate needs the package *installed* rather than importable: the",
        "        child in `tools/test_marketplace_envelope_parity.py` runs under",
        "        `-I`, so it ignores PYTHONPATH and sees only site-packages.",
    ]


def _render(verdict: Verdict, root: Path) -> list[str]:
    """The repair instruction. A guard that only says 'no' is half a guard."""
    return [
        f"{verdict.name}: an EDITABLE install points outside this worktree.",
        f"    recorded source  {verdict.source}",
        f"    this worktree    {root}",
        "",
        "    Every worktree's subprocesses import that directory, so this one is",
        "    testing another checkout's code — and re-pointing it while a peer's",
        "    gates run is what kills them mid-run.",
        "",
        "    You may not have caused this. `pip install -e` is global, so",
        "    whichever worktree bootstrapped last owns the pointer and every other",
        "    worktree inherits it.",
        "",
        "    To repair, preferring the first:",
        f"      python3 -m pip uninstall -y {verdict.name}",
        "        Fixes this for EVERY worktree at once, permanently. Almost",
        "        nothing here needs an install: the gates and suites resolve both",
        "        packages from source. The exception is a gate whose child runs",
        "        under `-I` and therefore cannot see PYTHONPATH; if uninstalling",
        "        reddens one, take the plain install below rather than an",
        "        editable.",
        *_second_repair(verdict.name, root),
    ]


def check(directory: Path) -> tuple[int, list[str]]:
    """Return an exit code and the lines to print."""
    root = worktree_root(directory)
    if root is None:
        return 0, [f"editable-install-guard: no worktree root at or above {directory}; skipped"]

    lines: list[str] = []
    offenders = 0
    for name in PACKAGES:
        verdict = inspect(name, root)
        if verdict.kind == "editable-elsewhere":
            offenders += 1
            lines.extend(_render(verdict, root))
        elif verdict.kind == "unreadable":
            # Report, never fail: an unparseable record is not the harm state.
            lines.append(
                f"editable-install-guard: {name}: install record unreadable"
                f" ({verdict.detail}); not treated as a failure"
            )
    return (1 if offenders else 0), lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--directory", default=".", help="worktree to check (default: cwd)")
    args = parser.parse_args(argv)

    code, lines = check(Path(args.directory))
    if lines:
        stream = sys.stderr if code else sys.stdout
        print("\n".join(lines), file=stream)
    if code:
        print(
            "\neditable-install-guard: FAILED — see ADR-0094 for why this repository"
            " imports both packages from source.",
            file=sys.stderr,
        )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
