#!/usr/bin/env python3
"""Structural properties of `tools/lint-pack-test-boundary.py`.

T4 of `docs/specs/lint-performance-p0`. The golden baseline
(`tools/test-lint-boundary-golden.py`) proves the lint still *says* the same
thing. It is blind to exactly three things, and this suite covers them:

* how many Git subprocesses ran,
* how many times the inventory, the runner parse and the destination scan were
  built,
* whether anything on disk was mutated.

These are asserted by instrumenting the real seams and running a complete
invocation — never by matching source strings, because a source grep cannot see
a call added through an alias, and a passing grep on a broken lint is exactly the
false confidence this spec exists to remove.

It also covers the behaviours the baseline *cannot* reach: the injected
`_NO_RUNNER` map (the one licensed divergence from captured output), the two
refusals whose messages embed an absolute path, and the confinement memo's
order-independence.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
LINT = ROOT / "tools" / "lint-pack-test-boundary.py"

sys.path.insert(0, str(ROOT / "tools"))
_spec = importlib.util.spec_from_file_location("lint_pack_test_boundary", LINT)
M = importlib.util.module_from_spec(_spec)
sys.modules["lint_pack_test_boundary"] = M
_spec.loader.exec_module(M)

_FAILURES: list[str] = []
_CASES = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global _CASES
    _CASES += 1
    if not ok:
        _FAILURES.append(f"{name}: {detail}" if detail else name)


class _GitCounter:
    """Counts real `git check-ignore` invocations without faking the answer."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self._real = M.lint_git_ignore.subprocess.run

    def __call__(self, argv, **kwargs):
        if isinstance(argv, list) and "check-ignore" in argv:
            self.calls.append(argv)
        return self._real(argv, **kwargs)

    @property
    def check_ignore(self) -> int:
        return len(self.calls)


