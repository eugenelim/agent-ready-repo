#!/usr/bin/env python3
"""Asserts the runtime export boundary holds for every pack in the catalogue.

`.apm/` is what gets projected into an installed agent environment, so nothing
that is not runtime content may live there. That rule survived for a long time
only because the installer happens to read `seeds/` and `.apm/` and ignore
everything else — an implicit exclusion, not a structural one. This lint makes
it structural: it fails when a test file appears under any pack's `.apm/`, and
when one appears in a projected skill.

Checking the projection *positively* is the point. Inferring "no tests are
installed" from "the installer ignores those paths" is exactly the reasoning
that let the violation persist; a future adapter that copies `.apm/**` wholesale
would break the inference without breaking any test.

Cross-pack behaviour is not pack-owned (`catalogue-authoring-standards.md` § 4),
which is why this lives in `tools/` rather than in one pack's test tree.

`evals/` is deliberately not flagged: eval fixtures are skill-local runtime
content and are projected with the skill by design.

Six checks:

1. **apm-carries-no-tests** — no pack's `.apm/` holds test content.
2. **projection-carries-no-tests** — no projected skill does either, asserted
   per pack against the self-host recipe's include list so a pack dropping out
   of the projection fails rather than passing on an empty iteration.
3. **tests-live-in-the-pack-tree** — a pack that owns tests has them under
   `packs/<pack>/tests/`.
4. **runners-keep-suites-isolated** — no single pytest invocation covers two
   skill test directories. Suite-local imports can bind a sibling skill's
   same-named subject module and pass green, even when test basenames differ.
5. **every-suite-dir-has-a-runner** — every skill test directory is named by a
   runner or declared in `_NO_RUNNER` with a reason. Without this, "which suites
   actually run" has no living home and the next directory is unrun by default.
6. **pack-tests-stay-in-pack** — Python pack tests may inspect their owning pack
   and temporary fixtures, but may not climb to the repository root and inspect
   another source tree.
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
import tomllib
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import NamedTuple

import lint_git_ignore  # tools/ is sys.path[0] for a script run

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "packs"
if not PACKS.is_dir():                      # wrong parents[] depth after a move
    raise SystemExit(f"packs/ not found at {PACKS} — check the parents[] depth")

RECIPE = (ROOT / "packages" / "agentbundle" / "agentbundle" / "build"
          / "recipes" / "self-host.toml")

# The shapes a test actually takes, across the languages this catalogue can grow
# into. Deliberately a superset of what the tree holds today: a matcher tuned to
# the current contents proves nothing about the next pack.
#
# Deliberate narrowings, each for a reason:
#   - no bare `test` substring — `test-fixtures.md` as reference material for a
#     skill *about* testing would be a false positive;
#   - `evals/` is runtime-adjacent by decision (ADR-0071) and is skipped;
#   - gitignored build residue is not authored content.
_TEST_FILE = re.compile(
    r"^(conftest\.py"
    r"|.+\.(test|spec)\.(py|sh|js|ts|tsx|mjs|cjs|go|ps1|rb)"
    r"|.+[-_]test\.(py|sh|js|ts|tsx|mjs|cjs|go|ps1|rb)"
    r"|test[-_].+\.(py|sh|js|ts|tsx|mjs|cjs|go|ps1|rb))$"
)
_TEST_DIR = frozenset({"tests", "test", "__tests__", "spec"})
_SKIP_DIR = frozenset({"evals"})

# `__pycache__` and friends are gitignored build residue, not authored content,
# so they are not a boundary violation. They were also a packaging problem —
# `package.py` walked `packs/**` and collected them — fixed in agentbundle
# 0.29.5, which prunes the same shapes from both archive flavours.
_TRANSIENT = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache",
                        ".ruff_cache", "node_modules"})


class _ParentsPath(NamedTuple):
    """A ``Path.parents`` sequence that retains its ``__file__`` origin."""

    path: Path


class _UnresolvedPath(NamedTuple):
    """A source-derived path whose final location cannot be proved local."""

    path: Path


class _StringValues(NamedTuple):
    """Literal or proven-confined filename values; empty means a safe glob."""

    values: tuple[str, ...]


class _PathConstructor(NamedTuple):
    """An alias of pathlib.Path."""

    name: str


_PathValue = (
    Path | _ParentsPath | _UnresolvedPath | _StringValues | _PathConstructor | None
)


def _is_linked_dir(path: Path) -> bool:
    """Whether a directory entry redirects the walk to another tree."""
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def _walk_candidates(base: Path) -> list[Path]:
    """Test-shaped content under *base*, before ignore filtering.

    Uses `os.walk(followlinks=False)` with an explicit symlink prune, matching
    `catalogue_tooling/package.py`'s archive walk. The lint and the walker that
    decides what actually ships must not hold two different definitions of what
    pack content is — and `Path.rglob`'s symlink behaviour changed across the
    3.12/3.13 boundary.

    Split from the ignore filter so every base's candidates can be gathered
    first and resolved in **one** `git check-ignore` process. The pruning here
    also means no candidate's ancestor chain crosses a symlink, which is the
    resolver's documented precondition.
    """
    found: list[Path] = []
    if not base.is_dir() or _is_linked_dir(base):
        return found
    for dirpath, dirnames, filenames in os.walk(str(base), followlinks=False):
        dp = Path(dirpath)
        dirnames[:] = [
            dn for dn in dirnames
            if dn not in _TRANSIENT and dn not in _SKIP_DIR
            and not _is_linked_dir(dp / dn)
        ]
        for dn in dirnames:
            if dn in _TEST_DIR:
                found.append(dp / dn)
        for fn in filenames:
            p = dp / fn
            if _TEST_FILE.match(fn) and not p.is_symlink():
                found.append(p)
    return found


class GitIgnoreUnresolved(RuntimeError):
    """A standalone walk could not resolve the ignore set. Never fail open."""


class IgnoreOutcome(NamedTuple):
    """The ignored subset, plus whether Git actually answered.

    `refused` distinguishes "git could not run" from "git ran and rejected the
    batch". The remediation differs — one says re-run where git works, the other
    says a candidate was unusable — so folding them together sends the reader the
    wrong way.
    """

    ignored: frozenset[Path]
    degraded: bool = False
    detail: str | None = None
    refused: bool = False


def _resolve_ignored(root: Path, candidates: list[Path]) -> IgnoreOutcome:
    """One batched `check-ignore` for the whole candidate set.

    A locally-generated, gitignored file is not a boundary violation, so the
    ignored set is *subtracted* from what the walk found. That subtraction is
    load-bearing in a direction that is easy to miss: two findings fire on the
    **emptiness** of what remains, so reporting "nothing is ignored" when Git
    never answered turns those failures into passes. Degradation is therefore
    returned rather than swallowed, and the caller refuses to report an
    ignore-derived verdict from an unresolved layer.
    """
    if not candidates:
        return IgnoreOutcome(frozenset())
    try:
        resolution = lint_git_ignore.git_ignored_paths(
            root, candidates,
            missing_git_policy=lint_git_ignore.MissingGitPolicy.FAIL_OPEN,
            timeout=120.0,
        )
    except lint_git_ignore.GitIgnoreError as exc:
        return IgnoreOutcome(frozenset(), degraded=True, detail=str(exc),
                             refused=True)
    except ValueError as exc:
        return IgnoreOutcome(frozenset(), degraded=True, detail=str(exc),
                             refused=True)
    return IgnoreOutcome(
        frozenset(resolution.ignored),
        degraded=resolution.degraded,
        detail=resolution.detail,
    )


def _walk(base: Path, ignored: frozenset[Path] | None = None,
          root: Path | None = None) -> list[Path]:
    """Authored test content under *base*, with gitignored residue removed.

    *ignored* is supplied by the per-invocation inventory, which resolves every
    base's candidates in one process. Callers outside a lint invocation — the
    self-test calls this directly — may omit it and pay for one batched
    resolution of just this base.

    Raises:
        GitIgnoreUnresolved: when no *ignored* set was supplied and Git could not
            answer. Returning unfiltered content would be fail-open in the one
            helper whose siblings go to lengths to be fail-closed, and silently
            so — the caller could not tell a clean tree from an unresolved one.
    """
    found = _walk_candidates(base)
    if not found:
        return found
    if ignored is None:
        outcome = _resolve_ignored(ROOT if root is None else root, found)
        if outcome.degraded:
            raise GitIgnoreUnresolved(
                f"cannot decide which paths under {base.name} are ignored "
                f"({outcome.detail}); refusing to return unfiltered content"
            )
        ignored = outcome.ignored
    return [p for p in found if p not in ignored]


def _rel(p: Path, root: Path | None = None) -> str:
    """Path relative to *root* (the repository by default).

    Explicit because a fixture-scoped run has a different root, and a message
    carrying an absolute temp path is both unportable and a privacy leak.
    """
    try:
        return str(p.relative_to(ROOT if root is None else root))
    except ValueError:
        return str(p)


@dataclass(frozen=True)
class BoundaryContext:
    """Everything a run needs to locate the catalogue it is checking.

    Explicit rather than module-global so a run can be pointed at a synthetic
    fixture. `no_runner` is in here for a concrete reason: it is a map of *real*
    repository paths, so a fixture run against the module constant reports one
    stale-exemption finding per entry — measured, not hypothesised.
    """

    root: Path
    packs_root: Path
    recipe_path: Path
    projected_roots: tuple[Path, ...]
    runner_files: tuple[str, ...]
    no_runner: Mapping[str, str]


def default_context(root: Path | None = None) -> BoundaryContext:
    """The real repository, as the no-argument CLI sees it."""
    base = ROOT if root is None else root
    return BoundaryContext(
        root=base,
        packs_root=base / "packs",
        recipe_path=(base / "packages" / "agentbundle" / "agentbundle" / "build"
                     / "recipes" / "self-host.toml"),
        projected_roots=tuple(
            r for r in (base / ".claude" / "skills", base / ".agents" / "skills")
            if r.is_dir()
        ),
        runner_files=_RUNNER_FILES,
        no_runner=_NO_RUNNER,
    )


@dataclass
class BoundaryInventory:
    """One view of the catalogue, built once per invocation.

    Every check reads this instead of deriving its own copy. Before, six checks
    independently rebuilt overlapping parts of it: the tree was walked 141 times
    over 109 distinct bases, glob bases were confinement-scanned 45 times over 16
    distinct ones, and the six runner files were read and parsed twice.

    Deliberately **not** cached across processes or invocations. A stale answer
    about what is on disk is worse than a slow one, and the point of the
    per-invocation scope is that it cannot go stale.
    """

    context: BoundaryContext
    packs: tuple[Path, ...]
    recipe_found: bool
    include: tuple[str, ...]
    ignored: frozenset[Path]
    ignore_degraded: bool
    ignore_detail: str | None
    ignore_refused: bool = False
    _walks: dict[Path, tuple[Path, ...]] = field(default_factory=dict)
    _confinement: dict[Path, bool] = field(default_factory=dict)
    _destinations: tuple[Path, ...] | None = None
    _runners: tuple[tuple, ...] | None = None
    _runner_findings: tuple[str, ...] | None = None
    walk_misses: int = 0
    runner_parses: int = 0
    destination_builds: int = 0

    def walk(self, base: Path) -> list[Path]:
        """Filtered test content under *base*, from the pre-resolved ignore set.

        A miss resolves that base's candidates on the spot rather than filtering
        them against a set they were never submitted to. Filtering against a
        stale set is the quiet failure: gitignored residue under an
        un-enumerated base would be reported as a boundary violation, and
        nothing would say why. `_enumerate_walk_bases` should make misses
        impossible — `walk_misses` is asserted zero for the real tree — so a miss
        is a bug being contained, not a supported path.
        """
        key = Path(os.path.normpath(str(base)))
        cached = self._walks.get(key)
        if cached is None:
            self.walk_misses += 1
            found = _walk_candidates(base)
            outcome = _resolve_ignored(self.context.root, found)
            if outcome.degraded:
                # Surfaced through the inventory so the caller's fatal-degradation
                # path sees it, rather than silently returning unfiltered content.
                self.ignore_degraded = True
                self.ignore_detail = outcome.detail
                # Carried too, or a batch git *refused* here would be reported as
                # "git is unavailable" — the conflation `refused` exists to stop.
                self.ignore_refused = self.ignore_refused or outcome.refused
            cached = tuple(p for p in found if p not in outcome.ignored)
            self._walks[key] = cached
        return list(cached)

    def glob_tree_is_confined(self, base: Path) -> bool:
        """Memoised tree-confinement verdict for one glob base.

        Keyed on the **lexically normalised unresolved** path, never
        `base.resolve()`. A resolved key collapses a symlink and its target into
        one entry: whichever is scanned first then decides for both, losing the
        symlink refusal in one order and falsely refusing the real tree in the
        other — wrong in both directions, and dependent on filesystem iteration
        order. Verified against a fixture before choosing this key.
        """
        try:
            key = Path(os.path.normpath(str(base)))
        except (OSError, RuntimeError, ValueError):
            return False          # no key to cache under; refuse without caching
        verdict = self._confinement.get(key)
        if verdict is None:
            verdict = _glob_tree_is_confined(base)
            self._confinement[key] = verdict
        return verdict

    def destinations(self) -> list[Path]:
        """Every skill test directory that holds a suite. Built once."""
        if self._destinations is None:
            self.destination_builds += 1
            out: list[Path] = []
            for pack in self.packs:
                skills = pack / "tests" / "skills"
                if not skills.is_dir():
                    continue
                for directory in sorted(skills.iterdir()):
                    if directory.is_dir() and self.walk(directory):
                        out.append(directory)
            self._destinations = tuple(out)
        return list(self._destinations)

    def runner_lines(self) -> tuple[list[tuple[str, int, set[str]]], list[str]]:
        """Parsed pytest invocations, plus the findings the parse itself produced.

        Parsed once; the findings are returned so each consuming check can
        re-emit them at its own position. Both checks reach this, so a missing or
        malformed runner file yields **two** findings — existing behaviour, and
        deduplicating the parse must not deduplicate the report.
        """
        if self._runners is None:
            self.runner_parses += 1
            lines, findings = _parse_runner_files(self.context)
            self._runners = tuple(lines)
            self._runner_findings = tuple(findings)
        return [tuple(item) for item in self._runners], list(self._runner_findings)


def _enumerate_walk_bases(context: BoundaryContext,
                          packs: tuple[Path, ...],
                          include: tuple[str, ...]) -> list[Path]:
    """Every base any check will walk, so one batch can cover them all."""
    bases: list[Path] = []
    for pack in packs:
        bases.append(pack / ".apm")
        bases.append(pack / "tests")
        skills = pack / "tests" / "skills"
        if skills.is_dir():
            bases.extend(d for d in sorted(skills.iterdir()) if d.is_dir())
    for name in include:
        skills_dir = context.packs_root / name / ".apm" / "skills"
        if not skills_dir.is_dir():
            continue
        for skill in sorted(p.name for p in skills_dir.iterdir() if p.is_dir()):
            for adapter_root in context.projected_roots:
                projected = adapter_root / skill
                if projected.is_dir():
                    bases.append(projected)
    return bases


def build_inventory(context: BoundaryContext) -> BoundaryInventory:
    """Construct the one inventory for this invocation. Instrumentation seam."""
    packs = tuple(
        p for p in sorted(context.packs_root.iterdir())
        if p.is_dir() and not p.name.startswith("_") and (p / "pack.toml").is_file()
    ) if context.packs_root.is_dir() else ()

    recipe_found = context.recipe_path.is_file()
    include: tuple[str, ...] = ()
    if recipe_found:
        data = tomllib.loads(context.recipe_path.read_text(encoding="utf-8"))
        include = tuple(data.get("recipe", {}).get("packs", {}).get("include", []))

    # Gather every base's candidates, then resolve the union in ONE process.
    candidates: list[Path] = []
    seen: set[Path] = set()
    prewalked: dict[Path, list[Path]] = {}
    for base in _enumerate_walk_bases(context, packs, include):
        key = Path(os.path.normpath(str(base)))
        if key in prewalked:
            continue
        found = _walk_candidates(base)
        prewalked[key] = found
        for path in found:
            if path not in seen:
                seen.add(path)
                candidates.append(path)

    outcome = _resolve_ignored(context.root, candidates)

    inventory = BoundaryInventory(
        context=context,
        packs=packs,
        recipe_found=recipe_found,
        include=include,
        ignored=outcome.ignored,
        ignore_degraded=outcome.degraded,
        ignore_detail=outcome.detail,
        ignore_refused=outcome.refused,
    )
    for key, found in prewalked.items():
        inventory._walks[key] = tuple(
            path for path in found if path not in outcome.ignored
        )
    return inventory


def case_apm_carries_no_tests(inv: BoundaryInventory, out: list[str]) -> str | None:
    root = inv.context.root
    packs = inv.packs
    if not packs:
        out.append("no packs found under packs/ — this must not pass "
                        "vacuously")
        return None
    hits: list[Path] = []
    for pack in packs:
        hits += inv.walk(pack / ".apm")
    if hits:
        out.append(
            "a pack's .apm/ is the runtime export boundary but carries test "
            "content:\n    " + "\n    ".join(_rel(h, root) for h in hits)
            + "\n  Move it to packs/<pack>/tests/ — see "
              "catalogue-authoring-standards.md § 4."
        )
        return None
    return f"ok   [apm-carries-no-tests] ({len(packs)} packs)"


def case_projection_carries_no_tests(inv: BoundaryInventory, out: list[str]) -> str | None:
    """The installed artifact, checked directly rather than inferred."""
    root = inv.context.root
    before = len(out)
    if not inv.recipe_found:
        out.append(
            f"self-host recipe not found at {_rel(inv.context.recipe_path, root)}"
        )
        # Deliberately no early return: the original reported BOTH the missing
        # recipe and the resulting empty include list, so a missing recipe is two
        # findings. The golden baseline caught the early return that lost one.
    include = list(inv.include)
    if not include:
        out.append("self-host recipe lists no packs to project")
        return None
    adapter_roots = list(inv.context.projected_roots)
    if not adapter_roots:
        out.append(
            "no projected skills tree found under .claude/skills or "
            ".agents/skills — run `make build-self`; this check must not pass "
            "vacuously"
        )
        return None
    hits: list[Path] = []
    total = 0
    for name in include:
        skills_dir = inv.context.packs_root / name / ".apm" / "skills"
        if not skills_dir.is_dir():
            continue
        skills = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())
        checked = 0
        for adapter_root in adapter_roots:
            for skill in skills:
                projected = adapter_root / skill
                if projected.is_dir():
                    checked += 1
                    hits += inv.walk(projected)
        if not checked:
            out.append(
                f"pack {name!r} is in the self-host include list but none of its "
                f"skills is projected — a pack dropping out of the projection "
                f"must fail here, not pass on an empty iteration"
            )
        total += checked
    if hits:
        out.append(
            f"projected skills carry test content ({total} checked):\n    "
            + "\n    ".join(_rel(h, root) for h in hits)
        )
        return None
    if len(out) == before:
        return (f"ok   [projection-carries-no-tests] ({total} projected "
                f"skills, {len(include)} packs)")
    return None


def case_tests_live_in_the_pack_tree(inv: BoundaryInventory, out: list[str]) -> str | None:
    """The positive half — a pack that owns tests has them where policy says."""
    root = inv.context.root
    before = len(out)
    owning = 0
    packs = inv.packs
    if not packs:
        out.append("no packs found under packs/ — this must not pass "
                        "vacuously")
        return None
    for pack in packs:
        tests = pack / "tests"
        if not tests.is_dir():
            continue                      # a pack may legitimately own no tests
        suites = inv.walk(tests)
        if not suites:
            out.append(
                f"{_rel(tests, root)} exists but holds no test content — an empty "
                f"test tree is a lost move, not a clean pack"
            )
            continue
        owning += 1
    if len(out) == before:
        return f"ok   [tests-live-in-the-pack-tree] ({owning} packs own tests)"
    return None


def _path_value(
    node: ast.AST,
    test_file: Path,
    names: dict[str, _PathValue],
    path_names: set[str],
    path_modules: set[str],
    inv: BoundaryInventory | None = None,
) -> _PathValue:
    """Resolve source paths built from ``__file__`` without executing a test."""
    if isinstance(node, ast.Name):
        if node.id == "__file__":
            return test_file
        if node.id in path_names:
            return _PathConstructor(node.id)
        return names.get(node.id)
    if (
        isinstance(node, ast.Attribute)
        and node.attr == "Path"
        and isinstance(node.value, ast.Name)
        and node.value.id in path_modules
    ):
        return _PathConstructor(ast.unparse(node))
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return _StringValues((node.value,))
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        strings = tuple(
            item.value
            for item in node.elts
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        )
        return _StringValues(strings) if len(strings) == len(node.elts) else None
    if isinstance(node, ast.GeneratorExp) and node.generators:
        return _path_value(
            node.generators[0].iter,
            test_file,
            names,
            path_names,
            path_modules,
            inv,
        )
    if isinstance(node, ast.Call):
        called = _path_value(node.func, test_file, names, path_names, path_modules, inv)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "cwd"
            and isinstance(
                _path_value(
                    node.func.value,
                    test_file,
                    names,
                    path_names,
                    path_modules,
                    inv,
                ),
                _PathConstructor,
            )
        ) or (
            (isinstance(node.func, ast.Attribute) and node.func.attr == "getcwd")
            or (isinstance(node.func, ast.Name) and node.func.id == "getcwd")
        ):
            return _UnresolvedPath(test_file)
        is_path_call = (
            isinstance(node.func, ast.Name) and node.func.id in path_names
        ) or (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "Path"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in path_modules
        ) or isinstance(called, _PathConstructor)
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in {"list", "set", "sorted", "tuple"}
            and len(node.args) == 1
        ):
            return _path_value(
                node.args[0], test_file, names, path_names, path_modules, inv
            )
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"abspath", "realpath"}
            and len(node.args) == 1
        ):
            value = _path_value(
                node.args[0], test_file, names, path_names, path_modules, inv
            )
            return value if isinstance(value, (Path, _UnresolvedPath)) else None
        if node.args and is_path_call:
            values = [
                _path_value(
                    argument, test_file, names, path_names, path_modules, inv
                )
                for argument in node.args
            ]
            source = next(
                (
                    value.path if isinstance(value, _UnresolvedPath) else value
                    for value in values
                    if isinstance(value, (Path, _UnresolvedPath))
                ),
                None,
            )
            if source is None:
                return None
            parts: list[Path | str] = []
            for value in values:
                if isinstance(value, Path):
                    parts.append(value)
                elif isinstance(value, _StringValues):
                    if any(_unsafe_path_segment(part) for part in value.values):
                        return _UnresolvedPath(source)
                    if value.values:
                        parts.append(value.values[0])
                else:
                    return _UnresolvedPath(source)
            return Path(*parts)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "joinpath":
            value = _path_value(
                node.func.value, test_file, names, path_names, path_modules, inv
            )
            if isinstance(value, _UnresolvedPath):
                return value
            if not isinstance(value, Path):
                return None
            parts: list[str] = []
            for argument in node.args:
                part = _path_value(
                    argument, test_file, names, path_names, path_modules, inv
                )
                if not isinstance(part, _StringValues):
                    return _UnresolvedPath(value)
                if any(_unsafe_path_segment(item) for item in part.values):
                    return _UnresolvedPath(value)
                if part.values:
                    parts.append(part.values[0])
            return value.joinpath(*parts)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"glob", "rglob"}
        ):
            value = _path_value(
                node.func.value, test_file, names, path_names, path_modules, inv
            )
            if isinstance(value, _UnresolvedPath):
                return value
            if not isinstance(value, Path):
                return None
            if (
                len(node.args) != 1
                or not isinstance(node.args[0], ast.Constant)
                or not isinstance(node.args[0].value, str)
            ):
                return _UnresolvedPath(value)
            if _unsafe_path_segment(node.args[0].value):
                return _UnresolvedPath(value)
            confined = (
                _glob_tree_is_confined(value) if inv is None
                else inv.glob_tree_is_confined(value)
            )
            if not confined:
                return _UnresolvedPath(value)
            return _StringValues(())
        if (
            not node.args
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"absolute", "resolve"}
        ):
            return _path_value(
                node.func.value, test_file, names, path_names, path_modules, inv
            )
        return None
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        value = _path_value(node.value, test_file, names, path_names, path_modules, inv)
        return value.parent if isinstance(value, Path) else None
    if isinstance(node, ast.Attribute) and node.attr == "parents":
        value = _path_value(
            node.value, test_file, names, path_names, path_modules, inv
        )
        return _ParentsPath(value) if isinstance(value, Path) else None
    if isinstance(node, ast.Subscript):
        value = _path_value(node.value, test_file, names, path_names, path_modules, inv)
        index = _integer_literal(node.slice)
        if isinstance(value, _ParentsPath) and isinstance(index, int):
            try:
                return value.path.parents[index]
            except IndexError:
                return None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        value = _path_value(node.left, test_file, names, path_names, path_modules, inv)
        if isinstance(value, _UnresolvedPath):
            return value
        right = _path_value(
            node.right, test_file, names, path_names, path_modules, inv
        )
        if isinstance(value, Path) and isinstance(right, _StringValues):
            if any(_unsafe_path_segment(part) for part in right.values):
                return _UnresolvedPath(value)
            return value / right.values[0] if right.values else value
        if isinstance(value, Path):
            return _UnresolvedPath(value)
    return None


def _unsafe_path_segment(value: str) -> bool:
    """Whether one literal can reset or traverse a path on POSIX or Windows."""
    for path in (PurePosixPath(value), PureWindowsPath(value)):
        if path.drive or path.root or ".." in path.parts:
            return True
    return False


def _glob_tree_is_confined(base: Path) -> bool:
    """Prove a glob base cannot redirect traversal outside itself."""
    if _is_linked_dir(base):
        return False
    try:
        resolved_base = base.resolve()
    except (OSError, RuntimeError):
        return False
    if not base.is_dir():
        return True
    for dirpath, dirnames, filenames in os.walk(str(base), followlinks=False):
        directory = Path(dirpath)
        kept_dirs: list[str] = []
        for name in dirnames:
            child = directory / name
            if _is_linked_dir(child):
                return False
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in filenames:
            child = directory / name
            if child.is_symlink():
                return False
            try:
                resolved_child = child.resolve()
            except (OSError, RuntimeError):
                return False
            if (
                resolved_child != resolved_base
                and resolved_base not in resolved_child.parents
            ):
                return False
    return True


def _integer_literal(node: ast.AST) -> int | None:
    """Return a signed integer literal without executing its expression."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, (ast.UAdd, ast.USub))
        and isinstance(node.operand, ast.Constant)
        and isinstance(node.operand.value, int)
    ):
        return (
            node.operand.value
            if isinstance(node.op, ast.UAdd)
            else -node.operand.value
        )
    return None


