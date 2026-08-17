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

``docs/specs/lint-performance-p0/spec.md`` § *Golden baseline* is the normative
enumeration of every class that surface normalises and of how each one is
supported. It is deliberately not restated here. An earlier version of this
docstring described a subset of the operations and closed on "compared byte
for byte" — the exact phrasing the spec spent two review rounds removing — which
is how a second description at the point of use becomes the drift vector for the
first. Read the spec; `_canonical` below is its implementation.

The raw streams are stored as well, base64-encoded, so a failure can be diagnosed
and a privacy audit can read exactly what was captured. Base64 rather than JSON
strings because a captured stream may contain bytes that are not valid UTF-8, and
a str round trip would silently replace them. (That rationale is implementation
detail this harness owns, which is why it stays here.)

Hermeticity
-----------
Every Git subprocess goes through ``lint_git_ignore.hermetic_git_env``; the spec's
*Hermeticity* bullet enumerates what it removes and what it sets, and is likewise
not duplicated here. Fixture repositories are *additionally* initialised with an
empty ``core.excludesFile`` via ``git config`` — a second mechanism, belt to the
env pin's braces.

Why any of it matters: a host ``core.excludesFile`` matching, say, ``tests/``
makes a fixture's pack test come back *ignored*, and because the lint
**subtracts** the ignored set while two of its findings fire on the emptiness of
what remains, those failures would be captured as required **passes** — and would
then reproduce green forever.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
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

sys.path.insert(0, str(ROOT / "tools"))
import lint_git_ignore  # noqa: E402 — needs the path insert above


