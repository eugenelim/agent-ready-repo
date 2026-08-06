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

Four checks:

1. **apm-carries-no-tests** — no pack's `.apm/` holds test content.
2. **projection-carries-no-tests** — no projected skill does either, asserted
   per pack against the self-host recipe's include list so a pack dropping out
   of the projection fails rather than passing on an empty iteration.
3. **tests-live-in-the-pack-tree** — a pack that owns tests has them under
   `packs/<pack>/tests/`.
4. **runners-keep-suites-isolated** — no single pytest invocation covers two
   destination directories whose test basenames overlap. Several skills ship a
   `test_render.py` and a `render.py`; pytest refuses the duplicate test
   basenames outright, and a sys.path-based sibling import would bind one
   module for all of them.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

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

# `__pycache__` and friends are gitignored build residue, not authored content.
# They are a real packaging problem — `package.py` walks `packs/**` and applies
# no denylist — but that belongs to `package-archive-carries-pycache` in the
# backlog, not to the source-tree boundary this lint owns.
_TRANSIENT = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache",
                        ".ruff_cache", "node_modules"})

FAILURES: list[str] = []


def _walk(base: Path) -> list[Path]:
    """Authored test content under *base*.

    Uses `os.walk(followlinks=False)` with an explicit symlink prune, matching
    `catalogue_tooling/package.py`'s archive walk. The lint and the walker that
    decides what actually ships must not hold two different definitions of what
    pack content is — and `Path.rglob`'s symlink behaviour changed across the
    3.12/3.13 boundary.
    """
    found: list[Path] = []
    if not base.is_dir():
        return found
    for dirpath, dirnames, filenames in os.walk(str(base), followlinks=False):
        dp = Path(dirpath)
        dirnames[:] = [
            dn for dn in dirnames
            if dn not in _TRANSIENT and dn not in _SKIP_DIR
            and not (dp / dn).is_symlink()
        ]
        for dn in dirnames:
            if dn in _TEST_DIR:
                found.append(dp / dn)
        for fn in filenames:
            p = dp / fn
            if _TEST_FILE.match(fn) and not p.is_symlink():
                found.append(p)
    return [p for p in found if not _is_ignored(p)]


def _is_ignored(path: Path) -> bool:
    """A locally-generated, gitignored file is not a boundary violation."""
    try:
        return subprocess.run(
            ["git", "check-ignore", "-q", "--", str(path)],
            cwd=ROOT, capture_output=True, check=False,
        ).returncode == 0
    except FileNotFoundError:
        return False  # no git available — judge every file on disk


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def _packs() -> list[Path]:
    return sorted(p for p in PACKS.iterdir()
                  if p.is_dir() and not p.name.startswith("_")
                  and (p / "pack.toml").is_file())


def _projected_packs() -> list[str]:
    """Packs this repo projects, per the self-host recipe's include list.

    Only these can be checked by the projection half; the rest are advertised
    through `marketplace.json` but never written into this tree.
    """
    if not RECIPE.is_file():
        FAILURES.append(f"self-host recipe not found at {_rel(RECIPE)}")
        return []
    data = tomllib.loads(RECIPE.read_text(encoding="utf-8"))
    return list(data.get("recipe", {}).get("packs", {}).get("include", []))


def case_apm_carries_no_tests() -> None:
    hits: list[Path] = []
    for pack in _packs():
        hits += _walk(pack / ".apm")
    if hits:
        FAILURES.append(
            "a pack's .apm/ is the runtime export boundary but carries test "
            "content:\n    " + "\n    ".join(_rel(h) for h in hits)
            + "\n  Move it to packs/<pack>/tests/ — see "
              "catalogue-authoring-standards.md § 4."
        )
        return
    print(f"ok   [apm-carries-no-tests] ({len(_packs())} packs)")