class _PackTestPathVisitor(ast.NodeVisitor):
    """Find checkout paths while respecting Python's lexical name scopes."""

    def __init__(self, test_file: Path, pack: Path, tree: ast.AST,
                 inv: BoundaryInventory | None = None) -> None:
        self._test_file = test_file
        self._inv = inv
        self._resolved_pack = pack.resolve()
        self._name_scopes: list[dict[str, _PathValue]] = [{}]
        self._path_names = {"Path"}
        self._path_modules = {"pathlib"}
        self._hits: list[tuple[int, str]] = []
        self._seen: set[tuple[int, int]] = set()
        self._node_stack: list[ast.AST] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "pathlib":
                self._path_names.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name == "Path"
                )
            elif isinstance(node, ast.Import):
                self._path_modules.update(
                    alias.asname or alias.name
                    for alias in node.names
                    if alias.name == "pathlib"
                )

    @property
    def hits(self) -> list[tuple[int, str]]:
        return sorted(set(self._hits))

    def _names(self) -> dict[str, _PathValue]:
        names: dict[str, _PathValue] = {}
        for scope in self._name_scopes:
            names.update(scope)
        return names

    def _value(self, node: ast.AST) -> _PathValue:
        return _path_value(
            node,
            self._test_file,
            self._names(),
            self._path_names,
            self._path_modules,
            self._inv,
        )

    def _record(self, node: ast.AST) -> None:
        value = self._value(node)
        if isinstance(value, _UnresolvedPath):
            self._add_hit(node)
            return
        if isinstance(value, (_StringValues, _PathConstructor)):
            return
        if isinstance(value, _ParentsPath):
            parent = self._node_stack[-1] if self._node_stack else None
            is_subscript_source = (
                isinstance(parent, ast.Subscript) and parent.value is node
            )
            is_alias_source = (
                isinstance(parent, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
                and parent.value is node
            )
            if not is_subscript_source and not is_alias_source:
                self._add_hit(node)
            return
        if value is None:
            if (
                isinstance(node, ast.Subscript)
                and isinstance(self._value(node.value), _ParentsPath)
            ):
                self._add_hit(node)
            return
        try:
            resolved_value = value.resolve()
        except (OSError, RuntimeError):
            self._add_hit(node)
            return
        if (
            resolved_value == self._resolved_pack
            or self._resolved_pack in resolved_value.parents
        ):
            return
        self._add_hit(node)

    def _add_hit(self, node: ast.AST) -> None:
        key = (getattr(node, "lineno", 1), getattr(node, "col_offset", 0))
        if key not in self._seen:
            self._seen.add(key)
            self._hits.append((key[0], ast.unparse(node)))

    def visit(self, node: ast.AST) -> None:
        self._record(node)
        self._node_stack.append(node)
        try:
            super().visit(node)
        finally:
            self._node_stack.pop()

    def _bind(self, target: ast.AST, value: _PathValue) -> None:
        if isinstance(target, ast.Name):
            self._name_scopes[-1][target.id] = value

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        value = self._value(node.value)
        for target in node.targets:
            self._bind(target, value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if node.value is not None:
            self.visit(node.value)
            self._bind(node.target, self._value(node.value))

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.visit(node.value)
        self._bind(node.target, self._value(node.value))

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._bind(node.target, self._value(node.iter))
        for statement in (*node.body, *node.orelse):
            self.visit(statement)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit_For(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in (*node.args.defaults, *node.args.kw_defaults):
            if default is not None:
                self.visit(default)
        if node.returns is not None:
            self.visit(node.returns)
        parameter_values: dict[str, _PathValue] = {}
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "parametrize"
                and len(decorator.args) >= 2
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, str)
                and "," not in decorator.args[0].value
            ):
                value = self._value(decorator.args[1])
                if isinstance(value, _StringValues):
                    parameter_values[decorator.args[0].value] = value
        self._name_scopes.append(parameter_values)
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self._name_scopes.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for expression in (*node.decorator_list, *node.bases, *node.keywords):
            self.visit(expression)
        self._name_scopes.append({})
        try:
            for statement in node.body:
                self.visit(statement)
        finally:
            self._name_scopes.pop()


def _pack_test_escapes(
    test_file: Path,
    source: str,
    inv: BoundaryInventory | None = None,
) -> list[tuple[int, str]]:
    """Return ``(line, expression)`` pairs that climb above the owning pack.

    *inv* supplies the per-invocation confinement memo and the packs root. It is
    optional so the self-test can call this directly with an off-tree path — the
    one shape no fixture plant can reach, because the walk only visits paths
    under a pack's test tree.
    """
    packs_root = PACKS if inv is None else inv.context.packs_root
    try:
        tree = ast.parse(source, filename=str(test_file))
    except SyntaxError as exc:
        return [(exc.lineno or 1, f"unparseable Python: {exc.msg}")]
    pack = next(
        (parent for parent in test_file.parents if parent.parent == packs_root),
        None,
    )
    if pack is None:
        return [(1, "test is not below packs/<pack>/")]

    visitor = _PackTestPathVisitor(test_file, pack, tree, inv)
    visitor.visit(tree)
    hits = visitor.hits

    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)):
            values = node.elts
        elif isinstance(node, ast.Call):
            values = node.args
        else:
            continue
        strings = {
            item.value
            for item in values
            if isinstance(item, ast.Constant) and isinstance(item.value, str)
        }
        if {"rev-parse", "--show-toplevel"}.issubset(strings):
            hits.append((node.lineno, ast.unparse(node)))
    return sorted(set(hits))


