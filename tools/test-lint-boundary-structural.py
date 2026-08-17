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

#: A single ~400-line main() aborts every later block on one exception, so the
#: reported count silently drops. Falling below this is a failure in itself.
_CASE_FLOOR = 84

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


def _symlinks_ok() -> bool:
    """Whether this host can create a symlink (Windows without Developer Mode)."""
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "t"
        target.write_text("x", encoding="utf-8")
        try:
            (Path(td) / "l").symlink_to(target)
        except OSError:
            return False
        return True


_SYMLINKS_OK = _symlinks_ok()


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
    # Two earlier attempts at this were tautological: `len(dict) ==
    # len(set(dict))` (dict keys are unique by construction), then
    # `set(memo) == {normpath(k) for k in memo}` (normpath is idempotent on
    # already-normalised keys, so it compared the memo to itself). The only
    # honest form observes what the scanner was actually *called* with.
    _scan_args: list[Path] = []
    _real_scan = M._glob_tree_is_confined

    def _recording_scan(base, _real=_real_scan):
        _scan_args.append(base)
        return _real(base)

    M._glob_tree_is_confined = _recording_scan
    try:
        inv_memo = M.build_inventory(context)
        _silent(M.case_pack_tests_stay_in_pack, inv_memo, [])
    finally:
        M._glob_tree_is_confined = _real_scan

    _distinct = {Path(os.path.normpath(str(b))) for b in _scan_args}
    check("the confinement scanner is called once per distinct base",
          len(_scan_args) == len(_distinct),
          f"{len(_scan_args)} calls for {len(_distinct)} distinct bases")
    check("the memo holds exactly the distinct bases scanned",
          set(inv_memo._confinement) == _distinct,
          f"memo={len(inv_memo._confinement)} scanned_distinct={len(_distinct)}")
    check("the confinement scan is not vacuous", len(_scan_args) > 0,
          "no glob base was ever scanned — the memo proves nothing")

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
        empty_map_ctx = M.BoundaryContext(
            root=base.root, packs_root=base.packs_root,
            recipe_path=base.recipe_path,
            projected_roots=base.projected_roots,
            runner_files=base.runner_files, no_runner={},
        )
        with_real, _, _ = _silent(M.inspect_boundary, base,
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
            if not _SYMLINKS_OK and name in _golden.SYMLINK_FIXTURES:
                continue          # the builder calls symlink_to
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

    # ---- the CLI selector contract, on stdout not just rc ---------------
    # Nothing asserted the partial-run output before: a scoped run could have
    # printed the six-check pass line and every rc-only assertion would still
    # have been green.
    with tempfile.TemporaryDirectory(prefix="boundary-cli-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)

        def cli(*args):
            return subprocess.run(
                [sys.executable, str(LINT), *args],
                capture_output=True, text=True, check=False,
            )

        one = cli("--check", "apm-carries-no-tests")
        check("a --check run exits 0 on a clean tree", one.returncode == 0,
              f"rc={one.returncode}\n{one.stderr[-400:]}")
        check("a --check run announces itself as partial",
              "partial run — checks: apm-carries-no-tests" in one.stdout,
              one.stdout[-400:])
        check("a --check run does NOT print the six-check pass line",
              "passed (6 cases)." not in one.stdout, one.stdout[-400:])
        check("a --check run reports how many of six ran",
              "passed (1 of 6 checks — partial run)." in one.stdout,
              one.stdout[-400:])
        check("a --check run prints only the selected check's ok line",
              one.stdout.count("ok   [") == 1, one.stdout[-400:])

        two = cli("--check", "apm-carries-no-tests",
                  "--check", "tests-live-in-the-pack-tree")
        check("--check is repeatable", two.returncode == 0
              and "passed (2 of 6 checks — partial run)." in two.stdout,
              two.stdout[-400:])

        unknown = cli("--check", "no-such-check")
        check("an unknown --check exits non-zero", unknown.returncode != 0,
              f"rc={unknown.returncode}")
        check("an unknown --check names the accepted set",
              "apm-carries-no-tests" in unknown.stdout + unknown.stderr,
              (unknown.stdout + unknown.stderr)[-500:])

        scoped = cli("--root", str(fixture))
        check("a --root run announces itself as partial",
              "partial run" in scoped.stdout, scoped.stdout[-400:])
        check("a --root run does NOT print the six-check pass line",
              "passed (6 cases)." not in scoped.stdout, scoped.stdout[-400:])

        # --root refusals that had no case: unresolvable, and a linked root.
        missing = cli("--root", str(Path(td) / "does-not-exist"))
        check("an unresolvable --root exits 2", missing.returncode == 2,
              f"rc={missing.returncode}")
        check("the unresolvable --root refusal names the path",
              "does-not-exist" in missing.stderr, missing.stderr[-300:])
        if _SYMLINKS_OK:
            linked = Path(td) / "linked-root"
            linked.symlink_to(fixture, target_is_directory=True)
            refused = cli("--root", str(linked))
            check("a symlinked --root is refused", refused.returncode == 2,
                  f"rc={refused.returncode}\n{refused.stderr[-300:]}")
            check("the symlinked-root refusal says why",
                  "symlink" in refused.stderr or "junction" in refused.stderr,
                  refused.stderr[-300:])
        else:
            check("symlinked --root case skipped (host cannot symlink)", True)
            sys.stderr.write("SKIP symlinked --root — host cannot create "
                             "symlinks\n")

    # ---- the three round-2 correctness fixes, each asserted --------------
    with tempfile.TemporaryDirectory(prefix="boundary-r2-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)

        # (a) the standalone _walk fails closed rather than returning unfiltered
        broken = Path(td) / "brokengit"
        broken.mkdir()
        (broken / "git").write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
        (broken / "git").chmod(0o755)
        raised = None
        original_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{broken}{os.pathsep}{original_path}"
        try:
            M._walk(fixture / "packs" / "demo" / "tests", root=fixture)
        except M.GitIgnoreUnresolved as exc:
            raised = exc
        finally:
            os.environ["PATH"] = original_path
        check("a standalone _walk raises rather than returning unfiltered content",
              raised is not None, repr(raised))

        # (b) a walk-miss resolves its own base instead of using a stale set
        inv_miss = M.build_inventory(M.default_context(fixture))
        before_misses = inv_miss.walk_misses
        unenumerated = fixture / "packs" / "demo" / ".apm" / "skills"
        inv_miss.walk(unenumerated)
        check("a base absent from the enumeration is counted as a miss",
              inv_miss.walk_misses == before_misses + 1,
              f"{before_misses} -> {inv_miss.walk_misses}")
        check("a miss does not mark the inventory degraded when git works",
              not inv_miss.ignore_degraded, repr(inv_miss.ignore_detail))

        # (c) a refused batch is reported as refused, not as unavailable
        real_resolve = M._resolve_ignored

        def _refusal_messages(**outcome_kwargs):
            def refusing(root, candidates):
                return M.IgnoreOutcome(frozenset(), degraded=True,
                                       detail="planted refusal",
                                       **outcome_kwargs)

            M._resolve_ignored = refusing
            try:
                found, _, _ = _silent(
                    M.inspect_boundary, M.default_context(fixture)
                )
            finally:
                M._resolve_ignored = real_resolve
            return " ".join(f.message for f in found)

        messages = _refusal_messages(refused=True, refused_by="git")
        check("a git-refused batch says git REJECTED the batch",
              "rejected the candidate batch" in messages, messages[-400:])
        check("a git-refused batch does not say git is unavailable",
              "git is unavailable" not in messages, messages[-400:])

        # The resolver can refuse a candidate before any subprocess starts — an
        # out-of-root path, or one carrying a leading `:`. Reporting that as
        # "git rejected the batch" points at a process that never ran.
        messages = _refusal_messages(refused=True, refused_by="resolver")
        check("a resolver refusal says the refusal happened before git ran",
              "refused before git was called" in messages, messages[-400:])
        check("a resolver refusal does not blame git for rejecting a batch",
              "rejected the candidate batch" not in messages, messages[-400:])
        check("a resolver refusal names both causes it could be",
              "outside the repository root" in messages
              and "pathspec magic" in messages, messages[-400:])
        check("a resolver refusal still does not say git is unavailable",
              "git is unavailable" not in messages, messages[-400:])

        # Absent git is the third, distinct state, and the only one whose remedy
        # is to change where you run.
        messages = _refusal_messages(refused=False)
        check("an unavailable git says so, and names no refusal",
              "git is unavailable" in messages
              and "refused" not in messages, messages[-400:])

    # ---- CheckResult.summary is pinned, including the one no baseline sees --
    with tempfile.TemporaryDirectory(prefix="boundary-summary-") as td:
        fixture = Path(td) / "fx"
        _build_min_fixture(fixture)
        base = M.default_context(fixture)
        empty_map = M.BoundaryContext(
            root=base.root, packs_root=base.packs_root,
            recipe_path=base.recipe_path, projected_roots=base.projected_roots,
            runner_files=base.runner_files, no_runner={})
        results, _, _ = _silent(M.inspect_boundary_results, empty_map)
        by_name = {r.check: r for r in results}
        check("every check returns a summary when it finds nothing",
              all(r.summary is not None for r in results if not r.findings),
              repr([(r.check, r.summary) for r in results]))
        # Vacuous against a clean fixture — nothing has findings, so `all()` over
        # an empty sequence passes whatever the code does. Plant a violation and
        # assert non-emptiness first.
        (empty_map.packs_root / "demo/.apm/skills/demo/test_planted.py").write_text(
            "def test_x():\n    pass\n", encoding="utf-8"
        )
        dirty, _, _ = _silent(M.inspect_boundary_results, empty_map)
        with_findings = [r for r in dirty if r.findings]
        check("the planted violation actually produces findings",
              len(with_findings) > 0,
              repr([(r.check, len(r.findings)) for r in dirty]))
        check("a check with findings returns no summary",
              all(r.summary is None for r in with_findings),
              repr([(r.check, r.summary) for r in with_findings]))
        check("checks that still pass alongside it keep their summaries",
              all(r.summary is not None for r in dirty if not r.findings),
              repr([(r.check, r.summary) for r in dirty if not r.findings]))
        # This one appears in NO captured baseline: the real _NO_RUNNER map makes
        # it fail in all 22 fixtures, so its counters are pinned only here.
        runner_summary = by_name["every-suite-dir-has-a-runner"].summary
        check("the every-suite-dir-has-a-runner summary is byte-exact",
              runner_summary == "ok   [every-suite-dir-has-a-runner] "
                                "(1 destinations, 0 declared unrun)",
              repr(runner_summary))

    # ---- the golden harness's ambient-state redaction ------------------
    # `_canonical` drops findings derived from the real repository's
    # `_NO_RUNNER` map and from `_RUNNER_FILES` entries no fixture creates.
    # Without a pin here the redaction could broaden until it swallowed real
    # regressions, and the golden gate would go quiet instead of red.
    G = _load_golden()
    ambient = (
        "FAIL: _NO_RUNNER names packs/x/tests/skills/y, which holds no suite\n"
        "FAIL: runner file tools/test-all.py does not exist — the collision\n"
        "FAIL: runner file tools/added-later.py does not exist — the collision\n"
        "FAIL: real regression sentinel\n"
        "\u2716 lint-pack-test-boundary: 4 failure(s)\n"
    )
    reduced = G._canonical(ambient)
    check("the real _NO_RUNNER map is redacted out of the compared surface",
          "_NO_RUNNER names" not in reduced, repr(reduced))
    check("a runner miss the fixture DOES create stays compared",
          "tools/test-all.py does not exist" in reduced, repr(reduced))
    check("a runner miss no fixture could cause is redacted",
          "tools/added-later.py" not in reduced, repr(reduced))
    # Structural, not incidental: a whitespace-only block never reaches the
    # compared surface, so deleting a line can never register as a diff on its
    # own. Asserted by feeding blanks directly rather than by trusting that every
    # redaction regex remembered to eat its newline.
    check("a whitespace-only block never reaches the compared surface",
          G._canonical("FAIL: kept\n\n   \n\nok   [c] (0)\n")
          == "FAIL: kept\nok   [c] (0)\n",
          repr(G._canonical("FAIL: kept\n\n   \n\nok   [c] (0)\n")))
    check("an unrelated finding survives redaction",
          "real regression sentinel" in reduced, repr(reduced))
    check("the failure tally is normalised, since it counts redacted findings",
          "<ambient-adjusted>" in reduced and "4 failure(s)" not in reduced,
          repr(reduced))
    # The set the redaction trusts must match what the fixture actually writes;
    # a typo here silently turns a compared finding into an ignored one.
    check("every trusted runner path is one the base fixture writes",
          {
              "Makefile",
              ".github/workflows/build-check.yml",
              ".github/workflows/catalogue-tooling-ci-gates.yml",
              ".github/workflows/docs.yml",
              "tools/test-all.py",
              "packages/agentbundle/agentbundle/catalogue_tooling/"
              "self_host_windows.py",
          } == G._FIXTURE_RUNNER_FILES, repr(sorted(G._FIXTURE_RUNNER_FILES)))
    check("the trusted set is exactly the subject's runner inventory",
          set(M._RUNNER_FILES) == G._FIXTURE_RUNNER_FILES,
          repr(sorted(set(M._RUNNER_FILES) ^ G._FIXTURE_RUNNER_FILES)))

    # ---- no persistence between invocations ----------------------------
    inv_a = M.build_inventory(context)
    inv_b = M.build_inventory(context)
    check("each invocation gets its own inventory", inv_a is not inv_b)
    check("no confinement state leaks between inventories",
          inv_b._confinement == {}, repr(inv_b._confinement))

    if _CASES < _CASE_FLOOR:
        _FAILURES.append(
            f"only {_CASES} cases ran, below the floor of {_CASE_FLOOR}; a run "
            f"that stops early must not report green"
        )

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
    env = M.lint_git_ignore.hermetic_git_env(os.environ, repo_root=root)
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
