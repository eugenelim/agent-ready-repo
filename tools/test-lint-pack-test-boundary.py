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
3. **Source confinement.** Direct owning-pack anchors pass; climbing to the
   repository root fails even when the expression later walks back into the
   owning pack. Temporary fixture paths are outside this source-path rule.
4. **Compatibility classes.** Grouping is explicit: a multi-suite invocation
   must match a declared class and cannot hide a future member behind an ancestor.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

from pack_test_compatibility import CompatibilityClass

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


#: How many times this suite may launch the production CLI against the REAL
#: tree. Fixtures cover the individual plants; these launches exist only to
#: prove the CLI is wired to the real catalogue. The number is asserted, so
#: adding one is a decision rather than an accident.
#:
#: Derived, not hard-coded: where symlinks are unavailable the linked-source
#: plant is skipped, which drops the count by one. A literal 4 would then red on
#: exactly the host class the skip was added to protect.


def _real_launch_budget() -> int:
    return 4 if _SYMLINKS else 3


#: Set near the CURRENT count, not the pre-change one. At 82 against an actual
#: 128 an entire block could vanish and still report green — the silent-drop
#: scenario the floor exists to catch. The pre-change count (82) remains the
#: separate no-regression bar recorded in the audit note.
_CASE_FLOOR = 124

_REAL_LAUNCHES = {"count": 0}