def case_pack_tests_stay_in_pack(inv: BoundaryInventory, out: list[str]) -> str | None:
    """Pack tests may inspect only their owning pack and temporary fixtures.

    Note this walk is deliberately NOT ignore-filtered: it uses a raw `os.walk`
    so a gitignored `.py` under a pack's test tree is still checked for climbing
    above its owning pack. Applying the inventory's ignored set here would newly
    exempt those files from source confinement.
    """
    root = inv.context.root
    before = len(out)
    checked = 0
    for pack in inv.packs:
        tests = pack / "tests"
        if _is_linked_dir(tests):
            out.append(
                f"{_rel(tests, root)}: pack test root is linked — linked test "
                "sources are not inspected"
            )
            continue
        if not tests.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(str(tests), followlinks=False):
            directory = Path(dirpath)
            kept_dirs: list[str] = []
            for name in dirnames:
                child = directory / name
                if name in _TRANSIENT:
                    continue
                if _is_linked_dir(child):
                    out.append(
                        f"{_rel(child, root)}: pack test tree contains a linked "
                        "directory — linked test sources are not inspected"
                    )
                    continue
                kept_dirs.append(name)
            dirnames[:] = kept_dirs
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                test_file = directory / name
                if test_file.is_symlink():
                    out.append(
                        f"{_rel(test_file, root)}: pack test is a symlink — linked "
                        "test sources are not inspected"
                    )
                    continue
                checked += 1
                source = test_file.read_text(encoding="utf-8", errors="replace")
                for lineno, expression in _pack_test_escapes(
                    test_file, source, inv
                ):
                    out.append(
                        f"{_rel(test_file, root)}:{lineno}: pack test reaches above "
                        f"{_rel(pack, root)} via `{expression}` — move repository-level "
                        "coverage to tests/conformance or tests/roster, or anchor "
                        "pack-local coverage directly at its owning pack"
                    )
    if len(out) == before:
        return f"ok   [pack-tests-stay-in-pack] ({checked} Python files checked)"
    return None


