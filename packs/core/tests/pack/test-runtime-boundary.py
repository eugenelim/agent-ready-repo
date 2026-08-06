#!/usr/bin/env python3
"""Asserts the core pack's runtime export boundary holds.

`.apm/` is what gets projected into an installed agent environment, so nothing
that is not runtime content may live there. That rule survived for a long time
only because the installer happens to read `seeds/` and `.apm/` and ignore
everything else — an implicit exclusion, not a structural one. This suite makes
it structural: it fails when a test file appears under `packs/core/.apm/`, and
when one appears in a projected core skill.

Checking the projection *positively* is the point. Inferring "no tests are
installed" from "the installer ignores those paths" is exactly the reasoning
that let the violation persist; a future adapter that copies `.apm/**` wholesale
would break the inference without breaking any test.

Scope is the core pack. The other packs still hold tests under
`.apm/skills/*/scripts/` — tracked in `workspace.toml [backlog].open` as
`pack-test-boundary-remaining-packs` — so a repo-wide assertion would fail on
deferred work rather than on a regression.

`evals/` is deliberately not flagged: eval fixtures are skill-local runtime
content and are projected with the skill by design.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Windows cp1252 guard — reconfigure stdout/stderr to UTF-8 before any print.
sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[1]                      # packs/core
ROOT = HERE.parents[3]                      # repo root
if not (PACK / ".apm").is_dir():            # wrong parents[] depth after a move
    raise SystemExit(f"pack root not found at {PACK} — check the parents[] depth")

# `test_x.py`, `test-x.py`, `x_test.py`, `tests/` — the shapes a test actually
# takes here. Deliberately not a bare "test" substring: `test-fixtures.md` as
# reference material for a skill *about* testing would be a false positive.
_TEST_FILE = re.compile(r"^(test[-_].+|.+[-_]test)\.(py|sh|js|ts)$")
_TEST_DIR = frozenset({"tests"})

# `__pycache__` and `.pytest_cache` are gitignored build residue, not authored
# content — running a suite twice would otherwise red this check. They are a
# real packaging problem (the archive walks `packs/**` and `package.py` never
# applies its own denylist), but that belongs to `package-archive-carries-pycache`
# in the backlog, not to the source-tree boundary this suite owns.
_TRANSIENT = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})

FAILURES: list[str] = []


def _walk(base: Path) -> list[Path]:
    """Authored test content under *base*, ignoring gitignored build residue."""
    found: list[Path] = []
    for path in sorted(base.rglob("*")):
        if _TRANSIENT & set(path.parts):
            continue
        if path.is_dir():
            if path.name in _TEST_DIR:
                found.append(path)
        elif _TEST_FILE.match(path.name) and not _is_ignored(path):
            found.append(path)
    return found


def _is_ignored(path: Path) -> bool:
    """A locally-generated, gitignored file is not a boundary violation."""
    try:
        return subprocess.run(
            ["git", "check-ignore", "-q", str(path)],
            cwd=ROOT, capture_output=True, check=False,
        ).returncode == 0
    except FileNotFoundError:
        return False  # no git available — judge every file on disk


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def case_apm_carries_no_tests() -> None:
    hits = _walk(PACK / ".apm")
    if hits:
        FAILURES.append(
            "core pack's .apm/ is the runtime export boundary but carries "
            "test content:\n    " + "\n    ".join(_rel(h) for h in hits)
            + "\n  Move it to packs/core/tests/ — see catalogue-authoring-standards.md § 4."
        )
        return
    print("ok   [apm-carries-no-tests]")


def case_projection_carries_no_tests() -> None:
    """The installed artifact, checked directly rather than inferred."""
    skills = sorted(p.name for p in (PACK / ".apm" / "skills").iterdir() if p.is_dir())
    if not skills:
        FAILURES.append("no core skills found — check the pack root")
        return
    checked = 0
    hits: list[Path] = []
    for adapter_root in (ROOT / ".claude" / "skills", ROOT / ".agents" / "skills"):
        if not adapter_root.is_dir():
            continue  # that adapter hasn't been projected in this checkout
        for skill in skills:
            projected = adapter_root / skill
            if not projected.is_dir():
                continue
            checked += 1
            hits += _walk(projected)
    if not checked:
        FAILURES.append(
            "no projected core skill found under .claude/skills or .agents/skills "
            "— run `make build-self`; this check must not pass vacuously"
        )
        return
    if hits:
        FAILURES.append(
            f"projected core skills carry test content ({checked} checked):\n    "
            + "\n    ".join(_rel(h) for h in hits)
        )
        return
    print(f"ok   [projection-carries-no-tests] ({checked} projected skills checked)")


def case_tests_live_in_the_pack_tree() -> None:
    """The positive half — the tests exist where the policy says they do."""
    tests = PACK / "tests"
    if not tests.is_dir():
        FAILURES.append(f"{_rel(tests)} does not exist")
        return
    suites = [p for p in tests.rglob("*") if _TEST_FILE.match(p.name)]
    if len(suites) < 10:
        FAILURES.append(
            f"expected the core pack's relocated suites under {_rel(tests)}, "
            f"found {len(suites)} — did a move lose one?"
        )
        return
    print(f"ok   [tests-live-in-the-pack-tree] ({len(suites)} suites)")


def main() -> int:
    for case in (case_apm_carries_no_tests,
                 case_projection_carries_no_tests,
                 case_tests_live_in_the_pack_tree):
        case()
    print()
    if FAILURES:
        for f in FAILURES:
            print(f"FAIL: {f}", file=sys.stderr)
        print(f"✖ test-runtime-boundary: {len(FAILURES)} failure(s)", file=sys.stderr)
        return 1
    print("✓ test-runtime-boundary: passed (3 cases).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