def _run_full() -> tuple[int, str, str]:
    """(exit code, stdout, stderr) from the production CLI on the REAL tree.

    The reason matters: the lint has several failure sites, so `exit != 0` alone
    would let a plant "pass" on an unrelated fault. stdout matters too — the
    success lines and the terminal verdict live there, and no captured baseline
    pins them because every fixture exits 1.
    """
    _REAL_LAUNCHES["count"] += 1
    r = subprocess.run([sys.executable, str(LINT)],
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def _run() -> tuple[int, str]:
    """(exit code, stderr) — the failure-path shape most plants want."""
    rc, _out, err = _run_full()
    return rc, err


def _load_golden():
    """The golden harness, for its fixture builders.

    Imported rather than duplicated: two copies of "what a minimal catalogue
    looks like" would drift, and the golden baseline is keyed to these exact
    shapes. The filename is hyphenated, so it needs a loader.
    """
    path = ROOT / "tools" / "test-lint-boundary-golden.py"
    spec = importlib.util.spec_from_file_location("lint_boundary_golden", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lint_boundary_golden"] = module
    spec.loader.exec_module(module)
    return module


_GOLDEN = _load_golden()
_FIXTURE_CACHE: dict[tuple[str, str], Path] = {}


def _fixture(tmp: Path, name: str) -> Path:
    """Build (once per run) the named fixture catalogue under *tmp*."""
    key = (str(tmp), name)
    if key not in _FIXTURE_CACHE:
        _FIXTURE_CACHE[key] = _GOLDEN._make_fixture(tmp, name)
    return _FIXTURE_CACHE[key]


def _fixture_context(mod, root: Path):
    """A context for a fixture root, with an EMPTY `_NO_RUNNER` map.

    The real map holds real repository paths, so against any fixture every entry
    reports as a stale exemption — eight findings of pure noise that would drown
    the one thing each plant is testing. Injecting an empty map is precisely why
    the map moved into the context. The map's own behaviour is covered in
    `tools/test-lint-boundary-structural.py`.
    """
    base = mod.default_context(root)
    return mod.BoundaryContext(
        root=base.root,
        packs_root=base.packs_root,
        recipe_path=base.recipe_path,
        projected_roots=base.projected_roots,
        runner_files=base.runner_files,
        no_runner={},
        classes=base.classes,
    )


def _findings(mod, root: Path, check_name: str | None):
    """Findings from one check (or all) against a fixture root.

    In-process through the callable API — no CLI launch, so a plant costs
    milliseconds rather than a full production run.

    Deliberately **unfiltered**: an earlier version returned only findings whose
    `check` matched, which made the attribution assertion downstream unable to
    fail — the very property the spec calls load-bearing. Selection is narrowed
    via `inspect_boundary`, and attribution is then a real claim about what came
    back.
    """
    selection = None if check_name is None else [check_name]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return list(
            mod.inspect_boundary(_fixture_context(mod, root), selection)
        )


def _class_fixture(tmp: Path, name: str, members: int = 2) -> tuple[Path, tuple[str, ...]]:
    """A clean declared-class fixture with explicit runner operands."""
    root = _fixture(tmp, name)
    paths = ["packs/demo/tests/skills/demo"]
    for index in range(2, members + 1):
        member = f"packs/demo/tests/skills/member-{index}"
        target = root / member / "test_member.py"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("def test_member():\n    pass\n", encoding="utf-8")
        paths.append(member)
    (root / "Makefile").write_text(
        "test:\n\tpytest " + " ".join(paths) + "\n", encoding="utf-8"
    )
    return root, tuple(paths)


def _class(members: tuple[str, ...], import_mode: str = "prepend") -> CompatibilityClass:
    """One otherwise-valid declaration for a fixture class."""
    return CompatibilityClass(
        identifier="demo-class",
        pack="demo",
        members=members,
        import_mode=import_mode,
        basename_resolution="none",
        subject_imports="none",
        rationale="self-test fixture",
    )


def _class_findings(mod, root: Path, classes: tuple[CompatibilityClass, ...],
                    check: str, exceptions=None):
    """Run one class check with fixture-only declarations and exceptions."""
    context = _fixture_context(mod, root)
    if exceptions is not None:
        context = mod.BoundaryContext(
            root=context.root,
            packs_root=context.packs_root,
            recipe_path=context.recipe_path,
            projected_roots=context.projected_roots,
            runner_files=context.runner_files,
            no_runner=context.no_runner,
            classes=classes,
            unresolvable_runner_exceptions=exceptions,
        )
    else:
        context = mod.BoundaryContext(
            root=context.root,
            packs_root=context.packs_root,
            recipe_path=context.recipe_path,
            projected_roots=context.projected_roots,
            runner_files=context.runner_files,
            no_runner=context.no_runner,
            classes=classes,
            unresolvable_runner_exceptions=context.unresolvable_runner_exceptions,
        )
    return list(mod.inspect_boundary(context, [check]))


def _rewrite(path: Path, text: str) -> None:
    """Replace one temporary-fixture runner, returning `None` for plants."""
    path.write_text(text, encoding="utf-8")


def _symlinks_available() -> bool:
    """Whether this host can create a symlink at all.

    Windows without Developer Mode cannot, and this suite is in the required gate
    chain — so the link cases report a counted SKIP rather than turning a
    Windows maintainer's build red for a capability the platform withholds.
    """
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        target = Path(td) / "t"
        target.write_text("x", encoding="utf-8")
        try:
            (Path(td) / "l").symlink_to(target)
        except OSError:
            return False
        return True


_SYMLINKS = _symlinks_available()


def _tracked_state() -> set[str]:
    """Snapshot of modified tracked files, for a before/after comparison.

    Compared rather than required-empty: the developer may legitimately have
    uncommitted work. What must be empty is the *difference* the suite makes.

    The suite used to append a deliberately-violating target to the real root
    Makefile and restore it afterwards. A concurrent `git add -A` during that
    window committed the injected violation, and the local re-run then passed
    because the file was restored — so it failed only in CI, against a tree the
    developer could not reproduce. That happened on PR #961.
    """
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    return {line for line in proc.stdout.splitlines() if line.strip()}


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
    _tracked_before = _tracked_state()

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

    # ---- layer 3: pack-test source confinement ---------------------------
    cases += 1
    pack_test = ROOT / "packs" / "core" / "tests" / "pack" / "test_x.py"
    accepted = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECT = PACK_ROOT / '.apm' / 'hooks' / 'pre-pr.py'
def test_fixture(tmp_path):
    assert (tmp_path / 'contracts' / 'x.json').is_file()
"""
    if hits := mod._pack_test_escapes(pack_test, accepted):
        failures.append(f"owning-pack and temporary anchors must pass: {hits}")

    cases += 1
    climbed = """
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[4]
SUBJECT = REPO_ROOT / 'packs' / 'core' / '.apm' / 'hooks' / 'pre-pr.py'
"""
    hits = mod._pack_test_escapes(pack_test, climbed)
    if not hits or not any("parents[4]" in expression for _, expression in hits):
        failures.append(
            "a repository-root round trip back into the owning pack must fail"
        )

    cases += 1
    negative_index = """
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[-1]
"""
    hits = mod._pack_test_escapes(pack_test, negative_index)
    if not hits or not any("parents[-1]" in expression for _, expression in hits):
        failures.append("a negative parents index that leaves the pack must fail")

    cases += 1
    dynamic_index = """
from pathlib import Path
DEPTH = 4
REPO_ROOT = Path(__file__).resolve().parents[DEPTH]
"""
    hits = mod._pack_test_escapes(pack_test, dynamic_index)
    if not hits or not any("parents[DEPTH]" in expression for _, expression in hits):
        failures.append("a dynamic parents index rooted in __file__ must fail closed")

    cases += 1
    parents_alias = """
from pathlib import Path
DEPTH = 4
PARENTS = Path(__file__).resolve().parents
REPO_ROOT = PARENTS[DEPTH]
"""
    hits = mod._pack_test_escapes(pack_test, parents_alias)
    if not hits or not any("PARENTS[DEPTH]" in expression for _, expression in hits):
        failures.append("an aliased __file__ parents sequence must fail closed")

    cases += 1
    parents_iteration = """
from pathlib import Path
for candidate in Path(__file__).resolve().parents:
    if (candidate / 'tools').is_dir():
        REPO_ROOT = candidate
        break
"""
    hits = mod._pack_test_escapes(pack_test, parents_iteration)
    if not hits or not any(".parents" in expression for _, expression in hits):
        failures.append("iterating an __file__ parents sequence must fail closed")

    cases += 1
    locally_aliased = """
def test_subject():
    from pathlib import Path as FilePath
    here = FilePath(__file__).resolve()
    repo = here.parents[4]
    assert (repo / 'tools' / 'lint-pack-test-boundary.py').is_file()
"""
    hits = mod._pack_test_escapes(pack_test, locally_aliased)
    if not hits or not any("parents[4]" in expression for _, expression in hits):
        failures.append(
            "a function-local __file__ alias and Path import alias must fail"
        )

    cases += 1
    constructor_alias = """
from pathlib import Path
P = Path
REPO_ROOT = P(__file__).resolve().parents[4]
"""
    hits = mod._pack_test_escapes(pack_test, constructor_alias)
    if not hits or not any("parents[4]" in expression for _, expression in hits):
        failures.append("a Path constructor alias must retain __file__ provenance")

    cases += 1
    abspath_source = """
import os
from pathlib import Path
REPO_ROOT = Path(os.path.abspath(__file__)).parents[4]
"""
    hits = mod._pack_test_escapes(pack_test, abspath_source)
    if not hits or not any("parents[4]" in expression for _, expression in hits):
        failures.append("os.path.abspath(__file__) must retain source provenance")

    cases += 1
    module_constructor_alias = """
import pathlib as pl
P = pl.Path
REPO_ROOT = P(__file__).resolve().parents[4]
"""
    hits = mod._pack_test_escapes(pack_test, module_constructor_alias)
    if not hits or not any("parents[4]" in expression for _, expression in hits):
        failures.append("a module-qualified Path alias must retain provenance")

    for cwd_source in (
        "from pathlib import Path\nROOT = Path.cwd()",
        "import os\nROOT = os.getcwd()",
    ):
        cases += 1
        hits = mod._pack_test_escapes(pack_test, cwd_source)
        if not hits:
            failures.append("working-directory root discovery must fail closed")

    cases += 1
    safe_loop = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
for name in ('one.py', 'two.py'):
    assert (PACK_ROOT / name).is_file()
"""
    if hits := mod._pack_test_escapes(pack_test, safe_loop):
        failures.append(f"literal filename loops inside the pack must pass: {hits}")

    cases += 1
    traversed = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECT = PACK_ROOT / '..' / '..' / 'tools' / 'lint-pack-test-boundary.py'
"""
    hits = mod._pack_test_escapes(pack_test, traversed)
    if not hits or not any("'..'" in expression for _, expression in hits):
        failures.append("lexical .. traversal above the owning pack must fail")

    cases += 1
    joined = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECT = PACK_ROOT.joinpath('..', '..', 'tools', 'lint-pack-test-boundary.py')
"""
    hits = mod._pack_test_escapes(pack_test, joined)
    if not hits or not any("joinpath" in expression for _, expression in hits):
        failures.append("joinpath traversal above the owning pack must fail")

    cases += 1
    multi_argument = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECT = Path(PACK_ROOT, '..', '..', 'tools', 'lint-pack-test-boundary.py')
"""
    hits = mod._pack_test_escapes(pack_test, multi_argument)
    if not hits or not any("Path(PACK_ROOT" in expression for _, expression in hits):
        failures.append("multi-argument Path traversal above the pack must fail")

    cases += 1
    dynamic_join = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
UP = '..'
SUBJECT = PACK_ROOT.joinpath(UP, UP, 'tools')
"""
    hits = mod._pack_test_escapes(pack_test, dynamic_join)
    if not hits or not any("joinpath" in expression for _, expression in hits):
        failures.append("dynamic joinpath segments must fail closed")

    cases += 1
    dynamic_path = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
UP = '..'
SUBJECT = Path(PACK_ROOT, UP, UP, 'tools')
"""
    hits = mod._pack_test_escapes(pack_test, dynamic_path)
    if not hits or not any("Path(PACK_ROOT" in expression for _, expression in hits):
        failures.append("dynamic multi-argument Path segments must fail closed")

    cases += 1
    dynamic_division = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECT = PACK_ROOT / dynamic_segment
"""
    hits = mod._pack_test_escapes(pack_test, dynamic_division)
    if not hits or not any("dynamic_segment" in expression for _, expression in hits):
        failures.append("dynamic division segments must fail closed")

    cases += 1
    glob_traversal = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECTS = list(PACK_ROOT.glob('../../tools/*.py'))
"""
    hits = mod._pack_test_escapes(pack_test, glob_traversal)
    if not hits or not any("glob" in expression for _, expression in hits):
        failures.append("glob parent traversal above the pack must fail")

    cases += 1
    dynamic_glob = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECTS = list(PACK_ROOT.rglob(pattern))
"""
    hits = mod._pack_test_escapes(pack_test, dynamic_glob)
    if not hits or not any("rglob" in expression for _, expression in hits):
        failures.append("dynamic rglob patterns must fail closed")

    for windows_segment in (r"..\tools", r"C:\src\outside", "C:/src/outside"):
        cases += 1
        windows_path = f"""
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECT = PACK_ROOT / {windows_segment!r}
"""
        hits = mod._pack_test_escapes(pack_test, windows_path)
        if not hits:
            failures.append(
                f"Windows path segment {windows_segment!r} must fail on every host"
            )

    cases += 1
    windows_glob = r"""
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECTS = list(PACK_ROOT.glob(r'..\tools\*.py'))
"""
    hits = mod._pack_test_escapes(pack_test, windows_glob)
    if not hits or not any("glob" in expression for _, expression in hits):
        failures.append("Windows glob traversal must fail on every host")

    cases += 1
    linked_glob = """
from pathlib import Path
PACK_ROOT = Path(__file__).resolve().parents[2]
SUBJECTS = list(PACK_ROOT.rglob('*.py'))
"""
    with mock.patch.object(mod, "_glob_tree_is_confined", return_value=False):
        hits = mod._pack_test_escapes(pack_test, linked_glob)
    if not hits or not any("rglob" in expression for _, expression in hits):
        failures.append("a glob over a linked or escaping tree must fail closed")

    cases += 1
    with mock.patch.object(mod, "_is_linked_dir", return_value=True):
        if mod._glob_tree_is_confined(pack_test.parent):
            failures.append("a linked glob base must fail confinement")

    cases += 1
    discovered = """
import subprocess
def repo_root():
    return subprocess.run(['git', 'rev-parse', '--show-toplevel'])
"""
    hits = mod._pack_test_escapes(pack_test, discovered)
    if not hits or not any("show-toplevel" in expression for _, expression in hits):
        failures.append("Git repository-root discovery in a pack test must fail")

    cases += 1
    helper_discovered = """
def test_subject(tmp_path):
    root = git(tmp_path, 'rev-parse', '--show-toplevel')
    assert root
"""
    hits = mod._pack_test_escapes(pack_test, helper_discovered)
    if not hits or not any("show-toplevel" in expression for _, expression in hits):
        failures.append("helper-shaped Git repository-root discovery must fail")

    cases += 1
    resolve_error = """
from pathlib import Path
BROKEN = Path(__file__).resolve().parents[2] / 'resolve-error'
"""
    original_resolve = mod.Path.resolve

    def fail_selected_resolve(path, *args, **kwargs):
        if path.name == "resolve-error":
            raise RuntimeError("planted resolve loop")
        return original_resolve(path, *args, **kwargs)

    with mock.patch.object(mod.Path, "resolve", fail_selected_resolve):
        hits = mod._pack_test_escapes(pack_test, resolve_error)
    if not hits or not any("resolve-error" in expression for _, expression in hits):
        failures.append("a path resolution error must fail closed")

    # The widened matcher must be a strict superset of the one it replaced.
    cases += 1
    for name in ("test_x.py", "test-x.sh", "x_test.js", "x-test.ts"):
        if not mod._TEST_FILE.match(name):
            failures.append(
                f"widened matcher lost {name!r} — the previous matcher caught it"
            )

    cases += 1
    fake_workflow = """
steps:
  - name: not a test runner
    working-directory: packs/core/tests/skills/work-loop
    run: python -c 'pass'
"""
    if mod._workflow_runner_lines("fake.yml", fake_workflow):
        failures.append(
            "a workflow working-directory without pytest must not count as a runner"
        )

    cases += 1
    real_workflow = """
steps:
  - name: test runner
    working-directory: packs/core/tests/skills/work-loop
    run: python -m pytest -q
"""
    workflow_runners = mod._workflow_runner_lines("fake.yml", real_workflow)
    if not workflow_runners or not any(
        "packs/core/tests/skills/work-loop" in tokens
        for _, _, tokens, _, _ in workflow_runners
    ):
        failures.append("a pytest workflow step must inherit its working-directory")

    # ---- layer 2: fixture falsification -----------------------------------
    # Each planted violation is proven against a small temporary catalogue via
    # the callable API. Four properties per plant, and the third is the one that
    # matters: a plant that fails for the *wrong* reason is a guard nobody has
    # actually checked.
    #
    #   1. the lint fails
    #   2. the failure names the plant or its policy
    #   3. the failure comes from the INTENDED check
    #   4. the same fixture without the plant passes that check
    #
    # These used to be twelve launches of the whole production lint against the
    # real worktree, two of which rewrote the real root Makefile. That is what
    # burned PR #961: a concurrent `git add -A` committed the injected violation,
    # and because the file was restored the local re-run passed — so it failed
    # only in CI, against a tree the developer could not reproduce.
    # Checks that both consume the runner inventory, so both report its failures.
    _RUNNER_CONSUMERS = frozenset(
        {"runners-use-approved-pack-compatibility-classes", "every-suite-dir-has-a-runner"}
    )
    plants = (
        # (fixture, check, needle[, expected bearer set — defaults to {check}])
        ("apm-test-file", "apm-carries-no-tests", "test_planted.py"),
        ("apm-singular-test-dir", "apm-carries-no-tests", "/test"),
        ("projection-test-content", "projection-carries-no-tests",
         "test_projected.py"),
        ("pack-not-projected", "projection-carries-no-tests",
         "none of its skills is projected"),
        ("empty-tests-tree", "tests-live-in-the-pack-tree",
         "holds no test content"),
        ("only-gitignored-tests", "tests-live-in-the-pack-tree",
         "holds no test content"),
        ("pack-test-escapes", "pack-tests-stay-in-pack", "reaches above"),
        ("pack-test-unparseable", "pack-tests-stay-in-pack",
         "unparseable Python:"),
        ("symlinked-test-source", "pack-tests-stay-in-pack", "is a symlink"),
        ("linked-test-dir", "pack-tests-stay-in-pack", "linked directory"),
        ("linked-test-root", "pack-tests-stay-in-pack", "root is linked"),
        ("suite-without-runner", "every-suite-dir-has-a-runner",
         "no runner names"),
        # These two are reported by BOTH consuming checks — one cause, two
        # findings — which is preserved behaviour, so the expected bearer set is
        # explicit rather than assumed to be a single check.
        ("missing-runner-file", "runners-use-approved-pack-compatibility-classes",
         "does not exist", _RUNNER_CONSUMERS),
        ("malformed-runner-file", "runners-use-approved-pack-compatibility-classes",
         "is not parseable", _RUNNER_CONSUMERS),
        ("empty-include-list", "projection-carries-no-tests",
         "lists no packs to project"),
        ("no-projected-roots", "projection-carries-no-tests",
         "no projected skills tree found"),
    )
    negatives = (
        # A fixture that plants *allowed* content must NOT fail its check.
        ("apm-evals-allowed", "apm-carries-no-tests"),
        ("apm-transient-allowed", "apm-carries-no-tests"),
    )

    with tempfile.TemporaryDirectory(prefix="boundary-falsify-") as td:
        tmp = Path(td)
        clean_root = _fixture(tmp, "clean")
        clean_ctx = _fixture_context(mod, clean_root)
        # Property 4 is one fact per *check*, not per plant: asserting it inside
        # the plant loop re-ran six distinct facts seventeen times and inflated
        # the case count without adding coverage.
        baseline_checks: set[str] = set()

        skipped_links = 0
        for plant in plants:
            fixture, check_name, needle = plant[:3]
            if not _SYMLINKS and fixture in _GOLDEN.SYMLINK_FIXTURES:
                # The builder itself calls symlink_to, so this must be filtered
                # BEFORE construction — an OSError here would abort the whole
                # suite hundreds of lines before the SKIP notice.
                skipped_links += 1
                cases += 1
                continue
            expected_bearers = plant[3] if len(plant) > 3 else {check_name}
            cases += 1
            root = _fixture(tmp, fixture)
            found = _findings(mod, root, check_name)
            if not found:
                failures.append(
                    f"{fixture}: planted violation did not fail "
                    f"[{check_name}]"
                )
                continue
            if not any(needle in f.message for f in found):
                failures.append(
                    f"{fixture}: [{check_name}] failed, but no finding names "
                    f"{needle!r} — it failed for another reason: "
                    f"{[f.message[:90] for f in found]}"
                )

            # Property 3 — attribution — asserted on an UNSELECTED run.
            # Two earlier attempts asserted it on a selected run, where it cannot
            # fail: `inspect_boundary` stamps each finding with the check that
            # produced it, so narrowing the selection narrows the labels too. Only
            # a full run can show a plant being caught by a check other than the
            # intended one.
            cases += 1
            every = _findings(mod, root, None)
            bearers = {f.check for f in every if needle in f.message}
            if not bearers:
                failures.append(
                    f"{fixture}: a full run does not reproduce the finding that "
                    f"names {needle!r}"
                )
            elif bearers != set(expected_bearers):
                failures.append(
                    f"{fixture}: {needle!r} is reported by {sorted(bearers)}, "
                    f"expected {sorted(expected_bearers)} — the plant is caught "
                    f"by an unintended check"
                )
            baseline_checks.add(check_name)

        for fixture, check_name in negatives:
            cases += 1
            root = _fixture(tmp, fixture)
            found = _findings(mod, root, check_name)
            if found:
                failures.append(
                    f"{fixture}: allowed content must not fail [{check_name}]: "
                    f"{[f.message[:90] for f in found]}"
                )

        # A missing or malformed runner file is reported by BOTH consuming
        # checks — one cause, two findings. Memoising the parse must not
        # collapse that, and the count is the only thing that notices.
        for fixture in ("missing-runner-file", "malformed-runner-file"):
            cases += 1
            root = _fixture(tmp, fixture)
            both = _findings(mod, root, None)
            reporters = {
                f.check for f in both
                if "does not exist" in f.message or "is not parseable" in f.message
            }
            if reporters != {"runners-use-approved-pack-compatibility-classes",
                             "every-suite-dir-has-a-runner"}:
                failures.append(
                    f"{fixture}: expected both consuming checks to report the "
                    f"runner-inventory failure, got {sorted(reporters)}"
                )

        # A parse failure is not permission to suppress an independent coverage
        # failure. The malformed Python runner remains one runner-inventory
        # finding per consumer while this new suite still needs its own report.
        cases += 1
        root = _fixture(tmp, "malformed-runner-file")
        orphan = root / "packs/demo/tests/skills/orphan/test_orphan.py"
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text("def test_orphan():\n    pass\n", encoding="utf-8")
        combined = _findings(mod, root, None)
        parse_reporters = {
            finding.check for finding in combined
            if "is not parseable" in finding.message
        }
        orphan_reporters = {
            finding.check for finding in combined
            if "orphan holds a suite that no runner names" in finding.message
        }
        if parse_reporters != _RUNNER_CONSUMERS or orphan_reporters != {
            "every-suite-dir-has-a-runner"
        }:
            failures.append(
                "a malformed runner suppressed an independent suite-coverage "
                f"finding: parse={sorted(parse_reporters)} "
                f"orphan={sorted(orphan_reporters)}"
            )

        if skipped_links:
            sys.stderr.write(
                f"SKIP {skipped_links} symlink fixture plant(s) — this host "
                f"cannot create symlinks\n"
            )

        # Property 4, once per check that any plant targeted.
        for check_name in sorted(baseline_checks):
            cases += 1
            if _findings(mod, clean_root, check_name):
                failures.append(
                    f"[{check_name}] fails on the clean fixture, so every plant "
                    f"targeting it proves nothing"
                )

        # The clean fixture must pass every check, or every plant above is
        # measured against a broken baseline.
        cases += 1
        clean_findings = mod.inspect_boundary(clean_ctx)
        if clean_findings:
            failures.append(
                f"the clean fixture does not pass, so every plant above is "
                f"measured against a broken baseline: "
                f"{[f.message[:90] for f in clean_findings]}"
            )

        # ---- compatibility-class red controls ----------------------------
        # Each begins with an otherwise-valid declaration and explicit runner,
        # then changes exactly one runner/declaration fact.  These are fixtures,
        # not real-worktree plants: the temporary directory is their cleanup.
        def class_control(label, root, baseline, planted, check_name, needle):
            nonlocal cases
            cases += 1
            before = _class_findings(mod, root, baseline, check_name)
            if before:
                failures.append(
                    f"{label}: clean control fails [{check_name}]: "
                    f"{[f.message for f in before]}"
                )
            cases += 1
            found = _class_findings(mod, root, planted(), check_name)
            if not any(needle in finding.message for finding in found):
                failures.append(
                    f"{label}: plant did not produce {needle!r}: "
                    f"{[f.message for f in found]}"
                )

        runner_check = "runners-use-approved-pack-compatibility-classes"
        well_formed = "compatibility-classes-are-well-formed"

        root, members = _class_fixture(tmp, "class-undeclared")
        declared = (_class(members),)
        class_control(
            "undeclared broad invocation", root, declared, lambda: (), runner_check,
            "does not exactly match a declared compatibility class",
        )

        root, members = _class_fixture(tmp, "class-extra")
        declared = (_class(members[:2]),)
        extra = root / "packs/demo/tests/skills/member-3/test_member.py"
        class_control(
            "broad invocation with an extra path", root, declared,
            lambda: (
                extra.parent.mkdir(parents=True, exist_ok=True),
                _rewrite(
                    extra, "def test_member():\n    pass\n"
                ),
                _rewrite(
                    root / "Makefile",
                    "test:\n\tpytest " + " ".join((*members, "packs/demo/tests/skills/member-3")) + "\n",
                ),
                declared,
            )[-1], runner_check,
            "does not exactly match a declared compatibility class",
        )

        root, members = _class_fixture(tmp, "class-missing")
        declared = (_class(members),)
        missing = root / "packs/demo/tests/skills/member-3/test_member.py"
        missing.parent.mkdir(parents=True, exist_ok=True)
        missing.write_text("def test_member():\n    pass\n", encoding="utf-8")
        class_control(
            "broad invocation missing a class member", root, declared,
            lambda: (_class((*members, "packs/demo/tests/skills/member-3")),),
            runner_check, "does not exactly match a declared compatibility class",
        )

        root, members = _class_fixture(tmp, "class-required-flag")
        importlib_class = (_class(members, import_mode="importlib"),)
        (root / "Makefile").write_text(
            "test:\n\tpytest --import-mode=importlib " + " ".join(members) + "\n",
            encoding="utf-8",
        )
        class_control(
            "grouped command missing its required flag", root, importlib_class,
            lambda: (_rewrite(
                root / "Makefile", "test:\n\tpytest " + " ".join(members) + "\n"
            ) or importlib_class),
            runner_check, "requires --import-mode=importlib",
        )

        root, members = _class_fixture(tmp, "class-ancestor")
        declared = (_class(members),)
        class_control(
            "ancestor-shaped invocation matching a class today", root, declared,
            lambda: (_rewrite(
                root / "Makefile", "test:\n\tpytest packs/demo/tests/skills\n"
            ) or declared),
            runner_check, "is ancestor-shaped",
        )

        root, members = _class_fixture(tmp, "class-cross-pack")
        declared = (_class(members),)
        cross_member = "packs/other/tests/skills/other"
        cross_test = root / cross_member / "test_other.py"
        cross_test.parent.mkdir(parents=True, exist_ok=True)
        (root / "packs/other/pack.toml").write_text("[pack]\nname = 'other'\n",
                                                     encoding="utf-8")
        cross_test.write_text("def test_other():\n    pass\n", encoding="utf-8")
        class_control(
            "class spanning two packs", root, declared,
            lambda: (_class((members[0], cross_member)),), well_formed,
            "is outside pack demo",
        )

        root, members = _class_fixture(tmp, "class-unused", members=3)
        unused = (_class(members),)
        class_control(
            "declared class with no runner", root, unused,
            lambda: (_rewrite(
                root / "Makefile", "test:\n\tpytest " + " ".join(members[:2]) + "\n"
            ) or unused),
            runner_check, "has no runner",
        )

        root, members = _class_fixture(tmp, "class-new-suite")
        declared = (_class(members),)
        new_suite = root / "packs/demo/tests/skills/new-suite/test_new.py"
        new_suite.parent.mkdir(parents=True, exist_ok=True)
        new_suite.write_text("def test_new():\n    pass\n", encoding="utf-8")
        class_control(
            "new suite does not join an existing class", root, declared,
            lambda: (_rewrite(
                root / "Makefile", "test:\n\tpytest packs/demo/tests/skills\n"
            ) or declared),
            runner_check, "does not exactly match a declared compatibility class",
        )

        root, members = _class_fixture(tmp, "class-unresolvable")
        declared = (_class(members),)
        class_control(
            "non-static pytest path", root, declared,
            lambda: (_rewrite(root / "Makefile", 'test:\n\tpytest "$suite"\n') or declared),
            runner_check, "'pytest \"$suite\"' is not statically resolvable",
        )

        root, members = _class_fixture(tmp, "class-stale-exception")
        declared = (_class(members),)
        stale = {("Makefile", 'pytest "$gone"'): "no such runner invocation"}
        cases += 1
        if _class_findings(mod, root, declared, runner_check):
            failures.append("stale AC31 exception: clean control fails")
        cases += 1
        stale_findings = _class_findings(
            mod, root, declared, runner_check, exceptions=stale
        )
        if not any("unresolvable runner exception Makefile 'pytest \"$gone\"' is stale" in finding.message
                   for finding in stale_findings):
            failures.append(
                "stale AC31 exception: plant did not report the stale entry: "
                f"{[f.message for f in stale_findings]}"
            )

        # AC31's shipped exception must match the parser's exact opaque
        # invocation key, rather than merely a substring of the source line.
        cases += 1
        real_exception_findings = list(mod.inspect_boundary(
            mod.default_context(), [runner_check]
        ))
        if any("unresolvable runner exception" in finding.message
               for finding in real_exception_findings):
            failures.append(
                "the shipped AC31 exception is stale on the real runner tree: "
                f"{[f.message for f in real_exception_findings]}"
            )

    # ---- layer 3: minimal real-tree end-to-end ----------------------------
    # Fixtures cannot prove the production CLI is wired to the real catalogue.
    # Only running it against the real catalogue can — so a small number of
    # launches stay, each with a try/finally cleanup guarantee and a refusal to
    # run if its target already exists.
    cases += 1
    rc, out, err = _run_full()
    if rc != 0:
        failures.append(f"real tree, clean: expected exit 0, got {rc}\n{err}")
    # Every captured baseline exits 1, so no golden case pins the SUCCESS path.
    # Assert the terminal wording here, byte-exact — it is the line an operator
    # reads to conclude the gate held, and the eight-check count in it is the
    # claim that all eight ran.
    cases += 1
    if "✓ lint-pack-test-boundary: passed (8 cases)." not in out:
        failures.append(
            f"the clean real tree did not print the eight-check pass line; "
            f"stdout tail: {out[-300:]!r}"
        )
    cases += 1
    if "partial run" in out:
        failures.append(
            "a no-argument run must not present itself as partial"
        )
    cases += 1
    expected_ok = [
        "ok   [apm-carries-no-tests]",
        "ok   [projection-carries-no-tests]",
        "ok   [tests-live-in-the-pack-tree]",
        "ok   [pack-tests-stay-in-pack]",
        "ok   [compatibility-classes-are-well-formed]",
        "ok   [class-members-keep-distinct-module-identity]",
        "ok   [runners-use-approved-pack-compatibility-classes]",
        "ok   [every-suite-dir-has-a-runner]",
    ]
    missing_ok = [line for line in expected_ok if line not in out]
    if missing_ok:
        failures.append(f"clean run omitted success lines: {missing_ok}")
    # Order matters: it is the documented execution order of the eight checks.
    cases += 1
    positions = [out.find(line) for line in expected_ok]
    if positions != sorted(positions):
        failures.append(
            f"the eight success lines are out of documented order: {positions}"
        )

    # One representative runtime-boundary plant.
    plant_dir = ROOT / "packs" / "figma" / ".apm" / "skills" / "figma" / "scripts"
    plant = plant_dir / "test_planted_boundary_violation.py"
    if not plant_dir.is_dir():
        failures.append(f"plant target missing: {plant_dir}")
    elif plant.exists():
        failures.append(f"refusing to plant over an existing file: {plant}")
    else:
        cases += 1
        plant.write_text("# planted by test-lint-pack-test-boundary.py\n",
                         encoding="utf-8")
        try:
            rc, err = _run()
            if rc == 0:
                failures.append("real tree: planted .apm/ test expected exit 1")
            elif plant.name not in err:
                failures.append(
                    f"real tree: lint failed but did not name the plant:\n{err}"
                )
        finally:
            plant.unlink(missing_ok=True)

    # One representative linked-tree plant.
    linked_test = ROOT / "packs" / "figma" / "tests" / "test_planted_link.py"
    if not _SYMLINKS:
        cases += 1
        sys.stderr.write(
            "SKIP real-tree linked-source plant — this host cannot create "
            "symlinks (Windows without Developer Mode); the fixture link cases "
            "are skipped for the same reason\n"
        )
    elif linked_test.exists() or linked_test.is_symlink():
        failures.append(f"refusing to plant over an existing path: {linked_test}")
    else:
        cases += 1
        try:
            linked_test.symlink_to(LINT)
        except OSError as exc:
            failures.append(f"could not plant symlinked pack test: {exc}")
        else:
            try:
                rc, err = _run()
                if rc == 0:
                    failures.append("real tree: symlinked pack test must fail")
                elif linked_test.name not in err or "symlink" not in err:
                    failures.append(
                        f"real tree: symlink plant failed without naming the "
                        f"linked source:\n{err}"
                    )
            finally:
                linked_test.unlink(missing_ok=True)

    # Cleanup restored the tree.
    cases += 1
    rc, err = _run()
    if rc != 0:
        failures.append(
            f"real tree after cleanup: expected exit 0, got {rc}\n{err}"
        )

    cases += 1
    budget = _real_launch_budget()
    if _REAL_LAUNCHES["count"] != budget:
        failures.append(
            f"real-tree production-CLI launches: {_REAL_LAUNCHES['count']} != "
            f"budget {budget}. Adding one is a decision, not an accident — "
            f"update _real_launch_budget deliberately."
        )

    # ---- real-tree controls ----------------------------------------------
    # These two must stay on the real tree: their whole job is to notice that
    # the real tree has drifted. Against a fixture they are trivially true and
    # stop proving anything.
    #
    # C1 — the collision fixture still collides.
    cases += 1
    docx = ROOT / "packs/converters/tests/skills/markdown-to-docx"
    pptx = ROOT / "packs/converters/tests/skills/markdown-to-pptx"
    if docx.is_dir() and pptx.is_dir():
        if not (mod._test_basenames(docx) & mod._test_basenames(pptx)):
            failures.append(
                "expected markdown-to-docx and markdown-to-pptx to share a test "
                "basename — the collision case this lint guards has vanished, so "
                "the guard is no longer proving anything"
            )
    else:
        failures.append("collision fixtures not found in the tree")

    # C2's precondition — the non-colliding pair is still non-colliding, so the
    # "a broad runner fails even without a collision" proof still means what it
    # says. The runner plant itself moved to a fixture.
    cases += 1
    adapt = ROOT / "packs/core/tests/skills/adapt-to-project"
    flow = ROOT / "packs/atlassian/tests/skills/flow-metrics"
    if adapt.is_dir() and flow.is_dir():
        if mod._test_basenames(adapt) & mod._test_basenames(flow):
            failures.append(
                "non-colliding runner fixtures now share a test basename — the "
                "'fails even without a collision' proof no longer holds"
            )
        adapt_subjects = {
            path.name for path in
            (ROOT / "packs/core/.apm/skills/adapt-to-project/scripts").glob("*.py")
        }
        flow_subjects = {
            path.name for path in
            (ROOT / "packs/atlassian/.apm/skills/flow-metrics/scripts").glob("*.py")
        }
        cases += 1
        if adapt_subjects & flow_subjects:
            failures.append(
                "non-colliding runner fixtures now share a subject basename"
            )
    else:
        failures.append("non-colliding runner fixtures not found in the tree")

    # The two real-tree plants are UNTRACKED, so `git status --untracked-files=no`
    # cannot see a leftover. Assert their absence directly.
    cases += 1
    leftover = [
        str(path.relative_to(ROOT))
        for path in (
            ROOT / "packs/figma/.apm/skills/figma/scripts"
                   "/test_planted_boundary_violation.py",
            ROOT / "packs/figma/tests/test_planted_link.py",
        )
        if path.exists() or path.is_symlink()
    ]
    if leftover:
        failures.append(
            f"real-tree plants survived the layer: {leftover}. The next run will "
            f"refuse to plant, and a `git add -A` would commit them."
        )

    # No case may leave a tracked file changed. Compared against the snapshot
    # taken before any plant ran, so the developer's own uncommitted work does
    # not read as a violation.
    cases += 1
    changed = _tracked_state() - _tracked_before
    if changed:
        failures.append(
            f"the suite left tracked files modified: {sorted(changed)}. No case "
            f"may mutate a tracked file — see the "
            f"selftest-mutates-tracked-makefile history."
        )

    # A single ~400-line main() aborts every later block on one exception, so
    # the count silently drops. The floor is the measured pre-change count from
    # the audit note; falling below it is a failure even if nothing else reds.
    if cases < _CASE_FLOOR:
        failures.append(
            f"only {cases} cases ran, below the floor of {_CASE_FLOOR}. A run "
            f"that stops early must not report green."
        )

    for f in failures:
        sys.stderr.write(f"FAIL {f}\n")
    if failures:
        return 1
    sys.stderr.write(f"ok — {cases} cases passed\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