def _hermetic_env(repo_root: Path | str | None = None) -> dict[str, str]:
    """The shared scrub, not a private copy.

    A second implementation is how a fix lands in one place and not the other —
    and this is the path that WRITES the committed baseline, so a gap here is a
    poisoned baseline that reproduces green forever.
    """
    return lint_git_ignore.hermetic_git_env(os.environ, repo_root=repo_root)


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), capture_output=True,
                   check=True, env=_hermetic_env(cwd))


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

    Reachable two ways, and the distinction matters: the **no-argument** CLI —
    which is how this fixture is captured, with the subject staged into the
    fixture root — reports it as an ordinary finding, while a `--root` run refuses
    before traversing. That is why the callable API accepts a context the
    `--root` path rejects.
    """
    _base_fixture(root)
    (root / "packages/agentbundle/agentbundle/build/recipes/self-host.toml").unlink()


# The inverse-exemption branch ("declared unrun but a runner names it") needs an
# INJECTED `_NO_RUNNER` map, which the pinned pre-refactor subject cannot accept —
# it reads the module constant. A fixture here would inherit that constant and
# capture bytes identical to `clean`, asserting coverage it does not provide.
# It is covered instead by tools/test-lint-boundary-structural.py's injected-map
# variant, which drives the callable API directly.


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


def symlinks_available() -> bool:
    """Whether this host can create a symlink.

    Windows without Developer Mode cannot, and this harness is in the required
    gate chain — an unguarded `symlink_to` would surface as a traceback there
    rather than a diagnosis.
    """
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "t"
        target.write_text("x", encoding="utf-8")
        try:
            (Path(td) / "l").symlink_to(target)
        except OSError:
            return False
        return True


SYMLINK_FIXTURES = (
    "symlinked-test-source", "linked-test-dir", "linked-test-root",
)


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


FIXTURES: dict[str, Callable[[Path], None]] = {
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
    "recipe-missing": _fx_recipe_missing,
}

# Deliberately NOT a fixture: a root with no `packs/` directory at all trips an
# import-time refusal whose message embeds an ABSOLUTE path, so its bytes are
# host-dependent and cannot be committed. T4 proves it by direct assertion on the
# CLI's exit code and relativized message instead.
#
# A root with `packs/` present but empty, and one missing only the RECIPE, ARE
# capturable and are fixtures below — for the recipe case the no-argument CLI
# reports an ordinary finding, and only a `--root` run refuses before walking.
UNCAPTURABLE = ("packs-missing-entirely",)


# ---------------------------------------------------------------------------
# Capture and canonicalisation
# ---------------------------------------------------------------------------

_SYNTAX_TAIL = re.compile(r"(is not parseable:).*", re.DOTALL)
_UNPARSEABLE_TAIL = re.compile(r"(unparseable Python:)[^`\n]*")

#: The runner files `_base_fixture` actually creates. A `runner file … does not
#: exist` finding naming one of these is fixture behaviour — the
#: `missing-runner-file` case deletes `tools/test-all.py` on purpose and the
#: baseline must keep reporting it. A finding naming anything else came from a
#: `_RUNNER_FILES` entry added after the pin, for a file no fixture ever had, and
#: is dropped for the same reason as the `_NO_RUNNER` map (see
#: `_AMBIENT_NO_RUNNER` below).
#:
#: Creating stand-ins instead is not an option: `_stage` puts the fixture's
#: `tools/` on the staged subject's `sys.path[0]`, and the stray-file guard below
#: refuses a fixture that writes there. That guard is fail-closed on purpose and
#: is not worth weakening for capture convenience.
#:
#: KNOWN RE-PIN TRIGGER, and the one this redaction does NOT cover: adding an
#: entry to `_RUNNER_FILES` adds `FAIL: runner file …` lines that this redaction
#: DOES drop — but not the consequence: the missing file makes
#: `runners-keep-suites-isolated` fail, so its `ok` line disappears from all 22
#: baselines, and no redaction can restore an absent line. `--regenerate` cannot
#: help either, because
#: it re-runs the pinned subject, whose older list still passes. Adding a runner
#: file therefore requires repointing `PINNED_COMMIT`/`PINNED_BLOB_SHA256` at a
#: commit containing it. That is accepted rather than fixed: `_RUNNER_FILES` grows
#: when the repo gains a CI runner (rare, structural, already a reviewed change),
#: whereas `_NO_RUNNER` grows whenever a suite is intentionally ungated (routine)
#: — and it was only the routine edit that made the gate something to route
#: around.
_FIXTURE_RUNNER_FILES = frozenset(
    {
        "Makefile",
        ".github/workflows/build-check.yml",
        ".github/workflows/catalogue-tooling-ci-gates.yml",
        ".github/workflows/docs.yml",
        "tools/test-all.py",
        "packages/agentbundle/agentbundle/catalogue_tooling/self_host_windows.py",
    }
)
_RUNNER_MISSING = re.compile(
    r"^FAIL: runner file (\S+) does not exist\b.*\n?", re.MULTILINE
)


def _drop_unpinned_runner_misses(stream: str) -> tuple[str, int]:
    """Drop `runner file … does not exist` lines the fixture never could cause.

    Returns the stream and how many lines went, because the caller subtracts that
    from the failure tally rather than erasing it.
    """
    dropped = 0

    def _sub(match: re.Match) -> str:
        nonlocal dropped
        if match.group(1) in _FIXTURE_RUNNER_FILES:
            return match.group(0)
        dropped += 1
        return ""

    return _RUNNER_MISSING.sub(_sub, stream), dropped


#: Findings derived from the REAL repository's `_NO_RUNNER` map rather than from
#: anything the fixture does. Every fixture inherits one per entry, because the
#: pinned subject reads that module constant and cannot be handed an injected map.
#:
#: They are dropped from the compared surface, and that is not cosmetic. Left in,
#: adding a `_NO_RUNNER` entry — the documented, sanctioned action when a new
#: suite is intentionally ungated — reddens 18 of 22 baselines, and
#: `--regenerate` cannot clear it because it re-reads the *pinned* subject and so
#: reproduces the old map. The gate would stay red until someone repointed the
#: pin, which is an `Ask first` amendment. A gate that a legitimate edit can
#: deadlock is a gate people learn to route around.
#:
#: Nothing is lost: the injected-map behaviour — including a stale entry and an
#: entry a runner also names — is pinned directly in
#: `tools/test-lint-boundary-structural.py`, which drives the callable API and
#: can supply its own map.
#: Only the three real line terminators. `str.splitlines()` would also split on
#: every character in `SPLITLINES_EXTRA` below — verified: a path
#: containing U+2028 or a form feed was silently broken into two lines and then
#: reordered by the tail rules, which contradicts the resolver's own criterion that
#: newlines and Unicode in paths round-trip correctly. Normalising `\r\n` and `\r`
#: to `\n` is deliberate and load-bearing (it is what lets a POSIX-captured
#: baseline compare on a Windows host, where `print()` emits `\r\n`); splitting on
#: anything else is not.
_LINE_TERMINATOR = re.compile(r"\r\n|\r|\n")

#: Every character `str.splitlines()` treats as a line boundary beyond CR and LF.
#: Enumerated once, here, and consumed by the structural suite's assertion loop —
#: an earlier revision listed a five-character subset in the spec, another subset
#: in the assertion, and the full set only in a comment, which is the same
#: three-copies-two-stale shape this spec's review kept finding elsewhere.
SPLITLINES_EXTRA = ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85",
                    "\u2028", "\u2029")


_AMBIENT_NO_RUNNER = re.compile(
    r"^FAIL: _NO_RUNNER names \S+, which holds no suite\b.*\n?", re.MULTILINE
)


def _canonical(stream: str) -> str:  # noqa: C901 — a flat normalisation pipeline
    """A comparable surface: order-stable and interpreter-version-stable.

    Findings are emitted in check order but a single finding can name several
    paths in filesystem order, and one message embeds `str(SyntaxError)`. Both
    are legitimate variation that must not read as a regression.
    """
    # FIRST, before anything else touches the stream. The two ambient-redaction
    # regexes below are `re.MULTILINE`, so their `^` anchors only after a `\n`. Run
    # against a bare-`\r` stream they see one logical line and `.*` — which matches
    # `\r` — swallows the whole surface: verified, a three-finding stream collapsed
    # to a single newline. Normalising terminators up front removes the precondition
    # instead of documenting it.
    stream = "\n".join(_LINE_TERMINATOR.split(stream))
    stream, ambient_no_runner = _AMBIENT_NO_RUNNER.subn("", stream)
    stream, ambient_runner_miss = _drop_unpinned_runner_misses(stream)
    redacted = ambient_no_runner + ambient_runner_miss
    blocks: list[str] = []
    current: list[str] = []
    for line in stream.split("\n"):   # terminators already folded above
        if line.startswith(("FAIL: ", "ok   [", "✓ ", "✖ ")) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current))

    normalised: list[str] = []
    for block in blocks:
        lines = block.split("\n")   # blocks were joined with "\n" above
        # Redaction above deletes whole lines. A deleted line leaves a blank
        # behind, and a blank does not start a new block, so it rides along as a
        # tail line of whatever block precedes it — which is precisely how a
        # dropped finding used to surface as a `+` blank-line diff. Blanks carry
        # no diagnostic content here, so discarding them (and any block left
        # holding only blanks) makes redaction whitespace-neutral by
        # construction. The regexes' trailing `\n?` is then belt-and-braces
        # rather than the only thing standing between a dropped line and a
        # spurious failure.
        if not any(line.strip() for line in lines):
            continue
        head, tail = lines[0], [t for t in lines[1:] if t.strip()]
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
    # The `✖ … N failure(s)` tally counts the ambient findings just dropped, so it
    # is adjusted DOWN by exactly that many rather than erased. The lint prints one
    # `FAIL:` line per finding and then `len(findings)`, so `original - redacted`
    # is exact, not an estimate.
    #
    # Keeping a number here is what preserves the one signal wholesale erasure
    # loses: a finding appended twice but printed once. That is not hypothetical —
    # the memoised runner parse must re-append its findings per consumer (spec
    # § Golden baseline, deliberate divergence 2), so a double-append is exactly
    # the regression this surface has to be able to see.

    def _adjust(match: re.Match) -> str:
        # Deliberately unclamped. A negative would mean the lint printed fewer
        # `FAIL:` lines than its own tally counted — a real defect in the lint, and
        # one worth reading as `-1 failure(s)` in a diff rather than hidden behind a
        # `max(0, …)` that would make the surface agree with a broken subject.
        return f"{match.group(1)}{int(match.group(2)) - redacted}{match.group(3)}"

    rest = [
        re.sub(r"(✖ lint-pack-test-boundary: )(\d+)( failure\(s\))", _adjust, b)
        for b in rest
    ]
    return "\n".join([*fails, *rest]).strip() + "\n"


def _pinned_subject() -> bytes:
    """The capture subject, from Git, with both anchors verified."""
    if not re.fullmatch(r"[0-9a-f]{40}", PINNED_COMMIT):
        raise SystemExit(f"PINNED_COMMIT is not a full 40-hex SHA: {PINNED_COMMIT}")
    proc = subprocess.run(
        ["git", "show", f"{PINNED_COMMIT}:{SUBJECT_REL}"],
        cwd=str(ROOT), capture_output=True, check=False,
        env=_hermetic_env(ROOT),
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

    # `test-all.py` is exempt because `_base_fixture` writes it as one of the
    # lint's six required runner files, and a hyphenated name is not importable —
    # so it cannot shadow anything.
    stray = sorted(
        p.name for p in tools.glob("*.py")
        if p.name not in {Path(SUBJECT_REL).name, Path(RESOLVER_REL).name,
                          "test-all.py"}
    )
    # A package directory shadows just as effectively as a module, and the glob
    # above cannot see it.
    stray += sorted(
        f"{d.name}/" for d in tools.iterdir()
        if d.is_dir() and (d / "__init__.py").exists()
    )
    if stray:
        raise SystemExit(
            f"fixture {root.name} wrote {stray} into tools/; staging makes that "
            f"directory the subject's sys.path[0], so a module or package named "
            f"os, ast or subprocess would shadow the standard library"
        )

    proc = subprocess.run(
        [sys.executable, str(target)], cwd=str(root), capture_output=True,
        check=False, env=_hermetic_env(root),
    )
    return {
        "exit_code": proc.returncode,
        "stdout_b64": lint_git_ignore.encode_stream(proc.stdout),
        "stderr_b64": lint_git_ignore.encode_stream(proc.stderr),
    }


def _decode(record: dict, key: str) -> str:
    return lint_git_ignore.decode_stream(record[key]).decode("utf-8", "replace")


def _raw(record: dict, key: str) -> bytes:
    """The captured stream as stored, undecoded.

    The privacy scan must use this, not `_decode`. `_decode` replaces every
    invalid byte with `U+FFFD`, so a needle containing non-ASCII — `Path.home()`
    on a host whose username is not ASCII, which `AGENTS.md § Privacy` names as
    forbidden content — can be broken apart by a substitution and slip past the
    refusal that guards the committed baseline. A backstop that a lossy decode can
    defeat is not a backstop.
    """
    return lint_git_ignore.decode_stream(record[key])


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


def _capture_all(subject: bytes | None) -> tuple[dict, str]:
    """Capture every fixture, returning the records and the temp root used.

    The temp root is returned so the caller's leak scan can look for the actual
    path rather than a hard-coded platform shape — the fixture root is
    `/var/folders/...` on macOS but `/tmp/...` on Linux CI, and a needle list
    written on one platform silently scans for nothing on the other.
    """
    cases: dict[str, dict] = {}
    # Fixture roots live outside the repository worktree: a surviving root inside
    # it would become a nested repo the real catalogue lints then walk.
    with tempfile.TemporaryDirectory(prefix="lint-golden-") as td:
        tmp = Path(td)
        skip_links = not symlinks_available()
        for name in FIXTURES:
            if skip_links and name in SYMLINK_FIXTURES:
                continue          # reported by the caller, not silently dropped
            cases[name] = _run_staged(_make_fixture(tmp, name), subject)
        used_root = td
    return cases, used_root


def _regenerate() -> int:
    subject = _pinned_subject()
    captured, temp_root = _capture_all(subject)
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
        "cases": captured,
    }
    # The one code path that WRITES the committed file must run the leak scan
    # over every case, not just the one `_self_check` samples. An absolute path
    # here is both a privacy leak and a host-dependent byte.
    needles = [
        str(ROOT), str(Path.home()), temp_root,
        str(Path(temp_root).resolve()), tempfile.gettempdir(),
        str(Path(tempfile.gettempdir()).resolve()),
    ]
    leaks: list[str] = []
    for name, record in payload["cases"].items():
        raw = _raw(record, "stdout_b64") + _raw(record, "stderr_b64")
        leaks += [f"{name}: {n}" for n in needles
                  if n and os.fsencode(n) in raw]
    if leaks:
        raise SystemExit(
            "refusing to write the baseline — captured streams contain absolute "
            "paths, which are host-dependent and a privacy leak:\n  "
            + "\n  ".join(leaks[:10])
        )
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

    produced, _ = _capture_all(None)
    missing = sorted(set(stored["cases"]) - set(produced))
    extra = sorted(set(produced) - set(stored["cases"]))
    if missing and not symlinks_available():
        skipped = [n for n in missing if n in SYMLINK_FIXTURES]
        missing = [n for n in missing if n not in SYMLINK_FIXTURES]
        if skipped:
            sys.stderr.write(
                f"SKIP {len(skipped)} symlink fixture(s) — this host cannot "
                f"create symlinks: {skipped}\n"
            )
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
                        _LINE_TERMINATOR.split(w), _LINE_TERMINATOR.split(g),
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
        # Determinism, over the fixtures that actually vary. `clean` exercises
        # neither source of non-determinism `_canonical` exists to absorb — a
        # multi-path finding in filesystem order, and interpreter-dependent
        # `str(SyntaxError)` text — so three captures of it proved little.
        for name in ("pack-test-escapes", "pack-test-unparseable",
                     "apm-test-file", "clean"):
            seen = set()
            for _ in range(3):
                root = _make_fixture(tmp, name)
                record = _run_staged(root, blob)
                seen.add((
                    record["exit_code"],
                    _canonical(lint_git_ignore.decode_stream(
                        record["stdout_b64"]).decode("utf-8", "replace")),
                    _canonical(lint_git_ignore.decode_stream(
                        record["stderr_b64"]).decode("utf-8", "replace")),
                ))
                shutil.rmtree(root)
            if len(seen) != 1:
                failures.append(
                    f"capture of {name!r} is not deterministic across 3 runs "
                    f"({len(seen)} distinct results)"
                )

        # No captured stream may carry an absolute path — that would be both a
        # privacy leak and a host-dependent byte.
        root = _make_fixture(tmp, "clean")
        rec = _run_staged(root, blob)
        raw = _raw(rec, "stdout_b64") + _raw(rec, "stderr_b64")
        for needle in (str(tmp), str(Path.home()), str(ROOT)):
            if needle and os.fsencode(needle) in raw:
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
