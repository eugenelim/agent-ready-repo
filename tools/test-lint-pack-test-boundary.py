#!/usr/bin/env python3
"""Self-test for `tools/lint-pack-test-boundary.py`.

Three layers:

1. **Falsification, both directions.** Plant a test file under a non-`core`
   pack's `.apm/` and the lint must fail; remove it and it must pass. A guard
   that has never been seen to fail is a guard nobody has checked.
2. **Matcher shapes.** Every shape `_TEST_FILE` and `_TEST_DIR` claim is
   asserted to match, and every documented narrowing is asserted *not* to. The
   widened matcher must be a superset of the one it replaced — the previous
   version could not see `*.test.js`, which is how three files sat under `.apm/`
   through an entire migration without anyone noticing.
3. **Runner isolation.** The collision check keys on what a single invocation
   covers, not on the tree: overlapping basenames across destination directories
   are the intended end state, so a lint that reds on those would red on a
   correct implementation.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
LINT = ROOT / "tools" / "lint-pack-test-boundary.py"
if not LINT.is_file():
    raise SystemExit(f"lint not found at {LINT}")


def _load():
    spec = importlib.util.spec_from_file_location("lint_pack_test_boundary", LINT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["lint_pack_test_boundary"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run() -> int:
    return subprocess.run([sys.executable, str(LINT)],
                          cwd=ROOT, capture_output=True, text=True).returncode


# Shapes the matcher must catch, and the ones it must deliberately not.
_MATCH = [
    "conftest.py",
    "test_foo.py", "test-foo.py", "test_foo.sh", "test-foo.js", "test_foo.ts",
    "test_foo.go", "test_foo.ps1", "test_foo.rb", "test_foo.mjs", "test_foo.cjs",
    "foo_test.py", "foo-test.js", "foo_test.go", "foo_test.rb",
    "renderer.test.js", "renderer.spec.ts", "pipeline.test.tsx",
]
_NO_MATCH = [
    # A bare `test` substring would false-positive on reference material about
    # testing — the narrowing is deliberate.
    "test-fixtures.md", "testing-strategy.md", "contest.py", "latest.json",
    "SKILL.md", "evals.json", "eval_queries.json", "render.py", "protest.py",
]
_MATCH_DIR = ["tests", "test", "__tests__", "spec"]
_NO_MATCH_DIR = ["evals", "scripts", "references", "assets", "seeds"]


def main() -> int:
    mod = _load()
    failures: list[str] = []
    cases = 0

    # ---- layer 2: matcher shapes ------------------------------------------
    for name in _MATCH:
        cases += 1
        if not mod._TEST_FILE.match(name):
            failures.append(f"_TEST_FILE should match {name!r}")
    for name in _NO_MATCH:
        cases += 1
        if mod._TEST_FILE.match(name):
            failures.append(f"_TEST_FILE should NOT match {name!r}")
    for name in _MATCH_DIR:
        cases += 1
        if name not in mod._TEST_DIR:
            failures.append(f"_TEST_DIR should contain {name!r}")
    for name in _NO_MATCH_DIR:
        cases += 1
        if name in mod._TEST_DIR:
            failures.append(f"_TEST_DIR should NOT contain {name!r}")

    # The widened matcher must be a strict superset of the one it replaced.
    cases += 1
    for name in ("test_x.py", "test-x.sh", "x_test.js", "x-test.ts"):
        if not mod._TEST_FILE.match(name):
            failures.append(
                f"widened matcher lost {name!r} — the previous matcher caught it"
            )

    # ---- layer 1: falsification, both directions ---------------------------
    cases += 1
    if _run() != 0:
        failures.append("clean tree: expected exit 0")

    # Plant under a non-core pack, so the check is proven repo-wide and not just
    # for the pack the guard used to be scoped to.
    plant_dir = ROOT / "packs" / "figma" / ".apm" / "skills" / "figma" / "scripts"
    plant = plant_dir / "test_planted_boundary_violation.py"
    if not plant_dir.is_dir():
        failures.append(f"plant target missing: {plant_dir}")
    else:
        cases += 1
        plant.write_text("# planted by test-lint-pack-test-boundary.py\n",
                         encoding="utf-8")
        try:
            if _run() == 0:
                failures.append(
                    "planted test under packs/figma/.apm/: expected exit 1"
                )
        finally:
            plant.unlink(missing_ok=True)
        cases += 1
        if _run() != 0:
            failures.append("after removing the plant: expected exit 0")

    # A `test/` directory (singular) is the shape the previous matcher missed.
    plant2 = plant_dir / "test"
    cases += 1
    plant2.mkdir(exist_ok=True)
    try:
        if _run() == 0:
            failures.append(
                "planted `test/` dir under packs/figma/.apm/: expected exit 1"
            )
    finally:
        plant2.rmdir()

    # ---- layer 3: runner isolation ----------------------------------------
    # Overlapping basenames across destinations are expected; the lint must key
    # on what one invocation covers. Assert both halves against the real tree.
    cases += 1
    docx = ROOT / "packs/converters/tests/skills/markdown-to-docx"
    pptx = ROOT / "packs/converters/tests/skills/markdown-to-pptx"
    if docx.is_dir() and pptx.is_dir():
        overlap = mod._test_basenames(docx) & mod._test_basenames(pptx)
        if not overlap:
            failures.append(
                "expected markdown-to-docx and markdown-to-pptx to share a test "
                "basename — the collision case this lint guards has vanished, so "
                "the guard is no longer proving anything"
            )
        elif _run() != 0:
            failures.append(
                "the tree has overlapping basenames across destinations and the "
                "lint failed — it must key on invocations, not on the tree"
            )
    else:
        failures.append("collision fixtures not found in the tree")

    for f in failures:
        sys.stderr.write(f"FAIL {f}\n")
    if failures:
        return 1
    sys.stderr.write(f"ok — {cases} cases passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