# Runner call sites: one invocation per line is close enough, because every
# runner in this repo puts one pytest command on one line.
_RUNNER_FILES = (
    "Makefile",
    ".github/workflows/build-check.yml",
    ".github/workflows/catalogue-tooling-ci-gates.yml",
    ".github/workflows/docs.yml",
    "tools/test-all.py",
    "packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py",
)
# Two shapes, because runners write paths two ways. A shell/Make/argv form
# (`packs/converters/tests/skills/x`), possibly with a `*` in the pack segment;
# and `self_host_windows.py`'s `root / "packs" / "atlassian" / "tests" / …`
# Path-part sequence, which no substring match can see — the spec records that
# same fact about grepping it.
_DEST = re.compile(r"packs/[A-Za-z0-9_*-]+/tests(?:/[A-Za-z0-9_.*/-]*)?")
_DEST_PARTS = re.compile(
    r'"packs"\s*/\s*"([A-Za-z0-9_-]+)"\s*/\s*"tests"((?:\s*/\s*"[A-Za-z0-9_-]+")*)'
)
_PART = re.compile(r'"([A-Za-z0-9_-]+)"')
_PYTEST = re.compile(r"(?:^|[\s\"'])pytest(?:$|[\s\"'])")

# Directories with no runner, and why. A destination directory must either be
# named by a runner or appear here — that is what keeps "which suites actually
# run" answerable from the tree rather than from a frozen spec note. Removing an
# entry whose directory is gone is part of deleting the suite.
_NO_RUNNER = {
    "packs/architect/tests/skills/architect-diagram":
        "needs the Mermaid CLI (mmdc); never gated",
    "packs/atlassian/tests/skills/confluence-publisher": "never gated",
    "packs/atlassian/tests/skills/jira-align": "never gated",
    "packs/atlassian/tests/skills/jira-team-status":
        "run by tools/check-atlassian-phase3-readiness.py, which no workflow invokes",
    "packs/converters/tests/skills/render-proof":
        "no CI exists for pack-level JavaScript; see pack-js-ci-workflow",
    "packs/figma/tests/skills/figma": "never gated",
    "packs/governance-extras/tests/skills/new-adr": "never gated",
    "packs/governance-extras/tests/skills/new-rfc": "never gated",
}


