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


def _run() -> tuple[int, str]:
    """(exit code, stderr). The reason matters: the lint has several failure
    sites, so `exit != 0` alone would let a plant "pass" on an unrelated fault."""
    r = subprocess.run([sys.executable, str(LINT)],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode, r.stderr


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
    rc, err = _run()
    if rc != 0:
        failures.append(f"clean tree: expected exit 0, got {rc}\n{err}")

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
            rc, err = _run()
            if rc == 0:
                failures.append(
                    "planted test under packs/figma/.apm/: expected exit 1"
                )
            elif plant.name not in err:
                failures.append(
                    "planted test under packs/figma/.apm/: lint failed, but its "
                    f"message does not name the plant — it failed for another "
                    f"reason:\n{err}"
                )
        finally:
            plant.unlink(missing_ok=True)
        cases += 1
        rc, err = _run()
        if rc != 0:
            failures.append(f"after removing the plant: expected exit 0\n{err}")

    # A `test/` directory (singular) is the shape the previous matcher missed.
    plant2 = plant_dir / "test"
    cases += 1
    plant2.mkdir(exist_ok=True)
    try:
        rc, err = _run()
        if rc == 0:
            failures.append(
                "planted `test/` dir under packs/figma/.apm/: expected exit 1"
            )
        elif "/test" not in err:
            failures.append(f"planted `test/` dir: failed for another reason\n{err}")
    finally:
        plant2.rmdir()

    # `evals/` untouchability is load-bearing (AC5) and is enforced by _SKIP_DIR,
    # not by _TEST_DIR — so asserting `"evals" not in _TEST_DIR` proves nothing.
    # Plant a test file inside a real evals/ tree and require it to be ignored.
    evals = ROOT / "packs" / "figma" / ".apm" / "skills" / "figma" / "evals"
    cases += 1
    if evals.is_dir():
        ep = evals / "test_planted_in_evals.py"
        ep.write_text("# planted\n", encoding="utf-8")
        try:
            rc, err = _run()
            if rc != 0:
                failures.append(
                    "a test file inside evals/ must be ignored — evals are "
                    f"skill-local runtime content (ADR-0071):\n{err}"
                )
        finally:
            ep.unlink(missing_ok=True)
    else:
        failures.append(f"evals plant target missing: {evals}")

    # Case 4 and case 5 had never been seen to fail. Plant a runner line that
    # collects two colliding destinations, and an undeclared destination.
    mk = ROOT / "Makefile"
    original = mk.read_text(encoding="utf-8")
    cases += 1
    try:
        mk.write_text(
            original + "\nlint-selftest-scratch:\n"
            "\tpytest packs/converters/tests/skills/markdown-to-docx "
            "packs/converters/tests/skills/markdown-to-pptx\n",
            encoding="utf-8")
        rc, err = _run()
        if rc == 0:
            failures.append(
                "a runner covering markdown-to-docx + markdown-to-pptx must fail "
                "— they share test_render.py and render.py"
            )
        elif "render.py" not in err:
            failures.append(
                f"collision plant failed, but not for the subject-module "
                f"collision that matters:\n{err}"
            )
    finally:
        mk.write_text(original, encoding="utf-8")

    cases += 1
    undeclared = ROOT / "packs" / "figma" / "tests" / "skills" / "planted-skill"
    undeclared.mkdir(parents=True, exist_ok=True)
    (undeclared / "test_planted.py").write_text("def test_x():\n    pass\n",
                                                encoding="utf-8")
    try:
        rc, err = _run()
        if rc == 0:
            failures.append(
                "a destination directory named by no runner and absent from "
                "_NO_RUNNER must fail"
            )
        elif "planted-skill" not in err:
            failures.append(f"undeclared-destination plant failed elsewhere\n{err}")
    finally:
        (undeclared / "test_planted.py").unlink(missing_ok=True)
        undeclared.rmdir()

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
        else:
            rc, err = _run()
            if rc != 0:
                failures.append(
                    "the tree has overlapping basenames across destinations and "
                    f"the lint failed — it must key on invocations:\n{err}"
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
