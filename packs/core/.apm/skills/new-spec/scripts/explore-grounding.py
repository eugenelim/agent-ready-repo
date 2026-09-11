#!/usr/bin/env python3
"""Answer "what already governs these paths?" before a spec or plan is authored.

Seven probes, seeded by the paths a change will touch, selected by stage. The cost is bounded by the
seed set and its references rather than by the repository, which is the whole
difference from a repository map: a map's cost scales with the repository and its
token budget truncates exactly the rare edge you needed.

  scoped rules   which governing files sit above a seed, root-ward
  path refs      which files name a seed path
  phrase pins    which files quote a distinctive line from a seed file
  gates          which runners would execute a seed path
  co-change      which files historically move with a seed path
  surfaces       which known grounding surfaces exist, and carry content
  dead refs      which paths a seed names that no longer resolve

`--phase` selects the set a stage needs: at discovery nothing is authored yet, so
a dead-reference scan returns a reassuring empty result; at review the artifacts
are the seeds and their references are the question.

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

# One script, directed differently by phase. The probe set is what changes, not
# the mechanism: at discovery nothing has been written yet, so dead references
# cannot exist and asking for them wastes a scan; at review the artifacts are the
# seeds and their references are the whole question.
PHASES = {
    # After durable outputs resolve destinations, before the spec body is written.
    "discovery": ("surfaces", "scoped", "refs", "pins", "gates"),
    # Per plan task, seeded by that task's own Touches.
    "task": ("scoped", "refs", "pins", "gates", "co-change"),
    # Over the authored artifacts themselves, to catch what repair rounds broke.
    "review": ("refs", "dead", "co-change"),
    "all": ("surfaces", "scoped", "refs", "pins", "gates", "dead", "co-change"),
}

# Every distinct outcome this explorer can report, keyed by name. Declared here
# so the repository-level catalogue check can verify that some case exercises
# each one; a probe outcome no test observes has no red case. It is a floor, not
# a derivation -- containing a fragment is not asserting on it.
FINDING_KINDS = {
    "none-found": "none found",
    "unavailable": "unavailable — input missing",
    "unreached": "UNREACHED — no runner names this path",
    "copies": "copies of seed",
    "dead-ref": "dead refs",
    "ambiguous-ref": "ambiguous refs",
    "capped": "capped at",
    "unconfined": "refusing seed outside root",
    "no-git": "git unavailable",
    "suffix-basis": "scanned suffixes",
    "co-min": "minimum co-occurrences",
    "oversize": "past the size bound",
    "cutoff-basis": "cutoff",
    "sweep-basis": "sweep-commit threshold",
}

# A seed suffix allowlist is a repository-shape assumption: on a TypeScript or Go
# adopter an omitted suffix makes every probe silently empty. The set is derived
# from what the repository actually tracks, capped so one stray binary extension
# cannot widen the scan without bound, overridable by flag, and named in the
# report -- silence about the candidate set is what turns a heuristic into a
# false clean.
BINARY_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz",
                   ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webp", ".so", ".dylib"}
SUFFIX_CAP = 40
FALLBACK_SUFFIXES = {".py", ".md", ".toml", ".json", ".yml", ".yaml", ".cfg", ".ini",
                     ".txt", ".sh", ""}


def text_suffixes(root: Path, tracked: set[str] | None,
                  override: tuple[str, ...] | None) -> tuple[set[str], str]:
    """Which file suffixes to scan, derived from the repository's own contents."""
    if override:
        return {s if s.startswith(".") or s == "" else f".{s}" for s in override}, "given"
    if not tracked:
        return set(FALLBACK_SUFFIXES), "default (no tracked set)"
    counts = Counter(Path(rel).suffix.lower() for rel in tracked)
    derived = {suffix for suffix, _ in counts.most_common(SUFFIX_CAP)
               if suffix not in BINARY_SUFFIXES}
    return derived or set(FALLBACK_SUFFIXES), f"derived from {len(tracked)} tracked file(s)"


TEXT_SUFFIXES = FALLBACK_SUFFIXES
MAX_READ_BYTES = 2_000_000
_TOP_CACHE: tuple[str, ...] = ()