def _test_basenames(d: Path) -> set[str]:
    """Test module basenames in *d*.

    `conftest.py` is excluded deliberately: one per directory is pytest's design
    and every destination has one, so including it would make every multi-
    directory invocation look like a collision for a reason that is not true.
    """
    return {p.name for p in _walk(d)
            if p.is_file() and p.name != "conftest.py"}


def _covered(line_paths: set[str], destinations: list[Path],
             root: Path | None = None) -> set[Path]:
    """Destination directories a set of matched path tokens covers.

    A token may be a glob (`packs/*/tests/`) or an ancestor
    (`packs/converters/tests/`); either way it covers every destination beneath
    it, which is exactly how one invocation ends up spanning several skills.
    """
    base = ROOT if root is None else root
    covered: set[Path] = set()
    for token in line_paths:
        for d in destinations:
            rel = _rel(d, base)
            if fnmatch(rel, token.rstrip("/")) or fnmatch(rel, token.rstrip("/") + "/*") \
               or rel.startswith(token.rstrip("/") + "/") or rel == token.rstrip("/"):
                covered.add(d)
    return covered


def _path_tokens(text: str) -> set[str]:
    """Pack-test paths named by one command or structured invocation."""
    tokens = set(_DEST.findall(text))
    normalized = text.replace("'", '"')
    for pack, tail in _DEST_PARTS.findall(normalized):
        parts = _PART.findall(tail)
        tokens.add("/".join(["packs", pack, "tests", *parts]))
    return tokens


