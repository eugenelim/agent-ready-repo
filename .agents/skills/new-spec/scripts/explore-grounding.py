#!/usr/bin/env python3
"""Answer "what already governs these paths?" before a spec or plan is authored.

Five probes, seeded by the paths a change will touch. The cost is bounded by the
seed set and its references rather than by the repository, which is the whole
difference from a repository map: a map's cost scales with the repository and its
token budget truncates exactly the rare edge you needed.

  scoped rules   which governing files sit above a seed, root-ward
  path refs      which files name a seed path
  phrase pins    which files quote a distinctive line from a seed file
  gates          which runners would execute a seed path
  co-change      which files historically move with a seed path

Three rules hold for every probe.

**It reports; it never decides.** The exit status is success unless the tool
itself failed. Blocking on a heuristic is a different mechanism with a different
failure mode, and a worse one.

**Three outcomes, always distinguishable:** found, none found, and input
unavailable. A probe that returns empty when its input is missing is
indistinguishable from a clean result -- and the co-change probe has no fallback,
so on a repository without history it must say so rather than say nothing.

**Nothing about this repository is hardcoded.** Top-level names and the tracked
set are derived at run time. A shipped allowlist of directories fails on an
adopter's first run by finding nothing, silently, forever.

Usage:
    python explore-grounding.py --root . <seed-path> [<seed-path> ...]
"""

from __future__ import annotations

import argparse
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Tier-2 defaults: what a runner looks like. Open-ended by nature -- an adopter
# may use something absent here -- so the report names what it considered, and
# `--runner-glob` overrides. Silence about the candidate set is what turns a
# heuristic into a false clean.
RUNNER_GLOBS = (
    "Makefile", "makefile", "*.mk", "Justfile", "justfile",
    "Taskfile.yml", "Taskfile.yaml", "noxfile.py", "tox.ini", "package.json",
    ".github/workflows/*.yml", ".github/workflows/*.yaml",
    ".gitlab-ci.yml", ".circleci/config.yml", "azure-pipelines.yml",
)

# A phrase found in more than this many files is shipped boilerplate, not a pin
# on the seed. Uncalibrated, this probe returned every skill in the catalogue.
BOILERPLATE_CUTOFF = 3
# Minimum co-occurrences before a partner is reported, and the commit size above
# which a commit is a sweep rather than a coupling. Both from the co-change
# literature; both repository-dependent, which is why they are flags.
CO_CHANGE_MIN = 3
SWEEP_COMMIT_SIZE = 30
# Per-probe result cap. Beyond it the remainder is counted, never listed: a probe
# that floods its caller pushes the real finding below the fold.
RESULT_CAP = 12

TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".yml", ".yaml", ".cfg", ".ini", ".txt", ".sh", ""}
MAX_READ_BYTES = 2_000_000


def _git(root: Path, *args: str) -> list[str] | None:
    """Run a git query. None means git could not answer, which is not "empty"."""
    try:
        done = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, check=False, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.split("\n") if done.returncode == 0 else None


def top_levels(root: Path) -> tuple[str, ...]:
    """The repository's own top-level directories, derived rather than declared."""
    tracked = _git(root, "ls-tree", "-d", "--name-only", "HEAD")
    names = [n for n in (tracked or []) if n]
    if not names:
        names = [d.name for d in root.iterdir() if d.is_dir() and d.name != ".git"]
    return tuple(sorted(names))


def confined_files(root: Path, tracked: set[str] | None) -> list[Path]:
    """Every readable regular file under root, symlinks refused rather than followed."""
    if tracked:
        out = []
        for rel in sorted(tracked):
            path = root / rel
            try:
                info = path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode) and path.suffix.lower() in TEXT_SUFFIXES:
                out.append(path)
        return out
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git" and not Path(dirpath, d).is_symlink()]
        for name in filenames:
            path = Path(dirpath, name)
            try:
                info = path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode) and path.suffix.lower() in TEXT_SUFFIXES:
                out.append(path)
    return out