def calibrate_sweep(root: Path, default: int) -> tuple[int, str]:
    """Derive the sweep-commit threshold from this repository's own commit sizes.

    A fixed number is a guess about someone else's repository. A monorepo's
    ordinary commit touches more files than a small library's, so the same
    constant is too tight in one and too loose in the other -- and being wrong is
    silent either way, because an over-tight threshold simply reports nothing.
    The p90 of recent commit sizes is this repository's own answer.
    """
    sizes = []
    shas = _git(root, "log", "--format=%H", "-n", "120")
    if shas is None:
        return default, "default (no history)"
    for sha in [x for x in shas if x][:120]:
        files = _git(root, "show", "--name-only", "--format=", "--no-renames", sha)
        if files is not None:
            sizes.append(len({f for f in files if f}))
    if len(sizes) < 20:
        return default, f"default (only {len(sizes)} commits)"
    sizes.sort()
    p90 = sizes[int(len(sizes) * 0.9)]
    return max(5, p90), f"p90 of {len(sizes)} commits"


def calibrate_cutoff(per_phrase: list[int], scanned: int, default: int) -> tuple[int, str]:
    """Derive the boilerplate cutoff from the observed match distribution.

    Shipped boilerplate is not "three files" -- that was this repository's shape.
    It is a phrase appearing in a share of the corpus no genuine pin ever reaches.
    Absent enough signal the default stands, and the report says which was used so
    a mis-calibration is visible rather than silently narrowing the results.
    """
    if scanned < 50 or len(per_phrase) < 8:
        return default, "default (too little signal)"
    ordered = sorted(per_phrase)
    p75 = ordered[int(len(ordered) * 0.75)]
    return max(default, p75), f"p75 of {len(per_phrase)} matched phrases"


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


def confined_files(root: Path, tracked: set[str] | None,
                   suffixes: set[str] | None = None) -> list[Path]:
    """Every readable regular file under root, symlinks refused rather than followed."""
    if tracked:
        out = []
        for rel in sorted(tracked):
            path = root / rel
            try:
                info = path.lstat()
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode) and path.suffix.lower() in (suffixes or TEXT_SUFFIXES):
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
            if stat.S_ISREG(info.st_mode) and path.suffix.lower() in (suffixes or TEXT_SUFFIXES):
                out.append(path)
    return out


def _runner_patterns(seed: str) -> list[re.Pattern[str]]:
    """How a runner might name this seed: itself, or a directory just above it.

    Two calibrations, both learned by getting it wrong. **Depth floor:** only
    ancestors of three segments or more, because `docs` or `packs` appears in
    every workflow and matching them reports nine gates for an architecture
    document. **Right boundary:** an ancestor must not be followed by another
    path character, or `packs/core/tests/skills` matches every sibling suite
    under it.
    """
    parts = seed.split("/")
    # The seed itself is always eligible however shallow it sits; the depth floor
    # governs only its ancestors, which are where the over-matching comes from.
    ancestors = ["/".join(parts[:i]) for i in (len(parts) - 1, len(parts) - 2)]
    candidates = [seed] + [a for a in ancestors if a and a.count("/") >= 2]
    return [
        re.compile(re.escape(c) + r"/?(?=[\s'\"\\]|$)")
        for c in dict.fromkeys(candidates)
    ]


def _oversize(files: list[Path]) -> int:
    """Files skipped for size. Counted rather than silently read as empty."""
    total = 0
    for path in files:
        try:
            total += path.stat().st_size > MAX_READ_BYTES
        except OSError:
            continue
    return total


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
    # A directory seed governs itself. Starting at the parent -- correct only for
    # a file -- silently drops the most governing file for the surface, and every
    # plan `Touches` field names directories.
    target = root / seed
    found, here = [], (target if target.is_dir() else target.parent)
    while True:
        candidate = here / filename
        if candidate.is_file():
            found.append(candidate.relative_to(root).as_posix())
        if here == root:
            break
        here = here.parent
    return found