def _workflow_runner_lines(
    rel: str,
    source: str,
) -> list[tuple[str, int, set[str]]]:
    """Pytest commands in a workflow, paired with their step working directory."""
    out: list[tuple[str, int, set[str]]] = []
    working_tokens: set[str] = set()
    lines = source.splitlines()
    pytest_helpers: set[str] = set()
    for index, line in enumerate(lines):
        definition = re.match(r"^\s*([A-Za-z_]\w*)\(\)\s*\(", line)
        if definition is None:
            continue
        indent = len(line) - len(line.lstrip())
        body: list[str] = []
        for candidate in lines[index + 1:]:
            if candidate.strip() == ")" and len(candidate) - len(candidate.lstrip()) == indent:
                break
            body.append(candidate)
        if any(_PYTEST.search(candidate) for candidate in body):
            pytest_helpers.add(definition.group(1))

    for lineno, line in enumerate(lines, 1):
        if re.match(r"^\s*-\s+name:", line):
            working_tokens = set()
        if re.match(r"^\s*working-directory:", line):
            working_tokens = _path_tokens(line)
        stripped = line.lstrip()
        helper_call = next(
            (name for name in pytest_helpers if stripped.startswith(name + " ")),
            None,
        )
        if not stripped.startswith("#") and (
            _PYTEST.search(line) or helper_call is not None
        ):
            tokens = _path_tokens(line) | working_tokens
            if tokens:
                out.append((rel, lineno, tokens))
    return out