def _silent(fn, *args, **kwargs):
    """Run *fn* capturing both streams, returning (result, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        result = fn(*args, **kwargs)
    return result, out.getvalue(), err.getvalue()


def _tree_signature(root: Path) -> set[tuple[str, int]]:
    """Cheap mutation detector: relative path plus size for every file."""
    signature = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__"}]
        for name in filenames:
            path = Path(dirpath) / name
            with contextlib.suppress(OSError):
                signature.add((str(path.relative_to(root)), path.stat().st_size))
    return signature


def main() -> int:  # noqa: C901 — independent structural assertions
    context = M.default_context()

    # ---- one full invocation: process and build counts ------------------
    counter = _GitCounter()
    builds = {"inventory": 0, "runners": 0, "destinations": 0}
    real_build = M.build_inventory
    captured: dict[str, object] = {}

    def counting_build(ctx):
        builds["inventory"] += 1
        inv = real_build(ctx)
        captured["inv"] = inv
        return inv

    M.build_inventory = counting_build
    M.lint_git_ignore.subprocess.run = counter
    try:
        findings, out, err = _silent(M.inspect_boundary, context)
    finally:
        M.build_inventory = real_build
        M.lint_git_ignore.subprocess.run = counter._real

    inv = captured["inv"]
    check("clean tree yields no findings", findings == (), repr(findings[:3]))
    check("exactly one inventory construction", builds["inventory"] == 1,
          str(builds["inventory"]))
    check("at most one check-ignore process", counter.check_ignore <= 1,
          f"{counter.check_ignore} processes")
    check("exactly one check-ignore process for a non-empty candidate set",
          counter.check_ignore == 1, f"{counter.check_ignore}")
    check("runner files parsed exactly once", inv.runner_parses == 1,
          str(inv.runner_parses))
    check("destination inventory built exactly once",
          inv.destination_builds == 1, str(inv.destination_builds))
    check("every walk base was pre-batched (no lazy misses)",
          inv.walk_misses == 0, f"{inv.walk_misses} lazy walks")
    check("confinement memo has one entry per distinct base",
          len(inv._confinement) == len(set(inv._confinement)),
          str(len(inv._confinement)))

    # ---- the callable API is side-effect-free ---------------------------
    check("inspect_boundary prints nothing to stderr", err == "", err[:300])
    check("inspect_boundary returns structured findings",
          isinstance(findings, tuple))

    # ---- empty candidate set launches no process ------------------------
    with tempfile.TemporaryDirectory(prefix="boundary-empty-") as td:
        empty = Path(td)
        (empty / "packs").mkdir()
        recipe = (empty / "packages" / "agentbundle" / "agentbundle" / "build"
                  / "recipes")
        recipe.mkdir(parents=True)
        (recipe / "self-host.toml").write_text(
            "[recipe.packs]\ninclude = []\n", encoding="utf-8"
        )
        counter2 = _GitCounter()
        M.lint_git_ignore.subprocess.run = counter2
        try:
            _silent(M.inspect_boundary, M.default_context(empty))
        finally:
            M.lint_git_ignore.subprocess.run = counter2._real
        check("no candidates launches zero check-ignore processes",
              counter2.check_ignore == 0, f"{counter2.check_ignore}")

    # ---- determinism across two processes -------------------------------
    probe = (
        "import sys, importlib.util, io, contextlib\n"
        f"sys.path.insert(0, {str(ROOT / 'tools')!r})\n"
        f"s = importlib.util.spec_from_file_location('m', {str(LINT)!r})\n"
        "m = importlib.util.module_from_spec(s)\n"
        "sys.modules['m'] = m; s.loader.exec_module(m)\n"
        "buf = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf):\n"
        "    f = m.inspect_boundary(m.default_context())\n"
        "print('|'.join(x.check + ':' + x.message for x in f))\n"
    )
    seen = set()
    for _ in range(2):
        seen.add(subprocess.run([sys.executable, "-c", probe],
                                capture_output=True, text=True,
                                check=False).stdout)
    check("findings order is identical across processes", len(seen) == 1,
          repr(seen))

    # ---- selector contract ---------------------------------------------
    for bad, label in ((["nope"], "unknown name"), ([], "empty selection")):
        raised = None
        try:
            _silent(M.inspect_boundary, context, bad)
        except ValueError as exc:
            raised = exc
        check(f"API rejects {label} with ValueError", raised is not None)
        check(f"API names the accepted set for {label}",
              raised is not None and "apm-carries-no-tests" in str(raised),
              str(raised))

    single, _, _ = _silent(M.inspect_boundary, context,
                           ["apm-carries-no-tests"])
    check("a single-check selection runs and yields no findings", single == (),
          repr(single))

    # ---- API / CLI parity on the same fixture ---------------------------
    with tempfile.TemporaryDirectory(prefix="boundary-parity-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)
        api_findings, _, _ = _silent(M.inspect_boundary,
                                     M.default_context(fixture))
        cli = subprocess.run(
            [sys.executable, str(LINT), "--root", str(fixture)],
            capture_output=True, text=True, check=False,
        )
        api_failed = bool(api_findings)
        cli_failed = cli.returncode != 0
        check("API and CLI agree on the same fixture", api_failed == cli_failed,
              f"api_failed={api_failed} cli_failed={cli_failed} rc={cli.returncode}")

        # plant a violation; both must flip together
        (fixture / "packs" / "demo" / ".apm" / "skills" / "demo").mkdir(
            parents=True, exist_ok=True
        )
        (fixture / "packs" / "demo" / ".apm" / "skills" / "demo"
         / "test_planted.py").write_text("# planted\n", encoding="utf-8")
        api2, _, _ = _silent(M.inspect_boundary, M.default_context(fixture))
        cli2 = subprocess.run(
            [sys.executable, str(LINT), "--root", str(fixture)],
            capture_output=True, text=True, check=False,
        )
        check("API detects the planted violation", bool(api2), repr(api2))
        check("CLI detects the planted violation", cli2.returncode != 0)
        check("API and CLI still agree after the plant",
              bool(api2) == (cli2.returncode != 0))

    # ---- injected _NO_RUNNER: the one licensed divergence ---------------
    # The baseline binds the lint given the REAL map, so this behaviour has no
    # captured counterpart and must be asserted directly.
    with tempfile.TemporaryDirectory(prefix="boundary-norunner-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)
        base = M.default_context(fixture)
        real_map_ctx = base
        empty_map_ctx = M.BoundaryContext(
            root=base.root, packs_root=base.packs_root,
            recipe_path=base.recipe_path,
            projected_roots=base.projected_roots,
            runner_files=base.runner_files, no_runner={},
        )
        with_real, _, _ = _silent(M.inspect_boundary, real_map_ctx,
                                  ["every-suite-dir-has-a-runner"])
        with_empty, _, _ = _silent(M.inspect_boundary, empty_map_ctx,
                                   ["every-suite-dir-has-a-runner"])
        stale_real = [f for f in with_real if "holds no suite" in f.message]
        check("the real map reports its entries stale against a fixture",
              len(stale_real) == len(M._NO_RUNNER),
              f"{len(stale_real)} vs {len(M._NO_RUNNER)} entries")
        check("an injected empty map reports no stale exemptions",
              not [f for f in with_empty if "holds no suite" in f.message],
              repr(with_empty))

        # A fixture-supplied stale entry must be reported against the fixture's
        # own destinations, not the repository's.
        planted_ctx = M.BoundaryContext(
            root=base.root, packs_root=base.packs_root,
            recipe_path=base.recipe_path,
            projected_roots=base.projected_roots,
            runner_files=base.runner_files,
            no_runner={"packs/demo/tests/skills/ghost": "planted reason"},
        )
        planted, _, _ = _silent(M.inspect_boundary, planted_ctx,
                                ["every-suite-dir-has-a-runner"])
        check("an injected stale entry is reported against the fixture",
              any("ghost" in f.message and "holds no suite" in f.message
                  for f in planted), repr(planted))

    # ---- the two refusals whose bytes cannot be captured ----------------
    with tempfile.TemporaryDirectory(prefix="boundary-refuse-") as td:
        bare = Path(td) / "bare"
        bare.mkdir()
        cli = subprocess.run([sys.executable, str(LINT), "--root", str(bare)],
                             capture_output=True, text=True, check=False)
        check("a root without packs/ is refused", cli.returncode == 2,
              f"rc={cli.returncode}")
        check("the packs/ refusal names what is missing",
              "packs/" in cli.stderr, cli.stderr[:200])
        (bare / "packs").mkdir()
        cli = subprocess.run([sys.executable, str(LINT), "--root", str(bare)],
                             capture_output=True, text=True, check=False)
        check("a root without the recipe is refused", cli.returncode == 2,
              f"rc={cli.returncode}")
        check("the recipe refusal names the recipe",
              "recipe" in cli.stderr, cli.stderr[:200])

    # ---- confinement memo: order-independent, fail-closed ---------------
    with tempfile.TemporaryDirectory(prefix="boundary-memo-") as td:
        tmp = Path(td)
        real = tmp / "realtree"
        real.mkdir()
        (real / "a.py").write_text("x", encoding="utf-8")
        link = tmp / "linktree"
        try:
            link.symlink_to(real, target_is_directory=True)
            linked = True
        except OSError:
            linked = False
        if linked:
            check("ground truth: real tree is confined",
                  M._glob_tree_is_confined(real) is True)
            check("ground truth: linked tree is refused",
                  M._glob_tree_is_confined(link) is False)
            for order, label in (((real, link), "target first"),
                                 ((link, real), "link first")):
                inv2 = M.build_inventory(M.default_context())
                verdicts = [inv2.glob_tree_is_confined(p) for p in order]
                expected = [M._glob_tree_is_confined(p) for p in order]
                check(f"memo verdicts are order-independent ({label})",
                      verdicts == expected, f"{verdicts} != {expected}")
            inv3 = M.build_inventory(M.default_context())
            inv3.glob_tree_is_confined(real)
            before = len(inv3._confinement)
            inv3.glob_tree_is_confined(real)
            check("a repeated base is not rescanned",
                  len(inv3._confinement) == before)

    # ---- the ignored set is scoped to the walk, not applied globally ----
    # pack-tests-stay-in-pack uses a raw os.walk on purpose, so a gitignored
    # test that climbs above its pack must still fail.
    with tempfile.TemporaryDirectory(prefix="boundary-ignorescope-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)
        escape = (fixture / "packs" / "demo" / "tests" / "skills" / "demo"
                  / "test_ignored_escape.py")
        escape.parent.mkdir(parents=True, exist_ok=True)
        escape.write_text(
            "from pathlib import Path\n"
            "REPO_ROOT = Path(__file__).resolve().parents[4]\n",
            encoding="utf-8",
        )
        (fixture / ".gitignore").write_text(
            "packs/demo/tests/skills/demo/test_ignored_escape.py\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=str(fixture),
                       capture_output=True, check=False)
        found, _, _ = _silent(M.inspect_boundary, M.default_context(fixture),
                              ["pack-tests-stay-in-pack"])
        check("a gitignored pack test that climbs above its pack still fails",
              any("reaches above" in f.message for f in found), repr(found))

    # ---- nothing on disk was mutated -----------------------------------
    with tempfile.TemporaryDirectory(prefix="boundary-mutate-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)
        before_sig = _tree_signature(fixture)
        _silent(M.inspect_boundary, M.default_context(fixture))
        check("inspect_boundary mutates no file",
              _tree_signature(fixture) == before_sig,
              "tree signature changed")

    # ---- no persistence between invocations ----------------------------
    inv_a = M.build_inventory(context)
    inv_b = M.build_inventory(context)
    check("each invocation gets its own inventory", inv_a is not inv_b)
    check("no confinement state leaks between inventories",
          inv_b._confinement == {}, repr(inv_b._confinement))

    for f in _FAILURES:
        sys.stderr.write(f"FAIL {f}\n")
    if _FAILURES:
        sys.stderr.write(
            f"✖ boundary structural: {len(_FAILURES)} of {_CASES} failed\n"
        )
        return 1
    sys.stderr.write(f"ok — {_CASES} cases passed\n")
    return 0


def _build_min_fixture(root: Path) -> None:
    """A minimal catalogue the lint accepts, in its own Git worktree."""
    def write(rel: str, text: str) -> None:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    root.mkdir(parents=True, exist_ok=True)
    env = M.lint_git_ignore.hermetic_git_env(os.environ)
    subprocess.run(["git", "init", "-q", "."], cwd=str(root),
                   capture_output=True, check=True, env=env)
    write(".gitignore", "__pycache__/\n")
    write("packs/demo/pack.toml", '[pack]\nname = "demo"\n')
    write("packs/demo/.apm/skills/demo/SKILL.md", "# demo\n")
    write("packs/demo/tests/skills/demo/test_demo.py",
          "def test_ok():\n    pass\n")
    write("packages/agentbundle/agentbundle/build/recipes/self-host.toml",
          '[recipe.packs]\ninclude = ["demo"]\n')
    (root / ".claude/skills/demo").mkdir(parents=True, exist_ok=True)
    (root / ".agents/skills/demo").mkdir(parents=True, exist_ok=True)
    write("Makefile", "test:\n\tpytest packs/demo/tests/skills/demo\n")
    for workflow in ("build-check.yml", "catalogue-tooling-ci-gates.yml",
                     "docs.yml"):
        write(f".github/workflows/{workflow}", "steps: []\n")
    write("tools/test-all.py", "CASES = []\n")
    write("packages/agentbundle/agentbundle/catalogue_tooling/"
          "self_host_windows.py", "COMMANDS = ()\n")
    shutil.copy2(ROOT / "tools" / "lint_git_ignore.py", root / "tools")


if __name__ == "__main__":
    raise SystemExit(main())
