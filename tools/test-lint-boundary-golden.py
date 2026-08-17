#!/usr/bin/env python3
"""Golden baseline for `tools/lint-pack-test-boundary.py`.

The behaviour contract for that lint is **captured, not described**. Earlier
drafts of `docs/specs/lint-performance-p0` enumerated its failure strings, their
sites, their counts and their check attributions in prose; review found that
enumeration wrong in a new place on every pass, because a hand-maintained
enumeration is a second implementation of the lint with no compiler. So instead:
run the *unmodified* lint against a set of small catalogues, record exactly what
it says, and require the refactored lint to say the same thing.

How it works
------------
The lint derives its root from its own ``__file__``, so copying it into
``<fixture>/tools/`` makes ``<fixture>`` its root. Every path it prints is
root-relative, which is what makes one root's output comparable with another's.

* ``--regenerate`` extracts the subject from a **pinned commit** (never the
  working tree), stages it into each fixture, runs it, and records the result.
* The default path stages whatever is in the working tree and compares.

Before the refactor those are the same file and the comparison is trivially
green. Afterwards, it is the contract.

What is compared
----------------
A **canonical surface** derived from the captured streams, not the raw bytes.
Two sources of legitimate non-determinism make raw bytes the wrong unit:

* the lint's walk returns filesystem order, so a finding that names several paths
  can order them differently on another filesystem;
* one message embeds ``str(SyntaxError)``, whose wording changes between CPython
  minor versions.

So findings are sorted, the path list inside a finding is sorted, and the
interpreter-dependent tail is redacted — then the result is compared byte for
byte. The raw streams are stored too, base64-encoded, so a failure can be
diagnosed and so a privacy audit can read exactly what was captured. Base64
rather than JSON strings because a captured stream may contain bytes that are not
valid UTF-8, and a str round trip would silently replace them.

Hermeticity
-----------
Every subprocess runs with a scrubbed Git environment, and every fixture repo is
initialised with an empty ``core.excludesFile``. This is not hygiene theatre: a
host ``core.excludesFile`` matching, say, ``tests/`` makes a fixture's pack test
come back *ignored*, and because the lint **subtracts** the ignored set while two
of its findings fire on the emptiness of what remains, those failures would be
captured as required **passes** — and would then reproduce green forever.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="strict")
sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")

ROOT = Path(__file__).resolve().parents[1]
SUBJECT_REL = "tools/lint-pack-test-boundary.py"
RESOLVER_REL = "tools/lint_git_ignore.py"
BASELINE = ROOT / "tools" / "lint-boundary-golden.json"

# The pinned capture subject. Changing either value is a spec amendment: pointing
# the pin at a post-refactor commit would make the baseline describe the very
# code it exists to police, while still technically being "a pinned revision".
PINNED_COMMIT = "0245556305e4d19d16af4c3a71f3003f57ce5788"
PINNED_BLOB_SHA256 = (
    "73dd318669c4094cdfc08cdfce825ffd8075d378ee8a67ab2130c0acb6276b3b"
)

_LEAKING_GIT_VARS = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
    "GIT_CEILING_DIRECTORIES", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_CONFIG",
)


def _hermetic_env() -> dict[str, str]:
    env = dict(os.environ)
    for name in _LEAKING_GIT_VARS:
        env.pop(name, None)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_SYSTEM"] = os.devnull
    return env


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                   check=True, env=_hermetic_env())


# ---------------------------------------------------------------------------
# Fixture construction
# ---------------------------------------------------------------------------

_SKILL = "demo"
_PACK = "demo"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _base_fixture(root: Path) -> None:
    """A minimal catalogue the lint passes cleanly, minus its exemption noise.

    Every one of the lint's six runner files must exist, or the runner-inventory
    refusal fires and swamps whatever the fixture is actually testing.
    """
    _write(root / ".gitignore", "__pycache__/\n*.gitignored\n")
    _write(root / f"packs/{_PACK}/pack.toml", '[pack]\nname = "demo"\n')
    _write(root / f"packs/{_PACK}/.apm/skills/{_SKILL}/SKILL.md", "# demo\n")
    _write(
        root / f"packs/{_PACK}/tests/skills/{_SKILL}/test_demo.py",
        "from pathlib import Path\n"
        "PACK_ROOT = Path(__file__).resolve().parents[3]\n"
        "def test_ok():\n    assert PACK_ROOT.is_dir()\n",
    )
    _write(
        root / "packages/agentbundle/agentbundle/build/recipes/self-host.toml",
        '[recipe.packs]\ninclude = ["demo"]\n',
    )
    (root / f".claude/skills/{_SKILL}").mkdir(parents=True, exist_ok=True)
    (root / f".agents/skills/{_SKILL}").mkdir(parents=True, exist_ok=True)
    # A runner naming the one suite, so the coverage check is satisfied.
    _write(
        root / "Makefile",
        "test:\n\tpytest packs/demo/tests/skills/demo\n",
    )
    for workflow in ("build-check.yml", "catalogue-tooling-ci-gates.yml",
                     "docs.yml"):
        _write(root / ".github/workflows" / workflow, "steps: []\n")
    _write(root / "tools/test-all.py", "CASES = []\n")
    _write(
        root
        / "packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py",
        "COMMANDS = ()\n",
    )


def _fx_empty_packs_root(root: Path) -> None:
    """`packs/` exists but holds no pack — the non-vacuity refusal.

    Reached by two checks, and by neither of the other fixtures: every one of
    them ships a pack. A coverage trace over the corpus is what found this gap.
    """
    _base_fixture(root)
    shutil.rmtree(root / f"packs/{_PACK}")
    _write(root / "packs/.keep", "")


def _fx_recipe_missing(root: Path) -> None:
    """The self-host recipe is absent.

    The CLI refuses such a root before traversing, so this refusal is only
    reachable through the callable API — which is exactly why the API accepts a
    context the CLI would reject.
    """
    _base_fixture(root)
    (root / "packages/agentbundle/agentbundle/build/recipes/self-host.toml").unlink()


def _fx_stale_exemption_also_run(root: Path) -> None:
    """A suite named by a runner AND declared unrun — the inverse exemption."""
    _base_fixture(root)
    # The base fixture's Makefile already names packs/demo/tests/skills/demo.
    # The suite is live and a runner names it, so declaring it unrun is the error.
    _write(root / "tools/exemption-marker", "see _NO_RUNNER injection\n")


def _fx_clean(root: Path) -> None:
    _base_fixture(root)


def _fx_apm_test_file(root: Path) -> None:
    _base_fixture(root)
    _write(root / f"packs/{_PACK}/.apm/skills/{_SKILL}/scripts/test_planted.py",
           "# planted\n")


def _fx_apm_singular_test_dir(root: Path) -> None:
    _base_fixture(root)
    (root / f"packs/{_PACK}/.apm/skills/{_SKILL}/test").mkdir(parents=True)
    # git will not track an empty directory; the lint walks the filesystem.
    _write(root / f"packs/{_PACK}/.apm/skills/{_SKILL}/test/.keep", "")


def _fx_apm_evals_allowed(root: Path) -> None:
    """`evals/` is skill-local runtime content (ADR-0071) — a negative case."""
    _base_fixture(root)
    _write(root / f"packs/{_PACK}/.apm/skills/{_SKILL}/evals/test_in_evals.py",
           "# allowed\n")


def _fx_apm_transient_allowed(root: Path) -> None:
    """Build residue is not authored content — another negative case."""
    _base_fixture(root)
    _write(root / f"packs/{_PACK}/.apm/skills/{_SKILL}/__pycache__/test_x.py",
           "# residue\n")


def _fx_projection_test_content(root: Path) -> None:
    _base_fixture(root)
    _write(root / f".claude/skills/{_SKILL}/test_projected.py", "# planted\n")


def _fx_pack_not_projected(root: Path) -> None:
    """A pack in the include list whose skills reach no adapter root."""
    _base_fixture(root)
    shutil.rmtree(root / f".claude/skills/{_SKILL}")
    shutil.rmtree(root / f".agents/skills/{_SKILL}")


def _fx_empty_tests_tree(root: Path) -> None:
    _base_fixture(root)
    shutil.rmtree(root / f"packs/{_PACK}/tests")
    (root / f"packs/{_PACK}/tests").mkdir(parents=True)
    _write(root / f"packs/{_PACK}/tests/.keep", "")


def _fx_only_gitignored_tests(root: Path) -> None:
    """The shape that proves the ignored set is still SUBTRACTED.

    A `tests/` tree whose only content is gitignored must still raise the
    empty-test-tree finding. A refactor that quietly drops ignore filtering
    reproduces every *other* baseline and passes; this one catches it, because
    without the subtraction the tree looks populated and the finding vanishes.

    The planted file must satisfy **both** conditions at once — it has to be a
    shape `_TEST_FILE` actually matches *and* be gitignored. An earlier version
    used `test_demo.gitignored`, which the matcher never recognised as a test
    file at all, so the fixture produced the right output for entirely the wrong
    reason and would not have caught the regression it exists for.
    """
    _base_fixture(root)
    shutil.rmtree(root / f"packs/{_PACK}/tests")
    _write(root / f"packs/{_PACK}/tests/skills/{_SKILL}/test_only_ignored.py",
           "def test_x():\n    pass\n")
    # A real `.py` test file, ignored by an explicit path rule.
    _write(
        root / ".gitignore",
        "__pycache__/\n*.gitignored\n"
        f"packs/{_PACK}/tests/skills/{_SKILL}/test_only_ignored.py\n",
    )
    # Keep a runner target for the now-absent suite out of the picture.
    _write(root / "Makefile", "test:\n\techo none\n")


def _fx_pack_test_escapes(root: Path) -> None:
    _base_fixture(root)
    _write(
        root / f"packs/{_PACK}/tests/skills/{_SKILL}/test_escape.py",
        "from pathlib import Path\n"
        "REPO_ROOT = Path(__file__).resolve().parents[4]\n",
    )


def _fx_pack_test_unparseable(root: Path) -> None:
    _base_fixture(root)
    _write(root / f"packs/{_PACK}/tests/skills/{_SKILL}/test_broken.py",
           "def broken(:\n")


def _fx_symlinked_test_source(root: Path) -> None:
    _base_fixture(root)
    target = root / f"packs/{_PACK}/tests/skills/{_SKILL}/test_demo.py"
    link = root / f"packs/{_PACK}/tests/skills/{_SKILL}/test_linked.py"
    link.symlink_to(target)


def _fx_linked_test_dir(root: Path) -> None:
    _base_fixture(root)
    (root / f"packs/{_PACK}/tests/linked_dir").symlink_to(
        root / f"packs/{_PACK}/.apm", target_is_directory=True
    )


def _fx_linked_test_root(root: Path) -> None:
    _base_fixture(root)
    shutil.rmtree(root / f"packs/{_PACK}/tests")
    (root / f"packs/{_PACK}/tests").symlink_to(
        root / f"packs/{_PACK}/.apm", target_is_directory=True
    )


def _fx_runner_spans_two_suites(root: Path) -> None:
    _base_fixture(root)
    _write(root / f"packs/{_PACK}/tests/skills/other/test_other.py",
           "def test_o():\n    pass\n")
    _write(
        root / "Makefile",
        "test:\n\tpytest packs/demo/tests/skills/demo "
        "packs/demo/tests/skills/other\n",
    )


def _fx_suite_without_runner(root: Path) -> None:
    _base_fixture(root)
    _write(root / f"packs/{_PACK}/tests/skills/orphan/test_orphan.py",
           "def test_x():\n    pass\n")


def _fx_missing_runner_file(root: Path) -> None:
    """Reaches the runner-inventory refusal from BOTH consuming checks."""
    _base_fixture(root)
    (root / "tools/test-all.py").unlink()


def _fx_malformed_runner_file(root: Path) -> None:
    """Only the Python runner path has a parse-failure branch."""
    _base_fixture(root)
    _write(root / "tools/test-all.py", "CASES = [ (unclosed\n")


def _fx_empty_include_list(root: Path) -> None:
    _base_fixture(root)
    _write(
        root / "packages/agentbundle/agentbundle/build/recipes/self-host.toml",
        "[recipe.packs]\ninclude = []\n",
    )


def _fx_no_projected_roots(root: Path) -> None:
    _base_fixture(root)
    shutil.rmtree(root / ".claude")
    shutil.rmtree(root / ".agents")


FIXTURES: dict[str, callable] = {
    "clean": _fx_clean,
    "apm-test-file": _fx_apm_test_file,
    "apm-singular-test-dir": _fx_apm_singular_test_dir,
    "apm-evals-allowed": _fx_apm_evals_allowed,
    "apm-transient-allowed": _fx_apm_transient_allowed,
    "projection-test-content": _fx_projection_test_content,
    "pack-not-projected": _fx_pack_not_projected,
    "empty-tests-tree": _fx_empty_tests_tree,
    "only-gitignored-tests": _fx_only_gitignored_tests,
    "pack-test-escapes": _fx_pack_test_escapes,
    "pack-test-unparseable": _fx_pack_test_unparseable,
    "symlinked-test-source": _fx_symlinked_test_source,
    "linked-test-dir": _fx_linked_test_dir,
    "linked-test-root": _fx_linked_test_root,
    "runner-spans-two-suites": _fx_runner_spans_two_suites,
    "suite-without-runner": _fx_suite_without_runner,
    "missing-runner-file": _fx_missing_runner_file,
    "malformed-runner-file": _fx_malformed_runner_file,
    "empty-include-list": _fx_empty_include_list,
    "no-projected-roots": _fx_no_projected_roots,
    "empty-packs-root": _fx_empty_packs_root,
    "recipe-missing-api-only": _fx_recipe_missing,
    "stale-exemption-also-run": _fx_stale_exemption_also_run,
}

# Deliberately NOT fixtures. A root without `packs/` or without the recipe trips
# an import-time refusal whose message embeds an ABSOLUTE path, so its bytes are
# host-dependent and cannot be committed or reproduced. T4 proves those two
# refusals by direct assertion on the CLI's exit code and relativized message.
# A root with no `packs/` at all trips an import-time refusal whose message
# embeds an ABSOLUTE path, so its bytes are host-dependent and cannot be
# committed. T4 proves it by direct assertion on exit code and message instead.
# (A root with `packs/` present but empty, and one missing only the recipe, ARE
# capturable — see the fixtures of those names.)
UNCAPTURABLE = ("packs-missing-entirely",)


# ---------------------------------------------------------------------------
# Capture and canonicalisation
# ---------------------------------------------------------------------------

_SYNTAX_TAIL = re.compile(r"(is not parseable:).*", re.DOTALL)
_UNPARSEABLE_TAIL = re.compile(r"(unparseable Python:)[^`\n]*")


def _canonical(stream: str) -> str:
    """A comparable surface: order-stable and interpreter-version-stable.

    Findings are emitted in check order but a single finding can name several
    paths in filesystem order, and one message embeds `str(SyntaxError)`. Both
    are legitimate variation that must not read as a regression.
    """
    blocks: list[str] = []
    current: list[str] = []
    for line in stream.splitlines():
        if line.startswith(("FAIL: ", "ok   [", "✓ ", "✖ ")) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    normalised: list[str] = []
    for block in blocks:
        lines = block.splitlines()
        head, tail = lines[0], lines[1:]
        head = _SYNTAX_TAIL.sub(r"\1 <interpreter-dependent>", head)
        head = _UNPARSEABLE_TAIL.sub(r"\1 <interpreter-dependent>", head)
        # Indented continuation lines are a path list in filesystem order.
        indented = sorted(t for t in tail if t.startswith("    "))
        other = [t for t in tail if not t.startswith("    ")]
        normalised.append("\n".join([head, *indented, *other]))

    # FAIL blocks are order-stable per check, but two checks can both contribute;
    # sorting makes the surface independent of accumulation order.
    fails = sorted(b for b in normalised if b.startswith("FAIL: "))
    rest = [b for b in normalised if not b.startswith("FAIL: ")]
    return "\n".join([*fails, *rest]).strip() + "\n"


def _pinned_subject() -> bytes:
    """The capture subject, from Git, with both anchors verified."""
    if not re.fullmatch(r"[0-9a-f]{40}", PINNED_COMMIT):
        raise SystemExit(f"PINNED_COMMIT is not a full 40-hex SHA: {PINNED_COMMIT}")
    proc = subprocess.run(
        ["git", "show", f"{PINNED_COMMIT}:{SUBJECT_REL}"],
        cwd=str(ROOT), capture_output=True, check=False, env=_hermetic_env(),
    )
    if proc.returncode != 0 or not proc.stdout:
        raise SystemExit(
            f"cannot read {SUBJECT_REL} at {PINNED_COMMIT} "
            f"(git exit {proc.returncode}); a shallow clone returns 128 with "
            f"empty stdout — fetch full history rather than staging an empty "
            f"subject"
        )
    digest = hashlib.sha256(proc.stdout).hexdigest()
    if digest != PINNED_BLOB_SHA256:
        raise SystemExit(
            f"subject blob at {PINNED_COMMIT} hashes {digest}, expected "
            f"{PINNED_BLOB_SHA256}. Either the pin moved or history was "
            f"rewritten; both are spec amendments, not refreshes."
        )
    return proc.stdout


def _run_staged(root: Path, subject: bytes | None) -> dict:
    """Stage a subject into *root* and run it with no arguments."""
    tools = root / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    target = tools / Path(SUBJECT_REL).name
    if subject is None:
        shutil.copy2(ROOT / SUBJECT_REL, target)
    else:
        target.write_bytes(subject)
    # Co-stage the resolver: after the refactor the subject imports it, and
    # `<fixture>/tools` is the subject's sys.path[0].
    if (ROOT / RESOLVER_REL).is_file():
        shutil.copy2(ROOT / RESOLVER_REL, tools / Path(RESOLVER_REL).name)

    stray = sorted(
        p.name for p in tools.glob("*.py")
        if p.name not in {Path(SUBJECT_REL).name, Path(RESOLVER_REL).name,
                          "test-all.py"}
    )
    if stray:
        raise SystemExit(
            f"fixture {root.name} wrote {stray} into tools/; staging makes that "
            f"directory the subject's sys.path[0], so a file named os.py or "
            f"ast.py would shadow the standard library"
        )

    proc = subprocess.run(
        [sys.executable, str(target)], cwd=str(root), capture_output=True,
        check=False, env=_hermetic_env(),
    )
    return {
        "exit_code": proc.returncode,
        "stdout_b64": base64.b64encode(proc.stdout).decode("ascii"),
        "stderr_b64": base64.b64encode(proc.stderr).decode("ascii"),
    }


def _decode(record: dict, key: str) -> str:
    return base64.b64decode(record[key].encode("ascii")).decode("utf-8", "replace")


def _make_fixture(tmp: Path, name: str) -> Path:
    root = tmp / name
    root.mkdir(parents=True)
    _git(["init", "-q", "."], root)
    empty = tmp / "empty-excludes"
    if not empty.exists():
        empty.write_text("", encoding="utf-8")
    _git(["config", "core.excludesFile", str(empty)], root)
    FIXTURES[name](root)
    return root


def _capture_all(subject: bytes | None) -> dict:
    cases: dict[str, dict] = {}
    # Fixture roots live outside the repository worktree: a surviving root inside
    # it would become a nested repo the real catalogue lints then walk.
    with tempfile.TemporaryDirectory(prefix="lint-golden-") as td:
        tmp = Path(td)
        for name in FIXTURES:
            cases[name] = _run_staged(_make_fixture(tmp, name), subject)
    return cases


def _regenerate() -> int:
    subject = _pinned_subject()
    payload = {
        "schema": 1,
        "comment": (
            "Captured behaviour of the boundary lint. Compared as a canonical "
            "surface (see the harness docstring); raw streams retained for "
            "diagnosis. Regenerating this file to make a comparison pass is "
            "forbidden by the spec's Never-do rails."
        ),
        "subject": {
            "path": SUBJECT_REL,
            "commit": PINNED_COMMIT,
            "blob_sha256": PINNED_BLOB_SHA256,
        },
        "cases": _capture_all(subject),
    }
    BASELINE.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    sys.stderr.write(
        f"regenerated {BASELINE.relative_to(ROOT)} — {len(payload['cases'])} "
        f"case(s) from {PINNED_COMMIT[:12]}\n"
    )
    return 0


def _compare() -> int:
    if not BASELINE.is_file():
        sys.stderr.write(
            f"FAIL no baseline at {BASELINE.relative_to(ROOT)} — run with "
            f"--regenerate against the pinned subject first\n"
        )
        return 1
    stored = json.loads(BASELINE.read_text(encoding="utf-8"))
    failures: list[str] = []

    if stored.get("subject", {}).get("commit") != PINNED_COMMIT:
        failures.append(
            f"baseline subject commit {stored.get('subject', {}).get('commit')} "
            f"!= pinned {PINNED_COMMIT}"
        )
    if stored.get("subject", {}).get("blob_sha256") != PINNED_BLOB_SHA256:
        failures.append("baseline subject blob hash != pinned blob hash")
    # Proves the pin still resolves and still hashes as recorded.
    _pinned_subject()

    produced = _capture_all(None)
    missing = sorted(set(stored["cases"]) - set(produced))
    extra = sorted(set(produced) - set(stored["cases"]))
    if missing:
        failures.append(f"baseline has cases the harness no longer builds: {missing}")
    if extra:
        failures.append(f"harness builds cases with no baseline: {extra}")

    for name in sorted(set(stored["cases"]) & set(produced)):
        want, got = stored["cases"][name], produced[name]
        if want["exit_code"] != got["exit_code"]:
            failures.append(
                f"{name}: exit {got['exit_code']} != baseline {want['exit_code']}"
            )
        for stream in ("stdout", "stderr"):
            w = _canonical(_decode(want, f"{stream}_b64"))
            g = _canonical(_decode(got, f"{stream}_b64"))
            if w != g:
                import difflib
                diff = "\n".join(
                    difflib.unified_diff(
                        w.splitlines(), g.splitlines(),
                        fromfile=f"baseline/{name}/{stream}",
                        tofile=f"produced/{name}/{stream}", lineterm="",
                    )
                )
                failures.append(f"{name}: {stream} differs\n{diff}")

    for f in failures:
        sys.stderr.write(f"FAIL {f}\n")
    if failures:
        sys.stderr.write(
            f"✖ lint-boundary-golden: {len(failures)} difference(s). If a "
            f"difference is intended, it is a spec amendment recorded with its "
            f"reason — not a --regenerate.\n"
        )
        return 1
    sys.stderr.write(
        f"ok — {len(produced)} captured case(s) reproduced "
        f"({len(UNCAPTURABLE)} refusal(s) deliberately not captured)\n"
    )
    return 0


def _self_check() -> int:
    """Invariants of the harness itself, not of the lint."""
    failures: list[str] = []
    blob = _pinned_subject()
    if hashlib.sha256(blob).hexdigest() != PINNED_BLOB_SHA256:
        failures.append("pinned blob hash mismatch")

    with tempfile.TemporaryDirectory(prefix="lint-golden-self-") as td:
        tmp = Path(td)
        # Determinism: three captures of one fixture must agree.
        seen = set()
        for i in range(3):
            root = _make_fixture(tmp, f"det{i}" if False else "clean")
            seen.add(json.dumps(_run_staged(root, blob), sort_keys=True))
            shutil.rmtree(root)
        if len(seen) != 1:
            failures.append(f"capture is not deterministic across 3 runs: {len(seen)}")

        # No captured stream may carry an absolute path — that would be both a
        # privacy leak and a host-dependent byte.
        root = _make_fixture(tmp, "clean")
        rec = _run_staged(root, blob)
        both = _decode(rec, "stdout_b64") + _decode(rec, "stderr_b64")
        for needle in (str(tmp), str(Path.home()), str(ROOT)):
            if needle and needle in both:
                failures.append(f"captured stream leaks an absolute path: {needle}")

    for f in failures:
        sys.stderr.write(f"FAIL {f}\n")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--regenerate", action="store_true",
        help="re-capture from the pinned subject; never a way to make a "
             "failing comparison pass",
    )
    args = ap.parse_args(argv)
    if args.regenerate:
        return _regenerate()
    rc = _self_check()
    return _compare() if rc == 0 else rc


if __name__ == "__main__":
    raise SystemExit(main())
