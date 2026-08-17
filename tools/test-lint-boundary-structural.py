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
import hashlib
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


def _load_golden():
    """The golden harness, for its fixture builders (hyphenated filename)."""
    path = ROOT / "tools" / "test-lint-boundary-golden.py"
    spec = importlib.util.spec_from_file_location("lint_boundary_golden", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lint_boundary_golden"] = module
    spec.loader.exec_module(module)
    return module


def _tree_signature(root: Path) -> set[tuple[str, str]]:
    """Mutation detector: relative path plus content hash for every file.

    Content hash rather than size — a same-length rewrite is exactly the edit a
    size comparison misses, and the spec's wording is "hashing".
    """
    signature = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__"}]
        for name in filenames:
            path = Path(dirpath) / name
            with contextlib.suppress(OSError):
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                signature.add((str(path.relative_to(root)), digest))
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
    check("exactly one check-ignore process for a non-empty candidate set",
          counter.check_ignore == 1, f"{counter.check_ignore}")
    check("runner files parsed exactly once", inv.runner_parses == 1,
          str(inv.runner_parses))
    check("destination inventory built exactly once",
          inv.destination_builds == 1, str(inv.destination_builds))
    check("every walk base was pre-batched (no lazy misses)",
          inv.walk_misses == 0, f"{inv.walk_misses} lazy walks")
    # Not `len(dict) == len(set(dict))` — dict keys are unique by construction,
    # so that form can never fail. Assert against the distinct bases actually
    # visited, and that the memo is not empty (a memo that never populated would
    # otherwise look tidy).
    _visited = {Path(os.path.normpath(str(b))) for b in inv._confinement}
    check("confinement memo is keyed by distinct normalised bases",
          set(inv._confinement) == _visited and len(inv._confinement) > 0,
          f"{len(inv._confinement)} entries")

    # ---- the callable API is side-effect-free ---------------------------
    check("inspect_boundary prints nothing to stdout", out == "", out[:300])
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
            # Count real scans rather than dict growth: a second call that
            # re-scanned and overwrote the same key leaves the length unchanged,
            # so size proves nothing about memoisation.
            inv3 = M.build_inventory(M.default_context())
            scans = {"n": 0}
            real_scan = M._glob_tree_is_confined

            def counting_scan(base, _real=real_scan):
                scans["n"] += 1
                return _real(base)

            M._glob_tree_is_confined = counting_scan
            try:
                inv3.glob_tree_is_confined(real)
                inv3.glob_tree_is_confined(real)
                inv3.glob_tree_is_confined(real)
            finally:
                M._glob_tree_is_confined = real_scan
            check("a repeated base is scanned exactly once", scans["n"] == 1,
                  f"{scans['n']} scans for 3 calls")

    # ---- the ignored set is scoped to the walk, not applied globally ----
    # pack-tests-stay-in-pack uses a raw os.walk on purpose, so a gitignored test
    # that climbs above its pack must still fail. The trap: if the ignore layer
    # silently degraded, the escape still fails and this case still greens — the
    # exact regression it exists to catch. So first prove the file really IS in
    # the resolved ignored set, then prove the check still reports it.
    with tempfile.TemporaryDirectory(prefix="boundary-ignorescope-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)
        rel = "packs/demo/tests/skills/demo/test_ignored_escape.py"
        escape = fixture / rel
        escape.parent.mkdir(parents=True, exist_ok=True)
        escape.write_text(
            "from pathlib import Path\n"
            "REPO_ROOT = Path(__file__).resolve().parents[4]\n",
            encoding="utf-8",
        )
        (fixture / ".gitignore").write_text(rel + "\n", encoding="utf-8")

        # Precondition, asserted rather than assumed.
        resolution = M.lint_git_ignore.git_ignored_paths(
            fixture, [escape],
            missing_git_policy=M.lint_git_ignore.MissingGitPolicy.FAIL_OPEN,
            timeout=30.0,
        )
        check("the planted escape really is gitignored (layer resolved)",
              not resolution.degraded and escape in set(resolution.ignored),
              f"degraded={resolution.degraded} ignored={resolution.ignored!r}")

        inv_scope = M.build_inventory(M.default_context(fixture))
        check("the inventory's ignored set contains the planted escape",
              escape in inv_scope.ignored,
              f"{len(inv_scope.ignored)} ignored paths")
        check("the inventory did not degrade", not inv_scope.ignore_degraded,
              repr(inv_scope.ignore_detail))
        # And the walk-derived view excludes it, which is what makes the next
        # assertion meaningful rather than incidental.
        walked = inv_scope.walk(fixture / "packs/demo/tests/skills/demo")
        check("the walk view excludes the gitignored file", escape not in walked,
              repr([p.name for p in walked]))

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

    # ---- every finding-emission site is exercised ----------------------
    # A case *count* is not coverage. This derives the answer mechanically:
    # walk the six checks for `out.append`/`out.extend` sites, then drive the
    # whole fixture corpus with a recording list that captures the caller's line
    # number. It found four unreached non-vacuity refusals when first written.
    import ast as _ast

    lint_src = LINT.read_text(encoding="utf-8")
    _tree = _ast.parse(lint_src)
    _check_fns = {f"case_{n}" for n in (
        "apm_carries_no_tests", "projection_carries_no_tests",
        "tests_live_in_the_pack_tree", "pack_tests_stay_in_pack",
        "runners_keep_suites_isolated", "every_suite_dir_has_a_runner")}
    _sites: set[int] = set()
    for _fn in _ast.walk(_tree):
        if isinstance(_fn, _ast.FunctionDef) and _fn.name in _check_fns:
            for _n in _ast.walk(_fn):
                if (isinstance(_n, _ast.Call)
                        and isinstance(_n.func, _ast.Attribute)
                        and _n.func.attr in {"append", "extend"}
                        and getattr(_n.func.value, "id", "") == "out"):
                    _sites.add(_n.lineno)

    _hit: set[int] = set()

    class _Recording(list):
        def append(self, item):
            _hit.add(sys._getframe(1).f_lineno)
            super().append(item)

        def extend(self, items):
            _hit.add(sys._getframe(1).f_lineno)
            super().extend(items)

    _golden = _load_golden()
    with tempfile.TemporaryDirectory(prefix="boundary-coverage-") as td:
        tmp = Path(td)
        for name in _golden.FIXTURES:
            root = _golden._make_fixture(tmp, name)
            base = M.default_context(root)
            variants = (
                base,
                M.BoundaryContext(
                    root=base.root, packs_root=base.packs_root,
                    recipe_path=base.recipe_path,
                    projected_roots=base.projected_roots,
                    runner_files=base.runner_files, no_runner={}),
                M.BoundaryContext(
                    root=base.root, packs_root=base.packs_root,
                    recipe_path=base.recipe_path,
                    projected_roots=base.projected_roots,
                    runner_files=base.runner_files,
                    no_runner={"packs/demo/tests/skills/demo": "planted"}),
            )
            for ctx in variants:
                inv = M.build_inventory(ctx)
                for spec_check in M.CHECKS:
                    _silent(spec_check.run, inv, _Recording())
        inv = M.build_inventory(M.default_context())
        for spec_check in M.CHECKS:
            _silent(spec_check.run, inv, _Recording())

    check("every finding-emission site is exercised by the fixture corpus",
          not (_sites - _hit),
          "unreached: " + ", ".join(
              f":{n} {lint_src.splitlines()[n - 1].strip()[:70]}"
              for n in sorted(_sites - _hit)))
    check("the emission-site scan is not vacuous", len(_sites) >= 20,
          f"found only {len(_sites)} sites")

    # ---- ignore-layer degradation is fatal, and named correctly ---------
    # The spec dedicates an AC section to this and nothing exercised it. Two
    # distinct causes, because the remediation differs: git that cannot run at
    # all, and git that runs and rejects the batch.
    with tempfile.TemporaryDirectory(prefix="boundary-degraded-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)
        broken = Path(td) / "brokengit"
        broken.mkdir()
        (broken / "git").write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
        (broken / "git").chmod(0o755)
        env = dict(os.environ)
        env["PATH"] = f"{broken}{os.pathsep}{env['PATH']}"
        cli = subprocess.run(
            [sys.executable, str(LINT), "--root", str(fixture)],
            capture_output=True, text=True, check=False, env=env,
        )
        merged = cli.stdout + cli.stderr
        check("a broken git makes the lint exit non-zero",
              cli.returncode != 0, f"rc={cli.returncode}")
        check("a broken git is reported as an ignore-layer failure",
              "could not be resolved" in merged or "ignored could not" in merged
              or "unavailable" in merged or "rejected" in merged,
              merged[-500:])
        check("a broken git does not traceback",
              "Traceback (most recent call last)" not in merged, merged[-400:])
        check("a broken git does not report a pass",
              "passed" not in merged, merged[-300:])

        # A refused batch reports a different cause than an unavailable git.
        refused = _resolve_refused(fixture)
        check("a refused batch is flagged refused, not merely degraded",
              refused is not None and refused.refused and refused.degraded,
              repr(refused))

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


def _resolve_refused(root: Path):
    """An IgnoreOutcome for a candidate git will refuse (pathspec magic)."""
    return M._resolve_ignored(root, [Path(":(glob)nope.py")])


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