def _read(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_READ_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def scoped_rules(root: Path, seed: str, filename: str) -> list[str]:
    """Every governing file from the seed's own directory root-ward, in order.

    The walk is the point. A nested file does not replace the one above it, so
    stopping at the first hit skips the rest silently.
    """
    found, here = [], (root / seed).parent
    while True:
        candidate = here / filename
        if candidate.is_file():
            found.append(candidate.relative_to(root).as_posix())
        if here == root:
            break
        here = here.parent
    return found


def distinctive_lines(root: Path, seed: str, limit: int = 40) -> list[str]:
    """Prose lines long enough to be distinctive, sampled across a seed file."""
    path = root / seed
    if not path.is_file() or path.suffix != ".md":
        return []
    lines = [
        line.strip() for line in _read(path).splitlines()
        if 60 <= len(line.strip()) <= 140 and line.strip()[:1].isalpha()
    ]
    step = max(1, len(lines) // limit)
    return lines[::step][:limit]


def runner_files(root: Path, globs: tuple[str, ...]) -> list[Path]:
    out: list[Path] = []
    for pattern in globs:
        out.extend(p for p in root.glob(pattern) if p.is_file())
    return sorted(set(out))


def co_change(root: Path, seeds: list[str]) -> tuple[str, list[tuple[str, int, float]]]:
    """Files that historically move with the seeds. ("unavailable", []) without history.

    Three calibrations, all from the co-change literature and all load-bearing:
    a commit touching more than `SWEEP_COMMIT_SIZE` files is a formatting sweep
    or a dependency bump rather than a coupling; a partner needs
    `CO_CHANGE_MIN` co-occurrences; and the reported figure is a confidence
    ratio, because a high raw count against a file that changes constantly means
    nothing.
    """
    shas = _git(root, "log", "--format=%H", "-n", "400", "--", *seeds)
    if shas is None:
        return "unavailable", []
    shas = [s for s in shas if s]
    if not shas:
        return "none", []
    partners: Counter[str] = Counter()
    for sha in shas:
        files = _git(root, "show", "--name-only", "--format=", "--no-renames", sha)
        if files is None:
            continue
        touched = {f for f in files if f}
        if len(touched) > SWEEP_COMMIT_SIZE:
            continue
        partners.update(touched - set(seeds))
    ranked = [
        (name, count, count / len(shas))
        for name, count in partners.most_common()
        if count >= CO_CHANGE_MIN
    ]
    return ("found" if ranked else "none"), ranked


def _emit(label: str, status: str, rows: list[str], cap: int) -> None:
    if status == "unavailable":
        print(f"  {label:<14} unavailable — input missing, not a clean result")
        return
    if not rows:
        print(f"  {label:<14} none found")
        return
    print(f"  {label:<14} {len(rows)}")
    for row in rows[:cap]:
        print(f"      {row}")
    if len(rows) > cap:
        print(f"      … and {len(rows) - cap} more (capped at {cap})")


def explore(root: Path, seeds: list[str], guidance: str, globs: tuple[str, ...], cap: int) -> None:
    tracked_raw = _git(root, "ls-files")
    tracked = {t for t in tracked_raw if t} if tracked_raw is not None else None
    tops = top_levels(root)
    files = confined_files(root, tracked)
    runners = runner_files(root, globs)

    print(f"seeds: {len(seeds)}   top-levels derived: {len(tops)}   "
          f"files scanned: {len(files)}   runner candidates: {len(runners)}")
    if tracked is None:
        print("note: git unavailable — tracked-set and co-change probes degrade; "
              "ignored files are not excluded")

    phrases = {s: distinctive_lines(root, s) for s in seeds}
    refs: dict[str, list[str]] = {s: [] for s in seeds}
    hits: dict[tuple[str, str], set[str]] = {}
    gates: dict[str, list[str]] = {s: [] for s in seeds}

    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel in seeds:
            continue
        text = _read(path)
        if not text:
            continue
        for seed in seeds:
            if seed in text:
                refs[seed].append(rel)
                if path in runners:
                    gates[seed].append(rel)
            for phrase in phrases.get(seed, ()):
                if phrase in text:
                    hits.setdefault((seed, phrase), set()).add(rel)

    for seed in seeds:
        # A phrase in many files is the shipped boilerplate every sibling carries.
        pins = sorted({
            rel for (s, _), where in hits.items()
            if s == seed and len(where) <= BOILERPLATE_CUTOFF
            for rel in where
        })
        print(f"\n=== {seed}")
        rules = scoped_rules(root, seed, guidance)
        _emit("scoped rules", "found" if rules else "none", rules, cap)
        _emit("path refs", "found" if refs[seed] else "none", sorted(refs[seed]), cap)
        _emit("phrase pins", "found" if pins else "none", pins, cap)
        if gates[seed]:
            _emit("gates", "found", sorted(gates[seed]), cap)
        else:
            print(f"  {'gates':<14} UNREACHED — no runner names this path "
                  f"(considered {len(runners)} runner file(s))")

    status, ranked = co_change(root, seeds)
    print(f"\n=== co-change over all {len(seeds)} seed(s)")
    _emit("partners", status,
          [f"{name}   {count} commits, confidence {ratio:.2f}" for name, count, ratio in ranked],
          cap)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--guidance-file", default="AGENTS.md")
    parser.add_argument("--runner-glob", action="append", default=None)
    parser.add_argument("--cap", type=int, default=RESULT_CAP)
    parser.add_argument("seed", nargs="+")
    args = parser.parse_args(argv)

    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    root = args.root.resolve()
    seeds = []
    for raw in args.seed:
        candidate = (root / raw).resolve()
        if root != candidate and root not in candidate.parents:
            print(f"explore-grounding: refusing seed outside root: {raw}")
            return 2
        seeds.append(candidate.relative_to(root).as_posix())

    explore(root, seeds, args.guidance_file,
            tuple(args.runner_glob) if args.runner_glob else RUNNER_GLOBS, args.cap)
    return 0          # reports; never decides


if __name__ == "__main__":
    raise SystemExit(main())