def case_projection_carries_no_tests() -> None:
    """The installed artifact, checked directly rather than inferred."""
    include = _projected_packs()
    if not include:
        FAILURES.append("self-host recipe lists no packs to project")
        return
    adapter_roots = [r for r in (ROOT / ".claude" / "skills",
                                 ROOT / ".agents" / "skills") if r.is_dir()]
    if not adapter_roots:
        FAILURES.append(
            "no projected skills tree found under .claude/skills or "
            ".agents/skills — run `make build-self`; this check must not pass "
            "vacuously"
        )
        return
    hits: list[Path] = []
    total = 0
    for name in include:
        skills_dir = PACKS / name / ".apm" / "skills"
        if not skills_dir.is_dir():
            continue
        skills = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())
        checked = 0
        for adapter_root in adapter_roots:
            for skill in skills:
                projected = adapter_root / skill
                if projected.is_dir():
                    checked += 1
                    hits += _walk(projected)
        if not checked:
            FAILURES.append(
                f"pack {name!r} is in the self-host include list but none of its "
                f"skills is projected — a pack dropping out of the projection "
                f"must fail here, not pass on an empty iteration"
            )
        total += checked
    if hits:
        FAILURES.append(
            f"projected skills carry test content ({total} checked):\n    "
            + "\n    ".join(_rel(h) for h in hits)
        )
        return
    if not FAILURES:
        print(f"ok   [projection-carries-no-tests] ({total} projected skills, "
              f"{len(include)} packs)")


def case_tests_live_in_the_pack_tree() -> None:
    """The positive half — a pack that owns tests has them where policy says."""
    owning = 0
    for pack in _packs():
        tests = pack / "tests"
        if not tests.is_dir():
            continue                      # a pack may legitimately own no tests
        suites = _walk(tests)
        if not suites:
            FAILURES.append(
                f"{_rel(tests)} exists but holds no test content — an empty "
                f"test tree is a lost move, not a clean pack"
            )
            continue
        owning += 1
    if not FAILURES:
        print(f"ok   [tests-live-in-the-pack-tree] ({owning} packs own tests)")


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
_DEST = re.compile(r"packs/[A-Za-z0-9_-]+/tests(?:/[A-Za-z0-9_./-]*)?")


def _test_basenames(d: Path) -> set[str]:
    return {p.name for p in d.rglob("*")
            if p.is_file() and _TEST_FILE.match(p.name)
            and not (_TRANSIENT & set(p.parts))}


def case_runners_keep_suites_isolated() -> None:
    """One pytest process per skill test directory — a correctness requirement.

    Overlapping basenames *across* destination directories are the expected end
    state (three skills ship a `test_render.py`), so the assertion is about what
    a single invocation covers, not about the tree.
    """
    checked = 0
    for rel in _RUNNER_FILES:
        f = ROOT / rel
        if not f.is_file():
            continue
        for lineno, line in enumerate(f.read_text(encoding="utf-8",
                                                  errors="replace").splitlines(), 1):
            if "pytest" not in line:
                continue
            paths = {ROOT / m for m in _DEST.findall(line)}
            dirs = sorted({p if p.is_dir() else p.parent for p in paths})
            if len(dirs) < 2:
                continue
            checked += 1
            for i, a in enumerate(dirs):
                for b in dirs[i + 1:]:
                    overlap = _test_basenames(a) & _test_basenames(b)
                    if overlap:
                        FAILURES.append(
                            f"{rel}:{lineno}: one pytest invocation covers "
                            f"{_rel(a)} and {_rel(b)}, which share test "
                            f"basenames {sorted(overlap)}. pytest refuses "
                            f"duplicate basenames; split the invocation."
                        )
    if not FAILURES:
        print(f"ok   [runners-keep-suites-isolated] "
              f"({checked} multi-directory invocation(s) checked)")


def main() -> int:
    for case in (case_apm_carries_no_tests,
                 case_projection_carries_no_tests,
                 case_tests_live_in_the_pack_tree,
                 case_runners_keep_suites_isolated):
        case()
    print()
    if FAILURES:
        for f in FAILURES:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"✖ lint-pack-test-boundary: {len(FAILURES)} failure(s)",
              file=sys.stderr)
        return 1
    print("✓ lint-pack-test-boundary: passed (4 cases).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