def distinctive_lines(root: Path, seed: str, limit: int = 40) -> list[str] | None:
    """Sampled prose lines, or None when the seed offers no text to sample.

    None is not an empty list. A seed that does not exist yet -- the normal
    discovery-phase seed, since discovery is seeded by destinations the delivery
    will create -- and a seed that is not prose both yield nothing, and reporting
    either as "none found" is the conflation of unavailable input with a clean
    result that this explorer refuses everywhere else.
    """
    path = root / seed
    if not path.is_file() or path.suffix != ".md":
        return None
    lines = [
        line.strip() for line in _read(path).splitlines()
        if 60 <= len(line.strip()) <= 140 and line.strip()[:1].isalpha()
    ]
    step = max(1, len(lines) // limit)
    return lines[::step][:limit]


def declared_new(text: str) -> set[str]:
    """Paths a document says it creates, which are legitimately absent.

    Read from a plan's Touches declarations, a spec's durable-output map, and any
    explicit `(new)` marker. The two artifacts declare creation differently, and
    reading only one of them makes the other's intentional absences look dead. Without this every task that creates a file reads as a dead
    reference, which is the false-positive class that dominates on a plan.
    """
    out: set[str] = set()
    for block in re.findall(r"\*\*Touches:\*\*(.+?)(?:\n\n)", text, re.S):
        out.update(_rooted(block))
    # A spec declares what the delivery will produce through its durable-output
    # map, never through Touches. Without this half every durable output a spec
    # names reads as a dead reference, because it does not exist yet by design --
    # which is the same false-positive class Touches closes for a plan.
    for block in re.findall(r"^## Durable [Oo]utputs(.+?)(?=^## |\Z)", text, re.S | re.M):
        out.update(_rooted(block))
    for line in text.splitlines():
        if "(new)" in line:
            out.update(_rooted(line))
    return out


def _rooted(text: str) -> set[str]:
    """Repository-rooted paths named in prose, calibrated against placeholders."""
    out: set[str] = set()
    for raw in re.findall(r"[A-Za-z0-9_.\-/]+", text):
        token = re.sub(r"[#:]\d+(-\d+)?$", "", raw.rstrip(".,:;)"))
        token = re.sub(r"#.*$", "", token)
        if "/" not in token or not token.startswith(_TOP_CACHE):
            continue
        if any(ch in token for ch in "*{}<>") or "NNNN" in token:
            continue
        out.add(token)
    return out


def live_references(
    root: Path, seed: str, known: set[str] | None
) -> tuple[list[str] | None, list[str]]:
    """Paths a seed names that no longer resolve, split from ambiguous ones.

    A path resolving under some other root is a scope question no rule settles --
    the same string is dead at the repository root and alive inside a package --
    so it is emitted as an ambiguity with its candidate rather than asserted dead.
    """
    text = _read(root / seed)
    if not text:
        # None, not an empty list. A directory seed -- which every plan Touches
        # field names -- an absent seed, and a file past the size bound all yield
        # no text, and reporting any of them as "none found" is the conflation
        # every other probe here was repaired to refuse.
        return None, []
    created = declared_new(text)
    dead: list[str] = []
    ambiguous: list[str] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for token in sorted(_rooted(line)):
            if (root / token).exists() or (known and token in known) or token in created:
                continue
            elsewhere = sorted(k for k in (known or ()) if k.endswith("/" + token))
            if elsewhere:
                ambiguous.append(f"{seed}:{lineno}  {token}  → resolves at {elsewhere[0]}")
            else:
                dead.append(f"{seed}:{lineno}  {token}")
    return dead, ambiguous


def surface_inventory(root: Path) -> list[str]:
    """Which known grounding surfaces exist, and whether they carry content.

    Reported so a degraded run is legible. Absence lowers the starting
    information and never fails the run.
    """
    rows = []
    for name in (".adapt-discovery.toml", ".adapt-pending.md", ".adapt-install-marker.toml",
                 "AGENTS.md", "docs/architecture/reference.md"):
        path = root / name
        if not path.is_file():
            rows.append(f"{name:<38} absent")
            continue
        body = _read(path)
        headings = len(re.findall(r"^#{1,3} ", body, re.M))
        rows.append(f"{name:<38} present  {len(body.splitlines())} lines, {headings} heading(s)")
    return rows


def runner_files(root: Path, globs: tuple[str, ...]) -> list[Path]:
    out: list[Path] = []
    for pattern in globs:
        out.extend(p for p in root.glob(pattern) if p.is_file())
    return sorted(set(out))


def co_change(root: Path, seeds: list[str], co_min: int = 3,
              sweep: int = 30) -> tuple[str, list[tuple[str, int, float]]]:
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
        if len(touched) > sweep:
            continue
        partners.update(touched - set(seeds))
    ranked = [
        (name, count, count / len(shas))
        for name, count in partners.most_common()
        if count >= co_min
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


def explore(root: Path, seeds: list[str], guidance: str, globs: tuple[str, ...],
            cap: int, cutoff: int, co_min: int, sweep: int,
            probes: tuple[str, ...], suffix_override: tuple[str, ...] | None) -> None:
    tracked_raw = _git(root, "ls-files")
    tracked = {t for t in tracked_raw if t} if tracked_raw is not None else None
    tops = top_levels(root)
    suffixes, suffix_basis = text_suffixes(root, tracked, suffix_override)
    files = confined_files(root, tracked, suffixes)
    runners = runner_files(root, globs)

    global _TOP_CACHE
    _TOP_CACHE = tuple(f"{t}/" for t in tops)
    print(f"seeds: {len(seeds)}   top-levels derived: {len(tops)}   "
          f"files scanned: {len(files)}   runner candidates: {len(runners)}")
    print(f"scanned suffixes: {len(suffixes)} — {suffix_basis}"
          + (f"; skipped {oversize} file(s) past the size bound" if (oversize := _oversize(files)) else ""))
    print(f"phase probes: {', '.join(probes)}")
    # A bound that filters results names itself on every run, not only on the
    # runs whose probe set consumes it: a reader cannot tell a filtered-out
    # partner from an absent one, and the criterion promises the value either way.
    print(f"minimum co-occurrences {co_min} — a partner below this is filtered out")
    if "surfaces" in probes:
        print("grounding surfaces:")
        for row in surface_inventory(root):
            print(f"  {row}")
    unlisted = sorted(
        p.name for p in root.iterdir()
        if p.is_file() and p not in runners
        and re.search(r"(?i)^(justfile|taskfile|noxfile|tox\.ini|.*\.mk|dagger\.json|earthfile)$", p.name)
    )
    if unlisted:
        print(f"  note: runner-like files not in the candidate set: {', '.join(unlisted)}")
    if tracked is None:
        print("note: git unavailable — tracked-set and co-change probes degrade; "
              "ignored files are not excluded")

    # Derived only when something consumes it: the walk costs one git call per
    # commit, and no phase but co-change reads the result.
    sweep_basis = "not derived (no co-change probe in this phase)"
    if "co-change" in probes:
        sweep, sweep_basis = calibrate_sweep(root, sweep)
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
            # A runner reaches a file by naming any directory above it: a suite
            # is invoked as `pytest <dir>/`, never file by file. Matching the
            # exact path only would report a covered test as unreached, which
            # inverts the probe -- its whole value is telling you when nothing
            # runs a path.
            if path in runners and any(p.search(text) for p in _runner_patterns(seed)):
                gates[seed].append(rel)
            for phrase in (phrases.get(seed) or ()):
                if phrase in text:
                    hits.setdefault((seed, phrase), set()).add(rel)

    for seed in seeds:
        # A phrase in many files is the shipped boilerplate every sibling carries.
        # A file matching most of the seed's sampled phrases is a copy of it --
        # a generated projection, a vendored duplicate -- not a pin on it. A pin
        # quotes one thing; a copy quotes everything. Content decides, so this
        # needs no knowledge of where a given repository puts its projections.
        # A floor, not just a ratio. With few sampled phrases half of them can be
        # one, and a single quotation is exactly what a pin looks like -- so
        # without the floor every pin is misread as a copy.
        sampled = max(1, len(phrases.get(seed) or ()))
        copy_threshold = max(2, sampled // 2)
        # Bound to a local, never back into `cutoff`. Reassigning the parameter
        # fed seed N's derived value in as seed N+1's default, so the value was
        # order-dependent and a thin second seed printed the first seed's number
        # under the basis "default" -- which defeats the point of naming a basis.
        seed_cutoff, cutoff_basis = calibrate_cutoff(
            [len(w) for (o, _), w in hits.items() if o == seed], len(files), cutoff)
        per_file: Counter[str] = Counter()
        for (owner, _), where in hits.items():
            if owner == seed:
                per_file.update(where)
        pins = sorted({
            rel for (owner, _), where in hits.items()
            if owner == seed and len(where) <= seed_cutoff
            for rel in where
            if per_file[rel] < copy_threshold
        })
        copies = sorted(rel for rel, n in per_file.items() if n >= copy_threshold)
        # Unavailable is not empty: a seed that is absent or not prose offers
        # nothing to sample, and reporting that as "none found" is the conflation
        # this explorer refuses everywhere else.
        pins_status = ("unavailable" if phrases.get(seed) is None
                       else ("found" if pins else "none"))
        print(f"\n=== {seed}")
        if "scoped" in probes:
            rules = scoped_rules(root, seed, guidance)
            _emit("scoped rules", "found" if rules else "none", rules, cap)
        if "refs" in probes:
            _emit("path refs", "found" if refs[seed] else "none", sorted(refs[seed]), cap)
        if "pins" in probes:
            _emit("phrase pins", pins_status, pins, cap)
            print(f"                 cutoff {seed_cutoff} — {cutoff_basis}")
        if copies and "pins" in probes:
            _emit("copies of seed", "found", copies, cap)
        if "dead" in probes:
            dead, ambiguous = live_references(root, seed, tracked)
            _emit("dead refs",
                  "unavailable" if dead is None else ("found" if dead else "none"),
                  dead or [], cap)
            if ambiguous:
                _emit("ambiguous refs", "found", ambiguous, cap)
        if "gates" not in probes:
            pass
        elif not runners:
            # No runner file exists at all. Printing UNREACHED here renders
            # missing input as the probe's positive finding, distinguishable only
            # by reading a parenthetical zero.
            print(f"  {'gates':<14} unavailable — input missing, not a clean result "
                  f"(no runner file found)")
        elif gates[seed]:
            _emit("gates", "found", sorted(gates[seed]), cap)
        else:
            print(f"  {'gates':<14} UNREACHED — no runner names this path "
                  f"(considered {len(runners)} runner file(s))")

    if "co-change" not in probes:
        return
    status, ranked = co_change(root, seeds, co_min, sweep)
    print(f"\n=== co-change over all {len(seeds)} seed(s)")
    print(f"  sweep-commit threshold {sweep} — {sweep_basis}")
    _emit("partners", status,
          [f"{name}   {count} commits, confidence {ratio:.2f}" for name, count, ratio in ranked],
          cap)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--guidance-file", default="AGENTS.md")
    parser.add_argument("--runner-glob", action="append", default=None)
    parser.add_argument("--cap", type=int, default=RESULT_CAP)
    parser.add_argument("--phrase-cutoff", type=int, default=BOILERPLATE_CUTOFF)
    parser.add_argument("--co-change-min", type=int, default=CO_CHANGE_MIN)
    parser.add_argument("--sweep-commit-size", type=int, default=SWEEP_COMMIT_SIZE)
    parser.add_argument("--suffix", action="append", default=None,
                        help="scan these file suffixes instead of the derived set")
    parser.add_argument("--phase", choices=sorted(PHASES), default="all",
                        help="which probe set this stage needs")
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
            tuple(args.runner_glob) if args.runner_glob else RUNNER_GLOBS,
            args.cap, args.phrase_cutoff, args.co_change_min, args.sweep_commit_size,
            PHASES[args.phase], tuple(args.suffix) if args.suffix else None)
    return 0          # reports; never decides


if __name__ == "__main__":
    raise SystemExit(main())