def _python_runner_lines(
    rel: str,
    source: str,
    findings: list[str],
) -> list[tuple[str, int, set[str]]]:
    """Structured Python argv lists whose enclosing call record invokes pytest.

    A parse failure is appended to *findings* rather than emitted, so the parse
    can be memoised while both consuming checks still report it.
    """
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as exc:
        findings.append(f"runner file {rel} is not parseable: {exc}")
        return []
    out: list[tuple[str, int, set[str]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Tuple):
            continue
        command_lists = [item for item in node.elts if isinstance(item, ast.List)]
        if not any(
            any(
                isinstance(item, ast.Constant) and item.value == "pytest"
                for item in command.elts
            )
            for command in command_lists
        ):
            continue
        tokens = _path_tokens(ast.unparse(node))
        if tokens:
            out.append((rel, node.lineno, tokens))
    return out


def _parse_runner_files(
    context: BoundaryContext,
) -> tuple[list[tuple[str, int, set[str]]], list[str]]:
    """Read and parse every runner file **once**, returning lines and findings.

    The findings are returned, not emitted. Both `runners-keep-suites-isolated`
    and `every-suite-dir-has-a-runner` consume this, and today a missing runner
    file produces one finding per consumer — two in total, suppressing both
    checks' `ok` lines. Memoising the parse must not collapse that to one, so the
    report stays the caller's job.
    """
    out: list[tuple[str, int, set[str]]] = []
    findings: list[str] = []
    for rel in context.runner_files:
        f = context.root / rel
        if not f.is_file():
            findings.append(
                f"runner file {rel} does not exist — the collision and coverage "
                f"checks silently stop reading it; update _RUNNER_FILES"
            )
            continue
        source = f.read_text(encoding="utf-8", errors="replace")
        if f.suffix in {".yml", ".yaml"}:
            out.extend(_workflow_runner_lines(rel, source))
            continue
        if f.suffix == ".py":
            out.extend(_python_runner_lines(rel, source, findings))
            continue
        for lineno, line in enumerate(source.splitlines(), 1):
            if line.lstrip().startswith("#") or not _PYTEST.search(line):
                continue
            if tokens := _path_tokens(line):
                out.append((rel, lineno, tokens))
    return out, findings


def case_runners_keep_suites_isolated(inv: BoundaryInventory, out: list[str]) -> str | None:
    """One pytest process per skill test directory — a correctness requirement.

    Overlapping basenames *across* destination directories are expected, and a
    newly added collision must not be what finally makes a broad runner fail.
    The assertion is therefore about invocation shape, not today's filenames.
    """
    before = len(out)
    destinations = inv.destinations()
    checked = 0
    runner_lines, runner_findings = inv.runner_lines()
    out.extend(runner_findings)
    for rel, lineno, tokens in runner_lines:
        covered = sorted(_covered(tokens, destinations, inv.context.root))
        if len(covered) < 2:
            continue
        checked += 1
        out.append(
            f"{rel}:{lineno}: one pytest invocation covers multiple skill "
            f"suites {[str(_rel(path, inv.context.root)) for path in covered]} "
            f"— split it into "
            "one process per skill directory before a test or subject module "
            "collision can pass green"
        )
    if len(out) == before:
        return (f"ok   [runners-keep-suites-isolated] "
                f"({checked} multi-directory invocation(s) checked)")
    return None


def case_every_suite_dir_has_a_runner(inv: BoundaryInventory, out: list[str]) -> str | None:
    """Every destination is named by a runner, or declared unrun with a reason.

    Without this the answer to "which suites actually run" lives only in a spec
    note, which freezes when the spec ships — so the next pack's test directory
    is unrun by default and nothing says so.
    """
    before = len(out)
    destinations = inv.destinations()
    if not destinations:
        out.append("no skill test directories found — this must not pass "
                        "vacuously")
        return None
    runner_lines, runner_findings = inv.runner_lines()
    out.extend(runner_findings)
    run: set[Path] = set()
    for _, _, tokens in runner_lines:
        run |= _covered(tokens, destinations, inv.context.root)
    for d in destinations:
        rel = _rel(d, inv.context.root)
        if d in run:
            if rel in inv.context.no_runner:
                out.append(
                    f"{rel} is declared unrun in _NO_RUNNER but a runner names "
                    f"it — drop the entry"
                )
            continue
        if rel not in inv.context.no_runner:
            out.append(
                f"{rel} holds a suite that no runner names. Wire it, or add it "
                f"to _NO_RUNNER with the reason — a suite nobody runs must be "
                f"declared, not discovered."
            )
    live = {_rel(d, inv.context.root) for d in destinations}
    for rel in sorted(set(inv.context.no_runner) - live):
        out.append(
            f"_NO_RUNNER names {rel}, which holds no suite — a stale exemption "
            f"hides the next directory that goes missing"
        )
    if len(out) == before:
        return (f"ok   [every-suite-dir-has-a-runner] "
                f"({len(destinations)} destinations, "
                f"{len(inv.context.no_runner)} declared unrun)")
    return None


class Check(NamedTuple):
    """One named check, in the order the terminal gate runs them."""

    name: str
    run: object


CHECKS: tuple[Check, ...] = (
    Check("apm-carries-no-tests", case_apm_carries_no_tests),
    Check("projection-carries-no-tests", case_projection_carries_no_tests),
    Check("tests-live-in-the-pack-tree", case_tests_live_in_the_pack_tree),
    Check("pack-tests-stay-in-pack", case_pack_tests_stay_in_pack),
    Check("runners-keep-suites-isolated", case_runners_keep_suites_isolated),
    Check("every-suite-dir-has-a-runner", case_every_suite_dir_has_a_runner),
)
CHECK_NAMES: tuple[str, ...] = tuple(check.name for check in CHECKS)


@dataclass(frozen=True)
class Finding:
    """One structured failure. `check` records which check produced it."""

    check: str
    message: str


@dataclass(frozen=True)
class CheckResult:
    """One check's outcome: its findings, and its success-line payload.

    `summary` exists because each `ok   [check] (…)` line embeds counters only
    that check computes. Returning it instead of printing it is what lets the
    callable API stay genuinely silent — the CLI does the printing.
    """

    check: str
    findings: tuple[Finding, ...]
    summary: str | None = None


def inspect_boundary(
    context: BoundaryContext,
    checks: Collection[str] | None = None,
) -> tuple[Finding, ...]:
    """Findings from the selected checks, in emission order.

    A thin wrapper over :func:`inspect_boundary_results` for callers that only
    want findings.
    """
    return tuple(
        finding
        for result in inspect_boundary_results(context, checks)
        for finding in result.findings
    )


def inspect_boundary_results(
    context: BoundaryContext,
    checks: Collection[str] | None = None,
) -> tuple[CheckResult, ...]:
    """Run the selected checks and return a :class:`CheckResult` for each.

    Side-effect-free: parses no arguments, prints nothing, calls no `sys.exit`,
    and mutates no file. The CLI is a thin formatter over this.

    Raises:
        ValueError: an unrecognised check name, or a selection that resolves to
            no checks — either would otherwise be a zero-finding exit 0 that
            reads as a pass.
    """
    if checks is not None:
        unknown = sorted(set(checks) - set(CHECK_NAMES))
        if unknown:
            raise ValueError(
                f"unrecognised check(s) {unknown}; accepted: "
                f"{list(CHECK_NAMES)}"
            )
        if not set(checks):
            raise ValueError(
                f"no checks selected; accepted: {list(CHECK_NAMES)}"
            )
    selected = [c for c in CHECKS if checks is None or c.name in set(checks)]

    inventory = build_inventory(context)
    results: list[CheckResult] = []
    for check in selected:
        emitted: list[str] = []
        summary = check.run(inventory, emitted)
        results.append(CheckResult(
            check=check.name,
            findings=tuple(Finding(check.name, m) for m in emitted),
            summary=summary,
        ))
    degraded_findings: list[Finding] = []
    if inventory.ignore_degraded:
        # Not cosmetic. `_walk` subtracts the ignored set and two findings fire
        # on the emptiness of what remains, so an unresolved ignore layer turns
        # those failures into passes. Refuse to report such a verdict.
        cause = (
            "git rejected the candidate batch"
            if inventory.ignore_refused else
            "git is unavailable"
        )
        remedy = (
            "a candidate was unusable — see the detail above"
            if inventory.ignore_refused else
            "re-run where git works"
        )
        degraded_findings.append(Finding(
            "ignore-layer",
            f"{cause}, so which paths are ignored could not be resolved "
            f"({inventory.ignore_detail}); the ignore-derived verdicts in this "
            f"run would be unsound, so no pass is reported. {remedy}.",
        ))
        results.append(CheckResult("ignore-layer",
                                   tuple(degraded_findings), None))
    return tuple(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Assert the runtime export boundary holds for every pack.",
    )
    parser.add_argument(
        "--check", action="append", dest="checks", metavar="NAME",
        choices=CHECK_NAMES,
        help="run only this check (repeatable). Default: all six, in order.",
    )
    parser.add_argument(
        "--root", default=None, metavar="PATH",
        help="catalogue root to inspect (default: this repository). A scoped "
             "run is marked partial and never prints the six-check pass line.",
    )
    args = parser.parse_args(argv)

    if args.root is None:
        context = default_context()
    else:
        try:
            root = Path(args.root).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            print(f"✖ --root {args.root!r} cannot be resolved: {exc}",
                  file=sys.stderr)
            return 2
        if _is_linked_dir(Path(args.root)):
            print(f"✖ --root {args.root!r} is a symlink or junction; a linked "
                  f"root is not inspected", file=sys.stderr)
            return 2
        context = default_context(root)
        # Refuse a root that cannot possibly be a catalogue, before walking it.
        missing = [
            label for label, path in (
                ("packs/", context.packs_root),
                ("the self-host recipe", context.recipe_path),
            ) if not path.exists()
        ]
        if missing:
            print(f"✖ --root {args.root!r} is missing {' and '.join(missing)} — "
                  f"refusing to walk it", file=sys.stderr)
            return 2

    partial = args.checks is not None or args.root is not None
    ran = list(args.checks) if args.checks else list(CHECK_NAMES)
    # Printed before the checks run, so it heads the output rather than
    # trailing the per-check `ok` lines those checks emit themselves.
    if partial:
        print(f"partial run — checks: {', '.join(ran)}"
              + (f" — root: {args.root}" if args.root else ""))
    try:
        results = inspect_boundary_results(context, args.checks)
    except ValueError as exc:
        # Reached only if `choices=` is ever relaxed; argparse rejects an unknown
        # name at exit 2 today. Kept so the API's contract has a CLI-side answer
        # rather than a traceback if that changes.
        print(f"✖ {exc}", file=sys.stderr)
        return 2

    # The CLI owns every byte of output. Each check returned its own success
    # line because only it can compute the counters in it; printing them here,
    # in check order, is what keeps the API silent without changing stdout.
    findings = [f for result in results for f in result.findings]
    for result in results:
        if result.summary is not None:
            print(result.summary)

    print()
    if findings:
        for finding in findings:
            print(f"FAIL: {finding.message}", file=sys.stderr)
        print(f"✖ lint-pack-test-boundary: {len(findings)} failure(s)",
              file=sys.stderr)
        return 1
    if partial:
        print(f"✓ lint-pack-test-boundary: passed ({len(ran)} of "
              f"{len(CHECKS)} checks — partial run).")
        return 0
    print("✓ lint-pack-test-boundary: passed (6 cases).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
